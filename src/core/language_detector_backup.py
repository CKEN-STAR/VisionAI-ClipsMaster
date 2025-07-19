"""
Language detection module for subtitle files.
"""

import os
import re
import logging
from typing import Optional, List, Dict, Any
import json

# 尝试导入可选语言检测库
try:
    import langdetect
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False

# 使用模拟的spaCy模块
from src.utils.log_handler import check_spacy
SPACY_AVAILABLE = check_spacy()

# 尝试导入spaCy
try:
    import spacy
except ImportError:
    spacy = None

logger = logging.getLogger(__name__)

# 语言代码映射
LANGUAGE_CODES = {
    "en": "english",
    "zh": "chinese",
    "fr": "french",
    "de": "german",
    "es": "spanish",
    "it": "italian",
    "ja": "japanese",
    "ko": "korean",
    "pt": "portuguese",
    "ru": "russian"
}

def detect_language(subtitle_file: str) -> str:
    """
    检测字幕文件的语言
    
    Args:
        subtitle_file: 字幕文件路径
        
    Returns:
        语言代码 (en/zh)
    """
    # 验证文件存在
    if not os.path.exists(subtitle_file):
        raise FileNotFoundError(f"字幕文件不存在: {subtitle_file}")
    
    # 读取字幕文件
    with open(subtitle_file, 'r', encoding='utf-8') as f:
        subtitle_text = f.read()
    
    # 提取纯文本内容
    text_content = extract_text_from_srt(subtitle_text)
    
    # 如果文本内容为空，返回默认语言
    if not text_content.strip():
        logger.warning(f"字幕文件 {subtitle_file} 中未找到文本内容，使用默认语言 (zh)")
        return "zh"
    
    # 使用主语言检测算法
    lang_code = _detect_language_primary(text_content)
    
    # 如果主检测算法失败，尝试备用方法
    if not lang_code:
        lang_code = _detect_language_fallback(text_content)
    
    # 映射语言代码 (目前只支持中文和英文)
    if lang_code and lang_code.startswith('zh'):
        return 'zh'
    elif lang_code and lang_code.startswith('en'):
        return 'en'
    
    # 默认返回中文
    logger.warning(f"无法确定字幕语言，使用默认语言 (zh)")
    return 'zh'

def _detect_language_primary(text: str) -> Optional[str]:
    """主语言检测算法"""
    # 尝试使用langdetect
    if LANGDETECT_AVAILABLE:
        try:
            lang = langdetect.detect(text)
            logger.debug(f"langdetect检测到语言: {lang}")
            return lang
        except Exception as e:
            logger.warning(f"langdetect检测失败: {str(e)}")
    
    # 尝试使用spaCy
    if SPACY_AVAILABLE:
        try:
            # 这里可以根据需要加载spaCy语言模型
            # 注意：需要先使用 python -m spacy download xx 下载语言模型
            # 例如：预测主要是在中英文之间，可以加载小的模型
            nlp = spacy.blank("xx")  # 使用多语言模型或空白模型
            doc = nlp(text[:500])  # 仅处理前500个字符
            
            # 这里实现spaCy语言检测逻辑
            # 实际实现中，需要根据spaCy的具体API进行适配
            
            logger.debug(f"spaCy检测到语言特征")
            # 此处返回语言代码
            return None  # 暂时返回None，使用备用方法
        except Exception as e:
            logger.warning(f"spaCy检测失败: {str(e)}")
    
    return None

def _detect_language_fallback(text: str) -> str:
    """备用语言检测算法"""
    # 简单规则检测中文特征
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    english_words = len(re.findall(r'\b[a-zA-Z]+\b', text))
    
    # 字符比例检测
    if chinese_chars > english_words * 0.3:
        logger.debug(f"备用检测算法检测到中文特征 (中文字符数: {chinese_chars}, 英文单词数: {english_words})")
        return 'zh'
    else:
        logger.debug(f"备用检测算法检测到英文特征 (中文字符数: {chinese_chars}, 英文单词数: {english_words})")
        return 'en'

def extract_text_from_srt(srt_content: str) -> str:
    """
    从SRT字幕中提取纯文本内容
    
    Args:
        srt_content: SRT字幕内容
        
    Returns:
        提取的纯文本
    """
    # SRT格式正则表达式 (匹配序号、时间码和文本内容)
    pattern = r'\d+\s+\d{2}:\d{2}:\d{2},\d{3}\s+-->\s+\d{2}:\d{2}:\d{2},\d{3}\s+(.*?)(?=\n\s*\n|\Z)'
    
    # 提取所有文本行
    matches = re.findall(pattern, srt_content, re.DOTALL)
    
    # 合并文本行
    text = '\n'.join(matches)
    
    # 去除HTML标签
    text = re.sub(r'<[^>]+>', '', text)
    
    return text.strip()

def get_supported_languages() -> List[Dict[str, Any]]:
    """
    获取支持的语言列表
    
    Returns:
        支持的语言列表，包含代码和名称
    """
    return [
        {"code": "zh", "name": "中文", "enabled": True, "default": True},
        {"code": "en", "name": "英文", "enabled": False, "default": False}
    ]

class LanguageDetector:
    """语言检测器类"""
    
    def __init__(self, cache_dir: Optional[str] = None):
        """初始化语言检测器
        
        Args:
            cache_dir: 缓存目录，用于存储语言检测结果
        """
        self.cache_dir = cache_dir
        self.cache = {}
        
        # 如果指定了缓存目录，尝试加载缓存
        if cache_dir and os.path.exists(cache_dir):
            self._load_cache()
        
        logger.debug("语言检测器初始化完成")
    
    def detect_from_file(self, subtitle_file: str) -> str:
        """从字幕文件检测语言
        
        Args:
            subtitle_file: 字幕文件路径
            
        Returns:
            语言代码 (en/zh)
        """
        # 检查缓存
        if subtitle_file in self.cache:
            logger.debug(f"从缓存获取语言: {subtitle_file} -> {self.cache[subtitle_file]}")
            return self.cache[subtitle_file]
        
        # 调用检测函数
        lang_code = detect_language(subtitle_file)
        
        # 更新缓存
        self.cache[subtitle_file] = lang_code
        self._save_cache()
        
        return lang_code
    
    def detect_from_text(self, text: str) -> str:
        """从文本内容检测语言
        
        Args:
            text: 文本内容
            
        Returns:
            语言代码 (en/zh)
        """
        # 首先尝试主检测算法
        lang_code = _detect_language_primary(text)
        
        # 如果主检测算法失败，尝试备用方法
        if not lang_code:
            lang_code = _detect_language_fallback(text)
        
        # 映射语言代码 (目前只支持中文和英文)
        if lang_code and lang_code.startswith('zh'):
            return 'zh'
        elif lang_code and lang_code.startswith('en'):
            return 'en'
        
        # 默认返回中文
        logger.warning(f"无法确定文本语言，使用默认语言 (zh)")
        return 'zh'
    
    def _load_cache(self) -> None:
        """加载语言检测缓存"""
        cache_file = os.path.join(self.cache_dir, 'language_cache.json')
        
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    self.cache = json.load(f)
                logger.debug(f"已加载语言检测缓存: {len(self.cache)}条记录")
            except Exception as e:
                logger.warning(f"加载语言检测缓存失败: {str(e)}")
                self.cache = {}
    
    def _save_cache(self) -> None:
        """保存语言检测缓存"""
        if not self.cache_dir:
            return
        
        # 确保缓存目录存在
        os.makedirs(self.cache_dir, exist_ok=True)
        
        cache_file = os.path.join(self.cache_dir, 'language_cache.json')
        
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
            logger.debug(f"已保存语言检测缓存: {len(self.cache)}条记录")
        except Exception as e:
            logger.warning(f"保存语言检测缓存失败: {str(e)}")
    
    def clear_cache(self) -> int:
        """清除缓存
        
        Returns:
            int: 清除的缓存条目数
        """
        count = len(self.cache)
        self.cache = {}
        
        if self.cache_dir:
            cache_file = os.path.join(self.cache_dir, 'language_cache.json')
            if os.path.exists(cache_file):
                try:
                    os.remove(cache_file)
                    logger.debug("已删除语言检测缓存文件")
                except Exception as e:
                    logger.warning(f"删除语言检测缓存文件失败: {str(e)}")
        
        return count
    
    def get_supported_languages(self) -> List[Dict[str, Any]]:
        """获取支持的语言列表
        
        Returns:
            List[Dict]: 支持的语言列表
        """
        return get_supported_languages()

    def detect_language(self, text: str) -> str:
        """检测文本语言（进一步优化的混合语言处理）"""
        if not text.strip():
            return "unknown"

        # 统计语言特征
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        # 使用更精确的英文单词识别
        english_words_list = re.findall(r'[a-zA-Z]+', text)
        english_words = len(english_words_list)

        # 分析文本结构
        words = text.split()
        total_words = len(words)

        # 计算字符比例而不是单词比例
        total_chars = len(re.sub(r'[^\u4e00-\u9fffa-zA-Z]', '', text))  # 只计算中英文字符
        chinese_char_ratio = chinese_chars / max(total_chars, 1)
        english_char_ratio = sum(len(word) for word in english_words_list) / max(total_chars, 1)

        # 重新设计判断逻辑
        # 1. 如果中文字符比例超过60%，判断为中文主导
        if chinese_char_ratio >= 0.6:
            return "zh"

        # 2. 如果英文字符比例超过60%，判断为英文主导
        if english_char_ratio >= 0.6:
            return "en"

        # 3. 特殊处理：以英文时间词开头的句子
        first_word = words[0] if words else ""
        time_words = ["Today", "Yesterday", "Tomorrow", "Now", "Then", "Here", "There", "Let's", "She", "He", "The"]
        if any(first_word.startswith(tw) for tw in time_words) and english_words >= 3:
            return "en"

        # 4. 如果中文字符数量明显多于英文单词数量，判断为中文主导
        if chinese_chars >= english_words and chinese_chars >= 3:
            return "zh"

        # 5. 如果英文单词数量明显多于中文字符数量，判断为英文主导
        if english_words > chinese_chars and english_words >= 3:
            return "en"

        # 6. 其他情况按字符比例判断
        if chinese_char_ratio > english_char_ratio:
            return "zh"
        elif english_char_ratio > chinese_char_ratio:
            return "en"
        elif chinese_chars > 0:
            return "zh"
        else:
            return "en"  # 默认英文

    def get_confidence(self, text: str) -> float:
        """获取检测置信度（改进实现）"""
        if not text.strip():
            return 0.0

        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        english_words = len(re.findall(r'\b[a-zA-Z]+\b', text))
        total_chars = len(text.replace(' ', ''))  # 排除空格

        if total_chars == 0:
            return 0.0

        # 改进的置信度计算
        detected_lang = self.detect_language(text)

        if detected_lang == "zh":
            # 中文置信度：中文字符比例
            confidence = min(chinese_chars / max(total_chars, 1) * 1.5, 1.0)
        elif detected_lang == "en":
            # 英文置信度：英文单词密度
            word_density = english_words / max(len(text.split()), 1)
            confidence = min(word_density * 1.2, 1.0)
        else:
            confidence = 0.5

        return max(confidence, 0.1)  # 最低置信度0.1

# 全局实例
_language_detector = None

def get_language_detector():
    """获取语言检测器实例"""
    global _language_detector
    if _language_detector is None:
        _language_detector = LanguageDetector()
    return _language_detector
