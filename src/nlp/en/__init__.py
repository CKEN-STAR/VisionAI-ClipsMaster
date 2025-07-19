"""
VisionAI-ClipsMaster 英文自然语言处理模块

此模块包含专门处理英文文本的NLP组件，包括：
- 英文分词
- 英文实体识别
- 英文情感分析
- 英文文本嵌入
等专用于英文的功能
"""

from loguru import logger
from src.nlp.en.beat_analyzer_en import EnBeatAnalyzer

__all__ = ['EnBeatAnalyzer']

def get_available_modules():
    """返回可用的英文NLP模块列表"""
    modules = []
    
    try:
        import nltk
        modules.append("nltk")
    except ImportError:
        logger.warning("NLTK未安装，某些英文处理功能可能受限")
    
    return modules 