"""
关键情节锚点检测器测试
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock
import json
import random
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.narrative.anchor_detector import AnchorDetector, detect_anchors, get_top_anchors
from src.narrative.anchor_types import AnchorType, AnchorInfo


class TestAnchorDetector(unittest.TestCase):
    """测试锚点检测器"""
    
    def setUp(self):
        """测试准备"""
        # 创建测试数据
        self.test_scenes = self._create_test_scenes()
        
        # 初始化检测器
        self.detector = AnchorDetector()
    
    def _create_test_scenes(self, num_scenes=10):
        """创建测试场景数据"""
        scenes = []
        
        # 基础情感曲线
        emotions = [0.2, 0.3, 0.1, 0.0, -0.3, -0.5, -0.2, 0.4, 0.8, 0.5]
        
        # 角色
        characters = ["张三", "李四", "王五"]
        
        # 场景类型和文本
        scene_types = ["opening", "exposition", "rising", "conflict", "climax", "falling", "resolution"]
        
        # 生成场景
        for i in range(num_scenes):
            # 选择场景类型
            scene_type = scene_types[min(i, len(scene_types) - 1)]
            
            # 生成文本
            if scene_type == "conflict":
                text = f"{characters[0]}和{characters[1]}因为误会发生了激烈的争吵。"
            elif scene_type == "climax":
                text = f"真相揭露的那一刻，{characters[0]}终于明白了一切。"
            else:
                text = f"{characters[0]}在思考接下来的行动方案。"
            
            # 添加特定关键词
            if i == 3:  # 添加悬念
                text += " 这个谜题让所有人都困惑不已。"
            elif i == 7:  # 添加解答
                text += " 原来这就是事情的真相。"
            
            # 选择角色
            if i in [1, 3, 5, 8]:
                scene_chars = characters[:2]  # 两个角色
            elif i in [2, 6]:
                scene_chars = characters  # 三个角色
            else:
                scene_chars = [characters[0]]  # 一个角色
            
            # 创建场景
            scene = {
                "id": f"scene_{i+1}",
                "type": scene_type,
                "text": text,
                "emotion_score": emotions[i] if i < len(emotions) else random.uniform(-0.5, 0.8),
                "characters": scene_chars,
                "duration": random.uniform(3.0, 8.0),
                "start_time": i * 5.0,
                "end_time": (i + 1) * 5.0
            }
            
            scenes.append(scene)
        
        return scenes
    
    def test_initialization(self):
        """测试初始化"""
        self.assertIsNotNone(self.detector)
        self.assertIsNotNone(self.detector.config)
        self.assertEqual(len(self.detector.anchors), 0)
    
    def test_detect_emotion_anchors(self):
        """测试情感锚点检测"""
        # 调用私有方法检测情感锚点
        emotion_anchors = self.detector._detect_emotion_anchors(self.test_scenes)
        
        # 验证结果
        self.assertIsInstance(emotion_anchors, list)
        
        # 应该至少有一个情感锚点
        self.assertGreater(len(emotion_anchors), 0)
        
        # 验证锚点类型
        for anchor in emotion_anchors:
            self.assertEqual(anchor.type, AnchorType.EMOTION)
            self.assertIsInstance(anchor.position, float)
            self.assertGreaterEqual(anchor.position, 0.0)
            self.assertLessEqual(anchor.position, 1.0)
    
    def test_detect_character_anchors(self):
        """测试人物锚点检测"""
        # 调用私有方法检测人物锚点
        character_anchors = self.detector._detect_character_anchors(self.test_scenes)
        
        # 验证结果
        self.assertIsInstance(character_anchors, list)
        
        # 验证锚点类型
        for anchor in character_anchors:
            self.assertEqual(anchor.type, AnchorType.CHARACTER)
            self.assertIsInstance(anchor.position, float)
            self.assertGreaterEqual(anchor.position, 0.0)
            self.assertLessEqual(anchor.position, 1.0)
    
    def test_detect_suspense_anchors(self):
        """测试悬念锚点检测"""
        # 调用私有方法检测悬念锚点
        suspense_anchors = self.detector._detect_suspense_anchors(self.test_scenes)
        
        # 验证结果
        self.assertIsInstance(suspense_anchors, list)
        
        # 验证锚点类型
        for anchor in suspense_anchors:
            self.assertEqual(anchor.type, AnchorType.SUSPENSE)
            self.assertIsInstance(anchor.position, float)
            self.assertGreaterEqual(anchor.position, 0.0)
            self.assertLessEqual(anchor.position, 1.0)
    
    def test_find_anchors(self):
        """测试查找所有锚点"""
        # 查找所有锚点
        anchors = self.detector.find_anchors(self.test_scenes)
        
        # 验证结果
        self.assertIsInstance(anchors, list)
        self.assertGreater(len(anchors), 0)
        
        # 验证锚点类型
        anchor_types = set(anchor.type for anchor in anchors)
        self.assertIn(AnchorType.EMOTION, anchor_types)
        
        # 验证按位置排序
        positions = [anchor.position for anchor in anchors]
        self.assertEqual(positions, sorted(positions))
    
    def test_merge_nearby_anchors(self):
        """测试合并相近锚点"""
        # 创建两个相近的锚点
        anchors = [
            AnchorInfo(id="test1", type=AnchorType.EMOTION, position=0.5, confidence=0.8),
            AnchorInfo(id="test2", type=AnchorType.EMOTION, position=0.51, confidence=0.7)
        ]
        
        # 调用合并函数
        self.detector.config["merge_strategy"]["proximity_threshold"] = 0.05
        merged = self.detector._merge_nearby_anchors(anchors)
        
        # 验证结果
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0].position, 0.5)
    
    def test_get_top_anchors(self):
        """测试获取最重要的锚点"""
        # 创建一些锚点
        anchors = [
            AnchorInfo(id="test1", type=AnchorType.EMOTION, position=0.2, importance=0.5),
            AnchorInfo(id="test2", type=AnchorType.CHARACTER, position=0.4, importance=0.8),
            AnchorInfo(id="test3", type=AnchorType.SUSPENSE, position=0.6, importance=0.3),
            AnchorInfo(id="test4", type=AnchorType.EMOTION, position=0.8, importance=0.9)
        ]
        
        # 获取前2个重要的锚点
        top_anchors = get_top_anchors(anchors, 2)
        
        # 验证结果
        self.assertEqual(len(top_anchors), 2)
        self.assertEqual(top_anchors[0].id, "test4")  # 最重要
        self.assertEqual(top_anchors[1].id, "test2")  # 第二重要
    
    def test_api_functions(self):
        """测试API函数"""
        # 测试便捷检测函数
        anchors = detect_anchors(self.test_scenes)
        self.assertIsInstance(anchors, list)
        self.assertGreater(len(anchors), 0)
        
        # 测试获取顶级锚点
        if anchors:
            top_anchors = get_top_anchors(anchors, 3)
            self.assertLessEqual(len(top_anchors), 3)
    
    def tearDown(self):
        """测试清理"""
        # 清理测试生成的缓存文件
        cache_dir = self.detector.config["caching"]["cache_dir"]
        if os.path.exists(cache_dir):
            for file_name in os.listdir(cache_dir):
                file_path = os.path.join(cache_dir, file_name)
                if os.path.isfile(file_path) and file_name.endswith(".json"):
                    try:
                        os.remove(file_path)
                    except:
                        pass


if __name__ == "__main__":
    unittest.main() 