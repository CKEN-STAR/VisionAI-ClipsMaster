#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
VisionAI-ClipsMaster UI线程安全管理器
确保所有UI操作都在主线程中安全执行
"""

import logging
import threading
from typing import Callable, Any, Optional
from functools import wraps

logger = logging.getLogger(__name__)

class UIThreadSafetyManager:
    """UI线程安全管理器"""
    
    def __init__(self):
        self.main_thread_id = threading.get_ident()
        self._qt_app = None
        self._main_thread = None
        self._safety_enabled = True
        
        # 尝试获取Qt应用实例
        self._initialize_qt_integration()
    
    def _initialize_qt_integration(self):
        """初始化Qt集成"""
        try:
            from PyQt6.QtWidgets import QApplication
            from PyQt6.QtCore import QThread, QMetaObject, Qt, QTimer
            
            # 获取当前应用实例
            self._qt_app = QApplication.instance()
            if self._qt_app is None:
                logger.warning("⚠️ 没有找到QApplication实例")
            else:
                self._main_thread = self._qt_app.thread()
                logger.info("✅ Qt集成初始化成功")
                
            # 保存Qt类引用
            self._QThread = QThread
            self._QMetaObject = QMetaObject
            self._QTimer = QTimer
            self._Qt = Qt
            
        except ImportError as e:
            logger.warning(f"⚠️ Qt集成初始化失败: {e}")
            self._safety_enabled = False
    
    def is_main_thread(self) -> bool:
        """检查当前是否在主线程"""
        if not self._safety_enabled:
            return True
        
        current_thread_id = threading.get_ident()
        return current_thread_id == self.main_thread_id
    
    def is_qt_main_thread(self) -> bool:
        """检查当前是否在Qt主线程"""
        if not self._safety_enabled or not hasattr(self, '_QThread'):
            return True
        
        try:
            current_thread = self._QThread.currentThread()
            return current_thread == self._main_thread
        except:
            return self.is_main_thread()
    
    def execute_in_main_thread(self, func: Callable, *args, **kwargs) -> Any:
        """在主线程中执行函数"""
        if not self._safety_enabled:
            return func(*args, **kwargs)
        
        if self.is_qt_main_thread():
            # 已经在主线程，直接执行
            return func(*args, **kwargs)
        else:
            # 不在主线程，使用Qt的线程安全机制
            return self._invoke_in_main_thread(func, *args, **kwargs)
    
    def _invoke_in_main_thread(self, func: Callable, *args, **kwargs) -> Any:
        """使用Qt机制在主线程中调用函数"""
        try:
            if hasattr(self, '_QMetaObject') and hasattr(self, '_Qt'):
                # 使用QMetaObject.invokeMethod进行线程安全调用
                result = [None]
                exception = [None]
                
                def wrapper():
                    try:
                        result[0] = func(*args, **kwargs)
                    except Exception as e:
                        exception[0] = e
                
                # 使用QTimer.singleShot确保在主线程执行
                if hasattr(self, '_QTimer'):
                    self._QTimer.singleShot(0, wrapper)
                    
                    # 等待执行完成（简单的同步机制）
                    import time
                    timeout = 5.0  # 5秒超时
                    start_time = time.time()
                    
                    while result[0] is None and exception[0] is None:
                        if time.time() - start_time > timeout:
                            raise TimeoutError("主线程调用超时")
                        time.sleep(0.01)
                    
                    if exception[0]:
                        raise exception[0]
                    
                    return result[0]
                else:
                    # 回退到直接调用
                    return func(*args, **kwargs)
            else:
                # 没有Qt支持，直接调用
                return func(*args, **kwargs)
                
        except Exception as e:
            logger.error(f"❌ 主线程调用失败: {e}")
            # 最后的回退：直接调用
            return func(*args, **kwargs)
    
    def safe_ui_call(self, func: Callable, *args, **kwargs) -> Any:
        """安全的UI调用"""
        try:
            return self.execute_in_main_thread(func, *args, **kwargs)
        except Exception as e:
            logger.error(f"❌ 安全UI调用失败: {e}")
            raise
    
    def thread_safe_decorator(self, func: Callable) -> Callable:
        """线程安全装饰器"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            return self.safe_ui_call(func, *args, **kwargs)
        return wrapper
    
    def get_safety_status(self) -> dict:
        """获取线程安全状态"""
        return {
            "safety_enabled": self._safety_enabled,
            "main_thread_id": self.main_thread_id,
            "current_thread_id": threading.get_ident(),
            "is_main_thread": self.is_main_thread(),
            "is_qt_main_thread": self.is_qt_main_thread(),
            "qt_app_available": self._qt_app is not None,
            "qt_integration": hasattr(self, '_QThread')
        }

# 全局线程安全管理器
_thread_safety_manager = None

def get_thread_safety_manager() -> UIThreadSafetyManager:
    """获取全局线程安全管理器"""
    global _thread_safety_manager
    if _thread_safety_manager is None:
        _thread_safety_manager = UIThreadSafetyManager()
    return _thread_safety_manager

def safe_ui_call(func: Callable, *args, **kwargs) -> Any:
    """安全的UI调用（全局函数）"""
    manager = get_thread_safety_manager()
    return manager.safe_ui_call(func, *args, **kwargs)

def thread_safe(func: Callable) -> Callable:
    """线程安全装饰器（全局函数）"""
    manager = get_thread_safety_manager()
    return manager.thread_safe_decorator(func)

def is_main_thread() -> bool:
    """检查是否在主线程（全局函数）"""
    manager = get_thread_safety_manager()
    return manager.is_main_thread()

def test_thread_safety() -> dict:
    """测试线程安全功能"""
    logger.info("🧪 开始测试UI线程安全功能")
    
    manager = get_thread_safety_manager()
    status = manager.get_safety_status()
    
    # 测试基本功能
    test_results = {
        "manager_initialized": manager is not None,
        "safety_enabled": status["safety_enabled"],
        "main_thread_detection": status["is_main_thread"],
        "qt_integration": status["qt_integration"]
    }
    
    # 测试装饰器
    @thread_safe
    def test_decorated_function():
        return "装饰器测试成功"
    
    try:
        result = test_decorated_function()
        test_results["decorator_test"] = result == "装饰器测试成功"
    except Exception as e:
        logger.warning(f"装饰器测试失败: {e}")
        test_results["decorator_test"] = False
    
    # 测试安全调用
    def test_safe_call():
        return "安全调用测试成功"
    
    try:
        result = safe_ui_call(test_safe_call)
        test_results["safe_call_test"] = result == "安全调用测试成功"
    except Exception as e:
        logger.warning(f"安全调用测试失败: {e}")
        test_results["safe_call_test"] = False
    
    success_count = sum(1 for result in test_results.values() if result)
    total_count = len(test_results)
    
    logger.info(f"📊 线程安全测试结果:")
    logger.info(f"  - 成功率: {success_count}/{total_count} ({success_count/total_count:.1%})")
    
    for test_name, result in test_results.items():
        status_icon = "✅" if result else "❌"
        logger.info(f"  - {test_name}: {status_icon}")
    
    return {
        "test_results": test_results,
        "safety_status": status,
        "success_rate": success_count / total_count if total_count > 0 else 0,
        "all_passed": success_count == total_count
    }

# UI组件线程安全包装器
class ThreadSafeUIComponent:
    """线程安全UI组件包装器"""
    
    def __init__(self, component):
        self._component = component
        self._manager = get_thread_safety_manager()
    
    def __getattr__(self, name):
        """代理属性访问"""
        attr = getattr(self._component, name)
        
        if callable(attr):
            # 如果是方法，包装为线程安全调用
            def safe_method(*args, **kwargs):
                return self._manager.safe_ui_call(attr, *args, **kwargs)
            return safe_method
        else:
            # 如果是属性，直接返回
            return attr
    
    def __setattr__(self, name, value):
        """代理属性设置"""
        if name.startswith('_'):
            # 内部属性直接设置
            super().__setattr__(name, value)
        else:
            # UI组件属性通过线程安全方式设置
            def set_attr():
                setattr(self._component, name, value)
            self._manager.safe_ui_call(set_attr)

def make_thread_safe(component):
    """将UI组件包装为线程安全版本"""
    return ThreadSafeUIComponent(component)

if __name__ == "__main__":
    # 独立测试
    test_result = test_thread_safety()
    print(f"线程安全测试完成，成功率: {test_result['success_rate']:.1%}")
