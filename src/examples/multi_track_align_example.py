#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
多轨时间轴对齐示例

此脚本演示如何使用多轨时间轴对齐模块来同步视频、音频和字幕轨道。
"""

import sys
import os
import logging

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from timecode.multi_track_align import (
    MultiTrackAligner,
    align_audio_video,
    align_multiple_tracks,
    AlignMethod
)

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("多轨对齐示例")

def simple_audio_video_align():
    """简单的音视频对齐示例"""
    logger.info("=== 简单的音视频对齐示例 ===")
    
    # 模拟音视频轨道数据
    audio_track = {
        "id": "main_audio",
        "type": "audio",
        "duration": 125.8,
        "sample_rate": 44100
    }
    
    video_track = {
        "id": "main_video",
        "type": "video",
        "duration": 120.5,
        "frame_rate": 30.0
    }
    
    # 对齐音视频
    logger.info(f"原始音频时长: {audio_track['duration']}秒, 视频时长: {video_track['duration']}秒")
    aligned_audio, aligned_video = align_audio_video(audio_track, video_track)
    
    # 查看对齐结果
    logger.info(f"对齐后音频时长: {aligned_audio['duration']}秒, 视频时长: {aligned_video['duration']}秒")
    
    if "stretch_ratio" in aligned_video:
        logger.info(f"视频拉伸比例: {aligned_video['stretch_ratio']:.4f}")
    
    if "time_shift" in aligned_audio:
        logger.info(f"音频时移: {aligned_audio['time_shift']}秒")
    
    if "rate_adjust" in aligned_audio:
        logger.info(f"音频速率调整: {aligned_audio['rate_adjust']:.4f}")


def multi_track_alignment():
    """多轨道对齐示例"""
    logger.info("\n=== 多轨道对齐示例 ===")
    
    # 模拟多轨道数据
    tracks = {
        "main_video": {
            "id": "main_video",
            "type": "video",
            "is_main": True,
            "duration": 120.0,
            "frame_rate": 30.0,
            "scenes": [
                {"start_time": 0.0, "end_time": 35.0, "duration": 35.0},
                {"start_time": 35.0, "end_time": 70.0, "duration": 35.0},
                {"start_time": 70.0, "end_time": 120.0, "duration": 50.0}
            ]
        },
        "main_audio": {
            "id": "main_audio",
            "type": "audio",
            "duration": 122.5,
            "sample_rate": 48000
        },
        "background_music": {
            "id": "background_music",
            "type": "audio",
            "duration": 180.0,
            "sample_rate": 44100
        },
        "subtitle": {
            "id": "subtitle",
            "type": "subtitle",
            "duration": 118.0,
            "subtitles": [
                {"id": "sub1", "start_time": 10.0, "end_time": 15.0, "text": "这是第一条字幕"},
                {"id": "sub2", "start_time": 20.0, "end_time": 25.0, "text": "这是第二条字幕"},
                {"id": "sub3", "start_time": 100.0, "end_time": 115.0, "text": "这是最后一条字幕"}
            ]
        },
        "effects": {
            "id": "effects",
            "type": "effects",
            "duration": 105.0,
            "keyframes": [15.0, 30.0, 45.0, 60.0, 90.0]
        }
    }
    
    # 打印原始时长
    logger.info("原始轨道时长:")
    for track_id, track in tracks.items():
        logger.info(f"  {track_id}: {track['duration']}秒")
    
    # 创建对齐器并配置
    config = {
        "alignment_threshold": 1.0,
        "max_stretch_ratio": 0.9,
        "prefer_audio_intact": True,
        "maintain_sync_points": True
    }
    aligner = MultiTrackAligner(config)
    
    # 对齐轨道
    aligned_tracks = aligner.align_tracks(tracks)
    
    # 打印对齐后时长
    logger.info("\n对齐后轨道时长:")
    for track_id, track in aligned_tracks.items():
        logger.info(f"  {track_id}: {track['duration']}秒 (原始: {track.get('original_duration', track['duration'])}秒)")
        
        # 显示对齐方式
        if "stretch_ratio" in track:
            logger.info(f"    - 伸缩比例: {track['stretch_ratio']:.4f}")
        if "time_shift" in track:
            logger.info(f"    - 时移: {track['time_shift']}秒")
        if "crop_info" in track:
            logger.info(f"    - 裁剪: 前端 {track['crop_info']['start_trim']:.2f}秒, 后端 {track['crop_info']['end_trim']:.2f}秒")
        if "pad_info" in track:
            logger.info(f"    - 填充: 前端 {track['pad_info']['start_pad']:.2f}秒, 后端 {track['pad_info']['end_pad']:.2f}秒")
    
    # 显示字幕时间调整
    if "subtitle" in aligned_tracks and "subtitles" in aligned_tracks["subtitle"]:
        logger.info("\n字幕时间点调整:")
        original_subs = tracks["subtitle"]["subtitles"]
        aligned_subs = aligned_tracks["subtitle"]["subtitles"]
        
        for i, (orig, aligned) in enumerate(zip(original_subs, aligned_subs)):
            logger.info(f"  字幕 {i+1}:")
            logger.info(f"    - 原始: {orig['start_time']:.2f}秒 - {orig['end_time']:.2f}秒")
            logger.info(f"    - 调整后: {aligned['start_time']:.2f}秒 - {aligned['end_time']:.2f}秒")


def list_alignment_example():
    """列表形式的多轨道对齐示例"""
    logger.info("\n=== 列表形式的多轨道对齐示例 ===")
    
    # 模拟轨道列表
    tracks = [
        {"id": "video", "type": "video", "duration": 100.0},
        {"id": "audio1", "type": "audio", "duration": 105.0},
        {"id": "audio2", "type": "audio", "duration": 95.0},
        {"id": "subtitle", "type": "subtitle", "duration": 98.0}
    ]
    
    # 打印原始时长
    logger.info("原始轨道时长:")
    for track in tracks:
        logger.info(f"  {track['id']}: {track['duration']}秒")
    
    # 对齐轨道
    aligned_tracks = align_multiple_tracks(tracks)
    
    # 打印对齐后时长
    logger.info("\n对齐后轨道时长:")
    for track in aligned_tracks:
        logger.info(f"  {track['id']}: {track['duration']}秒 (原始: {track.get('original_duration', track['duration'])}秒)")


if __name__ == "__main__":
    simple_audio_video_align()
    multi_track_alignment()
    list_alignment_example() 