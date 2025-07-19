#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SIMD向量化操作Python包装器 - VisionAI-ClipsMaster
为Python提供高性能SIMD向量化计算功能
"""

import os
import sys
import platform
import ctypes
import numpy as np
from typing import List, Union, Tuple, Optional, Dict
import logging
from pathlib import Path
import time
import json

# 项目根目录
ROOT_DIR = Path(__file__).resolve().parent.parent.parent

# 使用日志记录库
logger = logging.getLogger(__name__)

# SIMD库文件路径 (根据平台确定扩展名)
if platform.system() == "Windows":
    SIMD_LIB_PATH = os.path.join(ROOT_DIR, "lib", "simd_kernels.dll")
elif platform.system() == "Darwin":  # macOS
    SIMD_LIB_PATH = os.path.join(ROOT_DIR, "lib", "libsimd_kernels.dylib")
else:  # Linux和其他类Unix系统
    SIMD_LIB_PATH = os.path.join(ROOT_DIR, "lib", "libsimd_kernels.so")

# 尝试导入内存对齐模块
try:
    from src.hardware.memory_aligner import align_array, is_aligned, get_alignment_for_simd
    HAS_MEMORY_ALIGNMENT = True
except ImportError:
    HAS_MEMORY_ALIGNMENT = False
    logger.warning("内存对齐模块不可用，SIMD性能可能受到影响")

def _check_simd_lib_exists():
    """检查SIMD库文件是否存在"""
    return os.path.exists(SIMD_LIB_PATH)

def load_simd_config() -> Dict:
    """
    加载SIMD配置文件
    
    Returns:
        Dict: 配置字典，如果无法加载则返回默认配置
    """
    config_path = os.path.join(ROOT_DIR, "configs", "simd_config.json")
    default_config = {
        "simd_optimization": {
            "enabled": True,
            "auto_detect": True,
            "preferred_type": "auto",
            "fallback_to_numpy": True
        }
    }
    
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            logger.info(f"已加载SIMD配置: {config_path}")
            return config
        else:
            logger.warning(f"找不到SIMD配置文件: {config_path}，使用默认配置")
            return default_config
    except Exception as e:
        logger.error(f"加载SIMD配置失败: {str(e)}，使用默认配置")
        return default_config

class SimdOperations:
    """SIMD优化的矩阵和向量操作"""
    
    def __init__(self, simd_type: str = "auto"):
        """
        初始化SIMD操作
        
        Args:
            simd_type: SIMD指令集类型 ("avx512", "avx2", "avx", "sse4.2", "neon", "baseline" 或 "auto")
        """
        self.simd_type = simd_type
        self.simd_lib = None
        self.simd_lib_loaded = False
        
        # 加载配置
        self.config = load_simd_config()
        
        # 检查是否启用SIMD优化
        if not self.config["simd_optimization"]["enabled"]:
            logger.info("SIMD优化已在配置中禁用")
            self.simd_lib_loaded = False
            self.simd_type = "baseline"
            return
        
        # 使用配置中的首选类型（如果未指定）
        if simd_type == "auto" and self.config["simd_optimization"]["preferred_type"] != "auto":
            self.simd_type = self.config["simd_optimization"]["preferred_type"]
        
        # 尝试加载SIMD库
        self._load_simd_lib()
        
        # 如果设置为自动检测，则确定最佳SIMD类型
        if self.simd_type == "auto":
            self.simd_type = self._detect_best_simd_type()
        
        # 内存对齐配置
        self.memory_alignment = get_alignment_for_simd(self.simd_type) if HAS_MEMORY_ALIGNMENT else 16
        
    def _load_simd_lib(self):
        """尝试加载SIMD库"""
        try:
            if _check_simd_lib_exists():
                self.simd_lib = ctypes.CDLL(SIMD_LIB_PATH)
                
                # 设置函数参数和返回类型
                self._setup_function_signatures()
                
                self.simd_lib_loaded = True
                logger.info(f"已加载SIMD库: {SIMD_LIB_PATH}")
            else:
                # 使用mock实现 (纯Python)
                logger.warning(f"找不到SIMD库: {SIMD_LIB_PATH}，将使用Python实现")
                self.simd_lib_loaded = False
        except Exception as e:
            logger.error(f"加载SIMD库失败: {str(e)}")
            self.simd_lib_loaded = False
    
    def _setup_function_signatures(self):
        """设置库函数参数和返回类型"""
        if not self.simd_lib_loaded or not self.simd_lib:
            return
            
        try:
            # 设置dispatch_matrix_multiply函数签名
            self.simd_lib.dispatch_matrix_multiply.argtypes = [
                ctypes.POINTER(ctypes.c_float),
                ctypes.POINTER(ctypes.c_float),
                ctypes.POINTER(ctypes.c_float),
                ctypes.c_int,
                ctypes.c_int,
                ctypes.c_int,
                ctypes.c_char_p
            ]
            self.simd_lib.dispatch_matrix_multiply.restype = None
            
            # 基准实现（永远可用）
            self.simd_lib.matrix_mult_baseline.argtypes = [
                ctypes.POINTER(ctypes.c_float),
                ctypes.POINTER(ctypes.c_float),
                ctypes.POINTER(ctypes.c_float),
                ctypes.c_int
            ]
            self.simd_lib.matrix_mult_baseline.restype = None
            
            self.simd_lib.matrix_add_baseline.argtypes = [
                ctypes.POINTER(ctypes.c_float),
                ctypes.POINTER(ctypes.c_float),
                ctypes.POINTER(ctypes.c_float),
                ctypes.c_int
            ]
            self.simd_lib.matrix_add_baseline.restype = None
            
            self.simd_lib.vector_scale_baseline.argtypes = [
                ctypes.POINTER(ctypes.c_float),
                ctypes.c_float,
                ctypes.c_int
            ]
            self.simd_lib.vector_scale_baseline.restype = None
            
            self.simd_lib.fma_baseline.argtypes = [
                ctypes.POINTER(ctypes.c_float),
                ctypes.POINTER(ctypes.c_float),
                ctypes.POINTER(ctypes.c_float),
                ctypes.POINTER(ctypes.c_float),
                ctypes.c_int
            ]
            self.simd_lib.fma_baseline.restype = None
            
        except Exception as e:
            logger.error(f"设置函数签名失败: {str(e)}")
            self.simd_lib_loaded = False
    
    def _detect_best_simd_type(self) -> str:
        """
        检测当前系统最佳的SIMD指令集
        
        Returns:
            str: 最佳SIMD类型
        """
        # 尝试从指令集路由器获取
        try:
            from src.hardware.optimization_router import select_optimization_path
            opt_path = select_optimization_path()
            
            # 将路由器路径转换为我们的格式
            path_mapping = {
                'avx512': 'avx512',
                'avx2': 'avx2',
                'avx': 'avx', 
                'sse4.2': 'sse4.2',
                'neon': 'neon',
                'baseline': 'baseline'
            }
            
            return path_mapping.get(opt_path, 'baseline')
        except ImportError:
            pass
        
        # 根据平台检测
        if platform.machine().startswith(('arm', 'aarch')):
            # ARM平台检测NEON
            return 'neon' if self._check_arm_neon() else 'baseline'
        else:
            # x86平台检测
            if self._check_avx512():
                return 'avx512'
            elif self._check_avx2():
                return 'avx2'
            elif self._check_avx():
                return 'avx'
            elif self._check_sse42():
                return 'sse4.2'
            else:
                return 'baseline'
    
    def _check_avx512(self) -> bool:
        """检查是否支持AVX-512"""
        # CPU 特性检测
        if platform.system() == "Windows":
            # Windows平台没有简单的方法检测，使用try-except尝试
            return False  # 需要更复杂的检测方法
        elif platform.system() == "Linux":
            try:
                with open('/proc/cpuinfo', 'r') as f:
                    cpuinfo = f.read()
                return 'avx512f' in cpuinfo
            except:
                return False
        else:
            return False
    
    def _check_avx2(self) -> bool:
        """检查是否支持AVX2"""
        if platform.system() == "Windows":
            # 使用Python尝试
            try:
                import numpy as np
                return hasattr(np, '__AVX2__')
            except:
                return False
        elif platform.system() == "Linux":
            try:
                with open('/proc/cpuinfo', 'r') as f:
                    cpuinfo = f.read()
                return 'avx2' in cpuinfo
            except:
                return False
        else:
            return False
    
    def _check_avx(self) -> bool:
        """检查是否支持AVX"""
        if platform.system() == "Linux":
            try:
                with open('/proc/cpuinfo', 'r') as f:
                    cpuinfo = f.read()
                return 'avx' in cpuinfo
            except:
                return False
        else:
            # 默认为False
            return False
            
    def _check_sse42(self) -> bool:
        """检查是否支持SSE4.2"""
        if platform.system() == "Linux":
            try:
                with open('/proc/cpuinfo', 'r') as f:
                    cpuinfo = f.read()
                return 'sse4_2' in cpuinfo
            except:
                return False
        else:
            # 默认为False
            return False
    
    def _check_arm_neon(self) -> bool:
        """检查是否支持ARM NEON"""
        if platform.machine().startswith(('arm', 'aarch')):
            return True  # 大多数现代ARM处理器都支持NEON
        return False
    
    def _validate_arrays(self, *arrays):
        """验证所有输入数组是否为连续的float32数组"""
        for arr in arrays:
            if not isinstance(arr, np.ndarray):
                raise TypeError("输入必须是NumPy数组")
            if arr.dtype != np.float32:
                raise TypeError("输入数组必须是float32类型")
            if not arr.flags.c_contiguous:
                raise ValueError("输入数组必须是内存连续的")
    
    def _ensure_aligned(self, array: np.ndarray) -> np.ndarray:
        """
        确保数组内存对齐以获得最佳SIMD性能
        
        Args:
            array: 输入数组
            
        Returns:
            np.ndarray: 对齐的数组
        """
        if not HAS_MEMORY_ALIGNMENT:
            return array
            
        # 只有在需要时才进行对齐操作
        if not is_aligned(array, self.memory_alignment):
            return align_array(array, self.memory_alignment)
        return array
    
    def matrix_multiply(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        """
        矩阵乘法 C = A × B，使用SIMD优化
        
        Args:
            a: 矩阵A（2D数组）
            b: 矩阵B（2D数组）
            
        Returns:
            矩阵乘法结果C
        """
        # 进行内存对齐以获得最佳性能
        a_aligned = self._ensure_aligned(a)
        b_aligned = self._ensure_aligned(b)
        
        try:
            if self.simd_lib_loaded and self.simd_lib:
                # 获取数组指针
                a_ptr = a_aligned.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
                b_ptr = b_aligned.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
                c_ptr = np.zeros_like(a_aligned, dtype=np.float32).ctypes.data_as(ctypes.POINTER(ctypes.c_float))
                
                # 调用库函数
                simd_type_bytes = self.simd_type.encode('utf-8')
                self.simd_lib.dispatch_matrix_multiply(
                    a_ptr, b_ptr, c_ptr,
                    a_aligned.shape[0], a_aligned.shape[1], b_aligned.shape[1],
                    simd_type_bytes
                )
                return np.ctypeslib.as_array(c_ptr).reshape(a_aligned.shape[0], b_aligned.shape[1])
        except Exception as e:
            logger.warning(f"SIMD矩阵乘法失败: {str(e)}，回退到NumPy")
        
        # 回退到NumPy
        return np.matmul(a_aligned, b_aligned)
    
    def matrix_element_multiply(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        """
        矩阵元素点乘 (Hadamard积)
        
        Args:
            a: 矩阵A
            b: 矩阵B（与A形状相同）
            
        Returns:
            结果矩阵C，C[i,j] = A[i,j] * B[i,j]
        """
        # 进行内存对齐以获得最佳性能
        a_aligned = self._ensure_aligned(a)
        b_aligned = self._ensure_aligned(b)
        
        try:
            if self.simd_lib_loaded and self.simd_lib:
                # 将数组展平为1D
                a_flat = a_aligned.flatten()
                b_flat = b_aligned.flatten()
                c_flat = np.zeros_like(a_flat, dtype=np.float32)
                n = a_flat.size
                
                # 获取数组指针
                a_ptr = a_flat.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
                b_ptr = b_flat.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
                c_ptr = c_flat.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
                
                # 调用基准函数（即使没有对应SIMD实现）
                self.simd_lib.matrix_mult_baseline(a_ptr, b_ptr, c_ptr, n)
                return c_flat.reshape(a_aligned.shape)
        except Exception as e:
            logger.warning(f"SIMD元素乘法失败: {str(e)}，回退到NumPy")
        
        # 回退到NumPy
        return a_aligned * b_aligned
    
    def matrix_add(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        """
        矩阵元素加法
        
        Args:
            a: 矩阵A
            b: 矩阵B（与A形状相同）
            
        Returns:
            结果矩阵C，C[i,j] = A[i,j] + B[i,j]
        """
        # 进行内存对齐以获得最佳性能
        a_aligned = self._ensure_aligned(a)
        b_aligned = self._ensure_aligned(b)
        
        try:
            if self.simd_lib_loaded and self.simd_lib:
                # 将数组展平为1D
                a_flat = a_aligned.flatten()
                b_flat = b_aligned.flatten()
                c_flat = np.zeros_like(a_flat, dtype=np.float32)
                n = a_flat.size
                
                # 获取数组指针
                a_ptr = a_flat.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
                b_ptr = b_flat.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
                c_ptr = c_flat.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
                
                # 调用基准函数（即使没有对应SIMD实现）
                self.simd_lib.matrix_add_baseline(a_ptr, b_ptr, c_ptr, n)
                return c_flat.reshape(a_aligned.shape)
        except Exception as e:
            logger.warning(f"SIMD矩阵加法失败: {str(e)}，回退到NumPy")
        
        # 回退到NumPy
        return a_aligned + b_aligned
    
    def vector_scale(self, vec: np.ndarray, scalar: float) -> np.ndarray:
        """
        向量缩放操作 vec = vec * scalar
        
        Args:
            vec: 输入向量
            scalar: 缩放因子
            
        Returns:
            缩放后的向量
        """
        # 进行内存对齐以获得最佳性能
        vec_aligned = self._ensure_aligned(vec)
        
        try:
            if self.simd_lib_loaded and self.simd_lib:
                # 将数组展平为1D
                vec_flat = vec_aligned.flatten()
                n = vec_flat.size
                
                # 获取数组指针
                vec_ptr = vec_flat.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
                
                # 创建结果数组（复制原数组）
                result = vec_flat.copy()
                
                # 调用基准函数
                self.simd_lib.vector_scale_baseline(vec_ptr, scalar, n)
                return result.reshape(vec_aligned.shape)
        except Exception as e:
            logger.warning(f"SIMD向量缩放失败: {str(e)}，回退到NumPy")
        
        # 回退到NumPy
        return vec_aligned * scalar
    
    def fused_multiply_add(self, a: np.ndarray, b: np.ndarray, c: np.ndarray) -> np.ndarray:
        """
        融合乘加操作 (Fused Multiply-Add)
        result = a * b + c
        
        Args:
            a: 数组A
            b: 数组B（与A形状相同）
            c: 数组C（与A形状相同）
            
        Returns:
            结果数组 result = a * b + c
        """
        # 进行内存对齐以获得最佳性能
        a_aligned = self._ensure_aligned(a)
        b_aligned = self._ensure_aligned(b)
        c_aligned = self._ensure_aligned(c)
        
        try:
            if self.simd_lib_loaded and self.simd_lib:
                # 将数组展平为1D
                a_flat = a_aligned.flatten()
                b_flat = b_aligned.flatten()
                c_flat = c_aligned.flatten()
                result_flat = np.zeros_like(a_flat, dtype=np.float32)
                n = a_flat.size
                
                # 获取数组指针
                a_ptr = a_flat.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
                b_ptr = b_flat.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
                c_ptr = c_flat.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
                result_ptr = result_flat.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
                
                # 调用基准函数
                self.simd_lib.fma_baseline(a_ptr, b_ptr, c_ptr, result_ptr, n)
                return result_flat.reshape(a_aligned.shape)
        except Exception as e:
            logger.warning(f"SIMD融合乘加失败: {str(e)}，回退到NumPy")
        
        # 回退到NumPy
        return a_aligned * b_aligned + c_aligned
    
    def get_performance_stats(self) -> Dict:
        """
        获取性能统计信息
        
        Returns:
            Dict: 性能统计信息
        """
        stats = {
            "simd_type": self.simd_type,
            "simd_lib_loaded": self.simd_lib_loaded,
            "simd_lib_path": SIMD_LIB_PATH if self.simd_lib_loaded else None,
            "memory_alignment": self.memory_alignment,
            "has_memory_alignment": HAS_MEMORY_ALIGNMENT
        }
        
        # 进行性能测试
        stats.update(self._run_performance_test())
        
        return stats
    
    def _run_performance_test(self) -> Dict:
        """
        运行简单的性能测试
        
        Returns:
            Dict: 测试结果
        """
        # 创建测试矩阵
        size = 1000
        a = np.random.rand(size, size).astype(np.float32)
        b = np.random.rand(size, size).astype(np.float32)
        
        # 测试矩阵乘法性能
        start_time = time.time()
        c_numpy = np.matmul(a, b)
        numpy_time = time.time() - start_time
        
        # 测试SIMD实现性能
        start_time = time.time()
        c_simd = self.matrix_multiply(a, b)
        simd_time = time.time() - start_time
        
        # 验证结果正确性
        is_correct = np.allclose(c_numpy, c_simd, rtol=1e-5, atol=1e-5)
        
        # 计算性能提升
        if numpy_time > 0:
            speedup = numpy_time / simd_time
        else:
            speedup = 0.0
        
        return {
            "matrix_size": size,
            "numpy_time": numpy_time,
            "simd_time": simd_time,
            "speedup": speedup,
            "is_correct": is_correct
        }

    def get_info(self) -> Dict:
        """
        获取SIMD操作信息
        
        Returns:
            Dict: 包含SIMD详细信息的字典
        """
        return {
            'simd_type': self.simd_type,
            'is_native': self.simd_lib_loaded,
            'features': self._get_supported_operations(),
            'memory_alignment': self.memory_alignment,
            'has_memory_alignment': HAS_MEMORY_ALIGNMENT
        }

def get_simd_operations(simd_type: str = "auto") -> SimdOperations:
    """
    获取SIMD操作实例
    
    Args:
        simd_type: SIMD指令集类型，默认为自动检测
        
    Returns:
        SimdOperations: SIMD操作实例
    """
    return SimdOperations(simd_type)

if __name__ == "__main__":
    # 设置日志级别
    logging.basicConfig(level=logging.INFO, 
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # 创建SIMD操作实例
    simd_ops = get_simd_operations()
    
    # 显示检测到的SIMD类型
    print(f"检测到的SIMD类型: {simd_ops.simd_type}")
    print(f"SIMD库已加载: {simd_ops.simd_lib_loaded}")
    
    # 简单测试
    a = np.random.rand(1000, 1000).astype(np.float32)
    b = np.random.rand(1000, 1000).astype(np.float32)
    
    print("\n测试矩阵乘法性能...")
    start_time = time.time()
    c_numpy = np.matmul(a, b)
    numpy_time = time.time() - start_time
    print(f"NumPy时间: {numpy_time:.4f}秒")
    
    start_time = time.time()
    c_simd = simd_ops.matrix_multiply(a, b)
    simd_time = time.time() - start_time
    print(f"SIMD时间: {simd_time:.4f}秒")
    
    # 验证结果正确性
    is_close = np.allclose(c_numpy, c_simd, rtol=1e-5, atol=1e-5)
    print(f"结果正确: {is_close}")
    
    if numpy_time > 0:
        speedup = numpy_time / simd_time
        print(f"加速比: {speedup:.2f}x")
        
    # 获取性能统计信息
    stats = simd_ops.get_performance_stats()
    print("\n性能统计信息:")
    for key, value in stats.items():
        print(f"  {key}: {value}") 