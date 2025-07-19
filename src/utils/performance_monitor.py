#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 性能监控器
"""

import time
import psutil
import threading
from typing import Dict, Any

class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.monitoring = False
        self.stats = {
            "memory_usage": [],
            "cpu_usage": [],
            "response_times": []
        }
    
    def start_monitoring(self):
        """开始监控"""
        self.monitoring = True
        thread = threading.Thread(target=self._monitor_loop)
        thread.daemon = True
        thread.start()
    
    def stop_monitoring(self):
        """停止监控"""
        self.monitoring = False
    
    def _monitor_loop(self):
        """监控循环"""
        while self.monitoring:
            # 记录内存使用
            memory = psutil.virtual_memory()
            self.stats["memory_usage"].append({
                "timestamp": time.time(),
                "usage_mb": memory.used / 1024**2,
                "percent": memory.percent
            })
            
            # 记录CPU使用
            cpu_percent = psutil.cpu_percent(interval=1)
            self.stats["cpu_usage"].append({
                "timestamp": time.time(),
                "percent": cpu_percent
            })
            
            # 保持最近100个记录
            for key in self.stats:
                if len(self.stats[key]) > 100:
                    self.stats[key] = self.stats[key][-100:]
            
            time.sleep(5)  # 每5秒监控一次
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.stats.copy()
    
    def record_response_time(self, operation: str, duration: float):
        """记录响应时间"""
        self.stats["response_times"].append({
            "timestamp": time.time(),
            "operation": operation,
            "duration": duration
        })

# 全局监控器实例
performance_monitor = PerformanceMonitor()
