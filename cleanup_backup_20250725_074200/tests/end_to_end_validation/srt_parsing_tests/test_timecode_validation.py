#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 时间码验证测试模块

此模块专门测试SRT文件中时间码的精确性和有效性，确保时间码能够准确对应到原片视频的正确位置。
包括时间码格式验证、精度测试、边界条件检查等。
"""

import os
import sys
import json
import time
import logging
import unittest
import tempfile
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
import re
import math

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

# 导入核心模块
from src.core.srt_parser import SRTParser
from src.core.video_processor import VideoProcessor
from src.utils.log_handler import LogHandler

logger = logging.getLogger(__name__)


@dataclass
class TimecodeValidationResult:
    """时间码验证测试结果数据类"""
    test_name: str
    srt_file_path: str
    video_file_path: Optional[str]
    total_timecodes: int
    valid_timecodes: int
    invalid_timecodes: int
    precision_errors: List[Dict[str, Any]]
    boundary_errors: List[Dict[str, Any]]
    sequence_errors: List[Dict[str, Any]]
    video_alignment_errors: List[Dict[str, Any]]
    max_precision_error: float
    avg_precision_error: float
    video_duration_match: bool
    success: bool
    processing_time: float
    error_message: Optional[str] = None


class TimecodeValidator:
    """时间码验证器"""
    
    def __init__(self, config_path: str = None):
        """初始化时间码验证器"""
        self.config = self._load_config(config_path)
        
        # 设置日志
        self.logger = LogHandler.get_logger(
            name=__name__,
            level=self.config.get('test_environment', {}).get('log_level', 'INFO')
        )
        
        # 初始化核心组件
        self.srt_parser = SRTParser()
        self.video_processor = VideoProcessor()
        
        # 精度标准
        self.precision_threshold = self.config.get('quality_standards', {}).get('functional', {}).get('timecode_precision_seconds', 0.1)
        
        # 测试结果存储
        self.test_results = []
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """加载配置"""
        if config_path is None:
            config_path = "tests/end_to_end_validation/e2e_config.yaml"
        
        try:
            import yaml
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.logger.warning(f"无法加载配置文件 {config_path}: {e}")
            return {
                'quality_standards': {'functional': {'timecode_precision_seconds': 0.1}},
                'test_environment': {'log_level': 'INFO'}
            }
    
    def validate_timecode_format(self, srt_file_path: str) -> TimecodeValidationResult:
        """
        验证时间码格式
        
        Args:
            srt_file_path: SRT文件路径
            
        Returns:
            TimecodeValidationResult: 验证结果
        """
        test_name = "timecode_format_validation"
        start_time = time.time()
        
        try:
            # 解析SRT文件
            segments = self.srt_parser.parse(srt_file_path)
            
            total_timecodes = len(segments) * 2  # 每个片段有开始和结束时间
            valid_timecodes = 0
            invalid_timecodes = 0
            precision_errors = []
            boundary_errors = []
            sequence_errors = []
            
            for i, segment in enumerate(segments):
                start_time_str = segment.get('start_time', '')
                end_time_str = segment.get('end_time', '')
                
                # 验证开始时间码格式
                start_valid = self._validate_timecode_format(start_time_str)
                if start_valid:
                    valid_timecodes += 1
                else:
                    invalid_timecodes += 1
                    precision_errors.append({
                        'segment_index': i + 1,
                        'timecode_type': 'start',
                        'timecode': start_time_str,
                        'error': 'invalid_format'
                    })
                
                # 验证结束时间码格式
                end_valid = self._validate_timecode_format(end_time_str)
                if end_valid:
                    valid_timecodes += 1
                else:
                    invalid_timecodes += 1
                    precision_errors.append({
                        'segment_index': i + 1,
                        'timecode_type': 'end',
                        'timecode': end_time_str,
                        'error': 'invalid_format'
                    })
                
                # 如果两个时间码都有效，进行进一步验证
                if start_valid and end_valid:
                    start_seconds = self._timecode_to_seconds(start_time_str)
                    end_seconds = self._timecode_to_seconds(end_time_str)
                    
                    # 检查时间逻辑
                    if start_seconds >= end_seconds:
                        sequence_errors.append({
                            'segment_index': i + 1,
                            'start_time': start_time_str,
                            'end_time': end_time_str,
                            'error': 'end_time_not_after_start_time'
                        })
                    
                    # 检查边界条件
                    if start_seconds < 0:
                        boundary_errors.append({
                            'segment_index': i + 1,
                            'timecode': start_time_str,
                            'error': 'negative_time'
                        })
                    
                    # 检查时长合理性
                    duration = end_seconds - start_seconds
                    if duration > 600:  # 超过10分钟的单个片段
                        boundary_errors.append({
                            'segment_index': i + 1,
                            'duration': duration,
                            'error': 'segment_too_long'
                        })
                    elif duration < 0.1:  # 少于0.1秒的片段
                        boundary_errors.append({
                            'segment_index': i + 1,
                            'duration': duration,
                            'error': 'segment_too_short'
                        })
            
            # 检查片段间的时间序列
            for i in range(len(segments) - 1):
                current_segment = segments[i]
                next_segment = segments[i + 1]
                
                current_end = self._timecode_to_seconds(current_segment.get('end_time', ''))
                next_start = self._timecode_to_seconds(next_segment.get('start_time', ''))
                
                if current_end is not None and next_start is not None:
                    if current_end > next_start:
                        sequence_errors.append({
                            'segment_index': i + 1,
                            'next_segment_index': i + 2,
                            'overlap_duration': current_end - next_start,
                            'error': 'segments_overlap'
                        })
            
            # 计算精度统计
            all_errors = precision_errors + boundary_errors + sequence_errors
            max_precision_error = 0.0
            avg_precision_error = 0.0
            
            if precision_errors:
                # 这里可以添加更详细的精度误差计算
                max_precision_error = 1.0  # 格式错误视为最大误差
                avg_precision_error = len(precision_errors) / total_timecodes
            
            success = len(all_errors) == 0
            
            result = TimecodeValidationResult(
                test_name=test_name,
                srt_file_path=srt_file_path,
                video_file_path=None,
                total_timecodes=total_timecodes,
                valid_timecodes=valid_timecodes,
                invalid_timecodes=invalid_timecodes,
                precision_errors=precision_errors,
                boundary_errors=boundary_errors,
                sequence_errors=sequence_errors,
                video_alignment_errors=[],
                max_precision_error=max_precision_error,
                avg_precision_error=avg_precision_error,
                video_duration_match=True,  # 没有视频文件时默认为True
                success=success,
                processing_time=time.time() - start_time
            )
            
            self.test_results.append(result)
            self.logger.info(f"时间码格式验证完成: {srt_file_path}, 有效时间码: {valid_timecodes}/{total_timecodes}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"时间码格式验证失败: {srt_file_path}, 错误: {str(e)}")
            return TimecodeValidationResult(
                test_name=test_name,
                srt_file_path=srt_file_path,
                video_file_path=None,
                total_timecodes=0,
                valid_timecodes=0,
                invalid_timecodes=0,
                precision_errors=[],
                boundary_errors=[],
                sequence_errors=[],
                video_alignment_errors=[],
                max_precision_error=0.0,
                avg_precision_error=0.0,
                video_duration_match=False,
                success=False,
                processing_time=time.time() - start_time,
                error_message=str(e)
            )
    
    def validate_precision_boundaries(self, srt_file_path: str) -> TimecodeValidationResult:
        """
        验证时间码精度边界
        
        Args:
            srt_file_path: SRT文件路径
            
        Returns:
            TimecodeValidationResult: 验证结果
        """
        test_name = "precision_boundary_validation"
        start_time = time.time()
        
        try:
            # 解析SRT文件
            segments = self.srt_parser.parse(srt_file_path)
            
            precision_errors = []
            boundary_errors = []
            
            # 检查毫秒精度
            for i, segment in enumerate(segments):
                start_time_str = segment.get('start_time', '')
                end_time_str = segment.get('end_time', '')
                
                # 检查毫秒部分的精度
                if self._validate_timecode_format(start_time_str):
                    ms_part = start_time_str.split(',')[1] if ',' in start_time_str else '000'
                    if len(ms_part) != 3:
                        precision_errors.append({
                            'segment_index': i + 1,
                            'timecode': start_time_str,
                            'error': 'invalid_millisecond_precision'
                        })
                
                if self._validate_timecode_format(end_time_str):
                    ms_part = end_time_str.split(',')[1] if ',' in end_time_str else '000'
                    if len(ms_part) != 3:
                        precision_errors.append({
                            'segment_index': i + 1,
                            'timecode': end_time_str,
                            'error': 'invalid_millisecond_precision'
                        })
                
                # 检查时间码的数值边界
                start_seconds = self._timecode_to_seconds(start_time_str)
                end_seconds = self._timecode_to_seconds(end_time_str)
                
                if start_seconds is not None:
                    if start_seconds > 86400:  # 超过24小时
                        boundary_errors.append({
                            'segment_index': i + 1,
                            'timecode': start_time_str,
                            'error': 'exceeds_24_hours'
                        })
                
                if end_seconds is not None:
                    if end_seconds > 86400:  # 超过24小时
                        boundary_errors.append({
                            'segment_index': i + 1,
                            'timecode': end_time_str,
                            'error': 'exceeds_24_hours'
                        })
            
            all_errors = precision_errors + boundary_errors
            success = len(all_errors) == 0
            
            result = TimecodeValidationResult(
                test_name=test_name,
                srt_file_path=srt_file_path,
                video_file_path=None,
                total_timecodes=len(segments) * 2,
                valid_timecodes=len(segments) * 2 - len(all_errors),
                invalid_timecodes=len(all_errors),
                precision_errors=precision_errors,
                boundary_errors=boundary_errors,
                sequence_errors=[],
                video_alignment_errors=[],
                max_precision_error=1.0 if precision_errors else 0.0,
                avg_precision_error=len(precision_errors) / (len(segments) * 2) if segments else 0.0,
                video_duration_match=True,
                success=success,
                processing_time=time.time() - start_time
            )
            
            self.test_results.append(result)
            self.logger.info(f"精度边界验证完成: {srt_file_path}, 精度错误: {len(precision_errors)}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"精度边界验证失败: {srt_file_path}, 错误: {str(e)}")
            return TimecodeValidationResult(
                test_name=test_name,
                srt_file_path=srt_file_path,
                video_file_path=None,
                total_timecodes=0,
                valid_timecodes=0,
                invalid_timecodes=0,
                precision_errors=[],
                boundary_errors=[],
                sequence_errors=[],
                video_alignment_errors=[],
                max_precision_error=0.0,
                avg_precision_error=0.0,
                video_duration_match=False,
                success=False,
                processing_time=time.time() - start_time,
                error_message=str(e)
            )
    
    def _validate_timecode_format(self, timecode: str) -> bool:
        """验证时间码格式"""
        # SRT时间码格式：HH:MM:SS,mmm
        pattern = r'^\d{2}:\d{2}:\d{2},\d{3}$'
        return bool(re.match(pattern, timecode.strip()))
    
    def _timecode_to_seconds(self, timecode: str) -> Optional[float]:
        """将时间码转换为秒数"""
        try:
            if not self._validate_timecode_format(timecode):
                return None
            
            time_part, ms_part = timecode.strip().split(',')
            hours, minutes, seconds = map(int, time_part.split(':'))
            milliseconds = int(ms_part)
            
            total_seconds = hours * 3600 + minutes * 60 + seconds + milliseconds / 1000.0
            return total_seconds
        except (ValueError, IndexError):
            return None


class TestTimecodeValidation(unittest.TestCase):
    """时间码验证测试用例类"""
    
    @classmethod
    def setUpClass(cls):
        """设置测试类"""
        cls.validator = TimecodeValidator()
        cls.test_srt_file = cls._create_test_srt_file()
        cls.invalid_srt_file = cls._create_invalid_srt_file()
    
    @classmethod
    def _create_test_srt_file(cls) -> str:
        """创建测试SRT文件"""
        test_content = """1
00:00:10,000 --> 00:00:15,000
正常的时间码格式

2
00:00:20,000 --> 00:00:25,000
另一个正常片段

3
00:00:30,000 --> 00:00:35,000
第三个片段
"""
        
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.srt', delete=False, encoding='utf-8')
        temp_file.write(test_content)
        temp_file.close()
        
        return temp_file.name
    
    @classmethod
    def _create_invalid_srt_file(cls) -> str:
        """创建包含无效时间码的SRT文件"""
        invalid_content = """1
00:00:10,000 --> 00:00:05,000
结束时间早于开始时间

2
25:00:00,000 --> 25:00:05,000
超过24小时的时间码

3
00:00:30,00 --> 00:00:35,000
毫秒格式错误
"""
        
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.srt', delete=False, encoding='utf-8')
        temp_file.write(invalid_content)
        temp_file.close()
        
        return temp_file.name
    
    def test_valid_timecode_format(self):
        """测试有效时间码格式"""
        result = self.validator.validate_timecode_format(self.test_srt_file)
        
        self.assertTrue(result.success, "有效时间码格式验证应该成功")
        self.assertEqual(result.total_timecodes, 6, "应该有6个时间码")
        self.assertEqual(result.valid_timecodes, 6, "所有时间码都应该有效")
        self.assertEqual(len(result.precision_errors), 0, "不应该有精度错误")
    
    def test_invalid_timecode_format(self):
        """测试无效时间码格式"""
        result = self.validator.validate_timecode_format(self.invalid_srt_file)
        
        self.assertFalse(result.success, "无效时间码格式验证应该失败")
        self.assertGreater(len(result.sequence_errors), 0, "应该检测到序列错误")
        self.assertGreater(len(result.boundary_errors), 0, "应该检测到边界错误")
    
    def test_precision_boundaries(self):
        """测试精度边界"""
        result = self.validator.validate_precision_boundaries(self.test_srt_file)
        
        self.assertTrue(result.success, "精度边界验证应该成功")
        self.assertEqual(len(result.precision_errors), 0, "不应该有精度错误")
    
    @classmethod
    def tearDownClass(cls):
        """清理测试类"""
        if os.path.exists(cls.test_srt_file):
            os.unlink(cls.test_srt_file)
        if os.path.exists(cls.invalid_srt_file):
            os.unlink(cls.invalid_srt_file)


if __name__ == "__main__":
    unittest.main(verbosity=2)
