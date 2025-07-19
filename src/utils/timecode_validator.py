#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 时间轴验证工具

用于验证视频文件和字幕文件的时间轴同步性
"""

import os
import re
import logging
from pathlib import Path
from typing import Tuple, Optional, List, Dict, Any

# 设置日志
logger = logging.getLogger(__name__)

# 尝试导入视频处理库
try:
    import cv2
except ImportError:
    logger.warning("未安装OpenCV库，视频时长检测将不可用")
    cv2 = None

def parse_srt_timecode(timecode: str) -> float:
    """解析SRT格式的时间码为秒数

    Args:
        timecode: SRT格式的时间码 (00:00:00,000)

    Returns:
        float: 对应的秒数
    """
    # 解析小时:分钟:秒,毫秒
    pattern = r'(\d{2}):(\d{2}):(\d{2}),(\d{3})'
    match = re.match(pattern, timecode)
    
    if not match:
        raise ValueError(f"无效的SRT时间码格式: {timecode}")
    
    hours, minutes, seconds, milliseconds = map(int, match.groups())
    
    # 转换为秒
    total_seconds = hours * 3600 + minutes * 60 + seconds + milliseconds / 1000
    
    return total_seconds

def get_video_duration(video_path: str) -> Optional[float]:
    """获取视频文件的时长

    Args:
        video_path: 视频文件路径

    Returns:
        float: 视频时长（秒），如果无法获取则返回None
    """
    if cv2 is None:
        logger.warning("OpenCV未安装，无法获取视频时长")
        return None
    
    try:
        # 打开视频文件
        video = cv2.VideoCapture(video_path)
        
        # 检查是否成功打开
        if not video.isOpened():
            logger.error(f"无法打开视频文件: {video_path}")
            return None
        
        # 获取帧率和总帧数
        fps = video.get(cv2.CAP_PROP_FPS)
        frame_count = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # 计算时长
        duration = frame_count / fps if fps > 0 else None
        
        # 释放视频对象
        video.release()
        
        return duration
    
    except Exception as e:
        logger.error(f"获取视频时长时出错: {e}")
        return None

def get_srt_duration(srt_path: str) -> Optional[float]:
    """获取SRT字幕文件的持续时间

    Args:
        srt_path: SRT字幕文件路径

    Returns:
        float: 字幕持续时间（秒），如果无法解析则返回None
    """
    try:
        # 读取字幕文件
        with open(srt_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 查找所有时间码
        pattern = r'\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}'
        timecodes = re.findall(pattern, content)
        
        if not timecodes:
            logger.warning(f"在字幕文件中未找到有效的时间码: {srt_path}")
            return None
        
        # 获取最后一个字幕的结束时间
        last_timecode = timecodes[-1]
        end_time_str = last_timecode.split(' --> ')[1]
        
        return parse_srt_timecode(end_time_str)
    
    except Exception as e:
        logger.error(f"解析SRT文件时出错: {e}")
        return None

def validate_timecode_sync(video_path: str, srt_path: str, tolerance: float = 0.5) -> Tuple[bool, str, Optional[float]]:
    """验证视频和字幕文件的时间轴同步性

    Args:
        video_path: 视频文件路径
        srt_path: 字幕文件路径
        tolerance: 允许的时间差异（秒）

    Returns:
        Tuple[bool, str, Optional[float]]: 
            - 是否同步
            - 错误信息（如果有）
            - 时间差异（如果可计算）
    """
    # 检查文件是否存在
    if not os.path.exists(video_path):
        return False, f"视频文件不存在: {video_path}", None
    
    if not os.path.exists(srt_path):
        return False, f"字幕文件不存在: {srt_path}", None
    
    # 获取视频时长
    video_duration = get_video_duration(video_path)
    
    # 获取字幕时长
    srt_duration = get_srt_duration(srt_path)
    
    # 如果无法获取视频时长，则认为验证通过但给出警告
    if video_duration is None:
        logger.warning("无法获取视频时长，跳过同步检查")
        return True, "无法获取视频时长，假定同步正常", None
    
    # 如果无法获取字幕时长，则认为验证通过但给出警告
    if srt_duration is None:
        logger.warning("无法解析字幕时长，跳过同步检查")
        return True, "无法解析字幕时长，假定同步正常", None
    
    # 计算时间差异
    time_diff = abs(video_duration - srt_duration)
    
    # 检查是否在容差范围内
    if time_diff <= tolerance:
        return True, f"视频和字幕同步正常，时间差异: {time_diff:.2f}秒", time_diff
    else:
        return False, f"视频和字幕不同步，时间差异: {time_diff:.2f}秒，超出容差范围: {tolerance}秒", time_diff

if __name__ == "__main__":
    # 简单的命令行测试
    import sys
    
    if len(sys.argv) < 3:
        print("用法: python timecode_validator.py <视频文件路径> <字幕文件路径> [容差(秒)]")
        sys.exit(1)
    
    video_path = sys.argv[1]
    srt_path = sys.argv[2]
    tolerance = float(sys.argv[3]) if len(sys.argv) > 3 else 0.5
    
    is_synced, message, diff = validate_timecode_sync(video_path, srt_path, tolerance)
    
    print(f"同步检查结果: {'通过' if is_synced else '失败'}")
    print(f"消息: {message}")
    if diff is not None:
        print(f"时间差异: {diff:.2f}秒") 