#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
智能缓冲区管理模块

提供高效的内存数据管理机制，支持零拷贝操作和智能缓存策略，
专为视频处理和大规模数据流操作优化。集成了内存映射功能，
减少内存占用并提高数据处理效率。
"""

import os
import mmap
import time
import numpy as np
import threading
import logging
from typing import Dict, List, Optional, Union, Tuple, Any, BinaryIO
from enum import Enum, auto
from pathlib import Path

from src.utils.log_handler import get_logger
from src.exporters.memmap_engine import get_memmap_engine

# 配置日志记录器
logger = get_logger("smart_buffer")

# 缓冲区访问模式
class BufferAccessMode(Enum):
    """缓冲区访问模式枚举"""
    READ_ONLY = auto()   # 只读模式
    READ_WRITE = auto()  # 读写模式
    WRITE_ONLY = auto()  # 只写模式


class BufferStrategy(Enum):
    """缓冲区管理策略枚举"""
    FIFO = auto()        # 先进先出
    LRU = auto()         # 最近最少使用
    LFU = auto()         # 最不经常使用
    ADAPTIVE = auto()    # 自适应策略


class SmartBuffer:
    """智能缓冲区类
    
    提供高效的内存数据管理，支持内存映射、零拷贝传输和智能缓存策略。
    特别适用于视频处理中的大量数据流操作。
    """
    
    def __init__(self, 
                 name: str = None,
                 capacity: int = 256 * 1024 * 1024,  # 默认256MB
                 strategy: BufferStrategy = BufferStrategy.LRU,
                 enable_mmap: bool = True,
                 page_size: int = 4096):
        """初始化智能缓冲区
        
        Args:
            name: 缓冲区名称
            capacity: 最大容量(字节)
            strategy: 缓冲区管理策略
            enable_mmap: 是否启用内存映射
            page_size: 内存页大小(字节)
        """
        self.name = name or f"SmartBuffer-{id(self)}"
        self.capacity = capacity
        self.strategy = strategy
        self.enable_mmap = enable_mmap
        self.page_size = page_size
        
        # 初始化内部状态
        self._buffer: Dict[str, np.ndarray] = {}  # 数据缓冲区
        self._buffer_info: Dict[str, Dict[str, Any]] = {}  # 缓冲区元信息
        self._mapped_files: Dict[str, mmap.mmap] = {}  # 内存映射文件
        self._lock = threading.RLock()  # 线程锁
        self._temp_dir = os.environ.get("TEMP_BUFFER_DIR", os.path.join(os.getcwd(), "temp_buffers"))
        
        # 确保临时目录存在
        if not os.path.exists(self._temp_dir):
            os.makedirs(self._temp_dir, exist_ok=True)
        
        # 性能统计
        self.stats = {
            "hits": 0,              # 缓存命中次数
            "misses": 0,            # 缓存未命中次数
            "evictions": 0,         # 缓存驱逐次数
            "allocations": 0,       # 内存分配次数
            "current_size": 0,      # 当前使用大小
            "peak_size": 0,         # 峰值使用大小
            "total_operations": 0,  # 总操作次数
            "mem_mapped_size": 0,   # 内存映射大小
        }
        
        # 尝试获取内存映射引擎
        if self.enable_mmap:
            try:
                self.memmap_engine = get_memmap_engine()
            except Exception as e:
                logger.warning(f"无法初始化内存映射引擎: {e}")
                self.enable_mmap = False
        
        logger.info(f"智能缓冲区 '{self.name}' 初始化完成(容量: {self.capacity/1024/1024:.2f}MB, 策略: {self.strategy.name})")
    
    def allocate(self, 
                key: str, 
                shape: Tuple[int, ...], 
                dtype: np.dtype = np.float32, 
                mode: BufferAccessMode = BufferAccessMode.READ_WRITE) -> np.ndarray:
        """分配缓冲区
        
        Args:
            key: 缓冲区标识键
            shape: 数组形状
            dtype: 数据类型
            mode: 访问模式
            
        Returns:
            np.ndarray: 分配的数组
        """
        with self._lock:
            # 计算所需大小
            item_size = np.dtype(dtype).itemsize
            size = int(np.prod(shape)) * item_size
            
            # 检查是否已存在
            if key in self._buffer:
                buf_info = self._buffer_info[key]
                # 更新访问信息
                buf_info["last_access"] = time.time()
                buf_info["access_count"] += 1
                self.stats["hits"] += 1
                return self._buffer[key]
            
            self.stats["misses"] += 1
            
            # 检查容量，可能需要驱逐
            if self.stats["current_size"] + size > self.capacity:
                self._evict(size)
            
            # 分配新缓冲区
            array = np.zeros(shape, dtype=dtype)
            
            # 更新状态
            self._buffer[key] = array
            self._buffer_info[key] = {
                "size": size,
                "shape": shape,
                "dtype": dtype,
                "mode": mode,
                "creation_time": time.time(),
                "last_access": time.time(),
                "access_count": 1,
                "is_dirty": False
            }
            
            self.stats["allocations"] += 1
            self.stats["current_size"] += size
            self.stats["peak_size"] = max(self.stats["peak_size"], self.stats["current_size"])
            self.stats["total_operations"] += 1
            
            logger.debug(f"已分配缓冲区 '{key}' (大小: {size/1024/1024:.2f}MB, 形状: {shape})")
            return array
    
    def get(self, key: str, default: Any = None) -> Optional[np.ndarray]:
        """获取缓冲区数据
        
        Args:
            key: 缓冲区标识键
            default: 未找到时的默认返回值
            
        Returns:
            Optional[np.ndarray]: 缓冲区数据或默认值
        """
        with self._lock:
            if key not in self._buffer:
                return default
            
            # 更新访问统计
            self._buffer_info[key]["last_access"] = time.time()
            self._buffer_info[key]["access_count"] += 1
            self.stats["hits"] += 1
            self.stats["total_operations"] += 1
            
            return self._buffer[key]
    
    def put(self, key: str, data: np.ndarray, mode: BufferAccessMode = BufferAccessMode.READ_WRITE) -> None:
        """存入数据到缓冲区
        
        Args:
            key: 缓冲区标识键
            data: 要存储的数据
            mode: 访问模式
        """
        with self._lock:
            # 计算数据大小
            size = data.nbytes
            
            # 检查是否需要驱逐
            if key not in self._buffer and self.stats["current_size"] + size > self.capacity:
                self._evict(size)
            
            # 更新缓冲区
            if key in self._buffer:
                old_size = self._buffer_info[key]["size"]
                # 形状变化，需要重新分配
                if self._buffer[key].shape != data.shape or self._buffer[key].dtype != data.dtype:
                    self.stats["current_size"] -= old_size
                    self.stats["current_size"] += size
                    self._buffer[key] = data.copy()
                else:
                    # 原地更新
                    np.copyto(self._buffer[key], data)
                self._buffer_info[key]["last_access"] = time.time()
                self._buffer_info[key]["access_count"] += 1
                self._buffer_info[key]["is_dirty"] = True
            else:
                # 新增数据
                self._buffer[key] = data.copy()
                self._buffer_info[key] = {
                    "size": size,
                    "shape": data.shape,
                    "dtype": data.dtype,
                    "mode": mode,
                    "creation_time": time.time(),
                    "last_access": time.time(),
                    "access_count": 1,
                    "is_dirty": True
                }
                self.stats["current_size"] += size
            
            self.stats["peak_size"] = max(self.stats["peak_size"], self.stats["current_size"])
            self.stats["total_operations"] += 1
    
    def release(self, key: str) -> bool:
        """释放缓冲区
        
        Args:
            key: 缓冲区标识键
            
        Returns:
            bool: 是否成功释放
        """
        with self._lock:
            if key not in self._buffer:
                return False
            
            # 更新统计
            size = self._buffer_info[key]["size"]
            self.stats["current_size"] -= size
            
            # 移除缓冲区
            del self._buffer[key]
            del self._buffer_info[key]
            
            self.stats["total_operations"] += 1
            logger.debug(f"已释放缓冲区 '{key}' (大小: {size/1024/1024:.2f}MB)")
            return True
    
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
        if not self.enable_mmap:
            raise ValueError("内存映射功能未启用")
        
        path_str = str(path)
        
        with self._lock:
            # 尝试使用内存映射引擎
            if hasattr(self, 'memmap_engine'):
                if access_mode == 'r':
                    # 只读模式使用视频映射优化
                    if path_str.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
                        return self.memmap_engine.map_video_frames(path_str)
                    # 普通二进制文件映射
                    mapped_obj = self.memmap_engine.mmap_binary_file(path_str, mode=access_mode)
                else:
                    # 读写模式
                    mapped_obj = self.memmap_engine.mmap_binary_file(path_str, mode=access_mode)
                
                # 更新统计
                self.stats["mem_mapped_size"] += os.path.getsize(path_str)
                self.stats["total_operations"] += 1
                
                # 如果是np.memmap对象则直接返回
                if isinstance(mapped_obj, np.ndarray):
                    if shape is not None:
                        return mapped_obj.reshape(shape)
                    return mapped_obj
                
                # 否则创建numpy数组视图
                array = np.frombuffer(mapped_obj, dtype=dtype)
                if shape is not None:
                    array = array.reshape(shape)
                
                return array
            
            # 手动创建内存映射
            file_size = os.path.getsize(path_str)
            
            # 确定访问标志
            if access_mode == 'r':
                flags = mmap.ACCESS_READ
                mode = 'rb'
            else:
                flags = mmap.ACCESS_WRITE
                mode = 'r+b'
            
            # 打开文件并创建映射
            fd = open(path_str, mode)
            mapped_mem = mmap.mmap(fd.fileno(), length=0, access=flags)
            
            # 保存到映射缓存
            self._mapped_files[path_str] = mapped_mem
            
            # 创建numpy数组视图
            array = np.frombuffer(mapped_mem, dtype=dtype)
            if shape is not None:
                array = array.reshape(shape)
            
            # 更新统计
            self.stats["mem_mapped_size"] += file_size
            self.stats["total_operations"] += 1
            
            logger.debug(f"已创建文件映射 '{path_str}' (大小: {file_size/1024/1024:.2f}MB, 模式: {access_mode})")
            return array
    
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
        if not self.enable_mmap:
            raise ValueError("内存映射功能未启用")
        
        # 创建唯一临时文件名
        filename = f"{prefix}_{int(time.time())}_{os.getpid()}.buffer"
        filepath = os.path.join(self._temp_dir, filename)
        
        # 计算文件大小
        item_size = np.dtype(dtype).itemsize
        size = int(np.prod(shape)) * item_size
        
        with self._lock:
            # 创建并初始化文件
            with open(filepath, 'wb') as f:
                f.seek(size - 1)
                f.write(b'\0')
            
            # 映射为数组
            array = self.map_file(filepath, shape, dtype, access_mode='r+')
            
            logger.debug(f"已创建临时缓冲区 '{filepath}' (大小: {size/1024/1024:.2f}MB)")
            return filepath, array
    
    def unmap_file(self, path: Union[str, Path]) -> bool:
        """解除文件映射
        
        Args:
            path: 文件路径
            
        Returns:
            bool: 是否成功解除映射
        """
        path_str = str(path)
        
        with self._lock:
            # 尝试使用内存映射引擎
            if hasattr(self, 'memmap_engine'):
                try:
                    return self.memmap_engine.unmap(path_str)
                except Exception:
                    pass
            
            # 手动解除映射
            if path_str in self._mapped_files:
                self._mapped_files[path_str].close()
                del self._mapped_files[path_str]
                logger.debug(f"已解除文件映射 '{path_str}'")
                return True
            
            return False
    
    def copy(self, 
            src_key: str, 
            dst_key: str, 
            region: Optional[Tuple[slice, ...]] = None) -> bool:
        """在缓冲区间复制数据
        
        支持零拷贝操作，通过视图实现而不是数据复制
        
        Args:
            src_key: 源缓冲区键
            dst_key: 目标缓冲区键
            region: 要复制的区域（切片元组）
            
        Returns:
            bool: 是否成功复制
        """
        with self._lock:
            if src_key not in self._buffer:
                return False
            
            src_data = self._buffer[src_key]
            
            # 如果指定了区域，创建视图
            if region is not None:
                src_view = src_data[region]
            else:
                src_view = src_data
            
            # 目标缓冲区已存在
            if dst_key in self._buffer:
                dst_data = self._buffer[dst_key]
                # 检查形状兼容性
                if dst_data.shape == src_view.shape:
                    np.copyto(dst_data, src_view)
                    self._buffer_info[dst_key]["is_dirty"] = True
                    self._buffer_info[dst_key]["last_access"] = time.time()
                    self._buffer_info[dst_key]["access_count"] += 1
                else:
                    # 形状不兼容，重新分配
                    self.release(dst_key)
                    self.put(dst_key, src_view)
            else:
                # 创建新的目标缓冲区
                self.put(dst_key, src_view)
            
            self.stats["total_operations"] += 1
            return True
    
    def view(self, key: str, region: Tuple[slice, ...]) -> Optional[np.ndarray]:
        """创建缓冲区数据的视图（零拷贝）
        
        Args:
            key: 缓冲区标识键
            region: 视图区域（切片元组）
            
        Returns:
            Optional[np.ndarray]: 数据视图或None
        """
        with self._lock:
            if key not in self._buffer:
                return None
            
            # 更新访问统计
            self._buffer_info[key]["last_access"] = time.time()
            self._buffer_info[key]["access_count"] += 1
            self.stats["hits"] += 1
            self.stats["total_operations"] += 1
            
            # 返回视图
            return self._buffer[key][region]
    
    def clear(self) -> None:
        """清空所有缓冲区"""
        with self._lock:
            # 释放内存映射
            for path, mapped_obj in list(self._mapped_files.items()):
                mapped_obj.close()
            
            # 清空字典
            self._mapped_files.clear()
            self._buffer.clear()
            self._buffer_info.clear()
            
            # 重置统计
            self.stats["current_size"] = 0
            self.stats["mem_mapped_size"] = 0
            self.stats["total_operations"] += 1
            
            logger.info(f"已清空缓冲区 '{self.name}'")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取性能统计
        
        Returns:
            Dict[str, Any]: 性能统计信息
        """
        with self._lock:
            return {
                **self.stats,
                "buffer_count": len(self._buffer),
                "mapped_file_count": len(self._mapped_files),
                "memory_usage_percent": (self.stats["current_size"] / self.capacity) * 100 if self.capacity > 0 else 0,
                "hit_ratio": (self.stats["hits"] / (self.stats["hits"] + self.stats["misses"])) * 100 
                           if (self.stats["hits"] + self.stats["misses"]) > 0 else 0
            }
    
    def _evict(self, required_size: int) -> int:
        """根据策略驱逐缓冲区
        
        Args:
            required_size: 需要的空间大小
            
        Returns:
            int: 释放的空间大小
        """
        if not self._buffer:
            return 0
        
        freed_size = 0
        keys_to_evict = []
        
        # 按策略排序缓冲区
        if self.strategy == BufferStrategy.FIFO:
            # 先进先出：按创建时间排序
            sorted_keys = sorted(
                self._buffer_info.keys(),
                key=lambda k: self._buffer_info[k]["creation_time"]
            )
        elif self.strategy == BufferStrategy.LRU:
            # 最近最少使用：按最后访问时间排序
            sorted_keys = sorted(
                self._buffer_info.keys(),
                key=lambda k: self._buffer_info[k]["last_access"]
            )
        elif self.strategy == BufferStrategy.LFU:
            # 最不经常使用：按访问次数排序
            sorted_keys = sorted(
                self._buffer_info.keys(),
                key=lambda k: self._buffer_info[k]["access_count"]
            )
        else:  # 自适应策略
            # 组合多种因素：访问时间、频率、大小
            sorted_keys = sorted(
                self._buffer_info.keys(),
                key=lambda k: (
                    self._buffer_info[k]["last_access"],  # 先按时间
                    self._buffer_info[k]["access_count"],  # 再按频率
                    -self._buffer_info[k]["size"]  # 最后按大小（优先删除大的）
                )
            )
        
        # 按顺序驱逐，直到释放足够空间
        for key in sorted_keys:
            if freed_size >= required_size:
                break
                
            size = self._buffer_info[key]["size"]
            keys_to_evict.append(key)
            freed_size += size
        
        # 执行驱逐
        for key in keys_to_evict:
            logger.debug(f"驱逐缓冲区: '{key}' (大小: {self._buffer_info[key]['size']/1024/1024:.2f}MB)")
            del self._buffer[key]
            del self._buffer_info[key]
        
        # 更新统计
        self.stats["current_size"] -= freed_size
        self.stats["evictions"] += len(keys_to_evict)
        
        return freed_size
    
    def __contains__(self, key: str) -> bool:
        """检查键是否存在
        
        Args:
            key: 缓冲区标识键
            
        Returns:
            bool: 是否存在
        """
        return key in self._buffer
    
    def __getitem__(self, key: str) -> np.ndarray:
        """获取缓冲区数据
        
        Args:
            key: 缓冲区标识键
            
        Returns:
            np.ndarray: 缓冲区数据
            
        Raises:
            KeyError: 键不存在时抛出
        """
        result = self.get(key)
        if result is None:
            raise KeyError(f"缓冲区键 '{key}' 不存在")
        return result
    
    def __setitem__(self, key: str, value: np.ndarray) -> None:
        """设置缓冲区数据
        
        Args:
            key: 缓冲区标识键
            value: 要存储的数据
        """
        self.put(key, value)
    
    def __delitem__(self, key: str) -> None:
        """删除缓冲区
        
        Args:
            key: 缓冲区标识键
            
        Raises:
            KeyError: 键不存在时抛出
        """
        if not self.release(key):
            raise KeyError(f"缓冲区键 '{key}' 不存在")
    
    def __len__(self) -> int:
        """获取缓冲区数量
        
        Returns:
            int: 缓冲区数量
        """
        return len(self._buffer)
    
    def __iter__(self):
        """迭代缓冲区键
        
        Returns:
            Iterator: 键迭代器
        """
        return iter(self._buffer.keys())
    
    def __del__(self):
        """析构函数：释放资源"""
        try:
            self.clear()
        except Exception:
            pass


# 全局智能缓冲区实例
_global_buffer = None


def get_smart_buffer(capacity: int = 512 * 1024 * 1024) -> SmartBuffer:
    """获取全局智能缓冲区实例
    
    Args:
        capacity: 缓冲区容量（默认512MB）
        
    Returns:
        SmartBuffer: 全局智能缓冲区实例
    """
    global _global_buffer
    if _global_buffer is None:
        _global_buffer = SmartBuffer(
            name="GlobalBuffer",
            capacity=capacity,
            strategy=BufferStrategy.ADAPTIVE
        )
    return _global_buffer 