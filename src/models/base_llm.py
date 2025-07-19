#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
大语言模型基类 - 定义所有模型通用接口
"""

import os
import sys
import abc
import time
import logging
from typing import Dict, List, Any, Optional, Union
from pathlib import Path

from configs.model_config import ModelConfig

# 配置日志
logger = logging.getLogger(__name__)

# 导入GPU相关模块
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("PyTorch未安装，GPU加速功能将不可用")

try:
    from ui.hardware.gpu_detector import get_gpu_detector
    GPU_DETECTOR_AVAILABLE = True
except ImportError:
    GPU_DETECTOR_AVAILABLE = False
    logger.warning("GPU检测器不可用")

class BaseLLM(abc.ABC):
    """
    大语言模型抽象基类，定义通用接口
    
    所有具体模型实现必须继承此类并实现必要的方法
    """
    
    def __init__(self, config: ModelConfig):
        """
        初始化模型

        Args:
            config: 模型配置对象
        """
        self.config = config
        self.model = None
        self.tokenizer = None
        self.is_loaded = False
        self.model_info = {
            "name": config.model_info.get("name", "unknown"),
            "language": config.model_info.get("language", "unknown"),
            "size": config.model_info.get("size", "unknown"),
            "quantization": config.quantization,
            "context_length": config.context_length
        }

        # GPU加速相关初始化
        self.gpu_enabled = False
        self.device = 'cpu'
        self.gpu_info = None
        self.use_mixed_precision = False

        # 初始化GPU支持
        self._init_gpu_support()

        logger.info(f"初始化模型: {self.model_info['name']} ({self.model_info['language']})")
        if self.gpu_enabled:
            logger.info(f"✅ GPU加速已启用，设备: {self.device}")
        else:
            logger.info("⚠️ GPU加速未启用，使用CPU模式")
        
    @abc.abstractmethod
    def load(self) -> bool:
        """
        加载模型到内存
        
        Returns:
            加载是否成功
        """
        pass
        
    @abc.abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """
        生成文本响应
        
        Args:
            prompt: 输入提示词
            **kwargs: 其他生成参数
            
        Returns:
            生成的文本响应
        """
        pass
    
    @abc.abstractmethod
    def tokenize(self, text: str) -> List[int]:
        """
        对输入文本进行分词
        
        Args:
            text: 输入文本
            
        Returns:
            分词结果
        """
        pass
    
    def unload(self) -> bool:
        """
        从内存卸载模型
        
        Returns:
            卸载是否成功
        """
        if not self.is_loaded:
            return True
            
        try:
            # 清除模型和分词器
            self.model = None
            self.tokenizer = None
            
            # 主动触发垃圾回收
            import gc
            gc.collect()
            
            self.is_loaded = False
            logger.info(f"已卸载模型: {self.model_info['name']}")
            return True
        except Exception as e:
            logger.error(f"卸载模型失败: {str(e)}")
            return False
            
    def is_ready(self) -> bool:
        """
        检查模型是否已加载并可用
        
        Returns:
            模型是否可用
        """
        return self.is_loaded and self.model is not None
            
    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息

        Returns:
            模型信息字典
        """
        return self.model_info

    def _init_gpu_support(self):
        """初始化GPU支持"""
        try:
            if not TORCH_AVAILABLE:
                logger.info("PyTorch不可用，跳过GPU初始化")
                return

            # 检测GPU
            if GPU_DETECTOR_AVAILABLE:
                gpu_detector = get_gpu_detector()
                self.gpu_info = gpu_detector.detect_gpus()
                self.device = gpu_detector.get_best_device()
            else:
                # 备用GPU检测
                if torch.cuda.is_available():
                    self.device = 'cuda'
                else:
                    self.device = 'cpu'

            # 设置GPU状态
            if self.device != 'cpu':
                self.gpu_enabled = True

                # 检查是否支持混合精度
                if self.device == 'cuda':
                    try:
                        # 检查GPU是否支持FP16
                        device_props = torch.cuda.get_device_properties(0)
                        if device_props.major >= 7:  # Volta架构及以上支持Tensor Cores
                            self.use_mixed_precision = True
                            logger.info("✅ 支持混合精度训练 (FP16)")
                    except Exception:
                        pass

                logger.info(f"GPU检测成功，使用设备: {self.device}")
            else:
                logger.info("未检测到可用GPU，使用CPU模式")

        except Exception as e:
            logger.error(f"GPU初始化失败: {str(e)}")
            self.gpu_enabled = False
            self.device = 'cpu'

    def load_to_gpu(self) -> bool:
        """
        将模型加载到GPU

        Returns:
            bool: 是否成功加载到GPU
        """
        try:
            if not self.gpu_enabled or not self.is_loaded:
                logger.warning("GPU不可用或模型未加载")
                return False

            if self.model is None:
                logger.error("模型对象为空")
                return False

            logger.info(f"正在将模型加载到GPU: {self.device}")

            # 将模型移动到GPU
            self.model = self.model.to(self.device)

            # 如果支持混合精度，转换为半精度
            if self.use_mixed_precision and self.device == 'cuda':
                self.model = self.model.half()
                logger.info("✅ 模型已转换为FP16精度")

            # 验证GPU加载
            if hasattr(self.model, 'device'):
                actual_device = str(self.model.device)
                if self.device in actual_device:
                    logger.info(f"✅ 模型成功加载到GPU: {actual_device}")
                    return True
                else:
                    logger.error(f"GPU加载验证失败: 期望{self.device}, 实际{actual_device}")
                    return False
            else:
                logger.info("✅ 模型已移动到GPU (无法验证设备)")
                return True

        except Exception as e:
            logger.error(f"GPU加载失败: {str(e)}")
            return False

    def inference_gpu(self, input_text: str, **kwargs) -> str:
        """
        GPU加速推理

        Args:
            input_text: 输入文本
            **kwargs: 其他推理参数

        Returns:
            str: 推理结果
        """
        try:
            if not self.gpu_enabled:
                logger.warning("GPU不可用，使用CPU推理")
                return self.inference(input_text, **kwargs)

            # 确保模型在GPU上
            if not self._ensure_model_on_gpu():
                logger.warning("无法确保模型在GPU上，回退到CPU")
                return self.inference(input_text, **kwargs)

            logger.debug(f"开始GPU推理，设备: {self.device}")
            start_time = time.time()

            # 使用混合精度推理
            if self.use_mixed_precision and self.device == 'cuda':
                with torch.cuda.amp.autocast():
                    result = self._do_inference_gpu(input_text, **kwargs)
            else:
                result = self._do_inference_gpu(input_text, **kwargs)

            inference_time = time.time() - start_time
            logger.debug(f"GPU推理完成，耗时: {inference_time:.3f}秒")

            return result

        except Exception as e:
            logger.error(f"GPU推理失败: {str(e)}")
            logger.info("回退到CPU推理")
            return self.inference(input_text, **kwargs)

    def _ensure_model_on_gpu(self) -> bool:
        """确保模型在GPU上"""
        try:
            if not self.gpu_enabled or self.model is None:
                return False

            # 检查模型是否已在GPU上
            if hasattr(self.model, 'device'):
                current_device = str(self.model.device)
                if self.device not in current_device:
                    logger.info("模型不在GPU上，正在移动...")
                    return self.load_to_gpu()

            return True

        except Exception as e:
            logger.error(f"检查模型设备失败: {str(e)}")
            return False

    def _do_inference_gpu(self, input_text: str, **kwargs) -> str:
        """
        执行GPU推理（子类需要实现）

        Args:
            input_text: 输入文本
            **kwargs: 其他参数

        Returns:
            str: 推理结果
        """
        # 默认实现，子类应该重写此方法
        return self.inference(input_text, **kwargs)

    def get_gpu_memory_usage(self) -> Dict[str, float]:
        """
        获取GPU内存使用情况

        Returns:
            Dict[str, float]: 内存使用信息 (MB)
        """
        try:
            if not self.gpu_enabled or self.device == 'cpu':
                return {'total': 0, 'allocated': 0, 'cached': 0, 'free': 0}

            if self.device == 'cuda' and torch.cuda.is_available():
                device_id = 0  # 默认使用第一个GPU
                total_memory = torch.cuda.get_device_properties(device_id).total_memory
                allocated_memory = torch.cuda.memory_allocated(device_id)
                cached_memory = torch.cuda.memory_reserved(device_id)

                return {
                    'total': total_memory / (1024 * 1024),
                    'allocated': allocated_memory / (1024 * 1024),
                    'cached': cached_memory / (1024 * 1024),
                    'free': (total_memory - allocated_memory) / (1024 * 1024)
                }
            else:
                return {'total': 0, 'allocated': 0, 'cached': 0, 'free': 0}

        except Exception as e:
            logger.error(f"获取GPU内存使用失败: {str(e)}")
            return {'total': 0, 'allocated': 0, 'cached': 0, 'free': 0}

    def clear_gpu_cache(self):
        """清理GPU缓存"""
        try:
            if self.gpu_enabled and self.device == 'cuda':
                torch.cuda.empty_cache()
                logger.info("✅ GPU缓存已清理")
        except Exception as e:
            logger.error(f"清理GPU缓存失败: {str(e)}")


# 模型缓存
_model_cache = {}

# 增强版模型加载器
_enhanced_loader = None

def get_enhanced_loader():
    """获取增强版模型加载器实例"""
    global _enhanced_loader
    if _enhanced_loader is None:
        try:
            from src.core.enhanced_model_loader import get_enhanced_model_loader
            _enhanced_loader = get_enhanced_model_loader(memory_limit=3800)
            logger.info("增强版模型加载器初始化成功")
        except ImportError as e:
            logger.warning(f"增强版模型加载器不可用: {e}")
            _enhanced_loader = None
    return _enhanced_loader

def get_llm_for_language(language: str) -> Optional[BaseLLM]:
    """
    获取特定语言的LLM实例 - 增强版实现

    Args:
        language: 语言代码，如 'zh' 或 'en'

    Returns:
        对应语言的LLM实例，如果不存在则返回None
    """
    global _model_cache

    # 优先使用增强版模型加载器
    enhanced_loader = get_enhanced_loader()
    if enhanced_loader:
        try:
            logger.info(f"使用增强版加载器获取{language}语言模型")

            # 切换到指定语言
            if enhanced_loader.switch_language(language):
                model_object = enhanced_loader.get_current_model()
                if model_object:
                    logger.info(f"增强版加载器成功获取{language}语言模型")
                    return model_object

            logger.warning(f"增强版加载器获取{language}语言模型失败，使用传统方法")

        except Exception as e:
            logger.error(f"增强版加载器异常: {str(e)}，使用传统方法")

    # 回退到传统缓存方法
    logger.info(f"使用传统方法获取{language}语言模型")

    # 检查缓存
    if language in _model_cache and _model_cache[language] is not None:
        return _model_cache[language]

    try:
        if language == 'zh':
            # 懒加载中文模型
            from src.models.qwen import QwenLLM
            from configs.model_config import get_qwen_config

            config = get_qwen_config()
            if not config:
                logger.error("无法获取Qwen模型配置")
                return None

            model = QwenLLM(config)
            _model_cache['zh'] = model
            return model

        elif language == 'en':
            # 懒加载英文模型
            from src.models.mistral import MistralLLM
            from configs.model_config import get_mistral_config

            config = get_mistral_config()
            if not config:
                logger.error("无法获取Mistral模型配置")
                return None

            model = MistralLLM(config)
            _model_cache['en'] = model
            return model

        else:
            # 默认返回中文模型
            logger.warning(f"未知语言: {language}，默认使用中文模型")
            return get_llm_for_language('zh')

    except Exception as e:
        logger.error(f"获取{language}语言模型失败: {str(e)}")
        return None