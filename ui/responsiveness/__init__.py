"""
响应性优化模块
提供超快响应时间优化和用户交互体验提升
"""

from .ultra_fast_response import (
    ResponseTimeOptimizer,
    UltraFastResponseManager,
    get_response_manager,
    optimize_widget_response,
    start_timing,
    end_timing
)

__all__ = [
    'ResponseTimeOptimizer',
    'UltraFastResponseManager',
    'get_response_manager',
    'optimize_widget_response',
    'start_timing',
    'end_timing'
]
