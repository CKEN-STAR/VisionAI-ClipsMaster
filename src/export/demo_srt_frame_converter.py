#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster SRT时间码转换器演示程序

此脚本演示如何使用SRT时间码转换器的各种功能，包括：
1. 单个SRT时间码转换为帧号
2. 帧号转换回SRT时间码
3. 处理整个SRT文件
4. 在混剪导出工作流中的应用

这些功能对于将SRT字幕与视频帧精确同步非常重要。
"""

import os
import sys
import json
import traceback
from typing import Dict, List, Any

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

try:
    # 导入相关模块
    from src.export.srt_frame_converter import (
        parse_srt_time, frames_to_srt_time, convert_srt_file, 
        get_frame_timestamps
    )
    from src.export.fps_converter import RoundingMethod
except ImportError as e:
    print(f"导入模块失败: {e}")
    traceback.print_exc()
    sys.exit(1)


def demo_basic_conversion():
    """演示基本的时间码转换功能"""
    print("\n=== 基本时间码转换演示 ===")
    
    # 测试数据
    test_times = [
        "00:00:05,000",    # 5秒
        "00:01:30,500",    # 1分30.5秒
        "01:02:03,456"     # 1小时2分3.456秒
    ]
    
    # 测试不同帧率
    fps_values = [24, 25, 30, 60]
    
    for srt_time in test_times:
        print(f"\n时间码: {srt_time}")
        
        for fps in fps_values:
            try:
                frames = parse_srt_time(srt_time, fps)
                back_to_srt = frames_to_srt_time(frames, fps)
                
                print(f"  {fps}fps: {frames}帧 (回转: {back_to_srt})")
            except Exception as e:
                print(f"  {fps}fps: 转换失败 - {e}")


def demo_rounding_methods():
    """演示不同舍入方法的效果"""
    print("\n=== 不同舍入方法演示 ===")
    
    # 测试数据 - 选择会产生小数的时间点
    test_time = "00:00:10,500"  # 在特定帧率下会产生小数帧数
    fps = 24  # 使用24fps: 10.5秒 * 24 = 252帧
    
    print(f"时间码: {test_time} @ {fps}fps")
    
    try:
        # 尝试不同的舍入方法
        frames_round = parse_srt_time(test_time, fps, RoundingMethod.ROUND)
        frames_floor = parse_srt_time(test_time, fps, RoundingMethod.FLOOR)
        frames_ceil = parse_srt_time(test_time, fps, RoundingMethod.CEIL)
        
        print(f"  四舍五入: {frames_round}帧")
        print(f"  向下取整: {frames_floor}帧")
        print(f"  向上取整: {frames_ceil}帧")
    except Exception as e:
        print(f"  舍入方法演示失败: {e}")


def demo_srt_file_processing():
    """演示处理整个SRT文件"""
    print("\n=== SRT文件处理演示 ===")
    
    # 查找项目根目录的测试SRT文件
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
    test_srt = os.path.join(project_root, "test.srt")
    
    if not os.path.exists(test_srt):
        print(f"创建示例SRT文件: {test_srt}")
        
        # 创建一个简单的SRT文件用于测试
        with open(test_srt, 'w', encoding='utf-8') as f:
            f.write('''1
00:00:01,000 --> 00:00:04,000
这是一个测试字幕文件

2
00:00:05,000 --> 00:00:09,000
用于测试VisionAI-ClipsMaster的爆款SRT生成功能

3
00:00:10,000 --> 00:00:15,000
现在我们不需要手动调整参数了

4
00:00:16,000 --> 00:00:20,000
AI模型会根据训练自主决定最佳参数
''')
    
    print(f"使用SRT文件: {test_srt}")
    
    try:
        # 转换为帧号映射
        output_json = os.path.join(os.path.dirname(test_srt), "test_frames.json")
        frame_map = convert_srt_file(test_srt, fps=25.0, output_file=output_json, mode="frames")
        
        print("\n帧号映射结果:")
        for subtitle_id, data in frame_map.items():
            print(f"  字幕 #{subtitle_id}: {data['start_frame']} - {data['end_frame']} ({data['duration_frames']}帧) 内容: {data['text'][:20]}...")
        
        # 标准化时间码
        normalized_srt = os.path.join(os.path.dirname(test_srt), "test_normalized.srt")
        normalized_content = convert_srt_file(test_srt, fps=25.0, output_file=normalized_srt, mode="timecode")
        
        print(f"\n标准化SRT文件已保存至: {normalized_srt}")
        print("标准化内容预览:")
        lines = normalized_content.split('\n')
        for i in range(min(10, len(lines))):
            print(f"  {lines[i]}")
        if len(lines) > 10:
            print("  ...")
    except Exception as e:
        print(f"SRT文件处理失败: {e}")
        traceback.print_exc()


def demo_workflow_integration():
    """演示在混剪工作流中的应用"""
    print("\n=== 混剪工作流集成演示 ===")
    
    print("1. 从原始字幕提取关键片段")
    
    # 模拟SRT字幕数据
    subtitles = [
        {"id": "1", "start": "00:00:05,000", "end": "00:00:10,000", "text": "这是开场白"},
        {"id": "2", "start": "00:00:20,500", "end": "00:00:25,000", "text": "这是转场"},
        {"id": "3", "start": "00:01:05,800", "end": "00:01:15,500", "text": "这是结束语"}
    ]
    
    print(f"  找到 {len(subtitles)} 条字幕:")
    for idx, subtitle in enumerate(subtitles):
        print(f"  - 字幕 {idx+1}: {subtitle['start']} --> {subtitle['end']} - {subtitle['text']}")
        
    # 单独输出一行避免打印错误
    print("")
    
    try:
        # 演示如何将字幕转换为剪辑片段
        print("2. 生成混剪片段:")
        
        clips = []
        fps = 30.0
        
        for subtitle in subtitles:
            # 获取帧时间戳
            frames = get_frame_timestamps(subtitle["start"], subtitle["end"], fps)
            
            # 创建剪辑片段数据
            clip = {
                "id": f"clip_{subtitle['id']}",
                "start_frame": frames["start_frame"],
                "end_frame": frames["end_frame"],
                "duration_frames": frames["duration_frames"],
                "text": subtitle["text"],
                "source_subtitle_id": subtitle["id"]
            }
            
            clips.append(clip)
            print(f"  片段 #{clip['id']}: {clip['start_frame']} - {clip['end_frame']} ({clip['duration_frames']}帧) 内容: {clip['text']}")
        
        # 计算总时长
        total_frames = sum(clip["duration_frames"] for clip in clips)
        total_seconds = total_frames / fps
        
        print(f"\n3. 混剪总时长: {total_frames}帧 ({total_seconds:.2f}秒 @ {fps}fps)")
        
        # 添加时间码转换展示
        print("\n4. 最终输出时间码信息:")
        for i, clip in enumerate(clips):
            start_tc = frames_to_srt_time(clip["start_frame"], fps)
            end_tc = frames_to_srt_time(clip["end_frame"], fps)
            print(f"  剪辑 {i+1}: {start_tc} --> {end_tc} - {clip['text']}")
            
        # 确保看到所有输出
        import time
        time.sleep(0.1)
    
    except Exception as e:
        print(f"工作流集成演示失败: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    print("=== VisionAI-ClipsMaster SRT时间码转换器演示 ===")
    
    try:
        # 运行所有演示函数
        demo_basic_conversion()
        demo_rounding_methods()
        demo_srt_file_processing()
        demo_workflow_integration()
        
        # 确保看到所有输出
        import time
        time.sleep(0.1)
        
        print("\n演示完成!")
    except Exception as e:
        print(f"\n演示过程中发生错误: {e}")
        traceback.print_exc() 