#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
日志数据脱敏模块

提供日志数据敏感信息检测和脱敏功能。
保护包括银行卡号、身份证号、密码、API密钥等敏感信息。
支持复杂数据结构的递归脱敏。
"""

import re
import json
import copy
from typing import Dict, Any, List, Union, Pattern, Callable, Optional

from src.utils.logger import get_module_logger

# 模块日志记录器
logger = get_module_logger("log_sanitizer")

# 敏感信息正则表达式模式
SENSITIVE_PATTERNS = [
    # 银行卡号（16-19位数字，可能有分隔符）
    r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?(\d{0,3})?\b",  # 银行卡号
    
    # 身份证号（18位，最后一位可能是X）
    r"\b\d{17}[\dXx]\b",  # 身份证号
    r"\b\d{6}[-\s]?\d{8}[-\s]?\d{3}[0-9Xx]\b",  # 带分隔符的身份证
    
    # 手机号码（中国区号可选）
    r"\b((\+|00)86[-\s]?)?1[3-9]\d{9}\b",  # 中国手机号码
    
    # 邮箱地址
    r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b",  # 邮箱
    
    # 密码与密钥格式（常见密钥格式）
    r"\b(password|pwd|passwd|secret|api[-_]?key|access[-_]?key|auth[-_]?token)[\s:=]+['\"](.*?)['\"]",  # 密码和密钥
    r"\b[a-zA-Z0-9]{32,}\b",  # 可能的哈希值或长密钥
    
    # 常见API密钥格式
    r"\b(sk|pk|api|key|token|secret)_[a-zA-Z0-9]{16,}\b",  # API密钥常见格式
    
    # IP地址
    r"\b((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b",  # IPv4
    
    # 社交安全号码（美国）
    r"\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b",  # SSN
    
    # JWT令牌
    r"eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*"  # JWT格式
]

# 敏感字段名称列表
SENSITIVE_FIELD_NAMES = [
    "password", "pwd", "passwd", "secret", "api_key", "apikey", "token", 
    "access_token", "auth_token", "credentials", "private_key", "secret_key",
    "card_number", "credit_card", "cvv", "social_security", "ssn", 
    "身份证", "银行卡", "密码", "密钥", "证件号", "手机号", "电话", "邮箱"
]

# 编译正则表达式以提高性能
COMPILED_PATTERNS = [re.compile(pattern, re.IGNORECASE) for pattern in SENSITIVE_PATTERNS]

def sanitize_string(text: str, replacement: str = "[REDACTED]") -> str:
    """
    脱敏字符串中的敏感信息
    
    Args:
        text: 需要脱敏的字符串
        replacement: 替换敏感信息的字符串
        
    Returns:
        脱敏后的字符串
    """
    if not isinstance(text, str):
        return text
        
    sanitized = text
    for pattern in COMPILED_PATTERNS:
        sanitized = pattern.sub(replacement, sanitized)
    
    return sanitized

def is_sensitive_field(field_name: str) -> bool:
    """
    判断字段名是否为敏感字段
    
    Args:
        field_name: 字段名称
        
    Returns:
        是否为敏感字段
    """
    field_name_lower = field_name.lower()
    
    # 检查是否包含敏感字段名
    for sensitive_name in SENSITIVE_FIELD_NAMES:
        if sensitive_name in field_name_lower:
            return True
            
    return False

def sanitize_value(value: Any, field_name: str = "", replacement: str = "[REDACTED]") -> Any:
    """
    根据值类型和字段名称脱敏数据
    
    Args:
        value: 需要脱敏的值
        field_name: 字段名称，用于检查是否为敏感字段
        replacement: 替换敏感信息的字符串
        
    Returns:
        脱敏后的值
    """
    # 如果字段名是敏感的，直接替换整个值
    if field_name and is_sensitive_field(field_name):
        if isinstance(value, (str, int, float, bool)):
            return replacement
    
    # 根据值类型进行不同的脱敏处理
    if isinstance(value, str):
        return sanitize_string(value, replacement)
    elif isinstance(value, (int, float, bool, type(None))):
        return value
    elif isinstance(value, list):
        return [sanitize_value(item, "", replacement) for item in value]
    elif isinstance(value, dict):
        return sanitize_dict(value, replacement)
    elif hasattr(value, '__dict__'):
        # 处理对象
        try:
            obj_dict = value.__dict__.copy()
            sanitized_dict = sanitize_dict(obj_dict, replacement)
            for k, v in sanitized_dict.items():
                setattr(value, k, v)
        except:
            pass
        return value
    else:
        # 对于其他类型，尝试转为字符串处理
        try:
            str_value = str(value)
            sanitized = sanitize_string(str_value, replacement)
            if sanitized != str_value:
                return sanitized
            return value
        except:
            return value

def sanitize_dict(data: Dict[str, Any], replacement: str = "[REDACTED]") -> Dict[str, Any]:
    """
    递归脱敏字典中的敏感信息
    
    Args:
        data: 需要脱敏的字典
        replacement: 替换敏感信息的字符串
        
    Returns:
        脱敏后的字典
    """
    if not isinstance(data, dict):
        return data
        
    sanitized = {}
    for key, value in data.items():
        sanitized[key] = sanitize_value(value, key, replacement)
    
    return sanitized

def sanitize_log_entry(entry: Dict[str, Any], replacement: str = "[REDACTED]") -> Dict[str, Any]:
    """
    脱敏日志条目中的敏感信息
    
    Args:
        entry: 日志条目
        replacement: 替换敏感信息的字符串
        
    Returns:
        脱敏后的日志条目
    """
    if not isinstance(entry, dict):
        if isinstance(entry, str):
            return sanitize_string(entry, replacement)
        return entry
        
    # 创建条目的深拷贝，避免修改原始数据
    sanitized_entry = copy.deepcopy(entry)
    
    # 特殊处理某些字段
    if "message" in sanitized_entry and isinstance(sanitized_entry["message"], str):
        sanitized_entry["message"] = sanitize_string(sanitized_entry["message"], replacement)
        
    if "error" in sanitized_entry and isinstance(sanitized_entry["error"], dict):
        if "message" in sanitized_entry["error"]:
            sanitized_entry["error"]["message"] = sanitize_string(
                sanitized_entry["error"]["message"], replacement
            )
        if "traceback" in sanitized_entry["error"]:
            sanitized_entry["error"]["traceback"] = sanitize_string(
                sanitized_entry["error"]["traceback"], replacement
            )
            
    # 递归处理整个条目
    return sanitize_dict(sanitized_entry, replacement)

def create_sanitizing_filter(replacement: str = "[REDACTED]") -> Callable:
    """
    创建日志脱敏过滤器函数
    
    Args:
        replacement: 替换敏感信息的字符串
        
    Returns:
        脱敏过滤器函数
    """
    def filter_func(log_data: Dict[str, Any]) -> Dict[str, Any]:
        return sanitize_log_entry(log_data, replacement)
    
    return filter_func

def add_sensitive_pattern(pattern: Union[str, Pattern]) -> None:
    """
    添加自定义敏感信息模式
    
    Args:
        pattern: 正则表达式模式（字符串或已编译的正则表达式）
    """
    global COMPILED_PATTERNS
    
    if isinstance(pattern, str):
        COMPILED_PATTERNS.append(re.compile(pattern, re.IGNORECASE))
    elif hasattr(pattern, 'search') and callable(pattern.search):
        COMPILED_PATTERNS.append(pattern)
    else:
        raise ValueError("模式必须是字符串或已编译的正则表达式")

def add_sensitive_field_name(field_name: str) -> None:
    """
    添加自定义敏感字段名
    
    Args:
        field_name: 敏感字段名
    """
    global SENSITIVE_FIELD_NAMES
    field_name = field_name.lower()
    if field_name not in SENSITIVE_FIELD_NAMES:
        SENSITIVE_FIELD_NAMES.append(field_name)

def is_sensitive_data(data: Any) -> bool:
    """
    检查数据是否包含敏感信息
    
    Args:
        data: 要检查的数据
        
    Returns:
        是否包含敏感信息
    """
    if isinstance(data, str):
        for pattern in COMPILED_PATTERNS:
            if pattern.search(data):
                return True
        return False
    elif isinstance(data, dict):
        for key, value in data.items():
            if is_sensitive_field(key) or is_sensitive_data(value):
                return True
        return False
    elif isinstance(data, list):
        return any(is_sensitive_data(item) for item in data)
    else:
        # 对于其他类型，尝试转为字符串检查
        try:
            return is_sensitive_data(str(data))
        except:
            return False

if __name__ == "__main__":
    # 测试代码
    test_data = {
        "user": "张三",
        "message": "我的银行卡号是6222020903001483077，请帮我查询余额",
        "password": "p@ssw0rd123",
        "email": "zhangsan@example.com",
        "ip_address": "192.168.1.1",
        "card_info": {
            "card_number": "4111 1111 1111 1111",
            "expiry": "12/25",
            "cvv": "123"
        },
        "address": "北京市海淀区中关村",
        "phone": "13800138000",
        "id_card": "110101199003072814"
    }
    
    sanitized = sanitize_log_entry(test_data)
    print("原始数据:")
    print(json.dumps(test_data, ensure_ascii=False, indent=2))
    print("\n脱敏后数据:")
    print(json.dumps(sanitized, ensure_ascii=False, indent=2))
    
    # 测试字符串脱敏
    test_str = "API密钥是sk_live_1234567890abcdef，不要告诉别人"
    print("\n原始字符串:", test_str)
    print("脱敏后字符串:", sanitize_string(test_str))
    
    # 测试敏感信息检测
    print("\n数据是否包含敏感信息:", is_sensitive_data(test_data)) 