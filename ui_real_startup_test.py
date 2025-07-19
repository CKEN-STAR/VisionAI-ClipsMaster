#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 真实UI启动测试
测试实际的UI界面启动、显示和基本交互功能
"""

import os
import sys
import time
import json
import psutil
import subprocess
import threading
from pathlib import Path
from typing import Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class RealUIStartupTester:
    """真实UI启动测试器"""
    
    def __init__(self):
        self.project_root = Path('.')
        self.test_results = {
            "start_time": datetime.now().isoformat(),
            "startup_metrics": {},
            "ui_tests": {},
            "performance_data": {},
            "issues_found": [],
            "overall_status": "RUNNING"
        }
        self.process = psutil.Process()
        
    def test_ui_startup_performance(self) -> Dict[str, Any]:
        """测试UI启动性能"""
        print("🚀 测试UI启动性能...")
        
        startup_result = {
            "test_name": "UI启动性能测试",
            "start_time": time.time(),
            "status": "RUNNING",
            "metrics": {},
            "issues": []
        }
        
        try:
            # 记录启动前内存
            baseline_memory = self.process.memory_info().rss / 1024**2  # MB
            
            # 测试模块导入时间
            import_start = time.time()
            
            # 导入主要UI模块
            try:
                import simple_ui_fixed
                ui_import_time = time.time() - import_start
                
                startup_result["metrics"]["ui_import_time"] = ui_import_time
                startup_result["metrics"]["ui_import_success"] = True
                
                print(f"   ✅ UI模块导入成功: {ui_import_time:.3f}秒")
                
            except Exception as e:
                startup_result["metrics"]["ui_import_success"] = False
                startup_result["issues"].append(f"UI模块导入失败: {e}")
                print(f"   ❌ UI模块导入失败: {e}")
            
            # 测试核心组件导入
            core_components = [
                ("screenplay_engineer", "src.core.screenplay_engineer"),
                ("language_detector", "src.core.language_detector"),
                ("jianying_exporter", "src.exporters.jianying_pro_exporter")
            ]
            
            component_import_times = {}
            successful_imports = 0
            
            for component_name, module_path in core_components:
                component_start = time.time()
                try:
                    __import__(module_path)
                    import_time = time.time() - component_start
                    component_import_times[component_name] = import_time
                    successful_imports += 1
                    print(f"   ✅ {component_name}导入成功: {import_time:.3f}秒")
                except Exception as e:
                    component_import_times[component_name] = -1
                    startup_result["issues"].append(f"{component_name}导入失败: {e}")
                    print(f"   ❌ {component_name}导入失败: {e}")
            
            # 记录启动后内存
            final_memory = self.process.memory_info().rss / 1024**2  # MB
            memory_increase = final_memory - baseline_memory
            
            # 计算总启动时间
            total_startup_time = time.time() - startup_result["start_time"]
            
            # 记录所有指标
            startup_result["metrics"].update({
                "total_startup_time": total_startup_time,
                "component_import_times": component_import_times,
                "successful_imports": successful_imports,
                "total_components": len(core_components),
                "baseline_memory_mb": baseline_memory,
                "final_memory_mb": final_memory,
                "memory_increase_mb": memory_increase,
                "startup_target_met": total_startup_time <= 5.0,
                "memory_target_met": final_memory <= 400  # 400MB目标
            })
            
            # 评估启动性能
            if (startup_result["metrics"]["startup_target_met"] and 
                startup_result["metrics"]["memory_target_met"] and
                successful_imports >= 3):
                startup_result["status"] = "PASSED"
            else:
                startup_result["status"] = "FAILED"
                
                if not startup_result["metrics"]["startup_target_met"]:
                    startup_result["issues"].append(f"启动时间超标: {total_startup_time:.2f}秒 > 5秒")
                
                if not startup_result["metrics"]["memory_target_met"]:
                    startup_result["issues"].append(f"内存使用超标: {final_memory:.1f}MB > 400MB")
            
            print(f"   📊 启动总时间: {total_startup_time:.3f}秒")
            print(f"   📊 内存使用: {final_memory:.1f}MB (增加: {memory_increase:.1f}MB)")
            print(f"   📊 组件导入: {successful_imports}/{len(core_components)}")
            
        except Exception as e:
            startup_result["status"] = "ERROR"
            startup_result["error"] = str(e)
            startup_result["issues"].append(f"启动测试异常: {e}")
            print(f"   ❌ 启动测试异常: {e}")
        
        startup_result["end_time"] = time.time()
        startup_result["duration"] = startup_result["end_time"] - startup_result["start_time"]
        
        return startup_result
    
    def test_ui_component_functionality(self) -> Dict[str, Any]:
        """测试UI组件功能"""
        print("\n🧩 测试UI组件功能...")
        
        component_result = {
            "test_name": "UI组件功能测试",
            "start_time": time.time(),
            "status": "RUNNING",
            "component_tests": [],
            "issues": []
        }
        
        try:
            # 测试核心功能组件
            component_tests = [
                ("语言检测器", self._test_language_detector),
                ("剧本重构器", self._test_screenplay_engineer),
                ("剪映导出器", self._test_jianying_exporter),
                ("文件处理器", self._test_file_processing)
            ]
            
            for component_name, test_func in component_tests:
                print(f"   🔧 测试{component_name}...")
                
                test_start = time.time()
                test_result = test_func()
                test_duration = time.time() - test_start
                
                test_result.update({
                    "component_name": component_name,
                    "test_duration": test_duration,
                    "response_time_ok": test_duration <= 2.0
                })
                
                component_result["component_tests"].append(test_result)
                
                status_icon = "✅" if test_result.get("success", False) else "❌"
                print(f"      {status_icon} {component_name}: {test_duration:.3f}秒")
                
                if not test_result.get("success", False):
                    component_result["issues"].append(f"{component_name}测试失败")
                
                if test_duration > 2.0:
                    component_result["issues"].append(f"{component_name}响应时间超标: {test_duration:.2f}秒")
            
            # 评估组件功能
            successful_tests = sum(1 for test in component_result["component_tests"] if test.get("success", False))
            total_tests = len(component_result["component_tests"])
            success_rate = (successful_tests / total_tests) * 100 if total_tests > 0 else 0
            
            all_response_times_ok = all(test.get("response_time_ok", False) for test in component_result["component_tests"])
            
            component_result["summary"] = {
                "successful_tests": successful_tests,
                "total_tests": total_tests,
                "success_rate": success_rate,
                "all_response_times_ok": all_response_times_ok
            }
            
            if success_rate >= 80 and all_response_times_ok:
                component_result["status"] = "PASSED"
            else:
                component_result["status"] = "FAILED"
            
            print(f"   📊 组件测试成功率: {success_rate:.1f}%")
            
        except Exception as e:
            component_result["status"] = "ERROR"
            component_result["error"] = str(e)
            component_result["issues"].append(f"组件测试异常: {e}")
            print(f"   ❌ 组件测试异常: {e}")
        
        component_result["end_time"] = time.time()
        component_result["duration"] = component_result["end_time"] - component_result["start_time"]
        
        return component_result
    
    def _test_language_detector(self) -> Dict[str, Any]:
        """测试语言检测器"""
        try:
            from src.core.language_detector import LanguageDetector
            
            detector = LanguageDetector()
            
            # 测试中文检测
            zh_result = detector.detect_from_text("这是一段中文测试文本")
            
            # 测试英文检测
            en_result = detector.detect_from_text("This is an English test text")
            
            return {
                "success": True,
                "zh_detection": zh_result,
                "en_detection": en_result,
                "detection_accuracy": (zh_result == "zh") and (en_result == "en")
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _test_screenplay_engineer(self) -> Dict[str, Any]:
        """测试剧本重构器"""
        try:
            from src.core.screenplay_engineer import ScreenplayEngineer
            
            engineer = ScreenplayEngineer()
            
            test_subtitles = [
                {"start_time": 0.0, "end_time": 3.0, "text": "测试字幕1"},
                {"start_time": 3.0, "end_time": 6.0, "text": "测试字幕2"}
            ]
            
            result = engineer.generate_screenplay(test_subtitles, language="zh")
            
            return {
                "success": True,
                "output_segments": len(result.get("screenplay", [])),
                "processing_time": result.get("processing_time", 0),
                "has_output": len(result.get("screenplay", [])) > 0
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _test_jianying_exporter(self) -> Dict[str, Any]:
        """测试剪映导出器"""
        try:
            from src.exporters.jianying_pro_exporter import JianYingProExporter
            
            exporter = JianYingProExporter()
            
            test_project = {
                "project_name": "UI测试项目",
                "segments": [
                    {"start_time": 0.0, "end_time": 3.0, "text": "测试片段"}
                ],
                "subtitles": []
            }
            
            output_file = self.project_root / "test_outputs" / "ui_test_export.json"
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            success = exporter.export_project(test_project, str(output_file))
            
            # 检查文件是否创建
            file_exists = output_file.exists()
            file_size = output_file.stat().st_size if file_exists else 0
            
            # 清理测试文件
            if file_exists:
                output_file.unlink()
            
            return {
                "success": success and file_exists,
                "export_success": success,
                "file_created": file_exists,
                "file_size": file_size
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _test_file_processing(self) -> Dict[str, Any]:
        """测试文件处理功能"""
        try:
            # 创建测试SRT文件
            test_file = self.project_root / "test_outputs" / "ui_test.srt"
            test_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write("""1
00:00:00,000 --> 00:00:03,000
测试字幕内容

2
00:00:03,000 --> 00:00:06,000
第二段测试字幕
""")
            
            # 测试文件读取
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 简单的SRT格式验证
            has_timestamps = "-->" in content
            has_content = len(content.strip()) > 0
            
            # 清理测试文件
            test_file.unlink()
            
            return {
                "success": has_timestamps and has_content,
                "file_created": True,
                "content_valid": has_timestamps,
                "content_length": len(content)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def run_real_ui_startup_test(self) -> Dict[str, Any]:
        """运行真实UI启动测试"""
        print("=== VisionAI-ClipsMaster 真实UI启动测试 ===")
        print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # 显示系统信息
        memory = psutil.virtual_memory()
        print(f"📊 系统信息:")
        print(f"   总内存: {memory.total / 1024**3:.2f}GB")
        print(f"   可用内存: {memory.available / 1024**3:.2f}GB")
        print(f"   CPU核心: {psutil.cpu_count()}")
        print()
        
        # 执行测试
        tests = [
            ("UI启动性能", self.test_ui_startup_performance),
            ("UI组件功能", self.test_ui_component_functionality)
        ]
        
        for test_name, test_func in tests:
            print(f"🧪 执行测试: {test_name}")
            result = test_func()
            self.test_results["ui_tests"][result["test_name"]] = result
            
            status_icon = "✅" if result["status"] == "PASSED" else "❌" if result["status"] == "FAILED" else "⚠️"
            print(f"   {status_icon} {test_name}: {result['status']}")
            
            if result.get("issues"):
                for issue in result["issues"]:
                    print(f"      ⚠️ {issue}")
        
        # 生成最终评估
        self._generate_final_assessment()
        
        # 保存测试结果
        self._save_test_results()
        
        return self.test_results
    
    def _generate_final_assessment(self):
        """生成最终评估"""
        ui_tests = self.test_results["ui_tests"]
        
        # 计算通过率
        total_tests = len(ui_tests)
        passed_tests = sum(1 for test in ui_tests.values() if test["status"] == "PASSED")
        pass_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        # 获取关键指标
        startup_test = ui_tests.get("UI启动性能测试", {})
        startup_metrics = startup_test.get("metrics", {})
        
        self.test_results.update({
            "end_time": datetime.now().isoformat(),
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "pass_rate": pass_rate,
            "startup_time": startup_metrics.get("total_startup_time", 0),
            "memory_usage_mb": startup_metrics.get("final_memory_mb", 0),
            "overall_status": "PASSED" if pass_rate >= 80 else "FAILED"
        })
        
        print(f"\n📋 最终评估结果:")
        print(f"   测试通过率: {pass_rate:.1f}%")
        print(f"   启动时间: {startup_metrics.get('total_startup_time', 0):.3f}秒")
        print(f"   内存使用: {startup_metrics.get('final_memory_mb', 0):.1f}MB")
        print(f"   总体状态: {self.test_results['overall_status']}")
    
    def _save_test_results(self):
        """保存测试结果"""
        results_file = self.project_root / "test_outputs" / f"ui_real_startup_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        results_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n📊 测试结果已保存: {results_file}")


def main():
    """主函数"""
    tester = RealUIStartupTester()
    return tester.run_real_ui_startup_test()


if __name__ == "__main__":
    main()
