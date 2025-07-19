#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
XML格式合规性验证模块

提供对导出XML文件的格式合规性验证，确保:
1. 存在必要的法律声明节点
2. XML结构完整
3. 遵循推荐的XML格式规范

支持高性能的流式验证方式以减少内存使用，特别适用于大型XML文件
"""

import os
import sys
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple, Set
import logging

# 添加项目根目录到路径
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.utils.log_handler import get_logger
    from src.validation.xsd_schema_loader import (
        load_xsd_schema, 
        validate_xml_with_schema,
        detect_format_and_version
    )
except ImportError:
    # 简单日志替代
    logging.basicConfig(level=logging.INFO)
    def get_logger(name):
        return logging.getLogger(name)
    # Schema validation stubs if import fails
    def load_xsd_schema(*args, **kwargs):
        return None
    def validate_xml_with_schema(*args, **kwargs):
        return {"valid": False, "errors": ["Schema validation module not available"]}
    def detect_format_and_version(*args, **kwargs):
        return {"format_type": "default", "version": "1"}

# 配置日志
logger = get_logger("xml_validator")


def validate_legal_nodes(xml_path: str) -> bool:
    """
    验证法律声明节点是否存在
    
    Args:
        xml_path: XML文件路径
        
    Returns:
        bool: 验证是否通过
    """
    logger.info(f"验证XML文件法律声明节点: {xml_path}")
    
    try:
        # 解析XML文件
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        # 检查元数据节点和免责声明
        disclaimer_node = root.find(".//meta/disclaimer")
        if disclaimer_node is None:
            # 尝试其他可能的路径
            disclaimer_node = root.find(".//metadata/disclaimer")
            
        if disclaimer_node is None:
            logger.error("法律声明缺失")
            return False
        
        # 检查免责声明内容是否包含生成标记
        disclaimer_text = disclaimer_node.text
        if disclaimer_text is None or "AI Generated" not in disclaimer_text:
            logger.error("法律声明不包含AI生成标记")
            return False
            
        logger.info("法律声明验证通过")
        return True
        
    except Exception as e:
        logger.error(f"XML验证失败: {str(e)}")
        return False


def validate_xml_structure(xml_path: str) -> bool:
    """
    验证XML结构是否完整
    
    Args:
        xml_path: XML文件路径
        
    Returns:
        bool: 验证是否通过
    """
    logger.info(f"验证XML结构完整性: {xml_path}")
    
    try:
        # 解析XML文件
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        # 检查必要的基础结构
        required_elements = {
            "project": root.tag == "project",
            "resources": root.find(".//resources") is not None,
            "timeline": root.find(".//timeline") is not None
        }
        
        # 检查结果
        missing_elements = [elem for elem, exists in required_elements.items() if not exists]
        
        if missing_elements:
            logger.error(f"XML结构不完整，缺少元素: {', '.join(missing_elements)}")
            return False
            
        logger.info("XML结构验证通过")
        return True
        
    except Exception as e:
        logger.error(f"XML结构验证失败: {str(e)}")
        return False


def validate_schema(xml_path: str) -> bool:
    """
    使用XSD模式验证XML文件
    
    Args:
        xml_path: XML文件路径
        
    Returns:
        bool: 验证是否通过
    """
    logger.info(f"使用XSD模式验证XML文件: {xml_path}")
    
    try:
        # 检测XML格式和版本
        format_info = detect_format_and_version(xml_path)
        format_type = format_info["format_type"]
        version = format_info["version"]
        
        logger.info(f"检测到XML格式: {format_type}, 版本: {version}")
        
        # 验证XML与模式
        result = validate_xml_with_schema(xml_path, format_type, version)
        
        if not result["valid"]:
            logger.error("XSD模式验证失败:")
            for error in result["errors"]:
                logger.error(f"  - {error}")
            return False
            
        logger.info("XSD模式验证通过")
        return True
        
    except Exception as e:
        logger.error(f"XSD模式验证过程出错: {str(e)}")
        return False


def validate_export_xml(xml_path: str, strict: bool = False) -> Dict[str, bool]:
    """
    全面验证导出的XML文件
    
    Args:
        xml_path: XML文件路径
        strict: 是否使用严格模式验证
        
    Returns:
        Dict[str, bool]: 各项验证结果
    """
    logger.info(f"开始全面验证XML文件: {xml_path}")
    
    # 验证结果
    results = {
        "exists": os.path.exists(xml_path),
        "legal_nodes": False,
        "structure": False,
        "syntax": False,
        "schema": False
    }
    
    # 文件存在性验证
    if not results["exists"]:
        logger.error(f"XML文件不存在: {xml_path}")
        return results
    
    # XML格式语法验证
    try:
        tree = ET.parse(xml_path)
        results["syntax"] = True
    except Exception as e:
        logger.error(f"XML语法错误: {str(e)}")
        return results
    
    # 法律节点验证
    results["legal_nodes"] = validate_legal_nodes(xml_path)
    
    # 结构完整性验证
    results["structure"] = validate_xml_structure(xml_path)
    
    # XSD模式验证
    results["schema"] = validate_schema(xml_path)
    
    # 总体验证结果
    is_valid = all(results.values()) if strict else (results["exists"] and results["syntax"])
    
    if is_valid:
        logger.info("XML验证全部通过")
    else:
        logger.warning("XML验证未完全通过，请检查详细结果")
    
    return results


def fix_legal_nodes(xml_path: str, output_path: Optional[str] = None) -> str:
    """
    修复XML中缺失的法律声明节点
    
    Args:
        xml_path: 输入XML文件路径
        output_path: 输出XML文件路径，如果为None则覆盖原文件
        
    Returns:
        str: 修复后的XML文件路径
    """
    if output_path is None:
        output_path = xml_path
    
    logger.info(f"尝试修复XML文件中的法律声明: {xml_path}")
    
    try:
        from src.export.legal_injector import inject_disclaimer_to_xml
        
        # 默认的AI生成声明文本
        default_disclaimer = "本视频由AI生成，仅用于技术演示与学习。AI Generated Content by ClipsMaster."
        
        # 注入免责声明
        fixed_path = inject_disclaimer_to_xml(xml_path, default_disclaimer, output_path)
        
        logger.info(f"法律声明修复完成，保存到: {fixed_path}")
        return fixed_path
        
    except Exception as e:
        logger.error(f"修复法律声明失败: {str(e)}")
        return xml_path


def validate_xml(xml_path: str, auto_fix: bool = False) -> bool:
    """
    便捷的综合XML验证函数
    
    Args:
        xml_path: XML文件路径
        auto_fix: 是否自动修复问题
        
    Returns:
        bool: 验证是否通过
    """
    logger.info(f"验证XML文件: {xml_path}")
    
    results = validate_export_xml(xml_path)
    is_valid = all(results.values())
    
    if not is_valid and auto_fix:
        logger.info("尝试自动修复XML问题...")
        
        # 检查是否需要修复法律声明
        if not results["legal_nodes"]:
            xml_path = fix_legal_nodes(xml_path)
            
            # 重新验证
            logger.info("修复后重新验证...")
            results = validate_export_xml(xml_path)
            is_valid = all(results.values())
    
    return is_valid


def optimize_memory_validation(xml_path: str, strict: bool = False, 
                              max_file_size: int = 10 * 1024 * 1024) -> Dict[str, bool]:
    """
    内存优化的XML验证器，自动根据文件大小选择验证方式
    
    对于大文件，使用流式验证方式以减少内存使用；
    对于小文件，使用传统验证方式以获得最佳性能。
    
    Args:
        xml_path: XML文件路径
        strict: 是否使用严格验证
        max_file_size: 使用传统验证的最大文件大小(默认10MB)
        
    Returns:
        Dict[str, bool]: 验证结果
    """
    try:
        # 检查文件是否存在
        if not os.path.exists(xml_path):
            logger.error(f"文件不存在: {xml_path}")
            return {"exists": False}
        
        # 获取文件大小
        file_size = os.path.getsize(xml_path)
        
        # 如果文件大于阈值，使用流式验证
        if file_size > max_file_size:
            logger.info(f"文件较大 ({file_size/1024/1024:.2f} MB)，使用流式验证")
            from src.export.stream_xml_validator import stream_validate_xml
            return stream_validate_xml(xml_path, strict)
        else:
            # 对于小文件，使用传统验证
            logger.info(f"文件较小 ({file_size/1024/1024:.2f} MB)，使用传统验证")
            return validate_export_xml(xml_path, strict)
    
    except ImportError:
        # 如果流式验证模块不可用，回退到传统验证
        logger.warning("流式验证模块不可用，使用传统验证")
        return validate_export_xml(xml_path, strict)
    except Exception as e:
        logger.error(f"验证过程出错: {str(e)}")
        return {"exists": True, "syntax": False, "legal_nodes": False, "structure": False, "schema": False}


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="XML格式合规性验证工具")
    parser.add_argument("--xml", required=True, help="要验证的XML文件路径")
    parser.add_argument("--fix", action="store_true", help="自动修复问题")
    parser.add_argument("--strict", action="store_true", help="使用严格验证模式")
    parser.add_argument("--optimize", action="store_true", help="使用内存优化验证（推荐用于大文件）")
    parser.add_argument("--max-size", type=int, default=10, help="传统验证的最大文件大小(MB)")
    
    args = parser.parse_args()
    
    if args.optimize:
        results = optimize_memory_validation(
            args.xml, 
            args.strict, 
            args.max_size * 1024 * 1024
        )
    else:
        results = validate_export_xml(args.xml, args.strict)
    
    print("\n验证结果:")
    for key, value in results.items():
        print(f"  - {key}: {'通过' if value else '失败'}")
    
    if args.fix and not all(results.values()):
        print("\n尝试修复问题...")
        fixed = validate_xml(args.xml, auto_fix=True)
        print(f"修复后的验证结果: {'通过' if fixed else '失败'}")