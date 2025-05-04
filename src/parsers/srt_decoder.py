"""
SRT格式字幕解析器

解析标准SRT格式字幕文件，支持多种编码自动检测
"""

import re
import logging
from datetime import timedelta
from typing import List, Dict, Any, Optional, Tuple

from src.parsers.subtitle_parser import Subtitle, SubtitleDocument, SubtitleParser
from src.core.exceptions import InvalidSRTError


class SRTDecoder(SubtitleParser):
    """SRT格式字幕解析器
    
    解析标准SRT格式的字幕文件，包括：
    1. 数字索引行
    2. 时间戳行 (00:00:00,000 --> 00:00:00,000)
    3. 一行或多行字幕文本
    4. 空行分隔不同字幕条目
    """
    
    # 时间戳格式的正则表达式
    TIMESTAMP_PATTERN = re.compile(
        r'(\d{2}):(\d{2}):(\d{2}),(\d{3})\s+-->\s+(\d{2}):(\d{2}):(\d{2}),(\d{3})(?:\s+.*?)?$'
    )
    
    # 字幕索引行的正则表达式
    INDEX_PATTERN = re.compile(r'^\d+$')
    
    def __init__(self, file_path: Optional[str] = None, encoding: str = 'utf-8'):
        """初始化SRT解析器
        
        Args:
            file_path: SRT文件路径
            encoding: 文件编码，默认为utf-8
        """
        super().__init__(file_path, encoding)
        self.logger = logging.getLogger('SRTDecoder')
    
    def parse(self, content: Optional[str] = None) -> SubtitleDocument:
        """解析SRT格式字幕内容
        
        Args:
            content: SRT文本内容，如果为None则从file_path读取
            
        Returns:
            解析后的字幕文档对象
            
        Raises:
            FileOperationError: 文件操作错误
            InvalidSRTError: SRT格式错误
        """
        if content is None:
            return self.parse_file()
        
        subtitles = []
        
        # 按空行分割字幕块
        blocks = re.split(r'\n\s*\n', content.strip())
        
        for i, block in enumerate(blocks):
            if not block.strip():
                continue
            
            try:
                subtitle = self._parse_subtitle_block(block, i + 1)
                if subtitle:
                    subtitles.append(subtitle)
            except Exception as e:
                self.logger.warning(f"Error parsing subtitle block {i+1}: {str(e)}")
                # 继续解析，不因一个错误块而中断
        
        if not subtitles:
            raise InvalidSRTError("No valid subtitles found in the content")
        
        return SubtitleDocument(subtitles=subtitles)
    
    def _parse_subtitle_block(self, block: str, default_index: int) -> Optional[Subtitle]:
        """解析单个字幕块
        
        Args:
            block: 单个字幕块文本
            default_index: 默认索引，当无法解析索引时使用
            
        Returns:
            解析后的字幕对象，如果解析失败则返回None
        """
        lines = block.strip().split('\n')
        if len(lines) < 2:
            return None
        
        # 处理索引行
        if self.INDEX_PATTERN.match(lines[0].strip()):
            index = int(lines[0].strip())
            lines = lines[1:]
        else:
            index = default_index
        
        # 处理时间戳行
        timestamp_match = None
        for i, line in enumerate(lines):
            match = self.TIMESTAMP_PATTERN.match(line.strip())
            if match:
                timestamp_match = match
                content_start_index = i + 1
                break
        
        if not timestamp_match:
            raise InvalidSRTError(f"Invalid timestamp format in subtitle block: {block}")
        
        # 解析时间戳
        start_time = self._parse_timestamp(
            int(timestamp_match.group(1)),  # hours
            int(timestamp_match.group(2)),  # minutes
            int(timestamp_match.group(3)),  # seconds
            int(timestamp_match.group(4))   # milliseconds
        )
        
        end_time = self._parse_timestamp(
            int(timestamp_match.group(5)),  # hours
            int(timestamp_match.group(6)),  # minutes
            int(timestamp_match.group(7)),  # seconds
            int(timestamp_match.group(8))   # milliseconds
        )
        
        # 提取字幕内容
        content = '\n'.join(lines[content_start_index:]).strip()
        
        # 创建字幕对象
        return Subtitle(index, start_time, end_time, content)
    
    @staticmethod
    def _parse_timestamp(hours: int, minutes: int, seconds: int, milliseconds: int) -> timedelta:
        """将时、分、秒、毫秒转换为timedelta对象
        
        Args:
            hours: 小时
            minutes: 分钟
            seconds: 秒
            milliseconds: 毫秒
            
        Returns:
            表示时间点的timedelta对象
        """
        return timedelta(
            hours=hours,
            minutes=minutes,
            seconds=seconds,
            milliseconds=milliseconds
        )
    
    def auto_decode(self, file_path: Optional[str] = None) -> SubtitleDocument:
        """自动检测编码并解析SRT文件
        
        尝试多种常见编码（utf-8, utf-8-sig, gbk, big5, iso-8859-1等）
        
        Args:
            file_path: SRT文件路径，如果为None则使用初始化时的路径
            
        Returns:
            解析后的字幕文档对象
            
        Raises:
            FileOperationError: 文件操作错误
            InvalidSRTError: SRT格式错误
        """
        return self.parse_file(file_path)
    
    @staticmethod
    def verify_srt_format(content: str) -> bool:
        """验证内容是否符合SRT格式
        
        Args:
            content: 需要验证的字幕内容
            
        Returns:
            是否符合SRT格式
        """
        # 至少要有数字索引和时间戳
        index_pattern = re.compile(r'^\d+$', re.MULTILINE)
        timestamp_pattern = re.compile(
            r'\d{2}:\d{2}:\d{2},\d{3}\s+-->\s+\d{2}:\d{2}:\d{2},\d{3}',
            re.MULTILINE
        )
        
        has_index = bool(index_pattern.search(content))
        has_timestamp = bool(timestamp_pattern.search(content))
        
        return has_index and has_timestamp

def parse_srt_to_dict(srt_file_path: str) -> Dict[str, Any]:
    """
    解析SRT文件并转换为字典格式
    
    Args:
        srt_file_path: SRT文件路径
        
    Returns:
        包含字幕信息的字典，格式为:
        {
            "file_path": 文件路径,
            "total_count": 字幕总数,
            "total_duration": 总时长(秒),
            "subtitles": [
                {
                    "index": 索引号,
                    "start": 开始时间(秒),
                    "end": 结束时间(秒),
                    "duration": 持续时间(秒),
                    "text": 字幕文本
                },
                ...
            ]
        }
    """
    try:
        # 创建解析器
        decoder = SRTDecoder(srt_file_path)
        
        # 尝试自动检测编码并解析
        doc = decoder.auto_decode()
        
        # 构建结果字典
        subtitles_list = []
        total_duration = 0
        
        for subtitle in doc.subtitles:
            # 转换timedelta为秒
            start_seconds = subtitle.start_time.total_seconds()
            end_seconds = subtitle.end_time.total_seconds()
            duration = end_seconds - start_seconds
            
            # 累加总时长
            total_duration += duration
            
            # 添加到列表
            subtitles_list.append({
                "index": subtitle.index,
                "start": start_seconds,
                "end": end_seconds,
                "duration": duration,
                "text": subtitle.text
            })
        
        return {
            "file_path": srt_file_path,
            "total_count": len(subtitles_list),
            "total_duration": total_duration,
            "subtitles": subtitles_list
        }
        
    except Exception as e:
        logger = logging.getLogger('SRTParser')
        logger.error(f"解析SRT文件失败: {str(e)}")
        
        # 返回一个空字典作为降级处理
        return {
            "file_path": srt_file_path,
            "total_count": 0,
            "total_duration": 0,
            "subtitles": [],
            "error": str(e)
        } 