#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
平台特定汇编适配 - VisionAI-ClipsMaster
为不同平台提供优化的汇编实现，包括:
- Linux: 使用GCC内联汇编
- macOS: 调用Accelerate框架
- Windows: 使用Intel MKL
"""

import os
import sys
import platform
import ctypes
import logging
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import time

# 设置日志
logger = logging.getLogger(__name__)

# 项目根目录
ROOT_DIR = Path(__file__).resolve().parent.parent.parent

# 平台特定库文件名
if platform.system() == "Windows":
    ASM_LIB_NAME = "assembly_kernels.dll"
elif platform.system() == "Darwin":  # macOS
    ASM_LIB_NAME = "libassembly_kernels.dylib"
else:  # Linux和其他类Unix系统
    ASM_LIB_NAME = "libassembly_kernels.so"

# 库文件路径
ASM_LIB_PATH = os.path.join(ROOT_DIR, "lib", ASM_LIB_NAME)

class PlatformAsm:
    """平台特定汇编优化包装器"""
    
    def __init__(self):
        """初始化汇编包装器"""
        self.lib = None
        self.platform_info = self._get_platform_info()
        
        # 尝试加载平台特定库
        if platform.system() == 'Linux':
            self.lib = self._load_linux_asm_lib()
        elif platform.system() == 'Darwin':
            self.lib = self._load_macos_asm_lib()
        elif platform.system() == 'Windows':
            self.lib = self._load_windows_asm_lib()
        else:
            logger.warning(f"未知平台: {platform.system()}")
            self.lib = None
            
        # 设置函数签名
        if self.lib is not None:
            self._setup_function_signatures()
            logger.info(f"已加载{platform.system()}平台汇编库")
            
    def _get_platform_info(self) -> Dict:
        """获取平台信息"""
        return {
            'system': platform.system(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'python_version': sys.version,
            'python_bits': 64 if sys.maxsize > 2**32 else 32
        }
        
    def _load_linux_asm_lib(self) -> Optional[ctypes.CDLL]:
        """加载Linux平台汇编库"""
        try:
            if os.path.exists(ASM_LIB_PATH):
                return ctypes.CDLL(ASM_LIB_PATH)
            else:
                logger.warning(f"Linux平台汇编库不存在: {ASM_LIB_PATH}")
                return None
        except Exception as e:
            logger.error(f"加载Linux平台汇编库失败: {str(e)}")
            return None
            
    def _load_macos_asm_lib(self) -> Optional[ctypes.CDLL]:
        """加载macOS平台汇编库"""
        try:
            if os.path.exists(ASM_LIB_PATH):
                return ctypes.CDLL(ASM_LIB_PATH)
            else:
                logger.warning(f"macOS平台汇编库不存在: {ASM_LIB_PATH}")
                return None
        except Exception as e:
            logger.error(f"加载macOS平台汇编库失败: {str(e)}")
            return None
            
    def _load_windows_asm_lib(self) -> Optional[ctypes.CDLL]:
        """加载Windows平台汇编库"""
        try:
            if os.path.exists(ASM_LIB_PATH):
                return ctypes.CDLL(ASM_LIB_PATH)
            else:
                logger.warning(f"Windows平台汇编库不存在: {ASM_LIB_PATH}")
                return None
        except Exception as e:
            logger.error(f"加载Windows平台汇编库失败: {str(e)}")
            return None
            
    def _setup_function_signatures(self):
        """设置库函数签名"""
        if self.lib is None:
            return
            
        try:
            # 获取优化级别
            self.lib.get_assembly_optimization_level.argtypes = []
            self.lib.get_assembly_optimization_level.restype = ctypes.c_int
            
            # 矩阵乘法
            self.lib.asm_matrix_multiply.argtypes = [
                ctypes.POINTER(ctypes.c_float),  # A
                ctypes.POINTER(ctypes.c_float),  # B
                ctypes.POINTER(ctypes.c_float),  # C
                ctypes.c_int,  # M
                ctypes.c_int,  # N
                ctypes.c_int   # K
            ]
            self.lib.asm_matrix_multiply.restype = None
            
            # 矩阵加法
            self.lib.asm_matrix_add.argtypes = [
                ctypes.POINTER(ctypes.c_float),  # A
                ctypes.POINTER(ctypes.c_float),  # B
                ctypes.POINTER(ctypes.c_float),  # C
                ctypes.c_int   # size
            ]
            self.lib.asm_matrix_add.restype = None
            
            # 向量点积
            self.lib.asm_vector_dot.argtypes = [
                ctypes.POINTER(ctypes.c_float),  # A
                ctypes.POINTER(ctypes.c_float),  # B
                ctypes.c_int   # size
            ]
            self.lib.asm_vector_dot.restype = ctypes.c_float
            
            # 向量缩放
            self.lib.asm_vector_scale.argtypes = [
                ctypes.POINTER(ctypes.c_float),  # A
                ctypes.POINTER(ctypes.c_float),  # B
                ctypes.c_float,  # scalar
                ctypes.c_int   # size
            ]
            self.lib.asm_vector_scale.restype = None
            
            # 获取库版本
            self.lib.get_assembly_version.argtypes = []
            self.lib.get_assembly_version.restype = ctypes.c_char_p
            
            # 获取平台信息
            self.lib.get_platform_info.argtypes = []
            self.lib.get_platform_info.restype = ctypes.c_int
            
        except Exception as e:
            logger.error(f"设置函数签名失败: {str(e)}")
            self.lib = None
    
    def get_optimization_level(self) -> int:
        """
        获取汇编优化级别
        
        Returns:
            int: 优化级别 (0-不支持, 1-基本优化, 2-高级优化)
        """
        if self.lib is None:
            return 0
            
        try:
            return self.lib.get_assembly_optimization_level()
        except Exception as e:
            logger.error(f"获取优化级别失败: {str(e)}")
            return 0
            
    def get_library_info(self) -> Dict:
        """
        获取汇编库信息
        
        Returns:
            Dict: 库信息字典
        """
        info = {
            'available': self.lib is not None,
            'platform': self.platform_info,
            'optimization_level': self.get_optimization_level(),
            'version': None,
            'platform_id': None
        }
        
        if self.lib is not None:
            try:
                version_bytes = self.lib.get_assembly_version()
                info['version'] = version_bytes.decode('utf-8')
                info['platform_id'] = self.lib.get_platform_info()
            except Exception as e:
                logger.error(f"获取库信息失败: {str(e)}")
                
        return info
    
    def optimized_matrix_multiply(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        """
        使用汇编优化的矩阵乘法
        
        Args:
            a: 第一个矩阵
            b: 第二个矩阵
            
        Returns:
            np.ndarray: 结果矩阵
        """
        if self.lib is None:
            return fallback_matrix_multiply(a, b)
            
        # 确保数据类型正确
        a = np.ascontiguousarray(a, dtype=np.float32)
        b = np.ascontiguousarray(b, dtype=np.float32)
        
        # 检查维度
        if a.ndim != 2 or b.ndim != 2:
            raise ValueError("输入必须是2D矩阵")
            
        if a.shape[1] != b.shape[0]:
            raise ValueError(f"矩阵维度不匹配: {a.shape} 和 {b.shape}")
            
        # 创建结果矩阵
        m, k = a.shape
        k, n = b.shape
        c = np.zeros((m, n), dtype=np.float32)
        
        try:
            # 调用汇编优化函数
            self.lib.asm_matrix_multiply(
                a.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
                b.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
                c.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
                ctypes.c_int(m),
                ctypes.c_int(n),
                ctypes.c_int(k)
            )
            return c
        except Exception as e:
            logger.error(f"汇编矩阵乘法失败: {str(e)}")
            return fallback_matrix_multiply(a, b)
    
    def optimized_matrix_add(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        """
        使用汇编优化的矩阵加法
        
        Args:
            a: 第一个矩阵
            b: 第二个矩阵
            
        Returns:
            np.ndarray: 结果矩阵
        """
        if self.lib is None:
            return fallback_matrix_add(a, b)
            
        # 确保数据类型正确
        a = np.ascontiguousarray(a, dtype=np.float32)
        b = np.ascontiguousarray(b, dtype=np.float32)
        
        # 检查维度
        if a.shape != b.shape:
            raise ValueError(f"矩阵维度不匹配: {a.shape} 和 {b.shape}")
            
        # 创建结果矩阵
        c = np.zeros_like(a, dtype=np.float32)
        size = a.size
        
        try:
            # 调用汇编优化函数
            self.lib.asm_matrix_add(
                a.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
                b.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
                c.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
                ctypes.c_int(size)
            )
            return c
        except Exception as e:
            logger.error(f"汇编矩阵加法失败: {str(e)}")
            return fallback_matrix_add(a, b)
    
    def optimized_vector_dot(self, a: np.ndarray, b: np.ndarray) -> float:
        """
        使用汇编优化的向量点积
        
        Args:
            a: 第一个向量
            b: 第二个向量
            
        Returns:
            float: 点积结果
        """
        if self.lib is None:
            return fallback_vector_dot(a, b)
            
        # 确保数据类型正确
        a = np.ascontiguousarray(a, dtype=np.float32).flatten()
        b = np.ascontiguousarray(b, dtype=np.float32).flatten()
        
        # 检查维度
        if a.size != b.size:
            raise ValueError(f"向量维度不匹配: {a.size} 和 {b.size}")
            
        try:
            # 调用汇编优化函数
            result = self.lib.asm_vector_dot(
                a.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
                b.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
                ctypes.c_int(a.size)
            )
            return result
        except Exception as e:
            logger.error(f"汇编向量点积失败: {str(e)}")
            return fallback_vector_dot(a, b)
    
    def optimized_vector_scale(self, a: np.ndarray, scalar: float) -> np.ndarray:
        """
        使用汇编优化的向量缩放
        
        Args:
            a: 输入向量
            scalar: 缩放因子
            
        Returns:
            np.ndarray: 缩放后的向量
        """
        if self.lib is None:
            return fallback_vector_scale(a, scalar)
            
        # 确保数据类型正确
        a = np.ascontiguousarray(a, dtype=np.float32)
        b = np.zeros_like(a, dtype=np.float32)
        
        try:
            # 调用汇编优化函数
            self.lib.asm_vector_scale(
                a.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
                b.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
                ctypes.c_float(scalar),
                ctypes.c_int(a.size)
            )
            return b
        except Exception as e:
            logger.error(f"汇编向量缩放失败: {str(e)}")
            return fallback_vector_scale(a, scalar)
    
    def optimized_op(self, data, operation='matrix_multiply', **kwargs):
        """
        通用优化操作接口
        
        Args:
            data: 输入数据
            operation: 操作类型
            **kwargs: 额外参数
            
        Returns:
            操作结果
        """
        if self.lib:
            if operation == 'matrix_multiply':
                return self.optimized_matrix_multiply(data, kwargs.get('b'))
            elif operation == 'matrix_add':
                return self.optimized_matrix_add(data, kwargs.get('b'))
            elif operation == 'vector_dot':
                return self.optimized_vector_dot(data, kwargs.get('b'))
            elif operation == 'vector_scale':
                return self.optimized_vector_scale(data, kwargs.get('scalar', 1.0))
            else:
                logger.warning(f"不支持的操作: {operation}")
                return fallback_operation(data, operation, **kwargs)
        else:
            return fallback_operation(data, operation, **kwargs)
            
    def run_benchmark(self) -> Dict:
        """
        运行性能基准测试
        
        Returns:
            Dict: 基准测试结果
        """
        results = {}
        
        # 矩阵乘法基准测试
        sizes = [128, 256, 512, 1024]
        for size in sizes:
            # 创建随机矩阵
            a = np.random.rand(size, size).astype(np.float32)
            b = np.random.rand(size, size).astype(np.float32)
            
            # 测试优化版本
            start = time.time()
            c_opt = self.optimized_matrix_multiply(a, b)
            opt_time = time.time() - start
            
            # 测试NumPy版本
            start = time.time()
            c_np = np.matmul(a, b)
            np_time = time.time() - start
            
            # 检查结果正确性
            is_correct = np.allclose(c_opt, c_np, rtol=1e-5, atol=1e-5)
            
            results[f'matrix_multiply_{size}'] = {
                'size': size,
                'optimized_time': opt_time,
                'numpy_time': np_time,
                'speedup': np_time / opt_time if opt_time > 0 else 0,
                'is_correct': is_correct
            }
            
        # 矩阵加法基准测试
        for size in sizes:
            # 创建随机矩阵
            a = np.random.rand(size, size).astype(np.float32)
            b = np.random.rand(size, size).astype(np.float32)
            
            # 测试优化版本
            start = time.time()
            c_opt = self.optimized_matrix_add(a, b)
            opt_time = time.time() - start
            
            # 测试NumPy版本
            start = time.time()
            c_np = a + b
            np_time = time.time() - start
            
            # 检查结果正确性
            is_correct = np.allclose(c_opt, c_np, rtol=1e-5, atol=1e-5)
            
            results[f'matrix_add_{size}'] = {
                'size': size,
                'optimized_time': opt_time,
                'numpy_time': np_time,
                'speedup': np_time / opt_time if opt_time > 0 else 0,
                'is_correct': is_correct
            }
            
        # 向量点积基准测试
        vec_sizes = [1000, 10000, 100000, 1000000]
        for size in vec_sizes:
            # 创建随机向量
            a = np.random.rand(size).astype(np.float32)
            b = np.random.rand(size).astype(np.float32)
            
            # 测试优化版本
            start = time.time()
            dot_opt = self.optimized_vector_dot(a, b)
            opt_time = time.time() - start
            
            # 测试NumPy版本
            start = time.time()
            dot_np = np.dot(a, b)
            np_time = time.time() - start
            
            # 检查结果正确性
            is_correct = abs(dot_opt - dot_np) < 1e-3 * abs(dot_np)
            
            results[f'vector_dot_{size}'] = {
                'size': size,
                'optimized_time': opt_time,
                'numpy_time': np_time,
                'speedup': np_time / opt_time if opt_time > 0 else 0,
                'is_correct': is_correct
            }
            
        return results

# 纯Python回退实现

def fallback_matrix_multiply(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """纯NumPy矩阵乘法实现"""
    return np.matmul(a, b)

def fallback_matrix_add(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """纯NumPy矩阵加法实现"""
    return a + b

def fallback_vector_dot(a: np.ndarray, b: np.ndarray) -> float:
    """纯NumPy向量点积实现"""
    return float(np.dot(a.flatten(), b.flatten()))

def fallback_vector_scale(a: np.ndarray, scalar: float) -> np.ndarray:
    """纯NumPy向量缩放实现"""
    return a * scalar

def fallback_operation(data, operation='matrix_multiply', **kwargs):
    """通用回退操作"""
    if operation == 'matrix_multiply':
        return fallback_matrix_multiply(data, kwargs.get('b'))
    elif operation == 'matrix_add':
        return fallback_matrix_add(data, kwargs.get('b'))
    elif operation == 'vector_dot':
        return fallback_vector_dot(data, kwargs.get('b'))
    elif operation == 'vector_scale':
        return fallback_vector_scale(data, kwargs.get('scalar', 1.0))
    else:
        raise ValueError(f"不支持的操作: {operation}")

# 便捷函数

def get_platform_asm() -> PlatformAsm:
    """
    获取平台汇编优化实例
    
    Returns:
        PlatformAsm: 平台优化实例
    """
    return PlatformAsm()

# 测试代码
if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("=== VisionAI-ClipsMaster 平台特定汇编优化测试 ===\n")
    
    # 创建平台优化实例
    asm = PlatformAsm()
    
    # 显示库信息
    info = asm.get_library_info()
    print(f"平台: {info['platform']['system']} {info['platform']['machine']}")
    print(f"汇编库可用: {'是' if info['available'] else '否'}")
    
    if info['available']:
        print(f"库版本: {info['version']}")
        print(f"优化级别: {info['optimization_level']}")
        print(f"平台ID: {info['platform_id']}")
    
    # 运行简单测试
    print("\n简单性能测试:")
    
    # 创建测试矩阵
    size = 500
    a = np.random.rand(size, size).astype(np.float32)
    b = np.random.rand(size, size).astype(np.float32)
    
    # 测试矩阵乘法
    print(f"\n{size}x{size}矩阵乘法:")
    
    # 优化版本
    start = time.time()
    c_opt = asm.optimized_matrix_multiply(a, b)
    opt_time = time.time() - start
    print(f"  优化版本: {opt_time:.6f}秒")
    
    # NumPy版本
    start = time.time()
    c_np = np.matmul(a, b)
    np_time = time.time() - start
    print(f"  NumPy版本: {np_time:.6f}秒")
    
    # 检查结果
    is_correct = np.allclose(c_opt, c_np, rtol=1e-4, atol=1e-4)
    speedup = np_time / opt_time if opt_time > 0 else 0
    print(f"  加速比: {speedup:.2f}x")
    print(f"  结果正确: {'是' if is_correct else '否'}")
    
    # 运行完整基准测试
    print("\n运行完整基准测试...")
    benchmark = asm.run_benchmark()
    
    # 打印结果
    for test_name, result in benchmark.items():
        print(f"\n{test_name}:")
        print(f"  大小: {result['size']}")
        print(f"  优化时间: {result['optimized_time']:.6f}秒")
        print(f"  NumPy时间: {result['numpy_time']:.6f}秒")
        print(f"  加速比: {result['speedup']:.2f}x")
        print(f"  结果正确: {'是' if result['is_correct'] else '否'}") 