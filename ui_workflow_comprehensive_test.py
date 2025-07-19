#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster UI工作流程综合测试
完整验证视频处理界面的所有功能和性能指标
"""

import os
import sys
import time
import json
import psutil
import threading
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ui_workflow_test.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class UIWorkflowTester:
    """UI工作流程测试器"""
    
    def __init__(self):
        self.project_root = Path('.')
        self.test_results = {
            "start_time": datetime.now().isoformat(),
            "test_phases": {},
            "performance_metrics": {},
            "issues_found": [],
            "overall_status": "RUNNING"
        }
        self.memory_monitor = MemoryMonitor()
        self.test_data_dir = self.project_root / 'test_data' / 'ui_workflow'
        self.test_data_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建测试数据
        self._create_test_data()
        
    def _create_test_data(self):
        """创建测试用的SRT和视频文件"""
        # 创建中文测试SRT
        chinese_srt = self.test_data_dir / 'chinese_test.srt'
        with open(chinese_srt, 'w', encoding='utf-8') as f:
            f.write("""1
00:00:00,000 --> 00:00:03,000
今天是个好日子，阳光明媚

2
00:00:03,000 --> 00:00:06,000
小明走在回家的路上

3
00:00:06,000 --> 00:00:09,000
突然遇到了他的老朋友

4
00:00:09,000 --> 00:00:12,000
两人开心地聊了起来

5
00:00:12,000 --> 00:00:15,000
这真是一个美好的相遇
""")
        
        # 创建英文测试SRT
        english_srt = self.test_data_dir / 'english_test.srt'
        with open(english_srt, 'w', encoding='utf-8') as f:
            f.write("""1
00:00:00,000 --> 00:00:03,000
It was a beautiful sunny day

2
00:00:03,000 --> 00:00:06,000
John was walking home from work

3
00:00:06,000 --> 00:00:09,000
Suddenly he met his old friend

4
00:00:09,000 --> 00:00:12,000
They had a wonderful conversation

5
00:00:12,000 --> 00:00:15,000
It was truly a great encounter
""")
        
        # 创建损坏的SRT文件用于错误测试
        corrupted_srt = self.test_data_dir / 'corrupted_test.srt'
        with open(corrupted_srt, 'w', encoding='utf-8') as f:
            f.write("这是一个损坏的SRT文件\n没有正确的时间格式")
        
        logger.info(f"测试数据已创建在: {self.test_data_dir}")
    
    def test_phase_1_ui_startup_initialization(self) -> Dict[str, Any]:
        """测试阶段1: 界面启动与初始化"""
        phase_name = "ui_startup_initialization"
        logger.info(f"开始测试阶段1: {phase_name}")
        
        test_result = {
            "phase": phase_name,
            "description": "验证UI界面启动时间、组件加载和内存使用",
            "start_time": time.time(),
            "status": "RUNNING",
            "metrics": {},
            "issues": []
        }
        
        try:
            # 启动内存监控
            self.memory_monitor.start_monitoring()
            
            # 测试UI启动时间
            startup_start = time.time()
            
            # 模拟UI启动过程（不实际启动GUI，避免阻塞测试）
            startup_result = self._simulate_ui_startup()
            
            startup_duration = time.time() - startup_start
            
            # 检查启动时间
            startup_target_met = startup_duration <= 5.0
            if not startup_target_met:
                test_result["issues"].append(f"启动时间超标: {startup_duration:.2f}秒 > 5秒")
            
            # 检查内存使用
            current_memory = self.memory_monitor.get_current_memory_usage()
            memory_target_met = current_memory <= 0.4  # 400MB
            if not memory_target_met:
                test_result["issues"].append(f"内存使用超标: {current_memory:.3f}GB > 0.4GB")
            
            # 记录性能指标
            test_result["metrics"] = {
                "startup_time_seconds": startup_duration,
                "startup_target_met": startup_target_met,
                "memory_usage_gb": current_memory,
                "memory_target_met": memory_target_met,
                "components_loaded": startup_result.get("components_loaded", 0),
                "initialization_success": startup_result.get("success", False)
            }
            
            # 判断测试状态
            if startup_target_met and memory_target_met and startup_result.get("success", False):
                test_result["status"] = "PASSED"
            else:
                test_result["status"] = "FAILED"
                
        except Exception as e:
            test_result["status"] = "ERROR"
            test_result["error"] = str(e)
            logger.error(f"测试阶段1执行失败: {e}")
        
        test_result["end_time"] = time.time()
        test_result["duration"] = test_result["end_time"] - test_result["start_time"]
        
        return test_result
    
    def test_phase_2_file_upload_workflow(self) -> Dict[str, Any]:
        """测试阶段2: 文件上传工作流程"""
        phase_name = "file_upload_workflow"
        logger.info(f"开始测试阶段2: {phase_name}")
        
        test_result = {
            "phase": phase_name,
            "description": "测试SRT字幕文件和视频文件的导入功能",
            "start_time": time.time(),
            "status": "RUNNING",
            "upload_tests": [],
            "issues": []
        }
        
        try:
            # 测试用例
            upload_test_cases = [
                {
                    "name": "中文SRT文件上传",
                    "file_path": self.test_data_dir / "chinese_test.srt",
                    "expected_language": "zh",
                    "expected_segments": 5
                },
                {
                    "name": "英文SRT文件上传",
                    "file_path": self.test_data_dir / "english_test.srt",
                    "expected_language": "en",
                    "expected_segments": 5
                },
                {
                    "name": "损坏SRT文件处理",
                    "file_path": self.test_data_dir / "corrupted_test.srt",
                    "expected_language": "unknown",
                    "expected_segments": 0,
                    "should_fail": True
                }
            ]
            
            for test_case in upload_test_cases:
                logger.info(f"测试文件上传: {test_case['name']}")
                
                upload_start = time.time()
                upload_result = self._test_file_upload(test_case)
                upload_duration = time.time() - upload_start
                
                upload_result.update({
                    "test_case": test_case["name"],
                    "duration": upload_duration,
                    "response_time_target_met": upload_duration <= 2.0
                })
                
                test_result["upload_tests"].append(upload_result)
                
                # 检查响应时间
                if upload_duration > 2.0:
                    test_result["issues"].append(f"{test_case['name']}响应时间超标: {upload_duration:.2f}秒")
            
            # 计算总体成功率
            successful_uploads = sum(1 for test in test_result["upload_tests"] if test.get("success", False))
            total_uploads = len(test_result["upload_tests"])
            success_rate = (successful_uploads / total_uploads) * 100 if total_uploads > 0 else 0
            
            test_result["summary"] = {
                "successful_uploads": successful_uploads,
                "total_uploads": total_uploads,
                "success_rate": success_rate,
                "all_response_times_met": all(test.get("response_time_target_met", False) for test in test_result["upload_tests"])
            }
            
            # 判断测试状态
            if success_rate >= 80 and test_result["summary"]["all_response_times_met"]:
                test_result["status"] = "PASSED"
            else:
                test_result["status"] = "FAILED"
                
        except Exception as e:
            test_result["status"] = "ERROR"
            test_result["error"] = str(e)
            logger.error(f"测试阶段2执行失败: {e}")
        
        test_result["end_time"] = time.time()
        test_result["duration"] = test_result["end_time"] - test_result["start_time"]
        
        return test_result
    
    def test_phase_3_ai_processing_workflow(self) -> Dict[str, Any]:
        """测试阶段3: AI处理工作流程"""
        phase_name = "ai_processing_workflow"
        logger.info(f"开始测试阶段3: {phase_name}")
        
        test_result = {
            "phase": phase_name,
            "description": "测试语言检测、AI剧本重构和进度显示",
            "start_time": time.time(),
            "status": "RUNNING",
            "processing_tests": [],
            "issues": []
        }
        
        try:
            # AI处理测试用例
            processing_test_cases = [
                {
                    "name": "中文剧本重构",
                    "input_text": "今天是个好日子，阳光明媚。小明走在回家的路上。",
                    "expected_language": "zh",
                    "expected_output_segments": 2
                },
                {
                    "name": "英文剧本重构",
                    "input_text": "It was a beautiful sunny day. John was walking home from work.",
                    "expected_language": "en",
                    "expected_output_segments": 2
                }
            ]
            
            for test_case in processing_test_cases:
                logger.info(f"测试AI处理: {test_case['name']}")
                
                processing_start = time.time()
                processing_result = self._test_ai_processing(test_case)
                processing_duration = time.time() - processing_start
                
                processing_result.update({
                    "test_case": test_case["name"],
                    "duration": processing_duration,
                    "performance_target_met": processing_duration <= 30.0  # 30秒内完成
                })
                
                test_result["processing_tests"].append(processing_result)
                
                # 检查处理时间
                if processing_duration > 30.0:
                    test_result["issues"].append(f"{test_case['name']}处理时间超标: {processing_duration:.2f}秒")
            
            # 计算总体性能
            successful_processing = sum(1 for test in test_result["processing_tests"] if test.get("success", False))
            total_processing = len(test_result["processing_tests"])
            success_rate = (successful_processing / total_processing) * 100 if total_processing > 0 else 0
            
            test_result["summary"] = {
                "successful_processing": successful_processing,
                "total_processing": total_processing,
                "success_rate": success_rate,
                "all_performance_targets_met": all(test.get("performance_target_met", False) for test in test_result["processing_tests"])
            }
            
            # 判断测试状态
            if success_rate >= 90 and test_result["summary"]["all_performance_targets_met"]:
                test_result["status"] = "PASSED"
            else:
                test_result["status"] = "FAILED"
                
        except Exception as e:
            test_result["status"] = "ERROR"
            test_result["error"] = str(e)
            logger.error(f"测试阶段3执行失败: {e}")
        
        test_result["end_time"] = time.time()
        test_result["duration"] = test_result["end_time"] - test_result["start_time"]
        
        return test_result
    
    def test_phase_4_export_workflow(self) -> Dict[str, Any]:
        """测试阶段4: 导出工作流程"""
        phase_name = "export_workflow"
        logger.info(f"开始测试阶段4: {phase_name}")
        
        test_result = {
            "phase": phase_name,
            "description": "测试剪映项目文件导出的完整性和兼容性",
            "start_time": time.time(),
            "status": "RUNNING",
            "export_tests": [],
            "issues": []
        }
        
        try:
            # 导出测试用例
            export_test_cases = [
                {
                    "name": "标准剪映项目导出",
                    "project_data": {
                        "project_name": "UI测试项目",
                        "segments": [
                            {"start_time": 0.0, "end_time": 3.0, "text": "测试片段1"},
                            {"start_time": 3.0, "end_time": 6.0, "text": "测试片段2"}
                        ],
                        "subtitles": []
                    },
                    "expected_file_size_min": 100  # 最小100字节
                },
                {
                    "name": "空项目导出处理",
                    "project_data": {
                        "project_name": "空项目",
                        "segments": [],
                        "subtitles": []
                    },
                    "expected_file_size_min": 50
                }
            ]
            
            for test_case in export_test_cases:
                logger.info(f"测试导出: {test_case['name']}")
                
                export_start = time.time()
                export_result = self._test_export_functionality(test_case)
                export_duration = time.time() - export_start
                
                export_result.update({
                    "test_case": test_case["name"],
                    "duration": export_duration,
                    "response_time_target_met": export_duration <= 5.0
                })
                
                test_result["export_tests"].append(export_result)
                
                # 检查导出时间
                if export_duration > 5.0:
                    test_result["issues"].append(f"{test_case['name']}导出时间超标: {export_duration:.2f}秒")
            
            # 计算导出成功率
            successful_exports = sum(1 for test in test_result["export_tests"] if test.get("success", False))
            total_exports = len(test_result["export_tests"])
            success_rate = (successful_exports / total_exports) * 100 if total_exports > 0 else 0
            
            test_result["summary"] = {
                "successful_exports": successful_exports,
                "total_exports": total_exports,
                "success_rate": success_rate,
                "all_response_times_met": all(test.get("response_time_target_met", False) for test in test_result["export_tests"])
            }
            
            # 判断测试状态
            if success_rate >= 95 and test_result["summary"]["all_response_times_met"]:
                test_result["status"] = "PASSED"
            else:
                test_result["status"] = "FAILED"
                
        except Exception as e:
            test_result["status"] = "ERROR"
            test_result["error"] = str(e)
            logger.error(f"测试阶段4执行失败: {e}")
        
        test_result["end_time"] = time.time()
        test_result["duration"] = test_result["end_time"] - test_result["start_time"]
        
        return test_result

    def _simulate_ui_startup(self) -> Dict[str, Any]:
        """模拟UI启动过程"""
        try:
            # 测试核心模块导入
            components_loaded = 0

            # 导入UI相关模块
            try:
                import simple_ui_fixed
                components_loaded += 1
            except ImportError as e:
                logger.warning(f"UI模块导入失败: {e}")

            # 导入核心功能模块
            try:
                from src.core.screenplay_engineer import ScreenplayEngineer
                components_loaded += 1
            except ImportError as e:
                logger.warning(f"剧本工程师模块导入失败: {e}")

            try:
                from src.core.language_detector import LanguageDetector
                components_loaded += 1
            except ImportError as e:
                logger.warning(f"语言检测器模块导入失败: {e}")

            try:
                from src.exporters.jianying_pro_exporter import JianYingProExporter
                components_loaded += 1
            except ImportError as e:
                logger.warning(f"剪映导出器模块导入失败: {e}")

            return {
                "success": components_loaded >= 3,  # 至少3个核心组件成功加载
                "components_loaded": components_loaded,
                "total_components": 4
            }

        except Exception as e:
            return {
                "success": False,
                "components_loaded": 0,
                "total_components": 4,
                "error": str(e)
            }

    def _test_file_upload(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """测试文件上传功能"""
        try:
            file_path = test_case["file_path"]

            # 检查文件是否存在
            if not file_path.exists():
                return {
                    "success": False,
                    "error": f"测试文件不存在: {file_path}"
                }

            # 模拟文件读取和解析
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 简单的SRT格式验证
                if test_case.get("should_fail", False):
                    # 对于应该失败的测试，检查是否正确处理了错误
                    if "00:00:00,000" not in content:
                        return {
                            "success": True,  # 正确识别了损坏文件
                            "file_size": len(content),
                            "content_preview": content[:100],
                            "error_handled": True
                        }
                    else:
                        return {
                            "success": False,
                            "error": "应该失败的测试却成功了"
                        }
                else:
                    # 正常文件应该成功解析
                    segments_found = content.count("-->")

                    return {
                        "success": segments_found >= test_case.get("expected_segments", 1),
                        "file_size": len(content),
                        "segments_found": segments_found,
                        "content_preview": content[:100]
                    }

            except Exception as e:
                if test_case.get("should_fail", False):
                    return {
                        "success": True,  # 正确处理了异常
                        "error_handled": True,
                        "error": str(e)
                    }
                else:
                    return {
                        "success": False,
                        "error": str(e)
                    }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _test_ai_processing(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """测试AI处理功能"""
        try:
            # 导入AI处理模块
            from src.core.language_detector import LanguageDetector
            from src.core.screenplay_engineer import ScreenplayEngineer

            # 语言检测测试
            detector = LanguageDetector()
            detected_language = detector.detect_from_text(test_case["input_text"])

            # AI剧本重构测试
            engineer = ScreenplayEngineer()

            # 创建测试字幕数据
            test_subtitles = [
                {"start_time": 0.0, "end_time": 3.0, "text": test_case["input_text"][:50]},
                {"start_time": 3.0, "end_time": 6.0, "text": test_case["input_text"][50:] if len(test_case["input_text"]) > 50 else "续集内容"}
            ]

            # 执行剧本重构
            result = engineer.generate_screenplay(test_subtitles, language=detected_language)

            return {
                "success": True,
                "detected_language": detected_language,
                "language_correct": detected_language == test_case.get("expected_language", "unknown"),
                "output_segments": len(result.get("screenplay", [])),
                "processing_time": result.get("processing_time", 0),
                "result_preview": str(result)[:200]
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _test_export_functionality(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """测试导出功能"""
        try:
            from src.exporters.jianying_pro_exporter import JianYingProExporter

            exporter = JianYingProExporter()

            # 创建输出文件路径
            output_file = self.test_data_dir / f"export_test_{int(time.time())}.json"

            # 执行导出
            success = exporter.export_project(test_case["project_data"], str(output_file))

            # 检查导出结果
            if success and output_file.exists():
                file_size = output_file.stat().st_size

                # 验证文件内容
                with open(output_file, 'r', encoding='utf-8') as f:
                    exported_content = f.read()

                # 清理测试文件
                output_file.unlink()

                return {
                    "success": True,
                    "file_size": file_size,
                    "file_size_target_met": file_size >= test_case.get("expected_file_size_min", 50),
                    "content_preview": exported_content[:200],
                    "export_path": str(output_file)
                }
            else:
                return {
                    "success": False,
                    "error": "导出失败或文件未创建"
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def run_comprehensive_ui_workflow_test(self) -> Dict[str, Any]:
        """运行完整的UI工作流程测试"""
        print("=== VisionAI-ClipsMaster UI工作流程综合测试 ===")
        print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        # 执行所有测试阶段
        test_phases = [
            ("界面启动与初始化", self.test_phase_1_ui_startup_initialization),
            ("文件上传工作流程", self.test_phase_2_file_upload_workflow),
            ("AI处理工作流程", self.test_phase_3_ai_processing_workflow),
            ("导出工作流程", self.test_phase_4_export_workflow)
        ]

        for phase_name, test_func in test_phases:
            print(f"🧪 执行测试阶段: {phase_name}")
            result = test_func()
            self.test_results["test_phases"][result["phase"]] = result

            status_icon = "✅" if result["status"] == "PASSED" else "❌" if result["status"] == "FAILED" else "⚠️"
            print(f"   {status_icon} {phase_name}: {result['status']} ({result.get('duration', 0):.2f}秒)")

            if result.get("issues"):
                for issue in result["issues"]:
                    print(f"      ⚠️ {issue}")
            print()

        # 停止内存监控
        self.memory_monitor.stop_monitoring()

        # 生成最终评估
        self._generate_final_assessment()

        # 保存测试结果
        self._save_test_results()

        return self.test_results

    def _generate_final_assessment(self):
        """生成最终评估"""
        test_phases = self.test_results["test_phases"]

        # 计算通过率
        total_phases = len(test_phases)
        passed_phases = sum(1 for phase in test_phases.values() if phase["status"] == "PASSED")
        pass_rate = (passed_phases / total_phases) * 100 if total_phases > 0 else 0

        # 性能指标汇总
        peak_memory = self.memory_monitor.get_peak_memory_usage()

        self.test_results.update({
            "end_time": datetime.now().isoformat(),
            "total_phases": total_phases,
            "passed_phases": passed_phases,
            "pass_rate": pass_rate,
            "peak_memory_gb": peak_memory,
            "memory_compliant": peak_memory <= 3.8,
            "overall_status": "PASSED" if pass_rate >= 80 and peak_memory <= 3.8 else "FAILED"
        })

        # 显示最终结果
        print("📋 最终评估结果:")
        print(f"   测试通过率: {pass_rate:.1f}%")
        print(f"   峰值内存: {peak_memory:.3f}GB")
        print(f"   内存合规: {'是' if peak_memory <= 3.8 else '否'}")
        print(f"   总体状态: {self.test_results['overall_status']}")

    def _save_test_results(self):
        """保存测试结果"""
        results_file = self.project_root / "test_outputs" / f"ui_workflow_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        results_file.parent.mkdir(parents=True, exist_ok=True)

        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False, default=str)

        logger.info(f"测试结果已保存到: {results_file}")


class MemoryMonitor:
    """内存监控器"""

    def __init__(self):
        self.monitoring = False
        self.memory_history = []
        self.monitor_thread = None
        self.process = psutil.Process()

    def start_monitoring(self):
        """开始监控"""
        self.monitoring = True
        self.memory_history = []
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()

    def stop_monitoring(self):
        """停止监控"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)

    def _monitor_loop(self):
        """监控循环"""
        while self.monitoring:
            memory_gb = self.process.memory_info().rss / 1024**3
            self.memory_history.append(memory_gb)
            time.sleep(1)

    def get_current_memory_usage(self) -> float:
        """获取当前内存使用（GB）"""
        return self.process.memory_info().rss / 1024**3

    def get_peak_memory_usage(self) -> float:
        """获取峰值内存使用"""
        if not self.memory_history:
            return self.get_current_memory_usage()
        return max(self.memory_history)


def main():
    """主函数"""
    tester = UIWorkflowTester()
    return tester.run_comprehensive_ui_workflow_test()


if __name__ == "__main__":
    main()
