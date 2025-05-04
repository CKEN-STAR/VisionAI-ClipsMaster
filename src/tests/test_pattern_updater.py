"""
测试模式实时更新器
"""

import sys
import os
import unittest
from unittest.mock import patch, MagicMock
import json
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.core.pattern_updater import PatternUpdater


class TestPatternUpdater(unittest.TestCase):
    """测试模式实时更新器类"""
    
    def setUp(self):
        """测试前准备"""
        # 创建测试配置文件
        self.config_path = "configs/test_pattern_updater.yaml"
        with open(self.config_path, "w", encoding="utf-8") as f:
            f.write("""
# 测试配置
batch_size: 10
update_threshold: 0.5
min_patterns_for_version: 5
auto_version: true
version_interval: 3600
pattern_types:
  - opening
  - climax
  - transition
            """)
    
    def tearDown(self):
        """测试后清理"""
        # 删除测试配置文件
        if os.path.exists(self.config_path):
            os.remove(self.config_path)
    
    @patch('src.algorithms.pattern_mining.PatternMiner')
    @patch('src.data.hit_pattern_lake.HitPatternLake')
    @patch('src.version_management.pattern_version_manager.PatternVersionManager')
    @patch('src.evaluation.pattern_evaluator.PatternEvaluator')
    def test_streaming_update(self, mock_evaluator, mock_version_manager, mock_pattern_lake, mock_pattern_miner):
        """测试流式更新方法"""
        # 设置模拟
        mock_pattern_miner.return_value.extract_patterns.return_value = [
            {"id": "pattern1", "type": "opening", "frequency": 0.8},
            {"id": "pattern2", "type": "climax", "frequency": 0.7}
        ]
        mock_pattern_miner.return_value.filter_patterns.return_value = [
            {"id": "pattern1", "type": "opening", "frequency": 0.8},
            {"id": "pattern2", "type": "climax", "frequency": 0.7}
        ]
        
        mock_pattern_lake.return_value.query_patterns.return_value = MagicMock()
        mock_pattern_lake.return_value.query_patterns.return_value.empty = False
        mock_pattern_lake.return_value.query_patterns.return_value.to_dict.return_value = [
            {"id": "data1", "text": "测试数据1"},
            {"id": "data2", "text": "测试数据2"}
        ]
        
        mock_evaluator.return_value.evaluate_multiple_patterns.return_value = [
            {"pattern_id": "pattern1", "pattern_type": "opening", "impact_score": 0.8},
            {"pattern_id": "pattern2", "pattern_type": "climax", "impact_score": 0.6}
        ]
        
        mock_version_manager.return_value.get_pattern_config.return_value = {
            "top_patterns": []
        }
        mock_version_manager.return_value.get_latest_version.return_value = "v1.0"
        
        # 创建测试数据
        test_data = [
            {
                "id": "test1",
                "origin_srt": "原始字幕1",
                "hit_srt": "命中字幕1"
            },
            {
                "id": "test2",
                "origin_srt": "原始字幕2",
                "hit_srt": "命中字幕2"
            }
        ]
        
        # 初始化更新器
        updater = PatternUpdater(config_path=self.config_path)
        
        # 调用流式更新
        result = updater.streaming_update(test_data)
        
        # 断言
        self.assertIsNotNone(result)
        self.assertIn("update_id", result)
        self.assertIn("timestamp", result)
        self.assertIn("stats", result)
        self.assertEqual(result["stats"]["processed_items"], 2)
        self.assertEqual(result["stats"]["significant_patterns"], 2)
        
        # 验证调用
        mock_pattern_lake.return_value.ingest_data.assert_called()
        mock_pattern_miner.return_value.extract_patterns.assert_called()
        mock_evaluator.return_value.evaluate_multiple_patterns.assert_called()
        mock_version_manager.return_value.update_pattern_config.assert_called()
    
    def test_load_config(self):
        """测试配置加载"""
        updater = PatternUpdater(config_path=self.config_path)
        
        # 验证配置是否正确加载
        self.assertEqual(updater.config["batch_size"], 10)
        self.assertEqual(updater.config["update_threshold"], 0.5)
        self.assertEqual(updater.config["min_patterns_for_version"], 5)
        self.assertTrue(updater.config["auto_version"])
        self.assertEqual(updater.config["version_interval"], 3600)
        self.assertIn("opening", updater.config["pattern_types"])
        self.assertIn("climax", updater.config["pattern_types"])
        self.assertIn("transition", updater.config["pattern_types"])


if __name__ == "__main__":
    unittest.main() 