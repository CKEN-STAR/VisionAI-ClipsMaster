#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 最终综合测试报告生成器
汇总所有测试结果并生成详细的测试报告
"""

import os
import json
import glob
from datetime import datetime
from pathlib import Path

class FinalTestReportGenerator:
    def __init__(self):
        self.output_dir = Path("test_output")
        self.report_data = {
            "report_generation_time": datetime.now().isoformat(),
            "test_summary": {},
            "detailed_results": {},
            "recommendations": [],
            "overall_assessment": ""
        }
    
    def load_test_reports(self):
        """加载所有测试报告"""
        report_files = glob.glob(str(self.output_dir / "*_test_report_*.json"))
        
        for report_file in report_files:
            try:
                with open(report_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 提取报告类型
                filename = os.path.basename(report_file)
                if "comprehensive" in filename:
                    report_type = "comprehensive"
                elif "performance" in filename:
                    report_type = "performance"
                elif "training" in filename:
                    report_type = "training"
                elif "ui_component" in filename:
                    report_type = "ui_component"
                else:
                    report_type = "unknown"
                
                self.report_data["detailed_results"][report_type] = data
                print(f"已加载测试报告: {filename}")
                
            except Exception as e:
                print(f"加载报告失败 {report_file}: {e}")
    
    def analyze_results(self):
        """分析测试结果"""
        total_tests = 0
        total_passed = 0
        total_failed = 0
        total_skipped = 0
        total_warned = 0
        
        test_categories = {}
        
        for report_type, data in self.report_data["detailed_results"].items():
            if "summary" in data:
                summary = data["summary"]
                total_tests += summary.get("total_tests", 0)
                total_passed += summary.get("passed", 0)
                total_failed += summary.get("failed", 0)
                total_skipped += summary.get("skipped", 0)
                total_warned += summary.get("warned", 0)
                
                test_categories[report_type] = {
                    "total": summary.get("total_tests", 0),
                    "passed": summary.get("passed", 0),
                    "failed": summary.get("failed", 0),
                    "skipped": summary.get("skipped", 0),
                    "warned": summary.get("warned", 0),
                    "success_rate": summary.get("success_rate", "0%"),
                    "status": data.get("overall_status", "UNKNOWN")
                }
        
        self.report_data["test_summary"] = {
            "total_tests": total_tests,
            "total_passed": total_passed,
            "total_failed": total_failed,
            "total_skipped": total_skipped,
            "total_warned": total_warned,
            "overall_success_rate": f"{(total_passed/total_tests*100):.1f}%" if total_tests > 0 else "0%",
            "test_categories": test_categories
        }
    
    def generate_recommendations(self):
        """生成改进建议"""
        recommendations = []
        
        # 基于测试结果生成建议
        for report_type, data in self.report_data["detailed_results"].items():
            if data.get("overall_status") == "FAIL":
                if report_type == "comprehensive":
                    recommendations.append("🔧 核心功能模块需要修复，建议检查语言检测器和SRT解析器的接口")
                elif report_type == "training":
                    recommendations.append("📚 训练功能模块需要完善，建议补充数据增强和剧情增强器")
                elif report_type == "performance":
                    recommendations.append("⚡ 性能优化需要关注，建议检查内存使用和量化配置")
                elif report_type == "ui_component":
                    recommendations.append("🎨 UI组件需要完善，建议补充缺失的组件和修复QApplication问题")
        
        # 通用建议
        if self.report_data["test_summary"]["total_failed"] > 0:
            recommendations.append("🛠️ 建议优先修复失败的测试用例，确保核心功能稳定")
        
        if self.report_data["test_summary"]["total_skipped"] > 5:
            recommendations.append("📋 有较多跳过的测试，建议补充测试数据和环境配置")
        
        success_rate = float(self.report_data["test_summary"]["overall_success_rate"].rstrip('%'))
        if success_rate >= 90:
            recommendations.append("✅ 系统整体质量良好，可以进入生产环境")
        elif success_rate >= 70:
            recommendations.append("⚠️ 系统基本可用，但建议修复主要问题后再发布")
        else:
            recommendations.append("❌ 系统存在较多问题，建议全面修复后再考虑发布")
        
        self.report_data["recommendations"] = recommendations
    
    def generate_assessment(self):
        """生成整体评估"""
        success_rate = float(self.report_data["test_summary"]["overall_success_rate"].rstrip('%'))
        total_tests = self.report_data["test_summary"]["total_tests"]
        
        if success_rate >= 90:
            assessment = f"🎉 VisionAI-ClipsMaster系统测试表现优秀！在{total_tests}个测试中，成功率达到{success_rate:.1f}%，系统功能完整，性能稳定，可以投入生产使用。"
        elif success_rate >= 70:
            assessment = f"✅ VisionAI-ClipsMaster系统测试表现良好。在{total_tests}个测试中，成功率为{success_rate:.1f}%，核心功能基本完整，但仍有部分模块需要优化。"
        elif success_rate >= 50:
            assessment = f"⚠️ VisionAI-ClipsMaster系统测试表现一般。在{total_tests}个测试中，成功率为{success_rate:.1f}%，系统基本框架完整，但需要修复多个关键问题。"
        else:
            assessment = f"❌ VisionAI-ClipsMaster系统测试发现较多问题。在{total_tests}个测试中，成功率仅为{success_rate:.1f}%，建议全面检查和修复后再进行测试。"
        
        self.report_data["overall_assessment"] = assessment
    
    def generate_html_report(self):
        """生成HTML格式的测试报告"""
        html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VisionAI-ClipsMaster 综合测试报告</title>
    <style>
        body {{ font-family: 'Microsoft YaHei', Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; text-align: center; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; border-left: 4px solid #3498db; padding-left: 15px; }}
        .summary {{ background: #ecf0f1; padding: 20px; border-radius: 8px; margin: 20px 0; }}
        .test-category {{ background: #fff; border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px; }}
        .status-pass {{ color: #27ae60; font-weight: bold; }}
        .status-fail {{ color: #e74c3c; font-weight: bold; }}
        .status-warn {{ color: #f39c12; font-weight: bold; }}
        .recommendations {{ background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; }}
        .assessment {{ background: #d1ecf1; border: 1px solid #bee5eb; padding: 20px; border-radius: 5px; font-size: 16px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background-color: #3498db; color: white; }}
        .progress-bar {{ background: #ecf0f1; border-radius: 10px; overflow: hidden; height: 20px; }}
        .progress-fill {{ height: 100%; background: linear-gradient(90deg, #27ae60, #2ecc71); }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🎬 VisionAI-ClipsMaster 综合测试报告</h1>
        
        <div class="summary">
            <h2>📊 测试概览</h2>
            <p><strong>报告生成时间:</strong> {self.report_data['report_generation_time']}</p>
            <p><strong>总测试数:</strong> {self.report_data['test_summary']['total_tests']}</p>
            <p><strong>通过:</strong> <span class="status-pass">{self.report_data['test_summary']['total_passed']}</span></p>
            <p><strong>失败:</strong> <span class="status-fail">{self.report_data['test_summary']['total_failed']}</span></p>
            <p><strong>跳过:</strong> {self.report_data['test_summary']['total_skipped']}</p>
            <p><strong>警告:</strong> <span class="status-warn">{self.report_data['test_summary']['total_warned']}</span></p>
            <p><strong>整体成功率:</strong> {self.report_data['test_summary']['overall_success_rate']}</p>
            
            <div class="progress-bar">
                <div class="progress-fill" style="width: {self.report_data['test_summary']['overall_success_rate']}"></div>
            </div>
        </div>
        
        <h2>🔍 分类测试结果</h2>
        <table>
            <tr>
                <th>测试类别</th>
                <th>总数</th>
                <th>通过</th>
                <th>失败</th>
                <th>跳过</th>
                <th>成功率</th>
                <th>状态</th>
            </tr>
"""
        
        for category, data in self.report_data['test_summary']['test_categories'].items():
            status_class = "status-pass" if data['status'] == "PASS" else "status-fail"
            html_content += f"""
            <tr>
                <td>{category}</td>
                <td>{data['total']}</td>
                <td class="status-pass">{data['passed']}</td>
                <td class="status-fail">{data['failed']}</td>
                <td>{data['skipped']}</td>
                <td>{data['success_rate']}</td>
                <td class="{status_class}">{data['status']}</td>
            </tr>
"""
        
        html_content += f"""
        </table>
        
        <h2>💡 改进建议</h2>
        <div class="recommendations">
            <ul>
"""
        
        for recommendation in self.report_data['recommendations']:
            html_content += f"<li>{recommendation}</li>"
        
        html_content += f"""
            </ul>
        </div>
        
        <h2>🎯 整体评估</h2>
        <div class="assessment">
            {self.report_data['overall_assessment']}
        </div>
        
        <hr>
        <p style="text-align: center; color: #7f8c8d; font-size: 14px;">
            VisionAI-ClipsMaster 测试报告 | 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </p>
    </div>
</body>
</html>
"""
        
        return html_content
    
    def save_reports(self):
        """保存测试报告"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 保存JSON报告
        json_file = self.output_dir / f"final_comprehensive_report_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.report_data, f, ensure_ascii=False, indent=2)
        
        # 保存HTML报告
        html_file = self.output_dir / f"final_comprehensive_report_{timestamp}.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(self.generate_html_report())
        
        print(f"\n📋 最终测试报告已生成:")
        print(f"   JSON报告: {json_file}")
        print(f"   HTML报告: {html_file}")
        
        return json_file, html_file
    
    def generate_final_report(self):
        """生成最终综合测试报告"""
        print("🔍 正在收集测试报告...")
        self.load_test_reports()
        
        print("📊 正在分析测试结果...")
        self.analyze_results()
        
        print("💡 正在生成改进建议...")
        self.generate_recommendations()
        
        print("🎯 正在生成整体评估...")
        self.generate_assessment()
        
        print("💾 正在保存报告...")
        json_file, html_file = self.save_reports()
        
        # 打印摘要
        print(f"\n{'='*60}")
        print("🎬 VisionAI-ClipsMaster 最终测试报告摘要")
        print(f"{'='*60}")
        print(f"📊 总测试数: {self.report_data['test_summary']['total_tests']}")
        print(f"✅ 通过: {self.report_data['test_summary']['total_passed']}")
        print(f"❌ 失败: {self.report_data['test_summary']['total_failed']}")
        print(f"⏭️ 跳过: {self.report_data['test_summary']['total_skipped']}")
        print(f"📈 成功率: {self.report_data['test_summary']['overall_success_rate']}")
        print(f"\n{self.report_data['overall_assessment']}")
        print(f"{'='*60}")
        
        return self.report_data

if __name__ == "__main__":
    generator = FinalTestReportGenerator()
    final_report = generator.generate_final_report()
