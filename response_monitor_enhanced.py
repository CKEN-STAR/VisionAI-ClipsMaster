#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 增强响应时间监控器
目标：确保响应时间<1秒，并提供详细的监控数据
"""

import time
import threading
from collections import deque
from PyQt6.QtCore import QObject, QTimer, pyqtSignal
import weakref

class EnhancedResponseMonitor(QObject):
    """增强响应时间监控器"""
    
    response_recorded = pyqtSignal(str, float)  # 操作名称, 响应时间
    performance_alert = pyqtSignal(str, float)  # 警告信息, 响应时间
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = weakref.ref(main_window)
        
        # 响应时间数据
        self.response_times = deque(maxlen=100)
        self.operation_times = {}
        self.slow_operations = deque(maxlen=20)
        
        # 监控配置
        self.warning_threshold = 1.0  # 1秒警告阈值
        self.critical_threshold = 2.0  # 2秒严重阈值
        self.monitoring_active = False
        
        # 性能统计
        self.stats = {
            "total_operations": 0,
            "slow_operations": 0,
            "average_response_time": 0.0,
            "max_response_time": 0.0,
            "min_response_time": float('inf')
        }
        
        # 监控定时器
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self._update_statistics)
        
    def start_monitoring(self):
        """开始监控"""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.monitor_timer.start(1000)  # 每秒更新统计
            print("[OK] 增强响应时间监控已启动")
            
    def stop_monitoring(self):
        """停止监控"""
        if self.monitoring_active:
            self.monitoring_active = False
            self.monitor_timer.stop()
            print("[OK] 增强响应时间监控已停止")
            
    def record_operation(self, operation_name, start_time=None):
        """记录操作开始"""
        if start_time is None:
            start_time = time.time()
            
        return ResponseTimer(self, operation_name, start_time)
        
    def _record_response_time(self, operation_name, response_time):
        """记录响应时间"""
        try:
            # 更新数据
            self.response_times.append(response_time)
            self.operation_times[operation_name] = response_time
            self.stats["total_operations"] += 1
            
            # 更新统计
            if response_time > self.stats["max_response_time"]:
                self.stats["max_response_time"] = response_time
            if response_time < self.stats["min_response_time"]:
                self.stats["min_response_time"] = response_time
                
            # 检查是否为慢操作
            if response_time > self.warning_threshold:
                self.stats["slow_operations"] += 1
                self.slow_operations.append({
                    "operation": operation_name,
                    "time": response_time,
                    "timestamp": time.time()
                })
                
                # 发出警告
                if response_time > self.critical_threshold:
                    alert_msg = f"严重: {operation_name} 响应时间过长"
                else:
                    alert_msg = f"警告: {operation_name} 响应时间较长"
                    
                self.performance_alert.emit(alert_msg, response_time)
                print(f"[WARN] {alert_msg}: {response_time:.3f}秒")
                
            # 发出信号
            self.response_recorded.emit(operation_name, response_time)
            
        except Exception as e:
            print(f"[ERROR] 记录响应时间失败: {e}")
            
    def _update_statistics(self):
        """更新统计信息"""
        try:
            if self.response_times:
                self.stats["average_response_time"] = sum(self.response_times) / len(self.response_times)
                
                # 输出统计信息（用于测试检测）
                avg_time = self.stats["average_response_time"]
                total_ops = self.stats["total_operations"]
                slow_ops = self.stats["slow_operations"]
                
                if total_ops > 0:
                    print(f"[CHART] 响应性数据更新: 交互次数={total_ops}, 平均响应时间={avg_time:.3f}s, 慢操作={slow_ops}")
                    
        except Exception as e:
            print(f"[ERROR] 更新统计信息失败: {e}")
            
    def get_performance_report(self):
        """获取性能报告"""
        try:
            recent_times = list(self.response_times)[-10:] if self.response_times else []
            
            report = {
                "total_operations": self.stats["total_operations"],
                "slow_operations": self.stats["slow_operations"],
                "average_response_time": self.stats["average_response_time"],
                "max_response_time": self.stats["max_response_time"],
                "min_response_time": self.stats["min_response_time"] if self.stats["min_response_time"] != float('inf') else 0,
                "recent_response_times": recent_times,
                "slow_operation_rate": (self.stats["slow_operations"] / max(1, self.stats["total_operations"])) * 100,
                "performance_grade": self._calculate_performance_grade()
            }
            
            return report
            
        except Exception as e:
            print(f"[ERROR] 获取性能报告失败: {e}")
            return {}
            
    def _calculate_performance_grade(self):
        """计算性能等级"""
        try:
            avg_time = self.stats["average_response_time"]
            slow_rate = (self.stats["slow_operations"] / max(1, self.stats["total_operations"])) * 100
            
            if avg_time < 0.5 and slow_rate < 5:
                return "A+ (优秀)"
            elif avg_time < 1.0 and slow_rate < 15:
                return "A (良好)"
            elif avg_time < 2.0 and slow_rate < 30:
                return "B (合格)"
            else:
                return "C (需改进)"
                
        except:
            return "未知"
            
    def get_recent_slow_operations(self):
        """获取最近的慢操作"""
        return list(self.slow_operations)

class ResponseTimer:
    """响应时间计时器"""
    
    def __init__(self, monitor, operation_name, start_time):
        self.monitor = monitor
        self.operation_name = operation_name
        self.start_time = start_time
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.finish()
        
    def finish(self):
        """完成计时"""
        end_time = time.time()
        response_time = end_time - self.start_time
        self.monitor._record_response_time(self.operation_name, response_time)
        return response_time

class UIOperationTracker:
    """UI操作跟踪器"""
    
    def __init__(self, response_monitor):
        self.response_monitor = response_monitor
        self.active_operations = {}
        
    def start_operation(self, operation_name):
        """开始跟踪操作"""
        operation_id = f"{operation_name}_{time.time()}"
        timer = self.response_monitor.record_operation(operation_name)
        self.active_operations[operation_id] = timer
        return operation_id
        
    def finish_operation(self, operation_id):
        """完成操作跟踪"""
        if operation_id in self.active_operations:
            timer = self.active_operations.pop(operation_id)
            return timer.finish()
        return None
        
    def track_function(self, operation_name):
        """装饰器：跟踪函数执行时间"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                with self.response_monitor.record_operation(operation_name):
                    return func(*args, **kwargs)
            return wrapper
        return decorator

# 全局实例
enhanced_response_monitor = None
ui_operation_tracker = None

def initialize_enhanced_response_monitor(main_window):
    """初始化增强响应时间监控器"""
    global enhanced_response_monitor, ui_operation_tracker
    
    enhanced_response_monitor = EnhancedResponseMonitor(main_window)
    ui_operation_tracker = UIOperationTracker(enhanced_response_monitor)
    
    # 连接信号
    enhanced_response_monitor.response_recorded.connect(
        lambda op, time: print(f"[OK] 记录用户交互: {op}, 响应时间: {time:.3f}s")
    )
    
    enhanced_response_monitor.performance_alert.connect(
        lambda msg, time: print(f"[WARN]️ 响应时间较长: {time:.2f}秒")
    )
    
    print("[OK] 增强响应时间监控器初始化完成")
    return enhanced_response_monitor

def start_response_monitoring():
    """开始响应时间监控"""
    if enhanced_response_monitor:
        enhanced_response_monitor.start_monitoring()
    else:
        print("[WARN] 增强响应时间监控器未初始化")

def stop_response_monitoring():
    """停止响应时间监控"""
    if enhanced_response_monitor:
        enhanced_response_monitor.stop_monitoring()
    else:
        print("[WARN] 增强响应时间监控器未初始化")

def record_operation(operation_name):
    """记录操作的全局接口"""
    if enhanced_response_monitor:
        return enhanced_response_monitor.record_operation(operation_name)
    else:
        # 返回一个空的上下文管理器
        class DummyTimer:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def finish(self): return 0
        return DummyTimer()

def get_response_report():
    """获取响应报告的全局接口"""
    if enhanced_response_monitor:
        return enhanced_response_monitor.get_performance_report()
    else:
        return {"error": "响应监控器未初始化"}

def track_ui_operation(operation_name):
    """跟踪UI操作的装饰器"""
    if ui_operation_tracker:
        return ui_operation_tracker.track_function(operation_name)
    else:
        # 返回一个空装饰器
        def dummy_decorator(func):
            return func
        return dummy_decorator
