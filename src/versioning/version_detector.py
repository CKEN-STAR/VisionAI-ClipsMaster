#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
版本检测器模块

提供检测和验证项目文件中的版本信息的功能。
"""

import os
import re
import json
import logging
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional, Union, Tuple
from pathlib import Path

# 配置日志
logger = logging.getLogger(__name__)

class VersionDetector:
    """版本检测器类"""
    
    def __init__(self):
        """初始化版本检测器"""
        # 导入版本特征库
        try:
            from .version_features import get_version_features
            self.version_features = get_version_features()
        except ImportError:
            from src.versioning.version_features import get_version_features
            self.version_features = get_version_features()
        
    def detect_version_from_file(self, file_path: str) -> Dict[str, Any]:
        """
        从文件中检测版本信息
        
        Args:
            file_path: 文件路径
            
        Returns:
            Dict[str, Any]: 版本信息
        """
        if not os.path.exists(file_path):
            return {
                "success": False,
                "error": f"文件不存在: {file_path}"
            }
        
        # 获取文件扩展名
        ext = os.path.splitext(file_path)[1].lower()
        
        # 根据文件类型调用不同的检测方法
        try:
            if ext == '.xml':
                version_info = self._detect_from_xml(file_path)
            elif ext == '.json':
                version_info = self._detect_from_json(file_path)
            else:
                # 尝试根据内容检测
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                version_info = self._detect_from_content(content)
                
            # 补充文件信息
            file_stat = os.stat(file_path)
            version_info.update({
                "file_path": file_path,
                "file_size": file_stat.st_size,
                "last_modified": file_stat.st_mtime,
                "success": True
            })
            
            return version_info
        except Exception as e:
            logger.error(f"检测版本时出错: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "file_path": file_path
            }
    
    def _detect_from_xml(self, file_path: str) -> Dict[str, Any]:
        """从XML文件中检测版本信息"""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            version_info = {
                "format_type": self._determine_format_type(root.tag),
                "version": root.get('version', 'unknown'),
                "display_name": self._get_display_name(root)
            }
            
            # 添加更多信息
            self._add_feature_support_info(version_info)
            
            return version_info
        except ET.ParseError:
            # 如果XML解析失败，尝试使用正则表达式
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            return self._detect_from_content(content)
    
    def _detect_from_json(self, file_path: str) -> Dict[str, Any]:
        """从JSON文件中检测版本信息"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # 尝试从不同的JSON结构中提取版本信息
            version = 'unknown'
            
            # 常见的版本字段
            version_keys = ['version', 'app_version', 'project_version', 'jianying_version']
            
            for key in version_keys:
                if key in data:
                    version = data[key]
                    break
                    
            # 检查嵌套结构
            if 'meta' in data and isinstance(data['meta'], dict):
                for key in version_keys:
                    if key in data['meta']:
                        version = data['meta'][key]
                        break
                        
            if 'info' in data and isinstance(data['info'], dict):
                for key in version_keys:
                    if key in data['info']:
                        version = data['info'][key]
                        break
            
            # 确定格式类型
            format_type = 'unknown'
            if 'format' in data:
                format_type = data['format']
            elif 'type' in data:
                format_type = data['type']
            else:
                # 尝试通过关键字推断
                content = json.dumps(data)
                if 'jianying' in content.lower():
                    format_type = 'jianying'
                elif 'premiere' in content.lower():
                    format_type = 'premiere'
                elif 'fcpxml' in content.lower():
                    format_type = 'fcpxml'
            
            version_info = {
                "format_type": format_type,
                "version": version,
                "display_name": self._format_type_to_name(format_type)
            }
            
            # 添加更多信息
            self._add_feature_support_info(version_info)
            
            return version_info
        except json.JSONDecodeError:
            # 如果JSON解析失败，尝试作为文本处理
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            return self._detect_from_content(content)
    
    def _detect_from_content(self, content: str) -> Dict[str, Any]:
        """从文本内容中检测版本信息"""
        # 尝试匹配XML格式的版本信息
        xml_version_pattern = r'<[^>]+\s+version=["\']([^"\']+)["\']'
        xml_match = re.search(xml_version_pattern, content)
        
        if xml_match:
            version = xml_match.group(1)
            format_type = self._determine_format_type_from_content(content)
            
            version_info = {
                "format_type": format_type,
                "version": version,
                "display_name": self._format_type_to_name(format_type)
            }
            
            # 添加更多信息
            self._add_feature_support_info(version_info)
            
            return version_info
        
        # 尝试匹配JSON格式的版本信息
        json_version_pattern = r'"version"\s*:\s*"([^"]+)"'
        json_match = re.search(json_version_pattern, content)
        
        if json_match:
            version = json_match.group(1)
            format_type = self._determine_format_type_from_content(content)
            
            version_info = {
                "format_type": format_type,
                "version": version,
                "display_name": self._format_type_to_name(format_type)
            }
            
            # 添加更多信息
            self._add_feature_support_info(version_info)
            
            return version_info
        
        # 尝试匹配常规文本中的版本信息
        text_version_pattern = r'版本\s*[：:]\s*([0-9\.]+)'
        text_match = re.search(text_version_pattern, content)
        
        if text_match:
            version = text_match.group(1)
            format_type = self._determine_format_type_from_content(content)
            
            version_info = {
                "format_type": format_type,
                "version": version,
                "display_name": self._format_type_to_name(format_type)
            }
            
            # 添加更多信息
            self._add_feature_support_info(version_info)
            
            return version_info
        
        # 没有找到版本信息
        return {
            "format_type": self._determine_format_type_from_content(content),
            "version": "unknown",
            "display_name": "未知格式"
        }
    
    def _determine_format_type(self, root_tag: str) -> str:
        """根据XML根标签确定格式类型"""
        tag_to_format = {
            'jianying_project': 'jianying',
            'fcpxml': 'fcpxml',
            'xmeml': 'premiere',
            'project': 'premiere'
        }
        
        return tag_to_format.get(root_tag, 'unknown')
    
    def _determine_format_type_from_content(self, content: str) -> str:
        """从内容中推断格式类型"""
        content_lower = content.lower()
        
        if 'jianying' in content_lower:
            return 'jianying'
        elif 'fcpxml' in content_lower:
            return 'fcpxml'
        elif 'premiere' in content_lower or 'xmeml' in content_lower:
            return 'premiere'
        elif 'davinci' in content_lower:
            return 'davinci'
        
        return 'unknown'
    
    def _format_type_to_name(self, format_type: str) -> str:
        """将格式类型转换为显示名称"""
        format_names = {
            'jianying': '剪映',
            'fcpxml': 'Final Cut Pro',
            'premiere': 'Premiere Pro',
            'davinci': 'DaVinci Resolve',
            'unknown': '未知格式'
        }
        
        return format_names.get(format_type, '未知格式')
    
    def _get_display_name(self, root) -> str:
        """获取格式显示名称"""
        format_type = self._determine_format_type(root.tag)
        version = root.get('version', 'unknown')
        
        # 对于剪映格式，使用版本特征库中的显示名称
        if format_type == 'jianying' and version != 'unknown':
            display_name = self.version_features.get_display_name(version)
            if display_name:
                return display_name
        
        return self._format_type_to_name(format_type)
    
    def _add_feature_support_info(self, version_info: Dict[str, Any]) -> None:
        """添加特性支持信息"""
        if version_info['format_type'] != 'jianying' or version_info['version'] == 'unknown':
            return
            
        version = version_info['version']
        version_info['supported_features'] = []
        
        # 获取支持的特性
        supported_features = self.version_features.get_supported_features(version)
        for feature in supported_features:
            if isinstance(feature, dict):
                version_info['supported_features'].append(feature['name'])
            elif isinstance(feature, str):
                version_info['supported_features'].append(feature)
        
        # 获取支持的效果
        version_info['supported_effects'] = self.version_features.get_supported_effects(version)
        
        # 获取最大分辨率
        version_info['max_resolution'] = self.version_features.get_max_resolution(version)
        
        # 获取兼容版本
        version_info['compatible_versions'] = self.version_features.get_compatible_versions(version)


def detect_version(file_path: str) -> Dict[str, Any]:
    """
    从文件中检测版本信息
    
    Args:
        file_path: 文件路径
        
    Returns:
        Dict[str, Any]: 版本信息
    """
    detector = VersionDetector()
    return detector.detect_version_from_file(file_path)


def is_compatible(source_version: str, target_version: str) -> bool:
    """
    检查源版本是否与目标版本兼容
    
    Args:
        source_version: 源版本号
        target_version: 目标版本号
        
    Returns:
        bool: 是否兼容
    """
    # 导入版本特征库
    try:
        from .version_features import get_version_features
    except ImportError:
        from src.versioning.version_features import get_version_features
        
    version_features = get_version_features()
    return version_features.can_convert_to(source_version, target_version)


def get_conversion_path(source_version: str, target_version: str) -> List[str]:
    """
    获取从源版本到目标版本的转换路径
    
    Args:
        source_version: 源版本号
        target_version: 目标版本号
        
    Returns:
        List[str]: 转换路径中的版本列表
    """
    # 导入版本特征库
    try:
        from .version_features import get_version_features
    except ImportError:
        from src.versioning.version_features import get_version_features
        
    version_features = get_version_features()
    return version_features.find_conversion_path(source_version, target_version)


def get_version_display_name(version: str) -> str:
    """
    获取版本的显示名称
    
    Args:
        version: 版本号
        
    Returns:
        str: 版本显示名称
    """
    # 导入版本特征库
    try:
        from .version_features import get_version_features
    except ImportError:
        from src.versioning.version_features import get_version_features
        
    version_features = get_version_features()
    display_name = version_features.get_display_name(version)
    return display_name or version


if __name__ == "__main__":
    # 简单测试
    import sys
    
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        result = detect_version(file_path)
        
        print("版本检测结果:")
        for key, value in result.items():
            print(f"- {key}: {value}")
    else:
        print("请提供要检测的文件路径作为参数") 