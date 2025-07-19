#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
关键帧对齐器演示

此脚本演示了关键帧对齐器的使用方法和效果。
"""

import os
import sys
import json
import argparse
from typing import Dict, List, Any
import matplotlib.pyplot as plt
import numpy as np

# 确保可以导入模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.export.keyframe_aligner import (
    align_to_keyframes,
    find_optimal_keyframe,
    optimize_cut_points,
    extract_keyframes_from_timeline,
    synchronize_keyframes_across_tracks,
    KeyframeAligner
)
from src.export.fps_converter import time_to_frames, frames_to_time
from src.utils.log_handler import get_logger

# 配置日志
logger = get_logger("demo_keyframe_aligner")


def generate_sample_timeline() -> Dict[str, Any]:
    """生成用于演示的样本时间轴数据"""
    timeline = {
        'fps': 30.0,
        'clips': [
            {'id': 'clip1', 'start_frame': 101, 'end_frame': 152, 'content': '场景1'},
            {'id': 'clip2', 'start_frame': 201, 'end_frame': 248, 'content': '场景2'},
            {'id': 'clip3', 'start_frame': 301, 'end_frame': 359, 'content': '场景3'},
            {'id': 'clip4', 'start_frame': 402, 'end_frame': 448, 'content': '场景4'},
            {'id': 'clip5', 'start_frame': 502, 'end_frame': 549, 'content': '场景5'},
        ],
        'tracks': [
            {
                'id': 'video_track',
                'type': 'video',
                'items': [
                    {'id': 'v1', 'start_frame': 101, 'end_frame': 152, 'clip_id': 'clip1'},
                    {'id': 'v2', 'start_frame': 201, 'end_frame': 248, 'clip_id': 'clip2'},
                    {'id': 'v3', 'start_frame': 301, 'end_frame': 359, 'clip_id': 'clip3'},
                    {'id': 'v4', 'start_frame': 402, 'end_frame': 448, 'clip_id': 'clip4'},
                    {'id': 'v5', 'start_frame': 502, 'end_frame': 549, 'clip_id': 'clip5'},
                ]
            },
            {
                'id': 'audio_track',
                'type': 'audio',
                'items': [
                    {'id': 'a1', 'start_frame': 101, 'end_frame': 152, 'clip_id': 'clip1'},
                    {'id': 'a2', 'start_frame': 201, 'end_frame': 248, 'clip_id': 'clip2'},
                    {'id': 'a3', 'start_frame': 301, 'end_frame': 359, 'clip_id': 'clip3'},
                    {'id': 'a4', 'start_frame': 402, 'end_frame': 448, 'clip_id': 'clip4'},
                    {'id': 'a5', 'start_frame': 501, 'end_frame': 548, 'clip_id': 'clip5'}, # 注意：这里故意偏移1帧
                ]
            }
        ]
    }
    return timeline


def generate_sample_keyframes(fps: float = 30.0, duration: float = 20.0) -> List[float]:
    """生成样本视频的关键帧数据
    
    Args:
        fps: 帧率
        duration: 视频时长(秒)
        
    Returns:
        List[float]: 关键帧时间点列表(秒)
    """
    # 模拟场景切换点等处的关键帧
    keyframes = [
        # 场景1的关键点 (3.33秒左右)
        3.33, 3.5, 4.0, 4.5, 5.0,
        
        # 场景2的关键点 (6.67秒左右)
        6.67, 7.0, 7.5, 8.0, 8.33,
        
        # 场景3的关键点 (10秒左右)
        10.0, 10.5, 11.0, 11.5, 12.0,
        
        # 场景4的关键点 (13.33秒左右)
        13.33, 13.67, 14.0, 14.5, 15.0,
        
        # 场景5的关键点 (16.67秒左右)
        16.67, 17.0, 17.5, 18.0, 18.33
    ]
    return keyframes


def visualize_timeline(
    timeline: Dict[str, Any], 
    keyframes: List[float] = None,
    optimized_timeline: Dict[str, Any] = None,
    title: str = "时间轴可视化"
) -> None:
    """可视化时间轴和关键帧
    
    绘制时间轴上的片段和关键帧位置。
    
    Args:
        timeline: 时间轴数据
        keyframes: 关键帧列表(秒)
        optimized_timeline: 优化后的时间轴数据(可选)
        title: 图表标题
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        logger.error("需要安装matplotlib库来运行此演示")
        return
    
    fps = timeline.get('fps', 30.0)
    
    # 创建图表
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # 绘制原始时间轴
    y_pos = 0
    colors = ['royalblue', 'lightblue', 'cornflowerblue', 'steelblue', 'mediumblue']
    
    if 'clips' in timeline:
        for i, clip in enumerate(timeline['clips']):
            start_time = frames_to_time(clip['start_frame'], fps)
            end_time = frames_to_time(clip['end_frame'], fps)
            duration = end_time - start_time
            color_idx = i % len(colors)
            
            # 绘制片段
            ax.barh(
                y_pos, 
                duration, 
                left=start_time, 
                height=0.8, 
                color=colors[color_idx], 
                alpha=0.6,
                label=f"Clip {i+1}" if i == 0 else None
            )
            
            # 添加标签
            ax.text(
                start_time + duration/2, 
                y_pos, 
                f"{clip.get('content', f'片段{i+1}')}",
                ha='center', 
                va='center',
                color='black', 
                fontweight='bold'
            )
            
            # 标记起点和终点
            ax.plot([start_time, start_time], [y_pos-0.4, y_pos+0.4], 'k-', lw=1)
            ax.plot([end_time, end_time], [y_pos-0.4, y_pos+0.4], 'k-', lw=1)
    
    # 如果提供了优化后的时间轴，绘制它
    if optimized_timeline:
        y_pos = 1
        if 'clips' in optimized_timeline:
            for i, clip in enumerate(optimized_timeline['clips']):
                start_time = frames_to_time(clip['start_frame'], fps)
                end_time = frames_to_time(clip['end_frame'], fps)
                duration = end_time - start_time
                color_idx = i % len(colors)
                
                # 绘制优化后的片段
                ax.barh(
                    y_pos, 
                    duration, 
                    left=start_time, 
                    height=0.8, 
                    color=colors[color_idx], 
                    alpha=0.9,
                    label=f"优化后 Clip {i+1}" if i == 0 else None
                )
                
                # 添加标签
                ax.text(
                    start_time + duration/2, 
                    y_pos, 
                    f"{clip.get('content', f'片段{i+1}')} (优化后)",
                    ha='center', 
                    va='center', 
                    color='black', 
                    fontweight='bold'
                )
    
    # 绘制关键帧
    if keyframes:
        for kf in keyframes:
            ax.axvline(x=kf, color='red', linestyle='--', alpha=0.5)
    
    # 设置坐标轴和标题
    ax.set_yticks([0, 1])
    ax.set_yticklabels(['原始时间轴', '优化后时间轴'])
    ax.set_xlabel('时间 (秒)')
    ax.set_title(title)
    
    # 添加图例
    ax.legend(loc='upper right')
    
    # 显示网格
    ax.grid(True, alpha=0.3)
    
    # 显示图表
    plt.tight_layout()
    plt.show()


def run_demo() -> None:
    """运行关键帧对齐器演示"""
    logger.info("=== 关键帧对齐器演示 ===")
    
    # 生成样本数据
    timeline = generate_sample_timeline()
    fps = timeline.get('fps', 30.0)
    keyframes = generate_sample_keyframes(fps)
    
    # 将关键帧转换为帧号，用于演示
    keyframes_frames = [time_to_frames(t, fps) for t in keyframes]
    
    logger.info("1. 基本关键帧对齐演示")
    test_frames = [103, 201, 315, 405, 510]
    
    for frame in test_frames:
        aligned = align_to_keyframes(frame, keyframes_frames, threshold=5.0)
        logger.info(f"  原始帧: {frame}, 对齐到: {aligned}")
    
    logger.info("\n2. 最优关键帧查找演示")
    test_frame = 205
    
    previous = find_optimal_keyframe(test_frame, keyframes_frames, 'previous')
    next_kf = find_optimal_keyframe(test_frame, keyframes_frames, 'next')
    nearest = find_optimal_keyframe(test_frame, keyframes_frames, 'nearest')
    
    logger.info(f"  对于帧 {test_frame}:")
    logger.info(f"    前一个关键帧: {previous}")
    logger.info(f"    后一个关键帧: {next_kf}")
    logger.info(f"    最近的关键帧: {nearest}")
    
    logger.info("\n3. 使用KeyframeAligner类优化整个时间轴")
    
    # 创建关键帧对齐器
    aligner = KeyframeAligner(default_fps=fps)
    
    # 准备视频信息
    video_info = {
        'fps': fps,
        'duration': 20.0,
        'keyframes': keyframes
    }
    
    # 优化时间轴
    optimized_timeline = aligner.optimize_timeline_keyframes(
        timeline, 
        video_info,
        strictness='medium'
    )
    
    # 分析时间轴对齐情况
    report = aligner.analyze_keyframe_alignment(timeline, keyframes)
    
    logger.info("\n4. 关键帧对齐分析报告")
    logger.info(f"  总剪切点数量: {report['total_cut_points']}")
    logger.info(f"  已对齐的剪切点: {report['aligned_cuts']}")
    logger.info(f"  未对齐的剪切点: {report['non_aligned_cuts']}")
    logger.info(f"  对齐率: {report['alignment_rate']:.2%}")
    logger.info(f"  平均错位距离: {report['avg_misalignment']:.4f}秒")
    
    if report['misaligned_cuts']:
        logger.info("\n  最严重的错位剪切点:")
        for i, misaligned in enumerate(report['misaligned_cuts'][:3]):
            logger.info(
                f"    #{i+1}: 剪切点 {misaligned['cut_point']:.2f}秒, "
                f"最近关键帧 {misaligned['nearest_keyframe']:.2f}秒, "
                f"距离 {misaligned['distance']:.4f}秒"
            )
    
    # 优化后的分析
    optimized_report = aligner.analyze_keyframe_alignment(optimized_timeline, keyframes)
    
    logger.info("\n5. 优化后的关键帧对齐分析")
    logger.info(f"  对齐率: {report['alignment_rate']:.2%} -> {optimized_report['alignment_rate']:.2%}")
    logger.info(f"  未对齐剪切点: {report['non_aligned_cuts']} -> {optimized_report['non_aligned_cuts']}")
    logger.info(f"  平均错位距离: {report['avg_misalignment']:.4f}秒 -> {optimized_report['avg_misalignment']:.4f}秒")
    
    # 可视化结果
    logger.info("\n6. 可视化时间轴和关键帧")
    visualize_timeline(timeline, keyframes, optimized_timeline, "关键帧对齐优化演示")


if __name__ == "__main__":
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="关键帧对齐器演示")
    parser.add_argument("--no-plot", action="store_true", help="禁用绘图功能")
    args = parser.parse_args()
    
    # 如果指定了--no-plot参数，禁用绘图功能
    if args.no_plot:
        # 替换visualize_timeline函数为空函数
        def visualize_timeline(*args, **kwargs):
            logger.info("已禁用绘图功能")
    
    # 运行演示
    run_demo() 