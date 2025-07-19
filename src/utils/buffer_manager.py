#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
缓冲区管理器模块

为项目提供统一的缓冲区管理接口，整合内存映射和智能缓冲区功能，
支持流式处理管道的高效数据传输和处理。
"""

import os
import time
import threading
import numpy as np
from typing import Dict, List, Optional, Union, Tuple, Any, BinaryIO
from enum import Enum, auto
from pathlib import Path

from src.utils.smart_buffer import SmartBuffer, BufferStrategy, BufferAccessMode
from src.utils.log_handler import get_logger
from src.exporters.memmap_engine import get_memmap_engine

# 配置日志记录器
logger = get_logger("buffer_manager")


class BufferType(Enum):
    """缓冲区类型枚举"""
    NORMAL = auto()     # 普通缓冲区
    STREAM = auto()     # 流式缓冲区
    PIPELINE = auto()   # 管道缓冲区
    SHARED = auto()     # 共享缓冲区
    TEMPORARY = auto()  # 临时缓冲区


class BufferManager:
    """缓冲区管理器类
    
    为应用程序提供统一的缓冲区管理接口，支持不同类型的缓冲需求，
    并与流式处理管道集成，提供高效的数据传输和处理能力。
    """
    
    def __init__(self, 
                 normal_capacity: int = 512 * 1024 * 1024,  # 512MB
                 stream_capacity: int = 256 * 1024 * 1024,  # 256MB
                 pipeline_capacity: int = 128 * 1024 * 1024,  # 128MB
                 shared_capacity: int = 64 * 1024 * 1024,   # 64MB
                 temp_capacity: int = 32 * 1024 * 1024):    # 32MB
        """初始化缓冲区管理器
        
        Args:
            normal_capacity: 普通缓冲区容量(字节)
            stream_capacity: 流式缓冲区容量(字节)
            pipeline_capacity: 管道缓冲区容量(字节)
            shared_capacity: 共享缓冲区容量(字节)
            temp_capacity: 临时缓冲区容量(字节)
        """
        # 创建不同类型的智能缓冲区
        self.buffers = {
            BufferType.NORMAL: SmartBuffer(
                name="NormalBuffer",
                capacity=normal_capacity,
                strategy=BufferStrategy.LRU
            ),
            BufferType.STREAM: SmartBuffer(
                name="StreamBuffer",
                capacity=stream_capacity,
                strategy=BufferStrategy.FIFO
            ),
            BufferType.PIPELINE: SmartBuffer(
                name="PipelineBuffer",
                capacity=pipeline_capacity,
                strategy=BufferStrategy.ADAPTIVE
            ),
            BufferType.SHARED: SmartBuffer(
                name="SharedBuffer",
                capacity=shared_capacity,
                strategy=BufferStrategy.LFU
            ),
            BufferType.TEMPORARY: SmartBuffer(
                name="TempBuffer",
                capacity=temp_capacity,
                strategy=BufferStrategy.FIFO
            )
        }
        
        # 内存映射引擎
        try:
            self.memmap_engine = get_memmap_engine()
        except Exception as e:
            logger.warning(f"无法初始化内存映射引擎: {e}")
            self.memmap_engine = None
        
        # 缓冲区使用统计
        self.stats = {
            "creation_time": time.time(),
            "allocations": 0,
            "releases": 0,
            "total_ops": 0,
            "peak_memory": 0,
            "current_memory": 0
        }
        
        # 线程锁
        self._lock = threading.RLock()
        
        logger.info("缓冲区管理器初始化完成")
    
    def allocate(self, 
                key: str, 
                shape: Tuple[int, ...], 
                dtype: np.dtype = np.float32, 
                buffer_type: BufferType = BufferType.NORMAL) -> np.ndarray:
        """分配缓冲区
        
        Args:
            key: 缓冲区标识键
            shape: 数组形状
            dtype: 数据类型
            buffer_type: 缓冲区类型
            
        Returns:
            np.ndarray: 分配的数组
        """
        with self._lock:
            # 构建完整键名（包含类型前缀）
            full_key = f"{buffer_type.name.lower()}:{key}"
            
            # 调用相应缓冲区的分配方法
            array = self.buffers[buffer_type].allocate(
                full_key, shape, dtype, BufferAccessMode.READ_WRITE
            )
            
            # 更新统计
            self.stats["allocations"] += 1
            self.stats["total_ops"] += 1
            self._update_memory_stats()
            
            return array
    
    def get(self, 
           key: str, 
           buffer_type: BufferType = BufferType.NORMAL,
           default: Any = None) -> Optional[np.ndarray]:
        """获取缓冲区数据
        
        Args:
            key: 缓冲区标识键
            buffer_type: 缓冲区类型
            default: 未找到时的默认返回值
            
        Returns:
            Optional[np.ndarray]: 缓冲区数据或默认值
        """
        with self._lock:
            full_key = f"{buffer_type.name.lower()}:{key}"
            
            # 先在指定类型的缓冲区中查找
            result = self.buffers[buffer_type].get(full_key)
            
            if result is None:
                # 如果未找到，且不是NORMAL类型，尝试在NORMAL缓冲区中查找
                if buffer_type != BufferType.NORMAL:
                    normal_key = f"normal:{key}"
                    result = self.buffers[BufferType.NORMAL].get(normal_key)
                
                # 如果仍未找到，且不是SHARED类型，尝试在SHARED缓冲区中查找
                if result is None and buffer_type != BufferType.SHARED:
                    shared_key = f"shared:{key}"
                    result = self.buffers[BufferType.SHARED].get(shared_key)
            
            self.stats["total_ops"] += 1
            return result if result is not None else default
    
    def put(self, 
           key: str, 
           data: np.ndarray, 
           buffer_type: BufferType = BufferType.NORMAL) -> None:
        """存入数据到缓冲区
        
        Args:
            key: 缓冲区标识键
            data: 要存储的数据
            buffer_type: 缓冲区类型
        """
        with self._lock:
            full_key = f"{buffer_type.name.lower()}:{key}"
            
            # 存入相应的缓冲区
            self.buffers[buffer_type].put(full_key, data)
            
            # 更新统计
            self.stats["total_ops"] += 1
            self._update_memory_stats()
    
    def release(self, 
               key: str, 
               buffer_type: Optional[BufferType] = None) -> bool:
        """释放缓冲区
        
        Args:
            key: 缓冲区标识键
            buffer_type: 缓冲区类型，如果为None则在所有类型中尝试释放
            
        Returns:
            bool: 是否成功释放
        """
        with self._lock:
            released = False
            
            # 如果指定了类型，仅释放该类型
            if buffer_type is not None:
                full_key = f"{buffer_type.name.lower()}:{key}"
                released = self.buffers[buffer_type].release(full_key)
            else:
                # 否则在所有类型中尝试释放
                for buf_type in BufferType:
                    full_key = f"{buf_type.name.lower()}:{key}"
                    if self.buffers[buf_type].release(full_key):
                        released = True
            
            # 更新统计
            if released:
                self.stats["releases"] += 1
            self.stats["total_ops"] += 1
            self._update_memory_stats()
            
            return released
    
    def map_file(self, 
                path: Union[str, Path], 
                shape: Optional[Tuple[int, ...]] = None,
                dtype: np.dtype = np.float32,
                access_mode: str = 'r') -> np.ndarray:
        """将文件映射为数组
        
        Args:
            path: 文件路径
            shape: 数组形状，如果为None则自动推断
            dtype: 数据类型
            access_mode: 访问模式('r'或'r+')
            
        Returns:
            np.ndarray: 映射的数组
        """
        with self._lock:
            # 使用NORMAL类型的缓冲区进行映射
            result = self.buffers[BufferType.NORMAL].map_file(
                path, shape, dtype, access_mode
            )
            
            self.stats["total_ops"] += 1
            return result
    
    def create_temp_buffer(self, 
                         prefix: str, 
                         shape: Tuple[int, ...], 
                         dtype: np.dtype = np.float32) -> Tuple[str, np.ndarray]:
        """创建临时文件缓冲区
        
        Args:
            prefix: 文件名前缀
            shape: 数组形状
            dtype: 数据类型
            
        Returns:
            Tuple[str, np.ndarray]: 文件路径和映射的数组
        """
        with self._lock:
            # 使用TEMPORARY类型的缓冲区创建临时文件
            result = self.buffers[BufferType.TEMPORARY].create_temp_buffer(
                prefix, shape, dtype
            )
            
            self.stats["total_ops"] += 1
            self._update_memory_stats()
            
            return result
    
    def copy(self, 
            src_key: str, 
            dst_key: str, 
            src_type: BufferType = BufferType.NORMAL,
            dst_type: Optional[BufferType] = None,
            region: Optional[Tuple[slice, ...]] = None) -> bool:
        """在缓冲区间复制数据
        
        Args:
            src_key: 源缓冲区键
            dst_key: 目标缓冲区键
            src_type: 源缓冲区类型
            dst_type: 目标缓冲区类型，如果为None则与源类型相同
            region: 要复制的区域（切片元组）
            
        Returns:
            bool: 是否成功复制
        """
        if dst_type is None:
            dst_type = src_type
        
        with self._lock:
            src_full_key = f"{src_type.name.lower()}:{src_key}"
            dst_full_key = f"{dst_type.name.lower()}:{dst_key}"
            
            # 获取源数据
            src_data = self.buffers[src_type].get(src_full_key)
            if src_data is None:
                return False
            
            # 如果指定了区域，创建视图
            if region is not None:
                src_view = src_data[region]
            else:
                src_view = src_data
            
            # 存入目标缓冲区
            self.buffers[dst_type].put(dst_full_key, src_view)
            
            self.stats["total_ops"] += 1
            self._update_memory_stats()
            
            return True
    
    def view(self, 
            key: str, 
            region: Tuple[slice, ...],
            buffer_type: BufferType = BufferType.NORMAL) -> Optional[np.ndarray]:
        """创建缓冲区数据的视图（零拷贝）
        
        Args:
            key: 缓冲区标识键
            region: 视图区域（切片元组）
            buffer_type: 缓冲区类型
            
        Returns:
            Optional[np.ndarray]: 数据视图或None
        """
        with self._lock:
            full_key = f"{buffer_type.name.lower()}:{key}"
            
            result = self.buffers[buffer_type].view(full_key, region)
            
            self.stats["total_ops"] += 1
            return result
    
    def clear(self, buffer_type: Optional[BufferType] = None) -> None:
        """清空缓冲区
        
        Args:
            buffer_type: 要清空的缓冲区类型，如果为None则清空所有
        """
        with self._lock:
            if buffer_type is not None:
                # 清空指定类型
                self.buffers[buffer_type].clear()
            else:
                # 清空所有类型
                for buf_type in BufferType:
                    self.buffers[buf_type].clear()
            
            self.stats["total_ops"] += 1
            self._update_memory_stats()
            
            logger.info("缓冲区已清空")
    
    def get_buffer_stats(self, buffer_type: Optional[BufferType] = None) -> Dict[str, Any]:
        """获取缓冲区统计信息
        
        Args:
            buffer_type: 要获取统计的缓冲区类型，如果为None则获取所有
            
        Returns:
            Dict[str, Any]: 统计信息
        """
        with self._lock:
            if buffer_type is not None:
                # 获取指定类型的统计
                return self.buffers[buffer_type].get_stats()
            
            # 合并所有类型的统计
            combined_stats = {
                "total_buffer_count": 0,
                "total_current_size": 0,
                "total_peak_size": 0,
                "total_hits": 0,
                "total_misses": 0,
                "total_evictions": 0,
                "buffer_utilization": {}
            }
            
            for buf_type in BufferType:
                buf_stats = self.buffers[buf_type].get_stats()
                
                # 更新组合统计
                combined_stats["total_buffer_count"] += buf_stats["buffer_count"]
                combined_stats["total_current_size"] += buf_stats["current_size"]
                combined_stats["total_peak_size"] += buf_stats["peak_size"]
                combined_stats["total_hits"] += buf_stats["hits"]
                combined_stats["total_misses"] += buf_stats["misses"]
                combined_stats["total_evictions"] += buf_stats["evictions"]
                
                # 每个缓冲区类型的利用率
                combined_stats["buffer_utilization"][buf_type.name] = {
                    "current_size_mb": buf_stats["current_size"] / (1024 * 1024),
                    "capacity_mb": self.buffers[buf_type].capacity / (1024 * 1024),
                    "usage_percent": buf_stats["memory_usage_percent"],
                    "buffer_count": buf_stats["buffer_count"]
                }
            
            # 添加管理器统计
            combined_stats.update(self.stats)
            
            return combined_stats
    
    def _update_memory_stats(self):
        """更新内存使用统计"""
        current_memory = sum(
            self.buffers[buf_type].get_stats()["current_size"]
            for buf_type in BufferType
        )
        
        self.stats["current_memory"] = current_memory
        self.stats["peak_memory"] = max(self.stats["peak_memory"], current_memory)
    
    def get_pipeline_buffer_for_key(self, key: str) -> np.ndarray:
        """获取用于管道处理的缓冲区
        
        为流式处理管道提供专用的缓冲区访问接口
        
        Args:
            key: 缓冲区标识键
            
        Returns:
            np.ndarray: 管道缓冲区数据
        """
        return self.get(key, buffer_type=BufferType.PIPELINE)
    
    def has_buffer(self, key: str, buffer_type: Optional[BufferType] = None) -> bool:
        """检查缓冲区是否存在
        
        Args:
            key: 缓冲区标识键
            buffer_type: 缓冲区类型，如果为None则在所有类型中查找
            
        Returns:
            bool: 是否存在
        """
        if buffer_type is not None:
            # 检查指定类型
            full_key = f"{buffer_type.name.lower()}:{key}"
            return full_key in self.buffers[buffer_type]
        
        # 在所有类型中查找
        for buf_type in BufferType:
            full_key = f"{buf_type.name.lower()}:{key}"
            if full_key in self.buffers[buf_type]:
                return True
        
        return False
    
    def create_stream_buffer(self,
                           key: str,
                           frames: int,
                           height: int,
                           width: int,
                           channels: int = 3,
                           dtype: np.dtype = np.uint8) -> np.ndarray:
        """创建用于视频流的专用缓冲区
        
        Args:
            key: 缓冲区标识键
            frames: 帧数
            height: 高度
            width: 宽度
            channels: 通道数
            dtype: 数据类型
            
        Returns:
            np.ndarray: 分配的视频流缓冲区
        """
        return self.allocate(
            key=key,
            shape=(frames, height, width, channels),
            dtype=dtype,
            buffer_type=BufferType.STREAM
        )


# 全局缓冲区管理器实例
_global_buffer_manager = None


def get_buffer_manager() -> BufferManager:
    """获取全局缓冲区管理器实例
    
    Returns:
        BufferManager: 全局缓冲区管理器实例
    """
    global _global_buffer_manager
    if _global_buffer_manager is None:
        _global_buffer_manager = BufferManager()
    return _global_buffer_manager 