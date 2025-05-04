#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
高级时空连续性验证器演示

展示如何使用时空连续性验证器的高级功能分析场景序列，
包括叙事连贯性分析、视觉连续性检查和剪辑模式分析。
"""

import os
import sys
import json
from pathlib import Path
from pprint import pprint
import time
from datetime import datetime
import colorama
from colorama import Fore, Back, Style

# 添加项目根目录到Python路径
current_dir = Path(__file__).resolve().parent
root_dir = current_dir.parent.parent
if str(root_dir) not in sys.path:
    sys.path.append(str(root_dir))

from src.logic.spatiotemporal_checker import (
    SpatiotemporalValidator,
    validate_spatiotemporal_logic,
    format_time_ms
)

# 初始化colorama
colorama.init()

# 示例数据：一个完整的短剧混剪场景序列
COMPLEX_SCENE_SEQUENCE = [
    {
        "id": "scene_001",
        "source_file": "episode1.mp4",
        "start": 0,
        "end": 15000,
        "location": "家里",
        "character": "李明",
        "emotion": "平静",
        "text": "今天是我生日，但我不想庆祝。",
        "importance": 0.7,
        "time_of_day": "白天",
        "costume": "居家服"
    },
    {
        "id": "scene_002",
        "source_file": "episode1.mp4",
        "start": 15000,
        "end": 25000,
        "location": "家里",
        "character": "李明妈妈",
        "emotion": "关心",
        "text": "生日怎么能不庆祝呢？你一直很喜欢惊喜的。",
        "importance": 0.6,
        "time_of_day": "白天",
        "costume": "家居服"
    },
    {
        "id": "scene_003",
        "source_file": "episode1.mp4",
        "start": 25000,
        "end": 35000,
        "location": "咖啡厅",
        "character": "李明",
        "emotion": "惊讶",
        "text": "你们怎么都在这里？",
        "importance": 0.8,
        "time_of_day": "下午",
        "costume": "外出服"
    },
    {
        "id": "scene_004",
        "source_file": "episode2.mp4",
        "start": 35000,
        "end": 50000,
        "location": "咖啡厅",
        "character": "小红",
        "emotion": "高兴",
        "text": "生日快乐！我们准备了惊喜派对！",
        "importance": 0.9,
        "time_of_day": "下午",
        "costume": "连衣裙"
    },
    {
        "id": "scene_005",
        "source_file": "episode2.mp4",
        "start": 50000,
        "end": 65000,
        "location": "咖啡厅",
        "character": "李明",
        "emotion": "感动",
        "text": "谢谢大家，这是我最好的生日。",
        "importance": 0.9,
        "time_of_day": "傍晚",
        "costume": "外出服"
    }
]

# 存在问题的场景序列，用于展示各种检测能力
PROBLEMATIC_SCENE_SEQUENCE = [
    {
        "id": "prob_001",
        "source_file": "movie1.mp4",
        "start": 0,
        "end": 12000,
        "location": "办公室",
        "character": "张总",
        "emotion": "严肃",
        "text": "我们的项目必须在本周完成。",
        "importance": 0.8,
        "time_of_day": "白天",
        "costume": "西装"
    },
    {
        "id": "prob_002",
        "source_file": "movie1.mp4",
        "start": 12000,
        "end": 18000,
        "location": "咖啡厅", # 位置突变
        "character": "张总",
        "emotion": "放松", # 情感突变
        "text": "这里的咖啡真不错。",
        "importance": 0.3,
        "time_of_day": "白天",
        "costume": "休闲装" # 服装突变
    },
    {
        "id": "prob_003",
        "source_file": "movie2.mp4", # 源文件变化
        "start": 18000,
        "end": 22000,
        "location": "会议室",
        "character": "李经理",
        "emotion": "紧张",
        "text": "报告已经准备好了。",
        "importance": 0.7,
        "time_of_day": "晚上", # 时间突变
        "costume": "衬衫"
    },
    {
        "id": "prob_004",
        "source_file": "movie2.mp4",
        "start": 22000,
        "end": 28000,
        "location": "办公室",
        "character": "张总",
        "emotion": "愤怒",
        "text": "这份报告太糟糕了！完全不行！",
        "importance": 0.9,
        "time_of_day": "晚上",
        "costume": "西装" # 服装又变回来了
    },
    {
        "id": "prob_005",
        "source_file": "movie2.mp4",
        "start": 28000,
        "end": 32000,
        "location": "走廊",
        "character": "李经理",
        "emotion": "绝望",
        "text": "我要被开除了，怎么办...",
        "importance": 0.8,
        "time_of_day": "晚上",
        "costume": "衬衫"
    }
]

def print_colored_header(text, color=Fore.CYAN, symbol="="):
    """打印彩色标题"""
    width = 80
    print(f"\n{color}{symbol * width}")
    print(f"{text.center(width)}")
    print(f"{symbol * width}{Style.RESET_ALL}\n")

def print_subheader(text, color=Fore.YELLOW, symbol="-"):
    """打印彩色子标题"""
    width = 70
    print(f"\n{color}{symbol * 5} {text} {symbol * (width - len(text) - 7)}{Style.RESET_ALL}\n")

def print_result_item(label, value, label_color=Fore.GREEN, value_color=Fore.WHITE):
    """打印结果项"""
    print(f"{label_color}{label}: {value_color}{value}{Style.RESET_ALL}")

def print_scene(scene, index=None):
    """格式化打印单个场景"""
    prefix = f"[场景 {index}] " if index is not None else ""
    
    # 格式化时间
    start_str = format_time_ms(scene["start"]) if isinstance(scene["start"], (int, float)) else scene["start"]
    end_str = format_time_ms(scene["end"]) if isinstance(scene["end"], (int, float)) else scene["end"]
    
    print(f"{Fore.CYAN}{prefix}ID: {scene['id']}{Style.RESET_ALL}")
    print(f"  时间: {start_str} → {end_str}")
    print(f"  位置: {scene.get('location', '未知')}")
    print(f"  角色: {scene.get('character', '未知')}")
    print(f"  情感: {scene.get('emotion', '未知')}")
    
    # 打印额外属性
    for key in ["source_file", "costume", "time_of_day"]:
        if key in scene:
            print(f"  {key}: {scene[key]}")
    
    # 打印道具
    if "props" in scene:
        props_str = ", ".join(scene["props"]) if isinstance(scene["props"], list) else str(scene["props"])
        print(f"  道具: {props_str}")
    
    # 打印台词，限制长度
    text = scene.get("text", "")
    if len(text) > 50:
        text = text[:47] + "..."
    print(f"  台词: {text}")

def print_scenes(scenes, title=None):
    """格式化打印场景列表"""
    if title:
        print_subheader(title)
    
    for i, scene in enumerate(scenes):
        print_scene(scene, i+1)
        if i < len(scenes) - 1:
            print()

def print_suggestions(suggestions, title="建议"):
    """打印建议列表"""
    if not suggestions:
        return
        
    print_subheader(title)
    for i, suggestion in enumerate(suggestions):
        print(f"{Fore.GREEN}{i+1}. {suggestion}{Style.RESET_ALL}")

def demonstrate_basic_validation():
    """演示基本的时空连续性验证"""
    print_colored_header("基本时空连续性验证")
    
    validator = SpatiotemporalValidator()
    
    print_scenes(PROBLEMATIC_SCENE_SEQUENCE, "问题场景序列")
    
    # 执行验证
    results = validator.validate_scene_sequence(PROBLEMATIC_SCENE_SEQUENCE)
    
    # 打印验证结果
    print_subheader("验证结果")
    print_result_item("检测到的问题总数", results["error_count"])
    print_result_item("时间问题数", results.get("time_errors", 0))
    print_result_item("空间问题数", results.get("space_errors", 0))
    print_result_item("角色问题数", results.get("character_errors", 0))
    
    # 打印详细错误
    if results["errors"]:
        print("\n详细错误信息:")
        for i, error in enumerate(results["errors"]):
            print(f"{Fore.RED}{i+1}. {error['message']} (类型: {error['type']}){Style.RESET_ALL}")
    
    # 获取第一个错误的修复建议
    if results["errors"] and len(PROBLEMATIC_SCENE_SEQUENCE) >= 2:
        first_error = results["errors"][0]
        error_index = first_error.get("scene_index", 1)
        if error_index > 0 and error_index < len(PROBLEMATIC_SCENE_SEQUENCE):
            prev_scene = PROBLEMATIC_SCENE_SEQUENCE[error_index-1]
            curr_scene = PROBLEMATIC_SCENE_SEQUENCE[error_index]
            
            suggestions = validator.generate_fix_suggestions(prev_scene, curr_scene, [first_error["message"]])
            print_suggestions(suggestions, "修复建议")

def demonstrate_narrative_analysis():
    """演示叙事连贯性分析"""
    print_colored_header("叙事连贯性分析")
    
    validator = SpatiotemporalValidator()
    
    # 打印完整场景序列
    print_scenes(COMPLEX_SCENE_SEQUENCE, "完整场景序列")
    
    # 分析叙事连贯性
    narrative_results = validator.analyze_narrative_coherence(COMPLEX_SCENE_SEQUENCE)
    
    # 打印分析结果
    print_subheader("叙事分析结果")
    print_result_item("叙事评分", f"{narrative_results['narrative_score']:.1f}/10.0")
    
    # 打印优势
    if narrative_results["strengths"]:
        print(f"\n{Fore.GREEN}叙事优势:{Style.RESET_ALL}")
        for strength in narrative_results["strengths"]:
            print(f"+ {strength}")
    
    # 打印结构问题
    if narrative_results["structure_issues"]:
        print(f"\n{Fore.YELLOW}结构问题:{Style.RESET_ALL}")
        for issue in narrative_results["structure_issues"]:
            print(f"- {issue}")
    
    # 打印建议
    print_suggestions(narrative_results["suggestions"], "叙事改进建议")
    
def demonstrate_visual_continuity():
    """演示视觉连续性分析"""
    print_colored_header("视觉连续性分析")
    
    validator = SpatiotemporalValidator()
    
    # 分析问题场景序列的视觉连续性
    print_scenes(PROBLEMATIC_SCENE_SEQUENCE, "问题场景序列")
    
    visual_results = validator.analyze_visual_continuity(PROBLEMATIC_SCENE_SEQUENCE)
    
    # 打印分析结果
    print_subheader("视觉连续性分析结果")
    
    if visual_results["visual_continuity_issues"]:
        print(f"{Fore.YELLOW}检测到的视觉连续性问题:{Style.RESET_ALL}")
        for issue in visual_results["visual_continuity_issues"]:
            print(f"- {issue}")
    else:
        print(f"{Fore.GREEN}未检测到视觉连续性问题{Style.RESET_ALL}")
    
    # 打印建议
    print_suggestions(visual_results["suggestions"], "视觉连续性改进建议")

def demonstrate_editing_patterns():
    """演示剪辑模式分析"""
    print_colored_header("剪辑模式分析")
    
    validator = SpatiotemporalValidator()
    
    # 分析两个场景序列的剪辑模式
    for i, scenes in enumerate([COMPLEX_SCENE_SEQUENCE, PROBLEMATIC_SCENE_SEQUENCE]):
        title = "完整场景序列" if i == 0 else "问题场景序列"
        print_subheader(title)
        
        pattern_results = validator.analyze_editing_patterns(scenes)
        
        # 打印识别到的模式
        if pattern_results["identified_patterns"]:
            print(f"{Fore.CYAN}识别到的剪辑模式:{Style.RESET_ALL}")
            for pattern in pattern_results["identified_patterns"]:
                print(f"- {pattern}")
        else:
            print(f"{Fore.CYAN}未识别到明显的剪辑模式{Style.RESET_ALL}")
        
        # 打印建议
        print_suggestions(pattern_results["suggestions"], "剪辑改进建议")
        print("\n" + "-" * 70)

def demonstrate_comprehensive_analysis():
    """演示综合分析"""
    print_colored_header("综合场景分析", Fore.MAGENTA)
    
    validator = SpatiotemporalValidator()
    
    # 选择要分析的场景序列
    scenes = PROBLEMATIC_SCENE_SEQUENCE
    print_scenes(scenes, "待分析场景序列")
    
    # 执行所有分析
    basic_results = validator.validate_scene_sequence(scenes)
    narrative_results = validator.analyze_narrative_coherence(scenes)
    visual_results = validator.analyze_visual_continuity(scenes)
    pattern_results = validator.analyze_editing_patterns(scenes)
    
    # 打印综合分析报告
    print_subheader("综合分析报告", Fore.MAGENTA)
    
    # 基本时空逻辑
    print(f"{Fore.CYAN}基本时空逻辑:{Style.RESET_ALL}")
    print_result_item("  检测到的问题", basic_results["error_count"])
    error_types = []
    if basic_results.get("time_errors", 0) > 0: error_types.append("时间连续性")
    if basic_results.get("space_errors", 0) > 0: error_types.append("空间连续性")
    if basic_results.get("character_errors", 0) > 0: error_types.append("角色一致性")
    if error_types:
        print_result_item("  主要问题类型", ", ".join(error_types))
    
    # 叙事结构
    print(f"\n{Fore.CYAN}叙事结构:{Style.RESET_ALL}")
    print_result_item("  叙事评分", f"{narrative_results['narrative_score']:.1f}/10.0")
    if narrative_results["structure_issues"]:
        print_result_item("  结构问题数", len(narrative_results["structure_issues"]))
    
    # 视觉连续性
    print(f"\n{Fore.CYAN}视觉连续性:{Style.RESET_ALL}")
    print_result_item("  视觉问题数", len(visual_results["visual_continuity_issues"]))
    
    # 剪辑模式
    print(f"\n{Fore.CYAN}剪辑模式:{Style.RESET_ALL}")
    if pattern_results["identified_patterns"]:
        print_result_item("  识别到的模式", ", ".join(pattern_results["identified_patterns"]))
    
    # 汇总所有建议
    all_suggestions = []
    all_suggestions.extend([f"[时空逻辑] {s}" for s in [s for err in basic_results["errors"] for s in validator.generate_fix_suggestions(scenes[err["scene_index"]-1] if err["scene_index"] > 0 else {}, scenes[err["scene_index"]] if err["scene_index"] < len(scenes) else {}, [err["message"]])]])
    all_suggestions.extend([f"[叙事结构] {s}" for s in narrative_results["suggestions"]])
    all_suggestions.extend([f"[视觉连续性] {s}" for s in visual_results["suggestions"]])
    all_suggestions.extend([f"[剪辑模式] {s}" for s in pattern_results["suggestions"]])
    
    # 打印优先级最高的建议
    print_suggestions(all_suggestions[:5], "优先改进建议")

def main():
    """主函数"""
    print_colored_header("高级时空连续性验证器演示", Fore.MAGENTA, "=")
    
    # 演示基本验证
    demonstrate_basic_validation()
    
    # 演示叙事分析
    demonstrate_narrative_analysis()
    
    # 演示视觉连续性分析
    demonstrate_visual_continuity()
    
    # 演示剪辑模式分析
    demonstrate_editing_patterns()
    
    # 演示综合分析
    demonstrate_comprehensive_analysis()

if __name__ == "__main__":
    main() 