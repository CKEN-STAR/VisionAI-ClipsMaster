#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster v1.0.1 UI组件完整性验证
验证所有UI组件正常工作，修复导入和初始化问题
"""

import sys
import os
import time
import traceback
from datetime import datetime
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

class UIComponentVerifier:
    def __init__(self):
        self.test_results = {}
        self.errors = []
        
    def add_test_result(self, test_name, passed, details="", error_msg=""):
        self.test_results[test_name] = {
            "passed": passed,
            "details": details,
            "error_msg": error_msg,
            "timestamp": datetime.now().isoformat()
        }
        
    def add_error(self, error_msg, traceback_str=""):
        self.errors.append({
            "error": error_msg,
            "traceback": traceback_str,
            "timestamp": datetime.now().isoformat()
        })
        
    def test_basic_imports(self):
        """测试基本导入"""
        try:
            # 测试PyQt6导入
            from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget
            from PyQt6.QtCore import QTimer, QThread, pyqtSignal
            from PyQt6.QtGui import QFont, QIcon
            self.add_test_result("pyqt6_import", True, "PyQt6核心模块导入成功")
            
            # 测试系统模块导入
            import psutil
            import json
            import yaml
            self.add_test_result("system_modules_import", True, "系统模块导入成功")
            
            return True
            
        except Exception as e:
            error_msg = f"基本导入测试失败: {str(e)}"
            self.add_test_result("basic_imports", False, error_msg=error_msg)
            self.add_error(error_msg, traceback.format_exc())
            return False
            
    def test_simple_ui_import(self):
        """测试simple_ui_fixed模块导入"""
        try:
            import simple_ui_fixed
            self.add_test_result("simple_ui_import", True, "simple_ui_fixed模块导入成功")
            
            # 检查主要类是否存在
            if hasattr(simple_ui_fixed, 'SimpleScreenplayApp'):
                self.add_test_result("main_class_exists", True, "SimpleScreenplayApp类存在")
            else:
                self.add_test_result("main_class_exists", False, "SimpleScreenplayApp类不存在")
                
            # 检查AlertManager是否存在
            if hasattr(simple_ui_fixed, 'AlertManager'):
                self.add_test_result("alert_manager_exists", True, "AlertManager类存在")
            else:
                self.add_test_result("alert_manager_exists", False, "AlertManager类不存在")
                
            return True
            
        except Exception as e:
            error_msg = f"simple_ui_fixed导入失败: {str(e)}"
            self.add_test_result("simple_ui_import", False, error_msg=error_msg)
            self.add_error(error_msg, traceback.format_exc())
            return False
            
    def test_ui_creation(self):
        """测试UI创建"""
        try:
            from PyQt6.QtWidgets import QApplication
            
            # 创建QApplication
            if not QApplication.instance():
                app = QApplication(sys.argv)
            else:
                app = QApplication.instance()
                
            self.add_test_result("qapplication_creation", True, "QApplication创建成功")
            
            # 尝试创建主窗口
            import simple_ui_fixed
            main_window = simple_ui_fixed.SimpleScreenplayApp()
            self.add_test_result("main_window_creation", True, "主窗口创建成功")
            
            # 测试窗口基本属性
            main_window.setWindowTitle("VisionAI-ClipsMaster v1.0.1 - 验证测试")
            main_window.resize(800, 600)
            self.add_test_result("window_properties", True, "窗口属性设置成功")
            
            # 测试AlertManager
            if hasattr(simple_ui_fixed, 'AlertManager'):
                alert_manager = simple_ui_fixed.AlertManager(main_window)
                alert_manager.show_alert("测试预警消息", "info")
                self.add_test_result("alert_manager_test", True, "AlertManager功能测试成功")
            else:
                self.add_test_result("alert_manager_test", False, "AlertManager不可用")
                
            # 清理
            main_window.close()
            
            return True
            
        except Exception as e:
            error_msg = f"UI创建测试失败: {str(e)}"
            self.add_test_result("ui_creation", False, error_msg=error_msg)
            self.add_error(error_msg, traceback.format_exc())
            return False
            
    def test_core_modules_availability(self):
        """测试核心模块可用性"""
        try:
            import simple_ui_fixed
            
            # 检查核心模块标志
            core_available = getattr(simple_ui_fixed, 'CORE_MODULES_AVAILABLE', False)
            self.add_test_result("core_modules_flag", core_available, 
                                f"核心模块可用性标志: {core_available}")
            
            # 检查ClipGenerator
            if hasattr(simple_ui_fixed, 'ClipGenerator'):
                clip_gen = simple_ui_fixed.ClipGenerator()
                methods_available = []

                # 检查关键方法
                if hasattr(clip_gen, 'generate_from_srt'):
                    methods_available.append("generate_from_srt")
                if hasattr(clip_gen, 'generate_clips'):
                    methods_available.append("generate_clips")
                if hasattr(clip_gen, 'export_jianying_project'):
                    methods_available.append("export_jianying_project")

                if len(methods_available) >= 2:  # 至少有2个关键方法
                    self.add_test_result("clip_generator_methods", True,
                                        f"ClipGenerator方法可用: {', '.join(methods_available)}")
                else:
                    self.add_test_result("clip_generator_methods", False,
                                        f"ClipGenerator方法不完整: {', '.join(methods_available)}")
            else:
                self.add_test_result("clip_generator_methods", False, "ClipGenerator不可用")
                
            # 检查ModelTrainer
            if hasattr(simple_ui_fixed, 'ModelTrainer'):
                trainer = simple_ui_fixed.ModelTrainer()
                self.add_test_result("model_trainer_available", True, "ModelTrainer可用")
            else:
                self.add_test_result("model_trainer_available", False, "ModelTrainer不可用")
                
            return True
            
        except Exception as e:
            error_msg = f"核心模块可用性测试失败: {str(e)}"
            self.add_test_result("core_modules_availability", False, error_msg=error_msg)
            self.add_error(error_msg, traceback.format_exc())
            return False
            
    def test_performance_monitoring(self):
        """测试性能监控功能"""
        try:
            import simple_ui_fixed
            
            # 测试AlertManager的性能监控功能
            if hasattr(simple_ui_fixed, 'AlertManager'):
                alert_manager = simple_ui_fixed.AlertManager()
                
                # 测试性能检查方法
                if hasattr(alert_manager, 'check_system_performance'):
                    alert_manager.check_system_performance()
                    self.add_test_result("performance_monitoring", True, "性能监控功能正常")
                else:
                    self.add_test_result("performance_monitoring", False, "性能监控方法缺失")
                    
                # 测试预警方法
                if hasattr(alert_manager, 'show_performance_alert'):
                    alert_manager.show_performance_alert("CPU", 85, 80, "%")
                    self.add_test_result("performance_alerts", True, "性能预警功能正常")
                else:
                    self.add_test_result("performance_alerts", False, "性能预警方法缺失")
            else:
                self.add_test_result("performance_monitoring", False, "AlertManager不可用")
                
            return True
            
        except Exception as e:
            error_msg = f"性能监控测试失败: {str(e)}"
            self.add_test_result("performance_monitoring", False, error_msg=error_msg)
            self.add_error(error_msg, traceback.format_exc())
            return False
            
    def run_all_tests(self):
        """运行所有验证测试"""
        print("🔍 开始VisionAI-ClipsMaster v1.0.1 UI组件完整性验证")
        print("=" * 60)
        
        # 测试序列
        tests = [
            ("基本导入测试", self.test_basic_imports),
            ("UI模块导入测试", self.test_simple_ui_import),
            ("UI创建测试", self.test_ui_creation),
            ("核心模块可用性测试", self.test_core_modules_availability),
            ("性能监控测试", self.test_performance_monitoring),
        ]
        
        for test_name, test_func in tests:
            print(f"🧪 执行测试: {test_name}")
            try:
                success = test_func()
                status = "✅ 通过" if success else "❌ 失败"
                print(f"   {status}")
            except Exception as e:
                print(f"   ❌ 异常: {str(e)}")
                self.add_error(f"{test_name}异常", traceback.format_exc())
                
        return self.generate_report()
        
    def generate_report(self):
        """生成验证报告"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results.values() if r['passed'])
        failed_tests = total_tests - passed_tests
        
        print("\n" + "=" * 60)
        print("📊 UI组件完整性验证报告")
        print("=" * 60)
        print(f"总测试数: {total_tests}")
        print(f"通过: {passed_tests}")
        print(f"失败: {failed_tests}")
        print(f"成功率: {(passed_tests/total_tests*100):.1f}%")
        
        print("\n📋 详细测试结果:")
        for test_name, result in self.test_results.items():
            status = "✅" if result['passed'] else "❌"
            print(f"{status} {test_name}: {result.get('details', '')}")
            if result.get('error_msg'):
                print(f"   错误: {result['error_msg']}")
                
        if self.errors:
            print("\n🚨 错误详情:")
            for i, error in enumerate(self.errors, 1):
                print(f"{i}. {error['error']}")
                
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'success_rate': passed_tests / total_tests * 100 if total_tests > 0 else 0,
            'test_results': self.test_results,
            'errors': self.errors
        }

def main():
    """主函数"""
    verifier = UIComponentVerifier()
    result = verifier.run_all_tests()
    return result

if __name__ == "__main__":
    main()
