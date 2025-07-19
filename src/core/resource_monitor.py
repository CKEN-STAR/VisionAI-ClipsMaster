#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时资源监控与动态调整机制
监控系统资源使用情况，在内存压力过大时自动调整模型配置
"""

import gc
import time
import psutil
import logging
import threading
from typing import Dict, Any, List, Callable, Optional
from dataclasses import dataclass
from enum import Enum
from collections import deque
import json
from datetime import datetime


class AlertLevel(Enum):
    """警告级别"""
    NORMAL = "normal"       # 正常状态
    WARNING = "warning"     # 黄色警告 (>70%)
    CRITICAL = "critical"   # 红色警告 (>85%)
    EMERGENCY = "emergency" # 紧急状态 (>90%)


@dataclass
class ResourceSnapshot:
    """资源快照"""
    timestamp: float
    memory_usage_percent: float
    memory_used_gb: float
    memory_available_gb: float
    cpu_usage_percent: float
    gpu_usage_percent: float
    gpu_memory_used_gb: float
    alert_level: AlertLevel


@dataclass
class PerformanceMetrics:
    """性能指标"""
    startup_time: float
    model_switch_time: float
    inference_time: float
    bleu_score: float
    memory_efficiency: float


class ResourceMonitor:
    """资源监控器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """初始化资源监控器"""
        self.logger = logging.getLogger(__name__)
        self.config = config or self._get_default_config()
        
        # 监控状态
        self.monitoring = False
        self.monitor_thread = None
        
        # 资源历史
        self.resource_history = deque(maxlen=1000)  # 保留最近1000个快照
        self.performance_history = deque(maxlen=100)  # 保留最近100个性能记录
        
        # 警告阈值
        self.warning_threshold = self.config.get("warning_threshold", 0.70)
        self.critical_threshold = self.config.get("critical_threshold", 0.85)
        self.emergency_threshold = self.config.get("emergency_threshold", 0.90)
        
        # 回调函数
        self.alert_callbacks = []
        self.adjustment_callbacks = []
        
        # 当前状态
        self.current_alert_level = AlertLevel.NORMAL
        self.last_adjustment_time = 0
        
        self.logger.info("资源监控器初始化完成")
    
    def start_monitoring(self, interval: int = 30):
        """启动监控"""
        if self.monitoring:
            self.logger.warning("监控已在运行")
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval,),
            daemon=True
        )
        self.monitor_thread.start()
        self.logger.info(f"资源监控已启动，监控间隔: {interval}秒")
    
    def stop_monitoring(self):
        """停止监控"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        self.logger.info("资源监控已停止")
    
    def get_current_snapshot(self) -> ResourceSnapshot:
        """获取当前资源快照"""
        try:
            # 获取内存信息
            memory = psutil.virtual_memory()
            memory_usage_percent = memory.percent
            memory_used_gb = memory.used / (1024**3)
            memory_available_gb = memory.available / (1024**3)
            
            # 获取CPU使用率
            cpu_usage_percent = psutil.cpu_percent(interval=1)
            
            # 获取GPU信息（如果可用）
            gpu_usage_percent = 0.0
            gpu_memory_used_gb = 0.0
            try:
                import GPUtil
                gpus = GPUtil.getGPUs()
                if gpus:
                    gpu = gpus[0]  # 使用第一个GPU
                    gpu_usage_percent = gpu.load * 100
                    gpu_memory_used_gb = gpu.memoryUsed / 1024
            except:
                pass
            
            # 确定警告级别
            alert_level = self._determine_alert_level(memory_usage_percent)
            
            snapshot = ResourceSnapshot(
                timestamp=time.time(),
                memory_usage_percent=memory_usage_percent,
                memory_used_gb=memory_used_gb,
                memory_available_gb=memory_available_gb,
                cpu_usage_percent=cpu_usage_percent,
                gpu_usage_percent=gpu_usage_percent,
                gpu_memory_used_gb=gpu_memory_used_gb,
                alert_level=alert_level
            )
            
            return snapshot
            
        except Exception as e:
            self.logger.error(f"获取资源快照失败: {e}")
            return self._get_fallback_snapshot()
    
    def add_alert_callback(self, callback: Callable[[AlertLevel, ResourceSnapshot], None]):
        """添加警告回调函数"""
        self.alert_callbacks.append(callback)
    
    def add_adjustment_callback(self, callback: Callable[[str, Dict[str, Any]], None]):
        """添加调整回调函数"""
        self.adjustment_callbacks.append(callback)
    
    def record_performance_metrics(self, metrics: PerformanceMetrics):
        """记录性能指标"""
        self.performance_history.append(metrics)
        self.logger.debug(f"记录性能指标: {metrics}")
    
    def get_resource_statistics(self, duration_minutes: int = 60) -> Dict[str, Any]:
        """获取资源统计信息"""
        try:
            cutoff_time = time.time() - (duration_minutes * 60)
            recent_snapshots = [
                snapshot for snapshot in self.resource_history
                if snapshot.timestamp >= cutoff_time
            ]
            
            if not recent_snapshots:
                return {"error": "没有足够的历史数据"}
            
            memory_usages = [s.memory_usage_percent for s in recent_snapshots]
            cpu_usages = [s.cpu_usage_percent for s in recent_snapshots]
            
            return {
                "duration_minutes": duration_minutes,
                "sample_count": len(recent_snapshots),
                "memory": {
                    "avg_usage_percent": sum(memory_usages) / len(memory_usages),
                    "max_usage_percent": max(memory_usages),
                    "min_usage_percent": min(memory_usages),
                    "current_usage_percent": recent_snapshots[-1].memory_usage_percent
                },
                "cpu": {
                    "avg_usage_percent": sum(cpu_usages) / len(cpu_usages),
                    "max_usage_percent": max(cpu_usages),
                    "min_usage_percent": min(cpu_usages),
                    "current_usage_percent": recent_snapshots[-1].cpu_usage_percent
                },
                "alerts": {
                    "warning_count": sum(1 for s in recent_snapshots if s.alert_level == AlertLevel.WARNING),
                    "critical_count": sum(1 for s in recent_snapshots if s.alert_level == AlertLevel.CRITICAL),
                    "emergency_count": sum(1 for s in recent_snapshots if s.alert_level == AlertLevel.EMERGENCY)
                }
            }
            
        except Exception as e:
            self.logger.error(f"获取资源统计失败: {e}")
            return {"error": str(e)}
    
    def force_memory_cleanup(self):
        """强制内存清理"""
        try:
            self.logger.info("执行强制内存清理")
            
            # Python垃圾回收
            collected = gc.collect()
            self.logger.info(f"垃圾回收释放了 {collected} 个对象")
            
            # 触发调整回调
            for callback in self.adjustment_callbacks:
                try:
                    callback("memory_cleanup", {"collected_objects": collected})
                except Exception as e:
                    self.logger.error(f"调整回调执行失败: {e}")
                    
        except Exception as e:
            self.logger.error(f"强制内存清理失败: {e}")
    
    def _monitor_loop(self, interval: int):
        """监控循环"""
        while self.monitoring:
            try:
                # 获取资源快照
                snapshot = self.get_current_snapshot()
                self.resource_history.append(snapshot)
                
                # 检查警告级别变化
                if snapshot.alert_level != self.current_alert_level:
                    self._handle_alert_level_change(snapshot)
                
                # 检查是否需要自动调整
                self._check_auto_adjustment(snapshot)
                
                # 等待下一次检查
                time.sleep(interval)
                
            except Exception as e:
                self.logger.error(f"监控循环错误: {e}")
                time.sleep(interval)
    
    def _determine_alert_level(self, memory_usage_percent: float) -> AlertLevel:
        """确定警告级别"""
        usage_ratio = memory_usage_percent / 100
        
        if usage_ratio >= self.emergency_threshold:
            return AlertLevel.EMERGENCY
        elif usage_ratio >= self.critical_threshold:
            return AlertLevel.CRITICAL
        elif usage_ratio >= self.warning_threshold:
            return AlertLevel.WARNING
        else:
            return AlertLevel.NORMAL
    
    def _handle_alert_level_change(self, snapshot: ResourceSnapshot):
        """处理警告级别变化"""
        old_level = self.current_alert_level
        new_level = snapshot.alert_level
        
        self.logger.info(f"警告级别变化: {old_level.value} -> {new_level.value}")
        self.current_alert_level = new_level
        
        # 触发警告回调
        for callback in self.alert_callbacks:
            try:
                callback(new_level, snapshot)
            except Exception as e:
                self.logger.error(f"警告回调执行失败: {e}")
    
    def _check_auto_adjustment(self, snapshot: ResourceSnapshot):
        """检查是否需要自动调整"""
        try:
            current_time = time.time()
            
            # 避免频繁调整（至少间隔5分钟）
            if current_time - self.last_adjustment_time < 300:
                return
            
            if snapshot.alert_level == AlertLevel.EMERGENCY:
                self._trigger_emergency_adjustment(snapshot)
                self.last_adjustment_time = current_time
            elif snapshot.alert_level == AlertLevel.CRITICAL:
                self._trigger_critical_adjustment(snapshot)
                self.last_adjustment_time = current_time
                
        except Exception as e:
            self.logger.error(f"自动调整检查失败: {e}")
    
    def _trigger_emergency_adjustment(self, snapshot: ResourceSnapshot):
        """触发紧急调整"""
        self.logger.warning("触发紧急内存调整")
        
        adjustments = [
            ("force_memory_mode", {"reason": "emergency_memory_pressure"}),
            ("emergency_cleanup", {"memory_usage": snapshot.memory_usage_percent}),
            ("disable_concurrent_models", {"force": True})
        ]
        
        for action, params in adjustments:
            for callback in self.adjustment_callbacks:
                try:
                    callback(action, params)
                except Exception as e:
                    self.logger.error(f"紧急调整回调失败: {e}")
    
    def _trigger_critical_adjustment(self, snapshot: ResourceSnapshot):
        """触发关键调整"""
        self.logger.warning("触发关键内存调整")
        
        adjustments = [
            ("gradual_downgrade", {"memory_usage": snapshot.memory_usage_percent}),
            ("reduce_context_length", {"target_reduction": 0.5}),
            ("switch_to_lower_quantization", {"force": False})
        ]
        
        for action, params in adjustments:
            for callback in self.adjustment_callbacks:
                try:
                    callback(action, params)
                except Exception as e:
                    self.logger.error(f"关键调整回调失败: {e}")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "warning_threshold": 0.70,
            "critical_threshold": 0.85,
            "emergency_threshold": 0.90,
            "monitor_interval": 30,
            "auto_adjustment": True,
            "auto_cleanup": True
        }
    
    def _get_fallback_snapshot(self) -> ResourceSnapshot:
        """获取回退快照"""
        return ResourceSnapshot(
            timestamp=time.time(),
            memory_usage_percent=50.0,
            memory_used_gb=2.0,
            memory_available_gb=2.0,
            cpu_usage_percent=20.0,
            gpu_usage_percent=0.0,
            gpu_memory_used_gb=0.0,
            alert_level=AlertLevel.NORMAL
        )


if __name__ == "__main__":
    # 测试资源监控器
    monitor = ResourceMonitor()
    
    def alert_handler(level, snapshot):
        print(f"警告: {level.value} - 内存使用: {snapshot.memory_usage_percent:.1f}%")
    
    def adjustment_handler(action, params):
        print(f"调整: {action} - 参数: {params}")
    
    monitor.add_alert_callback(alert_handler)
    monitor.add_adjustment_callback(adjustment_handler)
    
    monitor.start_monitoring(5)
    
    try:
        time.sleep(30)
    except KeyboardInterrupt:
        pass
    finally:
        monitor.stop_monitoring()
