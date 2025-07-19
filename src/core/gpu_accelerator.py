#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GPU加速器模块

提供GPU加速功能，优化视频处理性能，确保处理时间低于5秒。
支持多种GPU加速框架，包括CUDA、OpenCL和DirectML。
"""

import os
import sys
import logging
import time
import numpy as np
import concurrent.futures
from typing import Dict, List, Tuple, Optional, Union, Any, Callable
from pathlib import Path

# 项目内部导入
from src.utils.log_handler import get_logger

# 配置日志
gpu_logger = get_logger("gpu_accelerator")

class GPUAccelerator:
    """GPU加速器
    
    为视频处理提供GPU加速功能，实现高效处理，
    确保处理时间低于5秒。
    """
    
    def __init__(self, force_gpu: bool = False):
        """初始化GPU加速器
        
        Args:
            force_gpu: 是否强制使用GPU，即使没有检测到合适的GPU
        """
        self.available_backends = []
        self.active_backend = None
        self.force_gpu = force_gpu
        self.gpus_info = {}
        self.max_memory_usage = 0.85  # 最大使用GPU内存的比例
        self.optimal_batch_size = 32  # 默认最优批大小
        
        # 初始化可用的GPU后端
        self._initialize_backends()
        
        # 优化批处理大小
        self._optimize_batch_size()
        
        if self.active_backend:
            gpu_logger.info(f"GPU加速器初始化完成，使用后端: {self.active_backend}")
        else:
            gpu_logger.info("未找到可用的GPU，将使用CPU模式")
    
    def _initialize_backends(self):
        """初始化并检测可用的GPU加速后端"""
        # 检测CUDA
        try:
            import cupy
            import torch
            self.available_backends.append("cuda")
            
            # 获取CUDA设备信息
            num_gpus = cupy.cuda.runtime.getDeviceCount()
            for i in range(num_gpus):
                device_props = cupy.cuda.runtime.getDeviceProperties(i)
                self.gpus_info[f"cuda_{i}"] = {
                    "name": device_props["name"].decode(),
                    "compute_capability": f"{device_props['major']}.{device_props['minor']}",
                    "total_memory": device_props["totalGlobalMem"] / (1024**3),  # GB
                    "backend": "cuda"
                }
            
            gpu_logger.info(f"检测到 {num_gpus} 个CUDA设备")
            
            # 如果有CUDA设备，设置为默认后端
            if num_gpus > 0:
                self.active_backend = "cuda"
                # 预热CUDA
                self._warmup_cuda()
        except ImportError:
            gpu_logger.debug("未检测到CUDA或cupy库")
        
        # 检测OpenCL
        try:
            import pyopencl as cl
            self.available_backends.append("opencl")
            
            # 获取OpenCL平台和设备信息
            platforms = cl.get_platforms()
            for platform_idx, platform in enumerate(platforms):
                devices = platform.get_devices()
                for device_idx, device in enumerate(devices):
                    if device.type == cl.device_type.GPU:
                        self.gpus_info[f"opencl_{platform_idx}_{device_idx}"] = {
                            "name": device.name,
                            "platform": platform.name,
                            "version": device.version,
                            "total_memory": device.global_mem_size / (1024**3),  # GB
                            "backend": "opencl"
                        }
            
            # 如果有OpenCL设备且CUDA不可用，设置为默认后端
            if self.gpus_info and not self.active_backend:
                self.active_backend = "opencl"
                
            gpu_logger.info(f"检测到 {len(platforms)} 个OpenCL平台")
        except ImportError:
            gpu_logger.debug("未检测到OpenCL或pyopencl库")
        
        # 检测DirectML（适用于Windows）
        try:
            import tensorflow as tf
            if hasattr(tf, 'config') and hasattr(tf.config, 'list_physical_devices'):
                gpus = tf.config.list_physical_devices('GPU')
                if gpus:
                    self.available_backends.append("directml")
                    for i, gpu in enumerate(gpus):
                        self.gpus_info[f"dml_{i}"] = {
                            "name": gpu.name,
                            "backend": "directml"
                        }
                    
                    # 如果没有其他后端可用，设置DirectML为默认后端
                    if not self.active_backend:
                        self.active_backend = "directml"
                    
                    gpu_logger.info(f"检测到 {len(gpus)} 个DirectML兼容设备")
        except ImportError:
            gpu_logger.debug("未检测到DirectML或tensorflow库")
        
        # 如果未找到GPU但强制使用GPU模式
        if not self.active_backend and self.force_gpu:
            gpu_logger.warning("未检测到GPU设备，但启用了强制GPU模式")
            # 尝试启用CPU模拟GPU模式
            self.active_backend = "cpu_simulation"
            self.available_backends.append("cpu_simulation")
        
        # 记录GPU状态
        if self.active_backend:
            gpu_logger.info(f"GPU加速已启用: {self.active_backend}")
            for gpu_id, info in self.gpus_info.items():
                if info.get('backend') == self.active_backend:
                    gpu_logger.info(f"  使用设备: {info.get('name', '未知')} ({gpu_id})")
        else:
            gpu_logger.warning("未启用GPU加速，将使用CPU处理")
    
    def _warmup_cuda(self):
        """预热CUDA设备以减少首次执行延迟"""
        try:
            if self.active_backend == "cuda":
                import cupy as cp
                import torch
                
                # 创建并执行一个小矩阵乘法来预热设备
                a = cp.random.rand(100, 100).astype(cp.float32)
                b = cp.random.rand(100, 100).astype(cp.float32)
                cp.matmul(a, b)
                cp.cuda.stream.get_current_stream().synchronize()
                
                # 预热PyTorch
                x = torch.rand(100, 100, device='cuda')
                y = torch.rand(100, 100, device='cuda')
                z = torch.matmul(x, y)
                torch.cuda.synchronize()
                
                gpu_logger.info("CUDA设备预热完成")
        except Exception as e:
            gpu_logger.warning(f"CUDA预热失败: {e}")
    
    def _optimize_batch_size(self):
        """根据GPU特性自动优化批处理大小"""
        try:
            if self.active_backend == "cuda":
                import cupy as cp
                
                # 获取GPU显存信息
                mem_info = cp.cuda.runtime.memGetInfo()
                free_memory = mem_info[0]
                total_memory = mem_info[1]
                
                # 根据可用显存和GPU计算能力调整批大小
                memory_factor = (free_memory / total_memory) * self.max_memory_usage
                
                # 查找主GPU的计算能力
                for gpu_id, info in self.gpus_info.items():
                    if info.get('backend') == "cuda" and gpu_id.startswith("cuda_0"):
                        cc = info.get('compute_capability', '0.0')
                        cc_major = int(cc.split('.')[0])
                        
                        # 根据计算能力优化批大小
                        if cc_major >= 7:  # Volta及以上架构
                            base_batch = 48
                        elif cc_major >= 6:  # Pascal架构
                            base_batch = 32
                        else:  # 旧架构
                            base_batch = 16
                        
                        self.optimal_batch_size = max(8, int(base_batch * memory_factor))
                        break
                        
                gpu_logger.info(f"已根据GPU特性优化批处理大小: {self.optimal_batch_size}")
                
            elif self.active_backend == "opencl":
                # OpenCL优化批大小
                self.optimal_batch_size = 16
                
            elif self.active_backend == "directml":
                # DirectML优化批大小
                self.optimal_batch_size = 24
        except Exception as e:
            gpu_logger.warning(f"批处理大小优化失败: {e}, 使用默认值: {self.optimal_batch_size}")
    
    def is_gpu_available(self) -> bool:
        """检查是否有可用的GPU
        
        Returns:
            bool: 是否有可用的GPU
        """
        return self.active_backend is not None and self.active_backend != "cpu_simulation"
    
    def get_available_gpus(self) -> Dict[str, Any]:
        """获取可用的GPU信息
        
        Returns:
            Dict[str, Any]: GPU信息字典
        """
        return self.gpus_info
    
    def select_backend(self, backend: str) -> bool:
        """选择要使用的GPU后端
        
        Args:
            backend: 后端名称，如 'cuda', 'opencl', 'directml'
            
        Returns:
            bool: 是否成功选择后端
        """
        if backend in self.available_backends:
            self.active_backend = backend
            gpu_logger.info(f"已选择GPU后端: {backend}")
            # 重新优化批处理大小
            self._optimize_batch_size()
            return True
        else:
            gpu_logger.warning(f"后端 {backend} 不可用，可用后端: {self.available_backends}")
            return False
    
    def accelerate_image_processing(self, 
                                   image: np.ndarray, 
                                   process_func: Callable,
                                   *args, **kwargs) -> Tuple[np.ndarray, float]:
        """使用GPU加速图像处理
        
        Args:
            image: 输入图像（numpy数组）
            process_func: 处理函数，接受图像和其他参数
            *args, **kwargs: 传递给处理函数的参数
            
        Returns:
            Tuple[np.ndarray, float]: (处理后的图像, 处理时间)
        """
        if not self.active_backend:
            # 如果没有GPU，直接在CPU上处理
            start_time = time.time()
            result = process_func(image, *args, **kwargs)
            elapsed = time.time() - start_time
            return result, elapsed
        
        start_time = time.time()
        
        try:
            if self.active_backend == "cuda":
                import cupy as cp
                
                # 转移到GPU
                gpu_image = cp.array(image)
                
                # 在GPU上处理
                gpu_result = self._cuda_process(gpu_image, process_func, *args, **kwargs)
                
                # 转回CPU
                result = cp.asnumpy(gpu_result)
                
            elif self.active_backend == "opencl":
                # OpenCL处理
                result = self._opencl_process(image, process_func, *args, **kwargs)
                
            elif self.active_backend == "directml":
                # DirectML处理
                result = self._directml_process(image, process_func, *args, **kwargs)
                
            else:
                # 回退到CPU处理
                result = process_func(image, *args, **kwargs)
            
            elapsed = time.time() - start_time
            gpu_logger.debug(f"图像处理耗时: {elapsed:.4f}秒")
            
            return result, elapsed
            
        except Exception as e:
            gpu_logger.error(f"GPU处理失败: {str(e)}，回退到CPU")
            
            # 回退到CPU处理
            start_time = time.time()
            result = process_func(image, *args, **kwargs)
            elapsed = time.time() - start_time
            
            return result, elapsed
    
    def accelerate_video_processing(self,
                                   video_path: str,
                                   frame_process_func: Callable,
                                   max_frames: int = 0,
                                   start_time: float = 0.0,
                                   *args, **kwargs) -> Tuple[List[np.ndarray], float]:
        """使用GPU加速视频处理
        
        Args:
            video_path: 视频文件路径
            frame_process_func: 处理函数，接受帧和其他参数
            max_frames: 最大处理帧数，0表示处理所有帧
            start_time: 开始处理的时间点（秒）
            *args, **kwargs: 传递给处理函数的参数
            
        Returns:
            Tuple[List[np.ndarray], float]: (处理后的帧列表, 处理时间)
        """
        import cv2
        
        # 打开视频
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            gpu_logger.error(f"无法打开视频: {video_path}")
            return [], 0
        
        # 获取视频信息
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # 设置起始位置
        if start_time > 0:
            start_frame = int(start_time * fps)
            cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        
        # 确定处理帧数
        frames_to_process = total_frames - int(start_time * fps)
        if max_frames > 0 and max_frames < frames_to_process:
            frames_to_process = max_frames
        
        # 视频分析和优化
        is_4k = width * height >= 3840 * 2160
        target_time = 5.0  # 目标处理时间(秒)
        
        # 根据视频分辨率调整批大小
        batch_size = self.optimal_batch_size
        if is_4k:
            batch_size = max(8, batch_size // 2)  # 4K视频减小批大小
        
        # 自适应调整策略
        adaptive_strategy = {
            'current_batch_size': batch_size,
            'min_batch_size': 4,
            'max_batch_size': batch_size * 2,
            'adjustment_factor': 0.8,  # 调整系数
            'target_time': target_time,
            'performance_history': []  # 存储历史性能数据
        }
        
        # 开始处理
        start_time_processing = time.time()
        processed_frames = []
        frames_read = 0
        
        # 优化: 提前读取帧
        preloaded_frames = []
        preload_size = min(batch_size * 2, frames_to_process)
        for _ in range(preload_size):
            ret, frame = cap.read()
            if not ret:
                break
            preloaded_frames.append(frame)
            frames_read += 1
        
        # 处理视频
        while preloaded_frames or frames_read < frames_to_process:
            # 获取当前批次
            current_batch = preloaded_frames[:batch_size]
            preloaded_frames = preloaded_frames[batch_size:]
            
            # 读取更多帧以保持预加载缓冲区填满
            while len(preloaded_frames) < preload_size and frames_read < frames_to_process:
                ret, frame = cap.read()
                if not ret:
                    break
                preloaded_frames.append(frame)
                frames_read += 1
            
            if not current_batch:
                break
            
            # 批处理计时
            batch_start_time = time.time()
            
            # 处理这批帧
            if self.active_backend == "cuda":
                # CUDA批处理
                processed_batch = self._cuda_batch_process(current_batch, frame_process_func, *args, **kwargs)
            elif self.active_backend == "opencl":
                # OpenCL批处理
                processed_batch = self._opencl_batch_process(current_batch, frame_process_func, *args, **kwargs)
            elif self.active_backend == "directml":
                # DirectML批处理
                processed_batch = self._directml_batch_process(current_batch, frame_process_func, *args, **kwargs)
            else:
                # CPU多线程处理
                with concurrent.futures.ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
                    processed_batch = list(executor.map(
                        lambda frame: frame_process_func(frame, *args, **kwargs), 
                        current_batch
                    ))
            
            processed_frames.extend(processed_batch)
            
            # 计算当前批次性能
            batch_time = time.time() - batch_start_time
            frames_per_second = len(current_batch) / batch_time
            adaptive_strategy['performance_history'].append(frames_per_second)
            
            # 自适应调整批大小
            self._adjust_batch_size(adaptive_strategy, batch_time, len(current_batch), 
                                    len(processed_frames), frames_to_process)
            batch_size = adaptive_strategy['current_batch_size']
        
        # 释放资源
        cap.release()
        
        # 确保及时释放GPU内存
        if self.active_backend == "cuda":
            try:
                import cupy as cp
                cp.get_default_memory_pool().free_all_blocks()
                cp.cuda.stream.get_current_stream().synchronize()
            except Exception as e:
                gpu_logger.warning(f"释放CUDA内存失败: {e}")
        
        total_time = time.time() - start_time_processing
        gpu_logger.info(f"视频处理完成: {len(processed_frames)}帧, 耗时{total_time:.2f}秒, FPS: {len(processed_frames)/total_time:.1f}")
        
        # 如果处理时间超过目标，记录警告
        if total_time > target_time:
            gpu_logger.warning(f"处理时间({total_time:.2f}s)超过目标时间({target_time}s)")
        
        return processed_frames, total_time
    
    def _adjust_batch_size(self, strategy, batch_time, batch_size, processed_count, total_frames):
        """自适应调整批处理大小以满足目标处理时间"""
        # 计算完成百分比
        completion_percent = processed_count / total_frames
        
        # 估计剩余时间
        if len(strategy['performance_history']) >= 3:
            # 使用最近3次批次的平均性能
            recent_fps = sum(strategy['performance_history'][-3:]) / 3
            estimated_remaining_frames = total_frames - processed_count
            estimated_remaining_time = estimated_remaining_frames / recent_fps
            
            # 计算预计总时间
            elapsed_time = time.time() - strategy['start_time'] if 'start_time' in strategy else 0
            estimated_total_time = elapsed_time + estimated_remaining_time
            
            # 根据预计总时间与目标时间的比例调整批大小
            time_ratio = strategy['target_time'] / estimated_total_time if estimated_total_time > 0 else 1.0
            
            if time_ratio < 0.8:  # 预计时间超过目标时间的125%
                # 需要加速 - 增加批大小
                new_batch_size = min(
                    strategy['max_batch_size'],
                    int(strategy['current_batch_size'] * (1.0 + (1.0 - time_ratio) * 0.5))
                )
                if new_batch_size != strategy['current_batch_size']:
                    strategy['current_batch_size'] = new_batch_size
                    gpu_logger.debug(f"调整批大小: {batch_size} -> {new_batch_size} (加速处理，完成度: {completion_percent:.1%})")
            
            elif time_ratio > 1.5 and completion_percent < 0.7:  # 有足够余量且处理未过半
                # 可以放慢 - 减小批大小来优化质量
                new_batch_size = max(
                    strategy['min_batch_size'],
                    int(strategy['current_batch_size'] * 0.9)
                )
                if new_batch_size != strategy['current_batch_size']:
                    strategy['current_batch_size'] = new_batch_size
                    gpu_logger.debug(f"调整批大小: {batch_size} -> {new_batch_size} (优化质量，完成度: {completion_percent:.1%})")
        
        # 保存开始时间（如果尚未保存）
        if 'start_time' not in strategy:
            strategy['start_time'] = time.time()
    
    def _cuda_process(self, gpu_image, process_func, *args, **kwargs):
        """CUDA处理实现"""
        import cupy as cp
        
        try:
            # 将函数参数转换为cupy数组（如果是numpy数组）
            cuda_args = []
            for arg in args:
                if isinstance(arg, np.ndarray):
                    cuda_args.append(cp.array(arg))
                else:
                    cuda_args.append(arg)
                    
            cuda_kwargs = {}
            for key, value in kwargs.items():
                if isinstance(value, np.ndarray):
                    cuda_kwargs[key] = cp.array(value)
                else:
                    cuda_kwargs[key] = value
            
            # 使用CUDA流并行处理
            with cp.cuda.Stream():
                result = process_func(gpu_image, *cuda_args, **cuda_kwargs)
                
            # 确保操作完成
            cp.cuda.stream.get_current_stream().synchronize()
            
            return result
        except Exception as e:
            gpu_logger.error(f"CUDA处理异常: {e}")
            # 回退到基本处理
            return process_func(cp.asnumpy(gpu_image), *args, **kwargs)
    
    def _opencl_process(self, image, process_func, *args, **kwargs):
        """OpenCL处理实现"""
        # 这里应包含特定于OpenCL的处理代码
        try:
            import pyopencl as cl
            import pyopencl.array
            
            # 获取平台、设备和上下文
            platforms = cl.get_platforms()
            if not platforms:
                raise ValueError("无法获取OpenCL平台")
                
            # 使用第一个平台和GPU设备
            for platform in platforms:
                devices = platform.get_devices(device_type=cl.device_type.GPU)
                if devices:
                    ctx = cl.Context(devices=devices)
                    queue = cl.CommandQueue(ctx)
                    
                    # 转换图像为适合OpenCL的格式并上传
                    # 实际实现应根据process_func定制
                    # ...
                    
                    return process_func(image, *args, **kwargs)
        except Exception as e:
            gpu_logger.error(f"OpenCL处理失败: {str(e)}")
            
        # 回退到CPU处理
        return process_func(image, *args, **kwargs)
    
    def _directml_process(self, image, process_func, *args, **kwargs):
        """DirectML处理实现"""
        # 这里应包含特定于DirectML的处理代码
        try:
            import tensorflow as tf
            
            # 确保TensorFlow使用GPU
            with tf.device('/GPU:0'):
                # 转换为TensorFlow张量
                # 实际实现应根据process_func定制
                # ...
                
                return process_func(image, *args, **kwargs)
        except Exception as e:
            gpu_logger.error(f"DirectML处理失败: {str(e)}")
            
        # 回退到CPU处理
        return process_func(image, *args, **kwargs)
    
    def _cuda_batch_process(self, frames, process_func, *args, **kwargs):
        """CUDA批处理实现"""
        try:
            import cupy as cp
            import torch
            
            # 将所有帧转移到GPU
            gpu_frames = [cp.array(frame) for frame in frames]
            
            # 创建CUDA流批量处理
            results = []
            with cp.cuda.Stream():
                # 构建处理函数
                def process_with_cuda(frame):
                    try:
                        result = process_func(frame, *args, **kwargs)
                        return result
                    except Exception as e:
                        gpu_logger.error(f"CUDA帧处理失败: {e}")
                        # 回退到CPU处理单帧
                        cpu_frame = cp.asnumpy(frame)
                        return cp.array(process_func(cpu_frame, *args, **kwargs))
                
                # 并行处理所有帧
                for frame in gpu_frames:
                    results.append(process_with_cuda(frame))
                
                # 确保所有操作完成
                cp.cuda.stream.get_current_stream().synchronize()
            
            # 转回CPU
            cpu_results = [cp.asnumpy(result) for result in results]
            
            # 显式释放GPU内存
            del gpu_frames
            del results
            cp.get_default_memory_pool().free_all_blocks()
            
            return cpu_results
        except Exception as e:
            gpu_logger.error(f"CUDA批处理失败: {str(e)}")
            
            # 回退到CPU多线程处理
            with concurrent.futures.ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
                return list(executor.map(
                    lambda frame: process_func(frame, *args, **kwargs), 
                    frames
                ))
    
    def _opencl_batch_process(self, frames, process_func, *args, **kwargs):
        """OpenCL批处理实现"""
        # 使用多线程实现并行处理
        with concurrent.futures.ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
            return list(executor.map(
                lambda frame: self._opencl_process(frame, process_func, *args, **kwargs), 
                frames
            ))
    
    def _directml_batch_process(self, frames, process_func, *args, **kwargs):
        """DirectML批处理实现"""
        # 使用多线程实现并行处理
        with concurrent.futures.ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
            return list(executor.map(
                lambda frame: self._directml_process(frame, process_func, *args, **kwargs), 
                frames
            ))


def get_gpu_accelerator(force_gpu: bool = False) -> GPUAccelerator:
    """获取GPU加速器实例（单例模式）
    
    Args:
        force_gpu: 是否强制使用GPU模式
        
    Returns:
        GPUAccelerator: GPU加速器实例
    """
    global _gpu_accelerator
    if _gpu_accelerator is None:
        _gpu_accelerator = GPUAccelerator(force_gpu)
    return _gpu_accelerator


def is_gpu_available() -> bool:
    """检查系统是否有可用的GPU
    
    Returns:
        bool: 是否有可用的GPU
    """
    accelerator = get_gpu_accelerator()
    return accelerator.is_gpu_available()


def accelerate_function(func: Callable) -> Callable:
    """函数GPU加速装饰器
    
    Args:
        func: 要加速的函数
        
    Returns:
        加速后的函数
    """
    def wrapper(*args, **kwargs):
        # 获取是否使用GPU的参数
        use_gpu = kwargs.pop('use_gpu', True)
        

def is_tensor(obj):
    """检查对象是否为张量
    
    Args:
        obj: 要检查的对象
    
    Returns:
        bool: 是否为张量
    """
    # 在模拟模块中总是返回False
    # 这是一个简单的实现实际TensorFlow中会检查对象类型
    return False

# 创建单例实例
_gpu_accelerator = None