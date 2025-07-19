#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
模型加载器

负责加载、管理和提供大模型接口。
"""

import os
import time
import logging
from typing import Dict, Any, Optional, List

from src.utils.config_manager import get_config

# 配置日志
logging.basicConfig(level=logging.INFO,
                  format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("model_loader")

class ModelLoader:
    """模型加载器
    
    负责加载和管理大模型，支持中英文模型的按需加载。
    """
    
    def __init__(self):
        """初始化模型加载器"""
        # 加载配置
        self.config = get_config("models")
        
        # 模型缓存
        self.models = {}
        
        # 模拟一些模型属性
        self.chinese_model_path = "models/chinese/Qwen2.5-7B"
        self.english_model_path = "models/english/Mistral-7B" 
        
        logger.info("模型加载器初始化完成")
    
    def load_chinese_model(self) -> Dict[str, Any]:
        """加载中文模型
        
        Returns:
            Dict[str, Any]: 加载的模型信息
        """
        model_config = self.config.get("chinese", {})
        
        if "chinese" in self.models:
            logger.info("中文模型已加载，直接返回")
            return self.models["chinese"]
        
        # 模拟模型加载过程
        logger.info(f"加载中文模型: {model_config.get('name')}")
        time.sleep(0.5)  # 模拟加载时间
        
        # 模拟模型对象
        model = {
            "name": model_config.get("name"),
            "loaded_at": time.time(),
            "quantized": model_config.get("use_quantization", False),
            "quant_level": model_config.get("quantization_level", 0) if model_config.get("use_quantization", False) else None
        }
        
        # 缓存模型
        self.models["chinese"] = model
        
        logger.info("中文模型加载完成")
        return model
    
    def load_english_model(self) -> Dict[str, Any]:
        """加载英文模型
        
        Returns:
            Dict[str, Any]: 加载的模型信息
        """
        model_config = self.config.get("english", {})
        
        if "english" in self.models:
            logger.info("英文模型已加载，直接返回")
            return self.models["english"]
        
        # 模拟模型加载过程
        logger.info(f"加载英文模型: {model_config.get('name')}")
        time.sleep(0.5)  # 模拟加载时间
        
        # 模拟模型对象
        model = {
            "name": model_config.get("name"),
            "loaded_at": time.time(),
            "quantized": model_config.get("use_quantization", False),
            "quant_level": model_config.get("quantization_level", 0) if model_config.get("use_quantization", False) else None
        }
        
        # 缓存模型
        self.models["english"] = model
        
        logger.info("英文模型加载完成")
        return model
    
    def unload_model(self, language: str) -> bool:
        """卸载指定语言的模型
        
        Args:
            language: 模型语言，支持"chinese"或"english"
            
        Returns:
            bool: 是否成功卸载
        """
        if language in self.models:
            logger.info(f"卸载{language}模型")
            del self.models[language]
            return True
        
        return False
    
    def unload_all_models(self) -> None:
        """卸载所有模型"""
        logger.info("卸载所有模型")
        self.models = {}

# 模型加载器实例
_model_loader = None

def get_model_loader() -> ModelLoader:
    """获取模型加载器实例（单例模式）
    
    Returns:
        ModelLoader: 模型加载器实例
    """
    global _model_loader
    
    if _model_loader is None:
        _model_loader = ModelLoader()
    
    return _model_loader 