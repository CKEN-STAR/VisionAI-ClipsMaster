"""
VisionAI-ClipsMaster 时间轴解析器

此模块提供精确的时间码解析和转换功能，支持多种格式的时间码处理，
并提供毫秒级精度的时间计算、比较和规范化功能。

支持的时间码格式：
- SRT格式: 00:12:34,567
- 标准格式: 00:12:34.567
- 帧率格式: 00:12:34:25 (基于帧率)
- 时间戳: 754.567 (秒)
"""

import re
from dataclasses import dataclass
from typing import Dict, List, Tuple, Union, Optional

class TimeCodeError(Exception):
    """时间码处理过程中的错误基类"""
    pass

@dataclass
class TimeCode:
    """时间码数据结构，支持精确到毫秒的时间表示"""
    hours: int = 0
    minutes: int = 0
    seconds: int = 0
    milliseconds: int = 0
    
    def __post_init__(self):
        """验证时间码字段的有效性"""
        if not 0 <= self.hours <= 99:
            raise TimeCodeError(f"小时必须在0-99范围内，当前值: {self.hours}")
        if not 0 <= self.minutes <= 59:
            raise TimeCodeError(f"分钟必须在0-59范围内，当前值: {self.minutes}")
        if not 0 <= self.seconds <= 59:
            raise TimeCodeError(f"秒必须在0-59范围内，当前值: {self.seconds}")
        if not 0 <= self.milliseconds <= 999:
            raise TimeCodeError(f"毫秒必须在0-999范围内，当前值: {self.milliseconds}")
    
    def to_milliseconds(self) -> int:
        """将时间码转换为总毫秒数"""
        return (self.hours * 3600000 + 
                self.minutes * 60000 + 
                self.seconds * 1000 + 
                self.milliseconds)
    
    def to_seconds(self) -> float:
        """将时间码转换为总秒数（浮点数）"""
        return self.to_milliseconds() / 1000.0
    
    def to_srt_format(self) -> str:
        """输出SRT格式的时间码字符串: 00:12:34,567"""
        return f"{self.hours:02d}:{self.minutes:02d}:{self.seconds:02d},{self.milliseconds:03d}"
    
    def to_standard_format(self) -> str:
        """输出标准格式的时间码字符串: 00:12:34.567"""
        return f"{self.hours:02d}:{self.minutes:02d}:{self.seconds:02d}.{self.milliseconds:03d}"
    
    def to_frame_format(self, fps: float = 25.0) -> str:
        """输出基于帧率的时间码字符串: 00:12:34:25"""
        frames = int(self.milliseconds / 1000 * fps)
        return f"{self.hours:02d}:{self.minutes:02d}:{self.seconds:02d}:{frames:02d}"
    
    def __add__(self, other):
        """时间码加法运算"""
        if isinstance(other, TimeCode):
            total_ms = self.to_milliseconds() + other.to_milliseconds()
            return TimeCode.from_milliseconds(total_ms)
        elif isinstance(other, (int, float)):
            # 假设添加的是毫秒
            return TimeCode.from_milliseconds(self.to_milliseconds() + int(other))
        else:
            raise TypeError(f"不支持的操作数类型: {type(other)}")
    
    def __sub__(self, other):
        """时间码减法运算"""
        if isinstance(other, TimeCode):
            total_ms = self.to_milliseconds() - other.to_milliseconds()
            if total_ms < 0:
                raise TimeCodeError("时间码减法结果不能为负")
            return TimeCode.from_milliseconds(total_ms)
        elif isinstance(other, (int, float)):
            # 假设减去的是毫秒
            result_ms = self.to_milliseconds() - int(other)
            if result_ms < 0:
                raise TimeCodeError("时间码减法结果不能为负")
            return TimeCode.from_milliseconds(result_ms)
        else:
            raise TypeError(f"不支持的操作数类型: {type(other)}")
    
    def __lt__(self, other):
        """小于比较运算符"""
        if isinstance(other, TimeCode):
            return self.to_milliseconds() < other.to_milliseconds()
        elif isinstance(other, (int, float)):
            return self.to_milliseconds() < int(other)
        else:
            raise TypeError(f"不支持的操作数类型: {type(other)}")
    
    def __le__(self, other):
        """小于等于比较运算符"""
        if isinstance(other, TimeCode):
            return self.to_milliseconds() <= other.to_milliseconds()
        elif isinstance(other, (int, float)):
            return self.to_milliseconds() <= int(other)
        else:
            raise TypeError(f"不支持的操作数类型: {type(other)}")
    
    def __gt__(self, other):
        """大于比较运算符"""
        if isinstance(other, TimeCode):
            return self.to_milliseconds() > other.to_milliseconds()
        elif isinstance(other, (int, float)):
            return self.to_milliseconds() > int(other)
        else:
            raise TypeError(f"不支持的操作数类型: {type(other)}")
    
    def __ge__(self, other):
        """大于等于比较运算符"""
        if isinstance(other, TimeCode):
            return self.to_milliseconds() >= other.to_milliseconds()
        elif isinstance(other, (int, float)):
            return self.to_milliseconds() >= int(other)
        else:
            raise TypeError(f"不支持的操作数类型: {type(other)}")
    
    def __eq__(self, other):
        """等于比较运算符"""
        if isinstance(other, TimeCode):
            return self.to_milliseconds() == other.to_milliseconds()
        elif isinstance(other, (int, float)):
            return self.to_milliseconds() == int(other)
        else:
            return False
    
    @classmethod
    def from_milliseconds(cls, milliseconds: int) -> 'TimeCode':
        """从总毫秒数创建时间码对象"""
        if milliseconds < 0:
            raise TimeCodeError(f"毫秒数不能为负: {milliseconds}")
        
        hours = milliseconds // 3600000
        milliseconds %= 3600000
        minutes = milliseconds // 60000
        milliseconds %= 60000
        seconds = milliseconds // 1000
        milliseconds %= 1000
        
        return cls(hours=hours, minutes=minutes, seconds=seconds, milliseconds=milliseconds)
    
    @classmethod
    def from_seconds(cls, seconds: float) -> 'TimeCode':
        """从总秒数创建时间码对象"""
        if seconds < 0:
            raise TimeCodeError(f"秒数不能为负: {seconds}")
        
        return cls.from_milliseconds(int(seconds * 1000))


def parse_timecode(tc_str: str) -> TimeCode:
    """
    解析时间码字符串，支持多种格式
    
    输入格式:
        - SRT格式: 00:12:34,567
        - 标准格式: 00:12:34.567
        - 时间戳: 754.567 (秒)
        - 范围格式: 00:12:34,567 --> 00:12:36,890
        
    返回:
        TimeCode: 解析后的时间码对象
    """
    # 清理输入字符串
    tc_str = tc_str.strip()
    
    # 如果是范围格式，只取第一部分
    if '-->' in tc_str:
        tc_str = tc_str.split('-->')[0].strip()
    
    # 使用正则表达式判断格式类型并解析
    # SRT格式: 00:12:34,567
    srt_pattern = r'^(\d{2}):(\d{2}):(\d{2}),(\d{3})$'
    match = re.match(srt_pattern, tc_str)
    if match:
        h, m, s, ms = map(int, match.groups())
        return TimeCode(hours=h, minutes=m, seconds=s, milliseconds=ms)
    
    # 标准格式: 00:12:34.567
    std_pattern = r'^(\d{2}):(\d{2}):(\d{2})\.(\d{3})$'
    match = re.match(std_pattern, tc_str)
    if match:
        h, m, s, ms = map(int, match.groups())
        return TimeCode(hours=h, minutes=m, seconds=s, milliseconds=ms)
    
    # 帧率格式: 00:12:34:25 (基于帧率)
    frame_pattern = r'^(\d{2}):(\d{2}):(\d{2}):(\d{2})$'
    match = re.match(frame_pattern, tc_str)
    if match:
        h, m, s, frames = map(int, match.groups())
        # 默认使用25fps将帧转换为毫秒
        ms = int(frames / 25 * 1000)
        return TimeCode(hours=h, minutes=m, seconds=s, milliseconds=ms)
    
    # 时间戳格式: 754.567
    timestamp_pattern = r'^(\d+)\.(\d+)$'
    match = re.match(timestamp_pattern, tc_str)
    if match:
        seconds, fractional = match.groups()
        # 根据小数位数调整毫秒值
        if len(fractional) == 3:
            ms = int(fractional)
        else:
            ms = int(fractional) * 10 ** (3 - len(fractional)) if len(fractional) < 3 else int(fractional) // 10 ** (len(fractional) - 3)
        
        total_seconds = int(seconds)
        h = total_seconds // 3600
        m = (total_seconds % 3600) // 60
        s = total_seconds % 60
        
        return TimeCode(hours=h, minutes=m, seconds=s, milliseconds=ms)
    
    # 纯数字格式（毫秒）: 754567
    if tc_str.isdigit():
        return TimeCode.from_milliseconds(int(tc_str))
    
    raise TimeCodeError(f"无法识别的时间码格式: {tc_str}")


def parse_timecode_range(tc_range: str) -> Dict[str, TimeCode]:
    """
    解析时间码范围，例如SRT格式的时间范围
    
    输入格式:
        00:12:34,567 --> 00:12:36,890
        
    返回:
        Dict: 包含'start'和'end'的时间码对象
    """
    # 标准SRT时间码范围格式
    pattern = r'(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})'
    match = re.match(pattern, tc_range)
    
    if not match:
        # 尝试标准格式（使用点而非逗号）
        pattern = r'(\d{2}:\d{2}:\d{2}\.\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}\.\d{3})'
        match = re.match(pattern, tc_range)
    
    if not match:
        raise TimeCodeError(f"无法识别的时间码范围格式: {tc_range}")
    
    start_str, end_str = match.groups()
    
    return {
        'start': parse_timecode(start_str),
        'end': parse_timecode(end_str)
    }


def adjust_timecode(timecode: TimeCode, offset_ms: int) -> TimeCode:
    """
    调整时间码，可以是正偏移或负偏移
    
    参数:
        timecode: 要调整的时间码对象
        offset_ms: 偏移量（毫秒），正值向后调整，负值向前调整
        
    返回:
        调整后的时间码对象
    """
    total_ms = timecode.to_milliseconds() + offset_ms
    if total_ms < 0:
        total_ms = 0
    
    return TimeCode.from_milliseconds(total_ms)


def calculate_duration(start: TimeCode, end: TimeCode) -> int:
    """
    计算两个时间码之间的持续时间（毫秒）
    
    参数:
        start: 起始时间码
        end: 结束时间码
        
    返回:
        持续时间（毫秒）
    """
    if end < start:
        raise TimeCodeError("结束时间不能早于起始时间")
    
    return end.to_milliseconds() - start.to_milliseconds() 