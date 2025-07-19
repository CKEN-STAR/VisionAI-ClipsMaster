#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
情感节奏调节器演示

演示如何使用情感节奏调节器调整场景的播放时长，以达到最佳情感表达效果。
展示不同情感模式下的节奏调整效果。
"""

import sys
import json
import os
import pprint
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Dict, List, Any

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).resolve().parent.parent))

# 导入情感节奏调节器
from src.emotion.rhythm_tuner import EmotionRhythm, adjust_pacing, process_scene_sequence

def print_json(data, title=None):
    """打印格式化的JSON数据"""
    if title:
        print(f"\n===== {title} =====")
    print(json.dumps(data, ensure_ascii=False, indent=2))

def visualize_rhythm(scenes, adjusted_scenes, title="情感节奏对比"):
    """可视化原始和调整后的场景节奏"""
    if not scenes or not adjusted_scenes:
        return
    
    # 提取原始持续时间和调整后的持续时间
    original_durations = []
    adjusted_durations = []
    emotion_scores = []
    scene_names = []
    
    for i, (orig, adj) in enumerate(zip(scenes, adjusted_scenes)):
        # 原始持续时间
        orig_dur = orig["end"] - orig["start"] if "end" in orig and "start" in orig else 1.0
        original_durations.append(orig_dur)
        
        # 调整后持续时间
        adj_dur = adj.get("adjusted_duration", orig_dur)
        adjusted_durations.append(adj_dur)
        
        # 情感强度
        emotion = adj.get("emotion", {"score": 0.5})
        score = emotion.get("score", 0.5) if isinstance(emotion, dict) else 0.5
        emotion_scores.append(score)
        
        # 场景名称
        name = f"场景{i+1}"
        if "id" in orig:
            name = orig["id"]
        elif "text" in orig and len(orig["text"]) > 10:
            name = orig["text"][:10] + "..."
        scene_names.append(name)
    
    # 创建图表
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), gridspec_kw={'height_ratios': [3, 1]})
    
    # 场景持续时间比较
    x = range(len(scenes))
    width = 0.35
    
    bars1 = ax1.bar(np.array(x) - width/2, original_durations, width, label='原始时长')
    bars2 = ax1.bar(np.array(x) + width/2, adjusted_durations, width, label='调整后时长')
    
    # 添加标签和图例
    ax1.set_ylabel('持续时间 (秒)')
    ax1.set_title(f'{title} - 场景持续时间对比')
    ax1.set_xticks(x)
    ax1.set_xticklabels(scene_names, rotation=45, ha='right')
    ax1.legend()
    
    # 添加调整百分比标签
    for i, (bar1, bar2) in enumerate(zip(bars1, bars2)):
        height1 = bar1.get_height()
        height2 = bar2.get_height()
        percent = (height2 - height1) / height1 * 100
        ax1.text(bar2.get_x() + bar2.get_width()/2., height2 + 0.1,
                f'{percent:.1f}%', ha='center', va='bottom')
    
    # 情感强度图
    ax2.plot(x, emotion_scores, 'ro-', label='情感强度')
    ax2.set_ylim(0, 1.0)
    ax2.set_ylabel('情感强度')
    ax2.set_xlabel('场景序列')
    ax2.set_xticks(x)
    ax2.set_xticklabels(scene_names, rotation=45, ha='right')
    ax2.grid(True, linestyle='--', alpha=0.7)
    
    # 在图中添加情感类型标注
    for i, scene in enumerate(adjusted_scenes):
        emotion_type = scene.get("emotion", {}).get("type", "")
        if emotion_type:
            ax2.annotate(emotion_type, 
                        (i, emotion_scores[i]),
                        textcoords="offset points",
                        xytext=(0, 10), 
                        ha='center')
    
    plt.tight_layout()
    plt.savefig("emotion_rhythm_visualization.png")
    print(f"节奏可视化图表已保存为: emotion_rhythm_visualization.png")

def demo_single_scene_adjustment():
    """演示单个场景的节奏调整"""
    print("\n[1] 单个场景节奏调整演示")
    
    # 创建测试场景
    scenes = [
        {
            "id": "悲伤场景",
            "text": "雨水打在窗户上，他静静地看着远方，眼中满是思念和悲伤。",
            "start": 0.0,
            "end": 10.0,
            "emotion": {
                "type": "悲伤",
                "score": 0.85
            }
        },
        {
            "id": "紧张场景",
            "text": "他的心跳加速，手心冒汗，死死盯着倒计时，还有最后十秒！",
            "start": 0.0,
            "end": 10.0,
            "emotion": {
                "type": "紧张",
                "score": 0.9
            }
        },
        {
            "id": "喜悦场景",
            "text": "她终于考上了梦寐以求的大学，激动地跳了起来，欢呼着拥抱父母。",
            "start": 0.0,
            "end": 10.0,
            "emotion": {
                "type": "喜悦",
                "score": 0.8
            }
        }
    ]
    
    # 创建节奏调节器
    rhythm_tuner = EmotionRhythm()
    
    # 处理每个场景并显示结果
    adjusted_scenes = []
    
    for scene in scenes:
        adjusted_scene = rhythm_tuner.adjust_pacing(scene)
        adjusted_scenes.append(adjusted_scene)
        
        print(f"\n-- {scene['id']} 节奏调整 --")
        print(f"原始持续时间: {scene['end'] - scene['start']:.2f}秒")
        print(f"调整后持续时间: {adjusted_scene['adjusted_duration']:.2f}秒")
        print(f"情感类型: {scene['emotion']['type']}, 强度: {scene['emotion']['score']:.2f}")
        print(f"调整因子: {adjusted_scene['timing_factor']:.2f}")
        
        # 计算变化百分比
        original_duration = scene["end"] - scene["start"]
        adjusted_duration = adjusted_scene["adjusted_duration"]
        change_percent = (adjusted_duration - original_duration) / original_duration * 100
        print(f"变化百分比: {change_percent:.1f}%")
    
    # 可视化结果
    visualize_rhythm(scenes, adjusted_scenes, "单一场景情感节奏调整")

def demo_scene_sequence():
    """演示场景序列的节奏处理"""
    print("\n[2] 场景序列节奏处理演示")
    
    # 创建测试场景序列 - 故事情节
    story_scenes = [
        {
            "id": "开场",
            "text": "清晨，阳光透过窗帘洒在房间里，小明伸了个懒腰准备迎接新的一天。",
            "start": 0.0,
            "end": 8.0,
            "emotion": {
                "type": "中性",
                "score": 0.3
            }
        },
        {
            "id": "发现",
            "text": "打开手机，小明惊讶地发现自己的银行账户上多了一笔巨款。",
            "start": 8.0,
            "end": 15.0,
            "emotion": {
                "type": "惊讶",
                "score": 0.7
            }
        },
        {
            "id": "疑惑",
            "text": "他反复查看转账记录，确认这笔钱确实是莫名其妙出现的，这让他既兴奋又忐忑。",
            "start": 15.0,
            "end": 22.0,
            "emotion": {
                "type": "紧张",
                "score": 0.5
            }
        },
        {
            "id": "冲突",
            "text": "电话突然响起，对方自称是银行工作人员，称这笔钱是系统错误，要求立即归还，否则将承担法律后果。",
            "start": 22.0,
            "end": 30.0,
            "emotion": {
                "type": "恐惧",
                "score": 0.75
            }
        },
        {
            "id": "纠结",
            "text": "小明犹豫了，这笔钱如果是自己的该多好，但如果是银行错误，拿了可能会惹上麻烦。",
            "start": 30.0,
            "end": 40.0,
            "emotion": {
                "type": "紧张",
                "score": 0.85
            }
        },
        {
            "id": "决定",
            "text": "经过一番思想斗争，小明决定联系银行核实情况，如果真是错误就归还这笔钱。",
            "start": 40.0,
            "end": 48.0,
            "emotion": {
                "type": "悲伤",
                "score": 0.4
            }
        },
        {
            "id": "转折",
            "text": "银行确认这是一笔意外的保险理赔，因为小明多年前的一份保险到期，这笔钱确实属于他！",
            "start": 48.0,
            "end": 56.0,
            "emotion": {
                "type": "惊讶",
                "score": 0.9
            }
        },
        {
            "id": "结局",
            "text": "小明激动地握着手机，脸上露出灿烂的笑容，他终于可以实现自己的梦想了！",
            "start": 56.0,
            "end": 65.0,
            "emotion": {
                "type": "喜悦",
                "score": 0.95
            }
        }
    ]
    
    # 演示不同节奏模式
    rhythm_tuner = EmotionRhythm()
    
    # 1. 自动选择节奏模式
    print("\n-- 自动选择节奏模式 --")
    auto_adjusted = rhythm_tuner.process_scene_sequence(story_scenes)
    pattern = auto_adjusted[0]["applied_rhythm_pattern"]
    print(f"自动选择的节奏模式: {pattern}")
    
    # 2. 指定节奏模式
    rhythm_patterns = ["emotional_crescendo", "emotional_wave", "emotional_focus"]
    
    for pattern in rhythm_patterns:
        print(f"\n-- 应用'{pattern}'节奏模式 --")
        adjusted_scenes = rhythm_tuner.process_scene_sequence(story_scenes, pattern)
        
        # 显示每个场景的调整结果摘要
        print(f"\n{pattern}模式下的场景调整:")
        for i, scene in enumerate(adjusted_scenes):
            original_duration = scene["rhythm_adjustment"]["original_duration"]
            new_duration = scene["adjusted_duration"]
            change = (new_duration - original_duration) / original_duration * 100
            
            print(f"{i+1}. {scene['id']}: {original_duration:.1f}秒 → {new_duration:.1f}秒 ({change:+.1f}%)")
        
        # 可视化
        visualize_rhythm(story_scenes, adjusted_scenes, f"{pattern}节奏模式")

def demo_emotional_coherence():
    """演示情感连贯性处理"""
    print("\n[3] 情感连贯性处理演示")
    
    # 创建一个情感变化剧烈的测试场景序列
    volatile_scenes = [
        {
            "id": "平静",
            "text": "湖面平静如镜，倒映着蓝天白云。",
            "start": 0.0,
            "end": 5.0,
            "emotion": {
                "type": "中性",
                "score": 0.2
            }
        },
        {
            "id": "惊吓",
            "text": "突然，一声巨响！所有人都被吓得跳了起来！",
            "start": 5.0,
            "end": 8.0,
            "emotion": {
                "type": "惊讶",
                "score": 0.9
            }
        },
        {
            "id": "恐惧",
            "text": "浓烟从远处升起，人们惊恐地四处逃窜。",
            "start": 8.0,
            "end": 12.0,
            "emotion": {
                "type": "恐惧",
                "score": 0.8
            }
        },
        {
            "id": "平静",
            "text": "原来只是一场烟花表演的预热，人们松了一口气。",
            "start": 12.0,
            "end": 16.0,
            "emotion": {
                "type": "中性",
                "score": 0.3
            }
        },
        {
            "id": "狂喜",
            "text": "绚丽的烟花在夜空绽放，观众们发出阵阵欢呼，掌声雷动！",
            "start": 16.0,
            "end": 25.0,
            "emotion": {
                "type": "喜悦",
                "score": 0.95
            }
        }
    ]
    
    # 创建节奏调节器，并设置两种模式进行对比
    rhythm_tuner = EmotionRhythm()
    
    # 1. 不启用连贯性保证
    print("\n-- 不启用连贯性保证 --")
    rhythm_tuner.config["coherence"]["enforce_continuity"] = False
    non_coherent = rhythm_tuner.process_scene_sequence(volatile_scenes)
    
    # 2. 启用连贯性保证
    print("\n-- 启用连贯性保证 --")
    rhythm_tuner.config["coherence"]["enforce_continuity"] = True
    coherent = rhythm_tuner.process_scene_sequence(volatile_scenes)
    
    # 比较两种处理方式的结果
    print("\n情感连贯性对比:")
    print(f"{'场景':<8} {'原始时长':<8} {'无连贯性':<10} {'有连贯性':<10} {'差异':<8}")
    print("-" * 50)
    
    for i, (orig, non_coh, coh) in enumerate(zip(volatile_scenes, non_coherent, coherent)):
        orig_dur = orig["end"] - orig["start"]
        non_coh_dur = non_coh["adjusted_duration"]
        coh_dur = coh["adjusted_duration"]
        diff = (coh_dur - non_coh_dur) / non_coh_dur * 100
        
        print(f"{orig['id']:<8} {orig_dur:<8.1f} {non_coh_dur:<10.1f} {coh_dur:<10.1f} {diff:+.1f}%")
    
    # 检查是否有场景被连贯性调整
    coherence_adjusted = [s for s in coherent if s.get("rhythm_adjustment", {}).get("coherence_adjusted", False)]
    if coherence_adjusted:
        print(f"\n{len(coherence_adjusted)}个场景被连贯性规则调整")
        for scene in coherence_adjusted:
            print(f"- {scene['id']}")
    
    # 可视化非连贯性的结果
    visualize_rhythm(volatile_scenes, non_coherent, "无连贯性保证的节奏调整")
    
    # 可视化连贯性的结果  
    visualize_rhythm(volatile_scenes, coherent, "有连贯性保证的节奏调整")

def main():
    """主函数"""
    print("===== 情感节奏调节器演示 =====")
    
    # 演示单个场景的节奏调整
    demo_single_scene_adjustment()
    
    # 演示场景序列的节奏处理和不同模式效果
    demo_scene_sequence()
    
    # 演示情感连贯性处理
    demo_emotional_coherence()
    
    print("\n===== 演示完成 =====")

if __name__ == "__main__":
    main() 