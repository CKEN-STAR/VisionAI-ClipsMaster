#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
资源跟踪器

该模块负责跟踪各种系统资源的使用情况，包括内存、GPU、磁盘等，
并提供报警和自动回收功能。
"""

import os
import gc
import time
import psutil
import threading
import logging
from typing import Dict, Any, List, Optional, Tuple

# 设置日志
logger = logging.getLogger("resource_tracker")

# 内存使用警告阈值（百分比）
MEMORY_WARNING_THRESHOLD = 80

class ResourceTracker:
    """资源跟踪器，用于监控系统资源使用"""
    
    def __init__(self):
        """初始化资源跟踪器"""
        self.resources = {}
        self.thresholds = {
            "memory": 0.9,  # 内存警告阈值，90%
            "disk": 0.95,  # 磁盘警告阈值，95%
            "gpu": 0.85  # GPU内存警告阈值，85%
        }
        self.callbacks = {
            "memory": [],
            "disk": [],
            "gpu": []
        }
        self.monitor_thread = None
        self.running = False
        self.lock = threading.RLock()
        
    def start_monitoring(self):
        """启动资源监控"""
        with self.lock:
            if self.monitor_thread is None or not self.monitor_thread.is_alive():
                self.running = True
                self.monitor_thread = threading.Thread(target=self._monitor_resources)
                self.monitor_thread.daemon = True
                self.monitor_thread.start()
                logger.info("资源监控已启动")
    
    def stop_monitoring(self):
        """停止资源监控"""
        with self.lock:
            self.running = False
            if self.monitor_thread and self.monitor_thread.is_alive():
                self.monitor_thread.join(timeout=2)
                logger.info("资源监控已停止")
    
    def _monitor_resources(self):
        """资源监控主循环"""
        while self.running:
            try:
                # 更新资源使用情况
                self._update_memory_usage()
                self._update_disk_usage()
                self._update_gpu_usage()
                
                # 检查是否超过阈值
                self._check_thresholds()
                
                # 等待10秒再次检查
                time.sleep(10)
            except Exception as e:
                logger.error(f"资源监控错误: {e}")
                time.sleep(30)  # 错误后等待较长时间
    
    def _update_memory_usage(self):
        """更新内存使用情况"""
        try:
            mem = psutil.virtual_memory()
            self.resources["memory"] = {
                "total": mem.total,
                "available": mem.available,
                "used": mem.used,
                "free": mem.free,
                "percent": mem.percent,
                "usage": mem.percent / 100.0
            }
        except Exception as e:
            logger.error(f"更新内存使用情况失败: {e}")
    
    def _update_disk_usage(self):
        """更新磁盘使用情况"""
        try:
            disk_path = os.path.abspath(os.curdir)
            disk = psutil.disk_usage(disk_path)
            self.resources["disk"] = {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": disk.percent,
                "usage": disk.percent / 100.0,
                "path": disk_path
            }
        except Exception as e:
            logger.error(f"更新磁盘使用情况失败: {e}")
    
    def _update_gpu_usage(self):
        """更新GPU使用情况"""
        # 尝试使用pynvml获取NVIDIA GPU信息
        try:
            import pynvml
            pynvml.nvmlInit()
            device_count = pynvml.nvmlDeviceGetCount()

            if device_count <= 0:
                self.resources["gpu"] = {"available": False}
                return
                
            self.resources["gpu"] = {
                "available": True,
                "devices": []
            }
            
            for i in range(device_count):
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                name = pynvml.nvmlDeviceGetName(handle)
                
                total_memory = memory_info.total
                used_memory = memory_info.used
                free_memory = memory_info.free
                
                device_info = {
                    "name": name,
                    "total_memory": total_memory,
                    "used_memory": used_memory,
                    "free_memory": free_memory,
                    "memory_usage": used_memory / total_memory,
                    "index": i
                }
                
                self.resources["gpu"]["devices"].append(device_info)
                
            pynvml.nvmlShutdown()
            
        except ImportError:
            self.resources["gpu"] = {"available": False, "error": "pynvml not installed"}
        except Exception as e:
            self.resources["gpu"] = {"available": False, "error": str(e)}
    
    def _check_thresholds(self):
        """检查资源是否超过阈值"""
        # 检查内存
        if "memory" in self.resources and self.resources["memory"]["usage"] > self.thresholds["memory"]:
            logger.warning(f"内存使用率超过阈值: {self.resources['memory']['percent']}%")
            self._trigger_callbacks("memory")
            
        # 检查磁盘
        if "disk" in self.resources and self.resources["disk"]["usage"] > self.thresholds["disk"]:
            logger.warning(f"磁盘使用率超过阈值: {self.resources['disk']['percent']}%")
            self._trigger_callbacks("disk")
            
        # 检查GPU
        if "gpu" in self.resources and self.resources["gpu"].get("available", False):
            for i, device in enumerate(self.resources["gpu"]["devices"]):
                if device["memory_usage"] > self.thresholds["gpu"]:
                    logger.warning(f"GPU {i} 内存使用率超过阈值: {device['memory_usage']*100:.1f}%")
                    self._trigger_callbacks("gpu")
    
    def _trigger_callbacks(self, resource_type: str):
        """触发资源回调
        
        Args:
            resource_type: 资源类型，如 'memory', 'disk', 'gpu'
        """
        if resource_type in self.callbacks:
            for callback in self.callbacks[resource_type]:
                try:
                    callback(self.resources[resource_type])
                except Exception as e:
                    logger.error(f"执行{resource_type}回调函数时出错: {e}")
    
    def register_callback(self, resource_type: str, callback):
        """注册资源回调
        
        Args:
            resource_type: 资源类型，如 'memory', 'disk', 'gpu'
            callback: 回调函数，接收资源信息字典作为参数
        """
        with self.lock:
            if resource_type in self.callbacks:
                if callback not in self.callbacks[resource_type]:
                    self.callbacks[resource_type].append(callback)
                    logger.info(f"已注册{resource_type}回调")
                    
    def unregister_callback(self, resource_type: str, callback):
        """注销资源回调
        
        Args:
            resource_type: 资源类型，如 'memory', 'disk', 'gpu'
            callback: 回调函数
        """
        with self.lock:
            if resource_type in self.callbacks and callback in self.callbacks[resource_type]:
                self.callbacks[resource_type].remove(callback)
                logger.info(f"已注销{resource_type}回调")
    
    def set_threshold(self, resource_type: str, threshold: float):
        """设置资源阈值
        
        Args:
            resource_type: 资源类型，如 'memory', 'disk', 'gpu'
            threshold: 阈值 (0.0-1.0)
        """
        with self.lock:
            if resource_type in self.thresholds:
                self.thresholds[resource_type] = min(max(0.0, threshold), 1.0)
                logger.info(f"设置{resource_type}阈值为{self.thresholds[resource_type]}")
    
    def get_resource_info(self, resource_type: str = None) -> Dict[str, Any]:
        """获取资源信息
        
        Args:
            resource_type: 资源类型，如果为None则返回所有资源
            
        Returns:
            Dict: 资源信息字典
        """
        if resource_type is None:
            return self.resources.copy()
            
        if resource_type in self.resources:
            return self.resources[resource_type].copy()
            
        return {}
    
    def is_resource_critical(self, resource_type: str) -> bool:
        """检查资源是否处于紧急状态
        
        Args:
            resource_type: 资源类型，如 'memory', 'disk', 'gpu'
            
        Returns:
            bool: 是否处于紧急状态
        """
        if resource_type in self.resources and resource_type in self.thresholds:
            usage = self.resources[resource_type].get("usage", 0)
            return usage > self.thresholds[resource_type]
            
        return False
        
    def force_garbage_collection(self):
        """强制垃圾收集"""
        gc.collect()
        logger.info("执行了强制垃圾收集")
        

# 全局资源跟踪器实例
_resource_tracker = None

def get_resource_tracker() -> ResourceTracker:
    """获取全局资源跟踪器实例
    
    Returns:
        ResourceTracker: 资源跟踪器实例
    """
    global _resource_tracker
    
    if _resource_tracker is None:
        _resource_tracker = ResourceTracker()
        _resource_tracker.start_monitoring()
        
    return _resource_tracker


if __name__ == "__main__":
    # 设置日志级别
    logging.basicConfig(level=logging.INFO, 
                       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # 测试资源跟踪器
    print("资源跟踪器测试")
    
    # 获取资源跟踪器实例
    tracker = get_resource_tracker()
    
    # 等待资源更新
    time.sleep(2)
    
    # 查看资源信息
    memory_info = tracker.get_resource_info("memory")
    disk_info = tracker.get_resource_info("disk")
    gpu_info = tracker.get_resource_info("gpu")
    
    print("\n内存信息:")
    print(f"总内存: {memory_info['total'] / (1024**3):.2f} GB")
    print(f"已用内存: {memory_info['used'] / (1024**3):.2f} GB")
    print(f"可用内存: {memory_info['available'] / (1024**3):.2f} GB")
    print(f"使用率: {memory_info['percent']}%")
    
    print("\n磁盘信息:")
    print(f"总空间: {disk_info['total'] / (1024**3):.2f} GB")
    print(f"已用空间: {disk_info['used'] / (1024**3):.2f} GB")
    print(f"可用空间: {disk_info['free'] / (1024**3):.2f} GB")
    print(f"使用率: {disk_info['percent']}%")
    print(f"路径: {disk_info['path']}")
    
    print("\nGPU信息:")
    if gpu_info.get("available", False):
        for i, device in enumerate(gpu_info["devices"]):
            print(f"GPU {i}: {device['name']}")
            print(f"  总显存: {device['total_memory'] / (1024**3):.2f} GB")
            print(f"  已用显存: {device['used_memory'] / (1024**3):.2f} GB")
            print(f"  可用显存: {device['free_memory'] / (1024**3):.2f} GB")
            print(f"  使用率: {device['memory_usage']*100:.1f}%")
    else:
        print(f"无可用GPU: {gpu_info.get('error', 'Unknown')}")
    
    # 停止监控
    tracker.stop_monitoring()
    print("\n测试完成") 