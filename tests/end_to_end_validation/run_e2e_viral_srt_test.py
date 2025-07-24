#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 爆款SRT剪辑功能端到端测试执行器

此脚本按照完整工作流程顺序执行所有测试步骤，验证从爆款SRT字幕文件到剪映工程文件的完整链路。
"""

import os
import sys
import json
import time
import logging
import argparse
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# 导入测试模块
from test_data_preparation.e2e_data_generator import E2EDataGenerator
from srt_parsing_tests.test_viral_srt_parser import ViralSRTParserTester
from srt_parsing_tests.test_timecode_validation import TimecodeValidator
from video_editing_tests.test_video_segment_cutting import VideoSegmentCutter
from video_editing_tests.test_segment_concatenation import SegmentConcatenator
from jianying_integration_tests.test_draftinfo_generation import DraftinfoGenerator
from jianying_integration_tests.test_jianying_import import JianyingImportTester

# 导入工具模块
from src.utils.log_handler import LogHandler

logger = logging.getLogger(__name__)


@dataclass
class E2ETestResult:
    """端到端测试结果"""
    test_id: str
    scenario_type: str
    start_time: float
    end_time: float
    total_duration: float
    stage_results: Dict[str, Any]
    overall_success: bool
    success_rate: float
    critical_errors: List[str]
    warnings: List[str]
    performance_metrics: Dict[str, float]


class E2EViralSRTTestRunner:
    """端到端爆款SRT测试执行器"""
    
    def __init__(self, config_path: str = None):
        """初始化测试执行器"""
        self.config = self._load_config(config_path)
        
        # 设置日志
        self.logger = LogHandler.get_logger(
            name=__name__,
            level=self.config.get('test_environment', {}).get('log_level', 'INFO')
        )
        
        # 初始化测试组件
        self.data_generator = E2EDataGenerator(config_path)
        self.srt_parser_tester = ViralSRTParserTester(config_path)
        self.timecode_validator = TimecodeValidator(config_path)
        self.video_cutter = VideoSegmentCutter(config_path)
        self.segment_concatenator = SegmentConcatenator(config_path)
        self.draftinfo_generator = DraftinfoGenerator(config_path)
        self.jianying_import_tester = JianyingImportTester(config_path)
        
        # 测试阶段配置
        self.test_stages = self.config.get('test_stages', {})
        
        # 测试结果存储
        self.test_results = []
        
        # 创建输出目录
        self.output_dir = Path(self.config.get('file_paths', {}).get('output', {}).get('reports_dir', 'tests/reports/e2e_validation'))
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """加载配置"""
        if config_path is None:
            config_path = "tests/end_to_end_validation/e2e_config.yaml"
        
        try:
            import yaml
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.warning(f"无法加载配置文件 {config_path}: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'test_environment': {'log_level': 'INFO'},
            'test_stages': {
                'srt_parsing': {'enabled': True, 'timeout': 30},
                'video_editing': {'enabled': True, 'timeout': 600},
                'jianying_integration': {'enabled': True, 'timeout': 120},
                'import_validation': {'enabled': True, 'timeout': 180}
            },
            'file_paths': {'output': {'reports_dir': 'tests/reports/e2e_validation'}}
        }
    
    def run_complete_e2e_test(self, scenario_types: List[str] = None, 
                             use_existing_data: bool = False) -> List[E2ETestResult]:
        """
        运行完整的端到端测试
        
        Args:
            scenario_types: 要测试的场景类型列表
            use_existing_data: 是否使用现有测试数据
            
        Returns:
            List[E2ETestResult]: 测试结果列表
        """
        if scenario_types is None:
            scenario_types = ["basic", "complex", "boundary"]
        
        self.logger.info(f"开始端到端测试，场景类型: {scenario_types}")
        
        all_results = []
        
        for scenario_type in scenario_types:
            try:
                result = self._run_single_scenario_test(scenario_type, use_existing_data)
                all_results.append(result)
                
                self.logger.info(f"场景 {scenario_type} 测试完成，成功率: {result.success_rate:.2%}")
                
            except Exception as e:
                self.logger.error(f"场景 {scenario_type} 测试失败: {str(e)}")
                
                # 创建失败结果
                failed_result = E2ETestResult(
                    test_id=f"e2e_test_{scenario_type}_{int(time.time())}",
                    scenario_type=scenario_type,
                    start_time=time.time(),
                    end_time=time.time(),
                    total_duration=0.0,
                    stage_results={},
                    overall_success=False,
                    success_rate=0.0,
                    critical_errors=[str(e)],
                    warnings=[],
                    performance_metrics={}
                )
                all_results.append(failed_result)
        
        # 生成综合报告
        self._generate_comprehensive_report(all_results)
        
        self.logger.info(f"端到端测试完成，总共测试了 {len(all_results)} 个场景")
        
        return all_results
    
    def _run_single_scenario_test(self, scenario_type: str, use_existing_data: bool) -> E2ETestResult:
        """运行单个场景的测试"""
        test_id = f"e2e_test_{scenario_type}_{int(time.time())}"
        start_time = time.time()
        
        self.logger.info(f"开始测试场景: {scenario_type}")
        
        stage_results = {}
        critical_errors = []
        warnings = []
        performance_metrics = {}
        
        try:
            # 阶段1：准备测试数据
            if not use_existing_data:
                self.logger.info("阶段1: 生成测试数据")
                dataset = self.data_generator.generate_complete_dataset(scenario_type)
            else:
                # 使用现有数据的逻辑
                dataset = self._load_existing_dataset(scenario_type)
            
            stage_results['data_preparation'] = {
                'success': True,
                'dataset_id': dataset.dataset_id,
                'files': {
                    'original_video': dataset.original_video_path,
                    'viral_srt': dataset.viral_srt_path,
                    'expected_segments': dataset.expected_segments_dir,
                    'expected_draftinfo': dataset.expected_draftinfo_path
                }
            }
            
            # 阶段2：SRT解析和验证
            if self.test_stages.get('srt_parsing', {}).get('enabled', True):
                self.logger.info("阶段2: SRT解析和验证")
                srt_results = self._run_srt_parsing_tests(dataset)
                stage_results['srt_parsing'] = srt_results
                
                if not srt_results['overall_success']:
                    critical_errors.extend(srt_results.get('errors', []))
            
            # 阶段3：视频编辑测试
            if self.test_stages.get('video_editing', {}).get('enabled', True):
                self.logger.info("阶段3: 视频编辑测试")
                video_results = self._run_video_editing_tests(dataset)
                stage_results['video_editing'] = video_results
                
                if not video_results['overall_success']:
                    critical_errors.extend(video_results.get('errors', []))
            
            # 阶段4：剪映集成测试
            if self.test_stages.get('jianying_integration', {}).get('enabled', True):
                self.logger.info("阶段4: 剪映集成测试")
                jianying_results = self._run_jianying_integration_tests(dataset)
                stage_results['jianying_integration'] = jianying_results
                
                if not jianying_results['overall_success']:
                    critical_errors.extend(jianying_results.get('errors', []))
            
            # 阶段5：导入验证测试
            if self.test_stages.get('import_validation', {}).get('enabled', True):
                self.logger.info("阶段5: 导入验证测试")
                import_results = self._run_import_validation_tests(dataset)
                stage_results['import_validation'] = import_results
                
                if not import_results['overall_success']:
                    critical_errors.extend(import_results.get('errors', []))
            
            # 计算总体结果
            end_time = time.time()
            total_duration = end_time - start_time
            
            # 计算成功率
            successful_stages = sum(1 for result in stage_results.values() if result.get('overall_success', False))
            total_stages = len(stage_results)
            success_rate = successful_stages / total_stages if total_stages > 0 else 0.0
            
            overall_success = len(critical_errors) == 0 and success_rate >= 0.8
            
            # 收集性能指标
            performance_metrics = self._collect_performance_metrics(stage_results, total_duration)
            
            result = E2ETestResult(
                test_id=test_id,
                scenario_type=scenario_type,
                start_time=start_time,
                end_time=end_time,
                total_duration=total_duration,
                stage_results=stage_results,
                overall_success=overall_success,
                success_rate=success_rate,
                critical_errors=critical_errors,
                warnings=warnings,
                performance_metrics=performance_metrics
            )
            
            self.test_results.append(result)
            return result
            
        except Exception as e:
            self.logger.error(f"场景 {scenario_type} 测试异常: {str(e)}")
            
            end_time = time.time()
            return E2ETestResult(
                test_id=test_id,
                scenario_type=scenario_type,
                start_time=start_time,
                end_time=end_time,
                total_duration=end_time - start_time,
                stage_results=stage_results,
                overall_success=False,
                success_rate=0.0,
                critical_errors=[str(e)],
                warnings=warnings,
                performance_metrics={}
            )
    
    def _run_srt_parsing_tests(self, dataset) -> Dict[str, Any]:
        """运行SRT解析测试"""
        results = {
            'stage_name': 'SRT解析和验证',
            'tests': {},
            'overall_success': True,
            'errors': []
        }
        
        try:
            # SRT格式验证
            format_result = self.srt_parser_tester.test_srt_format_validation(dataset.viral_srt_path)
            results['tests']['format_validation'] = {
                'success': format_result.success,
                'parsing_time': format_result.parsing_time,
                'valid_segments': format_result.valid_segments,
                'total_segments': format_result.total_segments
            }
            
            if not format_result.success:
                results['overall_success'] = False
                results['errors'].extend(format_result.format_errors)
            
            # 时间码精度验证
            precision_result = self.timecode_validator.validate_timecode_format(dataset.viral_srt_path)
            results['tests']['timecode_validation'] = {
                'success': precision_result.success,
                'processing_time': precision_result.processing_time,
                'valid_timecodes': precision_result.valid_timecodes,
                'total_timecodes': precision_result.total_timecodes
            }
            
            if not precision_result.success:
                results['overall_success'] = False
                results['errors'].extend([str(e) for e in precision_result.precision_errors])
            
            # 片段提取逻辑验证
            extraction_result = self.srt_parser_tester.test_segment_extraction_logic(dataset.viral_srt_path)
            results['tests']['segment_extraction'] = {
                'success': extraction_result.success,
                'processing_time': extraction_result.parsing_time,
                'extracted_segments': extraction_result.valid_segments
            }
            
            if not extraction_result.success:
                results['overall_success'] = False
                results['errors'].extend(extraction_result.timecode_errors)
            
        except Exception as e:
            results['overall_success'] = False
            results['errors'].append(f"SRT解析测试异常: {str(e)}")
        
        return results
    
    def _run_video_editing_tests(self, dataset) -> Dict[str, Any]:
        """运行视频编辑测试"""
        results = {
            'stage_name': '视频编辑测试',
            'tests': {},
            'overall_success': True,
            'errors': []
        }
        
        try:
            # 视频片段剪切测试
            cutting_result = self.video_cutter.test_segment_cutting_accuracy(
                dataset.original_video_path, dataset.viral_srt_path
            )
            results['tests']['segment_cutting'] = {
                'success': cutting_result.success,
                'processing_time': cutting_result.total_processing_time,
                'successfully_cut_segments': cutting_result.successfully_cut_segments,
                'total_segments': cutting_result.total_segments,
                'cutting_accuracy': cutting_result.cutting_accuracy
            }
            
            if not cutting_result.success:
                results['overall_success'] = False
                results['errors'].extend([str(e) for e in cutting_result.cutting_errors])
            
            # 如果剪切成功，进行拼接测试
            if cutting_result.success and cutting_result.output_segments_dir:
                concatenation_result = self.segment_concatenator.test_segment_concatenation(
                    cutting_result.output_segments_dir
                )
                results['tests']['segment_concatenation'] = {
                    'success': concatenation_result.success,
                    'processing_time': concatenation_result.processing_time,
                    'concatenated_segments': concatenation_result.successfully_concatenated_segments,
                    'duration_accuracy': concatenation_result.duration_accuracy_error
                }
                
                if not concatenation_result.success:
                    results['overall_success'] = False
                    results['errors'].extend([str(e) for e in concatenation_result.concatenation_errors])
            
        except Exception as e:
            results['overall_success'] = False
            results['errors'].append(f"视频编辑测试异常: {str(e)}")
        
        return results
    
    def _run_jianying_integration_tests(self, dataset) -> Dict[str, Any]:
        """运行剪映集成测试"""
        results = {
            'stage_name': '剪映集成测试',
            'tests': {},
            'overall_success': True,
            'errors': []
        }
        
        try:
            # 获取视频片段列表
            segments_dir = Path(dataset.expected_segments_dir)
            segment_files = list(segments_dir.glob("*.mp4"))
            
            # 剪映工程文件生成测试
            draftinfo_result = self.draftinfo_generator.test_draftinfo_generation(
                [str(f) for f in segment_files], f"test_project_{dataset.scenario_type}"
            )
            results['tests']['draftinfo_generation'] = {
                'success': draftinfo_result.success,
                'generation_time': draftinfo_result.generation_time,
                'file_size': draftinfo_result.file_size_bytes,
                'json_structure_valid': draftinfo_result.json_structure_valid,
                'file_paths_valid': draftinfo_result.file_paths_valid
            }
            
            if not draftinfo_result.success:
                results['overall_success'] = False
                results['errors'].extend([str(e) for e in draftinfo_result.validation_errors])
            
        except Exception as e:
            results['overall_success'] = False
            results['errors'].append(f"剪映集成测试异常: {str(e)}")
        
        return results
    
    def _run_import_validation_tests(self, dataset) -> Dict[str, Any]:
        """运行导入验证测试"""
        results = {
            'stage_name': '导入验证测试',
            'tests': {},
            'overall_success': True,
            'errors': []
        }
        
        try:
            # 剪映导入测试
            import_result = self.jianying_import_tester.test_jianying_import(
                dataset.expected_draftinfo_path
            )
            results['tests']['jianying_import'] = {
                'success': import_result.success,
                'import_time': import_result.import_time,
                'compatibility_score': import_result.compatibility_score,
                'timeline_structure_correct': import_result.timeline_structure_correct,
                'editing_capabilities_available': import_result.editing_capabilities_available
            }
            
            if not import_result.success:
                results['overall_success'] = False
                results['errors'].extend([str(e) for e in import_result.import_errors])
            
        except Exception as e:
            results['overall_success'] = False
            results['errors'].append(f"导入验证测试异常: {str(e)}")
        
        return results
    
    def _collect_performance_metrics(self, stage_results: Dict[str, Any], total_duration: float) -> Dict[str, float]:
        """收集性能指标"""
        metrics = {
            'total_duration': total_duration,
            'stages_count': len(stage_results),
            'successful_stages': sum(1 for r in stage_results.values() if r.get('overall_success', False))
        }
        
        # 收集各阶段的处理时间
        for stage_name, stage_result in stage_results.items():
            if stage_name == 'data_preparation':
                continue
            
            tests = stage_result.get('tests', {})
            stage_time = 0
            
            for test_name, test_result in tests.items():
                test_time = test_result.get('processing_time', 0) or test_result.get('generation_time', 0) or test_result.get('import_time', 0)
                stage_time += test_time
            
            if stage_time > 0:
                metrics[f'{stage_name}_duration'] = stage_time
        
        return metrics
    
    def _load_existing_dataset(self, scenario_type: str):
        """加载现有数据集（占位符实现）"""
        # 这里应该实现加载现有测试数据的逻辑
        raise NotImplementedError("加载现有数据集功能尚未实现")
    
    def _generate_comprehensive_report(self, results: List[E2ETestResult]):
        """生成综合测试报告"""
        report_data = {
            'test_summary': {
                'total_scenarios': len(results),
                'successful_scenarios': sum(1 for r in results if r.overall_success),
                'total_duration': sum(r.total_duration for r in results),
                'average_success_rate': sum(r.success_rate for r in results) / len(results) if results else 0
            },
            'scenario_results': [],
            'performance_analysis': {},
            'recommendations': []
        }
        
        for result in results:
            report_data['scenario_results'].append({
                'test_id': result.test_id,
                'scenario_type': result.scenario_type,
                'overall_success': result.overall_success,
                'success_rate': result.success_rate,
                'duration': result.total_duration,
                'critical_errors_count': len(result.critical_errors),
                'warnings_count': len(result.warnings)
            })
        
        # 保存报告
        report_path = self.output_dir / f"e2e_test_report_{int(time.time())}.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"综合测试报告已生成: {report_path}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='VisionAI-ClipsMaster 端到端测试执行器')
    parser.add_argument('--scenarios', nargs='+', default=['basic', 'complex'], 
                       help='要测试的场景类型')
    parser.add_argument('--config', type=str, help='配置文件路径')
    parser.add_argument('--use-existing-data', action='store_true', 
                       help='使用现有测试数据')
    parser.add_argument('--verbose', action='store_true', help='详细输出')
    
    args = parser.parse_args()
    
    # 设置日志级别
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    
    # 创建测试执行器
    runner = E2EViralSRTTestRunner(args.config)
    
    # 运行测试
    results = runner.run_complete_e2e_test(
        scenario_types=args.scenarios,
        use_existing_data=args.use_existing_data
    )
    
    # 输出结果摘要
    successful_count = sum(1 for r in results if r.overall_success)
    total_count = len(results)
    
    print(f"\n端到端测试完成:")
    print(f"总场景数: {total_count}")
    print(f"成功场景数: {successful_count}")
    print(f"成功率: {successful_count/total_count:.2%}")
    
    if successful_count == total_count:
        print("✅ 所有测试场景都通过了!")
        sys.exit(0)
    else:
        print("❌ 部分测试场景失败")
        sys.exit(1)


if __name__ == "__main__":
    main()
