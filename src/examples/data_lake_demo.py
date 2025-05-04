#!/usr/bin/env python
"""
爆款剧本数据湖演示脚本

展示如何使用爆款剧本数据湖功能进行：
1. 数据导入
2. 模式查询
3. 统计分析
4. 数据导出

此脚本可作为其他模块集成数据湖的参考样例。
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.data.hit_pattern_lake import HitPatternLake
from src.data.lake.generate_test_data import generate_test_data, add_test_data_to_lake
import pandas as pd
import numpy as np
import time
from loguru import logger


def demo_data_import():
    """演示数据导入功能"""
    print("\n1. 演示数据导入")
    print("-" * 50)
    
    # 生成测试数据
    test_data_dir = "data/demo_data"
    print(f"生成测试数据到: {test_data_dir}")
    pairs = generate_test_data(test_data_dir, num_pairs=3, languages=["zh"])
    
    # 导入数据到数据湖
    lake = HitPatternLake()
    print("\n导入数据到数据湖:")
    for origin_file, hit_file in pairs:
        success = lake.ingest_data(origin_file, hit_file)
        print(f"  导入 {origin_file} -> {hit_file}: {'成功' if success else '失败'}")
    
    # 查看数据湖统计信息
    stats = lake.get_statistics()
    print("\n数据湖统计:")
    print(f"  总文件数: {stats.get('total_files', 0)}")
    print(f"  记录数: {stats.get('record_count', 0)}")
    
    return lake


def demo_pattern_search(lake: HitPatternLake):
    """演示模式查询功能"""
    print("\n2. 演示模式查询")
    print("-" * 50)
    
    # 查询所有数据
    all_data = lake.query_patterns(limit=10)
    print(f"\n所有模式 (前{min(10, len(all_data))}条):")
    if not all_data.empty:
        for i, row in all_data.head(5).iterrows():
            print(f"  {i+1}. {row['origin_scene'][:30]}... -> {row['hit_scene'][:30]}...")
            print(f"     类型: {row['modification_type']}, 分值: {row['impact_score']:.2f}")
    else:
        print("  没有找到数据")
    
    # 按类型查询
    mod_types = all_data['modification_type'].unique() if not all_data.empty else []
    
    if mod_types:
        mod_type = mod_types[0]
        print(f"\n按类型查询 - {mod_type}:")
        type_data = lake.query_patterns(modification_type=mod_type, limit=5)
        
        for i, row in type_data.iterrows():
            print(f"  {i+1}. {row['origin_scene'][:30]}... -> {row['hit_scene'][:30]}...")
            print(f"     分值: {row['impact_score']:.2f}")
    
    # 按分值过滤
    min_score = 0.7
    print(f"\n高影响分值模式 (>= {min_score}):")
    high_impact = lake.query_patterns(min_impact=min_score, limit=5)
    
    if not high_impact.empty:
        for i, row in high_impact.iterrows():
            print(f"  {i+1}. {row['modification_type']}: {row['impact_score']:.2f}")
            print(f"     {row['origin_scene'][:50]}...")
            print(f"     {row['hit_scene'][:50]}...")
    else:
        print("  没有找到数据")


def demo_pattern_analysis(lake: HitPatternLake):
    """演示模式分析功能"""
    print("\n3. 演示模式分析")
    print("-" * 50)
    
    # 获取各类型的TOP模式
    top_patterns = lake.get_top_patterns(top_n=3)
    
    if top_patterns:
        print("\n各类型最佳模式:")
        for mod_type, patterns in top_patterns.items():
            print(f"\n类型: {mod_type} (Top {len(patterns)})")
            
            for i, pattern in enumerate(patterns, 1):
                print(f"  {i}. 分值: {pattern['impact_score']:.2f}")
                print(f"     原始: {pattern['origin_scene'][:50]}...")
                print(f"     改写: {pattern['hit_scene'][:50]}...")
    else:
        print("  没有找到数据")
    
    # 模拟模式应用
    print("\n模式应用示例:")
    example_scenes = [
        "主角无精打采地走在回家的路上",
        "两个朋友在咖啡厅里谈论着项目计划",
        "她看着窗外，思考着生活的意义"
    ]
    
    for scene in example_scenes:
        print(f"\n原始场景: {scene}")
        # 模拟应用模式（实际应用中可能涉及到更复杂的匹配和生成）
        if top_patterns:
            # 随机选择一种转换类型
            mod_type = list(top_patterns.keys())[0]
            if top_patterns[mod_type]:
                pattern = top_patterns[mod_type][0]
                # 简单示例：将原始场景的前半部分与模式的后半部分组合
                half = len(scene) // 2
                new_scene = scene[:half] + "，" + pattern['hit_scene'].split('，', 1)[-1] if '，' in pattern['hit_scene'] else pattern['hit_scene']
                print(f"应用 {mod_type} 模式后: {new_scene}")
                print(f"预计影响分值: {pattern['impact_score']:.2f}")


def demo_data_export(lake: HitPatternLake):
    """演示数据导出功能"""
    print("\n4. 演示数据导出")
    print("-" * 50)
    
    # 查询数据
    all_data = lake.query_patterns(limit=100)
    
    if all_data.empty:
        print("  没有数据可导出")
        return
    
    # 导出到CSV
    export_dir = "data/exports"
    os.makedirs(export_dir, exist_ok=True)
    
    # 导出所有数据
    all_data_path = os.path.join(export_dir, "all_patterns.csv")
    all_data.to_csv(all_data_path, index=False, encoding='utf-8')
    print(f"\n所有数据已导出到: {all_data_path}")
    
    # 按类型导出
    mod_types = all_data['modification_type'].unique()
    print("\n按类型导出:")
    
    for mod_type in mod_types:
        type_data = all_data[all_data['modification_type'] == mod_type]
        type_file = os.path.join(export_dir, f"{mod_type}_patterns.csv")
        type_data.to_csv(type_file, index=False, encoding='utf-8')
        print(f"  {mod_type}: {len(type_data)}条记录 -> {type_file}")
    
    # 导出统计摘要
    stats = lake.get_statistics()
    stats_file = os.path.join(export_dir, "lake_stats.json")
    
    import json
    with open(stats_file, 'w', encoding='utf-8') as f:
        # 处理不可序列化的类型
        clean_stats = {}
        for k, v in stats.items():
            if isinstance(v, np.integer):
                clean_stats[k] = int(v)
            elif isinstance(v, np.floating):
                clean_stats[k] = float(v)
            elif isinstance(v, np.ndarray):
                clean_stats[k] = v.tolist()
            else:
                clean_stats[k] = v
        
        json.dump(clean_stats, f, ensure_ascii=False, indent=2)
    
    print(f"\n数据湖统计信息已导出到: {stats_file}")


def main():
    """主函数"""
    print("=" * 80)
    print("爆款剧本数据湖演示")
    print("=" * 80)
    
    # 演示数据导入
    lake = demo_data_import()
    
    # 演示模式查询
    demo_pattern_search(lake)
    
    # 演示模式分析
    demo_pattern_analysis(lake)
    
    # 演示数据导出
    demo_data_export(lake)
    
    print("\n" + "=" * 80)
    print("演示完成!")
    print("=" * 80)


if __name__ == "__main__":
    main() 