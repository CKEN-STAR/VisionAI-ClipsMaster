#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 真实世界测试报告生成器

此模块生成详细的真实世界端到端测试报告，包括性能指标、
质量评估、用户体验分析、问题诊断和改进建议。
"""

import os
import sys
import json
import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
import matplotlib.pyplot as plt
import seaborn as sns

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from src.utils.log_handler import LogHandler

logger = logging.getLogger(__name__)


@dataclass
class TestSummary:
    """测试摘要"""
    total_tests: int
    successful_tests: int
    failed_tests: int
    success_rate: float
    total_duration: float
    average_processing_speed: float
    peak_memory_usage_mb: float
    critical_errors: int
    warnings: int


@dataclass
class PerformanceMetrics:
    """性能指标"""
    processing_speed_multiplier: float
    memory_usage_mb: float
    cpu_usage_percent: float
    disk_io_mbps: float
    response_time_seconds: float
    throughput_videos_per_hour: float


@dataclass
class QualityMetrics:
    """质量指标"""
    ai_understanding_accuracy: float
    viral_generation_quality: float
    cutting_precision_seconds: float
    timeline_accuracy: float
    jianying_compatibility_score: float
    user_satisfaction_score: float


class RealWorldReportGenerator:
    """真实世界测试报告生成器"""
    
    def __init__(self, config_path: str = None):
        """初始化报告生成器"""
        self.config = self._load_config(config_path)
        
        # 设置日志
        self.logger = LogHandler.get_logger(
            name=__name__,
            level=self.config.get('test_environment', {}).get('log_level', 'INFO')
        )
        
        # 报告配置
        self.report_config = self.config.get('reporting', {})
        self.output_formats = self.report_config.get('formats', ['html', 'json'])
        
        # 创建报告输出目录
        self.reports_dir = Path(self.config.get('file_paths', {}).get('output', {}).get('reports_dir', 'tests/reports/real_world_validation'))
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        # 设置图表样式
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """加载配置"""
        if config_path is None:
            config_path = "tests/real_world_validation/real_world_config.yaml"
        
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
            'reporting': {'formats': ['html', 'json']},
            'file_paths': {'output': {'reports_dir': 'tests/reports/real_world_validation'}}
        }
    
    def generate_comprehensive_report(self, test_results: List[Dict[str, Any]], 
                                    test_metadata: Dict[str, Any] = None) -> Dict[str, str]:
        """
        生成综合测试报告
        
        Args:
            test_results: 测试结果列表
            test_metadata: 测试元数据
            
        Returns:
            Dict[str, str]: 生成的报告文件路径
        """
        report_timestamp = int(time.time())
        report_id = f"real_world_report_{report_timestamp}"
        
        self.logger.info(f"开始生成综合测试报告: {report_id}")
        
        try:
            # 分析测试结果
            analysis_results = self._analyze_test_results(test_results)
            
            # 生成报告数据
            report_data = self._compile_report_data(analysis_results, test_metadata, report_id)
            
            # 生成图表
            charts_data = self._generate_charts(analysis_results, report_id)
            
            # 生成不同格式的报告
            generated_files = {}
            
            if 'html' in self.output_formats:
                html_file = self._generate_html_report(report_data, charts_data, report_id)
                generated_files['html'] = html_file
            
            if 'json' in self.output_formats:
                json_file = self._generate_json_report(report_data, report_id)
                generated_files['json'] = json_file
            
            if 'pdf' in self.output_formats:
                pdf_file = self._generate_pdf_report(report_data, charts_data, report_id)
                generated_files['pdf'] = pdf_file
            
            self.logger.info(f"综合测试报告生成完成: {report_id}")
            
            return generated_files
            
        except Exception as e:
            self.logger.error(f"生成综合测试报告失败: {str(e)}")
            raise
    
    def _analyze_test_results(self, test_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析测试结果"""
        if not test_results:
            return self._get_empty_analysis()
        
        # 计算测试摘要
        test_summary = self._calculate_test_summary(test_results)
        
        # 计算性能指标
        performance_metrics = self._calculate_performance_metrics(test_results)
        
        # 计算质量指标
        quality_metrics = self._calculate_quality_metrics(test_results)
        
        # 分析错误和问题
        error_analysis = self._analyze_errors_and_issues(test_results)
        
        # 性能趋势分析
        performance_trends = self._analyze_performance_trends(test_results)
        
        # 用户体验评估
        user_experience = self._evaluate_user_experience(test_results)
        
        # 生成改进建议
        recommendations = self._generate_recommendations(test_results, performance_metrics, quality_metrics)
        
        return {
            'test_summary': test_summary,
            'performance_metrics': performance_metrics,
            'quality_metrics': quality_metrics,
            'error_analysis': error_analysis,
            'performance_trends': performance_trends,
            'user_experience': user_experience,
            'recommendations': recommendations
        }
    
    def _calculate_test_summary(self, test_results: List[Dict[str, Any]]) -> TestSummary:
        """计算测试摘要"""
        total_tests = len(test_results)
        successful_tests = sum(1 for result in test_results if result.get('success', False))
        failed_tests = total_tests - successful_tests
        success_rate = successful_tests / total_tests if total_tests > 0 else 0
        
        total_duration = sum(result.get('total_duration', 0) for result in test_results)
        
        # 计算平均处理速度
        processing_speeds = []
        for result in test_results:
            if 'overall_performance' in result:
                speed = result['overall_performance'].get('processing_speed_multiplier', 0)
                if speed > 0:
                    processing_speeds.append(speed)
        
        average_processing_speed = sum(processing_speeds) / len(processing_speeds) if processing_speeds else 0
        
        # 计算峰值内存使用
        memory_usages = []
        for result in test_results:
            if 'overall_performance' in result:
                memory = result['overall_performance'].get('peak_memory_usage_mb', 0)
                if memory > 0:
                    memory_usages.append(memory)
        
        peak_memory_usage = max(memory_usages) if memory_usages else 0
        
        # 统计错误和警告
        critical_errors = sum(len(result.get('error_messages', [])) for result in test_results)
        warnings = sum(len(result.get('warnings', [])) for result in test_results)
        
        return TestSummary(
            total_tests=total_tests,
            successful_tests=successful_tests,
            failed_tests=failed_tests,
            success_rate=success_rate,
            total_duration=total_duration,
            average_processing_speed=average_processing_speed,
            peak_memory_usage_mb=peak_memory_usage,
            critical_errors=critical_errors,
            warnings=warnings
        )
    
    def _calculate_performance_metrics(self, test_results: List[Dict[str, Any]]) -> PerformanceMetrics:
        """计算性能指标"""
        # 收集性能数据
        processing_speeds = []
        memory_usages = []
        cpu_usages = []
        response_times = []
        
        for result in test_results:
            perf_data = result.get('overall_performance', {})
            
            if 'processing_speed_multiplier' in perf_data:
                processing_speeds.append(perf_data['processing_speed_multiplier'])
            
            if 'peak_memory_usage_mb' in perf_data:
                memory_usages.append(perf_data['peak_memory_usage_mb'])
            
            if 'average_cpu_usage' in perf_data:
                cpu_usages.append(perf_data['average_cpu_usage'])
            
            if 'total_duration' in result:
                response_times.append(result['total_duration'])
        
        # 计算平均值
        avg_processing_speed = sum(processing_speeds) / len(processing_speeds) if processing_speeds else 0
        avg_memory_usage = sum(memory_usages) / len(memory_usages) if memory_usages else 0
        avg_cpu_usage = sum(cpu_usages) / len(cpu_usages) if cpu_usages else 0
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        # 计算吞吐量（视频/小时）
        total_videos = len(test_results)
        total_time_hours = sum(response_times) / 3600 if response_times else 1
        throughput = total_videos / total_time_hours
        
        return PerformanceMetrics(
            processing_speed_multiplier=avg_processing_speed,
            memory_usage_mb=avg_memory_usage,
            cpu_usage_percent=avg_cpu_usage,
            disk_io_mbps=0,  # 需要从详细数据中提取
            response_time_seconds=avg_response_time,
            throughput_videos_per_hour=throughput
        )
    
    def _calculate_quality_metrics(self, test_results: List[Dict[str, Any]]) -> QualityMetrics:
        """计算质量指标"""
        # 收集质量数据
        ai_accuracies = []
        viral_scores = []
        cutting_precisions = []
        timeline_accuracies = []
        compatibility_scores = []
        user_scores = []
        
        for result in test_results:
            quality_data = result.get('quality_metrics', {})
            
            if 'ai_confidence' in quality_data:
                ai_accuracies.append(quality_data['ai_confidence'])
            
            if 'viral_score' in quality_data:
                viral_scores.append(quality_data['viral_score'])
            
            if 'cutting_accuracy' in quality_data:
                cutting_precisions.append(1.0 - quality_data['cutting_accuracy'])  # 转换为精度
            
            if 'overall_quality_score' in quality_data:
                timeline_accuracies.append(quality_data['overall_quality_score'])
            
            if 'compatibility_score' in result:
                compatibility_scores.append(result['compatibility_score'])
            
            if 'user_experience_score' in result:
                user_scores.append(result['user_experience_score'])
        
        # 计算平均值
        avg_ai_accuracy = sum(ai_accuracies) / len(ai_accuracies) if ai_accuracies else 0
        avg_viral_quality = sum(viral_scores) / len(viral_scores) if viral_scores else 0
        avg_cutting_precision = sum(cutting_precisions) / len(cutting_precisions) if cutting_precisions else 0
        avg_timeline_accuracy = sum(timeline_accuracies) / len(timeline_accuracies) if timeline_accuracies else 0
        avg_compatibility = sum(compatibility_scores) / len(compatibility_scores) if compatibility_scores else 0
        avg_user_satisfaction = sum(user_scores) / len(user_scores) if user_scores else 0
        
        return QualityMetrics(
            ai_understanding_accuracy=avg_ai_accuracy,
            viral_generation_quality=avg_viral_quality,
            cutting_precision_seconds=avg_cutting_precision,
            timeline_accuracy=avg_timeline_accuracy,
            jianying_compatibility_score=avg_compatibility,
            user_satisfaction_score=avg_user_satisfaction
        )
    
    def _analyze_errors_and_issues(self, test_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析错误和问题"""
        error_categories = {}
        warning_categories = {}
        failure_patterns = []
        
        for result in test_results:
            # 分析错误
            for error in result.get('error_messages', []):
                category = self._categorize_error(error)
                error_categories[category] = error_categories.get(category, 0) + 1
            
            # 分析警告
            for warning in result.get('warnings', []):
                category = self._categorize_warning(warning)
                warning_categories[category] = warning_categories.get(category, 0) + 1
            
            # 分析失败模式
            if not result.get('success', False):
                failure_patterns.append({
                    'test_type': result.get('test_name', 'unknown'),
                    'error_count': len(result.get('error_messages', [])),
                    'primary_error': result.get('error_messages', ['Unknown'])[0] if result.get('error_messages') else 'Unknown'
                })
        
        return {
            'error_categories': error_categories,
            'warning_categories': warning_categories,
            'failure_patterns': failure_patterns,
            'total_errors': sum(error_categories.values()),
            'total_warnings': sum(warning_categories.values())
        }
    
    def _analyze_performance_trends(self, test_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析性能趋势"""
        # 按时间排序的性能数据
        performance_timeline = []
        
        for i, result in enumerate(test_results):
            perf_data = result.get('overall_performance', {})
            performance_timeline.append({
                'test_index': i,
                'processing_speed': perf_data.get('processing_speed_multiplier', 0),
                'memory_usage': perf_data.get('peak_memory_usage_mb', 0),
                'cpu_usage': perf_data.get('average_cpu_usage', 0),
                'duration': result.get('total_duration', 0)
            })
        
        # 计算趋势
        trends = {
            'performance_degradation': self._detect_performance_degradation(performance_timeline),
            'memory_leak_trend': self._detect_memory_leak_trend(performance_timeline),
            'processing_speed_trend': self._calculate_trend(performance_timeline, 'processing_speed'),
            'stability_trend': self._calculate_stability_trend(test_results)
        }
        
        return {
            'performance_timeline': performance_timeline,
            'trends': trends
        }
    
    def _evaluate_user_experience(self, test_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """评估用户体验"""
        user_experience_scores = []
        response_times = []
        success_rates_by_type = {}
        
        for result in test_results:
            if 'user_experience_score' in result:
                user_experience_scores.append(result['user_experience_score'])
            
            if 'total_duration' in result:
                response_times.append(result['total_duration'])
            
            test_type = result.get('test_name', 'unknown')
            if test_type not in success_rates_by_type:
                success_rates_by_type[test_type] = {'total': 0, 'successful': 0}
            
            success_rates_by_type[test_type]['total'] += 1
            if result.get('success', False):
                success_rates_by_type[test_type]['successful'] += 1
        
        # 计算各类型成功率
        for test_type in success_rates_by_type:
            data = success_rates_by_type[test_type]
            data['success_rate'] = data['successful'] / data['total'] if data['total'] > 0 else 0
        
        return {
            'overall_user_experience_score': sum(user_experience_scores) / len(user_experience_scores) if user_experience_scores else 0,
            'average_response_time': sum(response_times) / len(response_times) if response_times else 0,
            'success_rates_by_type': success_rates_by_type,
            'user_satisfaction_level': self._determine_satisfaction_level(user_experience_scores)
        }
    
    def _generate_recommendations(self, test_results: List[Dict[str, Any]], 
                                performance_metrics: PerformanceMetrics,
                                quality_metrics: QualityMetrics) -> List[Dict[str, Any]]:
        """生成改进建议"""
        recommendations = []
        
        # 性能优化建议
        if performance_metrics.processing_speed_multiplier < 2.0:
            recommendations.append({
                'category': 'performance',
                'priority': 'high',
                'title': '处理速度优化',
                'description': f'当前处理速度为{performance_metrics.processing_speed_multiplier:.1f}x，低于2x目标',
                'suggestions': [
                    '优化AI模型推理速度',
                    '实现并行处理',
                    '优化视频编解码流程',
                    '使用GPU加速'
                ]
            })
        
        # 内存使用优化建议
        if performance_metrics.memory_usage_mb > 3500:
            recommendations.append({
                'category': 'memory',
                'priority': 'medium',
                'title': '内存使用优化',
                'description': f'峰值内存使用{performance_metrics.memory_usage_mb:.0f}MB，接近4GB限制',
                'suggestions': [
                    '实现内存池管理',
                    '优化大文件处理策略',
                    '及时释放临时资源',
                    '分块处理长视频'
                ]
            })
        
        # 质量改进建议
        if quality_metrics.ai_understanding_accuracy < 0.85:
            recommendations.append({
                'category': 'quality',
                'priority': 'high',
                'title': 'AI理解准确性提升',
                'description': f'AI理解准确性{quality_metrics.ai_understanding_accuracy:.2%}，低于85%目标',
                'suggestions': [
                    '优化模型训练数据',
                    '调整模型参数',
                    '增加多模态分析',
                    '实现模型集成'
                ]
            })
        
        # 兼容性改进建议
        if quality_metrics.jianying_compatibility_score < 0.95:
            recommendations.append({
                'category': 'compatibility',
                'priority': 'medium',
                'title': '剪映兼容性改进',
                'description': f'剪映兼容性评分{quality_metrics.jianying_compatibility_score:.2%}，需要提升',
                'suggestions': [
                    '更新剪映格式支持',
                    '优化文件路径处理',
                    '完善元数据生成',
                    '增加版本兼容性测试'
                ]
            })
        
        return recommendations
    
    def _generate_charts(self, analysis_results: Dict[str, Any], report_id: str) -> Dict[str, str]:
        """生成图表"""
        charts_dir = self.reports_dir / f"{report_id}_charts"
        charts_dir.mkdir(exist_ok=True)
        
        charts_data = {}
        
        try:
            # 1. 测试成功率饼图
            success_chart = self._create_success_rate_chart(analysis_results['test_summary'], charts_dir)
            charts_data['success_rate'] = success_chart
            
            # 2. 性能指标雷达图
            performance_chart = self._create_performance_radar_chart(analysis_results['performance_metrics'], charts_dir)
            charts_data['performance_radar'] = performance_chart
            
            # 3. 质量指标柱状图
            quality_chart = self._create_quality_metrics_chart(analysis_results['quality_metrics'], charts_dir)
            charts_data['quality_metrics'] = quality_chart
            
            # 4. 性能趋势线图
            trends_chart = self._create_performance_trends_chart(analysis_results['performance_trends'], charts_dir)
            charts_data['performance_trends'] = trends_chart
            
            # 5. 错误分布图
            error_chart = self._create_error_distribution_chart(analysis_results['error_analysis'], charts_dir)
            charts_data['error_distribution'] = error_chart
            
        except Exception as e:
            self.logger.warning(f"生成图表时出现错误: {str(e)}")
        
        return charts_data
    
    def _create_success_rate_chart(self, test_summary: TestSummary, charts_dir: Path) -> str:
        """创建测试成功率饼图"""
        try:
            fig, ax = plt.subplots(figsize=(8, 6))
            
            labels = ['成功', '失败']
            sizes = [test_summary.successful_tests, test_summary.failed_tests]
            colors = ['#2ecc71', '#e74c3c']
            
            ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
            ax.set_title('测试成功率分布', fontsize=16, fontweight='bold')
            
            chart_path = charts_dir / 'success_rate.png'
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            return str(chart_path)
            
        except Exception as e:
            self.logger.error(f"创建成功率图表失败: {str(e)}")
            return ""
    
    def _create_performance_radar_chart(self, performance_metrics: PerformanceMetrics, charts_dir: Path) -> str:
        """创建性能指标雷达图"""
        try:
            # 简化的雷达图实现
            fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection='polar'))
            
            categories = ['处理速度', '内存使用', 'CPU使用', '响应时间', '吞吐量']
            values = [
                min(performance_metrics.processing_speed_multiplier / 3.0, 1.0),  # 标准化到0-1
                1.0 - min(performance_metrics.memory_usage_mb / 4096, 1.0),  # 内存使用越低越好
                1.0 - min(performance_metrics.cpu_usage_percent / 100, 1.0),  # CPU使用越低越好
                1.0 - min(performance_metrics.response_time_seconds / 300, 1.0),  # 响应时间越短越好
                min(performance_metrics.throughput_videos_per_hour / 10, 1.0)  # 吞吐量标准化
            ]
            
            angles = [i * 2 * 3.14159 / len(categories) for i in range(len(categories))]
            angles += angles[:1]  # 闭合图形
            values += values[:1]
            
            ax.plot(angles, values, 'o-', linewidth=2, label='当前性能')
            ax.fill(angles, values, alpha=0.25)
            ax.set_xticks(angles[:-1])
            ax.set_xticklabels(categories)
            ax.set_ylim(0, 1)
            ax.set_title('性能指标雷达图', fontsize=16, fontweight='bold', pad=20)
            
            chart_path = charts_dir / 'performance_radar.png'
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            return str(chart_path)
            
        except Exception as e:
            self.logger.error(f"创建性能雷达图失败: {str(e)}")
            return ""
    
    def _create_quality_metrics_chart(self, quality_metrics: QualityMetrics, charts_dir: Path) -> str:
        """创建质量指标柱状图"""
        try:
            fig, ax = plt.subplots(figsize=(10, 6))
            
            metrics = ['AI理解准确性', '爆款生成质量', '剪切精度', '时间轴准确性', '剪映兼容性', '用户满意度']
            values = [
                quality_metrics.ai_understanding_accuracy,
                quality_metrics.viral_generation_quality,
                1.0 - quality_metrics.cutting_precision_seconds,  # 转换为正向指标
                quality_metrics.timeline_accuracy,
                quality_metrics.jianying_compatibility_score,
                quality_metrics.user_satisfaction_score
            ]
            
            bars = ax.bar(metrics, values, color=['#3498db', '#2ecc71', '#f39c12', '#9b59b6', '#e74c3c', '#1abc9c'])
            
            # 添加数值标签
            for bar, value in zip(bars, values):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                       f'{value:.2%}', ha='center', va='bottom')
            
            ax.set_ylabel('评分')
            ax.set_title('质量指标评估', fontsize=16, fontweight='bold')
            ax.set_ylim(0, 1.1)
            plt.xticks(rotation=45, ha='right')
            
            chart_path = charts_dir / 'quality_metrics.png'
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            return str(chart_path)
            
        except Exception as e:
            self.logger.error(f"创建质量指标图表失败: {str(e)}")
            return ""
    
    def _create_performance_trends_chart(self, performance_trends: Dict[str, Any], charts_dir: Path) -> str:
        """创建性能趋势线图"""
        try:
            timeline = performance_trends.get('performance_timeline', [])
            if not timeline:
                return ""
            
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 8))
            
            test_indices = [item['test_index'] for item in timeline]
            
            # 处理速度趋势
            processing_speeds = [item['processing_speed'] for item in timeline]
            ax1.plot(test_indices, processing_speeds, marker='o')
            ax1.set_title('处理速度趋势')
            ax1.set_ylabel('速度倍数')
            
            # 内存使用趋势
            memory_usages = [item['memory_usage'] for item in timeline]
            ax2.plot(test_indices, memory_usages, marker='s', color='orange')
            ax2.set_title('内存使用趋势')
            ax2.set_ylabel('内存使用 (MB)')
            
            # CPU使用趋势
            cpu_usages = [item['cpu_usage'] for item in timeline]
            ax3.plot(test_indices, cpu_usages, marker='^', color='green')
            ax3.set_title('CPU使用趋势')
            ax3.set_ylabel('CPU使用率 (%)')
            ax3.set_xlabel('测试序号')
            
            # 响应时间趋势
            durations = [item['duration'] for item in timeline]
            ax4.plot(test_indices, durations, marker='d', color='red')
            ax4.set_title('响应时间趋势')
            ax4.set_ylabel('响应时间 (秒)')
            ax4.set_xlabel('测试序号')
            
            plt.tight_layout()
            
            chart_path = charts_dir / 'performance_trends.png'
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            return str(chart_path)
            
        except Exception as e:
            self.logger.error(f"创建性能趋势图失败: {str(e)}")
            return ""
    
    def _create_error_distribution_chart(self, error_analysis: Dict[str, Any], charts_dir: Path) -> str:
        """创建错误分布图"""
        try:
            error_categories = error_analysis.get('error_categories', {})
            if not error_categories:
                return ""
            
            fig, ax = plt.subplots(figsize=(10, 6))
            
            categories = list(error_categories.keys())
            counts = list(error_categories.values())
            
            bars = ax.bar(categories, counts, color='#e74c3c')
            
            # 添加数值标签
            for bar, count in zip(bars, counts):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                       str(count), ha='center', va='bottom')
            
            ax.set_ylabel('错误数量')
            ax.set_title('错误类型分布', fontsize=16, fontweight='bold')
            plt.xticks(rotation=45, ha='right')
            
            chart_path = charts_dir / 'error_distribution.png'
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            return str(chart_path)
            
        except Exception as e:
            self.logger.error(f"创建错误分布图失败: {str(e)}")
            return ""
    
    def _compile_report_data(self, analysis_results: Dict[str, Any], 
                           test_metadata: Dict[str, Any], report_id: str) -> Dict[str, Any]:
        """编译报告数据"""
        return {
            'report_id': report_id,
            'generation_time': time.time(),
            'test_metadata': test_metadata or {},
            'analysis_results': analysis_results,
            'system_info': self._get_system_info(),
            'configuration': self._get_test_configuration()
        }
    
    def _generate_html_report(self, report_data: Dict[str, Any], 
                            charts_data: Dict[str, str], report_id: str) -> str:
        """生成HTML报告"""
        try:
            html_template = self._get_html_template()
            
            # 替换模板变量
            html_content = html_template.format(
                report_id=report_id,
                generation_time=time.strftime('%Y-%m-%d %H:%M:%S'),
                **report_data['analysis_results']
            )
            
            html_file = self.reports_dir / f"{report_id}.html"
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return str(html_file)
            
        except Exception as e:
            self.logger.error(f"生成HTML报告失败: {str(e)}")
            return ""
    
    def _generate_json_report(self, report_data: Dict[str, Any], report_id: str) -> str:
        """生成JSON报告"""
        try:
            json_file = self.reports_dir / f"{report_id}.json"
            
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2, default=str)
            
            return str(json_file)
            
        except Exception as e:
            self.logger.error(f"生成JSON报告失败: {str(e)}")
            return ""
    
    def _get_empty_analysis(self) -> Dict[str, Any]:
        """获取空分析结果"""
        return {
            'test_summary': TestSummary(0, 0, 0, 0, 0, 0, 0, 0, 0),
            'performance_metrics': PerformanceMetrics(0, 0, 0, 0, 0, 0),
            'quality_metrics': QualityMetrics(0, 0, 0, 0, 0, 0),
            'error_analysis': {'error_categories': {}, 'warning_categories': {}, 'failure_patterns': []},
            'performance_trends': {'performance_timeline': [], 'trends': {}},
            'user_experience': {'overall_user_experience_score': 0},
            'recommendations': []
        }
    
    def _categorize_error(self, error: str) -> str:
        """分类错误"""
        error_lower = error.lower()
        
        if 'memory' in error_lower or 'oom' in error_lower:
            return '内存相关'
        elif 'timeout' in error_lower or 'time' in error_lower:
            return '超时相关'
        elif 'file' in error_lower or 'path' in error_lower:
            return '文件相关'
        elif 'network' in error_lower or 'connection' in error_lower:
            return '网络相关'
        elif 'ai' in error_lower or 'model' in error_lower:
            return 'AI模型相关'
        elif 'video' in error_lower or 'codec' in error_lower:
            return '视频处理相关'
        else:
            return '其他'
    
    def _categorize_warning(self, warning: str) -> str:
        """分类警告"""
        warning_lower = warning.lower()
        
        if 'performance' in warning_lower or 'slow' in warning_lower:
            return '性能警告'
        elif 'quality' in warning_lower:
            return '质量警告'
        elif 'compatibility' in warning_lower:
            return '兼容性警告'
        elif 'memory' in warning_lower:
            return '内存警告'
        else:
            return '其他警告'
    
    def _detect_performance_degradation(self, timeline: List[Dict]) -> bool:
        """检测性能退化"""
        if len(timeline) < 3:
            return False
        
        # 简单的趋势检测
        recent_speeds = [item['processing_speed'] for item in timeline[-3:]]
        early_speeds = [item['processing_speed'] for item in timeline[:3]]
        
        recent_avg = sum(recent_speeds) / len(recent_speeds)
        early_avg = sum(early_speeds) / len(early_speeds)
        
        return recent_avg < early_avg * 0.8  # 性能下降超过20%
    
    def _detect_memory_leak_trend(self, timeline: List[Dict]) -> bool:
        """检测内存泄漏趋势"""
        if len(timeline) < 5:
            return False
        
        memory_values = [item['memory_usage'] for item in timeline]
        
        # 简单的线性趋势检测
        n = len(memory_values)
        x_sum = sum(range(n))
        y_sum = sum(memory_values)
        xy_sum = sum(i * memory_values[i] for i in range(n))
        x2_sum = sum(i * i for i in range(n))
        
        if n * x2_sum - x_sum * x_sum == 0:
            return False
        
        slope = (n * xy_sum - x_sum * y_sum) / (n * x2_sum - x_sum * x_sum)
        
        return slope > 10  # 内存增长超过10MB/测试
    
    def _calculate_trend(self, timeline: List[Dict], metric: str) -> str:
        """计算趋势"""
        if len(timeline) < 3:
            return "数据不足"
        
        values = [item[metric] for item in timeline if metric in item]
        if len(values) < 3:
            return "数据不足"
        
        # 简单的趋势判断
        first_half = values[:len(values)//2]
        second_half = values[len(values)//2:]
        
        first_avg = sum(first_half) / len(first_half)
        second_avg = sum(second_half) / len(second_half)
        
        if second_avg > first_avg * 1.1:
            return "上升"
        elif second_avg < first_avg * 0.9:
            return "下降"
        else:
            return "稳定"
    
    def _calculate_stability_trend(self, test_results: List[Dict]) -> str:
        """计算稳定性趋势"""
        if len(test_results) < 3:
            return "数据不足"
        
        success_rates = []
        window_size = 3
        
        for i in range(len(test_results) - window_size + 1):
            window = test_results[i:i + window_size]
            successes = sum(1 for result in window if result.get('success', False))
            success_rates.append(successes / window_size)
        
        if len(success_rates) < 2:
            return "数据不足"
        
        if success_rates[-1] > success_rates[0] + 0.1:
            return "改善"
        elif success_rates[-1] < success_rates[0] - 0.1:
            return "恶化"
        else:
            return "稳定"
    
    def _determine_satisfaction_level(self, scores: List[float]) -> str:
        """确定满意度水平"""
        if not scores:
            return "无数据"
        
        avg_score = sum(scores) / len(scores)
        
        if avg_score >= 0.9:
            return "非常满意"
        elif avg_score >= 0.8:
            return "满意"
        elif avg_score >= 0.7:
            return "一般"
        elif avg_score >= 0.6:
            return "不满意"
        else:
            return "非常不满意"
    
    def _get_system_info(self) -> Dict[str, Any]:
        """获取系统信息"""
        try:
            import platform
            import psutil
            
            return {
                'platform': platform.platform(),
                'python_version': platform.python_version(),
                'cpu_count': psutil.cpu_count(),
                'memory_total_gb': psutil.virtual_memory().total / (1024**3),
                'disk_total_gb': psutil.disk_usage('/').total / (1024**3)
            }
        except Exception:
            return {'error': '无法获取系统信息'}
    
    def _get_test_configuration(self) -> Dict[str, Any]:
        """获取测试配置"""
        return {
            'config_source': 'real_world_config.yaml',
            'test_environment': self.config.get('test_environment', {}),
            'quality_standards': self.config.get('quality_standards', {}),
            'performance_monitoring': self.config.get('performance_monitoring', {})
        }
    
    def _get_html_template(self) -> str:
        """获取HTML模板"""
        return """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VisionAI-ClipsMaster 真实世界测试报告</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; }}
        .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
        .metric {{ display: inline-block; margin: 10px; padding: 10px; background-color: #e9ecef; border-radius: 3px; }}
        .success {{ color: #28a745; }}
        .warning {{ color: #ffc107; }}
        .error {{ color: #dc3545; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>VisionAI-ClipsMaster 真实世界测试报告</h1>
        <p>报告ID: {report_id}</p>
        <p>生成时间: {generation_time}</p>
    </div>
    
    <div class="section">
        <h2>测试摘要</h2>
        <div class="metric">总测试数: {test_summary.total_tests}</div>
        <div class="metric success">成功: {test_summary.successful_tests}</div>
        <div class="metric error">失败: {test_summary.failed_tests}</div>
        <div class="metric">成功率: {test_summary.success_rate:.2%}</div>
    </div>
    
    <div class="section">
        <h2>性能指标</h2>
        <div class="metric">平均处理速度: {performance_metrics.processing_speed_multiplier:.2f}x</div>
        <div class="metric">峰值内存使用: {performance_metrics.memory_usage_mb:.0f}MB</div>
        <div class="metric">平均响应时间: {performance_metrics.response_time_seconds:.2f}秒</div>
    </div>
    
    <div class="section">
        <h2>质量指标</h2>
        <div class="metric">AI理解准确性: {quality_metrics.ai_understanding_accuracy:.2%}</div>
        <div class="metric">爆款生成质量: {quality_metrics.viral_generation_quality:.2%}</div>
        <div class="metric">剪映兼容性: {quality_metrics.jianying_compatibility_score:.2%}</div>
    </div>
    
    <div class="section">
        <h2>改进建议</h2>
        <ul>
        {recommendations_html}
        </ul>
    </div>
</body>
</html>
        """


if __name__ == "__main__":
    # 示例用法
    generator = RealWorldReportGenerator()
    
    # 模拟测试结果
    mock_results = [
        {
            'test_name': 'complete_pipeline',
            'success': True,
            'total_duration': 120.5,
            'overall_performance': {
                'processing_speed_multiplier': 2.3,
                'peak_memory_usage_mb': 2048,
                'average_cpu_usage': 65
            },
            'quality_metrics': {
                'ai_confidence': 0.87,
                'viral_score': 0.82,
                'cutting_accuracy': 0.05
            },
            'user_experience_score': 0.85,
            'error_messages': [],
            'warnings': ['处理时间略长']
        }
    ]
    
    # 生成报告
    report_files = generator.generate_comprehensive_report(mock_results)
    print(f"生成的报告文件: {report_files}")
