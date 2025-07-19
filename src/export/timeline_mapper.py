#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
时间轴映射模块

提供SRT时间轴到视频编辑轨道的映射功能。
转换字幕时间码到视频帧，生成可导入编辑软件的轨道数据。
"""

import os
import math
import logging
from typing import Dict, List, Any, Optional, Union, Tuple

from src.utils.log_handler import get_logger

# 配置日志
logger = get_logger("timeline_mapper")

def map_srt_to_tracks(srt_segments: List[Dict[str, Any]], fps: float = 25.0) -> str:
    """将SRT时间轴转换为剪辑轨道序列
    
    将SRT格式的字幕片段列表转换为轨道XML格式，便于导入到视频编辑软件。
    
    Args:
        srt_segments: SRT字幕片段列表，每个片段包含start_time、duration、text等信息
        fps: 帧率，默认25fps
        
    Returns:
        str: 轨道XML格式字符串
    """
    tracks = []
    
    for idx, seg in enumerate(srt_segments):
        # 获取片段信息
        asset_id = seg.get('asset_id', f"asset_{idx}")
        start_frame = time_to_frame(seg.get('start_time', 0), fps)
        end_frame = time_to_frame(seg.get('start_time', 0) + seg.get('duration', 5), fps)
        
        # 构建轨道片段XML
        clip_xml = f'''
<clip id="clip_{idx}">
    <asset ref="{asset_id}"/>
    <in>{start_frame}</in>
    <out>{end_frame}</out>
</clip>'''
        
        tracks.append(clip_xml)
        
    return '\n'.join(tracks)

def time_to_frame(time_seconds: float, fps: float = 25.0) -> int:
    """将时间（秒）转换为帧数
    
    Args:
        time_seconds: 时间（秒）
        fps: 帧率，默认25fps
        
    Returns:
        int: 对应的帧数
    """
    return math.floor(time_seconds * fps)

def frame_to_time(frame: int, fps: float = 25.0) -> float:
    """将帧数转换为时间（秒）
    
    Args:
        frame: 帧数
        fps: 帧率，默认25fps
        
    Returns:
        float: 对应的时间（秒）
    """
    return frame / fps

def format_timeline_timecode(seconds: float, fps: float = 25.0) -> str:
    """格式化时间为编辑软件可用的时间码
    
    Args:
        seconds: 时间（秒）
        fps: 帧率，默认25fps
        
    Returns:
        str: 格式化的时间码，格式为HH:MM:SS:FF
    """
    total_frames = int(seconds * fps)
    frames = total_frames % int(fps)
    total_seconds = total_frames // int(fps)
    
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    
    return f"{hours:02d}:{minutes:02d}:{secs:02d}:{frames:02d}"

def create_track_from_segments(segments: List[Dict[str, Any]], track_type: str = "video", fps: float = 25.0) -> Dict[str, Any]:
    """从片段列表创建轨道数据
    
    Args:
        segments: 片段列表
        track_type: 轨道类型，"video"或"audio"
        fps: 帧率，默认25fps
        
    Returns:
        Dict[str, Any]: 轨道数据
    """
    clips = []
    
    for idx, segment in enumerate(segments):
        # 确保有asset_id
        if 'asset_id' not in segment:
            segment['asset_id'] = f"asset_{idx}"
            
        # 获取开始和结束时间
        start_time = segment.get('start_time', 0.0)
        duration = segment.get('duration', 5.0)
        end_time = start_time + duration
        
        # 转换为帧
        start_frame = time_to_frame(start_time, fps)
        end_frame = time_to_frame(end_time, fps)
        
        # 创建片段数据
        clip = {
            "id": f"clip_{idx}",
            "asset_id": segment['asset_id'],
            "start_frame": start_frame,
            "end_frame": end_frame,
            "duration_frames": end_frame - start_frame,
            "start_time": start_time,
            "end_time": end_time,
            "duration": duration,
            "track_position": idx  # 默认按顺序排列
        }
        
        # 添加文本信息（如果有）
        if 'text' in segment:
            clip['text'] = segment['text']
            
        clips.append(clip)
    
    # 创建轨道
    track = {
        "type": track_type,
        "clips": clips,
        "total_duration": sum(clip['duration'] for clip in clips)
    }
    
    return track

def map_segments_to_timeline(segments: List[Dict[str, Any]], fps: float = 25.0) -> Dict[str, Any]:
    """将片段列表映射到完整时间轴
    
    创建一个完整的时间轴结构，包含视频和音频轨道
    
    Args:
        segments: 片段列表
        fps: 帧率，默认25fps
        
    Returns:
        Dict[str, Any]: 时间轴数据
    """
    # 创建视频轨道
    video_track = create_track_from_segments(segments, "video", fps)
    
    # 创建音频轨道
    audio_track = create_track_from_segments(
        [seg for seg in segments if seg.get('has_audio', True)],
        "audio", 
        fps
    )
    
    # 组合时间轴
    timeline = {
        "fps": fps,
        "duration": max(video_track['total_duration'], audio_track['total_duration']),
        "tracks": {
            "video": [video_track],
            "audio": [audio_track]
        }
    }
    
    return timeline

def generate_fcpxml_tracks(segments: List[Dict[str, Any]], fps: float = 25.0) -> str:
    """生成Final Cut Pro XML轨道数据
    
    Args:
        segments: 片段列表
        fps: 帧率，默认25fps
        
    Returns:
        str: FCPXML轨道数据
    """
    tracks = []
    
    for idx, seg in enumerate(segments):
        start_time = seg.get('start_time', 0.0)
        duration = seg.get('duration', 5.0)
        asset_id = seg.get('asset_id', f"asset_{idx}")
        
        clip_xml = f'''<clip id="clip_{idx}" start="{format_timeline_timecode(start_time, fps)}" duration="{format_timeline_timecode(duration, fps)}">
    <asset-ref ref="{asset_id}"/>
</clip>'''
        tracks.append(clip_xml)
    
    return "\n".join(tracks)

def generate_premiere_tracks(segments: List[Dict[str, Any]], fps: float = 25.0) -> str:
    """生成Premiere Pro XML轨道数据
    
    Args:
        segments: 片段列表
        fps: 帧率，默认25fps
        
    Returns:
        str: Premiere轨道数据
    """
    tracks = []
    current_position = 0
    
    for idx, seg in enumerate(segments):
        start_time = seg.get('start_time', 0.0)
        duration = seg.get('duration', 5.0)
        asset_id = seg.get('asset_id', f"asset_{idx}")
        
        # Premiere以帧为单位
        start_frame = time_to_frame(start_time, fps)
        end_frame = time_to_frame(start_time + duration, fps)
        pos_start = time_to_frame(current_position, fps)
        pos_end = time_to_frame(current_position + duration, fps)
        
        clip_xml = f'''<clipitem id="clipitem-{idx}">
    <name>Clip {idx}</name>
    <rate>
        <timebase>{int(fps)}</timebase>
    </rate>
    <in>{start_frame}</in>
    <out>{end_frame}</out>
    <start>{pos_start}</start>
    <end>{pos_end}</end>
    <file id="{asset_id}"/>
</clipitem>'''
        tracks.append(clip_xml)
        
        current_position += duration
    
    return "\n".join(tracks)

def generate_jianying_track_data(segments: List[Dict[str, Any]], fps: float = 25.0) -> Dict[str, Any]:
    """生成剪映轨道数据
    
    Args:
        segments: 片段列表
        fps: 帧率，默认25fps
        
    Returns:
        Dict[str, Any]: 剪映轨道数据
    """
    track_segments = []
    current_position = 0
    
    for idx, seg in enumerate(segments):
        start_time = seg.get('start_time', 0.0)
        duration = seg.get('duration', 5.0)
        asset_id = seg.get('asset_id', f"asset_{idx}")
        
        segment = {
            "id": f"segment_{idx}",
            "material_id": asset_id,
            "start_time": start_time,
            "duration": duration,
            "target_timerange": {
                "start": current_position,
                "duration": duration
            }
        }
        
        track_segments.append(segment)
        current_position += duration
    
    return {
        "segments": track_segments,
        "total_duration": current_position
    }

# 测试函数
def test_timeline_mapper():
    """测试时间轴映射功能"""
    test_segments = [
        {"start_time": 10.5, "duration": 5.0, "text": "第一个片段", "asset_id": "asset_12345678"},
        {"start_time": 25.0, "duration": 3.0, "text": "第二个片段", "asset_id": "asset_23456789"},
        {"start_time": 45.0, "duration": 8.0, "text": "第三个片段", "asset_id": "asset_34567890", "has_audio": False},
        {"start_time": 60.0, "duration": 4.0, "text": "第四个片段", "asset_id": "asset_45678901"}
    ]
    
    print("===== 测试时间轴映射功能 =====")
    
    # 测试基本映射
    tracks_xml = map_srt_to_tracks(test_segments)
    print("\n基本轨道映射:\n", tracks_xml)
    
    # 测试时间和帧转换
    test_time = 12.5
    test_frame = time_to_frame(test_time)
    print(f"\n时间 {test_time}s 对应帧: {test_frame}")
    print(f"帧 {test_frame} 对应时间: {frame_to_time(test_frame)}s")
    
    # 测试时间码格式化
    print(f"\n时间 {test_time}s 的时间码: {format_timeline_timecode(test_time)}")
    
    # 测试完整时间轴生成
    timeline = map_segments_to_timeline(test_segments)
    print("\n完整时间轴数据示例:")
    print(f"  总时长: {timeline['duration']}s")
    print(f"  视频轨道数: {len(timeline['tracks']['video'])}")
    print(f"  音频轨道数: {len(timeline['tracks']['audio'])}")
    print(f"  视频片段数: {len(timeline['tracks']['video'][0]['clips'])}")
    print(f"  音频片段数: {len(timeline['tracks']['audio'][0]['clips'])}")

if __name__ == "__main__":
    test_timeline_mapper() 