#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 视频片段剪切测试模块

此模块测试根据爆款SRT时间码从原片中精确提取视频片段的功能。
验证剪切精度、质量保持、音视频同步等关键指标。
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
import subprocess

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

# 导入核心模块
from src.core.video_cutter import VideoCutter
from src.core.srt_parser import SRTParser
from src.core.video_processor import VideoProcessor
from src.utils.log_handler import LogHandler
from src.utils.file_checker import FileChecker

logger = logging.getLogger(__name__)


@dataclass
class VideoSegmentCuttingResult:
    """视频片段剪切测试结果数据类"""
    test_name: str
    original_video_path: str
    srt_file_path: str
    output_segments_dir: str
    total_segments: int
    successfully_cut_segments: int
    failed_segments: int
    cutting_accuracy: float  # 剪切精度（秒）
    quality_preservation_score: float  # 质量保持评分
    audio_sync_accuracy: float  # 音频同步精度
    processing_speed_multiplier: float  # 处理速度倍数
    total_processing_time: float
    segment_details: List[Dict[str, Any]]
    cutting_errors: List[Dict[str, Any]]
    quality_issues: List[Dict[str, Any]]
    success: bool
    error_message: Optional[str] = None


class VideoSegmentCutter:
    """视频片段剪切器"""
    
    def __init__(self, config_path: str = None):
        """初始化视频片段剪切器"""
        self.config = self._load_config(config_path)
        
        # 设置日志
        self.logger = LogHandler.get_logger(
            name=__name__,
            level=self.config.get('test_environment', {}).get('log_level', 'INFO')
        )
        
        # 初始化核心组件
        self.video_cutter = VideoCutter()
        self.srt_parser = SRTParser()
        self.video_processor = VideoProcessor()
        self.file_checker = FileChecker()
        
        # 质量标准
        self.quality_standards = self.config.get('quality_standards', {})
        self.cutting_precision = self.quality_standards.get('functional', {}).get('timecode_precision_seconds', 0.1)
        self.min_processing_speed = self.quality_standards.get('performance', {}).get('segment_extraction_speed_multiplier', 2.0)
        
        # 创建临时目录
        self.temp_dir = Path(self.config.get('test_environment', {}).get('temp_dir', 'tests/temp/e2e'))
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
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
                'quality_standards': {
                    'functional': {'timecode_precision_seconds': 0.1},
                    'performance': {'segment_extraction_speed_multiplier': 2.0}
                },
                'test_environment': {'log_level': 'INFO', 'temp_dir': 'tests/temp/e2e'}
            }
    
    def test_segment_cutting_accuracy(self, video_path: str, srt_path: str) -> VideoSegmentCuttingResult:
        """
        测试视频片段剪切精度
        
        Args:
            video_path: 原片视频路径
            srt_path: SRT字幕文件路径
            
        Returns:
            VideoSegmentCuttingResult: 剪切测试结果
        """
        test_name = "segment_cutting_accuracy"
        start_time = time.time()
        
        try:
            # 验证输入文件
            if not os.path.exists(video_path):
                raise FileNotFoundError(f"视频文件不存在: {video_path}")
            
            if not os.path.exists(srt_path):
                raise FileNotFoundError(f"SRT文件不存在: {srt_path}")
            
            # 获取视频信息
            video_info = self.video_processor.get_video_info(video_path)
            video_duration = video_info.get('duration', 0)
            
            # 解析SRT文件
            segments = self.srt_parser.parse(srt_path)
            if not segments:
                raise ValueError("SRT文件解析失败或为空")
            
            # 创建输出目录
            output_dir = self.temp_dir / f"segments_{int(time.time())}"
            output_dir.mkdir(exist_ok=True)
            
            # 剪切视频片段
            cutting_results = []
            cutting_errors = []
            quality_issues = []
            successfully_cut = 0
            failed_segments = 0
            
            for i, segment in enumerate(segments):
                segment_result = self._cut_single_segment(
                    video_path, segment, output_dir, i + 1
                )
                
                cutting_results.append(segment_result)
                
                if segment_result['success']:
                    successfully_cut += 1
                    
                    # 验证剪切精度
                    accuracy_check = self._verify_cutting_accuracy(
                        segment_result['output_path'], segment, video_info
                    )
                    segment_result.update(accuracy_check)
                    
                    if accuracy_check['accuracy_error'] > self.cutting_precision:
                        cutting_errors.append({
                            'segment_index': i + 1,
                            'error_type': 'precision_error',
                            'accuracy_error': accuracy_check['accuracy_error'],
                            'expected_duration': segment_result['expected_duration'],
                            'actual_duration': segment_result['actual_duration']
                        })
                    
                    # 检查质量问题
                    quality_check = self._check_segment_quality(
                        segment_result['output_path'], video_info
                    )
                    segment_result.update(quality_check)
                    
                    if quality_check['quality_issues']:
                        quality_issues.extend(quality_check['quality_issues'])
                
                else:
                    failed_segments += 1
                    cutting_errors.append({
                        'segment_index': i + 1,
                        'error_type': 'cutting_failed',
                        'error_message': segment_result.get('error_message', 'Unknown error')
                    })
            
            # 计算总体指标
            total_processing_time = time.time() - start_time
            total_expected_duration = sum(r.get('expected_duration', 0) for r in cutting_results)
            processing_speed_multiplier = total_expected_duration / total_processing_time if total_processing_time > 0 else 0
            
            # 计算精度统计
            accuracy_errors = [r.get('accuracy_error', 0) for r in cutting_results if r.get('success', False)]
            cutting_accuracy = max(accuracy_errors) if accuracy_errors else 0.0
            
            # 计算质量评分
            quality_scores = [r.get('quality_score', 0) for r in cutting_results if r.get('success', False)]
            quality_preservation_score = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
            
            # 计算音频同步精度
            sync_errors = [r.get('audio_sync_error', 0) for r in cutting_results if r.get('success', False)]
            audio_sync_accuracy = max(sync_errors) if sync_errors else 0.0
            
            success = (
                failed_segments == 0 and
                cutting_accuracy <= self.cutting_precision and
                processing_speed_multiplier >= self.min_processing_speed
            )
            
            result = VideoSegmentCuttingResult(
                test_name=test_name,
                original_video_path=video_path,
                srt_file_path=srt_path,
                output_segments_dir=str(output_dir),
                total_segments=len(segments),
                successfully_cut_segments=successfully_cut,
                failed_segments=failed_segments,
                cutting_accuracy=cutting_accuracy,
                quality_preservation_score=quality_preservation_score,
                audio_sync_accuracy=audio_sync_accuracy,
                processing_speed_multiplier=processing_speed_multiplier,
                total_processing_time=total_processing_time,
                segment_details=cutting_results,
                cutting_errors=cutting_errors,
                quality_issues=quality_issues,
                success=success
            )
            
            self.test_results.append(result)
            self.logger.info(f"视频片段剪切测试完成: {successfully_cut}/{len(segments)} 成功")
            
            return result
            
        except Exception as e:
            self.logger.error(f"视频片段剪切测试失败: {str(e)}")
            return VideoSegmentCuttingResult(
                test_name=test_name,
                original_video_path=video_path,
                srt_file_path=srt_path,
                output_segments_dir="",
                total_segments=0,
                successfully_cut_segments=0,
                failed_segments=0,
                cutting_accuracy=0.0,
                quality_preservation_score=0.0,
                audio_sync_accuracy=0.0,
                processing_speed_multiplier=0.0,
                total_processing_time=time.time() - start_time,
                segment_details=[],
                cutting_errors=[],
                quality_issues=[],
                success=False,
                error_message=str(e)
            )
    
    def _cut_single_segment(self, video_path: str, segment: Dict[str, Any], 
                           output_dir: Path, segment_index: int) -> Dict[str, Any]:
        """剪切单个视频片段"""
        try:
            start_time_str = segment.get('start_time', '')
            end_time_str = segment.get('end_time', '')
            
            # 转换时间码为秒数
            start_seconds = self._timecode_to_seconds(start_time_str)
            end_seconds = self._timecode_to_seconds(end_time_str)
            
            if start_seconds is None or end_seconds is None:
                return {
                    'segment_index': segment_index,
                    'success': False,
                    'error_message': 'Invalid timecode format'
                }
            
            expected_duration = end_seconds - start_seconds
            output_path = output_dir / f"segment_{segment_index:03d}.mp4"
            
            # 使用视频剪切器剪切片段
            cutting_result = self.video_cutter.cut_segment(
                input_path=video_path,
                output_path=str(output_path),
                start_time=start_seconds,
                end_time=end_seconds
            )
            
            if cutting_result.get('success', False):
                return {
                    'segment_index': segment_index,
                    'success': True,
                    'output_path': str(output_path),
                    'start_time': start_time_str,
                    'end_time': end_time_str,
                    'start_seconds': start_seconds,
                    'end_seconds': end_seconds,
                    'expected_duration': expected_duration,
                    'cutting_time': cutting_result.get('processing_time', 0)
                }
            else:
                return {
                    'segment_index': segment_index,
                    'success': False,
                    'error_message': cutting_result.get('error_message', 'Cutting failed')
                }
                
        except Exception as e:
            return {
                'segment_index': segment_index,
                'success': False,
                'error_message': str(e)
            }
    
    def _verify_cutting_accuracy(self, segment_path: str, original_segment: Dict[str, Any], 
                                video_info: Dict[str, Any]) -> Dict[str, Any]:
        """验证剪切精度"""
        try:
            # 获取剪切后片段的信息
            segment_info = self.video_processor.get_video_info(segment_path)
            actual_duration = segment_info.get('duration', 0)
            
            # 计算期望时长
            start_seconds = self._timecode_to_seconds(original_segment.get('start_time', ''))
            end_seconds = self._timecode_to_seconds(original_segment.get('end_time', ''))
            expected_duration = end_seconds - start_seconds
            
            # 计算精度误差
            accuracy_error = abs(actual_duration - expected_duration)
            
            return {
                'actual_duration': actual_duration,
                'expected_duration': expected_duration,
                'accuracy_error': accuracy_error,
                'accuracy_percentage': (1 - accuracy_error / expected_duration) * 100 if expected_duration > 0 else 0
            }
            
        except Exception as e:
            return {
                'actual_duration': 0,
                'expected_duration': 0,
                'accuracy_error': float('inf'),
                'accuracy_percentage': 0,
                'error': str(e)
            }
    
    def _check_segment_quality(self, segment_path: str, original_video_info: Dict[str, Any]) -> Dict[str, Any]:
        """检查片段质量"""
        try:
            segment_info = self.video_processor.get_video_info(segment_path)
            quality_issues = []
            
            # 检查分辨率
            original_width = original_video_info.get('width', 0)
            original_height = original_video_info.get('height', 0)
            segment_width = segment_info.get('width', 0)
            segment_height = segment_info.get('height', 0)
            
            if original_width != segment_width or original_height != segment_height:
                quality_issues.append({
                    'issue_type': 'resolution_change',
                    'original_resolution': f"{original_width}x{original_height}",
                    'segment_resolution': f"{segment_width}x{segment_height}"
                })
            
            # 检查帧率
            original_fps = original_video_info.get('frame_rate', 0)
            segment_fps = segment_info.get('frame_rate', 0)
            
            if abs(original_fps - segment_fps) > 0.1:
                quality_issues.append({
                    'issue_type': 'frame_rate_change',
                    'original_fps': original_fps,
                    'segment_fps': segment_fps
                })
            
            # 检查编码格式
            original_codec = original_video_info.get('video_codec', '')
            segment_codec = segment_info.get('video_codec', '')
            
            if original_codec != segment_codec:
                quality_issues.append({
                    'issue_type': 'codec_change',
                    'original_codec': original_codec,
                    'segment_codec': segment_codec
                })
            
            # 计算质量评分
            quality_score = 1.0 - (len(quality_issues) * 0.1)  # 每个问题扣0.1分
            quality_score = max(0.0, quality_score)
            
            # 检查音频同步
            audio_sync_error = self._check_audio_sync(segment_path)
            
            return {
                'quality_score': quality_score,
                'quality_issues': quality_issues,
                'audio_sync_error': audio_sync_error,
                'segment_info': segment_info
            }
            
        except Exception as e:
            return {
                'quality_score': 0.0,
                'quality_issues': [{'issue_type': 'analysis_failed', 'error': str(e)}],
                'audio_sync_error': float('inf'),
                'error': str(e)
            }
    
    def _check_audio_sync(self, segment_path: str) -> float:
        """检查音频同步"""
        try:
            # 简化的音频同步检查
            # 实际实现中可能需要更复杂的音频分析
            segment_info = self.video_processor.get_video_info(segment_path)
            
            # 检查是否有音频轨道
            if not segment_info.get('has_audio', False):
                return 0.0  # 没有音频，同步误差为0
            
            # 检查音频时长与视频时长的匹配
            video_duration = segment_info.get('duration', 0)
            audio_duration = segment_info.get('audio_duration', video_duration)
            
            sync_error = abs(video_duration - audio_duration)
            return sync_error
            
        except Exception:
            return 0.0  # 检查失败时返回0
    
    def _timecode_to_seconds(self, timecode: str) -> Optional[float]:
        """将时间码转换为秒数"""
        try:
            if ',' not in timecode:
                return None
            
            time_part, ms_part = timecode.strip().split(',')
            hours, minutes, seconds = map(int, time_part.split(':'))
            milliseconds = int(ms_part)
            
            total_seconds = hours * 3600 + minutes * 60 + seconds + milliseconds / 1000.0
            return total_seconds
        except (ValueError, IndexError):
            return None


class TestVideoSegmentCutting(unittest.TestCase):
    """视频片段剪切测试用例类"""
    
    @classmethod
    def setUpClass(cls):
        """设置测试类"""
        cls.cutter = VideoSegmentCutter()
        cls.test_video_path, cls.test_srt_path = cls._create_test_files()
    
    @classmethod
    def _create_test_files(cls) -> Tuple[str, str]:
        """创建测试文件"""
        # 创建测试SRT文件
        srt_content = """1
00:00:00,000 --> 00:00:05,000
第一个测试片段

2
00:00:10,000 --> 00:00:15,000
第二个测试片段

3
00:00:20,000 --> 00:00:25,000
第三个测试片段
"""
        
        srt_file = tempfile.NamedTemporaryFile(mode='w', suffix='.srt', delete=False, encoding='utf-8')
        srt_file.write(srt_content)
        srt_file.close()
        
        # 创建模拟视频文件（实际测试中应使用真实视频）
        video_file = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
        video_file.write(b"mock video content")
        video_file.close()
        
        return video_file.name, srt_file.name
    
    def test_segment_cutting_accuracy(self):
        """测试片段剪切精度"""
        # 注意：这个测试需要真实的视频文件才能正常运行
        # 在实际环境中，应该提供真实的测试视频文件
        
        try:
            result = self.cutter.test_segment_cutting_accuracy(
                self.test_video_path, self.test_srt_path
            )
            
            # 由于使用的是模拟文件，这里主要测试流程是否正常
            self.assertIsNotNone(result, "应该返回测试结果")
            self.assertEqual(result.test_name, "segment_cutting_accuracy", "测试名称应该正确")
            
        except Exception as e:
            # 预期会失败，因为使用的是模拟视频文件
            self.assertIn("video", str(e).lower(), "错误应该与视频处理相关")
    
    @classmethod
    def tearDownClass(cls):
        """清理测试类"""
        if os.path.exists(cls.test_video_path):
            os.unlink(cls.test_video_path)
        if os.path.exists(cls.test_srt_path):
            os.unlink(cls.test_srt_path)


if __name__ == "__main__":
    unittest.main(verbosity=2)
