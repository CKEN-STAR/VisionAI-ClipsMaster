"""
语言检测工具

提供简单的语言检测功能，用于识别文本的语言类型
"""

import re
import os
import logging
from typing import Dict, Any, List, Optional, Union, Tuple
import json
from pathlib import Path

logger = logging.getLogger("language_detector")

# 语言特征特征
LANGUAGE_FEATURES = {
    "zh": {
        "name": "中文",
        "scripts": [
            (0x4E00, 0x9FFF),   # CJK 统一表意文字
            (0x3400, 0x4DBF),   # CJK 统一表意文字扩展 A
            (0x20000, 0x2A6DF), # CJK 统一表意文字扩展 B
        ],
        "common_words": ["的", "是", "在", "了", "和", "我", "有", "不", "这", "人"],
    },
    "en": {
        "name": "英文",
        "scripts": [
            (0x0041, 0x005A),   # 拉丁字母大写
            (0x0061, 0x007A),   # 拉丁字母小写
        ],
        "common_words": ["the", "be", "to", "of", "and", "a", "in", "that", "have", "I"],
    },
    "ja": {
        "name": "日文",
        "scripts": [
            (0x3040, 0x309F),   # 平假名
            (0x30A0, 0x30FF),   # 片假名
            (0x4E00, 0x9FFF),   # 汉字
        ],
        "common_words": ["の", "に", "は", "を", "た", "が", "で", "て", "と", "し"],
    },
    "ko": {
        "name": "韩文",
        "scripts": [
            (0xAC00, 0xD7A3),   # 韩文音节
            (0x1100, 0x11FF),   # 韩文字母
        ],
        "common_words": ["이", "는", "을", "에", "의", "가", "와", "한", "로", "하"],
    },
}


def detect_language(text: str, default: str = "zh") -> str:
    """
    检测文本的语言类型
    
    Args:
        text: 输入文本
        default: 默认语言
        
    Returns:
        语言代码，如'zh'、'en'等
    """
    if not text or len(text.strip()) == 0:
        return default
    
    # 字符分布统计
    lang_scores = {}
    
    # 分析字符脚本分布
    for lang_code, features in LANGUAGE_FEATURES.items():
        lang_scores[lang_code] = 0
        
        # 检查每个字符
        for char in text:
            code_point = ord(char)
            # 检查字符是否属于该语言的脚本范围
            for start, end in features["scripts"]:
                if start <= code_point <= end:
                    lang_scores[lang_code] += 1
                    break
    
    # 查找得分最高的语言
    if not lang_scores or max(lang_scores.values()) == 0:
        return default
    
    max_score = 0
    detected_lang = default
    
    for lang, score in lang_scores.items():
        if score > max_score:
            max_score = score
            detected_lang = lang
    
    # 如果中文和日文得分接近，进一步检查
    if detected_lang == "zh" and "ja" in lang_scores:
        if lang_scores["ja"] > lang_scores["zh"] * 0.8:
            # 检查日文特有字符
            hiragana_count = sum(1 for c in text if 0x3040 <= ord(c) <= 0x309F)
            katakana_count = sum(1 for c in text if 0x30A0 <= ord(c) <= 0x30FF)
            if hiragana_count + katakana_count > len(text) * 0.1:
                detected_lang = "ja"
    
    return detected_lang


def is_simplified_chinese(text: str) -> bool:
    """
    判断中文文本是简体还是繁体
    简单实现，可能不够精确
    
    Args:
        text: 中文文本
        
    Returns:
        bool: 是否是简体中文
    """
    # 简单识别，通过一些专有的简体和繁体字符
    simplified_chars = "国说话写对门来吗时"
    traditional_chars = "國說話寫對門來嗎時"
    
    simplified_count = sum(1 for c in text if c in simplified_chars)
    traditional_count = sum(1 for c in text if c in traditional_chars)
    
    return simplified_count >= traditional_count 