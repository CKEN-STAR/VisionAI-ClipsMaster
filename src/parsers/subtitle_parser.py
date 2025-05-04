"""
字幕解析基础模块

提供字幕解析的抽象基类和公共功能。各种字幕格式的解析器应该继承SubtitleParser基类。
"""

import os
import re
import logging
from typing import List, Dict, Any, Optional, Union, Tuple
from abc import ABC, abstractmethod
from datetime import timedelta
from pathlib import Path

from src.core.exceptions import InvalidSRTError, FileOperationError


class Subtitle:
    """字幕条目基类"""
    
    def __init__(
        self,
        index: int,
        start_time: timedelta,
        end_time: timedelta,
        content: str
    ):
        """初始化字幕条目
        
        Args:
            index: 字幕条目的索引号
            start_time: 字幕开始时间
            end_time: 字幕结束时间
            content: 字幕内容
        """
        self.index = index
        self.start_time = start_time
        self.end_time = end_time
        self.content = content
        self.duration = end_time - start_time
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"{self.index}: [{self.start_time} --> {self.end_time}] {self.content}"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式，方便序列化"""
        return {
            "index": self.index,
            "start_time": self.start_time.total_seconds(),
            "end_time": self.end_time.total_seconds(),
            "duration": self.duration.total_seconds(),
            "content": self.content
        }


class SubtitleDocument:
    """字幕文档类，包含多个字幕条目"""
    
    def __init__(self, subtitles: List[Subtitle] = None, metadata: Dict[str, Any] = None):
        """初始化字幕文档
        
        Args:
            subtitles: 字幕条目列表
            metadata: 字幕文档的元数据
        """
        self.subtitles = subtitles or []
        self.metadata = metadata or {}
    
    def add_subtitle(self, subtitle: Subtitle) -> None:
        """添加字幕条目
        
        Args:
            subtitle: 要添加的字幕条目
        """
        self.subtitles.append(subtitle)
    
    def get_subtitle_at_time(self, time_point: timedelta) -> Optional[Subtitle]:
        """获取特定时间点的字幕
        
        Args:
            time_point: 时间点
            
        Returns:
            如果找到匹配的字幕则返回，否则返回None
        """
        for subtitle in self.subtitles:
            if subtitle.start_time <= time_point <= subtitle.end_time:
                return subtitle
        return None
    
    def get_subtitles_by_timerange(
        self, start_time: timedelta, end_time: timedelta
    ) -> List[Subtitle]:
        """获取特定时间范围内的字幕
        
        Args:
            start_time: 起始时间
            end_time: 结束时间
            
        Returns:
            该时间范围内的字幕列表
        """
        return [
            s for s in self.subtitles
            if (start_time <= s.start_time <= end_time) or
               (start_time <= s.end_time <= end_time) or
               (s.start_time <= start_time and s.end_time >= end_time)
        ]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式，方便序列化
        
        Returns:
            包含所有字幕数据的字典
        """
        return {
            "metadata": self.metadata,
            "subtitles": [subtitle.to_dict() for subtitle in self.subtitles]
        }
    
    def __len__(self) -> int:
        """获取字幕条目数量"""
        return len(self.subtitles)
    
    def __getitem__(self, index: int) -> Subtitle:
        """通过索引获取字幕条目"""
        return self.subtitles[index]


class SubtitleParser(ABC):
    """字幕解析器抽象基类"""
    
    def __init__(self, file_path: Optional[str] = None, encoding: str = 'utf-8'):
        """初始化字幕解析器
        
        Args:
            file_path: 字幕文件路径
            encoding: 字幕文件编码，默认为utf-8
        """
        self.file_path = file_path
        self.encoding = encoding
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def parse(self, content: Optional[str] = None) -> SubtitleDocument:
        """解析字幕内容
        
        Args:
            content: 字幕文本内容，如果为None则从file_path读取
            
        Returns:
            解析后的字幕文档对象
            
        Raises:
            FileOperationError: 文件操作错误
            InvalidSRTError: 字幕格式错误
        """
        pass
    
    def parse_file(self, file_path: Optional[str] = None, encoding: Optional[str] = None) -> SubtitleDocument:
        """解析字幕文件
        
        Args:
            file_path: 字幕文件路径，如果为None则使用初始化时的路径
            encoding: 字幕文件编码，如果为None则使用初始化时的编码
            
        Returns:
            解析后的字幕文档对象
            
        Raises:
            FileOperationError: 文件操作错误
            InvalidSRTError: 字幕格式错误
        """
        file_path = file_path or self.file_path
        encoding = encoding or self.encoding
        
        if not file_path:
            raise FileOperationError("No file path provided")
        
        if not os.path.exists(file_path):
            raise FileOperationError(f"File not found: {file_path}", file_path=file_path)
        
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            return self.parse(content)
        except UnicodeDecodeError:
            # 尝试其他常见编码
            for enc in ['utf-8-sig', 'gbk', 'iso-8859-1', 'big5']:
                if enc == encoding:
                    continue
                try:
                    with open(file_path, 'r', encoding=enc) as f:
                        content = f.read()
                    self.logger.info(f"Successfully decoded using {enc} encoding")
                    self.encoding = enc  # 更新成功的编码
                    return self.parse(content)
                except UnicodeDecodeError:
                    continue
            
            # 如果所有尝试都失败
            raise FileOperationError(
                f"Failed to decode file with available encodings: {file_path}",
                file_path=file_path
            )
        except Exception as e:
            raise FileOperationError(f"Error reading file: {str(e)}", file_path=file_path)
    
    @staticmethod
    def detect_format(file_path: str) -> str:
        """检测字幕文件格式
        
        Args:
            file_path: 字幕文件路径
            
        Returns:
            检测到的格式名称: 'srt', 'ass', 'vtt', 'json', 'unknown'
        """
        # 首先根据扩展名判断
        ext = os.path.splitext(file_path)[1].lower()
        if ext in ['.srt']:
            return 'srt'
        elif ext in ['.ass', '.ssa']:
            return 'ass'
        elif ext in ['.vtt']:
            return 'vtt'
        elif ext in ['.json']:
            return 'json'
        
        # 如果扩展名不明确，尝试读取文件内容进行判断
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read(4096)  # 读取前4KB内容进行判断
                
                # SRT格式通常以数字索引开始，然后是时间戳格式 00:00:00,000 --> 00:00:00,000
                if re.search(r'^\d+\s*\n\d{2}:\d{2}:\d{2},\d{3}\s+-->\s+\d{2}:\d{2}:\d{2},\d{3}', content, re.MULTILINE):
                    return 'srt'
                
                # ASS格式通常包含 [Script Info] 和 [V4+ Styles] 等段落
                if '[Script Info]' in content and ('Styles]' in content or 'Events]' in content):
                    return 'ass'
                
                # WebVTT格式通常以 WEBVTT 开头
                if content.strip().startswith('WEBVTT'):
                    return 'vtt'
                
                # JSON格式
                if content.strip().startswith('{') and content.strip().endswith('}'):
                    return 'json'
                
        except Exception:
            pass
        
        return 'unknown'


def create_parser(file_path: str, auto_detect: bool = True) -> SubtitleParser:
    """创建适合字幕文件格式的解析器
    
    Args:
        file_path: 字幕文件路径
        auto_detect: 是否自动检测字幕格式，如果为False则根据扩展名判断
        
    Returns:
        对应格式的字幕解析器实例
        
    Raises:
        ValueError: 不支持的字幕格式
    """
    if auto_detect:
        format_type = SubtitleParser.detect_format(file_path)
    else:
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.srt':
            format_type = 'srt'
        elif ext in ['.ass', '.ssa']:
            format_type = 'ass'
        elif ext == '.vtt':
            format_type = 'vtt'
        elif ext == '.json':
            format_type = 'json'
        else:
            format_type = 'unknown'
    
    # 导入需要在函数内部进行，避免循环导入
    from src.parsers.srt_decoder import SRTDecoder
    
    if format_type == 'srt':
        return SRTDecoder(file_path)
    # 后续可以添加其他格式的解析器支持
    # elif format_type == 'ass':
    #    from src.parsers.ass_decoder import ASSDecoder
    #    return ASSDecoder(file_path)
    # elif format_type == 'vtt':
    #    from src.parsers.vtt_decoder import VTTDecoder
    #    return VTTDecoder(file_path)
    # elif format_type == 'json':
    #    from src.parsers.json_decoder import JSONDecoder
    #    return JSONDecoder(file_path)
    else:
        raise ValueError(f"Unsupported subtitle format: {format_type}") 