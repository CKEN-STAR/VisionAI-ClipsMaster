#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
实时预览模块单元测试
"""

import os
import sys
import unittest
import tempfile
from pathlib import Path
import matplotlib.pyplot as plt

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from timecode.live_preview import (
    PreviewGenerator, 
    generate_timeline_preview,
    generate_tracks_preview,
    generate_alignment_comparison
)


class TestLivePreview(unittest.TestCase):
    """实时预览模块测试类"""
    
    def setUp(self):
        """设置测试环境"""
        self.preview_gen = PreviewGenerator()
        self.test_output_dir = tempfile.mkdtemp()
        
        # 测试数据
        self.test_scenes = [
            {"start": 0, "end": 20, "emotion_score": 0.5, "sentiment": "neutral", "tags": ["开场"]},
            {"start": 20, "end": 35, "emotion_score": 0.7, "sentiment": "positive", "tags": ["介绍"]},
            {"start": 35, "end": 60, "emotion_score": 0.4, "sentiment": "neutral", "tags": ["过渡"]},
            {"start": 60, "end": 80, "emotion_score": 0.9, "sentiment": "positive", "scene_type": "climax", "tags": ["高潮"]},
            {"start": 80, "end": 100, "emotion_score": 0.3, "sentiment": "negative", "tags": ["结束"]}
        ]
        
        self.test_tracks = {
            "main_video": {"type": "video", "duration": 100.0},
            "main_audio": {"type": "audio", "duration": 105.0},
            "subtitle": {"type": "subtitle", "duration": 95.0}
        }
        
    def tearDown(self):
        """清理测试环境"""
        # 删除测试生成的临时文件
        for file in Path(self.test_output_dir).glob("*.html"):
            os.remove(file)
        os.rmdir(self.test_output_dir)
        
    def test_preview_generator_init(self):
        """测试预览生成器初始化"""
        self.assertIsNotNone(self.preview_gen)
        self.assertIsNotNone(self.preview_gen.config)
        
    def test_generate_waveform(self):
        """测试波形图生成"""
        html_content = self.preview_gen.generate_waveform(self.test_scenes)
        self.assertIsNotNone(html_content)
        self.assertTrue(len(html_content) > 1000)  # 确保生成了足够的内容
        
    def test_generate_track_view(self):
        """测试轨道视图生成"""
        html_content = self.preview_gen.generate_track_view(self.test_tracks)
        self.assertIsNotNone(html_content)
        self.assertTrue(len(html_content) > 1000)
        
    def test_generate_alignment_preview(self):
        """测试对齐前后比较"""
        # 创建原始和对齐后的轨道数据
        original_tracks = {
            "video": {"type": "video", "duration": 100.0},
            "audio": {"type": "audio", "duration": 95.0}
        }
        
        aligned_tracks = {
            "video": {"type": "video", "duration": 100.0},
            "audio": {"type": "audio", "duration": 100.0, "original_duration": 95.0}
        }
        
        html_content = self.preview_gen.generate_alignment_preview(original_tracks, aligned_tracks)
        self.assertIsNotNone(html_content)
        self.assertTrue(len(html_content) > 1000)
        
    def test_plt_to_html(self):
        """测试图表到HTML转换"""
        # 创建简单的matplotlib图表
        plt.figure(figsize=(6, 4))
        plt.plot([0, 1, 2, 3, 4], [0, 1, 4, 9, 16])
        plt.title("测试图表")
        
        # 转换为HTML
        html_content = self.preview_gen._plt_to_html(plt)
        self.assertIsNotNone(html_content)
        self.assertTrue(len(html_content) > 1000)
        
        # 保存到文件
        output_path = os.path.join(self.test_output_dir, "test_output.html")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # 检查文件是否存在并有内容
        self.assertTrue(os.path.exists(output_path))
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertTrue(len(content) > 0)
            
    def test_generate_timeline_preview(self):
        """测试时间轴预览生成函数"""
        html_content = generate_timeline_preview(self.test_scenes)
        self.assertIsNotNone(html_content)
        
    def test_generate_tracks_preview(self):
        """测试轨道预览生成函数"""
        html_content = generate_tracks_preview(self.test_tracks)
        self.assertIsNotNone(html_content)


if __name__ == "__main__":
    unittest.main() 