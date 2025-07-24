#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster UI整合测试综合报告生成器

汇总所有测试结果，生成完整的UI整合测试报告
"""

import json
import os
from datetime import datetime
from pathlib import Path

class UIIntegrationReportGenerator:
    """UI整合测试报告生成器"""
    
    def __init__(self):
        self.report_data = {
            "test_summary": {
                "timestamp": datetime.now().isoformat(),
                "test_type": "UI Integration Comprehensive Test",
                "version": "1.0.0"
            },
            "test_results": {},
            "performance_analysis": {},
            "issues_analysis": {},
            "recommendations": []
        }
        
    def load_test_results(self):
        """加载所有测试结果文件"""
        test_files = [
            ("integration_test", "ui_integration_test_*.json"),
            ("functional_test", "ui_functional_test_*.json")
        ]
        
        for test_type, pattern in test_files:
            # 查找最新的测试文件
            files = list(Path(".").glob(pattern))
            if files:
                latest_file = max(files, key=os.path.getctime)
                try:
                    with open(latest_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        self.report_data["test_results"][test_type] = {
                            "file": str(latest_file),
                            "data": data
                        }
                        print(f"加载测试结果: {latest_file}")
                except Exception as e:
                    print(f"加载测试文件失败 {latest_file}: {e}")
                    
    def analyze_test_results(self):
        """分析测试结果"""
        print("\n=== 测试结果分析 ===")
        
        # 分析整合测试结果
        if "integration_test" in self.report_data["test_results"]:
            integration_data = self.report_data["test_results"]["integration_test"]["data"]
            
            summary = integration_data.get("test_summary", {})
            total_tests = summary.get("total_tests", 0)
            passed = summary.get("passed", 0)
            failed = summary.get("failed", 0)
            
            success_rate = (passed / total_tests * 100) if total_tests > 0 else 0
            
            self.report_data["performance_analysis"]["integration_test"] = {
                "total_tests": total_tests,
                "passed": passed,
                "failed": failed,
                "success_rate": success_rate,
                "status": "良好" if success_rate >= 75 else "需要改进"
            }
            
            print(f"整合测试: {passed}/{total_tests} 通过 ({success_rate:.1f}%)")
            
        # 分析功能测试结果
        if "functional_test" in self.report_data["test_results"]:
            functional_data = self.report_data["test_results"]["functional_test"]["data"]
            
            issues_count = len(functional_data.get("issues_found", []))
            functional_tests = len(functional_data.get("functional_tests", {}))
            
            self.report_data["performance_analysis"]["functional_test"] = {
                "functional_tests": functional_tests,
                "issues_found": issues_count,
                "status": "良好" if issues_count == 0 else "发现问题"
            }
            
            print(f"功能测试: {functional_tests} 项测试, {issues_count} 个问题")
            
    def analyze_performance_metrics(self):
        """分析性能指标"""
        print("\n=== 性能指标分析 ===")
        
        performance_data = {}
        
        # 从功能测试中提取性能数据
        if "functional_test" in self.report_data["test_results"]:
            functional_data = self.report_data["test_results"]["functional_test"]["data"]
            
            # 内存使用分析
            memory_metrics = functional_data.get("performance_metrics", {}).get("memory_usage", {})
            if memory_metrics:
                memory_mb = memory_metrics.get("current_mb", 0)
                within_limits = memory_metrics.get("within_limits", False)
                
                performance_data["memory"] = {
                    "usage_mb": memory_mb,
                    "within_limits": within_limits,
                    "status": "良好" if within_limits else "超出限制",
                    "recommendation": "内存使用正常" if within_limits else "需要优化内存使用"
                }
                
                print(f"内存使用: {memory_mb:.1f}MB ({'正常' if within_limits else '超限'})")
                
            # UI响应性分析
            tab_switch_metrics = {}
            for key, value in functional_data.get("performance_metrics", {}).items():
                if key.startswith("tab_switch_"):
                    if isinstance(value, dict) and "switch_time" in value:
                        tab_switch_metrics[key] = value
                        
            if tab_switch_metrics:
                switch_times = [m["switch_time"] for m in tab_switch_metrics.values()]
                avg_switch_time = sum(switch_times) / len(switch_times)
                max_switch_time = max(switch_times)
                
                performance_data["ui_responsiveness"] = {
                    "avg_switch_time": avg_switch_time,
                    "max_switch_time": max_switch_time,
                    "responsive": avg_switch_time < 0.5,
                    "status": "响应良好" if avg_switch_time < 0.5 else "响应较慢"
                }
                
                print(f"UI响应性: 平均 {avg_switch_time:.3f}s, 最大 {max_switch_time:.3f}s")
                
        self.report_data["performance_analysis"]["metrics"] = performance_data
        
    def identify_issues_and_recommendations(self):
        """识别问题并生成建议"""
        print("\n=== 问题识别与建议 ===")
        
        issues = []
        recommendations = []
        
        # 从整合测试中提取问题
        if "integration_test" in self.report_data["test_results"]:
            integration_data = self.report_data["test_results"]["integration_test"]["data"]
            
            # 检查失败的测试
            for category, tests in integration_data.get("test_categories", {}).items():
                for test_name, test_result in tests.items():
                    if test_result.get("status") == "failed":
                        issue = {
                            "category": category,
                            "test": test_name,
                            "details": test_result.get("details", ""),
                            "error": test_result.get("error", "")
                        }
                        issues.append(issue)
                        
        # 从功能测试中提取问题
        if "functional_test" in self.report_data["test_results"]:
            functional_data = self.report_data["test_results"]["functional_test"]["data"]
            
            for issue in functional_data.get("issues_found", []):
                issues.append({
                    "category": "functional",
                    "details": issue
                })
                
        # 生成建议
        if issues:
            # UI组件相关问题
            ui_component_issues = [i for i in issues if "component" in i.get("test", "")]
            if ui_component_issues:
                recommendations.append({
                    "priority": "高",
                    "category": "UI组件",
                    "description": "部分UI组件名称不匹配，需要更新测试脚本或修复组件命名",
                    "action": "检查并统一UI组件命名规范"
                })
                
            # 方法缺失问题
            method_issues = [i for i in issues if "method" in i.get("test", "")]
            if method_issues:
                recommendations.append({
                    "priority": "中",
                    "category": "功能方法",
                    "description": "部分预期的功能方法不存在，可能影响用户体验",
                    "action": "实现缺失的功能方法或更新功能规格"
                })
        else:
            recommendations.append({
                "priority": "低",
                "category": "整体",
                "description": "UI整合测试基本通过，系统运行稳定",
                "action": "继续监控性能指标，定期进行回归测试"
            })
            
        # 性能相关建议
        performance_metrics = self.report_data["performance_analysis"].get("metrics", {})
        memory_data = performance_metrics.get("memory", {})
        
        if memory_data and not memory_data.get("within_limits", True):
            recommendations.append({
                "priority": "高",
                "category": "性能优化",
                "description": "内存使用超出预期限制，需要优化",
                "action": "分析内存使用模式，优化大对象的生命周期管理"
            })
            
        self.report_data["issues_analysis"] = {
            "total_issues": len(issues),
            "issues": issues,
            "recommendations": recommendations
        }
        
        print(f"发现问题: {len(issues)} 个")
        print(f"生成建议: {len(recommendations)} 条")
        
    def generate_comprehensive_report(self):
        """生成综合报告"""
        print("\n=== 生成综合报告 ===")
        
        # 加载测试结果
        self.load_test_results()
        
        # 分析测试结果
        self.analyze_test_results()
        
        # 分析性能指标
        self.analyze_performance_metrics()
        
        # 识别问题和建议
        self.identify_issues_and_recommendations()
        
        # 生成报告文件
        report_file = f"ui_integration_comprehensive_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.report_data, f, ensure_ascii=False, indent=2)
            
        # 生成HTML报告
        html_report = self.generate_html_report()
        html_file = report_file.replace('.json', '.html')
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_report)
            
        print(f"综合报告已保存:")
        print(f"  JSON: {report_file}")
        print(f"  HTML: {html_file}")
        
        return report_file, html_file
        
    def generate_html_report(self):
        """生成HTML格式的报告"""
        html_template = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VisionAI-ClipsMaster UI整合测试报告</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }}
        .header {{ background: #f4f4f4; padding: 20px; border-radius: 5px; }}
        .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
        .success {{ color: #28a745; }}
        .warning {{ color: #ffc107; }}
        .error {{ color: #dc3545; }}
        .metric {{ display: inline-block; margin: 10px; padding: 10px; background: #f8f9fa; border-radius: 3px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>VisionAI-ClipsMaster UI整合测试报告</h1>
        <p>生成时间: {timestamp}</p>
    </div>

    <div class="section">
        <h2>测试概览</h2>
        {test_overview}
    </div>

    <div class="section">
        <h2>性能指标</h2>
        {performance_metrics}
    </div>

    <div class="section">
        <h2>问题与建议</h2>
        {issues_recommendations}
    </div>
</body>
</html>"""
        
        # 生成测试概览
        test_overview = "<p>测试结果加载中...</p>"
        if "integration_test" in self.report_data["performance_analysis"]:
            integration = self.report_data["performance_analysis"]["integration_test"]
            test_overview = f"""
            <div class="metric">
                <strong>整合测试</strong><br>
                通过率: <span class="{'success' if integration['success_rate'] >= 75 else 'warning'}">{integration['success_rate']:.1f}%</span><br>
                ({integration['passed']}/{integration['total_tests']} 通过)
            </div>
            """
            
        # 生成性能指标
        performance_metrics = "<p>性能数据收集中...</p>"
        metrics = self.report_data["performance_analysis"].get("metrics", {})
        if metrics:
            memory = metrics.get("memory", {})
            ui_resp = metrics.get("ui_responsiveness", {})
            
            performance_metrics = f"""
            <div class="metric">
                <strong>内存使用</strong><br>
                {memory.get('usage_mb', 0):.1f}MB<br>
                <span class="{'success' if memory.get('within_limits') else 'error'}">{memory.get('status', '未知')}</span>
            </div>
            <div class="metric">
                <strong>UI响应性</strong><br>
                平均: {ui_resp.get('avg_switch_time', 0):.3f}s<br>
                <span class="{'success' if ui_resp.get('responsive') else 'warning'}">{ui_resp.get('status', '未知')}</span>
            </div>
            """
            
        # 生成问题与建议
        issues_analysis = self.report_data.get("issues_analysis", {})
        issues_recommendations = f"""
        <p>发现问题: {issues_analysis.get('total_issues', 0)} 个</p>
        <p>生成建议: {len(issues_analysis.get('recommendations', []))} 条</p>
        """
        
        return html_template.format(
            timestamp=self.report_data["test_summary"]["timestamp"],
            test_overview=test_overview,
            performance_metrics=performance_metrics,
            issues_recommendations=issues_recommendations
        )

def main():
    """主函数"""
    print("VisionAI-ClipsMaster UI整合测试综合报告生成器")
    print("=" * 60)
    
    generator = UIIntegrationReportGenerator()
    json_file, html_file = generator.generate_comprehensive_report()
    
    print("\n" + "=" * 60)
    print("报告生成完成!")
    print(f"详细数据: {json_file}")
    print(f"可视化报告: {html_file}")

if __name__ == "__main__":
    main()
