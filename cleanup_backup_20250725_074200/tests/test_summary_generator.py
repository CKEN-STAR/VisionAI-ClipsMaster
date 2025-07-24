#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 测试结果摘要生成器

分析测试结果并生成易读的摘要报告

作者: VisionAI-ClipsMaster Team
日期: 2025-07-23
"""

import os
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

class TestSummaryGenerator:
    """测试结果摘要生成器"""
    
    def __init__(self, test_output_dir: str):
        """初始化摘要生成器"""
        self.test_output_dir = Path(test_output_dir)
        self.summary_data = {
            "generation_time": datetime.now().isoformat(),
            "test_files_analyzed": [],
            "overall_summary": {},
            "detailed_results": {},
            "recommendations": []
        }
    
    def generate_summary(self) -> Dict[str, Any]:
        """生成测试摘要"""
        print("分析测试结果...")
        
        # 查找测试结果文件
        test_files = self._find_test_result_files()
        
        if not test_files:
            print("未找到测试结果文件")
            return self.summary_data
        
        # 分析每个测试文件
        for test_file in test_files:
            self._analyze_test_file(test_file)
        
        # 生成总体摘要
        self._generate_overall_summary()
        
        # 生成建议
        self._generate_recommendations()
        
        # 保存摘要
        self._save_summary()
        
        return self.summary_data
    
    def _find_test_result_files(self) -> List[Path]:
        """查找测试结果文件"""
        test_files = []
        
        if not self.test_output_dir.exists():
            return test_files
        
        # 查找JSON格式的测试报告
        for file_path in self.test_output_dir.glob("*test_report*.json"):
            test_files.append(file_path)
        
        # 查找其他格式的测试结果
        for file_path in self.test_output_dir.glob("*test*.json"):
            if file_path not in test_files:
                test_files.append(file_path)
        
        return sorted(test_files)
    
    def _analyze_test_file(self, test_file: Path):
        """分析单个测试文件"""
        try:
            with open(test_file, 'r', encoding='utf-8') as f:
                test_data = json.load(f)
            
            file_analysis = {
                "file_name": test_file.name,
                "file_path": str(test_file),
                "analysis_time": datetime.now().isoformat(),
                "test_suites": {},
                "performance_metrics": {},
                "validation_results": {},
                "issues_found": []
            }
            
            # 分析测试套件结果
            if "test_suites" in test_data:
                file_analysis["test_suites"] = self._analyze_test_suites(test_data["test_suites"])
            
            # 分析性能指标
            if "performance_metrics" in test_data:
                file_analysis["performance_metrics"] = self._analyze_performance_metrics(test_data["performance_metrics"])
            
            # 分析验证结果
            if "validation_results" in test_data:
                file_analysis["validation_results"] = self._analyze_validation_results(test_data["validation_results"])
            
            self.summary_data["test_files_analyzed"].append(file_analysis)
            self.summary_data["detailed_results"][test_file.name] = file_analysis
            
        except Exception as e:
            print(f"分析文件 {test_file} 时出错: {e}")
    
    def _analyze_test_suites(self, test_suites: Dict[str, Any]) -> Dict[str, Any]:
        """分析测试套件结果"""
        suite_analysis = {}
        
        for suite_name, suite_data in test_suites.items():
            if isinstance(suite_data, dict):
                analysis = {
                    "tests_run": suite_data.get("tests_run", 0),
                    "failures": suite_data.get("failures", 0),
                    "errors": suite_data.get("errors", 0),
                    "success_rate": suite_data.get("success_rate", 0),
                    "status": "PASS" if suite_data.get("success_rate", 0) >= 0.9 else "FAIL"
                }
                
                # 添加失败详情
                if suite_data.get("failures", 0) > 0:
                    analysis["failure_details"] = suite_data.get("failure_details", [])
                
                if suite_data.get("errors", 0) > 0:
                    analysis["error_details"] = suite_data.get("error_details", [])
                
                suite_analysis[suite_name] = analysis
        
        return suite_analysis
    
    def _analyze_performance_metrics(self, performance_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """分析性能指标"""
        metrics_analysis = {}
        
        # 定义性能阈值
        thresholds = {
            "alignment_avg_time": 0.5,
            "model_switch_avg_time": 1.5,
            "estimated_memory_usage_gb": 3.8,
            "startup_time": 5.0,
            "response_time": 2.0
        }
        
        for metric_name, metric_value in performance_metrics.items():
            analysis = {
                "value": metric_value,
                "threshold": thresholds.get(metric_name),
                "status": "UNKNOWN"
            }
            
            if metric_name in thresholds:
                threshold = thresholds[metric_name]
                if isinstance(metric_value, (int, float)):
                    analysis["status"] = "PASS" if metric_value <= threshold else "FAIL"
                    analysis["margin"] = threshold - metric_value
            
            metrics_analysis[metric_name] = analysis
        
        return metrics_analysis
    
    def _analyze_validation_results(self, validation_results: Dict[str, Any]) -> Dict[str, Any]:
        """分析验证结果"""
        validation_analysis = {}
        
        for validation_name, validation_data in validation_results.items():
            if isinstance(validation_data, dict) and "status" in validation_data:
                analysis = {
                    "status": validation_data["status"],
                    "measured": validation_data.get("measured"),
                    "standard": validation_data.get("standard"),
                    "passed": validation_data["status"] == "PASS"
                }
                
                validation_analysis[validation_name] = analysis
        
        return validation_analysis
    
    def _generate_overall_summary(self):
        """生成总体摘要"""
        total_tests = 0
        total_failures = 0
        total_errors = 0
        passed_validations = 0
        total_validations = 0
        
        for file_analysis in self.summary_data["test_files_analyzed"]:
            # 统计测试结果
            for suite_name, suite_data in file_analysis["test_suites"].items():
                total_tests += suite_data.get("tests_run", 0)
                total_failures += suite_data.get("failures", 0)
                total_errors += suite_data.get("errors", 0)
            
            # 统计验证结果
            for validation_name, validation_data in file_analysis["validation_results"].items():
                total_validations += 1
                if validation_data.get("passed", False):
                    passed_validations += 1
        
        overall_success_rate = (total_tests - total_failures - total_errors) / total_tests if total_tests > 0 else 0
        validation_success_rate = passed_validations / total_validations if total_validations > 0 else 0
        
        self.summary_data["overall_summary"] = {
            "total_test_files": len(self.summary_data["test_files_analyzed"]),
            "total_tests": total_tests,
            "total_failures": total_failures,
            "total_errors": total_errors,
            "overall_success_rate": overall_success_rate,
            "total_validations": total_validations,
            "passed_validations": passed_validations,
            "validation_success_rate": validation_success_rate,
            "overall_status": "PASS" if overall_success_rate >= 0.9 and validation_success_rate >= 0.8 else "FAIL"
        }
    
    def _generate_recommendations(self):
        """生成改进建议"""
        recommendations = []
        
        overall = self.summary_data["overall_summary"]
        
        # 基于测试结果的建议
        if overall.get("overall_success_rate", 0) < 0.9:
            recommendations.append({
                "type": "test_quality",
                "priority": "HIGH",
                "message": f"测试成功率 {overall.get('overall_success_rate', 0):.1%} 低于90%，需要修复失败的测试用例"
            })
        
        if overall.get("validation_success_rate", 0) < 0.8:
            recommendations.append({
                "type": "validation",
                "priority": "HIGH", 
                "message": f"验证通过率 {overall.get('validation_success_rate', 0):.1%} 低于80%，需要优化性能指标"
            })
        
        # 基于性能指标的建议
        for file_analysis in self.summary_data["test_files_analyzed"]:
            for metric_name, metric_data in file_analysis["performance_metrics"].items():
                if metric_data.get("status") == "FAIL":
                    recommendations.append({
                        "type": "performance",
                        "priority": "MEDIUM",
                        "message": f"性能指标 {metric_name} 超过阈值: {metric_data.get('value')} > {metric_data.get('threshold')}"
                    })
        
        # 通用建议
        if overall.get("total_failures", 0) > 0:
            recommendations.append({
                "type": "debugging",
                "priority": "MEDIUM",
                "message": "建议启用详细日志模式以便调试失败的测试用例"
            })
        
        if not recommendations:
            recommendations.append({
                "type": "success",
                "priority": "INFO",
                "message": "所有测试通过，系统运行良好！"
            })
        
        self.summary_data["recommendations"] = recommendations
    
    def _save_summary(self):
        """保存摘要到文件"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 保存JSON格式
        json_file = self.test_output_dir / f"test_summary_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.summary_data, f, indent=2, ensure_ascii=False)
        
        # 保存文本格式
        txt_file = self.test_output_dir / f"test_summary_{timestamp}.txt"
        with open(txt_file, 'w', encoding='utf-8') as f:
            self._write_text_summary(f)
        
        print(f"测试摘要已保存: {json_file}, {txt_file}")
    
    def _write_text_summary(self, f):
        """写入文本格式摘要"""
        overall = self.summary_data["overall_summary"]
        
        f.write("VisionAI-ClipsMaster 测试结果摘要\n")
        f.write("=" * 50 + "\n\n")
        
        f.write(f"生成时间: {self.summary_data['generation_time']}\n")
        f.write(f"分析文件数: {overall.get('total_test_files', 0)}\n\n")
        
        f.write("总体结果:\n")
        f.write(f"  总测试数: {overall.get('total_tests', 0)}\n")
        f.write(f"  失败数: {overall.get('total_failures', 0)}\n")
        f.write(f"  错误数: {overall.get('total_errors', 0)}\n")
        f.write(f"  成功率: {overall.get('overall_success_rate', 0):.1%}\n")
        f.write(f"  验证通过率: {overall.get('validation_success_rate', 0):.1%}\n")
        f.write(f"  总体状态: {overall.get('overall_status', 'UNKNOWN')}\n\n")
        
        f.write("改进建议:\n")
        for i, rec in enumerate(self.summary_data["recommendations"], 1):
            f.write(f"  {i}. [{rec['priority']}] {rec['message']}\n")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="VisionAI-ClipsMaster 测试摘要生成器")
    parser.add_argument("--test-output-dir", "-d", default="test_output", help="测试输出目录")
    
    args = parser.parse_args()
    
    generator = TestSummaryGenerator(args.test_output_dir)
    summary = generator.generate_summary()
    
    # 输出简要摘要
    overall = summary["overall_summary"]
    print(f"\n{'='*50}")
    print("测试结果摘要")
    print(f"{'='*50}")
    print(f"总测试数: {overall.get('total_tests', 0)}")
    print(f"成功率: {overall.get('overall_success_rate', 0):.1%}")
    print(f"验证通过率: {overall.get('validation_success_rate', 0):.1%}")
    print(f"总体状态: {overall.get('overall_status', 'UNKNOWN')}")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()
