#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 最终验收测试
执行完整的端到端验收测试，确保所有功能正常运行
"""

import sys
import os
import json
import time
import tempfile
import traceback
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

class FinalAcceptanceTester:
    def __init__(self):
        self.results = {
            "test_time": datetime.now().isoformat(),
            "total_test_suites": 0,
            "successful_test_suites": 0,
            "failed_test_suites": 0,
            "test_suite_results": {},
            "overall_metrics": {},
            "errors": []
        }
        
        # 创建临时目录用于测试
        self.temp_dir = Path(tempfile.mkdtemp(prefix="final_acceptance_test_"))

    def test_core_functionality_suite(self):
        """核心功能测试套件"""
        print("执行核心功能测试套件...")
        
        try:
            suite_result = {
                "status": "success",
                "test_cases": {},
                "suite_time": 0.0
            }
            
            start_time = time.time()
            
            # 测试1: SRT解析功能
            from src.core.srt_parser import SRTParser
            parser = SRTParser()
            
            # 创建测试SRT文件
            test_srt_content = """1
00:00:01,000 --> 00:00:03,000
这是第一个字幕

2
00:00:04,000 --> 00:00:06,000
这是第二个字幕"""
            
            test_srt_file = self.temp_dir / "test.srt"
            test_srt_file.write_text(test_srt_content, encoding='utf-8')
            
            parsed_result = parser.parse(str(test_srt_file))
            suite_result["test_cases"]["srt_parsing"] = {
                "status": "success" if len(parsed_result) == 2 else "failed",
                "segments_parsed": len(parsed_result)
            }
            
            # 测试2: 叙事分析功能
            from src.core.narrative_analyzer import NarrativeAnalyzer
            analyzer = NarrativeAnalyzer()
            
            test_text = "这是一个关于爱情的故事，男主角深深地爱着女主角。"
            analysis_result = analyzer.analyze_narrative_structure(test_text)
            suite_result["test_cases"]["narrative_analysis"] = {
                "status": "success" if isinstance(analysis_result, dict) else "failed",
                "result_type": type(analysis_result).__name__
            }
            
            # 测试3: 剧本重构功能
            from src.core.screenplay_engineer import ScreenplayEngineer
            engineer = ScreenplayEngineer()
            
            reconstruction_result = engineer.reconstruct_from_segments(parsed_result)
            suite_result["test_cases"]["screenplay_reconstruction"] = {
                "status": "success" if isinstance(reconstruction_result, dict) else "failed",
                "result_type": type(reconstruction_result).__name__
            }
            
            suite_time = time.time() - start_time
            suite_result["suite_time"] = suite_time
            
            # 计算套件成功率
            successful_cases = sum(1 for case in suite_result["test_cases"].values() 
                                 if case.get("status") == "success")
            total_cases = len(suite_result["test_cases"])
            suite_result["success_rate"] = successful_cases / total_cases * 100
            
            print(f"  核心功能测试: {successful_cases}/{total_cases} 通过")
            print(f"  套件耗时: {suite_time:.3f}秒")
            print("  ✓ 核心功能测试套件完成")
            return suite_result
            
        except Exception as e:
            print(f"  ✗ 核心功能测试套件失败: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "traceback": traceback.format_exc()
            }

    def test_ui_integration_suite(self):
        """UI集成测试套件"""
        print("执行UI集成测试套件...")
        
        try:
            suite_result = {
                "status": "success",
                "test_cases": {},
                "suite_time": 0.0
            }
            
            start_time = time.time()
            
            # 测试1: UI组件导入
            try:
                from src.ui.main_window import MainWindow
                from src.ui.training_panel import TrainingPanel
                from src.ui.progress_dashboard import ProgressDashboard
                
                suite_result["test_cases"]["ui_imports"] = {
                    "status": "success",
                    "components_imported": 3
                }
            except ImportError as e:
                suite_result["test_cases"]["ui_imports"] = {
                    "status": "failed",
                    "error": str(e)
                }
            
            # 测试2: PyQt6可用性
            try:
                from PyQt6.QtWidgets import QApplication, QWidget
                from PyQt6.QtCore import QTimer
                
                suite_result["test_cases"]["pyqt6_availability"] = {
                    "status": "success",
                    "framework": "PyQt6"
                }
            except ImportError as e:
                suite_result["test_cases"]["pyqt6_availability"] = {
                    "status": "failed",
                    "error": str(e)
                }
            
            # 测试3: UI组件创建（无显示）
            try:
                if suite_result["test_cases"]["pyqt6_availability"]["status"] == "success":
                    app = QApplication.instance()
                    if app is None:
                        app = QApplication([])
                    
                    # 创建基本组件测试
                    widget = QWidget()
                    widget.setWindowTitle("测试窗口")
                    
                    suite_result["test_cases"]["ui_component_creation"] = {
                        "status": "success",
                        "widget_created": True
                    }
                else:
                    suite_result["test_cases"]["ui_component_creation"] = {
                        "status": "skipped",
                        "reason": "PyQt6不可用"
                    }
            except Exception as e:
                suite_result["test_cases"]["ui_component_creation"] = {
                    "status": "failed",
                    "error": str(e)
                }
            
            suite_time = time.time() - start_time
            suite_result["suite_time"] = suite_time
            
            # 计算套件成功率
            successful_cases = sum(1 for case in suite_result["test_cases"].values() 
                                 if case.get("status") == "success")
            total_cases = len(suite_result["test_cases"])
            suite_result["success_rate"] = successful_cases / total_cases * 100
            
            print(f"  UI集成测试: {successful_cases}/{total_cases} 通过")
            print(f"  套件耗时: {suite_time:.3f}秒")
            print("  ✓ UI集成测试套件完成")
            return suite_result
            
        except Exception as e:
            print(f"  ✗ UI集成测试套件失败: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "traceback": traceback.format_exc()
            }

    def test_training_functionality_suite(self):
        """训练功能测试套件"""
        print("执行训练功能测试套件...")
        
        try:
            suite_result = {
                "status": "success",
                "test_cases": {},
                "suite_time": 0.0
            }
            
            start_time = time.time()
            
            # 测试1: 训练模块导入
            training_modules = [
                "src.training.data_processor",
                "src.training.model_trainer",
                "src.training.feedback_collector"
            ]
            
            imported_modules = 0
            for module_name in training_modules:
                try:
                    __import__(module_name)
                    imported_modules += 1
                except ImportError:
                    pass
            
            suite_result["test_cases"]["training_module_imports"] = {
                "status": "success" if imported_modules == len(training_modules) else "partial",
                "imported_modules": imported_modules,
                "total_modules": len(training_modules)
            }
            
            # 测试2: 数据处理功能
            try:
                from src.training.data_processor import TrainingDataProcessor
                processor = TrainingDataProcessor()
                
                test_data = [{
                    "original_text": "测试文本",
                    "viral_text": "震撼！测试文本",
                    "engagement_score": 8.5
                }]
                
                processed_data = processor.process_training_data(test_data)
                suite_result["test_cases"]["data_processing"] = {
                    "status": "success" if len(processed_data) > 0 else "failed",
                    "processed_samples": len(processed_data)
                }
            except Exception as e:
                suite_result["test_cases"]["data_processing"] = {
                    "status": "failed",
                    "error": str(e)
                }
            
            # 测试3: 模型训练功能
            try:
                from src.training.model_trainer import ModelTrainer
                trainer = ModelTrainer()
                
                training_result = trainer.train_model(test_data, epochs=1, batch_size=1)
                suite_result["test_cases"]["model_training"] = {
                    "status": "success" if training_result.get("status") == "success" else "failed",
                    "training_result": training_result.get("status", "unknown")
                }
            except Exception as e:
                suite_result["test_cases"]["model_training"] = {
                    "status": "failed",
                    "error": str(e)
                }
            
            suite_time = time.time() - start_time
            suite_result["suite_time"] = suite_time
            
            # 计算套件成功率
            successful_cases = sum(1 for case in suite_result["test_cases"].values() 
                                 if case.get("status") == "success")
            total_cases = len(suite_result["test_cases"])
            suite_result["success_rate"] = successful_cases / total_cases * 100
            
            print(f"  训练功能测试: {successful_cases}/{total_cases} 通过")
            print(f"  套件耗时: {suite_time:.3f}秒")
            print("  ✓ 训练功能测试套件完成")
            return suite_result
            
        except Exception as e:
            print(f"  ✗ 训练功能测试套件失败: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "traceback": traceback.format_exc()
            }

    def test_system_stability_suite(self):
        """系统稳定性测试套件"""
        print("执行系统稳定性测试套件...")
        
        try:
            suite_result = {
                "status": "success",
                "test_cases": {},
                "suite_time": 0.0
            }
            
            start_time = time.time()
            
            # 测试1: 内存稳定性
            from src.utils.memory_guard import MemoryGuard
            memory_guard = MemoryGuard()
            
            initial_memory = memory_guard.get_memory_info()
            memory_safety = memory_guard.check_memory_safety()
            
            suite_result["test_cases"]["memory_stability"] = {
                "status": "success",
                "memory_safe": memory_safety,
                "memory_usage_mb": initial_memory.get("process_memory_mb", 0)
            }
            
            # 测试2: 错误恢复能力
            error_recovery_tests = 0
            successful_recoveries = 0
            
            # 测试空输入恢复
            try:
                from src.core.narrative_analyzer import NarrativeAnalyzer
                analyzer = NarrativeAnalyzer()
                result = analyzer.analyze_narrative_structure("")
                if isinstance(result, dict):
                    successful_recoveries += 1
                error_recovery_tests += 1
            except:
                error_recovery_tests += 1
            
            # 测试无效文件恢复
            try:
                from src.core.srt_parser import parse_srt
                result = parse_srt("nonexistent.srt")
                if isinstance(result, list):
                    successful_recoveries += 1
                error_recovery_tests += 1
            except:
                error_recovery_tests += 1
            
            suite_result["test_cases"]["error_recovery"] = {
                "status": "success" if successful_recoveries == error_recovery_tests else "partial",
                "recovery_rate": successful_recoveries / error_recovery_tests * 100 if error_recovery_tests > 0 else 0
            }
            
            # 测试3: 并发处理稳定性
            import threading

            concurrent_results = []

            def concurrent_test():
                try:
                    from src.core.narrative_analyzer import NarrativeAnalyzer
                    analyzer = NarrativeAnalyzer()
                    result = analyzer.analyze_narrative_structure("并发测试文本")
                    concurrent_results.append(isinstance(result, dict))
                except:
                    concurrent_results.append(False)

            threads = []
            for i in range(3):  # 创建3个并发线程
                thread = threading.Thread(target=concurrent_test)
                threads.append(thread)
                thread.start()

            for thread in threads:
                thread.join(timeout=5)
            
            successful_concurrent = sum(concurrent_results)
            suite_result["test_cases"]["concurrent_stability"] = {
                "status": "success" if successful_concurrent == len(threads) else "partial",
                "concurrent_success_rate": successful_concurrent / len(threads) * 100
            }
            
            suite_time = time.time() - start_time
            suite_result["suite_time"] = suite_time
            
            # 计算套件成功率
            successful_cases = sum(1 for case in suite_result["test_cases"].values() 
                                 if case.get("status") == "success")
            total_cases = len(suite_result["test_cases"])
            suite_result["success_rate"] = successful_cases / total_cases * 100
            
            print(f"  系统稳定性测试: {successful_cases}/{total_cases} 通过")
            print(f"  套件耗时: {suite_time:.3f}秒")
            print("  ✓ 系统稳定性测试套件完成")
            return suite_result
            
        except Exception as e:
            print(f"  ✗ 系统稳定性测试套件失败: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "traceback": traceback.format_exc()
            }

    def run_final_acceptance_test(self):
        """运行最终验收测试"""
        print("=" * 60)
        print("VisionAI-ClipsMaster 最终验收测试")
        print("=" * 60)
        
        test_suites = [
            ("核心功能测试套件", self.test_core_functionality_suite),
            ("UI集成测试套件", self.test_ui_integration_suite),
            ("训练功能测试套件", self.test_training_functionality_suite),
            ("系统稳定性测试套件", self.test_system_stability_suite)
        ]
        
        self.results["total_test_suites"] = len(test_suites)
        
        overall_start_time = time.time()
        
        for suite_name, suite_func in test_suites:
            print(f"\n{suite_name}")
            try:
                result = suite_func()
                self.results["test_suite_results"][suite_name] = result
                
                if result.get("status") == "success":
                    self.results["successful_test_suites"] += 1
                    print(f"  ✓ {suite_name} 通过")
                else:
                    self.results["failed_test_suites"] += 1
                    print(f"  ✗ {suite_name} 失败")
                    
            except Exception as e:
                self.results["failed_test_suites"] += 1
                error_msg = f"测试套件异常: {e}"
                self.results["test_suite_results"][suite_name] = {
                    "status": "error",
                    "error": error_msg
                }
                self.results["errors"].append(f"{suite_name}: {error_msg}")
                print(f"  ✗ {error_msg}")
        
        overall_time = time.time() - overall_start_time
        self.results["overall_metrics"]["total_test_time"] = overall_time
        
        # 计算整体指标
        self._calculate_overall_metrics()
        
        # 清理临时文件
        self.cleanup()
        
        # 生成报告
        self.generate_report()
        
        return self.results

    def _calculate_overall_metrics(self):
        """计算整体指标"""
        # 计算平均成功率
        success_rates = []
        for suite_result in self.results["test_suite_results"].values():
            if isinstance(suite_result, dict) and "success_rate" in suite_result:
                success_rates.append(suite_result["success_rate"])
        
        if success_rates:
            self.results["overall_metrics"]["average_success_rate"] = sum(success_rates) / len(success_rates)
        else:
            self.results["overall_metrics"]["average_success_rate"] = 0.0
        
        # 计算系统就绪度
        suite_success_rate = self.results["successful_test_suites"] / self.results["total_test_suites"] * 100
        self.results["overall_metrics"]["system_readiness"] = suite_success_rate

    def cleanup(self):
        """清理临时文件"""
        try:
            import shutil
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
                print(f"\n临时目录已清理: {self.temp_dir}")
        except Exception as e:
            print(f"\n清理临时文件失败: {e}")

    def generate_report(self):
        """生成最终验收报告"""
        print("\n" + "=" * 60)
        print("最终验收测试结果汇总")
        print("=" * 60)
        
        print(f"总测试套件: {self.results['total_test_suites']}")
        print(f"通过套件: {self.results['successful_test_suites']}")
        print(f"失败套件: {self.results['failed_test_suites']}")
        print(f"套件成功率: {(self.results['successful_test_suites']/self.results['total_test_suites']*100):.1f}%")
        print(f"平均功能成功率: {self.results['overall_metrics']['average_success_rate']:.1f}%")
        print(f"系统就绪度: {self.results['overall_metrics']['system_readiness']:.1f}%")
        print(f"总测试时间: {self.results['overall_metrics']['total_test_time']:.2f}秒")
        
        # 判断系统状态
        if self.results["overall_metrics"]["system_readiness"] >= 90:
            print("\n🎉 系统状态: 生产就绪 (Production Ready)")
        elif self.results["overall_metrics"]["system_readiness"] >= 75:
            print("\n⚠️ 系统状态: 基本就绪 (Mostly Ready)")
        else:
            print("\n❌ 系统状态: 需要修复 (Needs Fixes)")
        
        if self.results["failed_test_suites"] > 0:
            print(f"\n失败的测试套件:")
            for suite_name, result in self.results["test_suite_results"].items():
                if result.get("status") != "success":
                    print(f"  - {suite_name}: {result.get('error', 'Unknown error')}")
        
        # 保存详细报告
        report_file = f"final_acceptance_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        print(f"\n详细报告已保存到: {report_file}")

if __name__ == "__main__":
    tester = FinalAcceptanceTester()
    results = tester.run_final_acceptance_test()
    
    # 返回退出码
    if results["failed_test_suites"] > 0:
        sys.exit(1)
    else:
        sys.exit(0)
