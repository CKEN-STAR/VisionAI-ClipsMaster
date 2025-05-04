#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
偏好预测模型模块

基于用户行为和画像数据，预测用户对不同内容的偏好概率分布，
支持个性化内容推荐和智能混剪生成。
"""

import os
import json
import time
import pickle
import logging
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Set, Union
from datetime import datetime
from collections import defaultdict, Counter
from pathlib import Path

from loguru import logger
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

from src.utils.log_handler import get_logger
from src.data.storage_manager import get_storage_manager
from src.audience.profile_builder import get_profile_engine, get_user_profile
from src.audience.behavior_decoder import get_behavior_decoder, decode_user_behavior, get_user_preferences

# 配置日志
predictor_logger = get_logger("preference_predictor")

class PreferencePredictor:
    """用户偏好预测模型
    
    基于用户历史行为和画像特征，预测用户对不同内容的偏好，
    包括创作风格偏好的预测和内容消费偏好的预测。
    """
    
    def __init__(self, model_path: Optional[str] = None):
        """初始化偏好预测模型
        
        Args:
            model_path: 预训练模型路径，如果提供则加载现有模型
        """
        # 获取存储管理器
        self.storage = get_storage_manager()
        
        # 获取用户画像引擎
        self.profile_engine = get_profile_engine()
        
        # 获取行为解码器
        self.behavior_decoder = get_behavior_decoder()
        
        # 模型配置
        self.config = {
            # 模型超参数
            "model_params": {
                "n_estimators": 100,
                "max_depth": 10,
                "min_samples_split": 5,
                "min_samples_leaf": 2
            },
            
            # 特征重要性阈值
            "feature_importance_threshold": 0.01,
            
            # 预测置信度阈值
            "confidence_threshold": 0.65,
            
            # 预测维度
            "prediction_dimensions": [
                "complexity",      # 剧情复杂度(简单/适中/烧脑)
                "emotion_tone",    # 情感基调(轻松/严肃/黑暗)
                "pacing",          # 节奏偏好(快/中/慢)
            ],
            
            # 预测类别配置
            "complexity_categories": ["simple", "medium", "complex"],
            "emotion_tone_categories": ["light", "neutral", "dark"],
            "pacing_categories": ["fast", "medium", "slow"],
            
            # 模型文件路径
            "model_dir": os.path.join("data", "models", "preference_prediction"),
            "complexity_model_file": "complexity_model.pkl",
            "emotion_tone_model_file": "emotion_tone_model.pkl",
            "pacing_model_file": "pacing_model.pkl"
        }
        
        # 初始化模型
        self.models = {}
        self.feature_encoders = {}
        
        # 加载或创建模型
        self._initialize_models(model_path)
        
        predictor_logger.info("偏好预测模型初始化完成")
    
    def _initialize_models(self, model_path: Optional[str] = None):
        """初始化或加载预训练模型
        
        Args:
            model_path: 预训练模型路径，如果提供则加载现有模型
        """
        # 确保模型目录存在
        os.makedirs(self.config["model_dir"], exist_ok=True)
        
        for dimension in self.config["prediction_dimensions"]:
            model_file = f"{dimension}_model.pkl"
            encoder_file = f"{dimension}_encoder.pkl"
            
            if model_path and os.path.exists(os.path.join(model_path, model_file)):
                # 加载已有模型
                try:
                    with open(os.path.join(model_path, model_file), 'rb') as f:
                        self.models[dimension] = pickle.load(f)
                    
                    with open(os.path.join(model_path, encoder_file), 'rb') as f:
                        self.feature_encoders[dimension] = pickle.load(f)
                    
                    predictor_logger.info(f"成功加载现有的 {dimension} 预测模型")
                except Exception as e:
                    predictor_logger.error(f"加载 {dimension} 模型失败: {str(e)}")
                    self._create_model(dimension)
            else:
                # 创建新模型
                self._create_model(dimension)
    
    def _create_model(self, dimension: str):
        """创建指定维度的预测模型
        
        Args:
            dimension: 预测维度名称
        """
        predictor_logger.info(f"创建新的 {dimension} 预测模型")
        
        # 创建梯度提升决策树模型
        model = GradientBoostingClassifier(
            n_estimators=self.config["model_params"]["n_estimators"],
            max_depth=self.config["model_params"]["max_depth"],
            min_samples_split=self.config["model_params"]["min_samples_split"],
            min_samples_leaf=self.config["model_params"]["min_samples_leaf"],
            random_state=42
        )
        
        # 将模型保存到模型字典
        self.models[dimension] = model
        
        # 创建特征编码器
        encoder = ColumnTransformer(
            transformers=[
                ('num', StandardScaler(), [0, 1, 2, 3, 4]),  # 数值特征
                ('cat', OneHotEncoder(handle_unknown='ignore'), [5, 6, 7])  # 分类特征
            ],
            remainder='passthrough'
        )
        
        self.feature_encoders[dimension] = encoder
    
    def predict(self, user_id: str) -> Dict[str, Any]:
        """预测用户偏好
        
        基于用户画像和偏好数据，预测用户对不同内容特性的偏好概率分布。
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict[str, Any]: 各维度偏好预测结果
        """
        predictor_logger.info(f"开始预测用户 {user_id} 的内容偏好")
        
        # 获取用户特征
        user_features = self._extract_user_features(user_id)
        if not user_features:
            predictor_logger.warning(f"未能提取用户 {user_id} 的有效特征")
            return {"user_id": user_id, "status": "error", "message": "无法提取有效特征"}
        
        # 预测结果
        predictions = {}
        
        # 为每个维度进行预测
        for dimension in self.config["prediction_dimensions"]:
            if dimension not in self.models:
                continue
            
            try:
                # 准备特征数据
                feature_vector = self._prepare_features(user_features, dimension)
                
                # 获取预测结果及概率
                prediction, probabilities = self._predict_dimension(dimension, feature_vector)
                
                # 计算置信度
                confidence = max(probabilities)
                
                # 记录预测结果
                predictions[dimension] = {
                    "prediction": prediction,
                    "probabilities": dict(zip(self._get_categories_for_dimension(dimension), probabilities.tolist())),
                    "confidence": confidence
                }
                
                predictor_logger.debug(f"用户 {user_id} 的 {dimension} 偏好预测结果: {prediction}, 置信度: {confidence:.2f}")
            except Exception as e:
                predictor_logger.error(f"预测用户 {user_id} 的 {dimension} 偏好失败: {str(e)}")
                predictions[dimension] = {"error": str(e)}
        
        # 组装预测结果
        result = {
            "user_id": user_id,
            "predictions": predictions,
            "predicted_at": datetime.now().isoformat(),
            "status": "success"
        }
        
        # 保存预测结果
        self._save_prediction_result(user_id, result)
        
        predictor_logger.info(f"用户 {user_id} 的偏好预测完成")
        return result
    
    def _get_categories_for_dimension(self, dimension: str) -> List[str]:
        """获取指定维度的类别列表
        
        Args:
            dimension: 预测维度名称
            
        Returns:
            List[str]: 类别列表
        """
        dimension_categories = self.config.get(f"{dimension}_categories")
        if dimension_categories:
            return dimension_categories
        
        # 默认返回通用类别
        return ["low", "medium", "high"]
    
    def _predict_dimension(self, dimension: str, feature_vector: np.ndarray) -> Tuple[str, np.ndarray]:
        """对指定维度进行预测
        
        Args:
            dimension: 预测维度名称
            feature_vector: 特征向量
            
        Returns:
            Tuple[str, np.ndarray]: 预测结果和概率分布
        """
        model = self.models[dimension]
        categories = self._get_categories_for_dimension(dimension)
        
        # 进行预测
        probabilities = model.predict_proba([feature_vector])[0]
        prediction_index = np.argmax(probabilities)
        prediction = categories[prediction_index]
        
        return prediction, probabilities
    
    def _extract_user_features(self, user_id: str) -> Optional[Dict[str, Any]]:
        """提取用户特征
        
        从用户画像和偏好数据中提取预测所需的特征。
        
        Args:
            user_id: 用户ID
            
        Returns:
            Optional[Dict[str, Any]]: 用户特征，如果提取失败则返回None
        """
        # 获取用户画像
        profile = get_user_profile(user_id)
        if not profile:
            predictor_logger.warning(f"未找到用户 {user_id} 的画像数据")
            return None
        
        # 获取用户偏好
        preferences = get_user_preferences(user_id)
        if not preferences or preferences.get("status") != "success":
            predictor_logger.warning(f"未找到用户 {user_id} 的偏好数据")
            # 尝试解码用户行为
            preferences = decode_user_behavior(user_id)
            if not preferences or preferences.get("status") != "success":
                return None
        
        # 提取特征
        features = {}
        
        # 1. 基本人口统计学特征
        basic_info = profile.get("basic_info", {})
        features["age_group"] = basic_info.get("age_group", "unknown")
        features["gender"] = basic_info.get("gender", "unknown")
        features["region"] = basic_info.get("region", "unknown")
        
        # 2. 内容偏好特征
        content_prefs = preferences.get("content_preferences", {})
        genre_strengths = {}
        for genre, data in content_prefs.get("genres", {}).items():
            genre_strengths[genre] = data.get("score", 0)
        features["top_genres"] = sorted(genre_strengths.items(), key=lambda x: x[1], reverse=True)[:3]
        
        # 3. 情感偏好特征
        emotion_prefs = preferences.get("emotion_preferences", {})
        features["emotion_intensity"] = emotion_prefs.get("intensity", 0.5)
        features["emotion_valence"] = emotion_prefs.get("valence", 0)
        
        # 提取主要情感偏好
        primary_emotions = emotion_prefs.get("primary_emotions", {})
        emotion_scores = {}
        for emotion, data in primary_emotions.items():
            emotion_scores[emotion] = data.get("score", 0)
        features["top_emotions"] = sorted(emotion_scores.items(), key=lambda x: x[1], reverse=True)[:2]
        
        # 4. 叙事结构偏好特征
        narrative_prefs = preferences.get("narrative_preferences", {})
        features["complexity_preference"] = narrative_prefs.get("complexity", 0.5)
        
        # 提取结构偏好
        structure_prefs = narrative_prefs.get("structures", {})
        structure_scores = {}
        for structure, data in structure_prefs.items():
            structure_scores[structure] = data.get("score", 0)
        features["top_structures"] = sorted(structure_scores.items(), key=lambda x: x[1], reverse=True)[:2]
        
        # 5. 节奏偏好特征
        pacing_prefs = preferences.get("pacing_preferences", {})
        scene_duration = pacing_prefs.get("scene_duration", {})
        features["preferred_scene_duration"] = scene_duration.get("preferred", 8.0)
        
        # 提取节奏偏好
        pace_prefs = pacing_prefs.get("overall_pace", {})
        pace_scores = {}
        for pace, data in pace_prefs.items():
            pace_scores[pace] = data.get("score", 0)
        features["top_paces"] = sorted(pace_scores.items(), key=lambda x: x[1], reverse=True)[:2]
        
        # 6. 设备偏好特征
        device_prefs = preferences.get("device_preferences", {})
        features["optimal_duration"] = device_prefs.get("optimal_duration")
        features["optimal_resolution"] = device_prefs.get("optimal_resolution")
        
        # 7. 行为模式特征
        behavior_patterns = profile.get("behavior_patterns", {})
        features["completion_rate"] = behavior_patterns.get("completion_rate", 0)
        features["engagement_level"] = behavior_patterns.get("engagement_level", "low")
        
        return features
    
    def _prepare_features(self, features: Dict[str, Any], dimension: str) -> np.ndarray:
        """准备用于预测的特征向量
        
        根据不同维度选择相关特征并转换为模型输入格式。
        
        Args:
            features: 用户特征字典
            dimension: 预测维度名称
            
        Returns:
            np.ndarray: 处理后的特征向量
        """
        # 基础特征提取 - 对所有维度通用的特征
        feature_vector = []
        
        # 1. 数值特征
        feature_vector.append(features.get("completion_rate", 0))
        feature_vector.append(features.get("emotion_intensity", 0.5))
        feature_vector.append(features.get("emotion_valence", 0))
        feature_vector.append(features.get("complexity_preference", 0.5))
        feature_vector.append(features.get("preferred_scene_duration", 8.0))
        
        # 2. 分类特征
        feature_vector.append(features.get("age_group", "unknown"))
        feature_vector.append(features.get("gender", "unknown"))
        feature_vector.append(features.get("engagement_level", "low"))
        
        # 维度特定特征
        if dimension == "complexity":
            # 针对剧情复杂度的特定特征
            top_structures = features.get("top_structures", [])
            if top_structures:
                # 添加最偏好的叙事结构
                feature_vector.append(top_structures[0][0])
                feature_vector.append(top_structures[0][1])  # 分数
            else:
                feature_vector.append("unknown")
                feature_vector.append(0)
        
        elif dimension == "emotion_tone":
            # 针对情感基调的特定特征
            top_emotions = features.get("top_emotions", [])
            if top_emotions:
                # 添加最偏好的情感类型
                feature_vector.append(top_emotions[0][0])
                feature_vector.append(top_emotions[0][1])  # 分数
            else:
                feature_vector.append("unknown")
                feature_vector.append(0)
        
        elif dimension == "pacing":
            # 针对节奏偏好的特定特征
            top_paces = features.get("top_paces", [])
            if top_paces:
                # 添加最偏好的节奏类型
                feature_vector.append(top_paces[0][0])
                feature_vector.append(top_paces[0][1])  # 分数
            else:
                feature_vector.append("unknown")
                feature_vector.append(0)
        
        # 使用编码器处理特征
        if dimension in self.feature_encoders and hasattr(self.feature_encoders[dimension], 'transform'):
            try:
                # 尝试使用编码器转换特征
                encoded_features = self.feature_encoders[dimension].transform([feature_vector])
                return encoded_features[0]
            except:
                # 如果编码器未训练，则返回原始特征
                return np.array(feature_vector)
        
        return np.array(feature_vector)
    
    def _save_prediction_result(self, user_id: str, result: Dict[str, Any]) -> bool:
        """保存用户偏好预测结果
        
        Args:
            user_id: 用户ID
            result: 预测结果
            
        Returns:
            bool: 保存是否成功
        """
        try:
            self.storage.save_preference_prediction(user_id, result)
            predictor_logger.debug(f"成功保存用户 {user_id} 的偏好预测结果")
            return True
        except Exception as e:
            predictor_logger.error(f"保存用户 {user_id} 偏好预测结果失败: {str(e)}")
            return False
    
    def train(self, training_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """训练偏好预测模型
        
        Args:
            training_data: 训练数据列表
            
        Returns:
            Dict[str, Any]: 训练结果和评估指标
        """
        predictor_logger.info("开始训练偏好预测模型")
        
        if not training_data:
            predictor_logger.error("训练数据为空，无法训练模型")
            return {"status": "error", "message": "没有训练数据"}
        
        training_results = {}
        
        # 为每个维度训练模型
        for dimension in self.config["prediction_dimensions"]:
            try:
                dimension_results = self._train_dimension_model(dimension, training_data)
                training_results[dimension] = dimension_results
            except Exception as e:
                predictor_logger.error(f"训练 {dimension} 模型失败: {str(e)}")
                training_results[dimension] = {"status": "error", "message": str(e)}
        
        # 保存模型
        self._save_models()
        
        predictor_logger.info("偏好预测模型训练完成")
        return {
            "status": "success",
            "results": training_results,
            "trained_at": datetime.now().isoformat()
        }
    
    def _train_dimension_model(self, dimension: str, training_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """训练特定维度的预测模型
        
        Args:
            dimension: 预测维度名称
            training_data: 训练数据列表
            
        Returns:
            Dict[str, Any]: 训练结果和评估指标
        """
        predictor_logger.info(f"训练 {dimension} 预测模型")
        
        # 提取特征和标签
        features = []
        labels = []
        
        for item in training_data:
            # 用户特征
            user_features = item.get("features", {})
            
            # 标签 - 用户对该维度的实际偏好
            user_label = item.get("labels", {}).get(dimension)
            
            if not user_features or not user_label:
                continue
            
            # 处理特征
            processed_features = self._prepare_training_features(user_features, dimension)
            features.append(processed_features)
            labels.append(user_label)
        
        if not features or not labels:
            raise ValueError(f"没有有效的训练数据用于 {dimension} 模型")
        
        # 划分训练集和测试集
        X_train, X_test, y_train, y_test = train_test_split(
            features, labels, test_size=0.2, random_state=42
        )
        
        # 创建和训练模型
        model = self.models.get(dimension)
        if not model:
            self._create_model(dimension)
            model = self.models[dimension]
        
        # 训练特征编码器
        encoder = self.feature_encoders.get(dimension)
        if encoder and hasattr(encoder, 'fit'):
            encoder.fit(X_train)
            X_train_encoded = encoder.transform(X_train)
            X_test_encoded = encoder.transform(X_test)
        else:
            X_train_encoded = np.array(X_train)
            X_test_encoded = np.array(X_test)
        
        # 训练模型
        model.fit(X_train_encoded, y_train)
        
        # 评估模型
        y_pred = model.predict(X_test_encoded)
        
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, average='weighted')
        recall = recall_score(y_test, y_pred, average='weighted')
        f1 = f1_score(y_test, y_pred, average='weighted')
        
        # 特征重要性
        feature_importance = {}
        if hasattr(model, 'feature_importances_'):
            importances = model.feature_importances_
            for i, importance in enumerate(importances):
                if importance > self.config["feature_importance_threshold"]:
                    feature_importance[f"feature_{i}"] = float(importance)
        
        return {
            "status": "success",
            "metrics": {
                "accuracy": accuracy,
                "precision": precision,
                "recall": recall,
                "f1_score": f1
            },
            "feature_importance": feature_importance,
            "train_samples": len(X_train),
            "test_samples": len(X_test)
        }
    
    def _prepare_training_features(self, user_features: Dict[str, Any], dimension: str) -> List[Any]:
        """准备用于训练的特征向量
        
        Args:
            user_features: 用户特征字典
            dimension: 预测维度名称
            
        Returns:
            List[Any]: 处理后的特征向量
        """
        # 与预测时特征提取保持一致
        feature_vector = []
        
        # 1. 数值特征
        feature_vector.append(user_features.get("completion_rate", 0))
        feature_vector.append(user_features.get("emotion_intensity", 0.5))
        feature_vector.append(user_features.get("emotion_valence", 0))
        feature_vector.append(user_features.get("complexity_preference", 0.5))
        feature_vector.append(user_features.get("preferred_scene_duration", 8.0))
        
        # 2. 分类特征
        feature_vector.append(user_features.get("age_group", "unknown"))
        feature_vector.append(user_features.get("gender", "unknown"))
        feature_vector.append(user_features.get("engagement_level", "low"))
        
        # 维度特定特征
        if dimension == "complexity":
            # 针对剧情复杂度的特定特征
            top_structures = user_features.get("top_structures", [])
            if top_structures:
                feature_vector.append(top_structures[0][0])
                feature_vector.append(top_structures[0][1])
            else:
                feature_vector.append("unknown")
                feature_vector.append(0)
        
        elif dimension == "emotion_tone":
            # 针对情感基调的特定特征
            top_emotions = user_features.get("top_emotions", [])
            if top_emotions:
                feature_vector.append(top_emotions[0][0])
                feature_vector.append(top_emotions[0][1])
            else:
                feature_vector.append("unknown")
                feature_vector.append(0)
        
        elif dimension == "pacing":
            # 针对节奏偏好的特定特征
            top_paces = user_features.get("top_paces", [])
            if top_paces:
                feature_vector.append(top_paces[0][0])
                feature_vector.append(top_paces[0][1])
            else:
                feature_vector.append("unknown")
                feature_vector.append(0)
        
        return feature_vector
    
    def _save_models(self) -> bool:
        """保存训练好的模型
        
        Returns:
            bool: 保存是否成功
        """
        success = True
        
        for dimension in self.config["prediction_dimensions"]:
            model_path = os.path.join(self.config["model_dir"], f"{dimension}_model.pkl")
            encoder_path = os.path.join(self.config["model_dir"], f"{dimension}_encoder.pkl")
            
            try:
                # 保存模型
                if dimension in self.models:
                    with open(model_path, 'wb') as f:
                        pickle.dump(self.models[dimension], f)
                
                # 保存编码器
                if dimension in self.feature_encoders:
                    with open(encoder_path, 'wb') as f:
                        pickle.dump(self.feature_encoders[dimension], f)
                
                predictor_logger.info(f"成功保存 {dimension} 模型和编码器")
            except Exception as e:
                predictor_logger.error(f"保存 {dimension} 模型失败: {str(e)}")
                success = False
        
        return success
    
    def get_prediction_history(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """获取用户历史预测结果
        
        Args:
            user_id: 用户ID
            limit: 返回结果数量限制
            
        Returns:
            List[Dict[str, Any]]: 历史预测结果列表
        """
        try:
            history = self.storage.get_preference_predictions(user_id, limit=limit)
            return history if history else []
        except Exception as e:
            predictor_logger.error(f"获取用户 {user_id} 偏好预测历史失败: {str(e)}")
            return []
    
    def generate_training_data(self, feedback_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """从用户反馈数据生成训练数据
        
        Args:
            feedback_data: 用户反馈数据列表
            
        Returns:
            List[Dict[str, Any]]: 生成的训练数据
        """
        training_data = []
        
        for feedback in feedback_data:
            user_id = feedback.get("user_id")
            if not user_id:
                continue
            
            # 提取用户特征
            user_features = self._extract_user_features(user_id)
            if not user_features:
                continue
            
            # 从反馈中提取标签
            labels = {}
            for dimension in self.config["prediction_dimensions"]:
                label = feedback.get("preferences", {}).get(dimension)
                if label:
                    labels[dimension] = label
            
            if not labels:
                continue
            
            # 添加到训练数据
            training_data.append({
                "user_id": user_id,
                "features": user_features,
                "labels": labels,
                "timestamp": feedback.get("timestamp", datetime.now().isoformat())
            })
        
        return training_data


# 模块级函数

_preference_predictor_instance = None

def get_preference_predictor() -> PreferencePredictor:
    """获取偏好预测模型单例实例
    
    Returns:
        PreferencePredictor: 偏好预测模型实例
    """
    global _preference_predictor_instance
    if _preference_predictor_instance is None:
        _preference_predictor_instance = PreferencePredictor()
    return _preference_predictor_instance

def predict_user_preferences(user_id: str) -> Dict[str, Any]:
    """预测用户偏好
    
    Args:
        user_id: 用户ID
        
    Returns:
        Dict[str, Any]: 预测结果
    """
    predictor = get_preference_predictor()
    return predictor.predict(user_id)

def train_preference_models(training_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """训练偏好预测模型
    
    Args:
        training_data: 训练数据
        
    Returns:
        Dict[str, Any]: 训练结果
    """
    predictor = get_preference_predictor()
    return predictor.train(training_data)

def get_user_prediction_history(user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    """获取用户历史预测结果
    
    Args:
        user_id: 用户ID
        limit: 返回结果数量限制
        
    Returns:
        List[Dict[str, Any]]: 历史预测结果列表
    """
    predictor = get_preference_predictor()
    return predictor.get_prediction_history(user_id, limit) 