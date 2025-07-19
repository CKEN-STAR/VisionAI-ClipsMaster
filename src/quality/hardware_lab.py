#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
硬件兼容性实验室模块

提供设备兼容性测试和性能评估功能，确保在各种配置下的稳定运行。
主要功能：
1. 设备兼容性矩阵测试
2. 性能基准测试
3. 最低配置测试
4. 设备特化优化
5. 资源利用率分析
"""

import os
import sys
import platform
import time
import json
import logging
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
from pathlib import Path

from loguru import logger
from src.utils.file_handler import ensure_dir_exists

# 尝试导入设备监控相关库
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logger.warning("psutil未安装，部分硬件监控功能将受限")

try:
    import GPUtil
    GPUTIL_AVAILABLE = True
except ImportError:
    GPUTIL_AVAILABLE = False
    logger.warning("GPUtil未安装，GPU监控功能将受限")


class DeviceEmulator:
    """设备仿真器，用于模拟不同硬件配置"""
    
    def __init__(self, device_config: Dict[str, Any]):
        """
        初始化设备仿真器
        
        Args:
            device_config: 设备配置字典
        """
        self.config = device_config
        self.device_type = device_config.get("type", "low-end")
        self.ram = device_config.get("ram", 4)  # 单位GB
        self.gpu_available = device_config.get("gpu", False)
        self.cpu_cores = device_config.get("cpu_cores", 2)
        self.storage_type = device_config.get("storage", "hdd")
        
        # 记录运行状态
        self.running = False
        self.performance_stats = {}
        self.error_log = []
        
        logger.debug(f"创建设备仿真器: {self.device_type}, RAM: {self.ram}GB, GPU: {self.gpu_available}")
    
    def render_test(self, video_path: str) -> Dict[str, Any]:
        """
        模拟在当前设备配置上渲染视频
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            Dict[str, Any]: 性能测试结果
        """
        self.running = True
        start_time = time.time()
        
        try:
            # 获取视频信息
            video_info = self._get_video_info(video_path)
            
            # 根据设备配置模拟性能表现
            processing_time = self._simulate_processing_time(video_info)
            memory_usage = self._simulate_memory_usage(video_info)
            cpu_usage = self._simulate_cpu_usage()
            gpu_usage = self._simulate_gpu_usage() if self.gpu_available else 0
            
            # 判断是否能够处理该视频
            can_process = self._can_process_video(video_info)
            
            # 延迟以模拟实际处理时间
            scaled_delay = min(processing_time / 10, 1.0)  # 最多延迟1秒
            time.sleep(scaled_delay)
            
            # 记录性能数据
            self.performance_stats = {
                "processing_time_seconds": processing_time,
                "memory_usage_mb": memory_usage,
                "cpu_usage_percent": cpu_usage,
                "gpu_usage_percent": gpu_usage if self.gpu_available else 0,
                "can_process": can_process,
                "bottleneck": self._identify_bottleneck()
            }
            
            result = {
                "success": can_process,
                "device_type": self.device_type,
                "performance": self.performance_stats
            }
            
            if not can_process:
                reason = self._get_failure_reason()
                result["reason"] = reason
                self.error_log.append(reason)
            
            return result
            
        except Exception as e:
            error_msg = f"渲染测试失败: {str(e)}"
            logger.error(error_msg)
            self.error_log.append(error_msg)
            return {
                "success": False,
                "device_type": self.device_type,
                "error": str(e)
            }
        finally:
            self.running = False
            end_time = time.time()
            logger.debug(f"设备仿真完成 - {self.device_type}, 耗时: {end_time - start_time:.2f}秒")
    
    def _get_video_info(self, video_path: str) -> Dict[str, Any]:
        """获取视频信息"""
        # 这里简化处理，实际应用中可以使用ffmpeg等工具分析视频
        file_size = os.path.getsize(video_path) if os.path.exists(video_path) else 1024 * 1024
        
        return {
            "file_size_bytes": file_size,
            "duration_seconds": 60,  # 假设60秒
            "resolution": (1920, 1080),  # 假设1080p
            "bitrate": file_size / 60,  # 简化估算
            "frames": 1800  # 假设30fps
        }
    
    def _simulate_processing_time(self, video_info: Dict[str, Any]) -> float:
        """模拟处理时间（秒）"""
        # 基础处理时间基于视频大小和时长
        base_time = video_info["duration_seconds"] * 0.5  # 基准：处理时间为视频时长的0.5倍
        
        # 设备因素调整
        device_factors = {
            "low-end": 3.0,      # 低端设备慢3倍
            "mid-range": 1.5,    # 中端设备慢1.5倍
            "flagship": 0.8      # 高端设备快20%
        }
        
        # GPU加速因素
        gpu_factor = 0.6 if self.gpu_available else 1.0  # GPU加速40%
        
        # 内存因素
        ram_factor = max(0.8, 4 / self.ram) if self.ram > 0 else 3.0  # 内存越大越快，但有上限
        
        # 综合计算
        adjusted_time = base_time * device_factors.get(self.device_type, 1.0) * gpu_factor * ram_factor
        
        return adjusted_time
    
    def _simulate_memory_usage(self, video_info: Dict[str, Any]) -> float:
        """模拟内存使用（MB）"""
        # 基础内存使用基于视频分辨率
        width, height = video_info["resolution"]
        pixels = width * height
        
        # 估算每帧处理所需内存（简化模型）
        frame_memory_mb = pixels * 4 / (1024 * 1024)  # 4字节/像素
        
        # 基础内存使用
        base_memory = 200 + frame_memory_mb * 5  # 基础200MB + 5帧缓冲
        
        return base_memory
    
    def _simulate_cpu_usage(self) -> float:
        """模拟CPU使用率"""
        # 基于设备类型估算
        base_usage = {
            "low-end": 85,    # 低端设备高负载
            "mid-range": 60,  # 中端设备中等负载
            "flagship": 40    # 高端设备低负载
        }
        
        # GPU可以分担部分负载
        gpu_offload = 20 if self.gpu_available else 0
        
        # 最终使用率，确保在0-100范围内
        usage = max(0, min(100, base_usage.get(self.device_type, 70) - gpu_offload))
        
        return usage
    
    def _simulate_gpu_usage(self) -> float:
        """模拟GPU使用率（如果可用）"""
        if not self.gpu_available:
            return 0
        
        # 估算GPU使用率
        base_usage = {
            "low-end": 95,    # 低端GPU几乎满载
            "mid-range": 70,  # 中端GPU中等负载
            "flagship": 50    # 高端GPU低负载
        }
        
        return base_usage.get(self.device_type, 80)
    
    def _can_process_video(self, video_info: Dict[str, Any]) -> bool:
        """判断是否能够处理该视频"""
        # 检查内存是否足够
        estimated_memory_mb = self._simulate_memory_usage(video_info)
        available_memory_mb = self.ram * 1024  # 转换为MB
        
        if estimated_memory_mb > available_memory_mb * 0.9:  # 留10%余量
            return False
        
        # 检查处理能力
        width, height = video_info["resolution"]
        
        # 低端设备4K限制
        if self.device_type == "low-end" and (width > 1920 or height > 1080):
            return False
        
        # 非GPU设备8K限制
        if not self.gpu_available and (width > 3840 or height > 2160):
            return False
        
        return True
    
    def _identify_bottleneck(self) -> str:
        """识别性能瓶颈"""
        if not self.performance_stats:
            return "unknown"
        
        cpu_usage = self.performance_stats.get("cpu_usage_percent", 0)
        memory_usage_mb = self.performance_stats.get("memory_usage_mb", 0)
        available_memory_mb = self.ram * 1024
        memory_usage_percent = memory_usage_mb / available_memory_mb * 100 if available_memory_mb > 0 else 100
        
        if memory_usage_percent > 85:
            return "memory"
        elif cpu_usage > 85:
            return "cpu"
        elif self.gpu_available and self.performance_stats.get("gpu_usage_percent", 0) > 85:
            return "gpu"
        else:
            return "none"
    
    def _get_failure_reason(self) -> str:
        """获取处理失败的原因"""
        bottleneck = self._identify_bottleneck()
        
        if bottleneck == "memory":
            return f"内存不足: 需要 {self.performance_stats.get('memory_usage_mb', 0):.0f}MB，可用 {self.ram * 1024}MB"
        elif bottleneck == "cpu":
            return f"CPU负载过高: {self.performance_stats.get('cpu_usage_percent', 0):.0f}%"
        elif bottleneck == "gpu":
            return f"GPU负载过高: {self.performance_stats.get('gpu_usage_percent', 0):.0f}%"
        else:
            return "设备配置不足，无法处理该视频"


class DeviceCompatibilityTester:
    """设备兼容性测试器，用于评估软件在不同设备上的性能表现"""
    
    def __init__(self):
        """初始化设备兼容性测试器"""
        # 设备规格矩阵
        self.DEVICE_MATRIX = [
            {"type": "low-end", "ram": 4, "gpu": False},
            {"type": "mid-range", "ram": 8, "gpu": True},
            {"type": "flagship", "ram": 12, "gpu": True}
        ]
        
        # 测试结果存储
        self.test_results = {}
        self.compatibility_matrix = {}
        
        # 创建设备模拟器
        self.emulators = {
            device["type"]: DeviceEmulator(device)
            for device in self.DEVICE_MATRIX
        }
        
        logger.info("设备兼容性测试器初始化完成")
    
    def full_test(self, video_path: str) -> Dict[str, Any]:
        """
        运行全面兼容性测试
        
        在所有设备配置上测试视频处理性能，
        并生成兼容性报告。
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            Dict[str, Any]: 测试结果报告
        """
        results = {}
        
        # 检查视频文件有效性
        if not os.path.exists(video_path):
            logger.error(f"视频文件不存在: {video_path}")
            return {"error": "视频文件不存在"}
        
        logger.info(f"开始全面兼容性测试: {video_path}")
        start_time = time.time()
        
        # 为每种设备配置运行测试
        for device in self.DEVICE_MATRIX:
            device_type = device["type"]
            logger.info(f"测试设备类型: {device_type}")
            
            # 获取仿真器
            emulator = self.emulators[device_type]
            
            # 运行测试
            result = emulator.render_test(video_path)
            results[device_type] = result
        
        # 处理测试结果
        success_count = sum(1 for r in results.values() if r.get("success", False))
        total_count = len(results)
        
        # 生成兼容性矩阵
        self.compatibility_matrix = {
            "timestamp": str(np.datetime64('now')),
            "video_path": video_path,
            "video_info": self._get_video_info(video_path),
            "compatibility_score": success_count / total_count if total_count > 0 else 0,
            "device_results": results,
            "minimum_requirements": self._determine_minimum_requirements(results),
            "optimization_suggestions": self._generate_optimization_suggestions(results)
        }
        
        # 存储测试结果
        self.test_results = {
            "last_test": self.compatibility_matrix
        }
        
        end_time = time.time()
        logger.info(f"兼容性测试完成，耗时: {end_time - start_time:.2f}秒")
        
        return self.compatibility_matrix
    
    def _get_current_device_info(self) -> Dict[str, Any]:
        """获取当前设备信息"""
        device_info = {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "python_version": platform.python_version(),
        }
        
        # 添加CPU信息
        if PSUTIL_AVAILABLE:
            device_info.update({
                "cpu_cores": psutil.cpu_count(logical=False),
                "cpu_threads": psutil.cpu_count(logical=True),
                "memory_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
                "memory_available_gb": round(psutil.virtual_memory().available / (1024**3), 2)
            })
        
        # 添加GPU信息
        if GPUTIL_AVAILABLE:
            try:
                gpus = GPUtil.getGPUs()
                if gpus:
                    device_info["gpu_info"] = [{
                        "name": gpu.name,
                        "memory_total": gpu.memoryTotal,
                        "memory_free": gpu.memoryFree
                    } for gpu in gpus]
            except Exception as e:
                logger.warning(f"获取GPU信息失败: {str(e)}")
        
        return device_info
    
    def _get_video_info(self, video_path: str) -> Dict[str, Any]:
        """获取视频基本信息"""
        # 简化实现，实际系统可能需要ffmpeg等工具
        file_size = os.path.getsize(video_path) if os.path.exists(video_path) else 0
        return {
            "file_size_bytes": file_size,
            "file_size_mb": round(file_size / (1024 * 1024), 2) if file_size > 0 else 0
        }
    
    def _determine_minimum_requirements(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """确定最低硬件要求"""
        min_requirements = {
            "ram_gb": 16,  # 默认值
            "gpu_required": True,
            "storage_type": "ssd",
            "cpu_cores": 4
        }
        
        # 如果低端设备测试通过，降低要求
        if test_results.get("low-end", {}).get("success", False):
            min_requirements.update({
                "ram_gb": 4,
                "gpu_required": False,
                "cpu_cores": 2
            })
        # 如果中端设备测试通过
        elif test_results.get("mid-range", {}).get("success", False):
            min_requirements.update({
                "ram_gb": 8,
                "gpu_required": True,
                "cpu_cores": 4
            })
        
        return min_requirements
    
    def _generate_optimization_suggestions(self, test_results: Dict[str, Any]) -> List[str]:
        """生成优化建议"""
        suggestions = []
        
        # 检查各设备类型的瓶颈
        for device_type, result in test_results.items():
            if not result.get("success", False):
                perf = result.get("performance", {})
                bottleneck = perf.get("bottleneck", "unknown")
                
                if bottleneck == "memory":
                    suggestions.append(f"优化内存使用，针对{device_type}设备")
                elif bottleneck == "cpu":
                    suggestions.append(f"降低CPU密集型操作，针对{device_type}设备")
                elif bottleneck == "gpu":
                    suggestions.append(f"优化GPU计算，针对{device_type}设备")
        
        # 添加通用建议
        if not test_results.get("low-end", {}).get("success", False):
            suggestions.append("考虑添加低端设备的特殊处理模式")
        
        # 避免重复建议
        return list(set(suggestions))
    
    def save_report(self, file_path: Optional[str] = None) -> str:
        """
        保存兼容性报告
        
        Args:
            file_path: 保存路径，如果不提供则使用默认路径
            
        Returns:
            str: 报告保存路径
        """
        if not self.compatibility_matrix:
            logger.warning("没有可用的测试结果")
            return ""
        
        if file_path is None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            file_path = os.path.join("data", "compatibility_reports", f"report_{timestamp}.json")
        
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # 添加当前设备信息
            report_data = {
                **self.compatibility_matrix,
                "current_device": self._get_current_device_info()
            }
            
            # 保存报告
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"兼容性报告已保存: {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"保存报告失败: {str(e)}")
            return ""


# 导出模块
__all__ = ['DeviceCompatibilityTester', 'DeviceEmulator'] 