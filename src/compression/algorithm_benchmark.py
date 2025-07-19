#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
压缩算法基准测试

对各种压缩算法进行基准测试，评估它们在不同场景下的性能
"""

import os
import time
import logging
import json
import numpy as np
from typing import Dict, List, Tuple, Any, Optional, Union
import matplotlib.pyplot as plt
from pathlib import Path
import threading

# 导入压缩器模块
from src.compression.compressors import (
    get_available_compressors,
    get_compressor,
    CompressorBase
)

# 配置日志
logger = logging.getLogger("AlgorithmBenchmark")

class CompressionBenchmark:
    """压缩算法基准测试类"""
    
    def __init__(self, output_dir: str = "reports/compression"):
        """
        初始化基准测试
        
        Args:
            output_dir: 输出目录
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 测试结果
        self.results = {}
        self.dataset_stats = {}
        
        # 缓存可用算法
        self.available_algorithms = get_available_compressors()
        
    def prepare_test_data(self, data_type: str = "text", size_mb: float = 1.0) -> bytes:
        """
        准备测试数据
        
        Args:
            data_type: 数据类型，可以是 'text', 'binary', 'numeric', 'model_weights', 'subtitle'
            size_mb: 数据大小（MB）
            
        Returns:
            bytes: 测试数据
        """
        size_bytes = int(size_mb * 1024 * 1024)
        
        if data_type == "text":
            # 创建随机文本数据
            chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 \n,.;:!?，。；：！？"
            text = "".join(np.random.choice(list(chars), size=size_bytes // 2))
            return text.encode('utf-8')
            
        elif data_type == "binary":
            # 创建随机二进制数据
            return np.random.bytes(size_bytes)
            
        elif data_type == "numeric":
            # 创建随机浮点数数组
            arr = np.random.randn(size_bytes // 8).astype(np.float64)
            return arr.tobytes()
            
        elif data_type == "model_weights":
            # 模拟模型权重数据（结构化浮点数）
            n = size_bytes // 16
            weights = []
            for i in range(5):  # 模拟多个权重层
                layer = np.random.randn(n // 5, 4).astype(np.float32)
                weights.append(layer)
            return np.concatenate([w.flatten() for w in weights]).tobytes()
            
        elif data_type == "subtitle":
            # 模拟字幕数据
            lines = []
            for i in range(size_bytes // 50):
                timestamp = f"{i//60:02d}:{i%60:02d}.000 --> {i//60:02d}:{i%60+2:02d}.000"
                text = "这是一段字幕文本，用于测试压缩算法。" if i % 2 == 0 else "This is subtitle text for testing compression algorithms."
                lines.extend([str(i+1), timestamp, text, ""])
            return "\n".join(lines).encode('utf-8')
            
        else:
            logger.warning(f"未知数据类型: {data_type}，使用随机二进制数据")
            return np.random.bytes(size_bytes)
    
    def benchmark_algorithm(self, data: bytes, algorithm: str) -> Dict[str, Any]:
        """
        测试单个算法的性能
        
        Args:
            data: 测试数据
            algorithm: 算法名称
            
        Returns:
            Dict: 测试结果
        """
        # 获取压缩器
        compressor = get_compressor(algorithm)
        if not compressor:
            return {
                "algorithm": algorithm,
                "available": False,
                "error": "压缩器不可用"
            }
            
        result = {
            "algorithm": algorithm,
            "original_size_bytes": len(data),
            "available": True
        }
        
        try:
            # 压缩测试
            start_time = time.time()
            compressed = compressor.compress(data)
            compress_time = time.time() - start_time
            
            # 解压测试
            start_time = time.time()
            decompressed = compressor.decompress(compressed)
            decompress_time = time.time() - start_time
            
            # 验证结果
            is_valid = decompressed == data
            
            # 记录结果
            result.update({
                "compressed_size_bytes": len(compressed),
                "ratio": len(compressed) / len(data),
                "compress_time_ms": compress_time * 1000,
                "decompress_time_ms": decompress_time * 1000,
                "compress_speed_mbps": (len(data) / 1024 / 1024) / compress_time,
                "decompress_speed_mbps": (len(compressed) / 1024 / 1024) / decompress_time,
                "valid": is_valid
            })
            
            # 如果压缩结果无效，记录错误
            if not is_valid:
                result["error"] = "压缩/解压结果验证失败"
                
        except Exception as e:
            logger.error(f"算法 {algorithm} 测试失败: {str(e)}")
            result["error"] = str(e)
            result["valid"] = False
            
        return result
    
    def run_benchmark(self, data_types: List[str] = None, sizes_mb: List[float] = None) -> Dict[str, Any]:
        """
        运行基准测试
        
        Args:
            data_types: 要测试的数据类型列表
            sizes_mb: 要测试的数据大小列表（MB）
            
        Returns:
            Dict: 测试结果
        """
        # 默认测试数据类型和大小
        if data_types is None:
            data_types = ["text", "binary", "numeric", "model_weights", "subtitle"]
            
        if sizes_mb is None:
            sizes_mb = [0.5, 5.0]
            
        # 清空之前的结果
        self.results = {}
        self.dataset_stats = {}
        
        # 对每种数据类型和大小进行测试
        for data_type in data_types:
            self.results[data_type] = {}
            
            for size_mb in sizes_mb:
                logger.info(f"测试数据类型: {data_type}, 大小: {size_mb}MB")
                
                # 准备测试数据
                data = self.prepare_test_data(data_type, size_mb)
                
                # 记录数据集统计信息
                key = f"{data_type}_{size_mb}MB"
                self.dataset_stats[key] = {
                    "type": data_type,
                    "size_mb": size_mb,
                    "size_bytes": len(data),
                    "entropy": self._calculate_entropy(data)
                }
                
                # 测试所有算法
                self.results[data_type][key] = {}
                for algorithm in self.available_algorithms:
                    logger.info(f"测试算法: {algorithm}")
                    
                    # 进行测试
                    result = self.benchmark_algorithm(data, algorithm)
                    
                    # 记录结果
                    self.results[data_type][key][algorithm] = result
        
        # 保存结果
        self._save_results()
        
        return self.results
                
    def _calculate_entropy(self, data: bytes) -> float:
        """
        计算数据的熵（信息量）
        
        Args:
            data: 输入数据
            
        Returns:
            float: 熵值
        """
        # 计算字节频率
        freq = np.zeros(256, dtype=np.float64)
        for b in data:
            freq[b] += 1
            
        # 计算概率
        prob = freq / len(data)
        prob = prob[prob > 0]  # 移除零概率
        
        # 计算熵
        entropy = -np.sum(prob * np.log2(prob))
        return entropy
    
    def _save_results(self) -> None:
        """保存测试结果"""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        
        # 保存为JSON
        result_file = self.output_dir / f"benchmark_results_{timestamp}.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump({
                "results": self.results,
                "dataset_stats": self.dataset_stats,
                "timestamp": timestamp
            }, f, indent=2)
            
        logger.info(f"结果已保存到: {result_file}")
            
        # 生成可视化
        self._generate_visualizations(timestamp)
    
    def _generate_visualizations(self, timestamp: str) -> None:
        """
        生成结果可视化
        
        Args:
            timestamp: 时间戳
        """
        # 创建图表目录
        charts_dir = self.output_dir / "charts"
        charts_dir.mkdir(exist_ok=True)
        
        # 对每种数据类型生成图表
        for data_type, size_results in self.results.items():
            for size_key, alg_results in size_results.items():
                # 提取算法名称和比率
                algorithms = []
                ratios = []
                compress_speeds = []
                decompress_speeds = []
                
                for alg, result in alg_results.items():
                    if result.get("valid", False) and "ratio" in result:
                        algorithms.append(alg)
                        ratios.append(result["ratio"])
                        compress_speeds.append(result.get("compress_speed_mbps", 0))
                        decompress_speeds.append(result.get("decompress_speed_mbps", 0))
                
                if not algorithms:
                    continue
                    
                # 按压缩率排序
                sort_idx = np.argsort(ratios)
                algorithms = [algorithms[i] for i in sort_idx]
                ratios = [ratios[i] for i in sort_idx]
                compress_speeds = [compress_speeds[i] for i in sort_idx]
                decompress_speeds = [decompress_speeds[i] for i in sort_idx]
                
                # 创建图表
                plt.figure(figsize=(12, 7))
                
                # 压缩率子图
                plt.subplot(2, 1, 1)
                bars = plt.bar(algorithms, ratios, color='skyblue')
                plt.ylabel('压缩率 (越小越好)')
                plt.title(f'数据类型: {data_type}, 大小: {size_key}')
                plt.xticks(rotation=45)
                plt.grid(axis='y', linestyle='--', alpha=0.7)
                
                # 添加数值标签
                for bar, ratio in zip(bars, ratios):
                    plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01,
                            f'{ratio:.2f}', ha='center', va='bottom')
                
                # 速度子图
                plt.subplot(2, 1, 2)
                x = np.arange(len(algorithms))
                width = 0.35
                
                plt.bar(x - width/2, compress_speeds, width, label='压缩速度 (MB/s)', color='green')
                plt.bar(x + width/2, decompress_speeds, width, label='解压速度 (MB/s)', color='orange')
                
                plt.ylabel('速度 (MB/s)')
                plt.xticks(x, algorithms, rotation=45)
                plt.legend()
                plt.grid(axis='y', linestyle='--', alpha=0.7)
                
                plt.tight_layout()
                
                # 保存图表
                chart_file = charts_dir / f"{data_type}_{size_key}_{timestamp}.png"
                plt.savefig(chart_file)
                plt.close()
                
                logger.info(f"图表已保存到: {chart_file}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        获取测试指标摘要
        
        Returns:
            Dict: 测试指标
        """
        if not self.results:
            return {"error": "未找到测试结果"}
            
        metrics = {
            "best_overall": {},
            "best_by_type": {},
            "fastest": {},
            "most_compact": {}
        }
        
        # 计算平均性能
        all_algorithm_metrics = {}
        
        for data_type, size_results in self.results.items():
            metrics["best_by_type"][data_type] = {}
            
            for size_key, alg_results in size_results.items():
                best_ratio = float('inf')
                best_alg_ratio = None
                
                fastest_compress = 0
                fastest_alg_compress = None
                
                fastest_decompress = 0
                fastest_alg_decompress = None
                
                for alg, result in alg_results.items():
                    if not result.get("valid", False):
                        continue
                        
                    # 初始化算法指标
                    if alg not in all_algorithm_metrics:
                        all_algorithm_metrics[alg] = {
                            "ratio_sum": 0,
                            "compress_speed_sum": 0,
                            "decompress_speed_sum": 0,
                            "count": 0
                        }
                    
                    # 累计指标
                    all_algorithm_metrics[alg]["ratio_sum"] += result["ratio"]
                    all_algorithm_metrics[alg]["compress_speed_sum"] += result.get("compress_speed_mbps", 0)
                    all_algorithm_metrics[alg]["decompress_speed_sum"] += result.get("decompress_speed_mbps", 0)
                    all_algorithm_metrics[alg]["count"] += 1
                    
                    # 更新最佳压缩率
                    if result["ratio"] < best_ratio:
                        best_ratio = result["ratio"]
                        best_alg_ratio = alg
                        
                    # 更新最快压缩速度
                    compress_speed = result.get("compress_speed_mbps", 0)
                    if compress_speed > fastest_compress:
                        fastest_compress = compress_speed
                        fastest_alg_compress = alg
                        
                    # 更新最快解压速度
                    decompress_speed = result.get("decompress_speed_mbps", 0)
                    if decompress_speed > fastest_decompress:
                        fastest_decompress = decompress_speed
                        fastest_alg_decompress = alg
                
                # 记录这个数据类型和大小的最佳结果
                if best_alg_ratio:
                    metrics["best_by_type"][data_type][size_key] = {
                        "best_ratio": {
                            "algorithm": best_alg_ratio,
                            "value": best_ratio
                        },
                        "fastest_compress": {
                            "algorithm": fastest_alg_compress,
                            "value": fastest_compress
                        },
                        "fastest_decompress": {
                            "algorithm": fastest_alg_decompress,
                            "value": fastest_decompress
                        }
                    }
        
        # 计算平均指标
        for alg, metrics_sum in all_algorithm_metrics.items():
            count = metrics_sum["count"]
            if count > 0:
                metrics_sum["avg_ratio"] = metrics_sum["ratio_sum"] / count
                metrics_sum["avg_compress_speed"] = metrics_sum["compress_speed_sum"] / count
                metrics_sum["avg_decompress_speed"] = metrics_sum["decompress_speed_sum"] / count
        
        # 找出总体最佳
        best_avg_ratio = float('inf')
        best_algorithm = None
        
        fastest_avg_compress = 0
        fastest_algorithm_compress = None
        
        fastest_avg_decompress = 0
        fastest_algorithm_decompress = None
        
        for alg, metrics_avg in all_algorithm_metrics.items():
            if "avg_ratio" in metrics_avg:
                # 更新最佳平均压缩率
                if metrics_avg["avg_ratio"] < best_avg_ratio:
                    best_avg_ratio = metrics_avg["avg_ratio"]
                    best_algorithm = alg
                    
                # 更新最快平均压缩速度
                if metrics_avg["avg_compress_speed"] > fastest_avg_compress:
                    fastest_avg_compress = metrics_avg["avg_compress_speed"]
                    fastest_algorithm_compress = alg
                    
                # 更新最快平均解压速度
                if metrics_avg["avg_decompress_speed"] > fastest_avg_decompress:
                    fastest_avg_decompress = metrics_avg["avg_decompress_speed"]
                    fastest_algorithm_decompress = alg
        
        # 记录总体最佳
        metrics["best_overall"] = {
            "algorithm": best_algorithm,
            "avg_ratio": best_avg_ratio
        }
        
        metrics["fastest"] = {
            "compress": {
                "algorithm": fastest_algorithm_compress,
                "avg_speed": fastest_avg_compress
            },
            "decompress": {
                "algorithm": fastest_algorithm_decompress,
                "avg_speed": fastest_avg_decompress
            }
        }
        
        metrics["all_metrics"] = all_algorithm_metrics
        
        return metrics

# 推荐算法映射
_ALGORITHM_RECOMMENDATIONS = {
    "model_weights": {
        "default": "zstd",
        "fallback": "gzip"
    },
    "subtitle": {
        "default": "lz4",
        "fallback": "gzip"
    },
    "numeric": {
        "default": "zstd",
        "fallback": "gzip"
    },
    "text": {
        "default": "lz4",
        "fallback": "gzip"
    },
    "binary": {
        "default": "zstd",
        "fallback": "gzip"
    }
}

def get_recommended_algorithm(data_type: str = "binary", 
                             balance_mode: str = "balanced") -> str:
    """
    获取推荐的压缩算法
    
    Args:
        data_type: 数据类型，可以是 'model_weights', 'subtitle', 'numeric', 'text', 'binary'
        balance_mode: 平衡模式，可以是 'speed', 'balanced', 'ratio'
        
    Returns:
        str: 推荐的算法名称
    """
    # 检查数据类型
    if data_type not in _ALGORITHM_RECOMMENDATIONS:
        logger.warning(f"未知数据类型: {data_type}，使用二进制推荐")
        data_type = "binary"
    
    # 根据平衡模式选择算法
    if balance_mode == "speed":
        # 速度优先
        if data_type == "subtitle" or data_type == "text":
            if get_compressor("lz4"):
                return "lz4"
        else:
            if get_compressor("zstd"):
                return "zstd"
        return "gzip"  # 默认回退到gzip
        
    elif balance_mode == "ratio":
        # 压缩率优先
        if get_compressor("zstd"):
            return "zstd"
        elif get_compressor("bzip2"):
            return "bzip2"
        return "gzip"  # 默认回退到gzip
        
    else:  # balanced
        # 平衡模式
        recommendation = _ALGORITHM_RECOMMENDATIONS[data_type]
        default_alg = recommendation["default"]
        
        # 检查首选算法是否可用
        if get_compressor(default_alg):
            return default_alg
            
        # 使用备选算法
        return recommendation["fallback"]


def benchmark_algorithms(data_types: List[str] = None, 
                        sizes_mb: List[float] = None,
                        output_dir: str = "reports/compression") -> Dict[str, Any]:
    """
    运行压缩算法基准测试的便捷函数
    
    Args:
        data_types: 要测试的数据类型列表
        sizes_mb: 要测试的数据大小列表（MB）
        output_dir: 输出目录
        
    Returns:
        Dict: 测试结果
    """
    benchmark = CompressionBenchmark(output_dir)
    results = benchmark.run_benchmark(data_types, sizes_mb)
    metrics = benchmark.get_metrics()
    
    return {
        "results": results,
        "metrics": metrics
    }


# 测试代码
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    # 测试基准
    print("开始算法基准测试...")
    results = benchmark_algorithms(
        data_types=["text", "model_weights"],
        sizes_mb=[0.1, 1.0]
    )
    
    # 打印测试指标
    metrics = results["metrics"]
    
    print("\n测试结果概要:")
    print(f"最佳总体算法: {metrics['best_overall']['algorithm']}, "
          f"平均压缩率: {metrics['best_overall']['avg_ratio']:.2f}")
    
    print(f"最快压缩: {metrics['fastest']['compress']['algorithm']}, "
          f"平均速度: {metrics['fastest']['compress']['avg_speed']:.2f} MB/s")
    
    print(f"最快解压: {metrics['fastest']['decompress']['algorithm']}, "
          f"平均速度: {metrics['fastest']['decompress']['avg_speed']:.2f} MB/s")
    
    # 每种数据类型的推荐
    print("\n各数据类型推荐算法:")
    for data_type in ["model_weights", "subtitle", "binary", "text", "numeric"]:
        alg = get_recommended_algorithm(data_type)
        print(f"{data_type}: {alg}") 