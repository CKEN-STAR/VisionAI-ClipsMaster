#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster UI整合测试脚本

对simple_ui_fixed.py进行全面的UI整合测试，验证功能完整性、界面交互、核心流程集成和性能稳定性
"""

import sys
import os
import time
import json
import traceback
import threading
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

class UIIntegrationTester:
    """UI整合测试器"""
    
    def __init__(self):
        self.test_results = {
            "timestamp": datetime.now().isoformat(),
            "test_summary": {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0
            },
            "test_categories": {
                "functionality": {},
                "interaction": {},
                "integration": {},
                "performance": {}
            },
            "issues_found": [],
            "recommendations": []
        }
        
        self.app = None
        self.main_window = None
        
    def log_test_result(self, category, test_name, status, details="", error=None):
        """记录测试结果"""
        self.test_results["test_summary"]["total_tests"] += 1
        self.test_results["test_summary"][status] += 1
        
        test_result = {
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        
        if error:
            test_result["error"] = str(error)
            test_result["traceback"] = traceback.format_exc()
            
        self.test_results["test_categories"][category][test_name] = test_result
        
        print(f"[{status.upper()}] {category}.{test_name}: {details}")
        
    def test_import_dependencies(self):
        """测试1: 功能完整性 - 依赖导入测试"""
        print("\n=== 1. 功能完整性测试 ===")
        
        # 测试PyQt6导入
        try:
            from PyQt6.QtWidgets import QApplication, QMainWindow
            from PyQt6.QtCore import Qt, QThread
            from PyQt6.QtGui import QFont
            self.log_test_result("functionality", "pyqt6_import", "passed", "PyQt6核心组件导入成功")
        except ImportError as e:
            self.log_test_result("functionality", "pyqt6_import", "failed", "PyQt6导入失败", e)
            return False
            
        # 测试simple_ui_fixed导入
        try:
            import simple_ui_fixed
            self.log_test_result("functionality", "main_ui_import", "passed", "主UI模块导入成功")
        except ImportError as e:
            self.log_test_result("functionality", "main_ui_import", "failed", "主UI模块导入失败", e)
            return False
            
        # 测试核心模块导入
        core_modules = [
            ("src.core.language_detector", "语言检测器"),
            ("src.core.model_switcher", "模型切换器"),
            ("src.core.screenplay_engineer", "剧本工程师"),
            ("src.core.narrative_analyzer", "叙事分析器"),
            ("src.core.video_processor", "视频处理器")
        ]
        
        for module_name, display_name in core_modules:
            try:
                __import__(module_name)
                self.log_test_result("functionality", f"core_module_{module_name.split('.')[-1]}", 
                                   "passed", f"{display_name}导入成功")
            except ImportError as e:
                self.log_test_result("functionality", f"core_module_{module_name.split('.')[-1]}", 
                                   "failed", f"{display_name}导入失败", e)
                
        return True
        
    def test_ui_initialization(self):
        """测试2: 界面交互 - UI初始化测试"""
        print("\n=== 2. 界面交互测试 ===")
        
        try:
            from PyQt6.QtWidgets import QApplication
            
            # 创建QApplication实例
            if not QApplication.instance():
                self.app = QApplication(sys.argv)
            else:
                self.app = QApplication.instance()
                
            self.log_test_result("interaction", "qapplication_creation", "passed", "QApplication创建成功")
            
            # 测试主窗口创建
            try:
                from simple_ui_fixed import SimpleScreenplayApp
                self.main_window = SimpleScreenplayApp()
                self.log_test_result("interaction", "main_window_creation", "passed", "主窗口创建成功")
                
                # 测试窗口基本属性
                if hasattr(self.main_window, 'setWindowTitle'):
                    self.main_window.setWindowTitle("UI测试模式")
                    self.log_test_result("interaction", "window_title_setting", "passed", "窗口标题设置成功")
                    
                # 测试窗口显示
                if hasattr(self.main_window, 'show'):
                    # 不实际显示窗口，只测试方法存在
                    self.log_test_result("interaction", "window_show_method", "passed", "窗口显示方法可用")
                    
            except Exception as e:
                self.log_test_result("interaction", "main_window_creation", "failed", "主窗口创建失败", e)
                return False
                
        except Exception as e:
            self.log_test_result("interaction", "qapplication_creation", "failed", "QApplication创建失败", e)
            return False
            
        return True
        
    def test_file_upload_functionality(self):
        """测试3: 核心流程集成 - 文件上传功能测试"""
        print("\n=== 3. 核心流程集成测试 ===")

        if not self.main_window:
            self.log_test_result("integration", "file_upload_test", "skipped", "主窗口未初始化")
            return False

        # 测试UI组件存在性（基于实际的组件名称）
        ui_components = [
            ("tabs", "主标签页容器"),
            ("video_list", "视频文件列表"),
            ("srt_list", "SRT文件列表"),
            ("lang_combo", "语言选择下拉框"),
            ("use_gpu_check", "GPU使用复选框"),
            ("progress_bar", "进度条"),
            ("process_progress_bar", "处理进度条"),
            ("status_label", "状态标签")
        ]

        for component_name, display_name in ui_components:
            if hasattr(self.main_window, component_name):
                self.log_test_result("integration", f"component_{component_name}", "passed", f"{display_name}组件存在")
            else:
                self.log_test_result("integration", f"component_{component_name}", "failed", f"{display_name}组件不存在")

        # 测试核心方法存在性（基于实际的方法名称）
        core_methods = [
            ("add_video_files", "添加视频文件"),
            ("add_srt_files", "添加SRT文件"),
            ("generate_viral_srt", "生成爆款字幕"),
            ("show_gpu_detection_dialog", "显示GPU检测对话框"),
            ("start_training", "开始训练"),
            ("update_model_status", "更新模型状态"),
            ("select_video", "选择视频文件"),
            ("select_subtitle", "选择字幕文件")
        ]

        for method_name, display_name in core_methods:
            if hasattr(self.main_window, method_name):
                self.log_test_result("integration", f"method_{method_name}", "passed", f"{display_name}方法存在")
            else:
                self.log_test_result("integration", f"method_{method_name}", "failed", f"{display_name}方法不存在")

        return True
        
    def test_language_detection_integration(self):
        """测试4: 语言检测和模型切换功能"""
        
        try:
            # 测试语言检测器
            from src.core.language_detector import LanguageDetector
            detector = LanguageDetector()
            
            # 测试中文检测
            chinese_text = "这是一个中文测试文本"
            result = detector.detect_language(chinese_text)
            if result and 'zh' in result.lower():
                self.log_test_result("integration", "chinese_detection", "passed", "中文检测正常")
            else:
                self.log_test_result("integration", "chinese_detection", "failed", f"中文检测异常: {result}")
                
            # 测试英文检测
            english_text = "This is an English test text"
            result = detector.detect_language(english_text)
            if result and 'en' in result.lower():
                self.log_test_result("integration", "english_detection", "passed", "英文检测正常")
            else:
                self.log_test_result("integration", "english_detection", "failed", f"英文检测异常: {result}")
                
        except Exception as e:
            self.log_test_result("integration", "language_detection", "failed", "语言检测功能测试失败", e)
            
    def test_memory_monitoring(self):
        """测试5: 性能和稳定性 - 内存监控测试"""
        print("\n=== 4. 性能和稳定性测试 ===")
        
        try:
            import psutil
            process = psutil.Process()
            
            # 获取初始内存使用
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            self.log_test_result("performance", "initial_memory_check", "passed", 
                               f"初始内存使用: {initial_memory:.1f}MB")
            
            # 检查内存是否在合理范围内（4GB限制下应该小于800MB）
            if initial_memory < 800:
                self.log_test_result("performance", "memory_usage_check", "passed", 
                                   f"内存使用在合理范围内: {initial_memory:.1f}MB")
            else:
                self.log_test_result("performance", "memory_usage_check", "failed", 
                                   f"内存使用过高: {initial_memory:.1f}MB")
                
        except Exception as e:
            self.log_test_result("performance", "memory_monitoring", "failed", "内存监控测试失败", e)
            
    def test_training_panel_functionality(self):
        """测试6: 训练投喂面板功能"""

        if not self.main_window:
            self.log_test_result("integration", "training_panel_test", "skipped", "主窗口未初始化")
            return False

        # 等待延迟绑定完成
        import time
        time.sleep(0.2)  # 等待QTimer.singleShot(100)完成

        # 处理应用程序事件，确保延迟绑定执行
        if self.app:
            self.app.processEvents()

        # 测试训练相关组件（基于实际的组件名称）
        training_components = [
            ("training_feeder", "训练组件"),
            ("train_feeder", "训练组件别名"),
            ("original_srt_list", "原始SRT列表"),
            ("viral_srt", "爆款SRT文本框"),
            ("use_gpu_checkbox", "GPU训练复选框"),
            ("training_mode_label", "训练模式标签")
        ]

        for component_name, display_name in training_components:
            if hasattr(self.main_window, component_name):
                component = getattr(self.main_window, component_name)
                if component is not None:
                    self.log_test_result("integration", f"training_{component_name}", "passed", f"{display_name}存在")
                else:
                    self.log_test_result("integration", f"training_{component_name}", "failed", f"{display_name}为None")
            else:
                self.log_test_result("integration", f"training_{component_name}", "failed", f"{display_name}不存在")

    def test_export_functionality(self):
        """测试7: 剪映工程导出功能"""

        try:
            # 测试剪映导出器
            from src.core.jianying_exporter import JianyingExporter
            exporter = JianyingExporter()
            self.log_test_result("integration", "jianying_exporter_import", "passed", "剪映导出器导入成功")

            # 测试导出方法存在性
            export_methods = [
                ("export_jianying_project", "剪映项目导出"),
                ("export_video_segments", "视频片段导出"),
                ("export_srt_subtitles", "SRT字幕导出"),
                ("export_complete_package", "完整包导出")
            ]

            for method_name, display_name in export_methods:
                if hasattr(exporter, method_name):
                    self.log_test_result("integration", f"export_{method_name}", "passed", f"{display_name}方法存在")
                else:
                    self.log_test_result("integration", f"export_{method_name}", "failed", f"{display_name}方法不存在")

        except Exception as e:
            self.log_test_result("integration", "jianying_exporter_test", "failed", "剪映导出器测试失败", e)

    def test_error_handling(self):
        """测试8: 异常处理和恢复机制"""

        try:
            # 测试全局异常处理器
            from simple_ui_fixed import setup_global_exception_handler
            setup_global_exception_handler()
            self.log_test_result("performance", "exception_handler_setup", "passed", "全局异常处理器设置成功")

            # 测试日志处理
            from simple_ui_fixed import LogHandler
            log_handler = LogHandler("test_log")
            log_handler.log("info", "测试日志记录")
            self.log_test_result("performance", "log_handler_test", "passed", "日志处理器测试成功")

            # 测试进程稳定性监控
            from simple_ui_fixed import ProcessStabilityMonitor
            monitor = ProcessStabilityMonitor()
            self.log_test_result("performance", "stability_monitor_test", "passed", "进程稳定性监控器测试成功")

        except Exception as e:
            self.log_test_result("performance", "error_handling", "failed", "异常处理测试失败", e)
            
    def run_all_tests(self):
        """运行所有测试"""
        print("开始VisionAI-ClipsMaster UI整合测试...")
        print("=" * 60)
        
        # 执行测试序列
        test_sequence = [
            self.test_import_dependencies,
            self.test_ui_initialization,
            self.test_file_upload_functionality,
            self.test_language_detection_integration,
            self.test_training_panel_functionality,
            self.test_export_functionality,
            self.test_memory_monitoring,
            self.test_error_handling
        ]
        
        for test_func in test_sequence:
            try:
                test_func()
            except Exception as e:
                print(f"测试执行异常: {test_func.__name__}: {e}")
                traceback.print_exc()
                
        # 生成测试报告
        self.generate_test_report()
        
    def generate_test_report(self):
        """生成测试报告"""
        print("\n" + "=" * 60)
        print("UI整合测试报告")
        print("=" * 60)
        
        summary = self.test_results["test_summary"]
        print(f"总测试数: {summary['total_tests']}")
        print(f"通过: {summary['passed']}")
        print(f"失败: {summary['failed']}")
        print(f"跳过: {summary['skipped']}")
        
        success_rate = (summary['passed'] / summary['total_tests'] * 100) if summary['total_tests'] > 0 else 0
        print(f"成功率: {success_rate:.1f}%")
        
        # 保存详细报告
        report_file = f"ui_integration_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, ensure_ascii=False, indent=2)
            
        print(f"\n详细测试报告已保存到: {report_file}")
        
        # 清理资源
        if self.main_window:
            try:
                self.main_window.close()
            except:
                pass
                
        if self.app:
            try:
                self.app.quit()
            except:
                pass

def main():
    """主函数"""
    tester = UIIntegrationTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()
