#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
结构化日志模式定义

定义日志数据结构和验证方法，用于确保日志数据一致性和完整性。
支持业务操作跟踪、资源使用统计和错误分析。
"""

import datetime
import uuid
import json
from typing import Dict, Any, List, Union, Optional

# 导出日志数据结构模式
EXPORT_LOG_SCHEMA = {
    "timestamp": {"type": "datetime", "required": True},
    "operation": {"type": "str", "values": ["init", "clip", "export", "analyze", "process", "combine"]},
    "user_id": {"type": "uuid", "mask": "partial"},  # 部分掩码用户ID
    "resource_usage": {
        "memory_mb": {"type": "float"},
        "cpu_percent": {"type": "float"},
        "gpu_util": {"type": "float"}
    },
    "model_info": {
        "name": {"type": "str"},
        "version": {"type": "str"},
        "language": {"type": "str", "values": ["zh", "en"]},
        "parameters": {"type": "dict"}
    },
    "video_info": {
        "duration": {"type": "float"},
        "resolution": {"type": "str"},
        "format": {"type": "str"},
        "frame_count": {"type": "int"}
    },
    "processing_stats": {
        "clips_created": {"type": "int"},
        "total_duration": {"type": "float"},
        "processing_time": {"type": "float"}
    },
    "error": {
        "code": {"type": "str"},
        "message": {"type": "str"},
        "traceback": {"type": "str", "sensitive": True}
    },
    "result": {"type": "enum", "values": ["success", "warning", "error"]}
}

# 类型验证器
TYPE_VALIDATORS = {
    "str": lambda x: isinstance(x, str),
    "int": lambda x: isinstance(x, int),
    "float": lambda x: isinstance(x, (float, int)),
    "bool": lambda x: isinstance(x, bool),
    "datetime": lambda x: isinstance(x, (datetime.datetime, str)),
    "dict": lambda x: isinstance(x, dict),
    "list": lambda x: isinstance(x, list),
    "uuid": lambda x: isinstance(x, (uuid.UUID, str)),
    "enum": lambda x, values: x in values
}

def validate_log(log_data: Dict[str, Any], schema: Dict[str, Any] = EXPORT_LOG_SCHEMA) -> bool:
    """
    验证日志数据是否符合模式定义
    
    Args:
        log_data: 要验证的日志数据
        schema: 验证模式，默认为EXPORT_LOG_SCHEMA
        
    Returns:
        验证结果，True表示有效，False表示无效
    
    Raises:
        ValueError: 当日志数据不符合模式定义时抛出，并附带详细错误信息
    """
    errors = []
    
    # 验证必填字段
    for field, field_schema in schema.items():
        if isinstance(field_schema, dict) and field_schema.get("required", False):
            if field not in log_data:
                errors.append(f"缺少必填字段: {field}")
    
    # 验证字段类型和值
    for field, value in log_data.items():
        if field not in schema:
            continue
            
        field_schema = schema[field]
        if isinstance(field_schema, dict):
            # 验证简单类型
            if "type" in field_schema:
                field_type = field_schema["type"]
                
                # 枚举值验证
                if field_type == "enum":
                    allowed_values = field_schema.get("values", [])
                    if not TYPE_VALIDATORS[field_type](value, allowed_values):
                        errors.append(f"字段 {field} 的值必须是以下之一: {allowed_values}, 当前值为: {value}")
                # 普通类型验证
                elif field_type in TYPE_VALIDATORS:
                    if value is not None and not TYPE_VALIDATORS[field_type](value):
                        errors.append(f"字段 {field} 必须是 {field_type} 类型, 当前类型为: {type(value).__name__}")
                        
            # 验证嵌套字段
            if isinstance(value, dict) and isinstance(field_schema, dict) and not "type" in field_schema:
                for nested_field, nested_schema in field_schema.items():
                    if isinstance(nested_schema, dict) and nested_field in value:
                        # 递归验证嵌套结构
                        nested_value = value[nested_field]
                        if nested_schema.get("type") == "enum":
                            allowed_values = nested_schema.get("values", [])
                            if not TYPE_VALIDATORS["enum"](nested_value, allowed_values):
                                errors.append(f"字段 {field}.{nested_field} 的值必须是以下之一: {allowed_values}, 当前值为: {nested_value}")
                        elif "type" in nested_schema and nested_schema["type"] in TYPE_VALIDATORS:
                            if nested_value is not None and not TYPE_VALIDATORS[nested_schema["type"]](nested_value):
                                errors.append(f"字段 {field}.{nested_field} 必须是 {nested_schema['type']} 类型, 当前类型为: {type(nested_value).__name__}")
    
    if errors:
        error_message = "\n".join(errors)
        raise ValueError(f"日志验证失败:\n{error_message}")
    
    return True

def mask_sensitive_data(log_data: Dict[str, Any], schema: Dict[str, Any] = EXPORT_LOG_SCHEMA) -> Dict[str, Any]:
    """
    掩码敏感数据，用于保护隐私
    
    Args:
        log_data: 要处理的日志数据
        schema: 验证模式，默认为EXPORT_LOG_SCHEMA
        
    Returns:
        处理后的日志数据副本
    """
    result = log_data.copy()
    
    # 处理掩码字段
    for field, field_schema in schema.items():
        if field not in result:
            continue
            
        if isinstance(field_schema, dict):
            # 处理UUID掩码
            if field_schema.get("type") == "uuid" and field_schema.get("mask") == "partial":
                if isinstance(result[field], str) and len(result[field]) > 8:
                    result[field] = result[field][:8] + "..." + result[field][-4:]
                    
            # 处理标记为敏感的字段
            if field_schema.get("sensitive", False) and result[field]:
                result[field] = "[REDACTED]"
                
            # 递归处理嵌套结构
            if isinstance(result[field], dict) and isinstance(field_schema, dict) and not "type" in field_schema:
                result[field] = mask_sensitive_data(result[field], field_schema)
    
    return result

def create_sample_log() -> Dict[str, Any]:
    """
    创建示例日志数据
    
    Returns:
        示例日志数据
    """
    return {
        "timestamp": datetime.datetime.now().isoformat(),
        "operation": "clip",
        "user_id": str(uuid.uuid4()),
        "resource_usage": {
            "memory_mb": 1254.6,
            "cpu_percent": 45.2,
            "gpu_util": 0.0
        },
        "model_info": {
            "name": "Qwen2.5-7B",
            "version": "1.0.0",
            "language": "zh",
            "parameters": {
                "temperature": 0.7,
                "top_p": 0.9
            }
        },
        "video_info": {
            "duration": 325.5,
            "resolution": "1920x1080",
            "format": "mp4",
            "frame_count": 7812
        },
        "processing_stats": {
            "clips_created": 8,
            "total_duration": 127.8,
            "processing_time": 45.6
        },
        "result": "success"
    }

if __name__ == "__main__":
    # 示例代码
    sample = create_sample_log()
    print(json.dumps(sample, indent=2, ensure_ascii=False))
    
    try:
        validate_log(sample)
        print("日志验证成功!")
        
        # 测试掩码功能
        masked_log = mask_sensitive_data(sample)
        print("掩码后的日志:")
        print(json.dumps(masked_log, indent=2, ensure_ascii=False))
    except ValueError as e:
        print(e) 