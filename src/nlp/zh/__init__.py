"""
中文自然语言处理模块
提供中文文本分析和处理功能
"""

from src.nlp.zh.beat_analyzer_zh import ZhBeatAnalyzer

__all__ = ['ZhBeatAnalyzer']

from loguru import logger

def get_available_modules():
    """返回可用的中文NLP模块列表"""
    modules = []
    
    try:
        import jieba
        modules.append("jieba")
    except ImportError:
        logger.warning("jieba未安装，中文分词功能受限")
    
    return modules 