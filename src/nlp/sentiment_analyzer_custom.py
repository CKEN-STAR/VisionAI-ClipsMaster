#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自定义情感分析器 - 增强版

提供更深入和准确的情感分析功能，支持多维度情感评估。
"""

import logging
import numpy as np
from typing import Dict, List, Any, Union, Optional, Tuple

logger = logging.getLogger(__name__)

# 扩展的情感标签集
EMOTION_LABELS = {
    "VERY_POSITIVE": {"score": 0.9, "intensity": 0.9, "description": "非常积极"},
    "POSITIVE": {"score": 0.7, "intensity": 0.6, "description": "积极"},
    "SLIGHTLY_POSITIVE": {"score": 0.55, "intensity": 0.4, "description": "略微积极"},
    "NEUTRAL": {"score": 0.5, "intensity": 0.2, "description": "中性"},
    "SLIGHTLY_NEGATIVE": {"score": 0.45, "intensity": 0.4, "description": "略微消极"},
    "NEGATIVE": {"score": 0.3, "intensity": 0.6, "description": "消极"},
    "VERY_NEGATIVE": {"score": 0.1, "intensity": 0.8, "description": "非常消极"},
    "SURPRISED": {"score": 0.6, "intensity": 0.7, "description": "惊讶"},
    "ANGRY": {"score": 0.2, "intensity": 0.8, "description": "愤怒"},
    "FEARFUL": {"score": 0.3, "intensity": 0.7, "description": "恐惧"},
    "EXCITED": {"score": 0.8, "intensity": 0.8, "description": "兴奋"},
    "FUNNY": {"score": 0.7, "intensity": 0.6, "description": "幽默"},
    "DRAMATIC": {"score": 0.5, "intensity": 0.8, "description": "戏剧性"},
    "SUSPENSEFUL": {"score": 0.4, "intensity": 0.7, "description": "悬疑"}
}

# 情感词典 - 简化示例，实际应用中应使用更大的词典
EMOTION_KEYWORDS = {
    "VERY_POSITIVE": ["非常好", "太棒了", "完美", "卓越", "精彩绝伦", "震撼", "完美无缺"],
    "POSITIVE": ["好", "不错", "满意", "开心", "高兴", "快乐", "喜欢"],
    "SLIGHTLY_POSITIVE": ["还行", "可以", "不坏", "尚可", "还不错"],
    "NEUTRAL": ["一般", "普通", "平常", "正常", "还好"],
    "SLIGHTLY_NEGATIVE": ["不太好", "有点差", "不太满意", "有待改进"],
    "NEGATIVE": ["差", "糟糕", "不好", "不满意", "失望", "不快"],
    "VERY_NEGATIVE": ["非常差", "极差", "糟透了", "可怕", "灾难", "令人失望"],
    "SURPRISED": ["惊讶", "震惊", "意外", "没想到", "吃惊"],
    "ANGRY": ["生气", "愤怒", "恼火", "激怒", "气愤"],
    "FEARFUL": ["害怕", "恐惧", "担心", "忧虑", "紧张"],
    "EXCITED": ["兴奋", "激动", "热情", "热血", "激情"],
    "FUNNY": ["搞笑", "有趣", "幽默", "逗乐", "欢笑"],
    "DRAMATIC": ["戏剧性", "夸张", "激烈", "强烈", "戏剧化"],
    "SUSPENSEFUL": ["悬疑", "紧张", "扣人心弦", "悬念", "期待"]
}

class EnhancedSentimentAnalyzer:
    """增强型情感分析器"""
    
    def __init__(self):
        """初始化增强型情感分析器"""
        self.model = None
        self.tokenizer = None
        self.is_loaded = False
        self.use_advanced_model = True
        logger.info("初始化增强型情感分析器")
        
    def load(self):
        """加载情感分析模型"""
        try:
            if self.use_advanced_model:
                from transformers import pipeline
                # 使用情感分析pipeline
                self.model = pipeline('sentiment-analysis')
                self.is_loaded = True
                logger.info("已加载Transformers情感分析模型")
            else:
                logger.info("使用本地规则情感分析器")
                self.is_loaded = True
            return True
        except Exception as e:
            logger.error(f"加载情感分析模型失败: {str(e)}")
            # 降级到使用本地规则
            self.use_advanced_model = False
            self.is_loaded = True
            logger.info("降级使用本地规则情感分析器")
            return True
    
    def analyze_text(self, text: str, lang: str = "auto") -> Dict[str, Any]:
        """
        分析文本情感 - 增强版
        
        参数:
            text: 要分析的文本
            lang: 语言代码或"auto"自动检测
            
        返回:
            情感分析结果字典
        """
        if not self.is_loaded:
            self.load()
        
        # 使用高级模型
        if self.use_advanced_model and self.model:
            try:
                # 使用transformers模型
                result = self.model(text)
                label = result[0]['label']
                score = result[0]['score']
                
                # 将transformers的结果映射到我们的情感标签
                if label.lower() == 'positive':
                    if score > 0.9:
                        mapped_label = "VERY_POSITIVE"
                    elif score > 0.7:
                        mapped_label = "POSITIVE"
                    else:
                        mapped_label = "SLIGHTLY_POSITIVE"
                elif label.lower() == 'negative':
                    if score > 0.9:
                        mapped_label = "VERY_NEGATIVE"
                    elif score > 0.7:
                        mapped_label = "NEGATIVE"
                    else:
                        mapped_label = "SLIGHTLY_NEGATIVE"
                else:
                    mapped_label = "NEUTRAL"
                
                # 增加多维度情感分析
                dimensions = self._analyze_emotional_dimensions(text)
                
                return {
                    "label": mapped_label,
                    "score": score,
                    "intensity": EMOTION_LABELS[mapped_label]["intensity"],
                    "description": EMOTION_LABELS[mapped_label]["description"],
                    "dimensions": dimensions
                }
            except Exception as e:
                logger.error(f"高级情感分析失败: {str(e)}")
                # 降级到本地规则
                return self._rule_based_analysis(text, lang)
        else:
            # 使用基于规则的分析
            return self._rule_based_analysis(text, lang)
    
    def _rule_based_analysis(self, text: str, lang: str = "auto") -> Dict[str, Any]:
        """基于规则的情感分析"""
        # 初始情感为中性
        emotion_scores = {"NEUTRAL": 1.0}
        
        # 分析文本中的情感关键词
        for emotion, keywords in EMOTION_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text:
                    if emotion in emotion_scores:
                        emotion_scores[emotion] += 1
                    else:
                        emotion_scores[emotion] = 1
        
        # 找出得分最高的情感
        max_emotion = max(emotion_scores.items(), key=lambda x: x[1])[0]
        
        # 获取情感信息
        emotion_info = EMOTION_LABELS.get(max_emotion, EMOTION_LABELS["NEUTRAL"])
        
        # 增加多维度情感分析
        dimensions = self._analyze_emotional_dimensions(text)
        
        return {
            "label": max_emotion,
            "score": emotion_info["score"],
            "intensity": emotion_info["intensity"],
            "description": emotion_info["description"],
            "dimensions": dimensions
        }
    
    def _analyze_emotional_dimensions(self, text: str) -> Dict[str, float]:
        """分析文本的多个情感维度"""
        dimensions = {
            "drama": 0.0,    # 戏剧性
            "humor": 0.0,    # 幽默感
            "tension": 0.0,  # 紧张感
            "warmth": 0.0,   # 温暖感
            "urgency": 0.0,  # 紧迫感
            "surprise": 0.0  # 惊奇感
        }
        
        # 检测戏剧性
        drama_keywords = ["震撼", "戏剧", "惊人", "难以置信", "史诗", "传奇"]
        for keyword in drama_keywords:
            if keyword in text:
                dimensions["drama"] += 0.2
        
        # 检测幽默感
        humor_keywords = ["笑", "幽默", "搞笑", "逗", "有趣"]
        for keyword in humor_keywords:
            if keyword in text:
                dimensions["humor"] += 0.2
        
        # 检测紧张感
        tension_keywords = ["紧张", "危险", "恐怖", "担忧", "害怕"]
        for keyword in tension_keywords:
            if keyword in text:
                dimensions["tension"] += 0.2
        
        # 检测温暖感
        warmth_keywords = ["温暖", "温馨", "感人", "感动", "幸福", "甜蜜"]
        for keyword in warmth_keywords:
            if keyword in text:
                dimensions["warmth"] += 0.2
        
        # 检测紧迫感
        urgency_keywords = ["紧急", "立即", "马上", "急", "快"]
        for keyword in urgency_keywords:
            if keyword in text:
                dimensions["urgency"] += 0.2
        
        # 检测惊奇感
        surprise_keywords = ["惊讶", "惊喜", "意外", "没想到", "竟然"]
        for keyword in surprise_keywords:
            if keyword in text:
                dimensions["surprise"] += 0.2
        
        # 限制最大值为1.0
        for key in dimensions:
            dimensions[key] = min(dimensions[key], 1.0)
        
        return dimensions

# 导出函数接口
def analyze_text_sentiment(text: str, lang: str = "auto") -> Dict[str, Any]:
    """分析文本情感的便捷函数"""
    analyzer = EnhancedSentimentAnalyzer()
    return analyzer.analyze_text(text, lang)

def analyze_sentiment(text: str, lang: str = "auto") -> Dict[str, Any]:
    """分析情感的便捷函数（保持API兼容）"""
    return analyze_text_sentiment(text, lang)

def analyze_batch(texts: List[str], lang: str = "auto") -> List[Dict[str, Any]]:
    """批量分析文本情感"""
    analyzer = EnhancedSentimentAnalyzer()
    return [analyzer.analyze_text(text, lang) for text in texts]

# 测试代码
if __name__ == "__main__":
    analyzer = EnhancedSentimentAnalyzer()
    
    test_texts = [
        "这个产品非常好用，我很喜欢！",
        "服务态度一般，但是价格还算公道。",
        "真是太差劲了，浪费了我的时间和金钱。",
        "哈哈哈，这也太搞笑了吧！",
        "太恐怖了，我被吓到了！",
        "这个悬疑故事真的很扣人心弦！"
    ]
    
    for text in test_texts:
        result = analyzer.analyze_text(text)
        print(f"文本: {text}")
        print(f"情感: {result['label']} ({result['description']})")
        print(f"分数: {result['score']:.2f}, 强度: {result['intensity']:.2f}")
        print(f"维度: {result['dimensions']}")
        print("-" * 50) 