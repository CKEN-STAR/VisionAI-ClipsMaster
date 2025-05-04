#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
情感词汇强化器

对文本中的情感词汇进行强化和替换，调整情感表达的强度。
用于增强或减弱视频混剪中的情感表达效果。
"""

import os
import re
import json
import math
import yaml
import random
import jieba
from typing import Dict, List, Tuple, Any, Optional, Union, Set
from loguru import logger

# 默认配置路径
DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                  "configs", "emotion_lexicon.yaml")
DEFAULT_LEXICON_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                   "configs", "sentiment_lexicon.json")

class EmotionLexicon:
    """情感词汇管理和强化类"""
    
    def __init__(self, config_path: Optional[str] = None, 
                lexicon_path: Optional[str] = None):
        """
        初始化情感词汇强化器
        
        Args:
            config_path: 配置文件路径，如不提供则使用默认路径
            lexicon_path: 情感词典文件路径，如不提供则使用默认路径
        """
        # 加载情感词典
        self.lexicon = self._load_lexicon(lexicon_path or DEFAULT_LEXICON_PATH)
        
        # 加载配置
        self.config = self._load_config(config_path or DEFAULT_CONFIG_PATH)
        
        # 替换词典初始化
        self.replacements = self._init_replacements()
        
        # 情感词强度映射表初始化
        self.intensity_map = self._build_intensity_map()
        
        # 加载同义词表
        self.synonyms = self._load_synonyms()
        
        # 日志记录
        logger.info("情感词汇强化器初始化完成")
    
    def _load_lexicon(self, lexicon_path: str) -> Dict[str, float]:
        """
        加载情感词典
        
        Args:
            lexicon_path: 情感词典文件路径
            
        Returns:
            情感词典，键为词汇，值为情感强度得分
        """
        try:
            if os.path.exists(lexicon_path):
                with open(lexicon_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                logger.warning(f"情感词典文件不存在: {lexicon_path}，使用默认词典")
                return self._default_lexicon()
        except Exception as e:
            logger.warning(f"加载情感词典失败: {e}，使用默认词典")
            return self._default_lexicon()
    
    def _default_lexicon(self) -> Dict[str, float]:
        """返回默认情感词典"""
        return {
            # 积极情感词
            "开心": 0.8, "快乐": 0.8, "高兴": 0.7, "兴奋": 0.9,
            "愉快": 0.7, "幸福": 0.9, "满意": 0.6, "喜欢": 0.7,
            "爱": 0.9, "赞": 0.7, "好": 0.6, "棒": 0.7,
            
            # 消极情感词
            "伤心": -0.8, "难过": -0.7, "悲伤": -0.8, "痛苦": -0.9,
            "失望": -0.7, "沮丧": -0.7, "忧郁": -0.7, "生气": -0.7,
            "愤怒": -0.8, "讨厌": -0.7, "恨": -0.9, "厌恶": -0.8
        }
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """
        加载配置文件
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            配置字典
        """
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f)
            else:
                logger.warning(f"配置文件不存在: {config_path}，使用默认配置")
                return self._default_config()
        except Exception as e:
            logger.warning(f"加载配置文件失败: {e}，使用默认配置")
            return self._default_config()
    
    def _default_config(self) -> Dict[str, Any]:
        """返回默认配置"""
        return {
            "lexicon_enhancer": {
                "intensify_factor": 1.3,  # 强化因子
                "reduce_factor": 0.7,     # 减弱因子
                "smart_replacement": True,  # 智能替换
                "context_aware": True,      # 上下文感知
                "use_synonyms": True,     # 使用同义词
                "max_replacements": 3,    # 每句最大替换次数
                "min_confidence": 0.7     # 最小替换置信度
            }
        }
    
    def _init_replacements(self) -> Dict[str, List[Tuple[str, float]]]:
        """
        初始化替换词典
        
        Returns:
            替换词典，键为原词，值为(替换词, 强度)的列表
        """
        # 根据现有词典构建替换表
        replacements = {
            # 基本高兴情绪替换
            "高兴": [("开心", 0.8), ("兴奋", 0.95)],
            "生气": [("愤怒", 0.9), ("恼火", 0.8)],
            "难过": [("伤心", 0.8), ("悲痛", 0.95)],
            "好": [("棒", 0.75), ("优秀", 0.85), ("出色", 0.9)],
            "喜欢": [("爱", 0.9), ("热爱", 0.95)],
            
            # 增强版本的情感替换
            "开心": [("欣喜若狂", 0.95), ("喜不自胜", 0.9)],
            "兴奋": [("激动不已", 0.95), ("热血沸腾", 0.9)],
            "愉快": [("心花怒放", 0.9), ("欣喜若狂", 0.95)],
            "满意": [("心满意足", 0.85), ("十分满意", 0.8)],
            "喜欢": [("钟爱", 0.85), ("痴迷", 0.9)],
            
            # 更多情感词替换...可根据需要扩展
        }
        
        # 添加配置中的自定义替换
        custom_replacements = self.config.get("lexicon_enhancer", {}).get("replacements", {})
        for word, replacements_list in custom_replacements.items():
            replacements[word] = [(r["word"], r["intensity"]) for r in replacements_list]
        
        return replacements
    
    def _build_intensity_map(self) -> Dict[str, float]:
        """
        构建情感词强度映射表
        
        Returns:
            情感词强度映射表
        """
        # 合并词典和替换表中的所有词汇
        intensity_map = self.lexicon.copy()
        
        # 添加替换词典中的词汇强度
        for word, replacements_list in self.replacements.items():
            for replacement, intensity in replacements_list:
                if replacement not in intensity_map:
                    # 使用替换强度或原词强度
                    base_intensity = self.lexicon.get(word, 0.5)
                    intensity_map[replacement] = base_intensity * intensity
        
        return intensity_map
    
    def _load_synonyms(self) -> Dict[str, List[str]]:
        """
        加载同义词表
        
        Returns:
            同义词字典
        """
        # 获取配置中的同义词表路径
        synonyms_path = self.config.get("lexicon_enhancer", {}).get("synonyms_path", "")
        
        if synonyms_path and os.path.exists(synonyms_path):
            try:
                with open(synonyms_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"加载同义词表失败: {e}，使用默认同义词表")
        
        # 使用简单的默认同义词表
        return {
            "开心": ["高兴", "快乐", "愉快", "欢喜"],
            "伤心": ["难过", "悲伤", "哀伤", "忧伤"],
            "生气": ["愤怒", "恼火", "火大", "暴怒"],
            "喜欢": ["爱", "钟爱", "喜爱", "热爱"],
            # 更多同义词...可根据需要扩展
        }
    
    def intensify(self, text: str, factor: float = None) -> str:
        """
        增强文本的情感强度
        
        Args:
            text: 输入文本
            factor: 强化因子，如不提供则使用配置值
            
        Returns:
            情感强化后的文本
        """
        if not text:
            return text
        
        # 使用配置的强化因子或默认值
        if factor is None:
            factor = self.config.get("lexicon_enhancer", {}).get("intensify_factor", 1.3)
        
        # 分词处理文本
        words = list(jieba.cut(text))
        
        # 替换计数
        replacements_made = 0
        max_replacements = self.config.get("lexicon_enhancer", {}).get("max_replacements", 3)
        
        # 处理每个词
        for i, word in enumerate(words):
            # 检查是否达到最大替换次数
            if replacements_made >= max_replacements:
                break
                
            # 查找替换词
            if word in self.replacements:
                # 获取可能的替换词列表
                candidates = self.replacements[word]
                
                # 根据因子选择合适的替换词
                current_intensity = self.lexicon.get(word, 0.5)
                target_intensity = min(1.0, current_intensity * factor)
                
                # 找到最接近目标强度的替换词
                selected = self._find_best_replacement(candidates, target_intensity)
                
                # 进行替换
                if selected:
                    words[i] = selected
                    replacements_made += 1
        
        # 重新组合文本
        return ''.join(words)
    
    def reduce(self, text: str, factor: float = None) -> str:
        """
        降低文本的情感强度
        
        Args:
            text: 输入文本
            factor: 减弱因子，如不提供则使用配置值
            
        Returns:
            情感减弱后的文本
        """
        if not text:
            return text
        
        # 使用配置的减弱因子或默认值
        if factor is None:
            factor = self.config.get("lexicon_enhancer", {}).get("reduce_factor", 0.7)
        
        # 分词处理文本
        words = list(jieba.cut(text))
        
        # 替换计数
        replacements_made = 0
        max_replacements = self.config.get("lexicon_enhancer", {}).get("max_replacements", 3)
        
        # 处理每个词
        for i, word in enumerate(words):
            # 检查是否达到最大替换次数
            if replacements_made >= max_replacements:
                break
                
            # 查找替换词
            if word in self.replacements:
                # 获取可能的替换词列表
                candidates = self.replacements[word]
                
                # 根据因子选择合适的替换词
                current_intensity = self.lexicon.get(word, 0.5)
                target_intensity = max(0.0, current_intensity * factor)
                
                # 找到最接近目标强度的替换词
                selected = self._find_best_replacement(candidates, target_intensity)
                
                # 进行替换
                if selected:
                    words[i] = selected
                    replacements_made += 1
        
        # 重新组合文本
        return ''.join(words)
    
    def adjust_to_level(self, text: str, target_level: float) -> str:
        """
        将文本情感调整到目标级别
        
        Args:
            text: 输入文本
            target_level: 目标情感级别 (0.0-1.0)
            
        Returns:
            情感调整后的文本
        """
        if not text:
            return text
        
        # 检查目标级别有效性
        target_level = max(0.0, min(1.0, target_level))
        
        # 分词处理文本
        words = list(jieba.cut(text))
        
        # 替换计数
        replacements_made = 0
        max_replacements = self.config.get("lexicon_enhancer", {}).get("max_replacements", 3)
        
        # 处理每个词
        for i, word in enumerate(words):
            # 检查是否达到最大替换次数
            if replacements_made >= max_replacements:
                break
                
            # 检查是否为情感词
            if word in self.lexicon:
                # 获取当前情感强度
                current_intensity = abs(self.lexicon[word])
                
                # 如果当前强度与目标差异较大，进行替换
                if abs(current_intensity - target_level) > 0.2:
                    # 查找替换词或同义词
                    replacement = self._find_word_with_intensity(word, target_level)
                    
                    # 进行替换
                    if replacement:
                        words[i] = replacement
                        replacements_made += 1
        
        # 重新组合文本
        return ''.join(words)
    
    def _find_best_replacement(self, candidates: List[Tuple[str, float]], 
                              target_intensity: float) -> Optional[str]:
        """
        从候选词中找到最接近目标强度的替换词
        
        Args:
            candidates: 候选词列表，每项为(词, 强度)
            target_intensity: 目标强度
            
        Returns:
            最佳替换词，如无合适词则返回None
        """
        if not candidates:
            return None
        
        # 最小置信度
        min_confidence = self.config.get("lexicon_enhancer", {}).get("min_confidence", 0.7)
        
        # 按与目标强度差异排序
        sorted_candidates = sorted(candidates, 
                                 key=lambda x: abs(x[1] - target_intensity))
        
        # 计算置信度 - 与目标的接近程度
        confidence = 1.0 - abs(sorted_candidates[0][1] - target_intensity)
        
        # 如果置信度高于阈值，返回最佳候选词
        if confidence >= min_confidence:
            return sorted_candidates[0][0]
        
        return None
    
    def _find_word_with_intensity(self, word: str, target_intensity: float) -> Optional[str]:
        """
        查找指定强度的替换词或同义词
        
        Args:
            word: 原词
            target_intensity: 目标强度
            
        Returns:
            合适的替换词，如无合适词则返回None
        """
        candidates = []
        
        # 先查找替换词
        if word in self.replacements:
            candidates.extend(self.replacements[word])
        
        # 再查找同义词
        if self.config.get("lexicon_enhancer", {}).get("use_synonyms", True) and word in self.synonyms:
            for synonym in self.synonyms[word]:
                if synonym in self.lexicon:
                    intensity = abs(self.lexicon[synonym])
                    candidates.append((synonym, intensity))
        
        # 从候选词中找到最佳替换词
        return self._find_best_replacement(candidates, target_intensity)


def intensify_text(text: str, factor: float = 1.3) -> str:
    """
    增强文本情感的便捷函数
    
    Args:
        text: 输入文本
        factor: 强化因子
        
    Returns:
        情感增强后的文本
    """
    enhancer = EmotionLexicon()
    return enhancer.intensify(text, factor)


def reduce_emotion(text: str, factor: float = 0.7) -> str:
    """
    减弱文本情感的便捷函数
    
    Args:
        text: 输入文本
        factor: 减弱因子
        
    Returns:
        情感减弱后的文本
    """
    enhancer = EmotionLexicon()
    return enhancer.reduce(text, factor)


def adjust_emotion_level(text: str, target_level: float) -> str:
    """
    调整文本情感到目标级别的便捷函数
    
    Args:
        text: 输入文本
        target_level: 目标情感级别 (0.0-1.0)
        
    Returns:
        情感调整后的文本
    """
    enhancer = EmotionLexicon()
    return enhancer.adjust_to_level(text, target_level) 