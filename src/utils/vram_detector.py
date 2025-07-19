"""显存精准检测模块

此模块负责精确检测和验证GPU显存状态，主要功能包括：
1. 实际可用显存检测
2. 显存碎片分析
3. 多GPU设备支持
4. 显存使用效率评估
"""

import torch
import numpy as np
from typing import Dict, List, Optional, Tuple
from loguru import logger

# 安全导入nvidia_smi，如果不可用则使用回退机制
try:
    import nvidia_smi
    NVIDIA_SMI_AVAILABLE = True
except ImportError:
    NVIDIA_SMI_AVAILABLE = False
    logger.warning("nvidia_smi不可用，将使用安全回退机制")

class VRAMDetector:
    """显存检测器"""
    
    def __init__(self):
        """初始化显存检测器 - 使用安全检测机制"""
        # 使用安全的GPU检测
        self.has_cuda = self._safe_cuda_detection()
        self.nvidia_smi_available = NVIDIA_SMI_AVAILABLE

        if self.has_cuda and self.nvidia_smi_available:
            try:
                nvidia_smi.nvmlInit()
                self.device_count = torch.cuda.device_count()
                logger.info("VRAM检测器初始化成功，nvidia_smi可用")
            except Exception as e:
                logger.warning(f"nvidia_smi初始化失败: {e}，使用基础CUDA检测")
                self.nvidia_smi_available = False
                self.device_count = torch.cuda.device_count() if self.has_cuda else 0
        elif self.has_cuda:
            # 只有CUDA可用，没有nvidia_smi
            self.device_count = torch.cuda.device_count()
            logger.info("VRAM检测器初始化成功，仅使用CUDA检测")
        else:
            self.device_count = 0
            logger.info("VRAM检测器初始化：无GPU设备")
            
    def __del__(self):
        """清理资源 - 安全清理"""
        if self.has_cuda and self.nvidia_smi_available:
            try:
                nvidia_smi.nvmlShutdown()
            except Exception:
                pass

    def _safe_cuda_detection(self) -> bool:
        """安全的CUDA检测"""
        try:
            return torch.cuda.is_available()
        except Exception as e:
            logger.warning(f"CUDA检测失败: {e}")
            return False

    def get_real_vram(self, device_index: int = 0) -> int:
        """获取实际可用显存大小 - 使用安全检测机制

        Args:
            device_index: GPU设备索引

        Returns:
            int: 实际可用显存大小（字节）
        """
        if not self.has_cuda or device_index >= self.device_count:
            return 0

        try:
            # 优先使用nvidia_smi获取理论显存大小
            total_memory = 0
            if self.nvidia_smi_available:
                try:
                    handle = nvidia_smi.nvmlDeviceGetHandleByIndex(device_index)
                    info = nvidia_smi.nvmlDeviceGetMemoryInfo(handle)
                    total_memory = info.total
                except Exception as e:
                    logger.debug(f"nvidia_smi获取显存信息失败: {e}")

            # 如果nvidia_smi不可用，使用PyTorch获取显存信息
            if total_memory == 0:
                try:
                    torch.cuda.set_device(device_index)
                    # 使用PyTorch的方式估算总显存
                    total_memory = torch.cuda.get_device_properties(device_index).total_memory
                except Exception as e:
                    logger.debug(f"PyTorch获取显存信息失败: {e}")
                    return 0
            
            # 通过实际分配测试验证
            torch.cuda.set_device(device_index)
            torch.cuda.empty_cache()
            
            # 使用二分查找确定最大可分配显存
            left, right = 0, total_memory
            max_allocatable = 0
            
            while left <= right:
                mid = (left + right) // 2
                try:
                    # 尝试分配显存
                    size = mid // 4  # 转换为float32大小
                    tensor = torch.cuda.FloatTensor(size)
                    del tensor
                    torch.cuda.empty_cache()
                    max_allocatable = mid
                    left = mid + 1
                except Exception:
                    right = mid - 1
            
            # 考虑系统和其他程序预留
            available_memory = max_allocatable * 0.95
            return int(available_memory)
            
        except Exception as e:
            logger.error(f"显存检测失败: {str(e)}")
            return 0
    
    def analyze_vram_fragmentation(self, device_index: int = 0) -> Dict:
        """分析显存碎片情况
        
        Args:
            device_index: GPU设备索引
            
        Returns:
            Dict: 碎片分析结果
        """
        if not self.has_cuda or device_index >= self.device_count:
            return {}
            
        try:
            torch.cuda.set_device(device_index)
            
            # 获取显存分配器状态
            allocated = torch.cuda.memory_allocated(device_index)
            reserved = torch.cuda.memory_reserved(device_index)
            
            # 计算碎片率
            fragmentation = 0 if reserved == 0 else (reserved - allocated) / reserved
            
            return {
                "allocated": allocated,
                "reserved": reserved,
                "fragmentation_ratio": fragmentation,
                "is_fragmented": fragmentation > 0.2  # 碎片率超过20%认为存在碎片化
            }
            
        except Exception as e:
            logger.error(f"显存碎片分析失败: {str(e)}")
            return {}
    
    def get_all_devices_info(self) -> List[Dict]:
        """获取所有GPU设备的显存信息
        
        Returns:
            List[Dict]: 设备信息列表
        """
        devices_info = []
        
        if not self.has_cuda:
            return devices_info
            
        try:
            for i in range(self.device_count):
                handle = nvidia_smi.nvmlDeviceGetHandleByIndex(i)
                info = nvidia_smi.nvmlDeviceGetMemoryInfo(handle)
                
                device_info = {
                    "index": i,
                    "name": torch.cuda.get_device_name(i),
                    "total_memory": info.total,
                    "free_memory": info.free,
                    "used_memory": info.used,
                    "real_available": self.get_real_vram(i),
                    "fragmentation": self.analyze_vram_fragmentation(i)
                }
                
                devices_info.append(device_info)
                
            return devices_info
            
        except Exception as e:
            logger.error(f"获取设备信息失败: {str(e)}")
            return devices_info
    
    def estimate_batch_size(self, model_size: int, device_index: int = 0) -> int:
        """估算可用的最大批处理大小
        
        Args:
            model_size: 模型大小（字节）
            device_index: GPU设备索引
            
        Returns:
            int: 估算的最大批处理大小
        """
        if not self.has_cuda or device_index >= self.device_count:
            return 0
            
        try:
            available_memory = self.get_real_vram(device_index)
            
            # 预留30%显存给中间计算结果
            usable_memory = available_memory * 0.7
            
            # 估算每个样本的显存开销（模型大小的1.5倍作为安全系数）
            sample_memory = model_size * 1.5
            
            # 计算最大批处理大小
            max_batch_size = int(usable_memory / sample_memory)
            return max(1, max_batch_size)
            
        except Exception as e:
            logger.error(f"批处理大小估算失败: {str(e)}")
            return 1
    
    def monitor_vram_usage(self, interval: float = 0.1) -> Dict:
        """监控显存使用情况
        
        Args:
            interval: 采样间隔（秒）
            
        Returns:
            Dict: 显存使用统计
        """
        if not self.has_cuda:
            return {}
            
        try:
            stats = {
                "peak_allocated": 0,
                "peak_reserved": 0,
                "current_allocated": 0,
                "current_reserved": 0
            }
            
            # 记录峰值
            stats["peak_allocated"] = torch.cuda.max_memory_allocated()
            stats["peak_reserved"] = torch.cuda.max_memory_reserved()
            
            # 当前使用
            stats["current_allocated"] = torch.cuda.memory_allocated()
            stats["current_reserved"] = torch.cuda.memory_reserved()
            
            return stats
            
        except Exception as e:
            logger.error(f"显存监控失败: {str(e)}")
            return {} 