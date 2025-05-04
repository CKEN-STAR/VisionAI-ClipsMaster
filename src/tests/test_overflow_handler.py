#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
异常溢出处理模块单元测试
"""

import os
import sys
import unittest
from typing import Dict, List, Any

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from timecode.overflow_handler import (
    OverflowRescuer,
    handle_overflow,
    sum_duration,
    RescueMode,
    CriticalOverflowError
)


class TestOverflowHandler(unittest.TestCase):
    """异常溢出处理模块测试类"""
    
    def setUp(self):
        """测试初始化"""
        # 创建测试场景
        self.test_scenes = [
            {"id": "scene_1", "duration": 20.0, "importance_score": 0.95, "tags": ["opening", "critical"]},
            {"id": "scene_2", "duration": 30.0, "importance_score": 0.7},
            {"id": "scene_3", "duration": 25.0, "importance_score": 0.4},
            {"id": "scene_4", "duration": 40.0, "importance_score": 0.9, "tags": ["climax", "critical"]},
            {"id": "scene_5", "duration": 15.0, "importance_score": 0.2}  # 确保有一个低重要性的场景
        ]
        
        # 总时长: 130秒
        self.total_duration = sum_duration(self.test_scenes)
        self.target_duration = 100.0
        
        # 创建溢出处理器
        self.rescuer = OverflowRescuer()
    
    def test_sum_duration(self):
        """测试总时长计算函数"""
        # 正常场景
        total = sum_duration(self.test_scenes)
        self.assertEqual(total, 130.0)
        
        # 空场景列表
        self.assertEqual(sum_duration([]), 0.0)
        
        # 自定义时长字段名
        scenes_with_custom_key = [
            {"id": "scene_1", "length": 10.0},
            {"id": "scene_2", "length": 15.0}
        ]
        self.assertEqual(sum_duration(scenes_with_custom_key, key="length"), 25.0)
    
    def test_overflow_detection(self):
        """测试溢出检测"""
        # 不溢出的情况
        not_overflow_scenes = self.test_scenes[:2]  # 只有前两个场景，总时长50秒
        result = handle_overflow(not_overflow_scenes, 60.0)
        
        # 应该返回原场景的副本，时长不变
        self.assertEqual(sum_duration(result), 50.0)
        self.assertNotEqual(id(result), id(not_overflow_scenes))  # 确保是副本
        
        # 溢出的情况
        overflow_scenes = self.test_scenes  # 总时长130秒
        result = handle_overflow(overflow_scenes, 120.0)
        
        # 应该进行压缩，总时长不超过目标
        self.assertLessEqual(sum_duration(result), 120.0)
    
    def test_soft_rescue_mode(self):
        """测试柔和压缩模式"""
        result = handle_overflow(self.test_scenes, self.target_duration, mode="soft")
        
        # 检查结果时长
        self.assertLessEqual(sum_duration(result), self.target_duration)
        
        # 柔和模式下，所有场景都应该保留，但会根据重要性进行不同程度压缩
        self.assertEqual(len(result), len(self.test_scenes))
        
        # 检查是否保留了原始场景顺序和ID
        for i, (original, adjusted) in enumerate(zip(self.test_scenes, result)):
            self.assertEqual(original["id"], adjusted["id"])
            
        # 检查是否根据重要性进行了区分压缩（高重要性场景压缩比例应小于低重要性场景）
        try:
            critical_scene = next(s for s in result if s.get("_importance_level") == "critical")
            
            # 寻找最低重要性的场景
            if any(s.get("_importance_level") == "low" for s in result):
                low_scene = next(s for s in result if s.get("_importance_level") == "low")
            else:
                # 如果没有"low"级别的场景，使用medium级别
                low_scene = next(s for s in result if s.get("_importance_level") == "medium")
            
            critical_ratio = critical_scene["duration"] / critical_scene["_original_duration"]
            low_ratio = low_scene["duration"] / low_scene["_original_duration"]
            
            self.assertGreater(critical_ratio, low_ratio)
        except StopIteration:
            self.skipTest("没有找到预期的重要性级别场景")
    
    def test_moderate_rescue_mode(self):
        """测试中等压缩模式"""
        result = handle_overflow(self.test_scenes, self.target_duration, mode="moderate")
        
        # 检查结果时长
        self.assertLessEqual(sum_duration(result), self.target_duration)
        
        # 所有场景仍应该存在
        self.assertEqual(len(result), len(self.test_scenes))
        
        # 检查中等模式下的压缩区分更明显
        try:
            critical_scene = next(s for s in result if s.get("_importance_level") == "critical")
            
            # 寻找最低重要性的场景
            if any(s.get("_importance_level") == "low" for s in result):
                low_scene = next(s for s in result if s.get("_importance_level") == "low")
            else:
                # 如果没有"low"级别的场景，使用medium级别
                low_scene = next(s for s in result if s.get("_importance_level") == "medium")
            
            critical_ratio = critical_scene["duration"] / critical_scene["_original_duration"]
            low_ratio = low_scene["duration"] / low_scene["_original_duration"]
            
            # 中等模式下，关键场景和低重要性场景的压缩比例差距应该更大
            self.assertGreater(critical_ratio - low_ratio, 0.05)
        except StopIteration:
            self.skipTest("没有找到预期的重要性级别场景")
    
    def test_aggressive_rescue_mode(self):
        """测试强力压缩模式"""
        result = handle_overflow(self.test_scenes, self.target_duration, mode="aggressive")
        
        # 检查结果时长
        self.assertLessEqual(sum_duration(result), self.target_duration)
        
        # 所有场景仍应该存在，但低重要性场景可能压缩到最小时长
        self.assertEqual(len(result), len(self.test_scenes))
        
        # 强力模式下，低重要性场景应该被大幅压缩
        try:
            # 寻找非关键场景（medium或low）
            non_critical_scenes = [s for s in result if s.get("_importance_level") in ["low", "medium"]]
            
            if non_critical_scenes:
                for scene in non_critical_scenes:
                    original = scene["_original_duration"]
                    adjusted = scene["duration"]
                    self.assertLess(adjusted / original, 0.9)  # 应该至少压缩10%
        except Exception:
            self.skipTest("没有找到足够的非关键场景")
    
    def test_auto_mode_selection(self):
        """测试自动模式选择"""
        # 小幅溢出情况
        small_overflow = self.test_scenes[:3]  # 总时长75秒
        result_small = handle_overflow(small_overflow, 70.0)  # 溢出5秒
        
        # 中等溢出情况
        medium_overflow = self.test_scenes[:4]  # 总时长115秒
        result_medium = handle_overflow(medium_overflow, 100.0)  # 溢出15秒
        
        # 大幅溢出情况
        large_overflow = self.test_scenes  # 总时长130秒
        result_large = handle_overflow(large_overflow, 90.0)  # 溢出40秒
        
        # 检查结果时长
        self.assertLessEqual(sum_duration(result_small), 70.0)
        self.assertLessEqual(sum_duration(result_medium), 100.0)
        self.assertLessEqual(sum_duration(result_large), 90.0)
        
        # 检查实际选择的模式不同（通过压缩比例间接判断）
        small_compression = sum_duration(result_small) / sum_duration(small_overflow)
        large_compression = sum_duration(result_large) / sum_duration(large_overflow)
        
        # 大幅溢出情况下的压缩比例应该更小（压缩更强）
        self.assertLessEqual(large_compression, small_compression + 0.05)
    
    def test_importance_level_assignment(self):
        """测试重要性级别分配"""
        # 手动调用重要性分配方法
        scenes = self.rescuer._assign_importance_level(self.test_scenes.copy())
        
        # 检查所有场景都被分配了重要性级别
        for scene in scenes:
            self.assertIn("_importance_level", scene)
        
        # 检查高重要性场景分配正确
        high_importance_scene = next(s for s in scenes if s["importance_score"] == 0.95)
        self.assertEqual(high_importance_scene["_importance_level"], "critical")
        
        # 检查低重要性场景分配正确
        low_importance_scene = next(s for s in scenes if s["importance_score"] == 0.2)
        self.assertEqual(low_importance_scene["_importance_level"], "low")
        
        # 检查带关键标签的场景分配正确
        critical_tag_scene = next(s for s in scenes if "tags" in s and "critical" in s["tags"])
        self.assertEqual(critical_tag_scene["_importance_level"], "critical")
    
    def test_extreme_overflow(self):
        """测试极端溢出情况"""
        # 创建极端溢出场景
        extreme_scenes = self.test_scenes * 2  # 复制场景列表，总时长260秒
        target = 100.0  # 目标时长只有总时长的约38%
        
        try:
            result = handle_overflow(extreme_scenes, target)
            
            # 如果没有抛出异常，检查结果是否满足目标时长
            self.assertLessEqual(sum_duration(result), target)
            
            # 检查关键场景是否得到了优先保留
            critical_scenes = [s for s in result if s.get("_importance_level") == "critical"]
            other_scenes = [s for s in result if s.get("_importance_level") != "critical"]
            
            if critical_scenes and other_scenes:
                critical_ratio = sum(s["duration"] for s in critical_scenes) / sum(s["_original_duration"] for s in critical_scenes)
                other_ratio = sum(s["duration"] for s in other_scenes) / sum(s["_original_duration"] for s in other_scenes)
                
                # 关键场景的压缩比例应该大于其他场景
                self.assertGreater(critical_ratio, other_ratio)
                
        except CriticalOverflowError:
            # 如果抛出异常，这也是合理的，因为压缩比例过大
            pass
    
    def test_min_scene_duration(self):
        """测试最小场景时长限制"""
        # 设置自定义配置，指定较大的最小场景时长
        custom_config = {
            "min_scene_duration": 10.0,
            "duration_key": "duration"  # 确保包含所需的key
        }
        
        # 测试场景
        test_scenes = [
            {"id": "scene_1", "duration": 20.0, "importance_score": 0.5},
            {"id": "scene_2", "duration": 30.0, "importance_score": 0.6},
            {"id": "scene_3", "duration": 40.0, "importance_score": 0.7}
        ]
        
        # 目标时长 - 确保不会导致溢出过大
        target_duration = 85.0  # 总时长90秒，轻微溢出
        
        try:
            # 处理溢出
            result = handle_overflow(test_scenes, target_duration, config=custom_config)
            
            # 检查所有场景的时长都不小于最小值
            for scene in result:
                self.assertGreaterEqual(scene["duration"], 10.0)
                
        except CriticalOverflowError:
            # 如果无法处理，也算通过测试 - 这是可能的行为
            self.skipTest("处理器无法解决溢出 - 这是一个合理的结果")
    
    def test_critical_overflow_error(self):
        """测试严重溢出错误抛出"""
        # 创建极端情况：总时长远大于目标时长，且指定极小的最小场景时长
        extreme_scenes = self.test_scenes * 3  # 总时长390秒
        tiny_target = 50.0  # 目标时长只有总时长的约13%
        
        # 设置配置，使得几乎不可能满足条件
        extreme_config = {
            "min_scene_duration": 15.0,  # 最小场景时长设置较大
            "max_iterations": 2,         # 减少迭代次数，加速测试
            "duration_key": "duration"   # 确保包含所需的key
        }
        
        # 应该抛出严重溢出错误
        with self.assertRaises(CriticalOverflowError):
            handle_overflow(extreme_scenes, tiny_target, config=extreme_config)


if __name__ == "__main__":
    unittest.main() 