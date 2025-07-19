#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SIMD向量化工具函数 - VisionAI-ClipsMaster
提供简便的SIMD优化访问接口
"""

import os
import sys
import time
import numpy as np
from typing import Dict, Optional, Tuple, Union, List, Callable
import logging
from functools import wraps
from pathlib import Path

# 设置日志
logger = logging.getLogger(__name__)

# 导入SIMD操作
from src.hardware.simd_wrapper import get_simd_operations, SimdOperations
from src.hardware.optimization_router import select_optimization_path

# 全局SIMD操作对象缓存
_GLOBAL_SIMD_OPS = None

def get_simd_ops() -> SimdOperations:
    """
    获取全局SIMD操作对象（单例模式）
    
    Returns:
        SimdOperations: SIMD操作对象
    """
    global _GLOBAL_SIMD_OPS
    if _GLOBAL_SIMD_OPS is None:
        _GLOBAL_SIMD_OPS = get_simd_operations()
    return _GLOBAL_SIMD_OPS

def reset_simd_ops(simd_type: str = "auto") -> SimdOperations:
    """
    重置全局SIMD操作对象
    
    Args:
        simd_type: SIMD指令集类型
        
    Returns:
        SimdOperations: 新的SIMD操作对象
    """
    global _GLOBAL_SIMD_OPS
    _GLOBAL_SIMD_OPS = get_simd_operations(simd_type)
    return _GLOBAL_SIMD_OPS

def with_simd_timing(func):
    """
    装饰器: 记录SIMD操作的执行时间
    
    Args:
        func: 要装饰的函数
        
    Returns:
        装饰后的函数
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        logger.debug(f"SIMD操作 {func.__name__} 执行时间: {end_time - start_time:.6f}秒")
        return result
    return wrapper

# 矩阵操作快捷函数

def matrix_multiply(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """
    SIMD优化的矩阵乘法
    
    Args:
        a: 矩阵A
        b: 矩阵B
        
    Returns:
        矩阵乘法结果C = A × B
    """
    return get_simd_ops().matrix_multiply(a, b)

def matrix_element_multiply(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """
    SIMD优化的元素乘法（Hadamard积）
    
    Args:
        a: 矩阵A
        b: 矩阵B（与A形状相同）
        
    Returns:
        元素乘法结果C，C[i,j] = A[i,j] * B[i,j]
    """
    return get_simd_ops().matrix_element_multiply(a, b)

def matrix_add(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """
    SIMD优化的矩阵加法
    
    Args:
        a: 矩阵A
        b: 矩阵B（与A形状相同）
        
    Returns:
        矩阵加法结果C = A + B
    """
    return get_simd_ops().matrix_add(a, b)

def vector_scale(vec: np.ndarray, scalar: float) -> np.ndarray:
    """
    SIMD优化的向量缩放
    
    Args:
        vec: 输入向量
        scalar: 缩放因子
        
    Returns:
        缩放后的向量 result = scalar * vec
    """
    return get_simd_ops().vector_scale(vec, scalar)

def fused_multiply_add(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> np.ndarray:
    """
    SIMD优化的融合乘加操作
    
    Args:
        a: 矩阵A
        b: 矩阵B（与A形状相同）
        c: 矩阵C（与A形状相同）
        
    Returns:
        融合乘加结果 result = A * B + C
    """
    return get_simd_ops().fused_multiply_add(a, b, c)

# 应用场景优化函数

def optimize_video_frame(frame: np.ndarray, kernel: np.ndarray) -> np.ndarray:
    """
    优化视频帧处理
    
    Args:
        frame: 输入视频帧
        kernel: 处理内核
        
    Returns:
        处理后的视频帧
    """
    return matrix_element_multiply(frame, kernel)

def linear_combination(matrices: List[np.ndarray], weights: List[float]) -> np.ndarray:
    """
    计算矩阵的线性组合: result = sum(weight_i * matrix_i)
    
    Args:
        matrices: 矩阵列表
        weights: 权重列表
        
    Returns:
        线性组合结果
    """
    if len(matrices) != len(weights):
        raise ValueError("矩阵数量和权重数量必须相同")
        
    result = vector_scale(matrices[0], weights[0])
    
    for i in range(1, len(matrices)):
        scaled = vector_scale(matrices[i], weights[i])
        result = matrix_add(result, scaled)
        
    return result

def batch_matrix_multiply(a: np.ndarray, b_list: List[np.ndarray]) -> List[np.ndarray]:
    """
    批量矩阵乘法: 将矩阵A与多个矩阵B相乘
    
    Args:
        a: 矩阵A
        b_list: B矩阵列表
        
    Returns:
        结果矩阵列表
    """
    return [matrix_multiply(a, b) for b in b_list]

@with_simd_timing
def model_layer_forward(input_data: np.ndarray, weights: np.ndarray, 
                      bias: Optional[np.ndarray] = None) -> np.ndarray:
    """
    模型层前向传播: output = input × weights + bias
    
    Args:
        input_data: 输入数据
        weights: 权重矩阵
        bias: 偏置向量（可选）
        
    Returns:
        层输出
    """
    output = matrix_multiply(input_data, weights)
    
    if bias is not None:
        output = matrix_add(output, bias)
        
    return output

def is_simd_available() -> bool:
    """
    检查SIMD操作是否可用
    
    Returns:
        bool: 是否可用
    """
    simd_ops = get_simd_ops()
    return simd_ops is not None

def get_simd_performance_rating() -> int:
    """
    获取SIMD性能评级 (0-100)
    
    Returns:
        int: 性能评级
    """
    from src.hardware.optimization_router import OptimizationRouter
    
    router = OptimizationRouter()
    level = router.get_optimization_level()
    
    return level.get('performance_rating', 0)

def get_simd_info() -> Dict:
    """
    获取SIMD信息
    
    Returns:
        Dict: SIMD信息
    """
    simd_ops = get_simd_ops()
    
    if simd_ops is None:
        return {
            "available": False,
            "simd_type": "none",
            "lib_loaded": False
        }
    
    return {
        "available": True,
        "simd_type": simd_ops.simd_type,
        "lib_loaded": simd_ops.simd_lib_loaded,
        "lib_path": simd_ops.simd_lib_path if hasattr(simd_ops, "simd_lib_path") else None,
        "performance_rating": get_simd_performance_rating()
    }

if __name__ == "__main__":
    # 设置日志级别
    logging.basicConfig(level=logging.INFO, 
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # 显示SIMD信息
    simd_info = get_simd_info()
    print("SIMD信息:")
    for key, value in simd_info.items():
        print(f"  {key}: {value}")
    
    # 简单测试
    size = 1000
    a = np.random.rand(size, size).astype(np.float32)
    b = np.random.rand(size, size).astype(np.float32)
    
    # 测试矩阵乘法
    print("\n测试矩阵乘法性能...")
    start_time = time.time()
    c_numpy = np.matmul(a, b)
    numpy_time = time.time() - start_time
    print(f"NumPy时间: {numpy_time:.4f}秒")
    
    start_time = time.time()
    c_simd = matrix_multiply(a, b)
    simd_time = time.time() - start_time
    print(f"SIMD时间: {simd_time:.4f}秒")
    
    is_correct = np.allclose(c_numpy, c_simd, rtol=1e-5, atol=1e-5)
    print(f"结果正确: {is_correct}")
    
    if numpy_time > 0:
        speedup = numpy_time / simd_time
        print(f"加速比: {speedup:.2f}x") 