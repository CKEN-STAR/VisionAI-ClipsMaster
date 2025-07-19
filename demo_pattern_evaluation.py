#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
模式重要性评估演示脚本

演示如何使用模式评估器来分析不同剧本模式的影响力和重要性，
并识别最适合用于爆款混剪的关键模式
"""

import os
import json
import argparse
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any
from loguru import logger
import matplotlib.pyplot as plt
import numpy as np

from src.evaluation.pattern_evaluator import (
    PatternEvaluator, 
    PatternFeature,
    evaluate_patterns,
    get_top_patterns
)

# 设置日志
logger.add("logs/pattern_evaluation_demo.log", rotation="10 MB")


def create_sample_patterns() -> List[Dict[str, Any]]:
    """
    创建示例模式数据
    
    Returns:
        List[Dict]: 示例模式列表
    """
    sample_patterns = [
        {
            "id": "opening_shock",
            "type": "opening",
            "frequency": 0.85,
            "position": 0.05,
            "duration": 3.5,
            "transition": "hard_cut",
            "sentiment": 0.7,
            "keywords": ["震惊", "爆炸", "突然"],
            "context_relevance": 0.6,
            "conflict_level": 0.8,
            "surprise_level": 0.9,
            "emotion_types": ["surprise", "fear"]
        },
        {
            "id": "emotional_revelation",
            "type": "climax",
            "frequency": 0.75,
            "position": 0.65,
            "duration": 5.0,
            "transition": "dissolve",
            "sentiment": -0.8,
            "keywords": ["泪水", "崩溃", "真相"],
            "context_relevance": 0.9,
            "conflict_level": 0.7,
            "surprise_level": 0.8,
            "emotion_types": ["sadness", "surprise"]
        },
        {
            "id": "comedy_relief",
            "type": "transition",
            "frequency": 0.6,
            "position": 0.45,
            "duration": 2.0,
            "transition": "whip",
            "sentiment": 0.9,
            "keywords": ["搞笑", "幽默", "反转"],
            "context_relevance": 0.5,
            "conflict_level": 0.2,
            "surprise_level": 0.7,
            "emotion_types": ["joy"]
        },
        {
            "id": "dramatic_confession",
            "type": "climax",
            "frequency": 0.8,
            "position": 0.75,
            "duration": 6.0,
            "transition": "slow_motion",
            "sentiment": 0.5,
            "keywords": ["告白", "真心", "感动"],
            "context_relevance": 0.85,
            "conflict_level": 0.4,
            "surprise_level": 0.6,
            "emotion_types": ["joy", "surprise"]
        },
        {
            "id": "betrayal_moment",
            "type": "conflict",
            "frequency": 0.7,
            "position": 0.35,
            "duration": 4.5,
            "transition": "zoom",
            "sentiment": -0.7,
            "keywords": ["背叛", "欺骗", "震惊"],
            "context_relevance": 0.8,
            "conflict_level": 0.9,
            "surprise_level": 0.85,
            "emotion_types": ["anger", "surprise"]
        },
        {
            "id": "mysterious_hint",
            "type": "transition",
            "frequency": 0.5,
            "position": 0.3,
            "duration": 1.5,
            "transition": "flash",
            "sentiment": 0.1,
            "keywords": ["线索", "谜团", "暗示"],
            "context_relevance": 0.7,
            "conflict_level": 0.3,
            "surprise_level": 0.5,
            "emotion_types": ["surprise"]
        },
        {
            "id": "final_resolution",
            "type": "resolution",
            "frequency": 0.65,
            "position": 0.85,
            "duration": 4.0,
            "transition": "fade",
            "sentiment": 0.6,
            "keywords": ["和解", "团圆", "幸福"],
            "context_relevance": 0.9,
            "conflict_level": 0.1,
            "surprise_level": 0.3,
            "emotion_types": ["joy"]
        },
        {
            "id": "epic_action",
            "type": "climax",
            "frequency": 0.55,
            "position": 0.6,
            "duration": 7.0,
            "transition": "fast_cut",
            "sentiment": 0.3,
            "keywords": ["打斗", "爆发", "惊险"],
            "context_relevance": 0.6,
            "conflict_level": 0.8,
            "surprise_level": 0.7,
            "emotion_types": ["fear", "anger"]
        },
        {
            "id": "romance_moment",
            "type": "climax",
            "frequency": 0.7,
            "position": 0.55,
            "duration": 3.5,
            "transition": "dissolve",
            "sentiment": 0.8,
            "keywords": ["浪漫", "爱情", "吻"],
            "context_relevance": 0.75,
            "conflict_level": 0.2,
            "surprise_level": 0.4,
            "emotion_types": ["joy"]
        },
        {
            "id": "final_twist",
            "type": "ending",
            "frequency": 0.75,
            "position": 0.95,
            "duration": 2.5,
            "transition": "hard_cut",
            "sentiment": -0.2,
            "keywords": ["反转", "悬念", "震撼"],
            "context_relevance": 0.7,
            "conflict_level": 0.6,
            "surprise_level": 0.95,
            "emotion_types": ["surprise"]
        }
    ]
    return sample_patterns


def save_patterns_to_file(patterns: List[Dict[str, Any]], file_path: str):
    """保存模式到文件"""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(patterns, f, ensure_ascii=False, indent=2)
    logger.info(f"示例模式已保存到: {file_path}")


def save_evaluation_results(results: List[Dict[str, Any]], file_path: str):
    """保存评估结果到文件"""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    logger.info(f"评估结果已保存到: {file_path}")


def print_evaluation_results(results: List[Dict[str, Any]]):
    """打印评估结果"""
    print("\n=== 模式重要性评估结果 ===")
    print(f"{'模式ID':<20} {'类型':<15} {'影响力分数':<10} {'是否显著'}")
    print("-" * 60)
    for result in results:
        pattern_id = result['pattern_id']
        pattern_type = result['pattern_type']
        impact_score = result['impact_score']
        is_significant = result['is_significant']
        print(f"{pattern_id:<20} {pattern_type:<15} {impact_score:.4f}    {'是' if is_significant else '否'}")


def visualize_top_patterns(results: List[Dict[str, Any]], output_path: str = None):
    """
    可视化顶级模式的评估结果
    
    Args:
        results: 评估结果
        output_path: 输出图像路径
    """
    if not results:
        logger.warning("没有结果可以可视化")
        return
    
    # 提取数据
    pattern_ids = [r['pattern_id'] for r in results]
    impact_scores = [r['impact_score'] for r in results]
    pattern_types = [r['pattern_type'] for r in results]
    
    # 为不同类型分配不同颜色
    type_colors = {
        'opening': '#FF5733',      # 红色
        'climax': '#C70039',       # 深红色
        'transition': '#FFC300',   # 黄色
        'conflict': '#900C3F',     # 紫红色
        'resolution': '#581845',   # 紫色
        'ending': '#2471A3'        # 蓝色
    }
    bar_colors = [type_colors.get(t, '#AEB6BF') for t in pattern_types]
    
    # 创建柱状图
    plt.figure(figsize=(12, 7))
    bars = plt.bar(pattern_ids, impact_scores, color=bar_colors)
    
    # 添加标注
    for bar, score in zip(bars, impact_scores):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                 f'{score:.2f}', ha='center', va='bottom', fontsize=9)
    
    # 设置图表属性
    plt.ylim(0, 1.1)
    plt.xlabel('模式ID')
    plt.ylabel('影响力分数')
    plt.title('模式重要性评估结果')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    # 添加图例
    from matplotlib.patches import Patch
    legend_elements = [Patch(facecolor=color, label=p_type) 
                       for p_type, color in type_colors.items() 
                       if p_type in pattern_types]
    plt.legend(handles=legend_elements, loc='best')
    
    # 保存图像
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        logger.info(f"可视化结果已保存到: {output_path}")
    
    # 显示图表
    plt.show()


def create_radar_chart(result: Dict[str, Any], output_path: str = None):
    """
    创建评估指标的雷达图
    
    Args:
        result: 单个模式的评估结果
        output_path: 输出图像路径
    """
    if not result or 'metrics' not in result:
        logger.warning("没有评估指标可以可视化")
        return
    
    # 提取指标数据
    metrics = result['metrics']
    categories = []
    values = []
    weights = []
    
    for metric_name, metric_data in metrics.items():
        categories.append(metric_data['description'])
        values.append(metric_data['raw_score'])
        weights.append(metric_data['weight'])
    
    # 确保闭合
    categories.append(categories[0])
    values.append(values[0])
    weights.append(weights[0])
    
    # 计算角度
    angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
    angles += angles[:1]
    
    # 创建雷达图
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
    
    # 绘制指标得分
    ax.plot(angles, values, 'o-', linewidth=2, label='得分')
    ax.fill(angles, values, alpha=0.25)
    
    # 设置雷达图属性
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_thetagrids(np.degrees(angles[:-1]), categories[:-1])
    
    # 设置y轴范围
    ax.set_ylim(0, 1)
    ax.set_rgrids([0.2, 0.4, 0.6, 0.8], angle=0)
    
    # 添加标题
    plt.title(f"模式 \"{result['pattern_id']}\" 的评估指标雷达图\n(总分: {result['impact_score']:.2f})")
    
    # 保存图像
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        logger.info(f"雷达图已保存到: {output_path}")
    
    # 显示图表
    plt.show()


def compare_pattern_types(results: List[Dict[str, Any]], output_path: str = None):
    """
    比较不同类型模式的平均影响力
    
    Args:
        results: 评估结果
        output_path: 输出图像路径
    """
    if not results:
        logger.warning("没有结果可以比较")
        return
    
    # 按类型分组
    type_scores = {}
    for result in results:
        pattern_type = result['pattern_type']
        impact_score = result['impact_score']
        
        if pattern_type not in type_scores:
            type_scores[pattern_type] = []
        
        type_scores[pattern_type].append(impact_score)
    
    # 计算平均分
    types = []
    avg_scores = []
    for pattern_type, scores in type_scores.items():
        types.append(pattern_type)
        avg_scores.append(sum(scores) / len(scores))
    
    # 创建柱状图
    plt.figure(figsize=(10, 6))
    bars = plt.bar(types, avg_scores, color='#3498DB')
    
    # 添加标注
    for bar, score in zip(bars, avg_scores):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                 f'{score:.2f}', ha='center', va='bottom')
    
    # 设置图表属性
    plt.ylim(0, 1.1)
    plt.xlabel('模式类型')
    plt.ylabel('平均影响力分数')
    plt.title('不同类型模式的平均影响力比较')
    plt.tight_layout()
    
    # 保存图像
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        logger.info(f"类型比较图已保存到: {output_path}")
    
    # 显示图表
    plt.show()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='模式重要性评估演示')
    parser.add_argument('--save_dir', type=str, default='data/demo',
                        help='保存示例数据和结果的目录')
    parser.add_argument('--visualize', action='store_true',
                        help='是否可视化结果')
    args = parser.parse_args()
    
    # 创建保存目录
    os.makedirs(args.save_dir, exist_ok=True)
    
    # 创建示例模式
    logger.info("创建示例模式...")
    patterns = create_sample_patterns()
    
    # 保存示例模式
    patterns_file = os.path.join(args.save_dir, 'sample_patterns.json')
    save_patterns_to_file(patterns, patterns_file)
    
    # 创建评估器
    logger.info("初始化模式评估器...")
    evaluator = PatternEvaluator()
    
    # 评估所有模式
    logger.info("评估模式重要性...")
    results = evaluator.evaluate_multiple_patterns(patterns)
    
    # 保存评估结果
    results_file = os.path.join(args.save_dir, 'evaluation_results.json')
    save_evaluation_results(results, results_file)
    
    # 打印结果
    print_evaluation_results(results)
    
    # 获取前5个重要模式
    top_patterns = evaluator.get_top_patterns(patterns, top_k=5)
    print("\n=== 前5个最重要的模式 ===")
    print_evaluation_results(top_patterns)
    
    # 添加解释性分析
    try:
        from src.interpretability.pattern_explainer import PatternExplainer
        
        print("\n=== 生成模式解释 ===")
        explainer = PatternExplainer()
        explanations = explainer.explain_batch(patterns[:3], results[:3])
        
        for i, explanation in enumerate(explanations):
            pattern_id = explanation.get("pattern_id", "unknown")
            explanation_text = explanation.get("explanation", "无法获取解释")
            
            print(f"\n模式: {pattern_id}")
            print("-" * 60)
            print(explanation_text)
            print("-" * 60)
            
        print("\n=== 使用便捷函数评估并解释 ===")
        from src.evaluation.pattern_evaluator import evaluate_and_explain
        
        combined_result = evaluate_and_explain(patterns, top_k=3)
        
        if combined_result.get("has_explanations", False):
            for explanation in combined_result["explanations"]:
                pattern_id = explanation.get("pattern_id", "unknown")
                explanation_text = explanation.get("explanation", "无法获取解释")
                
                print(f"\n模式: {pattern_id}")
                print("-" * 60)
                print(explanation_text)
                print("-" * 60)
    except ImportError:
        print("\n解释性分析模块不可用")
    except Exception as e:
        print(f"\n解释性分析出错: {e}")
    
    # 按模式类型分组
    grouped_patterns = evaluator.group_by_pattern_type(patterns)
    print("\n=== 按类型分组的模式 ===")
    for pattern_type, group_results in grouped_patterns.items():
        print(f"\n类型: {pattern_type} (共{len(group_results)}个)")
        print_evaluation_results(group_results)
    
    # 可视化结果
    if args.visualize:
        try:
            # 可视化顶级模式
            viz_file = os.path.join(args.save_dir, 'top_patterns_visualization.png')
            visualize_top_patterns(results, viz_file)
            
            # 第一个模式的雷达图
            if results:
                radar_file = os.path.join(args.save_dir, 'pattern_radar_chart.png')
                create_radar_chart(results[0], radar_file)
            
            # 比较不同类型
            compare_file = os.path.join(args.save_dir, 'pattern_types_comparison.png')
            compare_pattern_types(results, compare_file)
        except Exception as e:
            logger.error(f"可视化失败: {e}")
    
    logger.info("演示完成!")


if __name__ == '__main__':
    main() 