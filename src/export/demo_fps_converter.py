#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
帧率转换器演示脚本

演示帧率转换器(fps_converter.py)的主要功能和实际应用场景
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any

# 添加项目根目录到系统路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.export.fps_converter import (
    time_to_frames,
    frames_to_time,
    convert_frame_between_fps,
    timecode_to_frames,
    frames_to_timecode,
    FPS_PRESETS,
    get_preset_fps,
    get_common_fps,
    estimate_quality_loss,
    RoundingMethod,
    FPSConverter
)


def demo_basic_conversion():
    """演示基本的时间和帧数转换"""
    print("\n===== 1. 基本时间和帧数转换 =====")
    
    # 测试不同帧率下的时间转帧转换
    test_times = [1.0, 1.5, 2.0, 2.5, 5.0, 10.0]
    test_fps = [24.0, 25.0, 30.0, 60.0]
    
    print("时间 → 帧数:")
    for time in test_times[:3]:  # 只显示部分结果
        results = []
        for fps in test_fps:
            frames = time_to_frames(time, fps)
            results.append(f"{fps}fps: {frames}帧")
        print(f"  {time}秒 → {', '.join(results)}")
    
    print("\n帧数 → 时间:")
    test_frames = [24, 30, 60, 120, 240]
    for frames in test_frames[:3]:  # 只显示部分结果
        results = []
        for fps in test_fps:
            time = frames_to_time(frames, fps)
            results.append(f"{fps}fps: {time:.3f}秒")
        print(f"  {frames}帧 → {', '.join(results)}")


def demo_frame_conversion():
    """演示不同帧率之间的帧数转换"""
    print("\n===== 2. 不同帧率之间的帧数转换 =====")
    
    # 常见帧率转换场景
    test_cases = [
        (30, 30, 24),  # 30fps第30帧 → 24fps
        (24, 24, 30),  # 24fps第24帧 → 30fps
        (60, 30, 60),  # 30fps第60帧 → 60fps
        (60, 60, 30),  # 60fps第60帧 → 30fps
        (100, 25, 30)  # 25fps第100帧 → 30fps
    ]
    
    for frame, source_fps, target_fps in test_cases:
        result = convert_frame_between_fps(frame, source_fps, target_fps)
        print(f"  {source_fps}fps的第{frame}帧 → {target_fps}fps的第{result}帧")
    
    # 不同舍入方法的效果
    print("\n舍入方法的影响:")
    test_frame = 25
    source_fps = 25
    target_fps = 30
    for method in RoundingMethod:
        result = convert_frame_between_fps(test_frame, source_fps, target_fps, method)
        print(f"  {source_fps}fps的第{test_frame}帧 → {target_fps}fps的第{result}帧 (使用{method.name})")


def demo_timecode_conversion():
    """演示时间码与帧数的转换"""
    print("\n===== 3. 时间码与帧数的转换 =====")
    
    # 时间码 → 帧数
    test_timecodes = [
        "00:00:01.000",  # 1秒
        "00:00:01.500",  # 1.5秒
        "00:01:00.000",  # 1分钟
        "01:00:00.000",  # 1小时
        "00:00:01:15"    # 1秒15帧 (基于30fps)
    ]
    
    test_fps = [24.0, 25.0, 30.0]
    
    print("时间码 → 帧数:")
    for tc in test_timecodes[:3]:  # 只显示部分结果
        results = []
        for fps in test_fps:
            try:
                frames = timecode_to_frames(tc, fps)
                results.append(f"{fps}fps: {frames}帧")
            except ValueError as e:
                results.append(f"{fps}fps: 错误({str(e)})")
        print(f"  {tc} → {', '.join(results)}")
    
    # 帧数 → 时间码
    print("\n帧数 → 时间码:")
    test_frames = [24, 30, 45, 60, 90]
    for frame in test_frames[:3]:  # 只显示部分结果
        results = []
        for fps in test_fps:
            tc = frames_to_timecode(frame, fps)
            tc_frames = frames_to_timecode(frame, fps, use_frames=True)
            results.append(f"{fps}fps: {tc} / {tc_frames}")
        print(f"  {frame}帧 → {', '.join(results)}")


def demo_fps_presets():
    """演示帧率预设"""
    print("\n== 帧率预设演示 ==")
    
    # 显示所有预设
    presets = FPS_PRESETS
    print("可用帧率预设:")
    for name, fps in presets.items():
        print(f"  {name}: {fps} fps")
    
    # 获取特定预设
    print("\n获取特定预设:")
    test_presets = ["default", "cinematic", "mobile", "web", "high"]
    for preset in test_presets:
        try:
            fps = get_preset_fps(preset)
            print(f"  {preset} → {fps}fps")
        except ValueError as e:
            print(f"  {preset} → 错误({str(e)})")


def demo_conversion_quality():
    """演示帧率转换质量评估"""
    print("\n===== 5. 帧率转换质量评估 =====")
    
    # 常见的帧率转换场景
    test_pairs = [
        (24, 30),    # 电影 → 视频
        (30, 24),    # 视频 → 电影
        (60, 30),    # 高帧率 → 标准
        (30, 60),    # 标准 → 高帧率
        (25, 30),    # PAL → NTSC
        (29.97, 25), # NTSC → PAL
        (24, 23.976) # 电影 → 电视电影
    ]
    
    print("帧率转换质量损失估计:")
    for source, target in test_pairs:
        loss = estimate_quality_loss(source, target)
        common = get_common_fps(source, target)
        
        quality = "无损失" if loss == 0 else (
            "微小损失" if loss < 0.05 else (
            "轻微损失" if loss < 0.2 else (
            "中等损失" if loss < 0.5 else "严重损失")))
        
        print(f"  {source}fps → {target}fps:")
        print(f"    质量损失: {loss:.2%} ({quality})")
        print(f"    公共帧率: {common:.3f}fps")


def demo_timeline_conversion():
    """演示时间轴数据的帧率转换"""
    print("\n===== 6. 时间轴数据帧率转换 =====")
    
    # 创建示例时间轴数据
    timeline = {
        "name": "示例项目",
        "description": "帧率转换演示",
        "fps": 24.0,
        "clips": [
            {
                "id": "clip1",
                "name": "场景1",
                "start_frame": 0,
                "end_frame": 240,
                "in_frame": 0,
                "out_frame": 240,
                "start_time": 0.0,
                "end_time": 10.0,
                "duration": 10.0
            },
            {
                "id": "clip2",
                "name": "场景2",
                "start_frame": 240,
                "end_frame": 480,
                "in_frame": 0,
                "out_frame": 240,
                "start_time": 10.0,
                "end_time": 20.0,
                "duration": 10.0
            }
        ],
        "tracks": [
            {
                "id": "video_track",
                "name": "视频轨",
                "type": "video",
                "frame_rate": 24.0,
                "items": [
                    {
                        "id": "item1",
                        "clip_id": "clip1",
                        "start_frame": 0,
                        "end_frame": 240
                    },
                    {
                        "id": "item2",
                        "clip_id": "clip2",
                        "start_frame": 240,
                        "end_frame": 480
                    }
                ]
            }
        ]
    }
    
    # 显示原始时间轴数据
    print("原始时间轴数据 (24fps):")
    print(f"  全局帧率: {timeline['fps']}fps")
    print(f"  轨道帧率: {timeline['tracks'][0]['frame_rate']}fps")
    print(f"  片段1: 帧 {timeline['clips'][0]['start_frame']}-{timeline['clips'][0]['end_frame']}, "
          f"时间 {timeline['clips'][0]['start_time']:.1f}s-{timeline['clips'][0]['end_time']:.1f}s")
    
    # 转换到30fps
    converter = FPSConverter()
    converted = converter.convert_timeline(timeline, 24.0, 30.0)
    
    # 显示转换后的时间轴数据
    print("\n转换后的时间轴数据 (30fps):")
    print(f"  全局帧率: {converted['fps']}fps (原始: {converted['original_fps']}fps)")
    print(f"  轨道帧率: {converted['tracks'][0]['frame_rate']}fps "
          f"(原始: {converted['tracks'][0]['original_frame_rate']}fps)")
    print(f"  片段1: 帧 {converted['clips'][0]['start_frame']}-{converted['clips'][0]['end_frame']}, "
          f"时间 {converted['clips'][0]['start_time']:.1f}s-{converted['clips'][0]['end_time']:.1f}s")
    
    # 转换到25fps (从30fps)
    converted_again = converter.convert_timeline(converted, 30.0, 25.0)
    
    # 显示再次转换后的时间轴数据
    print("\n再次转换后的时间轴数据 (25fps):")
    print(f"  全局帧率: {converted_again['fps']}fps (原始: {converted_again['original_fps']}fps)")
    print(f"  轨道帧率: {converted_again['tracks'][0]['frame_rate']}fps "
          f"(原始: {converted_again['tracks'][0]['original_frame_rate']}fps)")
    print(f"  片段1: 帧 {converted_again['clips'][0]['start_frame']}-{converted_again['clips'][0]['end_frame']}, "
          f"时间 {converted_again['clips'][0]['start_time']:.1f}s-{converted_again['clips'][0]['end_time']:.1f}s")


def demo_practical_examples():
    """演示实际应用场景"""
    print("\n===== 7. 实际应用场景 =====")
    
    print("场景1: 电影到网络视频转换 (24fps → 30fps)")
    print("  步骤:")
    print("  1. 识别源片段帧率为24fps")
    print("  2. 确定目标网络平台使用30fps")
    print("  3. 估算质量损失:", end=" ")
    loss = estimate_quality_loss(24, 30)
    print(f"{loss:.2%} (无损失，因为是提升帧率)")
    print("  4. 计算100秒片段的帧数转换:")
    print(f"    24fps: {time_to_frames(100, 24)}帧")
    print(f"    30fps: {time_to_frames(100, 30)}帧")
    print("  5. 转换关键帧位置:")
    for frame in [240, 600, 1200]:  # 10秒, 25秒, 50秒的帧
        new_frame = convert_frame_between_fps(frame, 24, 30)
        print(f"    第{frame}帧 (24fps) → 第{new_frame}帧 (30fps)")
    
    print("\n场景2: 不同地区标准转换 (PAL 25fps ↔ NTSC 29.97fps)")
    print("  欧洲PAL标准: 25fps")
    print("  北美NTSC标准: 29.97fps")
    print("  转换PAL到NTSC:")
    for frame in [25, 50, 100]:  # 1秒, 2秒, 4秒的帧
        new_frame = convert_frame_between_fps(frame, 25, 29.97)
        print(f"    第{frame}帧 (25fps) → 第{new_frame}帧 (29.97fps)")
    print("  转换NTSC到PAL:")
    for frame in [30, 60, 120]:  # 1秒, 2秒, 4秒的帧
        new_frame = convert_frame_between_fps(frame, 29.97, 25)
        print(f"    第{frame}帧 (29.97fps) → 第{new_frame}帧 (25fps)")
    print("  质量损失估计:")
    print(f"    PAL→NTSC: {estimate_quality_loss(25, 29.97):.2%}")
    print(f"    NTSC→PAL: {estimate_quality_loss(29.97, 25):.2%}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="帧率转换器演示")
    parser.add_argument("--all", action="store_true", help="运行所有演示")
    parser.add_argument("--basic", action="store_true", help="基本时间和帧数转换")
    parser.add_argument("--frame", action="store_true", help="不同帧率之间的帧数转换")
    parser.add_argument("--timecode", action="store_true", help="时间码与帧数的转换")
    parser.add_argument("--presets", action="store_true", help="帧率预设")
    parser.add_argument("--quality", action="store_true", help="帧率转换质量评估")
    parser.add_argument("--timeline", action="store_true", help="时间轴数据帧率转换")
    parser.add_argument("--practical", action="store_true", help="实际应用场景")
    
    args = parser.parse_args()
    
    # 默认运行所有演示
    if not any(vars(args).values()):
        args.all = True
    
    # 打印标题
    print("==================================================")
    print("         帧率转换器(FPS Converter)演示")
    print("==================================================")
    
    # 运行所选的演示
    if args.all or args.basic:
        demo_basic_conversion()
    
    if args.all or args.frame:
        demo_frame_conversion()
    
    if args.all or args.timecode:
        demo_timecode_conversion()
    
    if args.all or args.presets:
        demo_fps_presets()
    
    if args.all or args.quality:
        demo_conversion_quality()
    
    if args.all or args.timeline:
        demo_timeline_conversion()
    
    if args.all or args.practical:
        demo_practical_examples()


if __name__ == "__main__":
    main() 