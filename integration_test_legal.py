#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
法律声明整合测试

测试法律声明注入功能与其他XML处理功能的整合使用
"""

from xml_builder import create_base_xml
from placeholder import insert_required_placeholders
from legal_injector import apply_legal_requirements

def test_integration():
    """测试整合流程"""
    print("=== 测试法律声明注入整合 ===")
    
    # 1. 创建基础XML
    base_xml = create_base_xml()
    print("1. 创建基础XML")
    
    # 2. 添加轨道占位符
    with_placeholders = insert_required_placeholders(base_xml)
    print("2. 添加轨道占位符")
    
    # 3. 应用法律声明
    final_xml = apply_legal_requirements(with_placeholders, 
                                        app_version="1.0.5",
                                        copyright_holder="VisionAI工作室")
    print("3. 应用法律声明")
    
    # 4. 检查结果
    success = (
        '<track type="video"' in final_xml and 
        '<track type="audio"' in final_xml and
        '<meta>' in final_xml and
        '<copyright>' in final_xml
    )
    
    print(f"\n结果验证: {'✓ 通过' if success else '❌ 失败'}")
    
    print("\n最终XML片段:")
    print("-" * 50)
    print(final_xml[:500] + "...\n...")  # 只显示部分内容
    print("-" * 50)
    
    return success

if __name__ == "__main__":
    test_integration() 