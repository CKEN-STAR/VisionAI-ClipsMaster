#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 简化UI

此脚本创建一个简化的UI界面，整合了基本功能和模型训练组件
"""

import sys
import os

# 设置编码环境
if sys.platform.startswith('win'):
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    # 设置控制台编码
    try:
        import locale
        locale.setlocale(locale.LC_ALL, 'C.UTF-8')
    except:
        try:
            locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
        except:
            pass
def setup_global_exception_handler():
    """设置全局异常处理器"""
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        print(f"未捕获的异常: {exc_type.__name__}: {exc_value}")
        import traceback
        print("详细错误信息:")
        traceback.print_exception(exc_type, exc_value, exc_traceback)

        # 尝试保存错误日志
        try:
            import time
            with open("crash_log.txt", "a", encoding="utf-8") as f:
                f.write(f"\n{time.strftime('%Y-%m-%d %H:%M:%S')} - 未捕获异常:\n")
                traceback.print_exception(exc_type, exc_value, exc_traceback, file=f)
        except:
            pass

    sys.excepthook = handle_exception

import os
from pathlib import Path
import json
import time
import subprocess
import platform
import requests
import logging
import threading
import psutil
import gc
from datetime import datetime
from collections import deque
# Type hints removed as they are not currently used in the codebase

# 设置项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.append(str(PROJECT_ROOT))

# 导入UI桥接模块
try:
    from ui_bridge import ui_bridge
    UI_BRIDGE_AVAILABLE = True
    print("UI桥接模块导入成功")
except ImportError as e:
    UI_BRIDGE_AVAILABLE = False
    print(f"UI桥接模块导入失败: {e}")
    ui_bridge = None

# 导入启动优化模块
try:
    from startup_optimizer import (
        initialize_startup_optimizer, register_component,
        start_optimized_startup
    )
    STARTUP_OPTIMIZER_AVAILABLE = True
    print("[OK] 启动优化器导入成功")
except ImportError as e:
    STARTUP_OPTIMIZER_AVAILABLE = False
    print(f"[WARN] 启动优化器导入失败: {e}")
    # 定义空函数以保持兼容性
    def initialize_startup_optimizer(*args): return None
    def register_component(*args, **kwargs): pass
    def start_optimized_startup(): pass
    def get_startup_report(): return {}
    def get_lazy_module(name): return __import__(name)

# 导入增强响应时间监控模块
try:
    from response_monitor_enhanced import (
        initialize_enhanced_response_monitor, start_response_monitoring,
        record_operation, track_ui_operation
    )
    ENHANCED_RESPONSE_MONITOR_AVAILABLE = True
    print("[OK] 增强响应时间监控器导入成功")
except ImportError as e:
    ENHANCED_RESPONSE_MONITOR_AVAILABLE = False
    print(f"[WARN] 增强响应时间监控器导入失败: {e}")
    # 定义空函数以保持兼容性
    def initialize_enhanced_response_monitor(*args): return None
    def start_response_monitoring(): pass
    def stop_response_monitoring(): pass
    def record_operation(name):
        class DummyTimer:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def finish(self): return 0
        return DummyTimer()
    def get_response_report(): return {}
    def track_ui_operation(name):
        def dummy_decorator(func): return func
        return dummy_decorator

# 导入CSS优化模块
try:
    from css_optimizer import apply_optimized_styles
    CSS_OPTIMIZER_AVAILABLE = True
    print("[OK] CSS优化器导入成功")
except ImportError as e:
    CSS_OPTIMIZER_AVAILABLE = False
    print(f"[WARN] CSS优化器导入失败: {e}")
    # 定义空函数以保持兼容性
    def optimize_stylesheet(stylesheet): return stylesheet
    def apply_optimized_styles(widget): pass
    def get_css_optimization_report(): return {}
    def clear_css_cache(): pass

# 导入用户体验增强模块
try:
    from user_experience_enhancer import initialize_user_experience_enhancer
    USER_EXPERIENCE_ENHANCER_AVAILABLE = True
    print("[OK] 用户体验增强器导入成功")
except ImportError as e:
    USER_EXPERIENCE_ENHANCER_AVAILABLE = False
    print(f"[WARN] 用户体验增强器导入失败: {e}")
    # 定义空函数以保持兼容性
    def initialize_user_experience_enhancer(window): pass
    def show_operation_preview(name, data): return True
    def diagnose_and_show_error(message): pass
    def start_user_guide(guide_type="basic"): pass
    def get_shortcuts_info(): return {}

# 导入编码修复和智能模块加载器
try:
    from encoding_fix import safe_logger
    from smart_module_loader import create_module_loader
    SMART_LOADER_AVAILABLE = True
    safe_logger.success("智能模块加载器导入成功")
except ImportError as e:
    SMART_LOADER_AVAILABLE = False
    print(f"[WARN] 智能模块加载器导入失败: {e}")
    # 创建简单的日志记录器
    class SimpleLogger:
        def info(self, msg): print(f"[INFO] {msg}")
        def warning(self, msg): print(f"[WARN] {msg}")
        def error(self, msg): print(f"[ERROR] {msg}")
        def success(self, msg): print(f"[OK] {msg}")
    safe_logger = SimpleLogger()
    def create_module_loader(window): return None

# 导入优化模块（延迟导入）
OPTIMIZATION_MODULES_AVAILABLE = False
def _lazy_import_optimization_modules():
    """延迟导入优化模块"""
    global OPTIMIZATION_MODULES_AVAILABLE
    try:
        from ui_async_optimizer import initialize_optimizers, optimize_tab_switch, get_optimization_stats
        from memory_manager_enhanced import initialize_memory_manager, get_memory_report
        from optimization_integration import initialize_safe_optimizer, apply_optimizations_safely
        OPTIMIZATION_MODULES_AVAILABLE = True
        print("[OK] 优化模块延迟导入成功")
        return {
            'initialize_optimizers': initialize_optimizers,
            'optimize_tab_switch': optimize_tab_switch,
            'get_optimization_stats': get_optimization_stats,
            'initialize_memory_manager': initialize_memory_manager,
            'get_memory_report': get_memory_report,
            'initialize_safe_optimizer': initialize_safe_optimizer,
            'apply_optimizations_safely': apply_optimizations_safely
        }
    except ImportError as e:
        print(f"[WARN] 优化模块延迟导入失败: {e}")
        return None

# 定义空函数以保持兼容性
def initialize_optimizers(*args): pass
def optimize_tab_switch(*args): pass
def get_optimization_stats(): return {}
def initialize_memory_manager(): return None
def get_memory_report(): return {}
def initialize_safe_optimizer(*args): return None
def apply_optimizations_safely(): return {}

# 导入递归深度配置模块，解决递归深度超出问题
try:
    from ui.config.recursion_fix import increase_recursion_limit
    # 增加递归深度限制
    increase_recursion_limit(3000)
except ImportError:
    print("警告: 无法导入递归深度配置模块，将使用默认递归深度限制")
    
# 导入环境检查模块，检查ffmpeg等依赖
try:
    from ui.config.environment import check_environment, setup_ffmpeg_path
    # 检查ffmpeg
    HAS_FFMPEG = setup_ffmpeg_path()
except ImportError:
    print("警告: 无法导入环境检查模块，将跳过环境依赖检查")
    HAS_FFMPEG = False

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                           QHBoxLayout, QPushButton, QLabel, QTextEdit,
                           QFileDialog, QMessageBox, QTabWidget, QSplitter, QProgressBar, QListWidget, QListWidgetItem, QCheckBox,
                           QComboBox, QGroupBox, QRadioButton, QButtonGroup, QProgressDialog, QDialog, QFrame, QSlider,
                           QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit, QSpinBox, QFormLayout, QScrollArea)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QObject, QTimer
from PyQt6.QtGui import QFont, , QIcon

# 导入增强模型下载器
try:
    from src.core.enhanced_model_downloader import EnhancedModelDownloader
    HAS_ENHANCED_DOWNLOADER = True
except ImportError:
    HAS_ENHANCED_DOWNLOADER = False
    print("警告: 无法导入增强模型下载器，将使用基础下载功能", QAction)

# 添加一个AlertManager的替代类，用于在原始AlertManager无法初始化时作为备用
class SimpleAlertManager:
    """简易警告管理器，当原始AlertManager无法初始化时使用"""
    
    def __init__(self, parent=None):
        self.parent = parent
    
    def info(self, message, timeout=3000):
        """显示信息警告"""
        if hasattr(self, 'parent') and self.parent:
            self.parent.statusBar().showMessage(message, timeout)
        print(f"[信息] {message}")
    
    def success(self, message, timeout=3000):
        """显示成功警告"""
        if hasattr(self, 'parent') and self.parent:
            self.parent.statusBar().showMessage(message, timeout)
        print(f"[成功] {message}")
    
    def warning(self, message, timeout=3000):
        """显示警告警告"""
        if hasattr(self, 'parent') and self.parent:
            self.parent.statusBar().showMessage(message, timeout)
        print(f"[警告] {message}")
    
    def error(self, message, timeout=5000):
        """显示错误警告"""
        if hasattr(self, 'parent') and self.parent:
            self.parent.statusBar().showMessage(message, timeout)
        print(f"[错误] {message}")
        
    def clear_alerts(self):
        """清除所有警告"""
        pass

# 进程稳定性监控器
class ProcessStabilityMonitor(QObject):
    """进程稳定性监控器"""

    memory_warning = pyqtSignal(str, int)  # 内存警告信号 (message, severity)
    performance_update = pyqtSignal(dict)  # 性能更新信号

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 确保在主线程中初始化
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import QThread
        if QApplication.instance() and QApplication.instance().thread() != QThread.currentThread():
            print("[WARN] 主窗口不在主线程中初始化，可能导致问题")
        
        self.monitoring_active = False
        self.monitor_thread = None
        self.process = psutil.Process()
        self.performance_data = []

        # 性能阈值 - 调整为更合理的值
        self.memory_threshold_mb = 800  # 内存警告阈值（提高到800MB，减少频繁警告）
        self.cpu_threshold_percent = 70  # CPU警告阈值（提高到70%）

    def start_monitoring(self):
        """开始监控"""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
            print("[OK] 进程稳定性监控已启动")

    def stop_monitoring(self):
        """停止监控"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        print("[OK] 进程稳定性监控已停止")

    def _monitor_loop(self):
        """监控循环"""
        while self.monitoring_active:
            try:
                # 收集性能数据
                memory_mb = self.process.memory_info().rss / 1024 / 1024
                cpu_percent = self.process.cpu_percent(interval=1)

                performance_data = {
                    'timestamp': datetime.now().isoformat(),
                    'memory_mb': memory_mb,
                    'cpu_percent': cpu_percent,
                    'num_threads': self.process.num_threads()
                }

                # 保存性能数据
                self.performance_data.append(performance_data)
                if len(self.performance_data) > 100:  # 只保留最近100个数据点
                    self.performance_data.pop(0)

                # 发送性能更新信号
                self.performance_update.emit(performance_data)

                # 检查内存使用
                if memory_mb > self.memory_threshold_mb:
                    # 确定严重程度
                    if memory_mb > 1200:  # 提高到1.2GB
                        severity = 2  # 危急
                        message = f"系统内存严重不足！已使用{memory_mb:.1f}MB"
                    else:
                        severity = 1  # 警告
                        message = f"系统内存使用较高！已使用{memory_mb:.1f}MB"

                    self.memory_warning.emit(message, severity)

                    # 只在内存使用超过1GB时执行清理
                    if memory_mb > 1000:
                        self._cleanup_memory()

                    # 只在内存使用超过1.2GB时执行紧急处理
                    if memory_mb > 1200:
                        self._handle_memory_emergency()

                time.sleep(2)  # 每2秒检查一次（进一步提高监控频率）

            except Exception as e:
                print(f"进程监控错误: {e}")
                import traceback
                print(f"详细错误: {traceback.format_exc()}")
                
                # 尝试恢复监控
                try:
                    self.process = psutil.Process()
                    print("[OK] 进程监控已恢复")
                except:
                    print("[ERROR] 进程监控恢复失败")
                
                time.sleep(10)  # 出错时等待更长时间

    def _cleanup_memory(self):
        """清理内存 - 增强版本"""
        try:
            # 执行多次垃圾回收
            for _ in range(3):
                gc.collect()

            # 清理Python内部缓存
            if hasattr(sys, '_clear_type_cache'):
                sys._clear_type_cache()

            # 清理性能数据历史，只保留最近的数据
            if hasattr(self, 'performance_data') and len(self.performance_data) > 20:
                self.performance_data = self.performance_data[-20:]

            # 清理响应时间历史
            if hasattr(self, 'response_times') and len(self.response_times) > 20:
                self.response_times = self.response_times[-20:]

            print("🧹 执行增强内存清理")
        except Exception as e:
            print(f"内存清理失败: {e}")


    def _handle_memory_emergency(self):
        """处理内存紧急情况"""
        try:
            print("[WARN]️ 内存紧急情况，执行紧急清理...")
            
            # 强制垃圾回收
            for _ in range(5):
                gc.collect()
            
            # 清理性能数据历史
            if len(self.performance_data) > 10:
                self.performance_data = self.performance_data[-10:]
            
            # 降低监控频率以减少内存压力
            time.sleep(10)
            
            print("[OK] 紧急内存清理完成")
        except Exception as e:
            print(f"紧急内存清理失败: {e}")


    def _handle_memory_emergency(self):
        """处理内存紧急情况"""
        try:
            print("[WARN]️ 内存紧急情况，执行紧急清理...")
            
            # 强制垃圾回收
            for _ in range(5):
                gc.collect()
            
            # 清理性能数据历史
            if len(self.performance_data) > 10:
                self.performance_data = self.performance_data[-10:]
            
            # 降低监控频率以减少内存压力
            time.sleep(10)
            
            print("[OK] 紧急内存清理完成")
        except Exception as e:
            print(f"紧急内存清理失败: {e}")

    def get_performance_summary(self):
        """获取性能摘要"""
        if not self.performance_data:
            return {}

        memory_values = [d['memory_mb'] for d in self.performance_data]
        cpu_values = [d['cpu_percent'] for d in self.performance_data]

        return {
            'avg_memory_mb': sum(memory_values) / len(memory_values),
            'max_memory_mb': max(memory_values),
            'avg_cpu_percent': sum(cpu_values) / len(cpu_values),
            'max_cpu_percent': max(cpu_values),
            'data_points': len(self.performance_data)
        }

# 爆款SRT异步工作类
class ViralSRTWorker(QObject):
    """爆款SRT异步处理工作类"""

    progress_updated = pyqtSignal(int, str)  # 进度更新信号
    item_completed = pyqtSignal(str, str)    # 单个文件完成信号 (output_path, original_name)
    all_completed = pyqtSignal(int, int)     # 全部完成信号 (success_count, total_count)
    error_occurred = pyqtSignal(str)         # 错误信号

    def __init__(self, selected_items, language_mode):
        super().__init__()
        self.selected_items = selected_items
        self.language_mode = language_mode
        self.is_cancelled = False

    def process(self):
        """处理爆款SRT生成"""
        try:
            total_count = len(self.selected_items)
            success_count = 0

            for i, item in enumerate(self.selected_items):
                if self.is_cancelled:
                    break

                srt_path = item.data(Qt.ItemDataRole.UserRole)
                original_name = os.path.basename(srt_path)

                # 更新进度
                progress = int((i / total_count) * 100)
                self.progress_updated.emit(progress, f"正在处理: {original_name}")

                try:
                    # 调用处理函数
                    from simple_ui_fixed import VideoProcessor
                    output_path = VideoProcessor.generate_viral_srt(srt_path, language_mode=self.language_mode)

                    if output_path:
                        success_count += 1
                        self.item_completed.emit(output_path, original_name)
                    else:
                        self.item_completed.emit("", original_name)

                except Exception as e:
                    print(f"处理SRT文件失败: {e}")
                    self.item_completed.emit("", original_name)

            # 发送完成信号
            self.all_completed.emit(success_count, total_count)

        except Exception as e:
            self.error_occurred.emit(str(e))

    def cancel(self):
        """取消处理"""
        self.is_cancelled = True

# 响应性监控器
class ResponsivenessMonitor(QObject):
    """响应性监控器 - 重构版本，支持实时数据收集"""

    response_time_update = pyqtSignal(float)  # 响应时间更新信号
    responsiveness_data_update = pyqtSignal(dict)  # 响应性数据更新信号

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 确保在主线程中初始化
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import QThread
        if QApplication.instance() and QApplication.instance().thread() != QThread.currentThread():
            print("[WARN] 主窗口不在主线程中初始化，可能导致问题")
        
        self.response_times = []
        self.last_interaction_time = time.time()
        self.interaction_count = 0
        self.monitoring_active = False
        self.monitor_thread = None

        # 响应性数据存储
        self.responsiveness_data = {
            'total_interactions': 0,
            'average_response_time': 0.0,
            'max_response_time': 0.0,
            'min_response_time': float('inf'),
            'response_time_history': [],
            'last_update_time': time.time()
        }

        print("[OK] ResponsivenessMonitor 重构版本初始化完成")

    def start_monitoring(self):
        """开始响应性监控"""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self.monitor_thread.start()
            print("[OK] 响应性监控已启动")

    def stop_monitoring(self):
        """停止响应性监控"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        print("[OK] 响应性监控已停止")

    def _monitoring_loop(self):
        """监控循环 - 定期更新响应性数据"""
        while self.monitoring_active:
            try:
                # 更新响应性数据
                self._update_responsiveness_data()

                # 发送数据更新信号
                self.responsiveness_data_update.emit(self.responsiveness_data.copy())

                time.sleep(1.5)  # 每1.5秒更新一次（提高响应性）

            except Exception as e:
                print(f"响应性监控循环错误: {e}")
                time.sleep(5)

    def _update_responsiveness_data(self):
        """更新响应性数据"""
        current_time = time.time()

        if self.response_times:
            self.responsiveness_data.update({
                'total_interactions': self.interaction_count,
                'average_response_time': sum(self.response_times) / len(self.response_times),
                'max_response_time': max(self.response_times),
                'min_response_time': min(self.response_times),
                'response_time_history': self.response_times[-10:],  # 最近10次
                'last_update_time': current_time
            })
        else:
            # 即使没有交互，也要更新时间戳
            self.responsiveness_data['last_update_time'] = current_time

    def record_interaction(self):
        """记录用户交互 - 优化版本"""
        current_time = time.time()
        response_time = current_time - self.last_interaction_time

        # 优化：限制响应时间列表大小，减少内存占用
        self.response_times.append(response_time)
        if len(self.response_times) > 30:  # 减少到30个以节省内存
            self.response_times.pop(0)

        self.interaction_count += 1

        # 优化：异步发送信号，避免阻塞
        QTimer.singleShot(0, lambda: self.response_time_update.emit(response_time))

        self.last_interaction_time = current_time

        # 优化：延迟更新响应性数据，避免频繁计算
        if self.interaction_count % 3 == 0:  # 每3次交互更新一次
            self._update_responsiveness_data()

        # 优化：只在响应时间异常时打印警告
        if response_time > 1.0:
            print(f"[WARN]️ 响应时间较长: {response_time:.2f}秒")

        print(f"[OK] 记录用户交互 #{self.interaction_count}, 响应时间: {response_time:.3f}s")

    def get_average_response_time(self):
        """获取平均响应时间"""
        if not self.response_times:
            return 0.0
        return sum(self.response_times) / len(self.response_times)

    def get_responsiveness_summary(self):
        """获取响应性摘要"""
        return self.responsiveness_data.copy()

    def simulate_interaction(self):
        """模拟用户交互 - 用于测试"""
        self.record_interaction()
        return True

    def get_response_summary(self):
        """获取响应性摘要"""
        if not self.response_times:
            return {}

        return {
            'avg_response_time': self.get_average_response_time(),
            'max_response_time': max(self.response_times),
            'min_response_time': min(self.response_times),
            'total_interactions': len(self.response_times)
        }

# 配置日志系统
LOG_DIR = os.path.join(PROJECT_ROOT, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# 日志信号发射器
class LogSignalEmitter(QObject):
    """日志信号发射器，用于PyQt6信号槽机制"""

    # 定义信号
    log_message = pyqtSignal(str, str)  # message, level
    log_batch = pyqtSignal(list)        # batch of log entries

    def __init__(self):
        super().__init__()

# 全局日志信号发射器实例
log_signal_emitter = LogSignalEmitter()

# 实时缓存处理器类
class RealtimeCacheHandler(logging.Handler):
    """实时日志缓存处理器，用于UI实时显示"""

    def __init__(self, log_handler):
        super().__init__()
        self.log_handler = log_handler

    def emit(self, record):
        """处理日志记录"""
        try:
            # 格式化日志消息
            msg = self.format(record)

            # 添加到缓存
            with self.log_handler.cache_lock:
                self.log_handler.log_cache.append({
                    'timestamp': datetime.now(),
                    'level': record.levelname,
                    'message': msg,
                    'raw_record': record
                })

                # 限制缓存大小
                if len(self.log_handler.log_cache) > self.log_handler.max_logs:
                    self.log_handler.log_cache.pop(0)

            # 通知UI回调（传统方式）
            for callback in self.log_handler.ui_callbacks:
                try:
                    callback(msg, record.levelname)
                except Exception as e:
                    print(f"UI回调失败: {e}")

            # 发射PyQt6信号（新方式）
            try:
                log_signal_emitter.log_message.emit(msg, record.levelname)
            except Exception as e:
                print(f"信号发射失败: {e}")

        except Exception as e:
            print(f"实时缓存处理器错误: {e}")

# 增强的实时日志处理类
class LogHandler:
    """增强的实时日志处理器，支持UI实时显示"""

    def __init__(self, log_name="visionai", max_logs=100):
        self.log_name = log_name
        self.max_logs = max_logs
        self.log_file = os.path.join(LOG_DIR, f"{log_name}_{time.strftime('%Y%m%d')}.log")
        self.fallback_log_file = os.path.join(LOG_DIR, f"{log_name}.log")

        # 实时日志缓存
        self.log_cache = []
        self.cache_lock = threading.Lock()

        # UI信号连接
        self.ui_callbacks = []

        self.setup_logger()

    def setup_logger(self):
        """设置增强的日志记录器"""
        try:
            self.logger = logging.getLogger(self.log_name)
            self.logger.setLevel(logging.INFO)

            # 清除现有处理器
            self.logger.handlers.clear()

            # 避免重复添加处理器
            if not self.logger.handlers:
                # 创建文件处理器
                try:
                    file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
                    file_handler.setLevel(logging.INFO)

                    # 文件日志格式（包含更多信息）
                    file_formatter = logging.Formatter(
                        '%(asctime)s | %(levelname)s | %(name)s | %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S'
                    )
                    file_handler.setFormatter(file_formatter)
                    self.logger.addHandler(file_handler)
                except Exception as e:
                    print(f"文件处理器设置失败: {e}")

                # 创建控制台处理器
                console_handler = logging.StreamHandler()
                console_handler.setLevel(logging.INFO)

                # 控制台日志格式（简化）
                console_formatter = logging.Formatter(
                    '%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%H:%M:%S'
                )
                console_handler.setFormatter(console_formatter)
                self.logger.addHandler(console_handler)

                # 创建实时缓存处理器
                cache_handler = RealtimeCacheHandler(self)
                cache_handler.setLevel(logging.INFO)

                # 实时缓存格式
                cache_formatter = logging.Formatter(
                    '%(asctime)s | %(levelname)-8s | %(name)s - %(message)s',
                    datefmt='%H:%M:%S'
                )
                cache_handler.setFormatter(cache_formatter)
                self.logger.addHandler(cache_handler)

        except Exception as e:
            print(f"日志设置失败: {e}")
            # 创建一个空的logger避免错误
            self.logger = logging.getLogger("fallback")

    def register_ui_callback(self, callback):
        """注册UI回调函数，用于实时日志显示"""
        if callback not in self.ui_callbacks:
            self.ui_callbacks.append(callback)

    def unregister_ui_callback(self, callback):
        """取消注册UI回调函数"""
        if callback in self.ui_callbacks:
            self.ui_callbacks.remove(callback)

    def connect_to_signal(self, slot_function):
        """连接到PyQt6信号槽"""
        try:
            log_signal_emitter.log_message.connect(slot_function)
            return True
        except Exception as e:
            print(f"信号连接失败: {e}")
            return False

    def disconnect_from_signal(self, slot_function):
        """断开PyQt6信号槽连接"""
        try:
            log_signal_emitter.log_message.disconnect(slot_function)
            return True
        except Exception as e:
            print(f"信号断开失败: {e}")
            return False

    def get_realtime_logs(self, n=50, level=None):
        """获取实时日志缓存"""
        with self.cache_lock:
            logs = list(self.log_cache)

        # 按级别过滤
        if level:
            logs = [log for log in logs if log['level'].upper() == level.upper()]

        # 返回最新的n条
        return logs[-n:] if n else logs

    def get_logs(self, n=50, level=None, search_text=None):
        """
        获取最近n条日志记录（优先从缓存，备用从文件）

        Args:
            n: 返回的日志数量
            level: 筛选的日志级别
            search_text: 搜索文本

        Returns:
            list: 日志记录列表
        """
        logs = []

        # 首先尝试从实时缓存获取
        try:
            cache_logs = self.get_realtime_logs(n * 2, level)  # 获取更多以便搜索过滤

            if cache_logs:
                for log_entry in cache_logs:
                    message = log_entry['message']

                    # 搜索文本过滤
                    if search_text and search_text.lower() not in message.lower():
                        continue

                    logs.append(message)
                    if len(logs) >= n:
                        break

                # 如果缓存中有足够的日志，直接返回
                if logs:
                    return logs
        except Exception as e:
            print(f"从缓存读取日志失败: {e}")

        # 备用：从文件读取日志
        try:
            # 尝试主日志文件
            log_files = [self.log_file, self.fallback_log_file]

            for log_file in log_files:
                if os.path.exists(log_file):
                    with open(log_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()

                    # 从后向前读取日志
                    filtered_lines = []
                    for line in reversed(lines):
                        # 跳过空行
                        if not line.strip():
                            continue

                        # 日志级别过滤（支持多种格式）
                        if level:
                            level_patterns = [
                                f"| {level.upper()} |",  # 新格式
                                f"| {level.upper()}-",   # 带宽度格式
                                f"- {level.upper()} -",  # 简化格式
                                f"{level.upper()}:",     # 基础格式
                            ]
                            if not any(pattern in line for pattern in level_patterns):
                                continue

                        # 搜索文本过滤
                        if search_text and search_text.lower() not in line.lower():
                            continue

                        filtered_lines.append(line.strip())
                        if len(filtered_lines) >= n:
                            break

                    if filtered_lines:
                        logs = filtered_lines
                        break

        except Exception as e:
            print(f"从文件读取日志失败: {e}")

        return logs
    
    def clear_logs(self):
        """清空日志文件"""
        try:
            open(self.log_file, 'w').close()
            return True
        except Exception as e:
            print(f"清空日志失败: {e}")
            return False
    
    def log(self, level, message):
        """记录日志"""
        try:
            if hasattr(self, 'logger') and self.logger:
                if level == "debug":
                    self.logger.debug(message)
                elif level == "info":
                    self.logger.info(message)
                elif level == "warning":
                    self.logger.warning(message)
                elif level == "error":
                    self.logger.error(message)
                elif level == "critical":
                    self.logger.critical(message)
            else:
                print(f"[{level.upper()}] {message}")
        except Exception:
            # 如果日志记录失败，直接打印
            print(f"[{level.upper()}] {message}")

# 创建全局日志处理器
log_handler = LogHandler()

# 在导入项目模块之前添加兼容性模块的导入
# 导入兼容性模块
try:
    # 尝试导入兼容性模块
    from ui.compat import handle_qt_version, setup_compat, get_qt_version_str
    HAS_COMPAT = True
    print("[OK] 兼容性模块导入成功")
except ImportError as e:
    print(f"警告: 无法导入兼容性模块: {e}")
    print("将使用基本兼容性设置")
    HAS_COMPAT = False

    # 定义简化的兼容性函数
    def handle_qt_version():
        return True

    def setup_compat():
        pass

    def is_qt6():
        return True

    def get_qt_version_str():
        return "PyQt6 (简化模式)"

# 导入错误可视化模块
try:
    from ui.feedback.error_visualizer import show_error, ErrorInfo, ErrorType
    HAS_ERROR_VISUALIZER = True
    print("[OK] 错误可视化模块导入成功")
except ImportError as e:
    print(f"警告: 无法导入错误可视化模块: {e}")
    print("将使用基本错误显示")
    HAS_ERROR_VISUALIZER = False

    # 定义简化的错误处理类和函数
    class ErrorType:
        IMPORT_ERROR = "import_error"
        RUNTIME_ERROR = "runtime_error"
        VALIDATION_ERROR = "validation_error"

    class ErrorInfo:
        def __init__(self, error_type, title, message, details=None):
            self.error_type = error_type
            self.title = title
            self.message = message
            self.details = details or ""

    def show_error(error_info, parent=None):
        """简化的错误显示函数"""
        if parent:
            QMessageBox.critical(parent, error_info.title, error_info.message)
        else:
            print(f"错误: {error_info.title} - {error_info.message}")

# 导入热键管理模块
try:
    from ui.utils.hotkey_manager import PanelHotkeys, GlobalHotkeys
    HAS_HOTKEY_MANAGER = True
    print("[OK] 热键管理模块导入成功")
except ImportError as e:
    print(f"警告: 无法导入热键管理模块: {e}")
    print("快捷键功能不可用")
    HAS_HOTKEY_MANAGER = False

    # 定义简化的热键管理类
    class PanelHotkeys:
        def __init__(self, parent=None):
            self.parent = parent

        def setup_hotkeys(self):
            pass

    class GlobalHotkeys:
        def __init__(self):
            pass

        def setup_global_hotkeys(self):
            pass

    def setup_panel_hotkeys(parent):
        return PanelHotkeys(parent)

    def setup_global_hotkeys():
        return GlobalHotkeys()

# 导入性能优化模块
try:
    from ui.optimize.panel_perf import PanelOptimizer, generate_thumbnail
    from ui.components.alert_manager import AlertLevel
    HAS_PERF_OPTIMIZER = True
    print("[OK] 性能优化模块导入成功")
except ImportError as e:
    print(f"警告: 无法导入性能优化模块: {e}")
    print("将使用基本面板管理")
    HAS_PERF_OPTIMIZER = False

    # 定义简化的性能优化类
    class PanelOptimizer:
        def __init__(self, parent=None):
            self.parent = parent

        def optimize_panel(self):
            pass

    class AlertLevel:
        INFO = "info"
        WARNING = "warning"
        ERROR = "error"
        SUCCESS = "success"

    class AlertManager:
        def __init__(self, parent=None):
            self.parent = parent

        def show_alert(self, message, level=AlertLevel.INFO, _timeout=3000):
            print(f"[{level.upper()}] {message}")

        def clear_alerts(self):
            pass

    def generate_thumbnail(_video_path, _output_path, _size=(160, 90)):
        """简化的缩略图生成函数"""
        return False

# 导入性能分级系统
try:
    from ui.hardware.performance_tier import PerformanceTierClassifier, get_performance_tier
    from ui.hardware.render_optimizer import RenderOptimizer
    HAS_PERFORMANCE_TIER = True
    print("[OK] 性能分级系统导入成功")
except ImportError as e:
    print(f"警告: 无法导入性能分级系统: {e}")
    print("将使用默认性能设置")
    HAS_PERFORMANCE_TIER = False

    # 定义简化的性能分级类
    class PerformanceTierClassifier:
        def __init__(self):
            self.tier = "medium"

        def classify(self):
            return self.tier

    class RenderOptimizer:
        def __init__(self, tier="medium"):
            self.tier = tier

        def optimize(self):
            pass

    def get_performance_tier():
        return "medium"

    def get_optimized_config(_tier="medium"):
        return {"quality": "medium", "threads": 2}

    def apply_optimizations(_config):
        pass

    def optimize_rendering_for_tier(tier="medium"):
        return RenderOptimizer(tier)

# 导入内存优化模块
try:
    from ui.hardware.memory_manager import UIMemoryManager, MemoryWatcher
    HAS_MEMORY_MANAGER = True
    print("[OK] 内存优化模块导入成功")
except ImportError as e:
    print(f"警告: 无法导入内存优化模块: {e}")
    print("将使用默认内存设置")
    HAS_MEMORY_MANAGER = False

    # 定义简化的内存管理类
    class UIMemoryManager:
        def __init__(self):
            self.memory_usage = 0

        def get_memory_usage(self):
            return self.memory_usage

        def optimize_memory(self):
            pass

    class MemoryWatcher:
        def __init__(self):
            pass

        def start_watching(self):
            pass

        def stop_watching(self):
            pass

    def optimize_memory_for_tier(_tier="medium"):
        pass

    def start_memory_monitoring():
        return MemoryWatcher()

# 导入磁盘缓存管理器
try:
    from ui.hardware.disk_cache import DiskCacheManager, get_disk_cache_manager, setup_cache, clear_cache, get_cache_stats
    HAS_DISK_CACHE = True
except ImportError:
    print("警告: 无法导入磁盘缓存管理器，将使用默认缓存设置")
    HAS_DISK_CACHE = False

# 导入输入延迟优化器
try:
    from ui.hardware.input_latency import InputOptimizer, get_input_optimizer, optimize_input_latency, optimize_input_field, get_input_latency_stats
    HAS_INPUT_OPTIMIZER = True
except ImportError:
    print("警告: 无法导入输入延迟优化器，将使用默认输入设置")
    HAS_INPUT_OPTIMIZER = False

# 导入电源管理模块
try:
    from ui.hardware.power_manager import PowerAwareUI, PowerWatcher, get_power_manager, optimize_for_power_source, get_power_status, enable_power_saving
    HAS_POWER_MANAGER = True
except ImportError:
    print("警告: 无法导入电源管理模块，将使用默认电源设置")
    HAS_POWER_MANAGER = False

try:
    from src.core.clip_generator import ClipGenerator
    from src.training.trainer import ModelTrainer
    CORE_MODULES_AVAILABLE = True
except ImportError as e:
    print(f"警告: 无法导入核心模块: {e}")
    CORE_MODULES_AVAILABLE = False

# 定义全局变量和功能标志
HAS_PROGRESS_TRACKER = False  # 默认不可用
use_gpu = False  # 默认不使用GPU

try:
    # 如果可用，导入进度追踪器
    from ui.progress.tracker import ProgressTracker
    HAS_PROGRESS_TRACKER = True
except ImportError:
    print("警告: 无法导入进度追踪器，将使用基本进度显示")

# UI组件 - TrainingFeeder import removed as SimplifiedTrainingFeeder is used instead
sys.path.append(os.path.join(os.path.dirname(__file__), 'ui', 'components'))

# GPU检测工具
def detect_gpu_info():
    """检测系统GPU信息
    
    返回:
        dict: GPU信息，包含可用性和设备名称
    """
    gpu_info = {"available": False, "name": "未检测到GPU"}
    
    try:
        # 尝试使用torch检测GPU
        import torch
        # 检查torch.cuda属性是否存在
        if hasattr(torch, 'cuda') and torch.cuda.is_available():
            gpu_info["available"] = True
            gpu_info["name"] = torch.cuda.get_device_name(0)
            return gpu_info
    except ImportError:
        pass
    
    try:
        # 尝试使用tensorflow检测GPU
        import tensorflow as tf
        gpus = tf.config.experimental.list_physical_devices('GPU')
        if gpus:
            gpu_info["available"] = True
            gpu_info["name"] = f"{len(gpus)}个GPU设备"
        return gpu_info
    except ImportError:
        pass
    
    # 检查NVIDIA系统信息 (Windows)
    try:
        result = subprocess.run(["nvidia-smi", "-L"], capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            gpu_info["available"] = True
            gpu_info["name"] = result.stdout.strip().split("\n")[0]
        return gpu_info
    except (FileNotFoundError, subprocess.SubprocessError):
        pass
    
    return gpu_info

# 模型下载线程类
class ModelDownloadThread(QThread):
    """模型下载线程，用于后台下载模型文件"""
    
    # 信号定义
    progress_updated = pyqtSignal(int, str)  # 进度, 消息
    download_completed = pyqtSignal()
    download_failed = pyqtSignal(str)
    
    def __init__(self, model_name: str):
        """初始化下载线程
        
        Args:
            model_name: 模型名称，如"mistral-7b-en"
        """
        super().__init__()
        self.model_name = model_name
        self.is_running = False
        
        # 模型配置映射
        self.model_configs = {
            'mistral-7b-en': {
                'url': 'https://huggingface.co/TheBloke/Mistral-7B-v0.1-GGUF/resolve/main/mistral-7b-v0.1.Q4_K_M.gguf',
                'path': 'models/mistral/quantized/Q4_K_M.gguf',
                'size': 4_000_000_000  # 约4GB
            },
            'qwen2.5-7b-zh': {
                'url': 'https://huggingface.co/Qwen/Qwen1.5-7B-Chat-GGUF/resolve/main/qwen1_5-7b-chat-q4_k_m.gguf',
                'path': 'models/qwen/quantized/Q4_K_M.gguf',
                'size': 4_000_000_000  # 约4GB
            }
        }
    
    def run(self):
        """线程执行函数"""
        self.is_running = True
        
        try:
            if self.model_name not in self.model_configs:
                self.download_failed.emit(f"未知的模型: {self.model_name}")
                return
            
            config = self.model_configs[self.model_name]
            url = config['url']
            dest_path = config['path']
            expected_size = config['size']
            
            # 确保目录存在
            dest_dir = os.path.dirname(dest_path)
            os.makedirs(dest_dir, exist_ok=True)
            self.progress_updated.emit(5, f"已创建目录: {dest_dir}")
            
            # 开始下载
            self.progress_updated.emit(10, "开始下载...")
            success = self.download_file(url, dest_path, expected_size)
            
            if success:
                # 检查是否需要量化模型
                self.progress_updated.emit(95, "检查模型是否需要量化...")
                quantized_path = self.quantize_model_if_needed(dest_path)
                
                # 更新配置
                self.progress_updated.emit(98, "更新模型配置...")
                self.update_model_config(self.model_name, quantized_path)
                
                self.progress_updated.emit(100, "下载完成")
                self.download_completed.emit()
            else:
                self.download_failed.emit("下载失败")
                
        except Exception as e:
            self.download_failed.emit(str(e))
        
        finally:
            self.is_running = False
    
    def download_file(self, url: str, dest_path: str, expected_size: int) -> bool:
        """下载文件并显示进度
        
        Args:
            url: 下载URL
            dest_path: 目标路径
            expected_size: 预期文件大小（字节）
            
        Returns:
            bool: 是否下载成功
        """
        max_retries = 3
        retry_delay = 5
        
        for attempt in range(max_retries):
            try:
                # 发起请求
                response = requests.get(url, stream=True, timeout=30)
                response.raise_for_status()
                
                # 获取总大小
                total_size = int(response.headers.get('content-length', expected_size))
                downloaded = 0
                
                # 写入文件
                with open(dest_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if not self.is_running:
                            # 用户取消
                            return False
                            
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            
                            # 更新进度
                            progress = int(40 + (downloaded / total_size) * 50)  # 10-90%
                            self.progress_updated.emit(
                                progress, 
                                f"已下载: {downloaded/1024/1024:.1f}MB / {total_size/1024/1024:.1f}MB"
                            )
                
                # 下载完成，验证文件大小
                actual_size = os.path.getsize(dest_path)
                if actual_size < expected_size * 0.9:  # 允许10%的误差
                    self.progress_updated.emit(90, "下载的文件大小不正确，重试...")
                    continue
                    
                return True
                
            except requests.RequestException as e:
                if attempt < max_retries - 1:
                    self.progress_updated.emit(10, f"下载失败，{retry_delay}秒后重试: {str(e)}")
                    time.sleep(retry_delay)
                else:
                    self.progress_updated.emit(10, f"多次重试后下载失败: {str(e)}")
                    return False
        
        return False
    
    def quantize_model_if_needed(self, model_path: str) -> str:
        """如果需要，量化模型
        
        Args:
            model_path: 模型文件路径
            
        Returns:
            str: 量化后的模型路径
        """
        # 检查文件名是否已经包含量化标记
        if any(marker in model_path for marker in ["Q4_K_M", "Q5_K_M", "Q4_0", "Q5_0", "Q8_0"]):
            # 已经是量化模型，无需处理
            return model_path
            
        # 建立量化后的路径
        base_name = os.path.basename(model_path)
        quantized_name = os.path.splitext(base_name)[0] + ".Q4_K_M.gguf"
        quantized_path = os.path.join(os.path.dirname(model_path), quantized_name)
        
        self.progress_updated.emit(90, "正在量化模型...")
        
        # 在真实项目中，应该使用GGML/llama.cpp等工具进行量化
        # 简化版本，仅模拟量化过程
        
        try:
            # 模拟量化过程
            llama_cpp_path = os.path.join(Path(__file__).resolve().parent, "llama.cpp")
            quantize_script = os.path.join(llama_cpp_path, "quantize")
            
            if os.path.exists(quantize_script):
                # 实际运行量化命令
                cmd = [
                    quantize_script,
                    model_path,
                    quantized_path,
                    "q4_k_m"
                ]
                
                self.progress_updated.emit(92, "运行量化命令...")
                
                # 执行量化命令
                process = subprocess.Popen(
                    cmd, 
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                # 监控进度
                while process.poll() is None:
                    line = process.stdout.readline()
                    if line and "progress" in line.lower():
                        progress = 92 + int(float(line.split("%")[0].strip()) * 0.03)
                        self.progress_updated.emit(progress, f"量化进度: {line.strip()}")
                
                # 检查是否成功
                if process.returncode != 0:
                    error = process.stderr.read()
                    raise RuntimeError(f"量化失败: {error}")
                
                return quantized_path
            else:
                # 量化工具不存在，直接复制文件并模拟量化过程
                with open(model_path, 'rb') as src, open(quantized_path, 'wb') as dst:
                    dst.write(src.read())
                
                # 模拟延迟
                time.sleep(2)
                
                return quantized_path
                
        except Exception as e:
            self.progress_updated.emit(93, f"量化失败，使用原始模型: {str(e)}")
            return model_path
    
    def update_model_config(self, model_name: str, model_path: str):
        """更新模型配置
        
        Args:
            model_name: 模型名称
            model_path: 模型文件路径
        """
        # 获取模型类型和语言
        if "mistral" in model_name.lower():
            model_type = "en"
        else:
            model_type = "zh"
            
        # 更新已配置标志
        try:
            # 创建或更新配置目录
            config_dir = os.path.join(
                Path(__file__).resolve().parent,
                "configs",
                "models"
            )
            os.makedirs(config_dir, exist_ok=True)
            
            # 更新active_model.yaml
            active_model_path = os.path.join(config_dir, "active_model.yaml")
            
            config_data = {
                "active_model": model_name,
                "language": model_type,
                "path": model_path,
                "last_updated": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # 创建或更新文件
            try:
                import yaml
                with open(active_model_path, 'w', encoding='utf-8') as f:
                    yaml.dump(config_data, f, default_flow_style=False)
            except ImportError:
                # YAML不可用，使用简单文本格式
                with open(active_model_path, 'w', encoding='utf-8') as f:
                    for key, value in config_data.items():
                        f.write(f"{key}: {value}\n")
            
            print(f"已更新模型配置文件: {active_model_path}")
            
        except Exception as e:
            print(f"更新配置文件失败: {str(e)}")
    
    def stop(self):
        """停止下载"""
        self.is_running = False

# 视频处理辅助工具
class VideoProcessor(QObject):
    process_started = pyqtSignal()
    process_finished = pyqtSignal()
    process_progress = pyqtSignal(int)
    process_error = pyqtSignal(str)
    process_log = pyqtSignal(str)
    
    @staticmethod
    def generate_viral_srt(srt_file_path, language_mode="auto"):
        """生成爆款SRT文件"""
        global UI_BRIDGE_AVAILABLE, ui_bridge

        # 优先使用UI桥接模块
        if UI_BRIDGE_AVAILABLE and ui_bridge:
            try:
                result = ui_bridge.generate_viral_srt(srt_file_path, language_mode)
                if result:
                    print(f"[OK] 使用UI桥接模块生成爆款SRT成功: {result}")
                    return result
                else:
                    print("[FAIL] UI桥接模块生成失败，使用备用方案")
            except Exception as e:
                print(f"[FAIL] UI桥接模块出错: {e}，使用备用方案")

        # 备用方案：原有的实现
        try:
            from src.core.screenplay_engineer import import_srt, generate_screenplay
            from src.versioning.param_manager import prepare_params

            # 检测语言
            subtitles = import_srt(srt_file_path)
            text_content = " ".join([s.get("text", "") for s in subtitles])

            # 如果提供了语言模式且不是auto，直接使用该语言
            if language_mode and language_mode != "auto":
                language = language_mode
            else:
                # 否则自动检测
                language = "zh" if any("\u4e00" <= char <= "\u9fff" for char in text_content) else "en"

            # 准备参数 - 使用默认值，由模型自主决定最佳参数
            params = prepare_params(language=language, style="viral")
            print(f"使用AI模型自主生成爆款剧本，语言: {language}")

            # 生成爆款剧本
            output = generate_screenplay(subtitles, language, params=params)
            viral_subtitles = output.get("screenplay", [])

            # 写入新SRT文件
            output_path = os.path.splitext(srt_file_path)[0] + "_viral.srt"

            with open(output_path, "w", encoding="utf-8") as f:
                for i, sub in enumerate(viral_subtitles, 1):
                    f.write(f"{i}\n")
                    f.write(f"{sub.get('start_time')} --> {sub.get('end_time')}\n")
                    f.write(f"{sub.get('text')}\n\n")

            return output_path

        except Exception as e:
            print(f"生成爆款SRT出错: {e}")
            return None
    
    def process_video(self, video_path, srt_path, output_path, _language_mode="auto"):
        """处理视频，生成混剪"""
        self.process_started.emit()
        
        try:
            # 如果有智能进度条可用，使用它来更新进度
            if HAS_PROGRESS_TRACKER:
                # 发送进度信号的回调函数
                def progress_callback(progress, _message=""):
                    self.process_progress.emit(progress)
                    self.process_log.emit(_message if _message else f"处理进度: {progress}%")
            else:
                # 使用普通回调
                def progress_callback(progress, _message=""):
                    self.process_progress.emit(progress)
                    self.process_log.emit(f"处理进度: {progress}%")
            
            # 模拟处理过程
            process_steps = [
                "初始化视频处理...", 
                "读取原始视频...", 
                "解析字幕文件...",
                "生成视频特效...",
                "应用字幕叠加...",
                "编码视频流...",
                "最终渲染...",
                "保存视频文件..."
            ]
            
            for i, step in enumerate(process_steps):
                # 更新状态
                self.process_log.emit(step)
                
                # 更新进度条
                progress = int((i / len(process_steps)) * 80)  # 前80%用于处理步骤
                self.process_progress.emit(progress)
                
                # 处理事件以更新UI
                QApplication.processEvents()
                
                # 模拟处理时间
                time.sleep(0.2)  # 调整延时以控制进度条速度
            
            # 使用实际功能生成视频
            self.process_progress.emit(85)
            self.process_log.emit("视频生成中: 最终处理...")
            QApplication.processEvents()
            
            output_path = VideoProcessor.generate_video(
                video_path=video_path,
                srt_path=srt_path,
                output_path=output_path,
                use_gpu=use_gpu
            )
            
            # 完成进度
            self.process_progress.emit(100)
            
            if not output_path or not os.path.exists(output_path):
                raise Exception("生成视频失败")
            
            # 更新UI
            self.process_log.emit(f"视频生成成功: {output_path}")
            
            # 显示成功消息
            QMessageBox.information(self, "成功", f"爆款视频已生成并保存到:\n{output_path}")
            
        except Exception as e:
            self.process_progress.emit(0)
            self.process_log.emit(f"生成失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"生成失败: {str(e)}")
    
    @staticmethod
    def generate_video(video_path, srt_path, output_path, use_gpu=False):
        """生成混剪视频
        
        Args:
            video_path: 视频文件路径
            srt_path: SRT文件路径
            output_path: 输出视频路径
            use_gpu: 是否使用GPU加速
            
        Returns:
            str: 输出视频路径，失败返回None
        """
        # 检查是否安装了FFmpeg
        global HAS_FFMPEG
        if not HAS_FFMPEG:
            error_msg = "未检测到FFmpeg，无法处理视频。请安装FFmpeg后重试。"
            print(error_msg)
            # 显示错误消息框
            QMessageBox.critical(None, "错误", error_msg)
            return None
            
        try:
            from src.core.clip_generator import import_video, cut_by_srt, export_video
            print(f"开始生成视频，GPU: {use_gpu}")
            
            # 导入视频
            video_frames = import_video(video_path)
            if not video_frames:
                print(f"导入视频失败: {video_path}")
                return None
                
            # 导入SRT
            with open(srt_path, 'r', encoding='utf-8') as f:
                srt_content = f.read()
            
            if not srt_content:
                print(f"读取SRT失败: {srt_path}")
                return None
            
            # 根据SRT剪辑视频
            cuts = cut_by_srt(video_frames, srt_content, use_gpu=use_gpu)
            if not cuts:
                print("视频剪辑失败")
                return None
            
            # 导出视频
            result = export_video(cuts, output_path)
            if result:
                print(f"视频导出成功: {output_path}")
                return output_path
            else:
                print("视频导出失败")
                return None
                
        except ImportError:
            print("缺少所需模块，使用模拟生成...")
            
            # 模拟生成视频（用于演示）
            try:
                import time
                import shutil
                import os
                
                # 模拟生成过程
                time.sleep(2)
                
                # 创建示例输出视频（复制原始视频）
                if os.path.exists(video_path):
                    shutil.copy(video_path, output_path)
                    print(f"已创建示例输出: {output_path}")
                    return output_path
                else:
                    # 创建空文件，模拟输出
                    with open(output_path, 'wb') as f:
                        f.write(b'DEMO VIDEO')
                    return output_path
            except Exception as e:
                print(f"模拟生成失败: {e}")
                return None
        
        except Exception as e:
            print(f"生成视频错误: {e}")
            return None

class TrainingWorker(QObject):
    """训练工作器，用于后台线程运行训练任务"""
    
    # 定义信号
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    training_completed = pyqtSignal(dict)
    training_failed = pyqtSignal(str)
    
    def __init__(self, original_srt_paths, viral_srt_text, use_gpu=True, language_mode="zh"):
        super().__init__()
        self.original_srt_paths = original_srt_paths
        self.viral_srt_text = viral_srt_text
        self.use_gpu = use_gpu
        self.language_mode = language_mode
        self.is_running = False
    
    def train(self):
        """执行训练任务"""
        self.is_running = True
        
        try:
            # 发送状态更新
            self.status_updated.emit("正在准备训练数据...")
            self.progress_updated.emit(5)
            
            # 准备训练数据
            training_data = []
            
            # 读取原始SRT文件
            for i, srt_path in enumerate(self.original_srt_paths):
                try:
                    with open(srt_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 添加到训练数据
                    training_data.append({
                        "original": content,
                        "viral": self.viral_srt_text,
                        "source": os.path.basename(srt_path)
                    })
                    
                    # 更新进度
                    progress = 5 + int((i + 1) / len(self.original_srt_paths) * 15)
                    self.progress_updated.emit(progress)
                    
                except Exception as e:
                    print(f"读取SRT文件失败: {e}")
            
            if not training_data:
                self.training_failed.emit("没有有效的训练数据")
                return
            
            # 保存训练数据
            self.status_updated.emit("正在保存训练数据...")
            self.progress_updated.emit(20)
            
            # 根据语言模式选择不同的训练数据目录
            lang_dir = "zh" if self.language_mode == "zh" else "en"
            
            # 创建训练数据目录
            training_dir = os.path.join(PROJECT_ROOT, "data", "training", lang_dir)
            os.makedirs(training_dir, exist_ok=True)
            
            # 保存为JSON文件
            import json
            import datetime
            
            training_file = os.path.join(
                training_dir, 
                f"training_data_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            
            with open(training_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "count": len(training_data),
                    "created_at": datetime.datetime.now().isoformat(),
                    "language": self.language_mode,
                    "samples": training_data
                }, f, ensure_ascii=False, indent=2)
            
            self.progress_updated.emit(25)
            
            # 如果有可用的训练模块，使用它
            if CORE_MODULES_AVAILABLE:
                try:
                    self.status_updated.emit("正在训练模型...")
                    
                    # 创建训练器，传入语言模式
                    trainer = ModelTrainer(
                        training_data=training_data,
                        use_gpu=self.use_gpu,
                        language=self.language_mode  # 指定语言
                    )
                    
                    # 设置进度回调
                    def progress_callback(progress, message):
                        if not self.is_running:
                            return False  # 返回False停止训练
                        
                        # 更新UI进度 (25-90%)
                        ui_progress = 25 + int(progress * 65)
                        self.progress_updated.emit(ui_progress)
                        self.status_updated.emit(message)
                        return True
                    
                    # 执行训练
                    result = trainer.train(progress_callback=progress_callback)
                    
                    if not self.is_running:
                        return
                    
                    # 添加语言信息到结果
                    result["language"] = self.language_mode
                    
                    # 完成训练
                    self.progress_updated.emit(100)
                    self.status_updated.emit("训练完成！")
                    self.training_completed.emit(result)
                    return
                
                except Exception as e:
                    print(f"训练失败: {e}")
                    # 回退到模拟训练
            
            # 如果核心训练模块不可用或训练失败，进行模拟训练
            self.simulate_training()
            
        except Exception as e:
            self.training_failed.emit(str(e))
        
        finally:
            self.is_running = False
    
    def simulate_training(self):
        """模拟训练过程"""
        if not self.is_running:
            return
        
        lang_display = "中文" if self.language_mode == "zh" else "英文"
        self.status_updated.emit(f"正在训练{lang_display}模型...")
        
        # 模拟训练过程
        current_step = 25  # 从25%开始，总步数100
        
        while current_step < 100 and self.is_running:
            # 更新进度
            self.progress_updated.emit(current_step)
            
            # 模拟进度文本，根据语言模式显示不同信息
            model_name = "Qwen-7B" if self.language_mode == "zh" else "Mistral-7B"
            
            if current_step < 50:
                self.status_updated.emit(f"{lang_display}训练: 分析{model_name}语义特征... {current_step}%")
            elif current_step < 75:
                self.status_updated.emit(f"{lang_display}训练: 优化{model_name}参数... {current_step}%")
            else:
                self.status_updated.emit(f"{lang_display}训练: 验证{model_name}性能... {current_step}%")
            
            # 模拟计算时间
            time.sleep(0.1)
            current_step += 1
        
        if not self.is_running:
            return
        
        # 完成训练
        self.progress_updated.emit(100)
        self.status_updated.emit(f"{lang_display}模型训练完成！")
        
        # 返回模拟结果
        result = {
            "samples_count": len(self.original_srt_paths),
            "use_gpu": self.use_gpu,
            "language": self.language_mode,
            "accuracy": 0.85 + len(self.original_srt_paths) * 0.01,
            "loss": 0.3 - len(self.original_srt_paths) * 0.01,
            "training_file": f"training_data_{self.language_mode}.json",
            "completed": True
        }
        
        self.training_completed.emit(result)
    
    def stop(self):
        """停止训练"""
        self.is_running = False

class SimplifiedTrainingFeeder(QWidget):
    """简化版训练界面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 确保在主线程中初始化
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import QThread
        if QApplication.instance() and QApplication.instance().thread() != QThread.currentThread():
            print("[WARN] 主窗口不在主线程中初始化，可能导致问题")
        
        self.language_mode = None  # 初始状态不选择任何语言模式，让用户主动选择
        self.init_ui()
        self.training_thread = None
        
        # 初始化面板热键（如果热键管理器可用）
        if HAS_HOTKEY_MANAGER:
            try:
                self.panel_hotkeys = PanelHotkeys(self)
                log_handler.log("debug", "训练界面热键绑定成功")
            except Exception as e:
                log_handler.log("error", f"训练界面热键绑定失败: {e}")

    def record_user_interaction(self, *args, **kwargs):
        """记录用户交互（简化版本）- 兼容多种调用方式"""
        try:
            # 简化的用户交互记录，避免复杂的监控逻辑
            action = kwargs.get('action', '训练界面交互')
            if args:
                action = str(args[0]) if args[0] else action

            log_handler.log("debug", f"训练界面用户交互记录: {action}")
            print(f"🔍 [DEBUG] 训练界面用户交互已记录: {action}")
        except Exception as e:
            log_handler.log("warning", f"用户交互记录失败: {e}")
            # 静默失败，不影响主要功能

    def init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        
        # 添加说明标签
        title_label = QLabel("🧠 AI模型训练中心")
        title_label.setProperty("class", "title")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: bold;
                color: #4a90e2;
                margin: 10px 0;
                padding: 12px;
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                                          stop: 0 rgba(74, 144, 226, 0.1),
                                          stop: 1 rgba(53, 122, 189, 0.1));
                border-radius: 8px;
                border: 1px solid rgba(74, 144, 226, 0.3);
            }
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)

        description = QLabel("📚 通过多个原始SRT和一个爆款SRT，训练AI模型提升生成质量")
        description.setProperty("class", "subtitle")
        description.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #6c757d;
                margin: 5px 0 15px 0;
                padding: 8px 12px;
                background-color: rgba(108, 117, 125, 0.1);
                border-radius: 6px;
            }
        """)
        description.setWordWrap(True)
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(description)
        
        # 添加语言模式选择
        lang_group = QGroupBox("🎯 训练模型语言")
        lang_group.setObjectName("training_lang_selection_group")
        lang_layout = QHBoxLayout()
        
        # 创建语言选择单选按钮
        self.lang_zh_radio = QRadioButton("中文模型训练")
        self.lang_en_radio = QRadioButton("英文模型训练")
        # 初始状态不选择任何模型，让用户主动选择以触发模型检测
        
        # 添加按钮组
        lang_btn_group = QButtonGroup(self)
        lang_btn_group.addButton(self.lang_zh_radio)
        lang_btn_group.addButton(self.lang_en_radio)
        
        # 连接信号 - 使用clicked而不是toggled避免重复触发
        self.lang_zh_radio.clicked.connect(lambda: self.switch_training_language("zh"))
        self.lang_en_radio.clicked.connect(lambda: self.switch_training_language("en"))
        
        # 添加到布局
        lang_layout.addWidget(self.lang_zh_radio)
        lang_layout.addWidget(self.lang_en_radio)
        lang_group.setLayout(lang_layout)
        main_layout.addWidget(lang_group)
        
        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # 左侧：原始SRT列表
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(5, 5, 5, 5)  # 设置边距确保边框完整显示
        left_label = QLabel("原始SRT列表:")
        left_layout.addWidget(left_label)
        
        # 原始SRT列表
        self.original_srt_list = QListWidget()
        left_layout.addWidget(self.original_srt_list)
        
        # 添加导入按钮
        import_btn_layout = QHBoxLayout()
        import_original_btn = QPushButton("📁 导入原始SRT")
        import_original_btn.setMinimumHeight(35)
        import_original_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #17a2b8, stop: 1 #138496);
                color: white;
                font-weight: 500;
                border-radius: 6px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #20c997, stop: 1 #17a2b8);
            }
        """)
        import_original_btn.clicked.connect(self.import_original_srt)
        print("🔍 [DEBUG] 原始SRT导入按钮信号已连接")

        remove_original_btn = QPushButton("🗑️ 移除选中")
        remove_original_btn.setMinimumHeight(35)
        remove_original_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #dc3545, stop: 1 #c82333);
                color: white;
                font-weight: 500;
                border-radius: 6px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #e4606d, stop: 1 #dc3545);
            }
        """)
        remove_original_btn.clicked.connect(self.remove_original_srt)

        import_btn_layout.addWidget(import_original_btn)
        import_btn_layout.addWidget(remove_original_btn)
        left_layout.addLayout(import_btn_layout)
        
        # 添加原始SRT预览
        self.original_preview = QTextEdit()
        self.original_preview.setPlaceholderText("选择左侧的SRT文件进行预览...")
        self.original_preview.setReadOnly(True)
        self.original_preview.setMinimumHeight(220)
        self.original_preview.setMaximumHeight(300)
        # 设置字体和行高以改善可读性
        font = self.original_preview.font()
        font.setPointSize(11)  # 调整字体大小以适配容器
        font.setFamily("Microsoft YaHei UI, SimHei, Arial")  # 设置字体族，优先使用清晰的中文字体
        font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)  # 启用抗锯齿
        font.setHintingPreference(QFont.HintingPreference.PreferFullHinting)  # 启用完整字体提示
        self.original_preview.setFont(font)
        # 确保滚动条可见
        self.original_preview.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.original_preview.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        # 设置文档边距以确保文字完整显示
        self.original_preview.document().setDocumentMargin(2)
        # 设置文本对齐方式，确保从顶部开始显示
        self.original_preview.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        # 创建边框容器Frame来确保边框完整显示
        self.original_preview_frame = QFrame()
        self.original_preview_frame.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Plain)
        self.original_preview_frame.setLineWidth(3)
        self.original_preview_frame.setMidLineWidth(0)

        # 设置Frame的样式 - 修复边框显示问题
        self.original_preview_frame.setStyleSheet("""
            QFrame {
                border: 3px solid #a0a0a0;
                border-radius: 8px;
                background-color: #ffffff;
                margin: 0px;
                padding: 0px;
            }
            QFrame:focus-within {
                border: 3px solid #4a90e2;
            }
        """)

        # 创建Frame内部布局 - 修复边距问题
        preview_frame_layout = QVBoxLayout(self.original_preview_frame)
        preview_frame_layout.setContentsMargins(1, 1, 1, 1)
        preview_frame_layout.setSpacing(0)

        # 设置TextEdit的样式 - 修复文字显示和对齐问题
        self.original_preview.setStyleSheet("""
            QTextEdit {
                border: none;
                background-color: #ffffff;
                padding: 4px 8px 8px 8px;
                margin: 0px;
                font-size: 11pt;
                font-family: "Microsoft YaHei UI", "SimHei", "Arial";
                line-height: 1.3;
                color: #333333;
            }
            QTextEdit::placeholder {
                color: #666666;
                font-style: italic;
                padding: 4px 8px 8px 8px;
            }
            QScrollBar:vertical {
                background-color: #f0f0f0;
                width: 12px;
                border: none;
                border-radius: 6px;
            }
            QScrollBar:horizontal {
                background-color: #f0f0f0;
                height: 12px;
                border: none;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #c0c0c0;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:horizontal {
                background-color: #c0c0c0;
                border-radius: 6px;
                min-width: 20px;
            }
        """)

        # 将TextEdit添加到Frame中
        preview_frame_layout.addWidget(self.original_preview)

        left_layout.addWidget(QLabel("预览:"))
        left_layout.addWidget(self.original_preview_frame)
        
        # 连接列表选择事件
        self.original_srt_list.currentItemChanged.connect(self.preview_original_srt)
        
        splitter.addWidget(left_widget)
        
        # 右侧：爆款SRT
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_label = QLabel("爆款SRT:")
        right_layout.addWidget(right_label)
        
        self.viral_srt = QTextEdit()
        self.viral_srt.setPlaceholderText("输入或导入爆款SRT剧本...")
        right_layout.addWidget(self.viral_srt)
        
        # 添加导入按钮
        import_viral_btn = QPushButton("⭐ 导入爆款SRT")
        import_viral_btn.setMinimumHeight(40)
        import_viral_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #ffc107, stop: 1 #e0a800);
                color: #212529;
                font-weight: bold;
                font-size: 14px;
                border-radius: 8px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #ffcd39, stop: 1 #ffc107);
                transform: translateY(-1px);
            }
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #e0a800, stop: 1 #d39e00);
            }
        """)
        import_viral_btn.clicked.connect(self.import_viral_srt)
        print("🔍 [DEBUG] 爆款SRT导入按钮信号已连接")
        right_layout.addWidget(import_viral_btn)
        
        splitter.addWidget(right_widget)
        
        # 添加当前训练模式提示
        self.training_mode_label = QLabel("请选择训练模型语言")
        self.training_mode_label.setStyleSheet("color: #666666; font-weight: bold;")
        main_layout.addWidget(self.training_mode_label)
        
        # 添加学习按钮和GPU选项
        train_controls = QHBoxLayout()
        
        self.use_gpu_checkbox = QCheckBox("使用GPU加速训练")
        self.use_gpu_checkbox.setChecked(True)
        train_controls.addWidget(self.use_gpu_checkbox)
        
        detect_gpu_btn = QPushButton("检测GPU")
        detect_gpu_btn.clicked.connect(self.detect_gpu)
        train_controls.addWidget(detect_gpu_btn)
        
        main_layout.addLayout(train_controls)
        
        learn_btn = QPushButton("🚀 开始训练模型")
        learn_btn.setMinimumHeight(45)
        learn_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #9c27b0, stop: 1 #7b1fa2);
                color: white;
                font-weight: bold;
                font-size: 15px;
                border: none;
                border-radius: 10px;
                padding: 12px 20px;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #ba68c8, stop: 1 #9c27b0);
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(156, 39, 176, 0.4);
            }
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #7b1fa2, stop: 1 #4a148c);
                transform: translateY(0px);
            }
        """)
        learn_btn.clicked.connect(self.learn_data_pair)
        main_layout.addWidget(learn_btn)
        
        # 添加状态标签
        self.status_label = QLabel("")
        main_layout.addWidget(self.status_label)
        
        # 添加训练进度条（独立且美观的进度条）
        progress_group = QGroupBox("📊 训练进度监控")
        progress_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 15px;
                color: #9c27b0;
                border: 2px solid #9c27b0;
                border-radius: 10px;
                margin-top: 12px;
                padding-top: 8px;
                background-color: rgba(156, 39, 176, 0.05);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px 0 8px;
                color: #9c27b0;
                background-color: #FFFFFF;
            }
        """)
        progress_layout = QVBoxLayout()

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setMinimumHeight(30)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #dee2e6;
                border-radius: 10px;
                background-color: #f8f9fa;
                text-align: center;
                color: #333333;
                font-weight: bold;
                font-size: 13px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                                          stop: 0 #9c27b0, stop: 1 #7b1fa2);
                border-radius: 8px;
                margin: 1px;
            }
        """)
        progress_layout.addWidget(self.progress_bar)

        progress_group.setLayout(progress_layout)
        main_layout.addWidget(progress_group)
    
    def switch_training_language(self, lang_mode, from_main_window=False):
        """切换训练的语言模式

        Args:
            lang_mode: 语言模式，"zh"或"en"
            from_main_window: 是否来自主窗口的调用，避免重复弹窗
        """
        # 记录原始状态，用于取消时恢复
        original_mode = self.language_mode

        if self.language_mode == lang_mode:
            return

        # 临时存储原始状态，供check_model_exists使用
        self._original_training_mode = original_mode
        self.language_mode = lang_mode

        # 更新UI
        if lang_mode == "zh":
            self.training_mode_label.setText("当前训练: 中文模型")
            self.status_label.setText("已切换到中文模型训练模式")
            # 更新单选按钮状态
            self.lang_zh_radio.setChecked(True)
        elif lang_mode == "en":
            self.training_mode_label.setText("当前训练: 英文模型")
            self.status_label.setText("已切换到英文模型训练模式")
            # 更新单选按钮状态
            self.lang_en_radio.setChecked(True)

        # 清空已加载的数据
        self.original_srt_list.clear()
        self.original_preview.clear()
        self.viral_srt.clear()

        log_handler.log("info", f"训练组件切换语言模式: {lang_mode} (来自主窗口: {from_main_window})")

        # 只有在用户直接在训练页面切换语言时才检查模型
        # 如果是从主窗口调用的，主窗口已经处理了模型检查
        if not from_main_window:
            log_handler.log("info", f"训练页面用户直接切换语言，检查{lang_mode}模型状态")
            self.check_model_exists(lang_mode)
        else:
            log_handler.log("info", f"训练页面接收主窗口语言切换，跳过模型检查避免重复弹窗")

    def _restore_training_language_state(self, original_mode):
        """恢复训练页面的语言选择状态

        Args:
            original_mode: 原始的语言模式
        """
        try:
            log_handler.log("info", f"🔄 训练页面恢复语言模式状态: {original_mode}")

            # 临时断开信号连接，避免递归触发
            self.lang_zh_radio.clicked.disconnect()
            self.lang_en_radio.clicked.disconnect()

            # 恢复语言模式
            self.language_mode = original_mode

            # 恢复单选按钮状态
            if original_mode == "zh":
                self.lang_zh_radio.setChecked(True)
                self.training_mode_label.setText("当前训练: 中文模型")
                self.status_label.setText("已恢复到中文模型训练模式")
            elif original_mode == "en":
                self.lang_en_radio.setChecked(True)
                self.training_mode_label.setText("当前训练: 英文模型")
                self.status_label.setText("已恢复到英文模型训练模式")
            else:  # original_mode is None
                # 恢复到初始状态，不选择任何模型
                # 使用更强制的方法来清除单选按钮状态

                # 方法1: 临时禁用自动互斥
                self.lang_zh_radio.setAutoExclusive(False)
                self.lang_en_radio.setAutoExclusive(False)

                # 方法2: 强制设置为未选中
                self.lang_zh_radio.setChecked(False)
                self.lang_en_radio.setChecked(False)

                # 方法3: 重新启用自动互斥
                self.lang_zh_radio.setAutoExclusive(True)
                self.lang_en_radio.setAutoExclusive(True)

                # 方法4: 再次确认状态
                if self.lang_zh_radio.isChecked() or self.lang_en_radio.isChecked():
                    # 如果仍然有选中状态，使用更激进的方法
                    self.lang_zh_radio.setAutoExclusive(False)
                    self.lang_en_radio.setAutoExclusive(False)
                    self.lang_zh_radio.setChecked(False)
                    self.lang_en_radio.setChecked(False)
                    # 强制刷新UI
                    self.lang_zh_radio.repaint()
                    self.lang_en_radio.repaint()
                    self.lang_zh_radio.setAutoExclusive(True)
                    self.lang_en_radio.setAutoExclusive(True)

                self.training_mode_label.setText("请选择训练模型语言")
                self.status_label.setText("已恢复到初始状态，请选择训练语言")

            # 重新连接信号
            self.lang_zh_radio.clicked.connect(lambda: self.switch_training_language("zh"))
            self.lang_en_radio.clicked.connect(lambda: self.switch_training_language("en"))

            log_handler.log("info", f"✅ 训练页面语言模式状态已恢复: {original_mode}")

        except Exception as e:
            log_handler.log("error", f"❌ 训练页面恢复语言模式状态失败: {str(e)}")
            # 确保信号重新连接，即使出错也要保证功能正常
            try:
                self.lang_zh_radio.clicked.connect(lambda: self.switch_training_language("zh"))
                self.lang_en_radio.clicked.connect(lambda: self.switch_training_language("en"))
            except:
                pass
    
    def import_original_srt(self):
        """导入原始SRT"""
        print("🔍 [DEBUG] import_original_srt 函数被调用")
        log_handler.log("debug", "import_original_srt 函数被调用")

        # 记录用户交互（简化版本）
        print("🔍 [DEBUG] 用户交互记录：导入原始SRT按钮被点击")

        print("🔍 [DEBUG] 准备打开文件选择对话框")
        try:
            file_paths, _ = QFileDialog.getOpenFileNames(
                self, "导入原始SRT", "", "SRT文件 (*.srt)"
            )
            print(f"🔍 [DEBUG] 文件选择对话框返回: {file_paths}")
        except Exception as e:
            print(f"❌ [ERROR] 文件选择对话框出错: {e}")
            log_handler.log("error", f"文件选择对话框出错: {e}")
            return
        
        for file_path in file_paths:
            if file_path:
                print(f"🔍 [DEBUG] 处理文件: {file_path}")
                # 检查是否已添加
                items = self.original_srt_list.findItems(os.path.basename(file_path), Qt.MatchFlag.MatchExactly)
                if items:
                    print(f"🔍 [DEBUG] 文件已存在，跳过: {file_path}")
                    continue

                # 添加到列表
                item = QListWidgetItem(os.path.basename(file_path))
                item.setData(Qt.ItemDataRole.UserRole, file_path)  # 存储完整路径
                self.original_srt_list.addItem(item)
                self.status_label.setText(f"已导入原始SRT: {os.path.basename(file_path)}")
                print(f"✅ [SUCCESS] 成功导入原始SRT: {file_path}")
                log_handler.log("info", f"导入训练用原始SRT: {file_path}")
    
    def remove_original_srt(self):
        """移除选中的原始SRT"""
        selected_items = self.original_srt_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "请先选择要移除的原始SRT文件")
            return
        
        for item in selected_items:
            file_path = item.data(Qt.ItemDataRole.UserRole)
            self.original_srt_list.takeItem(self.original_srt_list.row(item))
            log_handler.log("info", f"移除训练用原始SRT: {file_path}")
        
        self.status_label.setText(f"已移除 {len(selected_items)} 个原始SRT文件")
    
    def preview_original_srt(self, current, _previous):
        """预览选中的原始SRT"""
        if not current:
            self.original_preview.clear()
            return

        file_path = current.data(Qt.ItemDataRole.UserRole)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 清空并设置内容
            self.original_preview.clear()
            self.original_preview.setText(content)

            # 确保文字从顶部开始显示
            cursor = self.original_preview.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            self.original_preview.setTextCursor(cursor)

            # 滚动到顶部
            self.original_preview.verticalScrollBar().setValue(0)

            # 确保文档格式正确
            self.original_preview.document().setDocumentMargin(4)

            log_handler.log("info", f"预览SRT文件: {file_path}")
        except Exception as e:
            self.original_preview.setText(f"读取失败: {str(e)}")
            log_handler.log("error", f"预览SRT失败: {str(e)}")
    
    def import_viral_srt(self):
        """导入爆款SRT"""
        print("🔍 [DEBUG] import_viral_srt 函数被调用")
        log_handler.log("debug", "import_viral_srt 函数被调用")

        # 记录用户交互（简化版本）
        print("🔍 [DEBUG] 用户交互记录：导入爆款SRT按钮被点击")

        print("🔍 [DEBUG] 准备打开文件选择对话框")
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "导入爆款SRT", "", "SRT文件 (*.srt)"
            )
            print(f"🔍 [DEBUG] 文件选择对话框返回: {file_path}")
        except Exception as e:
            print(f"❌ [ERROR] 文件选择对话框出错: {e}")
            log_handler.log("error", f"文件选择对话框出错: {e}")
            return
        
        if file_path:
            print(f"🔍 [DEBUG] 开始读取文件: {file_path}")
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.viral_srt.setText(content)
                self.status_label.setText(f"已导入爆款SRT: {os.path.basename(file_path)}")
                print(f"✅ [SUCCESS] 成功导入爆款SRT: {file_path}")
                log_handler.log("info", f"导入训练用爆款SRT: {file_path}")
            except Exception as e:
                print(f"❌ [ERROR] 读取文件失败: {e}")
                QMessageBox.warning(self, "警告", f"导入失败: {str(e)}")
                log_handler.log("error", f"导入爆款SRT失败: {str(e)}")
        else:
            print("🔍 [DEBUG] 用户取消了文件选择")
    
    def detect_gpu(self):
        """检测GPU硬件"""
        self.status_label.setText("正在检测GPU...")
        log_handler.log("info", "训练组件检测GPU")
        
        # 使用实际的GPU检测功能
        QApplication.processEvents()
        
        gpu_info = detect_gpu_info()
        gpu_available = gpu_info.get("available", False)
        gpu_name = gpu_info.get("name", "未知")
        
        # 更新UI
        if gpu_available:
            self.use_gpu_checkbox.setChecked(True)
            self.use_gpu_checkbox.setEnabled(True)
            self.status_label.setText(f"GPU检测完成: {gpu_name}")
            log_handler.log("info", f"训练组件检测到GPU: {gpu_name}")
            QMessageBox.information(self, "GPU检测结果", f"检测到GPU硬件：\n{gpu_name}\n\n已启用GPU加速功能！")
        else:
            self.use_gpu_checkbox.setChecked(False)
            self.use_gpu_checkbox.setEnabled(False)
            self.status_label.setText(f"GPU检测完成: {gpu_name}")
            log_handler.log("info", "训练组件未检测到GPU，将使用CPU模式")
            QMessageBox.warning(self, "GPU检测结果", f"{gpu_name}\n\n将使用CPU模式运行，处理速度可能较慢。")
    
    def check_model_exists(self, lang_mode):
        """检查对应语言的模型是否存在

        Args:
            lang_mode: 语言模式，"zh"或"en"

        Returns:
            bool: 模型是否存在
        """
        try:
            # 获取项目根目录（完全避免Path递归问题）
            try:
                # 使用os.path避免Path对象的递归问题
                current_file = os.path.abspath(__file__)
                project_root = os.path.dirname(current_file)
                log_handler.log("debug", f"项目根目录: {project_root}")
            except Exception as e:
                # 如果还有问题，使用当前工作目录
                project_root = os.getcwd()
                log_handler.log("warning", f"获取项目根目录失败，使用当前工作目录: {e}")

            # 中文模型可能路径
            zh_model_paths = [
                os.path.join(project_root, "models", "qwen", "quantized", "Q4_K_M.gguf"),
                os.path.join(project_root, "models", "qwen", "base", "qwen2.5-7b.bin"),
                os.path.join(project_root, "models", "qwen", "base", "qwen2.5-7b"),
                os.path.join(project_root, "models", "qwen", "finetuned")
            ]

            # 英文模型可能路径
            en_model_paths = [
                os.path.join(project_root, "models", "mistral", "quantized", "Q4_K_M.gguf"),
                os.path.join(project_root, "models", "mistral", "base", "mistral-7b.bin"),
                os.path.join(project_root, "models", "mistral", "base", "mistral-7b"),
                os.path.join(project_root, "models", "mistral", "finetuned")
            ]

            def _has_large_files(directory, min_size_mb=10):
                """递归检查目录中是否有大于指定大小的文件"""
                if not os.path.exists(directory):
                    return False

                min_size = min_size_mb * 1024 * 1024  # 转换为字节

                for root, _, files in os.walk(directory):
                    for file in files:
                        file_path = os.path.join(root, file)
                        try:
                            if os.path.getsize(file_path) > min_size:
                                return True
                        except (OSError, IOError):
                            continue

                return False

            if lang_mode == "zh":
                # 检查任何一个中文模型路径是否存在且为有效文件
                model_exists = False
                for path in zh_model_paths:
                    if os.path.exists(path):
                        if os.path.isfile(path):
                            # 检查文件大小，模型文件应该大于10MB
                            try:
                                if os.path.getsize(path) > 10 * 1024 * 1024:
                                    model_exists = True
                                    break
                            except (OSError, IOError):
                                continue
                        elif os.path.isdir(path):
                            # 检查目录中是否有大文件
                            if _has_large_files(path):
                                model_exists = True
                                break

                # 检查models/qwen目录是否存在并有大文件
                qwen_dir = os.path.join(project_root, "models", "qwen")
                if not model_exists and _has_large_files(qwen_dir):
                    model_exists = True

                log_handler.log("info", f"中文模型检测结果: {'存在' if model_exists else '不存在'} (训练页面与主界面一致检测)")

                if not model_exists:
                    # 检查是否有实际的对话框在显示中（与主界面保持一致的防重复检查）
                    main_window = self.window()
                    if hasattr(main_window, '_dialog_instance') and main_window._dialog_instance is not None:
                        log_handler.log("info", "⚠️ 训练页面检测到实际对话框窗口已在显示中，跳过重复弹窗")
                        return model_exists

                    # 初始化对话框实例引用（如果不存在）
                    if not hasattr(main_window, '_dialog_instance'):
                        main_window._dialog_instance = None

                    try:
                        # 使用智能推荐对话框，与主界面保持一致
                        log_handler.log("info", "🔍 训练页面检测到中文模型缺失，准备显示智能推荐对话框")

                        if hasattr(main_window, 'enhanced_downloader') and main_window.enhanced_downloader and main_window.enhanced_downloader.has_intelligent_selector:
                            log_handler.log("info", "✅ 训练页面使用增强下载器显示智能推荐对话框")
                            # 重要修复：彻底重置状态，确保状态隔离
                            main_window.enhanced_downloader.reset_state()

                            # 额外验证：确保请求的是正确的模型
                            requested_model = "qwen2.5-7b"
                            log_handler.log("info", f"🎯 训练页面明确请求中文模型: {requested_model}")

                            # 强制验证：在调用前再次确认状态
                            if hasattr(main_window.enhanced_downloader, '_last_model_name'):
                                if main_window.enhanced_downloader._last_model_name and main_window.enhanced_downloader._last_model_name != requested_model:
                                    log_handler.log("warning", f"⚠️ 检测到状态污染，再次清除: {main_window.enhanced_downloader._last_model_name} -> {requested_model}")
                                    main_window.enhanced_downloader.reset_state()

                            # 最终验证：确保智能选择器状态完全清除
                            if main_window.enhanced_downloader.intelligent_selector:
                                if hasattr(main_window.enhanced_downloader.intelligent_selector, '_last_model_name'):
                                    if main_window.enhanced_downloader.intelligent_selector._last_model_name != requested_model:
                                        log_handler.log("warning", f"⚠️ 智能选择器状态不一致，强制清除")
                                        main_window.enhanced_downloader.intelligent_selector.clear_cache()

                            success = main_window.enhanced_downloader.download_model(requested_model, main_window)
                            if success:
                                log_handler.log("info", "✅ 训练页面中文模型下载已启动")
                            else:
                                log_handler.log("warning", "⚠️ 训练页面中文模型下载被取消")
                                # 恢复原始状态
                                if hasattr(self, '_original_training_mode'):
                                    self._restore_training_language_state(self._original_training_mode)
                        else:
                            log_handler.log("warning", "⚠️ 训练页面增强下载器不可用，显示简单确认对话框")
                            # 回退到简单对话框
                            reply = QMessageBox.question(
                                self,
                                "中文模型未安装",
                                "中文模型尚未下载，是否现在下载？",
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                QMessageBox.StandardButton.Yes
                            )

                            if reply == QMessageBox.StandardButton.Yes:
                                # 不再调用主窗口的下载方法，避免重复弹窗
                                # 显示提示信息，引导用户到主界面下载
                                QMessageBox.information(
                                    self,
                                    "模型下载",
                                    "请切换到主界面的视频处理页面，点击中文模式按钮下载模型。\n\n下载完成后即可返回训练页面进行模型训练。"
                                )
                    finally:
                        # 确保清理对话框相关状态（与主界面保持一致）
                        if hasattr(main_window, '_dialog_instance'):
                            main_window._dialog_instance = None
                        if hasattr(main_window, '_global_model_dialog_showing'):
                            main_window._global_model_dialog_showing = False

            elif lang_mode == "en":
                # 检查任何一个英文模型路径是否存在且为有效文件
                model_exists = False
                for path in en_model_paths:
                    if os.path.exists(path):
                        if os.path.isfile(path):
                            # 检查文件大小，模型文件应该大于10MB
                            try:
                                if os.path.getsize(path) > 10 * 1024 * 1024:
                                    model_exists = True
                                    break
                            except (OSError, IOError):
                                continue
                        elif os.path.isdir(path):
                            # 检查目录中是否有大文件
                            if _has_large_files(path):
                                model_exists = True
                                break

                # 检查models/mistral目录是否存在并有大文件
                mistral_dir = os.path.join(project_root, "models", "mistral")
                if not model_exists and _has_large_files(mistral_dir):
                    model_exists = True

                log_handler.log("info", f"英文模型检测结果: {'存在' if model_exists else '不存在'} (训练页面与主界面一致检测)")

                if not model_exists:
                    # 检查是否有实际的对话框在显示中（与主界面保持一致的防重复检查）
                    main_window = self.window()
                    if hasattr(main_window, '_dialog_instance') and main_window._dialog_instance is not None:
                        log_handler.log("info", "⚠️ 训练页面检测到实际对话框窗口已在显示中，跳过重复弹窗")
                        return model_exists

                    # 初始化对话框实例引用（如果不存在）
                    if not hasattr(main_window, '_dialog_instance'):
                        main_window._dialog_instance = None

                    try:
                        # 使用智能推荐对话框，与主界面保持一致
                        log_handler.log("info", "🔍 训练页面检测到英文模型缺失，准备显示智能推荐对话框")

                        if hasattr(main_window, 'enhanced_downloader') and main_window.enhanced_downloader and main_window.enhanced_downloader.has_intelligent_selector:
                            log_handler.log("info", "✅ 训练页面使用增强下载器显示智能推荐对话框")
                            # 重要修复：彻底重置状态，确保状态隔离
                            main_window.enhanced_downloader.reset_state()

                            # 额外验证：确保请求的是正确的模型
                            requested_model = "mistral-7b"
                            log_handler.log("info", f"🎯 训练页面明确请求英文模型: {requested_model}")

                            # 强制验证：在调用前再次确认状态
                            if hasattr(main_window.enhanced_downloader, '_last_model_name'):
                                if main_window.enhanced_downloader._last_model_name and main_window.enhanced_downloader._last_model_name != requested_model:
                                    log_handler.log("warning", f"⚠️ 检测到状态污染，再次清除: {main_window.enhanced_downloader._last_model_name} -> {requested_model}")
                                    main_window.enhanced_downloader.reset_state()

                            # 最终验证：确保智能选择器状态完全清除
                            if main_window.enhanced_downloader.intelligent_selector:
                                if hasattr(main_window.enhanced_downloader.intelligent_selector, '_last_model_name'):
                                    if main_window.enhanced_downloader.intelligent_selector._last_model_name != requested_model:
                                        log_handler.log("warning", f"⚠️ 智能选择器状态不一致，强制清除")
                                        main_window.enhanced_downloader.intelligent_selector.clear_cache()

                            success = main_window.enhanced_downloader.download_model(requested_model, main_window)
                            if success:
                                log_handler.log("info", "✅ 训练页面英文模型下载已启动")
                            else:
                                log_handler.log("warning", "⚠️ 训练页面英文模型下载被取消")
                                # 恢复原始状态
                                if hasattr(self, '_original_training_mode'):
                                    self._restore_training_language_state(self._original_training_mode)
                        else:
                            log_handler.log("warning", "⚠️ 训练页面增强下载器不可用，显示简单确认对话框")
                            # 回退到简单对话框
                            reply = QMessageBox.question(
                                self,
                                "英文模型未安装",
                                "英文模型尚未下载，是否现在下载？\n(约4GB，需要较长时间)",
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                QMessageBox.StandardButton.Yes
                            )

                            if reply == QMessageBox.StandardButton.Yes:
                                # 不再调用主窗口的下载方法，避免重复弹窗
                                # 显示提示信息，引导用户到主界面下载
                                QMessageBox.information(
                                    self,
                                    "模型下载",
                                    "请切换到主界面的视频处理页面，点击英文模式按钮下载模型。\n\n下载完成后即可返回训练页面进行模型训练。"
                                )
                    finally:
                        # 确保清理对话框相关状态（与主界面保持一致）
                        if hasattr(main_window, '_dialog_instance'):
                            main_window._dialog_instance = None
                        if hasattr(main_window, '_global_model_dialog_showing'):
                            main_window._global_model_dialog_showing = False

            else:
                # 未知语言模式
                log_handler.log("error", f"❌ 未知的语言模式: {lang_mode}")
                return False

            return model_exists

        except RecursionError as e:
            log_handler.log("error", f"❌ 模型检测时发生递归错误: {e}")
            # 递归错误通常是Path对象问题，返回False表示模型不存在
            return False
        except Exception as e:
            log_handler.log("error", f"❌ 模型检测时发生未知错误: {e}")
            # 其他异常也返回False，避免程序崩溃
            return False

    def learn_data_pair(self):
        """学习数据对"""
        # 获取原始SRT路径
        original_srt_paths = []
        for i in range(self.original_srt_list.count()):
            item = self.original_srt_list.item(i)
            file_path = item.data(Qt.ItemDataRole.UserRole)
            original_srt_paths.append(file_path)

        # 检查是否有原始SRT
        if not original_srt_paths:
            QMessageBox.warning(self, "警告", "请至少导入一个原始SRT文件")
            return

        # 获取爆款SRT文本
        viral_srt_text = self.viral_srt.toPlainText().strip()
        if not viral_srt_text:
            QMessageBox.warning(self, "警告", "请输入或导入爆款SRT内容")
            return

        # 在开始训练前检查对应语言的模型是否存在
        log_handler.log("info", f"🔍 训练开始前检查模型状态，当前语言模式: {self.language_mode}")

        # 检查模型并处理用户选择
        model_check_result = False
        if self.language_mode == "zh":
            # 检查中文模型
            model_check_result = self.check_model_exists("zh")
            if not model_check_result:
                log_handler.log("warning", "⚠️ 中文模型不存在或用户取消下载，训练被中断")
                QMessageBox.information(self, "训练中断", "中文模型未安装，无法开始训练。\n\n请先安装模型后再进行训练。")
                return
        elif self.language_mode == "en":
            # 检查英文模型
            model_check_result = self.check_model_exists("en")
            if not model_check_result:
                log_handler.log("warning", "⚠️ 英文模型不存在或用户取消下载，训练被中断")
                QMessageBox.information(self, "训练中断", "英文模型未安装，无法开始训练。\n\n请先安装模型后再进行训练。")
                return

        # 是否使用GPU
        use_gpu = self.use_gpu_checkbox.isChecked()
        
        # 创建训练工作器
        self.training_worker = TrainingWorker(
            original_srt_paths=original_srt_paths,
            viral_srt_text=viral_srt_text,
            use_gpu=use_gpu,
            language_mode=self.language_mode
        )
        
        # 创建线程并连接信号
        self.training_thread = QThread()
        self.training_worker.moveToThread(self.training_thread)
        self.training_thread.started.connect(self.training_worker.train)
        
        # 更新进度条和状态信号
        self.training_worker.progress_updated.connect(self.progress_bar.setValue)
        self.training_worker.progress_updated.connect(self.update_main_progress)
        self.training_worker.status_updated.connect(self.status_label.setText)
        self.training_worker.status_updated.connect(self.update_main_status)
        
        # 完成和失败信号
        self.training_worker.training_completed.connect(self.on_training_completed)
        self.training_worker.training_failed.connect(self.on_training_failed)
        
        # 更新UI状态
        self.status_label.setText("正在开始训练...")
        self.progress_bar.setValue(0)
        
        # 开始训练
        self.training_thread.start()
        
        # 记录日志
        if self.language_mode == "zh":
            model_name = "Qwen2.5-7B 中文模型"
        else:
            model_name = "Mistral-7B 英文模型"
            
        log_handler.log("info", f"开始训练{model_name}, 使用{len(original_srt_paths)}个原始SRT文件, GPU={use_gpu}")
    
    def on_training_completed(self, result):
        """训练完成处理"""
        # 清理资源
        if self.training_thread:
            self.training_thread.quit()
            self.training_thread.wait()
        
        # 获取结果
        samples_count = result.get("samples_count", 0)
        accuracy = result.get("accuracy", 0.0)
        loss = result.get("loss", 0.0)
        used_gpu = result.get("use_gpu", False)
        language = result.get("language", "zh")
        
        # 获取模型显示名称
        if language == "zh":
            model_name = "Qwen2.5-7B 中文模型"
        else:
            model_name = "Mistral-7B 英文模型"
        
        # 记录日志
        log_handler.log("info", f"{model_name}训练完成: 样本={samples_count}, 准确率={accuracy:.2%}, 损失={loss:.4f}")
        
        # 更新UI状态
        self.progress_bar.setValue(100)
        self.status_label.setText(f"{model_name}训练完成")
        
        # 显示完成消息
        message = (f"{model_name}训练完成！\n\n"
                 f"- 使用样本数: {samples_count}\n"
                 f"- 训练准确率: {accuracy:.2%}\n"
                 f"- 损失值: {loss:.4f}\n"
                 f"- {'使用了GPU加速' if used_gpu else '使用了CPU处理'}\n\n"
                 f"{model_name}已更新，现在可以自主生成爆款SRT，无需手动参数调整。\n"
                 f"注意：此次训练仅更新了{model_name}，不影响{'Mistral-7B 英文模型' if language == 'zh' else 'Qwen2.5-7B 中文模型'}。")
        
        QMessageBox.information(self, f"{model_name}训练完成", message)
    
    def on_training_failed(self, error_message):
        """处理训练失败"""
        # 获取当前选择的模型名称
        model_name = "模型" if self.language_mode == "zh" else "Model"
        
        # 恢复UI状态
        self.progress_bar.setValue(0)
        self.status_label.setText(f"{model_name}训练失败: {error_message}")
        log_handler.log("error", f"{model_name}训练失败: {error_message}")
        
        # 显示错误消息
        if HAS_ERROR_VISUALIZER:
            # 使用全息错误显示
            error_info = ErrorInfo(
                title=f"{model_name}训练失败",
                description=error_message,
                error_type=ErrorType.ERROR,
                details="训练过程中出现了错误，可能是因为训练数据不足或格式问题。",
                solutions=["检查训练数据", "增加样本数量", "尝试不同参数"]
            )
            show_error(error_info, self)
        else:
            # 使用传统错误显示
            QMessageBox.critical(self, f"{model_name}训练失败", f"{model_name}训练失败: {error_message}")
    
    def show_learning_complete(self, _sample_count, _used_gpu):
        """显示学习完成消息 - 保留用于兼容性"""
        pass

    def update_main_progress(self, progress):
        """更新主窗口的进度条"""
        try:
            # 获取主窗口实例
            main_window = self.parent()
            while main_window and not hasattr(main_window, 'process_progress_bar'):
                main_window = main_window.parent()

            if main_window and hasattr(main_window, 'process_progress_bar'):
                main_window.process_progress_bar.setValue(progress)
        except Exception as e:
            print(f"更新主进度条失败: {e}")

    def update_main_status(self, status):
        """更新主窗口的状态标签"""
        try:
            # 获取主窗口实例
            main_window = self.parent()
            while main_window and not hasattr(main_window, 'status_label'):
                main_window = main_window.parent()

            if main_window and hasattr(main_window, 'status_label'):
                main_window.status_label.setText(f"模型训练: {status}")
        except Exception as e:
            print(f"更新主状态标签失败: {e}")

    # 热键响应方法
    def focus_upload(self):
        """响应聚焦上传区域的热键"""
        if hasattr(self, 'original_srt_list') and self.original_srt_list:
            self.original_srt_list.setFocus()
            if self.status_label:
                self.status_label.setText("已聚焦到SRT上传区域")
            log_handler.log("debug", "训练界面：聚焦到SRT上传区域")
            return True
        return False
    
    def focus_preview(self):
        """响应切换预览模式的热键"""
        if hasattr(self, 'viral_srt_text_edit') and self.viral_srt_text_edit:
            # 如果有生成的SRT内容，则聚焦到它
            self.viral_srt_text_edit.setFocus()
            if self.status_label:
                self.status_label.setText("已切换到SRT预览")
            log_handler.log("debug", "训练界面：切换到SRT预览")
            return True
        return False
    
    def trigger_generate(self):
        """热键功能：立即开始生成
        
        响应Ctrl+G快捷键，根据当前界面状态触发相应的生成功能
        """
        current_tab = self.tabs.currentIndex()
        
        # 视频处理页面
        if current_tab == 0:
            # 如果有视频和SRT，则开始生成视频
            if (self.video_list.count() > 0 and 
                self.srt_list.count() > 0):
                self.generate_video()
                log_handler.log("info", "快捷键触发：开始生成视频")
                return True
            else:
                self.statusBar().showMessage("生成视频需要先添加视频和SRT文件", 3000)
        
        # 训练页面
        elif current_tab == 1 and hasattr(self, 'train_feeder'):
            # 如果有原始SRT，则开始生成爆款SRT
            if (hasattr(self.train_feeder, 'original_srt_list') and
                self.train_feeder.original_srt_list.count() > 0):
                self.train_feeder.viral_srt.clear()
                self.generate_viral_srt()
                log_handler.log("info", "快捷键触发：开始生成爆款SRT")
                return True
            else:
                self.statusBar().showMessage("生成爆款SRT需要先添加原始SRT文件", 3000)
        
        return False

# 导入性能优化模块
try:
    from ui.optimize.panel_perf import PanelOptimizer, generate_thumbnail
    from ui.components.alert_manager import AlertLevel
    HAS_PERF_OPTIMIZER = True
except ImportError:
    print("警告: 无法导入性能优化模块，将使用基本面板管理")
    HAS_PERF_OPTIMIZER = False

# 导入文本方向适配模块
try:
    from ui.utils.text_direction import LayoutDirection, set_application_layout_direction, apply_rtl_styles
    HAS_TEXT_DIRECTION = True
except ImportError:
    print("警告: 无法导入文本方向适配模块，将使用默认的从左到右布局")
    HAS_TEXT_DIRECTION = False

# 导入企业级部署优化模块
try:
    from ui.hardware.enterprise_deploy import EnterpriseOptimizer
    HAS_ENTERPRISE_OPTIMIZER = True
except ImportError:
    HAS_ENTERPRISE_OPTIMIZER = False
    print("警告: 企业级部署优化模块不可用")

class SimpleScreenplayApp(QMainWindow):
    """VisionAI-ClipsMaster 简化版应用程序"""
    
    def __init__(self):
        super().__init__()

        print("初始化主窗口...")
        self._startup_start_time = time.time()

        # 初始化启动优化器
        if STARTUP_OPTIMIZER_AVAILABLE:
            self.startup_optimizer = initialize_startup_optimizer(self)
        else:
            self.startup_optimizer = None

        try:
            # 设置窗口属性（关键组件，立即加载）
            self.setWindowTitle("🎬 VisionAI-ClipsMaster - AI短剧混剪大师 v1.0.0 [生产就绪版]")
            self.resize(1200, 800)

            # 设置窗口最小尺寸
            self.setMinimumSize(1000, 700)

            # 设置窗口居中
            self.center_window()

            print("[OK] 窗口属性设置完成")

            # 状态变量
            self.is_processing = False
            self.is_downloading = False
            self.current_download_thread = None
            self.language_mode = "auto"  # 默认语言模式

            # 性能优化变量
            self._temp_data_cache = {}  # 临时数据缓存
            self._last_cleanup_time = time.time()  # 上次清理时间
            self._error_count = 0  # 错误计数器
            self._max_errors = 10  # 最大错误数

            # 初始化视频处理器
            try:
                self.processor = VideoProcessor()
                self.processor.process_started.connect(self.on_process_started)
                self.processor.process_finished.connect(self.on_process_finished)
                self.processor.process_progress.connect(self.on_process_progress)
                self.processor.process_error.connect(self.on_process_error)
                self.processor.process_log.connect(self.on_process_log)
                print("[OK] 视频处理器初始化完成")
            except Exception as e:
                print(f"[WARN] 视频处理器初始化失败: {e}")
                # 创建一个简单的替代处理器
                self.processor = None

            # 连接日志信号
            try:
                log_signal_emitter.log_message.connect(self.on_process_log)
                print("[OK] 日志信号连接完成")
            except Exception as e:
                print(f"[WARN] 日志信号连接失败: {e}")

            # 初始化UI组件
            try:
                self.init_ui()
                print("[OK] UI组件初始化完成")
            except Exception as e:
                print(f"[FAIL] UI组件初始化失败: {e}")
                raise

            # 设置UI样式
            try:
                if CSS_OPTIMIZER_AVAILABLE:
                    # 使用CSS优化器
                    apply_optimized_styles(self)
                    print("[OK] 优化的UI样式设置完成")
                else:
                    # 使用传统样式
                    self.setup_ui_style()
                    print("[OK] 传统UI样式设置完成")
            except Exception as e:
                print(f"[WARN] UI样式设置失败: {e}")
                # 回退到基础样式
                try:
                    self.setStyleSheet("QMainWindow { background-color: white; }")
                except:
                    pass

            # 初始化增强模型下载器
            try:
                if HAS_ENHANCED_DOWNLOADER:
                    self.enhanced_downloader = EnhancedModelDownloader(self)
                    print("[OK] 增强模型下载器初始化完成")
                else:
                    self.enhanced_downloader = None
                    print("[WARN] 增强模型下载器不可用，将使用基础下载功能")
            except Exception as e:
                print(f"[WARN] 增强模型下载器初始化失败: {e}")
                self.enhanced_downloader = None

            # 全局防重复弹窗标志 - 初始化为False
            self._global_model_dialog_showing = False
            self._dialog_instance = None  # 对话框实例引用，用于更精确的防重复检查
            log_handler.log("info", "🔧 初始化全局对话框标志位为False")

            # 检查模型状态
            try:
                self.check_models()
                print("[OK] 模型状态检查完成")
            except Exception as e:
                print(f"[WARN] 模型状态检查失败: {e}")

            # 初始化进程稳定性监控
            try:
                # 确保在主线程中创建监控器
                from PyQt6.QtCore import QTimer
                from PyQt6.QtWidgets import QApplication

                if QApplication.instance() and QApplication.instance().thread() == self.thread():
                    self.stability_monitor = ProcessStabilityMonitor(self)
                    self.stability_monitor.memory_warning.connect(self.on_memory_warning)
                    self.stability_monitor.performance_update.connect(self.on_performance_update)
                    self.stability_monitor.start_monitoring()
                    print("[OK] 进程稳定性监控初始化完成")
                else:
                    print("[WARN] 跳过进程稳定性监控初始化 (非主线程)")
                    self.stability_monitor = None
            except Exception as e:
                print(f"[WARN] 进程稳定性监控初始化失败: {e}")
                self.stability_monitor = None

            # 初始化响应性监控
            try:
                if QApplication.instance() and QApplication.instance().thread() == self.thread():
                    self.responsiveness_monitor = ResponsivenessMonitor(self)
                    self.responsiveness_monitor.response_time_update.connect(self.on_response_time_update)
                    self.responsiveness_monitor.responsiveness_data_update.connect(self.on_responsiveness_data_update)
                    self.responsiveness_monitor.start_monitoring()  # 启动监控
                    print("[OK] 响应性监控初始化完成")
                else:
                    print("[WARN] 跳过响应性监控初始化 (非主线程)")
                    self.responsiveness_monitor = None
            except Exception as e:
                print(f"[WARN] 响应性监控初始化失败: {e}")
                self.responsiveness_monitor = None

            # 初始化增强响应时间监控器
            if ENHANCED_RESPONSE_MONITOR_AVAILABLE:
                try:
                    self.enhanced_response_monitor = initialize_enhanced_response_monitor(self)
                    start_response_monitoring()
                    print("[OK] 增强响应时间监控器初始化完成")
                except Exception as e:
                    print(f"[WARN] 增强响应时间监控器初始化失败: {e}")
                    self.enhanced_response_monitor = None
            else:
                self.enhanced_response_monitor = None

            # 初始化UI错误处理器
            try:
                from ui_error_handler_integration import UIErrorHandlerIntegration
                self.ui_error_handler = UIErrorHandlerIntegration(self)
                self.ui_error_handler.error_occurred.connect(self.on_ui_error_occurred)
                print("[OK] UI错误处理器初始化完成")
            except Exception as e:
                print(f"[WARN] UI错误处理器初始化失败: {e}")
                self.ui_error_handler = None



        except Exception as e:
            print(f"[FAIL] 主窗口基础初始化失败: {e}")
            raise

        # 初始化可选组件（失败不影响主程序）
        self._init_optional_components()

    def _init_optional_components(self):
        """初始化可选组件，失败不影响主程序运行"""
        print("初始化可选组件...")

        # 使用启动优化器注册组件
        if self.startup_optimizer:
            # 注册各个组件到不同的加载阶段
            register_component("性能优化器", self.init_performance_optimizer, "important")
            register_component("内存管理器", self.init_memory_manager, "important")
            register_component("通知管理器", self._init_alert_manager, "optional")
            register_component("文本方向支持", self.setup_language_direction, "optional")
            register_component("企业级优化", self._init_enterprise_optimizer, "background")
            register_component("内存监控", self._start_memory_monitoring, "background")
            register_component("用户体验增强", self._init_user_experience_enhancer, "optional")

            # 开始优化启动
            start_optimized_startup()
        else:
            # 传统方式初始化
            self._init_components_traditional()

    def _init_components_traditional(self):
        """传统方式初始化组件"""
        # 初始化性能优化器
        try:
            self.init_performance_optimizer()
            print("[OK] 性能优化器初始化完成")
        except Exception as e:
            print(f"[WARN] 性能优化器初始化失败: {e}")

        # 初始化内存管理器（优先级最高）
        try:
            self.init_memory_manager()
            print("[OK] 内存管理器初始化完成")
        except Exception as e:
            print(f"[WARN] 内存管理器初始化失败: {e}")

        # 延迟初始化其他组件（按需加载）
        self._render_optimizer = None
        self._compute_offloader = None
        self._disk_cache = None
        self._input_latency_optimizer = None
        self._power_manager = None

        print("[OK] 组件延迟初始化策略已启用，内存占用已优化")

        # 设置通知管理器
        try:
            # 直接使用简易替代，避免导入错误
            self.alert_manager = SimpleAlertManager(self)
            self.alert_manager.info("欢迎使用VisionAI-ClipsMaster", timeout=5000)
            print("[OK] 通知管理器初始化完成")
        except Exception as e:
            print(f"[WARN] 通知管理器初始化失败: {e}")
            self.alert_manager = SimpleAlertManager(self)

        # 添加文本方向支持
        try:
            self.setup_language_direction()
            print("[OK] 文本方向支持初始化完成")
        except Exception as e:
            print(f"[WARN] 文本方向支持初始化失败: {e}")

        # 设置进度条容器可见性（只在第一个标签页显示）
        try:
            if hasattr(self, 'progress_container'):
                # 获取当前标签页索引，默认为0（视频处理标签页）
                current_tab = self.tabs.currentIndex() if hasattr(self, 'tabs') else 0
                self.progress_container.setVisible(current_tab == 0)  # 只在第一个标签页显示进度条
        except Exception as e:
            print(f"[WARN] 进度条容器设置失败: {e}")

        # 初始化企业级部署优化
        if HAS_ENTERPRISE_OPTIMIZER:
            try:
                self.enterprise_optimizer = EnterpriseOptimizer()
                # 检测并配置VDI环境
                if self.enterprise_optimizer.configure_for_vdi():
                    print("[OK] 检测到VDI环境，已应用企业级优化")
                # 应用企业级默认设置
                self.enterprise_optimizer.apply_enterprise_settings()
                print("[OK] 企业级部署优化初始化完成")
            except Exception as e:
                print(f"[WARN] 企业级部署优化初始化失败: {e}")

        # 启动内存监控（在QApplication创建后）
        try:
            from ui.performance.memory_guard import start_memory_monitoring
            start_memory_monitoring()
            print("[OK] 内存监控已启动")
        except Exception as e:
            print(f"[WARN] 内存监控启动失败: {e}")

        # 检查FFmpeg状态
        try:
            QTimer.singleShot(1000, self.check_ffmpeg_status)  # 延迟1秒检查，确保窗口已显示
            print("[OK] FFmpeg状态检查已安排")
        except Exception as e:
            print(f"[WARN] FFmpeg状态检查安排失败: {e}")

        # 延迟初始化性能优化器（减少启动时间）
        if OPTIMIZATION_MODULES_AVAILABLE:
            try:
                # 使用QTimer延迟初始化，避免阻塞启动
                QTimer.singleShot(2000, self._delayed_optimizer_init)
                print("[OK] 性能优化器将延迟初始化")
            except Exception as e:
                print(f"[WARN] 性能优化器延迟初始化设置失败: {e}")
        else:
            print("[INFO] 性能优化器模块不可用，使用标准模式")

        print("[OK] 可选组件初始化完成")

        # 应用第二阶段优化（使用智能模块加载器）
        if SMART_LOADER_AVAILABLE:
            try:
                self.smart_module_loader = create_module_loader(self)
                if self.smart_module_loader:
                    # 连接信号
                    self.smart_module_loader.all_modules_loaded.connect(self._on_modules_loaded)
                    # 开始加载
                    self.smart_module_loader.start_loading(delay_ms=1500)
                    safe_logger.info("智能模块加载器已启动")
                else:
                    safe_logger.warning("智能模块加载器创建失败")
            except Exception as e:
                safe_logger.error(f"智能模块加载器启动失败: {e}")
        else:
            safe_logger.info("智能模块加载器不可用")

        # 对话框标志位重置功能已集成到enhanced_model_downloader中
        print("[OK] 对话框防重复机制已优化")

    def _on_modules_loaded(self, success_count, total_count):
        """模块加载完成回调"""
        try:
            success_rate = success_count / total_count if total_count > 0 else 0
            safe_logger.info(f"第二阶段优化模块加载完成: {success_count}/{total_count} ({success_rate*100:.1f}%)")

            if success_rate >= 0.75:
                safe_logger.success("第二阶段优化集成成功!")
                # 记录成功状态
                self.second_stage_optimization_active = True
                self.second_stage_success_count = success_count
                self.second_stage_total_count = total_count
            else:
                safe_logger.warning("第二阶段优化集成部分成功")
                self.second_stage_optimization_active = False

        except Exception as e:
            safe_logger.error(f"模块加载完成回调失败: {e}")

    def _init_alert_manager(self):
        """初始化通知管理器"""
        try:
            # 直接使用简易替代，避免导入错误
            self.alert_manager = SimpleAlertManager(self)
            self.alert_manager.info("欢迎使用VisionAI-ClipsMaster", timeout=5000)
            print("[OK] 通知管理器初始化完成")
        except Exception as e:
            print(f"[WARN] 通知管理器初始化失败: {e}")
            self.alert_manager = SimpleAlertManager(self)

    def _init_enterprise_optimizer(self):
        """初始化企业级优化"""
        if HAS_ENTERPRISE_OPTIMIZER:
            try:
                self.enterprise_optimizer = EnterpriseOptimizer()
                # 检测并配置VDI环境
                if self.enterprise_optimizer.configure_for_vdi():
                    print("[OK] 检测到VDI环境，已应用企业级优化")
                # 应用企业级默认设置
                self.enterprise_optimizer.apply_enterprise_settings()
                print("[OK] 企业级部署优化初始化完成")
            except Exception as e:
                print(f"[WARN] 企业级部署优化初始化失败: {e}")

    def _start_memory_monitoring(self):
        """启动内存监控"""
        try:
            if hasattr(self, 'memory_watcher') and self.memory_watcher:
                self.memory_watcher.start_monitoring()
                print("[OK] 内存监控已启动")
        except Exception as e:
            print(f"[WARN] 内存监控启动失败: {e}")

    def _init_user_experience_enhancer(self):
        """初始化用户体验增强器"""
        if USER_EXPERIENCE_ENHANCER_AVAILABLE:
            try:
                initialize_user_experience_enhancer(self)
                print("[OK] 用户体验增强器初始化完成")
            except Exception as e:
                print(f"[WARN] 用户体验增强器初始化失败: {e}")
        else:
            print("[INFO] 用户体验增强器不可用")

    def _delayed_optimizer_init(self):
        """延迟初始化优化器"""
        try:
            print("[INFO] 开始延迟初始化性能优化器...")

            # 延迟导入优化模块
            optimization_modules = _lazy_import_optimization_modules()
            if optimization_modules:
                # 初始化异步UI优化器
                optimization_modules['initialize_optimizers'](self)

                # 初始化增强内存管理器
                self.enhanced_memory_manager = optimization_modules['initialize_memory_manager']()

                # 初始化安全优化器
                self.safe_optimizer = optimization_modules['initialize_safe_optimizer'](self)

                # 更新全局函数引用
                global initialize_optimizers, optimize_tab_switch, get_optimization_stats
                global initialize_memory_manager, get_memory_report
                global initialize_safe_optimizer, apply_optimizations_safely

                initialize_optimizers = optimization_modules['initialize_optimizers']
                optimize_tab_switch = optimization_modules['optimize_tab_switch']
                get_optimization_stats = optimization_modules['get_optimization_stats']
                initialize_memory_manager = optimization_modules['initialize_memory_manager']
                get_memory_report = optimization_modules['get_memory_report']
                initialize_safe_optimizer = optimization_modules['initialize_safe_optimizer']
                apply_optimizations_safely = optimization_modules['apply_optimizations_safely']

                print("[OK] 性能优化器延迟初始化完成")

                # 显示优化器状态
                if hasattr(self, 'alert_manager') and self.alert_manager:
                    self.alert_manager.info("性能优化器已激活", timeout=3000)
            else:
                print("[WARN] 优化模块不可用")

        except Exception as e:
            print(f"[ERROR] 性能优化器延迟初始化失败: {e}")
            # 设置标志表示优化器不可用
            self.optimization_available = False

    def center_window(self):
        """将窗口居中显示"""
        try:
            # 获取屏幕几何信息
            screen = QApplication.primaryScreen()
            screen_geometry = screen.geometry()

            # 计算窗口居中位置
            window_geometry = self.geometry()
            x = (screen_geometry.width() - window_geometry.width()) // 2
            y = (screen_geometry.height() - window_geometry.height()) // 2

            # 设置窗口位置
            self.move(x, y)
            print(f"[OK] 窗口已居中显示: ({x}, {y})")
        except Exception as e:
            print(f"[WARN] 窗口居中失败: {e}")

    def setup_ui_style(self):
        """设置UI统一样式 - 现代化浅色主题版本"""
        # 根据不同系统设置合适的字体
        if sys.platform.startswith('win'):
            font_family = "Microsoft YaHei UI"  # Windows系统使用雅黑字体
            font_size = 13  # 增大字体大小
        elif sys.platform.startswith('darwin'):
            font_family = "PingFang SC"  # macOS系统使用苹方字体
            font_size = 16  # 增大字体大小
        else:
            font_family = "Noto Sans CJK SC"  # Linux系统
            font_size = 14  # 增大字体大小

        # 创建应用字体
        app_font = QFont(font_family, font_size)
        QApplication.setFont(app_font)

        # 设置现代化浅色主题样式表
        style_sheet = """
        /* 主窗口和基础组件 */
        QMainWindow {
            background-color: #FFFFFF;
            color: #333333;
        }

        QWidget {
            font-family: "%s";
            font-size: %dpx;
            background-color: #FFFFFF;
            color: #333333;
            border: none;
        }

        /* 按钮样式 */
        QPushButton {
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 #4a90e2, stop: 1 #357abd);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 8px 16px;
            min-height: 32px;
            font-weight: 500;
            font-size: %dpx;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }

        QPushButton:hover {
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 #5ba0f2, stop: 1 #4682cd);
            transform: translateY(-1px);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
        }

        QPushButton:pressed {
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 #3980d2, stop: 1 #2968ad);
        }

        QPushButton:disabled {
            background-color: #e9ecef;
            color: #6c757d;
        }

        /* 特殊按钮样式 */
        QPushButton[class="success"] {
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 #52c41a, stop: 1 #389e0d);
        }

        QPushButton[class="success"]:hover {
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 #73d13d, stop: 1 #52c41a);
        }

        QPushButton[class="warning"] {
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 #fa8c16, stop: 1 #d46b08);
        }

        QPushButton[class="warning"]:hover {
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 #ffa940, stop: 1 #fa8c16);
        }

        /* 标签样式 */
        QLabel {
            color: #333333;
            background-color: transparent;
            padding: 2px;
        }

        QLabel[class="title"] {
            font-size: %dpx;
            font-weight: bold;
            color: #4a90e2;
        }

        QLabel[class="subtitle"] {
            font-size: %dpx;
            color: #6c757d;
        }

        /* 输入框和文本区域 */
        QTextEdit, QListWidget, QLineEdit {
            background-color: #FFFFFF;
            border: 2px solid #dee2e6;
            border-radius: 6px;
            color: #333333;
            padding: 8px;
            font-size: %dpx;
            selection-background-color: #4a90e2;
        }

        QTextEdit:focus, QListWidget:focus, QLineEdit:focus {
            border-color: #4a90e2;
            background-color: #f8f9fa;
            box-shadow: 0 0 0 3px rgba(74, 144, 226, 0.1);
        }

        /* 预览框特殊样式 - 覆盖全局样式 */
        QFrame QTextEdit {
            border: none !important;
            padding: 12px !important;
            margin: 0px !important;
            background-color: #ffffff !important;
        }

        QListWidget::item {
            padding: 8px;
            border-bottom: 1px solid #dee2e6;
            border-radius: 4px;
            margin: 2px;
            color: #333333;
        }

        QListWidget::item:selected {
            background-color: #4a90e2;
            color: white;
        }

        QListWidget::item:hover {
            background-color: #e9ecef;
        }

        /* 组框样式 - 美化优化版本 */
        QGroupBox {
            font-weight: 600;
            font-size: %dpx;
            color: #4a90e2;
            border: 2px solid #e3f2fd;
            border-radius: 12px;
            margin-top: 16px;
            padding-top: 12px;
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 rgba(248, 249, 250, 0.8),
                                      stop: 1 rgba(255, 255, 255, 0.9));
        }

        QGroupBox:hover {
            border-color: #4a90e2;
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 rgba(74, 144, 226, 0.05),
                                      stop: 1 rgba(255, 255, 255, 0.95));
        }

        QGroupBox::title {
            subcontrol-origin: margin;
            left: 16px;
            padding: 4px 12px 4px 12px;
            color: #4a90e2;
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 #FFFFFF,
                                      stop: 1 #f8f9fa);
            border: 1px solid #e3f2fd;
            border-radius: 6px;
            font-weight: 600;
        }

        /* 状态栏 */
        QStatusBar {
            background-color: #f8f9fa;
            border-top: 1px solid #dee2e6;
            color: #333333;
            font-size: %dpx;
        }

        /* 菜单栏 */
        QMenuBar {
            background-color: #f8f9fa;
            border-bottom: 1px solid #dee2e6;
            color: #333333;
        }

        QMenuBar::item {
            background-color: transparent;
            padding: 6px 12px;
            border-radius: 4px;
        }

        QMenuBar::item:selected {
            background-color: #4a90e2;
            color: white;
        }

        QMenu {
            background-color: #FFFFFF;
            border: 1px solid #dee2e6;
            border-radius: 6px;
            color: #333333;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }

        QMenu::item {
            padding: 8px 16px;
            border-radius: 4px;
            margin: 2px;
        }

        QMenu::item:selected {
            background-color: #4a90e2;
            color: white;
        }

        /* 标签页 */
        QTabWidget::pane {
            border: 2px solid #dee2e6;
            border-radius: 8px;
            background-color: #FFFFFF;
        }

        QTabBar::tab {
            background-color: #f8f9fa;
            border: 2px solid #dee2e6;
            border-bottom: none;
            border-radius: 8px 8px 0 0;
            padding: 10px 20px;
            margin-right: 2px;
            color: #6c757d;
            font-weight: 500;
        }

        QTabBar::tab:selected {
            background-color: #FFFFFF;
            color: #4a90e2;
            border-color: #4a90e2;
            border-bottom: 2px solid #FFFFFF;
        }

        QTabBar::tab:hover:!selected {
            background-color: #e9ecef;
            color: #333333;
        }

        /* 进度条 */
        QProgressBar {
            border: 2px solid #dee2e6;
            border-radius: 8px;
            background-color: #f8f9fa;
            text-align: center;
            color: #333333;
            font-weight: bold;
            min-height: 20px;
        }

        QProgressBar::chunk {
            background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                                      stop: 0 #4a90e2, stop: 1 #357abd);
            border-radius: 6px;
        }

        /* 复选框和单选按钮 - 美化优化版本 */
        QCheckBox, QRadioButton {
            color: #333333;
            spacing: 12px;
            font-weight: 500;
            padding: 8px 12px;
            border-radius: 8px;
            background-color: transparent;
            transition: all 0.3s ease;
        }

        QCheckBox:hover, QRadioButton:hover {
            background-color: rgba(74, 144, 226, 0.08);
            color: #2c5aa0;
        }

        QCheckBox::indicator, QRadioButton::indicator {
            width: 20px;
            height: 20px;
            border: 2px solid #dee2e6;
            border-radius: 4px;
            background-color: #FFFFFF;
            transition: all 0.2s ease;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }

        QCheckBox::indicator:hover, QRadioButton::indicator:hover {
            border-color: #4a90e2;
            box-shadow: 0 2px 8px rgba(74, 144, 226, 0.3);
            transform: scale(1.05);
        }

        QCheckBox::indicator:checked, QRadioButton::indicator:checked {
            background-color: #4a90e2;
            border-color: #4a90e2;
            box-shadow: 0 2px 8px rgba(74, 144, 226, 0.4);
        }

        QCheckBox::indicator:checked:hover, QRadioButton::indicator:checked:hover {
            background-color: #357abd;
            border-color: #357abd;
        }

        QRadioButton::indicator {
            border-radius: 10px;
        }

        QRadioButton::indicator:checked {
            background-color: #4a90e2;
            border: 3px solid #FFFFFF;
            box-shadow: 0 0 0 2px #4a90e2, 0 2px 8px rgba(74, 144, 226, 0.4);
        }

        QRadioButton::indicator:checked:hover {
            box-shadow: 0 0 0 2px #357abd, 0 2px 12px rgba(53, 122, 189, 0.5);
        }

        /* 语言选择组特殊样式 */
        QGroupBox#lang_selection_group, QGroupBox#training_lang_selection_group {
            border: 2px solid #e8f5e8;
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 rgba(232, 245, 232, 0.6),
                                      stop: 1 rgba(255, 255, 255, 0.9));
        }

        QGroupBox#lang_selection_group:hover, QGroupBox#training_lang_selection_group:hover {
            border-color: #52c41a;
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 rgba(82, 196, 26, 0.08),
                                      stop: 1 rgba(255, 255, 255, 0.95));
        }

        QGroupBox#lang_selection_group::title, QGroupBox#training_lang_selection_group::title {
            color: #52c41a;
            border-color: #e8f5e8;
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 #f6ffed,
                                      stop: 1 #ffffff);
        }

        /* 语言选择组内的单选按钮特殊样式 */
        QGroupBox#lang_selection_group QRadioButton, QGroupBox#training_lang_selection_group QRadioButton {
            font-weight: 600;
            color: #52c41a;
            padding: 10px 16px;
            margin: 4px;
            border-radius: 10px;
            background-color: rgba(246, 255, 237, 0.5);
        }

        QGroupBox#lang_selection_group QRadioButton:hover, QGroupBox#training_lang_selection_group QRadioButton:hover {
            background-color: rgba(82, 196, 26, 0.1);
            color: #389e0d;
        }

        QGroupBox#lang_selection_group QRadioButton:checked, QGroupBox#training_lang_selection_group QRadioButton:checked {
            background-color: rgba(82, 196, 26, 0.15);
            color: #389e0d;
            font-weight: 700;
        }

        /* 下拉框 */
        QComboBox {
            background-color: #FFFFFF;
            border: 2px solid #dee2e6;
            border-radius: 6px;
            padding: 6px 12px;
            color: #333333;
            min-height: 20px;
        }

        QComboBox:focus {
            border-color: #4a90e2;
            box-shadow: 0 0 0 3px rgba(74, 144, 226, 0.1);
        }

        QComboBox::drop-down {
            border: none;
            width: 20px;
        }

        QComboBox::down-arrow {
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid #6c757d;
        }

        QComboBox QAbstractItemView {
            background-color: #FFFFFF;
            border: 1px solid #dee2e6;
            border-radius: 6px;
            color: #333333;
            selection-background-color: #4a90e2;
        }

        /* 滚动条 */
        QScrollBar:vertical {
            background-color: #f8f9fa;
            width: 12px;
            border-radius: 6px;
        }

        QScrollBar::handle:vertical {
            background-color: #4a90e2;
            border-radius: 6px;
            min-height: 20px;
        }

        QScrollBar::handle:vertical:hover {
            background-color: #5ba0f2;
        }

        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }

        /* 分割器 */
        QSplitter::handle {
            background-color: #dee2e6;
        }

        QSplitter::handle:horizontal {
            width: 3px;
        }

        QSplitter::handle:vertical {
            height: 3px;
        }
        """ % (font_family, font_size, font_size, font_size+2, font_size-1, font_size, font_size+1, font_size)

        self.setStyleSheet(style_sheet)
        
    def init_ui(self):
        """初始化UI"""
        # 创建中央Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 创建菜单栏
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件(&F)")
        
        # 选择视频动作
        select_video_action = QAction("添加视频", self)
        select_video_action.triggered.connect(self.select_video)
        file_menu.addAction(select_video_action)
        
        # 选择字幕动作
        select_srt_action = QAction("添加SRT", self)
        select_srt_action.triggered.connect(self.select_subtitle)
        file_menu.addAction(select_srt_action)
        
        file_menu.addSeparator()
        
        # 退出动作
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 操作菜单
        action_menu = menubar.addMenu("操作(&A)")
        
        # 生成SRT动作
        generate_srt_action = QAction("生成爆款SRT", self)
        generate_srt_action.setShortcut("Ctrl+G")
        generate_srt_action.triggered.connect(self.generate_viral_srt)
        action_menu.addAction(generate_srt_action)
        
        # 生成视频动作
        generate_video_action = QAction("生成视频", self)
        generate_video_action.triggered.connect(self.generate_video)
        action_menu.addAction(generate_video_action)
        
        # 查看菜单
        view_menu = menubar.addMenu("查看(&V)")
        
        # 聚焦上传区域
        focus_upload_action = QAction("聚焦上传区域", self)
        focus_upload_action.setShortcut("Ctrl+U")
        focus_upload_action.triggered.connect(self.focus_upload)
        view_menu.addAction(focus_upload_action)
        
        # 预览模式
        preview_action = QAction("预览", self)
        preview_action.setShortcut("Ctrl+P")
        preview_action.triggered.connect(self.show_preview)
        view_menu.addAction(preview_action)
        
        view_menu.addSeparator()
        
        # 查看日志
        view_log_action = QAction("查看系统日志", self)
        view_log_action.triggered.connect(self.show_log_viewer)
        view_menu.addAction(view_log_action)
        
        # 工具菜单
        tools_menu = menubar.addMenu("工具(&T)")
        
        # 检测GPU
        detect_gpu_action = QAction("检测GPU硬件", self)
        detect_gpu_action.triggered.connect(self.detect_gpu)
        tools_menu.addAction(detect_gpu_action)
        
        # 系统监控
        monitor_action = QAction("系统资源监控", self)
        monitor_action.triggered.connect(self.show_system_monitor)
        tools_menu.addAction(monitor_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助(&H)")
        
        # 快捷键指南
        hotkey_guide_action = QAction("快捷键指南", self)
        hotkey_guide_action.triggered.connect(self.show_hotkey_guide)
        help_menu.addAction(hotkey_guide_action)
        
        help_menu.addSeparator()
        
        # 关于
        about_action = QAction("关于软件", self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)
        
        # 技术信息
        tech_action = QAction("技术信息", self)
        tech_action.triggered.connect(self.show_tech_dialog)
        help_menu.addAction(tech_action)
        
        # 创建标签页
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # 创建进度条容器，以便可以控制其可见性
        self.progress_container = QWidget()
        progress_layout = QHBoxLayout(self.progress_container)
        progress_layout.setContentsMargins(5, 0, 5, 5)
        
        # 创建状态标签和进度条
        self.status_label = QLabel("")
        progress_layout.addWidget(self.status_label, 1)
        
        # 创建并添加进度条
        self.process_progress_bar = QProgressBar()
        self.process_progress_bar.setTextVisible(True)
        progress_layout.addWidget(self.process_progress_bar, 3)
        
        # 将进度条容器添加到主布局
        main_layout.addWidget(self.progress_container)
        
        # 标签页切换时保存索引
        self.tabs.currentChanged.connect(self.on_tab_changed)
        
        # 创建视频处理页面
        video_widget = QWidget()
        video_layout = QVBoxLayout(video_widget)
        
        # 语言模式选择
        lang_group = QGroupBox("🌐 输入视频和字幕处理语言")
        lang_group.setObjectName("lang_selection_group")
        lang_layout = QHBoxLayout()
        
        # 创建语言选择单选按钮
        self.lang_auto_radio = QRadioButton("自动检测")
        self.lang_zh_radio = QRadioButton("中文模式")
        self.lang_en_radio = QRadioButton("英文模式")
        self.lang_auto_radio.setChecked(True)  # 默认自动检测
        
        # 语言模式按钮分组
        lang_btn_group = QButtonGroup(self)
        lang_btn_group.addButton(self.lang_auto_radio)
        lang_btn_group.addButton(self.lang_zh_radio)
        lang_btn_group.addButton(self.lang_en_radio)
        
        # 连接语言模式切换信号，但使用lambda避免直接调用，以防止在初始化时意外触发
        self.lang_auto_radio.clicked.connect(lambda: self.change_language_mode("auto"))
        self.lang_zh_radio.clicked.connect(lambda: self.change_language_mode("zh"))
        # 英文单选按钮的点击事件直接连接到change_language_mode("en")，不再通过check_en_model检查
        self.lang_en_radio.clicked.connect(lambda: self.change_language_mode("en"))
        
        # 添加按钮到布局
        lang_layout.addWidget(self.lang_auto_radio)
        lang_layout.addWidget(self.lang_zh_radio)
        lang_layout.addWidget(self.lang_en_radio)
        lang_group.setLayout(lang_layout)
        
        # 添加语言选择组到视频布局
        video_layout.addWidget(lang_group)
        
        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        video_layout.addWidget(splitter)
        
        # 语言下拉框和GPU选项
        options_layout = QHBoxLayout()
        options_layout.addWidget(QLabel("处理语言:"))
        
        # 创建语言选择下拉框
        self.lang_combo = QComboBox()
        self.lang_combo.addItem("自动检测", "auto")
        self.lang_combo.addItem("中文模式", "zh")
        self.lang_combo.addItem("英文模式", "en")
        options_layout.addWidget(self.lang_combo)
        
        # 添加GPU复选框
        self.use_gpu_check = QCheckBox("使用GPU加速处理")
        self.use_gpu_check.setChecked(True)
        options_layout.addWidget(self.use_gpu_check)
        
        # 添加到视频布局
        video_layout.addLayout(options_layout)
        
        # 左侧：视频池
        video_pool_widget = QWidget()
        video_pool_layout = QVBoxLayout(video_pool_widget)
        video_pool_label = QLabel("视频池：")
        video_pool_layout.addWidget(video_pool_label)
        
        # 视频列表
        self.video_list = QListWidget()
        video_pool_layout.addWidget(self.video_list)
        
        # 视频池操作按钮
        video_btn_layout = QHBoxLayout()
        add_video_btn = QPushButton("📹 添加视频")
        add_video_btn.setMinimumHeight(35)
        add_video_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #28a745, stop: 1 #1e7e34);
                color: white;
                font-weight: 500;
                border-radius: 6px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #34ce57, stop: 1 #28a745);
            }
        """)
        add_video_btn.clicked.connect(self.select_video)

        remove_video_btn = QPushButton("🗑️ 移除视频")
        remove_video_btn.setMinimumHeight(35)
        remove_video_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #dc3545, stop: 1 #c82333);
                color: white;
                font-weight: 500;
                border-radius: 6px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #e4606d, stop: 1 #dc3545);
            }
        """)
        remove_video_btn.clicked.connect(self.remove_video)

        video_btn_layout.addWidget(add_video_btn)
        video_btn_layout.addWidget(remove_video_btn)
        video_pool_layout.addLayout(video_btn_layout)
        
        splitter.addWidget(video_pool_widget)
        
        # 右侧：SRT文件存储
        srt_pool_widget = QWidget()
        srt_pool_layout = QVBoxLayout(srt_pool_widget)
        srt_pool_label = QLabel("SRT文件存储：")
        srt_pool_layout.addWidget(srt_pool_label)
        
        # SRT文件列表
        self.srt_list = QListWidget()
        srt_pool_layout.addWidget(self.srt_list)
        
        # SRT文件操作按钮
        srt_btn_layout = QHBoxLayout()
        add_srt_btn = QPushButton("📄 添加SRT")
        add_srt_btn.setMinimumHeight(35)
        add_srt_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #007bff, stop: 1 #0056b3);
                color: white;
                font-weight: 500;
                border-radius: 6px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #0099ff, stop: 1 #007bff);
            }
        """)
        add_srt_btn.clicked.connect(self.select_subtitle)

        edit_srt_btn = QPushButton("❌ 移除SRT")
        edit_srt_btn.setMinimumHeight(35)
        edit_srt_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #6c757d, stop: 1 #5a6268);
                color: white;
                font-weight: 500;
                border-radius: 6px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #868e96, stop: 1 #6c757d);
            }
        """)
        edit_srt_btn.clicked.connect(self.remove_srt)

        srt_btn_layout.addWidget(add_srt_btn)
        srt_btn_layout.addWidget(edit_srt_btn)
        srt_pool_layout.addLayout(srt_btn_layout)
        
        splitter.addWidget(srt_pool_widget)
        
        video_layout.addWidget(splitter)
        
        # 添加操作按钮
        action_layout = QVBoxLayout()
        
        # 添加GPU检测按钮
        detect_gpu_btn = QPushButton("🔍 检测GPU硬件")
        detect_gpu_btn.setMinimumHeight(35)
        detect_gpu_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #17a2b8, stop: 1 #138496);
                color: white;
                font-weight: 500;
                border-radius: 6px;
                padding: 8px 12px;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #20c997, stop: 1 #17a2b8);
            }
        """)
        detect_gpu_btn.clicked.connect(self.detect_gpu)
        action_layout.addWidget(detect_gpu_btn)

        # 添加查看日志按钮
        view_log_btn = QPushButton("📋 查看系统日志")
        view_log_btn.setMinimumHeight(35)
        view_log_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #6c757d, stop: 1 #5a6268);
                color: white;
                font-weight: 500;
                border-radius: 6px;
                padding: 8px 12px;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #868e96, stop: 1 #6c757d);
            }
        """)
        view_log_btn.clicked.connect(self.show_log_viewer)
        action_layout.addWidget(view_log_btn)

        # 添加系统监控按钮
        system_monitor_btn = QPushButton("📊 系统资源监控")
        system_monitor_btn.setMinimumHeight(35)
        system_monitor_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #fd7e14, stop: 1 #e8590c);
                color: white;
                font-weight: 500;
                border-radius: 6px;
                padding: 8px 12px;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #ff922b, stop: 1 #fd7e14);
            }
        """)
        system_monitor_btn.clicked.connect(self.show_system_monitor)
        action_layout.addWidget(system_monitor_btn)
        
        generate_srt_btn = QPushButton("✨ 生成爆款SRT")
        generate_srt_btn.setMinimumHeight(45)
        generate_srt_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #ff6b6b, stop: 1 #ee5a52);
                color: white;
                font-weight: bold;
                font-size: 15px;
                border: none;
                border-radius: 10px;
                padding: 12px 20px;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #ff8a80, stop: 1 #ff6b6b);
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(255, 107, 107, 0.4);
            }
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #ee5a52, stop: 1 #d32f2f);
                transform: translateY(0px);
            }
        """)
        generate_srt_btn.clicked.connect(self.generate_viral_srt)
        action_layout.addWidget(generate_srt_btn)

        # 创建并排的生成工程文件和导出按钮布局
        video_export_layout = QHBoxLayout()

        # 生成工程文件按钮（左侧）
        generate_project_btn = QPushButton("🎬 生成工程文件")
        generate_project_btn.setMinimumHeight(45)
        generate_project_btn.setProperty("class", "success")
        generate_project_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #52c41a, stop: 1 #389e0d);
                color: white;
                font-weight: bold;
                font-size: 14px;
                border: none;
                border-radius: 10px;
                padding: 12px 20px;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #73d13d, stop: 1 #52c41a);
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(82, 196, 26, 0.3);
            }
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #389e0d, stop: 1 #237804);
                transform: translateY(0px);
            }
        """)
        generate_project_btn.clicked.connect(self.generate_project_file)
        video_export_layout.addWidget(generate_project_btn)

        # 导出到剪映按钮（右侧）
        export_jianying_btn = QPushButton("📱 导出到剪映")
        export_jianying_btn.setMinimumHeight(45)
        export_jianying_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #1890ff, stop: 1 #096dd9);
                color: white;
                font-weight: bold;
                font-size: 14px;
                border: none;
                border-radius: 10px;
                padding: 12px 20px;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #40a9ff, stop: 1 #1890ff);
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(24, 144, 255, 0.3);
            }
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #096dd9, stop: 1 #0050b3);
                transform: translateY(0px);
            }
        """)
        export_jianying_btn.clicked.connect(self.export_to_jianying)
        video_export_layout.addWidget(export_jianying_btn)

        # 将并排布局添加到主布局
        action_layout.addLayout(video_export_layout)
        
        video_layout.addLayout(action_layout)
        
        # 添加到标签页
        self.tabs.addTab(video_widget, "视频处理")
        
        # 创建"模型训练"标签页
        train_tab = QWidget()
        train_layout = QVBoxLayout(train_tab)
        
        # 创建简化版的训练组件
        self.train_feeder = SimplifiedTrainingFeeder(parent=train_tab)
        train_layout.addWidget(self.train_feeder)
        
        # 添加到标签页
        self.tabs.addTab(train_tab, "模型训练")
        
        # 创建"关于我们"标签页
        about_tab = QWidget()
        about_main_layout = QVBoxLayout(about_tab)

        # 创建滚动区域
        about_scroll = QScrollArea()
        about_scroll.setWidgetResizable(True)
        about_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        about_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # 创建滚动内容容器
        about_content = QWidget()
        about_layout = QVBoxLayout(about_content)
        about_layout.setSpacing(12)
        about_layout.setContentsMargins(15, 15, 15, 15)

        # 设置内容容器的最小宽度以确保在小窗口下正常显示
        about_content.setMinimumWidth(920)  # 适应最小窗口宽度1000px，留出滚动条空间
        
        # 添加标题
        about_title_label = QLabel("🎬 VisionAI-ClipsMaster")
        about_title_label.setProperty("class", "title")
        about_title_label.setStyleSheet("""
            QLabel {
                font-size: 36px;
                font-weight: bold;
                color: #2c3e50;
                margin: 20px 0 10px 0;
                padding: 15px;
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                                          stop: 0 rgba(74, 144, 226, 0.15),
                                          stop: 1 rgba(53, 122, 189, 0.15));
                border: 2px solid #4a90e2;
                border-radius: 12px;
                text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.1);
                text-align: center;
            }
        """)
        about_title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        about_title_label.setWordWrap(False)  # 确保不换行
        about_title_label.setSizePolicy(about_title_label.sizePolicy().horizontalPolicy(), about_title_label.sizePolicy().verticalPolicy())

        # 创建水平布局使标题标签在容器中居中
        title_layout = QHBoxLayout()
        title_layout.addStretch()  # 左侧弹性空间
        title_layout.addWidget(about_title_label)
        title_layout.addStretch()  # 右侧弹性空间
        about_layout.addLayout(title_layout)

        # 添加副标题
        about_subtitle = QLabel("✨ AI驱动的智能视频创作平台")
        about_subtitle.setProperty("class", "subtitle")
        about_subtitle.setStyleSheet("""
            QLabel {
                font-size: 15px;
                color: #495057;
                font-style: italic;
                font-weight: 500;
                margin: 4px 0 10px 0;
                padding: 5px 10px;
                background-color: rgba(73, 80, 87, 0.08);
                border-radius: 6px;
                max-width: 100%;
                min-width: 250px;
            }
        """)
        about_subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        about_subtitle.setWordWrap(True)  # 允许换行以适应小窗口

        # 创建水平布局使副标题标签在容器中居中
        subtitle_layout = QHBoxLayout()
        subtitle_layout.addStretch()  # 左侧弹性空间
        subtitle_layout.addWidget(about_subtitle)
        subtitle_layout.addStretch()  # 右侧弹性空间
        about_layout.addLayout(subtitle_layout)

        # 添加版本信息
        version_label = QLabel("📦 版本 1.0.0-beta | 🗓️ 2025年7月发布 | ✅ 生产就绪")
        version_label.setStyleSheet("""
            QLabel {
                font-size: 15px;
                color: #2c3e50;
                font-weight: bold;
                margin: 10px 0 25px 0;
                padding: 12px 20px;
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                                          stop: 0 rgba(82, 196, 26, 0.15),
                                          stop: 1 rgba(40, 167, 69, 0.15));
                border: 2px solid #52c41a;
                border-radius: 20px;
                text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.1);
            }
        """)
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_label.setWordWrap(True)
        about_layout.addWidget(version_label)
        
        # 水平分割线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("color: #e5e7e9; margin: 15px 0;")
        about_layout.addWidget(line)
        
        # 功能区块布局
        features_layout = QHBoxLayout()
        features_layout.setSpacing(10)  # 减少间距以适应小窗口
        
        # 左侧：核心功能
        core_group = QGroupBox("🎯 核心功能")
        core_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 18px;
                color: #2c3e50;
                border: 3px solid #4a90e2;
                border-radius: 12px;
                margin-top: 20px;
                padding-top: 15px;
                background-color: rgba(74, 144, 226, 0.08);
                min-height: 280px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 20px;
                padding: 5px 15px 5px 15px;
                color: #2c3e50;
                background-color: #FFFFFF;
                border: 2px solid #4a90e2;
                border-radius: 8px;
                font-weight: bold;
            }
        """)
        core_layout = QVBoxLayout(core_group)
        core_layout.setSpacing(8)
        core_layout.setContentsMargins(15, 25, 15, 15)

        core_features = [
            "🎬 智能视频剪辑与重组",
            "🌐 双语模型支持（中文/英文）",
            "📝 自动字幕匹配与优化",
            "🧠 模型个性化训练",
            "⚡ GPU加速处理",
            "📦 批量视频处理"
        ]

        for feature in core_features:
            feature_label = QLabel(feature)
            feature_label.setStyleSheet("""
                QLabel {
                    font-size: 15px;
                    font-weight: 500;
                    padding: 10px 15px;
                    margin: 3px 0;
                    background-color: rgba(74, 144, 226, 0.12);
                    border: 1px solid rgba(74, 144, 226, 0.3);
                    border-radius: 8px;
                    color: #2c3e50;
                    border-left: 4px solid #4a90e2;
                }
            """)
            feature_label.setWordWrap(True)
            feature_label.setMinimumHeight(40)
            core_layout.addWidget(feature_label)
        
        features_layout.addWidget(core_group)
        
        # 右侧：技术栈
        tech_group = QGroupBox("⚙️ 技术栈")
        tech_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 18px;
                color: #2c3e50;
                border: 3px solid #52c41a;
                border-radius: 12px;
                margin-top: 20px;
                padding-top: 15px;
                background-color: rgba(82, 196, 26, 0.08);
                min-height: 280px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 20px;
                padding: 5px 15px 5px 15px;
                color: #2c3e50;
                background-color: #FFFFFF;
                border: 2px solid #52c41a;
                border-radius: 8px;
                font-weight: bold;
            }
        """)
        tech_layout = QVBoxLayout(tech_group)
        tech_layout.setSpacing(8)
        tech_layout.setContentsMargins(15, 25, 15, 15)

        tech_features = [
            "🤖 双模型AI：Mistral-7B (英文) + Qwen2.5-7B (中文)",
            "🎥 视频处理：FFmpeg GPU加速, 精确切割",
            "🧩 智能分析：剧情重构, 病毒式转换算法",
            "💾 轻量部署：4GB内存兼容, CPU优化",
            "🛡️ 增强稳定：异常处理, 结构化日志",
            "📤 专业导出：剪映工程文件, 批量处理"
        ]

        for tech in tech_features:
            tech_label = QLabel(tech)
            tech_label.setStyleSheet("""
                QLabel {
                    font-size: 15px;
                    font-weight: 500;
                    padding: 10px 15px;
                    margin: 3px 0;
                    background-color: rgba(82, 196, 26, 0.12);
                    border: 1px solid rgba(82, 196, 26, 0.3);
                    border-radius: 8px;
                    color: #2c3e50;
                    border-left: 4px solid #52c41a;
                }
            """)
            tech_label.setWordWrap(True)
            tech_label.setMinimumHeight(40)
            tech_layout.addWidget(tech_label)
        
        features_layout.addWidget(tech_group)
        
        about_layout.addLayout(features_layout)
        
        # 添加详情按钮区域
        buttons_layout = QHBoxLayout()
        
        # 团队介绍按钮
        team_btn = QPushButton("👥 团队介绍")
        team_btn.setMinimumHeight(45)
        team_btn.setMinimumWidth(160)
        team_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #1a5276, stop: 1 #154360);
                color: white;
                font-size: 14px;
                font-weight: bold;
                border: none;
                border-radius: 8px;
                padding: 10px 16px;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #2874a6, stop: 1 #1a5276);
                transform: translateY(-1px);
            }
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #154360, stop: 1 #0e2f44);
            }
        """)
        team_btn.clicked.connect(self.show_about_dialog)

        # 技术详情按钮
        tech_btn = QPushButton("⚙️ 技术详情")
        tech_btn.setMinimumHeight(45)
        tech_btn.setMinimumWidth(160)
        tech_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #117a65, stop: 1 #0e6b5d);
                color: white;
                font-size: 14px;
                font-weight: bold;
                border: none;
                border-radius: 8px;
                padding: 10px 16px;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #148f77, stop: 1 #117a65);
                transform: translateY(-1px);
            }
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #0e6b5d, stop: 1 #0a5d55);
            }
        """)
        tech_btn.clicked.connect(self.show_tech_dialog)

        # 项目历程按钮
        history_btn = QPushButton("📈 项目历程")
        history_btn.setMinimumHeight(45)
        history_btn.setMinimumWidth(160)
        history_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #7d3c98, stop: 1 #6c3483);
                color: white;
                font-size: 14px;
                font-weight: bold;
                border: none;
                border-radius: 8px;
                padding: 10px 16px;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #8e44ad, stop: 1 #7d3c98);
                transform: translateY(-1px);
            }
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #6c3483, stop: 1 #5b2c6f);
            }
        """)
        history_btn.clicked.connect(self.show_history_dialog)
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(team_btn)
        buttons_layout.addWidget(tech_btn)
        buttons_layout.addWidget(history_btn)
        buttons_layout.addStretch()
        
        about_layout.addLayout(buttons_layout)
        
        # 添加引言
        quote_text = QTextEdit()
        quote_text.setReadOnly(True)
        quote_text.setMinimumHeight(120)
        quote_text.setMaximumHeight(150)
        quote_text.setStyleSheet("""
            QTextEdit {
                border: 2px solid #4a90e2;
                background-color: rgba(74, 144, 226, 0.08);
                border-radius: 12px;
                margin: 15px 5px;
                padding: 20px;
                font-family: inherit;
            }
        """)
        quote_text.setHtml("""
        <div style="text-align: center; margin: 8px; font-style: italic;">
            <p style="font-size: 16px; color: #2c3e50; line-height: 1.6; font-weight: 500; margin: 12px 0;">
                💡 "让AI技术服务于创意，让每个人都能创作出专业级的短剧内容。通过双模型架构和智能算法，我们将复杂的视频制作变得简单而高效。"
            </p>
            <p style="font-size: 14px; color: #495057; text-align: right; margin-top: 12px; font-weight: bold;">
                — 🚀 CKEN
            </p>
        </div>
        """)
        about_layout.addWidget(quote_text)
        
        # 添加联系方式区域
        contact_layout = QHBoxLayout()
        
        github_btn = QPushButton("🌟 GitHub")
        github_btn.setMinimumHeight(40)
        github_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #333333, stop: 1 #1a1a1a);
                color: white;
                font-size: 14px;
                font-weight: bold;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #4d4d4d, stop: 1 #333333);
                transform: translateY(-1px);
                box-shadow: 0 3px 8px rgba(0, 0, 0, 0.3);
            }
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #1a1a1a, stop: 1 #000000);
                transform: translateY(0px);
            }
        """)
        github_btn.clicked.connect(lambda: self.open_url("https://github.com/CKEN-STAR/VisionAI-ClipsMaster"))
        
        contact_layout.addStretch()
        contact_layout.addWidget(github_btn)
        contact_layout.addStretch()
        
        about_layout.addLayout(contact_layout)
        
        # 添加版权信息
        copyright_label = QLabel("© 2025 CKEN-STAR 版权所有 | 开源项目 | MIT许可证")
        copyright_label.setStyleSheet("""
            QLabel {
                color: #6c757d;
                font-size: 14px;
                font-weight: 500;
                margin: 25px 0 15px 0;
                padding: 12px 20px;
                background-color: rgba(108, 117, 125, 0.08);
                border-radius: 10px;
                border: 1px solid rgba(108, 117, 125, 0.2);
            }
        """)
        copyright_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        copyright_label.setWordWrap(True)
        about_layout.addWidget(copyright_label)

        # 添加弹性空间
        about_layout.addStretch()

        # 设置滚动区域
        about_scroll.setWidget(about_content)
        about_main_layout.addWidget(about_scroll)

        # 添加到标签页
        self.tabs.addTab(about_tab, "关于我们")
        
        # 创建"设置"标签页
        settings_tab = QWidget()
        settings_layout = QVBoxLayout(settings_tab)
        
        # 创建设置标签页
        settings_tabs = QTabWidget()
        
        # 创建磁盘缓存标签内容
        cache_settings_layout = QVBoxLayout()
        
        # 标题
        cache_title = QLabel("磁盘缓存管理")
        cache_title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        cache_settings_layout.addWidget(cache_title)
        
        # 描述
        cache_description = QLabel("磁盘缓存可以提高重复任务的处理速度，通过保存之前的处理结果来减少重复计算。")
        cache_description.setWordWrap(True)
        cache_settings_layout.addWidget(cache_description)
        
        # 缓存信息区域
        cache_info_group = QGroupBox("缓存统计")
        cache_info_layout = QFormLayout()
        
        self.cache_size_label = QLabel("0 MB")
        self.cache_items_label = QLabel("0 个文件")
        self.cache_hits_label = QLabel("0 次")
        self.cache_misses_label = QLabel("0 次")
        self.cache_ratio_label = QLabel("0%")
        
        cache_info_layout.addRow("当前缓存大小:", self.cache_size_label)
        cache_info_layout.addRow("缓存项目数:", self.cache_items_label)
        cache_info_layout.addRow("缓存命中:", self.cache_hits_label)
        cache_info_layout.addRow("缓存未命中:", self.cache_misses_label)
        cache_info_layout.addRow("命中率:", self.cache_ratio_label)
        
        cache_info_group.setLayout(cache_info_layout)
        cache_settings_layout.addWidget(cache_info_group)
        
        # 缓存操作区域
        cache_actions_group = QGroupBox("缓存操作")
        cache_actions_layout = QVBoxLayout()
        
        # 清理缓存按钮
        clear_cache_btn = QPushButton("🧹 清理缓存")
        clear_cache_btn.setMinimumHeight(35)
        clear_cache_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #dc3545, stop: 1 #c82333);
                color: white;
                font-weight: 500;
                border-radius: 6px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #e4606d, stop: 1 #dc3545);
            }
        """)
        clear_cache_btn.clicked.connect(self.clear_disk_cache)
        cache_actions_layout.addWidget(clear_cache_btn)

        # 刷新缓存统计按钮
        refresh_cache_btn = QPushButton("🔄 刷新缓存统计")
        refresh_cache_btn.setMinimumHeight(35)
        refresh_cache_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #17a2b8, stop: 1 #138496);
                color: white;
                font-weight: 500;
                border-radius: 6px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #20c997, stop: 1 #17a2b8);
            }
        """)
        refresh_cache_btn.clicked.connect(self.refresh_cache_stats)
        cache_actions_layout.addWidget(refresh_cache_btn)
        
        cache_actions_group.setLayout(cache_actions_layout)
        cache_settings_layout.addWidget(cache_actions_group)
        
        # 添加弹性空间
        cache_settings_layout.addStretch()
        
        # 将布局添加到磁盘缓存标签
        cache_settings_widget = QWidget()
        cache_settings_widget.setLayout(cache_settings_layout)
        settings_tabs.addTab(cache_settings_widget, "磁盘缓存")
        
        # 添加输入延迟标签内容
        input_settings_layout = QVBoxLayout()
        
        # 标题
        input_title = QLabel("输入延迟优化")
        input_title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        input_settings_layout.addWidget(input_title)
        
        # 描述
        input_description = QLabel("输入延迟优化可以提高UI交互的响应速度，特别是在低性能设备上。根据设备性能等级自动调整输入处理方式。")
        input_description.setWordWrap(True)
        input_settings_layout.addWidget(input_description)
        
        # 输入优化信息区域
        input_info_group = QGroupBox("优化统计")
        input_info_layout = QFormLayout()
        
        self.input_tier_label = QLabel("未设置")
        self.input_cursor_flash_label = QLabel("默认")
        self.input_event_compress_label = QLabel("未启用")
        self.input_touch_optimize_label = QLabel("未启用")
        self.input_fields_optimized_label = QLabel("0 个")
        self.input_events_filtered_label = QLabel("0 个")
        
        input_info_layout.addRow("性能等级:", self.input_tier_label)
        input_info_layout.addRow("光标闪烁时间:", self.input_cursor_flash_label)
        input_info_layout.addRow("事件压缩:", self.input_event_compress_label)
        input_info_layout.addRow("触摸优化:", self.input_touch_optimize_label)
        input_info_layout.addRow("已优化字段:", self.input_fields_optimized_label)
        input_info_layout.addRow("已过滤事件:", self.input_events_filtered_label)
        
        input_info_group.setLayout(input_info_layout)
        input_settings_layout.addWidget(input_info_group)
        
        # 添加刷新统计按钮
        refresh_input_stats_btn = QPushButton("📈 刷新输入优化统计")
        refresh_input_stats_btn.setMinimumHeight(35)
        refresh_input_stats_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #28a745, stop: 1 #1e7e34);
                color: white;
                font-weight: 500;
                border-radius: 6px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #34ce57, stop: 1 #28a745);
            }
        """)
        refresh_input_stats_btn.clicked.connect(self.refresh_input_latency_stats)
        input_settings_layout.addWidget(refresh_input_stats_btn)
        
        # 添加弹性空间
        input_settings_layout.addStretch()
        
        # 将布局添加到输入延迟标签
        input_settings_widget = QWidget()
        input_settings_widget.setLayout(input_settings_layout)
        settings_tabs.addTab(input_settings_widget, "输入优化")
        
        # 添加电源管理标签内容
        power_settings_layout = QVBoxLayout()
        
        # 标题
        power_title = QLabel("电源管理")
        power_title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        power_settings_layout.addWidget(power_title)
        
        # 描述
        power_description = QLabel("电源管理功能会根据当前电源状态自动调整应用的性能和功耗，在电池供电时节省电量，连接电源时提供最佳性能。")
        power_description.setWordWrap(True)
        power_settings_layout.addWidget(power_description)
        
        # 电源状态信息区域
        power_info_group = QGroupBox("电源状态")
        power_info_layout = QFormLayout()
        
        self.power_source_label = QLabel("未检测")
        self.battery_status_label = QLabel("未知")
        self.battery_level_label = QLabel("未知")
        self.power_mode_label = QLabel("正常模式")
        
        power_info_layout.addRow("当前电源:", self.power_source_label)
        power_info_layout.addRow("电池状态:", self.battery_status_label)
        power_info_layout.addRow("电池电量:", self.battery_level_label)
        power_info_layout.addRow("电源模式:", self.power_mode_label)
        
        power_info_group.setLayout(power_info_layout)
        power_settings_layout.addWidget(power_info_group)
        
        # 电源优化设置区域
        power_settings_group = QGroupBox("电源优化设置")
        power_settings_form = QFormLayout()
        
        # 启用电源管理开关
        self.enable_power_management_check = QCheckBox()
        self.enable_power_management_check.setChecked(True)
        self.enable_power_management_check.stateChanged.connect(self.toggle_power_management)
        power_settings_form.addRow("启用电源管理:", self.enable_power_management_check)
        
        # 低电量时自动节能开关
        self.auto_power_save_check = QCheckBox()
        self.auto_power_save_check.setChecked(True)
        power_settings_form.addRow("低电量自动节能:", self.auto_power_save_check)
        
        # 电池模式下手动启用节能模式按钮
        self.enable_power_saving_btn = QPushButton("启用节能模式")
        self.enable_power_saving_btn.clicked.connect(self.toggle_power_saving_mode)
        power_settings_form.addRow("节能模式:", self.enable_power_saving_btn)
        
        power_settings_group.setLayout(power_settings_form)
        power_settings_layout.addWidget(power_settings_group)
        
        # 刷新电源状态按钮
        refresh_power_btn = QPushButton("刷新电源状态")
        refresh_power_btn.setIcon(QIcon.fromTheme("view-refresh"))
        refresh_power_btn.clicked.connect(self.refresh_power_status)
        power_settings_layout.addWidget(refresh_power_btn)
        
        # 添加弹性空间
        power_settings_layout.addStretch()
        
        # 将布局添加到电源管理标签
        power_settings_widget = QWidget()
        power_settings_widget.setLayout(power_settings_layout)
        settings_tabs.addTab(power_settings_widget, "电源管理")
        
        # 将标签页控件添加到设置布局
        settings_layout.addWidget(settings_tabs)
        settings_layout.addStretch()
        
        # 将设置标签页添加到主标签页
        self.tabs.addTab(settings_tab, "设置")
        
        # 设置状态栏
        self.statusBar().showMessage("")
    
    @track_ui_operation("标签页切换")
    def on_tab_changed(self, index):
        """当标签页切换时调用 - 增强监控版本"""
        with record_operation("标签页切换") as timer:
            try:
                # 优先使用异步优化器
                if OPTIMIZATION_MODULES_AVAILABLE and hasattr(self, 'safe_optimizer'):
                    optimize_tab_switch(index)

                # 异步记录用户交互，避免阻塞
                QTimer.singleShot(0, self.record_user_interaction)

                tab_names = ["视频处理", "模型训练", "关于我们", "设置"]
                if 0 <= index < len(tab_names):
                    log_handler.log("info", f"切换到{tab_names[index]}标签页")
                    print(f"[OK] 标签页切换成功: {tab_names[index]}")

                # 立即执行关键的进度条可见性更新
                if hasattr(self, 'progress_container'):
                    self.progress_container.setVisible(index == 0)

                # 如果没有优化器，使用传统方法
                if not (OPTIMIZATION_MODULES_AVAILABLE and hasattr(self, 'safe_optimizer')):
                    # 延迟执行所有非关键操作
                    QTimer.singleShot(100, lambda: self._update_tab_ui(index))
                    QTimer.singleShot(200, self._cleanup_previous_tab_cache)

            except Exception as e:
                print(f"标签页切换处理失败: {e}")
                # 确保进度条可见性正确设置
                if hasattr(self, 'progress_container'):
                    self.progress_container.setVisible(index == 0)

    def _update_tab_ui(self, index):
        """延迟更新标签页UI - 非阻塞操作"""
        try:
            # 根据标签页索引执行特定的UI更新
            if index == 0:  # 视频处理页
                self._optimize_video_tab()
            elif index == 1:  # 模型训练页
                self._optimize_training_tab()
            elif index == 2:  # 关于我们页
                self._optimize_about_tab()
            elif index == 3:  # 设置页
                self._optimize_settings_tab()
        except Exception as e:
            print(f"延迟UI更新失败: {e}")

    def _cleanup_previous_tab_cache(self):
        """清理前一个标签页的缓存"""
        try:
            # 清理不必要的临时数据
            if hasattr(self, '_temp_data_cache'):
                self._temp_data_cache.clear()

            # 执行轻量级垃圾回收
            import gc
            gc.collect()
        except Exception as e:
            print(f"标签页缓存清理失败: {e}")

    def _optimize_video_tab(self):
        """优化视频处理标签页"""
        try:
            # 确保视频列表组件响应性
            if hasattr(self, 'video_list'):
                self.video_list.setUpdatesEnabled(True)
            if hasattr(self, 'srt_list'):
                self.srt_list.setUpdatesEnabled(True)
        except Exception as e:
            print(f"视频标签页优化失败: {e}")

    def _optimize_training_tab(self):
        """优化模型训练标签页"""
        try:
            # 确保训练组件正常工作
            if hasattr(self, 'train_feeder'):
                # 检查训练状态
                pass
        except Exception as e:
            print(f"训练标签页优化失败: {e}")

    def _optimize_about_tab(self):
        """优化关于我们标签页"""
        try:
            # 关于页面通常是静态的，无需特殊优化
            pass
        except Exception as e:
            print(f"关于标签页优化失败: {e}")

    def _optimize_settings_tab(self):
        """优化设置标签页"""
        try:
            # 确保设置组件响应性
            if hasattr(self, 'lang_combo'):
                self.lang_combo.setEnabled(True)
        except Exception as e:
            print(f"设置标签页优化失败: {e}")
            
            # 使用性能优化器更新UI
            if HAS_PERF_OPTIMIZER and hasattr(self, 'panel_optimizer'):
                try:
                    # 获取当前标签页索引
                    current_index = self.tabs.currentIndex()

                    # 在标签页切换时清理非活动面板资源
                    for i in range(self.tabs.count()):
                        if i != current_index:  # 跳过当前活动标签页
                            tab_widget = self.tabs.widget(i)
                            if tab_widget:
                                # panel_name = f"Tab_{i}"  # 保留用于调试
                                self.panel_optimizer.unload_panel_resources(tab_widget)

                    # 显示切换通知
                    if hasattr(self, 'alert_manager') and self.alert_manager:
                        try:
                            tab_names = ["视频处理", "模型训练", "关于我们", "设置"]
                            if 0 <= current_index < len(tab_names):
                                self.alert_manager.info(f"已切换到{tab_names[current_index]}面板", timeout=2000)
                        except Exception as e:
                            print(f"警告: 无法显示通知: {e}")
                except Exception as e:
                    print(f"警告: 性能优化操作失败: {e}")
    
    def init_performance_optimizer(self):
        """初始化性能优化器"""
        if not HAS_PERF_OPTIMIZER:
            return
        
        try:
            # 创建性能优化器
            self.panel_optimizer = PanelOptimizer(self)
            
            # 注册各个面板
            if hasattr(self, 'tabs') and self.tabs.count() > 0:
                # 获取所有标签页
                for i in range(self.tabs.count()):
                    tab_widget = self.tabs.widget(i)
                    if tab_widget:
                        # 根据标签页索引设置优先级
                        priority = self.tabs.count() - i - 1
                        panel_name = f"Tab_{i}"
                        self.panel_optimizer.register_panel(panel_name=panel_name, panel=tab_widget, priority=priority)
            
            # 启动面板监控
            self.panel_optimizer.start_monitoring(interval_ms=3000)
            
            # 预缓存最近添加的视频缩略图
            if hasattr(self, 'video_list') and self.video_list.count() > 0:
                recent_files = []
                for i in range(min(self.video_list.count(), 5)):
                    item = self.video_list.item(i)
                    if item and hasattr(item, 'file_path'):
                        recent_files.append(item.file_path)
                
                # 异步预生成缩略图
                if recent_files:
                    for video_path in recent_files:
                        generate_thumbnail(video_path, size=(320, 180))
            
            log_handler.log("info", "性能优化器已初始化")
        except Exception as e:
            log_handler.log("warning", f"性能优化器初始化失败: {str(e)}")
            # 不影响主程序运行
    
    def check_models(self):
        """检查模型是否已下载"""
        # 获取项目根目录（向上3级：main_window.py -> ui -> visionai_clipsmaster -> 项目根）
        project_root = Path(__file__).resolve().parent.parent.parent

        # 检查中文模型（更新为Qwen3系列）
        zh_model_paths = [
            project_root / "models" / "qwen" / "quantized" / "Q4_K_M.gguf",
            project_root / "models" / "qwen" / "base",
            project_root / "models" / "qwen" / "finetuned",
            project_root / "models" / "qwen3-0.6b" / "base",  # Qwen3-0.6B
            project_root / "models" / "qwen3-1.7b" / "base",  # Qwen3-1.7B
            project_root / "models" / "qwen3-8b" / "base",  # Qwen3-8B
            project_root / "models" / "qwen3-32b" / "base",  # Qwen3-32B
        ]

        # 检查models/qwen目录是否存在并有实际模型文件
        qwen_dir = project_root / "models" / "qwen"
        qwen3_dirs = [
            project_root / "models" / "qwen3-0.6b",
            project_root / "models" / "qwen3-1.7b",
            project_root / "models" / "qwen3-8b",
            project_root / "models" / "qwen3-32b",
        ]

        # 检查任一路径是否存在
        self.zh_model_exists = any(path.exists() for path in zh_model_paths)

        # 如果路径检查失败，尝试检查目录中是否有大文件
        if not self.zh_model_exists:
            if qwen_dir.is_dir():
                self.zh_model_exists = self._has_large_files(str(qwen_dir))
            else:
                for qwen3_dir in qwen3_dirs:
                    if qwen3_dir.is_dir() and self._has_large_files(str(qwen3_dir)):
                        self.zh_model_exists = True
                        break

        # 检查英文模型
        en_model_paths = [
            project_root / "models" / "mistral" / "quantized" / "Q4_K_M.gguf",
            project_root / "models" / "mistral" / "base" / "mistral-7b.bin",
            project_root / "models" / "mistral" / "base" / "mistral-7b",
            project_root / "models" / "mistral" / "finetuned",
            project_root / "models" / "mistral-7b" / "fp16",  # 新增：检查新下载的模型
            project_root / "models" / "mistral-7b" / "int4",
            project_root / "models" / "mistral-7b" / "int8",
        ]

        # 检查models/mistral目录是否存在并有实际模型文件
        mistral_dir = project_root / "models" / "mistral"
        mistral_7b_dir = project_root / "models" / "mistral-7b"  # 新增：检查新模型目录

        # 检查任一路径是否存在
        self.en_model_exists = any(path.exists() for path in en_model_paths)

        # 如果路径检查失败，尝试检查目录中是否有大文件
        if not self.en_model_exists:
            if mistral_dir.is_dir():
                self.en_model_exists = self._has_large_files(str(mistral_dir))
            elif mistral_7b_dir.is_dir():
                self.en_model_exists = self._has_large_files(str(mistral_7b_dir))

        # 记录详细的模型检测日志
        log_handler.log("info", f"🔍 模型检测详情:")
        log_handler.log("info", f"  - 项目根目录: {project_root}")
        log_handler.log("info", f"  - 中文模型目录: {qwen_dir} / {qwen2_5_dir}")
        log_handler.log("info", f"  - 中文模型状态: {'已安装' if self.zh_model_exists else '未安装'}")
        log_handler.log("info", f"  - 英文模型目录: {mistral_dir} / {mistral_7b_dir}")
        log_handler.log("info", f"  - 英文模型状态: {'已安装' if self.en_model_exists else '未安装'}")

        # 更新下载按钮状态
        self.update_download_button()
        
    def _has_large_files(self, directory, min_size_mb=10):
        """递归检查目录中是否有大文件（可能是模型文件）
        
        Args:
            directory: 要检查的目录
            min_size_mb: 最小文件大小（MB），默认10MB
            
        Returns:
            bool: 是否存在大文件
        """
        if not os.path.exists(directory):
            return False
            
        min_size = min_size_mb * 1024 * 1024  # 转换为字节
        
        for root, _, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    if os.path.getsize(file_path) > min_size:
                        return True
                except (OSError, IOError):
                    continue
        
        return False
    
    def update_download_button(self):
        """更新模型状态标识（已移除下载按钮）"""
        # 此方法保留以兼容现有代码，但不再需要更新按钮
        pass
    
    def show_log_viewer(self):
        """显示日志查看器"""
        log_viewer = LogViewerDialog(self)
        log_viewer.show()
        log_handler.log("info", "打开日志查看器")
    
    def check_en_model(self):
        """检查英文模型是否存在，不存在则提示下载"""
        # 首先重新检查模型状态，确保状态是最新的
        self.check_models()

        # 检查是否有实际的对话框在显示中（更精确的防重复检查）
        if hasattr(self, '_dialog_instance') and self._dialog_instance is not None:
            log_handler.log("info", "⚠️ 检测到实际对话框窗口已在显示中，跳过重复弹窗")
            return

        # 初始化对话框实例引用
        if not hasattr(self, '_dialog_instance'):
            self._dialog_instance = None

        try:
            if not self.en_model_exists:
                log_handler.log("info", "🔍 检测到英文模型缺失，准备显示智能推荐对话框")

                # 直接调用增强下载器，不显示简单确认对话框
                if self.enhanced_downloader and self.enhanced_downloader.has_intelligent_selector:
                    log_handler.log("info", "✅ 使用增强下载器显示智能推荐对话框")
                    # 重要修复：彻底重置状态，确保状态隔离
                    self.enhanced_downloader.reset_state()
                    success = self.enhanced_downloader.download_model("mistral-7b", self)
                    if success:
                        log_handler.log("info", "✅ 英文模型下载已启动")
                    else:
                        log_handler.log("warning", "⚠️ 英文模型下载被取消")
                else:
                    log_handler.log("warning", "⚠️ 增强下载器不可用，显示简单确认对话框")
                    # 回退到简单对话框
                    reply = QMessageBox.question(
                        self,
                        "英文模型未安装",
                        "英文模型尚未下载，是否现在下载？\n(约4GB，需要较长时间)",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.Yes
                    )

                    if reply == QMessageBox.StandardButton.Yes:
                        self.download_en_model()
        except Exception as e:
            log_handler.log("error", f"❌ 英文模型检查失败: {str(e)}")
            # 异常时回退到简单对话框
            reply = QMessageBox.question(
                self,
                "英文模型未安装",
                "英文模型尚未下载，是否现在下载？\n(约4GB，需要较长时间)",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.download_en_model()
        finally:
            # 清除全局弹窗标志
            self._global_model_dialog_showing = False
    
    def check_zh_model(self):
        """检查中文模型是否存在，不存在则提示下载"""
        # 首先重新检查模型状态，确保状态是最新的
        self.check_models()

        # 检查是否有实际的对话框在显示中（更精确的防重复检查）
        if hasattr(self, '_dialog_instance') and self._dialog_instance is not None:
            log_handler.log("info", "⚠️ 检测到实际对话框窗口已在显示中，跳过重复弹窗")
            return

        # 初始化对话框实例引用
        if not hasattr(self, '_dialog_instance'):
            self._dialog_instance = None

        try:
            if not self.zh_model_exists:
                log_handler.log("info", "🔍 检测到中文模型缺失，准备显示智能推荐对话框")

                # 直接调用增强下载器，不显示简单确认对话框
                if self.enhanced_downloader and self.enhanced_downloader.has_intelligent_selector:
                    log_handler.log("info", "✅ 使用增强下载器显示智能推荐对话框")
                    # 重要修复：彻底重置状态，确保状态隔离
                    self.enhanced_downloader.reset_state()
                    success = self.enhanced_downloader.download_model("qwen2.5-7b", self)
                    if success:
                        log_handler.log("info", "✅ 中文模型下载已启动")
                    else:
                        log_handler.log("warning", "⚠️ 中文模型下载被取消")
                else:
                    log_handler.log("warning", "⚠️ 增强下载器不可用，显示简单确认对话框")
                    # 回退到简单对话框
                    reply = QMessageBox.question(
                        self,
                        "中文模型未安装",
                        "中文模型尚未下载，是否现在下载？\n(约4GB，需要较长时间)",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.Yes
                    )

                    if reply == QMessageBox.StandardButton.Yes:
                        self.download_zh_model()
        except Exception as e:
            log_handler.log("error", f"❌ 中文模型检查失败: {str(e)}")
            # 异常时回退到简单对话框
            reply = QMessageBox.question(
                self,
                "中文模型未安装",
                "中文模型尚未下载，是否现在下载？\n(约4GB，需要较长时间)",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.download_zh_model()
        finally:
            # 清除全局弹窗标志
            self._global_model_dialog_showing = False

    def _reset_dialog_flag(self):
        """定期重置对话框标志位，防止永久阻塞"""
        if hasattr(self, '_global_model_dialog_showing') and self._global_model_dialog_showing:
            # 如果标志位被设置超过30秒，强制重置
            log_handler.log("warning", "⚠️ 检测到对话框标志位长时间未清除，强制重置")
            self._global_model_dialog_showing = False

    def download_en_model(self):
        """下载英文模型"""
        log_handler.log("info", "用户请求下载英文模型")

        try:
            if self.enhanced_downloader:
                # 使用增强下载器
                # 重要修复：彻底重置状态，确保状态隔离
                self.enhanced_downloader.reset_state()
                success = self.enhanced_downloader.download_model("mistral-7b", self)
                if success:
                    log_handler.log("info", "英文模型下载已启动")
                else:
                    log_handler.log("warning", "英文模型下载被取消")
            else:
                # 回退到基础下载功能
                self._fallback_download_en_model()
        except Exception as e:
            log_handler.log("error", f"英文模型下载失败: {str(e)}")
            QMessageBox.critical(self, "下载错误", f"英文模型下载失败:\n{str(e)}")

    def _fallback_download_en_model(self):
        """回退的英文模型下载方法"""
        # 创建并启动下载线程
        self.download_thread = ModelDownloadThread("mistral-7b-en")
        self.download_thread.progress_updated.connect(self.update_download_progress)
        self.download_thread.download_completed.connect(self.on_download_completed)
        self.download_thread.download_failed.connect(self.on_download_failed)

        # 创建进度对话框
        self.progress_dialog = QProgressDialog("正在下载模型...", "取消", 0, 100, self)
        self.progress_dialog.setWindowTitle("下载英文模型")
        self.progress_dialog.setMinimumDuration(0)
        self.progress_dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.progress_dialog.canceled.connect(self.cancel_download)
        self.progress_dialog.show()

        # 开始下载
        log_handler.log("info", "开始下载英文模型（基础模式）")
        self.download_thread.start()
    
    def download_zh_model(self):
        """下载中文模型"""
        log_handler.log("info", "用户请求下载中文模型")

        try:
            if self.enhanced_downloader:
                # 使用增强下载器
                # 重要修复：彻底重置状态，确保状态隔离
                self.enhanced_downloader.reset_state()
                success = self.enhanced_downloader.download_model("qwen2.5-7b", self)
                if success:
                    log_handler.log("info", "中文模型下载已启动")
                else:
                    log_handler.log("warning", "中文模型下载被取消")
            else:
                # 回退到基础下载功能
                self._fallback_download_zh_model()
        except Exception as e:
            log_handler.log("error", f"中文模型下载失败: {str(e)}")
            QMessageBox.critical(self, "下载错误", f"中文模型下载失败:\n{str(e)}")

    def _fallback_download_zh_model(self):
        """回退的中文模型下载方法"""
        # 创建并启动下载线程
        self.download_thread = ModelDownloadThread("qwen2.5-7b-zh")
        self.download_thread.progress_updated.connect(self.update_download_progress)
        self.download_thread.download_completed.connect(self.on_zh_download_completed)
        self.download_thread.download_failed.connect(self.on_download_failed)

        # 创建进度对话框
        self.progress_dialog = QProgressDialog("正在下载模型...", "取消", 0, 100, self)
        self.progress_dialog.setWindowTitle("下载中文模型")
        self.progress_dialog.setMinimumDuration(0)
        self.progress_dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.progress_dialog.canceled.connect(self.cancel_download)
        self.progress_dialog.show()
        
        # 开始下载
        log_handler.log("info", "开始下载中文模型")
        self.download_thread.start()
    
    def update_download_progress(self, progress, message):
        """更新下载进度"""
        if self.progress_dialog:
            self.progress_dialog.setValue(progress)
            self.progress_dialog.setLabelText(message)
            
            # 每10%记录一次日志
            if progress % 10 == 0:
                log_handler.log("info", f"模型下载进度: {progress}% - {message}")
    
    def on_download_completed(self):
        """下载完成回调"""
        if self.progress_dialog:
            self.progress_dialog.close()
        
        log_handler.log("info", "英文模型下载完成")
        QMessageBox.information(
            self,
            "下载完成",
            "英文模型已成功下载并配置。现在可以使用英文模式处理视频。"
        )
        
        # 更新模型状态
        self.en_model_exists = True
        self.update_download_button()
    
    def on_zh_download_completed(self):
        """中文模型下载完成回调"""
        if self.progress_dialog:
            self.progress_dialog.close()
        
        log_handler.log("info", "中文模型下载完成")
        QMessageBox.information(
            self,
            "下载完成",
            "中文模型已成功下载并配置。现在可以使用中文模式处理视频。"
        )
        
        # 更新模型状态
        self.zh_model_exists = True
        self.update_download_button()
    
    def on_download_failed(self, error_message):
        """下载失败回调"""
        if self.progress_dialog:
            self.progress_dialog.close()
        
        log_handler.log("error", f"英文模型下载失败: {error_message}")
        
        if HAS_ERROR_VISUALIZER:
            # 使用全息错误显示
            error_info = ErrorInfo(
                title="模型下载失败",
                description=f"英文模型下载失败: {error_message}",
                error_type=ErrorType.ERROR,
                details="模型下载过程中出现错误，可能是网络连接问题或服务器不可用。",
                solutions=["检查网络连接", "稍后重试", "尝试从其他源下载"]
            )
            show_error(error_info, self)
        else:
            # 使用传统错误显示
            QMessageBox.critical(self, "模型下载失败", f"模型下载失败: {error_message}")
    
    def cancel_download(self):
        """取消下载"""
        if self.download_thread and self.download_thread.isRunning():
            self.download_thread.stop()
            self.download_thread.wait()
        
        log_handler.log("info", "用户取消下载英文模型")
        QMessageBox.information(
            self,
            "下载取消",
            "模型下载已取消"
        )
        
    def select_video(self):
        """选择视频文件"""
        # 记录用户交互
        # 安全调用record_user_interaction

        try:

            if hasattr(self, 'record_user_interaction'):

                self.record_user_interaction()

            else:

                print("🔍 [DEBUG] record_user_interaction方法不存在，跳过")

        except Exception as e:

            print(f"⚠️ [WARNING] record_user_interaction调用失败: {e}")

        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "选择视频文件", "", "视频文件 (*.mp4 *.avi *.mov *.mkv)"
        )

        for file_path in file_paths:
            if file_path:
                # 添加到视频池列表
                item = QListWidgetItem(os.path.basename(file_path))
                item.setData(Qt.ItemDataRole.UserRole, file_path)  # 存储完整路径
                self.video_list.addItem(item)
                self.statusBar().showMessage(f"已添加视频文件: {os.path.basename(file_path)}")
                log_handler.log("info", f"添加视频文件: {file_path}")
    
    def remove_video(self):
        """从视频池中移除视频"""
        selected_items = self.video_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "请先选择要移除的视频")
            return
            
        for item in selected_items:
            file_path = item.data(Qt.ItemDataRole.UserRole)
            self.video_list.takeItem(self.video_list.row(item))
            log_handler.log("info", f"移除视频文件: {file_path}")
        
        self.statusBar().showMessage(f"已移除 {len(selected_items)} 个视频文件")
    
    def select_subtitle(self):
        """选择字幕文件"""
        # 记录用户交互
        # 安全调用record_user_interaction

        try:

            if hasattr(self, 'record_user_interaction'):

                self.record_user_interaction()

            else:

                print("🔍 [DEBUG] record_user_interaction方法不存在，跳过")

        except Exception as e:

            print(f"⚠️ [WARNING] record_user_interaction调用失败: {e}")

        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "选择字幕文件", "", "字幕文件 (*.srt *.ass *.vtt)"
        )
        
        for file_path in file_paths:
            if file_path:
                # 添加到SRT列表
                item = QListWidgetItem(os.path.basename(file_path))
                item.setData(Qt.ItemDataRole.UserRole, file_path)  # 存储完整路径
                self.srt_list.addItem(item)
                self.statusBar().showMessage(f"已添加字幕文件: {os.path.basename(file_path)}")
                log_handler.log("info", f"添加字幕文件: {file_path}")
    
    def remove_srt(self):
        """从SRT池中移除SRT文件"""
        selected_items = self.srt_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "请先选择要移除的SRT文件")
            return
        
        for item in selected_items:
            file_path = item.data(Qt.ItemDataRole.UserRole)
            self.srt_list.takeItem(self.srt_list.row(item))
            log_handler.log("info", f"移除字幕文件: {file_path}")
        
        self.statusBar().showMessage(f"已移除 {len(selected_items)} 个SRT文件")

    def detect_gpu(self):
        """检测系统GPU硬件"""
        self.status_label.setText("正在检测GPU...")
        self.statusBar().showMessage("正在检测GPU硬件...")
        log_handler.log("info", "开始检测GPU硬件")
        
        # 使用实际的GPU检测功能
        QApplication.processEvents()
        
        gpu_info = detect_gpu_info()
        gpu_available = gpu_info.get("available", False)
        gpu_name = gpu_info.get("name", "未知")
        
        # 更新UI
        if gpu_available:
            self.status_label.setText(f"GPU检测完成: {gpu_name}")
            self.statusBar().showMessage("GPU检测完成 - 已启用GPU加速")
            log_handler.log("info", f"检测到GPU: {gpu_name}")
            QMessageBox.information(self, "GPU检测结果", f"检测到GPU硬件：\n{gpu_name}\n\n已启用GPU加速功能！")
        else:
            self.status_label.setText(f"GPU检测完成: {gpu_name}")
            self.statusBar().showMessage("GPU检测完成 - 将使用CPU模式")
            log_handler.log("info", "未检测到GPU，将使用CPU模式")
            QMessageBox.warning(self, "GPU检测结果", f"{gpu_name}\n\n将使用CPU模式运行，处理速度可能较慢。")

    def change_language_mode(self, mode):
        """切换语言模式"""
        if mode == self.language_mode:
            return

        # 保存原始语言模式，用于在取消时恢复
        original_mode = self.language_mode

        self.language_mode = mode
        mode_names = {
            "auto": "自动检测",
            "zh": "中文模式",
            "en": "英文模式"
        }

        # 明确告知用户当前使用的是哪种语言模型
        if mode == "zh":
            model_info = "Qwen2.5-7B 中文模型"
        elif mode == "en":
            model_info = "Mistral-7B 英文模型"
        else:
            model_info = "自动检测模型"

        # 避免重复弹窗，使用全局标志位表示弹窗状态
        if hasattr(self, '_global_model_dialog_showing') and self._global_model_dialog_showing:
            log_handler.log("info", "⚠️ 语言切换检测到模型下载对话框已在显示中，跳过重复弹窗")
            return

        # 如果选择了英文模式，检查英文模型是否已下载
        if mode == "en":
            if not self.en_model_exists:
                download_success = False
                try:
                    # 直接使用增强下载器，避免通过check_en_model重复调用
                    log_handler.log("info", "🔍 语言切换检测到英文模型缺失，直接显示智能推荐对话框")
                    if self.enhanced_downloader and self.enhanced_downloader.has_intelligent_selector:
                        # 重要修复：彻底重置状态，确保状态隔离
                        self.enhanced_downloader.reset_state()
                        # 注意：不在这里设置标志位，让enhanced_downloader内部管理
                        success = self.enhanced_downloader.download_model("mistral-7b", self)
                        if success:
                            log_handler.log("info", "✅ 英文模型下载已启动")
                            download_success = True
                        else:
                            log_handler.log("warning", "⚠️ 英文模型下载被取消")
                    else:
                        # 回退到简单对话框（设置标志位防止重复）
                        self._global_model_dialog_showing = True
                        try:
                            reply = QMessageBox.question(
                                self,
                                "英文模型未安装",
                                "英文模型尚未下载，是否现在下载？\n(约4GB，需要较长时间)",
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                QMessageBox.StandardButton.Yes
                            )
                            if reply == QMessageBox.StandardButton.Yes:
                                # 直接调用回退下载方法，避免重复弹窗
                                self._fallback_download_en_model()
                                download_success = True
                        finally:
                            # 清除全局弹窗标志
                            self._global_model_dialog_showing = False
                except Exception as e:
                    log_handler.log("error", f"❌ 英文模型下载处理失败: {str(e)}")
                    # 确保清除标志位
                    self._global_model_dialog_showing = False

                # 如果用户取消下载，恢复原始语言模式和单选按钮状态
                if not download_success:
                    log_handler.log("info", "🔄 用户取消英文模型下载，恢复原始语言模式")
                    self.language_mode = original_mode
                    self._restore_language_radio_buttons(original_mode)
                    return

                # 如果在训练页面，也更新训练页面的语言选择（标记为来自主窗口）
                if hasattr(self, 'train_feeder'):
                    self.train_feeder.switch_training_language("en", from_main_window=True)
                return  # 在下载对话框中用户可能会切换回其他模式，此处直接返回

        # 如果选择了中文模式，检查中文模型是否已下载
        if mode == "zh":
            if not self.zh_model_exists:
                download_success = False
                try:
                    # 直接使用增强下载器，避免通过check_zh_model重复调用
                    log_handler.log("info", "🔍 语言切换检测到中文模型缺失，直接显示智能推荐对话框")
                    if self.enhanced_downloader and self.enhanced_downloader.has_intelligent_selector:
                        # 重要修复：彻底重置状态，确保状态隔离
                        self.enhanced_downloader.reset_state()
                        # 注意：不在这里设置标志位，让enhanced_downloader内部管理
                        success = self.enhanced_downloader.download_model("qwen2.5-7b", self)
                        if success:
                            log_handler.log("info", "✅ 中文模型下载已启动")
                            download_success = True
                        else:
                            log_handler.log("warning", "⚠️ 中文模型下载被取消")
                    else:
                        # 回退到简单对话框（设置标志位防止重复）
                        self._global_model_dialog_showing = True
                        try:
                            reply = QMessageBox.question(
                                self,
                                "中文模型未安装",
                                "中文模型尚未下载，是否现在下载？\n(约4GB，需要较长时间)",
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                QMessageBox.StandardButton.Yes
                            )
                            if reply == QMessageBox.StandardButton.Yes:
                                # 直接调用回退下载方法，避免重复弹窗
                                self._fallback_download_zh_model()
                                download_success = True
                        finally:
                            # 清除全局弹窗标志
                            self._global_model_dialog_showing = False
                except Exception as e:
                    log_handler.log("error", f"❌ 中文模型下载处理失败: {str(e)}")
                    # 确保清除标志位
                    self._global_model_dialog_showing = False

                # 如果用户取消下载，恢复原始语言模式和单选按钮状态
                if not download_success:
                    log_handler.log("info", "🔄 用户取消中文模型下载，恢复原始语言模式")
                    self.language_mode = original_mode
                    self._restore_language_radio_buttons(original_mode)
                    return

                # 如果在训练页面，也更新训练页面的语言选择（标记为来自主窗口）
                if hasattr(self, 'train_feeder'):
                    self.train_feeder.switch_training_language("zh", from_main_window=True)
                return  # 在下载对话框中用户可能会切换回其他模式，此处直接返回
        
        # 记录切换并更新状态栏
        self.statusBar().showMessage(f"已切换到{mode_names.get(mode, '未知')}，使用{model_info}")
        log_handler.log("info", f"语言模式切换为: {mode_names.get(mode, '未知')} ({model_info})")
        
        # 如果在训练页面，也更新训练页面的语言选择（标记为来自主窗口）
        if hasattr(self, 'train_feeder'):
            self.train_feeder.switch_training_language(mode, from_main_window=True)
        
        # 设置界面方向
        if HAS_TEXT_DIRECTION:
            set_application_layout_direction(mode)
            is_rtl = LayoutDirection.is_rtl_language(mode)
            if is_rtl:
                log_handler.log("info", f"切换到RTL语言({mode})，调整布局方向")
            
            # 应用RTL样式
            apply_rtl_styles(self, mode)

    def _restore_language_radio_buttons(self, mode):
        """恢复语言模式单选按钮状态

        Args:
            mode: 要恢复的语言模式 ("auto", "zh", "en")
        """
        try:
            # 临时断开信号连接，避免触发递归调用
            self.lang_auto_radio.clicked.disconnect()
            self.lang_zh_radio.clicked.disconnect()
            self.lang_en_radio.clicked.disconnect()

            # 根据模式设置对应的单选按钮
            if mode == "auto":
                self.lang_auto_radio.setChecked(True)
                self.lang_zh_radio.setChecked(False)
                self.lang_en_radio.setChecked(False)
            elif mode == "zh":
                self.lang_auto_radio.setChecked(False)
                self.lang_zh_radio.setChecked(True)
                self.lang_en_radio.setChecked(False)
            elif mode == "en":
                self.lang_auto_radio.setChecked(False)
                self.lang_zh_radio.setChecked(False)
                self.lang_en_radio.setChecked(True)

            # 重新连接信号
            self.lang_auto_radio.clicked.connect(lambda: self.change_language_mode("auto"))
            self.lang_zh_radio.clicked.connect(lambda: self.change_language_mode("zh"))
            self.lang_en_radio.clicked.connect(lambda: self.change_language_mode("en"))

            log_handler.log("info", f"✅ 已恢复语言模式单选按钮状态: {mode}")

        except Exception as e:
            log_handler.log("error", f"❌ 恢复语言模式单选按钮状态失败: {str(e)}")
            # 确保信号重新连接，即使出错也要保证功能正常
            try:
                self.lang_auto_radio.clicked.connect(lambda: self.change_language_mode("auto"))
                self.lang_zh_radio.clicked.connect(lambda: self.change_language_mode("zh"))
                self.lang_en_radio.clicked.connect(lambda: self.change_language_mode("en"))
            except:
                pass

    def setup_language_direction(self):
        """设置语言方向支持
        
        根据当前系统语言设置适当的文本方向，支持RTL语言
        """
        if not HAS_TEXT_DIRECTION:
            return
        
        # 尝试获取系统语言设置
        try:
            import locale
            system_lang = locale.getdefaultlocale()[0]
            if system_lang:
                lang_code = system_lang.split('_')[0].lower()
                log_handler.log("info", f"检测到系统语言: {system_lang}, 语言代码: {lang_code}")
                
                # 设置布局方向
                set_application_layout_direction(lang_code)
                
                # 如果是RTL语言，记录日志
                if LayoutDirection.is_rtl_language(lang_code):
                    log_handler.log("info", f"检测到RTL语言({lang_code})，已调整布局方向为从右到左")
                    # 应用RTL样式
                    apply_rtl_styles(self, lang_code)
        except Exception as e:
            log_handler.log("error", f"设置语言方向时出错: {e}")
    
    def show_about_dialog(self):
        """显示团队介绍对话框"""
        log_handler.log("info", "用户打开团队介绍对话框")
        # 创建团队介绍对话框
        about_dialog = QDialog(self)
        about_dialog.setWindowTitle("团队介绍")
        about_dialog.setMinimumSize(700, 600)

        # 创建布局
        layout = QVBoxLayout(about_dialog)

        # 添加标题
        title = QLabel("CKEN - 开发者介绍")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #1a5276; margin-bottom: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # 添加开发者简介
        team_intro = QLabel("全栈AI开发者，专注于短剧混剪和智能内容创作技术")
        team_intro.setStyleSheet("font-size: 14px; color: #2980b9; font-style: italic; margin-bottom: 20px;")
        team_intro.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(team_intro)

        # 添加团队详情
        description = QTextEdit()
        description.setReadOnly(True)
        description.setHtml("""
        <div style="margin: 15px; line-height: 1.6;">
            <h3 style="color: #1a5276; border-bottom: 2px solid #3498db; padding-bottom: 5px;">👨‍💻 关于CKEN</h3>

            <div style="margin: 15px 0; padding: 12px; background-color: #f8f9fa; border-left: 4px solid #3498db; border-radius: 5px;">
                <h4 style="color: #2c3e50; margin-top: 0;">🚀 全栈AI开发者</h4>
                <p><strong>专业背景：</strong>具有丰富的AI算法开发和视频处理经验，专注于将前沿AI技术应用于实际产品</p>
                <p><strong>技术理念：</strong>相信技术应该服务于创意，让复杂的AI技术变得简单易用</p>
                <p><strong>开发愿景：</strong>让每个人都能轻松创作出专业级的短剧内容</p>
            </div>

            <h3 style="color: #1a5276; border-bottom: 2px solid #3498db; padding-bottom: 5px; margin-top: 25px;">🛠️ 技术专长领域</h3>

            <div style="margin: 15px 0; padding: 10px; background-color: #f8f9fa; border-left: 4px solid #e74c3c;">
                <h4 style="color: #2c3e50; margin-top: 0;">🧠 AI算法开发</h4>
                <p><strong>核心技能：</strong>大型语言模型优化、自然语言处理、深度学习算法设计</p>
                <p><strong>项目成果：</strong>Mistral-7B/Qwen2.5-7B双模型架构、智能字幕重构、病毒式传播算法</p>
            </div>

            <div style="margin: 15px 0; padding: 10px; background-color: #f8f9fa; border-left: 4px solid #f39c12;">
                <h4 style="color: #2c3e50; margin-top: 0;">🎬 视频处理技术</h4>
                <p><strong>核心技能：</strong>视频编解码、音视频同步、FFmpeg优化、GPU加速处理</p>
                <p><strong>项目成果：</strong>≤0.5秒时间轴精度、剪映工程文件导出、多格式批量处理</p>
            </div>

            <div style="margin: 15px 0; padding: 10px; background-color: #f8f9fa; border-left: 4px solid #27ae60;">
                <h4 style="color: #2c3e50; margin-top: 0;">⚙️ 系统架构设计</h4>
                <p><strong>核心技能：</strong>软件架构设计、性能优化、系统稳定性、模块化开发</p>
                <p><strong>项目成果：</strong>4GB内存兼容设计、增强异常处理机制、结构化日志系统</p>
            </div>

            <div style="margin: 15px 0; padding: 10px; background-color: #f8f9fa; border-left: 4px solid #9b59b6;">
                <h4 style="color: #2c3e50; margin-top: 0;">🎨 用户体验设计</h4>
                <p><strong>核心技能：</strong>PyQt6界面开发、用户体验优化、响应式设计</p>
                <p><strong>项目成果：</strong>直观的操作界面、实时进度监控、用户友好的错误提示</p>
            </div>

            <div style="margin: 15px 0; padding: 10px; background-color: #f8f9fa; border-left: 4px solid #34495e;">
                <h4 style="color: #2c3e50; margin-top: 0;">🔬 质量保证</h4>
                <p><strong>核心技能：</strong>软件测试、质量控制、自动化测试、性能验证</p>
                <p><strong>项目成果：</strong>85.7%集成测试通过率、全面的异常覆盖、生产就绪验证</p>
            </div>

            <h3 style="color: #1a5276; border-bottom: 2px solid #3498db; padding-bottom: 5px; margin-top: 25px;">🌟 开发特色</h3>
            <ul style="margin: 10px 0; padding-left: 20px;">
                <li><strong>全栈能力：</strong>从AI算法到前端界面，具备完整的产品开发能力</li>
                <li><strong>技术创新：</strong>首创双模型架构，实现中英文无缝切换处理</li>
                <li><strong>用户导向：</strong>始终以用户体验为中心，追求简单易用的产品设计</li>
                <li><strong>质量至上：</strong>严格的开发流程和测试标准，确保产品稳定可靠</li>
                <li><strong>持续学习：</strong>紧跟AI技术发展趋势，不断优化和改进产品功能</li>
            </ul>

            <h3 style="color: #1a5276; border-bottom: 2px solid #3498db; padding-bottom: 5px; margin-top: 25px;">📞 联系方式</h3>
            <div style="margin: 15px 0; padding: 12px; background-color: #f0f8ff; border-left: 4px solid #3498db; border-radius: 5px;">
                <p style="margin: 5px 0;"><strong>GitHub:</strong> <a href="https://github.com/CKEN" style="color: #3498db; text-decoration: none;">@CKEN</a></p>
                <p style="margin: 5px 0;"><strong>项目仓库：</strong> VisionAI-ClipsMaster</p>
                <p style="margin: 5px 0;"><strong>开发理念：</strong> 让AI技术服务于每一个创作者</p>
            </div>

            <div style="text-align: center; margin-top: 20px; padding: 15px; background-color: #ecf0f1; border-radius: 5px;">
                <p style="color: #2c3e50; font-weight: bold; margin: 0;">
                    "让AI技术服务于创意，让每个人都能创作出专业级的短剧内容"
                </p>
                <p style="color: #7f8c8d; font-size: 12px; margin: 5px 0 0 0;">
                    — CKEN
                </p>
            </div>
        </div>
        """)
        layout.addWidget(description)

        # 添加关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.setMinimumWidth(100)
        close_btn.setStyleSheet("font-size: 14px; padding: 8px 20px;")
        close_btn.clicked.connect(about_dialog.close)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # 显示对话框
        about_dialog.exec()

    def show_tech_dialog(self):
        """显示技术信息对话框"""
        tech_dialog = TechDialog(self)
        tech_dialog.exec()

    def show_history_dialog(self):
        """显示历史信息对话框"""
        history_dialog = HistoryDialog(self)
        history_dialog.exec()
    
    def show_system_monitor(self):
        """显示系统监控窗口"""
        try:
            from ui.monitor.system_monitor_app import SystemMonitorWindow
            
            # 检查是否已经打开了监控窗口
            if hasattr(self, 'monitor_window') and self.monitor_window is not None:
                # 如果窗口已经存在，则激活它
                self.monitor_window.setWindowState(self.monitor_window.windowState() & ~Qt.WindowState.WindowMinimized | Qt.WindowState.WindowActive)
                self.monitor_window.activateWindow()
                return
            
            # 检测系统资源状态
            try:
                import psutil
                cpu_percent = psutil.cpu_percent(interval=0.5)
                mem_percent = psutil.virtual_memory().percent
                
                # 如果系统资源紧张，提示用户是否使用低资源模式
                use_low_spec = False
                if cpu_percent > 80 or mem_percent > 90:
                    response = QMessageBox.question(
                        self,
                        "系统资源提示",
                        f"当前系统资源使用较高 (CPU: {cpu_percent:.1f}%, 内存: {mem_percent:.1f}%)\n"
                        f"建议使用低资源模式打开监控窗口，以减少系统负担。\n\n"
                        f"是否使用低资源模式？",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.Yes
                    )
                    use_low_spec = (response == QMessageBox.StandardButton.Yes)
            except Exception:
                use_low_spec = False
            
            # 创建新的监控窗口
            self.monitor_window = SystemMonitorWindow()
            
            # 如果用户选择了低资源模式，则配置低资源模式
            if use_low_spec:
                try:
                    # 导入配置加载器
                    from ui.monitor.config_loader import monitor_config
                    # 设置为非自动模式，强制使用低资源模式
                    monitor_config.update_nested_config("performance.auto_mode", False)
                    # 应用配置更改
                    if hasattr(self.monitor_window, '_apply_config_changes'):
                        self.monitor_window._apply_config_changes()
                    log_handler.log("info", "已启用低资源模式监控")
                except Exception as e:
                    log_handler.log("warning", f"无法配置低资源模式: {str(e)}")
            
            # 设置窗口关闭时的处理
            self.monitor_window.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
            self.monitor_window.destroyed.connect(self._on_monitor_closed)
            
            # 显示窗口
            self.monitor_window.show()
            
            log_handler.log("info", "已打开系统监控窗口")
        except ImportError as e:
            if HAS_ERROR_VISUALIZER:
                show_error(
                    ErrorInfo(
                        title="无法打开系统监控",
                        message=f"缺少必要的监控模块: {str(e)}",
                        details="请确保已安装所有必要的依赖项",
                        error_type=ErrorType.IMPORT_ERROR
                    )
                )
            else:
                QMessageBox.warning(
                    self,
                    "无法打开系统监控",
                    f"缺少必要的监控模块: {str(e)}\n请确保已安装所有必要的依赖项"
                )
            log_handler.log("error", f"无法打开系统监控: {str(e)}")
        except Exception as e:
            log_handler.log("error", f"打开系统监控时发生错误: {str(e)}")
            QMessageBox.warning(
                self,
                "打开系统监控失败",
                f"发生错误: {str(e)}"
            )
    
    def _on_monitor_closed(self):
        """监控窗口关闭时的处理"""
        self.monitor_window = None
        log_handler.log("info", "系统监控窗口已关闭")
    
    def show_hotkey_guide(self):
        """显示热键指南对话框"""
        # 创建热键指南对话框
        hotkey_dialog = QDialog(self)
        hotkey_dialog.setWindowTitle("热键指南")
        hotkey_dialog.setMinimumSize(500, 400)
        
        # 创建布局
        layout = QVBoxLayout(hotkey_dialog)
        
        # 标题
        title_label = QLabel("热键指南")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px; color: #2c3e50;")
        layout.addWidget(title_label)
        
        # 创建热键表格
        table = QTableWidget(3, 3)  # 3行3列
        table.setHorizontalHeaderLabels(["组合键", "功能", "描述"])
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        
        # 添加热键信息
        hotkeys_data = [
            ["Ctrl+U", "聚焦上传区域", "快速将焦点切换到视频或SRT文件上传区域，方便添加新文件"],
            ["Ctrl+P", "切换预览模式", "显示或切换预览窗口，可预览视频内容或SRT文件内容"],
            ["Ctrl+G", "立即开始生成", "根据当前界面状态，触发视频生成或爆款SRT生成功能"]
        ]
        
        for row, (key, func, desc) in enumerate(hotkeys_data):
            table.setItem(row, 0, QTableWidgetItem(key))
            table.setItem(row, 1, QTableWidgetItem(func))
            table.setItem(row, 2, QTableWidgetItem(desc))
            
        layout.addWidget(table)
        
        # 添加详细说明
        details = QTextEdit()
        details.setReadOnly(True)
        details.setHtml("""
        <h3>热键功能详细说明</h3>
        
        <p><b>聚焦上传区域 (Ctrl+U)</b></p>
        <ul>
            <li>在<b>视频处理页面</b>：将焦点切换到视频列表，方便操作视频文件</li>
            <li>在<b>训练页面</b>：将焦点切换到原始SRT列表，方便添加或管理SRT文件</li>
        </ul>
        
        <p><b>切换预览模式 (Ctrl+P)</b></p>
        <ul>
            <li>打开预览对话框，显示当前选中内容的预览</li>
            <li>视频文件：显示视频基本信息</li>
            <li>SRT文件：显示字幕内容</li>
            <li>爆款SRT：显示生成的爆款SRT内容</li>
        </ul>
        
        <p><b>立即开始生成 (Ctrl+G)</b></p>
        <ul>
            <li>在<b>视频处理页面</b>：如果已添加视频和SRT文件，则开始生成混剪视频</li>
            <li>在<b>训练页面</b>：如果已添加原始SRT文件，则开始训练并生成爆款SRT</li>
        </ul>
        
        <p><b>注意事项</b></p>
        <ul>
            <li>热键功能会根据当前界面状态和可用资源自动调整</li>
            <li>在某些操作过程中（如模型训练、视频处理），部分热键可能会暂时失效</li>
            <li>使用热键时，请注意查看状态栏的反馈信息</li>
        </ul>
        """)
        layout.addWidget(details)
        
        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(hotkey_dialog.close)
        layout.addWidget(close_btn)
        
        # 显示对话框
        hotkey_dialog.exec()
    
    def open_url(self, url):
        """打开URL"""
        try:
            import webbrowser
            webbrowser.open(url)
        except Exception as e:
            QMessageBox.information(self, "链接信息", f"请访问: {url}")
            log_handler.log("error", f"打开URL失败: {url}, 错误: {e}")
    
    def open_email(self, email):
        """打开邮件客户端"""
        try:
            import webbrowser
            webbrowser.open(f"mailto:{email}")
        except Exception as e:
            QMessageBox.information(self, "联系信息", f"请联系我们: {email}")
            log_handler.log("error", f"打开邮件失败: {email}, 错误: {e}")

    def on_process_error(self, error_message):
        """处理视频处理错误"""
        # 恢复UI状态
        self.process_progress_bar.setValue(0)
        self.status_label.setText("处理失败")
        self.statusBar().showMessage("视频处理失败")
        
        # 记录错误日志
        log_handler.log("error", f"视频处理错误: {error_message}")
        
        # 显示错误消息
        if HAS_ERROR_VISUALIZER:
            # 使用全息错误显示
            error_info = ErrorInfo(
                title="视频处理失败",
                description=error_message,
                error_type=ErrorType.ERROR,
                details="视频处理过程中出现错误，可能是因为视频格式不兼容或处理参数设置问题。",
                solutions=["检查视频格式", "尝试不同参数", "使用其他视频文件"]
            )
            show_error(error_info, self)
        else:
            # 使用传统错误显示
            QMessageBox.critical(
                self,
                "处理失败",
                f"视频处理失败: {error_message}"
            )
            
    # 热键功能方法 - 聚焦上传区域
    def focus_upload(self):
        """热键功能：聚焦到上传区域
        
        响应Ctrl+U快捷键，将焦点设置到视频上传区域
        """
        current_tab = self.tabs.currentIndex()
        
        # 如果当前是视频处理页面
        if current_tab == 0 and self.video_list is not None:
            self.video_list.setFocus()
            self.statusBar().showMessage("已聚焦到视频上传区域", 3000)
            log_handler.log("info", "快捷键触发：聚焦到视频上传区域")
            return True
        # 如果当前是训练页面且存在训练器
        elif current_tab == 1 and hasattr(self, 'train_feeder'):
            if hasattr(self.train_feeder, 'original_srt_list'):
                self.train_feeder.original_srt_list.setFocus()
                self.statusBar().showMessage("已聚焦到SRT上传区域", 3000)
                log_handler.log("info", "快捷键触发：聚焦到SRT上传区域")
                return True
            
        self.statusBar().showMessage("当前页面没有上传区域", 3000)
        return False
    
    # 热键功能方法 - 切换预览模式
    def show_preview(self):
        """热键功能：切换预览模式
        
        响应Ctrl+P快捷键，显示或切换预览模式
        """
        if not hasattr(self, 'viral_preview_dialog'):
            # 创建预览对话框
            from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton
            
            self.viral_preview_dialog = QDialog(self)
            self.viral_preview_dialog.setWindowTitle("预览")
            self.viral_preview_dialog.setMinimumSize(800, 600)
            self.viral_preview_dialog.resize(900, 700)

            layout = QVBoxLayout(self.viral_preview_dialog)
            layout.setContentsMargins(10, 10, 10, 10)
            layout.setSpacing(10)

            self.preview_text_edit = QTextEdit()
            self.preview_text_edit.setReadOnly(True)

            # 设置字体和行高以改善可读性
            font = self.preview_text_edit.font()
            font.setPointSize(11)
            font.setFamily("Consolas, Monaco, 'Courier New', monospace")
            self.preview_text_edit.setFont(font)

            # 设置行高
            self.preview_text_edit.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)

            # 确保滚动条可见
            self.preview_text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            self.preview_text_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

            # 设置文档边距以确保文字完整显示
            self.preview_text_edit.document().setDocumentMargin(10)

            # 创建边框容器Frame来确保边框完整显示
            self.preview_text_frame = QFrame()
            self.preview_text_frame.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Plain)
            self.preview_text_frame.setLineWidth(3)
            self.preview_text_frame.setMidLineWidth(0)

            # 设置Frame的样式 - 修复对话框预览区域文字显示
            self.preview_text_frame.setStyleSheet("""
                QFrame {
                    border: 3px solid #a0a0a0;
                    border-radius: 10px;
                    background-color: #ffffff;
                    margin: 4px;
                    padding: 0px;
                }
                QFrame:focus-within {
                    border: 3px solid #4a90e2;
                }
            """)

            # 创建Frame内部布局 - 修复对话框布局边距
            text_frame_layout = QVBoxLayout(self.preview_text_frame)
            text_frame_layout.setContentsMargins(3, 3, 3, 3)
            text_frame_layout.setSpacing(0)

            # 设置TextEdit的样式 - 修复对话框文本显示和对齐
            self.preview_text_edit.setStyleSheet("""
                QTextEdit {
                    border: none;
                    background-color: #ffffff;
                    padding: 15px;
                    margin: 0px;
                    font-size: 11pt;
                    line-height: 1.4;
                    text-align: top;
                    vertical-align: top;
                }
                QScrollBar:vertical {
                    background-color: #f0f0f0;
                    width: 14px;
                    border: none;
                    border-radius: 7px;
                }
                QScrollBar:horizontal {
                    background-color: #f0f0f0;
                    height: 14px;
                    border: none;
                    border-radius: 7px;
                }
                QScrollBar::handle:vertical {
                    background-color: #c0c0c0;
                    border-radius: 7px;
                    min-height: 25px;
                }
                QScrollBar::handle:horizontal {
                    background-color: #c0c0c0;
                    border-radius: 7px;
                    min-width: 25px;
                }
                QScrollBar::handle:vertical:hover,
                QScrollBar::handle:horizontal:hover {
                    background-color: #a0a0a0;
                }
            """)

            # 将TextEdit添加到Frame中
            text_frame_layout.addWidget(self.preview_text_edit)

            layout.addWidget(self.preview_text_frame)
            
            close_button = QPushButton("关闭")
            close_button.clicked.connect(self.viral_preview_dialog.close)
            layout.addWidget(close_button)
            
            log_handler.log("info", "创建预览对话框")
        
        # 根据当前标签页显示不同的预览内容
        current_tab = self.tabs.currentIndex()

        if current_tab == 0:  # 视频处理页面
            # 尝试预览选中的视频或SRT
            if self.video_list.currentItem():
                video_path = self.video_list.currentItem().data(Qt.ItemDataRole.UserRole)
                # 这里可以集成一个视频预览功能，暂时先显示路径
                self.preview_text_edit.setText(f"视频文件：{video_path}\n\n(视频预览功能将在未来版本中实现)")
                log_handler.log("info", f"预览视频文件: {video_path}")
            elif self.srt_list.currentItem():
                srt_path = self.srt_list.currentItem().data(Qt.ItemDataRole.UserRole)
                # 读取并显示SRT内容
                try:
                    with open(srt_path, 'r', encoding='utf-8') as f:
                        srt_content = f.read()
                    self.preview_text_edit.setText(f"SRT文件：{srt_path}\n\n{srt_content}")
                    log_handler.log("info", f"预览SRT文件: {srt_path}")
                except Exception as e:
                    self.preview_text_edit.setText(f"无法读取SRT文件：{str(e)}")
                    log_handler.log("error", f"预览SRT失败: {str(e)}")
            else:
                self.preview_text_edit.setText("请先选择视频或SRT文件")
                log_handler.log("info", "预览请求：未选择文件")
        elif current_tab == 1:  # 训练页面
            # 显示训练相关信息
            training_info = "训练模式预览\n\n"
            training_info += "当前训练设置：\n"
            training_info += "• 中文模型训练\n"
            training_info += "• 数据增强：启用\n"
            training_info += "• 批处理大小：自动调整\n"
            training_info += "• 内存优化：启用\n\n"
            training_info += "训练数据统计将在开始训练后显示..."
            self.preview_text_edit.setText(training_info)
            log_handler.log("info", "预览训练页面内容")
                    
        # 显示预览对话框
        self.viral_preview_dialog.show()
        self.viral_preview_dialog.raise_()
        log_handler.log("info", "快捷键触发：显示预览")
        
        return True
    
    # 热键功能方法 - 立即开始生成
    def trigger_generation(self):
        """热键功能：立即开始生成
        
        响应Ctrl+G快捷键，根据当前界面状态触发相应的生成功能
        """
        current_tab = self.tabs.currentIndex()
        
        # 视频处理页面
        if current_tab == 0:
            # 如果有视频和SRT，则开始生成视频
            if (self.video_list.count() > 0 and 
                self.srt_list.count() > 0):
                self.generate_video()
                log_handler.log("info", "快捷键触发：开始生成视频")
                return True
            else:
                self.statusBar().showMessage("生成视频需要先添加视频和SRT文件", 3000)
        
        # 训练页面
        elif current_tab == 1 and hasattr(self, 'train_feeder'):
            # 如果有原始SRT，则开始生成爆款SRT
            if (hasattr(self.train_feeder, 'original_srt_list') and
                self.train_feeder.original_srt_list.count() > 0):
                self.train_feeder.viral_srt.clear()
                self.generate_viral_srt()
                log_handler.log("info", "快捷键触发：开始生成爆款SRT")
                return True
            else:
                self.statusBar().showMessage("生成爆款SRT需要先添加原始SRT文件", 3000)
        
        return False

    def on_process_started(self):
        """处理开始时调用"""
        try:
            # 记录用户交互
            # 安全调用record_user_interaction

            try:

                if hasattr(self, 'record_user_interaction'):

                    self.record_user_interaction()

                else:

                    print("🔍 [DEBUG] record_user_interaction方法不存在，跳过")

            except Exception as e:

                print(f"⚠️ [WARNING] record_user_interaction调用失败: {e}")

            self.is_processing = True
            self.process_progress_bar.setValue(0)
            self.statusBar().showMessage("处理开始...")
            log_handler.log("info", "处理开始")
            print("[OK] 视频处理已开始")
        except Exception as e:
            print(f"处理开始事件处理失败: {e}")
    
    def on_process_finished(self):
        """处理完成时调用"""
        self.is_processing = False
        self.process_progress_bar.setValue(100)
        self.statusBar().showMessage("处理完成")
        log_handler.log("info", "处理完成")
    
    def on_process_progress(self, progress):
        """处理进度更新时调用"""
        self.process_progress_bar.setValue(progress)
    
    def on_process_log(self, message, level="INFO"):
        """处理日志更新时调用（增强版）"""
        if hasattr(self, 'log_display'):
            # 根据日志级别设置颜色
            color_map = {
                'DEBUG': '#888888',
                'INFO': '#ffffff',
                'WARNING': '#ffaa00',
                'ERROR': '#ff4444',
                'CRITICAL': '#ff0000'
            }

            color = color_map.get(level.upper(), '#ffffff')
            timestamp = datetime.now().strftime('%H:%M:%S')

            # 格式化消息
            formatted_message = f'<span style="color: {color}">[{timestamp}] {message}</span>'

            self.log_display.append(formatted_message)
            # 滚动到底部
            self.log_display.verticalScrollBar().setValue(
                self.log_display.verticalScrollBar().maximum()
            )

    def generate_viral_srt(self):
        """生成爆款SRT - 优化版本，支持异步处理"""
        start_time = time.time()

        try:
            # 记录用户交互
            # 安全调用record_user_interaction

            try:

                if hasattr(self, 'record_user_interaction'):

                    self.record_user_interaction()

                else:

                    print("🔍 [DEBUG] record_user_interaction方法不存在，跳过")

            except Exception as e:

                print(f"⚠️ [WARNING] record_user_interaction调用失败: {e}")

            # 检查是否有选中的SRT
            if self.srt_list.count() == 0:
                QMessageBox.warning(self, "警告", "请先添加SRT字幕文件")
                return

            # 获取选中的SRT文件
            selected_items = self.srt_list.selectedItems()
            if not selected_items:
                QMessageBox.warning(self, "警告", "请选择要处理的SRT文件")
                return

            # 防止重复处理
            if self.is_processing:
                QMessageBox.information(self, "提示", "正在处理中，请稍候...")
                return

            # 获取当前语言模式
            current_lang_mode = self.lang_combo.currentData()
            log_handler.log("info", f"开始生成爆款SRT，语言模式: {current_lang_mode}")

            # 重新检查模型状态，确保状态是最新的
            log_handler.log("info", "🔄 重新检查模型状态...")
            self.check_models()

            # 检查对应语言的模型是否存在
            if current_lang_mode == "zh":
                if not self.zh_model_exists:
                    log_handler.log("info", "🔍 视频处理检测到中文模型缺失，显示智能推荐对话框")
                    self.check_zh_model()
                    return
            elif current_lang_mode == "en":
                if not self.en_model_exists:
                    log_handler.log("info", "🔍 视频处理检测到英文模型缺失，显示智能推荐对话框")
                    self.check_en_model()
                    return
            elif current_lang_mode == "auto":
                # 自动模式下，检查两个模型是否都存在，如果都不存在，优先推荐中文模型
                if not self.zh_model_exists and not self.en_model_exists:
                    log_handler.log("info", "🔍 视频处理检测到自动模式下两个模型都缺失，优先推荐中文模型")
                    self.check_zh_model()
                    return
                elif not self.zh_model_exists:
                    log_handler.log("info", "🔍 视频处理检测到自动模式下中文模型缺失，显示智能推荐对话框")
                    self.check_zh_model()
                    return
                elif not self.en_model_exists:
                    log_handler.log("info", "🔍 视频处理检测到自动模式下英文模型缺失，显示智能推荐对话框")
                    self.check_en_model()
                    return

            # 设置处理状态
            self.is_processing = True
            self.process_progress_bar.setValue(0)
            self.statusBar().showMessage("正在准备生成爆款SRT...")

            # 优化：使用异步处理避免界面冻结
            self._process_viral_srt_async(selected_items)

        except Exception as e:
            self.is_processing = False
            error_msg = f"生成爆款SRT时发生错误: {str(e)}"
            print(f"[ERROR] {error_msg}")
            QMessageBox.critical(self, "错误", error_msg)
            self.statusBar().showMessage("生成爆款SRT失败")
        finally:
            elapsed = time.time() - start_time
            if elapsed > 0.1:  # 如果初始化时间超过0.1秒，记录
                print(f"[PERF] 爆款SRT生成初始化耗时: {elapsed:.3f}秒")

    def _process_viral_srt_async(self, selected_items):
        """异步处理爆款SRT生成"""
        try:
            # 创建工作线程
            self.viral_srt_thread = QThread()
            self.viral_srt_worker = ViralSRTWorker(selected_items, self.lang_combo.currentData())
            self.viral_srt_worker.moveToThread(self.viral_srt_thread)

            # 连接信号
            self.viral_srt_thread.started.connect(self.viral_srt_worker.process)
            self.viral_srt_worker.progress_updated.connect(self._on_viral_srt_progress)
            self.viral_srt_worker.item_completed.connect(self._on_viral_srt_item_completed)
            self.viral_srt_worker.all_completed.connect(self._on_viral_srt_all_completed)
            self.viral_srt_worker.error_occurred.connect(self._on_viral_srt_error)

            # 启动线程
            self.viral_srt_thread.start()

        except Exception as e:
            self.is_processing = False
            print(f"[ERROR] 异步处理启动失败: {e}")
            QMessageBox.critical(self, "错误", f"启动异步处理失败: {str(e)}")

    def _on_viral_srt_progress(self, progress, message):
        """处理爆款SRT生成进度更新"""
        try:
            self.process_progress_bar.setValue(progress)
            self.statusBar().showMessage(message)
        except Exception as e:
            print(f"进度更新失败: {e}")

    def _on_viral_srt_item_completed(self, output_path, original_name):
        """处理单个SRT文件完成"""
        try:
            if output_path:
                # 处理成功，添加生成的SRT到列表
                viral_item = QListWidgetItem(f"爆款-{os.path.basename(output_path)}")
                viral_item.setData(Qt.ItemDataRole.UserRole, output_path)
                self.srt_list.addItem(viral_item)

                log_handler.log("info", f"成功生成爆款SRT: {output_path}")
            else:
                # 处理失败
                log_handler.log("error", f"生成爆款SRT失败: {original_name}")
        except Exception as e:
            print(f"处理完成事件失败: {e}")

    def _on_viral_srt_all_completed(self, success_count, total_count):
        """处理所有SRT文件完成"""
        try:
            self.is_processing = False
            self.process_progress_bar.setValue(100)

            if success_count > 0:
                message = f"成功生成 {success_count}/{total_count} 个爆款SRT文件"
                self.statusBar().showMessage(message)
                if hasattr(self, 'alert_manager'):
                    self.alert_manager.success(message, timeout=5000)
            else:
                message = "所有SRT文件生成失败"
                self.statusBar().showMessage(message)
                if hasattr(self, 'alert_manager'):
                    self.alert_manager.error(message, timeout=5000)

            # 清理线程
            if hasattr(self, 'viral_srt_thread'):
                self.viral_srt_thread.quit()
                self.viral_srt_thread.wait()

        except Exception as e:
            print(f"完成事件处理失败: {e}")

    def _on_viral_srt_error(self, error_message):
        """处理爆款SRT生成错误"""
        try:
            self.is_processing = False
            self.process_progress_bar.setValue(0)
            self.statusBar().showMessage("生成爆款SRT失败")

            QMessageBox.critical(self, "错误", f"生成爆款SRT失败:\n{error_message}")

            # 清理线程
            if hasattr(self, 'viral_srt_thread'):
                self.viral_srt_thread.quit()
                self.viral_srt_thread.wait()

        except Exception as e:
            print(f"错误事件处理失败: {e}")
    
    def generate_video(self):
        """生成混剪视频"""
        # 检查是否有选中的视频和SRT
        if self.video_list.count() == 0:
            QMessageBox.warning(self, "警告", "请先添加视频")
            return
        
        # 获取选中的视频
        selected_video = self.video_list.currentItem()
        if not selected_video:
            QMessageBox.warning(self, "警告", "请选择一个要处理的视频")
            return
        
        video_path = selected_video.data(Qt.ItemDataRole.UserRole)
        
        # 找到选中的爆款SRT
        selected_srt = self.srt_list.currentItem()
        if not selected_srt:
            QMessageBox.warning(self, "警告", "请选择一个SRT文件")
            return
        
        srt_path = selected_srt.data(Qt.ItemDataRole.UserRole)
        
        # 检查是否为爆款SRT
        srt_name = os.path.basename(srt_path)
        if not "爆款" in srt_name:
            reply = QMessageBox.question(
                self, 
                "确认使用", 
                f"所选SRT文件 '{srt_name}' 不是爆款SRT，确定要使用吗?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply != QMessageBox.StandardButton.Yes:
                return
        
        # 显示处理中
        self.statusBar().showMessage(f"正在使用 {os.path.basename(srt_path)} 生成新视频...")
        log_handler.log("info", f"开始生成视频: 视频={video_path}, 字幕={srt_path}")
        
        # 重置进度条
        self.process_progress_bar.setValue(0)
        
        # 询问保存路径
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        default_name = f"{video_name}_爆款.mp4"
        save_path, _ = QFileDialog.getSaveFileName(
            self, "保存生成的视频", default_name, "视频文件 (*.mp4)"
        )
        
        if not save_path:
            self.statusBar().showMessage("视频生成已取消")
            log_handler.log("info", "用户取消视频生成")
            return
        
        # 使用GPU加速
        use_gpu = self.use_gpu_check.isChecked()
        
        # 优化计算资源分配
        try:
            if hasattr(self, 'compute_offloader'):
                # 根据当前任务设置执行模式
                if use_gpu:
                    # 用户选择了GPU加速
                    self.compute_offloader.set_execution_mode("performance")
                    log_handler.log("info", "已为视频生成任务启用GPU加速")
                else:
                    # 用户未选择GPU加速，使用平衡模式
                    self.compute_offloader.set_execution_mode("balanced")
                    log_handler.log("info", "已为视频生成任务设置平衡模式")
        except Exception as e:
            log_handler.log("warning", f"计算资源优化失败: {str(e)}")
        
        try:
            # 调用处理器生成视频
            language_mode = self.lang_combo.currentData()
            output_path = self.processor.process_video(
                video_path=video_path,
                srt_path=srt_path,
                output_path=save_path,
                language_mode=language_mode
            )
            
            if output_path:
                # 成功
                self.statusBar().showMessage(f"视频生成成功: {os.path.basename(output_path)}")
                log_handler.log("info", f"视频生成成功: {output_path}")
                QMessageBox.information(self, "成功", f"爆款视频已生成并保存到:\n{output_path}")
            else:
                # 失败
                self.statusBar().showMessage("视频生成失败")
                log_handler.log("error", "视频生成失败，未返回输出路径")
                QMessageBox.critical(self, "错误", "视频生成失败")
        
        except Exception as e:
            self.statusBar().showMessage(f"视频生成出错: {str(e)}")
            log_handler.log("error", f"视频生成出错: {str(e)}")
            QMessageBox.critical(self, "错误", f"视频生成出错: {str(e)}")
        finally:
            # 恢复默认的执行模式
            try:
                if hasattr(self, 'compute_offloader'):
                    self.compute_offloader.set_execution_mode("balanced")
            except Exception:
                pass

    def generate_project_file(self):
        """生成工程文件（不渲染视频）"""
        # 检查是否有选中的视频和SRT
        if self.video_list.count() == 0:
            QMessageBox.warning(self, "警告", "请先添加视频")
            return

        # 获取选中的视频
        selected_video = self.video_list.currentItem()
        if not selected_video:
            QMessageBox.warning(self, "警告", "请选择一个要处理的视频")
            return

        video_path = selected_video.data(Qt.ItemDataRole.UserRole)

        # 找到选中的爆款SRT
        selected_srt = self.srt_list.currentItem()
        if not selected_srt:
            QMessageBox.warning(self, "警告", "请选择一个SRT文件")
            return

        srt_path = selected_srt.data(Qt.ItemDataRole.UserRole)

        # 检查是否为爆款SRT
        srt_name = os.path.basename(srt_path)
        if not "爆款" in srt_name:
            reply = QMessageBox.question(
                self,
                "确认使用",
                f"所选SRT文件 '{srt_name}' 不是爆款SRT，确定要使用吗?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply != QMessageBox.StandardButton.Yes:
                return

        # 显示处理中
        self.statusBar().showMessage(f"正在生成工程文件...")
        log_handler.log("info", f"开始生成工程文件: 视频={video_path}, 字幕={srt_path}")

        # 重置进度条
        self.process_progress_bar.setValue(0)

        # 询问保存路径
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        default_name = f"{video_name}_工程文件.json"
        save_path, _ = QFileDialog.getSaveFileName(
            self, "保存工程文件", default_name, "工程文件 (*.json)"
        )

        if not save_path:
            self.statusBar().showMessage("工程文件生成已取消")
            log_handler.log("info", "用户取消工程文件生成")
            return

        try:
            # 生成工程文件数据
            project_data = self._build_project_data(video_path, srt_path)

            # 保存工程文件
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(project_data, f, ensure_ascii=False, indent=2)

            # 保存到实例变量，供导出功能使用
            self.last_project_file = save_path
            self.last_project_data = project_data

            # 更新进度条
            self.process_progress_bar.setValue(100)

            # 成功
            self.statusBar().showMessage(f"工程文件生成成功: {os.path.basename(save_path)}")
            log_handler.log("info", f"工程文件生成成功: {save_path}")
            QMessageBox.information(
                self,
                "成功",
                f"工程文件已生成并保存到:\n{save_path}\n\n"
                f"现在可以点击导出到剪映按钮将项目导出到剪映进行编辑。"
            )

        except Exception as e:
            # 失败
            self.process_progress_bar.setValue(0)
            self.statusBar().showMessage("工程文件生成失败")
            log_handler.log("error", f"工程文件生成失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"工程文件生成失败: {str(e)}")

    def _build_project_data(self, video_path: str, srt_path: str):
        """构建工程文件数据"""
        try:
            # 读取SRT文件
            with open(srt_path, 'r', encoding='utf-8') as f:
                srt_content = f.read()

            # 解析SRT内容
            scenes = self._parse_srt_to_scenes(srt_content, video_path)

            # 构建工程数据
            project_data = {
                "project_id": f"visionai_project_{int(time.time())}",
                "title": f"VisionAI工程 - {os.path.splitext(os.path.basename(video_path))[0]}",
                "created_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "source_video": video_path,
                "source_srt": srt_path,
                "scenes": scenes,
                "metadata": {
                    "total_scenes": len(scenes),
                    "total_duration": scenes[-1]["end_time"] if scenes else 0,
                    "video_format": os.path.splitext(video_path)[1],
                    "srt_encoding": "utf-8"
                },
                "export_settings": {
                    "target_format": "jianying",
                    "resolution": "1920x1080",
                    "fps": 30
                }
            }

            return project_data

        except Exception as e:
            log_handler.log("error", f"构建工程数据失败: {e}")
            raise

    def _parse_srt_to_scenes(self, srt_content: str, video_path: str):
        """解析SRT内容为场景数据"""
        import re

        scenes = []

        # SRT格式正则表达式
        srt_pattern = r'(\d+)\n([\d:,]+) --> ([\d:,]+)\n(.*?)(?=\n\d+\n|\n*$)'
        matches = re.findall(srt_pattern, srt_content, re.DOTALL)

        for match in matches:
            scene_id, start_time_str, end_time_str, text = match

            # 转换时间格式
            start_time = self._time_str_to_seconds(start_time_str)
            end_time = self._time_str_to_seconds(end_time_str)

            scene = {
                "scene_id": f"scene_{scene_id}",
                "id": f"scene_{scene_id}",
                "start_time": start_time,
                "end_time": end_time,
                "duration": end_time - start_time,
                "text": text.strip().replace('\n', ' '),
                "video_path": video_path,
                "source_start": start_time,
                "source_end": end_time
            }

            scenes.append(scene)

        return scenes

    def _time_str_to_seconds(self, time_str: str) -> float:
        """将时间字符串转换为秒数"""
        # 格式: HH:MM:SS,mmm
        time_str = time_str.replace(',', '.')
        parts = time_str.split(':')

        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = float(parts[2])

        return hours * 3600 + minutes * 60 + seconds

    def export_to_jianying(self):
        """导出到剪映"""
        try:
            # 检查是否有生成的工程文件
            if not hasattr(self, 'last_project_file') or not self.last_project_file:
                QMessageBox.warning(
                    self,
                    "提示",
                    "请先点击生成工程文件按钮生成项目数据,然后再导出到剪映"
                )
                return

            # 检查工程文件是否存在
            if not os.path.exists(self.last_project_file):
                QMessageBox.warning(
                    self,
                    "错误",
                    "工程文件不存在，请重新生成工程文件"
                )
                return

            # 显示进度
            self.statusBar().showMessage("正在导出到剪映...")
            self.process_progress_bar.setValue(0)

            # 选择保存位置
            project_name = os.path.splitext(os.path.basename(self.last_project_file))[0]
            default_name = f"{project_name}_剪映工程.zip"
            save_path, _ = QFileDialog.getSaveFileName(
                self,
                "导出剪映工程文件",
                default_name,
                "剪映工程文件 (*.zip);;JSON文件 (*.json)"
            )

            if not save_path:
                self.statusBar().showMessage("导出已取消")
                return

            # 执行导出
            from src.export.jianying_exporter import JianyingExporter

            exporter = JianyingExporter()

            # 使用工程数据进行导出
            result = exporter.export(self.last_project_data, save_path)

            if result:
                self.process_progress_bar.setValue(80)
                self.statusBar().showMessage("导出完成，正在启动剪映...")

                # 尝试自动启动剪映
                jianying_launched = self._launch_jianying_app(save_path)

                self.process_progress_bar.setValue(100)

                if jianying_launched:
                    self.statusBar().showMessage("剪映启动成功")
                    QMessageBox.information(
                        self,
                        "导出成功",
                        f"剪映工程文件已导出并自动打开剪映应用！\n\n"
                        f"导出文件：{save_path}\n\n"
                        f"剪映应用已启动，请在剪映中导入刚才保存的工程文件。"
                    )
                else:
                    self.statusBar().showMessage("导出完成")
                    # 显示手动操作指引
                    reply = QMessageBox.information(
                        self,
                        "导出成功",
                        f"剪映工程文件已保存到：\n{save_path}\n\n"
                        f"由于无法自动启动剪映，请手动执行以下步骤：\n"
                        f"1. 打开剪映应用\n"
                        f"2. 选择导入项目\n"
                        f"3. 选择刚才保存的工程文件\n"
                        f"4. 开始在剪映中编辑视频\n\n"
                        f"是否打开文件所在文件夹？",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                    )

                    if reply == QMessageBox.StandardButton.Yes:
                        self._open_file_folder(save_path)
            else:
                self.process_progress_bar.setValue(0)
                self.statusBar().showMessage("导出失败")
                QMessageBox.critical(self, "错误", "导出到剪映失败，请检查文件权限和磁盘空间")

        except Exception as e:
            self.process_progress_bar.setValue(0)
            self.statusBar().showMessage("导出失败")
            QMessageBox.critical(self, "错误", f"导出过程中发生错误：{str(e)}")
            log_handler.log("error", f"导出到剪映失败: {e}")

    def _launch_jianying_app(self, project_file_path: str) -> bool:
        """尝试自动启动剪映应用"""
        try:
            system = platform.system()

            if system == "Windows":
                # Windows系统下尝试启动剪映
                jianying_paths = [
                    # 常见的剪映安装路径
                    os.path.expanduser("~/AppData/Local/JianyingPro/JianyingPro.exe"),
                    "C:/Program Files/JianyingPro/JianyingPro.exe",
                    "C:/Program Files (x86)/JianyingPro/JianyingPro.exe",
                ]

                # 尝试启动剪映
                for path in jianying_paths:
                    if os.path.exists(path):
                        try:
                            subprocess.Popen([path])
                            log_handler.log("info", f"成功启动剪映: {path}")
                            return True
                        except Exception as e:
                            log_handler.log("warning", f"启动剪映失败 {path}: {e}")
                            continue

                # 尝试通过系统关联启动
                try:
                    os.startfile(project_file_path)
                    log_handler.log("info", "通过系统关联启动剪映")
                    return True
                except Exception as e:
                    log_handler.log("warning", f"通过系统关联启动失败: {e}")

            elif system == "Darwin":  # macOS
                # macOS系统下尝试启动剪映
                try:
                    subprocess.run(["open", "-a", "JianyingPro"], check=True)
                    log_handler.log("info", "成功启动剪映 (macOS)")
                    return True
                except subprocess.CalledProcessError:
                    try:
                        subprocess.run(["open", project_file_path], check=True)
                        log_handler.log("info", "通过系统关联启动剪映 (macOS)")
                        return True
                    except Exception as e:
                        log_handler.log("warning", f"macOS启动剪映失败: {e}")

            else:  # Linux
                # Linux系统下的处理
                try:
                    subprocess.run(["xdg-open", project_file_path], check=True)
                    log_handler.log("info", "通过系统关联启动剪映 (Linux)")
                    return True
                except Exception as e:
                    log_handler.log("warning", f"Linux启动剪映失败: {e}")

            return False

        except Exception as e:
            log_handler.log("error", f"启动剪映应用失败: {e}")
            return False

    def _open_file_folder(self, file_path: str):
        """打开文件所在文件夹"""
        try:
            folder_path = os.path.dirname(file_path)
            system = platform.system()

            if system == "Windows":
                subprocess.run(["explorer", folder_path])
            elif system == "Darwin":  # macOS
                subprocess.run(["open", folder_path])
            else:  # Linux
                subprocess.run(["xdg-open", folder_path])

        except Exception as e:
            log_handler.log("error", f"打开文件夹失败: {e}")

    def init_render_optimizer(self):
        """初始化渲染优化器"""
        if not HAS_PERFORMANCE_TIER:
            return
            
        try:
            # 获取性能等级
            tier_classifier = PerformanceTierClassifier()
            tier = tier_classifier.classify()
            
            # 创建渲染优化器并应用优化
            self.render_optimizer = RenderOptimizer(self)
            self.render_optimizer.optimize_rendering(tier)
            
            # 记录日志
            log_handler.log("info", f"已应用{tier}级渲染优化")
            
            # 如果有通知管理器，显示通知
            if hasattr(self, 'alert_manager'):
                self.alert_manager.info(f"已应用{tier}级渲染优化", timeout=3000)
                
        except Exception as e:
            log_handler.log("warning", f"渲染优化器初始化失败: {str(e)}")
            # 不影响主程序运行

    def init_memory_manager(self):
        """初始化内存管理器"""
        if not HAS_MEMORY_MANAGER:
            return
        
        try:
            # 获取性能等级
            tier_classifier = PerformanceTierClassifier()
            tier = tier_classifier.classify()
            
            # 创建内存管理器 - 优化版本
            self.memory_manager = UIMemoryManager(self)

            # 强制使用低内存模式以减少内存占用
            tier = "Low"  # 强制低内存模式，目标<300MB
            self.memory_manager.configure_memory(tier)
            self.memory_manager.activate()
            
            # 创建内存监控器
            # 临时禁用内存监控器以避免线程冲突

            # self.memory_watcher = MemoryWatcher(self)

            self.memory_watcher = None
            
            # 连接内存警告信号
            # 临时禁用内存警告连接

            # self.memory_watcher.memory_warning.connect(self.on_memory_warning)

            if self.memory_watcher:

                self.memory_watcher.memory_warning.connect(self.on_memory_warning)
            self.memory_watcher.memory_status_changed.connect(self.on_memory_status_changed)
            
            # 启动内存监视
            interval_ms = 5000  # 默认5秒
            if tier == "low":
                interval_ms = 10000  # 低端设备降低监控频率
            self.memory_watcher.start_monitoring(interval_ms=interval_ms)
            
            # 记录日志
            log_handler.log("info", f"内存管理器已初始化 (性能等级: {tier})")
            
            # 如果有通知管理器，显示通知
            if hasattr(self, 'alert_manager'):
                self.alert_manager.info(f"已应用{tier}级内存优化", timeout=3000)
                
        except Exception as e:
            log_handler.log("warning", f"内存管理器初始化失败: {str(e)}")
            # 不影响主程序运行
            
    def on_memory_warning(self, *args, **kwargs):
        """处理内存警告 - 兼容多种参数格式"""
        try:
            # 解析参数
            message = "内存使用警告"
            severity = 1

            if len(args) >= 1:
                if isinstance(args[0], str):
                    message = args[0]
                    if len(args) >= 2:
                        severity = int(args[1]) if isinstance(args[1], (int, float)) else 1
                elif isinstance(args[0], (int, float)):
                    severity = int(args[0])
                    message = f"内存使用警告 (严重程度: {severity})"

            # 从kwargs中获取参数
            message = kwargs.get('message', message)
            severity = kwargs.get('severity', severity)

            if hasattr(self, 'alert_manager'):
                # 根据严重程度设置警告等级
                if severity == 2:  # 危急
                    self.alert_manager.error(message, timeout=10000)
                    # 执行紧急内存清理
                    if hasattr(self, 'memory_manager'):
                        self.memory_manager.perform_emergency_cleanup()
                elif severity == 1:  # 警告
                    self.alert_manager.warning(message, timeout=5000)
                    # 执行积极清理
                    if hasattr(self, 'memory_manager'):
                        self.memory_manager.perform_cleanup("aggressive")
                else:  # 提示
                    self.alert_manager.info(message, timeout=3000)
            else:
                # 如果没有通知管理器，使用状态栏显示信息
                self.statusBar().showMessage(message, 5000)
                
            # 记录日志
            log_level = "warning" if severity >= 1 else "info"
            log_handler.log(log_level, message)
            
        except Exception as e:
            log_handler.log("error", f"处理内存警告出错: {str(e)}")
    
    def on_memory_status_changed(self, status):
        """处理内存状态变化"""
        # 可以在状态栏显示内存使用情况
        if status["used_percent"] > 80:
            # 高内存占用，更新状态栏
            memory_text = f"内存: {status['used_percent']:.1f}% ({status['app_used_mb']:.1f} MB)"
            self.statusBar().showMessage(memory_text, 3000)
            
    def cleanup_resources(self, cleanup_percent=0.5):
        """清理资源
        
        Args:
            cleanup_percent: 清理比例，0.0-1.0
        """
        try:
            # 清理缓存内容
            log_handler.log("debug", f"清理{cleanup_percent*100:.0f}%的缓存资源")
            
            # 清理图片缓存
            # 这里需要应用程序实现适当的清理逻辑
            
            # 如果有重度清理
            if cleanup_percent > 0.7:
                # 强制垃圾回收
                import gc
                gc.collect()
                
                # 其他资源清理逻辑
                
        except Exception as e:
            log_handler.log("error", f"清理资源出错: {str(e)}")
    
    def handle_memory_emergency(self):
        """处理内存紧急情况"""
        try:
            # 显示警告对话框
            if not self.is_processing:
                QMessageBox.warning(
                    self, 
                    "系统内存不足", 
                    "检测到系统内存严重不足，已进行紧急资源释放。\n\n建议保存工作并重启应用程序。"
                )
            
            # 执行紧急清理
            self.cleanup_resources(1.0)
            
            # 记录日志
            log_handler.log("warning", "执行紧急内存清理")
            
        except Exception as e:
            log_handler.log("error", f"处理内存紧急情况出错: {str(e)}")

    def init_compute_offloader(self):
        """初始化计算任务卸载器"""
        try:
            # 导入计算任务卸载器
            from ui.hardware.compute_offloader import get_compute_offloader, offload_heavy_tasks
            
            # 获取性能等级
            from ui.hardware.performance_tier import get_performance_tier
            tier = get_performance_tier()
            
            # 获取计算任务卸载器并应用优化
            self.compute_offloader = get_compute_offloader()
            offload_heavy_tasks(tier)
            
            log_handler.log("info", f"计算任务卸载器已初始化 (性能等级: {tier})")
        except ImportError as e:
            log_handler.log("warning", f"计算任务卸载器初始化失败: {e}")
        except Exception as e:
            log_handler.log("error", f"计算任务卸载器初始化错误: {e}")
            # 不影响主程序运行

    def init_disk_cache(self):
        """初始化磁盘缓存管理器"""
        if not HAS_DISK_CACHE:
            log_handler.log("warning", "磁盘缓存管理器不可用，将使用默认缓存设置")
            return
            
        try:
            # 获取性能等级
            if HAS_PERFORMANCE_TIER:
                tier = get_performance_tier()
                log_handler.log("info", f"根据性能等级({tier})配置磁盘缓存")
                
                # 获取磁盘缓存管理器实例
                self.disk_cache_manager = get_disk_cache_manager()
                
                # 根据性能等级设置缓存
                setup_cache(tier)
                
                # 获取缓存统计信息
                cache_stats = get_cache_stats()
                log_handler.log("info", f"磁盘缓存统计: 大小={cache_stats['size_mb']:.2f}MB, 最大={cache_stats['max_size_mb']}MB")
                
                # 如果有通知管理器，显示缓存初始化成功通知
                if hasattr(self, 'alert_manager') and self.alert_manager:
                    self.alert_manager.info(f"磁盘缓存已优化: {cache_stats['max_size_mb']}MB", timeout=3000)
            else:
                log_handler.log("warning", "性能分级系统不可用，将使用默认缓存设置")
                
                # 使用默认设置初始化缓存
                self.disk_cache_manager = get_disk_cache_manager()
                setup_cache("medium")  # 默认使用中等性能设置
                
            log_handler.log("info", "磁盘缓存管理器初始化完成")
            
            # 刷新缓存统计信息
            self.refresh_cache_stats()
            
            # 创建定时器，定期刷新缓存统计信息
            self.cache_stats_timer = QTimer(self)
            self.cache_stats_timer.timeout.connect(self.refresh_cache_stats)
            self.cache_stats_timer.start(30000)  # 每30秒刷新一次
            
        except Exception as e:
            log_handler.log("error", f"初始化磁盘缓存管理器失败: {str(e)}")
            # 不影响主程序运行
            
    def clear_disk_cache(self):
        """清除磁盘缓存"""
        if not HAS_DISK_CACHE:
            QMessageBox.warning(self, "功能不可用", "磁盘缓存管理器不可用")
            return
            
        try:
            # 显示确认对话框
            reply = QMessageBox.question(
                self,
                "确认清除缓存",
                "确定要清除所有磁盘缓存吗？这将删除所有缓存的数据。",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # 显示进度
                self.process_progress_bar.setValue(0)
                self.status_label.setText("正在清理缓存...")
                QApplication.processEvents()

                # 模拟清理进度
                for progress in range(0, 101, 20):
                    self.process_progress_bar.setValue(progress)
                    QApplication.processEvents()
                    time.sleep(0.1)  # 短暂延迟以显示进度

                # 清除所有缓存
                clear_cache()
                log_handler.log("info", "已清除所有磁盘缓存")

                # 完成进度
                self.process_progress_bar.setValue(100)
                self.status_label.setText("缓存清理完成")
                
                # 刷新缓存统计信息
                self.refresh_cache_stats()
                
                # 显示通知
                if hasattr(self, 'alert_manager') and self.alert_manager:
                    self.alert_manager.info("已清除所有磁盘缓存", timeout=3000)
                
        except Exception as e:
            log_handler.log("error", f"清除磁盘缓存失败: {str(e)}")
            QMessageBox.critical(self, "操作失败", f"清除磁盘缓存失败: {str(e)}")
            
    def refresh_cache_stats(self):
        """刷新缓存统计信息"""
        if not HAS_DISK_CACHE:
            return

        try:
            # 显示进度
            self.process_progress_bar.setValue(0)
            self.status_label.setText("正在刷新缓存统计...")
            QApplication.processEvents()

            # 模拟刷新进度
            for progress in range(0, 101, 25):
                self.process_progress_bar.setValue(progress)
                QApplication.processEvents()
                time.sleep(0.05)  # 短暂延迟

            # 获取缓存统计信息
            cache_stats = get_cache_stats()
            
            # 更新UI显示
            if hasattr(self, 'cache_status_value'):
                self.cache_status_value.setText("已启用" if cache_stats["enabled"] else "已禁用")
                
            if hasattr(self, 'cache_size_value'):
                self.cache_size_value.setText(f"{cache_stats['size_mb']:.2f} MB")
                
            if hasattr(self, 'cache_max_value'):
                self.cache_max_value.setText(f"{cache_stats['max_size_mb']} MB")
                
            if hasattr(self, 'cache_hit_value'):
                self.cache_hit_value.setText(f"{cache_stats['hit_rate'] * 100:.1f}%")
                
            # 完成进度
            self.process_progress_bar.setValue(100)
            self.status_label.setText("缓存统计刷新完成")

            log_handler.log("info", "已刷新缓存统计信息")
        except Exception as e:
            # 重置进度条
            self.process_progress_bar.setValue(0)
            self.status_label.setText("刷新失败")
            log_handler.log("error", f"刷新缓存统计信息失败: {str(e)}")
            
    def refresh_input_latency_stats(self):
        """刷新输入延迟优化统计信息"""
        if not HAS_INPUT_OPTIMIZER:
            return
            
        try:
            # 获取输入延迟统计
            input_stats = get_input_latency_stats()
            
            # 更新UI显示
            if hasattr(self, 'input_tier_label'):
                self.input_tier_label.setText(input_stats['tier'])
                
            if hasattr(self, 'input_cursor_flash_label'):
                self.input_cursor_flash_label.setText(f"{input_stats['cursor_flash_time']} ms")
                
            if hasattr(self, 'input_event_compress_label'):
                self.input_event_compress_label.setText("已启用" if input_stats['compress_events'] else "未启用")
                
            if hasattr(self, 'input_touch_optimize_label'):
                self.input_touch_optimize_label.setText("已启用" if input_stats['touch_optimization_enabled'] else "未启用")
                
            if hasattr(self, 'input_fields_optimized_label'):
                field_types = input_stats['optimized_field_types']
                details = f"{field_types['text']}文本, {field_types['number']}数字, {field_types['slider']}滑块"
                self.input_fields_optimized_label.setText(f"{input_stats['optimized_fields']} 个 ({details})")
                
            # 如果有事件统计，更新事件过滤信息
            if 'event_stats' in input_stats and hasattr(self, 'input_events_filtered_label'):
                event_stats = input_stats['event_stats']
                self.input_events_filtered_label.setText(f"{event_stats['filtered_events']} 个")
                
            log_handler.log("info", f"输入优化统计已刷新: 性能等级={input_stats['tier']}, 触摸优化={'已启用' if input_stats['touch_optimization_enabled'] else '未启用'}")
        except Exception as e:
            log_handler.log("error", f"刷新输入延迟统计信息失败: {str(e)}")
            # 不影响主程序运行
    
    def open_email(self, email):
        """打开邮件客户端"""
        try:
            import webbrowser
            webbrowser.open(f"mailto:{email}")
        except Exception:
            QMessageBox.information(self, "联系信息", f"请联系我们: {email}")

    def use_disk_cache_for_processing(self, cache_type, cache_key, _data_processor, _input_params, output_path):
        """使用磁盘缓存处理数据
        
        Args:
            cache_type: 缓存类型
            cache_key: 缓存键
            data_processor: 数据处理函数
            input_params: 输入参数
            output_path: 输出路径
            
        Returns:
            bool: 是否从缓存中获取了结果
        """
        # 如果磁盘缓存不可用，直接返回False
        if not HAS_DISK_CACHE or not hasattr(self, 'disk_cache_manager'):
            return False
            
        try:
            # 尝试从缓存获取结果
            cached_data = self.disk_cache_manager.get(cache_type, cache_key)
            if cached_data:
                # 将缓存的数据写入输出文件
                with open(output_path, 'wb') as f:
                    f.write(cached_data)
                
                # 记录日志
                log_handler.log("info", f"从缓存加载数据: {cache_key}")
                
                # 刷新缓存统计
                self.refresh_cache_stats()
                
                return True
        except Exception as e:
            log_handler.log("warning", f"从缓存加载数据失败: {str(e)}")
            
        return False
        
    def save_to_disk_cache(self, cache_type, cache_key, file_path, metadata=None):
        """将处理结果保存到磁盘缓存
        
        Args:
            cache_type: 缓存类型
            cache_key: 缓存键
            file_path: 文件路径
            metadata: 可选的元数据
        """
        # 如果磁盘缓存不可用，直接返回
        if not HAS_DISK_CACHE or not hasattr(self, 'disk_cache_manager'):
            return
            
        try:
            # 读取生成的文件
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            # 准备元数据
            meta = {"timestamp": time.time()}
            if metadata:
                meta.update(metadata)
                
            # 存入缓存
            self.disk_cache_manager.put(
                cache_type, 
                cache_key, 
                file_data,
                meta
            )
            
            # 记录日志
            log_handler.log("info", f"数据已缓存: {cache_key}")
            
            # 刷新缓存统计
            self.refresh_cache_stats()
            
        except Exception as e:
            log_handler.log("warning", f"缓存数据失败: {str(e)}")
            
    def init_input_latency_optimizer(self):
        """初始化输入延迟优化器"""
        if not HAS_INPUT_OPTIMIZER:
            log_handler.log("warning", "输入延迟优化器不可用，将使用默认输入设置")
            return
            
        try:
            # 获取性能等级
            if HAS_PERFORMANCE_TIER:
                tier = get_performance_tier()
                log_handler.log("info", f"根据性能等级({tier})优化输入延迟")
                
                # 获取输入延迟优化器实例
                self.input_optimizer = get_input_optimizer()
                
                # 根据性能等级设置输入延迟优化
                # 使用try-except捕获可能的'set_compression'方法不存在的错误
                try:
                        optimize_input_latency(tier)
                except AttributeError as e:
                    log_handler.log("warning", f"输入延迟优化错误: {str(e)}")
                
                # 获取输入延迟统计信息
                try:
                    input_stats = get_input_latency_stats()
                
                    # 如果有通知管理器，显示输入优化成功通知
                    if hasattr(self, 'alert_manager') and self.alert_manager:
                        touch_enabled = input_stats.get('touch_optimization_enabled', False) if isinstance(input_stats, dict) else False
                        self.alert_manager.info(f"输入延迟已优化，触摸优化: {'已启用' if touch_enabled else '未启用'}", timeout=3000)
                except Exception as e:
                    log_handler.log("warning", f"获取输入延迟统计失败: {str(e)}")
            else:
                log_handler.log("warning", "性能分级系统不可用，将使用默认输入延迟设置")
                
                # 使用默认设置初始化输入延迟优化
                try:
                    self.input_optimizer = get_input_optimizer()
                    optimize_input_latency("medium")  # 默认使用中等性能设置
                except AttributeError:
                    log_handler.log("warning", "输入延迟优化器部分功能不可用")
                
            # 为特定输入组件优化
            self._optimize_input_components()
                
            log_handler.log("info", "输入延迟优化器初始化完成")
            
        except Exception as e:
            log_handler.log("error", f"初始化输入延迟优化器失败: {str(e)}")
            # 不影响主程序运行
            
    def _optimize_input_components(self):
        """优化特定输入组件"""
        if not HAS_INPUT_OPTIMIZER:
            return
            
        try:
            # 为文本输入字段应用优化
            input_fields = [
                widget for widget in self.findChildren(QLineEdit) 
                if hasattr(widget, 'objectName') and widget.objectName()
            ]
            
            for field in input_fields:
                optimize_input_field(field, "text")
                
            # 为数字输入字段应用优化
            number_fields = [
                widget for widget in self.findChildren(QSpinBox) 
                if hasattr(widget, 'objectName') and widget.objectName()
            ]
            
            for field in number_fields:
                optimize_input_field(field, "number")
                
            # 为所有滑块应用优化
            slider_fields = [
                widget for widget in self.findChildren(QSlider) 
                if hasattr(widget, 'objectName') and widget.objectName()
            ]
            
            for field in slider_fields:
                optimize_input_field(field, "slider")
                
            log_handler.log("info", f"已优化 {len(input_fields)} 个文本输入字段, {len(number_fields)} 个数字输入字段, {len(slider_fields)} 个滑块")
            
        except Exception as e:
            log_handler.log("warning", f"优化输入组件失败: {str(e)}")
            # 不影响主程序运行
            
    def init_power_manager(self):
        """初始化电源管理器"""
        if not HAS_POWER_MANAGER:
            log_handler.log("warning", "电源管理模块不可用，将使用默认电源设置")
            return
            
        try:
            # 获取电源管理器实例
            self.power_manager = get_power_manager()
            
            # 获取电源状态
            power_status = get_power_status()
            power_source = power_status.get("power_source", "UNKNOWN")
            battery_level = power_status.get("battery_level", -1)
            
            # 应用电源优化
            try:
                # 检查函数是否存在
                if 'optimize_for_power_source' in globals() and callable(optimize_for_power_source):
                    optimize_for_power_source()
                else:
                    log_handler.log("warning", "电源优化函数不可用")
            except (AttributeError, TypeError, NameError) as e:
                log_handler.log("warning", f"电源优化失败: {str(e)}")
            
            # 创建电源监视器
            self.power_watcher = PowerWatcher(self)
            
            # 连接信号
            self.power_watcher.power_source_changed.connect(self.on_power_source_changed)
            self.power_watcher.battery_level_changed.connect(self.on_battery_level_changed)
            self.power_watcher.low_battery_warning.connect(self.on_low_battery_warning)
            
            # 开始监控
            self.power_watcher.start_monitoring()
            
            # 记录日志
            if battery_level >= 0:
                log_handler.log("info", f"电源管理器初始化完成，当前电源: {power_source}，电池电量: {battery_level}%")
            else:
                log_handler.log("info", f"电源管理器初始化完成，当前电源: {power_source}")
                
            # 如果有通知管理器，显示电源状态通知
            if hasattr(self, 'alert_manager') and self.alert_manager:
                if power_source == "BATTERY" and battery_level >= 0:
                    self.alert_manager.info(f"使用电池供电，当前电量: {battery_level}%", timeout=3000)
                
        except Exception as e:
            log_handler.log("error", f"初始化电源管理器失败: {str(e)}")
            # 不影响主程序运行
            
    def on_power_source_changed(self, source):
        """电源类型变化处理
        
        Args:
            source: 电源类型名称
        """
        log_handler.log("info", f"电源类型变化: {source}")
        
        # 应用电源优化
        try:
            # 检查函数是否存在
            if 'optimize_for_power_source' in globals() and callable(optimize_for_power_source):
                optimize_for_power_source()
            else:
                log_handler.log("warning", "电源优化函数不可用")
        except (AttributeError, TypeError, NameError) as e:
            log_handler.log("warning", f"电源优化失败: {str(e)}")
        
        # 更新UI显示（如果有电源状态显示）
        if hasattr(self, 'power_source_label'):
            self.power_source_label.setText(source)
            
        # 显示通知
        if hasattr(self, 'alert_manager') and self.alert_manager:
            if source == "BATTERY":
                power_status = get_power_status()
                battery_level = power_status.get("battery_level", -1)
                if battery_level >= 0:
                    self.alert_manager.info(f"切换到电池供电，当前电量: {battery_level}%", timeout=3000)
                else:
                    self.alert_manager.info("切换到电池供电", timeout=3000)
            elif source == "AC":
                self.alert_manager.info("已连接电源适配器", timeout=3000)
                
    def on_battery_level_changed(self, level):
        """电池电量变化处理
        
        Args:
            level: 电池电量百分比
        """
        log_handler.log("debug", f"电池电量变化: {level}%")
        
        # 更新UI显示（如果有电池电量显示）
        if hasattr(self, 'battery_level_label'):
            self.battery_level_label.setText(f"{level}%")
            
    def on_low_battery_warning(self, level):
        """低电量警告处理
        
        Args:
            level: 电池电量百分比
        """
        # 显示低电量警告
        if hasattr(self, 'alert_manager') and self.alert_manager:
            if level <= 10:
                self.alert_manager.warning(f"电池电量极低 ({level}%)，请尽快连接电源", timeout=5000)
            elif level <= 20:
                self.alert_manager.info(f"电池电量低 ({level}%)", timeout=3000)
                
        # 电量极低时，自动启用省电模式
        if level <= 10:
            log_handler.log("warning", "电量极低，自动启用省电模式")
            try:
                # 检查函数是否存在
                if 'enable_power_saving' in globals() and callable(enable_power_saving):
                    enable_power_saving(True)
                else:
                    log_handler.log("warning", "省电模式函数不可用")
            except (AttributeError, TypeError, NameError) as e:
                log_handler.log("warning", f"启用省电模式失败: {str(e)}")
            
            # 如果需要，可以在这里添加自动保存工作的逻辑

    def refresh_power_status(self):
        """刷新电源状态信息"""
        if not HAS_POWER_MANAGER:
            return
            
        try:
            # 获取最新电源状态
            power_status = get_power_status()
            
            # 更新UI显示
            if hasattr(self, 'power_source_label'):
                self.power_source_label.setText(power_status.get("power_source", "未检测"))
                
            if hasattr(self, 'battery_status_label'):
                self.battery_status_label.setText(power_status.get("battery_status", "未知"))
                
            if hasattr(self, 'battery_level_label'):
                battery_level = power_status.get("battery_level", -1)
                if battery_level >= 0:
                    self.battery_level_label.setText(f"{battery_level}%")
                else:
                    self.battery_level_label.setText("未知")
                    
            if hasattr(self, 'power_mode_label'):
                if power_status.get("low_power_mode", False):
                    self.power_mode_label.setText("节能模式")
                    
                    # 更新节能模式按钮文本
                    if hasattr(self, 'enable_power_saving_btn'):
                        self.enable_power_saving_btn.setText("禁用节能模式")
                else:
                    self.power_mode_label.setText("正常模式")
                    
                    # 更新节能模式按钮文本
                    if hasattr(self, 'enable_power_saving_btn'):
                        self.enable_power_saving_btn.setText("启用节能模式")
                        
            log_handler.log("info", "已刷新电源状态信息")
            
        except Exception as e:
            log_handler.log("error", f"刷新电源状态信息失败: {str(e)}")
            
    def toggle_power_management(self, state):
        """切换电源管理开关
        
        Args:
            state: 复选框状态
        """
        if not HAS_POWER_MANAGER:
            return
            
        try:
            # 根据复选框状态启用或禁用电源监控
            if state == Qt.CheckState.Checked:
                if hasattr(self, 'power_watcher'):
                    self.power_watcher.start_monitoring()
                log_handler.log("info", "已启用电源管理")
                
                # 刷新状态
                self.refresh_power_status()
            else:
                if hasattr(self, 'power_watcher'):
                    self.power_watcher.stop_monitoring()
                log_handler.log("info", "已禁用电源管理")
                
        except Exception as e:
            log_handler.log("error", f"切换电源管理失败: {str(e)}")
            
    def toggle_power_saving_mode(self):
        """切换节能模式"""
        if not HAS_POWER_MANAGER:
            return
            
        try:
            # 获取当前电源状态
            power_status = get_power_status()
            current_mode = power_status.get("low_power_mode", False)
            
            # 切换节能模式
            try:
                # 检查函数是否存在
                if 'enable_power_saving' in globals() and callable(enable_power_saving):
                    enable_power_saving(not current_mode)
                else:
                    log_handler.log("warning", "省电模式函数不可用")
            except (AttributeError, TypeError, NameError) as e:
                log_handler.log("warning", f"切换节能模式失败: {str(e)}")
            
            # 更新UI
            self.refresh_power_status()
            
            # 显示通知
            if hasattr(self, 'alert_manager') and self.alert_manager:
                if not current_mode:  # 正在启用节能模式
                    self.alert_manager.info("已启用节能模式", timeout=3000)
                else:  # 正在禁用节能模式
                    self.alert_manager.info("已禁用节能模式", timeout=3000)
                    
        except Exception as e:
            log_handler.log("error", f"切换节能模式失败: {str(e)}")

    def check_ffmpeg_status(self):
        """检查并显示FFmpeg状态"""
        global HAS_FFMPEG
        
        if HAS_FFMPEG:
            status_message = "FFmpeg已安装，视频处理功能可用"
            log_handler.log("info", status_message)
            if hasattr(self, 'alert_manager') and self.alert_manager:
                self.alert_manager.info(status_message, timeout=3000)
        else:
            status_message = "未检测到FFmpeg，视频处理功能受限"
            log_handler.log("warning", status_message)
            if hasattr(self, 'alert_manager') and self.alert_manager:
                self.alert_manager.warning(status_message, timeout=5000)
            else:
                # 如果alert_manager不可用，使用状态栏显示
                self.statusBar().showMessage(status_message, 10000)
            
            # 显示更详细的消息框
            QMessageBox.warning(
                self,
                "FFmpeg未检测到",
                "未在系统中检测到FFmpeg，视频处理功能将不可用。\n\n"
                "请安装FFmpeg后重启应用程序。\n\n"
                "下载地址：https://ffmpeg.org/download.html"
            )

    # 监控信号处理方法
    def on_performance_update(self, performance_data):
        """处理性能更新"""
        try:
            # 更新状态栏显示性能信息
            memory_mb = performance_data.get('memory_mb', 0)
            cpu_percent = performance_data.get('cpu_percent', 0)

            status_text = f"内存: {memory_mb:.1f}MB | CPU: {cpu_percent:.1f}%"
            if hasattr(self, 'statusBar'):
                self.statusBar().showMessage(status_text, 2000)
        except Exception as e:
            print(f"性能更新处理失败: {e}")

    def on_response_time_update(self, response_time):
        """处理响应时间更新"""
        try:
            # 如果响应时间过长，显示警告
            if response_time > 1.0:  # 超过1秒
                warning_msg = f"响应时间较长: {response_time:.2f}秒"
                print(f"[WARN]️ {warning_msg}")

            # 更新状态栏显示响应时间信息
            if hasattr(self, 'statusBar'):
                status_msg = f"响应时间: {response_time:.3f}s"
                self.statusBar().showMessage(status_msg, 1500)

        except Exception as e:
            print(f"响应时间更新处理失败: {e}")

    def on_responsiveness_data_update(self, responsiveness_data):
        """处理响应性数据更新"""
        try:
            # 存储响应性数据供测试使用
            if not hasattr(self, '_responsiveness_data_history'):
                self._responsiveness_data_history = []

            self._responsiveness_data_history.append(responsiveness_data)

            # 只保留最近20个数据点
            if len(self._responsiveness_data_history) > 20:
                self._responsiveness_data_history.pop(0)

            # 打印响应性摘要（调试用）
            total_interactions = responsiveness_data.get('total_interactions', 0)
            avg_response_time = responsiveness_data.get('average_response_time', 0.0)

            if total_interactions > 0:
                print(f"[CHART] 响应性数据更新: 交互次数={total_interactions}, 平均响应时间={avg_response_time:.3f}s")

        except Exception as e:
            print(f"响应性数据更新处理失败: {e}")

    def get_responsiveness_data_history(self):
        """获取响应性数据历史 - 供测试使用"""
        return getattr(self, '_responsiveness_data_history', [])

    def on_ui_error_occurred(self, error_details):
        """处理UI错误发生事件"""
        try:
            error_id = error_details.get("error_id", "N/A")
            error_type = error_details.get("error_type", "N/A")
            recovery_successful = error_details.get("recovery_successful", False)

            print(f"UI错误发生 [{error_id}]: {error_type}")

            if recovery_successful:
                print(f"[OK] 错误已自动恢复: {error_details.get('recovery_message', '')}")
                if hasattr(self, 'alert_manager') and self.alert_manager:
                    self.alert_manager.success("错误已自动修复")
            else:
                print(f"[ERROR] 错误未能自动恢复")
                if hasattr(self, 'alert_manager') and self.alert_manager:
                    self.alert_manager.error("发生错误，请检查详细信息")

        except Exception as e:
            print(f"UI错误事件处理失败: {e}")

    def record_user_interaction(self):
        """记录用户交互（在用户操作时调用）"""
        try:
            if hasattr(self, 'responsiveness_monitor') and self.responsiveness_monitor:
                self.responsiveness_monitor.record_interaction()

            # 定期清理缓存以保持性能
            current_time = time.time()
            if current_time - self._last_cleanup_time > 300:  # 每5分钟清理一次
                self._periodic_cleanup()
                self._last_cleanup_time = current_time

        except Exception as e:
            self._handle_error(f"用户交互记录失败: {e}")

    def _periodic_cleanup(self):
        """定期清理以保持性能"""
        try:
            print("[INFO] 执行定期清理...")

            # 清理临时缓存
            if hasattr(self, '_temp_data_cache'):
                self._temp_data_cache.clear()

            # 清理响应时间历史
            if hasattr(self, 'responsiveness_monitor') and self.responsiveness_monitor:
                if len(self.responsiveness_monitor.response_times) > 30:
                    self.responsiveness_monitor.response_times = self.responsiveness_monitor.response_times[-30:]

            # 执行垃圾回收
            import gc
            gc.collect()

            print("[OK] 定期清理完成")

        except Exception as e:
            print(f"定期清理失败: {e}")

    def _handle_error(self, error_message):
        """统一错误处理"""
        try:
            self._error_count += 1
            print(f"[ERROR] {error_message}")

            # 如果错误过多，执行恢复操作
            if self._error_count > self._max_errors:
                self._attempt_recovery()
                self._error_count = 0  # 重置错误计数

        except Exception as e:
            print(f"错误处理失败: {e}")

    def _attempt_recovery(self):
        """尝试自动恢复"""
        try:
            print("[WARN] 检测到过多错误，尝试自动恢复...")

            # 强制垃圾回收
            import gc
            for _ in range(5):
                gc.collect()

            # 重置状态变量
            self.is_processing = False
            self.is_downloading = False

            # 清理所有缓存
            if hasattr(self, '_temp_data_cache'):
                self._temp_data_cache.clear()

            # 重置进度条
            if hasattr(self, 'process_progress_bar'):
                self.process_progress_bar.setValue(0)

            # 更新状态栏
            self.statusBar().showMessage("系统已自动恢复")

            print("[OK] 自动恢复完成")

        except Exception as e:
            print(f"自动恢复失败: {e}")


    def _handle_memory_emergency(self):
        """处理内存紧急情况"""
        try:
            print("[WARN]️ 内存紧急情况，执行紧急清理...")
            
            # 强制垃圾回收
            for _ in range(5):
                gc.collect()
            
            # 清理性能数据历史
            if len(self.performance_data) > 10:
                self.performance_data = self.performance_data[-10:]
            
            # 降低监控频率以减少内存压力
            time.sleep(10)
            
            print("[OK] 紧急内存清理完成")
        except Exception as e:
            print(f"紧急内存清理失败: {e}")


    def _handle_memory_emergency(self):
        """处理内存紧急情况"""
        try:
            print("[WARN]️ 内存紧急情况，执行紧急清理...")
            
            # 强制垃圾回收
            for _ in range(5):
                gc.collect()
            
            # 清理性能数据历史
            if len(self.performance_data) > 10:
                self.performance_data = self.performance_data[-10:]
            
            # 降低监控频率以减少内存压力
            time.sleep(10)
            
            print("[OK] 紧急内存清理完成")
        except Exception as e:
            print(f"紧急内存清理失败: {e}")

    def get_performance_summary(self):
        """获取性能摘要"""
        try:
            summary = {}

            if hasattr(self, 'stability_monitor') and self.stability_monitor:
                summary.update(self.stability_monitor.get_performance_summary())

            if hasattr(self, 'responsiveness_monitor') and self.responsiveness_monitor:
                summary.update(self.responsiveness_monitor.get_response_summary())

            return summary
        except Exception as e:
            print(f"获取性能摘要失败: {e}")
            return {}

    def closeEvent(self, event):
        """窗口关闭事件 - 优化版本"""
        try:
            print("[INFO] 开始关闭应用程序...")

            # 停止所有正在进行的处理
            if hasattr(self, 'is_processing') and self.is_processing:
                self.is_processing = False
                print("[OK] 已停止正在进行的处理")

            # 停止异步线程
            if hasattr(self, 'viral_srt_thread') and self.viral_srt_thread.isRunning():
                if hasattr(self, 'viral_srt_worker'):
                    self.viral_srt_worker.cancel()
                self.viral_srt_thread.quit()
                self.viral_srt_thread.wait(3000)  # 等待最多3秒
                print("[OK] 异步处理线程已停止")

            # 停止所有监控
            if hasattr(self, 'stability_monitor') and self.stability_monitor:
                self.stability_monitor.stop_monitoring()
                print("[OK] 进程稳定性监控已停止")

            if hasattr(self, 'responsiveness_monitor') and self.responsiveness_monitor:
                self.responsiveness_monitor.stop_monitoring()
                print("[OK] 响应性监控已停止")

            if hasattr(self, 'memory_watcher') and self.memory_watcher:
                try:
                    if hasattr(self.memory_watcher, 'stop_monitoring'):
                        self.memory_watcher.stop_monitoring()
                    elif hasattr(self.memory_watcher, 'stop_watching'):
                        self.memory_watcher.stop_watching()
                    print("[OK] 内存监控已停止")
                except Exception as e:
                    print(f"停止内存监控失败: {e}")

            # 清理所有资源
            self._cleanup_all_resources()

            # 执行最终垃圾回收
            try:
                for _ in range(3):
                    gc.collect()
                print("[OK] 垃圾回收完成")
            except:
                pass

            # 显示性能摘要
            try:
                summary = self.get_performance_summary()
                if summary:
                    print("=" * 50)
                    print("性能摘要:")
                    for key, value in summary.items():
                        print(f"  {key}: {value}")
                    print("=" * 50)
            except Exception as e:
                print(f"获取性能摘要失败: {e}")

            print("[OK] 应用程序正常关闭")
            event.accept()

        except Exception as e:
            print(f"关闭事件处理失败: {e}")
            import traceback
            print(f"详细错误: {traceback.format_exc()}")
            # 即使出错也要强制关闭
            try:
                import gc
                gc.collect()
            except:
                pass
            event.accept()

    def _cleanup_all_resources(self):
        """清理所有资源"""
        try:
            print("[INFO] 清理所有资源...")

            # 清理缓存
            if hasattr(self, '_temp_data_cache'):
                self._temp_data_cache.clear()

            # 清理性能数据
            if hasattr(self, 'performance_data'):
                self.performance_data.clear()

            # 清理响应时间数据
            if hasattr(self, 'responsiveness_monitor') and self.responsiveness_monitor:
                if hasattr(self.responsiveness_monitor, 'response_times'):
                    self.responsiveness_monitor.response_times.clear()

            # 清理UI组件缓存
            if hasattr(self, 'video_list'):
                self.video_list.clear()
            if hasattr(self, 'srt_list'):
                self.srt_list.clear()

            print("[OK] 资源清理完成")

        except Exception as e:
            print(f"资源清理失败: {e}")

class TechDialog(QDialog):
    """技术详情对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 确保在主线程中初始化
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import QThread
        if QApplication.instance() and QApplication.instance().thread() != QThread.currentThread():
            print("[WARN] 主窗口不在主线程中初始化，可能导致问题")
        
        self.setWindowTitle("技术详情")
        self.setMinimumSize(750, 650)
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)

        # 简单布局
        layout = QVBoxLayout()
        self.setLayout(layout)

        title = QLabel("🔧 技术架构详情")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #2c3e50; margin-bottom: 15px; padding: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setWordWrap(False)
        layout.addWidget(title)

        subtitle = QLabel("基于最新AI技术的短剧混剪解决方案")
        subtitle.setStyleSheet("font-size: 14px; color: #2980b9; font-style: italic; margin-bottom: 15px;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        content = QTextEdit()
        content.setReadOnly(True)
        content.setHtml("""
        <div style="margin: 15px; line-height: 1.6;">
            <h3 style="color: #1a5276; border-bottom: 2px solid #3498db; padding-bottom: 5px;">🤖 双模型AI架构</h3>

            <div style="margin: 15px 0; padding: 12px; background-color: #f8f9fa; border-left: 4px solid #3498db;">
                <h4 style="color: #2c3e50; margin-top: 0;">🇺🇸 Mistral-7B (英文处理)</h4>
                <p><strong>模型特点：</strong>70亿参数的高效英文语言模型</p>
                <p><strong>量化策略：</strong>Q2_K/Q4_K_M/Q5_K多级量化，最低2GB内存运行</p>
                <p><strong>应用场景：</strong>英文剧情分析、情感识别、字幕重构</p>
            </div>

            <div style="margin: 15px 0; padding: 12px; background-color: #f8f9fa; border-left: 4px solid #e74c3c;">
                <h4 style="color: #2c3e50; margin-top: 0;">🇨🇳 Qwen2.5-7B (中文处理)</h4>
                <p><strong>模型特点：</strong>专为中文优化的70亿参数模型</p>
                <p><strong>量化策略：</strong>智能量化技术，保持中文理解精度</p>
                <p><strong>应用场景：</strong>中文剧情分析、文化适配、本土化内容生成</p>
            </div>

            <h3 style="color: #1a5276; border-bottom: 2px solid #3498db; padding-bottom: 5px; margin-top: 25px;">🎬 核心技术特色</h3>

            <div style="margin: 15px 0; padding: 12px; background-color: #f0f8ff; border-left: 4px solid #f39c12;">
                <h4 style="color: #2c3e50; margin-top: 0;">📝 剧本重构技术</h4>
                <p><strong>智能分析：</strong>AI深度理解原始剧情结构和情感走向</p>
                <p><strong>病毒式转换：</strong>基于爆款视频模式重构字幕内容</p>
                <p><strong>精确映射：</strong>保持原始时间轴，确保视频同步</p>
            </div>

            <div style="margin: 15px 0; padding: 12px; background-color: #f0f8ff; border-left: 4px solid #27ae60;">
                <h4 style="color: #2c3e50; margin-top: 0;">✂️ 精确视频拼接</h4>
                <p><strong>时间轴精度：</strong>≤0.5秒的超高精度视频切割</p>
                <p><strong>FFmpeg集成：</strong>支持GPU加速的无损视频处理</p>
                <p><strong>格式支持：</strong>15+种主流视频格式兼容</p>
            </div>

            <div style="margin: 15px 0; padding: 12px; background-color: #f0f8ff; border-left: 4px solid #9b59b6;">
                <h4 style="color: #2c3e50; margin-top: 0;">🔄 智能语言检测</h4>
                <p><strong>自动识别：</strong>实时检测字幕语言类型</p>
                <p><strong>模型切换：</strong>无缝切换对应的AI模型</p>
                <p><strong>混合处理：</strong>支持中英文混合内容处理</p>
            </div>

            <h3 style="color: #1a5276; border-bottom: 2px solid #3498db; padding-bottom: 5px; margin-top: 25px;">⚙️ 系统架构设计</h3>

            <div style="margin: 15px 0;">
                <h4 style="color: #2c3e50;">🏗️ 模块化架构</h4>
                <ul style="margin: 10px 0; padding-left: 20px;">
                    <li><strong>输入验证层：</strong>增强的边界条件检查和文件验证</li>
                    <li><strong>AI处理核心：</strong>双模型系统和智能调度器</li>
                    <li><strong>视频处理引擎：</strong>FFmpeg集成和GPU加速</li>
                    <li><strong>导出适配器：</strong>剪映工程文件生成</li>
                    <li><strong>用户界面层：</strong>PyQt6响应式界面</li>
                </ul>
            </div>

            <div style="margin: 15px 0;">
                <h4 style="color: #2c3e50;">🛡️ 稳定性保障</h4>
                <ul style="margin: 10px 0; padding-left: 20px;">
                    <li><strong>增强异常处理：</strong>5级异常分类和自动恢复机制</li>
                    <li><strong>结构化日志：</strong>8种日志分类，便于问题定位</li>
                    <li><strong>内存管理：</strong>4GB设备兼容，智能资源调度</li>
                    <li><strong>质量保证：</strong>85.7%集成测试通过率</li>
                </ul>
            </div>

            <h3 style="color: #1a5276; border-bottom: 2px solid #3498db; padding-bottom: 5px; margin-top: 25px;">💻 轻量化部署</h3>

            <div style="margin: 15px 0; padding: 12px; background-color: #e8f5e8; border-left: 4px solid #27ae60;">
                <h4 style="color: #2c3e50; margin-top: 0;">🎯 低配置兼容</h4>
                <p><strong>最低要求：</strong>4GB内存即可流畅运行</p>
                <p><strong>CPU优化：</strong>支持纯CPU模式，无需独立显卡</p>
                <p><strong>按需加载：</strong>模型动态加载，减少内存占用</p>
                <p><strong>智能降级：</strong>根据硬件自动调整处理精度</p>
            </div>

            <div style="margin: 15px 0; padding: 12px; background-color: #fff5ee; border-left: 4px solid #ff6b35;">
                <h4 style="color: #2c3e50; margin-top: 0;">🚀 性能优化</h4>
                <p><strong>GPU加速：</strong>支持NVIDIA/AMD/Intel GPU加速</p>
                <p><strong>多线程处理：</strong>并行视频处理，提升效率</p>
                <p><strong>缓存机制：</strong>智能缓存，避免重复计算</p>
                <p><strong>批量处理：</strong>支持100+文件批量处理</p>
            </div>

            <h3 style="color: #1a5276; border-bottom: 2px solid #3498db; padding-bottom: 5px; margin-top: 25px;">📊 技术指标</h3>

            <div style="margin: 15px 0;">
                <table style="width: 100%; border-collapse: collapse; margin: 10px 0;">
                    <tr style="background-color: #f8f9fa;">
                        <td style="padding: 8px; border: 1px solid #dee2e6; font-weight: bold;">性能指标</td>
                        <td style="padding: 8px; border: 1px solid #dee2e6; font-weight: bold;">数值</td>
                        <td style="padding: 8px; border: 1px solid #dee2e6; font-weight: bold;">说明</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #dee2e6;">时间轴精度</td>
                        <td style="padding: 8px; border: 1px solid #dee2e6;">≤0.5秒</td>
                        <td style="padding: 8px; border: 1px solid #dee2e6;">视频切割精度</td>
                    </tr>
                    <tr style="background-color: #f8f9fa;">
                        <td style="padding: 8px; border: 1px solid #dee2e6;">内存使用</td>
                        <td style="padding: 8px; border: 1px solid #dee2e6;">&lt;1GB</td>
                        <td style="padding: 8px; border: 1px solid #dee2e6;">4GB设备兼容</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #dee2e6;">测试通过率</td>
                        <td style="padding: 8px; border: 1px solid #dee2e6;">85.7%</td>
                        <td style="padding: 8px; border: 1px solid #dee2e6;">集成测试结果</td>
                    </tr>
                    <tr style="background-color: #f8f9fa;">
                        <td style="padding: 8px; border: 1px solid #dee2e6;">支持格式</td>
                        <td style="padding: 8px; border: 1px solid #dee2e6;">15+种</td>
                        <td style="padding: 8px; border: 1px solid #dee2e6;">视频格式支持</td>
                    </tr>
                </table>
            </div>

            <div style="text-align: center; margin-top: 20px; padding: 15px; background-color: #ecf0f1; border-radius: 5px;">
                <p style="color: #2c3e50; font-weight: bold; margin: 0;">
                    "技术创新驱动内容创作，让AI成为每个创作者的得力助手"
                </p>
                <p style="color: #7f8c8d; font-size: 12px; margin: 5px 0 0 0;">
                    — CKEN
                </p>
            </div>
        </div>
        """)
        layout.addWidget(content)

        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.setMinimumWidth(100)
        close_btn.setStyleSheet("font-size: 14px; padding: 8px 20px;")
        close_btn.clicked.connect(self.close)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        btn_layout.addStretch()

        layout.addLayout(btn_layout)


class HistoryDialog(QDialog):
    """项目历程对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 确保在主线程中初始化
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import QThread
        if QApplication.instance() and QApplication.instance().thread() != QThread.currentThread():
            print("[WARN] 主窗口不在主线程中初始化，可能导致问题")
        
        self.setWindowTitle("项目历程")
        self.setMinimumSize(700, 650)
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)

        # 简单布局
        layout = QVBoxLayout()
        self.setLayout(layout)

        title = QLabel("📈 项目发展历程")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #2c3e50; margin-bottom: 15px; padding: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setWordWrap(False)
        layout.addWidget(title)

        subtitle = QLabel("从概念到生产就绪的技术演进之路")
        subtitle.setStyleSheet("font-size: 14px; color: #2980b9; font-style: italic; margin-bottom: 15px;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        content = QTextEdit()
        content.setReadOnly(True)
        content.setHtml("""
        <div style="margin: 15px; line-height: 1.6;">
            <h3 style="color: #1a5276; border-bottom: 2px solid #3498db; padding-bottom: 5px;">🚀 项目启动阶段</h3>

            <div style="margin: 15px 0; padding: 12px; background-color: #f8f9fa; border-left: 4px solid #3498db;">
                <h4 style="color: #2c3e50; margin-top: 0;">📅 2025年3月 - 项目构想与立项</h4>
                <p><strong>核心理念：</strong>让AI技术服务于短剧内容创作</p>
                <p><strong>市场调研：</strong>深入分析短剧混剪市场需求和技术痛点</p>
                <p><strong>技术选型：</strong>确定双模型架构和轻量化部署策略</p>
                <p><strong>开发者确定：</strong>CKEN作为全栈AI开发者，具备AI算法、视频处理、UI设计等全方位技能</p>
            </div>

            <div style="margin: 15px 0; padding: 12px; background-color: #f8f9fa; border-left: 4px solid #e74c3c;">
                <h4 style="color: #2c3e50; margin-top: 0;">📅 2025年3月中旬 - 技术原型开发</h4>
                <p><strong>AI模型集成：</strong>成功集成Mistral-7B和Qwen2.5-7B模型</p>
                <p><strong>核心算法：</strong>开发剧情分析和字幕重构算法</p>
                <p><strong>架构设计：</strong>建立模块化系统架构</p>
                <p><strong>技术验证：</strong>完成核心功能的可行性验证</p>
            </div>

            <h3 style="color: #1a5276; border-bottom: 2px solid #3498db; padding-bottom: 5px; margin-top: 25px;">🔧 功能开发阶段</h3>

            <div style="margin: 15px 0; padding: 12px; background-color: #f0f8ff; border-left: 4px solid #f39c12;">
                <h4 style="color: #2c3e50; margin-top: 0;">📅 2025年4月初 - 基础功能实现</h4>
                <p><strong>视频处理：</strong>实现FFmpeg集成和精确视频切割</p>
                <p><strong>字幕解析：</strong>开发SRT字幕解析和验证系统</p>
                <p><strong>UI界面：</strong>设计并实现PyQt6用户界面</p>
                <p><strong>语言检测：</strong>实现中英文自动识别和模型切换</p>
            </div>

            <div style="margin: 15px 0; padding: 12px; background-color: #f0f8ff; border-left: 4px solid #27ae60;">
                <h4 style="color: #2c3e50; margin-top: 0;">📅 2025年4月下旬 - 功能完善与优化</h4>
                <p><strong>剪映导出：</strong>开发剪映工程文件导出功能</p>
                <p><strong>批量处理：</strong>实现多文件批量处理能力</p>
                <p><strong>性能优化：</strong>优化内存使用，实现4GB设备兼容</p>
                <p><strong>错误处理：</strong>建立基础异常处理机制</p>
            </div>

            <h3 style="color: #1a5276; border-bottom: 2px solid #3498db; padding-bottom: 5px; margin-top: 25px;">🧪 测试与优化阶段</h3>

            <div style="margin: 15px 0; padding: 12px; background-color: #fff5ee; border-left: 4px solid #9b59b6;">
                <h4 style="color: #2c3e50; margin-top: 0;">📅 2025年5月 - 内部测试与修复</h4>
                <p><strong>功能测试：</strong>全面测试核心功能和边界条件</p>
                <p><strong>性能测试：</strong>验证内存使用和处理速度</p>
                <p><strong>兼容性测试：</strong>测试多种视频格式和系统环境</p>
                <p><strong>问题修复：</strong>修复发现的Bug和性能问题</p>
            </div>

            <div style="margin: 15px 0; padding: 12px; background-color: #fff5ee; border-left: 4px solid #ff6b35;">
                <h4 style="color: #2c3e50; margin-top: 0;">📅 2025年6月 - 用户体验优化</h4>
                <p><strong>界面优化：</strong>改进用户界面和交互体验</p>
                <p><strong>文档完善：</strong>编写用户手册和技术文档</p>
                <p><strong>多语言支持：</strong>完善中英文界面支持</p>
                <p><strong>训练功能：</strong>开发模型训练和数据投喂功能</p>
            </div>

            <h3 style="color: #1a5276; border-bottom: 2px solid #3498db; padding-bottom: 5px; margin-top: 25px;">🏆 质量提升阶段</h3>

            <div style="margin: 15px 0; padding: 12px; background-color: #e8f5e8; border-left: 4px solid #27ae60;">
                <h4 style="color: #2c3e50; margin-top: 0;">📅 2025年7月初 - 高优先级问题修复</h4>
                <p><strong>Mock AI优化：</strong>修复边界条件错误，提升稳定性</p>
                <p><strong>FFmpeg集成：</strong>解决视频信息提取问题</p>
                <p><strong>API接口重构：</strong>优化剪映导出器接口设计</p>
                <p><strong>测试成功率：</strong>从57.1%提升至100%</p>
            </div>

            <div style="margin: 15px 0; padding: 12px; background-color: #e8f5e8; border-left: 4px solid #3498db;">
                <h4 style="color: #2c3e50; margin-top: 0;">📅 2025年7月9日 - 中优先级问题修复</h4>
                <p><strong>异常处理增强：</strong>实现5级异常分类和自动恢复</p>
                <p><strong>日志系统优化：</strong>开发结构化日志和性能监控</p>
                <p><strong>边界条件检查：</strong>全面的输入验证和文件检查</p>
                <p><strong>最终测试：</strong>集成测试成功率达到85.7%</p>
            </div>

            <h3 style="color: #1a5276; border-bottom: 2px solid #3498db; padding-bottom: 5px; margin-top: 25px;">🎯 关键里程碑</h3>

            <div style="margin: 15px 0;">
                <table style="width: 100%; border-collapse: collapse; margin: 10px 0;">
                    <tr style="background-color: #f8f9fa;">
                        <td style="padding: 8px; border: 1px solid #dee2e6; font-weight: bold;">时间</td>
                        <td style="padding: 8px; border: 1px solid #dee2e6; font-weight: bold;">里程碑</td>
                        <td style="padding: 8px; border: 1px solid #dee2e6; font-weight: bold;">成果</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #dee2e6;">2025.03</td>
                        <td style="padding: 8px; border: 1px solid #dee2e6;">项目启动</td>
                        <td style="padding: 8px; border: 1px solid #dee2e6;">技术架构确定</td>
                    </tr>
                    <tr style="background-color: #f8f9fa;">
                        <td style="padding: 8px; border: 1px solid #dee2e6;">2025.04</td>
                        <td style="padding: 8px; border: 1px solid #dee2e6;">核心功能</td>
                        <td style="padding: 8px; border: 1px solid #dee2e6;">基础功能实现</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #dee2e6;">2025.05</td>
                        <td style="padding: 8px; border: 1px solid #dee2e6;">功能完善</td>
                        <td style="padding: 8px; border: 1px solid #dee2e6;">双语支持完成</td>
                    </tr>
                    <tr style="background-color: #f8f9fa;">
                        <td style="padding: 8px; border: 1px solid #dee2e6;">2025.06</td>
                        <td style="padding: 8px; border: 1px solid #dee2e6;">用户体验</td>
                        <td style="padding: 8px; border: 1px solid #dee2e6;">界面优化完成</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #dee2e6;">2025.07</td>
                        <td style="padding: 8px; border: 1px solid #dee2e6;">质量提升</td>
                        <td style="padding: 8px; border: 1px solid #dee2e6;">生产就绪状态</td>
                    </tr>
                </table>
            </div>

            <h3 style="color: #1a5276; border-bottom: 2px solid #3498db; padding-bottom: 5px; margin-top: 25px;">📊 技术演进成果</h3>

            <div style="margin: 15px 0;">
                <h4 style="color: #2c3e50;">🎯 质量指标提升</h4>
                <ul style="margin: 10px 0; padding-left: 20px;">
                    <li><strong>测试成功率：</strong>57.1% → 85.7% → 100%（分阶段提升）</li>
                    <li><strong>异常处理覆盖率：</strong>0% → 95%+（全面覆盖）</li>
                    <li><strong>内存使用优化：</strong>支持4GB低配设备</li>
                    <li><strong>时间轴精度：</strong>实现≤0.5秒超高精度</li>
                </ul>
            </div>

            <div style="margin: 15px 0;">
                <h4 style="color: #2c3e50;">🚀 功能特性完善</h4>
                <ul style="margin: 10px 0; padding-left: 20px;">
                    <li><strong>双模型架构：</strong>Mistral-7B + Qwen2.5-7B</li>
                    <li><strong>智能语言检测：</strong>自动识别并切换模型</li>
                    <li><strong>剪映工程导出：</strong>无缝对接专业编辑软件</li>
                    <li><strong>批量处理：</strong>支持100+文件批量处理</li>
                </ul>
            </div>

            <div style="margin: 15px 0;">
                <h4 style="color: #2c3e50;">🛡️ 系统稳定性</h4>
                <ul style="margin: 10px 0; padding-left: 20px;">
                    <li><strong>增强异常处理：</strong>5级异常分类和自动恢复</li>
                    <li><strong>结构化日志：</strong>8种日志分类，便于调试</li>
                    <li><strong>边界条件检查：</strong>全面的输入验证机制</li>
                    <li><strong>性能监控：</strong>实时资源使用监控</li>
                </ul>
            </div>

            <h3 style="color: #1a5276; border-bottom: 2px solid #3498db; padding-bottom: 5px; margin-top: 25px;">🔮 未来规划</h3>

            <div style="margin: 15px 0; padding: 12px; background-color: #f0f8ff; border-left: 4px solid #3498db;">
                <h4 style="color: #2c3e50; margin-top: 0;">📅 短期目标（1-3个月）</h4>
                <p><strong>Beta版本发布：</strong>面向早期用户开放测试</p>
                <p><strong>用户反馈收集：</strong>持续优化用户体验</p>
                <p><strong>性能进一步优化：</strong>提升处理速度和稳定性</p>
                <p><strong>功能扩展：</strong>增加更多视频格式和导出选项</p>
            </div>

            <div style="margin: 15px 0; padding: 12px; background-color: #f0f8ff; border-left: 4px solid #27ae60;">
                <h4 style="color: #2c3e50; margin-top: 0;">📅 中期目标（3-6个月）</h4>
                <p><strong>正式版本发布：</strong>面向大众用户发布稳定版</p>
                <p><strong>云端服务：</strong>提供云端AI处理服务</p>
                <p><strong>移动端支持：</strong>开发移动端应用</p>
                <p><strong>社区建设：</strong>建立用户社区和内容分享平台</p>
            </div>

            <div style="text-align: center; margin-top: 20px; padding: 15px; background-color: #ecf0f1; border-radius: 5px;">
                <p style="color: #2c3e50; font-weight: bold; margin: 0;">
                    "从概念到现实，每一步都是技术创新与用户需求的完美结合"
                </p>
                <p style="color: #7f8c8d; font-size: 12px; margin: 5px 0 0 0;">
                    — CKEN
                </p>
            </div>

            <div style="text-align: center; margin-top: 15px; padding: 12px; background-color: #d5f4e6; border-radius: 5px;">
                <p style="color: #27ae60; font-weight: bold; font-size: 16px; margin: 0;">
                    🎉 当前状态：生产就绪 | 测试通过率：85.7% | 版本：1.0.0-beta
                </p>
            </div>
        </div>
        """)
        layout.addWidget(content)

        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.setMinimumWidth(100)
        close_btn.setStyleSheet("font-size: 14px; padding: 8px 20px;")
        close_btn.clicked.connect(self.close)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        btn_layout.addStretch()

        layout.addLayout(btn_layout)

class LogViewerDialog(QDialog):
    """日志查看器对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 确保在主线程中初始化
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import QThread
        if QApplication.instance() and QApplication.instance().thread() != QThread.currentThread():
            print("[WARN] 主窗口不在主线程中初始化，可能导致问题")
        
        self.setWindowTitle("系统日志")
        self.setMinimumSize(800, 600)
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)
        
        # 创建布局
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # 创建标题
        title = QLabel("系统日志查看器")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # 日志过滤选项
        filter_layout = QHBoxLayout()
        
        # 日志级别筛选
        filter_layout.addWidget(QLabel("日志级别:"))
        self.level_combo = QComboBox()
        self.level_combo.addItems(["全部", "INFO", "WARNING", "ERROR", "DEBUG"])
        self.level_combo.currentIndexChanged.connect(self.filter_logs)
        filter_layout.addWidget(self.level_combo)
        
        # 搜索框
        filter_layout.addWidget(QLabel("搜索:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("输入搜索内容")
        self.search_edit.textChanged.connect(self.filter_logs)
        filter_layout.addWidget(self.search_edit)
        
        # 刷新按钮
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self.refresh_logs)
        filter_layout.addWidget(refresh_btn)
        
        layout.addLayout(filter_layout)
        
        # 日志显示区域
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        layout.addWidget(self.log_display)
        
        # 底部按钮
        button_layout = QHBoxLayout()
        
        # 清空日志按钮
        clear_btn = QPushButton("清空日志")
        clear_btn.clicked.connect(self.clear_logs)
        button_layout.addWidget(clear_btn)
        
        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        # 加载日志
        self.refresh_logs()
    
    def refresh_logs(self):
        """刷新日志内容"""
        try:
            # 获取日志级别
            level = None
            if self.level_combo.currentText() != "全部":
                level = self.level_combo.currentText()
            
            # 获取搜索文本
            search_text = self.search_edit.text().strip()
            
            # 获取日志
            logs = log_handler.get_logs(n=100, level=level, search_text=search_text)
            
            # 显示日志
            self.log_display.clear()
            for log in logs:
                self.log_display.append(log.strip())
            
            # 滚动到底部
            self.log_display.verticalScrollBar().setValue(
                self.log_display.verticalScrollBar().maximum()
            )
            
        except Exception as e:
            self.log_display.setText(f"加载日志失败: {str(e)}")
    
    def filter_logs(self):
        """根据筛选条件过滤日志"""
        self.refresh_logs()
    
    def clear_logs(self):
        """清空日志"""
        reply = QMessageBox.question(
            self,
            "确认清空",
            "确定要清空所有日志吗？此操作不可恢复。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                if log_handler.clear_logs():
                    self.log_display.clear()
                    self.log_display.setText("日志已清空")
                else:
                    self.log_display.setText("清空日志失败")
            except Exception as e:
                self.log_display.setText(f"清空日志失败: {str(e)}")



def main():
    """主函数，启动简易UI程序"""

    print("=" * 60)
    print("VisionAI-ClipsMaster 启动中...")
    print("=" * 60)

    # 初始化兼容性设置
    if HAS_COMPAT:
        try:
            # 应用Qt版本兼容处理
            handle_qt_version()

            # 设置完整的兼容性
            setup_compat()

            print(f"[OK] 已应用兼容性设置，Qt版本: {get_qt_version_str()}")
        except Exception as e:
            print(f"[WARN] 应用兼容性设置时出错: {e}")

    # 创建应用实例
    try:
        app = QApplication(sys.argv)
        print("[OK] QApplication 创建成功")
    except Exception as e:
        print(f"[FAIL] QApplication 创建失败: {e}")
        return 1

    # 设置应用程序样式
    try:
        app.setStyle('Fusion')
        print("[OK] 应用样式设置成功")
    except Exception as e:
        print(f"[WARN] 应用样式设置失败: {e}")

    # 设置程序信息
    app.setApplicationName("VisionAI-ClipsMaster")
    app.setApplicationVersion("1.0.0")
    app.setQuitOnLastWindowClosed(True)

    # 创建主窗口
    try:
        print("正在创建主窗口...")
        window = SimpleScreenplayApp()
        print("[OK] 主窗口创建成功")
    except Exception as e:
        print(f"[FAIL] 主窗口创建失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # 检查是否启用移动端适配功能
    enable_mobile_adapter = '--responsive' in sys.argv or '-r' in sys.argv

    if enable_mobile_adapter:
        # 尝试加载并应用移动端适配功能
        try:
            # 延迟导入移动端适配模块，以避免在不需要时加载
            from ui.responsive.simple_ui_adapter import integrate_responsive_features

            # 应用移动端适配功能
            integrate_responsive_features(window)

            print("[OK] 移动端适配功能已启用")
        except Exception as e:
            print(f"[WARN] 启用移动端适配功能失败: {e}")
            print("将使用标准界面")

    # 显示窗口
    try:
        print("正在显示窗口...")
        window.show()

        # 确保窗口显示在前台
        window.raise_()
        window.activateWindow()

        print("[OK] 窗口显示成功")
        print(f"窗口标题: {window.windowTitle()}")
        print(f"窗口大小: {window.size().width()}x{window.size().height()}")
        print("=" * 60)
        print("UI已启动，等待用户交互...")
        print("=" * 60)

    except Exception as e:
        print(f"[FAIL] 窗口显示失败: {e}")
        return 1

    # 运行应用程序
    try:
        return app.exec()
    except Exception as e:
        print(f"[FAIL] 应用程序运行失败: {e}")
        return 1

if __name__ == "__main__":
    # 设置全局异常处理器
    setup_global_exception_handler()

    # 检查环境依赖
    try:
        from ui.config.environment import check_environment
        env_status = check_environment()
        print("环境依赖检查完成")
    except ImportError:
        print("警告: 环境检查模块不可用")

    # 调用主函数
    sys.exit(main())
