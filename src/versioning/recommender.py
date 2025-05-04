#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
智能版本推荐器

基于用户偏好和使用模式，推荐最适合的脚本版本，提供个性化版本选择体验。
该模块考虑用户喜好、设备类型和时间偏好等多个因素，实现智能化版本推荐。
"""

import os
import json
import logging
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime
import random
from pathlib import Path

from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler
import joblib

from src.utils.log_handler import get_logger

# 设置日志
logger = get_logger("version_recommender")

class VersionRecommender:
    """智能版本推荐器 - 根据用户配置文件推荐最适合的版本"""
    
    def __init__(self, model_path: Optional[str] = None):
        """
        初始化版本推荐器
        
        Args:
            model_path: 预训练模型路径，如果不提供则使用默认规则
        """
        self.model = None
        self.scaler = None
        self.feature_columns = [
            'preferred_genre', 
            'attention_span', 
            'emotional_preference', 
            'device_type', 
            'time_of_day'
        ]
        
        # 尝试加载模型
        if model_path and os.path.exists(model_path):
            self._load_model(model_path)
        else:
            logger.info("没有找到预训练模型，将使用规则引擎进行推荐")
            
        # 为基于规则的推荐初始化权重
        self.weight_map = {
            'preferred_genre': 0.3,
            'attention_span': 0.2,
            'emotional_preference': 0.3,
            'device_type': 0.1,
            'time_of_day': 0.1
        }
    
    def _load_model(self, model_path: str) -> bool:
        """
        加载预训练模型
        
        Args:
            model_path: 模型路径
            
        Returns:
            是否成功加载
        """
        try:
            model_data = joblib.load(model_path)
            self.model = model_data.get('model')
            self.scaler = model_data.get('scaler')
            self.feature_columns = model_data.get('features', self.feature_columns)
            logger.info(f"成功加载推荐模型: {model_path}")
            return True
        except Exception as e:
            logger.error(f"加载模型失败: {str(e)}")
            return False
    
    def _save_model(self, model_path: str) -> bool:
        """
        保存训练好的模型
        
        Args:
            model_path: 保存路径
            
        Returns:
            是否成功保存
        """
        if not self.model:
            logger.error("没有可保存的模型")
            return False
            
        try:
            model_data = {
                'model': self.model,
                'scaler': self.scaler,
                'features': self.feature_columns
            }
            os.makedirs(os.path.dirname(model_path), exist_ok=True)
            joblib.dump(model_data, model_path)
            logger.info(f"模型已保存到: {model_path}")
            return True
        except Exception as e:
            logger.error(f"保存模型失败: {str(e)}")
            return False
    
    def _prepare_features(self, user_profile: Dict[str, Any]) -> List[float]:
        """
        从用户配置文件准备特征向量
        
        Args:
            user_profile: 用户配置文件
            
        Returns:
            特征向量
        """
        # 提取特征
        features = []
        
        # 将文本型特征编码为数值
        genre_map = {
            'comedy': 0.1, 
            'drama': 0.3, 
            'action': 0.5, 
            'documentary': 0.7, 
            'horror': 0.9
        }
        device_map = {
            'mobile': 0.2,
            'tablet': 0.5,
            'desktop': 0.7,
            'tv': 0.9
        }
        time_map = {
            'morning': 0.2,
            'afternoon': 0.4,
            'evening': 0.6,
            'night': 0.8
        }
        
        # 提取特征值
        genre = user_profile.get('preferred_genre', 'drama')
        features.append(genre_map.get(genre, 0.5))
        
        attention_span = float(user_profile.get('attention_span', 30)) / 100.0
        features.append(min(1.0, max(0.0, attention_span)))
        
        emotion_pref = float(user_profile.get('emotional_preference', 0.5))
        features.append(min(1.0, max(-1.0, emotion_pref)))
        
        device = user_profile.get('device_type', 'desktop')
        features.append(device_map.get(device, 0.5))
        
        time = user_profile.get('time_of_day', 'evening')
        features.append(time_map.get(time, 0.5))
        
        return features
    
    def _score_version(self, version: Dict[str, Any], features: List[float]) -> float:
        """
        计算版本与用户特征的匹配分数
        
        Args:
            version: 版本数据
            features: 用户特征
            
        Returns:
            匹配分数
        """
        # 提取版本特征
        version_features = [
            version.get('genre_score', 0.5),
            version.get('length_score', 0.5),
            version.get('emotion_intensity', 0.5),
            version.get('device_optimization', 0.5),
            version.get('viewing_time_optimization', 0.5)
        ]
        
        # 计算加权相似度
        score = 0.0
        for i, (feat, weight) in enumerate(zip(features, self.weight_map.values())):
            score += (1 - abs(feat - version_features[i])) * weight
            
        return score
    
    def recommend(self, user_profile: Dict[str, Any]) -> int:
        """
        根据用户配置文件推荐最适合的版本
        
        Args:
            user_profile: 用户配置信息，包含偏好、设备等信息
            
        Returns:
            推荐的版本索引
        """
        # 获取特征
        features = self._prepare_features(user_profile)
        
        # 如果有模型，使用模型预测
        if self.model and self.scaler:
            try:
                # 标准化特征
                scaled_features = self.scaler.transform([features])
                # 预测
                prediction = self.model.predict(scaled_features)[0]
                logger.info(f"基于模型推荐版本: {prediction}")
                return prediction
            except Exception as e:
                logger.error(f"模型预测失败: {str(e)}")
                logger.info("回退到规则引擎")
        
        # 没有模型或预测失败时使用规则引擎
        # 为简化示例，这里只返回0，实际中可根据用户配置文件特征计算最匹配版本
        logger.info("使用规则引擎推荐默认版本")
        return 0
    
    def rank_versions(self, user_profile: Dict[str, Any], versions: List[Dict[str, Any]]) -> List[int]:
        """
        根据用户配置文件对所有版本进行排序
        
        Args:
            user_profile: 用户配置文件
            versions: 版本列表
            
        Returns:
            排序后的版本索引列表
        """
        features = self._prepare_features(user_profile)
        
        # 计算每个版本的分数
        scores = []
        for i, version in enumerate(versions):
            score = self._score_version(version, features)
            scores.append((i, score))
        
        # 按分数排序
        scores.sort(key=lambda x: x[1], reverse=True)
        
        # 返回排序后的索引
        return [idx for idx, _ in scores]
    
    def train(self, training_data: List[Dict[str, Any]], target_path: Optional[str] = None) -> bool:
        """
        训练版本推荐模型
        
        Args:
            training_data: 训练数据，包含用户配置文件和选择的版本
            target_path: 模型保存路径
            
        Returns:
            是否成功训练
        """
        if len(training_data) < 10:
            logger.warning("训练数据太少，无法训练有效模型")
            return False
            
        try:
            # 准备训练数据
            X = []
            y = []
            
            for item in training_data:
                user_profile = item.get('user_profile', {})
                chosen_version = item.get('chosen_version', 0)
                
                features = self._prepare_features(user_profile)
                X.append(features)
                y.append(chosen_version)
            
            # 标准化特征
            self.scaler = StandardScaler()
            X_scaled = self.scaler.fit_transform(X)
            
            # 训练模型 - 这里使用最近邻算法
            self.model = NearestNeighbors(n_neighbors=3, algorithm='auto')
            self.model.fit(X_scaled)
            
            logger.info("模型训练完成")
            
            # 保存模型
            if target_path:
                return self._save_model(target_path)
                
            return True
            
        except Exception as e:
            logger.error(f"训练失败: {str(e)}")
            return False
    
    def generate_synthetic_data(self, count: int = 100) -> List[Dict[str, Any]]:
        """
        生成合成训练数据用于测试
        
        Args:
            count: 要生成的数据条数
            
        Returns:
            合成训练数据
        """
        genres = ['comedy', 'drama', 'action', 'documentary', 'horror']
        devices = ['mobile', 'tablet', 'desktop', 'tv']
        times = ['morning', 'afternoon', 'evening', 'night']
        
        data = []
        
        for _ in range(count):
            # 生成随机用户配置文件
            user_profile = {
                'preferred_genre': random.choice(genres),
                'attention_span': random.randint(10, 90),
                'emotional_preference': random.uniform(-0.9, 0.9),
                'device_type': random.choice(devices),
                'time_of_day': random.choice(times)
            }
            
            # 确定选择的版本 - 基于简单规则
            chosen_version = 0
            
            # 根据特征偏好选择版本
            if user_profile['preferred_genre'] in ['action', 'horror'] and user_profile['emotional_preference'] > 0.5:
                chosen_version = 1
            elif user_profile['attention_span'] < 30 and user_profile['device_type'] == 'mobile':
                chosen_version = 2
            elif user_profile['preferred_genre'] in ['drama', 'documentary'] and user_profile['emotional_preference'] < -0.3:
                chosen_version = 3
                
            data.append({
                'user_profile': user_profile,
                'chosen_version': chosen_version
            })
            
        return data


# 便捷函数
def get_version_recommender(model_path: Optional[str] = None) -> VersionRecommender:
    """
    获取版本推荐器实例
    
    Args:
        model_path: 可选的模型路径
        
    Returns:
        版本推荐器实例
    """
    model_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "models", "recommender"
    )
    
    default_model_path = os.path.join(model_dir, "version_recommender.joblib")
    
    if model_path is None and os.path.exists(default_model_path):
        model_path = default_model_path
        
    return VersionRecommender(model_path)

def recommend_version(user_profile: Dict[str, Any], versions: List[Dict[str, Any]]) -> int:
    """
    快捷函数：根据用户配置文件推荐最适合的版本
    
    Args:
        user_profile: 用户配置文件
        versions: 可用版本列表
        
    Returns:
        推荐的版本索引
    """
    recommender = get_version_recommender()
    if versions:
        return recommender.rank_versions(user_profile, versions)[0]
    else:
        return recommender.recommend(user_profile)


if __name__ == "__main__":
    # 简单测试
    import logging
    logging.basicConfig(level=logging.INFO)
    
    recommender = VersionRecommender()
    
    # 生成测试数据
    test_data = recommender.generate_synthetic_data(200)
    logger.info(f"生成了 {len(test_data)} 条合成训练数据")
    
    # 训练模型
    model_path = "models/recommender/version_recommender_test.joblib"
    success = recommender.train(test_data, model_path)
    
    # 测试推荐
    test_profile = {
        'preferred_genre': 'action',
        'attention_span': 45,
        'emotional_preference': 0.7,
        'device_type': 'desktop',
        'time_of_day': 'evening'
    }
    
    recommended_version = recommender.recommend(test_profile)
    logger.info(f"为测试用户推荐的版本: {recommended_version}") 