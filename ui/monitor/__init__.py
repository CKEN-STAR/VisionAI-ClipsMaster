"""
UI监控模块
提供系统监控和配置功能
"""

__version__ = "1.0.0"

# 导入监控模块
try:
    from .system_monitor_app import *
    from .config_loader import *
except ImportError as e:
    print(f"[WARN] UI监控模块导入警告: {e}")

__all__ = [
    'system_monitor_app',
    'config_loader'
]
