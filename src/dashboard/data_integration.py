#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
多维度数据源集成模块

该模块集成和聚合来自不同系统组件的监控数据，包括内存使用、缓存状态、
模型性能和系统资源指标，提供统一的数据接口用于混沌工程测试分析。
采用轻量级设计，适合在4GB RAM无GPU环境中运行。
"""

import os
import sys
import time
import json
import logging
import threading
import traceback
from typing import Dict, List, Any, Optional, Union, Set, Tuple
from datetime import datetime, timedelta
from functools import lru_cache
from pathlib import Path

# 创建日志记录器
logger = logging.getLogger("data_integration")

# 尝试导入各种监控客户端
try:
    import psutil
    has_psutil = True
except ImportError:
    has_psutil = False
    logger.warning("psutil库未安装，系统指标收集将受限")

try:
    import prometheus_client as prom
    from prometheus_client.parser import text_string_to_metric_families
    has_prometheus = True
except ImportError:
    has_prometheus = False
    logger.warning("prometheus_client库未安装，Prometheus指标收集将不可用")

try:
    import redis
    has_redis = True
except ImportError:
    has_redis = False
    logger.warning("redis库未安装，Redis缓存监控将不可用")


class PrometheusClient:
    """Prometheus客户端，用于从Prometheus服务器获取内存和系统指标"""
    
    def __init__(self, url="http://prom:9090"):
        """初始化Prometheus客户端
        
        Args:
            url: Prometheus服务器URL
        """
        self.url = url
        self.client = None
        self.logger = logging.getLogger("prometheus_client")
        self.connected = False
        
        if not has_prometheus:
            self.logger.warning("未安装prometheus_client库，功能将受限")
            return
            
        try:
            # 创建无状态客户端
            self.connected = True
            self.logger.info(f"Prometheus客户端已初始化: {url}")
        except Exception as e:
            self.logger.error(f"初始化Prometheus客户端失败: {e}")
            
    def scrape(self) -> Dict[str, Any]:
        """获取Prometheus指标
        
        Returns:
            Dict: Prometheus指标数据
        """
        if not has_prometheus or not self.connected:
            return self._fallback_metrics()
            
        try:
            # 使用HTTP请求获取指标值
            import requests
            resp = requests.get(f"{self.url}/api/v1/query", 
                              params={"query": "process_resident_memory_bytes"})
            
            if resp.status_code != 200:
                raise ValueError(f"获取Prometheus指标失败: {resp.status_code}")
                
            data = resp.json()
            mem_metrics = {}
            
            # 解析结果
            if "data" in data and "result" in data["data"]:
                for result in data["data"]["result"]:
                    if "metric" in result and "value" in result:
                        name = result["metric"].get("name", "unknown")
                        value = float(result["value"][1]) / (1024 * 1024)  # 转换为MB
                        mem_metrics[name] = value
            
            # 获取CPU指标
            resp = requests.get(f"{self.url}/api/v1/query", 
                              params={"query": "process_cpu_seconds_total"})
            
            if resp.status_code == 200:
                data = resp.json()
                if "data" in data and "result" in data["data"]:
                    for result in data["data"]["result"]:
                        if "metric" in result and "value" in result:
                            name = result["metric"].get("name", "unknown")
                            value = float(result["value"][1])
                            mem_metrics[f"{name}_cpu"] = value
            
            return {
                "memory_metrics": mem_metrics,
                "status": "ok"
            }
            
        except Exception as e:
            self.logger.error(f"获取Prometheus指标失败: {e}")
            return self._fallback_metrics()
    
    def _fallback_metrics(self) -> Dict[str, Any]:
        """提供备用指标，当无法连接Prometheus时使用
        
        Returns:
            Dict: 备用指标数据
        """
        metrics = {}
        
        if has_psutil:
            process = psutil.Process(os.getpid())
            metrics["fallback_process_rss"] = process.memory_info().rss / (1024 * 1024)  # MB
            metrics["fallback_system_mem_used"] = psutil.virtual_memory().used / (1024 * 1024)  # MB
            metrics["fallback_cpu_percent"] = process.cpu_percent(interval=0.1)
            
        return {
            "memory_metrics": metrics,
            "status": "fallback"
        }


class RedisMonitor:
    """Redis监控器，用于监控Redis缓存状态和性能"""
    
    def __init__(self, host="redis", port=6379, db=0, password=None):
        """初始化Redis监控器
        
        Args:
            host: Redis服务器主机名
            port: Redis服务器端口
            db: Redis数据库编号
            password: Redis认证密码（如有）
        """
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.client = None
        self.logger = logging.getLogger("redis_monitor")
        self.connected = False
        
        if not has_redis:
            self.logger.warning("未安装redis库，功能将受限")
            return
            
        try:
            # 初始化Redis客户端
            self.client = redis.Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                socket_timeout=2.0,  # 短超时，确保不阻塞
                socket_connect_timeout=2.0
            )
            
            # 测试连接
            self.client.ping()
            self.connected = True
            self.logger.info(f"Redis监控器已连接: {host}:{port}")
        except Exception as e:
            self.logger.error(f"连接Redis服务器失败: {e}")
    
    def scrape(self) -> Dict[str, Any]:
        """获取Redis缓存指标
        
        Returns:
            Dict: Redis指标数据
        """
        if not has_redis or not self.connected:
            return self._fallback_metrics()
            
        try:
            # 获取Redis INFO统计
            info = self.client.info()
            
            # 提取关键指标
            cache_metrics = {
                "used_memory_mb": int(info.get("used_memory", 0)) / (1024 * 1024),
                "used_memory_rss_mb": int(info.get("used_memory_rss", 0)) / (1024 * 1024),
                "connected_clients": info.get("connected_clients", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "evicted_keys": info.get("evicted_keys", 0),
                "expired_keys": info.get("expired_keys", 0),
                "uptime_seconds": info.get("uptime_in_seconds", 0)
            }
            
            # 计算命中率
            hits = cache_metrics["keyspace_hits"]
            misses = cache_metrics["keyspace_misses"]
            total = hits + misses
            
            if total > 0:
                cache_metrics["hit_rate"] = hits / total
            else:
                cache_metrics["hit_rate"] = 0.0
            
            return {
                "cache_metrics": cache_metrics,
                "status": "ok"
            }
            
        except Exception as e:
            self.logger.error(f"获取Redis指标失败: {e}")
            return self._fallback_metrics()
    
    def _fallback_metrics(self) -> Dict[str, Any]:
        """提供备用缓存指标
        
        Returns:
            Dict: 备用缓存指标
        """
        # 从项目内部缓存管理获取信息
        from src.cache import optimizer
        
        try:
            cache_stats = optimizer.get_cache_stats()
            
            return {
                "cache_metrics": {
                    "used_memory_mb": cache_stats.get("memory_usage_mb", 0),
                    "hit_rate": cache_stats.get("hit_rate", 0),
                    "evicted_keys": cache_stats.get("eviction_count", 0),
                    "expired_keys": cache_stats.get("expired_count", 0)
                },
                "status": "fallback"
            }
        except Exception:
            return {
                "cache_metrics": {
                    "used_memory_mb": 0,
                    "hit_rate": 0,
                    "evicted_keys": 0,
                    "expired_keys": 0
                },
                "status": "error"
            }


class ModelProfiler:
    """模型性能分析器，收集模型加载和推理性能指标"""
    
    def __init__(self):
        """初始化模型性能分析器"""
        self.logger = logging.getLogger("model_profiler")
        self.models_info = {}
        
        # 尝试加载现有的模型性能数据
        self._load_from_file()
    
    def _load_from_file(self):
        """从文件加载模型性能数据"""
        profile_path = Path("logs/models/performance.json")
        
        if not profile_path.exists():
            return
            
        try:
            with open(profile_path, "r", encoding="utf-8") as f:
                self.models_info = json.load(f)
        except Exception as e:
            self.logger.error(f"加载模型性能数据失败: {e}")
    
    def scrape(self) -> Dict[str, Any]:
        """获取模型性能指标
        
        Returns:
            Dict: 模型性能指标
        """
        # 尝试从监控模块获取数据
        try:
            from src.monitoring.data_collector import get_collector
            collector = get_collector()
            
            # 获取所有模型的性能数据
            models_data = {}
            for model_name in self.models_info.keys():
                model_perf = collector.get_model_performance(model_name)
                if model_perf:
                    models_data[model_name] = model_perf
                    
            # 如果没有数据，使用内部记录的数据
            if not models_data:
                models_data = self.models_info
                
            return {
                "model_metrics": models_data,
                "status": "ok" if models_data else "no_data"
            }
            
        except Exception as e:
            self.logger.error(f"获取模型性能指标失败: {e}")
            return {
                "model_metrics": self.models_info,
                "status": "fallback"
            }
            
    def record_inference(self, model_name: str, inference_time_ms: float):
        """记录模型推理性能
        
        Args:
            model_name: 模型名称
            inference_time_ms: 推理时间(毫秒)
        """
        if model_name not in self.models_info:
            self.models_info[model_name] = {
                "inference_times": [],
                "load_times": [],
                "avg_inference_ms": 0,
                "p95_inference_ms": 0,
                "avg_load_ms": 0
            }
        
        # 添加推理时间记录
        self.models_info[model_name]["inference_times"].append({
            "time_ms": inference_time_ms,
            "timestamp": time.time()
        })
        
        # 限制记录数量
        if len(self.models_info[model_name]["inference_times"]) > 100:
            self.models_info[model_name]["inference_times"].pop(0)
            
        # 更新统计信息
        times = [record["time_ms"] for record in self.models_info[model_name]["inference_times"]]
        if times:
            self.models_info[model_name]["avg_inference_ms"] = sum(times) / len(times)
            times.sort()
            p95_index = int(len(times) * 0.95)
            self.models_info[model_name]["p95_inference_ms"] = times[p95_index] if p95_index < len(times) else times[-1]


class OSStatsCollector:
    """操作系统统计信息收集器，收集系统级资源使用情况"""
    
    def __init__(self):
        """初始化操作系统统计信息收集器"""
        self.logger = logging.getLogger("os_stats_collector")
        
        if not has_psutil:
            self.logger.warning("未安装psutil库，系统统计功能将受限")
    
    def scrape(self) -> Dict[str, Any]:
        """获取系统统计信息
        
        Returns:
            Dict: 系统统计信息
        """
        stats = {}
        
        if not has_psutil:
            return {
                "system_metrics": {},
                "status": "unavailable"
            }
            
        try:
            # 获取物理内存信息
            virtual_memory = psutil.virtual_memory()
            swap_memory = psutil.swap_memory()
            
            # 获取CPU信息
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_freq = psutil.cpu_freq()
            
            # 获取磁盘信息
            disk_usage = psutil.disk_usage('/')
            disk_io = psutil.disk_io_counters()
            
            # 获取网络信息
            net_io = psutil.net_io_counters()
            
            # 构建系统指标
            stats = {
                "memory": {
                    "total_mb": virtual_memory.total / (1024 * 1024),
                    "available_mb": virtual_memory.available / (1024 * 1024),
                    "used_mb": virtual_memory.used / (1024 * 1024),
                    "percent": virtual_memory.percent,
                    "swap_total_mb": swap_memory.total / (1024 * 1024),
                    "swap_used_mb": swap_memory.used / (1024 * 1024),
                    "swap_percent": swap_memory.percent
                },
                "cpu": {
                    "percent": cpu_percent,
                    "count": psutil.cpu_count(),
                    "freq_mhz": cpu_freq.current if cpu_freq else None
                },
                "disk": {
                    "total_gb": disk_usage.total / (1024 * 1024 * 1024),
                    "used_gb": disk_usage.used / (1024 * 1024 * 1024),
                    "percent": disk_usage.percent,
                    "read_mb": disk_io.read_bytes / (1024 * 1024),
                    "write_mb": disk_io.write_bytes / (1024 * 1024)
                },
                "network": {
                    "bytes_sent_mb": net_io.bytes_sent / (1024 * 1024),
                    "bytes_recv_mb": net_io.bytes_recv / (1024 * 1024),
                    "packets_sent": net_io.packets_sent,
                    "packets_recv": net_io.packets_recv,
                    "errin": net_io.errin,
                    "errout": net_io.errout
                },
                "process": {
                    "timestamp": time.time(),
                    "hostname": os.uname().nodename if hasattr(os, 'uname') else platform.node()
                }
            }
            
            return {
                "system_metrics": stats,
                "status": "ok"
            }
            
        except Exception as e:
            self.logger.error(f"获取系统统计信息失败: {e}")
            return {
                "system_metrics": {},
                "status": "error",
                "error": str(e)
            }


class DataAggregator:
    """数据聚合器，集成多个数据源并提供统一查询接口"""
    
    SOURCES = {
        "memory": PrometheusClient(url="http://prom:9090"),
        "cache": RedisMonitor(host="redis"),
        "models": ModelProfiler(),
        "system": OSStatsCollector()
    }
    
    def __init__(self):
        """初始化数据聚合器"""
        self.logger = logging.getLogger("data_aggregator")
        
        # 最近一次抓取的数据
        self.last_fetch = {}
        
        # 数据源连接状态
        self.source_status = {src: False for src in self.SOURCES.keys()}
        
        # 自动更新数据线程
        self.update_thread = None
        self.should_stop = False
        
        # 源数据缓存
        self._data_cache = {}
        self._cache_timestamp = {}
        self._cache_lock = threading.RLock()
        
        # 健康状态检查
        self.health_status = self._check_health()
    
    def fetch_realtime_data(self) -> Dict[str, Any]:
        """聚合多源实时数据
        
        Returns:
            Dict: 聚合后的实时数据
        """
        return {name: source.scrape() for name, source in self.SOURCES.items()}
    
    def get_source_status(self, source_name: str) -> Dict[str, Any]:
        """获取特定数据源的状态
        
        Args:
            source_name: 数据源名称
        
        Returns:
            Dict: 数据源状态信息
        """
        if source_name not in self.SOURCES:
            return {"status": "unknown", "error": "未知数据源"}
            
        data = self.get_cached_data(source_name)
        status = data.get("status", "unknown")
        
        result = {
            "source": source_name,
            "status": status,
            "timestamp": self._cache_timestamp.get(source_name, time.time())
        }
        
        # 添加更多详细信息
        if status == "ok":
            if source_name == "memory":
                metrics = data.get("memory_metrics", {})
                result["metrics_count"] = len(metrics)
            elif source_name == "cache":
                metrics = data.get("cache_metrics", {})
                result["hit_rate"] = metrics.get("hit_rate", 0)
                result["memory_usage_mb"] = metrics.get("used_memory_mb", 0)
            elif source_name == "models":
                metrics = data.get("model_metrics", {})
                result["models_count"] = len(metrics)
            elif source_name == "system":
                metrics = data.get("system_metrics", {})
                result["cpu_percent"] = metrics.get("cpu", {}).get("percent", 0)
                result["memory_percent"] = metrics.get("memory", {}).get("percent", 0)
        
        return result
    
    def get_cached_data(self, source_name: str) -> Dict[str, Any]:
        """获取缓存的数据源数据
        
        Args:
            source_name: 数据源名称
            
        Returns:
            Dict: 数据源数据
        """
        with self._cache_lock:
            # 如果缓存不存在或已过期（超过30秒），重新获取
            now = time.time()
            if (source_name not in self._data_cache or 
                now - self._cache_timestamp.get(source_name, 0) > 30):
                
                try:
                    source = self.SOURCES.get(source_name)
                    if source:
                        data = source.scrape()
                        self._data_cache[source_name] = data
                        self._cache_timestamp[source_name] = now
                except Exception as e:
                    self.logger.error(f"获取数据源 {source_name} 数据失败: {e}")
                    return {"status": "error", "error": str(e)}
                    
            return self._data_cache.get(source_name, {"status": "no_data"})
    
    def start_auto_update(self, interval_seconds: int = 30):
        """启动自动更新数据线程
        
        Args:
            interval_seconds: 更新间隔（秒）
        """
        if self.update_thread and self.update_thread.is_alive():
            return
            
        self.should_stop = False
        
        def update_loop():
            while not self.should_stop:
                try:
                    # 更新所有数据源
                    for src_name in self.SOURCES.keys():
                        self.get_cached_data(src_name)
                        
                    # 更新健康状态
                    self.health_status = self._check_health()
                except Exception as e:
                    self.logger.error(f"自动更新数据失败: {e}")
                    
                # 等待下次更新
                time.sleep(interval_seconds)
        
        self.update_thread = threading.Thread(
            target=update_loop,
            daemon=True,
            name="data_aggregator_updater"
        )
        self.update_thread.start()
        self.logger.info(f"自动更新数据线程已启动，间隔 {interval_seconds} 秒")
    
    def stop_auto_update(self):
        """停止自动更新数据线程"""
        self.should_stop = True
        
        if self.update_thread and self.update_thread.is_alive():
            self.update_thread.join(timeout=5.0)
            
        self.logger.info("自动更新数据线程已停止")
    
    def _check_health(self) -> Dict[str, Any]:
        """检查所有数据源的健康状态
        
        Returns:
            Dict: 健康状态信息
        """
        health = {
            "status": "healthy",
            "timestamp": time.time(),
            "sources": {}
        }
        
        all_healthy = True
        
        for src_name, source in self.SOURCES.items():
            try:
                data = source.scrape()
                status = data.get("status", "unknown")
                
                health["sources"][src_name] = {
                    "status": status,
                    "healthy": status in ("ok", "fallback")
                }
                
                if status not in ("ok", "fallback"):
                    all_healthy = False
                    
            except Exception as e:
                health["sources"][src_name] = {
                    "status": "error",
                    "healthy": False,
                    "error": str(e)
                }
                all_healthy = False
                
        health["status"] = "healthy" if all_healthy else "degraded"
        
        return health
    
    def get_health_status(self) -> Dict[str, Any]:
        """获取聚合器的健康状态
        
        Returns:
            Dict: 健康状态信息
        """
        # 如果状态过期（超过60秒），重新检查
        if time.time() - self.health_status.get("timestamp", 0) > 60:
            self.health_status = self._check_health()
            
        return self.health_status


# 便捷函数：获取所有数据源连接状态
def fetch_data_sources_status() -> Dict[str, Any]:
    """获取所有数据源的连接状态
    
    Returns:
        Dict: 数据源状态信息
    """
    aggregator = DataAggregator()
    
    sources_status = {}
    for source_name in aggregator.SOURCES.keys():
        sources_status[source_name] = aggregator.get_source_status(source_name)
        
    return {
        "status": "ok",
        "timestamp": time.time(),
        "sources": sources_status
    }


# API路由处理函数
def api_data_sources_status():
    """API处理函数：获取所有数据源状态"""
    return fetch_data_sources_status()


# 当直接运行此脚本时的示例代码
if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # 创建聚合器并获取数据
    aggregator = DataAggregator()
    
    print("获取数据源状态:")
    for source in aggregator.SOURCES.keys():
        status = aggregator.get_source_status(source)
        print(f"{source}: {status['status']}")
    
    print("\n获取聚合数据:")
    data = aggregator.fetch_realtime_data()
    for source, results in data.items():
        print(f"{source}: {results['status']}")
        
    print("\n健康状态:")
    health = aggregator.get_health_status()
    print(f"整体状态: {health['status']}")
    for source, status in health['sources'].items():
        print(f"  {source}: {'健康' if status['healthy'] else '异常'}") 