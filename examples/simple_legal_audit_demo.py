#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简化版法律操作审计日志演示
"""

import os
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

# 添加项目根目录到路径
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

# 导入简化版审计日志功能
from src.exporters.simple_legal_logger import (
    log_legal_operation,
    log_operation,
    with_legal_audit,
    log_legal_injection,
    log_disclaimer_addition
)

def create_sample_xml(output_path):
    """创建示例XML文件"""
    root = ET.Element("project")
    
    meta = ET.SubElement(root, "meta")
    ET.SubElement(meta, "generator").text = "ClipsMaster Test"
    ET.SubElement(meta, "version").text = "1.0"
    
    content = ET.SubElement(root, "content")
    ET.SubElement(content, "title").text = "测试项目"
    
    tree = ET.ElementTree(root)
    tree.write(output_path, encoding="utf-8", xml_declaration=True)
    print(f"已创建XML文件: {output_path}")
    return output_path

@with_legal_audit("test_operation")
def process_xml_file(file_path, text_to_add):
    """处理XML文件（测试用）"""
    tree = ET.parse(file_path)
    root = tree.getroot()
    
    disclaimer = ET.SubElement(root.find("meta"), "disclaimer")
    disclaimer.text = text_to_add
    
    tree.write(file_path, encoding="utf-8", xml_declaration=True)
    return True

def main():
    """主函数"""
    print("====== 简化版法律操作审计日志演示 ======")
    
    # 创建临时文件
    with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as tmp:
        xml_path = tmp.name
    
    try:
        # 创建示例XML
        create_sample_xml(xml_path)
        
        # 1. 使用简单日志函数
        print("\n1. 使用简单日志函数")
        log_legal_operation("zh", "这是一个测试的法律声明文本")
        print("已记录简单法律操作")
        
        # 2. 使用操作日志函数
        print("\n2. 使用操作日志函数")
        log_operation(
            operation_type="test_log",
            details={
                "file_path": xml_path,
                "description": "测试操作日志功能"
            }
        )
        print("已记录详细操作日志")
        
        # 3. 使用便捷函数
        print("\n3. 使用便捷函数")
        log_legal_injection(
            file_path=xml_path,
            content_type="xml",
            legal_text="本内容受版权保护，未经许可不得复制或传播。"
        )
        print("已记录法律注入操作")
        
        # 4. 使用装饰器
        print("\n4. 使用装饰器")
        process_xml_file(
            xml_path,
            "本内容由AI生成，仅用于技术演示，不代表任何观点。"
        )
        print("已使用装饰器记录XML处理操作")
        
        # 查看修改后的XML
        with open(xml_path, "r", encoding="utf-8") as f:
            content = f.read()
            print(f"\n修改后的XML内容:\n{content[:200]}...")
        
        print("\n日志已写入到 logs/legal_operations.log 文件")
        
    finally:
        # 清理临时文件
        if os.path.exists(xml_path):
            os.unlink(xml_path)
    
    print("\n====== 演示结束 ======")

if __name__ == "__main__":
    main() 