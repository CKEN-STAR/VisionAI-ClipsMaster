#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
模式可解释性分析演示脚本

演示如何使用模式解释器来分析和解释不同剧本模式的重要性，
帮助用户理解为什么特定模式对爆款短视频有重要影响。
"""

import os
import json
import argparse
import pandas as pd
from typing import Dict, List, Any
from loguru import logger
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import numpy as np

# 配置中文字体显示（如有需要）
try:
    plt.rcParams['font.sans-serif'] = ['SimHei']  # 设置中文字体
    plt.rcParams['axes.unicode_minus'] = False    # 正确显示负号
except Exception as e:
    logger.warning(f"设置中文字体失败: {e}，可能导致中文显示异常")

# 导入相关模块
from src.evaluation.pattern_evaluator import (
    PatternEvaluator, 
    PatternFeature,
    evaluate_patterns,
    get_top_patterns
)
from src.interpretability.pattern_explainer import (
    PatternExplainer,
    explain_pattern,
    batch_explain_patterns
)

# 设置日志
logger.add("logs/pattern_interpretation_demo.log", rotation="10 MB")


def load_sample_patterns(file_path: str = None) -> List[Dict[str, Any]]:
    """
    加载示例模式数据
    
    Args:
        file_path: 模式数据文件路径，如果为None，使用内置示例
        
    Returns:
        List[Dict]: 示例模式列表
    """
    if file_path and os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                patterns = json.load(f)
            logger.info(f"从文件 {file_path} 加载了 {len(patterns)} 个模式")
            return patterns
        except Exception as e:
            logger.error(f"从文件加载模式失败: {e}，将使用内置示例")
    
    # 使用内置示例
    logger.info("使用内置示例模式数据")
    return [
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


def save_result_to_file(data: Any, file_path: str, indent: int = 2):
    """保存结果到文件"""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=indent)
        logger.info(f"结果已保存到: {file_path}")
        return True
    except Exception as e:
        logger.error(f"保存结果失败: {e}")
        return False


def print_explanations(explanations: List[Dict[str, Any]]):
    """打印模式解释"""
    print("\n=== 模式解释结果 ===")
    
    for i, explanation in enumerate(explanations):
        pattern_id = explanation.get("pattern_id", "unknown")
        explanation_text = explanation.get("explanation", "无法获取解释")
        
        print(f"\n{i+1}. 模式: {pattern_id}")
        print("-" * 80)
        print(explanation_text)
        print("-" * 80)


def create_explanation_visualization(explanations: List[Dict[str, Any]], 
                                   evaluation_results: List[Dict[str, Any]],
                                   output_path: str = None):
    """
    创建模式解释可视化图表
    
    Args:
        explanations: 解释结果列表
        evaluation_results: 评估结果列表
        output_path: 输出图像路径
    """
    if not explanations or not evaluation_results or len(explanations) != len(evaluation_results):
        logger.error("解释和评估结果不匹配，无法创建可视化图表")
        return
    
    # 准备数据
    pattern_ids = []
    impact_scores = []
    pattern_types = []
    explanation_snippets = []
    
    for i, (explanation, evaluation) in enumerate(zip(explanations, evaluation_results)):
        pattern_id = explanation.get("pattern_id", "unknown")
        pattern_ids.append(pattern_id)
        
        impact_score = evaluation.get("impact_score", 0)
        impact_scores.append(impact_score)
        
        pattern_type = evaluation.get("pattern_type", "generic")
        pattern_types.append(pattern_type)
        
        # 获取解释文本片段作为注释
        explanation_text = explanation.get("explanation", "")
        if explanation_text:
            # 截取前20个字符
            snippet = explanation_text[:20] + "..." if len(explanation_text) > 20 else explanation_text
            explanation_snippets.append(snippet)
        else:
            explanation_snippets.append("")
    
    # 为不同类型分配不同颜色
    type_colors = {
        'opening': '#FF5733',      # 红色
        'climax': '#C70039',       # 深红色
        'transition': '#FFC300',   # 黄色
        'conflict': '#900C3F',     # 紫红色
        'resolution': '#581845',   # 紫色
        'ending': '#2471A3'        # 蓝色
    }
    default_color = '#AEB6BF'     # 默认灰色
    
    bar_colors = [type_colors.get(pt, default_color) for pt in pattern_types]
    
    # 创建图表
    plt.figure(figsize=(14, 8))
    
    # 绘制条形图
    bars = plt.bar(pattern_ids, impact_scores, color=bar_colors, alpha=0.7)
    
    # 添加水平分隔线
    plt.axhline(y=0.6, color='r', linestyle='--', alpha=0.5, label='重要性阈值')
    
    # 添加标签
    plt.xlabel('模式ID')
    plt.ylabel('影响力分数')
    plt.title('模式重要性评估与解释')
    plt.xticks(rotation=45, ha='right')
    plt.ylim(0, 1.1)
    
    # 添加注释
    for i, (bar, score, snippet) in enumerate(zip(bars, impact_scores, explanation_snippets)):
        plt.text(
            bar.get_x() + bar.get_width()/2,
            score + 0.05,
            f"{score:.2f}",
            ha='center',
            va='bottom',
            fontsize=9
        )
        
        if snippet:
            plt.text(
                bar.get_x() + bar.get_width()/2,
                0.05,
                snippet,
                ha='center',
                va='bottom',
                fontsize=8,
                rotation=90,
                alpha=0.7
            )
    
    # 添加图例
    from matplotlib.patches import Patch
    legend_elements = [Patch(facecolor=color, label=p_type) 
                     for p_type, color in type_colors.items() 
                     if p_type in pattern_types]
    legend_elements.append(Patch(facecolor='r', alpha=0.5, label='重要性阈值'))
    plt.legend(handles=legend_elements, loc='best')
    
    plt.tight_layout()
    
    # 保存图像
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        logger.info(f"可视化图表已保存到: {output_path}")
    
    # 显示图表
    plt.show()


def create_text_report(patterns: List[Dict[str, Any]], 
                     evaluation_results: List[Dict[str, Any]],
                     explanations: List[Dict[str, Any]],
                     output_path: str = None) -> str:
    """
    创建文本报告
    
    Args:
        patterns: 模式数据
        evaluation_results: 评估结果
        explanations: 解释结果
        output_path: 输出文件路径
        
    Returns:
        str: 报告文本
    """
    if not patterns or not evaluation_results or not explanations:
        return "无法生成报告: 数据不完整"
    
    report = "# 模式重要性分析与解释报告\n\n"
    report += f"## 概述\n\n"
    report += f"本报告分析了{len(patterns)}个视频模式的重要性及其对爆款短视频的影响。\n\n"
    
    # 添加总体统计
    significant_count = sum(1 for r in evaluation_results if r.get("is_significant", False))
    avg_impact = sum(r.get("impact_score", 0) for r in evaluation_results) / len(evaluation_results)
    
    report += f"- 分析模式总数: {len(patterns)}\n"
    report += f"- 重要模式数量: {significant_count}\n"
    report += f"- 平均影响力分数: {avg_impact:.2f}\n\n"
    
    # 按类型统计
    pattern_types = {}
    for eval_result in evaluation_results:
        pattern_type = eval_result.get("pattern_type", "未知")
        if pattern_type not in pattern_types:
            pattern_types[pattern_type] = []
        pattern_types[pattern_type].append(eval_result.get("impact_score", 0))
    
    report += "## 模式类型分析\n\n"
    
    for pattern_type, scores in pattern_types.items():
        avg_score = sum(scores) / len(scores)
        report += f"- {pattern_type}: {len(scores)}个模式, 平均影响力: {avg_score:.2f}\n"
    
    report += "\n## 重要模式详细分析\n\n"
    
    # 对模式按照影响力排序
    sorted_indices = sorted(range(len(evaluation_results)), 
                          key=lambda i: evaluation_results[i].get("impact_score", 0),
                          reverse=True)
    
    # 输出前5个重要模式的详细分析
    for i in sorted_indices[:5]:
        pattern = patterns[i]
        eval_result = evaluation_results[i]
        explanation = explanations[i]
        
        pattern_id = pattern.get("id", "unknown")
        pattern_type = pattern.get("type", "generic")
        impact_score = eval_result.get("impact_score", 0)
        
        report += f"### 模式 {pattern_id} (类型: {pattern_type})\n\n"
        report += f"- 影响力分数: {impact_score:.2f}\n"
        report += f"- 是否显著: {'是' if eval_result.get('is_significant', False) else '否'}\n"
        
        # 添加指标分数
        report += "- 评分指标:\n"
        for metric_name, metric_data in eval_result.get("metrics", {}).items():
            raw_score = metric_data.get("raw_score", 0)
            description = metric_data.get("description", metric_name)
            report += f"  - {description}: {raw_score:.2f}\n"
        
        # 添加解释
        explanation_text = explanation.get("explanation", "无法获取解释")
        report += f"\n**解释:**\n\n{explanation_text}\n\n"
        report += "-" * 50 + "\n\n"
    
    # 保存报告
    if output_path:
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)
            logger.info(f"报告已保存到: {output_path}")
        except Exception as e:
            logger.error(f"保存报告失败: {e}")
    
    return report


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='模式可解释性分析演示')
    parser.add_argument('--input', type=str, default=None,
                        help='输入模式数据文件路径')
    parser.add_argument('--output_dir', type=str, default='data/interpretability_demo',
                        help='输出目录')
    parser.add_argument('--visualize', action='store_true',
                        help='是否生成可视化图表')
    args = parser.parse_args()
    
    # 创建输出目录
    os.makedirs(args.output_dir, exist_ok=True)
    
    # 加载示例模式
    patterns = load_sample_patterns(args.input)
    
    # 创建评估器和解释器
    logger.info("初始化模式评估器和解释器...")
    evaluator = PatternEvaluator()
    explainer = PatternExplainer()
    
    # 评估模式重要性
    logger.info(f"评估{len(patterns)}个模式的重要性...")
    evaluation_results = evaluator.evaluate_multiple_patterns(patterns)
    
    # 保存评估结果
    eval_output_path = os.path.join(args.output_dir, "evaluation_results.json")
    save_result_to_file(evaluation_results, eval_output_path)
    
    # 解释评估结果
    logger.info("生成模式重要性解释...")
    explanations = explainer.explain_batch(patterns, evaluation_results)
    
    # 保存解释结果
    expl_output_path = os.path.join(args.output_dir, "explanations.json")
    save_result_to_file(explanations, expl_output_path)
    
    # 打印解释
    print_explanations(explanations)
    
    # 创建报告
    logger.info("生成分析报告...")
    report_path = os.path.join(args.output_dir, "analysis_report.md")
    report = create_text_report(patterns, evaluation_results, explanations, report_path)
    
    # 可视化
    if args.visualize:
        logger.info("创建可视化图表...")
        viz_path = os.path.join(args.output_dir, "interpretation_visualization.png")
        create_explanation_visualization(explanations, evaluation_results, viz_path)
    
    logger.info(f"演示完成! 所有结果已保存到: {args.output_dir}")
    print(f"\n所有结果已保存到: {args.output_dir}")


if __name__ == '__main__':
    main() 