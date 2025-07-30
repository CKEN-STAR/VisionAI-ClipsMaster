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

        Raises:
            FileOperationError: 文件读取错误
            InvalidSRTError: SRT格式不正确
        """
        try:
            return parse_srt(file_path, self.encoding)
        except Exception as e:
            logger.error(f"SRTParser解析失败: {file_path}, 错误: {e}")
            raise

    def parse_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        解析SRT字幕文件（标准方法名）

        Args:
            file_path: SRT文件路径

        Returns:
            包含字幕信息的字典列表
        """
        return self.parse(file_path)

    def parse_srt_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        解析SRT字幕文件（别名方法）

        Args:
            file_path: SRT文件路径

        Returns:
            包含字幕信息的字典列表
        """
        return self.parse(file_path)

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

    def get_total_duration(self, subtitles: List[Dict[str, Any]]) -> float:
        """
        计算字幕的总时长

        Args:
            subtitles: 字幕列表，每个字幕包含start_time和end_time

        Returns:
            总时长（秒）
        """
        if not subtitles:
            return 0.0

        # 找到最早的开始时间和最晚的结束时间
        start_times = [sub.get('start_time', 0) for sub in subtitles]
        end_times = [sub.get('end_time', 0) for sub in subtitles]

        if not start_times or not end_times:
            return 0.0

        earliest_start = min(start_times)
        latest_end = max(end_times)

        return max(0.0, latest_end - earliest_start)

    def get_subtitle_count(self, subtitles: List[Dict[str, Any]]) -> int:
        """
        获取字幕条数

        Args:
            subtitles: 字幕列表

        Returns:
            字幕条数
        """
        return len(subtitles) if subtitles else 0

    def get_duration_stats(self, subtitles: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        获取字幕时长统计信息

        Args:
            subtitles: 字幕列表

        Returns:
            包含总时长、平均时长、最短时长、最长时长的字典
        """
        if not subtitles:
            return {
                'total_duration': 0.0,
                'average_duration': 0.0,
                'min_duration': 0.0,
                'max_duration': 0.0,
                'subtitle_count': 0
            }

        durations = [sub.get('duration', 0) for sub in subtitles]
        durations = [d for d in durations if d > 0]  # 过滤无效时长

        if not durations:
            return {
                'total_duration': 0.0,
                'average_duration': 0.0,
                'min_duration': 0.0,
                'max_duration': 0.0,
                'subtitle_count': len(subtitles)
            }

        return {
            'total_duration': self.get_total_duration(subtitles),
            'average_duration': sum(durations) / len(durations),
            'min_duration': min(durations),
            'max_duration': max(durations),
            'subtitle_count': len(subtitles)
        }


def parse_srt(file_path: str, encoding: str = 'utf-8') -> List[Dict[str, Any]]:
    """解析SRT字幕文件

    Args:
        file_path: SRT文件路径
        encoding: 文件编码，默认为utf-8

    Returns:
        包含字幕信息的字典列表，每个字典包含id, start_time, end_time, text等字段

    Raises:
        FileOperationError: 文件读取错误
        InvalidSRTError: SRT格式不正确
    """
    try:
        # 首先检查文件是否存在
        if not os.path.exists(file_path):
            error_msg = f"SRT文件不存在: {file_path}"
            logger.error(error_msg)
            raise FileOperationError(error_msg)

        # 检查文件是否可读
        if not os.access(file_path, os.R_OK):
            error_msg = f"SRT文件无法读取: {file_path}"
            logger.error(error_msg)
            raise FileOperationError(error_msg)

        # 检查文件大小
        try:
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                logger.warning(f"SRT文件为空: {file_path}")
                return []
        except OSError as e:
            error_msg = f"无法获取文件大小: {file_path}, 错误: {e}"
            logger.error(error_msg)
            raise FileOperationError(error_msg)

        # 检查文件内容是否只包含空白字符
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read().strip()
                if not content:
                    logger.warning(f"SRT文件内容为空: {file_path}")
                    return []
        except UnicodeDecodeError as e:
            error_msg = f"SRT文件编码错误: {file_path}, 编码: {encoding}, 错误: {e}"
            logger.error(error_msg)
            raise FileOperationError(error_msg)
        except IOError as e:
            error_msg = f"SRT文件读取失败: {file_path}, 错误: {e}"
            logger.error(error_msg)
            raise FileOperationError(error_msg)

        # 使用SRTDecoder解析文件
        try:
            decoder = SRTDecoder(file_path, encoding)
            doc = decoder.parse_file()

            # 检查是否解析出有效字幕
            if not doc or not hasattr(doc, 'subtitles') or not doc.subtitles:
                logger.warning(f"SRT文件中没有有效字幕: {file_path}")
                return []

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
        except InvalidSRTError as e:
            # 如果是"No valid subtitles found"错误，返回空列表而不是抛出异常
            if "No valid subtitles found" in str(e):
                logger.warning(f"SRT文件中没有有效字幕: {file_path}")
                return []
            else:
                logger.error(f"SRT格式错误: {file_path}, 错误: {e}")
                raise
        except Exception as e:
            error_msg = f"SRT解析过程中发生未知错误: {file_path}, 错误: {e}"
            logger.error(error_msg)
            raise FileOperationError(error_msg)

    except (FileOperationError, InvalidSRTError):
        # 重新抛出已知的异常
        raise
    except Exception as e:
        # 捕获所有其他异常并包装为FileOperationError
        error_msg = f"SRT文件处理失败: {file_path}, 错误: {e}"
        logger.error(error_msg)
        raise FileOperationError(error_msg)


def auto_detect_parse_srt(file_path: str) -> List[Dict[str, Any]]:
    """自动检测编码并解析SRT字幕文件

    Args:
        file_path: SRT文件路径

    Returns:
        包含字幕信息的字典列表，每个字典包含id, start_time, end_time, text等字段

    Raises:
        FileOperationError: 文件读取错误
        InvalidSRTError: SRT格式不正确
    """
    try:
        # 首先检查文件是否存在
        if not os.path.exists(file_path):
            error_msg = f"SRT文件不存在: {file_path}"
            logger.error(error_msg)
            raise FileOperationError(error_msg)

        decoder = SRTDecoder(file_path)
        doc = decoder.auto_decode()

        # 检查是否解析出有效字幕
        if not doc or not hasattr(doc, 'subtitles') or not doc.subtitles:
            logger.warning(f"SRT文件中没有有效字幕: {file_path}")
            return []

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
    except (FileOperationError, InvalidSRTError):
        # 重新抛出已知的异常
        raise
    except Exception as e:
        error_msg = f"自动检测解析SRT文件失败: {file_path}, 错误: {e}"
        logger.error(error_msg)
        raise FileOperationError(error_msg)


def parse_subtitle(file_path: str, auto_detect_format: bool = True) -> List[Dict[str, Any]]:
    """解析各种格式的字幕文件

    支持SRT, ASS/SSA, VTT, JSON等格式，会自动检测格式或根据文件扩展名判断

    Args:
        file_path: 字幕文件路径
        auto_detect_format: 是否自动检测字幕格式，如果为False则根据扩展名判断

    Returns:
        包含字幕信息的字典列表，每个字典包含id, start_time, end_time, text等字段

    Raises:
        FileOperationError: 文件读取错误
        ValueError: 不支持的字幕格式
        InvalidSRTError: 字幕格式不正确
    """
    try:
        # 首先检查文件是否存在
        if not os.path.exists(file_path):
            error_msg = f"字幕文件不存在: {file_path}"
            logger.error(error_msg)
            raise FileOperationError(error_msg)

        parser = create_parser(file_path, auto_detect_format)
        doc = parser.parse_file()

        # 检查是否解析出有效字幕
        if not doc or not hasattr(doc, 'subtitles') or not doc.subtitles:
            logger.warning(f"字幕文件中没有有效字幕: {file_path}")
            return []

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
    except (FileOperationError, ValueError, InvalidSRTError):
        # 重新抛出已知的异常
        raise
    except Exception as e:
        error_msg = f"解析字幕文件失败: {file_path}, 错误: {e}"
        logger.error(error_msg)
        raise FileOperationError(error_msg)


def is_valid_srt(file_path: str) -> bool:
    """检查文件是否是有效的SRT格式

    Args:
        file_path: SRT文件路径

    Returns:
        是否是有效的SRT格式
    """
    try:
        # 检查文件是否存在
        if not os.path.exists(file_path):
            return False

        # 检查文件是否可读
        if not os.access(file_path, os.R_OK):
            return False

        # 尝试解析SRT文件
        result = parse_srt(file_path)
        # 如果解析成功且有内容，则认为是有效的
        return isinstance(result, list)
    except Exception as e:
        logger.debug(f"SRT文件验证失败: {file_path}, 错误: {e}")
        return False
