#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
增强设备管理器
专门处理视频处理的GPU分配和性能优化
"""

import os
import sys
import time
import json
import logging
import threading
import psutil
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

# GPU相关导入
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    import pynvml
    NVML_AVAILABLE = True
except ImportError:
    NVML_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class DeviceCapabilities:
    """设备能力"""
    device_type: str  # "gpu" or "cpu"
    device_name: str
    memory_total: float  # GB
    memory_available: float  # GB
    compute_capability: Optional[Tuple[int, int]] = None
    supports_fp16: bool = False
    supports_int8: bool = False
    max_batch_size: int = 1
    estimated_performance: float = 1.0  # 相对性能评分

@dataclass
class WorkloadProfile:
    """工作负载配置"""
    task_type: str  # "video_decode", "video_encode", "frame_process", "subtitle_align"
    input_resolution: Tuple[int, int] = (1920, 1080)
    batch_size: int = 1
    precision: str = "fp32"  # "fp32", "fp16", "int8"
    memory_requirement: float = 1.0  # GB
    compute_intensity: str = "medium"  # "low", "medium", "high"

class EnhancedDeviceManager:
    """增强设备管理器"""
    
    def __init__(self, memory_limit_gb: float = 3.8):
        """
        初始化增强设备管理器
        
        Args:
            memory_limit_gb: 内存限制（GB）
        """
        self.memory_limit_gb = memory_limit_gb
        self.available_devices = {}
        self.current_allocations = {}
        self.performance_history = {}
        
        # 初始化NVML（如果可用）
        self.nvml_initialized = self._initialize_nvml()
        
        # 扫描可用设备
        self._scan_devices()
        
        # 启动监控
        self.monitoring_active = False
        self.monitor_thread = None
        
        logger.info(f"增强设备管理器初始化完成 - 发现 {len(self.available_devices)} 个设备")
    
    def _initialize_nvml(self) -> bool:
        """初始化NVIDIA管理库"""
        if not NVML_AVAILABLE:
            return False
        
        try:
            pynvml.nvmlInit()
            return True
        except Exception as e:
            logger.debug(f"NVML初始化失败: {e}")
            return False
    
    def _scan_devices(self):
        """扫描可用设备"""
        self.available_devices = {}
        
        # 扫描CPU
        cpu_caps = self._get_cpu_capabilities()
        self.available_devices["cpu"] = cpu_caps
        
        # 扫描GPU
        if TORCH_AVAILABLE and torch.cuda.is_available():
            for i in range(torch.cuda.device_count()):
                gpu_caps = self._get_gpu_capabilities(i)
                if gpu_caps:
                    self.available_devices[f"cuda:{i}"] = gpu_caps
        
        logger.info(f"设备扫描完成: {list(self.available_devices.keys())}")
    
    def _get_cpu_capabilities(self) -> DeviceCapabilities:
        """获取CPU能力"""
        memory = psutil.virtual_memory()
        
        return DeviceCapabilities(
            device_type="cpu",
            device_name=f"CPU ({psutil.cpu_count()} cores)",
            memory_total=memory.total / (1024**3),
            memory_available=memory.available / (1024**3),
            supports_fp16=False,
            supports_int8=True,
            max_batch_size=4,
            estimated_performance=1.0
        )
    
    def _get_gpu_capabilities(self, device_id: int) -> Optional[DeviceCapabilities]:
        """获取GPU能力"""
        try:
            device = torch.device(f"cuda:{device_id}")
            props = torch.cuda.get_device_properties(device_id)
            
            # 获取内存信息
            memory_total = props.total_memory / (1024**3)
            
            # 检查内存是否满足要求
            if memory_total < self.memory_limit_gb:
                logger.warning(f"GPU {device_id} 内存不足: {memory_total:.1f}GB < {self.memory_limit_gb}GB")
                return None
            
            # 获取可用内存
            torch.cuda.set_device(device_id)
            memory_free = torch.cuda.get_device_properties(device_id).total_memory - torch.cuda.memory_allocated(device_id)
            memory_available = memory_free / (1024**3)
            
            # 检查计算能力
            compute_capability = (props.major, props.minor)
            supports_fp16 = compute_capability >= (7, 0)  # Volta架构及以上
            supports_int8 = compute_capability >= (6, 1)  # Pascal架构及以上
            
            # 估算性能
            estimated_performance = self._estimate_gpu_performance(props)
            
            # 计算最大批处理大小
            max_batch_size = min(8, int(memory_available / 2))  # 保守估计
            
            return DeviceCapabilities(
                device_type="gpu",
                device_name=props.name,
                memory_total=memory_total,
                memory_available=memory_available,
                compute_capability=compute_capability,
                supports_fp16=supports_fp16,
                supports_int8=supports_int8,
                max_batch_size=max_batch_size,
                estimated_performance=estimated_performance
            )
            
        except Exception as e:
            logger.error(f"获取GPU {device_id} 能力失败: {e}")
            return None
    
    def _estimate_gpu_performance(self, props) -> float:
        """估算GPU性能"""
        try:
            # 基于GPU规格估算性能
            base_score = 1.0
            
            # 计算单元数量
            sm_count = props.multi_processor_count
            base_score *= (sm_count / 20)  # 以20个SM为基准
            
            # 内存带宽（简化估算）
            memory_gb = props.total_memory / (1024**3)
            base_score *= min(memory_gb / 8, 2.0)  # 以8GB为基准，最多2倍
            
            # 计算能力
            compute_capability = props.major * 10 + props.minor
            if compute_capability >= 75:  # Turing及以上
                base_score *= 1.5
            elif compute_capability >= 70:  # Volta
                base_score *= 1.3
            elif compute_capability >= 60:  # Pascal
                base_score *= 1.1
            
            return min(base_score, 10.0)  # 最大10倍性能
            
        except Exception as e:
            logger.debug(f"性能估算失败: {e}")
            return 1.0
    
    def select_optimal_device(self, workload: WorkloadProfile) -> Tuple[str, DeviceCapabilities]:
        """选择最优设备"""
        try:
            best_device = None
            best_score = -1
            best_caps = None
            
            for device_name, caps in self.available_devices.items():
                score = self._calculate_device_score(caps, workload)
                
                if score > best_score:
                    best_score = score
                    best_device = device_name
                    best_caps = caps
            
            if best_device is None:
                # 回退到CPU
                best_device = "cpu"
                best_caps = self.available_devices["cpu"]
            
            logger.info(f"为任务 {workload.task_type} 选择设备: {best_device} (评分: {best_score:.2f})")
            return best_device, best_caps
            
        except Exception as e:
            logger.error(f"设备选择失败: {e}")
            return "cpu", self.available_devices["cpu"]
    
    def _calculate_device_score(self, caps: DeviceCapabilities, workload: WorkloadProfile) -> float:
        """计算设备评分"""
        try:
            score = 0.0
            
            # 内存检查
            if caps.memory_available < workload.memory_requirement:
                return -1  # 内存不足，不可用
            
            # 基础性能评分
            score += caps.estimated_performance * 10
            
            # 任务类型适配性
            if workload.task_type in ["video_decode", "video_encode"]:
                if caps.device_type == "gpu":
                    score += 20  # GPU对视频编解码有优势
                else:
                    score += 5   # CPU也可以处理
            
            elif workload.task_type == "frame_process":
                if caps.device_type == "gpu":
                    score += 30  # GPU对帧处理有很大优势
                else:
                    score += 3
            
            elif workload.task_type == "subtitle_align":
                if caps.device_type == "gpu":
                    score += 15  # GPU对并行计算有优势
                else:
                    score += 8   # CPU也能很好处理
            
            # 精度支持
            if workload.precision == "fp16" and caps.supports_fp16:
                score += 10
            elif workload.precision == "int8" and caps.supports_int8:
                score += 5
            
            # 批处理大小
            if caps.max_batch_size >= workload.batch_size:
                score += 5
            else:
                score -= 10  # 批处理大小不足
            
            # 内存利用率
            memory_usage_ratio = workload.memory_requirement / caps.memory_available
            if memory_usage_ratio < 0.5:
                score += 5  # 内存充足
            elif memory_usage_ratio > 0.8:
                score -= 10  # 内存紧张
            
            return score
            
        except Exception as e:
            logger.error(f"设备评分计算失败: {e}")
            return 0.0
    
    def allocate_device(self, device_name: str, workload: WorkloadProfile) -> bool:
        """分配设备"""
        try:
            if device_name not in self.available_devices:
                return False
            
            caps = self.available_devices[device_name]
            
            # 检查资源是否足够
            current_allocation = self.current_allocations.get(device_name, 0)
            if current_allocation + workload.memory_requirement > caps.memory_available:
                logger.warning(f"设备 {device_name} 资源不足")
                return False
            
            # 分配资源
            self.current_allocations[device_name] = current_allocation + workload.memory_requirement
            
            logger.info(f"设备 {device_name} 分配成功，当前使用: {self.current_allocations[device_name]:.2f}GB")
            return True
            
        except Exception as e:
            logger.error(f"设备分配失败: {e}")
            return False
    
    def release_device(self, device_name: str, workload: WorkloadProfile):
        """释放设备"""
        try:
            if device_name in self.current_allocations:
                current = self.current_allocations[device_name]
                self.current_allocations[device_name] = max(0, current - workload.memory_requirement)
                
                logger.info(f"设备 {device_name} 释放成功，当前使用: {self.current_allocations[device_name]:.2f}GB")
                
        except Exception as e:
            logger.error(f"设备释放失败: {e}")
    
    def get_device_status(self) -> Dict[str, Any]:
        """获取设备状态"""
        status = {
            "available_devices": {},
            "current_allocations": self.current_allocations.copy(),
            "system_memory": self._get_system_memory_status(),
            "gpu_status": self._get_gpu_status() if self.nvml_initialized else {}
        }
        
        # 设备详情
        for device_name, caps in self.available_devices.items():
            status["available_devices"][device_name] = {
                "device_type": caps.device_type,
                "device_name": caps.device_name,
                "memory_total": caps.memory_total,
                "memory_available": caps.memory_available,
                "estimated_performance": caps.estimated_performance,
                "supports_fp16": caps.supports_fp16,
                "current_allocation": self.current_allocations.get(device_name, 0)
            }
        
        return status
    
    def _get_system_memory_status(self) -> Dict[str, float]:
        """获取系统内存状态"""
        memory = psutil.virtual_memory()
        return {
            "total_gb": memory.total / (1024**3),
            "available_gb": memory.available / (1024**3),
            "used_gb": memory.used / (1024**3),
            "percent": memory.percent
        }
    
    def _get_gpu_status(self) -> Dict[str, Any]:
        """获取GPU状态"""
        if not self.nvml_initialized:
            return {}
        
        gpu_status = {}
        
        try:
            device_count = pynvml.nvmlDeviceGetCount()
            
            for i in range(device_count):
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                
                # 基本信息
                name = pynvml.nvmlDeviceGetName(handle).decode('utf-8')
                
                # 内存信息
                mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                
                # 利用率信息
                try:
                    util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                    gpu_util = util.gpu
                    memory_util = util.memory
                except:
                    gpu_util = 0
                    memory_util = 0
                
                # 温度信息
                try:
                    temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
                except:
                    temp = 0
                
                gpu_status[f"gpu_{i}"] = {
                    "name": name,
                    "memory_total": mem_info.total / (1024**3),
                    "memory_used": mem_info.used / (1024**3),
                    "memory_free": mem_info.free / (1024**3),
                    "gpu_utilization": gpu_util,
                    "memory_utilization": memory_util,
                    "temperature": temp
                }
                
        except Exception as e:
            logger.debug(f"获取GPU状态失败: {e}")
        
        return gpu_status
    
    def start_monitoring(self):
        """启动设备监控"""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.monitor_thread = threading.Thread(target=self._monitor_devices, daemon=True)
            self.monitor_thread.start()
            logger.info("设备监控已启动")
    
    def stop_monitoring(self):
        """停止设备监控"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)
            logger.info("设备监控已停止")
    
    def _monitor_devices(self):
        """设备监控循环"""
        while self.monitoring_active:
            try:
                # 更新设备状态
                self._update_device_availability()
                
                # 记录性能历史
                self._record_performance_history()
                
                time.sleep(5)  # 5秒监控间隔
                
            except Exception as e:
                logger.debug(f"设备监控错误: {e}")
                time.sleep(10)
    
    def _update_device_availability(self):
        """更新设备可用性"""
        try:
            # 更新CPU内存
            if "cpu" in self.available_devices:
                memory = psutil.virtual_memory()
                self.available_devices["cpu"].memory_available = memory.available / (1024**3)
            
            # 更新GPU内存
            if TORCH_AVAILABLE:
                for device_name in self.available_devices:
                    if device_name.startswith("cuda:"):
                        device_id = int(device_name.split(":")[1])
                        try:
                            torch.cuda.set_device(device_id)
                            memory_free = torch.cuda.get_device_properties(device_id).total_memory - torch.cuda.memory_allocated(device_id)
                            self.available_devices[device_name].memory_available = memory_free / (1024**3)
                        except:
                            pass
                            
        except Exception as e:
            logger.debug(f"更新设备可用性失败: {e}")
    
    def _record_performance_history(self):
        """记录性能历史"""
        try:
            timestamp = time.time()
            
            for device_name in self.available_devices:
                if device_name not in self.performance_history:
                    self.performance_history[device_name] = []
                
                # 记录当前状态
                status = {
                    "timestamp": timestamp,
                    "memory_used": self.current_allocations.get(device_name, 0),
                    "memory_available": self.available_devices[device_name].memory_available
                }
                
                self.performance_history[device_name].append(status)
                
                # 保持历史记录在合理范围内
                if len(self.performance_history[device_name]) > 100:
                    self.performance_history[device_name] = self.performance_history[device_name][-100:]
                    
        except Exception as e:
            logger.debug(f"记录性能历史失败: {e}")
    
    def get_performance_recommendations(self, workload: WorkloadProfile) -> Dict[str, Any]:
        """获取性能建议"""
        recommendations = {
            "optimal_device": None,
            "suggested_batch_size": 1,
            "suggested_precision": "fp32",
            "memory_optimization": [],
            "performance_tips": []
        }
        
        try:
            # 选择最优设备
            device_name, caps = self.select_optimal_device(workload)
            recommendations["optimal_device"] = device_name
            
            # 批处理大小建议
            recommendations["suggested_batch_size"] = min(caps.max_batch_size, workload.batch_size)
            
            # 精度建议
            if caps.supports_fp16 and workload.task_type in ["frame_process", "subtitle_align"]:
                recommendations["suggested_precision"] = "fp16"
            elif caps.supports_int8:
                recommendations["suggested_precision"] = "int8"
            
            # 内存优化建议
            if caps.memory_available < 2.0:
                recommendations["memory_optimization"].append("使用较小的批处理大小")
                recommendations["memory_optimization"].append("启用梯度检查点")
            
            # 性能提示
            if caps.device_type == "gpu":
                recommendations["performance_tips"].append("使用GPU加速可显著提升性能")
                if caps.supports_fp16:
                    recommendations["performance_tips"].append("启用FP16可提升速度并节省内存")
            else:
                recommendations["performance_tips"].append("考虑使用多线程处理")
                
        except Exception as e:
            logger.error(f"生成性能建议失败: {e}")
        
        return recommendations
