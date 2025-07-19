#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SRT时间码解析器

提供专门针对SRT格式时间码的解析功能，支持将SRT格式时间码转换为秒数
"""

import re
from typing import Tuple, Union, Optional

def parse_srt_time(time_str: str) -> float:
    """
    将SRT格式时间码字符串转换为秒数
    
    Args:
        time_str: SRT格式时间码字符串，格式为 "00:01:23,456" 或 "00:01:23.456"
        
    Returns:
        float: 转换后的秒数，例如 "00:01:23,456" 返回 83.456
        
    Raises:
        ValueError: 无法解析的时间码格式
    """
    # 支持逗号或点作为毫秒分隔符
    time_str = time_str.strip().replace(',', '.')
    
    # 使用正则表达式匹配 HH:MM:SS.mmm 格式
    pattern = r'(\d{2,}):(\d{2}):(\d{2})\.(\d{1,3})'
    match = re.match(pattern, time_str)
    
    if not match:
        raise ValueError(f"无法解析的SRT时间码格式: {time_str}")
    
    # 提取小时、分钟、秒和毫秒
    h, m, s, ms = match.groups()
    
    # 将毫秒标准化为3位数
    ms = ms.ljust(3, '0')[:3]
    
    # 计算总秒数
    total_seconds = int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000
    
    return total_seconds

def format_srt_time(seconds: float) -> str:
    """
    将秒数转换为SRT格式时间码字符串
    
    Args:
        seconds: 秒数，可以是整数或浮点数
        
    Returns:
        str: SRT格式时间码字符串，格式为 "00:01:23,456"
    """
    # 确保输入是非负数
    if seconds < 0:
        raise ValueError("时间不能为负数")
    
    # 计算小时、分钟、秒和毫秒
    hours = int(seconds // 3600)
    seconds %= 3600
    minutes = int(seconds // 60)
    seconds %= 60
    whole_seconds = int(seconds)
    
    # 确保毫秒部分的精确转换，避免浮点数舍入误差
    # 先乘以1000，然后四舍五入到整数
    milliseconds = round((seconds - whole_seconds) * 1000)
    
    # 处理毫秒进位
    if milliseconds == 1000:
        milliseconds = 0
        whole_seconds += 1
        
        # 处理秒数进位
        if whole_seconds == 60:
            whole_seconds = 0
            minutes += 1
            
            # 处理分钟进位
            if minutes == 60:
                minutes = 0
                hours += 1
    
    # 格式化为SRT时间码
    return f"{hours:02d}:{minutes:02d}:{whole_seconds:02d},{milliseconds:03d}"

def parse_srt_timerange(timerange_str: str) -> Tuple[float, float]:
    """
    解析SRT时间范围字符串，格式为 "00:01:23,456 --> 00:01:26,789"
    
    Args:
        timerange_str: SRT格式时间范围字符串
        
    Returns:
        Tuple[float, float]: 包含开始和结束时间的元组(秒)
        
    Raises:
        ValueError: 无法解析的时间范围格式
    """
    # 分割时间范围
    parts = timerange_str.split('-->')
    if len(parts) != 2:
        raise ValueError(f"无法解析的SRT时间范围格式: {timerange_str}")
    
    # 解析开始和结束时间
    start_time = parse_srt_time(parts[0].strip())
    end_time = parse_srt_time(parts[1].strip())
    
    return (start_time, end_time)

def calculate_duration(start_time: Union[str, float], end_time: Union[str, float]) -> float:
    """
    计算两个时间点之间的持续时间
    
    Args:
        start_time: 开始时间，可以是SRT格式字符串或秒数
        end_time: 结束时间，可以是SRT格式字符串或秒数
        
    Returns:
        float: 持续时间(秒)
        
    Raises:
        ValueError: 无法解析的时间格式或结束时间早于开始时间
    """
    # 将输入转换为秒数
    if isinstance(start_time, str):
        start_seconds = parse_srt_time(start_time)
    else:
        start_seconds = float(start_time)
    
    if isinstance(end_time, str):
        end_seconds = parse_srt_time(end_time)
    else:
        end_seconds = float(end_time)
    
    # 计算持续时间
    duration = end_seconds - start_seconds
    
    # 验证持续时间是否为正数
    if duration < 0:
        raise ValueError(f"结束时间({end_time})早于开始时间({start_time})")
    
    return duration

def adjust_srt_time(time_str: str, offset_seconds: float) -> str:
    """
    调整SRT时间码，增加或减少指定的秒数
    
    Args:
        time_str: SRT格式时间码字符串
        offset_seconds: 偏移量(秒)，正数表示延后，负数表示提前
        
    Returns:
        str: 调整后的SRT格式时间码字符串
        
    Raises:
        ValueError: 无法解析的时间码格式或调整后时间为负
    """
    # 解析时间码为秒数
    seconds = parse_srt_time(time_str)
    
    # 应用偏移量
    adjusted_seconds = seconds + offset_seconds
    
    # 验证结果是否为正数
    if adjusted_seconds < 0:
        raise ValueError(f"调整后时间为负: {time_str} + {offset_seconds}s = {adjusted_seconds}s")
    
    # 转换回SRT格式
    return format_srt_time(adjusted_seconds)

def adjust_srt_timerange(timerange_str: str, offset_seconds: float) -> str:
    """
    调整SRT时间范围，增加或减少指定的秒数
    
    Args:
        timerange_str: SRT格式时间范围字符串
        offset_seconds: 偏移量(秒)，正数表示延后，负数表示提前
        
    Returns:
        str: 调整后的SRT格式时间范围字符串
        
    Raises:
        ValueError: 无法解析的时间范围格式或调整后时间为负
    """
    # 分割时间范围
    parts = timerange_str.split('-->')
    if len(parts) != 2:
        raise ValueError(f"无法解析的SRT时间范围格式: {timerange_str}")
    
    # 调整开始和结束时间
    adjusted_start = adjust_srt_time(parts[0].strip(), offset_seconds)
    adjusted_end = adjust_srt_time(parts[1].strip(), offset_seconds)
    
    # 重新组合时间范围
    return f"{adjusted_start} --> {adjusted_end}"

def is_valid_srt_time(time_str: str) -> bool:
    """
    检查字符串是否为有效的SRT时间码格式
    
    Args:
        time_str: 要检查的字符串
        
    Returns:
        bool: 是否为有效的SRT时间码格式
    """
    try:
        parse_srt_time(time_str)
        return True
    except ValueError:
        return False 