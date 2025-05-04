"""
版本管理模块

提供模型和模式的版本管理功能，支持版本切换、比较和追踪。
"""

from .pattern_version_manager import (
    PatternVersionManager,
    get_latest_version,
    get_available_versions,
    set_current_version,
    get_version_metadata
) 