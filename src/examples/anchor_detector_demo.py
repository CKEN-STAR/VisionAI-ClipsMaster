"""
关键情节锚点检测演示

演示如何使用关键情节锚点检测器识别视频或剧本中的关键情节点
"""

import os
import json
import random
from typing import Dict, List, Any
import argparse
from pathlib import Path

from src.narrative.anchor_detector import detect_anchors, get_top_anchors, visualize_anchors
from src.narrative.anchor_types import AnchorType


def create_sample_data(num_scenes: int = 20) -> List[Dict[str, Any]]:
    """
    创建示例场景数据用于演示
    
    Args:
        num_scenes: 场景数量
        
    Returns:
        场景列表
    """
    scenes = []
    
    # 场景类型
    scene_types = ["opening", "exposition", "rising_action", "conflict", "climax", "falling_action", "resolution"]
    
    # 角色名称
    character_names = ["张三", "李四", "王五", "赵六", "小明", "小红", "小刚"]
    
    # 情感曲线（基础情感曲线+随机波动）
    # 生成一个起伏的情感曲线：开始平稳，中间波动大，结尾回归平稳
    base_emotion = [0.2, 0.3, 0.1, -0.2, -0.3, -0.5, -0.7, -0.4, -0.1, 0.2, 0.5, 0.8, 0.7, 0.4, 0.3, 0.4, 0.5, 0.6, 0.5, 0.3]
    if len(base_emotion) < num_scenes:
        # 如果需要更多场景，复制并添加一些随机波动
        while len(base_emotion) < num_scenes:
            base_emotion.append(base_emotion[len(base_emotion) % len(base_emotion)] + random.uniform(-0.2, 0.2))
    
    # 文本模板
    text_templates = {
        "opening": [
            "故事开始于一个平静的小镇。{char1}正在家中准备出门。",
            "{char1}走在去学校的路上，今天是开学第一天。",
            "清晨，{char1}被闹钟叫醒，开始了新的一天。"
        ],
        "exposition": [
            "{char1}和{char2}是多年的好友，他们经常一起度过周末。",
            "在镇上的咖啡馆里，{char1}偶然遇到了{char2}。",
            "{char1}向{char2}介绍了自己的新计划。"
        ],
        "rising_action": [
            "{char1}发现了一个奇怪的现象，决定深入调查。",
            "当{char1}准备离开时，{char2}突然出现并带来了重要消息。",
            "{char1}和{char2}讨论着最近发生的怪事。"
        ],
        "conflict": [
            "{char1}和{char2}因为误会发生了激烈的争吵。",
            "当{char1}得知真相后，感到非常愤怒和背叛。",
            "{char1}面对着艰难的抉择，内心充满矛盾。"
        ],
        "climax": [
            "关键时刻，{char1}做出了勇敢的决定。",
            "在千钧一发之际，{char1}终于明白了一切。",
            "真相揭露的那一刻，所有人都震惊了。"
        ],
        "falling_action": [
            "危机解除后，{char1}和{char2}终于有机会好好谈一谈。",
            "随着事情的真相浮出水面，局势开始明朗。",
            "{char1}开始反思自己的行为和决定。"
        ],
        "resolution": [
            "{char1}和{char2}重修旧好，一起面对未来。",
            "所有谜题都得到了解答，{char1}终于松了一口气。",
            "故事接近尾声，{char1}和{char2}相视而笑。"
        ]
    }
    
    # 悬念关键词
    suspense_keywords = ["谜", "问题", "未知", "神秘", "为什么", "怎么会", "疑惑"]
    revelation_keywords = ["原来", "真相", "明白", "解开", "发现"]
    
    # 生成场景
    total_duration = 0
    for i in range(num_scenes):
        # 决定场景类型
        scene_progress = i / num_scenes
        if scene_progress < 0.1:
            scene_type = "opening"
        elif scene_progress < 0.25:
            scene_type = "exposition"
        elif scene_progress < 0.4:
            scene_type = "rising_action"
        elif scene_progress < 0.6:
            scene_type = "conflict"
        elif scene_progress < 0.7:
            scene_type = "climax"
        elif scene_progress < 0.85:
            scene_type = "falling_action"
        else:
            scene_type = "resolution"
        
        # 选择角色
        num_chars = random.randint(1, 3)
        scene_chars = random.sample(character_names, min(num_chars, len(character_names)))
        
        # 生成文本
        templates = text_templates.get(scene_type, text_templates["exposition"])
        text_template = random.choice(templates)
        
        # 修复：确保有足够的角色填充模板
        char_dict = {}
        for j in range(1, 3):  # 最多支持2个角色
            char_key = f"char{j}"
            if char_key in text_template:
                # 如果模板需要这个角色但场景角色不足，使用第一个角色
                if j-1 < len(scene_chars):
                    char_dict[char_key] = scene_chars[j-1]
                else:
                    char_dict[char_key] = scene_chars[0] if scene_chars else "某人"
        
        try:
            text = text_template.format(**char_dict)
        except KeyError as e:
            # 如果仍有缺失的角色，使用一个通用替代
            missing_key = str(e).strip("'")
            char_dict[missing_key] = "某人"
            text = text_template.format(**char_dict)
        
        # 添加一些悬念或揭示关键词
        if scene_type in ["rising_action", "conflict"] and random.random() < 0.4:
            suspense_word = random.choice(suspense_keywords)
            text += f" {suspense_word}这一切到底是怎么回事？"
        
        if scene_type in ["climax", "falling_action"] and random.random() < 0.5:
            revelation_word = random.choice(revelation_keywords)
            text += f" {revelation_word}一切都有了答案。"
        
        # 为冲突场景添加关系关键词
        if scene_type == "conflict" and random.random() < 0.7:
            relation_keywords = ["相遇", "分别", "和好", "争吵", "决裂", "结盟", "对抗"]
            relation_word = random.choice(relation_keywords)
            text += f" 这是他们关系中的一次重要{relation_word}。"
        
        # 创建情感分数
        emotion_score = base_emotion[i]
        if scene_type == "conflict":
            emotion_score = min(-0.3, emotion_score - random.uniform(0.1, 0.3))
        elif scene_type == "climax":
            emotion_score = emotion_score * 1.5  # 放大情感
        
        # 限制情感范围
        emotion_score = max(-1.0, min(1.0, emotion_score))
        
        # 设置场景时长
        duration = random.uniform(3.0, 10.0)
        if scene_type == "climax":
            duration *= 1.5  # 高潮场景更长
        
        total_duration += duration
        
        # 创建场景
        scene = {
            "id": f"scene_{i+1}",
            "type": scene_type,
            "text": text,
            "characters": scene_chars,
            "emotion_score": emotion_score,
            "duration": duration,
            "start_time": total_duration - duration,
            "end_time": total_duration
        }
        
        scenes.append(scene)
    
    return scenes


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="关键情节锚点检测演示")
    parser.add_argument("--input", "-i", help="输入场景JSON文件路径")
    parser.add_argument("--output", "-o", help="输出可视化JSON文件路径")
    parser.add_argument("--num-scenes", "-n", type=int, default=20, help="生成的示例场景数量")
    args = parser.parse_args()
    
    # 获取场景数据
    if args.input and os.path.exists(args.input):
        print(f"从文件加载场景: {args.input}")
        with open(args.input, "r", encoding="utf-8") as f:
            scenes = json.load(f)
    else:
        print(f"生成示例场景: {args.num_scenes}个")
        scenes = create_sample_data(args.num_scenes)
        
        # 如果指定了输入文件但不存在，保存生成的数据
        if args.input:
            os.makedirs(os.path.dirname(os.path.abspath(args.input)), exist_ok=True)
            with open(args.input, "w", encoding="utf-8") as f:
                json.dump(scenes, f, ensure_ascii=False, indent=2)
            print(f"已保存示例场景到: {args.input}")
    
    # 检测锚点
    print("检测关键情节锚点...")
    anchors = detect_anchors(scenes)
    print(f"共检测到 {len(anchors)} 个锚点")
    
    # 显示每种类型的锚点数量
    anchor_types = {}
    for anchor in anchors:
        anchor_type = anchor.type.value
        if anchor_type not in anchor_types:
            anchor_types[anchor_type] = 0
        anchor_types[anchor_type] += 1
    
    print("\n锚点类型统计:")
    for anchor_type, count in anchor_types.items():
        print(f"- {anchor_type}: {count}个")
    
    # 获取最重要的锚点
    top_anchors = get_top_anchors(anchors, 5)
    
    print("\n最重要的5个锚点:")
    for i, anchor in enumerate(top_anchors):
        print(f"{i+1}. [{anchor.type.value}] {anchor.description} " + 
              f"(位置: {anchor.position:.2f}, 重要性: {anchor.importance:.2f})")
    
    # 生成并保存可视化数据
    total_duration = sum(scene.get("duration", 0) for scene in scenes)
    
    output_path = args.output
    if not output_path:
        output_path = "anchor_visualization.json"
    
    visualization_data = visualize_anchors(anchors, total_duration, output_path)
    print(f"\n已保存可视化数据到: {output_path}")
    
    print("\n演示完成!")


if __name__ == "__main__":
    main()