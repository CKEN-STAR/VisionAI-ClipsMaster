"""
UI反馈模块
提供用户反馈和错误可视化功能
"""

__version__ = "1.0.0"

# 导入反馈模块
try:
    from .error_visualizer import *
except ImportError as e:
    print(f"[WARN] UI反馈模块导入警告: {e}")

__all__ = [
    'error_visualizer'
]
