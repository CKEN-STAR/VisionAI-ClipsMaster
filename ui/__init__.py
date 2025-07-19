"""
VisionAI-ClipsMaster UI模块
提供用户界面相关的功能和组件
"""

__version__ = "1.0.0"
__author__ = "VisionAI-ClipsMaster Team"

# 导入主要的UI组件
try:
    from .components import *
    from .utils import *
    from .config import *
    from .hardware import *
    from .fixes import *
    from .feedback import *
    from .optimize import *
    from .progress import *
    from .monitor import *
    from .responsive import *
    from .performance import *
except ImportError as e:
    # 在开发阶段，某些模块可能还未实现
    print(f"[WARN] UI模块导入警告: {e}")

__all__ = [
    'components',
    'utils', 
    'config',
    'hardware',
    'fixes',
    'feedback',
    'optimize',
    'progress',
    'monitor',
    'responsive',
    'performance'
]
