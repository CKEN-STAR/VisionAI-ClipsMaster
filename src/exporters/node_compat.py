#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
必需节点补偿模块

该模块提供功能，确保XML文件包含特定版本所需的节点和属性。
主要功能包括：
1. 添加必需节点：根据版本规格自动补充必需节点
2. 添加默认属性：为节点添加默认属性值
3. 根据版本规格进行节点补偿
"""

import os
import logging
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional, Union, Tuple
import re
import json

from src.utils.log_handler import get_logger

# 获取日志记录器
logger = get_logger("node_compat")

def add_required_nodes(xml_root: ET.Element, version_spec: Dict[str, Any]) -> ET.Element:
    """为旧版本添加必要识别节点
    
    根据版本规格为XML添加必需的节点，确保版本兼容性
    
    Args:
        xml_root: XML根元素
        version_spec: 版本规格，包含必需节点信息
        
    Returns:
        ET.Element: 修改后的XML根元素
    """
    try:
        # 检查version_spec中是否包含required_nodes列表
        if 'required_nodes' not in version_spec:
            logger.warning("版本规格中未找到必需节点列表")
            return xml_root
            
        # 遍历必需节点列表
        for node_path in version_spec['required_nodes']:
            # 解析节点路径
            parts = node_path.split('/')
            
            # 从根元素开始追踪和添加节点
            current = xml_root
            for i, part in enumerate(parts):
                # 检查是否包含属性
                attr_match = re.match(r'(.+)\[@(.+)=\'(.+)\'\]', part)
                if attr_match:
                    # 包含属性的节点
                    node_name = attr_match.group(1)
                    attr_name = attr_match.group(2)
                    attr_value = attr_match.group(3)
                    
                    # 尝试查找具有匹配属性的节点
                    found = False
                    for child in current.findall(node_name):
                        if child.get(attr_name) == attr_value:
                            current = child
                            found = True
                            break
                    
                    # 如果未找到节点，创建它
                    if not found:
                        new_node = ET.SubElement(current, node_name)
                        new_node.set(attr_name, attr_value)
                        current = new_node
                        logger.info(f"添加必需节点: {node_name} 带属性 {attr_name}='{attr_value}'")
                else:
                    # 不包含属性的普通节点
                    child = current.find(part)
                    if child is None:
                        # 节点不存在，创建它
                        current = ET.SubElement(current, part)
                        
                        # 添加默认文本和属性
                        if i == len(parts) - 1 and 'default_values' in version_spec:
                            if node_path in version_spec['default_values']:
                                default_value = version_spec['default_values'][node_path]
                                if isinstance(default_value, dict):
                                    # 处理属性字典
                                    for attr_name, attr_val in default_value.items():
                                        if attr_name == '_text':
                                            current.text = str(attr_val)
                                        else:
                                            current.set(attr_name, str(attr_val))
                                else:
                                    # 简单文本值
                                    current.text = str(default_value)
                        
                        logger.info(f"添加必需节点: {part}")
                    else:
                        current = child
        
        # 处理强制属性
        if 'required_attributes' in version_spec:
            for node_path, attributes in version_spec['required_attributes'].items():
                node = xml_root.find(node_path)
                if node is not None:
                    for attr_name, attr_value in attributes.items():
                        if node.get(attr_name) is None:
                            node.set(attr_name, str(attr_value))
                            logger.info(f"为节点 {node_path} 添加必需属性: {attr_name}='{attr_value}'")
        
        return xml_root
    except Exception as e:
        logger.error(f"添加必需节点时出错: {str(e)}")
        # 返回原始根元素，避免破坏XML结构
        return xml_root

def remove_unsupported_nodes(xml_root: ET.Element, version_spec: Dict[str, Any]) -> ET.Element:
    """移除不支持的节点
    
    根据版本规格中的不支持节点列表，从XML中移除这些节点
    
    Args:
        xml_root: XML根元素
        version_spec: 版本规格，包含不支持节点信息
        
    Returns:
        ET.Element: 修改后的XML根元素
    """
    try:
        # 检查version_spec中是否包含unsupported_nodes列表
        if 'unsupported_nodes' not in version_spec:
            return xml_root
            
        # 遍历不支持节点列表
        for node_path in version_spec['unsupported_nodes']:
            # 查找所有匹配的节点
            nodes = xml_root.findall(node_path)
            
            # 移除这些节点
            for node in nodes:
                parent = xml_root.getparent(node)
                if parent is not None:
                    parent.remove(node)
                    logger.info(f"移除不支持的节点: {node_path}")
        
        return xml_root
    except Exception as e:
        logger.error(f"移除不支持节点时出错: {str(e)}")
        # 返回原始根元素，避免破坏XML结构
        return xml_root

def verify_required_nodes(xml_root: ET.Element, version_spec: Dict[str, Any]) -> List[str]:
    """验证必需节点
    
    检查XML是否包含所有版本规格中定义的必需节点
    
    Args:
        xml_root: XML根元素
        version_spec: 版本规格，包含必需节点信息
        
    Returns:
        List[str]: 缺失节点的列表，如果没有缺失则为空列表
    """
    missing_nodes = []
    
    # 检查version_spec中是否包含required_nodes列表
    if 'required_nodes' not in version_spec:
        return missing_nodes
        
    # 遍历必需节点列表
    for node_path in version_spec['required_nodes']:
        # 解析节点路径
        parts = node_path.split('/')
        
        # 从根元素开始追踪节点
        current = xml_root
        node_exists = True
        
        for part in parts:
            # 检查是否包含属性
            attr_match = re.match(r'(.+)\[@(.+)=\'(.+)\'\]', part)
            if attr_match:
                # 包含属性的节点
                node_name = attr_match.group(1)
                attr_name = attr_match.group(2)
                attr_value = attr_match.group(3)
                
                # 尝试查找具有匹配属性的节点
                found = False
                for child in current.findall(node_name):
                    if child.get(attr_name) == attr_value:
                        current = child
                        found = True
                        break
                
                if not found:
                    node_exists = False
                    break
            else:
                # 不包含属性的普通节点
                child = current.find(part)
                if child is None:
                    node_exists = False
                    break
                current = child
        
        if not node_exists:
            missing_nodes.append(node_path)
            
    return missing_nodes

def validate_version_compatibility(xml_root: ET.Element, target_version: str) -> Tuple[bool, List[str]]:
    """验证版本兼容性
    
    检查XML是否满足目标版本的所有要求
    
    Args:
        xml_root: XML根元素
        target_version: 目标版本
        
    Returns:
        Tuple[bool, List[str]]: 是否兼容，以及不兼容原因列表
    """
    try:
        # 获取版本规格
        version_spec = get_version_specification(target_version)
        if version_spec is None:
            return False, [f"未找到版本 {target_version} 的规格"]
        
        # 验证必需节点
        missing_nodes = verify_required_nodes(xml_root, version_spec)
        
        # 验证版本属性
        version_attr = xml_root.get("version")
        if version_attr != target_version:
            missing_nodes.append(f"根元素版本属性不匹配: {version_attr} != {target_version}")
        
        if missing_nodes:
            return False, missing_nodes
        return True, []
    except Exception as e:
        logger.error(f"验证版本兼容性时出错: {str(e)}")
        return False, [str(e)]

def get_version_specification(version: str) -> Optional[Dict[str, Any]]:
    """获取版本规格
    
    从配置中获取特定版本的规格信息
    
    Args:
        version: 版本号
        
    Returns:
        Optional[Dict[str, Any]]: 版本规格，如果未找到则返回None
    """
    # 获取版本规格的路径
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                'configs', 'version_specifications.json')
    
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                specs = json.load(f)
                return specs.get(version)
    except Exception as e:
        logger.error(f"获取版本规格时出错: {str(e)}")
    
    # 返回默认规格
    return get_default_specification(version)

def get_default_specification(version: str) -> Dict[str, Any]:
    """获取默认版本规格
    
    为特定版本提供默认规格
    
    Args:
        version: 版本号
        
    Returns:
        Dict[str, Any]: 默认版本规格
    """
    if version == "3.0.0":
        return {
            "required_nodes": [
                "info/metadata",
                "info/project_settings",
                "info/project_settings/resolution",
                "resources",
                "timeline"
            ],
            "default_values": {
                "info/project_settings/resolution": {
                    "width": "1920",
                    "height": "1080"
                }
            },
            "required_attributes": {
                "timeline": {
                    "id": "main_timeline",
                    "duration": "00:00:00.000"
                }
            }
        }
    elif version == "2.9.5":
        return {
            "required_nodes": [
                "info/metadata",
                "info/project_settings",
                "info/project_settings/resolution",
                "resources",
                "timeline"
            ],
            "default_values": {
                "info/project_settings/resolution": {
                    "width": "1920",
                    "height": "1080"
                }
            },
            "required_attributes": {
                "timeline": {
                    "id": "main_timeline",
                    "duration": "00:00:00.000"
                }
            },
            "unsupported_nodes": [
                ".//nested_sequence",
                ".//4K"
            ]
        }
    elif version == "2.5.0":
        return {
            "required_nodes": [
                "info/metadata",
                "info/project_settings",
                "info/project_settings/resolution",
                "resources",
                "timeline"
            ],
            "default_values": {
                "info/project_settings/resolution": {
                    "width": "1920",
                    "height": "1080"
                }
            },
            "required_attributes": {
                "timeline": {
                    "id": "main_timeline",
                    "duration": "00:00:00.000"
                }
            },
            "unsupported_nodes": [
                ".//nested_sequence",
                ".//4K",
                ".//effects_track"
            ]
        }
    elif version == "2.0.0":
        return {
            "required_nodes": [
                "info/metadata",
                "info/project_settings",
                "info/project_settings/resolution",
                "resources",
                "timeline"
            ],
            "default_values": {
                "info/project_settings/resolution": {
                    "width": "1280",
                    "height": "720"
                }
            },
            "required_attributes": {
                "timeline": {
                    "id": "main_timeline",
                    "duration": "00:00:00.000"
                }
            },
            "unsupported_nodes": [
                ".//nested_sequence",
                ".//4K",
                ".//effects_track",
                ".//keyframe"
            ]
        }
    else:
        logger.warning(f"未定义版本 {version} 的默认规格，使用通用规格")
        return {
            "required_nodes": [
                "info/metadata",
                "resources",
                "timeline"
            ],
            "default_values": {},
            "required_attributes": {},
            "unsupported_nodes": []
        }

def process_xml_file(xml_path: str, target_version: str, output_path: Optional[str] = None) -> bool:
    """处理XML文件
    
    对XML文件进行必需节点补偿处理
    
    Args:
        xml_path: XML文件路径
        target_version: 目标版本
        output_path: 输出路径，如果为None则覆盖原文件
        
    Returns:
        bool: 处理是否成功
    """
    try:
        # 解析XML文件
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        # 获取版本规格
        version_spec = get_version_specification(target_version)
        if version_spec is None:
            logger.error(f"未找到版本 {target_version} 的规格")
            return False
        
        # 添加必需节点
        root = add_required_nodes(root, version_spec)
        
        # 移除不支持的节点
        root = remove_unsupported_nodes(root, version_spec)
        
        # 设置版本属性
        root.set("version", target_version)
        
        # 保存处理后的XML
        if output_path is None:
            output_path = xml_path
            
        tree.write(output_path, encoding="utf-8", xml_declaration=True)
        
        logger.info(f"成功处理XML文件: {xml_path} -> {output_path}")
        return True
    except Exception as e:
        logger.error(f"处理XML文件时出错: {str(e)}")
        return False

def batch_process_directory(directory: str, target_version: str, output_dir: Optional[str] = None) -> Dict[str, bool]:
    """批量处理目录中的XML文件
    
    Args:
        directory: 目录路径
        target_version: 目标版本
        output_dir: 输出目录，如果为None则覆盖原文件
        
    Returns:
        Dict[str, bool]: 处理结果，键为文件路径，值为处理是否成功
    """
    results = {}
    
    try:
        # 获取所有XML文件
        xml_files = [f for f in os.listdir(directory) if f.lower().endswith('.xml')]
        
        for file_name in xml_files:
            input_path = os.path.join(directory, file_name)
            
            if output_dir is not None:
                # 确保输出目录存在
                os.makedirs(output_dir, exist_ok=True)
                output_path = os.path.join(output_dir, file_name)
            else:
                output_path = input_path
                
            # 处理文件
            result = process_xml_file(input_path, target_version, output_path)
            results[input_path] = result
            
        return results
    except Exception as e:
        logger.error(f"批量处理目录时出错: {str(e)}")
        return results

# 主函数，用于命令行调用
if __name__ == "__main__":
    import sys
    import argparse
    
    # 设置日志级别
    logging.basicConfig(level=logging.INFO,
                       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # 创建参数解析器
    parser = argparse.ArgumentParser(description="XML节点兼容性处理工具")
    parser.add_argument("input", help="输入XML文件或目录")
    parser.add_argument("--output", "-o", help="输出文件或目录路径")
    parser.add_argument("--version", "-v", required=True, help="目标版本")
    parser.add_argument("--batch", "-b", action="store_true", help="批量处理目录")
    
    # 解析参数
    args = parser.parse_args()
    
    if args.batch:
        # 批量处理目录
        results = batch_process_directory(args.input, args.version, args.output)
        
        # 输出统计信息
        success_count = sum(1 for success in results.values() if success)
        total_count = len(results)
        
        print(f"批量处理完成: 成功 {success_count}/{total_count}")
    else:
        # 处理单个文件
        success = process_xml_file(args.input, args.version, args.output)
        
        if success:
            print(f"成功处理XML文件: {args.input}")
        else:
            print(f"处理XML文件失败: {args.input}")
            sys.exit(1) 