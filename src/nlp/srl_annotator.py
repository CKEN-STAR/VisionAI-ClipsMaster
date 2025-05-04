#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
语义角色标注模块 - 支持中英文双语言的语义角色分析
提供高效的内存管理，支持动态加载/卸载模型以适应低配置环境
"""

import os
import yaml
import logging
import numpy as np
from typing import Dict, Any, Optional, Tuple, List, Union
import threading
import time
import re

# 配置日志
from src.utils.log_handler import get_logger
logger = get_logger("srl_annotator")

# 尝试导入必要的库，如果不存在则提供优雅的降级方案
try:
    from transformers import pipeline, AutoTokenizer, AutoModelForTokenClassification
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    logger.warning("Transformers库未安装，将使用备用语义角色标注方案")
    TRANSFORMERS_AVAILABLE = False

# 尝试导入中文分词库
try:
    import jieba
    JIEBA_AVAILABLE = True
except ImportError:
    logger.warning("Jieba分词库未安装，中文处理将使用简单分词")
    JIEBA_AVAILABLE = False

# 配置目录路径
CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "configs")
MODEL_CONFIG_PATH = os.path.join(CONFIG_DIR, "model_config.yaml")

# 导入内存监控
from src.utils.memory_guard import track_memory, register_object, unregister_object, update_object_timestamp

class SRLCache:
    """语义角色标注结果缓存，减少重复计算"""
    
    def __init__(self, max_size: int = 1000):
        self.cache = {}
        self.max_size = max_size
        self.lock = threading.Lock()
        
    def get(self, text: str, lang: str) -> Optional[List[Dict[str, Any]]]:
        """获取缓存的语义角色标注结果"""
        key = f"{lang}:{text}"
        with self.lock:
            result = self.cache.get(key)
            if result:
                # 更新访问时间
                result['last_access'] = time.time()
            return result.get('roles') if result else None
    
    def set(self, text: str, lang: str, roles: List[Dict[str, Any]]) -> None:
        """存储语义角色标注结果到缓存"""
        key = f"{lang}:{text}"
        with self.lock:
            # 如果缓存已满，清除最早的20%条目
            if len(self.cache) >= self.max_size:
                # 按访问时间排序并保留80%的最新条目
                sorted_keys = sorted(self.cache.keys(), 
                                     key=lambda k: self.cache[k].get('last_access', 0))
                for old_key in sorted_keys[:int(self.max_size * 0.2)]:
                    del self.cache[old_key]
            
            # 添加访问时间戳
            self.cache[key] = {
                'roles': roles,
                'last_access': time.time()
            }


class MemoryOptimizedSRLPipeline:
    """内存优化的SRL模型管道，支持动态加载/卸载"""
    
    def __init__(self, model_path: str, task: str = "token-classification", device: str = "cpu"):
        self.model_path = model_path
        self.task = task
        self.device = device
        self.pipeline = None
        self.tokenizer = None
        self.model = None
        self.last_used = 0
        self.is_loaded = False
        self.lock = threading.Lock()
        
    def load(self) -> None:
        """加载模型和分词器"""
        if self.is_loaded:
            return
        
        with self.lock:
            if self.is_loaded:  # 双重检查锁定
                return
                
            try:
                logger.info(f"加载SRL模型: {self.model_path}")
                
                # 使用AutoTokenizer和AutoModel手动加载以实现更好的内存控制
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
                self.model = AutoModelForTokenClassification.from_pretrained(
                    self.model_path, 
                    torchscript=True,  # 启用TorchScript优化
                    low_cpu_mem_usage=True,  # 减少CPU内存使用
                )
                
                # 创建处理管道
                self.pipeline = pipeline(
                    self.task,
                    model=self.model,
                    tokenizer=self.tokenizer,
                    device=self.device,
                    aggregation_strategy="simple"  # 使用简单聚合，减少计算量
                )
                
                self.is_loaded = True
                self.last_used = time.time()
                logger.info(f"SRL模型 {self.model_path} 加载成功")
                
                # 注册对象用于内存监控
                register_object(f"srl_model_{self.model_path}", self, self.unload)
                
            except Exception as e:
                logger.error(f"加载SRL模型 {self.model_path} 失败: {str(e)}")
                # 清理可能部分加载的资源
                self.unload()
                raise
    
    def unload(self) -> None:
        """卸载模型以释放内存"""
        with self.lock:
            if not self.is_loaded:
                return
                
            logger.info(f"卸载SRL模型: {self.model_path}")
            
            # 删除模型和分词器引用
            self.pipeline = None
            self.model = None
            self.tokenizer = None
            
            # 手动触发垃圾回收
            import gc
            gc.collect()
            
            if 'torch' in globals() and torch.cuda.is_available():
                torch.cuda.empty_cache()
                
            self.is_loaded = False
            
            # 取消注册对象
            unregister_object(f"srl_model_{self.model_path}")
            
            logger.info(f"SRL模型 {self.model_path} 卸载成功")
    
    def __call__(self, text: Union[str, List[str]], **kwargs) -> Any:
        """运行语义角色标注"""
        # 确保模型已加载
        self.load()
        
        # 更新最后使用时间
        self.last_used = time.time()
        update_object_timestamp(f"srl_model_{self.model_path}")
        
        # 使用模型进行预测
        return self.pipeline(text, **kwargs)


class SemanticRoleLabeler:
    """双语语义角色标注器，支持中英文"""
    
    def __init__(self):
        # 加载配置
        self.config = self._load_config()
        
        # 初始化缓存
        self.cache = SRLCache(max_size=self.config.get('cache_size', 1000))
        
        # 判断是否使用Transformers或备用分析方案
        # 默认使用备用方案，只有在明确需要时才加载模型
        self.zh_srl = self._create_fallback_srl("zh")
        self.en_srl = self._create_fallback_srl("en")
        
        # 模型配置 - 用于后续按需加载
        if TRANSFORMERS_AVAILABLE:
            # 创建中文SRL管道配置
            self._zh_srl_config = {
                "model_path": "hfl/chinese-bert-wwm-ext",  # 未来需要替换为专门的中文SRL模型
                "task": "token-classification",
                "device": "cpu"
            }
            
            # 创建英文SRL管道配置
            self._en_srl_config = {
                "model_path": "https://storage.googleapis.com/allennlp-public-models/structured-prediction-srl-bert.2020.12.15.tar.gz",
                "task": "token-classification",
                "device": "cpu"
            }
        else:
            self._zh_srl_config = {"fallback": True}
            self._en_srl_config = {"fallback": True}
        
        # 模型管理线程
        self._start_model_manager()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            with open(MODEL_CONFIG_PATH, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                
            # 提取相关配置
            return {
                'max_memory_usage': config.get('loading_strategy', {}).get('max_memory_usage', 3800),
                'dynamic_unloading': config.get('loading_strategy', {}).get('dynamic_unloading', True),
                'unload_timeout': 300,  # 5分钟不使用自动卸载
                'cache_size': 1000
            }
        except Exception as e:
            logger.error(f"加载配置文件失败: {str(e)}")
            # 返回默认配置
            return {
                'max_memory_usage': 3800,
                'dynamic_unloading': True,
                'unload_timeout': 300,
                'cache_size': 1000
            }
    
    def _create_fallback_srl(self, lang: str):
        """创建备用语义角色标注器（基于规则）"""
        def analyze(text: str) -> List[Dict[str, Any]]:
            """简单的基于规则的语义角色标注"""
            results = []
            
            # 分词处理
            if lang == "zh":
                if JIEBA_AVAILABLE:
                    words = jieba.lcut(text)
                else:
                    # 简单的字符分割
                    words = list(text)
            else:  # 英文
                words = text.split()
            
            # 简单句式模式匹配
            if words:
                # 寻找主谓宾关系
                if lang == "zh":
                    # 中文基本句式规则
                    sentence_info = {"text": text, "words": words}
                    
                    # 尝试识别主语(通常在句首)
                    if len(words) > 1:
                        subject_len = min(3, len(words) // 3)
                        subject = "".join(words[:subject_len])
                        sentence_info["subject"] = subject
                    
                    # 尝试识别谓语动词
                    if len(words) > 2:
                        verb_pos = min(subject_len, len(words) // 2)
                        verb = words[verb_pos]
                        sentence_info["verb"] = verb
                    
                    # 尝试识别宾语
                    if len(words) > 3:
                        object_start = min(verb_pos + 1, len(words) - 1)
                        object_text = "".join(words[object_start:])
                        sentence_info["object"] = object_text
                    
                    results.append(sentence_info)
                else:
                    # 英文基本句式规则
                    # 寻找动词
                    verbs = [w for w in words if w.endswith("ing") or w.endswith("ed")]
                    
                    if verbs:
                        for verb in verbs:
                            verb_index = words.index(verb)
                            
                            # 构建基本的角色信息
                            role_info = {
                                "verb": verb,
                                "text": text
                            }
                            
                            # 提取主语(动词前)
                            if verb_index > 0:
                                subject = " ".join(words[:verb_index])
                                role_info["subject"] = subject
                            
                            # 提取宾语(动词后)
                            if verb_index < len(words) - 1:
                                object_text = " ".join(words[verb_index+1:])
                                role_info["object"] = object_text
                            
                            results.append(role_info)
                    else:
                        # 如果没有找到明确的动词，就直接分割主谓宾
                        if len(words) >= 3:
                            third = len(words) // 3
                            results.append({
                                "subject": " ".join(words[:third]),
                                "verb": " ".join(words[third:2*third]),
                                "object": " ".join(words[2*third:]),
                                "text": text
                            })
                        else:
                            # 句子太短，无法进行有效分割
                            results.append({"text": text})
            
            return results
                
        return analyze
    
    def _start_model_manager(self) -> None:
        """启动模型管理线程，定期检查并卸载不活跃的模型"""
        if not self.config.get('dynamic_unloading', True):
            return
            
        def model_manager():
            while True:
                try:
                    # 检查中文模型
                    if (self.zh_srl and hasattr(self.zh_srl, 'is_loaded') and 
                        self.zh_srl.is_loaded and 
                        time.time() - self.zh_srl.last_used > self.config.get('unload_timeout', 300)):
                        logger.info("中文SRL模型长时间未使用，正在卸载")
                        self.zh_srl.unload()
                    
                    # 检查英文模型
                    if (self.en_srl and hasattr(self.en_srl, 'is_loaded') and 
                        self.en_srl.is_loaded and 
                        time.time() - self.en_srl.last_used > self.config.get('unload_timeout', 300)):
                        logger.info("英文SRL模型长时间未使用，正在卸载")
                        self.en_srl.unload()
                        
                except Exception as e:
                    logger.error(f"模型管理线程异常: {str(e)}")
                
                # 每分钟检查一次
                time.sleep(60)
        
        # 启动后台线程
        threading.Thread(target=model_manager, daemon=True).start()
    
    def get_zh_srl(self, use_model: bool = False):
        """
        按需加载中文模型
        
        参数:
            use_model: 是否使用模型（True）或备用方案（False）
        """
        if use_model and TRANSFORMERS_AVAILABLE and not isinstance(self.zh_srl, MemoryOptimizedSRLPipeline):
            logger.info("加载中文SRL模型...")
            try:
                self.zh_srl = MemoryOptimizedSRLPipeline(
                    **self._zh_srl_config
                )
            except Exception as e:
                logger.error(f"加载中文SRL模型失败: {str(e)}")
                logger.info("退回使用中文备用SRL分析方案")
                self.zh_srl = self._create_fallback_srl("zh")
        return self.zh_srl
    
    def get_en_srl(self, use_model: bool = False):
        """
        按需加载英文模型
        
        参数:
            use_model: 是否使用模型（True）或备用方案（False）
        """
        if use_model and TRANSFORMERS_AVAILABLE and not isinstance(self.en_srl, MemoryOptimizedSRLPipeline):
            logger.info("加载英文SRL模型...")
            try:
                self.en_srl = MemoryOptimizedSRLPipeline(
                    **self._en_srl_config
                )
            except Exception as e:
                logger.error(f"加载英文SRL模型失败: {str(e)}")
                logger.info("退回使用英文备用SRL分析方案")
                self.en_srl = self._create_fallback_srl("en")
        return self.en_srl
    
    @track_memory("srl_processing")
    def annotate(self, text: str, lang: str = "auto", use_model: bool = False) -> List[Dict[str, Any]]:
        """
        分析文本的语义角色
        
        参数:
            text: 待分析的文本
            lang: 语言代码 ("zh", "en" 或 "auto")
            use_model: 是否使用模型，False表示使用备用方案
            
        返回:
            语义角色标注结果列表
        """
        if not text or len(text.strip()) == 0:
            return []
            
        # 自动检测语言
        if lang == "auto":
            # 简单语言检测：超过50%的字符是ASCII则视为英文
            ascii_ratio = sum(ord(c) < 128 for c in text) / len(text)
            lang = "en" if ascii_ratio > 0.5 else "zh"
        
        # 检查缓存
        cached_result = self.cache.get(text, lang)
        if cached_result:
            return cached_result
        
        # 选择适当的分析管道
        try:
            if lang == "zh":
                pipe = self.get_zh_srl(use_model)
            else:
                pipe = self.get_en_srl(use_model)
                
            # 分析语义角色
            raw_result = pipe(text)
            
            # 处理结果
            if lang == "zh":
                # 处理中文模型输出
                processed_result = self._process_zh_result(text, raw_result)
            else:
                # 处理英文模型输出
                processed_result = self._process_en_result(text, raw_result)
            
            # 缓存结果
            self.cache.set(text, lang, processed_result)
            
            return processed_result
                
        except Exception as e:
            logger.error(f"语义角色标注失败: {str(e)}")
            # 使用备用方案
            fallback = self._create_fallback_srl(lang)
            result = fallback(text)
            return result
    
    def _process_zh_result(self, text: str, raw_result: Any) -> List[Dict[str, Any]]:
        """处理中文SRL模型输出，转换为标准格式"""
        processed = []
        
        # 根据实际模型输出格式调整此处理逻辑
        # 当前为一个示例实现
        if isinstance(raw_result, list):
            for item in raw_result:
                if isinstance(item, dict):
                    # 提取角色信息
                    role_info = {
                        "text": text
                    }
                    
                    # 从raw_result中提取角色信息（具体字段取决于模型输出）
                    for key, value in item.items():
                        # 跳过内部特殊字段
                        if key.startswith("_") or key in ["score", "index"]:
                            continue
                        role_info[key] = value
                    
                    processed.append(role_info)
        
        # 如果无法解析结果，使用备用处理
        if not processed:
            fallback = self._create_fallback_srl("zh")
            processed = fallback(text)
        
        return processed
    
    def _process_en_result(self, text: str, raw_result: Any) -> List[Dict[str, Any]]:
        """处理英文SRL模型输出，转换为标准格式"""
        processed = []
        
        # 根据实际模型输出格式调整此处理逻辑
        # 当前为一个示例实现
        try:
            if isinstance(raw_result, list):
                for item in raw_result:
                    if isinstance(item, dict):
                        # 提取角色信息
                        role_info = {
                            "text": text
                        }
                        
                        # 从raw_result中提取角色信息（具体字段取决于模型输出）
                        for key, value in item.items():
                            # 跳过内部特殊字段
                            if key.startswith("_") or key in ["score", "index"]:
                                continue
                            role_info[key] = value
                        
                        processed.append(role_info)
            
            # 如果无法解析结果，使用备用处理
            if not processed:
                fallback = self._create_fallback_srl("en")
                processed = fallback(text)
        except Exception as e:
            logger.error(f"处理英文SRL结果失败: {str(e)}")
            fallback = self._create_fallback_srl("en")
            processed = fallback(text)
            
        return processed
    
    def annotate_batch(self, texts: List[str], lang: str = "auto", use_model: bool = False) -> List[List[Dict[str, Any]]]:
        """批量分析多个文本的语义角色"""
        return [self.annotate(text, lang, use_model) for text in texts]
        
    def annotate_subtitles(self, subtitle_segments: List[Dict[str, Any]], text_key: str = "text", 
                           lang: str = "auto", use_model: bool = False) -> List[Dict[str, Any]]:
        """
        分析字幕分段的语义角色
        
        参数:
            subtitle_segments: 字幕分段列表，每个分段为包含文本的字典
            text_key: 字典中文本的键名
            lang: 语言代码
            use_model: 是否使用模型，False表示使用备用方案
            
        返回:
            带有语义角色分析结果的分段列表
        """
        results = []
        
        for segment in subtitle_segments:
            text = segment.get(text_key, "")
            srl_result = self.annotate(text, lang, use_model)
            
            # 创建新的分段副本并添加语义角色分析结果
            new_segment = segment.copy()
            new_segment["srl"] = srl_result
            results.append(new_segment)
            
        return results
    
    def extract_events(self, srl_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        从SRL结果中提取事件
        
        参数:
            srl_results: SRL分析结果列表
            
        返回:
            事件列表，每个事件包含主体、动作和客体
        """
        events = []
        
        for item in srl_results:
            # 尝试提取主语、谓语和宾语
            subject = item.get("subject", "")
            verb = item.get("verb", "")
            object_text = item.get("object", "")
            
            # 只有当谓语存在时才认为是有效事件
            if verb:
                event = {
                    "subject": subject,
                    "action": verb,
                    "object": object_text,
                    "text": item.get("text", "")
                }
                events.append(event)
        
        return events


# 创建全局单例实例
srl_annotator = SemanticRoleLabeler()

def annotate_text(text: str, lang: str = "auto", use_model: bool = False) -> List[Dict[str, Any]]:
    """便捷函数，用于分析文本语义角色"""
    return srl_annotator.annotate(text, lang, use_model)

def annotate_batch(texts: List[str], lang: str = "auto", use_model: bool = False) -> List[List[Dict[str, Any]]]:
    """便捷函数，用于批量分析文本语义角色"""
    return [srl_annotator.annotate(text, lang, use_model) for text in texts]

def annotate_subtitles(subtitle_segments: List[Dict[str, Any]], lang: str = "auto", use_model: bool = False) -> List[Dict[str, Any]]:
    """便捷函数，用于分析字幕语义角色"""
    return srl_annotator.annotate_subtitles(subtitle_segments, "text", lang, use_model)

def extract_events(srl_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """便捷函数，用于从SRL结果中提取事件"""
    return srl_annotator.extract_events(srl_results)


if __name__ == "__main__":
    # 简单测试
    logging.basicConfig(level=logging.INFO)
    
    print("中文语义角色标注测试:")
    zh_text = "小明在公园里遇见了他的朋友小红"
    zh_result = annotate_text(zh_text, "zh")
    print(f"文本: {zh_text}")
    print(f"结果: {zh_result}")
    
    print("\n英文语义角色标注测试:")
    en_text = "John met his friend Mary in the park yesterday"
    en_result = annotate_text(en_text, "en")
    print(f"文本: {en_text}")
    print(f"结果: {en_result}")
    
    print("\n提取事件测试:")
    events = extract_events(zh_result)
    print(f"事件: {events}") 