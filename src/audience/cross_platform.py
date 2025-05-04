#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
跨平台习惯融合模块

整合用户在多个内容平台上的行为习惯和偏好，构建统一的用户画像，
为内容变形和推荐系统提供更全面的数据支持。
"""

import os
import json
import time
import hashlib
import logging
import requests
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timedelta
import numpy as np
from loguru import logger

from src.utils.log_handler import get_logger
from src.data.storage_manager import get_storage_manager
from src.audience.profile_builder import get_profile_engine
from src.audience.behavior_decoder import get_behavior_decoder
from src.utils.config_manager import get_config

# 配置日志
platform_logger = get_logger("cross_platform")

class CrossPlatformIntegrator:
    """跨平台习惯融合器
    
    整合用户在抖音、B站、YouTube等多个平台上的行为习惯和偏好，
    构建统一的用户画像，并提供统一的偏好表达。
    """
    
    def __init__(self):
        """初始化跨平台整合器"""
        # 获取存储管理器
        self.storage = get_storage_manager()
        
        # 获取用户画像引擎
        self.profile_engine = get_profile_engine()
        
        # 获取行为解码器
        self.behavior_decoder = get_behavior_decoder()
        
        # 加载配置
        self.config = get_config("audience").get("cross_platform", {})
        
        # 平台权重 - 决定各平台数据的重要性
        self.platform_weights = self.config.get("platform_weights", {
            "douyin": 1.0,
            "bilibili": 0.9,
            "youtube": 0.8,
            "kuaishou": 0.7,
            "tiktok": 0.7
        })
        
        # 平台API访问配置
        self.platform_apis = self.config.get("platform_apis", {})
        
        # 跨平台数据缓存
        self.platform_data_cache = {}
        
        # 缓存有效期（24小时）
        self.cache_ttl = 24 * 60 * 60
        
        platform_logger.info("跨平台习惯融合器初始化完成")
    
    def integrate_habits(self, user_id: str) -> Dict[str, Any]:
        """整合用户在多平台上的习惯与偏好
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict[str, Any]: 整合后的跨平台习惯数据
        """
        platform_logger.info(f"开始整合用户 {user_id} 的跨平台习惯")
        
        # 获取抖音平台数据
        douyin_data = self._get_douyin_habits(user_id)
        
        # 获取B站平台数据
        bilibili_data = self._get_bilibili_habits(user_id)
        
        # 获取YouTube平台数据
        youtube_data = self._get_youtube_habits(user_id)
        
        # 计算统一偏好表达
        unified_preference = self._calculate_unified_preference({
            "douyin": douyin_data,
            "bilibili": bilibili_data,
            "youtube": youtube_data
        })
        
        # 整合结果
        result = {
            "抖音": douyin_data,
            "B站": bilibili_data,
            "油管": youtube_data,
            "融合策略": unified_preference
        }
        
        # 保存整合结果
        self._save_integrated_data(user_id, result)
        
        platform_logger.info(f"用户 {user_id} 的跨平台习惯整合完成")
        return result
    
    def _get_douyin_habits(self, user_id: str) -> Dict[str, Any]:
        """获取用户抖音平台习惯数据
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict[str, Any]: 抖音平台习惯数据
        """
        platform_logger.debug(f"获取用户 {user_id} 的抖音习惯数据")
        
        # 检查缓存
        cache_key = f"douyin_{user_id}"
        if cache_key in self.platform_data_cache:
            cache_entry = self.platform_data_cache[cache_key]
            if time.time() - cache_entry["timestamp"] < self.cache_ttl:
                return cache_entry["data"]
        
        try:
            # 尝试从存储中获取抖音绑定信息
            douyin_binding = self.storage.get_platform_binding(user_id, "douyin")
            
            if not douyin_binding:
                platform_logger.warning(f"用户 {user_id} 未绑定抖音账号")
                return {}
            
            # 尝试从抖音API获取数据
            douyin_id = douyin_binding.get("platform_user_id")
            
            # 如果配置了API访问
            if "douyin" in self.platform_apis and douyin_id:
                douyin_data = self._fetch_douyin_api_data(douyin_id)
                if douyin_data:
                    # 处理并解析抖音数据
                    return self._process_douyin_data(douyin_data)
            
            # 如果无法通过API获取，则使用已存储的抖音习惯数据
            stored_data = self.storage.get_platform_data(user_id, "douyin")
            if stored_data:
                # 更新缓存
                self.platform_data_cache[cache_key] = {
                    "data": stored_data,
                    "timestamp": time.time()
                }
                return stored_data
                
        except Exception as e:
            platform_logger.error(f"获取抖音习惯数据失败: {str(e)}")
        
        # 如果没有获取到数据，返回空结果
        return {}
    
    def _fetch_douyin_api_data(self, douyin_id: str) -> Dict[str, Any]:
        """从抖音API获取数据
        
        Args:
            douyin_id: 抖音用户ID
            
        Returns:
            Dict[str, Any]: 抖音API返回的数据
        """
        # 这里是模拟获取抖音数据，实际项目中应通过抖音开放API获取
        # 由于API访问需要认证和配置，这里仅做示例
        
        try:
            # 如果有配置API访问令牌
            api_config = self.platform_apis.get("douyin", {})
            if not api_config:
                return {}
                
            # 模拟API调用结果
            mock_data = {
                "user_id": douyin_id,
                "favorite_categories": ["搞笑", "生活", "美食"],
                "avg_watch_duration": 35.6,
                "active_hours": ["18:00-22:00", "12:00-13:00"],
                "interaction_rate": 0.05,
                "content_preferences": {
                    "short_video": 0.8,
                    "live": 0.2
                }
            }
            return mock_data
            
        except Exception as e:
            platform_logger.error(f"抖音API调用失败: {str(e)}")
            return {}
    
    def _process_douyin_data(self, api_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理抖音API返回的数据
        
        Args:
            api_data: 抖音API返回的原始数据
            
        Returns:
            Dict[str, Any]: 处理后的抖音习惯数据
        """
        # 提取并标准化抖音数据
        result = {
            "favorite_categories": api_data.get("favorite_categories", []),
            "content_format_preference": {
                "短视频": api_data.get("content_preferences", {}).get("short_video", 0.5),
                "直播": api_data.get("content_preferences", {}).get("live", 0.2)
            },
            "watch_duration": {
                "average": api_data.get("avg_watch_duration", 0),
                "unit": "seconds"
            },
            "active_time_slots": api_data.get("active_hours", []),
            "interaction_habits": {
                "rate": api_data.get("interaction_rate", 0),
                "comment_frequency": "low",
                "like_frequency": "medium"
            },
            "last_updated": datetime.now().isoformat()
        }
        
        # 转换分类偏好格式
        category_preferences = {}
        for category in result.get("favorite_categories", []):
            category_preferences[category] = {
                "score": 0.8,  # 默认分数
                "strength": "strong_like"
            }
        
        result["category_preferences"] = category_preferences
        
        return result
    
    def _get_bilibili_habits(self, user_id: str) -> Dict[str, Any]:
        """获取用户B站平台习惯数据
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict[str, Any]: B站平台习惯数据
        """
        platform_logger.debug(f"获取用户 {user_id} 的B站习惯数据")
        
        # 检查缓存
        cache_key = f"bilibili_{user_id}"
        if cache_key in self.platform_data_cache:
            cache_entry = self.platform_data_cache[cache_key]
            if time.time() - cache_entry["timestamp"] < self.cache_ttl:
                return cache_entry["data"]
        
        try:
            # 尝试从存储中获取B站绑定信息
            bilibili_binding = self.storage.get_platform_binding(user_id, "bilibili")
            
            if not bilibili_binding:
                platform_logger.warning(f"用户 {user_id} 未绑定B站账号")
                return {}
            
            # 尝试从B站API获取数据
            bilibili_id = bilibili_binding.get("platform_user_id")
            
            # 如果配置了API访问
            if "bilibili" in self.platform_apis and bilibili_id:
                bilibili_data = self._fetch_bilibili_api_data(bilibili_id)
                if bilibili_data:
                    # 处理并解析B站数据
                    return self._process_bilibili_data(bilibili_data)
            
            # 如果无法通过API获取，则使用已存储的B站习惯数据
            stored_data = self.storage.get_platform_data(user_id, "bilibili")
            if stored_data:
                # 更新缓存
                self.platform_data_cache[cache_key] = {
                    "data": stored_data,
                    "timestamp": time.time()
                }
                return stored_data
                
        except Exception as e:
            platform_logger.error(f"获取B站习惯数据失败: {str(e)}")
        
        # 如果没有获取到数据，返回空结果
        return {}
    
    def _fetch_bilibili_api_data(self, bilibili_id: str) -> Dict[str, Any]:
        """从B站API获取数据
        
        Args:
            bilibili_id: B站用户ID
            
        Returns:
            Dict[str, Any]: B站API返回的数据
        """
        # 这里是模拟获取B站数据，实际项目中应通过B站开放API获取
        
        try:
            # 如果有配置API访问令牌
            api_config = self.platform_apis.get("bilibili", {})
            if not api_config:
                return {}
                
            # 模拟API调用结果
            mock_data = {
                "user_id": bilibili_id,
                "favorite_partitions": ["动画", "游戏", "科技"],
                "avg_watch_duration": 420.5,  # 秒
                "active_hours": ["19:00-23:00", "13:00-15:00"],
                "bangumi_follows": ["间谍过家家", "鬼灭之刃"],
                "content_preferences": {
                    "video": 0.6,
                    "live": 0.3,
                    "bangumi": 0.1
                }
            }
            return mock_data
            
        except Exception as e:
            platform_logger.error(f"B站API调用失败: {str(e)}")
            return {}
    
    def _process_bilibili_data(self, api_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理B站API返回的数据
        
        Args:
            api_data: B站API返回的原始数据
            
        Returns:
            Dict[str, Any]: 处理后的B站习惯数据
        """
        # 提取并标准化B站数据
        result = {
            "favorite_partitions": api_data.get("favorite_partitions", []),
            "content_format_preference": {
                "视频": api_data.get("content_preferences", {}).get("video", 0.5),
                "直播": api_data.get("content_preferences", {}).get("live", 0.2),
                "番剧": api_data.get("content_preferences", {}).get("bangumi", 0.3)
            },
            "watch_duration": {
                "average": api_data.get("avg_watch_duration", 0),
                "unit": "seconds"
            },
            "active_time_slots": api_data.get("active_hours", []),
            "favorite_series": api_data.get("bangumi_follows", []),
            "last_updated": datetime.now().isoformat()
        }
        
        # 转换分区偏好格式
        category_preferences = {}
        for category in result.get("favorite_partitions", []):
            category_preferences[category] = {
                "score": 0.8,  # 默认分数
                "strength": "strong_like"
            }
        
        result["category_preferences"] = category_preferences
        
        return result
    
    def _get_youtube_habits(self, user_id: str) -> Dict[str, Any]:
        """获取用户YouTube平台习惯数据
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict[str, Any]: YouTube平台习惯数据
        """
        platform_logger.debug(f"获取用户 {user_id} 的YouTube习惯数据")
        
        # 检查缓存
        cache_key = f"youtube_{user_id}"
        if cache_key in self.platform_data_cache:
            cache_entry = self.platform_data_cache[cache_key]
            if time.time() - cache_entry["timestamp"] < self.cache_ttl:
                return cache_entry["data"]
        
        try:
            # 尝试从存储中获取YouTube绑定信息
            youtube_binding = self.storage.get_platform_binding(user_id, "youtube")
            
            if not youtube_binding:
                platform_logger.warning(f"用户 {user_id} 未绑定YouTube账号")
                return {}
            
            # 尝试从YouTube API获取数据
            youtube_id = youtube_binding.get("platform_user_id")
            
            # 如果配置了API访问
            if "youtube" in self.platform_apis and youtube_id:
                youtube_data = self._fetch_youtube_api_data(youtube_id)
                if youtube_data:
                    # 处理并解析YouTube数据
                    return self._process_youtube_data(youtube_data)
            
            # 如果无法通过API获取，则使用已存储的YouTube习惯数据
            stored_data = self.storage.get_platform_data(user_id, "youtube")
            if stored_data:
                # 更新缓存
                self.platform_data_cache[cache_key] = {
                    "data": stored_data,
                    "timestamp": time.time()
                }
                return stored_data
                
        except Exception as e:
            platform_logger.error(f"获取YouTube习惯数据失败: {str(e)}")
        
        # 如果没有获取到数据，返回空结果
        return {}
    
    def _fetch_youtube_api_data(self, youtube_id: str) -> Dict[str, Any]:
        """从YouTube API获取数据
        
        Args:
            youtube_id: YouTube用户ID
            
        Returns:
            Dict[str, Any]: YouTube API返回的数据
        """
        # 这里是模拟获取YouTube数据，实际项目中应通过YouTube API获取
        
        try:
            # 如果有配置API访问令牌
            api_config = self.platform_apis.get("youtube", {})
            if not api_config:
                return {}
                
            # 模拟API调用结果
            mock_data = {
                "user_id": youtube_id,
                "subscribed_categories": ["Entertainment", "Technology", "Music"],
                "avg_watch_duration": 540.2,  # 秒
                "active_hours": ["20:00-24:00", "7:00-9:00"],
                "subscribed_channels": ["TED", "Marques Brownlee"],
                "content_preferences": {
                    "video": 0.7,
                    "shorts": 0.2,
                    "live": 0.1
                }
            }
            return mock_data
            
        except Exception as e:
            platform_logger.error(f"YouTube API调用失败: {str(e)}")
            return {}
    
    def _process_youtube_data(self, api_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理YouTube API返回的数据
        
        Args:
            api_data: YouTube API返回的原始数据
            
        Returns:
            Dict[str, Any]: 处理后的YouTube习惯数据
        """
        # 提取并标准化YouTube数据
        result = {
            "subscribed_categories": api_data.get("subscribed_categories", []),
            "content_format_preference": {
                "视频": api_data.get("content_preferences", {}).get("video", 0.5),
                "短视频": api_data.get("content_preferences", {}).get("shorts", 0.3),
                "直播": api_data.get("content_preferences", {}).get("live", 0.2)
            },
            "watch_duration": {
                "average": api_data.get("avg_watch_duration", 0),
                "unit": "seconds"
            },
            "active_time_slots": api_data.get("active_hours", []),
            "subscribed_channels": api_data.get("subscribed_channels", []),
            "last_updated": datetime.now().isoformat()
        }
        
        # 转换分类偏好格式
        category_preferences = {}
        for category in result.get("subscribed_categories", []):
            category_preferences[category] = {
                "score": 0.7,  # 默认分数
                "strength": "like"
            }
        
        result["category_preferences"] = category_preferences
        
        return result
    
    def _calculate_unified_preference(self, platform_data: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """计算统一的偏好表达
        
        将来自不同平台的偏好数据融合为一个统一的偏好表达
        
        Args:
            platform_data: 各平台数据字典
            
        Returns:
            Dict[str, Any]: 统一的偏好表达
        """
        platform_logger.debug("计算统一偏好表达")
        
        # 提取各平台的分类偏好
        category_preferences = {}
        for platform, data in platform_data.items():
            platform_weight = self.platform_weights.get(platform, 0.5)
            
            # 提取该平台的分类偏好
            platform_categories = data.get("category_preferences", {})
            
            # 合并到统一偏好中
            for category, pref_data in platform_categories.items():
                score = pref_data.get("score", 0.5) * platform_weight
                
                if category not in category_preferences:
                    category_preferences[category] = {
                        "score": score,
                        "platforms": [platform]
                    }
                else:
                    category_preferences[category]["score"] = (
                        category_preferences[category]["score"] + score
                    ) / 2  # 取平均值
                    category_preferences[category]["platforms"].append(platform)
        
        # 计算内容格式偏好
        format_preferences = {}
        for platform, data in platform_data.items():
            platform_weight = self.platform_weights.get(platform, 0.5)
            
            # 提取该平台的内容格式偏好
            platform_formats = data.get("content_format_preference", {})
            
            # 合并到统一偏好中
            for format_type, score in platform_formats.items():
                weighted_score = score * platform_weight
                
                if format_type not in format_preferences:
                    format_preferences[format_type] = {
                        "score": weighted_score,
                        "platforms": [platform]
                    }
                else:
                    format_preferences[format_type]["score"] = (
                        format_preferences[format_type]["score"] + weighted_score
                    ) / 2  # 取平均值
                    format_preferences[format_type]["platforms"].append(platform)
        
        # 计算活跃时段偏好
        time_slots = []
        for platform, data in platform_data.items():
            platform_slots = data.get("active_time_slots", [])
            time_slots.extend(platform_slots)
        
        # 提取观看时长偏好
        watch_durations = {}
        for platform, data in platform_data.items():
            if "watch_duration" in data and "average" in data["watch_duration"]:
                watch_durations[platform] = data["watch_duration"]["average"]
        
        avg_watch_duration = sum(watch_durations.values()) / len(watch_durations) if watch_durations else 0
        
        # 组装统一偏好表达
        unified_preference = {
            "category_preferences": category_preferences,
            "format_preferences": format_preferences,
            "active_time_slots": list(set(time_slots)),  # 去重
            "watch_duration": {
                "average": avg_watch_duration,
                "unit": "seconds"
            },
            "platform_coverage": {
                "douyin": "douyin" in platform_data and bool(platform_data["douyin"]),
                "bilibili": "bilibili" in platform_data and bool(platform_data["bilibili"]),
                "youtube": "youtube" in platform_data and bool(platform_data["youtube"])
            },
            "updated_at": datetime.now().isoformat()
        }
        
        return unified_preference
    
    def _save_integrated_data(self, user_id: str, integrated_data: Dict[str, Any]) -> bool:
        """保存整合后的跨平台数据
        
        Args:
            user_id: 用户ID
            integrated_data: 整合后的数据
            
        Returns:
            bool: 保存成功返回True，否则返回False
        """
        try:
            self.storage.save_cross_platform_data(user_id, integrated_data)
            platform_logger.debug(f"用户 {user_id} 的跨平台数据保存成功")
            return True
        except Exception as e:
            platform_logger.error(f"保存跨平台数据失败: {str(e)}")
            return False
    
    def get_unified_preference(self, user_id: str) -> Dict[str, Any]:
        """获取用户的统一偏好表达
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict[str, Any]: 统一的偏好表达
        """
        # 先尝试获取已有的整合数据
        try:
            integrated_data = self.storage.get_cross_platform_data(user_id)
            if integrated_data and "融合策略" in integrated_data:
                # 检查数据是否过期
                updated_at = datetime.fromisoformat(integrated_data["融合策略"].get("updated_at", "2000-01-01"))
                if (datetime.now() - updated_at).days < 1:  # 不超过1天
                    return integrated_data["融合策略"]
        except Exception:
            pass
        
        # 如果没有或已过期，重新整合
        integrated_data = self.integrate_habits(user_id)
        if integrated_data and "融合策略" in integrated_data:
            return integrated_data["融合策略"]
        
        # 如果无法整合，返回空结果
        return {}
    
    def get_platform_habit(self, user_id: str, platform: str) -> Dict[str, Any]:
        """获取特定平台的习惯数据
        
        Args:
            user_id: 用户ID
            platform: 平台名称 (douyin, bilibili, youtube)
            
        Returns:
            Dict[str, Any]: 平台习惯数据
        """
        if platform == "douyin":
            return self._get_douyin_habits(user_id)
        elif platform == "bilibili":
            return self._get_bilibili_habits(user_id)
        elif platform == "youtube":
            return self._get_youtube_habits(user_id)
        else:
            platform_logger.warning(f"不支持的平台: {platform}")
            return {}


# 全局单例
_platform_integrator = None

def get_platform_integrator() -> CrossPlatformIntegrator:
    """获取跨平台整合器实例
    
    Returns:
        CrossPlatformIntegrator: 跨平台整合器实例
    """
    global _platform_integrator
    if _platform_integrator is None:
        _platform_integrator = CrossPlatformIntegrator()
    return _platform_integrator

def integrate_user_habits(user_id: str) -> Dict[str, Any]:
    """整合用户跨平台习惯
    
    Args:
        user_id: 用户ID
        
    Returns:
        Dict[str, Any]: 整合后的跨平台习惯数据
    """
    integrator = get_platform_integrator()
    return integrator.integrate_habits(user_id)

def get_unified_preference(user_id: str) -> Dict[str, Any]:
    """获取用户的统一偏好表达
    
    Args:
        user_id: 用户ID
        
    Returns:
        Dict[str, Any]: 统一的偏好表达
    """
    integrator = get_platform_integrator()
    return integrator.get_unified_preference(user_id)

def get_platform_habit(user_id: str, platform: str) -> Dict[str, Any]:
    """获取特定平台的习惯数据
    
    Args:
        user_id: 用户ID
        platform: 平台名称 (douyin, bilibili, youtube)
        
    Returns:
        Dict[str, Any]: 平台习惯数据
    """
    integrator = get_platform_integrator()
    return integrator.get_platform_habit(user_id, platform) 