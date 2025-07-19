"""
叙事结构选择器演示

演示如何使用叙事结构选择器根据剧本特征选择最佳的叙事结构模式
"""

import os
import json
import argparse
from typing import Dict, List, Any, Optional
from pathlib import Path
import pprint

from src.narrative.structure_selector import (
    StructureSelector, 
    select_narrative_structure, 
    get_structure_patterns,
    organize_anchors_by_structure
)
from src.narrative.anchor_detector import detect_anchors
from src.api.structure_api import generate_structure_visualization


def create_sample_script_metadata(script_type: str = "default") -> Dict[str, Any]:
    """
    创建示例剧本元数据
    
    Args:
        script_type: 剧本类型，决定创建的元数据类型
        
    Returns:
        示例剧本元数据
    """
    # 基础类型映射
    type_map = {
        "default": {
            "genre": "剧情,家庭",
            "emotion_tone": "温情",
            "pace": "medium"
        },
        "suspense": {
            "genre": "悬疑,犯罪,推理",
            "emotion_tone": "紧张",
            "pace": "fast"
        },
        "action": {
            "genre": "动作,冒险",
            "emotion_tone": "激烈",
            "pace": "fast"
        },
        "romance": {
            "genre": "爱情,青春",
            "emotion_tone": "温情",
            "pace": "medium"
        },
        "epic": {
            "genre": "史诗,奇幻,战争",
            "emotion_tone": "宏大",
            "pace": "medium" 
        },
        "comedy": {
            "genre": "喜剧,幽默",
            "emotion_tone": "轻松",
            "pace": "fast"
        },
        "art": {
            "genre": "文艺,哲理",
            "emotion_tone": "深沉",
            "pace": "slow"
        }
    }
    
    # 返回指定类型
    if script_type in type_map:
        metadata = type_map[script_type].copy()
        metadata["title"] = f"示例剧本-{script_type}"
        return metadata
    else:
        return type_map["default"]


def load_sample_scenes(script_type: str = "default") -> List[Dict[str, Any]]:
    """
    加载或生成示例场景数据
    
    Args:
        script_type: 剧本类型
        
    Returns:
        场景数据列表
    """
    # 创建示例场景（简化版）
    scenes = []
    
    if script_type == "suspense":
        # 悬疑类型场景
        scenes = [
            {
                "id": "scene_1",
                "text": "主角在凌晨接到一个陌生来电，电话那头沉默不语。",
                "emotion_score": -0.3,
                "characters": ["主角"],
                "duration": 8.5
            },
            {
                "id": "scene_2",
                "text": "主角翻看自己的记事本，发现有几页被撕掉了。",
                "emotion_score": -0.4,
                "characters": ["主角"],
                "duration": 5.2
            },
            {
                "id": "scene_3",
                "text": "主角发现家门口有一个神秘包裹，里面是一张陌生照片。",
                "emotion_score": -0.5,
                "characters": ["主角"],
                "duration": 7.3
            },
            {
                "id": "scene_4",
                "text": "主角联系老友寻求帮助，但老友表现得异常紧张。",
                "emotion_score": -0.6,
                "characters": ["主角", "老友"],
                "duration": 12.1
            },
            {
                "id": "scene_5",
                "text": "主角回忆起一个月前的一个晚上，自己喝醉后发生的事情。",
                "emotion_score": -0.3,
                "characters": ["主角", "神秘人"],
                "duration": 15.3
            },
            {
                "id": "scene_6",
                "text": "主角找到关键证据，开始理解整个事件的真相。",
                "emotion_score": 0.2,
                "characters": ["主角"],
                "duration": 9.8
            },
            {
                "id": "scene_7",
                "text": "主角终于明白了一切，但真相比想象的更加可怕。",
                "emotion_score": -0.7,
                "characters": ["主角", "反派"],
                "duration": 14.2
            }
        ]
    elif script_type == "action":
        # 动作类型场景
        scenes = [
            {
                "id": "scene_1",
                "text": "主角在训练场上展示自己的格斗技巧。",
                "emotion_score": 0.3,
                "characters": ["主角", "教练"],
                "duration": 7.5
            },
            {
                "id": "scene_2",
                "text": "主角接到任务，必须在24小时内完成。",
                "emotion_score": 0.2,
                "characters": ["主角", "上级"],
                "duration": 5.8
            },
            {
                "id": "scene_3",
                "text": "主角与搭档计划行动方案。",
                "emotion_score": 0.1,
                "characters": ["主角", "搭档"],
                "duration": 8.2
            },
            {
                "id": "scene_4",
                "text": "主角潜入敌方基地，遭遇第一波敌人。",
                "emotion_score": 0.4,
                "characters": ["主角", "敌人"],
                "duration": 12.5
            },
            {
                "id": "scene_5",
                "text": "主角与敌方头目进行激烈对决。",
                "emotion_score": 0.7,
                "characters": ["主角", "头目"],
                "duration": 18.3
            },
            {
                "id": "scene_6",
                "text": "主角受伤但继续战斗，展现顽强意志。",
                "emotion_score": 0.8,
                "characters": ["主角"],
                "duration": 9.4
            },
            {
                "id": "scene_7",
                "text": "主角最终战胜敌人，完成任务。",
                "emotion_score": 0.9,
                "characters": ["主角", "搭档"],
                "duration": 11.2
            },
            {
                "id": "scene_8",
                "text": "主角回到基地，接受嘉奖。",
                "emotion_score": 0.6,
                "characters": ["主角", "上级", "搭档"],
                "duration": 6.8
            }
        ]
    elif script_type == "romance":
        # 爱情类型场景
        scenes = [
            {
                "id": "scene_1",
                "text": "男主在咖啡馆偶遇女主，两人目光交汇。",
                "emotion_score": 0.4,
                "characters": ["男主", "女主"],
                "duration": 8.5
            },
            {
                "id": "scene_2",
                "text": "男主鼓起勇气向女主搭讪，但表现得很笨拙。",
                "emotion_score": 0.3,
                "characters": ["男主", "女主"],
                "duration": 10.2
            },
            {
                "id": "scene_3",
                "text": "两人开始约会，共度愉快时光。",
                "emotion_score": 0.7,
                "characters": ["男主", "女主"],
                "duration": 15.8
            },
            {
                "id": "scene_4",
                "text": "因为误会，两人发生争执。",
                "emotion_score": -0.5,
                "characters": ["男主", "女主"],
                "duration": 12.3
            },
            {
                "id": "scene_5",
                "text": "男主努力解释，但女主不愿意听。",
                "emotion_score": -0.6,
                "characters": ["男主", "女主"],
                "duration": 9.7
            },
            {
                "id": "scene_6",
                "text": "男主做出浪漫举动，希望挽回女主的心。",
                "emotion_score": 0.4,
                "characters": ["男主"],
                "duration": 7.5
            },
            {
                "id": "scene_7",
                "text": "两人终于和好，承诺未来会更加坦诚。",
                "emotion_score": 0.9,
                "characters": ["男主", "女主"],
                "duration": 11.2
            }
        ]
    else:
        # 默认场景
        scenes = [
            {
                "id": "scene_1",
                "text": "主角在日常生活中遇到了一个小问题。",
                "emotion_score": 0.0,
                "characters": ["主角"],
                "duration": 7.5
            },
            {
                "id": "scene_2",
                "text": "主角开始尝试解决问题，但困难重重。",
                "emotion_score": -0.3,
                "characters": ["主角", "朋友"],
                "duration": 10.2
            },
            {
                "id": "scene_3",
                "text": "主角获得了新的启发，有了解决方向。",
                "emotion_score": 0.2,
                "characters": ["主角", "导师"],
                "duration": 8.8
            },
            {
                "id": "scene_4",
                "text": "主角面临更大的挑战，几乎要放弃。",
                "emotion_score": -0.6,
                "characters": ["主角"],
                "duration": 12.3
            },
            {
                "id": "scene_5",
                "text": "在朋友的鼓励下，主角重新振作。",
                "emotion_score": 0.4,
                "characters": ["主角", "朋友"],
                "duration": 9.7
            },
            {
                "id": "scene_6",
                "text": "主角最终解决了问题，获得了成长。",
                "emotion_score": 0.7,
                "characters": ["主角", "朋友", "导师"],
                "duration": 11.2
            }
        ]
    
    return scenes


def display_structure_result(result: Dict[str, Any]) -> None:
    """
    显示结构选择结果
    
    Args:
        result: 结构选择结果
    """
    print("\n" + "="*60)
    print(f"最佳匹配结构: {result['pattern_name']}")
    print(f"匹配置信度: {result['confidence']:.2f}")
    print(f"匹配原因: {result['reason']}")
    print("-"*60)
    print("结构步骤:")
    for i, step in enumerate(result['steps']):
        print(f"  {i+1}. {step}")
    print("-"*60)
    print(f"结构描述: {result['description']}")
    print(f"适用类型: {', '.join(result['suitability'])}")
    
    # 如果有锚点映射，显示映射结果
    if "anchor_mapping" in result:
        print("-"*60)
        print("锚点映射:")
        for step, anchors in result["anchor_mapping"].items():
            print(f"  {step} ({len(anchors)}个锚点):")
            for anchor in anchors[:3]:  # 最多显示3个锚点
                print(f"    - [{anchor['type']}] {anchor['description']} (重要性: {anchor['importance']:.2f})")
            if len(anchors) > 3:
                print(f"    ...等{len(anchors)-3}个锚点")
    print("="*60)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="叙事结构选择器演示")
    parser.add_argument("--type", "-t", default="default", 
                       choices=["default", "suspense", "action", "romance", "epic", "comedy", "art"],
                       help="剧本类型")
    parser.add_argument("--output", "-o", help="输出可视化JSON文件路径")
    parser.add_argument("--config", "-c", help="配置文件路径")
    args = parser.parse_args()
    
    # 创建剧本元数据
    script_type = args.type
    script_metadata = create_sample_script_metadata(script_type)
    
    print(f"\n使用 {script_type} 类型剧本进行测试:")
    print(f"  类型: {script_metadata['genre']}")
    print(f"  情感基调: {script_metadata['emotion_tone']}")
    print(f"  节奏: {script_metadata['pace']}")
    
    # 1. 仅基于元数据选择结构
    print("\n基于元数据选择叙事结构...")
    metadata_result = select_narrative_structure(script_metadata, None, args.config)
    display_structure_result(metadata_result)
    
    # 2. 加载场景，检测锚点并选择结构
    print("\n加载场景，基于锚点和元数据选择叙事结构...")
    scenes = load_sample_scenes(script_type)
    print(f"  加载了 {len(scenes)} 个场景")
    
    # 检测锚点
    anchors = detect_anchors(scenes)
    print(f"  检测到 {len(anchors)} 个锚点")
    
    # 基于锚点和元数据选择结构
    result = select_narrative_structure(script_metadata, anchors, args.config)
    display_structure_result(result)
    
    # 3. 映射锚点到结构
    print("\n将锚点映射到叙事结构...")
    structure_name = result["pattern_name"]
    selector = StructureSelector(args.config)
    anchor_mapping = selector.map_anchors_to_structure(anchors, structure_name)
    
    for step, step_anchors in anchor_mapping.items():
        print(f"  {step}: {len(step_anchors)}个锚点")
    
    # 4. 获取所有可用结构
    print("\n所有可用的叙事结构模式:")
    all_patterns = get_structure_patterns()
    for name in all_patterns:
        print(f"  - {name}")
    
    # 5. 生成可视化数据
    if args.output:
        print(f"\n生成叙事结构可视化数据...")
        visualization_result = generate_structure_visualization(
            anchors, structure_name, args.output, args.config
        )
        
        if visualization_result["success"]:
            print(f"  可视化数据已保存到: {args.output}")
        else:
            print(f"  生成可视化数据失败: {visualization_result.get('error', '未知错误')}")
    
    print("\n演示完成!")


if __name__ == "__main__":
    main() 