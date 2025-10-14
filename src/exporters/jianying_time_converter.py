"""
剪映时间转换器
统一处理时间单位转换，确保精度
"""

import re
from typing import Union, Optional
from dataclasses import dataclass


@dataclass
class Timerange:
    """时间范围类（微秒）"""
    start: int
    """开始时间（微秒）"""
    duration: int
    """持续时间（微秒）"""
    
    @property
    def end(self) -> int:
        """结束时间（微秒）"""
        return self.start + self.duration
    
    def __repr__(self) -> str:
        return f"Timerange(start={self.start}μs, duration={self.duration}μs, end={self.end}μs)"


class TimeConverter:
    """时间转换器 - 统一时间单位处理"""
    
    # 时间单位转换常量
    MICROSECONDS_PER_SECOND = 1_000_000
    MICROSECONDS_PER_MILLISECOND = 1_000
    
    @staticmethod
    def seconds_to_microseconds(seconds: float) -> int:
        """
        秒转微秒
        
        Args:
            seconds: 秒数（可以是小数）
            
        Returns:
            微秒数（整数）
        """
        return round(seconds * TimeConverter.MICROSECONDS_PER_SECOND)
    
    @staticmethod
    def milliseconds_to_microseconds(milliseconds: float) -> int:
        """
        毫秒转微秒
        
        Args:
            milliseconds: 毫秒数（可以是小数）
            
        Returns:
            微秒数（整数）
        """
        return round(milliseconds * TimeConverter.MICROSECONDS_PER_MILLISECOND)
    
    @staticmethod
    def microseconds_to_seconds(microseconds: int) -> float:
        """
        微秒转秒
        
        Args:
            microseconds: 微秒数
            
        Returns:
            秒数（浮点数）
        """
        return microseconds / TimeConverter.MICROSECONDS_PER_SECOND
    
    @staticmethod
    def microseconds_to_milliseconds(microseconds: int) -> float:
        """
        微秒转毫秒
        
        Args:
            microseconds: 微秒数
            
        Returns:
            毫秒数（浮点数）
        """
        return microseconds / TimeConverter.MICROSECONDS_PER_MILLISECOND
    
    @staticmethod
    def parse_srt_timestamp(timestamp: str) -> int:
        """
        解析SRT时间戳格式 (HH:MM:SS,mmm) 为微秒
        
        Args:
            timestamp: SRT时间戳字符串，格式如 "00:01:23,456"
            
        Returns:
            微秒数
            
        Raises:
            ValueError: 时间戳格式不正确
        """
        # 匹配 HH:MM:SS,mmm 或 HH:MM:SS.mmm 格式
        pattern = r'(\d{1,2}):(\d{2}):(\d{2})[,.](\d{3})'
        match = re.match(pattern, timestamp.strip())
        
        if not match:
            raise ValueError(f"无效的SRT时间戳格式: {timestamp}")
        
        hours, minutes, seconds, milliseconds = map(int, match.groups())
        
        # 转换为微秒
        total_microseconds = (
            hours * 3600 * TimeConverter.MICROSECONDS_PER_SECOND +
            minutes * 60 * TimeConverter.MICROSECONDS_PER_SECOND +
            seconds * TimeConverter.MICROSECONDS_PER_SECOND +
            milliseconds * TimeConverter.MICROSECONDS_PER_MILLISECOND
        )
        
        return total_microseconds
    
    @staticmethod
    def format_to_srt_timestamp(microseconds: int) -> str:
        """
        将微秒转换为SRT时间戳格式
        
        Args:
            microseconds: 微秒数
            
        Returns:
            SRT时间戳字符串，格式如 "00:01:23,456"
        """
        total_seconds = microseconds // TimeConverter.MICROSECONDS_PER_SECOND
        milliseconds = (microseconds % TimeConverter.MICROSECONDS_PER_SECOND) // TimeConverter.MICROSECONDS_PER_MILLISECOND
        
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"
    
    @staticmethod
    def tim(time_str: Union[str, int, float]) -> int:
        """
        智能时间解析函数（兼容pyCapCut的tim函数）
        
        支持的格式：
        - 整数/浮点数：视为秒
        - "1.5s" 或 "1.5"：秒
        - "1500ms"：毫秒
        - "00:01:23,456"：SRT格式
        
        Args:
            time_str: 时间字符串或数值
            
        Returns:
            微秒数
        """
        if isinstance(time_str, int):
            # 如果已经是整数，判断是否是微秒级别
            if time_str > 1_000_000_000:  # 大于1000秒，认为是微秒
                return time_str
            else:  # 否则认为是秒
                return TimeConverter.seconds_to_microseconds(time_str)
        
        if isinstance(time_str, float):
            # 浮点数视为秒
            return TimeConverter.seconds_to_microseconds(time_str)
        
        if isinstance(time_str, str):
            time_str = time_str.strip()
            
            # SRT格式
            if ':' in time_str:
                return TimeConverter.parse_srt_timestamp(time_str)
            
            # 毫秒格式
            if time_str.endswith('ms'):
                ms_value = float(time_str[:-2])
                return TimeConverter.milliseconds_to_microseconds(ms_value)
            
            # 秒格式（带或不带's'后缀）
            if time_str.endswith('s'):
                s_value = float(time_str[:-1])
                return TimeConverter.seconds_to_microseconds(s_value)
            
            # 纯数字字符串，视为秒
            try:
                s_value = float(time_str)
                return TimeConverter.seconds_to_microseconds(s_value)
            except ValueError:
                raise ValueError(f"无法解析时间字符串: {time_str}")
        
        raise TypeError(f"不支持的时间类型: {type(time_str)}")
    
    @staticmethod
    def create_timerange(start: Union[str, int, float], 
                        duration: Optional[Union[str, int, float]] = None,
                        end: Optional[Union[str, int, float]] = None) -> Timerange:
        """
        创建时间范围对象
        
        Args:
            start: 开始时间
            duration: 持续时间（与end二选一）
            end: 结束时间（与duration二选一）
            
        Returns:
            Timerange对象
            
        Raises:
            ValueError: 参数不正确
        """
        start_us = TimeConverter.tim(start)
        
        if duration is not None and end is not None:
            raise ValueError("duration和end参数不能同时指定")
        
        if duration is not None:
            duration_us = TimeConverter.tim(duration)
        elif end is not None:
            end_us = TimeConverter.tim(end)
            duration_us = end_us - start_us
            if duration_us < 0:
                raise ValueError(f"结束时间({end})不能小于开始时间({start})")
        else:
            raise ValueError("必须指定duration或end参数")
        
        return Timerange(start=start_us, duration=duration_us)
    
    @staticmethod
    def validate_timerange(timerange: Timerange, max_duration: Optional[int] = None) -> bool:
        """
        验证时间范围的有效性
        
        Args:
            timerange: 时间范围对象
            max_duration: 最大允许的持续时间（微秒），None表示不限制
            
        Returns:
            是否有效
        """
        # 检查基本有效性
        if timerange.start < 0:
            return False
        
        if timerange.duration <= 0:
            return False
        
        # 检查最大持续时间
        if max_duration is not None and timerange.duration > max_duration:
            return False
        
        return True

