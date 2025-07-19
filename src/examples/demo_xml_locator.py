#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
XML元数据节点定位器演示程序

展示如何使用XMLLocator进行元数据节点的查找、创建和修改操作
"""

import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
import json

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

try:
    from src.export.xml_locator import XMLLocator, find_meta_node, set_meta_attribute
    from src.export.xml_builder import create_project_xml, xml_to_string
    from src.utils.log_handler import get_logger
except ImportError as e:
    print(f"导入模块失败: {e}")
    sys.exit(1)

# 配置日志
logger = get_logger("demo_xml_locator")


def create_test_xml(format_type: str = "premiere") -> ET.Element:
    """
    创建测试用的XML文档
    
    Args:
        format_type: XML格式类型
        
    Returns:
        ET.Element: XML根元素
    """
    if format_type == "premiere":
        # 创建Premiere格式XML
        root = ET.fromstring("""<?xml version="1.0" encoding="UTF-8"?>
<project version="1.0">
  <resources>
    <video id="video1" path="test1.mp4" />
    <video id="video2" path="test2.mp4" />
  </resources>
  <timeline>
    <track type="video">
      <clip name="片段1" resourceId="video1" start="0" duration="5" />
      <clip name="片段2" resourceId="video2" start="5" duration="5" />
    </track>
  </timeline>
</project>""")
    elif format_type == "fcpxml":
        # 创建Final Cut Pro格式XML
        root = ET.fromstring("""<?xml version="1.0" encoding="UTF-8"?>
<fcpxml version="1.9">
  <resources>
    <asset id="asset1" src="test1.mp4" />
    <asset id="asset2" src="test2.mp4" />
  </resources>
  <project name="测试项目">
    <sequence>
      <spine>
        <clip name="片段1" ref="asset1" offset="0s" duration="5s" />
        <clip name="片段2" ref="asset2" offset="5s" duration="5s" />
      </spine>
    </sequence>
  </project>
</fcpxml>""")
    elif format_type == "davinci":
        # 创建DaVinci Resolve格式XML
        root = ET.fromstring("""<?xml version="1.0" encoding="UTF-8"?>
<Project>
  <Timeline>
    <Track>
      <ClipItem>
        <Name>片段1</Name>
        <Source>test1.mp4</Source>
        <Duration>5</Duration>
      </ClipItem>
      <ClipItem>
        <Name>片段2</Name>
        <Source>test2.mp4</Source>
        <Duration>5</Duration>
      </ClipItem>
    </Track>
  </Timeline>
</Project>""")
    else:
        # 默认简单XML
        root = ET.fromstring("""<?xml version="1.0" encoding="UTF-8"?>
<project>
  <resources>
    <video id="video1" path="test.mp4" />
  </resources>
  <timeline>
    <track type="video">
      <clip name="测试片段" resourceId="video1" start="0" duration="10" />
    </track>
  </timeline>
</project>""")

    return root


def demo_find_meta():
    """展示查找元数据节点的功能"""
    print("\n===== 查找元数据节点 =====")
    
    # 创建XMLLocator实例
    locator = XMLLocator()
    
    # 创建各种格式的XML
    formats = ["premiere", "fcpxml", "davinci", "default"]
    
    for format_type in formats:
        print(f"\n测试 {format_type} 格式:")
        
        # 创建测试XML
        root = create_test_xml(format_type)
        
        # 查找元数据节点
        meta_node = locator.find_meta_node(root)
        
        if meta_node is not None:
            print(f"找到元数据节点: <{meta_node.tag}>")
        else:
            print("未找到元数据节点")
            
            # 创建元数据节点
            meta_node = locator.create_meta_node(root, format_type)
            print(f"已创建元数据节点: <{meta_node.tag}>")


def demo_set_attributes():
    """展示设置元数据属性的功能"""
    print("\n===== 设置元数据属性 =====")
    
    # 创建XMLLocator实例
    locator = XMLLocator()
    
    # 创建测试XML
    root = create_test_xml()
    
    # 设置各种元数据属性
    attributes = {
        "copyright": "版权所有 © 2023 VisionAI-ClipsMaster",
        "generator": "VisionAI-ClipsMaster v1.0",
        "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "author": "AI助手",
        "description": "这是一个测试项目",
        "tags": "测试,示例,元数据"
    }
    
    print("设置以下属性:")
    for name, value in attributes.items():
        print(f"  {name}: {value}")
        locator.set_meta_attribute(root, name, value)
    
    # 检查是否设置成功
    meta_node = locator.find_meta_node(root)
    if meta_node is not None:
        print("\n元数据节点内容:")
        for child in meta_node:
            print(f"  <{child.tag}>{child.text}</{child.tag}>")


def demo_get_attributes():
    """展示获取元数据属性的功能"""
    print("\n===== 获取元数据属性 =====")
    
    # 创建XMLLocator实例
    locator = XMLLocator()
    
    # 创建测试XML
    root = create_test_xml()
    
    # 设置一些测试属性
    test_attrs = {
        "title": "测试项目",
        "version": "1.0.0",
        "publisher": "VisionAI-ClipsMaster",
        "color_space": "Rec.709",
        "audio_format": "Stereo",
        "fps": "30"
    }
    
    # 添加属性
    print("添加测试属性:")
    for name, value in test_attrs.items():
        locator.set_meta_attribute(root, name, value)
        print(f"  {name}: {value}")
    
    # 获取单个属性
    print("\n获取单个属性:")
    title = locator.get_meta_attribute(root, "title")
    version = locator.get_meta_attribute(root, "version")
    publisher = locator.get_meta_attribute(root, "publisher")
    
    print(f"  title: {title}")
    print(f"  version: {version}")
    print(f"  publisher: {publisher}")
    
    # 获取所有属性
    print("\n获取所有属性:")
    all_attrs = locator.get_all_meta_attributes(root)
    
    for name, value in all_attrs.items():
        print(f"  {name}: {value}")


def demo_update_attributes():
    """展示批量更新元数据属性的功能"""
    print("\n===== 批量更新元数据属性 =====")
    
    # 创建XMLLocator实例
    locator = XMLLocator()
    
    # 创建测试XML
    root = create_test_xml()
    
    # 设置初始属性
    init_attrs = {
        "title": "原始标题",
        "version": "0.1",
        "status": "草稿"
    }
    
    print("初始属性:")
    for name, value in init_attrs.items():
        locator.set_meta_attribute(root, name, value)
        print(f"  {name}: {value}")
    
    # 更新属性
    update_attrs = {
        "title": "更新后的标题",
        "version": "1.0",
        "status": "完成",
        "updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "new_attr": "新增的属性"
    }
    
    print("\n更新属性:")
    locator.update_meta_attributes(root, update_attrs)
    
    for name, value in update_attrs.items():
        print(f"  {name}: {value}")
    
    # 检查更新后的结果
    print("\n更新后的所有属性:")
    all_attrs = locator.get_all_meta_attributes(root)
    
    for name, value in all_attrs.items():
        print(f"  {name}: {value}")


def demo_remove_attribute():
    """展示移除元数据属性的功能"""
    print("\n===== 移除元数据属性 =====")
    
    # 创建XMLLocator实例
    locator = XMLLocator()
    
    # 创建测试XML
    root = create_test_xml()
    
    # 设置一些测试属性
    test_attrs = {
        "attr1": "值1",
        "attr2": "值2",
        "attr3": "值3",
        "temp": "临时值"
    }
    
    print("初始属性:")
    for name, value in test_attrs.items():
        locator.set_meta_attribute(root, name, value)
        print(f"  {name}: {value}")
    
    # 移除属性
    print("\n移除属性 'temp':")
    locator.remove_meta_attribute(root, "temp")
    
    # 检查移除后的结果
    print("\n移除后的所有属性:")
    all_attrs = locator.get_all_meta_attributes(root)
    
    for name, value in all_attrs.items():
        print(f"  {name}: {value}")
    
    # 尝试移除不存在的属性
    print("\n尝试移除不存在的属性 'nonexistent':")
    result = locator.remove_meta_attribute(root, "nonexistent")
    print(f"  操作结果: {'成功' if result else '失败'}")


def demo_update_xml_string():
    """展示更新XML字符串的功能"""
    print("\n===== 更新XML字符串 =====")
    
    # 创建XMLLocator实例
    locator = XMLLocator()
    
    # 测试XML字符串
    test_xml = """<?xml version="1.0" encoding="UTF-8"?>
<project>
  <resources>
    <video id="video1" path="test.mp4"/>
  </resources>
  <timeline>
    <track type="video">
      <clip name="测试片段" resourceId="video1" start="0" duration="10"/>
    </track>
  </timeline>
</project>"""
    
    print("原始XML字符串:")
    print(test_xml)
    
    # 要更新的属性
    update_attrs = {
        "copyright": "版权所有 © 2023",
        "generator": "VisionAI-ClipsMaster",
        "version": "1.0.0"
    }
    
    print("\n要更新的属性:")
    for name, value in update_attrs.items():
        print(f"  {name}: {value}")
    
    # 更新XML
    updated_xml = locator.update_xml_meta(test_xml, update_attrs)
    
    print("\n更新后的XML字符串:")
    print(updated_xml)


def demo_format_detection():
    """展示XML格式自动检测功能"""
    print("\n===== XML格式自动检测 =====")
    
    # 创建XMLLocator实例
    locator = XMLLocator()
    
    # 测试各种格式
    formats = ["premiere", "fcpxml", "davinci", "default"]
    
    for format_type in formats:
        root = create_test_xml(format_type)
        detected = locator.detect_xml_format(root)
        
        print(f"输入格式: {format_type}, 检测结果: {detected}")


def demo_integration():
    """展示与其他模块集成的功能"""
    print("\n===== 与其他模块集成 =====")
    
    # 创建项目XML
    project_root = create_project_xml("测试项目", 1920, 1080, 30.0)
    
    print("创建项目XML:")
    print(xml_to_string(project_root))
    
    # 使用静态方法接口操作元数据
    print("\n使用静态方法接口添加元数据:")
    meta_node = find_meta_node(project_root)
    
    if meta_node is None:
        print("未找到元数据节点，创建新节点...")
        meta_node = create_meta_node(project_root)
    
    # 设置元数据属性
    set_meta_attribute(project_root, "generator", "VisionAI-ClipsMaster")
    set_meta_attribute(project_root, "created", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    print("\n添加元数据后的项目XML:")
    print(xml_to_string(project_root))


def main():
    """主函数"""
    print("======= XML元数据节点定位器演示 =======")
    
    # 运行各个演示函数
    demo_find_meta()
    demo_set_attributes()
    demo_get_attributes()
    demo_update_attributes()
    demo_remove_attribute()
    demo_update_xml_string()
    demo_format_detection()
    demo_integration()
    
    print("\n演示完成!")


if __name__ == "__main__":
    main() 