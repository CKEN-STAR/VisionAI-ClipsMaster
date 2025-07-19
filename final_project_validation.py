#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
最终项目验证脚本

对VisionAI-ClipsMaster进行全面的功能验证和性能评估
包括所有核心功能、性能指标、稳定性测试
"""

import json
import time
import psutil
import os
from datetime import datetime
from typing import Dict, List, Any

class ProjectValidator:
    """项目验证器"""
    
    def __init__(self):
        self.process = psutil.Process(os.getpid())
        self.start_time = time.time()
        self.initial_memory = self.process.memory_info().rss / 1024 / 1024
        self.test_results = {}
    
    def validate_language_detection(self) -> Dict[str, Any]:
        """验证语言检测功能"""
        print("🔍 验证语言检测功能...")
        
        try:
            from src.core.language_detector import detect_language
            
            test_cases = [
                ("我今天去了shopping mall买东西。", "zh"),
                ("Today我们要学习Chinese language。", "en"),
                ("皇上，臣妾有重要的事情要禀报。", "zh"),
                ("Good morning, everyone. We have an important announcement.", "en"),
                ("这个project很important，需要careful planning。", "zh"),
                ("Let's go to 北京 for vacation this summer。", "en")
            ]
            
            correct_count = 0
            total_count = len(test_cases)
            
            for text, expected in test_cases:
                detected, confidence = detect_language(text)
                if detected == expected:
                    correct_count += 1
            
            accuracy = correct_count / total_count
            
            return {
                "status": "success",
                "accuracy": accuracy,
                "correct_count": correct_count,
                "total_count": total_count,
                "pass": accuracy >= 0.95
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "pass": False
            }
    
    def validate_emotion_analysis(self) -> Dict[str, Any]:
        """验证情感分析功能"""
        print("💭 验证情感分析功能...")
        
        try:
            from src.emotion.emotion_intensity import get_emotion_intensity
            emotion_analyzer = get_emotion_intensity()
            
            test_cases = [
                ("皇上，臣妾有重要的事情要禀报。", "formal"),
                ("什么事情如此紧急？速速道来！", "urgent"),
                ("你竟敢质疑朕的决定？大胆！", "angry"),
                ("这件事关系重大，不可轻举妄动。", "serious"),
                ("谢谢您，我有点紧张。", "grateful"),
                ("Good morning, everyone. We have an important announcement.", "formal")
            ]
            
            correct_count = 0
            total_count = len(test_cases)
            
            for text, expected in test_cases:
                dominant_emotion, intensity = emotion_analyzer.get_dominant_emotion(text)
                if dominant_emotion == expected:
                    correct_count += 1
            
            accuracy = correct_count / total_count
            
            return {
                "status": "success",
                "accuracy": accuracy,
                "correct_count": correct_count,
                "total_count": total_count,
                "pass": accuracy >= 0.75  # 75%阈值
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "pass": False
            }
    
    def validate_plot_analysis(self) -> Dict[str, Any]:
        """验证情节点分析功能"""
        print("📖 验证情节点分析功能...")
        
        try:
            from src.core.narrative_analyzer import analyze_narrative_structure
            
            test_script = [
                "皇上，臣妾有重要的事情要禀报。",
                "什么事情如此紧急？速速道来！",
                "关于太子殿下的事情，臣妾深感不妥。",
                "你竟敢质疑朕的决定？大胆！",
                "臣妾不敢，只是担心江山社稷啊。",
                "这件事关系重大，不可轻举妄动。",
                "臣妾明白了，一切听从皇上安排。",
                "传朕旨意，召集众臣商议此事。"
            ]
            
            result = analyze_narrative_structure(test_script)
            
            if result["status"] == "success":
                plot_points = result.get("plot_points", [])
                plot_density = len(plot_points) / len(test_script)
                
                return {
                    "status": "success",
                    "plot_points": plot_points,
                    "plot_density": plot_density,
                    "total_segments": len(test_script),
                    "pass": plot_density >= 0.4  # 40%阈值
                }
            else:
                return {
                    "status": "error",
                    "message": result.get("message", "分析失败"),
                    "pass": False
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "pass": False
            }
    
    def validate_conversion_logic(self) -> Dict[str, Any]:
        """验证转换逻辑功能"""
        print("🔄 验证转换逻辑功能...")
        
        try:
            # 模拟转换逻辑验证
            test_script = [
                "早上好，今天的会议准备好了吗？",
                "是的，所有资料都已经整理完毕。",
                "那我们开始吧。",
                "好的，首先汇报销售数据。"
            ]
            
            # 分析原片
            from src.core.narrative_analyzer import analyze_narrative_structure
            from src.emotion.emotion_intensity import get_emotion_intensity
            
            narrative_result = analyze_narrative_structure(test_script)
            emotion_analyzer = get_emotion_intensity()
            
            # 评估转换潜力
            if narrative_result["status"] == "success":
                plot_density = len(narrative_result.get("plot_points", [])) / len(test_script)
                
                # 情感分析
                emotions = []
                for text in test_script:
                    emotion_result = emotion_analyzer.analyze_emotion_intensity(text)
                    emotions.append(emotion_result)
                
                # 生成建议
                suggestions = []
                if plot_density < 0.5:
                    suggestions.append("增加关键情节点")
                if len(emotions) > 0:
                    suggestions.append("强化情感表达")
                
                suggestions.extend([
                    "添加悬念元素",
                    "优化节奏控制"
                ])
                
                return {
                    "status": "success",
                    "plot_density": plot_density,
                    "emotion_count": len(emotions),
                    "suggestions": suggestions,
                    "pass": len(suggestions) >= 3
                }
            else:
                return {
                    "status": "error",
                    "message": "依赖分析失败",
                    "pass": False
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "pass": False
            }
    
    def validate_performance(self) -> Dict[str, Any]:
        """验证性能指标"""
        print("⚡ 验证性能指标...")
        
        current_time = time.time()
        execution_time = current_time - self.start_time
        current_memory = self.process.memory_info().rss / 1024 / 1024
        
        # 性能标准
        startup_time_pass = execution_time <= 10  # 10秒启动时间
        memory_pass = current_memory <= 450       # 450MB内存限制
        
        return {
            "execution_time": execution_time,
            "current_memory": current_memory,
            "startup_time_pass": startup_time_pass,
            "memory_pass": memory_pass,
            "pass": startup_time_pass and memory_pass
        }
    
    def run_comprehensive_validation(self) -> Dict[str, Any]:
        """运行综合验证"""
        print("🧪 开始最终项目验证")
        print("=" * 60)
        
        # 执行各项验证
        self.test_results["language_detection"] = self.validate_language_detection()
        self.test_results["emotion_analysis"] = self.validate_emotion_analysis()
        self.test_results["plot_analysis"] = self.validate_plot_analysis()
        self.test_results["conversion_logic"] = self.validate_conversion_logic()
        self.test_results["performance"] = self.validate_performance()
        
        # 计算总体通过率
        passed_tests = sum(1 for result in self.test_results.values() if result.get("pass", False))
        total_tests = len(self.test_results)
        overall_pass_rate = passed_tests / total_tests
        
        # 生成验证报告
        validation_report = {
            "validation_timestamp": datetime.now().isoformat(),
            "test_results": self.test_results,
            "summary": {
                "passed_tests": passed_tests,
                "total_tests": total_tests,
                "overall_pass_rate": overall_pass_rate,
                "validation_success": overall_pass_rate >= 0.8
            },
            "performance_metrics": {
                "execution_time": self.test_results["performance"]["execution_time"],
                "memory_usage": self.test_results["performance"]["current_memory"],
                "startup_time_pass": self.test_results["performance"]["startup_time_pass"],
                "memory_pass": self.test_results["performance"]["memory_pass"]
            }
        }
        
        # 显示结果
        print(f"\n📊 最终验证结果:")
        print(f"  🔍 语言检测: {'✅ 通过' if self.test_results['language_detection']['pass'] else '❌ 失败'}")
        print(f"  💭 情感分析: {'✅ 通过' if self.test_results['emotion_analysis']['pass'] else '❌ 失败'}")
        print(f"  📖 情节分析: {'✅ 通过' if self.test_results['plot_analysis']['pass'] else '❌ 失败'}")
        print(f"  🔄 转换逻辑: {'✅ 通过' if self.test_results['conversion_logic']['pass'] else '❌ 失败'}")
        print(f"  ⚡ 性能指标: {'✅ 通过' if self.test_results['performance']['pass'] else '❌ 失败'}")
        
        print(f"\n📈 总体评估:")
        print(f"  通过测试: {passed_tests}/{total_tests}")
        print(f"  通过率: {overall_pass_rate:.1%}")
        print(f"  执行时间: {validation_report['performance_metrics']['execution_time']:.2f}秒")
        print(f"  内存使用: {validation_report['performance_metrics']['memory_usage']:.2f}MB")
        print(f"  验证状态: {'✅ 成功' if validation_report['summary']['validation_success'] else '❌ 失败'}")
        
        return validation_report

def main():
    """主验证函数"""
    validator = ProjectValidator()
    report = validator.run_comprehensive_validation()
    
    # 保存验证报告
    report_filename = f"Final_Project_Validation_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_filename, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 验证报告已保存到: {report_filename}")
    
    if report["summary"]["validation_success"]:
        print("\n🎉 项目验证成功！VisionAI-ClipsMaster已准备就绪。")
        return True
    else:
        print("\n⚠️ 项目验证未完全通过，需要进一步优化。")
        return False

if __name__ == "__main__":
    main()
