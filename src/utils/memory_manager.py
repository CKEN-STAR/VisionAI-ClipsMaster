"""内存管理器模块"""

import os
import psutil
import logging
import gc
import time
import threading
from typing import Dict, Optional, List, Any, Tuple

from src.utils.exceptions import MemoryError


class MemoryManager:
    """内存管理器类，用于处理运行时内存隔离和管理"""

    def __init__(self, min_required_memory: float = 2.0):
        """
        初始化内存管理器
        
        Args:
            min_required_memory: 最小所需内存（GB）
        """
        self.min_required_memory = min_required_memory * 1024 * 1024 * 1024  # 转换为字节
        self.process = psutil.Process(os.getpid())
        self.logger = logging.getLogger(__name__)
        
        # 初始化内存使用统计
        self.memory_stats = {
            'total_allocated': 0,
            'peak_usage': 0,
            'current_usage': 0
        }
        
        # 监控线程相关
        self._monitor_thread = None
        self._monitoring = False
        self._monitor_interval = 5.0  # 默认监控间隔5秒

    def check_system_memory(self) -> bool:
        """
        检查系统是否有足够的可用内存
        
        Returns:
            bool: 是否有足够内存
        """
        virtual_memory = psutil.virtual_memory()
        available_memory = virtual_memory.available
        
        if available_memory < self.min_required_memory:
            self.logger.error(
                f"系统可用内存不足: {available_memory / 1024 / 1024 / 1024:.2f}GB, "
                f"需要: {self.min_required_memory / 1024 / 1024 / 1024:.2f}GB"
            )
            return False
        return True

    def get_current_memory_usage(self) -> float:
        """
        获取当前进程的内存使用量
        
        Returns:
            float: 当前内存使用量（字节）
        """
        memory_info = self.process.memory_info()
        self.memory_stats['current_usage'] = memory_info.rss
        self.memory_stats['peak_usage'] = max(
            self.memory_stats['peak_usage'],
            memory_info.rss
        )
        return memory_info.rss

    def allocate_memory(self, size: int, purpose: str) -> bool:
        """
        为特定用途分配内存
        
        Args:
            size: 需要分配的内存大小（字节）
            purpose: 内存用途描述
            
        Returns:
            bool: 是否成功分配
            
        Raises:
            MemoryError: 内存分配失败时抛出
        """
        if not self.check_system_memory():
            raise MemoryError("系统内存不足，无法分配请求的内存")
            
        current_usage = self.get_current_memory_usage()
        available_memory = psutil.virtual_memory().available
        
        if current_usage + size > available_memory:
            raise MemoryError(
                f"无法为{purpose}分配{size / 1024 / 1024 / 1024:.2f}GB内存"
            )
            
        self.memory_stats['total_allocated'] += size
        self.logger.info(
            f"成功为{purpose}分配{size / 1024 / 1024 / 1024:.2f}GB内存"
        )
        return True

    def release_memory(self, size: int, purpose: str) -> None:
        """
        释放已分配的内存
        
        Args:
            size: 要释放的内存大小（字节）
            purpose: 内存用途描述
        """
        self.memory_stats['total_allocated'] -= size
        self.logger.info(
            f"已释放{purpose}使用的{size / 1024 / 1024 / 1024:.2f}GB内存"
        )

    def get_memory_stats(self) -> Dict[str, int]:
        """
        获取内存使用统计信息
        
        Returns:
            Dict[str, int]: 内存使用统计信息
        """
        self.get_current_memory_usage()  # 更新当前使用量
        return self.memory_stats

    def monitor_memory_usage(self, threshold: float = 0.9) -> Optional[str]:
        """
        监控内存使用情况，当超过阈值时发出警告
        
        Args:
            threshold: 内存使用警告阈值（0-1之间）
            
        Returns:
            Optional[str]: 如果超过阈值，返回警告信息；否则返回None
        """
        virtual_memory = psutil.virtual_memory()
        memory_percent = virtual_memory.percent / 100
        
        if memory_percent > threshold:
            warning_msg = (
                f"内存使用率({memory_percent:.2%})超过警告阈值({threshold:.2%})"
            )
            self.logger.warning(warning_msg)
            return warning_msg
        return None

    def cleanup(self) -> None:
        """清理内存管理器状态"""
        self.memory_stats = {
            'total_allocated': 0,
            'peak_usage': 0,
            'current_usage': 0
        }
        self.logger.info("内存管理器状态已重置")
        
    def monitor_start(self, interval: float = 5.0, threshold: float = 0.9) -> None:
        """
        启动内存监控线程
        
        Args:
            interval: 监控间隔时间（秒）
            threshold: 内存使用警告阈值（0-1之间）
        """
        if self._monitoring:
            self.logger.warning("内存监控线程已在运行")
            return
            
        self._monitoring = True
        self._monitor_interval = interval
        
        def _monitor_task():
            while self._monitoring:
                warning = self.monitor_memory_usage(threshold)
                if warning:
                    # 如果内存使用超过阈值，尝试自动优化
                    self.optimize_memory(aggressive=True)
                time.sleep(self._monitor_interval)
        
        self._monitor_thread = threading.Thread(target=_monitor_task, daemon=True)
        self._monitor_thread.start()
        self.logger.info(f"内存监控线程已启动 (间隔: {interval}秒, 阈值: {threshold:.2%})")
    
    def monitor_stop(self) -> None:
        """停止内存监控线程"""
        if not self._monitoring:
            self.logger.warning("内存监控线程未运行")
            return
            
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=1.0)
            self._monitor_thread = None
        self.logger.info("内存监控线程已停止")
    
    def get_memory_usage(self) -> Dict[str, float]:
        """
        获取当前内存使用情况的详细信息
        
        Returns:
            Dict[str, float]: 包含内存使用信息的字典
        """
        # 获取系统内存信息
        vm = psutil.virtual_memory()
        
        # 获取进程内存信息
        proc_info = self.process.memory_info()
        
        return {
            # 系统内存信息
            'total_mb': vm.total / (1024 * 1024),
            'available_mb': vm.available / (1024 * 1024),
            'used_mb': vm.used / (1024 * 1024),
            'free_mb': vm.free / (1024 * 1024),
            'percent': vm.percent,
            
            # 进程内存信息
            'process_rss_mb': proc_info.rss / (1024 * 1024),  # 物理内存使用
            'process_vms_mb': proc_info.vms / (1024 * 1024),  # 虚拟内存使用
            
            # 内存统计
            'peak_mb': self.memory_stats['peak_usage'] / (1024 * 1024),
            'allocated_mb': self.memory_stats['total_allocated'] / (1024 * 1024),
        }
    
    def optimize_memory(self, aggressive: bool = False) -> Tuple[float, float]:
        """
        优化内存使用，释放未使用的内存
        
        Args:
            aggressive: 是否使用更激进的内存优化
            
        Returns:
            Tuple[float, float]: 优化前和优化后的内存使用量（MB）
        """
        # 获取优化前的内存使用
        before = self.get_current_memory_usage() / (1024 * 1024)
        
        # 执行垃圾回收
        gc.collect()
        
        if aggressive:
            # 更激进的内存优化: 清理各种缓存
            import sys
            
            # 清理已导入但不再使用的模块
            for module_name in list(sys.modules.keys()):
                if module_name not in sys.modules:
                    continue
                if module_name.startswith('_') or module_name in ('sys', 'os', 'gc'):
                    continue
                try:
                    module = sys.modules[module_name]
                    attrs = dir(module)
                    for attr in attrs:
                        if attr.startswith('_'):
                            continue
                        try:
                            delattr(module, attr)
                        except (AttributeError, TypeError):
                            pass
                except (KeyError, AttributeError):
                    pass
            
            # 再次执行垃圾回收
            gc.collect()
        
        # 获取优化后的内存使用
        after = self.get_current_memory_usage() / (1024 * 1024)
        
        saved = before - after
        if saved > 0:
            self.logger.info(f"内存优化完成: 释放了 {saved:.2f} MB 内存")
        else:
            self.logger.info("内存优化完成，但未能释放显著内存")
            
        return before, after 