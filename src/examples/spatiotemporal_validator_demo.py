#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
时空连续性验证器演示

展示如何使用时空连续性验证器检查短剧混剪场景的时空逻辑合理性，
以及如何根据验证结果改进剧本。
"""

import os
import sys
import json
from pathlib import Path
import time
from datetime import datetime
from pprint import pprint

# 添加项目根目录到Python路径
current_dir = Path(__file__).resolve().parent
root_dir = current_dir.parent.parent
if str(root_dir) not in sys.path:
    sys.path.append(str(root_dir))

from src.logic.spatiotemporal_checker import (
    SpatiotemporalValidator,
    validate_spatiotemporal_logic,
    parse_time_ms,
    format_time_ms,
    preprocess_scene_data
)

# 示例场景数据，模拟一个短剧混剪的场景序列
EXAMPLE_SCENES = [
    {
        "id": "scene_001",
        "source_file": "episode1.mp4",
        "start": 0,
        "end": 12000,
        "location": "咖啡厅",
        "character": "林小美",
        "emotion": "期待",
        "text": "今天是我们第一次约会，我有点紧张。",
        "importance": 0.8
    },
    {
        "id": "scene_002",
        "source_file": "episode1.mp4",
        "start": 12000,
        "end": 25000,
        "location": "咖啡厅",
        "character": "张明",
        "emotion": "微笑",
        "text": "别紧张，我已经等这一天很久了。",
        "importance": 0.7
    },
    {
        "id": "scene_003",
        "source_file": "episode1.mp4",
        "start": 25000,
        "end": 38000,
        "location": "街道",  # 位置变化，但没有说明如何从咖啡厅到达街道
        "character": "林小美",
        "emotion": "惊喜",
        "text": "这条街真美啊!",
        "importance": 0.6
    },
    {
        "id": "scene_004",
        "source_file": "episode2.mp4",
        "start": 35000,  # 时间重叠问题
        "end": 48000,
        "location": "街道",
        "character": "张明",
        "emotion": "满足",
        "text": "我找了好久才发现这个地方。",
        "importance": 0.5
    },
    {
        "id": "scene_005",
        "source_file": "episode2.mp4",
        "start": 48000,
        "end": 60000,
        "location": "海边",  # 又一次位置变化
        "character": "林小美",
        "emotion": "哀伤",  # 情感突变
        "text": "我有些难过的事情想告诉你...",
        "importance": 0.9
    },
    {
        "id": "scene_006",
        "source_file": "episode3.mp4",
        "start": 60000,
        "end": 72000,
        "location": "海边",
        "character": "张明",
        "emotion": "关心",
        "text": "发生什么事了？你可以告诉我。",
        "importance": 0.8
    }
]

# 修复后的场景数据
FIXED_SCENES = [
    {
        "id": "scene_001",
        "source_file": "episode1.mp4",
        "start": 0,
        "end": 12000,
        "location": "咖啡厅",
        "character": "林小美",
        "emotion": "期待",
        "text": "今天是我们第一次约会，我有点紧张。",
        "importance": 0.8
    },
    {
        "id": "scene_002",
        "source_file": "episode1.mp4",
        "start": 12000,
        "end": 25000,
        "location": "咖啡厅",
        "character": "张明",
        "emotion": "微笑",
        "text": "别紧张，我已经等这一天很久了。",
        "importance": 0.7
    },
    {
        "id": "scene_transition_1",
        "source_file": "episode1.mp4",
        "start": 25000,
        "end": 28000,
        "location": "咖啡厅门口",
        "character": "林小美",
        "emotion": "轻松",
        "text": "我们出去走走吧，天气很好。",
        "props": ["walk"],
        "importance": 0.4
    },
    {
        "id": "scene_003",
        "source_file": "episode1.mp4",
        "start": 28000,
        "end": 38000,
        "location": "街道",
        "character": "林小美",
        "emotion": "惊喜",
        "text": "这条街真美啊!",
        "importance": 0.6
    },
    {
        "id": "scene_004",
        "source_file": "episode2.mp4",
        "start": 38000,  # 修复时间重叠
        "end": 48000,
        "location": "街道",
        "character": "张明",
        "emotion": "满足",
        "text": "我找了好久才发现这个地方。",
        "importance": 0.5
    },
    {
        "id": "scene_transition_2",
        "source_file": "episode2.mp4",
        "start": 48000,
        "end": 52000,
        "location": "出租车内",
        "character": "张明",
        "emotion": "期待",
        "text": "我们乘出租车去海边看日落吧。",
        "props": ["taxi"],
        "importance": 0.4
    },
    {
        "id": "scene_005_a",
        "source_file": "episode2.mp4",
        "start": 52000,
        "end": 56000,
        "location": "海边",
        "character": "林小美",
        "emotion": "沉思",  # 添加情感过渡
        "text": "这片海让我想起了很多事...",
        "importance": 0.7
    },
    {
        "id": "scene_005",
        "source_file": "episode2.mp4",
        "start": 56000,
        "end": 60000,
        "location": "海边",
        "character": "林小美",
        "emotion": "哀伤",
        "text": "我有些难过的事情想告诉你...",
        "importance": 0.9
    },
    {
        "id": "scene_006",
        "source_file": "episode3.mp4",
        "start": 60000,
        "end": 72000,
        "location": "海边",
        "character": "张明",
        "emotion": "关心",
        "text": "发生什么事了？你可以告诉我。",
        "importance": 0.8
    }
]

def print_divider(title=None):
    """打印分隔线"""
    width = 80
    if title:
        print(f"\n{'-' * ((width - len(title) - 2) // 2)} {title} {'-' * ((width - len(title) - 2) // 2)}\n")
    else:
        print(f"\n{'-' * width}\n")

def print_scene(scene, index=None):
    """格式化打印单个场景"""
    prefix = f"[场景 {index}] " if index is not None else ""
    
    # 格式化时间
    start_str = format_time_ms(scene["start"]) if isinstance(scene["start"], (int, float)) else scene["start"]
    end_str = format_time_ms(scene["end"]) if isinstance(scene["end"], (int, float)) else scene["end"]
    
    print(f"{prefix}ID: {scene['id']}")
    print(f"  时间: {start_str} → {end_str}")
    print(f"  位置: {scene.get('location', '未知')}")
    print(f"  角色: {scene.get('character', '未知')}")
    print(f"  情感: {scene.get('emotion', '未知')}")
    
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
        print_divider(title)
    
    for i, scene in enumerate(scenes):
        print_scene(scene, i+1)
        if i < len(scenes) - 1:
            print()  # 场景之间空一行

def print_validation_results(results):
    """格式化打印验证结果"""
    print_divider("验证结果")
    print(f"总场景数: {results['scene_count']}")
    print(f"检测到的问题数: {results['error_count']}")
    print(f"  时间问题: {results.get('time_errors', 0)}")
    print(f"  空间问题: {results.get('space_errors', 0)}")
    print(f"  角色问题: {results.get('character_errors', 0)}")
    
    if results["errors"]:
        print("\n具体问题:")
        for i, error in enumerate(results["errors"]):
            print(f"  {i+1}. {error['message']}")
            print(f"     位置: 场景 {error['prev_scene_id']} → {error['curr_scene_id']}")

def demonstrate_validation():
    """演示时空连续性验证功能"""
    print_divider("时空连续性验证器演示")
    print("这个演示展示了如何使用时空连续性验证器检查短剧混剪场景的逻辑问题。")
    
    # 打印原始场景数据
    print_scenes(EXAMPLE_SCENES, "原始混剪场景")
    
    # 创建验证器
    validator = SpatiotemporalValidator(time_threshold=5000)  # 设置更短的时间阈值以便演示
    
    # 验证原始场景
    print_divider("验证原始场景")
    results = validator.validate_scene_sequence(EXAMPLE_SCENES)
    print_validation_results(results)
    
    # 生成修复建议
    print_divider("修复建议")
    for i in range(1, len(EXAMPLE_SCENES)):
        prev_scene = EXAMPLE_SCENES[i-1]
        curr_scene = EXAMPLE_SCENES[i]
        
        errors = validator.validate_scene_transition(prev_scene, curr_scene)
        if errors:
            print(f"场景 {prev_scene['id']} → {curr_scene['id']} 存在问题:")
            for error in errors:
                print(f"  - {error}")
            
            suggestions = validator.generate_fix_suggestions(prev_scene, curr_scene, errors)
            if suggestions:
                print("  修复建议:")
                for suggestion in suggestions:
                    print(f"    * {suggestion}")
            print()
    
    # 验证修复后的场景
    print_scenes(FIXED_SCENES, "修复后的场景")
    
    print_divider("验证修复后的场景")
    fixed_results = validator.validate_scene_sequence(FIXED_SCENES)
    print_validation_results(fixed_results)
    
    # 展示效果对比
    print_divider("效果对比")
    print(f"原始场景问题数: {results['error_count']}")
    print(f"修复后场景问题数: {fixed_results['error_count']}")
    reduction = (results['error_count'] - fixed_results['error_count']) / max(1, results['error_count']) * 100
    print(f"问题减少率: {reduction:.1f}%")
    
    # 总结
    print_divider("总结")
    print("时空连续性验证可以帮助发现短剧混剪中的逻辑问题，提高视频质量。")
    print("主要检查的问题包括:")
    print("1. 时间连续性问题 - 场景时间重叠或倒退")
    print("2. 空间连续性问题 - 场景位置突变且没有合理解释")
    print("3. 角色连续性问题 - 角色情感状态突变")
    print("\n修复方法通常包括:")
    print("1. 调整场景时间，避免重叠")
    print("2. 添加过渡场景，解释位置变化")
    print("3. 添加情感过渡，使角色情感变化更自然")

if __name__ == "__main__":
    demonstrate_validation() 