import logging
import re
from typing import Dict, Optional, Any

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('language_detector')

def detect_language(text: str) -> str:
    """检测文本语言，区分中文和英文
    
    Args:
        text: 输入文本
        
    Returns:
        str: 语言代码 ('zh', 'en', 或 'mixed' 如果无法确定)
    """
    if not text or not isinstance(text, str):
        logger.warning(f"输入文本为空或非字符串: {type(text)}")
        return 'zh'  # 默认返回中文
        
    # 清理文本，移除标点和数字
    clean_text = re.sub(r'[^\w\s]', '', text)
    clean_text = re.sub(r'\d+', '', clean_text)
    
    if not clean_text:
        logger.warning("清理后文本为空")
        return 'zh'  # 默认返回中文
        
    # 计算中文字符和英文字符的数量
    chinese_chars = len([c for c in clean_text if '\u4e00' <= c <= '\u9fff'])
    english_chars = len([c for c in clean_text if 'a' <= c.lower() <= 'z'])
    
    # 计算字符比例
    total_chars = len(clean_text.strip())
    if total_chars == 0:
        return 'zh'  # 默认中文
        
    chinese_ratio = chinese_chars / total_chars
    english_ratio = english_chars / total_chars
    
    logger.debug(f"中文比例: {chinese_ratio:.2f}, 英文比例: {english_ratio:.2f}")
    
    # 根据比例判断语言
    if chinese_ratio > 0.5:
        return 'zh'
    elif english_ratio > 0.5:
        return 'en'
    elif chinese_ratio > english_ratio:
        return 'zh'
    elif english_ratio > chinese_ratio:
        return 'en'
    else:
        # 如果无法确定，默认返回中文
        return 'zh'

def get_language_ratio(text: str) -> Dict[str, float]:
    """获取文本中各语言的比例
    
    Args:
        text: 输入文本
        
    Returns:
        Dict: 语言比例字典 {'zh': 中文比例, 'en': 英文比例, 'other': 其他字符比例}
    """
    if not text or not isinstance(text, str):
        return {'zh': 0.0, 'en': 0.0, 'other': 1.0}
        
    # 清理空白字符但保留其他字符
    clean_text = re.sub(r'\s+', ' ', text).strip()
    
    if not clean_text:
        return {'zh': 0.0, 'en': 0.0, 'other': 1.0}
        
    total_chars = len(clean_text)
    
    # 计算各种字符数量
    chinese_chars = len([c for c in clean_text if '\u4e00' <= c <= '\u9fff'])
    english_chars = len([c for c in clean_text if 'a' <= c.lower() <= 'z'])
    other_chars = total_chars - chinese_chars - english_chars
    
    # 计算比例
    return {
        'zh': chinese_chars / total_chars,
        'en': english_chars / total_chars,
        'other': other_chars / total_chars
    }

if __name__ == "__main__":
    # 测试代码
    test_texts = [
        "这是一段纯中文文本，应该检测为中文。",
        "This is English text only, should be detected as English.",
        "这是混合的文本 with some English words.",
        "80% 的文本是英文 but there's also some Chinese 在里面。",
        "特殊符号和数字：!@#$%^&*()1234567890",
        ""  # 空字符串测试
    ]
    
    for text in test_texts:
        lang = detect_language(text)
        ratios = get_language_ratio(text)
        print(f"文本: {text[:30]}..." if len(text) > 30 else f"文本: {text}")
        print(f"检测结果: {lang}")
        print(f"语言比例: 中文={ratios['zh']:.2f}, 英文={ratios['en']:.2f}, 其他={ratios['other']:.2f}")
        print("-" * 50) 