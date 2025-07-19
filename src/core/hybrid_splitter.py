from typing import List, Dict
import re

def detect_char_lang(char: str) -> str:
    """判断单个字符的语言类型（支持中英文扩展）"""
    if '\u4e00' <= char <= '\u9fff':
        return 'zh'
    elif re.match(r'[a-zA-Z]', char):
        return 'en'
    else:
        return 'other'

def split_hybrid_content(text: str) -> List[Dict[str, str]]:
    """将混合文本按语言分段，支持中英文混合"""
    segments = []
    current_lang = None
    for char in text:
        lang = detect_char_lang(char)
        if lang == 'other':
            # 其他字符归入当前段落
            if segments:
                segments[-1]["text"] += char
            continue
        if lang != current_lang:
            segments.append({"lang": lang, "text": ""})
            current_lang = lang
        segments[-1]["text"] += char
    return segments 