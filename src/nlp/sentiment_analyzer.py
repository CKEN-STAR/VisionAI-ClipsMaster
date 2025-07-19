#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
情感分析模块

提供文本情感分析功能，支持多语言文本的情感极性和强度识别。
用于评估剧本场景的情感基调，辅助生成引人入胜的混剪。
"""

import re
import os
import logging
import random
from typing import Dict, List, Any, Optional, Union

# 创建日志记录器
logger = logging.getLogger(__name__)

# 情感词典路径
LEXICON_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                          "configs", "sentiment_lexicon.json")

# 情感标签
SENTIMENT_LABELS = ["POSITIVE", "NEGATIVE", "NEUTRAL", "SURPRISE"]

# 简单情感词典（备用）
SIMPLE_LEXICON = {
    "positive": [
        "开心", "高兴", "快乐", "兴奋", "愉悦", "幸福", "满意", "喜悦", "欣喜", "欢乐",
        "感动", "感激", "谢谢", "谢意", "称赞", "赞美", "欣赏", "喜欢", "爱", "爱慕",
        "微笑", "笑", "笑容", "拥抱", "亲吻", "亲切", "温暖", "温馨", "甜蜜", "好"
    ],
    "negative": [
        "难过", "伤心", "悲伤", "痛苦", "悲痛", "忧伤", "哀伤", "沮丧", "失落", "绝望",
        "烦恼", "苦恼", "烦躁", "焦虑", "担忧", "忧虑", "恐惧", "害怕", "惊恐", "恐慌",
        "愤怒", "生气", "愤怒", "暴怒", "恼火", "怨恨", "憎恨", "厌恶", "憎恶", "讨厌",
        "哭", "哭泣", "流泪", "抱怨", "指责", "批评", "谴责", "责备", "埋怨", "坏"
    ],
    "surprise": [
        "惊讶", "吃惊", "震惊", "诧异", "意外", "不可思议", "难以置信", "出乎意料", "没想到", "万万没想到",
        "目瞪口呆", "目瞪口呆", "瞠目结舌", "大吃一惊", "大为惊讶", "哇", "啊", "啊", "哦", "咦"
    ]
}

class SentimentAnalyzer:
    """情感分析器，用于分析文本情感"""
    
    def __init__(self, use_simple: bool = False):
        """
        初始化情感分析器
        
        Args:
            use_simple: 是否使用简单模式（无需外部模型）
        """
        self.use_simple = use_simple
        
        # 加载词典
        self.lexicon = SIMPLE_LEXICON
        
        logger.info("初始化情感分析器")
    
    def analyze(self, text: str) -> Dict[str, Any]:
        """
        分析文本情感
        
        Args:
            text: 待分析文本
            
        Returns:
            情感分析结果，包含情感标签和强度
        """
        if not text:
            return {"label": "NEUTRAL", "intensity": 0.5}
        
        # 使用简单分析
        return self._simple_analyze(text)
    
    def _simple_analyze(self, text: str) -> Dict[str, Any]:
        """使用词典进行简单情感分析"""
        # 计算各情感词出现次数
        positive_count = 0
        negative_count = 0
        surprise_count = 0
        
        for word in self.lexicon["positive"]:
            positive_count += len(re.findall(word, text))
        
        for word in self.lexicon["negative"]:
            negative_count += len(re.findall(word, text))
            
        for word in self.lexicon["surprise"]:
            surprise_count += len(re.findall(word, text))
        
        # 词数总计
        total_count = positive_count + negative_count + surprise_count
        
        # 确定情感标签
        if total_count == 0:
            return {"label": "NEUTRAL", "intensity": 0.5}
            
        if surprise_count > max(positive_count, negative_count):
            label = "SURPRISE"
            intensity = min(0.9, 0.5 + (surprise_count / len(text) * 10))
        elif positive_count > negative_count:
            label = "POSITIVE"
            intensity = min(0.9, 0.5 + (positive_count / len(text) * 10))
        elif negative_count > positive_count:
            label = "NEGATIVE"
            intensity = min(0.9, 0.5 + (negative_count / len(text) * 10))
        else:
            label = "NEUTRAL"
            intensity = 0.5
        
        return {
            "label": label,
            "intensity": intensity,
            "details": {
                "positive": positive_count,
                "negative": negative_count,
                "surprise": surprise_count
            }
        }


# 创建全局分析器实例
_analyzer = None

def get_analyzer() -> SentimentAnalyzer:
    """获取或创建情感分析器实例"""
    global _analyzer
    if _analyzer is None:
        _analyzer = SentimentAnalyzer()
    return _analyzer

def analyze_sentiment(text: str) -> Dict[str, Any]:
    """
    分析文本情感，返回基本情感分析结果
    
    Args:
        text: 待分析文本
        
    Returns:
        情感分析结果字典，包含情感类型和强度
    """
    try:
        # 尝试使用情感分析器
        analyzer = SentimentAnalyzer()
        result = analyzer.analyze(text)
        return result
    except Exception as e:
        logging.warning(f"情感分析出错: {e}")
        # 返回默认中性情感
        return {
            "sentiment": "NEUTRAL",
            "intensity": 0.5,
            "confidence": 0.6
        }

def analyze_text(text: str) -> Dict[str, Any]:
    """
    分析文本情感，并提供更详细的情感特征
    
    Args:
        text: 待分析文本
        
    Returns:
        详细的情感分析结果
    """
    # 获取基础情感分析
    base_result = analyze_sentiment(text)
    
    # 初始化详细结果
    detailed_result = {
        "sentiment": base_result.get("sentiment", "NEUTRAL"),
        "intensity": base_result.get("intensity", 0.5),
        "confidence": base_result.get("confidence", 0.6),
        "features": {}
    }
    
    # 分析情感特征
    # 1. 文本长度
    detailed_result["features"]["text_length"] = len(text)
    
    # 2. 感叹号和问号数量 - 表示情感强度
    exclamation_count = text.count('!') + text.count('！')
    question_count = text.count('?') + text.count('？')
    detailed_result["features"]["exclamation_count"] = exclamation_count
    detailed_result["features"]["question_count"] = question_count
    
    # 3. 重复标点 - 表示强调
    import re
    emphasis_patterns = [r'[!！]{2,}', r'[?？]{2,}', r'[.。]{3,}']
    emphasis_count = sum(len(re.findall(pattern, text)) for pattern in emphasis_patterns)
    detailed_result["features"]["emphasis_count"] = emphasis_count
    
    # 4. 大写字母比例 - 英文文本的强调
    if re.search(r'[A-Za-z]', text):
        caps_count = sum(1 for c in text if c.isupper())
        alpha_count = sum(1 for c in text if c.isalpha())
        caps_ratio = caps_count / alpha_count if alpha_count > 0 else 0
        detailed_result["features"]["caps_ratio"] = caps_ratio
    
    # 5. 情感词汇 - 常见情感词的出现
    sentiment_words = {
        "positive": ["happy", "glad", "joy", "love", "wonderful", "excellent", "great", "good", 
                    "喜欢", "高兴", "快乐", "欣喜", "满意", "美好", "优秀", "棒", "真好"],
        "negative": ["sad", "angry", "hate", "terrible", "awful", "bad", "worst", "poor",
                    "难过", "生气", "讨厌", "糟糕", "可怕", "不好", "差劲", "失望"],
        "surprise": ["wow", "amazing", "incredible", "unbelievable", "shocked", "surprise",
                    "哇", "惊人", "难以置信", "不可思议", "震惊", "惊讶"]
    }
    
    word_counts = {}
    for category, words in sentiment_words.items():
        count = sum(1 for word in words if word.lower() in text.lower())
        word_counts[category] = count
    
    detailed_result["features"]["sentiment_words"] = word_counts
    
    # 6. 情感倾向强度调整
    # 基于情感词和标点符号调整情感强度
    intensity_adjustment = 0
    intensity_adjustment += min(0.2, exclamation_count * 0.05)
    intensity_adjustment += min(0.1, emphasis_count * 0.1)
    intensity_adjustment += min(0.2, word_counts.get("positive", 0) * 0.05)
    intensity_adjustment += min(0.2, word_counts.get("negative", 0) * 0.05)
    
    # 负向情感的标记（根据原始情感类型）
    if base_result.get("sentiment", "NEUTRAL") == "NEGATIVE":
        intensity_adjustment = -intensity_adjustment
    
    # 调整情感强度，但保持在[0.1, 0.9]范围内
    adjusted_intensity = base_result.get("intensity", 0.5) + intensity_adjustment
    detailed_result["intensity"] = max(0.1, min(0.9, adjusted_intensity))
    
    return detailed_result

def analyze_sentiment_batch(texts: List[str]) -> List[Dict[str, Any]]:
    """
    批量分析情感
    
    Args:
        texts: 文本列表
        
    Returns:
        情感分析结果列表
    """
    analyzer = get_analyzer()
    return [analyzer.analyze(text) for text in texts]


if __name__ == "__main__":
    # 测试情感分析
    logging.basicConfig(level=logging.INFO)
    
    test_texts = [
        "我非常高兴见到你，真是太开心了！",
        "这真是太糟糕了，我非常伤心和难过。",
        "他面无表情地走进了房间。",
        "天啊！没想到竟然是这样的结果，太令人震惊了！"
    ]
    
    results = analyze_sentiment_batch(test_texts)
    
    for i, (text, result) in enumerate(zip(test_texts, results)):
        print(f"\n文本 {i+1}: {text}")
        print(f"情感: {result['label']}, 强度: {result['intensity']:.2f}")
        if 'details' in result:
            print(f"详情: {result['details']}") 