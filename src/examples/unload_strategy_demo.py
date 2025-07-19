#!/usr/bin/env python
"""分片卸载策略演示

此脚本演示如何使用分片卸载策略自动管理内存中的分片，
优先卸载无依赖、最少使用和内存占用最大的分片。
"""

import os
import gc
import time
import random
import torch
import argparse
from loguru import logger

from src.sharding.metadata_manager import MetadataManager
from src.sharding.cache_manager import ShardManager
from src.sharding.unload_strategy import create_unload_strategy, UnloadPriority


def simulate_memory_pressure():
    """模拟内存压力
    
    创建一个大的张量占用内存，然后释放
    """
    # 创建一个大的张量 (约1GB)
    large_tensor = torch.ones((1024, 1024, 128), dtype=torch.float32)
    logger.info(f"已分配 {large_tensor.nelement() * large_tensor.element_size() / 1024 / 1024:.2f} MB 内存")
    
    # 等待一段时间
    time.sleep(2)
    
    # 释放内存
    del large_tensor
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    
    logger.info("已释放内存")


def create_test_metadata(model_name="test_model", shard_count=10):
    """创建测试用的元数据
    
    Args:
        model_name: 模型名称
        shard_count: 分片数量
    
    Returns:
        MetadataManager: 元数据管理器
    """
    metadata_manager = MetadataManager()
    
    # 创建分片元数据
    shards = {}
    for i in range(shard_count):
        shard_id = f"shard_{i}"
        # 随机生成依赖关系（保证没有循环依赖）
        dependencies = [f"shard_{j}" for j in range(i) if random.random() < 0.3]
        
        # 随机分配层
        layers = [f"layer_{i}_{j}" for j in range(random.randint(1, 3))]
        
        # 分片大小（随机，用于测试内存策略）
        size_mb = random.randint(50, 500)
        
        shards[shard_id] = {
            "id": shard_id,
            "path": f"models/{model_name}/shards/{shard_id}.bin",
            "size_bytes": size_mb * 1024 * 1024,  # 转为字节
            "depends_on": dependencies,
            "layers": layers
        }
    
    # 设置元数据
    metadata_manager.set_metadata(model_name, {
        "name": model_name,
        "version": "1.0.0",
        "shards": shards
    })
    
    return metadata_manager


def demo_unload_strategy():
    """演示分片卸载策略"""
    logger.info("开始分片卸载策略演示")
    
    # 创建测试元数据
    model_name = "unload_test_model"
    shard_count = 8
    metadata_manager = create_test_metadata(model_name, shard_count)
    
    # 创建分片管理器
    shard_manager = ShardManager(
        model_name=model_name,
        max_shards_in_memory=5,  # 最多5个分片同时加载
        metadata_manager=metadata_manager
    )
    
    # 创建卸载策略
    unload_strategy = create_unload_strategy(
        shard_manager=shard_manager,
        priority="hybrid",
        memory_threshold=70.0,  # 内存使用率超过70%时触发卸载
        min_cache_size=2  # 缓存中至少保留2个分片
    )
    
    logger.info("=== 测试场景1: 按顺序加载分片 ===")
    # 按顺序加载分片
    for i in range(shard_count):
        shard_id = f"shard_{i}"
        logger.info(f"加载分片: {shard_id}")
        shard_manager.load_shard(shard_id, recursive=False)
        
        # 显示当前缓存状态
        cached_shards = shard_manager.shard_cache.get_cached_shards()
        logger.info(f"当前缓存分片: {cached_shards}")
        
        # 当内存不足时触发卸载
        if i >= 3:  # 从第4个分片开始模拟内存压力
            # 模拟内存压力
            simulate_memory_pressure()
            
            # 触发卸载
            unloaded_count = unload_strategy.trigger_unload_if_needed()
            logger.info(f"已卸载 {unloaded_count} 个分片")
            
            # 显示卸载后的缓存状态
            cached_shards = shard_manager.shard_cache.get_cached_shards()
            logger.info(f"卸载后缓存分片: {cached_shards}")
        
        # 等待一段时间
        time.sleep(1)
    
    # 清空缓存
    shard_manager.clear_cache()
    
    logger.info("\n=== 测试场景2: 随机访问分片 ===")
    # 创建一个新的卸载策略，使用最近最少使用（LRU）优先级
    unload_strategy = create_unload_strategy(
        shard_manager=shard_manager,
        priority="lru",
        memory_threshold=70.0,
        min_cache_size=2
    )
    
    # 随机访问分片
    for _ in range(10):
        # 随机选择一个分片
        shard_id = f"shard_{random.randint(0, shard_count-1)}"
        logger.info(f"访问分片: {shard_id}")
        shard_manager.load_shard(shard_id, recursive=False)
        
        # 显示当前缓存状态
        cached_shards = shard_manager.shard_cache.get_cached_shards()
        logger.info(f"当前缓存分片: {cached_shards}")
        
        # 模拟内存压力并触发卸载
        simulate_memory_pressure()
        unloaded_count = unload_strategy.trigger_unload_if_needed()
        
        if unloaded_count > 0:
            logger.info(f"已卸载 {unloaded_count} 个分片")
            cached_shards = shard_manager.shard_cache.get_cached_shards()
            logger.info(f"卸载后缓存分片: {cached_shards}")
        
        # 等待一段时间
        time.sleep(1)
    
    # 清空缓存
    shard_manager.clear_cache()
    
    logger.info("\n=== 测试场景3: 基于内存占用卸载 ===")
    # 创建一个新的卸载策略，使用内存占用大小优先级
    unload_strategy = create_unload_strategy(
        shard_manager=shard_manager,
        priority="memory",
        memory_threshold=70.0,
        min_cache_size=2
    )
    
    # 加载所有分片
    logger.info("加载所有分片")
    for i in range(shard_count):
        shard_id = f"shard_{i}"
        shard_manager.load_shard(shard_id, recursive=False)
    
    # 显示当前缓存状态和内存占用
    cached_shards = shard_manager.shard_cache.get_cached_shards()
    logger.info(f"当前缓存分片: {cached_shards}")
    
    # 显示内存占用
    logger.info("分片内存占用:")
    for shard_id in cached_shards:
        memory_usage = unload_strategy.memory_usage.get(shard_id, 0) / (1024 * 1024)
        logger.info(f"  {shard_id}: {memory_usage:.2f} MB")
    
    # 模拟内存压力并触发卸载
    simulate_memory_pressure()
    unloaded_count = unload_strategy.trigger_unload_if_needed()
    
    if unloaded_count > 0:
        logger.info(f"已卸载 {unloaded_count} 个分片")
        cached_shards = shard_manager.shard_cache.get_cached_shards()
        logger.info(f"卸载后缓存分片: {cached_shards}")
    
    logger.info("分片卸载策略演示完成")


if __name__ == "__main__":
    # 设置日志级别
    logger.remove()
    logger.add(
        lambda msg: print(msg, end=""), 
        level="INFO", 
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{function}</cyan>: <level>{message}</level>"
    )
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="分片卸载策略演示")
    parser.add_argument(
        "--strategy", 
        type=str, 
        choices=["no_dependencies", "lru", "memory", "hybrid"],
        default="hybrid",
        help="卸载策略"
    )
    parser.add_argument(
        "--threshold", 
        type=float, 
        default=70.0,
        help="内存使用率阈值"
    )
    args = parser.parse_args()
    
    # 运行演示
    demo_unload_strategy() 