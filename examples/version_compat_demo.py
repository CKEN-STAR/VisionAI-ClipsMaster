#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
版本兼容性适配演示

该脚本演示了如何使用版本兼容性模块对XML项目文件进行版本兼容性处理，
包括向后兼容性修复和版本升级功能。
"""

import os
import sys
import xml.etree.ElementTree as ET
from xml.dom import minidom
import tempfile
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
sys.path.append(str(project_root))

# 导入项目模块
from src.exporters.version_compat import (
    get_xml_version,
    is_version_compatible,
    backward_compatibility_fix,
    upgrade_version,
    process_xml_file,
    batch_process_directory,
    compare_versions,
    find_conversion_path,
    VERSIONS
)
from src.utils.log_handler import get_logger

# 配置日志
logger = get_logger("version_compat_demo")

def create_demo_xml(version="3.0"):
    """
    创建演示用的XML文件内容
    
    Args:
        version: XML版本
        
    Returns:
        str: XML内容
    """
    # 基础项目结构
    timeline_elem = '<timeline>'
    
    # 根据版本添加不同的内容
    if compare_versions(version, "2.5") >= 0:
        timeline_elem = '<timeline advanced="true">'
    
    # 基本的设置节点
    settings_elem = ''
    if compare_versions(version, "3.0") >= 0:
        settings_elem = '''  <settings>
    <resolution type="4k" width="3840" height="2160" />
  </settings>
'''
    
    # 元数据节点
    meta_elem = ''
    if compare_versions(version, "2.0") >= 0:
        meta_elem = f'''  <meta>
    <created>{datetime.now().isoformat()}</created>
    <author>VisionAI-ClipsMaster</author>
  </meta>
'''
    
    # 构建完整XML
    xml_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<project version="{version}">
{meta_elem}{settings_elem}  {timeline_elem}
    <clip id="clip1" start="0" duration="10" />
    <clip id="clip2" start="10" duration="5" />
  </timeline>
</project>
'''
    
    return xml_content

def pretty_print_xml(xml_content):
    """美化XML输出"""
    try:
        root = ET.fromstring(xml_content)
        pretty_xml = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
        return pretty_xml
    except ET.ParseError:
        return xml_content

def run_demo():
    """运行版本兼容性演示"""
    print("\n=== 版本兼容性适配演示 ===\n")
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    
    try:
        # 创建各个版本的XML文件
        version_files = {}
        for version in VERSIONS.keys():
            xml_content = create_demo_xml(version)
            file_path = os.path.join(temp_dir, f"project_v{version.replace('.', '_')}.xml")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(xml_content)
            version_files[version] = file_path
            print(f"已创建 {version} 版本项目文件: {os.path.basename(file_path)}")
        
        print("\n1. 向后兼容性演示: 3.0 -> 2.0")
        print("-" * 40)
        
        # 读取3.0版本文件
        v3_path = version_files.get("3.0")
        with open(v3_path, "r", encoding="utf-8") as f:
            v3_content = f.read()
        
        print("\n原始3.0版本内容:")
        print("-" * 20)
        print(v3_content)
        
        # 转换为2.0版本
        output_path = os.path.join(temp_dir, "converted_to_v2.xml")
        success = process_xml_file(v3_path, output_path, "2.0")
        
        if success:
            # 读取转换后的内容
            with open(output_path, "r", encoding="utf-8") as f:
                converted_content = f.read()
            
            print("\n转换为2.0版本后的内容:")
            print("-" * 20)
            print(converted_content)
            
            # 解析并验证版本
            tree = ET.parse(output_path)
            root = tree.getroot()
            print(f"\n转换后版本: {root.get('version')}")
            
            # 验证4K元素是否已移除
            settings = root.find("./settings/resolution[@type='4k']")
            print(f"4K分辨率元素是否存在: {'是' if settings is not None else '否 (已正确移除)'}")
            
            # 验证高级时间线属性是否已移除
            timeline = root.find("./timeline")
            advanced_attr = timeline.get("advanced")
            print(f"高级时间线属性是否存在: {'是' if advanced_attr else '否 (已正确移除)'}")
        else:
            print("转换失败")
        
        print("\n2. 版本升级演示: 1.0 -> 3.0")
        print("-" * 40)
        
        # 读取1.0版本文件
        v1_path = version_files.get("1.0")
        with open(v1_path, "r", encoding="utf-8") as f:
            v1_content = f.read()
        
        print("\n原始1.0版本内容:")
        print("-" * 20)
        print(v1_content)
        
        # 升级为3.0版本
        output_path = os.path.join(temp_dir, "upgraded_to_v3.xml")
        success = process_xml_file(v1_path, output_path, "3.0")
        
        if success:
            # 读取升级后的内容
            with open(output_path, "r", encoding="utf-8") as f:
                upgraded_content = f.read()
            
            print("\n升级为3.0版本后的内容:")
            print("-" * 20)
            print(upgraded_content)
            
            # 解析并验证版本
            tree = ET.parse(output_path)
            root = tree.getroot()
            print(f"\n升级后版本: {root.get('version')}")
            
            # 验证元数据是否已添加
            meta = root.find("./meta")
            print(f"元数据是否已添加: {'是' if meta is not None else '否 (升级失败)'}")
            
            # 验证4K支持是否已添加
            settings = root.find("./settings/resolution[@type='4k']")
            print(f"4K分辨率元素是否添加: {'是' if settings is not None else '否 (升级失败)'}")
        else:
            print("升级失败")
        
        print("\n3. 批量处理演示")
        print("-" * 40)
        
        # 创建输出目录
        output_dir = os.path.join(temp_dir, "batch_output")
        os.makedirs(output_dir, exist_ok=True)
        
        # 批量转换所有文件为2.5版本
        print("\n批量转换所有文件为2.5版本...")
        results = batch_process_directory(temp_dir, "2.5", output_dir)
        
        print(f"处理完成，共处理 {len(results)} 个文件")
        for file_name, success in results.items():
            print(f"- {file_name}: {'成功' if success else '失败'}")
        
        # 检查输出文件
        output_files = list(Path(output_dir).glob("*.xml"))
        if output_files:
            print(f"\n已生成 {len(output_files)} 个输出文件:")
            for file_path in output_files:
                print(f"- {file_path.name}")
                
                # 验证版本
                try:
                    tree = ET.parse(file_path)
                    root = tree.getroot()
                    version = root.get("version")
                    if version == "2.5":
                        print(f"  ✓ 版本正确: {version}")
                    else:
                        print(f"  ✗ 版本错误: {version}, 应为 2.5")
                except ET.ParseError:
                    print("  ✗ 无法解析XML文件")
        
    finally:
        # 清理临时文件
        import shutil
        shutil.rmtree(temp_dir)
    
    print("\n=== 演示完成 ===")

if __name__ == "__main__":
    run_demo() 