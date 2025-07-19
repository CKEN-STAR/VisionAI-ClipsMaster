#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
法律声明存在性验证模块

该模块用于检查导出的XML文件是否包含必要的法律声明和免责信息，
确保所有生成的视频项目文件都符合法律合规要求。
"""

import os
import re
import logging
from typing import Dict, Optional, List, Union, Any
import xml.etree.ElementTree as ET
from pathlib import Path

# 导入项目模块
from src.utils.log_handler import get_logger
from src.utils.legal_text_loader import load_legal_text, LegalTextLoader

# 获取日志记录器
logger = get_logger("legal_validator")

class LegalComplianceError(Exception):
    """法律合规性检查异常"""
    pass

def check_legal_metadata(xml_root: ET.Element) -> bool:
    """强制检查法律声明节点
    
    Args:
        xml_root: XML根元素
        
    Returns:
        bool: 检查是否通过
        
    Raises:
        LegalComplianceError: 当未找到必要的法律声明时抛出
    """
    disclaimer = xml_root.findtext("./meta/disclaimer")
    if not disclaimer or "AI Generated" not in disclaimer:
        raise LegalComplianceError("法律声明不符合要求")
    
    return True

def validate_xml_legal_compliance(xml_path: str, language: str = "zh") -> Dict[str, Any]:
    """验证XML文件的法律合规性
    
    检查XML文件是否包含必要的法律声明、免责信息和版权信息
    
    Args:
        xml_path: XML文件路径
        language: 语言代码 (zh/en)
        
    Returns:
        Dict: 包含验证结果的字典
    """
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        # 检查结果
        results = {
            "file": os.path.basename(xml_path),
            "valid": True,
            "missing_elements": [],
            "warnings": [],
        }
        
        # 检查元数据部分
        meta = root.find("./meta")
        if meta is None:
            results["valid"] = False
            results["missing_elements"].append("meta")
            return results
        
        # 检查免责声明
        disclaimer = meta.findtext("disclaimer")
        if not disclaimer:
            results["valid"] = False
            results["missing_elements"].append("disclaimer")
        elif len(disclaimer) < 10:  # 简单检查声明长度是否合理
            results["warnings"].append("免责声明过短，可能不符合要求")
        
        # 检查版权信息
        copyright_info = meta.findtext("copyright")
        if not copyright_info:
            results["valid"] = False
            results["missing_elements"].append("copyright")
        
        # 检查法律属性
        legal_attr = meta.get("legal_compliance")
        if not legal_attr or legal_attr.lower() != "true":
            results["valid"] = False
            results["missing_elements"].append("legal_compliance attribute")
        
        # 检查生成标记
        ai_generated = meta.findtext("ai_generated")
        if not ai_generated or ai_generated.lower() != "true":
            results["warnings"].append("未标记AI生成属性")
        
        return results
        
    except ET.ParseError as e:
        logger.error(f"XML解析错误: {str(e)}")
        return {
            "file": os.path.basename(xml_path),
            "valid": False,
            "error": f"XML解析错误: {str(e)}",
        }
    except Exception as e:
        logger.error(f"验证过程发生错误: {str(e)}")
        return {
            "file": os.path.basename(xml_path),
            "valid": False,
            "error": str(e),
        }

def validate_batch_files(directory: str, pattern: str = "*.xml") -> List[Dict[str, Any]]:
    """批量验证目录中的文件
    
    Args:
        directory: 目录路径
        pattern: 文件模式
        
    Returns:
        List: 验证结果列表
    """
    results = []
    file_paths = list(Path(directory).glob(pattern))
    
    for file_path in file_paths:
        result = validate_xml_legal_compliance(str(file_path))
        results.append(result)
    
    return results

def inject_missing_legal_elements(xml_path: str, language: str = "zh") -> bool:
    """注入缺失的法律元素到XML文件
    
    Args:
        xml_path: XML文件路径
        language: 语言代码
        
    Returns:
        bool: 是否成功注入
    """
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        # 确保meta节点存在
        meta = root.find("./meta")
        if meta is None:
            meta = ET.SubElement(root, "meta")
        
        # 加载法律文本
        disclaimer_text = load_legal_text("disclaimer", language)
        copyright_text = load_legal_text("copyright", language)
        
        # 检查并添加免责声明
        disclaimer = meta.find("disclaimer")
        if disclaimer is None:
            disclaimer = ET.SubElement(meta, "disclaimer")
            disclaimer.text = disclaimer_text
        elif not disclaimer.text:
            disclaimer.text = disclaimer_text
        
        # 检查并添加版权信息
        copyright_elem = meta.find("copyright")
        if copyright_elem is None:
            copyright_elem = ET.SubElement(meta, "copyright")
            copyright_elem.text = copyright_text
        elif not copyright_elem.text:
            copyright_elem.text = copyright_text
        
        # 设置法律合规属性
        meta.set("legal_compliance", "true")
        
        # 添加AI生成标记
        ai_generated = meta.find("ai_generated")
        if ai_generated is None:
            ai_generated = ET.SubElement(meta, "ai_generated")
            ai_generated.text = "true"
        else:
            ai_generated.text = "true"
        
        # 保存修改后的文件
        tree.write(xml_path, encoding="utf-8", xml_declaration=True)
        return True
        
    except Exception as e:
        logger.error(f"注入法律元素失败: {str(e)}")
        return False

def validate_srt_legal_notice(srt_path: str) -> Dict[str, Any]:
    """验证SRT文件中的法律声明
    
    Args:
        srt_path: SRT文件路径
        
    Returns:
        Dict: 验证结果
    """
    result = {
        "file": os.path.basename(srt_path),
        "valid": False,
        "has_disclaimer": False,
    }
    
    try:
        with open(srt_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否包含免责声明文本
        disclaimer_patterns = [
            r"免责声明",
            r"仅供.*?参考",
            r"不代表.*?观点",
            r"版权.*?原作者",
            r"Disclaimer",
            r"for reference only",
        ]
        
        for pattern in disclaimer_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                result["has_disclaimer"] = True
                break
        
        result["valid"] = result["has_disclaimer"]
        return result
        
    except Exception as e:
        logger.error(f"验证SRT文件失败: {str(e)}")
        return {
            "file": os.path.basename(srt_path),
            "valid": False,
            "error": str(e),
        }

if __name__ == "__main__":
    # 简单测试
    from xml.dom import minidom
    
    # 创建测试XML
    root = ET.Element("project")
    meta = ET.SubElement(root, "meta")
    
    # 测试合规性检查
    try:
        check_legal_metadata(root)
    except LegalComplianceError as e:
        print(f"预期的错误: {str(e)}")
    
    # 添加必要元素
    disclaimer = ET.SubElement(meta, "disclaimer")
    disclaimer.text = "This content is AI Generated and for demonstration purposes only."
    
    # 再次检查
    try:
        if check_legal_metadata(root):
            print("法律声明验证通过")
    except LegalComplianceError as e:
        print(f"错误: {str(e)}")
    
    # 美化输出XML
    xml_str = ET.tostring(root, encoding='utf-8')
    pretty_xml = minidom.parseString(xml_str).toprettyxml()
    print(pretty_xml) 