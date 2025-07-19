#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
版本特征库读取模块

提供从版本特征库配置文件中加载、查询和使用版本特征信息的功能。
"""

import os
import yaml
import logging
from typing import Dict, List, Any, Optional, Union, Tuple
from functools import lru_cache
from pathlib import Path

# 配置日志
logger = logging.getLogger(__name__)

# 默认版本特征库文件路径
DEFAULT_VERSION_FEATURES_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "configs", "jianying_versions.yaml"
)

class VersionFeatures:
    """版本特征库管理类"""
    
    def __init__(self, config_path: str = None):
        """
        初始化版本特征库
        
        Args:
            config_path: 配置文件路径，默认为configs/jianying_versions.yaml
        """
        self.config_path = config_path or DEFAULT_VERSION_FEATURES_PATH
        self.version_data = self._load_version_features()
        
    def _load_version_features(self) -> Dict[str, Any]:
        """加载版本特征库配置文件"""
        try:
            if not os.path.exists(self.config_path):
                logger.error(f"版本特征库配置文件不存在: {self.config_path}")
                return {}
                
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                
            return data
        except Exception as e:
            logger.error(f"加载版本特征库配置文件失败: {str(e)}")
            return {}
    
    def get_all_versions(self) -> List[Dict[str, Any]]:
        """
        获取所有版本信息
        
        Returns:
            List[Dict[str, Any]]: 所有版本信息列表
        """
        if not self.version_data or 'version_specs' not in self.version_data:
            return []
            
        return self.version_data['version_specs']
    
    def get_version_info(self, version: str) -> Optional[Dict[str, Any]]:
        """
        获取指定版本的信息
        
        Args:
            version: 版本号 (例如 "3.0.0")
            
        Returns:
            Optional[Dict[str, Any]]: 版本信息字典，如果未找到则返回None
        """
        if not self.version_data or 'version_specs' not in self.version_data:
            return None
            
        # 规范化版本号
        normalized_version = self._normalize_version(version)
        
        # 查找版本
        for version_info in self.version_data['version_specs']:
            if self._normalize_version(version_info.get('version', '')) == normalized_version:
                return version_info
                
        return None
    
    def get_schema_for_version(self, version: str) -> Optional[str]:
        """
        获取指定版本的XSD模式文件名
        
        Args:
            version: 版本号 (例如 "3.0.0")
            
        Returns:
            Optional[str]: XSD文件名，如果未找到则返回None
        """
        version_info = self.get_version_info(version)
        if not version_info:
            return None
            
        return version_info.get('schema')
    
    def get_supported_features(self, version: str) -> List[Dict[str, Any]]:
        """
        获取指定版本支持的特性列表
        
        Args:
            version: 版本号 (例如 "3.0.0")
            
        Returns:
            List[Dict[str, Any]]: 支持的特性列表
        """
        version_info = self.get_version_info(version)
        if not version_info:
            return []
            
        return version_info.get('supported_features', [])
    
    def get_supported_effects(self, version: str) -> List[str]:
        """
        获取指定版本支持的效果列表
        
        Args:
            version: 版本号 (例如 "3.0.0")
            
        Returns:
            List[str]: 支持的效果列表
        """
        version_info = self.get_version_info(version)
        if not version_info:
            return []
            
        return version_info.get('supported_effects', [])
    
    def get_max_resolution(self, version: str) -> Optional[str]:
        """
        获取指定版本支持的最大分辨率
        
        Args:
            version: 版本号 (例如 "3.0.0")
            
        Returns:
            Optional[str]: 最大分辨率字符串 (例如 "7680x4320")
        """
        version_info = self.get_version_info(version)
        if not version_info:
            return None
            
        return version_info.get('max_resolution')
    
    def get_display_name(self, version: str) -> Optional[str]:
        """
        获取指定版本的显示名称
        
        Args:
            version: 版本号 (例如 "3.0.0")
            
        Returns:
            Optional[str]: 显示名称 (例如 "专业版")
        """
        version_info = self.get_version_info(version)
        if not version_info:
            return None
            
        return version_info.get('display_name')
    
    def get_compatible_versions(self, version: str) -> List[str]:
        """
        获取与指定版本兼容的版本列表
        
        Args:
            version: 版本号 (例如 "3.0.0")
            
        Returns:
            List[str]: 兼容的版本列表
        """
        version_info = self.get_version_info(version)
        if not version_info:
            return []
            
        return version_info.get('compatibility', [])
    
    def is_feature_supported(self, version: str, feature_name: str) -> bool:
        """
        检查指定版本是否支持某个特性
        
        Args:
            version: 版本号 (例如 "3.0.0")
            feature_name: 特性名称
            
        Returns:
            bool: 是否支持该特性
        """
        supported_features = self.get_supported_features(version)
        
        for feature in supported_features:
            if isinstance(feature, dict) and feature.get('name') == feature_name:
                return True
            elif isinstance(feature, str) and feature == feature_name:
                return True
                
        return False
    
    def is_effect_supported(self, version: str, effect_name: str) -> bool:
        """
        检查指定版本是否支持某个效果
        
        Args:
            version: 版本号 (例如 "3.0.0")
            effect_name: 效果名称
            
        Returns:
            bool: 是否支持该效果
        """
        supported_effects = self.get_supported_effects(version)
        return effect_name in supported_effects
    
    def can_convert_to(self, source_version: str, target_version: str) -> bool:
        """
        检查是否可以将源版本转换为目标版本
        
        Args:
            source_version: 源版本号
            target_version: 目标版本号
            
        Returns:
            bool: 是否可以转换
        """
        # 获取源版本信息
        source_info = self.get_version_info(source_version)
        if not source_info:
            return False
            
        # 如果源版本和目标版本相同，可以转换
        if self._normalize_version(source_version) == self._normalize_version(target_version):
            return True
            
        # 检查目标版本是否在源版本的兼容性列表中
        compatibility = source_info.get('compatibility', [])
        return any(self._normalize_version(ver) == self._normalize_version(target_version) for ver in compatibility)
    
    def get_conversion_operations(self, source_version: str, target_version: str) -> List[Dict[str, Any]]:
        """
        获取版本转换操作
        
        Args:
            source_version: 源版本号
            target_version: 目标版本号
            
        Returns:
            List[Dict[str, Any]]: 转换操作列表
        """
        if not self.version_data or 'version_conversions' not in self.version_data:
            return []
            
        # 规范化版本号
        source = self._normalize_version(source_version)
        target = self._normalize_version(target_version)
        
        # 构建转换键名
        conversion_key = f"{source}-to-{target}"
        
        # 确定转换方向
        if self.compare_versions(source, target) > 0:
            # 降级转换
            conversions = self.version_data['version_conversions'].get('downgrade', {})
        else:
            # 升级转换
            conversions = self.version_data['version_conversions'].get('upgrade', {})
            
        # 查找转换操作
        for key, value in conversions.items():
            if key == conversion_key:
                return value.get('operations', [])
                
        return []
    
    def compare_versions(self, version1: str, version2: str) -> int:
        """
        比较两个版本号
        
        Args:
            version1: 第一个版本号
            version2: 第二个版本号
            
        Returns:
            int: 
                如果version1 > version2，返回1
                如果version1 < version2，返回-1
                如果version1 == version2，返回0
        """
        v1 = self._normalize_version(version1)
        v2 = self._normalize_version(version2)
        
        v1_parts = [int(part) for part in v1.split('.')]
        v2_parts = [int(part) for part in v2.split('.')]
        
        # 补齐版本号长度
        while len(v1_parts) < 3:
            v1_parts.append(0)
        while len(v2_parts) < 3:
            v2_parts.append(0)
        
        # 比较版本号
        for i in range(3):
            if v1_parts[i] > v2_parts[i]:
                return 1
            elif v1_parts[i] < v2_parts[i]:
                return -1
                
        return 0
    
    def find_conversion_path(self, source_version: str, target_version: str) -> List[str]:
        """
        查找从源版本到目标版本的转换路径
        
        Args:
            source_version: 源版本号
            target_version: 目标版本号
            
        Returns:
            List[str]: 转换路径中的版本列表
        """
        # 规范化版本号
        source = self._normalize_version(source_version)
        target = self._normalize_version(target_version)
        
        # 如果源版本和目标版本相同，无需转换
        if source == target:
            return []
            
        # 获取所有版本
        all_versions = [self._normalize_version(v.get('version', '')) for v in self.get_all_versions()]
        
        # 确保源版本和目标版本都在列表中
        if source not in all_versions or target not in all_versions:
            return []
            
        # 对版本进行排序
        all_versions.sort(key=lambda v: self._version_to_tuple(v))
        
        # 查找路径
        if self.compare_versions(source, target) > 0:
            # 降级路径（从高版本到低版本）
            versions_between = [v for v in all_versions 
                               if self.compare_versions(target, v) <= 0 
                               and self.compare_versions(v, source) < 0]
            versions_between.reverse()  # 从高到低
            path = [source] + versions_between + [target]
        else:
            # 升级路径（从低版本到高版本）
            versions_between = [v for v in all_versions 
                               if self.compare_versions(v, target) <= 0 
                               and self.compare_versions(source, v) < 0]
            path = [source] + versions_between + [target]
            
        return path
    
    def _normalize_version(self, version: str) -> str:
        """规范化版本号"""
        if not version:
            return "0.0.0"
            
        # 移除版本号前缀（如v, V等）
        version = version.lower()
        if version.startswith('v'):
            version = version[1:]
            
        # 确保有足够的版本号部分
        parts = version.split('.')
        while len(parts) < 3:
            parts.append('0')
            
        # 只保留三个部分
        parts = parts[:3]
        
        # 确保每部分都是数字
        parts = [p.strip() for p in parts]
        for i, part in enumerate(parts):
            try:
                int(part)
            except ValueError:
                # 如果不是数字，替换为0
                parts[i] = '0'
                
        return '.'.join(parts)
    
    def _version_to_tuple(self, version: str) -> Tuple[int, ...]:
        """将版本号转换为元组以便比较"""
        parts = self._normalize_version(version).split('.')
        return tuple(int(part) for part in parts)


# 单例模式的版本特征库
_version_features_instance = None

def get_version_features() -> VersionFeatures:
    """
    获取版本特征库实例
    
    Returns:
        VersionFeatures: 版本特征库实例
    """
    global _version_features_instance
    if _version_features_instance is None:
        _version_features_instance = VersionFeatures()
    return _version_features_instance


if __name__ == "__main__":
    # 简单测试
    version_features = get_version_features()
    
    print("所有版本:")
    for version in version_features.get_all_versions():
        print(f"- {version.get('version')} ({version.get('display_name')})")
    
    print("\n3.0.0版本信息:")
    v3_info = version_features.get_version_info("3.0.0")
    if v3_info:
        print(f"- 名称: {v3_info.get('display_name')}")
        print(f"- 架构: {v3_info.get('schema')}")
        print(f"- 最大分辨率: {v3_info.get('max_resolution')}")
        print(f"- 所需节点: {v3_info.get('required_nodes')}")
        
        print("\n支持的功能:")
        for feature in v3_info.get('supported_features', []):
            print(f"- {feature.get('name')}: {feature.get('description')}")
        
        print("\n支持的效果:")
        for effect in v3_info.get('supported_effects', []):
            print(f"- {effect}") 