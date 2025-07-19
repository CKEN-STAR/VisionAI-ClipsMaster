#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 增强内存管理器
专门用于优化内存使用，目标从567MB降低到<500MB
"""

import gc
import sys
import time
import weakref
import psutil
import threading
from collections import defaultdict, deque
from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from PyQt6.QtWidgets import QWidget

class LazyComponentLoader:
    """懒加载组件管理器"""
    
    def __init__(self):
        self._components = {}
        self._loaded = set()
        self._loading = set()
        self._access_count = defaultdict(int)
        self._last_access = {}
        
    def register_component(self, name, create_func, priority=1):
        """注册组件
        
        Args:
            name: 组件名称
            create_func: 创建函数
            priority: 优先级 (0=立即加载, 1=按需加载, 2=延迟加载)
        """
        self._components[name] = {
            "create_func": create_func,
            "priority": priority,
            "instance": None,
            "size_estimate": 0
        }
        
        # 立即加载高优先级组件
        if priority == 0:
            self.get_component(name)
            
    def get_component(self, name):
        """获取组件实例"""
        if name not in self._components:
            raise ValueError(f"未注册的组件: {name}")
            
        # 记录访问
        self._access_count[name] += 1
        self._last_access[name] = time.time()
        
        # 如果已加载，直接返回
        if name in self._loaded and self._components[name]["instance"]:
            return self._components[name]["instance"]
            
        # 如果正在加载，等待
        if name in self._loading:
            while name in self._loading:
                time.sleep(0.001)
            return self._components[name]["instance"]
            
        # 开始加载
        self._loading.add(name)
        
        try:
            print(f"[INFO] 懒加载组件: {name}")
            start_time = time.time()
            
            component_info = self._components[name]
            instance = component_info["create_func"]()
            
            # 估算内存使用
            if hasattr(instance, '__sizeof__'):
                component_info["size_estimate"] = sys.getsizeof(instance)
            
            component_info["instance"] = instance
            self._loaded.add(name)
            
            elapsed = time.time() - start_time
            print(f"[OK] 组件 {name} 加载完成，耗时: {elapsed:.3f}秒")
            
            return instance
            
        except Exception as e:
            print(f"[ERROR] 组件 {name} 加载失败: {e}")
            raise
        finally:
            self._loading.discard(name)
            
    def unload_component(self, name):
        """卸载组件"""
        if name in self._loaded:
            component_info = self._components[name]
            if component_info["instance"]:
                # 清理组件
                instance = component_info["instance"]
                if hasattr(instance, 'cleanup'):
                    instance.cleanup()
                    
                component_info["instance"] = None
                self._loaded.discard(name)
                print(f"[OK] 组件 {name} 已卸载")
                
    def cleanup_unused_components(self, max_idle_time=300):
        """清理未使用的组件"""
        current_time = time.time()
        to_unload = []
        
        for name in self._loaded:
            last_access = self._last_access.get(name, 0)
            if current_time - last_access > max_idle_time:
                # 检查优先级，不卸载高优先级组件
                if self._components[name]["priority"] > 0:
                    to_unload.append(name)
                    
        for name in to_unload:
            self.unload_component(name)
            
        if to_unload:
            print(f"[INFO] 清理了 {len(to_unload)} 个未使用组件")
            
    def get_memory_stats(self):
        """获取内存统计"""
        total_size = sum(
            info["size_estimate"] 
            for info in self._components.values() 
            if info["instance"]
        )
        
        return {
            "loaded_components": len(self._loaded),
            "total_components": len(self._components),
            "estimated_memory_mb": total_size / 1024 / 1024,
            "access_stats": dict(self._access_count)
        }

class SmartMemoryManager(QObject):
    """智能内存管理器"""
    
    memory_warning = pyqtSignal(str, int)
    memory_optimized = pyqtSignal(float)
    
    def __init__(self):
        super().__init__()
        self.process = psutil.Process()
        self.baseline_memory = self._get_memory_usage()
        
        # 内存阈值配置
        self.warning_threshold = 500  # 500MB警告
        self.critical_threshold = 600  # 600MB危急
        self.target_memory = 480  # 目标480MB
        
        # 监控配置
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self._monitor_memory)
        self.monitor_timer.start(5000)  # 5秒监控一次
        
        # 清理配置
        self.cleanup_timer = QTimer()
        self.cleanup_timer.timeout.connect(self._smart_cleanup)
        self.cleanup_timer.start(60000)  # 1分钟清理一次
        
        # 内存历史
        self.memory_history = deque(maxlen=100)
        self.gc_history = deque(maxlen=50)
        
        # 组件管理
        self.component_loader = LazyComponentLoader()
        
    def _get_memory_usage(self):
        """获取当前内存使用量（MB）"""
        try:
            return self.process.memory_info().rss / 1024 / 1024
        except:
            return 0
            
    def _monitor_memory(self):
        """监控内存使用"""
        try:
            current_memory = self._get_memory_usage()
            self.memory_history.append({
                "timestamp": time.time(),
                "memory_mb": current_memory
            })
            
            # 检查是否需要警告
            if current_memory > self.critical_threshold:
                self.memory_warning.emit(
                    f"内存使用过高: {current_memory:.1f}MB", 2
                )
                self._emergency_cleanup()
            elif current_memory > self.warning_threshold:
                self.memory_warning.emit(
                    f"内存使用较高: {current_memory:.1f}MB", 1
                )
                self._gentle_cleanup()
                
        except Exception as e:
            print(f"[ERROR] 内存监控失败: {e}")
            
    def _smart_cleanup(self):
        """智能清理"""
        try:
            start_memory = self._get_memory_usage()
            
            # 清理未使用组件
            self.component_loader.cleanup_unused_components()
            
            # 执行垃圾回收
            collected = gc.collect()
            
            end_memory = self._get_memory_usage()
            freed_memory = start_memory - end_memory
            
            if freed_memory > 0:
                self.memory_optimized.emit(freed_memory)
                print(f"[OK] 智能清理释放内存: {freed_memory:.1f}MB")
                
            # 记录GC历史
            self.gc_history.append({
                "timestamp": time.time(),
                "collected": collected,
                "freed_mb": freed_memory
            })
            
        except Exception as e:
            print(f"[ERROR] 智能清理失败: {e}")
            
    def _gentle_cleanup(self):
        """温和清理"""
        try:
            # 清理缓存
            if hasattr(self, '_temp_cache'):
                self._temp_cache.clear()
                
            # 限制历史数据
            if len(self.memory_history) > 50:
                self.memory_history = deque(
                    list(self.memory_history)[-50:], maxlen=100
                )
                
            # 执行一次GC
            gc.collect()
            
        except Exception as e:
            print(f"[ERROR] 温和清理失败: {e}")
            
    def _emergency_cleanup(self):
        """紧急清理"""
        try:
            print("[WARN] 执行紧急内存清理...")
            
            # 卸载所有低优先级组件
            for name in list(self.component_loader._loaded):
                component_info = self.component_loader._components.get(name, {})
                if component_info.get("priority", 1) >= 2:
                    self.component_loader.unload_component(name)
                    
            # 强制垃圾回收
            for _ in range(3):
                gc.collect()
                
            # 清理所有缓存
            self._clear_all_caches()
            
            current_memory = self._get_memory_usage()
            print(f"[OK] 紧急清理完成，当前内存: {current_memory:.1f}MB")
            
        except Exception as e:
            print(f"[ERROR] 紧急清理失败: {e}")
            
    def _clear_all_caches(self):
        """清理所有缓存"""
        try:
            # 清理各种缓存
            caches_to_clear = [
                '_temp_cache', '_ui_cache', '_data_cache',
                'response_times', 'performance_data'
            ]
            
            for cache_name in caches_to_clear:
                if hasattr(self, cache_name):
                    cache = getattr(self, cache_name)
                    if hasattr(cache, 'clear'):
                        cache.clear()
                        
        except Exception as e:
            print(f"[ERROR] 清理缓存失败: {e}")
            
    def register_ui_component(self, name, create_func, priority=1):
        """注册UI组件"""
        self.component_loader.register_component(name, create_func, priority)
        
    def get_ui_component(self, name):
        """获取UI组件"""
        return self.component_loader.get_component(name)
        
    def get_memory_report(self):
        """获取内存报告"""
        current_memory = self._get_memory_usage()
        
        # 计算内存趋势
        if len(self.memory_history) >= 2:
            recent_avg = sum(
                h["memory_mb"] for h in list(self.memory_history)[-5:]
            ) / min(5, len(self.memory_history))
            
            trend = "上升" if recent_avg > current_memory else "下降"
        else:
            recent_avg = current_memory
            trend = "稳定"
            
        # 组件统计
        component_stats = self.component_loader.get_memory_stats()
        
        return {
            "current_memory_mb": current_memory,
            "baseline_memory_mb": self.baseline_memory,
            "memory_increase_mb": current_memory - self.baseline_memory,
            "target_memory_mb": self.target_memory,
            "memory_trend": trend,
            "recent_average_mb": recent_avg,
            "component_stats": component_stats,
            "gc_count": len(self.gc_history),
            "total_freed_mb": sum(h["freed_mb"] for h in self.gc_history),
            "memory_efficiency": min(100, (self.target_memory / current_memory) * 100)
        }

# 全局内存管理器实例
enhanced_memory_manager = None

def initialize_memory_manager():
    """初始化增强内存管理器"""
    global enhanced_memory_manager
    enhanced_memory_manager = SmartMemoryManager()
    print("[OK] 增强内存管理器初始化完成")
    return enhanced_memory_manager
    
def register_component(name, create_func, priority=1):
    """注册组件的全局接口"""
    if enhanced_memory_manager:
        enhanced_memory_manager.register_ui_component(name, create_func, priority)
    else:
        print("[WARN] 增强内存管理器未初始化")
        
def get_component(name):
    """获取组件的全局接口"""
    if enhanced_memory_manager:
        return enhanced_memory_manager.get_ui_component(name)
    else:
        print("[WARN] 增强内存管理器未初始化")
        return None
        
def get_memory_report():
    """获取内存报告的全局接口"""
    if enhanced_memory_manager:
        return enhanced_memory_manager.get_memory_report()
    else:
        return {"error": "内存管理器未初始化"}
