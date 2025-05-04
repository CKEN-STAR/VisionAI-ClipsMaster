#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
节奏调节器演示脚本

演示如何使用节奏调节器调整短剧节奏，创造更富表现力的剪辑
"""

import os
import sys
import json
import argparse
from typing import Dict, List, Any, Optional
import random
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

# 导入必要的模块
from src.nonlinear.rhythm_tuner import RhythmTuner, adjust_pacing, get_available_structures
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
        script_type: 剧本类型，可选值：detective, romance, action, inspiration
        
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
        "inspiration": [
            {
                "scene_id": "scene001",
                "text": "「旁白：你是否曾经感到迷茫，不知道自己该走向何方？」黑屏，字幕淡入。",
                "duration": 4.0,
                "tags": ["开场", "提问"]
            },
            {
                "scene_id": "scene002",
                "text": "主角小林坐在办公桌前，面对电脑屏幕，一脸疲惫。窗外是灰蒙蒙的天空。",
                "character": "小林",
                "duration": 5.0,
                "tags": ["低谷"]
            },
            {
                "scene_id": "scene003",
                "text": "「旁白：每天重复同样的工作，感觉生活失去了意义...」",
                "duration": 3.0
            },
            {
                "scene_id": "scene004",
                "text": "小林翻开一本书，是《改变从现在开始》。镜头特写书页上的一句话：「成功不是偶然，而是习惯。」",
                "character": "小林",
                "prop": "书",
                "duration": 4.5,
                "tags": ["转折点", "启示"]
            },
            {
                "scene_id": "scene005",
                "text": "「旁白：改变，往往始于一个决定，一个行动。」",
                "duration": 3.2,
                "tags": ["激励"]
            },
            {
                "scene_id": "scene006",
                "text": "小林开始清晨跑步。画面显示：Day 1。呼吸困难，才跑了几分钟就停下来。",
                "character": "小林",
                "duration": 4.0,
                "tags": ["行动", "开始"]
            },
            {
                "scene_id": "scene007",
                "text": "快速剪辑：Day 7, Day 15, Day 30。小林的跑步姿态越来越轻松，距离越来越远。",
                "character": "小林",
                "duration": 6.0,
                "tags": ["进步", "成长"]
            },
            {
                "scene_id": "scene008",
                "text": "小林开始学习新技能，屏幕上显示编程代码。时钟快速旋转，表示时间流逝。",
                "character": "小林",
                "duration": 5.5,
                "tags": ["学习", "努力"]
            },
            {
                "scene_id": "scene009",
                "text": "「旁白：成功是由无数个小进步累积而成...」",
                "duration": 3.0,
                "tags": ["干货"]
            },
            {
                "scene_id": "scene010",
                "text": "小林参加面试，与面试官热情握手。",
                "character": "小林",
                "duration": 4.2,
                "tags": ["机会"]
            },
            {
                "scene_id": "scene011",
                "text": "小林收到录用通知，欣喜若狂。",
                "character": "小林",
                "prop": "通知书",
                "duration": 3.8,
                "tags": ["成功", "高潮"]
            },
            {
                "scene_id": "scene012",
                "text": "小林站在新公司前，阳光照射在他的脸上，充满自信。",
                "character": "小林",
                "duration": 4.5,
                "tags": ["新起点"]
            },
            {
                "scene_id": "scene013",
                "text": "「旁白：记住，永远不会太晚，重要的是你是否愿意迈出第一步...」",
                "duration": 4.0,
                "tags": ["激励", "金句"]
            },
            {
                "scene_id": "scene014",
                "text": "画面切回最初的办公室场景，但这次窗外阳光明媚，小林面带微笑。",
                "character": "小林",
                "duration": 5.0,
                "tags": ["对比", "变化"]
            },
            {
                "scene_id": "scene015",
                "text": "「旁白：改变，就是现在。」文字特效：「改变，从现在开始」",
                "duration": 4.0,
                "tags": ["结语", "呼吁"]
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


def visualize_pacing(original_scenes: List[Dict[str, Any]], adjusted_scenes: List[Dict[str, Any]], 
                    structure_name: str) -> None:
    """
    可视化展示节奏调整前后的对比
    
    Args:
        original_scenes: 原始场景列表
        adjusted_scenes: 调整后的场景列表
        structure_name: 使用的节奏结构名称
    """
    # 提取持续时间数据
    original_durations = []
    adjusted_durations = []
    scene_indices = []
    
    for i, (orig, adj) in enumerate(zip(original_scenes, adjusted_scenes)):
        # 获取原始时长
        if "duration" in orig:
            orig_duration = orig["duration"]
        elif "time" in orig and "start" in orig["time"] and "end" in orig["time"]:
            orig_duration = orig["time"]["end"] - orig["time"]["start"]
        else:
            continue
            
        # 获取调整后时长
        if "duration" in adj:
            adj_duration = adj["duration"]
        elif "time" in adj and "start" in adj["time"] and "end" in adj["time"]:
            adj_duration = adj["time"]["end"] - adj["time"]["start"]
        else:
            continue
        
        original_durations.append(orig_duration)
        adjusted_durations.append(adj_duration)
        scene_indices.append(i + 1)
    
    # 创建图表
    plt.figure(figsize=(12, 6))
    
    # 绘制条形图
    width = 0.35
    plt.bar(scene_indices, original_durations, width, label='原始时长', alpha=0.7, color='#3498db')
    plt.bar([x + width for x in scene_indices], adjusted_durations, width, label='调整后时长', alpha=0.7, color='#e74c3c')
    
    # 添加调整因子曲线
    ax1 = plt.gca()
    ax2 = ax1.twinx()
    factors = [s["rhythm_adjustments"]["adjustment_factor"] for s in adjusted_scenes if "rhythm_adjustments" in s]
    if factors:
        ax2.plot(scene_indices, factors, 'g-', marker='o', linewidth=2, label='调整因子')
        ax2.set_ylabel('调整因子', color='g')
        ax2.tick_params(axis='y', labelcolor='g')
        ax2.set_ylim(0.5, 2.0)
        ax2.axhline(y=1.0, color='g', linestyle='--', alpha=0.3)
    
    # 设置图表属性
    plt.title(f'节奏结构：{structure_name} - 场景时长调整对比')
    ax1.set_xlabel('场景编号')
    ax1.set_ylabel('时长(秒)')
    ax1.legend(loc='upper left')
    if factors:
        ax2.legend(loc='upper right')
    
    plt.grid(True, alpha=0.3)
    ax1.xaxis.set_major_locator(MaxNLocator(integer=True))
    
    # 保存图表
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "output")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f"rhythm_{structure_name.replace(' ', '_')}.png"))
    print(f"节奏调整可视化图表已保存至 output/rhythm_{structure_name.replace(' ', '_')}.png")
    plt.close()


def print_script_info(scenes: List[Dict[str, Any]], title: str = "剧本内容", max_scenes: int = None) -> None:
    """
    打印剧本信息
    
    Args:
        scenes: 场景列表
        title: 标题
        max_scenes: 最多显示的场景数，None表示全部显示
    """
    if max_scenes is None:
        max_scenes = len(scenes)
    else:
        max_scenes = min(max_scenes, len(scenes))
    
    print(f"\n====== {title} ======")
    
    for i in range(max_scenes):
        scene = scenes[i]
        scene_id = scene.get("scene_id", f"scene{i+1}")
        
        # 获取时长
        if "duration" in scene:
            duration = scene["duration"]
        elif "time" in scene and "start" in scene["time"] and "end" in scene["time"]:
            duration = scene["time"]["end"] - scene["time"]["start"]
        else:
            duration = "未知"
        
        print(f"场景 {i+1} ({scene_id}): 时长={duration}秒")
        print(f"  内容: {scene.get('text', '')}")
        
        # 打印调整信息（如果有）
        if "rhythm_adjustments" in scene:
            ra = scene["rhythm_adjustments"]
            print(f"  节奏调整: 原始={ra.get('original_duration', 0):.1f}秒, "
                  f"调整后={ra.get('adjusted_duration', 0):.1f}秒, "
                  f"因子={ra.get('adjustment_factor', 1.0):.2f}")
        
        # 打印转场信息（如果有）
        if "transition" in scene:
            trans = scene["transition"]
            print(f"  转场: {trans.get('type', '无')}")
            
        print()


def adjust_script_rhythm(script: List[Dict[str, Any]], structure: str = None, 
                        detect_narrative_anchors: bool = True, 
                        visualize: bool = True) -> List[Dict[str, Any]]:
    """
    调整剧本节奏
    
    Args:
        script: 原始剧本
        structure: 节奏结构，None表示自动检测
        detect_narrative_anchors: 是否检测叙事锚点
        visualize: 是否可视化结果
        
    Returns:
        调整后的剧本
    """
    # 初始化节奏调节器
    tuner = RhythmTuner()
    
    # 设置节奏结构（如果指定）
    if structure:
        tuner.set_structure(structure)
        used_structure = structure
    else:
        # 自动检测
        used_structure = tuner._detect_structure(script)
        print(f"自动检测到的节奏结构: {used_structure}")
    
    # 获取叙事锚点（如果需要）
    anchors = None
    if detect_narrative_anchors:
        try:
            anchors = detect_anchors(script)
            print(f"检测到 {len(anchors)} 个叙事锚点")
            for i, anchor in enumerate(anchors):
                print(f"  锚点 {i+1}: 类型={anchor.type.value}, 位置={anchor.position:.2f}, "
                      f"描述={anchor.description}")
        except Exception as e:
            print(f"锚点检测失败: {str(e)}")
    
    # 调整节奏
    adjusted_script = tuner.adjust_pacing(script, anchors)
    
    # 可视化结果
    if visualize:
        visualize_pacing(script, adjusted_script, used_structure)
    
    return adjusted_script


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='节奏调节器演示')
    parser.add_argument('--type', '-t', choices=['detective', 'romance', 'action', 'inspiration'], 
                      default='detective', help='剧本类型')
    parser.add_argument('--structure', '-s', 
                      help='节奏结构，不指定则自动检测')
    parser.add_argument('--no-anchors', action='store_true', 
                      help='不使用叙事锚点')
    parser.add_argument('--no-vis', action='store_true',
                      help='不生成可视化图表')
    parser.add_argument('--max', '-m', type=int, default=5,
                      help='显示的最大场景数，默认为5')
    parser.add_argument('--save', action='store_true',
                      help='保存调整后的剧本到文件')
    parser.add_argument('--compare-all', action='store_true',
                      help='比较所有可用的节奏结构')
    
    args = parser.parse_args()
    
    print(f"===== 节奏调节器演示 - {args.type}类型剧本 =====")
    
    # 加载示例剧本
    script = load_sample_script(args.type)
    
    # 如果需要比较所有结构
    if args.compare_all:
        tuner = RhythmTuner()
        structures = tuner.get_available_structures()
        
        print(f"\n将比较所有 {len(structures)} 种节奏结构")
        
        for structure in structures:
            print(f"\n----- 使用节奏结构: {structure} -----")
            
            # 调整节奏
            adjusted = adjust_script_rhythm(
                script, 
                structure=structure,
                detect_narrative_anchors=not args.no_anchors,
                visualize=not args.no_vis
            )
            
            # 输出简短摘要
            print(f"结构 '{structure}' 调整结果摘要:")
            
            # 计算平均调整因子
            factors = [s["rhythm_adjustments"]["adjustment_factor"] 
                     for s in adjusted if "rhythm_adjustments" in s]
            
            if factors:
                avg_factor = sum(factors) / len(factors)
                min_factor = min(factors)
                max_factor = max(factors)
                print(f"调整因子: 平均={avg_factor:.2f}, 最小={min_factor:.2f}, 最大={max_factor:.2f}")
                
            # 计算调整前后总时长变化
            total_before = sum([s.get("duration", 0) for s in script])
            total_after = sum([s.get("duration", 0) for s in adjusted])
            print(f"总时长: 调整前={total_before:.1f}秒, 调整后={total_after:.1f}秒, 变化={((total_after-total_before)/total_before*100):.1f}%")
            
            print("-" * 40)
    else:
        # 打印原始剧本信息
        print_script_info(script, "原始剧本", args.max)
        
        # 调整节奏
        adjusted_script = adjust_script_rhythm(
            script, 
            structure=args.structure,
            detect_narrative_anchors=not args.no_anchors,
            visualize=not args.no_vis
        )
        
        # 打印调整后的剧本信息
        print_script_info(adjusted_script, "调整后剧本", args.max)
        
        # 保存结果
        if args.save:
            output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "output")
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
                
            # 获取使用的结构名称
            if args.structure:
                structure_name = args.structure
            else:
                # 从任意场景的元数据中获取
                for scene in adjusted_script:
                    if "metadata" in scene and "rhythm_structure" in scene["metadata"]:
                        structure_name = scene["metadata"]["rhythm_structure"]
                        break
                else:
                    structure_name = "unknown"
            
            output_file = os.path.join(output_dir, f"rhythm_{args.type}_{structure_name.replace(' ', '_')}.json")
            
            # 构建结果字典
            result = {
                "script_type": args.type,
                "rhythm_structure": structure_name,
                "original_script": script,
                "adjusted_script": adjusted_script
            }
            
            # 保存到文件
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2, cls=CustomJSONEncoder)
                print(f"\n调整后的剧本已保存至: {output_file}")
            except Exception as e:
                print(f"\n保存剧本失败: {str(e)}")


if __name__ == "__main__":
    main() 