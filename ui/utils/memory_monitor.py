"""
内存监控器
监控和优化内存使用，确保不超过400MB限制
"""

import gc
import time
import threading
from typing import Optional, Dict, Any, Callable
from PyQt6.QtCore import QObject, QTimer, pyqtSignal

class MemoryMonitor(QObject):
    """内存监控器"""
    
    # 信号
    memory_warning = pyqtSignal(float)    # 内存警告（MB）
    memory_critical = pyqtSignal(float)   # 内存危险（MB）
    memory_optimized = pyqtSignal(float)  # 内存优化完成（MB）
    
    def __init__(self):
        super().__init__()
        self.memory_limit = 400  # MB
        self.warning_threshold = 0.8  # 80%
        self.critical_threshold = 0.95  # 95%
        
        self.monitoring_enabled = True
        self.monitoring_interval = 5000  # 5秒
        self.last_memory_usage = 0.0
        
        # 监控定时器
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self._check_memory)
        
        # 优化策略
        self.optimization_strategies = [
            self._basic_gc_cleanup,
            self._aggressive_gc_cleanup,
            self._clear_caches,
            self._emergency_cleanup
        ]
        
        self.current_strategy_index = 0
        
    def start_monitoring(self):
        """开始内存监控"""
        if not self.monitoring_enabled:
            return
        
        print(f"[INFO] 开始内存监控，限制: {self.memory_limit}MB")
        self.monitor_timer.start(self.monitoring_interval)
    
    def stop_monitoring(self):
        """停止内存监控"""
        self.monitor_timer.stop()
        print("[INFO] 内存监控已停止")
    
    def _check_memory(self):
        """检查内存使用"""
        try:
            memory_mb = self._get_memory_usage()
            self.last_memory_usage = memory_mb
            
            # 计算使用率
            usage_ratio = memory_mb / self.memory_limit
            
            if usage_ratio >= self.critical_threshold:
                # 危险级别
                print(f"[CRITICAL] 内存使用危险: {memory_mb:.1f}MB ({usage_ratio:.1%})")
                self.memory_critical.emit(memory_mb)
                self._emergency_memory_optimization()
                
            elif usage_ratio >= self.warning_threshold:
                # 警告级别
                print(f"[WARN] 内存使用警告: {memory_mb:.1f}MB ({usage_ratio:.1%})")
                self.memory_warning.emit(memory_mb)
                self._optimize_memory()
                
            else:
                # 正常级别
                if hasattr(self, '_last_warning_time'):
                    # 如果之前有警告，现在恢复正常
                    print(f"[OK] 内存使用正常: {memory_mb:.1f}MB ({usage_ratio:.1%})")
                    delattr(self, '_last_warning_time')
            
        except Exception as e:
            print(f"[ERROR] 内存检查失败: {e}")
    
    def _get_memory_usage(self) -> float:
        """获取当前内存使用量（MB）"""
        try:
            import psutil
            process = psutil.Process()
            memory_bytes = process.memory_info().rss
            return memory_bytes / 1024 / 1024
        except ImportError:
            # 如果psutil不可用，使用简单的估算
            return self._estimate_memory_usage()
        except Exception as e:
            print(f"[WARN] 获取内存使用失败: {e}")
            return 0.0
    
    def _estimate_memory_usage(self) -> float:
        """估算内存使用量"""
        try:
            # 简单的内存估算
            import sys
            
            # 获取对象数量作为内存使用的粗略指标
            object_count = len(gc.get_objects())
            
            # 粗略估算：每1000个对象约1MB（这只是一个粗略的估算）
            estimated_mb = object_count / 1000
            
            return min(estimated_mb, self.memory_limit)  # 不超过限制
            
        except Exception:
            return 100.0  # 默认估算值
    
    def _optimize_memory(self):
        """优化内存使用"""
        try:
            if self.current_strategy_index < len(self.optimization_strategies):
                strategy = self.optimization_strategies[self.current_strategy_index]
                
                # 记录优化前的内存
                before_memory = self._get_memory_usage()
                
                # 执行优化策略
                strategy()
                
                # 记录优化后的内存
                after_memory = self._get_memory_usage()
                
                # 计算优化效果
                saved_memory = before_memory - after_memory
                
                if saved_memory > 0:
                    print(f"[OK] 内存优化成功，释放: {saved_memory:.1f}MB")
                    self.memory_optimized.emit(after_memory)
                    # 重置策略索引
                    self.current_strategy_index = 0
                else:
                    # 当前策略无效，尝试下一个
                    self.current_strategy_index += 1
                    if self.current_strategy_index < len(self.optimization_strategies):
                        print(f"[INFO] 尝试下一个优化策略: {self.current_strategy_index}")
                        self._optimize_memory()
                    else:
                        print("[WARN] 所有优化策略都已尝试")
                        self.current_strategy_index = 0
            
        except Exception as e:
            print(f"[ERROR] 内存优化失败: {e}")
    
    def _emergency_memory_optimization(self):
        """紧急内存优化"""
        try:
            print("[INFO] 执行紧急内存优化")
            
            # 执行所有优化策略
            for strategy in self.optimization_strategies:
                try:
                    strategy()
                except Exception as e:
                    print(f"[WARN] 优化策略失败: {e}")
            
            # 检查优化效果
            current_memory = self._get_memory_usage()
            usage_ratio = current_memory / self.memory_limit
            
            if usage_ratio < self.critical_threshold:
                print(f"[OK] 紧急优化成功: {current_memory:.1f}MB")
                self.memory_optimized.emit(current_memory)
            else:
                print(f"[WARN] 紧急优化效果有限: {current_memory:.1f}MB")
            
        except Exception as e:
            print(f"[ERROR] 紧急内存优化失败: {e}")
    
    def _basic_gc_cleanup(self):
        """基础垃圾回收清理"""
        gc.collect()
        print("[INFO] 执行基础垃圾回收")
    
    def _aggressive_gc_cleanup(self):
        """激进垃圾回收清理"""
        # 多次垃圾回收
        for _ in range(3):
            gc.collect()
        
        # 调整垃圾回收阈值
        gc.set_threshold(700, 10, 10)
        
        print("[INFO] 执行激进垃圾回收")
    
    def _clear_caches(self):
        """清理缓存"""
        try:
            # 清理样式缓存
            from .style_manager import get_style_manager
            style_manager = get_style_manager()
            if hasattr(style_manager, 'style_cache'):
                style_manager.style_cache.clear()
            
            # 清理其他缓存
            import sys
            if hasattr(sys, '_clear_type_cache'):
                sys._clear_type_cache()
            
            print("[INFO] 清理缓存完成")
            
        except Exception as e:
            print(f"[WARN] 清理缓存失败: {e}")
    
    def _emergency_cleanup(self):
        """紧急清理"""
        try:
            # 强制清理所有可能的缓存
            self._clear_caches()
            
            # 多次强制垃圾回收
            for _ in range(5):
                gc.collect()
            
            # 尝试释放未使用的内存
            try:
                import ctypes
                libc = ctypes.CDLL("libc.so.6")
                libc.malloc_trim(0)
            except:
                pass  # 在Windows上可能不可用
            
            print("[INFO] 紧急清理完成")
            
        except Exception as e:
            print(f"[WARN] 紧急清理失败: {e}")
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """获取内存统计信息"""
        current_memory = self._get_memory_usage()
        usage_ratio = current_memory / self.memory_limit
        
        return {
            "current_memory_mb": current_memory,
            "memory_limit_mb": self.memory_limit,
            "usage_ratio": usage_ratio,
            "warning_threshold": self.warning_threshold,
            "critical_threshold": self.critical_threshold,
            "monitoring_enabled": self.monitoring_enabled,
            "monitoring_interval": self.monitoring_interval,
            "is_warning": usage_ratio >= self.warning_threshold,
            "is_critical": usage_ratio >= self.critical_threshold
        }
    
    def set_memory_limit(self, limit_mb: float):
        """设置内存限制"""
        self.memory_limit = limit_mb
        print(f"[INFO] 内存限制已设置为: {limit_mb}MB")
    
    def set_monitoring_interval(self, interval_ms: int):
        """设置监控间隔"""
        self.monitoring_interval = interval_ms
        if self.monitor_timer.isActive():
            self.monitor_timer.setInterval(interval_ms)
        print(f"[INFO] 监控间隔已设置为: {interval_ms}ms")

# 全局内存监控器实例
_memory_monitor = None

def get_memory_monitor() -> MemoryMonitor:
    """获取全局内存监控器实例"""
    global _memory_monitor
    if _memory_monitor is None:
        _memory_monitor = MemoryMonitor()
    return _memory_monitor

def start_memory_monitoring():
    """开始内存监控的便捷函数"""
    monitor = get_memory_monitor()
    monitor.start_monitoring()

def get_current_memory_usage() -> float:
    """获取当前内存使用量的便捷函数"""
    monitor = get_memory_monitor()
    return monitor._get_memory_usage()

__all__ = [
    'MemoryMonitor',
    'get_memory_monitor',
    'start_memory_monitoring',
    'get_current_memory_usage'
]
