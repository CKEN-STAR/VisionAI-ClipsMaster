from typing import Tuple, Dict, List, Optional
from loguru import logger
import re

# 多语言情感词表
EMOTION_LEXICON = {
    "zh": {
        "positive": [
            "开心", "快乐", "高兴", "愉快", "幸福", "美好", "欢乐", "喜欢", "爱", "赞", 
            "好", "棒", "强", "优秀", "精彩", "成功", "胜利", "幸运", "惊喜", "感动",
            "希望", "温暖", "舒适", "轻松", "平静", "满意", "享受", "憧憬", "祝福"
        ],
        "negative": [
            "难过", "伤心", "痛苦", "悲伤", "忧愁", "沮丧", "失望", "绝望", "后悔", "内疚",
            "悔恨", "恐惧", "害怕", "担忧", "焦虑", "紧张", "恐慌", "厌恶", "讨厌", "恨",
            "愤怒", "生气", "烦躁", "不满", "怨恨", "嫉妒", "羞耻", "尴尬", "孤独"
        ]
    },
    "en": {
        "positive": [
            "happy", "joy", "delighted", "glad", "pleased", "cheerful", "content", "satisfied",
            "thrilled", "ecstatic", "elated", "jubilant", "good", "great", "wonderful", "amazing",
            "excellent", "fantastic", "terrific", "awesome", "love", "adore", "like", "enjoy",
            "appreciate", "grateful", "thankful", "hopeful", "optimistic", "excited"
        ],
        "negative": [
            "sad", "unhappy", "depressed", "miserable", "gloomy", "sorrowful", "grief", "heartbroken",
            "disappointed", "frustrated", "annoyed", "irritated", "angry", "mad", "furious", "enraged",
            "hate", "dislike", "detest", "loathe", "fear", "afraid", "scared", "terrified", "anxious",
            "worried", "stressed", "nervous", "disgusted", "regretful", "guilty", "ashamed", "embarrassed"
        ]
    }
}

def detect_language(text: str) -> str:
    """简单检测文本语言"""
    # 检测是否包含中文字符
    if re.search(r'[\u4e00-\u9fff]', text):
        return 'zh'
    # 默认返回英文
    return 'en'

def analyze_emotion(text: str) -> float:
    """多语言情感分析，返回[-1.0, 1.0]，可用NLP库替换"""
    # 检测语言
    lang = detect_language(text)
    
    # 获取对应语言的情感词表
    positive_words = EMOTION_LEXICON.get(lang, EMOTION_LEXICON['en'])['positive']
    negative_words = EMOTION_LEXICON.get(lang, EMOTION_LEXICON['en'])['negative']
    
    # 情感分析
    score = 0.0
    total_matches = 0
    
    # 文本标准化
    text_lower = text.lower()
    
    # 积极情感词计分
    for word in positive_words:
        matches = len(re.findall(re.escape(word.lower()), text_lower))
        if matches > 0:
            score += 0.5 * matches
            total_matches += matches
    
    # 消极情感词计分
    for word in negative_words:
        matches = len(re.findall(re.escape(word.lower()), text_lower))
        if matches > 0:
            score -= 0.5 * matches
            total_matches += matches
    
    # 归一化分数
    if total_matches > 0:
        score = score / (total_matches * 0.5)
    
    # 确保在范围内
    return max(-1.0, min(1.0, score))

def adjust_emotion(generated: str, target_emotion: float) -> str:
    """根据目标情感调整生成内容"""
    # 检测语言
    lang = detect_language(generated)
    
    # 根据语言和情感添加适当的标记
    if lang == 'zh':
        if target_emotion > 0.3:
            return generated + " [情感:积极]"
        elif target_emotion < -0.3:
            return generated + " [情感:消极]"
        else:
            return generated + " [情感:中性]"
    else:
        if target_emotion > 0.3:
            return generated + " [emotion:positive]"
        elif target_emotion < -0.3:
            return generated + " [emotion:negative]"
        else:
            return generated + " [emotion:neutral]"

def sync_emotion(origin: str, generated: str) -> str:
    """确保生成内容情感与原文一致"""
    try:
        origin_emotion = analyze_emotion(origin)
        generated_emotion = analyze_emotion(generated)
        
        # 判断情感差异是否超过阈值
        threshold = 0.3
        if abs(origin_emotion - generated_emotion) > threshold:
            logger.info(f"情感差异较大：原文情感={origin_emotion:.2f}，生成情感={generated_emotion:.2f}")
            return adjust_emotion(generated, origin_emotion)
        
        logger.debug(f"情感一致：原文情感={origin_emotion:.2f}，生成情感={generated_emotion:.2f}")
        return generated
    
    except Exception as e:
        logger.error(f"情感同步失败: {e}")
        return generated 