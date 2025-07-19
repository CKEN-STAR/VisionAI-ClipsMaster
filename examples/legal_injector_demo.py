#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
声明内容安全注入演示

演示如何在XML文件中安全地注入包含特殊字符的声明内容
"""

import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.export.legal_injector import inject_with_escape
from src.export.xml_locator import find_meta_node_or_create


def main():
    """主函数"""
    print("=== 声明内容安全注入演示 ===\n")
    
    # 创建示例XML
    xml_string = '''<?xml version="1.0" encoding="UTF-8"?>
<project>
  <resources>
    <video id="clip1" path="video/test.mp4" />
  </resources>
  <timeline>
    <track>
      <clip ref="clip1" start="0" duration="10" />
    </track>
  </timeline>
</project>'''
    
    print("原始XML:")
    print("-" * 50)
    print(xml_string)
    print("-" * 50)
    
    # 解析XML
    root = ET.fromstring(xml_string)
    
    # 包含特殊字符的免责声明文本
    disclaimer_text = '''
本内容由ClipsMaster AI生成，仅用于技术演示目的。
使用条款 & 限制:
1. 不得用于<商业用途>
2. 内容可能包含AI生成的不准确信息
3. 请遵守当地法律法规

版权所有 © 2023-2024 VisionAI
'''
    
    print("\n包含特殊字符的免责声明文本:")
    print("-" * 50)
    print(disclaimer_text)
    print("-" * 50)
    
    # 获取或创建元数据节点
    meta_node = find_meta_node_or_create(root)
    
    # 注入转义后的免责声明
    inject_with_escape(disclaimer_text, meta_node)
    
    # 将更新后的XML转换回字符串
    updated_xml = ET.tostring(root, encoding='utf-8').decode('utf-8')
    
    print("\n注入免责声明后的XML:")
    print("-" * 50)
    print(updated_xml)
    print("-" * 50)
    
    # 验证结果
    # 再次解析XML以确认结构完整
    try:
        ET.fromstring(updated_xml)
        print("\n✓ XML结构验证通过 - 特殊字符已安全转义")
    except ET.ParseError as e:
        print(f"\n❌ XML结构验证失败: {e}")


if __name__ == "__main__":
    main() 