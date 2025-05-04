#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
认知负荷优化器测试模块

测试认知负荷优化器的核心功能，包括负荷计算、内容优化和简化策略。
"""

import unittest
from unittest.mock import MagicMock, patch
import json
import numpy as np
from datetime import datetime

# 修改Python路径以导入项目模块
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.audience.cognitive_optimizer import (
    CognitiveLoadBalancer, get_cognitive_optimizer, 
    optimize_content, calculate_cognitive_load
)

class TestCognitiveOptimizer(unittest.TestCase):
    """认知负荷优化器测试类"""
    
    def setUp(self):
        """测试准备工作"""
        # 创建被测对象
        with patch('src.audience.cognitive_optimizer.get_logger', return_value=MagicMock()):
            self.optimizer = CognitiveLoadBalancer()
        
        # 测试内容数据
        self.test_content = {
            "title": "测试视频",
            "duration": 120.0,  # 2分钟
            "scenes": [
                {
                    "id": "scene_1",
                    "description": "开场介绍",
                    "duration": 15.0,
                    "elements": [
                        {"type": "text", "content": "欢迎", "importance": 0.8},
                        {"type": "image", "source": "logo.png", "importance": 0.7}
                    ],
                    "transitions": [
                        {"type": "fade", "duration": 1.0, "importance": 0.6}
                    ],
                    "effects": [],
                    "importance": 0.8
                },
                {
                    "id": "scene_2",
                    "description": "主要内容",
                    "duration": 60.0,
                    "elements": [
                        {"type": "video", "source": "clip1.mp4", "importance": 0.9},
                        {"type": "text", "content": "关键信息", "importance": 0.9},
                        {"type": "image", "source": "graphic1.png", "importance": 0.7},
                        {"type": "image", "source": "graphic2.png", "importance": 0.5},
                        {"type": "text", "content": "补充说明", "importance": 0.4}
                    ],
                    "transitions": [
                        {"type": "slide", "duration": 0.8, "importance": 0.7},
                        {"type": "zoom", "duration": 1.2, "importance": 0.5}
                    ],
                    "effects": [
                        {"type": "highlight", "duration": 2.0, "importance": 0.8},
                        {"type": "blur", "duration": 1.5, "importance": 0.4}
                    ],
                    "importance": 0.9,
                    "has_key_information": True
                },
                {
                    "id": "scene_3",
                    "description": "次要内容",
                    "duration": 30.0,
                    "elements": [
                        {"type": "video", "source": "clip2.mp4", "importance": 0.6},
                        {"type": "text", "content": "次要信息", "importance": 0.5},
                        {"type": "image", "source": "graphic3.png", "importance": 0.4}
                    ],
                    "transitions": [
                        {"type": "fade", "duration": 1.0, "importance": 0.5}
                    ],
                    "effects": [
                        {"type": "color_shift", "duration": 2.0, "importance": 0.3}
                    ],
                    "importance": 0.6
                },
                {
                    "id": "scene_4",
                    "description": "结尾总结",
                    "duration": 15.0,
                    "elements": [
                        {"type": "text", "content": "总结", "importance": 0.8},
                        {"type": "image", "source": "logo.png", "importance": 0.7}
                    ],
                    "transitions": [
                        {"type": "fade", "duration": 1.0, "importance": 0.6}
                    ],
                    "effects": [],
                    "importance": 0.7,
                    "emotional_peak": True
                }
            ],
            "dialogues": [
                {"speaker": "narrator", "text": "欢迎观看我们的演示视频", "importance": 0.8},
                {"speaker": "presenter", "text": "今天我们将介绍一个重要的新功能", "importance": 0.9},
                {"speaker": "presenter", "text": "这个功能有很多优点和特性", "importance": 0.7},
                {"speaker": "presenter", "text": "首先，它能够大幅提升效率", "importance": 0.8},
                {"speaker": "presenter", "text": "其次，它使用起来非常简单", "importance": 0.7},
                {"speaker": "presenter", "text": "最后，它与现有系统完美兼容", "importance": 0.6},
                {"speaker": "narrator", "text": "感谢观看，请不要忘记关注我们", "importance": 0.7}
            ],
            "tags": ["教程", "技术", "新功能"],
            "complexity": 0.7,
            "twists_per_min": 3.5
        }
        
        # 测试用户画像
        self.test_user_profile = {
            "id": "user_123",
            "name": "测试用户",
            "cognitive_abilities": {
                "attention_span": 0.6,
                "processing_speed": 0.7,
                "domain_knowledge": 0.4
            },
            "preferences": {
                "content_complexity": 0.5,
                "visual_density": 0.6,
                "pacing": 0.7
            }
        }
        
        # 测试超高复杂度内容
        self.complex_content = {
            "title": "复杂测试视频",
            "duration": 180.0,  # 3分钟
            "scenes": [
                # 添加8个复杂场景
            ],
            "dialogues": [
                # 添加15个对话
            ],
            "tags": ["高级", "技术", "专业"],
            "complexity": 0.9,
            "twists_per_min": 6.0
        }
        
        # 补充复杂内容的场景
        for i in range(8):
            scene = {
                "id": f"complex_scene_{i+1}",
                "description": f"复杂场景 {i+1}",
                "duration": 20.0,
                "elements": [],
                "transitions": [],
                "effects": [],
                "importance": 0.7 if i % 2 == 0 else 0.5
            }
            
            # 添加多个元素
            for j in range(8):
                scene["elements"].append({
                    "type": "element",
                    "content": f"元素 {j+1}",
                    "importance": 0.8 if j < 2 else (0.6 if j < 4 else 0.4)
                })
            
            # 添加多个转场
            for j in range(4):
                scene["transitions"].append({
                    "type": "transition",
                    "duration": 1.0,
                    "importance": 0.7 if j < 2 else 0.4
                })
            
            # 添加多个特效
            for j in range(5):
                scene["effects"].append({
                    "type": "effect",
                    "duration": 2.0,
                    "importance": 0.7 if j < 2 else 0.3
                })
            
            self.complex_content["scenes"].append(scene)
        
        # 添加对话
        for i in range(15):
            self.complex_content["dialogues"].append({
                "speaker": "presenter" if i % 2 == 0 else "expert",
                "text": f"这是一段复杂的专业对话内容，包含了许多技术术语和复杂概念 {i+1}",
                "importance": 0.8 if i < 5 else (0.6 if i < 10 else 0.4)
            })
    
    def test_initialization(self):
        """测试初始化"""
        self.assertIsNotNone(self.optimizer)
        self.assertEqual(self.optimizer.MAX_LOAD, 0.7)
        self.assertIn("thresholds", self.optimizer.config)
        self.assertIn("user_factors", self.optimizer.config)
        self.assertIn("content_factors", self.optimizer.config)
    
    def test_calculate_load(self):
        """测试认知负荷计算"""
        # 使用默认用户画像计算负荷
        load = self.optimizer._calculate_load(self.test_content)
        
        # 验证结果在合理范围
        self.assertGreaterEqual(load, 0.0)
        self.assertLessEqual(load, 1.0)
        
        # 使用提供的用户画像计算负荷
        load_with_profile = self.optimizer._calculate_load(self.test_content, self.test_user_profile)
        
        # 验证结果在合理范围
        self.assertGreaterEqual(load_with_profile, 0.0)
        self.assertLessEqual(load_with_profile, 1.0)
    
    def test_extract_content_features(self):
        """测试内容特征提取"""
        features = self.optimizer._extract_content_features(self.test_content)
        
        self.assertIn("complexity", features)
        self.assertIn("density", features)
        self.assertIn("pacing", features)
        self.assertIn("novelty", features)
        
        # 验证特征值在合理范围
        for feature, value in features.items():
            self.assertGreaterEqual(value, 0.0)
            self.assertLessEqual(value, 1.0)
    
    def test_extract_user_factors(self):
        """测试用户因素提取"""
        factors = self.optimizer._extract_user_factors(self.test_user_profile)
        
        self.assertIn("attention_span", factors)
        self.assertIn("processing_speed", factors)
        self.assertIn("domain_knowledge", factors)
        
        # 验证因素值与输入一致
        self.assertEqual(factors["attention_span"], 0.6)
        self.assertEqual(factors["processing_speed"], 0.7)
        self.assertEqual(factors["domain_knowledge"], 0.4)
    
    def test_optimize_normal_content(self):
        """测试优化普通内容"""
        # 优化普通内容
        optimized = self.optimizer.optimize(self.test_content, self.test_user_profile)
        
        # 验证优化结果非空
        self.assertIsNotNone(optimized)
        self.assertIn("scenes", optimized)
        self.assertIn("dialogues", optimized)
        
        # 验证优化前后负荷变化
        load_before = self.optimizer._calculate_load(self.test_content, self.test_user_profile)
        load_after = self.optimizer._calculate_load(optimized, self.test_user_profile)
        
        # 如果原始负荷高于阈值，验证优化后负荷降低
        if load_before > self.optimizer.config["thresholds"]["max_cognitive_load"]:
            self.assertLess(load_after, load_before)
    
    def test_optimize_complex_content(self):
        """测试优化复杂内容"""
        # 优化复杂内容
        optimized = self.optimizer.optimize(self.complex_content, self.test_user_profile)
        
        # 验证优化结果非空
        self.assertIsNotNone(optimized)
        self.assertIn("scenes", optimized)
        
        # 验证优化前后负荷变化
        load_before = self.optimizer._calculate_load(self.complex_content, self.test_user_profile)
        load_after = self.optimizer._calculate_load(optimized, self.test_user_profile)
        
        # 验证优化后负荷降低
        self.assertLess(load_after, load_before)
        
        # 验证场景数量减少
        self.assertLessEqual(len(optimized["scenes"]), len(self.complex_content["scenes"]))
    
    def test_reduce_information_density(self):
        """测试降低信息密度"""
        # 应用信息密度降低
        simplified = self.optimizer._reduce_information_density(self.test_content, 0.8)
        
        # 验证结果
        self.assertIsNotNone(simplified)
        
        # 验证元素数量减少
        elements_before = sum(len(scene.get("elements", [])) for scene in self.test_content["scenes"])
        elements_after = sum(len(scene.get("elements", [])) for scene in simplified["scenes"])
        
        self.assertLessEqual(elements_after, elements_before)
    
    def test_slow_down_pacing(self):
        """测试降低节奏"""
        # 应用节奏降低
        simplified = self.optimizer._slow_down_pacing(self.test_content, 0.7)
        
        # 验证结果
        self.assertIsNotNone(simplified)
        
        # 验证场景持续时间变化
        total_duration_before = sum(scene.get("duration", 0) for scene in self.test_content["scenes"])
        total_duration_after = sum(scene.get("duration", 0) for scene in simplified["scenes"])
        
        # 如果有场景合并，可能有些场景被移除，但总持续时间不会减少
        if len(simplified["scenes"]) == len(self.test_content["scenes"]):
            self.assertGreaterEqual(total_duration_after, total_duration_before)
    
    def test_reduce_transitions(self):
        """测试减少转场和特效"""
        # 应用转场和特效减少
        simplified = self.optimizer._reduce_transitions(self.test_content, 0.9)
        
        # 验证结果
        self.assertIsNotNone(simplified)
        
        # 验证转场和特效数量减少
        transitions_before = sum(len(scene.get("transitions", [])) for scene in self.test_content["scenes"])
        transitions_after = sum(len(scene.get("transitions", [])) for scene in simplified["scenes"])
        
        effects_before = sum(len(scene.get("effects", [])) for scene in self.test_content["scenes"])
        effects_after = sum(len(scene.get("effects", [])) for scene in simplified["scenes"])
        
        # 检查是否减少
        self.assertLessEqual(transitions_after, transitions_before)
        self.assertLessEqual(effects_after, effects_before)
    
    def test_prioritize_essential_content(self):
        """测试优先保留核心内容"""
        # 应用核心内容优先
        simplified = self.optimizer._prioritize_essential_content(self.complex_content, 0.8)
        
        # 验证结果
        self.assertIsNotNone(simplified)
        
        # 验证场景数量减少
        self.assertLess(len(simplified["scenes"]), len(self.complex_content["scenes"]))
        
        # 验证重要场景保留
        for scene in simplified["scenes"]:
            # 检查是否保留了重要性高的场景
            if "importance" in scene:
                self.assertGreaterEqual(scene["importance"], 0.5)
    
    def test_convenience_functions(self):
        """测试便捷函数"""
        # 测试单例模式
        optimizer1 = get_cognitive_optimizer()
        optimizer2 = get_cognitive_optimizer()
        self.assertIs(optimizer1, optimizer2)
        
        # 测试优化内容便捷函数
        with patch('src.audience.cognitive_optimizer._cognitive_optimizer', self.optimizer):
            result = optimize_content(self.test_content, self.test_user_profile)
            self.assertIsNotNone(result)
        
        # 测试计算负荷便捷函数
        with patch('src.audience.cognitive_optimizer._cognitive_optimizer', self.optimizer):
            load = calculate_cognitive_load(self.test_content, self.test_user_profile)
            self.assertGreaterEqual(load, 0.0)
            self.assertLessEqual(load, 1.0)


if __name__ == "__main__":
    unittest.main() 