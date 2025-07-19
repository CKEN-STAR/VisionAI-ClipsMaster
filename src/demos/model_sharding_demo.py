#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
模型分片功能演示

演示如何使用模型分片切割器对大型模型进行分片处理，以及如何根据不同硬件条件选择分片策略。
"""

import os
import sys
import time
import argparse
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.sharding.model_splitter import ModelSplitter
from src.core.shard_policy_manager import ShardPolicyManager
from src.utils.memory_manager import MemoryManager
from src.utils.device_manager import HybridDevice
from loguru import logger


def create_dummy_model(path: Path, size_mb: int):
    """创建一个虚拟模型文件用于测试
    
    Args:
        path: 模型文件路径
        size_mb: 文件大小(MB)
    """
    # 确保目录存在
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # 创建指定大小的文件
    size_bytes = size_mb * 1024 * 1024
    
    # 每次写入1MB
    chunk_size = 1024 * 1024
    num_chunks = size_bytes // chunk_size
    remaining_bytes = size_bytes % chunk_size
    
    print(f"创建 {size_mb}MB 的虚拟模型文件: {path}")
    
    with open(path, 'wb') as f:
        for i in range(num_chunks):
            # 生成随机数据
            data = os.urandom(chunk_size)
            f.write(data)
            
            # 显示进度
            if i % 100 == 0:
                progress = (i + 1) / num_chunks * 100
                print(f"  进度: {progress:.1f}% ({i+1}/{num_chunks})", end='\r')
        
        # 写入剩余字节
        if remaining_bytes > 0:
            f.write(os.urandom(remaining_bytes))
    
    print(f"\n虚拟模型文件创建完成: {path} ({size_mb}MB)")
    return path


def demonstrate_sharding(model_path, output_dir=None, strategies=None):
    """演示不同策略的模型分片
    
    Args:
        model_path: 模型文件路径
        output_dir: 输出目录
        strategies: 要演示的策略列表，默认为所有策略
    """
    # 初始化分片管理器
    policy_manager = ShardPolicyManager()
    available_strategies = [s["name"] for s in policy_manager.get_all_strategies()]
    
    # 如果没有指定策略，使用所有可用策略
    if not strategies:
        strategies = available_strategies
    else:
        # 验证指定的策略是否有效
        for strategy in strategies:
            if strategy not in available_strategies:
                print(f"警告: 策略 '{strategy}' 不存在，将被跳过")
        
        # 过滤无效策略
        strategies = [s for s in strategies if s in available_strategies]
    
    if not strategies:
        print("没有有效的策略可供演示")
        return
    
    # 初始化分片切割器
    splitter = ModelSplitter(policy_manager=policy_manager)
    
    # 检查模型文件
    model_path = Path(model_path)
    if not model_path.exists():
        print(f"错误: 模型文件不存在: {model_path}")
        return
    
    model_size_mb = model_path.stat().st_size / (1024 * 1024)
    print(f"\n模型文件: {model_path}")
    print(f"文件大小: {model_size_mb:.2f} MB")
    
    # 确定输出目录
    if output_dir:
        base_output_dir = Path(output_dir)
    else:
        base_output_dir = model_path.parent / "demo_shards"
    
    base_output_dir.mkdir(parents=True, exist_ok=True)
    
    # 对每个策略进行分片演示
    print(f"\n开始演示 {len(strategies)} 个分片策略:\n")
    
    results = []
    
    for i, strategy in enumerate(strategies, 1):
        strategy_output_dir = base_output_dir / f"{model_path.stem}_{strategy}_shards"
        
        print(f"[策略 {i}/{len(strategies)}] {strategy}")
        
        # 记录开始时间
        start_time = time.time()
        
        try:
            # 执行分片
            result = splitter.split_model(
                model_path=model_path,
                strategy=strategy,
                output_dir=strategy_output_dir
            )
            
            elapsed = time.time() - start_time
            
            # 记录结果
            result["elapsed_time"] = elapsed
            results.append(result)
            
            # 输出结果
            shard_count = result["num_shards"]
            shard_size_mb = result.get("shard_size_mb", 0)
            if shard_size_mb == 0 and "shard_size_bytes" in result:
                shard_size_mb = result["shard_size_bytes"] / (1024 * 1024)
            
            print(f"  分片数量: {shard_count}")
            print(f"  每片大小: {shard_size_mb:.2f} MB")
            print(f"  耗时: {elapsed:.2f} 秒")
            print(f"  输出目录: {strategy_output_dir}\n")
            
        except Exception as e:
            print(f"  分片失败: {e}\n")
    
    # 比较结果
    if results:
        print("\n分片策略比较:")
        print(f"{'策略':<15} {'分片数':<8} {'每片大小 (MB)':<15} {'耗时 (秒)':<12}")
        print("-" * 55)
        
        # 按耗时排序
        sorted_results = sorted(results, key=lambda x: x["elapsed_time"])
        
        for result in sorted_results:
            strategy = result["strategy"]
            num_shards = result["num_shards"]
            
            shard_size_mb = result.get("shard_size_mb", 0)
            if shard_size_mb == 0 and "shard_size_bytes" in result:
                shard_size_mb = result["shard_size_bytes"] / (1024 * 1024)
            
            elapsed = result["elapsed_time"]
            
            print(f"{strategy:<15} {num_shards:<8} {shard_size_mb:<15.2f} {elapsed:<12.2f}")


def demonstrate_strategy_selection():
    """演示不同硬件条件下的自动策略选择"""
    # 初始化分片管理器
    policy_manager = ShardPolicyManager()
    memory_manager = MemoryManager()
    device_manager = HybridDevice()
    
    # 获取当前系统信息
    available_memory = memory_manager.get_available_memory()
    has_gpu = device_manager.has_gpu
    device_capabilities = device_manager.get_capabilities()
    
    print("\n系统硬件信息:")
    print(f"  可用内存: {available_memory} MB")
    print(f"  是否有GPU: {has_gpu}")
    
    if has_gpu:
        gpu_info = device_capabilities.get("gpu", {})
        print(f"  GPU类型: {gpu_info.get('name', 'Unknown')}")
        print(f"  GPU内存: {gpu_info.get('memory', 0)} MB")
    
    # 测试不同内存条件下的策略选择
    print("\n不同内存条件下的自动策略选择:")
    print(f"{'内存 (MB)':<12} {'选择策略':<15} {'最大分片 (MB)':<15} {'适用场景'}")
    print("-" * 70)
    
    memory_scenarios = [
        3500,    # 低内存
        5500,    # 中低内存
        8000,    # 中等内存
        16000,   # 高内存
        32000    # 极高内存
    ]
    
    for mem in memory_scenarios:
        # 模拟可用内存值，替换掉内存管理器中的实际获取函数
        memory_manager.get_available_memory = lambda: mem
        
        # 重新初始化分片管理器以使用新的内存值
        test_manager = ShardPolicyManager()
        test_manager.memory_manager = memory_manager
        
        # 获取自动选择的策略
        strategy_name = test_manager._auto_select_strategy()
        strategy = test_manager._get_strategy_by_name(strategy_name)
        
        print(f"{mem:<12} {strategy_name:<15} {strategy['max_shard_size']:<15} {strategy['suitable_for']}")
    
    # 恢复原始函数
    memory_manager.get_available_memory = MemoryManager().get_available_memory


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="模型分片功能演示")
    
    subparsers = parser.add_subparsers(dest="command", help="子命令")
    
    # 创建虚拟模型命令
    create_parser = subparsers.add_parser("create", help="创建虚拟模型文件")
    create_parser.add_argument("output_path", help="输出文件路径")
    create_parser.add_argument("--size", type=int, default=1000, help="文件大小(MB)")
    
    # 分片演示命令
    shard_parser = subparsers.add_parser("shard", help="演示模型分片")
    shard_parser.add_argument("model_path", help="模型文件路径")
    shard_parser.add_argument("--output-dir", help="输出目录")
    shard_parser.add_argument("--strategies", nargs="+", help="要演示的策略")
    
    # 策略选择演示命令
    subparsers.add_parser("strategy", help="演示策略选择")
    
    # 解析参数
    args = parser.parse_args()
    
    if args.command == "create":
        create_dummy_model(Path(args.output_path), args.size)
    elif args.command == "shard":
        demonstrate_sharding(args.model_path, args.output_dir, args.strategies)
    elif args.command == "strategy":
        demonstrate_strategy_selection()
    else:
        parser.print_help()


if __name__ == "__main__":
    main() 