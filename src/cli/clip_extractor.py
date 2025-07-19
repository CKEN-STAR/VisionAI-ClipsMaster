#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
短视频片段提取命令行工具

提供从长视频中自动提取精彩片段的命令行界面，
支持字幕分析、场景检测和智能片段选择。
"""

import os
import sys
import time
import argparse
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

# 确保可以导入项目模块
sys.path.append(str(Path(__file__).resolve().parents[2]))

from src.core.video_processor import get_video_processor
from src.utils.log_handler import get_logger, setup_logging
from src.utils.file_utils import ensure_dir, get_temp_path

# 配置日志
setup_logging()
cli_logger = get_logger("clip_extractor_cli")

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="智能视频片段提取工具")
    
    # 输入视频路径（必需）
    parser.add_argument("video_path", help="输入视频文件的路径")
    
    # 输出目录（可选）
    parser.add_argument("-o", "--output-dir", help="输出目录路径，默认为'output'子目录")
    
    # 最小片段时长
    parser.add_argument("--min-duration", type=float, default=3.0,
                        help="最小片段时长（秒），默认3秒")
    
    # 最大片段时长
    parser.add_argument("--max-duration", type=float, default=30.0,
                        help="最大片段时长（秒），默认30秒")
    
    # 最大片段数量
    parser.add_argument("--max-clips", type=int, default=10,
                        help="最大生成片段数量，默认10个")
    
    # 是否导出片段
    parser.add_argument("--export", action="store_true",
                        help="是否导出视频片段，默认只分析不导出")
    
    # 场景变化阈值
    parser.add_argument("--scene-threshold", type=float, default=30.0,
                        help="场景变化检测阈值，值越大场景检测越不敏感，默认30.0")
    
    # 保存分析结果的JSON文件名
    parser.add_argument("--save-analysis", action="store_true",
                        help="是否保存分析结果到JSON文件")
    
    # 显示详细信息
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="显示详细处理信息")
    
    return parser.parse_args()

def process_video(args):
    """处理视频文件"""
    # 获取视频处理器
    video_processor = get_video_processor()
    
    # 设置处理参数
    video_processor.min_clip_duration = args.min_duration
    video_processor.max_clip_duration = args.max_duration
    video_processor.scene_change_threshold = args.scene_threshold
    
    # 确保输出目录存在
    if args.output_dir:
        output_dir = args.output_dir
    else:
        # 根据视频文件名创建输出目录
        video_name = os.path.splitext(os.path.basename(args.video_path))[0]
        output_dir = os.path.join(os.path.dirname(args.video_path), f"output_{video_name}")
    
    ensure_dir(output_dir)
    cli_logger.info(f"处理视频: {args.video_path}")
    cli_logger.info(f"输出目录: {output_dir}")
    
    # 处理视频
    start_time = time.time()
    result = video_processor.process_video(args.video_path, output_dir)
    process_time = time.time() - start_time
    
    # 打印处理结果
    selected_clips = result.get("selected_clips", [])
    cli_logger.info(f"处理完成，耗时: {process_time:.2f}秒")
    cli_logger.info(f"检测到 {result.get('scene_count', 0)} 个场景")
    cli_logger.info(f"音频峰值: {result.get('audio_peaks', 0)} 个")
    cli_logger.info(f"候选片段: {result.get('candidate_clip_count', 0)} 个")
    cli_logger.info(f"选定片段: {len(selected_clips)} 个")
    
    # 显示详细片段信息
    if args.verbose:
        for i, clip in enumerate(selected_clips, 1):
            start = clip["start_time"]
            end = clip["end_time"]
            duration = clip["duration"]
            score = clip.get("score", 0)
            clip_type = clip["type"]
            
            print(f"\n片段 {i}:")
            print(f"  时间范围: {format_time(start)} - {format_time(end)} (时长: {format_time(duration)})")
            print(f"  评分: {score:.1f}")
            print(f"  类型: {clip_type}")
            
            if clip_type == "subtitle_based" and "subtitles" in clip:
                print(f"  字幕内容: {' '.join(clip['subtitles'])[:100]}...")
    
    # 导出视频片段
    if args.export and selected_clips:
        cli_logger.info("开始导出视频片段...")
        
        for i, clip in enumerate(selected_clips, 1):
            start = clip["start_time"]
            end = clip["end_time"]
            
            # 创建输出文件名
            clip_filename = f"clip_{i:02d}_{format_time(start).replace(':', '-')}_to_{format_time(end).replace(':', '-')}.mp4"
            clip_path = os.path.join(output_dir, clip_filename)
            
            # 导出片段
            success = video_processor.export_clip(args.video_path, clip_path, start, end)
            
            if success:
                cli_logger.info(f"已导出片段 {i}: {clip_path}")
            else:
                cli_logger.error(f"导出片段 {i} 失败")
    
    # 保存分析结果
    if args.save_analysis:
        analysis_path = os.path.join(output_dir, "analysis_result.json")
        with open(analysis_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        cli_logger.info(f"分析结果已保存: {analysis_path}")
    
    return result

def format_time(seconds):
    """将秒格式化为时:分:秒格式"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = seconds % 60
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:06.3f}"
    else:
        return f"{minutes:02d}:{seconds:06.3f}"

def main():
    """主函数"""
    # 解析命令行参数
    args = parse_args()
    
    try:
        # 验证输入文件存在
        if not os.path.exists(args.video_path):
            cli_logger.error(f"视频文件不存在: {args.video_path}")
            return 1
        
        # 处理视频
        process_video(args)
        
        return 0
        
    except KeyboardInterrupt:
        cli_logger.info("处理已被用户中断")
        return 130
    except Exception as e:
        cli_logger.error(f"处理过程中发生错误: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main()) 