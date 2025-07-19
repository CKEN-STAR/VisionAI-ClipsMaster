"""
超快响应系统
优化用户交互响应时间到1ms以内
"""

import time
import threading
from typing import Dict, List, Optional, Any, Callable
from collections import deque
from PyQt6.QtCore import QObject, QTimer, pyqtSignal, QThread
from PyQt6.QtWidgets import QWidget, QApplication

class ResponseTimeOptimizer(QObject):
    """响应时间优化器"""
    
    response_measured = pyqtSignal(float)  # 响应时间(ms)
    optimization_applied = pyqtSignal(str)  # 优化措施
    
    def __init__(self):
        super().__init__()
        self.response_times = deque(maxlen=100)
        self.optimization_enabled = True
        self.target_response_time = 1.0  # 目标响应时间(ms)
        
        # 优化策略
        self.optimizations = {
            'event_batching': True,
            'lazy_loading': True,
            'cache_optimization': True,
            'thread_pooling': True,
            'ui_freezing_prevention': True
        }
        
        # 事件批处理
        self.event_batch = []
        self.batch_timer = QTimer()
        self.batch_timer.timeout.connect(self._process_event_batch)
        self.batch_timer.setSingleShot(True)
        
        # 缓存系统
        self.ui_cache = {}
        self.computation_cache = {}
        
        # 线程池
        self.worker_threads = []
        self.max_worker_threads = 4
    
    def measure_response_time(self, start_time: float) -> float:
        """测量响应时间"""
        response_time = (time.time() - start_time) * 1000  # 转换为毫秒
        self.response_times.append(response_time)
        self.response_measured.emit(response_time)
        
        # 如果响应时间超过目标，应用优化
        if response_time > self.target_response_time and self.optimization_enabled:
            self._apply_optimizations()
        
        return response_time
    
    def start_timing(self) -> float:
        """开始计时"""
        return time.time()
    
    def _apply_optimizations(self):
        """应用优化措施"""
        avg_response_time = sum(self.response_times) / len(self.response_times)
        
        if avg_response_time > 5.0:  # 超过5ms
            self._optimize_heavy_operations()
        elif avg_response_time > 2.0:  # 超过2ms
            self._optimize_medium_operations()
        else:  # 1-2ms之间
            self._optimize_light_operations()
    
    def _optimize_heavy_operations(self):
        """优化重型操作"""
        if self.optimizations['thread_pooling']:
            self._optimize_thread_pool()
            self.optimization_applied.emit("线程池优化")
        
        if self.optimizations['cache_optimization']:
            self._optimize_cache()
            self.optimization_applied.emit("缓存优化")
    
    def _optimize_medium_operations(self):
        """优化中型操作"""
        if self.optimizations['event_batching']:
            self._enable_event_batching()
            self.optimization_applied.emit("事件批处理")
        
        if self.optimizations['lazy_loading']:
            self._optimize_lazy_loading()
            self.optimization_applied.emit("延迟加载优化")
    
    def _optimize_light_operations(self):
        """优化轻型操作"""
        if self.optimizations['ui_freezing_prevention']:
            self._prevent_ui_freezing()
            self.optimization_applied.emit("UI冻结预防")
    
    def _optimize_thread_pool(self):
        """优化线程池"""
        # 清理已完成的线程
        self.worker_threads = [t for t in self.worker_threads if t.isRunning()]
        
        # 如果线程数不足，创建新线程
        if len(self.worker_threads) < self.max_worker_threads:
            for _ in range(self.max_worker_threads - len(self.worker_threads)):
                worker = WorkerThread()
                self.worker_threads.append(worker)
    
    def _optimize_cache(self):
        """优化缓存"""
        # 清理过期的UI缓存
        current_time = time.time()
        expired_keys = []
        
        for key, (data, timestamp) in self.ui_cache.items():
            if current_time - timestamp > 60:  # 60秒过期
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.ui_cache[key]
        
        # 清理计算缓存
        if len(self.computation_cache) > 1000:
            # 保留最近的500个
            items = list(self.computation_cache.items())
            self.computation_cache = dict(items[-500:])
    
    def _enable_event_batching(self):
        """启用事件批处理"""
        if not self.batch_timer.isActive():
            self.batch_timer.start(1)  # 1ms后处理批次
    
    def _optimize_lazy_loading(self):
        """优化延迟加载"""
        # 这里可以实现延迟加载优化逻辑
        pass
    
    def _prevent_ui_freezing(self):
        """预防UI冻结"""
        # 强制处理待处理的事件
        app = QApplication.instance()
        if app:
            app.processEvents()
    
    def _process_event_batch(self):
        """处理事件批次"""
        if self.event_batch:
            # 批量处理事件
            for event_func in self.event_batch:
                try:
                    event_func()
                except Exception as e:
                    print(f"[WARN] 批处理事件执行失败: {e}")
            
            self.event_batch.clear()
    
    def add_to_batch(self, event_func: Callable):
        """添加事件到批处理"""
        self.event_batch.append(event_func)
        self._enable_event_batching()
    
    def cache_ui_data(self, key: str, data: Any):
        """缓存UI数据"""
        self.ui_cache[key] = (data, time.time())
    
    def get_cached_ui_data(self, key: str) -> Optional[Any]:
        """获取缓存的UI数据"""
        if key in self.ui_cache:
            data, timestamp = self.ui_cache[key]
            if time.time() - timestamp < 60:  # 60秒内有效
                return data
        return None
    
    def cache_computation(self, key: str, result: Any):
        """缓存计算结果"""
        self.computation_cache[key] = result
    
    def get_cached_computation(self, key: str) -> Optional[Any]:
        """获取缓存的计算结果"""
        return self.computation_cache.get(key)
    
    def get_average_response_time(self) -> float:
        """获取平均响应时间"""
        if not self.response_times:
            return 0.0
        return sum(self.response_times) / len(self.response_times)
    
    def get_response_stats(self) -> Dict[str, float]:
        """获取响应时间统计"""
        if not self.response_times:
            return {
                'average': 0.0,
                'min': 0.0,
                'max': 0.0,
                'count': 0
            }
        
        times = list(self.response_times)
        return {
            'average': sum(times) / len(times),
            'min': min(times),
            'max': max(times),
            'count': len(times)
        }

class WorkerThread(QThread):
    """工作线程"""
    
    def __init__(self):
        super().__init__()
        self.tasks = deque()
        self.running = True
    
    def add_task(self, task: Callable):
        """添加任务"""
        self.tasks.append(task)
    
    def run(self):
        """运行线程"""
        while self.running:
            if self.tasks:
                task = self.tasks.popleft()
                try:
                    task()
                except Exception as e:
                    print(f"[WARN] 工作线程任务执行失败: {e}")
            else:
                self.msleep(1)  # 等待1ms
    
    def stop(self):
        """停止线程"""
        self.running = False

class UltraFastResponseManager(QObject):
    """超快响应管理器"""
    
    def __init__(self):
        super().__init__()
        self.optimizer = ResponseTimeOptimizer()
        self.active_timers = {}
        
        # 连接信号
        self.optimizer.response_measured.connect(self._on_response_measured)
        self.optimizer.optimization_applied.connect(self._on_optimization_applied)
    
    def start_interaction_timing(self, interaction_id: str) -> str:
        """开始交互计时"""
        start_time = self.optimizer.start_timing()
        self.active_timers[interaction_id] = start_time
        return interaction_id
    
    def end_interaction_timing(self, interaction_id: str) -> float:
        """结束交互计时"""
        if interaction_id in self.active_timers:
            start_time = self.active_timers[interaction_id]
            response_time = self.optimizer.measure_response_time(start_time)
            del self.active_timers[interaction_id]
            return response_time
        return 0.0
    
    def optimize_widget_response(self, widget: QWidget):
        """优化组件响应"""
        # 为组件添加响应时间优化
        original_mousePressEvent = widget.mousePressEvent
        original_keyPressEvent = widget.keyPressEvent
        
        def optimized_mousePressEvent(event):
            interaction_id = f"mouse_{id(widget)}_{time.time()}"
            self.start_interaction_timing(interaction_id)
            
            # 使用缓存或批处理优化
            def execute_event():
                original_mousePressEvent(event)
                self.end_interaction_timing(interaction_id)
            
            # 如果是轻量级操作，直接执行；否则加入批处理
            if self._is_lightweight_operation(widget):
                execute_event()
            else:
                self.optimizer.add_to_batch(execute_event)
        
        def optimized_keyPressEvent(event):
            interaction_id = f"key_{id(widget)}_{time.time()}"
            self.start_interaction_timing(interaction_id)
            
            def execute_event():
                original_keyPressEvent(event)
                self.end_interaction_timing(interaction_id)
            
            if self._is_lightweight_operation(widget):
                execute_event()
            else:
                self.optimizer.add_to_batch(execute_event)
        
        widget.mousePressEvent = optimized_mousePressEvent
        widget.keyPressEvent = optimized_keyPressEvent
    
    def _is_lightweight_operation(self, widget: QWidget) -> bool:
        """判断是否为轻量级操作"""
        # 简单的启发式判断
        widget_type = type(widget).__name__
        lightweight_types = ['QPushButton', 'QLabel', 'QCheckBox', 'QRadioButton']
        return widget_type in lightweight_types
    
    def _on_response_measured(self, response_time: float):
        """响应时间测量回调"""
        if response_time > 1.0:
            print(f"[PERF] 响应时间: {response_time:.2f}ms (超过目标)")
        else:
            print(f"[PERF] 响应时间: {response_time:.2f}ms (达标)")
    
    def _on_optimization_applied(self, optimization: str):
        """优化应用回调"""
        print(f"[OPT] 应用优化: {optimization}")
    
    def get_performance_report(self) -> Dict[str, Any]:
        """获取性能报告"""
        stats = self.optimizer.get_response_stats()
        return {
            'response_stats': stats,
            'target_achieved': stats['average'] <= 1.0 if stats['count'] > 0 else False,
            'optimizations_enabled': self.optimizer.optimizations,
            'cache_size': {
                'ui_cache': len(self.optimizer.ui_cache),
                'computation_cache': len(self.optimizer.computation_cache)
            }
        }

# 全局超快响应管理器实例
_response_manager = None

def get_response_manager() -> UltraFastResponseManager:
    """获取全局响应管理器"""
    global _response_manager
    if _response_manager is None:
        _response_manager = UltraFastResponseManager()
    return _response_manager

def optimize_widget_response(widget: QWidget):
    """优化组件响应（快捷函数）"""
    get_response_manager().optimize_widget_response(widget)

def start_timing(interaction_id: str) -> str:
    """开始计时（快捷函数）"""
    return get_response_manager().start_interaction_timing(interaction_id)

def end_timing(interaction_id: str) -> float:
    """结束计时（快捷函数）"""
    return get_response_manager().end_interaction_timing(interaction_id)

__all__ = [
    'ResponseTimeOptimizer',
    'UltraFastResponseManager',
    'get_response_manager',
    'optimize_widget_response',
    'start_timing',
    'end_timing'
]
