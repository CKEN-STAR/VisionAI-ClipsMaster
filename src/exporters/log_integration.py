#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
日志集成模块

将结构化日志系统集成到应用程序的各个模块中。
提供装饰器和工具函数，方便在各处记录日志。
"""

import os
import sys
import time
import functools
import traceback
import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Callable, TypeVar, cast

from src.exporters.structured_logger import get_structured_logger, StructuredLogger
from src.exporters.log_analyzer import LogAnalyzer
from src.exporters.log_visualizer import LogVisualizer
from src.utils.logger import get_module_logger
from src.exporters.log_path import get_log_directory, get_log_file_path

# 模块日志记录器
logger = get_module_logger("log_integration")

# 类型变量，用于装饰器的类型提示
F = TypeVar('F', bound=Callable[..., Any])

# 获取全局结构化日志记录器实例
structured_logger = get_structured_logger()

def log_operation(operation: str, **kwargs) -> Callable[[F], F]:
    """
    操作日志装饰器
    
    Args:
        operation: 操作类型
        **kwargs: 其他日志字段
        
    Returns:
        装饰器函数
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **func_kwargs: Any) -> Any:
            # 函数开始时间
            start_time = time.time()
            result_status = "success"
            error_info = None
            
            try:
                # 执行原函数
                result = func(*args, **func_kwargs)
                return result
            except Exception as e:
                # 记录异常信息
                result_status = "error"
                error_info = {
                    "code": type(e).__name__,
                    "message": str(e),
                    "traceback": traceback.format_exc()
                }
                raise
            finally:
                # 函数执行时间
                execution_time = time.time() - start_time
                
                # 构建日志数据
                log_data = {
                    "processing_stats": {
                        "processing_time": round(execution_time, 3)
                    }
                }
                
                # 添加用户提供的额外数据
                for key, value in kwargs.items():
                    log_data[key] = value
                
                # 记录日志
                structured_logger.log_operation(
                    operation=operation,
                    result=result_status,
                    error=error_info,
                    **log_data
                )
                
        return cast(F, wrapper)
    return decorator

def log_video_process(operation: str, **kwargs) -> Callable[[F], F]:
    """
    视频处理日志装饰器
    
    Args:
        operation: 操作类型
        **kwargs: 其他日志字段
        
    Returns:
        装饰器函数
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **func_kwargs: Any) -> Any:
            # 尝试从参数中提取视频路径
            video_path = None
            
            # 查找视频路径参数
            for arg in args:
                if isinstance(arg, (str, Path)) and str(arg).lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
                    video_path = str(arg)
                    break
                    
            if video_path is None:
                # 查找关键字参数中的视频路径
                for param_name in ['video_path', 'input_path', 'source', 'video', 'file']:
                    if param_name in func_kwargs and isinstance(func_kwargs[param_name], (str, Path)):
                        path = str(func_kwargs[param_name])
                        if path.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
                            video_path = path
                            break
            
            # 函数开始时间
            start_time = time.time()
            result_status = "success"
            error_info = None
            
            # 初始化处理统计信息
            stats = {
                "processing_time": 0,
                "clips_created": 0,
                "total_duration": 0
            }
            
            try:
                # 执行原函数
                result = func(*args, **func_kwargs)
                
                # 尝试从结果中提取统计信息
                if isinstance(result, dict):
                    if "clips" in result and isinstance(result["clips"], list):
                        stats["clips_created"] = len(result["clips"])
                    
                    if "duration" in result:
                        stats["total_duration"] = float(result["duration"])
                        
                return result
            except Exception as e:
                # 记录异常信息
                result_status = "error"
                error_info = {
                    "code": type(e).__name__,
                    "message": str(e),
                    "traceback": traceback.format_exc()
                }
                raise
            finally:
                # 函数执行时间
                execution_time = time.time() - start_time
                stats["processing_time"] = round(execution_time, 3)
                
                # 添加模型信息（如果提供）
                model_info = kwargs.pop("model_info", None)
                
                # 如果没有视频路径，使用一个占位符
                if video_path is None:
                    video_path = "unknown_video"
                
                # 记录日志
                structured_logger.log_video_processing(
                    video_path=video_path,
                    operation=operation,
                    stats=stats,
                    model_info=model_info,
                    result=result_status,
                    error=error_info,
                    **kwargs
                )
                
        return cast(F, wrapper)
    return decorator

def log_error(error: Exception, operation: str, additional_info: Optional[Dict[str, Any]] = None) -> None:
    """
    记录错误日志
    
    Args:
        error: 异常对象
        operation: 操作类型
        additional_info: 附加信息
    """
    error_info = {
        "code": type(error).__name__,
        "message": str(error),
        "traceback": traceback.format_exc()
    }
    
    # 构建日志数据
    log_data = additional_info or {}
    
    # 记录日志
    structured_logger.log_operation(
        operation=operation,
        result="error",
        error=error_info,
        **log_data
    )

def log_model_usage(model_name: str, language: str, operation: str, 
                   parameters: Optional[Dict[str, Any]] = None, 
                   **kwargs) -> None:
    """
    记录模型使用日志
    
    Args:
        model_name: 模型名称
        language: 语言（zh 或 en）
        operation: 操作类型
        parameters: 模型参数
        **kwargs: 其他日志字段
    """
    # 构建模型信息
    model_info = {
        "name": model_name,
        "language": language,
        "parameters": parameters or {}
    }
    
    # 记录日志
    structured_logger.log_operation(
        operation=operation,
        model_info=model_info,
        **kwargs
    )

class LoggingManager:
    """
    日志管理器
    
    管理全局日志配置和提供便捷的日志分析与可视化方法。
    """
    
    def __init__(self, log_dir: Union[str, Path] = None,
                app_name: str = "visionai_clips_master"):
        """
        初始化日志管理器
        
        Args:
            log_dir: 日志目录（默认使用跨平台日志目录）
            app_name: 应用名称
        """
        # 使用跨平台日志目录
        if log_dir is None:
            self.log_dir = get_log_directory() / "structured"
        else:
            self.log_dir = Path(log_dir)
            
        self.app_name = app_name
        
        # 结构化日志记录器
        global structured_logger
        if structured_logger is None:
            structured_logger = StructuredLogger(log_dir=self.log_dir, app_name=self.app_name)
            
        # 日志分析器
        self.analyzer = LogAnalyzer(log_dir=self.log_dir)
        
        # 日志可视化器
        self.visualizer = LogVisualizer(log_dir=self.log_dir)
        
    def configure_logger(self, enable_file_logging: bool = True) -> None:
        """
        配置日志记录器
        
        Args:
            enable_file_logging: 是否启用文件日志记录
        """
        global structured_logger
        structured_logger = StructuredLogger(
            log_dir=self.log_dir,
            app_name=self.app_name,
            enable_file_logging=enable_file_logging
        )
        
    def generate_report(self, session_id: Optional[str] = None,
                      date: Optional[Union[str, datetime.date]] = None,
                      output_dir: Union[str, Path] = None) -> str:
        """
        生成日志报告
        
        Args:
            session_id: 会话ID
            date: 日期
            output_dir: 输出目录
            
        Returns:
            报告文件路径
        """
        # 使用跨平台日志目录
        if output_dir is None:
            output_dir = get_log_directory() / "reports"
        else:
            output_dir = Path(output_dir)
            
        # 确保目录存在
        output_dir.mkdir(parents=True, exist_ok=True)
        
        return self.analyzer.generate_report(
            session_id=session_id,
            date=date,
            output_dir=output_dir
        )
        
    def generate_dashboard(self, session_id: Optional[str] = None,
                         date: Optional[Union[str, datetime.date]] = None,
                         output_path: Union[str, Path] = None) -> str:
        """
        生成日志仪表盘
        
        Args:
            session_id: 会话ID
            date: 日期
            output_path: 输出文件路径
            
        Returns:
            仪表盘文件路径
        """
        # 使用跨平台日志目录
        if output_path is None:
            output_dir = get_log_directory() / "dashboard"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / "dashboard.html"
        else:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
        return self.visualizer.generate_dashboard(
            session_id=session_id,
            date=date,
            output_path=output_path
        )
        
    def export_logs(self, output_path: Union[str, Path] = None,
                   format: str = "json",
                   session_id: Optional[str] = None,
                   date: Optional[Union[str, datetime.date]] = None) -> bool:
        """
        导出日志
        
        Args:
            output_path: 输出文件路径
            format: 输出格式 (json, csv)
            session_id: 会话ID
            date: 日期
            
        Returns:
            是否成功导出
        """
        # 使用跨平台日志目录
        if output_path is None:
            output_dir = get_log_directory() / "export"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = output_dir / f"logs_export_{timestamp}.{format}"
        else:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
        return structured_logger.export_logs(
            output_path=output_path,
            format=format,
            session_id=session_id,
            date=date
        )

# 全局日志管理器实例
_global_manager = None

def get_logging_manager() -> LoggingManager:
    """获取全局日志管理器实例"""
    global _global_manager
    if _global_manager is None:
        _global_manager = LoggingManager()
    return _global_manager


if __name__ == "__main__":
    # 测试代码
    
    # 使用操作日志装饰器
    @log_operation("test_operation", test_param="test_value")
    def test_function(a, b):
        print(f"测试函数: {a} + {b} = {a + b}")
        return a + b
        
    # 使用视频处理日志装饰器
    @log_video_process("test_video_process", video_info={"format": "mp4", "resolution": "1920x1080"})
    def process_video(video_path):
        print(f"处理视频: {video_path}")
        time.sleep(1)  # 模拟处理
        return {
            "clips": ["clip1.mp4", "clip2.mp4"],
            "duration": 60.5
        }
        
    # 测试函数调用
    result = test_function(1, 2)
    print(f"结果: {result}")
    
    # 测试视频处理
    process_result = process_video("test_video.mp4")
    print(f"处理结果: {process_result}")
    
    # 测试错误日志
    try:
        1 / 0
    except Exception as e:
        log_error(e, "division", {"value": 0})
        
    # 测试模型使用日志
    log_model_usage(
        model_name="Qwen2.5-7B",
        language="zh",
        operation="text_generation",
        parameters={
            "temperature": 0.7,
            "top_p": 0.9
        }
    )
    
    # 测试日志管理器
    manager = get_logging_manager()
    
    # 生成报告
    report_path = manager.generate_report()
    if report_path:
        print(f"报告已生成: {report_path}")
        
    # 生成仪表板
    dashboard_path = manager.generate_dashboard()
    if dashboard_path:
        print(f"仪表板已生成: {dashboard_path}") 