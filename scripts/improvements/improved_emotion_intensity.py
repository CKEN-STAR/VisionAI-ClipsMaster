#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
改进的情感强度分析模块

扩展情感词典，支持更多情感类型和更准确的情感识别
"""

import re
from typing import Dict, List, Tuple, Any

class ImprovedEmotionIntensity:
    """改进的情感强度分析器"""

    def __init__(self):
        # 扩展的情感词典
        self.emotion_keywords = {
            # 基础情感
            "joy": ["开心", "快乐", "高兴", "兴奋", "愉快", "欢喜", "喜悦", "满意", "舒心"],
            "anger": ["愤怒", "生气", "恼火", "暴怒", "气愤", "恼怒", "大胆", "质疑", "竟敢"],
            "sadness": ["悲伤", "难过", "伤心", "痛苦", "忧伤", "沮丧", "失望", "绝望"],
            "fear": ["害怕", "恐惧", "担心", "紧张", "焦虑", "不安", "恐慌", "畏惧", "不敢"],
            "surprise": ["惊讶", "震惊", "意外", "吃惊", "惊奇", "诧异", "突然", "没想到"],
            "disgust": ["厌恶", "恶心", "讨厌", "反感", "憎恨", "嫌弃", "不妥", "不当"],
            
            # 扩展情感类型
            "formal": ["皇上", "臣妾", "禀报", "殿下", "陛下", "奏请", "恭敬", "谨慎"],
            "urgent": ["紧急", "速速", "立即", "马上", "急忙", "赶紧", "迅速", "火急"],
            "worried": ["担心", "忧虑", "不安", "忧心", "顾虑", "操心", "挂念"],
            "serious": ["重大", "严重", "重要", "关键", "严肃", "庄重", "慎重"],
            "submissive": ["听从", "遵命", "服从", "顺从", "依从", "明白", "是的"],
            "authoritative": ["传朕", "旨意", "命令", "决定", "安排", "指示", "要求"],
            "polite": ["请问", "谢谢", "不好意思", "劳烦", "麻烦", "打扰", "客气"],
            "professional": ["公司", "工作", "职业", "业务", "专业", "正式", "规范"],
            "nervous": ["紧张", "忐忑", "不安", "焦虑", "担忧", "心慌", "紧张"],
            "grateful": ["谢谢", "感谢", "感激", "多谢", "谢您", "感恩", "致谢"],
            "encouraging": ["加油", "努力", "坚持", "相信", "支持", "鼓励", "祝福"],
            "reassuring": ["放心", "别担心", "没关系", "不要紧", "安心", "放宽心"],
            "relieved": ["放心", "安心", "松了口气", "轻松", "舒缓", "缓解"],
            "secretive": ["秘密", "保密", "隐瞒", "不可", "绝不", "私下", "暗中"],
            "obedient": ["遵从", "听话", "服从", "照办", "按照", "依照", "执行"],
            "helpful": ["帮助", "协助", "支持", "配合", "合作", "援助", "相助"]
        }

        # 强度修饰词
        self.intensity_modifiers = {
            "very": ["非常", "极其", "特别", "十分", "相当", "格外", "很", "太", "超级"],
            "somewhat": ["有点", "稍微", "略微", "一点", "些许", "轻微", "稍", "略"]
        }
        
        # 否定词
        self.negation_words = ["不", "没", "无", "非", "未", "别", "勿", "莫"]
        
        # 语境增强词
        self.context_enhancers = {
            "formal": ["皇上", "陛下", "殿下", "臣妾", "奏请", "禀报"],
            "urgent": ["速速", "立即", "马上", "急", "快"],
            "authority": ["朕", "传", "旨意", "命令", "决定"],
            "respect": ["请", "劳烦", "麻烦", "谢谢", "感谢"],
            "workplace": ["公司", "工作", "面试", "职业", "业务"]
        }

    def analyze_emotion_intensity(self, text: str) -> Dict[str, float]:
        """分析文本的情感强度"""
        emotions = {}
        text_lower = text.lower()

        # 检查每种情感
        for emotion, keywords in self.emotion_keywords.items():
            intensity = 0.0
            keyword_matches = 0

            for keyword in keywords:
                if keyword in text:
                    keyword_matches += 1
                    base_intensity = 1.0

                    # 检查强度修饰词
                    for modifier_type, modifiers in self.intensity_modifiers.items():
                        for modifier in modifiers:
                            if modifier in text:
                                if modifier_type == "very":
                                    base_intensity *= 1.5
                                elif modifier_type == "somewhat":
                                    base_intensity *= 0.7

                    # 检查否定词
                    negated = False
                    for neg_word in self.negation_words:
                        if neg_word in text and text.find(neg_word) < text.find(keyword):
                            negated = True
                            break
                    
                    if negated:
                        base_intensity *= 0.3  # 否定降低强度

                    intensity = max(intensity, base_intensity)

            # 语境增强
            context_boost = self._calculate_context_boost(text, emotion)
            intensity += context_boost

            # 多关键词加成
            if keyword_matches > 1:
                intensity *= (1 + 0.2 * (keyword_matches - 1))

            if intensity > 0:
                emotions[emotion] = min(intensity, 2.0)  # 限制最大强度

        # 如果没有检测到任何情感，返回中性情感
        if not emotions:
            emotions["neutral"] = 0.5

        return emotions

    def _calculate_context_boost(self, text: str, emotion: str) -> float:
        """计算语境增强分数"""
        boost = 0.0
        
        # 根据情感类型检查相关语境
        if emotion == "formal":
            for enhancer in self.context_enhancers["formal"]:
                if enhancer in text:
                    boost += 0.3
        elif emotion == "urgent":
            for enhancer in self.context_enhancers["urgent"]:
                if enhancer in text:
                    boost += 0.4
        elif emotion == "authoritative":
            for enhancer in self.context_enhancers["authority"]:
                if enhancer in text:
                    boost += 0.5
        elif emotion in ["polite", "grateful"]:
            for enhancer in self.context_enhancers["respect"]:
                if enhancer in text:
                    boost += 0.3
        elif emotion == "professional":
            for enhancer in self.context_enhancers["workplace"]:
                if enhancer in text:
                    boost += 0.3
        
        return min(boost, 1.0)  # 限制最大增强

    def get_dominant_emotion(self, text: str) -> Tuple[str, float]:
        """获取主导情感"""
        emotions = self.analyze_emotion_intensity(text)
        
        if not emotions:
            return ("neutral", 0.0)
        
        dominant_emotion = max(emotions.items(), key=lambda x: x[1])
        return dominant_emotion

    def get_emotion_profile(self, text: str) -> Dict[str, Any]:
        """获取完整的情感分析档案"""
        emotions = self.analyze_emotion_intensity(text)
        dominant_emotion, dominant_intensity = self.get_dominant_emotion(text)
        
        # 计算情感多样性
        emotion_count = len([e for e in emotions.values() if e > 0.1])
        emotion_diversity = emotion_count / len(self.emotion_keywords)
        
        # 计算总体情感强度
        total_intensity = sum(emotions.values())
        
        return {
            "emotions": emotions,
            "dominant_emotion": dominant_emotion,
            "dominant_intensity": dominant_intensity,
            "emotion_diversity": emotion_diversity,
            "total_intensity": total_intensity,
            "text_length": len(text),
            "emotion_density": total_intensity / max(len(text), 1)
        }

# 全局实例
_emotion_intensity = None

def get_emotion_intensity():
    """获取情感强度分析器实例"""
    global _emotion_intensity
    if _emotion_intensity is None:
        _emotion_intensity = ImprovedEmotionIntensity()
    return _emotion_intensity

# 测试函数
def test_improved_emotion_analysis():
    """测试改进的情感分析"""
    analyzer = ImprovedEmotionIntensity()
    
    test_cases = [
        "皇上，臣妾有重要的事情要禀报。",
        "什么事情如此紧急？速速道来！",
        "你竟敢质疑朕的决定？大胆！",
        "臣妾不敢，只是担心江山社稷啊。",
        "你好，请问这里是星辰公司吗？",
        "我有点紧张。",
        "别紧张，我们公司氛围很好的。",
        "谢谢您，我有点紧张。"
    ]
    
    print("🧪 测试改进的情感分析")
    print("=" * 50)
    
    for i, text in enumerate(test_cases):
        profile = analyzer.get_emotion_profile(text)
        dominant = profile["dominant_emotion"]
        intensity = profile["dominant_intensity"]
        
        print(f"文本{i+1}: '{text}'")
        print(f"  主导情感: {dominant} (强度: {intensity:.2f})")
        print(f"  所有情感: {profile['emotions']}")
        print()

if __name__ == "__main__":
    test_improved_emotion_analysis()
