#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
实时A/B测试路由器

根据用户特征、偏好和行为，为用户分配最佳的内容或功能变体，
用于优化用户体验和测试不同混剪策略的效果。
"""

import os
import json
import time
import hashlib
import random
import numpy as np
import logging
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime
from sklearn.metrics.pairwise import cosine_similarity
from loguru import logger

from src.utils.log_handler import get_logger
from src.data.storage_manager import get_storage_manager
from src.audience.profile_builder import get_profile_engine

# 配置日志
ab_logger = get_logger("ab_router")

class ABRouter:
    """A/B测试路由器
    
    基于用户画像特征，为用户分配最优的内容或功能变体，
    同时记录测试数据用于效果分析与优化。
    """
    
    def __init__(self):
        """初始化A/B测试路由器"""
        # 获取存储管理器
        self.storage = get_storage_manager()
        
        # 获取用户画像引擎
        self.profile_engine = get_profile_engine()
        
        # 测试配置缓存
        self.test_configs = {}
        
        # 用户分配缓存
        self.user_assignments = {}
        
        # 特征向量缓存
        self.feature_vectors = {}
        
        # 默认分配策略
        self.default_assignment_strategy = "random"  # random, deterministic, weighted
        
        # 路由决策缓存有效期（秒）
        self.cache_ttl = 3600  # 1小时
        
        # 测量指标
        self.metrics = [
            "completion_rate",      # 完成率
            "engagement_time",      # 参与时间
            "interaction_count",    # 互动次数
            "share_rate",           # 分享率
            "retention_impact",     # 留存影响
            "conversion_rate"       # 转化率
        ]
        
        ab_logger.info("A/B测试路由器初始化完成")
    
    def route_version(self, user_id: str, variants: List[Dict[str, Any]]) -> Dict[str, Any]:
        """基于用户特征分配最优版本
        
        Args:
            user_id: 用户ID
            variants: 可选变体列表，每个变体应包含feature_vector

        Returns:
            Dict[str, Any]: 分配的最优变体
        """
        if not variants:
            ab_logger.warning(f"用户 {user_id} 的变体列表为空")
            return {}
        
        # 检查缓存中是否有有效的分配结果
        cached_result = self._check_cache(user_id, variants)
        if cached_result:
            ab_logger.debug(f"用户 {user_id} 使用缓存分配结果")
            return cached_result

        # 编码用户特征向量
        user_vector = self._encode_user(user_id)
        
        # 计算用户向量与各变体特征向量的相似度
        scores = [self._calculate_similarity(user_vector, v["feature_vector"]) for v in variants]
        
        # 选择最佳匹配的变体
        best_variant_index = np.argmax(scores)
        best_variant = variants[best_variant_index]
        
        # 记录分配结果
        self._record_assignment(user_id, best_variant, scores)
        
        # 缓存分配结果
        self._cache_assignment(user_id, best_variant)
        
        ab_logger.info(f"用户 {user_id} 被分配到变体 {best_variant.get('id', 'unknown')}")
        return best_variant
    
    def _encode_user(self, user_id: str) -> np.ndarray:
        """将用户特征编码为向量
        
        Args:
            user_id: 用户ID
            
        Returns:
            np.ndarray: 用户特征向量
        """
        # 检查缓存
        if user_id in self.feature_vectors and time.time() - self.feature_vectors[user_id]['timestamp'] < self.cache_ttl:
            return self.feature_vectors[user_id]['vector']
        
        # 获取用户画像
        user_profile = self.profile_engine.get_profile(user_id)
        if not user_profile:
            # 如果没有用户画像，返回默认向量
            ab_logger.warning(f"用户 {user_id} 没有画像数据，使用默认向量")
            default_vector = np.zeros(64)  # 默认维度为64
            
            # 缓存默认向量
            self.feature_vectors[user_id] = {
                'vector': default_vector,
                'timestamp': time.time()
            }
            
            return default_vector
        
        # 提取关键特征
        feature_dict = {
            # 内容偏好特征
            'content_preferences': self._normalize_preferences(user_profile.get('content_preferences', {})),
            
            # 情感响应特征
            'emotion_response': self._normalize_preferences(user_profile.get('emotion_response', {})),
            
            # 编辑风格偏好
            'editing_preferences': self._normalize_preferences(user_profile.get('editing_preferences', {})),
            
            # 叙事结构偏好
            'narrative_preferences': self._normalize_preferences(user_profile.get('narrative_preferences', {})),
            
            # 节奏偏好
            'pacing_preferences': self._normalize_preferences(user_profile.get('pacing_preferences', {}))
        }
        
        # 将特征字典转换为向量
        feature_vector = self._dict_to_vector(feature_dict)
        
        # 缓存用户向量
        self.feature_vectors[user_id] = {
            'vector': feature_vector,
            'timestamp': time.time()
        }
        
        return feature_vector
    
    def _normalize_preferences(self, preferences: Dict[str, Any]) -> Dict[str, float]:
        """规范化偏好数据
        
        Args:
            preferences: 原始偏好数据
            
        Returns:
            Dict[str, float]: 规范化后的偏好数据
        """
        result = {}
        
        # 提取偏好分数
        if isinstance(preferences, dict):
            for key, value in preferences.items():
                if isinstance(value, dict) and 'score' in value:
                    result[key] = float(value['score'])
                elif isinstance(value, (int, float)):
                    result[key] = float(value)
        
        # 如果偏好为空，返回空字典
        if not result:
            return {}
        
        # 规范化分数总和为1
        total = sum(result.values())
        if total > 0:
            for key in result:
                result[key] = result[key] / total
        
        return result
    
    def _dict_to_vector(self, feature_dict: Dict[str, Dict[str, float]]) -> np.ndarray:
        """将特征字典转换为向量
        
        Args:
            feature_dict: 特征字典
            
        Returns:
            np.ndarray: 特征向量
        """
        # 拼接所有特征值
        all_values = []
        
        # 处理每个特征类别
        for category, prefs in feature_dict.items():
            values = list(prefs.values())
            if values:
                all_values.extend(values)
            else:
                # 如果该类别没有值，添加一个默认值0
                all_values.append(0)
        
        # 转换为numpy数组
        return np.array(all_values)
    
    def _calculate_similarity(self, user_vector: np.ndarray, variant_vector: List[float]) -> float:
        """计算用户向量与变体向量的相似度
        
        Args:
            user_vector: 用户特征向量
            variant_vector: 变体特征向量
            
        Returns:
            float: 相似度分数
        """
        # 如果向量长度不同，调整为相同长度
        variant_vector_np = np.array(variant_vector)
        
        if len(user_vector) != len(variant_vector_np):
            min_len = min(len(user_vector), len(variant_vector_np))
            user_vector = user_vector[:min_len]
            variant_vector_np = variant_vector_np[:min_len]
        
        # 检查向量是否为零向量
        if np.all(user_vector == 0) or np.all(variant_vector_np == 0):
            return 0.0
        
        # 计算余弦相似度
        try:
            user_vector = user_vector.reshape(1, -1)
            variant_vector_np = variant_vector_np.reshape(1, -1)
            similarity = cosine_similarity(user_vector, variant_vector_np)[0][0]
            return float(similarity)
        except Exception as e:
            ab_logger.error(f"计算相似度时出错: {str(e)}")
            return 0.0
    
    def _check_cache(self, user_id: str, variants: List[Dict[str, Any]]) -> Dict[str, Any]:
        """检查缓存中是否有有效的分配结果
        
        Args:
            user_id: 用户ID
            variants: 变体列表
            
        Returns:
            Dict[str, Any]: 缓存的分配结果，如果无效则返回None
        """
        # 检查用户是否在缓存中
        if user_id not in self.user_assignments:
            return None
        
        cached_assignment = self.user_assignments[user_id]
        
        # 检查缓存是否过期
        if time.time() - cached_assignment.get('timestamp', 0) > self.cache_ttl:
            return None
        
        # 检查缓存的变体是否在当前变体列表中
        variant_id = cached_assignment.get('variant_id')
        for v in variants:
            if v.get('id') == variant_id:
                return v
        
        return None
    
    def _cache_assignment(self, user_id: str, variant: Dict[str, Any]) -> None:
        """缓存用户的分配结果
        
        Args:
            user_id: 用户ID
            variant: 分配的变体
        """
        self.user_assignments[user_id] = {
            'variant_id': variant.get('id'),
            'timestamp': time.time()
        }
    
    def _record_assignment(self, user_id: str, variant: Dict[str, Any], scores: List[float]) -> None:
        """记录用户分配结果
        
        Args:
            user_id: 用户ID
            variant: 分配的变体
            scores: 各变体的分数
        """
        try:
            assignment_record = {
                'user_id': user_id,
                'variant_id': variant.get('id'),
                'test_id': variant.get('test_id'),
                'timestamp': datetime.now().isoformat(),
                'scores': scores
            }
            
            # 存储分配记录
            self.storage.save_ab_assignment(user_id, assignment_record)
            
        except Exception as e:
            ab_logger.error(f"记录用户 {user_id} 的分配结果时出错: {str(e)}")
    
    def create_test(self, test_id: str, variants: List[Dict[str, Any]], config: Dict[str, Any] = None) -> Dict[str, Any]:
        """创建新的A/B测试
        
        Args:
            test_id: 测试ID
            variants: 变体列表
            config: 测试配置
            
        Returns:
            Dict[str, Any]: 测试配置
        """
        if not config:
            config = {}
        
        # 创建测试配置
        test_config = {
            'id': test_id,
            'variants': variants,
            'start_time': config.get('start_time', datetime.now().isoformat()),
            'end_time': config.get('end_time', None),
            'metrics': config.get('metrics', self.metrics),
            'assignment_strategy': config.get('assignment_strategy', self.default_assignment_strategy),
            'status': 'active',
            'created_at': datetime.now().isoformat()
        }
        
        # 缓存测试配置
        self.test_configs[test_id] = test_config
        
        # 存储测试配置
        try:
            self.storage.save_ab_test(test_id, test_config)
            ab_logger.info(f"创建A/B测试 {test_id}")
        except Exception as e:
            ab_logger.error(f"存储A/B测试 {test_id} 配置时出错: {str(e)}")
        
        return test_config
    
    def get_test(self, test_id: str) -> Dict[str, Any]:
        """获取测试配置
        
        Args:
            test_id: 测试ID
            
        Returns:
            Dict[str, Any]: 测试配置
        """
        # 检查缓存
        if test_id in self.test_configs:
            return self.test_configs[test_id]
        
        # 从存储中获取
        try:
            test_config = self.storage.get_ab_test(test_id)
            if test_config:
                # 更新缓存
                self.test_configs[test_id] = test_config
                return test_config
        except Exception as e:
            ab_logger.error(f"获取A/B测试 {test_id} 配置时出错: {str(e)}")
        
        return {}
    
    def record_event(self, user_id: str, variant_id: str, event_type: str, event_data: Dict[str, Any] = None) -> None:
        """记录用户事件
        
        Args:
            user_id: 用户ID
            variant_id: 变体ID
            event_type: 事件类型
            event_data: 事件数据
        """
        if not event_data:
            event_data = {}
        
        try:
            event_record = {
                'user_id': user_id,
                'variant_id': variant_id,
                'event_type': event_type,
                'timestamp': datetime.now().isoformat(),
                'data': event_data
            }
            
            # 存储事件记录
            self.storage.save_ab_event(user_id, event_record)
            
        except Exception as e:
            ab_logger.error(f"记录用户 {user_id} 的事件 {event_type} 时出错: {str(e)}")
    
    def analyze_test_results(self, test_id: str) -> Dict[str, Any]:
        """分析测试结果
        
        Args:
            test_id: 测试ID
            
        Returns:
            Dict[str, Any]: 测试结果分析
        """
        # 获取测试配置
        test_config = self.get_test(test_id)
        if not test_config:
            ab_logger.warning(f"找不到A/B测试 {test_id} 的配置")
            return {}
        
        # 获取变体ID列表
        variant_ids = [v.get('id') for v in test_config.get('variants', [])]
        
        # 获取测试指标
        metrics = test_config.get('metrics', self.metrics)
        
        # 获取事件数据
        events = self.storage.get_ab_events(test_id)
        
        # 分析结果
        results = {
            'test_id': test_id,
            'analysis_time': datetime.now().isoformat(),
            'metrics': {},
            'sample_sizes': {},
            'recommendations': []
        }
        
        # 计算每个变体的指标
        for variant_id in variant_ids:
            variant_events = [e for e in events if e.get('variant_id') == variant_id]
            results['sample_sizes'][variant_id] = len(variant_events)
            
            # 计算每个指标
            for metric in metrics:
                if metric not in results['metrics']:
                    results['metrics'][metric] = {}
                
                # 计算指标值（示例实现）
                metric_value = self._calculate_metric(variant_events, metric)
                results['metrics'][metric][variant_id] = metric_value
        
        # 生成建议
        results['recommendations'] = self._generate_recommendations(results)
        
        return results
    
    def _calculate_metric(self, events: List[Dict[str, Any]], metric: str) -> float:
        """计算指标值
        
        Args:
            events: 事件列表
            metric: 指标名称
            
        Returns:
            float: 指标值
        """
        # 根据不同指标计算
        if metric == "completion_rate":
            completions = sum(1 for e in events if e.get('event_type') == 'completion')
            starts = sum(1 for e in events if e.get('event_type') == 'start')
            return completions / starts if starts > 0 else 0
            
        elif metric == "engagement_time":
            engagement_times = [e.get('data', {}).get('duration', 0) for e in events if e.get('event_type') == 'engagement']
            return sum(engagement_times) / len(engagement_times) if engagement_times else 0
            
        elif metric == "interaction_count":
            interactions = sum(1 for e in events if e.get('event_type') == 'interaction')
            users = len(set(e.get('user_id') for e in events))
            return interactions / users if users > 0 else 0
            
        elif metric == "share_rate":
            shares = sum(1 for e in events if e.get('event_type') == 'share')
            views = sum(1 for e in events if e.get('event_type') == 'view')
            return shares / views if views > 0 else 0
            
        elif metric == "retention_impact":
            # 简化的留存计算
            return random.uniform(0.7, 1.0)  # 示例实现
            
        elif metric == "conversion_rate":
            conversions = sum(1 for e in events if e.get('event_type') == 'conversion')
            users = len(set(e.get('user_id') for e in events))
            return conversions / users if users > 0 else 0
            
        return 0
    
    def _generate_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """生成测试建议
        
        Args:
            results: 测试结果
            
        Returns:
            List[str]: 建议列表
        """
        recommendations = []
        
        # 示例实现：根据各指标找出最佳变体
        for metric, values in results.get('metrics', {}).items():
            if values:
                best_variant = max(values.items(), key=lambda x: x[1])
                recommendations.append(f"在{metric}指标上，变体{best_variant[0]}表现最佳，得分为{best_variant[1]:.2f}")
        
        # 根据样本大小给出建议
        sample_sizes = results.get('sample_sizes', {})
        if sample_sizes:
            min_sample = min(sample_sizes.values())
            if min_sample < 100:
                recommendations.append(f"测试样本量较小，建议继续收集数据以提高置信度")
        
        return recommendations


# 全局单例
_ab_router = None

def get_ab_router() -> ABRouter:
    """获取A/B测试路由器实例
    
    Returns:
        ABRouter: A/B测试路由器实例
    """
    global _ab_router
    if _ab_router is None:
        _ab_router = ABRouter()
    return _ab_router

def route_variant(user_id: str, variants: List[Dict[str, Any]]) -> Dict[str, Any]:
    """为用户分配最优变体的便捷函数
    
    Args:
        user_id: 用户ID
        variants: 变体列表
        
    Returns:
        Dict[str, Any]: 分配的变体
    """
    router = get_ab_router()
    return router.route_version(user_id, variants)

def create_ab_test(test_id: str, variants: List[Dict[str, Any]], config: Dict[str, Any] = None) -> Dict[str, Any]:
    """创建A/B测试的便捷函数
    
    Args:
        test_id: 测试ID
        variants: 变体列表
        config: 测试配置
        
    Returns:
        Dict[str, Any]: 测试配置
    """
    router = get_ab_router()
    return router.create_test(test_id, variants, config)

def record_ab_event(user_id: str, variant_id: str, event_type: str, event_data: Dict[str, Any] = None) -> None:
    """记录A/B测试事件的便捷函数
    
    Args:
        user_id: 用户ID
        variant_id: 变体ID
        event_type: 事件类型
        event_data: 事件数据
    """
    router = get_ab_router()
    router.record_event(user_id, variant_id, event_type, event_data)

def analyze_ab_results(test_id: str) -> Dict[str, Any]:
    """分析A/B测试结果的便捷函数
    
    Args:
        test_id: 测试ID
        
    Returns:
        Dict[str, Any]: 测试结果分析
    """
    router = get_ab_router()
    return router.analyze_test_results(test_id) 