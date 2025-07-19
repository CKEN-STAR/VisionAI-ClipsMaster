#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
情感演进监测器示例

演示如何使用情感演进监测器分析视频情感连贯性。
"""

import sys
import os
from pathlib import Path
import json
import matplotlib.pyplot as plt

# 直接导入我们的实现
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from emotion_continuity_standalone import (
    EmotionTransitionMonitor, 
    validate_emotion_continuity, 
    EmotionCategory
)

def load_demo_scenes():
    """加载示例场景数据"""
    # 场景1：平滑过渡的情感曲线（适合喜剧）
    smooth_comedy = [
        {"id": "comedy_1", "emotion_score": 0.4, "emotion_type": "happiness"},
        {"id": "comedy_2", "emotion_score": 0.5, "emotion_type": "happiness"},
        {"id": "comedy_3", "emotion_score": 0.7, "emotion_type": "happiness"},
        {"id": "comedy_4", "emotion_score": 0.6, "emotion_type": "surprise"},
        {"id": "comedy_5", "emotion_score": 0.8, "emotion_type": "happiness"},
        {"id": "comedy_6", "emotion_score": 0.7, "emotion_type": "happiness"},
    ]
    
    # 场景2：起伏较大的情感曲线（适合剧情片）
    drama_curve = [
        {"id": "drama_1", "emotion_score": 0.3, "emotion_type": "neutral"},
        {"id": "drama_2", "emotion_score": 0.5, "emotion_type": "happiness"},
        {"id": "drama_3", "emotion_score": 0.2, "emotion_type": "sadness"},
        {"id": "drama_4", "emotion_score": 0.1, "emotion_type": "sadness"},
        {"id": "drama_5", "emotion_score": 0.3, "emotion_type": "neutral"},
        {"id": "drama_6", "emotion_score": 0.6, "emotion_type": "anticipation"},
        {"id": "drama_7", "emotion_score": 0.8, "emotion_type": "happiness"},
        {"id": "drama_8", "emotion_score": 0.7, "emotion_type": "happiness"},
    ]
    
    # 场景3：情感跳跃问题（需要修正）
    problem_curve = [
        {"id": "problem_1", "emotion_score": 0.3, "emotion_type": "neutral"},
        {"id": "problem_2", "emotion_score": 0.9, "emotion_type": "happiness"},  # 跳跃过大
        {"id": "problem_3", "emotion_score": 0.2, "emotion_type": "sadness"},    # 跳跃过大
        {"id": "problem_4", "emotion_score": 0.7, "emotion_type": "surprise"},   # 跳跃过大
        {"id": "problem_5", "emotion_score": 0.4, "emotion_type": "neutral"},
    ]
    
    # 场景4：恐怖片的情感曲线
    horror_curve = [
        {"id": "horror_1", "emotion_score": 0.2, "emotion_type": "neutral"},
        {"id": "horror_2", "emotion_score": 0.3, "emotion_type": "anticipation"},
        {"id": "horror_3", "emotion_score": 0.5, "emotion_type": "fear"},
        {"id": "horror_4", "emotion_score": 0.4, "emotion_type": "neutral"},
        {"id": "horror_5", "emotion_score": 0.7, "emotion_type": "fear"},
        {"id": "horror_6", "emotion_score": 0.9, "emotion_type": "fear"},
        {"id": "horror_7", "emotion_score": 0.6, "emotion_type": "surprise"},
        {"id": "horror_8", "emotion_score": 0.8, "emotion_type": "fear"},
    ]
    
    return {
        "comedy": smooth_comedy,
        "drama": drama_curve,
        "problem": problem_curve,
        "horror": horror_curve
    }

def demo_emotion_flow_check():
    """演示情感流分析功能"""
    print("===== 情感流分析演示 =====\n")
    
    scenes = load_demo_scenes()
    monitor = EmotionTransitionMonitor()
    
    # 分析正常场景
    print("1. 分析平滑过渡的情感曲线（喜剧）")
    comedy_problems = monitor.check_emotion_flow(scenes["comedy"])
    if comedy_problems:
        print(f"发现 {len(comedy_problems)} 个问题:")
        for problem in comedy_problems:
            print(f"  - {problem['message']}")
    else:
        print("  ✓ 情感流连贯，未检测到问题")
    
    # 分析问题场景
    print("\n2. 分析存在问题的情感曲线")
    problem_issues = monitor.check_emotion_flow(scenes["problem"])
    print(f"发现 {len(problem_issues)} 个问题:")
    for issue in problem_issues:
        print(f"  - {issue['message']}")
        print(f"    在位置 {issue['position']}, 情感从 {issue['prev_score']} 跳跃到 {issue['current_score']}")

def demo_emotion_conflicts():
    """演示情感冲突分析功能"""
    print("\n===== 情感冲突分析演示 =====\n")
    
    scenes = load_demo_scenes()
    monitor = EmotionTransitionMonitor()
    
    # 分析情感冲突
    problem_conflicts = monitor.analyze_emotion_conflicts(scenes["problem"])
    print(f"问题场景中发现 {len(problem_conflicts)} 个情感冲突:")
    for conflict in problem_conflicts:
        print(f"  - {conflict['message']}")
        print(f"    情感类型从 {conflict['prev_emotion']} 变为 {conflict['current_emotion']}")

def demo_convenience_function():
    """演示便捷函数的使用方式"""
    print("\n===== 便捷函数使用演示 =====\n")
    
    scenes = load_demo_scenes()
    
    # 分析问题场景
    print("分析问题场景:")
    result = validate_emotion_continuity(scenes["problem"])
    
    # 输出主要分析结果
    print(f"检测到问题: {'是' if result['issues_detected'] else '否'}")
    print(f"情感跳跃问题数量: {len(result['emotion_jumps'])}")
    print(f"情感冲突问题数量: {len(result['emotion_conflicts'])}")

if __name__ == "__main__":
    print("情感演进监测器演示程序\n")
    
    # 创建输出目录
    os.makedirs("./output", exist_ok=True)
    
    # 运行演示
    demo_emotion_flow_check()
    demo_emotion_conflicts()
    demo_convenience_function()
    
    print("\n演示完成!") 