"""资源预测模型

此模块负责预测模型运行时所需的系统资源，包括：
1. 内存使用预测
2. 显存使用预测
3. 磁盘空间预测
4. CPU/GPU负载预测
5. 批处理大小建议
"""

import os
import math
import json
from typing import Dict, Optional, Tuple, Union
from loguru import logger

class ResourcePredictor:
    """资源需求预测器"""
    
    def __init__(self):
        """初始化资源预测器"""
        # 基础模型内存需求（字节）
        self.base_memory_requirements = {
            "Q2_K": 2.8 * 1024 * 1024 * 1024,  # 2.8GB
            "Q4_K_M": 4.1 * 1024 * 1024 * 1024,  # 4.1GB
            "Q5_K": 6.3 * 1024 * 1024 * 1024,   # 6.3GB
            "Q6_K": 7.8 * 1024 * 1024 * 1024,   # 7.8GB
            "Q8_0": 8.5 * 1024 * 1024 * 1024    # 8.5GB
        }
        
        # 运行时内存系数
        self.runtime_memory_factor = 1.5  # 运行时额外内存需求
        self.gpu_memory_factor = 1.7     # GPU模式下的额外显存需求
        
        # 磁盘空间预测基准（字节）
        self.disk_space_base = {
            "model": 10 * 1024 * 1024 * 1024,    # 基础模型文件
            "cache": 2 * 1024 * 1024 * 1024,     # 缓存文件
            "temp": 5 * 1024 * 1024 * 1024       # 临时文件
        }
    
    def predict_memory_usage(self,
                           model_size: int,
                           batch_size: int = 1,
                           use_gpu: bool = False) -> Dict[str, int]:
        """预测内存使用情况
        
        Args:
            model_size: 模型大小（字节）
            batch_size: 批处理大小
            use_gpu: 是否使用GPU
            
        Returns:
            Dict[str, int]: 预测的内存使用情况（字节）
        """
        try:
            # 基础内存需求
            base_memory = model_size * self.runtime_memory_factor
            
            # 批处理大小影响
            batch_memory = model_size * 0.1 * (batch_size - 1)  # 每增加一个batch增加10%内存
            
            # 运行时缓存
            runtime_cache = min(2 * 1024 * 1024 * 1024,  # 最大2GB缓存
                              model_size * 0.2)          # 或模型大小的20%
            
            # 系统预留
            system_reserve = 2 * 1024 * 1024 * 1024  # 2GB系统预留
            
            total_memory = base_memory + batch_memory + runtime_cache + system_reserve
            
            # GPU模式下的显存预测
            gpu_memory = 0
            if use_gpu:
                gpu_memory = total_memory * self.gpu_memory_factor
            
            return {
                "total_memory": int(total_memory),
                "base_memory": int(base_memory),
                "batch_memory": int(batch_memory),
                "runtime_cache": int(runtime_cache),
                "system_reserve": int(system_reserve),
                "gpu_memory": int(gpu_memory) if use_gpu else 0
            }
            
        except Exception as e:
            logger.error(f"内存使用预测失败: {str(e)}")
            return {}
    
    def predict_disk_space(self,
                          model_size: int,
                          include_cache: bool = True) -> Dict[str, int]:
        """预测所需磁盘空间
        
        Args:
            model_size: 模型大小（字节）
            include_cache: 是否包含缓存空间
            
        Returns:
            Dict[str, int]: 预测的磁盘空间使用情况（字节）
        """
        try:
            # 基础空间需求
            base_space = self.disk_space_base["model"]
            
            # 模型文件空间
            model_space = model_size * 1.1  # 预留10%空间给模型文件
            
            # 缓存空间
            cache_space = (self.disk_space_base["cache"] if include_cache else 0)
            
            # 临时文件空间
            temp_space = self.disk_space_base["temp"]
            
            # 总空间
            total_space = base_space + model_space + cache_space + temp_space
            
            return {
                "total_space": int(total_space),
                "base_space": int(base_space),
                "model_space": int(model_space),
                "cache_space": int(cache_space),
                "temp_space": int(temp_space)
            }
            
        except Exception as e:
            logger.error(f"磁盘空间预测失败: {str(e)}")
            return {}
    
    def predict_optimal_batch_size(self,
                                 available_memory: int,
                                 model_size: int,
                                 min_batch: int = 1,
                                 max_batch: int = 32) -> int:
        """预测最优批处理大小
        
        Args:
            available_memory: 可用内存（字节）
            model_size: 模型大小（字节）
            min_batch: 最小批处理大小
            max_batch: 最大批处理大小
            
        Returns:
            int: 建议的批处理大小
        """
        try:
            # 预留系统内存和运行时缓存
            usable_memory = available_memory - (
                2 * 1024 * 1024 * 1024 +  # 系统预留
                model_size * 0.2           # 运行时缓存
            )
            
            # 每个批次的内存开销
            memory_per_batch = model_size * 0.1
            
            # 计算理论最大批处理大小
            theoretical_max = int(usable_memory / memory_per_batch)
            
            # 确保在合理范围内
            optimal_batch = min(max(theoretical_max, min_batch), max_batch)
            
            return optimal_batch
            
        except Exception as e:
            logger.error(f"批处理大小预测失败: {str(e)}")
            return min_batch
    
    def predict_performance(self,
                          model_size: int,
                          batch_size: int,
                          use_gpu: bool = False) -> Dict[str, Union[float, str]]:
        """预测性能指标
        
        Args:
            model_size: 模型大小（字节）
            batch_size: 批处理大小
            use_gpu: 是否使用GPU
            
        Returns:
            Dict: 性能预测指标
        """
        try:
            # 基础推理时间（毫秒）
            base_inference_time = 100 if use_gpu else 300
            
            # 批处理影响
            batch_factor = math.log2(batch_size + 1) * 0.7
            
            # 模型大小影响
            size_factor = (model_size / (4 * 1024 * 1024 * 1024)) * 1.2
            
            # 预测推理时间
            inference_time = base_inference_time * batch_factor * size_factor
            
            # 预测吞吐量（每秒样本数）
            throughput = batch_size / (inference_time / 1000)
            
            # 预测CPU/GPU使用率
            if use_gpu:
                gpu_util = min(95, 40 + batch_size * 5)  # 最高95%
                cpu_util = 30  # GPU模式下CPU使用率较低
            else:
                gpu_util = 0
                cpu_util = min(95, 50 + batch_size * 10)  # 最高95%
            
            return {
                "inference_time_ms": round(inference_time, 2),
                "throughput_samples_per_sec": round(throughput, 2),
                "estimated_cpu_util": round(cpu_util, 1),
                "estimated_gpu_util": round(gpu_util, 1) if use_gpu else 0,
                "performance_level": self._get_performance_level(inference_time, throughput)
            }
            
        except Exception as e:
            logger.error(f"性能预测失败: {str(e)}")
            return {}
    
    def _get_performance_level(self,
                             inference_time: float,
                             throughput: float) -> str:
        """根据性能指标确定性能等级"""
        if inference_time < 100 and throughput > 10:
            return "excellent"
        elif inference_time < 200 and throughput > 5:
            return "good"
        elif inference_time < 500 and throughput > 2:
            return "fair"
        else:
            return "poor"
    
    def get_resource_summary(self,
                           model_size: int,
                           batch_size: int = 1,
                           use_gpu: bool = False) -> Dict:
        """获取完整的资源需求摘要
        
        Args:
            model_size: 模型大小（字节）
            batch_size: 批处理大小
            use_gpu: 是否使用GPU
            
        Returns:
            Dict: 资源需求摘要
        """
        try:
            summary = {
                "memory": self.predict_memory_usage(
                    model_size, batch_size, use_gpu
                ),
                "disk": self.predict_disk_space(
                    model_size
                ),
                "performance": self.predict_performance(
                    model_size, batch_size, use_gpu
                ),
                "recommendations": self._get_recommendations(
                    model_size, batch_size, use_gpu
                )
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"资源摘要生成失败: {str(e)}")
            return {}
    
    def _get_recommendations(self,
                           model_size: int,
                           batch_size: int,
                           use_gpu: bool) -> Dict[str, str]:
        """生成资源使用建议
        
        Args:
            model_size: 模型大小（字节）
            batch_size: 批处理大小
            use_gpu: 是否使用GPU
            
        Returns:
            Dict[str, str]: 资源使用建议
        """
        recommendations = {}
        
        try:
            # 内存建议
            memory_usage = self.predict_memory_usage(model_size, batch_size, use_gpu)
            if memory_usage["total_memory"] > 16 * 1024 * 1024 * 1024:  # 16GB
                recommendations["memory"] = "建议增加系统内存或使用更小的模型"
            
            # GPU建议
            if use_gpu and memory_usage["gpu_memory"] > 8 * 1024 * 1024 * 1024:  # 8GB
                recommendations["gpu"] = "建议使用更大显存的GPU或减小批处理大小"
            
            # 批处理大小建议
            perf = self.predict_performance(model_size, batch_size, use_gpu)
            if perf["performance_level"] == "poor" and batch_size > 1:
                recommendations["batch_size"] = "建议减小批处理大小以提高性能"
            
            # 磁盘空间建议
            disk_usage = self.predict_disk_space(model_size)
            if disk_usage["total_space"] > 100 * 1024 * 1024 * 1024:  # 100GB
                recommendations["disk"] = "建议确保有足够的磁盘空间"
            
            return recommendations
            
        except Exception as e:
            logger.error(f"建议生成失败: {str(e)}")
            return {"error": "无法生成资源使用建议"} 