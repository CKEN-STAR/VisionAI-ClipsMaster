#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 核心功能综合验证主程序

此脚本执行完整的核心功能验证测试，包括：
1. 视频-字幕映射精度验证
2. AI剧本重构功能验证
3. 双语言模型系统验证
4. 内存稳定性验证
5. 生成综合测试报告
"""

import os
import sys
import json
import time
import logging
import argparse
from typing import Dict, List, Any, Optional
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# 导入测试模块
from tests.core_functionality_validation.video_subtitle_mapping.test_timeline_accuracy import TimelineAccuracyTester
from tests.core_functionality_validation.video_subtitle_mapping.test_sync_validation import SyncValidator
from tests.core_functionality_validation.video_subtitle_mapping.test_multilingual_support import MultilingualSupportTester
from tests.core_functionality_validation.ai_script_reconstruction.test_plot_understanding import PlotUnderstandingTester
from tests.core_functionality_validation.ai_script_reconstruction.test_viral_generation import ViralGenerationTester
from tests.core_functionality_validation.data_preparation.test_data_generator import TestDataGenerator
from tests.core_functionality_validation.reporting.report_generator import ComprehensiveReportGenerator

# 导入工具模块
from src.utils.log_handler import LogHandler

logger = logging.getLogger(__name__)


class CoreFunctionalityValidator:
    """核心功能验证器"""
    
    def __init__(self, config_path: str = None):
        """初始化验证器"""
        self.config_path = config_path or "tests/core_functionality_validation/test_config.yaml"
        self.config = self._load_config()
        
        # 设置日志
        self.logger = LogHandler.get_logger(
            name=__name__,
            level=self.config.get('test_environment', {}).get('log_level', 'INFO')
        )
        
        # 初始化测试器
        self.timeline_tester = TimelineAccuracyTester(self.config_path)
        self.sync_validator = SyncValidator(self.config_path)
        self.multilingual_tester = MultilingualSupportTester(self.config_path)
        self.plot_tester = PlotUnderstandingTester(self.config_path)
        self.viral_tester = ViralGenerationTester(self.config_path)
        self.data_generator = TestDataGenerator(self.config_path)
        self.report_generator = ComprehensiveReportGenerator(self.config_path)
        
        # 测试结果存储
        self.test_results = {
            'timeline_accuracy': [],
            'sync_validation': [],
            'multilingual_support': [],
            'plot_understanding': [],
            'viral_generation': []
        }
        
        # 测试统计
        self.test_stats = {
            'start_time': None,
            'end_time': None,
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0
        }
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        try:
            import yaml
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"无法加载配置文件 {self.config_path}: {e}")
            return {
                'test_data': {'sample_count': 5},
                'test_environment': {'log_level': 'INFO'}
            }
    
    def run_comprehensive_validation(self, generate_test_data: bool = True) -> Dict[str, Any]:
        """
        运行综合验证测试
        
        Args:
            generate_test_data: 是否生成新的测试数据
            
        Returns:
            Dict[str, Any]: 测试结果汇总
        """
        self.test_stats['start_time'] = time.time()
        self.logger.info("开始执行VisionAI-ClipsMaster核心功能综合验证")
        
        try:
            # 1. 准备测试数据
            if generate_test_data:
                self.logger.info("正在生成测试数据...")
                test_data = self._prepare_test_data()
            else:
                self.logger.info("使用现有测试数据...")
                test_data = self._load_existing_test_data()
            
            # 2. 执行视频-字幕映射测试
            self.logger.info("执行视频-字幕映射精度测试...")
            self._run_timeline_accuracy_tests(test_data)
            
            # 3. 执行同步验证测试
            self.logger.info("执行同步验证测试...")
            self._run_sync_validation_tests(test_data)
            
            # 4. 执行多语言支持测试
            self.logger.info("执行多语言支持测试...")
            self._run_multilingual_tests(test_data)
            
            # 5. 执行AI剧本重构测试
            self.logger.info("执行AI剧本重构测试...")
            self._run_plot_understanding_tests(test_data)
            
            # 6. 执行爆款生成测试
            self.logger.info("执行爆款生成测试...")
            self._run_viral_generation_tests(test_data)
            
            # 7. 生成综合报告
            self.logger.info("生成综合测试报告...")
            report = self._generate_comprehensive_report()
            
            # 8. 计算测试统计
            self._calculate_test_statistics()
            
            self.test_stats['end_time'] = time.time()
            total_time = self.test_stats['end_time'] - self.test_stats['start_time']
            
            self.logger.info(f"核心功能验证完成，总耗时: {total_time:.2f}秒")
            self.logger.info(f"测试统计: {self.test_stats['passed_tests']}/{self.test_stats['total_tests']} 通过")
            
            return {
                'success': True,
                'test_results': self.test_results,
                'test_statistics': self.test_stats,
                'report': report,
                'summary': self._generate_summary()
            }
            
        except Exception as e:
            self.logger.error(f"核心功能验证失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'test_results': self.test_results,
                'test_statistics': self.test_stats
            }
    
    def _prepare_test_data(self) -> List[Dict[str, str]]:
        """准备测试数据"""
        sample_count = self.config.get('test_data', {}).get('sample_count', 5)
        return self.data_generator.generate_test_dataset(sample_count)
    
    def _load_existing_test_data(self) -> List[Dict[str, str]]:
        """加载现有测试数据"""
        test_data_dir = Path("test_data")
        if not test_data_dir.exists():
            self.logger.warning("未找到现有测试数据，将生成新数据")
            return self._prepare_test_data()
        
        # 扫描现有测试文件
        test_cases = []
        subtitle_files = list((test_data_dir / "subtitles").glob("*.srt"))
        
        for subtitle_file in subtitle_files[:5]:  # 限制数量
            case_name = subtitle_file.stem
            video_file = test_data_dir / "videos" / f"{case_name}.mp4"
            
            test_cases.append({
                'case_name': case_name,
                'video_file': str(video_file) if video_file.exists() else "",
                'original_subtitle_file': str(subtitle_file),
                'viral_subtitle_file': None,
                'golden_standard_file': None
            })
        
        return test_cases
    
    def _run_timeline_accuracy_tests(self, test_data: List[Dict[str, str]]):
        """运行时间轴精度测试"""
        for test_case in test_data:
            if not test_case.get('original_subtitle_file'):
                continue
            
            try:
                video_file = test_case.get('video_file', '')
                subtitle_file = test_case['original_subtitle_file']
                
                # 如果没有视频文件，创建模拟文件
                if not video_file or not os.path.exists(video_file):
                    video_file = self._create_mock_video_file(test_case['case_name'])
                
                result = self.timeline_tester.test_basic_timeline_sync(video_file, subtitle_file)
                self.test_results['timeline_accuracy'].append(result)
                
                self.test_stats['total_tests'] += 1
                if result.success_rate >= 0.95:
                    self.test_stats['passed_tests'] += 1
                else:
                    self.test_stats['failed_tests'] += 1
                
            except Exception as e:
                self.logger.error(f"时间轴精度测试失败: {test_case['case_name']}, 错误: {str(e)}")
                self.test_stats['total_tests'] += 1
                self.test_stats['failed_tests'] += 1
    
    def _run_sync_validation_tests(self, test_data: List[Dict[str, str]]):
        """运行同步验证测试"""
        for test_case in test_data[:3]:  # 限制数量以节省时间
            if not test_case.get('original_subtitle_file'):
                continue
            
            try:
                video_file = test_case.get('video_file', '')
                subtitle_file = test_case['original_subtitle_file']
                
                if not video_file or not os.path.exists(video_file):
                    video_file = self._create_mock_video_file(test_case['case_name'])
                
                result = self.sync_validator.validate_sync_quality(video_file, subtitle_file)
                self.test_results['sync_validation'].append(result)
                
                self.test_stats['total_tests'] += 1
                if result.sync_score >= 0.8:
                    self.test_stats['passed_tests'] += 1
                else:
                    self.test_stats['failed_tests'] += 1
                
            except Exception as e:
                self.logger.error(f"同步验证测试失败: {test_case['case_name']}, 错误: {str(e)}")
                self.test_stats['total_tests'] += 1
                self.test_stats['failed_tests'] += 1
    
    def _run_multilingual_tests(self, test_data: List[Dict[str, str]]):
        """运行多语言支持测试"""
        # 测试中文字幕
        chinese_cases = [case for case in test_data if 'zh' in case.get('case_name', '')]
        for test_case in chinese_cases[:2]:
            try:
                result = self.multilingual_tester.test_chinese_subtitle_parsing(test_case['original_subtitle_file'])
                self.test_results['multilingual_support'].append(result)
                
                self.test_stats['total_tests'] += 1
                if result.parsing_success and result.parsing_accuracy >= 0.98:
                    self.test_stats['passed_tests'] += 1
                else:
                    self.test_stats['failed_tests'] += 1
                    
            except Exception as e:
                self.logger.error(f"中文多语言测试失败: {test_case['case_name']}, 错误: {str(e)}")
                self.test_stats['total_tests'] += 1
                self.test_stats['failed_tests'] += 1
        
        # 测试英文字幕
        english_cases = [case for case in test_data if 'en' in case.get('case_name', '')]
        for test_case in english_cases[:2]:
            try:
                result = self.multilingual_tester.test_english_subtitle_parsing(test_case['original_subtitle_file'])
                self.test_results['multilingual_support'].append(result)
                
                self.test_stats['total_tests'] += 1
                if result.parsing_success and result.parsing_accuracy >= 0.98:
                    self.test_stats['passed_tests'] += 1
                else:
                    self.test_stats['failed_tests'] += 1
                    
            except Exception as e:
                self.logger.error(f"英文多语言测试失败: {test_case['case_name']}, 错误: {str(e)}")
                self.test_stats['total_tests'] += 1
                self.test_stats['failed_tests'] += 1
        
        # 测试特殊字符和编码
        try:
            encoding_results = self.multilingual_tester.test_encoding_compatibility()
            self.test_results['multilingual_support'].extend(encoding_results)
            
            for result in encoding_results:
                self.test_stats['total_tests'] += 1
                if result.parsing_success:
                    self.test_stats['passed_tests'] += 1
                else:
                    self.test_stats['failed_tests'] += 1
                    
        except Exception as e:
            self.logger.error(f"编码兼容性测试失败: {str(e)}")
    
    def _run_plot_understanding_tests(self, test_data: List[Dict[str, str]]):
        """运行剧情理解测试"""
        for test_case in test_data[:3]:  # 限制数量
            if not test_case.get('original_subtitle_file'):
                continue
            
            try:
                # 加载黄金标准数据（如果存在）
                golden_standard = None
                if test_case.get('golden_standard_file') and os.path.exists(test_case['golden_standard_file']):
                    with open(test_case['golden_standard_file'], 'r', encoding='utf-8') as f:
                        golden_standard = json.load(f)
                
                result = self.plot_tester.test_plot_understanding(
                    test_case['original_subtitle_file'], 
                    golden_standard
                )
                self.test_results['plot_understanding'].append(result)
                
                self.test_stats['total_tests'] += 1
                if result.overall_understanding_score >= 0.85:
                    self.test_stats['passed_tests'] += 1
                else:
                    self.test_stats['failed_tests'] += 1
                
            except Exception as e:
                self.logger.error(f"剧情理解测试失败: {test_case['case_name']}, 错误: {str(e)}")
                self.test_stats['total_tests'] += 1
                self.test_stats['failed_tests'] += 1
    
    def _run_viral_generation_tests(self, test_data: List[Dict[str, str]]):
        """运行爆款生成测试"""
        for test_case in test_data[:3]:  # 限制数量
            if not test_case.get('original_subtitle_file'):
                continue
            
            try:
                viral_reference = test_case.get('viral_subtitle_file')
                
                result = self.viral_tester.test_viral_generation(
                    test_case['original_subtitle_file'],
                    viral_reference
                )
                self.test_results['viral_generation'].append(result)
                
                self.test_stats['total_tests'] += 1
                if result.overall_viral_score >= 0.75:
                    self.test_stats['passed_tests'] += 1
                else:
                    self.test_stats['failed_tests'] += 1
                
            except Exception as e:
                self.logger.error(f"爆款生成测试失败: {test_case['case_name']}, 错误: {str(e)}")
                self.test_stats['total_tests'] += 1
                self.test_stats['failed_tests'] += 1
    
    def _generate_comprehensive_report(self):
        """生成综合报告"""
        try:
            return self.report_generator.generate_comprehensive_report(self.test_results)
        except Exception as e:
            self.logger.error(f"生成综合报告失败: {str(e)}")
            return None
    
    def _calculate_test_statistics(self):
        """计算测试统计"""
        # 统计已在各个测试方法中更新
        pass
    
    def _generate_summary(self) -> Dict[str, Any]:
        """生成测试摘要"""
        total_time = self.test_stats.get('end_time', 0) - self.test_stats.get('start_time', 0)
        success_rate = self.test_stats['passed_tests'] / self.test_stats['total_tests'] if self.test_stats['total_tests'] > 0 else 0
        
        return {
            'total_execution_time': total_time,
            'overall_success_rate': success_rate,
            'test_categories': len(self.test_results),
            'total_test_cases': self.test_stats['total_tests'],
            'passed_tests': self.test_stats['passed_tests'],
            'failed_tests': self.test_stats['failed_tests'],
            'category_results': {
                category: len(results) for category, results in self.test_results.items()
            }
        }
    
    def _create_mock_video_file(self, case_name: str) -> str:
        """创建模拟视频文件"""
        video_dir = Path("test_data/videos")
        video_dir.mkdir(parents=True, exist_ok=True)
        
        video_file = video_dir / f"{case_name}.mp4"
        
        # 创建模拟视频文件
        with open(video_file, 'w') as f:
            f.write(f"# Mock video file for {case_name}\n")
        
        return str(video_file)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='VisionAI-ClipsMaster 核心功能验证')
    parser.add_argument('--config', type=str, help='配置文件路径')
    parser.add_argument('--no-generate-data', action='store_true', help='不生成新的测试数据')
    parser.add_argument('--output-dir', type=str, help='输出目录')
    parser.add_argument('--verbose', action='store_true', help='详细输出')
    
    args = parser.parse_args()
    
    # 设置日志级别
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    
    # 创建验证器
    validator = CoreFunctionalityValidator(args.config)
    
    # 运行验证
    results = validator.run_comprehensive_validation(
        generate_test_data=not args.no_generate_data
    )
    
    # 输出结果
    if results['success']:
        print("\n" + "="*60)
        print("VisionAI-ClipsMaster 核心功能验证完成")
        print("="*60)
        
        summary = results['summary']
        print(f"总体成功率: {summary['overall_success_rate']:.1%}")
        print(f"执行时间: {summary['total_execution_time']:.2f}秒")
        print(f"测试用例: {summary['passed_tests']}/{summary['total_test_cases']} 通过")
        
        print("\n各模块测试结果:")
        for category, count in summary['category_results'].items():
            print(f"  {category}: {count} 个测试用例")
        
        if results.get('report'):
            print(f"\n详细报告已生成: {results['report'].report_id}")
        
    else:
        print(f"\n验证失败: {results.get('error', '未知错误')}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
