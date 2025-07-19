"""
SRT字幕解析器模块

此模块是core层对parsers模块的包装，提供简单的接口用于解析SRT字幕文件
且保留了向后兼容性
"""

from typing import Dict, List, Any, Optional
from datetime import timedelta
import os
import logging

from src.parsers.srt_decoder import SRTDecoder
from src.parsers.subtitle_parser import Subtitle, SubtitleDocument, create_parser
from src.core.exceptions import InvalidSRTError, FileOperationError


logger = logging.getLogger(__name__)


class SRTParser:
    """SRT字幕解析器类"""

    def __init__(self, encoding: str = 'utf-8'):
        """
        初始化SRT解析器

        Args:
            encoding: 文件编码，默认为utf-8
        """
        self.encoding = encoding

    def parse(self, file_path: str) -> List[Dict[str, Any]]:
        """
        解析SRT字幕文件

        Args:
            file_path: SRT文件路径

        Returns:
            包含字幕信息的字典列表
        """
        return parse_srt(file_path, self.encoding)

    def parse_srt_content(self, srt_content: str) -> List[Dict[str, Any]]:
        """
        解析SRT字幕内容字符串

        Args:
            srt_content: SRT内容字符串

        Returns:
            包含字幕信息的字典列表
        """
        import re

        segments = []
        lines = srt_content.strip().split('\n')

        time_pattern = re.compile(r'(\d{2}):(\d{2}):(\d{2}),(\d{3}) --> (\d{2}):(\d{2}):(\d{2}),(\d{3})')

        i = 0
        while i < len(lines):
            if lines[i].strip().isdigit():
                segment_id = int(lines[i].strip())

                if i + 1 < len(lines):
                    time_match = time_pattern.match(lines[i + 1].strip())
                    if time_match:
                        start_time = self._parse_time(time_match.groups()[:4])
                        end_time = self._parse_time(time_match.groups()[4:])

                        # 收集字幕文本
                        text_lines = []
                        j = i + 2
                        while j < len(lines) and lines[j].strip():
                            text_lines.append(lines[j].strip())
                            j += 1

                        segments.append({
                            "id": segment_id,
                            "start_time": start_time,
                            "end_time": end_time,
                            "duration": end_time - start_time,
                            "text": "\n".join(text_lines)
                        })

                        i = j
                    else:
                        i += 1
                else:
                    i += 1
            else:
                i += 1

        return segments

    def _parse_time(self, time_parts: tuple) -> float:
        """解析时间为秒数"""
        hours, minutes, seconds, milliseconds = map(int, time_parts)
        return hours * 3600 + minutes * 60 + seconds + milliseconds / 1000.0


def parse_srt(file_path: str, encoding: str = 'utf-8') -> List[Dict[str, Any]]:
    """解析SRT字幕文件
    
    Args:
        file_path: SRT文件路径
        encoding: 文件编码，默认为utf-8
    
    Returns:
        包含字幕信息的字典列表，每个字典包含id, start_time, end_time, text等字段
    
    Raises:
        InvalidSRTError: SRT格式不正确
        FileOperationError: 文件读取错误
    """
    decoder = SRTDecoder(file_path, encoding)
    try:
        doc = decoder.parse_file()
        return [
            {
                "id": subtitle.index,
                "start_time": subtitle.start_time.total_seconds(),
                "end_time": subtitle.end_time.total_seconds(),
                "duration": subtitle.duration.total_seconds(),
                "text": subtitle.content
            }
            for subtitle in doc.subtitles
        ]
    except Exception as e:
        logger.error(f"Error parsing SRT file: {str(e)}")
        raise


def auto_detect_parse_srt(file_path: str) -> List[Dict[str, Any]]:
    """自动检测编码并解析SRT字幕文件
    
    Args:
        file_path: SRT文件路径
    
    Returns:
        包含字幕信息的字典列表，每个字典包含id, start_time, end_time, text等字段
    
    Raises:
        InvalidSRTError: SRT格式不正确
        FileOperationError: 文件读取错误
    """
    decoder = SRTDecoder(file_path)
    try:
        doc = decoder.auto_decode()
        return [
            {
                "id": subtitle.index,
                "start_time": subtitle.start_time.total_seconds(),
                "end_time": subtitle.end_time.total_seconds(),
                "duration": subtitle.duration.total_seconds(),
                "text": subtitle.content
            }
            for subtitle in doc.subtitles
        ]
    except Exception as e:
        logger.error(f"Error auto-parsing SRT file: {str(e)}")
        raise


def parse_subtitle(file_path: str, auto_detect_format: bool = True) -> List[Dict[str, Any]]:
    """解析各种格式的字幕文件
    
    支持SRT, ASS/SSA, VTT, JSON等格式，会自动检测格式或根据文件扩展名判断
    
    Args:
        file_path: 字幕文件路径
        auto_detect_format: 是否自动检测字幕格式，如果为False则根据扩展名判断
    
    Returns:
        包含字幕信息的字典列表，每个字典包含id, start_time, end_time, text等字段
    
    Raises:
        ValueError: 不支持的字幕格式
        InvalidSRTError: 字幕格式不正确
        FileOperationError: 文件读取错误
    """
    try:
        parser = create_parser(file_path, auto_detect_format)
        doc = parser.parse_file()
        return [
            {
                "id": subtitle.index,
                "start_time": subtitle.start_time.total_seconds(),
                "end_time": subtitle.end_time.total_seconds(),
                "duration": subtitle.duration.total_seconds(),
                "text": subtitle.content
            }
            for subtitle in doc.subtitles
        ]
    except Exception as e:
        logger.error(f"Error parsing subtitle file: {str(e)}")
        raise


def is_valid_srt(file_path: str) -> bool:
    """检查文件是否是有效的SRT格式
    
    Args:
        file_path: SRT文件路径
    
    Returns:
        是否是有效的SRT格式
    """
    if not os.path.exists(file_path):
        return False
    
    try:
        parse_srt(file_path)
        return True
    except Exception:
        return False
