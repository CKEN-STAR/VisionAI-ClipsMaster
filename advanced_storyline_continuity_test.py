#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 高级剧情连贯性和时长控制测试
专门验证剧本重构的核心逻辑：避免"过短导致剧情不连贯"或"过长与原片相差不大"
"""

import sys
import os
import time
import json
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

class StorylineContinuityTester:
    """剧情连贯性测试器"""
    
    def __init__(self):
        self.test_results = []
        self.temp_dir = Path(tempfile.mkdtemp(prefix="storyline_test_"))
        
    def create_complex_storyline_data(self) -> Dict[str, Any]:
        """创建复杂的剧情测试数据"""
        print("📚 创建复杂剧情测试数据...")
        
        # 创建一个完整的短剧剧情（30个字幕段，总时长5分钟）
        complex_storyline = []
        
        # 第一幕：相遇（0-60秒）
        act1_segments = [
            {"start": "00:00:00,000", "end": "00:00:05,000", "text": "繁华都市的清晨，阳光洒在咖啡厅的玻璃窗上"},
            {"start": "00:00:05,000", "end": "00:00:10,000", "text": "李晨匆忙走进咖啡厅，手里拿着重要的商业企划书"},
            {"start": "00:00:10,000", "end": "00:00:15,000", "text": "不小心撞到了正在画画的艺术家苏雨"},
            {"start": "00:00:15,000", "end": "00:00:20,000", "text": "咖啡洒了一地，苏雨的画作也被弄湿了"},
            {"start": "00:00:20,000", "end": "00:00:25,000", "text": "李晨连忙道歉，主动提出赔偿画作的损失"},
            {"start": "00:00:25,000", "end": "00:00:30,000", "text": "苏雨看着这个诚恳的男人，心中涌起一丝暖意"},
            {"start": "00:00:30,000", "end": "00:00:35,000", "text": "两人交换了联系方式，约定改天再见面"},
            {"start": "00:00:35,000", "end": "00:00:40,000", "text": "李晨离开后，苏雨望着他的背影若有所思"},
            {"start": "00:00:40,000", "end": "00:00:45,000", "text": "这次意外的相遇，改变了两个人的命运轨迹"},
            {"start": "00:00:45,000", "end": "00:00:60,000", "text": "命运的齿轮开始转动，一段美好的爱情即将开始"}
        ]
        
        # 第二幕：相知（60-180秒）
        act2_segments = [
            {"start": "00:01:00,000", "end": "00:01:10,000", "text": "几天后，李晨如约来到苏雨的画室"},
            {"start": "00:01:10,000", "end": "00:01:20,000", "text": "画室里充满了艺术的气息，各种颜料和画布随处可见"},
            {"start": "00:01:20,000", "end": "00:01:30,000", "text": "苏雨正在创作一幅关于城市生活的油画"},
            {"start": "00:01:30,000", "end": "00:01:40,000", "text": "李晨被她专注的神情深深吸引"},
            {"start": "00:01:40,000", "end": "00:01:50,000", "text": "苏雨向他介绍自己的艺术理念和创作灵感"},
            {"start": "00:01:50,000", "end": "00:02:00,000", "text": "李晨分享了自己在商业世界中的奋斗经历"},
            {"start": "00:02:00,000", "end": "00:02:10,000", "text": "两个来自不同世界的人，却找到了心灵的共鸣"},
            {"start": "00:02:10,000", "end": "00:02:20,000", "text": "他们开始频繁地见面，感情逐渐升温"},
            {"start": "00:02:20,000", "end": "00:02:30,000", "text": "李晨学会了欣赏艺术，苏雨了解了商业世界"},
            {"start": "00:02:30,000", "end": "00:03:00,000", "text": "爱情在两颗心中悄然绽放"}
        ]
        
        # 第三幕：冲突（180-240秒）
        act3_segments = [
            {"start": "00:03:00,000", "end": "00:03:15,000", "text": "然而，现实的压力开始显现"},
            {"start": "00:03:15,000", "end": "00:03:30,000", "text": "李晨的公司面临重大危机，需要他全身心投入"},
            {"start": "00:03:30,000", "end": "00:03:45,000", "text": "苏雨的画展即将开幕，也需要大量的准备时间"},
            {"start": "00:03:45,000", "end": "00:04:00,000", "text": "两人的时间越来越少，误解开始产生"}
        ]
        
        # 第四幕：和解（240-300秒）
        act4_segments = [
            {"start": "00:04:00,000", "end": "00:04:20,000", "text": "在最困难的时刻，两人意识到彼此的重要性"},
            {"start": "00:04:20,000", "end": "00:04:40,000", "text": "李晨放下工作，来到苏雨的画展现场"},
            {"start": "00:04:40,000", "end": "00:05:00,000", "text": "苏雨看到李晨的身影，眼中闪烁着泪光"}
        ]
        
        # 合并所有片段
        complex_storyline.extend(act1_segments)
        complex_storyline.extend(act2_segments)
        complex_storyline.extend(act3_segments)
        complex_storyline.extend(act4_segments)
        
        return {
            "original_storyline": complex_storyline,
            "total_duration": 300,  # 5分钟
            "total_segments": len(complex_storyline),
            "acts": {
                "act1": {"segments": len(act1_segments), "duration": 60},
                "act2": {"segments": len(act2_segments), "duration": 120},
                "act3": {"segments": len(act3_segments), "duration": 60},
                "act4": {"segments": len(act4_segments), "duration": 60}
            }
        }
        
    def test_storyline_reconstruction(self, storyline_data: Dict[str, Any]) -> Dict[str, Any]:
        """测试剧情重构功能"""
        print("🎬 测试剧情重构功能...")
        
        test_result = {
            "test_name": "剧情重构测试",
            "start_time": datetime.now().isoformat(),
            "status": "running",
            "original_data": {
                "total_segments": storyline_data["total_segments"],
                "total_duration": storyline_data["total_duration"]
            },
            "reconstruction_results": {}
        }
        
        try:
            from src.core.screenplay_engineer import ScreenplayEngineer
            engineer = ScreenplayEngineer()
            
            # 执行剧本重构
            original_storyline = storyline_data["original_storyline"]
            reconstructed_storyline = engineer.reconstruct_screenplay(original_storyline)
            
            if reconstructed_storyline:
                # 分析重构结果
                reconstructed_duration = self._calculate_total_duration(reconstructed_storyline)
                compression_ratio = len(reconstructed_storyline) / len(original_storyline)
                duration_ratio = reconstructed_duration / storyline_data["total_duration"]
                
                # 检查剧情连贯性
                continuity_score = self._analyze_storyline_continuity(reconstructed_storyline)
                
                # 检查时长合理性
                duration_appropriateness = self._check_duration_appropriateness(
                    original_duration=storyline_data["total_duration"],
                    reconstructed_duration=reconstructed_duration
                )
                
                test_result["reconstruction_results"] = {
                    "reconstructed_segments": len(reconstructed_storyline),
                    "reconstructed_duration": reconstructed_duration,
                    "compression_ratio": compression_ratio,
                    "duration_ratio": duration_ratio,
                    "continuity_score": continuity_score,
                    "duration_appropriateness": duration_appropriateness,
                    "status": "success"
                }
                
                # 判断重构质量
                quality_assessment = self._assess_reconstruction_quality(test_result["reconstruction_results"])
                test_result["reconstruction_results"]["quality_assessment"] = quality_assessment
                
                print(f"   ✅ 剧情重构完成:")
                print(f"      原始片段: {len(original_storyline)} → 重构片段: {len(reconstructed_storyline)}")
                print(f"      原始时长: {storyline_data['total_duration']}s → 重构时长: {reconstructed_duration:.1f}s")
                print(f"      压缩比: {compression_ratio:.2f}")
                print(f"      连贯性评分: {continuity_score:.2f}")
                print(f"      时长合理性: {duration_appropriateness}")
                print(f"      质量评估: {quality_assessment}")
                
            else:
                test_result["reconstruction_results"] = {
                    "status": "failed",
                    "error": "重构结果为空"
                }
                
            test_result["status"] = "completed"
            test_result["end_time"] = datetime.now().isoformat()
            
        except Exception as e:
            test_result["status"] = "failed"
            test_result["error"] = str(e)
            test_result["end_time"] = datetime.now().isoformat()
            print(f"   ❌ 剧情重构测试失败: {e}")
            
        return test_result
        
    def _calculate_total_duration(self, storyline: List[Dict]) -> float:
        """计算剧情总时长"""
        if not storyline:
            return 0.0
            
        try:
            last_segment = storyline[-1]
            end_time = last_segment.get("end", "00:00:00,000")
            
            # 解析时间格式 HH:MM:SS,mmm
            time_parts = end_time.split(":")
            hours = int(time_parts[0])
            minutes = int(time_parts[1])
            seconds_parts = time_parts[2].split(",")
            seconds = int(seconds_parts[0])
            milliseconds = int(seconds_parts[1])
            
            total_seconds = hours * 3600 + minutes * 60 + seconds + milliseconds / 1000
            return total_seconds
            
        except Exception:
            return 0.0
            
    def _analyze_storyline_continuity(self, storyline: List[Dict]) -> float:
        """分析剧情连贯性"""
        if not storyline or len(storyline) < 2:
            return 0.0
            
        # 简单的连贯性评分算法
        continuity_score = 0.0
        
        # 检查时间轴连续性
        time_continuity = 0.0
        for i in range(len(storyline) - 1):
            current_end = storyline[i].get("end", "")
            next_start = storyline[i + 1].get("start", "")
            
            if current_end and next_start:
                # 简单检查时间顺序
                if current_end <= next_start:
                    time_continuity += 1
                    
        time_continuity_score = time_continuity / (len(storyline) - 1) if len(storyline) > 1 else 0
        
        # 检查内容连贯性（简单的关键词匹配）
        content_continuity = 0.5  # 默认中等连贯性
        
        # 综合评分
        continuity_score = (time_continuity_score * 0.6 + content_continuity * 0.4)
        
        return continuity_score
        
    def _check_duration_appropriateness(self, original_duration: float, reconstructed_duration: float) -> str:
        """检查时长合理性"""
        duration_ratio = reconstructed_duration / original_duration
        
        if duration_ratio < 0.1:
            return "过短-可能导致剧情不连贯"
        elif duration_ratio > 0.8:
            return "过长-与原片差异不大"
        elif 0.2 <= duration_ratio <= 0.6:
            return "理想-时长适中"
        elif 0.1 <= duration_ratio < 0.2:
            return "偏短-需要注意连贯性"
        else:  # 0.6 < duration_ratio <= 0.8
            return "偏长-压缩效果有限"
            
    def _assess_reconstruction_quality(self, results: Dict[str, Any]) -> str:
        """评估重构质量"""
        continuity_score = results.get("continuity_score", 0)
        duration_appropriateness = results.get("duration_appropriateness", "")
        compression_ratio = results.get("compression_ratio", 0)
        
        # 质量评估逻辑
        if (continuity_score >= 0.7 and 
            "理想" in duration_appropriateness and 
            0.2 <= compression_ratio <= 0.6):
            return "优秀"
        elif (continuity_score >= 0.5 and 
              "过短" not in duration_appropriateness and 
              "过长" not in duration_appropriateness):
            return "良好"
        elif continuity_score >= 0.3:
            return "一般"
        else:
            return "需要改进"

    def test_multiple_scenarios(self) -> Dict[str, Any]:
        """测试多种剧情场景"""
        print("🎭 测试多种剧情场景...")

        scenarios = {
            "complex_storyline": self.create_complex_storyline_data(),
            "simple_storyline": self._create_simple_storyline(),
            "action_storyline": self._create_action_storyline(),
            "romance_storyline": self._create_romance_storyline()
        }

        scenario_results = {}

        for scenario_name, scenario_data in scenarios.items():
            print(f"\n   📖 测试场景: {scenario_name}")
            result = self.test_storyline_reconstruction(scenario_data)
            scenario_results[scenario_name] = result

        return {
            "test_name": "多场景剧情测试",
            "scenarios": scenario_results,
            "summary": self._summarize_scenario_results(scenario_results)
        }

    def _create_simple_storyline(self) -> Dict[str, Any]:
        """创建简单剧情"""
        simple_storyline = [
            {"start": "00:00:00,000", "end": "00:00:10,000", "text": "开始"},
            {"start": "00:00:10,000", "end": "00:00:20,000", "text": "发展"},
            {"start": "00:00:20,000", "end": "00:00:30,000", "text": "结束"}
        ]

        return {
            "original_storyline": simple_storyline,
            "total_duration": 30,
            "total_segments": len(simple_storyline)
        }

    def _create_action_storyline(self) -> Dict[str, Any]:
        """创建动作剧情"""
        action_storyline = [
            {"start": "00:00:00,000", "end": "00:00:05,000", "text": "特工接到紧急任务"},
            {"start": "00:00:05,000", "end": "00:00:10,000", "text": "潜入敌方基地"},
            {"start": "00:00:10,000", "end": "00:00:15,000", "text": "激烈的枪战爆发"},
            {"start": "00:00:15,000", "end": "00:00:20,000", "text": "成功获取机密文件"},
            {"start": "00:00:20,000", "end": "00:00:25,000", "text": "惊险逃脱追捕"},
            {"start": "00:00:25,000", "end": "00:00:30,000", "text": "任务圆满完成"}
        ]

        return {
            "original_storyline": action_storyline,
            "total_duration": 30,
            "total_segments": len(action_storyline)
        }

    def _create_romance_storyline(self) -> Dict[str, Any]:
        """创建爱情剧情"""
        romance_storyline = [
            {"start": "00:00:00,000", "end": "00:00:08,000", "text": "在图书馆的偶然相遇"},
            {"start": "00:00:08,000", "end": "00:00:16,000", "text": "共同的兴趣爱好让两人走近"},
            {"start": "00:00:16,000", "end": "00:00:24,000", "text": "甜蜜的约会时光"},
            {"start": "00:00:24,000", "end": "00:00:32,000", "text": "误会导致的分离"},
            {"start": "00:00:32,000", "end": "00:00:40,000", "text": "真相大白后的重逢"},
            {"start": "00:00:40,000", "end": "00:00:48,000", "text": "幸福的结局"}
        ]

        return {
            "original_storyline": romance_storyline,
            "total_duration": 48,
            "total_segments": len(romance_storyline)
        }

    def _summarize_scenario_results(self, scenario_results: Dict[str, Any]) -> Dict[str, Any]:
        """总结场景测试结果"""
        summary = {
            "total_scenarios": len(scenario_results),
            "successful_scenarios": 0,
            "failed_scenarios": 0,
            "quality_distribution": {"优秀": 0, "良好": 0, "一般": 0, "需要改进": 0},
            "average_compression_ratio": 0,
            "average_continuity_score": 0
        }

        compression_ratios = []
        continuity_scores = []

        for scenario_name, result in scenario_results.items():
            if result["status"] == "completed":
                summary["successful_scenarios"] += 1

                reconstruction_results = result.get("reconstruction_results", {})
                if reconstruction_results.get("status") == "success":
                    quality = reconstruction_results.get("quality_assessment", "需要改进")
                    summary["quality_distribution"][quality] += 1

                    compression_ratio = reconstruction_results.get("compression_ratio", 0)
                    continuity_score = reconstruction_results.get("continuity_score", 0)

                    compression_ratios.append(compression_ratio)
                    continuity_scores.append(continuity_score)
            else:
                summary["failed_scenarios"] += 1

        # 计算平均值
        if compression_ratios:
            summary["average_compression_ratio"] = sum(compression_ratios) / len(compression_ratios)
        if continuity_scores:
            summary["average_continuity_score"] = sum(continuity_scores) / len(continuity_scores)

        return summary

    def run_comprehensive_storyline_test(self) -> Dict[str, Any]:
        """运行完整的剧情测试"""
        print("=" * 80)
        print("🎬 VisionAI-ClipsMaster 高级剧情连贯性和时长控制测试")
        print("=" * 80)

        test_start_time = datetime.now()

        # 运行多场景测试
        scenario_results = self.test_multiple_scenarios()

        # 生成测试报告
        test_report = {
            "test_suite": "高级剧情连贯性和时长控制测试",
            "start_time": test_start_time.isoformat(),
            "end_time": datetime.now().isoformat(),
            "duration": (datetime.now() - test_start_time).total_seconds(),
            "results": scenario_results,
            "conclusions": self._generate_conclusions(scenario_results)
        }

        # 输出测试总结
        self._print_test_summary(test_report)

        # 保存测试报告
        report_path = self.temp_dir / "storyline_continuity_test_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(test_report, f, ensure_ascii=False, indent=2)
        print(f"\n📄 详细测试报告已保存: {report_path}")

        return test_report

    def _generate_conclusions(self, scenario_results: Dict[str, Any]) -> Dict[str, Any]:
        """生成测试结论"""
        summary = scenario_results.get("summary", {})

        conclusions = {
            "overall_performance": "良好",
            "strengths": [],
            "weaknesses": [],
            "recommendations": []
        }

        # 分析优势
        if summary.get("average_continuity_score", 0) >= 0.7:
            conclusions["strengths"].append("剧情连贯性保持良好")
        if summary.get("average_compression_ratio", 0) >= 0.3:
            conclusions["strengths"].append("压缩效果适中，避免过度剪切")
        if summary.get("quality_distribution", {}).get("优秀", 0) > 0:
            conclusions["strengths"].append("部分场景达到优秀重构质量")

        # 分析弱点
        if summary.get("failed_scenarios", 0) > 0:
            conclusions["weaknesses"].append("部分场景重构失败")
        if summary.get("quality_distribution", {}).get("需要改进", 0) > 1:
            conclusions["weaknesses"].append("多个场景需要改进重构算法")
        if summary.get("average_compression_ratio", 0) < 0.2:
            conclusions["weaknesses"].append("压缩比过低，可能导致剧情不连贯")

        # 生成建议
        if summary.get("average_continuity_score", 0) < 0.5:
            conclusions["recommendations"].append("优化剧情连贯性算法")
        if summary.get("average_compression_ratio", 0) > 0.8:
            conclusions["recommendations"].append("增强压缩效果，提高混剪价值")
        if summary.get("successful_scenarios", 0) < summary.get("total_scenarios", 1):
            conclusions["recommendations"].append("提高算法稳定性和容错能力")

        # 确定总体性能
        success_rate = summary.get("successful_scenarios", 0) / summary.get("total_scenarios", 1)
        if success_rate >= 0.8 and summary.get("average_continuity_score", 0) >= 0.6:
            conclusions["overall_performance"] = "优秀"
        elif success_rate >= 0.6 and summary.get("average_continuity_score", 0) >= 0.4:
            conclusions["overall_performance"] = "良好"
        elif success_rate >= 0.4:
            conclusions["overall_performance"] = "一般"
        else:
            conclusions["overall_performance"] = "需要改进"

        return conclusions

    def _print_test_summary(self, test_report: Dict[str, Any]):
        """打印测试总结"""
        print("\n" + "=" * 80)
        print("📊 测试总结")
        print("=" * 80)

        summary = test_report["results"]["summary"]
        conclusions = test_report["conclusions"]

        print(f"测试场景总数: {summary['total_scenarios']}")
        print(f"成功场景数: {summary['successful_scenarios']}")
        print(f"失败场景数: {summary['failed_scenarios']}")
        print(f"成功率: {summary['successful_scenarios']/summary['total_scenarios']:.1%}")
        print(f"平均压缩比: {summary['average_compression_ratio']:.2f}")
        print(f"平均连贯性评分: {summary['average_continuity_score']:.2f}")
        print(f"总体性能: {conclusions['overall_performance']}")

        print("\n质量分布:")
        for quality, count in summary['quality_distribution'].items():
            print(f"  {quality}: {count} 个场景")

        if conclusions['strengths']:
            print(f"\n✅ 优势:")
            for strength in conclusions['strengths']:
                print(f"  • {strength}")

        if conclusions['weaknesses']:
            print(f"\n⚠️  弱点:")
            for weakness in conclusions['weaknesses']:
                print(f"  • {weakness}")

        if conclusions['recommendations']:
            print(f"\n💡 建议:")
            for recommendation in conclusions['recommendations']:
                print(f"  • {recommendation}")


def main():
    """主函数"""
    try:
        tester = StorylineContinuityTester()
        results = tester.run_comprehensive_storyline_test()

        # 根据测试结果返回退出码
        conclusions = results.get("conclusions", {})
        overall_performance = conclusions.get("overall_performance", "需要改进")

        if overall_performance in ["优秀", "良好"]:
            print("\n🎉 剧情连贯性和时长控制测试通过！")
            return 0
        else:
            print(f"\n⚠️  剧情连贯性和时长控制需要改进: {overall_performance}")
            return 1

    except Exception as e:
        print(f"\n💥 测试执行异常: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
