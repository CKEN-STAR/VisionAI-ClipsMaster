#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
日志脱敏集成模块

将日志脱敏功能与实时日志和结构化日志系统集成。
确保所有日志在写入前都经过敏感信息检测和脱敏处理。
提供简便的接口进行安全日志记录。
"""

import time
import datetime
from typing import Dict, Any, List, Optional, Union, Callable, TypeVar, cast
from functools import wraps

from src.exporters.log_sanitizer import sanitize_log_entry, is_sensitive_data, add_sensitive_pattern
from src.exporters.log_writer import get_realtime_logger
from src.exporters.structured_logger import get_structured_logger
from src.exporters.log_integration_realtime import get_log_integrator
from src.utils.logger import get_module_logger

# 模块日志记录器
logger = get_module_logger("log_integration_sanitized")

# 类型变量
F = TypeVar('F', bound=Callable[..., Any])

class SanitizedLogger:
    """
    脱敏日志记录器
    
    提供自动脱敏的日志记录功能，同时支持实时日志和结构化日志。
    """
    
    def __init__(self, enable_sanitization: bool = True,
                enable_warnings: bool = True,
                replacement: str = "[REDACTED]"):
        """
        初始化脱敏日志记录器
        
        Args:
            enable_sanitization: 是否启用脱敏
            enable_warnings: 是否在检测到敏感信息时发出警告
            replacement: 替换敏感信息的字符串
        """
        self.enable_sanitization = enable_sanitization
        self.enable_warnings = enable_warnings
        self.replacement = replacement
        
        # 获取日志集成器
        self.integrator = get_log_integrator()
        
        # 统计信息
        self.stats = {
            "total_logs": 0,
            "sanitized_logs": 0,
            "sensitive_data_detected": 0,
            "start_time": time.time()
        }
        
    def log(self, log_data: Dict[str, Any], validate: bool = True) -> bool:
        """
        记录脱敏后的日志
        
        Args:
            log_data: 日志数据
            validate: 是否验证日志格式
            
        Returns:
            是否成功记录
        """
        self.stats["total_logs"] += 1
        
        # 检测敏感信息
        contains_sensitive = is_sensitive_data(log_data)
        if contains_sensitive:
            self.stats["sensitive_data_detected"] += 1
            
            if self.enable_warnings:
                logger.warning("检测到日志中包含敏感信息，将进行脱敏处理")
        
        # 脱敏处理
        if self.enable_sanitization:
            sanitized_data = sanitize_log_entry(log_data, self.replacement)
            self.stats["sanitized_logs"] += 1
        else:
            sanitized_data = log_data
            
        # 使用集成器记录日志
        return self.integrator.log(sanitized_data, validate)
    
    def log_operation(self, operation: str, result: str = "success", 
                    error: Optional[Dict[str, Any]] = None,
                    **kwargs) -> bool:
        """
        记录操作日志（自动脱敏）
        
        Args:
            operation: 操作类型
            result: 操作结果
            error: 错误信息
            **kwargs: 其他字段
            
        Returns:
            是否成功记录
        """
        log_data = {
            "timestamp": datetime.datetime.now().isoformat(),
            "operation": operation,
            "result": result
        }
        
        # 添加错误信息
        if error is not None:
            log_data["error"] = error
            
        # 添加其他字段
        for key, value in kwargs.items():
            log_data[key] = value
            
        # 记录脱敏日志
        return self.log(log_data)
        
    def flush(self) -> None:
        """刷新日志记录器"""
        self.integrator.flush()
        
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = self.stats.copy()
        
        # 添加运行时间
        stats["uptime"] = time.time() - stats["start_time"]
        
        # 添加集成器统计
        integrator_stats = self.integrator.get_stats()
        for key, value in integrator_stats.items():
            stats[f"integrator_{key}"] = value
            
        return stats
        
    def shutdown(self) -> None:
        """关闭日志记录器"""
        self.integrator.shutdown()

# 脱敏日志装饰器
def log_sanitized(event_type: str, **log_kwargs):
    """
    脱敏日志记录装饰器
    
    Args:
        event_type: 事件类型
        **log_kwargs: 其他日志字段
        
    Returns:
        装饰器函数
    """
    def decorator(func: F) -> F:
        logger = SanitizedLogger()
        
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
                
                # 记录日志（自动脱敏）
                logger.log(log_data)
                
        return cast(F, wrapper)
    
    return decorator

# 全局脱敏日志记录器
_sanitized_logger = None

def get_sanitized_logger() -> SanitizedLogger:
    """获取全局脱敏日志记录器实例"""
    global _sanitized_logger
    if _sanitized_logger is None:
        _sanitized_logger = SanitizedLogger()
    return _sanitized_logger

def log_safe(log_data: Dict[str, Any], validate: bool = True) -> bool:
    """
    安全记录日志的便捷函数（自动脱敏）
    
    Args:
        log_data: 日志数据
        validate: 是否验证日志格式
        
    Returns:
        是否成功记录
    """
    logger = get_sanitized_logger()
    return logger.log(log_data, validate)

if __name__ == "__main__":
    # 测试代码
    import random
    
    # 创建脱敏日志记录器
    sanitized_logger = get_sanitized_logger()
    
    # 测试记录包含敏感信息的日志
    sensitive_log = {
        "user": "张三",
        "message": "我的银行卡号是6222020903001483077，请帮我查询余额",
        "card_info": {
            "card_number": "4111 1111 1111 1111",
            "expiry": "12/25",
            "cvv": "123"
        },
        "operation": "query_balance",
        "result": "success"
    }
    
    print("记录包含敏感信息的日志...")
    sanitized_logger.log(sensitive_log)
    
    # 测试装饰器
    @log_sanitized("payment_operation", service="payment")
    def process_payment(user_id, amount, card_number):
        print(f"处理支付: 用户ID {user_id}, 金额 {amount}, 卡号 {card_number}")
        if random.random() < 0.2:
            raise ValueError("支付处理失败")
        return {"transaction_id": f"TXN-{random.randint(10000, 99999)}"}
    
    try:
        result = process_payment("user123", 100.50, "4111 1111 1111 1111")
        print(f"支付结果: {result}")
    except Exception as e:
        print(f"支付出错: {e}")
    
    # 显示统计信息
    stats = sanitized_logger.get_stats()
    print("\n日志统计信息:")
    for key, value in stats.items():
        if isinstance(value, float) and key not in ["start_time", "integrator_start_time"]:
            print(f"  {key}: {value:.2f}")
        else:
            print(f"  {key}: {value}")
    
    # 关闭日志记录器
    sanitized_logger.shutdown()
    print("日志记录器已关闭") 