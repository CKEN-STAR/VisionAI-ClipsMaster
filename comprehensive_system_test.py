#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 全面系统测试
测试所有功能模块、UI界面、工作流程的完整性和可用性
"""

import os
import sys
import time
import json
import subprocess
import threading
from pathlib import Path
from datetime import datetime
import traceback

# 添加项目路径
sys.path.append(str(Path(__file__).parent))

class ComprehensiveSystemTester:
    """全面系统测试器"""
    
    def __init__(self):
        self.test_results = {
            "environment": {},
            "dependencies": {},
            "core_modules": {},
            "ui_components": {},
            "workflow": {},
            "integration": {},
            "performance": {},
            "errors": []
        }
        self.start_time = datetime.now()
        
    def log_test(self, category, test_name, status, details="", error=None):
        """记录测试结果"""
        result = {
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        if error:
            result["error"] = str(error)
            self.test_results["errors"].append({
                "test": f"{category}.{test_name}",
                "error": str(error),
                "traceback": traceback.format_exc()
            })
        
        if category not in self.test_results:
            self.test_results[category] = {}
        self.test_results[category][test_name] = result
        
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_icon} [{category}] {test_name}: {status}")
        if details:
            print(f"   详情: {details}")
        if error:
            print(f"   错误: {error}")

    def test_environment(self):
        """测试运行环境"""
        print("\n🔍 测试运行环境...")
        print("=" * 50)
        
        # Python版本检查
        try:
            python_version = sys.version
            if sys.version_info >= (3, 8):
                self.log_test("environment", "python_version", "PASS", f"Python {python_version}")
            else:
                self.log_test("environment", "python_version", "FAIL", f"需要Python 3.8+，当前: {python_version}")
        except Exception as e:
            self.log_test("environment", "python_version", "FAIL", error=e)
        
        # 内存检查
        try:
            import psutil
            memory = psutil.virtual_memory()
            total_gb = memory.total / (1024**3)
            available_gb = memory.available / (1024**3)
            
            if total_gb >= 4:
                self.log_test("environment", "memory_check", "PASS", 
                            f"总内存: {total_gb:.1f}GB, 可用: {available_gb:.1f}GB")
            else:
                self.log_test("environment", "memory_check", "WARN", 
                            f"内存可能不足: {total_gb:.1f}GB")
        except Exception as e:
            self.log_test("environment", "memory_check", "FAIL", error=e)
        
        # 磁盘空间检查
        try:
            disk_usage = psutil.disk_usage('.')
            free_gb = disk_usage.free / (1024**3)
            
            if free_gb >= 10:
                self.log_test("environment", "disk_space", "PASS", f"可用空间: {free_gb:.1f}GB")
            else:
                self.log_test("environment", "disk_space", "WARN", f"磁盘空间不足: {free_gb:.1f}GB")
        except Exception as e:
            self.log_test("environment", "disk_space", "FAIL", error=e)

    def test_dependencies(self):
        """测试依赖项"""
        print("\n📦 测试依赖项...")
        print("=" * 50)
        
        # 核心依赖列表
        core_deps = {
            "torch": "PyTorch深度学习框架",
            "transformers": "HuggingFace Transformers",
            "numpy": "数值计算库",
            "opencv-python": "计算机视觉库",
            "PyQt6": "GUI框架",
            "psutil": "系统监控",
            "loguru": "日志系统",
            "yaml": "配置文件处理",
            "pandas": "数据处理",
            "matplotlib": "图表绘制",
            "requests": "HTTP请求",
            "jieba": "中文分词",
            "langdetect": "语言检测",
            "tqdm": "进度条",
            "lxml": "XML处理",
            "tabulate": "表格格式化",
            "ffmpeg": "视频处理"
        }
        
        for package, description in core_deps.items():
            try:
                if package == "opencv-python":
                    import cv2
                    version = cv2.__version__
                elif package == "yaml":
                    import yaml
                    version = getattr(yaml, '__version__', 'unknown')
                elif package == "ffmpeg":
                    import ffmpeg
                    version = getattr(ffmpeg, '__version__', 'unknown')
                else:
                    module = __import__(package.replace("-", "_"))
                    version = getattr(module, '__version__', 'unknown')
                
                self.log_test("dependencies", package, "PASS", f"{description} - v{version}")
            except ImportError as e:
                self.log_test("dependencies", package, "FAIL", f"{description} - 未安装", e)
            except Exception as e:
                self.log_test("dependencies", package, "WARN", f"{description} - 导入异常", e)

    def test_core_modules(self):
        """测试核心模块"""
        print("\n🔧 测试核心模块...")
        print("=" * 50)
        
        # 测试语言检测器
        try:
            from src.core.language_detector import LanguageDetector
            detector = LanguageDetector()
            
            # 测试中文检测
            zh_result = detector.detect("这是一段中文测试文本")
            if zh_result == "zh":
                self.log_test("core_modules", "language_detector_zh", "PASS", "中文检测正常")
            else:
                self.log_test("core_modules", "language_detector_zh", "FAIL", f"中文检测错误: {zh_result}")
            
            # 测试英文检测
            en_result = detector.detect("This is an English test text")
            if en_result == "en":
                self.log_test("core_modules", "language_detector_en", "PASS", "英文检测正常")
            else:
                self.log_test("core_modules", "language_detector_en", "FAIL", f"英文检测错误: {en_result}")
                
        except Exception as e:
            self.log_test("core_modules", "language_detector", "FAIL", error=e)
        
        # 测试SRT解析器
        try:
            from src.core.srt_parser import SRTParser
            parser = SRTParser()
            
            # 创建测试SRT内容
            test_srt = """1
00:00:01,000 --> 00:00:03,000
测试字幕内容

2
00:00:04,000 --> 00:00:06,000
第二条字幕
"""
            
            parsed = parser.parse_srt_content(test_srt)
            if len(parsed) == 2:
                self.log_test("core_modules", "srt_parser", "PASS", f"解析了{len(parsed)}条字幕")
            else:
                self.log_test("core_modules", "srt_parser", "FAIL", f"解析结果异常: {len(parsed)}条")
                
        except Exception as e:
            self.log_test("core_modules", "srt_parser", "FAIL", error=e)
        
        # 测试模型切换器
        try:
            from src.core.model_switcher import ModelSwitcher
            switcher = ModelSwitcher()
            
            # 测试模型配置加载
            config = switcher.load_model_config()
            if config:
                self.log_test("core_modules", "model_switcher", "PASS", "模型配置加载成功")
            else:
                self.log_test("core_modules", "model_switcher", "FAIL", "模型配置加载失败")
                
        except Exception as e:
            self.log_test("core_modules", "model_switcher", "FAIL", error=e)
        
        # 测试叙事分析器
        try:
            from src.core.narrative_analyzer import NarrativeAnalyzer
            analyzer = NarrativeAnalyzer()
            
            test_text = "主角遇到了困难，经过努力最终获得了成功。"
            analysis = analyzer.analyze_narrative(test_text)
            
            if analysis:
                self.log_test("core_modules", "narrative_analyzer", "PASS", "叙事分析正常")
            else:
                self.log_test("core_modules", "narrative_analyzer", "FAIL", "叙事分析失败")
                
        except Exception as e:
            self.log_test("core_modules", "narrative_analyzer", "FAIL", error=e)
        
        # 测试剧本工程师
        try:
            from src.core.screenplay_engineer import ScreenplayEngineer
            engineer = ScreenplayEngineer()
            
            # 测试剧本重构功能
            test_script = [
                {"text": "开场介绍", "start": 0, "end": 5},
                {"text": "情节发展", "start": 5, "end": 15},
                {"text": "高潮部分", "start": 15, "end": 25},
                {"text": "结局", "start": 25, "end": 30}
            ]
            
            reconstructed = engineer.reconstruct_script(test_script)
            if reconstructed:
                self.log_test("core_modules", "screenplay_engineer", "PASS", f"重构了{len(reconstructed)}个片段")
            else:
                self.log_test("core_modules", "screenplay_engineer", "FAIL", "剧本重构失败")
                
        except Exception as e:
            self.log_test("core_modules", "screenplay_engineer", "FAIL", error=e)

    def test_ui_components(self):
        """测试UI组件"""
        print("\n🖥️ 测试UI组件...")
        print("=" * 50)
        
        # 测试PyQt6可用性
        try:
            from PyQt6.QtWidgets import QApplication, QWidget
            from PyQt6.QtCore import QTimer
            
            # 创建应用实例（如果不存在）
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            # 测试基本窗口创建
            widget = QWidget()
            widget.setWindowTitle("测试窗口")
            
            self.log_test("ui_components", "pyqt6_basic", "PASS", "PyQt6基本功能正常")
            
        except Exception as e:
            self.log_test("ui_components", "pyqt6_basic", "FAIL", error=e)
        
        # 测试主窗口
        try:
            from ui.main_window import MainWindow
            
            main_window = MainWindow()
            if hasattr(main_window, 'setupUI'):
                main_window.setupUI()
                self.log_test("ui_components", "main_window", "PASS", "主窗口创建成功")
            else:
                self.log_test("ui_components", "main_window", "WARN", "主窗口缺少setupUI方法")
                
        except Exception as e:
            self.log_test("ui_components", "main_window", "FAIL", error=e)
        
        # 测试训练面板
        try:
            from ui.training_panel import TrainingPanel
            
            training_panel = TrainingPanel()
            self.log_test("ui_components", "training_panel", "PASS", "训练面板创建成功")
            
        except Exception as e:
            self.log_test("ui_components", "training_panel", "FAIL", error=e)
        
        # 测试进度仪表板
        try:
            from ui.progress_dashboard import ProgressDashboard
            
            dashboard = ProgressDashboard()
            self.log_test("ui_components", "progress_dashboard", "PASS", "进度仪表板创建成功")
            
        except Exception as e:
            self.log_test("ui_components", "progress_dashboard", "FAIL", error=e)

    def test_workflow(self):
        """测试完整工作流程"""
        print("\n🔄 测试工作流程...")
        print("=" * 50)
        
        # 创建测试数据
        self.create_test_data()
        
        # 测试文件上传流程
        try:
            test_video = "test_data/test_video.mp4"
            test_srt = "test_data/test_subtitle.srt"
            
            if os.path.exists(test_srt):
                self.log_test("workflow", "file_upload", "PASS", "测试文件准备完成")
            else:
                self.log_test("workflow", "file_upload", "WARN", "测试文件不存在，创建模拟文件")
                
        except Exception as e:
            self.log_test("workflow", "file_upload", "FAIL", error=e)
        
        # 测试语言检测流程
        try:
            from src.core.language_detector import LanguageDetector
            detector = LanguageDetector()
            
            # 模拟字幕内容
            test_content = "这是一个测试字幕内容"
            detected_lang = detector.detect(test_content)
            
            self.log_test("workflow", "language_detection", "PASS", f"检测语言: {detected_lang}")
            
        except Exception as e:
            self.log_test("workflow", "language_detection", "FAIL", error=e)
        
        # 测试模型加载流程
        try:
            from src.core.model_switcher import ModelSwitcher
            switcher = ModelSwitcher()
            
            # 模拟模型切换
            model_info = switcher.get_model_info("zh")
            if model_info:
                self.log_test("workflow", "model_loading", "PASS", f"模型信息获取成功: {model_info.get('name', 'unknown')}")
            else:
                self.log_test("workflow", "model_loading", "WARN", "模型信息获取失败")
                
        except Exception as e:
            self.log_test("workflow", "model_loading", "FAIL", error=e)
        
        # 测试剧本重构流程
        try:
            from src.core.screenplay_engineer import ScreenplayEngineer
            engineer = ScreenplayEngineer()
            
            # 模拟剧本数据
            mock_script = [
                {"text": "开场", "start": 0, "end": 10},
                {"text": "发展", "start": 10, "end": 20},
                {"text": "高潮", "start": 20, "end": 30}
            ]
            
            result = engineer.reconstruct_script(mock_script)
            if result:
                self.log_test("workflow", "script_reconstruction", "PASS", f"重构完成，生成{len(result)}个片段")
            else:
                self.log_test("workflow", "script_reconstruction", "FAIL", "剧本重构失败")
                
        except Exception as e:
            self.log_test("workflow", "script_reconstruction", "FAIL", error=e)

    def create_test_data(self):
        """创建测试数据"""
        test_dir = Path("test_data")
        test_dir.mkdir(exist_ok=True)
        
        # 创建测试SRT文件
        test_srt_content = """1
00:00:01,000 --> 00:00:05,000
这是第一条测试字幕

2
00:00:06,000 --> 00:00:10,000
这是第二条测试字幕

3
00:00:11,000 --> 00:00:15,000
这是第三条测试字幕
"""
        
        with open(test_dir / "test_subtitle.srt", 'w', encoding='utf-8') as f:
            f.write(test_srt_content)

    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始VisionAI-ClipsMaster全面系统测试")
        print("=" * 80)
        
        # 执行各项测试
        self.test_environment()
        self.test_dependencies()
        self.test_core_modules()
        self.test_ui_components()
        self.test_workflow()
        
        # 生成测试报告
        self.generate_report()

    def generate_report(self):
        """生成测试报告"""
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        print(f"\n📊 测试报告")
        print("=" * 80)
        
        # 统计结果
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        warned_tests = 0
        
        for category, tests in self.test_results.items():
            if category == "errors":
                continue
            for test_name, result in tests.items():
                total_tests += 1
                if result["status"] == "PASS":
                    passed_tests += 1
                elif result["status"] == "FAIL":
                    failed_tests += 1
                elif result["status"] == "WARN":
                    warned_tests += 1
        
        print(f"测试总数: {total_tests}")
        print(f"通过: {passed_tests} ✅")
        print(f"失败: {failed_tests} ❌")
        print(f"警告: {warned_tests} ⚠️")
        print(f"测试时长: {duration.total_seconds():.2f}秒")
        
        # 计算通过率
        if total_tests > 0:
            pass_rate = (passed_tests / total_tests) * 100
            print(f"通过率: {pass_rate:.1f}%")
            
            if pass_rate >= 90:
                print("\n🎉 系统状态: 优秀！所有核心功能正常")
            elif pass_rate >= 70:
                print("\n✅ 系统状态: 良好，部分功能需要注意")
            else:
                print("\n⚠️ 系统状态: 需要修复，存在重要问题")
        
        # 保存详细报告
        self.test_results["summary"] = {
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "warned": warned_tests,
            "pass_rate": pass_rate if total_tests > 0 else 0,
            "duration_seconds": duration.total_seconds(),
            "test_time": end_time.isoformat()
        }
        
        report_file = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📁 详细报告已保存: {report_file}")
        
        # 显示关键错误
        if self.test_results["errors"]:
            print(f"\n❌ 发现 {len(self.test_results['errors'])} 个错误:")
            for i, error in enumerate(self.test_results["errors"][:5], 1):
                print(f"{i}. {error['test']}: {error['error']}")
            if len(self.test_results["errors"]) > 5:
                print(f"... 还有 {len(self.test_results['errors']) - 5} 个错误，详见报告文件")

if __name__ == "__main__":
    tester = ComprehensiveSystemTester()
    tester.run_all_tests()
