"""
内存守护模块
提供内存监控和保护功能
"""

import gc
import time
import threading
from typing import Dict, Any, Optional, Callable
from PyQt6.QtCore import QObject, QTimer, pyqtSignal

class MemoryGuard(QObject):
    """内存守护器"""
    
    memory_warning = pyqtSignal(float)  # 内存警告信号
    memory_critical = pyqtSignal(float)  # 内存危险信号
    cleanup_performed = pyqtSignal(int)  # 清理完成信号
    
    def __init__(self):
        super().__init__()
        self.monitoring_enabled = False
        self.warning_threshold = 80.0  # 警告阈值
        self.critical_threshold = 90.0  # 危险阈值
        self.cleanup_callbacks: list = []
        
        # 监控定时器
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self._check_memory)
        
        # 统计信息
        self.stats = {
            'checks_performed': 0,
            'warnings_issued': 0,
            'cleanups_performed': 0,
            'memory_freed_mb': 0
        }
    
    def start_memory_monitoring(self, interval_ms: int = 10000) -> bool:
        """
        开始内存监控
        
        Args:
            interval_ms: 监控间隔（毫秒）
            
        Returns:
            是否成功启动
        """
        try:
            self.monitoring_enabled = True
            self.monitor_timer.start(interval_ms)
            print(f"[OK] 内存监控已启动，间隔: {interval_ms}ms")
            return True
        except Exception as e:
            print(f"[WARN] 启动内存监控失败: {e}")
            return False
    
    def stop_memory_monitoring(self):
        """停止内存监控"""
        try:
            self.monitoring_enabled = False
            self.monitor_timer.stop()
            print("[OK] 内存监控已停止")
        except Exception as e:
            print(f"[WARN] 停止内存监控失败: {e}")
    
    def _check_memory(self):
        """检查内存使用情况"""
        try:
            if not self.monitoring_enabled:
                return
            
            self.stats['checks_performed'] += 1
            memory_info = self._get_memory_info()
            usage_percent = memory_info['usage_percent']
            
            # 检查警告阈值
            if usage_percent >= self.critical_threshold:
                self.stats['warnings_issued'] += 1
                self.memory_critical.emit(usage_percent)
                
                # 自动执行清理
                self._perform_emergency_cleanup()
                
            elif usage_percent >= self.warning_threshold:
                self.stats['warnings_issued'] += 1
                self.memory_warning.emit(usage_percent)
            
        except Exception as e:
            print(f"[WARN] 内存检查失败: {e}")
    
    def _get_memory_info(self) -> Dict[str, float]:
        """获取内存信息"""
        try:
            import psutil
            memory = psutil.virtual_memory()
            
            return {
                'total_mb': memory.total / (1024**2),
                'used_mb': memory.used / (1024**2),
                'available_mb': memory.available / (1024**2),
                'usage_percent': memory.percent
            }
            
        except ImportError:
            # 如果psutil不可用，返回模拟数据
            return {
                'total_mb': 8192,
                'used_mb': 4096,
                'available_mb': 4096,
                'usage_percent': 50.0
            }
        except Exception as e:
            print(f"[WARN] 获取内存信息失败: {e}")
            return {
                'total_mb': 0,
                'used_mb': 0,
                'available_mb': 0,
                'usage_percent': 0.0
            }
    
    def _perform_emergency_cleanup(self):
        """执行紧急清理"""
        try:
            before_memory = self._get_memory_info()['used_mb']
            
            # 1. 执行垃圾回收
            gc.collect()
            
            # 2. 调用注册的清理回调
            for callback in self.cleanup_callbacks:
                try:
                    callback()
                except Exception as e:
                    print(f"[WARN] 清理回调执行失败: {e}")
            
            # 3. 再次垃圾回收
            gc.collect()
            
            after_memory = self._get_memory_info()['used_mb']
            freed_mb = max(0, int(before_memory - after_memory))
            
            self.stats['cleanups_performed'] += 1
            self.stats['memory_freed_mb'] += freed_mb
            
            self.cleanup_performed.emit(freed_mb)
            
            print(f"[OK] 紧急内存清理完成，释放: {freed_mb}MB")
            
        except Exception as e:
            print(f"[WARN] 紧急内存清理失败: {e}")
    
    def add_cleanup_callback(self, callback: Callable):
        """添加清理回调函数"""
        if callback and callback not in self.cleanup_callbacks:
            self.cleanup_callbacks.append(callback)
    
    def remove_cleanup_callback(self, callback: Callable):
        """移除清理回调函数"""
        if callback in self.cleanup_callbacks:
            self.cleanup_callbacks.remove(callback)
    
    def manual_cleanup(self) -> int:
        """手动执行清理"""
        try:
            before_memory = self._get_memory_info()['used_mb']
            
            # 执行清理
            gc.collect()
            
            # 调用清理回调
            for callback in self.cleanup_callbacks:
                try:
                    callback()
                except Exception as e:
                    print(f"[WARN] 清理回调执行失败: {e}")
            
            gc.collect()
            
            after_memory = self._get_memory_info()['used_mb']
            freed_mb = max(0, int(before_memory - after_memory))
            
            self.stats['cleanups_performed'] += 1
            self.stats['memory_freed_mb'] += freed_mb
            
            print(f"[OK] 手动内存清理完成，释放: {freed_mb}MB")
            return freed_mb
            
        except Exception as e:
            print(f"[WARN] 手动内存清理失败: {e}")
            return 0
    
    def set_thresholds(self, warning: float, critical: float):
        """设置内存阈值"""
        if 0 < warning < critical <= 100:
            self.warning_threshold = warning
            self.critical_threshold = critical
            print(f"[OK] 内存阈值已设置 - 警告: {warning}%, 危险: {critical}%")
        else:
            print("[WARN] 无效的内存阈值设置")
    
    def get_memory_status(self) -> Dict[str, Any]:
        """获取内存状态"""
        memory_info = self._get_memory_info()
        memory_info.update({
            'warning_threshold': self.warning_threshold,
            'critical_threshold': self.critical_threshold,
            'monitoring_enabled': self.monitoring_enabled,
            'cleanup_callbacks': len(self.cleanup_callbacks)
        })
        return memory_info
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.stats.copy()
    
    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            'checks_performed': 0,
            'warnings_issued': 0,
            'cleanups_performed': 0,
            'memory_freed_mb': 0
        }

# 全局内存守护器实例
_memory_guard: Optional[MemoryGuard] = None

def get_memory_guard() -> MemoryGuard:
    """获取全局内存守护器"""
    global _memory_guard
    if _memory_guard is None:
        _memory_guard = MemoryGuard()
    return _memory_guard

def start_memory_monitoring(interval_ms: int = 10000) -> bool:
    """启动内存监控"""
    guard = get_memory_guard()
    return guard.start_memory_monitoring(interval_ms)

def stop_memory_monitoring():
    """停止内存监控"""
    guard = get_memory_guard()
    guard.stop_memory_monitoring()

def manual_memory_cleanup() -> int:
    """手动内存清理"""
    guard = get_memory_guard()
    return guard.manual_cleanup()

def add_memory_cleanup_callback(callback: Callable):
    """添加内存清理回调"""
    guard = get_memory_guard()
    guard.add_cleanup_callback(callback)

def get_memory_status() -> Dict[str, Any]:
    """获取内存状态"""
    guard = get_memory_guard()
    return guard.get_memory_status()

def set_memory_thresholds(warning: float = 80.0, critical: float = 90.0):
    """设置内存阈值"""
    guard = get_memory_guard()
    guard.set_thresholds(warning, critical)

__all__ = [
    'MemoryGuard',
    'get_memory_guard',
    'start_memory_monitoring',
    'stop_memory_monitoring',
    'manual_memory_cleanup',
    'add_memory_cleanup_callback',
    'get_memory_status',
    'set_memory_thresholds'
]
