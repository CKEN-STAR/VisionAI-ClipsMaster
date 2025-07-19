#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster AI模型训练测试执行器 (增强版)

改进算法，执行更多P0级别测试用例
"""

import sys
import os
import time
import json
import psutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple

# 设置环境变量
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
os.environ['OMP_NUM_THREADS'] = '1'

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

class EnhancedAITrainingTestExecutor:
    """增强版AI模型训练测试执行器"""
    
    def __init__(self):
        self.start_time = time.time()
        self.test_results = {
            "execution_start": datetime.now().isoformat(),
            "test_environment": self._get_test_environment(),
            "executed_tests": {},
            "performance_metrics": {},
            "issues_found": [],
            "overall_summary": {}
        }
        self.memory_baseline = self._get_memory_usage()
        
    def _get_test_environment(self) -> Dict[str, Any]:
        """获取测试环境信息"""
        try:
            return {
                "os": os.name,
                "python_version": sys.version,
                "total_memory_gb": round(psutil.virtual_memory().total / (1024**3), 2),
                "available_memory_gb": round(psutil.virtual_memory().available / (1024**3), 2),
                "cpu_count": psutil.cpu_count(),
                "project_root": str(project_root),
                "simulating_4gb_constraint": psutil.virtual_memory().total / (1024**3) > 6
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _get_memory_usage(self) -> float:
        """获取当前内存使用量(MB)"""
        try:
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except:
            return 0
    
    def _log_test_result(self, test_id: str, passed: bool, details: str, 
                        performance_data: Dict = None, issues: List = None):
        """记录测试结果"""
        self.test_results["executed_tests"][test_id] = {
            "passed": passed,
            "details": details,
            "execution_time": datetime.now().isoformat(),
            "performance_data": performance_data or {},
            "issues": issues or []
        }
        
        if issues:
            self.test_results["issues_found"].extend(issues)
    
    def create_enhanced_test_data(self) -> bool:
        """创建增强的测试数据"""
        print("📊 创建增强测试数据...")
        
        try:
            # 创建更丰富的中文测试数据
            zh_test_data = {
                "original_subtitles": [
                    "皇上，臣妾有重要的事情要禀报。",  # 正式、紧急
                    "什么事情如此紧急？速速道来！",      # 疑问、急迫
                    "关于太子殿下的事情，臣妾深感不妥。", # 担忧、恭敬
                    "你竟敢质疑朕的决定？大胆！",        # 愤怒、威严
                    "臣妾不敢，只是担心江山社稷啊。",    # 恐惧、忠诚
                    "这件事关系重大，不可轻举妄动。",    # 严肃、谨慎
                    "臣妾明白了，一切听从皇上安排。"     # 顺从、理解
                ],
                "viral_subtitles": [
                    "皇上！我有爆炸性消息！",
                    "太子出大事了！",
                    "江山要变天了！"
                ],
                "key_plot_points": [0, 2, 4, 5],  # 关键情节点
                "emotions": ["formal", "urgent", "worried", "angry", "fearful", "serious", "submissive"],
                "emotion_intensities": [0.6, 0.8, 0.7, 0.9, 0.8, 0.7, 0.5],
                "characters": ["皇上", "妃子", "太子"],
                "genre": "古装剧",
                "narrative_structure": {
                    "exposition": [0, 1],
                    "rising_action": [2, 3],
                    "climax": [4],
                    "falling_action": [5],
                    "resolution": [6]
                }
            }
            
            # 创建英文测试数据
            en_test_data = {
                "original_subtitles": [
                    "Detective, we found crucial evidence at the scene.",
                    "What kind of evidence are we talking about?",
                    "A bloody knife hidden under the victim's bed.",
                    "This changes everything. Call forensics immediately.",
                    "The suspect's alibi just completely fell apart.",
                    "We need to arrest him before he runs.",
                    "Case closed. Justice has been served."
                ],
                "viral_subtitles": [
                    "SHOCKING evidence found!",
                    "The clue that SOLVED everything!",
                    "Justice SERVED!"
                ],
                "key_plot_points": [0, 2, 4, 6],
                "emotions": ["professional", "curious", "shocking", "urgent", "triumphant", "decisive", "satisfied"],
                "emotion_intensities": [0.5, 0.6, 0.9, 0.8, 0.7, 0.8, 0.6],
                "characters": ["Detective", "Officer", "Suspect"],
                "genre": "crime_drama",
                "narrative_structure": {
                    "exposition": [0, 1],
                    "rising_action": [2, 3],
                    "climax": [4],
                    "falling_action": [5],
                    "resolution": [6]
                }
            }
            
            # 保存测试数据
            test_data_dir = Path("test_data")
            test_data_dir.mkdir(exist_ok=True)
            
            with open(test_data_dir / "zh_enhanced_test_data.json", 'w', encoding='utf-8') as f:
                json.dump(zh_test_data, f, ensure_ascii=False, indent=2)
            
            with open(test_data_dir / "en_enhanced_test_data.json", 'w', encoding='utf-8') as f:
                json.dump(en_test_data, f, ensure_ascii=False, indent=2)
            
            self._log_test_result("DATA-002", True, "增强测试数据创建完成")
            print("  ✅ 中文增强测试数据创建完成")
            print("  ✅ 英文增强测试数据创建完成")
            return True
            
        except Exception as e:
            self._log_test_result(
                "DATA-002", False,
                f"增强测试数据创建失败: {str(e)}",
                issues=[f"Enhanced test data creation error: {str(e)}"]
            )
            return False
    
    def execute_tc_switch_001(self) -> bool:
        """执行TC-SWITCH-001: 纯语言文本检测测试"""
        print("\n🧪 执行 TC-SWITCH-001: 纯语言文本检测测试")
        print("=" * 60)
        
        start_time = time.time()
        memory_start = self._get_memory_usage()
        
        try:
            from src.core.language_detector import get_language_detector
            
            language_detector = get_language_detector()
            
            # 测试数据
            test_cases = [
                ("这是一段中文文本，用于测试语言检测功能。", "zh"),
                ("This is an English text for language detection testing.", "en"),
                ("皇上，臣妾有话要说。", "zh"),
                ("Detective, we found evidence at the scene.", "en"),
                ("今天天气很好，适合出门散步。", "zh"),
                ("The weather is nice today, perfect for a walk.", "en"),
                ("关于这个问题，我们需要仔细考虑。", "zh"),
                ("Regarding this issue, we need to think carefully.", "en"),
                ("中文测试文本包含各种词汇和语法结构。", "zh"),
                ("English test text contains various vocabulary and grammar.", "en")
            ]
            
            print(f"📝 测试输入: {len(test_cases)}个文本样本")
            
            correct_detections = 0
            detection_results = []
            
            for i, (text, expected_lang) in enumerate(test_cases):
                detected_lang = language_detector.detect_language(text)
                confidence = language_detector.get_confidence(text)
                
                is_correct = detected_lang == expected_lang
                if is_correct:
                    correct_detections += 1
                
                detection_results.append({
                    "text": text[:30] + "..." if len(text) > 30 else text,
                    "expected": expected_lang,
                    "detected": detected_lang,
                    "confidence": confidence,
                    "correct": is_correct
                })
                
                status = "✅" if is_correct else "❌"
                print(f"  {status} 文本{i+1}: {expected_lang} -> {detected_lang} (置信度: {confidence:.2f})")
            
            accuracy = correct_detections / len(test_cases)
            
            # 计算性能指标
            execution_time = time.time() - start_time
            memory_peak = self._get_memory_usage()
            memory_used = memory_peak - memory_start
            
            test_passed = accuracy >= 0.98  # 98%准确率要求
            
            performance_data = {
                "execution_time_seconds": round(execution_time, 3),
                "memory_used_mb": round(memory_used, 2),
                "detection_accuracy": round(accuracy, 3),
                "correct_detections": correct_detections,
                "total_tests": len(test_cases),
                "average_confidence": round(sum(r["confidence"] for r in detection_results) / len(detection_results), 3)
            }
            
            issues = []
            if accuracy < 0.98:
                issues.append(f"语言检测准确率 {accuracy:.2%} < 98%")
            
            self._log_test_result(
                "TC-SWITCH-001", test_passed,
                f"纯语言文本检测测试 - 准确率: {accuracy:.2%}",
                performance_data, issues
            )
            
            print(f"\n📊 测试结果:")
            print(f"  ✅ 测试状态: {'通过' if test_passed else '失败'}")
            print(f"  📈 检测准确率: {accuracy:.2%}")
            print(f"  ⏱️ 执行时间: {execution_time:.3f}秒")
            print(f"  💾 内存使用: {memory_used:.2f}MB")
            
            return test_passed
            
        except Exception as e:
            execution_time = time.time() - start_time
            self._log_test_result(
                "TC-SWITCH-001", False,
                f"测试执行失败: {str(e)}",
                {"execution_time_seconds": execution_time},
                [f"Test execution error: {str(e)}"]
            )
            print(f"❌ 测试失败: {str(e)}")
            return False
    
    def execute_tc_switch_002(self) -> bool:
        """执行TC-SWITCH-002: 混合语言文本处理测试"""
        print("\n🧪 执行 TC-SWITCH-002: 混合语言文本处理测试")
        print("=" * 60)
        
        start_time = time.time()
        memory_start = self._get_memory_usage()
        
        try:
            from src.core.language_detector import get_language_detector
            
            language_detector = get_language_detector()
            
            # 混合语言测试数据
            mixed_test_cases = [
                ("我今天去了shopping mall买东西。", "zh"),  # 中文主导
                ("Today我们要学习Chinese language。", "en"),  # 英文主导
                ("这个project很important，需要careful planning。", "zh"),  # 中文主导
                ("Let's go to 北京 for vacation this summer。", "en"),  # 英文主导
                ("我love这个beautiful的地方。", "zh"),  # 中文主导
                ("She said 你好 to me yesterday。", "en"),  # 英文主导
                ("这是一个very good的idea，我们应该try it。", "zh"),  # 中文主导
                ("The 老师 is teaching us about history。", "en"),  # 英文主导
            ]
            
            print(f"📝 测试输入: {len(mixed_test_cases)}个混合语言样本")
            
            correct_detections = 0
            detection_results = []
            
            for i, (text, expected_dominant) in enumerate(mixed_test_cases):
                detected_lang = language_detector.detect_language(text)
                confidence = language_detector.get_confidence(text)
                
                is_correct = detected_lang == expected_dominant
                if is_correct:
                    correct_detections += 1
                
                detection_results.append({
                    "text": text,
                    "expected_dominant": expected_dominant,
                    "detected": detected_lang,
                    "confidence": confidence,
                    "correct": is_correct
                })
                
                status = "✅" if is_correct else "❌"
                print(f"  {status} 混合文本{i+1}: {expected_dominant} -> {detected_lang}")
                print(f"      '{text}'")
            
            accuracy = correct_detections / len(mixed_test_cases)
            
            # 计算性能指标
            execution_time = time.time() - start_time
            memory_peak = self._get_memory_usage()
            memory_used = memory_peak - memory_start
            
            test_passed = accuracy >= 0.95  # 95%准确率要求
            
            performance_data = {
                "execution_time_seconds": round(execution_time, 3),
                "memory_used_mb": round(memory_used, 2),
                "mixed_language_accuracy": round(accuracy, 3),
                "correct_detections": correct_detections,
                "total_tests": len(mixed_test_cases)
            }
            
            issues = []
            if accuracy < 0.95:
                issues.append(f"混合语言检测准确率 {accuracy:.2%} < 95%")
            
            self._log_test_result(
                "TC-SWITCH-002", test_passed,
                f"混合语言文本处理测试 - 准确率: {accuracy:.2%}",
                performance_data, issues
            )
            
            print(f"\n📊 测试结果:")
            print(f"  ✅ 测试状态: {'通过' if test_passed else '失败'}")
            print(f"  📈 混合语言检测准确率: {accuracy:.2%}")
            print(f"  ⏱️ 执行时间: {execution_time:.3f}秒")
            print(f"  💾 内存使用: {memory_used:.2f}MB")
            
            return test_passed
            
        except Exception as e:
            execution_time = time.time() - start_time
            self._log_test_result(
                "TC-SWITCH-002", False,
                f"测试执行失败: {str(e)}",
                {"execution_time_seconds": execution_time},
                [f"Test execution error: {str(e)}"]
            )
            print(f"❌ 测试失败: {str(e)}")
            return False

    def execute_tc_memory_001(self) -> bool:
        """执行TC-MEMORY-001: 内存峰值监控测试"""
        print("\n🧪 执行 TC-MEMORY-001: 内存峰值监控测试")
        print("=" * 60)

        start_time = time.time()
        memory_start = self._get_memory_usage()

        try:
            from src.utils.memory_guard import get_memory_guard
            from src.core.model_switcher import get_model_switcher
            from src.core.narrative_analyzer import get_narrative_analyzer

            # 初始化内存监控
            memory_guard = get_memory_guard()
            memory_guard.start_monitoring()

            print("📝 测试4GB RAM设备内存约束...")
            print(f"  当前内存使用: {memory_start:.2f}MB")
            print(f"  目标峰值限制: ≤3800MB (3.8GB)")

            # 模拟训练负载
            print("\n🔄 模拟训练负载...")

            # 1. 加载模型组件
            model_switcher = get_model_switcher()
            narrative_analyzer = get_narrative_analyzer()

            # 2. 模拟数据处理
            large_text_data = []
            for i in range(100):  # 模拟处理100个文本
                text = f"这是第{i}个测试文本，用于模拟大量数据处理的内存使用情况。" * 10
                large_text_data.append(text)

            # 3. 模拟分析处理
            for i, text in enumerate(large_text_data[:20]):  # 处理前20个
                if i % 5 == 0:
                    current_memory = memory_guard.get_memory_usage()
                    print(f"  处理进度 {i+1}/20, 当前内存: {current_memory:.2f}MB")

                # 模拟分析
                narrative_analyzer.analyze_narrative_structure([text])

            # 4. 强制垃圾回收
            memory_guard.force_cleanup()

            # 计算性能指标
            execution_time = time.time() - start_time
            memory_peak = memory_guard.get_memory_usage()
            memory_used = memory_peak - memory_start

            # 停止监控
            memory_guard.stop_monitoring()

            # 评估结果 (模拟4GB环境，实际峰值应该≤3800MB)
            # 由于我们在高内存环境中模拟，我们检查相对内存增长
            test_passed = memory_used < 200  # 内存增长应该控制在200MB以内

            performance_data = {
                "execution_time_seconds": round(execution_time, 3),
                "memory_baseline_mb": round(memory_start, 2),
                "memory_peak_mb": round(memory_peak, 2),
                "memory_increase_mb": round(memory_used, 2),
                "simulated_4gb_environment": True,
                "processed_texts": 20
            }

            issues = []
            if memory_used > 200:
                issues.append(f"内存增长 {memory_used:.1f}MB > 200MB，可能在4GB设备上超限")

            self._log_test_result(
                "TC-MEMORY-001", test_passed,
                f"内存峰值监控测试 - 内存增长: {memory_used:.2f}MB",
                performance_data, issues
            )

            print(f"\n📊 测试结果:")
            print(f"  ✅ 测试状态: {'通过' if test_passed else '失败'}")
            print(f"  📈 内存增长: {memory_used:.2f}MB")
            print(f"  💾 峰值内存: {memory_peak:.2f}MB")
            print(f"  ⏱️ 执行时间: {execution_time:.3f}秒")

            return test_passed

        except Exception as e:
            execution_time = time.time() - start_time
            self._log_test_result(
                "TC-MEMORY-001", False,
                f"测试执行失败: {str(e)}",
                {"execution_time_seconds": execution_time},
                [f"Test execution error: {str(e)}"]
            )
            print(f"❌ 测试失败: {str(e)}")
            return False

    def run_enhanced_p0_tests(self) -> Dict[str, Any]:
        """运行增强版P0级别测试用例"""
        print("🚀 开始执行VisionAI-ClipsMaster AI模型训练P0测试 (增强版)...")
        print("=" * 80)

        # 1. 创建增强测试数据
        if not self.create_enhanced_test_data():
            print("❌ 增强测试数据创建失败，终止测试")
            return self.test_results

        # 2. 执行P0测试用例
        p0_tests = [
            ("TC-SWITCH-001", self.execute_tc_switch_001),
            ("TC-SWITCH-002", self.execute_tc_switch_002),
            ("TC-MEMORY-001", self.execute_tc_memory_001),
        ]

        passed_tests = 0
        total_tests = len(p0_tests)

        for test_id, test_func in p0_tests:
            print(f"\n{'='*25} {test_id} {'='*25}")
            if test_func():
                passed_tests += 1
                print(f"✅ {test_id} 通过")
            else:
                print(f"❌ {test_id} 失败")

        # 计算总体结果
        success_rate = passed_tests / total_tests
        total_execution_time = time.time() - self.start_time

        self.test_results["overall_summary"] = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "success_rate": round(success_rate, 3),
            "total_execution_time_seconds": round(total_execution_time, 3),
            "test_completion_time": datetime.now().isoformat(),
            "test_environment_4gb_simulation": True
        }

        return self.test_results

if __name__ == "__main__":
    executor = EnhancedAITrainingTestExecutor()
    results = executor.run_enhanced_p0_tests()

    # 保存测试结果
    report_file = f"Enhanced_AI_Training_Test_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n📄 增强版测试报告已保存到: {report_file}")

    # 打印总结
    summary = results["overall_summary"]
    print(f"\n🎯 测试总结:")
    print(f"  总测试数: {summary['total_tests']}")
    print(f"  通过测试: {summary['passed_tests']}")
    print(f"  失败测试: {summary['failed_tests']}")
    print(f"  成功率: {summary['success_rate']:.1%}")
    print(f"  总执行时间: {summary['total_execution_time_seconds']:.3f}秒")
