"""安全回退引擎

此模块负责在系统资源不足时进行安全降级，主要功能包括：
1. 自动检测系统资源状态
2. 智能降级模型量化等级
3. 必要时切换到CPU模式
4. 资源监控和预警
"""

import os
import psutil
from typing import Optional, List, Dict
from loguru import logger

from src.utils.resource_predictor import ResourcePredictor
from src.utils.device_manager import HybridDevice, DeviceType

class FallbackEngine:
    """安全回退引擎"""
    
    def __init__(self):
        """初始化回退引擎"""
        self.resource_predictor = ResourcePredictor()
        self.device_manager = HybridDevice()
        
        # 量化等级列表（按内存需求从高到低排序）
        self.quant_levels = ['Q8_0', 'Q6_K', 'Q5_K', 'Q4_K_M', 'Q2_K']
        
        # 最低资源要求（字节）
        self.min_memory = 2 * 1024 * 1024 * 1024  # 2GB
        self.min_vram = 2 * 1024 * 1024 * 1024    # 2GB
        
        # 资源预警阈值
        self.memory_warning_threshold = 0.85  # 85%
        self.vram_warning_threshold = 0.85    # 85%
        
        # 当前状态
        self.current_quant_level = None
        self.current_device = None
        self.is_fallback_active = False
    
    def check_resource_status(self) -> Dict[str, float]:
        """检查当前资源状态
        
        Returns:
            Dict[str, float]: 资源使用率
        """
        try:
            # 系统内存状态
            memory = psutil.virtual_memory()
            memory_usage = memory.percent / 100.0
            
            # GPU显存状态
            vram_usage = 0.0
            if self.device_manager.gpu_available:
                gpu_stats = self.device_manager.device_stats.get("gpu", {})
                if gpu_stats and "primary" in gpu_stats:
                    total_vram = gpu_stats["primary"]["vram_total"]
                    used_vram = gpu_stats["primary"]["vram_used"]
                    vram_usage = used_vram / total_vram if total_vram > 0 else 1.0
            
            return {
                "memory_usage": memory_usage,
                "vram_usage": vram_usage
            }
            
        except Exception as e:
            logger.error(f"资源状态检查失败: {str(e)}")
            return {"memory_usage": 1.0, "vram_usage": 1.0}
    
    def predict_resource_requirements(self, 
                                   model_size: int,
                                   quant_level: str) -> Dict[str, int]:
        """预测特定量化等级的资源需求
        
        Args:
            model_size: 模型大小（字节）
            quant_level: 量化等级
            
        Returns:
            Dict[str, int]: 预测的资源需求
        """
        try:
            # 获取当前设备类型
            use_gpu = self.current_device in [DeviceType.CUDA, DeviceType.MPS]
            
            # 预测资源使用
            memory_usage = self.resource_predictor.predict_memory_usage(
                model_size=model_size,
                batch_size=1,
                use_gpu=use_gpu
            )
            
            return memory_usage
            
        except Exception as e:
            logger.error(f"资源需求预测失败: {str(e)}")
            return {}
    
    def auto_fallback(self,
                     model_size: int,
                     force_cpu: bool = False) -> Optional[str]:
        """自动回退到合适的量化等级
        
        Args:
            model_size: 模型大小（字节）
            force_cpu: 是否强制使用CPU模式
            
        Returns:
            Optional[str]: 选择的量化等级，如果无法找到合适的等级则返回None
        """
        try:
            # 更新设备状态
            self.device_manager.update_device_stats()
            
            # 如果需要强制使用CPU或GPU不可用，切换到CPU模式
            if force_cpu or not self.device_manager.gpu_available:
                self.current_device = self.device_manager.select_device(
                    preferred=DeviceType.CPU_AVX2
                )
            else:
                self.current_device = self.device_manager.select_device()
            
            # 获取可用内存
            memory = psutil.virtual_memory()
            available_memory = memory.available
            
            # 获取可用显存（如果使用GPU）
            available_vram = 0
            if self.current_device == DeviceType.CUDA:
                gpu_stats = self.device_manager.device_stats.get("gpu", {})
                if gpu_stats and "primary" in gpu_stats:
                    available_vram = gpu_stats["primary"]["vram_free"]
            
            # 遍历量化等级，找到第一个符合资源要求的等级
            for quant_level in self.quant_levels:
                resource_req = self.predict_resource_requirements(
                    model_size, quant_level
                )
                
                if not resource_req:
                    continue
                
                # 检查内存要求
                if resource_req["total_memory"] > available_memory:
                    continue
                
                # 如果使用GPU，检查显存要求
                if (self.current_device == DeviceType.CUDA and 
                    resource_req["gpu_memory"] > available_vram):
                    continue
                
                # 找到合适的量化等级
                self.current_quant_level = quant_level
                self.is_fallback_active = True
                logger.info(f"选择量化等级: {quant_level}")
                return quant_level
            
            # 如果没有找到合适的量化等级，尝试切换到CPU模式
            if not force_cpu:
                logger.warning("GPU资源不足，尝试切换到CPU模式")
                return self.auto_fallback(model_size, force_cpu=True)
            
            logger.error("无法找到合适的量化等级")
            return None
            
        except Exception as e:
            logger.error(f"自动回退失败: {str(e)}")
            return None
    
    def monitor_resources(self, callback: Optional[callable] = None) -> None:
        """监控资源使用情况
        
        Args:
            callback: 资源预警时的回调函数
        """
        try:
            status = self.check_resource_status()
            
            # 检查是否超过预警阈值
            memory_warning = status["memory_usage"] > self.memory_warning_threshold
            vram_warning = status["vram_usage"] > self.vram_warning_threshold
            
            if memory_warning or vram_warning:
                warning_msg = []
                if memory_warning:
                    warning_msg.append(f"系统内存使用率: {status['memory_usage']*100:.1f}%")
                if vram_warning:
                    warning_msg.append(f"GPU显存使用率: {status['vram_usage']*100:.1f}%")
                
                logger.warning("资源使用预警: " + ", ".join(warning_msg))
                
                if callback:
                    callback(status)
            
        except Exception as e:
            logger.error(f"资源监控失败: {str(e)}")
    
    def get_fallback_status(self) -> Dict:
        """获取回退状态信息
        
        Returns:
            Dict: 当前回退状态
        """
        return {
            "is_active": self.is_fallback_active,
            "current_quant_level": self.current_quant_level,
            "current_device": self.current_device.value if self.current_device else None,
            "resource_status": self.check_resource_status()
        } 