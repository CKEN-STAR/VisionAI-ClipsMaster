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

class QuantizationManager:
    """量化管理器 - 管理模型量化策略"""

    def __init__(self, memory_guard=None):
        """初始化量化管理器

        Args:
            memory_guard: 内存守护器实例
        """
        self.memory_guard = memory_guard
        self.current_strategy = "balanced"
        self.available_strategies = {
            "aggressive": {"name": "Q2_K", "memory_mb": 2200, "quality": 0.75},
            "balanced": {"name": "Q4_K_M", "memory_mb": 3200, "quality": 0.88},
            "quality": {"name": "Q5_K", "memory_mb": 4500, "quality": 0.94},
            "original": {"name": "FP16", "memory_mb": 16000, "quality": 1.0}
        }

    def select_strategy(self, available_memory_mb: float) -> str:
        """根据可用内存选择量化策略"""
        if available_memory_mb < 3000:
            return "aggressive"
        elif available_memory_mb < 5000:
            return "balanced"
        elif available_memory_mb < 16000:
            return "quality"
        else:
            return "original"

    def get_strategy_info(self, strategy: str) -> Dict:
        """获取策略信息"""
        return self.available_strategies.get(strategy, self.available_strategies["balanced"])

class MemoryGuard(MemoryManager):
    """内存守护器（向后兼容）"""

    def get_memory_info(self) -> Dict[str, float]:
        """获取详细的内存信息"""
        try:
            import psutil

            # 获取系统内存信息
            memory = psutil.virtual_memory()

            # 获取当前进程内存信息
            process = psutil.Process()
            process_memory = process.memory_info()

            return {
                "total_memory_gb": memory.total / (1024**3),
                "available_memory_gb": memory.available / (1024**3),
                "used_memory_gb": memory.used / (1024**3),
                "memory_percent": memory.percent,
                "process_memory_mb": process_memory.rss / (1024**2),
                "process_memory_gb": process_memory.rss / (1024**3)
            }
        except Exception as e:
            return {
                "total_memory_gb": 0.0,
                "available_memory_gb": 0.0,
                "used_memory_gb": 0.0,
                "memory_percent": 0.0,
                "process_memory_mb": 0.0,
                "process_memory_gb": 0.0,
                "error": str(e)
            }

    def optimize_memory_usage(self) -> Dict[str, Any]:
        """优化内存使用"""
        try:
            import gc

            # 记录优化前的内存使用
            before_memory = self.get_memory_usage()

            # 执行垃圾回收
            collected = gc.collect()

            # 触发清理回调
            self._trigger_cleanup()

            # 记录优化后的内存使用
            after_memory = self.get_memory_usage()

            return {
                "status": "success",
                "before_memory_mb": before_memory,
                "after_memory_mb": after_memory,
                "freed_memory_mb": before_memory - after_memory,
                "gc_collected": collected
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e)
            }

    def check_memory_safety(self) -> bool:
        """检查内存安全状态"""
        try:
            memory_info = self.get_memory_info()

            # 检查系统内存使用率
            if memory_info["memory_percent"] > 90:
                return False

            # 检查进程内存使用
            if memory_info["process_memory_gb"] > 3.5:  # 4GB设备的安全阈值
                return False

            return True
        except Exception:
            return False

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
