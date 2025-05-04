#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
A/B测试路由器测试模块

测试A/B测试路由器的核心功能，包括变体路由、测试创建和结果分析。
"""

import unittest
from unittest.mock import MagicMock, patch
import json
import numpy as np
from datetime import datetime, timedelta

# 修改Python路径以导入项目模块
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.audience.ab_router import (
    ABRouter, get_ab_router, route_variant, 
    create_ab_test, record_ab_event, analyze_ab_results
)

class TestABRouter(unittest.TestCase):
    """A/B测试路由器测试类"""
    
    def setUp(self):
        """测试准备工作"""
        # 模拟存储管理器
        self.mock_storage = MagicMock()
        
        # 模拟用户画像引擎
        self.mock_profile_engine = MagicMock()
        
        # 创建被测对象
        with patch('src.audience.ab_router.get_storage_manager', return_value=self.mock_storage), \
             patch('src.audience.ab_router.get_profile_engine', return_value=self.mock_profile_engine):
            self.ab_router = ABRouter()
        
        # 测试用户ID
        self.test_user_id = "test_user_456"
        
        # 测试变体列表
        self.test_variants = [
            {
                "id": "variant_1",
                "name": "原始版本",
                "description": "当前使用的混剪版本",
                "feature_vector": [0.8, 0.2, 0.4, 0.6, 0.1]
            },
            {
                "id": "variant_2",
                "name": "情感强化版",
                "description": "增强情感变化的混剪版本",
                "feature_vector": [0.3, 0.9, 0.5, 0.2, 0.7]
            },
            {
                "id": "variant_3",
                "name": "节奏优化版",
                "description": "优化节奏变化的混剪版本",
                "feature_vector": [0.5, 0.4, 0.9, 0.3, 0.6]
            }
        ]
        
        # 测试用户画像
        self.test_profile = {
            "content_preferences": {
                "comedy": {"score": 0.8},
                "action": {"score": 0.3},
                "drama": {"score": 0.5}
            },
            "emotion_response": {
                "joy": {"score": 0.7},
                "surprise": {"score": 0.6},
                "curiosity": {"score": 0.4}
            },
            "editing_preferences": {
                "fast_cuts": {"score": 0.9},
                "transitions": {"score": 0.5},
                "effects": {"score": 0.2}
            },
            "narrative_preferences": {
                "non_linear": {"score": 0.8},
                "character_focus": {"score": 0.4},
                "plot_twists": {"score": 0.6}
            },
            "pacing_preferences": {
                "dynamic": {"score": 0.7},
                "build_up": {"score": 0.5},
                "consistent": {"score": 0.3}
            }
        }
    
    def test_router_initialization(self):
        """测试路由器初始化"""
        self.assertIsNotNone(self.ab_router)
        self.assertEqual(self.ab_router.default_assignment_strategy, "random")
        self.assertEqual(len(self.ab_router.metrics), 6)  # 应该有6个默认指标
    
    def test_route_version_empty_variants(self):
        """测试空变体列表的路由"""
        result = self.ab_router.route_version(self.test_user_id, [])
        self.assertEqual(result, {})
    
    def test_encode_user_with_profile(self):
        """测试用户编码（有画像）"""
        # 设置模拟返回值
        self.mock_profile_engine.get_profile.return_value = self.test_profile
        
        # 调用被测方法
        user_vector = self.ab_router._encode_user(self.test_user_id)
        
        # 验证向量非空
        self.assertIsNotNone(user_vector)
        self.assertGreater(len(user_vector), 0)
        
        # 验证调用
        self.mock_profile_engine.get_profile.assert_called_once_with(self.test_user_id)
    
    def test_encode_user_without_profile(self):
        """测试用户编码（无画像）"""
        # 设置模拟返回值
        self.mock_profile_engine.get_profile.return_value = None
        
        # 调用被测方法
        user_vector = self.ab_router._encode_user(self.test_user_id)
        
        # 验证结果为默认向量
        self.assertEqual(len(user_vector), 64)  # 默认向量长度
        self.assertTrue(np.all(user_vector == 0))  # 所有元素应为0
        
        # 验证调用
        self.mock_profile_engine.get_profile.assert_called_once_with(self.test_user_id)
    
    def test_normalize_preferences(self):
        """测试偏好规范化"""
        # 准备测试数据
        test_prefs = {
            "feature1": {"score": 2.0},
            "feature2": {"score": 3.0},
            "feature3": {"score": 5.0}
        }
        
        # 调用被测方法
        normalized = self.ab_router._normalize_preferences(test_prefs)
        
        # 验证结果
        self.assertEqual(sum(normalized.values()), 1.0)  # 总和应为1
        self.assertEqual(normalized["feature1"], 0.2)  # 2.0 / 10.0
        self.assertEqual(normalized["feature2"], 0.3)  # 3.0 / 10.0
        self.assertEqual(normalized["feature3"], 0.5)  # 5.0 / 10.0
    
    def test_calculate_similarity(self):
        """测试相似度计算"""
        # 准备测试数据
        user_vector = np.array([0.5, 0.3, 0.9, 0.1])
        variant_vector = [0.6, 0.2, 0.8, 0.2]
        
        # 调用被测方法
        similarity = self.ab_router._calculate_similarity(user_vector, variant_vector)
        
        # 验证结果
        self.assertGreaterEqual(similarity, 0.0)
        self.assertLessEqual(similarity, 1.0)
    
    def test_route_version(self):
        """测试版本路由功能"""
        # 设置模拟返回值
        user_vector = np.array([0.3, 0.9, 0.5, 0.2, 0.7])  # 与variant_2最相似
        self.ab_router._encode_user = MagicMock(return_value=user_vector)
        
        # 调用被测方法
        result = self.ab_router.route_version(self.test_user_id, self.test_variants)
        
        # 验证结果
        self.assertEqual(result["id"], "variant_2")
        
        # 验证记录分配结果被调用
        self.mock_storage.save_ab_assignment.assert_called_once()
    
    def test_create_test(self):
        """测试创建A/B测试"""
        # 准备测试数据
        test_id = "test_123"
        config = {"assignment_strategy": "weighted"}
        
        # 调用被测方法
        result = self.ab_router.create_test(test_id, self.test_variants, config)
        
        # 验证结果
        self.assertEqual(result["id"], test_id)
        self.assertEqual(result["variants"], self.test_variants)
        self.assertEqual(result["assignment_strategy"], "weighted")
        self.assertEqual(result["status"], "active")
        
        # 验证存储被调用
        self.mock_storage.save_ab_test.assert_called_once_with(test_id, result)
    
    def test_get_test(self):
        """测试获取A/B测试配置"""
        # 准备测试数据
        test_id = "test_123"
        test_config = {"id": test_id, "status": "active"}
        
        # 设置模拟返回值
        self.mock_storage.get_ab_test.return_value = test_config
        
        # 调用被测方法
        result = self.ab_router.get_test(test_id)
        
        # 验证结果
        self.assertEqual(result["id"], test_id)
        self.assertEqual(result["status"], "active")
        
        # 验证调用
        self.mock_storage.get_ab_test.assert_called_once_with(test_id)
    
    def test_record_event(self):
        """测试记录事件"""
        # 准备测试数据
        variant_id = "variant_1"
        event_type = "view"
        event_data = {"duration": 30}
        
        # 调用被测方法
        self.ab_router.record_event(self.test_user_id, variant_id, event_type, event_data)
        
        # 验证存储被调用
        self.mock_storage.save_ab_event.assert_called_once()
        
        # 获取调用参数
        args = self.mock_storage.save_ab_event.call_args[0]
        
        # 验证参数
        self.assertEqual(args[0], self.test_user_id)
        event_record = args[1]
        self.assertEqual(event_record["user_id"], self.test_user_id)
        self.assertEqual(event_record["variant_id"], variant_id)
        self.assertEqual(event_record["event_type"], event_type)
        self.assertEqual(event_record["data"], event_data)
    
    def test_analyze_test_results(self):
        """测试分析测试结果"""
        # 准备测试数据
        test_id = "test_123"
        test_config = {
            "id": test_id,
            "variants": self.test_variants,
            "metrics": ["completion_rate", "engagement_time"]
        }
        
        events = [
            {"variant_id": "variant_1", "event_type": "start", "user_id": "user1"},
            {"variant_id": "variant_1", "event_type": "completion", "user_id": "user1"},
            {"variant_id": "variant_2", "event_type": "start", "user_id": "user2"},
            {"variant_id": "variant_2", "event_type": "start", "user_id": "user3"},
            {"variant_id": "variant_2", "event_type": "completion", "user_id": "user2"}
        ]
        
        # 设置模拟返回值
        self.ab_router.get_test = MagicMock(return_value=test_config)
        self.mock_storage.get_ab_events.return_value = events
        
        # 调用被测方法
        results = self.ab_router.analyze_test_results(test_id)
        
        # 验证结果
        self.assertEqual(results["test_id"], test_id)
        self.assertIn("metrics", results)
        self.assertIn("recommendations", results)
        self.assertIn("sample_sizes", results)
        
        # 验证样本大小
        self.assertEqual(results["sample_sizes"]["variant_1"], 2)
        self.assertEqual(results["sample_sizes"]["variant_2"], 3)
    
    def test_convenience_functions(self):
        """测试便捷函数"""
        # 全局单例重置
        with patch('src.audience.ab_router._ab_router', self.ab_router):
            # 测试route_variant
            self.ab_router.route_version = MagicMock(return_value={"id": "variant_1"})
            result = route_variant(self.test_user_id, self.test_variants)
            self.assertEqual(result["id"], "variant_1")
            self.ab_router.route_version.assert_called_once_with(self.test_user_id, self.test_variants)
            
            # 测试create_ab_test
            self.ab_router.create_test = MagicMock(return_value={"id": "test_123"})
            result = create_ab_test("test_123", self.test_variants)
            self.assertEqual(result["id"], "test_123")
            self.ab_router.create_test.assert_called_once()
            
            # 测试record_ab_event
            self.ab_router.record_event = MagicMock()
            record_ab_event(self.test_user_id, "variant_1", "view")
            self.ab_router.record_event.assert_called_once()
            
            # 测试analyze_ab_results
            self.ab_router.analyze_test_results = MagicMock(return_value={"test_id": "test_123"})
            result = analyze_ab_results("test_123")
            self.assertEqual(result["test_id"], "test_123")
            self.ab_router.analyze_test_results.assert_called_once_with("test_123")

if __name__ == "__main__":
    unittest.main() 