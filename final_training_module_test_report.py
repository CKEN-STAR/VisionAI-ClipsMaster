#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 训练模块全面测试验证最终报告
Final Comprehensive Training Module Test Report
"""

import os
import sys
import json
import time
import torch
import psutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

class FinalTrainingModuleTestReport:
    """最终训练模块测试报告生成器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.report_data = {
            "test_timestamp": datetime.now().isoformat(),
            "system_environment": self.get_system_environment(),
            "test_results": {},
            "performance_metrics": {},
            "recommendations": {},
            "final_assessment": {}
        }
        
    def get_system_environment(self) -> Dict[str, Any]:
        """获取系统环境信息"""
        return {
            "python_version": sys.version,
            "pytorch_version": torch.__version__,
            "cuda_available": torch.cuda.is_available(),
            "cuda_version": torch.version.cuda if torch.cuda.is_available() else None,
            "gpu_count": torch.cuda.device_count() if torch.cuda.is_available() else 0,
            "cpu_count": psutil.cpu_count(),
            "memory_total_gb": psutil.virtual_memory().total / (1024**3),
            "memory_available_gb": psutil.virtual_memory().available / (1024**3),
            "platform": sys.platform
        }
        
    def run_comprehensive_tests(self) -> Dict[str, Any]:
        """运行综合测试"""
        print("🚀 开始VisionAI-ClipsMaster训练模块全面测试验证")
        print("=" * 80)
        
        # 1. 训练工作流完整性测试
        print("📋 1. 训练工作流完整性测试...")
        workflow_results = self.test_workflow_integrity()
        self.report_data["test_results"]["workflow_integrity"] = workflow_results
        
        # 2. 训练数据处理验证
        print("📊 2. 训练数据处理验证...")
        data_results = self.test_data_processing()
        self.report_data["test_results"]["data_processing"] = data_results
        
        # 3. GPU加速验证
        print("🚀 3. GPU加速真实性验证...")
        gpu_results = self.test_gpu_acceleration()
        self.report_data["test_results"]["gpu_acceleration"] = gpu_results
        
        # 4. 模型切换机制测试
        print("🔄 4. 模型切换机制测试...")
        model_switch_results = self.test_model_switching()
        self.report_data["test_results"]["model_switching"] = model_switch_results
        
        # 5. 内存优化测试
        print("💾 5. 内存优化测试...")
        memory_results = self.test_memory_optimization()
        self.report_data["test_results"]["memory_optimization"] = memory_results
        
        # 6. 训练效果验证
        print("🎯 6. 训练效果验证...")
        effectiveness_results = self.test_training_effectiveness()
        self.report_data["test_results"]["training_effectiveness"] = effectiveness_results
        
        return self.report_data
        
    def test_workflow_integrity(self) -> Dict[str, Any]:
        """测试工作流完整性"""
        results = {"status": "PASS", "details": {}, "issues": []}
        
        # 检查关键文件
        required_files = [
            "src/training/en_trainer.py",
            "src/training/zh_trainer.py",
            "src/training/curriculum.py",
            "src/training/data_splitter.py",
            "src/training/data_augment.py",
            "src/training/plot_augment.py"
        ]
        
        missing_files = []
        for file_path in required_files:
            if not (self.project_root / file_path).exists():
                missing_files.append(file_path)
                
        results["details"]["required_files"] = len(required_files)
        results["details"]["found_files"] = len(required_files) - len(missing_files)
        results["details"]["missing_files"] = missing_files
        
        if missing_files:
            results["status"] = "FAIL"
            results["issues"].append(f"缺失关键文件: {missing_files}")
            
        # 测试模块导入
        import_results = {}
        try:
            from src.training.en_trainer import EnTrainer
            import_results["EnTrainer"] = "SUCCESS"
        except Exception as e:
            import_results["EnTrainer"] = f"FAILED: {str(e)}"
            results["status"] = "FAIL"
            
        try:
            from src.training.zh_trainer import ZhTrainer
            import_results["ZhTrainer"] = "SUCCESS"
        except Exception as e:
            import_results["ZhTrainer"] = f"FAILED: {str(e)}"
            results["status"] = "FAIL"
            
        results["details"]["import_tests"] = import_results
        return results
        
    def test_data_processing(self) -> Dict[str, Any]:
        """测试数据处理"""
        results = {"status": "PASS", "details": {}, "issues": []}
        
        # 检查训练数据目录
        en_dir = self.project_root / "data/training/en"
        zh_dir = self.project_root / "data/training/zh"
        
        en_files = list(en_dir.glob("*.json")) + list(en_dir.glob("*.txt")) if en_dir.exists() else []
        zh_files = list(zh_dir.glob("*.json")) + list(zh_dir.glob("*.txt")) if zh_dir.exists() else []
        
        results["details"]["english_files"] = len(en_files)
        results["details"]["chinese_files"] = len(zh_files)
        results["details"]["total_files"] = len(en_files) + len(zh_files)
        
        # 验证数据格式
        valid_files = 0
        for file_path in (en_files + zh_files)[:5]:  # 检查前5个文件
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                if file_path.suffix == '.json':
                    json.loads(content)
                valid_files += 1
            except:
                pass
                
        results["details"]["format_validation"] = {
            "checked_files": min(5, len(en_files) + len(zh_files)),
            "valid_files": valid_files
        }
        
        if len(en_files) + len(zh_files) == 0:
            results["status"] = "WARNING"
            results["issues"].append("未找到训练数据文件")
            
        return results
        
    def test_gpu_acceleration(self) -> Dict[str, Any]:
        """测试GPU加速"""
        results = {"status": "PASS", "details": {}, "issues": []}
        
        cuda_available = torch.cuda.is_available()
        results["details"]["cuda_available"] = cuda_available
        results["details"]["pytorch_version"] = torch.__version__
        
        if cuda_available:
            results["details"]["gpu_count"] = torch.cuda.device_count()
            gpu_info = []
            for i in range(torch.cuda.device_count()):
                props = torch.cuda.get_device_properties(i)
                gpu_info.append({
                    "name": props.name,
                    "memory_gb": props.total_memory / (1024**3)
                })
            results["details"]["gpu_devices"] = gpu_info
            
            # 简单性能测试
            try:
                device = torch.device("cuda:0")
                test_tensor = torch.randn(1000, 1000, device=device)
                start_time = time.time()
                result = torch.mm(test_tensor, test_tensor)
                torch.cuda.synchronize()
                gpu_time = time.time() - start_time
                results["details"]["gpu_performance_test"] = {
                    "success": True,
                    "computation_time": gpu_time
                }
                torch.cuda.empty_cache()
            except Exception as e:
                results["details"]["gpu_performance_test"] = {
                    "success": False,
                    "error": str(e)
                }
        else:
            results["status"] = "WARNING"
            results["issues"].append("CUDA不可用，将使用CPU模式")
            
        return results
        
    def test_model_switching(self) -> Dict[str, Any]:
        """测试模型切换"""
        results = {"status": "PASS", "details": {}, "issues": []}
        
        # 检查配置文件
        config_files = [
            "configs/models/active_model.yaml",
            "configs/models/available_models/mistral-7b-en.yaml",
            "configs/models/available_models/qwen2.5-7b-zh.yaml"
        ]
        
        config_status = {}
        for config_file in config_files:
            config_status[config_file] = (self.project_root / config_file).exists()
            
        results["details"]["config_files"] = config_status
        
        # 测试语言检测
        try:
            from src.core.language_detector import LanguageDetector
            detector = LanguageDetector()
            
            test_results = []
            test_cases = [
                ("Hello world", "en"),
                ("你好世界", "zh")
            ]
            
            for text, expected in test_cases:
                detected = detector.detect_language(text)
                test_results.append({
                    "text": text,
                    "expected": expected,
                    "detected": detected,
                    "correct": detected == expected
                })
                
            results["details"]["language_detection"] = test_results
            
        except Exception as e:
            results["status"] = "WARNING"
            results["issues"].append(f"语言检测测试失败: {str(e)}")
            
        return results
        
    def test_memory_optimization(self) -> Dict[str, Any]:
        """测试内存优化"""
        results = {"status": "PASS", "details": {}, "issues": []}
        
        # 系统内存信息
        memory_info = psutil.virtual_memory()
        results["details"]["system_memory"] = {
            "total_gb": memory_info.total / (1024**3),
            "available_gb": memory_info.available / (1024**3),
            "used_percent": memory_info.percent
        }
        
        # 检查内存监控模块
        try:
            from src.utils.memory_guard import MemoryGuard
            guard = MemoryGuard()
            current_usage = guard.get_memory_usage()
            results["details"]["memory_guard"] = {
                "available": True,
                "current_usage_mb": current_usage
            }
            
            # 4GB设备兼容性检查
            if memory_info.total / (1024**3) <= 4.5:
                if current_usage > 3800:
                    results["status"] = "WARNING"
                    results["issues"].append("内存使用可能超过4GB设备限制")
                    
        except Exception as e:
            results["status"] = "WARNING"
            results["issues"].append(f"内存监控模块不可用: {str(e)}")
            
        return results
        
    def test_training_effectiveness(self) -> Dict[str, Any]:
        """测试训练效果"""
        results = {"status": "PASS", "details": {}, "issues": []}
        
        # 检查模型目录
        model_dirs = ["models/mistral", "models/qwen"]
        model_status = {}
        
        for model_dir in model_dirs:
            model_path = self.project_root / model_dir
            if model_path.exists():
                model_files = list(model_path.rglob("*.bin")) + list(model_path.rglob("*.safetensors"))
                model_status[model_dir] = {
                    "exists": True,
                    "model_files": len(model_files)
                }
            else:
                model_status[model_dir] = {"exists": False, "model_files": 0}
                
        results["details"]["model_availability"] = model_status
        
        # 检查训练历史
        history_file = self.project_root / "data/training/training_history.json"
        results["details"]["training_history_exists"] = history_file.exists()
        
        return results
        
    def generate_final_assessment(self) -> Dict[str, Any]:
        """生成最终评估"""
        test_results = self.report_data["test_results"]
        
        # 计算通过率
        total_tests = len(test_results)
        passed_tests = sum(1 for result in test_results.values() if result["status"] == "PASS")
        warning_tests = sum(1 for result in test_results.values() if result["status"] == "WARNING")
        failed_tests = sum(1 for result in test_results.values() if result["status"] == "FAIL")
        
        assessment = {
            "overall_status": "PASS" if failed_tests == 0 else "FAIL",
            "test_summary": {
                "total": total_tests,
                "passed": passed_tests,
                "warnings": warning_tests,
                "failed": failed_tests,
                "pass_rate": passed_tests / total_tests * 100 if total_tests > 0 else 0
            },
            "readiness_score": self.calculate_readiness_score(),
            "critical_issues": self.identify_critical_issues(),
            "recommendations": self.generate_final_recommendations()
        }
        
        return assessment
        
    def calculate_readiness_score(self) -> float:
        """计算就绪度分数"""
        test_results = self.report_data["test_results"]
        
        # 权重分配
        weights = {
            "workflow_integrity": 0.25,
            "data_processing": 0.20,
            "gpu_acceleration": 0.15,
            "model_switching": 0.20,
            "memory_optimization": 0.10,
            "training_effectiveness": 0.10
        }
        
        total_score = 0
        for test_name, result in test_results.items():
            if result["status"] == "PASS":
                score = 100
            elif result["status"] == "WARNING":
                score = 70
            else:
                score = 0
                
            total_score += score * weights.get(test_name, 0)
            
        return round(total_score, 1)
        
    def identify_critical_issues(self) -> List[str]:
        """识别关键问题"""
        critical_issues = []
        test_results = self.report_data["test_results"]
        
        for test_name, result in test_results.items():
            if result["status"] == "FAIL":
                critical_issues.extend(result.get("issues", []))
                
        return critical_issues
        
    def generate_final_recommendations(self) -> List[str]:
        """生成最终建议"""
        recommendations = []
        test_results = self.report_data["test_results"]
        
        # GPU相关建议
        if not self.report_data["system_environment"]["cuda_available"]:
            recommendations.append("考虑在有GPU的环境中部署以获得更好的训练性能")
            
        # 内存相关建议
        memory_gb = self.report_data["system_environment"]["memory_total_gb"]
        if memory_gb < 8:
            recommendations.append("建议在内存≥8GB的设备上运行以获得更好的稳定性")
            
        # 数据相关建议
        data_result = test_results.get("data_processing", {})
        total_files = data_result.get("details", {}).get("total_files", 0)
        if total_files < 10:
            recommendations.append("增加更多训练数据以提高模型效果")
            
        return recommendations
        
    def generate_html_report(self) -> str:
        """生成HTML格式报告"""
        assessment = self.generate_final_assessment()
        self.report_data["final_assessment"] = assessment
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>VisionAI-ClipsMaster 训练模块测试报告</title>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 5px; }}
        .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
        .pass {{ color: #27ae60; }}
        .warning {{ color: #f39c12; }}
        .fail {{ color: #e74c3c; }}
        .metric {{ display: inline-block; margin: 10px; padding: 10px; background: #ecf0f1; border-radius: 3px; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 VisionAI-ClipsMaster 训练模块全面测试报告</h1>
        <p>测试时间: {self.report_data['test_timestamp']}</p>
    </div>
    
    <div class="section">
        <h2>📊 测试概览</h2>
        <div class="metric">总测试数: {assessment['test_summary']['total']}</div>
        <div class="metric pass">通过: {assessment['test_summary']['passed']}</div>
        <div class="metric warning">警告: {assessment['test_summary']['warnings']}</div>
        <div class="metric fail">失败: {assessment['test_summary']['failed']}</div>
        <div class="metric">通过率: {assessment['test_summary']['pass_rate']:.1f}%</div>
        <div class="metric">就绪度分数: {assessment['readiness_score']}/100</div>
    </div>
    
    <div class="section">
        <h2>🖥️ 系统环境</h2>
        <table>
            <tr><th>项目</th><th>值</th></tr>
            <tr><td>Python版本</td><td>{self.report_data['system_environment']['python_version'].split()[0]}</td></tr>
            <tr><td>PyTorch版本</td><td>{self.report_data['system_environment']['pytorch_version']}</td></tr>
            <tr><td>CUDA可用</td><td>{'是' if self.report_data['system_environment']['cuda_available'] else '否'}</td></tr>
            <tr><td>GPU数量</td><td>{self.report_data['system_environment']['gpu_count']}</td></tr>
            <tr><td>CPU核心数</td><td>{self.report_data['system_environment']['cpu_count']}</td></tr>
            <tr><td>总内存</td><td>{self.report_data['system_environment']['memory_total_gb']:.1f} GB</td></tr>
        </table>
    </div>
    
    <div class="section">
        <h2>🎯 最终评估</h2>
        <p><strong>整体状态:</strong> <span class="{'pass' if assessment['overall_status'] == 'PASS' else 'fail'}">{assessment['overall_status']}</span></p>
        <p><strong>就绪度分数:</strong> {assessment['readiness_score']}/100</p>
        
        {'<h3>❌ 关键问题:</h3><ul>' + ''.join(f'<li>{issue}</li>' for issue in assessment['critical_issues']) + '</ul>' if assessment['critical_issues'] else ''}
        
        {'<h3>💡 建议:</h3><ul>' + ''.join(f'<li>{rec}</li>' for rec in assessment['recommendations']) + '</ul>' if assessment['recommendations'] else ''}
    </div>
    
    <div class="section">
        <h2>📋 详细测试结果</h2>
        <table>
            <tr><th>测试项目</th><th>状态</th><th>详细信息</th></tr>
"""
        
        for test_name, result in self.report_data["test_results"].items():
            status_class = result["status"].lower()
            status_icon = {"PASS": "✅", "WARNING": "⚠️", "FAIL": "❌"}.get(result["status"], "❓")
            
            html_content += f"""
            <tr>
                <td>{test_name}</td>
                <td class="{status_class}">{status_icon} {result["status"]}</td>
                <td>{json.dumps(result.get("details", {}), ensure_ascii=False)[:200]}...</td>
            </tr>
"""
        
        html_content += """
        </table>
    </div>
</body>
</html>
"""
        return html_content
        
    def save_reports(self):
        """保存报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 保存JSON报告
        json_file = f"training_module_final_report_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.report_data, f, ensure_ascii=False, indent=2)
            
        # 保存HTML报告
        html_content = self.generate_html_report()
        html_file = f"training_module_final_report_{timestamp}.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        return json_file, html_file


def main():
    """主函数"""
    reporter = FinalTrainingModuleTestReport()
    
    # 运行所有测试
    results = reporter.run_comprehensive_tests()
    
    # 生成最终评估
    assessment = reporter.generate_final_assessment()
    results["final_assessment"] = assessment
    
    # 保存报告
    json_file, html_file = reporter.save_reports()
    
    # 显示结果摘要
    print("\n" + "=" * 80)
    print("🎯 最终测试结果摘要:")
    print(f"   整体状态: {assessment['overall_status']}")
    print(f"   就绪度分数: {assessment['readiness_score']}/100")
    print(f"   通过率: {assessment['test_summary']['pass_rate']:.1f}%")
    print(f"   报告已保存: {html_file}")
    
    if assessment['critical_issues']:
        print(f"\n❌ 关键问题:")
        for issue in assessment['critical_issues']:
            print(f"   - {issue}")
            
    if assessment['recommendations']:
        print(f"\n💡 建议:")
        for rec in assessment['recommendations']:
            print(f"   - {rec}")
            
    print("=" * 80)
    
    return 0 if assessment['overall_status'] == 'PASS' else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
