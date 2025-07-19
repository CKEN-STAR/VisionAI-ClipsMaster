#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据类型校验模块

提供严格的数据类型验证功能，确保XML元素和其他数据结构中的值符合预期类型和约束条件。
这个模块是导出器工作流的关键组件，确保导出前的数据符合格式规范。
"""

import sys
import os
import re
import logging
from pathlib import Path
from typing import Any, Dict, Callable, Tuple, List, Union, Optional
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET

# 添加项目根目录到路径
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.utils.log_handler import get_logger
except ImportError:
    # 简单日志替代
    logging.basicConfig(level=logging.INFO)
    def get_logger(name):
        return logging.getLogger(name)

# 配置日志
logger = get_logger("type_checker")


class TypeError(Exception):
    """类型错误异常"""
    pass


class ValidationError(Exception):
    """验证错误异常"""
    pass


def validate_type(value: Any, expected_type: str) -> bool:
    """
    验证值是否符合预期类型
    
    Args:
        value: 要验证的值
        expected_type: 预期类型的字符串标识，支持的类型包括:
            - 'xs:int', 'xs:integer' - 整数
            - 'xs:float', 'xs:decimal' - 浮点数
            - 'xs:string' - 字符串
            - 'xs:boolean' - 布尔值
            - 'xs:date' - 日期
            - 'xs:time' - 时间
            - 'xs:dateTime' - 日期时间
            - 'xs:duration' - 时长
            - 'xs:anyURI' - URI
            - 'xs:ID', 'xs:IDREF' - ID引用
            
    Returns:
        bool: 验证是否通过
    """
    if value is None:
        return False
    
    # 转换为小写以便不区分大小写匹配
    expected_type = expected_type.lower()
    
    # 整数类型
    if expected_type in ('xs:int', 'xs:integer'):
        if isinstance(value, str):
            return value.strip().isdigit() or (value.startswith('-') and value[1:].strip().isdigit())
        return isinstance(value, int)
    
    # 浮点数类型
    elif expected_type in ('xs:float', 'xs:decimal'):
        if isinstance(value, str):
            try:
                float(value)
                return True
            except ValueError:
                return False
        return isinstance(value, (float, int))
    
    # 字符串类型
    elif expected_type == 'xs:string':
        return isinstance(value, str)
    
    # 布尔类型
    elif expected_type == 'xs:boolean':
        if isinstance(value, str):
            value = value.lower()
            return value in ('true', 'false', '1', '0')
        return isinstance(value, bool)
    
    # 日期类型
    elif expected_type == 'xs:date':
        if not isinstance(value, str):
            return False
        try:
            datetime.strptime(value, '%Y-%m-%d')
            return True
        except ValueError:
            return False
    
    # 时间类型
    elif expected_type == 'xs:time':
        if not isinstance(value, str):
            return False
        try:
            datetime.strptime(value, '%H:%M:%S')
            return True
        except ValueError:
            try:
                datetime.strptime(value, '%H:%M:%S.%f')
                return True
            except ValueError:
                return False
    
    # 日期时间类型
    elif expected_type == 'xs:datetime':
        if not isinstance(value, str):
            return False
        try:
            datetime.fromisoformat(value.replace('Z', '+00:00'))
            return True
        except (ValueError, AttributeError):
            try:
                datetime.strptime(value, '%Y-%m-%dT%H:%M:%S')
                return True
            except ValueError:
                try:
                    datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
                    return True
                except ValueError:
                    return False
    
    # 时长类型
    elif expected_type == 'xs:duration':
        if not isinstance(value, str):
            return False
        # ISO 8601 时长格式，例如 "PT1H30M45S"
        duration_pattern = r'^P(?:(\d+)Y)?(?:(\d+)M)?(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+(?:\.\d+)?)S)?)?$'
        return bool(re.match(duration_pattern, value))
    
    # URI类型
    elif expected_type == 'xs:anyuri':
        if not isinstance(value, str):
            return False
        uri_pattern = r'^[a-zA-Z][a-zA-Z0-9+.-]*://[^\\s"<>]+$'
        file_pattern = r'^file:///[^\\s"<>]+$'
        return bool(re.match(uri_pattern, value) or re.match(file_pattern, value) or value.startswith('./') or value.startswith('../'))
    
    # ID类型
    elif expected_type in ('xs:id', 'xs:idref'):
        if not isinstance(value, str):
            return False
        id_pattern = r'^[a-zA-Z_][a-zA-Z0-9_\-\.]*$'
        return bool(re.match(id_pattern, value))
    
    # 自定义或未知类型
    else:
        logger.warning(f"未知类型: {expected_type}，使用宽松验证")
        return True


def check_data_types(element: Any, type_rules: Optional[Dict[str, Tuple[str, Callable]]] = None) -> bool:
    """
    严格检验属性值数据类型
    
    Args:
        element: 要验证的元素，可以是ET.Element, dict或具有get方法的对象
        type_rules: 类型规则字典，键为属性名，值为(类型, 验证函数)元组
        
    Returns:
        bool: 验证是否通过
        
    Raises:
        TypeError: 当验证失败时抛出
    """
    # 如果没有提供规则，使用默认规则
    if type_rules is None:
        type_rules = {
            'width': ('xs:int', lambda x: x > 0),
            'height': ('xs:int', lambda x: x > 0),
            'duration': ('xs:float', lambda x: x >= 0.1),
            'fps': ('xs:float', lambda x: x > 0),
            'frame_rate': ('xs:float', lambda x: x > 0),
            'start': ('xs:float', lambda x: x >= 0),
            'end': ('xs:float', lambda x: x > 0),
            'in': ('xs:int', lambda x: x >= 0),
            'out': ('xs:int', lambda x: x >= 0),
            'timecode': ('xs:string', lambda x: bool(re.match(r'^(\d{2}:){3}\d{2}$', x))),
            'version': ('xs:string', lambda x: bool(x))
        }
    
    for attr, (data_type, validator) in type_rules.items():
        # 获取属性值
        if hasattr(element, 'get') and callable(element.get):
            value = element.get(attr)
        elif isinstance(element, dict):
            value = element.get(attr)
        else:
            # 尝试作为对象属性访问
            try:
                value = getattr(element, attr, None)
            except (AttributeError, TypeError):
                continue
        
        # 如果没有找到属性，跳过验证
        if value is None:
            continue
        
        # 验证类型和约束条件
        if not validate_type(value, data_type) or not validator(value):
            error_message = f"属性 {attr} 值 {value} 无效"
            logger.error(error_message)
            raise TypeError(error_message)
    
    return True


def validate_numeric_ranges(data: Dict[str, Any], rules: Dict[str, Dict[str, Any]]) -> bool:
    """
    验证数值是否在有效范围内
    
    Args:
        data: 要验证的数据字典
        rules: 验证规则，键为字段名，值为规则字典，包含min, max等约束
        
    Returns:
        bool: 验证是否通过
        
    Raises:
        ValidationError: 当验证失败时抛出
    """
    for field, rule in rules.items():
        if field not in data:
            continue
        
        value = data[field]
        
        # 类型检查
        if 'type' in rule:
            if not validate_type(value, rule['type']):
                raise ValidationError(f"字段 {field} 的值 {value} 类型不符合 {rule['type']}")
        
        # 转换为适当的类型进行比较
        if rule['type'] in ('xs:int', 'xs:integer'):
            try:
                numeric_value = int(value)
            except (ValueError, TypeError):
                raise ValidationError(f"字段 {field} 的值 {value} 无法转换为整数")
        elif rule['type'] in ('xs:float', 'xs:decimal'):
            try:
                numeric_value = float(value)
            except (ValueError, TypeError):
                raise ValidationError(f"字段 {field} 的值 {value} 无法转换为浮点数")
        else:
            # 对于非数值类型，跳过范围检查
            continue
        
        # 最小值检查
        if 'min' in rule and numeric_value < rule['min']:
            raise ValidationError(f"字段 {field} 的值 {value} 小于最小值 {rule['min']}")
        
        # 最大值检查
        if 'max' in rule and numeric_value > rule['max']:
            raise ValidationError(f"字段 {field} 的值 {value} 大于最大值 {rule['max']}")
        
        # 允许值列表检查
        if 'allowed' in rule and numeric_value not in rule['allowed']:
            raise ValidationError(f"字段 {field} 的值 {value} 不在允许值列表中: {rule['allowed']}")
    
    return True


def validate_xml_element_types(element: ET.Element, element_rules: Dict[str, Dict[str, Any]]) -> Dict[str, List[str]]:
    """
    验证XML元素的属性和子元素类型
    
    Args:
        element: XML元素
        element_rules: 元素验证规则，针对属性和子元素的类型验证规则
        
    Returns:
        Dict[str, List[str]]: 验证错误信息，按属性名分组
    """
    errors = {}
    
    # 验证属性
    for attr, rules in element_rules.get('attributes', {}).items():
        attr_value = element.get(attr)
        
        # 检查必需属性
        if rules.get('required', False) and attr_value is None:
            if 'attributes' not in errors:
                errors['attributes'] = []
            errors['attributes'].append(f"缺少必需属性: {attr}")
            continue
        
        # 如果属性不存在且不是必需的，跳过验证
        if attr_value is None:
            continue
        
        # 类型验证
        if 'type' in rules:
            if not validate_type(attr_value, rules['type']):
                if 'attributes' not in errors:
                    errors['attributes'] = []
                errors['attributes'].append(f"属性 {attr} 的值 {attr_value} 类型不符合 {rules['type']}")
        
        # 自定义验证函数
        if 'validator' in rules and callable(rules['validator']):
            try:
                if not rules['validator'](attr_value):
                    if 'attributes' not in errors:
                        errors['attributes'] = []
                    errors['attributes'].append(f"属性 {attr} 的值 {attr_value} 未通过自定义验证")
            except Exception as e:
                if 'attributes' not in errors:
                    errors['attributes'] = []
                errors['attributes'].append(f"属性 {attr} 的验证函数发生错误: {str(e)}")
    
    # 验证子元素
    for child_name, rules in element_rules.get('children', {}).items():
        child_elements = element.findall(f'.//{child_name}')
        
        # 检查必需子元素
        if rules.get('required', False) and not child_elements:
            if 'children' not in errors:
                errors['children'] = []
            errors['children'].append(f"缺少必需子元素: {child_name}")
            continue
        
        # 检查子元素数量
        min_occurs = rules.get('min_occurs', 0)
        max_occurs = rules.get('max_occurs')
        
        if len(child_elements) < min_occurs:
            if 'children' not in errors:
                errors['children'] = []
            errors['children'].append(f"子元素 {child_name} 数量不足: 预期至少 {min_occurs}，实际 {len(child_elements)}")
        
        if max_occurs is not None and len(child_elements) > max_occurs:
            if 'children' not in errors:
                errors['children'] = []
            errors['children'].append(f"子元素 {child_name} 数量过多: 预期最多 {max_occurs}，实际 {len(child_elements)}")
        
        # 验证每个子元素
        for idx, child in enumerate(child_elements):
            if 'child_rules' in rules:
                child_errors = validate_xml_element_types(child, rules['child_rules'])
                
                if child_errors:
                    if 'children' not in errors:
                        errors['children'] = []
                    errors['children'].append(f"子元素 {child_name}[{idx}] 验证失败: {child_errors}")
    
    return errors


def get_common_type_rules() -> Dict[str, Dict[str, Any]]:
    """
    获取常用的类型验证规则
    
    Returns:
        Dict[str, Dict[str, Any]]: 常用类型验证规则字典
    """
    return {
        # 视频属性规则
        'video': {
            'width': {
                'type': 'xs:int',
                'min': 1,
                'max': 7680  # 8K分辨率的宽度
            },
            'height': {
                'type': 'xs:int',
                'min': 1,
                'max': 4320  # 8K分辨率的高度
            },
            'fps': {
                'type': 'xs:float',
                'min': 1.0,
                'max': 240.0,
                'allowed': [23.976, 24, 25, 29.97, 30, 50, 59.94, 60, 120, 240]
            }
        },
        
        # 音频属性规则
        'audio': {
            'sample_rate': {
                'type': 'xs:int',
                'min': 8000,
                'max': 192000,
                'allowed': [8000, 11025, 16000, 22050, 32000, 44100, 48000, 88200, 96000, 176400, 192000]
            },
            'bit_depth': {
                'type': 'xs:int',
                'min': 8,
                'max': 32,
                'allowed': [8, 16, 24, 32]
            },
            'channels': {
                'type': 'xs:int',
                'min': 1,
                'max': 8
            }
        },
        
        # 时间码属性规则
        'timecode': {
            'frames': {
                'type': 'xs:int',
                'min': 0
            },
            'seconds': {
                'type': 'xs:float',
                'min': 0.0
            },
            'format': {
                'type': 'xs:string',
                'allowed': ['NDF', 'DF', '24', 'PAL']
            }
        }
    }


if __name__ == "__main__":
    # 如果作为脚本运行，进行简单测试
    import argparse
    
    parser = argparse.ArgumentParser(description='数据类型验证')
    parser.add_argument('xml_path', help='要验证的XML文件路径')
    parser.add_argument('--element', help='要验证的元素XPath', default='.//project')
    
    args = parser.parse_args()
    
    try:
        tree = ET.parse(args.xml_path)
        root = tree.getroot()
        
        element = root.find(args.element)
        if element is None:
            print(f"未找到元素: {args.element}")
            sys.exit(1)
        
        # 创建简单的测试规则
        test_rules = {
            'width': ('xs:int', lambda x: int(x) > 0),
            'height': ('xs:int', lambda x: int(x) > 0),
            'duration': ('xs:float', lambda x: float(x) >= 0)
        }
        
        # 验证元素
        check_data_types(element, test_rules)
        print("验证通过")
        
    except Exception as e:
        print(f"验证失败: {str(e)}")
        sys.exit(1) 