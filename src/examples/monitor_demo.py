#!/usr/bin/env python
"""分片加载监控演示

此脚本演示如何使用分片监控系统跟踪和分析分片加载模式，
识别热点分片，提供优化建议。
"""

import os
import time
import random
import argparse
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
from loguru import logger

from src.sharding.metadata_manager import MetadataManager
from src.sharding.cache_manager import ShardManager
from src.sharding.monitor import ShardMonitor, create_shard_monitor


def create_test_metadata(model_name="test_model", shard_count=10, model_size_mb=500):
    """创建测试用的模型元数据
    
    Args:
        model_name: 模型名称
        shard_count: 分片数量
        model_size_mb: 模型总大小（MB）
        
    Returns:
        MetadataManager: 元数据管理器
    """
    metadata_manager = MetadataManager()
    
    # 创建分片元数据
    shards = {}
    
    # 计算每个分片的基础大小
    base_size_mb = model_size_mb / shard_count
    
    for i in range(shard_count):
        shard_id = f"shard_{i}"
        
        # 随机生成依赖关系（保证没有循环依赖）
        dependencies = [f"shard_{j}" for j in range(i) if random.random() < 0.3]
        
        # 随机分配层
        layers = [f"layer_{i}_{j}" for j in range(random.randint(1, 3))]
        
        # 分片大小（随机变化，但总体接近预设大小）
        size_mb = base_size_mb * (0.8 + 0.4 * random.random())
        
        shards[shard_id] = {
            "id": shard_id,
            "path": f"models/{model_name}/shards/{shard_id}.bin",
            "size_bytes": int(size_mb * 1024 * 1024),  # 转为字节
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


def simulate_load_patterns(shard_manager, monitor, pattern_type="random", iterations=50):
    """模拟不同的加载模式
    
    Args:
        shard_manager: 分片管理器
        monitor: 分片监控器
        pattern_type: 加载模式类型
        iterations: 模拟迭代次数
    """
    metadata = shard_manager.metadata
    all_shards = list(metadata.get_shards().keys())
    
    logger.info(f"开始模拟 {pattern_type} 加载模式，{iterations} 次迭代")
    
    # 确保目录存在
    os.makedirs("reports", exist_ok=True)
    
    if pattern_type == "random":
        # 随机加载模式
        for i in range(iterations):
            shard_id = random.choice(all_shards)
            logger.info(f"[{i+1}/{iterations}] 随机加载分片: {shard_id}")
            shard_manager.load_shard(shard_id, recursive=True)
            time.sleep(0.1)  # 短暂暂停
    
    elif pattern_type == "sequential":
        # 顺序加载模式
        for i in range(iterations):
            idx = i % len(all_shards)
            shard_id = all_shards[idx]
            logger.info(f"[{i+1}/{iterations}] 顺序加载分片: {shard_id}")
            shard_manager.load_shard(shard_id, recursive=True)
            time.sleep(0.1)
    
    elif pattern_type == "hotspot":
        # 热点分片加载模式
        hot_shards = all_shards[:3]  # 前3个分片作为热点
        for i in range(iterations):
            if random.random() < 0.7:  # 70%概率加载热点分片
                shard_id = random.choice(hot_shards)
            else:
                shard_id = random.choice(all_shards)
            
            logger.info(f"[{i+1}/{iterations}] {'热点' if shard_id in hot_shards else '普通'}分片: {shard_id}")
            shard_manager.load_shard(shard_id, recursive=True)
            time.sleep(0.1)
    
    elif pattern_type == "mixed":
        # 混合加载模式
        phases = ["sequential", "random", "hotspot"]
        phase_length = iterations // len(phases)
        
        for phase_idx, phase in enumerate(phases):
            logger.info(f"混合模式阶段 {phase_idx+1}/{len(phases)}: {phase}")
            
            start_idx = phase_idx * phase_length
            end_idx = start_idx + phase_length
            
            if phase == "sequential":
                for i in range(start_idx, end_idx):
                    idx = i % len(all_shards)
                    shard_id = all_shards[idx]
                    logger.info(f"[{i+1}/{iterations}] 顺序加载分片: {shard_id}")
                    shard_manager.load_shard(shard_id, recursive=True)
                    time.sleep(0.1)
            
            elif phase == "random":
                for i in range(start_idx, end_idx):
                    shard_id = random.choice(all_shards)
                    logger.info(f"[{i+1}/{iterations}] 随机加载分片: {shard_id}")
                    shard_manager.load_shard(shard_id, recursive=True)
                    time.sleep(0.1)
            
            elif phase == "hotspot":
                hot_shards = all_shards[:3]
                for i in range(start_idx, end_idx):
                    if random.random() < 0.7:
                        shard_id = random.choice(hot_shards)
                    else:
                        shard_id = random.choice(all_shards)
                    
                    logger.info(f"[{i+1}/{iterations}] {'热点' if shard_id in hot_shards else '普通'}分片: {shard_id}")
                    shard_manager.load_shard(shard_id, recursive=True)
                    time.sleep(0.1)
    
    # 生成监控报告
    generate_monitoring_report(monitor, pattern_type)


def generate_monitoring_report(monitor, pattern_name):
    """生成监控报告
    
    Args:
        monitor: 分片监控器
        pattern_name: 模式名称
    """
    logger.info(f"为 {pattern_name} 模式生成监控报告")
    
    # 报告热点分片
    hot_shards = monitor.report_hot_shards(limit=5)
    
    # 获取加载缓慢的分片
    slow_shards = monitor.get_slow_loading_shards(limit=5)
    logger.info("加载最慢的分片:")
    for shard_id, avg_time in slow_shards:
        logger.info(f"  {shard_id}: 平均加载时间 {avg_time:.4f}秒")
    
    # 获取监控统计信息
    stats = monitor.get_monitor_stats()
    logger.info("监控统计信息:")
    for key, value in stats.items():
        logger.info(f"  {key}: {value}")
    
    # 生成优化建议
    suggestions = monitor.generate_optimization_suggestions()
    logger.info("优化建议:")
    for suggestion in suggestions:
        logger.info(f"  - {suggestion}")
    
    # 保存可视化图表
    output_path = f"reports/load_pattern_{pattern_name}.png"
    monitor.visualize_load_pattern(output_path)
    
    # 保存监控数据
    monitor._save_monitoring_data()


def show_monitor_report(save_path):
    """显示保存的监控报告
    
    Args:
        save_path: 监控数据保存路径
    """
    import json
    
    try:
        with open(save_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print("\n===== 分片监控报告 =====")
        
        # 显示基本统计
        stats = data.get("stats", {})
        print(f"总加载次数: {stats.get('total_loads', 0)}")
        print(f"总加载时间: {stats.get('total_load_time', 0):.4f}秒")
        print(f"失败次数: {stats.get('failed_loads', 0)}")
        print(f"失败率: {stats.get('fail_rate', 0) * 100:.2f}%")
        print(f"监控分片数: {stats.get('unique_shards', 0)}")
        
        # 显示热点分片
        print("\n热点分片:")
        for item in data.get("hot_shards", [])[:5]:
            shard_id, count = item
            print(f"  {shard_id}: 加载 {count} 次")
        
        # 显示加载缓慢的分片
        print("\n加载缓慢的分片:")
        for item in data.get("slow_shards", [])[:5]:
            print(f"  {item['shard_id']}: 平均 {item['avg_time']:.4f}秒")
        
        # 显示优化建议
        print("\n优化建议:")
        for suggestion in data.get("suggestions", []):
            print(f"  - {suggestion}")
    
    except Exception as e:
        print(f"读取监控报告失败: {str(e)}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="分片加载监控演示")
    parser.add_argument(
        "--pattern", 
        choices=["random", "sequential", "hotspot", "mixed"], 
        default="mixed",
        help="加载模式"
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=50,
        help="模拟迭代次数"
    )
    parser.add_argument(
        "--shards",
        type=int,
        default=10,
        help="分片数量"
    )
    parser.add_argument(
        "--save-path",
        default="reports/shard_monitor_data.json",
        help="监控数据保存路径"
    )
    parser.add_argument(
        "--show-report",
        action="store_true",
        help="只显示已保存的监控报告"
    )
    
    args = parser.parse_args()
    
    # 设置日志格式
    logger.remove()
    logger.add(
        lambda msg: print(msg, end=""), 
        level="INFO", 
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{function}</cyan>: <level>{message}</level>"
    )
    
    # 如果只显示报告
    if args.show_report:
        show_monitor_report(args.save_path)
        return
    
    # 创建测试元数据
    model_name = "monitor_test_model"
    metadata_manager = create_test_metadata(model_name, args.shards)
    
    # 创建分片管理器
    shard_manager = ShardManager(
        model_name=model_name,
        max_shards_in_memory=5,
        metadata_manager=metadata_manager
    )
    
    # 创建分片监控器
    monitor = create_shard_monitor(
        shard_manager=shard_manager,
        save_path=args.save_path,
        hot_threshold=3
    )
    
    # 模拟加载模式
    simulate_load_patterns(
        shard_manager=shard_manager,
        monitor=monitor,
        pattern_type=args.pattern,
        iterations=args.iterations
    )
    
    # 清理资源
    shard_manager.clear_cache()
    logger.info("演示完成")


if __name__ == "__main__":
    main() 