import re
import yaml
from typing import List, Dict
from loguru import logger
import os

class TermGuard:
    """术语保护系统，支持多语言术语保护与还原"""
    def __init__(self, config_path: str = "configs/protected_terms.yaml", lang: str = "zh"):
        self.lang = lang
        self.protected_terms = self._load_term_list(config_path, lang)

    def _load_term_list(self, config_path: str, lang: str) -> List[str]:
        """加载指定语言的术语表"""
        if not os.path.exists(config_path):
            logger.warning(f"术语配置文件不存在: {config_path}")
            return []
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            return data.get(lang, [])
        except Exception as e:
            logger.error(f"加载术语表失败: {e}")
            return []

    def protect(self, text: str) -> str:
        """在翻译/重构时保护术语原样"""
        for term in sorted(self.protected_terms, key=len, reverse=True):
            # 避免嵌套保护，使用正则确保完整词匹配
            pattern = re.escape(term)
            text = re.sub(fr'(?<!\[PROTECT\]?)({pattern})(?!\[/PROTECT\])', r'[PROTECT]\1[/PROTECT]', text)
        return text

    def restore(self, processed_text: str) -> str:
        """移除保护标记，恢复原文"""
        return re.sub(r'\[/?PROTECT\]', '', processed_text)

    def update_language(self, lang: str, config_path: str = "configs/protected_terms.yaml"):
        """切换术语语言"""
        self.lang = lang
        self.protected_terms = self._load_term_list(config_path, lang) 