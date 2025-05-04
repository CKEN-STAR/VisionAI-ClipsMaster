#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
内容变形器演示脚本

展示如何使用动态内容变形器根据用户偏好调整内容，
包括情感增强、节奏调整和文化本地化等变形策略。
"""

import os
import sys
import json
import time
from pprint import pprint
from typing import Dict, Any, List

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.audience.content_morpher import (
    get_content_morpher, morph_content, apply_user_preferences,
    amplify_emotion, adjust_pacing, replace_cultural_references
)
from src.audience.profile_builder import get_user_profile
from src.audience.behavior_decoder import get_user_preferences
from src.audience.mock_data_generator import generate_mock_content

def print_section(title: str):
    """打印分节标题"""
    print("\n" + "=" * 50)
    print(f" {title} ".center(50, "="))
    print("=" * 50 + "\n")

def print_content_summary(content: Dict[str, Any], title: str = "内容摘要"):
    """打印内容摘要"""
    print(f"\n--- {title} ---")
    print(f"ID: {content.get('id', 'unknown')}")
    print(f"标题: {content.get('title', 'unknown')}")
    print(f"描述: {content.get('description', 'unknown')}")
    
    # 打印场景信息
    print("\n场景:")
    for i, scene in enumerate(content.get("scenes", [])[:3]):
        print(f"  场景 {i+1}: {scene.get('duration', 0):.1f}秒"
              f" ({scene.get('adjusted_duration', 'N/A'):.1f}秒调整后)" 
              if "adjusted_duration" in scene else
              f"  场景 {i+1}: {scene.get('duration', 0):.1f}秒")
        if "emotion" in scene:
            emo = scene["emotion"]
            print(f"    情感: {emo.get('type', 'unknown')}, "
                  f"强度: {emo.get('intensity', 0):.2f}, "
                  f"分数: {emo.get('score', 0):.2f}")
    
    # 打印情感信息
    if "emotions" in content:
        print("\n整体情感:")
        for emotion in content.get("emotions", [])[:3]:
            print(f"  {emotion.get('type', 'unknown')}: "
                  f"强度: {emotion.get('intensity', 0):.2f}, "
                  f"分数: {emotion.get('score', 0):.2f}")
    
    # 打印对话样本
    if "dialogues" in content:
        print("\n对话样本:")
        for dialogue in content.get("dialogues", [])[:2]:
            print(f"  \"{dialogue.get('text', '')}\"")
    
    print("\n")

def demonstrate_emotion_amplification():
    """演示情感增强功能"""
    print_section("情感增强演示")
    
    # 获取示例内容
    print("生成示例内容...")
    content = generate_mock_content("悲情爱情故事")
    
    # 打印原始内容
    print_content_summary(content, "原始内容")
    
    # 应用情感增强
    print("应用情感增强变形...")
    amplified = amplify_emotion(content, factor=1.8)
    
    # 打印增强后的内容
    print_content_summary(amplified, "情感增强后的内容")
    
    # 展示效果对比
    print("效果对比 (原始 vs 增强):")
    for i, (orig, ampl) in enumerate(zip(content.get("emotions", []), amplified.get("emotions", []))):
        print(f"情感 {i+1} ({orig.get('type', 'unknown')}): "
              f"强度 {orig.get('intensity', 0):.2f} → {ampl.get('intensity', 0):.2f}, "
              f"分数 {orig.get('score', 0):.2f} → {ampl.get('score', 0):.2f}")

def demonstrate_pacing_adjustment():
    """演示节奏调整功能"""
    print_section("节奏调整演示")
    
    # 获取示例内容
    print("生成示例内容...")
    content = generate_mock_content("悬疑动作片段")
    
    # 打印原始内容
    print_content_summary(content, "原始内容")
    
    # 应用快节奏调整
    print("应用快节奏调整...")
    fast_paced = adjust_pacing(content, target_bpm=150)
    
    # 打印调整后的内容
    print_content_summary(fast_paced, "快节奏调整后的内容")
    
    # 应用慢节奏调整
    print("应用慢节奏调整...")
    slow_paced = adjust_pacing(content, target_bpm=80)
    
    # 打印调整后的内容
    print_content_summary(slow_paced, "慢节奏调整后的内容")
    
    # 展示效果对比
    print("效果对比 (原始场景持续时间 vs 快节奏 vs 慢节奏):")
    for i, scene in enumerate(content.get("scenes", [])[:3]):
        orig_dur = scene.get("duration", 0)
        fast_dur = fast_paced["scenes"][i].get("adjusted_duration", 0) if i < len(fast_paced.get("scenes", [])) else 0
        slow_dur = slow_paced["scenes"][i].get("adjusted_duration", 0) if i < len(slow_paced.get("scenes", [])) else 0
        print(f"场景 {i+1}: {orig_dur:.1f}秒 → 快节奏: {fast_dur:.1f}秒, 慢节奏: {slow_dur:.1f}秒")

def demonstrate_cultural_localization():
    """演示文化本地化功能"""
    print_section("文化本地化演示")
    
    # 创建包含文化引用的示例内容
    content = {
        "id": "cultural_demo_1",
        "title": "春节的故事",
        "description": "一个关于中国新年的温馨故事",
        "scenes": [
            {
                "id": "scene_1",
                "duration": 10.0,
                "emotion": {"type": "喜悦", "intensity": 0.7}
            }
        ],
        "dialogues": [
            {
                "id": "dialogue_1",
                "text": "春节快到了，我们要准备红包和年夜饭。",
                "start": 2.0,
                "end": 5.0
            },
            {
                "id": "dialogue_2",
                "text": "大家一起贴春联，象征新的一年的到来。",
                "start": 7.0,
                "end": 10.0
            }
        ],
        "narration": [
            {
                "id": "narration_1",
                "text": "在中国传统文化中，春节是最重要的节日。",
                "start": 0.0,
                "end": 3.0
            }
        ]
    }
    
    # 打印原始内容
    print_content_summary(content, "原始内容 (中文文化引用)")
    
    # 应用文化本地化 - 中文到英文
    print("应用文化本地化 (中文→英文)...")
    localized_en = replace_cultural_references(content, "zh", "en")
    
    # 打印本地化后的内容
    print_content_summary(localized_en, "本地化后的内容 (英文文化引用)")
    
    # 创建包含西方文化引用的示例内容
    western_content = {
        "id": "cultural_demo_2",
        "title": "Christmas Story",
        "description": "A heartwarming tale of Christmas celebration",
        "scenes": [
            {
                "id": "scene_1",
                "duration": 10.0,
                "emotion": {"type": "joy", "intensity": 0.7}
            }
        ],
        "dialogues": [
            {
                "id": "dialogue_1",
                "text": "Christmas is coming, we need to prepare gifts and turkey dinner.",
                "start": 2.0,
                "end": 5.0
            },
            {
                "id": "dialogue_2",
                "text": "Let's decorate the Christmas tree together.",
                "start": 7.0,
                "end": 10.0
            }
        ],
        "narration": [
            {
                "id": "narration_1",
                "text": "Christmas is the most important holiday in western tradition.",
                "start": 0.0,
                "end": 3.0
            }
        ]
    }
    
    # 打印原始内容
    print_content_summary(western_content, "原始内容 (英文文化引用)")
    
    # 应用文化本地化 - 英文到中文
    print("应用文化本地化 (英文→中文)...")
    localized_zh = replace_cultural_references(western_content, "en", "zh")
    
    # 打印本地化后的内容
    print_content_summary(localized_zh, "本地化后的内容 (中文文化引用)")

def demonstrate_user_preference_based_morphing():
    """演示基于用户偏好的内容变形"""
    print_section("用户偏好驱动的内容变形演示")
    
    # 获取示例内容
    print("生成示例内容...")
    content = generate_mock_content("动作冒险片段")
    
    # 打印原始内容
    print_content_summary(content, "原始内容")
    
    # 创建示例用户偏好
    user_preferences = {
        "user_id": "demo_user_123",
        "basic_info": {
            "age_group": "25-34",
            "gender": "female",
            "region": "east"
        },
        "emotion_preferences": {
            "primary_emotions": {
                "joy": {"score": 0.8, "strength": "strong_like"},
                "tension": {"score": 0.6, "strength": "like"}
            },
            "intensity": 0.8,
            "valence": 0.7
        },
        "pacing_preferences": {
            "overall_pace": {
                "fast": {"score": 0.8, "strength": "strong_like"},
                "medium": {"score": 0.4, "strength": "neutral"},
                "slow": {"score": 0.2, "strength": "dislike"}
            },
            "scene_duration": {
                "preferred": 4.0
            }
        }
    }
    
    print("用户偏好摘要:")
    print(f"- 情感强度偏好: {user_preferences['emotion_preferences']['intensity']:.1f}/1.0")
    print(f"- 主要情感偏好: 喜悦({user_preferences['emotion_preferences']['primary_emotions']['joy']['score']:.1f}), "
          f"紧张({user_preferences['emotion_preferences']['primary_emotions']['tension']['score']:.1f})")
    print(f"- 节奏偏好: 快({user_preferences['pacing_preferences']['overall_pace']['fast']['score']:.1f}), "
          f"中({user_preferences['pacing_preferences']['overall_pace']['medium']['score']:.1f}), "
          f"慢({user_preferences['pacing_preferences']['overall_pace']['slow']['score']:.1f})")
    
    # 获取内容变形器
    morpher = get_content_morpher()
    
    # 应用用户偏好
    print("\n根据用户偏好应用变形策略...")
    morphed_content = morpher.apply_user_preferences(content, user_preferences)
    
    # 打印变形后的内容
    print_content_summary(morphed_content, "基于用户偏好变形后的内容")
    
    # 查看策略权重
    print("应用的策略权重:")
    strategy_weights = morpher._preferences_to_strategies(user_preferences)
    for strategy, weight in strategy_weights.items():
        print(f"- {strategy}: {weight:.2f}")

def demonstrate_combined_strategies():
    """演示组合应用多种变形策略"""
    print_section("组合变形策略演示")
    
    # 获取示例内容
    print("生成示例内容...")
    content = generate_mock_content("剧情片段")
    
    # 打印原始内容
    print_content_summary(content, "原始内容")
    
    # 定义策略权重
    strategy_weights = {
        "情感极化": 0.8,   # 情感增强
        "快节奏": 0.7,    # 快节奏调整
        "西方化": 0.9     # 文化本地化
    }
    
    print("应用的策略权重:")
    for strategy, weight in strategy_weights.items():
        print(f"- {strategy}: {weight:.2f}")
    
    # 获取内容变形器
    morpher = get_content_morpher()
    
    # 应用组合策略
    print("\n组合应用多种变形策略...")
    morphed_content = morpher.morph_content(content, strategy_weights)
    
    # 打印变形后的内容
    print_content_summary(morphed_content, "应用组合策略后的内容")


if __name__ == "__main__":
    try:
        # 演示情感增强
        demonstrate_emotion_amplification()
        
        # 演示节奏调整
        demonstrate_pacing_adjustment()
        
        # 演示文化本地化
        demonstrate_cultural_localization()
        
        # 演示基于用户偏好的变形
        demonstrate_user_preference_based_morphing()
        
        # 演示组合策略
        demonstrate_combined_strategies()
        
        print("\n演示完成。内容变形器功能展示成功！")
        
    except Exception as e:
        print(f"演示过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc() 