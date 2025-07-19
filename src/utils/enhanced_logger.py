#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 增强日志系统

提供结构化、可搜索、便于调试的日志输出格式
"""

import os
import sys
import json
import time
import logging
import traceback
from datetime import datetime
from typing import Dict, Any, Optional, Union
from pathlib import Path
import threading

class LogLevel:
    """日志级别常量"""
    CRITICAL = "CRITICAL"
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"
    DEBUG = "DEBUG"
    TRACE = "TRACE"  # 自定义追踪级别

class LogCategory:
    """日志分类"""
    SYSTEM = "SYSTEM"           # 系统级日志
    USER_ACTION = "USER_ACTION" # 用户操作日志
    PERFORMANCE = "PERFORMANCE" # 性能监控日志
    EXCEPTION = "EXCEPTION"     # 异常处理日志
    AI_MODEL = "AI_MODEL"       # AI模型相关日志
    VIDEO_PROCESS = "VIDEO_PROCESS"  # 视频处理日志
    FILE_IO = "FILE_IO"         # 文件操作日志
    NETWORK = "NETWORK"         # 网络相关日志

class StructuredFormatter(logging.Formatter):
    """结构化日志格式化器"""
    
    def __init__(self, include_traceback: bool = True):
        super().__init__()
        self.include_traceback = include_traceback
    
    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录"""
        # 基础信息
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread_id": record.thread,
            "thread_name": record.threadName,
            "process_id": record.process
        }
        
        # 添加自定义字段
        if hasattr(record, 'category'):
            log_entry["category"] = record.category
        
        if hasattr(record, 'user_id'):
            log_entry["user_id"] = record.user_id
        
        if hasattr(record, 'session_id'):
            log_entry["session_id"] = record.session_id
        
        if hasattr(record, 'operation'):
            log_entry["operation"] = record.operation
        
        if hasattr(record, 'duration'):
            log_entry["duration_ms"] = record.duration
        
        if hasattr(record, 'memory_usage'):
            log_entry["memory_mb"] = record.memory_usage
        
        if hasattr(record, 'file_path'):
            log_entry["file_path"] = record.file_path
        
        if hasattr(record, 'error_code'):
            log_entry["error_code"] = record.error_code
        
        if hasattr(record, 'context'):
            log_entry["context"] = record.context
        
        # 异常信息
        if record.exc_info and self.include_traceback:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        # 格式化输出
        return self._format_output(log_entry, record.levelname)
    
    def _format_output(self, log_entry: Dict[str, Any], level: str) -> str:
        """格式化输出"""
        # 时间戳（简化格式）
        timestamp = log_entry["timestamp"].split('T')[1][:12]  # HH:MM:SS.mmm
        
        # 级别标识（带颜色）
        level_colors = {
            "CRITICAL": "\033[95m",  # 紫色
            "ERROR": "\033[91m",     # 红色
            "WARNING": "\033[93m",   # 黄色
            "INFO": "\033[92m",      # 绿色
            "DEBUG": "\033[94m",     # 蓝色
            "TRACE": "\033[96m"      # 青色
        }
        reset_color = "\033[0m"
        
        level_color = level_colors.get(level, "")
        level_str = f"{level_color}[{level:8}]{reset_color}"
        
        # 基础信息行
        basic_info = f"{timestamp} {level_str} {log_entry['logger']:20} | {log_entry['message']}"
        
        # 详细信息
        details = []
        
        # 位置信息
        location = f"📍 {log_entry['module']}.{log_entry['function']}:{log_entry['line']}"
        details.append(location)
        
        # 分类信息
        if 'category' in log_entry:
            details.append(f"🏷️  {log_entry['category']}")
        
        # 操作信息
        if 'operation' in log_entry:
            details.append(f"⚙️  {log_entry['operation']}")
        
        # 性能信息
        if 'duration_ms' in log_entry:
            details.append(f"⏱️  {log_entry['duration_ms']:.2f}ms")
        
        if 'memory_mb' in log_entry:
            details.append(f"💾 {log_entry['memory_mb']:.1f}MB")
        
        # 文件信息
        if 'file_path' in log_entry:
            details.append(f"📁 {log_entry['file_path']}")
        
        # 错误代码
        if 'error_code' in log_entry:
            details.append(f"🚨 {log_entry['error_code']}")
        
        # 上下文信息
        if 'context' in log_entry and log_entry['context']:
            context_str = json.dumps(log_entry['context'], ensure_ascii=False)
            details.append(f"📋 {context_str}")
        
        # 异常信息
        if 'exception' in log_entry:
            exc = log_entry['exception']
            details.append(f"❌ {exc['type']}: {exc['message']}")
            if level in ["CRITICAL", "ERROR"]:
                # 只在严重错误时显示完整堆栈
                details.extend([f"   {line.strip()}" for line in exc['traceback']])
        
        # 组合输出
        if details:
            detail_lines = [f"    {detail}" for detail in details]
            return basic_info + "\n" + "\n".join(detail_lines)
        else:
            return basic_info

class EnhancedLogger:
    """增强日志记录器"""
    
    def __init__(self, name: str, log_dir: str = "logs"):
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # 创建日志记录器
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # 避免重复添加处理器
        if not self.logger.handlers:
            self._setup_handlers()
        
        # 会话信息
        self.session_id = f"session_{int(time.time())}"
        self.user_id = "default_user"
        
        # 性能监控
        self.operation_start_times = {}
        self.lock = threading.Lock()
    
    def _setup_handlers(self):
        """设置日志处理器"""
        formatter = StructuredFormatter(include_traceback=True)
        
        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # 文件处理器（所有级别）
        today = datetime.now().strftime("%Y%m%d")
        log_file = self.log_dir / f"{self.name}_{today}.log"
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # 错误文件处理器（仅错误）
        error_file = self.log_dir / f"{self.name}_errors_{today}.log"
        error_handler = logging.FileHandler(error_file, encoding='utf-8')
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        self.logger.addHandler(error_handler)
    
    def _log_with_context(self, level: int, message: str, **kwargs):
        """带上下文的日志记录"""
        extra = {
            'session_id': self.session_id,
            'user_id': self.user_id
        }
        extra.update(kwargs)
        
        self.logger.log(level, message, extra=extra)
    
    def trace(self, message: str, **kwargs):
        """追踪级别日志"""
        self._log_with_context(5, message, **kwargs)  # 自定义级别
    
    def debug(self, message: str, **kwargs):
        """调试日志"""
        self._log_with_context(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """信息日志"""
        self._log_with_context(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """警告日志"""
        self._log_with_context(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """错误日志"""
        self._log_with_context(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """严重错误日志"""
        self._log_with_context(logging.CRITICAL, message, **kwargs)
    
    def log_exception(self, message: str, exception: Exception, **kwargs):
        """记录异常"""
        kwargs.update({
            'category': LogCategory.EXCEPTION,
            'error_code': type(exception).__name__,
            'context': {'exception_args': str(exception.args)}
        })
        self.logger.error(message, exc_info=True, extra=kwargs)
    
    def log_performance(self, operation: str, duration_ms: float, **kwargs):
        """记录性能信息"""
        kwargs.update({
            'category': LogCategory.PERFORMANCE,
            'operation': operation,
            'duration': duration_ms
        })
        
        # 性能阈值警告
        if duration_ms > 5000:  # 5秒
            self.warning(f"操作耗时过长: {operation}", **kwargs)
        elif duration_ms > 1000:  # 1秒
            self.info(f"操作完成: {operation}", **kwargs)
        else:
            self.debug(f"操作完成: {operation}", **kwargs)
    
    def log_user_action(self, action: str, **kwargs):
        """记录用户操作"""
        kwargs.update({
            'category': LogCategory.USER_ACTION,
            'operation': action
        })
        self.info(f"用户操作: {action}", **kwargs)
    
    def log_file_operation(self, operation: str, file_path: str, **kwargs):
        """记录文件操作"""
        kwargs.update({
            'category': LogCategory.FILE_IO,
            'operation': operation,
            'file_path': file_path
        })
        self.debug(f"文件操作: {operation}", **kwargs)
    
    def start_operation(self, operation_id: str) -> str:
        """开始操作计时"""
        with self.lock:
            self.operation_start_times[operation_id] = time.time()
        return operation_id
    
    def end_operation(self, operation_id: str, operation_name: str = None, **kwargs):
        """结束操作计时"""
        with self.lock:
            start_time = self.operation_start_times.pop(operation_id, None)
        
        if start_time:
            duration_ms = (time.time() - start_time) * 1000
            operation_name = operation_name or operation_id
            self.log_performance(operation_name, duration_ms, **kwargs)
        else:
            self.warning(f"未找到操作开始时间: {operation_id}")
    
    def set_user_context(self, user_id: str, session_id: str = None):
        """设置用户上下文"""
        self.user_id = user_id
        if session_id:
            self.session_id = session_id

# 全局日志管理器
_loggers = {}
_lock = threading.Lock()

def get_logger(name: str, log_dir: str = "logs") -> EnhancedLogger:
    """获取增强日志记录器"""
    with _lock:
        if name not in _loggers:
            _loggers[name] = EnhancedLogger(name, log_dir)
        return _loggers[name]

def log_operation_time(operation_name: str, logger_name: str = "performance"):
    """操作计时装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger = get_logger(logger_name)
            operation_id = logger.start_operation(f"{func.__name__}_{int(time.time())}")
            
            try:
                result = func(*args, **kwargs)
                logger.end_operation(operation_id, operation_name, 
                                   context={"function": func.__name__, "success": True})
                return result
            except Exception as e:
                logger.end_operation(operation_id, operation_name,
                                   context={"function": func.__name__, "success": False, "error": str(e)})
                raise
        return wrapper
    return decorator
