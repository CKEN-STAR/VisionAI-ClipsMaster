#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
情感强度分析模块 - 分析文本的情感强度
"""

import re
from typing import Dict, List, Tuple

class EmotionIntensity:
    """情感强度分析器"""

    def __init__(self):
        # 情感词典
        self.emotion_keywords = {
            "joy": ["开心", "快乐", "高兴", "兴奋", "愉快", "欢喜"],
            "anger": ["愤怒", "生气", "恼火", "暴怒", "气愤", "恼怒"],
            "sadness": ["悲伤", "难过", "伤心", "痛苦", "忧伤", "沮丧"],
            "fear": ["害怕", "恐惧", "担心", "紧张", "焦虑", "不安"],
            "surprise": ["惊讶", "震惊", "意外", "吃惊", "惊奇", "诧异"],
            "disgust": ["厌恶", "恶心", "讨厌", "反感", "憎恨", "嫌弃"]
        }

        # 强度修饰词
        self.intensity_modifiers = {
            "very": ["非常", "极其", "特别", "十分", "相当", "格外"],
            "somewhat": ["有点", "稍微", "略微", "一点", "些许", "轻微"]
        }

    def analyze_emotion_intensity(self, text: str) -> Dict[str, float]:
        """分析文本的情感强度"""
        emotions = {}

        for emotion, keywords in self.emotion_keywords.items():
            intensity = 0.0

            for keyword in keywords:
                if keyword in text:
                    base_intensity = 1.0

                    # 检查强度修饰词
                    for modifier_type, modifiers in self.intensity_modifiers.items():
                        for modifier in modifiers:
                            if modifier in text and keyword in text:
                                if modifier_type == "very":
                                    base_intensity *= 1.5
                                elif modifier_type == "somewhat":
                                    base_intensity *= 0.7

                    intensity = max(intensity, base_intensity)

            emotions[emotion] = min(intensity, 2.0)  # 限制最大强度

        return emotions

    def get_dominant_emotion(self, text: str) -> Tuple[str, float]:
        """获取主导情感"""
        emotions = self.analyze_emotion_intensity(text)

        if not emotions:
            return "neutral", 0.0

        dominant_emotion = max(emotions.items(), key=lambda x: x[1])
        return dominant_emotion

    def calculate_emotional_curve(self, texts: List[str]) -> List[Dict[str, float]]:
        """计算情感曲线"""
        curve = []

        for text in texts:
            emotions = self.analyze_emotion_intensity(text)
            curve.append(emotions)

        return curve

# 全局实例
emotion_intensity = EmotionIntensity()

def get_emotion_intensity():
    """获取情感强度分析器实例"""
    return emotion_intensity
