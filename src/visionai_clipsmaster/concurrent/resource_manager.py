#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 资源管理器模块

提供系统资源监控和管理功能，支持：
1. 内存使用监控和限制
2. CPU使用率监控
3. 磁盘I/O监控
4. 4GB内存设备优化
"""

import psutil
import threading
import time
import logging
from typing import Dict, Any, Optional, List, Callable
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)

class ResourceType(Enum):
    """资源类型"""
    MEMORY = "memory"
    CPU = "cpu"
    DISK_IO = "disk_io"
    NETWORK = "network"

@dataclass
class ResourceLimit:
    """资源限制配置"""
    resource_type: ResourceType
    max_value: float
    warning_threshold: float = 0.8
    critical_threshold: float = 0.9
    unit: str = ""

@dataclass
class ResourceUsage:
    """资源使用情况"""
    resource_type: ResourceType
    current_value: float
    max_value: float
    percentage: float
    unit: str = ""
    timestamp: float = 0.0

@dataclass
class ResourceAllocation:
    """资源分配记录"""
    allocation_id: str
    resource_type: ResourceType
    allocated_amount: float
    requester: str
    timestamp: float
    is_active: bool = True

class ResourceManager:
    """系统资源管理器"""
    
    def __init__(self, 
                 max_memory_gb: float = 3.8,
                 max_cpu_percent: float = 80.0,
                 max_disk_io_mbps: float = 100.0,
                 enable_monitoring: bool = True):
        """初始化资源管理器
        
        Args:
            max_memory_gb: 最大内存使用限制（GB）
            max_cpu_percent: 最大CPU使用率限制（%）
            max_disk_io_mbps: 最大磁盘I/O限制（MB/s）
            enable_monitoring: 是否启用实时监控
        """
        self.max_memory_gb = max_memory_gb
        self.max_cpu_percent = max_cpu_percent
        self.max_disk_io_mbps = max_disk_io_mbps
        self.enable_monitoring = enable_monitoring
        
        # 资源限制配置
        self.resource_limits = {
            ResourceType.MEMORY: ResourceLimit(
                ResourceType.MEMORY, 
                max_memory_gb * 1024 * 1024 * 1024,  # 转换为字节
                0.8, 0.9, "GB"
            ),
            ResourceType.CPU: ResourceLimit(
                ResourceType.CPU,
                max_cpu_percent,
                0.7, 0.85, "%"
            ),
            ResourceType.DISK_IO: ResourceLimit(
                ResourceType.DISK_IO,
                max_disk_io_mbps * 1024 * 1024,  # 转换为字节/秒
                0.8, 0.9, "MB/s"
            )
        }
        
        # 资源分配跟踪
        self.allocations: Dict[str, ResourceAllocation] = {}
        self.allocation_counter = 0
        
        # 监控数据
        self.usage_history: Dict[ResourceType, List[ResourceUsage]] = {
            ResourceType.MEMORY: [],
            ResourceType.CPU: [],
            ResourceType.DISK_IO: []
        }
        
        # 回调函数
        self.warning_callbacks: List[Callable] = []
        self.critical_callbacks: List[Callable] = []
        
        # 控制标志
        self.is_monitoring = False
        self.monitor_thread = None
        self.shutdown_event = threading.Event()
        
        # 启动监控
        if enable_monitoring:
            self.start_monitoring()
            
        logger.info(f"资源管理器初始化完成: 内存限制={max_memory_gb}GB, CPU限制={max_cpu_percent}%")
        
    def get_current_usage(self, resource_type: ResourceType) -> ResourceUsage:
        """获取当前资源使用情况"""
        current_time = time.time()
        
        if resource_type == ResourceType.MEMORY:
            memory = psutil.virtual_memory()
            current_bytes = memory.used
            max_bytes = self.resource_limits[ResourceType.MEMORY].max_value
            percentage = (current_bytes / max_bytes) * 100
            
            return ResourceUsage(
                resource_type=ResourceType.MEMORY,
                current_value=current_bytes / (1024**3),  # 转换为GB
                max_value=max_bytes / (1024**3),
                percentage=percentage,
                unit="GB",
                timestamp=current_time
            )
            
        elif resource_type == ResourceType.CPU:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            max_percent = self.resource_limits[ResourceType.CPU].max_value
            percentage = (cpu_percent / max_percent) * 100
            
            return ResourceUsage(
                resource_type=ResourceType.CPU,
                current_value=cpu_percent,
                max_value=max_percent,
                percentage=percentage,
                unit="%",
                timestamp=current_time
            )
            
        elif resource_type == ResourceType.DISK_IO:
            disk_io = psutil.disk_io_counters()
            if disk_io:
                # 简化的磁盘I/O计算（实际应该基于时间间隔）
                current_io = (disk_io.read_bytes + disk_io.write_bytes) / (1024**2)  # MB
                max_io = self.resource_limits[ResourceType.DISK_IO].max_value / (1024**2)
                percentage = (current_io / max_io) * 100 if max_io > 0 else 0
                
                return ResourceUsage(
                    resource_type=ResourceType.DISK_IO,
                    current_value=current_io,
                    max_value=max_io,
                    percentage=percentage,
                    unit="MB/s",
                    timestamp=current_time
                )
        
        # 默认返回空使用情况
        return ResourceUsage(
            resource_type=resource_type,
            current_value=0.0,
            max_value=0.0,
            percentage=0.0,
            timestamp=current_time
        )
        
    def check_resource_availability(self, resource_type: ResourceType, required_amount: float) -> bool:
        """检查资源是否可用"""
        current_usage = self.get_current_usage(resource_type)
        limit = self.resource_limits[resource_type]
        
        if resource_type == ResourceType.MEMORY:
            # 检查内存是否足够
            required_bytes = required_amount * 1024 * 1024 * 1024  # GB转字节
            available_bytes = limit.max_value - (current_usage.current_value * 1024 * 1024 * 1024)
            return available_bytes >= required_bytes
            
        elif resource_type == ResourceType.CPU:
            # 检查CPU是否可用
            available_percent = limit.max_value - current_usage.current_value
            return available_percent >= required_amount
            
        return True
        
    def allocate_resource(self, resource_type: ResourceType, amount: float, requester: str) -> Optional[str]:
        """分配资源"""
        if not self.check_resource_availability(resource_type, amount):
            logger.warning(f"资源不足，无法分配 {amount} {resource_type.value} 给 {requester}")
            return None
            
        # 创建分配记录
        allocation_id = f"alloc_{self.allocation_counter}_{int(time.time())}"
        self.allocation_counter += 1
        
        allocation = ResourceAllocation(
            allocation_id=allocation_id,
            resource_type=resource_type,
            allocated_amount=amount,
            requester=requester,
            timestamp=time.time(),
            is_active=True
        )
        
        self.allocations[allocation_id] = allocation
        logger.debug(f"资源分配成功: {allocation_id} - {amount} {resource_type.value} 给 {requester}")
        
        return allocation_id
        
    def release_resource(self, allocation_id: str) -> bool:
        """释放资源"""
        if allocation_id not in self.allocations:
            logger.warning(f"未找到分配记录: {allocation_id}")
            return False
            
        allocation = self.allocations[allocation_id]
        allocation.is_active = False
        
        logger.debug(f"资源释放成功: {allocation_id}")
        return True
        
    def start_monitoring(self):
        """启动资源监控"""
        if self.is_monitoring:
            return
            
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        logger.info("资源监控已启动")
        
    def stop_monitoring(self):
        """停止资源监控"""
        self.is_monitoring = False
        self.shutdown_event.set()
        
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)
            
        logger.info("资源监控已停止")
        
    def _monitor_loop(self):
        """监控循环"""
        while self.is_monitoring and not self.shutdown_event.is_set():
            try:
                # 监控各种资源
                for resource_type in [ResourceType.MEMORY, ResourceType.CPU, ResourceType.DISK_IO]:
                    usage = self.get_current_usage(resource_type)
                    
                    # 添加到历史记录
                    history = self.usage_history[resource_type]
                    history.append(usage)
                    
                    # 保持历史记录大小
                    if len(history) > 1000:
                        history.pop(0)
                    
                    # 检查阈值
                    limit = self.resource_limits[resource_type]
                    
                    if usage.percentage >= limit.critical_threshold * 100:
                        self._trigger_critical_alert(usage, limit)
                    elif usage.percentage >= limit.warning_threshold * 100:
                        self._trigger_warning_alert(usage, limit)
                
                # 等待下次监控
                time.sleep(5)  # 每5秒监控一次
                
            except Exception as e:
                logger.error(f"资源监控异常: {e}")
                time.sleep(10)
                
    def _trigger_warning_alert(self, usage: ResourceUsage, limit: ResourceLimit):
        """触发警告回调"""
        for callback in self.warning_callbacks:
            try:
                callback(usage, limit, "warning")
            except Exception as e:
                logger.error(f"警告回调执行失败: {e}")
                
    def _trigger_critical_alert(self, usage: ResourceUsage, limit: ResourceLimit):
        """触发严重警告回调"""
        for callback in self.critical_callbacks:
            try:
                callback(usage, limit, "critical")
            except Exception as e:
                logger.error(f"严重警告回调执行失败: {e}")
                
    def add_warning_callback(self, callback: Callable):
        """添加警告回调函数"""
        self.warning_callbacks.append(callback)
        
    def add_critical_callback(self, callback: Callable):
        """添加严重警告回调函数"""
        self.critical_callbacks.append(callback)
        
    def get_stats(self) -> Dict[str, Any]:
        """获取资源管理统计信息"""
        stats = {
            "resource_limits": {rt.value: {
                "max_value": limit.max_value,
                "warning_threshold": limit.warning_threshold,
                "critical_threshold": limit.critical_threshold,
                "unit": limit.unit
            } for rt, limit in self.resource_limits.items()},
            "current_usage": {},
            "active_allocations": len([a for a in self.allocations.values() if a.is_active]),
            "total_allocations": len(self.allocations),
            "is_monitoring": self.is_monitoring
        }
        
        # 添加当前使用情况
        for resource_type in [ResourceType.MEMORY, ResourceType.CPU, ResourceType.DISK_IO]:
            usage = self.get_current_usage(resource_type)
            stats["current_usage"][resource_type.value] = {
                "current_value": usage.current_value,
                "max_value": usage.max_value,
                "percentage": usage.percentage,
                "unit": usage.unit
            }
            
        return stats
