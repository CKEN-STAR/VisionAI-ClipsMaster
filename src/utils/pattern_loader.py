"""
模式加载工具

提供从版本管理系统中加载模式和配置的工具函数
"""

import os
import yaml
import json
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from loguru import logger

# 尝试导入版本管理模块
try:
    from src.version_management.pattern_version_manager import (
        get_latest_version,
        get_version_metadata,
        get_pattern_config,
        set_current_version
    )
    HAS_VERSION_MANAGER = True
except ImportError:
    logger.warning("版本管理模块不可用，将使用默认配置")
    HAS_VERSION_MANAGER = False

# 默认配置路径
DEFAULT_CONFIG_PATH = "configs/pattern_evaluation.yaml"


def get_current_pattern_config() -> Dict[str, Any]:
    """
    获取当前版本的模式配置
    
    Returns:
        Dict[str, Any]: 模式配置字典
    """
    if HAS_VERSION_MANAGER:
        try:
            # 从版本管理系统加载配置
            config = get_pattern_config()
            if config:
                logger.info("已从版本管理系统加载模式配置")
                return config
        except Exception as e:
            logger.error(f"从版本管理系统加载配置失败: {e}")
    
    # 回退到默认配置
    try:
        with open(DEFAULT_CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        logger.info(f"已从默认路径加载模式配置: {DEFAULT_CONFIG_PATH}")
        return config
    except Exception as e:
        logger.error(f"加载默认配置失败: {e}")
        return {}


def get_recommended_combinations() -> List[Dict[str, Any]]:
    """
    获取推荐的模式组合
    
    Returns:
        List[Dict[str, Any]]: 推荐模式组合列表
    """
    config = get_current_pattern_config()
    return config.get("recommended_combinations", [])


def get_pattern_parameters(pattern_type: str) -> Dict[str, Any]:
    """
    获取特定模式类型的参数配置
    
    Args:
        pattern_type: 模式类型，如"opening", "climax"等
        
    Returns:
        Dict[str, Any]: 模式参数配置
    """
    config = get_current_pattern_config()
    params = config.get("pattern_parameters", {}).get(pattern_type, {})
    return params


def get_evaluation_weights() -> Dict[str, float]:
    """
    获取评估权重配置
    
    Returns:
        Dict[str, float]: 评估权重配置
    """
    config = get_current_pattern_config()
    return config.get("evaluation_weights", {})


def get_thresholds() -> Dict[str, float]:
    """
    获取评估阈值配置
    
    Returns:
        Dict[str, float]: 评估阈值配置
    """
    config = get_current_pattern_config()
    return config.get("thresholds", {})


def get_feature_importance() -> Dict[str, float]:
    """
    获取特征重要性权重
    
    Returns:
        Dict[str, float]: 特征重要性权重
    """
    config = get_current_pattern_config()
    return config.get("feature_importance", {})


def get_platform_optimization(platform: str = None) -> Dict[str, Any]:
    """
    获取平台优化参数
    
    Args:
        platform: 平台名称，如"douyin", "kuaishou"，如果为None则返回所有平台
        
    Returns:
        Dict[str, Any]: 平台优化参数
    """
    config = get_current_pattern_config()
    platform_config = config.get("platform_optimization", {})
    
    if platform is None:
        return platform_config
    
    return platform_config.get(platform, {})


def get_version_info() -> Dict[str, Any]:
    """
    获取当前使用的模式版本信息
    
    Returns:
        Dict[str, Any]: 版本信息
    """
    if not HAS_VERSION_MANAGER:
        return {
            "version": "unknown",
            "has_version_manager": False
        }
    
    try:
        metadata = get_version_metadata()
        if not metadata:
            latest = get_latest_version()
            metadata = get_version_metadata(latest) or {}
        
        return {
            "version": metadata.get("version", "unknown"),
            "created_at": metadata.get("created_at", "未知"),
            "description": metadata.get("description", ""),
            "author": metadata.get("author", "未知"),
            "data_size": metadata.get("data_size", "未知"),
            "coverage": metadata.get("coverage", {}),
            "has_version_manager": True
        }
    except Exception as e:
        logger.error(f"获取版本信息失败: {e}")
        return {
            "version": "unknown",
            "error": str(e),
            "has_version_manager": True
        }


def switch_pattern_version(version_name: str) -> bool:
    """
    切换到指定的模式版本
    
    Args:
        version_name: 版本名称，如"v1.0"
        
    Returns:
        bool: 是否切换成功
    """
    if not HAS_VERSION_MANAGER:
        logger.error("版本管理模块不可用，无法切换版本")
        return False
    
    try:
        success = set_current_version(version_name)
        if success:
            logger.info(f"已切换到模式版本: {version_name}")
        else:
            logger.error(f"切换版本失败: {version_name}")
        return success
    except Exception as e:
        logger.error(f"切换版本异常: {e}")
        return False 