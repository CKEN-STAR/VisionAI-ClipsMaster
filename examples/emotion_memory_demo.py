#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
情感记忆触发器演示脚本

展示如何使用情感记忆触发器为场景添加记忆钩子，增强观众情感共鸣。
演示不同类型的记忆触发点和自定义配置的使用方法。
"""

import os
import sys
import json
from typing import Dict, List, Any, Optional

# 添加项目根目录到系统路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.emotion.memory_trigger import EmotionMemoryTrigger, implant_memory_hooks
from src.config.constants import MEMORY_TRIGGER_TEMPLATES

def print_header(title: str) -> None:
    """打印带有格式的标题"""
    print("\n" + "=" * 60)
    print(f" {title} ".center(60, "="))
    print("=" * 60)

def print_scene_info(scene: Dict[str, Any], index: int) -> None:
    """打印场景信息"""
    emotion = scene.get("emotion", {})
    emotion_type = emotion.get("type", "未知")
    tags = scene.get("tags", [])
    text = scene.get("text", "")
    
    print(f"场景 {index}:")
    print(f"  情感类型: {emotion_type}")
    print(f"  标签: {', '.join(tags) if tags else '无'}")
    print(f"  描述文本: {text}")
    print()

def create_sample_scenes() -> List[Dict[str, Any]]:
    """创建样本场景列表"""
    return [
        {
            "id": "scene_1",
            "emotion": {
                "type": "neutral",
                "score": 0.5
            },
            "tags": ["开场"],
            "text": "主角走在街道上，神情平静，观察周围的环境。"
        },
        {
            "id": "scene_2",
            "emotion": {
                "type": "joy",
                "score": 0.7
            },
            "tags": ["胜利"],
            "text": "主角获得比赛冠军，举起奖杯，面带笑容。"
        },
        {
            "id": "scene_3",
            "emotion": {
                "type": "sadness",
                "score": 0.6
            },
            "tags": ["悲剧", "离别"],
            "text": "主角站在火车站台，目送远去的列车，眼含泪水。"
        },
        {
            "id": "scene_4",
            "emotion": {
                "type": "fear",
                "score": 0.8
            },
            "tags": ["危机"],
            "text": "主角在黑暗的房间中听到奇怪的声音，紧张地环顾四周。"
        },
        {
            "id": "scene_5",
            "emotion": {
                "type": "surprise",
                "score": 0.9
            },
            "tags": ["转折", "高潮"],
            "text": "门突然打开，意想不到的人物出现在门口，主角震惊地后退一步。"
        },
        {
            "id": "scene_6",
            "emotion": {
                "type": "anger",
                "score": 0.7
            },
            "tags": ["冲突"],
            "text": "主角与对手面对面站立，怒视对方，握紧拳头。"
        },
        {
            "id": "scene_7",
            "emotion": {
                "type": "neutral",
                "score": 0.4
            },
            "tags": ["结局"],
            "text": "主角站在山顶，望向远方的城市，表情平静而坚定。"
        }
    ]

def demonstrate_basic_triggers() -> None:
    """演示基本的记忆触发器功能"""
    print_header("基本记忆触发器演示")
    
    scenes = create_sample_scenes()
    
    print("原始场景信息:")
    for i, scene in enumerate(scenes, 1):
        print_scene_info(scene, i)
    
    # 创建记忆触发器
    trigger = EmotionMemoryTrigger()
    
    # 处理场景
    processed_scenes = trigger.process_scenes(scenes)
    
    print_header("添加记忆触发点后")
    
    print("处理后场景信息:")
    for i, scene in enumerate(processed_scenes, 1):
        print_scene_info(scene, i)
        # 如果有记忆触发器，打印额外信息
        if scene.get("has_memory_trigger"):
            trigger_type = scene.get("memory_trigger_type", "未知")
            print(f"  [已添加记忆触发点: {trigger_type}]")
            print()

def demonstrate_simple_function() -> None:
    """演示简单函数的使用"""
    print_header("简单函数调用演示")
    
    scenes = create_sample_scenes()
    
    # 使用简单函数处理场景
    processed_scenes = implant_memory_hooks(scenes)
    
    print("使用implant_memory_hooks函数处理后:")
    for i, scene in enumerate(processed_scenes, 1):
        # 只打印那些含有"高潮"或"胜利"标签的场景
        if "高潮" in scene.get("tags", []) or "胜利" in scene.get("tags", []):
            print_scene_info(scene, i)

def demonstrate_custom_config() -> None:
    """演示自定义配置的使用"""
    print_header("自定义配置演示")
    
    scenes = create_sample_scenes()
    
    # 创建自定义配置
    custom_config = {
        "language": "zh",
        "memory_tag_map": {
            # 添加新的记忆标签映射
            "危机": ["紧张", "恐慌", "危险"],
            "结局": ["结束", "收尾", "完结"]
        },
        "trigger_templates": {
            # 自定义模板
            "危机": [
                "[插入快速心跳声，引发观众紧张感]",
                "[光线闪烁，增强不安全感]"
            ],
            "结局": [
                "[音乐渐弱，给观众留下思考空间]",
                "[全景镜头缓慢后退，象征故事结束]"
            ]
        }
    }
    
    # 创建自定义触发器
    custom_trigger = EmotionMemoryTrigger(custom_config)
    
    # 处理场景
    processed_scenes = custom_trigger.process_scenes(scenes)
    
    print("使用自定义配置处理后:")
    for i, scene in enumerate(processed_scenes, 1):
        # 只显示包含"危机"或"结局"标签的场景
        if "危机" in scene.get("tags", []) or "结局" in scene.get("tags", []):
            print_scene_info(scene, i)

def demonstrate_memory_hooks_batch() -> None:
    """演示批量处理场景的效果"""
    print_header("批量处理场景演示")
    
    # 创建大量场景
    scenes = []
    for i in range(1, 6):
        scene = {
            "id": f"batch_scene_{i}",
            "emotion": {
                "type": "joy" if i % 2 == 0 else "sadness",
                "score": 0.5 + (i * 0.1)
            },
            "tags": ["高潮"] if i == 3 else ["一般场景"],
            "text": f"这是第{i}个测试场景，用于演示批量处理效果。"
        }
        scenes.append(scene)
    
    # 创建记忆触发器
    trigger = EmotionMemoryTrigger()
    
    # 处理场景
    processed_scenes = trigger.process_scenes(scenes)
    
    print("批量处理后的场景:")
    for i, scene in enumerate(processed_scenes, 1):
        print_scene_info(scene, i)

def display_available_templates() -> None:
    """显示可用的记忆触发模板"""
    print_header("可用记忆触发模板")
    
    # 显示情感类型模板
    print("情感类型触发模板:")
    emotion_types = ["喜悦", "悲伤", "愤怒", "恐惧", "厌恶", "惊讶", "中性"]
    for emotion_type in emotion_types:
        templates = MEMORY_TRIGGER_TEMPLATES.get(emotion_type, [])
        if templates:
            print(f"  {emotion_type}:")
            for template in templates:
                print(f"    - {template}")
            print()
    
    # 显示情感记忆标签模板
    print("情感记忆标签触发模板:")
    memory_tags = ["高潮", "胜利", "悲剧", "冲突", "启示", "离别", "团聚", "成长", "牺牲", "转折"]
    for tag in memory_tags:
        templates = MEMORY_TRIGGER_TEMPLATES.get(tag, [])
        if templates:
            print(f"  {tag}:")
            for template in templates:
                print(f"    - {template}")
            print()

if __name__ == "__main__":
    demonstrate_basic_triggers()
    demonstrate_simple_function()
    demonstrate_custom_config()
    demonstrate_memory_hooks_batch()
    display_available_templates() 