#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
版本兼容性适配模块

该模块提供版本兼容性转换功能，确保导出的项目文件能够在不同版本的软件中兼容运行。
主要功能包括:
1. 向后兼容性修复，使新版本生成的文件适配旧版本软件
2. 版本升级转换，将旧版本文件升级到新版本格式
3. 版本检测与验证
"""

import os
import logging
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional, Union, Tuple
from pathlib import Path
import re
import json

from src.utils.log_handler import get_logger

# 获取日志记录器
logger = get_logger("version_compat")

# 支持的版本常量
VERSIONS = {
    "1.0": "初始版本",
    "2.0": "添加元数据支持",
    "2.5": "添加高级时间线格式",
    "3.0": "当前最新版本，支持4K处理",
    "3.1": "未来版本，实验性支持"
}

# 版本兼容性映射
VERSION_COMPATIBILITY = {
    "3.0": ["2.5", "2.0"],  # 3.0版本兼容2.5和2.0
    "2.5": ["2.0"],         # 2.5版本兼容2.0
    "2.0": ["1.0"],         # 2.0版本兼容1.0
    "1.0": []               # 1.0版本没有向下兼容版本
}

class VersionError(Exception):
    """版本兼容性错误"""
    pass

def get_xml_version(xml_tree: ET.ElementTree) -> str:
    """
    获取XML项目文件的版本
    
    Args:
        xml_tree: XML元素树
        
    Returns:
        str: 版本号
    """
    root = xml_tree.getroot()
    version = root.get("version", "1.0")  # 默认版本为1.0
    
    return version

def is_version_compatible(source_version: str, target_version: str) -> bool:
    """
    检查源版本是否与目标版本兼容
    
    Args:
        source_version: 源版本
        target_version: 目标版本
        
    Returns:
        bool: 是否兼容
    """
    if source_version == target_version:
        return True
    
    # 检查目标版本是否在源版本的兼容列表中
    if target_version in VERSION_COMPATIBILITY.get(source_version, []):
        return True
    
    return False

def backward_compatibility_fix(xml_tree: ET.ElementTree, target_version: str) -> ET.ElementTree:
    """
    修改XML文件以向后兼容旧版本
    
    Args:
        xml_tree: XML元素树
        target_version: 目标版本
        
    Returns:
        ET.ElementTree: 修改后的XML元素树
    """
    root = xml_tree.getroot()
    current_version = root.get("version", "3.0")
    
    logger.info(f"正在进行版本兼容性适配: 从 {current_version} 到 {target_version}")
    
    # 如果当前版本已经是目标版本，无需适配
    if current_version == target_version:
        return xml_tree
    
    # 检查是否支持目标版本
    if target_version not in VERSIONS:
        raise VersionError(f"不支持的目标版本: {target_version}")
    
    # 检查是否能够向下兼容到目标版本
    if not is_version_compatible(current_version, target_version):
        logger.warning(f"版本 {current_version} 无法直接兼容到 {target_version}，尝试逐级转换")
        
        # 尝试逐级向下转换
        intermediate_versions = find_conversion_path(current_version, target_version)
        if not intermediate_versions:
            raise VersionError(f"无法从版本 {current_version} 转换到 {target_version}")
        
        # 逐级转换
        for iv in intermediate_versions:
            xml_tree = _convert_to_specific_version(xml_tree, iv)
    else:
        # 直接转换到目标版本
        xml_tree = _convert_to_specific_version(xml_tree, target_version)
    
    return xml_tree

def _convert_to_specific_version(xml_tree: ET.ElementTree, target_version: str) -> ET.ElementTree:
    """
    将XML转换为特定版本格式
    
    Args:
        xml_tree: XML元素树
        target_version: 目标版本
        
    Returns:
        ET.ElementTree: 转换后的XML元素树
    """
    root = xml_tree.getroot()
    current_version = root.get("version", "3.0")
    
    logger.info(f"正在转换: {current_version} -> {target_version}")
    
    # 3.0 -> 2.5 转换
    if current_version == "3.0" and target_version == "2.5":
        # 移除4K相关属性
        for node in root.findall(".//resolution[@type='4k']"):
            node.getparent().remove(node)
        
        # 修改版本号
        root.set("version", "2.5")
    
    # 3.0 -> 2.0 转换
    elif current_version == "3.0" and target_version == "2.0":
        # 移除4K相关属性
        for node in root.findall(".//resolution[@type='4k']"):
            node.getparent().remove(node)
        
        # 移除高级时间线格式
        for node in root.findall(".//timeline[@advanced='true']"):
            node.attrib.pop("advanced", None)
        
        # 修改版本号
        root.set("version", "2.0")
    
    # 2.5 -> 2.0 转换
    elif current_version == "2.5" and target_version == "2.0":
        # 移除高级时间线格式
        for node in root.findall(".//timeline[@advanced='true']"):
            node.attrib.pop("advanced", None)
        
        # 修改版本号
        root.set("version", "2.0")
    
    # 2.0 -> 1.0 转换
    elif current_version == "2.0" and target_version == "1.0":
        # 移除元数据
        meta_node = root.find("./meta")
        if meta_node is not None:
            root.remove(meta_node)
        
        # 修改版本号
        root.set("version", "1.0")
    
    # 特殊处理：针对旧版本不支持的特性
    if target_version < "3.0":
        # 移除4K标签
        for node in root.findall(".//4K"):
            node.getparent().remove(node)
    
    return xml_tree

def upgrade_version(xml_tree: ET.ElementTree, target_version: str) -> ET.ElementTree:
    """
    将XML文件升级到较新版本
    
    Args:
        xml_tree: XML元素树
        target_version: 目标版本
        
    Returns:
        ET.ElementTree: 升级后的XML元素树
    """
    root = xml_tree.getroot()
    current_version = root.get("version", "1.0")
    
    logger.info(f"正在升级版本: 从 {current_version} 到 {target_version}")
    
    # 如果当前版本已经是目标版本或更高，无需升级
    if compare_versions(current_version, target_version) >= 0:
        logger.info(f"当前版本 {current_version} 已经是目标版本 {target_version} 或更高，无需升级")
        return xml_tree
    
    # 检查是否支持目标版本
    if target_version not in VERSIONS:
        raise VersionError(f"不支持的目标版本: {target_version}")
    
    # 1.0 -> 2.0 升级
    if current_version == "1.0" and (target_version == "2.0" or compare_versions(target_version, "2.0") > 0):
        # 添加元数据
        if root.find("./meta") is None:
            meta = ET.SubElement(root, "meta")
            ET.SubElement(meta, "created").text = datetime.now().isoformat()
            ET.SubElement(meta, "version").text = "2.0"
        
        # 如果目标版本是2.0，就停止升级
        if target_version == "2.0":
            root.set("version", "2.0")
            return xml_tree
    
    # 2.0 -> 2.5 升级
    if current_version <= "2.0" and (target_version == "2.5" or compare_versions(target_version, "2.5") > 0):
        # 升级时间线格式
        timeline_nodes = root.findall(".//timeline")
        for timeline in timeline_nodes:
            timeline.set("advanced", "true")
        
        # 如果目标版本是2.5，就停止升级
        if target_version == "2.5":
            root.set("version", "2.5")
            return xml_tree
    
    # 2.5 -> 3.0 升级
    if current_version <= "2.5" and target_version == "3.0":
        # 添加4K支持
        settings = root.find("./settings")
        if settings is None:
            settings = ET.SubElement(root, "settings")
        
        resolution = ET.SubElement(settings, "resolution")
        resolution.set("type", "4k")
        resolution.set("width", "3840")
        resolution.set("height", "2160")
        
        # 更新版本号
        root.set("version", "3.0")
    
    return xml_tree

def compare_versions(version1: str, version2: str) -> int:
    """
    比较两个版本号的大小
    
    Args:
        version1: 第一个版本号
        version2: 第二个版本号
        
    Returns:
        int: 如果version1 > version2返回1，相等返回0，小于返回-1
    """
    v1_parts = list(map(int, version1.split('.')))
    v2_parts = list(map(int, version2.split('.')))
    
    # 补齐位数
    while len(v1_parts) < len(v2_parts):
        v1_parts.append(0)
    while len(v2_parts) < len(v1_parts):
        v2_parts.append(0)
    
    for i in range(len(v1_parts)):
        if v1_parts[i] > v2_parts[i]:
            return 1
        elif v1_parts[i] < v2_parts[i]:
            return -1
    
    return 0

def find_conversion_path(source_version: str, target_version: str) -> List[str]:
    """
    查找从源版本到目标版本的转换路径
    
    Args:
        source_version: 源版本
        target_version: 目标版本
        
    Returns:
        List[str]: 转换路径中的版本列表
    """
    if source_version == target_version:
        return []
    
    # 版本降级路径
    if compare_versions(source_version, target_version) > 0:
        versions = sorted(VERSIONS.keys(), key=lambda v: compare_versions(v, "0"), reverse=True)
        path = []
        
        for v in versions:
            if compare_versions(v, target_version) >= 0 and compare_versions(v, source_version) < 0:
                path.append(v)
        
        path.append(target_version)
        return path
    
    # 版本升级路径
    else:
        versions = sorted(VERSIONS.keys(), key=lambda v: compare_versions(v, "0"))
        path = []
        
        for v in versions:
            if compare_versions(v, source_version) > 0 and compare_versions(v, target_version) <= 0:
                path.append(v)
        
        return path

def process_xml_file(input_path: str, output_path: str, target_version: str) -> bool:
    """
    处理XML文件，进行版本兼容性转换
    
    Args:
        input_path: 输入文件路径
        output_path: 输出文件路径
        target_version: 目标版本
        
    Returns:
        bool: 处理是否成功
    """
    try:
        # 解析XML
        tree = ET.parse(input_path)
        root = tree.getroot()
        
        # 获取当前版本
        current_version = root.get("version", "3.0")
        
        # 进行版本转换
        if compare_versions(current_version, target_version) > 0:
            # 降级
            tree = backward_compatibility_fix(tree, target_version)
        else:
            # 升级
            tree = upgrade_version(tree, target_version)
        
        # 保存结果
        tree.write(output_path, encoding="utf-8", xml_declaration=True)
        logger.info(f"版本转换成功: {input_path} -> {output_path} (版本: {target_version})")
        
        return True
    
    except Exception as e:
        logger.error(f"版本转换失败: {str(e)}")
        return False

def batch_process_directory(directory: str, target_version: str, output_dir: Optional[str] = None) -> Dict[str, bool]:
    """
    批量处理目录中的XML文件
    
    Args:
        directory: 输入目录
        target_version: 目标版本
        output_dir: 输出目录，默认为在原文件名后添加后缀
        
    Returns:
        Dict[str, bool]: 文件处理结果
    """
    results = {}
    dir_path = Path(directory)
    
    if output_dir is None:
        output_dir = directory
    else:
        os.makedirs(output_dir, exist_ok=True)
    
    for xml_file in dir_path.glob("*.xml"):
        input_path = str(xml_file)
        file_name = xml_file.name
        output_name = f"{xml_file.stem}_v{target_version.replace('.', '_')}.xml"
        output_path = os.path.join(output_dir, output_name)
        
        success = process_xml_file(input_path, output_path, target_version)
        results[file_name] = success
    
    return results

if __name__ == "__main__":
    # 简单测试
    from datetime import datetime
    import tempfile
    
    # 创建测试XML
    test_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<project version="3.0">
  <meta>
    <created>{datetime.now().isoformat()}</created>
    <author>VisionAI-ClipsMaster</author>
  </meta>
  <settings>
    <resolution type="4k" width="3840" height="2160" />
  </settings>
  <timeline advanced="true">
    <clip id="clip1" start="0" duration="10" />
    <clip id="clip2" start="10" duration="5" />
  </timeline>
</project>
"""
    
    # 保存测试文件
    temp_dir = tempfile.mkdtemp()
    input_path = os.path.join(temp_dir, "test_v3.xml")
    
    with open(input_path, "w", encoding="utf-8") as f:
        f.write(test_xml)
    
    # 转换到2.0版本
    output_path = os.path.join(temp_dir, "test_v2.xml")
    process_xml_file(input_path, output_path, "2.0")
    
    # 读取并打印结果
    with open(output_path, "r", encoding="utf-8") as f:
        print(f.read())
    
    # 清理临时文件
    os.remove(input_path)
    os.remove(output_path)
    os.rmdir(temp_dir) 