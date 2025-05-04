#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
用户偏好分析模块

分析用户观看行为和交互数据，发现用户对内容风格、类型和叙事结构的偏好。
"""

import os
import json
import time
from typing import Dict, List, Any, Optional, Tuple, Set, Union
from datetime import datetime
from collections import Counter, defaultdict
import numpy as np
from loguru import logger

from src.utils.log_handler import get_logger
from src.audience.profile_builder import get_user_profile, get_profile_engine

# 配置日志
pref_logger = get_logger("preference_analyzer")

class PreferenceAnalyzer:
    """用户偏好分析器
    
    分析用户对内容类型、风格、叙述结构等元素的偏好，
    为内容个性化推荐和用户体验定制提供数据支持。
    """
    
    def __init__(self):
        """初始化偏好分析器"""
        self.profile_engine = get_profile_engine()
        
        # 偏好分析维度
        self.preference_dimensions = [
            "genre",        # 内容类型
            "narrative",    # 叙述风格
            "pace",         # 节奏偏好
            "visuals",      # 视觉风格
            "audio",        # 音频风格
            "complexity",   # 复杂度
            "emotional",    # 情感偏好
            "themes"        # 主题偏好
        ]
        
        # 偏好强度分级
        self.preference_strengths = [
            "very_strong",  # 极强偏好
            "strong",       # 强偏好
            "moderate",     # 中等偏好
            "slight",       # 轻微偏好
            "neutral",      # 中立
            "slight_aversion", # 轻微厌恶
            "aversion"      # 厌恶
        ]
        
        # 偏好时间衰减因子 - 决定近期行为的重要性
        self.recency_decay_factor = 0.9  # 每过去一个时间单位，重要性衰减10%
        
        pref_logger.info("用户偏好分析器初始化完成")
    
    def analyze_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """分析用户偏好
        
        综合分析用户在各个维度上的内容偏好。
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict[str, Any]: 用户偏好分析结果
        """
        pref_logger.info(f"开始分析用户 {user_id} 的内容偏好")
        
        # 获取用户画像
        profile = get_user_profile(user_id)
        if not profile:
            pref_logger.warning(f"用户 {user_id} 没有有效的用户画像，无法分析偏好")
            return {"user_id": user_id, "preferences": {}, "status": "no_profile"}
        
        # 分析各个维度的偏好
        genre_prefs = self._analyze_genre_preferences(profile)
        narrative_prefs = self._analyze_narrative_preferences(profile)
        pace_prefs = self._analyze_pace_preferences(profile)
        visual_prefs = self._analyze_visual_preferences(profile)
        audio_prefs = self._analyze_audio_preferences(profile)
        complexity_prefs = self._analyze_complexity_preferences(profile)
        emotional_prefs = self._analyze_emotional_preferences(profile)
        theme_prefs = self._analyze_theme_preferences(profile)
        
        # 组合偏好结果
        preferences = {
            "user_id": user_id,
            "genre": genre_prefs,
            "narrative": narrative_prefs,
            "pace": pace_prefs,
            "visuals": visual_prefs,
            "audio": audio_prefs,
            "complexity": complexity_prefs,
            "emotional": emotional_prefs,
            "themes": theme_prefs,
            "analyzed_at": datetime.now().isoformat(),
            "status": "success"
        }
        
        # 计算整体偏好总结
        preferences["summary"] = self._summarize_preferences(preferences)
        
        pref_logger.info(f"用户 {user_id} 的偏好分析完成")
        return preferences
    
    def _analyze_genre_preferences(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """分析用户对内容类型的偏好
        
        Args:
            profile: 用户画像
            
        Returns:
            Dict[str, Any]: 内容类型偏好
        """
        # 初始化结果
        genre_preferences = {
            "favorites": [],
            "aversions": [],
            "strength_map": {},
            "confidence": 0.0
        }
        
        # 从行为数据中提取体裁偏好
        behavior = profile.get("behavior_patterns", {})
        genre_prefs = behavior.get("genre_preferences", {})
        
        if not genre_prefs:
            genre_preferences["confidence"] = 0.0
            return genre_preferences
        
        # 计算总观看次数
        total_views = sum(genre_prefs.values())
        if total_views == 0:
            genre_preferences["confidence"] = 0.0
            return genre_preferences
        
        # 计算每个体裁的占比
        strength_map = {}
        for genre, count in genre_prefs.items():
            ratio = count / total_views
            
            # 确定偏好强度
            if ratio >= 0.3:
                strength = "very_strong"
            elif ratio >= 0.2:
                strength = "strong"
            elif ratio >= 0.1:
                strength = "moderate"
            elif ratio >= 0.05:
                strength = "slight"
            else:
                strength = "neutral"
            
            strength_map[genre] = {
                "ratio": round(ratio, 4),
                "strength": strength,
                "view_count": count
            }
        
        # 排序并获取最喜欢的体裁
        sorted_genres = sorted(strength_map.items(), key=lambda x: x[1]["ratio"], reverse=True)
        favorites = [genre for genre, data in sorted_genres if data["strength"] in ["very_strong", "strong", "moderate"]]
        
        # 确定不喜欢的体裁（假设有丢弃行为数据）
        aversions = []
        if "skipped_genres" in behavior:
            for genre, data in behavior["skipped_genres"].items():
                if data.get("skip_rate", 0) > 0.7:  # 如果跳过率超过70%
                    aversions.append(genre)
                    strength_map[genre] = {
                        "ratio": 0,
                        "strength": "aversion",
                        "skip_rate": data.get("skip_rate", 0)
                    }
        
        # 填充结果
        genre_preferences["favorites"] = favorites[:5]  # 最多5个最爱体裁
        genre_preferences["aversions"] = aversions
        genre_preferences["strength_map"] = strength_map
        
        # 计算置信度 - 基于数据量和一致性
        data_volume_confidence = min(1.0, total_views / 30)  # 至少30次观看达到最高置信度
        
        # 一致性 - 检查前几个体裁的比例是否明显高于其他
        consistency = 0.0
        if favorites:
            top_ratios = [strength_map[genre]["ratio"] for genre in favorites[:3] if genre in strength_map]
            if top_ratios:
                avg_top = sum(top_ratios) / len(top_ratios)
                all_ratios = [data["ratio"] for data in strength_map.values() if "ratio" in data]
                avg_all = sum(all_ratios) / len(all_ratios) if all_ratios else 0
                
                if avg_all > 0:
                    consistency = min(1.0, (avg_top / avg_all - 1) * 2)  # 比例越大，一致性越高
        
        genre_preferences["confidence"] = round((data_volume_confidence * 0.7 + consistency * 0.3), 2)
        
        return genre_preferences 
    
    def _analyze_narrative_preferences(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """分析用户对叙事风格的偏好
        
        Args:
            profile: 用户画像
            
        Returns:
            Dict[str, Any]: 叙事风格偏好
        """
        # 初始化结果
        narrative_preferences = {
            "preferred_styles": [],
            "strength_map": {},
            "confidence": 0.0
        }
        
        # 从用户行为中提取叙事偏好
        view_heatmap = profile.get("view_heatmap", {})
        behavior = profile.get("behavior_patterns", {})
        
        # 如果有直接的叙事偏好数据
        if "narrative_preferences" in behavior:
            narrative_prefs = behavior.get("narrative_preferences", {})
            
            # 计算总值
            total_value = sum(narrative_prefs.values())
            if total_value == 0:
                narrative_preferences["confidence"] = 0.0
                return narrative_preferences
            
            # 计算每种叙事风格的比例和强度
            strength_map = {}
            for style, value in narrative_prefs.items():
                ratio = value / total_value
                
                # 确定偏好强度
                if ratio >= 0.3:
                    strength = "very_strong"
                elif ratio >= 0.2:
                    strength = "strong"
                elif ratio >= 0.1:
                    strength = "moderate"
                elif ratio >= 0.05:
                    strength = "slight"
                else:
                    strength = "neutral"
                
                strength_map[style] = {
                    "ratio": round(ratio, 4),
                    "strength": strength,
                    "count": value
                }
            
            # 排序并获取首选叙事风格
            sorted_styles = sorted(strength_map.items(), key=lambda x: x[1]["ratio"], reverse=True)
            preferred_styles = [style for style, data in sorted_styles 
                               if data["strength"] in ["very_strong", "strong", "moderate"]]
            
            narrative_preferences["preferred_styles"] = preferred_styles[:3]
            narrative_preferences["strength_map"] = strength_map
            narrative_preferences["confidence"] = min(1.0, total_value / 20)  # 至少20个数据点达到最高置信度
            
            return narrative_preferences
        
        # 如果没有直接数据，从内容热图推断
        hotspots = view_heatmap.get("hotspots", [])
        if not hotspots:
            narrative_preferences["confidence"] = 0.0
            return narrative_preferences
        
        # 分析热点数据，尝试推断叙事偏好
        # 这里只是一个简化的推断逻辑示例
        narrative_types = defaultdict(int)
        
        # 根据热点模式推断叙事偏好
        for hotspot in hotspots:
            # 这里假设我们有一些方法来确定热点位置的叙事类型
            # 实际实现中，可能需要结合内容元数据或者内容分析
            content_id = hotspot.get("content_id")
            timestamp = hotspot.get("timestamp")
            
            # 这里只是一个示例逻辑，实际上需要更复杂的推断
            if content_id:
                # 假设我们可以获取这个时间点的内容叙事类型
                # narrative_type = get_narrative_type_at_timestamp(content_id, timestamp)
                # narrative_types[narrative_type] += 1
                
                # 简化处理，随机分配一些叙事类型
                import random
                narrative_type = random.choice(["linear", "non_linear", "character_driven", 
                                               "plot_driven", "mystery", "action", "drama"])
                narrative_types[narrative_type] += 1
        
        # 如果有推断的叙事类型数据
        if narrative_types:
            total_hotspots = sum(narrative_types.values())
            
            # 计算每种叙事类型的比例和强度
            strength_map = {}
            for style, count in narrative_types.items():
                ratio = count / total_hotspots
                
                # 确定偏好强度
                if ratio >= 0.3:
                    strength = "strong"
                elif ratio >= 0.15:
                    strength = "moderate"
                elif ratio >= 0.05:
                    strength = "slight"
                else:
                    strength = "neutral"
                
                strength_map[style] = {
                    "ratio": round(ratio, 4),
                    "strength": strength,
                    "count": count
                }
            
            # 排序并获取首选叙事风格
            sorted_styles = sorted(strength_map.items(), key=lambda x: x[1]["ratio"], reverse=True)
            preferred_styles = [style for style, data in sorted_styles 
                               if data["strength"] in ["strong", "moderate"]]
            
            narrative_preferences["preferred_styles"] = preferred_styles[:3]
            narrative_preferences["strength_map"] = strength_map
            
            # 置信度较低，因为这是基于推断
            narrative_preferences["confidence"] = min(0.7, total_hotspots / 30)
        
        return narrative_preferences
    
    def _analyze_pace_preferences(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """分析用户对内容节奏的偏好
        
        Args:
            profile: 用户画像
            
        Returns:
            Dict[str, Any]: 节奏偏好
        """
        # 初始化结果
        pace_preferences = {
            "preferred_pace": "moderate",
            "skip_behavior": {},
            "engagement_by_pace": {},
            "confidence": 0.0
        }
        
        # 从用户行为中提取节奏偏好
        behavior = profile.get("behavior_patterns", {})
        view_heatmap = profile.get("view_heatmap", {})
        
        # 分析跳过行为
        skipped_sections = view_heatmap.get("skipped_sections", [])
        if skipped_sections:
            # 计算跳过的总时长
            total_skipped_duration = sum(section.get("end", 0) - section.get("start", 0) 
                                        for section in skipped_sections)
            
            # 跳过行为可能表明用户不喜欢慢节奏
            pace_preferences["skip_behavior"] = {
                "total_skips": len(skipped_sections),
                "total_skipped_duration": total_skipped_duration,
                "avg_skip_duration": total_skipped_duration / len(skipped_sections) if skipped_sections else 0
            }
        
        # 如果有直接的节奏偏好数据
        if "pace_preferences" in behavior:
            pace_prefs = behavior.get("pace_preferences", {})
            
            if pace_prefs:
                # 按照观看完成率排序
                pace_by_completion = sorted(pace_prefs.items(), 
                                           key=lambda x: x[1].get("completion_rate", 0), 
                                           reverse=True)
                
                # 第一个是首选节奏
                if pace_by_completion:
                    pace_preferences["preferred_pace"] = pace_by_completion[0][0]
                
                # 记录不同节奏的参与度
                engagement_by_pace = {}
                for pace, data in pace_prefs.items():
                    engagement_by_pace[pace] = {
                        "completion_rate": data.get("completion_rate", 0),
                        "view_count": data.get("view_count", 0),
                        "avg_view_time": data.get("avg_view_time", 0)
                    }
                
                pace_preferences["engagement_by_pace"] = engagement_by_pace
                
                # 计算置信度 - 基于数据量
                total_views = sum(data.get("view_count", 0) for data in pace_prefs.values())
                pace_preferences["confidence"] = min(1.0, total_views / 20)
                
                return pace_preferences
        
        # 如果没有直接数据，尝试从内容观看行为推断
        completion_by_content = behavior.get("completion_by_content", {})
        if completion_by_content:
            # 假设我们有一些方法来确定内容的节奏类型
            # 实际实现中，需要结合内容元数据
            pace_completion_rates = defaultdict(list)
            
            for content_id, data in completion_by_content.items():
                completion_rate = data.get("completion_rate", 0)
                
                # 获取内容节奏类型（这里需要实际实现）
                # pace_type = get_content_pace(content_id)
                
                # 简化处理，随机分配一些节奏类型
                import random
                pace_type = random.choice(["slow", "moderate", "fast", "variable"])
                
                pace_completion_rates[pace_type].append(completion_rate)
            
            # 计算每种节奏类型的平均完成率
            engagement_by_pace = {}
            for pace, rates in pace_completion_rates.items():
                avg_rate = sum(rates) / len(rates) if rates else 0
                engagement_by_pace[pace] = {
                    "completion_rate": round(avg_rate, 3),
                    "view_count": len(rates)
                }
            
            # 按照完成率排序，找出最高的
            sorted_paces = sorted(engagement_by_pace.items(), 
                                 key=lambda x: x[1]["completion_rate"], 
                                 reverse=True)
            
            if sorted_paces:
                pace_preferences["preferred_pace"] = sorted_paces[0][0]
            
            pace_preferences["engagement_by_pace"] = engagement_by_pace
            
            # 置信度适中，因为这是基于推断
            total_samples = sum(len(rates) for rates in pace_completion_rates.values())
            pace_preferences["confidence"] = min(0.8, total_samples / 15)
        
        # 结合跳过行为进行调整
        if "skip_behavior" in pace_preferences and pace_preferences["skip_behavior"]:
            skip_ratio = pace_preferences["skip_behavior"]["total_skips"] / 10  # 每10次跳过调整一次
            
            # 如果跳过行为显著，可能偏好更快节奏
            if skip_ratio > 0.5 and pace_preferences["preferred_pace"] == "slow":
                pace_preferences["preferred_pace"] = "moderate"
            elif skip_ratio > 1.0 and pace_preferences["preferred_pace"] in ["slow", "moderate"]:
                pace_preferences["preferred_pace"] = "fast"
        
        return pace_preferences
    
    def _analyze_visual_preferences(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """分析用户对视觉风格的偏好
        
        Args:
            profile: 用户画像
            
        Returns:
            Dict[str, Any]: 视觉风格偏好
        """
        # 初始化结果
        visual_preferences = {
            "preferred_styles": [],
            "strength_map": {},
            "confidence": 0.0
        }
        
        # 从用户行为中提取视觉偏好
        view_heatmap = profile.get("view_heatmap", {})
        behavior = profile.get("behavior_patterns", {})
        
        # 如果有直接的视觉偏好数据
        if "visual_preferences" in behavior:
            visual_prefs = behavior.get("visual_preferences", {})
            
            # 计算总值
            total_value = sum(visual_prefs.values())
            if total_value == 0:
                visual_preferences["confidence"] = 0.0
                return visual_preferences
            
            # 计算每种视觉风格的比例和强度
            strength_map = {}
            for style, value in visual_prefs.items():
                ratio = value / total_value
                
                # 确定偏好强度
                if ratio >= 0.3:
                    strength = "very_strong"
                elif ratio >= 0.2:
                    strength = "strong"
                elif ratio >= 0.1:
                    strength = "moderate"
                elif ratio >= 0.05:
                    strength = "slight"
                else:
                    strength = "neutral"
                
                strength_map[style] = {
                    "ratio": round(ratio, 4),
                    "strength": strength,
                    "count": value
                }
            
            # 排序并获取首选视觉风格
            sorted_styles = sorted(strength_map.items(), key=lambda x: x[1]["ratio"], reverse=True)
            preferred_styles = [style for style, data in sorted_styles 
                               if data["strength"] in ["very_strong", "strong", "moderate"]]
            
            visual_preferences["preferred_styles"] = preferred_styles[:3]
            visual_preferences["strength_map"] = strength_map
            visual_preferences["confidence"] = min(1.0, total_value / 20)  # 至少20个数据点达到最高置信度
            
            return visual_preferences
        
        # 如果没有直接数据，从内容热图推断
        hotspots = view_heatmap.get("hotspots", [])
        if not hotspots:
            visual_preferences["confidence"] = 0.0
            return visual_preferences
        
        # 分析热点数据，尝试推断视觉偏好
        # 这里只是一个简化的推断逻辑示例
        visual_types = defaultdict(int)
        
        # 根据热点模式推断视觉偏好
        for hotspot in hotspots:
            # 这里假设我们有一些方法来确定热点位置的视觉类型
            # 实际实现中，可能需要结合内容元数据或者内容分析
            content_id = hotspot.get("content_id")
            timestamp = hotspot.get("timestamp")
            
            # 这里只是一个示例逻辑，实际上需要更复杂的推断
            if content_id:
                # 假设我们可以获取这个时间点的内容视觉类型
                # visual_type = get_visual_type_at_timestamp(content_id, timestamp)
                # visual_types[visual_type] += 1
                
                # 简化处理，随机分配一些视觉类型
                import random
                visual_type = random.choice(["abstract", "realistic", "cartoon", "anime", "digital", "hand_drawn"])
                visual_types[visual_type] += 1
        
        # 如果有推断的视觉类型数据
        if visual_types:
            total_hotspots = sum(visual_types.values())
            
            # 计算每种视觉类型的比例和强度
            strength_map = {}
            for style, count in visual_types.items():
                ratio = count / total_hotspots
                
                # 确定偏好强度
                if ratio >= 0.3:
                    strength = "strong"
                elif ratio >= 0.15:
                    strength = "moderate"
                elif ratio >= 0.05:
                    strength = "slight"
                else:
                    strength = "neutral"
                
                strength_map[style] = {
                    "ratio": round(ratio, 4),
                    "strength": strength,
                    "count": count
                }
            
            # 排序并获取首选视觉风格
            sorted_styles = sorted(strength_map.items(), key=lambda x: x[1]["ratio"], reverse=True)
            preferred_styles = [style for style, data in sorted_styles 
                               if data["strength"] in ["strong", "moderate"]]
            
            visual_preferences["preferred_styles"] = preferred_styles[:3]
            visual_preferences["strength_map"] = strength_map
            
            # 置信度较低，因为这是基于推断
            visual_preferences["confidence"] = min(0.7, total_hotspots / 30)
        
        return visual_preferences
    
    def _analyze_audio_preferences(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """分析用户对音频风格的偏好
        
        Args:
            profile: 用户画像
            
        Returns:
            Dict[str, Any]: 音频风格偏好
        """
        # 初始化结果
        audio_preferences = {
            "preferred_styles": [],
            "strength_map": {},
            "confidence": 0.0
        }
        
        # 从用户行为中提取音频偏好
        behavior = profile.get("behavior_patterns", {})
        view_heatmap = profile.get("view_heatmap", {})
        
        # 如果有直接的音频偏好数据
        if "audio_preferences" in behavior:
            audio_prefs = behavior.get("audio_preferences", {})
            
            # 计算总值
            total_value = sum(audio_prefs.values())
            if total_value == 0:
                audio_preferences["confidence"] = 0.0
                return audio_preferences
            
            # 计算每种音频风格的比例和强度
            strength_map = {}
            for style, value in audio_prefs.items():
                ratio = value / total_value
                
                # 确定偏好强度
                if ratio >= 0.3:
                    strength = "very_strong"
                elif ratio >= 0.2:
                    strength = "strong"
                elif ratio >= 0.1:
                    strength = "moderate"
                elif ratio >= 0.05:
                    strength = "slight"
                else:
                    strength = "neutral"
                
                strength_map[style] = {
                    "ratio": round(ratio, 4),
                    "strength": strength,
                    "count": value
                }
            
            # 排序并获取首选音频风格
            sorted_styles = sorted(strength_map.items(), key=lambda x: x[1]["ratio"], reverse=True)
            preferred_styles = [style for style, data in sorted_styles 
                               if data["strength"] in ["very_strong", "strong", "moderate"]]
            
            audio_preferences["preferred_styles"] = preferred_styles[:3]
            audio_preferences["strength_map"] = strength_map
            audio_preferences["confidence"] = min(1.0, total_value / 20)  # 至少20个数据点达到最高置信度
            
            return audio_preferences
        
        # 如果没有直接数据，从内容热图推断
        hotspots = view_heatmap.get("hotspots", [])
        if not hotspots:
            audio_preferences["confidence"] = 0.0
            return audio_preferences
        
        # 分析热点数据，尝试推断音频偏好
        # 这里只是一个简化的推断逻辑示例
        audio_types = defaultdict(int)
        
        # 根据热点模式推断音频偏好
        for hotspot in hotspots:
            # 这里假设我们有一些方法来确定热点位置的音频类型
            # 实际实现中，可能需要结合内容元数据或者内容分析
            content_id = hotspot.get("content_id")
            timestamp = hotspot.get("timestamp")
            
            # 这里只是一个示例逻辑，实际上需要更复杂的推断
            if content_id:
                # 假设我们可以获取这个时间点的内容音频类型
                # audio_type = get_audio_type_at_timestamp(content_id, timestamp)
                # audio_types[audio_type] += 1
                
                # 简化处理，随机分配一些音频类型
                import random
                audio_type = random.choice(["classical", "rock", "pop", "jazz", "electronic", "hip_hop"])
                audio_types[audio_type] += 1
        
        # 如果有推断的音频类型数据
        if audio_types:
            total_hotspots = sum(audio_types.values())
            
            # 计算每种音频类型的比例和强度
            strength_map = {}
            for style, count in audio_types.items():
                ratio = count / total_hotspots
                
                # 确定偏好强度
                if ratio >= 0.3:
                    strength = "strong"
                elif ratio >= 0.15:
                    strength = "moderate"
                elif ratio >= 0.05:
                    strength = "slight"
                else:
                    strength = "neutral"
                
                strength_map[style] = {
                    "ratio": round(ratio, 4),
                    "strength": strength,
                    "count": count
                }
            
            # 排序并获取首选音频风格
            sorted_styles = sorted(strength_map.items(), key=lambda x: x[1]["ratio"], reverse=True)
            preferred_styles = [style for style, data in sorted_styles 
                               if data["strength"] in ["strong", "moderate"]]
            
            audio_preferences["preferred_styles"] = preferred_styles[:3]
            audio_preferences["strength_map"] = strength_map
            
            # 置信度较低，因为这是基于推断
            audio_preferences["confidence"] = min(0.7, total_hotspots / 30)
        
        return audio_preferences
    
    def _analyze_complexity_preferences(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """分析用户对内容复杂度的偏好
        
        Args:
            profile: 用户画像
            
        Returns:
            Dict[str, Any]: 内容复杂度偏好
        """
        # 初始化结果
        complexity_preferences = {
            "preferred_complexity": "moderate",
            "strength_map": {},
            "confidence": 0.0
        }
        
        # 从用户行为中提取复杂度偏好
        behavior = profile.get("behavior_patterns", {})
        view_heatmap = profile.get("view_heatmap", {})
        
        # 分析复杂度偏好
        complexity_prefs = behavior.get("complexity_preferences", {})
        
        if not complexity_prefs:
            complexity_preferences["confidence"] = 0.0
            return complexity_preferences
        
        # 计算总值
        total_value = sum(complexity_prefs.values())
        if total_value == 0:
            complexity_preferences["confidence"] = 0.0
            return complexity_preferences
        
        # 计算每种复杂度的比例和强度
        strength_map = {}
        for complexity, value in complexity_prefs.items():
            ratio = value / total_value
            
            # 确定偏好强度
            if ratio >= 0.3:
                strength = "very_strong"
            elif ratio >= 0.2:
                strength = "strong"
            elif ratio >= 0.1:
                strength = "moderate"
            elif ratio >= 0.05:
                strength = "slight"
            else:
                strength = "neutral"
            
            strength_map[complexity] = {
                "ratio": round(ratio, 4),
                "strength": strength,
                "count": value
            }
        
        # 排序并获取首选复杂度
        sorted_complexities = sorted(strength_map.items(), key=lambda x: x[1]["ratio"], reverse=True)
        preferred_complexities = [complexity for complexity, data in sorted_complexities 
                                   if data["strength"] in ["very_strong", "strong", "moderate"]]
        
        complexity_preferences["preferred_complexity"] = preferred_complexities[0]
        complexity_preferences["strength_map"] = strength_map
        complexity_preferences["confidence"] = min(1.0, total_value / 20)  # 至少20个数据点达到最高置信度
        
        return complexity_preferences
    
    def _analyze_emotional_preferences(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """分析用户对情感的偏好
        
        Args:
            profile: 用户画像
            
        Returns:
            Dict[str, Any]: 情感偏好
        """
        # 初始化结果
        emotional_preferences = {
            "preferred_emotions": [],
            "strength_map": {},
            "confidence": 0.0
        }
        
        # 从用户行为中提取情感偏好
        behavior = profile.get("behavior_patterns", {})
        view_heatmap = profile.get("view_heatmap", {})
        
        # 分析情感偏好
        emotional_prefs = behavior.get("emotional_preferences", {})
        
        if not emotional_prefs:
            emotional_preferences["confidence"] = 0.0
            return emotional_preferences
        
        # 计算总值
        total_value = sum(emotional_prefs.values())
        if total_value == 0:
            emotional_preferences["confidence"] = 0.0
            return emotional_preferences
        
        # 计算每种情感的比例和强度
        strength_map = {}
        for emotion, value in emotional_prefs.items():
            ratio = value / total_value
            
            # 确定偏好强度
            if ratio >= 0.3:
                strength = "very_strong"
            elif ratio >= 0.2:
                strength = "strong"
            elif ratio >= 0.1:
                strength = "moderate"
            elif ratio >= 0.05:
                strength = "slight"
            else:
                strength = "neutral"
            
            strength_map[emotion] = {
                "ratio": round(ratio, 4),
                "strength": strength,
                "count": value
            }
        
        # 排序并获取首选情感
        sorted_emotions = sorted(strength_map.items(), key=lambda x: x[1]["ratio"], reverse=True)
        preferred_emotions = [emotion for emotion, data in sorted_emotions 
                               if data["strength"] in ["very_strong", "strong", "moderate"]]
        
        emotional_preferences["preferred_emotions"] = preferred_emotions[:3]
        emotional_preferences["strength_map"] = strength_map
        emotional_preferences["confidence"] = min(1.0, total_value / 20)  # 至少20个数据点达到最高置信度
        
        return emotional_preferences
    
    def _analyze_theme_preferences(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """分析用户对主题的偏好
        
        Args:
            profile: 用户画像
            
        Returns:
            Dict[str, Any]: 主题偏好
        """
        # 初始化结果
        theme_preferences = {
            "preferred_themes": [],
            "strength_map": {},
            "confidence": 0.0
        }
        
        # 从用户行为中提取主题偏好
        behavior = profile.get("behavior_patterns", {})
        view_heatmap = profile.get("view_heatmap", {})
        
        # 分析主题偏好
        theme_prefs = behavior.get("theme_preferences", {})
        
        if not theme_prefs:
            theme_preferences["confidence"] = 0.0
            return theme_preferences
        
        # 计算总值
        total_value = sum(theme_prefs.values())
        if total_value == 0:
            theme_preferences["confidence"] = 0.0
            return theme_preferences
        
        # 计算每种主题的比例和强度
        strength_map = {}
        for theme, value in theme_prefs.items():
            ratio = value / total_value
            
            # 确定偏好强度
            if ratio >= 0.3:
                strength = "very_strong"
            elif ratio >= 0.2:
                strength = "strong"
            elif ratio >= 0.1:
                strength = "moderate"
            elif ratio >= 0.05:
                strength = "slight"
            else:
                strength = "neutral"
            
            strength_map[theme] = {
                "ratio": round(ratio, 4),
                "strength": strength,
                "count": value
            }
        
        # 排序并获取首选主题
        sorted_themes = sorted(strength_map.items(), key=lambda x: x[1]["ratio"], reverse=True)
        preferred_themes = [theme for theme, data in sorted_themes 
                               if data["strength"] in ["very_strong", "strong", "moderate"]]
        
        theme_preferences["preferred_themes"] = preferred_themes[:3]
        theme_preferences["strength_map"] = strength_map
        theme_preferences["confidence"] = min(1.0, total_value / 20)  # 至少20个数据点达到最高置信度
        
        return theme_preferences
    
    def _summarize_preferences(self, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """总结用户偏好，创建整体偏好概览
        
        Args:
            preferences: 各个维度的偏好数据
            
        Returns:
            Dict[str, Any]: 偏好总结
        """
        # 初始化总结
        summary = {
            "top_preferences": [],
            "overall_profile": {},
            "confidence_scores": {}
        }
        
        # 提取各维度的置信度
        for dimension in self.preference_dimensions:
            if dimension in preferences:
                conf = preferences[dimension].get("confidence", 0.0)
                summary["confidence_scores"][dimension] = round(conf, 2)
        
        # 计算总体置信度
        if summary["confidence_scores"]:
            summary["overall_confidence"] = round(
                sum(summary["confidence_scores"].values()) / len(summary["confidence_scores"]), 2)
        else:
            summary["overall_confidence"] = 0.0
        
        # 获取每个维度的首选项目
        dimension_top_items = {}
        for dimension in self.preference_dimensions:
            if dimension in preferences:
                pref_data = preferences[dimension]
                
                # 获取该维度的首选项目
                if dimension == "genre":
                    top_items = pref_data.get("favorites", [])
                elif dimension == "pace":
                    top_items = [pref_data.get("preferred_pace", "moderate")]
                elif dimension == "complexity":
                    top_items = [pref_data.get("preferred_complexity", "moderate")]
                elif dimension == "emotional":
                    top_items = pref_data.get("preferred_emotions", [])
                elif dimension == "themes":
                    top_items = pref_data.get("preferred_themes", [])
                else:
                    top_items = pref_data.get("preferred_styles", [])
                
                if top_items:
                    dimension_top_items[dimension] = top_items
        
        # 找出最高置信度的维度和其首选项目
        if dimension_top_items:
            # 按置信度排序维度
            sorted_dimensions = sorted(
                summary["confidence_scores"].items(), 
                key=lambda x: x[1], 
                reverse=True
            )
            
            # 获取前3个最高置信度维度的首选项目
            top_preferences = []
            for dimension, _ in sorted_dimensions[:3]:
                if dimension in dimension_top_items and dimension_top_items[dimension]:
                    # 取每个维度的第一个首选项
                    item = dimension_top_items[dimension][0]
                    top_preferences.append({
                        "dimension": dimension,
                        "item": item,
                        "confidence": summary["confidence_scores"][dimension]
                    })
            
            summary["top_preferences"] = top_preferences
        
        # 创建整体用户画像描述
        profile_descriptors = []
        
        # 添加体裁偏好
        if "genre" in preferences and preferences["genre"].get("favorites"):
            favorite_genre = preferences["genre"]["favorites"][0]
            profile_descriptors.append(f"{favorite_genre}_fan")
        
        # 添加叙事偏好
        if "narrative" in preferences and preferences["narrative"].get("preferred_styles"):
            narrative_style = preferences["narrative"]["preferred_styles"][0]
            profile_descriptors.append(f"{narrative_style}_narrative")
        
        # 添加节奏偏好
        if "pace" in preferences:
            pace = preferences["pace"].get("preferred_pace")
            if pace:
                profile_descriptors.append(f"{pace}_pace")
        
        # 添加复杂度偏好
        if "complexity" in preferences:
            complexity = preferences["complexity"].get("preferred_complexity")
            if complexity:
                profile_descriptors.append(f"{complexity}_complexity")
        
        # 添加情感偏好
        if "emotional" in preferences and preferences["emotional"].get("preferred_emotions"):
            emotion = preferences["emotional"]["preferred_emotions"][0]
            profile_descriptors.append(f"{emotion}_emotional")
        
        summary["overall_profile"] = profile_descriptors
        
        return summary

# 模块级函数

_preference_analyzer_instance = None

def get_preference_analyzer() -> PreferenceAnalyzer:
    """获取偏好分析器单例实例
    
    Returns:
        PreferenceAnalyzer: 偏好分析器实例
    """
    global _preference_analyzer_instance
    if _preference_analyzer_instance is None:
        _preference_analyzer_instance = PreferenceAnalyzer()
    return _preference_analyzer_instance

def analyze_user_preferences(user_id: str) -> Dict[str, Any]:
    """分析用户内容偏好
    
    Args:
        user_id: 用户ID
        
    Returns:
        Dict[str, Any]: 用户偏好分析结果
    """
    analyzer = get_preference_analyzer()
    return analyzer.analyze_user_preferences(user_id)

def get_user_genre_preferences(user_id: str) -> Dict[str, Any]:
    """获取用户体裁偏好
    
    Args:
        user_id: 用户ID
        
    Returns:
        Dict[str, Any]: 用户体裁偏好
    """
    analyzer = get_preference_analyzer()
    preferences = analyzer.analyze_user_preferences(user_id)
    return preferences.get("genre", {})

def get_user_style_preferences(user_id: str) -> Dict[str, Any]:
    """获取用户风格偏好
    
    包括叙事风格、视觉风格和音频风格的综合偏好。
    
    Args:
        user_id: 用户ID
        
    Returns:
        Dict[str, Any]: 用户风格偏好
    """
    analyzer = get_preference_analyzer()
    preferences = analyzer.analyze_user_preferences(user_id)
    
    style_preferences = {
        "narrative": preferences.get("narrative", {}),
        "visuals": preferences.get("visuals", {}),
        "audio": preferences.get("audio", {})
    }
    
    # 计算综合风格偏好
    combined_styles = {}
    for style_type, prefs in style_preferences.items():
        if "strength_map" in prefs:
            for style, data in prefs["strength_map"].items():
                if style not in combined_styles:
                    combined_styles[style] = {
                        "count": 0,
                        "total_ratio": 0.0,
                        "dimensions": []
                    }
                
                combined_styles[style]["count"] += 1
                combined_styles[style]["total_ratio"] += data.get("ratio", 0)
                combined_styles[style]["dimensions"].append(style_type)
    
    # 计算平均比例并排序
    style_ranking = []
    for style, data in combined_styles.items():
        if data["count"] > 0:
            avg_ratio = data["total_ratio"] / data["count"]
            style_ranking.append({
                "style": style,
                "avg_ratio": avg_ratio,
                "dimensions": data["dimensions"],
                "dimension_count": data["count"]
            })
    
    # 排序获取前几名
    sorted_styles = sorted(style_ranking, key=lambda x: x["avg_ratio"], reverse=True)
    
    style_preferences["combined"] = {
        "top_styles": sorted_styles[:5],
        "all_styles": sorted_styles
    }
    
    return style_preferences 