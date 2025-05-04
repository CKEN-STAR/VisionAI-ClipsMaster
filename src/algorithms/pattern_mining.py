"""
模式挖掘工具

该模块提供从剧本数据中挖掘模式的功能
"""

import os
import logging
from typing import Dict, Any, List, Optional, Union, Set
from dataclasses import dataclass
from loguru import logger
import random
import math


class PatternMiner:
    """模式挖掘器，从剧本数据中挖掘模式"""
    
    def __init__(self):
        """初始化模式挖掘器"""
        logger.info("模式挖掘器初始化完成")
    
    def extract_patterns(self, scripts: List[Dict[str, Any]], min_support: float = 0.3) -> List[Dict[str, Any]]:
        """
        从多个剧本中提取共同模式
        
        Args:
            scripts: 剧本数据列表
            min_support: 最小支持度
            
        Returns:
            List[Dict]: 提取的模式列表
        """
        if not scripts:
            return []
        
        # 示例实现：生成一些随机模式
        patterns = []
        pattern_types = ["opening", "climax", "transition", "conflict", "resolution", "ending"]
        
        for pattern_type in pattern_types:
            # 每种类型生成1-3个模式
            for _ in range(random.randint(1, 3)):
                pattern = self._generate_sample_pattern(pattern_type)
                patterns.append(pattern)
        
        return patterns
    
    def _generate_sample_pattern(self, pattern_type: str) -> Dict[str, Any]:
        """生成示例模式"""
        import uuid
        pattern_id = f"{pattern_type}_{uuid.uuid4().hex[:8]}"
        
        # 根据模式类型设置参数
        if pattern_type == "opening":
            position = random.uniform(0.0, 0.15)
            duration = random.uniform(2.0, 8.0)
            frequency = random.uniform(0.7, 0.9)
            sentiment = random.uniform(0.1, 0.8)
        elif pattern_type == "climax":
            position = random.uniform(0.6, 0.8)
            duration = random.uniform(3.0, 10.0)
            frequency = random.uniform(0.6, 0.9)
            sentiment = random.uniform(-0.9, 0.9) * random.choice([-1, 1])
        elif pattern_type == "ending":
            position = random.uniform(0.85, 1.0)
            duration = random.uniform(2.0, 6.0)
            frequency = random.uniform(0.6, 0.85)
            sentiment = random.uniform(0.3, 0.8)
        elif pattern_type == "conflict":
            position = random.uniform(0.3, 0.5)
            duration = random.uniform(3.0, 8.0)
            frequency = random.uniform(0.5, 0.8)
            sentiment = random.uniform(-0.9, -0.3)
        else:
            position = random.uniform(0.2, 0.9)
            duration = random.uniform(1.0, 5.0)
            frequency = random.uniform(0.3, 0.7)
            sentiment = random.uniform(-0.5, 0.5)
        
        # 随机生成其他特征
        context_relevance = random.uniform(0.6, 0.9)
        conflict_level = random.uniform(0.3, 0.8) if pattern_type in ["conflict", "climax"] else random.uniform(0.1, 0.4)
        surprise_level = random.uniform(0.6, 0.9) if pattern_type in ["climax", "ending"] else random.uniform(0.3, 0.6)
        
        # 随机生成关键词
        keyword_pool = {
            "opening": ["开场", "引入", "设置", "开始", "吸引"],
            "climax": ["高潮", "震撼", "惊讶", "转折", "情感"],
            "transition": ["过渡", "切换", "转场", "变化", "连接"],
            "conflict": ["冲突", "对抗", "矛盾", "争执", "紧张"],
            "resolution": ["解决", "缓和", "和解", "释然", "答案"],
            "ending": ["结束", "收束", "解决", "完结", "结局"],
            "generic": ["重要", "关键", "核心", "精彩", "亮点"]
        }
        
        keywords = random.sample(keyword_pool.get(pattern_type, keyword_pool["generic"]), 
                             min(3, len(keyword_pool.get(pattern_type, keyword_pool["generic"]))))
        
        # 随机生成转场类型
        transition_types = ["cut", "dissolve", "fade", "wipe", "zoom", "flash"]
        transition = random.choice(transition_types)
        
        # 随机生成情感类型
        emotion_pool = {
            "positive": ["joy", "surprise", "anticipation"],
            "negative": ["anger", "sadness", "fear", "disgust"],
            "neutral": ["neutral"]
        }
        
        if sentiment > 0.3:
            emotion_category = "positive"
        elif sentiment < -0.3:
            emotion_category = "negative"
        else:
            emotion_category = "neutral"
        
        emotion_types = random.sample(emotion_pool[emotion_category], 
                                  min(2, len(emotion_pool[emotion_category])))
        
        # 创建模式
        pattern = {
            "id": pattern_id,
            "type": pattern_type,
            "description": f"{pattern_type.capitalize()}类型模式",
            "frequency": frequency,
            "position": position,
            "duration": duration,
            "transition": transition,
            "sentiment": sentiment,
            "keywords": keywords,
            "context_relevance": context_relevance,
            "conflict_level": conflict_level,
            "surprise_level": surprise_level,
            "emotion_types": emotion_types
        }
        
        return pattern
    
    def filter_patterns(self, patterns: List[Dict[str, Any]], 
                       min_frequency: float = 0.0, 
                       pattern_types: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        根据条件过滤模式
        
        Args:
            patterns: 待过滤的模式列表
            min_frequency: 最小频率
            pattern_types: 需要的模式类型
            
        Returns:
            过滤后的模式列表
        """
        filtered = []
        
        for pattern in patterns:
            # 检查频率
            if pattern.get("frequency", 0) < min_frequency:
                continue
                
            # 检查类型
            if pattern_types and pattern.get("type") not in pattern_types:
                continue
                
            filtered.append(pattern)
            
        return filtered
    
    def rank_patterns(self, patterns: List[Dict[str, Any]], 
                    ranking_field: str = "frequency") -> List[Dict[str, Any]]:
        """
        对模式按指定字段排序
        
        Args:
            patterns: 模式列表
            ranking_field: 排序字段
            
        Returns:
            排序后的模式列表
        """
        return sorted(patterns, key=lambda x: x.get(ranking_field, 0), reverse=True) 