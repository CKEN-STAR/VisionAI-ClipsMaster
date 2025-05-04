"""
测试跨媒介模式迁移适配
"""

import sys
import os
import unittest
from unittest.mock import patch, MagicMock
import json
import yaml
from pathlib import Path
import random

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.adaptation.cross_media import CrossMediaAdapter


class TestCrossMediaAdapter(unittest.TestCase):
    """测试跨媒介模式迁移适配器"""
    
    def setUp(self):
        """测试前准备"""
        # 创建测试配置文件
        self.config_path = "configs/test_cross_media.yaml"
        with open(self.config_path, "w", encoding="utf-8") as f:
            yaml.dump({
                "media_types": ["短视频", "互动剧", "广播剧", "漫画"],
                "adaptation_rules": {
                    "短视频": {
                        "duration_factor": 0.5,
                        "pattern_priorities": ["climax", "conflict"]
                    }
                }
            }, f, allow_unicode=True)
        
        # 创建测试模式
        self.test_pattern = {
            "id": "test_pattern_1",
            "type": "climax",
            "media_type": "电影",
            "description": "测试模式",
            "duration": 120.0,
            "position": 0.7,
            "sentiment": 0.5,
            "keywords": ["高潮", "转折", "惊喜"],
            "narrative_density": 0.8
        }
    
    def tearDown(self):
        """测试后清理"""
        # 删除测试配置文件
        if os.path.exists(self.config_path):
            os.remove(self.config_path)
    
    @patch("src.version_management.pattern_version_manager.PatternVersionManager")
    @patch("src.algorithms.pattern_mining.PatternMiner")
    def test_init(self, mock_miner, mock_version_manager):
        """测试初始化"""
        adapter = CrossMediaAdapter(self.config_path)
        
        # 检查配置是否正确加载
        self.assertIn("短视频", adapter.config["media_types"])
        self.assertEqual(0.5, adapter.config["adaptation_rules"]["短视频"]["duration_factor"])
        
        # 检查映射是否正确初始化
        self.assertIn("short_video", adapter.media_type_mapping)
        self.assertEqual("短视频", adapter.media_type_mapping["short_video"])
        self.assertEqual("short_video", adapter.reverse_media_mapping["短视频"])
    
    @patch("src.version_management.pattern_version_manager.PatternVersionManager")
    @patch("src.algorithms.pattern_mining.PatternMiner")
    def test_adapt_pattern_short_video(self, mock_miner, mock_version_manager):
        """测试适配模式到短视频"""
        adapter = CrossMediaAdapter(self.config_path)
        
        # 适配到短视频
        adapted = adapter.adapt_pattern(self.test_pattern, "短视频")
        
        # 检查适配结果
        self.assertEqual("短视频", adapted["media_type"])
        self.assertEqual(self.test_pattern["id"], adapted["id"])
        self.assertEqual(self.test_pattern["type"], adapted["type"])
        self.assertLess(adapted["duration"], self.test_pattern["duration"])
        self.assertTrue(adapted["adapted"])
        self.assertIn("adaptation_method", adapted)
        self.assertEqual("电影", adapted["source_media"])
        self.assertEqual("短视频", adapted["target_media"])
        self.assertIn("adaptation_history", adapted)
        self.assertEqual(1, len(adapted["adaptation_history"]))
    
    @patch("src.version_management.pattern_version_manager.PatternVersionManager")
    @patch("src.algorithms.pattern_mining.PatternMiner") 
    def test_adapt_pattern_interactive(self, mock_miner, mock_version_manager):
        """测试适配模式到互动剧"""
        adapter = CrossMediaAdapter(self.config_path)
        
        # 适配到互动剧
        adapted = adapter.adapt_pattern(self.test_pattern, "互动剧")
        
        # 检查适配结果
        self.assertEqual("互动剧", adapted["media_type"])
        self.assertTrue(adapted["has_branches"])
        self.assertIn("branch_points", adapted)
        self.assertIn("branch_factor", adapted)
        
        # 检查高潮类型是否有决策需求
        self.assertTrue(adapted["decision_required"])
        self.assertIn("choice_options", adapted)
    
    @patch("src.version_management.pattern_version_manager.PatternVersionManager")
    @patch("src.algorithms.pattern_mining.PatternMiner")
    def test_batch_adapt_patterns(self, mock_miner, mock_version_manager):
        """测试批量适配模式"""
        adapter = CrossMediaAdapter(self.config_path)
        
        # 创建多个测试模式
        patterns = []
        for i in range(3):
            pattern = self.test_pattern.copy()
            pattern["id"] = f"test_pattern_{i+1}"
            patterns.append(pattern)
        
        # 批量适配
        adapted = adapter.batch_adapt_patterns(patterns, "短视频")
        
        # 检查适配结果
        self.assertEqual(3, len(adapted))
        for p in adapted:
            self.assertEqual("短视频", p["media_type"])
            self.assertTrue(p["adapted"])
    
    @patch("src.version_management.pattern_version_manager.PatternVersionManager")
    @patch("src.algorithms.pattern_mining.PatternMiner")
    def test_get_adaptation_method(self, mock_miner, mock_version_manager):
        """测试获取适配方法"""
        adapter = CrossMediaAdapter(self.config_path)
        
        # 测试各种组合
        method = adapter._get_adaptation_method("opening", "短视频")
        self.assertEqual("compress", method)
        
        method = adapter._get_adaptation_method("climax", "互动剧")
        self.assertEqual("decision_point", method)
        
        method = adapter._get_adaptation_method("unknown", "短视频")
        self.assertEqual("default", method)
    
    @patch("src.version_management.pattern_version_manager.PatternVersionManager")
    @patch("src.algorithms.pattern_mining.PatternMiner")
    def test_get_supported_media_types(self, mock_miner, mock_version_manager):
        """测试获取支持的媒介类型"""
        adapter = CrossMediaAdapter(self.config_path)
        
        media_types = adapter.get_supported_media_types()
        self.assertIsInstance(media_types, list)
        self.assertIn("短视频", media_types)
        self.assertIn("互动剧", media_types)


if __name__ == "__main__":
    unittest.main() 