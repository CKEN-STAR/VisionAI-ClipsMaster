#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
内存管理器 - 监控和优化内存使用
"""

import psutil
import gc
import threading
import time
from typing import Optional, Dict, Any

class MemoryManager:
    """内存管理器主类"""
    
    def __init__(self, max_memory_mb: int = 400):
        self.max_memory_mb = max_memory_mb
        self.monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.callbacks = []
        
    def start_monitoring(self):
        """开始内存监控"""
        if not self.monitoring:
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
    
    def stop_monitoring(self):
        """停止内存监控"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)
    
    def _monitor_loop(self):
        """内存监控循环"""
        while self.monitoring:
            try:
                current_memory = self.get_memory_usage()
                if current_memory > self.max_memory_mb:
                    self._trigger_cleanup()
                time.sleep(1)
            except Exception:
                pass
    
    def get_memory_usage(self) -> float:
        """获取当前内存使用量(MB)"""
        try:
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except:
            return 0
    
    def _trigger_cleanup(self):
        """触发内存清理"""
        gc.collect()
        for callback in self.callbacks:
            try:
                callback()
            except:
                pass
    
    def add_cleanup_callback(self, callback):
        """添加清理回调"""
        self.callbacks.append(callback)
    
    def force_cleanup(self):
        """强制清理内存"""
        self._trigger_cleanup()

class MemoryGuard(MemoryManager):
    """内存守护器（向后兼容）"""
    pass

# 全局实例
memory_manager = MemoryManager()

def track_memory(operation_name: str):
    """
    内存跟踪装饰器

    Args:
        operation_name: 操作名称
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # 记录开始时的内存使用
            start_memory = memory_manager.get_memory_usage()

            try:
                # 执行函数
                result = func(*args, **kwargs)

                # 记录结束时的内存使用
                end_memory = memory_manager.get_memory_usage()
                memory_diff = end_memory - start_memory

                # 如果内存增长过多，触发垃圾回收
                if memory_diff > 100:  # 100MB
                    gc.collect()

                return result

            except Exception as e:
                # 发生异常时也要清理内存
                gc.collect()
                raise e

        return wrapper
    return decorator
memory_guard = MemoryGuard()

def get_memory_manager():
    """获取内存管理器实例"""
    return memory_manager

def get_memory_guard():
    """获取内存守护器实例（向后兼容）"""
    return memory_guard
