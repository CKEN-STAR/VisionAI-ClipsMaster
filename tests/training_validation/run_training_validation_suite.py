#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
训练验证系统主运行脚本
整合所有训练验证测试，生成综合报告
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
from tests.training_validation.test_training_effectiveness import TrainingEffectivenessTest
from tests.training_validation.test_gpu_acceleration import GPUAccelerationTest
from tests.training_validation.test_quality_metrics import QualityMetricsTest

class TrainingValidationSuite:
    """训练验证系统主类"""
    
    def __init__(self):
        """初始化验证系统"""
        self.start_time = time.time()
        self.results = {
            "suite_info": {
                "start_time": datetime.now().isoformat(),
                "version": "1.0.0",
                "description": "VisionAI-ClipsMaster训练模块验证系统"
            },
            "test_results": {},
            "summary": {},
            "recommendations": []
        }
        
        # 设置日志
        self._setup_logging()
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("=" * 60)
        self.logger.info("VisionAI-ClipsMaster 训练验证系统启动")
        self.logger.info("=" * 60)
    
    def _setup_logging(self):
        """设置日志系统"""
        log_dir = os.path.join(PROJECT_ROOT, "logs")
        os.makedirs(log_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(log_dir, f"training_validation_{timestamp}.log")
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    def run_all_tests(self) -> Dict[str, Any]:
        """运行所有训练验证测试"""
        self.logger.info("开始执行完整的训练验证测试套件...")
        
        test_modules = [
            ("training_effectiveness", TrainingEffectivenessTest),
            ("gpu_acceleration", GPUAccelerationTest),
            ("quality_metrics", QualityMetricsTest)
        ]
        
        for test_name, test_class in test_modules:
            self.logger.info(f"\n{'='*50}")
            self.logger.info(f"执行测试模块: {test_name}")
            self.logger.info(f"{'='*50}")
            
            try:
                result = self._run_test_module(test_class, test_name)
                self.results["test_results"][test_name] = result
                
                if result["success"]:
                    self.logger.info(f"✅ {test_name} 测试完成")
                else:
                    self.logger.error(f"❌ {test_name} 测试失败: {result.get('error', '未知错误')}")
                    
            except Exception as e:
                error_msg = f"测试模块 {test_name} 执行异常: {str(e)}"
                self.logger.error(error_msg)
                self.logger.error(traceback.format_exc())
                
                self.results["test_results"][test_name] = {
                    "success": False,
                    "error": error_msg,
                    "traceback": traceback.format_exc()
                }
        
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
            # 创建测试套件
            suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
            
            # 运行测试
            runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
            test_result = runner.run(suite)
            
            # 收集结果
            result = {
                "success": test_result.wasSuccessful(),
                "tests_run": test_result.testsRun,
                "failures": len(test_result.failures),
                "errors": len(test_result.errors),
                "skipped": len(test_result.skipped) if hasattr(test_result, 'skipped') else 0,
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
    
    def _generate_summary(self):
        """生成测试结果摘要"""
        total_tests = 0
        total_failures = 0
        total_errors = 0
        successful_modules = 0
        
        for module_name, result in self.results["test_results"].items():
            if result.get("success", False):
                successful_modules += 1
            
            total_tests += result.get("tests_run", 0)
            total_failures += result.get("failures", 0)
            total_errors += result.get("errors", 0)
        
        end_time = time.time()
        duration = end_time - self.start_time
        
        self.results["summary"] = {
            "total_modules": len(self.results["test_results"]),
            "successful_modules": successful_modules,
            "total_tests": total_tests,
            "total_failures": total_failures,
            "total_errors": total_errors,
            "success_rate": (total_tests - total_failures - total_errors) / total_tests if total_tests > 0 else 0,
            "duration_seconds": duration,
            "overall_success": total_failures == 0 and total_errors == 0
        }
        
        # 记录摘要
        summary = self.results["summary"]
        self.logger.info(f"\n{'='*60}")
        self.logger.info("测试结果摘要")
        self.logger.info(f"{'='*60}")
        self.logger.info(f"总模块数: {summary['total_modules']}")
        self.logger.info(f"成功模块: {summary['successful_modules']}")
        self.logger.info(f"总测试数: {summary['total_tests']}")
        self.logger.info(f"失败测试: {summary['total_failures']}")
        self.logger.info(f"错误测试: {summary['total_errors']}")
        self.logger.info(f"成功率: {summary['success_rate']:.1%}")
        self.logger.info(f"总耗时: {summary['duration_seconds']:.1f}秒")
        self.logger.info(f"整体状态: {'✅ 成功' if summary['overall_success'] else '❌ 失败'}")
    
    def _generate_recommendations(self):
        """生成优化建议"""
        recommendations = []
        
        # 分析测试结果并生成建议
        test_results = self.results["test_results"]
        
        # 训练效果建议
        if "training_effectiveness" in test_results:
            effectiveness_result = test_results["training_effectiveness"]
            if not effectiveness_result.get("success", False):
                recommendations.append({
                    "category": "训练效果",
                    "priority": "高",
                    "issue": "训练效果验证失败",
                    "recommendation": "检查训练数据质量和模型配置，确保训练环境正确设置"
                })
        
        # GPU加速建议
        if "gpu_acceleration" in test_results:
            gpu_result = test_results["gpu_acceleration"]
            if not gpu_result.get("success", False):
                recommendations.append({
                    "category": "GPU加速",
                    "priority": "中",
                    "issue": "GPU加速测试失败",
                    "recommendation": "检查GPU驱动和CUDA环境，确保GPU可用性"
                })
        
        # 质量指标建议
        if "quality_metrics" in test_results:
            quality_result = test_results["quality_metrics"]
            if not quality_result.get("success", False):
                recommendations.append({
                    "category": "质量指标",
                    "priority": "中",
                    "issue": "质量指标计算失败",
                    "recommendation": "检查评估算法实现，确保指标计算的准确性"
                })
        
        # 通用建议
        summary = self.results["summary"]
        if summary["success_rate"] < 0.8:
            recommendations.append({
                "category": "整体质量",
                "priority": "高",
                "issue": f"测试成功率过低: {summary['success_rate']:.1%}",
                "recommendation": "全面检查训练模块实现，重点关注失败的测试用例"
            })
        
        if summary["duration_seconds"] > 300:  # 5分钟
            recommendations.append({
                "category": "性能优化",
                "priority": "低",
                "issue": f"测试执行时间过长: {summary['duration_seconds']:.1f}秒",
                "recommendation": "优化测试用例和训练算法，提高执行效率"
            })
        
        # 如果没有问题，给出积极建议
        if not recommendations:
            recommendations.append({
                "category": "系统状态",
                "priority": "信息",
                "issue": "所有测试通过",
                "recommendation": "训练系统运行良好，可以考虑增加更多测试用例以提高覆盖率"
            })
        
        self.results["recommendations"] = recommendations
        
        # 记录建议
        self.logger.info(f"\n{'='*60}")
        self.logger.info("优化建议")
        self.logger.info(f"{'='*60}")
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
            json_file = os.path.join(output_dir, f"training_validation_report_{timestamp}.json")
            
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False)
            
            # 生成HTML报告
            html_file = os.path.join(output_dir, f"training_validation_report_{timestamp}.html")
            self._generate_html_report(html_file)
            
            self.logger.info(f"\n📊 综合测试报告已生成:")
            self.logger.info(f"   JSON报告: {json_file}")
            self.logger.info(f"   HTML报告: {html_file}")
            
        except Exception as e:
            self.logger.error(f"保存测试报告失败: {e}")
    
    def _generate_html_report(self, html_file: str):
        """生成HTML格式的测试报告"""
        try:
            summary = self.results["summary"]
            
            html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VisionAI-ClipsMaster 训练验证报告</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .summary {{ background-color: #e8f5e8; padding: 15px; margin: 20px 0; border-radius: 5px; }}
        .error {{ background-color: #ffe8e8; }}
        .success {{ color: green; }}
        .failure {{ color: red; }}
        .recommendation {{ background-color: #fff3cd; padding: 10px; margin: 10px 0; border-radius: 3px; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>VisionAI-ClipsMaster 训练验证报告</h1>
        <p>生成时间: {self.results['suite_info']['end_time']}</p>
        <p>测试版本: {self.results['suite_info']['version']}</p>
    </div>
    
    <div class="summary {'success' if summary['overall_success'] else 'error'}">
        <h2>测试摘要</h2>
        <p><strong>整体状态:</strong> {'✅ 成功' if summary['overall_success'] else '❌ 失败'}</p>
        <p><strong>成功率:</strong> {summary['success_rate']:.1%}</p>
        <p><strong>总测试数:</strong> {summary['total_tests']}</p>
        <p><strong>失败数:</strong> {summary['total_failures']}</p>
        <p><strong>错误数:</strong> {summary['total_errors']}</p>
        <p><strong>执行时间:</strong> {summary['duration_seconds']:.1f}秒</p>
    </div>
    
    <h2>详细结果</h2>
    <table>
        <tr>
            <th>测试模块</th>
            <th>状态</th>
            <th>测试数</th>
            <th>失败数</th>
            <th>错误数</th>
        </tr>
"""
            
            for module_name, result in self.results["test_results"].items():
                status = "✅ 成功" if result.get("success", False) else "❌ 失败"
                status_class = "success" if result.get("success", False) else "failure"
                
                html_content += f"""
        <tr>
            <td>{module_name}</td>
            <td class="{status_class}">{status}</td>
            <td>{result.get('tests_run', 0)}</td>
            <td>{result.get('failures', 0)}</td>
            <td>{result.get('errors', 0)}</td>
        </tr>
"""
            
            html_content += """
    </table>
    
    <h2>优化建议</h2>
"""
            
            for i, rec in enumerate(self.results["recommendations"], 1):
                html_content += f"""
    <div class="recommendation">
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

def main():
    """主函数"""
    try:
        # 创建并运行验证系统
        validation_suite = TrainingValidationSuite()
        results = validation_suite.run_all_tests()
        
        # 返回退出码
        if results["summary"]["overall_success"]:
            print("\n🎉 所有训练验证测试通过！")
            sys.exit(0)
        else:
            print("\n⚠️  部分训练验证测试失败，请查看详细报告")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 训练验证系统执行失败: {e}")
        traceback.print_exc()
        sys.exit(2)

if __name__ == "__main__":
    main()
