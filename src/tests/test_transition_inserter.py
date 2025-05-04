"""
VisionAI-ClipsMaster 过渡帧插入器单元测试

此模块包含对过渡帧智能插入功能的全面测试，
确保在各种场景和边界条件下过渡效果处理的正确性。
"""

import unittest
import sys
import os
from typing import Dict, List, Any

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from timecode.transition_inserter import (
    TransitionInserter,
    TransitionType,
    insert_transitions,
    create_transition_frame
)


class TestTransitionInserter(unittest.TestCase):
    """测试过渡帧插入器的基础功能"""
    
    def setUp(self):
        """测试前的准备工作"""
        # 创建测试场景数据
        self.test_scenes = [
            {
                "id": "scene1",
                "start_time": 0.0,
                "end_time": 5.0,
                "duration": 5.0,
                "compression_rate": 0.4,  # 高压缩率，应触发过渡
                "importance": 0.6,
                "tags": ["动作", "快速"]
            },
            {
                "id": "scene2",
                "start_time": 5.0,
                "end_time": 10.0,
                "duration": 5.0,
                "compression_rate": 0.2,  # 低压缩率
                "importance": 0.8,
                "tags": ["对话", "情感"]
            },
            {
                "id": "scene3",
                "start_time": 10.0,
                "end_time": 15.0,
                "duration": 5.0,
                "compression_rate": 0.5,  # 高压缩率，应触发过渡
                "tags": ["转折", "场景变化"]
            }
        ]
        
        # 创建配置了保护信息的场景
        self.protected_scenes = [
            {
                "id": "protected1",
                "start_time": 0.0,
                "end_time": 5.0,
                "duration": 5.0,
                "compression_rate": 0.4,
                "_protection_info": {
                    "level": "HIGH",
                    "strategies": ["NO_TRANSITION", "LOCK"]
                }
            },
            {
                "id": "protected2",
                "start_time": 5.0,
                "end_time": 10.0,
                "duration": 5.0,
                "compression_rate": 0.5,
                "_protection_info": {
                    "level": "HIGH",
                    "strategies": ["NO_TRANSITION"]
                }
            }
        ]
        
        # 创建插入器实例
        self.inserter = TransitionInserter()
    
    def test_initialization(self):
        """测试初始化和配置加载"""
        # 默认配置初始化
        default_inserter = TransitionInserter()
        self.assertEqual(default_inserter.config["compression_threshold"], 0.3)
        
        # 自定义配置初始化
        custom_config = {
            "compression_threshold": 0.5,
            "max_transition_duration": 80,
            "time_unit": "ms"
        }
        custom_inserter = TransitionInserter(custom_config)
        self.assertEqual(custom_inserter.config["compression_threshold"], 0.5)
        self.assertEqual(custom_inserter.config["max_transition_duration"], 80)
        self.assertEqual(custom_inserter.config["time_unit"], "ms")
    
    def test_insert_transitions(self):
        """测试过渡帧插入主功能"""
        # 插入过渡帧
        processed_scenes = self.inserter.insert_transitions(self.test_scenes)
        
        # 应该有5个场景（原始3个场景 + 2个过渡）
        self.assertEqual(len(processed_scenes), 5)
        
        # 检查过渡帧类型
        transitions = [scene for scene in processed_scenes if scene.get("type") == "transition"]
        self.assertEqual(len(transitions), 2)
        
        # 验证第一个过渡帧
        first_transition = transitions[0]
        self.assertEqual(first_transition["source_scenes"], ["scene1", "scene2"])
        self.assertTrue("transition_type" in first_transition)
        self.assertTrue("transition_duration_ms" in first_transition)
        
        # 验证场景时间调整
        # 原始场景的结束时间应该调整为考虑过渡效果
        adjusted_scene1 = next(s for s in processed_scenes if s["id"] == "scene1")
        adjusted_scene2 = next(s for s in processed_scenes if s["id"] == "scene2")
        self.assertLess(adjusted_scene1["end_time"], 5.0)
        self.assertLess(adjusted_scene2["start_time"], 5.0)
    
    def test_respect_protection(self):
        """测试尊重场景保护设置"""
        # 默认配置（respect_protection=True）
        processed_scenes = self.inserter.insert_transitions(self.protected_scenes)
        
        # 由于两个场景都有高级别保护，不应插入过渡帧
        self.assertEqual(len(processed_scenes), 2)
        
        # 获取默认配置并修改需要的部分
        default_config = self.inserter._default_config()
        default_config["respect_protection"] = False
        
        # 创建自定义配置的插入器
        custom_inserter = TransitionInserter(default_config)
        processed_scenes = custom_inserter.insert_transitions(self.protected_scenes)
        
        # 应该有3个场景（原始2个场景 + 1个过渡）
        self.assertEqual(len(processed_scenes), 3)
    
    def test_transition_type_selection(self):
        """测试过渡类型选择逻辑"""
        # 动作场景，应选择动态过渡
        action_scene = {"tags": ["动作", "快速"]}
        next_scene = {"tags": ["普通"]}
        transition_type = self.inserter._select_transition_type(action_scene, next_scene)
        self.assertEqual(transition_type, TransitionType.DYNAMIC)
        
        # 转折场景，应选择滑动转场
        transition_scene = {"tags": ["转折", "场景变化"]}
        next_scene = {"tags": ["普通"]}
        transition_type = self.inserter._select_transition_type(transition_scene, next_scene)
        self.assertEqual(transition_type, TransitionType.SLIDE)
        
        # 情感场景，应选择淡入淡出
        emotion_scene = {"tags": ["情感", "氛围"]}
        next_scene = {"tags": ["普通"]}
        transition_type = self.inserter._select_transition_type(emotion_scene, next_scene)
        self.assertEqual(transition_type, TransitionType.FADE)
        
        # 普通场景，应选择交叉溶解
        normal_scene = {"tags": ["普通"]}
        next_scene = {"tags": ["普通"]}
        transition_type = self.inserter._select_transition_type(normal_scene, next_scene)
        self.assertEqual(transition_type, TransitionType.CROSSFADE)
    
    def test_transition_duration_calculation(self):
        """测试过渡持续时间计算逻辑"""
        # 高重要性场景，应有较短的过渡时间
        important_scene = {"importance": 0.9, "compression_rate": 0.3}
        next_scene = {"importance": 0.8, "compression_rate": 0.2}
        duration = self.inserter._calculate_transition_duration(
            important_scene, next_scene, TransitionType.CROSSFADE
        )
        
        # 标准过渡时间为50ms，但高重要性应该减少时间
        self.assertLess(duration, 50)
        
        # 高压缩率场景，应有较长的过渡时间
        compressed_scene = {"importance": 0.5, "compression_rate": 0.8}
        next_scene = {"importance": 0.5, "compression_rate": 0.7}
        duration = self.inserter._calculate_transition_duration(
            compressed_scene, next_scene, TransitionType.CROSSFADE
        )
        
        # 标准过渡时间为50ms，但高压缩率应该增加时间
        self.assertGreater(duration, 50)
    
    def test_create_transition_frame(self):
        """测试过渡帧创建功能"""
        curr_scene = {
            "id": "scene1", 
            "start_time": 0.0,
            "end_time": 5.0,
            "duration": 5.0
        }
        next_scene = {
            "id": "scene2", 
            "start_time": 5.0,
            "end_time": 10.0,
            "duration": 5.0
        }
        
        # 创建过渡帧
        transition_frame = self.inserter._create_transition_frame(
            curr_scene, next_scene, TransitionType.CROSSFADE, 50
        )
        
        # 验证过渡帧属性
        self.assertEqual(transition_frame["id"], "transition_scene1_scene2")
        self.assertEqual(transition_frame["transition_type"], TransitionType.CROSSFADE)
        self.assertEqual(transition_frame["transition_duration_ms"], 50)
        self.assertEqual(transition_frame["source_scenes"], ["scene1", "scene2"])
        self.assertTrue(transition_frame["_meta"]["auto_generated"])
    
    def test_helper_functions(self):
        """测试辅助函数"""
        # 测试insert_transitions辅助函数
        processed_scenes = insert_transitions(
            self.test_scenes,
            compression_threshold=0.35,
            config={"max_transition_duration": 70}
        )
        
        # 应该有5个场景（原始3个场景 + 2个过渡）
        self.assertEqual(len(processed_scenes), 5)
        
        # 测试create_transition_frame辅助函数
        curr_scene = {"id": "scene1", "start_time": 0.0, "end_time": 5.0}
        next_scene = {"id": "scene2", "start_time": 5.0, "end_time": 10.0}
        
        transition = create_transition_frame(
            curr_scene, next_scene, TransitionType.SLIDE, 80
        )
        
        self.assertEqual(transition["transition_type"], TransitionType.SLIDE)
        self.assertEqual(transition["transition_duration_ms"], 80)
    
    def test_time_unit_conversion(self):
        """测试时间单位转换"""
        # 为毫秒测试创建适配的场景数据
        ms_scenes = [
            {
                "id": "scene1",
                "start_time": 0,
                "end_time": 5000,
                "duration": 5000,
                "compression_rate": 0.4
            },
            {
                "id": "scene2",
                "start_time": 5000,
                "end_time": 10000,
                "duration": 5000,
                "compression_rate": 0.2
            }
        ]
        
        # 使用辅助函数而不是自定义插入器
        processed_scenes = insert_transitions(
            ms_scenes,
            compression_threshold=0.3,
            config={"time_unit": "ms"}
        )
        
        # 应该有3个场景（原始2个场景 + 1个过渡）
        self.assertEqual(len(processed_scenes), 3)
        
        # 验证时间单位正确处理
        transition = next(s for s in processed_scenes if s.get("type") == "transition")
        # 检查过渡持续时间是否在合理范围内（毫秒）
        self.assertTrue(0 < transition["transition_duration_ms"] <= 100)
    
    def test_empty_scene_list(self):
        """测试空场景列表处理"""
        # 空列表
        empty_result = self.inserter.insert_transitions([])
        self.assertEqual(empty_result, [])
        
        # 只有一个场景的列表
        single_scene = [{"id": "scene1", "start_time": 0.0, "end_time": 5.0}]
        single_result = self.inserter.insert_transitions(single_scene)
        self.assertEqual(single_result, single_scene)


if __name__ == '__main__':
    unittest.main() 