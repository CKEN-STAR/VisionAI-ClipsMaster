#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
文本分析工具

提供关键词提取、文本相似度计算等基础NLP功能
用于支持叙事分析和文本处理相关任务
"""

import re
import math
import logging
from typing import Dict, List, Any, Optional, Tuple, Set, Union
from collections import Counter

# 创建日志记录器
logger = logging.getLogger("text_analyzer")

# 中文停用词表（常见的没有实际意义的词）
STOPWORDS = {
    "的", "了", "和", "是", "就", "都", "而", "及", "与", "这", "那", "你", "我", "他", "她", "它",
    "们", "个", "之", "去", "来", "说", "着", "为", "吗", "啊", "从", "到", "给", "在", "上", "下",
    "前", "后", "里", "外", "中", "什么", "怎么", "一个", "一种", "一样", "如何", "什么样", "哪些",
    "可以", "不可", "没有", "不是", "但是", "因为", "所以", "如果", "已经", "现在", "当时", "仍然",
    "正在", "将会", "一直", "曾经", "一些", "有些", "这些", "那些", "这样", "那样", "只是", "於是",
    "然後", "然而", "不过", "除了", "只有", "不仅", "还有", "甚至", "反而", "却是", "亦是", "其中", 
    "不过", "这个", "那个", "每个", "哪个", "多少", "一下", "一次", "一边", "一点", "许多", "各种",
    "有点", "无论", "即使", "虽然", "只要", "不要", "当然", "究竟", "难道"
}

def tokenize_chinese(text: str) -> List[str]:
    """
    简单的中文分词处理
    
    Args:
        text: 输入文本
        
    Returns:
        分词结果列表
    """
    # 去除特殊字符和标点
    text = re.sub(r'[^\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff\d]+', ' ', text)
    
    # 简单切分
    # 在实际产品中，这里应该使用专业的分词库如jieba
    # 由于不需要下载额外模型的需求，这里使用简化方法
    
    # 字符级切分
    chars = list(text.strip())
    
    # 合并数字
    tokens = []
    temp_num = ""
    
    for char in chars:
        if char.isdigit():
            temp_num += char
        else:
            if temp_num:
                tokens.append(temp_num)
                temp_num = ""
            if char.strip():
                tokens.append(char)
    
    # 处理末尾数字
    if temp_num:
        tokens.append(temp_num)
    
    # 过滤停用词
    tokens = [t for t in tokens if t not in STOPWORDS and len(t.strip()) > 0]
    
    return tokens

def extract_keywords(text: str, top_k: int = 5) -> List[str]:
    """
    从文本中提取关键词
    
    Args:
        text: 输入文本
        top_k: 返回的关键词数量
        
    Returns:
        关键词列表
    """
    if not text:
        return []
    
    # 分词
    tokens = tokenize_chinese(text)
    
    # 统计词频
    counter = Counter(tokens)
    
    # 取频率最高的几个词作为关键词
    # 在实际产品中，应该使用TF-IDF或TextRank等算法
    keywords = [word for word, _ in counter.most_common(top_k)]
    
    return keywords

def calc_text_similarity(text1: str, text2: str) -> float:
    """
    计算两段文本的相似度（简化版余弦相似度）
    
    Args:
        text1: 第一段文本
        text2: 第二段文本
        
    Returns:
        相似度得分（0-1之间）
    """
    if not text1 or not text2:
        return 0.0
    
    # 分词
    tokens1 = tokenize_chinese(text1)
    tokens2 = tokenize_chinese(text2)
    
    # 创建词袋
    all_tokens = set(tokens1 + tokens2)
    if not all_tokens:
        return 0.0
    
    # 计算词频向量
    vec1 = [tokens1.count(token) for token in all_tokens]
    vec2 = [tokens2.count(token) for token in all_tokens]
    
    # 计算余弦相似度
    dot_product = sum(v1 * v2 for v1, v2 in zip(vec1, vec2))
    magnitude1 = math.sqrt(sum(v * v for v in vec1))
    magnitude2 = math.sqrt(sum(v * v for v in vec2))
    
    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0
    
    similarity = dot_product / (magnitude1 * magnitude2)
    
    return similarity

def extract_entities(text: str) -> Dict[str, List[str]]:
    """
    从文本中提取实体（人物、地点、物品等）
    
    Args:
        text: 输入文本
        
    Returns:
        各类实体列表字典
    """
    # 简单实现，在实际产品中应使用专业NER工具
    entities = {
        "person": [],
        "location": [],
        "object": []
    }
    
    # 人名识别（简化）- 查找带有"小"、"老"等前缀的常见人名格式
    person_patterns = [
        r'小[\u4e00-\u9fff]{1,2}',  # 小X，小XX
        r'老[\u4e00-\u9fff]{1,2}',  # 老X，老XX
        r'[\u4e00-\u9fff]{1,2}(先生|小姐|同学|老师)'  # X先生，XX小姐等
    ]
    
    for pattern in person_patterns:
        entities["person"].extend(re.findall(pattern, text))
    
    # 地点识别（简化）
    location_patterns = [
        r'在([\u4e00-\u9fff]{2,6})',  # 在XX
        r'([\u4e00-\u9fff]{2,6})(大厦|公园|广场|街道|路|小区|中心)'  # XX路，XX小区等
    ]
    
    for pattern in location_patterns:
        entities["location"].extend(re.findall(pattern, text))
    
    # 物品识别（简化）
    object_patterns = [
        r'(这|那|一)(个|把|件|台|部)([\u4e00-\u9fff]{1,4})'  # 这个XX，那把XX等
    ]
    
    for pattern in object_patterns:
        matches = re.findall(pattern, text)
        entities["object"].extend([m[2] for m in matches if len(m) > 2])
    
    return entities

def detect_emotion(text: str) -> Tuple[str, float]:
    """
    检测文本情感倾向
    
    Args:
        text: 输入文本
        
    Returns:
        (情感类型, 置信度)
    """
    # 简化版情感分析，仅通过关键词匹配
    
    # 积极情感词
    positive_words = {
        "高兴", "快乐", "欢喜", "喜悦", "开心", "兴奋", "激动", "满意", "欣慰", "舒心", 
        "愉快", "好", "棒", "妙", "优秀", "精彩", "成功", "胜利", "希望", "美好",
        "幸福", "幸运", "感谢", "谢谢", "喜欢", "热爱", "爱", "微笑", "笑"
    }
    
    # 消极情感词
    negative_words = {
        "难过", "悲伤", "伤心", "痛苦", "忧愁", "伤感", "遗憾", "失望", "沮丧", "绝望", 
        "悲痛", "悲哀", "凄凉", "恐惧", "担忧", "焦虑", "紧张", "害怕", "恐慌", "苦恼",
        "烦躁", "生气", "愤怒", "暴怒", "讨厌", "憎恨", "怨恨", "厌恶", "反感", "不满"
    }
    
    # 分词
    tokens = tokenize_chinese(text)
    
    # 计算情感得分
    positive_count = sum(1 for token in tokens if token in positive_words)
    negative_count = sum(1 for token in tokens if token in negative_words)
    
    total_emotion_words = positive_count + negative_count
    if total_emotion_words == 0:
        return "neutral", 0.5  # 中性情感
    
    if positive_count > negative_count:
        confidence = positive_count / total_emotion_words
        return "positive", min(confidence, 0.95)
    elif negative_count > positive_count:
        confidence = negative_count / total_emotion_words
        return "negative", min(confidence, 0.95)
    else:
        return "neutral", 0.5


if __name__ == "__main__":
    # 简单测试
    test_text = "小明和小红一起去公园玩，他们很开心地度过了一个美好的下午。"
    
    print(f"原文: {test_text}")
    print(f"分词: {tokenize_chinese(test_text)}")
    print(f"关键词: {extract_keywords(test_text)}")
    print(f"情感: {detect_emotion(test_text)}")
    
    test_text2 = "小明很伤心，因为他丢失了心爱的玩具。"
    print(f"\n原文: {test_text2}")
    print(f"情感: {detect_emotion(test_text2)}")
    
    print(f"\n相似度: {calc_text_similarity(test_text, test_text2)}")
    
    print(f"\n实体: {extract_entities(test_text)}") 