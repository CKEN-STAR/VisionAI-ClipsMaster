#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
情感节奏调节器

根据情感强度和类型调整场景节奏，创造情感共鸣的视听体验。
主要功能：
1. 根据情感强度调整场景时长
2. 确保情感连贯性和过渡自然
3. 提供情感节奏模板和预设
4. 在保持内容完整性的同时优化情感表达
"""

import logging
import math
import os
import yaml
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union

# 导入相关模块
from src.emotion.intensity_mapper import EmotionMapper
from src.emotion.focus_locator import EmotionFocusLocator
from src.utils.config_utils import load_config

# 创建日志记录器
logger = logging.getLogger("emotion_rhythm")

class EmotionRhythm:
    """
    情感节奏调节器，根据情感内容调整场景节奏
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化情感节奏调节器
        
        Args:
            config_path: 配置文件路径，如果为None则使用默认配置
        """
        # 默认配置路径
        if config_path is None:
            config_path = "configs/emotion_rhythm.yaml"
            
        # 加载配置
        self.config = load_config(config_path)
        if not self.config:
            # 如果配置加载失败，使用默认配置
            self.config = self._get_default_config()
        
        # 初始化依赖模块
        self.emotion_mapper = EmotionMapper()
        self.focus_locator = EmotionFocusLocator()
        
        # 日志记录
        logger.info("情感节奏调节器初始化完成")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "intensity_pacing": {
                "high_intensity": {
                    "factor": 1.3,          # 高情感强度延长因子
                    "threshold": 0.8,        # 高强度阈值
                    "max_extension": 0.5     # 最大延长比例
                },
                "medium_intensity": {
                    "factor": 1.0,          # 中情感强度因子
                    "threshold_low": 0.4,    # 中强度下限
                    "threshold_high": 0.8    # 中强度上限
                },
                "low_intensity": {
                    "factor": 0.7,          # 低情感强度缩短因子
                    "threshold": 0.4,        # 低强度阈值
                    "min_duration": 0.7      # 最小持续时间比例
                }
            },
            "emotion_type_adjustment": {
                "悲伤": 1.2,                # 悲伤情感场景延长因子
                "喜悦": 0.9,                # 喜悦情感场景缩短因子
                "紧张": 0.8,                # 紧张情感场景缩短因子
                "恐惧": 0.85,               # 恐惧情感场景缩短因子
                "愤怒": 0.95,               # 愤怒情感场景微缩因子
                "惊讶": 1.1                 # 惊讶情感场景延长因子
            },
            "coherence": {
                "max_delta": 0.15,          # 相邻场景最大变化率
                "enforce_continuity": True,  # 是否强制连续性
                "smooth_transitions": True   # 平滑过渡
            },
            "scene_constraints": {
                "min_duration": 0.8,         # 最小场景持续时间(秒)
                "max_duration": 15.0         # 最大场景持续时间(秒)
            },
            "rhythm_patterns": {
                "emotional_crescendo": {     # 情感渐强模式
                    "start_factor": 0.8,
                    "end_factor": 1.2,
                    "curve": "linear"
                },
                "emotional_wave": {          # 情感波浪模式
                    "amplitude": 0.2,
                    "frequency": 2,
                    "base_factor": 1.0
                },
                "emotional_focus": {         # 情感焦点模式
                    "regular_factor": 0.85,
                    "focus_factor": 1.25,
                    "focus_range": 0.2
                }
            }
        }
    
    def adjust_pacing(self, scene: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据情感强度调整单个场景的节奏
        
        Args:
            scene: 场景数据字典
        
        Returns:
            调整后的场景
        """
        # 创建场景的副本以避免修改原始数据
        adjusted_scene = scene.copy()
        
        # 检查场景是否包含必要的时间信息
        if "start" not in scene or "end" not in scene:
            logger.warning("场景缺少时间信息，无法调整节奏")
            return adjusted_scene
        
        # 计算基础时长
        base_dur = scene["end"] - scene["start"]
        
        # 检查场景是否包含情感信息
        if "emotion" not in scene or not isinstance(scene["emotion"], dict):
            logger.warning("场景缺少情感信息，使用默认调整")
            adjusted_scene["adjusted_duration"] = base_dur
            return adjusted_scene
        
        # 获取情感信息
        emotion_type = scene["emotion"].get("type", "中性")
        emotion_score = scene["emotion"].get("score", 0.5)
        
        # 根据情感强度调整节奏
        factor = self._get_intensity_factor(emotion_score)
        
        # 根据情感类型进一步调整
        type_factor = self.config["emotion_type_adjustment"].get(emotion_type, 1.0)
        
        # 计算综合调整因子
        combined_factor = factor * type_factor
        
        # 应用调整因子计算新的持续时间
        new_duration = base_dur * combined_factor
        
        # 确保在最小和最大持续时间范围内
        min_dur = self.config["scene_constraints"]["min_duration"]
        max_dur = self.config["scene_constraints"]["max_duration"]
        new_duration = max(min_dur, min(max_dur, new_duration))
        
        # 更新场景信息
        adjusted_scene["adjusted_duration"] = new_duration
        adjusted_scene["timing_factor"] = combined_factor
        adjusted_scene["rhythm_adjustment"] = {
            "original_duration": base_dur,
            "new_duration": new_duration,
            "intensity_factor": factor,
            "type_factor": type_factor,
            "emotion_type": emotion_type,
            "emotion_score": emotion_score
        }
        
        return adjusted_scene
    
    def _get_intensity_factor(self, emotion_score: float) -> float:
        """
        根据情感强度获取调整因子
        
        Args:
            emotion_score: 情感强度分数 (0-1)
            
        Returns:
            调整因子
        """
        # 获取配置信息
        intensity_config = self.config["intensity_pacing"]
        
        # 高强度情感
        if emotion_score >= intensity_config["high_intensity"]["threshold"]:
            return intensity_config["high_intensity"]["factor"]
        
        # 低强度情感
        if emotion_score <= intensity_config["low_intensity"]["threshold"]:
            return intensity_config["low_intensity"]["factor"]
        
        # 中等强度情感 - 线性插值
        low_threshold = intensity_config["low_intensity"]["threshold"]
        high_threshold = intensity_config["high_intensity"]["threshold"]
        low_factor = intensity_config["low_intensity"]["factor"]
        high_factor = intensity_config["high_intensity"]["factor"]
        
        # 计算插值
        ratio = (emotion_score - low_threshold) / (high_threshold - low_threshold)
        return low_factor + ratio * (high_factor - low_factor)
    
    def process_scene_sequence(self, scenes: List[Dict[str, Any]], pattern: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        处理场景序列，确保情感节奏的连贯性
        
        Args:
            scenes: 场景列表
            pattern: 节奏模式名称，如果为None则根据内容自动选择
            
        Returns:
            调整后的场景列表
        """
        if not scenes:
            return []
        
        # 创建场景副本
        adjusted_scenes = [scene.copy() for scene in scenes]
        
        # 单独调整每个场景
        for i, scene in enumerate(adjusted_scenes):
            adjusted_scenes[i] = self.adjust_pacing(scene)
        
        # 应用特定节奏模式（如果指定）
        if pattern and pattern in self.config["rhythm_patterns"]:
            adjusted_scenes = self._apply_rhythm_pattern(adjusted_scenes, pattern)
        else:
            # 自动选择节奏模式
            pattern = self._select_rhythm_pattern(adjusted_scenes)
            adjusted_scenes = self._apply_rhythm_pattern(adjusted_scenes, pattern)
        
        # 确保场景间的连贯性
        if self.config["coherence"]["enforce_continuity"]:
            adjusted_scenes = self._ensure_coherence(adjusted_scenes)
        
        # 记录应用的节奏模式
        for scene in adjusted_scenes:
            scene["applied_rhythm_pattern"] = pattern
        
        return adjusted_scenes
    
    def _select_rhythm_pattern(self, scenes: List[Dict[str, Any]]) -> str:
        """
        根据场景内容自动选择节奏模式
        
        Args:
            scenes: 场景列表
            
        Returns:
            节奏模式名称
        """
        if not scenes:
            return "emotional_wave"  # 默认模式
        
        # 分析情感变化趋势
        emotion_scores = []
        for scene in scenes:
            if "emotion" in scene and isinstance(scene["emotion"], dict):
                emotion_scores.append(scene["emotion"].get("score", 0.5))
            else:
                emotion_scores.append(0.5)  # 默认中等强度
        
        # 检查情感趋势
        if len(emotion_scores) >= 3:
            # 计算差分
            diffs = [emotion_scores[i+1] - emotion_scores[i] for i in range(len(emotion_scores)-1)]
            avg_diff = sum(diffs) / len(diffs)
            
            # 如果整体趋势是上升的，使用渐强模式
            if avg_diff > 0.05:
                return "emotional_crescendo"
            
            # 检查波动性
            variance = np.var(emotion_scores)
            if variance > 0.03:
                return "emotional_wave"
            
            # 检查是否有明显的高点
            max_score = max(emotion_scores)
            if max_score > 0.7 and max_score - np.mean(emotion_scores) > 0.2:
                return "emotional_focus"
        
        # 默认使用波浪模式
        return "emotional_wave"
    
    def _apply_rhythm_pattern(self, scenes: List[Dict[str, Any]], pattern: str) -> List[Dict[str, Any]]:
        """
        应用特定的节奏模式
        
        Args:
            scenes: 场景列表
            pattern: 节奏模式名称
            
        Returns:
            调整后的场景列表
        """
        if not scenes or pattern not in self.config["rhythm_patterns"]:
            return scenes
        
        pattern_config = self.config["rhythm_patterns"][pattern]
        adjusted_scenes = [scene.copy() for scene in scenes]
        
        # 根据模式类型应用不同的调整
        if pattern == "emotional_crescendo":
            # 情感渐强模式：逐渐增加场景持续时间
            start_factor = pattern_config["start_factor"]
            end_factor = pattern_config["end_factor"]
            
            for i, scene in enumerate(adjusted_scenes):
                # 线性插值计算因子
                progress = i / (len(adjusted_scenes) - 1) if len(adjusted_scenes) > 1 else 0.5
                factor = start_factor + progress * (end_factor - start_factor)
                
                # 应用因子
                base_duration = scene["rhythm_adjustment"]["original_duration"]
                scene["adjusted_duration"] = base_duration * factor
                scene["rhythm_adjustment"]["pattern_factor"] = factor
        
        elif pattern == "emotional_wave":
            # 情感波浪模式：波浪状调整场景持续时间
            amplitude = pattern_config["amplitude"]
            frequency = pattern_config["frequency"]
            base_factor = pattern_config["base_factor"]
            
            for i, scene in enumerate(adjusted_scenes):
                # 使用正弦函数创建波浪
                wave_pos = i * frequency / len(adjusted_scenes) * (2 * math.pi)
                factor = base_factor + amplitude * math.sin(wave_pos)
                
                # 应用因子
                base_duration = scene["rhythm_adjustment"]["original_duration"]
                scene["adjusted_duration"] = base_duration * factor
                scene["rhythm_adjustment"]["pattern_factor"] = factor
        
        elif pattern == "emotional_focus":
            # 情感焦点模式：找出情感高峰并延长，其他缩短
            regular_factor = pattern_config["regular_factor"]
            focus_factor = pattern_config["focus_factor"]
            
            # 找出情感强度最高的场景
            max_score = 0
            max_index = 0
            for i, scene in enumerate(adjusted_scenes):
                score = scene.get("emotion", {}).get("score", 0)
                if score > max_score:
                    max_score = score
                    max_index = i
            
            # 应用不同因子
            for i, scene in enumerate(adjusted_scenes):
                # 计算与焦点的距离（归一化）
                distance = abs(i - max_index) / (len(adjusted_scenes) / 2)
                
                # 越靠近焦点，因子越接近focus_factor
                factor = focus_factor if distance < pattern_config["focus_range"] else regular_factor
                
                # 应用因子
                base_duration = scene["rhythm_adjustment"]["original_duration"]
                scene["adjusted_duration"] = base_duration * factor
                scene["rhythm_adjustment"]["pattern_factor"] = factor
                scene["rhythm_adjustment"]["is_focus"] = (distance < pattern_config["focus_range"])
        
        return adjusted_scenes
    
    def _ensure_coherence(self, scenes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        确保场景间节奏的连贯性，避免突变
        
        Args:
            scenes: 场景列表
            
        Returns:
            调整后的场景列表
        """
        if len(scenes) <= 1:
            return scenes
        
        max_delta = self.config["coherence"]["max_delta"]
        adjusted_scenes = [scenes[0].copy()]
        
        for i in range(1, len(scenes)):
            current_scene = scenes[i].copy()
            prev_factor = adjusted_scenes[-1]["timing_factor"]
            current_factor = current_scene["timing_factor"]
            
            # 检查相邻场景的调整因子变化是否超过阈值
            delta = abs(current_factor - prev_factor)
            if delta > max_delta:
                # 限制变化
                if current_factor > prev_factor:
                    current_factor = prev_factor + max_delta
                else:
                    current_factor = prev_factor - max_delta
                
                # 重新计算持续时间
                base_duration = current_scene["rhythm_adjustment"]["original_duration"]
                current_scene["adjusted_duration"] = base_duration * current_factor
                current_scene["timing_factor"] = current_factor
                current_scene["rhythm_adjustment"]["coherence_adjusted"] = True
            
            adjusted_scenes.append(current_scene)
        
        return adjusted_scenes


# 对外直接调用的函数
def adjust_pacing(scene: Dict[str, Any]) -> Dict[str, Any]:
    """
    根据情感强度调整单个场景的节奏
    
    Args:
        scene: 场景数据字典
    
    Returns:
        调整后的场景
    """
    adjuster = EmotionRhythm()
    return adjuster.adjust_pacing(scene)

def process_scene_sequence(scenes: List[Dict[str, Any]], pattern: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    处理场景序列，确保情感节奏的连贯性
    
    Args:
        scenes: 场景列表
        pattern: 节奏模式名称，如果为None则根据内容自动选择
        
    Returns:
        调整后的场景列表
    """
    adjuster = EmotionRhythm()
    return adjuster.process_scene_sequence(scenes, pattern) 