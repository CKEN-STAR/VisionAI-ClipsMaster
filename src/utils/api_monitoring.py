"""
API性能监控模块

该模块提供API性能监控功能，记录和分析以下关键指标：
1. 请求成功率 - 追踪API请求的成功/失败比率
2. 平均响应时间 - 记录各端点的响应时间统计
3. 资源占用峰值 - 监控API调用期间的内存和CPU使用情况

监控数据支持以下输出方式：
- 日志文件 (通过LogHandler)
- InfluxDB时序数据库 (可选)
- Prometheus指标 (可选)
- 内存中的统计缓存 (用于实时UI展示)
"""

import os
import time
import json
import threading
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
import platform
import psutil

from loguru import logger
from src.utils.log_handler import LogHandler

# 可选依赖 - 如果已安装则导入
try:
    from influxdb_client import InfluxDBClient, Point
    from influxdb_client.client.write_api import SYNCHRONOUS
    INFLUXDB_AVAILABLE = True
except ImportError:
    INFLUXDB_AVAILABLE = False

try:
    from prometheus_client import Counter, Gauge, Histogram, Summary
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False


class APIMonitor:
    """API性能监控类，负责收集、记录和分析API性能指标"""
    
    def __init__(self, influx_config: Optional[Dict[str, Any]] = None):
        """
        初始化API监控器
        
        Args:
            influx_config: InfluxDB配置，包含url、token、org和bucket等字段
                           如果为None，则不使用InfluxDB
        """
        self.log_handler = LogHandler()
        self.metrics_lock = threading.RLock()
        
        # 性能指标内存缓存 - 用于实时统计
        self._metrics_cache = {
            "requests": {},        # 各端点请求计数
            "latencies": {},       # 各端点响应时间列表
            "errors": {},          # 各端点错误计数
            "resources": {         # 资源使用情况
                "memory": [],
                "cpu": []
            },
            "start_time": datetime.now(),
            "last_reset": datetime.now()
        }
        
        # 设置InfluxDB客户端(如果配置了)
        self.influx_client = None
        self.influx_write_api = None
        if influx_config and INFLUXDB_AVAILABLE:
            try:
                self.influx_client = InfluxDBClient(
                    url=influx_config.get("url", "http://localhost:8086"),
                    token=influx_config.get("token", ""),
                    org=influx_config.get("org", "")
                )
                self.influx_write_api = self.influx_client.write_api(write_options=SYNCHRONOUS)
                logger.info("InfluxDB客户端初始化成功")
            except Exception as e:
                logger.error(f"InfluxDB客户端初始化失败: {e}")
        
        # 设置Prometheus指标(如果可用)
        if PROMETHEUS_AVAILABLE:
            # 请求计数器
            self.prom_requests = Counter(
                "api_requests_total", 
                "API请求总数", 
                ["endpoint", "status"]
            )
            
            # 响应时间直方图
            self.prom_latency = Histogram(
                "api_request_latency_seconds",
                "API请求响应时间(秒)",
                ["endpoint"],
                buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10)
            )
            
            # 资源使用量仪表
            self.prom_memory = Gauge(
                "api_memory_usage_bytes",
                "API内存使用量(字节)"
            )
            self.prom_cpu = Gauge(
                "api_cpu_usage_percent",
                "API CPU使用率(%)"
            )
            
            logger.info("Prometheus指标初始化成功")
    
    def track_request(self, path: str, latency: float, status_code: int = 200) -> None:
        """
        记录API请求性能指标
        
        Args:
            path: API路径
            latency: 响应时间(毫秒)
            status_code: HTTP状态码，默认为200
        """
        success = 200 <= status_code < 400
        
        # 记录到日志
        self.log_handler.log_performance_metric(
            metric_name=f"api_{path.replace('/', '_')}",
            value=latency,
            unit="ms"
        )
        
        # 更新内存缓存
        with self.metrics_lock:
            # 初始化该端点的指标(如果不存在)
            if path not in self._metrics_cache["requests"]:
                self._metrics_cache["requests"][path] = {"success": 0, "error": 0}
            if path not in self._metrics_cache["latencies"]:
                self._metrics_cache["latencies"][path] = []
            if path not in self._metrics_cache["errors"]:
                self._metrics_cache["errors"][path] = {}
            
            # 更新请求计数
            if success:
                self._metrics_cache["requests"][path]["success"] += 1
            else:
                self._metrics_cache["requests"][path]["error"] += 1
                error_key = f"{status_code}"
                if error_key not in self._metrics_cache["errors"][path]:
                    self._metrics_cache["errors"][path][error_key] = 0
                self._metrics_cache["errors"][path][error_key] += 1
            
            # 更新响应时间
            self._metrics_cache["latencies"][path].append(latency)
            
            # 限制存储的响应时间样本数量(保留最近1000个)
            if len(self._metrics_cache["latencies"][path]) > 1000:
                self._metrics_cache["latencies"][path] = self._metrics_cache["latencies"][path][-1000:]
        
        # 记录资源使用情况
        self._record_resource_usage()
        
        # 发送到InfluxDB(如果已配置)
        if self.influx_write_api:
            try:
                point = Point("api_performance") \
                    .tag("endpoint", path) \
                    .tag("success", str(success)) \
                    .tag("status_code", str(status_code)) \
                    .field("latency_ms", float(latency)) \
                    .time(datetime.utcnow())
                    
                self.influx_write_api.write(
                    bucket=self.influx_client._bucket,
                    record=point
                )
            except Exception as e:
                logger.error(f"InfluxDB写入失败: {e}")
        
        # 更新Prometheus指标(如果可用)
        if PROMETHEUS_AVAILABLE:
            status_label = "success" if success else "error"
            self.prom_requests.labels(endpoint=path, status=status_label).inc()
            self.prom_latency.labels(endpoint=path).observe(latency / 1000.0)  # 转换为秒
    
    def _record_resource_usage(self) -> None:
        """记录当前资源使用情况"""
        process = psutil.Process(os.getpid())
        
        # 记录内存使用
        memory_bytes = process.memory_info().rss
        
        # 记录CPU使用率
        cpu_percent = process.cpu_percent(interval=0.1)
        
        # 更新内存缓存
        with self.metrics_lock:
            self._metrics_cache["resources"]["memory"].append(memory_bytes)
            self._metrics_cache["resources"]["cpu"].append(cpu_percent)
            
            # 限制存储的资源样本数量(保留最近100个)
            if len(self._metrics_cache["resources"]["memory"]) > 100:
                self._metrics_cache["resources"]["memory"] = self._metrics_cache["resources"]["memory"][-100:]
            if len(self._metrics_cache["resources"]["cpu"]) > 100:
                self._metrics_cache["resources"]["cpu"] = self._metrics_cache["resources"]["cpu"][-100:]
        
        # 更新Prometheus指标(如果可用)
        if PROMETHEUS_AVAILABLE:
            self.prom_memory.set(memory_bytes)
            self.prom_cpu.set(cpu_percent)
    
    def get_statistics(self, time_window: Optional[int] = None) -> Dict[str, Any]:
        """
        获取API性能统计数据
        
        Args:
            time_window: 时间窗口(分钟)，如果提供，则只返回该时间窗口内的统计数据
                         默认为None，返回所有统计数据
        
        Returns:
            包含各种性能指标的字典
        """
        with self.metrics_lock:
            stats = {
                "endpoints": {},
                "system": {
                    "memory": {
                        "current": self._metrics_cache["resources"]["memory"][-1] if self._metrics_cache["resources"]["memory"] else 0,
                        "peak": max(self._metrics_cache["resources"]["memory"]) if self._metrics_cache["resources"]["memory"] else 0,
                        "average": statistics.mean(self._metrics_cache["resources"]["memory"]) if self._metrics_cache["resources"]["memory"] else 0
                    },
                    "cpu": {
                        "current": self._metrics_cache["resources"]["cpu"][-1] if self._metrics_cache["resources"]["cpu"] else 0,
                        "peak": max(self._metrics_cache["resources"]["cpu"]) if self._metrics_cache["resources"]["cpu"] else 0,
                        "average": statistics.mean(self._metrics_cache["resources"]["cpu"]) if self._metrics_cache["resources"]["cpu"] else 0
                    }
                },
                "uptime": (datetime.now() - self._metrics_cache["start_time"]).total_seconds(),
                "time_since_reset": (datetime.now() - self._metrics_cache["last_reset"]).total_seconds()
            }
            
            # 计算各端点的统计数据
            for path in self._metrics_cache["requests"]:
                success_count = self._metrics_cache["requests"][path]["success"]
                error_count = self._metrics_cache["requests"][path]["error"]
                total_count = success_count + error_count
                
                if total_count == 0:
                    continue
                
                latencies = self._metrics_cache["latencies"][path]
                
                stats["endpoints"][path] = {
                    "requests": {
                        "total": total_count,
                        "success": success_count,
                        "error": error_count,
                        "success_rate": success_count / total_count if total_count > 0 else 0
                    },
                    "latency": {
                        "avg": statistics.mean(latencies) if latencies else 0,
                        "min": min(latencies) if latencies else 0,
                        "max": max(latencies) if latencies else 0,
                        "p50": statistics.median(latencies) if latencies else 0,
                        "p95": self._percentile(latencies, 95) if latencies else 0,
                        "p99": self._percentile(latencies, 99) if latencies else 0
                    },
                    "errors": self._metrics_cache["errors"][path]
                }
            
            return stats
    
    def reset_statistics(self) -> None:
        """重置所有统计数据"""
        with self.metrics_lock:
            self._metrics_cache = {
                "requests": {},
                "latencies": {},
                "errors": {},
                "resources": {
                    "memory": [],
                    "cpu": []
                },
                "start_time": self._metrics_cache["start_time"],  # 保留初始启动时间
                "last_reset": datetime.now()
            }
        logger.info("API性能统计数据已重置")
    
    def export_statistics(self, output_path: str) -> bool:
        """
        导出统计数据到JSON文件
        
        Args:
            output_path: 输出文件路径
        
        Returns:
            导出是否成功
        """
        try:
            stats = self.get_statistics()
            
            # 添加导出时间戳
            stats["export_time"] = datetime.now().isoformat()
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=2, ensure_ascii=False)
            
            logger.info(f"API性能统计数据已导出到 {output_path}")
            return True
        except Exception as e:
            logger.error(f"导出API性能统计数据失败: {e}")
            return False
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """
        计算百分位数
        
        Args:
            data: 数据列表
            percentile: 百分位(0-100)
        
        Returns:
            百分位值
        """
        if not data:
            return 0
        
        sorted_data = sorted(data)
        k = (len(sorted_data) - 1) * percentile / 100
        f = int(k)
        c = k - f
        
        if f + 1 < len(sorted_data):
            return sorted_data[f] * (1 - c) + sorted_data[f + 1] * c
        else:
            return sorted_data[f]


# 单例模式实现 - 全局API监控实例
_api_monitor_instance = None

def get_api_monitor(influx_config: Optional[Dict[str, Any]] = None) -> APIMonitor:
    """
    获取APIMonitor实例(单例模式)
    
    Args:
        influx_config: InfluxDB配置(仅在首次调用时有效)
    
    Returns:
        APIMonitor实例
    """
    global _api_monitor_instance
    if _api_monitor_instance is None:
        _api_monitor_instance = APIMonitor(influx_config)
    return _api_monitor_instance 