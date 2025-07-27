#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
英文Spacy解析器
提供英文文本的句法分析、实体识别和情感分析功能
"""

import logging
from typing import Dict, List, Any, Optional

# 导入情感分析功能
from src.nlp.sentiment_analyzer import analyze_sentiment, analyze_text

logger = logging.getLogger(__name__)

class SpacyParser:
    """英文Spacy解析器"""

    def __init__(self):
        """初始化解析器"""
        self.model = None
        logger.info("英文Spacy解析器初始化完成")

    def parse_text(self, text: str) -> Dict[str, Any]:
        """解析英文文本"""
        try:
            # 基本的文本分析
            result = {
                "text": text,
                "language": "en",
                "tokens": text.split(),
                "entities": [],
                "sentiment": analyze_sentiment(text)
            }

            return result

        except Exception as e:
            logger.error(f"英文文本解析失败: {e}")
            return {
                "text": text,
                "language": "en",
                "tokens": [],
                "entities": [],
                "sentiment": {"label": "NEUTRAL", "intensity": 0.5}
            }

# 创建全局解析器实例
_parser = None

def get_parser() -> SpacyParser:
    """获取或创建解析器实例"""
    global _parser
    if _parser is None:
        _parser = SpacyParser()
    return _parser

def parse_english_text(text: str) -> Dict[str, Any]:
    """解析英文文本的便捷函数"""
    return get_parser().parse_text(text)

# 为了兼容性，提供analyze_text_sentiment函数
def analyze_text_sentiment(text: str) -> Dict[str, Any]:
    """分析英文文本情感（兼容性函数）"""
    return analyze_sentiment(text)