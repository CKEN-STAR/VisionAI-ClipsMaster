"""
时空折叠引擎测试模块
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock
import json
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.nonlinear.time_folder import (
    TimeFolder, fold_timeline, FoldingMode, TimeFoldingStrategy,
    get_folding_strategy, list_folding_strategies
)
from src.narrative.anchor_types import AnchorType, AnchorInfo


class TestTimeFolder(unittest.TestCase):
    """测试时空折叠引擎"""
    
    def setUp(self):
        """测试准备"""
        # 创建测试对象
        self.folder = TimeFolder()
        
        # 创建测试场景
        self.test_scenes = [
            {
                "id": "scene_1",
                "text": "主角在早晨醒来，准备开始新的一天。",
                "emotion_score": 0.2,
                "characters": ["主角"],
                "duration": 5.0
            },
            {
                "id": "scene_2",
                "text": "主角在工作中遇到了一个难题。",
                "emotion_score": -0.3,
                "characters": ["主角", "同事"],
                "duration": 8.0
            },
            {
                "id": "scene_3",
                "text": "主角回忆起过去解决类似问题的经验。",
                "emotion_score": 0.1,
                "characters": ["主角"],
                "duration": 6.0
            },
            {
                "id": "scene_4",
                "text": "主角成功解决了问题，获得了同事的赞赏。",
                "emotion_score": 0.7,
                "characters": ["主角", "同事", "上司"],
                "duration": 10.0
            },
            {
                "id": "scene_5",
                "text": "主角结束了一天的工作，感到满足。",
                "emotion_score": 0.5,
                "characters": ["主角"],
                "duration": 4.0
            }
        ]
        
        # 创建测试锚点
        self.test_anchors = [
            AnchorInfo(
                id="emotion_anchor_1",
                type=AnchorType.EMOTION,
                position=0.2,  # 大约对应场景2
                confidence=0.8,
                importance=0.6,
                description="情感低谷",
                emotion_score=-0.3
            ),
            AnchorInfo(
                id="climax_anchor_1",
                type=AnchorType.CLIMAX,
                position=0.7,  # 大约对应场景4
                confidence=0.9,
                importance=0.9,
                description="剧情高潮",
                emotion_score=0.7
            ),
            AnchorInfo(
                id="character_anchor_1",
                type=AnchorType.CHARACTER,
                position=0.7,  # 大约对应场景4
                confidence=0.8,
                importance=0.7,
                description="人物互动高峰",
                characters=["主角", "同事", "上司"]
            ),
            AnchorInfo(
                id="resolution_anchor_1",
                type=AnchorType.RESOLUTION,
                position=0.9,  # 大约对应场景5
                confidence=0.7,
                importance=0.6,
                description="情节解决",
                emotion_score=0.5
            )
        ]
    
    def test_initialization(self):
        """测试初始化"""
        self.assertIsNotNone(self.folder)
        self.assertIsNotNone(self.folder.strategies)
        self.assertTrue(len(self.folder.strategies) > 0)
    
    def test_fold_timeline_preserve_anchors(self):
        """测试保留锚点的折叠方法"""
        result = self.folder.fold_timeline(
            self.test_scenes, 
            self.test_anchors,
            structure_name="高潮迭起",
            mode=FoldingMode.PRESERVE_ANCHORS
        )
        
        # 验证结果
        self.assertIsNotNone(result)
        self.assertIsInstance(result, list)
        
        # 在保留锚点模式下，场景数量应该减少
        self.assertLessEqual(len(result), len(self.test_scenes))
        
        # 所有结果场景都应该标记为已折叠
        for scene in result:
            self.assertTrue(scene.get("folded", False))
            self.assertEqual(scene.get("structure_name"), "高潮迭起")
            # 验证策略名称正确
            self.assertIn(scene.get("folding_strategy"), ["高潮迭起", "escalating_peaks"])
    
    def test_fold_timeline_default(self):
        """测试默认参数的折叠"""
        result = fold_timeline(self.test_scenes, self.test_anchors)
        
        # 验证结果
        self.assertIsNotNone(result)
        self.assertIsInstance(result, list)
        self.assertLess(len(result), len(self.test_scenes))
    
    def test_folding_strategy_availability(self):
        """测试折叠策略可用性"""
        # 获取所有策略名称
        strategies = list_folding_strategies()
        
        # 验证结果
        self.assertIsNotNone(strategies)
        self.assertIsInstance(strategies, list)
        self.assertTrue(len(strategies) > 0)
        
        # 测试已知策略是否存在
        known_strategies = ["倒叙风暴", "多线织网", "环形结构", "高潮迭起", "并行蒙太奇"]
        for strategy in known_strategies:
            self.assertIn(strategy, strategies)
        
        # 测试获取具体策略信息
        for strategy_name in strategies:
            strategy_info = get_folding_strategy(strategy_name)
            self.assertIsNotNone(strategy_info)
            self.assertEqual(strategy_info["name"], strategy_name)
    
    def test_fold_narrative_driven(self):
        """测试叙事驱动的折叠方法"""
        # 使用倒叙风暴结构
        result = self.folder.fold_timeline(
            self.test_scenes, 
            self.test_anchors,
            structure_name="倒叙风暴",
            mode=FoldingMode.NARRATIVE_DRIVEN
        )
        
        # 在倒叙风暴结构中，第一个场景应该是高潮
        self.assertTrue(any(scene.get("is_climax", False) for scene in result))
        
        # 应该存在回闪场景
        self.assertTrue(any(scene.get("is_flashback", False) for scene in result))
    
    def tearDown(self):
        """测试清理"""
        pass


if __name__ == "__main__":
    unittest.main() 