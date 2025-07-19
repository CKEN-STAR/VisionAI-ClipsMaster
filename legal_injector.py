#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
法律声明注入模块

提供在XML导出文件中添加合法元数据和版权声明的功能，
确保生成的内容符合法律要求，保护知识产权。
"""

import re
import datetime

def inject_legal_meta(xml_str, app_version="1.0", copyright_holder="AI Generated Content", additional_meta=None):
    """在XML中注入法律元数据"""
    # 创建基础声明
    declaration = """
<meta>
    <generator>ClipsMaster v{}</generator>
    <copyright>{}</copyright>
    <creation_date>{}</creation_date>
    <legal_notice>此内容由AI辅助生成，使用者应遵守相关法律法规</legal_notice>
""".format(
        app_version,
        copyright_holder,
        datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    
    # 添加附加元数据
    if additional_meta:
        for key, value in additional_meta.items():
            declaration += f"    <{key}>{value}</{key}>\n"
    
    # 关闭meta标签
    declaration += "</meta>"
    
    # 查找并替换
    if "<project" in xml_str and not "<meta>" in xml_str:
        # 使用正则表达式在<project>标签后插入声明
        pattern = r"(<project[^>]*>)"
        replacement = r"\\\\\\1\\n" + declaration
        return re.sub(pattern, replacement, xml_str)
    
    return xml_str

def inject_legal_comment(xml_str, comment=None):
    """在XML中注入法律相关注释"""
    if comment is None:
        comment = """
<!-- 
    本文件由VisionAI-ClipsMaster生成
    版权声明: 此文件中的内容受版权法保护
    使用限制: 未经许可，不得用于商业用途
-->
"""
    
    # 在XML声明后添加注释
    if xml_str.startswith("<?xml"):
        xml_declaration_end = xml_str.find("?>") + 2
        return xml_str[:xml_declaration_end] + comment + xml_str[xml_declaration_end:]
    else:
        return comment + xml_str

def apply_legal_requirements(xml_str, app_version="1.0", copyright_holder="AI Generated Content", include_comment=True, additional_meta=None):
    """应用所有法律要求"""
    # 添加元数据
    result = inject_legal_meta(xml_str, app_version, copyright_holder, additional_meta)
    
    # 添加注释
    if include_comment:
        result = inject_legal_comment(result)
    
    return result

if __name__ == "__main__":
    # 测试代码
    test_xml = """<?xml version="1.0" encoding="UTF-8"?>
<project version="3.0">
  <resources>
    <!-- 素材资源区 -->
  </resources>
  <timeline>
    <!-- 时间轴轨道区 -->
  </timeline>
</project>"""
    
    print("=== 法律声明注入功能测试 ===")
    print("\n原始XML:")
    print("-" * 50)
    print(test_xml)
    print("-" * 50)
    
    # 测试元数据注入
    meta_result = inject_legal_meta(test_xml)
    print("\n注入元数据后:")
    print("-" * 50)
    print(meta_result)
    print("-" * 50)
    
    # 测试注释注入
    comment_result = inject_legal_comment(test_xml)
    print("\n注入注释后:")
    print("-" * 50)
    print(comment_result)
    print("-" * 50)
    
    # 测试完整应用
    full_result = apply_legal_requirements(test_xml)
    print("\n完整应用法律要求后:")
    print("-" * 50)
    print(full_result)
    print("-" * 50)
    
    # 验证结果
    success = '<meta>' in full_result and '<generator>' in full_result and '<!--' in full_result
    print(f"\n测试结果: {'✓ 通过' if success else '❌ 失败'}") 