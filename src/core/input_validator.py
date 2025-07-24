#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 输入验证阶段实现
严格按照核心工作流程第1阶段要求：输入验证阶段

核心功能：
1. 视频文件格式验证(MP4/AVI/MOV)
2. SRT字幕文件格式和时间码完整性验证
3. 视频时长与字幕时间范围匹配验证
4. 严格的技术约束检查

技术约束：
- 支持的视频格式：MP4, AVI, MOV
- 字幕格式：SRT
- 时间同步精度：≤0.5秒
- 内存使用限制：4GB约束下运行
"""

import os
import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
from datetime import timedelta

# 配置日志
logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """验证结果数据类"""
    is_valid: bool
    error_code: str = ""
    error_message: str = ""
    warnings: List[str] = None
    details: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []
        if self.details is None:
            self.details = {}

@dataclass
class VideoInfo:
    """视频信息数据类"""
    file_path: str
    format: str
    duration: float  # 秒
    width: int
    height: int
    fps: float
    codec: str
    file_size: int  # 字节

@dataclass
class SubtitleInfo:
    """字幕信息数据类"""
    file_path: str
    format: str
    total_subtitles: int
    duration: float  # 秒
    first_timestamp: float
    last_timestamp: float
    encoding: str
    file_size: int  # 字节
    time_gaps: List[Tuple[float, float]] = None  # 时间间隙
    
    def __post_init__(self):
        if self.time_gaps is None:
            self.time_gaps = []

class InputValidator:
    """
    VisionAI-ClipsMaster 输入验证器
    
    严格按照核心工作流程第1阶段要求实现：
    - 接收用户上传的短剧原片视频文件（支持MP4/AVI/MOV格式）
    - 验证对应的完整SRT字幕文件格式和时间码完整性
    - 确保视频时长与字幕时间范围匹配
    """
    
    # 支持的视频格式（严格按照技术约束）
    SUPPORTED_VIDEO_FORMATS = {'.mp4', '.avi', '.mov'}
    
    # 支持的字幕格式
    SUPPORTED_SUBTITLE_FORMATS = {'.srt'}
    
    # 时间同步容差（≤0.5秒）
    TIME_SYNC_TOLERANCE = 0.5
    
    # 文件大小限制（4GB内存约束考虑）
    MAX_VIDEO_SIZE = 2 * 1024 * 1024 * 1024  # 2GB
    MAX_SUBTITLE_SIZE = 10 * 1024 * 1024     # 10MB
    
    def __init__(self):
        """初始化输入验证器"""
        self.validation_history = []
        logger.info("VisionAI-ClipsMaster 输入验证器初始化完成")
    
    def validate_input_files(self, video_path: str, subtitle_path: str) -> ValidationResult:
        """
        验证输入文件（核心工作流程第1阶段）
        
        Args:
            video_path: 视频文件路径
            subtitle_path: 字幕文件路径
            
        Returns:
            ValidationResult: 验证结果
        """
        try:
            logger.info(f"开始输入验证阶段：视频={video_path}, 字幕={subtitle_path}")
            
            # 第1步：基础文件存在性检查
            basic_check = self._validate_file_existence(video_path, subtitle_path)
            if not basic_check.is_valid:
                return basic_check
            
            # 第2步：视频文件格式验证
            video_validation = self._validate_video_file(video_path)
            if not video_validation.is_valid:
                return video_validation
            
            # 第3步：字幕文件格式验证
            subtitle_validation = self._validate_subtitle_file(subtitle_path)
            if not subtitle_validation.is_valid:
                return subtitle_validation
            
            # 第4步：时间码完整性验证
            timecode_validation = self._validate_timecode_integrity(subtitle_path)
            if not timecode_validation.is_valid:
                return timecode_validation
            
            # 第5步：视频与字幕时间范围匹配验证
            sync_validation = self._validate_time_sync(
                video_validation.details['video_info'],
                subtitle_validation.details['subtitle_info']
            )
            if not sync_validation.is_valid:
                return sync_validation
            
            # 汇总验证结果
            result = ValidationResult(
                is_valid=True,
                error_code="SUCCESS",
                error_message="输入验证阶段通过",
                details={
                    "video_info": video_validation.details['video_info'],
                    "subtitle_info": subtitle_validation.details['subtitle_info'],
                    "sync_info": sync_validation.details
                }
            )
            
            # 收集所有警告
            result.warnings.extend(video_validation.warnings)
            result.warnings.extend(subtitle_validation.warnings)
            result.warnings.extend(sync_validation.warnings)
            
            logger.info("输入验证阶段完成：验证通过")
            self.validation_history.append(result)
            
            return result
            
        except Exception as e:
            error_result = ValidationResult(
                is_valid=False,
                error_code="VALIDATION_ERROR",
                error_message=f"输入验证阶段异常: {str(e)}"
            )
            logger.error(f"输入验证阶段失败: {str(e)}")
            return error_result
    
    def _validate_file_existence(self, video_path: str, subtitle_path: str) -> ValidationResult:
        """验证文件存在性"""
        try:
            if not os.path.exists(video_path):
                return ValidationResult(
                    is_valid=False,
                    error_code="VIDEO_NOT_FOUND",
                    error_message=f"视频文件不存在: {video_path}"
                )
            
            if not os.path.exists(subtitle_path):
                return ValidationResult(
                    is_valid=False,
                    error_code="SUBTITLE_NOT_FOUND",
                    error_message=f"字幕文件不存在: {subtitle_path}"
                )
            
            return ValidationResult(is_valid=True)
            
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                error_code="FILE_ACCESS_ERROR",
                error_message=f"文件访问错误: {str(e)}"
            )
    
    def _validate_video_file(self, video_path: str) -> ValidationResult:
        """验证视频文件格式和基本信息"""
        try:
            # 检查文件扩展名
            file_ext = Path(video_path).suffix.lower()
            if file_ext not in self.SUPPORTED_VIDEO_FORMATS:
                return ValidationResult(
                    is_valid=False,
                    error_code="UNSUPPORTED_VIDEO_FORMAT",
                    error_message=f"不支持的视频格式: {file_ext}，支持格式: {', '.join(self.SUPPORTED_VIDEO_FORMATS)}"
                )
            
            # 检查文件大小
            file_size = os.path.getsize(video_path)
            if file_size > self.MAX_VIDEO_SIZE:
                return ValidationResult(
                    is_valid=False,
                    error_code="VIDEO_TOO_LARGE",
                    error_message=f"视频文件过大: {file_size / (1024*1024*1024):.2f}GB，最大支持: {self.MAX_VIDEO_SIZE / (1024*1024*1024):.2f}GB"
                )
            
            # 获取视频信息
            video_info = self._get_video_info(video_path)
            if not video_info:
                return ValidationResult(
                    is_valid=False,
                    error_code="VIDEO_INFO_ERROR",
                    error_message="无法获取视频信息，可能文件损坏"
                )
            
            warnings = []
            
            # 检查视频质量
            if video_info.width < 1280 or video_info.height < 720:
                warnings.append(f"视频分辨率较低: {video_info.width}x{video_info.height}，建议至少720p")
            
            if video_info.fps < 24:
                warnings.append(f"视频帧率较低: {video_info.fps}fps，建议至少24fps")
            
            if video_info.duration < 10:
                warnings.append(f"视频时长较短: {video_info.duration:.2f}秒")
            
            return ValidationResult(
                is_valid=True,
                warnings=warnings,
                details={"video_info": video_info}
            )
            
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                error_code="VIDEO_VALIDATION_ERROR",
                error_message=f"视频验证失败: {str(e)}"
            )
    
    def _validate_subtitle_file(self, subtitle_path: str) -> ValidationResult:
        """验证字幕文件格式和基本信息"""
        try:
            # 检查文件扩展名
            file_ext = Path(subtitle_path).suffix.lower()
            if file_ext not in self.SUPPORTED_SUBTITLE_FORMATS:
                return ValidationResult(
                    is_valid=False,
                    error_code="UNSUPPORTED_SUBTITLE_FORMAT",
                    error_message=f"不支持的字幕格式: {file_ext}，支持格式: {', '.join(self.SUPPORTED_SUBTITLE_FORMATS)}"
                )
            
            # 检查文件大小
            file_size = os.path.getsize(subtitle_path)
            if file_size > self.MAX_SUBTITLE_SIZE:
                return ValidationResult(
                    is_valid=False,
                    error_code="SUBTITLE_TOO_LARGE",
                    error_message=f"字幕文件过大: {file_size / (1024*1024):.2f}MB，最大支持: {self.MAX_SUBTITLE_SIZE / (1024*1024):.2f}MB"
                )
            
            # 解析字幕文件
            subtitle_info = self._parse_subtitle_file(subtitle_path)
            if not subtitle_info:
                return ValidationResult(
                    is_valid=False,
                    error_code="SUBTITLE_PARSE_ERROR",
                    error_message="字幕文件解析失败，可能格式不正确"
                )
            
            warnings = []
            
            # 检查字幕质量
            if subtitle_info.total_subtitles < 10:
                warnings.append(f"字幕条数较少: {subtitle_info.total_subtitles}条")
            
            if subtitle_info.duration < 10:
                warnings.append(f"字幕总时长较短: {subtitle_info.duration:.2f}秒")
            
            # 检查时间间隙
            if len(subtitle_info.time_gaps) > 0:
                large_gaps = [gap for gap in subtitle_info.time_gaps if gap[1] - gap[0] > 5]
                if large_gaps:
                    warnings.append(f"发现{len(large_gaps)}个较大的时间间隙(>5秒)")
            
            return ValidationResult(
                is_valid=True,
                warnings=warnings,
                details={"subtitle_info": subtitle_info}
            )
            
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                error_code="SUBTITLE_VALIDATION_ERROR",
                error_message=f"字幕验证失败: {str(e)}"
            )

    def _validate_timecode_integrity(self, subtitle_path: str) -> ValidationResult:
        """验证时间码完整性"""
        try:
            # 解析字幕文件获取时间码信息
            from src.core.srt_parser import parse_srt

            subtitles = parse_srt(subtitle_path)
            if not subtitles:
                return ValidationResult(
                    is_valid=False,
                    error_code="EMPTY_SUBTITLE",
                    error_message="字幕文件为空或无有效内容"
                )

            warnings = []
            errors = []

            # 检查时间码格式和逻辑
            for i, subtitle in enumerate(subtitles):
                # 检查时间码有效性
                if subtitle['start_time'] < 0 or subtitle['end_time'] < 0:
                    errors.append(f"字幕{subtitle['id']}时间码为负值")

                if subtitle['start_time'] >= subtitle['end_time']:
                    errors.append(f"字幕{subtitle['id']}开始时间晚于或等于结束时间")

                if subtitle['duration'] <= 0:
                    errors.append(f"字幕{subtitle['id']}持续时间无效")

                # 检查时间码连续性
                if i > 0:
                    prev_subtitle = subtitles[i-1]

                    # 检查时间重叠
                    if subtitle['start_time'] < prev_subtitle['end_time']:
                        overlap = prev_subtitle['end_time'] - subtitle['start_time']
                        if overlap > self.TIME_SYNC_TOLERANCE:
                            warnings.append(f"字幕{prev_subtitle['id']}和{subtitle['id']}存在时间重叠: {overlap:.2f}秒")

                    # 检查时间间隙
                    gap = subtitle['start_time'] - prev_subtitle['end_time']
                    if gap > 10:  # 超过10秒的间隙
                        warnings.append(f"字幕{prev_subtitle['id']}和{subtitle['id']}之间存在较大时间间隙: {gap:.2f}秒")

                # 检查字幕持续时间合理性
                if subtitle['duration'] > 10:  # 单条字幕超过10秒
                    warnings.append(f"字幕{subtitle['id']}持续时间较长: {subtitle['duration']:.2f}秒")
                elif subtitle['duration'] < 0.5:  # 单条字幕少于0.5秒
                    warnings.append(f"字幕{subtitle['id']}持续时间过短: {subtitle['duration']:.2f}秒")

            # 如果有严重错误，验证失败
            if errors:
                return ValidationResult(
                    is_valid=False,
                    error_code="TIMECODE_INTEGRITY_ERROR",
                    error_message=f"时间码完整性验证失败: {'; '.join(errors[:3])}{'...' if len(errors) > 3 else ''}",
                    details={"errors": errors, "warnings": warnings}
                )

            return ValidationResult(
                is_valid=True,
                warnings=warnings,
                details={"timecode_check": "passed", "total_errors": 0, "total_warnings": len(warnings)}
            )

        except Exception as e:
            return ValidationResult(
                is_valid=False,
                error_code="TIMECODE_VALIDATION_ERROR",
                error_message=f"时间码验证失败: {str(e)}"
            )

    def _validate_time_sync(self, video_info: VideoInfo, subtitle_info: SubtitleInfo) -> ValidationResult:
        """验证视频与字幕时间范围匹配"""
        try:
            # 计算时间差异
            duration_diff = abs(video_info.duration - subtitle_info.duration)

            # 检查字幕是否超出视频范围
            subtitle_overrun = subtitle_info.last_timestamp - video_info.duration

            warnings = []
            errors = []

            # 严格的时间同步检查（≤0.5秒精度要求）
            if duration_diff > self.TIME_SYNC_TOLERANCE:
                if duration_diff > 5:  # 超过5秒认为是严重不匹配
                    errors.append(f"视频时长({video_info.duration:.2f}s)与字幕时长({subtitle_info.duration:.2f}s)差异过大: {duration_diff:.2f}s")
                else:
                    warnings.append(f"视频与字幕时长存在差异: {duration_diff:.2f}s")

            # 检查字幕是否超出视频范围
            if subtitle_overrun > self.TIME_SYNC_TOLERANCE:
                errors.append(f"字幕结束时间({subtitle_info.last_timestamp:.2f}s)超出视频时长({video_info.duration:.2f}s): {subtitle_overrun:.2f}s")

            # 检查字幕开始时间
            if subtitle_info.first_timestamp > 10:  # 字幕开始时间超过10秒
                warnings.append(f"字幕开始时间较晚: {subtitle_info.first_timestamp:.2f}s")

            # 如果有严重错误，验证失败
            if errors:
                return ValidationResult(
                    is_valid=False,
                    error_code="TIME_SYNC_ERROR",
                    error_message=f"时间同步验证失败: {'; '.join(errors)}",
                    details={
                        "duration_diff": duration_diff,
                        "subtitle_overrun": subtitle_overrun,
                        "errors": errors,
                        "warnings": warnings
                    }
                )

            return ValidationResult(
                is_valid=True,
                warnings=warnings,
                details={
                    "duration_diff": duration_diff,
                    "subtitle_overrun": subtitle_overrun,
                    "sync_quality": "excellent" if duration_diff <= 0.1 else "good" if duration_diff <= 0.5 else "acceptable"
                }
            )

        except Exception as e:
            return ValidationResult(
                is_valid=False,
                error_code="TIME_SYNC_VALIDATION_ERROR",
                error_message=f"时间同步验证失败: {str(e)}"
            )

    def _get_video_info(self, video_path: str) -> Optional[VideoInfo]:
        """获取视频信息"""
        try:
            # 尝试使用ffmpeg-python
            try:
                import ffmpeg

                probe = ffmpeg.probe(video_path)
                video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)

                if not video_stream:
                    logger.error("视频文件中未找到视频流")
                    return None

                duration = float(probe['format']['duration'])
                width = int(video_stream['width'])
                height = int(video_stream['height'])

                # 解析帧率
                fps_str = video_stream.get('r_frame_rate', '25/1')
                if '/' in fps_str:
                    num, den = fps_str.split('/')
                    fps = float(num) / float(den)
                else:
                    fps = float(fps_str)

                codec = video_stream.get('codec_name', 'unknown')
                file_size = os.path.getsize(video_path)

                return VideoInfo(
                    file_path=video_path,
                    format=Path(video_path).suffix.lower(),
                    duration=duration,
                    width=width,
                    height=height,
                    fps=fps,
                    codec=codec,
                    file_size=file_size
                )

            except ImportError:
                logger.warning("ffmpeg-python未安装，使用备用方法获取视频信息")
                # 备用方法：使用基础文件信息
                file_size = os.path.getsize(video_path)
                return VideoInfo(
                    file_path=video_path,
                    format=Path(video_path).suffix.lower(),
                    duration=0.0,  # 无法获取
                    width=1920,    # 默认值
                    height=1080,   # 默认值
                    fps=25.0,      # 默认值
                    codec='unknown',
                    file_size=file_size
                )

        except Exception as e:
            logger.error(f"获取视频信息失败: {str(e)}")
            return None

    def _parse_subtitle_file(self, subtitle_path: str) -> Optional[SubtitleInfo]:
        """解析字幕文件信息"""
        try:
            from src.core.srt_parser import parse_srt

            subtitles = parse_srt(subtitle_path)
            if not subtitles:
                return None

            # 计算基本信息
            total_subtitles = len(subtitles)
            first_timestamp = subtitles[0]['start_time']
            last_timestamp = subtitles[-1]['end_time']
            duration = last_timestamp - first_timestamp
            file_size = os.path.getsize(subtitle_path)

            # 检测编码
            encoding = self._detect_file_encoding(subtitle_path)

            # 计算时间间隙
            time_gaps = []
            for i in range(1, len(subtitles)):
                gap_start = subtitles[i-1]['end_time']
                gap_end = subtitles[i]['start_time']
                if gap_end > gap_start:
                    time_gaps.append((gap_start, gap_end))

            return SubtitleInfo(
                file_path=subtitle_path,
                format=Path(subtitle_path).suffix.lower(),
                total_subtitles=total_subtitles,
                duration=duration,
                first_timestamp=first_timestamp,
                last_timestamp=last_timestamp,
                encoding=encoding,
                file_size=file_size,
                time_gaps=time_gaps
            )

        except Exception as e:
            logger.error(f"解析字幕文件失败: {str(e)}")
            return None

    def _detect_file_encoding(self, file_path: str) -> str:
        """检测文件编码"""
        try:
            import chardet

            with open(file_path, 'rb') as f:
                raw_data = f.read(10240)  # 读取前10KB
                result = chardet.detect(raw_data)
                return result.get('encoding', 'utf-8')

        except ImportError:
            # 如果没有chardet，尝试常见编码
            encodings = ['utf-8', 'gbk', 'gb2312', 'utf-16']
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        f.read(1024)
                    return encoding
                except UnicodeDecodeError:
                    continue
            return 'utf-8'  # 默认返回utf-8
        except Exception as e:
            logger.warning(f"编码检测失败: {str(e)}")
            return 'utf-8'

    def get_validation_summary(self) -> Dict[str, Any]:
        """获取验证历史摘要"""
        if not self.validation_history:
            return {"total_validations": 0, "success_rate": 0.0}

        total = len(self.validation_history)
        successful = sum(1 for result in self.validation_history if result.is_valid)

        return {
            "total_validations": total,
            "successful_validations": successful,
            "failed_validations": total - successful,
            "success_rate": successful / total,
            "last_validation": self.validation_history[-1].error_code if self.validation_history else None
        }

    def clear_validation_history(self):
        """清空验证历史"""
        self.validation_history.clear()
        logger.info("验证历史已清空")

    def validate_srt_file(self, srt_path: str) -> bool:
        """
        验证SRT字幕文件

        Args:
            srt_path: SRT文件路径

        Returns:
            bool: 验证是否通过
        """
        try:
            if not os.path.exists(srt_path):
                logger.error(f"SRT文件不存在: {srt_path}")
                return False

            if not srt_path.lower().endswith('.srt'):
                logger.error(f"文件不是SRT格式: {srt_path}")
                return False

            # 读取并验证SRT内容
            with open(srt_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 基本的SRT格式验证
            srt_pattern = r'\d+\s*\n\d{2}:\d{2}:\d{2},\d{3}\s*-->\s*\d{2}:\d{2}:\d{2},\d{3}\s*\n.+?(?=\n\d+\s*\n|\n*$)'
            matches = re.findall(srt_pattern, content, re.DOTALL)

            if len(matches) == 0:
                logger.error(f"SRT文件格式无效: {srt_path}")
                return False

            logger.info(f"SRT文件验证通过: {srt_path}, 包含 {len(matches)} 个字幕条目")
            return True

        except Exception as e:
            logger.error(f"SRT文件验证失败: {srt_path}, 错误: {e}")
            return False

    def validate_video_file(self, video_path: str) -> bool:
        """
        验证视频文件

        Args:
            video_path: 视频文件路径

        Returns:
            bool: 验证是否通过
        """
        try:
            if not os.path.exists(video_path):
                logger.error(f"视频文件不存在: {video_path}")
                return False

            # 检查文件扩展名
            valid_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv']
            file_ext = os.path.splitext(video_path)[1].lower()

            if file_ext not in valid_extensions:
                logger.error(f"不支持的视频格式: {file_ext}")
                return False

            # 检查文件大小
            file_size = os.path.getsize(video_path)
            if file_size == 0:
                logger.error(f"视频文件为空: {video_path}")
                return False

            logger.info(f"视频文件验证通过: {video_path}, 大小: {file_size / (1024*1024):.2f}MB")
            return True

        except Exception as e:
            logger.error(f"视频文件验证失败: {video_path}, 错误: {e}")
            return False

# 便捷函数
def validate_input_files(video_path: str, subtitle_path: str) -> ValidationResult:
    """
    便捷函数：验证输入文件

    Args:
        video_path: 视频文件路径
        subtitle_path: 字幕文件路径

    Returns:
        ValidationResult: 验证结果
    """
    validator = InputValidator()
    return validator.validate_input_files(video_path, subtitle_path)

def quick_format_check(video_path: str, subtitle_path: str) -> bool:
    """
    快速格式检查

    Args:
        video_path: 视频文件路径
        subtitle_path: 字幕文件路径

    Returns:
        bool: 格式是否正确
    """
    try:
        # 检查文件扩展名
        video_ext = Path(video_path).suffix.lower()
        subtitle_ext = Path(subtitle_path).suffix.lower()

        video_valid = video_ext in InputValidator.SUPPORTED_VIDEO_FORMATS
        subtitle_valid = subtitle_ext in InputValidator.SUPPORTED_SUBTITLE_FORMATS

        return video_valid and subtitle_valid

    except Exception:
        return False
