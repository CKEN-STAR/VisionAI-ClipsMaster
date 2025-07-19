#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
悬念植入器演示脚本

演示如何使用悬念植入器在短剧剧本中构建悬念架构
"""

import os
import sys
import json
import argparse
from typing import Dict, List, Any, Optional
import random

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

# 导入必要的模块
from src.nonlinear.suspense_planter import SuspensePlanter, ClueType, plant_suspense
from src.narrative.anchor_types import AnchorInfo, AnchorType
from src.narrative.anchor_detector import detect_anchors


# JSON序列化器，处理自定义类型
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, AnchorType):
            return obj.value  # 将枚举转换为值
        if hasattr(obj, '__dict__'):
            # 将对象转换为字典
            result = {}
            for key, val in obj.__dict__.items():
                if key.startswith('_'):
                    continue  # 跳过私有属性
                result[key] = val
            return result
        return super().default(obj)


def load_sample_script(script_type: str = "detective") -> List[Dict[str, Any]]:
    """
    加载示例剧本
    
    Args:
        script_type: 剧本类型，可选值：detective, romance, action
        
    Returns:
        场景列表
    """
    scripts = {
        "detective": [
            {
                "scene_id": "scene001",
                "text": "夜晚，空旷的停车场。侦探李明下车，走向一栋废弃大楼。",
                "character": "李明",
                "duration": 5.2,
                "tags": ["开场", "夜晚"]
            },
            {
                "scene_id": "scene002",
                "text": "李明走进大楼，手电筒照着四周。地上有些杂乱的脚印。",
                "character": "李明",
                "prop": "手电筒",
                "duration": 4.8,
                "tags": ["线索"]
            },
            {
                "scene_id": "scene003",
                "text": "「李明：看来有人比我先到一步。」李明仔细观察着地上的脚印。",
                "character": "李明",
                "duration": 3.5
            },
            {
                "scene_id": "scene004",
                "text": "办公室内，王秘书正在整理文件。电话突然响起。",
                "character": "王秘书",
                "duration": 4.0,
                "tags": ["新场景"]
            },
            {
                "scene_id": "scene005",
                "text": "「王秘书：喂，您好。」「神秘声音：文件准备好了吗？」「王秘书：（紧张）都按您说的做了。」",
                "characters": ["王秘书", "神秘声音"],
                "duration": 6.5
            },
            {
                "scene_id": "scene006",
                "text": "李明在大楼二层发现一个打开的保险箱，里面空空如也。",
                "character": "李明",
                "prop": "保险箱",
                "duration": 5.0,
                "tags": ["关键道具"]
            },
            {
                "scene_id": "scene007",
                "text": "「李明：晚了一步。」李明拿出手机，拨通一个号码。",
                "character": "李明",
                "prop": "手机",
                "duration": 3.2
            },
            {
                "scene_id": "scene008",
                "text": "「李明：张局长，保险箱已经被人清空了。」「张局长：什么？！那个U盘对我们至关重要！」",
                "characters": ["李明", "张局长"],
                "duration": 7.0,
                "tags": ["重要信息"]
            },
            {
                "scene_id": "scene009",
                "text": "王秘书驾车离开办公大楼，不安地看了看后视镜。",
                "character": "王秘书",
                "duration": 4.3
            },
            {
                "scene_id": "scene010",
                "text": "李明回到车上，发现一个信封放在挡风玻璃下。",
                "character": "李明",
                "prop": "信封",
                "duration": 3.8,
                "tags": ["转折点"]
            },
            {
                "scene_id": "scene011",
                "text": "李明打开信封，里面是一张照片，照片上是王秘书和一个陌生男子的交易画面。",
                "character": "李明",
                "prop": "照片",
                "duration": 6.5,
                "tags": ["关键信息"]
            },
            {
                "scene_id": "scene012",
                "text": "「李明：（自言自语）原来如此...」李明若有所思地看着照片。",
                "character": "李明",
                "duration": 4.0
            },
            {
                "scene_id": "scene013",
                "text": "王秘书到达一个隐蔽的仓库，四下张望后匆忙进入。",
                "character": "王秘书",
                "duration": 5.5
            },
            {
                "scene_id": "scene014",
                "text": "仓库内，王秘书将一个U盘交给陌生男子。「王秘书：这是你要的东西。现在我可以走了吗？」",
                "characters": ["王秘书", "陌生男子"],
                "prop": "U盘",
                "duration": 7.2,
                "tags": ["高潮"]
            },
            {
                "scene_id": "scene015",
                "text": "「陌生男子：（冷笑）当然，不过...」话音未落，仓库大门被撞开。",
                "character": "陌生男子",
                "duration": 5.0
            },
            {
                "scene_id": "scene016",
                "text": "李明带着警察冲进仓库。「李明：警察！不许动！」",
                "characters": ["李明", "警察"],
                "duration": 4.8,
                "tags": ["高潮", "冲突"]
            },
            {
                "scene_id": "scene017",
                "text": "混乱中，陌生男子试图逃跑，但被警察制服。U盘掉在地上。",
                "characters": ["陌生男子", "警察"],
                "prop": "U盘",
                "duration": 6.0
            },
            {
                "scene_id": "scene018",
                "text": "李明捡起U盘，看向惊慌失措的王秘书。「李明：游戏结束了。」",
                "characters": ["李明", "王秘书"],
                "prop": "U盘",
                "duration": 5.5,
                "tags": ["结局"]
            }
        ],
        "romance": [
            # 省略浪漫剧本示例...
            {
                "scene_id": "scene001",
                "text": "春日午后，咖啡馆。小雨坐在窗边，翻看着一本书。",
                "character": "小雨",
                "duration": 4.5,
                "tags": ["开场", "春天"]
            },
            {
                "scene_id": "scene002",
                "text": "门铃响起，小雨不经意抬头，与刚进门的陈远对视一秒。",
                "characters": ["小雨", "陈远"],
                "duration": 3.8
            },
            {
                "scene_id": "scene003",
                "text": "陈远点了杯咖啡，在靠窗的位置坐下，恰好与小雨只隔一张桌子。",
                "character": "陈远",
                "duration": 5.0
            }
            # 更多场景...省略
        ],
        "action": [
            # 省略动作剧本示例...
            {
                "scene_id": "scene001",
                "text": "废弃工厂，夜。张刚小心翼翼地潜行在集装箱之间。",
                "character": "张刚",
                "duration": 6.0,
                "tags": ["开场", "夜晚"]
            },
            {
                "scene_id": "scene002",
                "text": "远处，几名持枪守卫在巡逻。张刚迅速躲到一个集装箱后。",
                "characters": ["张刚", "守卫"],
                "duration": 5.2
            },
            {
                "scene_id": "scene003",
                "text": "张刚从口袋掏出一张照片，照片上是一个金属箱子。",
                "character": "张刚",
                "prop": "照片",
                "duration": 4.0,
                "tags": ["任务目标"]
            }
            # 更多场景...省略
        ]
    }
    
    return scripts.get(script_type, scripts["detective"])


def print_script(script: List[Dict[str, Any]], max_scenes: int = None) -> None:
    """
    打印剧本内容
    
    Args:
        script: 场景列表
        max_scenes: 最多显示的场景数，None表示全部显示
    """
    if max_scenes is None:
        max_scenes = len(script)
    
    print("\n====== 剧本内容 ======")
    for i, scene in enumerate(script[:max_scenes]):
        print(f"场景 {i+1}: {scene.get('scene_id', f'scene{i+1}')}")
        print(f"  内容: {scene.get('text', '')}")
        
        if 'characters' in scene:
            chars = scene['characters']
            print(f"  角色: {', '.join(chars) if isinstance(chars, list) else chars}")
        elif 'character' in scene:
            print(f"  角色: {scene['character']}")
            
        if 'tags' in scene:
            tags = scene['tags']
            print(f"  标签: {', '.join(tags) if isinstance(tags, list) else tags}")
            
        if 'prop' in scene:
            print(f"  道具: {scene['prop']}")
            
        print(f"  时长: {scene.get('duration', 0):.1f}秒")
        print()


def print_suspense_comparison(original: List[Dict[str, Any]], modified: List[Dict[str, Any]], 
                            max_scenes: int = None) -> None:
    """
    打印原始剧本和添加悬念后的对比
    
    Args:
        original: 原始场景列表
        modified: 修改后的场景列表
        max_scenes: 最多显示的场景数，None表示全部显示
    """
    if max_scenes is None:
        max_scenes = min(len(original), len(modified))
    
    print("\n====== 悬念植入前后对比 ======")
    
    for i in range(min(max_scenes, len(original), len(modified))):
        orig_scene = original[i]
        mod_scene = modified[i]
        
        # 检查是否有变化
        orig_text = orig_scene.get('text', '')
        mod_text = mod_scene.get('text', '')
        
        if orig_text != mod_text:
            print(f"场景 {i+1} ({orig_scene.get('scene_id', f'scene{i+1}')})")
            print("  原始内容:")
            print(f"    {orig_text}")
            print("  植入悬念后:")
            print(f"    {mod_text}")
            
            # 高亮显示添加的内容
            if orig_text in mod_text:
                added_text = mod_text.replace(orig_text, '').strip()
                print(f"  添加内容: {added_text}")
                
            print()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='悬念植入器演示')
    parser.add_argument('--type', '-t', choices=['detective', 'romance', 'action'], 
                      default='detective', help='剧本类型')
    parser.add_argument('--mode', '-m', choices=['early', 'full'], 
                      default='full', help='植入模式 (early=仅前期, full=完整)')
    parser.add_argument('--max', type=int, default=None, 
                      help='最多显示的场景数量')
    parser.add_argument('--save', '-s', action='store_true', 
                      help='是否保存结果到文件')
    
    args = parser.parse_args()
    
    print(f"===== 悬念植入器演示 - {args.type}剧本/{args.mode}模式 =====")
    
    # 加载示例剧本
    script = load_sample_script(args.type)
    
    # 打印原始剧本
    print_script(script, args.max)
    
    # 检测剧情锚点
    try:
        anchors = detect_anchors(script)
    except Exception as e:
        print(f"检测锚点时出错: {str(e)}")
        anchors = []  # 使用空列表作为回退
        
    # 植入悬念
    planter = SuspensePlanter()
    
    if args.mode == 'early':
        # 仅在前期植入线索
        modified_script = planter.plant_early_clues(script)
        print("\n== 已在剧本前半部分植入伏笔和线索 ==")
    else:
        # 完整悬念植入
        modified_script = planter.plant_suspense(script, anchors)
        print("\n== 已在剧本全程策略性植入悬念元素 ==")
    
    # 打印对比
    print_suspense_comparison(script, modified_script, args.max)
    
    # 统计悬念线索分布
    early_count = mid_count = late_count = 0
    total_scenes = len(modified_script)
    
    for i, scene in enumerate(modified_script):
        tags = scene.get('tags', [])
        if isinstance(tags, str):
            tags = [tags]
            
        if '悬念线索' in tags:
            rel_pos = i / total_scenes
            if rel_pos < 0.35:
                early_count += 1
            elif rel_pos < 0.7:
                mid_count += 1
            else:
                late_count += 1
                
    print("\n== 悬念线索分布统计 ==")
    print(f"前期线索: {early_count} 个")
    print(f"中期线索: {mid_count} 个")
    print(f"后期线索: {late_count} 个")
    print(f"总计: {early_count + mid_count + late_count} 个")
    
    # 保存结果
    if args.save:
        output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "output")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        output_file = os.path.join(output_dir, f"suspense_{args.type}_{args.mode}.json")
        
        result = {
            "script_type": args.type,
            "mode": args.mode,
            "original_script": script,
            "modified_script": modified_script,
            "stats": {
                "early_clues": early_count,
                "mid_clues": mid_count,
                "late_clues": late_count,
                "total_clues": early_count + mid_count + late_count
            }
        }
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2, cls=CustomJSONEncoder)
                
            print(f"\n结果已保存到: {output_file}")
        except Exception as e:
            print(f"\n保存结果时出错: {str(e)}")


if __name__ == '__main__':
    main() 