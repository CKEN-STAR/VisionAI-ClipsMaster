#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
中文显示自动修复 wrapper
"""
import sys
import os
import ctypes

# 设置控制台编码
if sys.platform.startswith('win'):
    try:
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleCP(65001)
        kernel32.SetConsoleOutputCP(65001)
    except:
        pass
    os.system('chcp 65001 > nul')

# 设置环境变量
os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["PYTHONLEGACYWINDOWSSTDIO"] = "utf-8"
os.environ["LANG"] = "zh_CN.UTF-8"
os.environ["LC_ALL"] = "zh_CN.UTF-8"
os.environ["NLS_LANG"] = "SIMPLIFIED CHINESE_CHINA.UTF8"

# 初始化Qt设置
os.environ["QT_SCALE_FACTOR"] = "1"
os.environ["QT_FONT_DPI"] = "96"

# 修改字体渲染
def patch_qt():
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtGui import QFont, QFontDatabase
    
    # 查找中文字体
    font_db = QFontDatabase()
    families = font_db.families()
    
    # 中文字体优先级
    priority = ["Microsoft YaHei UI", "Microsoft YaHei", "微软雅黑", "SimHei", "黑体"]
    
    # 查找第一个可用的中文字体
    chinese_font = None
    for name in priority:
        for font in families:
            if name in font:
                chinese_font = QFont(font, 12)
                chinese_font.setHintingPreference(QFont.PreferFullHinting)
                break
        if chinese_font:
            break
            
    # 如果未找到，使用默认字体
    if not chinese_font:
        chinese_font = QFont("MS Shell Dlg 2", 12)
    
    # 设置全局字体
    app = QApplication.instance()
    if app:
        app.setFont(chinese_font)
    
    print(f"使用中文字体: {chinese_font.family()}")

# 这个函数会在导入时自动执行
patch_qt()

# 执行主程序
import simple_ui
simple_ui.main()
