#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 用户自定义法律文本替换演示

此演示脚本展示如何使用用户自定义法律文本替换功能：
1. 简单的变量替换
2. 使用预先定义的替换模板
3. 创建和保存自定义模板
4. 对不同类型内容进行处理（XML、JSON、SRT）
5. 与Legal Injector集成
"""

import os
import sys
import json
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

# 添加项目根目录到路径
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

# 导入自定义法律文本处理模块
from src.exporters.custom_legal import (
    apply_custom_rules,
    load_user_config,
    save_user_config,
    create_user_template,
    apply_custom_legal,
    apply_direct,
    get_user_variables,
    apply_to_legal_injector
)

# 导入法律注入器
from src.export.legal_injector import LegalInjector


def create_sample_files():
    """创建演示用的样例文件"""
    # 创建临时目录
    temp_dir = Path(tempfile.mkdtemp())
    
    # 创建XML示例文件
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<project>
  <meta>
    <generator>ClipsMaster v1.0</generator>
    <copyright>AI Generated Content by ClipsMaster v1.0</copyright>
    <disclaimer>本视频仅用于技术演示，不代表任何观点。内容由AI生成，可能存在不准确之处。</disclaimer>
  </meta>
  <content>
    <title>示例项目</title>
  </content>
</project>"""
    
    xml_file = temp_dir / "sample.xml"
    with open(xml_file, "w", encoding="utf-8") as f:
        f.write(xml_content)
    
    # 创建JSON示例文件
    json_content = {
        "meta": {
            "generator": "ClipsMaster v1.0",
            "copyright": "AI Generated Content by ClipsMaster v1.0",
            "disclaimer": "本视频仅用于技术演示，不代表任何观点。"
        },
        "content": {
            "title": "示例项目",
            "items": [
                {"name": "片段1", "duration": 10.5},
                {"name": "片段2", "duration": 5.2}
            ]
        }
    }
    
    json_file = temp_dir / "sample.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(json_content, f, ensure_ascii=False, indent=2)
    
    # 创建SRT示例文件
    srt_content = """1
00:00:00,000 --> 00:00:05,000
本视频由ClipsMaster AI自动生成
仅用于技术演示

2
00:00:05,500 --> 00:00:10,000
这是演示内容

3
00:00:10,500 --> 00:00:15,000
版权声明：本视频版权归ClipsMaster所有
"""
    
    srt_file = temp_dir / "sample.srt"
    with open(srt_file, "w", encoding="utf-8") as f:
        f.write(srt_content)
    
    return temp_dir, xml_file, json_file, srt_file


def demo_simple_replacement():
    """演示简单的文本替换"""
    print("\n==== 演示1: 简单的变量替换 ====")
    
    # 准备测试文本
    text = "版权所有 © 2023 {company_name}. 由{app_name} v{version}生成"
    print(f"原始文本: {text}")
    
    # 1. 直接替换
    replaced = apply_direct(
        text, 
        company_name="我的公司",
        app_name="超级剪辑",
        version="2.0"
    )
    print(f"直接替换: {replaced}")
    
    # 2. 使用配置文件替换
    config = load_user_config()
    replaced = apply_custom_rules(text, config)
    print(f"使用配置替换: {replaced}")
    
    # 显示所有可用变量
    variables = get_user_variables()
    print("\n当前可用变量:")
    for key, value in variables.items():
        print(f"  - {{{key}}} = {value}")


def demo_templates():
    """演示使用和创建模板"""
    print("\n==== 演示2: 使用和创建模板 ====")
    
    # 加载用户配置
    config = load_user_config()
    
    # 显示现有模板
    print("现有模板:")
    for template_name, rules in config.get("templates", {}).items():
        print(f"  - {template_name}:")
        for pattern, replacement in rules.items():
            print(f"    {pattern} -> {replacement}")
    
    # 创建新模板
    print("\n创建新模板 'professional'")
    new_template = {
        "ClipsMaster AI": "专业视频工作室",
        "技术演示": "专业制作",
        "AI生成": "精心制作"
    }
    
    config = create_user_template("professional", new_template)
    print("模板已创建并设为活动模板")
    
    # 测试模板效果
    text = "本视频由ClipsMaster AI创建，仅用于技术演示。内容为AI生成。"
    print(f"\n原始文本: {text}")
    
    replaced = apply_custom_rules(text, config)
    print(f"应用'professional'模板后: {replaced}")
    
    # 切换回默认模板
    config["active_template"] = "default"
    save_user_config(config)
    
    replaced = apply_custom_rules(text, config)
    print(f"应用'default'模板后: {replaced}")


def demo_content_types(xml_file, json_file, srt_file):
    """演示处理不同类型的内容"""
    print("\n==== 演示3: 处理不同类型的内容 ====")
    
    # 加载用户配置
    config = load_user_config()
    
    # 1. 处理XML
    print("\n处理XML文件:")
    with open(xml_file, "r", encoding="utf-8") as f:
        xml_content = f.read()
    
    print("原始XML (部分):")
    print(xml_content[:200] + "...")
    
    processed_xml = apply_custom_legal(xml_content, "xml", config)
    print("\n处理后XML (部分):")
    print(processed_xml[:200] + "...")
    
    # 2. 处理JSON
    print("\n处理JSON文件:")
    with open(json_file, "r", encoding="utf-8") as f:
        json_content = f.read()
    
    processed_json = apply_custom_legal(json_content, "json", config)
    print("处理后JSON (部分):")
    print(processed_json[:200] + "...")
    
    # 3. 处理SRT
    print("\n处理SRT文件:")
    with open(srt_file, "r", encoding="utf-8") as f:
        srt_content = f.read()
    
    processed_srt = apply_custom_legal(srt_content, "srt", config)
    print("处理后SRT (部分):")
    print(processed_srt[:200] + "...")


def demo_injector_integration():
    """演示与法律注入器的集成"""
    print("\n==== 演示4: 与Legal Injector集成 ====")
    
    # 创建法律注入器实例
    injector = LegalInjector(app_version="2.0")
    
    # 显示原始默认值
    print(f"原始版权文本: {injector.DEFAULT_COPYRIGHT}")
    print(f"原始免责声明: {injector.DEFAULT_DISCLAIMER}")
    
    # 应用自定义规则
    apply_to_legal_injector(injector)
    
    # 显示修改后的默认值
    print(f"\n修改后版权文本: {injector.DEFAULT_COPYRIGHT}")
    print(f"修改后免责声明: {injector.DEFAULT_DISCLAIMER}")
    
    # 测试注入
    xml_str = "<project></project>"
    injected_xml = injector.inject_legal_meta(xml_str)
    
    print("\n注入法律元数据后的XML:")
    print(injected_xml)


def main():
    """主函数"""
    print("===== VisionAI-ClipsMaster 用户自定义法律文本替换演示 =====")
    
    # 创建示例文件
    temp_dir, xml_file, json_file, srt_file = create_sample_files()
    
    try:
        # 演示简单替换
        demo_simple_replacement()
        
        # 演示模板使用
        demo_templates()
        
        # 演示不同内容类型处理
        demo_content_types(xml_file, json_file, srt_file)
        
        # 演示与注入器集成
        demo_injector_integration()
        
    finally:
        # 清理临时文件
        import shutil
        shutil.rmtree(temp_dir)
    
    print("\n===== 演示结束 =====")


if __name__ == "__main__":
    main() 