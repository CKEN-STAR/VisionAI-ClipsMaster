#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
跨平台习惯融合模块测试

测试跨平台习惯融合模块的功能，验证多平台数据整合的正确性。
"""

import os
import sys
import json
import unittest
from unittest.mock import MagicMock, patch

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.audience.cross_platform import (
    CrossPlatformIntegrator, get_platform_integrator,
    integrate_user_habits, get_unified_preference, get_platform_habit
)

class TestCrossPlatformIntegrator(unittest.TestCase):
    """跨平台习惯融合器测试类"""
    
    def setUp(self):
        """测试准备工作"""
        # 创建测试用用户ID
        self.test_user_id = "test_user_789"
        
        # 模拟存储管理器
        self.mock_storage = MagicMock()
        
        # 模拟平台数据
        self.mock_douyin_data = {
            "favorite_categories": ["搞笑", "生活", "美食"],
            "content_format_preference": {
                "短视频": 0.8,
                "直播": 0.2
            },
            "watch_duration": {
                "average": 35.6,
                "unit": "seconds"
            },
            "active_time_slots": ["18:00-22:00", "12:00-13:00"],
            "category_preferences": {
                "搞笑": {"score": 0.8, "strength": "strong_like"},
                "生活": {"score": 0.7, "strength": "like"},
                "美食": {"score": 0.9, "strength": "strong_like"}
            }
        }
        
        self.mock_bilibili_data = {
            "favorite_partitions": ["动画", "游戏", "科技"],
            "content_format_preference": {
                "视频": 0.6,
                "直播": 0.3,
                "番剧": 0.1
            },
            "watch_duration": {
                "average": 420.5,
                "unit": "seconds"
            },
            "active_time_slots": ["19:00-23:00", "13:00-15:00"],
            "category_preferences": {
                "动画": {"score": 0.8, "strength": "strong_like"},
                "游戏": {"score": 0.9, "strength": "strong_like"},
                "科技": {"score": 0.7, "strength": "like"}
            }
        }
        
        self.mock_youtube_data = {
            "subscribed_categories": ["Entertainment", "Technology", "Music"],
            "content_format_preference": {
                "视频": 0.7,
                "短视频": 0.2,
                "直播": 0.1
            },
            "watch_duration": {
                "average": 540.2,
                "unit": "seconds"
            },
            "active_time_slots": ["20:00-24:00", "7:00-9:00"],
            "category_preferences": {
                "Entertainment": {"score": 0.7, "strength": "like"},
                "Technology": {"score": 0.8, "strength": "strong_like"},
                "Music": {"score": 0.6, "strength": "like"}
            }
        }
        
        # 创建并配置测试对象
        with patch('src.audience.cross_platform.get_storage_manager', return_value=self.mock_storage), \
             patch('src.audience.cross_platform.get_profile_engine'), \
             patch('src.audience.cross_platform.get_behavior_decoder'), \
             patch('src.audience.cross_platform.get_config', return_value={"cross_platform": {}}):
            self.integrator = CrossPlatformIntegrator()
        
        # 配置模拟返回值
        self.integrator._get_douyin_habits = MagicMock(return_value=self.mock_douyin_data)
        self.integrator._get_bilibili_habits = MagicMock(return_value=self.mock_bilibili_data)
        self.integrator._get_youtube_habits = MagicMock(return_value=self.mock_youtube_data)
    
    def test_integrate_habits(self):
        """测试跨平台习惯整合"""
        # 调用被测方法
        result = self.integrator.integrate_habits(self.test_user_id)
        
        # 验证结果包含所有平台数据
        self.assertIn("抖音", result)
        self.assertIn("B站", result)
        self.assertIn("油管", result)
        self.assertIn("融合策略", result)
        
        # 验证平台数据获取方法被调用
        self.integrator._get_douyin_habits.assert_called_once_with(self.test_user_id)
        self.integrator._get_bilibili_habits.assert_called_once_with(self.test_user_id)
        self.integrator._get_youtube_habits.assert_called_once_with(self.test_user_id)
    
    def test_calculate_unified_preference(self):
        """测试统一偏好计算"""
        # 准备输入数据
        platform_data = {
            "douyin": self.mock_douyin_data,
            "bilibili": self.mock_bilibili_data,
            "youtube": self.mock_youtube_data
        }
        
        # 调用被测方法
        result = self.integrator._calculate_unified_preference(platform_data)
        
        # 验证结果结构
        self.assertIn("category_preferences", result)
        self.assertIn("format_preferences", result)
        self.assertIn("active_time_slots", result)
        self.assertIn("watch_duration", result)
        
        # 验证内容类型偏好融合
        category_prefs = result["category_preferences"]
        self.assertIn("搞笑", category_prefs)
        self.assertIn("动画", category_prefs)
        self.assertIn("Technology", category_prefs)
        
        # 验证内容格式偏好融合
        format_prefs = result["format_preferences"]
        self.assertIn("短视频", format_prefs)
        self.assertIn("直播", format_prefs)
        self.assertIn("视频", format_prefs)
        
        # 验证观看时长计算
        self.assertGreater(result["watch_duration"]["average"], 0)
        
        # 验证平台覆盖信息
        self.assertTrue(result["platform_coverage"]["douyin"])
        self.assertTrue(result["platform_coverage"]["bilibili"])
        self.assertTrue(result["platform_coverage"]["youtube"])
    
    def test_get_unified_preference(self):
        """测试获取统一偏好表达"""
        # 模拟存储管理器方法
        self.mock_storage.get_cross_platform_data = MagicMock(return_value=None)
        self.mock_storage.save_cross_platform_data = MagicMock()
        
        # 调用被测方法
        result = self.integrator.get_unified_preference(self.test_user_id)
        
        # 验证结果
        self.assertIsInstance(result, dict)
        self.assertIn("category_preferences", result)
        self.assertIn("format_preferences", result)
        
        # 验证存储管理器方法被调用
        self.mock_storage.get_cross_platform_data.assert_called_once_with(self.test_user_id)
    
    def test_get_platform_habit(self):
        """测试获取特定平台习惯数据"""
        # 调用被测方法获取抖音习惯
        douyin_result = self.integrator.get_platform_habit(self.test_user_id, "douyin")
        
        # 验证结果
        self.assertEqual(douyin_result, self.mock_douyin_data)
        self.integrator._get_douyin_habits.assert_called_with(self.test_user_id)
        
        # 调用被测方法获取B站习惯
        bilibili_result = self.integrator.get_platform_habit(self.test_user_id, "bilibili")
        
        # 验证结果
        self.assertEqual(bilibili_result, self.mock_bilibili_data)
        self.integrator._get_bilibili_habits.assert_called_with(self.test_user_id)
        
        # 调用被测方法获取不支持的平台习惯
        unknown_result = self.integrator.get_platform_habit(self.test_user_id, "unknown")
        
        # 验证结果
        self.assertEqual(unknown_result, {})
    
    def test_module_level_functions(self):
        """测试模块级函数"""
        with patch('src.audience.cross_platform._platform_integrator', self.integrator):
            # 测试获取整合器实例
            integrator = get_platform_integrator()
            self.assertEqual(integrator, self.integrator)
            
            # 测试整合用户习惯
            result = integrate_user_habits(self.test_user_id)
            self.integrator.integrate_habits.assert_called_once_with(self.test_user_id)
            
            # 测试获取统一偏好
            result = get_unified_preference(self.test_user_id)
            self.integrator.get_unified_preference.assert_called_once_with(self.test_user_id)
            
            # 测试获取平台习惯
            result = get_platform_habit(self.test_user_id, "douyin")
            self.integrator.get_platform_habit.assert_called_once_with(self.test_user_id, "douyin")


if __name__ == "__main__":
    unittest.main() 