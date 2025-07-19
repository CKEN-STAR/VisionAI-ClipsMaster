"""
UI响应式模块
提供响应式设计和适配功能
"""

__version__ = "1.0.0"

# 导入响应式模块
try:
    from .simple_ui_adapter import *
except ImportError as e:
    print(f"[WARN] UI响应式模块导入警告: {e}")

__all__ = [
    'simple_ui_adapter'
]
