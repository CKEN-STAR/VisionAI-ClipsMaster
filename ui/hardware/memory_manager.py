"""
UI内存管理器
提供UI相关的内存管理和优化功能
"""

import gc
import time
import threading
from typing import Dict, Any, Optional, List, Callable
from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from PyQt6.QtWidgets import QWidget, QApplication

class UIMemoryManager(QObject):
    """UI内存管理器"""
    
    memory_warning = pyqtSignal(float)  # 内存使用率警告
    memory_cleaned = pyqtSignal(int)    # 清理的内存量(MB)
    memory_status_changed = pyqtSignal(dict)  # 内存状态变化
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.parent_widget = parent
        self.memory_stats = {
            'peak_usage_mb': 0,
            'current_usage_mb': 0,
            'cleanups_performed': 0,
            'widgets_tracked': 0
        }
        self.tracked_widgets: List[QWidget] = []
        self.cleanup_callbacks: List[Callable] = []
        self.monitoring_enabled = False
        self.warning_threshold = 80.0  # 80%内存使用率警告
        
        # 监控定时器（线程安全初始化）
        self.monitor_timer = None
        self._init_timer_safely()

    def _init_timer_safely(self):
        """线程安全地初始化定时器"""
        try:
            from PyQt6.QtWidgets import QApplication
            from PyQt6.QtCore import QThread, QTimer

            app = QApplication.instance()
            if app and QThread.currentThread() == app.thread():
                # 在主线程中直接初始化
                self.monitor_timer = QTimer(self)
                self.monitor_timer.timeout.connect(self._monitor_memory)
            else:
                # 不在主线程中，使用QTimer.singleShot延迟初始化
                QTimer.singleShot(0, self._init_timer_in_main_thread)

        except Exception as e:
            print(f"[WARN] 定时器初始化失败: {e}")

    def _init_timer_in_main_thread(self):
        """在主线程中初始化定时器"""
        try:
            from PyQt6.QtCore import QTimer
            self.monitor_timer = QTimer(self)
            self.monitor_timer.timeout.connect(self._monitor_memory)
        except Exception as e:
            print(f"[WARN] 主线程定时器初始化失败: {e}")

    def configure_memory(self, tier: str):
        """
        配置内存管理策略

        Args:
            tier: 性能等级 ("Low", "Medium", "High", "Ultra")
        """
        try:
            tier_lower = tier.lower()

            if tier_lower == "low":
                self.warning_threshold = 70.0  # 低配设备更早警告
                print("[OK] 内存配置: 低配模式")
            elif tier_lower == "medium":
                self.warning_threshold = 80.0
                print("[OK] 内存配置: 中等模式")
            elif tier_lower == "high":
                self.warning_threshold = 85.0
                print("[OK] 内存配置: 高配模式")
            else:  # ultra
                self.warning_threshold = 90.0
                print("[OK] 内存配置: 超高配模式")

        except Exception as e:
            print(f"[WARN] 配置内存失败: {e}")

    def activate(self):
        """激活内存管理器"""
        try:
            self.start_monitoring()
            print("[OK] 内存管理器已激活")
        except Exception as e:
            print(f"[WARN] 激活内存管理器失败: {e}")

    def start_monitoring(self, interval_ms: int = 5000):
        """
        开始内存监控（线程安全版本）

        Args:
            interval_ms: 监控间隔（毫秒）
        """
        try:
            from PyQt6.QtWidgets import QApplication
            from PyQt6.QtCore import QThread, QTimer

            # 检查是否在主线程中
            app = QApplication.instance()
            if app and QThread.currentThread() != app.thread():
                # 不在主线程中，使用QTimer.singleShot在主线程中执行
                QTimer.singleShot(0, lambda: self._start_monitoring_in_main_thread(interval_ms))
                print(f"[OK] 内存监控将在主线程中启动，间隔: {interval_ms}ms")
                return

            # 在主线程中直接启动
            self._start_monitoring_in_main_thread(interval_ms)

        except Exception as e:
            print(f"[WARN] 启动内存监控失败: {e}")

    def _start_monitoring_in_main_thread(self, interval_ms: int):
        """在主线程中启动监控"""
        try:
            from PyQt6.QtWidgets import QApplication
            from PyQt6.QtCore import QThread

            # 确保在主线程中执行
            app = QApplication.instance()
            if app and QThread.currentThread() != app.thread():
                print(f"[WARN] 仍不在主线程中，延迟启动监控")
                return

            # 确保定时器已初始化
            if not self.monitor_timer:
                self._init_timer_in_main_thread()

            if self.monitor_timer:
                self.monitoring_enabled = True
                # 确保定时器在主线程中
                if self.monitor_timer.thread() != app.thread():
                    self.monitor_timer.moveToThread(app.thread())

                self.monitor_timer.start(interval_ms)
                print(f"[OK] 内存监控已在主线程中启动，间隔: {interval_ms}ms")
            else:
                print(f"[WARN] 监控定时器初始化失败")

        except Exception as e:
            print(f"[WARN] 在主线程中启动内存监控失败: {e}")
            self.monitoring_enabled = False
    
    def stop_monitoring(self):
        """停止内存监控"""
        try:
            self.monitoring_enabled = False
            self.monitor_timer.stop()
            print("[OK] 内存监控已停止")
            
        except Exception as e:
            print(f"[WARN] 停止内存监控失败: {e}")
    
    def _monitor_memory(self):
        """监控内存使用"""
        try:
            if not self.monitoring_enabled:
                return
            
            usage_info = self.get_memory_usage()
            current_usage = usage_info['usage_percent']
            
            # 更新统计
            self.memory_stats['current_usage_mb'] = usage_info['used_mb']
            if usage_info['used_mb'] > self.memory_stats['peak_usage_mb']:
                self.memory_stats['peak_usage_mb'] = usage_info['used_mb']
            
            # 发出内存状态变化信号
            status_info = {
                'usage_percent': current_usage,
                'used_mb': usage_info['used_mb'],
                'available_mb': usage_info['available_mb'],
                'total_mb': usage_info['total_mb']
            }

            # 安全地发出信号
            try:
                if hasattr(self, 'memory_status_changed'):
                    self.memory_status_changed.emit(status_info)
            except Exception as e:
                print(f"[WARN] 发出内存状态信号失败: {e}")

            # 检查是否需要警告
            if current_usage > self.warning_threshold:
                self.memory_warning.emit(current_usage)

                # 自动清理
                if current_usage > 90.0:  # 超过90%自动清理
                    self.cleanup_memory()
                    
        except Exception as e:
            print(f"[WARN] 内存监控异常: {e}")
    
    def get_memory_usage(self) -> Dict[str, float]:
        """获取内存使用情况"""
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
            print(f"[WARN] 获取内存使用失败: {e}")
            return {
                'total_mb': 0,
                'used_mb': 0,
                'available_mb': 0,
                'usage_percent': 0.0
            }
    
    def track_widget(self, widget: QWidget):
        """跟踪组件内存使用"""
        try:
            if widget and widget not in self.tracked_widgets:
                self.tracked_widgets.append(widget)
                self.memory_stats['widgets_tracked'] += 1
                
                # 连接销毁信号
                widget.destroyed.connect(lambda: self._widget_destroyed(widget))
                
        except Exception as e:
            print(f"[WARN] 跟踪组件失败: {e}")
    
    def _widget_destroyed(self, widget: QWidget):
        """组件销毁时的清理"""
        try:
            if widget in self.tracked_widgets:
                self.tracked_widgets.remove(widget)
                self.memory_stats['widgets_tracked'] -= 1
                
        except Exception as e:
            print(f"[WARN] 组件销毁清理失败: {e}")
    
    def cleanup_memory(self) -> int:
        """
        清理内存
        
        Returns:
            清理的内存量(MB)
        """
        try:
            before_usage = self.get_memory_usage()['used_mb']
            
            # 1. 清理已销毁的组件引用
            self._cleanup_destroyed_widgets()
            
            # 2. 执行自定义清理回调
            for callback in self.cleanup_callbacks:
                try:
                    callback()
                except Exception as e:
                    print(f"[WARN] 清理回调失败: {e}")
            
            # 3. 强制垃圾回收
            gc.collect()
            
            # 4. 清理Qt对象缓存
            self._cleanup_qt_cache()
            
            after_usage = self.get_memory_usage()['used_mb']
            cleaned_mb = max(0, int(before_usage - after_usage))
            
            # 更新统计
            self.memory_stats['cleanups_performed'] += 1
            
            # 发送信号
            self.memory_cleaned.emit(cleaned_mb)
            
            print(f"[OK] 内存清理完成，释放: {cleaned_mb}MB")
            return cleaned_mb
            
        except Exception as e:
            print(f"[WARN] 内存清理失败: {e}")
            return 0
    
    def _cleanup_destroyed_widgets(self):
        """清理已销毁的组件"""
        try:
            # 过滤掉已销毁的组件
            valid_widgets = []
            for widget in self.tracked_widgets:
                try:
                    # 尝试访问组件属性来检查是否有效
                    _ = widget.isVisible()
                    valid_widgets.append(widget)
                except RuntimeError:
                    # 组件已被销毁
                    pass
            
            removed_count = len(self.tracked_widgets) - len(valid_widgets)
            self.tracked_widgets = valid_widgets
            self.memory_stats['widgets_tracked'] = len(valid_widgets)
            
            if removed_count > 0:
                print(f"[OK] 清理了 {removed_count} 个已销毁的组件引用")
                
        except Exception as e:
            print(f"[WARN] 清理已销毁组件失败: {e}")
    
    def _cleanup_qt_cache(self):
        """清理Qt缓存"""
        try:
            app = QApplication.instance()
            if app:
                # 清理样式表缓存
                app.setStyleSheet(app.styleSheet())
                
                # 清理字体缓存
                from PyQt6.QtGui import QFontDatabase
                QFontDatabase.removeAllApplicationFonts()
                
        except Exception as e:
            print(f"[WARN] 清理Qt缓存失败: {e}")
    
    def add_cleanup_callback(self, callback: Callable):
        """添加清理回调函数"""
        if callback and callback not in self.cleanup_callbacks:
            self.cleanup_callbacks.append(callback)
    
    def remove_cleanup_callback(self, callback: Callable):
        """移除清理回调函数"""
        if callback in self.cleanup_callbacks:
            self.cleanup_callbacks.remove(callback)
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """获取内存统计信息"""
        stats = self.memory_stats.copy()
        stats.update(self.get_memory_usage())
        stats['tracked_widgets'] = len(self.tracked_widgets)
        stats['cleanup_callbacks'] = len(self.cleanup_callbacks)
        stats['monitoring_enabled'] = self.monitoring_enabled
        return stats
    
    def set_warning_threshold(self, threshold: float):
        """设置内存警告阈值"""
        if 0 < threshold <= 100:
            self.warning_threshold = threshold
            print(f"[OK] 内存警告阈值已设置为: {threshold}%")

class MemoryWatcher(QObject):
    """内存监视器（轻量级）"""

    # 信号定义
    memory_warning = pyqtSignal(str)
    memory_status_changed = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.last_check_time = time.time()
        self.check_interval = 10.0  # 10秒
        self.monitoring = False
        self.monitor_timer = None
    
    def should_cleanup(self) -> bool:
        """检查是否应该清理内存"""
        try:
            current_time = time.time()
            if current_time - self.last_check_time < self.check_interval:
                return False
            
            self.last_check_time = current_time
            
            # 简单的内存检查
            try:
                import psutil
                memory = psutil.virtual_memory()
                return memory.percent > 85.0
            except ImportError:
                return False
                
        except Exception:
            return False
    
    def quick_cleanup(self):
        """快速清理"""
        try:
            gc.collect()
        except Exception:
            pass

    def start_monitoring(self, interval_ms: int = 5000):
        """开始内存监控"""
        try:
            if self.monitoring:
                return

            self.monitoring = True
            self.check_interval = interval_ms / 1000.0  # 转换为秒

            # 创建定时器
            from PyQt6.QtCore import QTimer
            self.monitor_timer = QTimer()
            self.monitor_timer.timeout.connect(self._check_memory)
            self.monitor_timer.start(interval_ms)

            print(f"[OK] 内存监控已启动，间隔: {interval_ms}ms")

        except Exception as e:
            print(f"[ERROR] 启动内存监控失败: {e}")

    def stop_monitoring(self):
        """停止内存监控"""
        try:
            if self.monitor_timer:
                self.monitor_timer.stop()
                self.monitor_timer = None

            self.monitoring = False
            print("[OK] 内存监控已停止")

        except Exception as e:
            print(f"[ERROR] 停止内存监控失败: {e}")

    def _check_memory(self):
        """检查内存状态"""
        try:
            import psutil
            memory = psutil.virtual_memory()

            # 发送状态更新信号
            status = {
                "percent": memory.percent,
                "available": memory.available,
                "total": memory.total
            }
            self.memory_status_changed.emit(status)

            # 检查是否需要发出警告
            if memory.percent > 85.0:
                warning_msg = f"内存使用率过高: {memory.percent:.1f}%"
                self.memory_warning.emit(warning_msg)

        except Exception as e:
            print(f"[WARN] 内存检查失败: {e}")

# 全局内存管理器实例
_memory_manager: Optional[UIMemoryManager] = None

def get_memory_manager() -> UIMemoryManager:
    """获取全局内存管理器"""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = UIMemoryManager()
    return _memory_manager

def start_memory_monitoring(interval_ms: int = 5000):
    """启动内存监控"""
    manager = get_memory_manager()
    manager.start_monitoring(interval_ms)

def cleanup_ui_memory() -> int:
    """清理UI内存"""
    manager = get_memory_manager()
    return manager.cleanup_memory()

def get_ui_memory_stats() -> Dict[str, Any]:
    """获取UI内存统计"""
    manager = get_memory_manager()
    return manager.get_memory_stats()

__all__ = [
    'UIMemoryManager',
    'MemoryWatcher',
    'get_memory_manager',
    'start_memory_monitoring',
    'cleanup_ui_memory',
    'get_ui_memory_stats'
]
