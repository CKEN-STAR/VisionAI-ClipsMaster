# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 源代码包
"""

# 导入版本信息
try:
    from ..version import __version__, get_version, get_version_info
except ImportError:
    # 如果无法导入，使用默认版本
    __version__ = "1.0.1"

    def get_version():
        return __version__

    def get_version_info():
        return {"version": __version__}

__all__ = ["__version__", "get_version", "get_version_info"]
