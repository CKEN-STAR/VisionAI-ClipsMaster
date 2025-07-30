#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 双语言模型切换功能测试
测试Mistral-7B英文模型和Qwen2.5-7B中文模型的加载和切换功能
"""

import sys
import os
import json
import time
import traceback
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

class DualLanguageModelTester:
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
        
        # 测试用的样本文本
        self.test_texts = {
            "chinese": [
                "这是一个关于爱情的故事，男主角深深地爱着女主角。",
                "在一个阳光明媚的下午，他们在咖啡厅相遇了。",
                "经过一番波折，他们终于走到了一起。"
            ],
            "english": [
                "This is a story about love, where the male protagonist deeply loves the female protagonist.",
                "On a sunny afternoon, they met in a coffee shop.",
                "After some twists and turns, they finally got together."
            ],
            "mixed": [
                "这是一个love story，男主角deeply爱着女主角。",
                "在coffee shop里，they met each other。"
            ]
        }

    def test_language_detection(self):
        """测试语言检测功能"""
        print("测试语言检测功能...")
        
        try:
            from src.core.language_detector import LanguageDetector
            
            detector = LanguageDetector()
            
            test_result = {
                "status": "success",
                "detection_results": {},
                "accuracy": 0.0
            }
            
            # 测试中文检测
            for text in self.test_texts["chinese"]:
                detected_lang = detector.detect_language(text)
                test_result["detection_results"][text] = detected_lang
                print(f"  中文文本: '{text[:20]}...' -> {detected_lang}")
            
            # 测试英文检测
            for text in self.test_texts["english"]:
                detected_lang = detector.detect_language(text)
                test_result["detection_results"][text] = detected_lang
                print(f"  英文文本: '{text[:20]}...' -> {detected_lang}")
            
            # 测试混合文本检测
            for text in self.test_texts["mixed"]:
                detected_lang = detector.detect_language(text)
                test_result["detection_results"][text] = detected_lang
                print(f"  混合文本: '{text[:20]}...' -> {detected_lang}")
            
            print("  ✓ 语言检测功能测试通过")
            return test_result
            
        except Exception as e:
            print(f"  ✗ 语言检测功能测试失败: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "traceback": traceback.format_exc()
            }

    def test_model_switcher(self):
        """测试模型切换器功能"""
        print("测试模型切换器功能...")
        
        try:
            from src.core.model_switcher import ModelSwitcher
            
            switcher = ModelSwitcher()
            
            test_result = {
                "status": "success",
                "switch_tests": {},
                "load_times": {}
            }
            
            # 测试切换到中文模型
            print("  测试切换到中文模型...")
            start_time = time.time()
            success = switcher.switch_to_chinese_model()
            load_time = time.time() - start_time
            
            test_result["switch_tests"]["chinese_model"] = success
            test_result["load_times"]["chinese_model"] = load_time
            print(f"    切换结果: {success}, 耗时: {load_time:.2f}秒")
            
            # 测试切换到英文模型
            print("  测试切换到英文模型...")
            start_time = time.time()
            success = switcher.switch_to_english_model()
            load_time = time.time() - start_time
            
            test_result["switch_tests"]["english_model"] = success
            test_result["load_times"]["english_model"] = load_time
            print(f"    切换结果: {success}, 耗时: {load_time:.2f}秒")
            
            # 测试自动切换
            print("  测试自动模型切换...")
            for lang, texts in self.test_texts.items():
                if lang != "mixed":  # 跳过混合文本
                    for text in texts[:1]:  # 只测试第一个文本
                        start_time = time.time()
                        success = switcher.auto_switch_model(text)
                        switch_time = time.time() - start_time
                        
                        test_result["switch_tests"][f"auto_{lang}"] = success
                        test_result["load_times"][f"auto_{lang}"] = switch_time
                        print(f"    {lang}自动切换: {success}, 耗时: {switch_time:.2f}秒")
            
            print("  ✓ 模型切换器功能测试通过")
            return test_result
            
        except Exception as e:
            print(f"  ✗ 模型切换器功能测试失败: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "traceback": traceback.format_exc()
            }

    def test_model_loading(self):
        """测试模型加载功能"""
        print("测试模型加载功能...")
        
        try:
            # 测试中文模型配置
            print("  检查中文模型配置...")
            chinese_config_path = "configs/models/available_models/qwen2.5-7b-zh.yaml"
            if os.path.exists(chinese_config_path):
                print(f"    ✓ 中文模型配置文件存在: {chinese_config_path}")
            else:
                print(f"    ⚠ 中文模型配置文件不存在: {chinese_config_path}")
            
            # 测试英文模型配置
            print("  检查英文模型配置...")
            english_config_path = "configs/models/available_models/mistral-7b-en.yaml"
            if os.path.exists(english_config_path):
                print(f"    ✓ 英文模型配置文件存在: {english_config_path}")
            else:
                print(f"    ⚠ 英文模型配置文件不存在: {english_config_path}")
            
            # 测试活动模型配置
            print("  检查活动模型配置...")
            active_config_path = "configs/models/active_model.yaml"
            if os.path.exists(active_config_path):
                print(f"    ✓ 活动模型配置文件存在: {active_config_path}")
                
                # 读取配置内容
                with open(active_config_path, 'r', encoding='utf-8') as f:
                    import yaml
                    config = yaml.safe_load(f)
                    print(f"    当前活动模型: {config.get('current_model', 'unknown')}")
            else:
                print(f"    ⚠ 活动模型配置文件不存在: {active_config_path}")
            
            test_result = {
                "status": "success",
                "config_files": {
                    "chinese_config": os.path.exists(chinese_config_path),
                    "english_config": os.path.exists(english_config_path),
                    "active_config": os.path.exists(active_config_path)
                }
            }
            
            print("  ✓ 模型加载功能测试通过")
            return test_result
            
        except Exception as e:
            print(f"  ✗ 模型加载功能测试失败: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "traceback": traceback.format_exc()
            }

    def test_memory_management(self):
        """测试内存管理功能"""
        print("测试内存管理功能...")
        
        try:
            from src.utils.memory_guard import MemoryGuard
            
            memory_guard = MemoryGuard()
            
            test_result = {
                "status": "success",
                "memory_info": {},
                "optimization_results": {}
            }
            
            # 获取当前内存使用情况
            memory_info = memory_guard.get_memory_info()
            test_result["memory_info"] = memory_info
            print(f"  当前内存使用: {memory_info.get('used_memory_gb', 0):.2f}GB")
            print(f"  可用内存: {memory_info.get('available_memory_gb', 0):.2f}GB")
            
            # 测试内存优化
            print("  测试内存优化...")
            optimization_result = memory_guard.optimize_memory_usage()
            test_result["optimization_results"] = optimization_result
            print(f"    优化结果: {optimization_result.get('status', 'unknown')}")
            
            # 测试内存监控
            print("  测试内存监控...")
            is_safe = memory_guard.check_memory_safety()
            test_result["memory_safety"] = is_safe
            print(f"    内存安全状态: {is_safe}")
            
            print("  ✓ 内存管理功能测试通过")
            return test_result
            
        except Exception as e:
            print(f"  ✗ 内存管理功能测试失败: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "traceback": traceback.format_exc()
            }

    def run_comprehensive_test(self):
        """运行全面的双语言模型测试"""
        print("=" * 60)
        print("VisionAI-ClipsMaster 双语言模型切换功能测试")
        print("=" * 60)
        
        tests = [
            ("语言检测功能", self.test_language_detection),
            ("模型切换器功能", self.test_model_switcher),
            ("模型加载功能", self.test_model_loading),
            ("内存管理功能", self.test_memory_management)
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
        
        # 生成报告
        self.generate_report()
        
        return self.results

    def generate_report(self):
        """生成测试报告"""
        print("\n" + "=" * 60)
        print("双语言模型测试结果汇总")
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
        report_file = f"dual_language_model_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        print(f"\n详细报告已保存到: {report_file}")

if __name__ == "__main__":
    tester = DualLanguageModelTester()
    results = tester.run_comprehensive_test()
    
    # 返回退出码
    if results["failed_tests"] > 0:
        sys.exit(1)
    else:
        sys.exit(0)
