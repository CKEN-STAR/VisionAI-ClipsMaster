#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 多语言支持测试模块

此模块验证系统对中英文字幕的解析和处理能力，包括：
1. 中文字幕解析准确性
2. 英文字幕解析准确性
3. 混合语言字幕处理
4. 字符编码兼容性
5. 语言检测准确性
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
from src.core.srt_parser import SRTParser
from src.core.language_detector import LanguageDetector
from src.utils.file_checker import FileChecker
from src.utils.log_handler import LogHandler

logger = logging.getLogger(__name__)


@dataclass
class MultilingualTestResult:
    """多语言测试结果数据类"""
    test_name: str
    subtitle_file: str
    detected_language: str
    expected_language: str
    language_detection_correct: bool
    parsing_success: bool
    total_subtitles: int
    parsed_subtitles: int
    parsing_accuracy: float
    encoding_issues: int
    character_corruption: int
    timestamp_errors: int
    processing_time: float
    detailed_errors: List[Dict[str, Any]]


class MultilingualSupportTester:
    """多语言支持测试器"""
    
    def __init__(self, config_path: str = None):
        """初始化多语言测试器"""
        self.config = self._load_config(config_path)
        self.srt_parser = SRTParser()
        self.language_detector = LanguageDetector()
        self.file_checker = FileChecker()
        
        # 设置日志
        self.logger = LogHandler.get_logger(
            name=__name__,
            level=self.config.get('test_environment', {}).get('log_level', 'INFO')
        )
        
        # 创建临时目录
        self.temp_dir = Path(self.config.get('test_environment', {}).get('temp_dir', 'tests/temp'))
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # 测试结果存储
        self.test_results = []
    
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
            return {'test_environment': {'log_level': 'INFO', 'temp_dir': 'tests/temp'}}
    
    def test_chinese_subtitle_parsing(self, subtitle_path: str) -> MultilingualTestResult:
        """
        测试中文字幕解析
        
        Args:
            subtitle_path: 中文字幕文件路径
            
        Returns:
            MultilingualTestResult: 测试结果
        """
        return self._test_language_parsing(subtitle_path, "zh", "chinese_subtitle_parsing")
    
    def test_english_subtitle_parsing(self, subtitle_path: str) -> MultilingualTestResult:
        """
        测试英文字幕解析
        
        Args:
            subtitle_path: 英文字幕文件路径
            
        Returns:
            MultilingualTestResult: 测试结果
        """
        return self._test_language_parsing(subtitle_path, "en", "english_subtitle_parsing")
    
    def test_mixed_language_parsing(self, subtitle_path: str) -> MultilingualTestResult:
        """
        测试混合语言字幕解析
        
        Args:
            subtitle_path: 混合语言字幕文件路径
            
        Returns:
            MultilingualTestResult: 测试结果
        """
        return self._test_language_parsing(subtitle_path, "mixed", "mixed_language_parsing")
    
    def _test_language_parsing(self, subtitle_path: str, expected_language: str, test_name: str) -> MultilingualTestResult:
        """
        通用语言解析测试方法
        
        Args:
            subtitle_path: 字幕文件路径
            expected_language: 期望的语言类型
            test_name: 测试名称
            
        Returns:
            MultilingualTestResult: 测试结果
        """
        start_time = time.time()
        
        try:
            # 检查文件存在性
            if not os.path.exists(subtitle_path):
                raise FileNotFoundError(f"字幕文件不存在: {subtitle_path}")
            
            # 读取文件内容进行语言检测
            with open(subtitle_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 语言检测
            detected_language = self.language_detector.detect_language(content)
            language_detection_correct = self._is_language_detection_correct(detected_language, expected_language)
            
            # 解析字幕
            parsing_success = True
            parsed_subtitles = []
            detailed_errors = []
            encoding_issues = 0
            character_corruption = 0
            timestamp_errors = 0
            
            try:
                parsed_subtitles = self.srt_parser.parse(subtitle_path)
                if not parsed_subtitles:
                    parsing_success = False
                    detailed_errors.append({
                        'error_type': 'empty_result',
                        'message': '字幕解析结果为空'
                    })
            except UnicodeDecodeError as e:
                parsing_success = False
                encoding_issues += 1
                detailed_errors.append({
                    'error_type': 'encoding_error',
                    'message': f'编码错误: {str(e)}'
                })
            except Exception as e:
                parsing_success = False
                detailed_errors.append({
                    'error_type': 'parsing_error',
                    'message': f'解析错误: {str(e)}'
                })
            
            # 分析解析结果
            total_subtitles = len(parsed_subtitles) if parsed_subtitles else 0
            
            if parsed_subtitles:
                # 检查字符损坏
                character_corruption = self._count_character_corruption(parsed_subtitles, expected_language)
                
                # 检查时间戳错误
                timestamp_errors = self._count_timestamp_errors(parsed_subtitles)
            
            parsing_accuracy = (total_subtitles - character_corruption - timestamp_errors) / total_subtitles if total_subtitles > 0 else 0.0
            
            result = MultilingualTestResult(
                test_name=test_name,
                subtitle_file=subtitle_path,
                detected_language=detected_language,
                expected_language=expected_language,
                language_detection_correct=language_detection_correct,
                parsing_success=parsing_success,
                total_subtitles=total_subtitles,
                parsed_subtitles=total_subtitles,
                parsing_accuracy=parsing_accuracy,
                encoding_issues=encoding_issues,
                character_corruption=character_corruption,
                timestamp_errors=timestamp_errors,
                processing_time=time.time() - start_time,
                detailed_errors=detailed_errors
            )
            
            self.test_results.append(result)
            self.logger.info(f"多语言测试完成: {test_name}, 解析准确率: {parsing_accuracy:.2%}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"多语言测试失败: {test_name}, 错误: {str(e)}")
            return MultilingualTestResult(
                test_name=test_name,
                subtitle_file=subtitle_path,
                detected_language="unknown",
                expected_language=expected_language,
                language_detection_correct=False,
                parsing_success=False,
                total_subtitles=0,
                parsed_subtitles=0,
                parsing_accuracy=0.0,
                encoding_issues=1,
                character_corruption=0,
                timestamp_errors=0,
                processing_time=time.time() - start_time,
                detailed_errors=[{'error': str(e)}]
            )
    
    def test_encoding_compatibility(self) -> List[MultilingualTestResult]:
        """测试字符编码兼容性"""
        results = []
        
        # 测试不同编码的字幕文件
        encodings = ['utf-8', 'gbk', 'utf-16']
        test_content = {
            'zh': "1\n00:00:00,000 --> 00:00:05,000\n你好，世界！\n\n2\n00:00:05,000 --> 00:00:10,000\n这是中文字幕测试。\n",
            'en': "1\n00:00:00,000 --> 00:00:05,000\nHello, World!\n\n2\n00:00:05,000 --> 00:00:10,000\nThis is English subtitle test.\n"
        }
        
        for lang, content in test_content.items():
            for encoding in encodings:
                try:
                    # 创建不同编码的测试文件
                    test_file = self.temp_dir / f"encoding_test_{lang}_{encoding}.srt"
                    
                    with open(test_file, 'w', encoding=encoding) as f:
                        f.write(content)
                    
                    # 测试解析
                    result = self._test_language_parsing(str(test_file), lang, f"encoding_compatibility_{lang}_{encoding}")
                    results.append(result)
                    
                except Exception as e:
                    self.logger.error(f"编码兼容性测试失败: {lang}_{encoding}, 错误: {str(e)}")
        
        return results
    
    def test_special_characters(self) -> List[MultilingualTestResult]:
        """测试特殊字符处理"""
        results = []
        
        # 特殊字符测试用例
        special_cases = {
            'chinese_punctuation': {
                'content': "1\n00:00:00,000 --> 00:00:05,000\n你好，世界！？：；""''（）【】\n",
                'language': 'zh'
            },
            'english_symbols': {
                'content': "1\n00:00:00,000 --> 00:00:05,000\nHello @#$%^&*()_+-={}[]|\\:;\"'<>?,./\n",
                'language': 'en'
            },
            'emoji_test': {
                'content': "1\n00:00:00,000 --> 00:00:05,000\n😀😃😄😁😆😅😂🤣😊😇\n",
                'language': 'mixed'
            },
            'unicode_test': {
                'content': "1\n00:00:00,000 --> 00:00:05,000\n测试Unicode: αβγδε ñáéíóú\n",
                'language': 'mixed'
            }
        }
        
        for case_name, case_data in special_cases.items():
            try:
                test_file = self.temp_dir / f"special_chars_{case_name}.srt"
                
                with open(test_file, 'w', encoding='utf-8') as f:
                    f.write(case_data['content'])
                
                result = self._test_language_parsing(str(test_file), case_data['language'], f"special_characters_{case_name}")
                results.append(result)
                
            except Exception as e:
                self.logger.error(f"特殊字符测试失败: {case_name}, 错误: {str(e)}")
        
        return results
    
    def _is_language_detection_correct(self, detected: str, expected: str) -> bool:
        """判断语言检测是否正确"""
        if expected == "mixed":
            # 混合语言情况下，检测到中文或英文都算正确
            return detected in ["zh", "en", "mixed"]
        else:
            return detected == expected
    
    def _count_character_corruption(self, subtitles: List[Dict], expected_language: str) -> int:
        """统计字符损坏数量"""
        corruption_count = 0
        
        for subtitle in subtitles:
            text = subtitle.get('text', '')
            
            # 检查是否包含乱码字符
            if '�' in text:  # Unicode替换字符
                corruption_count += 1
                continue
            
            # 根据期望语言检查字符合理性
            if expected_language == "zh":
                # 中文字幕应该主要包含中文字符
                chinese_chars = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
                if len(text) > 0 and chinese_chars / len(text) < 0.3:  # 中文字符比例过低
                    corruption_count += 1
            elif expected_language == "en":
                # 英文字幕应该主要包含ASCII字符
                ascii_chars = sum(1 for char in text if ord(char) < 128)
                if len(text) > 0 and ascii_chars / len(text) < 0.8:  # ASCII字符比例过低
                    corruption_count += 1
        
        return corruption_count
    
    def _count_timestamp_errors(self, subtitles: List[Dict]) -> int:
        """统计时间戳错误数量"""
        error_count = 0
        
        for subtitle in subtitles:
            start_time = subtitle.get('start_time', '')
            end_time = subtitle.get('end_time', '')
            
            # 检查时间戳格式
            if not self._is_valid_timestamp(start_time) or not self._is_valid_timestamp(end_time):
                error_count += 1
                continue
            
            # 检查时间逻辑
            start_seconds = self._parse_timestamp(start_time)
            end_seconds = self._parse_timestamp(end_time)
            
            if start_seconds is not None and end_seconds is not None:
                if start_seconds >= end_seconds:  # 开始时间不应该晚于结束时间
                    error_count += 1
        
        return error_count
    
    def _is_valid_timestamp(self, timestamp: str) -> bool:
        """检查时间戳格式是否有效"""
        try:
            if not timestamp:
                return False
            
            # 标准SRT时间戳格式：HH:MM:SS,mmm
            if ',' not in timestamp:
                return False
            
            time_part, ms_part = timestamp.split(',')
            
            if len(ms_part) != 3:  # 毫秒部分应该是3位
                return False
            
            time_components = time_part.split(':')
            if len(time_components) != 3:
                return False
            
            # 检查各部分是否为数字
            hours, minutes, seconds = time_components
            int(hours)
            int(minutes)
            int(seconds)
            int(ms_part)
            
            # 检查范围
            if int(minutes) >= 60 or int(seconds) >= 60:
                return False
            
            return True
            
        except (ValueError, IndexError):
            return False
    
    def _parse_timestamp(self, timestamp_str: str) -> Optional[float]:
        """解析时间戳字符串为秒数"""
        try:
            if not self._is_valid_timestamp(timestamp_str):
                return None
            
            time_part, ms_part = timestamp_str.split(',')
            milliseconds = int(ms_part)
            
            time_components = time_part.split(':')
            hours = int(time_components[0])
            minutes = int(time_components[1])
            seconds = int(time_components[2])
            
            total_seconds = hours * 3600 + minutes * 60 + seconds + milliseconds / 1000.0
            return total_seconds
            
        except (ValueError, IndexError):
            return None
    
    def generate_multilingual_test_report(self, output_path: str = None) -> Dict[str, Any]:
        """生成多语言测试报告"""
        if not self.test_results:
            self.logger.warning("没有测试结果可生成报告")
            return {}
        
        # 按语言分组统计
        language_stats = {}
        for result in self.test_results:
            lang = result.expected_language
            if lang not in language_stats:
                language_stats[lang] = {
                    'test_count': 0,
                    'parsing_success_count': 0,
                    'language_detection_correct_count': 0,
                    'total_subtitles': 0,
                    'total_errors': 0,
                    'parsing_accuracies': []
                }
            
            stats = language_stats[lang]
            stats['test_count'] += 1
            if result.parsing_success:
                stats['parsing_success_count'] += 1
            if result.language_detection_correct:
                stats['language_detection_correct_count'] += 1
            stats['total_subtitles'] += result.total_subtitles
            stats['total_errors'] += (result.encoding_issues + result.character_corruption + result.timestamp_errors)
            stats['parsing_accuracies'].append(result.parsing_accuracy)
        
        # 计算统计指标
        for lang_data in language_stats.values():
            lang_data['parsing_success_rate'] = lang_data['parsing_success_count'] / lang_data['test_count'] if lang_data['test_count'] > 0 else 0.0
            lang_data['language_detection_accuracy'] = lang_data['language_detection_correct_count'] / lang_data['test_count'] if lang_data['test_count'] > 0 else 0.0
            lang_data['average_parsing_accuracy'] = sum(lang_data['parsing_accuracies']) / len(lang_data['parsing_accuracies']) if lang_data['parsing_accuracies'] else 0.0
            lang_data['error_rate'] = lang_data['total_errors'] / lang_data['total_subtitles'] if lang_data['total_subtitles'] > 0 else 0.0
        
        # 总体统计
        total_tests = len(self.test_results)
        successful_parsing = sum(1 for r in self.test_results if r.parsing_success)
        correct_language_detection = sum(1 for r in self.test_results if r.language_detection_correct)
        
        report = {
            'test_summary': {
                'total_tests': total_tests,
                'successful_parsing': successful_parsing,
                'parsing_success_rate': successful_parsing / total_tests if total_tests > 0 else 0.0,
                'correct_language_detection': correct_language_detection,
                'language_detection_accuracy': correct_language_detection / total_tests if total_tests > 0 else 0.0
            },
            'language_statistics': language_stats,
            'detailed_results': [
                {
                    'test_name': r.test_name,
                    'subtitle_file': r.subtitle_file,
                    'detected_language': r.detected_language,
                    'expected_language': r.expected_language,
                    'language_detection_correct': r.language_detection_correct,
                    'parsing_success': r.parsing_success,
                    'parsing_accuracy': r.parsing_accuracy,
                    'encoding_issues': r.encoding_issues,
                    'character_corruption': r.character_corruption,
                    'timestamp_errors': r.timestamp_errors,
                    'processing_time': r.processing_time
                }
                for r in self.test_results
            ]
        }
        
        # 保存报告
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            self.logger.info(f"多语言测试报告已保存到: {output_path}")
        
        return report


class TestMultilingualSupport(unittest.TestCase):
    """多语言支持测试用例类"""
    
    @classmethod
    def setUpClass(cls):
        """设置测试类"""
        cls.tester = MultilingualSupportTester()
    
    def test_chinese_parsing_accuracy(self):
        """测试中文解析准确性"""
        # 创建中文测试字幕
        chinese_content = """1
00:00:00,000 --> 00:00:05,000
你好，世界！

2
00:00:05,000 --> 00:00:10,000
这是一个中文字幕测试。

3
00:00:10,000 --> 00:00:15,000
包含标点符号：，。？！；：""''（）
"""
        test_file = self.tester.temp_dir / "test_chinese.srt"
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(chinese_content)
        
        result = self.tester.test_chinese_subtitle_parsing(str(test_file))
        
        self.assertTrue(result.parsing_success, "中文字幕解析应该成功")
        self.assertGreaterEqual(result.parsing_accuracy, 0.98, "中文字幕解析准确率应≥98%")
        self.assertTrue(result.language_detection_correct, "中文语言检测应该正确")
    
    def test_english_parsing_accuracy(self):
        """测试英文解析准确性"""
        english_content = """1
00:00:00,000 --> 00:00:05,000
Hello, World!

2
00:00:05,000 --> 00:00:10,000
This is an English subtitle test.

3
00:00:10,000 --> 00:00:15,000
Including punctuation: .,?!;:"'()[]{}
"""
        test_file = self.tester.temp_dir / "test_english.srt"
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(english_content)
        
        result = self.tester.test_english_subtitle_parsing(str(test_file))
        
        self.assertTrue(result.parsing_success, "英文字幕解析应该成功")
        self.assertGreaterEqual(result.parsing_accuracy, 0.98, "英文字幕解析准确率应≥98%")
        self.assertTrue(result.language_detection_correct, "英文语言检测应该正确")
    
    def test_mixed_language_parsing(self):
        """测试混合语言解析"""
        mixed_content = """1
00:00:00,000 --> 00:00:05,000
Hello 你好 World 世界!

2
00:00:05,000 --> 00:00:10,000
This is 这是 a mixed language test 混合语言测试.
"""
        test_file = self.tester.temp_dir / "test_mixed.srt"
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(mixed_content)
        
        result = self.tester.test_mixed_language_parsing(str(test_file))
        
        self.assertTrue(result.parsing_success, "混合语言字幕解析应该成功")
        self.assertGreaterEqual(result.parsing_accuracy, 0.94, "混合语言字幕解析准确率应≥94%")
    
    def test_encoding_compatibility(self):
        """测试编码兼容性"""
        results = self.tester.test_encoding_compatibility()
        
        # 至少UTF-8编码应该完全支持
        utf8_results = [r for r in results if 'utf-8' in r.test_name]
        for result in utf8_results:
            self.assertTrue(result.parsing_success, f"UTF-8编码解析应该成功: {result.test_name}")
    
    def test_special_characters(self):
        """测试特殊字符处理"""
        results = self.tester.test_special_characters()
        
        for result in results:
            self.assertTrue(result.parsing_success, f"特殊字符解析应该成功: {result.test_name}")
            self.assertEqual(result.encoding_issues, 0, f"不应该有编码问题: {result.test_name}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
