#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
情感分析器备用模块

当spaCy和主要情感分析模块不可用时，提供基础的情感分析功能。
"""

import re
from typing import Dict, Any, List, Tuple, Optional

# 积极词汇和消极词汇
POSITIVE_WORDS = {
    "喜欢", "爱", "好", "棒", "赞", "优秀", "精彩", "美", "漂亮", "享受",
    "开心", "快乐", "高兴", "欢乐", "愉快", "满意", "称赞", "成功", "感动",
    "精彩", "舒适", "幸福", "温暖", "惊喜", "完美", "期待", "笑", "希望",
    "interesting", "good", "great", "excellent", "amazing", "wonderful",
    "happy", "love", "enjoy", "beautiful", "best", "perfect", "nice"
}

NEGATIVE_WORDS = {
    "不", "坏", "差", "糟", "烂", "讨厌", "恨", "失望", "悲伤", "痛苦",
    "难过", "伤心", "恐惧", "担心", "焦虑", "后悔", "遗憾", "无聊", "厌倦",
    "不满", "生气", "愤怒", "沮丧", "抱怨", "批评", "反对", "困难", "恶心",
    "bad", "terrible", "awful", "horrible", "poor", "disappointing", "hate",
    "dislike", "boring", "sad", "unfortunately", "worst", "annoying", "wrong"
}

def analyze_text_sentiment(text: str) -> Dict[str, Any]:
    """
    分析文本情感
    
    使用简单的词汇匹配方法计算情感分数
    
    Args:
        text: 输入文本
        
    Returns:
        Dict[str, Any]: 包含情感分析结果的字典
    """
    if not text:
        return {
            "sentiment": "neutral",
            "score": 0.0,
            "confidence": 0.5,
            "details": {
                "positive_score": 0.0,
                "negative_score": 0.0
            }
        }
    
    # 简单的分词（按空格和标点拆分）
    words = re.findall(r'\w+', text.lower())
    
    # 统计积极和消极词汇
    positive_count = sum(1 for word in words if word in POSITIVE_WORDS)
    negative_count = sum(1 for word in words if word in NEGATIVE_WORDS)
    
    # 计算情感分数
    total_count = positive_count + negative_count or 1  # 避免除零
    positive_score = positive_count / len(words) if words else 0
    negative_score = negative_count / len(words) if words else 0
    
    # 最终情感分数(-1到1之间)
    sentiment_score = (positive_score - negative_score) * 2
    
    # 置信度（根据匹配词占比计算）
    confidence = min(0.5 + (total_count / len(words)) * 0.5 if words else 0.5, 0.9)
    
    # 情感标签
    if sentiment_score > 0.1:
        sentiment = "positive"
    elif sentiment_score < -0.1:
        sentiment = "negative"
    else:
        sentiment = "neutral"
    
    return {
        "sentiment": sentiment,
        "score": sentiment_score,
        "confidence": confidence,
        "details": {
            "positive_score": positive_score,
            "negative_score": negative_score,
            "positive_count": positive_count,
            "negative_count": negative_count,
            "word_count": len(words)
        }
    }

# 别名 - 为了保持API兼容性
analyze_sentiment = analyze_text_sentiment

class SimpleSentimentAnalyzer:
    """简单情感分析器类
    
    基于词典的情感分析器，用于在主情感分析器不可用时提供基础功能
    """
    
    def __init__(self):
        """初始化情感分析器"""
        self.positive_words = POSITIVE_WORDS
        self.negative_words = NEGATIVE_WORDS
        self._ready = True
    
    def analyze(self, text: str) -> Dict[str, Any]:
        """分析文本情感
        
        Args:
            text: 输入文本
            
        Returns:
            Dict[str, Any]: 情感分析结果
        """
        return analyze_text_sentiment(text)
    
    def batch_analyze(self, texts: List[str]) -> List[Dict[str, Any]]:
        """批量分析文本情感
        
        Args:
            texts: 输入文本列表
            
        Returns:
            List[Dict[str, Any]]: 情感分析结果列表
        """
        return [self.analyze(text) for text in texts]
    
    def analyze_with_highlights(self, text: str) -> Tuple[Dict[str, Any], List[Tuple[str, str]]]:
        """分析文本情感并提供情感关键词高亮
        
        Args:
            text: 输入文本
            
        Returns:
            Tuple[Dict[str, Any], List[Tuple[str, str]]]: 情感分析结果和高亮词汇列表
        """
        result = self.analyze(text)
        
        # 查找情感词汇
        highlights = []
        words = re.findall(r'\w+', text.lower())
        
        for word in words:
            if word in self.positive_words:
                highlights.append((word, "positive"))
            elif word in self.negative_words:
                highlights.append((word, "negative"))
        
        return result, highlights
    
    def is_ready(self) -> bool:
        """检查分析器是否就绪
        
        Returns:
            bool: 是否就绪
        """
        return self._ready
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息
        
        Returns:
            Dict[str, Any]: 模型信息
        """
        return {
            "name": "SimpleSentimentAnalyzer",
            "type": "dictionary-based",
            "languages": ["zh", "en"],
            "version": "1.0.0",
            "fallback": True
        } 