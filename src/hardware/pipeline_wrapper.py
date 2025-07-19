#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
指令流水线优化包装器 - VisionAI-ClipsMaster
提供Python接口访问底层汇编优化的流水线指令

该模块提供以下功能:
1. 动态加载流水线优化库
2. 提供Python友好的接口调用优化代码
3. 根据CPU微架构特性选择最佳优化路径
4. 无缝整合到已有代码中的替换接口
5. 性能监控和统计
"""

import os
import sys
import time
import ctypes
import logging
import platform
import numpy as np
from typing import Dict, List, Optional, Tuple, Union, Any
from pathlib import Path

# 导入微架构优化相关模块
try:
    from src.hardware.microarch_tuner import get_microarch_tuner
    HAS_MICROARCH_TUNER = True
except ImportError:
    HAS_MICROARCH_TUNER = False
    
# 配置日志
logger = logging.getLogger(__name__)

# 常量定义
LIB_NAME = "pipeline_opt"  # 动态库名称
FALLBACK_MODE = "numpy"    # 无优化库时的回退模式

class PipelineOptimizer:
    """流水线优化器类，提供对底层优化操作的访问"""
    
    def __init__(self):
        """初始化流水线优化器"""
        self.lib = None
        self.supported = False
        self.optimization_level = 0
        self.stats = {"calls": 0, "fallbacks": 0, "total_time": 0.0}
        
        # 尝试加载优化库
        self._load_library()
        
        # 检查流水线优化支持
        if self.lib is not None:
            self.supported = True
            self.optimization_level = self._check_optimization_level()
            logger.info(f"指令流水线优化支持级别: {self.optimization_level}")
        
    def _load_library(self):
        """尝试加载流水线优化动态库"""
        try:
            # 确定库路径和文件名
            root_dir = Path(__file__).resolve().parent
            
            if platform.system() == 'Windows':
                lib_path = root_dir / f"{LIB_NAME}.dll"
            elif platform.system() == 'Darwin':  # macOS
                lib_path = root_dir / f"lib{LIB_NAME}.dylib"
            else:  # Linux and others
                lib_path = root_dir / f"lib{LIB_NAME}.so"
            
            # 尝试加载库
            if lib_path.exists():
                self.lib = ctypes.CDLL(str(lib_path))
                logger.info(f"成功加载流水线优化库: {lib_path}")
                
                # 设置函数参数和返回类型
                self._setup_function_types()
            else:
                logger.warning(f"流水线优化库不存在: {lib_path}")
        except Exception as e:
            logger.error(f"加载流水线优化库失败: {str(e)}")
            self.lib = None
    
    def _setup_function_types(self):
        """设置C函数的参数和返回类型"""
        if self.lib is None:
            return
            
        # 矩阵乘法
        self.lib.matrix_mult_avx2.argtypes = [
            ctypes.POINTER(ctypes.c_float),  # A
            ctypes.POINTER(ctypes.c_float),  # B
            ctypes.POINTER(ctypes.c_float),  # C
            ctypes.c_int,                    # M
            ctypes.c_int,                    # N
            ctypes.c_int                     # K
        ]
        self.lib.matrix_mult_avx2.restype = None
        
        # 向量点积
        self.lib.vector_dot_product_avx2.argtypes = [
            ctypes.POINTER(ctypes.c_float),  # A
            ctypes.POINTER(ctypes.c_float),  # B
            ctypes.c_int                     # size
        ]
        self.lib.vector_dot_product_avx2.restype = ctypes.c_float
        
        # 矩阵向量乘法
        self.lib.matrix_vector_mult_avx2.argtypes = [
            ctypes.POINTER(ctypes.c_float),  # A
            ctypes.POINTER(ctypes.c_float),  # x
            ctypes.POINTER(ctypes.c_float),  # y
            ctypes.c_int,                    # rows
            ctypes.c_int                     # cols
        ]
        self.lib.matrix_vector_mult_avx2.restype = None
        
        # 支持检测
        self.lib.is_pipeline_opt_supported.argtypes = []
        self.lib.is_pipeline_opt_supported.restype = ctypes.c_int
    
    def _check_optimization_level(self) -> int:
        """
        检查当前系统支持的流水线优化级别
        
        Returns:
            int: 优化级别 (0-不支持, 1-部分支持, 2-完全支持)
        """
        if self.lib is None:
            return 0
            
        try:
            return self.lib.is_pipeline_opt_supported()
        except Exception as e:
            logger.error(f"检查优化级别失败: {str(e)}")
            return 0
    
    def matrix_multiply(self, A: np.ndarray, B: np.ndarray) -> np.ndarray:
        """
        优化的矩阵乘法操作
        
        Args:
            A: 输入矩阵A (numpy ndarray)
            B: 输入矩阵B (numpy ndarray)
            
        Returns:
            np.ndarray: 结果矩阵 C = A × B
        """
        self.stats["calls"] += 1
        start_time = time.time()
        
        # 确保输入是正确的浮点格式
        A = np.ascontiguousarray(A, dtype=np.float32)
        B = np.ascontiguousarray(B, dtype=np.float32)
        
        # 获取维度
        M, K = A.shape
        K2, N = B.shape
        
        # 检查维度兼容性
        if K != K2:
            raise ValueError(f"矩阵维度不兼容: A是{A.shape}, B是{B.shape}")
        
        # 创建结果矩阵
        C = np.zeros((M, N), dtype=np.float32)
        
        # 如果可以使用优化库，则调用
        if self.lib is not None and self.optimization_level > 0:
            try:
                # 获取数组指针
                A_ptr = A.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
                B_ptr = B.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
                C_ptr = C.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
                
                # 调用优化函数
                self.lib.matrix_mult_avx2(A_ptr, B_ptr, C_ptr, M, N, K)
            except Exception as e:
                logger.warning(f"优化矩阵乘法失败，回退到NumPy: {str(e)}")
                self.stats["fallbacks"] += 1
                C = np.matmul(A, B)
        else:
            # 没有优化库，使用NumPy
            self.stats["fallbacks"] += 1
            C = np.matmul(A, B)
        
        # 更新统计信息
        elapsed = time.time() - start_time
        self.stats["total_time"] += elapsed
        
        return C
    
    def vector_dot_product(self, A: np.ndarray, B: np.ndarray) -> float:
        """
        优化的向量点积操作
        
        Args:
            A: 输入向量A (numpy ndarray)
            B: 输入向量B (numpy ndarray)
            
        Returns:
            float: 点积结果 A·B
        """
        self.stats["calls"] += 1
        start_time = time.time()
        
        # 确保输入是正确的浮点格式和一维数组
        A = np.ascontiguousarray(A.flatten(), dtype=np.float32)
        B = np.ascontiguousarray(B.flatten(), dtype=np.float32)
        
        # 检查维度兼容性
        if A.shape[0] != B.shape[0]:
            raise ValueError(f"向量长度不匹配: A是{A.shape}, B是{B.shape}")
        
        size = A.shape[0]
        result = 0.0
        
        # 如果可以使用优化库，则调用
        if self.lib is not None and self.optimization_level > 0:
            try:
                # 获取数组指针
                A_ptr = A.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
                B_ptr = B.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
                
                # 调用优化函数
                result = self.lib.vector_dot_product_avx2(A_ptr, B_ptr, size)
            except Exception as e:
                logger.warning(f"优化向量点积失败，回退到NumPy: {str(e)}")
                self.stats["fallbacks"] += 1
                result = np.dot(A, B)
        else:
            # 没有优化库，使用NumPy
            self.stats["fallbacks"] += 1
            result = np.dot(A, B)
        
        # 更新统计信息
        elapsed = time.time() - start_time
        self.stats["total_time"] += elapsed
        
        return float(result)
    
    def matrix_vector_multiply(self, A: np.ndarray, x: np.ndarray) -> np.ndarray:
        """
        优化的矩阵向量乘法操作
        
        Args:
            A: 输入矩阵A (numpy ndarray)
            x: 输入向量x (numpy ndarray)
            
        Returns:
            np.ndarray: 结果向量 y = A × x
        """
        self.stats["calls"] += 1
        start_time = time.time()
        
        # 确保输入是正确的浮点格式
        A = np.ascontiguousarray(A, dtype=np.float32)
        x = np.ascontiguousarray(x.flatten(), dtype=np.float32)
        
        # 获取维度
        rows, cols = A.shape
        
        # 检查维度兼容性
        if cols != x.shape[0]:
            raise ValueError(f"维度不兼容: A是{A.shape}, x是{x.shape}")
        
        # 创建结果向量
        y = np.zeros(rows, dtype=np.float32)
        
        # 如果可以使用优化库，则调用
        if self.lib is not None and self.optimization_level > 0:
            try:
                # 获取数组指针
                A_ptr = A.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
                x_ptr = x.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
                y_ptr = y.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
                
                # 调用优化函数
                self.lib.matrix_vector_mult_avx2(A_ptr, x_ptr, y_ptr, rows, cols)
            except Exception as e:
                logger.warning(f"优化矩阵向量乘法失败，回退到NumPy: {str(e)}")
                self.stats["fallbacks"] += 1
                y = np.dot(A, x)
        else:
            # 没有优化库，使用NumPy
            self.stats["fallbacks"] += 1
            y = np.dot(A, x)
        
        # 更新统计信息
        elapsed = time.time() - start_time
        self.stats["total_time"] += elapsed
        
        return y
    
    def get_stats(self) -> Dict[str, Union[int, float]]:
        """
        获取优化器使用统计信息
        
        Returns:
            Dict: 含有调用次数、回退次数和总时间的字典
        """
        return {
            "calls": self.stats["calls"],
            "fallbacks": self.stats["fallbacks"],
            "total_time": round(self.stats["total_time"], 4),
            "avg_time": round(self.stats["total_time"] / max(1, self.stats["calls"]), 6),
            "fallback_rate": round(self.stats["fallbacks"] / max(1, self.stats["calls"]) * 100, 2),
            "optimization_level": self.optimization_level
        }
    
    def is_supported(self) -> bool:
        """
        检查当前系统是否支持指令流水线优化
        
        Returns:
            bool: 是否支持
        """
        return self.supported and self.optimization_level > 0
        
    def optimize_for_microarch(self) -> Dict[str, Any]:
        """
        根据当前CPU微架构调整优化参数
        
        Returns:
            Dict: 优化参数字典
        """
        # 如果存在微架构调优器，获取最佳参数
        if HAS_MICROARCH_TUNER:
            tuner = get_microarch_tuner()
            params = tuner.tune_for_microarch()
            
            # 记录调优结果
            logger.info(f"根据微架构'{tuner.detected_arch}'优化流水线参数")
            
            return params
        else:
            # 没有微架构调优器，返回默认参数
            return {
                'cache_line_size': 64,
                'prefetch_distance': 128,
                'loop_unroll_factor': 4,
                'branch_prediction': 'moderate',
                'simd_alignment': 32,
                'memory_pattern': 'standard'
            }

# 全局单例
_pipeline_optimizer = None

def get_pipeline_optimizer() -> PipelineOptimizer:
    """
    获取流水线优化器单例
    
    Returns:
        PipelineOptimizer: 流水线优化器实例
    """
    global _pipeline_optimizer
    
    if _pipeline_optimizer is None:
        _pipeline_optimizer = PipelineOptimizer()
        
    return _pipeline_optimizer

def matrix_multiply(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    """
    使用流水线优化的矩阵乘法(全局便捷函数)
    
    Args:
        A: 输入矩阵A
        B: 输入矩阵B
        
    Returns:
        np.ndarray: 结果矩阵 C = A × B
    """
    optimizer = get_pipeline_optimizer()
    return optimizer.matrix_multiply(A, B)

def vector_dot_product(A: np.ndarray, B: np.ndarray) -> float:
    """
    使用流水线优化的向量点积(全局便捷函数)
    
    Args:
        A: 输入向量A
        B: 输入向量B
        
    Returns:
        float: 点积结果
    """
    optimizer = get_pipeline_optimizer()
    return optimizer.vector_dot_product(A, B)

def matrix_vector_multiply(A: np.ndarray, x: np.ndarray) -> np.ndarray:
    """
    使用流水线优化的矩阵向量乘法(全局便捷函数)
    
    Args:
        A: 输入矩阵A
        x: 输入向量x
        
    Returns:
        np.ndarray: 结果向量 y = A × x
    """
    optimizer = get_pipeline_optimizer()
    return optimizer.matrix_vector_multiply(A, x)

def is_pipeline_opt_available() -> bool:
    """
    检查流水线优化是否可用(全局便捷函数)
    
    Returns:
        bool: 是否可用
    """
    optimizer = get_pipeline_optimizer()
    return optimizer.is_supported()

# 主入口，用于测试和示例
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 测试流水线优化
    optimizer = get_pipeline_optimizer()
    print(f"流水线优化支持: {optimizer.is_supported()}")
    print(f"优化级别: {optimizer.optimization_level}")
    
    # 获取微架构优化参数
    params = optimizer.optimize_for_microarch()
    print("流水线微架构优化参数:")
    for k, v in params.items():
        print(f"  {k}: {v}")
    
    # 测试矩阵乘法
    try:
        A = np.random.rand(100, 100).astype(np.float32)
        B = np.random.rand(100, 100).astype(np.float32)
        
        # 优化版本
        start = time.time()
        C1 = optimizer.matrix_multiply(A, B)
        opt_time = time.time() - start
        
        # NumPy版本
        start = time.time()
        C2 = np.matmul(A, B)
        numpy_time = time.time() - start
        
        # 检查结果
        error = np.max(np.abs(C1 - C2))
        print(f"矩阵乘法结果误差: {error}")
        print(f"优化版本时间: {opt_time:.6f}秒")
        print(f"NumPy版本时间: {numpy_time:.6f}秒")
        if opt_time < numpy_time:
            speedup = numpy_time / opt_time
            print(f"加速比: {speedup:.2f}x")
        else:
            print("无加速")
    except Exception as e:
        print(f"矩阵乘法测试失败: {str(e)}")
    
    # 输出统计信息
    print("\n优化器统计信息:")
    stats = optimizer.get_stats()
    for k, v in stats.items():
        print(f"  {k}: {v}") 