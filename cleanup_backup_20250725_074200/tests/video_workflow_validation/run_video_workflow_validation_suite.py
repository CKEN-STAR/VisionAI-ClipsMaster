#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频处理工作流验证系统主运行脚本
整合所有视频工作流测试，生成综合报告
"""

import os
import sys
import json
import time
import logging
import unittest
import traceback
from typing import Dict, List, Any, Optional
from datetime import datetime

# 添加项目路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

# 导入测试模块
from tests.video_workflow_validation.test_end_to_end_workflow import EndToEndWorkflowTest
from tests.video_workflow_validation.test_video_format_compatibility import VideoFormatCompatibilityTest
from tests.video_workflow_validation.test_quality_validation import QualityValidationTest
from tests.video_workflow_validation.test_ui_integration import UIIntegrationTest
from tests.video_workflow_validation.test_exception_handling import ExceptionHandlingTest

class VideoWorkflowValidationSuite:
    """视频工作流验证系统主类"""
    
    def __init__(self):
        """初始化验证系统"""
        self.start_time = time.time()
        self.results = {
            "suite_info": {
                "start_time": datetime.now().isoformat(),
                "version": "1.0.0",
                "description": "VisionAI-ClipsMaster视频处理工作流验证系统"
            },
            "test_results": {},
            "performance_metrics": {},
            "summary": {},
            "recommendations": []
        }
        
        # 设置日志
        self._setup_logging()
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("=" * 70)
        self.logger.info("VisionAI-ClipsMaster 视频工作流验证系统启动")
        self.logger.info("=" * 70)
    
    def _setup_logging(self):
        """设置日志系统"""
        log_dir = os.path.join(PROJECT_ROOT, "logs")
        os.makedirs(log_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(log_dir, f"video_workflow_validation_{timestamp}.log")
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    def run_all_tests(self) -> Dict[str, Any]:
        """运行所有视频工作流验证测试"""
        self.logger.info("开始执行完整的视频工作流验证测试套件...")
        
        test_modules = [
            ("end_to_end_workflow", EndToEndWorkflowTest, "端到端工作流测试"),
            ("video_format_compatibility", VideoFormatCompatibilityTest, "视频格式兼容性测试"),
            ("quality_validation", QualityValidationTest, "质量验证测试"),
            ("ui_integration", UIIntegrationTest, "UI界面集成测试"),
            ("exception_handling", ExceptionHandlingTest, "异常处理测试")
        ]
        
        for test_name, test_class, description in test_modules:
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"执行测试模块: {description}")
            self.logger.info(f"{'='*60}")
            
            try:
                result = self._run_test_module(test_class, test_name)
                self.results["test_results"][test_name] = result
                
                if result["success"]:
                    self.logger.info(f"✅ {description} 完成")
                else:
                    self.logger.error(f"❌ {description} 失败: {result.get('error', '未知错误')}")
                    
            except Exception as e:
                error_msg = f"测试模块 {test_name} 执行异常: {str(e)}"
                self.logger.error(error_msg)
                self.logger.error(traceback.format_exc())
                
                self.results["test_results"][test_name] = {
                    "success": False,
                    "error": error_msg,
                    "traceback": traceback.format_exc()
                }
        
        # 生成性能指标
        self._generate_performance_metrics()
        
        # 生成综合分析
        self._generate_summary()
        
        # 生成建议
        self._generate_recommendations()
        
        # 保存结果
        self._save_comprehensive_report()
        
        return self.results
    
    def _run_test_module(self, test_class, test_name: str) -> Dict[str, Any]:
        """运行单个测试模块"""
        try:
            # 记录开始时间
            module_start_time = time.time()
            
            # 创建测试套件
            suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
            
            # 运行测试
            runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
            test_result = runner.run(suite)
            
            # 记录结束时间
            module_end_time = time.time()
            module_duration = module_end_time - module_start_time
            
            # 收集结果
            result = {
                "success": test_result.wasSuccessful(),
                "tests_run": test_result.testsRun,
                "failures": len(test_result.failures),
                "errors": len(test_result.errors),
                "skipped": len(test_result.skipped) if hasattr(test_result, 'skipped') else 0,
                "duration": module_duration,
                "details": {
                    "failures": [str(failure) for failure in test_result.failures],
                    "errors": [str(error) for error in test_result.errors]
                }
            }
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            }
    
    def _generate_performance_metrics(self):
        """生成性能指标"""
        try:
            total_duration = time.time() - self.start_time
            
            # 收集各模块的性能数据
            module_durations = {}
            total_tests = 0
            
            for module_name, result in self.results["test_results"].items():
                if result.get("success") is not None:
                    module_durations[module_name] = result.get("duration", 0)
                    total_tests += result.get("tests_run", 0)
            
            # 计算性能指标
            self.results["performance_metrics"] = {
                "total_duration": total_duration,
                "total_tests": total_tests,
                "avg_test_duration": total_duration / total_tests if total_tests > 0 else 0,
                "module_durations": module_durations,
                "fastest_module": min(module_durations.items(), key=lambda x: x[1]) if module_durations else None,
                "slowest_module": max(module_durations.items(), key=lambda x: x[1]) if module_durations else None,
                "performance_score": self._calculate_performance_score(module_durations, total_duration)
            }
            
        except Exception as e:
            self.logger.error(f"生成性能指标失败: {e}")
            self.results["performance_metrics"] = {"error": str(e)}
    
    def _calculate_performance_score(self, module_durations: Dict[str, float], total_duration: float) -> float:
        """计算性能分数"""
        try:
            # 基于预期时间计算性能分数
            expected_durations = {
                "end_to_end_workflow": 120,      # 2分钟
                "video_format_compatibility": 180, # 3分钟
                "quality_validation": 150,        # 2.5分钟
                "ui_integration": 60,             # 1分钟
                "exception_handling": 90          # 1.5分钟
            }
            
            total_expected = sum(expected_durations.values())
            performance_ratio = total_expected / total_duration if total_duration > 0 else 0
            
            # 转换为0-100分数
            return min(100, max(0, performance_ratio * 100))
            
        except Exception as e:
            self.logger.error(f"计算性能分数失败: {e}")
            return 0.0
    
    def _generate_summary(self):
        """生成测试结果摘要"""
        total_modules = len(self.results["test_results"])
        successful_modules = 0
        total_tests = 0
        total_failures = 0
        total_errors = 0
        
        for module_name, result in self.results["test_results"].items():
            if result.get("success", False):
                successful_modules += 1
            
            total_tests += result.get("tests_run", 0)
            total_failures += result.get("failures", 0)
            total_errors += result.get("errors", 0)
        
        end_time = time.time()
        duration = end_time - self.start_time
        
        self.results["summary"] = {
            "total_modules": total_modules,
            "successful_modules": successful_modules,
            "module_success_rate": successful_modules / total_modules if total_modules > 0 else 0,
            "total_tests": total_tests,
            "total_failures": total_failures,
            "total_errors": total_errors,
            "test_success_rate": (total_tests - total_failures - total_errors) / total_tests if total_tests > 0 else 0,
            "duration_seconds": duration,
            "overall_success": total_failures == 0 and total_errors == 0 and successful_modules == total_modules
        }
        
        # 记录摘要
        summary = self.results["summary"]
        self.logger.info(f"\n{'='*70}")
        self.logger.info("视频工作流验证结果摘要")
        self.logger.info(f"{'='*70}")
        self.logger.info(f"总模块数: {summary['total_modules']}")
        self.logger.info(f"成功模块: {summary['successful_modules']}")
        self.logger.info(f"模块成功率: {summary['module_success_rate']:.1%}")
        self.logger.info(f"总测试数: {summary['total_tests']}")
        self.logger.info(f"失败测试: {summary['total_failures']}")
        self.logger.info(f"错误测试: {summary['total_errors']}")
        self.logger.info(f"测试成功率: {summary['test_success_rate']:.1%}")
        self.logger.info(f"总耗时: {summary['duration_seconds']:.1f}秒")
        self.logger.info(f"整体状态: {'✅ 成功' if summary['overall_success'] else '❌ 失败'}")
    
    def _generate_recommendations(self):
        """生成优化建议"""
        recommendations = []
        
        # 分析测试结果并生成建议
        test_results = self.results["test_results"]
        performance_metrics = self.results["performance_metrics"]
        
        # 端到端工作流建议
        if "end_to_end_workflow" in test_results:
            workflow_result = test_results["end_to_end_workflow"]
            if not workflow_result.get("success", False):
                recommendations.append({
                    "category": "端到端工作流",
                    "priority": "高",
                    "issue": "端到端工作流测试失败",
                    "recommendation": "检查视频处理管道和字幕重构服务的集成，确保工作流各阶段正常运行"
                })
        
        # 视频格式兼容性建议
        if "video_format_compatibility" in test_results:
            format_result = test_results["video_format_compatibility"]
            if not format_result.get("success", False):
                recommendations.append({
                    "category": "格式兼容性",
                    "priority": "中",
                    "issue": "视频格式兼容性测试失败",
                    "recommendation": "增强视频格式检测和转换功能，支持更多主流视频格式"
                })
        
        # 质量验证建议
        if "quality_validation" in test_results:
            quality_result = test_results["quality_validation"]
            if not quality_result.get("success", False):
                recommendations.append({
                    "category": "视频质量",
                    "priority": "高",
                    "issue": "视频质量验证失败",
                    "recommendation": "优化视频处理算法，确保输出质量和字幕同步精度"
                })
        
        # UI集成建议
        if "ui_integration" in test_results:
            ui_result = test_results["ui_integration"]
            if not ui_result.get("success", False):
                recommendations.append({
                    "category": "用户界面",
                    "priority": "中",
                    "issue": "UI集成测试失败",
                    "recommendation": "改进用户界面响应性和错误处理，提升用户体验"
                })
        
        # 异常处理建议
        if "exception_handling" in test_results:
            exception_result = test_results["exception_handling"]
            if not exception_result.get("success", False):
                recommendations.append({
                    "category": "异常处理",
                    "priority": "高",
                    "issue": "异常处理测试失败",
                    "recommendation": "加强异常处理机制和恢复策略，提高系统稳定性"
                })
        
        # 性能建议
        if performance_metrics.get("performance_score", 0) < 70:
            recommendations.append({
                "category": "性能优化",
                "priority": "中",
                "issue": f"系统性能分数较低: {performance_metrics.get('performance_score', 0):.1f}",
                "recommendation": "优化视频处理算法和内存管理，提高处理速度"
            })
        
        # 如果没有问题，给出积极建议
        if not recommendations:
            recommendations.append({
                "category": "系统状态",
                "priority": "信息",
                "issue": "所有测试通过",
                "recommendation": "视频工作流系统运行良好，可以考虑增加更多测试用例和性能优化"
            })
        
        self.results["recommendations"] = recommendations
        
        # 记录建议
        self.logger.info(f"\n{'='*70}")
        self.logger.info("优化建议")
        self.logger.info(f"{'='*70}")
        for i, rec in enumerate(recommendations, 1):
            self.logger.info(f"{i}. [{rec['priority']}] {rec['category']}: {rec['issue']}")
            self.logger.info(f"   建议: {rec['recommendation']}")
    
    def _save_comprehensive_report(self):
        """保存综合测试报告"""
        try:
            # 更新结束时间
            self.results["suite_info"]["end_time"] = datetime.now().isoformat()
            self.results["suite_info"]["duration_seconds"] = time.time() - self.start_time
            
            # 保存JSON报告
            output_dir = os.path.join(PROJECT_ROOT, "test_output")
            os.makedirs(output_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            json_file = os.path.join(output_dir, f"video_workflow_validation_report_{timestamp}.json")
            
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False)
            
            # 生成HTML报告
            html_file = os.path.join(output_dir, f"video_workflow_validation_report_{timestamp}.html")
            self._generate_html_report(html_file)
            
            # 生成性能基准报告
            benchmark_file = os.path.join(output_dir, f"performance_benchmark_{timestamp}.json")
            self._generate_benchmark_report(benchmark_file)
            
            self.logger.info(f"\n📊 综合测试报告已生成:")
            self.logger.info(f"   JSON报告: {json_file}")
            self.logger.info(f"   HTML报告: {html_file}")
            self.logger.info(f"   性能基准: {benchmark_file}")
            
        except Exception as e:
            self.logger.error(f"保存测试报告失败: {e}")
    
    def _generate_html_report(self, html_file: str):
        """生成HTML格式的测试报告"""
        try:
            summary = self.results["summary"]
            performance = self.results["performance_metrics"]
            
            html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VisionAI-ClipsMaster 视频工作流验证报告</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; }}
        .summary {{ background-color: #f8f9fa; padding: 20px; margin: 20px 0; border-radius: 8px; border-left: 5px solid #007bff; }}
        .success {{ background-color: #d4edda; border-color: #28a745; }}
        .warning {{ background-color: #fff3cd; border-color: #ffc107; }}
        .error {{ background-color: #f8d7da; border-color: #dc3545; }}
        .metric-card {{ background: white; padding: 15px; margin: 10px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); display: inline-block; min-width: 200px; }}
        .recommendation {{ background-color: #e3f2fd; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #2196f3; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background-color: #f2f2f2; font-weight: bold; }}
        .status-success {{ color: #28a745; font-weight: bold; }}
        .status-error {{ color: #dc3545; font-weight: bold; }}
        .progress-bar {{ background-color: #e9ecef; border-radius: 4px; overflow: hidden; }}
        .progress-fill {{ background-color: #28a745; height: 20px; transition: width 0.3s ease; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🎬 VisionAI-ClipsMaster 视频工作流验证报告</h1>
        <p>生成时间: {self.results['suite_info']['end_time']}</p>
        <p>测试版本: {self.results['suite_info']['version']}</p>
    </div>
    
    <div class="summary {'success' if summary['overall_success'] else 'error'}">
        <h2>📊 测试摘要</h2>
        <div class="metric-card">
            <h3>整体状态</h3>
            <p class="{'status-success' if summary['overall_success'] else 'status-error'}">
                {'✅ 全部通过' if summary['overall_success'] else '❌ 存在问题'}
            </p>
        </div>
        <div class="metric-card">
            <h3>模块成功率</h3>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {summary['module_success_rate']*100:.1f}%"></div>
            </div>
            <p>{summary['module_success_rate']:.1%} ({summary['successful_modules']}/{summary['total_modules']})</p>
        </div>
        <div class="metric-card">
            <h3>测试成功率</h3>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {summary['test_success_rate']*100:.1f}%"></div>
            </div>
            <p>{summary['test_success_rate']:.1%} ({summary['total_tests'] - summary['total_failures'] - summary['total_errors']}/{summary['total_tests']})</p>
        </div>
        <div class="metric-card">
            <h3>执行时间</h3>
            <p>{summary['duration_seconds']:.1f} 秒</p>
        </div>
        <div class="metric-card">
            <h3>性能分数</h3>
            <p>{performance.get('performance_score', 0):.1f}/100</p>
        </div>
    </div>
    
    <h2>📋 详细测试结果</h2>
    <table>
        <tr>
            <th>测试模块</th>
            <th>状态</th>
            <th>测试数</th>
            <th>失败数</th>
            <th>错误数</th>
            <th>耗时(秒)</th>
        </tr>
"""
            
            module_names = {
                "end_to_end_workflow": "端到端工作流",
                "video_format_compatibility": "视频格式兼容性",
                "quality_validation": "质量验证",
                "ui_integration": "UI界面集成",
                "exception_handling": "异常处理"
            }
            
            for module_key, result in self.results["test_results"].items():
                module_name = module_names.get(module_key, module_key)
                status = "✅ 成功" if result.get("success", False) else "❌ 失败"
                status_class = "status-success" if result.get("success", False) else "status-error"
                
                html_content += f"""
        <tr>
            <td>{module_name}</td>
            <td class="{status_class}">{status}</td>
            <td>{result.get('tests_run', 0)}</td>
            <td>{result.get('failures', 0)}</td>
            <td>{result.get('errors', 0)}</td>
            <td>{result.get('duration', 0):.1f}</td>
        </tr>
"""
            
            html_content += """
    </table>
    
    <h2>💡 优化建议</h2>
"""
            
            for i, rec in enumerate(self.results["recommendations"], 1):
                priority_class = {
                    "高": "error",
                    "中": "warning", 
                    "低": "success",
                    "信息": "success"
                }.get(rec['priority'], "summary")
                
                html_content += f"""
    <div class="recommendation {priority_class}">
        <h4>{i}. [{rec['priority']}] {rec['category']}</h4>
        <p><strong>问题:</strong> {rec['issue']}</p>
        <p><strong>建议:</strong> {rec['recommendation']}</p>
    </div>
"""
            
            html_content += """
</body>
</html>
"""
            
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
                
        except Exception as e:
            self.logger.error(f"生成HTML报告失败: {e}")
    
    def _generate_benchmark_report(self, benchmark_file: str):
        """生成性能基准报告"""
        try:
            benchmark_data = {
                "timestamp": datetime.now().isoformat(),
                "system_info": {
                    "platform": sys.platform,
                    "python_version": sys.version
                },
                "performance_metrics": self.results["performance_metrics"],
                "baseline_comparison": {
                    "expected_total_duration": 600,  # 10分钟基准
                    "actual_total_duration": self.results["performance_metrics"].get("total_duration", 0),
                    "performance_ratio": self.results["performance_metrics"].get("performance_score", 0) / 100
                }
            }
            
            with open(benchmark_file, 'w', encoding='utf-8') as f:
                json.dump(benchmark_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"生成性能基准报告失败: {e}")

def main():
    """主函数"""
    try:
        # 创建并运行验证系统
        validation_suite = VideoWorkflowValidationSuite()
        results = validation_suite.run_all_tests()
        
        # 返回退出码
        if results["summary"]["overall_success"]:
            print("\n🎉 所有视频工作流验证测试通过！")
            sys.exit(0)
        else:
            print("\n⚠️  部分视频工作流验证测试失败，请查看详细报告")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 视频工作流验证系统执行失败: {e}")
        traceback.print_exc()
        sys.exit(2)

if __name__ == "__main__":
    main()
