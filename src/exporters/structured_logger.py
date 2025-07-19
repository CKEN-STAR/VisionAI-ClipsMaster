#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
结构化日志记录器

提供结构化日志记录功能，包括日志写入、读取和分析。
集成日志模式验证，确保日志数据格式一致性。
"""

import os
import json
import datetime
import uuid
import platform
import psutil
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Callable

from src.exporters.log_schema import EXPORT_LOG_SCHEMA, validate_log, mask_sensitive_data
from src.utils.logger import get_module_logger
from src.exporters.log_path import get_log_directory, get_temp_log_directory

# 模块日志记录器
logger = get_module_logger("structured_logger")

class StructuredLogger:
    """
    结构化日志记录器类
    
    提供高级日志记录功能，包括日志存储、查询和导出功能。
    支持结构化日志格式，确保日志数据可被高效分析。
    """
    
    def __init__(self, log_dir: Union[str, Path] = None, 
                 app_name: str = "visionai_clips_master",
                 enable_file_logging: bool = True):
        """
        初始化结构化日志记录器
        
        Args:
            log_dir: 日志文件目录（默认使用跨平台日志目录）
            app_name: 应用名称
            enable_file_logging: 是否启用文件日志记录
        """
        # 使用跨平台日志目录
        if log_dir is None:
            self.log_dir = get_log_directory() / "structured"
        else:
            self.log_dir = Path(log_dir)
            
        self.app_name = app_name
        self.enable_file_logging = enable_file_logging
        self.session_id = str(uuid.uuid4())
        self.start_time = datetime.datetime.now()
        
        # 创建会话目录
        if self.enable_file_logging:
            self._ensure_log_dir()
            
        # 系统信息
        self.system_info = self._collect_system_info()
        
        # 会话初始化日志
        self._log_session_start()
        
    def _ensure_log_dir(self) -> None:
        """确保日志目录存在"""
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        self.session_dir = self.log_dir / today / self.session_id
        self.session_dir.mkdir(parents=True, exist_ok=True)
        
        # 会话主日志文件
        self.main_log_file = self.session_dir / f"{self.app_name}.jsonl"
        
    def _collect_system_info(self) -> Dict[str, Any]:
        """收集系统信息"""
        try:
            memory = psutil.virtual_memory()
            return {
                "os": platform.system(),
                "os_version": platform.version(),
                "python_version": platform.python_version(),
                "cpu_count": psutil.cpu_count(logical=True),
                "total_memory_mb": round(memory.total / (1024 * 1024), 2),
                "hostname": platform.node()
            }
        except Exception as e:
            logger.error(f"收集系统信息时出错: {str(e)}")
            return {"error": str(e)}
            
    def _log_session_start(self) -> None:
        """记录会话开始日志"""
        session_log = {
            "timestamp": self.start_time.isoformat(),
            "operation": "init",
            "session_id": self.session_id,
            "system_info": self.system_info,
            "result": "success"
        }
        self.log("session_start", session_log)
            
    def log(self, event_type: str, data: Dict[str, Any]) -> bool:
        """
        记录结构化日志
        
        Args:
            event_type: 事件类型
            data: 日志数据
            
        Returns:
            日志记录是否成功
        """
        # 添加基本字段
        if "timestamp" not in data:
            data["timestamp"] = datetime.datetime.now().isoformat()
            
        if "session_id" not in data:
            data["session_id"] = self.session_id
            
        # 记录事件类型
        data["event_type"] = event_type
        
        try:
            # 验证日志格式
            validate_log(data, EXPORT_LOG_SCHEMA)
            
            # 掩码敏感数据
            masked_data = mask_sensitive_data(data, EXPORT_LOG_SCHEMA)
            
            # 写入文件
            if self.enable_file_logging:
                self._write_log_to_file(masked_data)
                
            return True
        except Exception as e:
            logger.error(f"记录日志失败: {str(e)}")
            return False
            
    def _write_log_to_file(self, data: Dict[str, Any]) -> None:
        """写入日志到文件"""
        try:
            with open(self.main_log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(data, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error(f"写入日志文件失败: {str(e)}")
            
    def log_operation(self, operation: str, result: str = "success", 
                     error: Optional[Dict[str, Any]] = None,
                     resource_usage: Optional[Dict[str, Any]] = None,
                     **kwargs) -> bool:
        """
        记录操作日志
        
        Args:
            operation: 操作类型
            result: 操作结果
            error: 错误信息
            resource_usage: 资源使用情况
            **kwargs: 其他字段
            
        Returns:
            日志记录是否成功
        """
        # 构建基本日志数据
        log_data = {
            "timestamp": datetime.datetime.now().isoformat(),
            "operation": operation,
            "result": result
        }
        
        # 添加资源使用情况
        if resource_usage is None:
            resource_usage = self._collect_resource_usage()
        log_data["resource_usage"] = resource_usage
        
        # 添加错误信息
        if error is not None:
            log_data["error"] = error
        
        # 添加其他字段
        for key, value in kwargs.items():
            log_data[key] = value
            
        return self.log(f"operation_{operation}", log_data)
        
    def _collect_resource_usage(self) -> Dict[str, float]:
        """收集资源使用情况"""
        try:
            process = psutil.Process(os.getpid())
            memory_mb = process.memory_info().rss / (1024 * 1024)
            cpu_percent = process.cpu_percent(interval=0.1)
            
            # 尝试获取GPU使用率，如果失败则设为0
            gpu_util = 0.0
            try:
                # 实际使用中，这里可能需要使用如 pynvml 等库获取 GPU 信息
                pass
            except:
                pass
                
            return {
                "memory_mb": round(memory_mb, 2),
                "cpu_percent": round(cpu_percent, 2),
                "gpu_util": round(gpu_util, 2)
            }
        except Exception as e:
            logger.error(f"收集资源使用情况失败: {str(e)}")
            return {
                "memory_mb": 0.0,
                "cpu_percent": 0.0,
                "gpu_util": 0.0
            }
            
    def log_video_processing(self, video_path: str, operation: str, stats: Dict[str, Any],
                           model_info: Optional[Dict[str, Any]] = None,
                           **kwargs) -> bool:
        """
        记录视频处理日志
        
        Args:
            video_path: 视频文件路径
            operation: 操作类型
            stats: 处理统计信息
            model_info: 模型信息
            **kwargs: 其他字段
            
        Returns:
            日志记录是否成功
        """
        # 构建视频处理日志
        log_data = {
            "timestamp": datetime.datetime.now().isoformat(),
            "operation": operation,
            "processing_stats": stats,
            "video_info": {
                "path": video_path
            }
        }
        
        # 添加模型信息
        if model_info:
            log_data["model_info"] = model_info
            
        # 添加其他字段
        for key, value in kwargs.items():
            log_data[key] = value
            
        return self.log(f"video_processing_{operation}", log_data)
    
    def performance_timer(self, operation: str, **kwargs) -> Callable:
        """
        性能计时装饰器
        
        Args:
            operation: 操作名称
            **kwargs: 其他日志字段
            
        Returns:
            装饰器函数
        """
        def decorator(func):
            def wrapper(*args, **func_kwargs):
                start_time = time.time()
                start_resource = self._collect_resource_usage()
                
                try:
                    result = func(*args, **func_kwargs)
                    success = True
                except Exception as e:
                    result = None
                    success = False
                    error = {
                        "code": type(e).__name__,
                        "message": str(e)
                    }
                    
                end_time = time.time()
                end_resource = self._collect_resource_usage()
                
                # 处理统计
                stats = {
                    "processing_time": round(end_time - start_time, 3),
                    "memory_delta_mb": round(end_resource["memory_mb"] - start_resource["memory_mb"], 2),
                    "cpu_avg": round((end_resource["cpu_percent"] + start_resource["cpu_percent"]) / 2, 2)
                }
                
                # 日志数据
                log_data = {
                    "timestamp": datetime.datetime.now().isoformat(),
                    "operation": operation,
                    "processing_stats": stats,
                    "resource_usage": end_resource,
                    "result": "success" if success else "error"
                }
                
                # 添加错误信息
                if not success:
                    log_data["error"] = error
                    
                # 添加其他字段
                for key, value in kwargs.items():
                    log_data[key] = value
                    
                # 记录日志
                self.log(f"performance_{operation}", log_data)
                
                if not success:
                    raise e
                    
                return result
            return wrapper
        return decorator
    
    def query_logs(self, event_type: Optional[str] = None, 
                  start_time: Optional[Union[str, datetime.datetime]] = None,
                  end_time: Optional[Union[str, datetime.datetime]] = None,
                  operation: Optional[str] = None,
                  result: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        查询日志
        
        Args:
            event_type: 事件类型
            start_time: 开始时间
            end_time: 结束时间
            operation: 操作类型
            result: 操作结果
            
        Returns:
            符合条件的日志列表
        """
        if not self.enable_file_logging:
            logger.warning("文件日志记录未启用，无法查询日志")
            return []
            
        # 转换时间格式
        if isinstance(start_time, datetime.datetime):
            start_time = start_time.isoformat()
        if isinstance(end_time, datetime.datetime):
            end_time = end_time.isoformat()
            
        results = []
        try:
            with open(self.main_log_file, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        log_entry = json.loads(line)
                        
                        # 应用过滤条件
                        if event_type and log_entry.get("event_type") != event_type:
                            continue
                            
                        log_time = log_entry.get("timestamp", "")
                        if start_time and log_time < start_time:
                            continue
                        if end_time and log_time > end_time:
                            continue
                            
                        if operation and log_entry.get("operation") != operation:
                            continue
                            
                        if result and log_entry.get("result") != result:
                            continue
                            
                        results.append(log_entry)
                    except:
                        continue
        except Exception as e:
            logger.error(f"查询日志失败: {str(e)}")
            
        return results
        
    def export_logs(self, output_path: Union[str, Path], 
                   format: str = "json",
                   **query_params) -> bool:
        """
        导出日志
        
        Args:
            output_path: 输出文件路径
            format: 输出格式（json, csv）
            **query_params: 查询参数
            
        Returns:
            导出是否成功
        """
        logs = self.query_logs(**query_params)
        
        if not logs:
            logger.warning("没有符合条件的日志可导出")
            return False
            
        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            if format.lower() == "json":
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(logs, f, ensure_ascii=False, indent=2)
            elif format.lower() == "csv":
                import csv
                
                # 获取所有字段
                fields = set()
                for log in logs:
                    fields.update(log.keys())
                fields = sorted(list(fields))
                
                with open(output_path, "w", encoding="utf-8", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=fields)
                    writer.writeheader()
                    writer.writerows(logs)
            else:
                logger.error(f"不支持的导出格式: {format}")
                return False
                
            return True
        except Exception as e:
            logger.error(f"导出日志失败: {str(e)}")
            return False
    
    def __del__(self):
        """析构函数，记录会话结束日志"""
        end_time = datetime.datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        session_end_log = {
            "timestamp": end_time.isoformat(),
            "operation": "shutdown",
            "session_id": self.session_id,
            "session_duration": round(duration, 2),
            "result": "success"
        }
        
        self.log("session_end", session_end_log)


# 全局日志记录器实例
_structured_logger = None

def get_structured_logger() -> StructuredLogger:
    """
    获取结构化日志记录器单例
    
    返回全局共享的结构化日志记录器实例，确保在整个应用中只有一个实例。
    
    Returns:
        StructuredLogger: 结构化日志记录器实例
    """
    global _structured_logger
    if _structured_logger is None:
        # 使用跨平台日志目录
        log_dir = get_log_directory() / "structured"
        _structured_logger = StructuredLogger(log_dir=log_dir)
    return _structured_logger


if __name__ == "__main__":
    # 测试代码
    logger = StructuredLogger(log_dir="logs/test_structured")
    
    # 记录操作日志
    logger.log_operation("clip", 
                        result="success",
                        video_info={
                            "duration": 120.5,
                            "resolution": "1920x1080",
                            "format": "mp4",
                            "frame_count": 3615
                        })
    
    # 性能计时装饰器测试
    @logger.performance_timer("test_function")
    def test_function():
        print("测试函数运行中...")
        time.sleep(1)
        return "测试完成"
        
    result = test_function()
    print(result)
    
    # 查询日志
    logs = logger.query_logs(operation="clip")
    print(f"查询到 {len(logs)} 条日志")
    
    # 导出日志
    success = logger.export_logs("logs/test_structured/export.json")
    print(f"导出日志{'成功' if success else '失败'}") 