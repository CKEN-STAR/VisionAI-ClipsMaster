#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
知识图谱构建器测试模块

测试知识图谱的构建、分析和可视化功能
"""

import unittest
import tempfile
import os
import json
from pathlib import Path
from datetime import timedelta

from src.knowledge.graph_builder import DramaKnowledgeGraph, build_knowledge_graph
from src.parsers.subtitle_parser import Subtitle, SubtitleDocument

class MockSubtitle:
    """测试用字幕对象"""
    def __init__(self, index, start_time, end_time, content):
        self.index = index
        self.start_time = timedelta(seconds=start_time)
        self.end_time = timedelta(seconds=end_time)
        self.content = content
    
    def to_dict(self):
        return {
            "index": self.index,
            "start_time": self.start_time.total_seconds(),
            "end_time": self.end_time.total_seconds(),
            "duration": (self.end_time - self.start_time).total_seconds(),
            "content": self.content
        }

class TestKnowledgeGraph(unittest.TestCase):
    """知识图谱测试用例"""
    
    def setUp(self):
        """准备测试数据"""
        # 模拟短剧字幕数据
        self.test_subtitles = [
            MockSubtitle(1, 0, 3, "小明：今天天气真好。").to_dict(),
            MockSubtitle(2, 4, 7, "小红：是啊，我们去公园吧。").to_dict(),
            MockSubtitle(3, 8, 12, "小明：好的，我们叫上小刚一起去。").to_dict(),
            MockSubtitle(4, 13, 16, "小红：我和小刚昨天吵架了，我不想见他。").to_dict(),
            MockSubtitle(5, 17, 20, "小明：别这样，大家都是好朋友。").to_dict(),
            MockSubtitle(6, 21, 24, "小刚：嘿，你们在聊什么？").to_dict(),
            MockSubtitle(7, 25, 28, "小明：我们准备去公园，一起吗？").to_dict(),
            MockSubtitle(8, 29, 33, "小刚：当然！小红，昨天的事我很抱歉。").to_dict(),
            MockSubtitle(9, 34, 37, "小红：没关系，我也有错。").to_dict(),
            MockSubtitle(10, 38, 41, "三人一起去了公园，度过了愉快的一天。").to_dict(),
        ]
        
        # 预期的角色
        self.expected_characters = {"小明", "小红", "小刚"}
        
        # 预期的地点
        self.expected_locations = {"公园"}
        
        # 预期的关系
        self.expected_relationships = [
            ("小明", "小红"), 
            ("小明", "小刚"), 
            ("小红", "小刚")
        ]
    
    def test_build_knowledge_graph(self):
        """测试知识图谱构建"""
        # 构建知识图谱
        kg = build_knowledge_graph(self.test_subtitles, "zh")
        
        # 检查基本属性
        self.assertTrue(kg.is_built)
        self.assertGreater(len(kg.graph.nodes()), 0)
        self.assertGreater(len(kg.graph.edges()), 0)
        
        # 检查是否识别了预期的角色
        for character in self.expected_characters:
            self.assertIn(character, kg.characters)
        
        # 检查是否识别了预期的地点
        for location in self.expected_locations:
            self.assertIn(location, kg.locations)
        
        # 检查角色重要性
        importance = kg.get_character_importance()
        self.assertGreater(len(importance), 0)
        
        # 检查是否能提取关键事件
        key_events = kg.get_key_events(top_k=3)
        self.assertLessEqual(len(key_events), 3)
    
    def test_character_relationships(self):
        """测试角色关系提取"""
        # 构建知识图谱
        kg = build_knowledge_graph(self.test_subtitles, "zh")
        
        # 检查小明的关系
        xiaoming_relations = kg.get_character_relationships("小明")
        self.assertGreater(len(xiaoming_relations), 0)
        
        # 确保每个关系都有必要的属性
        for relation in xiaoming_relations:
            self.assertIn("character", relation)
            self.assertIn("relation", relation)
            self.assertIn("weight", relation)
            self.assertIn("direction", relation)
    
    def test_visualize(self):
        """测试图谱可视化"""
        # 构建知识图谱
        kg = build_knowledge_graph(self.test_subtitles, "zh")
        
        # 创建临时文件用于保存可视化图像
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
            output_path = temp_file.name
        
        try:
            # 生成可视化图像
            kg.visualize(output_path)
            
            # 验证文件是否存在且大小大于0
            self.assertTrue(os.path.exists(output_path))
            self.assertGreater(os.path.getsize(output_path), 0)
        finally:
            # 清理临时文件
            if os.path.exists(output_path):
                os.unlink(output_path)
    
    def test_export_json(self):
        """测试导出JSON"""
        # 构建知识图谱
        kg = build_knowledge_graph(self.test_subtitles, "zh")
        
        # 创建临时文件用于保存JSON
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as temp_file:
            output_path = temp_file.name
        
        try:
            # 导出为JSON
            result = kg.export_json(output_path)
            
            # 验证导出是否成功
            self.assertTrue(result)
            self.assertTrue(os.path.exists(output_path))
            
            # 读取并验证JSON内容
            with open(output_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 验证JSON结构
            self.assertIn("nodes", data)
            self.assertIn("edges", data)
            self.assertIn("metadata", data)
            
            # 验证元数据
            metadata = data["metadata"]
            self.assertEqual(metadata["character_count"], len(kg.characters))
            self.assertEqual(metadata["location_count"], len(kg.locations))
            
        finally:
            # 清理临时文件
            if os.path.exists(output_path):
                os.unlink(output_path)
    
    def test_empty_subtitles(self):
        """测试空字幕处理"""
        # 构建知识图谱
        kg = build_knowledge_graph([], "zh")
        
        # 验证处理空字幕不会崩溃
        self.assertTrue(kg.is_built)
        self.assertEqual(len(kg.characters), 0)
        self.assertEqual(len(kg.locations), 0)
        self.assertEqual(len(kg.events), 0)
        
        # 验证各种方法在空数据时的行为
        self.assertEqual(kg.get_character_importance(), {})
        self.assertEqual(kg.get_key_events(top_k=3), [])
        self.assertEqual(kg.get_character_relationships("任意角色"), [])

if __name__ == "__main__":
    unittest.main() 