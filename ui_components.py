#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster UI组件工厂
专门处理中文UI元素的创建和显示
"""
import sys
from PyQt5.QtWidgets import (
    QLabel, QPushButton, QTextEdit, QLineEdit, QComboBox,
    QGroupBox, QTabWidget, QCheckBox, QRadioButton
)
from PyQt5.QtGui import QFont, QPalette, QColor
from PyQt5.QtCore import Qt

# 创建默认的中文字体
def create_chinese_font(size=12, bold=False):
    """创建中文字体对象
    
    Args:
        size: 字体大小
        bold: 是否粗体
    
    Returns:
        QFont: 中文字体对象
    """
    # 字体优先级
    font_families = ["Microsoft YaHei UI", "微软雅黑", "SimHei", "黑体", "SimSun", "宋体"]
    
    for family in font_families:
        font = QFont(family, size)
        if font.exactMatch():
            if bold:
                font.setBold(True)
            font.setHintingPreference(QFont.PreferFullHinting)
            font.setStyleStrategy(QFont.PreferAntialias)
            return font
    
    # 如果没有匹配的字体，使用系统默认字体
    font = QFont("", size)
    if bold:
        font.setBold(True)
    return font

# 创建标签
def create_label(text, size=12, bold=False, alignment=None):
    """创建中文标签
    
    Args:
        text: 标签文本
        size: 字体大小
        bold: 是否粗体
        alignment: 对齐方式
    
    Returns:
        QLabel: 标签对象
    """
    label = QLabel(text)
    font = create_chinese_font(size, bold)
    label.setFont(font)
    
    if alignment:
        label.setAlignment(alignment)
    
    # 确保使用原生字体渲染
    label.setTextFormat(Qt.TextFormat.PlainText)
    return label

# 创建按钮
def create_button(text, size=12, bold=False, min_height=None):
    """创建中文按钮
    
    Args:
        text: 按钮文本
        size: 字体大小
        bold: 是否粗体
        min_height: 最小高度
    
    Returns:
        QPushButton: 按钮对象
    """
    button = QPushButton(text)
    font = create_chinese_font(size, bold)
    button.setFont(font)
    
    if min_height:
        button.setMinimumHeight(min_height)
    
    return button

# 创建文本编辑框
def create_text_edit(placeholder_text=None, size=12, read_only=False):
    """创建中文文本编辑框
    
    Args:
        placeholder_text: 占位文本
        size: 字体大小
        read_only: 是否只读
    
    Returns:
        QTextEdit: 文本编辑框对象
    """
    text_edit = QTextEdit()
    font = create_chinese_font(size)
    text_edit.setFont(font)
    
    if placeholder_text:
        text_edit.setPlaceholderText(placeholder_text)
    
    if read_only:
        text_edit.setReadOnly(True)
    
    return text_edit

# 创建单行编辑框
def create_line_edit(placeholder_text=None, size=12):
    """创建中文单行编辑框
    
    Args:
        placeholder_text: 占位文本
        size: 字体大小
    
    Returns:
        QLineEdit: 单行编辑框对象
    """
    line_edit = QLineEdit()
    font = create_chinese_font(size)
    line_edit.setFont(font)
    
    if placeholder_text:
        line_edit.setPlaceholderText(placeholder_text)
    
    return line_edit

# 创建下拉框
def create_combo_box(items=None, size=12):
    """创建中文下拉框
    
    Args:
        items: 下拉项列表
        size: 字体大小
    
    Returns:
        QComboBox: 下拉框对象
    """
    combo_box = QComboBox()
    font = create_chinese_font(size)
    combo_box.setFont(font)
    
    if items:
        for item in items:
            combo_box.addItem(item)
    
    return combo_box

# 创建分组框
def create_group_box(title, size=12, bold=True):
    """创建中文分组框
    
    Args:
        title: 标题
        size: 字体大小
        bold: 是否粗体
    
    Returns:
        QGroupBox: 分组框对象
    """
    group_box = QGroupBox(title)
    font = create_chinese_font(size, bold)
    group_box.setFont(font)
    
    return group_box

# 创建标签页组件
def create_tab_widget(size=12):
    """创建中文标签页组件
    
    Args:
        size: 字体大小
    
    Returns:
        QTabWidget: 标签页组件
    """
    tab_widget = QTabWidget()
    font = create_chinese_font(size)
    tab_widget.setFont(font)
    
    return tab_widget

# 创建复选框
def create_check_box(text, size=12, checked=False):
    """创建中文复选框
    
    Args:
        text: 文本
        size: 字体大小
        checked: 是否选中
    
    Returns:
        QCheckBox: 复选框对象
    """
    check_box = QCheckBox(text)
    font = create_chinese_font(size)
    check_box.setFont(font)
    check_box.setChecked(checked)
    
    return check_box

# 创建单选按钮
def create_radio_button(text, size=12, checked=False):
    """创建中文单选按钮
    
    Args:
        text: 文本
        size: 字体大小
        checked: 是否选中
    
    Returns:
        QRadioButton: 单选按钮对象
    """
    radio_button = QRadioButton(text)
    font = create_chinese_font(size)
    radio_button.setFont(font)
    radio_button.setChecked(checked)
    
    return radio_button

# 设置全局样式表
def apply_chinese_style_sheet(app):
    """应用中文样式表
    
    Args:
        app: QApplication对象
    """
    style_sheet = """
    * {
        font-family: "Microsoft YaHei UI", "微软雅黑", "SimHei", "黑体";
    }
    QLabel {
        color: #000000;
    }
    QPushButton {
        padding: 5px 10px;
        background-color: #f0f0f0;
        border: 1px solid #c0c0c0;
        border-radius: 3px;
    }
    QGroupBox {
        font-weight: bold;
        border: 1px solid #c0c0c0;
        border-radius: 5px;
        margin-top: 10px;
        padding-top: 15px;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 10px;
        padding: 0 5px;
    }
    QTabWidget::tab-bar {
        alignment: center;
    }
    QTabBar::tab {
        background-color: #f0f0f0;
        border: 1px solid #c0c0c0;
        border-bottom: none;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
        min-width: 100px;
        padding: 5px 10px;
    }
    QTabBar::tab:selected {
        background-color: #ffffff;
        border-bottom: 1px solid #ffffff;
    }
    """
    
    app.setStyleSheet(style_sheet)

# 设置中文环境
def setup_chinese_environment():
    """设置中文环境，包括编码和字体"""
    import os
    
    # 设置环境变量
    os.environ["PYTHONIOENCODING"] = "utf-8"
    os.environ["LANG"] = "zh_CN.UTF-8"
    os.environ["LC_ALL"] = "zh_CN.UTF-8"
    
    # 设置控制台编码
    if sys.platform.startswith('win'):
        import codecs
        import locale
        
        # 设置控制台代码页
        os.system("chcp 65001 > nul")
        
        # 设置Windows API
        try:
            import ctypes
            k32 = ctypes.windll.kernel32
            k32.SetConsoleCP(65001)
            k32.SetConsoleOutputCP(65001)
        except:
            pass
        
        # 设置标准输出
        try:
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
            sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
        except:
            pass
        
        # 设置区域
        try:
            locale.setlocale(locale.LC_ALL, 'zh_CN.UTF-8')
        except:
            try:
                locale.setlocale(locale.LC_ALL, 'Chinese_China.936')
            except:
                pass 