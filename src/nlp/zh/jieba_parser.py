#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中文Jieba解析器
提供中文文本的分词、词性标注、命名实体识别和情感分析功能
"""

import logging
from typing import Dict, List, Any, Optional

# 导入情感分析功能
from src.nlp.sentiment_analyzer import analyze_sentiment, analyze_text

logger = logging.getLogger(__name__)

class JiebaParser:
    """中文Jieba解析器"""

    def __init__(self):
        """初始化解析器"""
        self.jieba = None
        try:
            import jieba
            import jieba.posseg as pseg
            self.jieba = jieba
            self.pseg = pseg
            logger.info("中文Jieba解析器初始化完成")
        except ImportError:
            logger.warning("jieba库未安装，使用简单分词")

    def parse_text(self, text: str) -> Dict[str, Any]:
        """解析中文文本"""
        try:
            # 基本的文本分析
            if self.jieba:
                # 使用jieba分词
                tokens = list(self.jieba.cut(text))
                # 词性标注
                pos_tags = [(word, flag) for word, flag in self.pseg.cut(text)]
            else:
                # 简单分词（按字符）
                tokens = list(text)
                pos_tags = [(char, 'n') for char in text if char.strip()]

            result = {
                "text": text,
                "language": "zh",
                "tokens": tokens,
                "pos_tags": pos_tags,
                "entities": [],
                "sentiment": analyze_sentiment(text)
            }

            return result

        except Exception as e:
            logger.error(f"中文文本解析失败: {e}")
            return {
                "text": text,
                "language": "zh",
                "tokens": [],
                "pos_tags": [],
                "entities": [],
                "sentiment": {"label": "NEUTRAL", "intensity": 0.5}
            }

# 创建全局解析器实例
_parser = None

def get_parser() -> JiebaParser:
    """获取或创建解析器实例"""
    global _parser
    if _parser is None:
        _parser = JiebaParser()
    return _parser

def parse_chinese_text(text: str) -> Dict[str, Any]:
    """解析中文文本的便捷函数"""
    return get_parser().parse_text(text)

# 为了兼容性，提供analyze_text_sentiment函数
def analyze_text_sentiment(text: str) -> Dict[str, Any]:
    """分析中文文本情感（兼容性函数）"""
    return analyze_sentiment(text)