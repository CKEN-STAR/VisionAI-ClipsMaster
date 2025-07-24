#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
UI兼容性模块
处理不同Qt版本的兼容性问题
"""

import sys

def handle_qt_version():
    """处理Qt版本兼容性"""
    try:
        import PyQt6
        return "PyQt6"
    except ImportError:
        try:
            import PyQt5
            return "PyQt5"
        except ImportError:
            return None

def setup_compat():
    """设置兼容性环境"""
    qt_version = handle_qt_version()
    if qt_version:
        print(f"[OK] 检测到 {qt_version}")
        return True
    else:
        print("[ERROR] 未检测到可用的Qt版本")
        return False

def get_qt_version_str():
    """获取Qt版本字符串"""
    qt_version = handle_qt_version()
    return qt_version or "Unknown"
