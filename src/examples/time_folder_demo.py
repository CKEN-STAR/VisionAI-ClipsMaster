"""
时空折叠引擎演示

演示如何使用时空折叠引擎将线性时间轴重构为非线性叙事结构
"""

import os
import json
import argparse
from typing import Dict, List, Any, Optional
from pathlib import Path
import pprint

from src.nonlinear.time_folder import (
    TimeFolder, fold_timeline, FoldingMode, 
    get_folding_strategy, list_folding_strategies
)
from src.narrative.anchor_types import AnchorType, AnchorInfo
from src.narrative.anchor_detector import detect_anchors


def create_sample_scenes(scene_type: str = "default") -> List[Dict[str, Any]]:
    """
    创建示例场景
    
    Args:
        scene_type: 场景类型
        
    Returns:
        场景列表
    """
    if scene_type == "suspense":
        # 悬疑类型示例场景
        return [
            {
                "id": "scene_1",
                "text": "主角在深夜接到一个神秘电话。",
                "emotion_score": -0.2,
                "characters": ["主角"],
                "duration": 8.0
            },
            {
                "id": "scene_2",
                "text": "主角发现家中有陌生人闯入的痕迹。",
                "emotion_score": -0.4,
                "characters": ["主角"],
                "duration": 7.5
            },
            {
                "id": "scene_3",
                "text": "主角在抽屉中发现一张陌生的照片。",
                "emotion_score": -0.3,
                "characters": ["主角"],
                "duration": 6.0
            },
            {
                "id": "scene_4",
                "text": "照片背面有一行神秘数字。",
                "emotion_score": -0.2,
                "characters": ["主角"],
                "duration": 5.0
            },
            {
                "id": "scene_5",
                "text": "主角找到老友寻求帮助。",
                "emotion_score": 0.1,
                "characters": ["主角", "老友"],
                "duration": 12.0
            },
            {
                "id": "scene_6",
                "text": "老友认出照片中的人物，表情变得严肃。",
                "emotion_score": -0.5,
                "characters": ["主角", "老友"],
                "duration": 8.0
            },
            {
                "id": "scene_7",
                "text": "老友透露那是失踪多年的前同事。",
                "emotion_score": -0.3,
                "characters": ["主角", "老友"],
                "duration": 10.0
            },
            {
                "id": "scene_8",
                "text": "主角回忆起一个月前的奇怪邮件。",
                "emotion_score": -0.3,
                "characters": ["主角"],
                "duration": 15.0
            },
            {
                "id": "scene_9",
                "text": "主角和老友决定找出真相。",
                "emotion_score": 0.2,
                "characters": ["主角", "老友"],
                "duration": 7.0
            },
            {
                "id": "scene_10",
                "text": "他们发现前同事有一个秘密身份。",
                "emotion_score": 0.0,
                "characters": ["主角", "老友", "警官"],
                "duration": 13.0
            },
            {
                "id": "scene_11",
                "text": "主角在档案室找到了关键证据。",
                "emotion_score": 0.3,
                "characters": ["主角"],
                "duration": 9.0
            },
            {
                "id": "scene_12",
                "text": "主角被神秘人袭击，陷入危险。",
                "emotion_score": -0.8,
                "characters": ["主角", "神秘人"],
                "duration": 11.0
            },
            {
                "id": "scene_13",
                "text": "老友及时赶到解救主角。",
                "emotion_score": 0.5,
                "characters": ["主角", "老友", "神秘人"],
                "duration": 12.0
            },
            {
                "id": "scene_14",
                "text": "真相揭晓，前同事卷入了一场阴谋。",
                "emotion_score": 0.2,
                "characters": ["主角", "老友", "警官"],
                "duration": 14.0
            },
            {
                "id": "scene_15",
                "text": "主角和老友成功阻止了阴谋。",
                "emotion_score": 0.7,
                "characters": ["主角", "老友", "警官"],
                "duration": 10.0
            }
        ]
    elif scene_type == "action":
        # 动作类型示例场景
        return [
            {
                "id": "scene_1",
                "text": "主角在特种部队训练场展示格斗技巧。",
                "emotion_score": 0.3,
                "characters": ["主角", "教官"],
                "duration": 10.0
            },
            {
                "id": "scene_2",
                "text": "主角接到紧急任务，必须营救被绑架的科学家。",
                "emotion_score": 0.1,
                "characters": ["主角", "指挥官"],
                "duration": 8.0
            },
            {
                "id": "scene_3",
                "text": "主角与团队成员制定营救计划。",
                "emotion_score": 0.2,
                "characters": ["主角", "队友A", "队友B"],
                "duration": 12.0
            },
            {
                "id": "scene_4",
                "text": "团队乘直升机前往任务地点。",
                "emotion_score": 0.3,
                "characters": ["主角", "队友A", "队友B", "飞行员"],
                "duration": 7.0
            },
            {
                "id": "scene_5",
                "text": "团队潜入敌方基地外围。",
                "emotion_score": 0.4,
                "characters": ["主角", "队友A", "队友B"],
                "duration": 9.0
            },
            {
                "id": "scene_6",
                "text": "遭遇第一波敌人，展开激烈交火。",
                "emotion_score": 0.6,
                "characters": ["主角", "队友A", "队友B", "敌人"],
                "duration": 14.0
            },
            {
                "id": "scene_7",
                "text": "队友A受伤，主角掩护撤退。",
                "emotion_score": -0.3,
                "characters": ["主角", "队友A", "敌人"],
                "duration": 8.0
            },
            {
                "id": "scene_8",
                "text": "主角单独潜入基地内部。",
                "emotion_score": 0.2,
                "characters": ["主角"],
                "duration": 10.0
            },
            {
                "id": "scene_9",
                "text": "主角找到被关押的科学家。",
                "emotion_score": 0.5,
                "characters": ["主角", "科学家"],
                "duration": 6.0
            },
            {
                "id": "scene_10",
                "text": "撤离途中遭遇埋伏。",
                "emotion_score": -0.4,
                "characters": ["主角", "科学家", "敌人"],
                "duration": 13.0
            },
            {
                "id": "scene_11",
                "text": "主角与敌方头目展开搏斗。",
                "emotion_score": 0.7,
                "characters": ["主角", "敌方头目"],
                "duration": 15.0
            },
            {
                "id": "scene_12",
                "text": "主角击败敌方头目，但身受重伤。",
                "emotion_score": 0.5,
                "characters": ["主角", "敌方头目"],
                "duration": 12.0
            },
            {
                "id": "scene_13",
                "text": "队友B驾驶车辆接应，紧急撤离。",
                "emotion_score": 0.6,
                "characters": ["主角", "科学家", "队友B"],
                "duration": 11.0
            },
            {
                "id": "scene_14",
                "text": "敌人追击，展开公路追逐战。",
                "emotion_score": 0.8,
                "characters": ["主角", "科学家", "队友B", "敌人"],
                "duration": 16.0
            },
            {
                "id": "scene_15",
                "text": "成功甩脱追兵，任务完成。",
                "emotion_score": 0.9,
                "characters": ["主角", "科学家", "队友B"],
                "duration": 8.0
            },
            {
                "id": "scene_16",
                "text": "回到基地，受到表彰。",
                "emotion_score": 0.7,
                "characters": ["主角", "科学家", "队友A", "队友B", "指挥官"],
                "duration": 9.0
            }
        ]
    else:
        # 默认示例场景
        return [
            {
                "id": "scene_1",
                "text": "主角早晨起床，准备出门。",
                "emotion_score": 0.1,
                "characters": ["主角"],
                "duration": 5.0
            },
            {
                "id": "scene_2",
                "text": "主角在咖啡店遇见老朋友。",
                "emotion_score": 0.4,
                "characters": ["主角", "朋友"],
                "duration": 8.0
            },
            {
                "id": "scene_3",
                "text": "朋友提到一个工作机会。",
                "emotion_score": 0.3,
                "characters": ["主角", "朋友"],
                "duration": 7.0
            },
            {
                "id": "scene_4",
                "text": "主角参加面试，表现出色。",
                "emotion_score": 0.5,
                "characters": ["主角", "面试官"],
                "duration": 10.0
            },
            {
                "id": "scene_5",
                "text": "主角获得工作offer，心情愉悦。",
                "emotion_score": 0.8,
                "characters": ["主角"],
                "duration": 3.0
            },
            {
                "id": "scene_6",
                "text": "主角回家路上遇到一点小麻烦。",
                "emotion_score": -0.2,
                "characters": ["主角", "路人"],
                "duration": 6.0
            },
            {
                "id": "scene_7",
                "text": "主角与家人分享好消息。",
                "emotion_score": 0.7,
                "characters": ["主角", "家人"],
                "duration": 9.0
            },
            {
                "id": "scene_8",
                "text": "主角规划未来，期待新工作。",
                "emotion_score": 0.6,
                "characters": ["主角"],
                "duration": 4.0
            }
        ]


def display_folding_result(original_scenes: List[Dict[str, Any]], 
                          folded_scenes: List[Dict[str, Any]],
                          anchors: List[AnchorInfo],
                          strategy_name: str,
                          structure_name: str) -> None:
    """
    显示折叠结果
    
    Args:
        original_scenes: 原始场景列表
        folded_scenes: 折叠后的场景列表
        anchors: 锚点列表
        strategy_name: 策略名称
        structure_name: 结构名称
    """
    print("\n" + "="*70)
    print(f"时空折叠结果 | 策略: {strategy_name} | 结构: {structure_name}")
    print("-"*70)
    
    # 显示基本统计信息
    original_duration = sum(s.get("duration", 0) for s in original_scenes)
    folded_duration = sum(s.get("duration", 0) for s in folded_scenes)
    
    print(f"原始场景数: {len(original_scenes)}")
    print(f"折叠后场景数: {len(folded_scenes)}")
    print(f"场景减少率: {(1 - len(folded_scenes)/len(original_scenes))*100:.1f}%")
    print(f"原始时长: {original_duration:.1f}秒")
    print(f"折叠后时长: {folded_duration:.1f}秒")
    print(f"时长减少率: {(1 - folded_duration/original_duration)*100:.1f}%")
    
    # 显示锚点信息
    print("-"*70)
    print(f"检测到的锚点 ({len(anchors)}):")
    for anchor in anchors:
        print(f"  - [{anchor.type.value}] {anchor.description} "
              f"(位置: {anchor.position:.2f}, 重要性: {anchor.importance:.2f})")
    
    # 显示结果场景序列
    print("-"*70)
    print("折叠后的场景序列:")
    for i, scene in enumerate(folded_scenes):
        # 原始索引
        orig_idx = next((j for j, s in enumerate(original_scenes) if s["id"] == scene["id"]), -1)
        
        # 特殊标记
        markers = []
        if scene.get("is_climax"):
            markers.append("高潮")
        if scene.get("is_flashback"):
            markers.append("回闪")
        
        marker_str = f" [{', '.join(markers)}]" if markers else ""
        
        print(f"  {i+1}. {scene['text']}{marker_str}")
        print(f"     原始位置: {orig_idx+1}/{len(original_scenes)}, "
              f"情感值: {scene.get('emotion_score', 0):.1f}, "
              f"角色: {', '.join(scene.get('characters', []))}")
    
    print("="*70)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="时空折叠引擎演示")
    parser.add_argument("--type", "-t", choices=["default", "suspense", "action"], default="suspense",
                      help="示例场景类型")
    parser.add_argument("--structure", "-s", default=None, 
                      help="叙事结构名称")
    parser.add_argument("--mode", "-m", 
                      choices=["preserve_anchors", "condense_similar", "highlight_contrast", "narrative_driven"],
                      default="narrative_driven",
                      help="折叠模式")
    args = parser.parse_args()
    
    # 创建示例场景
    scenes = create_sample_scenes(args.type)
    print(f"创建了 {len(scenes)} 个{args.type}类型的示例场景")
    
    # 检测锚点
    anchors = detect_anchors(scenes)
    print(f"检测到 {len(anchors)} 个锚点")
    
    # 确定叙事结构
    structure_map = {
        "suspense": "倒叙风暴",
        "action": "高潮迭起",
        "default": "环形结构"
    }
    structure_name = args.structure or structure_map.get(args.type, "倒叙风暴")
    
    # 确定折叠模式
    mode_map = {
        "preserve_anchors": FoldingMode.PRESERVE_ANCHORS,
        "condense_similar": FoldingMode.CONDENSE_SIMILAR,
        "highlight_contrast": FoldingMode.HIGHLIGHT_CONTRAST,
        "narrative_driven": FoldingMode.NARRATIVE_DRIVEN
    }
    folding_mode = mode_map.get(args.mode, FoldingMode.NARRATIVE_DRIVEN)
    
    # 创建时空折叠引擎
    folder = TimeFolder()
    
    # 执行折叠
    print(f"\n使用 {structure_name} 结构和 {args.mode} 模式执行时空折叠...")
    folded_scenes = folder.fold_timeline(scenes, anchors, structure_name, mode=folding_mode)
    
    # 显示结果
    display_folding_result(
        scenes, folded_scenes, anchors, 
        folder._get_strategy_for_structure(structure_name).name,
        structure_name
    )
    
    print("\n演示完成!")


if __name__ == "__main__":
    main() 