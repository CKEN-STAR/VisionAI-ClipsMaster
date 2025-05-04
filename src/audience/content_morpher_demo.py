#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
内容变形器独立演示脚本

这是一个独立的演示脚本，展示内容变形器的核心功能，
不依赖于其他模块，方便快速测试和演示。
"""

import os
import copy
import json
import random
from typing import Dict, List, Any
from datetime import datetime

# 简单的日志函数
def log(message):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

class ContentMorpher:
    """内容变形器简化版"""
    
    def __init__(self):
        """初始化内容变形器"""
        log("内容变形器初始化")
    
    def morph_content(self, content, strategy_weights):
        """根据策略权重变形内容"""
        log(f"应用变形策略: {strategy_weights}")
        
        # 创建内容副本
        result = copy.deepcopy(content)
        
        # 应用情感增强策略
        if "情感增强" in strategy_weights and strategy_weights["情感增强"] > 0.5:
            factor = 1.0 + strategy_weights["情感增强"] * 0.5  # 0.5 ~ 1.5
            result = self._amplify_emotions(result, factor)
            log(f"应用情感增强变形，因子: {factor:.2f}")
        
        # 应用节奏调整策略
        if "节奏调整" in strategy_weights and strategy_weights["节奏调整"] > 0.5:
            if "快节奏" in strategy_weights and strategy_weights["快节奏"] > 0.6:
                target_bpm = 150
                log("应用快节奏调整")
            elif "慢节奏" in strategy_weights and strategy_weights["慢节奏"] > 0.6:
                target_bpm = 80
                log("应用慢节奏调整")
            else:
                target_bpm = 120
                log("应用中等节奏调整")
            
            result = self._adjust_pacing(result, target_bpm)
        
        # 应用文化本地化策略
        if "文化本地化" in strategy_weights and strategy_weights["文化本地化"] > 0.5:
            source_lang = "zh"
            target_lang = "en"
            
            if "中国化" in strategy_weights and strategy_weights["中国化"] > 0.6:
                source_lang, target_lang = "en", "zh"
                log("应用中国化变形")
            else:
                log("应用西方化变形")
            
            result = self._localize_cultural_references(result, source_lang, target_lang)
        
        return result
    
    def _amplify_emotions(self, content, factor=1.5):
        """增强内容的情感强度"""
        result = copy.deepcopy(content)
        
        # 处理情感数据
        if "emotions" in result and isinstance(result["emotions"], list):
            for emotion in result["emotions"]:
                if isinstance(emotion, dict):
                    # 增强情感强度
                    if "intensity" in emotion:
                        emotion["intensity"] = min(1.0, emotion["intensity"] * factor)
                    
                    # 增强情感分数
                    if "score" in emotion:
                        emotion["score"] = min(1.0, emotion["score"] * factor)
        
        # 处理场景数据
        if "scenes" in result and isinstance(result["scenes"], list):
            for scene in result["scenes"]:
                if isinstance(scene, dict) and "emotion" in scene:
                    # 增强场景情感强度
                    if isinstance(scene["emotion"], dict):
                        if "intensity" in scene["emotion"]:
                            scene["emotion"]["intensity"] = min(1.0, scene["emotion"]["intensity"] * factor)
                        
                        if "score" in scene["emotion"]:
                            scene["emotion"]["score"] = min(1.0, scene["emotion"]["score"] * factor)
        
        return result
    
    def _adjust_pacing(self, content, target_bpm=120):
        """调整内容的节奏"""
        result = copy.deepcopy(content)
        
        # 处理场景数据
        if "scenes" in result and isinstance(result["scenes"], list):
            # 计算当前的平均BPM (简化版)
            current_bpm = 100  # 假设的值
            if len(result["scenes"]) > 0:
                total_duration = sum(scene.get("duration", 0) for scene in result["scenes"])
                scene_count = len(result["scenes"])
                if total_duration > 0:
                    current_bpm = (scene_count / total_duration) * 60
            
            # 计算调整因子
            adjustment_factor = target_bpm / max(1, current_bpm)
            
            # 调整场景持续时间
            for scene in result["scenes"]:
                if isinstance(scene, dict) and "duration" in scene:
                    # 应用节奏调整
                    scene["adjusted_duration"] = scene["duration"] / adjustment_factor
                    scene["pacing_adjustment"] = {
                        "original_duration": scene["duration"],
                        "target_bpm": target_bpm,
                        "current_bpm": current_bpm,
                        "adjustment_factor": adjustment_factor
                    }
        
        return result
    
    def _localize_cultural_references(self, content, source_lang="zh", target_lang="en"):
        """本地化文化引用"""
        result = copy.deepcopy(content)
        
        # 文化引用映射
        cultural_references = {
            "zh_to_en": {
                "春节": "Chinese New Year",
                "中秋节": "Mid-Autumn Festival",
                "红包": "red envelope",
                "年夜饭": "reunion dinner",
                "春联": "Spring Festival couplets"
            },
            "en_to_zh": {
                "Christmas": "圣诞节",
                "Thanksgiving": "感恩节",
                "Halloween": "万圣节",
                "turkey dinner": "火鸡大餐",
                "Christmas tree": "圣诞树"
            }
        }
        
        direction = f"{source_lang}_to_{target_lang}"
        references = cultural_references.get(direction, {})
        
        # 处理对话数据
        if "dialogues" in result and isinstance(result["dialogues"], list):
            for dialogue in result["dialogues"]:
                if isinstance(dialogue, dict) and "text" in dialogue:
                    # 本地化文化引用
                    text = dialogue["text"]
                    for original, localized in references.items():
                        text = text.replace(original, localized)
                    dialogue["text"] = text
        
        # 处理叙述数据
        if "narration" in result and isinstance(result["narration"], list):
            for narration in result["narration"]:
                if isinstance(narration, dict) and "text" in narration:
                    # 本地化文化引用
                    text = narration["text"]
                    for original, localized in references.items():
                        text = text.replace(original, localized)
                    narration["text"] = text
        
        # 处理标题和描述
        if "title" in result and isinstance(result["title"], str):
            text = result["title"]
            for original, localized in references.items():
                text = text.replace(original, localized)
            result["title"] = text
        
        if "description" in result and isinstance(result["description"], str):
            text = result["description"]
            for original, localized in references.items():
                text = text.replace(original, localized)
            result["description"] = text
        
        return result


def generate_mock_content(content_type="剧情片段"):
    """生成模拟内容数据"""
    content_id = f"content_{random.randint(10000, 99999)}"
    
    # 根据内容类型调整生成参数
    if "爱情" in content_type or "情感" in content_type:
        primary_emotions = ["喜悦", "悲伤"]
        primary_themes = ["爱情", "成长", "亲情"]
    elif "悬疑" in content_type or "推理" in content_type:
        primary_emotions = ["紧张", "惊讶", "恐惧"]
        primary_themes = ["悬疑", "复仇", "智斗"]
    elif "动作" in content_type or "冒险" in content_type:
        primary_emotions = ["紧张", "惊讶", "喜悦"]
        primary_themes = ["冒险", "智斗", "生存"]
    else:
        primary_emotions = ["喜悦", "悲伤", "愤怒", "恐惧", "厌恶", "惊讶", "中性"]
        primary_themes = ["成长", "爱情", "友情", "亲情", "复仇", "救赎", "冒险", "生存"]
    
    # 生成标题和描述
    title = f"《{random.choice(['星辰', '流光', '追梦', '逐风', '暗夜', '晨曦'])}{random.choice(['之旅', '传说', '故事', '探险', '秘闻'])}》"
    description = f"一段关于{random.choice(primary_themes)}的{content_type}，{random.choice(['令人深思', '扣人心弦', '感人至深', '引人入胜'])}"
    
    # 生成场景数据
    scene_count = random.randint(3, 7)
    scenes = []
    current_time = 0.0
    
    for i in range(scene_count):
        # 场景持续时间，3-15秒
        scene_duration = random.uniform(3.0, 15.0)
        scene_duration = round(scene_duration, 1)
        
        # 场景情感
        emotion_type = random.choice(primary_emotions)
        emotion_intensity = random.uniform(0.3, 0.8)
        emotion_intensity = round(emotion_intensity, 2)
        emotion_score = random.uniform(emotion_intensity - 0.1, emotion_intensity + 0.2)
        emotion_score = round(min(1.0, emotion_score), 2)
        
        scene = {
            "id": f"scene_{i+1}",
            "start": current_time,
            "end": current_time + scene_duration,
            "duration": scene_duration,
            "emotion": {
                "type": emotion_type,
                "intensity": emotion_intensity,
                "score": emotion_score
            }
        }
        
        scenes.append(scene)
        current_time += scene_duration
    
    # 生成整体情感数据
    emotions = []
    for emotion_type in random.sample(primary_emotions, min(3, len(primary_emotions))):
        emotion_intensity = random.uniform(0.3, 0.8)
        emotion_intensity = round(emotion_intensity, 2)
        emotion_score = random.uniform(emotion_intensity - 0.1, emotion_intensity + 0.2)
        emotion_score = round(min(1.0, emotion_score), 2)
        
        emotions.append({
            "type": emotion_type,
            "intensity": emotion_intensity,
            "score": emotion_score
        })
    
    # 生成对话数据
    dialogue_samples = [
        "你觉得人生的意义是什么？",
        "有些事情，只能靠自己去面对。",
        "我们已经走了这么远，不能放弃。",
        "无论发生什么，我都会在你身边。",
        "有时候，放手也是一种勇气。",
        "我不后悔认识你，即使结局是这样。",
        "真相往往比我们想象的更复杂。",
        "春节快到了，我们要准备红包。",
        "这次考试真难，我要好好复习。",
        "你看窗外的风景，多美啊。"
    ]
    
    dialogues = []
    for i in range(min(4, scene_count)):
        scene = scenes[i]
        start_time = scene["start"] + random.uniform(0.5, 1.5)
        end_time = min(scene["end"] - 0.5, start_time + 3.0)
        
        dialogues.append({
            "id": f"dialogue_{i+1}",
            "text": random.choice(dialogue_samples),
            "start": round(start_time, 1),
            "end": round(end_time, 1)
        })
    
    # 生成旁白数据
    narration_samples = [
        "时间如同流水，带走了太多回忆。",
        "在这座城市里，每个人都有自己的故事。",
        "命运有时就是这样奇妙，让两个人在最美的时刻相遇。",
        "有些选择，一旦做出，就再也无法回头。",
        "这是一个关于勇气与坚持的故事。",
        "黎明前的黑暗，总是最为漫长。"
    ]
    
    narrations = []
    for i in range(min(2, scene_count)):
        scene = scenes[i]
        start_time = scene["start"] + random.uniform(0.5, 1.0)
        end_time = min(scene["end"] - 0.5, start_time + 3.0)
        
        narrations.append({
            "id": f"narration_{i+1}",
            "text": random.choice(narration_samples),
            "start": round(start_time, 1),
            "end": round(end_time, 1)
        })
    
    # 组装内容数据
    content = {
        "id": content_id,
        "title": title,
        "description": description,
        "type": content_type,
        "duration": scenes[-1]["end"],
        "scenes": scenes,
        "emotions": emotions,
        "dialogues": dialogues,
        "narration": narrations,
        "themes": random.sample(primary_themes, min(3, len(primary_themes))),
        "created_at": datetime.now().isoformat()
    }
    
    return content


def print_divider(title=""):
    """打印分隔线"""
    width = 80
    print("\n" + "=" * width)
    if title:
        title_with_padding = f" {title} "
        padding_size = (width - len(title_with_padding)) // 2
        print("=" * padding_size + title_with_padding + "=" * padding_size)
    print("=" * width + "\n")


def print_content_summary(content, title="内容摘要"):
    """打印内容摘要"""
    print(f"\n--- {title} ---")
    print(f"ID: {content.get('id', 'unknown')}")
    print(f"标题: {content.get('title', 'unknown')}")
    print(f"描述: {content.get('description', 'unknown')}")
    
    # 打印场景信息
    print("\n场景:")
    for i, scene in enumerate(content.get("scenes", [])[:3]):
        print(f"  场景 {i+1}: {scene.get('duration', 0):.1f}秒"
              f" ({scene.get('adjusted_duration', 'N/A'):.1f}秒调整后)" 
              if "adjusted_duration" in scene else
              f"  场景 {i+1}: {scene.get('duration', 0):.1f}秒")
        if "emotion" in scene:
            emo = scene["emotion"]
            print(f"    情感: {emo.get('type', 'unknown')}, "
                  f"强度: {emo.get('intensity', 0):.2f}, "
                  f"分数: {emo.get('score', 0):.2f}")
    
    # 打印情感信息
    if "emotions" in content:
        print("\n整体情感:")
        for emotion in content.get("emotions", [])[:3]:
            print(f"  {emotion.get('type', 'unknown')}: "
                  f"强度: {emotion.get('intensity', 0):.2f}, "
                  f"分数: {emotion.get('score', 0):.2f}")
    
    # 打印对话样本
    if "dialogues" in content:
        print("\n对话样本:")
        for dialogue in content.get("dialogues", [])[:2]:
            print(f"  \"{dialogue.get('text', '')}\"")
    
    print("")


def demonstrate_emotion_amplification():
    """演示情感增强功能"""
    print_divider("情感增强演示")
    
    # 获取示例内容
    print("生成示例内容...")
    content = generate_mock_content("悲情爱情故事")
    
    # 打印原始内容
    print_content_summary(content, "原始内容")
    
    # 初始化变形器
    morpher = ContentMorpher()
    
    # 应用情感增强
    print("应用情感增强变形...")
    amplified = morpher.morph_content(content, {"情感增强": 0.8})
    
    # 打印增强后的内容
    print_content_summary(amplified, "情感增强后的内容")
    
    # 展示效果对比
    print("效果对比 (原始 vs 增强):")
    for i, (orig, ampl) in enumerate(zip(content.get("emotions", []), amplified.get("emotions", []))):
        print(f"情感 {i+1} ({orig.get('type', 'unknown')}): "
              f"强度 {orig.get('intensity', 0):.2f} → {ampl.get('intensity', 0):.2f}, "
              f"分数 {orig.get('score', 0):.2f} → {ampl.get('score', 0):.2f}")


def demonstrate_pacing_adjustment():
    """演示节奏调整功能"""
    print_divider("节奏调整演示")
    
    # 获取示例内容
    print("生成示例内容...")
    content = generate_mock_content("悬疑动作片段")
    
    # 打印原始内容
    print_content_summary(content, "原始内容")
    
    # 初始化变形器
    morpher = ContentMorpher()
    
    # 应用快节奏调整
    print("应用快节奏调整...")
    fast_paced = morpher.morph_content(content, {"节奏调整": 0.9, "快节奏": 0.8})
    
    # 打印调整后的内容
    print_content_summary(fast_paced, "快节奏调整后的内容")
    
    # 应用慢节奏调整
    print("应用慢节奏调整...")
    slow_paced = morpher.morph_content(content, {"节奏调整": 0.9, "慢节奏": 0.8})
    
    # 打印调整后的内容
    print_content_summary(slow_paced, "慢节奏调整后的内容")


def demonstrate_cultural_localization():
    """演示文化本地化功能"""
    print_divider("文化本地化演示")
    
    # 创建包含文化引用的示例内容
    content = {
        "id": "cultural_demo_1",
        "title": "春节的故事",
        "description": "一个关于中国新年的温馨故事",
        "scenes": [
            {
                "id": "scene_1",
                "duration": 10.0,
                "emotion": {"type": "喜悦", "intensity": 0.7}
            }
        ],
        "dialogues": [
            {
                "id": "dialogue_1",
                "text": "春节快到了，我们要准备红包和年夜饭。",
                "start": 2.0,
                "end": 5.0
            },
            {
                "id": "dialogue_2",
                "text": "大家一起贴春联，象征新的一年的到来。",
                "start": 7.0,
                "end": 10.0
            }
        ],
        "narration": [
            {
                "id": "narration_1",
                "text": "在中国传统文化中，春节是最重要的节日。",
                "start": 0.0,
                "end": 3.0
            }
        ]
    }
    
    # 打印原始内容
    print_content_summary(content, "原始内容 (中文文化引用)")
    
    # 初始化变形器
    morpher = ContentMorpher()
    
    # 应用文化本地化 - 中文到英文
    print("应用文化本地化 (中文→英文)...")
    localized_en = morpher.morph_content(content, {"文化本地化": 0.9})
    
    # 打印本地化后的内容
    print_content_summary(localized_en, "本地化后的内容 (英文文化引用)")
    
    # 创建包含西方文化引用的示例内容
    western_content = {
        "id": "cultural_demo_2",
        "title": "Christmas Story",
        "description": "A heartwarming tale of Christmas celebration",
        "scenes": [
            {
                "id": "scene_1",
                "duration": 10.0,
                "emotion": {"type": "joy", "intensity": 0.7}
            }
        ],
        "dialogues": [
            {
                "id": "dialogue_1",
                "text": "Christmas is coming, we need to prepare gifts and turkey dinner.",
                "start": 2.0,
                "end": 5.0
            },
            {
                "id": "dialogue_2",
                "text": "Let's decorate the Christmas tree together.",
                "start": 7.0,
                "end": 10.0
            }
        ],
        "narration": [
            {
                "id": "narration_1",
                "text": "Christmas is the most important holiday in western tradition.",
                "start": 0.0,
                "end": 3.0
            }
        ]
    }
    
    # 打印原始内容
    print_content_summary(western_content, "原始内容 (英文文化引用)")
    
    # 应用文化本地化 - 英文到中文
    print("应用文化本地化 (英文→中文)...")
    localized_zh = morpher.morph_content(western_content, {"文化本地化": 0.9, "中国化": 0.8})
    
    # 打印本地化后的内容
    print_content_summary(localized_zh, "本地化后的内容 (中文文化引用)")


def demonstrate_combined_strategies():
    """演示组合应用多种变形策略"""
    print_divider("组合变形策略演示")
    
    # 获取示例内容
    print("生成示例内容...")
    content = generate_mock_content("剧情片段")
    
    # 打印原始内容
    print_content_summary(content, "原始内容")
    
    # 定义策略权重
    strategy_weights = {
        "情感增强": 0.8,   # 情感增强
        "节奏调整": 0.7,   # 节奏调整
        "快节奏": 0.9,     # 快节奏
        "文化本地化": 0.8   # 文化本地化
    }
    
    print("应用的策略权重:")
    for strategy, weight in strategy_weights.items():
        print(f"- {strategy}: {weight:.2f}")
    
    # 初始化变形器
    morpher = ContentMorpher()
    
    # 应用组合策略
    print("\n组合应用多种变形策略...")
    morphed_content = morpher.morph_content(content, strategy_weights)
    
    # 打印变形后的内容
    print_content_summary(morphed_content, "应用组合策略后的内容")


def main():
    """主函数"""
    print("\n内容变形器演示\n")
    print("这个独立演示展示了内容变形器的核心功能，包括情感增强、节奏调整和文化本地化。")
    
    try:
        # 演示情感增强
        demonstrate_emotion_amplification()
        
        # 演示节奏调整
        demonstrate_pacing_adjustment()
        
        # 演示文化本地化
        demonstrate_cultural_localization()
        
        # 演示组合策略
        demonstrate_combined_strategies()
        
        print("\n演示完成，内容变形器功能展示成功！")
        
    except Exception as e:
        print(f"演示过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 