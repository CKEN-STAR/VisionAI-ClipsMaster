#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 综合测试报告生成器

此模块负责生成详细的测试报告，包括：
1. 测试结果汇总和分析
2. 性能指标可视化
3. 问题诊断和建议
4. 多格式报告输出（HTML、JSON、PDF）
"""

import os
import sys
import json
import time
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
import numpy as np

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from src.utils.log_handler import LogHandler

logger = logging.getLogger(__name__)


@dataclass
class TestReport:
    """测试报告数据结构"""
    report_id: str
    generated_at: datetime
    test_summary: Dict[str, Any]
    timeline_accuracy_results: List[Dict[str, Any]]
    plot_understanding_results: List[Dict[str, Any]]
    viral_generation_results: List[Dict[str, Any]]
    multilingual_results: List[Dict[str, Any]]
    performance_metrics: Dict[str, Any]
    recommendations: List[str]
    detailed_analysis: Dict[str, Any]


class ComprehensiveReportGenerator:
    """综合测试报告生成器"""
    
    def __init__(self, config_path: str = None):
        """初始化报告生成器"""
        self.config = self._load_config(config_path)
        
        # 设置日志
        self.logger = LogHandler.get_logger(
            name=__name__,
            level=self.config.get('test_environment', {}).get('log_level', 'INFO')
        )
        
        # 创建报告输出目录
        self.output_dir = Path(self.config.get('reporting', {}).get('output_directory', 'tests/reports/core_functionality'))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 报告配置
        self.report_config = self.config.get('reporting', {})
        self.output_formats = self.report_config.get('output_formats', ['html', 'json'])
        self.include_visualizations = self.report_config.get('include_visualizations', True)
        
        # 阈值配置
        self.thresholds = self.config.get('test_thresholds', {})
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """加载配置"""
        if config_path is None:
            config_path = "tests/core_functionality_validation/test_config.yaml"
        
        try:
            import yaml
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.logger.warning(f"无法加载配置文件 {config_path}: {e}")
            return {
                'reporting': {
                    'output_directory': 'tests/reports/core_functionality',
                    'output_formats': ['html', 'json'],
                    'include_visualizations': True
                },
                'test_thresholds': {},
                'test_environment': {'log_level': 'INFO'}
            }
    
    def generate_comprehensive_report(self, test_results: Dict[str, List[Any]]) -> TestReport:
        """
        生成综合测试报告
        
        Args:
            test_results: 包含各类测试结果的字典
            
        Returns:
            TestReport: 生成的测试报告
        """
        report_id = f"core_functionality_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.logger.info(f"开始生成综合测试报告: {report_id}")
        
        # 提取各类测试结果
        timeline_results = test_results.get('timeline_accuracy', [])
        plot_results = test_results.get('plot_understanding', [])
        viral_results = test_results.get('viral_generation', [])
        multilingual_results = test_results.get('multilingual_support', [])
        
        # 生成测试汇总
        test_summary = self._generate_test_summary(test_results)
        
        # 分析性能指标
        performance_metrics = self._analyze_performance_metrics(test_results)
        
        # 生成详细分析
        detailed_analysis = self._generate_detailed_analysis(test_results)
        
        # 生成建议
        recommendations = self._generate_recommendations(test_results, performance_metrics)
        
        # 创建报告对象
        report = TestReport(
            report_id=report_id,
            generated_at=datetime.now(),
            test_summary=test_summary,
            timeline_accuracy_results=timeline_results,
            plot_understanding_results=plot_results,
            viral_generation_results=viral_results,
            multilingual_results=multilingual_results,
            performance_metrics=performance_metrics,
            recommendations=recommendations,
            detailed_analysis=detailed_analysis
        )
        
        # 保存报告
        self._save_report(report)
        
        self.logger.info(f"综合测试报告生成完成: {report_id}")
        
        return report
    
    def _generate_test_summary(self, test_results: Dict[str, List[Any]]) -> Dict[str, Any]:
        """生成测试汇总"""
        summary = {
            'total_test_categories': len(test_results),
            'total_test_cases': sum(len(results) for results in test_results.values()),
            'test_execution_time': datetime.now().isoformat(),
            'category_summaries': {}
        }
        
        # 分析各类测试结果
        for category, results in test_results.items():
            if not results:
                continue
            
            category_summary = self._analyze_category_results(category, results)
            summary['category_summaries'][category] = category_summary
        
        # 计算总体成功率
        total_passed = sum(cat['passed_tests'] for cat in summary['category_summaries'].values())
        total_tests = sum(cat['total_tests'] for cat in summary['category_summaries'].values())
        summary['overall_success_rate'] = total_passed / total_tests if total_tests > 0 else 0.0
        
        return summary
    
    def _analyze_category_results(self, category: str, results: List[Any]) -> Dict[str, Any]:
        """分析特定类别的测试结果"""
        if not results:
            return {
                'total_tests': 0,
                'passed_tests': 0,
                'failed_tests': 0,
                'success_rate': 0.0,
                'average_score': 0.0,
                'key_metrics': {}
            }
        
        total_tests = len(results)
        passed_tests = 0
        scores = []
        key_metrics = {}
        
        if category == 'timeline_accuracy':
            passed_tests = sum(1 for r in results if getattr(r, 'success_rate', 0) >= 0.95)
            scores = [getattr(r, 'success_rate', 0) for r in results]
            key_metrics = {
                'average_error': np.mean([getattr(r, 'average_error', 0) for r in results]),
                'max_error': np.max([getattr(r, 'max_error', 0) for r in results]),
                'mapping_success_rate': np.mean([getattr(r, 'success_rate', 0) for r in results])
            }
        
        elif category == 'plot_understanding':
            passed_tests = sum(1 for r in results if getattr(r, 'overall_understanding_score', 0) >= 0.85)
            scores = [getattr(r, 'overall_understanding_score', 0) for r in results]
            key_metrics = {
                'character_recognition_avg': np.mean([getattr(r, 'character_recognition_accuracy', 0) for r in results]),
                'plot_extraction_avg': np.mean([getattr(r, 'plot_point_extraction_score', 0) for r in results]),
                'narrative_coherence_avg': np.mean([getattr(r, 'narrative_coherence', 0) for r in results])
            }
        
        elif category == 'viral_generation':
            passed_tests = sum(1 for r in results if getattr(r, 'overall_viral_score', 0) >= 0.75)
            scores = [getattr(r, 'overall_viral_score', 0) for r in results]
            key_metrics = {
                'compression_ratio_avg': np.mean([getattr(r, 'compression_ratio', 0) for r in results]),
                'viral_features_avg': np.mean([getattr(r, 'viral_features_match', 0) for r in results]),
                'information_retention_avg': np.mean([getattr(r, 'key_information_retention', 0) for r in results])
            }
        
        elif category == 'multilingual_support':
            passed_tests = sum(1 for r in results if getattr(r, 'parsing_accuracy', 0) >= 0.98)
            scores = [getattr(r, 'parsing_accuracy', 0) for r in results]
            key_metrics = {
                'language_detection_accuracy': np.mean([1.0 if getattr(r, 'language_detection_correct', False) else 0.0 for r in results]),
                'parsing_success_rate': np.mean([1.0 if getattr(r, 'parsing_success', False) else 0.0 for r in results]),
                'encoding_error_rate': np.mean([getattr(r, 'encoding_issues', 0) for r in results])
            }
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': total_tests - passed_tests,
            'success_rate': passed_tests / total_tests,
            'average_score': np.mean(scores) if scores else 0.0,
            'key_metrics': key_metrics
        }
    
    def _analyze_performance_metrics(self, test_results: Dict[str, List[Any]]) -> Dict[str, Any]:
        """分析性能指标"""
        performance_metrics = {
            'processing_times': {},
            'memory_usage': {},
            'throughput': {},
            'resource_efficiency': {}
        }
        
        for category, results in test_results.items():
            if not results:
                continue
            
            # 处理时间分析
            processing_times = [getattr(r, 'processing_time', 0) for r in results if hasattr(r, 'processing_time')]
            if processing_times:
                performance_metrics['processing_times'][category] = {
                    'average': np.mean(processing_times),
                    'median': np.median(processing_times),
                    'min': np.min(processing_times),
                    'max': np.max(processing_times),
                    'std': np.std(processing_times)
                }
            
            # 内存使用分析
            memory_usages = [getattr(r, 'memory_usage', 0) for r in results if hasattr(r, 'memory_usage')]
            if memory_usages:
                performance_metrics['memory_usage'][category] = {
                    'average': np.mean(memory_usages),
                    'peak': np.max(memory_usages),
                    'min': np.min(memory_usages)
                }
            
            # 吞吐量分析
            if processing_times:
                # 假设每个测试处理一个单位的数据
                throughput = [1.0 / pt if pt > 0 else 0 for pt in processing_times]
                performance_metrics['throughput'][category] = {
                    'average_items_per_second': np.mean(throughput),
                    'peak_items_per_second': np.max(throughput)
                }
        
        # 计算资源效率
        performance_metrics['resource_efficiency'] = self._calculate_resource_efficiency(performance_metrics)
        
        return performance_metrics
    
    def _calculate_resource_efficiency(self, performance_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """计算资源效率"""
        efficiency = {}
        
        # 时间效率：处理速度相对于基准的比率
        baseline_time = 1.0  # 1秒作为基准
        for category, times in performance_metrics['processing_times'].items():
            avg_time = times.get('average', baseline_time)
            efficiency[f'{category}_time_efficiency'] = baseline_time / avg_time if avg_time > 0 else 0
        
        # 内存效率：内存使用相对于限制的比率
        memory_limit = 3.8 * 1024  # 3.8GB转换为MB
        for category, memory in performance_metrics['memory_usage'].items():
            avg_memory = memory.get('average', 0)
            efficiency[f'{category}_memory_efficiency'] = 1.0 - (avg_memory / memory_limit) if memory_limit > 0 else 1.0
        
        return efficiency
    
    def _generate_detailed_analysis(self, test_results: Dict[str, List[Any]]) -> Dict[str, Any]:
        """生成详细分析"""
        analysis = {
            'threshold_compliance': {},
            'trend_analysis': {},
            'correlation_analysis': {},
            'failure_analysis': {}
        }
        
        # 阈值合规性分析
        analysis['threshold_compliance'] = self._analyze_threshold_compliance(test_results)
        
        # 趋势分析
        analysis['trend_analysis'] = self._analyze_trends(test_results)
        
        # 相关性分析
        analysis['correlation_analysis'] = self._analyze_correlations(test_results)
        
        # 失败分析
        analysis['failure_analysis'] = self._analyze_failures(test_results)
        
        return analysis
    
    def _analyze_threshold_compliance(self, test_results: Dict[str, List[Any]]) -> Dict[str, Any]:
        """分析阈值合规性"""
        compliance = {}
        
        for category, results in test_results.items():
            if not results:
                continue
            
            category_compliance = {}
            
            if category == 'timeline_accuracy':
                threshold = self.thresholds.get('timeline_accuracy', 0.5)
                errors = [getattr(r, 'average_error', float('inf')) for r in results]
                compliant_count = sum(1 for error in errors if error <= threshold)
                category_compliance['timeline_accuracy_threshold'] = {
                    'threshold': threshold,
                    'compliant_tests': compliant_count,
                    'total_tests': len(results),
                    'compliance_rate': compliant_count / len(results)
                }
            
            elif category == 'plot_understanding':
                threshold = self.thresholds.get('plot_understanding', 0.85)
                scores = [getattr(r, 'overall_understanding_score', 0) for r in results]
                compliant_count = sum(1 for score in scores if score >= threshold)
                category_compliance['plot_understanding_threshold'] = {
                    'threshold': threshold,
                    'compliant_tests': compliant_count,
                    'total_tests': len(results),
                    'compliance_rate': compliant_count / len(results)
                }
            
            compliance[category] = category_compliance
        
        return compliance
    
    def _analyze_trends(self, test_results: Dict[str, List[Any]]) -> Dict[str, Any]:
        """分析趋势"""
        trends = {}
        
        # 简化的趋势分析：检查性能是否随测试进行而变化
        for category, results in test_results.items():
            if len(results) < 3:  # 需要至少3个数据点
                continue
            
            # 提取时间序列数据
            if category == 'timeline_accuracy':
                values = [getattr(r, 'success_rate', 0) for r in results]
            elif category == 'plot_understanding':
                values = [getattr(r, 'overall_understanding_score', 0) for r in results]
            elif category == 'viral_generation':
                values = [getattr(r, 'overall_viral_score', 0) for r in results]
            else:
                values = [getattr(r, 'parsing_accuracy', 0) for r in results]
            
            # 计算趋势
            x = list(range(len(values)))
            if len(x) > 1 and len(values) > 1:
                correlation = np.corrcoef(x, values)[0, 1] if not np.isnan(np.corrcoef(x, values)[0, 1]) else 0
                trends[category] = {
                    'trend_direction': 'improving' if correlation > 0.1 else 'declining' if correlation < -0.1 else 'stable',
                    'correlation_coefficient': correlation,
                    'first_value': values[0],
                    'last_value': values[-1],
                    'change_percentage': ((values[-1] - values[0]) / values[0] * 100) if values[0] != 0 else 0
                }
        
        return trends
    
    def _analyze_correlations(self, test_results: Dict[str, List[Any]]) -> Dict[str, Any]:
        """分析相关性"""
        correlations = {}
        
        # 分析处理时间与性能的相关性
        categories = list(test_results.keys())
        
        for category in categories:
            results = test_results[category]
            if len(results) < 3:
                continue
            
            processing_times = [getattr(r, 'processing_time', 0) for r in results if hasattr(r, 'processing_time')]
            
            if category == 'timeline_accuracy':
                performance_scores = [getattr(r, 'success_rate', 0) for r in results]
            elif category == 'plot_understanding':
                performance_scores = [getattr(r, 'overall_understanding_score', 0) for r in results]
            else:
                performance_scores = [1.0] * len(results)  # 默认值
            
            if len(processing_times) == len(performance_scores) and len(processing_times) > 2:
                try:
                    correlation = np.corrcoef(processing_times, performance_scores)[0, 1]
                    if not np.isnan(correlation):
                        correlations[f'{category}_time_vs_performance'] = {
                            'correlation': correlation,
                            'interpretation': self._interpret_correlation(correlation)
                        }
                except Exception:
                    pass
        
        return correlations
    
    def _interpret_correlation(self, correlation: float) -> str:
        """解释相关性系数"""
        abs_corr = abs(correlation)
        if abs_corr >= 0.7:
            strength = "强"
        elif abs_corr >= 0.3:
            strength = "中等"
        else:
            strength = "弱"
        
        direction = "正" if correlation > 0 else "负"
        return f"{strength}{direction}相关"
    
    def _analyze_failures(self, test_results: Dict[str, List[Any]]) -> Dict[str, Any]:
        """分析失败情况"""
        failures = {}
        
        for category, results in test_results.items():
            category_failures = {
                'total_failures': 0,
                'failure_types': {},
                'common_issues': []
            }
            
            for result in results:
                # 检查是否为失败的测试
                is_failure = False
                
                if category == 'timeline_accuracy':
                    is_failure = getattr(result, 'success_rate', 1.0) < 0.95
                elif category == 'plot_understanding':
                    is_failure = getattr(result, 'overall_understanding_score', 1.0) < 0.85
                elif category == 'viral_generation':
                    is_failure = getattr(result, 'overall_viral_score', 1.0) < 0.75
                elif category == 'multilingual_support':
                    is_failure = not getattr(result, 'parsing_success', True)
                
                if is_failure:
                    category_failures['total_failures'] += 1
                    
                    # 分析失败原因
                    if hasattr(result, 'detailed_errors') and result.detailed_errors:
                        for error in result.detailed_errors:
                            error_type = error.get('error_type', 'unknown')
                            if error_type not in category_failures['failure_types']:
                                category_failures['failure_types'][error_type] = 0
                            category_failures['failure_types'][error_type] += 1
            
            # 识别常见问题
            if category_failures['failure_types']:
                sorted_failures = sorted(category_failures['failure_types'].items(), key=lambda x: x[1], reverse=True)
                category_failures['common_issues'] = [f"{error_type} ({count}次)" for error_type, count in sorted_failures[:3]]
            
            failures[category] = category_failures
        
        return failures
    
    def _generate_recommendations(self, test_results: Dict[str, List[Any]], 
                                performance_metrics: Dict[str, Any]) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        # 基于测试结果生成建议
        for category, results in test_results.items():
            if not results:
                continue
            
            category_summary = self._analyze_category_results(category, results)
            
            if category_summary['success_rate'] < 0.8:
                recommendations.append(f"{category}模块成功率较低({category_summary['success_rate']:.1%})，建议重点优化")
            
            if category == 'timeline_accuracy':
                avg_error = category_summary['key_metrics'].get('average_error', 0)
                if avg_error > 0.3:
                    recommendations.append(f"时间轴精度需要改进，当前平均误差{avg_error:.2f}秒，建议优化对齐算法")
            
            elif category == 'plot_understanding':
                char_accuracy = category_summary['key_metrics'].get('character_recognition_avg', 0)
                if char_accuracy < 0.8:
                    recommendations.append(f"角色识别准确率偏低({char_accuracy:.1%})，建议改进角色提取算法")
            
            elif category == 'viral_generation':
                compression_ratio = category_summary['key_metrics'].get('compression_ratio_avg', 0)
                if compression_ratio < 0.3 or compression_ratio > 0.7:
                    recommendations.append(f"压缩比不在理想范围({compression_ratio:.1%})，建议调整压缩策略")
        
        # 基于性能指标生成建议
        for category, times in performance_metrics.get('processing_times', {}).items():
            if times.get('average', 0) > 60:  # 超过1分钟
                recommendations.append(f"{category}处理时间过长({times['average']:.1f}秒)，建议优化算法效率")
        
        for category, memory in performance_metrics.get('memory_usage', {}).items():
            if memory.get('peak', 0) > 3500:  # 超过3.5GB
                recommendations.append(f"{category}内存使用过高({memory['peak']:.0f}MB)，建议优化内存管理")
        
        # 如果没有发现问题，给出积极建议
        if not recommendations:
            recommendations.append("所有测试指标均达到预期标准，系统运行良好")
            recommendations.append("建议继续监控系统性能，定期进行回归测试")
        
        return recommendations
    
    def _save_report(self, report: TestReport):
        """保存报告到文件"""
        # 保存JSON格式
        if 'json' in self.output_formats:
            json_file = self.output_dir / f"{report.report_id}.json"
            self._save_json_report(report, json_file)
        
        # 保存HTML格式
        if 'html' in self.output_formats:
            html_file = self.output_dir / f"{report.report_id}.html"
            self._save_html_report(report, html_file)
        
        # 保存PDF格式（如果配置了）
        if 'pdf' in self.output_formats:
            pdf_file = self.output_dir / f"{report.report_id}.pdf"
            self._save_pdf_report(report, pdf_file)
    
    def _save_json_report(self, report: TestReport, file_path: Path):
        """保存JSON格式报告"""
        try:
            report_data = {
                'report_id': report.report_id,
                'generated_at': report.generated_at.isoformat(),
                'test_summary': report.test_summary,
                'performance_metrics': report.performance_metrics,
                'recommendations': report.recommendations,
                'detailed_analysis': report.detailed_analysis,
                'test_results': {
                    'timeline_accuracy': [self._serialize_result(r) for r in report.timeline_accuracy_results],
                    'plot_understanding': [self._serialize_result(r) for r in report.plot_understanding_results],
                    'viral_generation': [self._serialize_result(r) for r in report.viral_generation_results],
                    'multilingual_support': [self._serialize_result(r) for r in report.multilingual_results]
                }
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2, default=str)
            
            self.logger.info(f"JSON报告已保存: {file_path}")
            
        except Exception as e:
            self.logger.error(f"保存JSON报告失败: {str(e)}")
    
    def _save_html_report(self, report: TestReport, file_path: Path):
        """保存HTML格式报告"""
        try:
            html_content = self._generate_html_content(report)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            self.logger.info(f"HTML报告已保存: {file_path}")
            
        except Exception as e:
            self.logger.error(f"保存HTML报告失败: {str(e)}")
    
    def _save_pdf_report(self, report: TestReport, file_path: Path):
        """保存PDF格式报告"""
        try:
            # 这里需要实现PDF生成逻辑
            # 可以使用reportlab或者将HTML转换为PDF
            self.logger.info(f"PDF报告功能待实现: {file_path}")
            
        except Exception as e:
            self.logger.error(f"保存PDF报告失败: {str(e)}")
    
    def _serialize_result(self, result) -> Dict[str, Any]:
        """序列化测试结果对象"""
        if hasattr(result, '__dict__'):
            return {k: v for k, v in result.__dict__.items() if not k.startswith('_')}
        else:
            return str(result)
    
    def _generate_html_content(self, report: TestReport) -> str:
        """生成HTML报告内容"""
        html_template = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VisionAI-ClipsMaster 核心功能测试报告</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }
        .header { background: #f4f4f4; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
        .summary { background: #e8f5e8; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
        .section { margin-bottom: 30px; }
        .metric { display: inline-block; margin: 10px; padding: 10px; background: #f9f9f9; border-radius: 3px; }
        .success { color: #28a745; }
        .warning { color: #ffc107; }
        .error { color: #dc3545; }
        table { width: 100%; border-collapse: collapse; margin: 10px 0; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        .recommendations { background: #fff3cd; padding: 15px; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>VisionAI-ClipsMaster 核心功能测试报告</h1>
        <p><strong>报告ID:</strong> {report_id}</p>
        <p><strong>生成时间:</strong> {generated_at}</p>
    </div>
    
    <div class="summary">
        <h2>测试汇总</h2>
        <div class="metric">
            <strong>总体成功率:</strong> 
            <span class="{overall_success_class}">{overall_success_rate:.1%}</span>
        </div>
        <div class="metric">
            <strong>测试类别:</strong> {total_categories}
        </div>
        <div class="metric">
            <strong>测试用例:</strong> {total_test_cases}
        </div>
    </div>
    
    <div class="section">
        <h2>各模块测试结果</h2>
        {category_results_html}
    </div>
    
    <div class="section">
        <h2>性能指标</h2>
        {performance_metrics_html}
    </div>
    
    <div class="recommendations">
        <h2>改进建议</h2>
        <ul>
            {recommendations_html}
        </ul>
    </div>
</body>
</html>
        """
        
        # 填充模板数据
        overall_success_rate = report.test_summary.get('overall_success_rate', 0)
        overall_success_class = 'success' if overall_success_rate >= 0.9 else 'warning' if overall_success_rate >= 0.7 else 'error'
        
        category_results_html = self._generate_category_results_html(report.test_summary.get('category_summaries', {}))
        performance_metrics_html = self._generate_performance_metrics_html(report.performance_metrics)
        recommendations_html = '\n'.join([f'<li>{rec}</li>' for rec in report.recommendations])
        
        return html_template.format(
            report_id=report.report_id,
            generated_at=report.generated_at.strftime('%Y-%m-%d %H:%M:%S'),
            overall_success_rate=overall_success_rate,
            overall_success_class=overall_success_class,
            total_categories=report.test_summary.get('total_test_categories', 0),
            total_test_cases=report.test_summary.get('total_test_cases', 0),
            category_results_html=category_results_html,
            performance_metrics_html=performance_metrics_html,
            recommendations_html=recommendations_html
        )
    
    def _generate_category_results_html(self, category_summaries: Dict[str, Any]) -> str:
        """生成类别结果HTML"""
        html = "<table><tr><th>测试类别</th><th>成功率</th><th>通过/总数</th><th>平均评分</th></tr>"
        
        for category, summary in category_summaries.items():
            success_rate = summary.get('success_rate', 0)
            success_class = 'success' if success_rate >= 0.9 else 'warning' if success_rate >= 0.7 else 'error'
            
            html += f"""
            <tr>
                <td>{category}</td>
                <td class="{success_class}">{success_rate:.1%}</td>
                <td>{summary.get('passed_tests', 0)}/{summary.get('total_tests', 0)}</td>
                <td>{summary.get('average_score', 0):.3f}</td>
            </tr>
            """
        
        html += "</table>"
        return html
    
    def _generate_performance_metrics_html(self, performance_metrics: Dict[str, Any]) -> str:
        """生成性能指标HTML"""
        html = "<h3>处理时间</h3><table><tr><th>类别</th><th>平均时间(秒)</th><th>最大时间(秒)</th></tr>"
        
        for category, times in performance_metrics.get('processing_times', {}).items():
            html += f"""
            <tr>
                <td>{category}</td>
                <td>{times.get('average', 0):.2f}</td>
                <td>{times.get('max', 0):.2f}</td>
            </tr>
            """
        
        html += "</table>"
        
        html += "<h3>内存使用</h3><table><tr><th>类别</th><th>平均内存(MB)</th><th>峰值内存(MB)</th></tr>"
        
        for category, memory in performance_metrics.get('memory_usage', {}).items():
            html += f"""
            <tr>
                <td>{category}</td>
                <td>{memory.get('average', 0):.0f}</td>
                <td>{memory.get('peak', 0):.0f}</td>
            </tr>
            """
        
        html += "</table>"
        return html


if __name__ == "__main__":
    # 测试报告生成器
    generator = ComprehensiveReportGenerator()
    
    # 模拟测试结果
    mock_results = {
        'timeline_accuracy': [],
        'plot_understanding': [],
        'viral_generation': [],
        'multilingual_support': []
    }
    
    # 生成报告
    report = generator.generate_comprehensive_report(mock_results)
    print(f"测试报告已生成: {report.report_id}")
