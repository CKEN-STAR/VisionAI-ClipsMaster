#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
动态内容变形器测试

测试内容变形器的功能，验证不同变形策略的效果和组合应用。
"""

import os
import sys
import json
import unittest
from unittest.mock import MagicMock, patch

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.audience.content_morpher import (
    ContentMorpher, get_content_morpher, morph_content, 
    amplify_emotion, adjust_pacing, replace_cultural_references
)
from src.audience.profile_builder import get_user_profile
from src.audience.behavior_decoder import get_user_preferences

class TestContentMorpher(unittest.TestCase):
    """内容变形器测试类"""
    
    def setUp(self):
        """测试准备工作"""
        # 创建测试用用户ID
        self.test_user_id = "test_user_456"
        
        # 模拟用户画像引擎
        self.mock_profile_engine = MagicMock()
        
        # 模拟行为解码器
        self.mock_decoder = MagicMock()
        
        # 模拟文化适配器
        self.mock_culture_adapter = MagicMock()
        
        # 测试内容数据
        self.test_content = {
            "id": "content_123",
            "title": "春节的故事",
            "description": "一个关于中国新年的温馨故事",
            "scenes": [
                {
                    "id": "scene_1",
                    "start": 0.0,
                    "end": 5.0,
                    "duration": 5.0,
                    "emotion": {
                        "type": "喜悦",
                        "intensity": 0.6,
                        "score": 0.7
                    }
                },
                {
                    "id": "scene_2",
                    "start": 5.0,
                    "end": 15.0,
                    "duration": 10.0,
                    "emotion": {
                        "type": "悲伤",
                        "intensity": 0.4,
                        "score": 0.5
                    }
                },
                {
                    "id": "scene_3",
                    "start": 15.0,
                    "end": 20.0,
                    "duration": 5.0,
                    "emotion": {
                        "type": "紧张",
                        "intensity": 0.7,
                        "score": 0.8
                    }
                }
            ],
            "emotions": [
                {
                    "type": "喜悦",
                    "intensity": 0.6,
                    "score": 0.65
                },
                {
                    "type": "悲伤",
                    "intensity": 0.3,
                    "score": 0.35
                },
                {
                    "type": "紧张",
                    "intensity": 0.5,
                    "score": 0.55
                }
            ],
            "dialogues": [
                {
                    "id": "dialogue_1",
                    "text": "春节快到了，我们要准备红包和年夜饭。",
                    "start": 2.0,
                    "end": 5.0
                },
                {
                    "id": "dialogue_2",
                    "text": "大家一起贴春联，象征新的一年的到来。",
                    "start": 7.0,
                    "end": 10.0
                }
            ],
            "narration": [
                {
                    "id": "narration_1",
                    "text": "在中国传统文化中，春节是最重要的节日。",
                    "start": 0.0,
                    "end": 3.0
                }
            ]
        }
        
        # 测试用用户偏好数据
        self.test_preferences = {
            "user_id": self.test_user_id,
            "basic_info": {
                "age_group": "25-34",
                "gender": "male",
                "region": "east"
            },
            "emotion_preferences": {
                "primary_emotions": {
                    "joy": {"score": 0.8, "strength": "strong_like"},
                    "tension": {"score": 0.6, "strength": "like"}
                },
                "intensity": 0.8,
                "valence": 0.7
            },
            "pacing_preferences": {
                "overall_pace": {
                    "fast": {"score": 0.8, "strength": "strong_like"},
                    "medium": {"score": 0.4, "strength": "neutral"},
                    "slow": {"score": 0.2, "strength": "dislike"}
                },
                "scene_duration": {
                    "preferred": 4.0
                }
            }
        }
        
        # 创建变形器实例并注入mock对象
        self.morpher = ContentMorpher()
        
        # 使用MagicMock替换外部依赖
        self.orig_culture_adapter = self.morpher.culture_adapter
        self.morpher.culture_adapter = self.mock_culture_adapter
        
        # 配置模拟返回
        self.mock_culture_adapter.localize_cultural_references.side_effect = \
            lambda text, src, tgt: text.replace("春节", "Chinese New Year") \
                if src == "zh" and tgt == "en" \
                else text.replace("Christmas", "圣诞节") \
                if src == "en" and tgt == "zh" \
                else text
    
    def tearDown(self):
        """测试清理工作"""
        # 恢复原始对象
        if hasattr(self, 'morpher') and hasattr(self, 'orig_culture_adapter'):
            self.morpher.culture_adapter = self.orig_culture_adapter
    
    def test_amplify_emotion(self):
        """测试情感增强功能"""
        # 应用情感增强
        amplified = amplify_emotion(self.test_content, 1.5)
        
        # 验证情感数据被正确增强
        self.assertEqual(amplified["emotions"][0]["intensity"], 0.9)  # 0.6 * 1.5 = 0.9
        self.assertEqual(amplified["emotions"][0]["score"], 0.975)    # 0.65 * 1.5 = 0.975
        
        # 验证场景情感也被正确增强
        self.assertEqual(amplified["scenes"][0]["emotion"]["intensity"], 0.9)  # 0.6 * 1.5 = 0.9
        self.assertEqual(amplified["scenes"][0]["emotion"]["score"], 1.0)      # 0.7 * 1.5 = 1.05, capped at 1.0
        
        # 验证原始数据未被修改
        self.assertEqual(self.test_content["emotions"][0]["intensity"], 0.6)
        self.assertEqual(self.test_content["emotions"][0]["score"], 0.65)
    
    def test_adjust_pacing(self):
        """测试节奏调整功能"""
        # 应用节奏调整
        adjusted = adjust_pacing(self.test_content, target_bpm=150)
        
        # 验证场景持续时间被调整
        self.assertIn("adjusted_duration", adjusted["scenes"][0])
        self.assertIn("pacing_adjustment", adjusted["scenes"][0])
        
        # 验证调整信息
        adjustment = adjusted["scenes"][0]["pacing_adjustment"]
        self.assertEqual(adjustment["original_duration"], 5.0)
        self.assertEqual(adjustment["target_bpm"], 150)
        
        # 验证原始数据未被修改
        self.assertEqual(self.test_content["scenes"][0]["duration"], 5.0)
        self.assertNotIn("adjusted_duration", self.test_content["scenes"][0])
    
    def test_replace_cultural_references(self):
        """测试文化引用替换功能"""
        # 调用模拟的文化适配器
        localized = replace_cultural_references(self.test_content, "zh", "en")
        
        # 验证对话文本中的文化引用被替换
        self.assertIn("Chinese New Year", localized["dialogues"][0]["text"])
        
        # 验证标题和描述也被处理
        self.assertIn("Chinese New Year", localized["title"])
        
        # 验证原始数据未被修改
        self.assertIn("春节", self.test_content["dialogues"][0]["text"])
        self.assertIn("春节", self.test_content["title"])
    
    def test_morph_content_combined_strategies(self):
        """测试组合应用多种变形策略"""
        # 定义策略权重
        strategy_weights = {
            "情感极化": 0.8,
            "快节奏": 0.7,
            "西方化": 0.9
        }
        
        # 应用组合策略
        result = self.morpher.morph_content(self.test_content, strategy_weights)
        
        # 验证多种变形效果被应用
        # 1. 情感增强效果
        self.assertNotEqual(result["emotions"][0]["intensity"], self.test_content["emotions"][0]["intensity"])
        
        # 2. 节奏调整效果
        self.assertIn("adjusted_duration", result["scenes"][0])
        
        # 3. 文化本地化效果
        self.assertEqual(self.mock_culture_adapter.localize_cultural_references.call_count, 4)
    
    def test_apply_user_preferences(self):
        """测试根据用户偏好应用变形策略"""
        # 应用用户偏好
        result = self.morpher.apply_user_preferences(self.test_content, self.test_preferences)
        
        # 验证变形效果
        # 由于用户偏好包含高情感强度和快节奏偏好，这些策略应该被应用
        self.assertNotEqual(result["emotions"][0]["intensity"], self.test_content["emotions"][0]["intensity"])
        self.assertIn("adjusted_duration", result["scenes"][0])
    
    def test_preferences_to_strategies_conversion(self):
        """测试用户偏好到策略权重的转换"""
        # 转换用户偏好到策略权重
        weights = self.morpher._preferences_to_strategies(self.test_preferences)
        
        # 验证权重
        self.assertIn("情感极化", weights)
        self.assertIn("快节奏", weights)
        self.assertTrue(weights["情感极化"] > 0.7)  # 因为情感强度偏好为0.8
        self.assertTrue(weights["快节奏"] > 0.7)    # 因为快节奏偏好分数为0.8
    
    def test_specific_emotion_amplification(self):
        """测试特定情感增强功能"""
        # 应用特定情感增强
        result = self.morpher._amplify_specific_emotion(self.test_content, "悲伤", 2.0)
        
        # 验证只有指定的情感类型被增强
        self.assertEqual(result["emotions"][0]["intensity"], 0.6)  # 喜悦类型未修改
        self.assertEqual(result["emotions"][1]["intensity"], 0.6)  # 悲伤类型被增强: 0.3 * 2.0 = 0.6
        self.assertEqual(result["emotions"][2]["intensity"], 0.5)  # 紧张类型未修改


if __name__ == "__main__":
    unittest.main() 