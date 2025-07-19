#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
内存对齐优化模块 - VisionAI-ClipsMaster
提供内存对齐分配功能，以优化SIMD和汇编操作的性能

内存对齐的主要优势:
1. 提高内存访问速度: 对齐的内存访问可以减少CPU访问内存所需的周期数
2. SIMD指令要求: 许多SIMD指令要求数据在内存中是对齐的
3. 避免分割访问: 防止CPU跨缓存行访问数据，提高缓存效率
4. 硬件优化: 现代处理器对对齐的内存访问进行了硬件级优化

此模块提供:
- 不同平台的内存对齐分配
- 支持32位、64位和128位等常见对齐需求
- 与SIMD和汇编优化的无缝集成
- 自动内存管理和释放机制
"""

import os
import sys
import ctypes
import logging
import platform
import numpy as np
from typing import Dict, List, Optional, Tuple, Union, Any
from pathlib import Path
import functools
import gc
import weakref
import threading

# 设置日志
logger = logging.getLogger(__name__)

# 默认内存对齐常量
DEFAULT_ALIGNMENT = 64  # 默认64字节对齐 (适用于大多数SIMD指令)
CACHE_LINE_SIZE = 64    # 常见处理器的缓存行大小

# 平台特定设置
if platform.system() == 'Windows':
    try:
        import _aligned_memory
        HAS_ALIGNED_MEMORY = True
    except ImportError:
        HAS_ALIGNED_MEMORY = False
else:
    HAS_ALIGNED_MEMORY = False

# 追踪已分配的内存，以便正确释放
_ALLOCATED_MEMORY = weakref.WeakValueDictionary()
_MEMORY_LOCK = threading.RLock()

def aligned_alloc(size: int, alignment: int = DEFAULT_ALIGNMENT) -> ctypes.c_void_p:
    """
    申请内存对齐缓冲区 (64字节对齐)
    
    Args:
        size: 请求的内存大小（字节）
        alignment: 内存对齐值（字节），默认为64
        
    Returns:
        ctypes.c_void_p: 对齐的内存指针
    """
    # 确保alignment是2的幂
    if alignment & (alignment - 1) != 0:
        raise ValueError(f"对齐值必须是2的幂，而不是 {alignment}")
    
    # 创建原始内存缓冲区 (比请求的大，以便可以进行对齐调整)
    raw_ptr = ctypes.create_string_buffer(size + alignment)
    
    # 计算内存地址对齐的偏移
    offset = alignment - (ctypes.addressof(raw_ptr) % alignment)
    
    # 返回对齐后的指针
    ptr = ctypes.cast(ctypes.addressof(raw_ptr) + offset, ctypes.c_void_p)
    
    # 使用弱引用字典保存原始缓冲区引用，防止垃圾回收
    with _MEMORY_LOCK:
        _ALLOCATED_MEMORY[ptr.value] = raw_ptr
    
    return ptr

def aligned_free(ptr: ctypes.c_void_p) -> bool:
    """
    释放已对齐的内存
    
    Args:
        ptr: 对齐内存的指针
        
    Returns:
        bool: 释放是否成功
    """
    with _MEMORY_LOCK:
        if ptr.value in _ALLOCATED_MEMORY:
            del _ALLOCATED_MEMORY[ptr.value]
            return True
    return False

def get_alignment_for_simd(instruction_set: str = None) -> int:
    """
    基于SIMD指令集确定最优内存对齐值
    
    Args:
        instruction_set: SIMD指令集名称 (avx512/avx2/avx/sse/neon)
        
    Returns:
        int: 推荐的内存对齐字节数
    """
    # 如果未指定指令集，尝试自动检测
    if instruction_set is None:
        try:
            from src.hardware.optimization_router import select_optimization_path
            instruction_set = select_optimization_path()
        except ImportError:
            # 默认使用安全的对齐值
            return DEFAULT_ALIGNMENT
    
    # 针对不同指令集的最佳对齐值
    alignment_map = {
        'avx512': 64,  # 512位 = 64字节
        'avx2': 32,    # 256位 = 32字节
        'avx': 32,     # 256位 = 32字节
        'sse4.2': 16,  # 128位 = 16字节
        'sse': 16,     # 128位 = 16字节
        'neon': 16,    # 128位 = 16字节
        'baseline': 8  # 默认对齐
    }
    
    return alignment_map.get(instruction_set.lower(), DEFAULT_ALIGNMENT)

class AlignedMemory:
    """内存对齐管理类，提供自动内存管理和NumPy数组支持"""
    
    def __init__(self, alignment: int = DEFAULT_ALIGNMENT):
        """
        初始化对齐内存管理器
        
        Args:
            alignment: 内存对齐字节数
        """
        self.alignment = alignment
        self.allocations = {}  # 跟踪分配的内存
        self.lock = threading.RLock()
    
    def allocate(self, size: int) -> ctypes.c_void_p:
        """
        分配对齐内存
        
        Args:
            size: 请求的内存大小（字节）
            
        Returns:
            ctypes.c_void_p: 对齐的内存指针
        """
        with self.lock:
            ptr = aligned_alloc(size, self.alignment)
            self.allocations[ptr.value] = size
            return ptr
    
    def free(self, ptr: ctypes.c_void_p) -> bool:
        """
        释放对齐内存
        
        Args:
            ptr: 内存指针
            
        Returns:
            bool: 操作是否成功
        """
        with self.lock:
            if ptr.value in self.allocations:
                del self.allocations[ptr.value]
                return aligned_free(ptr)
            return False
    
    def create_array(self, shape: Tuple[int, ...], dtype=np.float32) -> np.ndarray:
        """
        创建对齐的NumPy数组
        
        Args:
            shape: 数组形状
            dtype: 数据类型
            
        Returns:
            np.ndarray: 对齐的NumPy数组
        """
        size = int(np.prod(shape)) * np.dtype(dtype).itemsize
        ptr = self.allocate(size)
        
        # 创建使用此内存的NumPy数组
        array = np.frombuffer(
            (ctypes.c_byte * size).from_address(ptr.value),
            dtype=dtype
        ).reshape(shape)
        
        # 使数组不可调整大小，防止在不知情的情况下重新分配内存
        array.flags.writeable = True
        
        return array
    
    def get_allocation_stats(self) -> Dict[str, int]:
        """
        获取内存分配统计信息
        
        Returns:
            Dict[str, int]: 包含分配统计的字典
        """
        with self.lock:
            return {
                'count': len(self.allocations),
                'total_bytes': sum(self.allocations.values()),
                'alignment': self.alignment
            }
    
    def cleanup(self) -> int:
        """
        清理所有分配的内存
        
        Returns:
            int: 释放的内存块数量
        """
        with self.lock:
            count = len(self.allocations)
            for ptr_value in list(self.allocations.keys()):
                ptr = ctypes.c_void_p(ptr_value)
                aligned_free(ptr)
            self.allocations.clear()
            return count
    
    def __del__(self):
        """析构函数，确保清理所有分配的内存"""
        self.cleanup()

class AlignedArray:
    """使用对齐内存的NumPy数组包装类，提供自动内存管理"""
    
    def __init__(self, shape: Tuple[int, ...], dtype=np.float32, alignment: int = None):
        """
        初始化对齐数组
        
        Args:
            shape: 数组形状
            dtype: 数据类型
            alignment: 内存对齐字节数，如果为None则自动选择
        """
        if alignment is None:
            alignment = get_alignment_for_simd()
        
        self.alignment = alignment
        self.memory_manager = AlignedMemory(alignment)
        self.array = self.memory_manager.create_array(shape, dtype)
    
    def get_array(self) -> np.ndarray:
        """获取底层NumPy数组"""
        return self.array
    
    def __getattr__(self, name):
        """委托属性访问到底层数组"""
        return getattr(self.array, name)
    
    def __del__(self):
        """清理资源"""
        self.memory_manager.cleanup()

# 便捷函数

def create_aligned_array(shape: Union[Tuple[int, ...], List[int]],
                        dtype=np.float32,
                        alignment: int = None) -> np.ndarray:
    """
    创建内存对齐的NumPy数组
    
    Args:
        shape: 数组形状
        dtype: 数据类型
        alignment: 对齐字节数 (如果为None，会自动选择最佳值)
        
    Returns:
        np.ndarray: 内存对齐的NumPy数组
    """
    if alignment is None:
        alignment = get_alignment_for_simd()
    
    aligned_obj = AlignedArray(shape, dtype, alignment)
    return aligned_obj.get_array()

def is_aligned(array: np.ndarray, alignment: int = DEFAULT_ALIGNMENT) -> bool:
    """
    检查数组是否已对齐到指定边界
    
    Args:
        array: 要检查的NumPy数组
        alignment: 检查的对齐边界
        
    Returns:
        bool: 数组是否对齐
    """
    return array.ctypes.data % alignment == 0

def align_array(array: np.ndarray, alignment: int = None) -> np.ndarray:
    """
    复制数组到对齐的内存中
    
    Args:
        array: 要对齐的数组
        alignment: 对齐字节数
        
    Returns:
        np.ndarray: 对齐的数组副本
    """
    # 如果数组已经对齐，直接返回
    if alignment is not None and is_aligned(array, alignment):
        return array
    
    # 创建对齐的数组并复制数据
    aligned = create_aligned_array(array.shape, array.dtype, alignment)
    aligned[:] = array
    return aligned

# 在模块导入时注册清理函数
def _cleanup_on_exit():
    with _MEMORY_LOCK:
        _ALLOCATED_MEMORY.clear()
    gc.collect()

import atexit
atexit.register(_cleanup_on_exit)

# 测试代码
if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("\n=== 内存对齐优化测试 ===\n")
    
    # 检测平台优化
    print(f"当前平台: {platform.system()} {platform.machine()}")
    
    # 获取最佳对齐值
    optimal_alignment = get_alignment_for_simd()
    print(f"最佳内存对齐: {optimal_alignment}字节")
    
    # 创建对齐的数组
    shape = (1000, 1000)
    dtype = np.float32
    
    print(f"\n创建形状为{shape}的对齐数组")
    start = time.time()
    aligned_array = create_aligned_array(shape, dtype)
    print(f"创建对齐数组耗时: {(time.time() - start)*1000:.2f}ms")
    
    # 验证对齐
    print(f"数组地址: {aligned_array.ctypes.data}")
    print(f"是否对齐到{optimal_alignment}字节: {is_aligned(aligned_array, optimal_alignment)}")
    
    # 与标准NumPy数组比较
    start = time.time()
    standard_array = np.zeros(shape, dtype=dtype)
    print(f"创建标准NumPy数组耗时: {(time.time() - start)*1000:.2f}ms")
    print(f"标准数组是否对齐到{optimal_alignment}字节: {is_aligned(standard_array, optimal_alignment)}")
    
    # 简单的性能测试
    print("\n性能测试:")
    
    # 填充随机数据
    aligned_array[:] = np.random.random(shape).astype(dtype)
    standard_array[:] = aligned_array.copy()
    
    # 矩阵乘法测试
    print("矩阵乘法测试:")
    iterations = 10
    
    # 对齐数组测试
    start = time.time()
    for _ in range(iterations):
        result_aligned = np.dot(aligned_array, aligned_array)
    aligned_time = time.time() - start
    print(f"对齐数组: {aligned_time/iterations*1000:.2f}ms/次")
    
    # 标准数组测试
    start = time.time()
    for _ in range(iterations):
        result_standard = np.dot(standard_array, standard_array)
    standard_time = time.time() - start
    print(f"标准数组: {standard_time/iterations*1000:.2f}ms/次")
    
    # 比较结果
    speedup = standard_time / aligned_time if aligned_time > 0 else 0
    print(f"加速比: {speedup:.2f}x")
    
    # 清理资源
    print("\n清理资源...")
    _cleanup_on_exit()
    print("测试完成!") 