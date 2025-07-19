#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
情感一致性检验演示脚本

展示如何使用情感一致性检验功能检测和修复情感断层问题。
演示不同场景下的情感一致性检验和修复建议生成。
"""

import os
import sys
import json
from typing import Dict, List, Any, Optional

# 添加项目根目录到系统路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.emotion.consistency_check import (
    EmotionValidator, 
    validate_emotion_consistency,
    get_consistency_suggestions
)

def print_header(title: str) -> None:
    """打印带有格式的标题"""
    print("\n" + "=" * 60)
    print(f" {title} ".center(60, "="))
    print("=" * 60)

def print_scene_emotion(scene: Dict[str, Any], index: int) -> None:
    """打印场景的情感信息"""
    emotion = scene.get("emotion", {})
    emotion_type = emotion.get("type", "未知")
    emotion_score = emotion.get("score", 0.0)
    
    print(f"场景 {index}: {emotion_type}, 强度: {emotion_score:.2f}")

def print_suggestion(suggestion: Dict[str, Any]) -> None:
    """打印修复建议信息"""
    location = suggestion.get("location", {})
    issue = suggestion.get("issue", {})
    solutions = suggestion.get("solutions", [])
    
    print(f"发现问题: 场景 {location.get('prev_scene_index', '?')} 到 {location.get('current_scene_index', '?')}")
    print(f"  情感变化: {issue.get('prev_score', 0):.2f} -> {issue.get('current_score', 0):.2f}")
    print(f"  变化幅度: {issue.get('delta', 0):.2f}, 阈值: {issue.get('threshold', 0):.2f}")
    
    print("修复建议:")
    for i, solution in enumerate(solutions, 1):
        print(f"  {i}. {solution.get('description', '未知')}")
    
    print()

def create_smooth_scenes() -> List[Dict[str, Any]]:
    """创建情感过渡平滑的场景序列"""
    return [
        {
            "id": "scene_1",
            "emotion": {
                "type": "neutral",
                "score": 0.5
            }
        },
        {
            "id": "scene_2",
            "emotion": {
                "type": "joy",
                "score": 0.6
            }
        },
        {
            "id": "scene_3",
            "emotion": {
                "type": "joy",
                "score": 0.7
            }
        },
        {
            "id": "scene_4",
            "emotion": {
                "type": "surprise",
                "score": 0.9
            }
        },
        {
            "id": "scene_5",
            "emotion": {
                "type": "fear",
                "score": 0.7
            }
        },
        {
            "id": "scene_6",
            "emotion": {
                "type": "neutral",
                "score": 0.5
            }
        }
    ]

def create_problem_scenes() -> List[Dict[str, Any]]:
    """创建存在情感断层的场景序列"""
    return [
        {
            "id": "scene_1",
            "emotion": {
                "type": "neutral",
                "score": 0.3
            }
        },
        {
            "id": "scene_2",
            "emotion": {
                "type": "joy",
                "score": 0.9  # 情感跳跃过大
            }
        },
        {
            "id": "scene_3",
            "emotion": {
                "type": "joy",
                "score": 0.7
            }
        },
        {
            "id": "scene_4",
            "emotion": {
                "type": "anger",
                "score": 0.1  # 情感跳跃过大
            }
        },
        {
            "id": "scene_5",
            "emotion": {
                "type": "fear",
                "score": 0.8  # 情感跳跃过大
            }
        },
        {
            "id": "scene_6",
            "emotion": {
                "type": "neutral",
                "score": 0.4
            }
        }
    ]

def demonstrate_smooth_validation() -> None:
    """演示平滑情感序列的验证"""
    print_header("平滑情感序列验证")
    
    scenes = create_smooth_scenes()
    
    # 打印场景情感信息
    print("场景情感信息:")
    for i, scene in enumerate(scenes, 1):
        print_scene_emotion(scene, i)
    
    # 验证情感一致性
    result, error_msg = validate_emotion_consistency(scenes)
    
    print("\n验证结果:")
    if result:
        print("✅ 情感序列通过一致性验证!")
    else:
        print(f"❌ 情感序列存在问题: {error_msg}")

def demonstrate_problem_validation() -> None:
    """演示问题情感序列的验证和修复"""
    print_header("问题情感序列验证")
    
    scenes = create_problem_scenes()
    
    # 打印场景情感信息
    print("场景情感信息:")
    for i, scene in enumerate(scenes, 1):
        print_scene_emotion(scene, i)
    
    # 验证情感一致性
    result, error_msg = validate_emotion_consistency(scenes)
    
    print("\n验证结果:")
    if result:
        print("✅ 情感序列通过一致性验证!")
    else:
        print(f"❌ 情感序列存在问题: {error_msg}")
        
        # 获取修复建议
        suggestions = get_consistency_suggestions(scenes)
        
        print("\n修复建议:")
        if not suggestions:
            print("没有可用的修复建议。")
        else:
            for suggestion in suggestions:
                print_suggestion(suggestion)
        
        # 应用第一个修复建议
        if suggestions:
            print_header("应用修复建议")
            
            validator = EmotionValidator()
            fixed_scenes = validator.apply_suggestion(scenes, suggestions[0])
            
            print("修复后场景情感信息:")
            for i, scene in enumerate(fixed_scenes, 1):
                print_scene_emotion(scene, i)
            
            # 重新验证
            result, error_msg = validate_emotion_consistency(fixed_scenes)
            
            print("\n重新验证结果:")
            if result:
                print("✅ 修复后情感序列通过一致性验证!")
            else:
                print(f"❌ 修复后情感序列仍存在问题: {error_msg}")

def demonstrate_config_customization() -> None:
    """演示自定义配置的验证"""
    print_header("自定义配置验证")
    
    scenes = create_problem_scenes()
    
    # 自定义配置
    custom_config = {
        "max_emotion_delta": 0.8,  # 放宽阈值
        "require_smooth_transitions": True,
        "allow_jumps_at_scene_change": True,
    }
    
    # 创建自定义验证器
    validator = EmotionValidator(custom_config)
    
    # 验证情感一致性
    result, error_msg = validator.check_arc(scenes)
    
    print("使用自定义配置 (max_emotion_delta=0.8) 验证结果:")
    if result:
        print("✅ 情感序列通过一致性验证!")
    else:
        print(f"❌ 情感序列存在问题: {error_msg}")

if __name__ == "__main__":
    demonstrate_smooth_validation()
    demonstrate_problem_validation()
    demonstrate_config_customization() 