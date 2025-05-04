#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
行为解码器测试

测试行为解码器模块的功能，验证行为解析和偏好信号提取的准确性。
"""

import os
import sys
import json
from datetime import datetime, timedelta
import unittest
from unittest.mock import MagicMock, patch

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.audience.behavior_decoder import (
    BehaviorDecoder, get_behavior_decoder, 
    decode_user_behavior, decode_realtime_behavior, get_user_preferences
)
from src.audience.mock_data_generator import generate_mock_behavior_data

class TestBehaviorDecoder(unittest.TestCase):
    """行为解码器测试类"""
    
    def setUp(self):
        """测试准备工作"""
        # 创建测试用户ID
        self.test_user_id = "test_user_123"
        
        # 模拟存储管理器
        self.mock_storage = MagicMock()
        
        # 模拟行为跟踪器
        self.mock_tracker = MagicMock()
        
        # 模拟用户画像引擎
        self.mock_profile_engine = MagicMock()
        
        # 测试用行为数据
        self.test_behavior_data = generate_mock_behavior_data(self.test_user_id)
        
        # 配置行为跟踪器返回测试数据
        self.mock_tracker.get_user_behavior_summary.return_value = self.test_behavior_data
        
        # 创建解码器实例并注入mock对象
        self.decoder = BehaviorDecoder()
        self.decoder.storage = self.mock_storage
        self.decoder.behavior_tracker = self.mock_tracker
        self.decoder.profile_engine = self.mock_profile_engine
    
    def test_decode_user_behavior(self):
        """测试用户行为解码"""
        # 执行解码
        result = self.decoder.decode_user_behavior(self.test_user_id)
        
        # 验证结果
        self.assertEqual(result["user_id"], self.test_user_id)
        self.assertEqual(result["status"], "success")
        
        # 验证各个偏好维度存在
        self.assertIn("content_preferences", result)
        self.assertIn("emotion_preferences", result)
        self.assertIn("narrative_preferences", result)
        self.assertIn("pacing_preferences", result)
        self.assertIn("editing_preferences", result)
        self.assertIn("device_preferences", result)
        
        # 验证解码后数据被保存
        self.mock_storage.save_user_preferences.assert_called_once()
    
    def test_decode_realtime_behavior(self):
        """测试实时行为解码"""
        # 创建测试行为事件
        test_event = {
            "event_type": "view_complete",
            "content_id": "content_456",
            "completion_rate": 0.85,
            "duration": 180,
            "timestamp": datetime.now().isoformat(),
            "metadata": {
                "genre": "comedy",
                "theme": "friendship",
                "character_type": "ensemble",
                "narrative_style": "linear",
                "pacing": "fast"
            }
        }
        
        # 执行实时解码
        result = self.decoder.decode_realtime_behavior(self.test_user_id, test_event)
        
        # 验证结果
        self.assertEqual(result["user_id"], self.test_user_id)
        self.assertEqual(result["event_type"], "view_complete")
        self.assertEqual(result["content_id"], "content_456")
        
        # 验证偏好信号存在
        self.assertIn("preference_signals", result)
        self.assertGreater(len(result["preference_signals"]), 0)
        
        # 验证置信度存在且合理
        self.assertIn("confidence", result)
        self.assertGreaterEqual(result["confidence"], 0.0)
        self.assertLessEqual(result["confidence"], 1.0)
        
        # 验证偏好信号被保存
        self.mock_storage.save_preference_signal.assert_called_once()
    
    def test_content_preference_score_calculation(self):
        """测试内容偏好分数计算"""
        # 测试高完成率和正面交互
        score1 = self.decoder._calculate_content_preference_score(0.95, {
            "like": True,
            "share": True,
            "replay_count": 2
        })
        
        # 测试中等完成率和部分交互
        score2 = self.decoder._calculate_content_preference_score(0.7, {
            "like": True,
            "share": False
        })
        
        # 测试低完成率和无交互
        score3 = self.decoder._calculate_content_preference_score(0.2, {})
        
        # 验证分数排序正确
        self.assertGreater(score1, score2)
        self.assertGreater(score2, score3)
        
        # 验证分数范围正确
        self.assertGreaterEqual(score1, -1.0)
        self.assertLessEqual(score1, 1.0)
    
    def test_interest_point_identification(self):
        """测试兴趣点识别"""
        # 执行兴趣点识别
        interest_points = self.decoder._identify_interest_points(self.test_behavior_data)
        
        # 验证结果列表存在
        self.assertIsInstance(interest_points, list)
        
        # 如果有兴趣点，验证其格式
        if interest_points:
            point = interest_points[0]
            self.assertIn("content_id", point)
            self.assertIn("timestamp", point)
            self.assertIn("reason", point)
    
    def test_preference_strength_assignment(self):
        """测试偏好强度分配"""
        # 测试分数
        test_scores = {
            "item1": 0.9,
            "item2": 0.6,
            "item3": 0.1,
            "item4": -0.3,
            "item5": -0.8
        }
        
        # 执行强度分配
        result = self.decoder._assign_preference_strength(test_scores)
        
        # 验证结果
        self.assertEqual(result["item1"]["strength"], "strong_like")
        self.assertEqual(result["item2"]["strength"], "like")
        self.assertEqual(result["item3"]["strength"], "neutral")
        self.assertEqual(result["item4"]["strength"], "dislike")
        self.assertEqual(result["item5"]["strength"], "strong_dislike")


if __name__ == "__main__":
    unittest.main() 