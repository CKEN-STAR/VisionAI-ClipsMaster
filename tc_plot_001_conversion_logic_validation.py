#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
TC-PLOT-001: 原片-爆款转换逻辑验证测试

测试VisionAI-ClipsMaster的核心转换逻辑：
1. 原片剧本分析准确性
2. 爆款特征识别能力
3. 转换逻辑的合理性
4. 输出质量评估
"""

import json
import time
import psutil
import os
from datetime import datetime
from typing import Dict, List, Any, Tuple

def create_conversion_test_data() -> Dict[str, Any]:
    """创建转换逻辑测试数据"""
    
    # 原片剧本示例
    original_scripts = {
        "palace_drama": {
            "title": "宫廷日常",
            "original_subtitles": [
                "皇上，今日朝政如何？",
                "还算顺利，只是有些小事需要处理。",
                "臣妾为皇上准备了茶水。",
                "多谢爱妃的关心。",
                "太子殿下今日功课如何？",
                "回禀母后，功课已经完成。",
                "很好，继续努力。",
                "是，母后。",
                "今日天气不错，可以到御花园走走。",
                "臣妾陪同皇上一起。"
            ],
            "viral_target": {
                "style": "dramatic_conflict",
                "key_elements": ["权力斗争", "情感冲突", "悬念设置"],
                "expected_improvements": [
                    "增加紧张感",
                    "强化角色冲突", 
                    "添加悬念元素",
                    "提升情感强度"
                ]
            }
        },
        
        "modern_office": {
            "title": "办公室日常",
            "original_subtitles": [
                "早上好，今天的会议准备好了吗？",
                "是的，所有资料都已经整理完毕。",
                "那我们开始吧。",
                "好的，首先汇报销售数据。",
                "这个月的业绩还不错。",
                "确实，比上个月有所提升。",
                "继续保持这个势头。",
                "我们会努力的。",
                "会议就到这里，大家辛苦了。",
                "谢谢领导。"
            ],
            "viral_target": {
                "style": "workplace_drama",
                "key_elements": ["职场竞争", "人际关系", "成长励志"],
                "expected_improvements": [
                    "增加职场冲突",
                    "强化竞争元素",
                    "添加励志色彩",
                    "提升戏剧张力"
                ]
            }
        }
    }
    
    return original_scripts

def analyze_original_script(subtitles: List[str]) -> Dict[str, Any]:
    """分析原片剧本"""
    try:
        from src.core.narrative_analyzer import analyze_narrative_structure
        from src.emotion.emotion_intensity import get_emotion_intensity
        
        # 叙事结构分析
        narrative_result = analyze_narrative_structure(subtitles)
        
        # 情感分析
        emotion_analyzer = get_emotion_intensity()
        emotion_profile = []
        
        for subtitle in subtitles:
            emotions = emotion_analyzer.analyze_emotion_intensity(subtitle)
            dominant_emotion, intensity = emotion_analyzer.get_dominant_emotion(subtitle)
            emotion_profile.append({
                "text": subtitle,
                "dominant_emotion": dominant_emotion,
                "intensity": intensity,
                "all_emotions": emotions
            })
        
        return {
            "status": "success",
            "narrative_analysis": narrative_result,
            "emotion_profile": emotion_profile,
            "total_segments": len(subtitles),
            "plot_points": narrative_result.get("plot_points", []),
            "emotion_variety": len(set(ep["dominant_emotion"] for ep in emotion_profile))
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "total_segments": len(subtitles)
        }

def evaluate_viral_potential(analysis_result: Dict[str, Any], viral_target: Dict[str, Any]) -> Dict[str, Any]:
    """评估爆款潜力"""
    if analysis_result["status"] != "success":
        return {"viral_score": 0.0, "recommendations": ["分析失败，无法评估"]}
    
    viral_score = 0.0
    recommendations = []
    
    # 1. 情节密度评估
    plot_points = analysis_result.get("plot_points", [])
    total_segments = analysis_result.get("total_segments", 1)
    plot_density = len(plot_points) / total_segments
    
    if plot_density >= 0.5:
        viral_score += 25
    elif plot_density >= 0.3:
        viral_score += 15
        recommendations.append("增加关键情节点密度")
    else:
        viral_score += 5
        recommendations.append("大幅增加情节转折点")
    
    # 2. 情感强度评估
    emotion_profile = analysis_result.get("emotion_profile", [])
    if emotion_profile:
        avg_intensity = sum(ep["intensity"] for ep in emotion_profile) / len(emotion_profile)
        max_intensity = max(ep["intensity"] for ep in emotion_profile)
        
        if avg_intensity >= 1.0 and max_intensity >= 2.0:
            viral_score += 25
        elif avg_intensity >= 0.7:
            viral_score += 15
            recommendations.append("提升整体情感强度")
        else:
            viral_score += 5
            recommendations.append("大幅提升情感表达强度")
    
    # 3. 情感多样性评估
    emotion_variety = analysis_result.get("emotion_variety", 1)
    if emotion_variety >= 5:
        viral_score += 20
    elif emotion_variety >= 3:
        viral_score += 12
        recommendations.append("增加情感类型多样性")
    else:
        viral_score += 3
        recommendations.append("丰富情感表达类型")
    
    # 4. 叙事流向评估
    narrative_analysis = analysis_result.get("narrative_analysis", {})
    narrative_flow = narrative_analysis.get("narrative_flow", {})
    flow_type = narrative_flow.get("flow_type", "flat")
    
    if flow_type in ["classic", "climax_centered"]:
        viral_score += 20
    elif flow_type in ["distributed"]:
        viral_score += 12
        recommendations.append("优化叙事节奏")
    else:
        viral_score += 5
        recommendations.append("重构叙事结构")
    
    # 5. 目标风格匹配度评估
    target_style = viral_target.get("style", "")
    if target_style == "dramatic_conflict":
        # 检查是否有冲突元素
        conflict_emotions = ["angry", "worried", "fearful", "urgent"]
        has_conflict = any(ep["dominant_emotion"] in conflict_emotions for ep in emotion_profile)
        if has_conflict:
            viral_score += 10
        else:
            recommendations.append("增加戏剧冲突元素")
    elif target_style == "workplace_drama":
        # 检查是否有职场元素
        professional_emotions = ["professional", "serious", "authoritative"]
        has_professional = any(ep["dominant_emotion"] in professional_emotions for ep in emotion_profile)
        if has_professional:
            viral_score += 10
        else:
            recommendations.append("强化职场专业氛围")
    
    return {
        "viral_score": min(viral_score, 100.0),
        "recommendations": recommendations,
        "analysis_details": {
            "plot_density": plot_density,
            "avg_emotion_intensity": avg_intensity if emotion_profile else 0.0,
            "emotion_variety": emotion_variety,
            "narrative_flow": flow_type
        }
    }

def generate_conversion_suggestions(analysis_result: Dict[str, Any], viral_evaluation: Dict[str, Any]) -> List[str]:
    """生成转换建议"""
    suggestions = []
    
    recommendations = viral_evaluation.get("recommendations", [])
    analysis_details = viral_evaluation.get("analysis_details", {})
    
    # 基于分析结果生成具体建议
    if analysis_details.get("plot_density", 0) < 0.3:
        suggestions.append("在第2、5、8段添加转折点，增加剧情张力")
    
    if analysis_details.get("avg_emotion_intensity", 0) < 0.7:
        suggestions.append("强化对话的情感表达，使用更有力的词汇")
    
    if analysis_details.get("emotion_variety", 0) < 3:
        suggestions.append("增加情感类型：愤怒、惊讶、恐惧等强烈情感")
    
    if analysis_details.get("narrative_flow") == "flat":
        suggestions.append("重新安排情节顺序，创造起承转合的经典结构")
    
    # 添加通用的爆款化建议
    suggestions.extend([
        "在开头3秒内设置悬念钩子",
        "每15-20秒设置一个小高潮",
        "结尾留下悬念或反转",
        "使用短句和强烈的情感词汇"
    ])
    
    return suggestions[:8]  # 限制建议数量

def test_conversion_logic(test_data: Dict[str, Any]) -> Dict[str, Any]:
    """测试转换逻辑"""
    results = {}
    
    for script_name, script_data in test_data.items():
        print(f"  📖 测试 {script_data['title']} 转换逻辑")
        
        # 1. 分析原片
        original_analysis = analyze_original_script(script_data["original_subtitles"])
        
        # 2. 评估爆款潜力
        viral_evaluation = evaluate_viral_potential(original_analysis, script_data["viral_target"])
        
        # 3. 生成转换建议
        conversion_suggestions = generate_conversion_suggestions(original_analysis, viral_evaluation)
        
        # 4. 计算转换逻辑质量分数
        logic_score = 0.0
        
        # 分析成功性
        if original_analysis["status"] == "success":
            logic_score += 30
        
        # 爆款评估合理性
        viral_score = viral_evaluation.get("viral_score", 0)
        if 20 <= viral_score <= 80:  # 合理的分数范围
            logic_score += 25
        elif viral_score > 0:
            logic_score += 15
        
        # 建议质量
        if len(conversion_suggestions) >= 5:
            logic_score += 25
        elif len(conversion_suggestions) >= 3:
            logic_score += 15
        
        # 建议相关性
        recommendations = viral_evaluation.get("recommendations", [])
        if len(recommendations) > 0:
            logic_score += 20
        
        results[script_name] = {
            "original_analysis": original_analysis,
            "viral_evaluation": viral_evaluation,
            "conversion_suggestions": conversion_suggestions,
            "logic_score": logic_score,
            "viral_score": viral_score
        }
        
        print(f"    原片分析: {'✅ 成功' if original_analysis['status'] == 'success' else '❌ 失败'}")
        print(f"    爆款潜力: {viral_score:.1f}/100")
        print(f"    转换建议: {len(conversion_suggestions)}条")
        print(f"    逻辑质量: {logic_score:.1f}/100")
    
    return results

def main():
    """主测试函数"""
    print("🧪 开始TC-PLOT-001: 原片-爆款转换逻辑验证测试")
    print("=" * 70)
    
    start_time = time.time()
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    # 创建测试数据
    print("📊 创建转换逻辑测试数据...")
    test_data = create_conversion_test_data()
    
    # 测试转换逻辑
    print("🔄 测试原片-爆款转换逻辑...")
    conversion_results = test_conversion_logic(test_data)
    
    # 计算总体结果
    end_time = time.time()
    final_memory = process.memory_info().rss / 1024 / 1024  # MB
    execution_time = end_time - start_time
    
    # 计算平均分数
    logic_scores = [result["logic_score"] for result in conversion_results.values()]
    viral_scores = [result["viral_score"] for result in conversion_results.values()]
    
    avg_logic_score = sum(logic_scores) / len(logic_scores) if logic_scores else 0.0
    avg_viral_score = sum(viral_scores) / len(viral_scores) if viral_scores else 0.0
    
    # 判断测试结果
    logic_pass = avg_logic_score >= 70  # 70%阈值
    viral_pass = avg_viral_score >= 30  # 30%阈值（原片通常分数较低）
    memory_pass = final_memory <= 450  # 450MB阈值
    
    overall_pass = logic_pass and viral_pass and memory_pass
    
    print(f"\n📊 TC-PLOT-001 测试结果:")
    print(f"  🔄 转换逻辑质量: {avg_logic_score:.1f}/100 ({'✅ 通过' if logic_pass else '❌ 失败'})")
    print(f"  🎯 爆款潜力评估: {avg_viral_score:.1f}/100 ({'✅ 通过' if viral_pass else '❌ 失败'})")
    print(f"  ⏱️ 执行时间: {execution_time:.3f}秒")
    print(f"  💾 内存使用: {final_memory:.2f}MB ({'✅ 通过' if memory_pass else '❌ 超限'})")
    print(f"  🎯 总体状态: {'✅ 通过' if overall_pass else '❌ 失败'}")
    
    # 保存测试报告
    report = {
        "test_name": "TC-PLOT-001",
        "test_description": "原片-爆款转换逻辑验证测试",
        "timestamp": datetime.now().isoformat(),
        "execution_time": execution_time,
        "memory_usage": final_memory,
        "results": {
            "conversion_logic": {
                "average_score": avg_logic_score,
                "individual_scores": {k: v["logic_score"] for k, v in conversion_results.items()},
                "pass": logic_pass
            },
            "viral_potential": {
                "average_score": avg_viral_score,
                "individual_scores": {k: v["viral_score"] for k, v in conversion_results.items()},
                "pass": viral_pass
            }
        },
        "detailed_results": conversion_results,
        "overall_pass": overall_pass,
        "performance": {
            "memory_pass": memory_pass,
            "execution_time": execution_time
        }
    }
    
    report_filename = f"TC_PLOT_001_Test_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_filename, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 测试报告已保存到: {report_filename}")
    
    if overall_pass:
        print("\n🎉 TC-PLOT-001 测试通过！转换逻辑功能正常。")
        return True
    else:
        print("\n⚠️ TC-PLOT-001 测试未完全通过，需要进一步优化。")
        return False

if __name__ == "__main__":
    main()
