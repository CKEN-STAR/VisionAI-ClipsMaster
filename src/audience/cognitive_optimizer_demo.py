#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
认知负荷优化器演示脚本

展示如何使用认知负荷优化器优化内容，降低认知负荷，提高用户体验。
"""

import os
import sys
import json
from pprint import pprint
import time
from datetime import datetime
import traceback
import random
import numpy as np

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

print("开始认知负荷优化器演示脚本...")

# 替换真实模块为模拟模块
import src.audience.privacy_guard_mock as mock
sys.modules['src.data.storage_manager'] = mock
sys.modules['src.utils.log_handler'] = mock
sys.modules['src.utils.privacy_manager'] = mock
sys.modules['src.core.privacy_manager'] = mock

# 导入认知负荷优化器
try:
    from src.audience.cognitive_optimizer import (
        CognitiveLoadBalancer, get_cognitive_optimizer, 
        optimize_content, calculate_cognitive_load
    )
    print("成功导入认知负荷优化器模块")
except Exception as e:
    print(f"导入认知负荷优化器模块时出错: {str(e)}")
    traceback.print_exc()
    sys.exit(1)

def print_section(title):
    """打印分节标题"""
    print("\n" + "=" * 60)
    print(f" {title} ".center(60, "="))
    print("=" * 60)

def generate_sample_content(complexity_level="medium"):
    """
    生成示例内容
    
    Args:
        complexity_level: 复杂度级别，可选值为 low, medium, high
        
    Returns:
        示例内容数据
    """
    # 基础结构
    content = {
        "id": f"content_{int(time.time())}",
        "title": "认知负荷测试内容",
        "duration": 120.0,  # 2分钟
        "scenes": [],
        "dialogues": [],
        "tags": ["测试", "演示"],
        "twists_per_min": 2.0
    }
    
    # 设置复杂度参数
    if complexity_level == "low":
        num_scenes = 3
        elements_per_scene = 2
        transitions_per_scene = 1
        effects_per_scene = 0
        num_dialogues = 4
        content["twists_per_min"] = 1.0
        content["complexity"] = 0.3
    elif complexity_level == "medium":
        num_scenes = 5
        elements_per_scene = 4
        transitions_per_scene = 2
        effects_per_scene = 1
        num_dialogues = 7
        content["twists_per_min"] = 2.0
        content["complexity"] = 0.5
    else:  # high
        num_scenes = 8
        elements_per_scene = 7
        transitions_per_scene = 3
        effects_per_scene = 3
        num_dialogues = 12
        content["twists_per_min"] = 4.0
        content["complexity"] = 0.8
    
    # 生成场景
    for i in range(num_scenes):
        scene = {
            "id": f"scene_{i+1}",
            "description": f"场景 {i+1}",
            "duration": 120.0 / num_scenes,
            "elements": [],
            "transitions": [],
            "effects": [],
            "importance": random.uniform(0.4, 0.9)
        }
        
        # 关键场景标记
        if i == 1 or i == num_scenes - 2:
            scene["has_key_information"] = True
        
        # 情感高潮
        if i == num_scenes - 1:
            scene["emotional_peak"] = True
        
        # 生成元素
        for j in range(elements_per_scene):
            element_type = random.choice(["text", "image", "video", "graphic"])
            element = {
                "type": element_type,
                "content": f"{element_type} 内容 {j+1}",
                "importance": random.uniform(0.3, 0.9)
            }
            scene["elements"].append(element)
        
        # 生成转场
        for j in range(transitions_per_scene):
            transition_type = random.choice(["fade", "slide", "zoom", "dissolve"])
            transition = {
                "type": transition_type,
                "duration": random.uniform(0.5, 2.0),
                "importance": random.uniform(0.3, 0.7)
            }
            scene["transitions"].append(transition)
        
        # 生成特效
        for j in range(effects_per_scene):
            effect_type = random.choice(["highlight", "blur", "color_shift", "particle"])
            effect = {
                "type": effect_type,
                "duration": random.uniform(1.0, 3.0),
                "importance": random.uniform(0.2, 0.6)
            }
            scene["effects"].append(effect)
        
        content["scenes"].append(scene)
    
    # 生成对话
    speakers = ["narrator", "presenter", "guest", "expert"]
    for i in range(num_dialogues):
        dialogue = {
            "speaker": random.choice(speakers),
            "text": f"这是第 {i+1} 段对话内容，包含了一些" + "重要信息" * (i % 3 == 0),
            "importance": random.uniform(0.4, 0.9) if i % 3 == 0 else random.uniform(0.3, 0.7)
        }
        content["dialogues"].append(dialogue)
    
    return content

def generate_user_profiles():
    """
    生成不同类型的用户画像
    
    Returns:
        用户画像字典
    """
    profiles = {
        "高认知能力用户": {
            "id": "user_high",
            "name": "高认知能力用户",
            "cognitive_abilities": {
                "attention_span": 0.9,
                "processing_speed": 0.8,
                "domain_knowledge": 0.8
            },
            "preferences": {
                "content_complexity": 0.8,
                "visual_density": 0.7,
                "pacing": 0.8
            }
        },
        "中等认知能力用户": {
            "id": "user_medium",
            "name": "中等认知能力用户",
            "cognitive_abilities": {
                "attention_span": 0.6,
                "processing_speed": 0.6,
                "domain_knowledge": 0.5
            },
            "preferences": {
                "content_complexity": 0.5,
                "visual_density": 0.5,
                "pacing": 0.6
            }
        },
        "低认知能力用户": {
            "id": "user_low",
            "name": "低认知能力用户",
            "cognitive_abilities": {
                "attention_span": 0.3,
                "processing_speed": 0.4,
                "domain_knowledge": 0.2
            },
            "preferences": {
                "content_complexity": 0.3,
                "visual_density": 0.3,
                "pacing": 0.4
            }
        },
        "注意力不足用户": {
            "id": "user_adhd",
            "name": "注意力不足用户",
            "cognitive_abilities": {
                "attention_span": 0.2,
                "processing_speed": 0.7,
                "domain_knowledge": 0.5
            },
            "preferences": {
                "content_complexity": 0.4,
                "visual_density": 0.3,
                "pacing": 0.7
            }
        },
        "专业领域用户": {
            "id": "user_expert",
            "name": "专业领域用户",
            "cognitive_abilities": {
                "attention_span": 0.7,
                "processing_speed": 0.6,
                "domain_knowledge": 0.9
            },
            "preferences": {
                "content_complexity": 0.9,
                "visual_density": 0.7,
                "pacing": 0.5
            }
        }
    }
    
    return profiles

def print_content_stats(content, label="内容"):
    """
    打印内容统计信息
    
    Args:
        content: 内容数据
        label: 内容标签
    """
    print(f"\n{label}统计:")
    
    # 基本信息
    print(f"- 标题: {content.get('title', '未知')}")
    print(f"- 时长: {content.get('duration', 0):.1f} 秒")
    
    # 场景统计
    scenes = content.get("scenes", [])
    print(f"- 场景数量: {len(scenes)}")
    
    # 元素统计
    total_elements = sum(len(scene.get("elements", [])) for scene in scenes)
    print(f"- 总元素数量: {total_elements}")
    
    # 转场统计
    total_transitions = sum(len(scene.get("transitions", [])) for scene in scenes)
    print(f"- 总转场数量: {total_transitions}")
    
    # 特效统计
    total_effects = sum(len(scene.get("effects", [])) for scene in scenes)
    print(f"- 总特效数量: {total_effects}")
    
    # 对话统计
    dialogues = content.get("dialogues", [])
    print(f"- 对话数量: {len(dialogues)}")
    
    # 每分钟转折点
    print(f"- 每分钟转折点: {content.get('twists_per_min', 0):.1f}")

def demonstrate_cognitive_optimizer():
    """演示认知负荷优化器功能"""
    print_section("认知负荷优化器演示")
    
    # 获取优化器实例
    print("正在获取认知负荷优化器...")
    try:
        optimizer = get_cognitive_optimizer()
        print("成功获取认知负荷优化器")
    except Exception as e:
        print(f"获取认知负荷优化器时发生错误: {str(e)}")
        traceback.print_exc()
        return
    
    # 演示1：生成不同复杂度的内容
    print_section("1. 不同复杂度内容")
    
    print("\n生成不同复杂度的内容...")
    simple_content = generate_sample_content("low")
    medium_content = generate_sample_content("medium")
    complex_content = generate_sample_content("high")
    
    print("\n简单内容:")
    print_content_stats(simple_content, "简单内容")
    
    print("\n中等内容:")
    print_content_stats(medium_content, "中等内容")
    
    print("\n复杂内容:")
    print_content_stats(complex_content, "复杂内容")
    
    # 演示2：计算不同内容的认知负荷
    print_section("2. 计算认知负荷")
    
    # 生成用户画像
    user_profiles = generate_user_profiles()
    
    print("\n计算不同内容对不同用户的认知负荷...")
    for content_name, content in [
        ("简单内容", simple_content),
        ("中等内容", medium_content),
        ("复杂内容", complex_content)
    ]:
        print(f"\n{content_name}的认知负荷:")
        
        # 计算标准负荷（不考虑用户画像）
        standard_load = calculate_cognitive_load(content)
        print(f"- 标准负荷: {standard_load:.2f}")
        
        # 计算针对不同用户的负荷
        for profile_name, profile in user_profiles.items():
            user_load = calculate_cognitive_load(content, profile)
            print(f"- {profile_name}: {user_load:.2f}")
    
    # 演示3：优化高复杂度内容
    print_section("3. 认知负荷优化")
    
    print("\n为不同用户优化复杂内容...")
    
    for profile_name, profile in user_profiles.items():
        print(f"\n为 {profile_name} 优化内容:")
        
        # 计算优化前的认知负荷
        original_load = calculate_cognitive_load(complex_content, profile)
        print(f"- 优化前认知负荷: {original_load:.2f}")
        
        # 优化内容
        optimized_content = optimize_content(complex_content, profile)
        
        # 计算优化后的认知负荷
        optimized_load = calculate_cognitive_load(optimized_content, profile)
        print(f"- 优化后认知负荷: {optimized_load:.2f}")
        
        # 打印优化前后的内容统计
        print_content_stats(complex_content, "优化前")
        print_content_stats(optimized_content, "优化后")
        
        # 计算减少百分比
        scenes_reduction = (len(complex_content["scenes"]) - len(optimized_content["scenes"])) / len(complex_content["scenes"]) * 100
        elements_before = sum(len(scene.get("elements", [])) for scene in complex_content["scenes"])
        elements_after = sum(len(scene.get("elements", [])) for scene in optimized_content["scenes"])
        elements_reduction = (elements_before - elements_after) / elements_before * 100
        
        print(f"- 场景减少: {scenes_reduction:.1f}%")
        print(f"- 元素减少: {elements_reduction:.1f}%")
        
        # 计算负荷减少百分比
        load_reduction = (original_load - optimized_load) / original_load * 100
        print(f"- 认知负荷减少: {load_reduction:.1f}%")
    
    # 演示4：自适应优化不同类型内容
    print_section("4. 自适应优化")
    
    # 选择一个用户画像
    user_profile = user_profiles["中等认知能力用户"]
    
    print(f"\n为用户 {user_profile['name']} 自适应优化不同内容:")
    
    for content_name, content in [
        ("简单内容", simple_content),
        ("中等内容", medium_content),
        ("复杂内容", complex_content)
    ]:
        print(f"\n优化 {content_name}:")
        
        # 计算优化前的认知负荷
        original_load = calculate_cognitive_load(content, user_profile)
        print(f"- 优化前认知负荷: {original_load:.2f}")
        
        # 优化内容
        optimized_content = optimize_content(content, user_profile)
        
        # 计算优化后的认知负荷
        optimized_load = calculate_cognitive_load(optimized_content, user_profile)
        print(f"- 优化后认知负荷: {optimized_load:.2f}")
        
        # 对比优化前后
        scenes_before = len(content["scenes"])
        scenes_after = len(optimized_content["scenes"])
        
        if original_load > optimizer.config["thresholds"]["max_cognitive_load"]:
            print(f"- 进行了优化，场景从 {scenes_before} 变为 {scenes_after}")
        else:
            print(f"- 内容已经适合用户，保持不变或微调")
    
    print("\n演示完成！")

if __name__ == "__main__":
    try:
        demonstrate_cognitive_optimizer()
    except Exception as e:
        print(f"演示过程中发生错误: {str(e)}")
        traceback.print_exc() 