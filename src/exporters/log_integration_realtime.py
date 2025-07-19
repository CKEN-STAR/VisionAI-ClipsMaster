#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
实时日志集成模块

将实时日志系统与结构化日志系统集成，提供统一的日志接口。
支持高性能实时日志记录，同时保持结构化日志的优势。
"""

import json
import time
import threading
import datetime
from typing import Dict, Any, List, Optional, Union, Callable, TypeVar, cast
from functools import wraps, update_wrapper

from src.exporters.log_writer import RealtimeLogger, get_realtime_logger
from src.exporters.structured_logger import get_structured_logger
from src.exporters.log_schema import validate_log, mask_sensitive_data, EXPORT_LOG_SCHEMA
from src.utils.logger import get_module_logger

# 模块日志记录器
logger = get_module_logger("log_integration_realtime")

# 类型变量
F = TypeVar('F', bound=Callable[..., Any])

class RealtimeLogIntegrator:
    """
    实时日志集成器
    
    将实时日志系统与结构化日志系统集成，提供统一的接口。
    """
    
    def __init__(self, enable_structured_logging: bool = True, 
                enable_realtime_logging: bool = True):
        """
        初始化实时日志集成器
        
        Args:
            enable_structured_logging: 是否启用结构化日志
            enable_realtime_logging: 是否启用实时日志
        """
        self.enable_structured_logging = enable_structured_logging
        self.enable_realtime_logging = enable_realtime_logging
        
        # 获取日志记录器实例
        if enable_structured_logging:
            self.structured_logger = get_structured_logger()
        else:
            self.structured_logger = None
            
        if enable_realtime_logging:
            self.realtime_logger = get_realtime_logger()
        else:
            self.realtime_logger = None
            
        # 性能统计
        self.stats = {
            "total_logs": 0,
            "structured_logs": 0,
            "realtime_logs": 0,
            "validation_errors": 0,
            "start_time": time.time()
        }
        
    def log(self, log_data: Dict[str, Any], validate: bool = True) -> bool:
        """
        记录日志
        
        Args:
            log_data: 日志数据
            validate: 是否验证日志格式
            
        Returns:
            是否成功记录
        """
        self.stats["total_logs"] += 1
        success = True
        
        # 添加时间戳（如果没有）
        if "timestamp" not in log_data:
            log_data["timestamp"] = datetime.datetime.now().isoformat()
            
        # 验证日志格式
        valid_log = True
        if validate:
            try:
                validate_log(log_data, EXPORT_LOG_SCHEMA)
            except ValueError as e:
                valid_log = False
                self.stats["validation_errors"] += 1
                logger.error(f"日志验证失败: {str(e)}")
                
        # 结构化日志
        if self.enable_structured_logging and valid_log:
            try:
                if hasattr(self.structured_logger, "log"):
                    # 使用通用log方法（如果存在）
                    event_type = log_data.get("event_type", "general")
                    self.structured_logger.log(event_type, log_data)
                elif hasattr(self.structured_logger, "log_operation"):
                    # 使用log_operation方法
                    operation = log_data.get("operation", "unknown")
                    result = log_data.get("result", "success")
                    self.structured_logger.log_operation(
                        operation=operation,
                        result=result,
                        **log_data
                    )
                self.stats["structured_logs"] += 1
            except Exception as e:
                success = False
                logger.error(f"结构化日志记录失败: {str(e)}")
                
        # 实时日志
        if self.enable_realtime_logging:
            try:
                # 掩码敏感数据
                if valid_log:
                    masked_data = mask_sensitive_data(log_data, EXPORT_LOG_SCHEMA)
                else:
                    masked_data = log_data
                    
                # 记录实时日志
                self.realtime_logger.log(masked_data)
                self.stats["realtime_logs"] += 1
            except Exception as e:
                success = False
                logger.error(f"实时日志记录失败: {str(e)}")
                
        return success
        
    def flush(self):
        """刷新所有日志记录器"""
        if self.realtime_logger:
            try:
                self.realtime_logger.flush()
            except Exception as e:
                logger.error(f"刷新实时日志失败: {str(e)}")
                
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = self.stats.copy()
        
        # 添加运行时间
        stats["uptime"] = time.time() - stats["start_time"]
        
        # 添加实时日志记录器统计（如果可用）
        if self.realtime_logger:
            rt_stats = self.realtime_logger.get_stats()
            for key, value in rt_stats.items():
                stats[f"realtime_{key}"] = value
                
        return stats
        
    def shutdown(self):
        """关闭日志集成器"""
        if self.realtime_logger:
            try:
                self.realtime_logger.shutdown()
            except Exception as e:
                logger.error(f"关闭实时日志记录器失败: {str(e)}")


# 实时日志记录装饰器
def realtime_log(event_type: str, **log_kwargs):
    """
    实时日志记录装饰器
    
    Args:
        event_type: 事件类型
        **log_kwargs: 其他日志字段
        
    Returns:
        装饰器函数
    """
    def decorator(func: F) -> F:
        integrator = RealtimeLogIntegrator()
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 函数开始时间
            start_time = time.time()
            result_status = "success"
            error_info = None
            
            try:
                # 执行原函数
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                # 记录异常信息
                result_status = "error"
                error_info = {
                    "code": type(e).__name__,
                    "message": str(e)
                }
                raise
            finally:
                # 函数执行时间
                execution_time = time.time() - start_time
                
                # 构建日志数据
                log_data = {
                    "timestamp": datetime.datetime.now().isoformat(),
                    "event_type": event_type,
                    "result": result_status,
                    "execution_time": round(execution_time, 3)
                }
                
                # 添加错误信息
                if error_info:
                    log_data["error"] = error_info
                    
                # 添加用户提供的额外数据
                for key, value in log_kwargs.items():
                    log_data[key] = value
                
                # 记录日志
                integrator.log(log_data)
                
        return cast(F, wrapper)
    
    return decorator


# 全局日志集成器
_log_integrator = None

def get_log_integrator() -> RealtimeLogIntegrator:
    """获取全局日志集成器实例"""
    global _log_integrator
    if _log_integrator is None:
        _log_integrator = RealtimeLogIntegrator()
    return _log_integrator


def log_realtime(log_data: Dict[str, Any], validate: bool = True) -> bool:
    """
    记录实时日志的便捷函数
    
    Args:
        log_data: 日志数据
        validate: 是否验证日志格式
        
    Returns:
        是否成功记录
    """
    integrator = get_log_integrator()
    return integrator.log(log_data, validate)


if __name__ == "__main__":
    # 测试代码
    import random
    
    # 创建日志集成器
    integrator = RealtimeLogIntegrator()
    
    # 测试直接记录日志
    for i in range(100):
        log_data = {
            "timestamp": datetime.datetime.now().isoformat(),
            "operation": random.choice(["read", "write", "process", "export"]),
            "result": random.choice(["success", "warning", "error"]),
            "resource_usage": {
                "memory_mb": random.uniform(100, 500),
                "cpu_percent": random.uniform(10, 80)
            },
            "message": f"测试日志消息 {i}"
        }
        integrator.log(log_data)
        
    # 测试装饰器
    @realtime_log("math_operation", category="test")
    def calculate(a, b):
        if random.random() < 0.2:
            raise ValueError("随机错误")
        return a + b
        
    for i in range(10):
        try:
            result = calculate(i, i * 2)
            print(f"计算结果: {result}")
        except Exception as e:
            print(f"计算错误: {e}")
            
    # 显示统计信息
    stats = integrator.get_stats()
    print("\n日志统计信息:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
        
    # 关闭日志集成器
    integrator.shutdown()
    print("日志集成器已关闭") 