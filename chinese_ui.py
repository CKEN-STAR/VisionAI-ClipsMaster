#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
中文UI启动解决方案
"""
import sys
import os
import subprocess
import locale

# 设置Python环境变量
os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["LANG"] = "zh_CN.UTF-8"
os.environ["LC_ALL"] = "zh_CN.UTF-8"
os.environ["NLS_LANG"] = "SIMPLIFIED CHINESE_CHINA.UTF8"

# 设置PyQt环境变量，确保正确渲染中文
os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = os.path.join(sys.prefix, 'Lib', 'site-packages', 'PyQt5', 'Qt5', 'plugins', 'platforms')
os.environ["QT_QPA_PLATFORM"] = "windows"
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
os.environ["QT_SCALE_FACTOR"] = "1"
os.environ["QT_FONT_DPI"] = "96"

if __name__ == "__main__":
    # 设置控制台编码
    if sys.platform.startswith('win'):
        # 修改控制台代码页为UTF-8
        os.system("chcp 65001 > nul")
        
    print("正在启动VisionAI-ClipsMaster中文界面...")
    
    # 显示系统中可用的字体，帮助调试
    try:
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtGui import QFontDatabase
        app = QApplication([])
        fontdb = QFontDatabase()
        available_fonts = fontdb.families()
        print(f"系统中可用的中文字体: {[f for f in available_fonts if '微软雅黑' in f or 'SimSun' in f or 'SimHei' in f]}")
        del app
    except Exception as e:
        print(f"无法列出可用的字体: {e}")
    
    # 执行原始脚本
    from simple_ui import main
    main() 