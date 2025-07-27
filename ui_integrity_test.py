#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster UI界面完整性测试
测试所有UI组件的加载、显示和基本交互功能
"""

import sys
import os
import json
import traceback
from datetime import datetime
from pathlib import Path
import warnings

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

# 设置Qt环境变量（避免一些警告）
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = ''

class UIIntegrityTester:
    def __init__(self):
        self.results = {
            "test_time": datetime.now().isoformat(),
            "total_components": 0,
            "successful_loads": 0,
            "failed_loads": 0,
            "ui_test_results": {},
            "warnings": [],
            "errors": []
        }
        
        # UI组件列表
        self.ui_components = [
            {
                "name": "主窗口",
                "module": "ui.main_window",
                "class": "MainWindow"
            },
            {
                "name": "训练面板",
                "module": "ui.training_panel", 
                "class": "TrainingPanel"
            },
            {
                "name": "进度看板",
                "module": "ui.progress_dashboard",
                "class": "ProgressDashboard"
            },
            {
                "name": "实时图表",
                "module": "ui.components.realtime_charts",
                "class": "RealtimeCharts"
            },
            {
                "name": "警告管理器",
                "module": "ui.components.alert_manager",
                "class": "AlertManager"
            }
        ]

    def test_qt_availability(self):
        """测试Qt库的可用性"""
        print("检查Qt库可用性...")
        
        try:
            # 尝试导入PyQt6
            import PyQt6.QtWidgets as QtWidgets
            import PyQt6.QtCore as QtCore
            import PyQt6.QtGui as QtGui
            
            print("  ✓ PyQt6可用")
            
            # 创建QApplication实例（如果不存在）
            app = QtWidgets.QApplication.instance()
            if app is None:
                app = QtWidgets.QApplication(sys.argv)
                print("  ✓ QApplication创建成功")
            else:
                print("  ✓ QApplication已存在")
            
            return True, app
            
        except ImportError as e:
            print(f"  ✗ PyQt6导入失败: {e}")
            
            # 尝试导入PyQt5作为备选
            try:
                import PyQt5.QtWidgets as QtWidgets
                import PyQt5.QtCore as QtCore
                import PyQt5.QtGui as QtGui
                
                print("  ✓ PyQt5可用（备选）")
                
                app = QtWidgets.QApplication.instance()
                if app is None:
                    app = QtWidgets.QApplication(sys.argv)
                    print("  ✓ QApplication创建成功")
                
                return True, app
                
            except ImportError as e2:
                print(f"  ✗ PyQt5也不可用: {e2}")
                return False, None

    def test_component_import(self, component):
        """测试单个UI组件的导入"""
        try:
            print(f"  导入模块: {component['module']}")
            
            # 导入模块
            module = __import__(component['module'], fromlist=[component['class']])
            
            # 获取类
            if hasattr(module, component['class']):
                component_class = getattr(module, component['class'])
                print(f"    ✓ 类 {component['class']} 导入成功")
                return True, component_class
            else:
                print(f"    ✗ 类 {component['class']} 不存在")
                return False, None
                
        except Exception as e:
            print(f"    ✗ 导入失败: {e}")
            return False, None

    def test_component_creation(self, component_class, component_name):
        """测试UI组件的创建"""
        try:
            print(f"    创建 {component_name} 实例...")
            
            # 尝试创建实例
            if component_name == "主窗口":
                # 主窗口可能需要特殊处理
                instance = component_class()
            else:
                # 其他组件可能需要父窗口
                instance = component_class()
            
            print(f"    ✓ {component_name} 创建成功")
            return True, instance
            
        except Exception as e:
            print(f"    ✗ {component_name} 创建失败: {e}")
            return False, None

    def test_component_basic_functionality(self, instance, component_name):
        """测试UI组件的基本功能"""
        try:
            print(f"    测试 {component_name} 基本功能...")
            
            # 基本属性测试
            if hasattr(instance, 'show'):
                print(f"      ✓ 有show方法")
            
            if hasattr(instance, 'hide'):
                print(f"      ✓ 有hide方法")
            
            if hasattr(instance, 'setWindowTitle'):
                print(f"      ✓ 有setWindowTitle方法")
            
            # 尝试设置基本属性
            if hasattr(instance, 'resize'):
                instance.resize(800, 600)
                print(f"      ✓ 可以调整大小")
            
            print(f"    ✓ {component_name} 基本功能正常")
            return True
            
        except Exception as e:
            print(f"    ✗ {component_name} 基本功能测试失败: {e}")
            return False

    def run_comprehensive_ui_test(self):
        """运行全面的UI测试"""
        print("=" * 60)
        print("VisionAI-ClipsMaster UI界面完整性测试")
        print("=" * 60)
        
        # 首先测试Qt库可用性
        qt_available, app = self.test_qt_availability()
        if not qt_available:
            print("Qt库不可用，无法进行UI测试")
            self.results["errors"].append("Qt库不可用")
            return self.results
        
        self.results["total_components"] = len(self.ui_components)
        
        print(f"\n测试 {len(self.ui_components)} 个UI组件...")
        
        for i, component in enumerate(self.ui_components, 1):
            print(f"\n[{i:2d}/{len(self.ui_components)}] 测试组件: {component['name']}")
            
            component_result = {
                "import_success": False,
                "creation_success": False,
                "functionality_success": False,
                "errors": []
            }
            
            # 测试导入
            import_success, component_class = self.test_component_import(component)
            component_result["import_success"] = import_success
            
            if import_success:
                # 测试创建
                creation_success, instance = self.test_component_creation(
                    component_class, component['name']
                )
                component_result["creation_success"] = creation_success
                
                if creation_success:
                    # 测试基本功能
                    functionality_success = self.test_component_basic_functionality(
                        instance, component['name']
                    )
                    component_result["functionality_success"] = functionality_success
                    
                    # 清理实例
                    try:
                        if hasattr(instance, 'close'):
                            instance.close()
                        del instance
                    except:
                        pass
            
            self.results["ui_test_results"][component['name']] = component_result
            
            # 统计成功/失败
            if (component_result["import_success"] and 
                component_result["creation_success"] and 
                component_result["functionality_success"]):
                self.results["successful_loads"] += 1
                print(f"  ✓ {component['name']} 测试通过")
            else:
                self.results["failed_loads"] += 1
                print(f"  ✗ {component['name']} 测试失败")
        
        # 生成报告
        self.generate_ui_report()
        
        return self.results

    def generate_ui_report(self):
        """生成UI测试报告"""
        print("\n" + "=" * 60)
        print("UI测试结果汇总")
        print("=" * 60)
        
        print(f"总组件数: {self.results['total_components']}")
        print(f"测试通过: {self.results['successful_loads']}")
        print(f"测试失败: {self.results['failed_loads']}")
        print(f"成功率: {(self.results['successful_loads']/self.results['total_components']*100):.1f}%")
        
        if self.results["failed_loads"] > 0:
            print(f"\n失败的组件:")
            for component_name, result in self.results["ui_test_results"].items():
                if not (result["import_success"] and result["creation_success"] and result["functionality_success"]):
                    status = []
                    if not result["import_success"]:
                        status.append("导入失败")
                    if not result["creation_success"]:
                        status.append("创建失败")
                    if not result["functionality_success"]:
                        status.append("功能测试失败")
                    print(f"  - {component_name}: {', '.join(status)}")
        
        # 保存详细报告
        report_file = f"ui_integrity_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        print(f"\n详细报告已保存到: {report_file}")

if __name__ == "__main__":
    tester = UIIntegrityTester()
    results = tester.run_comprehensive_ui_test()
    
    # 返回退出码
    if results["failed_loads"] > 0:
        sys.exit(1)
    else:
        sys.exit(0)
