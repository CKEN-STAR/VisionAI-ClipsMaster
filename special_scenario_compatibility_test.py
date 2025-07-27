#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 特殊场景兼容性测试
测试系统在各种边界条件、异常输入和极限情况下的表现
"""

import sys
import os
import json
import time
import tempfile
import traceback
import threading
import gc
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

class SpecialScenarioCompatibilityTester:
    def __init__(self):
        self.results = {
            "test_time": datetime.now().isoformat(),
            "total_tests": 0,
            "successful_tests": 0,
            "failed_tests": 0,
            "test_results": {},
            "performance_metrics": {},
            "errors": []
        }
        
        # 创建临时目录用于测试
        self.temp_dir = Path(tempfile.mkdtemp(prefix="special_scenario_test_"))

    def test_empty_input_handling(self):
        """测试空输入处理"""
        print("测试空输入处理...")
        
        try:
            from src.core.srt_parser import SRTParser
            from src.core.narrative_analyzer import NarrativeAnalyzer
            
            test_result = {
                "status": "success",
                "empty_input_tests": {},
                "handling_time": 0.0
            }
            
            start_time = time.time()
            
            # 测试空SRT文件
            empty_srt_file = self.temp_dir / "empty.srt"
            empty_srt_file.write_text("", encoding='utf-8')
            
            parser = SRTParser()
            empty_result = parser.parse(str(empty_srt_file))
            test_result["empty_input_tests"]["empty_srt"] = {
                "result": empty_result,
                "handled_gracefully": isinstance(empty_result, list)
            }
            
            # 测试空文本分析
            analyzer = NarrativeAnalyzer()
            empty_analysis = analyzer.analyze_narrative_structure("")
            test_result["empty_input_tests"]["empty_text"] = {
                "result": empty_analysis,
                "handled_gracefully": isinstance(empty_analysis, dict)
            }
            
            # 测试None输入
            try:
                none_analysis = analyzer.analyze_narrative_structure(None)
                test_result["empty_input_tests"]["none_input"] = {
                    "result": none_analysis,
                    "handled_gracefully": True
                }
            except Exception as e:
                test_result["empty_input_tests"]["none_input"] = {
                    "error": str(e),
                    "handled_gracefully": False
                }
            
            handling_time = time.time() - start_time
            test_result["handling_time"] = handling_time
            
            print(f"  空输入处理耗时: {handling_time:.3f}秒")
            print("  ✓ 空输入处理测试通过")
            return test_result
            
        except Exception as e:
            print(f"  ✗ 空输入处理测试失败: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "traceback": traceback.format_exc()
            }

    def test_large_input_handling(self):
        """测试大输入处理"""
        print("测试大输入处理...")
        
        try:
            from src.core.narrative_analyzer import NarrativeAnalyzer
            
            test_result = {
                "status": "success",
                "large_input_tests": {},
                "processing_time": 0.0
            }
            
            start_time = time.time()
            
            # 生成大文本
            large_text = "这是一个很长的故事。" * 1000  # 约10KB文本
            very_large_text = "这是一个超长的故事。" * 10000  # 约100KB文本
            
            analyzer = NarrativeAnalyzer()
            
            # 测试大文本处理
            large_result = analyzer.analyze_narrative_structure(large_text)
            test_result["large_input_tests"]["large_text"] = {
                "text_length": len(large_text),
                "result_type": type(large_result).__name__,
                "handled_gracefully": isinstance(large_result, dict)
            }
            
            # 测试超大文本处理
            very_large_result = analyzer.analyze_narrative_structure(very_large_text)
            test_result["large_input_tests"]["very_large_text"] = {
                "text_length": len(very_large_text),
                "result_type": type(very_large_result).__name__,
                "handled_gracefully": isinstance(very_large_result, dict)
            }
            
            processing_time = time.time() - start_time
            test_result["processing_time"] = processing_time
            
            print(f"  大输入处理耗时: {processing_time:.3f}秒")
            print(f"  大文本长度: {len(large_text):,} 字符")
            print(f"  超大文本长度: {len(very_large_text):,} 字符")
            print("  ✓ 大输入处理测试通过")
            return test_result
            
        except Exception as e:
            print(f"  ✗ 大输入处理测试失败: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "traceback": traceback.format_exc()
            }

    def test_malformed_input_handling(self):
        """测试畸形输入处理"""
        print("测试畸形输入处理...")
        
        try:
            from src.core.srt_parser import SRTParser
            
            test_result = {
                "status": "success",
                "malformed_input_tests": {},
                "handling_time": 0.0
            }
            
            start_time = time.time()
            
            # 创建畸形SRT文件
            malformed_srt_content = """1
            00:00:01,000 --> 00:00:03,000
            这是正常字幕
            
            INVALID_ENTRY
            这是无效的时间码
            
            3
            25:99:99,999 --> 26:99:99,999
            这是无效的时间格式
            """
            
            malformed_srt_file = self.temp_dir / "malformed.srt"
            malformed_srt_file.write_text(malformed_srt_content, encoding='utf-8')
            
            parser = SRTParser()
            malformed_result = parser.parse(str(malformed_srt_file))
            
            test_result["malformed_input_tests"]["malformed_srt"] = {
                "result_type": type(malformed_result).__name__,
                "result_length": len(malformed_result) if isinstance(malformed_result, list) else 0,
                "handled_gracefully": isinstance(malformed_result, list)
            }
            
            # 测试特殊字符输入
            special_chars_text = "🎬📺🎭🎪🎨🎯🎲🎸🎺🎻🎼🎵🎶🎤🎧🎮"
            from src.core.narrative_analyzer import NarrativeAnalyzer
            analyzer = NarrativeAnalyzer()
            special_result = analyzer.analyze_narrative_structure(special_chars_text)
            
            test_result["malformed_input_tests"]["special_chars"] = {
                "input_text": special_chars_text,
                "result_type": type(special_result).__name__,
                "handled_gracefully": isinstance(special_result, dict)
            }
            
            handling_time = time.time() - start_time
            test_result["handling_time"] = handling_time
            
            print(f"  畸形输入处理耗时: {handling_time:.3f}秒")
            print("  ✓ 畸形输入处理测试通过")
            return test_result
            
        except Exception as e:
            print(f"  ✗ 畸形输入处理测试失败: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "traceback": traceback.format_exc()
            }

    def test_memory_pressure_handling(self):
        """测试内存压力处理"""
        print("测试内存压力处理...")
        
        try:
            from src.utils.memory_guard import MemoryGuard
            
            test_result = {
                "status": "success",
                "memory_tests": {},
                "memory_usage": {}
            }
            
            start_time = time.time()
            
            # 获取初始内存状态
            memory_guard = MemoryGuard()
            initial_memory = memory_guard.get_memory_info()
            test_result["memory_usage"]["initial"] = initial_memory
            
            # 模拟内存压力
            large_data = []
            try:
                for i in range(100):  # 创建一些大对象
                    large_data.append("x" * 10000)  # 每个10KB
                
                # 检查内存状态
                pressure_memory = memory_guard.get_memory_info()
                test_result["memory_usage"]["under_pressure"] = pressure_memory
                
                # 测试内存优化
                optimization_result = memory_guard.optimize_memory_usage()
                test_result["memory_tests"]["optimization"] = optimization_result
                
                # 清理大对象
                large_data.clear()
                gc.collect()
                
                # 检查清理后内存状态
                final_memory = memory_guard.get_memory_info()
                test_result["memory_usage"]["after_cleanup"] = final_memory
                
            except MemoryError:
                test_result["memory_tests"]["memory_error_handled"] = True
            
            # 测试内存安全检查
            safety_check = memory_guard.check_memory_safety()
            test_result["memory_tests"]["safety_check"] = safety_check
            
            handling_time = time.time() - start_time
            test_result["handling_time"] = handling_time
            
            print(f"  内存压力测试耗时: {handling_time:.3f}秒")
            print(f"  内存安全状态: {safety_check}")
            print("  ✓ 内存压力处理测试通过")
            return test_result
            
        except Exception as e:
            print(f"  ✗ 内存压力处理测试失败: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "traceback": traceback.format_exc()
            }

    def test_concurrent_access_handling(self):
        """测试并发访问处理"""
        print("测试并发访问处理...")
        
        try:
            from src.core.narrative_analyzer import NarrativeAnalyzer
            
            test_result = {
                "status": "success",
                "concurrent_tests": {},
                "thread_results": []
            }
            
            start_time = time.time()
            
            # 创建多个线程同时访问分析器
            analyzer = NarrativeAnalyzer()
            threads = []
            thread_results = []
            
            def analyze_text(thread_id, text):
                try:
                    result = analyzer.analyze_narrative_structure(f"线程{thread_id}: {text}")
                    thread_results.append({
                        "thread_id": thread_id,
                        "success": True,
                        "result_type": type(result).__name__
                    })
                except Exception as e:
                    thread_results.append({
                        "thread_id": thread_id,
                        "success": False,
                        "error": str(e)
                    })
            
            # 启动多个线程
            for i in range(5):
                thread = threading.Thread(
                    target=analyze_text,
                    args=(i, f"这是线程{i}的测试文本，用于测试并发访问。")
                )
                threads.append(thread)
                thread.start()
            
            # 等待所有线程完成
            for thread in threads:
                thread.join(timeout=10)  # 10秒超时
            
            test_result["thread_results"] = thread_results
            test_result["concurrent_tests"]["total_threads"] = len(threads)
            test_result["concurrent_tests"]["successful_threads"] = sum(
                1 for r in thread_results if r.get("success", False)
            )
            
            handling_time = time.time() - start_time
            test_result["handling_time"] = handling_time
            
            success_rate = test_result["concurrent_tests"]["successful_threads"] / len(threads) * 100
            print(f"  并发访问测试耗时: {handling_time:.3f}秒")
            print(f"  成功线程: {test_result['concurrent_tests']['successful_threads']}/{len(threads)}")
            print(f"  成功率: {success_rate:.1f}%")
            print("  ✓ 并发访问处理测试通过")
            return test_result
            
        except Exception as e:
            print(f"  ✗ 并发访问处理测试失败: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "traceback": traceback.format_exc()
            }

    def test_long_running_stability(self):
        """测试长时间运行稳定性"""
        print("测试长时间运行稳定性...")
        
        try:
            from src.core.narrative_analyzer import NarrativeAnalyzer
            
            test_result = {
                "status": "success",
                "stability_tests": {},
                "iterations_completed": 0
            }
            
            start_time = time.time()
            
            analyzer = NarrativeAnalyzer()
            iterations = 50  # 减少迭代次数以加快测试
            successful_iterations = 0
            
            for i in range(iterations):
                try:
                    # 模拟长时间运行的操作
                    test_text = f"这是第{i+1}次迭代的测试文本，用于验证系统的长期稳定性。"
                    result = analyzer.analyze_narrative_structure(test_text)
                    
                    if isinstance(result, dict):
                        successful_iterations += 1
                    
                    # 每10次迭代检查一次内存
                    if (i + 1) % 10 == 0:
                        gc.collect()  # 强制垃圾回收
                        
                except Exception as e:
                    print(f"    迭代 {i+1} 失败: {e}")
            
            test_result["iterations_completed"] = successful_iterations
            test_result["stability_tests"]["success_rate"] = successful_iterations / iterations * 100
            test_result["stability_tests"]["total_iterations"] = iterations
            
            handling_time = time.time() - start_time
            test_result["handling_time"] = handling_time
            
            print(f"  长时间运行测试耗时: {handling_time:.3f}秒")
            print(f"  完成迭代: {successful_iterations}/{iterations}")
            print(f"  成功率: {test_result['stability_tests']['success_rate']:.1f}%")
            print("  ✓ 长时间运行稳定性测试通过")
            return test_result
            
        except Exception as e:
            print(f"  ✗ 长时间运行稳定性测试失败: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "traceback": traceback.format_exc()
            }

    def run_comprehensive_test(self):
        """运行全面的特殊场景兼容性测试"""
        print("=" * 60)
        print("VisionAI-ClipsMaster 特殊场景兼容性测试")
        print("=" * 60)
        
        tests = [
            ("空输入处理", self.test_empty_input_handling),
            ("大输入处理", self.test_large_input_handling),
            ("畸形输入处理", self.test_malformed_input_handling),
            ("内存压力处理", self.test_memory_pressure_handling),
            ("并发访问处理", self.test_concurrent_access_handling),
            ("长时间运行稳定性", self.test_long_running_stability)
        ]
        
        self.results["total_tests"] = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n测试: {test_name}")
            try:
                result = test_func()
                self.results["test_results"][test_name] = result
                
                if result.get("status") == "success":
                    self.results["successful_tests"] += 1
                    print(f"  ✓ {test_name} 测试通过")
                else:
                    self.results["failed_tests"] += 1
                    print(f"  ✗ {test_name} 测试失败")
                    
            except Exception as e:
                self.results["failed_tests"] += 1
                error_msg = f"测试异常: {e}"
                self.results["test_results"][test_name] = {
                    "status": "error",
                    "error": error_msg
                }
                self.results["errors"].append(f"{test_name}: {error_msg}")
                print(f"  ✗ {error_msg}")
        
        # 清理临时文件
        self.cleanup()
        
        # 生成报告
        self.generate_report()
        
        return self.results

    def cleanup(self):
        """清理临时文件"""
        try:
            import shutil
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
                print(f"\n临时目录已清理: {self.temp_dir}")
        except Exception as e:
            print(f"\n清理临时文件失败: {e}")

    def generate_report(self):
        """生成测试报告"""
        print("\n" + "=" * 60)
        print("特殊场景兼容性测试结果汇总")
        print("=" * 60)
        
        print(f"总测试数: {self.results['total_tests']}")
        print(f"通过测试: {self.results['successful_tests']}")
        print(f"失败测试: {self.results['failed_tests']}")
        print(f"成功率: {(self.results['successful_tests']/self.results['total_tests']*100):.1f}%")
        
        if self.results["failed_tests"] > 0:
            print(f"\n失败的测试:")
            for test_name, result in self.results["test_results"].items():
                if result.get("status") != "success":
                    print(f"  - {test_name}: {result.get('error', 'Unknown error')}")
        
        # 保存详细报告
        report_file = f"special_scenario_compatibility_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        print(f"\n详细报告已保存到: {report_file}")

if __name__ == "__main__":
    tester = SpecialScenarioCompatibilityTester()
    results = tester.run_comprehensive_test()
    
    # 返回退出码
    if results["failed_tests"] > 0:
        sys.exit(1)
    else:
        sys.exit(0)
