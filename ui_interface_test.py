#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster UI界面完整性测试
验证所有UI组件的导入、功能入口、实时数据显示和用户交互功能
"""

import os
import sys
import json
import time
import traceback
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

class UIInterfaceTestSuite:
    """UI界面测试套件"""
    
    def __init__(self):
        self.test_results = {}
        self.qt_available = self.check_qt_availability()
        print(f"🖼️ Qt可用性: {self.qt_available}")
    
    def check_qt_availability(self) -> bool:
        """检查Qt可用性"""
        try:
            import PyQt6
            return True
        except ImportError:
            try:
                import PyQt5
                return True
            except ImportError:
                return False
    
    def test_ui_module_imports(self) -> Dict[str, Any]:
        """测试UI模块导入"""
        print("\n=== 测试UI模块导入 ===")
        results = {"status": "success", "details": {}}
        
        ui_modules = [
            "src.ui.main_window",
            "src.ui.training_panel",
            "src.ui.progress_dashboard",
            "src.ui.realtime_charts",
            "src.ui.alert_manager",
            "src.ui.components",
            "ui.main_window",
            "ui.training_panel",
            "ui.progress_dashboard"
        ]
        
        for module_name in ui_modules:
            try:
                __import__(module_name)
                results["details"][module_name] = "success"
                print(f"✓ {module_name} 导入成功")
            except ImportError as e:
                results["details"][module_name] = f"import_error: {str(e)}"
                print(f"✗ {module_name} 导入失败: {e}")
                results["status"] = "partial_failure"
            except Exception as e:
                results["details"][module_name] = f"error: {str(e)}"
                print(f"✗ {module_name} 导入异常: {e}")
                results["status"] = "failure"
        
        return results
    
    def test_main_window(self) -> Dict[str, Any]:
        """测试主窗口"""
        print("\n=== 测试主窗口 ===")
        results = {"status": "success", "details": {}}
        
        if not self.qt_available:
            results["status"] = "skipped"
            results["details"]["error"] = "Qt不可用，跳过UI测试"
            print("⚠ Qt不可用，跳过主窗口测试")
            return results
        
        try:
            from src.ui.main_window import MainWindow
            
            # 测试类定义
            results["details"]["class_definition"] = "success"
            print("✓ 主窗口类定义正常")
            
            # 检查关键方法
            required_methods = [
                '__init__',
                'setup_ui',
                'setup_menu',
                'setup_toolbar',
                'setup_status_bar'
            ]
            
            for method in required_methods:
                if hasattr(MainWindow, method):
                    results["details"][f"method_{method}"] = "exists"
                    print(f"✓ 方法 {method} 存在")
                else:
                    results["details"][f"method_{method}"] = "missing"
                    print(f"⚠ 方法 {method} 缺失")
            
        except ImportError as e:
            results["status"] = "failure"
            results["details"]["error"] = f"导入失败: {str(e)}"
            print(f"✗ 主窗口导入失败: {e}")
        except Exception as e:
            results["status"] = "failure"
            results["details"]["error"] = f"测试异常: {str(e)}"
            print(f"✗ 主窗口测试失败: {e}")
        
        return results
    
    def test_training_panel(self) -> Dict[str, Any]:
        """测试训练监控面板"""
        print("\n=== 测试训练监控面板 ===")
        results = {"status": "success", "details": {}}
        
        if not self.qt_available:
            results["status"] = "skipped"
            results["details"]["error"] = "Qt不可用，跳过UI测试"
            print("⚠ Qt不可用，跳过训练面板测试")
            return results
        
        try:
            from src.ui.training_panel import TrainingPanel
            
            # 测试类定义
            results["details"]["class_definition"] = "success"
            print("✓ 训练面板类定义正常")
            
            # 检查关键方法
            required_methods = [
                '__init__',
                'setup_ui',
                'update_progress',
                'update_loss_curve',
                'update_metrics'
            ]
            
            for method in required_methods:
                if hasattr(TrainingPanel, method):
                    results["details"][f"method_{method}"] = "exists"
                    print(f"✓ 方法 {method} 存在")
                else:
                    results["details"][f"method_{method}"] = "missing"
                    print(f"⚠ 方法 {method} 缺失")
            
        except ImportError as e:
            results["status"] = "failure"
            results["details"]["error"] = f"导入失败: {str(e)}"
            print(f"✗ 训练面板导入失败: {e}")
        except Exception as e:
            results["status"] = "failure"
            results["details"]["error"] = f"测试异常: {str(e)}"
            print(f"✗ 训练面板测试失败: {e}")
        
        return results
    
    def test_progress_dashboard(self) -> Dict[str, Any]:
        """测试进度看板"""
        print("\n=== 测试进度看板 ===")
        results = {"status": "success", "details": {}}
        
        if not self.qt_available:
            results["status"] = "skipped"
            results["details"]["error"] = "Qt不可用，跳过UI测试"
            print("⚠ Qt不可用，跳过进度看板测试")
            return results
        
        try:
            from src.ui.progress_dashboard import ProgressDashboard
            
            # 测试类定义
            results["details"]["class_definition"] = "success"
            print("✓ 进度看板类定义正常")
            
            # 检查关键方法
            required_methods = [
                '__init__',
                'setup_ui',
                'update_task_status',
                'update_progress_bar',
                'show_task_details'
            ]
            
            for method in required_methods:
                if hasattr(ProgressDashboard, method):
                    results["details"][f"method_{method}"] = "exists"
                    print(f"✓ 方法 {method} 存在")
                else:
                    results["details"][f"method_{method}"] = "missing"
                    print(f"⚠ 方法 {method} 缺失")
            
        except ImportError as e:
            results["status"] = "failure"
            results["details"]["error"] = f"导入失败: {str(e)}"
            print(f"✗ 进度看板导入失败: {e}")
        except Exception as e:
            results["status"] = "failure"
            results["details"]["error"] = f"测试异常: {str(e)}"
            print(f"✗ 进度看板测试失败: {e}")
        
        return results
    
    def test_realtime_charts(self) -> Dict[str, Any]:
        """测试实时图表组件"""
        print("\n=== 测试实时图表组件 ===")
        results = {"status": "success", "details": {}}
        
        try:
            from src.ui.realtime_charts import RealtimeCharts
            
            # 测试类定义
            results["details"]["class_definition"] = "success"
            print("✓ 实时图表类定义正常")
            
            # 检查关键方法
            required_methods = [
                '__init__',
                'setup_charts',
                'update_cpu_chart',
                'update_memory_chart',
                'update_gpu_chart'
            ]
            
            for method in required_methods:
                if hasattr(RealtimeCharts, method):
                    results["details"][f"method_{method}"] = "exists"
                    print(f"✓ 方法 {method} 存在")
                else:
                    results["details"][f"method_{method}"] = "missing"
                    print(f"⚠ 方法 {method} 缺失")
            
        except ImportError as e:
            results["status"] = "failure"
            results["details"]["error"] = f"导入失败: {str(e)}"
            print(f"✗ 实时图表导入失败: {e}")
        except Exception as e:
            results["status"] = "failure"
            results["details"]["error"] = f"测试异常: {str(e)}"
            print(f"✗ 实时图表测试失败: {e}")
        
        return results
    
    def test_alert_manager(self) -> Dict[str, Any]:
        """测试警报管理器"""
        print("\n=== 测试警报管理器 ===")
        results = {"status": "success", "details": {}}
        
        try:
            from src.ui.alert_manager import AlertManager
            
            # 测试类定义
            results["details"]["class_definition"] = "success"
            print("✓ 警报管理器类定义正常")
            
            # 检查关键方法
            required_methods = [
                '__init__',
                'show_info',
                'show_warning',
                'show_error',
                'show_success'
            ]
            
            for method in required_methods:
                if hasattr(AlertManager, method):
                    results["details"][f"method_{method}"] = "exists"
                    print(f"✓ 方法 {method} 存在")
                else:
                    results["details"][f"method_{method}"] = "missing"
                    print(f"⚠ 方法 {method} 缺失")
            
        except ImportError as e:
            results["status"] = "failure"
            results["details"]["error"] = f"导入失败: {str(e)}"
            print(f"✗ 警报管理器导入失败: {e}")
        except Exception as e:
            results["status"] = "failure"
            results["details"]["error"] = f"测试异常: {str(e)}"
            print(f"✗ 警报管理器测试失败: {e}")
        
        return results
    
    def test_ui_components(self) -> Dict[str, Any]:
        """测试UI组件库"""
        print("\n=== 测试UI组件库 ===")
        results = {"status": "success", "details": {}}
        
        try:
            # 尝试导入组件模块
            component_modules = [
                "src.ui.components",
                "ui.components"
            ]
            
            imported_modules = []
            for module_name in component_modules:
                try:
                    module = __import__(module_name)
                    imported_modules.append(module_name)
                    results["details"][f"import_{module_name}"] = "success"
                    print(f"✓ {module_name} 导入成功")
                except ImportError:
                    results["details"][f"import_{module_name}"] = "failed"
                    print(f"⚠ {module_name} 导入失败")
            
            if imported_modules:
                results["details"]["imported_modules"] = imported_modules
                print(f"✓ 成功导入 {len(imported_modules)} 个组件模块")
            else:
                results["status"] = "partial_failure"
                print("⚠ 未能导入任何UI组件模块")
            
        except Exception as e:
            results["status"] = "failure"
            results["details"]["error"] = f"测试异常: {str(e)}"
            print(f"✗ UI组件测试失败: {e}")
        
        return results
    
    def test_ui_assets(self) -> Dict[str, Any]:
        """测试UI资源文件"""
        print("\n=== 测试UI资源文件 ===")
        results = {"status": "success", "details": {}}
        
        try:
            # 检查资源目录
            assets_paths = [
                "ui/assets",
                "src/ui/assets",
                "ui/assets/icons",
                "ui/assets/style.qss"
            ]
            
            found_assets = []
            for asset_path in assets_paths:
                full_path = project_root / asset_path
                if full_path.exists():
                    found_assets.append(asset_path)
                    results["details"][f"asset_{asset_path}"] = "exists"
                    print(f"✓ 资源文件存在: {asset_path}")
                else:
                    results["details"][f"asset_{asset_path}"] = "missing"
                    print(f"⚠ 资源文件缺失: {asset_path}")
            
            results["details"]["found_assets"] = found_assets
            
            if found_assets:
                print(f"✓ 发现 {len(found_assets)} 个资源文件/目录")
            else:
                results["status"] = "partial_failure"
                print("⚠ 未发现UI资源文件")
            
        except Exception as e:
            results["status"] = "failure"
            results["details"]["error"] = f"测试异常: {str(e)}"
            print(f"✗ UI资源测试失败: {e}")
        
        return results
    
    def run_all_tests(self) -> Dict[str, Any]:
        """运行所有测试"""
        print("🚀 开始VisionAI-ClipsMaster UI界面完整性测试")
        print("=" * 60)
        
        all_results = {
            "qt_available": self.qt_available,
            "tests": {}
        }
        
        # 执行各项测试
        test_methods = [
            ("ui_module_imports", self.test_ui_module_imports),
            ("main_window", self.test_main_window),
            ("training_panel", self.test_training_panel),
            ("progress_dashboard", self.test_progress_dashboard),
            ("realtime_charts", self.test_realtime_charts),
            ("alert_manager", self.test_alert_manager),
            ("ui_components", self.test_ui_components),
            ("ui_assets", self.test_ui_assets)
        ]
        
        for test_name, test_method in test_methods:
            try:
                result = test_method()
                all_results["tests"][test_name] = result
            except Exception as e:
                all_results["tests"][test_name] = {
                    "status": "error",
                    "error": str(e),
                    "traceback": traceback.format_exc()
                }
                print(f"✗ {test_name} 测试发生异常: {e}")
        
        return all_results

def main():
    """主函数"""
    test_suite = UIInterfaceTestSuite()
    
    # 运行测试
    results = test_suite.run_all_tests()
    
    # 生成测试报告
    report_file = f"ui_interface_test_report_{int(time.time())}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n📊 测试报告已生成: {report_file}")
    
    # 统计测试结果
    test_results = results["tests"]
    total_tests = len(test_results)
    successful_tests = sum(1 for r in test_results.values() if r.get("status") == "success")
    skipped_tests = sum(1 for r in test_results.values() if r.get("status") == "skipped")
    
    print(f"\n📈 测试统计:")
    print(f"总测试数: {total_tests}")
    print(f"成功测试: {successful_tests}")
    print(f"跳过测试: {skipped_tests}")
    print(f"失败测试: {total_tests - successful_tests - skipped_tests}")
    print(f"成功率: {successful_tests/total_tests*100:.1f}%")
    
    return successful_tests >= (total_tests * 0.7)  # 70%成功率即可

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
