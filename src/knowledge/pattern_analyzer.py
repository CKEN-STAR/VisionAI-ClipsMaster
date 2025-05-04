"""
模式分析器模块

负责分析和提取视频脚本中的模式特征和结构
"""

import os
import logging
from typing import Dict, Any, List, Optional, Union, Set
from dataclasses import dataclass
from loguru import logger
import math
import random

@dataclass
class PatternElement:
    """模式元素数据类"""
    # 元素ID
    id: str
    # 元素类型
    type: str
    # 元素文本
    text: str
    # 元素开始时间
    start_time: float
    # 元素结束时间
    end_time: float
    # 情感值
    sentiment: float
    # 相关关键词
    keywords: List[str]


class PatternAnalyzer:
    """模式分析器，用于分析视频脚本中的模式"""
    
    def __init__(self):
        """初始化模式分析器"""
        logger.info("模式分析器初始化")
        # 后续可添加模型加载
    
    def extract_patterns(self, segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        从字幕段落中提取模式
        
        Args:
            segments: 字幕段落列表
            
        Returns:
            List[Dict]: 提取的模式列表
        """
        if not segments:
            return []
        
        # 示例实现：提取简单模式
        patterns = []
        
        # 检测开场模式
        if len(segments) >= 2:
            opening_segments = segments[:2]
            opening_pattern = self._create_pattern(
                "opening",
                opening_segments,
                0.05,  # 相对位置
                "开场引入场景"
            )
            patterns.append(opening_pattern)
        
        # 检测高潮模式
        if len(segments) >= 5:
            # 假设高潮在中后部
            climax_start = max(2, len(segments) // 2)
            climax_end = min(climax_start + 2, len(segments))
            climax_segments = segments[climax_start:climax_end]
            
            climax_pattern = self._create_pattern(
                "climax",
                climax_segments,
                0.7,  # 相对位置
                "情感高潮场景"
            )
            patterns.append(climax_pattern)
        
        # 检测结尾模式
        if len(segments) >= 3:
            ending_segments = segments[-2:]
            ending_pattern = self._create_pattern(
                "ending",
                ending_segments,
                0.95,  # 相对位置
                "结尾收束场景"
            )
            patterns.append(ending_pattern)
        
        # 检测冲突模式
        if len(segments) >= 7:
            conflict_start = len(segments) // 3
            conflict_segments = segments[conflict_start:conflict_start+2]
            conflict_pattern = self._create_pattern(
                "conflict",
                conflict_segments,
                0.4,  # 相对位置
                "冲突转折场景"
            )
            patterns.append(conflict_pattern)
        
        # 随机添加一些转场模式
        if len(segments) >= 8:
            transition_indices = [i for i in range(2, len(segments)-3, 2)]
            if transition_indices:
                transition_idx = random.choice(transition_indices)
                transition_segments = segments[transition_idx:transition_idx+1]
                position = transition_idx / len(segments)
                
                transition_pattern = self._create_pattern(
                    "transition",
                    transition_segments,
                    position,
                    "过渡转场场景"
                )
                patterns.append(transition_pattern)
        
        return patterns
    
    def _create_pattern(self, 
                      pattern_type: str, 
                      segments: List[Dict[str, Any]],
                      position: float,
                      description: str) -> Dict[str, Any]:
        """
        根据段落创建模式
        
        Args:
            pattern_type: 模式类型
            segments: 段落列表
            position: 模式在视频中的相对位置
            description: 模式描述
            
        Returns:
            Dict: 模式数据
        """
        # 生成随机ID
        import uuid
        pattern_id = f"{pattern_type}_{uuid.uuid4().hex[:8]}"
        
        # 提取文本
        texts = [seg.get("text", "") for seg in segments]
        joined_text = " ".join(texts)
        
        # 计算持续时间
        try:
            start_time = min(seg.get("time", {}).get("start", 0) for seg in segments)
            end_time = max(seg.get("time", {}).get("end", 0) for seg in segments)
            duration = end_time - start_time
        except:
            duration = 3.0  # 默认值
        
        # 随机生成情感值
        if pattern_type == "climax":
            sentiment = random.uniform(0.6, 0.9) * random.choice([-1, 1])
        elif pattern_type == "conflict":
            sentiment = random.uniform(-0.9, -0.5)
        elif pattern_type == "ending":
            sentiment = random.uniform(0.3, 0.8)
        else:
            sentiment = random.uniform(-0.5, 0.5)
        
        # 随机生成其他特征
        frequency = random.uniform(0.5, 0.9)
        context_relevance = random.uniform(0.6, 0.9)
        conflict_level = random.uniform(0.3, 0.8) if pattern_type in ["conflict", "climax"] else random.uniform(0.1, 0.4)
        surprise_level = random.uniform(0.6, 0.9) if pattern_type in ["climax", "ending"] else random.uniform(0.3, 0.6)
        
        # 随机生成关键词
        keyword_pool = {
            "opening": ["开场", "引入", "设置", "开始", "吸引"],
            "climax": ["高潮", "震撼", "惊讶", "转折", "情感"],
            "transition": ["过渡", "切换", "转场", "变化", "连接"],
            "conflict": ["冲突", "对抗", "矛盾", "争执", "紧张"],
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
            "description": description,
            "text": joined_text[:100] + "..." if len(joined_text) > 100 else joined_text,
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
    
    def analyze_pattern_features(self, pattern: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析模式特征
        
        Args:
            pattern: 模式数据
            
        Returns:
            Dict: 特征分析结果
        """
        # 示例实现：返回简单的特征分析
        pattern_type = pattern.get("type", "unknown")
        position = pattern.get("position", 0)
        sentiment = pattern.get("sentiment", 0)
        
        analysis = {
            "type_effectiveness": self._analyze_type_position(pattern_type, position),
            "emotional_impact": self._analyze_emotion(pattern_type, sentiment),
            "suitable_content_types": self._get_suitable_content_types(pattern_type)
        }
        
        return analysis
    
    def _analyze_type_position(self, pattern_type: str, position: float) -> Dict[str, Any]:
        """分析模式类型和位置的有效性"""
        ideal_positions = {
            "opening": 0.0,
            "conflict": 0.4,
            "transition": 0.5,
            "climax": 0.7,
            "resolution": 0.8,
            "ending": 0.95
        }
        
        ideal = ideal_positions.get(pattern_type, 0.5)
        deviation = abs(position - ideal)
        
        effectiveness = max(0, 1 - deviation * 2)
        
        return {
            "ideal_position": ideal,
            "actual_position": position,
            "position_deviation": deviation,
            "effectiveness": effectiveness
        }
    
    def _analyze_emotion(self, pattern_type: str, sentiment: float) -> Dict[str, Any]:
        """分析情感影响力"""
        expected_sentiment = {
            "opening": 0.3,  # 开场一般略微积极
            "conflict": -0.7,  # 冲突通常负面
            "transition": 0.0,  # 转场通常中性
            "climax": 0.8,  # 高潮通常强烈情感（正面）
            "resolution": 0.5,  # 解决通常正面
            "ending": 0.4  # 结尾通常正面
        }
        
        expected = expected_sentiment.get(pattern_type, 0)
        is_negative_expected = pattern_type in ["conflict"]
        
        if is_negative_expected:
            match_level = max(0, min(1, (sentiment * -1 + 1) / 2))
        else:
            sentiment_distance = abs(sentiment - expected)
            match_level = max(0, 1 - sentiment_distance)
        
        # 情感强度
        intensity = abs(sentiment)
        
        return {
            "expected_sentiment": expected,
            "actual_sentiment": sentiment,
            "intensity": intensity,
            "match_level": match_level
        }
    
    def _get_suitable_content_types(self, pattern_type: str) -> List[str]:
        """获取适合该模式的内容类型"""
        content_types = {
            "opening": ["剧情短剧", "悬疑短剧", "励志短剧", "搞笑短剧"],
            "conflict": ["剧情短剧", "悬疑短剧", "情感短剧"],
            "transition": ["剧情短剧", "纪录片", "生活记录"],
            "climax": ["剧情短剧", "悬疑短剧", "励志短剧", "情感短剧"],
            "resolution": ["剧情短剧", "励志短剧", "情感短剧"],
            "ending": ["剧情短剧", "励志短剧", "搞笑短剧", "情感短剧"]
        }
        
        return content_types.get(pattern_type, ["通用内容"]) 