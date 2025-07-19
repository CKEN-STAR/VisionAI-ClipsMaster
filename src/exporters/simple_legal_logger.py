#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简化版法律操作审计日志模块

提供基本的法律操作日志记录功能，确保可以满足XML异常回滚机制的需要。
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from functools import wraps
from typing import Dict, Any, Optional

# 创建日志目录
logs_dir = Path(__file__).resolve().parent.parent.parent / "logs"
logs_dir.mkdir(exist_ok=True)

# 配置基本日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(logs_dir / "legal_operations.log", encoding="utf-8")
    ]
)

logger = logging.getLogger("legal_audit")


def log_legal_operation(lang: str, text: str):
    """记录法律操作信息
    
    Args:
        lang: 语言代码
        text: 法律声明文本
    """
    logger.info(f"[法律嵌入] 时间:{datetime.now()} 语言:{lang} 内容摘要:{text[:20]}...")


def log_operation(operation_type: str, details: Dict[str, Any], status: str = "success"):
    """记录详细的操作信息
    
    Args:
        operation_type: 操作类型
        details: 操作详情
        status: 操作状态
    """
    entry = {
        "timestamp": datetime.now().isoformat(),
        "operation_type": operation_type,
        "status": status,
        "details": details
    }
    
    logger.info(json.dumps(entry, ensure_ascii=False))


def with_legal_audit(operation_type: str):
    """为函数添加法律审计日志的装饰器
    
    Args:
        operation_type: 操作类型
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 提取文件路径
            file_path = None
            for arg in args:
                if isinstance(arg, str) and arg.endswith(('.xml', '.fcpxml', '.json')):
                    file_path = arg
                    break
            
            for key, value in kwargs.items():
                if key in ['file_path', 'xml_path', 'path'] and isinstance(value, str):
                    file_path = value
                    break
            
            # 记录操作开始
            log_operation(
                operation_type=f"{operation_type}_start",
                details={
                    "function": func.__name__,
                    "file_path": file_path
                }
            )
            
            # 执行原始函数
            try:
                result = func(*args, **kwargs)
                
                # 记录操作成功
                log_operation(
                    operation_type=operation_type,
                    details={
                        "function": func.__name__, 
                        "file_path": file_path,
                        "result": "success"
                    }
                )
                
                return result
                
            except Exception as e:
                # 记录操作失败
                log_operation(
                    operation_type=operation_type,
                    details={
                        "function": func.__name__,
                        "file_path": file_path,
                        "error": str(e)
                    },
                    status="failed"
                )
                raise
                
        return wrapper
    return decorator


# 导出便捷函数
def log_legal_injection(file_path: str, content_type: str, legal_text: str):
    """记录法律注入操作
    
    Args:
        file_path: 文件路径
        content_type: 内容类型
        legal_text: 法律文本
    """
    log_operation(
        operation_type="legal_injection",
        details={
            "file_path": file_path,
            "content_type": content_type,
            "text_preview": legal_text[:50] + "..." if len(legal_text) > 50 else legal_text
        }
    )
    
    # 同时使用简单日志格式
    lang = "zh"  # 默认中文
    log_legal_operation(lang, legal_text)


def log_disclaimer_addition(file_path: str, disclaimer_text: str):
    """记录免责声明添加操作
    
    Args:
        file_path: 文件路径
        disclaimer_text: 免责声明文本
    """
    log_operation(
        operation_type="disclaimer_addition",
        details={
            "file_path": file_path,
            "text_preview": disclaimer_text[:50] + "..." if len(disclaimer_text) > 50 else disclaimer_text
        }
    )
    
    # 同时使用简单日志格式
    log_legal_operation("zh", disclaimer_text) 