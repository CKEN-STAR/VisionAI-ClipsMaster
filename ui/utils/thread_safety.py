"""
线程安全管理器
确保UI操作在主线程中执行
"""

import threading
import traceback
from typing import Callable, Any, Optional
from PyQt6.QtCore import QObject, QTimer, QMetaObject, Qt, Q_ARG, pyqtSlot, pyqtSignal

class ThreadSafetyManager(QObject):
    """线程安全管理器"""
    
    # 信号
    operation_completed = pyqtSignal(object)  # 操作完成
    operation_failed = pyqtSignal(str)        # 操作失败
    
    def __init__(self):
        super().__init__()
        self.main_thread = threading.main_thread()
        self.debug_mode = False
    
    def is_main_thread(self) -> bool:
        """检查当前是否在主线程中"""
        return threading.current_thread() == self.main_thread
    
    def run_in_main_thread(self, func: Callable, *args, **kwargs) -> Any:
        """
        确保函数在主线程中运行
        
        Args:
            func: 要执行的函数
            *args: 函数参数
            **kwargs: 函数关键字参数
            
        Returns:
            函数返回值（如果在主线程中直接执行）
            None（如果通过信号在主线程中执行）
        """
        if self.is_main_thread():
            # 已经在主线程中，直接执行
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if self.debug_mode:
                    print(f"[ERROR] 主线程执行失败: {e}")
                    traceback.print_exc()
                self.operation_failed.emit(str(e))
                return None
        else:
            # 不在主线程中，使用QTimer.singleShot确保在主线程中执行
            if self.debug_mode:
                print(f"[INFO] 将操作转移到主线程执行: {func.__name__}")
            
            # 使用QTimer.singleShot
            QTimer.singleShot(0, lambda: self._execute_in_main_thread(func, args, kwargs))
            return None
    
    def _execute_in_main_thread(self, func: Callable, args: tuple, kwargs: dict):
        """在主线程中执行函数"""
        try:
            result = func(*args, **kwargs)
            self.operation_completed.emit(result)
        except Exception as e:
            if self.debug_mode:
                print(f"[ERROR] 主线程执行失败: {e}")
                traceback.print_exc()
            self.operation_failed.emit(str(e))
    
    def invoke_method(self, obj: QObject, method_name: str, *args) -> bool:
        """
        使用QMetaObject.invokeMethod在主线程中调用对象方法
        
        Args:
            obj: 目标对象
            method_name: 方法名
            *args: 方法参数
            
        Returns:
            是否成功调用
        """
        try:
            if not obj:
                if self.debug_mode:
                    print("[ERROR] 无效的对象")
                return False
            
            # 构建参数
            q_args = [Q_ARG(type(arg), arg) for arg in args]
            
            # 调用方法
            return QMetaObject.invokeMethod(
                obj, 
                method_name,
                Qt.ConnectionType.QueuedConnection,
                *q_args
            )
        except Exception as e:
            if self.debug_mode:
                print(f"[ERROR] 方法调用失败: {e}")
                traceback.print_exc()
            return False
    
    def safe_connect(self, signal, slot, connection_type=None):
        """
        安全地连接信号和槽
        
        Args:
            signal: 信号
            slot: 槽函数
            connection_type: 连接类型
            
        Returns:
            是否成功连接
        """
        try:
            if connection_type is None:
                # 如果槽函数不在主线程，使用队列连接
                if not self.is_main_thread():
                    connection_type = Qt.ConnectionType.QueuedConnection
                else:
                    connection_type = Qt.ConnectionType.AutoConnection
            
            # 连接信号和槽
            signal.connect(slot, connection_type)
            return True
            
        except Exception as e:
            if self.debug_mode:
                print(f"[ERROR] 信号连接失败: {e}")
                traceback.print_exc()
            return False
    
    def create_safe_slot(self, func: Callable) -> Callable:
        """
        创建线程安全的槽函数
        
        Args:
            func: 原始函数
            
        Returns:
            线程安全的槽函数
        """
        @pyqtSlot(*func.__code__.co_varnames[:func.__code__.co_argcount])
        def safe_slot(*args, **kwargs):
            return self.run_in_main_thread(func, *args, **kwargs)
        
        return safe_slot
    
    def set_debug_mode(self, enabled: bool):
        """设置调试模式"""
        self.debug_mode = enabled
        if enabled:
            print("[INFO] 线程安全管理器调试模式已启用")
        else:
            print("[INFO] 线程安全管理器调试模式已禁用")

# 全局线程安全管理器实例
_thread_safety_manager = None

def get_thread_safety_manager() -> ThreadSafetyManager:
    """获取全局线程安全管理器实例"""
    global _thread_safety_manager
    if _thread_safety_manager is None:
        _thread_safety_manager = ThreadSafetyManager()
    return _thread_safety_manager

def run_in_main_thread(func: Callable, *args, **kwargs) -> Any:
    """确保函数在主线程中运行的便捷函数"""
    manager = get_thread_safety_manager()
    return manager.run_in_main_thread(func, *args, **kwargs)

def is_main_thread() -> bool:
    """检查当前是否在主线程中的便捷函数"""
    manager = get_thread_safety_manager()
    return manager.is_main_thread()

def safe_connect(signal, slot, connection_type=None) -> bool:
    """安全地连接信号和槽的便捷函数"""
    manager = get_thread_safety_manager()
    return manager.safe_connect(signal, slot, connection_type)

def create_safe_slot(func: Callable) -> Callable:
    """创建线程安全的槽函数的便捷函数"""
    manager = get_thread_safety_manager()
    return manager.create_safe_slot(func)

__all__ = [
    'ThreadSafetyManager',
    'get_thread_safety_manager',
    'run_in_main_thread',
    'is_main_thread',
    'safe_connect',
    'create_safe_slot'
]
