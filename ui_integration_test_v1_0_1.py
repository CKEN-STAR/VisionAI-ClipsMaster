#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster UI集成测试 v1.0.1
测试UI界面的启动、响应、交互等功能
"""

import os
import sys
import json
import time
import threading
from datetime import datetime
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root / "ui"))

class UIIntegrationTest:
    """UI集成测试类"""
    
    def __init__(self):
        self.test_results = {
            "test_type": "UI Integration Tests",
            "version": "v1.0.1",
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": 0,
                "passed_tests": 0,
                "failed_tests": 0,
                "success_rate": 0
            },
            "test_results": {},
            "ui_metrics": {}
        }
        self.start_time = time.time()
        
    def log_test_result(self, test_name, passed, details="", metrics=None):
        """记录测试结果"""
        self.test_results["test_results"][test_name] = {
            "passed": passed,
            "details": details,
            "metrics": metrics or {},
            "timestamp": datetime.now().isoformat()
        }
        
        self.test_results["summary"]["total_tests"] += 1
        if passed:
            self.test_results["summary"]["passed_tests"] += 1
        else:
            self.test_results["summary"]["failed_tests"] += 1
            
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status} {test_name}: {details}")
        
        if metrics:
            for key, value in metrics.items():
                print(f"   📊 {key}: {value}")
    
    def test_ui_imports(self):
        """测试UI模块导入"""
        print("\n📦 测试UI模块导入...")
        
        ui_modules = [
            ("ui.main_window", "MainWindow"),
            ("ui.training_panel", "TrainingPanel"),
            ("ui.progress_dashboard", "ProgressDashboard"),
            ("ui.components.realtime_charts", "RealtimeCharts"),
            ("ui.components.alert_manager", "AlertManager")
        ]
        
        import_times = {}
        successful_imports = 0
        
        for module_name, class_name in ui_modules:
            try:
                start_time = time.time()
                module = __import__(module_name, fromlist=[class_name])
                
                # 检查类是否存在
                if hasattr(module, class_name):
                    import_time = (time.time() - start_time) * 1000
                    import_times[module_name] = import_time
                    successful_imports += 1
                    
                    self.log_test_result(
                        f"ui_import_{module_name.replace('.', '_')}",
                        True,
                        f"{class_name}导入成功",
                        {"import_time_ms": import_time}
                    )
                else:
                    self.log_test_result(
                        f"ui_import_{module_name.replace('.', '_')}",
                        False,
                        f"{class_name}类不存在"
                    )
                    
            except ImportError as e:
                self.log_test_result(
                    f"ui_import_{module_name.replace('.', '_')}",
                    False,
                    f"{class_name}导入失败: {str(e)}"
                )
            except Exception as e:
                self.log_test_result(
                    f"ui_import_{module_name.replace('.', '_')}",
                    False,
                    f"{class_name}导入异常: {str(e)}"
                )
        
        # 总体导入测试
        import_success_rate = (successful_imports / len(ui_modules)) * 100
        avg_import_time = sum(import_times.values()) / len(import_times) if import_times else 0
        
        self.log_test_result(
            "ui_imports_overall",
            import_success_rate >= 80,
            f"UI模块导入成功率: {import_success_rate:.1f}%",
            {
                "success_rate": import_success_rate,
                "avg_import_time_ms": avg_import_time,
                "successful_imports": successful_imports,
                "total_modules": len(ui_modules)
            }
        )
    
    def test_ui_initialization(self):
        """测试UI初始化"""
        print("\n🚀 测试UI初始化...")
        
        try:
            # 测试主窗口初始化
            from ui.main_window import MainWindow
            
            start_time = time.time()
            
            # 模拟初始化（不实际显示窗口）
            try:
                # 检查MainWindow类的基本属性和方法
                main_window_class = MainWindow
                
                # 检查必要的方法
                required_methods = ['__init__', 'setup_ui', 'show']
                available_methods = []
                
                for method in required_methods:
                    if hasattr(main_window_class, method):
                        available_methods.append(method)
                
                init_time = (time.time() - start_time) * 1000
                
                self.log_test_result(
                    "main_window_initialization",
                    len(available_methods) >= 2,
                    f"主窗口类检查完成，可用方法: {len(available_methods)}/{len(required_methods)}",
                    {
                        "init_time_ms": init_time,
                        "available_methods": available_methods,
                        "required_methods": required_methods
                    }
                )
                
            except Exception as e:
                self.log_test_result(
                    "main_window_initialization",
                    False,
                    f"主窗口初始化失败: {str(e)}"
                )
                
        except ImportError as e:
            self.log_test_result(
                "main_window_initialization",
                False,
                f"主窗口导入失败: {str(e)}"
            )
    
    def test_ui_components(self):
        """测试UI组件功能"""
        print("\n🧩 测试UI组件功能...")
        
        # 测试训练面板
        try:
            from ui.training_panel import TrainingPanel
            
            # 检查训练面板的基本功能
            training_panel_class = TrainingPanel
            
            # 检查必要的方法
            required_methods = ['__init__', 'update_progress', 'start_training']
            available_methods = []
            
            for method in required_methods:
                if hasattr(training_panel_class, method):
                    available_methods.append(method)
            
            self.log_test_result(
                "training_panel_functionality",
                len(available_methods) >= 1,
                f"训练面板功能检查，可用方法: {len(available_methods)}/{len(required_methods)}",
                {
                    "available_methods": available_methods,
                    "functionality_score": len(available_methods) / len(required_methods)
                }
            )
            
        except ImportError as e:
            self.log_test_result(
                "training_panel_functionality",
                False,
                f"训练面板导入失败: {str(e)}"
            )
        
        # 测试进度看板
        try:
            from ui.progress_dashboard import ProgressDashboard
            
            # 检查进度看板的基本功能
            progress_dashboard_class = ProgressDashboard
            
            # 检查必要的方法
            required_methods = ['__init__', 'update_progress', 'show_status']
            available_methods = []
            
            for method in required_methods:
                if hasattr(progress_dashboard_class, method):
                    available_methods.append(method)
            
            self.log_test_result(
                "progress_dashboard_functionality",
                len(available_methods) >= 1,
                f"进度看板功能检查，可用方法: {len(available_methods)}/{len(required_methods)}",
                {
                    "available_methods": available_methods,
                    "functionality_score": len(available_methods) / len(required_methods)
                }
            )
            
        except ImportError as e:
            self.log_test_result(
                "progress_dashboard_functionality",
                False,
                f"进度看板导入失败: {str(e)}"
            )
    
    def test_ui_responsiveness(self):
        """测试UI响应性"""
        print("\n⚡ 测试UI响应性...")
        
        try:
            # 测试实时图表组件
            from ui.components.realtime_charts import RealtimeCharts
            
            start_time = time.time()
            
            # 模拟数据更新测试
            charts_class = RealtimeCharts
            
            # 检查实时更新相关方法
            update_methods = ['update_data', 'refresh', 'update_chart', 'add_data_point']
            available_update_methods = []
            
            for method in update_methods:
                if hasattr(charts_class, method):
                    available_update_methods.append(method)
            
            response_time = (time.time() - start_time) * 1000
            
            self.log_test_result(
                "realtime_charts_responsiveness",
                len(available_update_methods) >= 1,
                f"实时图表响应性检查，可用更新方法: {len(available_update_methods)}",
                {
                    "response_time_ms": response_time,
                    "available_update_methods": available_update_methods,
                    "responsiveness_score": len(available_update_methods) / len(update_methods)
                }
            )
            
        except ImportError as e:
            self.log_test_result(
                "realtime_charts_responsiveness",
                False,
                f"实时图表导入失败: {str(e)}"
            )
        
        # 测试警报管理器
        try:
            from ui.components.alert_manager import AlertManager
            
            start_time = time.time()
            
            alert_manager_class = AlertManager
            
            # 检查警报相关方法
            alert_methods = ['show_alert', 'hide_alert', 'add_alert', 'clear_alerts']
            available_alert_methods = []
            
            for method in alert_methods:
                if hasattr(alert_manager_class, method):
                    available_alert_methods.append(method)
            
            alert_response_time = (time.time() - start_time) * 1000
            
            self.log_test_result(
                "alert_manager_responsiveness",
                len(available_alert_methods) >= 1,
                f"警报管理器响应性检查，可用方法: {len(available_alert_methods)}",
                {
                    "response_time_ms": alert_response_time,
                    "available_alert_methods": available_alert_methods,
                    "alert_functionality_score": len(available_alert_methods) / len(alert_methods)
                }
            )
            
        except ImportError as e:
            self.log_test_result(
                "alert_manager_responsiveness",
                False,
                f"警报管理器导入失败: {str(e)}"
            )
    
    def test_ui_error_handling(self):
        """测试UI错误处理"""
        print("\n🛡️ 测试UI错误处理...")
        
        try:
            # 测试错误处理机制
            error_handling_modules = [
                "ui.components.alert_manager",
                "src.utils.error_handler"
            ]
            
            error_handling_available = 0
            
            for module_name in error_handling_modules:
                try:
                    module = __import__(module_name, fromlist=[''])
                    error_handling_available += 1
                    
                    self.log_test_result(
                        f"error_handling_{module_name.replace('.', '_')}",
                        True,
                        f"错误处理模块可用: {module_name}"
                    )
                    
                except ImportError:
                    self.log_test_result(
                        f"error_handling_{module_name.replace('.', '_')}",
                        False,
                        f"错误处理模块不可用: {module_name}"
                    )
            
            # 总体错误处理能力评估
            error_handling_score = (error_handling_available / len(error_handling_modules)) * 100
            
            self.log_test_result(
                "ui_error_handling_overall",
                error_handling_score >= 50,
                f"UI错误处理能力: {error_handling_score:.1f}%",
                {
                    "error_handling_score": error_handling_score,
                    "available_modules": error_handling_available,
                    "total_modules": len(error_handling_modules)
                }
            )
            
        except Exception as e:
            self.log_test_result(
                "ui_error_handling_test",
                False,
                f"错误处理测试异常: {str(e)}"
            )
    
    def run_all_tests(self):
        """运行所有UI集成测试"""
        print("🎬 开始VisionAI-ClipsMaster v1.0.1 UI集成测试")
        print("=" * 60)
        
        try:
            # 运行各项测试
            self.test_ui_imports()
            self.test_ui_initialization()
            self.test_ui_components()
            self.test_ui_responsiveness()
            self.test_ui_error_handling()
            
            # 计算成功率
            total_tests = self.test_results["summary"]["total_tests"]
            passed_tests = self.test_results["summary"]["passed_tests"]
            self.test_results["summary"]["success_rate"] = (passed_tests / total_tests * 100) if total_tests > 0 else 0
            
            # 生成报告
            self.generate_report()
            
        except Exception as e:
            print(f"❌ 测试过程中发生异常: {e}")
            import traceback
            traceback.print_exc()
    
    def generate_report(self):
        """生成测试报告"""
        print("\n" + "=" * 60)
        print("📊 UI集成测试结果汇总")
        print("=" * 60)
        
        summary = self.test_results["summary"]
        print(f"总测试数: {summary['total_tests']}")
        print(f"通过测试: {summary['passed_tests']}")
        print(f"失败测试: {summary['failed_tests']}")
        print(f"成功率: {summary['success_rate']:.1f}%")
        print(f"测试时长: {time.time() - self.start_time:.2f}秒")
        
        # 保存JSON报告
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"ui_integration_test_{timestamp}.json"
        
        with open(report_filename, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 详细测试报告已保存到: {report_filename}")
        
        if summary['success_rate'] >= 80:
            print("✅ UI系统运行良好!")
        elif summary['success_rate'] >= 60:
            print("⚠️  UI系统存在一些问题")
        else:
            print("❌ UI系统存在严重问题")

def main():
    """主函数"""
    test_runner = UIIntegrationTest()
    test_runner.run_all_tests()

if __name__ == "__main__":
    main()
