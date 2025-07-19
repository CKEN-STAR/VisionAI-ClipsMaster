#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster - 内容过滤防火墙

负责检测和过滤不当内容，确保系统生成的内容合规、安全。
实现多级过滤：
1. 基于关键词的精确匹配
2. 基于语义的内容分析（使用BERT或其他NLP模型）
"""

import os
import re
import sys
import json
import logging
import importlib
from pathlib import Path
from typing import List, Set, Dict, Tuple, Optional, Union, Any

# 获取项目根目录
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

# 尝试导入项目模块
try:
    from src.utils.log_handler import get_logger
    logger = get_logger("content_filter")
except ImportError:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger("content_filter")

# 定义内容违规异常
class ContentViolationError(Exception):
    """内容违规异常"""
    def __init__(self, message: str, term: str = "", category: str = "", severity: int = 2):
        """
        初始化内容违规异常
        
        Args:
            message: 异常信息
            term: 触发违规的词汇或内容
            category: 违规类别（暴力/色情/政治等）
            severity: 严重程度 (1-轻微, 2-中等, 3-严重)
        """
        self.term = term
        self.category = category
        self.severity = severity
        self.violation_info = {
            "term": term,
            "category": category,
            "severity": severity
        }
        super().__init__(message)


class ContentFilter:
    """内容过滤防火墙"""
    
    def __init__(self, blacklist_path: str = None, 
                 enable_semantic: bool = True,
                 semantic_threshold: float = 0.85,
                 lang: str = "auto"):
        """
        初始化内容过滤器
        
        Args:
            blacklist_path: 黑名单文件路径，默认使用legal/forbidden_terms.txt
            enable_semantic: 是否启用语义分析，默认启用
            semantic_threshold: 语义分析阈值，高于此值将触发内容违规，默认0.85
            lang: 使用语言，可为"auto", "zh", "en"
        """
        self.blacklist: Set[str] = set()
        self.categories: Dict[str, List[str]] = {}
        self.enable_semantic = enable_semantic
        self.semantic_threshold = semantic_threshold
        self.lang = lang
        
        # 加载黑名单
        if blacklist_path is None:
            blacklist_path = os.path.join(PROJECT_ROOT, "legal", "forbidden_terms.txt")
        self._load_blacklist(blacklist_path)
        
        # 初始化语义分析模型
        self.semantic_model = None
        if self.enable_semantic:
            self._init_semantic_model()
        
        logger.info(f"内容过滤防火墙初始化完成，关键词黑名单数量: {len(self.blacklist)}")
    
    def _load_blacklist(self, blacklist_path: str) -> None:
        """
        加载黑名单
        
        Args:
            blacklist_path: 黑名单文件路径
        """
        try:
            if not os.path.exists(blacklist_path):
                logger.warning(f"黑名单文件不存在: {blacklist_path}，使用内置默认黑名单")
                # 创建一个最小化的内置黑名单
                self.blacklist = {"violence", "porn", "hate", "暴力", "色情", "歧视"}
                return
            
            current_category = "general"
            with open(blacklist_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # 跳过空行和注释行
                    if not line or line.startswith('#'):
                        # 检查是否是分类注释
                        if line.startswith('# ') and len(line) > 2:
                            current_category = line[2:].strip()
                            if current_category not in self.categories:
                                self.categories[current_category] = []
                        continue
                    
                    # 添加到黑名单和分类
                    self.blacklist.add(line.lower())
                    if current_category not in self.categories:
                        self.categories[current_category] = []
                    self.categories[current_category].append(line.lower())
            
            logger.info(f"已加载黑名单，共 {len(self.blacklist)} 个词汇，{len(self.categories)} 个分类")
        
        except Exception as e:
            logger.error(f"加载黑名单失败: {str(e)}")
            # 创建一个最小化的内置黑名单
            self.blacklist = {"violence", "porn", "hate", "暴力", "色情", "歧视"}
    
    def _init_semantic_model(self) -> None:
        """初始化语义分析模型"""
        try:
            # 尝试导入transformers
            import_transformers = importlib.util.find_spec("transformers")
            
            if import_transformers:
                logger.info("正在初始化语义分析模型...")
                self.has_transformers = True
                
                # 延迟导入，避免启动时加载
                # 实际使用时会在第一次需要语义分析时加载
                self.transformer_modules = {
                    "available": True,
                    "loaded": False,
                    "model": None,
                    "tokenizer": None
                }
            else:
                logger.warning("未找到transformers库，语义分析功能将被禁用")
                self.has_transformers = False
                self.enable_semantic = False
        except Exception as e:
            logger.warning(f"初始化语义分析模型失败: {str(e)}，将使用关键词匹配")
            self.has_transformers = False
            self.enable_semantic = False
    
    def _load_model_if_needed(self) -> bool:
        """
        按需加载模型
        
        Returns:
            bool: 加载是否成功
        """
        if not self.has_transformers or not self.enable_semantic:
            return False
            
        if self.transformer_modules.get("loaded", False):
            return True
            
        try:
            # 导入必要的库
            from transformers import AutoModelForSequenceClassification, AutoTokenizer
            
            # 根据语言选择合适的模型
            if self.lang == "zh" or (self.lang == "auto" and self._is_chinese_dominant):
                # 中文模型
                model_name = "uer/roberta-base-finetuned-chinanews-chinese"
                logger.info(f"加载中文语义分析模型: {model_name}")
            else:
                # 英文模型
                model_name = "distilbert-base-uncased-finetuned-sst-2-english"
                logger.info(f"加载英文语义分析模型: {model_name}")
            
            # 使用小型模型以降低资源消耗
            self.transformer_modules["tokenizer"] = AutoTokenizer.from_pretrained(model_name)
            self.transformer_modules["model"] = AutoModelForSequenceClassification.from_pretrained(model_name)
            self.transformer_modules["loaded"] = True
            
            logger.info("语义分析模型加载完成")
            return True
        except Exception as e:
            logger.error(f"加载模型失败: {str(e)}")
            self.enable_semantic = False
            return False
    
    @property
    def _is_chinese_dominant(self) -> bool:
        """判断是否以中文为主"""
        # 如果明确指定语言，返回对应结果
        if self.lang == "zh":
            return True
        elif self.lang == "en":
            return False
        
        # 自动检测基于项目配置
        try:
            # 读取激活模型配置
            model_config_path = os.path.join(PROJECT_ROOT, "configs", "models", "active_model.yaml")
            if os.path.exists(model_config_path):
                import yaml
                with open(model_config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    if config and 'language' in config:
                        return config['language'] == 'zh'
        except Exception:
            pass
        
        # 默认返回False（使用英文模型）
        return False
    
    def filter_script(self, text: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        过滤剧本文本
        
        Args:
            text: 要过滤的文本
            
        Returns:
            Tuple[bool, Optional[Dict]]: (是否通过过滤, 违规信息)
            
        Raises:
            ContentViolationError: 当检测到违规内容时
        """
        # 如果文本为空，直接通过
        if not text or not text.strip():
            return True, None
        
        # 1. 关键词过滤
        for term in self.blacklist:
            # 使用正则表达式查找完整的词
            pattern = fr'\b{re.escape(term)}\b'
            if re.search(pattern, text, re.I):
                # 找到违规词汇
                category = self._get_term_category(term)
                violation_info = {
                    "term": term,
                    "match_type": "keyword",
                    "category": category,
                    "severity": 2
                }
                raise ContentViolationError(f"包含违禁词汇: {term}", term, category)
        
        # 2. 语义分析（如果启用）
        if self.enable_semantic and len(text.strip()) > 10:
            is_violation, semantic_result = self._semantic_analysis(text)
            if is_violation:
                violation_info = {
                    "term": semantic_result.get("flagged_content", ""),
                    "match_type": "semantic",
                    "category": semantic_result.get("category", "unknown"),
                    "severity": semantic_result.get("severity", 1),
                    "confidence": semantic_result.get("confidence", 0)
                }
                raise ContentViolationError(
                    f"语义违规: {semantic_result.get('category', '未知类别')}",
                    semantic_result.get("flagged_content", ""),
                    semantic_result.get("category", "unknown"),
                    semantic_result.get("severity", 1)
                )
        
        # 通过所有过滤
        return True, None
    
    def _get_term_category(self, term: str) -> str:
        """
        获取词汇所属分类
        
        Args:
            term: 词汇
            
        Returns:
            str: 分类名称
        """
        for category, terms in self.categories.items():
            if term.lower() in [t.lower() for t in terms]:
                return category
        return "general"
    
    def _semantic_analysis(self, text: str) -> Tuple[bool, Dict[str, Any]]:
        """
        语义分析
        
        Args:
            text: 要分析的文本
            
        Returns:
            Tuple[bool, Dict]: (是否违规, 分析结果)
        """
        result = {
            "flagged": False,
            "category": "unknown",
            "severity": 0,
            "confidence": 0,
            "flagged_content": ""
        }
        
        # 如果没有启用语义分析或文本太短，返回安全
        if not self.enable_semantic or len(text) < 10:
            return False, result
        
        # 尝试使用transformers进行分析
        if self.has_transformers:
            if not self._load_model_if_needed():
                # 模型加载失败，回退到简单分析
                return self._simple_semantic_analysis(text)
            
            try:
                # 使用加载的模型进行分析
                tokenizer = self.transformer_modules["tokenizer"]
                model = self.transformer_modules["model"]
                
                # 将长文本分段
                max_length = tokenizer.model_max_length - 10  # 留一些余量
                segments = [text[i:i+max_length] for i in range(0, len(text), max_length)]
                
                # 分析每个段落
                flagged = False
                max_confidence = 0
                flagged_segment = ""
                
                for segment in segments:
                    inputs = tokenizer(segment, return_tensors="pt", truncation=True)
                    import torch
                    with torch.no_grad():
                        outputs = model(**inputs)
                    
                    # 获取预测结果
                    predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
                    negative_score = predictions[0][0].item()  # 假设0是负面
                    
                    # 如果负面分数超过阈值，标记为违规
                    if negative_score > self.semantic_threshold:
                        flagged = True
                        if negative_score > max_confidence:
                            max_confidence = negative_score
                            flagged_segment = segment
                
                if flagged:
                    result = {
                        "flagged": True,
                        "category": "inappropriate_content",
                        "severity": 1 if max_confidence < 0.92 else 2,
                        "confidence": max_confidence,
                        "flagged_content": flagged_segment[:100] + "..." if len(flagged_segment) > 100 else flagged_segment
                    }
                    return True, result
                
                return False, result
                
            except Exception as e:
                logger.error(f"语义分析错误: {str(e)}")
                # 回退到简单分析
                return self._simple_semantic_analysis(text)
        else:
            # 使用简单的分析
            return self._simple_semantic_analysis(text)
    
    def _simple_semantic_analysis(self, text: str) -> Tuple[bool, Dict[str, Any]]:
        """
        简单的语义分析（不使用大型模型）
        
        Args:
            text: 要分析的文本
            
        Returns:
            Tuple[bool, Dict]: (是否违规, 分析结果)
        """
        # 这是一个非常简单的分析，仅用于没有更高级模型时的回退选项
        text = text.lower()
        result = {
            "flagged": False,
            "category": "unknown",
            "severity": 0,
            "confidence": 0,
            "flagged_content": ""
        }
        
        # 组合词检测（检测可能的词组合，这些组合在单词检测中可能被忽略）
        bad_combinations = [
            (["暴力", "血腥", "打斗"], "violence"),
            (["性", "裸露", "情色"], "adult_content"),
            (["政府", "颠覆", "政治"], "political_sensitive"),
            (["赌博", "毒品", "犯罪"], "illegal_activity")
        ]
        
        for word_list, category in bad_combinations:
            # 如果文本中包含多个关键词，可能是违规内容
            matches = sum(1 for word in word_list if word in text)
            if matches >= 2:  # 如果至少匹配两个词
                context = self._extract_context(text, word_list)
                result = {
                    "flagged": True,
                    "category": category,
                    "severity": 1,  # 低严重度
                    "confidence": min(0.7 + (matches * 0.1), 0.9),  # 基于匹配数量增加置信度
                    "flagged_content": context
                }
                return True, result
        
        # 检查敏感话题频率
        sensitive_topics = ["政治", "敏感", "宗教", "民族", "war", "drugs"]
        topic_count = sum(text.count(topic) for topic in sensitive_topics)
        
        if topic_count >= 3:  # 如果敏感话题出现频率较高
            context = self._extract_context(text, sensitive_topics)
            result = {
                "flagged": True,
                "category": "sensitive_topics",
                "severity": 1,
                "confidence": min(0.6 + (topic_count * 0.05), 0.85),
                "flagged_content": context
            }
            return True, result
        
        return False, result
    
    def _extract_context(self, text: str, keywords: List[str]) -> str:
        """
        提取关键词上下文
        
        Args:
            text: 文本
            keywords: 关键词列表
            
        Returns:
            str: 包含关键词的上下文
        """
        for keyword in keywords:
            if keyword in text:
                index = text.find(keyword)
                start = max(0, index - 20)
                end = min(len(text), index + len(keyword) + 20)
                return text[start:end].strip() + "..."
        
        return ""
    
    def is_safe_content(self, text: str) -> bool:
        """
        判断内容是否安全（不抛出异常的版本）
        
        Args:
            text: 要检查的文本
            
        Returns:
            bool: 内容是否安全
        """
        try:
            self.filter_script(text)
            return True
        except ContentViolationError:
            return False
    
    def get_violations(self, text: str) -> List[Dict[str, Any]]:
        """
        获取文本中的所有违规内容
        
        Args:
            text: 要检查的文本
            
        Returns:
            List[Dict]: 违规信息列表
        """
        violations = []
        
        # 关键词检查
        for term in self.blacklist:
            pattern = fr'\b{re.escape(term)}\b'
            matches = re.finditer(pattern, text, re.I)
            for match in matches:
                category = self._get_term_category(term)
                violations.append({
                    "term": term,
                    "match_type": "keyword",
                    "category": category,
                    "position": match.start(),
                    "context": text[max(0, match.start()-20):min(len(text), match.end()+20)],
                    "severity": 2
                })
        
        # 语义分析
        if self.enable_semantic and len(text) > 10:
            is_violation, semantic_result = self._semantic_analysis(text)
            if is_violation:
                violations.append({
                    "term": semantic_result.get("flagged_content", ""),
                    "match_type": "semantic",
                    "category": semantic_result.get("category", "unknown"),
                    "context": semantic_result.get("flagged_content", ""),
                    "confidence": semantic_result.get("confidence", 0),
                    "severity": semantic_result.get("severity", 1),
                })
        
        return violations


def load_blacklist(file_path: str = None) -> List[str]:
    """
    加载黑名单
    
    Args:
        file_path: 黑名单文件路径，默认使用legal/forbidden_terms.txt
        
    Returns:
        List[str]: 黑名单词汇列表
    """
    if file_path is None:
        file_path = os.path.join(PROJECT_ROOT, "legal", "forbidden_terms.txt")
    
    try:
        if not os.path.exists(file_path):
            logger.warning(f"黑名单文件不存在: {file_path}")
            return []
        
        blacklist = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    blacklist.append(line)
        
        return blacklist
    except Exception as e:
        logger.error(f"加载黑名单失败: {str(e)}")
        return []


# 快速测试
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("内容过滤防火墙自测")
    
    # 创建内容过滤器
    content_filter = ContentFilter()
    
    # 测试文本
    safe_text = "这是一个正常的句子，描述了生活中的日常场景。"
    unsafe_text = "这段内容充满了暴力描写，包括血腥场景。"
    borderline_text = "这段内容有些敏感，提到了一些政治话题。"
    
    # 测试过滤
    logger.info(f"安全文本测试: {'通过' if content_filter.is_safe_content(safe_text) else '不通过'}")
    logger.info(f"不安全文本测试: {'通过' if content_filter.is_safe_content(unsafe_text) else '不通过'}")
    logger.info(f"边缘文本测试: {'通过' if content_filter.is_safe_content(borderline_text) else '不通过'}")
    
    # 获取违规详情
    violations = content_filter.get_violations(unsafe_text)
    if violations:
        logger.info(f"检测到 {len(violations)} 个违规:")
        for v in violations:
            logger.info(f"  - 类型: {v['match_type']}, 词汇: {v['term']}, 类别: {v['category']}") 