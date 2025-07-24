#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 真实世界端到端测试主执行器

此脚本执行完整的真实环境端到端功能验证测试，
从视频上传到剪映工程文件生成的全链路测试。
"""

import os
import sys
import time
import logging
import argparse
from typing import Dict, List, Any, Optional
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# 导入测试模块
from video_preprocessing.test_video_upload import RealWorldVideoUploadTester
from ai_script_reconstruction.test_content_understanding import RealWorldContentUnderstandingTester
from workflow_integration.test_complete_pipeline import CompletePipelineTester
from performance_monitoring.test_memory_constraints import MemoryConstraintTester
from jianying_compatibility.test_import_compatibility import JianyingImportCompatibilityTester
from reporting.real_world_report_generator import RealWorldReportGenerator
from test_data.create_test_dataset import RealWorldTestDatasetCreator

# 导入工具模块
from src.utils.log_handler import LogHandler

logger = logging.getLogger(__name__)


class RealWorldE2ETestRunner:
    """真实世界端到端测试执行器"""
    
    def __init__(self, config_path: str = None):
        """初始化测试执行器"""
        self.config_path = config_path or "tests/real_world_validation/real_world_config.yaml"
        self.config = self._load_config()
        
        # 设置日志
        self.logger = LogHandler.get_logger(
            name=__name__,
            level=self.config.get('test_environment', {}).get('log_level', 'INFO')
        )
        
        # 初始化测试组件
        self.video_upload_tester = RealWorldVideoUploadTester(self.config_path)
        self.content_understanding_tester = RealWorldContentUnderstandingTester(self.config_path)
        self.pipeline_tester = CompletePipelineTester(self.config_path)
        self.memory_tester = MemoryConstraintTester(self.config_path)
        self.compatibility_tester = JianyingImportCompatibilityTester(self.config_path)
        self.report_generator = RealWorldReportGenerator(self.config_path)
        self.dataset_creator = RealWorldTestDatasetCreator(self.config_path)
        
        # 测试结果存储
        self.all_test_results = []
        
        # 创建输出目录
        self.output_dir = Path(self.config.get('file_paths', {}).get('output', {}).get('reports_dir', 'tests/reports/real_world_validation'))
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        try:
            import yaml
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.warning(f"无法加载配置文件 {self.config_path}: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'test_environment': {'log_level': 'INFO'},
            'file_paths': {'output': {'reports_dir': 'tests/reports/real_world_validation'}}
        }
    
    def run_complete_real_world_test(self, test_videos: List[str] = None, 
                                   test_duration_hours: float = 2.0,
                                   skip_data_creation: bool = False) -> Dict[str, Any]:
        """
        运行完整的真实世界测试
        
        Args:
            test_videos: 测试视频文件列表
            test_duration_hours: 测试持续时间
            skip_data_creation: 是否跳过测试数据创建
            
        Returns:
            Dict[str, Any]: 测试结果摘要
        """
        test_start_time = time.time()
        
        self.logger.info("=" * 80)
        self.logger.info("开始VisionAI-ClipsMaster真实世界端到端测试")
        self.logger.info("=" * 80)
        
        try:
            # 阶段1：准备测试数据
            if not skip_data_creation:
                self.logger.info("阶段1: 准备测试数据")
                test_dataset = self._prepare_test_data()
                if test_videos is None:
                    test_videos = [video.name for video in test_dataset.videos if os.path.exists(video.name)]
            else:
                test_videos = test_videos or self._get_existing_test_videos()
            
            if not test_videos:
                raise RuntimeError("没有可用的测试视频文件")
            
            self.logger.info(f"使用测试视频: {len(test_videos)} 个文件")
            
            # 阶段2：视频上传和预处理测试
            self.logger.info("阶段2: 视频上传和预处理测试")
            upload_results = self._run_video_upload_tests(test_videos)
            
            # 阶段3：AI内容理解测试
            self.logger.info("阶段3: AI内容理解测试")
            understanding_results = self._run_content_understanding_tests(test_videos)
            
            # 阶段4：完整工作流程测试
            self.logger.info("阶段4: 完整工作流程测试")
            pipeline_results = self._run_complete_pipeline_tests(test_videos)
            
            # 阶段5：性能和稳定性测试
            self.logger.info("阶段5: 性能和稳定性测试")
            performance_results = self._run_performance_tests(test_videos, test_duration_hours)
            
            # 阶段6：剪映兼容性测试
            self.logger.info("阶段6: 剪映兼容性测试")
            compatibility_results = self._run_compatibility_tests(pipeline_results)
            
            # 收集所有测试结果
            all_results = {
                'video_upload': upload_results,
                'content_understanding': understanding_results,
                'complete_pipeline': pipeline_results,
                'performance_monitoring': performance_results,
                'jianying_compatibility': compatibility_results
            }
            
            # 阶段7：生成综合报告
            self.logger.info("阶段7: 生成综合报告")
            report_files = self._generate_comprehensive_report(all_results, test_start_time)
            
            # 计算总体结果
            test_summary = self._calculate_test_summary(all_results, test_start_time)
            
            self.logger.info("=" * 80)
            self.logger.info("真实世界端到端测试完成")
            self.logger.info(f"总体成功率: {test_summary['overall_success_rate']:.2%}")
            self.logger.info(f"总测试时间: {test_summary['total_duration']:.1f} 秒")
            self.logger.info(f"生成报告: {list(report_files.values())}")
            self.logger.info("=" * 80)
            
            return {
                'success': test_summary['overall_success'],
                'summary': test_summary,
                'detailed_results': all_results,
                'report_files': report_files
            }
            
        except Exception as e:
            self.logger.error(f"真实世界端到端测试失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'summary': {'overall_success_rate': 0.0, 'total_duration': time.time() - test_start_time},
                'detailed_results': {},
                'report_files': {}
            }
    
    def _prepare_test_data(self):
        """准备测试数据"""
        try:
            self.logger.info("创建测试数据集...")
            dataset = self.dataset_creator.create_complete_test_dataset()
            self.logger.info(f"测试数据集创建完成: {dataset.dataset_id}")
            return dataset
        except Exception as e:
            self.logger.warning(f"创建测试数据集失败: {str(e)}")
            return None
    
    def _get_existing_test_videos(self) -> List[str]:
        """获取现有测试视频"""
        videos_dir = Path("tests/real_world_validation/test_data/videos")
        if not videos_dir.exists():
            return []
        
        video_files = []
        for ext in ['*.mp4', '*.mov', '*.avi', '*.mkv']:
            video_files.extend(videos_dir.glob(ext))
        
        return [str(f) for f in video_files if f.stat().st_size > 1024]  # 过滤掉太小的文件
    
    def _run_video_upload_tests(self, test_videos: List[str]) -> List[Dict[str, Any]]:
        """运行视频上传测试"""
        results = []
        
        for video_file in test_videos:
            try:
                self.logger.info(f"测试视频上传: {Path(video_file).name}")
                result = self.video_upload_tester.test_real_video_upload(video_file)
                results.append(result.__dict__)
            except Exception as e:
                self.logger.error(f"视频上传测试失败: {video_file}, 错误: {str(e)}")
                results.append({
                    'test_name': 'video_upload',
                    'video_file_path': video_file,
                    'success': False,
                    'error_message': str(e)
                })
        
        return results
    
    def _run_content_understanding_tests(self, test_videos: List[str]) -> List[Dict[str, Any]]:
        """运行内容理解测试"""
        results = []
        
        for video_file in test_videos:
            try:
                self.logger.info(f"测试内容理解: {Path(video_file).name}")
                result = self.content_understanding_tester.test_real_video_content_understanding(video_file)
                results.append(result.__dict__)
            except Exception as e:
                self.logger.error(f"内容理解测试失败: {video_file}, 错误: {str(e)}")
                results.append({
                    'test_name': 'content_understanding',
                    'video_file_path': video_file,
                    'success': False,
                    'error_message': str(e)
                })
        
        return results
    
    def _run_complete_pipeline_tests(self, test_videos: List[str]) -> List[Dict[str, Any]]:
        """运行完整流水线测试"""
        results = []
        
        for video_file in test_videos:
            try:
                self.logger.info(f"测试完整流水线: {Path(video_file).name}")
                result = self.pipeline_tester.test_complete_pipeline(video_file)
                results.append(result.__dict__)
            except Exception as e:
                self.logger.error(f"完整流水线测试失败: {video_file}, 错误: {str(e)}")
                results.append({
                    'test_name': 'complete_pipeline',
                    'video_file_path': video_file,
                    'success': False,
                    'error_message': str(e)
                })
        
        return results
    
    def _run_performance_tests(self, test_videos: List[str], test_duration_hours: float) -> List[Dict[str, Any]]:
        """运行性能测试"""
        results = []
        
        try:
            self.logger.info(f"开始性能和稳定性测试，持续时间: {test_duration_hours} 小时")
            
            # 内存限制测试
            memory_result = self.memory_tester.test_memory_constrained_processing(
                test_videos, test_duration_hours
            )
            results.append(memory_result.__dict__)
            
        except Exception as e:
            self.logger.error(f"性能测试失败: {str(e)}")
            results.append({
                'test_name': 'performance_monitoring',
                'success': False,
                'error_message': str(e)
            })
        
        return results
    
    def _run_compatibility_tests(self, pipeline_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """运行兼容性测试"""
        results = []
        
        # 从流水线结果中提取生成的draftinfo文件
        draftinfo_files = []
        for result in pipeline_results:
            if result.get('success', False) and 'final_outputs' in result:
                draftinfo_path = result['final_outputs'].get('draftinfo_file', '')
                if draftinfo_path and os.path.exists(draftinfo_path):
                    draftinfo_files.append(draftinfo_path)
        
        if not draftinfo_files:
            self.logger.warning("没有找到可用的剪映工程文件进行兼容性测试")
            return results
        
        for draftinfo_file in draftinfo_files:
            try:
                self.logger.info(f"测试剪映兼容性: {Path(draftinfo_file).name}")
                result = self.compatibility_tester.test_real_world_import_compatibility(draftinfo_file)
                results.append(result.__dict__)
            except Exception as e:
                self.logger.error(f"兼容性测试失败: {draftinfo_file}, 错误: {str(e)}")
                results.append({
                    'test_name': 'jianying_compatibility',
                    'draftinfo_file_path': draftinfo_file,
                    'success': False,
                    'error_message': str(e)
                })
        
        return results
    
    def _generate_comprehensive_report(self, all_results: Dict[str, List], test_start_time: float) -> Dict[str, str]:
        """生成综合报告"""
        try:
            # 展平所有测试结果
            flattened_results = []
            for category, results in all_results.items():
                for result in results:
                    result['test_category'] = category
                    flattened_results.append(result)
            
            # 生成测试元数据
            test_metadata = {
                'test_start_time': test_start_time,
                'test_end_time': time.time(),
                'test_categories': list(all_results.keys()),
                'total_tests': sum(len(results) for results in all_results.values()),
                'config_file': self.config_path
            }
            
            # 生成报告
            report_files = self.report_generator.generate_comprehensive_report(
                flattened_results, test_metadata
            )
            
            return report_files
            
        except Exception as e:
            self.logger.error(f"生成综合报告失败: {str(e)}")
            return {}
    
    def _calculate_test_summary(self, all_results: Dict[str, List], test_start_time: float) -> Dict[str, Any]:
        """计算测试摘要"""
        total_tests = 0
        successful_tests = 0
        
        category_summaries = {}
        
        for category, results in all_results.items():
            category_total = len(results)
            category_successful = sum(1 for result in results if result.get('success', False))
            
            total_tests += category_total
            successful_tests += category_successful
            
            category_summaries[category] = {
                'total': category_total,
                'successful': category_successful,
                'success_rate': category_successful / category_total if category_total > 0 else 0
            }
        
        overall_success_rate = successful_tests / total_tests if total_tests > 0 else 0
        total_duration = time.time() - test_start_time
        
        return {
            'total_tests': total_tests,
            'successful_tests': successful_tests,
            'failed_tests': total_tests - successful_tests,
            'overall_success_rate': overall_success_rate,
            'overall_success': overall_success_rate >= 0.8,  # 80%成功率阈值
            'total_duration': total_duration,
            'category_summaries': category_summaries
        }


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='VisionAI-ClipsMaster 真实世界端到端测试')
    parser.add_argument('--videos', nargs='+', help='指定测试视频文件')
    parser.add_argument('--duration', type=float, default=2.0, help='性能测试持续时间（小时）')
    parser.add_argument('--config', type=str, help='配置文件路径')
    parser.add_argument('--skip-data-creation', action='store_true', help='跳过测试数据创建')
    parser.add_argument('--verbose', action='store_true', help='详细输出')
    parser.add_argument('--performance-test', action='store_true', help='仅运行性能测试')
    
    args = parser.parse_args()
    
    # 设置日志级别
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    else:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # 创建测试执行器
    runner = RealWorldE2ETestRunner(args.config)
    
    try:
        # 运行测试
        if args.performance_test:
            # 仅运行性能测试
            test_videos = args.videos or runner._get_existing_test_videos()
            if not test_videos:
                print("❌ 没有找到测试视频文件")
                sys.exit(1)
            
            print(f"🚀 开始性能测试，持续时间: {args.duration} 小时")
            performance_results = runner._run_performance_tests(test_videos, args.duration)
            
            success_count = sum(1 for result in performance_results if result.get('success', False))
            print(f"\n性能测试完成:")
            print(f"总测试数: {len(performance_results)}")
            print(f"成功数: {success_count}")
            print(f"成功率: {success_count/len(performance_results):.2%}")
        else:
            # 运行完整测试
            print("🚀 开始VisionAI-ClipsMaster真实世界端到端测试")
            
            result = runner.run_complete_real_world_test(
                test_videos=args.videos,
                test_duration_hours=args.duration,
                skip_data_creation=args.skip_data_creation
            )
            
            # 输出结果摘要
            if result['success']:
                summary = result['summary']
                print(f"\n✅ 测试完成!")
                print(f"总测试数: {summary['total_tests']}")
                print(f"成功数: {summary['successful_tests']}")
                print(f"失败数: {summary['failed_tests']}")
                print(f"总体成功率: {summary['overall_success_rate']:.2%}")
                print(f"测试时长: {summary['total_duration']:.1f} 秒")
                
                # 显示各类别结果
                print(f"\n📊 各类别测试结果:")
                for category, cat_summary in summary['category_summaries'].items():
                    print(f"  {category}: {cat_summary['successful']}/{cat_summary['total']} ({cat_summary['success_rate']:.2%})")
                
                # 显示报告文件
                if result['report_files']:
                    print(f"\n📄 生成的报告文件:")
                    for format_type, file_path in result['report_files'].items():
                        print(f"  {format_type.upper()}: {file_path}")
                
                sys.exit(0 if summary['overall_success'] else 1)
            else:
                print(f"❌ 测试失败: {result.get('error', 'Unknown error')}")
                sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n⚠️  测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 测试执行异常: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
