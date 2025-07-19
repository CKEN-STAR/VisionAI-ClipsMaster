#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
模型配置类 - 负责加载和管理模型配置
"""

import os
import yaml
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

# 配置日志
logger = logging.getLogger(__name__)

class ModelConfig:
    """模型配置类
    
    保存模型相关的配置信息，如模型路径、量化设置、上下文长度等。
    """
    
    def __init__(self, 
                 model_info: Dict[str, Any],
                 quantization: Optional[str] = None,
                 context_length: int = 4096):
        """初始化模型配置
        
        Args:
            model_info: 模型信息字典
            quantization: 量化等级，如"INT4"或"INT8"，None表示不量化
            context_length: 上下文长度
        """
        self.model_info = model_info
        self.quantization = quantization
        self.context_length = context_length
        
    def __repr__(self) -> str:
        """返回配置的字符串表示"""
        return f"ModelConfig(name={self.model_info.get('name')}, language={self.model_info.get('language')}, quantization={self.quantization})"
        
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置项
        
        Args:
            key: 配置键
            default: 默认值
            
        Returns:
            配置值
        """
        return self.model_info.get(key, default)
        
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典表示
        
        Returns:
            配置字典
        """
        return self.model_info 

def load_model_config() -> Dict[str, Any]:
    """加载模型配置
    
    从YAML文件加载模型配置信息
    
    Returns:
        Dict[str, Any]: 模型配置字典
    """
    config_path = Path(__file__).parent / "model_config.yaml"
    
    # 如果配置文件不存在，返回默认配置
    if not config_path.exists():
        logger.warning(f"模型配置文件不存在: {config_path}，使用默认配置")
        return get_default_model_config()
    
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        
        logger.info(f"成功加载模型配置: {len(config.get('models', {}))}个模型")
        return config
    except Exception as e:
        logger.error(f"加载模型配置失败: {str(e)}，使用默认配置")
        return get_default_model_config()

def get_default_model_config() -> Dict[str, Any]:
    """获取默认模型配置
    
    Returns:
        Dict[str, Any]: 默认模型配置字典
    """
    return {
        "models": {
            "qwen2.5-7b-zh": {
                "name": "Qwen2.5-7B-Instruct",
                "checkpoint": "Qwen/Qwen2.5-7B-Instruct",
                "language": "zh",
                "size": "7B",
                "quantization": "INT4",
                "context_length": 8192
            },
            "mistral-7b-en": {
                "name": "Mistral-7B-Instruct-v0.2",
                "checkpoint": "mistralai/Mistral-7B-Instruct-v0.2",
                "language": "en",
                "size": "7B",
                "quantization": "INT4",
                "context_length": 8192
            }
        },
        "default_models": {
            "zh": "qwen2.5-7b-zh",
            "en": "mistral-7b-en"
        }
    }

def get_model_config(model_id: str) -> Optional[ModelConfig]:
    """获取指定模型的配置
    
    Args:
        model_id: 模型ID
        
    Returns:
        Optional[ModelConfig]: 模型配置对象，如果不存在则返回None
    """
    config = load_model_config()
    models = config.get("models", {})
    
    if model_id not in models:
        logger.warning(f"未找到模型配置: {model_id}")
        return None
    
    model_info = models[model_id]
    
    return ModelConfig(
        model_info=model_info,
        quantization=model_info.get("quantization"),
        context_length=model_info.get("context_length", 4096)
    )

def get_qwen_config() -> ModelConfig:
    """获取Qwen模型配置
    
    Returns:
        ModelConfig: Qwen模型配置对象
    """
    config = load_model_config()
    default_zh_model_id = config.get("default_models", {}).get("zh", "qwen2.5-7b-zh")
    return get_model_config(default_zh_model_id)

def get_mistral_config() -> ModelConfig:
    """获取Mistral模型配置
    
    Returns:
        ModelConfig: Mistral模型配置对象
    """
    config = load_model_config()
    default_en_model_id = config.get("default_models", {}).get("en", "mistral-7b-en")
    return get_model_config(default_en_model_id) 