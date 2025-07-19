#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
透明压缩内存分配器

提供透明的内存压缩分配功能，在内存紧张情况下通过压缩技术优化内存使用
"""

import os
import sys
import time
import logging
import threading
import mmap
import gc
import weakref
from typing import Dict, Any, List, Optional, Tuple, Union, Set
import ctypes
from enum import Enum
import numpy as np

from src.compression.core import Compressor, compress, decompress
from src.utils.log_handler import get_logger

# 配置日志
logger = get_logger("CompressedAllocator")

# 内存块状态
class BlockState(Enum):
    """内存块状态枚举"""
    FREE = 0          # 空闲
    COMPRESSED = 1    # 已压缩
    UNCOMPRESSED = 2  # 已解压
    LOCKED = 3        # 锁定中(正在压缩/解压)

# 内存块元数据
class MemoryBlockMeta:

    # 内存使用警告阈值（百分比）
    memory_warning_threshold = 80
    """内存块元数据"""
    
    def __init__(self, 
                 original_size: int, 
                 compressed_size: Optional[int] = None,
                 ptr: Optional[int] = None,
                 compressed_ptr: Optional[int] = None):
        """
        初始化内存块元数据
        
        Args:
            original_size: 原始大小
            compressed_size: 压缩后大小
            ptr: 解压后内存指针
            compressed_ptr: 压缩内存指针
        """
        self.original_size = original_size
        self.compressed_size = compressed_size
        self.ptr = ptr
        self.compressed_ptr = compressed_ptr
        self.state = BlockState.FREE
        self.last_access_time = time.time()
        self.access_count = 0
        self.compression_ratio = 1.0
        self.lock = threading.RLock()
        
    def __str__(self) -> str:
        """字符串表示"""
        state_str = self.state.name
        ratio_str = f"{self.compression_ratio:.2f}" if self.compression_ratio else "N/A"
        comp_size_str = f"{self.compressed_size/1024:.1f}KB" if self.compressed_size else "N/A"
        
        return (f"MemBlock[{id(self):#x}]: "
                f"State={state_str}, "
                f"Size={self.original_size/1024:.1f}KB, "
                f"CompSize={comp_size_str}, "
                f"Ratio={ratio_str}")
    
    def update_stats(self, is_access: bool = False):
        """更新统计信息"""
        self.last_access_time = time.time()
        if is_access:
            self.access_count += 1

# 主分配器类
class CompressedAllocator:
    """透明压缩内存分配器
    
    通过在内存分配和访问之间自动进行压缩/解压操作来优化内存使用。
    对用户代码透明，但会增加一定的CPU开销。
    """
    
    def __init__(self, 
                 compression_algo: str = 'zstd',
                 compression_level: int = 3,
                 compression_threshold: int = 1024 * 1024,  # 1MB以上才压缩
                 auto_compress_after: int = 5,  # 5秒后自动压缩
                 compression_ratio_threshold: float = 0.7):  # 压缩率低于0.7才保存
        """
        初始化压缩内存分配器
        
        Args:
            compression_algo: 压缩算法
            compression_level: 压缩级别
            compression_threshold: 压缩阈值(字节)
            auto_compress_after: 多少秒不访问后自动压缩
            compression_ratio_threshold: 压缩率阈值
        """
        self.compression_algo = compression_algo
        self.compression_level = compression_level
        self.compression_threshold = compression_threshold
        self.auto_compress_after = auto_compress_after
        self.compression_ratio_threshold = compression_ratio_threshold
        
        # 创建压缩器
        self.compressor = Compressor(
            algo=compression_algo,
            level=compression_level,
            threads=4
        )
        
        # 内存块映射表 {地址: 元数据}
        self.memory_blocks: Dict[int, MemoryBlockMeta] = {}
        
        # 虚拟地址到物理地址的映射
        self.address_map: Dict[int, int] = {}
        
        # 全局锁，用于同步内存块表访问
        self.global_lock = threading.RLock()
        
        # 压缩统计信息
        self.stats = {
            'total_allocations': 0,
            'total_original_bytes': 0,
            'total_compressed_bytes': 0,
            'compression_operations': 0,
            'decompression_operations': 0,
            'memory_saved': 0,
            'total_allocation_time': 0,
            'total_access_time': 0
        }
        
        # 启动后台自动压缩线程
        self.compress_thread_active = True
        self.compress_thread = threading.Thread(
            target=self._auto_compress_thread,
            daemon=True
        )
        self.compress_thread.start()
        
        logger.info(f"透明压缩内存分配器初始化完成，算法: {compression_algo}, 级别: {compression_level}")
    
    def __del__(self):
        """析构函数，停止后台线程"""
        self.compress_thread_active = False
        if hasattr(self, 'compress_thread') and self.compress_thread.is_alive():
            self.compress_thread.join(timeout=1.0)
        
        # 释放所有内存
        self.release_all()
    
    def malloc(self, size: int) -> int:
        """
        分配内存块
        
        Args:
            size: 要分配的字节数
            
        Returns:
            int: 内存指针(地址)
        """
        start_time = time.time()
        
        # 申请原始内存
        raw = self._allocate_raw(size)
        
        # 创建元数据
        meta = MemoryBlockMeta(original_size=size, ptr=raw)
        
        # 如果大小超过阈值，则立即压缩
        if size >= self.compression_threshold:
            try:
                # 读取原始内存内容
                data = self._read_memory(raw, size)
                
                # 压缩数据
                compressed = self.compressor.compress(data)
                compressed_size = len(compressed)
                
                # 计算压缩率
                compression_ratio = compressed_size / size
                
                # 如果压缩效果好，则使用压缩版本
                if compression_ratio <= self.compression_ratio_threshold:
                    # 释放原始内存
                    self._free_raw(raw)
                    
                    # 分配压缩内存
                    compressed_ptr = self._allocate_raw(compressed_size)
                    
                    # 写入压缩数据
                    self._write_memory(compressed_ptr, compressed)
                    
                    # 更新元数据
                    meta.compressed_ptr = compressed_ptr
                    meta.compressed_size = compressed_size
                    meta.compression_ratio = compression_ratio
                    meta.state = BlockState.COMPRESSED
                    meta.ptr = None  # 原始指针已释放
                else:
                    # 压缩效果不好，保留原始数据
                    meta.state = BlockState.UNCOMPRESSED
                
                self.stats['compression_operations'] += 1
                
            except Exception as e:
                logger.warning(f"内存压缩失败: {e}")
                # 失败时保持原始内存
                meta.state = BlockState.UNCOMPRESSED
        else:
            # 小内存块不压缩
            meta.state = BlockState.UNCOMPRESSED
        
        # 为该块分配一个虚拟地址(简单实现，使用id作为虚拟地址)
        virtual_address = id(meta)
        
        # 注册到内存块表
        with self.global_lock:
            self.memory_blocks[virtual_address] = meta
            
            # 更新地址映射
            if meta.state == BlockState.COMPRESSED:
                self.address_map[virtual_address] = meta.compressed_ptr
            else:
                self.address_map[virtual_address] = meta.ptr
            
            # 更新统计信息
            self.stats['total_allocations'] += 1
            self.stats['total_original_bytes'] += size
            if meta.compressed_size:
                self.stats['total_compressed_bytes'] += meta.compressed_size
                self.stats['memory_saved'] += (size - meta.compressed_size)
        
        # 计算分配耗时
        self.stats['total_allocation_time'] += (time.time() - start_time)
        
        return virtual_address
    
    def access(self, ptr: int) -> bytearray:
        """
        访问内存块内容
        
        Args:
            ptr: 内存指针(虚拟地址)
            
        Returns:
            bytearray: 内存内容
        """
        start_time = time.time()
        
        # 查找内存块
        with self.global_lock:
            if ptr not in self.memory_blocks:
                raise ValueError(f"无效的内存指针: {ptr:#x}")
            
            meta = self.memory_blocks[ptr]
        
        # 使用元数据的锁确保线程安全
        with meta.lock:
            # 如果已压缩，则解压
            if meta.state == BlockState.COMPRESSED:
                try:
                    # 标记为正在处理
                    meta.state = BlockState.LOCKED
                    
                    # 读取压缩数据
                    compressed_data = self._read_memory(meta.compressed_ptr, meta.compressed_size)
                    
                    # 解压数据
                    data = self.compressor.decompress(compressed_data)
                    
                    # 分配新的原始内存
                    raw_ptr = self._allocate_raw(meta.original_size)
                    
                    # 写入解压后的数据
                    self._write_memory(raw_ptr, data)
                    
                    # 更新元数据
                    meta.ptr = raw_ptr
                    meta.state = BlockState.UNCOMPRESSED
                    
                    # 更新地址映射
                    with self.global_lock:
                        self.address_map[ptr] = raw_ptr
                    
                    # 更新统计信息
                    self.stats['decompression_operations'] += 1
                    
                except Exception as e:
                    logger.error(f"内存解压失败: {e}")
                    # 失败时恢复状态
                    meta.state = BlockState.COMPRESSED
                    raise RuntimeError(f"内存解压失败: {e}")
            
            # 直接读取原始内存
            data = self._read_memory(meta.ptr, meta.original_size)
            
            # 更新访问统计
            meta.update_stats(is_access=True)
        
        # 计算访问耗时
        self.stats['total_access_time'] += (time.time() - start_time)
        
        return data
    
    def free(self, ptr: int) -> bool:
        """
        释放内存块
        
        Args:
            ptr: 内存指针(虚拟地址)
            
        Returns:
            bool: 是否成功
        """
        # 查找内存块
        with self.global_lock:
            if ptr not in self.memory_blocks:
                logger.warning(f"尝试释放无效的内存指针: {ptr:#x}")
                return False
            
            meta = self.memory_blocks[ptr]
            
            # 从映射表中移除
            self.memory_blocks.pop(ptr)
            self.address_map.pop(ptr, None)
        
        # 使用元数据的锁确保线程安全
        with meta.lock:
            # 释放内存
            if meta.state == BlockState.UNCOMPRESSED and meta.ptr:
                self._free_raw(meta.ptr)
            
            if meta.compressed_ptr:
                self._free_raw(meta.compressed_ptr)
            
            # 标记为已释放
            meta.state = BlockState.FREE
            meta.ptr = None
            meta.compressed_ptr = None
        
        return True
    
    def release_all(self):
        """释放所有内存块"""
        with self.global_lock:
            # 复制键列表，避免在迭代过程中修改字典
            ptrs = list(self.memory_blocks.keys())
        
        # 逐个释放
        for ptr in ptrs:
            self.free(ptr)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self.global_lock:
            # 复制统计信息
            stats = dict(self.stats)
            
            # 添加当前状态
            stats['active_blocks'] = len(self.memory_blocks)
            stats['compressed_blocks'] = sum(
                1 for meta in self.memory_blocks.values() 
                if meta.state == BlockState.COMPRESSED
            )
            stats['uncompressed_blocks'] = sum(
                1 for meta in self.memory_blocks.values() 
                if meta.state == BlockState.UNCOMPRESSED
            )
            
            # 计算总内存节省
            if stats['total_original_bytes'] > 0:
                stats['overall_compression_ratio'] = (
                    stats['total_compressed_bytes'] / stats['total_original_bytes']
                    if stats['total_compressed_bytes'] > 0 else 1.0
                )
                stats['memory_saving_percent'] = (
                    (1 - stats['overall_compression_ratio']) * 100
                )
            else:
                stats['overall_compression_ratio'] = 1.0
                stats['memory_saving_percent'] = 0.0
            
            # 计算平均操作时间
            if stats['total_allocations'] > 0:
                stats['avg_allocation_time_ms'] = (
                    stats['total_allocation_time'] / stats['total_allocations'] * 1000
                )
            else:
                stats['avg_allocation_time_ms'] = 0.0
                
            if stats['decompression_operations'] > 0:
                stats['avg_access_time_ms'] = (
                    stats['total_access_time'] / stats['decompression_operations'] * 1000
                )
            else:
                stats['avg_access_time_ms'] = 0.0
        
        return stats
    
    def compress_unused_blocks(self, idle_seconds: Optional[float] = None) -> int:
        """
        压缩闲置内存块
        
        Args:
            idle_seconds: 多少秒不使用视为闲置(None=使用默认值)
            
        Returns:
            int: 压缩的块数
        """
        if idle_seconds is None:
            idle_seconds = self.auto_compress_after
        
        current_time = time.time()
        compressed_count = 0
        
        # 查找所有未压缩且闲置的块
        candidates = []
        with self.global_lock:
            for ptr, meta in list(self.memory_blocks.items()):
                if (meta.state == BlockState.UNCOMPRESSED and 
                    current_time - meta.last_access_time >= idle_seconds and
                    meta.original_size >= self.compression_threshold):
                    candidates.append((ptr, meta))
        
        # 压缩每个候选块
        for ptr, meta in candidates:
            # 使用元数据的锁确保线程安全
            if not meta.lock.acquire(blocking=False):
                continue  # 跳过已锁定的块
            
            try:
                # 再次检查状态(可能在获取锁的过程中已改变)
                if meta.state != BlockState.UNCOMPRESSED or not meta.ptr:
                    continue
                
                # 标记为正在处理
                meta.state = BlockState.LOCKED
                
                # 读取原始数据
                data = self._read_memory(meta.ptr, meta.original_size)
                
                # 压缩数据
                compressed = self.compressor.compress(data)
                compressed_size = len(compressed)
                
                # 计算压缩率
                compression_ratio = compressed_size / meta.original_size
                
                # 如果压缩效果好，则使用压缩版本
                if compression_ratio <= self.compression_ratio_threshold:
                    # 分配压缩内存
                    compressed_ptr = self._allocate_raw(compressed_size)
                    
                    # 写入压缩数据
                    self._write_memory(compressed_ptr, compressed)
                    
                    # 释放原始内存
                    self._free_raw(meta.ptr)
                    
                    # 更新元数据
                    meta.compressed_ptr = compressed_ptr
                    meta.compressed_size = compressed_size
                    meta.compression_ratio = compression_ratio
                    meta.state = BlockState.COMPRESSED
                    meta.ptr = None  # 原始指针已释放
                    
                    # 更新地址映射
                    with self.global_lock:
                        self.address_map[ptr] = compressed_ptr
                    
                    # 更新统计信息
                    with self.global_lock:
                        self.stats['compression_operations'] += 1
                        self.stats['memory_saved'] += (meta.original_size - compressed_size)
                        self.stats['total_compressed_bytes'] += compressed_size
                    
                    compressed_count += 1
                else:
                    # 压缩效果不好，恢复状态
                    meta.state = BlockState.UNCOMPRESSED
            
            except Exception as e:
                logger.error(f"自动压缩失败: {e}")
                # 恢复原始状态
                meta.state = BlockState.UNCOMPRESSED
            
            finally:
                # 释放锁
                meta.lock.release()
        
        return compressed_count
    
    def _allocate_raw(self, size: int) -> int:
        """
        分配原始内存
        
        Args:
            size: 字节数
            
        Returns:
            int: 内存指针
        """
        # 使用ctypes分配内存
        buffer = (ctypes.c_byte * size)()
        return ctypes.addressof(buffer)
    
    def _free_raw(self, ptr: int) -> None:
        """
        释放原始内存
        
        Args:
            ptr: 内存指针
        """
        # ctypes分配的内存会自动由Python GC释放
        # 此处可添加自定义内存管理逻辑
        pass
    
    def _read_memory(self, ptr: int, size: int) -> bytearray:
        """
        读取内存内容
        
        Args:
            ptr: 内存指针
            size: 字节数
            
        Returns:
            bytearray: 内存内容
        """
        # 使用ctypes从地址读取数据
        buffer = (ctypes.c_byte * size).from_address(ptr)
        return bytearray(buffer)
    
    def _write_memory(self, ptr: int, data: Union[bytes, bytearray]) -> None:
        """
        写入内存内容
        
        Args:
            ptr: 内存指针
            data: 要写入的数据
        """
        # 使用ctypes写入地址
        buffer = (ctypes.c_byte * len(data)).from_address(ptr)
        for i, b in enumerate(data):
            buffer[i] = b
    
    def _auto_compress_thread(self):
        """自动压缩后台线程"""
        while self.compress_thread_active:
            try:
                # 压缩闲置块
                compressed = self.compress_unused_blocks()
                if compressed > 0:
                    logger.debug(f"自动压缩了 {compressed} 个内存块")
                
                # 等待一段时间
                for _ in range(10):  # 分成10次检查，便于更快响应退出
                    if not self.compress_thread_active:
                        break
                    time.sleep(self.auto_compress_after / 10)
                    
            except Exception as e:
                logger.error(f"自动压缩线程异常: {e}")
                time.sleep(1)  # 发生错误时短暂等待

# 创建一个全局实例供模块导入使用
default_allocator = CompressedAllocator()

# 便捷函数
def malloc(size: int) -> int:
    """分配压缩内存"""
    return default_allocator.malloc(size)

def access(ptr: int) -> bytearray:
    """访问压缩内存"""
    return default_allocator.access(ptr)

def free(ptr: int) -> bool:
    """释放压缩内存"""
    return default_allocator.free(ptr)

def get_compression_stats() -> Dict[str, Any]:
    """获取压缩统计信息"""
    return default_allocator.get_stats() 