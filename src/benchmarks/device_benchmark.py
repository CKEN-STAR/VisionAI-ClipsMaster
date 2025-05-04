"""性能基准测试模块

此模块负责执行系统性能基准测试，包括：
1. CPU性能测试
2. GPU性能测试
3. 内存速度测试
4. 磁盘IO测试
5. 模型推理性能测试
"""

import os
import time
import numpy as np
import torch
import psutil
from typing import Dict, List, Optional, Union
from loguru import logger

from src.utils.device_manager import HybridDevice, DeviceType
from src.utils.resource_predictor import ResourcePredictor

class DeviceBenchmark:
    """设备性能基准测试类"""
    
    def __init__(self):
        """初始化基准测试器"""
        self.device_manager = HybridDevice()
        self.resource_predictor = ResourcePredictor()
        
        # 基准测试参数
        self.cpu_test_size = 1000  # CPU测试矩阵大小
        self.gpu_test_size = 2000  # GPU测试矩阵大小
        self.memory_test_size = 1024 * 1024 * 100  # 100MB
        self.disk_test_size = 1024 * 1024 * 256    # 256MB
        
        # 性能评分基准
        self.score_weights = {
            "cpu": 0.3,
            "gpu": 0.3,
            "memory": 0.2,
            "disk": 0.2
        }
        
        # 测试结果
        self.benchmark_results = {}
    
    def run_cpu_benchmark(self) -> Dict[str, float]:
        """运行CPU性能测试
        
        Returns:
            Dict[str, float]: CPU性能指标
        """
        try:
            # 矩阵运算测试
            start_time = time.time()
            matrix_a = np.random.rand(self.cpu_test_size, self.cpu_test_size)
            matrix_b = np.random.rand(self.cpu_test_size, self.cpu_test_size)
            _ = np.dot(matrix_a, matrix_b)
            matrix_time = time.time() - start_time
            
            # 浮点运算测试
            start_time = time.time()
            for _ in range(1000000):
                _ = np.sin(np.random.rand()) * np.cos(np.random.rand())
            float_time = time.time() - start_time
            
            # 整数运算测试
            start_time = time.time()
            numbers = list(range(1000000))
            _ = sorted(numbers, reverse=True)
            int_time = time.time() - start_time
            
            results = {
                "matrix_time": matrix_time,
                "float_time": float_time,
                "int_time": int_time,
                "cpu_score": self._calculate_cpu_score(matrix_time, float_time, int_time)
            }
            
            self.benchmark_results["cpu"] = results
            return results
            
        except Exception as e:
            logger.error(f"CPU基准测试失败: {str(e)}")
            return {}
    
    def run_gpu_benchmark(self) -> Dict[str, float]:
        """运行GPU性能测试
        
        Returns:
            Dict[str, float]: GPU性能指标
        """
        try:
            if not torch.cuda.is_available():
                logger.warning("GPU不可用，跳过GPU基准测试")
                return {}
            
            # 准备GPU测试数据
            device = torch.device("cuda")
            matrix_a = torch.rand(self.gpu_test_size, self.gpu_test_size).to(device)
            matrix_b = torch.rand(self.gpu_test_size, self.gpu_test_size).to(device)
            
            # GPU矩阵运算测试
            torch.cuda.synchronize()
            start_time = time.time()
            _ = torch.matmul(matrix_a, matrix_b)
            torch.cuda.synchronize()
            matrix_time = time.time() - start_time
            
            # GPU内存传输测试
            cpu_tensor = torch.rand(self.gpu_test_size, self.gpu_test_size)
            start_time = time.time()
            gpu_tensor = cpu_tensor.to(device)
            torch.cuda.synchronize()
            transfer_time = time.time() - start_time
            
            # GPU并行计算测试
            start_time = time.time()
            for _ in range(10):
                _ = torch.nn.functional.relu(matrix_a)
            torch.cuda.synchronize()
            parallel_time = time.time() - start_time
            
            results = {
                "matrix_time": matrix_time,
                "transfer_time": transfer_time,
                "parallel_time": parallel_time,
                "gpu_score": self._calculate_gpu_score(matrix_time, transfer_time, parallel_time)
            }
            
            self.benchmark_results["gpu"] = results
            return results
            
        except Exception as e:
            logger.error(f"GPU基准测试失败: {str(e)}")
            return {}
    
    def run_memory_benchmark(self) -> Dict[str, float]:
        """运行内存性能测试
        
        Returns:
            Dict[str, float]: 内存性能指标
        """
        try:
            # 内存写入测试
            data = bytearray(self.memory_test_size)
            start_time = time.time()
            for i in range(0, self.memory_test_size, 4096):
                data[i] = i % 256
            write_time = time.time() - start_time
            
            # 内存读取测试
            start_time = time.time()
            for i in range(0, self.memory_test_size, 4096):
                _ = data[i]
            read_time = time.time() - start_time
            
            # 内存拷贝测试
            start_time = time.time()
            data_copy = data[:]
            copy_time = time.time() - start_time
            
            results = {
                "write_time": write_time,
                "read_time": read_time,
                "copy_time": copy_time,
                "memory_score": self._calculate_memory_score(write_time, read_time, copy_time)
            }
            
            self.benchmark_results["memory"] = results
            return results
            
        except Exception as e:
            logger.error(f"内存基准测试失败: {str(e)}")
            return {}
    
    def run_disk_benchmark(self) -> Dict[str, float]:
        """运行磁盘性能测试
        
        Returns:
            Dict[str, float]: 磁盘性能指标
        """
        try:
            test_file = "benchmark_test.tmp"
            data = os.urandom(self.disk_test_size)
            
            # 写入测试
            start_time = time.time()
            with open(test_file, "wb") as f:
                f.write(data)
            write_time = time.time() - start_time
            
            # 读取测试
            start_time = time.time()
            with open(test_file, "rb") as f:
                _ = f.read()
            read_time = time.time() - start_time
            
            # 随机访问测试
            start_time = time.time()
            with open(test_file, "rb") as f:
                for _ in range(100):
                    pos = np.random.randint(0, self.disk_test_size)
                    f.seek(pos)
                    _ = f.read(4096)
            random_time = time.time() - start_time
            
            # 清理测试文件
            try:
                os.remove(test_file)
            except Exception:
                pass
            
            results = {
                "write_time": write_time,
                "read_time": read_time,
                "random_time": random_time,
                "disk_score": self._calculate_disk_score(write_time, read_time, random_time)
            }
            
            self.benchmark_results["disk"] = results
            return results
            
        except Exception as e:
            logger.error(f"磁盘基准测试失败: {str(e)}")
            return {}
    
    def run_full_benchmark(self) -> Dict:
        """运行完整的基准测试
        
        Returns:
            Dict: 完整的基准测试结果
        """
        logger.info("开始运行完整基准测试...")
        
        # 运行各项测试
        cpu_results = self.run_cpu_benchmark()
        gpu_results = self.run_gpu_benchmark()
        memory_results = self.run_memory_benchmark()
        disk_results = self.run_disk_benchmark()
        
        # 计算总分
        total_score = self._calculate_total_score()
        
        # 生成性能等级和建议
        performance_level = self._get_performance_level(total_score)
        recommendations = self._generate_recommendations()
        
        results = {
            "total_score": total_score,
            "performance_level": performance_level,
            "cpu_benchmark": cpu_results,
            "gpu_benchmark": gpu_results,
            "memory_benchmark": memory_results,
            "disk_benchmark": disk_results,
            "recommendations": recommendations
        }
        
        logger.info(f"基准测试完成，总分: {total_score:.2f}")
        return results
    
    def _calculate_cpu_score(self,
                           matrix_time: float,
                           float_time: float,
                           int_time: float) -> float:
        """计算CPU性能得分"""
        # 基准时间（在中等配置机器上的测试时间）
        base_matrix = 2.0  # 秒
        base_float = 1.0   # 秒
        base_int = 0.5     # 秒
        
        # 计算相对性能比
        matrix_score = base_matrix / max(matrix_time, 0.001)
        float_score = base_float / max(float_time, 0.001)
        int_score = base_int / max(int_time, 0.001)
        
        # 加权平均
        return (matrix_score * 0.5 + float_score * 0.3 + int_score * 0.2) * 100
    
    def _calculate_gpu_score(self,
                           matrix_time: float,
                           transfer_time: float,
                           parallel_time: float) -> float:
        """计算GPU性能得分"""
        # 基准时间
        base_matrix = 0.5    # 秒
        base_transfer = 0.2  # 秒
        base_parallel = 0.3  # 秒
        
        # 计算相对性能比
        matrix_score = base_matrix / max(matrix_time, 0.001)
        transfer_score = base_transfer / max(transfer_time, 0.001)
        parallel_score = base_parallel / max(parallel_time, 0.001)
        
        # 加权平均
        return (matrix_score * 0.4 + transfer_score * 0.3 + parallel_score * 0.3) * 100
    
    def _calculate_memory_score(self,
                              write_time: float,
                              read_time: float,
                              copy_time: float) -> float:
        """计算内存性能得分"""
        # 基准时间
        base_write = 0.1  # 秒
        base_read = 0.05  # 秒
        base_copy = 0.02  # 秒
        
        # 计算相对性能比
        write_score = base_write / max(write_time, 0.001)
        read_score = base_read / max(read_time, 0.001)
        copy_score = base_copy / max(copy_time, 0.001)
        
        # 加权平均
        return (write_score * 0.3 + read_score * 0.4 + copy_score * 0.3) * 100
    
    def _calculate_disk_score(self,
                            write_time: float,
                            read_time: float,
                            random_time: float) -> float:
        """计算磁盘性能得分"""
        # 基准时间
        base_write = 0.5    # 秒
        base_read = 0.3     # 秒
        base_random = 1.0   # 秒
        
        # 计算相对性能比
        write_score = base_write / max(write_time, 0.001)
        read_score = base_read / max(read_time, 0.001)
        random_score = base_random / max(random_time, 0.001)
        
        # 加权平均
        return (write_score * 0.4 + read_score * 0.4 + random_score * 0.2) * 100
    
    def _calculate_total_score(self) -> float:
        """计算总性能得分"""
        total_score = 0.0
        
        if "cpu" in self.benchmark_results:
            total_score += self.benchmark_results["cpu"]["cpu_score"] * self.score_weights["cpu"]
            
        if "gpu" in self.benchmark_results:
            total_score += self.benchmark_results["gpu"]["gpu_score"] * self.score_weights["gpu"]
            
        if "memory" in self.benchmark_results:
            total_score += self.benchmark_results["memory"]["memory_score"] * self.score_weights["memory"]
            
        if "disk" in self.benchmark_results:
            total_score += self.benchmark_results["disk"]["disk_score"] * self.score_weights["disk"]
        
        return total_score
    
    def _get_performance_level(self, total_score: float) -> str:
        """根据总分确定性能等级"""
        if total_score >= 90:
            return "excellent"
        elif total_score >= 75:
            return "good"
        elif total_score >= 60:
            return "fair"
        else:
            return "poor"
    
    def _generate_recommendations(self) -> List[str]:
        """生成性能优化建议"""
        recommendations = []
        
        # CPU建议
        if "cpu" in self.benchmark_results:
            cpu_score = self.benchmark_results["cpu"]["cpu_score"]
            if cpu_score < 60:
                recommendations.append("CPU性能较弱，建议升级处理器或减少批处理大小")
        
        # GPU建议
        if "gpu" in self.benchmark_results:
            gpu_score = self.benchmark_results["gpu"]["gpu_score"]
            if gpu_score < 60:
                recommendations.append("GPU性能不足，建议使用更强大的显卡或降低模型量化等级")
        elif torch.cuda.is_available():
            recommendations.append("未检测到GPU，建议使用支持CUDA的显卡以提升性能")
        
        # 内存建议
        if "memory" in self.benchmark_results:
            memory_score = self.benchmark_results["memory"]["memory_score"]
            if memory_score < 60:
                recommendations.append("内存性能较低，建议使用更快的内存或增加内存容量")
        
        # 磁盘建议
        if "disk" in self.benchmark_results:
            disk_score = self.benchmark_results["disk"]["disk_score"]
            if disk_score < 60:
                recommendations.append("磁盘性能较慢，建议使用SSD存储设备")
        
        return recommendations 