#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 字幕-镜头映射器演示

此脚本展示如何使用字幕-镜头映射模块将SRT字幕与视频镜头进行同步，
并可视化映射质量和结果。
"""

import os
import sys
import json
from pprint import pprint
import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, List, Any, Tuple

# 确保可以导入模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.export.text_visual_sync import (
    map_subtitle_to_shot,
    batch_map_subtitles,
    calculate_sync_score,
    generate_mapping_report,
    adjust_mapping_times,
    TextVisualSyncer,
    get_text_visual_syncer,
    sync_text_with_visuals
)
from src.utils.log_handler import get_logger

# 配置日志
logger = get_logger("demo_text_visual_sync")


def demo_single_mapping():
    """演示单条字幕与镜头的映射"""
    print("\n=== 演示单条字幕映射 ===\n")
    
    # 示例字幕
    subtitle = {"id": "sub1", "start": 3.5, "end": 5.5, "content": "你好，世界！"}
    
    # 示例镜头列表
    shots = [
        {"id": "shot1", "start": 0.0, "end": 2.0, "source": "scene1.mp4"},
        {"id": "shot2", "start": 2.0, "end": 4.0, "source": "scene2.mp4"},
        {"id": "shot3", "start": 4.0, "end": 6.0, "source": "scene3.mp4"},
        {"id": "shot4", "start": 6.0, "end": 8.0, "source": "scene4.mp4"}
    ]
    
    print("字幕信息:")
    print(f"  内容: {subtitle['content']}")
    print(f"  时间范围: {subtitle['start']} - {subtitle['end']}秒")
    
    print("\n可用镜头:")
    for shot in shots:
        print(f"  镜头 {shot['id']}: {shot['start']} - {shot['end']}秒, 来源: {shot['source']}")
    
    # 执行映射
    best_shot = map_subtitle_to_shot(subtitle, shots)
    
    # 计算同步评分
    sync_score = calculate_sync_score(subtitle, best_shot)
    
    print("\n映射结果:")
    print(f"  最佳匹配镜头: {best_shot['id']}")
    print(f"  镜头时间范围: {best_shot['start']} - {best_shot['end']}秒")
    print(f"  来源: {best_shot['source']}")
    print(f"  同步评分: {sync_score:.2f} (0-1范围, 越高越好)")
    
    # 可视化时间线
    visualize_timeline(subtitle, shots, best_shot)


def visualize_timeline(subtitle, shots, matched_shot):
    """可视化字幕和镜头时间线"""
    try:
        plt.figure(figsize=(12, 4))
        
        # 绘制所有镜头
        for i, shot in enumerate(shots):
            color = 'lightblue'
            if shot == matched_shot:
                color = 'green'  # 高亮匹配的镜头
            
            plt.barh(i+1, shot['end'] - shot['start'], left=shot['start'], 
                    height=0.5, color=color, alpha=0.7)
            plt.text(shot['start'], i+1, f"{shot['id']}", va='center')
        
        # 绘制字幕
        plt.barh(len(shots) + 1, subtitle['end'] - subtitle['start'], 
                left=subtitle['start'], height=0.5, color='red', alpha=0.6)
        plt.text(subtitle['start'], len(shots) + 1, f"字幕: {subtitle['content'][:15]}...", va='center')
        
        # 设置坐标轴
        plt.yticks(range(1, len(shots) + 2), [f"镜头 {i+1}" for i in range(len(shots))] + ["字幕"])
        plt.xlabel('时间 (秒)')
        plt.title('字幕与镜头时间线映射')
        plt.grid(axis='x', linestyle='--', alpha=0.7)
        
        # 保存图像
        plt.tight_layout()
        plt.savefig('timeline_mapping.png')
        print("\n[已生成时间线映射可视化: timeline_mapping.png]")
        
    except Exception as e:
        logger.error(f"可视化时间线时出错: {str(e)}")
        print("\n[无法生成可视化，可能缺少matplotlib库]")


def demo_batch_mapping():
    """演示批量字幕映射"""
    print("\n=== 演示批量字幕映射 ===\n")
    
    # 示例字幕列表
    subtitles = [
        {"id": "sub1", "start": 1.0, "end": 3.0, "content": "第一条字幕"},
        {"id": "sub2", "start": 3.5, "end": 5.5, "content": "第二条字幕"},
        {"id": "sub3", "start": 6.0, "end": 8.0, "content": "第三条字幕"},
        {"id": "sub4", "start": 9.0, "end": 10.0, "content": "第四条字幕"}
    ]
    
    # 示例镜头列表
    shots = [
        {"id": "shot1", "start": 0.0, "end": 2.5, "source": "scene1.mp4"},
        {"id": "shot2", "start": 2.5, "end": 4.5, "source": "scene2.mp4"},
        {"id": "shot3", "start": 4.5, "end": 7.0, "source": "scene3.mp4"},
        {"id": "shot4", "start": 7.0, "end": 10.5, "source": "scene4.mp4"}
    ]
    
    print("字幕列表:")
    for sub in subtitles:
        print(f"  {sub['id']}: {sub['start']} - {sub['end']}秒, '{sub['content']}'")
    
    print("\n镜头列表:")
    for shot in shots:
        print(f"  {shot['id']}: {shot['start']} - {shot['end']}秒, 来源: {shot['source']}")
    
    # 执行批量映射
    mappings = batch_map_subtitles(subtitles, shots)
    
    print("\n映射结果:")
    for i, (subtitle, shot) in enumerate(mappings):
        score = calculate_sync_score(subtitle, shot)
        print(f"  字幕 {subtitle['id']} → 镜头 {shot['id']}, 同步评分: {score:.2f}")
    
    # 生成映射报告
    report = generate_mapping_report(mappings)
    
    print("\n映射质量报告:")
    print(f"  总映射数: {report['total_mappings']}")
    print(f"  完美匹配数: {report['perfect_match_count']}")
    print(f"  部分匹配数: {report['partial_match_count']}")
    print(f"  低质量匹配数: {report['low_quality_match_count']}")
    print(f"  平均评分: {report['average_score']:.2f}")
    
    print("\n评分分布:")
    for category, count in report['score_distribution'].items():
        print(f"  {category}: {count}")
    
    # 可视化评分分布
    visualize_score_distribution(report)


def visualize_score_distribution(report):
    """可视化映射评分分布"""
    try:
        categories = list(report['score_distribution'].keys())
        values = list(report['score_distribution'].values())
        
        plt.figure(figsize=(8, 6))
        
        # 设置颜色映射
        colors = ['red', 'orange', 'lightgreen', 'darkgreen']
        
        plt.bar(categories, values, color=colors)
        plt.title('字幕-镜头映射质量分布')
        plt.xlabel('映射质量')
        plt.ylabel('数量')
        
        # 添加数值标签
        for i, v in enumerate(values):
            plt.text(i, v + 0.1, str(v), ha='center')
        
        # 保存图像
        plt.tight_layout()
        plt.savefig('mapping_quality.png')
        print("\n[已生成映射质量分布可视化: mapping_quality.png]")
        
    except Exception as e:
        logger.error(f"可视化评分分布时出错: {str(e)}")
        print("\n[无法生成可视化，可能缺少matplotlib库]")


def demo_adjusted_timeline():
    """演示调整后的时间线"""
    print("\n=== 演示调整后的时间线 ===\n")
    
    # 示例字幕和镜头
    subtitles = [
        {"id": "sub1", "start": 1.0, "end": 3.0, "content": "我们需要更多的资源。"},
        {"id": "sub2", "start": 4.0, "end": 6.0, "content": "我已经安排好了。"},
        {"id": "sub3", "start": 7.0, "end": 9.0, "content": "太好了！我们可以开始了。"}
    ]
    
    shots = [
        {"id": "shot1", "start": 0.5, "end": 3.5, "source": "scene1.mp4"},
        {"id": "shot2", "start": 3.5, "end": 6.5, "source": "scene2.mp4"},
        {"id": "shot3", "start": 6.5, "end": 9.5, "source": "scene3.mp4"}
    ]
    
    # 执行映射和调整
    mappings = batch_map_subtitles(subtitles, shots)
    adjusted_clips = adjust_mapping_times(mappings)
    
    print("原始镜头:")
    for shot in shots:
        print(f"  {shot['id']}: {shot['start']} - {shot['end']}秒")
    
    print("\n字幕时间:")
    for sub in subtitles:
        print(f"  {sub['id']}: {sub['start']} - {sub['end']}秒, '{sub['content']}'")
    
    print("\n调整后的片段:")
    for clip in adjusted_clips:
        print(f"  片段(来源:{clip['id']}): {clip['start']} - {clip['end']}秒")
        print(f"    字幕: '{clip['subtitle']}'")
    
    # 可视化调整前后对比
    visualize_adjustment(shots, subtitles, adjusted_clips)


def visualize_adjustment(shots, subtitles, adjusted_clips):
    """可视化调整前后的对比"""
    try:
        plt.figure(figsize=(12, 6))
        
        # 上半部分：原始镜头和字幕
        for i, shot in enumerate(shots):
            plt.subplot(2, 1, 1)
            plt.barh(i+1, shot['end'] - shot['start'], left=shot['start'], 
                    height=0.5, color='lightblue', alpha=0.7)
            plt.text(shot['start'], i+1, f"{shot['id']}", va='center')
        
        # 添加字幕位置
        for i, sub in enumerate(subtitles):
            plt.subplot(2, 1, 1)
            plt.barh(len(shots) + i + 1, sub['end'] - sub['start'], 
                    left=sub['start'], height=0.5, color='red', alpha=0.6)
            plt.text(sub['start'], len(shots) + i + 1, f"{sub['id']}", va='center')
        
        plt.title('调整前: 原始镜头和字幕')
        plt.grid(axis='x', linestyle='--', alpha=0.5)
        plt.yticks(range(1, len(shots) + len(subtitles) + 1), 
                  [f"镜头 {i+1}" for i in range(len(shots))] + 
                  [f"字幕 {i+1}" for i in range(len(subtitles))])
        
        # 下半部分：调整后的片段
        plt.subplot(2, 1, 2)
        for i, clip in enumerate(adjusted_clips):
            plt.barh(i+1, clip['end'] - clip['start'], left=clip['start'], 
                    height=0.5, color='green', alpha=0.7)
            plt.text(clip['start'], i+1, f"片段 {i+1}", va='center')
        
        plt.title('调整后: 基于字幕的片段')
        plt.xlabel('时间 (秒)')
        plt.grid(axis='x', linestyle='--', alpha=0.5)
        plt.yticks(range(1, len(adjusted_clips) + 1), [f"片段 {i+1}" for i in range(len(adjusted_clips))])
        
        # 保存图像
        plt.tight_layout()
        plt.savefig('timeline_adjustment.png')
        print("\n[已生成时间线调整对比可视化: timeline_adjustment.png]")
        
    except Exception as e:
        logger.error(f"可视化调整对比时出错: {str(e)}")
        print("\n[无法生成可视化，可能缺少matplotlib库]")


def demo_syncer_class():
    """演示TextVisualSyncer类"""
    print("\n=== 演示TextVisualSyncer类 ===\n")
    
    # 较复杂的示例数据
    subtitles = [
        {"id": "sub1", "start": 1.0, "end": 3.0, "content": "今天天气真好。"},
        {"id": "sub2", "start": 3.5, "end": 5.5, "content": "是啊，非常适合出去走走。"},
        {"id": "sub3", "start": 6.0, "end": 8.0, "content": "我们去公园怎么样？"},
        {"id": "sub4", "start": 8.5, "end": 10.5, "content": "好主意，我们现在就出发。"},
        {"id": "sub5", "start": 11.0, "end": 15.0, "content": "这里的风景真美，我很喜欢这里的环境。"}
    ]
    
    shots = [
        {"id": "shot1", "start": 0.0, "end": 2.0, "source": "outdoor1.mp4"},
        {"id": "shot2", "start": 2.0, "end": 4.0, "source": "outdoor2.mp4"},
        {"id": "shot3", "start": 4.0, "end": 6.0, "source": "conversation1.mp4"},
        {"id": "shot4", "start": 6.0, "end": 9.0, "source": "conversation2.mp4"},
        {"id": "shot5", "start": 9.0, "end": 12.0, "source": "walking.mp4"},
        {"id": "shot6", "start": 12.0, "end": 16.0, "source": "park_scene.mp4"}
    ]
    
    print(f"输入: {len(subtitles)}条字幕和{len(shots)}个镜头")
    
    # 获取同步处理器实例
    syncer = get_text_visual_syncer()
    
    # 执行处理
    result = syncer.process(subtitles, shots)
    
    print("\n处理结果摘要:")
    print(f"  映射数量: {len(result['mappings'])}")
    print(f"  调整后片段数量: {len(result['adjusted_clips'])}")
    
    print("\n映射质量报告:")
    report = result['report']
    print(f"  平均同步评分: {report['average_score']:.2f}")
    print(f"  完美匹配数: {report['perfect_match_count']}")
    print(f"  部分匹配数: {report['partial_match_count']}")
    print(f"  低质量匹配数: {report['low_quality_match_count']}")
    
    print("\n调整后的片段示例:")
    for i, clip in enumerate(result['adjusted_clips'][:3]):  # 只显示前3个
        print(f"  片段 {i+1}: {clip['start']}s - {clip['end']}s, 来源: {clip['id']}")
        print(f"    字幕: '{clip['subtitle']}'")
    
    if len(result['adjusted_clips']) > 3:
        print(f"  ... 以及 {len(result['adjusted_clips']) - 3} 个更多片段")


def main():
    """主函数"""
    print("=== VisionAI-ClipsMaster 字幕-镜头映射器演示 ===")
    
    # 演示各种功能
    demo_single_mapping()
    demo_batch_mapping()
    demo_adjusted_timeline()
    demo_syncer_class()
    
    print("\n=== 演示完成 ===")
    print("本演示展示了如何使用字幕-镜头映射器将字幕与视频内容同步，生成混剪片段。")
    print("映射器会尝试找到最佳匹配的视频片段，确保字幕与视觉内容保持一致。")
    print("在实际应用中，这将确保最终混剪视频的视听连贯性。")


if __name__ == "__main__":
    main() 