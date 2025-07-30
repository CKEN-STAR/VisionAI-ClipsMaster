#!/usr/bin/env python3
"""
测试结果验证器
根据预期标准验证测试结果，生成详细的验证报告
"""

import json
import yaml
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime

class TestResultValidator:
    """测试结果验证器"""
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path or Path(__file__).parent / "test_config.yaml"
        self.config = self._load_config()
        self.validation_results = {
            "validation_timestamp": datetime.now().isoformat(),
            "overall_status": "unknown",
            "module_validations": {},
            "critical_failures": [],
            "warnings": [],
            "recommendations": [],
            "compliance_score": 0.0
        }
    
    def _load_config(self) -> Dict[str, Any]:
        """加载测试配置"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"警告: 无法加载配置文件 {self.config_path}: {e}")
            return {}
    
    def validate_test_results(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """验证测试结果"""
        print("🔍 开始验证测试结果...")
        
        # 1. 验证视频-字幕映射精度
        if "alignment_precision" in test_results.get("test_modules", {}):
            self._validate_alignment_precision(test_results["test_modules"]["alignment_precision"])
        
        # 2. 验证AI剧本重构功能
        if "viral_srt_generation" in test_results.get("test_modules", {}):
            self._validate_viral_srt_generation(test_results["test_modules"]["viral_srt_generation"])
        
        # 3. 验证系统集成
        if "system_integration" in test_results.get("test_modules", {}):
            self._validate_system_integration(test_results["test_modules"]["system_integration"])
        
        # 4. 验证性能指标
        if "performance_metrics" in test_results:
            self._validate_performance_metrics(test_results["performance_metrics"])
        
        # 5. 验证内存压力测试
        if "memory_stress_test" in test_results:
            self._validate_memory_stress_test(test_results["memory_stress_test"])
        
        # 6. 计算总体合规性评分
        self._calculate_compliance_score()
        
        # 7. 生成最终状态和建议
        self._generate_final_assessment()
        
        print(f"✅ 测试结果验证完成 - 合规性评分: {self.validation_results['compliance_score']:.1%}")
        
        return self.validation_results
    
    def _validate_alignment_precision(self, alignment_results: Dict[str, Any]):
        """验证视频-字幕映射精度"""
        module_name = "alignment_precision"
        config = self.config.get("alignment_precision_test", {})
        requirements = config.get("precision_requirements", {})
        
        validation = {
            "module_name": module_name,
            "status": "passed",
            "checks": [],
            "score": 0.0,
            "issues": []
        }
        
        # 检查精度指标
        precision_metrics = alignment_results.get("precision_metrics", {})
        
        # 1. 检查成功率
        success_rate = precision_metrics.get("success_rate", 0)
        min_accuracy = requirements.get("min_accuracy_rate", 0.95)
        
        check_result = {
            "check_name": "success_rate",
            "actual_value": success_rate,
            "expected_value": min_accuracy,
            "passed": success_rate >= min_accuracy,
            "weight": 0.4
        }
        validation["checks"].append(check_result)
        
        if not check_result["passed"]:
            validation["issues"].append(f"成功率不达标: {success_rate:.1%} < {min_accuracy:.1%}")
        
        # 2. 检查平均精度误差
        avg_error = precision_metrics.get("average_precision_error", 1.0)
        max_error = requirements.get("max_alignment_error_seconds", 0.5)
        
        check_result = {
            "check_name": "average_precision_error",
            "actual_value": avg_error,
            "expected_value": max_error,
            "passed": avg_error <= max_error,
            "weight": 0.4
        }
        validation["checks"].append(check_result)
        
        if not check_result["passed"]:
            validation["issues"].append(f"平均精度误差过大: {avg_error:.3f}s > {max_error:.3f}s")
        
        # 3. 检查最大精度误差
        max_precision_error = precision_metrics.get("max_precision_error", 1.0)
        
        check_result = {
            "check_name": "max_precision_error",
            "actual_value": max_precision_error,
            "expected_value": max_error,
            "passed": max_precision_error <= max_error,
            "weight": 0.2
        }
        validation["checks"].append(check_result)
        
        if not check_result["passed"]:
            validation["issues"].append(f"最大精度误差过大: {max_precision_error:.3f}s > {max_error:.3f}s")
        
        # 计算模块评分
        total_weight = sum(check["weight"] for check in validation["checks"])
        weighted_score = sum(check["weight"] if check["passed"] else 0 for check in validation["checks"])
        validation["score"] = weighted_score / total_weight if total_weight > 0 else 0
        
        # 确定模块状态
        if validation["score"] >= 0.8:
            validation["status"] = "passed"
        elif validation["score"] >= 0.6:
            validation["status"] = "warning"
        else:
            validation["status"] = "failed"
            self.validation_results["critical_failures"].append(f"{module_name}: 精度验证失败")
        
        self.validation_results["module_validations"][module_name] = validation
    
    def _validate_viral_srt_generation(self, viral_results: Dict[str, Any]):
        """验证AI剧本重构功能"""
        module_name = "viral_srt_generation"
        config = self.config.get("viral_srt_generation_test", {})
        quality_requirements = config.get("quality_requirements", {})
        
        validation = {
            "module_name": module_name,
            "status": "passed",
            "checks": [],
            "score": 0.0,
            "issues": []
        }
        
        generation_metrics = viral_results.get("generation_metrics", {})
        
        # 1. 检查生成成功率
        success_rate = generation_metrics.get("success_rate", 0)
        min_success_rate = quality_requirements.get("min_generation_success_rate", 0.9)
        
        check_result = {
            "check_name": "generation_success_rate",
            "actual_value": success_rate,
            "expected_value": min_success_rate,
            "passed": success_rate >= min_success_rate,
            "weight": 0.3
        }
        validation["checks"].append(check_result)
        
        # 2. 检查爆款特征覆盖率
        viral_coverage = generation_metrics.get("viral_feature_coverage", 0)
        min_viral_score = quality_requirements.get("min_viral_feature_score", 0.75)
        
        check_result = {
            "check_name": "viral_feature_coverage",
            "actual_value": viral_coverage,
            "expected_value": min_viral_score,
            "passed": viral_coverage >= min_viral_score,
            "weight": 0.3
        }
        validation["checks"].append(check_result)
        
        # 3. 检查整体质量评分
        overall_quality = generation_metrics.get("overall_quality_score", 0)
        min_quality = quality_requirements.get("min_text_quality_score", 0.8)
        
        check_result = {
            "check_name": "overall_quality_score",
            "actual_value": overall_quality,
            "expected_value": min_quality,
            "passed": overall_quality >= min_quality,
            "weight": 0.2
        }
        validation["checks"].append(check_result)
        
        # 4. 检查模型切换效率
        model_switching = generation_metrics.get("model_switching_efficiency", 0)
        min_switching_efficiency = 0.9
        
        check_result = {
            "check_name": "model_switching_efficiency",
            "actual_value": model_switching,
            "expected_value": min_switching_efficiency,
            "passed": model_switching >= min_switching_efficiency,
            "weight": 0.2
        }
        validation["checks"].append(check_result)
        
        # 计算评分和状态
        self._calculate_module_score_and_status(validation, module_name)
        self.validation_results["module_validations"][module_name] = validation
    
    def _validate_system_integration(self, integration_results: Dict[str, Any]):
        """验证系统集成"""
        module_name = "system_integration"
        config = self.config.get("system_integration_test", {})
        workflow_performance = config.get("workflow_performance", {})
        
        validation = {
            "module_name": module_name,
            "status": "passed",
            "checks": [],
            "score": 0.0,
            "issues": []
        }
        
        workflow_metrics = integration_results.get("workflow_metrics", {})
        
        # 1. 检查工作流成功率
        success_rate = workflow_metrics.get("success_rate", 0)
        min_workflow_success = workflow_performance.get("min_workflow_success_rate", 0.9)
        
        check_result = {
            "check_name": "workflow_success_rate",
            "actual_value": success_rate,
            "expected_value": min_workflow_success,
            "passed": success_rate >= min_workflow_success,
            "weight": 0.3
        }
        validation["checks"].append(check_result)
        
        # 2. 检查导出兼容性
        export_compatibility = workflow_metrics.get("export_compatibility", 0)
        min_export_compatibility = 0.94
        
        check_result = {
            "check_name": "export_compatibility",
            "actual_value": export_compatibility,
            "expected_value": min_export_compatibility,
            "passed": export_compatibility >= min_export_compatibility,
            "weight": 0.25
        }
        validation["checks"].append(check_result)
        
        # 3. 检查恢复可靠性
        recovery_reliability = workflow_metrics.get("recovery_reliability", 0)
        min_recovery_reliability = 0.9
        
        check_result = {
            "check_name": "recovery_reliability",
            "actual_value": recovery_reliability,
            "expected_value": min_recovery_reliability,
            "passed": recovery_reliability >= min_recovery_reliability,
            "weight": 0.2
        }
        validation["checks"].append(check_result)
        
        # 4. 检查性能效率
        performance_efficiency = workflow_metrics.get("performance_efficiency", 0)
        min_performance_efficiency = 0.85
        
        check_result = {
            "check_name": "performance_efficiency",
            "actual_value": performance_efficiency,
            "expected_value": min_performance_efficiency,
            "passed": performance_efficiency >= min_performance_efficiency,
            "weight": 0.25
        }
        validation["checks"].append(check_result)
        
        # 计算评分和状态
        self._calculate_module_score_and_status(validation, module_name)
        self.validation_results["module_validations"][module_name] = validation
    
    def _validate_performance_metrics(self, performance_metrics: Dict[str, Any]):
        """验证性能指标"""
        # 检查测试用例通过率
        test_case_success_rate = performance_metrics.get("test_case_success_rate", 0)
        if test_case_success_rate < 0.9:
            self.validation_results["warnings"].append(
                f"测试用例通过率偏低: {test_case_success_rate:.1%}"
            )
        
        # 检查模块成功率
        module_success_rate = performance_metrics.get("module_success_rate", 0)
        if module_success_rate < 1.0:
            self.validation_results["warnings"].append(
                f"模块成功率不完美: {module_success_rate:.1%}"
            )
    
    def _validate_memory_stress_test(self, memory_test: Dict[str, Any]):
        """验证内存压力测试"""
        if not memory_test.get("test_passed", False):
            self.validation_results["critical_failures"].append(
                f"内存压力测试失败: 峰值内存 {memory_test.get('peak_memory_usage_gb', 0):.2f}GB"
            )
        
        if not memory_test.get("memory_stable", True):
            self.validation_results["warnings"].append("内存使用不够稳定")
    
    def _calculate_module_score_and_status(self, validation: Dict[str, Any], module_name: str):
        """计算模块评分和状态"""
        total_weight = sum(check["weight"] for check in validation["checks"])
        weighted_score = sum(check["weight"] if check["passed"] else 0 for check in validation["checks"])
        validation["score"] = weighted_score / total_weight if total_weight > 0 else 0
        
        # 收集失败的检查
        failed_checks = [check for check in validation["checks"] if not check["passed"]]
        for check in failed_checks:
            validation["issues"].append(
                f"{check['check_name']}: {check['actual_value']} (期望: {check['expected_value']})"
            )
        
        # 确定状态
        if validation["score"] >= 0.8:
            validation["status"] = "passed"
        elif validation["score"] >= 0.6:
            validation["status"] = "warning"
            self.validation_results["warnings"].append(f"{module_name}: 部分指标不达标")
        else:
            validation["status"] = "failed"
            self.validation_results["critical_failures"].append(f"{module_name}: 验证失败")
    
    def _calculate_compliance_score(self):
        """计算总体合规性评分"""
        if not self.validation_results["module_validations"]:
            self.validation_results["compliance_score"] = 0.0
            return
        
        # 使用配置中的权重
        quality_weights = self.config.get("reporting", {}).get("quality_assessment", {}).get("overall_quality_weights", {})
        default_weight = 1.0 / len(self.validation_results["module_validations"])
        
        total_weighted_score = 0.0
        total_weight = 0.0
        
        for module_name, validation in self.validation_results["module_validations"].items():
            weight = quality_weights.get(module_name, default_weight)
            total_weighted_score += validation["score"] * weight
            total_weight += weight
        
        self.validation_results["compliance_score"] = total_weighted_score / total_weight if total_weight > 0 else 0.0
    
    def _generate_final_assessment(self):
        """生成最终评估"""
        compliance_score = self.validation_results["compliance_score"]
        critical_failures = len(self.validation_results["critical_failures"])
        
        # 确定总体状态
        if critical_failures > 0:
            self.validation_results["overall_status"] = "failed"
        elif compliance_score >= 0.8:
            self.validation_results["overall_status"] = "passed"
        elif compliance_score >= 0.6:
            self.validation_results["overall_status"] = "warning"
        else:
            self.validation_results["overall_status"] = "failed"
        
        # 生成建议
        if compliance_score < 0.6:
            self.validation_results["recommendations"].append("系统需要重大改进才能达到生产就绪状态")
        elif compliance_score < 0.8:
            self.validation_results["recommendations"].append("系统基本可用，但建议优化关键指标")
        else:
            self.validation_results["recommendations"].append("系统表现良好，可以考虑部署到生产环境")
        
        # 针对具体问题的建议
        for module_name, validation in self.validation_results["module_validations"].items():
            if validation["status"] == "failed":
                self.validation_results["recommendations"].append(f"优先修复 {module_name} 模块的关键问题")
            elif validation["status"] == "warning":
                self.validation_results["recommendations"].append(f"改进 {module_name} 模块的性能指标")
    
    def save_validation_report(self, output_path: str):
        """保存验证报告"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.validation_results, f, indent=2, ensure_ascii=False)
        
        print(f"📄 验证报告已保存: {output_file}")

def main():
    """主函数 - 用于独立运行验证器"""
    import argparse
    
    parser = argparse.ArgumentParser(description="测试结果验证器")
    parser.add_argument("test_results_file", help="测试结果JSON文件路径")
    parser.add_argument("--config", help="测试配置文件路径")
    parser.add_argument("--output", help="验证报告输出路径")
    
    args = parser.parse_args()
    
    # 加载测试结果
    with open(args.test_results_file, 'r', encoding='utf-8') as f:
        test_results = json.load(f)
    
    # 创建验证器
    validator = TestResultValidator(args.config)
    
    # 执行验证
    validation_results = validator.validate_test_results(test_results)
    
    # 保存验证报告
    if args.output:
        validator.save_validation_report(args.output)
    
    # 显示结果
    print(f"\n验证结果: {validation_results['overall_status'].upper()}")
    print(f"合规性评分: {validation_results['compliance_score']:.1%}")
    
    if validation_results['critical_failures']:
        print("\n关键失败:")
        for failure in validation_results['critical_failures']:
            print(f"  ❌ {failure}")
    
    if validation_results['warnings']:
        print("\n警告:")
        for warning in validation_results['warnings']:
            print(f"  ⚠️ {warning}")
    
    return 0 if validation_results['overall_status'] in ['passed', 'warning'] else 1

if __name__ == "__main__":
    exit(main())
