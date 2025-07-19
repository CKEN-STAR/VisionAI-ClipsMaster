#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
量化决策算法演示
展示如何在实际项目中使用量化决策引擎
"""

import os
import sys
import psutil
import time
from loguru import logger

# 添加项目根目录到路径以解决导入问题
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.quant.quant_decision import QuantDecisionEngine, select_quant_level
from src.utils.memory_guard import MemoryGuard


def simulate_memory_changes(engine):
    """模拟内存变化场景并展示决策效果"""
    print("\n模拟内存变化场景测试")
    print("=" * 60)
    print(f"{'时间点':10} | {'可用内存(MB)':15} | {'决策结果':10} | {'内存需求(MB)':15} | {'质量分':8}")
    print("-" * 60)
    
    # 模拟一系列内存变化场景，可用内存在模拟，单位MB
    memory_scenarios = [
        ("启动时", 9000),
        ("加载数据", 6500),
        ("处理视频", 4200),
        ("内存压力", 2800),
        ("极限状态", 900),
        ("释放资源", 3800),
        ("恢复正常", 7200)
    ]
    
    for scenario, available_memory in memory_scenarios:
        # 获取决策结果
        quant_level = engine.select_quant_level(available_memory)
        
        # 获取量化级别详情
        level_info = engine.quant_config.get_level_info(quant_level) or {}
        memory_usage = level_info.get('memory_usage', 0)
        quality = level_info.get('quality_score', 0)
        
        # 打印决策结果
        print(f"{scenario:10} | {available_memory:15} | {quant_level:10} | {memory_usage:15} | {quality:8}")
        
        # 小延迟，模拟时间流逝
        time.sleep(0.5)
    
    print("=" * 60)


def demonstrate_model_specific_decisions():
    """演示模型特定的量化决策"""
    print("\n模型特定的量化决策")
    print("=" * 60)
    
    engine = QuantDecisionEngine()
    memory_guard = MemoryGuard()
    
    # 获取当前系统内存信息
    mem_info = memory_guard.get_memory_info()
    available_mb = mem_info['available'] / (1024 * 1024)  # 转换为MB
    total_gb = mem_info['total'] / (1024 * 1024 * 1024)  # 转换为GB
    
    print(f"系统总内存: {total_gb:.2f} GB")
    print(f"当前可用内存: {available_mb:.2f} MB")
    print("-" * 60)
    
    # 测试不同内存场景下的模型配置
    memory_scenarios = [
        ("低内存环境", available_mb * 0.3),
        ("中等内存环境", available_mb * 0.6),
        ("高内存环境", available_mb * 0.9)
    ]
    
    models = ["qwen2.5-7b-zh", "mistral-7b-en"]
    
    for scenario, mem in memory_scenarios:
        print(f"\n{scenario} ({mem:.2f} MB可用):")
        print("-" * 40)
        
        for model in models:
            params = engine.select_model_specific_quant(model, mem)
            
            print(f"模型: {model}")
            print(f"  推荐量化级别: {params['level']}")
            print(f"  内存使用: {params['memory_usage_mb']} MB")
            print(f"  质量评分: {params['quality_score']}")
            print(f"  描述: {params['description']}")
            
    print("=" * 60)


def demonstrate_constraint_based_decisions():
    """演示基于约束的决策"""
    print("\n基于约束的决策演示")
    print("=" * 60)
    
    engine = QuantDecisionEngine()
    
    # 不同约束场景
    constraint_scenarios = [
        ("无约束", None, None),
        ("内存约束", None, 4000),
        ("质量约束", 85, None),
        ("双重约束", 85, 5000),
        ("严格约束", 90, 3000)
    ]
    
    print(f"{'约束场景':15} | {'最低质量':10} | {'最大内存':10} | {'决策结果':10}")
    print("-" * 60)
    
    for scenario, min_quality, max_memory in constraint_scenarios:
        quant_level = engine.recommend_with_constraints(min_quality, max_memory)
        
        # 获取量化级别详情
        level_info = engine.quant_config.get_level_info(quant_level) or {}
        
        print(f"{scenario:15} | {min_quality or '无':10} | {max_memory or '无':10} | {quant_level:10}")
    
    print("=" * 60)


def demonstrate_decision_evaluation():
    """演示决策评估"""
    print("\n决策评估演示")
    print("=" * 60)
    
    engine = QuantDecisionEngine()
    
    # 获取当前系统推荐
    mem_info = psutil.virtual_memory()
    available_mb = mem_info.available / (1024 * 1024)
    recommended = engine.select_quant_level(available_mb)
    
    print(f"当前系统推荐量化级别: {recommended}")
    print("-" * 60)
    
    # 评估不同量化级别对中文模型的影响
    model = "qwen2.5-7b-zh"
    print(f"模型 {model} 的量化级别评估:")
    print("-" * 40)
    
    for level in ["Q2_K", "Q4_K_M", "Q6_K"]:
        eval_result = engine.evaluate_decision(level, model)
        
        print(f"量化级别: {level}")
        print(f"  内存使用: {eval_result['memory_usage_mb']} MB")
        print(f"  质量评分: {eval_result['quality_score']}/100")
        print(f"  与默认级别相比: {'增加' if eval_result['quality_diff'] > 0 else '减少'} {abs(eval_result['quality_diff'])} 分")
        print(f"  内存差异: {'增加' if eval_result['memory_diff'] > 0 else '减少'} {abs(eval_result['memory_diff'])} MB")
        print()
    
    print("=" * 60)


def main():
    """主函数"""
    logger.info("量化决策引擎演示程序")
    
    # 创建决策引擎
    engine = QuantDecisionEngine()
    
    # 1. 简单使用示例
    print("\n基础用法示例:")
    print("=" * 60)
    
    # 获取当前系统内存状态
    mem = psutil.virtual_memory()
    available_mb = mem.available / (1024 * 1024)
    
    # 方法1: 使用全局函数
    level1 = select_quant_level(available_mb)
    print(f"方法1 - 全局函数调用: ")
    print(f"  可用内存: {available_mb:.2f} MB")
    print(f"  推荐量化级别: {level1}")
    
    # 方法2: 使用引擎实例
    level2 = engine.select_quant_level()
    print(f"\n方法2 - 使用引擎实例: ")
    print(f"  自动检测内存")
    print(f"  推荐量化级别: {level2}")
    
    # 2. 模拟内存变化场景
    simulate_memory_changes(engine)
    
    # 3. 模型特定决策
    demonstrate_model_specific_decisions()
    
    # 4. 基于约束的决策
    demonstrate_constraint_based_decisions()
    
    # 5. 决策评估
    demonstrate_decision_evaluation()
    
    # 结束演示
    print("\n量化决策引擎演示完成")


if __name__ == "__main__":
    main() 