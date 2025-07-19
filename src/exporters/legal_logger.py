#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
法律操作审计日志模块

记录系统中的法律相关操作，提供合规性审计支持。
主要功能：
1. 记录所有法律相关操作（版权声明注入、免责声明添加等）
2. 提供结构化、可搜索的审计日志
3. 支持多种日志输出格式（JSON、CSV）
4. 跟踪操作执行人员、时间和内容摘要
"""

import os
import sys
import json
import logging
import hashlib
import traceback
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Tuple
from logging.handlers import RotatingFileHandler
from functools import wraps
from pathlib import Path

# 尝试导入项目中的模块
try:
    from src.utils.log_handler import get_logger
except ImportError:
    # 简单日志替代
    logging.basicConfig(level=logging.INFO)
    def get_logger(name):
        return logging.getLogger(name)

# 创建日志目录
logs_dir = Path(__file__).resolve().parent.parent.parent / "logs"
legal_logs_dir = logs_dir / "legal"
for dir_path in [logs_dir, legal_logs_dir]:
    dir_path.mkdir(exist_ok=True)

# 配置审计日志
logger = get_logger("legal_audit")


class LegalAuditLogger:
    """法律操作审计日志记录器"""
    
    _instance = None  # 单例实例
    
    def __new__(cls, *args, **kwargs):
        """实现单例模式"""
        if cls._instance is None:
            cls._instance = super(LegalAuditLogger, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, log_dir: str = None):
        """初始化审计日志记录器
        
        Args:
            log_dir: 日志目录，默认为 logs/legal
        """
        # 单例模式下防止重复初始化
        if getattr(self, '_initialized', False):
            return
            
        # 设置日志目录
        if log_dir is None:
            self.log_dir = str(legal_logs_dir)
        else:
            self.log_dir = log_dir
            os.makedirs(self.log_dir, exist_ok=True)
        
        # 配置审计日志记录器
        self.audit_logger = logging.getLogger('legal_audit')
        self.audit_logger.setLevel(logging.INFO)
        
        # 如果已经有处理器，不再添加
        if not self.audit_logger.handlers:
            # 文件处理器，按日期轮转
            audit_file = os.path.join(self.log_dir, 'legal_audit.log')
            file_handler = RotatingFileHandler(
                audit_file, 
                maxBytes=10*1024*1024,  # 10MB
                backupCount=30,  # 保留30个备份
                encoding='utf-8'
            )
            
            # 设置日志格式
            formatter = logging.Formatter(
                '%(asctime)s | %(levelname)-8s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(formatter)
            self.audit_logger.addHandler(file_handler)
            
            # 同时输出到控制台
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.audit_logger.addHandler(console_handler)
        
        # 初始化操作计数
        self.operation_count = 0
        
        # 初始化会话ID (用于关联同一会话的多个操作)
        self.session_id = self._generate_session_id()
        
        # 标记为已初始化
        self._initialized = True
        
        # 记录初始化信息
        self.log_system_start()
    
    def _generate_session_id(self) -> str:
        """生成唯一的会话ID
        
        Returns:
            str: 会话ID
        """
        # 使用时间戳和随机数生成唯一ID
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_part = os.urandom(4).hex()
        return f"{timestamp}-{random_part}"
    
    def _get_user_info(self) -> Dict[str, Any]:
        """获取当前用户信息
        
        Returns:
            Dict[str, Any]: 用户信息字典
        """
        import getpass
        import platform
        
        return {
            "username": getpass.getuser(),
            "hostname": platform.node(),
            "os": platform.system(),
            "version": platform.version()
        }
    
    def _calculate_content_hash(self, content: str) -> str:
        """计算内容的哈希值，用于追踪内容变化
        
        Args:
            content: 要计算哈希的内容
            
        Returns:
            str: 内容的MD5哈希值
        """
        if not content:
            return "empty_content"
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def log_operation(self, operation_type: str, details: Dict[str, Any], 
                    content_before: str = None, content_after: str = None,
                    status: str = "success", error: Exception = None):
        """记录法律操作
        
        Args:
            operation_type: 操作类型，如 'copyright_injection', 'disclaimer_addition'
            details: 操作细节
            content_before: 操作前的内容
            content_after: 操作后的内容
            status: 操作状态，'success' 或 'failed'
            error: 如果操作失败，提供错误信息
        """
        # 增加操作计数
        self.operation_count += 1
        
        # 构建审计条目
        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "operation_id": f"{self.session_id}-{self.operation_count}",
            "operation_type": operation_type,
            "status": status,
            "details": details,
            "user": self._get_user_info()
        }
        
        # 添加内容哈希（如果提供）
        if content_before:
            audit_entry["content_before_hash"] = self._calculate_content_hash(content_before)
        
        if content_after:
            audit_entry["content_after_hash"] = self._calculate_content_hash(content_after)
            
            # 如果提供了前后内容，计算变化百分比
            if content_before:
                before_len = len(content_before)
                after_len = len(content_after)
                change_percent = abs(after_len - before_len) / (before_len if before_len > 0 else 1) * 100
                audit_entry["content_change_percent"] = round(change_percent, 2)
        
        # 添加错误信息（如果有）
        if error:
            audit_entry["error"] = {
                "type": error.__class__.__name__,
                "message": str(error),
                "traceback": traceback.format_exc()
            }
        
        # 记录审计条目
        self.audit_logger.info(json.dumps(audit_entry, ensure_ascii=False))
        
        return audit_entry["operation_id"]
    
    def log_legal_injection(self, file_path: str, content_type: str, 
                         injection_type: str, content_before: str = None,
                         content_after: str = None, status: str = "success",
                         error: Exception = None):
        """记录法律内容注入操作
        
        Args:
            file_path: 文件路径
            content_type: 内容类型，如 'xml', 'json', 'srt'
            injection_type: 注入类型，如 'copyright', 'disclaimer'
            content_before: 注入前的内容
            content_after: 注入后的内容
            status: 操作状态
            error: 错误信息
        """
        details = {
            "file_path": file_path,
            "content_type": content_type,
            "injection_type": injection_type,
            "file_size": os.path.getsize(file_path) if os.path.exists(file_path) else 0,
            "timestamp": datetime.now().isoformat()
        }
        
        return self.log_operation(
            operation_type="legal_injection",
            details=details,
            content_before=content_before,
            content_after=content_after,
            status=status,
            error=error
        )
    
    def log_copyright_check(self, file_path: str, has_copyright: bool, 
                         copyright_text: str = None, status: str = "success",
                         error: Exception = None):
        """记录版权检查操作
        
        Args:
            file_path: 文件路径
            has_copyright: 是否包含版权信息
            copyright_text: 版权文本(如果有)
            status: 操作状态
            error: 错误信息
        """
        details = {
            "file_path": file_path,
            "has_copyright": has_copyright,
            "copyright_text": copyright_text,
            "file_size": os.path.getsize(file_path) if os.path.exists(file_path) else 0,
            "timestamp": datetime.now().isoformat()
        }
        
        return self.log_operation(
            operation_type="copyright_check",
            details=details,
            status=status,
            error=error
        )
    
    def log_disclaimer_addition(self, file_path: str, disclaimer_type: str,
                             content_before: str = None, content_after: str = None,
                             status: str = "success", error: Exception = None):
        """记录免责声明添加操作
        
        Args:
            file_path: 文件路径
            disclaimer_type: 免责声明类型
            content_before: 添加前的内容
            content_after: 添加后的内容
            status: 操作状态
            error: 错误信息
        """
        details = {
            "file_path": file_path,
            "disclaimer_type": disclaimer_type,
            "file_size": os.path.getsize(file_path) if os.path.exists(file_path) else 0,
            "timestamp": datetime.now().isoformat()
        }
        
        return self.log_operation(
            operation_type="disclaimer_addition",
            details=details,
            content_before=content_before,
            content_after=content_after,
            status=status,
            error=error
        )
    
    def log_watermark_operation(self, file_path: str, watermark_type: str,
                             text: str = None, position: str = None,
                             status: str = "success", error: Exception = None):
        """记录水印操作
        
        Args:
            file_path: 文件路径
            watermark_type: 水印类型，如 'text', 'image'
            text: 水印文本(如果适用)
            position: 水印位置
            status: 操作状态
            error: 错误信息
        """
        details = {
            "file_path": file_path,
            "watermark_type": watermark_type,
            "text": text,
            "position": position,
            "file_size": os.path.getsize(file_path) if os.path.exists(file_path) else 0,
            "timestamp": datetime.now().isoformat()
        }
        
        return self.log_operation(
            operation_type="watermark_operation",
            details=details,
            status=status,
            error=error
        )
    
    def log_system_start(self):
        """记录系统启动信息"""
        import platform
        import socket
        
        details = {
            "event": "system_start",
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "hostname": socket.gethostname(),
            "ip_address": socket.gethostbyname(socket.gethostname()),
            "timestamp": datetime.now().isoformat()
        }
        
        # 尝试获取系统更多信息
        try:
            import psutil
            details["cpu_count"] = psutil.cpu_count()
            details["memory_total"] = psutil.virtual_memory().total
            details["disk_usage"] = psutil.disk_usage('/').percent
        except ImportError:
            pass
        
        return self.log_operation(
            operation_type="system_event",
            details=details
        )
    
    def export_logs(self, output_format: str = "json", start_date: str = None,
                  end_date: str = None, operation_types: List[str] = None,
                  output_file: str = None) -> str:
        """导出审计日志
        
        Args:
            output_format: 输出格式，'json' 或 'csv'
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            operation_types: 操作类型列表
            output_file: 输出文件路径
            
        Returns:
            str: 输出文件路径
        """
        import csv
        from datetime import datetime, timedelta
        
        # 设置默认输出文件
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            output_file = os.path.join(self.log_dir, f"legal_audit_export_{timestamp}.{output_format}")
        
        # 解析日期范围
        if start_date:
            start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
        else:
            # 默认从30天前开始
            start_datetime = datetime.now() - timedelta(days=30)
            
        if end_date:
            end_datetime = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)  # 包含结束日期
        else:
            end_datetime = datetime.now() + timedelta(days=1)  # 包含今天
        
        # 从日志文件中提取匹配的记录
        matching_records = []
        log_file = os.path.join(self.log_dir, 'legal_audit.log')
        
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        # 解析日志行
                        parts = line.strip().split(' | ', 2)
                        if len(parts) < 3:
                            continue
                            
                        timestamp_str = parts[0]
                        log_datetime = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                        
                        # 检查日期范围
                        if start_datetime <= log_datetime <= end_datetime:
                            # 解析JSON部分
                            json_part = parts[2]
                            record = json.loads(json_part)
                            
                            # 检查操作类型
                            if operation_types and record.get('operation_type') not in operation_types:
                                continue
                                
                            matching_records.append(record)
                    except Exception as e:
                        logger.warning(f"解析日志行时出错: {str(e)}")
        
        # 导出记录
        if output_format == 'json':
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(matching_records, f, ensure_ascii=False, indent=2)
        elif output_format == 'csv':
            if matching_records:
                # 确定CSV列
                fieldnames = ['timestamp', 'operation_type', 'status']
                for record in matching_records:
                    for key in record.keys():
                        if key not in fieldnames and isinstance(record[key], (str, int, float, bool)):
                            fieldnames.append(key)
                
                with open(output_file, 'w', encoding='utf-8', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    
                    for record in matching_records:
                        # 只写入基本字段，避免嵌套结构
                        row = {}
                        for key in fieldnames:
                            if key in record and isinstance(record[key], (str, int, float, bool)):
                                row[key] = record[key]
                        writer.writerow(row)
        
        return output_file


# 装饰器：用于记录法律操作
def log_legal_operation(operation_type_or_lang, text=None):
    """法律操作日志记录装饰器或简便函数
    
    可以作为装饰器使用: @log_legal_operation("operation_type")
    或作为函数使用: log_legal_operation("zh", "文本内容")
    
    Args:
        operation_type_or_lang: 操作类型或语言代码
        text: 如果作为函数使用，此参数为文本内容
    """
    # 作为简单日志函数使用
    if text is not None:
        lang = operation_type_or_lang
        logger.info(f"[法律嵌入] 时间:{datetime.now()} 语言:{lang} 内容摘要:{text[:20]}...")
        return
    
    # 作为装饰器使用
    operation_type = operation_type_or_lang
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 初始化审计日志记录器
            audit_logger = LegalAuditLogger()
            
            # 提取文件路径参数
            file_path = None
            content_type = None
            content_before = None
            
            # 尝试从参数中提取文件路径
            for arg in args:
                if isinstance(arg, str) and os.path.exists(arg):
                    file_path = arg
                    # 尝试读取操作前的内容
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content_before = f.read()
                    except:
                        pass
                    break
            
            # 如果未在位置参数中找到，查找关键字参数
            if file_path is None:
                for param_name in ['file_path', 'path', 'xml_path', 'output_path']:
                    if param_name in kwargs and isinstance(kwargs[param_name], str) and os.path.exists(kwargs[param_name]):
                        file_path = kwargs[param_name]
                        # 尝试读取操作前的内容
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content_before = f.read()
                        except:
                            pass
                        break
            
            # 提取内容类型
            if file_path:
                ext = os.path.splitext(file_path)[1].lower()
                if ext == '.xml':
                    content_type = 'xml'
                elif ext == '.json':
                    content_type = 'json'
                elif ext == '.srt':
                    content_type = 'srt'
                else:
                    content_type = ext[1:] if ext.startswith('.') else ext
            
            # 执行原始函数
            try:
                result = func(*args, **kwargs)
                status = "success"
                error = None
            except Exception as e:
                result = None
                status = "failed"
                error = e
                raise
            finally:
                # 尝试读取操作后的内容
                content_after = None
                if file_path and os.path.exists(file_path):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content_after = f.read()
                    except:
                        pass
                
                # 记录操作
                details = {
                    "function": func.__name__,
                    "args": str(args),
                    "kwargs": str(kwargs),
                    "file_path": file_path,
                    "content_type": content_type
                }
                
                audit_logger.log_operation(
                    operation_type=operation_type,
                    details=details,
                    content_before=content_before,
                    content_after=content_after,
                    status=status,
                    error=error
                )
            
            return result
        return wrapper
    
    return decorator


# 创建单例记录器实例
_audit_logger = LegalAuditLogger()

# 导出简便函数
def log_legal_operation_func(operation_type: str, **kwargs):
    """记录法律操作的简便函数
    
    Args:
        operation_type: 操作类型
        **kwargs: 其他参数
    """
    return _audit_logger.log_operation(operation_type=operation_type, **kwargs)

def get_legal_logger():
    """获取法律审计日志记录器"""
    return _audit_logger

# 示例用法
def log_legal_injection(file_path: str, content_type: str, injection_type: str, 
                      content_before: str = None, content_after: str = None):
    """记录法律内容注入"""
    return _audit_logger.log_legal_injection(
        file_path=file_path,
        content_type=content_type,
        injection_type=injection_type,
        content_before=content_before,
        content_after=content_after
    )

# 简便函数：记录法律操作，参考步骤图示例
def log_legal_operation(lang, text):
    """记录法律声明明操作详情"""
    logger.info(f"[法律嵌入] 时间:{datetime.now()} 语言:{lang} 内容摘要:{text[:20]}...") 