#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GPU回退机制 - VisionAI-ClipsMaster
提供GPU与CPU之间的智能切换功能，适用于不同硬件环境

该模块允许系统在有GPU时利用GPU加速，在没有GPU或显存不足时
自动回退到CPU优化路径，确保在各种硬件环境下都能正常运行。

主要功能:
1. 智能GPU检测和回退策略
2. 不同CPU指令集优化级联
3. 模型动态加载与设备切换
4. 内存使用监控与优化
5. 为中文Qwen2.5-7B模型和英文Mistral-7B模型提供统一接口
"""

import os
import sys
import logging
import platform
from typing import Dict, List, Optional, Tuple, Union, Any, Callable
import gc
import warnings

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 检查PyTorch可用性
try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
    logger.warning("PyTorch不可用，将仅使用CPU执行")

# 检查CPU特性
def has_avx():
    """
    检查系统是否支持AVX指令集
    
    Returns:
        bool: 是否支持AVX
    """
    try:
        # 简单检测，根据平台进行不同处理
        if platform.system() == 'Windows':
            import ctypes
            # 尝试使用Windows特定API检测
            return False  # 简化版本，默认不支持
        elif platform.system() == 'Linux':
            # 尝试读取/proc/cpuinfo
            with open('/proc/cpuinfo', 'r') as f:
                for line in f:
                    if line.startswith('flags'):
                        return 'avx' in line
            return False
        else:
            return False
    except:
        return False

class GPUFallbackManager:
    """GPU回退管理器，提供设备智能选择与切换功能"""
    
    def __init__(self,
                min_vram_mb: int = 4096,  # 默认最小要求4GB显存
                prefer_gpu: bool = True):
        """
        初始化GPU回退管理器
        
        Args:
            min_vram_mb: 运行模型所需的最小显存(MB)
            prefer_gpu: 是否优先使用GPU(如果可用)
        """
        self.min_vram_mb = min_vram_mb
        self.prefer_gpu = prefer_gpu
        
        # 初始化设备状态
        self.cuda_available = False
        self.current_device = "cpu"
        self.optimization_path = "baseline"
        self.vram_info = {"available": False, "free_mb": 0}
        
        # 检测可用设备
        self._detect_devices()
        
        logger.info(f"GPU回退管理器初始化完成，当前设备: {self.current_device}, 优化路径: {self.optimization_path}")
     
    def _detect_devices(self):
        """检测可用的计算设备并选择最佳设备"""
        # 检查CUDA可用性
        if HAS_TORCH:
            self.cuda_available = torch.cuda.is_available()
            if self.cuda_available and self.prefer_gpu:
                # 检测可用显存
                try:
                    # 简单检测可用显存
                    if torch.cuda.is_available():
                        device = torch.cuda.current_device()
                        free_mem = torch.cuda.get_device_properties(device).total_memory - torch.cuda.memory_allocated(device)
                        free_mb = free_mem / (1024 * 1024)  # 转换为MB
                        
                        self.vram_info = {
                            "available": True,
                            "free_mb": free_mb
                        }
                        
                        # 根据显存决定是否使用GPU
                        if self.vram_info["free_mb"] >= self.min_vram_mb:
                            self.current_device = "cuda"
                            logger.info(f"将使用CUDA加速, 可用显存: {self.vram_info['free_mb']:.2f}MB")
                        else:
                            self.current_device = "cpu"
                            logger.warning(f"显存不足(需要{self.min_vram_mb}MB, 可用{self.vram_info['free_mb']:.2f}MB)，回退到CPU")
                except Exception as e:
                    # 无法检测显存，保守使用CPU
                    self.current_device = "cpu"
                    logger.warning(f"无法检测显存: {str(e)}，保守回退到CPU模式")
            else:
                self.current_device = "cpu"
                if not self.cuda_available:
                    logger.info("CUDA不可用，使用CPU模式")
                elif not self.prefer_gpu:
                    logger.info("根据配置使用CPU模式")
        else:
            self.current_device = "cpu"
            logger.info("PyTorch不可用，使用CPU模式")
                
        # 获取CPU优化路径
        if self.current_device == "cpu":
            # 尝试检测基本指令集支持
            if has_avx():
                self.optimization_path = "avx"
                logger.info("检测到AVX支持，使用AVX优化路径")
            else:
                self.optimization_path = "baseline"
                logger.info("未检测到高级指令集支持，使用基线优化路径")

    def try_gpu_accel(self, model):
        """
        尝试GPU加速，如果不可用则回退到CPU优化路径
        
        Args:
            model: 要加速的PyTorch模型
            
        Returns:
            加速后的模型
        """
        # 清理缓存
        if HAS_TORCH:
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        
        # 使用CUDA加速（如果可用）
        if self.current_device == "cuda" and HAS_TORCH:
            try:
                logger.info("尝试将模型移至GPU...")
                if hasattr(model, "to"):
                    model = model.to("cuda")
                    logger.info("模型已成功加载到GPU")
                return model
            except Exception as e:
                logger.warning(f"GPU加速失败: {str(e)}，回退到CPU")
                # 回收GPU内存
                if hasattr(model, "cpu"):
                    model = model.cpu()
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                gc.collect()
        
        # 使用CPU版本
        if hasattr(model, "to"):
            model = model.to("cpu")
        return model

    def get_device_state(self) -> Dict[str, Any]:
        """
        获取当前设备状态 - 增强版

        Returns:
            设备状态信息字典
        """
        state = {
            "current_device": self.current_device,
            "cuda_available": self.cuda_available,
            "optimization_path": self.optimization_path,
            "vram_info": self.vram_info,
            "opencl_available": False,
            "directml_available": False,
            "integrated_gpu_info": None,
            "recommended_device": self.current_device,
            "fallback_options": []
        }

        # 检测OpenCL支持
        try:
            import pyopencl as cl
            platforms = cl.get_platforms()
            if platforms:
                state["opencl_available"] = True
                state["fallback_options"].append("opencl")

                # 获取OpenCL设备信息
                opencl_devices = []
                for platform in platforms:
                    devices = platform.get_devices()
                    for device in devices:
                        if device.type == cl.device_type.GPU:
                            opencl_devices.append({
                                'name': device.name,
                                'vendor': device.vendor,
                                'memory_mb': device.global_mem_size // (1024 * 1024)
                            })
                state["opencl_devices"] = opencl_devices
        except ImportError:
            logger.debug("PyOpenCL不可用")
        except Exception as e:
            logger.debug(f"OpenCL检测失败: {e}")

        # 检测DirectML支持 (Windows)
        import platform
        if platform.system() == "Windows":
            try:
                import torch_directml
                state["directml_available"] = True
                state["fallback_options"].append("directml")
            except ImportError:
                logger.debug("DirectML不可用")
            except Exception as e:
                logger.debug(f"DirectML检测失败: {e}")

        # 检测集成显卡
        try:
            from ui.hardware.gpu_detector import GPUDetector
            detector = GPUDetector()
            gpu_info = detector.detect_gpus()

            # 查找Intel集成显卡
            for intel_gpu in gpu_info.get('intel_gpus', []):
                if intel_gpu.get('type') == 'integrated':
                    state["integrated_gpu_info"] = {
                        'vendor': 'Intel',
                        'name': intel_gpu.get('name'),
                        'capabilities': intel_gpu.get('capabilities', {}),
                        'supported_apis': intel_gpu.get('supported_apis', [])
                    }
                    state["fallback_options"].append("integrated_gpu")
                    break
        except Exception as e:
            logger.debug(f"集成显卡检测失败: {e}")

        # 智能设备推荐
        state["recommended_device"] = self._recommend_optimal_device(state)

        # 添加CPU信息
        try:
            import cpuinfo
            cpu_info = cpuinfo.get_cpu_info()
            state["cpu_info"] = {
                "brand": cpu_info.get("brand_raw", "Unknown"),
                "cores": os.cpu_count(),
                "architecture": platform.machine()
            }
        except:
            state["cpu_info"] = {
                "brand": "Unknown",
                "cores": os.cpu_count(),
                "architecture": platform.machine()
            }

        # 添加回退选项
        if not state["fallback_options"]:
            state["fallback_options"] = ["cpu"]

        return state

    def _recommend_optimal_device(self, state: Dict[str, Any]) -> str:
        """推荐最优设备"""
        # 优先级: CUDA > DirectML > OpenCL > 集成显卡 > CPU

        if state.get('cuda_available'):
            vram_info = state.get('vram_info', {})
            free_mb = vram_info.get('free_mb', 0)

            # 如果VRAM足够，推荐CUDA
            if free_mb >= 2048:  # 至少2GB
                return 'cuda'
            elif free_mb >= 1024:  # 1-2GB，适合轻量任务
                return 'cuda_light'

        if state.get('directml_available'):
            return 'directml'

        if state.get('opencl_available'):
            opencl_devices = state.get('opencl_devices', [])

            # 如果有性能较好的OpenCL设备
            for device in opencl_devices:
                if device.get('memory_mb', 0) >= 1024:
                    return 'opencl'

        if state.get('integrated_gpu_info'):
            integrated = state['integrated_gpu_info']
            capabilities = integrated.get('capabilities', {})

            # 如果集成显卡支持计算
            if capabilities.get('compute_support'):
                return 'integrated_gpu'

        return 'cpu'

    def get_optimized_config(self, model_name: str) -> Dict[str, Any]:
        """
        获取模型优化配置
        
        Args:
            model_name: 模型名称
            
        Returns:
            优化配置字典
        """
        config = {
            "device": self.current_device,
            "threads": os.cpu_count() or 4,
            "batch_size": 1,
            "quantization": "Q4_K_M",  # 默认平衡量化
            "optimization_level": "auto"
        }
        
        # GPU配置
        if self.current_device == "cuda":
            config["threads"] = 1  # GPU模式下线程通常设为1
            config["batch_size"] = 4  # GPU可以处理更大的批次
            
        # 对于不同模型的特定配置
        if "qwen2.5-7b" in model_name.lower():
            # 中文模型Qwen2.5-7B配置
            config["model_type"] = "qwen"
        elif "mistral-7b" in model_name.lower():
            # 英文模型Mistral-7B配置
            config["model_type"] = "mistral"
        
        return config

# 创建全局回退管理器单例
_gpu_fallback_manager = None

def get_gpu_fallback_manager(min_vram_mb: int = 4096, prefer_gpu: bool = True) -> GPUFallbackManager:
    """
    获取GPU回退管理器全局实例
    
    Args:
        min_vram_mb: 所需最小显存(MB)
        prefer_gpu: 是否优先使用GPU
        
    Returns:
        GPUFallbackManager实例
    """
    global _gpu_fallback_manager
    
    if _gpu_fallback_manager is None:
        _gpu_fallback_manager = GPUFallbackManager(min_vram_mb, prefer_gpu)
        
    return _gpu_fallback_manager

def try_gpu_accel(model):
    """
    尝试GPU加速，全局便捷函数
    
    Args:
        model: 要加速的PyTorch模型
        
    Returns:
        加速后的模型
    """
    manager = get_gpu_fallback_manager()
    return manager.try_gpu_accel(model)

def get_device_info() -> Dict[str, Any]:
    """
    获取当前设备信息
    
    Returns:
        设备信息字典
    """
    manager = get_gpu_fallback_manager()
    return manager.get_device_state()

# 主入口，模块测试用
if __name__ == "__main__":
    # 测试GPU回退功能
    manager = get_gpu_fallback_manager()
    print(f"当前设备: {manager.current_device}")
    print(f"优化路径: {manager.optimization_path}")
    print(f"设备状态: {manager.get_device_state()}")
    
    # 测试模型配置
    qwen_config = manager.get_optimized_config("qwen2.5-7b-zh")
    print(f"Qwen2.5-7B中文模型配置: {qwen_config}")
    
    mistral_config = manager.get_optimized_config("mistral-7b-en")
    print(f"Mistral-7B英文模型配置: {mistral_config}")
    
    # 测试导入到其他模块
    print("\n测试全局辅助函数:")
    print(f"设备信息: {get_device_info()}")
    print(f"系统支持AVX: {has_avx()}") 