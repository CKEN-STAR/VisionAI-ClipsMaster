#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
个性化推荐引擎模块

基于用户画像和内容特征，为用户提供个性化内容推荐。
"""

import os
import json
import time
from typing import Dict, List, Any, Optional, Tuple, Set, Union
from datetime import datetime, timedelta
import random
from collections import defaultdict, Counter
import numpy as np
from loguru import logger

from src.utils.log_handler import get_logger
from src.data.storage_manager import get_storage_manager
from src.audience.profile_builder import get_user_profile
from src.audience.preference_analyzer import get_user_genre_preferences, get_user_style_preferences

# 配置日志
recom_logger = get_logger("recommendation_engine")

class RecommendationEngine:
    """个性化推荐引擎
    
    基于用户画像和偏好分析，为用户提供个性化内容推荐，
    支持多种推荐策略和算法。
    """
    
    def __init__(self):
        """初始化推荐引擎"""
        # 获取存储管理器
        self.storage = get_storage_manager()
        
        # 推荐策略列表
        self.recommendation_strategies = [
            "content_based",   # 基于内容特征的推荐
            "collaborative",   # 协同过滤推荐
            "popularity",      # 基于流行度的推荐
            "trending",        # 基于趋势的推荐
            "diversity",       # 多样性推荐
            "serendipity"      # 意外发现推荐
        ]
        
        # 推荐结果缓存
        self.recommendation_cache = {}
        
        # 缓存过期时间（小时）
        self.cache_expiry_hours = 6
        
        # 相似度计算方法
        self.similarity_metrics = {
            "cosine": self._cosine_similarity,
            "jaccard": self._jaccard_similarity,
            "pearson": self._pearson_correlation
        }
        
        recom_logger.info("个性化推荐引擎初始化完成") 

    def get_personalized_recommendations(self, user_id: str, count: int = 10,
                                  strategies: List[str] = None) -> List[Dict[str, Any]]:
        """获取个性化推荐
        
        基于用户画像和偏好，为用户生成个性化内容推荐。
        
        Args:
            user_id: 用户ID
            count: 推荐结果数量
            strategies: 使用的推荐策略列表，默认使用所有策略
            
        Returns:
            List[Dict[str, Any]]: 推荐结果列表
        """
        # 检查缓存
        cache_key = f"{user_id}_recommendations_{count}"
        if cache_key in self.recommendation_cache:
            cache_time, recommendations = self.recommendation_cache[cache_key]
            # 检查缓存是否过期
            if (datetime.now() - cache_time).total_seconds() < self.cache_expiry_hours * 3600:
                recom_logger.debug(f"使用缓存的推荐结果，用户: {user_id}")
                return recommendations
        
        # 如果没有指定策略，使用所有策略
        if strategies is None:
            strategies = self.recommendation_strategies
        
        # 获取用户画像
        user_profile = get_user_profile(user_id)
        if not user_profile:
            recom_logger.warning(f"用户 {user_id} 没有画像数据，使用通用推荐")
            return self._get_generic_recommendations(count)
        
        # 使用各种策略生成推荐
        recommendations = []
        
        # 基于内容的推荐
        if "content_based" in strategies:
            content_based_recs = self._get_content_based_recommendations(user_id, user_profile)
            recommendations.extend(content_based_recs)
        
        # 协同过滤推荐
        if "collaborative" in strategies:
            collaborative_recs = self._get_collaborative_recommendations(user_id)
            recommendations.extend(collaborative_recs)
        
        # 流行度推荐
        if "popularity" in strategies:
            popularity_recs = self._get_popularity_recommendations(count // 3)
            recommendations.extend(popularity_recs)
        
        # 趋势推荐
        if "trending" in strategies:
            trending_recs = self._get_trending_recommendations(count // 3)
            recommendations.extend(trending_recs)
        
        # 多样性推荐
        if "diversity" in strategies:
            diversity_recs = self._get_diversity_recommendations(user_id, user_profile)
            recommendations.extend(diversity_recs)
        
        # 意外发现推荐
        if "serendipity" in strategies:
            serendipity_recs = self._get_serendipity_recommendations(user_id, user_profile)
            recommendations.extend(serendipity_recs)
        
        # 排序并去重
        unique_recommendations = self._deduplicate_recommendations(recommendations)
        
        # 限制结果数量
        final_recommendations = unique_recommendations[:count]
        
        # 缓存结果
        self.recommendation_cache[cache_key] = (datetime.now(), final_recommendations)
        
        recom_logger.info(f"为用户 {user_id} 生成了 {len(final_recommendations)} 个推荐")
        return final_recommendations
    
    def _get_content_based_recommendations(self, user_id: str, user_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """基于内容的推荐
        
        基于用户偏好和内容特征，推荐与用户喜好相似的内容。
        
        Args:
            user_id: 用户ID
            user_profile: 用户画像
            
        Returns:
            List[Dict[str, Any]]: 推荐结果列表
        """
        recommendations = []
        
        try:
            # 获取用户偏好
            genre_preferences = get_user_genre_preferences(user_id)
            style_preferences = get_user_style_preferences(user_id)
            
            # 提取用户喜欢的体裁
            favorite_genres = []
            if "favorites" in genre_preferences:
                favorite_genres = genre_preferences["favorites"]
            
            # 获取符合用户体裁偏好的内容
            for genre in favorite_genres:
                genre_content = self.storage.get_content_by_genre(genre, limit=5)
                for content in genre_content:
                    # 为推荐添加匹配原因
                    content["recommendation_reason"] = f"基于您对{genre}类型的喜好"
                    content["recommendation_type"] = "content_based"
                    content["recommendation_confidence"] = genre_preferences.get("confidence", 0.5)
                    recommendations.append(content)
            
            # 获取符合用户风格偏好的内容
            if "combined" in style_preferences and "top_styles" in style_preferences["combined"]:
                top_styles = style_preferences["combined"]["top_styles"]
                for style_info in top_styles[:2]:  # 使用前两个最高风格
                    style = style_info["style"]
                    style_content = self.storage.get_content_by_style(style, limit=3)
                    for content in style_content:
                        # 为推荐添加匹配原因
                        content["recommendation_reason"] = f"基于您对{style}风格的喜好"
                        content["recommendation_type"] = "content_based"
                        content["recommendation_confidence"] = style_info.get("avg_ratio", 0.5)
                        recommendations.append(content)
            
            return recommendations
        except Exception as e:
            recom_logger.error(f"获取基于内容的推荐失败: {str(e)}")
            return []
    
    def _get_collaborative_recommendations(self, user_id: str) -> List[Dict[str, Any]]:
        """协同过滤推荐
        
        基于相似用户的喜好，推荐相似用户喜欢但当前用户尚未接触的内容。
        
        Args:
            user_id: 用户ID
            
        Returns:
            List[Dict[str, Any]]: 推荐结果列表
        """
        recommendations = []
        
        try:
            # 获取相似用户
            similar_users = self.storage.get_similar_users(user_id, limit=5)
            
            # 获取用户已观看内容
            user_views = self.storage.get_user_view_history(user_id)
            viewed_content_ids = set(view["content_id"] for view in user_views if "content_id" in view)
            
            # 获取相似用户喜欢的内容
            for similar_user in similar_users:
                similar_id = similar_user["user_id"]
                similarity = similar_user["similarity"]
                
                # 获取相似用户喜欢的内容
                liked_content = self.storage.get_user_liked_content(similar_id, limit=5)
                
                for content in liked_content:
                    content_id = content["content_id"]
                    
                    # 排除用户已观看的内容
                    if content_id in viewed_content_ids:
                        continue
                    
                    # 为推荐添加匹配原因
                    content["recommendation_reason"] = "基于与您品味相似的用户喜欢的内容"
                    content["recommendation_type"] = "collaborative"
                    content["recommendation_confidence"] = similarity
                    recommendations.append(content)
            
            return recommendations
        except Exception as e:
            recom_logger.error(f"获取协同过滤推荐失败: {str(e)}")
            return []
    
    def _get_popularity_recommendations(self, count: int = 5) -> List[Dict[str, Any]]:
        """流行度推荐
        
        推荐平台上最受欢迎的内容。
        
        Args:
            count: 推荐结果数量
            
        Returns:
            List[Dict[str, Any]]: 推荐结果列表
        """
        try:
            popular_content = self.storage.get_popular_content(limit=count)
            
            # 为推荐添加匹配原因
            for content in popular_content:
                content["recommendation_reason"] = "平台热门内容"
                content["recommendation_type"] = "popularity"
                content["recommendation_confidence"] = 0.7  # 固定置信度
            
            return popular_content
        except Exception as e:
            recom_logger.error(f"获取流行度推荐失败: {str(e)}")
            return []
    
    def _get_trending_recommendations(self, count: int = 5) -> List[Dict[str, Any]]:
        """趋势推荐
        
        推荐最近上升趋势明显的内容。
        
        Args:
            count: 推荐结果数量
            
        Returns:
            List[Dict[str, Any]]: 推荐结果列表
        """
        try:
            trending_content = self.storage.get_trending_content(limit=count)
            
            # 为推荐添加匹配原因
            for content in trending_content:
                content["recommendation_reason"] = "近期热门趋势内容"
                content["recommendation_type"] = "trending"
                content["recommendation_confidence"] = 0.6  # 固定置信度
            
            return trending_content
        except Exception as e:
            recom_logger.error(f"获取趋势推荐失败: {str(e)}")
            return []
    
    def _get_diversity_recommendations(self, user_id: str, user_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """多样性推荐
        
        推荐与用户当前偏好有一定差异，但仍可能感兴趣的内容，增加推荐多样性。
        
        Args:
            user_id: 用户ID
            user_profile: 用户画像
            
        Returns:
            List[Dict[str, Any]]: 推荐结果列表
        """
        recommendations = []
        
        try:
            # 获取用户偏好
            genre_preferences = get_user_genre_preferences(user_id)
            
            # 排除用户最喜欢的体裁，获取其他体裁
            excluded_genres = []
            if "favorites" in genre_preferences:
                excluded_genres = genre_preferences["favorites"]
            
            # 获取用户可能感兴趣但尚未尝试的体裁
            related_genres = self.storage.get_related_genres(excluded_genres, limit=3)
            
            for genre in related_genres:
                genre_content = self.storage.get_content_by_genre(genre, limit=2)
                for content in genre_content:
                    content["recommendation_reason"] = f"尝试不同于您常看的{genre}类型"
                    content["recommendation_type"] = "diversity"
                    content["recommendation_confidence"] = 0.4  # 较低的置信度
                    recommendations.append(content)
            
            return recommendations
        except Exception as e:
            recom_logger.error(f"获取多样性推荐失败: {str(e)}")
            return []
    
    def _get_serendipity_recommendations(self, user_id: str, user_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """意外发现推荐
        
        推荐与用户当前偏好差异较大，但有可能带来意外惊喜的内容。
        
        Args:
            user_id: 用户ID
            user_profile: 用户画像
            
        Returns:
            List[Dict[str, Any]]: 推荐结果列表
        """
        recommendations = []
        
        try:
            # 随机选择一些高质量但与用户偏好差异较大的内容
            serendipity_content = self.storage.get_serendipity_content(limit=3)
            
            for content in serendipity_content:
                content["recommendation_reason"] = "您可能会喜欢的意外发现"
                content["recommendation_type"] = "serendipity"
                content["recommendation_confidence"] = 0.3  # 较低的置信度
                recommendations.append(content)
            
            return recommendations
        except Exception as e:
            recom_logger.error(f"获取意外发现推荐失败: {str(e)}")
            return []
    
    def _get_generic_recommendations(self, count: int = 10) -> List[Dict[str, Any]]:
        """获取通用推荐
        
        当用户没有画像数据时，提供通用的推荐结果。
        
        Args:
            count: 推荐结果数量
            
        Returns:
            List[Dict[str, Any]]: 推荐结果列表
        """
        recommendations = []
        
        # 获取一些流行内容
        popular_content = self._get_popularity_recommendations(count // 2)
        recommendations.extend(popular_content)
        
        # 获取一些趋势内容
        trending_content = self._get_trending_recommendations(count // 2)
        recommendations.extend(trending_content)
        
        # 排序并去重
        unique_recommendations = self._deduplicate_recommendations(recommendations)
        
        # 限制结果数量
        return unique_recommendations[:count]
    
    def _deduplicate_recommendations(self, recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """去除重复推荐
        
        对推荐结果进行去重，保留推荐置信度最高的版本。
        
        Args:
            recommendations: 原始推荐结果列表
            
        Returns:
            List[Dict[str, Any]]: 去重后的推荐结果列表
        """
        # 使用字典来去重，保留置信度最高的版本
        unique_dict = {}
        
        for rec in recommendations:
            content_id = rec.get("content_id", "")
            confidence = rec.get("recommendation_confidence", 0.0)
            
            if content_id not in unique_dict or confidence > unique_dict[content_id].get("recommendation_confidence", 0.0):
                unique_dict[content_id] = rec
        
        # 按置信度排序结果
        sorted_recommendations = sorted(
            unique_dict.values(),
            key=lambda x: x.get("recommendation_confidence", 0.0),
            reverse=True
        )
        
        return sorted_recommendations
    
    def get_style_recommendations(self, style_type: str, style_value: str, count: int = 10) -> List[Dict[str, Any]]:
        """获取特定风格的内容推荐
        
        基于指定的风格类型和值，推荐符合该风格的内容。
        
        Args:
            style_type: 风格类型（如narrative, visual, audio等）
            style_value: 风格值
            count: 推荐结果数量
            
        Returns:
            List[Dict[str, Any]]: 推荐结果列表
        """
        try:
            # 获取符合风格的内容
            style_content = self.storage.get_content_by_style(style_value, style_type, limit=count)
            
            # 为推荐添加匹配原因
            for content in style_content:
                content["recommendation_reason"] = f"符合{style_value}风格"
                content["recommendation_type"] = "style_specific"
                content["recommendation_confidence"] = 0.8  # 高置信度，因为是直接风格匹配
            
            return style_content
        except Exception as e:
            recom_logger.error(f"获取风格推荐失败: {str(e)}")
            return []
    
    def get_similar_content(self, content_id: str, count: int = 10, 
                          similarity_metric: str = "cosine") -> List[Dict[str, Any]]:
        """获取与指定内容相似的内容
        
        基于内容特征，推荐与给定内容相似的其他内容。
        
        Args:
            content_id: 内容ID
            count: 推荐结果数量
            similarity_metric: 相似度计算方法
            
        Returns:
            List[Dict[str, Any]]: 相似内容列表
        """
        try:
            # 获取内容特征
            content_features = self.storage.get_content_features(content_id)
            
            if not content_features:
                recom_logger.warning(f"无法获取内容 {content_id} 的特征")
                return []
            
            # 获取所有内容的特征
            all_content_features = self.storage.get_all_content_features(limit=100)
            
            # 计算相似度
            content_similarities = []
            
            for other_content in all_content_features:
                if other_content["content_id"] == content_id:
                    continue
                
                # 使用指定的相似度度量
                similarity_func = self.similarity_metrics.get(similarity_metric, self._cosine_similarity)
                
                # 计算特征向量的相似度
                similarity = similarity_func(
                    content_features.get("feature_vector", []),
                    other_content.get("feature_vector", [])
                )
                
                content_similarities.append({
                    "content_id": other_content["content_id"],
                    "similarity": similarity,
                    "metadata": other_content.get("metadata", {})
                })
            
            # 按相似度排序
            sorted_content = sorted(content_similarities, key=lambda x: x["similarity"], reverse=True)
            
            # 限制结果数量
            limited_content = sorted_content[:count]
            
            # 获取完整内容信息
            similar_content = []
            for item in limited_content:
                content_details = self.storage.get_content_details(item["content_id"])
                if content_details:
                    # 添加相似度信息
                    content_details["similarity"] = item["similarity"]
                    content_details["recommendation_reason"] = "与您正在查看的内容相似"
                    content_details["recommendation_type"] = "content_similarity"
                    content_details["recommendation_confidence"] = item["similarity"]
                    similar_content.append(content_details)
            
            return similar_content
        except Exception as e:
            recom_logger.error(f"获取相似内容失败: {str(e)}")
            return []
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度
        
        Args:
            vec1: 向量1
            vec2: 向量2
            
        Returns:
            float: 相似度值，范围[0,1]
        """
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0
        
        try:
            # 转换为numpy数组
            vec1_array = np.array(vec1)
            vec2_array = np.array(vec2)
            
            # 计算点积
            dot_product = np.dot(vec1_array, vec2_array)
            
            # 计算范数
            norm1 = np.linalg.norm(vec1_array)
            norm2 = np.linalg.norm(vec2_array)
            
            # 避免除零错误
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            # 计算余弦相似度
            similarity = dot_product / (norm1 * norm2)
            
            # 确保结果在[0,1]范围内
            return max(0.0, min(1.0, similarity))
        except Exception as e:
            recom_logger.error(f"计算余弦相似度失败: {str(e)}")
            return 0.0
    
    def _jaccard_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算Jaccard相似度
        
        对于分类特征，计算集合交集与并集的比值。
        
        Args:
            vec1: 向量1
            vec2: 向量2
            
        Returns:
            float: 相似度值，范围[0,1]
        """
        if not vec1 or not vec2:
            return 0.0
        
        try:
            # 将向量转换为集合
            set1 = set(vec1)
            set2 = set(vec2)
            
            # 计算交集和并集
            intersection = len(set1.intersection(set2))
            union = len(set1.union(set2))
            
            # 避免除零错误
            if union == 0:
                return 0.0
            
            # 计算Jaccard相似度
            similarity = intersection / union
            
            return similarity
        except Exception as e:
            recom_logger.error(f"计算Jaccard相似度失败: {str(e)}")
            return 0.0
    
    def _pearson_correlation(self, vec1: List[float], vec2: List[float]) -> float:
        """计算Pearson相关系数
        
        Args:
            vec1: 向量1
            vec2: 向量2
            
        Returns:
            float: 相关系数，范围[-1,1]，转换为[0,1]
        """
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0
        
        try:
            # 转换为numpy数组
            vec1_array = np.array(vec1)
            vec2_array = np.array(vec2)
            
            # 计算Pearson相关系数
            correlation = np.corrcoef(vec1_array, vec2_array)[0, 1]
            
            # 处理NaN结果
            if np.isnan(correlation):
                return 0.0
            
            # 将[-1,1]映射到[0,1]范围
            similarity = (correlation + 1) / 2
            
            return similarity
        except Exception as e:
            recom_logger.error(f"计算Pearson相关系数失败: {str(e)}")
            return 0.0


# 模块级函数

_recommendation_engine_instance = None

def get_recommendation_engine() -> RecommendationEngine:
    """获取推荐引擎单例实例
    
    Returns:
        RecommendationEngine: 推荐引擎实例
    """
    global _recommendation_engine_instance
    if _recommendation_engine_instance is None:
        _recommendation_engine_instance = RecommendationEngine()
    return _recommendation_engine_instance

def get_personalized_recommendations(user_id: str, count: int = 10,
                                   strategies: List[str] = None) -> List[Dict[str, Any]]:
    """获取个性化推荐
    
    Args:
        user_id: 用户ID
        count: 推荐结果数量
        strategies: 使用的推荐策略列表
        
    Returns:
        List[Dict[str, Any]]: 推荐结果列表
    """
    engine = get_recommendation_engine()
    return engine.get_personalized_recommendations(user_id, count, strategies)

def get_style_recommendations(style_type: str, style_value: str, count: int = 10) -> List[Dict[str, Any]]:
    """获取特定风格的内容推荐
    
    Args:
        style_type: 风格类型
        style_value: 风格值
        count: 推荐结果数量
        
    Returns:
        List[Dict[str, Any]]: 推荐结果列表
    """
    engine = get_recommendation_engine()
    return engine.get_style_recommendations(style_type, style_value, count)

def get_similar_content(content_id: str, count: int = 10,
                      similarity_metric: str = "cosine") -> List[Dict[str, Any]]:
    """获取与指定内容相似的内容
    
    Args:
        content_id: 内容ID
        count: 推荐结果数量
        similarity_metric: 相似度计算方法
        
    Returns:
        List[Dict[str, Any]]: 相似内容列表
    """
    engine = get_recommendation_engine()
    return engine.get_similar_content(content_id, count, similarity_metric) 