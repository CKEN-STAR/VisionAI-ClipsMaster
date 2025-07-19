"""混合设备管理模块

此模块负责管理和调度不同计算设备，主要功能包括：
1. 设备特性检测
2. 智能设备选择
3. 负载均衡
4. 性能监控
5. 资源调度
"""

import os
import torch
import psutil
import platform
from enum import Enum
from typing import Dict, List, Optional, Union, Any
from loguru import logger

from src.utils.vram_detector import VRAMDetector
from src.utils.cpu_feature import CPUFeatureDetector
from src.utils.gpu_detector import SafeGPUDetector

class DeviceType(Enum):
    """设备类型枚举"""
    CPU_BASIC = "cpu-basic"     # 基础CPU模式
    CPU_AVX2 = "cpu-avx2"      # 支持AVX2的CPU模式
    CUDA = "cuda"              # NVIDIA GPU模式
    MPS = "mps"               # Apple Silicon GPU模式
    AUTO = "auto"             # 自动选择最佳设备

class HybridDevice:
    """混合设备管理器"""
    
    def __init__(self, min_vram: int = 4 * 1024 * 1024 * 1024):  # 默认最小4GB显存
        """初始化混合设备管理器

        Args:
            min_vram: 最小显存要求（字节）
        """
        self.min_vram = min_vram
        self.system = platform.system()
        self.vram_detector = VRAMDetector()
        self.cpu_detector = CPUFeatureDetector()
        self.gpu_detector = SafeGPUDetector()

        # 使用SafeGPUDetector进行完全安全的GPU检测
        try:
            gpu_info = self.gpu_detector.detect_gpus()
            self.gpu_available = gpu_info["available"]
            self.gpu_devices = gpu_info["devices"]
            self.gpu_detection_method = gpu_info.get("detection_method", "unknown")
            logger.info(f"GPU检测完成: 可用={self.gpu_available}, 设备数={gpu_info['device_count']}, 方法={self.gpu_detection_method}")
        except Exception as e:
            logger.warning(f"GPU检测失败，回退到CPU模式: {e}")
            self.gpu_available = False
            self.gpu_devices = []
            self.gpu_detection_method = "failed"

        # 安全检测Apple Silicon MPS
        try:
            self.mps_available = (
                hasattr(torch.backends, "mps") and
                torch.backends.mps.is_available()
            )
            if self.mps_available:
                logger.info("检测到Apple Silicon MPS支持")
        except Exception as e:
            logger.debug(f"MPS检测失败: {e}")
            self.mps_available = False
        
        # 获取CPU信息
        self.cpu_features = self.cpu_detector.check_instruction_sets()
        self.cpu_cores = psutil.cpu_count(logical=False)
        self.cpu_threads = psutil.cpu_count(logical=True)
        
        # 初始化设备状态
        self.current_device = None
        self.device_stats = {}
        self.update_device_stats()
        
    def update_device_stats(self):
        """更新设备状态信息"""
        try:
            stats = {
                "cpu": {
                    "cores": self.cpu_cores,
                    "threads": self.cpu_threads,
                    "features": self.cpu_features,
                    "usage": psutil.cpu_percent(interval=0.1),
                    "memory": psutil.virtual_memory().percent
                }
            }
            
            # GPU状态
            if self.gpu_available:
                gpu_info = self.vram_detector.get_all_devices_info()
                stats["gpu"] = {
                    "devices": gpu_info,
                    "primary": {
                        "vram_total": gpu_info[0]["total_memory"],
                        "vram_free": gpu_info[0]["free_memory"],
                        "vram_used": gpu_info[0]["used_memory"]
                    } if gpu_info else None
                }
            
            # Apple Silicon状态
            if self.mps_available:
                stats["mps"] = {
                    "available": True,
                    "platform": "Apple Silicon"
                }
                
            self.device_stats = stats
            
        except Exception as e:
            logger.error(f"设备状态更新失败: {str(e)}")
    
    def select_device(self, 
                     preferred: Optional[DeviceType] = None,
                     model_size: Optional[int] = None) -> DeviceType:
        """智能选择最佳设备
        
        Args:
            preferred: 优先使用的设备类型
            model_size: 模型大小（字节）
            
        Returns:
            DeviceType: 选择的设备类型
        """
        try:
            self.update_device_stats()
            
            # 如果指定了优先设备且可用，直接返回
            if preferred and preferred != DeviceType.AUTO:
                if self._check_device_available(preferred, model_size):
                    self.current_device = preferred
                    return preferred
            
            # 自动选择最佳设备
            # 1. 首选具有足够显存的CUDA设备
            if (self.gpu_available and 
                self._check_device_available(DeviceType.CUDA, model_size)):
                self.current_device = DeviceType.CUDA
                return DeviceType.CUDA
            
            # 2. 其次选择Apple Silicon
            if (self.mps_available and 
                self._check_device_available(DeviceType.MPS, model_size)):
                self.current_device = DeviceType.MPS
                return DeviceType.MPS
            
            # 3. 最后选择CPU，优先使用AVX2
            if (self.cpu_features.get("avx2", False) and 
                self.cpu_cores >= 4):
                self.current_device = DeviceType.CPU_AVX2
                return DeviceType.CPU_AVX2
            
            # 4. 基础CPU模式
            self.current_device = DeviceType.CPU_BASIC
            return DeviceType.CPU_BASIC
            
        except Exception as e:
            logger.error(f"设备选择失败: {str(e)}")
            return DeviceType.CPU_BASIC
    
    def _check_device_available(self, 
                              device_type: DeviceType,
                              model_size: Optional[int] = None) -> bool:
        """检查设备是否可用
        
        Args:
            device_type: 设备类型
            model_size: 模型大小（字节）
            
        Returns:
            bool: 设备是否可用
        """
        try:
            if device_type == DeviceType.CUDA:
                if not self.gpu_available:
                    return False
                    
                # 检查显存
                if model_size:
                    free_vram = self.device_stats["gpu"]["primary"]["vram_free"]
                    return free_vram >= max(model_size * 1.5, self.min_vram)
                return True
                
            elif device_type == DeviceType.MPS:
                return self.mps_available
                
            elif device_type == DeviceType.CPU_AVX2:
                return (self.cpu_features.get("avx2", False) and 
                       self.cpu_cores >= 4)
                
            elif device_type == DeviceType.CPU_BASIC:
                return True
                
            return False
            
        except Exception:
            return False
    
    def get_device_info(self) -> Dict:
        """获取当前设备详细信息
        
        Returns:
            Dict: 设备信息
        """
        try:
            self.update_device_stats()
            
            info = {
                "current_device": self.current_device.value if self.current_device else None,
                "available_devices": self._get_available_devices(),
                "stats": self.device_stats,
                "recommendations": self._get_device_recommendations()
            }
            
            return info
            
        except Exception as e:
            logger.error(f"获取设备信息失败: {str(e)}")
            return {}
    
    def _get_available_devices(self) -> List[DeviceType]:
        """获取所有可用设备列表"""
        devices = [DeviceType.CPU_BASIC]
        
        if self.cpu_features.get("avx2", False) and self.cpu_cores >= 4:
            devices.append(DeviceType.CPU_AVX2)
            
        if self.gpu_available:
            devices.append(DeviceType.CUDA)
            
        if self.mps_available:
            devices.append(DeviceType.MPS)
            
        return devices
    
    def _get_device_recommendations(self) -> List[str]:
        """获取设备使用建议"""
        recommendations = []
        
        try:
            # CPU相关建议
            if not self.cpu_features.get("avx2", False):
                recommendations.append("推荐使用支持AVX2的CPU以提高性能")
            
            if self.cpu_cores < 4:
                recommendations.append("推荐使用4核或更多核心的CPU")
            
            # GPU相关建议
            if self.gpu_available:
                gpu_info = self.device_stats["gpu"]["primary"]
                if gpu_info["vram_total"] < self.min_vram:
                    recommendations.append(f"GPU显存小于推荐值{self.min_vram / 1024**3:.1f}GB")
            else:
                recommendations.append("推荐使用支持CUDA的NVIDIA GPU")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"生成设备建议失败: {str(e)}")
            return ["无法生成设备使用建议"]
    
    def optimize_device_settings(self) -> Dict:
        """优化当前设备设置
        
        Returns:
            Dict: 优化后的设置
        """
        try:
            settings = {
                "device_type": self.current_device,
                "num_threads": self._get_optimal_threads(),
                "batch_size": self._get_optimal_batch_size(),
                "memory_settings": self._get_memory_settings()
            }
            
            return settings
            
        except Exception as e:
            logger.error(f"设备设置优化失败: {str(e)}")
            return {}
    
    def _get_optimal_threads(self) -> int:
        """获取最优线程数"""
        if self.current_device in [DeviceType.CUDA, DeviceType.MPS]:
            return 2  # GPU模式下使用较少CPU线程
            
        return max(1, self.cpu_threads - 1)  # 预留一个线程给系统
    
    def _get_optimal_batch_size(self) -> int:
        """获取最优批处理大小"""
        if self.current_device == DeviceType.CUDA:
            gpu_info = self.device_stats["gpu"]["primary"]
            free_vram = gpu_info["vram_free"]
            # 根据可用显存估算，预留30%给计算过程
            return max(1, int((free_vram * 0.7) / (1024 * 1024 * 1024)))  # 每GB显存对应1的批大小
            
        elif self.current_device == DeviceType.MPS:
            return 4  # Apple Silicon默认批大小
            
        elif self.current_device == DeviceType.CPU_AVX2:
            return 2  # AVX2 CPU的默认批大小
            
        return 1  # 基础CPU模式使用最小批大小
    
    def _get_memory_settings(self) -> Dict:
        """获取内存相关设置"""
        settings = {
            "pin_memory": self.current_device == DeviceType.CUDA,
            "non_blocking": self.current_device in [DeviceType.CUDA, DeviceType.MPS],
            "num_workers": self._get_optimal_threads(),
            "prefetch_factor": 2 if self.current_device in [DeviceType.CUDA, DeviceType.MPS] else 1
        }
        
        return settings

    def detect_gpus(self) -> List[Dict]:
        """检测GPU设备（兼容性方法）

        Returns:
            List[Dict]: GPU设备列表
        """
        try:
            if hasattr(self, 'gpu_devices'):
                return self.gpu_devices
            else:
                gpu_info = self.gpu_detector.detect_gpus()
                return gpu_info.get("devices", [])
        except Exception as e:
            logger.error(f"GPU检测失败: {e}")
            return []

    def test_cpu_fallback(self) -> bool:
        """测试CPU回退功能

        Returns:
            bool: CPU回退是否可用
        """
        try:
            # 测试CPU基本功能
            import torch
            test_tensor = torch.tensor([1.0, 2.0, 3.0])
            result = test_tensor.sum()
            return result.item() == 6.0
        except Exception as e:
            logger.error(f"CPU回退测试失败: {e}")
            return False

    def get_gpu_detection_summary(self) -> Dict[str, Any]:
        """获取GPU检测摘要

        Returns:
            Dict[str, Any]: GPU检测摘要信息
        """
        try:
            return self.gpu_detector.get_device_summary()
        except Exception as e:
            logger.error(f"获取GPU检测摘要失败: {e}")
            return {
                "gpu_available": False,
                "device_count": 0,
                "detection_method": None,
                "fallback_reason": f"检测摘要获取失败: {e}",
                "recommended_device": "cpu",
                "cpu_fallback_ready": True
            }


# 设备管理器实例
DeviceManager = HybridDevice