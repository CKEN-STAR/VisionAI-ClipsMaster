#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
安全GPU检测模块

此模块提供安全的GPU检测功能，当nvidia_smi或其他GPU检测工具不可用时，
能够优雅地回退到CPU模式，确保系统正常启动和运行。

主要功能：
1. 多种GPU检测方法的安全封装
2. 优雅的错误处理和回退机制
3. 详细的日志记录
4. 性能监控和状态报告
"""

import os
import sys
import subprocess
import logging
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

# 配置日志
logger = logging.getLogger(__name__)

class SafeGPUDetector:
    """安全GPU检测器
    
    提供多种GPU检测方法，当某种方法失败时自动尝试其他方法，
    最终优雅回退到CPU模式。
    """
    
    def __init__(self):
        """初始化GPU检测器"""
        self.detection_methods = [
            self._detect_via_torch,
            self._detect_via_nvidia_smi,
            self._detect_via_pynvml,
            self._detect_via_gputil,
            self._detect_via_tensorflow
        ]
        
        self.gpu_info = {
            "available": False,
            "device_count": 0,
            "devices": [],
            "detection_method": None,
            "fallback_reason": None
        }
        
        logger.info("SafeGPUDetector初始化完成")

    def detect_gpus(self) -> Dict[str, Any]:
        """安全检测GPU设备
        
        尝试多种检测方法，确保在任何环境下都能正常工作。
        
        Returns:
            Dict[str, Any]: GPU检测结果
        """
        logger.info("开始安全GPU检测...")
        
        # 重置检测结果
        self.gpu_info = {
            "available": False,
            "device_count": 0,
            "devices": [],
            "detection_method": None,
            "fallback_reason": None
        }
        
        # 依次尝试各种检测方法
        for method in self.detection_methods:
            try:
                logger.debug(f"尝试检测方法: {method.__name__}")
                success = method()
                
                if success:
                    self.gpu_info["detection_method"] = method.__name__
                    logger.info(f"GPU检测成功，使用方法: {method.__name__}")
                    logger.info(f"检测到 {self.gpu_info['device_count']} 个GPU设备")
                    return self.gpu_info
                    
            except Exception as e:
                logger.debug(f"检测方法 {method.__name__} 失败: {e}")
                continue
        
        # 所有方法都失败，记录回退原因
        self.gpu_info["fallback_reason"] = "所有GPU检测方法都失败，回退到CPU模式"
        logger.warning("未检测到可用GPU，系统将使用CPU模式运行")
        
        return self.gpu_info

    def _detect_via_torch(self) -> bool:
        """使用PyTorch检测GPU
        
        Returns:
            bool: 检测是否成功
        """
        try:
            import torch
            
            if not hasattr(torch, 'cuda'):
                logger.debug("PyTorch未编译CUDA支持")
                return False
                
            if not torch.cuda.is_available():
                logger.debug("PyTorch报告CUDA不可用")
                return False
            
            device_count = torch.cuda.device_count()
            if device_count == 0:
                logger.debug("PyTorch检测到0个CUDA设备")
                return False
            
            # 获取设备信息
            devices = []
            for i in range(device_count):
                try:
                    device_name = torch.cuda.get_device_name(i)
                    device_props = torch.cuda.get_device_properties(i)
                    
                    devices.append({
                        "id": i,
                        "name": device_name,
                        "memory_total": device_props.total_memory,
                        "memory_free": device_props.total_memory - torch.cuda.memory_allocated(i),
                        "compute_capability": f"{device_props.major}.{device_props.minor}",
                        "multiprocessor_count": device_props.multi_processor_count
                    })
                    
                except Exception as e:
                    logger.debug(f"获取设备 {i} 信息失败: {e}")
                    devices.append({
                        "id": i,
                        "name": f"CUDA设备 {i}",
                        "memory_total": 0,
                        "memory_free": 0,
                        "error": str(e)
                    })
            
            self.gpu_info.update({
                "available": True,
                "device_count": device_count,
                "devices": devices
            })
            
            return True
            
        except ImportError:
            logger.debug("PyTorch未安装")
            return False
        except Exception as e:
            logger.debug(f"PyTorch GPU检测异常: {e}")
            return False

    def _detect_via_nvidia_smi(self) -> bool:
        """使用nvidia-smi命令检测GPU
        
        Returns:
            bool: 检测是否成功
        """
        try:
            # 检查nvidia-smi是否可用
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,memory.total,memory.free,memory.used", 
                 "--format=csv,noheader,nounits"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                logger.debug(f"nvidia-smi返回错误代码: {result.returncode}")
                return False
            
            if not result.stdout.strip():
                logger.debug("nvidia-smi输出为空")
                return False
            
            # 解析输出
            devices = []
            lines = result.stdout.strip().split('\n')
            
            for i, line in enumerate(lines):
                try:
                    parts = [part.strip() for part in line.split(',')]
                    if len(parts) >= 4:
                        devices.append({
                            "id": i,
                            "name": parts[0],
                            "memory_total": int(parts[1]) * 1024 * 1024,  # 转换为字节
                            "memory_free": int(parts[2]) * 1024 * 1024,
                            "memory_used": int(parts[3]) * 1024 * 1024
                        })
                except (ValueError, IndexError) as e:
                    logger.debug(f"解析nvidia-smi输出行失败: {line}, 错误: {e}")
                    continue
            
            if not devices:
                logger.debug("nvidia-smi未检测到有效GPU设备")
                return False
            
            self.gpu_info.update({
                "available": True,
                "device_count": len(devices),
                "devices": devices
            })
            
            return True
            
        except FileNotFoundError:
            logger.debug("nvidia-smi命令不存在")
            return False
        except subprocess.TimeoutExpired:
            logger.debug("nvidia-smi命令超时")
            return False
        except Exception as e:
            logger.debug(f"nvidia-smi检测异常: {e}")
            return False

    def _detect_via_pynvml(self) -> bool:
        """使用pynvml库检测GPU（安全版本）

        Returns:
            bool: 检测是否成功
        """
        try:
            # 尝试导入pynvml，如果失败则跳过
            try:
                import pynvml
            except ImportError:
                logger.debug("pynvml库未安装")
                return False

            # 安全初始化NVML
            try:
                pynvml.nvmlInit()
            except Exception as e:
                logger.debug(f"NVML初始化失败: {e}")
                return False

            device_count = pynvml.nvmlDeviceGetCount()

            if device_count == 0:
                logger.debug("pynvml检测到0个设备")
                return False

            devices = []
            for i in range(device_count):
                try:
                    handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                    name = pynvml.nvmlDeviceGetName(handle).decode('utf-8')
                    memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)

                    devices.append({
                        "id": i,
                        "name": name,
                        "memory_total": memory_info.total,
                        "memory_free": memory_info.free,
                        "memory_used": memory_info.used
                    })
                    
                except Exception as e:
                    logger.debug(f"获取pynvml设备 {i} 信息失败: {e}")
                    continue
            
            if not devices:
                logger.debug("pynvml未获取到有效设备信息")
                return False
            
            self.gpu_info.update({
                "available": True,
                "device_count": len(devices),
                "devices": devices
            })
            
            return True
            
        except ImportError:
            logger.debug("pynvml库未安装")
            return False
        except Exception as e:
            logger.debug(f"pynvml检测异常: {e}")
            return False

    def _detect_via_gputil(self) -> bool:
        """使用GPUtil库检测GPU
        
        Returns:
            bool: 检测是否成功
        """
        try:
            import GPUtil
            
            gpus = GPUtil.getGPUs()
            
            if not gpus:
                logger.debug("GPUtil未检测到GPU设备")
                return False
            
            devices = []
            for i, gpu in enumerate(gpus):
                devices.append({
                    "id": i,
                    "name": gpu.name,
                    "memory_total": gpu.memoryTotal * 1024 * 1024,  # 转换为字节
                    "memory_free": gpu.memoryFree * 1024 * 1024,
                    "memory_used": gpu.memoryUsed * 1024 * 1024,
                    "load": gpu.load,
                    "temperature": gpu.temperature
                })
            
            self.gpu_info.update({
                "available": True,
                "device_count": len(devices),
                "devices": devices
            })
            
            return True
            
        except ImportError:
            logger.debug("GPUtil库未安装")
            return False
        except Exception as e:
            logger.debug(f"GPUtil检测异常: {e}")
            return False

    def _detect_via_tensorflow(self) -> bool:
        """使用TensorFlow检测GPU
        
        Returns:
            bool: 检测是否成功
        """
        try:
            import tensorflow as tf
            
            # 抑制TensorFlow日志
            tf.get_logger().setLevel('ERROR')
            
            gpus = tf.config.experimental.list_physical_devices('GPU')
            
            if not gpus:
                logger.debug("TensorFlow未检测到GPU设备")
                return False
            
            devices = []
            for i, gpu in enumerate(gpus):
                devices.append({
                    "id": i,
                    "name": gpu.name,
                    "device_type": gpu.device_type,
                    "memory_total": "未知",  # TensorFlow不直接提供内存信息
                    "memory_free": "未知",
                    "memory_used": "未知"
                })
            
            self.gpu_info.update({
                "available": True,
                "device_count": len(devices),
                "devices": devices
            })
            
            return True
            
        except ImportError:
            logger.debug("TensorFlow未安装")
            return False
        except Exception as e:
            logger.debug(f"TensorFlow检测异常: {e}")
            return False

    def get_best_device(self) -> str:
        """获取最佳计算设备
        
        Returns:
            str: 设备名称 ('cuda', 'cpu')
        """
        if self.gpu_info["available"] and self.gpu_info["device_count"] > 0:
            return "cuda"
        else:
            return "cpu"

    def get_device_summary(self) -> Dict[str, Any]:
        """获取设备检测摘要
        
        Returns:
            Dict[str, Any]: 设备摘要信息
        """
        return {
            "gpu_available": self.gpu_info["available"],
            "device_count": self.gpu_info["device_count"],
            "detection_method": self.gpu_info["detection_method"],
            "fallback_reason": self.gpu_info["fallback_reason"],
            "recommended_device": self.get_best_device(),
            "cpu_fallback_ready": True
        }


def safe_gpu_detection() -> Tuple[bool, Dict[str, Any]]:
    """安全的GPU检测函数
    
    这是一个便捷函数，用于快速进行GPU检测。
    
    Returns:
        Tuple[bool, Dict[str, Any]]: (是否检测到GPU, 详细信息)
    """
    detector = SafeGPUDetector()
    gpu_info = detector.detect_gpus()
    return gpu_info["available"], gpu_info


def get_safe_device() -> str:
    """获取安全的计算设备
    
    Returns:
        str: 设备名称 ('cuda' 或 'cpu')
    """
    detector = SafeGPUDetector()
    detector.detect_gpus()
    return detector.get_best_device()


if __name__ == "__main__":
    # 测试GPU检测功能
    print("=== 安全GPU检测测试 ===")
    
    detector = SafeGPUDetector()
    gpu_info = detector.detect_gpus()
    
    print(f"GPU可用: {gpu_info['available']}")
    print(f"设备数量: {gpu_info['device_count']}")
    print(f"检测方法: {gpu_info['detection_method']}")
    print(f"推荐设备: {detector.get_best_device()}")
    
    if gpu_info['fallback_reason']:
        print(f"回退原因: {gpu_info['fallback_reason']}")
    
    print("\n设备摘要:")
    summary = detector.get_device_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")
