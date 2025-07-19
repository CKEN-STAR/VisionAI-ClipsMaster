#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GPU检测器修复补丁

专门解决nvidia_smi模块缺失导致的GPU检测失败问题。
提供安全的GPU检测方法，确保系统在没有GPU或GPU检测工具缺失时能正常运行。
"""

import os
import sys
import logging
import subprocess
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

def safe_gpu_detection() -> Dict[str, Any]:
    """安全的GPU检测函数
    
    这个函数专门解决nvidia_smi模块缺失的问题，
    提供多种回退方案确保系统正常运行。
    
    Returns:
        Dict[str, Any]: GPU检测结果
    """
    result = {
        "available": False,
        "gpu_count": 0,
        "gpus": [],
        "detection_method": "none",
        "error": None,
        "fallback_to_cpu": True
    }
    
    # 方法1: 使用PyTorch检测（最可靠）
    try:
        import torch
        if hasattr(torch, 'cuda') and callable(getattr(torch.cuda, 'is_available', None)):
            if torch.cuda.is_available():
                device_count = torch.cuda.device_count()
                if device_count > 0:
                    gpus = []
                    for i in range(device_count):
                        try:
                            gpu_name = torch.cuda.get_device_name(i)
                            gpu_props = torch.cuda.get_device_properties(i)
                            gpus.append({
                                "id": i,
                                "name": gpu_name,
                                "memory_total": gpu_props.total_memory,
                                "compute_capability": f"{gpu_props.major}.{gpu_props.minor}"
                            })
                        except Exception as e:
                            logger.debug(f"获取GPU {i} 信息失败: {e}")
                            gpus.append({"id": i, "name": f"GPU {i}", "error": str(e)})
                    
                    result.update({
                        "available": True,
                        "gpu_count": device_count,
                        "gpus": gpus,
                        "detection_method": "pytorch",
                        "fallback_to_cpu": False
                    })
                    logger.info(f"✅ PyTorch检测到 {device_count} 个GPU")
                    return result
    except Exception as e:
        logger.debug(f"PyTorch GPU检测失败: {e}")
    
    # 方法2: 使用nvidia-smi命令（不依赖nvidia_smi模块）
    try:
        result_smi = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result_smi.returncode == 0 and result_smi.stdout.strip():
            lines = result_smi.stdout.strip().split('\n')
            gpus = []
            for i, line in enumerate(lines):
                parts = line.split(', ')
                if len(parts) >= 2:
                    gpus.append({
                        "id": i,
                        "name": parts[0].strip(),
                        "memory_total": f"{parts[1].strip()} MB"
                    })
            
            if gpus:
                result.update({
                    "available": True,
                    "gpu_count": len(gpus),
                    "gpus": gpus,
                    "detection_method": "nvidia-smi",
                    "fallback_to_cpu": False
                })
                logger.info(f"✅ nvidia-smi检测到 {len(gpus)} 个GPU")
                return result
                
    except Exception as e:
        logger.debug(f"nvidia-smi检测失败: {e}")
    
    # 方法3: 使用pynvml库（如果可用）
    try:
        import pynvml
        pynvml.nvmlInit()
        device_count = pynvml.nvmlDeviceGetCount()
        
        if device_count > 0:
            gpus = []
            for i in range(device_count):
                try:
                    handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                    name = pynvml.nvmlDeviceGetName(handle).decode('utf-8')
                    memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                    gpus.append({
                        "id": i,
                        "name": name,
                        "memory_total": memory_info.total,
                        "memory_free": memory_info.free
                    })
                except Exception as e:
                    logger.debug(f"获取pynvml设备 {i} 信息失败: {e}")
            
            if gpus:
                result.update({
                    "available": True,
                    "gpu_count": len(gpus),
                    "gpus": gpus,
                    "detection_method": "pynvml",
                    "fallback_to_cpu": False
                })
                logger.info(f"✅ pynvml检测到 {len(gpus)} 个GPU")
                return result
                
    except Exception as e:
        logger.debug(f"pynvml检测失败: {e}")
    
    # 所有方法都失败，但提供CPU模式作为成功的回退方案
    result["detection_method"] = "cpu_fallback"
    result["available"] = False  # GPU不可用
    result["fallback_to_cpu"] = True
    result["error"] = "未检测到GPU设备，已启用CPU模式"
    result["cpu_info"] = {
        "cores": os.cpu_count(),
        "architecture": "x86_64",
        "mode": "CPU推理模式"
    }
    logger.info("ℹ️ 未检测到GPU设备，系统将使用CPU模式运行（这是正常的回退行为）")
    return result

def get_gpu_detector():
    """获取GPU检测器实例
    
    Returns:
        SafeGPUDetector: GPU检测器实例
    """
    try:
        from src.utils.gpu_detector import SafeGPUDetector
        return SafeGPUDetector()
    except ImportError:
        # 如果导入失败，返回一个简单的检测结果
        class FallbackDetector:
            def detect_gpus(self):
                return safe_gpu_detection()
        return FallbackDetector()

def is_gpu_available() -> bool:
    """检查GPU是否可用
    
    Returns:
        bool: GPU是否可用
    """
    result = safe_gpu_detection()
    return result["available"]

def get_gpu_count() -> int:
    """获取GPU数量
    
    Returns:
        int: GPU数量
    """
    result = safe_gpu_detection()
    return result["gpu_count"]

def get_gpu_info() -> Dict[str, Any]:
    """获取GPU信息
    
    Returns:
        Dict[str, Any]: GPU信息
    """
    return safe_gpu_detection()

# 兼容性函数
def detect_gpu_info() -> Dict[str, Any]:
    """检测GPU信息（兼容性函数）
    
    Returns:
        Dict[str, Any]: GPU信息
    """
    result = safe_gpu_detection()
    return {
        "available": result["available"],
        "name": result["gpus"][0]["name"] if result["gpus"] else "未检测到GPU",
        "count": result["gpu_count"],
        "detection_method": result["detection_method"]
    }

if __name__ == "__main__":
    # 测试GPU检测
    print("测试GPU检测功能...")
    gpu_info = safe_gpu_detection()
    print(f"GPU可用: {gpu_info['available']}")
    print(f"GPU数量: {gpu_info['gpu_count']}")
    print(f"检测方法: {gpu_info['detection_method']}")
    if gpu_info['gpus']:
        for gpu in gpu_info['gpus']:
            print(f"  - {gpu['name']}")
