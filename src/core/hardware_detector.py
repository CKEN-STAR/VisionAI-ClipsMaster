#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
硬件检测与分析模块
自动检测系统硬件配置，评估性能等级，为自适应模型配置提供基础数据
"""

import os
import sys
import platform
import psutil
import logging
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# 尝试导入GPU检测库
try:
    import GPUtil
    GPU_UTIL_AVAILABLE = True
except ImportError:
    GPU_UTIL_AVAILABLE = False

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

logger = logging.getLogger(__name__)


class PerformanceLevel(Enum):
    """设备性能等级"""
    LOW = "low"          # 低配设备 (4GB RAM, 无独显)
    MEDIUM = "medium"    # 中配设备 (8GB RAM, 集成显卡)
    HIGH = "high"        # 高配设备 (16GB+ RAM, 独立显卡)
    ULTRA = "ultra"      # 超高配设备 (32GB+ RAM, 高端显卡)


class GPUType(Enum):
    """GPU类型"""
    NONE = "none"
    INTEGRATED = "integrated"
    NVIDIA = "nvidia"
    AMD = "amd"
    INTEL = "intel"


@dataclass
class HardwareInfo:
    """硬件信息数据类"""
    # 内存信息
    total_memory_gb: float
    available_memory_gb: float
    memory_usage_percent: float
    
    # CPU信息
    cpu_count: int
    cpu_freq_mhz: float
    cpu_architecture: str
    cpu_brand: str
    
    # GPU信息
    gpu_type: GPUType
    gpu_count: int
    gpu_memory_gb: float
    gpu_names: list
    
    # 系统信息
    os_type: str
    os_version: str
    python_version: str
    
    # 性能评级
    performance_level: PerformanceLevel
    memory_tier: str
    compute_tier: str
    
    # 推荐配置
    recommended_quantization: str
    max_model_memory_gb: float
    concurrent_models: int


class HardwareDetector:
    """硬件检测器"""
    
    def __init__(self):
        """初始化硬件检测器"""
        self.logger = logging.getLogger(__name__)
        
    def detect_hardware(self) -> HardwareInfo:
        """检测硬件配置"""
        try:
            self.logger.info("开始检测硬件配置...")
            
            # 检测内存
            memory_info = self._detect_memory()
            
            # 检测CPU
            cpu_info = self._detect_cpu()
            
            # 检测GPU
            gpu_info = self._detect_gpu()
            
            # 检测系统信息
            system_info = self._detect_system()
            
            # 评估性能等级
            performance_level = self._evaluate_performance_level(
                memory_info, cpu_info, gpu_info
            )
            
            # 生成推荐配置
            recommendations = self._generate_recommendations(
                memory_info, cpu_info, gpu_info, performance_level
            )
            
            # 构建硬件信息对象
            hardware_info = HardwareInfo(
                # 内存信息
                total_memory_gb=memory_info["total_gb"],
                available_memory_gb=memory_info["available_gb"],
                memory_usage_percent=memory_info["usage_percent"],
                
                # CPU信息
                cpu_count=cpu_info["count"],
                cpu_freq_mhz=cpu_info["freq_mhz"],
                cpu_architecture=cpu_info["architecture"],
                cpu_brand=cpu_info["brand"],
                
                # GPU信息
                gpu_type=gpu_info["type"],
                gpu_count=gpu_info["count"],
                gpu_memory_gb=gpu_info["memory_gb"],
                gpu_names=gpu_info["names"],
                
                # 系统信息
                os_type=system_info["os_type"],
                os_version=system_info["os_version"],
                python_version=system_info["python_version"],
                
                # 性能评级
                performance_level=performance_level,
                memory_tier=recommendations["memory_tier"],
                compute_tier=recommendations["compute_tier"],
                
                # 推荐配置
                recommended_quantization=recommendations["quantization"],
                max_model_memory_gb=recommendations["max_model_memory"],
                concurrent_models=recommendations["concurrent_models"]
            )
            
            self.logger.info(f"硬件检测完成 - 性能等级: {performance_level.value}")
            return hardware_info
            
        except Exception as e:
            self.logger.error(f"硬件检测失败: {e}")
            # 返回默认的低配配置
            return self._get_default_low_config()
    
    def _detect_memory(self) -> Dict[str, Any]:
        """检测内存信息"""
        try:
            memory = psutil.virtual_memory()
            return {
                "total_gb": round(memory.total / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "used_gb": round(memory.used / (1024**3), 2),
                "usage_percent": memory.percent
            }
        except Exception as e:
            self.logger.error(f"内存检测失败: {e}")
            return {"total_gb": 4.0, "available_gb": 2.0, "used_gb": 2.0, "usage_percent": 50.0}
    
    def _detect_cpu(self) -> Dict[str, Any]:
        """检测CPU信息"""
        try:
            cpu_freq = psutil.cpu_freq()
            cpu_count = psutil.cpu_count()
            
            # 获取CPU架构和品牌信息
            architecture = platform.machine()
            processor = platform.processor()
            
            return {
                "count": cpu_count,
                "freq_mhz": cpu_freq.current if cpu_freq else 2000.0,
                "architecture": architecture,
                "brand": processor if processor else "Unknown"
            }
        except Exception as e:
            self.logger.error(f"CPU检测失败: {e}")
            return {"count": 4, "freq_mhz": 2000.0, "architecture": "x86_64", "brand": "Unknown"}
    
    def _detect_gpu(self) -> Dict[str, Any]:
        """检测GPU信息"""
        try:
            gpu_info = {
                "type": GPUType.NONE,
                "count": 0,
                "memory_gb": 0.0,
                "names": []
            }
            
            # 检测NVIDIA GPU
            if GPU_UTIL_AVAILABLE:
                try:
                    gpus = GPUtil.getGPUs()
                    if gpus:
                        gpu_info["type"] = GPUType.NVIDIA
                        gpu_info["count"] = len(gpus)
                        gpu_info["memory_gb"] = sum(gpu.memoryTotal / 1024 for gpu in gpus)
                        gpu_info["names"] = [gpu.name for gpu in gpus]
                        return gpu_info
                except:
                    pass
            
            # 检测PyTorch CUDA支持
            if TORCH_AVAILABLE:
                try:
                    if torch.cuda.is_available():
                        gpu_count = torch.cuda.device_count()
                        if gpu_count > 0:
                            gpu_info["type"] = GPUType.NVIDIA
                            gpu_info["count"] = gpu_count
                            gpu_info["names"] = [torch.cuda.get_device_name(i) for i in range(gpu_count)]
                            # 估算显存
                            gpu_info["memory_gb"] = gpu_count * 8.0  # 估算值
                            return gpu_info
                except:
                    pass
            
            # 检测集成显卡（通过系统信息推断）
            if "intel" in platform.processor().lower():
                gpu_info["type"] = GPUType.INTEL
                gpu_info["count"] = 1
                gpu_info["names"] = ["Intel Integrated Graphics"]
            
            return gpu_info
            
        except Exception as e:
            self.logger.error(f"GPU检测失败: {e}")
            return {"type": GPUType.NONE, "count": 0, "memory_gb": 0.0, "names": []}
    
    def _detect_system(self) -> Dict[str, Any]:
        """检测系统信息"""
        try:
            return {
                "os_type": platform.system(),
                "os_version": platform.version(),
                "python_version": sys.version.split()[0]
            }
        except Exception as e:
            self.logger.error(f"系统信息检测失败: {e}")
            return {"os_type": "Unknown", "os_version": "Unknown", "python_version": "3.11"}

    def _evaluate_performance_level(self, memory_info: Dict, cpu_info: Dict, gpu_info: Dict) -> PerformanceLevel:
        """评估设备性能等级"""
        try:
            total_memory = memory_info["total_gb"]
            cpu_count = cpu_info["count"]
            cpu_freq = cpu_info["freq_mhz"]
            gpu_type = gpu_info["type"]
            gpu_memory = gpu_info["memory_gb"]

            # 计算性能分数
            memory_score = self._calculate_memory_score(total_memory)
            cpu_score = self._calculate_cpu_score(cpu_count, cpu_freq)
            gpu_score = self._calculate_gpu_score(gpu_type, gpu_memory)

            # 综合评分
            total_score = memory_score + cpu_score + gpu_score

            # 根据分数确定性能等级
            if total_score >= 80:
                return PerformanceLevel.ULTRA
            elif total_score >= 60:
                return PerformanceLevel.HIGH
            elif total_score >= 40:
                return PerformanceLevel.MEDIUM
            else:
                return PerformanceLevel.LOW

        except Exception as e:
            self.logger.error(f"性能等级评估失败: {e}")
            return PerformanceLevel.LOW

    def _calculate_memory_score(self, total_memory_gb: float) -> int:
        """计算内存分数"""
        if total_memory_gb >= 32:
            return 30
        elif total_memory_gb >= 16:
            return 25
        elif total_memory_gb >= 8:
            return 20
        elif total_memory_gb >= 4:
            return 15
        else:
            return 10

    def _calculate_cpu_score(self, cpu_count: int, cpu_freq_mhz: float) -> int:
        """计算CPU分数"""
        # CPU核心数分数
        core_score = min(cpu_count * 2, 20)  # 最多20分

        # CPU频率分数
        freq_score = 0
        if cpu_freq_mhz >= 3000:
            freq_score = 15
        elif cpu_freq_mhz >= 2500:
            freq_score = 12
        elif cpu_freq_mhz >= 2000:
            freq_score = 10
        else:
            freq_score = 8

        return core_score + freq_score

    def _calculate_gpu_score(self, gpu_type: GPUType, gpu_memory_gb: float) -> int:
        """计算GPU分数"""
        if gpu_type == GPUType.NVIDIA:
            if gpu_memory_gb >= 16:
                return 25
            elif gpu_memory_gb >= 8:
                return 20
            elif gpu_memory_gb >= 4:
                return 15
            else:
                return 10
        elif gpu_type == GPUType.AMD:
            return 15  # AMD GPU基础分数
        elif gpu_type == GPUType.INTEL:
            return 8   # 集成显卡分数
        else:
            return 0   # 无GPU

    def _generate_recommendations(self, memory_info: Dict, cpu_info: Dict,
                                gpu_info: Dict, performance_level: PerformanceLevel) -> Dict[str, Any]:
        """生成推荐配置"""
        try:
            total_memory = memory_info["total_gb"]
            available_memory = memory_info["available_gb"]

            # 根据性能等级生成推荐配置
            if performance_level == PerformanceLevel.ULTRA:
                return {
                    "memory_tier": "ultra",
                    "compute_tier": "ultra",
                    "quantization": "Q5_K",
                    "max_model_memory": min(total_memory * 0.6, 12.0),
                    "concurrent_models": 2
                }
            elif performance_level == PerformanceLevel.HIGH:
                return {
                    "memory_tier": "high",
                    "compute_tier": "high",
                    "quantization": "Q4_K_M",
                    "max_model_memory": min(total_memory * 0.5, 8.0),
                    "concurrent_models": 2
                }
            elif performance_level == PerformanceLevel.MEDIUM:
                return {
                    "memory_tier": "medium",
                    "compute_tier": "medium",
                    "quantization": "Q4_K_M",
                    "max_model_memory": min(total_memory * 0.4, 6.0),
                    "concurrent_models": 1
                }
            else:  # LOW
                return {
                    "memory_tier": "low",
                    "compute_tier": "low",
                    "quantization": "Q2_K",
                    "max_model_memory": min(total_memory * 0.8, 3.5),
                    "concurrent_models": 1
                }

        except Exception as e:
            self.logger.error(f"推荐配置生成失败: {e}")
            return self._get_default_recommendations()

    def _get_default_low_config(self) -> HardwareInfo:
        """获取默认低配配置"""
        return HardwareInfo(
            total_memory_gb=4.0,
            available_memory_gb=2.0,
            memory_usage_percent=50.0,
            cpu_count=4,
            cpu_freq_mhz=2000.0,
            cpu_architecture="x86_64",
            cpu_brand="Unknown",
            gpu_type=GPUType.NONE,
            gpu_count=0,
            gpu_memory_gb=0.0,
            gpu_names=[],
            os_type="Windows",
            os_version="Unknown",
            python_version="3.11",
            performance_level=PerformanceLevel.LOW,
            memory_tier="low",
            compute_tier="low",
            recommended_quantization="Q2_K",
            max_model_memory_gb=3.2,
            concurrent_models=1
        )

    def _get_default_recommendations(self) -> Dict[str, Any]:
        """获取默认推荐配置"""
        return {
            "memory_tier": "low",
            "compute_tier": "low",
            "quantization": "Q2_K",
            "max_model_memory": 3.2,
            "concurrent_models": 1
        }


if __name__ == "__main__":
    # 测试硬件检测
    detector = HardwareDetector()
    hardware_info = detector.detect_hardware()
    print(f"检测到的硬件配置: {hardware_info}")
