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
