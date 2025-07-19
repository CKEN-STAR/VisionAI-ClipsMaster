"""
UI组件模块
提供各种UI组件和管理器
"""

__version__ = "1.0.0"

# 导入组件模块
try:
    from .alert_manager import *
except ImportError as e:
    print(f"[WARN] UI组件模块导入警告: {e}")

__all__ = [
    'alert_manager'
]
