#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
XML结构验证器

提供对XML文件基础结构的验证，确保必要节点存在且符合预期结构。
作为XSD模式验证的补充，此模块聚焦于关键结构元素的存在性检查，
无需深入验证元素内容和类型。
"""

import os
import sys
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Set, Tuple
import logging

# 添加项目根目录到路径
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.utils.log_handler import get_logger
except ImportError:
    # 简单日志替代
    logging.basicConfig(level=logging.INFO)
    def get_logger(name):
        return logging.getLogger(name)

# 配置日志
logger = get_logger("structure_validator")


# 自定义异常
class StructureError(Exception):
    """XML结构错误异常"""
    pass


class XMLStructureValidator:
    """XML结构验证器类"""
    
    # 不同格式的必要节点配置
    FORMAT_REQUIRED_NODES = {
        "jianying": {
            "root": "jianying_project",
            "nodes": ["info", "resources", "timeline"],
            "attributes": {
                "version": "1.0"
            }
        },
        "premiere": {
            "root": "project",
            "nodes": ["meta", "movie"],
            "attributes": {
                "version": "1.0"
            }
        },
        "fcpxml": {
            "root": "fcpxml",
            "nodes": ["resources", "library"],
            "attributes": {
                "version": "1.8"
            }
        },
        "davinci": {
            "root": "xml",
            "nodes": ["project"],
            "attributes": {}
        },
        "default": {
            "root": "project",
            "nodes": ["resources", "timeline"],
            "attributes": {}
        }
    }
    
    def __init__(self):
        """初始化结构验证器"""
        self.logger = logger
    
    def detect_format(self, xml_root: ET.Element) -> str:
        """
        检测XML格式类型
        
        Args:
            xml_root: XML根元素
            
        Returns:
            str: 格式类型名称，如"jianying", "premiere"等
        """
        root_tag = xml_root.tag
        
        # 根据根标签判断
        if root_tag == "jianying_project":
            return "jianying"
        elif root_tag == "project":
            # 进一步区分Premiere和其他project根标签格式
            if xml_root.find("./movie") is not None:
                return "premiere"
            else:
                return "default"
        elif root_tag == "fcpxml":
            return "fcpxml"
        elif root_tag == "xml" and xml_root.find("./project") is not None:
            return "davinci"
        
        # 如果没有匹配到，使用默认格式
        return "default"
    
    def validate_root_structure(self, xml_root: ET.Element) -> Tuple[bool, List[str]]:
        """
        验证根节点结构合规性
        
        Args:
            xml_root: XML根元素
            
        Returns:
            Tuple[bool, List[str]]: (验证结果, 错误信息列表)
        """
        # 检测格式
        format_type = self.detect_format(xml_root)
        self.logger.info(f"检测到XML格式类型: {format_type}")
        
        # 获取该格式的必要节点配置
        config = self.FORMAT_REQUIRED_NODES.get(format_type, self.FORMAT_REQUIRED_NODES["default"])
        
        # 验证根标签
        if xml_root.tag != config["root"]:
            return False, [f"根标签错误: 预期 '{config['root']}', 实际为 '{xml_root.tag}'"]
        
        # 验证必要属性
        errors = []
        for attr, expected_value in config["attributes"].items():
            if attr not in xml_root.attrib:
                errors.append(f"缺少必要属性: '{attr}'")
            elif expected_value and xml_root.attrib[attr] != expected_value:
                errors.append(f"属性值错误: '{attr}' 预期为 '{expected_value}', 实际为 '{xml_root.attrib[attr]}'")
        
        # 验证必要节点
        required_nodes = config["nodes"]
        for node in required_nodes:
            if xml_root.find(f".//{node}") is None:
                errors.append(f"关键节点缺失: '{node}'")
        
        # 返回验证结果
        is_valid = len(errors) == 0
        return is_valid, errors
    
    def validate_detailed_structure(self, xml_root: ET.Element, format_type: Optional[str] = None) -> Tuple[bool, List[str]]:
        """
        进行详细的结构验证，根据不同格式有不同的验证规则
        
        Args:
            xml_root: XML根元素
            format_type: 格式类型，如果为None则自动检测
            
        Returns:
            Tuple[bool, List[str]]: (验证结果, 错误信息列表)
        """
        # 如果未指定格式，则检测格式
        if format_type is None:
            format_type = self.detect_format(xml_root)
        
        # 先进行基础结构验证
        is_valid, errors = self.validate_root_structure(xml_root)
        if not is_valid:
            return is_valid, errors
        
        # 根据不同格式进行特定验证
        if format_type == "jianying":
            return self._validate_jianying_structure(xml_root)
        elif format_type == "premiere":
            return self._validate_premiere_structure(xml_root)
        elif format_type == "fcpxml":
            return self._validate_fcpxml_structure(xml_root)
        elif format_type == "davinci":
            return self._validate_davinci_structure(xml_root)
        else:
            # 对于未知格式，只进行基础验证
            return True, []
    
    def _validate_jianying_structure(self, xml_root: ET.Element) -> Tuple[bool, List[str]]:
        """剪映格式特定结构验证"""
        errors = []
        
        # 检查info/metadata节点必须包含必要子节点
        metadata = xml_root.find(".//info/metadata")
        if metadata is not None:
            # 检查必要元数据字段
            required_metadata = ["jy_type", "project_id"]
            for field in required_metadata:
                if metadata.find(f"./{field}") is None:
                    errors.append(f"metadata缺少必要字段: '{field}'")
        
        # 检查timeline必须有id和duration属性
        timeline = xml_root.find(".//timeline")
        if timeline is not None:
            required_attrs = ["id", "duration"]
            for attr in required_attrs:
                if attr not in timeline.attrib:
                    errors.append(f"timeline缺少必要属性: '{attr}'")
        
        # 返回验证结果
        is_valid = len(errors) == 0
        return is_valid, errors
    
    def _validate_premiere_structure(self, xml_root: ET.Element) -> Tuple[bool, List[str]]:
        """Premiere格式特定结构验证"""
        errors = []
        
        # 检查movie/sequence节点必须存在
        sequence = xml_root.find(".//movie/sequence")
        if sequence is None:
            errors.append("缺少必要节点: 'movie/sequence'")
        else:
            # 检查sequence必须有id和name属性
            required_attrs = ["id", "name"]
            for attr in required_attrs:
                if attr not in sequence.attrib:
                    errors.append(f"sequence缺少必要属性: '{attr}'")
            
            # 检查必要的子节点
            required_nodes = ["duration", "rate", "timecode"]
            for node in required_nodes:
                if sequence.find(f"./{node}") is None:
                    errors.append(f"sequence缺少必要子节点: '{node}'")
        
        # 返回验证结果
        is_valid = len(errors) == 0
        return is_valid, errors
    
    def _validate_fcpxml_structure(self, xml_root: ET.Element) -> Tuple[bool, List[str]]:
        """FCPXML格式特定结构验证"""
        # 此处添加FCPXML特定验证逻辑
        return True, []  # 暂时不做详细验证
    
    def _validate_davinci_structure(self, xml_root: ET.Element) -> Tuple[bool, List[str]]:
        """DaVinci Resolve格式特定结构验证"""
        # 此处添加DaVinci特定验证逻辑
        return True, []  # 暂时不做详细验证


# 提供便捷函数
def validate_root_structure(xml_root: ET.Element) -> bool:
    """
    验证根节点结构合规性的便捷函数
    
    Args:
        xml_root: XML根元素
        
    Returns:
        bool: 验证是否通过
        
    Raises:
        StructureError: 当验证失败时抛出的异常
    """
    validator = XMLStructureValidator()
    is_valid, errors = validator.validate_root_structure(xml_root)
    
    if not is_valid:
        error_msg = "; ".join(errors)
        raise StructureError(error_msg)
    
    return True


def validate_xml_structure(xml_path: str) -> bool:
    """
    验证XML文件结构合规性的便捷函数
    
    Args:
        xml_path: XML文件路径
        
    Returns:
        bool: 验证是否通过
        
    Raises:
        StructureError: 当验证失败时抛出的异常
    """
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        return validate_root_structure(root)
    except ET.ParseError as e:
        logger.error(f"XML解析错误: {str(e)}")
        raise StructureError(f"XML解析错误: {str(e)}")
    except Exception as e:
        logger.error(f"验证XML结构时发生错误: {str(e)}")
        raise StructureError(f"验证失败: {str(e)}")


if __name__ == "__main__":
    # 作为脚本运行时的简单测试
    import argparse
    
    parser = argparse.ArgumentParser(description='验证XML结构合规性')
    parser.add_argument('xml_path', help='要验证的XML文件路径')
    parser.add_argument('--detailed', action='store_true', help='执行详细结构验证')
    
    args = parser.parse_args()
    
    try:
        tree = ET.parse(args.xml_path)
        root = tree.getroot()
        
        validator = XMLStructureValidator()
        
        if args.detailed:
            is_valid, errors = validator.validate_detailed_structure(root)
            print(f"详细结构验证结果: {'通过' if is_valid else '失败'}")
            if not is_valid:
                for error in errors:
                    print(f"  - {error}")
        else:
            is_valid, errors = validator.validate_root_structure(root)
            print(f"基础结构验证结果: {'通过' if is_valid else '失败'}")
            if not is_valid:
                for error in errors:
                    print(f"  - {error}")
        
        sys.exit(0 if is_valid else 1)
        
    except Exception as e:
        print(f"验证失败: {str(e)}")
        sys.exit(1) 