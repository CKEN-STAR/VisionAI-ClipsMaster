#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
硬件检测器模块

提供系统硬件加速能力的检测，支持多种视频处理和AI加速技术，
包括NVIDIA CUDA/NVDEC、Intel QSV、AMD VCE等。
"""

import os
import sys
import platform
import subprocess
import ctypes
import logging
from typing import Dict, List, Set, Tuple, Optional, Union, Any
from enum import Enum, auto
import re

from src.utils.log_handler import get_logger

# 配置日志记录器
logger = get_logger("hw_detector")

# 导出函数列表
__all__ = [
    'AccelerationType',
    'detect_zero_copy_acceleration',
    'check_zero_copy_availability',
    'check_nvidia_support',
    'check_intel_qsv',
    'get_cuda_device_info',
    'get_detected_acceleration',
    'print_acceleration_report'
]

class AccelerationType(Enum):
    """硬件加速类型枚举"""
    NVIDIA_CUDA = auto()     # NVIDIA CUDA计算加速
    NVIDIA_NVENC = auto()    # NVIDIA NVENC编码加速
    NVIDIA_NVDEC = auto()    # NVIDIA NVDEC解码加速
    INTEL_QSV = auto()       # Intel Quick Sync Video加速
    INTEL_MFX = auto()       # Intel Media SDK加速
    AMD_AMF = auto()         # AMD Advanced Media Framework加速
    AMD_VCE = auto()         # AMD Video Coding Engine加速
    OPENCL = auto()          # OpenCL通用计算加速
    VULKAN = auto()          # Vulkan计算加速
    CPU_AVX = auto()         # CPU AVX指令集加速
    CPU_AVX2 = auto()        # CPU AVX2指令集加速
    ZERO_COPY = auto()       # 零拷贝内存传输支持


def check_zero_copy_availability():
    """检查零拷贝功能是否可用
    
    检测系统是否支持零拷贝内存传输
    
    Returns:
        bool: 是否支持零拷贝
    """
    # 检查内存映射功能
    try:
        import mmap
        # 检查系统是否支持mmap
        if hasattr(mmap, 'mmap'):
            # 尝试创建小的内存映射测试
            with open(os.devnull, 'wb') as f:
                try:
                    mapped = mmap.mmap(f.fileno(), 4096, access=mmap.ACCESS_READ)
                    mapped.close()
                    logger.info("内存映射功能可用")
                    
                    # 检查硬件加速零拷贝支持
                    hw_accel = detect_zero_copy_acceleration()
                    if hw_accel:
                        logger.info(f"硬件加速零拷贝可用: {hw_accel}")
                        return True
                    
                    # 即使无硬件加速，基本零拷贝仍可用
                    logger.info("基本零拷贝功能可用（无硬件加速）")
                    return True
                except Exception as e:
                    logger.debug(f"内存映射测试失败: {e}")
    except ImportError:
        logger.warning("mmap模块不可用")
    
    # 检查是否有共享内存支持
    if sys.platform == 'linux':
        try:
            # 检查Linux共享内存支持
            import posix_ipc
            logger.info("POSIX IPC共享内存支持可用")
            return True
        except ImportError:
            pass
    
    # 检查numpy的零拷贝视图功能
    try:
        import numpy as np
        # 创建一个简单的测试数组
        a = np.zeros((100, 100), dtype=np.uint8)
        # 尝试创建视图
        b = a.view()
        # 视图和原数组共享内存
        if np.shares_memory(a, b):
            logger.info("NumPy零拷贝视图功能可用")
            return True
    except ImportError:
        logger.warning("NumPy模块不可用")
    
    logger.warning("系统不支持零拷贝功能")
    return False


def detect_zero_copy_acceleration():
    """检测可用硬件加速方案
    
    检测系统中可用的零拷贝硬件加速方案
    
    Returns:
        List[str]: 可用加速器列表
    """
    accelerators = []
    
    if check_nvidia_support():
        accelerators.append('nvidia_nvdec')
    
    if check_intel_qsv():
        accelerators.append('intel_qsv')
    
    return accelerators


def check_nvidia_support():
    """检测NVIDIA支持
    
    检测系统是否有NVIDIA GPU并支持CUDA/NVDEC
    
    Returns:
        bool: 是否支持
    """
    # 首先检查系统环境
    if sys.platform == 'win32':
        try:
            # 使用nvml查询
            import pynvml
            try:
                pynvml.nvmlInit()
                device_count = pynvml.nvmlDeviceGetCount()
                pynvml.nvmlShutdown()
                if device_count > 0:
                    logger.info(f"检测到{device_count}个NVIDIA设备")
                    return True
            except Exception as e:
                pass
                
            # 使用subprocess查询
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=name', '--format=csv,noheader'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=True
            )
            if result.returncode == 0 and result.stdout.strip():
                logger.info(f"检测到NVIDIA GPU: {result.stdout.strip()}")
                return True
        except Exception as e:
            logger.debug(f"NVIDIA检测错误: {e}")
    
    elif sys.platform == 'linux':
        try:
            # Linux系统检查
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=name', '--format=csv,noheader'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            if result.returncode == 0 and result.stdout.strip():
                logger.info(f"检测到NVIDIA GPU: {result.stdout.strip()}")
                return True
        except Exception as e:
            logger.debug(f"NVIDIA检测错误: {e}")
    
    elif sys.platform == 'darwin':
        # macOS不支持NVIDIA CUDA
        return False
    
    # 检查环境变量
    if 'CUDA_VISIBLE_DEVICES' in os.environ:
        if os.environ['CUDA_VISIBLE_DEVICES'].strip() and os.environ['CUDA_VISIBLE_DEVICES'] != '-1':
            logger.info(f"从环境变量CUDA_VISIBLE_DEVICES检测到NVIDIA支持")
            return True
    
    # 检查CUDA库
    try:
        import torch
        if torch.cuda.is_available():
            device_count = torch.cuda.device_count()
            logger.info(f"通过PyTorch检测到{device_count}个CUDA设备")
            return device_count > 0
    except ImportError:
        pass
    
    return False


def check_intel_qsv():
    """检测Intel QSV支持
    
    检测系统是否有Intel GPU并支持Quick Sync Video
    
    Returns:
        bool: 是否支持
    """
    # 检测系统环境
    if sys.platform == 'win32':
        try:
            # Windows下检测QSV
            import dxgidebug
            try:
                adapters = dxgidebug.get_adapters()
                for adapter in adapters:
                    if 'Intel' in adapter.description:
                        logger.info(f"检测到Intel显示适配器: {adapter.description}")
                        return True
            except Exception:
                pass
            
            # 通过WMIC检测
            result = subprocess.run(
                ['wmic', 'path', 'win32_VideoController', 'get', 'name'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=True
            )
            if result.returncode == 0:
                if 'Intel' in result.stdout and ('HD Graphics' in result.stdout or 'UHD Graphics' in result.stdout or 'Iris' in result.stdout):
                    logger.info(f"检测到Intel GPU: {result.stdout.strip()}")
                    return True
        except Exception as e:
            logger.debug(f"Intel QSV检测错误: {e}")
    
    elif sys.platform == 'linux':
        try:
            # 检查Linux系统上的Intel GPU
            result = subprocess.run(
                ['lspci', '-k'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            if result.returncode == 0:
                if 'Intel Corporation' in result.stdout and ('Graphics' in result.stdout or 'VGA' in result.stdout):
                    logger.info(f"检测到Intel GPU")
                    return True
                    
            # 检查i915驱动
            if os.path.exists('/dev/dri'):
                logger.info(f"检测到DRI设备，可能支持Intel QSV")
                return True
        except Exception as e:
            logger.debug(f"Intel QSV检测错误: {e}")
    
    elif sys.platform == 'darwin':
        # macOS上，如果是Intel CPU，通常支持QSV
        if platform.processor() == 'i386':
            logger.info(f"在macOS上检测到Intel CPU，可能支持QSV")
            return True
    
    return False


def get_cuda_device_info():
    """获取CUDA设备信息
    
    详细获取CUDA设备信息，包括设备名称、CUDA版本、计算能力等
    
    Returns:
        Dict[str, Any]: CUDA设备信息
    """
    info = {
        "available": False,
        "devices": [],
        "cuda_version": None,
        "driver_version": None
    }
    
    try:
        import torch
        if torch.cuda.is_available():
            info["available"] = True
            info["cuda_version"] = torch.version.cuda
            device_count = torch.cuda.device_count()
            
            for i in range(device_count):
                device_props = {
                    "name": torch.cuda.get_device_name(i),
                    "index": i,
                    "total_memory_mb": torch.cuda.get_device_properties(i).total_memory / (1024 * 1024),
                    "capability": f"{torch.cuda.get_device_capability(i)[0]}.{torch.cuda.get_device_capability(i)[1]}"
                }
                info["devices"].append(device_props)
            
            # 尝试获取驱动版本
            try:
                import pynvml
                pynvml.nvmlInit()
                info["driver_version"] = pynvml.nvmlSystemGetDriverVersion().decode('utf-8')
                pynvml.nvmlShutdown()
            except Exception:
                pass
    except ImportError:
        try:
            # 尝试使用subprocess调用nvidia-smi
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=name,memory.total,driver_version,cuda_version', '--format=csv,noheader,nounits'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            if result.returncode == 0 and result.stdout.strip():
                info["available"] = True
                lines = result.stdout.strip().split('\n')
                
                for i, line in enumerate(lines):
                    parts = line.split(', ')
                    if len(parts) >= 4:
                        device_props = {
                            "name": parts[0],
                            "index": i,
                            "total_memory_mb": float(parts[1]),
                            "capability": "unknown"
                        }
                        info["devices"].append(device_props)
                
                if info["devices"]:
                    info["driver_version"] = parts[2]
                    info["cuda_version"] = parts[3]
        except Exception as e:
            logger.debug(f"获取CUDA信息错误: {e}")
    
    return info


def get_detected_acceleration():
    """获取系统检测到的所有加速方案
    
    全面检测系统中可用的硬件加速方案
    
    Returns:
        Dict[AccelerationType, bool]: 加速方案可用性字典
    """
    acceleration = {t: False for t in AccelerationType}
    
    # 检测NVIDIA支持
    has_nvidia = check_nvidia_support()
    acceleration[AccelerationType.NVIDIA_CUDA] = has_nvidia
    acceleration[AccelerationType.NVIDIA_NVENC] = has_nvidia
    acceleration[AccelerationType.NVIDIA_NVDEC] = has_nvidia
    
    # 检测Intel支持
    has_intel_qsv = check_intel_qsv()
    acceleration[AccelerationType.INTEL_QSV] = has_intel_qsv
    acceleration[AccelerationType.INTEL_MFX] = has_intel_qsv
    
    # 检测AMD支持
    # 此处省略AMD支持检测代码，实际使用时需要补充
    
    # 检测通用计算加速
    acceleration[AccelerationType.OPENCL] = check_opencl_support()
    acceleration[AccelerationType.VULKAN] = check_vulkan_support()
    
    # 检测CPU加速指令集
    acceleration[AccelerationType.CPU_AVX] = check_cpu_feature('avx')
    acceleration[AccelerationType.CPU_AVX2] = check_cpu_feature('avx2')
    
    # 零拷贝支持(至少有一种硬件加速时可用)
    acceleration[AccelerationType.ZERO_COPY] = (
        acceleration[AccelerationType.NVIDIA_CUDA] or 
        acceleration[AccelerationType.INTEL_QSV]
    )
    
    return acceleration


def check_opencl_support():
    """检测OpenCL支持
    
    检测系统是否支持OpenCL通用计算
    
    Returns:
        bool: 是否支持
    """
    try:
        import pyopencl
        platforms = pyopencl.get_platforms()
        if platforms:
            logger.info(f"检测到OpenCL平台: {[p.name for p in platforms]}")
            return True
    except ImportError:
        pass
    except Exception as e:
        logger.debug(f"OpenCL检测错误: {e}")
    
    return False


def check_vulkan_support():
    """检测Vulkan支持
    
    检测系统是否支持Vulkan计算
    
    Returns:
        bool: 是否支持
    """
    if sys.platform == 'win32':
        try:
            # 检查vulkaninfo
            result = subprocess.run(
                ['vulkaninfo'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=True
            )
            if result.returncode == 0:
                return True
        except Exception:
            pass
    
    elif sys.platform == 'linux':
        try:
            # 检查vulkaninfo
            result = subprocess.run(
                ['vulkaninfo'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            if result.returncode == 0:
                return True
        except Exception:
            pass
    
    return False


def check_cpu_feature(feature):
    """检测CPU特性
    
    检测CPU是否支持特定指令集
    
    Args:
        feature: 指令集名称，如'avx', 'avx2'等
        
    Returns:
        bool: 是否支持
    """
    if sys.platform == 'win32':
        try:
            # Windows上，尝试通过Python检测
            import cpuinfo
            info = cpuinfo.get_cpu_info()
            if 'flags' in info and feature.lower() in [f.lower() for f in info['flags']]:
                return True
        except ImportError:
            pass
    
    elif sys.platform == 'linux':
        try:
            # Linux上，从/proc/cpuinfo检测
            with open('/proc/cpuinfo', 'r') as f:
                for line in f:
                    if line.startswith('flags'):
                        flags = line.split(':')[1].strip().split()
                        if feature.lower() in [f.lower() for f in flags]:
                            return True
        except Exception:
            pass
    
    elif sys.platform == 'darwin':
        try:
            # macOS上，使用sysctl
            result = subprocess.run(
                ['sysctl', '-a'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            if result.returncode == 0:
                if feature.lower() in result.stdout.lower():
                    return True
        except Exception:
            pass
    
    return False


def print_acceleration_report():
    """打印加速能力报告
    
    生成并打印系统硬件加速能力的详细报告
    """
    logger.info("======== 硬件加速能力报告 ========")
    
    # 获取检测结果
    acceleration = get_detected_acceleration()
    
    # 打印系统信息
    logger.info(f"系统: {platform.system()} {platform.release()}")
    logger.info(f"处理器: {platform.processor()}")
    
    # 打印硬件加速支持情况
    for accel_type, supported in acceleration.items():
        status = "✓ 支持" if supported else "✗ 不支持"
        logger.info(f"{accel_type.name}: {status}")
    
    # 如果有NVIDIA CUDA，打印详细信息
    if acceleration[AccelerationType.NVIDIA_CUDA]:
        cuda_info = get_cuda_device_info()
        logger.info("\nCUDA设备详情:")
        logger.info(f"CUDA版本: {cuda_info.get('cuda_version', '未知')}")
        logger.info(f"驱动版本: {cuda_info.get('driver_version', '未知')}")
        
        for i, device in enumerate(cuda_info.get('devices', [])):
            logger.info(f"\n设备 #{i}: {device.get('name', '未知')}")
            logger.info(f"  内存: {device.get('total_memory_mb', 0):.0f} MB")
            logger.info(f"  计算能力: {device.get('capability', '未知')}")
    
    logger.info("\n推荐加速方案:")
    if acceleration[AccelerationType.NVIDIA_CUDA]:
        logger.info("- NVIDIA CUDA/NVDEC (最佳选择)")
    elif acceleration[AccelerationType.INTEL_QSV]:
        logger.info("- Intel Quick Sync Video")
    elif acceleration[AccelerationType.CPU_AVX2]:
        logger.info("- CPU AVX2 指令集加速")
    else:
        logger.info("- 标准CPU处理 (无硬件加速)")
    
    logger.info("====================================")


if __name__ == "__main__":
    # 直接运行时，打印硬件加速报告
    print_acceleration_report() 