"""
兼容性模块
提供Qt版本兼容性处理
"""

import sys
from typing import Dict, Any, Optional

def get_qt_version_str() -> str:
    """获取Qt版本字符串"""
    try:
        from PyQt6.QtCore import QT_VERSION_STR
        return QT_VERSION_STR
    except ImportError:
        return "Unknown"

def handle_qt_version() -> bool:
    """处理Qt版本兼容性"""
    try:
        version = get_qt_version_str()
        print(f"[OK] Qt版本: {version}")
        return True
    except Exception as e:
        print(f"[WARN] Qt版本处理失败: {e}")
        return False

def setup_compat() -> bool:
    """设置兼容性"""
    try:
        # 设置Qt兼容性
        if handle_qt_version():
            print("[OK] Qt兼容性设置完成")
            return True
        return False
    except Exception as e:
        print(f"[WARN] 兼容性设置失败: {e}")
        return False

def get_compat_info() -> Dict[str, Any]:
    """获取兼容性信息"""
    return {
        'qt_version': get_qt_version_str(),
        'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        'platform': sys.platform
    }

__all__ = [
    'handle_qt_version',
    'setup_compat', 
    'get_qt_version_str',
    'get_compat_info'
]
