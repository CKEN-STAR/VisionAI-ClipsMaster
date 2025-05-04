#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
示例数据工具

为测试和开发提供各种示例数据，包括脚本、场景和字幕等。
这些数据用于功能测试、演示和开发过程中的调试。
"""

from typing import Dict, List, Any, Optional
import os
import json
import random
import logging
import math

# 创建日志记录器
logger = logging.getLogger(__name__)

def get_sample_script() -> List[Dict[str, Any]]:
    """
    获取示例脚本数据
    
    Returns:
        示例脚本列表
    """
    # 首先尝试加载外部示例数据
    sample_path = os.path.join("data", "samples", "demo_script.json")
    if os.path.exists(sample_path):
        try:
            with open(sample_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                logger.info(f"从 {sample_path} 加载示例脚本")
                return data
        except Exception as e:
            logger.warning(f"加载示例脚本失败: {e}")
    
    # 使用内置示例数据
    logger.info("使用内置示例脚本")
    
    # 创建示例场景
    script = [
        {
            "text": "李明站在小区门口, 手里拿着一束鲜花, 不时地看看手表.",
            "tags": ["开场", "人物介绍"],
            "sentiment": {
                "label": "NEUTRAL",
                "intensity": 0.3
            }
        },
        {
            "text": "小雨匆匆跑来, 脸上带着歉意的笑容. \"对不起, 我迟到了, 路上堵车.\"",
            "tags": ["引入", "角色出场"],
            "sentiment": {
                "label": "POSITIVE",
                "intensity": 0.6
            }
        },
        {
            "text": "李明微笑着递上花束, \"没关系, 我刚到没多久. 这是送给你的.\"",
            "tags": ["互动"],
            "sentiment": {
                "label": "POSITIVE",
                "intensity": 0.8
            }
        },
        {
            "text": "小雨接过花, 脸上洋溢着幸福的笑容. 两人并肩走进餐厅.",
            "tags": ["发展"],
            "sentiment": {
                "label": "POSITIVE",
                "intensity": 0.9
            }
        },
        {
            "text": "餐厅内, 李明紧张地从口袋里掏出一个小盒子. \"我有话想对你说.\"",
            "tags": ["转折点"],
            "sentiment": {
                "label": "NEUTRAL",
                "intensity": 0.5
            }
        },
        {
            "text": "小雨的手机突然响起, 她看了一眼, 脸色立刻变得苍白. \"我妈出事了, 我得马上去医院.\"",
            "tags": ["突发事件"],
            "sentiment": {
                "label": "NEGATIVE",
                "intensity": 0.8
            }
        },
        {
            "text": "医院走廊上, 小雨焦急地等待着, 李明握着她的手, 安慰道: \"别担心, 会没事的.\"",
            "tags": ["危机"],
            "sentiment": {
                "label": "NEGATIVE",
                "intensity": 0.7
            }
        },
        {
            "text": "医生走出手术室, 摘下口罩: \"手术很成功, 没什么大碍了.\"",
            "tags": ["解决"],
            "sentiment": {
                "label": "POSITIVE",
                "intensity": 0.7
            }
        },
        {
            "text": "小雨松了一口气, 靠在李明怀里. 李明这时拿出那个小盒子, 单膝跪地: \"嫁给我好吗?\"",
            "tags": ["高潮"],
            "sentiment": {
                "label": "POSITIVE",
                "intensity": 0.95
            }
        },
        {
            "text": "小雨眼含泪水, 重重地点头. 医院走廊上, 响起了一片祝福的掌声.",
            "tags": ["结局"],
            "sentiment": {
                "label": "POSITIVE",
                "intensity": 0.9
            }
        }
    ]
    
    return script

def get_sample_anchors() -> List[Dict[str, Any]]:
    """
    获取示例锚点数据
    
    Returns:
        示例锚点列表
    """
    return [
        {
            "type": "character",
            "description": "李明第一次出场",
            "position": 0.0,
            "strength": 0.7
        },
        {
            "type": "emotion",
            "description": "两人初次见面的喜悦",
            "position": 0.2,
            "strength": 0.6
        },
        {
            "type": "suspense",
            "description": "李明准备求婚的铺垫",
            "position": 0.4,
            "strength": 0.5
        },
        {
            "type": "conflict",
            "description": "小雨母亲出事的突发状况",
            "position": 0.5,
            "strength": 0.8
        },
        {
            "type": "climax",
            "description": "求婚的高潮时刻",
            "position": 0.9,
            "strength": 0.9
        }
    ]

def generate_random_script(scene_count: int = 10) -> List[Dict[str, Any]]:
    """
    生成随机脚本
    
    Args:
        scene_count: 场景数量
        
    Returns:
        随机生成的脚本
    """
    characters = ["李明", "小雨", "张伟", "王芳", "陈晓", "刘洋", "赵琳"]
    locations = ["咖啡厅", "公园", "办公室", "家里", "学校", "餐厅", "医院", "商场"]
    actions = [
        "微笑着说", "皱眉思考", "惊讶地看着", "生气地转身", "兴奋地跳起来",
        "疑惑地问", "担心地看", "大笑起来", "轻声呢喃", "紧张地握拳"
    ]
    emotions = ["POSITIVE", "NEGATIVE", "NEUTRAL", "SURPRISE"]
    
    script = []
    
    for i in range(scene_count):
        # 随机生成场景内容
        character1 = random.choice(characters)
        character2 = random.choice([c for c in characters if c != character1])
        location = random.choice(locations)
        action1 = random.choice(actions)
        action2 = random.choice(actions)
        
        # 构建场景文本
        position = i / scene_count
        
        if position < 0.2:
            # 开头场景
            text = f"{character1}在{location}里等待着, 不时看表. {character2}走进来, 两人打招呼."
            tags = ["开场", "人物介绍"]
            emotion = "NEUTRAL"
            intensity = 0.3 + random.random() * 0.2
        elif position < 0.4:
            # 发展场景
            text = f"{location}里, {character1}和{character2}正在交谈. {character1}{action1}: \"我有件事想告诉你.\""
            tags = ["发展", "铺垫"]
            emotion = "POSITIVE" if random.random() > 0.5 else "NEUTRAL"
            intensity = 0.4 + random.random() * 0.3
        elif position < 0.6:
            # 冲突场景
            text = f"{character2}听了{character1}的话后, {action2}. 气氛一时变得紧张起来."
            tags = ["冲突", "转折"]
            emotion = "NEGATIVE"
            intensity = 0.5 + random.random() * 0.4
        elif position < 0.8:
            # 高潮场景
            text = f"{location}里的气氛达到了顶点, {character1}和{character2}终于摊牌了."
            tags = ["高潮", "对抗"]
            emotion = random.choice(emotions)
            intensity = 0.7 + random.random() * 0.3
        else:
            # 结局场景
            text = f"最终, {character1}和{character2}在{location}解开了误会, 相视一笑."
            tags = ["结局", "解决"]
            emotion = "POSITIVE"
            intensity = 0.6 + random.random() * 0.4
            
        # 创建场景对象
        scene = {
            "text": text,
            "tags": tags,
            "sentiment": {
                "label": emotion,
                "intensity": intensity
            }
        }
        
        script.append(scene)
        
    return script

def generate_sample_script(scene_count: int = 15, script_type: str = "standard") -> List[Dict[str, Any]]:
    """
    生成带有特定情感曲线模式的样本脚本
    
    Args:
        scene_count: 场景数量
        script_type: 脚本类型，可选值:
            - "standard": 标准类型（起承转合）
            - "emotional": 高情感变化类型
            - "flat": 平坦情感类型
            - "rollercoaster": 情感过山车类型
            
    Returns:
        生成的样本脚本
    """
    characters = ["李明", "小雨", "张伟", "王芳", "陈晓", "刘洋", "赵琳", "黄强", "周静", "陈冰"]
    locations = ["咖啡厅", "公园", "办公室", "家里", "学校", "餐厅", "医院", "商场", "车站", "酒店大堂"]
    events = ["相遇", "争吵", "和解", "告别", "求婚", "表白", "误会", "帮助", "道歉", "庆祝", "冲突", "挽救"]
    emotions = {
        "POSITIVE": ["喜悦", "兴奋", "满足", "幸福", "放松", "安心", "期待", "愉快", "开心"],
        "NEGATIVE": ["愤怒", "悲伤", "失望", "焦虑", "恐惧", "嫉妒", "内疚", "遗憾", "烦躁"],
        "NEUTRAL": ["平静", "沉思", "观察", "等待", "思考", "犹豫", "克制", "迷茫", "淡然"],
        "SURPRISE": ["震惊", "惊喜", "意外", "困惑", "好奇", "不可思议", "惊讶", "吃惊", "难以置信"]
    }
    
    # 生成场景时间码
    def generate_timestamps(count):
        start_times = [i * 30 for i in range(count)]  # 每30秒一个场景
        end_times = [t + random.randint(15, 25) for t in start_times]  # 场景持续15-25秒
        
        # 转换为时间码格式 HH:MM:SS,mmm
        def format_time(seconds):
            m, s = divmod(seconds, 60)
            h, m = divmod(m, 60)
            return f"{h:02d}:{m:02d}:{s:02d},000"
        
        starts = [format_time(t) for t in start_times]
        ends = [format_time(t) for t in end_times]
        
        return list(zip(starts, ends))
    
    # 生成情感强度曲线
    def generate_emotion_curve(count, curve_type):
        if curve_type == "standard":
            # 标准情感曲线：开始平稳，中间上升，高潮后降低
            return [0.3] * int(count * 0.2) + \
                   [0.3 + 0.6 * i/(count * 0.6) for i in range(int(count * 0.6))] + \
                   [0.9 - 0.3 * i/(count * 0.2) for i in range(int(count * 0.2))]
        
        elif curve_type == "emotional":
            # 高情感变化：大起大落
            base = [0.2 + 0.7 * math.sin(i * math.pi * 3 / count) for i in range(count)]
            # 添加随机波动
            return [min(1.0, max(0.1, v + random.uniform(-0.1, 0.1))) for v in base]
        
        elif curve_type == "flat":
            # 平坦情感：很少变化
            base = [0.4 + random.uniform(-0.05, 0.05) for _ in range(count)]
            # 添加1-2个小高峰
            if count > 5:
                peaks = random.sample(range(count), min(2, count // 5))
                for p in peaks:
                    base[p] = 0.6 + random.uniform(0, 0.2)
            return base
        
        elif curve_type == "rollercoaster":
            # 情感过山车：频繁大幅度变化
            base = []
            current = 0.5
            for _ in range(count):
                # 大概率改变方向
                direction = random.choice([-1, 1]) if random.random() > 0.3 else (1 if current < 0.5 else -1)
                change = random.uniform(0.15, 0.35) * direction
                current = max(0.1, min(0.9, current + change))
                base.append(current)
            return base
        
        # 默认返回标准曲线
        return [0.5] * count
    
    # 生成情感标签
    def get_emotion_label(intensity):
        if intensity > 0.7:
            return random.choice(["POSITIVE", "SURPRISE"]) if random.random() > 0.3 else "NEGATIVE"
        elif intensity < 0.3:
            return "NEUTRAL"
        else:
            return random.choice(["POSITIVE", "NEGATIVE", "NEUTRAL"])
    
    # 生成时间码
    timestamps = generate_timestamps(scene_count)
    
    # 生成情感曲线
    intensity_curve = generate_emotion_curve(scene_count, script_type)
    # 确保长度匹配
    intensity_curve = intensity_curve[:scene_count]
    while len(intensity_curve) < scene_count:
        intensity_curve.append(0.5)
    
    # 生成剧本
    script = []
    
    # 确保有主要角色
    main_characters = random.sample(characters, min(4, len(characters)))
    
    for i in range(scene_count):
        # 选择角色和场景
        char_count = random.randint(1, 3)
        scene_chars = random.sample(main_characters, min(char_count, len(main_characters)))
        location = random.choice(locations)
        
        # 选择情感
        intensity = intensity_curve[i]
        emotion_label = get_emotion_label(intensity)
        emotion_desc = random.choice(emotions[emotion_label])
        
        # 生成场景描述
        if i == 0:
            # 开场场景
            text = f"{scene_chars[0]}独自一人在{location}，{random.choice(emotions[emotion_label])}地等待着什么。"
            if len(scene_chars) > 1:
                text += f"{scene_chars[1]}出现在远处，向这边走来。"
        
        elif i == scene_count - 1:
            # 结束场景
            if emotion_label in ["POSITIVE", "NEUTRAL"]:
                text = f"在{location}，" + "、".join(scene_chars) + f"终于解开了误会，{random.choice(emotions[emotion_label])}地告别。"
            else:
                text = f"{scene_chars[0]}在{location}{random.choice(emotions[emotion_label])}地离开，留下其他人面面相觑。"
        
        else:
            # 中间场景
            event = random.choice(events)
            if emotion_label == "POSITIVE":
                if len(scene_chars) > 1:
                    text = f"{scene_chars[0]}在{location}里{random.choice(emotions[emotion_label])}地向{scene_chars[1]}{event}。"
                else:
                    text = f"{scene_chars[0]}在{location}里{random.choice(emotions[emotion_label])}地{event}。"
            elif emotion_label == "NEGATIVE":
                if len(scene_chars) > 1:
                    text = f"{scene_chars[0]}在{location}里{random.choice(emotions[emotion_label])}地与{scene_chars[1]}{event}。"
                else:
                    text = f"{scene_chars[0]}在{location}里{random.choice(emotions[emotion_label])}地{event}。"
            elif emotion_label == "SURPRISE":
                text = f"在{location}里，{scene_chars[0]}突然面临意外情况，{random.choice(emotions[emotion_label])}。"
            else:
                text = f"{scene_chars[0]}在{location}里{random.choice(emotions[emotion_label])}地思考着。"
            
            if random.random() > 0.7 and len(scene_chars) > 1:
                text += f"{scene_chars[1]}在一旁{random.choice(emotions[random.choice(list(emotions.keys()))])}地看着这一切。"
        
        # 创建一个有对话的版本
        if random.random() > 0.6:
            if len(scene_chars) > 1:
                dialogue = f'"{random.choice(scene_chars)}对{random.choice([c for c in scene_chars if c != scene_chars[0]])}说：'
                if emotion_label == "POSITIVE":
                    dialogue += f'我真的很{random.choice(emotions["POSITIVE"])}，谢谢你。"'
                elif emotion_label == "NEGATIVE":
                    dialogue += f'我感到非常{random.choice(emotions["NEGATIVE"])}，你怎么能这样？"'
                elif emotion_label == "SURPRISE":
                    dialogue += f'天啊，这真是太{random.choice(emotions["SURPRISE"])}了！"'
                else:
                    dialogue += f'我们需要好好{random.choice(emotions["NEUTRAL"])}一下这件事。"'
                
                # 有50%概率添加对话到文本
                if random.random() > 0.5:
                    text += " " + dialogue
        
        # 添加场景
        start, end = timestamps[i]
        scene = {
            "id": f"scene_{i+1}",
            "start": start,
            "end": end,
            "text": text,
            "characters": scene_chars,
            "location": location,
            "emotion": {
                "type": emotion_label.lower(),
                "description": emotion_desc,
                "score": intensity
            }
        }
        
        script.append(scene)
    
    return script 