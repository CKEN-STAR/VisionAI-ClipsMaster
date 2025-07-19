#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 内存优化器
实现高效的内存管理、模型缓存和动态卸载机制
"""

import gc
import sys
import time
import threading
import weakref
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
from collections import OrderedDict
import psutil
import logging

logger = logging.getLogger(__name__)

@dataclass
class MemoryStats:
    """内存统计信息"""
    total_mb: float
    available_mb: float
    used_mb: float
    percent: float
    process_mb: float

class LRUCache:
    """LRU缓存实现，支持内存限制"""
    
    def __init__(self, max_size: int = 3, memory_limit_mb: float = 2000):
        self.max_size = max_size
        self.memory_limit_mb = memory_limit_mb
        self.cache = OrderedDict()
        self.memory_usage = {}
        self.access_times = {}
        self._lock = threading.RLock()
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存项"""
        with self._lock:
            if key in self.cache:
                # 更新访问时间和顺序
                self.access_times[key] = time.time()
                self.cache.move_to_end(key)
                return self.cache[key]
            return None
    
    def put(self, key: str, value: Any, memory_mb: float = 0):
        """添加缓存项"""
        with self._lock:
            # 如果已存在，更新
            if key in self.cache:
                self.cache[key] = value
                self.memory_usage[key] = memory_mb
                self.access_times[key] = time.time()
                self.cache.move_to_end(key)
                return
            
            # 检查内存限制
            total_memory = sum(self.memory_usage.values()) + memory_mb
            if total_memory > self.memory_limit_mb:
                self._evict_by_memory()
            
            # 检查大小限制
            if len(self.cache) >= self.max_size:
                self._evict_lru()
            
            # 添加新项
            self.cache[key] = value
            self.memory_usage[key] = memory_mb
            self.access_times[key] = time.time()
    
    def remove(self, key: str) -> bool:
        """移除缓存项"""
        with self._lock:
            if key in self.cache:
                del self.cache[key]
                del self.memory_usage[key]
                del self.access_times[key]
                return True
            return False
    
    def _evict_lru(self):
        """移除最久未使用的项"""
        if self.cache:
            oldest_key = next(iter(self.cache))
            logger.info(f"LRU缓存移除最久未使用项: {oldest_key}")
            self.remove(oldest_key)
    
    def _evict_by_memory(self):
        """基于内存使用移除项"""
        # 按内存使用量排序，移除占用最多的
        if self.memory_usage:
            largest_key = max(self.memory_usage.keys(), key=lambda k: self.memory_usage[k])
            logger.info(f"内存缓存移除最大占用项: {largest_key} ({self.memory_usage[largest_key]:.1f}MB)")
            self.remove(largest_key)
    
    def clear(self):
        """清空缓存"""
        with self._lock:
            self.cache.clear()
            self.memory_usage.clear()
            self.access_times.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        with self._lock:
            return {
                "size": len(self.cache),
                "max_size": self.max_size,
                "total_memory_mb": sum(self.memory_usage.values()),
                "memory_limit_mb": self.memory_limit_mb,
                "items": list(self.cache.keys())
            }

class MemoryOptimizer:
    """内存优化器"""
    
    def __init__(self, memory_limit_mb: float = 3800):
        self.memory_limit_mb = memory_limit_mb
        self.process = psutil.Process()
        self.model_cache = LRUCache(max_size=2, memory_limit_mb=memory_limit_mb * 0.7)
        self.data_cache = LRUCache(max_size=10, memory_limit_mb=memory_limit_mb * 0.2)
        self.monitoring = False
        self.cleanup_callbacks = []
        self._lock = threading.RLock()
        
        # 启动内存监控
        self.start_monitoring()
    
    def get_memory_stats(self) -> MemoryStats:
        """获取当前内存统计"""
        vm = psutil.virtual_memory()
        process_memory = self.process.memory_info().rss / 1024 / 1024
        
        return MemoryStats(
            total_mb=vm.total / 1024 / 1024,
            available_mb=vm.available / 1024 / 1024,
            used_mb=vm.used / 1024 / 1024,
            percent=vm.percent,
            process_mb=process_memory
        )
    
    def check_memory_pressure(self) -> bool:
        """检查内存压力"""
        stats = self.get_memory_stats()
        
        # 检查进程内存使用
        if stats.process_mb > self.memory_limit_mb * 0.9:
            logger.warning(f"进程内存使用过高: {stats.process_mb:.1f}MB / {self.memory_limit_mb}MB")
            return True
        
        # 检查系统内存使用
        if stats.percent > 85:
            logger.warning(f"系统内存使用过高: {stats.percent:.1f}%")
            return True
        
        return False
    
    def force_cleanup(self):
        """强制清理内存"""
        logger.info("开始强制内存清理...")
        
        with self._lock:
            # 清理模型缓存
            self.model_cache.clear()
            
            # 清理数据缓存
            self.data_cache.clear()
            
            # 执行注册的清理回调
            for callback in self.cleanup_callbacks:
                try:
                    callback()
                except Exception as e:
                    logger.error(f"清理回调执行失败: {e}")
            
            # 强制垃圾回收
            collected = gc.collect()
            logger.info(f"垃圾回收释放了 {collected} 个对象")
        
        # 获取清理后的内存状态
        stats = self.get_memory_stats()
        logger.info(f"清理后进程内存: {stats.process_mb:.1f}MB")
    
    def register_cleanup_callback(self, callback: Callable):
        """注册内存清理回调"""
        self.cleanup_callbacks.append(callback)
    
    def cache_model(self, key: str, model: Any, memory_mb: float):
        """缓存模型"""
        self.model_cache.put(key, model, memory_mb)
        logger.info(f"模型已缓存: {key} ({memory_mb:.1f}MB)")
    
    def get_cached_model(self, key: str) -> Optional[Any]:
        """获取缓存的模型"""
        model = self.model_cache.get(key)
        if model:
            logger.info(f"从缓存获取模型: {key}")
        return model
    
    def cache_data(self, key: str, data: Any, memory_mb: float = 0):
        """缓存数据"""
        if memory_mb == 0:
            # 估算数据大小
            memory_mb = sys.getsizeof(data) / 1024 / 1024
        
        self.data_cache.put(key, data, memory_mb)
    
    def get_cached_data(self, key: str) -> Optional[Any]:
        """获取缓存的数据"""
        return self.data_cache.get(key)
    
    def start_monitoring(self):
        """启动内存监控"""
        if self.monitoring:
            return
        
        self.monitoring = True
        
        def monitor_loop():
            while self.monitoring:
                try:
                    if self.check_memory_pressure():
                        logger.info("检测到内存压力，执行自动清理...")
                        self.force_cleanup()
                    
                    time.sleep(5)  # 每5秒检查一次
                except Exception as e:
                    logger.error(f"内存监控错误: {e}")
                    time.sleep(10)
        
        self.monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("内存监控已启动")
    
    def stop_monitoring(self):
        """停止内存监控"""
        self.monitoring = False
        logger.info("内存监控已停止")
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """获取优化统计信息"""
        memory_stats = self.get_memory_stats()
        
        return {
            "memory_stats": {
                "process_mb": memory_stats.process_mb,
                "system_percent": memory_stats.percent,
                "available_mb": memory_stats.available_mb
            },
            "model_cache": self.model_cache.get_stats(),
            "data_cache": self.data_cache.get_stats(),
            "memory_limit_mb": self.memory_limit_mb,
            "memory_pressure": self.check_memory_pressure()
        }

# 全局内存优化器实例
_memory_optimizer = None

def get_memory_optimizer() -> MemoryOptimizer:
    """获取全局内存优化器实例"""
    global _memory_optimizer
    if _memory_optimizer is None:
        _memory_optimizer = MemoryOptimizer()
    return _memory_optimizer

def optimize_memory_usage():
    """优化内存使用的装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            optimizer = get_memory_optimizer()
            
            # 执行前检查内存
            if optimizer.check_memory_pressure():
                optimizer.force_cleanup()
            
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                # 执行后进行轻量级清理
                gc.collect()
        
        return wrapper
    return decorator
