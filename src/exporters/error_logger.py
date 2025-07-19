#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
智能错误日志系统

为导出流程提供先进的错误日志记录、分析和故障排除功能：
1. 结构化JSON格式错误日志，包含丰富上下文信息
2. 自动捕获内存状态和系统资源信息
3. 智能错误聚合和去重
4. 错误模式识别
5. 支持将日志导出为各种格式
6. 集成异常分类系统
"""

import os
import sys
import json
import time
import datetime
import traceback
import hashlib
import logging
import threading
from enum import Enum
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Set, Tuple, Callable
from contextlib import contextmanager

# 添加项目根目录到路径
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

from src.utils.log_handler import get_logger
from src.utils.exceptions import ClipMasterError, ErrorCode
from src.exporters.error_reporter import ErrorInfo, ErrorLevel, ErrorCategory

# 配置日志
logger = get_logger("error_logger")

# 确保日志目录存在
LOG_DIR = project_root / "logs" / "exporters"
LOG_DIR.mkdir(parents=True, exist_ok=True)


class ExportLogger:
    """导出模块智能错误日志系统"""
    
    # 错误日志模式定义
    ERROR_LOG_SCHEMA = {
        "timestamp": "datetime",   # 错误发生时间
        "phase": "str",            # 导出阶段
        "error_code": "hex",       # 错误代码
        "video_md5": "str",        # 视频文件MD5（便于追踪特定视频的问题）
        "memory_dump": "bytes",    # 内存状态转储
        "system_info": "dict",     # 系统信息
        "context": "dict",         # 上下文信息
        "stack_trace": "str",      # 完整堆栈跟踪
        "error_hash": "str",       # 错误哈希（用于去重）
        "retry_count": "int",      # 重试计数
        "recovery_attempt": "bool" # 是否已尝试恢复
    }
    
    # 单例实例
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        """确保单例模式"""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ExportLogger, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self, log_file: str = None, max_logs: int = 1000, 
                 retention_days: int = 30, auto_flush: bool = True):
        """初始化错误日志系统
        
        Args:
            log_file: 日志文件路径，默认为logs/exporters/export_errors.json
            max_logs: 单个日志文件最大记录数，超过后将创建新文件
            retention_days: 日志保留天数
            auto_flush: 是否自动刷新日志到磁盘
        """
        # 避免重复初始化
        if getattr(self, '_initialized', False):
            return
            
        # 日志文件和设置
        self.log_file = log_file or str(LOG_DIR / "export_errors.json")
        self.max_logs = max_logs
        self.retention_days = retention_days
        self.auto_flush = auto_flush
        
        # 内部状态
        self.current_phase = None
        self.current_video_hash = None
        self.error_counts = {}  # 按错误类型统计
        self.error_patterns = {}  # 识别的错误模式
        self.last_flush_time = time.time()
        self.pending_logs = []
        self.flush_interval = 60  # 秒
        
        # 确保日志目录存在
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        
        # 初始化完成
        self._initialized = True
        logger.info(f"智能错误日志系统已初始化，日志文件: {self.log_file}")
        
        # 清理过期日志
        self._cleanup_old_logs()
    
    def set_context(self, phase: str = None, video_hash: str = None) -> None:
        """设置当前上下文
        
        Args:
            phase: 当前导出阶段
            video_hash: 当前处理视频的哈希值
        """
        if phase:
            self.current_phase = phase
        if video_hash:
            self.current_video_hash = video_hash
    
    def log_structured_error(self, error: Union[Exception, ClipMasterError], 
                            context: Dict[str, Any] = None) -> Dict[str, Any]:
        """结构化错误日志记录
        
        Args:
            error: 错误对象
            context: 额外上下文信息
            
        Returns:
            Dict[str, Any]: 记录的日志条目
        """
        # 创建基础日志条目
        log_entry = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "phase": self.current_phase,
            "video_md5": self.current_video_hash,
            "context": context or {},
            "retry_count": 0,
            "recovery_attempt": False
        }
        
        # 添加错误信息
        if isinstance(error, ClipMasterError):
            # 获取错误代码
            code = error.code
            
            # 处理不同类型的错误代码
            if hasattr(code, 'value'):  # ErrorCode枚举
                log_entry["error_code"] = f"0x{code.value:04x}"
            elif isinstance(code, int):  # 整数值
                log_entry["error_code"] = f"0x{code:04x}"
            elif isinstance(code, str):  # 字符串值
                if code.startswith("0x"):
                    log_entry["error_code"] = code.upper()
                else:
                    log_entry["error_code"] = f"0x{code.upper()}"
            else:
                # 无法识别的代码类型，使用通用错误
                log_entry["error_code"] = "0x0000"
            
            error_msg = str(error)
            error_details = getattr(error, 'details', {}) or {}
            log_entry["context"].update(error_details)
        else:
            log_entry["error_code"] = "0xFFFF"  # 通用错误代码
            error_msg = f"{type(error).__name__}: {str(error)}"
        
        log_entry["message"] = error_msg
        log_entry["stack_trace"] = "".join(traceback.format_exception(
            type(error), error, error.__traceback__
        ))
        
        # 尝试添加内存和系统信息
        try:
            log_entry["system_info"] = self._get_system_info()
            log_entry["memory_dump"] = self._get_memory_state()
        except Exception as e:
            logger.warning(f"收集系统/内存信息失败: {e}")
            log_entry["system_info"] = {"error": str(e)}
            log_entry["memory_dump"] = {}
        
        # 计算错误哈希（用于去重和模式识别）
        error_hash = self._compute_error_hash(error_msg, log_entry["stack_trace"])
        log_entry["error_hash"] = error_hash
        
        # 更新错误统计
        self.error_counts[error_hash] = self.error_counts.get(error_hash, 0) + 1
        
        # 检测错误模式
        self._detect_error_patterns(log_entry)
        
        # 添加到待处理日志
        self.pending_logs.append(log_entry)
        
        # 根据设置自动刷新
        if self.auto_flush and (time.time() - self.last_flush_time > self.flush_interval or 
                               len(self.pending_logs) >= 10):
            self.flush()
        
        logger.error(f"已记录错误 [{log_entry['error_code']}]: {error_msg}")
        return log_entry
    
    def _compute_error_hash(self, message: str, stack_trace: str) -> str:
        """计算错误指纹哈希，用于去重和聚类
        
        Args:
            message: 错误消息
            stack_trace: 堆栈跟踪
            
        Returns:
            str: 错误哈希值
        """
        # 从堆栈跟踪中提取关键帧（排除行号和变量值）
        try:
            lines = stack_trace.strip().split('\n')
            key_frames = []
            for line in lines:
                if 'File "' in line:
                    # 提取文件名和函数名，忽略行号
                    parts = line.split('File "')[1].split('"')
                    file_name = parts[0].split('/')[-1]  # 只取文件名
                    if ', line ' in line and ' in ' in line:
                        func_name = line.split(' in ')[1].split('\n')[0]
                        key_frames.append(f"{file_name}:{func_name}")
            
            # 最多保留前5个帧，避免哈希过于特异
            frames_str = ';'.join(key_frames[:5])
            # 简化错误消息，移除变量值
            simplified_message = ''.join(c for c in message if c.isalnum() or c in ' _.:')
            
            # 计算哈希值
            hash_input = f"{simplified_message}|{frames_str}"
            return hashlib.md5(hash_input.encode('utf-8')).hexdigest()[:12]
        except Exception as e:
            logger.warning(f"计算错误哈希失败: {e}")
            # 降级策略
            return hashlib.md5(message.encode('utf-8')).hexdigest()[:12]
    
    def _get_system_info(self) -> Dict[str, Any]:
        """获取当前系统信息
        
        Returns:
            Dict[str, Any]: 系统信息
        """
        info = {
            "time": datetime.datetime.now().isoformat(),
            "platform": sys.platform,
            "python_version": sys.version
        }
        
        # 添加进程信息
        if PSUTIL_AVAILABLE:
            try:
                process = psutil.Process()
                info.update({
                    "cpu_percent": process.cpu_percent(interval=0.1),
                    "memory_percent": process.memory_percent(),
                    "memory_rss": process.memory_info().rss / (1024 * 1024),  # MB
                    "num_threads": process.num_threads(),
                    "open_files": len(process.open_files()),
                    "create_time": datetime.datetime.fromtimestamp(process.create_time()).isoformat()
                })
                
                # 系统级信息
                info.update({
                    "system_cpu_percent": psutil.cpu_percent(interval=0.1),
                    "system_memory_percent": psutil.virtual_memory().percent,
                    "system_memory_available": psutil.virtual_memory().available / (1024 * 1024 * 1024),  # GB
                    "disk_usage_percent": psutil.disk_usage('/').percent
                })
            except Exception as e:
                info["psutil_error"] = str(e)
        
        # 添加CUDA信息
        try:
            import torch
            info.update({
                "cuda_available": torch.cuda.is_available(),
                "cuda_device_count": torch.cuda.device_count() if torch.cuda.is_available() else 0,
                "cuda_device_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "N/A"
            })
        except ImportError:
            info["torch_available"] = False
        
        return info
    
    def _get_memory_state(self) -> Dict[str, Any]:
        """获取当前内存状态
        
        Returns:
            Dict[str, Any]: 内存状态信息
        """
        memory_info = {}
        
        if PSUTIL_AVAILABLE:
            try:
                process = psutil.Process()
                memory_info = process.memory_full_info()._asdict()
                # 转换为MB
                for key, value in memory_info.items():
                    if isinstance(value, int) and key not in ('num_page_faults', 'peak_pagefile'):
                        memory_info[key] = value / (1024 * 1024)
            except Exception as e:
                memory_info["error"] = str(e)
        
        # 尝试获取更多应用级内存信息
        try:
            import gc
            objects_count = {}
            for obj in gc.get_objects():
                obj_type = type(obj).__name__
                objects_count[obj_type] = objects_count.get(obj_type, 0) + 1
            
            # 保留最常见的类型
            memory_info["top_objects"] = dict(sorted(
                objects_count.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:20])
        except Exception as e:
            memory_info["gc_error"] = str(e)
        
        return memory_info
    
    def _detect_error_patterns(self, log_entry: Dict[str, Any]) -> None:
        """检测错误模式
        
        Args:
            log_entry: 日志条目
        """
        error_hash = log_entry["error_hash"]
        
        # 如果是第一次看到这个错误，初始化模式记录
        if error_hash not in self.error_patterns:
            self.error_patterns[error_hash] = {
                "first_seen": log_entry["timestamp"],
                "count": 1,
                "phases": {log_entry["phase"]: 1} if log_entry["phase"] else {},
                "videos": {log_entry["video_md5"]: 1} if log_entry["video_md5"] else {},
                "consecutive": 1,
                "last_seen": log_entry["timestamp"]
            }
        else:
            # 更新已有模式
            pattern = self.error_patterns[error_hash]
            pattern["count"] += 1
            
            # 检查是否连续出现
            time_diff = datetime.datetime.fromisoformat(log_entry["timestamp"]) - datetime.datetime.fromisoformat(pattern["last_seen"])
            if time_diff.total_seconds() < 300:  # 5分钟内认为是连续
                pattern["consecutive"] += 1
            else:
                pattern["consecutive"] = 1
            
            # 更新最后一次出现时间
            pattern["last_seen"] = log_entry["timestamp"]
            
            # 更新阶段统计
            if log_entry["phase"]:
                pattern["phases"][log_entry["phase"]] = pattern["phases"].get(log_entry["phase"], 0) + 1
            
            # 更新视频统计
            if log_entry["video_md5"]:
                pattern["videos"][log_entry["video_md5"]] = pattern["videos"].get(log_entry["video_md5"], 0) + 1
        
        # 检查是否需要警报（例如同一错误连续出现多次）
        pattern = self.error_patterns[error_hash]
        if pattern["consecutive"] >= 3:
            logger.warning(f"检测到错误模式: 错误 [{log_entry['error_code']}] 已连续出现 {pattern['consecutive']} 次")
    
    def flush(self) -> None:
        """将挂起的日志条目刷新到磁盘"""
        if not self.pending_logs:
            return
            
        try:
            # 确保日志目录存在
            os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
            
            # 检查文件大小
            logs = []
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    try:
                        logs = json.load(f)
                    except json.JSONDecodeError:
                        # 文件为空或损坏，从头开始
                        logs = []
            
            # 添加新的日志条目
            logs.extend(self.pending_logs)
            
            # 检查是否超过最大记录数
            if len(logs) > self.max_logs:
                # 创建带有时间戳的备份文件
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = f"{os.path.splitext(self.log_file)[0]}_{timestamp}.json"
                with open(backup_file, 'w', encoding='utf-8') as f:
                    json.dump(logs, f, ensure_ascii=False, indent=2)
                
                # 重新开始新的日志文件
                logs = self.pending_logs
            
            # 写入日志文件
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(logs, f, ensure_ascii=False, indent=2)
            
            # 更新状态
            self.pending_logs = []
            self.last_flush_time = time.time()
            
            logger.debug(f"已刷新 {len(logs)} 条错误日志条目到磁盘")
        except Exception as e:
            logger.error(f"刷新错误日志失败: {e}")
    
    def _cleanup_old_logs(self) -> None:
        """清理过期的日志文件"""
        try:
            log_dir = os.path.dirname(self.log_file)
            base_name = os.path.splitext(os.path.basename(self.log_file))[0]
            current_time = time.time()
            
            for filename in os.listdir(log_dir):
                if filename.startswith(base_name) and filename.endswith(".json") and filename != os.path.basename(self.log_file):
                    file_path = os.path.join(log_dir, filename)
                    file_age = current_time - os.path.getmtime(file_path)
                    
                    # 转换为天数
                    file_age_days = file_age / (60 * 60 * 24)
                    
                    if file_age_days > self.retention_days:
                        os.remove(file_path)
                        logger.info(f"已清理过期日志文件: {filename}")
        except Exception as e:
            logger.warning(f"清理过期日志文件失败: {e}")
    
    def get_error_stats(self) -> Dict[str, Any]:
        """获取错误统计信息
        
        Returns:
            Dict[str, Any]: 错误统计
        """
        return {
            "total_errors": sum(self.error_counts.values()),
            "unique_errors": len(self.error_counts),
            "most_frequent": dict(sorted(
                self.error_counts.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:5]),
            "error_patterns": {
                k: {
                    "count": v["count"],
                    "consecutive": v["consecutive"],
                    "first_seen": v["first_seen"],
                    "last_seen": v["last_seen"],
                    "most_common_phase": max(v["phases"].items(), key=lambda x: x[1])[0] if v["phases"] else None
                } 
                for k, v in self.error_patterns.items()
            }
        }
    
    def export_logs(self, format: str = "json", output_file: str = None) -> Optional[str]:
        """导出错误日志
        
        Args:
            format: 导出格式 ("json", "csv", "html")
            output_file: 输出文件路径
            
        Returns:
            Optional[str]: 如果未指定输出文件，则返回导出内容
        """
        # 先刷新所有日志
        self.flush()
        
        try:
            # 确保目录存在
            if output_file:
                os.makedirs(os.path.dirname(output_file), exist_ok=True)
                
            # 读取日志文件
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
            else:
                logs = []
            
            if format == "json":
                output = json.dumps(logs, ensure_ascii=False, indent=2)
            elif format == "csv":
                import csv
                import io
                
                output = io.StringIO()
                if logs:
                    # 获取所有可能的列
                    columns = set()
                    for log in logs:
                        columns.update(log.keys())
                    
                    # 按照一定的顺序排列
                    preferred_order = ["timestamp", "phase", "error_code", "message", "video_md5", "error_hash"]
                    columns = [col for col in preferred_order if col in columns] + [col for col in columns if col not in preferred_order]
                    
                    writer = csv.DictWriter(output, fieldnames=columns)
                    writer.writeheader()
                    for log in logs:
                        # 扁平化某些嵌套字段
                        flat_log = {}
                        for key, value in log.items():
                            if isinstance(value, dict) and key in ["context", "system_info"]:
                                for subkey, subvalue in value.items():
                                    flat_log[f"{key}_{subkey}"] = subvalue
                            else:
                                flat_log[key] = value
                        writer.writerow({col: flat_log.get(col, '') for col in columns})
                
                output = output.getvalue()
            elif format == "html":
                # 简单的HTML报告
                html_parts = ['<!DOCTYPE html><html><head><title>错误日志报告</title>',
                             '<style>body{font-family:Arial;margin:20px}table{border-collapse:collapse;width:100%}',
                             'th,td{text-align:left;padding:8px;border:1px solid #ddd}',
                             'tr:nth-child(even){background-color:#f2f2f2}',
                             'th{background-color:#4CAF50;color:white}',
                             '</style></head><body>',
                             '<h1>错误日志报告</h1>',
                             f'<p>生成时间: {datetime.datetime.now().isoformat()}</p>',
                             f'<p>总记录数: {len(logs)}</p>',
                             '<table><tr>',
                             '<th>时间</th><th>阶段</th><th>错误码</th><th>消息</th><th>视频</th>',
                             '</tr>']
                
                for log in logs:
                    html_parts.append('<tr>')
                    html_parts.append(f'<td>{log.get("timestamp", "")}</td>')
                    html_parts.append(f'<td>{log.get("phase", "")}</td>')
                    html_parts.append(f'<td>{log.get("error_code", "")}</td>')
                    html_parts.append(f'<td>{log.get("message", "")}</td>')
                    html_parts.append(f'<td>{log.get("video_md5", "")}</td>')
                    html_parts.append('</tr>')
                
                html_parts.append('</table></body></html>')
                output = ''.join(html_parts)
            else:
                raise ValueError(f"不支持的导出格式: {format}")
            
            # 写入文件或返回
            if output_file:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(output)
                logger.info(f"错误日志已导出到: {output_file}")
                return None
            else:
                return output
        except Exception as e:
            logger.error(f"导出错误日志失败: {e}")
            return None
    
    @contextmanager
    def log_errors(self, phase: str = None, video_hash: str = None):
        """错误记录上下文管理器
        
        Args:
            phase: 当前阶段
            video_hash: 当前视频哈希
            
        Example:
            ```python
            logger = ExportLogger()
            with logger.log_errors(phase="RENDERING"):
                # 可能引发异常的代码
                process_video()
            ```
        """
        # 保存当前上下文
        old_phase = self.current_phase
        old_hash = self.current_video_hash
        
        # 设置新上下文
        self.set_context(phase, video_hash)
        
        try:
            yield
        except Exception as e:
            # 记录错误
            self.log_structured_error(e)
            # 重新抛出异常
            raise
        finally:
            # 恢复旧上下文
            self.current_phase = old_phase
            self.current_video_hash = old_hash


# 单例访问函数
def get_export_logger() -> ExportLogger:
    """获取导出日志记录器单例
    
    Returns:
        ExportLogger: 导出日志记录器实例
    """
    return ExportLogger()


def log_export_error(error: Exception, phase: str = None, 
                    video_hash: str = None, context: Dict[str, Any] = None) -> None:
    """快速记录导出错误
    
    Args:
        error: 错误对象
        phase: 当前阶段
        video_hash: 当前视频哈希
        context: 额外上下文
    """
    logger = get_export_logger()
    if phase or video_hash:
        logger.set_context(phase, video_hash)
    logger.log_structured_error(error, context)


# 装饰器: 自动错误日志记录
def with_error_logging(phase: str = None):
    """为函数添加自动错误日志记录
    
    Args:
        phase: 导出阶段名称
        
    Returns:
        装饰器函数
    """
    def decorator(func):
        from functools import wraps
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_export_logger()
            
            # 尝试提取视频哈希
            video_hash = None
            for arg in list(args) + list(kwargs.values()):
                if isinstance(arg, dict) and "video_hash" in arg:
                    video_hash = arg["video_hash"]
                    break
                elif hasattr(arg, "video_hash"):
                    video_hash = arg.video_hash
                    break
            
            with logger.log_errors(phase=phase, video_hash=video_hash):
                return func(*args, **kwargs)
        
        return wrapper
    
    return decorator 