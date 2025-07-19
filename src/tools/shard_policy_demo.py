#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
分片策略配置中心演示脚本

此脚本演示如何使用分片策略配置中心的功能：
1. 获取当前分片策略
2. 切换不同级别的分片策略
3. 生成模型分片计划
4. 根据系统条件动态调整策略
"""

import os
import sys
import time
import json
import argparse
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.core.shard_policy_manager import ShardPolicyManager
from src.utils.memory_manager import MemoryManager
from loguru import logger


def display_json(data, title=None):
    """格式化显示JSON数据"""
    if title:
        print(f"\n===== {title} =====")
    print(json.dumps(data, indent=2, ensure_ascii=False))
    print("=" * 50)


def demo_basic_operations(manager):
    """演示基本操作"""
    print("\n🔹 演示基本操作")
    
    # 1. 获取当前分片策略
    current = manager.get_current_strategy()
    display_json(current, "当前分片策略")
    
    # 2. 获取所有可用的分片策略
    all_strategies = manager.get_all_strategies()
    print(f"\n可用的分片策略 ({len(all_strategies)}):")
    for i, strategy in enumerate(all_strategies, 1):
        print(f"  {i}. {strategy['name']} - {strategy['desc']} (最大分片大小: {strategy['max_shard_size']}MB)")
    
    # 3. 获取配置摘要
    summary = manager.get_configuration_summary()
    display_json(summary, "配置摘要")


def demo_strategy_switching(manager):
    """演示策略切换"""
    print("\n🔹 演示策略切换")
    
    original_strategy = manager.current_strategy
    print(f"初始策略: {original_strategy}")
    
    # 依次切换到每个策略
    strategies = ["minimum", "conservative", "balanced", "performance"]
    
    for strategy in strategies:
        if strategy == manager.current_strategy:
            print(f"跳过当前策略: {strategy}")
            continue
            
        print(f"\n切换到 {strategy} 策略...")
        success = manager.apply_strategy(strategy, f"演示切换到{strategy}")
        
        if success:
            current = manager.get_current_strategy()
            print(f"✅ 成功切换到 {strategy} 策略")
            print(f"   描述: {current['desc']}")
            print(f"   最大分片大小: {current['max_shard_size']}MB")
            time.sleep(1)
        else:
            print(f"❌ 切换到 {strategy} 策略失败")
    
    # 恢复原始策略
    print(f"\n恢复到原始策略: {original_strategy}")
    manager.apply_strategy(original_strategy, "恢复原始策略")


def demo_model_specific_settings(manager):
    """演示模型特定设置"""
    print("\n🔹 演示模型特定设置")
    
    # 1. 获取现有模型设置
    models = ["qwen2.5-7b-zh", "mistral-7b-en"]
    
    for model in models:
        settings = manager.get_model_specific_settings(model)
        if settings:
            print(f"\n模型 {model} 的特定设置:")
            display_json(settings)
        else:
            print(f"\n模型 {model} 没有特定设置")
    
    # 2. 创建/更新模型设置
    test_model = "test-model"
    custom_settings = {
        "default_strategy": "balanced",
        "custom_settings": {
            "max_shard_size": 1500,
            "layer_grouping_override": [
                {"group": ["embedding", "attention_1"]},
                {"group": ["ffn_1", "attention_2"]}
            ],
            "load_priority": ["embedding", "attention_1"]
        }
    }
    
    print(f"\n为测试模型 {test_model} 更新设置...")
    success = manager.update_model_settings(test_model, custom_settings)
    
    if success:
        print(f"✅ 成功更新模型设置")
        updated_settings = manager.get_model_specific_settings(test_model)
        display_json(updated_settings, f"模型 {test_model} 的更新设置")
    else:
        print(f"❌ 更新模型设置失败")


def demo_sharding_plan(manager):
    """演示生成分片计划"""
    print("\n🔹 演示生成分片计划")
    
    # 为不同大小的模型生成分片计划
    model_sizes = {
        "小型模型 (3GB)": 3 * 1024 * 1024 * 1024,
        "中型模型 (7GB)": 7 * 1024 * 1024 * 1024,
        "大型模型 (14GB)": 14 * 1024 * 1024 * 1024,
        "超大模型 (30GB)": 30 * 1024 * 1024 * 1024
    }
    
    for name, size in model_sizes.items():
        print(f"\n为{name}生成分片计划:")
        plan = manager.generate_sharding_plan("generic-model", size)
        
        print(f"  策略: {plan['strategy']}")
        print(f"  分片数量: {plan['num_shards']}")
        print(f"  每个分片大小: {plan['shard_size_mb']:.2f}MB")
        print(f"  加载模式: {plan['loading_mode']}")
        print(f"  验证级别: {plan['verification_level']}")


def demo_dynamic_adjustment(manager, memory_manager):
    """演示动态调整"""
    print("\n🔹 演示动态调整")
    
    # 确保启用动态调整
    if not manager.enable_dynamic:
        manager.enable_dynamic = True
        print("已启用动态调整")
    
    # 获取当前内存状态
    current_memory = memory_manager.get_available_memory()
    print(f"\n当前可用内存: {current_memory}MB")
    
    # 评估当前条件
    needs_adjustment, suggested_strategy, reason = manager.evaluate_current_conditions()
    
    print(f"需要调整: {needs_adjustment}")
    print(f"建议策略: {suggested_strategy if suggested_strategy else '无'}")
    print(f"原因: {reason}")
    
    # 如果需要，自动调整
    if needs_adjustment:
        print("\n执行自动调整...")
        adjusted = manager.adjust_if_needed()
        
        if adjusted:
            current = manager.get_current_strategy()
            print(f"✅ 已自动调整到 {manager.current_strategy} 策略")
            print(f"   描述: {current['desc']}")
        else:
            print("❌ 自动调整失败")
    
    # 显示策略历史
    history = manager.get_strategy_history()
    print(f"\n策略变更历史 (最近 {len(history)} 条记录):")
    
    for i, record in enumerate(reversed(history[:5]), 1):
        print(f"  {i}. {record['datetime']}: {record.get('prev_strategy', '无')} -> {record['new_strategy']}")
        print(f"     原因: {record['reason']}")
        print(f"     可用内存: {record['memory_available']}MB")
        print("")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="分片策略配置中心演示")
    parser.add_argument("--config", default="configs/shard_policy.yaml", help="配置文件路径")
    parser.add_argument("--demo", choices=["all", "basic", "switch", "model", "plan", "dynamic"], 
                        default="all", help="要运行的演示")
    args = parser.parse_args()
    
    # 初始化管理器
    manager = ShardPolicyManager(config_path=args.config)
    memory_manager = MemoryManager()
    
    print("\n========================================")
    print("🚀 分片策略配置中心演示")
    print("========================================")
    
    # 运行选定的演示
    if args.demo in ["all", "basic"]:
        demo_basic_operations(manager)
    
    if args.demo in ["all", "switch"]:
        demo_strategy_switching(manager)
    
    if args.demo in ["all", "model"]:
        demo_model_specific_settings(manager)
    
    if args.demo in ["all", "plan"]:
        demo_sharding_plan(manager)
    
    if args.demo in ["all", "dynamic"]:
        demo_dynamic_adjustment(manager, memory_manager)
    
    print("\n========================================")
    print("✨ 演示完成")
    print("========================================")


if __name__ == "__main__":
    main() 