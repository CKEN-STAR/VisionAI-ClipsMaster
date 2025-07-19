#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据类型验证演示

本示例演示如何使用数据类型验证模块进行XML元素和其他数据结构的类型检查。
"""

import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Any

# 添加项目根目录到路径
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

try:
    # 导入类型验证功能
    from src.exporters.type_checker import (
        validate_type,
        check_data_types,
        validate_numeric_ranges,
        validate_xml_element_types,
        get_common_type_rules,
        TypeError,
        ValidationError
    )
except ImportError as e:
    print(f"导入错误: {e}")
    sys.exit(1)


def create_test_xml():
    """创建一个测试XML文件"""
    print("创建测试XML文件...")
    
    # 创建根元素
    root = ET.Element("project", version="1.0")
    
    # 创建视频设置元素
    video_settings = ET.SubElement(root, "video_settings")
    video_settings.set("width", "1920")
    video_settings.set("height", "1080")
    video_settings.set("fps", "29.97")
    
    # 创建音频设置元素
    audio_settings = ET.SubElement(root, "audio_settings")
    audio_settings.set("sample_rate", "48000")
    audio_settings.set("bit_depth", "24")
    audio_settings.set("channels", "2")
    
    # 创建时间码元素
    timecode = ET.SubElement(root, "timecode")
    timecode.set("format", "NDF")
    timecode.set("frames", "0")
    timecode.text = "00:00:00:00"
    
    # 创建一个包含无效值的元素（用于演示验证失败）
    invalid_element = ET.SubElement(root, "invalid_settings")
    invalid_element.set("width", "-100")  # 负宽度，无效
    invalid_element.set("duration", "abc")  # 非数字，无效
    
    # 创建XML树
    tree = ET.ElementTree(root)
    
    # 创建输出目录
    output_dir = project_root / "test"
    os.makedirs(output_dir, exist_ok=True)
    
    # 保存XML文件
    output_path = output_dir / "type_validation_test.xml"
    ET.indent(tree)
    tree.write(output_path, encoding="utf-8", xml_declaration=True)
    
    print(f"测试XML文件已保存到: {output_path}")
    return output_path


def demo_simple_type_validation():
    """演示简单类型验证"""
    print("\n=== 简单类型验证 ===")
    
    test_cases = [
        {"value": "42", "type": "xs:int", "expected": True},
        {"value": "-10", "type": "xs:int", "expected": True},
        {"value": "3.14", "type": "xs:float", "expected": True},
        {"value": "not a number", "type": "xs:float", "expected": False},
        {"value": "2023-01-15", "type": "xs:date", "expected": True},
        {"value": "2023/01/15", "type": "xs:date", "expected": False},
        {"value": "true", "type": "xs:boolean", "expected": True},
        {"value": "FALSE", "type": "xs:boolean", "expected": True},
        {"value": "maybe", "type": "xs:boolean", "expected": False},
        {"value": "PT1H30M45S", "type": "xs:duration", "expected": True},
        {"value": "1:30:45", "type": "xs:duration", "expected": False},
        {"value": "http://example.com", "type": "xs:anyURI", "expected": True},
        {"value": "not a uri", "type": "xs:anyURI", "expected": False},
        {"value": "valid_id_123", "type": "xs:ID", "expected": True},
        {"value": "123invalid", "type": "xs:ID", "expected": False}
    ]
    
    for i, case in enumerate(test_cases):
        result = validate_type(case["value"], case["type"])
        status = "通过" if result == case["expected"] else "失败"
        print(f"测试 {i+1}: 值 '{case['value']}' 验证为 '{case['type']}' - 结果: {result} - 预期: {case['expected']} - {status}")


def demo_element_validation(xml_path):
    """演示XML元素验证"""
    print("\n=== XML元素验证 ===")
    
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        # 获取视频设置元素
        video_settings = root.find(".//video_settings")
        if video_settings is not None:
            print("\n验证视频设置元素:")
            type_rules = {
                'width': ('xs:int', lambda x: int(x) > 0),
                'height': ('xs:int', lambda x: int(x) > 0),
                'fps': ('xs:float', lambda x: float(x) > 0)
            }
            
            try:
                check_data_types(video_settings, type_rules)
                print("✓ 视频设置验证通过")
            except TypeError as e:
                print(f"✗ 视频设置验证失败: {str(e)}")
        
        # 获取音频设置元素
        audio_settings = root.find(".//audio_settings")
        if audio_settings is not None:
            print("\n验证音频设置元素:")
            type_rules = {
                'sample_rate': ('xs:int', lambda x: int(x) in [44100, 48000, 96000]),
                'bit_depth': ('xs:int', lambda x: int(x) in [16, 24, 32]),
                'channels': ('xs:int', lambda x: 1 <= int(x) <= 8)
            }
            
            try:
                check_data_types(audio_settings, type_rules)
                print("✓ 音频设置验证通过")
            except TypeError as e:
                print(f"✗ 音频设置验证失败: {str(e)}")
        
        # 获取无效元素（应该验证失败）
        invalid_element = root.find(".//invalid_settings")
        if invalid_element is not None:
            print("\n验证无效元素（预期失败）:")
            type_rules = {
                'width': ('xs:int', lambda x: int(x) > 0),
                'duration': ('xs:float', lambda x: float(x) >= 0)
            }
            
            try:
                check_data_types(invalid_element, type_rules)
                print("✓ 无效元素验证通过（意外结果）")
            except TypeError as e:
                print(f"✓ 预期的验证失败: {str(e)}")
        
    except Exception as e:
        print(f"XML解析或验证出错: {str(e)}")


def demo_numeric_range_validation():
    """演示数值范围验证"""
    print("\n=== 数值范围验证 ===")
    
    # 测试数据
    test_data = {
        "width": "1920",
        "height": "1080",
        "fps": "29.97",
        "bit_depth": "24",
        "channels": "5"
    }
    
    # 验证规则
    validation_rules = {
        "width": {
            "type": "xs:int",
            "min": 1,
            "max": 7680  # 8K分辨率的宽度
        },
        "height": {
            "type": "xs:int",
            "min": 1,
            "max": 4320  # 8K分辨率的高度
        },
        "fps": {
            "type": "xs:float",
            "min": 1.0,
            "max": 240.0,
            "allowed": [23.976, 24, 25, 29.97, 30, 50, 59.94, 60, 120]
        },
        "bit_depth": {
            "type": "xs:int",
            "allowed": [8, 16, 24, 32]
        }
    }
    
    try:
        validate_numeric_ranges(test_data, validation_rules)
        print("✓ 数值范围验证通过")
    except ValidationError as e:
        print(f"✗ 数值范围验证失败: {str(e)}")
    
    # 测试超出范围的值
    print("\n测试超出范围的值（预期失败）:")
    invalid_data = test_data.copy()
    invalid_data["width"] = "10000"  # 超出最大值
    
    try:
        validate_numeric_ranges(invalid_data, validation_rules)
        print("✓ 范围验证通过（意外结果）")
    except ValidationError as e:
        print(f"✓ 预期的验证失败: {str(e)}")


def demo_xml_element_validation(xml_path):
    """演示完整的XML元素结构验证"""
    print("\n=== XML元素结构验证 ===")
    
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        # 定义验证规则
        project_rules = {
            'attributes': {
                'version': {
                    'type': 'xs:string',
                    'required': True
                }
            },
            'children': {
                'video_settings': {
                    'required': True,
                    'min_occurs': 1,
                    'max_occurs': 1,
                    'child_rules': {
                        'attributes': {
                            'width': {
                                'type': 'xs:int',
                                'required': True,
                                'validator': lambda x: int(x) > 0
                            },
                            'height': {
                                'type': 'xs:int',
                                'required': True,
                                'validator': lambda x: int(x) > 0
                            },
                            'fps': {
                                'type': 'xs:float',
                                'required': True,
                                'validator': lambda x: float(x) > 0
                            }
                        }
                    }
                },
                'audio_settings': {
                    'required': True,
                    'min_occurs': 1,
                    'max_occurs': 1
                },
                'timecode': {
                    'required': True,
                    'min_occurs': 1
                }
            }
        }
        
        # 验证XML元素
        errors = validate_xml_element_types(root, project_rules)
        
        if errors:
            print("✗ XML元素结构验证失败:")
            for category, error_list in errors.items():
                print(f"  {category}:")
                for error in error_list:
                    print(f"    - {error}")
        else:
            print("✓ XML元素结构验证通过")
        
    except Exception as e:
        print(f"XML解析或验证出错: {str(e)}")


def main():
    # 创建测试XML文件
    xml_path = create_test_xml()
    
    # 演示不同类型的验证
    demo_simple_type_validation()
    demo_element_validation(xml_path)
    demo_numeric_range_validation()
    demo_xml_element_validation(xml_path)
    
    print("\n演示完成")


if __name__ == "__main__":
    main() 