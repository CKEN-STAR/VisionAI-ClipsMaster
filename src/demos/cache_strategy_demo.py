#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""缓存策略演示脚本

此脚本演示如何使用不同的缓存策略，并比较它们的性能表现。
支持以下功能：
1. 加载不同的缓存策略
2. 模拟不同的访问模式
3. 比较不同策略的命中率和性能
4. 自动选择最佳策略
"""

import os
import sys
import time
import random
import argparse
import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, List, Optional, Tuple, Union
from pathlib import Path

# 添加项目根目录到系统路径
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, root_dir)

from src.sharding.strategy_manager import StrategyManager
from src.sharding.cache_manager import ShardManager
from src.sharding.cache_policy import (
    LRUPolicy, 
    LFUPolicy, 
    FIFOPolicy, 
    WeightAwarePolicy, 
    FreqAwarePolicy
)
from loguru import logger


class CacheStrategyBenchmark:
    """缓存策略基准测试
    
    比较不同缓存策略在不同访问模式下的性能表现。
    """
    
    def __init__(
        self, 
        model_name: str,
        cache_size: int = 5,
        output_dir: Optional[str] = None
    ):
        """初始化基准测试
        
        Args:
            model_name: 测试使用的模型名称
            cache_size: 缓存大小
            output_dir: 输出目录，用于保存结果图表
        """
        self.model_name = model_name
        self.cache_size = cache_size
        self.output_dir = output_dir or os.path.join(root_dir, "benchmark_results", "cache_strategy")
        
        # 确保输出目录存在
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 策略管理器
        self.strategy_manager = StrategyManager(model_name=model_name)
        
        # 获取所有可用的策略
        self.available_strategies = list(self.strategy_manager.get_all_strategies().keys())
        logger.info(f"可用策略: {self.available_strategies}")
        
        # 测试结果
        self.results = {}
    
    def test_strategy(
        self, 
        strategy_name: str, 
        access_pattern: List[str], 
        access_repeats: int = 1
    ) -> Dict[str, Union[float, int, List]]:
        """测试单个策略的性能
        
        使用指定的访问模式测试特定缓存策略的性能。
        
        Args:
            strategy_name: 策略名称
            access_pattern: 访问模式（分片ID序列）
            access_repeats: 重复次数
            
        Returns:
            Dict: 性能指标
        """
        # 创建分片管理器并设置策略
        shard_manager = ShardManager(
            model_name=self.model_name,
            max_shards_in_memory=self.cache_size,
            strategy_name=strategy_name,
            auto_adjust_strategy=False
        )
        
        hits = 0
        misses = 0
        total_time = 0.0
        access_times = []
        
        # 记录初始缓存状态
        initial_stats = shard_manager.get_cache_stats()
        
        # 执行访问模式
        for _ in range(access_repeats):
            for shard_id in access_pattern:
                start_time = time.time()
                # 模拟加载分片
                # 注意：这里没有实际加载分片，只测试缓存逻辑
                cache_policy = shard_manager.cache_policy
                if cache_policy.contains(shard_id):
                    # 缓存命中
                    hits += 1
                    _ = cache_policy.get(shard_id)
                else:
                    # 缓存未命中
                    misses += 1
                    # 模拟分片加载过程
                    time.sleep(0.01)  # 假设加载需要10ms
                    # 向缓存添加模拟数据
                    cache_policy.add(shard_id, {"id": shard_id, "data": f"模拟分片数据 {shard_id}"})
                
                access_time = time.time() - start_time
                total_time += access_time
                access_times.append(access_time)
        
        # 记录最终缓存状态
        final_stats = shard_manager.get_cache_stats()
        
        # 计算性能指标
        total_accesses = hits + misses
        hit_rate = hits / total_accesses if total_accesses > 0 else 0
        average_access_time = total_time / total_accesses if total_accesses > 0 else 0
        
        # 清理资源
        shard_manager.clear_cache()
        
        return {
            "strategy": strategy_name,
            "hits": hits,
            "misses": misses,
            "hit_rate": hit_rate,
            "total_time": total_time,
            "average_access_time": average_access_time,
            "access_times": access_times,
            "initial_stats": initial_stats,
            "final_stats": final_stats
        }
    
    def generate_random_access_pattern(
        self, 
        num_shards: int = 20, 
        pattern_length: int = 100,
        pattern_type: str = "random"
    ) -> List[str]:
        """生成随机访问模式
        
        Args:
            num_shards: 分片总数
            pattern_length: 访问模式长度
            pattern_type: 访问模式类型，支持random、zipf、sequential、repeated
            
        Returns:
            List[str]: 分片ID序列
        """
        # 创建分片ID列表
        shard_ids = [f"shard_{i}" for i in range(num_shards)]
        
        if pattern_type == "random":
            # 完全随机访问
            return random.choices(shard_ids, k=pattern_length)
            
        elif pattern_type == "zipf":
            # Zipf分布 (长尾分布，少数分片被频繁访问)
            weights = [1.0/(i+1) for i in range(num_shards)]
            return random.choices(shard_ids, weights=weights, k=pattern_length)
            
        elif pattern_type == "sequential":
            # 顺序访问
            repeats = pattern_length // num_shards + 1
            return (shard_ids * repeats)[:pattern_length]
            
        elif pattern_type == "repeated":
            # 重复访问固定集合
            hot_shards = shard_ids[:self.cache_size + 2]  # 稍多于缓存大小的热点分片
            return random.choices(hot_shards, k=pattern_length)
            
        elif pattern_type == "mixed":
            # 混合模式: 80%的访问集中在20%的分片上
            hot_shard_count = max(1, num_shards // 5)
            hot_shards = shard_ids[:hot_shard_count]
            cold_shards = shard_ids[hot_shard_count:]
            
            pattern = []
            for _ in range(pattern_length):
                if random.random() < 0.8:
                    # 80%的概率访问热点分片
                    pattern.append(random.choice(hot_shards))
                else:
                    # 20%的概率访问冷分片
                    pattern.append(random.choice(cold_shards))
            
            return pattern
        
        else:
            logger.warning(f"未知的访问模式类型: {pattern_type}，使用随机模式")
            return random.choices(shard_ids, k=pattern_length)
    
    def benchmark_all_strategies(
        self,
        pattern_types: List[str] = ["random", "zipf", "sequential", "repeated", "mixed"],
        pattern_length: int = 200,
        num_shards: int = 30
    ) -> Dict[str, Dict[str, Dict]]:
        """对所有策略进行基准测试
        
        Args:
            pattern_types: 要测试的访问模式类型列表
            pattern_length: 访问模式长度
            num_shards: 分片总数
            
        Returns:
            Dict: 测试结果
        """
        results = {}
        
        for pattern_type in pattern_types:
            logger.info(f"测试访问模式: {pattern_type}")
            
            # 为每种模式生成访问序列
            access_pattern = self.generate_random_access_pattern(
                num_shards=num_shards,
                pattern_length=pattern_length,
                pattern_type=pattern_type
            )
            
            pattern_results = {}
            
            # 测试每种策略
            for strategy in self.available_strategies:
                logger.info(f"  测试策略: {strategy}")
                
                # 运行测试
                result = self.test_strategy(
                    strategy_name=strategy,
                    access_pattern=access_pattern
                )
                
                pattern_results[strategy] = result
                logger.info(f"    命中率: {result['hit_rate']:.2f}, "
                           f"平均访问时间: {result['average_access_time']*1000:.2f}ms")
            
            results[pattern_type] = pattern_results
        
        self.results = results
        return results
    
    def plot_hit_rates(self, save_path: Optional[str] = None) -> None:
        """绘制命中率对比图
        
        Args:
            save_path: 保存路径，如果为None则显示图表
        """
        if not self.results:
            logger.warning("没有可用的测试结果")
            return
        
        # 准备数据
        pattern_types = list(self.results.keys())
        strategies = list(self.available_strategies)
        
        # 创建柱状图
        fig, ax = plt.subplots(figsize=(12, 7))
        
        x = np.arange(len(pattern_types))
        width = 0.15
        multiplier = 0
        
        for strategy in strategies:
            hit_rates = [self.results[pattern][strategy]['hit_rate'] for pattern in pattern_types]
            offset = width * multiplier
            rects = ax.bar(x + offset, hit_rates, width, label=strategy)
            ax.bar_label(rects, fmt='{:.2f}', padding=3, rotation=90, fontsize=8)
            multiplier += 1
        
        # 添加标签和图例
        ax.set_ylabel('命中率')
        ax.set_title('不同访问模式下各缓存策略的命中率')
        ax.set_xticks(x + width * (len(strategies) - 1) / 2)
        ax.set_xticklabels(pattern_types)
        ax.legend(loc='upper left', bbox_to_anchor=(1, 1))
        ax.set_ylim(0, 1)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path)
            logger.info(f"命中率对比图已保存至: {save_path}")
        else:
            plt.show()
    
    def plot_access_times(self, save_path: Optional[str] = None) -> None:
        """绘制平均访问时间对比图
        
        Args:
            save_path: 保存路径，如果为None则显示图表
        """
        if not self.results:
            logger.warning("没有可用的测试结果")
            return
        
        # 准备数据
        pattern_types = list(self.results.keys())
        strategies = list(self.available_strategies)
        
        # 创建柱状图
        fig, ax = plt.subplots(figsize=(12, 7))
        
        x = np.arange(len(pattern_types))
        width = 0.15
        multiplier = 0
        
        for strategy in strategies:
            access_times = [self.results[pattern][strategy]['average_access_time'] * 1000 
                          for pattern in pattern_types]  # 转换为毫秒
            offset = width * multiplier
            rects = ax.bar(x + offset, access_times, width, label=strategy)
            ax.bar_label(rects, fmt='{:.1f}', padding=3, rotation=90, fontsize=8)
            multiplier += 1
        
        # 添加标签和图例
        ax.set_ylabel('平均访问时间 (毫秒)')
        ax.set_title('不同访问模式下各缓存策略的平均访问时间')
        ax.set_xticks(x + width * (len(strategies) - 1) / 2)
        ax.set_xticklabels(pattern_types)
        ax.legend(loc='upper left', bbox_to_anchor=(1, 1))
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path)
            logger.info(f"访问时间对比图已保存至: {save_path}")
        else:
            plt.show()
    
    def run_full_benchmark(self) -> None:
        """运行完整的基准测试并生成报告"""
        # 运行所有策略的基准测试
        self.benchmark_all_strategies()
        
        # 绘制结果图表
        self.plot_hit_rates(os.path.join(self.output_dir, "hit_rates.png"))
        self.plot_access_times(os.path.join(self.output_dir, "access_times.png"))
        
        # 输出推荐策略
        self._print_recommendations()
    
    def _print_recommendations(self) -> None:
        """根据测试结果输出策略推荐"""
        if not self.results:
            return
            
        logger.info("===== 策略推荐 =====")
        
        for pattern_type, pattern_results in self.results.items():
            # 按命中率排序
            strategies_by_hit_rate = sorted(
                pattern_results.items(),
                key=lambda x: x[1]['hit_rate'],
                reverse=True
            )
            
            # 按访问时间排序
            strategies_by_time = sorted(
                pattern_results.items(),
                key=lambda x: x[1]['average_access_time']
            )
            
            logger.info(f"访问模式: {pattern_type}")
            logger.info(f"  命中率最高的策略: {strategies_by_hit_rate[0][0]} "
                       f"({strategies_by_hit_rate[0][1]['hit_rate']:.2f})")
            logger.info(f"  访问时间最短的策略: {strategies_by_time[0][0]} "
                       f"({strategies_by_time[0][1]['average_access_time']*1000:.2f}ms)")


def demonstrate_policy_switching():
    """演示动态切换缓存策略"""
    logger.info("===== 策略切换演示 =====")
    
    # 创建分片管理器，使用默认策略
    shard_manager = ShardManager(
        model_name="qwen2.5-7b-zh",
        max_shards_in_memory=5
    )
    
    # 获取当前策略
    initial_strategy = shard_manager.strategy_manager.get_current_strategy_name()
    logger.info(f"初始策略: {initial_strategy}")
    
    # 获取可用策略列表
    available_strategies = shard_manager.get_available_strategies()
    logger.info(f"可用策略: {available_strategies}")
    
    # 模拟加载一些分片
    test_shards = [f"shard_{i}" for i in range(10)]
    for shard_id in test_shards[:5]:
        # 添加到缓存
        shard_manager.cache_policy.add(shard_id, {"id": shard_id, "data": f"测试数据 {shard_id}"})
    
    # 获取初始缓存状态
    initial_stats = shard_manager.get_cache_stats()
    logger.info(f"初始缓存状态: {initial_stats}")
    
    # 切换到另一个策略
    new_strategy = "freq_aware" if initial_strategy != "freq_aware" else "lfu"
    success = shard_manager.switch_cache_strategy(new_strategy)
    
    if success:
        logger.info(f"已切换到策略: {new_strategy}")
        
        # 获取切换后的缓存状态
        new_stats = shard_manager.get_cache_stats()
        logger.info(f"切换后缓存状态: {new_stats}")
        
        # 验证缓存内容是否保持一致
        cached_items = shard_manager.cache_policy.get_keys()
        logger.info(f"缓存中的项目: {cached_items}")
        
        # 测试新策略的一些操作
        for shard_id in test_shards[5:8]:
            shard_manager.cache_policy.add(shard_id, {"id": shard_id, "data": f"新数据 {shard_id}"})
        
        # 访问一些项目以测试新策略
        for shard_id in test_shards[:8]:
            item = shard_manager.cache_policy.get(shard_id)
            logger.debug(f"访问 {shard_id}: {'命中' if item else '未命中'}")
        
        # 获取最终状态
        final_stats = shard_manager.get_cache_stats()
        logger.info(f"最终缓存状态: {final_stats}")
    else:
        logger.error(f"切换到策略 {new_strategy} 失败")
    
    # 清理资源
    shard_manager.clear_cache()


def demonstrate_auto_adjustment():
    """演示自动调整策略"""
    logger.info("===== 自动策略调整演示 =====")
    
    # 创建分片管理器，启用自动调整
    shard_manager = ShardManager(
        model_name="qwen2.5-7b-zh",
        max_shards_in_memory=5,
        auto_adjust_strategy=True
    )
    
    # 获取初始内存级别和策略
    initial_level = shard_manager.strategy_manager.memory_level
    initial_strategy = shard_manager.strategy_manager.get_current_strategy_name()
    logger.info(f"初始内存级别: {initial_level.name}, 策略: {initial_strategy}")
    
    # 模拟内存压力变化 (通过直接修改内存级别来模拟)
    logger.info("模拟内存压力增加...")
    shard_manager.strategy_manager.memory_level = shard_manager.strategy_manager.memory_level.__class__.CRITICAL
    
    # 触发策略调整
    adjusted = shard_manager.strategy_manager.adjust_strategy_if_needed()
    
    if adjusted:
        new_strategy = shard_manager.strategy_manager.get_current_strategy_name()
        logger.info(f"策略已自动调整为: {new_strategy}")
    else:
        logger.info("策略未发生变化")
    
    # 清理资源
    shard_manager.clear_cache()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="缓存策略演示和基准测试")
    parser.add_argument('--benchmark', action='store_true', help="运行基准测试")
    parser.add_argument('--model', default="qwen2.5-7b-zh", help="模型名称")
    parser.add_argument('--cache-size', type=int, default=5, help="缓存大小")
    parser.add_argument('--demo-switch', action='store_true', help="演示策略切换")
    parser.add_argument('--demo-auto', action='store_true', help="演示自动调整")
    args = parser.parse_args()
    
    # 设置日志级别
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    
    # 运行基准测试
    if args.benchmark:
        benchmark = CacheStrategyBenchmark(
            model_name=args.model,
            cache_size=args.cache_size
        )
        benchmark.run_full_benchmark()
    
    # 演示策略切换
    if args.demo_switch:
        demonstrate_policy_switching()
    
    # 演示自动调整
    if args.demo_auto:
        demonstrate_auto_adjustment()
    
    # 如果没有指定任何操作，默认运行所有演示
    if not (args.benchmark or args.demo_switch or args.demo_auto):
        demonstrate_policy_switching()
        print("\n")
        demonstrate_auto_adjustment()


if __name__ == "__main__":
    main() 