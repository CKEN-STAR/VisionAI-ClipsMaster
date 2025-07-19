#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""缓存命中率优化使用示例

此脚本展示了如何在实际应用中使用缓存命中率优化器，包括：
1. 基于实际使用模式的缓存大小自适应调整
2. 针对不同模型分片的差异化优化策略
3. 如何监控和分析缓存命中率
4. 如何手动调整优化器参数
"""

import os
import sys
import time
import numpy as np
import matplotlib.pyplot as plt
from threading import Thread
from loguru import logger

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.cache import (
    model_shard_cache,
    hit_rate_optimizer,
    cache_janitor
)
from src.utils.file_utils import ensure_directory


class ModelLoader:
    """模型加载器
    
    模拟模型分片加载过程，用于演示缓存命中率优化
    """
    
    def __init__(self, model_name="qwen2.5-7b-zh", cache=model_shard_cache):
        """初始化模型加载器
        
        Args:
            model_name: 模型名称
            cache: 缓存对象
        """
        self.model_name = model_name
        self.cache = cache
        self.shard_count = 12 if "qwen" in model_name else 8
        self.shard_size_mb = 100  # 每个分片约100MB
        
        # 记录最近访问的分片
        self.recent_shards = []
        self.max_recent = 5
        
        # 统计分片访问次数
        self.shard_access_count = {}
        
        # 确保输出目录存在
        ensure_directory("output")
    
    def simulate_load_shard(self, shard_id):
        """模拟加载分片
        
        Args:
            shard_id: 分片ID
            
        Returns:
            分片数据
        """
        cache_key = f"{self.model_name}_shard_{shard_id}"
        
        # 更新访问计数
        if shard_id not in self.shard_access_count:
            self.shard_access_count[shard_id] = 0
        self.shard_access_count[shard_id] += 1
        
        # 尝试从缓存获取
        shard_data = self.cache.get(cache_key)
        
        if shard_data is None:
            # 缓存未命中，模拟从磁盘加载
            logger.info(f"缓存未命中: {cache_key}, 模拟加载分片...")
            time.sleep(0.5)  # 模拟加载延迟
            
            # 创建模拟分片数据 (假设每个分片有不同的数据)
            shard_size_bytes = self.shard_size_mb * 1024 * 1024
            shard_data = np.random.rand(int(shard_size_bytes / 8))
            
            # 缓存分片数据，设置大小和重要性
            # 根据分片ID设置不同的重要性（前几个分片通常更重要）
            importance = 1.5 if shard_id < 3 else 1.0
            self.cache.put(cache_key, shard_data, shard_size_bytes, importance)
            
            logger.info(f"分片 {shard_id} 已加载并缓存，重要性: {importance}")
        else:
            logger.info(f"缓存命中: {cache_key}")
        
        # 更新最近访问的分片
        if shard_id in self.recent_shards:
            self.recent_shards.remove(shard_id)
        self.recent_shards.insert(0, shard_id)
        
        # 保持最近访问列表的长度限制
        if len(self.recent_shards) > self.max_recent:
            self.recent_shards = self.recent_shards[:self.max_recent]
        
        return shard_data
    
    def simulate_inference(self, num_steps=500, locality_pattern="zipf"):
        """模拟推理过程
        
        生成一系列分片访问请求，模拟真实推理过程中的访问模式
        
        Args:
            num_steps: 模拟步数
            locality_pattern: 访问模式 ("random", "local", "zipf")
            
        Returns:
            命中率历史
        """
        hit_rates = []
        cache_sizes = []
        
        logger.info(f"开始模拟 {num_steps} 步推理过程，访问模式: {locality_pattern}")
        
        for step in range(num_steps):
            # 根据不同模式生成分片访问序列
            if locality_pattern == "random":
                # 完全随机访问
                shard_id = np.random.randint(0, self.shard_count)
            
            elif locality_pattern == "local":
                # 局部性访问：80%的时间访问最近使用的分片，20%随机访问
                if self.recent_shards and np.random.random() < 0.8:
                    shard_id = np.random.choice(self.recent_shards)
                else:
                    shard_id = np.random.randint(0, self.shard_count)
            
            elif locality_pattern == "zipf":
                # Zipf分布：模拟真实访问中的幂律分布（少数分片被频繁访问）
                if step < 50:
                    # 前50步随机访问，建立初始访问频率
                    shard_id = np.random.randint(0, self.shard_count)
                else:
                    # 基于已有访问频率生成Zipf分布
                    probs = []
                    for i in range(self.shard_count):
                        count = self.shard_access_count.get(i, 0) + 1
                        probs.append(count)
                    
                    # 归一化概率
                    probs = np.array(probs) / sum(probs)
                    shard_id = np.random.choice(range(self.shard_count), p=probs)
            
            else:
                shard_id = np.random.randint(0, self.shard_count)
            
            # 加载选定的分片
            self.simulate_load_shard(shard_id)
            
            # 每10步记录一次命中率
            if step % 10 == 0:
                # 获取当前命中率和缓存大小
                stats = hit_rate_optimizer.get_stats()
                hit_rate = stats["current_hit_rate"]
                cache_size_mb = stats["cache_size"]["current"] / (1024 * 1024)
                
                hit_rates.append(hit_rate)
                cache_sizes.append(cache_size_mb)
                
                if step % 50 == 0:
                    logger.info(f"步骤 {step}, 命中率: {hit_rate:.2f}, 缓存大小: {cache_size_mb:.1f}MB")
        
        logger.info(f"模拟完成，最终命中率: {hit_rates[-1]:.2f}")
        return hit_rates, cache_sizes
    
    def plot_results(self, hit_rates, cache_sizes, pattern_name):
        """绘制结果图表
        
        Args:
            hit_rates: 命中率历史
            cache_sizes: 缓存大小历史
            pattern_name: 访问模式名称
        """
        plt.figure(figsize=(12, 8))
        
        # 绘制命中率
        plt.subplot(2, 1, 1)
        x = range(len(hit_rates))
        plt.plot(x, hit_rates, 'b-', linewidth=2)
        plt.title(f"缓存命中率变化 - {pattern_name}访问模式")
        plt.xlabel("时间步（每10步记录一次）")
        plt.ylabel("命中率")
        plt.grid(True)
        
        # 绘制缓存大小
        plt.subplot(2, 1, 2)
        plt.plot(x, cache_sizes, 'r-', linewidth=2)
        plt.title(f"缓存大小变化 - {pattern_name}访问模式")
        plt.xlabel("时间步（每10步记录一次）")
        plt.ylabel("缓存大小(MB)")
        plt.grid(True)
        
        plt.tight_layout()
        
        # 保存图表
        output_path = f"output/cache_optimization_{pattern_name}.png"
        plt.savefig(output_path)
        logger.info(f"图表已保存到: {output_path}")
        
        # 关闭图形
        plt.close()


def run_optimization_example():
    """运行优化示例"""
    logger.info("===== 缓存命中率优化示例 =====")
    
    # 清理缓存，确保干净的实验环境
    model_shard_cache.clear()
    
    # 可以手动调整优化器参数
    hit_rate_optimizer.adjust_thresholds(low_threshold=0.5, high_threshold=0.85)
    hit_rate_optimizer.adjust_ratios(increase_ratio=0.3, decrease_ratio=0.15)
    
    logger.info("已调整优化器参数:")
    logger.info(f"  - 低命中率阈值: {hit_rate_optimizer.low_threshold}")
    logger.info(f"  - 高命中率阈值: {hit_rate_optimizer.high_threshold}")
    logger.info(f"  - 增加比例: {hit_rate_optimizer.increase_ratio}")
    logger.info(f"  - 减少比例: {hit_rate_optimizer.decrease_ratio}")
    
    # 创建模型加载器
    qwen_loader = ModelLoader(model_name="qwen2.5-7b-zh")
    
    # 定义要测试的访问模式
    patterns = {
        "random": "随机",
        "local": "局部性", 
        "zipf": "幂律"
    }
    
    # 对每种访问模式运行模拟
    for pattern, name in patterns.items():
        logger.info(f"\n测试 {name} 访问模式...")
        
        # 清空命中窗口和缓存
        hit_rate_optimizer.reset_hit_window()
        model_shard_cache.clear()
        
        # 运行模拟
        hit_rates, cache_sizes = qwen_loader.simulate_inference(
            num_steps=500, 
            locality_pattern=pattern
        )
        
        # 输出优化器统计信息
        stats = hit_rate_optimizer.get_stats()
        logger.info("\n优化器统计信息:")
        logger.info(f"  - 总调整次数: {stats['total_adjustments']}")
        logger.info(f"  - 增加次数: {stats['increases']}")
        logger.info(f"  - 减少次数: {stats['decreases']}")
        logger.info(f"  - 最终命中率: {stats['current_hit_rate']:.4f}")
        logger.info(f"  - 最终缓存大小: {stats['cache_size']['current'] / (1024*1024):.1f} MB")
        logger.info(f"  - 缓存大小比例: {stats['cache_size']['current_ratio']:.2f}x")
        
        # 分析不同分片的访问情况
        model_stats = stats.get("model_stats", {})
        if "qwen2.5-7b-zh" in model_stats:
            logger.info(f"  - 模型命中率: {model_stats['qwen2.5-7b-zh']['hit_rate']:.4f}")
        
        # 绘制结果
        qwen_loader.plot_results(hit_rates, cache_sizes, name)
        
        # 获取推荐的分片重要性
        recommendations = hit_rate_optimizer.recommend_shard_importance()
        logger.info("\n分片重要性推荐:")
        for model, importance in recommendations.items():
            logger.info(f"  - {model}: {importance:.2f}")
        
        # 短暂暂停，让系统恢复
        time.sleep(2)
    
    logger.info("\n示例运行完成，查看output目录下的图表了解优化效果")


def dual_model_example():
    """双模型使用示例
    
    展示在中英文双模型环境下的缓存优化
    """
    logger.info("===== 双模型缓存优化示例 =====")
    
    # 清理缓存
    model_shard_cache.clear()
    hit_rate_optimizer.reset_hit_window()
    
    # 创建两个加载器
    qwen_loader = ModelLoader(model_name="qwen2.5-7b-zh")
    mistral_loader = ModelLoader(model_name="mistral-7b-en")
    
    logger.info("开始双模型交替访问模拟...")
    
    # 模拟双模型交替使用 (70% 中文/30% 英文)
    # 这种比例更符合以中文为主的应用场景
    for step in range(1000):
        # 随机选择使用哪个模型
        if np.random.random() < 0.7:
            # 使用中文模型
            shard_id = np.random.randint(0, qwen_loader.shard_count)
            qwen_loader.simulate_load_shard(shard_id)
        else:
            # 使用英文模型
            shard_id = np.random.randint(0, mistral_loader.shard_count)
            mistral_loader.simulate_load_shard(shard_id)
        
        # 每50步输出一次状态
        if step % 50 == 0:
            stats = hit_rate_optimizer.get_stats()
            model_stats = stats.get("model_stats", {})
            
            logger.info(f"\n步骤 {step}:")
            logger.info(f"  - 总命中率: {stats['current_hit_rate']:.4f}")
            logger.info(f"  - 缓存大小: {stats['cache_size']['current'] / (1024*1024):.1f} MB")
            
            # 如果有模型统计，打印各个模型的命中率
            if model_stats:
                if "qwen2.5-7b-zh" in model_stats:
                    logger.info(f"  - 中文模型命中率: {model_stats['qwen2.5-7b-zh']['hit_rate']:.4f}")
                if "mistral-7b-en" in model_stats:
                    logger.info(f"  - 英文模型命中率: {model_stats['mistral-7b-en']['hit_rate']:.4f}")
    
    # 输出最终结果
    logger.info("\n双模型模拟完成，最终状态:")
    stats = hit_rate_optimizer.get_stats()
    model_stats = stats.get("model_stats", {})
    
    # 分片重要性推荐
    recommendations = hit_rate_optimizer.recommend_shard_importance()
    
    logger.info(f"最终缓存大小: {stats['cache_size']['current'] / (1024*1024):.1f} MB")
    logger.info(f"调整次数: 增加 {stats['increases']}次, 减少 {stats['decreases']}次")
    
    logger.info("\n模型命中率比较:")
    qwen_rate = model_stats.get("qwen2.5-7b-zh", {}).get("hit_rate", 0)
    mistral_rate = model_stats.get("mistral-7b-en", {}).get("hit_rate", 0)
    
    logger.info(f"  - 中文模型: {qwen_rate:.4f} (推荐重要性: {recommendations.get('qwen2.5-7b-zh', 0):.2f})")
    logger.info(f"  - 英文模型: {mistral_rate:.4f} (推荐重要性: {recommendations.get('mistral-7b-en', 0):.2f})")
    
    # 根据命中率，提供策略建议
    logger.info("\n基于命中率的策略建议:")
    if qwen_rate > mistral_rate + 0.1:
        logger.info("  - 中文模型命中率明显高于英文模型，建议增加中文模型分片重要性")
    elif mistral_rate > qwen_rate + 0.1:
        logger.info("  - 英文模型命中率明显高于中文模型，建议增加英文模型分片重要性")
    else:
        logger.info("  - 两个模型命中率相近，建议保持当前重要性配置")


def manual_optimization_example():
    """手动优化示例
    
    展示如何手动控制和调整缓存优化器
    """
    logger.info("===== 手动缓存优化示例 =====")
    
    # 关闭自动优化
    hit_rate_optimizer.stop_auto_optimize()
    
    # 清理缓存和统计
    model_shard_cache.clear()
    hit_rate_optimizer.reset_hit_window()
    
    # 创建模型加载器
    loader = ModelLoader(model_name="qwen2.5-7b-zh")
    
    logger.info("开始手动优化示例...")
    
    # 首先，模拟一些访问建立基准命中率
    for step in range(200):
        shard_id = np.random.randint(0, loader.shard_count)
        loader.simulate_load_shard(shard_id)
    
    # 获取基准命中率
    base_hit_rate = hit_rate_optimizer.get_current_hit_rate()
    base_cache_size = model_shard_cache.max_size_bytes
    
    logger.info(f"\n基准状态:")
    logger.info(f"  - 命中率: {base_hit_rate:.4f}")
    logger.info(f"  - 缓存大小: {base_cache_size / (1024*1024):.1f} MB")
    
    # 手动增加缓存大小
    target_size = int(base_cache_size * 1.5)  # 增加50%
    logger.info(f"\n手动调整缓存大小至 {target_size / (1024*1024):.1f} MB...")
    
    hit_rate_optimizer.force_resize(target_size)
    
    # 再次运行一段时间看看效果
    logger.info("\n运行更多访问以观察效果...")
    for step in range(300):
        shard_id = np.random.randint(0, loader.shard_count)
        loader.simulate_load_shard(shard_id)
        
        if step % 100 == 0 and step > 0:
            current_hit_rate = hit_rate_optimizer.get_current_hit_rate()
            logger.info(f"  步骤 {step}: 命中率 {current_hit_rate:.4f}")
    
    # 获取调整后的命中率
    adjusted_hit_rate = hit_rate_optimizer.get_current_hit_rate()
    
    logger.info(f"\n调整后状态:")
    logger.info(f"  - 命中率: {adjusted_hit_rate:.4f} (变化: {adjusted_hit_rate - base_hit_rate:.4f})")
    logger.info(f"  - 缓存大小: {target_size / (1024*1024):.1f} MB")
    
    # 根据效果提供建议
    improvement = adjusted_hit_rate - base_hit_rate
    
    if improvement > 0.1:
        logger.info("\n手动调整效果显著，建议维持较大的缓存大小")
    elif improvement > 0:
        logger.info("\n手动调整有轻微效果，建议根据实际资源情况决定是否维持")
    else:
        logger.info("\n手动调整未带来明显改善，建议恢复原始缓存大小以节省内存")
    
    # 恢复自动优化
    logger.info("\n重新启用自动优化...")
    hit_rate_optimizer.start_auto_optimize()


if __name__ == "__main__":
    # 设置日志级别
    logger.remove()
    logger.add(sys.stdout, level="INFO")
    
    # 运行示例
    run_optimization_example()
    
    # 双模型示例 (可选)
    # dual_model_example()
    
    # 手动优化示例 (可选)
    # manual_optimization_example() 