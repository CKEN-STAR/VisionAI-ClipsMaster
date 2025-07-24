#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 时间轴精度测试模块

此模块验证原片视频与SRT字幕文件的时间轴对应关系，确保同步误差在可接受范围内（≤0.5秒）

测试目标：
1. 验证字幕时间码与视频帧的精确对应
2. 检查多语言字幕的解析准确性
3. 测试边界条件和异常情况处理
4. 评估时间轴映射的稳定性和可靠性
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
from datetime import timedelta
import numpy as np

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

# 导入核心模块
from src.core.srt_parser import SRTParser
from src.core.alignment_engineer import AlignmentEngineer, AlignmentPrecision
from src.core.language_detector import LanguageDetector
from src.utils.file_checker import FileChecker
from src.utils.log_handler import LogHandler

# 导入测试工具
from tests.golden_samples.compare_engine import CompareEngine
from tests.test_data_preparation import TestDataGenerator

logger = logging.getLogger(__name__)


@dataclass
class TimelineTestResult:
    """时间轴测试结果数据类"""
    test_name: str
    video_file: str
    subtitle_file: str
    language: str
    total_subtitles: int
    successful_mappings: int
    failed_mappings: int
    average_error: float
    max_error: float
    min_error: float
    errors_within_threshold: int
    threshold: float
    success_rate: float
    processing_time: float
    memory_usage: float
    detailed_errors: List[Dict[str, Any]]


class TimelineAccuracyTester:
    """时间轴精度测试器"""
    
    def __init__(self, config_path: str = None):
        """
        初始化测试器
        
        Args:
            config_path: 测试配置文件路径
        """
        self.config = self._load_config(config_path)
        self.srt_parser = SRTParser()
        self.alignment_engineer = AlignmentEngineer()
        self.language_detector = LanguageDetector()
        self.file_checker = FileChecker()
        self.compare_engine = CompareEngine()
        self.test_results = []
        
        # 设置日志
        self.logger = LogHandler.get_logger(
            name=__name__,
            level=self.config.get('test_environment', {}).get('log_level', 'INFO')
        )
        
        # 创建临时目录
        self.temp_dir = Path(self.config.get('test_environment', {}).get('temp_dir', 'tests/temp'))
        self.temp_dir.mkdir(parents=True, exist_ok=True)
    
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
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'test_thresholds': {
                'timeline_accuracy': 0.5,
                'mapping_success_rate': 0.95,
                'sync_tolerance': 0.3
            },
            'test_environment': {
                'log_level': 'INFO',
                'temp_dir': 'tests/temp'
            }
        }
    
    def test_basic_timeline_sync(self, video_path: str, subtitle_path: str) -> TimelineTestResult:
        """
        测试基础时间轴同步
        
        Args:
            video_path: 视频文件路径
            subtitle_path: 字幕文件路径
            
        Returns:
            TimelineTestResult: 测试结果
        """
        start_time = time.time()
        test_name = "basic_timeline_sync"
        
        try:
            # 验证文件存在性和完整性
            if not self.file_checker.check_file_integrity(video_path):
                raise FileNotFoundError(f"视频文件不存在或损坏: {video_path}")
            
            if not self.file_checker.check_file_integrity(subtitle_path):
                raise FileNotFoundError(f"字幕文件不存在或损坏: {subtitle_path}")
            
            # 解析字幕文件
            subtitles = self.srt_parser.parse(subtitle_path)
            if not subtitles:
                raise ValueError(f"字幕文件解析失败或为空: {subtitle_path}")
            
            # 检测语言
            subtitle_text = " ".join([sub.get('text', '') for sub in subtitles])
            language = self.language_detector.detect_language(subtitle_text)
            
            # 执行时间轴对齐
            alignment_result = self.alignment_engineer.align_subtitles_to_video(
                video_path=video_path,
                subtitles=subtitles,
                precision=AlignmentPrecision.HIGH
            )
            
            # 计算精度指标
            errors = []
            successful_mappings = 0
            failed_mappings = 0
            detailed_errors = []
            
            threshold = self.config['test_thresholds']['timeline_accuracy']
            
            for i, (original_sub, aligned_sub) in enumerate(zip(subtitles, alignment_result.aligned_subtitles)):
                original_start = self._parse_timestamp(original_sub.get('start_time', ''))
                aligned_start = self._parse_timestamp(aligned_sub.get('start_time', ''))
                
                if original_start is not None and aligned_start is not None:
                    error = abs(original_start - aligned_start)
                    errors.append(error)
                    
                    if error <= threshold:
                        successful_mappings += 1
                    else:
                        failed_mappings += 1
                        detailed_errors.append({
                            'subtitle_index': i,
                            'original_time': original_sub.get('start_time', ''),
                            'aligned_time': aligned_sub.get('start_time', ''),
                            'error_seconds': error,
                            'text': original_sub.get('text', '')[:50] + '...'
                        })
                else:
                    failed_mappings += 1
                    detailed_errors.append({
                        'subtitle_index': i,
                        'error_type': 'timestamp_parse_error',
                        'original_time': original_sub.get('start_time', ''),
                        'aligned_time': aligned_sub.get('start_time', ''),
                        'text': original_sub.get('text', '')[:50] + '...'
                    })
            
            # 计算统计指标
            if errors:
                average_error = np.mean(errors)
                max_error = np.max(errors)
                min_error = np.min(errors)
                errors_within_threshold = sum(1 for e in errors if e <= threshold)
            else:
                average_error = max_error = min_error = 0.0
                errors_within_threshold = 0
            
            total_subtitles = len(subtitles)
            success_rate = successful_mappings / total_subtitles if total_subtitles > 0 else 0.0
            processing_time = time.time() - start_time
            
            # 获取内存使用情况
            memory_usage = self._get_memory_usage()
            
            result = TimelineTestResult(
                test_name=test_name,
                video_file=video_path,
                subtitle_file=subtitle_path,
                language=language,
                total_subtitles=total_subtitles,
                successful_mappings=successful_mappings,
                failed_mappings=failed_mappings,
                average_error=average_error,
                max_error=max_error,
                min_error=min_error,
                errors_within_threshold=errors_within_threshold,
                threshold=threshold,
                success_rate=success_rate,
                processing_time=processing_time,
                memory_usage=memory_usage,
                detailed_errors=detailed_errors
            )
            
            self.test_results.append(result)
            self.logger.info(f"时间轴同步测试完成: {test_name}, 成功率: {success_rate:.2%}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"时间轴同步测试失败: {test_name}, 错误: {str(e)}")
            # 返回失败结果
            return TimelineTestResult(
                test_name=test_name,
                video_file=video_path,
                subtitle_file=subtitle_path,
                language="unknown",
                total_subtitles=0,
                successful_mappings=0,
                failed_mappings=1,
                average_error=float('inf'),
                max_error=float('inf'),
                min_error=float('inf'),
                errors_within_threshold=0,
                threshold=threshold,
                success_rate=0.0,
                processing_time=time.time() - start_time,
                memory_usage=self._get_memory_usage(),
                detailed_errors=[{'error': str(e)}]
            )
    
    def test_multilingual_support(self, test_cases: List[Tuple[str, str]]) -> List[TimelineTestResult]:
        """
        测试多语言支持
        
        Args:
            test_cases: 测试用例列表，每个元素为(video_path, subtitle_path)元组
            
        Returns:
            List[TimelineTestResult]: 测试结果列表
        """
        results = []
        
        for video_path, subtitle_path in test_cases:
            self.logger.info(f"开始多语言测试: {subtitle_path}")
            result = self.test_basic_timeline_sync(video_path, subtitle_path)
            result.test_name = "multilingual_support"
            results.append(result)
        
        return results
    
    def test_boundary_conditions(self) -> List[TimelineTestResult]:
        """测试边界条件"""
        results = []
        
        # 测试用例：空字幕文件
        empty_subtitle_result = self._test_empty_subtitle_file()
        if empty_subtitle_result:
            results.append(empty_subtitle_result)
        
        # 测试用例：损坏的时间戳格式
        invalid_timestamp_result = self._test_invalid_timestamp_format()
        if invalid_timestamp_result:
            results.append(invalid_timestamp_result)
        
        # 测试用例：极长字幕
        long_subtitle_result = self._test_extremely_long_subtitle()
        if long_subtitle_result:
            results.append(long_subtitle_result)
        
        return results
    
    def _test_empty_subtitle_file(self) -> Optional[TimelineTestResult]:
        """测试空字幕文件"""
        try:
            # 创建空字幕文件
            empty_srt_path = self.temp_dir / "empty_test.srt"
            with open(empty_srt_path, 'w', encoding='utf-8') as f:
                f.write("")
            
            # 创建测试视频文件路径（假设存在）
            test_video_path = "test_data/videos/test_video.mp4"
            
            result = self.test_basic_timeline_sync(str(test_video_path), str(empty_srt_path))
            result.test_name = "empty_subtitle_file"
            
            return result
            
        except Exception as e:
            self.logger.error(f"空字幕文件测试失败: {str(e)}")
            return None
    
    def _test_invalid_timestamp_format(self) -> Optional[TimelineTestResult]:
        """测试无效时间戳格式"""
        try:
            # 创建包含无效时间戳的字幕文件
            invalid_srt_path = self.temp_dir / "invalid_timestamp_test.srt"
            invalid_content = """1
invalid_timestamp --> 00:00:05,000
测试字幕内容

2
00:00:05,000 --> invalid_end_time
另一个测试字幕
"""
            with open(invalid_srt_path, 'w', encoding='utf-8') as f:
                f.write(invalid_content)
            
            test_video_path = "test_data/videos/test_video.mp4"
            
            result = self.test_basic_timeline_sync(str(test_video_path), str(invalid_srt_path))
            result.test_name = "invalid_timestamp_format"
            
            return result
            
        except Exception as e:
            self.logger.error(f"无效时间戳格式测试失败: {str(e)}")
            return None
    
    def _test_extremely_long_subtitle(self) -> Optional[TimelineTestResult]:
        """测试极长字幕"""
        try:
            # 创建包含极长字幕的文件
            long_srt_path = self.temp_dir / "long_subtitle_test.srt"
            long_text = "这是一个非常长的字幕内容，" * 100  # 创建很长的字幕文本
            
            long_content = f"""1
00:00:00,000 --> 00:00:10,000
{long_text}

2
00:00:10,000 --> 00:00:20,000
{long_text}
"""
            with open(long_srt_path, 'w', encoding='utf-8') as f:
                f.write(long_content)
            
            test_video_path = "test_data/videos/test_video.mp4"
            
            result = self.test_basic_timeline_sync(str(test_video_path), str(long_srt_path))
            result.test_name = "extremely_long_subtitle"
            
            return result
            
        except Exception as e:
            self.logger.error(f"极长字幕测试失败: {str(e)}")
            return None
    
    def _parse_timestamp(self, timestamp_str: str) -> Optional[float]:
        """
        解析时间戳字符串为秒数
        
        Args:
            timestamp_str: 时间戳字符串，格式如 "00:01:23,456"
            
        Returns:
            float: 秒数，解析失败返回None
        """
        try:
            if not timestamp_str or '-->' in timestamp_str:
                return None
            
            # 移除可能的空格
            timestamp_str = timestamp_str.strip()
            
            # 解析格式：HH:MM:SS,mmm
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
            
        except (ValueError, IndexError) as e:
            self.logger.debug(f"时间戳解析失败: {timestamp_str}, 错误: {str(e)}")
            return None
    
    def _get_memory_usage(self) -> float:
        """获取当前内存使用量（MB）"""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            return memory_info.rss / 1024 / 1024  # 转换为MB
        except ImportError:
            return 0.0
    
    def generate_test_report(self, output_path: str = None) -> Dict[str, Any]:
        """
        生成测试报告
        
        Args:
            output_path: 输出文件路径
            
        Returns:
            Dict[str, Any]: 测试报告数据
        """
        if not self.test_results:
            self.logger.warning("没有测试结果可生成报告")
            return {}
        
        # 计算总体统计
        total_tests = len(self.test_results)
        successful_tests = sum(1 for r in self.test_results if r.success_rate >= 0.95)
        total_subtitles = sum(r.total_subtitles for r in self.test_results)
        total_successful_mappings = sum(r.successful_mappings for r in self.test_results)
        
        average_errors = [r.average_error for r in self.test_results if r.average_error != float('inf')]
        overall_average_error = np.mean(average_errors) if average_errors else float('inf')
        
        max_errors = [r.max_error for r in self.test_results if r.max_error != float('inf')]
        overall_max_error = np.max(max_errors) if max_errors else float('inf')
        
        total_processing_time = sum(r.processing_time for r in self.test_results)
        average_memory_usage = np.mean([r.memory_usage for r in self.test_results])
        
        # 按语言分组统计
        language_stats = {}
        for result in self.test_results:
            lang = result.language
            if lang not in language_stats:
                language_stats[lang] = {
                    'test_count': 0,
                    'success_rate': [],
                    'average_errors': []
                }
            language_stats[lang]['test_count'] += 1
            language_stats[lang]['success_rate'].append(result.success_rate)
            if result.average_error != float('inf'):
                language_stats[lang]['average_errors'].append(result.average_error)
        
        # 计算语言统计
        for lang_data in language_stats.values():
            lang_data['avg_success_rate'] = np.mean(lang_data['success_rate'])
            lang_data['avg_error'] = np.mean(lang_data['average_errors']) if lang_data['average_errors'] else float('inf')
        
        report = {
            'test_summary': {
                'total_tests': total_tests,
                'successful_tests': successful_tests,
                'test_success_rate': successful_tests / total_tests if total_tests > 0 else 0.0,
                'total_subtitles_processed': total_subtitles,
                'total_successful_mappings': total_successful_mappings,
                'overall_mapping_success_rate': total_successful_mappings / total_subtitles if total_subtitles > 0 else 0.0,
                'overall_average_error': overall_average_error,
                'overall_max_error': overall_max_error,
                'total_processing_time': total_processing_time,
                'average_memory_usage': average_memory_usage
            },
            'language_statistics': language_stats,
            'detailed_results': [
                {
                    'test_name': r.test_name,
                    'video_file': r.video_file,
                    'subtitle_file': r.subtitle_file,
                    'language': r.language,
                    'success_rate': r.success_rate,
                    'average_error': r.average_error,
                    'max_error': r.max_error,
                    'processing_time': r.processing_time,
                    'memory_usage': r.memory_usage,
                    'failed_mappings': r.failed_mappings
                }
                for r in self.test_results
            ],
            'threshold_compliance': {
                'timeline_accuracy_threshold': self.config['test_thresholds']['timeline_accuracy'],
                'tests_meeting_threshold': sum(1 for r in self.test_results if r.average_error <= self.config['test_thresholds']['timeline_accuracy']),
                'compliance_rate': sum(1 for r in self.test_results if r.average_error <= self.config['test_thresholds']['timeline_accuracy']) / total_tests if total_tests > 0 else 0.0
            },
            'recommendations': self._generate_recommendations()
        }
        
        # 保存报告
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            self.logger.info(f"测试报告已保存到: {output_path}")
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        if not self.test_results:
            return ["无测试结果，无法生成建议"]
        
        # 分析成功率
        low_success_tests = [r for r in self.test_results if r.success_rate < 0.9]
        if low_success_tests:
            recommendations.append(f"有{len(low_success_tests)}个测试的成功率低于90%，建议优化时间轴对齐算法")
        
        # 分析误差
        high_error_tests = [r for r in self.test_results if r.average_error > 0.3]
        if high_error_tests:
            recommendations.append(f"有{len(high_error_tests)}个测试的平均误差超过0.3秒，建议提高对齐精度")
        
        # 分析内存使用
        high_memory_tests = [r for r in self.test_results if r.memory_usage > 1000]  # 1GB
        if high_memory_tests:
            recommendations.append(f"有{len(high_memory_tests)}个测试的内存使用超过1GB，建议优化内存管理")
        
        # 分析处理时间
        slow_tests = [r for r in self.test_results if r.processing_time > 60]  # 1分钟
        if slow_tests:
            recommendations.append(f"有{len(slow_tests)}个测试的处理时间超过1分钟，建议优化处理速度")
        
        if not recommendations:
            recommendations.append("所有测试均达到预期标准，系统运行良好")
        
        return recommendations


class TestTimelineAccuracy(unittest.TestCase):
    """时间轴精度测试用例类"""
    
    @classmethod
    def setUpClass(cls):
        """设置测试类"""
        cls.tester = TimelineAccuracyTester()
        cls.test_data_generator = TestDataGenerator()
    
    def test_chinese_subtitle_sync(self):
        """测试中文字幕同步"""
        # 生成测试数据
        video_path, subtitle_path = self.test_data_generator.generate_chinese_test_case()
        
        result = self.tester.test_basic_timeline_sync(video_path, subtitle_path)
        
        # 断言
        self.assertGreaterEqual(result.success_rate, 0.95, "中文字幕同步成功率应≥95%")
        self.assertLessEqual(result.average_error, 0.5, "中文字幕平均误差应≤0.5秒")
    
    def test_english_subtitle_sync(self):
        """测试英文字幕同步"""
        video_path, subtitle_path = self.test_data_generator.generate_english_test_case()
        
        result = self.tester.test_basic_timeline_sync(video_path, subtitle_path)
        
        self.assertGreaterEqual(result.success_rate, 0.95, "英文字幕同步成功率应≥95%")
        self.assertLessEqual(result.average_error, 0.5, "英文字幕平均误差应≤0.5秒")
    
    def test_mixed_language_sync(self):
        """测试混合语言字幕同步"""
        video_path, subtitle_path = self.test_data_generator.generate_mixed_language_test_case()
        
        result = self.tester.test_basic_timeline_sync(video_path, subtitle_path)
        
        self.assertGreaterEqual(result.success_rate, 0.90, "混合语言字幕同步成功率应≥90%")
        self.assertLessEqual(result.average_error, 0.5, "混合语言字幕平均误差应≤0.5秒")
    
    def test_boundary_conditions(self):
        """测试边界条件"""
        results = self.tester.test_boundary_conditions()
        
        # 验证边界条件测试能够正常处理异常情况
        self.assertIsInstance(results, list, "边界条件测试应返回结果列表")
        
        for result in results:
            self.assertIsInstance(result, TimelineTestResult, "每个结果应为TimelineTestResult类型")


if __name__ == "__main__":
    # 运行测试
    unittest.main(verbosity=2)
