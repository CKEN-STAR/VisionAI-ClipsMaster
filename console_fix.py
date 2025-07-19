#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
控制台中文编码修复
"""
import sys
import os
import ctypes
import io

def fix_console_encoding():
    """修复Windows控制台中文编码问题"""
    if sys.platform.startswith('win'):
        # 修改控制台代码页为UTF-8
        os.system('chcp 65001 > nul')
        
        # 使用Windows API设置控制台代码页
        try:
            k32 = ctypes.windll.kernel32
            k32.SetConsoleCP(65001)
            k32.SetConsoleOutputCP(65001)
            print("已设置Windows控制台代码页为UTF-8 (CP65001)")
        except Exception as e:
            print(f"设置控制台代码页失败: {e}")
    
    # 重定向标准输出流为UTF-8
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    
    # 设置环境变量
    os.environ["PYTHONIOENCODING"] = "utf-8"
    os.environ["LC_ALL"] = "zh_CN.UTF-8"
    os.environ["LANG"] = "zh_CN.UTF-8"
    
    print("控制台编码已修复，现在可以正常显示中文: 测试中文显示")

# 自动运行
if __name__ == "__main__":
    fix_console_encoding() 