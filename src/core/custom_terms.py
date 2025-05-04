import json
import os
from typing import Dict, Set, List
from loguru import logger
import re

class UserTermManager:
    def __init__(self, file_path: str = "configs/user_terms.json"):
        self.file_path = file_path
        self.terms: Dict[str, Set[str]] = {}
        self.term_stats: Dict[str, Dict[str, int]] = {}  # 术语使用统计
        self._load_from_file()

    def _load_from_file(self):
        if not os.path.exists(self.file_path):
            self.terms = {}
            return
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.terms = {lang: set(terms) for lang, terms in data.get('user_terms', {}).items()}
            self.term_stats = data.get('term_stats', {})
        except Exception as e:
            logger.error(f"加载用户术语失败: {e}")
            self.terms = {}
            self.term_stats = {}

    def _save_to_file(self):
        try:
            data = {
                'user_terms': {lang: list(terms) for lang, terms in self.terms.items()},
                'term_stats': self.term_stats
            }
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存用户术语失败: {e}")

    def add_term(self, term: str, lang: str) -> bool:
        """添加用户自定义术语"""
        if not self.validate_term(term, lang):
            return False

        if lang not in self.terms:
            self.terms[lang] = set()
        self.terms[lang].add(term)
        self._save_to_file()
        return True

    def remove_term(self, term: str, lang: str) -> bool:
        """移除用户自定义术语"""
        if lang in self.terms and term in self.terms[lang]:
            self.terms[lang].remove(term)
            self._save_to_file()
            return True
        return False

    def get_terms(self, lang: str) -> Set[str]:
        """获取指定语言的所有术语"""
        return self.terms.get(lang, set())

    def validate_term(self, term: str, lang: str) -> bool:
        """验证术语是否有效"""
        if not term.strip():
            return False

        # 检查术语长度
        if len(term) > 50:  # 设置最大长度限制
            return False

        # 检查是否已存在
        if term in self.terms.get(lang, set()):
            return False

        # 检查特殊字符
        if lang == 'zh':
            # 中文术语只允许中文、数字和基本标点
            if not re.match(r'^[\u4e00-\u9fa5\d\s，。！？、]+$', term):
                return False
        else:
            # 英文术语只允许字母、数字和基本标点
            if not re.match(r'^[a-zA-Z\d\s\.,!?]+$', term):
                return False

        return True

    def import_terms(self, file_path: str) -> bool:
        """从文件导入术语"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            imported_terms = data.get('user_terms', {})
            for lang, terms in imported_terms.items():
                if lang not in self.terms:
                    self.terms[lang] = set()
                for term in terms:
                    if self.validate_term(term, lang):
                        self.terms[lang].add(term)

            self._save_to_file()
            return True
        except Exception as e:
            logger.error(f"导入术语失败: {e}")
            return False

    def export_terms(self, file_path: str) -> bool:
        """导出术语到文件"""
        try:
            data = {
                'user_terms': {lang: list(terms) for lang, terms in self.terms.items()},
                'term_stats': self.term_stats
            }
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"导出术语失败: {e}")
            return False

    def update_term_stats(self, term: str, lang: str):
        """更新术语使用统计"""
        if lang not in self.term_stats:
            self.term_stats[lang] = {}
        if term not in self.term_stats[lang]:
            self.term_stats[lang][term] = 0
        self.term_stats[lang][term] += 1
        self._save_to_file()

    def get_term_stats(self, lang: str) -> Dict[str, int]:
        """获取指定语言的术语使用统计"""
        return self.term_stats.get(lang, {})

    def get_most_used_terms(self, lang: str, limit: int = 10) -> List[str]:
        """获取最常用的术语"""
        stats = self.get_term_stats(lang)
        sorted_terms = sorted(stats.items(), key=lambda x: x[1], reverse=True)
        return [term for term, _ in sorted_terms[:limit]]
        
    def protect_terms_in_text(self, text: str, lang: str) -> str:
        """保护文本中的用户自定义术语，添加保护标记"""
        try:
            terms = sorted(self.get_terms(lang), key=len, reverse=True)
            for term in terms:
                if term in text:
                    # 使用标记包围术语
                    text = text.replace(term, f"[USERTERM]{term}[/USERTERM]")
                    # 更新使用统计
                    self.update_term_stats(term, lang)
            return text
        except Exception as e:
            logger.error(f"术语保护失败: {e}")
            return text
            
    def restore_terms_in_text(self, text: str) -> str:
        """移除术语保护标记，恢复原始术语"""
        try:
            # 移除保护标记但保留术语内容
            text = re.sub(r'\[USERTERM\](.*?)\[/USERTERM\]', r'\1', text)
            return text
        except Exception as e:
            logger.error(f"术语恢复失败: {e}")
            return text
            
    def apply_terms_protection(self, text: str) -> str:
        """应用术语保护处理流程
        
        1. 检测文本语言
        2. 保护用户术语
        3. 在文本处理后使用restore_terms_in_text恢复
        """
        # 简单语言检测
        lang = 'zh' if re.search(r'[\u4e00-\u9fff]', text) else 'en'
        return self.protect_terms_in_text(text, lang) 