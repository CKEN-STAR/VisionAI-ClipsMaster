#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
线程安全工具模块

提供PyQt6线程安全的工具函数和装饰器。
"""

import threading
from functools import wraps
from typing import Callable, Any

try:
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import QThread, QTimer, QMetaObject, Qt
    QT_AVAILABLE = True
except ImportError:
    QT_AVAILABLE = False

def is_main_thread() -> bool:
    """检查是否在主线程中"""
    if not QT_AVAILABLE:
        return True
    
    app = QApplication.instance()
    if not app:
        return True
    
    return QThread.currentThread() == app.thread()

def ensure_main_thread(func: Callable) -> Callable:
    """装饰器：确保函数在主线程中执行"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if is_main_thread():
            return func(*args, **kwargs)
        else:
            print(f"[WARN] 函数 {func.__name__} 不在主线程中执行")
            # 使用QTimer.singleShot在主线程中执行
            if QT_AVAILABLE:
                QTimer.singleShot(0, lambda: func(*args, **kwargs))
            else:
                return func(*args, **kwargs)
    return wrapper

def safe_timer_create(parent=None, interval=1000, single_shot=False):
    """安全创建定时器"""
    if not QT_AVAILABLE:
        return None
    
    if is_main_thread():
        timer = QTimer(parent)
        timer.setInterval(interval)
        timer.setSingleShot(single_shot)
        return timer
    else:
        print("[WARN] 定时器不在主线程中创建")
        return None

class ThreadSafeSignalEmitter:
    """线程安全的信号发射器"""
    
    def __init__(self, signal):
        self.signal = signal
    
    def emit_safe(self, *args, **kwargs):
        """安全发射信号"""
        if is_main_thread():
            self.signal.emit(*args, **kwargs)
        else:
            # 使用QMetaObject.invokeMethod在主线程中发射
            if QT_AVAILABLE:
                QMetaObject.invokeMethod(
                    self.signal.parent(),
                    lambda: self.signal.emit(*args, **kwargs),
                    Qt.ConnectionType.QueuedConnection
                )
