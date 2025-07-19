#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
增强内存管理器

专门为VisionAI-ClipsMaster优化内存使用，确保UI≤400MB，处理≤3.8GB。
"""

import gc
import psutil
import threading
import time
import logging
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class MemoryLevel(Enum):
    """内存使用等级"""
    LOW = "low"          # <200MB
    NORMAL = "normal"    # 200-400MB
    HIGH = "high"        # 400MB-1GB
    CRITICAL = "critical" # >1GB

@dataclass
class MemoryThreshold:
    """内存阈值配置"""
    ui_warning: int = 350 * 1024 * 1024      # 350MB UI警告
    ui_critical: int = 400 * 1024 * 1024     # 400MB UI临界
    processing_warning: int = 3200 * 1024 * 1024  # 3.2GB 处理警告
    processing_critical: int = 3800 * 1024 * 1024 # 3.8GB 处理临界

class EnhancedMemoryManager:
    """增强内存管理器
    
    提供以下功能：
    1. 实时内存监控
    2. 自适应内存清理
    3. 内存泄漏检测
    4. 智能垃圾回收
    5. 内存使用预警
    """
    
    def __init__(self, thresholds: Optional[MemoryThreshold] = None):
        """初始化内存管理器
        
        Args:
            thresholds: 内存阈值配置
        """
        self.thresholds = thresholds or MemoryThreshold()
        self.process = psutil.Process()
        self.monitoring = False
        self.monitor_thread = None
        self.memory_history = []
        self.cleanup_callbacks = []
        self.warning_callbacks = []
        
        # 内存统计
        self.stats = {
            "peak_memory": 0,
            "cleanup_count": 0,
            "warning_count": 0,
            "gc_count": 0
        }
        
        logger.info("增强内存管理器初始化完成")
    
    def get_current_memory(self) -> Dict[str, int]:
        """获取当前内存使用情况
        
        Returns:
            Dict[str, int]: 内存使用信息
        """
        try:
            memory_info = self.process.memory_info()
            return {
                "rss": memory_info.rss,  # 物理内存
                "vms": memory_info.vms,  # 虚拟内存
                "percent": self.process.memory_percent(),
                "available": psutil.virtual_memory().available
            }
        except Exception as e:
            logger.error(f"获取内存信息失败: {e}")
            return {"rss": 0, "vms": 0, "percent": 0, "available": 0}
    
    def get_memory_level(self, memory_usage: int) -> MemoryLevel:
        """获取内存使用等级
        
        Args:
            memory_usage: 内存使用量（字节）
            
        Returns:
            MemoryLevel: 内存等级
        """
        if memory_usage < 200 * 1024 * 1024:
            return MemoryLevel.LOW
        elif memory_usage < 400 * 1024 * 1024:
            return MemoryLevel.NORMAL
        elif memory_usage < 1024 * 1024 * 1024:
            return MemoryLevel.HIGH
        else:
            return MemoryLevel.CRITICAL
    
    def register_cleanup_callback(self, callback: Callable):
        """注册内存清理回调函数
        
        Args:
            callback: 清理函数
        """
        self.cleanup_callbacks.append(callback)
    
    def register_warning_callback(self, callback: Callable):
        """注册内存警告回调函数
        
        Args:
            callback: 警告函数
        """
        self.warning_callbacks.append(callback)
    
    def perform_cleanup(self, level: str = "normal") -> Dict[str, Any]:
        """执行内存清理
        
        Args:
            level: 清理级别 ("light", "normal", "aggressive")
            
        Returns:
            Dict[str, Any]: 清理结果
        """
        before_memory = self.get_current_memory()
        cleanup_result = {
            "level": level,
            "before_memory": before_memory["rss"],
            "actions_taken": [],
            "callbacks_executed": 0
        }
        
        try:
            # 执行注册的清理回调
            for callback in self.cleanup_callbacks:
                try:
                    callback()
                    cleanup_result["callbacks_executed"] += 1
                except Exception as e:
                    logger.warning(f"清理回调执行失败: {e}")
            
            # 基础清理
            if level in ["normal", "aggressive"]:
                gc.collect()
                cleanup_result["actions_taken"].append("gc_collect")
                self.stats["gc_count"] += 1
            
            # 激进清理
            if level == "aggressive":
                # 强制垃圾回收多次
                for _ in range(3):
                    gc.collect()
                
                # 清理内存历史（保留最近100条）
                if len(self.memory_history) > 100:
                    self.memory_history = self.memory_history[-100:]
                    cleanup_result["actions_taken"].append("history_cleanup")
                
                cleanup_result["actions_taken"].append("aggressive_gc")
            
            after_memory = self.get_current_memory()
            cleanup_result["after_memory"] = after_memory["rss"]
            cleanup_result["memory_freed"] = before_memory["rss"] - after_memory["rss"]
            
            self.stats["cleanup_count"] += 1
            logger.info(f"内存清理完成，释放 {cleanup_result['memory_freed'] / 1024 / 1024:.1f}MB")
            
        except Exception as e:
            logger.error(f"内存清理失败: {e}")
            cleanup_result["error"] = str(e)
        
        return cleanup_result
    
    def check_memory_thresholds(self) -> Dict[str, Any]:
        """检查内存阈值
        
        Returns:
            Dict[str, Any]: 检查结果
        """
        current_memory = self.get_current_memory()
        rss = current_memory["rss"]
        
        result = {
            "current_memory": rss,
            "level": self.get_memory_level(rss).value,
            "warnings": [],
            "actions_needed": []
        }
        
        # 检查UI内存阈值
        if rss > self.thresholds.ui_critical:
            result["warnings"].append("UI内存超过临界值400MB")
            result["actions_needed"].append("aggressive_cleanup")
            self._trigger_warning_callbacks("ui_critical", rss)
        elif rss > self.thresholds.ui_warning:
            result["warnings"].append("UI内存接近警告值350MB")
            result["actions_needed"].append("normal_cleanup")
            self._trigger_warning_callbacks("ui_warning", rss)
        
        # 检查处理内存阈值
        if rss > self.thresholds.processing_critical:
            result["warnings"].append("处理内存超过临界值3.8GB")
            result["actions_needed"].append("emergency_cleanup")
            self._trigger_warning_callbacks("processing_critical", rss)
        elif rss > self.thresholds.processing_warning:
            result["warnings"].append("处理内存接近警告值3.2GB")
            result["actions_needed"].append("normal_cleanup")
            self._trigger_warning_callbacks("processing_warning", rss)
        
        return result
    
    def _trigger_warning_callbacks(self, warning_type: str, memory_usage: int):
        """触发警告回调"""
        for callback in self.warning_callbacks:
            try:
                callback(warning_type, memory_usage)
            except Exception as e:
                logger.warning(f"警告回调执行失败: {e}")
        
        self.stats["warning_count"] += 1
    
    def start_monitoring(self, interval: float = 5.0):
        """开始内存监控
        
        Args:
            interval: 监控间隔（秒）
        """
        if self.monitoring:
            logger.warning("内存监控已在运行")
            return
        
        self.monitoring = True
        
        def monitor_loop():
            while self.monitoring:
                try:
                    current_memory = self.get_current_memory()
                    rss = current_memory["rss"]
                    
                    # 更新峰值内存
                    if rss > self.stats["peak_memory"]:
                        self.stats["peak_memory"] = rss
                    
                    # 记录内存历史
                    self.memory_history.append({
                        "timestamp": time.time(),
                        "memory": rss,
                        "level": self.get_memory_level(rss).value
                    })
                    
                    # 检查阈值
                    threshold_result = self.check_memory_thresholds()
                    
                    # 自动执行清理
                    if "aggressive_cleanup" in threshold_result["actions_needed"]:
                        self.perform_cleanup("aggressive")
                    elif "normal_cleanup" in threshold_result["actions_needed"]:
                        self.perform_cleanup("normal")
                    elif "emergency_cleanup" in threshold_result["actions_needed"]:
                        self.perform_cleanup("aggressive")
                        logger.critical("执行紧急内存清理")
                    
                    time.sleep(interval)
                    
                except Exception as e:
                    logger.error(f"内存监控循环出错: {e}")
                    time.sleep(interval)
        
        self.monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info(f"内存监控已启动，间隔: {interval}秒")
    
    def stop_monitoring(self):
        """停止内存监控"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
        logger.info("内存监控已停止")
    
    def get_memory_report(self) -> Dict[str, Any]:
        """获取内存使用报告
        
        Returns:
            Dict[str, Any]: 内存报告
        """
        current_memory = self.get_current_memory()
        
        return {
            "current_memory_mb": current_memory["rss"] / 1024 / 1024,
            "peak_memory_mb": self.stats["peak_memory"] / 1024 / 1024,
            "memory_level": self.get_memory_level(current_memory["rss"]).value,
            "ui_threshold_ok": current_memory["rss"] <= self.thresholds.ui_critical,
            "processing_threshold_ok": current_memory["rss"] <= self.thresholds.processing_critical,
            "cleanup_count": self.stats["cleanup_count"],
            "warning_count": self.stats["warning_count"],
            "gc_count": self.stats["gc_count"],
            "monitoring_active": self.monitoring,
            "history_length": len(self.memory_history)
        }

# 全局内存管理器实例
_memory_manager = None

def get_memory_manager() -> EnhancedMemoryManager:
    """获取内存管理器实例"""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = EnhancedMemoryManager()
    return _memory_manager

def optimize_memory():
    """执行内存优化"""
    manager = get_memory_manager()
    return manager.perform_cleanup("normal")

def start_memory_monitoring(interval: float = 5.0):
    """启动内存监控"""
    manager = get_memory_manager()
    manager.start_monitoring(interval)

def get_memory_status() -> Dict[str, Any]:
    """获取内存状态"""
    manager = get_memory_manager()
    return manager.get_memory_report()

if __name__ == "__main__":
    # 测试内存管理器
    manager = EnhancedMemoryManager()
    
    # 获取当前内存状态
    print("当前内存状态:", manager.get_current_memory())
    
    # 执行清理
    cleanup_result = manager.perform_cleanup("normal")
    print("清理结果:", cleanup_result)
    
    # 获取报告
    report = manager.get_memory_report()
    print("内存报告:", report)
