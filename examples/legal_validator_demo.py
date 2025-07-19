#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
法律声明存在性验证演示

该脚本演示了如何使用法律声明验证器检查和确保输出文件
包含必要的法律声明和免责信息。
"""

import os
import sys
import logging
import xml.etree.ElementTree as ET
from xml.dom import minidom
import tempfile
from pathlib import Path

# 添加项目根目录到路径
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
sys.path.append(str(project_root))

# 导入项目模块
from src.exporters.legal_validator import (
    check_legal_metadata,
    validate_xml_legal_compliance,
    inject_missing_legal_elements,
    validate_srt_legal_notice,
    LegalComplianceError
)
from src.utils.log_handler import get_logger

# 配置日志
logger = get_logger("legal_validator_demo")

def create_demo_xml(output_path, include_legal=False):
    """创建演示用的XML文件
    
    Args:
        output_path: 输出路径
        include_legal: 是否包含法律声明
    """
    # 创建基本的项目结构
    root = ET.Element("project")
    root.set("version", "1.0")
    
    # 添加元数据
    meta = ET.SubElement(root, "meta")
    title = ET.SubElement(meta, "title")
    title.text = "演示项目"
    
    author = ET.SubElement(meta, "author")
    author.text = "VisionAI-ClipsMaster"
    
    # 如果需要，添加法律声明
    if include_legal:
        disclaimer = ET.SubElement(meta, "disclaimer")
        disclaimer.text = "This content is AI Generated and for demonstration purposes only."
        
        copyright_elem = ET.SubElement(meta, "copyright")
        copyright_elem.text = "Copyright 2023. All rights reserved."
        
        meta.set("legal_compliance", "true")
        
        ai_generated = ET.SubElement(meta, "ai_generated")
        ai_generated.text = "true"
    
    # 添加一些项目内容
    content = ET.SubElement(root, "content")
    
    clip = ET.SubElement(content, "clip")
    clip.set("id", "clip1")
    clip.set("start", "0")
    clip.set("duration", "10.5")
    
    clip = ET.SubElement(content, "clip")
    clip.set("id", "clip2")
    clip.set("start", "10.5")
    clip.set("duration", "5.2")
    
    # 保存为漂亮的XML
    xml_str = ET.tostring(root, encoding='utf-8')
    pretty_xml = minidom.parseString(xml_str).toprettyxml(indent="  ")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(pretty_xml)
    
    logger.info(f"创建演示XML文件: {output_path}")
    return output_path

def run_demo():
    """运行法律声明验证演示"""
    print("\n=== 法律声明存在性验证演示 ===\n")
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    
    try:
        # 创建不包含法律声明的XML
        no_legal_xml = os.path.join(temp_dir, "no_legal.xml")
        create_demo_xml(no_legal_xml, include_legal=False)
        
        # 创建包含法律声明的XML
        legal_xml = os.path.join(temp_dir, "with_legal.xml")
        create_demo_xml(legal_xml, include_legal=True)
        
        print("\n1. 验证不合规的XML文件")
        print("-" * 40)
        
        try:
            check_legal_metadata(ET.parse(no_legal_xml).getroot())
            print("✓ 验证通过（意外结果）")
        except LegalComplianceError as e:
            print(f"✗ 验证失败（预期结果）: {e}")
        
        result = validate_xml_legal_compliance(no_legal_xml)
        print(f"详细验证结果: 有效={result['valid']}")
        if 'missing_elements' in result:
            print(f"缺少元素: {', '.join(result['missing_elements'])}")
        
        print("\n2. 验证合规的XML文件")
        print("-" * 40)
        
        try:
            check_legal_metadata(ET.parse(legal_xml).getroot())
            print("✓ 验证通过（预期结果）")
        except LegalComplianceError as e:
            print(f"✗ 验证失败（意外结果）: {e}")
        
        result = validate_xml_legal_compliance(legal_xml)
        print(f"详细验证结果: 有效={result['valid']}")
        
        print("\n3. 自动修复不合规的XML")
        print("-" * 40)
        
        fixed_xml = os.path.join(temp_dir, "fixed.xml")
        shutil.copy(no_legal_xml, fixed_xml)
        
        print(f"修复前验证结果: {validate_xml_legal_compliance(fixed_xml)['valid']}")
        success = inject_missing_legal_elements(fixed_xml)
        print(f"修复结果: {'成功' if success else '失败'}")
        print(f"修复后验证结果: {validate_xml_legal_compliance(fixed_xml)['valid']}")
        
        # 创建测试SRT文件
        srt_path = os.path.join(temp_dir, "test.srt")
        with open(srt_path, "w", encoding="utf-8") as f:
            f.write("1\n00:00:01,000 --> 00:00:05,000\n这是一个测试字幕\n\n")
        
        # 创建带免责声明的SRT文件
        srt_with_disclaimer_path = os.path.join(temp_dir, "with_disclaimer.srt")
        with open(srt_with_disclaimer_path, "w", encoding="utf-8") as f:
            f.write("1\n00:00:01,000 --> 00:00:05,000\n这是一个测试字幕\n\n")
            f.write("2\n00:00:06,000 --> 00:00:10,000\n免责声明：本视频仅供参考，版权归原作者所有\n\n")
        
        print("\n4. 验证SRT文件中的法律声明")
        print("-" * 40)
        
        result = validate_srt_legal_notice(srt_path)
        print(f"无声明SRT验证结果: 有效={result['valid']}, 包含声明={result['has_disclaimer']}")
        
        result = validate_srt_legal_notice(srt_with_disclaimer_path)
        print(f"有声明SRT验证结果: 有效={result['valid']}, 包含声明={result['has_disclaimer']}")
        
    finally:
        # 清理临时文件
        for file_name in os.listdir(temp_dir):
            file_path = os.path.join(temp_dir, file_name)
            if os.path.isfile(file_path):
                os.remove(file_path)
        
        # 删除临时目录
        os.rmdir(temp_dir)
    
    print("\n=== 演示完成 ===")

if __name__ == "__main__":
    import shutil  # 添加必要的导入
    run_demo() 