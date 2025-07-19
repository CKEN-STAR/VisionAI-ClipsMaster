#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
跨平台时间基准处理演示

此脚本演示了跨平台时间基准处理的功能和效果。
"""

import os
import sys
import json
import argparse
from typing import Dict, List, Any, Optional
import matplotlib.pyplot as plt
import numpy as np

# 确保可以导入模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.export.timebase_unifier import (
    convert_timebase,
    normalize_timecode,
    detect_platform,
    get_platform_timebase,
    get_timebase_fps,
    adjust_for_platform_precision,
    unify_timeline_timebase,
    compensate_timeline_boundaries,
    convert_timing_values,
    detect_and_fix_timebase_issues,
    TimebaseStandard,
    PlatformType
)
from src.utils.log_handler import get_logger

# 配置日志
logger = get_logger("demo_timebase_unifier")


def generate_sample_timeline() -> Dict[str, Any]:
    """生成演示用的示例时间轴"""
    timeline = {
        'fps': 24.0,
        'duration': 10.0,
        'source_platform': PlatformType.WINDOWS.value,
        'clips': [
            {
                'id': 'clip1',
                'start_frame': 24,
                'end_frame': 72,
                'start_time': 1.0,
                'end_time': 3.0,
                'content': '场景1'
            },
            {
                'id': 'clip2',
                'start_frame': 96,
                'end_frame': 144,
                'start_time': 4.0,
                'end_time': 6.0,
                'content': '场景2'
            },
            {
                'id': 'clip3',
                'start_frame': 168,
                'end_frame': 216,
                'start_time': 7.0,
                'end_time': 9.0,
                'content': '场景3'
            }
        ],
        'tracks': [
            {
                'id': 'video_track',
                'type': 'video',
                'items': [
                    {
                        'id': 'v1',
                        'start_frame': 24,
                        'end_frame': 72,
                        'start_time': 1.0,
                        'end_time': 3.0,
                        'clip_id': 'clip1'
                    },
                    {
                        'id': 'v2',
                        'start_frame': 96,
                        'end_frame': 144,
                        'start_time': 4.0,
                        'end_time': 6.0,
                        'clip_id': 'clip2'
                    },
                    {
                        'id': 'v3',
                        'start_frame': 168,
                        'end_frame': 216,
                        'start_time': 7.0,
                        'end_time': 9.0,
                        'clip_id': 'clip3'
                    }
                ]
            },
            {
                'id': 'audio_track',
                'type': 'audio',
                'items': [
                    {
                        'id': 'a1',
                        'start_frame': 24,
                        'end_frame': 72,
                        'start_time': 1.0,
                        'end_time': 3.0,
                        'clip_id': 'clip1'
                    },
                    {
                        'id': 'a2',
                        'start_frame': 96,
                        'end_frame': 144,
                        'start_time': 4.0,
                        'end_time': 6.0,
                        'clip_id': 'clip2'
                    },
                    {
                        'id': 'a3',
                        'start_frame': 168,
                        'end_frame': 216,
                        'start_time': 7.0,
                        'end_time': 9.0,
                        'clip_id': 'clip3'
                    }
                ]
            }
        ]
    }
    return timeline


def generate_broken_timeline() -> Dict[str, Any]:
    """生成具有问题的时间轴数据，用于演示修复功能"""
    broken_timeline = {
        'fps': 24.0,
        'duration': -1.0,  # 负时长
        'clips': [
            {
                'id': 'clip1',
                'start_frame': 72,  # 故意颠倒起止时间
                'end_frame': 24,
                'start_time': 3.0,
                'end_time': 1.0,
                'content': '场景1'
            },
            {
                'id': 'clip2',
                'start_frame': 96,
                'end_frame': 96,  # 零时长剪辑
                'start_time': 4.0,
                'end_time': 4.0,
                'content': '场景2'
            },
            {
                'id': 'clip3',
                'start_frame': 168,
                'end_frame': 216,
                'start_time': 7.0,
                'end_time': 9.0,
                'content': '场景3'
            }
        ],
        'tracks': [
            {
                'id': 'video_track',
                'type': 'video',
                'items': [
                    {
                        'id': 'v1',
                        'start_frame': 72,  # 故意颠倒起止时间
                        'end_frame': 24,
                        'start_time': 3.0,
                        'end_time': 1.0,
                        'clip_id': 'clip1'
                    }
                ]
            }
        ]
    }
    return broken_timeline


def visualize_timeline_conversion(
    original: Dict[str, Any],
    converted: Dict[str, Any],
    title: str = "时间轴转换比较"
) -> None:
    """可视化时间轴转换前后的对比
    
    Args:
        original: 原始时间轴
        converted: 转换后的时间轴
        title: 图表标题
    """
    # 创建图表
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
    
    # 原始时间轴帧率
    orig_fps = original.get('fps', 24.0)
    # 转换后时间轴帧率
    conv_fps = converted.get('fps', 25.0)
    
    # 绘制原始时间轴
    ax1.set_title(f"原始时间轴 ({orig_fps} fps)")
    y_pos = 0
    colors = ['royalblue', 'lightblue', 'cornflowerblue']
    
    if 'clips' in original and isinstance(original['clips'], list):
        for i, clip in enumerate(original['clips']):
            start_time = clip.get('start_time', clip.get('start_frame', 0) / orig_fps)
            end_time = clip.get('end_time', clip.get('end_frame', 0) / orig_fps)
            duration = end_time - start_time
            color_idx = i % len(colors)
            
            # 绘制片段
            ax1.barh(
                y_pos, 
                duration, 
                left=start_time, 
                height=0.6, 
                color=colors[color_idx], 
                alpha=0.7
            )
            
            # 添加标签
            ax1.text(
                start_time + duration/2, 
                y_pos, 
                f"{clip.get('content', f'片段{i+1}')} ({clip.get('start_frame')}-{clip.get('end_frame')})",
                ha='center', 
                va='center',
                color='black', 
                fontweight='bold',
                fontsize=9
            )
    
    # 绘制转换后的时间轴
    ax2.set_title(f"转换后时间轴 ({conv_fps} fps)")
    
    if 'clips' in converted and isinstance(converted['clips'], list):
        for i, clip in enumerate(converted['clips']):
            start_time = clip.get('start_time', clip.get('start_frame', 0) / conv_fps)
            end_time = clip.get('end_time', clip.get('end_frame', 0) / conv_fps)
            duration = end_time - start_time
            color_idx = i % len(colors)
            
            # 绘制片段
            ax2.barh(
                y_pos, 
                duration, 
                left=start_time, 
                height=0.6, 
                color=colors[color_idx], 
                alpha=0.7
            )
            
            # 添加标签
            ax2.text(
                start_time + duration/2, 
                y_pos, 
                f"{clip.get('content', f'片段{i+1}')} ({clip.get('start_frame')}-{clip.get('end_frame')})",
                ha='center', 
                va='center',
                color='black', 
                fontweight='bold',
                fontsize=9
            )
    
    # 设置坐标轴
    ax1.set_yticks([])
    ax2.set_yticks([])
    ax2.set_xlabel('时间 (秒)')
    
    # 显示网格
    ax1.grid(True, alpha=0.3)
    ax2.grid(True, alpha=0.3)
    
    # 设置总标题
    fig.suptitle(title, fontsize=14)
    
    # 调整布局
    plt.tight_layout()
    plt.subplots_adjust(top=0.9)
    
    # 显示图表
    plt.show()


def visualize_timecode_comparison(
    src_timebase: TimebaseStandard,
    dst_timebase: TimebaseStandard,
    timecodes: List[str] = None
) -> None:
    """可视化不同时间基准下的时间码转换
    
    Args:
        src_timebase: 源时间基准
        dst_timebase: 目标时间基准
        timecodes: 要转换的时间码列表，如果为None则使用默认值
    """
    if timecodes is None:
        timecodes = ["00:00:10:00", "00:00:30:00", "00:01:00:00", "00:02:00:00"]
    
    # 获取帧率
    src_fps = get_timebase_fps(src_timebase)
    dst_fps = get_timebase_fps(dst_timebase)
    
    # 创建图表
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # 转换时间码
    converted_timecodes = []
    for tc in timecodes:
        converted = normalize_timecode(tc, src_timebase, dst_timebase)
        converted_timecodes.append(converted)
    
    # 设置数据
    y_pos = np.arange(len(timecodes))
    width = 0.35
    
    # 将时间码转换为秒数进行比较
    from src.export.fps_converter import timecode_to_frames, frames_to_time
    
    original_seconds = []
    converted_seconds = []
    
    for tc in timecodes:
        frames = timecode_to_frames(tc, src_fps)
        original_seconds.append(frames_to_time(frames, src_fps))
    
    for tc in converted_timecodes:
        frames = timecode_to_frames(tc, dst_fps)
        converted_seconds.append(frames_to_time(frames, dst_fps))
    
    # 绘制条形图
    ax.barh(y_pos - width/2, original_seconds, width, label=f'{src_timebase.value} ({src_fps} fps)')
    ax.barh(y_pos + width/2, converted_seconds, width, label=f'{dst_timebase.value} ({dst_fps} fps)')
    
    # 添加标签
    for i, (orig, conv) in enumerate(zip(timecodes, converted_timecodes)):
        ax.text(original_seconds[i] + 0.1, i - width/2, orig, va='center')
        ax.text(converted_seconds[i] + 0.1, i + width/2, conv, va='center')
    
    # 设置图表属性
    ax.set_yticks(y_pos)
    ax.set_yticklabels([f"样例 {i+1}" for i in range(len(timecodes))])
    ax.set_xlabel('时间 (秒)')
    ax.set_title(f'时间码转换: {src_timebase.value} → {dst_timebase.value}')
    ax.legend()
    
    # 显示网格
    ax.grid(True, alpha=0.3)
    
    # 显示图表
    plt.tight_layout()
    plt.show()


def visualize_platform_precision(
    src_platform: PlatformType,
    dst_platform: PlatformType,
    time_values: List[float] = None
) -> None:
    """可视化平台间精度差异
    
    Args:
        src_platform: 源平台
        dst_platform: 目标平台
        time_values: 要调整的时间值列表，如果为None则使用默认值
    """
    if time_values is None:
        time_values = [1.123456789, 2.987654321, 3.333333333, 5.555555555]
    
    # 创建图表
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # 调整时间值
    adjusted_values = []
    for tv in time_values:
        adjusted = adjust_for_platform_precision(tv, src_platform, dst_platform)
        adjusted_values.append(adjusted)
    
    # 设置数据
    y_pos = np.arange(len(time_values))
    width = 0.35
    
    # 绘制条形图
    bar1 = ax.barh(y_pos - width/2, time_values, width, label=f'{src_platform.value}平台')
    bar2 = ax.barh(y_pos + width/2, adjusted_values, width, label=f'{dst_platform.value}平台')
    
    # 添加精度差异标签
    for i, (orig, adj) in enumerate(zip(time_values, adjusted_values)):
        diff = adj - orig
        if abs(diff) > 0.00001:  # 忽略极小差异
            diff_percent = (diff / orig) * 100
            ax.text(max(orig, adj) + 0.01, i, f"Δ = {diff:.6f} ({diff_percent:.2f}%)", va='center')
            
        # 在条形上显示精确值
        ax.text(orig / 2, i - width/2, f"{orig:.6f}", ha='center', va='center', color='white')
        ax.text(adj / 2, i + width/2, f"{adj:.6f}", ha='center', va='center', color='white')
    
    # 设置图表属性
    ax.set_yticks(y_pos)
    ax.set_yticklabels([f"时间值 {i+1}" for i in range(len(time_values))])
    ax.set_xlabel('时间 (秒)')
    ax.set_title(f'平台精度适配: {src_platform.value} → {dst_platform.value}')
    ax.legend()
    
    # 显示网格
    ax.grid(True, alpha=0.3)
    
    # 显示图表
    plt.tight_layout()
    plt.show()


def visualize_timebase_issues(
    original: Dict[str, Any],
    fixed: Dict[str, Any],
    logs: List[str]
) -> None:
    """可视化时间基准问题修复
    
    Args:
        original: 原始时间轴（有问题）
        fixed: 修复后的时间轴
        logs: 修复日志
    """
    # 创建图表
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
    
    # 获取帧率
    fps = original.get('fps', 24.0)
    
    # 绘制原始时间轴
    ax1.set_title("有问题的时间轴")
    y_pos = 0
    colors = ['red', 'orange', 'yellow']
    
    if 'clips' in original and isinstance(original['clips'], list):
        for i, clip in enumerate(original['clips']):
            try:
                start_time = clip.get('start_time', clip.get('start_frame', 0) / fps)
                end_time = clip.get('end_time', clip.get('end_frame', 0) / fps)
                duration = end_time - start_time
                color_idx = i % len(colors)
                
                # 绘制片段
                ax1.barh(
                    y_pos, 
                    duration, 
                    left=start_time, 
                    height=0.6, 
                    color=colors[color_idx], 
                    alpha=0.7
                )
                
                # 添加标签
                ax1.text(
                    start_time + duration/2, 
                    y_pos, 
                    f"{clip.get('content', f'片段{i+1}')} ({clip.get('start_frame')}-{clip.get('end_frame')})",
                    ha='center', 
                    va='center',
                    color='black', 
                    fontweight='bold',
                    fontsize=9
                )
            except Exception as e:
                # 处理异常，如负时长等
                ax1.text(
                    5, 
                    y_pos, 
                    f"片段 {i+1} 数据异常: {e}",
                    ha='center', 
                    va='center',
                    color='red'
                )
    
    # 绘制修复后的时间轴
    ax2.set_title("修复后的时间轴")
    
    if 'clips' in fixed and isinstance(fixed['clips'], list):
        for i, clip in enumerate(fixed['clips']):
            start_time = clip.get('start_time', clip.get('start_frame', 0) / fps)
            end_time = clip.get('end_time', clip.get('end_frame', 0) / fps)
            duration = end_time - start_time
            color_idx = i % len(colors)
            
            # 绘制片段
            ax2.barh(
                y_pos, 
                duration, 
                left=start_time, 
                height=0.6, 
                color='green', 
                alpha=0.7
            )
            
            # 添加标签
            ax2.text(
                start_time + duration/2, 
                y_pos, 
                f"{clip.get('content', f'片段{i+1}')} ({clip.get('start_frame')}-{clip.get('end_frame')})",
                ha='center', 
                va='center',
                color='black', 
                fontweight='bold',
                fontsize=9
            )
    
    # 设置坐标轴
    ax1.set_yticks([])
    ax2.set_yticks([])
    ax2.set_xlabel('时间 (秒)')
    
    # 在图表中添加修复日志
    log_text = "\n".join(logs)
    fig.text(0.5, 0.01, f"修复日志:\n{log_text}", ha='center', va='bottom', fontsize=10, bbox=dict(facecolor='yellow', alpha=0.2))
    
    # 显示网格
    ax1.grid(True, alpha=0.3)
    ax2.grid(True, alpha=0.3)
    
    # 设置总标题
    fig.suptitle("时间基准问题检测与修复", fontsize=14)
    
    # 调整布局
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.2)
    
    # 显示图表
    plt.show()


def run_demo() -> None:
    """运行跨平台时间基准处理演示"""
    logger.info("=== 跨平台时间基准处理演示 ===")
    
    # 检测当前平台
    current_platform = detect_platform()
    current_timebase, current_fps = get_platform_timebase(current_platform)
    
    logger.info(f"1. 当前平台信息:")
    logger.info(f"  平台类型: {current_platform.value}")
    logger.info(f"  默认时间基准: {current_timebase.value}")
    logger.info(f"  默认帧率: {current_fps}")
    
    # 演示时间基准转换
    logger.info("\n2. 时间基准转换示例:")
    
    conversions = [
        (24.0, 30.0),  # 电影到数字
        (25.0, 29.97),  # PAL到NTSC
        (29.97, 24.0),  # NTSC到电影
        (60.0, 25.0),  # 高帧率到PAL
    ]
    
    for src_fps, dst_fps in conversions:
        result = convert_timebase(1.0, 2.0, src_fps, dst_fps)
        logger.info(f"  {src_fps}fps到{dst_fps}fps的转换:")
        logger.info(f"    1.0秒 -> {result['start']}秒")
        logger.info(f"    2.0秒 -> {result['end']}秒")
    
    # 演示时间码标准化
    logger.info("\n3. 时间码标准化示例:")
    
    timecode_tests = [
        ("00:00:10:00", TimebaseStandard.MOVIE, TimebaseStandard.PAL),
        ("00:01:00:00", TimebaseStandard.NTSC, TimebaseStandard.MOVIE),
        ("00:02:00:00", TimebaseStandard.PAL, TimebaseStandard.DIGITAL)
    ]
    
    for tc, src_tb, dst_tb in timecode_tests:
        normalized = normalize_timecode(tc, src_tb, dst_tb)
        src_fps = get_timebase_fps(src_tb)
        dst_fps = get_timebase_fps(dst_tb)
        logger.info(f"  {src_tb.value}({src_fps}fps)到{dst_tb.value}({dst_fps}fps)的时间码转换:")
        logger.info(f"    {tc} -> {normalized}")
    
    # 演示平台精度适配
    logger.info("\n4. 平台精度适配示例:")
    
    precision_tests = [
        (1.123456789, PlatformType.WINDOWS, PlatformType.MACOS),
        (2.987654321, PlatformType.MACOS, PlatformType.LINUX),
        (3.333333333, PlatformType.LINUX, PlatformType.IOS)
    ]
    
    for time_val, src_plat, dst_plat in precision_tests:
        adjusted = adjust_for_platform_precision(time_val, src_plat, dst_plat)
        logger.info(f"  {src_plat.value}到{dst_plat.value}的精度适配:")
        logger.info(f"    {time_val} -> {adjusted}")
        logger.info(f"    差异: {adjusted - time_val}")
    
    # 演示时间轴统一
    logger.info("\n5. 时间轴时间基准统一示例:")
    
    # 生成样本时间轴
    sample_timeline = generate_sample_timeline()
    
    # 转换到不同时间基准
    conversions = [
        (TimebaseStandard.PAL, "PAL标准(25fps)"),
        (TimebaseStandard.NTSC, "NTSC标准(29.97fps)"),
        (TimebaseStandard.DIGITAL, "数字标准(30fps)")
    ]
    
    for target_tb, desc in conversions:
        unified = unify_timeline_timebase(sample_timeline, target_tb)
        logger.info(f"  转换到{desc}:")
        logger.info(f"    原始帧率: {sample_timeline['fps']}fps -> 目标帧率: {unified['fps']}fps")
        logger.info(f"    第一个片段起止帧: {sample_timeline['clips'][0]['start_frame']}-{sample_timeline['clips'][0]['end_frame']} -> {unified['clips'][0]['start_frame']}-{unified['clips'][0]['end_frame']}")
    
    # 演示时间基准问题检测与修复
    logger.info("\n6. 时间基准问题检测与修复示例:")
    
    # 生成有问题的时间轴
    broken_timeline = generate_broken_timeline()
    
    # 检测和修复问题
    fixed_timeline, logs = detect_and_fix_timebase_issues(broken_timeline)
    
    logger.info("  检测到的问题:")
    for log in logs:
        logger.info(f"    - {log}")
    
    logger.info("  修复结果:")
    logger.info(f"    第一个片段起止帧: {broken_timeline['clips'][0]['start_frame']}-{broken_timeline['clips'][0]['end_frame']} -> {fixed_timeline['clips'][0]['start_frame']}-{fixed_timeline['clips'][0]['end_frame']}")
    logger.info(f"    第二个片段起止帧: {broken_timeline['clips'][1]['start_frame']}-{broken_timeline['clips'][1]['end_frame']} -> {fixed_timeline['clips'][1]['start_frame']}-{fixed_timeline['clips'][1]['end_frame']}")
    
    # 可视化演示 (如果未禁用)
    if not args.no_plot:
        logger.info("\n7. 可视化演示:")
        
        # 可视化时间轴转换
        logger.info("  显示时间轴转换可视化...")
        unified_pal = unify_timeline_timebase(sample_timeline, TimebaseStandard.PAL)
        visualize_timeline_conversion(sample_timeline, unified_pal, "24fps到25fps(PAL)的时间轴转换")
        
        # 可视化时间码比较
        logger.info("  显示时间码标准化可视化...")
        visualize_timecode_comparison(TimebaseStandard.MOVIE, TimebaseStandard.PAL)
        
        # 可视化平台精度
        logger.info("  显示平台精度适配可视化...")
        visualize_platform_precision(PlatformType.WINDOWS, PlatformType.MACOS)
        
        # 可视化问题修复
        logger.info("  显示时间基准问题修复可视化...")
        visualize_timebase_issues(broken_timeline, fixed_timeline, logs)


if __name__ == "__main__":
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="跨平台时间基准处理演示")
    parser.add_argument("--no-plot", action="store_true", help="禁用绘图功能")
    args = parser.parse_args()
    
    # 运行演示
    run_demo() 