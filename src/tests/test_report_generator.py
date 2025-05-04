"""测试报告生成器

此模块实现全面的测试报告生成功能，包括：
1. 测试结果收集
2. 测试覆盖率分析
3. 性能指标统计
4. 问题分类统计
5. 多语言支持报告
6. 报告导出功能
"""

import os
import json
import time
import datetime
import statistics
from typing import Dict, List, Optional, Any
from loguru import logger
from ..utils.file_handler import FileHandler
from ..utils.config_manager import ConfigManager
from ..core.model_switcher import ModelSwitcher

class TestReportGenerator:
    """测试报告生成器"""
    
    def __init__(self):
        """初始化测试报告生成器"""
        self.file_handler = FileHandler()
        self.config_manager = ConfigManager()
        self.model_switcher = ModelSwitcher()
        
        # 报告配置
        self.report_config = {
            'report_dir': 'reports',
            'report_formats': ['json', 'html', 'md'],
            'languages': ['zh', 'en'],
            'performance_metrics': [
                'execution_time',
                'memory_usage',
                'cpu_usage',
                'model_inference_time'
            ],
            'coverage_metrics': [
                'code_coverage',
                'test_coverage',
                'branch_coverage'
            ]
        }
        
        # 创建报告目录
        os.makedirs(self.report_config['report_dir'], exist_ok=True)
        
        # 初始化报告数据
        self.report_data = {
            'test_summary': {
                'total_tests': 0,
                'passed_tests': 0,
                'failed_tests': 0,
                'skipped_tests': 0,
                'start_time': None,
                'end_time': None,
                'duration': None
            },
            'test_cases': [],
            'performance_metrics': {},
            'coverage_metrics': {},
            'issues': {
                'critical': [],
                'high': [],
                'medium': [],
                'low': []
            },
            'language_support': {
                'zh': {'status': 'supported', 'tests': []},
                'en': {'status': 'configured', 'tests': []}
            }
        }
    
    def collect_test_results(self, test_results: List[Dict[str, Any]]) -> None:
        """收集测试结果
        
        Args:
            test_results: 测试结果列表
        """
        logger.info("开始收集测试结果")
        
        # 更新测试摘要
        self.report_data['test_summary']['total_tests'] = len(test_results)
        self.report_data['test_summary']['passed_tests'] = sum(
            1 for result in test_results if result['status'] == 'passed'
        )
        self.report_data['test_summary']['failed_tests'] = sum(
            1 for result in test_results if result['status'] == 'failed'
        )
        self.report_data['test_summary']['skipped_tests'] = sum(
            1 for result in test_results if result['status'] == 'skipped'
        )
        
        # 记录测试用例详情
        self.report_data['test_cases'] = test_results
        
        # 记录测试时间
        if not self.report_data['test_summary']['start_time']:
            self.report_data['test_summary']['start_time'] = datetime.datetime.now().isoformat()
        self.report_data['test_summary']['end_time'] = datetime.datetime.now().isoformat()
        self.report_data['test_summary']['duration'] = (
            datetime.datetime.fromisoformat(self.report_data['test_summary']['end_time']) -
            datetime.datetime.fromisoformat(self.report_data['test_summary']['start_time'])
        ).total_seconds()
    
    def analyze_performance(self, performance_data: Dict[str, List[float]]) -> None:
        """分析性能指标
        
        Args:
            performance_data: 性能数据
        """
        logger.info("开始分析性能指标")
        
        for metric, values in performance_data.items():
            if metric in self.report_config['performance_metrics']:
                self.report_data['performance_metrics'][metric] = {
                    'min': min(values),
                    'max': max(values),
                    'mean': statistics.mean(values),
                    'median': statistics.median(values),
                    'std_dev': statistics.stdev(values) if len(values) > 1 else 0
                }
    
    def analyze_coverage(self, coverage_data: Dict[str, float]) -> None:
        """分析测试覆盖率
        
        Args:
            coverage_data: 覆盖率数据
        """
        logger.info("开始分析测试覆盖率")
        
        for metric, value in coverage_data.items():
            if metric in self.report_config['coverage_metrics']:
                self.report_data['coverage_metrics'][metric] = value
    
    def classify_issues(self, issues: List[Dict[str, Any]]) -> None:
        """分类问题
        
        Args:
            issues: 问题列表
        """
        logger.info("开始分类问题")
        
        for issue in issues:
            severity = issue.get('severity', 'medium')
            if severity in self.report_data['issues']:
                self.report_data['issues'][severity].append(issue)
    
    def analyze_language_support(self) -> None:
        """分析多语言支持情况"""
        logger.info("开始分析多语言支持情况")
        
        # 分析中文支持
        zh_tests = [
            test for test in self.report_data['test_cases']
            if test.get('language') == 'zh'
        ]
        self.report_data['language_support']['zh']['tests'] = zh_tests
        
        # 分析英文支持（仅配置）
        en_tests = [
            test for test in self.report_data['test_cases']
            if test.get('language') == 'en'
        ]
        self.report_data['language_support']['en']['tests'] = en_tests
    
    def generate_report(self, format: str = 'json') -> str:
        """生成测试报告
        
        Args:
            format: 报告格式
            
        Returns:
            str: 报告文件路径
        """
        logger.info(f"开始生成{format}格式测试报告")
        
        if format not in self.report_config['report_formats']:
            raise ValueError(f"不支持的报告格式: {format}")
        
        # 生成报告文件名
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        report_name = f"test_report_{timestamp}.{format}"
        report_path = os.path.join(self.report_config['report_dir'], report_name)
        
        # 根据格式生成报告
        if format == 'json':
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(self.report_data, f, ensure_ascii=False, indent=2)
        elif format == 'html':
            self._generate_html_report(report_path)
        elif format == 'md':
            self._generate_markdown_report(report_path)
        
        return report_path
    
    def _generate_html_report(self, report_path: str) -> None:
        """生成HTML格式报告
        
        Args:
            report_path: 报告文件路径
        """
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>测试报告</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .summary { background-color: #f5f5f5; padding: 20px; margin-bottom: 20px; }
                .metrics { display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; }
                .issues { margin-top: 20px; }
                .issue { padding: 10px; margin: 5px 0; }
                .critical { background-color: #ffebee; }
                .high { background-color: #fff3e0; }
                .medium { background-color: #fff8e1; }
                .low { background-color: #f1f8e9; }
            </style>
        </head>
        <body>
            <h1>测试报告</h1>
            <div class="summary">
                <h2>测试摘要</h2>
                <p>总测试数: {total_tests}</p>
                <p>通过测试: {passed_tests}</p>
                <p>失败测试: {failed_tests}</p>
                <p>跳过测试: {skipped_tests}</p>
                <p>测试时长: {duration}秒</p>
            </div>
            <div class="metrics">
                <div>
                    <h2>性能指标</h2>
                    {performance_metrics}
                </div>
                <div>
                    <h2>覆盖率指标</h2>
                    {coverage_metrics}
                </div>
            </div>
            <div class="issues">
                <h2>问题统计</h2>
                {issues}
            </div>
            <div>
                <h2>多语言支持</h2>
                {language_support}
            </div>
        </body>
        </html>
        """
        
        # 格式化数据
        performance_metrics = "\n".join(
            f"<p>{metric}: {data}</p>"
            for metric, data in self.report_data['performance_metrics'].items()
        )
        
        coverage_metrics = "\n".join(
            f"<p>{metric}: {value}%</p>"
            for metric, value in self.report_data['coverage_metrics'].items()
        )
        
        issues = "\n".join(
            f'<div class="issue {severity}">{len(issues)}个{severity}级别问题</div>'
            for severity, issues in self.report_data['issues'].items()
        )
        
        language_support = "\n".join(
            f"<p>{lang}: {data['status']} ({len(data['tests'])}个测试)</p>"
            for lang, data in self.report_data['language_support'].items()
        )
        
        # 填充模板
        html_content = html_template.format(
            total_tests=self.report_data['test_summary']['total_tests'],
            passed_tests=self.report_data['test_summary']['passed_tests'],
            failed_tests=self.report_data['test_summary']['failed_tests'],
            skipped_tests=self.report_data['test_summary']['skipped_tests'],
            duration=self.report_data['test_summary']['duration'],
            performance_metrics=performance_metrics,
            coverage_metrics=coverage_metrics,
            issues=issues,
            language_support=language_support
        )
        
        # 写入文件
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def _generate_markdown_report(self, report_path: str) -> None:
        """生成Markdown格式报告
        
        Args:
            report_path: 报告文件路径
        """
        md_content = [
            "# 测试报告",
            "",
            "## 测试摘要",
            f"- 总测试数: {self.report_data['test_summary']['total_tests']}",
            f"- 通过测试: {self.report_data['test_summary']['passed_tests']}",
            f"- 失败测试: {self.report_data['test_summary']['failed_tests']}",
            f"- 跳过测试: {self.report_data['test_summary']['skipped_tests']}",
            f"- 测试时长: {self.report_data['test_summary']['duration']}秒",
            "",
            "## 性能指标",
        ]
        
        # 添加性能指标
        for metric, data in self.report_data['performance_metrics'].items():
            md_content.extend([
                f"### {metric}",
                f"- 最小值: {data['min']}",
                f"- 最大值: {data['max']}",
                f"- 平均值: {data['mean']}",
                f"- 中位数: {data['median']}",
                f"- 标准差: {data['std_dev']}",
                ""
            ])
        
        # 添加覆盖率指标
        md_content.extend([
            "## 覆盖率指标",
        ])
        for metric, value in self.report_data['coverage_metrics'].items():
            md_content.append(f"- {metric}: {value}%")
        md_content.append("")
        
        # 添加问题统计
        md_content.extend([
            "## 问题统计",
        ])
        for severity, issues in self.report_data['issues'].items():
            md_content.append(f"- {severity}级别: {len(issues)}个问题")
        md_content.append("")
        
        # 添加多语言支持
        md_content.extend([
            "## 多语言支持",
        ])
        for lang, data in self.report_data['language_support'].items():
            md_content.append(f"- {lang}: {data['status']} ({len(data['tests'])}个测试)")
        
        # 写入文件
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(md_content)) 