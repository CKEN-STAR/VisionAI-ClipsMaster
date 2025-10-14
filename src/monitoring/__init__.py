#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
监控模块 - 提供系统监控和告警功能
"""

import psutil
import time
import logging
from enum import Enum
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger("monitoring")


# ==================== 枚举类型 ====================

class AlertLevel(Enum):
    """告警级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertCategory(Enum):
    """告警类别"""
    MEMORY = "memory"
    CPU = "cpu"
    DISK = "disk"
    NETWORK = "network"
    SYSTEM = "system"


# ==================== 数据类 ====================

@dataclass
class MetricData:
    """指标数据"""
    timestamp: float
    value: float
    unit: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Alert:
    """告警信息"""
    level: AlertLevel
    category: AlertCategory
    message: str
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


# ==================== 数据收集器 ====================

class DataCollector:
    """数据收集器"""
    
    def __init__(self):
        self.metrics: Dict[str, List[MetricData]] = {}
        self.max_history = 1000  # 最多保留1000个数据点
        logger.info("DataCollector 初始化完成")
    
    def collect(self, metric_name: str, value: float, unit: str = "", metadata: Dict = None):
        """收集指标数据"""
        if metric_name not in self.metrics:
            self.metrics[metric_name] = []
        
        metric = MetricData(
            timestamp=time.time(),
            value=value,
            unit=unit,
            metadata=metadata or {}
        )
        
        self.metrics[metric_name].append(metric)
        
        # 限制历史数据量
        if len(self.metrics[metric_name]) > self.max_history:
            self.metrics[metric_name] = self.metrics[metric_name][-self.max_history:]
    
    def get_latest(self, metric_name: str) -> Optional[MetricData]:
        """获取最新的指标数据"""
        if metric_name in self.metrics and self.metrics[metric_name]:
            return self.metrics[metric_name][-1]
        return None
    
    def get_history(self, metric_name: str, count: int = 100) -> List[MetricData]:
        """获取历史数据"""
        if metric_name in self.metrics:
            return self.metrics[metric_name][-count:]
        return []
    
    def clear(self, metric_name: Optional[str] = None):
        """清空数据"""
        if metric_name:
            if metric_name in self.metrics:
                self.metrics[metric_name].clear()
        else:
            self.metrics.clear()


# ==================== 告警管理器 ====================

class AlertManager:
    """告警管理器"""
    
    def __init__(self):
        self.alerts: List[Alert] = []
        self.callbacks: List[Callable[[Alert], None]] = []
        self.max_alerts = 500  # 最多保留500条告警
        logger.info("AlertManager 初始化完成")
    
    def add_alert(self, level: AlertLevel, category: AlertCategory, message: str, metadata: Dict = None):
        """添加告警"""
        alert = Alert(
            level=level,
            category=category,
            message=message,
            metadata=metadata or {}
        )
        
        self.alerts.append(alert)
        
        # 限制告警数量
        if len(self.alerts) > self.max_alerts:
            self.alerts = self.alerts[-self.max_alerts:]
        
        # 触发回调
        for callback in self.callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"告警回调执行失败: {e}")
        
        logger.info(f"[{level.value.upper()}] {category.value}: {message}")
    
    def register_callback(self, callback: Callable[[Alert], None]):
        """注册告警回调"""
        if callback not in self.callbacks:
            self.callbacks.append(callback)
    
    def unregister_callback(self, callback: Callable[[Alert], None]):
        """注销告警回调"""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
    
    def get_alerts(self, level: Optional[AlertLevel] = None, category: Optional[AlertCategory] = None, count: int = 100) -> List[Alert]:
        """获取告警列表"""
        filtered = self.alerts
        
        if level:
            filtered = [a for a in filtered if a.level == level]
        
        if category:
            filtered = [a for a in filtered if a.category == category]
        
        return filtered[-count:]
    
    def clear_alerts(self):
        """清空告警"""
        self.alerts.clear()


# ==================== 指标收集器 ====================

class MetricsCollector:
    """系统指标收集器"""
    
    def __init__(self):
        self.data_collector = DataCollector()
        self.alert_manager = AlertManager()
        self.running = False
        logger.info("MetricsCollector 初始化完成")
    
    def collect_memory_metrics(self):
        """收集内存指标"""
        try:
            mem = psutil.virtual_memory()
            self.data_collector.collect("memory_percent", mem.percent, "%")
            self.data_collector.collect("memory_used", mem.used / (1024**3), "GB")
            self.data_collector.collect("memory_available", mem.available / (1024**3), "GB")
            
            # 检查内存使用率
            if mem.percent > 90:
                self.alert_manager.add_alert(
                    AlertLevel.CRITICAL,
                    AlertCategory.MEMORY,
                    f"内存使用率过高: {mem.percent:.1f}%"
                )
            elif mem.percent > 80:
                self.alert_manager.add_alert(
                    AlertLevel.WARNING,
                    AlertCategory.MEMORY,
                    f"内存使用率较高: {mem.percent:.1f}%"
                )
        except Exception as e:
            logger.error(f"收集内存指标失败: {e}")
    
    def collect_cpu_metrics(self):
        """收集CPU指标"""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            self.data_collector.collect("cpu_percent", cpu_percent, "%")
            
            # 检查CPU使用率
            if cpu_percent > 90:
                self.alert_manager.add_alert(
                    AlertLevel.WARNING,
                    AlertCategory.CPU,
                    f"CPU使用率过高: {cpu_percent:.1f}%"
                )
        except Exception as e:
            logger.error(f"收集CPU指标失败: {e}")
    
    def collect_disk_metrics(self):
        """收集磁盘指标"""
        try:
            disk = psutil.disk_usage('/')
            self.data_collector.collect("disk_percent", disk.percent, "%")
            self.data_collector.collect("disk_free", disk.free / (1024**3), "GB")
            
            # 检查磁盘使用率
            if disk.percent > 95:
                self.alert_manager.add_alert(
                    AlertLevel.CRITICAL,
                    AlertCategory.DISK,
                    f"磁盘空间不足: {disk.percent:.1f}%"
                )
            elif disk.percent > 85:
                self.alert_manager.add_alert(
                    AlertLevel.WARNING,
                    AlertCategory.DISK,
                    f"磁盘空间较少: {disk.percent:.1f}%"
                )
        except Exception as e:
            logger.error(f"收集磁盘指标失败: {e}")
    
    def collect_all_metrics(self):
        """收集所有指标"""
        self.collect_memory_metrics()
        self.collect_cpu_metrics()
        self.collect_disk_metrics()


# ==================== 全局实例 ====================

_metrics_collector: Optional[MetricsCollector] = None
_data_collector: Optional[DataCollector] = None
_alert_manager: Optional[AlertManager] = None


def get_metrics_collector() -> MetricsCollector:
    """获取全局指标收集器"""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


def get_collector() -> DataCollector:
    """获取全局数据收集器"""
    global _data_collector
    if _data_collector is None:
        _data_collector = DataCollector()
    return _data_collector


def get_alert_manager() -> AlertManager:
    """获取全局告警管理器"""
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager()
    return _alert_manager


# ==================== 工具函数 ====================

def check_memory_usage() -> Dict[str, Any]:
    """检查内存使用情况"""
    try:
        mem = psutil.virtual_memory()
        return {
            "total": mem.total / (1024**3),  # GB
            "used": mem.used / (1024**3),    # GB
            "available": mem.available / (1024**3),  # GB
            "percent": mem.percent,
            "status": "critical" if mem.percent > 90 else "warning" if mem.percent > 80 else "normal"
        }
    except Exception as e:
        logger.error(f"检查内存使用失败: {e}")
        return {
            "total": 0,
            "used": 0,
            "available": 0,
            "percent": 0,
            "status": "error",
            "error": str(e)
        }


# ==================== 导出 ====================

__all__ = [
    # 枚举
    "AlertLevel",
    "AlertCategory",
    # 数据类
    "MetricData",
    "Alert",
    # 类
    "DataCollector",
    "AlertManager",
    "MetricsCollector",
    # 全局实例获取函数
    "get_metrics_collector",
    "get_collector",
    "get_alert_manager",
    # 工具函数
    "check_memory_usage",
]

