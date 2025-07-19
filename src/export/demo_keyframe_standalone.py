#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
关键帧对齐器独立演示

此脚本提供了关键帧对齐功能的简单演示，完全独立于其他模块。
"""

import math
import bisect
from typing import Dict, List, Any, Optional
import copy
import matplotlib.pyplot as plt
import numpy as np


def frames_to_time(frames: int, fps: float) -> float:
    """将帧号转换为时间（秒）"""
    return frames / float(fps)


def time_to_frames(seconds: float, fps: float) -> int:
    """将时间（秒）转换为帧号"""
    return round(seconds * float(fps))


def align_to_keyframes(frame: float, keyframes: List[float], threshold: float = 3.0) -> float:
    """将指定帧对齐到最近的关键帧
    
    查找距离给定帧最近的关键帧，如果距离在阈值内则对齐到该关键帧。
    
    Args:
        frame: 需要对齐的帧号
        keyframes: 可用的关键帧列表
        threshold: 最大对齐距离阈值，超过此阈值不进行对齐
        
    Returns:
        float: 对齐后的帧号
    """
    if not keyframes:
        return frame
    
    # 如果帧值恰好是关键帧，直接返回
    if frame in keyframes:
        return frame
    
    # 找到最近的关键帧
    nearest = min(keyframes, key=lambda x: abs(x - frame))
    
    # 计算距离
    distance = abs(nearest - frame)
    
    # 如果距离在阈值内，进行对齐
    if distance <= threshold:
        print(f"帧 {frame} 对齐到关键帧 {nearest}，距离: {distance}")
        return nearest
    
    # 否则保持原值
    return frame


def find_optimal_keyframe(
    target_frame: float, 
    keyframes: List[float], 
    preference: str = 'nearest'
) -> float:
    """找到最优的关键帧进行对齐
    
    根据不同的优化策略找到最适合的关键帧。
    
    Args:
        target_frame: 目标帧
        keyframes: 可用的关键帧列表
        preference: 优先策略，可选值:
                   'nearest' - 最近的关键帧
                   'previous' - 前一个关键帧(用于剪切点)
                   'next' - 后一个关键帧(用于转场起点)
        
    Returns:
        float: 最优的关键帧位置
    """
    if not keyframes:
        return target_frame
    
    # 确保关键帧列表有序
    sorted_keyframes = sorted(keyframes)
    
    if preference == 'nearest':
        # 找到最近的关键帧
        return min(sorted_keyframes, key=lambda x: abs(x - target_frame))
    
    elif preference == 'previous':
        # 找到前一个关键帧
        idx = bisect.bisect_left(sorted_keyframes, target_frame)
        if idx > 0:
            return sorted_keyframes[idx - 1]
        return sorted_keyframes[0]  # 如果没有前一个，返回第一个
    
    elif preference == 'next':
        # 找到后一个关键帧
        idx = bisect.bisect_right(sorted_keyframes, target_frame)
        if idx < len(sorted_keyframes):
            return sorted_keyframes[idx]
        return sorted_keyframes[-1]  # 如果没有后一个，返回最后一个
    
    # 默认返回最近的关键帧
    return min(sorted_keyframes, key=lambda x: abs(x - target_frame))


def optimize_cut_points(
    cut_points: List[float], 
    keyframes: List[float], 
    min_segment_duration: float = 1.0
) -> List[float]:
    """优化剪切点，确保它们对齐到关键帧并保持最小段落时长
    
    Args:
        cut_points: 原始剪切点列表
        keyframes: 可用的关键帧列表
        min_segment_duration: 最小段落时长(秒)
        
    Returns:
        List[float]: 优化后的剪切点
    """
    if not cut_points or not keyframes:
        return cut_points
    
    # 确保列表有序
    sorted_cuts = sorted(cut_points)
    sorted_keyframes = sorted(keyframes)
    
    optimized_cuts = []
    previous_cut = 0  # 假设时间轴从0开始
    
    for cut in sorted_cuts:
        # 找到最近的关键帧
        aligned_cut = find_optimal_keyframe(cut, sorted_keyframes, preference='previous')
        
        # 确保与前一个剪切点的距离不小于最小段落时长
        if aligned_cut - previous_cut < min_segment_duration:
            # 尝试使用下一个关键帧
            next_candidate = find_optimal_keyframe(cut, sorted_keyframes, preference='next')
            if next_candidate - previous_cut >= min_segment_duration:
                aligned_cut = next_candidate
            else:
                # 如果下一个关键帧也不满足，则强制设置为最小距离
                aligned_cut = previous_cut + min_segment_duration
        
        optimized_cuts.append(aligned_cut)
        previous_cut = aligned_cut
    
    return optimized_cuts


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


def visualize_keyframes_alignment(
    original_frames: List[float],
    aligned_frames: List[float],
    keyframes: List[float],
    fps: float = 30.0,
    title: str = "关键帧对齐效果"
) -> None:
    """可视化关键帧对齐效果
    
    Args:
        original_frames: 原始帧列表
        aligned_frames: 对齐后的帧列表
        keyframes: 参考关键帧列表
        fps: 帧率
        title: 图表标题
    """
    # 转换为时间
    original_times = [frames_to_time(f, fps) for f in original_frames]
    aligned_times = [frames_to_time(f, fps) for f in aligned_frames]
    
    # 创建图表
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # 绘制关键帧
    for kf in keyframes:
        ax.axvline(x=kf, color='red', linestyle='--', alpha=0.5)
    
    # 绘制原始帧和对齐后的帧
    for i, (orig, aligned) in enumerate(zip(original_times, aligned_times)):
        # 绘制原始帧
        ax.plot([orig], [1], 'bo', markersize=8, label='原始帧' if i == 0 else None)
        
        # 绘制对齐后的帧
        ax.plot([aligned], [1.2], 'go', markersize=8, label='对齐后的帧' if i == 0 else None)
        
        # 连接线
        if orig != aligned:
            ax.plot([orig, aligned], [1, 1.2], 'k-', alpha=0.5)
    
    # 设置坐标轴和标题
    ax.set_yticks([])
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
    print("=== 关键帧对齐器演示 ===")
    
    # 生成样本数据
    fps = 30.0
    timeline = generate_sample_timeline()
    keyframes = generate_sample_keyframes(fps)
    
    # 将关键帧转换为帧号
    keyframes_frames = [time_to_frames(t, fps) for t in keyframes]
    
    print("1. 基本关键帧对齐演示")
    test_frames = [103, 201, 315, 405, 510]
    aligned_frames = []
    
    for frame in test_frames:
        aligned = align_to_keyframes(frame, keyframes_frames, threshold=5.0)
        aligned_frames.append(aligned)
        print(f"  原始帧: {frame}, 对齐到: {aligned}")
    
    # 可视化基本对齐效果
    visualize_keyframes_alignment(
        test_frames, 
        aligned_frames, 
        keyframes, 
        fps, 
        "基本关键帧对齐效果"
    )
    
    print("\n2. 最优关键帧查找演示")
    test_frame = 205
    
    previous = find_optimal_keyframe(test_frame, keyframes_frames, 'previous')
    next_kf = find_optimal_keyframe(test_frame, keyframes_frames, 'next')
    nearest = find_optimal_keyframe(test_frame, keyframes_frames, 'nearest')
    
    print(f"  对于帧 {test_frame}:")
    print(f"    前一个关键帧: {previous}")
    print(f"    后一个关键帧: {next_kf}")
    print(f"    最近的关键帧: {nearest}")
    
    # 可视化不同策略的效果
    strategy_frames = [
        find_optimal_keyframe(frame, keyframes_frames, 'nearest') 
        for frame in test_frames
    ]
    visualize_keyframes_alignment(
        test_frames, 
        strategy_frames, 
        keyframes, 
        fps, 
        "最近关键帧策略效果"
    )
    
    strategy_frames = [
        find_optimal_keyframe(frame, keyframes_frames, 'previous') 
        for frame in test_frames
    ]
    visualize_keyframes_alignment(
        test_frames, 
        strategy_frames, 
        keyframes, 
        fps, 
        "前一个关键帧策略效果"
    )
    
    print("\n3. 剪切点优化演示")
    cut_points = [103, 200, 296, 388, 478]
    print(f"  原始剪切点: {cut_points}")
    
    optimized_cuts = optimize_cut_points(cut_points, keyframes_frames, min_segment_duration=30)
    print(f"  优化后剪切点: {optimized_cuts}")
    
    # 可视化剪切点优化效果
    visualize_keyframes_alignment(
        cut_points, 
        optimized_cuts, 
        keyframes, 
        fps, 
        "剪切点优化效果"
    )


if __name__ == "__main__":
    run_demo() 
 