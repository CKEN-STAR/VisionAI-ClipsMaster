#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 集成功能测试套件

此脚本执行全面的集成功能测试，验证核心功能模块、性能指标和稳定性
"""

import os
import sys
import time
import json
import subprocess
import traceback
from datetime import datetime
from pathlib import Path

# 确保使用系统Python解释器
SYSTEM_PYTHON = r"C:\Users\13075\AppData\Local\Programs\Python\Python313\python.exe"

class IntegrationTestSuite:
    def __init__(self):
        self.test_results = {}
        self.start_time = time.time()
        self.project_root = Path(__file__).parent
        self.test_data_dir = self.project_root / "test_data"
        self.output_dir = self.project_root / "integration_test_output"
        self.output_dir.mkdir(exist_ok=True)
        
        # 测试配置
        self.config = {
            "memory_limit_gb": 4,
            "precision_threshold_seconds": 0.5,
            "ui_stability_minutes": 30,
            "target_ui_score": 75
        }
        
    def log(self, message, level="INFO"):
        """记录测试日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] [{level}] {message}"
        print(log_message)
        
        # 写入日志文件
        log_file = self.output_dir / "integration_test.log"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(log_message + "\n")
    
    def run_test(self, test_name, test_func):
        """运行单个测试并记录结果"""
        self.log(f"开始测试: {test_name}")
        start_time = time.time()
        
        try:
            result = test_func()
            duration = time.time() - start_time
            
            self.test_results[test_name] = {
                "status": "PASS" if result.get("success", False) else "FAIL",
                "duration": duration,
                "details": result,
                "timestamp": datetime.now().isoformat()
            }
            
            self.log(f"测试完成: {test_name} - {self.test_results[test_name]['status']} ({duration:.2f}s)")
            
        except Exception as e:
            duration = time.time() - start_time
            error_details = {
                "error": str(e),
                "traceback": traceback.format_exc()
            }
            
            self.test_results[test_name] = {
                "status": "ERROR",
                "duration": duration,
                "details": error_details,
                "timestamp": datetime.now().isoformat()
            }
            
            self.log(f"测试错误: {test_name} - {str(e)}", "ERROR")
    
    def test_environment_setup(self):
        """测试环境准备与验证"""
        results = {"success": True, "checks": {}}
        
        # 检查系统Python解释器
        try:
            result = subprocess.run([SYSTEM_PYTHON, "--version"], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                results["checks"]["python_interpreter"] = {
                    "status": "PASS",
                    "version": result.stdout.strip()
                }
            else:
                results["checks"]["python_interpreter"] = {
                    "status": "FAIL",
                    "error": result.stderr
                }
                results["success"] = False
        except Exception as e:
            results["checks"]["python_interpreter"] = {
                "status": "ERROR",
                "error": str(e)
            }
            results["success"] = False
        
        # 检查PyQt6依赖
        try:
            result = subprocess.run([SYSTEM_PYTHON, "-c", 
                                   "from PyQt6.QtCore import QT_VERSION_STR; print('PyQt6:', QT_VERSION_STR)"],
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                results["checks"]["pyqt6"] = {
                    "status": "PASS",
                    "version": result.stdout.strip()
                }
            else:
                results["checks"]["pyqt6"] = {
                    "status": "FAIL",
                    "error": result.stderr
                }
                results["success"] = False
        except Exception as e:
            results["checks"]["pyqt6"] = {
                "status": "ERROR",
                "error": str(e)
            }
            results["success"] = False
        
        # 检查FFmpeg配置
        ffmpeg_path = self.project_root / "bin" / "ffmpeg.exe"
        if ffmpeg_path.exists():
            try:
                result = subprocess.run([str(ffmpeg_path), "-version"],
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    results["checks"]["ffmpeg"] = {
                        "status": "PASS",
                        "version": result.stdout.split('\n')[0]
                    }
                else:
                    results["checks"]["ffmpeg"] = {
                        "status": "FAIL",
                        "error": result.stderr
                    }
                    results["success"] = False
            except Exception as e:
                results["checks"]["ffmpeg"] = {
                    "status": "ERROR",
                    "error": str(e)
                }
                results["success"] = False
        else:
            results["checks"]["ffmpeg"] = {
                "status": "FAIL",
                "error": "FFmpeg executable not found"
            }
            results["success"] = False
        
        # 检查测试数据
        required_test_files = [
            "test_data/valid_test_video.mp4",
            "test_data/sample_drama.srt",
            "test_data/test_chinese_drama.srt",
            "test_data/test_english_drama.srt"
        ]
        
        missing_files = []
        for file_path in required_test_files:
            if not (self.project_root / file_path).exists():
                missing_files.append(file_path)
        
        if missing_files:
            results["checks"]["test_data"] = {
                "status": "FAIL",
                "missing_files": missing_files
            }
            results["success"] = False
        else:
            results["checks"]["test_data"] = {
                "status": "PASS",
                "message": "All required test files found"
            }
        
        return results
    
    def test_dual_model_system(self):
        """测试双模型系统（Mock AI）"""
        results = {"success": True, "tests": {}}

        # 测试语言检测
        try:
            # 导入语言检测模块
            sys.path.insert(0, str(self.project_root / "src" / "core"))
            from language_detector import detect_language

            # 创建临时测试文件
            chinese_test_file = self.output_dir / "test_chinese.srt"
            with open(chinese_test_file, "w", encoding="utf-8") as f:
                f.write("1\n00:00:01,000 --> 00:00:03,000\n这是一个中文测试文本\n\n")

            lang_result = detect_language(str(chinese_test_file))

            if lang_result == "zh":
                results["tests"]["chinese_detection"] = {"status": "PASS"}
            else:
                results["tests"]["chinese_detection"] = {
                    "status": "FAIL",
                    "expected": "zh",
                    "actual": lang_result
                }
                results["success"] = False

            # 测试英文检测
            english_test_file = self.output_dir / "test_english.srt"
            with open(english_test_file, "w", encoding="utf-8") as f:
                f.write("1\n00:00:01,000 --> 00:00:03,000\nThis is an English test text\n\n")

            lang_result = detect_language(str(english_test_file))

            if lang_result == "en":
                results["tests"]["english_detection"] = {"status": "PASS"}
            else:
                results["tests"]["english_detection"] = {
                    "status": "FAIL",
                    "expected": "en",
                    "actual": lang_result
                }
                results["success"] = False

        except Exception as e:
            results["tests"]["language_detection"] = {
                "status": "ERROR",
                "error": str(e)
            }
            results["success"] = False

        # 测试Mock AI模型加载
        try:
            sys.path.insert(0, str(self.test_data_dir))
            from mock_ai_models import MockAIPlotAnalyzer, MockAIViralTransformer

            # 测试剧情分析器
            analyzer = MockAIPlotAnalyzer()
            test_subtitles = [
                {"text": "Hello world", "start_time": 1.0, "end_time": 3.0}
            ]
            analysis_result = analyzer.analyze_plot(test_subtitles, "en")

            if analysis_result and hasattr(analysis_result, 'language'):
                results["tests"]["plot_analyzer_mock"] = {"status": "PASS"}
            else:
                results["tests"]["plot_analyzer_mock"] = {
                    "status": "FAIL",
                    "error": "Invalid result from plot analyzer"
                }
                results["success"] = False

            # 测试病毒式转换器
            transformer = MockAIViralTransformer()
            transform_result = transformer.transform_to_viral(test_subtitles, "en")

            if transform_result and len(transform_result) > 0:
                results["tests"]["viral_transformer_mock"] = {"status": "PASS"}
            else:
                results["tests"]["viral_transformer_mock"] = {
                    "status": "FAIL",
                    "error": "Empty result from viral transformer"
                }
                results["success"] = False

        except Exception as e:
            results["tests"]["mock_models"] = {
                "status": "ERROR",
                "error": str(e)
            }
            results["success"] = False

        return results
    
    def test_screenplay_reconstruction(self):
        """测试剧本重构核心逻辑"""
        results = {"success": True, "tests": {}}

        try:
            # 测试SRT解析
            sys.path.insert(0, str(self.project_root / "src" / "core"))
            from srt_parser import parse_srt

            # 测试中文SRT解析
            chinese_srt_path = self.test_data_dir / "test_chinese_drama.srt"
            if chinese_srt_path.exists():
                chinese_subtitles = parse_srt(str(chinese_srt_path))

                if chinese_subtitles and len(chinese_subtitles) > 0:
                    results["tests"]["chinese_srt_parsing"] = {
                        "status": "PASS",
                        "subtitle_count": len(chinese_subtitles)
                    }
                else:
                    results["tests"]["chinese_srt_parsing"] = {
                        "status": "FAIL",
                        "error": "No subtitles parsed"
                    }
                    results["success"] = False
            else:
                results["tests"]["chinese_srt_parsing"] = {
                    "status": "SKIP",
                    "reason": "Chinese SRT file not found"
                }

            # 测试英文SRT解析
            english_srt_path = self.test_data_dir / "test_english_drama.srt"
            if english_srt_path.exists():
                english_subtitles = parse_srt(str(english_srt_path))

                if english_subtitles and len(english_subtitles) > 0:
                    results["tests"]["english_srt_parsing"] = {
                        "status": "PASS",
                        "subtitle_count": len(english_subtitles)
                    }
                else:
                    results["tests"]["english_srt_parsing"] = {
                        "status": "FAIL",
                        "error": "No subtitles parsed"
                    }
                    results["success"] = False
            else:
                results["tests"]["english_srt_parsing"] = {
                    "status": "SKIP",
                    "reason": "English SRT file not found"
                }

        except Exception as e:
            results["tests"]["srt_parsing"] = {
                "status": "ERROR",
                "error": str(e)
            }
            results["success"] = False

        return results

    def test_video_processing_precision(self):
        """测试视频处理精度"""
        results = {"success": True, "tests": {}}

        try:
            # 测试FFmpeg视频信息获取
            test_video = self.test_data_dir / "valid_test_video.mp4"
            if test_video.exists():
                ffmpeg_path = self.project_root / "bin" / "ffmpeg.exe"
                result = subprocess.run([
                    str(ffmpeg_path), "-i", str(test_video),
                    "-f", "null", "-"
                ], capture_output=True, text=True, timeout=30)

                if "Duration:" in result.stderr:
                    # 提取时长信息
                    duration_line = [line for line in result.stderr.split('\n') if 'Duration:' in line]
                    if duration_line:
                        results["tests"]["video_info_extraction"] = {
                            "status": "PASS",
                            "duration_info": duration_line[0].strip()
                        }
                    else:
                        results["tests"]["video_info_extraction"] = {"status": "PASS"}
                else:
                    results["tests"]["video_info_extraction"] = {
                        "status": "FAIL",
                        "error": "Cannot extract video duration",
                        "stderr": result.stderr[:500]  # 前500字符的错误信息
                    }
                    results["success"] = False
            else:
                results["tests"]["video_info_extraction"] = {
                    "status": "SKIP",
                    "reason": "Test video file not found"
                }

        except Exception as e:
            results["tests"]["video_processing"] = {
                "status": "ERROR",
                "error": str(e)
            }
            results["success"] = False

        return results

    def test_jianying_export(self):
        """测试剪映工程文件导出"""
        results = {"success": True, "tests": {}}

        try:
            # 检查导出器模块
            sys.path.insert(0, str(self.project_root / "src" / "exporters"))
            from jianying_pro_exporter import JianYingProExporter

            exporter = JianYingProExporter()

            # 测试基本导出功能
            test_segments = [
                {
                    "start_time": 1.0,
                    "end_time": 3.0,
                    "video_path": "test.mp4",
                    "subtitle": "Test subtitle"
                }
            ]

            export_result = exporter.export_project(test_segments, str(self.output_dir / "test_project"))

            if export_result:
                results["tests"]["jianying_export"] = {"status": "PASS"}
            else:
                results["tests"]["jianying_export"] = {
                    "status": "FAIL",
                    "error": "Export failed"
                }
                results["success"] = False

        except Exception as e:
            results["tests"]["jianying_export"] = {
                "status": "ERROR",
                "error": str(e)
            }
            results["success"] = False

        return results

    def test_memory_performance(self):
        """测试内存和性能"""
        results = {"success": True, "tests": {}}

        try:
            import psutil

            # 获取当前内存使用
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024

            # 检查内存使用是否在合理范围内（小于1GB）
            if memory_mb < 1024:
                results["tests"]["memory_usage"] = {
                    "status": "PASS",
                    "memory_mb": f"{memory_mb:.1f}MB"
                }
            else:
                results["tests"]["memory_usage"] = {
                    "status": "FAIL",
                    "memory_mb": f"{memory_mb:.1f}MB",
                    "error": "Memory usage too high"
                }
                results["success"] = False

        except ImportError:
            results["tests"]["memory_usage"] = {
                "status": "SKIP",
                "reason": "psutil not available"
            }
        except Exception as e:
            results["tests"]["memory_performance"] = {
                "status": "ERROR",
                "error": str(e)
            }
            results["success"] = False

        return results

    def test_ui_basic_functionality(self):
        """测试UI基本功能"""
        results = {"success": True, "tests": {}}

        try:
            # 检查UI文件是否存在
            ui_file = self.project_root / "simple_ui_fixed.py"
            if ui_file.exists():
                results["tests"]["ui_file_exists"] = {"status": "PASS"}

                # 尝试导入UI模块（不启动GUI）
                import importlib.util
                spec = importlib.util.spec_from_file_location("simple_ui_fixed", ui_file)
                ui_module = importlib.util.module_from_spec(spec)

                # 检查关键类是否存在
                with open(ui_file, 'r', encoding='utf-8') as f:
                    ui_content = f.read()

                if "class SimpleScreenplayApp" in ui_content:
                    results["tests"]["ui_main_class"] = {"status": "PASS"}
                else:
                    results["tests"]["ui_main_class"] = {
                        "status": "FAIL",
                        "error": "Main UI class not found"
                    }
                    results["success"] = False
            else:
                results["tests"]["ui_file_exists"] = {
                    "status": "FAIL",
                    "error": "UI file not found"
                }
                results["success"] = False

        except Exception as e:
            results["tests"]["ui_functionality"] = {
                "status": "ERROR",
                "error": str(e)
            }
            results["success"] = False

        return results

    def run_all_tests(self):
        """运行所有集成测试"""
        self.log("开始VisionAI-ClipsMaster集成功能测试")
        
        # 测试列表
        tests = [
            ("环境准备与验证", self.test_environment_setup),
            ("双模型系统测试", self.test_dual_model_system),
            ("剧本重构核心逻辑测试", self.test_screenplay_reconstruction),
            ("视频处理精度测试", self.test_video_processing_precision),
            ("剪映工程文件导出测试", self.test_jianying_export),
            ("内存和性能测试", self.test_memory_performance),
            ("UI基本功能测试", self.test_ui_basic_functionality),
        ]
        
        # 执行测试
        for test_name, test_func in tests:
            self.run_test(test_name, test_func)
        
        # 生成测试报告
        self.generate_report()
    
    def generate_report(self):
        """生成测试报告"""
        total_duration = time.time() - self.start_time
        
        # 统计结果
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results.values() if r["status"] == "PASS")
        failed_tests = sum(1 for r in self.test_results.values() if r["status"] == "FAIL")
        error_tests = sum(1 for r in self.test_results.values() if r["status"] == "ERROR")
        
        # 生成报告
        report = {
            "test_summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "errors": error_tests,
                "success_rate": f"{(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "0%",
                "total_duration": f"{total_duration:.2f}s"
            },
            "test_results": self.test_results,
            "timestamp": datetime.now().isoformat(),
            "environment": {
                "python_version": sys.version,
                "platform": sys.platform,
                "project_root": str(self.project_root)
            }
        }
        
        # 保存JSON报告
        report_file = self.output_dir / f"integration_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # 打印摘要
        self.log("=" * 60)
        self.log("集成测试完成")
        self.log(f"总测试数: {total_tests}")
        self.log(f"通过: {passed_tests}")
        self.log(f"失败: {failed_tests}")
        self.log(f"错误: {error_tests}")
        self.log(f"成功率: {report['test_summary']['success_rate']}")
        self.log(f"总耗时: {report['test_summary']['total_duration']}")
        self.log(f"报告文件: {report_file}")
        self.log("=" * 60)

if __name__ == "__main__":
    test_suite = IntegrationTestSuite()
    test_suite.run_all_tests()
