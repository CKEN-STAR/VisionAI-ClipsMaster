#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
跨平台习惯融合模块简化测试

这是一个独立的测试脚本，验证跨平台习惯融合模块的核心功能，
不依赖于其他模块，方便快速测试。
"""

import unittest
from datetime import datetime
from standalone_cross_platform_demo import SimpleCrossPlatformIntegrator

class TestSimpleCrossPlatformIntegrator(unittest.TestCase):
    """简化版跨平台习惯融合器测试类"""
    
    def setUp(self):
        """测试准备工作"""
        # 创建测试用用户ID
        self.test_user_id = "test_user_789"
        
        # 创建测试对象
        self.integrator = SimpleCrossPlatformIntegrator()
    
    def test_get_platform_habit(self):
        """测试获取平台习惯数据"""
        # 获取抖音习惯数据
        douyin_data = self.integrator.get_platform_habit(self.test_user_id, "douyin")
        
        # 验证数据结构
        self.assertIn("favorite_categories", douyin_data)
        self.assertIn("content_format_preference", douyin_data)
        self.assertIn("watch_duration", douyin_data)
        self.assertIn("active_time_slots", douyin_data)
        
        # 验证内容格式偏好
        self.assertIn("短视频", douyin_data["content_format_preference"])
        self.assertIn("直播", douyin_data["content_format_preference"])
        
        # 验证观看时长
        self.assertIn("average", douyin_data["watch_duration"])
        self.assertIn("unit", douyin_data["watch_duration"])
        
        # 获取B站习惯数据
        bilibili_data = self.integrator.get_platform_habit(self.test_user_id, "bilibili")
        
        # 验证数据结构
        self.assertIn("favorite_partitions", bilibili_data)
        self.assertIn("content_format_preference", bilibili_data)
        self.assertIn("番剧", bilibili_data["content_format_preference"])
        
        # 获取YouTube习惯数据
        youtube_data = self.integrator.get_platform_habit(self.test_user_id, "youtube")
        
        # 验证数据结构
        self.assertIn("subscribed_categories", youtube_data)
        self.assertIn("Technology", youtube_data["category_preferences"])
    
    def test_integrate_habits(self):
        """测试跨平台习惯整合"""
        # 调用整合方法
        result = self.integrator.integrate_habits(self.test_user_id)
        
        # 验证结果结构
        self.assertIn("抖音", result)
        self.assertIn("B站", result)
        self.assertIn("油管", result)
        self.assertIn("融合策略", result)
        
        # 验证平台数据
        self.assertEqual(result["抖音"], self.integrator.get_douyin_habits(self.test_user_id))
        self.assertEqual(result["B站"], self.integrator.get_bilibili_habits(self.test_user_id))
        self.assertEqual(result["油管"], self.integrator.get_youtube_habits(self.test_user_id))
    
    def test_calculate_unified_preference(self):
        """测试统一偏好计算"""
        # 准备测试数据
        platform_data = {
            "douyin": self.integrator.get_douyin_habits(self.test_user_id),
            "bilibili": self.integrator.get_bilibili_habits(self.test_user_id),
            "youtube": self.integrator.get_youtube_habits(self.test_user_id)
        }
        
        # 调用被测方法
        result = self.integrator.calculate_unified_preference(platform_data)
        
        # 验证结果结构
        self.assertIn("category_preferences", result)
        self.assertIn("format_preferences", result)
        self.assertIn("active_time_slots", result)
        self.assertIn("watch_duration", result)
        self.assertIn("platform_coverage", result)
        
        # 验证分类偏好
        category_prefs = result["category_preferences"]
        self.assertIn("搞笑", category_prefs)
        self.assertIn("动画", category_prefs)
        self.assertIn("Technology", category_prefs)
        
        # 验证格式偏好
        format_prefs = result["format_preferences"]
        self.assertIn("短视频", format_prefs)
        self.assertIn("直播", format_prefs)
        self.assertIn("视频", format_prefs)
        
        # 验证平台来源
        self.assertEqual(category_prefs["搞笑"]["platforms"], ["douyin"])
        self.assertEqual(category_prefs["游戏"]["platforms"], ["bilibili"])
        self.assertEqual(category_prefs["Technology"]["platforms"], ["youtube"])
        
        # 验证跨平台格式
        self.assertIn("douyin", format_prefs["直播"]["platforms"])
        self.assertIn("bilibili", format_prefs["直播"]["platforms"])
        self.assertIn("youtube", format_prefs["直播"]["platforms"])
        
        # 验证观看时长计算
        avg_duration = (35.6 + 420.5 + 540.2) / 3
        self.assertAlmostEqual(result["watch_duration"]["average"], avg_duration, places=1)
        
        # 验证活跃时段
        time_slots = set(platform_data["douyin"]["active_time_slots"] + 
                         platform_data["bilibili"]["active_time_slots"] + 
                         platform_data["youtube"]["active_time_slots"])
        self.assertEqual(set(result["active_time_slots"]), time_slots)
    
    def test_get_unified_preference(self):
        """测试获取统一偏好表达"""
        # 调用被测方法
        result = self.integrator.get_unified_preference(self.test_user_id)
        
        # 验证结果结构
        self.assertIn("category_preferences", result)
        self.assertIn("format_preferences", result)
        self.assertIn("active_time_slots", result)
        self.assertIn("watch_duration", result)
        self.assertIn("platform_coverage", result)
        
        # 验证覆盖信息
        self.assertTrue(result["platform_coverage"]["douyin"])
        self.assertTrue(result["platform_coverage"]["bilibili"])
        self.assertTrue(result["platform_coverage"]["youtube"])

if __name__ == "__main__":
    unittest.main() 