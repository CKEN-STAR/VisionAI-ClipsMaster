"""
UI修复模块
提供各种UI相关的修复和优化功能
"""

__version__ = "1.0.0"

# 导入修复模块
try:
    from .integrated_fix import *
except ImportError as e:
    print(f"[WARN] UI修复模块导入警告: {e}")

__all__ = ['integrated_fix']
