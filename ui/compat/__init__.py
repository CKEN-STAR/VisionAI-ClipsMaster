#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI兼容性模块
处理PyQt6相关的兼容性问题
"""

import sys
import os

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
    # 设置编码
    if hasattr(sys, 'setdefaultencoding'):
        sys.setdefaultencoding('utf-8')
    
    # Windows特殊处理
    if os.name == 'nt':
        os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '1'
        os.environ['QT_SCALE_FACTOR'] = '1'
        os.environ['QT_FONT_DPI'] = '96'

def get_qt_version_str():
    """获取Qt版本字符串"""
    qt_version = handle_qt_version()
    if qt_version:
        try:
            if qt_version == "PyQt6":
                from PyQt6.QtCore import QT_VERSION_STR
                return f"PyQt6 (Qt {QT_VERSION_STR})"
            elif qt_version == "PyQt5":
                from PyQt5.QtCore import QT_VERSION_STR
                return f"PyQt5 (Qt {QT_VERSION_STR})"
        except:
            return qt_version
    else:
        return "Qt未安装"

# 自动设置
setup_compat()
