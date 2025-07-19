"""
自然语言处理工具包
包含多种文本处理和分析工具，支持中英文
"""

import os
import sys
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def check_nlp_dependencies():
    """检查NLP依赖"""
    # 检查transformers
    try:
        import transformers
        logger.info(f"transformers可用: 版本 {transformers.__version__}")
    except ImportError:
        logger.warning("transformers未安装，深度学习模型功能受限")
    
    # 检查spaCy
    try:
        import spacy
        logger.info(f"spaCy可用: 版本 {spacy.__version__}")
    except ImportError:
        logger.warning("spaCy未安装，将使用备用方法进行NLP处理")
    
    # 检查jieba
    try:
        import jieba
        logger.info(f"jieba可用: 版本 {jieba.__version__}")
    except ImportError:
        logger.warning("jieba未安装，中文分词功能可能受限")
    
    # 检查nltk
    try:
        import nltk
        logger.info(f"nltk可用: 版本 {nltk.__version__}")
    except ImportError:
        logger.warning("nltk未安装，自然语言处理功能可能受限")
    
    # 检查sentence-transformers
    try:
        import sentence_transformers
        logger.info(f"sentence-transformers可用: 版本 {sentence_transformers.__version__}")
    except ImportError:
        logger.warning("sentence-transformers未安装，文本嵌入功能将使用备用算法")

# 运行依赖检查
check_nlp_dependencies()

# 导入主要函数
try:
    # 尝试使用自定义情感分析器
    try:
        from src.nlp.sentiment_analyzer_custom import (
            analyze_text_sentiment, 
            analyze_sentiment,
            analyze_batch
        )
        logger.info("已加载自定义情感分析器")
    except ImportError:
        # 如果自定义情感分析器不可用，尝试使用原始情感分析器
        from src.nlp.sentiment_analyzer import (
            analyze_text_sentiment, 
            analyze_sentiment,
            analyze_batch
        )
        logger.info("已加载原始情感分析器")
except ImportError:
    logger.warning("主要情感分析器不可用，使用备用版本")
    from src.nlp.sentiment_analyzer_fallback import analyze_text_sentiment
    
    # 为了保持API一致，提供与主版本相同的函数名
    def analyze_sentiment(text, lang="auto"):
        return analyze_text_sentiment(text)
    
    def analyze_batch(texts, lang="auto"):
        return [analyze_text_sentiment(text) for text in texts]

# 导入文本嵌入功能
try:
    # 尝试使用自定义文本嵌入
    try:
        from src.nlp.text_embeddings_custom import (
            get_sentence_embeddings,
            get_document_embedding,
            calculate_cosine_similarity,
            clear_embedding_cache
        )
        logger.info("已加载自定义文本嵌入功能")
    except ImportError:
        # 如果自定义文本嵌入不可用，尝试使用原始文本嵌入
        from src.nlp.text_embeddings import (
            get_sentence_embeddings,
            get_document_embedding,
            calculate_cosine_similarity,
            clear_embedding_cache
        )
        logger.info("已加载原始文本嵌入功能")
except ImportError:
    logger.warning("文本嵌入功能不可用")
    
    # 提供备用的空实现
    import numpy as np
    
    def get_sentence_embeddings(texts, use_cache=True):
        if isinstance(texts, str):
            return np.zeros(384)
        return np.zeros((len(texts), 384))
    
    def get_document_embedding(document):
        return np.zeros(384)
    
    def calculate_cosine_similarity(vec1, vec2):
        return 0.0
    
    def clear_embedding_cache():
        return 0

__all__ = [
    'analyze_text_sentiment', 'analyze_sentiment', 'analyze_batch',
    'get_sentence_embeddings', 'get_document_embedding', 
    'calculate_cosine_similarity', 'clear_embedding_cache'
]

# 延迟导入以提高启动性能
def get_sentiment_analyzer():
    from src.nlp.sentiment_analyzer import sentiment_analyzer
    return sentiment_analyzer

def get_srl_annotator():
    from src.nlp.srl_annotator import srl_annotator
    return srl_annotator

def process_subtitle_text(subtitle_text, target_language="auto", style="viral", intensity=0.7):
    """
    处理字幕文本，生成具有特定风格的新字幕
    
    Args:
        subtitle_text: 原始字幕文本（SRT格式）
        target_language: 目标语言（'auto'自动检测，'zh'中文，'en'英文）
        style: 目标风格 ("viral"爆款, "formal"正式, "casual"休闲)
        intensity: 风格强度 (0.0-1.0)
        
    Returns:
        dict: 处理结果，包含viral_text字段
    """
    import re
    import random
    
    # 记录日志
    logger.info(f"处理字幕，目标风格: {style}, 强度: {intensity}")
    
    # 检测字幕语言
    lang = "auto"
    if len(subtitle_text) > 10:
        try:
            from langdetect import detect
            sample_text = re.sub(r'\d+|:|-->|，|。|！|？', '', subtitle_text)
            sample_text = ' '.join(sample_text.split()[:100])
            lang = detect(sample_text)
        except:
            if re.search(r'[\u4e00-\u9fff]', subtitle_text):
                lang = "zh"
            else:
                lang = "en"
    
    # 解析SRT
    subtitle_blocks = []
    current_block = []
    for line in subtitle_text.strip().split('\n'):
        if line.strip().isdigit() and current_block:
            subtitle_blocks.append(current_block)
            current_block = []
        current_block.append(line)
    
    if current_block:
        subtitle_blocks.append(current_block)
    
    # 生成新字幕
    result_blocks = []
    
    # 定义风格词汇库
    viral_prefixes = [
        "【震撼】", "【独家】", "【揭秘】", "【必看】", "【紧急】",
        "【重磅】", "【突发】", "【首发】", "【爆料】", "【惊呆】"
    ]
    viral_suffixes = [
        "太震撼了！", "简直难以置信！", "史诗级体验！", "满分推荐！", 
        "不容错过！", "超乎想象！", "前所未见！", "必看系列！"
    ]
    
    for block in subtitle_blocks:
        new_block = []
        for i, line in enumerate(block):
            if i < 2:  # 保留序号和时间码
                new_block.append(line)
            elif line.strip():  # 处理文本行
                # 如果是爆款风格，添加爆款特征
                if style == "viral" and len(line) > 3:
                    if random.random() < intensity * 0.3:
                        prefix = random.choice(viral_prefixes)
                    else:
                        prefix = ""
                        
                    if random.random() < intensity * 0.2:
                        suffix = random.choice(viral_suffixes)
                    else:
                        suffix = ""
                    
                    new_line = f"{prefix}{line}{suffix}"
                    new_block.append(new_line)
                else:
                    new_block.append(line)
            else:  # 保留空行
                new_block.append(line)
        
        result_blocks.append(new_block)
    
    # 组装结果
    viral_text = '\n'.join(['\n'.join(block) for block in result_blocks])
    
    return {
        "original_text": subtitle_text,
        "viral_text": viral_text,
        "language": lang,
        "style": style,
        "intensity": intensity,
        "success": True
    }

# 更新__all__列表
__all__.extend(['process_subtitle_text', 'get_sentiment_analyzer', 'get_srl_annotator']) 