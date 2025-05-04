#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
动态内容变形器模块

根据用户偏好对内容进行智能调整和变形，使内容更符合用户的喜好和体验期望。
支持情感增强、节奏调整和文化本地化等多种变形策略。
"""

import os
import copy
import json
import logging
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union, Callable

from loguru import logger
from src.utils.log_handler import get_logger
from src.emotion.rhythm_tuner import process_scene_sequence, adjust_pacing
from src.emotion.intensity_mapper import EmotionMapper, amplify_emotion
from src.adaptation.culture_adapter import CultureAdapter

# 配置日志
morpher_logger = get_logger("content_morpher")

class ContentMorpher:
    """
    动态内容变形器
    
    基于用户偏好对内容进行智能调整和变形，使内容更符合用户的喜好和体验预期。
    提供多种变形策略，包括情感增强、节奏调整和文化本地化等。
    """
    
    # 变形策略映射
    MORPH_STRATEGIES = {
        "情感极化": lambda x, factor=1.5: amplify_emotion(x, factor),
        "节奏适配": lambda x, target_bpm=120: adjust_pacing(x, target_bpm=target_bpm),
        "文化本地化": lambda x, source_lang="zh", target_lang="en": replace_cultural_references(x, source_lang, target_lang)
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化内容变形器
        
        Args:
            config_path: 配置文件路径，如果为None则使用默认配置
        """
        # 加载配置
        self.config = self._load_config(config_path)
        
        # 初始化相关组件
        self.emotion_mapper = EmotionMapper()
        self.culture_adapter = CultureAdapter()
        
        # 扩展变形策略
        self._initialize_strategies()
        
        morpher_logger.info("内容变形器初始化完成")
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """
        加载配置文件
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            配置字典
        """
        default_config = {
            "default_strategies": {
                "情感极化": {
                    "enabled": True,
                    "default_factor": 1.5,
                    "min_factor": 1.1,
                    "max_factor": 2.0
                },
                "节奏适配": {
                    "enabled": True,
                    "default_bpm": 120,
                    "min_bpm": 60,
                    "max_bpm": 180
                },
                "文化本地化": {
                    "enabled": True,
                    "default_source": "zh",
                    "default_target": "en"
                }
            },
            "threshold": {
                "strategy_application": 0.5,  # 策略应用阈值
                "emotion_filter": 0.3         # 情感过滤阈值
            }
        }
        
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                return config
            except Exception as e:
                morpher_logger.error(f"加载配置文件失败: {str(e)}")
                
        return default_config
    
    def _initialize_strategies(self):
        """
        初始化和扩展变形策略
        """
        # 扩展情感极化策略
        self.MORPH_STRATEGIES.update({
            "悲伤强化": lambda x, factor=1.3: self._amplify_specific_emotion(x, "悲伤", factor),
            "喜悦强化": lambda x, factor=1.4: self._amplify_specific_emotion(x, "喜悦", factor),
            "紧张强化": lambda x, factor=1.6: self._amplify_specific_emotion(x, "紧张", factor),
        })
        
        # 扩展节奏适配策略
        self.MORPH_STRATEGIES.update({
            "快节奏": lambda x: adjust_pacing(x, target_bpm=150),
            "中节奏": lambda x: adjust_pacing(x, target_bpm=120),
            "慢节奏": lambda x: adjust_pacing(x, target_bpm=80),
        })
        
        # 扩展文化本地化策略
        self.MORPH_STRATEGIES.update({
            "中国化": lambda x: replace_cultural_references(x, "en", "zh"),
            "西方化": lambda x: replace_cultural_references(x, "zh", "en"),
        })
    
    def morph_content(self, content: Dict[str, Any], strategy_weights: Dict[str, float]) -> Dict[str, Any]:
        """
        根据策略权重混合应用变形策略
        
        Args:
            content: 原始内容
            strategy_weights: 策略权重字典，格式为 {策略名: 权重值}
            
        Returns:
            变形后的内容
        """
        morpher_logger.info("开始应用内容变形策略")
        
        # 创建内容副本，避免修改原始内容
        morphed = copy.deepcopy(content)
        
        # 应用策略
        for strategy, weight in strategy_weights.items():
            # 检查权重是否超过阈值
            if weight > self.config["threshold"]["strategy_application"]:
                morpher_logger.debug(f"应用策略 '{strategy}', 权重: {weight}")
                
                # 检查策略是否存在
                if strategy in self.MORPH_STRATEGIES:
                    # 应用变形策略
                    morphed = self.MORPH_STRATEGIES[strategy](morphed)
                else:
                    morpher_logger.warning(f"未找到策略 '{strategy}'")
        
        morpher_logger.info("内容变形完成")
        return morphed
    
    def _amplify_specific_emotion(self, content: Dict[str, Any], emotion_type: str, factor: float) -> Dict[str, Any]:
        """
        增强特定类型的情感
        
        Args:
            content: 内容数据
            emotion_type: 情感类型
            factor: 增强因子
            
        Returns:
            情感增强后的内容
        """
        # 检查内容是否包含情感数据
        if "emotions" not in content or not isinstance(content["emotions"], list):
            return content
        
        # 创建内容副本
        result = copy.deepcopy(content)
        
        # 遍历情感数据
        for i, emotion_data in enumerate(result["emotions"]):
            if isinstance(emotion_data, dict) and "type" in emotion_data:
                # 如果匹配目标情感类型，则增强强度
                if emotion_data["type"] == emotion_type:
                    # 增强情感强度
                    if "intensity" in emotion_data:
                        emotion_data["intensity"] = min(1.0, emotion_data["intensity"] * factor)
                    
                    # 增强情感分数
                    if "score" in emotion_data:
                        emotion_data["score"] = min(1.0, emotion_data["score"] * factor)
        
        return result
    
    def apply_user_preferences(self, content: Dict[str, Any], user_preferences: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据用户偏好自动选择和应用变形策略
        
        Args:
            content: 原始内容
            user_preferences: 用户偏好数据
            
        Returns:
            根据用户偏好变形后的内容
        """
        morpher_logger.info("根据用户偏好应用变形策略")
        
        # 解析用户偏好，转换为策略权重
        strategy_weights = self._preferences_to_strategies(user_preferences)
        
        # 应用变形策略
        morphed_content = self.morph_content(content, strategy_weights)
        
        return morphed_content
    
    def _preferences_to_strategies(self, preferences: Dict[str, Any]) -> Dict[str, float]:
        """
        将用户偏好转换为策略权重
        
        Args:
            preferences: 用户偏好数据
            
        Returns:
            策略权重字典
        """
        strategy_weights = {}
        
        # 处理情感偏好
        emotion_prefs = preferences.get("emotion_preferences", {})
        if emotion_prefs:
            # 情感强度偏好
            intensity = emotion_prefs.get("intensity", 0.5)
            if intensity > 0.7:
                strategy_weights["情感极化"] = min(1.0, intensity * 1.2)
            
            # 特定情感偏好
            primary_emotions = emotion_prefs.get("primary_emotions", {})
            for emotion, data in primary_emotions.items():
                if isinstance(data, dict) and data.get("score", 0) > 0.7:
                    if emotion == "joy" or emotion == "喜悦":
                        strategy_weights["喜悦强化"] = min(1.0, data.get("score", 0.7) * 1.1)
                    elif emotion == "sadness" or emotion == "悲伤":
                        strategy_weights["悲伤强化"] = min(1.0, data.get("score", 0.7) * 1.1)
                    elif emotion == "tension" or emotion == "紧张":
                        strategy_weights["紧张强化"] = min(1.0, data.get("score", 0.7) * 1.1)
        
        # 处理节奏偏好
        pacing_prefs = preferences.get("pacing_preferences", {})
        if pacing_prefs:
            # 节奏速度偏好
            overall_pace = pacing_prefs.get("overall_pace", {})
            
            # 检查各种节奏的偏好程度
            fast_score = overall_pace.get("fast", {}).get("score", 0) if isinstance(overall_pace.get("fast"), dict) else 0
            medium_score = overall_pace.get("medium", {}).get("score", 0) if isinstance(overall_pace.get("medium"), dict) else 0
            slow_score = overall_pace.get("slow", {}).get("score", 0) if isinstance(overall_pace.get("slow"), dict) else 0
            
            # 选择得分最高的节奏
            if fast_score > medium_score and fast_score > slow_score and fast_score > 0.6:
                strategy_weights["快节奏"] = min(1.0, fast_score * 1.2)
            elif medium_score > fast_score and medium_score > slow_score and medium_score > 0.6:
                strategy_weights["中节奏"] = min(1.0, medium_score * 1.2)
            elif slow_score > fast_score and slow_score > medium_score and slow_score > 0.6:
                strategy_weights["慢节奏"] = min(1.0, slow_score * 1.2)
            else:
                # 默认使用中等节奏
                strategy_weights["节奏适配"] = 0.7
        
        # 处理文化偏好
        basic_info = preferences.get("basic_info", {})
        if basic_info:
            region = basic_info.get("region", "").lower()
            if region in ["us", "uk", "europe", "north_america", "australia"]:
                strategy_weights["西方化"] = 0.8
            elif region in ["china", "asia", "east", "southeast_asia"]:
                strategy_weights["中国化"] = 0.8
        
        return strategy_weights


# 辅助函数

def amplify_emotion(content: Dict[str, Any], factor: float = 1.5) -> Dict[str, Any]:
    """
    增强内容的情感强度
    
    Args:
        content: 内容数据
        factor: 情感增强因子
        
    Returns:
        情感增强后的内容
    """
    result = copy.deepcopy(content)
    
    # 处理情感数据
    if "emotions" in result and isinstance(result["emotions"], list):
        for emotion in result["emotions"]:
            if isinstance(emotion, dict):
                # 增强情感强度
                if "intensity" in emotion:
                    emotion["intensity"] = min(1.0, emotion["intensity"] * factor)
                
                # 增强情感分数
                if "score" in emotion:
                    emotion["score"] = min(1.0, emotion["score"] * factor)
    
    # 处理场景数据
    if "scenes" in result and isinstance(result["scenes"], list):
        for scene in result["scenes"]:
            if isinstance(scene, dict) and "emotion" in scene:
                # 增强场景情感强度
                if isinstance(scene["emotion"], dict):
                    if "intensity" in scene["emotion"]:
                        scene["emotion"]["intensity"] = min(1.0, scene["emotion"]["intensity"] * factor)
                    
                    if "score" in scene["emotion"]:
                        scene["emotion"]["score"] = min(1.0, scene["emotion"]["score"] * factor)
    
    return result


def adjust_pacing(content: Dict[str, Any], target_bpm: int = 120) -> Dict[str, Any]:
    """
    调整内容的节奏
    
    Args:
        content: 内容数据
        target_bpm: 目标每分钟节拍数
        
    Returns:
        节奏调整后的内容
    """
    result = copy.deepcopy(content)
    
    # 处理场景数据
    if "scenes" in result and isinstance(result["scenes"], list):
        # 计算当前的平均BPM
        current_bpm = _calculate_content_bpm(result["scenes"])
        
        # 计算调整因子
        adjustment_factor = target_bpm / max(1, current_bpm)
        
        # 调整场景持续时间
        for scene in result["scenes"]:
            if isinstance(scene, dict) and "duration" in scene:
                # 应用节奏调整
                scene["adjusted_duration"] = scene["duration"] / adjustment_factor
                scene["pacing_adjustment"] = {
                    "original_duration": scene["duration"],
                    "target_bpm": target_bpm,
                    "current_bpm": current_bpm,
                    "adjustment_factor": adjustment_factor
                }
    
    return result


def _calculate_content_bpm(scenes: List[Dict[str, Any]]) -> float:
    """
    计算内容的每分钟节拍数
    
    Args:
        scenes: 场景列表
        
    Returns:
        每分钟节拍数
    """
    if not scenes:
        return 120  # 默认BPM
    
    # 计算场景切换频率
    total_duration = sum(scene.get("duration", 0) for scene in scenes if isinstance(scene, dict))
    scene_count = len(scenes)
    
    if total_duration <= 0:
        return 120  # 默认BPM
    
    # 每分钟场景数作为节拍的近似值
    return (scene_count / total_duration) * 60


def replace_cultural_references(content: Dict[str, Any], source_lang: str = "zh", target_lang: str = "en") -> Dict[str, Any]:
    """
    替换内容中的文化引用
    
    Args:
        content: 内容数据
        source_lang: 源语言
        target_lang: 目标语言
        
    Returns:
        文化本地化后的内容
    """
    result = copy.deepcopy(content)
    
    # 初始化文化适配器
    adapter = CultureAdapter()
    
    # 处理对话数据
    if "dialogues" in result and isinstance(result["dialogues"], list):
        for dialogue in result["dialogues"]:
            if isinstance(dialogue, dict) and "text" in dialogue:
                # 本地化文化引用
                dialogue["text"] = adapter.localize_cultural_references(
                    dialogue["text"], source_lang, target_lang
                )
    
    # 处理叙述数据
    if "narration" in result and isinstance(result["narration"], list):
        for narration in result["narration"]:
            if isinstance(narration, dict) and "text" in narration:
                # 本地化文化引用
                narration["text"] = adapter.localize_cultural_references(
                    narration["text"], source_lang, target_lang
                )
    
    # 处理标题和描述
    if "title" in result and isinstance(result["title"], str):
        result["title"] = adapter.localize_cultural_references(
            result["title"], source_lang, target_lang
        )
    
    if "description" in result and isinstance(result["description"], str):
        result["description"] = adapter.localize_cultural_references(
            result["description"], source_lang, target_lang
        )
    
    return result


# 获取内容变形器实例
_content_morpher_instance = None

def get_content_morpher() -> ContentMorpher:
    """
    获取内容变形器单例实例
    
    Returns:
        ContentMorpher: 内容变形器实例
    """
    global _content_morpher_instance
    if _content_morpher_instance is None:
        _content_morpher_instance = ContentMorpher()
    return _content_morpher_instance


def morph_content(content: Dict[str, Any], strategy_weights: Dict[str, float]) -> Dict[str, Any]:
    """
    根据策略权重混合应用变形策略
    
    Args:
        content: 原始内容
        strategy_weights: 策略权重字典
        
    Returns:
        变形后的内容
    """
    morpher = get_content_morpher()
    return morpher.morph_content(content, strategy_weights)


def apply_user_preferences(content: Dict[str, Any], user_preferences: Dict[str, Any]) -> Dict[str, Any]:
    """
    根据用户偏好自动选择和应用变形策略
    
    Args:
        content: 原始内容
        user_preferences: 用户偏好数据
        
    Returns:
        根据用户偏好变形后的内容
    """
    morpher = get_content_morpher()
    return morpher.apply_user_preferences(content, user_preferences) 