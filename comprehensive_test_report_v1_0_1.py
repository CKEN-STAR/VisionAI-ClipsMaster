#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster v1.0.1 综合测试报告生成器
汇总所有测试结果，生成详细的测试报告
"""

import json
import os
import glob
from datetime import datetime
from pathlib import Path

class ComprehensiveTestReportGenerator:
    def __init__(self):
        self.test_reports = {}
        self.overall_summary = {}
        
    def load_test_reports(self):
        """加载所有测试报告"""
        # 查找所有测试报告文件
        report_patterns = [
            "ui_test_report_v1_0_1_*.json",
            "core_functionality_test_report_v1_0_1_*.json", 
            "performance_monitoring_test_report_v1_0_1_*.json"
        ]
        
        for pattern in report_patterns:
            files = glob.glob(pattern)
            if files:
                # 取最新的报告文件
                latest_file = max(files, key=os.path.getctime)
                try:
                    with open(latest_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        test_type = data.get('test_type', 'Unknown')
                        self.test_reports[test_type] = data
                        print(f"✅ 已加载测试报告: {test_type} ({latest_file})")
                except Exception as e:
                    print(f"❌ 加载测试报告失败: {latest_file} - {e}")
                    
    def calculate_overall_summary(self):
        """计算总体测试摘要"""
        total_tests = 0
        total_passed = 0
        total_failed = 0
        
        test_categories = {}
        
        for test_type, report in self.test_reports.items():
            summary = report.get('summary', {})
            category_total = summary.get('total_tests', 0)
            category_passed = summary.get('passed_tests', 0)
            category_failed = category_total - category_passed
            
            total_tests += category_total
            total_passed += category_passed
            total_failed += category_failed
            
            test_categories[test_type] = {
                'total': category_total,
                'passed': category_passed,
                'failed': category_failed,
                'success_rate': summary.get('success_rate', 0)
            }
            
        overall_success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        self.overall_summary = {
            'total_tests': total_tests,
            'total_passed': total_passed,
            'total_failed': total_failed,
            'overall_success_rate': overall_success_rate,
            'test_categories': test_categories,
            'version': '1.0.1',
            'test_date': datetime.now().isoformat()
        }
        
    def generate_html_report(self):
        """生成HTML格式的测试报告"""
        html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VisionAI-ClipsMaster v1.0.1 综合测试报告</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .header h1 {{ color: #2c3e50; margin-bottom: 10px; }}
        .header .version {{ color: #7f8c8d; font-size: 18px; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .summary-card {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; text-align: center; }}
        .summary-card h3 {{ margin: 0 0 10px 0; font-size: 14px; opacity: 0.9; }}
        .summary-card .value {{ font-size: 28px; font-weight: bold; margin: 0; }}
        .test-category {{ margin-bottom: 30px; }}
        .test-category h2 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
        .test-results {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 15px; }}
        .test-item {{ background: #f8f9fa; padding: 15px; border-radius: 5px; border-left: 4px solid #28a745; }}
        .test-item.failed {{ border-left-color: #dc3545; }}
        .test-item .test-name {{ font-weight: bold; color: #2c3e50; }}
        .test-item .test-details {{ color: #6c757d; margin-top: 5px; font-size: 14px; }}
        .performance-data {{ background: #e9ecef; padding: 20px; border-radius: 8px; margin-top: 20px; }}
        .performance-data h3 {{ margin-top: 0; color: #495057; }}
        .performance-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; }}
        .performance-item {{ background: white; padding: 10px; border-radius: 4px; text-align: center; }}
        .performance-item .metric {{ font-weight: bold; color: #495057; }}
        .performance-item .value {{ color: #007bff; font-size: 18px; }}
        .footer {{ text-align: center; margin-top: 40px; padding-top: 20px; border-top: 1px solid #dee2e6; color: #6c757d; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎬 VisionAI-ClipsMaster 综合测试报告</h1>
            <div class="version">版本 v{self.overall_summary['version']} - 稳定优化版</div>
            <div class="version">测试日期: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}</div>
        </div>
        
        <div class="summary">
            <div class="summary-card">
                <h3>总测试数</h3>
                <div class="value">{self.overall_summary['total_tests']}</div>
            </div>
            <div class="summary-card">
                <h3>通过测试</h3>
                <div class="value">{self.overall_summary['total_passed']}</div>
            </div>
            <div class="summary-card">
                <h3>失败测试</h3>
                <div class="value">{self.overall_summary['total_failed']}</div>
            </div>
            <div class="summary-card">
                <h3>成功率</h3>
                <div class="value">{self.overall_summary['overall_success_rate']:.1f}%</div>
            </div>
        </div>
"""
        
        # 添加各测试类别的详细结果
        for test_type, report in self.test_reports.items():
            category_info = self.overall_summary['test_categories'][test_type]
            html_content += f"""
        <div class="test-category">
            <h2>{test_type} (成功率: {category_info['success_rate']:.1f}%)</h2>
            <div class="test-results">
"""
            
            test_results = report.get('test_results', {})
            for test_name, result in test_results.items():
                status_class = "" if result['passed'] else "failed"
                status_icon = "✅" if result['passed'] else "❌"
                details = result.get('details', '')
                error_msg = result.get('error_msg', '')
                
                html_content += f"""
                <div class="test-item {status_class}">
                    <div class="test-name">{status_icon} {test_name}</div>
                    <div class="test-details">{details}</div>
                    {f'<div class="test-details" style="color: #dc3545;">错误: {error_msg}</div>' if error_msg else ''}
                </div>
"""
            
            html_content += """
            </div>
"""
            
            # 添加性能数据
            performance_data = report.get('performance_data', {})
            if performance_data:
                html_content += """
            <div class="performance-data">
                <h3>📈 性能数据</h3>
                <div class="performance-grid">
"""
                for metric_name, data in performance_data.items():
                    html_content += f"""
                    <div class="performance-item">
                        <div class="metric">{metric_name}</div>
                        <div class="value">{data['value']} {data['unit']}</div>
                    </div>
"""
                html_content += """
                </div>
            </div>
"""
            
            html_content += """
        </div>
"""
        
        html_content += f"""
        <div class="footer">
            <p>🎬 VisionAI-ClipsMaster v1.0.1 - 让AI为您的创作赋能，让每个视频都成为爆款！</p>
            <p>报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>
"""
        
        return html_content
        
    def generate_comprehensive_report(self):
        """生成综合测试报告"""
        print("🔍 开始生成VisionAI-ClipsMaster v1.0.1 综合测试报告")
        print("=" * 60)
        
        # 加载测试报告
        self.load_test_reports()
        
        if not self.test_reports:
            print("❌ 未找到任何测试报告文件")
            return None
            
        # 计算总体摘要
        self.calculate_overall_summary()
        
        # 生成HTML报告
        html_content = self.generate_html_report()
        
        # 保存报告
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        html_filename = f"comprehensive_test_report_v1_0_1_{timestamp}.html"
        json_filename = f"comprehensive_test_report_v1_0_1_{timestamp}.json"
        
        # 保存HTML报告
        with open(html_filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        # 保存JSON报告
        comprehensive_data = {
            'overall_summary': self.overall_summary,
            'detailed_reports': self.test_reports,
            'generation_time': datetime.now().isoformat()
        }
        
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(comprehensive_data, f, ensure_ascii=False, indent=2)
            
        # 打印摘要
        print("\n📊 综合测试报告摘要")
        print("=" * 60)
        print(f"版本: v{self.overall_summary['version']}")
        print(f"总测试数: {self.overall_summary['total_tests']}")
        print(f"通过测试: {self.overall_summary['total_passed']}")
        print(f"失败测试: {self.overall_summary['total_failed']}")
        print(f"总体成功率: {self.overall_summary['overall_success_rate']:.1f}%")
        
        print("\n📋 各测试类别成功率:")
        for test_type, category in self.overall_summary['test_categories'].items():
            print(f"• {test_type}: {category['success_rate']:.1f}% ({category['passed']}/{category['total']})")
            
        print(f"\n📄 报告已保存:")
        print(f"• HTML报告: {html_filename}")
        print(f"• JSON报告: {json_filename}")
        
        return comprehensive_data

def main():
    """主函数"""
    generator = ComprehensiveTestReportGenerator()
    result = generator.generate_comprehensive_report()
    return result

if __name__ == "__main__":
    main()
