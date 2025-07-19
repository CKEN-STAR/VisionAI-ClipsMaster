"""混合数据处理模块

此模块负责处理包含多语言混合的内容，主要功能包括：
1. 检测文本中的中英文比例
2. 识别主导语言
3. 处理混合内容的分割和清理
4. 验证混合内容的合规性
"""

import re
from typing import Tuple, Optional
from loguru import logger

from src.utils.exceptions import HybridContentError


class HybridContentHandler:
    """混合内容处理器类"""

    def __init__(self):
        """初始化混合内容处理器"""
        # 定义语言检测的阈值
        self.ratio_threshold = 0.3  # 单一语言占比阈值
        self.mixed_threshold = 0.8  # 混合内容总占比阈值
        
        # 编译正则表达式以提高性能
        self.zh_pattern = re.compile(r'[\u4e00-\u9fff]')
        self.en_pattern = re.compile(r'[a-zA-Z]')
        self.number_pattern = re.compile(r'[0-9]')
        self.punct_pattern = re.compile(r'[^\w\s]')

    def chinese_char_ratio(self, text: str) -> float:
        """计算中文字符占比
        
        Args:
            text: 要分析的文本
            
        Returns:
            float: 中文字符占比
        """
        if not text:
            return 0.0
            
        total_chars = len(text)
        chinese_chars = len(self.zh_pattern.findall(text))
        
        return chinese_chars / total_chars

    def english_char_ratio(self, text: str) -> float:
        """计算英文字符占比
        
        Args:
            text: 要分析的文本
            
        Returns:
            float: 英文字符占比
        """
        if not text:
            return 0.0
            
        total_chars = len(text)
        english_chars = len(self.en_pattern.findall(text))
        
        return english_chars / total_chars

    def get_content_stats(self, text: str) -> dict:
        """获取文本内容的统计信息
        
        Args:
            text: 要分析的文本
            
        Returns:
            dict: 包含各类字符统计信息的字典
        """
        if not text:
            return {
                'total_length': 0,
                'chinese_ratio': 0.0,
                'english_ratio': 0.0,
                'number_ratio': 0.0,
                'punct_ratio': 0.0,
                'space_ratio': 0.0
            }
            
        total_length = len(text)
        chinese_chars = len(self.zh_pattern.findall(text))
        english_chars = len(self.en_pattern.findall(text))
        number_chars = len(self.number_pattern.findall(text))
        punct_chars = len(self.punct_pattern.findall(text))
        space_chars = len([c for c in text if c.isspace()])
        
        return {
            'total_length': total_length,
            'chinese_ratio': chinese_chars / total_length,
            'english_ratio': english_chars / total_length,
            'number_ratio': number_chars / total_length,
            'punct_ratio': punct_chars / total_length,
            'space_ratio': space_chars / total_length
        }

    def dominant_lang(self, text: str) -> str:
        """确定文本的主导语言
        
        Args:
            text: 要分析的文本
            
        Returns:
            str: 主导语言代码 ('zh', 'en' 或 'mixed')
        """
        zh_ratio = self.chinese_char_ratio(text)
        en_ratio = self.english_char_ratio(text)
        
        if zh_ratio > en_ratio and zh_ratio > self.ratio_threshold:
            return 'zh'
        elif en_ratio > zh_ratio and en_ratio > self.ratio_threshold:
            return 'en'
        else:
            return 'mixed'

    def split_mixed_content(self, text: str) -> Tuple[str, str]:
        """分割混合内容为中英文部分
        
        Args:
            text: 要分割的文本
            
        Returns:
            Tuple[str, str]: (中文内容, 英文内容)
        """
        chinese_parts = []
        english_parts = []
        current_part = []
        current_type = None
        
        for char in text:
            if self.zh_pattern.match(char):
                if current_type == 'en':
                    english_parts.append(''.join(current_part))
                    current_part = []
                current_type = 'zh'
                current_part.append(char)
            elif self.en_pattern.match(char):
                if current_type == 'zh':
                    chinese_parts.append(''.join(current_part))
                    current_part = []
                current_type = 'en'
                current_part.append(char)
            else:
                if current_part:
                    if current_type == 'zh':
                        chinese_parts.append(''.join(current_part))
                    else:
                        english_parts.append(''.join(current_part))
                    current_part = []
                current_type = None
                
        # 处理最后一部分
        if current_part:
            if current_type == 'zh':
                chinese_parts.append(''.join(current_part))
            else:
                english_parts.append(''.join(current_part))
                
        return ' '.join(chinese_parts), ' '.join(english_parts)

    def validate_mixed_ratio(self, text: str) -> Tuple[bool, Optional[str]]:
        """验证混合内容的比例是否合理
        
        Args:
            text: 要验证的文本
            
        Returns:
            Tuple[bool, Optional[str]]: (是否合规, 错误信息)
        """
        stats = self.get_content_stats(text)
        total_valid_ratio = (
            stats['chinese_ratio'] + 
            stats['english_ratio'] + 
            stats['punct_ratio'] + 
            stats['space_ratio']
        )
        
        if total_valid_ratio < self.mixed_threshold:
            return False, "有效内容比例过低"
            
        if stats['chinese_ratio'] > 0.3 and stats['english_ratio'] > 0.3:
            return False, "中英文混合比例过高"
            
        return True, None

    def handle_hybrid_content(self, text: str) -> str:
        """处理混合内容
        
        Args:
            text: 要处理的文本
            
        Returns:
            str: 处理后的文本
            
        Raises:
            HybridContentError: 当混合内容不符合要求时
        """
        # 首先验证混合比例
        is_valid, error_msg = self.validate_mixed_ratio(text)
        if not error_msg:
            logger.warning(f"混合内容验证失败: {error_msg}")
            raise HybridContentError(error_msg)
            
        # 确定主导语言
        main_lang = self.dominant_lang(text)
        
        if main_lang == 'mixed':
            # 对于无法确定主导语言的内容，进行分割处理
            zh_content, en_content = self.split_mixed_content(text)
            logger.info(f"混合内容已分割: 中文={len(zh_content)}字符, 英文={len(en_content)}字符")
            
            # 返回主要部分
            return zh_content if len(zh_content) > len(en_content) else en_content
        else:
            # 对于有明确主导语言的内容，直接返回
            return text

    def clean_hybrid_text(self, text: str) -> str:
        """清理混合文本
        
        Args:
            text: 要清理的文本
            
        Returns:
            str: 清理后的文本
        """
        # 移除多余的空白字符
        text = ' '.join(text.split())
        
        # 标准化标点符号
        text = re.sub(r'[，。！？、；：""''）（]', 
                     lambda m: {
                         '，': ',', '。': '.', '！': '!', '？': '?',
                         '、': ',', '；': ';', '：': ':',
                         '"': '"', '"': '"', ''': "'", ''': "'",
                         '（': '(', '）': ')'
                     }.get(m.group(), m.group()),
                     text)
        
        return text 