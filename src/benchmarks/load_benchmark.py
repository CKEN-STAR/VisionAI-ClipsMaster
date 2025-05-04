"""加载性能分析模块

此模块负责分析模型加载性能，包括:
1. 加载时间测试
2. 内存使用分析
3. 设备利用率监控
4. 性能瓶颈检测
5. 优化建议生成
"""

import time
import psutil
import torch
import numpy as np
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from loguru import logger
from ..utils.cpu_feature import CPUFeatureDetector
from ..utils.memory_manager import MemoryManager
from ..utils.device_manager import HybridDevice

class LoadBenchmark:
    """加载性能分析器"""
    
    def __init__(self,
                 memory_manager: Optional[MemoryManager] = None,
                 device_manager: Optional[HybridDevice] = None):
        """初始化性能分析器
        
        Args:
            memory_manager: 内存管理器实例
            device_manager: 设备管理器实例
        """
        self.memory_manager = memory_manager or MemoryManager()
        self.device_manager = device_manager or HybridDevice()
        self.cpu_detector = CPUFeatureDetector()
        
        # 性能统计
        self._stats = {
            "load_times": [],
            "memory_usage": [],
            "device_utilization": [],
            "bottlenecks": []
        }
    
    def benchmark_load_time(self,
                          model_paths: List[str],
                          iterations: int = 3,
                          warm_up: bool = True) -> Dict:
        """测试模型加载时间
        
        Args:
            model_paths: 模型文件路径列表
            iterations: 每个模型测试次数
            warm_up: 是否进行预热
            
        Returns:
            Dict: 测试结果
        """
        results = {}
        
        for model_path in model_paths:
            try:
                model_name = Path(model_path).stem
                logger.info(f"开始测试模型: {model_name}")
                
                # 预热
                if warm_up:
                    self._warm_up_load(model_path)
                
                # 多次测试取平均
                load_times = []
                memory_usage = []
                device_util = []
                
                for i in range(iterations):
                    # 清理缓存
                    self._clear_cache()
                    
                    # 记录起始状态
                    start_memory = self.memory_manager.get_current_memory_usage()
                    start_time = time.perf_counter()
                    
                    # 加载模型
                    try:
                        self._load_model(model_path)
                        
                        # 记录结束状态
                        end_time = time.perf_counter()
                        end_memory = self.memory_manager.get_current_memory_usage()
                        device_usage = self.device_manager.get_device_utilization()
                        
                        # 计算指标
                        load_time = end_time - start_time
                        memory_delta = end_memory - start_memory
                        
                        load_times.append(load_time)
                        memory_usage.append(memory_delta)
                        device_util.append(device_usage)
                        
                        logger.info(f"迭代 {i+1}: 加载时间 {load_time:.2f}s")
                        
                    except Exception as e:
                        logger.error(f"加载失败: {str(e)}")
                        continue
                
                # 计算统计数据
                results[model_name] = {
                    "load_time": {
                        "mean": np.mean(load_times),
                        "std": np.std(load_times),
                        "min": np.min(load_times),
                        "max": np.max(load_times)
                    },
                    "memory_usage": {
                        "mean": np.mean(memory_usage) / (1024 * 1024),  # MB
                        "peak": np.max(memory_usage) / (1024 * 1024)    # MB
                    },
                    "device_utilization": {
                        "mean": np.mean(device_util, axis=0),
                        "peak": np.max(device_util, axis=0)
                    }
                }
                
                # 更新统计信息
                self._stats["load_times"].extend(load_times)
                self._stats["memory_usage"].extend(memory_usage)
                self._stats["device_utilization"].extend(device_util)
                
            except Exception as e:
                logger.error(f"测试失败 {model_name}: {str(e)}")
                continue
        
        return results
    
    def analyze_bottlenecks(self) -> List[Dict]:
        """分析性能瓶颈
        
        Returns:
            List[Dict]: 瓶颈分析结果
        """
        bottlenecks = []
        
        try:
            # 分析加载时间
            load_times = np.array(self._stats["load_times"])
            if len(load_times) > 0:
                if np.mean(load_times) > 5.0:  # 平均加载时间超过5秒
                    bottlenecks.append({
                        "type": "load_time",
                        "severity": "high",
                        "description": "模型加载时间过长",
                        "suggestion": "考虑使用量化模型或优化模型结构"
                    })
            
            # 分析内存使用
            memory_usage = np.array(self._stats["memory_usage"])
            if len(memory_usage) > 0:
                peak_memory = np.max(memory_usage) / (1024 * 1024)  # MB
                if peak_memory > 4096:  # 超过4GB
                    bottlenecks.append({
                        "type": "memory_usage",
                        "severity": "high",
                        "description": "内存使用量过大",
                        "suggestion": "考虑使用内存映射或分片加载"
                    })
            
            # 分析设备利用率
            device_util = np.array(self._stats["device_utilization"])
            if len(device_util) > 0:
                if np.mean(device_util) > 0.9:  # 设备利用率超过90%
                    bottlenecks.append({
                        "type": "device_utilization",
                        "severity": "medium",
                        "description": "设备利用率过高",
                        "suggestion": "考虑使用混合精度或优化批处理大小"
                    })
            
            # 检查CPU特性
            cpu_score = self.cpu_detector.estimate_performance_score()
            if cpu_score < 60:
                bottlenecks.append({
                    "type": "cpu_performance",
                    "severity": "medium",
                    "description": "CPU性能可能不足",
                    "suggestion": "考虑升级硬件或使用GPU加速"
                })
            
            # 更新统计信息
            self._stats["bottlenecks"] = bottlenecks
            
        except Exception as e:
            logger.error(f"瓶颈分析失败: {str(e)}")
        
        return bottlenecks
    
    def generate_report(self) -> Dict:
        """生成性能报告
        
        Returns:
            Dict: 性能报告
        """
        try:
            report = {
                "summary": {
                    "total_tests": len(self._stats["load_times"]),
                    "average_load_time": np.mean(self._stats["load_times"]),
                    "peak_memory_usage": np.max(self._stats["memory_usage"]) / (1024 * 1024),
                    "average_device_utilization": np.mean(self._stats["device_utilization"]),
                },
                "bottlenecks": self.analyze_bottlenecks(),
                "recommendations": self._generate_recommendations(),
                "system_info": {
                    "cpu_features": self.cpu_detector.get_cpu_details(),
                    "memory_info": self.memory_manager.get_memory_stats(),
                    "device_info": self.device_manager.get_device_info()
                }
            }
            
            return report
            
        except Exception as e:
            logger.error(f"生成报告失败: {str(e)}")
            return {}
    
    def _warm_up_load(self, model_path: str):
        """预热加载过程
        
        Args:
            model_path: 模型文件路径
        """
        try:
            logger.info("开始预热...")
            self._clear_cache()
            self._load_model(model_path)
            self._clear_cache()
            logger.info("预热完成")
            
        except Exception as e:
            logger.warning(f"预热失败: {str(e)}")
    
    def _load_model(self, model_path: str):
        """加载模型
        
        Args:
            model_path: 模型文件路径
        """
        # 这里应该实现实际的模型加载逻辑
        # 由于我们现在不下载英文模型，这里只模拟加载过程
        time.sleep(0.1)  # 模拟加载时间
    
    def _clear_cache(self):
        """清理缓存"""
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        self.memory_manager.cleanup()
    
    def _generate_recommendations(self) -> List[str]:
        """生成优化建议
        
        Returns:
            List[str]: 优化建议列表
        """
        recommendations = []
        
        try:
            # 基于CPU特性的建议
            cpu_suggestions = self.cpu_detector.suggest_optimizations()
            recommendations.extend(cpu_suggestions)
            
            # 基于内存使用的建议
            if np.mean(self._stats["memory_usage"]) > 2048 * 1024 * 1024:  # 2GB
                recommendations.append("建议使用增量加载或内存映射来减少内存使用")
            
            # 基于加载时间的建议
            if np.mean(self._stats["load_times"]) > 3.0:
                recommendations.append("建议使用异步加载或多线程加载来提高加载速度")
            
            # 基于设备利用率的建议
            if np.mean(self._stats["device_utilization"]) < 0.3:
                recommendations.append("当前设备利用率较低，可以考虑增加批处理大小")
            
        except Exception as e:
            logger.error(f"生成建议失败: {str(e)}")
        
        return recommendations 