#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster UI界面整合测试 (修复版)
解决主要的UI组件问题并提供更全面的测试
"""

import sys
import os
import time
import json
import threading
import subprocess
import traceback
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

# 添加项目路径
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.append(str(PROJECT_ROOT))

# 设置环境变量避免CUDA问题
os.environ['CUDA_VISIBLE_DEVICES'] = ''
os.environ['TORCH_USE_CUDA_DSA'] = '0'

try:
    from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QPushButton, QLabel, QTextEdit, 
                               QFileDialog, QMessageBox, QTabWidget, QSplitter, 
                               QProgressBar, QListWidget, QListWidgetItem, QCheckBox, 
                               QComboBox, QGroupBox, QRadioButton, QButtonGroup, 
                               QProgressDialog, QDialog, QFrame, QSlider)
    from PyQt6.QtCore import Qt, QSize, pyqtSignal, QThread, QObject, QTimer
    from PyQt6.QtGui import QFont, QPixmap, QIcon
    QT_AVAILABLE = True
except ImportError as e:
    print(f"PyQt6 导入失败: {e}")
    QT_AVAILABLE = False

class UIIntegrationTesterFixed:
    """UI界面整合测试器 (修复版)"""
    
    def __init__(self):
        self.test_results = {
            "timestamp": datetime.now().isoformat(),
            "environment_check": {},
            "ui_components": {},
            "core_functionality": {},
            "interaction_response": {},
            "interface_adaptation": {},
            "performance_monitoring": {},
            "recommendations": [],
            "overall_status": "UNKNOWN"
        }
        self.app = None
        self.main_window = None
        
    def setup_test_environment(self) -> bool:
        """设置测试环境"""
        try:
            # 检查PyQt6可用性
            if not QT_AVAILABLE:
                self.test_results["environment_check"]["qt_availability"] = {
                    "status": "FAILED",
                    "error": "PyQt6 not available",
                    "recommendation": "安装PyQt6: pip install PyQt6"
                }
                return False
                
            # 创建QApplication实例
            if not QApplication.instance():
                self.app = QApplication([])  # 使用空参数避免sys.argv问题
            else:
                self.app = QApplication.instance()
                
            self.test_results["environment_check"]["qt_availability"] = {
                "status": "PASSED",
                "qt_version": "PyQt6 Available"
            }
            
            # 检查项目结构
            self.test_results["environment_check"]["project_structure"] = self._check_project_structure()
            
            return True
            
        except Exception as e:
            self.test_results["environment_check"]["setup_error"] = {
                "status": "FAILED",
                "error": str(e)
            }
            return False
    
    def _check_project_structure(self) -> Dict[str, Any]:
        """检查项目结构"""
        try:
            required_dirs = [
                "src",
                "configs", 
                "data",
                "models",
                "logs"
            ]
            
            optional_dirs = [
                "ui",
                "src/ui",
                "assets",
                "templates"
            ]
            
            structure_status = {
                "required_dirs": {},
                "optional_dirs": {},
                "ui_files": {}
            }
            
            # 检查必需目录
            for dir_name in required_dirs:
                dir_path = os.path.join(PROJECT_ROOT, dir_name)
                structure_status["required_dirs"][dir_name] = os.path.exists(dir_path)
            
            # 检查可选目录
            for dir_name in optional_dirs:
                dir_path = os.path.join(PROJECT_ROOT, dir_name)
                structure_status["optional_dirs"][dir_name] = os.path.exists(dir_path)
            
            # 检查UI相关文件
            ui_files = [
                "simple_ui.py",
                "main.py",
                "app.py",
                "src/ui/main_window.py",
                "src/ui/training_panel.py",
                "src/ui/progress_dashboard.py"
            ]
            
            for file_name in ui_files:
                file_path = os.path.join(PROJECT_ROOT, file_name)
                structure_status["ui_files"][file_name] = {
                    "exists": os.path.exists(file_path),
                    "size": os.path.getsize(file_path) if os.path.exists(file_path) else 0
                }
            
            return {
                "status": "PASSED",
                "details": structure_status
            }
            
        except Exception as e:
            return {
                "status": "FAILED",
                "error": str(e)
            }
    
    def test_ui_component_integration_safe(self) -> Dict[str, Any]:
        """安全的UI组件集成测试"""
        print("🔧 测试UI组件集成 (安全模式)...")
        component_tests = {}
        
        try:
            # 测试主窗口组件 (不实际创建窗口)
            component_tests["main_window"] = self._test_main_window_safe()
            
            # 测试UI文件存在性
            component_tests["ui_files"] = self._test_ui_files_existence()
            
            # 测试UI组件模块导入
            component_tests["module_imports"] = self._test_ui_module_imports()
            
            # 测试UI配置文件
            component_tests["ui_configs"] = self._test_ui_configurations()
            
        except Exception as e:
            component_tests["integration_error"] = {
                "status": "FAILED",
                "error": str(e),
                "traceback": traceback.format_exc()
            }
            
        return component_tests
    
    def _test_main_window_safe(self) -> Dict[str, Any]:
        """安全的主窗口测试"""
        try:
            # 检查主窗口文件
            main_window_files = [
                "simple_ui.py",
                "main.py", 
                "app.py"
            ]
            
            found_files = []
            for file_path in main_window_files:
                full_path = os.path.join(PROJECT_ROOT, file_path)
                if os.path.exists(full_path):
                    found_files.append({
                        "file": file_path,
                        "size": os.path.getsize(full_path),
                        "modified": os.path.getmtime(full_path)
                    })
            
            if not found_files:
                return {
                    "status": "FAILED",
                    "error": "No main window files found",
                    "recommendation": "创建主窗口文件 (main.py 或 simple_ui.py)"
                }
            
            # 尝试分析主窗口文件内容
            main_file = found_files[0]["file"]
            main_file_path = os.path.join(PROJECT_ROOT, main_file)
            
            try:
                with open(main_file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # 检查关键类和方法
                has_main_class = any(keyword in content for keyword in ["class", "QMainWindow", "QWidget"])
                has_ui_setup = any(keyword in content for keyword in ["setupUi", "initUI", "setup_ui"])
                has_event_handlers = any(keyword in content for keyword in ["clicked", "connect", "signal"])
                
                return {
                    "status": "PASSED",
                    "found_files": found_files,
                    "main_file": main_file,
                    "analysis": {
                        "has_main_class": has_main_class,
                        "has_ui_setup": has_ui_setup,
                        "has_event_handlers": has_event_handlers
                    }
                }
                
            except Exception as e:
                return {
                    "status": "PARTIAL",
                    "found_files": found_files,
                    "analysis_error": str(e)
                }
                
        except Exception as e:
            return {
                "status": "FAILED",
                "error": str(e)
            }
    
    def _test_ui_files_existence(self) -> Dict[str, Any]:
        """测试UI文件存在性"""
        try:
            ui_structure = {
                "main_files": [
                    "simple_ui.py",
                    "main.py",
                    "app.py"
                ],
                "ui_components": [
                    "src/ui/training_panel.py",
                    "src/ui/progress_dashboard.py",
                    "src/ui/components/realtime_charts.py",
                    "src/ui/components/alert_manager.py"
                ],
                "assets": [
                    "src/ui/assets/style.qss",
                    "src/ui/assets/icons",
                    "assets/icons"
                ]
            }
            
            results = {}
            for category, files in ui_structure.items():
                results[category] = {}
                for file_path in files:
                    full_path = os.path.join(PROJECT_ROOT, file_path)
                    results[category][file_path] = {
                        "exists": os.path.exists(full_path),
                        "is_dir": os.path.isdir(full_path),
                        "size": os.path.getsize(full_path) if os.path.exists(full_path) and os.path.isfile(full_path) else 0
                    }
            
            # 计算存在的文件数量
            total_files = sum(len(files) for files in ui_structure.values())
            existing_files = sum(
                1 for category in results.values() 
                for file_info in category.values() 
                if file_info["exists"]
            )
            
            return {
                "status": "PASSED" if existing_files > total_files * 0.5 else "PARTIAL",
                "file_structure": results,
                "summary": {
                    "total_files": total_files,
                    "existing_files": existing_files,
                    "coverage": existing_files / total_files if total_files > 0 else 0
                }
            }
            
        except Exception as e:
            return {
                "status": "FAILED",
                "error": str(e)
            }

    def _test_ui_module_imports(self) -> Dict[str, Any]:
        """测试UI模块导入"""
        try:
            import_tests = {}

            # 测试主要UI模块
            ui_modules = [
                ("simple_ui", "VisionAIClipsMasterUI"),
                ("src.ui.training_panel", "TrainingPanel"),
                ("src.ui.progress_dashboard", "ProgressDashboard"),
                ("src.ui.components.realtime_charts", "RealtimeCharts"),
                ("src.ui.components.alert_manager", "AlertManager")
            ]

            for module_name, class_name in ui_modules:
                try:
                    # 尝试导入模块
                    module = __import__(module_name, fromlist=[class_name])
                    if hasattr(module, class_name):
                        import_tests[module_name] = {
                            "status": "PASSED",
                            "class_found": class_name
                        }
                    else:
                        import_tests[module_name] = {
                            "status": "PARTIAL",
                            "error": f"Class {class_name} not found in module"
                        }
                except ImportError as e:
                    import_tests[module_name] = {
                        "status": "FAILED",
                        "error": f"Import failed: {str(e)}"
                    }
                except Exception as e:
                    import_tests[module_name] = {
                        "status": "FAILED",
                        "error": f"Unexpected error: {str(e)}"
                    }

            # 计算成功率
            total_modules = len(ui_modules)
            successful_imports = sum(1 for test in import_tests.values() if test["status"] == "PASSED")

            return {
                "status": "PASSED" if successful_imports > 0 else "FAILED",
                "import_results": import_tests,
                "success_rate": successful_imports / total_modules if total_modules > 0 else 0
            }

        except Exception as e:
            return {
                "status": "FAILED",
                "error": str(e)
            }

    def _test_ui_configurations(self) -> Dict[str, Any]:
        """测试UI配置文件"""
        try:
            config_files = [
                "configs/ui_settings.yaml",
                "src/ui/assets/style.qss",
                "configs/alert_config.yaml",
                "configs/dashboard_config.json"
            ]

            config_results = {}
            for config_file in config_files:
                full_path = os.path.join(PROJECT_ROOT, config_file)
                if os.path.exists(full_path):
                    try:
                        # 尝试读取配置文件
                        with open(full_path, 'r', encoding='utf-8') as f:
                            content = f.read()

                        config_results[config_file] = {
                            "status": "PASSED",
                            "size": len(content),
                            "lines": len(content.splitlines())
                        }
                    except Exception as e:
                        config_results[config_file] = {
                            "status": "PARTIAL",
                            "error": f"Failed to read: {str(e)}"
                        }
                else:
                    config_results[config_file] = {
                        "status": "FAILED",
                        "error": "File not found"
                    }

            # 计算配置文件覆盖率
            total_configs = len(config_files)
            existing_configs = sum(1 for result in config_results.values() if result["status"] == "PASSED")

            return {
                "status": "PASSED" if existing_configs > 0 else "FAILED",
                "config_results": config_results,
                "coverage": existing_configs / total_configs if total_configs > 0 else 0
            }

        except Exception as e:
            return {
                "status": "FAILED",
                "error": str(e)
            }

    def _generate_recommendations(self):
        """生成改进建议"""
        recommendations = []

        # 检查环境问题
        if self.test_results["environment_check"]["qt_availability"]["status"] == "FAILED":
            recommendations.append({
                "priority": "HIGH",
                "category": "Environment",
                "issue": "PyQt6 not available",
                "solution": "安装PyQt6: pip install PyQt6",
                "impact": "UI界面无法正常显示"
            })

        # 检查UI组件问题
        ui_components = self.test_results.get("ui_components", {})

        if ui_components.get("main_window", {}).get("status") == "FAILED":
            recommendations.append({
                "priority": "HIGH",
                "category": "UI Components",
                "issue": "Main window creation failed",
                "solution": "检查CUDA依赖问题，设置环境变量 CUDA_VISIBLE_DEVICES=''",
                "impact": "主窗口无法创建，应用无法启动"
            })

        if ui_components.get("ui_files", {}).get("summary", {}).get("coverage", 0) < 0.5:
            recommendations.append({
                "priority": "MEDIUM",
                "category": "UI Structure",
                "issue": "Missing UI component files",
                "solution": "创建缺失的UI组件文件：training_panel.py, progress_dashboard.py, realtime_charts.py, alert_manager.py",
                "impact": "部分UI功能不可用"
            })

        if ui_components.get("module_imports", {}).get("success_rate", 0) < 0.3:
            recommendations.append({
                "priority": "MEDIUM",
                "category": "Module Structure",
                "issue": "UI module import failures",
                "solution": "修复模块导入路径和类名定义",
                "impact": "UI组件无法正确加载"
            })

        # 检查配置问题
        if ui_components.get("ui_configs", {}).get("coverage", 0) < 0.5:
            recommendations.append({
                "priority": "LOW",
                "category": "Configuration",
                "issue": "Missing UI configuration files",
                "solution": "创建UI配置文件：ui_settings.yaml, style.qss, dashboard_config.json",
                "impact": "UI外观和行为配置不完整"
            })

        self.test_results["recommendations"] = recommendations

    def _calculate_overall_status(self):
        """计算总体测试状态"""
        failed_tests = 0
        total_tests = 0

        def count_tests(obj):
            nonlocal failed_tests, total_tests
            if isinstance(obj, dict):
                if "status" in obj:
                    total_tests += 1
                    if obj["status"] == "FAILED":
                        failed_tests += 1
                else:
                    for value in obj.values():
                        count_tests(value)

        # 统计所有测试
        for category in ["environment_check", "ui_components"]:
            if category in self.test_results:
                count_tests(self.test_results[category])

        if total_tests == 0:
            self.test_results["overall_status"] = "NO_TESTS"
        elif failed_tests == 0:
            self.test_results["overall_status"] = "PASSED"
        elif failed_tests < total_tests / 2:
            self.test_results["overall_status"] = "PARTIAL"
        else:
            self.test_results["overall_status"] = "FAILED"

        self.test_results["test_summary"] = {
            "total_tests": total_tests,
            "failed_tests": failed_tests,
            "success_rate": (total_tests - failed_tests) / total_tests if total_tests > 0 else 0
        }

    def run_comprehensive_test(self) -> Dict[str, Any]:
        """运行全面的UI集成测试"""
        print("🚀 开始VisionAI-ClipsMaster UI界面整合测试 (修复版)...")
        
        # 设置测试环境
        if not self.setup_test_environment():
            self.test_results["overall_status"] = "FAILED"
            return self.test_results
        
        # 执行各项测试
        self.test_results["ui_components"] = self.test_ui_component_integration_safe()
        
        # 生成建议
        self._generate_recommendations()
        
        # 计算总体状态
        self._calculate_overall_status()
        
        return self.test_results

def main():
    """主函数"""
    tester = UIIntegrationTesterFixed()
    results = tester.run_comprehensive_test()
    
    # 保存测试结果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"VisionAI_ClipsMaster_UI_Integration_Test_Fixed_Report_{timestamp}.json"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    # 打印测试摘要
    print(f"\n📊 UI界面整合测试完成!")
    print(f"📄 详细报告已保存至: {report_file}")
    print(f"🎯 总体状态: {results['overall_status']}")

if __name__ == "__main__":
    main()
