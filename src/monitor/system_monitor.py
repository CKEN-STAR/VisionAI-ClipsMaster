#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 系统监控模块

提供系统资源监控和性能分析功能
"""

import os
import sys
import time
import logging
import platform
import threading
import datetime
from typing import Dict, List, Any, Optional, Tuple

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

# 导入温度适配器
try:
    from src.monitor.platform_adapters import get_temperatures
    HAS_TEMP_ADAPTER = True
except ImportError:
    HAS_TEMP_ADAPTER = False

# 配置日志
logger = logging.getLogger(__name__)

# 系统资源警告阈值
DEFAULT_WARNING_THRESHOLDS = {
    "cpu_percent": 80.0,     # CPU使用率超过80%时警告
    "memory_percent": 85.0,  # 内存使用率超过85%时警告（从70%调整为85%）
    "disk_percent": 90.0,    # 磁盘使用率超过90%时警告
    "temperature": 80.0      # 温度超过80℃时警告
}

class SystemMonitor:
    """系统监控类，用于监控系统资源使用情况"""
    
    def __init__(self, interval: float = 1.0, warning_thresholds: Dict[str, float] = None):
        """初始化系统监控
        
        Args:
            interval: 监控间隔，单位秒
            warning_thresholds: 资源警告阈值，None则使用默认值
        """
        self.interval = interval
        self.running = False
        self.thread = None
        self.callbacks = []
        self.history = {
            "cpu": [],
            "memory": [],
            "disk": [],
            "network": [],
            "temperature": [],
            "timestamp": []
        }
        self.history_max_size = 60  # 保存60个采样点
        
        # 设置警告阈值
        self.warning_thresholds = warning_thresholds or DEFAULT_WARNING_THRESHOLDS.copy()
        
        # 系统信息
        self.system_info = self._get_system_info()
        
        logger.info("系统监控已初始化")
    
    def _get_system_info(self) -> Dict[str, Any]:
        """获取系统基本信息
        
        Returns:
            系统信息字典
        """
        info = {
            "platform": platform.platform(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "hostname": platform.node()
        }
        
        if HAS_PSUTIL:
            try:
                info.update({
                    "cpu_count": psutil.cpu_count(logical=True),
                    "physical_cpu_count": psutil.cpu_count(logical=False),
                    "total_memory": psutil.virtual_memory().total,
                    "boot_time": datetime.datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")
                })
            except Exception as e:
                logger.warning(f"获取系统信息时出错: {e}")
        
        return info
    
    def start(self) -> bool:
        """启动监控
        
        Returns:
            是否成功启动
        """
        if self.running:
            logger.warning("监控已在运行中")
            return False
        
        if not HAS_PSUTIL:
            logger.error("无法启动监控: 缺少psutil库")
            return False
        
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop)
        self.thread.daemon = True
        self.thread.start()
        
        logger.info(f"系统监控已启动 (间隔: {self.interval}秒)")
        return True
    
    def stop(self) -> None:
        """停止监控"""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)
        
        logger.info("系统监控已停止")
    
    def _monitor_loop(self) -> None:
        """监控循环"""
        while self.running:
            try:
                stats = self._collect_stats()
                
                # 检查资源使用是否超过警告阈值
                self._check_resource_warnings(stats)
                
                # 更新历史记录
                self._update_history(stats)
                
                # 调用回调函数
                for callback in self.callbacks:
                    try:
                        callback(stats)
                    except Exception as e:
                        logger.error(f"执行监控回调时出错: {e}")
                
            except Exception as e:
                logger.error(f"监控循环出错: {e}")
            
            time.sleep(self.interval)
    
    def _check_resource_warnings(self, stats: Dict[str, Any]) -> None:
        """检查资源使用是否超过警告阈值
        
        Args:
            stats: 系统统计信息
        """
        # 检查CPU使用率
        if "cpu" in stats and stats["cpu"]["percent"] > self.warning_thresholds["cpu_percent"]:
            logger.warning(f"CPU使用率过高: {stats['cpu']['percent']}% > {self.warning_thresholds['cpu_percent']}%")
        
        # 检查内存使用率
        if "memory" in stats and stats["memory"]["percent"] > self.warning_thresholds["memory_percent"]:
            logger.warning(f"内存使用率过高: {stats['memory']['percent']}% > {self.warning_thresholds['memory_percent']}%")
        
        # 检查磁盘使用率
        if "disk" in stats and stats["disk"]["percent"] > self.warning_thresholds["disk_percent"]:
            logger.warning(f"磁盘使用率过高: {stats['disk']['percent']}% > {self.warning_thresholds['disk_percent']}%")
        
        # 检查温度
        if "temperature" in stats:
            for device, sensors in stats["temperature"].items():
                for sensor in sensors:
                    if sensor.get("current", 0) > self.warning_thresholds["temperature"]:
                        logger.warning(f"温度过高: {sensor['label']} {sensor['current']}°C > {self.warning_thresholds['temperature']}°C")
    
    def _collect_stats(self) -> Dict[str, Any]:
        """收集系统统计信息
        
        Returns:
            系统统计信息字典
        """
        stats = {
            "timestamp": time.time()
        }
        
        if not HAS_PSUTIL:
            return stats
        
        try:
            # CPU使用率
            stats["cpu"] = {
                "percent": psutil.cpu_percent(interval=None),
                "per_cpu": psutil.cpu_percent(interval=None, percpu=True)
            }
            
            # 内存使用情况
            mem = psutil.virtual_memory()
            stats["memory"] = {
                "total": mem.total,
                "available": mem.available,
                "used": mem.used,
                "percent": mem.percent
            }
            
            # 磁盘使用情况
            disk = psutil.disk_usage('/')
            stats["disk"] = {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": disk.percent
            }
            
            # 网络使用情况
            net_io = psutil.net_io_counters()
            stats["network"] = {
                "bytes_sent": net_io.bytes_sent,
                "bytes_recv": net_io.bytes_recv,
                "packets_sent": net_io.packets_sent,
                "packets_recv": net_io.packets_recv
            }
            
            # 进程信息
            current_process = psutil.Process(os.getpid())
            stats["process"] = {
                "cpu_percent": current_process.cpu_percent(interval=None),
                "memory_percent": current_process.memory_percent(),
                "memory_info": dict(current_process.memory_info()._asdict()),
                "num_threads": current_process.num_threads()
            }
            
            # 温度信息（使用适配器）
            if HAS_TEMP_ADAPTER:
                try:
                    stats["temperature"] = get_temperatures()
                except Exception as e:
                    logger.debug(f"获取温度信息失败: {e}")
            else:
                # 尝试直接使用psutil获取温度（可能在某些平台不可用）
                try:
                    temps = psutil.sensors_temperatures()
                    if temps:
                        stats["temperature"] = temps
                except (AttributeError, OSError):
                    # 在Windows上psutil.sensors_temperatures()可能不可用
                    pass
            
        except Exception as e:
            logger.error(f"收集系统统计信息时出错: {e}")
        
        return stats
    
    def _update_history(self, stats: Dict[str, Any]) -> None:
        """更新历史记录
        
        Args:
            stats: 当前统计信息
        """
        # 添加时间戳
        self.history["timestamp"].append(stats["timestamp"])
        
        # 添加CPU使用率
        if "cpu" in stats:
            self.history["cpu"].append(stats["cpu"]["percent"])
        else:
            self.history["cpu"].append(None)
        
        # 添加内存使用率
        if "memory" in stats:
            self.history["memory"].append(stats["memory"]["percent"])
        else:
            self.history["memory"].append(None)
        
        # 添加磁盘使用率
        if "disk" in stats:
            self.history["disk"].append(stats["disk"]["percent"])
        else:
            self.history["disk"].append(None)
        
        # 添加网络使用情况
        if "network" in stats:
            self.history["network"].append({
                "sent": stats["network"]["bytes_sent"],
                "recv": stats["network"]["bytes_recv"]
            })
        else:
            self.history["network"].append(None)
        
        # 添加温度信息
        if "temperature" in stats:
            # 记录CPU温度的平均值
            cpu_temps = []
            if "cpu" in stats["temperature"]:
                for sensor in stats["temperature"]["cpu"]:
                    if "current" in sensor:
                        cpu_temps.append(sensor["current"])
            
            if cpu_temps:
                avg_temp = sum(cpu_temps) / len(cpu_temps)
                self.history["temperature"].append(avg_temp)
            else:
                self.history["temperature"].append(None)
        else:
            self.history["temperature"].append(None)
        
        # 限制历史记录大小
        for key in self.history:
            if len(self.history[key]) > self.history_max_size:
                self.history[key] = self.history[key][-self.history_max_size:]
    
    def get_current_stats(self) -> Dict[str, Any]:
        """获取当前系统统计信息
        
        Returns:
            当前系统统计信息
        """
        return self._collect_stats()
    
    def get_history(self) -> Dict[str, List]:
        """获取历史记录
        
        Returns:
            历史记录字典
        """
        return self.history
    
    def get_system_info(self) -> Dict[str, Any]:
        """获取系统信息
        
        Returns:
            系统信息字典
        """
        return self.system_info
    
    def register_callback(self, callback) -> None:
        """注册回调函数
        
        Args:
            callback: 回调函数，接收一个参数(stats)
        """
        if callback not in self.callbacks:
            self.callbacks.append(callback)
    
    def unregister_callback(self, callback) -> None:
        """取消注册回调函数
        
        Args:
            callback: 要取消的回调函数
        """
        if callback in self.callbacks:
            self.callbacks.remove(callback)

# 全局实例
_monitor = None

def get_system_monitor() -> SystemMonitor:
    """获取系统监控全局实例
    
    Returns:
        系统监控实例
    """
    global _monitor
    if _monitor is None:
        try:
            _monitor = SystemMonitor()
        except Exception as e:
            logger.error(f"创建系统监控失败: {str(e)}")
            _monitor = None
    
    return _monitor

# 便捷函数
def get_current_stats() -> Dict[str, Any]:
    """获取当前系统统计信息
    
    Returns:
        当前系统统计信息
    """
    monitor = get_system_monitor()
    if monitor:
        return monitor.get_current_stats()
    return {}

def get_system_info() -> Dict[str, Any]:
    """获取系统信息
    
    Returns:
        系统信息
    """
    monitor = get_system_monitor()
    if monitor:
        return monitor.get_system_info()
    return {}

# 测试代码
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    print(" VisionAI-ClipsMaster 系统监控测试 ")
    print("-" * 50)
    
    monitor = get_system_monitor()
    
    if not HAS_PSUTIL:
        print("警告: 未安装psutil库，功能受限")
    
    print("系统信息:")
    for key, value in monitor.get_system_info().items():
        print(f"  {key}: {value}")
    
    print("\n当前系统状态:")
    stats = monitor.get_current_stats()
    if "cpu" in stats:
        print(f"  CPU使用率: {stats['cpu']['percent']}%")
    if "memory" in stats:
        print(f"  内存使用率: {stats['memory']['percent']}%")
    if "disk" in stats:
        print(f"  磁盘使用率: {stats['disk']['percent']}%")
    if "temperature" in stats and stats["temperature"]:
        print("  温度信息:")
        for device, sensors in stats["temperature"].items():
            for sensor in sensors:
                print(f"    {sensor['label']}: {sensor['current']:.1f}°C")
    
    print("\n启动监控 (5秒)...")
    
    def print_stats(stats):
        if "cpu" in stats:
            print(f"CPU: {stats['cpu']['percent']}%, 内存: {stats['memory']['percent']}%")
    
    monitor.register_callback(print_stats)
    monitor.start()
    
    time.sleep(5)
    
    monitor.stop()
    print("\n系统监控测试完成。") 