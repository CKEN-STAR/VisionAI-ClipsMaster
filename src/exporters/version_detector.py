#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
版本元数据提取模块

该模块提供从不同项目文件中提取版本信息的功能，支持多种项目格式。
主要特性:
1. 剪映项目版本提取
2. XML格式版本检测
3. 多种编辑软件格式版本提取
4. 版本元数据的统一返回格式
"""

import os
import re
import json
import logging
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional, Union, Tuple
from pathlib import Path

# 配置日志
logger = logging.getLogger(__name__)

# 支持的格式
SUPPORTED_FORMATS = {
    "jianying": "剪映",
    "premiere": "Premiere Pro",
    "fcpxml": "Final Cut Pro",
    "davinci": "DaVinci Resolve",
    "default": "未知格式"
}


def detect_jianying_version(output_path: str) -> str:
    """
    从剪映工程文件中提取版本信息
    
    Args:
        output_path: 剪映工程文件路径
        
    Returns:
        str: 提取到的版本号，如果无法提取则返回"unknown"
    """
    try:
        with open(output_path, 'r', encoding='utf-8') as f:
            for line in f:
                if '<project version' in line or '<jianying_project version' in line:
                    # 提取 version="X.Y" 中的 X.Y
                    match = re.search(r'version=["\']([^"\']+)["\']', line)
                    if match:
                        return match.group(1)
                
                if '<project_version>' in line:
                    # 提取 <project_version>X.Y</project_version> 中的 X.Y
                    match = re.search(r'<project_version>([^<]+)</project_version>', line)
                    if match:
                        return match.group(1)

                # 检查是否包含 "project version" 字段
                if 'project version' in line.lower() and ':' in line:
                    # 提取冒号后面的内容作为版本
                    version_text = line.split(':', 1)[1].strip()
                    # 尝试从文本中提取版本号（数字和点）
                    match = re.search(r'([\d\.]+)', version_text)
                    if match:
                        return match.group(1)
    except Exception as e:
        logger.error(f"从剪映项目文件提取版本失败: {str(e)}")
    
    return "unknown"


def extract_version_from_xml(xml_path: str) -> Dict[str, str]:
    """
    从XML文件中提取版本和格式信息
    
    Args:
        xml_path: XML文件路径
        
    Returns:
        Dict[str, str]: 包含format_type和version的字典
    """
    result = {
        "format_type": "default",
        "version": "unknown"
    }
    
    try:
        # 尝试解析XML
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        # 确定格式类型
        if root.tag == "project" or root.tag == "xmeml":
            if root.find(".//premiere") is not None:
                result["format_type"] = "premiere"
            elif root.find(".//davinci_resolve") is not None:
                result["format_type"] = "davinci"
        elif root.tag == "fcpxml" or root.find(".//fcpxml") is not None:
            result["format_type"] = "fcpxml"
        elif root.tag == "jianying_project" or root.find(".//jianying") is not None or root.find(".//info/metadata/jy_type") is not None:
            result["format_type"] = "jianying"
        
        # 从XML直接提取版本属性
        version_attr = root.get("version")
        if version_attr:
            result["version"] = version_attr
            return result
            
        # 尝试从版本标签提取
        version_nodes = [
            root.find(".//version"),
            root.find(".//format_version"),
            root.find(".//app_version"),
            root.find(".//project_version")
        ]
        
        for node in version_nodes:
            if node is not None and node.text:
                version_text = node.text.strip()
                # 提取版本号（数字和点）
                match = re.search(r'([\d\.]+)', version_text)
                if match:
                    result["version"] = match.group(1)
                    return result
    except Exception as e:
        logger.error(f"从XML提取版本信息失败: {str(e)}")
    
    return result


def extract_version_from_json(json_path: str) -> Dict[str, str]:
    """
    从JSON文件中提取版本信息
    
    Args:
        json_path: JSON文件路径
        
    Returns:
        Dict[str, str]: 包含format_type和version的字典
    """
    result = {
        "format_type": "default",
        "version": "unknown"
    }
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 检查是否为剪映JSON格式
        if "meta" in data and isinstance(data["meta"], dict):
            result["format_type"] = "jianying"
            
            # 尝试从meta中提取版本
            if "version" in data["meta"]:
                result["version"] = str(data["meta"]["version"])
            elif "app_version" in data["meta"]:
                result["version"] = str(data["meta"]["app_version"])
        
        # 如果没有找到版本，尝试递归查找version字段
        if result["version"] == "unknown":
            def find_version_field(obj):
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        if key in ["version", "app_version", "project_version", "format_version"]:
                            if isinstance(value, (str, int, float)):
                                return str(value)
                        
                        # 递归查找
                        sub_result = find_version_field(value)
                        if sub_result != "unknown":
                            return sub_result
                
                elif isinstance(obj, list):
                    for item in obj:
                        sub_result = find_version_field(item)
                        if sub_result != "unknown":
                            return sub_result
                
                return "unknown"
            
            version = find_version_field(data)
            if version != "unknown":
                result["version"] = version
    except Exception as e:
        logger.error(f"从JSON提取版本信息失败: {str(e)}")
    
    return result


def get_format_display_name(format_type: str) -> str:
    """
    获取格式类型的显示名称
    
    Args:
        format_type: 格式类型代码
        
    Returns:
        str: 显示名称
    """
    return SUPPORTED_FORMATS.get(format_type, SUPPORTED_FORMATS["default"])


def detect_version(file_path: str) -> Dict[str, Any]:
    """
    检测文件的格式和版本
    
    Args:
        file_path: 项目文件路径
        
    Returns:
        Dict[str, Any]: 版本信息字典，包含format_type、version和display_name
    """
    result = {
        "format_type": "default",
        "version": "unknown",
        "display_name": SUPPORTED_FORMATS["default"],
        "file_path": file_path
    }
    
    if not os.path.exists(file_path):
        logger.error(f"文件不存在: {file_path}")
        return result
    
    file_ext = os.path.splitext(file_path)[1].lower()
    
    try:
        # 根据文件扩展名选择处理方法
        if file_ext in ['.xml', '.fcpxml']:
            version_info = extract_version_from_xml(file_path)
            result.update(version_info)
        elif file_ext == '.json':
            version_info = extract_version_from_json(file_path)
            result.update(version_info)
        elif file_ext in ['.txt', '.srt', '.vtt']:
            # 简单文本文件，可能需要特殊处理
            logger.info(f"文本文件类型 {file_ext} 不包含版本信息")
        else:
            # 尝试作为XML解析
            try:
                version_info = extract_version_from_xml(file_path)
                result.update(version_info)
            except:
                # 尝试作为JSON解析
                try:
                    version_info = extract_version_from_json(file_path)
                    result.update(version_info)
                except:
                    # 如果是剪映文件，尝试专用方法
                    if "jianying" in file_path.lower():
                        version = detect_jianying_version(file_path)
                        result["version"] = version
                        result["format_type"] = "jianying"
        
        # 设置显示名称
        result["display_name"] = get_format_display_name(result["format_type"])
        
        # 添加文件元数据
        result["file_size"] = os.path.getsize(file_path)
        result["last_modified"] = os.path.getmtime(file_path)
    
    except Exception as e:
        logger.error(f"版本检测失败: {str(e)}")
    
    return result


def detect_jianying_version_from_string(content: str) -> str:
    """
    从字符串内容中提取剪映版本信息
    
    Args:
        content: 文件内容字符串
        
    Returns:
        str: 提取到的版本号，如果无法提取则返回"unknown"
    """
    try:
        # 检查XML格式的版本信息
        if '<project version' in content or '<jianying_project version' in content:
            match = re.search(r'version=["\']([^"\']+)["\']', content)
            if match:
                return match.group(1)
        
        # 检查项目版本标签
        if '<project_version>' in content:
            match = re.search(r'<project_version>([^<]+)</project_version>', content)
            if match:
                return match.group(1)
        
        # 检查JSON格式
        if '"version":' in content or '"app_version":' in content:
            try:
                # 尝试加载为JSON
                data = json.loads(content)
                # 递归查找版本字段
                def find_version(obj):
                    if isinstance(obj, dict):
                        for key, value in obj.items():
                            if key in ["version", "app_version", "project_version"] and isinstance(value, (str, int, float)):
                                return str(value)
                            
                            sub_result = find_version(value)
                            if sub_result != "unknown":
                                return sub_result
                    
                    if isinstance(obj, list):
                        for item in obj:
                            sub_result = find_version(item)
                            if sub_result != "unknown":
                                return sub_result
                    
                    return "unknown"
                
                version = find_version(data)
                if version != "unknown":
                    return version
            except:
                pass
        
        # 使用正则表达式查找版本模式
        version_patterns = [
            r'版本\s*[:：]\s*([\d\.]+)',  # 版本: X.Y 或 版本：X.Y
            r'version\s*[:：]\s*([\d\.]+)',  # version: X.Y
            r'project\s+version\s*[:：]\s*([\d\.]+)',  # project version: X.Y
            r'"version"\s*:\s*"([\d\.]+)"',  # "version": "X.Y"
            r'"app_version"\s*:\s*"([\d\.]+)"',  # "app_version": "X.Y"
        ]
        
        for pattern in version_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1)
    
    except Exception as e:
        logger.error(f"从内容字符串提取版本失败: {str(e)}")
    
    return "unknown"


if __name__ == "__main__":
    # 测试代码
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python version_detector.py <文件路径>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    result = detect_version(file_path)
    
    print(f"文件: {file_path}")
    print(f"格式: {result['display_name']} ({result['format_type']})")
    print(f"版本: {result['version']}")
    print(f"文件大小: {result['file_size']} 字节")
    print(f"最后修改时间: {result['last_modified']}") 