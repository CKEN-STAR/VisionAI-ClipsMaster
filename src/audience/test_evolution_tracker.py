#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
偏好进化追踪器单元测试

测试偏好进化追踪器的功能，包括偏好迁移检测、趋势计算和预测功能。
"""

import unittest
import json
import os
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any
from unittest.mock import patch, MagicMock

# 添加项目根目录到系统路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

try:
    from src.audience.evolution_tracker import (
        PreferenceEvolution, 
        detect_preference_shift,
        track_preference_changes,
        get_preference_evolution_summary
    )
except ImportError:
    # 处理导入错误
    print("无法导入偏好进化追踪器模块，请确保代码路径正确")


class TestPreferenceEvolutionTracker(unittest.TestCase):
    """偏好进化追踪器单元测试类"""
    
    def setUp(self):
        """测试前准备"""
        # 创建测试数据
        self.test_user_id = "test_user_123"
        self.test_history = self._create_test_history()
        
        # 创建模拟存储管理器
        self.mock_storage = MagicMock()
        self.mock_storage.get_preference_history.return_value = self.test_history
        
        # 创建模拟偏好分析器
        self.mock_analyzer = MagicMock()
        self.mock_analyzer.analyze_user_preferences.return_value = self._create_test_preferences()
        
        # 使用补丁替换依赖
        self.storage_patcher = patch('src.audience.evolution_tracker.get_storage_manager')
        self.analyzer_patcher = patch('src.audience.evolution_tracker.PreferenceAnalyzer')
        self.logger_patcher = patch('src.audience.evolution_tracker.get_logger')
        
        self.mock_get_storage = self.storage_patcher.start()
        self.mock_get_analyzer = self.analyzer_patcher.start()
        self.mock_get_logger = self.logger_patcher.start()
        
        self.mock_get_storage.return_value = self.mock_storage
        self.mock_get_analyzer.return_value = self.mock_analyzer
        
        # 创建模拟日志器
        self.mock_logger = MagicMock()
        self.mock_get_logger.return_value = self.mock_logger
        
        # 创建偏好进化追踪器实例
        self.tracker = PreferenceEvolution()
    
    def tearDown(self):
        """测试后清理"""
        # 停止模拟补丁
        self.storage_patcher.stop()
        self.analyzer_patcher.stop()
        self.logger_patcher.stop()
    
    def test_init(self):
        """测试初始化"""
        self.assertIsNotNone(self.tracker)
        self.assertEqual(self.tracker.forecast_window, 30)
        self.assertEqual(self.tracker.min_history_points, 5)
        self.assertAlmostEqual(self.tracker.time_decay, 0.95)
    
    def test_detect_shift(self):
        """测试偏好迁移检测"""
        # 执行测试
        result = self.tracker.detect_shift(self.test_user_id)
        
        # 验证结果
        self.assertIn("current_trend", result)
        self.assertIn("predicted_shift", result)
        
        # 验证调用
        self.mock_storage.get_preference_history.assert_called_once_with(self.test_user_id)
    
    def test_calc_trend(self):
        """测试趋势计算"""
        # 执行测试
        result = self.tracker._calc_trend(self.test_history[-6:])
        
        # 验证结果
        self.assertIn("status", result)
        self.assertEqual(result["status"], "success")
        self.assertIn("dimension_trends", result)
        self.assertIn("significant_shifts", result)
        self.assertIn("overall_stability", result)
        
        # 验证维度趋势
        for dimension in self.tracker.tracked_dimensions:
            self.assertIn(dimension, result["dimension_trends"])
    
    def test_prophet_forecast(self):
        """测试偏好预测"""
        # 执行测试
        result = self.tracker._prophet_forecast(self.test_history)
        
        # 验证结果
        self.assertIn("status", result)
        self.assertEqual(result["status"], "success")
        self.assertIn("dimension_forecasts", result)
        self.assertIn("potential_shifts", result)
        
        # 至少应该有一些维度的预测
        self.assertGreater(len(result["dimension_forecasts"]), 0)
    
    def test_extract_dimension_values(self):
        """测试维度值提取"""
        # 执行测试
        result = self.tracker._extract_dimension_values(self.test_history, "genre")
        
        # 验证结果
        self.assertGreater(len(result), 0)
        for item in result:
            self.assertIn("timestamp", item)
            self.assertIn("value", item)
    
    def test_get_dimension_metric(self):
        """测试维度指标获取"""
        # 测试数据
        genre_data = {
            "favorites": ["动作", "科幻"],
            "strength_map": {
                "动作": {"ratio": 0.75},
                "科幻": {"ratio": 0.55}
            }
        }
        
        pace_data = {
            "preferred_pace": "fast"
        }
        
        # 执行测试
        genre_value = self.tracker._get_dimension_metric(genre_data, "genre")
        pace_value = self.tracker._get_dimension_metric(pace_data, "pace")
        
        # 验证结果
        self.assertAlmostEqual(genre_value, 0.75)
        self.assertAlmostEqual(pace_value, 0.75)  # fast应该映射到0.75
    
    def test_calculate_trend_slope(self):
        """测试趋势斜率计算"""
        # 测试数据
        time_series = [
            {"timestamp": datetime.now() - timedelta(days=5), "value": 0.4},
            {"timestamp": datetime.now() - timedelta(days=4), "value": 0.45},
            {"timestamp": datetime.now() - timedelta(days=3), "value": 0.5},
            {"timestamp": datetime.now() - timedelta(days=2), "value": 0.55},
            {"timestamp": datetime.now() - timedelta(days=1), "value": 0.6}
        ]
        
        # 执行测试
        slope, correlation = self.tracker._calculate_trend_slope(time_series)
        
        # 验证结果 - 应该有正斜率和高相关性
        self.assertGreater(slope, 0)
        self.assertGreater(correlation, 0.9)  # 线性增长应有高相关性
    
    def test_track_preference_evolution(self):
        """测试偏好演变追踪"""
        # 执行测试
        result = self.tracker.track_preference_evolution(self.test_user_id)
        
        # 验证结果
        self.assertIn("status", result)
        self.assertEqual(result["status"], "success")
        self.assertIn("current_preferences", result)
        self.assertIn("shifts", result)
        
        # 验证调用
        self.mock_analyzer.analyze_user_preferences.assert_called_once_with(self.test_user_id)
        self.mock_storage.get_preference_history.assert_called_with(self.test_user_id)
        self.mock_storage.save_preference_evolution.assert_called_once()
    
    def test_get_evolution_summary(self):
        """测试获取偏好演变摘要"""
        # 执行测试
        result = self.tracker.get_evolution_summary(self.test_user_id, 30)
        
        # 验证结果
        self.assertIn("status", result)
        self.assertEqual(result["status"], "success")
        self.assertIn("user_id", result)
        self.assertEqual(result["user_id"], self.test_user_id)
        self.assertIn("time_range", result)
        self.assertIn("overall_stability", result)
        self.assertIn("significant_changes", result)
        
        # 验证调用
        self.mock_storage.get_preference_history.assert_called_with(self.test_user_id)
    
    def test_utility_functions(self):
        """测试工具函数"""
        # 模拟依赖函数
        with patch('src.audience.evolution_tracker.get_evolution_tracker') as mock_get_tracker:
            mock_tracker = MagicMock()
            mock_get_tracker.return_value = mock_tracker
            
            # 测试detect_preference_shift
            detect_preference_shift(self.test_user_id)
            mock_tracker.detect_shift.assert_called_once_with(self.test_user_id)
            
            # 测试track_preference_changes
            track_preference_changes(self.test_user_id)
            mock_tracker.track_preference_evolution.assert_called_once_with(self.test_user_id)
            
            # 测试get_preference_evolution_summary
            get_preference_evolution_summary(self.test_user_id, 60)
            mock_tracker.get_evolution_summary.assert_called_once_with(self.test_user_id, 60)
    
    def _create_test_history(self) -> List[Dict[str, Any]]:
        """创建测试历史数据"""
        history = []
        
        # 创建90天的历史数据
        for i in range(90, 0, -5):  # 每5天一个数据点
            # 生成日期
            date = datetime.now() - timedelta(days=i)
            
            # 随着时间变化的偏好值
            genre_value = 0.5 + (90 - i) * 0.002  # 逐渐增加
            pace_value = 0.6 - (90 - i) * 0.001   # 逐渐减少
            
            # 创建偏好数据
            preferences = {
                "genre": {
                    "favorites": ["动作", "科幻"],
                    "strength_map": {
                        "动作": {"ratio": genre_value},
                        "科幻": {"ratio": 0.3}
                    }
                },
                "pace": {
                    "preferred_pace": "fast" if i % 25 == 0 else "moderate",
                    "engagement_by_pace": {
                        "fast": {"completion_rate": pace_value},
                        "moderate": {"completion_rate": 0.5}
                    }
                },
                "visuals": {
                    "preferred_styles": ["高饱和", "流畅"],
                    "strength_map": {
                        "高饱和": {"ratio": 0.4 + (90 - i) * 0.003},
                        "流畅": {"ratio": 0.3}
                    }
                }
            }
            
            # 添加到历史
            history.append({
                "timestamp": date.isoformat(),
                "preferences": preferences
            })
        
        return history
    
    def _create_test_preferences(self) -> Dict[str, Any]:
        """创建测试当前偏好数据"""
        return {
            "status": "success",
            "user_id": self.test_user_id,
            "genre": {
                "favorites": ["动作", "科幻"],
                "strength_map": {
                    "动作": {"ratio": 0.7, "strength": "strong"},
                    "科幻": {"ratio": 0.3, "strength": "moderate"}
                },
                "confidence": 0.85
            },
            "narrative": {
                "preferred_styles": ["紧凑", "非线性"],
                "strength_map": {
                    "紧凑": {"ratio": 0.6},
                    "非线性": {"ratio": 0.4}
                },
                "confidence": 0.7
            },
            "pace": {
                "preferred_pace": "fast",
                "engagement_by_pace": {
                    "fast": {"completion_rate": 0.8},
                    "moderate": {"completion_rate": 0.6}
                },
                "confidence": 0.9
            },
            "analyzed_at": datetime.now().isoformat()
        }


if __name__ == "__main__":
    unittest.main() 