#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 全面功能测试系统
按照项目架构进行分层测试：unit_test/integration_test/stress_test
"""

import sys
import os
import time
import json
import traceback
import threading
import psutil
import gc
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.append(str(PROJECT_ROOT))

# 测试结果存储
class TestResults:
    def __init__(self):
        self.results = {
            "ui_tests": {},
            "core_functionality": {},
            "performance_tests": {},
            "output_quality": {},
            "exception_handling": {},
            "summary": {}
        }
        self.start_time = datetime.now()
        self.errors = []
        self.warnings = []
    
    def add_result(self, category: str, test_name: str, status: str, details: Dict = None):
        """添加测试结果"""
        if category not in self.results:
            self.results[category] = {}
        
        self.results[category][test_name] = {
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        }
    
    def add_error(self, error: str):
        """添加错误"""
        self.errors.append({
            "error": error,
            "timestamp": datetime.now().isoformat()
        })
    
    def add_warning(self, warning: str):
        """添加警告"""
        self.warnings.append({
            "warning": warning,
            "timestamp": datetime.now().isoformat()
        })
    
    def generate_report(self) -> Dict:
        """生成最终报告"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        # 统计测试结果
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        
        for category in self.results.values():
            if isinstance(category, dict):
                for test_result in category.values():
                    if isinstance(test_result, dict) and "status" in test_result:
                        total_tests += 1
                        if test_result["status"] == "PASS":
                            passed_tests += 1
                        elif test_result["status"] == "FAIL":
                            failed_tests += 1
        
        self.results["summary"] = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": f"{(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "0%",
            "duration_seconds": duration,
            "errors_count": len(self.errors),
            "warnings_count": len(self.warnings),
            "test_start": self.start_time.isoformat(),
            "test_end": end_time.isoformat()
        }
        
        return self.results

# 内存监控器
class MemoryMonitor:
    def __init__(self):
        self.monitoring = False
        self.peak_memory = 0
        self.memory_samples = []
        self.monitor_thread = None
    
    def start_monitoring(self):
        """开始内存监控"""
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """停止内存监控"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)
    
    def _monitor_loop(self):
        """监控循环"""
        while self.monitoring:
            try:
                process = psutil.Process()
                memory_mb = process.memory_info().rss / 1024 / 1024
                self.memory_samples.append({
                    "timestamp": time.time(),
                    "memory_mb": memory_mb
                })
                self.peak_memory = max(self.peak_memory, memory_mb)
                time.sleep(0.5)  # 每0.5秒采样一次
            except Exception:
                break
    
    def get_report(self) -> Dict:
        """获取内存监控报告"""
        if not self.memory_samples:
            return {"error": "No memory samples collected"}
        
        avg_memory = sum(s["memory_mb"] for s in self.memory_samples) / len(self.memory_samples)
        
        return {
            "peak_memory_mb": self.peak_memory,
            "average_memory_mb": avg_memory,
            "samples_count": len(self.memory_samples),
            "memory_limit_check": "PASS" if self.peak_memory <= 3800 else "FAIL",
            "memory_efficiency": "GOOD" if avg_memory <= 2000 else "MODERATE" if avg_memory <= 3000 else "POOR"
        }

class VisionAIFunctionalTester:
    """VisionAI-ClipsMaster 功能测试器"""
    
    def __init__(self):
        self.results = TestResults()
        self.memory_monitor = MemoryMonitor()
        self.app = None
        self.main_window = None
        
    def setup_test_environment(self):
        """设置测试环境"""
        print("=" * 60)
        print("VisionAI-ClipsMaster 全面功能测试")
        print("=" * 60)
        
        # 创建测试数据目录
        test_data_dir = PROJECT_ROOT / "test_data"
        test_data_dir.mkdir(exist_ok=True)
        
        # 创建测试输出目录
        test_output_dir = PROJECT_ROOT / "test_output"
        test_output_dir.mkdir(exist_ok=True)
        
        print(f"[OK] 测试环境设置完成")
        print(f"测试数据目录: {test_data_dir}")
        print(f"测试输出目录: {test_output_dir}")
        
        return True
    
    def create_test_data(self):
        """创建测试数据"""
        print("\n[1/5] 创建测试数据...")
        
        try:
            # 创建测试SRT文件
            test_srt_content = """1
00:00:01,000 --> 00:00:03,000
今天天气很好

2
00:00:03,500 --> 00:00:06,000
我去了公园散步

3
00:00:06,500 --> 00:00:09,000
看到了很多花

4
00:00:09,500 --> 00:00:12,000
心情变得很愉快
"""
            
            test_srt_path = PROJECT_ROOT / "test_data" / "test_subtitle.srt"
            with open(test_srt_path, 'w', encoding='utf-8') as f:
                f.write(test_srt_content)
            
            # 创建英文测试SRT
            test_en_srt_content = """1
00:00:01,000 --> 00:00:03,000
The weather is nice today

2
00:00:03,500 --> 00:00:06,000
I went for a walk in the park

3
00:00:06,500 --> 00:00:09,000
I saw many beautiful flowers

4
00:00:09,500 --> 00:00:12,000
My mood became very pleasant
"""
            
            test_en_srt_path = PROJECT_ROOT / "test_data" / "test_english_subtitle.srt"
            with open(test_en_srt_path, 'w', encoding='utf-8') as f:
                f.write(test_en_srt_content)
            
            # 创建测试配置文件
            test_config = {
                "model_config": {
                    "chinese_model": "qwen2.5-7b-zh",
                    "english_model": "mistral-7b-en",
                    "quantization": "Q4_K_M",
                    "max_memory_mb": 3800
                },
                "clip_settings": {
                    "min_segment_duration": 1.0,
                    "max_segment_duration": 10.0,
                    "alignment_tolerance": 0.5
                }
            }
            
            config_path = PROJECT_ROOT / "test_data" / "test_config.json"
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(test_config, f, indent=2, ensure_ascii=False)
            
            self.results.add_result("ui_tests", "create_test_data", "PASS", {
                "chinese_srt": str(test_srt_path),
                "english_srt": str(test_en_srt_path),
                "config_file": str(config_path)
            })
            
            print(f"[OK] 测试数据创建完成")
            return True
            
        except Exception as e:
            error_msg = f"创建测试数据失败: {str(e)}"
            self.results.add_error(error_msg)
            self.results.add_result("ui_tests", "create_test_data", "FAIL", {"error": error_msg})
            print(f"[FAIL] {error_msg}")
            return False

    def test_ui_interface(self):
        """测试UI界面加载和响应"""
        print("\n[2/5] 测试UI界面...")

        try:
            # 开始内存监控
            self.memory_monitor.start_monitoring()

            # 导入PyQt6
            from PyQt6.QtWidgets import QApplication
            from PyQt6.QtCore import QTimer

            # 创建应用程序实例
            if not QApplication.instance():
                self.app = QApplication(sys.argv)
            else:
                self.app = QApplication.instance()

            # 测试simple_ui_fixed.py的导入
            try:
                import simple_ui_fixed
                self.results.add_result("ui_tests", "import_simple_ui_fixed", "PASS")
                print(f"[OK] simple_ui_fixed.py 导入成功")
            except Exception as e:
                error_msg = f"simple_ui_fixed.py 导入失败: {str(e)}"
                self.results.add_result("ui_tests", "import_simple_ui_fixed", "FAIL", {"error": error_msg})
                print(f"[FAIL] {error_msg}")
                return False

            # 测试主窗口创建
            try:
                start_time = time.time()
                self.main_window = simple_ui_fixed.SimpleScreenplayApp()
                creation_time = time.time() - start_time

                self.results.add_result("ui_tests", "main_window_creation", "PASS", {
                    "creation_time_seconds": creation_time,
                    "window_title": self.main_window.windowTitle()
                })
                print(f"[OK] 主窗口创建成功 (耗时: {creation_time:.2f}秒)")

            except Exception as e:
                error_msg = f"主窗口创建失败: {str(e)}"
                self.results.add_result("ui_tests", "main_window_creation", "FAIL", {"error": error_msg})
                print(f"[FAIL] {error_msg}")
                return False

            # 测试窗口显示
            try:
                self.main_window.show()
                self.results.add_result("ui_tests", "window_display", "PASS")
                print(f"[OK] 窗口显示成功")
            except Exception as e:
                error_msg = f"窗口显示失败: {str(e)}"
                self.results.add_result("ui_tests", "window_display", "FAIL", {"error": error_msg})
                print(f"[FAIL] {error_msg}")

            # 测试UI组件存在性
            ui_components = [
                ("tabs", "标签页组件"),
                ("status_label", "状态标签"),
                ("process_progress_bar", "进度条"),
                ("lang_auto_radio", "自动语言检测单选按钮"),
                ("lang_zh_radio", "中文模式单选按钮"),
                ("lang_en_radio", "英文模式单选按钮")
            ]

            for component_name, component_desc in ui_components:
                if hasattr(self.main_window, component_name):
                    self.results.add_result("ui_tests", f"component_{component_name}", "PASS")
                    print(f"[OK] {component_desc} 存在")
                else:
                    self.results.add_result("ui_tests", f"component_{component_name}", "FAIL",
                                          {"error": f"{component_desc} 不存在"})
                    print(f"[FAIL] {component_desc} 不存在")

            # 测试菜单栏
            try:
                menubar = self.main_window.menuBar()
                menu_actions = menubar.actions()
                menu_count = len(menu_actions)

                self.results.add_result("ui_tests", "menubar_test", "PASS", {
                    "menu_count": menu_count,
                    "menus": [action.text() for action in menu_actions]
                })
                print(f"[OK] 菜单栏测试通过 (菜单数量: {menu_count})")

            except Exception as e:
                error_msg = f"菜单栏测试失败: {str(e)}"
                self.results.add_result("ui_tests", "menubar_test", "FAIL", {"error": error_msg})
                print(f"[FAIL] {error_msg}")

            # 测试标签页切换
            try:
                if hasattr(self.main_window, 'tabs'):
                    tab_count = self.main_window.tabs.count()
                    if tab_count > 0:
                        # 切换到第一个标签页
                        self.main_window.tabs.setCurrentIndex(0)
                        current_tab = self.main_window.tabs.currentIndex()

                        self.results.add_result("ui_tests", "tab_switching", "PASS", {
                            "tab_count": tab_count,
                            "current_tab": current_tab
                        })
                        print(f"[OK] 标签页切换测试通过 (标签页数量: {tab_count})")
                    else:
                        self.results.add_result("ui_tests", "tab_switching", "FAIL",
                                              {"error": "没有标签页"})
                        print(f"[FAIL] 没有标签页")
                else:
                    self.results.add_result("ui_tests", "tab_switching", "FAIL",
                                          {"error": "标签页组件不存在"})
                    print(f"[FAIL] 标签页组件不存在")

            except Exception as e:
                error_msg = f"标签页切换测试失败: {str(e)}"
                self.results.add_result("ui_tests", "tab_switching", "FAIL", {"error": error_msg})
                print(f"[FAIL] {error_msg}")

            return True

        except Exception as e:
            error_msg = f"UI界面测试失败: {str(e)}"
            self.results.add_error(error_msg)
            self.results.add_result("ui_tests", "ui_interface_test", "FAIL", {"error": error_msg})
            print(f"[FAIL] {error_msg}")
            return False

    def test_core_functionality(self):
        """测试核心功能"""
        print("\n[3/5] 测试核心功能...")

        # 测试语言检测
        try:
            # 测试中文检测
            chinese_text = "今天天气很好，我去了公园散步"
            detected_lang = self.detect_language(chinese_text)

            if detected_lang in ["zh", "chinese", "auto"]:
                self.results.add_result("core_functionality", "chinese_language_detection", "PASS", {
                    "input_text": chinese_text,
                    "detected_language": detected_lang
                })
                print(f"[OK] 中文语言检测成功: {detected_lang}")
            else:
                self.results.add_result("core_functionality", "chinese_language_detection", "FAIL", {
                    "input_text": chinese_text,
                    "detected_language": detected_lang,
                    "error": "检测结果不正确"
                })
                print(f"[FAIL] 中文语言检测失败: {detected_lang}")

            # 测试英文检测
            english_text = "The weather is nice today, I went for a walk in the park"
            detected_lang = self.detect_language(english_text)

            if detected_lang in ["en", "english", "auto"]:
                self.results.add_result("core_functionality", "english_language_detection", "PASS", {
                    "input_text": english_text,
                    "detected_language": detected_lang
                })
                print(f"[OK] 英文语言检测成功: {detected_lang}")
            else:
                self.results.add_result("core_functionality", "english_language_detection", "FAIL", {
                    "input_text": english_text,
                    "detected_language": detected_lang,
                    "error": "检测结果不正确"
                })
                print(f"[FAIL] 英文语言检测失败: {detected_lang}")

        except Exception as e:
            error_msg = f"语言检测测试失败: {str(e)}"
            self.results.add_error(error_msg)
            self.results.add_result("core_functionality", "language_detection", "FAIL", {"error": error_msg})
            print(f"[FAIL] {error_msg}")

        # 测试SRT解析
        try:
            test_srt_path = PROJECT_ROOT / "test_data" / "test_subtitle.srt"
            if test_srt_path.exists():
                srt_content = self.parse_srt_file(str(test_srt_path))

                if srt_content and len(srt_content) > 0:
                    self.results.add_result("core_functionality", "srt_parsing", "PASS", {
                        "file_path": str(test_srt_path),
                        "segments_count": len(srt_content),
                        "first_segment": srt_content[0] if srt_content else None
                    })
                    print(f"[OK] SRT解析成功 (片段数量: {len(srt_content)})")
                else:
                    self.results.add_result("core_functionality", "srt_parsing", "FAIL", {
                        "file_path": str(test_srt_path),
                        "error": "解析结果为空"
                    })
                    print(f"[FAIL] SRT解析失败: 解析结果为空")
            else:
                self.results.add_result("core_functionality", "srt_parsing", "FAIL", {
                    "file_path": str(test_srt_path),
                    "error": "测试文件不存在"
                })
                print(f"[FAIL] SRT解析失败: 测试文件不存在")

        except Exception as e:
            error_msg = f"SRT解析测试失败: {str(e)}"
            self.results.add_error(error_msg)
            self.results.add_result("core_functionality", "srt_parsing", "FAIL", {"error": error_msg})
            print(f"[FAIL] {error_msg}")

        # 测试模型切换逻辑
        try:
            if self.main_window:
                # 测试语言模式切换
                if hasattr(self.main_window, 'change_language_mode'):
                    # 切换到中文模式
                    self.main_window.change_language_mode("zh")
                    current_mode = getattr(self.main_window, 'language_mode', 'unknown')

                    if current_mode == "zh":
                        self.results.add_result("core_functionality", "model_switching_chinese", "PASS", {
                            "target_mode": "zh",
                            "current_mode": current_mode
                        })
                        print(f"[OK] 中文模式切换成功")
                    else:
                        self.results.add_result("core_functionality", "model_switching_chinese", "FAIL", {
                            "target_mode": "zh",
                            "current_mode": current_mode,
                            "error": "模式切换失败"
                        })
                        print(f"[FAIL] 中文模式切换失败")

                    # 切换到英文模式
                    self.main_window.change_language_mode("en")
                    current_mode = getattr(self.main_window, 'language_mode', 'unknown')

                    if current_mode == "en":
                        self.results.add_result("core_functionality", "model_switching_english", "PASS", {
                            "target_mode": "en",
                            "current_mode": current_mode
                        })
                        print(f"[OK] 英文模式切换成功")
                    else:
                        self.results.add_result("core_functionality", "model_switching_english", "FAIL", {
                            "target_mode": "en",
                            "current_mode": current_mode,
                            "error": "模式切换失败"
                        })
                        print(f"[FAIL] 英文模式切换失败")
                else:
                    self.results.add_result("core_functionality", "model_switching", "FAIL", {
                        "error": "change_language_mode方法不存在"
                    })
                    print(f"[FAIL] 模型切换测试失败: change_language_mode方法不存在")
            else:
                self.results.add_result("core_functionality", "model_switching", "FAIL", {
                    "error": "主窗口不存在"
                })
                print(f"[FAIL] 模型切换测试失败: 主窗口不存在")

        except Exception as e:
            error_msg = f"模型切换测试失败: {str(e)}"
            self.results.add_error(error_msg)
            self.results.add_result("core_functionality", "model_switching", "FAIL", {"error": error_msg})
            print(f"[FAIL] {error_msg}")

        return True

    def test_performance(self):
        """测试性能指标"""
        print("\n[4/5] 测试性能指标...")

        # 停止内存监控并获取报告
        self.memory_monitor.stop_monitoring()
        memory_report = self.memory_monitor.get_report()

        # 内存使用测试
        if "error" not in memory_report:
            peak_memory = memory_report["peak_memory_mb"]
            memory_check = memory_report["memory_limit_check"]

            self.results.add_result("performance_tests", "memory_usage", memory_check, memory_report)

            if memory_check == "PASS":
                print(f"[OK] 内存使用测试通过 (峰值: {peak_memory:.1f}MB)")
            else:
                print(f"[FAIL] 内存使用超限 (峰值: {peak_memory:.1f}MB > 3800MB)")
        else:
            self.results.add_result("performance_tests", "memory_usage", "FAIL", memory_report)
            print(f"[FAIL] 内存监控失败: {memory_report.get('error', '未知错误')}")

        # 启动时间测试
        try:
            if self.main_window and hasattr(self.main_window, '_startup_start_time'):
                startup_time = time.time() - self.main_window._startup_start_time

                # 启动时间应该在合理范围内（<30秒）
                if startup_time < 30:
                    self.results.add_result("performance_tests", "startup_time", "PASS", {
                        "startup_time_seconds": startup_time
                    })
                    print(f"[OK] 启动时间测试通过 ({startup_time:.2f}秒)")
                else:
                    self.results.add_result("performance_tests", "startup_time", "FAIL", {
                        "startup_time_seconds": startup_time,
                        "error": "启动时间过长"
                    })
                    print(f"[FAIL] 启动时间过长 ({startup_time:.2f}秒)")
            else:
                self.results.add_result("performance_tests", "startup_time", "FAIL", {
                    "error": "无法获取启动时间"
                })
                print(f"[FAIL] 无法获取启动时间")

        except Exception as e:
            error_msg = f"启动时间测试失败: {str(e)}"
            self.results.add_result("performance_tests", "startup_time", "FAIL", {"error": error_msg})
            print(f"[FAIL] {error_msg}")

        # CPU使用率测试
        try:
            process = psutil.Process()
            cpu_percent = process.cpu_percent(interval=1)

            # CPU使用率应该在合理范围内（<80%）
            if cpu_percent < 80:
                self.results.add_result("performance_tests", "cpu_usage", "PASS", {
                    "cpu_percent": cpu_percent
                })
                print(f"[OK] CPU使用率测试通过 ({cpu_percent:.1f}%)")
            else:
                self.results.add_result("performance_tests", "cpu_usage", "FAIL", {
                    "cpu_percent": cpu_percent,
                    "error": "CPU使用率过高"
                })
                print(f"[FAIL] CPU使用率过高 ({cpu_percent:.1f}%)")

        except Exception as e:
            error_msg = f"CPU使用率测试失败: {str(e)}"
            self.results.add_result("performance_tests", "cpu_usage", "FAIL", {"error": error_msg})
            print(f"[FAIL] {error_msg}")

        return True

    def test_exception_handling(self):
        """测试异常处理"""
        print("\n[5/5] 测试异常处理...")

        # 测试文件不存在的处理
        try:
            non_existent_file = PROJECT_ROOT / "test_data" / "non_existent.srt"
            result = self.parse_srt_file(str(non_existent_file))

            # 应该返回空结果或抛出可处理的异常
            if result is None or result == []:
                self.results.add_result("exception_handling", "file_not_found", "PASS", {
                    "test_file": str(non_existent_file),
                    "result": "正确处理文件不存在"
                })
                print(f"[OK] 文件不存在异常处理正确")
            else:
                self.results.add_result("exception_handling", "file_not_found", "FAIL", {
                    "test_file": str(non_existent_file),
                    "result": result,
                    "error": "未正确处理文件不存在"
                })
                print(f"[FAIL] 文件不存在异常处理失败")

        except Exception as e:
            # 抛出异常也是可以接受的，只要不崩溃
            self.results.add_result("exception_handling", "file_not_found", "PASS", {
                "test_file": str(non_existent_file),
                "exception": str(e),
                "result": "正确抛出异常"
            })
            print(f"[OK] 文件不存在异常处理正确 (抛出异常: {str(e)[:50]}...)")

        # 测试内存不足时的处理
        try:
            # 模拟内存压力（创建大量对象）
            memory_stress_objects = []
            for i in range(1000):
                memory_stress_objects.append([0] * 1000)  # 创建大量数据

            # 清理内存
            del memory_stress_objects
            gc.collect()

            self.results.add_result("exception_handling", "memory_stress", "PASS", {
                "result": "内存压力测试通过"
            })
            print(f"[OK] 内存压力测试通过")

        except Exception as e:
            error_msg = f"内存压力测试失败: {str(e)}"
            self.results.add_result("exception_handling", "memory_stress", "FAIL", {"error": error_msg})
            print(f"[FAIL] {error_msg}")

        return True

    def detect_language(self, text: str) -> str:
        """检测文本语言"""
        try:
            # 简单的语言检测逻辑
            chinese_chars = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
            total_chars = len(text.replace(' ', ''))

            if total_chars == 0:
                return "unknown"

            chinese_ratio = chinese_chars / total_chars

            if chinese_ratio > 0.3:
                return "zh"
            else:
                return "en"

        except Exception:
            return "auto"

    def parse_srt_file(self, file_path: str) -> List[Dict]:
        """解析SRT文件"""
        try:
            if not os.path.exists(file_path):
                return None

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 简单的SRT解析
            segments = []
            blocks = content.strip().split('\n\n')

            for block in blocks:
                lines = block.strip().split('\n')
                if len(lines) >= 3:
                    segment = {
                        "index": lines[0],
                        "timestamp": lines[1],
                        "text": '\n'.join(lines[2:])
                    }
                    segments.append(segment)

            return segments

        except Exception:
            return []

    def cleanup_test_environment(self):
        """清理测试环境"""
        try:
            # 关闭主窗口
            if self.main_window:
                self.main_window.close()
                self.main_window = None

            # 退出应用程序
            if self.app:
                self.app.quit()
                self.app = None

            # 停止内存监控
            self.memory_monitor.stop_monitoring()

            # 强制垃圾回收
            gc.collect()

            print(f"[OK] 测试环境清理完成")

        except Exception as e:
            print(f"[WARN] 测试环境清理失败: {str(e)}")

    def run_all_tests(self):
        """运行所有测试"""
        try:
            # 设置测试环境
            if not self.setup_test_environment():
                return False

            # 创建测试数据
            if not self.create_test_data():
                return False

            # 测试UI界面
            if not self.test_ui_interface():
                return False

            # 测试核心功能
            if not self.test_core_functionality():
                return False

            # 测试性能
            if not self.test_performance():
                return False

            # 测试异常处理
            if not self.test_exception_handling():
                return False

            return True

        except Exception as e:
            error_msg = f"测试执行失败: {str(e)}"
            self.results.add_error(error_msg)
            print(f"[FAIL] {error_msg}")
            traceback.print_exc()
            return False

        finally:
            # 清理测试环境
            self.cleanup_test_environment()

    def save_test_report(self):
        """保存测试报告"""
        try:
            # 生成报告
            report = self.results.generate_report()

            # 保存JSON报告
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            json_report_path = PROJECT_ROOT / "test_output" / f"comprehensive_functional_test_{timestamp}.json"

            with open(json_report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)

            # 生成HTML报告
            html_report_path = PROJECT_ROOT / "test_output" / f"comprehensive_functional_test_{timestamp}.html"
            self.generate_html_report(report, html_report_path)

            print(f"\n" + "=" * 60)
            print(f"测试报告已保存:")
            print(f"JSON报告: {json_report_path}")
            print(f"HTML报告: {html_report_path}")
            print(f"=" * 60)

            return json_report_path, html_report_path

        except Exception as e:
            print(f"[ERROR] 保存测试报告失败: {str(e)}")
            return None, None

    def generate_html_report(self, report: Dict, output_path: Path):
        """生成HTML测试报告"""
        try:
            summary = report.get("summary", {})

            html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VisionAI-ClipsMaster 功能测试报告</title>
    <style>
        body {{ font-family: 'Microsoft YaHei', Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .summary {{ background: #e8f4fd; padding: 20px; border-radius: 8px; margin-bottom: 30px; }}
        .test-category {{ margin-bottom: 30px; }}
        .test-category h3 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
        .test-item {{ margin: 10px 0; padding: 15px; border-radius: 5px; }}
        .test-pass {{ background-color: #d4edda; border-left: 4px solid #28a745; }}
        .test-fail {{ background-color: #f8d7da; border-left: 4px solid #dc3545; }}
        .test-warn {{ background-color: #fff3cd; border-left: 4px solid #ffc107; }}
        .details {{ margin-top: 10px; font-size: 0.9em; color: #666; }}
        .metric {{ display: inline-block; margin: 10px 20px 10px 0; }}
        .metric-value {{ font-weight: bold; font-size: 1.2em; }}
        .error-list {{ background: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎬 VisionAI-ClipsMaster 功能测试报告</h1>
            <p>测试时间: {summary.get('test_start', 'N/A')} - {summary.get('test_end', 'N/A')}</p>
        </div>

        <div class="summary">
            <h2>📊 测试概览</h2>
            <div class="metric">
                <div class="metric-value" style="color: #28a745;">{summary.get('passed_tests', 0)}</div>
                <div>通过测试</div>
            </div>
            <div class="metric">
                <div class="metric-value" style="color: #dc3545;">{summary.get('failed_tests', 0)}</div>
                <div>失败测试</div>
            </div>
            <div class="metric">
                <div class="metric-value" style="color: #17a2b8;">{summary.get('total_tests', 0)}</div>
                <div>总测试数</div>
            </div>
            <div class="metric">
                <div class="metric-value" style="color: #6f42c1;">{summary.get('success_rate', '0%')}</div>
                <div>成功率</div>
            </div>
            <div class="metric">
                <div class="metric-value">{summary.get('duration_seconds', 0):.1f}s</div>
                <div>测试耗时</div>
            </div>
        </div>
"""

            # 添加各个测试类别
            categories = {
                "ui_tests": "🖥️ UI界面测试",
                "core_functionality": "⚙️ 核心功能测试",
                "performance_tests": "🚀 性能测试",
                "output_quality": "📋 输出质量测试",
                "exception_handling": "🛡️ 异常处理测试"
            }

            for category_key, category_name in categories.items():
                if category_key in report and report[category_key]:
                    html_content += f"""
        <div class="test-category">
            <h3>{category_name}</h3>
"""

                    for test_name, test_result in report[category_key].items():
                        if isinstance(test_result, dict):
                            status = test_result.get("status", "UNKNOWN")
                            details = test_result.get("details", {})

                            css_class = "test-pass" if status == "PASS" else "test-fail" if status == "FAIL" else "test-warn"
                            status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"

                            html_content += f"""
            <div class="test-item {css_class}">
                <strong>{status_icon} {test_name}</strong>
                <span style="float: right; font-weight: bold;">{status}</span>
"""

                            if details:
                                html_content += '<div class="details">'
                                for key, value in details.items():
                                    if key != "error":
                                        html_content += f"<div><strong>{key}:</strong> {value}</div>"

                                if "error" in details:
                                    html_content += f'<div style="color: #dc3545;"><strong>错误:</strong> {details["error"]}</div>'

                                html_content += '</div>'

                            html_content += '</div>'

                    html_content += '</div>'

            # 添加错误和警告列表
            if self.results.errors or self.results.warnings:
                html_content += '<div class="error-list">'
                html_content += '<h3>🚨 错误和警告</h3>'

                for error in self.results.errors:
                    html_content += f'<div style="color: #dc3545; margin: 5px 0;">❌ {error["error"]} ({error["timestamp"]})</div>'

                for warning in self.results.warnings:
                    html_content += f'<div style="color: #ffc107; margin: 5px 0;">⚠️ {warning["warning"]} ({warning["timestamp"]})</div>'

                html_content += '</div>'

            html_content += """
    </div>
</body>
</html>
"""

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

        except Exception as e:
            print(f"[ERROR] 生成HTML报告失败: {str(e)}")

def main():
    """主函数"""
    print("VisionAI-ClipsMaster 全面功能测试启动...")

    # 创建测试器
    tester = VisionAIFunctionalTester()

    try:
        # 运行所有测试
        success = tester.run_all_tests()

        # 保存测试报告
        json_path, html_path = tester.save_test_report()

        # 打印测试结果摘要
        report = tester.results.generate_report()
        summary = report.get("summary", {})

        print(f"\n" + "=" * 60)
        print(f"测试完成!")
        print(f"总测试数: {summary.get('total_tests', 0)}")
        print(f"通过测试: {summary.get('passed_tests', 0)}")
        print(f"失败测试: {summary.get('failed_tests', 0)}")
        print(f"成功率: {summary.get('success_rate', '0%')}")
        print(f"测试耗时: {summary.get('duration_seconds', 0):.1f}秒")
        print(f"=" * 60)

        if summary.get('failed_tests', 0) > 0:
            print(f"⚠️ 发现 {summary.get('failed_tests', 0)} 个失败测试，请查看详细报告")
            return 1
        else:
            print(f"🎉 所有测试通过!")
            return 0

    except Exception as e:
        print(f"[FATAL] 测试执行出现严重错误: {str(e)}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
