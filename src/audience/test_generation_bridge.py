#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
代际差异桥接器测试模块

测试代际差异桥接器的核心功能，包括世代检测、代际转换和文化参考适配。
"""

import unittest
from unittest.mock import MagicMock, patch
import json
import os
import sys
from pathlib import Path

# 修改Python路径以导入项目模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.audience.generation_gap import (
    GenerationBridge, get_generation_bridge,
    bridge_gap, detect_content_generation,
    insert_cultural_elements
)

class TestGenerationBridge(unittest.TestCase):
    """代际差异桥接器测试类"""
    
    def setUp(self):
        """测试准备工作"""
        # 创建被测对象
        with patch('src.audience.generation_gap.get_logger', return_value=MagicMock()):
            with patch('src.audience.generation_gap.CultureAdapter', return_value=MagicMock()):
                with patch('src.audience.generation_gap.TextProcessor', return_value=MagicMock()):
                    self.bridge = GenerationBridge()
        
        # 测试内容数据 - Z世代风格
        self.z_gen_content = {
            "title": "二次元动漫角色大盘点",
            "description": "这些角色简直绝绝子，太可了，我直接笑死！",
            "scenes": [
                {
                    "id": "scene_1",
                    "description": "玩梗时刻，满屏yyds",
                    "elements": [
                        {"type": "text", "content": "这个角色也太A了，破防了"},
                        {"type": "image", "source": "meme.png"}
                    ]
                },
                {
                    "id": "scene_2",
                    "description": "开局整片化，原神启动",
                    "elements": [
                        {"type": "video", "content": "原神游戏中最嘎嘎猛的时刻"}
                    ]
                }
            ],
            "dialogues": [
                {"speaker": "narrator", "text": "这些梗真是太香了，yyds！"},
                {"speaker": "presenter", "text": "直接一整个无语子，破防了家人们！"}
            ]
        }
        
        # 测试内容数据 - 80后风格
        self.gen80_content = {
            "title": "怀旧经典动画角色回顾",
            "description": "这些角色陪伴了我们的童年，满满的回忆",
            "scenes": [
                {
                    "id": "scene_1",
                    "description": "经典港台动画，长篇叙事",
                    "elements": [
                        {"type": "text", "content": "小时候最喜欢看的卡通形象"},
                        {"type": "image", "source": "classic.png"}
                    ]
                },
                {
                    "id": "scene_2",
                    "description": "青春记忆，经典款角色",
                    "elements": [
                        {"type": "video", "content": "80年代最流行的动画角色"}
                    ]
                }
            ],
            "dialogues": [
                {"speaker": "narrator", "text": "这些经典角色真是满满的回忆啊"},
                {"speaker": "presenter", "text": "那个年代的动画真是越看越有味道"}
            ]
        }
        
        # 通用内容（无明显世代特征）
        self.generic_content = {
            "title": "动画角色介绍",
            "description": "介绍几个知名动画角色",
            "scenes": [
                {
                    "id": "scene_1",
                    "description": "角色登场",
                    "elements": [
                        {"type": "text", "content": "这个角色很受欢迎"},
                        {"type": "image", "source": "character.png"}
                    ]
                }
            ],
            "dialogues": [
                {"speaker": "narrator", "text": "这些角色各有特色"}
            ]
        }
    
    def test_initialization(self):
        """测试初始化"""
        self.assertIsNotNone(self.bridge)
        self.assertIn("Z世代", self.bridge.REFERENCE_POINTS)
        self.assertIn("80后", self.bridge.REFERENCE_POINTS)
        self.assertIn(("Z世代", "80后"), self.bridge.generation_maps)
    
    def test_detect_generation(self):
        """测试世代检测"""
        # 检测Z世代内容
        detected_gen = self.bridge._detect_generation(self.z_gen_content)
        self.assertEqual(detected_gen, "Z世代")
        
        # 检测80后内容
        detected_gen = self.bridge._detect_generation(self.gen80_content)
        self.assertEqual(detected_gen, "80后")
        
        # 检测通用内容（应返回一个默认世代）
        detected_gen = self.bridge._detect_generation(self.generic_content)
        self.assertIn(detected_gen, self.bridge.REFERENCE_POINTS.keys())
    
    def test_extract_text_content(self):
        """测试文本内容提取"""
        # 从Z世代内容提取文本
        text = self.bridge._extract_text_content(self.z_gen_content)
        self.assertIn("二次元", text)
        self.assertIn("绝绝子", text)
        self.assertIn("玩梗", text)
        self.assertIn("yyds", text)
        
        # 验证是否包含所有场景和对话文本
        self.assertIn("整片化", text)
        self.assertIn("破防了家人们", text)
    
    def test_transform_text(self):
        """测试文本转换"""
        # Z世代到80后的转换
        z_text = "这个角色绝绝子，yyds，太可了！"
        transformed = self.bridge._transform_text(
            z_text, 
            self.bridge.generation_maps[("Z世代", "80后")],
            "Z世代",
            "80后"
        )
        
        # 验证关键词转换
        self.assertNotIn("绝绝子", transformed)
        self.assertNotIn("yyds", transformed)
        self.assertIn("太厉害了", transformed) # 或其他对应转换词
        
        # 80后到Z世代的转换
        eighties_text = "这些经典角色充满港台风格，满满的童年回忆"
        transformed = self.bridge._transform_text(
            eighties_text, 
            self.bridge.generation_maps[("80后", "Z世代")],
            "80后",
            "Z世代"
        )
        
        # 验证风格应用
        self.assertNotEqual(eighties_text, transformed)
    
    def test_bridge_gap_z_to_80(self):
        """测试代际桥接 - Z世代到80后"""
        # 模拟_detect_generation方法返回"Z世代"
        with patch.object(self.bridge, '_detect_generation', return_value="Z世代"):
            # 模拟_transform_to_generation方法
            with patch.object(self.bridge, '_transform_to_generation') as mock_transform:
                mock_transform.return_value = {"transformed": True}
                
                # 执行代际桥接
                result = self.bridge.bridge_gap(self.z_gen_content, "80后")
                
                # 验证调用
                mock_transform.assert_called_once()
                # 验证传递的参数
                args, kwargs = mock_transform.call_args
                self.assertEqual(args[1], "Z世代")  # 源世代
                self.assertEqual(args[2], "80后")   # 目标世代
    
    def test_bridge_gap_same_generation(self):
        """测试相同世代间的桥接"""
        # 模拟_detect_generation方法返回"Z世代"
        with patch.object(self.bridge, '_detect_generation', return_value="Z世代"):
            # 执行相同世代的桥接
            result = self.bridge.bridge_gap(self.z_gen_content, "Z世代")
            
            # 应返回原内容的副本，不做转换
            self.assertEqual(result["title"], self.z_gen_content["title"])
            self.assertEqual(result["description"], self.z_gen_content["description"])
    
    def test_transform_to_generation(self):
        """测试内容世代转换"""
        # 模拟_transform_text方法
        with patch.object(self.bridge, '_transform_text') as mock_transform:
            mock_transform.return_value = "transformed text"
            
            # 执行世代转换
            result = self.bridge._transform_to_generation(
                self.z_gen_content, "Z世代", "80后"
            )
            
            # 验证是否转换了标题和描述
            self.assertTrue(mock_transform.called)
            
            # 验证是否添加了转换标记
            self.assertIn("generation_adaptation", result)
            self.assertEqual(result["generation_adaptation"]["source_generation"], "Z世代")
            self.assertEqual(result["generation_adaptation"]["target_generation"], "80后")
    
    def test_insert_cultural_elements(self):
        """测试文化元素插入"""
        # 测试文化元素列表
        cultural_refs = ["二次元", "鬼畜", "yyds"]
        
        # 执行文化元素插入
        result = insert_cultural_elements(self.generic_content, cultural_refs)
        
        # 至少应有一个文化元素被插入
        text_content = self.bridge._extract_text_content(result)
        cultural_inserted = any(ref in text_content for ref in cultural_refs)
        self.assertTrue(cultural_inserted)
    
    def test_apply_generation_styles(self):
        """测试世代风格应用"""
        # 测试Z世代风格
        text = "这是一个普通的句子"
        z_styled = self.bridge._apply_z_generation_style(text)
        self.assertNotEqual(text, z_styled)
        
        # 测试80后风格
        eighties_styled = self.bridge._apply_80s_style(text)
        self.assertNotEqual(text, eighties_styled)
        self.assertNotEqual(z_styled, eighties_styled)
        
        # 测试90后风格
        nineties_styled = self.bridge._apply_90s_style(text)
        self.assertNotEqual(text, nineties_styled)
        self.assertNotEqual(z_styled, nineties_styled)
    
    def test_convenience_functions(self):
        """测试便捷函数"""
        # 使用单例模式测试
        with patch('src.audience.generation_gap._generation_bridge', self.bridge):
            # 测试获取单例实例
            bridge_instance = get_generation_bridge()
            self.assertIs(bridge_instance, self.bridge)
            
            # 测试桥接便捷函数
            with patch.object(self.bridge, 'bridge_gap') as mock_bridge:
                bridge_gap(self.z_gen_content, "80后")
                mock_bridge.assert_called_once_with(self.z_gen_content, "80后")
            
            # 测试世代检测便捷函数
            with patch.object(self.bridge, '_detect_generation') as mock_detect:
                detect_content_generation(self.z_gen_content)
                mock_detect.assert_called_once_with(self.z_gen_content)


if __name__ == "__main__":
    unittest.main() 