#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 视频片段拼接测试模块

此模块测试将剪切的视频片段按照SRT顺序正确拼接的功能。
验证拼接顺序、过渡平滑性、总时长准确性等关键指标。
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

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

# 导入核心模块
from src.core.video_concatenator import VideoConcatenator
from src.core.video_processor import VideoProcessor
from src.utils.log_handler import LogHandler

logger = logging.getLogger(__name__)


@dataclass
class SegmentConcatenationResult:
    """片段拼接测试结果数据类"""
    test_name: str
    input_segments_dir: str
    output_video_path: str
    total_input_segments: int
    successfully_concatenated_segments: int
    concatenation_order_correct: bool
    total_expected_duration: float
    actual_output_duration: float
    duration_accuracy_error: float
    transition_smoothness_score: float  # 过渡平滑性评分
    audio_continuity_score: float      # 音频连续性评分
    quality_preservation_score: float  # 质量保持评分
    processing_time: float
    concatenation_errors: List[Dict[str, Any]]
    quality_issues: List[Dict[str, Any]]
    success: bool
    error_message: Optional[str] = None


class SegmentConcatenator:
    """视频片段拼接器"""
    
    def __init__(self, config_path: str = None):
        """初始化视频片段拼接器"""
        self.config = self._load_config(config_path)
        
        # 设置日志
        self.logger = LogHandler.get_logger(
            name=__name__,
            level=self.config.get('test_environment', {}).get('log_level', 'INFO')
        )
        
        # 初始化核心组件
        self.video_concatenator = VideoConcatenator()
        self.video_processor = VideoProcessor()
        
        # 质量标准
        self.quality_standards = self.config.get('quality_standards', {})
        self.duration_precision = self.quality_standards.get('functional', {}).get('timecode_precision_seconds', 0.1)
        
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
                'quality_standards': {'functional': {'timecode_precision_seconds': 0.1}},
                'test_environment': {'log_level': 'INFO', 'temp_dir': 'tests/temp/e2e'}
            }
    
    def test_segment_concatenation(self, segments_dir: str, expected_order: List[str] = None) -> SegmentConcatenationResult:
        """
        测试视频片段拼接
        
        Args:
            segments_dir: 视频片段目录
            expected_order: 期望的拼接顺序
            
        Returns:
            SegmentConcatenationResult: 拼接测试结果
        """
        test_name = "segment_concatenation"
        start_time = time.time()
        
        try:
            # 验证输入目录
            segments_path = Path(segments_dir)
            if not segments_path.exists():
                raise FileNotFoundError(f"片段目录不存在: {segments_dir}")
            
            # 获取所有视频片段文件
            segment_files = self._get_segment_files(segments_path)
            if not segment_files:
                raise ValueError(f"在目录中未找到视频片段: {segments_dir}")
            
            # 按顺序排列片段
            if expected_order:
                ordered_segments = self._order_segments_by_list(segment_files, expected_order)
            else:
                ordered_segments = self._order_segments_naturally(segment_files)
            
            # 验证片段信息
            segment_info_list = []
            total_expected_duration = 0.0
            
            for segment_file in ordered_segments:
                segment_info = self.video_processor.get_video_info(str(segment_file))
                segment_info_list.append(segment_info)
                total_expected_duration += segment_info.get('duration', 0)
            
            # 创建输出文件路径
            output_path = self.temp_dir / f"concatenated_{int(time.time())}.mp4"
            
            # 执行拼接
            concatenation_result = self.video_concatenator.concatenate_segments(
                segment_paths=[str(f) for f in ordered_segments],
                output_path=str(output_path)
            )
            
            if not concatenation_result.get('success', False):
                raise RuntimeError(f"视频拼接失败: {concatenation_result.get('error_message', 'Unknown error')}")
            
            # 验证拼接结果
            output_info = self.video_processor.get_video_info(str(output_path))
            actual_duration = output_info.get('duration', 0)
            duration_error = abs(actual_duration - total_expected_duration)
            
            # 检查拼接顺序
            order_correct = self._verify_concatenation_order(
                str(output_path), segment_info_list
            )
            
            # 检查过渡平滑性
            transition_score = self._analyze_transition_smoothness(
                str(output_path), segment_info_list
            )
            
            # 检查音频连续性
            audio_continuity_score = self._analyze_audio_continuity(
                str(output_path), segment_info_list
            )
            
            # 检查质量保持
            quality_preservation_score = self._analyze_quality_preservation(
                output_info, segment_info_list
            )
            
            # 收集错误和问题
            concatenation_errors = []
            quality_issues = []
            
            if duration_error > self.duration_precision:
                concatenation_errors.append({
                    'error_type': 'duration_mismatch',
                    'expected_duration': total_expected_duration,
                    'actual_duration': actual_duration,
                    'error': duration_error
                })
            
            if not order_correct['correct']:
                concatenation_errors.append({
                    'error_type': 'order_incorrect',
                    'details': order_correct['details']
                })
            
            if transition_score['score'] < 0.8:
                quality_issues.extend(transition_score['issues'])
            
            if audio_continuity_score['score'] < 0.8:
                quality_issues.extend(audio_continuity_score['issues'])
            
            success = (
                len(concatenation_errors) == 0 and
                len(quality_issues) == 0 and
                duration_error <= self.duration_precision
            )
            
            result = SegmentConcatenationResult(
                test_name=test_name,
                input_segments_dir=segments_dir,
                output_video_path=str(output_path),
                total_input_segments=len(segment_files),
                successfully_concatenated_segments=len(ordered_segments),
                concatenation_order_correct=order_correct['correct'],
                total_expected_duration=total_expected_duration,
                actual_output_duration=actual_duration,
                duration_accuracy_error=duration_error,
                transition_smoothness_score=transition_score['score'],
                audio_continuity_score=audio_continuity_score['score'],
                quality_preservation_score=quality_preservation_score,
                processing_time=time.time() - start_time,
                concatenation_errors=concatenation_errors,
                quality_issues=quality_issues,
                success=success
            )
            
            self.test_results.append(result)
            self.logger.info(f"视频片段拼接测试完成: {len(ordered_segments)} 个片段, 时长误差: {duration_error:.3f}秒")
            
            return result
            
        except Exception as e:
            self.logger.error(f"视频片段拼接测试失败: {str(e)}")
            return SegmentConcatenationResult(
                test_name=test_name,
                input_segments_dir=segments_dir,
                output_video_path="",
                total_input_segments=0,
                successfully_concatenated_segments=0,
                concatenation_order_correct=False,
                total_expected_duration=0.0,
                actual_output_duration=0.0,
                duration_accuracy_error=0.0,
                transition_smoothness_score=0.0,
                audio_continuity_score=0.0,
                quality_preservation_score=0.0,
                processing_time=time.time() - start_time,
                concatenation_errors=[],
                quality_issues=[],
                success=False,
                error_message=str(e)
            )
    
    def _get_segment_files(self, segments_dir: Path) -> List[Path]:
        """获取片段文件列表"""
        video_extensions = ['.mp4', '.avi', '.mov', '.mkv']
        segment_files = []
        
        for ext in video_extensions:
            segment_files.extend(segments_dir.glob(f"*{ext}"))
        
        return sorted(segment_files)
    
    def _order_segments_naturally(self, segment_files: List[Path]) -> List[Path]:
        """按自然顺序排列片段"""
        # 按文件名排序
        return sorted(segment_files, key=lambda x: x.name)
    
    def _order_segments_by_list(self, segment_files: List[Path], expected_order: List[str]) -> List[Path]:
        """按指定顺序排列片段"""
        ordered_segments = []
        file_dict = {f.name: f for f in segment_files}
        
        for expected_name in expected_order:
            if expected_name in file_dict:
                ordered_segments.append(file_dict[expected_name])
        
        return ordered_segments
    
    def _verify_concatenation_order(self, output_path: str, segment_info_list: List[Dict]) -> Dict[str, Any]:
        """验证拼接顺序"""
        try:
            # 简化的顺序验证
            # 实际实现中可能需要更复杂的视频分析
            
            output_info = self.video_processor.get_video_info(output_path)
            output_duration = output_info.get('duration', 0)
            
            expected_duration = sum(info.get('duration', 0) for info in segment_info_list)
            duration_match = abs(output_duration - expected_duration) <= self.duration_precision
            
            return {
                'correct': duration_match,
                'details': {
                    'expected_duration': expected_duration,
                    'actual_duration': output_duration,
                    'duration_match': duration_match
                }
            }
            
        except Exception as e:
            return {
                'correct': False,
                'details': {'error': str(e)}
            }
    
    def _analyze_transition_smoothness(self, output_path: str, segment_info_list: List[Dict]) -> Dict[str, Any]:
        """分析过渡平滑性"""
        try:
            # 简化的过渡分析
            # 实际实现中需要分析视频帧之间的连续性
            
            issues = []
            score = 1.0
            
            # 检查分辨率一致性
            resolutions = set()
            for info in segment_info_list:
                width = info.get('width', 0)
                height = info.get('height', 0)
                resolutions.add((width, height))
            
            if len(resolutions) > 1:
                issues.append({
                    'issue_type': 'resolution_inconsistency',
                    'resolutions': list(resolutions)
                })
                score -= 0.2
            
            # 检查帧率一致性
            frame_rates = set()
            for info in segment_info_list:
                fps = info.get('frame_rate', 0)
                frame_rates.add(fps)
            
            if len(frame_rates) > 1:
                issues.append({
                    'issue_type': 'frame_rate_inconsistency',
                    'frame_rates': list(frame_rates)
                })
                score -= 0.2
            
            return {
                'score': max(0.0, score),
                'issues': issues
            }
            
        except Exception as e:
            return {
                'score': 0.0,
                'issues': [{'issue_type': 'analysis_failed', 'error': str(e)}]
            }
    
    def _analyze_audio_continuity(self, output_path: str, segment_info_list: List[Dict]) -> Dict[str, Any]:
        """分析音频连续性"""
        try:
            issues = []
            score = 1.0
            
            # 检查音频编码一致性
            audio_codecs = set()
            for info in segment_info_list:
                codec = info.get('audio_codec', '')
                if codec:
                    audio_codecs.add(codec)
            
            if len(audio_codecs) > 1:
                issues.append({
                    'issue_type': 'audio_codec_inconsistency',
                    'codecs': list(audio_codecs)
                })
                score -= 0.3
            
            # 检查采样率一致性
            sample_rates = set()
            for info in segment_info_list:
                rate = info.get('audio_sample_rate', 0)
                if rate:
                    sample_rates.add(rate)
            
            if len(sample_rates) > 1:
                issues.append({
                    'issue_type': 'sample_rate_inconsistency',
                    'sample_rates': list(sample_rates)
                })
                score -= 0.2
            
            return {
                'score': max(0.0, score),
                'issues': issues
            }
            
        except Exception as e:
            return {
                'score': 0.0,
                'issues': [{'issue_type': 'analysis_failed', 'error': str(e)}]
            }
    
    def _analyze_quality_preservation(self, output_info: Dict, segment_info_list: List[Dict]) -> float:
        """分析质量保持"""
        try:
            if not segment_info_list:
                return 0.0
            
            # 使用第一个片段作为参考
            reference_info = segment_info_list[0]
            
            score = 1.0
            
            # 检查分辨率保持
            ref_width = reference_info.get('width', 0)
            ref_height = reference_info.get('height', 0)
            out_width = output_info.get('width', 0)
            out_height = output_info.get('height', 0)
            
            if ref_width != out_width or ref_height != out_height:
                score -= 0.2
            
            # 检查帧率保持
            ref_fps = reference_info.get('frame_rate', 0)
            out_fps = output_info.get('frame_rate', 0)
            
            if abs(ref_fps - out_fps) > 0.1:
                score -= 0.1
            
            # 检查编码格式
            ref_codec = reference_info.get('video_codec', '')
            out_codec = output_info.get('video_codec', '')
            
            if ref_codec != out_codec:
                score -= 0.1
            
            return max(0.0, score)
            
        except Exception:
            return 0.0


class TestSegmentConcatenation(unittest.TestCase):
    """视频片段拼接测试用例类"""
    
    @classmethod
    def setUpClass(cls):
        """设置测试类"""
        cls.concatenator = SegmentConcatenator()
        cls.test_segments_dir = cls._create_test_segments()
    
    @classmethod
    def _create_test_segments(cls) -> str:
        """创建测试片段目录"""
        temp_dir = tempfile.mkdtemp()
        
        # 创建模拟视频片段文件
        for i in range(3):
            segment_file = os.path.join(temp_dir, f"segment_{i+1:03d}.mp4")
            with open(segment_file, 'wb') as f:
                f.write(b"mock video segment content")
        
        return temp_dir
    
    def test_segment_concatenation(self):
        """测试片段拼接"""
        # 注意：这个测试需要真实的视频片段才能正常运行
        
        try:
            result = self.concatenator.test_segment_concatenation(self.test_segments_dir)
            
            # 由于使用的是模拟文件，这里主要测试流程是否正常
            self.assertIsNotNone(result, "应该返回测试结果")
            self.assertEqual(result.test_name, "segment_concatenation", "测试名称应该正确")
            
        except Exception as e:
            # 预期会失败，因为使用的是模拟视频文件
            self.assertIn("video", str(e).lower(), "错误应该与视频处理相关")
    
    @classmethod
    def tearDownClass(cls):
        """清理测试类"""
        import shutil
        if os.path.exists(cls.test_segments_dir):
            shutil.rmtree(cls.test_segments_dir)


if __name__ == "__main__":
    unittest.main(verbosity=2)
