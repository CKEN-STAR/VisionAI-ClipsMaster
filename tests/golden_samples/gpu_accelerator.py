#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GPU硬件加速模块

该模块提供基于GPU的硬件加速功能，用于优化视频处理和比较操作的性能。
支持多种GPU后端，包括CUDA、OpenCL和ROCm，根据系统可用的硬件自动选择最佳后端。
"""

import os
import sys
import logging
import numpy as np
from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional, Union

# 获取项目根目录
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

# 配置日志
logger = logging.getLogger("hardware_accel")

# 全局配置
USE_GPU = True  # 是否启用GPU加速
GPU_MEMORY_LIMIT = 0.8  # GPU内存使用限制（占总内存的比例）
PREFERRED_BACKEND = "auto"  # 首选后端，可选值：auto、cuda、opencl、rocm

# 支持的后端
BACKENDS = {
    "cuda": False,
    "opencl": False,
    "rocm": False
}

# 尝试导入CUDA (OpenCV)
try:
    import cv2
    cuda_available = cv2.cuda.getCudaEnabledDeviceCount() > 0
    if cuda_available:
        BACKENDS["cuda"] = True
        logger.info("CUDA后端可用 (OpenCV)")
except Exception as e:
    logger.warning(f"OpenCV CUDA不可用: {str(e)}")

# 尝试导入CuPy
try:
    import cupy as cp
    BACKENDS["cuda"] = True
    logger.info("CUDA后端可用 (CuPy)")
except ImportError:
    logger.warning("CuPy未安装，部分CUDA功能将使用替代方法")

# 尝试导入OpenCL
try:
    import pyopencl as cl
    platforms = cl.get_platforms()
    if platforms:
        BACKENDS["opencl"] = True
        logger.info(f"OpenCL后端可用: {len(platforms)} 个平台")
except ImportError:
    logger.warning("PyOpenCL未安装，OpenCL功能不可用")

# 尝试导入ROCm (AMD)
try:
    import rocm
    BACKENDS["rocm"] = True
    logger.info("ROCm后端可用")
except ImportError:
    logger.debug("ROCm未安装，AMD GPU加速不可用")

# 确定最佳后端
ACTIVE_BACKEND = None
if USE_GPU:
    if PREFERRED_BACKEND == "auto":
        # 按优先级顺序选择后端
        for backend in ["cuda", "opencl", "rocm"]:
            if BACKENDS[backend]:
                ACTIVE_BACKEND = backend
                break
    else:
        # 使用指定后端，如果可用
        if BACKENDS.get(PREFERRED_BACKEND, False):
            ACTIVE_BACKEND = PREFERRED_BACKEND

if ACTIVE_BACKEND:
    logger.info(f"已启用硬件加速，使用 {ACTIVE_BACKEND} 后端")
else:
    logger.warning("未找到可用的GPU加速后端，将使用CPU模式")

class VideoComparatorGPU:
    """GPU加速的视频比较器"""
    
    def __init__(self):
        """初始化比较器"""
        self.backend = ACTIVE_BACKEND
        
        if self.backend == "cuda" and BACKENDS["cuda"]:
            try:
                self.stream = cv2.cuda.Stream()
                logger.info("CUDA流初始化成功")
            except Exception as e:
                logger.error(f"CUDA流初始化失败: {str(e)}")
                self.stream = None
        else:
            self.stream = None
    
    def gpu_compare(self, frame1, frame2) -> float:
        """
        GPU加速的帧比较
        
        使用GPU计算两帧之间的绝对差异
        
        Args:
            frame1: 第一帧
            frame2: 第二帧
            
        Returns:
            float: 差异值 (越小表示越相似)
        """
        if self.backend == "cuda" and BACKENDS["cuda"]:
            try:
                # 使用OpenCV CUDA
                gpu_frame1 = cv2.cuda.GpuMat()
                gpu_frame2 = cv2.cuda.GpuMat()
                
                # 上传到GPU
                gpu_frame1.upload(frame1)
                gpu_frame2.upload(frame2)
                
                # 确保两帧大小相同
                if gpu_frame1.size() != gpu_frame2.size():
                    gpu_frame2 = cv2.cuda.resize(gpu_frame2, (gpu_frame1.cols, gpu_frame1.rows))
                
                # 计算绝对差异
                diff = cv2.cuda.absdiff(gpu_frame1, gpu_frame2)
                
                # 计算平均差异
                return cv2.cuda.mean(diff)[0]
            
            except Exception as e:
                logger.warning(f"CUDA处理失败，回退到CPU: {str(e)}")
                return self._cpu_fallback_compare(frame1, frame2)
        
        elif self.backend == "opencl" and BACKENDS["opencl"]:
            # OpenCL实现
            try:
                return self._opencl_compare(frame1, frame2)
            except Exception as e:
                logger.warning(f"OpenCL处理失败，回退到CPU: {str(e)}")
                return self._cpu_fallback_compare(frame1, frame2)
        
        else:
            # 回退到CPU实现
            return self._cpu_fallback_compare(frame1, frame2)
    
    def _cpu_fallback_compare(self, frame1, frame2) -> float:
        """CPU回退实现"""
        # 确保两帧大小相同
        if frame1.shape != frame2.shape:
            frame2 = cv2.resize(frame2, (frame1.shape[1], frame1.shape[0]))
        
        # 计算绝对差异
        diff = cv2.absdiff(frame1, frame2)
        
        # 计算平均差异
        return np.mean(diff)
    
    def _opencl_compare(self, frame1, frame2) -> float:
        """OpenCL实现的帧比较"""
        try:
            # 获取平台和设备
            platforms = cl.get_platforms()
            devices = platforms[0].get_devices()
            context = cl.Context([devices[0]])
            queue = cl.CommandQueue(context)
            
            # 确保两帧大小相同
            if frame1.shape != frame2.shape:
                frame2 = cv2.resize(frame2, (frame1.shape[1], frame1.shape[0]))
            
            # 创建OpenCL缓冲区
            frame1_buf = cl.Buffer(context, cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR, hostbuf=frame1.astype(np.float32))
            frame2_buf = cl.Buffer(context, cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR, hostbuf=frame2.astype(np.float32))
            result_buf = cl.Buffer(context, cl.mem_flags.WRITE_ONLY, frame1.nbytes)
            
            # OpenCL程序
            program = cl.Program(context, """
            __kernel void absdiff(__global const float *frame1, 
                                  __global const float *frame2,
                                  __global float *result,
                                  const int width,
                                  const int height,
                                  const int channels) {
                int x = get_global_id(0);
                int y = get_global_id(1);
                
                if (x < width && y < height) {
                    for (int c = 0; c < channels; c++) {
                        int idx = (y * width + x) * channels + c;
                        result[idx] = fabs(frame1[idx] - frame2[idx]);
                    }
                }
            }
            """).build()
            
            # 执行内核
            height, width = frame1.shape[:2]
            channels = 3 if len(frame1.shape) > 2 else 1
            
            program.absdiff(queue, (width, height), None, 
                          frame1_buf, frame2_buf, result_buf,
                          np.int32(width), np.int32(height), np.int32(channels))
            
            # 获取结果
            result = np.zeros_like(frame1, dtype=np.float32)
            cl.enqueue_copy(queue, result, result_buf)
            
            return np.mean(result)
            
        except Exception as e:
            logger.error(f"OpenCL处理出错: {str(e)}")
            return self._cpu_fallback_compare(frame1, frame2)
    
    def gpu_histogram(self, frame) -> np.ndarray:
        """
        GPU加速的直方图计算
        
        Args:
            frame: 输入帧
            
        Returns:
            np.ndarray: 计算的直方图
        """
        if self.backend == "cuda" and BACKENDS["cuda"]:
            try:
                # 转换为HSV
                gpu_frame = cv2.cuda.GpuMat()
                gpu_frame.upload(frame)
                gpu_hsv = cv2.cuda.cvtColor(gpu_frame, cv2.COLOR_BGR2HSV)
                
                # 计算直方图
                h_hist = cv2.cuda_hist.histogram(gpu_hsv, 0, 180, 30)
                s_hist = cv2.cuda_hist.histogram(gpu_hsv, 1, 256, 32)
                
                return np.concatenate([h_hist.download(), s_hist.download()])
            
            except Exception as e:
                logger.warning(f"CUDA直方图计算失败，回退到CPU: {str(e)}")
                return self._cpu_histogram(frame)
        else:
            return self._cpu_histogram(frame)
    
    def _cpu_histogram(self, frame) -> np.ndarray:
        """CPU回退的直方图计算"""
        # 转换为HSV
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # 计算直方图
        h_hist = cv2.calcHist([hsv], [0], None, [30], [0, 180])
        s_hist = cv2.calcHist([hsv], [1], None, [32], [0, 256])
        
        # 归一化
        cv2.normalize(h_hist, h_hist, 0, 1, cv2.NORM_MINMAX)
        cv2.normalize(s_hist, s_hist, 0, 1, cv2.NORM_MINMAX)
        
        return np.concatenate([h_hist.flatten(), s_hist.flatten()])
    
    def gpu_psnr(self, frame1, frame2) -> float:
        """
        GPU加速的PSNR计算
        
        Args:
            frame1: 第一帧
            frame2: 第二帧
            
        Returns:
            float: PSNR值 (越高表示越相似)
        """
        if self.backend == "cuda" and BACKENDS["cuda"]:
            try:
                # 上传到GPU
                gpu_frame1 = cv2.cuda.GpuMat()
                gpu_frame2 = cv2.cuda.GpuMat()
                gpu_frame1.upload(frame1)
                gpu_frame2.upload(frame2)
                
                # 确保尺寸相同
                if gpu_frame1.size() != gpu_frame2.size():
                    gpu_frame2 = cv2.cuda.resize(gpu_frame2, (gpu_frame1.cols, gpu_frame1.rows))
                
                # 计算差异的平方
                diff = cv2.cuda.absdiff(gpu_frame1, gpu_frame2)
                gpu_diff_squared = cv2.cuda.multiply(diff, diff)
                
                # 计算MSE
                mse = cv2.cuda.mean(gpu_diff_squared)[0]
                
                # 计算PSNR
                if mse == 0:
                    return float('inf')
                
                return 10.0 * np.log10((255.0 * 255.0) / mse)
            
            except Exception as e:
                logger.warning(f"CUDA PSNR计算失败，回退到CPU: {str(e)}")
                return self._cpu_psnr(frame1, frame2)
        else:
            return self._cpu_psnr(frame1, frame2)
    
    def _cpu_psnr(self, frame1, frame2) -> float:
        """CPU回退的PSNR计算"""
        # 确保尺寸相同
        if frame1.shape != frame2.shape:
            frame2 = cv2.resize(frame2, (frame1.shape[1], frame1.shape[0]))
        
        # 计算MSE
        mse = np.mean((frame1.astype(np.float64) - frame2.astype(np.float64)) ** 2)
        
        # 计算PSNR
        if mse == 0:
            return float('inf')
        
        return 10.0 * np.log10((255.0 * 255.0) / mse)

class VideoProcessorGPU:
    """GPU加速的视频处理器"""
    
    def __init__(self):
        """初始化处理器"""
        self.backend = ACTIVE_BACKEND
        
        if self.backend == "cuda" and BACKENDS["cuda"]:
            try:
                self.stream = cv2.cuda.Stream()
            except Exception as e:
                logger.error(f"CUDA流初始化失败: {str(e)}")
                self.stream = None
        else:
            self.stream = None
    
    def gpu_resize(self, frame, width: int, height: int) -> np.ndarray:
        """
        GPU加速的尺寸调整
        
        Args:
            frame: 输入帧
            width: 目标宽度
            height: 目标高度
            
        Returns:
            np.ndarray: 调整大小后的帧
        """
        if self.backend == "cuda" and BACKENDS["cuda"]:
            try:
                gpu_frame = cv2.cuda.GpuMat()
                gpu_frame.upload(frame)
                
                # 调整大小
                gpu_resized = cv2.cuda.resize(gpu_frame, (width, height))
                
                # 下载结果
                return gpu_resized.download()
            
            except Exception as e:
                logger.warning(f"CUDA尺寸调整失败，回退到CPU: {str(e)}")
                return cv2.resize(frame, (width, height))
        else:
            return cv2.resize(frame, (width, height))
    
    def gpu_filter(self, frame, filter_type: str = "gaussian", kernel_size: int = 5) -> np.ndarray:
        """
        GPU加速的滤波处理
        
        Args:
            frame: 输入帧
            filter_type: 滤波类型，可选 "gaussian", "median", "bilateral"
            kernel_size: 核大小
            
        Returns:
            np.ndarray: 滤波后的帧
        """
        if self.backend == "cuda" and BACKENDS["cuda"]:
            try:
                gpu_frame = cv2.cuda.GpuMat()
                gpu_frame.upload(frame)
                
                # 应用滤波
                if filter_type == "gaussian":
                    gpu_filtered = cv2.cuda.GaussianBlur(gpu_frame, (kernel_size, kernel_size), 0)
                elif filter_type == "median":
                    # CUDA不直接支持中值滤波，回退到CPU
                    return cv2.medianBlur(frame, kernel_size)
                elif filter_type == "bilateral":
                    # CUDA不直接支持双边滤波，回退到CPU
                    return cv2.bilateralFilter(frame, kernel_size, 75, 75)
                else:
                    raise ValueError(f"不支持的滤波类型: {filter_type}")
                
                # 下载结果
                return gpu_filtered.download()
            
            except Exception as e:
                logger.warning(f"CUDA滤波处理失败，回退到CPU: {str(e)}")
        
        # CPU处理
        if filter_type == "gaussian":
            return cv2.GaussianBlur(frame, (kernel_size, kernel_size), 0)
        elif filter_type == "median":
            return cv2.medianBlur(frame, kernel_size)
        elif filter_type == "bilateral":
            return cv2.bilateralFilter(frame, kernel_size, 75, 75)
        else:
            raise ValueError(f"不支持的滤波类型: {filter_type}")

def get_gpu_info() -> Dict[str, Any]:
    """
    获取GPU信息
    
    Returns:
        Dict[str, Any]: GPU信息，包括可用性、型号、内存等
    """
    gpu_info = {
        "available": False,
        "backend": ACTIVE_BACKEND,
        "devices": []
    }
    
    if ACTIVE_BACKEND == "cuda":
        try:
            # 尝试获取CUDA设备信息
            device_count = cv2.cuda.getCudaEnabledDeviceCount()
            gpu_info["available"] = device_count > 0
            
            for i in range(device_count):
                try:
                    device_name = cv2.cuda.getDevice()
                    device_info = {
                        "index": i,
                        "name": f"CUDA Device {i}",
                        "compute_capability": cv2.cuda.getDevice()
                    }
                    gpu_info["devices"].append(device_info)
                except Exception as e:
                    logger.warning(f"获取CUDA设备 {i} 信息失败: {str(e)}")
            
            # 尝试从CuPy获取更详细的信息
            try:
                import cupy as cp
                for i in range(len(gpu_info["devices"])):
                    with cp.cuda.Device(i):
                        props = cp.cuda.runtime.getDeviceProperties(i)
                        mem_info = cp.cuda.runtime.memGetInfo()
                        
                        gpu_info["devices"][i].update({
                            "name": props["name"].decode(),
                            "total_memory": mem_info[1],
                            "free_memory": mem_info[0],
                            "compute_capability": f"{props['major']}.{props['minor']}"
                        })
            except (ImportError, Exception) as e:
                logger.debug(f"无法从CuPy获取详细GPU信息: {str(e)}")
        
        except Exception as e:
            logger.warning(f"获取CUDA信息失败: {str(e)}")
    
    elif ACTIVE_BACKEND == "opencl":
        try:
            import pyopencl as cl
            platforms = cl.get_platforms()
            gpu_info["available"] = len(platforms) > 0
            
            for platform_idx, platform in enumerate(platforms):
                devices = platform.get_devices(device_type=cl.device_type.GPU)
                
                for device_idx, device in enumerate(devices):
                    device_info = {
                        "index": device_idx,
                        "platform": platform.name,
                        "name": device.name,
                        "type": "GPU",
                        "vendor": device.vendor,
                        "version": device.version,
                        "total_memory": device.global_mem_size
                    }
                    gpu_info["devices"].append(device_info)
        
        except Exception as e:
            logger.warning(f"获取OpenCL信息失败: {str(e)}")
    
    return gpu_info

def benchmark_gpu() -> Dict[str, float]:
    """
    对GPU加速性能进行基准测试
    
    Returns:
        Dict[str, float]: 基准测试结果
    """
    results = {
        "cpu_time": 0.0,
        "gpu_time": 0.0,
        "speedup": 0.0,
        "frames_per_sec_cpu": 0.0,
        "frames_per_sec_gpu": 0.0
    }
    
    import time
    import numpy as np
    
    # 创建测试帧
    frame1 = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
    frame2 = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
    
    # 创建比较器
    gpu_comparator = VideoComparatorGPU()
    
    # CPU测试
    t0 = time.time()
    num_iterations = 100
    
    for _ in range(num_iterations):
        _ = gpu_comparator._cpu_fallback_compare(frame1, frame2)
    
    cpu_time = time.time() - t0
    results["cpu_time"] = cpu_time
    results["frames_per_sec_cpu"] = num_iterations / cpu_time
    
    # GPU测试
    if ACTIVE_BACKEND:
        t0 = time.time()
        
        for _ in range(num_iterations):
            _ = gpu_comparator.gpu_compare(frame1, frame2)
        
        gpu_time = time.time() - t0
        results["gpu_time"] = gpu_time
        results["frames_per_sec_gpu"] = num_iterations / gpu_time
        
        # 计算加速比
        if cpu_time > 0:
            results["speedup"] = cpu_time / gpu_time
    
    return results

if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # 显示GPU信息
    gpu_info = get_gpu_info()
    print("GPU信息:")
    print(f"  可用性: {'是' if gpu_info['available'] else '否'}")
    print(f"  后端: {gpu_info['backend'] or '无'}")
    print(f"  设备数量: {len(gpu_info['devices'])}")
    
    for i, device in enumerate(gpu_info["devices"]):
        print(f"  设备 {i}:")
        for key, value in device.items():
            if key != "index":
                print(f"    {key}: {value}")
    
    # 运行基准测试
    if gpu_info["available"]:
        print("\n运行基准测试...")
        benchmark = benchmark_gpu()
        
        print(f"CPU处理速度: {benchmark['frames_per_sec_cpu']:.1f} 帧/秒")
        print(f"GPU处理速度: {benchmark['frames_per_sec_gpu']:.1f} 帧/秒")
        print(f"加速比: {benchmark['speedup']:.1f}x") 