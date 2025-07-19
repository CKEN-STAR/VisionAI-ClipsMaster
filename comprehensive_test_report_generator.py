#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 综合测试报告生成器
汇总所有测试结果，提供性能指标、问题分析和改进建议
"""

import sys
import os
import json
import glob
from datetime import datetime
from pathlib import Path

class ComprehensiveTestReportGenerator:
    """综合测试报告生成器"""
    
    def __init__(self):
        self.report_data = {
            "report_generation_time": datetime.now().isoformat(),
            "test_summary": {},
            "performance_metrics": {},
            "issues_analysis": {},
            "recommendations": {},
            "verification_standards": {}
        }
        
    def load_test_reports(self):
        """加载所有测试报告"""
        report_files = {
            "comprehensive": glob.glob("comprehensive_test_report_*.json"),
            "screenplay_reconstruction": glob.glob("screenplay_reconstruction_test_report_*.json"),
            "video_processing": glob.glob("video_processing_test_report_*.json"),
            "performance_memory": glob.glob("performance_memory_test_report_*.json"),
            "stability_exception": glob.glob("stability_exception_test_report_*.json")
        }
        
        loaded_reports = {}
        
        for category, files in report_files.items():
            if files:
                # 取最新的报告文件
                latest_file = max(files, key=os.path.getctime)
                try:
                    with open(latest_file, 'r', encoding='utf-8') as f:
                        loaded_reports[category] = json.load(f)
                    print(f"已加载 {category} 测试报告: {latest_file}")
                except Exception as e:
                    print(f"加载 {category} 报告失败: {e}")
            else:
                print(f"未找到 {category} 测试报告")
        
        return loaded_reports
    
    def analyze_test_results(self, reports):
        """分析测试结果"""
        total_tests = 0
        total_passed = 0
        total_failed = 0
        
        test_categories = {}
        
        for category, report in reports.items():
            if "summary" in report:
                summary = report["summary"]
                category_tests = summary.get("total_tests", 0)
                category_passed = summary.get("passed_tests", 0)
                category_failed = summary.get("failed_tests", 0)
                category_pass_rate = summary.get("pass_rate", 0)
                
                test_categories[category] = {
                    "total_tests": category_tests,
                    "passed_tests": category_passed,
                    "failed_tests": category_failed,
                    "pass_rate": category_pass_rate
                }
                
                total_tests += category_tests
                total_passed += category_passed
                total_failed += category_failed
        
        overall_pass_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        self.report_data["test_summary"] = {
            "total_tests": total_tests,
            "total_passed": total_passed,
            "total_failed": total_failed,
            "overall_pass_rate": round(overall_pass_rate, 2),
            "categories": test_categories
        }
        
        return overall_pass_rate
    
    def extract_performance_metrics(self, reports):
        """提取性能指标"""
        metrics = {}
        
        # 从性能测试报告中提取指标
        if "performance_memory" in reports:
            perf_report = reports["performance_memory"]
            if "tests" in perf_report:
                tests = perf_report["tests"]
                
                # 内存使用指标
                if "内存基线测试" in tests:
                    memory_test = tests["内存基线测试"]
                    if memory_test.get("status") == "PASS" and "details" in memory_test:
                        details = memory_test["details"]
                        metrics["memory"] = {
                            "total_gb": details.get("system_memory", {}).get("total_gb", 0),
                            "available_gb": details.get("system_memory", {}).get("available_gb", 0),
                            "usage_percent": details.get("system_memory", {}).get("percent", 0),
                            "meets_4gb_requirement": details.get("meets_4gb_requirement", False)
                        }
                
                # UI响应时间
                if "UI响应时间测试" in tests:
                    ui_test = tests["UI响应时间测试"]
                    if ui_test.get("status") == "PASS" and "details" in ui_test:
                        details = ui_test["details"]
                        metrics["ui_performance"] = {
                            "creation_time_ms": details.get("component_creation_time", 0),
                            "response_time_ms": details.get("component_response_time", 0),
                            "total_time_ms": details.get("total_ui_time", 0),
                            "meets_1s_requirement": details.get("meets_1s_requirement", False)
                        }
                
                # 模型切换性能
                if "模型切换性能测试" in tests:
                    switch_test = tests["模型切换性能测试"]
                    if switch_test.get("status") == "PASS" and "details" in switch_test:
                        details = switch_test["details"]
                        metrics["model_switching"] = {
                            "chinese_detection_ms": details.get("chinese_detection_time", 0),
                            "english_detection_ms": details.get("english_detection_time", 0),
                            "average_switch_ms": details.get("average_switch_time", 0),
                            "meets_1_5s_requirement": details.get("meets_1_5s_requirement", False)
                        }
        
        # 从稳定性测试报告中提取指标
        if "stability_exception" in reports:
            stability_report = reports["stability_exception"]
            if "tests" in stability_report:
                tests = stability_report["tests"]
                
                # 稳定性指标
                if "短期稳定性测试（5分钟）" in tests:
                    stability_test = tests["短期稳定性测试（5分钟）"]
                    if stability_test.get("status") == "PASS" and "details" in stability_test:
                        details = stability_test["details"]
                        metrics["stability"] = {
                            "duration_seconds": details.get("actual_duration_seconds", 0),
                            "total_operations": details.get("total_operations", 0),
                            "operations_per_second": details.get("operations_per_second", 0),
                            "error_rate_percent": details.get("error_rate_percent", 0),
                            "stability_achieved": details.get("stability_achieved", False)
                        }
        
        self.report_data["performance_metrics"] = metrics
    
    def analyze_issues(self, reports):
        """分析发现的问题"""
        issues = []
        
        for category, report in reports.items():
            if "tests" in report:
                for test_name, test_result in report["tests"].items():
                    if test_result.get("status") == "FAIL":
                        issue = {
                            "category": category,
                            "test_name": test_name,
                            "error": test_result.get("error", "未知错误"),
                            "details": test_result.get("details", {}),
                            "severity": self._assess_severity(test_name, test_result)
                        }
                        issues.append(issue)
        
        self.report_data["issues_analysis"] = {
            "total_issues": len(issues),
            "issues": issues,
            "critical_issues": [i for i in issues if i["severity"] == "critical"],
            "major_issues": [i for i in issues if i["severity"] == "major"],
            "minor_issues": [i for i in issues if i["severity"] == "minor"]
        }
    
    def _assess_severity(self, test_name, test_result):
        """评估问题严重程度"""
        error = str(test_result.get("error", "")).lower()
        
        # 关键问题
        if any(keyword in test_name.lower() for keyword in ["内存", "memory", "稳定性", "stability"]):
            return "critical"
        
        # 主要问题
        if any(keyword in test_name.lower() for keyword in ["模型", "model", "切换", "switch"]):
            return "major"
        
        # 次要问题
        return "minor"
    
    def generate_recommendations(self):
        """生成改进建议"""
        recommendations = []
        
        # 基于问题分析生成建议
        issues = self.report_data["issues_analysis"]
        
        if issues["critical_issues"]:
            recommendations.append({
                "priority": "高",
                "category": "内存优化",
                "description": "发现关键内存问题，建议优化内存使用策略",
                "actions": [
                    "实现更激进的量化策略（Q2_K）",
                    "优化模型分片加载机制",
                    "增强内存监控和自动清理功能"
                ]
            })
        
        if issues["major_issues"]:
            recommendations.append({
                "priority": "中",
                "category": "模型性能",
                "description": "模型切换或加载存在性能问题",
                "actions": [
                    "优化模型预加载策略",
                    "实现模型缓存机制",
                    "改进语言检测算法"
                ]
            })
        
        # 基于性能指标生成建议
        metrics = self.report_data["performance_metrics"]
        
        if "memory" in metrics and not metrics["memory"].get("meets_4gb_requirement", True):
            recommendations.append({
                "priority": "高",
                "category": "内存兼容性",
                "description": "系统内存使用超出4GB限制",
                "actions": [
                    "启用更激进的量化模式",
                    "实现动态内存管理",
                    "优化数据结构和算法"
                ]
            })
        
        if "ui_performance" in metrics and not metrics["ui_performance"].get("meets_1s_requirement", True):
            recommendations.append({
                "priority": "中",
                "category": "UI性能",
                "description": "UI响应时间超出1秒要求",
                "actions": [
                    "优化UI组件加载",
                    "实现异步UI更新",
                    "减少UI初始化开销"
                ]
            })
        
        self.report_data["recommendations"] = recommendations
    
    def check_verification_standards(self):
        """检查验证标准"""
        standards = {
            "core_functionality_pass_rate": {
                "target": 98.0,
                "actual": self.report_data["test_summary"].get("overall_pass_rate", 0),
                "status": "PASS" if self.report_data["test_summary"].get("overall_pass_rate", 0) >= 98.0 else "FAIL"
            },
            "memory_peak_limit": {
                "target": 3.8,
                "actual": self.report_data["performance_metrics"].get("memory", {}).get("usage_percent", 0) / 100 * 
                         self.report_data["performance_metrics"].get("memory", {}).get("total_gb", 16),
                "status": "UNKNOWN"  # 需要更详细的内存峰值数据
            },
            "ui_response_time": {
                "target": 1000,  # 毫秒
                "actual": self.report_data["performance_metrics"].get("ui_performance", {}).get("total_time_ms", 0),
                "status": "PASS" if self.report_data["performance_metrics"].get("ui_performance", {}).get("meets_1s_requirement", False) else "FAIL"
            },
            "model_switching_delay": {
                "target": 1500,  # 毫秒
                "actual": max(
                    self.report_data["performance_metrics"].get("model_switching", {}).get("chinese_detection_ms", 0),
                    self.report_data["performance_metrics"].get("model_switching", {}).get("english_detection_ms", 0)
                ),
                "status": "PASS" if self.report_data["performance_metrics"].get("model_switching", {}).get("meets_1_5s_requirement", False) else "FAIL"
            }
        }
        
        self.report_data["verification_standards"] = standards
    
    def generate_report(self):
        """生成综合测试报告"""
        print("=" * 80)
        print("VisionAI-ClipsMaster 综合功能测试报告")
        print("=" * 80)
        
        # 加载所有测试报告
        reports = self.load_test_reports()
        
        if not reports:
            print("❌ 未找到任何测试报告文件")
            return
        
        # 分析测试结果
        overall_pass_rate = self.analyze_test_results(reports)
        
        # 提取性能指标
        self.extract_performance_metrics(reports)
        
        # 分析问题
        self.analyze_issues(reports)
        
        # 生成建议
        self.generate_recommendations()
        
        # 检查验证标准
        self.check_verification_standards()
        
        # 输出报告
        self.print_report()
        
        # 保存报告
        self.save_report()
        
        return self.report_data
    
    def print_report(self):
        """打印报告内容"""
        print("\n📊 测试总结")
        print("-" * 40)
        summary = self.report_data["test_summary"]
        print(f"总测试数: {summary['total_tests']}")
        print(f"通过测试: {summary['total_passed']}")
        print(f"失败测试: {summary['total_failed']}")
        print(f"总体通过率: {summary['overall_pass_rate']:.2f}%")
        
        print("\n📈 各模块测试结果")
        print("-" * 40)
        for category, stats in summary["categories"].items():
            status = "✅" if stats["pass_rate"] == 100 else "⚠️" if stats["pass_rate"] >= 80 else "❌"
            print(f"{status} {category}: {stats['passed_tests']}/{stats['total_tests']} ({stats['pass_rate']:.1f}%)")
        
        print("\n⚡ 性能指标")
        print("-" * 40)
        metrics = self.report_data["performance_metrics"]
        
        if "memory" in metrics:
            mem = metrics["memory"]
            print(f"内存使用: {mem.get('usage_percent', 0):.1f}% ({mem.get('available_gb', 0):.1f}GB可用)")
        
        if "ui_performance" in metrics:
            ui = metrics["ui_performance"]
            print(f"UI响应时间: {ui.get('total_time_ms', 0):.1f}ms")
        
        if "stability" in metrics:
            stab = metrics["stability"]
            print(f"稳定性测试: {stab.get('total_operations', 0)}次操作，错误率{stab.get('error_rate_percent', 0):.2f}%")
        
        print("\n🔍 验证标准检查")
        print("-" * 40)
        standards = self.report_data["verification_standards"]
        for standard, data in standards.items():
            status = "✅" if data["status"] == "PASS" else "❌" if data["status"] == "FAIL" else "❓"
            print(f"{status} {standard}: {data['actual']} (目标: {data['target']})")
        
        issues = self.report_data["issues_analysis"]
        if issues["total_issues"] > 0:
            print(f"\n⚠️ 发现问题")
            print("-" * 40)
            print(f"关键问题: {len(issues['critical_issues'])}个")
            print(f"主要问题: {len(issues['major_issues'])}个")
            print(f"次要问题: {len(issues['minor_issues'])}个")
        
        recommendations = self.report_data["recommendations"]
        if recommendations:
            print(f"\n💡 改进建议")
            print("-" * 40)
            for rec in recommendations:
                print(f"[{rec['priority']}] {rec['category']}: {rec['description']}")
    
    def save_report(self):
        """保存综合报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"VisionAI_ClipsMaster_Comprehensive_Test_Report_{timestamp}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.report_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 综合测试报告已保存: {report_file}")

if __name__ == "__main__":
    generator = ComprehensiveTestReportGenerator()
    generator.generate_report()
