#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster UI异步优化器
专门用于优化UI响应时间，目标从1.8秒降低到<1秒
"""

import time
import queue
import threading
from PyQt6.QtCore import QObject, QTimer, QThread, pyqtSignal
from PyQt6.QtWidgets import QApplication
from collections import deque
import weakref

class AsyncUIUpdater(QObject):
    """异步UI更新器 - 核心优化组件"""
    
    update_completed = pyqtSignal(str, float)  # 更新完成信号
    
    def __init__(self):
        super().__init__()
        self.update_queue = queue.PriorityQueue()
        self.is_processing = False
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._process_updates)
        self.update_timer.start(16)  # 60FPS更新频率
        
        # 性能监控
        self.response_times = deque(maxlen=50)
        self.update_count = 0
        
    def queue_update(self, update_func, priority=1, delay_ms=0):
        """队列化UI更新操作
        
        Args:
            update_func: 更新函数
            priority: 优先级 (0=最高, 1=高, 2=中, 3=低)
            delay_ms: 延迟毫秒数
        """
        timestamp = time.time() + (delay_ms / 1000.0)
        self.update_queue.put((priority, timestamp, update_func))
        
    def _process_updates(self):
        """处理更新队列"""
        if self.is_processing or self.update_queue.empty():
            return
            
        self.is_processing = True
        start_time = time.time()
        
        try:
            # 批量处理更新（每帧最多处理3个）
            processed = 0
            current_time = time.time()
            
            while not self.update_queue.empty() and processed < 3:
                try:
                    priority, timestamp, update_func = self.update_queue.get_nowait()
                    
                    # 检查是否到达执行时间
                    if timestamp <= current_time:
                        update_func()
                        processed += 1
                        self.update_count += 1
                    else:
                        # 重新放回队列
                        self.update_queue.put((priority, timestamp, update_func))
                        break
                        
                except queue.Empty:
                    break
                except Exception as e:
                    print(f"[ERROR] UI更新失败: {e}")
                    
        finally:
            self.is_processing = False
            
            # 记录性能
            elapsed = time.time() - start_time
            self.response_times.append(elapsed)
            
            if elapsed > 0.016:  # 超过16ms (60FPS)
                print(f"[WARN] UI更新耗时: {elapsed*1000:.1f}ms")
                
    def get_performance_stats(self):
        """获取性能统计"""
        if not self.response_times:
            return {}
            
        return {
            "avg_response_time": sum(self.response_times) / len(self.response_times),
            "max_response_time": max(self.response_times),
            "update_count": self.update_count,
            "queue_size": self.update_queue.qsize()
        }

class TabSwitchOptimizer:
    """标签页切换优化器"""
    
    def __init__(self, main_window):
        self.main_window = weakref.ref(main_window)
        self.ui_updater = AsyncUIUpdater()
        self.tab_cache = {}
        self.preload_timer = QTimer()
        self.preload_timer.timeout.connect(self._preload_tabs)
        
    def optimize_tab_switch(self, index):
        """优化的标签页切换"""
        start_time = time.time()
        
        try:
            window = self.main_window()
            if not window:
                return
                
            # 立即响应UI切换（最高优先级）
            self.ui_updater.queue_update(
                lambda: self._immediate_tab_switch(window, index),
                priority=0
            )
            
            # 延迟执行非关键操作（低优先级）
            self.ui_updater.queue_update(
                lambda: self._delayed_tab_operations(window, index),
                priority=2,
                delay_ms=50
            )
            
            # 预加载相邻标签页（最低优先级）
            self.ui_updater.queue_update(
                lambda: self._preload_adjacent_tabs(window, index),
                priority=3,
                delay_ms=200
            )
            
        except Exception as e:
            print(f"[ERROR] 标签页切换优化失败: {e}")
            
    def _immediate_tab_switch(self, window, index):
        """立即执行的标签页切换"""
        try:
            # 只执行最关键的UI更新
            if hasattr(window, 'progress_container'):
                window.progress_container.setVisible(index == 0)
                
            # 记录用户交互（异步）
            QTimer.singleShot(0, window.record_user_interaction)
            
        except Exception as e:
            print(f"[ERROR] 立即标签页切换失败: {e}")
            
    def _delayed_tab_operations(self, window, index):
        """延迟执行的标签页操作"""
        try:
            tab_names = ["视频处理", "模型训练", "关于我们", "设置"]
            if 0 <= index < len(tab_names):
                # 只在必要时执行特定操作
                if index == 0 and not hasattr(window, '_video_tab_initialized'):
                    self._init_video_tab(window)
                    window._video_tab_initialized = True
                elif index == 3 and not hasattr(window, '_settings_tab_initialized'):
                    self._init_settings_tab(window)
                    window._settings_tab_initialized = True
                    
        except Exception as e:
            print(f"[ERROR] 延迟标签页操作失败: {e}")
            
    def _init_video_tab(self, window):
        """初始化视频处理标签页"""
        try:
            if hasattr(window, 'check_ffmpeg_status'):
                window.check_ffmpeg_status()
        except Exception as e:
            print(f"[ERROR] 视频标签页初始化失败: {e}")
            
    def _init_settings_tab(self, window):
        """初始化设置标签页"""
        try:
            if hasattr(window, 'detect_gpu_hardware'):
                window.detect_gpu_hardware()
        except Exception as e:
            print(f"[ERROR] 设置标签页初始化失败: {e}")
            
    def _preload_adjacent_tabs(self, window, current_index):
        """预加载相邻标签页"""
        try:
            # 预加载前后标签页的内容
            tab_count = window.tabs.count() if hasattr(window, 'tabs') else 4
            
            for offset in [-1, 1]:
                adjacent_index = current_index + offset
                if 0 <= adjacent_index < tab_count:
                    self._cache_tab_content(window, adjacent_index)
                    
        except Exception as e:
            print(f"[ERROR] 预加载相邻标签页失败: {e}")
            
    def _cache_tab_content(self, window, index):
        """缓存标签页内容"""
        try:
            if index not in self.tab_cache:
                # 缓存标签页的基本信息
                self.tab_cache[index] = {
                    "initialized": True,
                    "timestamp": time.time()
                }
        except Exception as e:
            print(f"[ERROR] 缓存标签页内容失败: {e}")
            
    def _preload_tabs(self):
        """定期预加载标签页"""
        try:
            window = self.main_window()
            if window and hasattr(window, 'tabs'):
                current_index = window.tabs.currentIndex()
                self._preload_adjacent_tabs(window, current_index)
        except Exception as e:
            print(f"[ERROR] 定期预加载失败: {e}")

class MemoryOptimizer:
    """内存优化器"""
    
    def __init__(self):
        self.object_pool = {}
        self.cache_limit = 50
        self.cleanup_timer = QTimer()
        self.cleanup_timer.timeout.connect(self._periodic_cleanup)
        self.cleanup_timer.start(30000)  # 30秒清理一次
        
    def get_pooled_object(self, obj_type, create_func):
        """从对象池获取对象"""
        pool_key = obj_type.__name__
        
        if pool_key not in self.object_pool:
            self.object_pool[pool_key] = deque(maxlen=self.cache_limit)
            
        pool = self.object_pool[pool_key]
        
        if pool:
            return pool.popleft()
        else:
            return create_func()
            
    def return_to_pool(self, obj, obj_type):
        """将对象返回到池中"""
        pool_key = obj_type.__name__
        
        if pool_key in self.object_pool:
            pool = self.object_pool[pool_key]
            if len(pool) < self.cache_limit:
                # 重置对象状态
                if hasattr(obj, 'reset'):
                    obj.reset()
                pool.append(obj)
                
    def _periodic_cleanup(self):
        """定期清理对象池"""
        try:
            for pool_key, pool in self.object_pool.items():
                # 清理一半的缓存对象
                cleanup_count = len(pool) // 2
                for _ in range(cleanup_count):
                    if pool:
                        pool.popleft()
                        
            print(f"[INFO] 对象池清理完成，当前池大小: {sum(len(p) for p in self.object_pool.values())}")
            
        except Exception as e:
            print(f"[ERROR] 对象池清理失败: {e}")

# 全局优化器实例
ui_async_optimizer = None
memory_optimizer = MemoryOptimizer()

def initialize_optimizers(main_window):
    """初始化优化器"""
    global ui_async_optimizer
    ui_async_optimizer = TabSwitchOptimizer(main_window)
    print("[OK] UI异步优化器初始化完成")
    
def optimize_tab_switch(index):
    """优化标签页切换的全局接口"""
    if ui_async_optimizer:
        ui_async_optimizer.optimize_tab_switch(index)
    else:
        print("[WARN] UI异步优化器未初始化")
        
def get_optimization_stats():
    """获取优化统计信息"""
    stats = {}
    
    if ui_async_optimizer:
        stats["ui_performance"] = ui_async_optimizer.ui_updater.get_performance_stats()
        
    stats["memory_pools"] = {
        pool_key: len(pool) 
        for pool_key, pool in memory_optimizer.object_pool.items()
    }
    
    return stats
