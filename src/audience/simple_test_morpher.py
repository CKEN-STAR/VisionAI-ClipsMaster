#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import copy
import unittest
from content_morpher_demo import ContentMorpher, generate_mock_content

class SimpleMorpherTest(unittest.TestCase):
    """简化版内容变形器测试"""
    
    def setUp(self):
        """测试准备"""
        self.morpher = ContentMorpher()
        
        # 创建测试内容
        self.test_content = {
            "id": "test_content_123",
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
                    "end": 10.0,
                    "duration": 5.0,
                    "emotion": {
                        "type": "悲伤",
                        "intensity": 0.4,
                        "score": 0.5
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
                }
            ],
            "dialogues": [
                {
                    "id": "dialogue_1",
                    "text": "春节快到了，我们要准备红包和年夜饭。",
                    "start": 2.0,
                    "end": 5.0
                }
            ]
        }
    
    def test_emotion_amplification(self):
        """测试情感增强功能"""
        # 应用情感增强
        result = self.morpher.morph_content(self.test_content, {"情感增强": 0.8})
        
        # 验证情感被增强
        self.assertGreater(result["emotions"][0]["intensity"], self.test_content["emotions"][0]["intensity"])
        self.assertGreater(result["emotions"][0]["score"], self.test_content["emotions"][0]["score"])
        
        # 验证场景情感也被增强
        self.assertGreater(result["scenes"][0]["emotion"]["intensity"], 
                           self.test_content["scenes"][0]["emotion"]["intensity"])
        
        # 验证原始数据未被修改
        self.assertEqual(self.test_content["emotions"][0]["intensity"], 0.6)
    
    def test_pacing_adjustment(self):
        """测试节奏调整功能"""
        # 应用节奏调整
        result = self.morpher.morph_content(self.test_content, {"节奏调整": 0.8, "快节奏": 0.7})
        
        # 验证场景持续时间被调整
        self.assertTrue(hasattr(result["scenes"][0], "adjusted_duration") or 
                        "adjusted_duration" in result["scenes"][0])
        
        # 验证原始数据未被修改
        self.assertEqual(self.test_content["scenes"][0]["duration"], 5.0)
        self.assertFalse(hasattr(self.test_content["scenes"][0], "adjusted_duration") or 
                         "adjusted_duration" in self.test_content["scenes"][0])
    
    def test_cultural_localization(self):
        """测试文化本地化功能"""
        # 应用文化本地化
        result = self.morpher.morph_content(self.test_content, {"文化本地化": 0.8})
        
        # 验证对话文本被本地化
        self.assertIn("Chinese New Year", result["dialogues"][0]["text"])
        self.assertIn("red envelope", result["dialogues"][0]["text"])
        
        # 验证原始数据未被修改
        self.assertIn("春节", self.test_content["dialogues"][0]["text"])
        self.assertIn("红包", self.test_content["dialogues"][0]["text"])
    
    def test_combined_strategies(self):
        """测试组合策略功能"""
        # 应用组合策略
        result = self.morpher.morph_content(self.test_content, {
            "情感增强": 0.8,
            "节奏调整": 0.7,
            "文化本地化": 0.9
        })
        
        # 验证情感被增强
        self.assertGreater(result["emotions"][0]["intensity"], self.test_content["emotions"][0]["intensity"])
        
        # 验证节奏被调整
        self.assertTrue(hasattr(result["scenes"][0], "adjusted_duration") or 
                        "adjusted_duration" in result["scenes"][0])
        
        # 验证文化被本地化
        self.assertIn("Chinese New Year", result["dialogues"][0]["text"])

if __name__ == "__main__":
    unittest.main() 