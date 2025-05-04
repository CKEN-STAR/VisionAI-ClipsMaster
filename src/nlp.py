#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
NLP工具模块 - 简化版（UI演示用）
"""

import logging
import importlib.util
import sys
from pathlib import Path

# 设置日志
logger = logging.getLogger(__name__)

# 检查各种NLP库的可用性
def check_transformers():
    """检查transformers库是否可用"""
    try:
        import transformers
        logger.info(f"transformers可用: 版本 {transformers.__version__}")
        return True
    except ImportError:
        logger.warning("transformers未安装，高级NLP功能不可用")
        return False

def check_spacy():
    """检查spaCy库是否可用"""
    try:
        import spacy
        logger.info(f"spaCy可用: 版本 {spacy.__version__}")
        return True
    except ImportError:
        logger.warning("spaCy未安装，将使用备用方法进行NLP处理")
        return False

def check_jieba():
    """检查jieba库是否可用"""
    try:
        import jieba
        logger.info(f"jieba可用: 版本 {jieba.__version__}")
        return True
    except ImportError:
        logger.warning("jieba未安装，中文分词功能受限")
        return False

def check_nltk():
    """检查NLTK库是否可用"""
    try:
        import nltk
        logger.info(f"nltk可用: 版本 {nltk.__version__}")
        return True
    except ImportError:
        logger.warning("nltk未安装，部分自然语言处理功能受限")
        return False

def check_sentence_transformers():
    """检查sentence-transformers库是否可用"""
    try:
        import sentence_transformers
        logger.info(f"sentence-transformers可用: 版本 {sentence_transformers.__version__}")
        return True
    except ImportError:
        logger.warning("sentence-transformers未安装，语义相似度比较功能受限")
        return False

# 初始化
HAS_TRANSFORMERS = check_transformers()
HAS_SPACY = check_spacy()
HAS_JIEBA = check_jieba()
HAS_NLTK = check_nltk()
HAS_SENTENCE_TRANSFORMERS = check_sentence_transformers()

# 简单的文本处理功能
def segment_text(text, lang="auto"):
    """分词"""
    if lang == "auto":
        # 简单的语言检测
        if any('\u4e00' <= char <= '\u9fff' for char in text):
            lang = "zh"
        else:
            lang = "en"
    
    if lang == "zh":
        if HAS_JIEBA:
            import jieba
            return list(jieba.cut(text))
        else:
            # 极简中文分词
            return [char for char in text if char.strip()]
    else:
        if HAS_NLTK:
            import nltk
            return nltk.word_tokenize(text)
        else:
            # 极简英文分词
            return text.split()

def detect_emotion(text, lang="auto"):
    """情感检测"""
    if HAS_TRANSFORMERS:
        try:
            from transformers import pipeline
            classifier = pipeline("sentiment-analysis")
            result = classifier(text)
            return result[0]
        except Exception as e:
            logger.warning(f"主要情感分析器不可用，使用备用版本")
    
    # 备用情感分析（基于关键词）
    text = text.lower()
    positive_words = {"happy", "good", "excellent", "wonderful", "great", "love", "enjoy", "amazing"}
    negative_words = {"sad", "bad", "terrible", "awful", "hate", "dislike", "poor", "negative"}
    
    words = segment_text(text, lang)
    pos_count = sum(1 for word in words if word in positive_words)
    neg_count = sum(1 for word in words if word in negative_words)
    
    if pos_count > neg_count:
        return {"label": "POSITIVE", "score": 0.8}
    elif neg_count > pos_count:
        return {"label": "NEGATIVE", "score": 0.8}
    else:
        return {"label": "NEUTRAL", "score": 0.9}

def get_text_embedding(text):
    """获取文本嵌入向量"""
    if HAS_SENTENCE_TRANSFORMERS:
        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer('all-MiniLM-L6-v2')
            return model.encode(text)
        except Exception as e:
            logger.warning("文本嵌入功能不可用")
    
    # 返回一个简单的dummy向量
    return [0.0] * 10

# 初始化检查
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("NLP模块自检")
    check_transformers()
    check_spacy()
    check_jieba()
    check_nltk()
    check_sentence_transformers()
    
    # 测试功能
    text = "I love this product. It's amazing!"
    logger.info(f"测试文本: {text}")
    logger.info(f"分词结果: {segment_text(text)}")
    logger.info(f"情感检测: {detect_emotion(text)}")
    embedding = get_text_embedding(text)
    logger.info(f"文本嵌入 (前5维): {embedding[:5] if len(embedding) > 5 else embedding}") 