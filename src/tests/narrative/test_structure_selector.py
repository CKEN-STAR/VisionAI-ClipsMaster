"""
叙事结构选择器测试
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock
import json
import yaml
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.narrative.structure_selector import StructureSelector, select_narrative_structure
from src.narrative.anchor_types import AnchorType, AnchorInfo


class TestStructureSelector(unittest.TestCase):
    """测试叙事结构选择器"""
    
    def setUp(self):
        """测试准备"""
        # 创建选择器实例
        self.selector = StructureSelector()
        
        # 创建测试元数据
        self.test_metadata = {
            "genre": "悬疑,犯罪",
            "emotion_tone": "紧张",
            "pace": "fast"
        }
        
        # 创建测试锚点
        self.test_anchors = [
            AnchorInfo(
                id="test_anchor_1",
                type=AnchorType.EMOTION,
                position=0.2,
                confidence=0.8,
                importance=0.7,
                description="情感高潮点"
            ),
            AnchorInfo(
                id="test_anchor_2",
                type=AnchorType.SUSPENSE,
                position=0.4,
                confidence=0.9,
                importance=0.8,
                description="悬念设置点"
            ),
            AnchorInfo(
                id="test_anchor_3",
                type=AnchorType.CHARACTER,
                position=0.6,
                confidence=0.7,
                importance=0.6,
                description="角色关系转折点"
            ),
            AnchorInfo(
                id="test_anchor_4",
                type=AnchorType.SUSPENSE,
                position=0.8,
                confidence=0.9,
                importance=0.9,
                description="悬念解决点"
            )
        ]
    
    def test_initialization(self):
        """测试初始化"""
        self.assertIsNotNone(self.selector)
        self.assertIsNotNone(self.selector.config)
        self.assertIsNotNone(self.selector.patterns)
        self.assertTrue(len(self.selector.patterns) > 0)
    
    def test_select_best_fit_metadata_only(self):
        """测试仅基于元数据选择最佳结构"""
        # 测试悬疑类型
        result = self.selector.select_best_fit(self.test_metadata)
        
        self.assertIsNotNone(result)
        self.assertIn("pattern_name", result)
        self.assertIn("confidence", result)
        self.assertIn("reason", result)
        self.assertIn("pattern_data", result)
        
        # 由于"悬疑"类型，预期会匹配悬念递进或倒叙风暴等模式
        pattern_name = result["pattern_name"]
        self.assertTrue(
            "悬念" in pattern_name or "倒叙" in pattern_name or 
            any("悬疑" in suit for suit in result["pattern_data"].get("suitability", []))
        )
        
        # 测试其他类型
        action_metadata = {
            "genre": "动作,冒险",
            "emotion_tone": "激烈",
            "pace": "fast"
        }
        action_result = self.selector.select_best_fit(action_metadata)
        self.assertIsNotNone(action_result)
        
        # 测试情感类型
        emotion_metadata = {
            "genre": "爱情,文艺",
            "emotion_tone": "温情",
            "pace": "slow"
        }
        emotion_result = self.selector.select_best_fit(emotion_metadata)
        self.assertIsNotNone(emotion_result)
    
    def test_select_best_fit_with_anchors(self):
        """测试使用锚点和元数据选择最佳结构"""
        result = self.selector.select_best_fit(self.test_metadata, self.test_anchors)
        
        self.assertIsNotNone(result)
        self.assertIn("pattern_name", result)
        self.assertIn("confidence", result)
        self.assertIn("reason", result)
        
        # 验证锚点对结果的影响
        # 1. 创建不同类型的锚点
        emotion_anchors = [a for a in self.test_anchors if a.type == AnchorType.EMOTION]
        suspense_anchors = [a for a in self.test_anchors if a.type == AnchorType.SUSPENSE]
        character_anchors = [a for a in self.test_anchors if a.type == AnchorType.CHARACTER]
        
        # 2. 仅使用情感锚点
        emotion_result = self.selector.select_best_fit(self.test_metadata, emotion_anchors)
        
        # 3. 仅使用悬念锚点
        suspense_result = self.selector.select_best_fit(self.test_metadata, suspense_anchors)
        
        # 验证不同锚点组合可能导致不同的选择结果
        self.assertIsNotNone(emotion_result["pattern_name"])
        self.assertIsNotNone(suspense_result["pattern_name"])
    
    def test_calculate_genre_similarity(self):
        """测试类型匹配度计算"""
        # 完全匹配
        similarity = self.selector._calculate_genre_similarity(
            "悬疑,犯罪", ["悬疑", "犯罪", "推理"]
        )
        self.assertGreaterEqual(similarity, 0.7)
        
        # 部分匹配
        similarity = self.selector._calculate_genre_similarity(
            "悬疑,爱情,喜剧", ["悬疑", "犯罪"]
        )
        self.assertGreater(similarity, 0.3)
        self.assertLess(similarity, 0.7)
        
        # 不匹配
        similarity = self.selector._calculate_genre_similarity(
            "爱情,喜剧", ["悬疑", "犯罪", "恐怖"]
        )
        self.assertLessEqual(similarity, 0.3)
    
    def test_calculate_anchor_compatibility(self):
        """测试锚点兼容性计算"""
        # 匹配的锚点类型
        pattern_data = {
            "anchor_types": [AnchorType.SUSPENSE, AnchorType.EMOTION],
            "min_anchors": 3
        }
        compatibility = self.selector._calculate_anchor_compatibility(
            self.test_anchors, pattern_data
        )
        self.assertGreaterEqual(compatibility, 0.7)
        
        # 部分匹配的锚点类型
        pattern_data = {
            "anchor_types": [AnchorType.CHARACTER, AnchorType.REVELATION],
            "min_anchors": 3
        }
        compatibility = self.selector._calculate_anchor_compatibility(
            self.test_anchors, pattern_data
        )
        self.assertLess(compatibility, 0.7)
        
        # 锚点数量不足
        pattern_data = {
            "anchor_types": [AnchorType.SUSPENSE, AnchorType.EMOTION],
            "min_anchors": 10
        }
        compatibility = self.selector._calculate_anchor_compatibility(
            self.test_anchors, pattern_data
        )
        self.assertLess(compatibility, 0.7)
    
    def test_map_anchors_to_structure(self):
        """测试将锚点映射到结构"""
        # 获取一个结构
        structures = self.selector.get_all_patterns()
        structure_name = list(structures.keys())[0]
        
        # 映射锚点
        mapping = self.selector.map_anchors_to_structure(self.test_anchors, structure_name)
        
        # 验证映射结果
        self.assertIsNotNone(mapping)
        self.assertGreater(len(mapping), 0)
        
        # 验证每个步骤都有对应的锚点列表
        steps = self.selector.get_structure_steps(structure_name)
        for step in steps:
            self.assertIn(step, mapping)
            self.assertIsInstance(mapping[step], list)
        
        # 验证所有锚点都被映射
        total_mapped = sum(len(anchors) for anchors in mapping.values())
        self.assertEqual(total_mapped, len(self.test_anchors))
    
    def test_get_structure_steps(self):
        """测试获取结构步骤"""
        # 获取所有模式
        patterns = self.selector.get_all_patterns()
        
        # 验证每个模式都有步骤
        for name in patterns:
            steps = self.selector.get_structure_steps(name)
            self.assertIsNotNone(steps)
            self.assertGreater(len(steps), 0)
        
        # 测试不存在的模式
        steps = self.selector.get_structure_steps("不存在的模式")
        self.assertEqual(steps, ["铺垫", "发展", "高潮", "结局"])
    
    def test_api_functions(self):
        """测试API函数"""
        # 测试选择叙事结构函数
        result = select_narrative_structure(self.test_metadata, self.test_anchors)
        self.assertIsNotNone(result)
        self.assertIn("pattern_name", result)
        self.assertIn("confidence", result)
    
    def tearDown(self):
        """测试清理"""
        pass


if __name__ == "__main__":
    unittest.main() 