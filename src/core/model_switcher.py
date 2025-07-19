#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
模型切换器 - 智能切换语言模型
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any

# 获取日志记录器
logger = logging.getLogger(__name__)

class ModelSwitcher:
    """模型切换器"""
    
    def __init__(self, model_root=None):
        self.model_root = Path(model_root) if model_root else Path('models')
        self._current_model = None
        self.available_models = {
            "zh": "qwen2.5-7b-zh",
            "en": "mistral-7b-en"
        }
        self.model_cache = {}
        logger.info(f"模型切换器初始化完成，模型根目录: {self.model_root}")
    
    def switch_model(self, language: str) -> bool:
        """切换到指定语言的模型"""
        logger.info(f"开始切换模型到语言: {language}")

        if language not in self.available_models:
            logger.error(f"不支持的语言: {language}，支持的语言: {list(self.available_models.keys())}")
            return False

        target_model = self.available_models[language]

        if self._current_model == target_model:
            logger.info(f"模型 {target_model} 已经是当前模型，无需切换")
            return True

        try:
            logger.info(f"正在切换模型: {self._current_model} -> {target_model}")
            # 模拟模型切换
            self._current_model = target_model
            logger.info(f"模型切换成功: {target_model}")
            return True
        except Exception as e:
            logger.error(f"模型切换失败: {e}")
            return False
    
    def get_current_model(self) -> Optional[str]:
        """获取当前模型"""
        return self._current_model
    
    def is_model_loaded(self, language: str) -> bool:
        """检查模型是否已加载"""
        return language in self.model_cache
    
    def unload_model(self, language: str):
        """卸载模型"""
        logger.info(f"开始卸载模型: {language}")
        if language in self.model_cache:
            del self.model_cache[language]
            logger.info(f"模型 {language} 已卸载")
        else:
            logger.warning(f"模型 {language} 未加载，无需卸载")
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            "current_model": self._current_model,
            "available_models": self.available_models,
            "loaded_models": list(self.model_cache.keys())
        }
    
    def __del__(self):
        """清理资源"""
        try:
            if hasattr(self, 'model_cache'):
                self.model_cache.clear()
        except:
            pass

# 全局实例
model_switcher = ModelSwitcher()

def get_model_switcher():
    """获取模型切换器实例"""
    return model_switcher
