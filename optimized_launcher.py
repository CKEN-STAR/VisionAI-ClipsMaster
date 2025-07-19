#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 优化启动脚本
"""

import os
import sys
import gc
from pathlib import Path

def optimize_startup():
    """优化启动过程"""
    # 设置垃圾回收阈值
    gc.set_threshold(700, 10, 10)
    
    # 设置环境变量
    os.environ['PYTHONOPTIMIZE'] = '1'
    os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
    
    # 预编译正则表达式
    import re
    re.compile(r'\d+')  # 预编译常用正则
    
    print("🚀 启动优化完成")

def main():
    """主启动函数"""
    optimize_startup()
    
    # 导入主应用
    try:
        from simple_ui_fixed import main as ui_main
        ui_main()
    except ImportError:
        print("❌ 无法导入UI模块")
        sys.exit(1)

if __name__ == "__main__":
    main()
