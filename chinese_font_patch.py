#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
中文字体补丁 - 自动注入到PyQt中
"""
import sys
import os
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QTextEdit, QMainWindow
from PyQt5.QtGui import QFont, QFontDatabase, QPainter, QFontMetrics, QPalette
from PyQt5.QtCore import Qt

# 保存原始类
_OrigQWidget = QWidget
_OrigQLabel = QLabel
_OrigQPushButton = QPushButton
_OrigQTextEdit = QTextEdit
_OrigQMainWindow = QMainWindow

# 创建中文字体
def create_chinese_font():
    font = QFont("Microsoft YaHei UI", 12)
    font.setHintingPreference(QFont.PreferFullHinting)
    font.setStyleStrategy(QFont.PreferAntialias)
    return font

# 替换QWidget类
class ChineseQWidget(_OrigQWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFont(create_chinese_font())

# 替换QLabel类
class ChineseQLabel(_OrigQLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFont(create_chinese_font())
        
    def paintEvent(self, event):
        # 检查是否包含中文字符
        if any(ord(c) > 127 for c in self.text()):
            painter = QPainter(self)
            painter.setFont(self.font())
            painter.setPen(self.palette().color(QPalette.WindowText))
            painter.drawText(self.rect(), self.alignment(), self.text())
            painter.end()
        else:
            super().paintEvent(event)

# 替换QPushButton类
class ChineseQPushButton(_OrigQPushButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFont(create_chinese_font())

# 替换QTextEdit类
class ChineseQTextEdit(_OrigQTextEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFont(create_chinese_font())

# 替换QMainWindow类
class ChineseQMainWindow(_OrigQMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFont(create_chinese_font())

# 应用补丁
def apply_patch():
    # 替换类
    sys.modules['PyQt5.QtWidgets'].QWidget = ChineseQWidget
    sys.modules['PyQt5.QtWidgets'].QLabel = ChineseQLabel
    sys.modules['PyQt5.QtWidgets'].QPushButton = ChineseQPushButton
    sys.modules['PyQt5.QtWidgets'].QTextEdit = ChineseQTextEdit
    sys.modules['PyQt5.QtWidgets'].QMainWindow = ChineseQMainWindow
    
    # 设置全局字体
    app = QApplication.instance()
    if app:
        app.setFont(create_chinese_font())
    
    print("已应用中文字体补丁: Microsoft YaHei UI")

# 自动应用补丁
apply_patch()
