#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 基础功能完整性验证器

在进行任何修改之前，验证所有基础功能的完整性和稳定性
"""

import sys
import os
import time
import json
import subprocess
import psutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple

# 设置环境变量
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
os.environ['OMP_NUM_THREADS'] = '1'

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

class BaselineFunctionalityValidator:
    """基础功能完整性验证器"""
    
    def __init__(self):
        self.start_time = time.time()
        self.validation_results = {
            "validation_start": datetime.now().isoformat(),
            "test_environment": self._get_test_environment(),
            "validation_tests": {},
            "critical_issues": [],
            "warnings": [],
            "overall_status": "UNKNOWN"
        }
        
    def _get_test_environment(self) -> Dict[str, Any]:
        """获取测试环境信息"""
        try:
            return {
                "os": os.name,
                "python_version": sys.version,
                "total_memory_gb": round(psutil.virtual_memory().total / (1024**3), 2),
                "available_memory_gb": round(psutil.virtual_memory().available / (1024**3), 2),
                "cpu_count": psutil.cpu_count(),
                "project_root": str(project_root)
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _log_validation_result(self, test_id: str, passed: bool, details: str, 
                              issues: List = None, warnings: List = None):
        """记录验证结果"""
        self.validation_results["validation_tests"][test_id] = {
            "passed": passed,
            "details": details,
            "execution_time": datetime.now().isoformat(),
            "issues": issues or [],
            "warnings": warnings or []
        }
        
        if issues:
            self.validation_results["critical_issues"].extend(issues)
        if warnings:
            self.validation_results["warnings"].extend(warnings)
    
    def validate_program_startup(self) -> bool:
        """验证程序启动功能"""
        print("🚀 验证程序启动功能...")
        print("=" * 50)
        
        try:
            # 检查主程序文件是否存在
            main_program = Path("simple_ui_fixed.py")
            if not main_program.exists():
                self._log_validation_result(
                    "STARTUP-001", False,
                    "主程序文件不存在",
                    issues=["simple_ui_fixed.py文件缺失"]
                )
                return False
            
            print(f"  ✅ 主程序文件存在: {main_program}")
            
            # 尝试启动程序（测试模式）
            print("  🔄 测试程序启动...")
            
            # 使用subprocess启动程序并快速关闭
            try:
                process = subprocess.Popen(
                    [sys.executable, "simple_ui_fixed.py", "--test"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=str(project_root)
                )
                
                # 等待3秒看是否能正常启动
                time.sleep(3)
                
                # 检查进程状态
                if process.poll() is None:
                    # 进程仍在运行，说明启动成功
                    print("  ✅ 程序启动成功")
                    process.terminate()
                    process.wait(timeout=5)
                    startup_success = True
                else:
                    # 进程已退出，检查退出码
                    stdout, stderr = process.communicate()
                    if process.returncode == 0:
                        print("  ✅ 程序正常启动并退出")
                        startup_success = True
                    else:
                        print(f"  ❌ 程序启动失败，退出码: {process.returncode}")
                        print(f"  错误信息: {stderr.decode('utf-8', errors='ignore')}")
                        startup_success = False
                
            except subprocess.TimeoutExpired:
                print("  ⚠️ 程序启动超时")
                startup_success = False
            except Exception as e:
                print(f"  ❌ 程序启动异常: {str(e)}")
                startup_success = False
            
            self._log_validation_result(
                "STARTUP-001", startup_success,
                "程序启动验证" + ("成功" if startup_success else "失败"),
                issues=[] if startup_success else ["程序无法正常启动"]
            )
            
            return startup_success
            
        except Exception as e:
            self._log_validation_result(
                "STARTUP-001", False,
                f"程序启动验证异常: {str(e)}",
                issues=[f"启动验证异常: {str(e)}"]
            )
            return False
    
    def validate_ui_components(self) -> bool:
        """验证UI界面完整性"""
        print("\n🎨 验证UI界面完整性...")
        print("=" * 50)
        
        try:
            # 检查PyQt6可用性
            try:
                from PyQt6.QtWidgets import QApplication, QMainWindow
                print("  ✅ PyQt6导入成功")
                pyqt6_available = True
            except ImportError as e:
                print(f"  ❌ PyQt6导入失败: {e}")
                pyqt6_available = False
            
            # 检查UI组件文件
            ui_components = [
                "ui/main_window.py",
                "ui/training_panel.py", 
                "ui/progress_dashboard.py"
            ]
            
            missing_components = []
            for component in ui_components:
                if Path(component).exists():
                    print(f"  ✅ UI组件存在: {component}")
                else:
                    print(f"  ❌ UI组件缺失: {component}")
                    missing_components.append(component)
            
            # 尝试导入UI组件（仅测试导入，不实例化）
            ui_import_success = True
            try:
                # 创建临时QApplication用于测试
                from PyQt6.QtWidgets import QApplication
                import sys

                # 检查是否已有QApplication实例
                app = QApplication.instance()
                if app is None:
                    app = QApplication(sys.argv)
                    app_created = True
                else:
                    app_created = False

                if Path("ui/main_window.py").exists():
                    from ui.main_window import get_main_window
                    # 只测试导入，不实际创建实例
                    print("  ✅ 主窗口组件导入成功")

                if Path("ui/training_panel.py").exists():
                    from ui.training_panel import get_training_panel
                    # 只测试导入，不实际创建实例
                    print("  ✅ 训练面板组件导入成功")

                if Path("ui/progress_dashboard.py").exists():
                    from ui.progress_dashboard import get_progress_dashboard
                    # 只测试导入，不实际创建实例
                    print("  ✅ 进度仪表板组件导入成功")

                # 清理临时QApplication
                if app_created:
                    app.quit()

            except Exception as e:
                print(f"  ❌ UI组件导入失败: {e}")
                ui_import_success = False
            
            overall_ui_success = pyqt6_available and len(missing_components) == 0 and ui_import_success
            
            issues = []
            if not pyqt6_available:
                issues.append("PyQt6不可用")
            if missing_components:
                issues.extend([f"缺失UI组件: {comp}" for comp in missing_components])
            if not ui_import_success:
                issues.append("UI组件导入失败")
            
            self._log_validation_result(
                "UI-001", overall_ui_success,
                f"UI界面完整性验证{'成功' if overall_ui_success else '失败'}",
                issues=issues
            )
            
            return overall_ui_success
            
        except Exception as e:
            self._log_validation_result(
                "UI-001", False,
                f"UI验证异常: {str(e)}",
                issues=[f"UI验证异常: {str(e)}"]
            )
            return False
    
    def validate_module_imports(self) -> bool:
        """验证模块导入完整性"""
        print("\n📦 验证模块导入完整性...")
        print("=" * 50)
        
        # 核心模块列表
        core_modules = {
            "src.utils.memory_guard": "内存管理器",
            "src.core.model_switcher": "模型切换器",
            "src.core.narrative_analyzer": "叙事分析器",
            "src.core.language_detector": "语言检测器",
            "src.emotion.emotion_intensity": "情感强度分析器"
        }
        
        import_results = {}
        failed_imports = []
        
        for module_name, description in core_modules.items():
            try:
                __import__(module_name)
                print(f"  ✅ {description}: {module_name}")
                import_results[module_name] = True
            except ImportError as e:
                print(f"  ❌ {description}: {module_name} - {e}")
                import_results[module_name] = False
                failed_imports.append(f"{description} ({module_name})")
            except Exception as e:
                print(f"  ⚠️ {description}: {module_name} - 导入异常: {e}")
                import_results[module_name] = False
                failed_imports.append(f"{description} ({module_name}) - 异常")
        
        success_rate = sum(import_results.values()) / len(import_results)
        overall_success = success_rate >= 0.8  # 80%以上成功率
        
        self._log_validation_result(
            "IMPORT-001", overall_success,
            f"模块导入验证 - 成功率: {success_rate:.1%}",
            issues=[f"导入失败: {module}" for module in failed_imports] if failed_imports else []
        )
        
        return overall_success
    
    def validate_basic_functionality(self) -> bool:
        """验证基础功能可用性"""
        print("\n⚙️ 验证基础功能可用性...")
        print("=" * 50)
        
        functionality_results = {}
        
        # 1. 内存管理功能
        try:
            from src.utils.memory_guard import get_memory_guard
            memory_guard = get_memory_guard()
            current_memory = memory_guard.get_memory_usage()
            print(f"  ✅ 内存管理功能正常 - 当前内存: {current_memory:.2f}MB")
            functionality_results["memory_management"] = True
        except Exception as e:
            print(f"  ❌ 内存管理功能异常: {e}")
            functionality_results["memory_management"] = False
        
        # 2. 语言检测功能
        try:
            from src.core.language_detector import get_language_detector
            language_detector = get_language_detector()
            test_result = language_detector.detect_language("这是中文测试")
            print(f"  ✅ 语言检测功能正常 - 测试结果: {test_result}")
            functionality_results["language_detection"] = True
        except Exception as e:
            print(f"  ❌ 语言检测功能异常: {e}")
            functionality_results["language_detection"] = False
        
        # 3. 模型切换功能
        try:
            from src.core.model_switcher import get_model_switcher
            model_switcher = get_model_switcher()
            model_info = model_switcher.get_model_info()
            print(f"  ✅ 模型切换功能正常 - 可用模型: {len(model_info.get('available_models', {}))}")
            functionality_results["model_switching"] = True
        except Exception as e:
            print(f"  ❌ 模型切换功能异常: {e}")
            functionality_results["model_switching"] = False
        
        # 4. 叙事分析功能
        try:
            from src.core.narrative_analyzer import get_narrative_analyzer
            narrative_analyzer = get_narrative_analyzer()
            test_analysis = narrative_analyzer.analyze_narrative_structure(["测试文本"])
            print(f"  ✅ 叙事分析功能正常 - 分析片段: {test_analysis.get('total_segments', 0)}")
            functionality_results["narrative_analysis"] = True
        except Exception as e:
            print(f"  ❌ 叙事分析功能异常: {e}")
            functionality_results["narrative_analysis"] = False
        
        # 5. 情感分析功能
        try:
            from src.emotion.emotion_intensity import get_emotion_intensity
            emotion_analyzer = get_emotion_intensity()
            emotion_result = emotion_analyzer.get_dominant_emotion("测试情感")
            print(f"  ✅ 情感分析功能正常 - 检测结果: {emotion_result}")
            functionality_results["emotion_analysis"] = True
        except Exception as e:
            print(f"  ❌ 情感分析功能异常: {e}")
            functionality_results["emotion_analysis"] = False
        
        success_rate = sum(functionality_results.values()) / len(functionality_results)
        overall_success = success_rate >= 0.8  # 80%以上成功率
        
        failed_functions = [name for name, success in functionality_results.items() if not success]
        
        self._log_validation_result(
            "FUNC-001", overall_success,
            f"基础功能验证 - 成功率: {success_rate:.1%}",
            issues=[f"功能异常: {func}" for func in failed_functions] if failed_functions else []
        )
        
        return overall_success

    def validate_workflow_continuity(self) -> bool:
        """验证工作流程连贯性"""
        print("\n🔄 验证工作流程连贯性...")
        print("=" * 50)

        workflow_steps = {}

        try:
            # 模拟完整工作流程
            print("  📁 步骤1: 模拟文件上传...")
            test_text = "这是一个测试文本，用于验证工作流程的连贯性。"
            workflow_steps["file_upload"] = True
            print("    ✅ 文件上传模拟成功")

            # 步骤2: 语言检测
            print("  🔍 步骤2: 语言检测...")
            from src.core.language_detector import get_language_detector
            language_detector = get_language_detector()
            detected_language = language_detector.detect_language(test_text)
            confidence = language_detector.get_confidence(test_text)
            workflow_steps["language_detection"] = True
            print(f"    ✅ 语言检测成功: {detected_language} (置信度: {confidence:.2f})")

            # 步骤3: 模型切换
            print("  🔄 步骤3: 模型切换...")
            from src.core.model_switcher import get_model_switcher
            model_switcher = get_model_switcher()
            switch_result = model_switcher.switch_model(detected_language)
            workflow_steps["model_switching"] = switch_result
            print(f"    {'✅' if switch_result else '❌'} 模型切换{'成功' if switch_result else '失败'}")

            # 步骤4: 剧本分析
            print("  📖 步骤4: 剧本分析...")
            from src.core.narrative_analyzer import get_narrative_analyzer
            narrative_analyzer = get_narrative_analyzer()
            analysis_result = narrative_analyzer.analyze_narrative_structure([test_text])
            workflow_steps["script_analysis"] = True
            print(f"    ✅ 剧本分析成功: {analysis_result.get('total_segments', 0)}个片段")

            # 步骤5: 情感分析
            print("  💭 步骤5: 情感分析...")
            from src.emotion.emotion_intensity import get_emotion_intensity
            emotion_analyzer = get_emotion_intensity()
            emotion_result = emotion_analyzer.analyze_emotion_intensity(test_text)
            workflow_steps["emotion_analysis"] = True
            print(f"    ✅ 情感分析成功: {len(emotion_result)}种情感")

        except Exception as e:
            print(f"  ❌ 工作流程执行异常: {e}")
            workflow_steps["workflow_exception"] = str(e)

        success_rate = sum(1 for v in workflow_steps.values() if v is True) / len(workflow_steps)
        overall_success = success_rate >= 0.8 and "workflow_exception" not in workflow_steps

        failed_steps = [step for step, success in workflow_steps.items() if success is not True]

        self._log_validation_result(
            "WORKFLOW-001", overall_success,
            f"工作流程验证 - 成功率: {success_rate:.1%}",
            issues=[f"步骤失败: {step}" for step in failed_steps] if failed_steps else []
        )

        return overall_success

    def run_complete_validation(self) -> Dict[str, Any]:
        """运行完整的基础功能验证"""
        print("🔍 开始VisionAI-ClipsMaster基础功能完整性验证...")
        print("=" * 80)

        # 执行所有验证步骤
        validation_steps = [
            ("程序启动验证", self.validate_program_startup),
            ("UI界面完整性验证", self.validate_ui_components),
            ("模块导入完整性验证", self.validate_module_imports),
            ("基础功能可用性验证", self.validate_basic_functionality),
            ("工作流程连贯性验证", self.validate_workflow_continuity)
        ]

        passed_validations = 0
        total_validations = len(validation_steps)

        for step_name, validation_func in validation_steps:
            print(f"\n{'='*20} {step_name} {'='*20}")
            try:
                if validation_func():
                    passed_validations += 1
                    print(f"✅ {step_name} 通过")
                else:
                    print(f"❌ {step_name} 失败")
            except Exception as e:
                print(f"❌ {step_name} 异常: {e}")

        # 计算总体结果
        success_rate = passed_validations / total_validations
        total_execution_time = time.time() - self.start_time

        # 确定总体状态
        if success_rate >= 0.9:
            overall_status = "EXCELLENT"
        elif success_rate >= 0.8:
            overall_status = "GOOD"
        elif success_rate >= 0.6:
            overall_status = "FAIR"
        else:
            overall_status = "POOR"

        self.validation_results.update({
            "overall_status": overall_status,
            "success_rate": round(success_rate, 3),
            "passed_validations": passed_validations,
            "total_validations": total_validations,
            "total_execution_time_seconds": round(total_execution_time, 3),
            "validation_completion_time": datetime.now().isoformat()
        })

        return self.validation_results

    def generate_validation_report(self):
        """生成验证报告"""
        print("\n" + "=" * 80)
        print("📋 VisionAI-ClipsMaster 基础功能完整性验证报告")
        print("=" * 80)

        # 总体状态
        status_emoji = {
            "EXCELLENT": "🟢",
            "GOOD": "🟡",
            "FAIR": "🟠",
            "POOR": "🔴"
        }

        results = self.validation_results
        print(f"\n📊 总体状态: {status_emoji.get(results['overall_status'], '❓')} {results['overall_status']}")
        print(f"📈 验证通过率: {results.get('success_rate', 0):.1%} ({results.get('passed_validations', 0)}/{results.get('total_validations', 0)})")
        print(f"⏱️ 总执行时间: {results.get('total_execution_time_seconds', 0):.3f}秒")

        # 验证结果详情
        print(f"\n🔍 验证结果详情:")
        for test_id, result in results["validation_tests"].items():
            status = "✅" if result["passed"] else "❌"
            print(f"  {status} {test_id}: {result['details']}")

        # 关键问题
        if results["critical_issues"]:
            print(f"\n🔴 关键问题 ({len(results['critical_issues'])}个):")
            for issue in results["critical_issues"]:
                print(f"  • {issue}")

        # 警告
        if results["warnings"]:
            print(f"\n⚠️ 警告 ({len(results['warnings'])}个):")
            for warning in results["warnings"]:
                print(f"  • {warning}")

        # 建议
        print(f"\n💡 建议:")
        if results["overall_status"] == "EXCELLENT":
            print("  ✅ 所有基础功能正常，可以安全进行下一步测试和优化")
        elif results["overall_status"] == "GOOD":
            print("  🟡 基础功能基本正常，建议修复少量问题后继续")
        elif results["overall_status"] == "FAIR":
            print("  🟠 存在一些问题，建议优先修复关键问题")
        else:
            print("  🔴 存在严重问题，必须修复后才能继续")

        return results["overall_status"] in ["EXCELLENT", "GOOD"]

if __name__ == "__main__":
    validator = BaselineFunctionalityValidator()
    results = validator.run_complete_validation()

    # 保存验证结果
    report_file = f"Baseline_Functionality_Validation_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # 生成报告
    validation_passed = validator.generate_validation_report()

    print(f"\n📄 详细验证报告已保存到: {report_file}")

    # 返回验证状态
    if validation_passed:
        print("\n🎉 基础功能验证通过！可以安全进行下一步工作。")
        sys.exit(0)
    else:
        print("\n⚠️ 基础功能验证未完全通过，建议先修复问题。")
        sys.exit(1)
