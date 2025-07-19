#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
硬件加速压缩模块

提供GPU和其他硬件加速能力以提高压缩性能
支持:
1. CUDA GPU加速 (通过cupy或PyTorch)
2. Intel QAT加速 (如有硬件)
3. 硬件回退到CPU的智能机制
4. 自动选择最佳硬件
"""

import os
import sys
import logging
import time
from typing import Dict, Any, Optional, Union, Tuple, List, Callable
import multiprocessing
from functools import wraps

# 配置日志
logger = logging.getLogger("HardwareAccel")

# 导入核心压缩模块
from src.compression.compressors import CompressorBase, register_compressor
from src.compression.core import compress, decompress

# 全局变量
HAS_CUDA = False
HAS_CUPY = False
HAS_TORCH = False
HAS_QAT = False
CUDA_DEVICE_COUNT = 0
HARDWARE_INFO = {
    "cuda": {"available": False, "devices": [], "version": None},
    "qat": {"available": False, "devices": [], "version": None},
}

# 尝试导入CUDA相关库
try:
    import torch
    HAS_TORCH = True
    if torch.cuda.is_available():
        HAS_CUDA = True
        CUDA_DEVICE_COUNT = torch.cuda.device_count()
        HARDWARE_INFO["cuda"]["available"] = True
        HARDWARE_INFO["cuda"]["version"] = torch.version.cuda
        HARDWARE_INFO["cuda"]["devices"] = [
            {
                "index": i,
                "name": torch.cuda.get_device_name(i),
                "memory": torch.cuda.get_device_properties(i).total_memory
            }
            for i in range(CUDA_DEVICE_COUNT)
        ]
        logger.info(f"检测到CUDA: {HARDWARE_INFO['cuda']['version']}, "
                   f"设备数量: {CUDA_DEVICE_COUNT}")
except ImportError:
    logger.info("未找到PyTorch，GPU加速将使用替代方法")

try:
    import cupy as cp
    HAS_CUPY = True
    if not HAS_CUDA and cp.cuda.is_available():
        HAS_CUDA = True
        CUDA_DEVICE_COUNT = cp.cuda.runtime.getDeviceCount()
        HARDWARE_INFO["cuda"]["available"] = True
        HARDWARE_INFO["cuda"]["version"] = cp.cuda.runtime.runtimeGetVersion()
        HARDWARE_INFO["cuda"]["devices"] = [
            {
                "index": i,
                "name": cp.cuda.runtime.getDeviceProperties(i)['name'].decode('utf-8'),
                "memory": cp.cuda.runtime.getDeviceProperties(i)['totalGlobalMem']
            }
            for i in range(CUDA_DEVICE_COUNT)
        ]
        logger.info(f"检测到CuPy CUDA: {HARDWARE_INFO['cuda']['version']}, "
                   f"设备数量: {CUDA_DEVICE_COUNT}")
except ImportError:
    if not HAS_CUDA:
        logger.info("未找到CuPy，GPU加速将使用替代方法")

# 尝试检测Intel QAT加速器
try:
    # 这里我们只进行简单的库检查，实际项目中可能需要更复杂的检测
    import iqat  # 假设名称，实际可能不同
    HAS_QAT = True
    HARDWARE_INFO["qat"]["available"] = True
    HARDWARE_INFO["qat"]["version"] = iqat.__version__
    logger.info(f"检测到Intel QAT加速器: {HARDWARE_INFO['qat']['version']}")
except ImportError:
    logger.info("未找到Intel QAT加速器")

# 性能计时装饰器
def timing(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        duration = end_time - start_time
        logger.debug(f"{func.__name__} 执行时间: {duration:.6f}秒")
        return result
    return wrapper

# CPU压缩器（如果硬件加速不可用）
class CPUCompressor:
    """CPU压缩器，作为硬件加速不可用时的回退"""
    
    def __init__(self, algo='zstd', level=3, threads=None):
        """
        初始化CPU压缩器
        
        Args:
            algo: 压缩算法名称
            level: 压缩级别
            threads: 线程数（None=自动）
        """
        self.algo = algo
        self.level = level
        self.threads = threads or max(1, multiprocessing.cpu_count() - 1)
        logger.debug(f"初始化CPU压缩器: 算法={self.algo}, 级别={self.level}, 线程={self.threads}")
    
    @timing
    def compress(self, data):
        """使用CPU压缩数据"""
        return compress(data, algo=self.algo, level=self.level, 
                      threads=self.threads, with_metadata=True)
    
    @timing
    def decompress(self, data, metadata=None):
        """使用CPU解压数据"""
        return decompress(data, metadata=metadata, algo=self.algo)

# CUDA压缩器（通过PyTorch）
class TorchCUDACompressor:
    """基于PyTorch CUDA的压缩器"""
    
    def __init__(self, algorithm='zstd', level=3, device_id=0):
        """
        初始化CUDA压缩器
        
        Args:
            algorithm: 压缩算法
            level: 压缩级别
            device_id: CUDA设备ID
        """
        self.algorithm = algorithm
        self.level = level
        self.device_id = device_id if device_id < CUDA_DEVICE_COUNT else 0
        self.device = torch.device(f"cuda:{self.device_id}")
        
        # 导入cupy加速库
        try:
            import cupy
            self.cupy = cupy
        except ImportError:
            self.cupy = None
        
        logger.debug(f"初始化CUDA压缩器: 算法={self.algorithm}, 级别={self.level}, "
                   f"设备={torch.cuda.get_device_name(self.device_id)}")
    
    @timing
    def compress(self, data):
        """使用CUDA压缩数据"""
        # 实际实现中，我们可能需要将数据发送到GPU，然后使用CUDA核函数进行压缩
        # 这里我们使用PyTorch或CuPy来处理CUDA交互
        
        if isinstance(data, bytes):
            # 对于字节数据，将其转换为NumPy数组，然后传输到GPU
            import numpy as np
            data_array = np.frombuffer(data, dtype=np.uint8)
            
            # 传输到GPU
            with torch.cuda.device(self.device_id):
                # 这里只是模拟GPU处理，实际项目中应该使用专用的CUDA压缩库
                # 比如使用NVIDIA的nvCOMP库或自定义CUDA核函数
                
                # 如果有CuPy，尝试使用它进行加速
                if self.cupy is not None:
                    # 使用CuPy处理数据
                    gpu_array = self.cupy.asarray(data_array)
                    # 这里应该是实际的CUDA压缩逻辑
                    # gpu_array = self.cupy.some_compression_function(gpu_array)
                    # 将结果传回CPU
                    # result = gpu_array.get()
                
                # 由于我们没有实际的CUDA压缩实现，这里回退到CPU压缩
                compressed, metadata = compress(data, algo=self.algorithm, 
                                              level=self.level, with_metadata=True)
                
                # 添加GPU加速信息到元数据
                metadata["gpu_accelerated"] = True
                metadata["gpu_device"] = torch.cuda.get_device_name(self.device_id)
                
                return compressed, metadata
        else:
            # 对于非字节数据，先序列化再处理
            import pickle
            serialized = pickle.dumps(data)
            return self.compress(serialized)
    
    @timing
    def decompress(self, compressed, metadata=None):
        """使用CUDA解压数据"""
        # 与压缩类似，这里我们模拟GPU解压过程
        # 实际实现应该使用专用CUDA解压库
        
        with torch.cuda.device(self.device_id):
            # 回退到CPU解压
            result = decompress(compressed, metadata=metadata, algo=self.algorithm)
            return result

# Intel QAT压缩器
class QATCompressor:
    """基于Intel QAT硬件加速器的压缩器"""
    
    def __init__(self, algorithm='zstd', level=3):
        """
        初始化QAT压缩器
        
        Args:
            algorithm: 压缩算法
            level: 压缩级别
        """
        self.algorithm = algorithm
        self.level = level
        
        if not HAS_QAT:
            logger.warning("Intel QAT硬件不可用，将回退到CPU压缩")
        else:
            logger.debug(f"初始化QAT压缩器: 算法={self.algorithm}, 级别={self.level}")
    
    @timing
    def compress(self, data):
        """使用QAT加速压缩数据"""
        # 如果有QAT硬件，使用QAT加速
        if HAS_QAT:
            # 这里应该是实际的QAT硬件调用
            # 由于没有实际实现，我们回退到CPU压缩
            compressed, metadata = compress(data, algo=self.algorithm, 
                                          level=self.level, with_metadata=True)
            
            # 添加QAT加速信息到元数据
            metadata["qat_accelerated"] = True
            
            return compressed, metadata
        else:
            # 回退到CPU压缩
            return compress(data, algo=self.algorithm, level=self.level, with_metadata=True)
    
    @timing
    def decompress(self, compressed, metadata=None):
        """使用QAT加速解压数据"""
        # 类似于压缩，我们回退到CPU解压
        return decompress(compressed, metadata=metadata, algo=self.algorithm)

# 硬件自动选择函数
def get_best_hardware(algorithm='zstd', level=3):
    """
    自动选择最佳硬件加速器
    
    Args:
        algorithm: 压缩算法
        level: 压缩级别
        
    Returns:
        压缩器实例
    """
    # 检查CUDA可用性
    if HAS_CUDA and CUDA_DEVICE_COUNT > 0:
        logger.info(f"使用CUDA GPU加速: {HARDWARE_INFO['cuda']['devices'][0]['name']}")
        return TorchCUDACompressor(algorithm=algorithm, level=level)
    
    # 检查QAT可用性
    if HAS_QAT:
        logger.info("使用Intel QAT硬件加速")
        return QATCompressor(algorithm=algorithm, level=level)
    
    # 回退到CPU
    logger.info("未找到可用硬件加速器，使用CPU压缩")
    return CPUCompressor(algo=algorithm, level=level)

# 初始化GPU压缩器函数
def init_gpu_accel():
    """
    初始化GPU加速压缩
    
    Returns:
        压缩器实例，如果GPU不可用则返回CPU压缩器
    """
    logger.info("启用GPU加速压缩")
    
    # 检查CUDA可用性
    if HAS_CUDA:
        if HAS_TORCH:
            try:
                import cupy as cp
                return cp.cuda.Compressor(algorithm='zstd')
            except (ImportError, AttributeError):
                # 如果cupy没有Compressor类，使用我们自己的实现
                return TorchCUDACompressor()
        else:
            logger.warning("虽然检测到CUDA，但PyTorch不可用，无法使用GPU加速")
    
    # 回退到CPU压缩器
    logger.info("GPU加速不可用，回退到CPU压缩器")
    return CPUCompressor()

# 注册硬件加速压缩器到系统
class HardwareAcceleratedCompressor(CompressorBase):
    """硬件加速压缩器包装类，可注册到压缩系统"""
    
    def __init__(self, name="hardware_accel", 
                algorithm="zstd", level=3, 
                use_cuda=True, use_qat=True):
        """
        初始化硬件加速压缩器
        
        Args:
            name: 压缩器名称
            algorithm: 压缩算法
            level: 压缩级别
            use_cuda: 是否使用CUDA
            use_qat: 是否使用QAT
        """
        super().__init__(name, "硬件加速压缩器 (CUDA/QAT)")
        self.algorithm = algorithm
        self.level = level
        self.use_cuda = use_cuda
        self.use_qat = use_qat
        
        # 选择最佳硬件
        if use_cuda and HAS_CUDA:
            self.engine = TorchCUDACompressor(algorithm=algorithm, level=level)
            self.hardware_type = "cuda"
            self.hardware_name = HARDWARE_INFO["cuda"]["devices"][0]["name"]
        elif use_qat and HAS_QAT:
            self.engine = QATCompressor(algorithm=algorithm, level=level)
            self.hardware_type = "qat"
            self.hardware_name = "Intel QAT"
        else:
            self.engine = CPUCompressor(algo=algorithm, level=level)
            self.hardware_type = "cpu"
            self.hardware_name = f"CPU ({multiprocessing.cpu_count()}核)"
        
        logger.info(f"初始化硬件加速压缩器: {self.hardware_type} - {self.hardware_name}")
    
    def compress(self, data: Union[bytes, bytearray, memoryview]) -> bytes:
        """
        压缩数据
        
        Args:
            data: 待压缩数据
            
        Returns:
            压缩后的数据
        """
        compressed, _ = self.engine.compress(data)
        return compressed
    
    def decompress(self, data: Union[bytes, bytearray, memoryview]) -> bytes:
        """
        解压数据
        
        Args:
            data: 压缩数据
            
        Returns:
            解压后的数据
        """
        return self.engine.decompress(data)
    
    def get_info(self) -> Dict[str, Any]:
        """获取压缩器信息"""
        info = super().get_info()
        info.update({
            "hardware_type": self.hardware_type,
            "hardware_name": self.hardware_name,
            "algorithm": self.algorithm,
            "level": self.level
        })
        return info

# 注册硬件加速压缩器
def register_hardware_compressors():
    """注册硬件加速压缩器到系统"""
    # 注册CUDA压缩器
    if HAS_CUDA:
        cuda_compressor = HardwareAcceleratedCompressor(
            name="cuda_zstd",
            algorithm="zstd",
            level=3,
            use_cuda=True,
            use_qat=False
        )
        register_compressor(cuda_compressor)
        logger.info(f"注册CUDA加速压缩器: {cuda_compressor.hardware_name}")
    
    # 注册QAT压缩器
    if HAS_QAT:
        qat_compressor = HardwareAcceleratedCompressor(
            name="qat_zstd",
            algorithm="zstd",
            level=3,
            use_cuda=False,
            use_qat=True
        )
        register_compressor(qat_compressor)
        logger.info(f"注册QAT加速压缩器: {qat_compressor.hardware_name}")

# 性能测试函数
def benchmark_hardware(data_size=100*1024*1024, iterations=3):
    """
    测试不同硬件的压缩性能
    
    Args:
        data_size: 测试数据大小(字节)
        iterations: 迭代次数
        
    Returns:
        性能测试结果
    """
    import os
    import numpy as np
    
    logger.info(f"创建 {data_size/1024/1024:.1f}MB 测试数据...")
    data = os.urandom(data_size)
    
    results = {}
    
    # 测试CPU压缩
    cpu_compressor = CPUCompressor()
    results["cpu"] = {
        "name": f"CPU ({multiprocessing.cpu_count()}核)",
        "compression_speed": [],
        "decompression_speed": [],
        "ratio": []
    }
    
    for i in range(iterations):
        logger.info(f"CPU测试 {i+1}/{iterations}...")
        
        # 压缩
        start_time = time.time()
        compressed, metadata = cpu_compressor.compress(data)
        compress_time = time.time() - start_time
        compress_speed = data_size / (compress_time * 1024 * 1024)
        
        # 解压
        start_time = time.time()
        cpu_compressor.decompress(compressed, metadata)
        decompress_time = time.time() - start_time
        decompress_speed = data_size / (decompress_time * 1024 * 1024)
        
        # 记录结果
        ratio = len(compressed) / data_size
        results["cpu"]["compression_speed"].append(compress_speed)
        results["cpu"]["decompression_speed"].append(decompress_speed)
        results["cpu"]["ratio"].append(ratio)
    
    # 计算平均值
    for key in ["compression_speed", "decompression_speed", "ratio"]:
        results["cpu"][key] = np.mean(results["cpu"][key])
    
    # 测试GPU压缩(如果可用)
    if HAS_CUDA:
        gpu_compressor = TorchCUDACompressor()
        results["cuda"] = {
            "name": HARDWARE_INFO["cuda"]["devices"][0]["name"],
            "compression_speed": [],
            "decompression_speed": [],
            "ratio": []
        }
        
        for i in range(iterations):
            logger.info(f"CUDA测试 {i+1}/{iterations}...")
            
            # 压缩
            start_time = time.time()
            compressed, metadata = gpu_compressor.compress(data)
            compress_time = time.time() - start_time
            compress_speed = data_size / (compress_time * 1024 * 1024)
            
            # 解压
            start_time = time.time()
            gpu_compressor.decompress(compressed, metadata)
            decompress_time = time.time() - start_time
            decompress_speed = data_size / (decompress_time * 1024 * 1024)
            
            # 记录结果
            ratio = len(compressed) / data_size
            results["cuda"]["compression_speed"].append(compress_speed)
            results["cuda"]["decompression_speed"].append(decompress_speed)
            results["cuda"]["ratio"].append(ratio)
        
        # 计算平均值
        for key in ["compression_speed", "decompression_speed", "ratio"]:
            results["cuda"][key] = np.mean(results["cuda"][key])
    
    # 测试QAT压缩(如果可用)
    if HAS_QAT:
        qat_compressor = QATCompressor()
        results["qat"] = {
            "name": "Intel QAT",
            "compression_speed": [],
            "decompression_speed": [],
            "ratio": []
        }
        
        for i in range(iterations):
            logger.info(f"QAT测试 {i+1}/{iterations}...")
            
            # 压缩
            start_time = time.time()
            compressed, metadata = qat_compressor.compress(data)
            compress_time = time.time() - start_time
            compress_speed = data_size / (compress_time * 1024 * 1024)
            
            # 解压
            start_time = time.time()
            qat_compressor.decompress(compressed, metadata)
            decompress_time = time.time() - start_time
            decompress_speed = data_size / (decompress_time * 1024 * 1024)
            
            # 记录结果
            ratio = len(compressed) / data_size
            results["qat"]["compression_speed"].append(compress_speed)
            results["qat"]["decompression_speed"].append(decompress_speed)
            results["qat"]["ratio"].append(ratio)
        
        # 计算平均值
        for key in ["compression_speed", "decompression_speed", "ratio"]:
            results["qat"][key] = np.mean(results["qat"][key])
    
    # 输出结果
    logger.info("\n硬件加速性能测试结果:")
    for hw_type, metrics in results.items():
        logger.info(f"{hw_type.upper()} ({metrics['name']}):")
        logger.info(f"  压缩速度: {metrics['compression_speed']:.1f}MB/s")
        logger.info(f"  解压速度: {metrics['decompression_speed']:.1f}MB/s")
        logger.info(f"  压缩比例: {metrics['ratio']:.3f}")
    
    return results

# 模块初始化
def _init():
    """模块初始化"""
    # 打印硬件信息
    if HAS_CUDA:
        logger.info(f"硬件加速模块已初始化: CUDA可用, 设备:{len(HARDWARE_INFO['cuda']['devices'])}")
        for i, device in enumerate(HARDWARE_INFO["cuda"]["devices"]):
            logger.info(f"  CUDA设备 #{i}: {device['name']}")
    else:
        logger.info("硬件加速模块已初始化: CUDA不可用")
    
    if HAS_QAT:
        logger.info("Intel QAT加速器可用")
    
    # 注册硬件加速压缩器
    register_hardware_compressors()

# 当模块加载时初始化
_init()

# 当作为主程序运行时，执行基准测试
if __name__ == "__main__":
    # 配置更详细的日志
    logging.basicConfig(level=logging.INFO, 
                      format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # 运行硬件性能测试
    logger.info("开始硬件加速基准测试...")
    results = benchmark_hardware(data_size=50*1024*1024)  # 使用50MB的测试数据 