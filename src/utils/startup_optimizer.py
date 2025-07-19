#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
启动优化器 - 优化程序启动性能
"""

import os
import sys
import time
from pathlib import Path

class StartupOptimizer:
    """启动优化器"""
    
    def __init__(self):
        self.start_time = time.time()
        self.optimizations_applied = []
    
    def optimize_imports(self):
        """优化导入性能"""
        # 设置环境变量减少导入时间
        os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
        os.environ['PYTHONUNBUFFERED'] = '1'
        
        # 预编译常用模块
        try:
            import py_compile
            common_modules = [
                'src/core/language_detector.py',
                'src/utils/memory_guard.py',
                'ui/main_window.py'
            ]
            
            for module in common_modules:
                if Path(module).exists():
                    try:
                        py_compile.compile(module, doraise=True)
                    except:
                        pass
        except:
            pass
        
        self.optimizations_applied.append("优化了模块导入")
    
    def optimize_memory(self):
        """优化内存使用"""
        import gc
        
        # 强制垃圾回收
        gc.collect()
        
        # 设置垃圾回收阈值
        gc.set_threshold(700, 10, 10)
        
        self.optimizations_applied.append("优化了内存使用")
    
    def get_startup_time(self):
        """获取启动时间"""
        return time.time() - self.start_time
    
    def apply_all_optimizations(self):
        """应用所有优化"""
        self.optimize_imports()
        self.optimize_memory()
        
        return self.optimizations_applied

# 全局实例
startup_optimizer = StartupOptimizer()

def get_startup_optimizer():
    """获取启动优化器实例"""
    return startup_optimizer
