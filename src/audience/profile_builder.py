#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
用户画像构建引擎

基于用户行为、偏好和使用环境构建多维度用户画像，用于个性化内容推荐和用户体验优化。
特别针对短剧混剪项目优化，提供剪辑偏好与习惯分析。
"""

import os
import json
import time
import hashlib
import logging
from typing import Dict, List, Any, Optional, Tuple, Set, Union
from datetime import datetime
import numpy as np
from loguru import logger

from src.utils.log_handler import get_logger
from src.data.storage_manager import get_storage_manager

# 配置日志
profile_logger = get_logger("user_profile")

class UserProfileEngine:
    """多维度用户画像构建引擎
    
    基于用户的行为数据、内容偏好、设备使用情况和混剪喜好等多维度信息，
    构建全面的用户画像，用于个性化内容推荐和混剪模板优化。
    """
    
    def __init__(self):
        """初始化用户画像引擎"""
        # 用户画像维度定义
        self.dimensions = [
            'demographic',     # 年龄/性别/地域
            'behavioral',      # 观看时长/留存点
            'emotional',       # 情感共鸣点
            'technical',       # 设备类型/网络环境
            'content',         # 内容偏好
            'editing_style',   # 剪辑风格偏好
            'narrative',       # 叙事结构偏好
            'pacing',          # 节奏偏好
        ]
        
        # 获取存储管理器
        self.storage = get_storage_manager()
        
        # 用户画像缓存
        self.profile_cache = {}
        
        # 数据采样率配置
        self.sampling_rate = 0.1  # 默认采样10%的行为数据
        
        # 特征重要性权重
        self.feature_weights = {
            'content_preference': 2.0,    # 内容类型偏好权重
            'pacing_preference': 1.8,     # 节奏偏好权重
            'emotional_arc': 1.7,         # 情感曲线偏好
            'narrative_structure': 1.5,   # 叙事结构偏好
            'technical_constraints': 1.0, # 技术约束
            'editing_transitions': 1.2,   # 转场偏好
        }
        
        profile_logger.info("用户画像构建引擎初始化完成")
    
    def create_profile(self, user_id: str) -> Dict[str, Any]:
        """构建用户多维度画像
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict[str, Any]: 多维度用户画像
        """
        profile_logger.info(f"开始构建用户 {user_id} 的多维度画像")
        
        # 基本信息
        basic_info = self._get_demographics(user_id)
        
        # 内容偏好分析
        content_preferences = self._analyze_content_preferences(user_id)
        
        # 情感响应特征
        emotion_response = self._analyze_emotion_preferences(user_id)
        
        # 设备和网络约束
        device_constraints = self._get_device_specs(user_id)
        
        # 剪辑风格偏好
        editing_preferences = self._analyze_editing_preferences(user_id)
        
        # 叙事结构偏好
        narrative_preferences = self._analyze_narrative_preferences(user_id)
        
        # 节奏偏好
        pacing_preferences = self._analyze_pacing_preferences(user_id)
        
        # 组装完整画像
        profile = {
            "user_id": user_id,
            "basic_info": basic_info,
            "content_preferences": content_preferences,
            "emotion_response": emotion_response,
            "device_constraints": device_constraints,
            "editing_preferences": editing_preferences,
            "narrative_preferences": narrative_preferences,
            "pacing_preferences": pacing_preferences,
            "created_at": datetime.now().isoformat(),
            "version": "1.0"
        }
        
        # 缓存用户画像
        self.profile_cache[user_id] = profile
        
        # 存储用户画像
        self._save_profile(user_id, profile)
        
        profile_logger.info(f"用户 {user_id} 的多维度画像构建完成")
        return profile

    def _get_demographics(self, user_id: str) -> Dict[str, Any]:
        """获取用户基本人口统计学信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict[str, Any]: 人口统计学信息
        """
        # 尝试从存储中获取用户注册信息
        try:
            user_data = self.storage.get_user_data(user_id)
            if user_data:
                demographic = {
                    "age_group": user_data.get("age_group", "unknown"),
                    "gender": user_data.get("gender", "unknown"),
                    "region": user_data.get("region", "unknown"),
                    "language": user_data.get("language", "zh"),  # 默认中文
                    "registered_since": user_data.get("registration_date", "unknown")
                }
                return demographic
        except Exception as e:
            profile_logger.error(f"获取用户 {user_id} 人口统计信息失败: {str(e)}")
        
        # 如果获取失败，返回默认信息
        return {
            "age_group": "unknown",
            "gender": "unknown",
            "region": "unknown",
            "language": "zh",  # 默认中文
            "registered_since": "unknown"
        }
    
    def _analyze_heatmap(self, user_id: str) -> Dict[str, Any]:
        """分析用户内容观看热图
        
        分析用户观看视频时的停留点、重复观看点，
        构建视频内容兴趣热图。
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict[str, Any]: 内容观看热图分析
        """
        # 获取用户近期观看历史
        view_history = self._get_user_view_history(user_id)
        if not view_history:
            return {"heatmap_data": [], "hotspots": [], "skipped_sections": []}
        
        # 统计观看热点
        hotspots = []
        skipped_sections = []
        heatmap_data = []
        
        # 分析每个观看记录
        for view in view_history:
            content_id = view.get("content_id")
            view_timeline = view.get("timeline", [])
            
            # 如果有时间线数据，分析停留点和跳过点
            if view_timeline:
                # 处理观看热点（停留点）
                for segment in view_timeline:
                    if segment.get("action") == "pause" or segment.get("replay_count", 0) > 1:
                        hotspots.append({
                            "content_id": content_id,
                            "timestamp": segment.get("timestamp"),
                            "duration": segment.get("duration", 0),
                            "replay_count": segment.get("replay_count", 1)
                        })
                
                # 处理跳过区域
                for i in range(1, len(view_timeline)):
                    prev = view_timeline[i-1]
                    curr = view_timeline[i]
                    if curr.get("timestamp") - prev.get("timestamp") > prev.get("duration", 0) + 2:
                        skipped_sections.append({
                            "content_id": content_id,
                            "start": prev.get("timestamp") + prev.get("duration", 0),
                            "end": curr.get("timestamp")
                        })
            
            # 构建热图数据点
            if "play_positions" in view:
                positions = view.get("play_positions", [])
                for pos in positions:
                    heatmap_data.append({
                        "content_id": content_id,
                        "position": pos.get("position"),
                        "duration": pos.get("duration", 0),
                        "event_type": pos.get("event_type", "play")
                    })
        
        return {
            "heatmap_data": heatmap_data,
            "hotspots": hotspots,
            "skipped_sections": skipped_sections,
            "updated_at": datetime.now().isoformat()
        }
    
    def _get_user_view_history(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """获取用户观看历史
        
        Args:
            user_id: 用户ID
            limit: 历史记录数量限制
            
        Returns:
            List[Dict[str, Any]]: 观看历史记录
        """
        try:
            # 从存储中获取用户观看历史
            history = self.storage.get_user_view_history(user_id, limit=limit)
            return history if history else []
        except Exception as e:
            profile_logger.error(f"获取用户 {user_id} 观看历史失败: {str(e)}")
            return [] 

    def _load_biometric_data(self, user_id: str) -> Dict[str, Any]:
        """加载用户生物识别和情感响应数据
        
        加载用户在观看内容时的情感反应数据，如果有可用的
        生物识别或情感测量数据。
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict[str, Any]: 情感响应数据
        """
        # 初始化情感响应数据结构
        emotion_data = {
            "emotional_markers": [],
            "content_resonance": [],
            "emotion_metrics": {
                "engagement": 0.0,
                "joy": 0.0,
                "sadness": 0.0, 
                "surprise": 0.0,
                "fear": 0.0,
                "anger": 0.0
            },
            "has_biometric_data": False
        }
        
        try:
            # 尝试从存储加载情感分析数据
            biometric_data = self.storage.get_user_biometric_data(user_id)
            if not biometric_data:
                return emotion_data
            
            # 标记有可用的生物识别数据
            emotion_data["has_biometric_data"] = True
            
            # 处理情感标记数据
            if "emotional_markers" in biometric_data:
                emotion_data["emotional_markers"] = biometric_data["emotional_markers"]
            
            # 处理内容共鸣点
            if "content_resonance" in biometric_data:
                emotion_data["content_resonance"] = biometric_data["content_resonance"]
            
            # 处理情感量化指标
            if "emotion_metrics" in biometric_data:
                emotion_data["emotion_metrics"] = biometric_data["emotion_metrics"]
            
            return emotion_data
        except Exception as e:
            profile_logger.error(f"加载用户 {user_id} 情感数据失败: {str(e)}")
            return emotion_data
    
    def _get_device_specs(self, user_id: str) -> Dict[str, Any]:
        """获取用户设备规格和技术约束
        
        分析用户设备性能和网络条件，确定技术约束。
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict[str, Any]: 设备规格和技术约束
        """
        # 获取用户设备数据
        device_data = self.storage.get_user_devices(user_id)
        
        # 默认设备约束
        default_constraints = {
            "memory_limit": 4096,  # 默认4GB内存限制
            "cpu_cores": 4,        # 默认4核CPU
            "gpu_available": False, # 默认无GPU
            "network_speed": "medium", # 默认中等网速
            "storage_available": 10240, # 默认10GB存储空间
            "display_resolution": "hd", # 默认高清
            "confidence": 0.5      # 默认中等置信度
        }
        
        if not device_data:
            return default_constraints
        
        # 分析设备能力
        primary_device = device_data.get("primary_device", {})
        
        # 提取设备规格
        memory = primary_device.get("memory_mb", default_constraints["memory_limit"])
        cpu_cores = primary_device.get("cpu_cores", default_constraints["cpu_cores"])
        gpu_available = primary_device.get("gpu_available", default_constraints["gpu_available"])
        network_type = primary_device.get("network_type", "unknown")
        storage = primary_device.get("storage_mb", default_constraints["storage_available"])
        resolution = primary_device.get("screen_resolution", "unknown")
        
        # 推断网络速度
        if network_type == "wifi":
            network_speed = "high"
        elif network_type == "mobile":
            network_speed = "medium"
        elif network_type == "slow-mobile":
            network_speed = "low"
        else:
            network_speed = default_constraints["network_speed"]
        
        # 推断显示分辨率类别
        if resolution != "unknown":
            try:
                width, height = resolution.split("x")
                width, height = int(width), int(height)
                
                if width >= 1920 or height >= 1080:
                    display_resolution = "fullhd"
                elif width >= 1280 or height >= 720:
                    display_resolution = "hd"
                else:
                    display_resolution = "sd"
            except:
                display_resolution = default_constraints["display_resolution"]
        else:
            display_resolution = default_constraints["display_resolution"]
        
        return {
            "memory_limit": memory,
            "cpu_cores": cpu_cores,
            "gpu_available": gpu_available,
            "network_speed": network_speed,
            "storage_available": storage,
            "display_resolution": display_resolution,
            "confidence": 0.9 if primary_device else 0.5  # 如果有设备数据，置信度高
        }
    
    def _analyze_device_capabilities(self, device_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析设备能力，确定其支持的视频质量和功能
        
        Args:
            device_data: 设备数据
            
        Returns:
            Dict[str, Any]: 设备能力分析
        """
        capabilities = {
            "max_resolution": "720p",  # 默认支持720p
            "hdr_support": False,
            "audio_channels": "stereo",
            "adaptive_streaming": True,
            "live_streaming": True,
            "download_support": True
        }
        
        # 根据设备类型和分辨率调整能力
        device_type = device_data.get("device_type", "").lower()
        resolution = device_data.get("screen_resolution", "").lower()
        
        # 分辨率分析
        if resolution:
            try:
                # 尝试从分辨率字符串解析宽高
                if "x" in resolution:
                    width, height = map(int, resolution.split("x"))
                    if width >= 3840 and height >= 2160:
                        capabilities["max_resolution"] = "4K"
                    elif width >= 2560 and height >= 1440:
                        capabilities["max_resolution"] = "2K"
                    elif width >= 1920 and height >= 1080:
                        capabilities["max_resolution"] = "1080p"
                    elif width >= 1280 and height >= 720:
                        capabilities["max_resolution"] = "720p"
                    else:
                        capabilities["max_resolution"] = "480p"
            except:
                pass
        
        # 设备类型分析
        if "tv" in device_type or "television" in device_type:
            capabilities["hdr_support"] = True
            capabilities["audio_channels"] = "surround"
        elif "mobile" in device_type or "phone" in device_type:
            capabilities["download_support"] = True
            capabilities["adaptive_streaming"] = True
        
        # 网络类型分析
        network_type = device_data.get("network_type", "").lower()
        if network_type == "mobile" or network_type == "cellular":
            capabilities["adaptive_streaming"] = True
            if capabilities["max_resolution"] == "4K":
                capabilities["max_resolution"] = "1080p"  # 移动网络下降级
        
        return capabilities 

    def _analyze_behavior_patterns(self, user_id: str) -> Dict[str, Any]:
        """分析用户行为模式特征
        
        分析用户的内容观看行为，包括观看完成率、观看持续时间、
        内容类型偏好等行为特征。
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict[str, Any]: 行为模式分析结果
        """
        # 初始化行为模式数据
        behavior_patterns = {
            "completion_rate": 0.0,
            "avg_session_duration": 0.0,
            "genre_preferences": {},
            "content_type_preferences": {},
            "viewing_sessions": [],
            "engagement_level": "low",
            "binge_watching": False
        }
        
        try:
            # 获取用户行为数据
            behavior_data = self.storage.get_user_behavior_data(user_id, days=30)
            if not behavior_data:
                return behavior_patterns
            
            # 计算平均完成率
            if "completions" in behavior_data and behavior_data["completions"]:
                completion_rates = [item.get("completion_rate", 0) for item in behavior_data["completions"]]
                behavior_patterns["completion_rate"] = sum(completion_rates) / len(completion_rates)
            
            # 计算平均会话时长
            if "sessions" in behavior_data and behavior_data["sessions"]:
                session_durations = [session.get("duration", 0) for session in behavior_data["sessions"]]
                behavior_patterns["avg_session_duration"] = sum(session_durations) / len(session_durations)
                behavior_patterns["viewing_sessions"] = behavior_data["sessions"][:10]  # 最多保留10个会话
            
            # 分析体裁偏好
            if "genre_views" in behavior_data:
                behavior_patterns["genre_preferences"] = behavior_data["genre_views"]
            
            # 分析内容类型偏好
            if "content_types" in behavior_data:
                behavior_patterns["content_type_preferences"] = behavior_data["content_types"]
            
            # 确定参与度级别
            engagement_level = "low"
            avg_completion = behavior_patterns["completion_rate"]
            avg_duration = behavior_patterns["avg_session_duration"]
            
            if avg_completion > 0.8 and avg_duration > 25:
                engagement_level = "high"
            elif avg_completion > 0.5 and avg_duration > 15:
                engagement_level = "medium"
            
            behavior_patterns["engagement_level"] = engagement_level
            
            # 判断是否存在追剧行为
            if "binge_data" in behavior_data:
                behavior_patterns["binge_watching"] = behavior_data["binge_data"].get("is_binger", False)
                if "binge_sessions" in behavior_data["binge_data"]:
                    behavior_patterns["binge_sessions"] = behavior_data["binge_data"]["binge_sessions"]
            
            return behavior_patterns
        except Exception as e:
            profile_logger.error(f"分析用户 {user_id} 行为模式失败: {str(e)}")
            return behavior_patterns
    
    def _analyze_temporal_patterns(self, user_id: str) -> Dict[str, Any]:
        """分析用户时间模式
        
        分析用户的内容观看时间模式，包括一天中的活跃时段、
        一周内的活跃日，以及其他时间相关的特征。
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict[str, Any]: 时间模式分析结果
        """
        # 初始化时间模式数据
        time_patterns = {
            "active_hours": [0] * 24,  # 一天24小时的活跃度统计
            "active_days": [0] * 7,    # 一周7天的活跃度统计
            "peak_hour": 0,
            "peak_day": 0,
            "weekend_vs_weekday": {
                "weekend": 0,
                "weekday": 0
            },
            "morning_vs_evening": {
                "morning": 0,    # 5:00-12:00
                "afternoon": 0,  # 12:00-18:00
                "evening": 0,    # 18:00-23:00
                "night": 0       # 23:00-5:00
            }
        }
        
        try:
            # 获取用户活动时间数据
            temporal_data = self.storage.get_user_temporal_data(user_id, days=30)
            if not temporal_data or "activities" not in temporal_data:
                return time_patterns
            
            activities = temporal_data["activities"]
            
            # 统计每小时活跃度
            hour_counts = [0] * 24
            for activity in activities:
                if "timestamp" in activity:
                    try:
                        dt = datetime.fromisoformat(activity["timestamp"])
                        hour = dt.hour
                        day = dt.weekday()  # 0是周一，6是周日
                        
                        # 更新小时统计
                        hour_counts[hour] += 1
                        
                        # 更新星期统计
                        time_patterns["active_days"][day] += 1
                        
                        # 更新工作日vs周末统计
                        if day < 5:  # 0-4是工作日
                            time_patterns["weekend_vs_weekday"]["weekday"] += 1
                        else:
                            time_patterns["weekend_vs_weekday"]["weekend"] += 1
                        
                        # 更新一天中的时段统计
                        if 5 <= hour < 12:
                            time_patterns["morning_vs_evening"]["morning"] += 1
                        elif 12 <= hour < 18:
                            time_patterns["morning_vs_evening"]["afternoon"] += 1
                        elif 18 <= hour < 23:
                            time_patterns["morning_vs_evening"]["evening"] += 1
                        else:
                            time_patterns["morning_vs_evening"]["night"] += 1
                    except:
                        continue
            
            # 保存小时活跃度并找出峰值
            time_patterns["active_hours"] = hour_counts
            if sum(hour_counts) > 0:
                time_patterns["peak_hour"] = hour_counts.index(max(hour_counts))
            
            # 找出最活跃的星期几
            if sum(time_patterns["active_days"]) > 0:
                time_patterns["peak_day"] = time_patterns["active_days"].index(max(time_patterns["active_days"]))
            
            return time_patterns
        except Exception as e:
            profile_logger.error(f"分析用户 {user_id} 时间模式失败: {str(e)}")
            return time_patterns 

    def _extract_interaction_features(self, user_id: str) -> Dict[str, Any]:
        """提取用户交互特征
        
        分析用户与平台和内容的交互模式，包括UI偏好、
        互动频率和交互类型等特征。
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict[str, Any]: 交互特征分析结果
        """
        # 初始化交互特征数据
        interaction_features = {
            "ui_interactions": {
                "menu_navigation": "standard",
                "preferred_layout": "grid",
                "search_frequency": "low",
                "filter_usage": "low"
            },
            "content_interactions": {
                "like_rate": 0.0,
                "comment_rate": 0.0,
                "share_rate": 0.0,
                "save_rate": 0.0
            },
            "interaction_frequency": "low",
            "last_interaction": None,
            "common_actions": []
        }
        
        try:
            # 获取用户交互数据
            interaction_data = self.storage.get_user_interaction_data(user_id, days=30)
            if not interaction_data:
                return interaction_features
            
            # 分析UI交互
            if "ui_actions" in interaction_data:
                ui_actions = interaction_data["ui_actions"]
                
                # 分析布局偏好
                if "layout_changes" in ui_actions:
                    layouts = [change.get("new_layout") for change in ui_actions["layout_changes"]]
                    if layouts:
                        # 获取最常用布局
                        from collections import Counter
                        layouts_counter = Counter(layouts)
                        interaction_features["ui_interactions"]["preferred_layout"] = layouts_counter.most_common(1)[0][0]
                
                # 分析搜索频率
                if "search_count" in ui_actions:
                    search_count = ui_actions["search_count"]
                    if search_count > 10:
                        interaction_features["ui_interactions"]["search_frequency"] = "high"
                    elif search_count > 3:
                        interaction_features["ui_interactions"]["search_frequency"] = "medium"
                
                # 分析筛选器使用情况
                if "filter_usage" in ui_actions:
                    filter_count = ui_actions["filter_usage"].get("count", 0)
                    if filter_count > 7:
                        interaction_features["ui_interactions"]["filter_usage"] = "high"
                    elif filter_count > 2:
                        interaction_features["ui_interactions"]["filter_usage"] = "medium"
            
            # 分析内容交互率
            if "content_actions" in interaction_data:
                content_actions = interaction_data["content_actions"]
                total_views = content_actions.get("view_count", 0)
                
                if total_views > 0:
                    # 计算各类交互率
                    like_count = content_actions.get("like_count", 0)
                    comment_count = content_actions.get("comment_count", 0)
                    share_count = content_actions.get("share_count", 0)
                    save_count = content_actions.get("save_count", 0)
                    
                    interaction_features["content_interactions"]["like_rate"] = round(like_count / total_views, 3)
                    interaction_features["content_interactions"]["comment_rate"] = round(comment_count / total_views, 3)
                    interaction_features["content_interactions"]["share_rate"] = round(share_count / total_views, 3)
                    interaction_features["content_interactions"]["save_rate"] = round(save_count / total_views, 3)
            
            # 分析交互频率
            if "frequency" in interaction_data:
                interactions_per_day = interaction_data["frequency"].get("actions_per_day", 0)
                
                if interactions_per_day > 5:
                    interaction_features["interaction_frequency"] = "high"
                elif interactions_per_day > 2:
                    interaction_features["interaction_frequency"] = "medium"
            
            # 获取最后交互时间
            if "last_action" in interaction_data:
                interaction_features["last_interaction"] = interaction_data["last_action"].get("timestamp")
            
            # 获取常用操作
            if "common_actions" in interaction_data:
                interaction_features["common_actions"] = interaction_data["common_actions"][:5]  # 取前5个常用操作
            
            return interaction_features
        except Exception as e:
            profile_logger.error(f"提取用户 {user_id} 交互特征失败: {str(e)}")
            return interaction_features

    def _extract_social_features(self, user_id: str) -> Dict[str, Any]:
        """提取用户社交特征
        
        分析用户在社交平台上的行为特征，包括关注、分享、评论等。
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict[str, Any]: 社交特征分析结果
        """
        # 初始化社交特征数据
        social_features = {
            "following_count": 0,
            "follower_count": 0,
            "post_count": 0,
            "comment_count": 0,
            "share_count": 0,
            "last_interaction": None
        }
        
        try:
            # 获取用户社交数据
            social_data = self.storage.get_user_social_data(user_id)
            if not social_data:
                return social_features
            
            # 填充社交特征数据
            if "following_count" in social_data:
                social_features["following_count"] = social_data["following_count"]
            if "follower_count" in social_data:
                social_features["follower_count"] = social_data["follower_count"]
            if "post_count" in social_data:
                social_features["post_count"] = social_data["post_count"]
            if "comment_count" in social_data:
                social_features["comment_count"] = social_data["comment_count"]
            if "share_count" in social_data:
                social_features["share_count"] = social_data["share_count"]
            
            # 获取最后交互时间
            if "last_interaction" in social_data:
                social_features["last_interaction"] = social_data["last_interaction"].get("timestamp")
            
            return social_features
        except Exception as e:
            profile_logger.error(f"提取用户 {user_id} 社交特征失败: {str(e)}")
            return social_features 

    def update_profile(self, user_id: str, partial_update: bool = True) -> Dict[str, Any]:
        """更新用户画像
        
        Args:
            user_id: 用户ID
            partial_update: 是否只更新有新数据的部分
            
        Returns:
            Dict[str, Any]: 更新后的用户画像
        """
        profile_logger.info(f"开始更新用户 {user_id} 的画像")
        
        # 检查是否存在现有画像
        existing_profile = self.get_profile(user_id)
        
        if not existing_profile or not partial_update:
            # 如果不存在现有画像或要求全量更新，则创建全新画像
            return self.create_profile(user_id)
        
        # 部分更新逻辑 - 只更新有新数据的维度
        updated_dimensions = []
        
        # 更新基本信息
        basic_info = self._get_demographics(user_id)
        if basic_info != existing_profile.get("basic_info"):
            existing_profile["basic_info"] = basic_info
            updated_dimensions.append("basic_info")
        
        # 更新内容偏好
        content_heatmap = self._analyze_heatmap(user_id)
        if content_heatmap.get("updated_at", "") > existing_profile.get("view_heatmap", {}).get("updated_at", ""):
            existing_profile["view_heatmap"] = content_heatmap
            updated_dimensions.append("view_heatmap")
        
        # 更新情感响应
        emotion_response = self._load_biometric_data(user_id)
        if emotion_response != existing_profile.get("emotion_response"):
            existing_profile["emotion_response"] = emotion_response
            updated_dimensions.append("emotion_response")
        
        # 更新设备约束
        device_constraints = self._get_device_specs(user_id)
        if device_constraints != existing_profile.get("device_constraints"):
            existing_profile["device_constraints"] = device_constraints
            updated_dimensions.append("device_constraints")
        
        # 更新行为模式
        behavior_patterns = self._analyze_behavior_patterns(user_id)
        if behavior_patterns != existing_profile.get("behavior_patterns"):
            existing_profile["behavior_patterns"] = behavior_patterns
            updated_dimensions.append("behavior_patterns")
        
        # 更新时间模式
        temporal_patterns = self._analyze_temporal_patterns(user_id)
        if temporal_patterns != existing_profile.get("temporal_patterns"):
            existing_profile["temporal_patterns"] = temporal_patterns
            updated_dimensions.append("temporal_patterns")
        
        # 更新交互特征
        interaction_features = self._extract_interaction_features(user_id)
        if interaction_features != existing_profile.get("interaction_features"):
            existing_profile["interaction_features"] = interaction_features
            updated_dimensions.append("interaction_features")
        
        # 更新社交特征
        social_features = self._extract_social_features(user_id)
        if social_features != existing_profile.get("social_features"):
            existing_profile["social_features"] = social_features
            updated_dimensions.append("social_features")
        
        # 更新时间戳
        existing_profile["updated_at"] = datetime.now().isoformat()
        
        # 存储更新后的画像
        self._save_profile(user_id, existing_profile)
        
        # 更新缓存
        self.profile_cache[user_id] = existing_profile
        
        profile_logger.info(f"用户 {user_id} 的画像已更新，更新维度: {', '.join(updated_dimensions)}")
        return existing_profile
    
    def get_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户画像
        
        先尝试从缓存获取，如果缓存中没有，则从存储中加载。
        
        Args:
            user_id: 用户ID
            
        Returns:
            Optional[Dict[str, Any]]: 用户画像，如果不存在则返回None
        """
        # 先检查缓存
        if user_id in self.profile_cache:
            return self.profile_cache[user_id]
        
        # 从存储中加载
        try:
            profile = self.storage.get_user_profile(user_id)
            if profile:
                # 更新缓存
                self.profile_cache[user_id] = profile
                return profile
        except Exception as e:
            profile_logger.error(f"获取用户 {user_id} 画像失败: {str(e)}")
        
        return None
    
    def _save_profile(self, user_id: str, profile: Dict[str, Any]) -> bool:
        """保存用户画像到存储
        
        Args:
            user_id: 用户ID
            profile: 用户画像数据
            
        Returns:
            bool: 保存是否成功
        """
        try:
            self.storage.save_user_profile(user_id, profile)
            return True
        except Exception as e:
            profile_logger.error(f"保存用户 {user_id} 画像失败: {str(e)}")
            return False
    
    def get_profile_dimension(self, user_id: str, dimension: str) -> Optional[Dict[str, Any]]:
        """获取用户画像中特定维度的数据
        
        Args:
            user_id: 用户ID
            dimension: 维度名称
            
        Returns:
            Optional[Dict[str, Any]]: 维度数据，如果不存在则返回None
        """
        profile = self.get_profile(user_id)
        if not profile:
            return None
        
        # 尝试获取请求的维度
        dimension_mapping = {
            'demographic': 'basic_info',
            'behavioral': 'behavior_patterns',
            'emotional': 'emotion_response',
            'technical': 'device_constraints',
            'content': 'view_heatmap',
            'interaction': 'interaction_features',
            'temporal': 'temporal_patterns',
            'social': 'social_features'
        }
        
        # 获取实际存储的键名
        actual_key = dimension_mapping.get(dimension, dimension)
        
        return profile.get(actual_key)
    
    def get_user_segment(self, user_id: str) -> str:
        """确定用户所属细分群体
        
        基于用户画像数据，将用户分配到预定义的细分群体。
        
        Args:
            user_id: 用户ID
            
        Returns:
            str: 用户细分标识
        """
        profile = self.get_profile(user_id)
        if not profile:
            return "unknown"
        
        # 初始化分数计算器
        segment_scores = {
            "casual_viewer": 0,     # 休闲观众
            "content_enthusiast": 0, # 内容爱好者
            "binge_watcher": 0,     # 追剧用户
            "social_sharer": 0,     # 社交分享者
            "critic": 0,            # 评论者
            "mobile_first": 0,      # 移动优先用户
            "prime_time": 0,        # 黄金时段用户
            "weekender": 0          # 周末用户
        }
        
        # 分析行为模式指标
        behavior = profile.get("behavior_patterns", {})
        completion_rate = behavior.get("completion_rate", 0)
        avg_session = behavior.get("avg_session_duration", 0)
        binge_watching = behavior.get("binge_watching", False)
        
        if completion_rate < 0.3 and avg_session < 15:
            segment_scores["casual_viewer"] += 3
        
        if completion_rate > 0.8 and avg_session > 30:
            segment_scores["content_enthusiast"] += 3
        
        if binge_watching:
            segment_scores["binge_watcher"] += 4
        
        # 分析内容交互指标
        interaction = profile.get("interaction_features", {})
        content_interactions = interaction.get("content_interactions", {})
        comment_rate = content_interactions.get("comment_rate", 0)
        share_rate = content_interactions.get("share_rate", 0)
        
        if comment_rate > 0.1:
            segment_scores["critic"] += 3
        
        if share_rate > 0.05:
            segment_scores["social_sharer"] += 3
        
        # 分析设备偏好
        device = profile.get("device_constraints", {})
        device_type = device.get("device_type", "").lower()
        
        if "mobile" in device_type or "phone" in device_type:
            segment_scores["mobile_first"] += 2
        
        # 分析时间模式
        temporal = profile.get("temporal_patterns", {})
        peak_hour = temporal.get("peak_hour", 0)
        peak_day = temporal.get("peak_day", 0)
        weekend_vs_weekday = temporal.get("weekend_vs_weekday", {})
        
        if 19 <= peak_hour <= 22:  # 晚间7点到10点
            segment_scores["prime_time"] += 2
        
        if peak_day >= 5 or weekend_vs_weekday.get("weekend", 0) > weekend_vs_weekday.get("weekday", 0) * 1.5:
            segment_scores["weekender"] += 2
        
        # 找出得分最高的细分群体
        max_segment = max(segment_scores.items(), key=lambda x: x[1])
        
        # 如果没有明显的分类，则将用户标记为"mixed"
        if max_segment[1] < 2:
            return "mixed"
        
        return max_segment[0]

    def _analyze_content_preferences(self, user_id: str) -> Dict[str, Any]:
        """分析用户内容偏好
        
        分析用户对不同短剧类型、内容主题和角色类型的偏好。
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict[str, Any]: 内容偏好分析
        """
        # 获取用户观看历史
        view_history = self._get_user_view_history(user_id)
        
        # 初始化偏好计数器
        genre_counts = {}  # 短剧类型
        theme_counts = {}  # 主题
        character_counts = {}  # 角色类型
        
        # 分析观看历史
        for view in view_history:
            content_id = view.get("content_id")
            metadata = view.get("metadata", {})
            
            # 计数短剧类型
            genre = metadata.get("genre")
            if genre:
                genre_counts[genre] = genre_counts.get(genre, 0) + 1
            
            # 计数主题
            themes = metadata.get("themes", [])
            for theme in themes:
                theme_counts[theme] = theme_counts.get(theme, 0) + 1
            
            # 计数角色类型
            characters = metadata.get("character_types", [])
            for char_type in characters:
                character_counts[char_type] = character_counts.get(char_type, 0) + 1
        
        # 计算偏好强度
        total_views = len(view_history) if view_history else 1
        
        # 排序偏好
        favorite_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)
        favorite_themes = sorted(theme_counts.items(), key=lambda x: x[1], reverse=True)
        favorite_characters = sorted(character_counts.items(), key=lambda x: x[1], reverse=True)
        
        return {
            "favorite_genres": [{"genre": g, "strength": c/total_views} for g, c in favorite_genres[:5]],
            "favorite_themes": [{"theme": t, "strength": c/total_views} for t, c in favorite_themes[:5]],
            "favorite_characters": [{"character_type": c, "strength": n/total_views} for c, n in favorite_characters[:5]],
            "total_analyzed_views": total_views,
            "confidence": min(1.0, total_views / 20)  # 至少20次观看达到最高置信度
        }
    
    def _analyze_emotion_preferences(self, user_id: str) -> Dict[str, Any]:
        """分析用户情感偏好
        
        分析用户对不同情感类型和情感曲线的偏好。
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict[str, Any]: 情感偏好分析
        """
        # 获取用户情感反馈数据
        emotion_data = self.storage.get_user_biometric_data(user_id)
        
        # 初始化情感偏好
        emotion_prefs = {
            "primary_emotions": [],
            "emotional_arcs": [],
            "emotional_intensity": 0.5,  # 默认中等强度
            "confidence": 0.0
        }
        
        if not emotion_data:
            return emotion_prefs
        
        # 分析情感反馈
        emotion_counts = {}
        arc_counts = {}
        intensity_sum = 0
        intensity_count = 0
        
        # 处理情感数据
        responses = emotion_data.get("responses", [])
        for response in responses:
            # 主要情感类型
            emotion = response.get("primary_emotion")
            if emotion:
                emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
            
            # 情感曲线类型
            arc = response.get("emotional_arc")
            if arc:
                arc_counts[arc] = arc_counts.get(arc, 0) + 1
            
            # 情感强度
            intensity = response.get("intensity")
            if intensity is not None:
                intensity_sum += intensity
                intensity_count += 1
        
        # 计算结果
        if emotion_counts:
            sorted_emotions = sorted(emotion_counts.items(), key=lambda x: x[1], reverse=True)
            emotion_prefs["primary_emotions"] = [{"emotion": e, "count": c} for e, c in sorted_emotions[:3]]
        
        if arc_counts:
            sorted_arcs = sorted(arc_counts.items(), key=lambda x: x[1], reverse=True)
            emotion_prefs["emotional_arcs"] = [{"arc": a, "count": c} for a, c in sorted_arcs[:3]]
        
        if intensity_count > 0:
            emotion_prefs["emotional_intensity"] = intensity_sum / intensity_count
        
        # 计算置信度
        emotion_prefs["confidence"] = min(1.0, len(responses) / 15)  # 至少15个情感反馈达到最高置信度
        
        return emotion_prefs
    
    def _analyze_editing_preferences(self, user_id: str) -> Dict[str, Any]:
        """分析用户剪辑风格偏好
        
        分析用户对不同剪辑手法、转场效果和风格的偏好。
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict[str, Any]: 剪辑风格偏好
        """
        # 初始化剪辑偏好
        editing_prefs = {
            "transition_types": [],
            "cutting_pace": "medium",  # 默认中等剪辑节奏
            "visual_effects": [],
            "color_grading": "standard",
            "confidence": 0.0
        }
        
        # 获取用户剪辑偏好数据
        behavior_data = self.storage.get_user_behavior_data(user_id)
        if not behavior_data or "editing_preferences" not in behavior_data:
            return editing_prefs
        
        edit_data = behavior_data["editing_preferences"]
        
        # 分析转场偏好
        if "transitions" in edit_data:
            transitions = edit_data["transitions"]
            sorted_transitions = sorted(transitions.items(), key=lambda x: x[1], reverse=True)
            editing_prefs["transition_types"] = [
                {"type": t, "frequency": f} for t, f in sorted_transitions[:3]
            ]
        
        # 分析剪辑节奏
        if "cutting_pace" in edit_data:
            pace_data = edit_data["cutting_pace"]
            # 找出最常用的节奏
            max_pace = "medium"
            max_count = 0
            for pace, count in pace_data.items():
                if count > max_count:
                    max_count = count
                    max_pace = pace
            editing_prefs["cutting_pace"] = max_pace
        
        # 分析视觉效果
        if "visual_effects" in edit_data:
            effects = edit_data["visual_effects"]
            sorted_effects = sorted(effects.items(), key=lambda x: x[1], reverse=True)
            editing_prefs["visual_effects"] = [
                {"effect": e, "frequency": f} for e, f in sorted_effects[:3]
            ]
        
        # 分析色彩风格
        if "color_grading" in edit_data:
            grading = edit_data["color_grading"]
            # 找出最常用的色彩风格
            max_grade = "standard"
            max_count = 0
            for grade, count in grading.items():
                if count > max_count:
                    max_count = count
                    max_grade = grade
            editing_prefs["color_grading"] = max_grade
        
        # 计算置信度
        total_edits = edit_data.get("total_edits", 0)
        editing_prefs["confidence"] = min(1.0, total_edits / 10)  # 至少10次编辑达到最高置信度
        
        return editing_prefs

    def _analyze_narrative_preferences(self, user_id: str) -> Dict[str, Any]:
        """分析用户叙事结构偏好
        
        分析用户对不同叙事结构和故事元素的偏好。
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict[str, Any]: 叙事结构偏好
        """
        # 初始化叙事偏好
        narrative_prefs = {
            "structure_types": [],
            "conflict_intensity": 0.5,  # 默认中等冲突强度
            "character_focus": "balanced",  # 默认平衡角色焦点
            "plot_elements": [],
            "confidence": 0.0
        }
        
        # 获取用户叙事偏好数据
        behavior_data = self.storage.get_user_behavior_data(user_id)
        if not behavior_data or "narrative_preferences" not in behavior_data:
            return narrative_prefs
        
        narrative_data = behavior_data["narrative_preferences"]
        
        # 分析叙事结构偏好
        if "structures" in narrative_data:
            structures = narrative_data["structures"]
            sorted_structures = sorted(structures.items(), key=lambda x: x[1], reverse=True)
            narrative_prefs["structure_types"] = [
                {"type": s, "frequency": f} for s, f in sorted_structures[:3]
            ]
        
        # 分析冲突强度偏好
        if "conflict_intensity" in narrative_data:
            intensities = narrative_data["conflict_intensity"]
            total = sum(intensities.values())
            if total > 0:
                weighted_sum = sum(float(k) * v for k, v in intensities.items())
                narrative_prefs["conflict_intensity"] = weighted_sum / total
        
        # 分析角色焦点偏好
        if "character_focus" in narrative_data:
            focus = narrative_data["character_focus"]
            # 找出最常用的角色焦点
            max_focus = "balanced"
            max_count = 0
            for f, count in focus.items():
                if count > max_count:
                    max_count = count
                    max_focus = f
            narrative_prefs["character_focus"] = max_focus
        
        # 分析剧情元素偏好
        if "plot_elements" in narrative_data:
            elements = narrative_data["plot_elements"]
            sorted_elements = sorted(elements.items(), key=lambda x: x[1], reverse=True)
            narrative_prefs["plot_elements"] = [
                {"element": e, "frequency": f} for e, f in sorted_elements[:5]
            ]
        
        # 计算置信度
        analyzed_count = narrative_data.get("analyzed_count", 0)
        narrative_prefs["confidence"] = min(1.0, analyzed_count / 10)  # 至少10次分析达到最高置信度
        
        return narrative_prefs
    
    def _analyze_pacing_preferences(self, user_id: str) -> Dict[str, Any]:
        """分析用户节奏偏好
        
        分析用户对视频节奏、场景长度和剪辑频率的偏好。
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict[str, Any]: 节奏偏好分析
        """
        # 初始化节奏偏好
        pacing_prefs = {
            "overall_pace": "medium",  # 默认中等节奏
            "scene_duration": {
                "min": 3.0,  # 默认最短3秒
                "max": 15.0,  # 默认最长15秒
                "average": 8.0  # 默认平均8秒
            },
            "cut_frequency": "medium",  # 默认中等剪辑频率
            "tension_build": "gradual",  # 默认渐进式紧张度构建
            "confidence": 0.0
        }
        
        # 获取用户节奏偏好数据
        temporal_data = self.storage.get_user_temporal_data(user_id)
        if not temporal_data:
            return pacing_prefs
        
        # 分析整体节奏偏好
        if "pace_preferences" in temporal_data:
            paces = temporal_data["pace_preferences"]
            max_pace = "medium"
            max_count = 0
            for pace, count in paces.items():
                if count > max_count:
                    max_count = count
                    max_pace = pace
            pacing_prefs["overall_pace"] = max_pace
        
        # 分析场景时长偏好
        if "scene_durations" in temporal_data:
            durations = temporal_data["scene_durations"]
            if durations:
                # 计算平均、最小、最大场景时长
                all_durations = []
                for duration_range, count in durations.items():
                    try:
                        # 假设键的格式为 "min-max"
                        min_val, max_val = map(float, duration_range.split('-'))
                        mid_val = (min_val + max_val) / 2
                        all_durations.extend([mid_val] * count)
                    except:
                        continue
                
                if all_durations:
                    all_durations.sort()
                    pacing_prefs["scene_duration"] = {
                        "min": all_durations[0],
                        "max": all_durations[-1],
                        "average": sum(all_durations) / len(all_durations)
                    }
        
        # 分析剪辑频率偏好
        if "cut_frequency" in temporal_data:
            frequencies = temporal_data["cut_frequency"]
            max_freq = "medium"
            max_count = 0
            for freq, count in frequencies.items():
                if count > max_count:
                    max_count = count
                    max_freq = freq
            pacing_prefs["cut_frequency"] = max_freq
        
        # 分析紧张度构建偏好
        if "tension_build" in temporal_data:
            tension_types = temporal_data["tension_build"]
            max_tension = "gradual"
            max_count = 0
            for tension, count in tension_types.items():
                if count > max_count:
                    max_count = count
                    max_tension = tension
            pacing_prefs["tension_build"] = max_tension
        
        # 计算置信度
        analyzed_count = temporal_data.get("analyzed_count", 0)
        pacing_prefs["confidence"] = min(1.0, analyzed_count / 10)  # 至少10次分析达到最高置信度
        
        return pacing_prefs


# 模块级函数

_profile_engine_instance = None

def get_profile_engine() -> UserProfileEngine:
    """获取用户画像引擎单例实例
    
    Returns:
        UserProfileEngine: 用户画像引擎实例
    """
    global _profile_engine_instance
    if _profile_engine_instance is None:
        _profile_engine_instance = UserProfileEngine()
    return _profile_engine_instance

def create_user_profile(user_id: str) -> Dict[str, Any]:
    """创建用户画像
    
    Args:
        user_id: 用户ID
        
    Returns:
        Dict[str, Any]: 用户画像
    """
    engine = get_profile_engine()
    return engine.create_profile(user_id)

def update_user_profile(user_id: str, partial_update: bool = True) -> Dict[str, Any]:
    """更新用户画像
    
    Args:
        user_id: 用户ID
        partial_update: 是否只更新有新数据的部分
        
    Returns:
        Dict[str, Any]: 更新后的用户画像
    """
    engine = get_profile_engine()
    return engine.update_profile(user_id, partial_update)

def get_user_profile(user_id: str) -> Optional[Dict[str, Any]]:
    """获取用户画像
    
    Args:
        user_id: 用户ID
        
    Returns:
        Optional[Dict[str, Any]]: 用户画像，如果不存在则返回None
    """
    engine = get_profile_engine()
    return engine.get_profile(user_id) 