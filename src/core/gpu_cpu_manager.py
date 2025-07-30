#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPU/CPU兼容性管理器
自动检测和无缝切换GPU/CPU，确保系统在任何环境下都能正常运行
"""

import os
import sys
import platform
import subprocess
import logging
import psutil
import torch
from typing import Dict, Any, Optional, List
from pathlib import Path

class GPUCPUManager:
    """GPU/CPU兼容性管理器"""
    
    def __init__(self):
        """初始化GPU/CPU管理器"""
        self.logger = self._setup_logger()
        self.system_info = self._detect_system_info()
        self.gpu_info = self._detect_gpu_info()
        self.cpu_info = self._detect_cpu_info()
        self.recommended_device = self._determine_best_device()
        
        self.logger.info("🔧 GPU/CPU兼容性管理器初始化完成")
        self.logger.info(f"💻 系统: {self.system_info['platform']}")
        self.logger.info(f"🎯 推荐设备: {self.recommended_device}")
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger("GPUCPUManager")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
    
    def _detect_system_info(self) -> Dict[str, Any]:
        """检测系统信息"""
        return {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "architecture": platform.architecture()[0],
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "memory_total_gb": psutil.virtual_memory().total / (1024**3)
        }
    
    def _detect_gpu_info(self) -> Dict[str, Any]:
        """检测GPU信息"""
        gpu_info = {
            "cuda_available": False,
            "cuda_version": None,
            "gpu_count": 0,
            "gpu_devices": [],
            "total_memory_gb": 0,
            "driver_version": None
        }
        
        try:
            # 检测CUDA
            if torch.cuda.is_available():
                gpu_info["cuda_available"] = True
                gpu_info["cuda_version"] = torch.version.cuda
                gpu_info["gpu_count"] = torch.cuda.device_count()
                
                # 获取每个GPU的详细信息
                for i in range(gpu_info["gpu_count"]):
                    props = torch.cuda.get_device_properties(i)
                    device_info = {
                        "id": i,
                        "name": props.name,
                        "memory_gb": props.total_memory / (1024**3),
                        "compute_capability": f"{props.major}.{props.minor}"
                    }
                    gpu_info["gpu_devices"].append(device_info)
                    gpu_info["total_memory_gb"] += device_info["memory_gb"]
                
                self.logger.info(f"✅ 检测到 {gpu_info['gpu_count']} 个GPU设备")
                for device in gpu_info["gpu_devices"]:
                    self.logger.info(f"  📱 {device['name']}: {device['memory_gb']:.1f}GB")
            else:
                self.logger.info("❌ 未检测到CUDA支持")
                
        except Exception as e:
            self.logger.warning(f"⚠️ GPU检测失败: {str(e)}")
        
        # 尝试检测NVIDIA驱动
        try:
            if platform.system() == "Windows":
                result = subprocess.run(
                    ["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader,nounits"],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    gpu_info["driver_version"] = result.stdout.strip().split('\n')[0]
            else:
                result = subprocess.run(
                    ["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader,nounits"],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    gpu_info["driver_version"] = result.stdout.strip().split('\n')[0]
        except:
            pass
        
        return gpu_info
    
    def _detect_cpu_info(self) -> Dict[str, Any]:
        """检测CPU信息"""
        cpu_info = {
            "cores": psutil.cpu_count(logical=False),
            "threads": psutil.cpu_count(logical=True),
            "frequency_mhz": psutil.cpu_freq().current if psutil.cpu_freq() else 0,
            "usage_percent": psutil.cpu_percent(interval=1),
            "architecture": platform.machine(),
            "supports_avx": self._check_cpu_features()
        }
        
        self.logger.info(f"💻 CPU: {cpu_info['cores']}核{cpu_info['threads']}线程")
        self.logger.info(f"⚡ 频率: {cpu_info['frequency_mhz']:.0f}MHz")
        
        return cpu_info
    
    def _check_cpu_features(self) -> Dict[str, bool]:
        """检查CPU特性支持"""
        features = {
            "avx": False,
            "avx2": False,
            "sse4": False
        }
        
        try:
            if platform.system() == "Windows":
                # Windows下检查CPU特性
                import cpuinfo
                info = cpuinfo.get_cpu_info()
                flags = info.get('flags', [])
                features["avx"] = 'avx' in flags
                features["avx2"] = 'avx2' in flags
                features["sse4"] = 'sse4_1' in flags or 'sse4_2' in flags
        except:
            # 如果无法检测，假设支持基本特性
            features["sse4"] = True
        
        return features
    
    def _determine_best_device(self) -> str:
        """确定最佳设备"""
        # 优先级：GPU > CPU
        if self.gpu_info["cuda_available"] and self.gpu_info["gpu_count"] > 0:
            # 检查GPU内存是否足够
            best_gpu = max(self.gpu_info["gpu_devices"], key=lambda x: x["memory_gb"])
            if best_gpu["memory_gb"] >= 4.0:  # 至少4GB显存
                return f"cuda:{best_gpu['id']}"
            else:
                self.logger.warning(f"⚠️ GPU显存不足 ({best_gpu['memory_gb']:.1f}GB < 4GB)")
        
        # 检查CPU是否足够强大
        if self.cpu_info["cores"] >= 4 and self.system_info["memory_total_gb"] >= 8:
            return "cpu"
        else:
            self.logger.warning("⚠️ CPU配置较低，可能影响性能")
            return "cpu"  # 仍然返回CPU，但会有性能警告
    
    def get_optimal_config(self, task_type: str = "training") -> Dict[str, Any]:
        """获取最优配置"""
        device = self.recommended_device
        
        if device.startswith("cuda"):
            # GPU配置
            gpu_id = int(device.split(":")[1])
            gpu_device = self.gpu_info["gpu_devices"][gpu_id]
            
            config = {
                "device": device,
                "device_type": "gpu",
                "batch_size": min(8, max(2, int(gpu_device["memory_gb"] / 2))),
                "num_workers": min(4, self.cpu_info["threads"]),
                "mixed_precision": gpu_device["memory_gb"] >= 6,
                "gradient_accumulation": max(1, 8 // min(8, max(2, int(gpu_device["memory_gb"] / 2)))),
                "memory_limit_gb": gpu_device["memory_gb"] * 0.8  # 80%的显存
            }
        else:
            # CPU配置
            config = {
                "device": "cpu",
                "device_type": "cpu",
                "batch_size": max(1, min(4, self.cpu_info["cores"] // 2)),
                "num_workers": max(1, min(4, self.cpu_info["cores"] // 2)),
                "mixed_precision": False,
                "gradient_accumulation": max(2, 8 // max(1, min(4, self.cpu_info["cores"] // 2))),
                "memory_limit_gb": self.system_info["memory_total_gb"] * 0.6  # 60%的内存
            }
        
        # 任务特定调整
        if task_type == "inference":
            config["batch_size"] = max(1, config["batch_size"] // 2)
        elif task_type == "training":
            # 训练时更保守的内存使用
            config["memory_limit_gb"] *= 0.8
        
        return config
    
    def auto_configure_torch(self) -> Dict[str, Any]:
        """自动配置PyTorch"""
        config = self.get_optimal_config()
        
        try:
            # 设置设备
            device = torch.device(config["device"])
            
            # 设置线程数（仅在未设置时）
            if config["device_type"] == "cpu":
                try:
                    torch.set_num_threads(config["num_workers"])
                except RuntimeError:
                    # 如果已经设置过，忽略错误
                    pass
                try:
                    torch.set_num_interop_threads(config["num_workers"])
                except RuntimeError:
                    # 如果已经设置过，忽略错误
                    pass
            
            # 设置内存策略
            if config["device_type"] == "gpu":
                torch.cuda.set_per_process_memory_fraction(0.8)
                torch.cuda.empty_cache()
            
            self.logger.info(f"✅ PyTorch配置完成: {config['device']}")
            self.logger.info(f"📊 批次大小: {config['batch_size']}")
            self.logger.info(f"🔧 工作线程: {config['num_workers']}")
            
            return {
                "success": True,
                "device": device,
                "config": config
            }
            
        except Exception as e:
            self.logger.error(f"❌ PyTorch配置失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "fallback_device": torch.device("cpu")
            }
    
    def check_compatibility(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """检查兼容性"""
        compatibility = {
            "compatible": True,
            "warnings": [],
            "errors": [],
            "recommendations": []
        }
        
        # 检查内存要求
        required_memory = requirements.get("memory_gb", 4)
        if self.recommended_device.startswith("cuda"):
            gpu_id = int(self.recommended_device.split(":")[1])
            available_memory = self.gpu_info["gpu_devices"][gpu_id]["memory_gb"]
        else:
            available_memory = self.system_info["memory_total_gb"]
        
        if available_memory < required_memory:
            compatibility["errors"].append(
                f"内存不足: 需要{required_memory}GB，可用{available_memory:.1f}GB"
            )
            compatibility["compatible"] = False
        
        # 检查CUDA版本
        required_cuda = requirements.get("cuda_version")
        if required_cuda and self.gpu_info["cuda_available"]:
            current_cuda = self.gpu_info["cuda_version"]
            if current_cuda != required_cuda:
                compatibility["warnings"].append(
                    f"CUDA版本不匹配: 需要{required_cuda}，当前{current_cuda}"
                )
        
        # 性能建议
        if self.recommended_device == "cpu" and self.cpu_info["cores"] < 8:
            compatibility["recommendations"].append(
                "建议使用8核以上CPU以获得更好性能"
            )
        
        if self.gpu_info["cuda_available"] and not self.recommended_device.startswith("cuda"):
            compatibility["recommendations"].append(
                "检测到GPU但未使用，可能是显存不足"
            )
        
        return compatibility
    
    def get_system_report(self) -> Dict[str, Any]:
        """获取系统报告"""
        return {
            "system_info": self.system_info,
            "gpu_info": self.gpu_info,
            "cpu_info": self.cpu_info,
            "recommended_device": self.recommended_device,
            "optimal_config": self.get_optimal_config(),
            "torch_config": self.auto_configure_torch()
        }
