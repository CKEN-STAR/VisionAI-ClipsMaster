#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 全面测试执行脚本

功能:
1. 执行6大测试领域的完整测试套件
2. 生成详细的测试报告
3. 计算测试通过率和性能指标
4. 提供修复建议和优化方向
"""

import os
import sys
import time
import json
import subprocess
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class ComprehensiveTestRunner:
    """全面测试执行器"""
    
    def __init__(self):
        self.test_categories = {
            "core_functionality": {
                "name": "核心功能测试",
                "priority": "P0",
                "tests": [
                    "tests/core_functionality/test_screenplay_reconstruction.py",
                    "tests/core_functionality/test_dual_model_system.py", 
                    "tests/core_functionality/test_training_system.py"
                ],
                "target_pass_rate": 0.95
            },
            "performance": {
                "name": "性能与资源测试",
                "priority": "P0", 
                "tests": [
                    "tests/performance/test_resource_management.py"
                ],
                "target_pass_rate": 0.90
            },
            "ui_interface": {
                "name": "UI界面测试",
                "priority": "P1",
                "tests": [
                    "tests/ui_interface/test_ui_components.py"
                ],
                "target_pass_rate": 0.85
            },
            "export_compatibility": {
                "name": "导出兼容性测试", 
                "priority": "P0",
                "tests": [
                    "tests/export_compatibility/test_jianying_export.py"
                ],
                "target_pass_rate": 0.95
            },
            "exception_recovery": {
                "name": "异常处理与恢复测试",
                "priority": "P1",
                "tests": [
                    "tests/exception_recovery/test_stability_recovery.py"
                ],
                "target_pass_rate": 0.90
            },
            "security_compliance": {
                "name": "安全与合规测试",
                "priority": "P2", 
                "tests": [
                    "tests/security_compliance/test_security_compliance.py"
                ],
                "target_pass_rate": 0.80
            }
        }
        
        self.results = {}
        self.start_time = None
        self.end_time = None

    def run_all_tests(self, skip_slow_tests: bool = False) -> Dict[str, Any]:
        """运行所有测试"""
        print("🚀 开始VisionAI-ClipsMaster全面测试")
        print("=" * 80)
        
        self.start_time = time.time()
        
        # 设置环境变量
        if skip_slow_tests:
            os.environ["SKIP_LONG_TESTS"] = "true"
        
        # 按优先级执行测试
        priority_order = ["P0", "P1", "P2"]
        
        for priority in priority_order:
            print(f"\n📋 执行{priority}优先级测试...")
            
            for category_id, category_info in self.test_categories.items():
                if category_info["priority"] == priority:
                    print(f"\n🔍 {category_info['name']} ({priority})")
                    print("-" * 50)
                    
                    category_result = self._run_category_tests(category_id, category_info)
                    self.results[category_id] = category_result
                    
                    # 显示即时结果
                    self._print_category_summary(category_id, category_result)
        
        self.end_time = time.time()
        
        # 生成综合报告
        comprehensive_report = self._generate_comprehensive_report()
        
        # 保存报告
        self._save_test_report(comprehensive_report)
        
        # 显示最终结果
        self._print_final_summary(comprehensive_report)
        
        return comprehensive_report

    def _run_category_tests(self, category_id: str, category_info: Dict[str, Any]) -> Dict[str, Any]:
        """运行单个测试类别"""
        category_result = {
            "name": category_info["name"],
            "priority": category_info["priority"],
            "target_pass_rate": category_info["target_pass_rate"],
            "test_results": [],
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "skipped_tests": 0,
            "execution_time": 0,
            "pass_rate": 0.0,
            "status": "unknown"
        }
        
        start_time = time.time()
        
        for test_file in category_info["tests"]:
            print(f"  ▶️ 执行: {os.path.basename(test_file)}")
            
            test_result = self._run_single_test(test_file)
            category_result["test_results"].append(test_result)
            
            # 累计统计
            category_result["total_tests"] += test_result["total"]
            category_result["passed_tests"] += test_result["passed"]
            category_result["failed_tests"] += test_result["failed"]
            category_result["skipped_tests"] += test_result["skipped"]
        
        category_result["execution_time"] = time.time() - start_time
        
        # 计算通过率
        if category_result["total_tests"] > 0:
            category_result["pass_rate"] = category_result["passed_tests"] / category_result["total_tests"]
        
        # 确定状态
        if category_result["pass_rate"] >= category_result["target_pass_rate"]:
            category_result["status"] = "PASS"
        else:
            category_result["status"] = "FAIL"
        
        return category_result

    def _run_single_test(self, test_file: str) -> Dict[str, Any]:
        """运行单个测试文件"""
        test_result = {
            "file": test_file,
            "total": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "execution_time": 0,
            "output": "",
            "errors": []
        }
        
        start_time = time.time()
        
        try:
            # 使用pytest运行测试
            cmd = [
                sys.executable, "-m", "pytest",
                test_file,
                "-v",
                "--tb=short",
                "--json-report",
                "--json-report-file=/tmp/pytest_report.json"
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            test_result["output"] = result.stdout
            test_result["execution_time"] = time.time() - start_time
            
            # 解析pytest输出
            if result.returncode == 0:
                # 测试全部通过
                lines = result.stdout.split('\n')
                for line in lines:
                    if "passed" in line and "failed" in line:
                        # 解析统计行
                        parts = line.split()
                        for i, part in enumerate(parts):
                            if part == "passed":
                                test_result["passed"] = int(parts[i-1])
                            elif part == "failed":
                                test_result["failed"] = int(parts[i-1])
                            elif part == "skipped":
                                test_result["skipped"] = int(parts[i-1])
                        break
            else:
                # 有测试失败或错误
                test_result["errors"].append(result.stderr)
                
                # 尝试解析部分结果
                lines = result.stdout.split('\n')
                for line in lines:
                    if "FAILED" in line:
                        test_result["failed"] += 1
                    elif "PASSED" in line:
                        test_result["passed"] += 1
                    elif "SKIPPED" in line:
                        test_result["skipped"] += 1
            
            test_result["total"] = test_result["passed"] + test_result["failed"] + test_result["skipped"]
            
        except subprocess.TimeoutExpired:
            test_result["errors"].append("测试执行超时")
            test_result["execution_time"] = 300
        except Exception as e:
            test_result["errors"].append(f"测试执行异常: {str(e)}")
            test_result["execution_time"] = time.time() - start_time
        
        return test_result

    def _generate_comprehensive_report(self) -> Dict[str, Any]:
        """生成综合测试报告"""
        total_execution_time = self.end_time - self.start_time
        
        # 计算总体统计
        overall_stats = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "skipped_tests": 0,
            "total_categories": len(self.test_categories),
            "passed_categories": 0,
            "failed_categories": 0
        }
        
        for category_result in self.results.values():
            overall_stats["total_tests"] += category_result["total_tests"]
            overall_stats["passed_tests"] += category_result["passed_tests"]
            overall_stats["failed_tests"] += category_result["failed_tests"]
            overall_stats["skipped_tests"] += category_result["skipped_tests"]
            
            if category_result["status"] == "PASS":
                overall_stats["passed_categories"] += 1
            else:
                overall_stats["failed_categories"] += 1
        
        # 计算总体通过率
        overall_pass_rate = 0.0
        if overall_stats["total_tests"] > 0:
            overall_pass_rate = overall_stats["passed_tests"] / overall_stats["total_tests"]
        
        # 确定总体状态
        overall_status = "PASS" if overall_pass_rate >= 0.95 else "FAIL"
        
        # 生成性能指标
        performance_metrics = self._calculate_performance_metrics()
        
        # 生成修复建议
        fix_recommendations = self._generate_fix_recommendations()
        
        comprehensive_report = {
            "test_summary": {
                "start_time": datetime.fromtimestamp(self.start_time).isoformat(),
                "end_time": datetime.fromtimestamp(self.end_time).isoformat(),
                "execution_time": total_execution_time,
                "overall_status": overall_status,
                "overall_pass_rate": overall_pass_rate,
                "target_pass_rate": 0.95
            },
            "statistics": overall_stats,
            "category_results": self.results,
            "performance_metrics": performance_metrics,
            "fix_recommendations": fix_recommendations,
            "production_readiness": {
                "ready": overall_pass_rate >= 0.95,
                "confidence_level": self._calculate_confidence_level(overall_pass_rate),
                "deployment_recommendation": self._get_deployment_recommendation(overall_pass_rate)
            }
        }
        
        return comprehensive_report

    def _calculate_performance_metrics(self) -> Dict[str, Any]:
        """计算性能指标"""
        metrics = {
            "test_execution_efficiency": 0.0,
            "category_balance": 0.0,
            "priority_coverage": {"P0": 0, "P1": 0, "P2": 0},
            "bottleneck_categories": []
        }
        
        # 计算执行效率
        total_time = self.end_time - self.start_time
        total_tests = sum(result["total_tests"] for result in self.results.values())
        if total_tests > 0:
            metrics["test_execution_efficiency"] = total_tests / total_time
        
        # 计算优先级覆盖
        for category_result in self.results.values():
            priority = category_result["priority"]
            metrics["priority_coverage"][priority] += category_result["total_tests"]
        
        # 识别瓶颈类别
        for category_id, category_result in self.results.items():
            if category_result["execution_time"] > 60:  # 超过1分钟
                metrics["bottleneck_categories"].append({
                    "category": category_id,
                    "execution_time": category_result["execution_time"],
                    "test_count": category_result["total_tests"]
                })
        
        return metrics

    def _generate_fix_recommendations(self) -> List[Dict[str, Any]]:
        """生成修复建议"""
        recommendations = []
        
        for category_id, category_result in self.results.items():
            if category_result["status"] == "FAIL":
                recommendation = {
                    "category": category_id,
                    "priority": category_result["priority"],
                    "current_pass_rate": category_result["pass_rate"],
                    "target_pass_rate": category_result["target_pass_rate"],
                    "gap": category_result["target_pass_rate"] - category_result["pass_rate"],
                    "suggested_actions": []
                }
                
                # 根据类别生成具体建议
                if category_id == "core_functionality":
                    recommendation["suggested_actions"] = [
                        "检查AI剧本重构逻辑实现",
                        "优化双语言模型切换性能",
                        "验证训练系统数据流程"
                    ]
                elif category_id == "performance":
                    recommendation["suggested_actions"] = [
                        "优化内存使用策略",
                        "改进启动时间性能",
                        "增强资源管理机制"
                    ]
                elif category_id == "ui_interface":
                    recommendation["suggested_actions"] = [
                        "修复UI组件兼容性问题",
                        "优化界面响应时间",
                        "完善主题切换功能"
                    ]
                elif category_id == "export_compatibility":
                    recommendation["suggested_actions"] = [
                        "修复剪映导出格式问题",
                        "提高时间轴精度",
                        "完善多格式支持"
                    ]
                elif category_id == "exception_recovery":
                    recommendation["suggested_actions"] = [
                        "增强异常处理机制",
                        "改进断点续剪功能",
                        "提高恢复成功率"
                    ]
                elif category_id == "security_compliance":
                    recommendation["suggested_actions"] = [
                        "完善水印检测算法",
                        "加强数据安全保护",
                        "改进合规性检查"
                    ]
                
                recommendations.append(recommendation)
        
        return recommendations

    def _calculate_confidence_level(self, pass_rate: float) -> str:
        """计算置信度等级"""
        if pass_rate >= 0.98:
            return "Very High"
        elif pass_rate >= 0.95:
            return "High"
        elif pass_rate >= 0.90:
            return "Medium"
        elif pass_rate >= 0.80:
            return "Low"
        else:
            return "Very Low"

    def _get_deployment_recommendation(self, pass_rate: float) -> str:
        """获取部署建议"""
        if pass_rate >= 0.98:
            return "强烈推荐立即部署到生产环境"
        elif pass_rate >= 0.95:
            return "推荐部署到生产环境，建议监控关键指标"
        elif pass_rate >= 0.90:
            return "建议先部署到预生产环境进行验证"
        elif pass_rate >= 0.80:
            return "需要修复关键问题后再考虑部署"
        else:
            return "不建议部署，需要大幅改进"

    def _print_category_summary(self, category_id: str, result: Dict[str, Any]):
        """打印类别测试摘要"""
        status_emoji = "✅" if result["status"] == "PASS" else "❌"
        print(f"    {status_emoji} {result['name']}: {result['passed_tests']}/{result['total_tests']} "
              f"({result['pass_rate']:.1%}) - {result['execution_time']:.1f}s")

    def _print_final_summary(self, report: Dict[str, Any]):
        """打印最终测试摘要"""
        print("\n" + "=" * 80)
        print("🎯 VisionAI-ClipsMaster 全面测试报告")
        print("=" * 80)
        
        summary = report["test_summary"]
        stats = report["statistics"]
        
        print(f"📊 总体结果: {summary['overall_status']}")
        print(f"📈 通过率: {summary['overall_pass_rate']:.1%} (目标: {summary['target_pass_rate']:.0%})")
        print(f"⏱️ 执行时间: {summary['execution_time']:.1f}秒")
        print(f"🧪 测试统计: {stats['passed_tests']}/{stats['total_tests']} 通过")
        
        print(f"\n📋 分类结果:")
        for category_id, result in report["category_results"].items():
            status_emoji = "✅" if result["status"] == "PASS" else "❌"
            print(f"  {status_emoji} {result['name']} ({result['priority']}): {result['pass_rate']:.1%}")
        
        # 生产就绪性评估
        readiness = report["production_readiness"]
        ready_emoji = "🚀" if readiness["ready"] else "⚠️"
        print(f"\n{ready_emoji} 生产就绪性: {'是' if readiness['ready'] else '否'}")
        print(f"🎯 置信度: {readiness['confidence_level']}")
        print(f"💡 部署建议: {readiness['deployment_recommendation']}")
        
        # 修复建议
        if report["fix_recommendations"]:
            print(f"\n🔧 修复建议:")
            for rec in report["fix_recommendations"]:
                print(f"  • {rec['category']} ({rec['priority']}): 通过率差距 {rec['gap']:.1%}")

    def _save_test_report(self, report: Dict[str, Any]):
        """保存测试报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # JSON报告
        json_file = f"tests/reports/comprehensive_test_report_{timestamp}.json"
        os.makedirs(os.path.dirname(json_file), exist_ok=True)
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 详细报告已保存: {json_file}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="VisionAI-ClipsMaster 全面测试执行器")
    parser.add_argument("--skip-slow", action="store_true", help="跳过长时间测试")
    parser.add_argument("--category", help="只运行指定类别的测试")
    
    args = parser.parse_args()
    
    runner = ComprehensiveTestRunner()
    
    if args.category:
        # 运行指定类别
        if args.category in runner.test_categories:
            category_info = runner.test_categories[args.category]
            result = runner._run_category_tests(args.category, category_info)
            runner._print_category_summary(args.category, result)
        else:
            print(f"❌ 未知测试类别: {args.category}")
            print(f"可用类别: {', '.join(runner.test_categories.keys())}")
            return 1
    else:
        # 运行全部测试
        report = runner.run_all_tests(skip_slow_tests=args.skip_slow)
        
        # 返回适当的退出码
        if report["production_readiness"]["ready"]:
            return 0
        else:
            return 1


if __name__ == "__main__":
    sys.exit(main())
