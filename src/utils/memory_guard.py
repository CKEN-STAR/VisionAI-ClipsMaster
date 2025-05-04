#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
内存监控模块 - 简化版（UI演示用）
"""

import functools
from typing import Any, Callable

def track_memory(operation_name: str):
    """内存追踪装饰器 - 简化版（UI演示用）"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # 简化版装饰器，直接调用函数
            return func(*args, **kwargs)
        return wrapper
    return decorator
