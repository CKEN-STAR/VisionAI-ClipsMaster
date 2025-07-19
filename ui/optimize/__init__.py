"""
UI优化模块
提供UI性能优化功能
"""

__version__ = "1.0.0"

# 导入优化模块
try:
    from .panel_perf import *
except ImportError as e:
    print(f"[WARN] UI优化模块导入警告: {e}")

__all__ = [
    'panel_perf'
]
