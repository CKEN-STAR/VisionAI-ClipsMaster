#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
时间轴转换模块

提供剪映时间轴格式转换功能，支持不同帧率和时间码格式的转换。
"""

import re
import datetime
import math
from typing import Dict, Any, List, Union, Tuple, Optional

from src.utils.logger import get_module_logger

# 初始化日志记录器
logger = get_module_logger("timeline_converter")

class TimelineConverter:
    """时间轴转换类"""
    
    def __init__(self, fps: float = 30.0):
        """
        初始化时间轴转换器
        
        Args:
            fps: 帧率，默认30fps
        """
        self.fps = fps
    
    def set_fps(self, fps: float) -> None:
        """
        设置帧率
        
        Args:
            fps: 帧率
        """
        self.fps = fps
    
    def seconds_to_frames(self, seconds: float) -> int:
        """
        秒转换为帧数
        
        Args:
            seconds: 秒数
            
        Returns:
            帧数
        """
        return round(seconds * self.fps)
    
    def frames_to_seconds(self, frames: int) -> float:
        """
        帧数转换为秒数
        
        Args:
            frames: 帧数
            
        Returns:
            秒数
        """
        return frames / self.fps
    
    def seconds_to_timecode(self, seconds: float) -> str:
        """
        秒数转换为时间码
        
        Args:
            seconds: 秒数
            
        Returns:
            时间码字符串 (HH:MM:SS:FF)
        """
        total_frames = self.seconds_to_frames(seconds)
        frames = total_frames % int(self.fps)
        
        total_seconds = int(seconds)
        s = total_seconds % 60
        m = (total_seconds // 60) % 60
        h = total_seconds // 3600
        
        return f"{h:02d}:{m:02d}:{s:02d}:{frames:02d}"
    
    def timecode_to_seconds(self, timecode: str) -> float:
        """
        时间码转换为秒数
        
        Args:
            timecode: 时间码字符串 (HH:MM:SS:FF 或 HH:MM:SS.sss)
            
        Returns:
            秒数
        """
        # 检查时间码格式
        if ":" in timecode:
            if timecode.count(":") == 3:
                # HH:MM:SS:FF 格式
                h, m, s, f = map(int, timecode.split(":"))
                return h * 3600 + m * 60 + s + f / self.fps
            elif timecode.count(":") == 2:
                # HH:MM:SS 格式
                h, m, s = map(int, timecode.split(":"))
                return h * 3600 + m * 60 + s
        elif "." in timecode:
            # 带小数点的秒数格式
            try:
                return float(timecode)
            except ValueError:
                logger.error(f"无效的时间码格式: {timecode}")
                return 0.0
        
        logger.error(f"无效的时间码格式: {timecode}")
        return 0.0
    
    def convert_timeline_data(self, timeline_data: Dict[str, Any], target_fps: float) -> Dict[str, Any]:
        """
        转换时间轴数据到目标帧率
        
        Args:
            timeline_data: 时间轴数据
            target_fps: 目标帧率
            
        Returns:
            转换后的时间轴数据
        """
        # 深拷贝时间轴数据
        import copy
        converted_data = copy.deepcopy(timeline_data)
        
        # 计算帧率比例
        fps_ratio = target_fps / self.fps
        
        # 更新时间轴属性
        if "attributes" in converted_data:
            converted_data["attributes"]["fps"] = str(target_fps)
        
        # 转换轨道
        if "tracks" in converted_data and isinstance(converted_data["tracks"], list):
            for track in converted_data["tracks"]:
                if "clips" in track and isinstance(track["clips"], list):
                    for clip in track["clips"]:
                        # 转换片段时间属性
                        if "start" in clip:
                            start_seconds = self.parse_time_value(clip["start"])
                            clip["start"] = str(start_seconds)
                        
                        if "duration" in clip:
                            duration_seconds = self.parse_time_value(clip["duration"])
                            clip["duration"] = str(duration_seconds)
                        
                        # 转换效果时间属性
                        if "effects" in clip and isinstance(clip["effects"], list):
                            for effect in clip["effects"]:
                                if "start" in effect:
                                    start_seconds = self.parse_time_value(effect["start"])
                                    effect["start"] = str(start_seconds)
                                
                                if "duration" in effect:
                                    duration_seconds = self.parse_time_value(effect["duration"])
                                    effect["duration"] = str(duration_seconds)
        
        # 设置当前帧率为目标帧率
        self.fps = target_fps
        
        return converted_data
    
    def parse_time_value(self, time_value: Union[str, float, int]) -> float:
        """
        解析时间值
        
        Args:
            time_value: 时间值（时间码字符串、秒数或帧数）
            
        Returns:
            秒数
        """
        if isinstance(time_value, (int, float)):
            return float(time_value)
        
        if isinstance(time_value, str):
            if ":" in time_value:
                return self.timecode_to_seconds(time_value)
            else:
                try:
                    return float(time_value)
                except ValueError:
                    logger.error(f"无效的时间值: {time_value}")
                    return 0.0
        
        logger.error(f"无效的时间值类型: {type(time_value)}")
        return 0.0
    
    def format_time_value(self, seconds: float, format_type: str = "seconds") -> str:
        """
        格式化时间值
        
        Args:
            seconds: 秒数
            format_type: 格式类型 ("seconds", "timecode", "frames")
            
        Returns:
            格式化的时间字符串
        """
        if format_type == "seconds":
            return f"{seconds:.3f}"
        elif format_type == "timecode":
            return self.seconds_to_timecode(seconds)
        elif format_type == "frames":
            frames = self.seconds_to_frames(seconds)
            return str(frames)
        else:
            logger.error(f"无效的格式类型: {format_type}")
            return f"{seconds:.3f}"
    
    def convert_markers(self, markers: List[Dict[str, Any]], source_fps: float, target_fps: float) -> List[Dict[str, Any]]:
        """
        转换标记点列表
        
        Args:
            markers: 标记点列表
            source_fps: 源帧率
            target_fps: 目标帧率
            
        Returns:
            转换后的标记点列表
        """
        # 临时保存当前帧率
        original_fps = self.fps
        
        # 设置源帧率
        self.fps = source_fps
        
        # 深拷贝标记点
        import copy
        converted_markers = copy.deepcopy(markers)
        
        # 转换每个标记点
        for marker in converted_markers:
            if "time" in marker:
                time_seconds = self.parse_time_value(marker["time"])
                
                # 设置目标帧率
                self.fps = target_fps
                
                # 转换为目标帧率下的时间
                if "format" in marker:
                    marker["time"] = self.format_time_value(time_seconds, marker["format"])
                else:
                    marker["time"] = self.format_time_value(time_seconds, "seconds")
        
        # 恢复原始帧率
        self.fps = original_fps
        
        return converted_markers


# 模块函数

def create_converter(fps: float = 30.0) -> TimelineConverter:
    """
    创建时间轴转换器
    
    Args:
        fps: 帧率
        
    Returns:
        时间轴转换器实例
    """
    return TimelineConverter(fps)

def convert_timeline(timeline_data: Dict[str, Any], source_fps: float, target_fps: float) -> Dict[str, Any]:
    """
    转换时间轴
    
    Args:
        timeline_data: 时间轴数据
        source_fps: 源帧率
        target_fps: 目标帧率
        
    Returns:
        转换后的时间轴数据
    """
    converter = TimelineConverter(source_fps)
    return converter.convert_timeline_data(timeline_data, target_fps)

def seconds_to_timecode(seconds: float, fps: float = 30.0) -> str:
    """
    秒数转换为时间码
    
    Args:
        seconds: 秒数
        fps: 帧率
        
    Returns:
        时间码字符串
    """
    converter = TimelineConverter(fps)
    return converter.seconds_to_timecode(seconds)

def timecode_to_seconds(timecode: str, fps: float = 30.0) -> float:
    """
    时间码转换为秒数
    
    Args:
        timecode: 时间码字符串
        fps: 帧率
        
    Returns:
        秒数
    """
    converter = TimelineConverter(fps)
    return converter.timecode_to_seconds(timecode)


if __name__ == "__main__":
    # 测试代码
    converter = TimelineConverter(30.0)
    
    # 测试时间转换
    test_seconds = 3723.5  # 1小时1分钟3秒15帧 (at 30fps)
    timecode = converter.seconds_to_timecode(test_seconds)
    print(f"{test_seconds} 秒 = {timecode}")
    
    back_seconds = converter.timecode_to_seconds(timecode)
    print(f"{timecode} = {back_seconds} 秒")
    
    # 测试时间轴转换
    timeline_data = {
        "attributes": {"fps": "30", "duration": "60.0"},
        "tracks": [
            {
                "type": "video",
                "clips": [
                    {
                        "start": "0.0",
                        "duration": "30.0",
                        "effects": [
                            {"start": "5.0", "duration": "10.0"}
                        ]
                    }
                ]
            }
        ]
    }
    
    converted = converter.convert_timeline_data(timeline_data, 24.0)
    print("转换后的时间轴数据:")
    print(converted) 