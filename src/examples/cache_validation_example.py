#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""缓存验证器使用示例

此示例展示了如何在实际应用中使用缓存验证器，包括：
1. 缓存一致性验证的应用场景
2. 热点数据和冷数据的差异化验证策略
3. 如何处理验证失败情况
4. 如何调整验证参数以满足不同需求
"""

import os
import sys
import time
import numpy as np
import json
from loguru import logger

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.cache import (
    model_shard_cache,
    cache_janitor, 
    cache_validator,
    sync_with_memory_guard
)


class ModelManager:
    """模型管理器
    
    模拟实际应用中模型加载和管理过程
    """
    
    def __init__(self, model_name: str = "qwen2.5-7b-zh"):
        """初始化模型管理器
        
        Args:
            model_name: 模型名称
        """
        self.model_name = model_name
        self.loaded_shards = {}
        
        # 模拟模型分片信息
        self.shard_info = {
            f"{model_name}_embedding": {"size_mb": 120, "importance": 1.5},
            f"{model_name}_attention_1": {"size_mb": 90, "importance": 1.3},
            f"{model_name}_attention_2": {"size_mb": 90, "importance": 1.2},
            f"{model_name}_attention_3": {"size_mb": 90, "importance": 1.1},
            f"{model_name}_ffn_1": {"size_mb": 150, "importance": 1.2},
            f"{model_name}_ffn_2": {"size_mb": 150, "importance": 1.1},
            f"{model_name}_lm_head": {"size_mb": 80, "importance": 1.4}
        }
        
        logger.info(f"模型管理器初始化完成: {model_name}")
    
    def create_mock_data(self, size_mb: int, seed: int) -> np.ndarray:
        """创建模拟数据
        
        Args:
            size_mb: 数据大小(MB)
            seed: 随机种子
            
        Returns:
            numpy数组
        """
        np.random.seed(seed)
        bytes_per_mb = 1024 * 1024
        return np.random.rand(size_mb * bytes_per_mb // 8).astype(np.float64)
    
    def load_shard(self, shard_name: str) -> np.ndarray:
        """加载模型分片
        
        Args:
            shard_name: 分片名称
            
        Returns:
            分片数据
        """
        # 检查缓存中是否存在
        shard_data = model_shard_cache.get(shard_name)
        
        if shard_data is not None:
            logger.debug(f"缓存命中: {shard_name}")
            return shard_data
        
        # 缓存未命中，创建模拟数据
        logger.info(f"缓存未命中，加载分片: {shard_name}")
        
        # 获取分片信息
        if shard_name not in self.shard_info:
            raise ValueError(f"未知的分片名称: {shard_name}")
        
        shard_spec = self.shard_info[shard_name]
        size_mb = shard_spec["size_mb"]
        importance = shard_spec["importance"]
        
        # 创建模拟数据（使用分片名称作为种子）
        seed = hash(shard_name) % 10000
        shard_data = self.create_mock_data(size_mb, seed)
        
        # 缓存数据
        model_shard_cache.put(
            shard_name,
            shard_data,
            size_bytes=size_mb * 1024 * 1024,
            importance=importance
        )
        
        # 记录已加载分片
        self.loaded_shards[shard_name] = True
        
        # 确保新加载的分片被验证器检查
        cache_validator.check_consistency(shard_name)
        
        return shard_data
    
    def run_inference(self, text: str) -> str:
        """执行推理（模拟）
        
        Args:
            text: 输入文本
            
        Returns:
            str: 推理结果
        """
        logger.info(f"执行推理: {text[:20]}...")
        
        # 模拟推理过程中的分片访问顺序
        access_sequence = [
            f"{self.model_name}_embedding",
            f"{self.model_name}_attention_1",
            f"{self.model_name}_ffn_1",
            f"{self.model_name}_attention_2",
            f"{self.model_name}_ffn_2",
            f"{self.model_name}_lm_head"
        ]
        
        # 加载并使用各个分片
        for shard_name in access_sequence:
            shard_data = self.load_shard(shard_name)
            # 模拟使用分片数据
            result = np.sum(shard_data[:100])
            logger.debug(f"使用分片 {shard_name}, 结果: {result}")
        
        # 检查内存状态
        sync_with_memory_guard()
        
        # 返回模拟结果
        return f"模型输出: {hash(text) % 1000}"
    
    def simulate_corruption(self, shard_name: str):
        """模拟分片数据损坏
        
        Args:
            shard_name: 要损坏的分片名称
        """
        # 检查分片是否在缓存中
        if not model_shard_cache.contains(shard_name):
            logger.warning(f"分片 {shard_name} 不在缓存中，无法模拟损坏")
            return
        
        # 获取分片信息
        shard_spec = self.shard_info.get(shard_name)
        if not shard_spec:
            logger.warning(f"未知的分片名称: {shard_name}")
            return
        
        # 创建不同的数据
        size_mb = shard_spec["size_mb"]
        importance = shard_spec["importance"]
        
        # 使用不同的种子创建新数据
        new_seed = hash(shard_name + "_corrupted") % 10000
        new_data = self.create_mock_data(size_mb, new_seed)
        
        # 替换缓存中的数据
        logger.warning(f"模拟分片损坏: {shard_name}")
        model_shard_cache.put(
            shard_name,
            new_data,
            size_bytes=size_mb * 1024 * 1024,
            importance=importance
        )


def demonstrate_validation_workflow():
    """演示验证工作流程"""
    logger.info("=== 验证工作流程演示 ===")
    
    # 清空缓存
    model_shard_cache.clear()
    
    # 创建模型管理器
    model = ModelManager("qwen2.5-7b-zh")
    
    # 1. 正常使用过程
    logger.info("\n1. 正常模型使用过程")
    
    # 执行几次推理
    for i in range(3):
        result = model.run_inference(f"这是第{i+1}次测试输入")
        logger.info(f"推理结果: {result}")
    
    # 查看验证统计
    stats = cache_validator.get_stats()
    logger.info(f"正常使用后验证统计:\n{json.dumps(stats, indent=2)}")
    
    # 2. 模拟数据损坏
    logger.info("\n2. 模拟数据损坏情况")
    
    # 选择一个分片进行损坏
    target_shard = f"{model.model_name}_attention_1"
    model.simulate_corruption(target_shard)
    
    # 强制验证
    logger.info("执行强制验证...")
    validation_results = cache_validator.force_validation()
    inconsistent_count = sum(1 for result in validation_results.values() if not result)
    logger.info(f"验证结果: 检测到 {inconsistent_count} 个不一致")
    
    # 3. 验证后恢复
    logger.info("\n3. 验证后恢复")
    
    # 重新执行推理，此时应该会重新加载损坏的分片
    result = model.run_inference("验证后的测试输入")
    logger.info(f"恢复后推理结果: {result}")
    
    # 再次验证，应该已经恢复一致
    validation_results = cache_validator.force_validation()
    inconsistent_count = sum(1 for result in validation_results.values() if not result)
    logger.info(f"恢复后验证结果: 检测到 {inconsistent_count} 个不一致")
    
    # 查看最终统计
    stats = cache_validator.get_stats()
    logger.info(f"最终验证统计:\n{json.dumps(stats, indent=2)}")


def demonstrate_validation_strategies():
    """演示不同的验证策略"""
    logger.info("\n=== 验证策略演示 ===")
    
    # 清空缓存
    model_shard_cache.clear()
    
    # 创建模型管理器
    model = ModelManager("qwen2.5-7b-zh")
    
    # 1. 热点数据验证
    logger.info("\n1. 热点数据验证策略")
    
    # 加载所有分片
    for shard_name in model.shard_info.keys():
        model.load_shard(shard_name)
    
    # 频繁访问某些分片，使其成为热点
    hot_shards = [
        f"{model.model_name}_embedding",
        f"{model.model_name}_lm_head"
    ]
    
    logger.info(f"创建热点分片: {hot_shards}")
    for _ in range(15):  # 超过热点阈值
        for shard_name in hot_shards:
            data = model_shard_cache.get(shard_name)
    
    # 查看热点数据
    if hasattr(cache_janitor, 'hot_keys'):
        logger.info(f"当前热点数据: {cache_janitor.hot_keys}")
    
    # 演示验证任务的差异
    logger.info("执行验证任务...")
    cache_validator.validation_task()
    
    # 查看验证统计
    stats = cache_validator.get_stats()
    logger.info(f"验证统计:\n{json.dumps(stats, indent=2)}")
    
    # 2. 仅验证热点数据
    logger.info("\n2. 仅验证热点数据")
    
    # 强制只验证热点数据
    validation_results = cache_validator.force_validation(include_hot_only=True)
    logger.info(f"热点验证结果: 验证了 {len(validation_results)} 个分片")
    
    # 3. 自定义验证频率
    logger.info("\n3. 自定义验证频率")
    
    # 临时调整验证频率
    original_hot_interval = cache_validator.hot_check_interval
    original_cold_interval = cache_validator.cold_check_interval
    
    cache_validator.hot_check_interval = 1800  # 30分钟
    cache_validator.cold_check_interval = 43200  # 12小时
    
    logger.info(f"调整验证频率: 热点={cache_validator.hot_check_interval}秒, "
               f"冷点={cache_validator.cold_check_interval}秒")
    
    # 恢复原始频率
    cache_validator.hot_check_interval = original_hot_interval
    cache_validator.cold_check_interval = original_cold_interval
    
    logger.info(f"恢复验证频率: 热点={cache_validator.hot_check_interval}秒, "
               f"冷点={cache_validator.cold_check_interval}秒")


def demonstrate_validation_integration():
    """演示与其他缓存组件的集成"""
    logger.info("\n=== 验证集成演示 ===")
    
    # 清空缓存
    model_shard_cache.clear()
    
    # 创建模型管理器
    model = ModelManager("qwen2.5-7b-zh")
    
    # 1. 与内存监控的集成
    logger.info("\n1. 与内存监控的集成")
    
    # 加载所有分片
    for shard_name in model.shard_info.keys():
        model.load_shard(shard_name)
        # 每次加载后检查内存状态
        sync_with_memory_guard()
    
    # 模拟数据损坏
    target_shard = f"{model.model_name}_ffn_1"
    model.simulate_corruption(target_shard)
    
    # 强制验证
    validation_results = cache_validator.force_validation()
    
    # 同步内存监控
    sync_with_memory_guard()
    
    # 2. 与缓存清理的集成
    logger.info("\n2. 与缓存清理的集成")
    
    # 触发缓存清理
    if hasattr(cache_janitor, 'clean_expired'):
        cleaned = cache_janitor.clean_expired()
        logger.info(f"清理过期项: {cleaned}")
    
    # 验证清理后的缓存
    validation_results = cache_validator.force_validation()
    logger.info(f"清理后验证: {len(validation_results)} 个分片")
    
    # 计算所有哈希值
    cache_validator.calculate_all_hashes()
    
    # 3. 在生产环境中的使用建议
    logger.info("\n3. 生产环境使用建议")
    logger.info("- 对热点数据设置较短的验证间隔（如1小时）")
    logger.info("- 对冷数据设置较长的验证间隔（如1天）")
    logger.info("- 定期计算所有哈希值（如每天一次）")
    logger.info("- 处理验证失败时优先保证服务可用性")
    logger.info("- 结合内存监控，在低内存情况下降低验证频率")


def main():
    """主函数"""
    logger.info("开始缓存验证器使用示例")
    
    # 演示验证工作流程
    demonstrate_validation_workflow()
    
    # 演示验证策略
    demonstrate_validation_strategies()
    
    # 演示验证集成
    demonstrate_validation_integration()
    
    # 清理缓存
    model_shard_cache.clear()
    
    logger.info("缓存验证器使用示例完成")


if __name__ == "__main__":
    main() 