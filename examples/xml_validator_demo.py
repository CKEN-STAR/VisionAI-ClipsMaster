#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
XML格式合规性验证演示

展示如何使用XML验证器验证导出文件的合规性，包括检查法律声明节点
"""

import os
import sys
import argparse
import tempfile
from pathlib import Path
import xml.etree.ElementTree as ET

# 添加项目根目录到路径
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

from src.export.xml_validator import (
    validate_legal_nodes,
    validate_xml_structure,
    validate_export_xml,
    fix_legal_nodes
)
from src.export.legal_injector import inject_disclaimer_to_xml


def create_sample_xml(output_path: str, include_disclaimer: bool = True) -> str:
    """
    创建示例XML文件
    
    Args:
        output_path: 输出文件路径
        include_disclaimer: 是否包含法律声明
        
    Returns:
        str: 创建的文件路径
    """
    # 创建基本XML结构
    root = ET.Element("project")
    
    # 添加资源节点
    resources = ET.SubElement(root, "resources")
    video = ET.SubElement(resources, "video", {
        "id": "video1",
        "path": "sample.mp4",
        "name": "示例视频"
    })
    
    # 添加元数据节点
    meta = ET.SubElement(root, "meta")
    ET.SubElement(meta, "generator").text = "ClipsMaster Demo"
    ET.SubElement(meta, "copyright").text = "ClipsMaster 2023"
    
    # 根据参数决定是否添加免责声明
    if include_disclaimer:
        ET.SubElement(meta, "disclaimer").text = "本视频由AI生成，仅用于技术演示。AI Generated Content by ClipsMaster."
    
    # 添加时间轴节点
    timeline = ET.SubElement(root, "timeline")
    track = ET.SubElement(timeline, "track", {"type": "video"})
    clip = ET.SubElement(track, "clip", {
        "resourceId": "video1",
        "start": "0",
        "duration": "10"
    })
    
    # 创建XML树并保存
    tree = ET.ElementTree(root)
    tree.write(output_path, encoding="utf-8", xml_declaration=True)
    
    return output_path


def demo_validation():
    """演示验证功能"""
    print("=" * 50)
    print("XML格式合规性验证演示")
    print("=" * 50)
    
    # 创建临时目录
    with tempfile.TemporaryDirectory() as temp_dir:
        # 创建有效的XML文件
        valid_xml_path = os.path.join(temp_dir, "valid_sample.xml")
        create_sample_xml(valid_xml_path, include_disclaimer=True)
        print(f"\n1. 已创建含法律声明的XML示例文件: {valid_xml_path}")
        
        # 验证有效XML
        print("\n验证含法律声明的XML:")
        results = validate_export_xml(valid_xml_path)
        for key, value in results.items():
            print(f"  - {key}: {'通过' if value else '失败'}")
        
        # 创建无效的XML文件（缺少法律声明）
        invalid_xml_path = os.path.join(temp_dir, "invalid_sample.xml")
        create_sample_xml(invalid_xml_path, include_disclaimer=False)
        print(f"\n2. 已创建缺少法律声明的XML示例文件: {invalid_xml_path}")
        
        # 验证无效XML
        print("\n验证缺少法律声明的XML:")
        results = validate_export_xml(invalid_xml_path)
        for key, value in results.items():
            print(f"  - {key}: {'通过' if value else '失败'}")
        
        # 修复无效XML
        fixed_xml_path = os.path.join(temp_dir, "fixed_sample.xml")
        print(f"\n3. 修复缺少法律声明的XML文件:")
        fix_legal_nodes(invalid_xml_path, fixed_xml_path)
        print(f"  - 修复结果保存到: {fixed_xml_path}")
        
        # 验证修复后的XML
        print("\n验证修复后的XML:")
        results = validate_export_xml(fixed_xml_path)
        for key, value in results.items():
            print(f"  - {key}: {'通过' if value else '失败'}")
        
        print("\n演示完成!")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="XML格式合规性验证演示")
    parser.add_argument("--xml", help="要验证的XML文件路径")
    parser.add_argument("--fix", action="store_true", help="修复XML中的法律声明问题")
    parser.add_argument("--output", help="修复后输出的文件路径")
    
    args = parser.parse_args()
    
    if args.xml:
        # 验证指定的XML文件
        print(f"验证XML文件: {args.xml}")
        results = validate_export_xml(args.xml)
        
        for key, value in results.items():
            print(f"  - {key}: {'通过' if value else '失败'}")
        
        if args.fix and not results["legal_nodes"]:
            output_path = args.output or args.xml
            print(f"\n修复法律声明节点...")
            fixed_path = fix_legal_nodes(args.xml, output_path)
            print(f"修复完成，结果保存到: {fixed_path}")
            
            # 重新验证
            print("\n重新验证修复后的文件:")
            results = validate_export_xml(fixed_path)
            for key, value in results.items():
                print(f"  - {key}: {'通过' if value else '失败'}")
    else:
        # 运行演示
        demo_validation()


if __name__ == "__main__":
    main() 