#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
多维度监控集成模块

负责收集和整合来自不同层次的系统指标：
1. 应用级监控 - JVM/.NET运行时内存、GC状态等
2. OS级监控 - 通过/proc/meminfo等系统接口获取内存、CPU、磁盘指标
3. 硬件级监控 - 通过SMBIOS等接口获取传感器数据（温度、风扇等）

设计为插件化架构，支持动态添加新的监控源
"""

import os
import sys
import time
import json
import logging
import platform
import threading
import subprocess
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
from pathlib import Path
from datetime import datetime

import psutil
try:
    # 尝试导入硬件监控相关库
    import py3nvml.py3nvml as nvml
    NVML_AVAILABLE = True
except ImportError:
    NVML_AVAILABLE = False
    
try:
    # Windows硬件监控
    import wmi
    WMI_AVAILABLE = True
except ImportError:
    WMI_AVAILABLE = False

# 导入项目模块
from src.utils.memory_guard import get_memory_guard, log_memory_usage
from src.utils.device_manager import detect_hardware_capabilities
from src.monitoring.data_collector import get_collector, record_system_metrics
from src.monitoring.metrics_collector import MetricsCollector

# 配置日志
logger = logging.getLogger("multi_source_monitor")


class MetricSource(ABC):
    """
    指标源抽象基类，所有指标收集器都应继承此类
    """
    
    def __init__(self, name: str, collection_interval: float = 5.0):
        """
        初始化指标源
        
        Args:
            name: 指标源名称
            collection_interval: 收集间隔（秒）
        """
        self.name = name
        self.collection_interval = collection_interval
        self.enabled = True
        self.last_collection_time = 0
        self.last_metrics = {}
        self.error_count = 0
        self.max_errors = 3  # 连续错误阈值
        
    @abstractmethod
    def fetch(self) -> Dict[str, Any]:
        """
        获取指标数据
        
        Returns:
            Dict: 包含指标名称和值的字典
        """
        pass
        
    def should_collect(self) -> bool:
        """
        检查是否应该收集指标
        
        Returns:
            bool: 是否应该收集
        """
        current_time = time.time()
        return (current_time - self.last_collection_time) >= self.collection_interval
        
    def collect(self) -> Dict[str, Any]:
        """
        收集并返回指标数据
        
        Returns:
            Dict: 带有时间戳的指标数据
        """
        if not self.enabled:
            return {}
            
        if not self.should_collect():
            return self.last_metrics
            
        try:
            metrics = self.fetch()
            metrics["timestamp"] = datetime.now().isoformat()
            metrics["source"] = self.name
            self.last_metrics = metrics
            self.last_collection_time = time.time()
            self.error_count = 0  # 重置错误计数
            return metrics
        except Exception as e:
            logger.error(f"Error collecting metrics from {self.name}: {str(e)}")
            self.error_count += 1
            # 如果连续错误太多，禁用此源
            if self.error_count >= self.max_errors:
                logger.warning(f"Disabling {self.name} due to repeated errors")
                self.enabled = False
            return {"error": str(e), "source": self.name, "timestamp": datetime.now().isoformat()}


class PrometheusScraperSource(MetricSource):
    """从Prometheus端点抓取指标"""
    
    def __init__(self, url: str = "localhost:9090", collection_interval: float = 10.0):
        """
        初始化Prometheus抓取器
        
        Args:
            url: Prometheus服务器URL
            collection_interval: 收集间隔（秒）
        """
        super().__init__(name="prometheus", collection_interval=collection_interval)
        self.url = url
        try:
            import requests
            self.requests = requests
        except ImportError:
            logger.warning("请安装requests库以启用Prometheus指标收集")
            self.enabled = False
            self.requests = None
            
    def fetch(self) -> Dict[str, Any]:
        """获取Prometheus指标"""
        if not self.requests:
            return {"error": "requests module not available"}
            
        try:
            # 获取内存相关指标
            memory_metrics = {}
            mem_url = f"http://{self.url}/api/v1/query?query=process_resident_memory_bytes"
            response = self.requests.get(mem_url)
            if response.status_code == 200:
                data = response.json()
                if "data" in data and "result" in data["data"] and len(data["data"]["result"]) > 0:
                    memory_metrics["resident_memory_bytes"] = float(data["data"]["result"][0]["value"][1])
            
            # 获取CPU相关指标
            cpu_metrics = {}
            cpu_url = f"http://{self.url}/api/v1/query?query=process_cpu_seconds_total"
            response = self.requests.get(cpu_url)
            if response.status_code == 200:
                data = response.json()
                if "data" in data and "result" in data["data"] and len(data["data"]["result"]) > 0:
                    cpu_metrics["cpu_seconds_total"] = float(data["data"]["result"][0]["value"][1])
            
            # 合并指标
            return {
                "memory": memory_metrics,
                "cpu": cpu_metrics
            }
        except Exception as e:
            logger.error(f"Error fetching Prometheus metrics: {str(e)}")
            return {"error": str(e)}


class KernelRingBuffer(MetricSource):
    """内核环形缓冲区监控器（dmesg日志）"""
    
    def __init__(self, collection_interval: float = 30.0):
        """
        初始化内核缓冲区监控器
        
        Args:
            collection_interval: 收集间隔（秒）
        """
        super().__init__(name="kernel_ring_buffer", collection_interval=collection_interval)
        self.last_timestamp = 0
        
    def fetch(self) -> Dict[str, Any]:
        """获取内核日志中的OOM和硬件错误"""
        kernel_metrics = {
            "oom_events": 0,
            "hardware_errors": 0,
            "io_errors": 0,
            "critical_events": []
        }
        
        try:
            if platform.system() == "Linux":
                # 使用dmesg获取内核消息
                cmd = ["dmesg", "--time-format", "iso", "--level", "err,crit,alert,emerg"]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    for line in result.stdout.splitlines():
                        # 只处理上次检查后的消息
                        if " : " in line:  # ISO时间格式包含此分隔符
                            timestamp_str, message = line.split(" : ", 1)
                            try:
                                timestamp = datetime.fromisoformat(timestamp_str).timestamp()
                                if timestamp > self.last_timestamp:
                                    # 检测OOM事件
                                    if "Out of memory" in message or "oom-killer" in message:
                                        kernel_metrics["oom_events"] += 1
                                        kernel_metrics["critical_events"].append(
                                            {"type": "oom", "timestamp": timestamp_str, "message": message}
                                        )
                                    # 检测硬件错误
                                    elif "hardware error" in message or "CPU" in message and "error" in message:
                                        kernel_metrics["hardware_errors"] += 1
                                        kernel_metrics["critical_events"].append(
                                            {"type": "hardware", "timestamp": timestamp_str, "message": message}
                                        )
                                    # 检测IO错误
                                    elif "I/O error" in message or "sd" in message and "error" in message:
                                        kernel_metrics["io_errors"] += 1
                                        kernel_metrics["critical_events"].append(
                                            {"type": "io", "timestamp": timestamp_str, "message": message}
                                        )
                            except ValueError:
                                # 忽略无效时间戳
                                pass
                    # 更新最后时间戳
                    self.last_timestamp = time.time()
            elif platform.system() == "Windows":
                # Windows下通过事件日志获取类似信息
                # 这里使用简化实现，实际应使用win32evtlog或wmi
                kernel_metrics["note"] = "Full Windows kernel monitoring requires privileged access"
                
            return kernel_metrics
        except Exception as e:
            logger.error(f"Error reading kernel ring buffer: {str(e)}")
            return {"error": str(e)}


class EbpfMemTracer(MetricSource):
    """eBPF内存跟踪器（Linux专用）"""
    
    def __init__(self, collection_interval: float = 60.0):
        """
        初始化eBPF内存跟踪器
        
        Args:
            collection_interval: 收集间隔（秒）
        """
        super().__init__(name="ebpf_mem_tracer", collection_interval=collection_interval)
        
        # 检查是否可以使用BCC
        self.bcc_available = False
        try:
            import bcc
            self.bcc = bcc
            self.bcc_available = True
            logger.info("BCC库可用，启用eBPF内存跟踪")
        except ImportError:
            logger.warning("BCC库不可用，禁用eBPF内存跟踪")
            self.enabled = False
            
    def fetch(self) -> Dict[str, Any]:
        """获取eBPF内存跟踪指标"""
        if not self.bcc_available:
            return {"error": "BCC not available"}
            
        # eBPF指标收集是一个复杂主题，这里仅作示例
        # 实际实现需要定制的eBPF程序
        
        try:
            # 简单调用内存使用统计的例子
            memory_metrics = {
                "note": "Full eBPF memory tracing requires root privileges and custom eBPF programs"
            }
            
            if os.geteuid() == 0:  # 只在root权限下尝试运行
                # 运行简单的eBPF程序追踪内存分配（示例）
                memory_metrics["has_root"] = True
                # 实际实现略——需要编写和加载eBPF程序
            else:
                memory_metrics["has_root"] = False
                
            return memory_metrics
        except Exception as e:
            logger.error(f"Error in eBPF memory tracing: {str(e)}")
            return {"error": str(e)}


class HybridMonitor:
    """
    多维度监控器，整合不同来源的监控数据
    """
    
    # 默认指标源列表
    METRIC_SOURCES = [
        PrometheusScraperSource(url="localhost:9090"),
        KernelRingBuffer(),
        EbpfMemTracer()
    ]
    
    def __init__(self, sources: List[MetricSource] = None):
        """
        初始化混合监控器
        
        Args:
            sources: 指标源列表，如不提供则使用默认列表
        """
        self.sources = sources or self.METRIC_SOURCES.copy()
        self.running = False
        self.collection_thread = None
        self.metrics_history = []
        self.max_history_items = 1000  # 最多保留1000个历史数据点
        self.callbacks = []  # 注册数据收集回调
        
        # 确保历史目录存在
        os.makedirs("data/metrics_history", exist_ok=True)
        
        # 尝试获取内存监控器
        try:
            self.memory_guard = get_memory_guard()
        except Exception:
            logger.warning("无法获取内存监控器，使用有限功能")
            self.memory_guard = None
            
        # 尝试获取指标收集器
        try:
            self.metrics_collector = MetricsCollector()
        except Exception:
            logger.warning("无法获取指标收集器，使用有限功能")
            self.metrics_collector = None
        
    def add_source(self, source: MetricSource) -> None:
        """
        添加新的指标源
        
        Args:
            source: 要添加的指标源
        """
        self.sources.append(source)
        logger.info(f"Added new metric source: {source.name}")
        
    def remove_source(self, source_name: str) -> bool:
        """
        移除指标源
        
        Args:
            source_name: 要移除的指标源名称
            
        Returns:
            bool: 是否成功移除
        """
        for i, source in enumerate(self.sources):
            if source.name == source_name:
                self.sources.pop(i)
                logger.info(f"Removed metric source: {source_name}")
                return True
        logger.warning(f"Metric source not found: {source_name}")
        return False
        
    def get_mem_metrics(self) -> Dict[str, Any]:
        """
        获取整合的内存指标
        
        Returns:
            Dict: 包含各种内存指标的字典
        """
        metrics = {}
        
        # 从各源收集指标
        for source in self.sources:
            if source.enabled:
                source_metrics = source.collect()
                if source_metrics and not (len(source_metrics) == 1 and "error" in source_metrics):
                    metrics.update({source.name: source_metrics})
        
        # 合并指标
        return self.merge_metrics(metrics)
    
    def merge_metrics(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        合并来自不同源的指标数据
        
        Args:
            metrics: 原始指标数据
            
        Returns:
            Dict: 合并后的指标数据
        """
        merged = {
            "timestamp": datetime.now().isoformat(),
            "memory": {},
            "cpu": {},
            "io": {},
            "hardware": {},
            "errors": []
        }
        
        # 处理多源数据
        for source_name, source_data in metrics.items():
            # 处理错误
            if "error" in source_data:
                merged["errors"].append({
                    "source": source_name,
                    "error": source_data["error"]
                })
                continue
                
            # 提取特定指标
            if source_name == "prometheus" and "memory" in source_data:
                for k, v in source_data["memory"].items():
                    merged["memory"][f"prometheus_{k}"] = v
                    
            elif source_name == "kernel_ring_buffer":
                # 内核缓冲区错误
                if "critical_events" in source_data:
                    merged["errors"].extend(source_data["critical_events"])
                # 其他指标
                for k, v in source_data.items():
                    if k != "critical_events":
                        merged["hardware"][f"kernel_{k}"] = v
        
        # 添加系统指标
        try:
            # 内存指标
            vm = psutil.virtual_memory()
            merged["memory"].update({
                "total_gb": round(vm.total / (1024**3), 2),
                "available_gb": round(vm.available / (1024**3), 2),
                "used_gb": round(vm.used / (1024**3), 2),
                "percent": vm.percent
            })
            
            # CPU指标
            merged["cpu"].update({
                "percent": psutil.cpu_percent(interval=0.1),
                "count": psutil.cpu_count(),
                "logical_count": psutil.cpu_count(logical=True)
            })
            
            # 磁盘指标
            disk = psutil.disk_usage('/')
            merged["io"].update({
                "disk_total_gb": round(disk.total / (1024**3), 2),
                "disk_used_gb": round(disk.used / (1024**3), 2),
                "disk_free_gb": round(disk.free / (1024**3), 2),
                "disk_percent": disk.percent
            })
            
            # 添加进程指标
            process = psutil.Process(os.getpid())
            merged["memory"]["process_rss_mb"] = round(process.memory_info().rss / (1024**2), 2)
            merged["cpu"]["process_cpu_percent"] = process.cpu_percent(interval=0.1)
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {str(e)}")
            merged["errors"].append({
                "source": "system",
                "error": str(e)
            })
            
        # 如果可用，增加内存监视器的数据
        if self.memory_guard:
            try:
                mem_status = self.memory_guard.get_memory_status()
                if mem_status:
                    for k, v in mem_status.items():
                        if k not in ("timestamp", "errors"):
                            merged["memory"][f"guard_{k}"] = v
            except Exception as e:
                logger.error(f"Error getting memory guard status: {str(e)}")
                
        return merged
    
    def register_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        注册指标收集回调函数
        
        Args:
            callback: 回调函数，接收指标字典
        """
        self.callbacks.append(callback)
        logger.info(f"Registered metrics callback, total callbacks: {len(self.callbacks)}")
        
    def _collection_loop(self) -> None:
        """指标收集循环"""
        while self.running:
            try:
                # 收集指标
                metrics = self.get_mem_metrics()
                
                # 添加到历史记录
                self.metrics_history.append(metrics)
                if len(self.metrics_history) > self.max_history_items:
                    self.metrics_history.pop(0)
                    
                # 执行回调
                for callback in self.callbacks:
                    try:
                        callback(metrics)
                    except Exception as e:
                        logger.error(f"Error in metrics callback: {str(e)}")
                        
                # 记录到监控系统
                if self.metrics_collector:
                    try:
                        # 记录关键指标
                        if "memory" in metrics and "percent" in metrics["memory"]:
                            self.metrics_collector.record_metric(
                                "memory_usage_percent", 
                                metrics["memory"]["percent"]
                            )
                        if "cpu" in metrics and "percent" in metrics["cpu"]:
                            self.metrics_collector.record_metric(
                                "cpu_usage_percent", 
                                metrics["cpu"]["percent"]
                            )
                    except Exception as e:
                        logger.error(f"Error recording to metrics collector: {str(e)}")
                
                # 周期性保存历史数据
                current_hour = datetime.now().hour
                if current_hour % 6 == 0 and len(self.metrics_history) > 100:
                    self._save_metrics_history()
                
            except Exception as e:
                logger.error(f"Error in metrics collection loop: {str(e)}")
                
            # 间隔10秒
            time.sleep(10)
    
    def start(self) -> None:
        """启动监控"""
        if self.running:
            logger.warning("Hybrid monitor is already running")
            return
            
        self.running = True
        self.collection_thread = threading.Thread(target=self._collection_loop)
        self.collection_thread.daemon = True
        self.collection_thread.start()
        logger.info("Hybrid monitor started")
        
    def stop(self) -> None:
        """停止监控"""
        if not self.running:
            logger.warning("Hybrid monitor is not running")
            return
            
        self.running = False
        if self.collection_thread:
            self.collection_thread.join(timeout=2)
        logger.info("Hybrid monitor stopped")
        
        # 保存最终历史数据
        self._save_metrics_history()
        
    def _save_metrics_history(self) -> None:
        """保存指标历史到磁盘"""
        if not self.metrics_history:
            return
            
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            history_file = f"data/metrics_history/metrics_{timestamp}.json"
            
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(self.metrics_history, f, ensure_ascii=False, indent=2)
                
            logger.info(f"Saved metrics history to {history_file}")
        except Exception as e:
            logger.error(f"Error saving metrics history: {str(e)}")
    
    def get_latest_metrics(self) -> Dict[str, Any]:
        """
        获取最新指标
        
        Returns:
            Dict: 最新指标数据
        """
        if not self.metrics_history:
            return self.get_mem_metrics()
        return self.metrics_history[-1]
        
    def get_metrics_summary(self) -> Dict[str, Any]:
        """
        获取指标摘要
        
        Returns:
            Dict: 指标摘要数据
        """
        if not self.metrics_history:
            return {"error": "No metrics history available"}
            
        summary = {
            "timestamp": datetime.now().isoformat(),
            "samples": len(self.metrics_history),
            "memory": {},
            "cpu": {},
            "errors": {
                "count": 0,
                "sources": {}
            }
        }
        
        # 计算平均值和最大值
        for field in ["memory", "cpu"]:
            values = {}
            for metrics in self.metrics_history:
                if field in metrics:
                    for k, v in metrics[field].items():
                        if isinstance(v, (int, float)):
                            if k not in values:
                                values[k] = []
                            values[k].append(v)
            
            # 计算统计信息
            for k, v_list in values.items():
                if v_list:
                    summary[field][f"{k}_avg"] = sum(v_list) / len(v_list)
                    summary[field][f"{k}_max"] = max(v_list)
                    summary[field][f"{k}_min"] = min(v_list)
        
        # 统计错误
        for metrics in self.metrics_history:
            if "errors" in metrics:
                summary["errors"]["count"] += len(metrics["errors"])
                for error in metrics["errors"]:
                    source = error.get("source", "unknown")
                    if source not in summary["errors"]["sources"]:
                        summary["errors"]["sources"][source] = 0
                    summary["errors"]["sources"][source] += 1
        
        return summary


# 单例模式
_hybrid_monitor = None

def get_hybrid_monitor() -> HybridMonitor:
    """
    获取混合监控器单例
    
    Returns:
        HybridMonitor: 混合监控器实例
    """
    global _hybrid_monitor
    if _hybrid_monitor is None:
        _hybrid_monitor = HybridMonitor()
    return _hybrid_monitor


if __name__ == "__main__":
    # 设置日志格式
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 启动监控器
    monitor = get_hybrid_monitor()
    monitor.start()
    
    # 示例：注册回调函数
    def print_metrics(metrics):
        if "memory" in metrics and "percent" in metrics["memory"]:
            print(f"Memory usage: {metrics['memory']['percent']}%")
        if "cpu" in metrics and "percent" in metrics["cpu"]:
            print(f"CPU usage: {metrics['cpu']['percent']}%")
    
    monitor.register_callback(print_metrics)
    
    try:
        # 运行60秒
        print("Monitoring for 60 seconds...")
        time.sleep(60)
    finally:
        # 停止监控器
        monitor.stop()
        
        # 打印摘要
        summary = monitor.get_metrics_summary()
        print("Metrics summary:")
        print(json.dumps(summary, indent=2)) 