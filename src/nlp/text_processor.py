#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
文本处理器

提供文本分词、预处理、清洗和标准化功能。
为情感分析和焦点定位等NLP模块提供基础文本处理支持。
"""

import re
import string
import unicodedata
from typing import List, Dict, Any, Set, Optional, Union
from loguru import logger

class TextProcessor:
    """文本处理器，提供各种文本预处理功能"""
    
    def __init__(self, language: str = "zh"):
        """
        初始化文本处理器
        
        Args:
            language: 语言代码，默认为中文 (zh)
        """
        self.language = language
        
        # 停用词集
        self.stopwords = self._load_stopwords()
        
        # 标点符号集
        self.punctuation = set(string.punctuation + "，。！？；：""''（）【】《》、…")
    
    def _load_stopwords(self) -> Set[str]:
        """
        加载停用词表
        
        Returns:
            停用词集合
        """
        # 默认停用词
        default_stopwords = {
            "的", "了", "和", "是", "在", "我", "有", "这", "他", "们",
            "来", "到", "时", "地", "得", "着", "那", "就", "很", "可以",
            "你", "会", "对", "吗", "都", "而", "去", "被", "还", "说"
        }
        
        # 可以从文件加载更完整的停用词表
        # TODO: 实现从文件加载停用词
        
        return default_stopwords
    
    def split_sentences(self, text: str) -> List[str]:
        """
        将文本分割为句子
        
        Args:
            text: 输入文本
            
        Returns:
            句子列表
        """
        if not text:
            return []
        
        # 句子分隔符模式
        if self.language == "zh":
            # 中文句子分隔符
            pattern = r'([^。！？\!\?]+[。！？\!\?]+)'
            sentences = re.findall(pattern, text)
            
            # 处理最后可能没有标点的句子
            last_end = 0
            for s in sentences:
                last_end = text.find(s, last_end) + len(s)
            
            if last_end < len(text.strip()):
                remaining = text[last_end:].strip()
                if remaining:
                    sentences.append(remaining)
        else:
            # 英文句子分隔符
            pattern = r'([^\.!\?]+[\.!\?]+)'
            sentences = re.findall(pattern, text)
            
            # 处理最后可能没有标点的句子
            if text and not any(text.endswith(p) for p in ['.', '!', '?']):
                last_period = max(text.rfind('.'), text.rfind('!'), text.rfind('?'))
                if last_period != -1 and last_period < len(text) - 1:
                    remaining = text[last_period + 1:].strip()
                    if remaining:
                        sentences.append(remaining)
        
        return [s.strip() for s in sentences if s.strip()]
    
    def normalize_text(self, text: str) -> str:
        """
        标准化文本，去除异常字符，转换为一致格式
        
        Args:
            text: 输入文本
            
        Returns:
            标准化后的文本
        """
        if not text:
            return ""
        
        # 将全角字符转换为半角
        text = self._full_to_half(text)
        
        # 去除多余空白
        text = ' '.join(text.split())
        
        # 中文文本特殊处理
        if self.language == "zh":
            # 统一中文标点
            text = re.sub(r'\.{3,}', '…', text)  # 将多个点替换为省略号
            text = re.sub(r'\.{2}', '。', text)   # 将双点替换为句号
            
            # 确保常见标点间没有空格
            text = re.sub(r'\s+([，。！？；：])', r'\1', text)
        
        return text
    
    def _full_to_half(self, text: str) -> str:
        """
        将全角字符转换为半角字符
        
        Args:
            text: 输入文本
            
        Returns:
            转换后的文本
        """
        result = ""
        for char in text:
            # 全角空格直接转换
            if char == '\u3000':
                result += ' '
            # 其他字符通过unicode转换
            else:
                code = ord(char)
                if code == 0x3000:
                    code = 0x20
                elif 0xFF01 <= code <= 0xFF5E:
                    code -= 0xFEE0
                result += chr(code)
        return result
    
    def clean_text(self, text: str, remove_stopwords: bool = False) -> str:
        """
        清洗文本，去除无用信息
        
        Args:
            text: 输入文本
            remove_stopwords: 是否去除停用词
            
        Returns:
            清洗后的文本
        """
        if not text:
            return ""
        
        # 标准化
        text = self.normalize_text(text)
        
        # 去除特殊字符（保留中文标点）
        text = re.sub(r'[^\w\s，。！？；：""''（）【】《》、…]', '', text)
        
        # 去除停用词
        if remove_stopwords:
            words = text.split()
            words = [w for w in words if w.lower() not in self.stopwords]
            text = ' '.join(words)
        
        return text.strip()
    
    def extract_keywords(self, text: str, top_n: int = 5) -> List[str]:
        """
        提取文本中的关键词
        
        简单实现，基于词频和停用词过滤
        
        Args:
            text: 输入文本
            top_n: 返回前N个关键词
            
        Returns:
            关键词列表
        """
        if not text:
            return []
        
        # 清洗文本
        clean_text = self.clean_text(text, remove_stopwords=True)
        
        # 中文分词
        if self.language == "zh":
            try:
                import jieba
                words = jieba.lcut(clean_text)
            except ImportError:
                # 如果没有jieba，简单按空格分词
                words = clean_text.split()
        else:
            # 英文按空格分词
            words = clean_text.split()
        
        # 过滤停用词和标点
        words = [w for w in words if w and w not in self.stopwords and w not in self.punctuation]
        
        # 统计词频
        word_freq = {}
        for word in words:
            if len(word) > 1:  # 仅统计长度大于1的词
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # 按词频排序，返回前N个
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_words[:top_n]]
    
    def detect_language(self, text: str) -> str:
        """
        检测文本语言
        
        简单实现，基于字符特征判断
        
        Args:
            text: 输入文本
            
        Returns:
            检测到的语言代码 (zh/en)
        """
        if not text:
            return "unknown"
        
        # 统计中文和英文字符数量
        chinese_chars = 0
        english_chars = 0
        
        for char in text:
            if '\u4e00' <= char <= '\u9fff':
                chinese_chars += 1
            elif 'a' <= char.lower() <= 'z':
                english_chars += 1
        
        # 根据字符比例判断
        if chinese_chars > english_chars:
            return "zh"
        elif english_chars > chinese_chars:
            return "en"
        else:
            return "unknown"


def process_text(text: str, language: str = None) -> Dict[str, Any]:
    """
    处理文本的便捷函数
    
    Args:
        text: 输入文本
        language: 指定语言，如不指定则自动检测
        
    Returns:
        文本处理结果，包含分句、关键词等信息
    """
    processor = TextProcessor()
    
    # 如果未指定语言，自动检测
    if language is None:
        language = processor.detect_language(text)
        processor.language = language
    
    # 标准化文本
    normalized_text = processor.normalize_text(text)
    
    # 分句
    sentences = processor.split_sentences(normalized_text)
    
    # 提取关键词
    keywords = processor.extract_keywords(normalized_text)
    
    return {
        "text": normalized_text,
        "language": language,
        "sentences": sentences,
        "sentence_count": len(sentences),
        "keywords": keywords
    } 