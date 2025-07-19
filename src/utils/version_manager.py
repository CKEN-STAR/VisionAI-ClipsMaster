#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
版本管理工具

提供版本相关的配置、检测和兼容性处理功能。用于支持多版本特性配置和测试。
"""

from typing import Dict, Any, List, Optional, Union, Tuple
import re
import os
import json
import logging
from pathlib import Path

# 配置日志
logger = logging.getLogger(__name__)

# 版本正则表达式模式 - 支持标准版本和移动版本
VERSION_PATTERN = r'^(\d+\.\d+\.\d+|mobile_\d+\.\d+)$'

# 版本特性配置目录
_CONFIG_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    'configs',
    'versions'
)

# 版本配置缓存
_version_config_cache: Dict[str, Dict[str, Any]] = {}

def get_version_config(version: str) -> Dict[str, Any]:
    """
    获取指定版本的配置信息
    
    Args:
        version: 版本号，格式为 "x.y.z" 或 "mobile_x.y"
        
    Returns:
        包含版本配置的字典
        
    Raises:
        ValueError: 当版本号格式无效时
        FileNotFoundError: 当版本配置文件不存在时
    """
    # 验证版本号格式
    if not re.match(VERSION_PATTERN, version):
        raise ValueError(f"无效的版本号格式: {version}，应为 x.y.z 或 mobile_x.y")
    
    # 检查缓存
    if version in _version_config_cache:
        return _version_config_cache[version]
    
    # 尝试加载配置文件
    if version.startswith("mobile_"):
        # 移动版本使用特殊命名格式
        config_file = os.path.join(_CONFIG_DIR, f"v_{version.replace('.', '_')}.json")
    else:
        # 标准版本使用v3_0_0格式
        config_file = os.path.join(_CONFIG_DIR, f"v{version.replace('.', '_')}.json")
    
    if not os.path.exists(config_file):
        # 如果特定版本配置不存在，尝试使用最近的主要版本配置
        if version.startswith("mobile_"):
            # 移动版本匹配
            major_minor = version.split('.')[0]  # mobile_2
            pattern = re.compile(f"v_{major_minor.replace('.', '_')}\\..+\\.json")
        else:
            # 标准版本匹配
            major_minor = '.'.join(version.split('.')[:2])
            pattern = re.compile(f"v{major_minor.replace('.', '_')}\\..+\\.json")
        
        # 检查配置目录是否存在
        if not os.path.exists(_CONFIG_DIR):
            os.makedirs(_CONFIG_DIR, exist_ok=True)
            logger.warning(f"创建版本配置目录: {_CONFIG_DIR}")
            
            # 返回默认空配置
            _version_config_cache[version] = {}
            return {}
            
        # 尝试查找匹配的配置文件
        for filename in os.listdir(_CONFIG_DIR):
            if pattern.match(filename):
                config_file = os.path.join(_CONFIG_DIR, filename)
                break
        else:
            # 仍找不到，使用默认空配置
            logger.warning(f"未找到版本 {version} 的配置文件")
            _version_config_cache[version] = {}
            return {}
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
            _version_config_cache[version] = config
            return config
    except Exception as e:
        logger.error(f"加载版本配置文件 {config_file} 失败: {e}")
        # 返回默认空配置
        _version_config_cache[version] = {}
        return {}

def compare_versions(version1: str, version2: str) -> int:
    """
    比较两个版本号
    
    Args:
        version1: 第一个版本号
        version2: 第二个版本号
        
    Returns:
        -1 如果version1 < version2
         0 如果version1 = version2
         1 如果version1 > version2
         
    Raises:
        ValueError: 当版本号格式无效时
    """
    # 验证版本号格式
    if not re.match(VERSION_PATTERN, version1):
        raise ValueError(f"无效的版本号格式: {version1}")
    if not re.match(VERSION_PATTERN, version2):
        raise ValueError(f"无效的版本号格式: {version2}")
    
    # 处理版本类型不同的情况
    is_mobile1 = version1.startswith("mobile_")
    is_mobile2 = version2.startswith("mobile_")
    
    # 如果类型不同，按约定移动版本小于标准版本
    if is_mobile1 and not is_mobile2:
        return -1
    if not is_mobile1 and is_mobile2:
        return 1
    
    # 类型相同的情况下比较版本号
    if is_mobile1:
        # 移动版本格式: mobile_x.y
        v1_parts = [int(x) for x in version1.replace("mobile_", "").split('.')]
        v2_parts = [int(x) for x in version2.replace("mobile_", "").split('.')]
    else:
        # 标准版本格式: x.y.z
        v1_parts = [int(x) for x in version1.split('.')]
        v2_parts = [int(x) for x in version2.split('.')]
    
    # 比较各部分
    for i in range(min(len(v1_parts), len(v2_parts))):
        if v1_parts[i] < v2_parts[i]:
            return -1
        elif v1_parts[i] > v2_parts[i]:
            return 1
    
    # 如果前面部分相同，较长的版本号较大
    if len(v1_parts) < len(v2_parts):
        return -1
    elif len(v1_parts) > len(v2_parts):
        return 1
    
    # 完全相同
    return 0

def get_supported_features(version: str) -> List[str]:
    """
    获取指定版本支持的特性列表
    
    Args:
        version: 版本号
        
    Returns:
        支持的特性名称列表
    """
    config = get_version_config(version)
    return config.get("supported_features", [])

def is_feature_supported(feature: str, version: str) -> bool:
    """
    检查指定版本是否支持某个特性
    
    Args:
        feature: 特性名称
        version: 版本号
        
    Returns:
        如果支持则为True，否则为False
    """
    return feature in get_supported_features(version)

def get_version_differences(version1: str, version2: str) -> Dict[str, Any]:
    """
    比较两个版本之间的差异
    
    Args:
        version1: 第一个版本号
        version2: 第二个版本号
        
    Returns:
        包含差异信息的字典
    """
    config1 = get_version_config(version1)
    config2 = get_version_config(version2)
    
    # 分析差异
    result = {
        "added_features": [],
        "removed_features": [],
        "modified_features": []
    }
    
    # 检查新增和修改的特性
    features1 = set(get_supported_features(version1))
    features2 = set(get_supported_features(version2))
    
    result["added_features"] = list(features2 - features1)
    result["removed_features"] = list(features1 - features2)
    
    # 检查共有但配置不同的特性
    common_features = features1.intersection(features2)
    for feature in common_features:
        # 获取特性配置
        feature_config1 = config1.get("feature_config", {}).get(feature, {})
        feature_config2 = config2.get("feature_config", {}).get(feature, {})
        
        # 如果配置不同，标记为已修改
        if feature_config1 != feature_config2:
            result["modified_features"].append(feature)
    
    return result

def create_version_config_template(version: str, output_path: Optional[str] = None) -> Dict[str, Any]:
    """
    创建版本配置模板
    
    Args:
        version: 版本号
        output_path: 可选的输出文件路径
        
    Returns:
        配置模板字典
    """
    # 验证版本号格式
    if not re.match(VERSION_PATTERN, version):
        raise ValueError(f"无效的版本号格式: {version}")
    
    # 创建模板
    template = {
        "version": version,
        "release_date": "YYYY-MM-DD",
        "supported_features": [],
        "feature_config": {},
        "compatibility": {
            "min_compatible_version": "",
            "max_compatible_version": ""
        },
        "deprecated_features": [],
        "metadata": {
            "description": "",
            "created_by": ""
        }
    }
    
    # 如果是移动版本，添加特定字段
    if version.startswith("mobile_"):
        template["compatibility"]["desktop_compatible_version"] = ""
        template["feature_config"]["mobile_optimization"] = {
            "enabled": True,
            "battery_optimization": True,
            "reduced_memory_mode": True
        }
    
    # 如果指定了输出路径，保存模板
    if output_path:
        # 确保目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # 写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(template, f, indent=4, ensure_ascii=False)
            
        logger.info(f"已创建版本配置模板: {output_path}")
    
    return template

# 辅助函数
def ensure_version_config_dir() -> str:
    """
    确保版本配置目录存在
    
    Returns:
        配置目录路径
    """
    if not os.path.exists(_CONFIG_DIR):
        os.makedirs(_CONFIG_DIR, exist_ok=True)
        logger.info(f"已创建版本配置目录: {_CONFIG_DIR}")
    return _CONFIG_DIR

def is_mobile_version(version: str) -> bool:
    """
    检查是否是移动版本
    
    Args:
        version: 版本号
        
    Returns:
        如果是移动版本则为True，否则为False
    """
    return version.startswith("mobile_") 