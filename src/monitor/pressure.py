#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
内存压力模拟器

提供各种内存压力测试工具，用于测试VisionAI-ClipsMaster在各种极端条件下的稳定性。
"""

import os
import sys
import time
import threading
import logging
import random
import numpy as np
from typing import List, Dict, Optional, Any, Callable, Tuple
from contextlib import contextmanager

# 导入平台适配层
from .platform_adapter import get_memory_usage, get_platform_info, get_cpu_usage

# 配置日志
logger = logging.getLogger("pressure_simulator")

class MemoryPressureSimulator:

    # 内存使用警告阈值（百分比）
    memory_warning_threshold = 80
    """内存压力模拟器
    
    模拟各种内存压力场景，如高频分配、内存泄漏、内存峰值等。
    """
    
    def __init__(self, rate: int = 100, duration: int = 10, 
                 pattern: str = "constant", seed: Optional[int] = None):
        """初始化内存压力模拟器
        
        Args:
            rate: 内存分配速率 (MB/s)
            duration: 测试持续时间 (秒)
            pattern: 内存分配模式 ("constant", "spike", "wave", "leak")
            seed: 随机种子
        """
        self.rate = rate
        self.duration = duration
        self.pattern = pattern
        self.seed = seed
        
        # 初始化随机数生成器
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)
        
        # 内存块列表
        self.memory_blocks: List[np.ndarray] = []
        
        # 停止标志
        self._stop_event = threading.Event()
        
        # 监控数据
        self.allocation_history: List[Tuple[float, float]] = []  # (timestamp, allocated_mb)
        
        logger.info(f"初始化内存压力模拟器: 速率={rate}MB/s, 模式={pattern}, 持续时间={duration}秒")
    
    def _allocate_memory(self, size_mb: float) -> np.ndarray:
        """分配指定大小的内存
        
        Args:
            size_mb: 内存大小 (MB)
            
        Returns:
            分配的内存数组
        """
        # 将MB转换为字节
        size_bytes = int(size_mb * 1024 * 1024)
        
        # 分配内存并填充随机数据以确保实际分配
        try:
            mem_block = np.random.bytes(size_bytes)
            return mem_block
        except MemoryError:
            logger.error(f"内存分配失败: 无法分配 {size_mb}MB")
            return np.array([])
    
    def _constant_allocation(self):
        """恒定速率内存分配"""
        start_time = time.time()
        elapsed = 0
        
        # 计算每次分配的内存大小和间隔
        alloc_size = self.rate / 10  # 每次分配的MB数
        interval = 0.1  # 分配间隔(秒)
        
        while elapsed < self.duration and not self._stop_event.is_set():
            # 分配内存
            mem_block = self._allocate_memory(alloc_size)
            if len(mem_block) > 0:
                self.memory_blocks.append(mem_block)
                
                # 记录分配历史
                current_allocated = sum(len(block) for block in self.memory_blocks) / (1024 * 1024)
                self.allocation_history.append((elapsed, current_allocated))
                
                logger.debug(f"已分配 {alloc_size}MB, 总计: {current_allocated:.2f}MB")
            
            # 等待间隔
            time.sleep(interval)
            
            # 更新已过时间
            elapsed = time.time() - start_time
    
    def _spike_allocation(self):
        """内存峰值分配
        
        模拟突发的大内存分配，然后释放部分内存
        """
        start_time = time.time()
        elapsed = 0
        
        # 计算峰值数量和每个峰值的大小
        num_spikes = max(1, self.duration // 2)
        spike_interval = self.duration / num_spikes
        
        for i in range(num_spikes):
            if self._stop_event.is_set():
                break
                
            # 计算峰值大小 (是基础速率的3-5倍)
            spike_size = self.rate * random.uniform(3, 5)
            
            logger.info(f"生成内存峰值: {spike_size:.2f}MB")
            
            # 分配峰值内存
            mem_block = self._allocate_memory(spike_size)
            if len(mem_block) > 0:
                self.memory_blocks.append(mem_block)
                
                # 记录分配历史
                current_allocated = sum(len(block) for block in self.memory_blocks) / (1024 * 1024)
                elapsed = time.time() - start_time
                self.allocation_history.append((elapsed, current_allocated))
                
                logger.debug(f"峰值分配 {spike_size:.2f}MB, 总计: {current_allocated:.2f}MB")
            
            # 保持峰值一小段时间
            time.sleep(0.5)
            
            # 释放部分内存 (释放50-80%)
            release_ratio = random.uniform(0.5, 0.8)
            blocks_to_release = int(len(self.memory_blocks) * release_ratio)
            
            if blocks_to_release > 0:
                for _ in range(blocks_to_release):
                    if self.memory_blocks:
                        self.memory_blocks.pop(0)
                
                # 记录释放后的内存
                current_allocated = sum(len(block) for block in self.memory_blocks) / (1024 * 1024)
                elapsed = time.time() - start_time
                self.allocation_history.append((elapsed, current_allocated))
                
                logger.debug(f"释放内存后, 总计: {current_allocated:.2f}MB")
            
            # 等待下一个峰值
            if i < num_spikes - 1:  # 不是最后一个峰值
                wait_time = max(0, spike_interval - 0.5)
                time.sleep(wait_time)
    
    def _wave_allocation(self):
        """波浪式内存分配
        
        模拟内存使用的周期性波动
        """
        start_time = time.time()
        elapsed = 0
        
        # 波浪参数
        num_waves = max(1, self.duration // 3)
        wave_period = self.duration / num_waves
        samples_per_wave = 20
        sample_interval = wave_period / samples_per_wave
        
        while elapsed < self.duration and not self._stop_event.is_set():
            # 计算当前在波浪中的位置 (0到2π)
            phase = (elapsed % wave_period) / wave_period * 2 * np.pi
            
            # 计算当前分配速率 (使用正弦波，范围在rate的0.1到2倍之间)
            current_rate = self.rate * (0.1 + 0.95 * (1 + np.sin(phase)))
            
            # 计算当前时间间隔内的分配量
            alloc_size = current_rate * sample_interval
            
            logger.debug(f"波浪分配: {alloc_size:.2f}MB, 速率: {current_rate:.2f}MB/s")
            
            # 分配内存
            mem_block = self._allocate_memory(alloc_size)
            if len(mem_block) > 0:
                self.memory_blocks.append(mem_block)
                
                # 记录分配历史
                current_allocated = sum(len(block) for block in self.memory_blocks) / (1024 * 1024)
                self.allocation_history.append((elapsed, current_allocated))
            
            # 释放部分内存以维持波浪形状
            if phase > np.pi and self.memory_blocks:
                # 在波浪下降期释放一些内存
                blocks_to_release = max(1, int(len(self.memory_blocks) * 0.05))
                for _ in range(blocks_to_release):
                    if self.memory_blocks:
                        self.memory_blocks.pop(0)
                
                # 记录释放后的内存
                current_allocated = sum(len(block) for block in self.memory_blocks) / (1024 * 1024)
                self.allocation_history.append((elapsed, current_allocated))
            
            # 等待下一个采样点
            time.sleep(sample_interval)
            
            # 更新已过时间
            elapsed = time.time() - start_time
    
    def _leak_allocation(self):
        """内存泄漏模拟
        
        模拟逐渐增加的内存泄漏
        """
        start_time = time.time()
        elapsed = 0
        
        # 计算基础分配速率和增长率
        base_rate = self.rate * 0.1  # 基础速率是指定速率的10%
        growth_factor = 1.05  # 每次分配增加5%
        
        # 计算初始分配大小和间隔
        current_size = base_rate / 10
        interval = 0.1
        
        while elapsed < self.duration and not self._stop_event.is_set():
            # 分配内存
            mem_block = self._allocate_memory(current_size)
            if len(mem_block) > 0:
                self.memory_blocks.append(mem_block)
                
                # 记录分配历史
                current_allocated = sum(len(block) for block in self.memory_blocks) / (1024 * 1024)
                self.allocation_history.append((elapsed, current_allocated))
                
                logger.debug(f"泄漏分配 {current_size:.2f}MB, 总计: {current_allocated:.2f}MB")
            
            # 增加分配大小 (模拟泄漏增长)
            current_size *= growth_factor
            
            # 等待间隔
            time.sleep(interval)
            
            # 更新已过时间
            elapsed = time.time() - start_time
    
    def _pressure_thread(self):
        """压力测试线程"""
        try:
            if self.pattern == "constant":
                self._constant_allocation()
            elif self.pattern == "spike":
                self._spike_allocation()
            elif self.pattern == "wave":
                self._wave_allocation()
            elif self.pattern == "leak":
                self._leak_allocation()
            else:
                logger.error(f"未知的内存分配模式: {self.pattern}")
        except Exception as e:
            logger.exception(f"压力测试线程异常: {e}")
    
    def start(self):
        """启动压力测试"""
        logger.info(f"启动内存压力测试: {self.pattern} 模式")
        
        # 清除停止标志
        self._stop_event.clear()
        
        # 创建并启动线程
        self.thread = threading.Thread(
            target=self._pressure_thread,
            name=f"memory-pressure-{self.pattern}",
            daemon=True
        )
        self.thread.start()
    
    def stop(self):
        """停止压力测试"""
        logger.info("停止内存压力测试")
        
        # 设置停止标志
        self._stop_event.set()
        
        # 等待线程结束
        if hasattr(self, 'thread') and self.thread.is_alive():
            self.thread.join(timeout=2.0)
    
    def release_memory(self):
        """释放所有分配的内存"""
        logger.info(f"释放所有分配的内存: {len(self.memory_blocks)} 块")
        
        # 清空内存块列表
        self.memory_blocks.clear()
        
        # 强制垃圾回收
        import gc
        gc.collect()
    
    @contextmanager
    def apply_pressure(self):
        """使用上下文管理器应用内存压力
        
        示例:
            with MemoryPressureSimulator(rate=500, pattern="spike").apply_pressure():
                # 在内存压力下执行代码
        """
        try:
            self.start()
            yield self
        finally:
            self.stop()
            self.release_memory()


class MemoryMonitor:
    """内存监控器
    
    监控系统和进程的内存使用情况，检测内存泄漏和异常行为。
    """
    
    def __init__(self, sample_interval: float = 0.1):
        """初始化内存监控器
        
        Args:
            sample_interval: 采样间隔 (秒)
        """
        self.sample_interval = sample_interval
        
        # 监控数据
        self.memory_history: List[Tuple[float, float, float]] = []  # (timestamp, process_mb, system_percent)
        
        # 停止标志
        self._stop_event = threading.Event()
        
        # 记录开始时间
        self.start_time = None
        
        # 记录平台信息
        self.platform_info = get_platform_info()
        
        logger.info(f"初始化内存监控器: 采样间隔={sample_interval}秒, 平台={self.platform_info['system']}")
    
    def __enter__(self):
        """上下文管理器入口"""
        return self.start()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.stop()
        return False  # 不抑制异常
    
    def _monitor_thread(self):
        """内存监控线程"""
        try:
            while not self._stop_event.is_set():
                try:
                    # 获取当前时间
                    current_time = time.time()
                    elapsed = current_time - self.start_time
                    
                    # 使用平台适配层获取内存信息
                    mem_info = get_memory_usage()
                    
                    # 获取进程内存和系统内存百分比
                    process_mem = mem_info['process']  # MB
                    system_percent = mem_info['percent']  # %
                    
                    # 记录数据
                    self.memory_history.append((elapsed, process_mem, system_percent))
                    
                    logger.debug(f"内存监控: 进程={process_mem:.2f}MB, 系统={system_percent:.1f}%")
                    
                except Exception as e:
                    logger.error(f"监控数据采集异常: {e}")
                
                # 等待下一个采样点
                time.sleep(self.sample_interval)
                
        except Exception as e:
            logger.exception(f"内存监控线程异常: {e}")
    
    def start(self):
        """启动内存监控"""
        logger.info("启动内存监控")
        
        # 记录开始时间
        self.start_time = time.time()
        
        # 清除停止标志
        self._stop_event.clear()
        
        # 清除历史数据
        self.memory_history.clear()
        
        # 创建并启动线程
        self.thread = threading.Thread(
            target=self._monitor_thread,
            name="memory-monitor",
            daemon=True
        )
        self.thread.start()
        
        return self
    
    def stop(self):
        """停止内存监控"""
        logger.info("停止内存监控")
        
        # 设置停止标志
        self._stop_event.set()
        
        # 等待线程结束
        if hasattr(self, 'thread') and self.thread.is_alive():
            self.thread.join(timeout=2.0)
    
    def detect_leak(self, threshold_percent: float = 5.0, window_size: int = 10) -> bool:
        """检测内存泄漏
        
        通过分析内存增长趋势检测潜在的内存泄漏。
        
        Args:
            threshold_percent: 增长阈值百分比
            window_size: 使用最近的几个采样点进行分析
            
        Returns:
            如果检测到内存泄漏返回True，否则返回False
        """
        if len(self.memory_history) < window_size + 1:
            logger.warning(f"内存历史记录不足，无法检测泄漏 (至少需要 {window_size + 1} 个采样点)")
            return False
        
        # 获取最近的窗口数据
        recent_data = self.memory_history[-window_size:]
        
        # 计算起始和结束内存
        start_mem = recent_data[0][1]  # 进程内存
        end_mem = recent_data[-1][1]  # 进程内存
        
        # 计算增长百分比
        if start_mem > 0:
            growth_percent = ((end_mem - start_mem) / start_mem) * 100
            logger.debug(f"内存增长: {growth_percent:.2f}% (阈值: {threshold_percent}%)")
            
            # 检查是否超过阈值
            return growth_percent > threshold_percent
        
        return False
    
    def detect_leak_time(self, threshold_percent: float = 5.0) -> float:
        """检测检测到内存泄漏所需的时间
        
        返回从监控开始到首次检测到内存泄漏的时间。
        
        Args:
            threshold_percent: 增长阈值百分比
            
        Returns:
            检测到泄漏的时间（秒），如果未检测到则返回监控总时间
        """
        if len(self.memory_history) < 2:
            return float('inf')
            
        # 初始内存值
        initial_mem = self.memory_history[0][1]
        
        for timestamp, mem, _ in self.memory_history:
            # 计算增长百分比
            if initial_mem > 0:
                growth_percent = ((mem - initial_mem) / initial_mem) * 100
                
                # 检查是否超过阈值
                if growth_percent > threshold_percent:
                    logger.info(f"在 {timestamp:.2f} 秒时检测到内存泄漏 (增长: {growth_percent:.2f}%)")
                    return timestamp
        
        # 如果未检测到泄漏，返回监控总时间
        if self.memory_history:
            return self.memory_history[-1][0]
        else:
            return 0.0
    
    def detect_spikes(self, threshold_percent: float = 20.0) -> List[Tuple[float, float]]:
        """检测内存峰值
        
        检测内存使用的突然增加。
        
        Args:
            threshold_percent: 峰值阈值百分比
            
        Returns:
            内存峰值列表 [(timestamp, spike_percent), ...]
        """
        if len(self.memory_history) < 2:
            return []
            
        spikes = []
        
        for i in range(1, len(self.memory_history)):
            prev_mem = self.memory_history[i-1][1]
            curr_mem = self.memory_history[i][1]
            curr_time = self.memory_history[i][0]
            
            # 计算增长百分比
            if prev_mem > 0:
                spike_percent = ((curr_mem - prev_mem) / prev_mem) * 100
                
                # 检查是否超过阈值
                if spike_percent > threshold_percent:
                    logger.info(f"在 {curr_time:.2f} 秒时检测到内存峰值 (增长: {spike_percent:.2f}%)")
                    spikes.append((curr_time, spike_percent))
        
        return spikes
    
    def get_max_memory(self) -> float:
        """获取最大内存使用
        
        Returns:
            最大进程内存使用 (MB)
        """
        if not self.memory_history:
            return 0.0
            
        return max(mem for _, mem, _ in self.memory_history)
    
    def get_max_system_percent(self) -> float:
        """获取最大系统内存百分比
        
        Returns:
            最大系统内存使用百分比
        """
        if not self.memory_history:
            return 0.0
            
        return max(sys_percent for _, _, sys_percent in self.memory_history)
    
    def get_average_memory(self) -> float:
        """获取平均内存使用
        
        Returns:
            平均进程内存使用 (MB)
        """
        if not self.memory_history:
            return 0.0
            
        total_mem = sum(mem for _, mem, _ in self.memory_history)
        return total_mem / len(self.memory_history)


def start_monitor() -> MemoryMonitor:
    """启动内存监控
    
    Returns:
        内存监控器实例
    """
    monitor = MemoryMonitor()
    return monitor.start()


# 导出主要类和函数
__all__ = ['MemoryPressureSimulator', 'MemoryMonitor', 'start_monitor'] 