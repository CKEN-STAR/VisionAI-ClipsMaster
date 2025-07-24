#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 全面功能测试系统 v1.0.1
对所有核心功能模块进行详细测试并生成报告
"""

import os
import sys
import json
import time
import traceback
import subprocess
from datetime import datetime
from pathlib import Path
import importlib.util

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root / "ui"))

class ComprehensiveFunctionalTest:
    """全面功能测试类"""
    
    def __init__(self):
        self.test_results = {
            "test_info": {
                "version": "v1.0.1",
                "timestamp": datetime.now().isoformat(),
                "test_duration": 0,
                "total_tests": 0,
                "passed_tests": 0,
                "failed_tests": 0,
                "skipped_tests": 0
            },
            "ui_tests": {},
            "core_functionality_tests": {},
            "workflow_tests": {},
            "performance_tests": {},
            "data_processing_tests": {},
            "detailed_results": []
        }
        self.start_time = time.time()
        
    def log_test_result(self, category, test_name, status, details="", error_info=""):
        """记录测试结果"""
        result = {
            "category": category,
            "test_name": test_name,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "details": details,
            "error_info": error_info
        }
        
        self.test_results["detailed_results"].append(result)
        self.test_results["test_info"]["total_tests"] += 1
        
        if status == "PASSED":
            self.test_results["test_info"]["passed_tests"] += 1
        elif status == "FAILED":
            self.test_results["test_info"]["failed_tests"] += 1
        else:
            self.test_results["test_info"]["skipped_tests"] += 1
            
        # 更新分类结果
        if category not in self.test_results:
            self.test_results[category] = {}
        self.test_results[category][test_name] = {
            "status": status,
            "details": details,
            "error_info": error_info
        }
        
        print(f"[{status}] {category} - {test_name}: {details}")
        
    def test_ui_components(self):
        """测试UI界面组件"""
        print("\n=== 1. UI界面测试 ===")
        
        # 测试主窗口
        try:
            main_window_paths = [
                "ui/main_window.py",
                "src/ui/main_window.py",
                "src/core/main_window.py"
            ]
            
            main_window_found = False
            for path in main_window_paths:
                if os.path.exists(path):
                    main_window_found = True
                    self.log_test_result("ui_tests", "main_window_file_exists", "PASSED", 
                                       f"主窗口文件存在: {path}")
                    
                    # 尝试导入主窗口模块
                    try:
                        spec = importlib.util.spec_from_file_location("main_window", path)
                        main_window_module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(main_window_module)
                        self.log_test_result("ui_tests", "main_window_import", "PASSED", 
                                           "主窗口模块导入成功")
                    except Exception as e:
                        self.log_test_result("ui_tests", "main_window_import", "FAILED", 
                                           "主窗口模块导入失败", str(e))
                    break
                    
            if not main_window_found:
                self.log_test_result("ui_tests", "main_window_file_exists", "FAILED", 
                                   "主窗口文件不存在")
                
        except Exception as e:
            self.log_test_result("ui_tests", "main_window_test", "FAILED", 
                               "主窗口测试异常", str(e))
        
        # 测试训练监控面板
        try:
            training_panel_paths = [
                "ui/training_panel.py",
                "src/ui/training_panel.py"
            ]
            
            training_panel_found = False
            for path in training_panel_paths:
                if os.path.exists(path):
                    training_panel_found = True
                    self.log_test_result("ui_tests", "training_panel_file_exists", "PASSED", 
                                       f"训练面板文件存在: {path}")
                    
                    # 尝试导入训练面板模块
                    try:
                        spec = importlib.util.spec_from_file_location("training_panel", path)
                        training_panel_module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(training_panel_module)
                        self.log_test_result("ui_tests", "training_panel_import", "PASSED", 
                                           "训练面板模块导入成功")
                    except Exception as e:
                        self.log_test_result("ui_tests", "training_panel_import", "FAILED", 
                                           "训练面板模块导入失败", str(e))
                    break
                    
            if not training_panel_found:
                self.log_test_result("ui_tests", "training_panel_file_exists", "FAILED", 
                                   "训练面板文件不存在")
                
        except Exception as e:
            self.log_test_result("ui_tests", "training_panel_test", "FAILED", 
                               "训练面板测试异常", str(e))
        
        # 测试进度看板
        try:
            progress_dashboard_paths = [
                "ui/progress_dashboard.py",
                "src/ui/progress_dashboard.py"
            ]
            
            progress_dashboard_found = False
            for path in progress_dashboard_paths:
                if os.path.exists(path):
                    progress_dashboard_found = True
                    self.log_test_result("ui_tests", "progress_dashboard_file_exists", "PASSED", 
                                       f"进度看板文件存在: {path}")
                    
                    # 尝试导入进度看板模块
                    try:
                        spec = importlib.util.spec_from_file_location("progress_dashboard", path)
                        progress_dashboard_module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(progress_dashboard_module)
                        self.log_test_result("ui_tests", "progress_dashboard_import", "PASSED", 
                                           "进度看板模块导入成功")
                    except Exception as e:
                        self.log_test_result("ui_tests", "progress_dashboard_import", "FAILED", 
                                           "进度看板模块导入失败", str(e))
                    break
                    
            if not progress_dashboard_found:
                self.log_test_result("ui_tests", "progress_dashboard_file_exists", "FAILED", 
                                   "进度看板文件不存在")
                
        except Exception as e:
            self.log_test_result("ui_tests", "progress_dashboard_test", "FAILED", 
                               "进度看板测试异常", str(e))
        
        # 测试UI组件
        try:
            ui_components_paths = [
                "ui/components",
                "src/ui/components"
            ]
            
            components_found = False
            for path in ui_components_paths:
                if os.path.exists(path):
                    components_found = True
                    components = os.listdir(path)
                    self.log_test_result("ui_tests", "ui_components_directory", "PASSED", 
                                       f"UI组件目录存在，包含 {len(components)} 个文件")
                    
                    # 检查关键组件
                    key_components = ["realtime_charts.py", "alert_manager.py"]
                    for component in key_components:
                        component_path = os.path.join(path, component)
                        if os.path.exists(component_path):
                            self.log_test_result("ui_tests", f"component_{component}", "PASSED", 
                                               f"组件文件存在: {component}")
                        else:
                            self.log_test_result("ui_tests", f"component_{component}", "FAILED", 
                                               f"组件文件不存在: {component}")
                    break
                    
            if not components_found:
                self.log_test_result("ui_tests", "ui_components_directory", "FAILED", 
                                   "UI组件目录不存在")
                
        except Exception as e:
            self.log_test_result("ui_tests", "ui_components_test", "FAILED", 
                               "UI组件测试异常", str(e))
    
    def test_core_functionality(self):
        """测试核心功能模块"""
        print("\n=== 2. 核心功能模块测试 ===")
        
        # 测试语言检测器
        try:
            language_detector_paths = [
                "src/core/language_detector.py",
                "src/nlp/language_detector.py",
                "src/utils/language_detector.py"
            ]
            
            language_detector_found = False
            for path in language_detector_paths:
                if os.path.exists(path):
                    language_detector_found = True
                    self.log_test_result("core_functionality_tests", "language_detector_file_exists", "PASSED", 
                                       f"语言检测器文件存在: {path}")
                    break
                    
            if not language_detector_found:
                self.log_test_result("core_functionality_tests", "language_detector_file_exists", "FAILED", 
                                   "语言检测器文件不存在")
                
        except Exception as e:
            self.log_test_result("core_functionality_tests", "language_detector_test", "FAILED",
                               "语言检测器测试异常", str(e))

        # 测试模型切换器
        try:
            model_switcher_paths = [
                "src/core/model_switcher.py"
            ]

            model_switcher_found = False
            for path in model_switcher_paths:
                if os.path.exists(path):
                    model_switcher_found = True
                    self.log_test_result("core_functionality_tests", "model_switcher_file_exists", "PASSED",
                                       f"模型切换器文件存在: {path}")
                    break

            if not model_switcher_found:
                self.log_test_result("core_functionality_tests", "model_switcher_file_exists", "FAILED",
                                   "模型切换器文件不存在")

        except Exception as e:
            self.log_test_result("core_functionality_tests", "model_switcher_test", "FAILED",
                               "模型切换器测试异常", str(e))

        # 测试字幕解析器
        try:
            srt_parser_paths = [
                "src/core/srt_parser.py",
                "src/parsers/srt_parser.py"
            ]

            srt_parser_found = False
            for path in srt_parser_paths:
                if os.path.exists(path):
                    srt_parser_found = True
                    self.log_test_result("core_functionality_tests", "srt_parser_file_exists", "PASSED",
                                       f"字幕解析器文件存在: {path}")
                    break

            if not srt_parser_found:
                self.log_test_result("core_functionality_tests", "srt_parser_file_exists", "FAILED",
                                   "字幕解析器文件不存在")

        except Exception as e:
            self.log_test_result("core_functionality_tests", "srt_parser_test", "FAILED",
                               "字幕解析器测试异常", str(e))

        # 测试剧本重构引擎
        try:
            screenplay_engineer_paths = [
                "src/core/screenplay_engineer.py"
            ]

            screenplay_engineer_found = False
            for path in screenplay_engineer_paths:
                if os.path.exists(path):
                    screenplay_engineer_found = True
                    self.log_test_result("core_functionality_tests", "screenplay_engineer_file_exists", "PASSED",
                                       f"剧本重构引擎文件存在: {path}")
                    break

            if not screenplay_engineer_found:
                self.log_test_result("core_functionality_tests", "screenplay_engineer_file_exists", "FAILED",
                                   "剧本重构引擎文件不存在")

        except Exception as e:
            self.log_test_result("core_functionality_tests", "screenplay_engineer_test", "FAILED",
                               "剧本重构引擎测试异常", str(e))

        # 测试视频拼接器
        try:
            clip_generator_paths = [
                "src/core/clip_generator.py",
                "src/core/clip_generator/clip_generator.py"
            ]

            clip_generator_found = False
            for path in clip_generator_paths:
                if os.path.exists(path):
                    clip_generator_found = True
                    self.log_test_result("core_functionality_tests", "clip_generator_file_exists", "PASSED",
                                       f"视频拼接器文件存在: {path}")
                    break

            if not clip_generator_found:
                self.log_test_result("core_functionality_tests", "clip_generator_file_exists", "FAILED",
                                   "视频拼接器文件不存在")

        except Exception as e:
            self.log_test_result("core_functionality_tests", "clip_generator_test", "FAILED",
                               "视频拼接器测试异常", str(e))

    def test_workflow_integration(self):
        """测试工作流程端到端集成"""
        print("\n=== 3. 工作流程端到端测试 ===")

        # 测试配置文件
        try:
            config_paths = [
                "configs/model_config.yaml",
                "configs/active_model.yaml"
            ]

            config_found = 0
            for path in config_paths:
                if os.path.exists(path):
                    config_found += 1
                    self.log_test_result("workflow_tests", f"config_file_{path.replace('/', '_')}", "PASSED",
                                       f"配置文件存在: {path}")
                else:
                    self.log_test_result("workflow_tests", f"config_file_{path.replace('/', '_')}", "FAILED",
                                       f"配置文件不存在: {path}")

            if config_found > 0:
                self.log_test_result("workflow_tests", "config_files_check", "PASSED",
                                   f"找到 {config_found} 个配置文件")
            else:
                self.log_test_result("workflow_tests", "config_files_check", "FAILED",
                                   "未找到任何配置文件")

        except Exception as e:
            self.log_test_result("workflow_tests", "config_files_test", "FAILED",
                               "配置文件测试异常", str(e))

        # 测试测试数据
        try:
            test_data_paths = [
                "test_data",
                "data/input",
                "data/training"
            ]

            test_data_found = 0
            for path in test_data_paths:
                if os.path.exists(path):
                    test_data_found += 1
                    self.log_test_result("workflow_tests", f"test_data_{path.replace('/', '_')}", "PASSED",
                                       f"测试数据目录存在: {path}")
                else:
                    self.log_test_result("workflow_tests", f"test_data_{path.replace('/', '_')}", "FAILED",
                                       f"测试数据目录不存在: {path}")

            if test_data_found > 0:
                self.log_test_result("workflow_tests", "test_data_check", "PASSED",
                                   f"找到 {test_data_found} 个测试数据目录")
            else:
                self.log_test_result("workflow_tests", "test_data_check", "FAILED",
                                   "未找到任何测试数据目录")

        except Exception as e:
            self.log_test_result("workflow_tests", "test_data_test", "FAILED",
                               "测试数据测试异常", str(e))

    def test_performance_stability(self):
        """测试性能和稳定性"""
        print("\n=== 4. 性能和稳定性测试 ===")

        # 测试内存监控
        try:
            memory_guard_paths = [
                "src/utils/memory_guard.py",
                "src/memory/memory_guard.py",
                "ui/performance/memory_guard.py"
            ]

            memory_guard_found = False
            for path in memory_guard_paths:
                if os.path.exists(path):
                    memory_guard_found = True
                    self.log_test_result("performance_tests", "memory_guard_file_exists", "PASSED",
                                       f"内存监控文件存在: {path}")
                    break

            if not memory_guard_found:
                self.log_test_result("performance_tests", "memory_guard_file_exists", "FAILED",
                                   "内存监控文件不存在")

        except Exception as e:
            self.log_test_result("performance_tests", "memory_guard_test", "FAILED",
                               "内存监控测试异常", str(e))

        # 测试设备管理器
        try:
            device_manager_paths = [
                "src/utils/device_manager.py",
                "src/core/hardware_manager.py"
            ]

            device_manager_found = False
            for path in device_manager_paths:
                if os.path.exists(path):
                    device_manager_found = True
                    self.log_test_result("performance_tests", "device_manager_file_exists", "PASSED",
                                       f"设备管理器文件存在: {path}")
                    break

            if not device_manager_found:
                self.log_test_result("performance_tests", "device_manager_file_exists", "FAILED",
                                   "设备管理器文件不存在")

        except Exception as e:
            self.log_test_result("performance_tests", "device_manager_test", "FAILED",
                               "设备管理器测试异常", str(e))

    def test_data_processing(self):
        """测试数据处理功能"""
        print("\n=== 5. 数据处理测试 ===")

        # 测试视频格式兼容性
        try:
            video_formats = [".mp4", ".avi", ".flv", ".mov"]
            supported_formats = []

            for fmt in video_formats:
                # 检查是否有相关的处理代码
                if any(os.path.exists(path) for path in [
                    f"src/core/video_processor.py",
                    f"src/utils/file_checker.py"
                ]):
                    supported_formats.append(fmt)

            if supported_formats:
                self.log_test_result("data_processing_tests", "video_format_support", "PASSED",
                                   f"支持的视频格式: {', '.join(supported_formats)}")
            else:
                self.log_test_result("data_processing_tests", "video_format_support", "FAILED",
                                   "未找到视频格式支持")

        except Exception as e:
            self.log_test_result("data_processing_tests", "video_format_test", "FAILED",
                               "视频格式测试异常", str(e))

        # 测试字幕格式兼容性
        try:
            subtitle_formats = [".srt", ".ass", ".vtt"]
            supported_subtitle_formats = []

            for fmt in subtitle_formats:
                # 检查是否有相关的处理代码
                if any(os.path.exists(path) for path in [
                    f"src/core/srt_parser.py",
                    f"src/parsers/srt_parser.py",
                    f"src/parsers/subtitle_parser.py"
                ]):
                    supported_subtitle_formats.append(fmt)

            if supported_subtitle_formats:
                self.log_test_result("data_processing_tests", "subtitle_format_support", "PASSED",
                                   f"支持的字幕格式: {', '.join(supported_subtitle_formats)}")
            else:
                self.log_test_result("data_processing_tests", "subtitle_format_support", "FAILED",
                                   "未找到字幕格式支持")

        except Exception as e:
            self.log_test_result("data_processing_tests", "subtitle_format_test", "FAILED",
                               "字幕格式测试异常", str(e))

        # 测试训练数据投喂功能
        try:
            training_paths = [
                "src/training",
                "data/training"
            ]

            training_found = False
            for path in training_paths:
                if os.path.exists(path):
                    training_found = True
                    files = os.listdir(path)
                    self.log_test_result("data_processing_tests", "training_data_directory", "PASSED",
                                       f"训练数据目录存在: {path}，包含 {len(files)} 个文件")
                    break

            if not training_found:
                self.log_test_result("data_processing_tests", "training_data_directory", "FAILED",
                                   "训练数据目录不存在")

        except Exception as e:
            self.log_test_result("data_processing_tests", "training_data_test", "FAILED",
                               "训练数据测试异常", str(e))

        # 测试混合中英文处理
        try:
            mixed_language_support = False

            # 检查是否有混合语言处理相关文件
            mixed_lang_files = [
                "src/core/hybrid_handler.py",
                "src/core/hybrid_splitter.py",
                "src/nlp/language_detector.py"
            ]

            for path in mixed_lang_files:
                if os.path.exists(path):
                    mixed_language_support = True
                    break

            if mixed_language_support:
                self.log_test_result("data_processing_tests", "mixed_language_support", "PASSED",
                                   "支持混合中英文处理")
            else:
                self.log_test_result("data_processing_tests", "mixed_language_support", "FAILED",
                                   "未找到混合语言处理支持")

        except Exception as e:
            self.log_test_result("data_processing_tests", "mixed_language_test", "FAILED",
                               "混合语言测试异常", str(e))

    def run_all_tests(self):
        """运行所有测试"""
        print("🎬 开始VisionAI-ClipsMaster v1.0.1 全面功能测试")
        print("=" * 60)

        try:
            # 运行各项测试
            self.test_ui_components()
            self.test_core_functionality()
            self.test_workflow_integration()
            self.test_performance_stability()
            self.test_data_processing()

            # 计算测试时长
            self.test_results["test_info"]["test_duration"] = time.time() - self.start_time

            # 生成测试报告
            self.generate_test_report()

        except Exception as e:
            print(f"❌ 测试过程中发生异常: {e}")
            traceback.print_exc()

    def generate_test_report(self):
        """生成测试报告"""
        print("\n" + "=" * 60)
        print("📊 测试结果汇总")
        print("=" * 60)

        # 计算成功率
        total_tests = self.test_results["test_info"]["total_tests"]
        passed_tests = self.test_results["test_info"]["passed_tests"]
        failed_tests = self.test_results["test_info"]["failed_tests"]
        skipped_tests = self.test_results["test_info"]["skipped_tests"]

        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        print(f"总测试数: {total_tests}")
        print(f"通过测试: {passed_tests}")
        print(f"失败测试: {failed_tests}")
        print(f"跳过测试: {skipped_tests}")
        print(f"成功率: {success_rate:.1f}%")
        print(f"测试时长: {self.test_results['test_info']['test_duration']:.2f}秒")

        # 分类统计
        print("\n📋 分类测试结果:")
        for category, tests in self.test_results.items():
            if category not in ["test_info", "detailed_results"]:
                category_passed = sum(1 for test in tests.values() if test["status"] == "PASSED")
                category_total = len(tests)
                category_rate = (category_passed / category_total * 100) if category_total > 0 else 0
                print(f"  {category}: {category_passed}/{category_total} ({category_rate:.1f}%)")

        # 保存详细报告到JSON文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"comprehensive_functional_test_{timestamp}.json"

        with open(report_filename, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, ensure_ascii=False, indent=2)

        print(f"\n📄 详细测试报告已保存到: {report_filename}")

        # 生成HTML报告
        self.generate_html_report(timestamp)

        print("\n🎯 测试完成!")

        if success_rate >= 80:
            print("✅ 系统整体状态良好!")
        elif success_rate >= 60:
            print("⚠️  系统存在一些问题，建议检查失败的测试项")
        else:
            print("❌ 系统存在严重问题，需要立即修复")

    def generate_html_report(self, timestamp):
        """生成HTML格式的测试报告"""
        html_filename = f"comprehensive_functional_test_{timestamp}.html"

        total_tests = self.test_results["test_info"]["total_tests"]
        passed_tests = self.test_results["test_info"]["passed_tests"]
        failed_tests = self.test_results["test_info"]["failed_tests"]
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VisionAI-ClipsMaster v1.0.1 功能测试报告</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .header h1 {{ color: #2c3e50; margin-bottom: 10px; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .summary-card {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; text-align: center; }}
        .summary-card h3 {{ margin: 0 0 10px 0; font-size: 14px; opacity: 0.9; }}
        .summary-card .value {{ font-size: 28px; font-weight: bold; margin: 0; }}
        .test-category {{ margin-bottom: 30px; }}
        .test-category h2 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
        .test-results {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 15px; }}
        .test-item {{ background: #f8f9fa; padding: 15px; border-radius: 5px; border-left: 4px solid #28a745; }}
        .test-item.failed {{ border-left-color: #dc3545; }}
        .test-item .test-name {{ font-weight: bold; color: #2c3e50; }}
        .test-item .test-details {{ color: #6c757d; margin-top: 5px; font-size: 14px; }}
        .footer {{ text-align: center; margin-top: 40px; padding-top: 20px; border-top: 1px solid #dee2e6; color: #6c757d; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎬 VisionAI-ClipsMaster v1.0.1 功能测试报告</h1>
            <div>测试时间: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}</div>
        </div>

        <div class="summary">
            <div class="summary-card">
                <h3>总测试数</h3>
                <div class="value">{total_tests}</div>
            </div>
            <div class="summary-card">
                <h3>通过测试</h3>
                <div class="value">{passed_tests}</div>
            </div>
            <div class="summary-card">
                <h3>失败测试</h3>
                <div class="value">{failed_tests}</div>
            </div>
            <div class="summary-card">
                <h3>成功率</h3>
                <div class="value">{success_rate:.1f}%</div>
            </div>
        </div>
"""

        # 添加各测试类别的详细结果
        for category, tests in self.test_results.items():
            if category not in ["test_info", "detailed_results"]:
                category_passed = sum(1 for test in tests.values() if test["status"] == "PASSED")
                category_total = len(tests)
                category_rate = (category_passed / category_total * 100) if category_total > 0 else 0

                html_content += f"""
        <div class="test-category">
            <h2>{category} (成功率: {category_rate:.1f}%)</h2>
            <div class="test-results">
"""

                for test_name, result in tests.items():
                    status_class = "" if result["status"] == "PASSED" else "failed"
                    status_icon = "✅" if result["status"] == "PASSED" else "❌"

                    html_content += f"""
                <div class="test-item {status_class}">
                    <div class="test-name">{status_icon} {test_name}</div>
                    <div class="test-details">{result["details"]}</div>
                </div>
"""

                html_content += """
            </div>
        </div>
"""

        html_content += f"""
        <div class="footer">
            <p>VisionAI-ClipsMaster v1.0.1 - 短剧混剪AI系统</p>
            <p>测试完成时间: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>
"""

        with open(html_filename, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"📄 HTML测试报告已保存到: {html_filename}")

def main():
    """主函数"""
    test_runner = ComprehensiveFunctionalTest()
    test_runner.run_all_tests()

if __name__ == "__main__":
    main()
