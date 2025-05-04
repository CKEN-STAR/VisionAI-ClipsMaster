#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
行为解码器模块

实时解析用户的观看行为，转化为具有意义的偏好信号，
用于构建用户偏好模型并支持智能混剪推荐。
"""

import os
import json
import time
from typing import Dict, List, Any, Optional, Tuple, Set, Union
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import numpy as np
from loguru import logger

from src.utils.log_handler import get_logger
from src.data.storage_manager import get_storage_manager
from src.audience.behavior_tracker import get_behavior_tracker
from src.audience.profile_builder import get_profile_engine

# 配置日志
decoder_logger = get_logger("behavior_decoder")

class BehaviorDecoder:
    """用户行为解码器
    
    解析用户观看和交互行为中的隐含偏好信号，
    将原始行为转化为具有实际意义的偏好表达。
    """
    
    def __init__(self):
        """初始化行为解码器"""
        # 获取存储管理器
        self.storage = get_storage_manager()
        
        # 获取行为跟踪器
        self.behavior_tracker = get_behavior_tracker()
        
        # 获取用户画像引擎
        self.profile_engine = get_profile_engine()
        
        # 行为解码配置
        self.config = {
            # 行为类型重要性权重
            "behavior_weights": {
                "completion": 2.0,      # 完成度权重
                "replay": 1.8,          # 重播权重
                "skip": -1.5,           # 跳过权重
                "like": 1.5,            # 点赞权重
                "share": 2.0,           # 分享权重
                "comment": 1.2,         # 评论权重
                "save": 1.8,            # 收藏权重
                "search": 1.0,          # 搜索权重
                "click": 0.8,           # 点击权重
            },
            
            # 时间衰减系数 - 决定近期行为的重要性
            "time_decay_factor": 0.95,   # 每过去一天，重要性衰减5%
            
            # 偏好分数阈值
            "preference_thresholds": {
                "strong_like": 0.7,     # 强烈喜欢阈值
                "like": 0.5,            # 喜欢阈值
                "neutral": 0.0,         # 中立阈值
                "dislike": -0.5,        # 不喜欢阈值
                "strong_dislike": -0.7, # 强烈不喜欢阈值
            },
            
            # 关注度判断配置
            "engagement_config": {
                "min_view_ratio": 0.7,   # 最小观看比例
                "action_threshold": 2,   # 最小交互动作数
                "replay_bonus": 0.3,     # 重播加分
            },
            
            # 兴趣点检测配置
            "interest_point_config": {
                "pause_threshold": 2.0,  # 暂停阈值（秒）
                "replay_threshold": 1,   # 重播阈值（次数）
                "hover_threshold": 3.0,  # 悬停阈值（秒）
            }
        }
        
        decoder_logger.info("行为解码器初始化完成")
    
    def decode_user_behavior(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """解码用户行为中的偏好信号
        
        Args:
            user_id: 用户ID
            days: 分析的历史天数
            
        Returns:
            Dict[str, Any]: 解码后的偏好信号
        """
        decoder_logger.info(f"开始解码用户 {user_id} 的行为偏好")
        
        # 获取用户行为数据
        behavior_data = self.behavior_tracker.get_user_behavior_summary(user_id, days)
        if not behavior_data:
            decoder_logger.warning(f"未找到用户 {user_id} 的行为数据")
            return {"user_id": user_id, "preferences": {}, "status": "no_data"}
        
        # 解码内容类型偏好
        content_preferences = self._decode_content_preferences(behavior_data)
        
        # 解码情感偏好
        emotion_preferences = self._decode_emotion_preferences(behavior_data)
        
        # 解码叙事结构偏好
        narrative_preferences = self._decode_narrative_preferences(behavior_data)
        
        # 解码节奏偏好
        pacing_preferences = self._decode_pacing_preferences(behavior_data)
        
        # 解码剪辑风格偏好
        editing_preferences = self._decode_editing_preferences(behavior_data)
        
        # 解码设备使用偏好
        device_preferences = self._decode_device_preferences(behavior_data)
        
        # 识别关键兴趣点
        interest_points = self._identify_interest_points(behavior_data)
        
        # 组装解码结果
        decoded_preferences = {
            "user_id": user_id,
            "content_preferences": content_preferences,
            "emotion_preferences": emotion_preferences,
            "narrative_preferences": narrative_preferences,
            "pacing_preferences": pacing_preferences,
            "editing_preferences": editing_preferences,
            "device_preferences": device_preferences,
            "interest_points": interest_points,
            "decoded_at": datetime.now().isoformat(),
            "data_period_days": days,
            "status": "success"
        }
        
        # 保存解码结果
        self._save_decoded_preferences(user_id, decoded_preferences)
        
        decoder_logger.info(f"用户 {user_id} 的行为偏好解码完成")
        return decoded_preferences
    
    def _decode_content_preferences(self, behavior_data: Dict[str, Any]) -> Dict[str, Any]:
        """解码内容类型偏好
        
        Args:
            behavior_data: 用户行为数据
            
        Returns:
            Dict[str, Any]: 内容类型偏好
        """
        # 初始化内容偏好
        content_preferences = {
            "genres": {},     # 类型偏好
            "themes": {},     # 主题偏好
            "characters": {}, # 角色偏好
            "formats": {},    # 格式偏好
            "confidence": 0.0
        }
        
        # 检查行为数据中的内容观看记录
        if "content_views" not in behavior_data:
            return content_preferences
        
        content_views = behavior_data["content_views"]
        
        # 提取各类内容元素计数
        genre_counter = Counter()
        theme_counter = Counter()
        character_counter = Counter()
        format_counter = Counter()
        
        # 记录各内容的偏好分数
        genre_scores = defaultdict(float)
        theme_scores = defaultdict(float)
        character_scores = defaultdict(float)
        format_scores = defaultdict(float)
        
        # 分析每个内容的观看数据
        for content_id, view_data in content_views.items():
            metadata = view_data.get("metadata", {})
            completion_rate = view_data.get("completion_rate", 0)
            interactions = view_data.get("interactions", {})
            
            # 计算该内容的整体偏好分数
            score = self._calculate_content_preference_score(completion_rate, interactions)
            
            # 提取并计分类型
            if "genre" in metadata:
                genre = metadata["genre"]
                genre_counter[genre] += 1
                genre_scores[genre] += score
            
            # 提取并计分主题
            if "themes" in metadata and isinstance(metadata["themes"], list):
                for theme in metadata["themes"]:
                    theme_counter[theme] += 1
                    theme_scores[theme] += score
            
            # 提取并计分角色类型
            if "characters" in metadata and isinstance(metadata["characters"], list):
                for character in metadata["characters"]:
                    character_counter[character] += 1
                    character_scores[character] += score
            
            # 提取并计分内容格式
            if "format" in metadata:
                format_type = metadata["format"]
                format_counter[format_type] += 1
                format_scores[format_type] += score
        
        # 计算平均分数
        for genre in genre_counter:
            if genre_counter[genre] > 0:
                genre_scores[genre] /= genre_counter[genre]
        
        for theme in theme_counter:
            if theme_counter[theme] > 0:
                theme_scores[theme] /= theme_counter[theme]
        
        for character in character_counter:
            if character_counter[character] > 0:
                character_scores[character] /= character_counter[character]
        
        for format_type in format_counter:
            if format_counter[format_type] > 0:
                format_scores[format_type] /= format_counter[format_type]
        
        # 为每种类型分配强度级别
        content_preferences["genres"] = self._assign_preference_strength(genre_scores)
        content_preferences["themes"] = self._assign_preference_strength(theme_scores)
        content_preferences["characters"] = self._assign_preference_strength(character_scores)
        content_preferences["formats"] = self._assign_preference_strength(format_scores)
        
        # 计算置信度
        total_views = len(content_views)
        content_preferences["confidence"] = min(1.0, total_views / 20)
        
        return content_preferences
    
    def _calculate_content_preference_score(self, completion_rate: float, 
                                          interactions: Dict[str, Any]) -> float:
        """计算内容偏好分数
        
        基于完成率和交互行为计算内容偏好分数。
        
        Args:
            completion_rate: 内容完成率
            interactions: 交互行为数据
            
        Returns:
            float: 偏好分数，范围 [-1, 1]
        """
        # 初始化基础分数
        base_score = 0.0
        weights = self.config["behavior_weights"]
        
        # 基于完成率评分
        if completion_rate >= 0.9:
            base_score += weights["completion"] * 1.0
        elif completion_rate >= 0.7:
            base_score += weights["completion"] * 0.7
        elif completion_rate >= 0.5:
            base_score += weights["completion"] * 0.3
        elif completion_rate <= 0.3:
            base_score += weights["skip"] * 0.7  # 负面分数
        elif completion_rate <= 0.1:
            base_score += weights["skip"] * 1.0  # 强负面分数
        
        # 基于交互行为评分
        if "like" in interactions and interactions["like"]:
            base_score += weights["like"]
        
        if "share" in interactions and interactions["share"]:
            base_score += weights["share"]
        
        if "save" in interactions and interactions["save"]:
            base_score += weights["save"]
        
        if "comment" in interactions and interactions["comment"]:
            base_score += weights["comment"]
        
        # 重播情况
        replay_count = interactions.get("replay_count", 0)
        if replay_count > 0:
            replay_score = min(replay_count * 0.3, 1.0) * weights["replay"]
            base_score += replay_score
        
        # 标准化分数到 [-1, 1] 范围
        max_possible_score = weights["completion"] + weights["like"] + weights["share"] + \
                             weights["save"] + weights["comment"] + weights["replay"]
        min_possible_score = weights["skip"]
        
        normalized_score = 2 * (base_score - min_possible_score) / (max_possible_score - min_possible_score) - 1
        normalized_score = max(-1.0, min(1.0, normalized_score))
        
        return normalized_score
    
    def _assign_preference_strength(self, scores: Dict[str, float]) -> Dict[str, Dict[str, Any]]:
        """为偏好分数分配强度级别
        
        Args:
            scores: 偏好项目的分数字典
            
        Returns:
            Dict[str, Dict[str, Any]]: 带有强度级别的偏好字典
        """
        thresholds = self.config["preference_thresholds"]
        result = {}
        
        for item, score in scores.items():
            if score >= thresholds["strong_like"]:
                strength = "strong_like"
            elif score >= thresholds["like"]:
                strength = "like"
            elif score > thresholds["dislike"]:
                strength = "neutral"
            elif score > thresholds["strong_dislike"]:
                strength = "dislike"
            else:
                strength = "strong_dislike"
            
            result[item] = {
                "score": round(score, 2),
                "strength": strength
            }
        
        return result
    
    def _decode_emotion_preferences(self, behavior_data: Dict[str, Any]) -> Dict[str, Any]:
        """解码情感偏好
        
        Args:
            behavior_data: 用户行为数据
            
        Returns:
            Dict[str, Any]: 情感偏好
        """
        # 初始化情感偏好
        emotion_preferences = {
            "primary_emotions": {},  # 主要情感偏好
            "emotional_arcs": {},    # 情感曲线偏好
            "intensity": 0.5,        # 情感强度偏好（0.0-1.0）
            "valence": 0.0,          # 情感价值偏好（-1.0消极到1.0积极）
            "confidence": 0.0
        }
        
        # 检查是否有情感反馈数据
        if "emotional_responses" not in behavior_data:
            return emotion_preferences
        
        emotional_responses = behavior_data["emotional_responses"]
        if not emotional_responses:
            return emotion_preferences
        
        # 提取情感类型和曲线计数
        emotion_counter = Counter()
        arc_counter = Counter()
        
        # 情感分数累加器
        emotion_scores = defaultdict(float)
        arc_scores = defaultdict(float)
        intensity_values = []
        valence_values = []
        
        # 分析每条情感反馈
        for content_id, response_data in emotional_responses.items():
            emotion_type = response_data.get("primary_emotion")
            arc_type = response_data.get("emotional_arc")
            intensity = response_data.get("intensity", 0.5)
            valence = response_data.get("valence", 0.0)
            engagement = response_data.get("engagement", 0.0)
            
            # 只处理有足够参与度的反馈
            if engagement < 0.3:
                continue
            
            # 计算反馈权重
            weight = engagement * 1.0
            
            # 更新情感类型统计
            if emotion_type:
                emotion_counter[emotion_type] += 1
                emotion_scores[emotion_type] += weight
            
            # 更新情感曲线统计
            if arc_type:
                arc_counter[arc_type] += 1
                arc_scores[arc_type] += weight
            
            # 更新强度和价值统计
            if intensity is not None:
                intensity_values.append(intensity)
            
            if valence is not None:
                valence_values.append(valence)
        
        # 计算平均分数
        for emotion in emotion_counter:
            if emotion_counter[emotion] > 0:
                emotion_scores[emotion] /= emotion_counter[emotion]
        
        for arc in arc_counter:
            if arc_counter[arc] > 0:
                arc_scores[arc] /= arc_counter[arc]
        
        # 为每种情感类型和曲线分配强度级别
        emotion_preferences["primary_emotions"] = self._assign_preference_strength(emotion_scores)
        emotion_preferences["emotional_arcs"] = self._assign_preference_strength(arc_scores)
        
        # 计算平均强度和价值
        if intensity_values:
            emotion_preferences["intensity"] = sum(intensity_values) / len(intensity_values)
        
        if valence_values:
            emotion_preferences["valence"] = sum(valence_values) / len(valence_values)
        
        # 计算置信度
        total_responses = len(emotional_responses)
        emotion_preferences["confidence"] = min(1.0, total_responses / 15)
        
        return emotion_preferences
    
    def _decode_narrative_preferences(self, behavior_data: Dict[str, Any]) -> Dict[str, Any]:
        """解码叙事结构偏好
        
        Args:
            behavior_data: 用户行为数据
            
        Returns:
            Dict[str, Any]: 叙事结构偏好
        """
        # 初始化叙事偏好
        narrative_preferences = {
            "structures": {},         # 叙事结构偏好
            "conflict_types": {},     # 冲突类型偏好
            "character_focus": {},    # 角色焦点偏好
            "complexity": 0.5,        # 复杂度偏好（0.0简单到1.0复杂）
            "confidence": 0.0
        }
        
        # 检查是否有内容观看数据
        if "content_views" not in behavior_data:
            return narrative_preferences
        
        content_views = behavior_data["content_views"]
        
        # 提取叙事结构计数
        structure_counter = Counter()
        conflict_counter = Counter()
        character_focus_counter = Counter()
        
        # 叙事分数累加器
        structure_scores = defaultdict(float)
        conflict_scores = defaultdict(float)
        character_focus_scores = defaultdict(float)
        complexity_values = []
        
        # 分析每个内容的观看数据
        for content_id, view_data in content_views.items():
            metadata = view_data.get("metadata", {})
            completion_rate = view_data.get("completion_rate", 0)
            interactions = view_data.get("interactions", {})
            
            # 只分析观看完成度较高的内容
            if completion_rate < 0.5:
                continue
            
            # 计算该内容的偏好分数
            score = self._calculate_content_preference_score(completion_rate, interactions)
            
            # 提取叙事结构信息
            narrative_data = metadata.get("narrative", {})
            
            # 更新叙事结构统计
            structure = narrative_data.get("structure")
            if structure:
                structure_counter[structure] += 1
                structure_scores[structure] += score
            
            # 更新冲突类型统计
            conflict = narrative_data.get("conflict_type")
            if conflict:
                conflict_counter[conflict] += 1
                conflict_scores[conflict] += score
            
            # 更新角色焦点统计
            focus = narrative_data.get("character_focus")
            if focus:
                character_focus_counter[focus] += 1
                character_focus_scores[focus] += score
            
            # 更新复杂度统计
            complexity = narrative_data.get("complexity")
            if complexity is not None:
                complexity_values.append(complexity)
        
        # 计算平均分数
        for structure in structure_counter:
            if structure_counter[structure] > 0:
                structure_scores[structure] /= structure_counter[structure]
        
        for conflict in conflict_counter:
            if conflict_counter[conflict] > 0:
                conflict_scores[conflict] /= conflict_counter[conflict]
        
        for focus in character_focus_counter:
            if character_focus_counter[focus] > 0:
                character_focus_scores[focus] /= character_focus_counter[focus]
        
        # 为每种叙事元素分配强度级别
        narrative_preferences["structures"] = self._assign_preference_strength(structure_scores)
        narrative_preferences["conflict_types"] = self._assign_preference_strength(conflict_scores)
        narrative_preferences["character_focus"] = self._assign_preference_strength(character_focus_scores)
        
        # 计算平均复杂度
        if complexity_values:
            narrative_preferences["complexity"] = sum(complexity_values) / len(complexity_values)
        
        # 计算置信度
        analyzed_contents = sum(1 for view_data in content_views.values() if view_data.get("completion_rate", 0) >= 0.5)
        narrative_preferences["confidence"] = min(1.0, analyzed_contents / 10)
        
        return narrative_preferences
    
    def _decode_pacing_preferences(self, behavior_data: Dict[str, Any]) -> Dict[str, Any]:
        """解码节奏偏好
        
        Args:
            behavior_data: 用户行为数据
            
        Returns:
            Dict[str, Any]: 节奏偏好
        """
        # 初始化节奏偏好
        pacing_preferences = {
            "overall_pace": {},       # 整体节奏偏好
            "scene_duration": {       # 场景时长偏好
                "min": 3.0,
                "max": 15.0,
                "preferred": 8.0
            },
            "cut_frequency": {},      # 剪辑频率偏好
            "tension_build": {},      # 紧张感构建偏好
            "confidence": 0.0
        }
        
        # 检查是否有内容观看数据
        if "content_views" not in behavior_data:
            return pacing_preferences
        
        content_views = behavior_data["content_views"]
        
        # 提取节奏相关计数
        pace_counter = Counter()
        cut_counter = Counter()
        tension_counter = Counter()
        
        # 节奏分数累加器
        pace_scores = defaultdict(float)
        cut_scores = defaultdict(float)
        tension_scores = defaultdict(float)
        scene_durations = []
        
        # 分析每个内容的观看数据
        for content_id, view_data in content_views.items():
            metadata = view_data.get("metadata", {})
            completion_rate = view_data.get("completion_rate", 0)
            interactions = view_data.get("interactions", {})
            
            # 只分析观看完成度较高的内容
            if completion_rate < 0.5:
                continue
            
            # 计算该内容的偏好分数
            score = self._calculate_content_preference_score(completion_rate, interactions)
            
            # 提取节奏信息
            pacing_data = metadata.get("pacing", {})
            
            # 更新整体节奏统计
            pace = pacing_data.get("overall_pace")
            if pace:
                pace_counter[pace] += 1
                pace_scores[pace] += score
            
            # 更新剪辑频率统计
            cut_freq = pacing_data.get("cut_frequency")
            if cut_freq:
                cut_counter[cut_freq] += 1
                cut_scores[cut_freq] += score
            
            # 更新紧张感构建统计
            tension = pacing_data.get("tension_build")
            if tension:
                tension_counter[tension] += 1
                tension_scores[tension] += score
            
            # 更新场景时长统计
            avg_scene_duration = pacing_data.get("avg_scene_duration")
            if avg_scene_duration:
                scene_durations.append(avg_scene_duration)
        
        # 计算平均分数
        for pace in pace_counter:
            if pace_counter[pace] > 0:
                pace_scores[pace] /= pace_counter[pace]
        
        for cut in cut_counter:
            if cut_counter[cut] > 0:
                cut_scores[cut] /= cut_counter[cut]
        
        for tension in tension_counter:
            if tension_counter[tension] > 0:
                tension_scores[tension] /= tension_counter[tension]
        
        # 为每种节奏元素分配强度级别
        pacing_preferences["overall_pace"] = self._assign_preference_strength(pace_scores)
        pacing_preferences["cut_frequency"] = self._assign_preference_strength(cut_scores)
        pacing_preferences["tension_build"] = self._assign_preference_strength(tension_scores)
        
        # 计算场景时长偏好
        if scene_durations:
            scene_durations.sort()
            if len(scene_durations) >= 3:
                # 移除极值
                scene_durations = scene_durations[1:-1]
            
            pacing_preferences["scene_duration"] = {
                "min": min(scene_durations),
                "max": max(scene_durations),
                "preferred": sum(scene_durations) / len(scene_durations)
            }
        
        # 计算置信度
        analyzed_contents = sum(1 for view_data in content_views.values() if view_data.get("completion_rate", 0) >= 0.5)
        pacing_preferences["confidence"] = min(1.0, analyzed_contents / 10)
        
        return pacing_preferences
    
    def _decode_editing_preferences(self, behavior_data: Dict[str, Any]) -> Dict[str, Any]:
        """解码剪辑风格偏好
        
        Args:
            behavior_data: 用户行为数据
            
        Returns:
            Dict[str, Any]: 剪辑风格偏好
        """
        # 初始化剪辑偏好
        editing_preferences = {
            "transitions": {},        # 转场偏好
            "visual_effects": {},     # 视觉效果偏好
            "color_grading": {},      # 色彩风格偏好
            "audio_treatment": {},    # 音频处理偏好
            "confidence": 0.0
        }
        
        # 检查是否有内容观看数据
        if "content_views" not in behavior_data:
            return editing_preferences
        
        content_views = behavior_data["content_views"]
        
        # 提取剪辑元素计数
        transition_counter = Counter()
        effect_counter = Counter()
        color_counter = Counter()
        audio_counter = Counter()
        
        # 剪辑分数累加器
        transition_scores = defaultdict(float)
        effect_scores = defaultdict(float)
        color_scores = defaultdict(float)
        audio_scores = defaultdict(float)
        
        # 分析每个内容的观看数据
        for content_id, view_data in content_views.items():
            metadata = view_data.get("metadata", {})
            completion_rate = view_data.get("completion_rate", 0)
            interactions = view_data.get("interactions", {})
            
            # 只分析观看完成度较高的内容
            if completion_rate < 0.5:
                continue
            
            # 计算该内容的偏好分数
            score = self._calculate_content_preference_score(completion_rate, interactions)
            
            # 提取剪辑风格信息
            editing_data = metadata.get("editing", {})
            
            # 更新转场偏好统计
            transition = editing_data.get("transition_type")
            if transition:
                transition_counter[transition] += 1
                transition_scores[transition] += score
            
            # 更新视觉效果统计
            effects = editing_data.get("visual_effects", [])
            for effect in effects:
                effect_counter[effect] += 1
                effect_scores[effect] += score
            
            # 更新色彩风格统计
            color = editing_data.get("color_grading")
            if color:
                color_counter[color] += 1
                color_scores[color] += score
            
            # 更新音频处理统计
            audio = editing_data.get("audio_treatment")
            if audio:
                audio_counter[audio] += 1
                audio_scores[audio] += score
        
        # 计算平均分数
        for transition in transition_counter:
            if transition_counter[transition] > 0:
                transition_scores[transition] /= transition_counter[transition]
        
        for effect in effect_counter:
            if effect_counter[effect] > 0:
                effect_scores[effect] /= effect_counter[effect]
        
        for color in color_counter:
            if color_counter[color] > 0:
                color_scores[color] /= color_counter[color]
        
        for audio in audio_counter:
            if audio_counter[audio] > 0:
                audio_scores[audio] /= audio_counter[audio]
        
        # 为每种剪辑元素分配强度级别
        editing_preferences["transitions"] = self._assign_preference_strength(transition_scores)
        editing_preferences["visual_effects"] = self._assign_preference_strength(effect_scores)
        editing_preferences["color_grading"] = self._assign_preference_strength(color_scores)
        editing_preferences["audio_treatment"] = self._assign_preference_strength(audio_scores)
        
        # 计算置信度
        analyzed_contents = sum(1 for view_data in content_views.values() if view_data.get("completion_rate", 0) >= 0.5)
        editing_preferences["confidence"] = min(1.0, analyzed_contents / 10)
        
        return editing_preferences
    
    def _decode_device_preferences(self, behavior_data: Dict[str, Any]) -> Dict[str, Any]:
        """解码设备使用偏好
        
        Args:
            behavior_data: 用户行为数据
            
        Returns:
            Dict[str, Any]: 设备使用偏好
        """
        # 初始化设备偏好
        device_preferences = {
            "device_types": {},          # 设备类型偏好
            "viewing_conditions": {},    # 观看条件偏好
            "optimal_resolution": None,  # 最佳分辨率
            "optimal_duration": None,    # 最佳时长
            "confidence": 0.0
        }
        
        # 检查是否有设备使用数据
        if "device_usage" not in behavior_data:
            return device_preferences
        
        device_usage = behavior_data["device_usage"]
        
        # 提取设备类型计数
        device_counter = Counter()
        condition_counter = Counter()
        resolutions = []
        durations = []
        
        # 设备使用分数累加器
        device_scores = defaultdict(float)
        condition_scores = defaultdict(float)
        
        # 分析每条设备使用记录
        for session_id, usage_data in device_usage.items():
            device_type = usage_data.get("device_type")
            viewing_condition = usage_data.get("viewing_condition")
            resolution = usage_data.get("resolution")
            session_duration = usage_data.get("session_duration")
            engagement = usage_data.get("engagement", 0.0)
            
            # 只处理有足够参与度的会话
            if engagement < 0.3:
                continue
            
            # 计算会话权重
            weight = engagement * 1.0
            
            # 更新设备类型统计
            if device_type:
                device_counter[device_type] += 1
                device_scores[device_type] += weight
            
            # 更新观看条件统计
            if viewing_condition:
                condition_counter[viewing_condition] += 1
                condition_scores[viewing_condition] += weight
            
            # 更新分辨率和时长统计
            if resolution and session_duration and engagement > 0.5:
                resolutions.append(resolution)
                durations.append(session_duration)
        
        # 计算平均分数
        for device in device_counter:
            if device_counter[device] > 0:
                device_scores[device] /= device_counter[device]
        
        for condition in condition_counter:
            if condition_counter[condition] > 0:
                condition_scores[condition] /= condition_counter[condition]
        
        # 为每种设备元素分配强度级别
        device_preferences["device_types"] = self._assign_preference_strength(device_scores)
        device_preferences["viewing_conditions"] = self._assign_preference_strength(condition_scores)
        
        # 确定最佳分辨率
        if resolutions:
            from collections import Counter
            resolution_count = Counter(resolutions)
            device_preferences["optimal_resolution"] = resolution_count.most_common(1)[0][0]
        
        # 确定最佳内容时长
        if durations:
            # 按参与度加权的平均时长
            device_preferences["optimal_duration"] = sum(durations) / len(durations)
        
        # 计算置信度
        total_sessions = len(device_usage)
        device_preferences["confidence"] = min(1.0, total_sessions / 10)
        
        return device_preferences
    
    def _identify_interest_points(self, behavior_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """识别用户行为中的关键兴趣点
        
        Args:
            behavior_data: 用户行为数据
            
        Returns:
            List[Dict[str, Any]]: 关键兴趣点列表
        """
        interest_points = []
        
        # 检查是否有内容观看数据
        if "content_views" not in behavior_data:
            return interest_points
        
        content_views = behavior_data["content_views"]
        config = self.config["interest_point_config"]
        
        # 分析每个内容的观看数据
        for content_id, view_data in content_views.items():
            # 获取时间线数据
            timeline = view_data.get("timeline", [])
            if not timeline:
                continue
            
            # 分析时间线上的每个事件
            for i, event in enumerate(timeline):
                event_type = event.get("event_type")
                timestamp = event.get("timestamp", 0)
                duration = event.get("duration", 0)
                
                # 检查是否为暂停/重播/悬停等兴趣事件
                is_interest_point = False
                interest_reason = None
                
                # 暂停点
                if event_type == "pause" and duration >= config["pause_threshold"]:
                    is_interest_point = True
                    interest_reason = "pause"
                
                # 重播点
                elif event_type == "replay" and event.get("count", 0) >= config["replay_threshold"]:
                    is_interest_point = True
                    interest_reason = "replay"
                
                # 悬停点 (UI事件)
                elif event_type == "hover" and duration >= config["hover_threshold"]:
                    is_interest_point = True
                    interest_reason = "hover"
                
                # 记录兴趣点
                if is_interest_point:
                    # 提取相关的内容元数据
                    metadata = view_data.get("metadata", {})
                    scene_info = None
                    
                    # 尝试找到对应的场景信息
                    scenes = metadata.get("scenes", [])
                    for scene in scenes:
                        scene_start = scene.get("start_time", 0)
                        scene_end = scene_start + scene.get("duration", 0)
                        if scene_start <= timestamp <= scene_end:
                            scene_info = scene
                            break
                    
                    # 创建兴趣点记录
                    interest_point = {
                        "content_id": content_id,
                        "timestamp": timestamp,
                        "reason": interest_reason,
                        "duration": duration,
                        "scene_info": scene_info,
                        "metadata": {
                            "content_title": metadata.get("title", "Unknown"),
                            "content_type": metadata.get("type", "Unknown"),
                            "genre": metadata.get("genre", "Unknown")
                        }
                    }
                    
                    interest_points.append(interest_point)
        
        # 按兴趣强度排序（按暂停/重播时长）
        interest_points.sort(key=lambda x: x.get("duration", 0), reverse=True)
        
        return interest_points[:20]  # 返回最多20个最强的兴趣点
    
    def decode_realtime_behavior(self, user_id: str, 
                               behavior_event: Dict[str, Any]) -> Dict[str, Any]:
        """实时解码单个用户行为事件
        
        Args:
            user_id: 用户ID
            behavior_event: 行为事件数据
            
        Returns:
            Dict[str, Any]: 实时解码的偏好信号
        """
        decoder_logger.debug(f"实时解码用户 {user_id} 的行为事件")
        
        # 初始化解码结果
        decoded_signal = {
            "user_id": user_id,
            "event_id": behavior_event.get("event_id", str(time.time())),
            "event_type": behavior_event.get("event_type"),
            "content_id": behavior_event.get("content_id"),
            "timestamp": behavior_event.get("timestamp", datetime.now().isoformat()),
            "preference_signals": {},
            "confidence": 0.0
        }
        
        # 根据事件类型进行不同的解码逻辑
        event_type = behavior_event.get("event_type")
        
        if event_type == "view_complete":
            # 完成观看事件
            completion_rate = behavior_event.get("completion_rate", 0)
            view_duration = behavior_event.get("duration", 0)
            content_metadata = behavior_event.get("metadata", {})
            
            # 解析内容偏好信号
            if completion_rate >= 0.8:
                # 高完成率表示强烈喜欢
                preference = "strong_like"
                confidence = min(1.0, completion_rate)
            elif completion_rate >= 0.6:
                # 中等完成率表示喜欢
                preference = "like"
                confidence = completion_rate * 0.8
            elif completion_rate <= 0.3:
                # 低完成率表示不喜欢
                preference = "dislike"
                confidence = (1 - completion_rate) * 0.7
            else:
                # 其他情况为中性
                preference = "neutral"
                confidence = 0.5
            
            # 从内容元数据中提取关键特征
            for feature_key in ["genre", "theme", "character_type", "narrative_style", "pacing"]:
                feature_value = content_metadata.get(feature_key)
                if feature_value:
                    decoded_signal["preference_signals"][f"{feature_key}:{feature_value}"] = {
                        "preference": preference,
                        "confidence": confidence
                    }
            
            # 设置整体置信度
            decoded_signal["confidence"] = confidence
            
        elif event_type == "like" or event_type == "share" or event_type == "save":
            # 积极的交互行为表示强烈喜欢
            content_metadata = behavior_event.get("metadata", {})
            
            # 从内容元数据中提取关键特征
            for feature_key in ["genre", "theme", "character_type", "narrative_style", "pacing"]:
                feature_value = content_metadata.get(feature_key)
                if feature_value:
                    decoded_signal["preference_signals"][f"{feature_key}:{feature_value}"] = {
                        "preference": "strong_like",
                        "confidence": 0.9
                    }
            
            # 设置整体置信度
            decoded_signal["confidence"] = 0.9
            
        elif event_type == "skip":
            # 跳过行为表示不喜欢
            skip_time = behavior_event.get("skip_time", 0)
            content_duration = behavior_event.get("content_duration", 1)
            skip_ratio = skip_time / content_duration if content_duration > 0 else 0
            content_metadata = behavior_event.get("metadata", {})
            
            # 早期跳过表示强烈不喜欢
            if skip_ratio <= 0.2:
                preference = "strong_dislike"
                confidence = 0.8
            else:
                preference = "dislike"
                confidence = 0.6
            
            # 从内容元数据中提取关键特征
            for feature_key in ["genre", "theme", "character_type", "narrative_style", "pacing"]:
                feature_value = content_metadata.get(feature_key)
                if feature_value:
                    decoded_signal["preference_signals"][f"{feature_key}:{feature_value}"] = {
                        "preference": preference,
                        "confidence": confidence
                    }
            
            # 设置整体置信度
            decoded_signal["confidence"] = confidence
            
        elif event_type == "pause" or event_type == "replay":
            # 暂停或重播通常表示兴趣点
            position = behavior_event.get("position", 0)
            content_metadata = behavior_event.get("metadata", {})
            
            # 记录兴趣点
            decoded_signal["interest_point"] = {
                "position": position,
                "content_id": behavior_event.get("content_id"),
                "scene_info": behavior_event.get("scene_info")
            }
            
            # 适度的正向偏好
            for feature_key in ["genre", "theme", "character_type", "narrative_style", "pacing"]:
                feature_value = content_metadata.get(feature_key)
                if feature_value:
                    decoded_signal["preference_signals"][f"{feature_key}:{feature_value}"] = {
                        "preference": "like",
                        "confidence": 0.7
                    }
            
            # 设置整体置信度
            decoded_signal["confidence"] = 0.7
        
        # 保存解码信号
        self._save_realtime_signal(user_id, decoded_signal)
        
        return decoded_signal
    
    def _save_decoded_preferences(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        """保存解码后的偏好数据
        
        Args:
            user_id: 用户ID
            preferences: 偏好数据
            
        Returns:
            bool: 保存是否成功
        """
        try:
            self.storage.save_user_preferences(user_id, preferences)
            decoder_logger.debug(f"成功保存用户 {user_id} 的偏好数据")
            return True
        except Exception as e:
            decoder_logger.error(f"保存用户 {user_id} 偏好数据失败: {str(e)}")
            return False
    
    def _save_realtime_signal(self, user_id: str, signal: Dict[str, Any]) -> bool:
        """保存实时解码信号
        
        Args:
            user_id: 用户ID
            signal: 实时解码信号
            
        Returns:
            bool: 保存是否成功
        """
        try:
            self.storage.save_preference_signal(user_id, signal)
            decoder_logger.debug(f"成功保存用户 {user_id} 的实时偏好信号")
            return True
        except Exception as e:
            decoder_logger.error(f"保存用户 {user_id} 实时偏好信号失败: {str(e)}")
            return False
    
    def get_decoded_preferences(self, user_id: str) -> Dict[str, Any]:
        """获取用户已解码的偏好数据
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict[str, Any]: 偏好数据
        """
        try:
            preferences = self.storage.get_user_preferences(user_id)
            if not preferences:
                decoder_logger.debug(f"未找到用户 {user_id} 的已解码偏好，开始解码")
                return self.decode_user_behavior(user_id)
            return preferences
        except Exception as e:
            decoder_logger.error(f"获取用户 {user_id} 偏好数据失败: {str(e)}")
            return {"user_id": user_id, "status": "error", "error": str(e)}


# 模块级函数

_behavior_decoder_instance = None

def get_behavior_decoder() -> BehaviorDecoder:
    """获取行为解码器单例实例
    
    Returns:
        BehaviorDecoder: 行为解码器实例
    """
    global _behavior_decoder_instance
    if _behavior_decoder_instance is None:
        _behavior_decoder_instance = BehaviorDecoder()
    return _behavior_decoder_instance

def decode_user_behavior(user_id: str, days: int = 30) -> Dict[str, Any]:
    """解码用户行为中的偏好信号
    
    Args:
        user_id: 用户ID
        days: 分析的历史天数
        
    Returns:
        Dict[str, Any]: 解码后的偏好信号
    """
    decoder = get_behavior_decoder()
    return decoder.decode_user_behavior(user_id, days)

def decode_realtime_behavior(user_id: str, behavior_event: Dict[str, Any]) -> Dict[str, Any]:
    """实时解码单个用户行为事件
    
    Args:
        user_id: 用户ID
        behavior_event: 行为事件数据
        
    Returns:
        Dict[str, Any]: 实时解码的偏好信号
    """
    decoder = get_behavior_decoder()
    return decoder.decode_realtime_behavior(user_id, behavior_event)

def get_user_preferences(user_id: str) -> Dict[str, Any]:
    """获取用户偏好数据
    
    Args:
        user_id: 用户ID
        
    Returns:
        Dict[str, Any]: 用户偏好数据
    """
    decoder = get_behavior_decoder()
    return decoder.get_decoded_preferences(user_id) 