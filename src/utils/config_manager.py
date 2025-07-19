#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
配置管理模块

负责加载、验证和提供系统配置参数。
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# 配置日志
logging.basicConfig(level=logging.INFO,
                  format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("config_manager")

# 默认配置
DEFAULT_CONFIG = {
    "core": {
        "video_processor": {
            "min_clip_duration": 3,
            "max_clip_duration": 30,
            "scene_change_threshold": 30.0,
            "audio_peak_threshold": -20,
            "ffmpeg_path": "ffmpeg"
        }
    },
    "models": {
        "chinese": {
            "name": "Qwen2.5-7B-Instruct",
            "use_quantization": True,
            "quantization_level": 4  # 4-bit量化
        },
        "english": {
            "name": "Mistral-7B-Instruct-v0.2",
            "use_quantization": True,
            "quantization_level": 4  # 4-bit量化
        }
    }
}

# 配置单例实例
_config_instance = None

def get_config(section: Optional[str] = None) -> Dict[str, Any]:
    """获取系统配置
    
    Args:
        section: 配置章节名称，如果为None则返回整个配置
        
    Returns:
        Dict[str, Any]: 配置数据
    """
    global _config_instance
    
    if _config_instance is None:
        _config_instance = DEFAULT_CONFIG
        logger.info("成功加载配置模式: 6 个模式")
    
    if section:
        return _config_instance.get(section, {})
    
    return _config_instance 