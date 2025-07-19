#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
多模态情感共振演示

此示例展示了多模态情感共振模块的基本功能，包括：
1. 单个场景的情感分析和效果增强
2. 多个场景的连续处理和情感流程分析
3. 脚本级别的情感共振处理
"""

import sys
import json
import os
import pprint
from pathlib import Path
from typing import Dict, Any

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.emotion.multimodal_resonance import (
    EmotionalResonance, 
    apply_multimodal_resonance,
    process_script_with_resonance
)

def print_json(data, title=None):
    """打印格式化的JSON数据"""
    if title:
        print(f"\n===== {title} =====")
    print(json.dumps(data, ensure_ascii=False, indent=2))

def demo_single_scene():
    """演示处理单个场景"""
    print("\n[1] 单个场景情感共振演示")
    
    # 创建测试场景 - 悲伤场景
    sad_scene = {
        "id": "scene_001",
        "text": "他站在雨中，泪水与雨水一起滑落脸颊，内心充满了对过去的思念和无尽的悔恨。",
        "video_path": "assets/videos/rain_scene.mp4",
        "duration": 15.0,
        "emotion": {
            "type": "悲伤",
            "intensity": 0.85
        }
    }
    
    # 创建测试场景 - 喜悦场景
    happy_scene = {
        "id": "scene_002",
        "text": "她兴奋地跑向终点线，欢呼雀跃，终于实现了自己多年的梦想，笑容灿烂如阳光。",
        "video_path": "assets/videos/victory_scene.mp4",
        "duration": 12.0,
        "emotion": {
            "type": "喜悦",
            "intensity": 0.9
        }
    }
    
    # 创建测试场景 - 紧张场景
    tense_scene = {
        "id": "scene_003",
        "text": "时间一分一秒地流逝，他的心跳越来越快，手心冒汗，死死盯着那个倒计时，生死就在这一刻。",
        "video_path": "assets/videos/countdown_scene.mp4",
        "duration": 18.0,
        "emotion": {
            "type": "紧张",
            "intensity": 0.95
        },
        "rhythm": {
            "peaks": [
                {"time": 5.5, "intensity": 0.7},
                {"time": 10.2, "intensity": 0.8},
                {"time": 16.5, "intensity": 0.95}
            ]
        }
    }
    
    # 使用情感共振器处理场景
    resonator = EmotionalResonance()
    
    # 处理并展示结果
    enhanced_sad = resonator.add_audiovisual_cues(sad_scene)
    print_json(enhanced_sad, "悲伤场景增强效果")
    
    enhanced_happy = resonator.add_audiovisual_cues(happy_scene)
    print_json(enhanced_happy, "喜悦场景增强效果")
    
    # 添加节奏同步
    enhanced_tense = resonator.add_audiovisual_cues(tense_scene)
    enhanced_tense = resonator.synchronize_emotion_with_rhythm(enhanced_tense)
    print_json(enhanced_tense, "紧张场景增强效果（带节奏同步）")

def demo_scene_sequence():
    """演示处理场景序列"""
    print("\n[2] 场景序列情感共振演示")
    
    # 创建场景序列 - 小故事
    scenes = [
        {
            "id": "story_001",
            "text": "早晨，阳光明媚，小明起床准备去公园。他的心情非常愉快，哼着小曲。",
            "video_path": "assets/videos/morning_scene.mp4",
            "duration": 8.0,
            "emotion": {
                "type": "喜悦",
                "intensity": 0.65
            }
        },
        {
            "id": "story_002",
            "text": "公园里人很多，小明开心地打招呼，享受着这美好的一天。",
            "video_path": "assets/videos/park_scene.mp4",
            "duration": 10.0,
            "emotion": {
                "type": "喜悦",
                "intensity": 0.7
            }
        },
        {
            "id": "story_003",
            "text": "突然，天空乌云密布，开始下起了大雨，所有人都措手不及。",
            "video_path": "assets/videos/sudden_rain.mp4",
            "duration": 6.0,
            "emotion": {
                "type": "惊讶",
                "intensity": 0.8
            },
            "rhythm": {
                "peaks": [
                    {"time": 3.0, "intensity": 0.8}
                ]
            }
        },
        {
            "id": "story_004",
            "text": "小明没带雨伞，浑身湿透，他失落地走在回家的路上。",
            "video_path": "assets/videos/wet_walking.mp4",
            "duration": 12.0,
            "emotion": {
                "type": "悲伤",
                "intensity": 0.6
            }
        },
        {
            "id": "story_005",
            "text": "回到家，小明换了干衣服，泡了一杯热茶，望着窗外的雨景，心情逐渐平静。",
            "video_path": "assets/videos/home_rain_window.mp4",
            "duration": 15.0,
            "emotion": {
                "type": "平静",
                "intensity": 0.4
            }
        }
    ]
    
    # 使用情感共振器处理场景组
    resonator = EmotionalResonance()
    enhanced_scenes = resonator.enhance_scene_group(scenes)
    
    # 显示处理结果摘要
    print("\n场景序列处理摘要:")
    for i, scene in enumerate(enhanced_scenes):
        emo_info = scene.get("applied_emotion_resonance", {})
        print(f"场景 {i+1}: {emo_info.get('type', '未知')} "
              f"(强度: {emo_info.get('intensity', 0):.2f})")
        
        # 显示转场信息
        if "emotion_transition" in scene:
            transition = scene["emotion_transition"]
            print(f"  转场: {transition['from']} → {transition['to']} "
                  f"({transition['transition_style']})")
        
        # 显示应用的效果数量
        video_effects = len(scene.get("video_effects", []))
        audio_effects = len(scene.get("audio_effects", []))
        print(f"  应用效果: 视频({video_effects}), 音频({audio_effects})")
    
    # 分析情感流程
    emotion_flow = resonator.analyze_emotion_flow(enhanced_scenes)
    print_json(emotion_flow, "情感流程分析")

def demo_full_script():
    """演示处理完整脚本"""
    print("\n[3] 完整脚本情感共振演示")
    
    # 创建一个简单的脚本
    script = {
        "title": "雨中邂逅",
        "author": "示例作者",
        "scenes": [
            {
                "id": "script_001",
                "text": "繁华的城市街道，人来人往。男主角匆忙走在路上，准备去参加重要的面试。",
                "video_path": "assets/videos/busy_street.mp4",
                "duration": 10.0
            },
            {
                "id": "script_002",
                "text": "天空突然下起大雨，男主角没带雨伞，四处寻找避雨的地方。",
                "video_path": "assets/videos/sudden_rain_man.mp4",
                "duration": 8.0,
                "rhythm": {
                    "peaks": [
                        {"time": 2.5, "intensity": 0.7}
                    ]
                }
            },
            {
                "id": "script_003",
                "text": "一家咖啡店门口，女主角注意到了男主角的窘境，犹豫了一下，然后走过去，将自己的伞递给了他。",
                "video_path": "assets/videos/umbrella_share.mp4",
                "duration": 15.0
            },
            {
                "id": "script_004",
                "text": "男主角受宠若惊，感激地接过伞，两人眼神交流，一种特别的感觉在两人之间流动。",
                "video_path": "assets/videos/eye_contact.mp4",
                "duration": 12.0
            },
            {
                "id": "script_005",
                "text": "女主角微笑着转身离开，消失在雨中。男主角看着手中的伞，若有所思。",
                "video_path": "assets/videos/leaving_rain.mp4",
                "duration": 10.0
            }
        ]
    }
    
    # 处理脚本
    enhanced_script = process_script_with_resonance(script)
    
    # 显示处理后脚本的主要情感流程
    emotion_flow = enhanced_script["emotion_flow"]
    print(f"\n脚本主要情感: {emotion_flow['dominant_emotion']}")
    print(f"情感变化模式: {emotion_flow['emotional_pattern']}")
    print(f"平均情感强度: {emotion_flow['avg_intensity']:.2f}")
    print(f"情感变化率: {emotion_flow['intensity_change_rate']:.2f}")
    print(f"情感高峰点数量: {len(emotion_flow['emotional_peaks'])}")
    
    # 显示每个场景的应用效果
    print("\n场景效果应用摘要:")
    for i, scene in enumerate(enhanced_script["scenes"]):
        emo_info = scene.get("applied_emotion_resonance", {})
        print(f"场景 {i+1}: {emo_info.get('type', '未知')} "
              f"(强度: {emo_info.get('intensity', 0):.2f})")
        
        # 统计应用的效果
        video_effects = scene.get("video_effects", [])
        audio_effects = scene.get("audio_effects", [])
        transitions = scene.get("transitions", [])
        
        print(f"  视频效果: {len(video_effects)}, 音频效果: {len(audio_effects)}, 转场: {len(transitions)}")
        
        # 显示部分效果详情
        if video_effects:
            print(f"  示例视频效果: {video_effects[0]['type']}")
        if audio_effects:
            print(f"  示例音频效果: {audio_effects[0]['type']}")

def main():
    """主函数"""
    print("=== 多模态情感共振模块演示 ===")
    
    # 运行单场景演示
    demo_single_scene()
    
    # 运行场景序列演示
    demo_scene_sequence()
    
    # 运行完整脚本演示
    demo_full_script()
    
    print("\n=== 演示完成 ===")

if __name__ == "__main__":
    main() 