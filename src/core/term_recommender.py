from typing import List, Dict
from loguru import logger
import jieba
import re
from collections import Counter

class TermRecommender:
    def __init__(self, term_manager):
        self.term_manager = term_manager
        
    def recommend_terms(self, context: str, lang: str) -> List[str]:
        """基于上下文推荐术语"""
        if lang == 'zh':
            return self._recommend_chinese_terms(context)
        else:
            return self._recommend_english_terms(context)
            
    def _recommend_chinese_terms(self, context: str) -> List[str]:
        """推荐中文术语"""
        # 分词
        words = list(jieba.cut(context))
        
        # 获取所有中文术语
        all_terms = self.term_manager.get_terms('zh')
        if not all_terms:
            return []
            
        # 计算术语使用频率
        term_stats = self.term_manager.get_term_stats('zh')
        
        # 计算每个术语与上下文的相似度
        term_scores = []
        for term in all_terms:
            # 计算术语在上下文中的出现次数
            term_words = list(jieba.cut(term))
            matches = sum(1 for word in term_words if word in words)
            
            # 计算相似度分数
            similarity = matches / len(term_words) if term_words else 0
            
            # 考虑使用频率
            frequency = term_stats.get(term, 0)
            
            # 综合分数
            score = similarity * 0.7 + (frequency / (frequency + 1)) * 0.3
            term_scores.append((term, score))
            
        # 按分数排序并返回前10个
        term_scores.sort(key=lambda x: x[1], reverse=True)
        return [term for term, _ in term_scores[:10]]
        
    def _recommend_english_terms(self, context: str) -> List[str]:
        """推荐英文术语"""
        # 分词
        words = re.findall(r'\b\w+\b', context.lower())
        
        # 获取所有英文术语
        all_terms = self.term_manager.get_terms('en')
        if not all_terms:
            return []
            
        # 计算术语使用频率
        term_stats = self.term_manager.get_term_stats('en')
        
        # 计算每个术语与上下文的相似度
        term_scores = []
        for term in all_terms:
            # 计算术语在上下文中的出现次数
            term_words = re.findall(r'\b\w+\b', term.lower())
            matches = sum(1 for word in term_words if word in words)
            
            # 计算相似度分数
            similarity = matches / len(term_words) if term_words else 0
            
            # 考虑使用频率
            frequency = term_stats.get(term, 0)
            
            # 综合分数
            score = similarity * 0.7 + (frequency / (frequency + 1)) * 0.3
            term_scores.append((term, score))
            
        # 按分数排序并返回前10个
        term_scores.sort(key=lambda x: x[1], reverse=True)
        return [term for term, _ in term_scores[:10]]
        
    def update_term_usage(self, term: str, lang: str):
        """更新术语使用情况"""
        self.term_manager.update_term_stats(term, lang)
        
    def get_most_used_terms(self, lang: str, limit: int = 10) -> List[str]:
        """获取最常用的术语"""
        return self.term_manager.get_most_used_terms(lang, limit) 