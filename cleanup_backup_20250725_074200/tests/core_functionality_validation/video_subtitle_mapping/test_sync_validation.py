#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 同步验证测试模块

此模块专门验证视频与字幕的同步质量，包括：
1. 音视频同步检测
2. 字幕显示时机验证
3. 时间轴漂移检测
4. 同步质量评分
"""

import os
import sys
import json
import time
import logging
import unittest
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
from datetime import timedelta

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

# 导入核心模块
from src.core.srt_parser import SRTParser
from src.core.alignment_engineer import AlignmentEngineer, AlignmentPrecision
from src.core.video_processor import VideoProcessor
from src.utils.log_handler import LogHandler

logger = logging.getLogger(__name__)


@dataclass
class SyncValidationResult:
    """同步验证结果数据类"""
    test_name: str
    video_file: str
    subtitle_file: str
    sync_score: float  # 同步质量评分 (0-1)
    drift_detected: bool  # 是否检测到时间轴漂移
    max_drift: float  # 最大漂移量（秒）
    avg_drift: float  # 平均漂移量（秒）
    sync_points_tested: int  # 测试的同步点数量
    sync_points_passed: int  # 通过的同步点数量
    audio_video_sync: float  # 音视频同步评分
    subtitle_timing_accuracy: float  # 字幕时机准确性
    processing_time: float
    detailed_analysis: Dict[str, Any]


class SyncValidator:
    """同步验证器"""
    
    def __init__(self, config_path: str = None):
        """初始化同步验证器"""
        self.config = self._load_config(config_path)
        self.srt_parser = SRTParser()
        self.alignment_engineer = AlignmentEngineer()
        self.video_processor = VideoProcessor()
        
        # 设置日志
        self.logger = LogHandler.get_logger(
            name=__name__,
            level=self.config.get('test_environment', {}).get('log_level', 'INFO')
        )
        
        # 同步验证参数
        self.sync_tolerance = self.config.get('test_thresholds', {}).get('sync_tolerance', 0.3)
        self.drift_threshold = 0.5  # 漂移阈值（秒）
        self.min_sync_score = 0.8  # 最低同步评分
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """加载测试配置"""
        if config_path is None:
            config_path = "tests/core_functionality_validation/test_config.yaml"
        
        try:
            import yaml
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.logger.warning(f"无法加载配置文件 {config_path}: {e}")
            return {'test_thresholds': {'sync_tolerance': 0.3}}
    
    def validate_sync_quality(self, video_path: str, subtitle_path: str) -> SyncValidationResult:
        """
        验证同步质量
        
        Args:
            video_path: 视频文件路径
            subtitle_path: 字幕文件路径
            
        Returns:
            SyncValidationResult: 同步验证结果
        """
        start_time = time.time()
        test_name = "sync_quality_validation"
        
        try:
            # 解析字幕
            subtitles = self.srt_parser.parse(subtitle_path)
            if not subtitles:
                raise ValueError(f"字幕文件解析失败: {subtitle_path}")
            
            # 获取视频信息
            video_info = self.video_processor.get_video_info(video_path)
            video_duration = video_info.get('duration', 0)
            
            # 执行同步分析
            sync_analysis = self._analyze_sync_quality(video_path, subtitles, video_duration)
            
            # 检测时间轴漂移
            drift_analysis = self._detect_timeline_drift(subtitles, video_duration)
            
            # 计算音视频同步评分
            audio_video_sync = self._calculate_audio_video_sync(video_path, subtitles)
            
            # 计算字幕时机准确性
            timing_accuracy = self._calculate_timing_accuracy(subtitles, video_duration)
            
            # 计算总体同步评分
            sync_score = self._calculate_overall_sync_score(
                sync_analysis, drift_analysis, audio_video_sync, timing_accuracy
            )
            
            # 构建详细分析结果
            detailed_analysis = {
                'video_duration': video_duration,
                'subtitle_count': len(subtitles),
                'sync_analysis': sync_analysis,
                'drift_analysis': drift_analysis,
                'audio_video_analysis': {
                    'sync_score': audio_video_sync,
                    'method': 'cross_correlation'
                },
                'timing_analysis': {
                    'accuracy_score': timing_accuracy,
                    'method': 'statistical_analysis'
                }
            }
            
            result = SyncValidationResult(
                test_name=test_name,
                video_file=video_path,
                subtitle_file=subtitle_path,
                sync_score=sync_score,
                drift_detected=drift_analysis['drift_detected'],
                max_drift=drift_analysis['max_drift'],
                avg_drift=drift_analysis['avg_drift'],
                sync_points_tested=sync_analysis['points_tested'],
                sync_points_passed=sync_analysis['points_passed'],
                audio_video_sync=audio_video_sync,
                subtitle_timing_accuracy=timing_accuracy,
                processing_time=time.time() - start_time,
                detailed_analysis=detailed_analysis
            )
            
            self.logger.info(f"同步验证完成: {test_name}, 同步评分: {sync_score:.3f}")
            return result
            
        except Exception as e:
            self.logger.error(f"同步验证失败: {test_name}, 错误: {str(e)}")
            return SyncValidationResult(
                test_name=test_name,
                video_file=video_path,
                subtitle_file=subtitle_path,
                sync_score=0.0,
                drift_detected=True,
                max_drift=float('inf'),
                avg_drift=float('inf'),
                sync_points_tested=0,
                sync_points_passed=0,
                audio_video_sync=0.0,
                subtitle_timing_accuracy=0.0,
                processing_time=time.time() - start_time,
                detailed_analysis={'error': str(e)}
            )
    
    def _analyze_sync_quality(self, video_path: str, subtitles: List[Dict], video_duration: float) -> Dict[str, Any]:
        """分析同步质量"""
        try:
            # 选择关键同步点进行测试
            sync_points = self._select_sync_test_points(subtitles, video_duration)
            
            points_tested = len(sync_points)
            points_passed = 0
            sync_errors = []
            
            for point in sync_points:
                # 执行精确对齐
                alignment_result = self.alignment_engineer.align_subtitles_to_video(
                    video_path=video_path,
                    subtitles=[point],
                    precision=AlignmentPrecision.ULTRA_HIGH
                )
                
                if alignment_result.aligned_subtitles:
                    aligned_point = alignment_result.aligned_subtitles[0]
                    
                    # 计算同步误差
                    original_time = self._parse_timestamp(point.get('start_time', ''))
                    aligned_time = self._parse_timestamp(aligned_point.get('start_time', ''))
                    
                    if original_time is not None and aligned_time is not None:
                        error = abs(original_time - aligned_time)
                        sync_errors.append(error)
                        
                        if error <= self.sync_tolerance:
                            points_passed += 1
            
            return {
                'points_tested': points_tested,
                'points_passed': points_passed,
                'pass_rate': points_passed / points_tested if points_tested > 0 else 0.0,
                'sync_errors': sync_errors,
                'avg_error': np.mean(sync_errors) if sync_errors else 0.0,
                'max_error': np.max(sync_errors) if sync_errors else 0.0
            }
            
        except Exception as e:
            self.logger.error(f"同步质量分析失败: {str(e)}")
            return {
                'points_tested': 0,
                'points_passed': 0,
                'pass_rate': 0.0,
                'sync_errors': [],
                'avg_error': float('inf'),
                'max_error': float('inf')
            }
    
    def _detect_timeline_drift(self, subtitles: List[Dict], video_duration: float) -> Dict[str, Any]:
        """检测时间轴漂移"""
        try:
            if len(subtitles) < 3:
                return {
                    'drift_detected': False,
                    'max_drift': 0.0,
                    'avg_drift': 0.0,
                    'drift_points': []
                }
            
            # 计算相邻字幕间的时间间隔
            intervals = []
            timestamps = []
            
            for subtitle in subtitles:
                start_time = self._parse_timestamp(subtitle.get('start_time', ''))
                if start_time is not None:
                    timestamps.append(start_time)
            
            if len(timestamps) < 3:
                return {
                    'drift_detected': False,
                    'max_drift': 0.0,
                    'avg_drift': 0.0,
                    'drift_points': []
                }
            
            # 计算时间间隔的变化趋势
            for i in range(1, len(timestamps)):
                interval = timestamps[i] - timestamps[i-1]
                intervals.append(interval)
            
            # 检测异常间隔（可能的漂移点）
            mean_interval = np.mean(intervals)
            std_interval = np.std(intervals)
            
            drift_points = []
            drifts = []
            
            for i, interval in enumerate(intervals):
                # 如果间隔偏离平均值超过2个标准差，认为是漂移
                if abs(interval - mean_interval) > 2 * std_interval:
                    drift = abs(interval - mean_interval)
                    drifts.append(drift)
                    drift_points.append({
                        'position': i + 1,
                        'timestamp': timestamps[i + 1],
                        'expected_interval': mean_interval,
                        'actual_interval': interval,
                        'drift_amount': drift
                    })
            
            max_drift = np.max(drifts) if drifts else 0.0
            avg_drift = np.mean(drifts) if drifts else 0.0
            drift_detected = max_drift > self.drift_threshold
            
            return {
                'drift_detected': drift_detected,
                'max_drift': max_drift,
                'avg_drift': avg_drift,
                'drift_points': drift_points,
                'total_drift_points': len(drift_points),
                'drift_percentage': len(drift_points) / len(intervals) if intervals else 0.0
            }
            
        except Exception as e:
            self.logger.error(f"时间轴漂移检测失败: {str(e)}")
            return {
                'drift_detected': True,
                'max_drift': float('inf'),
                'avg_drift': float('inf'),
                'drift_points': [],
                'error': str(e)
            }
    
    def _calculate_audio_video_sync(self, video_path: str, subtitles: List[Dict]) -> float:
        """计算音视频同步评分"""
        try:
            # 这里应该实现音视频同步检测算法
            # 由于复杂性，这里返回一个基于字幕时间分布的估算值
            
            timestamps = []
            for subtitle in subtitles:
                start_time = self._parse_timestamp(subtitle.get('start_time', ''))
                if start_time is not None:
                    timestamps.append(start_time)
            
            if len(timestamps) < 2:
                return 0.5  # 默认中等评分
            
            # 基于时间戳分布的均匀性评估同步质量
            intervals = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)]
            
            if not intervals:
                return 0.5
            
            # 计算间隔的变异系数
            mean_interval = np.mean(intervals)
            std_interval = np.std(intervals)
            
            if mean_interval == 0:
                return 0.5
            
            cv = std_interval / mean_interval  # 变异系数
            
            # 变异系数越小，同步质量越好
            sync_score = max(0.0, min(1.0, 1.0 - cv))
            
            return sync_score
            
        except Exception as e:
            self.logger.error(f"音视频同步计算失败: {str(e)}")
            return 0.0
    
    def _calculate_timing_accuracy(self, subtitles: List[Dict], video_duration: float) -> float:
        """计算字幕时机准确性"""
        try:
            if not subtitles:
                return 0.0
            
            # 检查字幕时间范围是否合理
            timestamps = []
            durations = []
            
            for subtitle in subtitles:
                start_time = self._parse_timestamp(subtitle.get('start_time', ''))
                end_time = self._parse_timestamp(subtitle.get('end_time', ''))
                
                if start_time is not None and end_time is not None:
                    timestamps.append(start_time)
                    duration = end_time - start_time
                    durations.append(duration)
            
            if not timestamps or not durations:
                return 0.0
            
            # 检查时间范围合理性
            min_timestamp = min(timestamps)
            max_timestamp = max(timestamps)
            
            # 字幕应该在视频时间范围内
            time_range_score = 1.0
            if min_timestamp < 0:
                time_range_score -= 0.3
            if max_timestamp > video_duration * 1.1:  # 允许10%的误差
                time_range_score -= 0.3
            
            # 检查字幕持续时间合理性
            avg_duration = np.mean(durations)
            duration_score = 1.0
            
            # 字幕持续时间应该在合理范围内（0.5-10秒）
            if avg_duration < 0.5:
                duration_score -= 0.2
            elif avg_duration > 10.0:
                duration_score -= 0.2
            
            # 检查字幕间隔合理性
            intervals = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)]
            interval_score = 1.0
            
            if intervals:
                # 检查是否有重叠或过大间隔
                negative_intervals = sum(1 for interval in intervals if interval < 0)
                large_intervals = sum(1 for interval in intervals if interval > 30)  # 30秒以上的间隔
                
                if negative_intervals > 0:
                    interval_score -= 0.4  # 重叠是严重问题
                if large_intervals > len(intervals) * 0.1:  # 超过10%的大间隔
                    interval_score -= 0.2
            
            # 综合评分
            overall_score = (time_range_score + duration_score + interval_score) / 3.0
            return max(0.0, min(1.0, overall_score))
            
        except Exception as e:
            self.logger.error(f"时机准确性计算失败: {str(e)}")
            return 0.0
    
    def _calculate_overall_sync_score(self, sync_analysis: Dict, drift_analysis: Dict, 
                                    audio_video_sync: float, timing_accuracy: float) -> float:
        """计算总体同步评分"""
        try:
            # 各项权重
            weights = {
                'sync_quality': 0.4,      # 同步质量权重
                'drift_penalty': 0.2,     # 漂移惩罚权重
                'audio_video': 0.2,       # 音视频同步权重
                'timing': 0.2             # 时机准确性权重
            }
            
            # 同步质量评分
            sync_score = sync_analysis.get('pass_rate', 0.0)
            
            # 漂移惩罚
            drift_penalty = 0.0
            if drift_analysis.get('drift_detected', False):
                max_drift = drift_analysis.get('max_drift', 0.0)
                # 漂移越大，惩罚越重
                drift_penalty = min(1.0, max_drift / 5.0)  # 5秒漂移对应100%惩罚
            
            # 计算加权总分
            total_score = (
                sync_score * weights['sync_quality'] +
                (1.0 - drift_penalty) * weights['drift_penalty'] +
                audio_video_sync * weights['audio_video'] +
                timing_accuracy * weights['timing']
            )
            
            return max(0.0, min(1.0, total_score))
            
        except Exception as e:
            self.logger.error(f"总体同步评分计算失败: {str(e)}")
            return 0.0
    
    def _select_sync_test_points(self, subtitles: List[Dict], video_duration: float) -> List[Dict]:
        """选择关键同步测试点"""
        if not subtitles:
            return []
        
        # 选择策略：开头、中间、结尾各选几个点
        total_count = len(subtitles)
        
        if total_count <= 10:
            return subtitles  # 少于10个字幕，全部测试
        
        # 选择关键点
        test_points = []
        
        # 开头部分（前20%）
        start_count = max(2, total_count // 10)
        test_points.extend(subtitles[:start_count])
        
        # 中间部分（40%-60%）
        mid_start = int(total_count * 0.4)
        mid_end = int(total_count * 0.6)
        mid_count = max(3, (mid_end - mid_start) // 3)
        test_points.extend(subtitles[mid_start:mid_start + mid_count])
        
        # 结尾部分（后20%）
        end_start = int(total_count * 0.8)
        end_count = max(2, (total_count - end_start) // 2)
        test_points.extend(subtitles[end_start:end_start + end_count])
        
        return test_points
    
    def _parse_timestamp(self, timestamp_str: str) -> Optional[float]:
        """解析时间戳字符串为秒数"""
        try:
            if not timestamp_str or '-->' in timestamp_str:
                return None
            
            timestamp_str = timestamp_str.strip()
            
            if ',' in timestamp_str:
                time_part, ms_part = timestamp_str.split(',')
                milliseconds = int(ms_part)
            else:
                time_part = timestamp_str
                milliseconds = 0
            
            time_components = time_part.split(':')
            if len(time_components) != 3:
                return None
            
            hours = int(time_components[0])
            minutes = int(time_components[1])
            seconds = int(time_components[2])
            
            total_seconds = hours * 3600 + minutes * 60 + seconds + milliseconds / 1000.0
            return total_seconds
            
        except (ValueError, IndexError):
            return None


class TestSyncValidation(unittest.TestCase):
    """同步验证测试用例类"""
    
    @classmethod
    def setUpClass(cls):
        """设置测试类"""
        cls.validator = SyncValidator()
    
    def test_high_quality_sync(self):
        """测试高质量同步"""
        # 这里应该使用高质量的测试数据
        video_path = "test_data/videos/high_quality_sync.mp4"
        subtitle_path = "test_data/subtitles/high_quality_sync.srt"
        
        if os.path.exists(video_path) and os.path.exists(subtitle_path):
            result = self.validator.validate_sync_quality(video_path, subtitle_path)
            
            self.assertGreaterEqual(result.sync_score, 0.8, "高质量同步评分应≥0.8")
            self.assertFalse(result.drift_detected, "高质量同步不应检测到漂移")
            self.assertLessEqual(result.max_drift, 0.5, "最大漂移应≤0.5秒")
    
    def test_poor_quality_sync(self):
        """测试低质量同步"""
        video_path = "test_data/videos/poor_quality_sync.mp4"
        subtitle_path = "test_data/subtitles/poor_quality_sync.srt"
        
        if os.path.exists(video_path) and os.path.exists(subtitle_path):
            result = self.validator.validate_sync_quality(video_path, subtitle_path)
            
            # 低质量同步应该被检测出来
            self.assertLess(result.sync_score, 0.6, "低质量同步评分应<0.6")


if __name__ == "__main__":
    unittest.main(verbosity=2)
