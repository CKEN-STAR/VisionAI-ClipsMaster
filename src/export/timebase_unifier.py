#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 跨平台时间基准处理模块

此模块提供用于处理不同编辑平台和操作系统之间时间基准差异的功能，确保导出的时间轴在不同平台上保持一致。

主要功能：
1. 不同平台时间基准的转换
2. 跨平台帧率适配
3. 时间码标准化
4. 平台特定时间处理的补偿
5. 时间基准差异检测和修正
"""

import math
import os
import platform
import logging
import json
from enum import Enum
from typing import Dict, List, Any, Optional, Union, Tuple, Callable

from src.utils.log_handler import get_logger
from src.export.fps_converter import (
    time_to_frames, 
    frames_to_time, 
    convert_frame_between_fps,
    RoundingMethod
)
from src.export.precision_compensator import compensate_rounding_error

# 配置日志
logger = get_logger("timebase_unifier")


class TimebaseStandard(Enum):
    """时间基准标准枚举"""
    MOVIE = "movie"        # 电影标准：24fps
    PAL = "pal"            # PAL制式：25fps
    NTSC = "ntsc"          # NTSC制式：29.97fps
    NTSC_DROP = "ntsc_drop" # NTSC丢帧：29.97fps带丢帧
    FILM = "film"          # 胶片标准：23.976fps
    DIGITAL = "digital"    # 数字标准：30fps
    WEB = "web"            # 网络标准：30fps或60fps
    CUSTOM = "custom"      # 自定义标准


class PlatformType(Enum):
    """平台类型枚举"""
    WINDOWS = "windows"
    MACOS = "macos"
    LINUX = "linux"
    IOS = "ios"
    ANDROID = "android"
    WEB = "web"
    

# 不同平台的默认时间基准
PLATFORM_TIMEBASE = {
    PlatformType.WINDOWS: TimebaseStandard.NTSC,
    PlatformType.MACOS: TimebaseStandard.NTSC,
    PlatformType.LINUX: TimebaseStandard.PAL,
    PlatformType.IOS: TimebaseStandard.DIGITAL,
    PlatformType.ANDROID: TimebaseStandard.DIGITAL,
    PlatformType.WEB: TimebaseStandard.WEB
}

# 不同时间基准的默认帧率
TIMEBASE_FPS = {
    TimebaseStandard.MOVIE: 24.0,
    TimebaseStandard.PAL: 25.0,
    TimebaseStandard.NTSC: 29.97,
    TimebaseStandard.NTSC_DROP: 29.97,
    TimebaseStandard.FILM: 23.976,
    TimebaseStandard.DIGITAL: 30.0,
    TimebaseStandard.WEB: 30.0,
    TimebaseStandard.CUSTOM: None  # 自定义需要指定
}

# 不同平台的时间精度差异
PLATFORM_TIME_PRECISION = {
    PlatformType.WINDOWS: 1000,  # 毫秒精度
    PlatformType.MACOS: 1000000,  # 微秒精度
    PlatformType.LINUX: 1000000,  # 微秒精度
    PlatformType.IOS: 1000000000,  # 纳秒精度
    PlatformType.ANDROID: 1000000,  # 微秒精度
    PlatformType.WEB: 1000  # 毫秒精度
}


def detect_platform() -> PlatformType:
    """检测当前运行平台
    
    根据操作系统类型检测当前平台类型。
    
    Returns:
        PlatformType: 检测到的平台类型
    """
    system = platform.system().lower()
    
    if 'windows' in system:
        return PlatformType.WINDOWS
    elif 'darwin' in system:
        return PlatformType.MACOS
    elif 'linux' in system:
        return PlatformType.LINUX
    elif 'ios' in system or ('darwin' in system and platform.machine() == 'arm64'):
        return PlatformType.IOS
    elif 'android' in system:
        return PlatformType.ANDROID
    else:
        # 默认返回Web平台，假设在浏览器中运行
        return PlatformType.WEB


def get_platform_timebase(platform_type: Optional[PlatformType] = None) -> Tuple[TimebaseStandard, float]:
    """获取指定平台的时间基准
    
    Args:
        platform_type: 平台类型，如果为None则检测当前平台
        
    Returns:
        Tuple[TimebaseStandard, float]: (时间基准标准, 对应帧率)
    """
    if platform_type is None:
        platform_type = detect_platform()
    
    timebase = PLATFORM_TIMEBASE.get(platform_type, TimebaseStandard.DIGITAL)
    fps = TIMEBASE_FPS.get(timebase, 30.0)
    
    return timebase, fps


def get_timebase_fps(timebase: TimebaseStandard, custom_fps: Optional[float] = None) -> float:
    """获取时间基准对应的帧率
    
    Args:
        timebase: 时间基准标准
        custom_fps: 自定义帧率，仅当timebase为CUSTOM时使用
        
    Returns:
        float: 对应的帧率
        
    Raises:
        ValueError: 如果timebase为CUSTOM但未指定custom_fps
    """
    if timebase == TimebaseStandard.CUSTOM:
        if custom_fps is None:
            raise ValueError("使用自定义时间基准时必须指定custom_fps")
        return float(custom_fps)
    
    return TIMEBASE_FPS.get(timebase, 30.0)


def convert_timebase(
    start: float, 
    end: float, 
    src_fps: float, 
    dst_fps: float
) -> Dict[str, float]:
    """处理不同帧率工程的时间基准统一
    
    将源帧率下的开始和结束时间转换为目标帧率下的对应时间。
    
    Args:
        start: 源帧率下的开始时间(秒)
        end: 源帧率下的结束时间(秒)
        src_fps: 源帧率
        dst_fps: 目标帧率
        
    Returns:
        Dict[str, float]: 包含转换后的开始和结束时间
    """
    # 计算缩放因子
    scale_factor = dst_fps / src_fps
    
    # 转换时间
    dst_start = round(start * scale_factor, 3)
    dst_end = round(end * scale_factor, 3)
    
    # 返回转换结果
    return {
        'start': dst_start,
        'end': dst_end
    }


def normalize_timecode(
    timecode: str, 
    src_timebase: TimebaseStandard,
    dst_timebase: TimebaseStandard,
    custom_src_fps: Optional[float] = None,
    custom_dst_fps: Optional[float] = None
) -> str:
    """标准化时间码
    
    将一种时间基准下的时间码转换为另一种时间基准下的时间码。
    
    Args:
        timecode: 源时间码字符串 (格式: "HH:MM:SS:FF" 或 "HH:MM:SS.mmm")
        src_timebase: 源时间基准
        dst_timebase: 目标时间基准
        custom_src_fps: 自定义源帧率，仅当src_timebase为CUSTOM时使用
        custom_dst_fps: 自定义目标帧率，仅当dst_timebase为CUSTOM时使用
        
    Returns:
        str: 转换后的时间码
    """
    from src.export.fps_converter import timecode_to_frames, frames_to_timecode
    
    # 获取源和目标帧率
    src_fps = get_timebase_fps(src_timebase, custom_src_fps)
    dst_fps = get_timebase_fps(dst_timebase, custom_dst_fps)
    
    # 将时间码转换为帧
    frames = timecode_to_frames(timecode, src_fps)
    
    # 计算在目标帧率下对应的帧数
    dst_frames = convert_frame_between_fps(frames, src_fps, dst_fps)
    
    # 将帧转换回时间码
    use_frames = True if dst_timebase in [TimebaseStandard.FILM, TimebaseStandard.MOVIE, 
                                         TimebaseStandard.NTSC, TimebaseStandard.NTSC_DROP] else False
    
    return frames_to_timecode(dst_frames, dst_fps, use_frames)


def adjust_for_platform_precision(
    time_value: float,
    source_platform: PlatformType,
    target_platform: PlatformType
) -> float:
    """调整时间值以适应目标平台的精度
    
    Args:
        time_value: 源平台的时间值（秒）
        source_platform: 源平台类型
        target_platform: 目标平台类型
        
    Returns:
        float: 调整后的时间值
    """
    # 获取源平台和目标平台的精度
    source_precision = PLATFORM_TIME_PRECISION.get(source_platform, 1000)
    target_precision = PLATFORM_TIME_PRECISION.get(target_platform, 1000)
    
    # 如果精度相同，无需调整
    if source_precision == target_precision:
        return time_value
    
    # 将时间值转换为整数（基于源平台精度）
    source_time_int = round(time_value * source_precision)
    
    # 调整为目标平台精度
    adjustment_factor = target_precision / source_precision
    target_time_int = round(source_time_int * adjustment_factor)
    
    # 转换回小数形式
    return target_time_int / target_precision


def unify_timeline_timebase(
    timeline_data: Dict[str, Any],
    target_timebase: TimebaseStandard,
    target_platform: Optional[PlatformType] = None,
    custom_fps: Optional[float] = None
) -> Dict[str, Any]:
    """统一时间轴的时间基准
    
    将时间轴数据转换为指定时间基准和平台。
    
    Args:
        timeline_data: 时间轴数据
        target_timebase: 目标时间基准
        target_platform: 目标平台，如果为None则使用当前平台
        custom_fps: 自定义帧率，仅当target_timebase为CUSTOM时使用
        
    Returns:
        Dict[str, Any]: 转换后的时间轴数据
    """
    # 深拷贝以避免修改原数据
    import copy
    result = copy.deepcopy(timeline_data)
    
    # 获取源帧率
    source_fps = result.get('fps', 30.0)
    
    # 获取目标帧率
    target_fps = get_timebase_fps(target_timebase, custom_fps)
    
    # 获取目标平台
    if target_platform is None:
        target_platform = detect_platform()
    
    # 更新时间轴的帧率
    result['original_fps'] = source_fps
    result['fps'] = target_fps
    result['timebase'] = target_timebase.value
    result['target_platform'] = target_platform.value
    
    # 遍历并转换所有时间值
    if 'clips' in result and isinstance(result['clips'], list):
        for clip in result['clips']:
            # 转换基于帧的属性
            for key in ['start_frame', 'end_frame']:
                if key in clip:
                    # 先转换为时间
                    time_value = frames_to_time(clip[key], source_fps)
                    # 再转换回目标帧率下的帧
                    clip[key] = time_to_frames(time_value, target_fps)
            
            # 转换基于时间的属性
            for key in ['start_time', 'end_time', 'duration']:
                if key in clip:
                    # 调整时间值
                    original_platform = result.get('source_platform', detect_platform().value)
                    clip[key] = adjust_for_platform_precision(
                        clip[key],
                        PlatformType(original_platform),
                        target_platform
                    )
                    
    # 处理轨道数据
    if 'tracks' in result and isinstance(result['tracks'], list):
        for track in result['tracks']:
            if 'items' in track and isinstance(track['items'], list):
                for item in track['items']:
                    # 转换基于帧的属性
                    for key in ['start_frame', 'end_frame']:
                        if key in item:
                            time_value = frames_to_time(item[key], source_fps)
                            item[key] = time_to_frames(time_value, target_fps)
                    
                    # 转换基于时间的属性
                    for key in ['start_time', 'end_time', 'duration']:
                        if key in item:
                            original_platform = result.get('source_platform', detect_platform().value)
                            item[key] = adjust_for_platform_precision(
                                item[key],
                                PlatformType(original_platform),
                                target_platform
                            )
    
    # 补偿剪辑边界的舍入误差
    result = compensate_timeline_boundaries(result)
    
    return result


def compensate_timeline_boundaries(timeline_data: Dict[str, Any]) -> Dict[str, Any]:
    """补偿时间轴边界舍入误差
    
    确保时间轴中的片段边界在转换后不会出现缝隙或重叠。
    
    Args:
        timeline_data: 时间轴数据
        
    Returns:
        Dict[str, Any]: 补偿后的时间轴数据
    """
    # 深拷贝以避免修改原数据
    import copy
    result = copy.deepcopy(timeline_data)
    fps = result.get('fps', 30.0)
    
    # 处理剪辑列表
    if 'clips' in result and isinstance(result['clips'], list):
        # 按开始时间排序
        clips = sorted(result['clips'], key=lambda x: x.get('start_frame', 0))
        
        # 检查并修复相邻剪辑之间的间隙或重叠
        for i in range(1, len(clips)):
            prev_clip = clips[i-1]
            curr_clip = clips[i]
            
            prev_end = prev_clip.get('end_frame', 0)
            curr_start = curr_clip.get('start_frame', 0)
            
            # 如果存在间隙，扩展前一个剪辑的结束时间
            if curr_start > prev_end:
                # 计算差距
                gap = curr_start - prev_end
                # 如果差距小于阈值（例如1帧），调整前一个剪辑的结束时间
                if gap == 1:
                    prev_clip['end_frame'] = curr_start
                    if 'end_time' in prev_clip:
                        prev_clip['end_time'] = frames_to_time(curr_start, fps)
            
            # 如果存在重叠，调整当前剪辑的开始时间
            elif curr_start < prev_end:
                # 计算重叠量
                overlap = prev_end - curr_start
                # 如果重叠小于阈值，调整当前剪辑的开始时间
                if overlap == 1:
                    curr_clip['start_frame'] = prev_end
                    if 'start_time' in curr_clip:
                        curr_clip['start_time'] = frames_to_time(prev_end, fps)
    
    # 处理轨道列表
    if 'tracks' in result and isinstance(result['tracks'], list):
        for track in result['tracks']:
            if 'items' in track and isinstance(track['items'], list):
                # 按开始时间排序
                items = sorted(track['items'], key=lambda x: x.get('start_frame', 0))
                
                # 检查并修复相邻项之间的间隙或重叠
                for i in range(1, len(items)):
                    prev_item = items[i-1]
                    curr_item = items[i]
                    
                    prev_end = prev_item.get('end_frame', 0)
                    curr_start = curr_item.get('start_frame', 0)
                    
                    # 处理间隙
                    if curr_start > prev_end:
                        gap = curr_start - prev_end
                        if gap == 1:
                            prev_item['end_frame'] = curr_start
                            if 'end_time' in prev_item:
                                prev_item['end_time'] = frames_to_time(curr_start, fps)
                    
                    # 处理重叠
                    elif curr_start < prev_end:
                        overlap = prev_end - curr_start
                        if overlap == 1:
                            curr_item['start_frame'] = prev_end
                            if 'start_time' in curr_item:
                                curr_item['start_time'] = frames_to_time(prev_end, fps)
    
    return result


def convert_timing_values(
    timing_data: Dict[str, Union[int, float]],
    src_fps: float,
    dst_fps: float
) -> Dict[str, Union[int, float]]:
    """转换时间相关数值
    
    将一组时间相关的数值从源帧率转换为目标帧率。
    
    Args:
        timing_data: 包含时间相关数值的字典
        src_fps: 源帧率
        dst_fps: 目标帧率
        
    Returns:
        Dict[str, Union[int, float]]: 转换后的时间数值字典
    """
    result = {}
    
    # 确定哪些键是基于帧的，哪些是基于时间的
    frame_keys = ['start_frame', 'end_frame', 'duration_frames', 'position', 'offset']
    time_keys = ['start_time', 'end_time', 'duration']
    
    # 转换基于帧的数值
    for key, value in timing_data.items():
        if key in frame_keys and isinstance(value, (int, float)):
            # 先转换为时间
            time_value = frames_to_time(value, src_fps)
            # 再转换为目标帧率下的帧
            result[key] = time_to_frames(time_value, dst_fps)
        elif key in time_keys and isinstance(value, (int, float)):
            # 基于时间的值乘以比例因子
            scale_factor = dst_fps / src_fps
            result[key] = value * scale_factor
        else:
            # 其他值直接保留
            result[key] = value
    
    return result


def detect_and_fix_timebase_issues(timeline_data: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    """检测并修复时间基准问题
    
    分析时间轴数据，检测可能的时间基准问题并尝试修复。
    
    Args:
        timeline_data: 时间轴数据
        
    Returns:
        Tuple[Dict[str, Any], List[str]]: (修复后的时间轴数据, 问题和修复日志)
    """
    # 深拷贝以避免修改原数据
    import copy
    result = copy.deepcopy(timeline_data)
    logs = []
    
    # 检查帧率是否合理
    fps = result.get('fps', 30.0)
    if fps <= 0 or fps > 1000:
        new_fps = 30.0
        logs.append(f"检测到异常帧率: {fps}，已修正为: {new_fps}")
        result['fps'] = new_fps
        fps = new_fps
    
    # 检查时长是否合理
    if 'duration' in result:
        duration = result['duration']
        if duration < 0:
            result['duration'] = 0
            logs.append(f"检测到负时长: {duration}，已修正为0")
        elif duration > 86400:  # 超过24小时
            logs.append(f"警告: 时长超过24小时: {duration}")
    
    # 检查剪辑的起止时间是否合理
    if 'clips' in result and isinstance(result['clips'], list):
        for i, clip in enumerate(result['clips']):
            if 'start_frame' in clip and 'end_frame' in clip:
                start = clip['start_frame']
                end = clip['end_frame']
                
                # 确保开始时间不大于结束时间
                if start > end:
                    clip['start_frame'], clip['end_frame'] = end, start
                    logs.append(f"剪辑 {i} 的起止时间颠倒，已修正")
                
                # 确保时长不为零
                if start == end:
                    clip['end_frame'] = start + 1
                    logs.append(f"剪辑 {i} 时长为零，已调整为1帧")
    
    # 检查轨道项的起止时间
    if 'tracks' in result and isinstance(result['tracks'], list):
        for t_idx, track in enumerate(result['tracks']):
            if 'items' in track and isinstance(track['items'], list):
                for i_idx, item in enumerate(track['items']):
                    if 'start_frame' in item and 'end_frame' in item:
                        start = item['start_frame']
                        end = item['end_frame']
                        
                        # 确保开始时间不大于结束时间
                        if start > end:
                            item['start_frame'], item['end_frame'] = end, start
                            logs.append(f"轨道 {t_idx} 项目 {i_idx} 的起止时间颠倒，已修正")
                        
                        # 确保时长不为零
                        if start == end:
                            item['end_frame'] = start + 1
                            logs.append(f"轨道 {t_idx} 项目 {i_idx} 时长为零，已调整为1帧")
    
    # 如果有修复操作，重新计算相关的时间值
    if logs:
        # 更新clip的时间值
        if 'clips' in result and isinstance(result['clips'], list):
            for clip in result['clips']:
                if 'start_frame' in clip and 'end_frame' in clip:
                    # 重新计算时间
                    clip['start_time'] = frames_to_time(clip['start_frame'], fps)
                    clip['end_time'] = frames_to_time(clip['end_frame'], fps)
                    clip['duration'] = clip['end_time'] - clip['start_time']
        
        # 更新track项的时间值
        if 'tracks' in result and isinstance(result['tracks'], list):
            for track in result['tracks']:
                if 'items' in track and isinstance(track['items'], list):
                    for item in track['items']:
                        if 'start_frame' in item and 'end_frame' in item:
                            # 重新计算时间
                            item['start_time'] = frames_to_time(item['start_frame'], fps)
                            item['end_time'] = frames_to_time(item['end_frame'], fps)
                            item['duration'] = item['end_time'] - item['start_time']
    
    return result, logs


# 测试函数
def test_timebase_unifier():
    """测试时间基准统一功能"""
    # 测试简单的时间基准转换
    result = convert_timebase(1.0, 2.0, 24.0, 30.0)
    print(f"将1-2秒从24fps转换到30fps: {result}")
    
    # 测试时间码标准化
    tc = normalize_timecode("00:00:10:00", TimebaseStandard.MOVIE, TimebaseStandard.PAL)
    print(f"将电影标准的10秒时间码转换为PAL标准: {tc}")
    
    # 创建一个测试时间轴
    test_timeline = {
        "fps": 24.0,
        "duration": 10.0,
        "clips": [
            {"start_frame": 24, "end_frame": 72, "start_time": 1.0, "end_time": 3.0},
            {"start_frame": 96, "end_frame": 144, "start_time": 4.0, "end_time": 6.0}
        ],
        "tracks": [
            {
                "items": [
                    {"start_frame": 24, "end_frame": 72, "start_time": 1.0, "end_time": 3.0},
                    {"start_frame": 96, "end_frame": 144, "start_time": 4.0, "end_time": 6.0}
                ]
            }
        ]
    }
    
    # 测试时间轴转换
    unified = unify_timeline_timebase(test_timeline, TimebaseStandard.PAL)
    print("将24fps时间轴转换为PAL标准:")
    print(json.dumps(unified, indent=2))
    
    # 测试检测和修复
    test_timeline_broken = {
        "fps": 24.0,
        "duration": -1.0,
        "clips": [
            {"start_frame": 72, "end_frame": 24, "start_time": 3.0, "end_time": 1.0},
            {"start_frame": 96, "end_frame": 96, "start_time": 4.0, "end_time": 4.0}
        ]
    }
    
    fixed, logs = detect_and_fix_timebase_issues(test_timeline_broken)
    print("修复的时间轴:")
    print(json.dumps(fixed, indent=2))
    print("修复日志:")
    for log in logs:
        print(f"- {log}")


if __name__ == "__main__":
    # 运行测试
    test_timebase_unifier() 