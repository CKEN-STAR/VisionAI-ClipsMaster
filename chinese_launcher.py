#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 中文版启动器
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
        os.system('chcp 65001 > nul')
    except:
        pass

# 设置环境变量
os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["PYTHONLEGACYWINDOWSSTDIO"] = "utf-8"
os.environ["LANG"] = "zh_CN.UTF-8"
os.environ["LC_ALL"] = "zh_CN.UTF-8"
os.environ["NLS_LANG"] = "SIMPLIFIED CHINESE_CHINA.UTF8"

# Qt环境变量
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
os.environ["QT_FONT_DPI"] = "96"

# 导入中文字体补丁
print("正在加载中文字体补丁...")
import qt_chinese_patch

# 启动主程序
print("正在启动主程序...")
from simple_ui import main
main()
