#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 综合功能测试计划
"""

import sys
import os
import time
from pathlib import Path
from typing import Dict, List, Any

# 设置项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.append(str(PROJECT_ROOT))

class ComprehensiveTestSuite:
    """综合测试套件"""
    
    def __init__(self):
        self.test_results = {}
        self.failed_tests = []
        self.passed_tests = []
    
    def log_test(self, test_name: str, status: str, details: str = ""):
        """记录测试结果"""
        self.test_results[test_name] = {
            'status': status,
            'details': details,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        if status == 'PASS':
            self.passed_tests.append(test_name)
            print(f"✅ {test_name}: {details}")
        elif status == 'FAIL':
            self.failed_tests.append(test_name)
            print(f"❌ {test_name}: {details}")
        else:
            print(f"⚠️ {test_name}: {details}")
    
    def test_1_basic_imports(self):
        """测试1: 基础导入验证"""
        print("\n=== 测试1: 基础导入验证 ===")
        
        # 测试PyQt6
        try:
            from PyQt6.QtWidgets import QApplication, QMainWindow
            from PyQt6.QtCore import QThread, pyqtSignal
            self.log_test("PyQt6导入", "PASS", "所有PyQt6组件导入成功")
        except ImportError as e:
            self.log_test("PyQt6导入", "FAIL", f"导入失败: {e}")
        
        # 测试核心工具
        try:
            from src.utils.config_utils import load_config, load_yaml_config
            self.log_test("配置工具导入", "PASS", "配置工具导入成功")
        except ImportError as e:
            self.log_test("配置工具导入", "FAIL", f"导入失败: {e}")
        
        # 测试UI桥接
        try:
            from ui_bridge import UIBridge
            self.log_test("UI桥接导入", "PASS", "UI桥接模块导入成功")
        except ImportError as e:
            self.log_test("UI桥接导入", "FAIL", f"导入失败: {e}")
    
    def test_2_core_modules(self):
        """测试2: 核心模块验证"""
        print("\n=== 测试2: 核心模块验证 ===")
        
        core_modules = [
            ("clip_generator", "src.core.clip_generator", "ClipGenerator"),
            ("screenplay_engineer", "src.core.screenplay_engineer", "ScreenplayEngineer"),
            ("model_switcher", "src.core.model_switcher", "ModelSwitcher"),
            ("language_detector", "src.core.language_detector", "LanguageDetector"),
            ("srt_parser", "src.core.srt_parser", "parse_srt"),  # 这是函数，不是类
        ]
        
        for name, module_path, class_name in core_modules:
            try:
                module = __import__(module_path, fromlist=[class_name])
                if name == "srt_parser":
                    # 对于srt_parser，检查函数而不是类
                    getattr(module, class_name)
                    self.log_test(f"核心模块-{name}", "PASS", f"{class_name}函数导入成功")
                else:
                    getattr(module, class_name)
                    self.log_test(f"核心模块-{name}", "PASS", f"{class_name}类导入成功")
            except ImportError as e:
                self.log_test(f"核心模块-{name}", "FAIL", f"模块导入失败: {e}")
            except AttributeError as e:
                self.log_test(f"核心模块-{name}", "FAIL", f"类/函数不存在: {e}")
    
    def test_3_training_modules(self):
        """测试3: 训练模块验证"""
        print("\n=== 测试3: 训练模块验证 ===")
        
        training_modules = [
            ("trainer", "src.training.trainer", "ModelTrainer"),
            ("en_trainer", "src.training.en_trainer", "EnTrainer"),
            ("zh_trainer", "src.training.zh_trainer", "ZhTrainer"),
        ]
        
        for name, module_path, class_name in training_modules:
            try:
                module = __import__(module_path, fromlist=[class_name])
                getattr(module, class_name)
                self.log_test(f"训练模块-{name}", "PASS", f"{class_name}类导入成功")
            except ImportError as e:
                self.log_test(f"训练模块-{name}", "FAIL", f"模块导入失败: {e}")
            except AttributeError as e:
                self.log_test(f"训练模块-{name}", "FAIL", f"类不存在: {e}")
    
    def test_4_ui_creation(self):
        """测试4: UI创建验证"""
        print("\n=== 测试4: UI创建验证 ===")
        
        try:
            from PyQt6.QtWidgets import QApplication
            
            # 检查是否已有QApplication实例
            app = QApplication.instance()
            if app is None:
                app = QApplication(sys.argv)
                created_new_app = True
            else:
                created_new_app = False
            
            # 尝试导入主UI
            try:
                from simple_ui_fixed import SimpleScreenplayApp
                self.log_test("主UI类导入", "PASS", "SimpleScreenplayApp类导入成功")

                # 尝试创建UI实例
                try:
                    ui = SimpleScreenplayApp()
                    self.log_test("UI实例创建", "PASS", "UI实例创建成功")

                    # 测试UI显示（不运行事件循环）
                    ui.show()
                    self.log_test("UI显示", "PASS", "UI窗口可以显示")
                    ui.close()

                except Exception as e:
                    self.log_test("UI实例创建", "FAIL", f"UI实例创建失败: {e}")

            except ImportError as e:
                self.log_test("主UI类导入", "FAIL", f"主UI类导入失败: {e}")
            
            # 清理
            if created_new_app:
                app.quit()
                
        except Exception as e:
            self.log_test("UI框架初始化", "FAIL", f"UI框架初始化失败: {e}")
    
    def test_5_file_structure(self):
        """测试5: 文件结构验证"""
        print("\n=== 测试5: 文件结构验证 ===")
        
        required_files = [
            "simple_ui_fixed.py",
            "ui_bridge.py",
            "src/core/clip_generator.py",
            "src/utils/config_utils.py",
            "src/training/trainer.py",
        ]
        
        required_dirs = [
            "src",
            "src/core",
            "src/training",
            "src/utils",
            "configs",
            "data",
        ]
        
        # 检查文件
        for file_path in required_files:
            full_path = PROJECT_ROOT / file_path
            if full_path.exists():
                self.log_test(f"文件存在-{file_path}", "PASS", "文件存在")
            else:
                self.log_test(f"文件存在-{file_path}", "FAIL", "文件不存在")
        
        # 检查目录
        for dir_path in required_dirs:
            full_path = PROJECT_ROOT / dir_path
            if full_path.exists() and full_path.is_dir():
                self.log_test(f"目录存在-{dir_path}", "PASS", "目录存在")
            else:
                self.log_test(f"目录存在-{dir_path}", "FAIL", "目录不存在")
    
    def test_6_dependencies(self):
        """测试6: 依赖包验证"""
        print("\n=== 测试6: 依赖包验证 ===")
        
        dependencies = [
            ("PyQt6", "PyQt6"),
            ("torch", "torch"),
            ("transformers", "transformers"),
            ("opencv", "cv2"),
            ("numpy", "numpy"),
            ("plotly", "plotly"),
        ]
        
        for name, import_name in dependencies:
            try:
                __import__(import_name)
                self.log_test(f"依赖-{name}", "PASS", f"{name}已安装")
            except ImportError:
                self.log_test(f"依赖-{name}", "FAIL", f"{name}未安装")
    
    def test_7_gpu_detection(self):
        """测试7: GPU检测验证"""
        print("\n=== 测试7: GPU检测验证 ===")
        
        try:
            import torch
            if torch.cuda.is_available():
                gpu_name = torch.cuda.get_device_name(0)
                self.log_test("GPU检测", "PASS", f"检测到GPU: {gpu_name}")
            else:
                self.log_test("GPU检测", "PASS", "未检测到GPU，将使用CPU模式（符合低配要求）")
        except ImportError:
            self.log_test("GPU检测", "SKIP", "PyTorch未安装，无法检测GPU")
    
    def generate_report(self):
        """生成测试报告"""
        print("\n" + "="*60)
        print("VisionAI-ClipsMaster 综合测试报告")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_count = len(self.passed_tests)
        failed_count = len(self.failed_tests)
        
        print(f"总测试数: {total_tests}")
        print(f"通过: {passed_count}")
        print(f"失败: {failed_count}")
        print(f"成功率: {passed_count/total_tests*100:.1f}%")
        
        if self.failed_tests:
            print(f"\n失败的测试:")
            for test in self.failed_tests:
                result = self.test_results[test]
                print(f"  ❌ {test}: {result['details']}")
        
        print(f"\n详细结果:")
        for test_name, result in self.test_results.items():
            status_icon = "✅" if result['status'] == 'PASS' else "❌" if result['status'] == 'FAIL' else "⚠️"
            print(f"  {status_icon} {test_name}: {result['details']}")
        
        return passed_count == total_tests
    
    def run_all_tests(self):
        """运行所有测试"""
        print("开始VisionAI-ClipsMaster综合功能测试...")
        
        self.test_1_basic_imports()
        self.test_2_core_modules()
        self.test_3_training_modules()
        self.test_4_ui_creation()
        self.test_5_file_structure()
        self.test_6_dependencies()
        self.test_7_gpu_detection()
        
        return self.generate_report()

def main():
    """主函数"""
    test_suite = ComprehensiveTestSuite()
    success = test_suite.run_all_tests()
    
    if success:
        print("\n🎉 所有测试通过！VisionAI-ClipsMaster准备就绪。")
        return 0
    else:
        print("\n⚠️ 部分测试失败，请查看上述报告进行修复。")
        return 1

if __name__ == "__main__":
    sys.exit(main())
