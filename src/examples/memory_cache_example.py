#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""内存缓存联动示例

此示例展示了如何在实际应用中集成内存缓存联动功能，
特别是在资源受限环境下（如4GB内存无独显设备）高效运行大型模型。
"""

import os
import sys
import time
import threading
import random
import numpy as np
from typing import Dict, Any, List
from loguru import logger

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.cache import (
    model_shard_cache,
    memory_cache_link,
    sync_with_memory_guard
)


class ModelShardSimulator:
    """模型分片模拟器
    
    模拟不同大小和重要性的模型分片，用于测试缓存系统。
    """
    
    def __init__(self, model_name: str = "qwen2.5-7b-zh"):
        """初始化模型分片模拟器
        
        Args:
            model_name: 模型名称
        """
        self.model_name = model_name
        
        # 模拟不同层的分片大小和重要性
        self.shard_specs = {
            # 分片名称: (大小MB, 重要性)
            "embedding": (120, 1.5),        # 嵌入层，较大但非常重要
            "attention_1": (90, 1.3),       # 第一注意力层，重要
            "attention_2": (90, 1.2),       # 第二注意力层，重要
            "attention_3": (90, 1.1),       # 第三注意力层
            "attention_4": (90, 1.0),       # 第四注意力层
            "ffn_1": (150, 1.2),            # 第一前馈层，较大且重要
            "ffn_2": (150, 1.1),            # 第二前馈层
            "ffn_3": (150, 1.0),            # 第三前馈层
            "ffn_4": (150, 0.9),            # 第四前馈层
            "lm_head": (80, 1.4)            # 语言模型头，较小但重要
        }
        
        # 已加载的分片
        self.loaded_shards: Dict[str, np.ndarray] = {}
        
        # 分片访问统计
        self.access_stats = {name: 0 for name in self.shard_specs}
        
        logger.info(f"模型分片模拟器初始化完成: {model_name}, {len(self.shard_specs)}个分片")
    
    def load_shard(self, shard_name: str) -> np.ndarray:
        """加载模型分片
        
        如果分片已在缓存中，直接获取；否则创建并缓存
        
        Args:
            shard_name: 分片名称
            
        Returns:
            np.ndarray: 分片数据
        """
        # 构建缓存键
        cache_key = f"{self.model_name}_{shard_name}"
        
        # 尝试从缓存获取
        shard_data = model_shard_cache.get(cache_key)
        
        if shard_data is not None:
            # 缓存命中
            logger.debug(f"缓存命中: {shard_name}")
            
            # 更新访问统计
            self.access_stats[shard_name] += 1
            
            return shard_data
        
        # 缓存未命中，创建模拟分片
        logger.info(f"缓存未命中，加载分片: {shard_name}")
        
        # 获取分片规格
        if shard_name not in self.shard_specs:
            raise ValueError(f"未知的分片名称: {shard_name}")
        
        size_mb, importance = self.shard_specs[shard_name]
        
        # 创建模拟数据
        bytes_per_mb = 1024 * 1024
        shard_data = np.ones(size_mb * bytes_per_mb // 8, dtype=np.float64)
        
        # 放入缓存
        model_shard_cache.put(
            cache_key, 
            shard_data, 
            size_bytes=size_mb*bytes_per_mb,
            importance=importance
        )
        
        # 记录到已加载分片
        self.loaded_shards[shard_name] = shard_data
        
        # 更新访问统计
        self.access_stats[shard_name] += 1
        
        # 每次加载后检查内存状态
        sync_with_memory_guard()
        
        return shard_data
    
    def execute_inference(self, sequence_length: int = 128, random_access: bool = False):
        """执行推理，模拟访问不同分片
        
        Args:
            sequence_length: 序列长度，影响分片访问次数
            random_access: 是否随机访问分片，否则按顺序访问
        
        Returns:
            Dict[str, Any]: 推理结果和统计信息
        """
        logger.info(f"开始执行推理，序列长度: {sequence_length}, 随机访问: {random_access}")
        
        # 模拟推理过程中的分片访问
        access_sequence = []
        
        # 确定访问顺序
        if random_access:
            # 随机访问模式，根据Zipf分布（模拟真实访问模式，某些分片被频繁访问）
            shard_names = list(self.shard_specs.keys())
            
            # 按照Zipf分布生成访问序列
            for _ in range(sequence_length):
                # 简化的Zipf模拟
                rank = int(np.random.zipf(1.5, 1)[0]) % len(shard_names)
                if rank >= len(shard_names):
                    rank = len(shard_names) - 1
                access_sequence.append(shard_names[rank])
        else:
            # 顺序访问模式
            layers_sequence = [
                "embedding",  # 首先是embedding
                "attention_1", "ffn_1",  # 第一层
                "attention_2", "ffn_2",  # 第二层
                "attention_3", "ffn_3",  # 第三层
                "attention_4", "ffn_4",  # 第四层
                "lm_head"  # 最后是输出层
            ]
            
            # 重复多次以达到指定序列长度
            access_sequence = layers_sequence * (sequence_length // len(layers_sequence) + 1)
            access_sequence = access_sequence[:sequence_length]
        
        # 执行分片访问
        start_time = time.time()
        for i, shard_name in enumerate(access_sequence):
            # 加载分片
            shard = self.load_shard(shard_name)
            
            # 模拟使用分片进行计算（简单求和）
            result = np.sum(shard[:100])
            
            # 每10次访问检查一次内存状态
            if i % 10 == 0:
                logger.debug(f"推理进度: {i+1}/{sequence_length} 分片: {shard_name}")
        
        # 计算耗时
        inference_time = time.time() - start_time
        
        # 获取缓存统计
        cache_stats = model_shard_cache.get_stats()
        
        # 准备返回结果
        result = {
            "sequence_length": sequence_length,
            "random_access": random_access,
            "inference_time": inference_time,
            "cache_hit_rate": cache_stats.get("hit_rate", 0),
            "cache_items_count": cache_stats.get("items_count", 0),
            "cache_size_mb": cache_stats.get("current_size_bytes", 0) / (1024*1024),
            "access_stats": dict(self.access_stats)
        }
        
        logger.info(f"推理完成，耗时: {inference_time:.2f}秒, 缓存命中率: {result['cache_hit_rate']:.2%}")
        
        return result


def simulate_low_memory_environment():
    """模拟低内存环境中的模型使用"""
    logger.info("=== 模拟低内存环境下的模型推理 ===")
    
    # 创建模型分片模拟器
    model_simulator = ModelShardSimulator("qwen2.5-7b-zh")
    
    # 创建工作线程函数
    def worker_thread(thread_id: int, sequence_length: int, is_random: bool):
        """工作线程
        
        Args:
            thread_id: 线程ID
            sequence_length: 序列长度
            is_random: 是否随机访问
        """
        logger.info(f"线程 {thread_id} 开始执行推理")
        
        # 执行推理
        result = model_simulator.execute_inference(
            sequence_length=sequence_length,
            random_access=is_random
        )
        
        logger.info(f"线程 {thread_id} 完成推理，耗时: {result['inference_time']:.2f}秒")
    
    # 创建并启动工作线程
    threads = []
    
    # 模拟不同类型的工作负载
    thread_configs = [
        (1, 50, False),   # 顺序访问，短序列
        (2, 100, True),   # 随机访问，中序列
        (3, 30, False),   # 顺序访问，短序列
        (4, 80, True)     # 随机访问，中序列
    ]
    
    # 启动线程
    for thread_id, seq_len, is_random in thread_configs:
        thread = threading.Thread(
            target=worker_thread,
            args=(thread_id, seq_len, is_random),
            daemon=True
        )
        threads.append(thread)
        thread.start()
        # 稍微延迟，避免同时启动
        time.sleep(1)
    
    # 等待所有线程完成
    for thread in threads:
        thread.join()
    
    # 获取最终缓存状态
    final_stats = model_shard_cache.get_stats()
    memory_link_stats = memory_cache_link.get_stats()
    
    logger.info("\n=== 最终统计 ===")
    logger.info(f"缓存项数量: {final_stats['items_count']}")
    logger.info(f"缓存大小: {final_stats['current_size_bytes'] / (1024*1024):.2f}MB")
    logger.info(f"缓存命中率: {final_stats['hit_rate']:.2%}")
    logger.info(f"内存联动状态: {memory_link_stats['current_status']}")
    logger.info(f"内存联动操作次数: {memory_link_stats['actions_taken']}")


def demonstrate_features():
    """演示内存缓存联动的主要特性"""
    logger.info("\n=== 功能演示 ===")
    
    # 1. 展示不同内存阈值下的响应
    logger.info("1. 展示不同内存阈值下的响应")
    
    # 创建模型分片模拟器
    simulator = ModelShardSimulator()
    
    # 按顺序预加载几个分片
    logger.info("预加载分片...")
    for shard_name in ["embedding", "attention_1", "ffn_1"]:
        simulator.load_shard(shard_name)
    
    # 查看当前缓存状态
    cache_stats = model_shard_cache.get_stats()
    logger.info(f"初始缓存状态: {cache_stats['items_count']}个项目, "
               f"{cache_stats['current_size_bytes'] / (1024*1024):.2f}MB")
    
    # 2. 展示热点数据保护
    logger.info("\n2. 展示热点数据保护")
    
    # 反复访问embedding分片，使其成为热点
    logger.info("创建热点数据...")
    for _ in range(15):  # 超过热点阈值
        simulator.load_shard("embedding")
    
    # 3. 展示在内存压力下的行为
    logger.info("\n3. 展示在内存压力下的行为")
    
    # 创建大数组模拟内存压力
    logger.info("模拟内存压力...")
    pressure_arrays = []
    try:
        for i in range(3):
            # 每次增加500MB
            size_mb = 500
            logger.info(f"增加 {size_mb}MB 内存压力...")
            pressure_arrays.append(np.ones(size_mb * 1024 * 1024 // 8, dtype=np.float64))
            
            # 检查内存状态
            result = memory_cache_link.force_check()
            logger.info(f"内存检查结果: {result}")
            
            # 尝试加载新分片
            new_shard = f"attention_{i+2}"
            logger.info(f"尝试加载分片: {new_shard}")
            simulator.load_shard(new_shard)
            
            # 检查热点是否保留
            embedding_data = simulator.load_shard("embedding")
            logger.info(f"热点数据 'embedding' 是否保留: {embedding_data is not None}")
    
    finally:
        # 释放内存压力
        logger.info("释放内存压力...")
        del pressure_arrays
        import gc
        gc.collect()
    
    # 最终状态
    cache_stats = model_shard_cache.get_stats()
    memory_stats = memory_cache_link.get_stats()
    
    logger.info("\n=== 最终状态 ===")
    logger.info(f"缓存项数量: {cache_stats['items_count']}")
    logger.info(f"缓存大小: {cache_stats['current_size_bytes'] / (1024*1024):.2f}MB")
    logger.info(f"内存联动状态: {memory_stats['current_status']}")
    logger.info(f"热点保护效果: embedding分片的访问次数 = {simulator.access_stats['embedding']}")
    logger.info("演示完成")


def main():
    """主函数"""
    logger.info("开始内存缓存联动示例")
    
    # 确保缓存为空
    model_shard_cache.clear()
    
    # 演示特性
    demonstrate_features()
    
    # 模拟低内存环境
    simulate_low_memory_environment()
    
    logger.info("示例结束")


if __name__ == "__main__":
    main() 