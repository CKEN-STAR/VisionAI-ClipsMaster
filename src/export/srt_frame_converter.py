#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster SRT时间码转换器

此模块提供从SRT时间码到帧数的直接转换功能，是导出功能的关键组件。
可以处理多种格式的时间码，并支持不同的舍入策略。

主要功能：
1. SRT时间码直接转换为帧号
2. 帧号转换为SRT时间码
3. 批量处理SRT字幕文件
4. 不同帧率的自动适配
"""

import os
import re
from typing import List, Dict, Any, Union, Tuple, Optional
from enum import Enum

# 导入相关模块
from src.utils.log_handler import get_logger
from src.parsers.timecode_parser import parse_timecode, TimeCode
from src.export.fps_converter import (
    time_to_frames, frames_to_time, timecode_to_frames, 
    frames_to_timecode, RoundingMethod
)

# 配置日志
logger = get_logger("srt_frame_converter")


def parse_srt_time(srt_time: str, fps: float = 25.0, 
                  rounding: RoundingMethod = RoundingMethod.ROUND) -> int:
    """将SRT格式时间码转换为对应帧号
    
    Args:
        srt_time: SRT格式时间码 (格式: 00:01:30,500)
        fps: 目标帧率
        rounding: 舍入方法
        
    Returns:
        转换后的帧号
    """
    # 解析SRT时间
    tc = parse_timecode(srt_time)
    
    # 转换为帧数
    return time_to_frames(tc.to_seconds(), fps, rounding)


def frames_to_srt_time(frames: int, fps: float = 25.0) -> str:
    """将帧号转换为SRT格式时间码
    
    Args:
        frames: 帧号
        fps: 帧率
        
    Returns:
        SRT格式时间码字符串 (格式: 00:01:30,500)
    """
    # 先转换为秒
    seconds = frames_to_time(frames, fps)
    
    # 创建TimeCode对象
    tc = TimeCode.from_seconds(seconds)
    
    # 返回SRT格式
    return tc.to_srt_format()


def convert_srt_file(srt_file_path: str, fps: float = 25.0,
                    output_file: str = None, mode: str = "frames") -> Union[Dict[str, Any], str]:
    """转换整个SRT文件
    
    Args:
        srt_file_path: SRT文件路径
        fps: 目标帧率
        output_file: 输出文件路径(如果为None则不输出文件)
        mode: 转换模式 - "frames"(输出帧号) 或 "timecode"(保持时间码格式)
        
    Returns:
        如果mode="frames"，返回字幕ID到帧号范围的映射字典
        如果mode="timecode"，返回转换后的SRT内容字符串
    """
    # 确保文件存在
    if not os.path.exists(srt_file_path):
        logger.error(f"SRT文件不存在: {srt_file_path}")
        raise FileNotFoundError(f"SRT文件不存在: {srt_file_path}")
    
    # 读取SRT文件
    with open(srt_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 解析SRT内容
    subtitle_pattern = r'(\d+)\s+(\d{2}:\d{2}:\d{2},\d{3})\s+-->\s+(\d{2}:\d{2}:\d{2},\d{3})\s+([\s\S]*?)(?=\n\s*\n\d+\s+|$)'
    subtitles = re.findall(subtitle_pattern, content)
    
    if mode == "frames":
        # 构建字幕ID到帧号范围的映射
        frame_map = {}
        for subtitle in subtitles:
            subtitle_id, start_time, end_time, text = subtitle
            start_frame = parse_srt_time(start_time, fps)
            end_frame = parse_srt_time(end_time, fps)
            frame_map[subtitle_id] = {
                "start_frame": start_frame,
                "end_frame": end_frame,
                "duration_frames": end_frame - start_frame,
                "text": text.strip()
            }
        
        # 如果指定了输出文件，将映射保存为JSON
        if output_file:
            import json
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(frame_map, f, ensure_ascii=False, indent=2)
        
        return frame_map
    
    elif mode == "timecode":
        # 保持时间码格式，但标准化时间码
        converted_content = ""
        for subtitle in subtitles:
            subtitle_id, start_time, end_time, text = subtitle
            
            # 解析时间码并重新格式化
            start_tc = parse_timecode(start_time)
            end_tc = parse_timecode(end_time)
            
            # 添加到转换后内容
            converted_content += f"{subtitle_id}\n"
            converted_content += f"{start_tc.to_srt_format()} --> {end_tc.to_srt_format()}\n"
            converted_content += f"{text.strip()}\n\n"
        
        # 如果指定了输出文件，保存转换后的内容
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(converted_content)
        
        return converted_content
    
    else:
        logger.error(f"不支持的转换模式: {mode}")
        raise ValueError(f"不支持的转换模式: {mode}, 必须是 'frames' 或 'timecode'")


# 便捷导出函数，用于被其他模块调用
def get_frame_timestamps(srt_time_start: str, srt_time_end: str, fps: float = 25.0) -> Dict[str, int]:
    """获取SRT时间范围对应的帧时间戳
    
    Args:
        srt_time_start: 开始时间 (SRT格式: 00:01:30,500)
        srt_time_end: 结束时间 (SRT格式: 00:01:35,000)
        fps: 帧率
        
    Returns:
        包含start_frame和end_frame的字典
    """
    start_frame = parse_srt_time(srt_time_start, fps)
    end_frame = parse_srt_time(srt_time_end, fps)
    
    return {
        "start_frame": start_frame,
        "end_frame": end_frame,
        "duration_frames": end_frame - start_frame
    }


if __name__ == "__main__":
    # 简单测试
    test_time = "00:01:30,500"
    frames = parse_srt_time(test_time, 25.0)
    print(f"SRT时间 {test_time} 在25fps下对应帧号: {frames}")
    
    # 反向测试
    frames = 2263
    srt_time = frames_to_srt_time(frames, 25.0)
    print(f"帧号 {frames} 在25fps下对应SRT时间: {srt_time}")
    
    # 时间范围测试
    time_range = get_frame_timestamps("00:01:30,500", "00:01:35,000", 25.0)
    print(f"时间范围对应的帧信息: {time_range}") 