#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
配置工具模块

提供简单的配置文件加载和管理功能。
支持 YAML 和 JSON 格式的配置文件。
"""

import os
import yaml
import json
import logging
from pathlib import Path
from typing import Dict, Any, Union, Optional

logger = logging.getLogger(__name__)

def load_yaml_config(config_path: Union[str, Path]) -> Dict[str, Any]:
    """
    加载YAML配置文件

    Args:
        config_path: YAML配置文件路径

    Returns:
        配置字典

    Raises:
        FileNotFoundError: 文件不存在
        yaml.YAMLError: YAML格式错误
    """
    config_path = Path(config_path)

    if not config_path.exists():
        logger.warning(f"YAML配置文件不存在: {config_path}")
        return {}

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        logger.info(f"成功加载YAML配置: {config_path}")
        return config or {}

    except yaml.YAMLError as e:
        logger.error(f"YAML格式错误: {config_path} - {e}")
        return {}
    except Exception as e:
        logger.error(f"加载YAML配置失败: {config_path} - {e}")
        return {}

def load_config(config_path: Union[str, Path]) -> Dict[str, Any]:
    """
    加载配置文件
    
    支持 YAML 和 JSON 格式的配置文件。
    如果文件不存在，则返回空字典。
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        配置字典
        
    Raises:
        ValueError: 不支持的文件格式
    """
    config_path = Path(config_path)
    
    # 检查文件是否存在
    if not config_path.exists():
        logger.warning(f"配置文件不存在: {config_path}")
        return {}
    
    # 加载配置
    try:
        suffix = config_path.suffix.lower()
        
        if suffix in ['.yml', '.yaml']:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
        elif suffix == '.json':
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        else:
            raise ValueError(f"不支持的配置文件格式: {suffix}")
        
        logger.info(f"成功加载配置文件: {config_path}")
        return config or {}
    
    except Exception as e:
        logger.error(f"加载配置文件失败: {config_path}, 错误: {e}")
        return {}

def save_config(config: Dict[str, Any], config_path: Union[str, Path]) -> bool:
    """
    保存配置到文件
    
    根据文件扩展名确定保存格式。
    
    Args:
        config: 要保存的配置字典
        config_path: 配置文件保存路径
        
    Returns:
        是否保存成功
    """
    config_path = Path(config_path)
    
    # 确保目录存在
    os.makedirs(config_path.parent, exist_ok=True)
    
    try:
        suffix = config_path.suffix.lower()
        
        if suffix in ['.yml', '.yaml']:
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        elif suffix == '.json':
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        else:
            raise ValueError(f"不支持的配置文件格式: {suffix}")
        
        logger.info(f"成功保存配置文件: {config_path}")
        return True
    
    except Exception as e:
        logger.error(f"保存配置文件失败: {config_path}, 错误: {e}")
        return False

def merge_configs(base_config: Dict[str, Any], override_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    合并两个配置字典
    
    override_config 中的值会覆盖 base_config 中的值。
    
    Args:
        base_config: 基础配置
        override_config: 覆盖配置
        
    Returns:
        合并后的配置
    """
    result = base_config.copy()
    
    for key, value in override_config.items():
        # 如果两个都是字典，递归合并
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_configs(result[key], value)
        else:
            result[key] = value
    
    return result 