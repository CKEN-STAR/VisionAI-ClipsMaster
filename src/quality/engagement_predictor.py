#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
观众行为预测器模块

基于视频内容特征，预测用户观看行为和互动模式。
提供多种预测功能:
1. 观看时长预测
2. 完播率预测
3. 互动度预测
4. 留存率预测
5. 分享率预测
"""

import os
import json
import numpy as np
import pickle
from typing import Dict, List, Any, Optional, Tuple, Union
from pathlib import Path

from loguru import logger
from src.utils.file_handler import ensure_dir_exists


class BasePredictor:
    """预测器基类"""
    
    def __init__(self, model_path: Optional[str] = None):
        """
        初始化预测器
        
        Args:
            model_path: 预训练模型路径，如果不提供则使用默认路径
        """
        self.model = None
        self.feature_importance = {}
        self.is_trained = False
        
        # 加载模型(如果路径有效)
        if model_path and os.path.exists(model_path):
            self._load_model(model_path)
    
    def _load_model(self, model_path: str) -> None:
        """
        加载预训练模型
        
        Args:
            model_path: 模型文件路径
        """
        try:
            with open(model_path, 'rb') as f:
                model_data = pickle.load(f)
                
            self.model = model_data.get('model')
            self.feature_importance = model_data.get('feature_importance', {})
            self.is_trained = True
            
            logger.info(f"已加载预测器模型: {model_path}")
        except Exception as e:
            logger.error(f"加载模型失败 {model_path}: {str(e)}")
            self.model = None
            self.is_trained = False
    
    def _save_model(self, model_path: str) -> bool:
        """
        保存模型到文件
        
        Args:
            model_path: 保存路径
            
        Returns:
            bool: 是否保存成功
        """
        try:
            model_dir = os.path.dirname(model_path)
            ensure_dir_exists(model_dir)
            
            model_data = {
                'model': self.model,
                'feature_importance': self.feature_importance,
                'created_at': str(np.datetime64('now'))
            }
            
            with open(model_path, 'wb') as f:
                pickle.dump(model_data, f)
                
            logger.info(f"已保存预测器模型: {model_path}")
            return True
        except Exception as e:
            logger.error(f"保存模型失败 {model_path}: {str(e)}")
            return False
            
    def _validate_features(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证并标准化特征
        
        Args:
            features: 原始特征
            
        Returns:
            Dict[str, Any]: 标准化后的特征
        """
        # 基类中提供默认实现，子类可以重写
        return features
    
    def get_feature_importance(self) -> Dict[str, float]:
        """
        获取特征重要性
        
        Returns:
            Dict[str, float]: 特征重要性字典
        """
        return self.feature_importance


class WatchTimePredictor(BasePredictor):
    """
    观看时长预测器
    
    基于视频特征预测观众平均观看时长，
    可用于评估视频对观众的吸引力
    """
    
    def __init__(self, model_path: Optional[str] = None):
        """
        初始化观看时长预测器
        
        Args:
            model_path: 预训练模型路径，如果不提供则使用默认路径
        """
        if model_path is None:
            model_path = os.path.join("data", "models", "engagement", "watch_time_predictor.pkl")
        
        super().__init__(model_path)
        
        # 预测参数
        self.config = {
            "feature_weights": {
                "opening_shots": 0.15,       # 开场镜头重要性
                "first_dialog": 0.12,        # 首个对白重要性
                "initial_bgm": 0.10,         # 初始背景音乐重要性
                "story_hook": 0.20,          # 故事钩子重要性
                "pacing": 0.15,              # 节奏重要性
                "conflict_intensity": 0.18,  # 冲突强度重要性
                "visual_quality": 0.10       # 视觉质量重要性
            },
            "engagement_thresholds": {
                "high": 0.8,       # 高参与度阈值
                "medium": 0.5,     # 中等参与度阈值
                "low": 0.3         # 低参与度阈值
            }
        }
        
        # 如果没有加载模型，则创建一个简单的预测模型
        if not self.is_trained:
            self._initialize_simple_model()
    
    def _initialize_simple_model(self) -> None:
        """初始化一个简单的预测模型"""
        # 这里我们使用基于规则的简单模型，真实系统会使用机器学习模型
        self.model = {'weights': self.config['feature_weights']}
        self.feature_importance = self.config['feature_weights']
        self.is_trained = True
    
    def predict_watch_time(self, video_features: Dict[str, Any]) -> float:
        """
        预测观看时长百分比
        
        Args:
            video_features: 视频特征字典
            
        Returns:
            float: 预计观看时长百分比(0.0-1.0)
        """
        if not self.is_trained or not self.model:
            logger.warning("模型未训练，使用默认预测")
            return 0.5  # 默认预测中等观看率
        
        # 验证并补全特征
        validated_features = self._validate_features(video_features)
        
        try:
            # 使用简单线性模型进行预测
            watch_time_score = 0.0
            weights = self.model['weights']
            
            # 计算加权得分
            for feature, weight in weights.items():
                if feature in validated_features:
                    feature_value = validated_features[feature]
                    # 确保特征值为数值类型
                    if isinstance(feature_value, (int, float)):
                        watch_time_score += feature_value * weight
                    else:
                        # 非数值特征使用默认值
                        watch_time_score += 0.5 * weight
                else:
                    # 缺失特征使用默认值
                    watch_time_score += 0.5 * weight
            
            # 标准化到[0,1]范围
            watch_time_score = max(0.0, min(1.0, watch_time_score))
            
            logger.debug(f"预测观看时长评分: {watch_time_score:.2f}")
            return watch_time_score
            
        except Exception as e:
            logger.error(f"预测失败: {str(e)}")
            return 0.5  # 出错时返回默认值
    
    def predict_audience_retention(self, video_features: Dict[str, Any]) -> float:
        """
        预测前15秒观众留存率
        
        Args:
            video_features: 视频特征字典
            
        Returns:
            float: 预计留存率(0.0-1.0)
        """
        # 提取关键开场特征
        opening_features = {
            'opening_shots': video_features.get('opening_shots', 0.5),
            'first_dialog': video_features.get('first_dialog', 0.5),
            'initial_bgm': video_features.get('initial_bgm', 0.5)
        }
        
        # 预测留存率 - 这里重点关注开场特征
        retention_score = 0.0
        total_weight = 0.0
        
        for feature, value in opening_features.items():
            weight = self.config['feature_weights'].get(feature, 0.1)
            retention_score += value * weight
            total_weight += weight
        
        if total_weight > 0:
            retention_score /= total_weight
            
        # 应用非线性调整，开场效果对留存率影响更大
        retention_score = 0.3 + 0.7 * retention_score  # 基础留存率至少0.3
        
        return max(0.0, min(1.0, retention_score))
    
    def _validate_features(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证并标准化特征
        
        Args:
            features: 原始特征
            
        Returns:
            Dict[str, Any]: 标准化后的特征
        """
        validated = {}
        
        # 确保所有必要特征都存在
        for feature in self.config['feature_weights'].keys():
            # 使用原始特征或默认值
            validated[feature] = features.get(feature, 0.5)
            
            # 确保特征值在[0,1]范围内
            if isinstance(validated[feature], (int, float)):
                validated[feature] = max(0.0, min(1.0, validated[feature]))
        
        return validated
    
    def train(self, training_data: List[Dict[str, Any]]) -> bool:
        """
        训练预测模型
        
        Args:
            training_data: 训练数据列表，每条数据包含特征和实际观看时长
            
        Returns:
            bool: 是否训练成功
        """
        if not training_data:
            logger.error("训练数据为空")
            return False
        
        try:
            logger.info(f"开始训练观看时长预测器，数据量: {len(training_data)}")
            
            # 在实际应用中，这里会训练一个真正的机器学习模型
            # 这里仅用简单方法优化权重
            
            # 提取特征和标签
            X = []
            y = []
            
            for item in training_data:
                features = self._validate_features(item.get('features', {}))
                watch_time = item.get('watch_time', 0.5)
                
                # 转换为特征向量
                feature_vector = [features.get(f, 0.5) for f in self.config['feature_weights'].keys()]
                X.append(feature_vector)
                y.append(watch_time)
            
            # 简化训练：计算特征和观看时长的相关性来更新权重
            X = np.array(X)
            y = np.array(y)
            
            # 计算每个特征的相关系数
            correlations = {}
            feature_names = list(self.config['feature_weights'].keys())
            
            for i, feature in enumerate(feature_names):
                # 计算相关系数
                if X[:, i].std() > 0 and np.std(y) > 0:
                    corr = np.corrcoef(X[:, i], y)[0, 1]
                    correlations[feature] = abs(corr)  # 使用绝对值
                else:
                    correlations[feature] = 0.1  # 默认相关性
            
            # 归一化相关系数作为权重
            total_corr = sum(correlations.values())
            if total_corr > 0:
                weights = {f: c / total_corr for f, c in correlations.items()}
            else:
                weights = {f: 1.0 / len(correlations) for f in correlations}
            
            # 更新模型
            self.model = {'weights': weights}
            self.feature_importance = weights
            self.is_trained = True
            
            logger.info("观看时长预测器训练完成")
            logger.debug(f"特征重要性: {self.feature_importance}")
            
            return True
        except Exception as e:
            logger.error(f"训练失败: {str(e)}")
            return False


class InteractionPredictor(BasePredictor):
    """
    观众互动预测器
    
    预测观众与视频的互动行为，如点赞、评论、分享等
    """
    
    def __init__(self, model_path: Optional[str] = None):
        """
        初始化互动预测器
        
        Args:
            model_path: 预训练模型路径
        """
        if model_path is None:
            model_path = os.path.join("data", "models", "engagement", "interaction_predictor.pkl")
        
        super().__init__(model_path)
        
        # 互动类型及其阈值
        self.interaction_types = {
            'like': 0.6,       # 点赞阈值
            'comment': 0.7,    # 评论阈值
            'share': 0.8,      # 分享阈值
            'save': 0.75       # 收藏阈值
        }
        
        # 互动特征权重
        self.interaction_weights = {
            'emotional_impact': 0.3,     # 情感冲击力
            'conflict_intensity': 0.2,   # 冲突强度
            'novelty': 0.15,             # 新颖度
            'relatability': 0.25,        # 共鸣度
            'production_quality': 0.1    # 制作质量
        }
        
        # 默认模型初始化
        if not self.is_trained:
            self._initialize_simple_model()
    
    def _initialize_simple_model(self) -> None:
        """初始化简单预测模型"""
        self.model = {
            'interaction_weights': self.interaction_weights,
            'interaction_thresholds': self.interaction_types
        }
        self.feature_importance = self.interaction_weights
        self.is_trained = True
    
    def predict_interactions(self, video_features: Dict[str, Any]) -> Dict[str, float]:
        """
        预测视频的各类互动概率
        
        Args:
            video_features: 视频特征
            
        Returns:
            Dict[str, float]: 各类互动的概率
        """
        if not self.is_trained or not self.model:
            logger.warning("模型未训练，使用默认预测")
            return {k: 0.5 for k in self.interaction_types.keys()}
        
        # 验证特征
        validated_features = self._validate_features(video_features)
        
        # 计算互动基础分
        base_score = 0.0
        total_weight = 0.0
        
        for feature, weight in self.interaction_weights.items():
            if feature in validated_features:
                base_score += validated_features[feature] * weight
                total_weight += weight
        
        if total_weight > 0:
            base_score /= total_weight
        
        # 预测各类互动概率
        predictions = {}
        for interaction_type, threshold in self.interaction_types.items():
            # 不同互动类型有不同的计算调整
            if interaction_type == 'like':
                # 点赞更容易受情感影响
                emotional_factor = validated_features.get('emotional_impact', 0.5)
                predictions[interaction_type] = 0.7 * base_score + 0.3 * emotional_factor
            elif interaction_type == 'share':
                # 分享更看重新颖度和共鸣度
                novelty = validated_features.get('novelty', 0.5)
                relatability = validated_features.get('relatability', 0.5)
                predictions[interaction_type] = 0.5 * base_score + 0.3 * novelty + 0.2 * relatability
            elif interaction_type == 'comment':
                # 评论与冲突强度相关
                conflict = validated_features.get('conflict_intensity', 0.5)
                predictions[interaction_type] = 0.6 * base_score + 0.4 * conflict
            else:
                # 其他互动类型
                predictions[interaction_type] = base_score
            
            # 确保结果在[0,1]范围内
            predictions[interaction_type] = max(0.0, min(1.0, predictions[interaction_type]))
        
        return predictions
    
    def _validate_features(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """验证特征"""
        validated = {}
        
        # 确保所有关键特征存在
        for feature in self.interaction_weights.keys():
            validated[feature] = features.get(feature, 0.5)
            
            # 范围限制
            if isinstance(validated[feature], (int, float)):
                validated[feature] = max(0.0, min(1.0, validated[feature]))
        
        return validated


# 导出模块
__all__ = ['WatchTimePredictor', 'InteractionPredictor'] 