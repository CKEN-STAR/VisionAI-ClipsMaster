#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
性能优化器
优化内存使用，提升推理速度，为生产环境部署做准备
"""

import os
import gc
import time
import psutil
import logging
import threading
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path
import json

# 尝试导入性能优化相关库
try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

logger = logging.getLogger(__name__)

class PerformanceOptimizer:
    """性能优化器"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化性能优化器
        
        Args:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        
        # 性能监控
        self.monitoring_active = False
        self.performance_data = []
        self.monitoring_thread = None
        
        # 优化状态
        self.optimization_history = []
        
        # 回调函数
        self.alert_callback = None
        
        logger.info("性能优化器初始化完成")
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """加载配置"""
        default_config = {
            "memory": {
                "max_usage_percent": 85,  # 最大内存使用率
                "cleanup_threshold": 80,  # 清理阈值
                "emergency_threshold": 95,  # 紧急阈值
                "monitor_interval": 5  # 监控间隔（秒）
            },
            "cpu": {
                "max_usage_percent": 90,
                "optimization_threshold": 80
            },
            "gpu": {
                "max_memory_percent": 90,
                "cleanup_threshold": 85
            },
            "optimization": {
                "auto_cleanup": True,
                "aggressive_mode": False,
                "cache_management": True
            },
            "alerts": {
                "memory_warning": True,
                "cpu_warning": True,
                "performance_degradation": True
            }
        }
        
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except Exception as e:
                logger.warning(f"加载配置失败: {e}")
        
        return default_config
    
    def set_alert_callback(self, callback: Callable[[str, Dict[str, Any]], None]):
        """设置警报回调函数"""
        self.alert_callback = callback
    
    def start_monitoring(self):
        """开始性能监控"""
        if self.monitoring_active:
            logger.warning("性能监控已在运行")
            return
        
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        logger.info("性能监控已启动")
    
    def stop_monitoring(self):
        """停止性能监控"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        logger.info("性能监控已停止")
    
    def _monitoring_loop(self):
        """监控循环"""
        interval = self.config["memory"]["monitor_interval"]
        
        while self.monitoring_active:
            try:
                # 收集性能数据
                perf_data = self.get_system_performance()
                self.performance_data.append(perf_data)
                
                # 保持最近1000条记录
                if len(self.performance_data) > 1000:
                    self.performance_data = self.performance_data[-1000:]
                
                # 检查是否需要优化
                self._check_optimization_triggers(perf_data)
                
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"性能监控错误: {str(e)}")
                time.sleep(interval)
    
    def get_system_performance(self) -> Dict[str, Any]:
        """获取系统性能数据"""
        try:
            # 内存信息
            memory = psutil.virtual_memory()
            memory_info = {
                "total": memory.total,
                "available": memory.available,
                "used": memory.used,
                "percent": memory.percent
            }
            
            # CPU信息
            cpu_info = {
                "percent": psutil.cpu_percent(interval=1),
                "count": psutil.cpu_count(),
                "freq": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
            }
            
            # GPU信息（如果可用）
            gpu_info = {}
            if HAS_TORCH and torch.cuda.is_available():
                try:
                    gpu_info = {
                        "device_count": torch.cuda.device_count(),
                        "current_device": torch.cuda.current_device(),
                        "memory_allocated": torch.cuda.memory_allocated(),
                        "memory_reserved": torch.cuda.memory_reserved(),
                        "memory_cached": torch.cuda.memory_cached() if hasattr(torch.cuda, 'memory_cached') else 0
                    }
                except Exception as e:
                    logger.warning(f"获取GPU信息失败: {e}")
            
            # 进程信息
            process = psutil.Process()
            process_info = {
                "memory_info": process.memory_info()._asdict(),
                "cpu_percent": process.cpu_percent(),
                "num_threads": process.num_threads()
            }
            
            return {
                "timestamp": time.time(),
                "memory": memory_info,
                "cpu": cpu_info,
                "gpu": gpu_info,
                "process": process_info
            }
            
        except Exception as e:
            logger.error(f"获取系统性能数据失败: {str(e)}")
            return {"timestamp": time.time(), "error": str(e)}
    
    def _check_optimization_triggers(self, perf_data: Dict[str, Any]):
        """检查优化触发条件"""
        try:
            memory_config = self.config["memory"]
            cpu_config = self.config["cpu"]
            
            # 检查内存使用率
            memory_percent = perf_data.get("memory", {}).get("percent", 0)
            if memory_percent > memory_config["emergency_threshold"]:
                self._trigger_emergency_cleanup()
                self._send_alert("memory_emergency", {
                    "memory_percent": memory_percent,
                    "threshold": memory_config["emergency_threshold"]
                })
            elif memory_percent > memory_config["cleanup_threshold"]:
                if self.config["optimization"]["auto_cleanup"]:
                    self.optimize_memory_usage()
                self._send_alert("memory_warning", {
                    "memory_percent": memory_percent,
                    "threshold": memory_config["cleanup_threshold"]
                })
            
            # 检查CPU使用率
            cpu_percent = perf_data.get("cpu", {}).get("percent", 0)
            if cpu_percent > cpu_config["optimization_threshold"]:
                self._send_alert("cpu_warning", {
                    "cpu_percent": cpu_percent,
                    "threshold": cpu_config["optimization_threshold"]
                })
            
            # 检查GPU内存（如果可用）
            if perf_data.get("gpu") and HAS_TORCH:
                gpu_memory_percent = self._calculate_gpu_memory_percent(perf_data["gpu"])
                if gpu_memory_percent > self.config["gpu"]["cleanup_threshold"]:
                    self.optimize_gpu_memory()
                    
        except Exception as e:
            logger.error(f"检查优化触发条件失败: {str(e)}")
    
    def _calculate_gpu_memory_percent(self, gpu_info: Dict[str, Any]) -> float:
        """计算GPU内存使用百分比"""
        try:
            if HAS_TORCH and torch.cuda.is_available():
                total_memory = torch.cuda.get_device_properties(0).total_memory
                used_memory = gpu_info.get("memory_allocated", 0)
                return (used_memory / total_memory) * 100
            return 0.0
        except Exception:
            return 0.0
    
    def _send_alert(self, alert_type: str, data: Dict[str, Any]):
        """发送警报"""
        if self.alert_callback and self.config["alerts"].get(alert_type, False):
            try:
                self.alert_callback(alert_type, data)
            except Exception as e:
                logger.warning(f"发送警报失败: {e}")
    
    def optimize_memory_usage(self) -> Dict[str, Any]:
        """优化内存使用"""
        try:
            logger.info("开始内存优化")
            start_time = time.time()
            
            # 记录优化前的内存状态
            before_memory = psutil.virtual_memory().percent
            
            optimization_actions = []
            
            # 1. Python垃圾回收
            collected = gc.collect()
            optimization_actions.append(f"Python GC: 回收 {collected} 个对象")
            
            # 2. 清理PyTorch缓存（如果可用）
            if HAS_TORCH and torch.cuda.is_available():
                torch.cuda.empty_cache()
                optimization_actions.append("清理PyTorch GPU缓存")
            
            # 3. 清理NumPy缓存（如果可用）
            if HAS_NUMPY:
                # NumPy没有直接的缓存清理方法，但可以强制垃圾回收
                gc.collect()
                optimization_actions.append("强制NumPy垃圾回收")
            
            # 4. 清理系统缓存（如果配置允许）
            if self.config["optimization"]["cache_management"]:
                self._clear_system_caches()
                optimization_actions.append("清理系统缓存")
            
            # 记录优化后的内存状态
            after_memory = psutil.virtual_memory().percent
            memory_saved = before_memory - after_memory
            
            processing_time = time.time() - start_time
            
            result = {
                "success": True,
                "before_memory_percent": before_memory,
                "after_memory_percent": after_memory,
                "memory_saved_percent": memory_saved,
                "processing_time": processing_time,
                "actions": optimization_actions
            }
            
            # 记录优化历史
            self.optimization_history.append({
                "timestamp": time.time(),
                "type": "memory_optimization",
                "result": result
            })
            
            logger.info(f"内存优化完成，节省 {memory_saved:.2f}% 内存")
            return result
            
        except Exception as e:
            logger.error(f"内存优化失败: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def optimize_gpu_memory(self) -> Dict[str, Any]:
        """优化GPU内存"""
        try:
            if not HAS_TORCH or not torch.cuda.is_available():
                return {"success": False, "error": "GPU不可用"}
            
            logger.info("开始GPU内存优化")
            start_time = time.time()
            
            # 记录优化前的GPU内存
            before_allocated = torch.cuda.memory_allocated()
            before_reserved = torch.cuda.memory_reserved()
            
            # 清理GPU缓存
            torch.cuda.empty_cache()
            
            # 强制垃圾回收
            gc.collect()
            
            # 记录优化后的GPU内存
            after_allocated = torch.cuda.memory_allocated()
            after_reserved = torch.cuda.memory_reserved()
            
            processing_time = time.time() - start_time
            
            result = {
                "success": True,
                "before_allocated": before_allocated,
                "after_allocated": after_allocated,
                "before_reserved": before_reserved,
                "after_reserved": after_reserved,
                "memory_freed": before_allocated - after_allocated,
                "processing_time": processing_time
            }
            
            logger.info(f"GPU内存优化完成，释放 {result['memory_freed']} 字节")
            return result
            
        except Exception as e:
            logger.error(f"GPU内存优化失败: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _trigger_emergency_cleanup(self):
        """触发紧急清理"""
        try:
            logger.warning("触发紧急内存清理")
            
            # 激进的内存清理
            for _ in range(3):
                gc.collect()
            
            if HAS_TORCH and torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.synchronize()
            
            # 清理性能数据历史（保留最近100条）
            if len(self.performance_data) > 100:
                self.performance_data = self.performance_data[-100:]
            
            # 清理优化历史（保留最近50条）
            if len(self.optimization_history) > 50:
                self.optimization_history = self.optimization_history[-50:]
            
            logger.info("紧急清理完成")
            
        except Exception as e:
            logger.error(f"紧急清理失败: {str(e)}")
    
    def _clear_system_caches(self):
        """清理系统缓存"""
        try:
            # 这里可以实现系统级缓存清理
            # 注意：需要根据操作系统进行适配
            pass
        except Exception as e:
            logger.warning(f"清理系统缓存失败: {e}")
    
    def get_performance_report(self) -> Dict[str, Any]:
        """获取性能报告"""
        try:
            if not self.performance_data:
                return {"error": "没有性能数据"}
            
            # 计算统计信息
            memory_usage = [data.get("memory", {}).get("percent", 0) for data in self.performance_data]
            cpu_usage = [data.get("cpu", {}).get("percent", 0) for data in self.performance_data]
            
            report = {
                "data_points": len(self.performance_data),
                "time_range": {
                    "start": self.performance_data[0]["timestamp"],
                    "end": self.performance_data[-1]["timestamp"]
                },
                "memory": {
                    "avg": sum(memory_usage) / len(memory_usage),
                    "max": max(memory_usage),
                    "min": min(memory_usage),
                    "current": memory_usage[-1] if memory_usage else 0
                },
                "cpu": {
                    "avg": sum(cpu_usage) / len(cpu_usage),
                    "max": max(cpu_usage),
                    "min": min(cpu_usage),
                    "current": cpu_usage[-1] if cpu_usage else 0
                },
                "optimizations": len(self.optimization_history),
                "last_optimization": self.optimization_history[-1] if self.optimization_history else None
            }
            
            return report
            
        except Exception as e:
            logger.error(f"生成性能报告失败: {str(e)}")
            return {"error": str(e)}
    
    def cleanup(self):
        """清理资源"""
        try:
            self.stop_monitoring()
            self.performance_data.clear()
            self.optimization_history.clear()
            logger.info("性能优化器资源清理完成")
        except Exception as e:
            logger.error(f"清理资源失败: {str(e)}")
    
    def __del__(self):
        """析构函数"""
        self.cleanup()
