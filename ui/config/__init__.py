"""
UI配置模块
提供UI相关的配置和环境设置
"""

__version__ = "1.0.0"

# 导入配置模块
try:
    from .recursion_fix import *
    from .environment import *
except ImportError as e:
    print(f"[WARN] UI配置模块导入警告: {e}")

__all__ = [
    'recursion_fix',
    'environment'
]
