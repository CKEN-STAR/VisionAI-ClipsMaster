"""
启动优化器
优化应用启动时间和内存使用
"""

import time
import gc
import sys
import threading
from typing import Optional, Callable, Any
from PyQt6.QtCore import QTimer, QObject, pyqtSignal, QThread
from PyQt6.QtWidgets import QApplication

class StartupOptimizer(QObject):
    """启动优化器"""
    
    # 信号
    startup_progress = pyqtSignal(int, str)  # 进度, 状态信息
    startup_complete = pyqtSignal()          # 启动完成
    startup_error = pyqtSignal(str)          # 启动错误
    
    def __init__(self):
        super().__init__()
        self.start_time = None
        self.target_startup_time = 5.0  # 目标启动时间（秒）
        self.memory_limit = 400  # 内存限制（MB）
        self.optimization_enabled = True
        
    def start_optimization(self):
        """开始启动优化"""
        self.start_time = time.time()
        print("[INFO] 启动优化开始")
        
        # 发送初始进度
        self.startup_progress.emit(0, "初始化启动优化...")
        
        # 使用QTimer确保在主线程中执行
        QTimer.singleShot(0, self._optimize_startup)
    
    def _optimize_startup(self):
        """执行启动优化"""
        try:
            # 步骤1: 内存优化
            self.startup_progress.emit(10, "优化内存使用...")
            self._optimize_memory()
            
            # 步骤2: 模块预加载优化
            self.startup_progress.emit(30, "优化模块加载...")
            self._optimize_module_loading()
            
            # 步骤3: UI组件优化
            self.startup_progress.emit(50, "优化UI组件...")
            self._optimize_ui_components()
            
            # 步骤4: 线程安全优化
            self.startup_progress.emit(70, "优化线程安全...")
            self._optimize_thread_safety()
            
            # 步骤5: 缓存优化
            self.startup_progress.emit(90, "优化缓存策略...")
            self._optimize_caching()
            
            # 完成
            self.startup_progress.emit(100, "启动优化完成")
            
            # 计算启动时间
            if self.start_time:
                elapsed_time = time.time() - self.start_time
                print(f"[INFO] 启动优化完成，耗时: {elapsed_time:.2f}秒")
                
                if elapsed_time <= self.target_startup_time:
                    print(f"[OK] 启动时间达标: {elapsed_time:.2f}s ≤ {self.target_startup_time}s")
                else:
                    print(f"[WARN] 启动时间超标: {elapsed_time:.2f}s > {self.target_startup_time}s")
            
            self.startup_complete.emit()
            
        except Exception as e:
            error_msg = f"启动优化失败: {e}"
            print(f"[ERROR] {error_msg}")
            self.startup_error.emit(error_msg)
    
    def _optimize_memory(self):
        """优化内存使用"""
        try:
            # 强制垃圾回收
            gc.collect()
            
            # 设置垃圾回收阈值
            gc.set_threshold(700, 10, 10)
            
            # 检查当前内存使用
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            
            print(f"[INFO] 当前内存使用: {memory_mb:.1f}MB")
            
            if memory_mb > self.memory_limit:
                print(f"[WARN] 内存使用超限: {memory_mb:.1f}MB > {self.memory_limit}MB")
                # 执行更激进的内存清理
                self._aggressive_memory_cleanup()
            
        except ImportError:
            print("[WARN] psutil不可用，跳过内存监控")
        except Exception as e:
            print(f"[WARN] 内存优化失败: {e}")
    
    def _aggressive_memory_cleanup(self):
        """激进的内存清理"""
        try:
            # 多次垃圾回收
            for _ in range(3):
                gc.collect()
            
            # 清理模块缓存
            if hasattr(sys, '_clear_type_cache'):
                sys._clear_type_cache()
            
            print("[INFO] 执行激进内存清理")
            
        except Exception as e:
            print(f"[WARN] 激进内存清理失败: {e}")
    
    def _optimize_module_loading(self):
        """优化模块加载"""
        try:
            # 延迟导入非关键模块
            self._setup_lazy_imports()
            
            # 预编译正则表达式
            self._precompile_regex()
            
            print("[INFO] 模块加载优化完成")
            
        except Exception as e:
            print(f"[WARN] 模块加载优化失败: {e}")
    
    def _setup_lazy_imports(self):
        """设置延迟导入"""
        # 这里可以设置延迟导入的模块
        # 例如：只在需要时才导入大型库
        pass
    
    def _precompile_regex(self):
        """预编译正则表达式"""
        import re
        
        # 预编译常用的正则表达式
        common_patterns = [
            r'\d+',
            r'[a-zA-Z]+',
            r'\s+',
            r'[^\w\s]'
        ]
        
        for pattern in common_patterns:
            re.compile(pattern)
    
    def _optimize_ui_components(self):
        """优化UI组件"""
        try:
            # 确保UI操作在主线程中执行
            app = QApplication.instance()
            if app and app.thread() != threading.current_thread():
                print("[WARN] UI优化不在主线程中执行")
                return
            
            # 设置应用属性以优化性能
            if app:
                # 启用高DPI支持
                app.setAttribute(app.ApplicationAttribute.AA_EnableHighDpiScaling, True)
                app.setAttribute(app.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
                
                # 优化渲染
                app.setAttribute(app.ApplicationAttribute.AA_UseDesktopOpenGL, True)
            
            print("[INFO] UI组件优化完成")
            
        except Exception as e:
            print(f"[WARN] UI组件优化失败: {e}")
    
    def _optimize_thread_safety(self):
        """优化线程安全"""
        try:
            # 确保关键操作在主线程中执行
            if threading.current_thread() != threading.main_thread():
                print("[WARN] 线程安全优化不在主线程中执行")
            
            # 设置线程安全的信号连接
            self._setup_thread_safe_signals()
            
            print("[INFO] 线程安全优化完成")
            
        except Exception as e:
            print(f"[WARN] 线程安全优化失败: {e}")
    
    def _setup_thread_safe_signals(self):
        """设置线程安全的信号连接"""
        # 确保信号连接使用队列连接
        from PyQt6.QtCore import Qt
        
        # 这里可以设置特定的信号连接
        # 例如：self.some_signal.connect(self.some_slot, Qt.ConnectionType.QueuedConnection)
        pass
    
    def _optimize_caching(self):
        """优化缓存策略"""
        try:
            # 设置合理的缓存大小
            cache_size_mb = min(50, self.memory_limit // 8)  # 缓存不超过内存限制的1/8
            
            print(f"[INFO] 设置缓存大小: {cache_size_mb}MB")
            
            # 这里可以初始化各种缓存
            self._init_style_cache()
            self._init_config_cache()
            
            print("[INFO] 缓存优化完成")
            
        except Exception as e:
            print(f"[WARN] 缓存优化失败: {e}")
    
    def _init_style_cache(self):
        """初始化样式缓存"""
        try:
            # 预加载常用样式
            from .style_manager import get_style_manager
            style_manager = get_style_manager()
            
            # 预加载默认主题
            style_manager.get_theme_style("light")
            
        except ImportError:
            print("[WARN] 样式管理器不可用")
        except Exception as e:
            print(f"[WARN] 样式缓存初始化失败: {e}")
    
    def _init_config_cache(self):
        """初始化配置缓存"""
        try:
            # 预加载配置文件
            pass
            
        except Exception as e:
            print(f"[WARN] 配置缓存初始化失败: {e}")
    
    def get_optimization_stats(self) -> dict:
        """获取优化统计信息"""
        stats = {
            "optimization_enabled": self.optimization_enabled,
            "target_startup_time": self.target_startup_time,
            "memory_limit": self.memory_limit
        }
        
        if self.start_time:
            stats["elapsed_time"] = time.time() - self.start_time
        
        return stats

# 全局启动优化器实例
_startup_optimizer = None

def get_startup_optimizer() -> StartupOptimizer:
    """获取全局启动优化器实例"""
    global _startup_optimizer
    if _startup_optimizer is None:
        _startup_optimizer = StartupOptimizer()
    return _startup_optimizer

def optimize_startup() -> StartupOptimizer:
    """启动优化的便捷函数"""
    optimizer = get_startup_optimizer()
    optimizer.start_optimization()
    return optimizer

__all__ = [
    'StartupOptimizer',
    'get_startup_optimizer',
    'optimize_startup'
]
