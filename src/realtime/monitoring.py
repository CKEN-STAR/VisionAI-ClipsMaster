#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
全链路监控看板

提供实时通信组件的性能指标收集、分析和可视化功能，
支持多种监控后端和告警机制。
"""

import os
import json
import time
import asyncio
import threading
import statistics
import datetime
import logging
from typing import Dict, List, Any, Optional, Tuple, Union, Callable

# 配置日志
logger = logging.getLogger(__name__)

# 尝试导入可选依赖
try:
    import prometheus_client
    from prometheus_client import Counter, Gauge, Histogram, Summary
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logger.warning("未安装prometheus_client，Prometheus指标将不可用")

try:
    import grafana_client
    GRAFANA_AVAILABLE = True
except ImportError:
    GRAFANA_AVAILABLE = False
    logger.warning("未安装grafana_client，Grafana集成将不可用")


class PrometheusClient:
    """Prometheus客户端
    
    管理Prometheus指标收集和导出。
    """
    
    def __init__(self):
        """初始化Prometheus客户端"""
        self.metrics: Dict[str, Any] = {}
        
        if not PROMETHEUS_AVAILABLE:
            logger.warning("Prometheus客户端初始化失败：缺少依赖")
            return
        
        # 初始化通用指标
        
        # 连接计数器
        self.metrics["ws_connections"] = Gauge(
            "visionai_ws_connections", 
            "WebSocket连接数",
            ["status"]
        )
        
        # 通信延迟
        self.metrics["avg_latency_ms"] = Gauge(
            "visionai_avg_latency_ms",
            "平均通信延迟(毫秒)"
        )
        
        # 消息计数器
        self.metrics["messages"] = Counter(
            "visionai_messages_total",
            "消息总数",
            ["direction", "type", "status"]
        )
        
        # 带宽使用
        self.metrics["bandwidth"] = Counter(
            "visionai_bandwidth_bytes_total",
            "带宽使用(字节)",
            ["direction"]
        )
        
        # 错误计数器
        self.metrics["errors"] = Counter(
            "visionai_errors_total",
            "错误总数",
            ["component", "severity"]
        )
        
        # 实时会话指标
        self.metrics["active_sessions"] = Gauge(
            "visionai_active_sessions",
            "活跃会话数"
        )
        
        # 资源使用
        self.metrics["memory_usage"] = Gauge(
            "visionai_memory_usage_bytes",
            "内存使用(字节)"
        )
        
        self.metrics["cpu_usage"] = Gauge(
            "visionai_cpu_usage_percent",
            "CPU使用率(%)"
        )
        
        # 任务队列
        self.metrics["queue_size"] = Gauge(
            "visionai_queue_size",
            "任务队列大小",
            ["queue_name"]
        )
        
        # 请求延迟
        self.metrics["request_latency"] = Histogram(
            "visionai_request_latency_seconds",
            "请求延迟(秒)",
            ["operation"],
            buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5)
        )
        
        logger.info("Prometheus客户端初始化成功")
    
    def update_connection_count(self, status: str, count: int) -> None:
        """更新连接计数
        
        Args:
            status: 连接状态(active/idle/total)
            count: 连接数量
        """
        if not PROMETHEUS_AVAILABLE:
            return
            
        self.metrics["ws_connections"].labels(status=status).set(count)
    
    def set_latency(self, latency_ms: float) -> None:
        """设置平均延迟
        
        Args:
            latency_ms: 平均延迟(毫秒)
        """
        if not PROMETHEUS_AVAILABLE:
            return
            
        self.metrics["avg_latency_ms"].set(latency_ms)
    
    def increment_messages(self, direction: str, msg_type: str, status: str = "success") -> None:
        """增加消息计数
        
        Args:
            direction: 消息方向(incoming/outgoing)
            msg_type: 消息类型
            status: 消息状态(success/error)
        """
        if not PROMETHEUS_AVAILABLE:
            return
            
        self.metrics["messages"].labels(direction=direction, type=msg_type, status=status).inc()
    
    def add_bandwidth(self, direction: str, bytes_count: int) -> None:
        """添加带宽使用量
        
        Args:
            direction: 数据方向(incoming/outgoing)
            bytes_count: 字节数
        """
        if not PROMETHEUS_AVAILABLE:
            return
            
        self.metrics["bandwidth"].labels(direction=direction).inc(bytes_count)
    
    def increment_error(self, component: str, severity: str = "error") -> None:
        """增加错误计数
        
        Args:
            component: 发生错误的组件
            severity: 错误严重程度(warning/error/critical)
        """
        if not PROMETHEUS_AVAILABLE:
            return
            
        self.metrics["errors"].labels(component=component, severity=severity).inc()
    
    def set_active_sessions(self, count: int) -> None:
        """设置活跃会话数
        
        Args:
            count: 活跃会话数
        """
        if not PROMETHEUS_AVAILABLE:
            return
            
        self.metrics["active_sessions"].set(count)
    
    def set_resource_usage(self, memory_bytes: int, cpu_percent: float) -> None:
        """设置资源使用情况
        
        Args:
            memory_bytes: 内存使用(字节)
            cpu_percent: CPU使用率(%)
        """
        if not PROMETHEUS_AVAILABLE:
            return
            
        self.metrics["memory_usage"].set(memory_bytes)
        self.metrics["cpu_usage"].set(cpu_percent)
    
    def set_queue_size(self, queue_name: str, size: int) -> None:
        """设置队列大小
        
        Args:
            queue_name: 队列名称
            size: 队列大小
        """
        if not PROMETHEUS_AVAILABLE:
            return
            
        self.metrics["queue_size"].labels(queue_name=queue_name).set(size)
    
    def observe_latency(self, operation: str, seconds: float) -> None:
        """观察请求延迟
        
        Args:
            operation: 操作名称
            seconds: 延迟时间(秒)
        """
        if not PROMETHEUS_AVAILABLE:
            return
            
        self.metrics["request_latency"].labels(operation=operation).observe(seconds)
    
    def query(self, metric_name: str, **labels) -> Optional[float]:
        """查询指标当前值
        
        Args:
            metric_name: 指标名称
            **labels: 标签键值对
        
        Returns:
            Optional[float]: 指标值，不存在则返回None
        """
        if not PROMETHEUS_AVAILABLE:
            return None
            
        if metric_name not in self.metrics:
            logger.warning(f"未知指标: {metric_name}")
            return None
            
        try:
            # 尝试获取指标值
            if hasattr(self.metrics[metric_name], "_value"):
                # Gauge/Counter等简单类型
                return self.metrics[metric_name]._value
            elif labels and hasattr(self.metrics[metric_name], "labels"):
                # 带标签的指标
                labeled_metric = self.metrics[metric_name].labels(**labels)
                return labeled_metric._value
            else:
                logger.warning(f"无法读取指标: {metric_name}")
                return None
        except Exception as e:
            logger.error(f"查询指标出错: {e}")
            return None


class GrafanaIntegrator:
    """Grafana集成器
    
    提供与Grafana的集成，管理仪表盘和面板。
    """
    
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        """初始化Grafana集成器
        
        Args:
            base_url: Grafana API基础URL
            api_key: Grafana API密钥
        """
        self.base_url = base_url or "http://localhost:3000"
        self.api_key = api_key
        self.client = None
        
        if not GRAFANA_AVAILABLE:
            logger.warning("Grafana集成初始化失败：缺少依赖")
            return
            
        if api_key:
            try:
                self.client = grafana_client.GrafanaApi(
                    auth=api_key,
                    host=self.base_url
                )
                logger.info("Grafana客户端初始化成功")
            except Exception as e:
                logger.error(f"Grafana客户端初始化失败: {e}")
    
    def get_panel(self, panel_id: str) -> Optional[Dict[str, Any]]:
        """获取面板数据
        
        Args:
            panel_id: 面板ID
        
        Returns:
            Optional[Dict[str, Any]]: 面板数据，失败则返回None
        """
        if not GRAFANA_AVAILABLE or not self.client:
            return None
            
        try:
            # 此处简化实现，实际需要通过Grafana API获取
            panel_data = {"id": panel_id, "data": "面板数据示例"}
            return panel_data
        except Exception as e:
            logger.error(f"获取Grafana面板失败: {e}")
            return None


class TelemetryDashboard:
    """遥测仪表盘
    
    收集、分析和可视化各个组件的性能指标。
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化遥测仪表盘
        
        Args:
            config: 配置字典
        """
        self.config = config or {}
        
        # 初始化各监控客户端
        self.prometheus = PrometheusClient()
        
        # 初始化Grafana集成
        grafana_config = self.config.get("grafana", {})
        self.grafana = GrafanaIntegrator(
            base_url=grafana_config.get("url"),
            api_key=grafana_config.get("api_key")
        )
        
        # 指标缓存
        self.metrics_cache = {
            "connections": {
                "active": 0,
                "idle": 0,
                "total": 0
            },
            "latency": {
                "values": [],
                "avg": 0,
                "min": 0,
                "max": 0,
                "p95": 0,
                "p99": 0
            },
            "messages": {
                "incoming": 0,
                "outgoing": 0,
                "total": 0
            },
            "bandwidth": {
                "incoming": 0,
                "outgoing": 0,
                "total": 0
            },
            "errors": {
                "total": 0,
                "by_component": {}
            },
            "sessions": {
                "active": 0,
                "total": 0
            },
            "resources": {
                "memory": 0,
                "cpu": 0
            },
            "queues": {},
            "start_time": time.time(),
            "last_update": time.time()
        }
        
        # 更新线程
        self.update_thread = None
        self.stop_event = threading.Event()
        
        logger.info("遥测仪表盘初始化完成")
    
    def start_background_collection(self, interval_seconds: float = 5.0) -> None:
        """启动后台指标收集
        
        Args:
            interval_seconds: 收集间隔(秒)
        """
        if self.update_thread and self.update_thread.is_alive():
            logger.warning("后台收集线程已在运行")
            return
            
        self.stop_event.clear()
        
        def update_loop():
            while not self.stop_event.is_set():
                try:
                    # 收集资源使用情况
                    import psutil
                    process = psutil.Process(os.getpid())
                    memory_bytes = process.memory_info().rss
                    cpu_percent = process.cpu_percent(interval=0.1)
                    
                    # 更新资源使用指标
                    self.metrics_cache["resources"]["memory"] = memory_bytes
                    self.metrics_cache["resources"]["cpu"] = cpu_percent
                    
                    # 更新Prometheus指标
                    self.prometheus.set_resource_usage(memory_bytes, cpu_percent)
                    
                    # 更新最后更新时间
                    self.metrics_cache["last_update"] = time.time()
                except Exception as e:
                    logger.error(f"指标收集出错: {e}")
                
                time.sleep(interval_seconds)
        
        self.update_thread = threading.Thread(target=update_loop, daemon=True)
        self.update_thread.start()
        logger.info(f"后台指标收集已启动，间隔: {interval_seconds}秒")
    
    def stop_background_collection(self) -> None:
        """停止后台指标收集"""
        if self.update_thread and self.update_thread.is_alive():
            self.stop_event.set()
            self.update_thread.join(timeout=5.0)
            logger.info("后台指标收集已停止")
    
    def update_connection_metrics(self, active: int, idle: int) -> None:
        """更新连接指标
        
        Args:
            active: 活跃连接数
            idle: 空闲连接数
        """
        total = active + idle
        
        # 更新缓存
        self.metrics_cache["connections"]["active"] = active
        self.metrics_cache["connections"]["idle"] = idle
        self.metrics_cache["connections"]["total"] = total
        
        # 更新Prometheus指标
        self.prometheus.update_connection_count("active", active)
        self.prometheus.update_connection_count("idle", idle)
        self.prometheus.update_connection_count("total", total)
    
    def record_latency(self, latency_ms: float) -> None:
        """记录延迟数据
        
        Args:
            latency_ms: 延迟时间(毫秒)
        """
        # 更新缓存
        self.metrics_cache["latency"]["values"].append(latency_ms)
        
        # 保留最近1000个值
        if len(self.metrics_cache["latency"]["values"]) > 1000:
            self.metrics_cache["latency"]["values"] = self.metrics_cache["latency"]["values"][-1000:]
        
        # 计算统计信息
        values = self.metrics_cache["latency"]["values"]
        if values:
            self.metrics_cache["latency"]["avg"] = sum(values) / len(values)
            self.metrics_cache["latency"]["min"] = min(values)
            self.metrics_cache["latency"]["max"] = max(values)
            
            # 计算百分位数
            sorted_values = sorted(values)
            self.metrics_cache["latency"]["p95"] = sorted_values[int(len(sorted_values) * 0.95)]
            self.metrics_cache["latency"]["p99"] = sorted_values[int(len(sorted_values) * 0.99)]
        
        # 更新Prometheus指标
        self.prometheus.set_latency(self.metrics_cache["latency"]["avg"])
    
    def record_message(self, direction: str, size_bytes: int, msg_type: str = "data") -> None:
        """记录消息
        
        Args:
            direction: 消息方向(incoming/outgoing)
            size_bytes: 消息大小(字节)
            msg_type: 消息类型
        """
        # 检查方向参数
        if direction not in ["incoming", "outgoing"]:
            logger.warning(f"无效的消息方向: {direction}")
            return
            
        # 更新缓存
        self.metrics_cache["messages"][direction] += 1
        self.metrics_cache["messages"]["total"] += 1
        self.metrics_cache["bandwidth"][direction] += size_bytes
        self.metrics_cache["bandwidth"]["total"] += size_bytes
        
        # 更新Prometheus指标
        self.prometheus.increment_messages(direction, msg_type)
        self.prometheus.add_bandwidth(direction, size_bytes)
    
    def record_error(self, component: str, severity: str = "error") -> None:
        """记录错误
        
        Args:
            component: 发生错误的组件
            severity: 错误严重程度(warning/error/critical)
        """
        # 更新缓存
        self.metrics_cache["errors"]["total"] += 1
        
        if component not in self.metrics_cache["errors"]["by_component"]:
            self.metrics_cache["errors"]["by_component"][component] = 0
        
        self.metrics_cache["errors"]["by_component"][component] += 1
        
        # 更新Prometheus指标
        self.prometheus.increment_error(component, severity)
    
    def update_session_count(self, active: int, total: int = None) -> None:
        """更新会话计数
        
        Args:
            active: 活跃会话数
            total: 总会话数，如果为None则不更新
        """
        # 更新缓存
        self.metrics_cache["sessions"]["active"] = active
        if total is not None:
            self.metrics_cache["sessions"]["total"] = total
        
        # 更新Prometheus指标
        self.prometheus.set_active_sessions(active)
    
    def update_queue_size(self, queue_name: str, size: int) -> None:
        """更新队列大小
        
        Args:
            queue_name: 队列名称
            size: 队列大小
        """
        # 更新缓存
        self.metrics_cache["queues"][queue_name] = size
        
        # 更新Prometheus指标
        self.prometheus.set_queue_size(queue_name, size)
    
    def display_realtime_metrics(self) -> Dict[str, Any]:
        """获取实时指标数据用于展示
        
        Returns:
            Dict[str, Any]: 实时指标数据
        """
        uptime_seconds = time.time() - self.metrics_cache["start_time"]
        last_update_seconds = time.time() - self.metrics_cache["last_update"]
        
        metrics = {
            "connections": self.metrics_cache["connections"],
            "latency": self.metrics_cache["latency"],
            "messages": self.metrics_cache["messages"],
            "bandwidth": self.metrics_cache["bandwidth"],
            "errors": self.metrics_cache["errors"],
            "sessions": self.metrics_cache["sessions"],
            "resources": self.metrics_cache["resources"],
            "queues": self.metrics_cache["queues"],
            "uptime": uptime_seconds,
            "last_update": last_update_seconds
        }
        
        # 添加Prometheus指标
        metrics["prometheus"] = {
            "ws_connections": self.prometheus.query("ws_connections"),
            "avg_latency_ms": self.prometheus.query("avg_latency_ms"),
            "error_rate": self.prometheus.query("error_rate")
        }
        
        # 添加Grafana面板
        metrics["grafana"] = {
            "error_rate": self.grafana.get_panel("error_rate")
        }
        
        return metrics


# 全局单例
_dashboard_instance = None
_dashboard_lock = threading.Lock()

def get_telemetry_dashboard() -> TelemetryDashboard:
    """获取遥测仪表盘实例
    
    Returns:
        TelemetryDashboard: 遥测仪表盘实例
    """
    global _dashboard_instance
    
    if _dashboard_instance is None:
        with _dashboard_lock:
            if _dashboard_instance is None:
                # 尝试加载配置
                config = None
                config_path = os.path.join("configs", "monitoring.json")
                if os.path.exists(config_path):
                    try:
                        with open(config_path, "r", encoding="utf-8") as f:
                            config = json.load(f)
                    except Exception as e:
                        logger.error(f"加载监控配置失败: {str(e)}")
                
                _dashboard_instance = TelemetryDashboard(config)
                _dashboard_instance.start_background_collection()
    
    return _dashboard_instance

async def initialize_telemetry_dashboard(config: Optional[Dict[str, Any]] = None) -> TelemetryDashboard:
    """初始化遥测仪表盘
    
    Args:
        config: 配置字典，不提供则使用默认配置
    
    Returns:
        TelemetryDashboard: 遥测仪表盘实例
    """
    global _dashboard_instance
    
    with _dashboard_lock:
        if _dashboard_instance is not None:
            _dashboard_instance.stop_background_collection()
        
        _dashboard_instance = TelemetryDashboard(config)
        _dashboard_instance.start_background_collection()
    
    return _dashboard_instance 