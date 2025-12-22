#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
RealAIEngine适配器 - 将RealAIEngine适配为BaseLLM接口

这个适配器允许RealAIEngine与现有的剧本分析模块无缝集成
"""

import logging
from typing import Dict, List, Any, Optional

from src.models.base_llm import BaseLLM
from configs.model_config import ModelConfig

logger = logging.getLogger(__name__)


class RealAIEngineAdapter(BaseLLM):
    """
    RealAIEngine适配器类
    
    将RealAIEngine的接口适配为BaseLLM接口，使其可以在现有代码中使用
    """
    
    def __init__(self, language: str = "zh"):
        """
        初始化适配器
        
        Args:
            language: 语言代码（zh或en）
        """
        # 创建一个简单的配置对象
        config = ModelConfig(
            model_info={
                "name": f"RealAIEngine-{language}",
                "language": language,
                "size": "7B",
            },
            quantization="Q4_K_M",
            context_length=2048
        )
        
        # 调用父类初始化
        super().__init__(config)
        
        self.language = language
        self.engine = None
        
        logger.info(f"初始化RealAIEngine适配器，语言: {language}")
    
    def load(self) -> bool:
        """
        加载RealAIEngine

        Returns:
            加载是否成功
        """
        try:
            if self.is_loaded:
                logger.info("RealAIEngine已加载")
                return True

            # 导入并创建RealAIEngine实例
            from src.core.real_ai_engine import RealAIEngine

            logger.info(f"正在加载RealAIEngine（{self.language}）...")
            self.engine = RealAIEngine(config_path=None)

            # 加载指定语言的模型
            if not self.engine.load_model(self.language):
                logger.error(f"加载{self.language}语言模型失败")
                return False

            self.is_loaded = True
            logger.info(f"✅ RealAIEngine加载成功（{self.language}）")
            return True

        except Exception as e:
            logger.error(f"加载RealAIEngine失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def generate(self, prompt: str, **kwargs) -> str:
        """
        生成文本响应
        
        Args:
            prompt: 输入提示词
            **kwargs: 其他生成参数
            
        Returns:
            生成的文本响应
        """
        try:
            # 确保引擎已加载
            if not self.is_loaded:
                if not self.load():
                    logger.error("RealAIEngine未加载，无法生成响应")
                    return ""
            
            # 使用RealAIEngine生成响应（透传可选参数，例如 json_only）
            response = self.engine.generate(prompt, language=self.language, **kwargs)

            return response

        except Exception as e:
            logger.error(f"生成响应失败: {e}")
            return ""
    
    def tokenize(self, text: str) -> List[int]:
        """
        对输入文本进行分词
        
        Args:
            text: 输入文本
            
        Returns:
            分词结果（简化实现，返回字符列表）
        """
        # RealAIEngine不直接提供tokenize接口
        # 这里提供一个简化实现
        return list(range(len(text)))
    
    def unload(self) -> bool:
        """
        从内存卸载模型
        
        Returns:
            卸载是否成功
        """
        try:
            if self.engine:
                # RealAIEngine有自己的清理方法
                self.engine.cleanup()
                self.engine = None
            
            self.is_loaded = False
            logger.info(f"✅ RealAIEngine已卸载（{self.language}）")
            return True
            
        except Exception as e:
            logger.error(f"卸载RealAIEngine失败: {e}")
            return False
    
    def is_ready(self) -> bool:
        """
        检查模型是否已加载并可用
        
        Returns:
            模型是否可用
        """
        return self.is_loaded and self.engine is not None
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息
        
        Returns:
            模型信息字典
        """
        info = super().get_model_info()
        info["adapter"] = "RealAIEngineAdapter"
        info["engine_type"] = "GGUF"
        return info


# 全局缓存
_real_ai_engine_cache = {}


def get_real_ai_engine_adapter(language: str) -> Optional[RealAIEngineAdapter]:
    """
    获取RealAIEngine适配器实例（带缓存）
    
    Args:
        language: 语言代码（zh或en）
        
    Returns:
        RealAIEngine适配器实例
    """
    global _real_ai_engine_cache
    
    try:
        # 检查缓存
        if language in _real_ai_engine_cache:
            adapter = _real_ai_engine_cache[language]
            if adapter.is_ready():
                logger.info(f"使用缓存的RealAIEngine适配器（{language}）")
                return adapter
        
        # 创建新的适配器
        logger.info(f"创建新的RealAIEngine适配器（{language}）")
        adapter = RealAIEngineAdapter(language=language)
        
        # 加载引擎
        if adapter.load():
            _real_ai_engine_cache[language] = adapter
            return adapter
        else:
            logger.error(f"RealAIEngine适配器加载失败（{language}）")
            return None
            
    except Exception as e:
        logger.error(f"获取RealAIEngine适配器失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None

