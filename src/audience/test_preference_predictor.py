#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
偏好预测模型测试

测试偏好预测模型的功能，验证用户偏好预测的准确性和模型训练过程。
"""

import os
import sys
import json
from datetime import datetime, timedelta
import unittest
from unittest.mock import MagicMock, patch

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.audience.preference_predictor import (
    PreferencePredictor, get_preference_predictor, 
    predict_user_preferences, train_preference_models
)
from src.audience.mock_data_generator import generate_mock_behavior_data

class TestPreferencePredictor(unittest.TestCase):
    """偏好预测模型测试类"""
    
    def setUp(self):
        """测试准备工作"""
        # 创建测试用户ID
        self.test_user_id = "test_user_123"
        
        # 模拟存储管理器
        self.mock_storage = MagicMock()
        
        # 模拟用户画像引擎
        self.mock_profile_engine = MagicMock()
        
        # 模拟行为解码器
        self.mock_decoder = MagicMock()
        
        # 测试用用户画像数据
        self.test_profile = {
            "user_id": self.test_user_id,
            "basic_info": {
                "age_group": "18-24",
                "gender": "female",
                "region": "east"
            },
            "behavior_patterns": {
                "completion_rate": 0.85,
                "engagement_level": "high",
                "genre_preferences": {
                    "comedy": 10,
                    "romance": 8,
                    "action": 3
                }
            }
        }
        
        # 测试用用户偏好数据
        self.test_preferences = {
            "user_id": self.test_user_id,
            "status": "success",
            "content_preferences": {
                "genres": {
                    "comedy": {"score": 0.85, "strength": "strong_like"},
                    "romance": {"score": 0.7, "strength": "like"},
                    "action": {"score": 0.3, "strength": "neutral"}
                }
            },
            "emotion_preferences": {
                "primary_emotions": {
                    "joy": {"score": 0.8, "strength": "strong_like"},
                    "surprise": {"score": 0.6, "strength": "like"}
                },
                "intensity": 0.7,
                "valence": 0.6
            },
            "narrative_preferences": {
                "structures": {
                    "linear": {"score": 0.75, "strength": "strong_like"},
                    "nonlinear": {"score": 0.4, "strength": "neutral"}
                },
                "complexity": 0.4
            },
            "pacing_preferences": {
                "overall_pace": {
                    "fast": {"score": 0.8, "strength": "strong_like"},
                    "medium": {"score": 0.5, "strength": "like"},
                    "slow": {"score": 0.2, "strength": "neutral"}
                },
                "scene_duration": {
                    "preferred": 5.0
                }
            }
        }
        
        # 配置模拟返回数据
        self.mock_profile_engine.get_user_profile.return_value = self.test_profile
        self.mock_decoder.get_user_preferences.return_value = self.test_preferences
        
        # 创建预测器实例并注入mock对象
        self.predictor = PreferencePredictor()
        self.predictor.storage = self.mock_storage
        self.predictor.profile_engine = self.mock_profile_engine
        self.predictor.behavior_decoder = self.mock_decoder
    
    def test_feature_extraction(self):
        """测试用户特征提取"""
        features = self.predictor._extract_user_features(self.test_user_id)
        
        # 验证基本特征存在
        self.assertIsNotNone(features)
        self.assertEqual(features["age_group"], "18-24")
        self.assertEqual(features["gender"], "female")
        
        # 验证内容偏好特征
        self.assertIn("top_genres", features)
        self.assertTrue(isinstance(features["top_genres"], list))
        
        # 验证情感偏好特征
        self.assertIn("emotion_intensity", features)
        self.assertIn("emotion_valence", features)
        
        # 验证叙事偏好特征
        self.assertIn("complexity_preference", features)
    
    def test_user_preference_prediction(self):
        """测试用户偏好预测"""
        # 模拟预测
        result = self.predictor.predict(self.test_user_id)
        
        # 验证结果
        self.assertEqual(result["user_id"], self.test_user_id)
        self.assertEqual(result["status"], "success")
        
        # 验证预测维度
        self.assertIn("predictions", result)
        predictions = result["predictions"]
        
        # 验证预测维度
        for dimension in self.predictor.config["prediction_dimensions"]:
            if dimension in predictions:
                prediction = predictions[dimension]
                # 验证预测结果包含预测值和概率
                self.assertIn("prediction", prediction)
                self.assertIn("probabilities", prediction)
                self.assertIn("confidence", prediction)
    
    def test_model_training(self):
        """测试模型训练"""
        # 创建模拟训练数据
        training_data = [
            {
                "user_id": "user1",
                "features": {
                    "age_group": "18-24",
                    "gender": "female",
                    "completion_rate": 0.85,
                    "emotion_intensity": 0.7,
                    "emotion_valence": 0.6,
                    "complexity_preference": 0.4,
                    "preferred_scene_duration": 5.0,
                    "engagement_level": "high",
                    "top_genres": [("comedy", 0.85), ("romance", 0.7)],
                    "top_emotions": [("joy", 0.8), ("surprise", 0.6)],
                    "top_structures": [("linear", 0.75), ("nonlinear", 0.4)],
                    "top_paces": [("fast", 0.8), ("medium", 0.5)]
                },
                "labels": {
                    "complexity": "medium",
                    "emotion_tone": "light",
                    "pacing": "fast"
                }
            },
            {
                "user_id": "user2",
                "features": {
                    "age_group": "25-34",
                    "gender": "male",
                    "completion_rate": 0.6,
                    "emotion_intensity": 0.5,
                    "emotion_valence": 0.1,
                    "complexity_preference": 0.8,
                    "preferred_scene_duration": 10.0,
                    "engagement_level": "medium",
                    "top_genres": [("drama", 0.9), ("thriller", 0.8)],
                    "top_emotions": [("tension", 0.9), ("fear", 0.7)],
                    "top_structures": [("nonlinear", 0.8), ("complex", 0.7)],
                    "top_paces": [("medium", 0.7), ("slow", 0.6)]
                },
                "labels": {
                    "complexity": "complex",
                    "emotion_tone": "dark",
                    "pacing": "medium"
                }
            }
        ]
        
        # 训练模型
        result = self.predictor.train(training_data)
        
        # 验证训练结果
        self.assertEqual(result["status"], "success")
        self.assertIn("results", result)
        
        # 验证各维度训练结果
        for dimension in self.predictor.config["prediction_dimensions"]:
            if dimension in result["results"]:
                dim_result = result["results"][dimension]
                self.assertIn("status", dim_result)
                if dim_result["status"] == "success":
                    self.assertIn("metrics", dim_result)
    
    def test_empty_training_data(self):
        """测试空训练数据"""
        result = self.predictor.train([])
        self.assertEqual(result["status"], "error")
    
    def test_prediction_history(self):
        """测试历史预测结果获取"""
        # 模拟历史预测数据
        mock_history = [
            {
                "user_id": self.test_user_id,
                "predictions": {
                    "complexity": {"prediction": "medium", "confidence": 0.8},
                    "emotion_tone": {"prediction": "light", "confidence": 0.7},
                    "pacing": {"prediction": "fast", "confidence": 0.9}
                },
                "predicted_at": (datetime.now() - timedelta(days=1)).isoformat()
            },
            {
                "user_id": self.test_user_id,
                "predictions": {
                    "complexity": {"prediction": "medium", "confidence": 0.75},
                    "emotion_tone": {"prediction": "light", "confidence": 0.8},
                    "pacing": {"prediction": "fast", "confidence": 0.85}
                },
                "predicted_at": datetime.now().isoformat()
            }
        ]
        
        # 配置模拟返回数据
        self.mock_storage.get_preference_predictions.return_value = mock_history
        
        # 获取历史预测
        history = self.predictor.get_prediction_history(self.test_user_id)
        
        # 验证历史数据
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["user_id"], self.test_user_id)
        self.assertIn("predictions", history[0])


if __name__ == "__main__":
    unittest.main() 