#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster UI组件详细测试
测试UI界面的各个组件和功能
"""

import sys
import os
import time
import json
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class UIComponentTester:
    def __init__(self):
        self.test_results = {
            "test_start_time": datetime.now().isoformat(),
            "ui_component_tests": {},
            "training_panel_tests": {},
            "progress_dashboard_tests": {},
            "theme_tests": {},
            "overall_status": "RUNNING"
        }
        self.output_dir = Path("test_output")
        self.output_dir.mkdir(exist_ok=True)
    
    def log_test_result(self, category, test_name, status, details=None, error=None):
        """记录测试结果"""
        result = {
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "details": details or {},
            "error": error
        }
        self.test_results[category][test_name] = result
        print(f"[{status}] {category}.{test_name}: {details.get('message', '') if details else ''}")
        if error:
            print(f"    错误: {error}")
    
    def test_main_ui_components(self):
        """测试主UI组件"""
        print("\n=== UI组件测试 ===")
        
        # 测试UI主窗口类
        try:
            from ui.main_window import MainWindow
            self.log_test_result("ui_component_tests", "main_window_import", "PASS", 
                               {"message": "主窗口类导入成功"})
        except ImportError as e:
            self.log_test_result("ui_component_tests", "main_window_import", "FAIL", 
                               {"message": "主窗口类导入失败"}, str(e))
        
        # 测试实时图表组件
        try:
            from ui.components.realtime_charts import RealtimeCharts
            self.log_test_result("ui_component_tests", "realtime_charts", "PASS",
                               {"message": "实时图表组件导入成功"})
        except ImportError as e:
            self.log_test_result("ui_component_tests", "realtime_charts", "FAIL",
                               {"message": "实时图表组件导入失败"}, str(e))

        # 测试警报管理器
        try:
            from ui.components.alert_manager import AlertManager
            self.log_test_result("ui_component_tests", "alert_manager", "PASS",
                               {"message": "警报管理器导入成功"})
        except ImportError as e:
            self.log_test_result("ui_component_tests", "alert_manager", "FAIL",
                               {"message": "警报管理器导入失败"}, str(e))

        # 测试样式管理器
        try:
            from ui.utils.style_manager import StyleManager
            style_mgr = StyleManager()
            self.log_test_result("ui_component_tests", "style_manager", "PASS",
                               {"message": "样式管理器导入成功"})
        except ImportError as e:
            self.log_test_result("ui_component_tests", "style_manager", "FAIL",
                               {"message": "样式管理器导入失败"}, str(e))
    
    def test_training_panel(self):
        """测试训练监控面板"""
        print("\n=== 训练监控面板测试 ===")
        
        try:
            from ui.training_panel import TrainingPanel
            panel = TrainingPanel()
            self.log_test_result("training_panel_tests", "training_panel_import", "PASS", 
                               {"message": "训练面板导入成功"})
            
            # 测试面板初始化
            if hasattr(panel, 'setup_ui'):
                self.log_test_result("training_panel_tests", "setup_ui_method", "PASS", 
                                   {"message": "setup_ui方法存在"})
            else:
                self.log_test_result("training_panel_tests", "setup_ui_method", "FAIL", 
                                   {"message": "setup_ui方法不存在"})
            
            # 测试训练状态更新
            if hasattr(panel, 'update_training_status'):
                self.log_test_result("training_panel_tests", "update_status_method", "PASS", 
                                   {"message": "update_training_status方法存在"})
            else:
                self.log_test_result("training_panel_tests", "update_status_method", "FAIL", 
                                   {"message": "update_training_status方法不存在"})
                
        except ImportError as e:
            self.log_test_result("training_panel_tests", "training_panel_import", "FAIL", 
                               {"message": "训练面板导入失败"}, str(e))
    
    def test_progress_dashboard(self):
        """测试进度看板"""
        print("\n=== 进度看板测试 ===")
        
        try:
            from ui.progress_dashboard import ProgressDashboard
            dashboard = ProgressDashboard()
            self.log_test_result("progress_dashboard_tests", "progress_dashboard_import", "PASS", 
                               {"message": "进度看板导入成功"})
            
            # 测试进度更新方法
            if hasattr(dashboard, 'update_progress'):
                self.log_test_result("progress_dashboard_tests", "update_progress_method", "PASS", 
                                   {"message": "update_progress方法存在"})
            else:
                self.log_test_result("progress_dashboard_tests", "update_progress_method", "FAIL", 
                                   {"message": "update_progress方法不存在"})
            
            # 测试可视化功能
            if hasattr(dashboard, 'create_visualization'):
                self.log_test_result("progress_dashboard_tests", "visualization_method", "PASS", 
                                   {"message": "create_visualization方法存在"})
            else:
                self.log_test_result("progress_dashboard_tests", "visualization_method", "FAIL", 
                                   {"message": "create_visualization方法不存在"})
                
        except ImportError as e:
            self.log_test_result("progress_dashboard_tests", "progress_dashboard_import", "FAIL", 
                               {"message": "进度看板导入失败"}, str(e))
    
    def test_theme_functionality(self):
        """测试主题功能"""
        print("\n=== 主题功能测试 ===")
        
        # 测试主题设置对话框
        try:
            from ui.theme_settings_dialog import ThemeSettingsDialog
            dialog = ThemeSettingsDialog()
            self.log_test_result("theme_tests", "theme_dialog_import", "PASS", 
                               {"message": "主题设置对话框导入成功"})
        except ImportError as e:
            self.log_test_result("theme_tests", "theme_dialog_import", "FAIL", 
                               {"message": "主题设置对话框导入失败"}, str(e))
        
        # 测试主题切换器
        try:
            from ui.theme_switcher import ThemeSwitcher
            switcher = ThemeSwitcher()
            self.log_test_result("theme_tests", "theme_switcher_import", "PASS", 
                               {"message": "主题切换器导入成功"})
        except ImportError as e:
            self.log_test_result("theme_tests", "theme_switcher_import", "FAIL", 
                               {"message": "主题切换器导入失败"}, str(e))
        
        # 测试样式管理器
        try:
            from ui.enhanced_style_manager import EnhancedStyleManager
            style_mgr = EnhancedStyleManager()
            self.log_test_result("theme_tests", "style_manager_import", "PASS", 
                               {"message": "样式管理器导入成功"})
        except ImportError as e:
            self.log_test_result("theme_tests", "style_manager_import", "FAIL", 
                               {"message": "样式管理器导入失败"}, str(e))
    
    def generate_report(self):
        """生成测试报告"""
        self.test_results["test_end_time"] = datetime.now().isoformat()
        
        # 统计测试结果
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        
        for category in ["ui_component_tests", "training_panel_tests", "progress_dashboard_tests", "theme_tests"]:
            for test_name, result in self.test_results[category].items():
                total_tests += 1
                if result["status"] == "PASS":
                    passed_tests += 1
                elif result["status"] == "FAIL":
                    failed_tests += 1
        
        # 确定整体状态
        if failed_tests > 0:
            self.test_results["overall_status"] = "FAIL"
        elif passed_tests > 0:
            self.test_results["overall_status"] = "PASS"
        else:
            self.test_results["overall_status"] = "SKIP"
        
        self.test_results["summary"] = {
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "success_rate": f"{(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "0%"
        }
        
        # 保存测试报告
        report_file = self.output_dir / f"ui_component_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, ensure_ascii=False, indent=2)
        
        print(f"\n=== UI组件测试报告 ===")
        print(f"总测试数: {total_tests}")
        print(f"通过: {passed_tests}")
        print(f"失败: {failed_tests}")
        print(f"成功率: {self.test_results['summary']['success_rate']}")
        print(f"整体状态: {self.test_results['overall_status']}")
        print(f"详细报告已保存到: {report_file}")
        
        return self.test_results
    
    def run_all_tests(self):
        """运行所有UI组件测试"""
        print("开始VisionAI-ClipsMaster UI组件测试...")
        print(f"测试开始时间: {self.test_results['test_start_time']}")
        
        try:
            self.test_main_ui_components()
            self.test_training_panel()
            self.test_progress_dashboard()
            self.test_theme_functionality()
        except Exception as e:
            print(f"测试执行异常: {e}")
        finally:
            return self.generate_report()

if __name__ == "__main__":
    ui_tester = UIComponentTester()
    results = ui_tester.run_all_tests()
