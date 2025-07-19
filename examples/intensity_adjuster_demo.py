#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
动态强度调节器演示脚本

展示了如何使用动态强度调节器来调整场景的情感强度、冲突激烈度和视觉刺激强度。
"""

import os
import sys
import json
from typing import Dict, List, Any

# 添加项目根目录到系统路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.adaptation.dynamic_intensity_adjuster import DynamicIntensityAdjuster

def print_header(title: str) -> None:
    """打印带有格式的标题"""
    print("\n" + "=" * 60)
    print(f" {title} ".center(60, "="))
    print("=" * 60)

def print_scene_info(scene: Dict[str, Any], prefix: str = "") -> None:
    """打印场景信息"""
    print(f"{prefix}场景: {scene.get('id', '未命名')}")
    
    # 打印情感信息
    if "emotion" in scene and isinstance(scene["emotion"], dict):
        emotion = scene["emotion"]
        emotion_type = emotion.get("type", "未知")
        emotion_score = emotion.get("score", emotion.get("intensity", 0.0))
        adjusted_score = emotion.get("adjusted_score", None)
        
        print(f"{prefix}  情感: {emotion_type}, 强度: {emotion_score:.2f}")
        if adjusted_score is not None:
            print(f"{prefix}  调整后情感强度: {adjusted_score:.2f}")
    
    # 打印冲突信息
    if "conflict" in scene and isinstance(scene["conflict"], dict):
        conflict = scene["conflict"]
        conflict_type = conflict.get("type", "未知")
        conflict_intensity = conflict.get("intensity", 0.0)
        adjusted_intensity = conflict.get("adjusted_intensity", None)
        
        print(f"{prefix}  冲突: {conflict_type}, 强度: {conflict_intensity:.2f}")
        if adjusted_intensity is not None:
            print(f"{prefix}  调整后冲突强度: {adjusted_intensity:.2f}")
    
    # 打印视觉信息
    if "visual" in scene and isinstance(scene["visual"], dict):
        visual = scene["visual"]
        visual_style = visual.get("style", "未知")
        visual_intensity = visual.get("intensity", 0.0)
        adjusted_intensity = visual.get("adjusted_intensity", None)
        
        print(f"{prefix}  视觉: {visual_style}, 强度: {visual_intensity:.2f}")
        if adjusted_intensity is not None:
            print(f"{prefix}  调整后视觉强度: {adjusted_intensity:.2f}")
    
    # 打印文本内容
    if "text" in scene:
        text = scene.get("text", "")
        if "original_text" in scene:
            print(f"{prefix}  原始文本: {scene['original_text']}")
            print(f"{prefix}  调整后文本: {text}")
        else:
            print(f"{prefix}  文本: {text}")
    
    print()

def create_test_scenes() -> List[Dict[str, Any]]:
    """创建测试场景数据"""
    return [
        # 引入场景 - 平静
        {
            "id": "scene_1",
            "start": 0.0,
            "end": 10.0,
            "text": "这是一个平静的下午，阳光透过窗户照射进来。",
            "emotion": {
                "type": "neutral",
                "score": 0.5
            },
            "visual": {
                "style": "slow_paced",
                "intensity": 0.4
            }
        },
        # 铺垫场景 - 喜悦
        {
            "id": "scene_2",
            "start": 10.0,
            "end": 20.0,
            "text": "他们笑着聊天，分享着各自的故事。",
            "emotion": {
                "type": "joy",
                "score": 0.6
            },
            "visual": {
                "style": "gentle",
                "intensity": 0.5
            }
        },
        # 冲突开始 - 紧张
        {
            "id": "scene_3",
            "start": 20.0,
            "end": 30.0,
            "text": "突然，电话铃声打破了平静。她迅速站起身来。",
            "emotion": {
                "type": "surprise",
                "score": 0.7
            },
            "visual": {
                "style": "fast_paced",
                "intensity": 0.6
            },
            "conflict": {
                "type": "psychological",
                "intensity": 0.5
            }
        },
        # 高潮场景 - 愤怒
        {
            "id": "scene_4",
            "start": 30.0,
            "end": 40.0,
            "text": "他怒视着对方，大声喊道：'你怎么能这样做？'",
            "emotion": {
                "type": "anger",
                "score": 0.8
            },
            "visual": {
                "style": "intense",
                "intensity": 0.7
            },
            "conflict": {
                "type": "verbal",
                "intensity": 0.75
            },
            "dialog": [
                {"character": "男主角", "text": "你怎么能这样做？"}
            ]
        },
        # 高潮场景 - 恐惧
        {
            "id": "scene_5",
            "start": 40.0,
            "end": 50.0,
            "text": "她颤抖着后退，眼中充满恐惧。黑暗笼罩了整个房间。",
            "emotion": {
                "type": "fear",
                "score": 0.85
            },
            "visual": {
                "style": "high_contrast",
                "intensity": 0.8
            },
            "conflict": {
                "type": "physical",
                "intensity": 0.8
            }
        },
        # 解决场景 - 释然
        {
            "id": "scene_6",
            "start": 50.0,
            "end": 60.0,
            "text": "最终，他们理解了彼此的立场。阳光再次照进房间。",
            "emotion": {
                "type": "joy",
                "score": 0.6
            },
            "visual": {
                "style": "gentle",
                "intensity": 0.5
            },
            "conflict": {
                "type": "emotional",
                "intensity": 0.3
            }
        }
    ]

def demonstrate_intensity_adjustment() -> None:
    """演示情感强度调整功能"""
    # 创建动态强度调节器实例
    print_header("创建动态强度调节器")
    adjuster = DynamicIntensityAdjuster()
    
    # 创建测试场景
    scenes = create_test_scenes()
    
    # 打印原始场景信息
    print_header("原始场景信息")
    for scene in scenes:
        print_scene_info(scene)
    
    # 使用平衡预设调整场景
    print_header("使用「平衡」预设调整")
    balanced_scenes = adjuster.adjust_scenes(scenes)
    for scene in balanced_scenes:
        print_scene_info(scene)
    
    # 切换到强烈预设并调整场景
    print_header("使用「强烈」预设调整")
    adjuster.set_user_preference("intense")
    intense_scenes = adjuster.adjust_scenes(scenes)
    for scene in intense_scenes:
        print_scene_info(scene)
    
    # 切换到柔和预设并调整场景
    print_header("使用「柔和」预设调整")
    adjuster.set_user_preference("subtle")
    subtle_scenes = adjuster.adjust_scenes(scenes)
    for scene in subtle_scenes:
        print_scene_info(scene)
    
    # 显示调整历史
    print_header("调整历史记录")
    history = adjuster.get_adjustment_history()
    for entry in history:
        print(f"时间: {entry['timestamp']}")
        print(f"预设: {entry['preset']}")
        print(f"场景数: {entry['scene_count']}")
        print(f"平均情感强度: {entry['average_emotion']:.2f}")
        print(f"平均冲突强度: {entry['average_conflict']:.2f}")
        print(f"平均视觉强度: {entry['average_visual']:.2f}")
        print()

if __name__ == "__main__":
    demonstrate_intensity_adjustment() 