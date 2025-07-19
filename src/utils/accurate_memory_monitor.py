#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 精确内存监控器
"""

import psutil
import threading
import time
from typing import List, Dict, Any

class AccurateMemoryMonitor:
    """精确内存监控器"""
    
    def __init__(self):
        self.process = psutil.Process()
        self.monitoring = False
        self.memory_history = []
        self.monitor_thread = None
    
    def start_monitoring(self):
        """开始监控"""
        self.monitoring = True
        self.memory_history = []
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """停止监控"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)
    
    def _monitor_loop(self):
        """监控循环"""
        while self.monitoring:
            # 只监控当前进程的内存使用
            memory_info = self.process.memory_info()
            memory_gb = memory_info.rss / 1024**3
            
            self.memory_history.append({
                "timestamp": time.time(),
                "rss_gb": memory_gb,
                "vms_gb": memory_info.vms / 1024**3
            })
            
            # 保持最近1000个记录
            if len(self.memory_history) > 1000:
                self.memory_history = self.memory_history[-1000:]
            
            time.sleep(1)  # 每秒监控一次
    
    def get_current_memory_usage(self) -> float:
        """获取当前内存使用（GB）"""
        memory_info = self.process.memory_info()
        return memory_info.rss / 1024**3
    
    def get_peak_memory_usage(self) -> float:
        """获取峰值内存使用"""
        if not self.memory_history:
            return self.get_current_memory_usage()
        
        return max(record["rss_gb"] for record in self.memory_history)
    
    def get_memory_statistics(self) -> Dict[str, float]:
        """获取内存统计信息"""
        if not self.memory_history:
            current = self.get_current_memory_usage()
            return {
                "current_gb": current,
                "peak_gb": current,
                "average_gb": current,
                "min_gb": current
            }
        
        memory_values = [record["rss_gb"] for record in self.memory_history]
        
        return {
            "current_gb": self.get_current_memory_usage(),
            "peak_gb": max(memory_values),
            "average_gb": sum(memory_values) / len(memory_values),
            "min_gb": min(memory_values)
        }

# 全局精确内存监控器
accurate_memory_monitor = AccurateMemoryMonitor()
