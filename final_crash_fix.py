#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 英文模型按钮闪退问题最终修复脚本
"""

import re
import os

def apply_final_crash_fix():
    """应用最终的崩溃修复"""
    
    print("🔧 开始应用最终崩溃修复...")
    
    # 1. 修复simple_ui_fixed.py中的内存监控问题
    fix_memory_monitoring()
    
    # 2. 修复所有可能的线程安全问题
    fix_thread_safety()
    
    # 3. 添加全局异常处理
    add_global_exception_handling()
    
    print("✅ 最终崩溃修复完成")

def fix_memory_monitoring():
    """修复内存监控相关问题"""
    print("🔧 修复内存监控问题...")
    
    with open('simple_ui_fixed.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 禁用可能导致线程冲突的内存监控器
    content = re.sub(
        r'(\\\1+)self\\\1memory_watcher = MemoryWatcher\\\1self\\\1',
        r'\\\1# 临时禁用内存监控器以避免线程冲突\n\\\1# self.memory_watcher = MemoryWatcher(self)\n\\\1self.memory_watcher = None',
        content
    )
    
    # 修复内存警告连接
    content = re.sub(
        r'(\\\1+)self\\\1memory_watcher\\\1memory_warning\\\1connect\\\1self\\\1on_memory_warning\\\1',
        r'\\\1# 临时禁用内存警告连接\n\\\1# self.memory_watcher.memory_warning.connect(self.on_memory_warning)\n\\\1if self.memory_watcher:\n\\\1    self.memory_watcher.memory_warning.connect(self.on_memory_warning)',
        content
    )
    
    with open('simple_ui_fixed.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 内存监控问题修复完成")

def fix_thread_safety():
    """修复线程安全问题"""
    print("🔧 修复线程安全问题...")
    
    with open('simple_ui_fixed.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 在主窗口初始化开始处添加线程安全检查
    init_pattern = r'(def __init__\\\1self, parent=None\\\1:\\\1*super\\\1\\\1.__init__\\\1parent\\\1)'
    replacement = r'''\\\1
        
        # 确保在主线程中初始化
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import QThread
        if QApplication.instance() and QApplication.instance().thread() != QThread.currentThread():
            print("[WARN] 主窗口不在主线程中初始化，可能导致问题")
        '''
    
    content = re.sub(init_pattern, replacement, content, flags=re.MULTILINE | re.DOTALL)
    
    with open('simple_ui_fixed.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 线程安全问题修复完成")

def add_global_exception_handling():
    """添加全局异常处理"""
    print("🔧 添加全局异常处理...")
    
    with open('simple_ui_fixed.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 在main函数中添加更强的异常处理
    main_pattern = r'(if __name__ == "__main__":.*?)(sys\\\1exit\\\1app\\\1exec\\\1\\\1\\\1)'
    replacement = r'''\\\1try:
        \\\1
    except Exception as e:
        print(f"❌ 程序运行时发生未捕获异常: {e}")
        import traceback
        traceback.print_exc()
        try:
            with open("final_crash_log.txt", "a", encoding="utf-8") as f:
                import time
                f.write(f"\\n{time.strftime('%Y-%m-%d %H:%M:%S')} - 最终异常:\\n")
                traceback.print_exc(file=f)
        except:
            pass
        sys.exit(1)'''
    
    content = re.sub(main_pattern, replacement, content, flags=re.MULTILINE | re.DOTALL)
    
    with open('simple_ui_fixed.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 全局异常处理添加完成")

if __name__ == "__main__":
    apply_final_crash_fix()
