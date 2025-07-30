#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试用模拟模块
用于在缺少某些依赖时提供基本功能
"""

import os
import json
import time
from typing import Dict, List, Any, Optional
from pathlib import Path

class MockSRTParser:
    """模拟SRT解析器"""
    
    @staticmethod
    def parse_srt(file_path: str) -> List[Dict[str, Any]]:
        """解析SRT文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            subtitles = []
            blocks = content.strip().split('\n\n')
            
            for i, block in enumerate(blocks):
                lines = block.strip().split('\n')
                if len(lines) >= 3:
                    # 解析时间码
                    time_line = lines[1]
                    if ' --> ' in time_line:
                        start_str, end_str = time_line.split(' --> ')
                        start_time = MockSRTParser._parse_time(start_str)
                        end_time = MockSRTParser._parse_time(end_str)
                        
                        # 获取字幕文本
                        text = '\n'.join(lines[2:])
                        
                        subtitles.append({
                            'index': i + 1,
                            'start_time': start_time,
                            'end_time': end_time,
                            'text': text
                        })
            
            return subtitles
            
        except Exception as e:
            print(f"SRT解析失败: {e}")
            return []
    
    @staticmethod
    def _parse_time(time_str: str) -> float:
        """解析时间字符串为秒数"""
        try:
            # 格式: HH:MM:SS,mmm
            time_str = time_str.replace(',', '.')
            parts = time_str.split(':')
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = float(parts[2])
            
            return hours * 3600 + minutes * 60 + seconds
        except:
            return 0.0

class MockScreenplayEngineer:
    """模拟剧本工程师"""
    
    def __init__(self):
        self.processing_history = []
        self.current_subtitles = []
        
    def load_subtitles(self, srt_data) -> List[Dict[str, Any]]:
        """加载字幕"""
        if isinstance(srt_data, str):
            # 文件路径
            subtitles = MockSRTParser.parse_srt(srt_data)
        elif isinstance(srt_data, list):
            # 字幕列表
            subtitles = srt_data
        else:
            subtitles = []
            
        self.current_subtitles = subtitles
        return subtitles
    
    def analyze_plot_structure(self, subtitles: List[Dict]) -> Dict[str, Any]:
        """分析剧情结构"""
        if not subtitles:
            return {}
            
        analysis = {
            "plot_points": [],
            "emotion_curve": [],
            "characters": [],
            "themes": []
        }
        
        # 简单的情节点识别
        for i, subtitle in enumerate(subtitles):
            text = subtitle.get('text', '').lower()
            
            # 识别关键情节点
            if any(keyword in text for keyword in ['开始', '相遇', '冲突', '解决', '结束']):
                analysis["plot_points"].append({
                    "index": i,
                    "type": "key_moment",
                    "text": subtitle.get('text', '')
                })
            
            # 简单的情感分析
            emotion_score = 0.5  # 中性
            if any(word in text for word in ['爱', '喜欢', '开心', '快乐']):
                emotion_score = 0.8
            elif any(word in text for word in ['难过', '伤心', '痛苦', '困难']):
                emotion_score = 0.2
                
            analysis["emotion_curve"].append({
                "time": subtitle.get('start_time', 0),
                "emotion": emotion_score
            })
        
        return analysis
    
    def generate_viral_srt(self, subtitles: List[Dict]) -> List[Dict]:
        """生成爆款字幕"""
        if not subtitles:
            return []
            
        # 简化的爆款生成逻辑
        viral_subtitles = []
        
        # 选择关键片段（每3个字幕选1个）
        for i in range(0, len(subtitles), 3):
            if i < len(subtitles):
                original = subtitles[i].copy()
                
                # 添加一些"爆款"元素
                text = original.get('text', '')
                if text:
                    # 简单的文本优化
                    if not text.endswith('！') and not text.endswith('？'):
                        text += '！'
                    
                    original['text'] = text
                    viral_subtitles.append(original)
        
        return viral_subtitles

class MockClipGenerator:
    """模拟剪辑生成器"""
    
    def __init__(self):
        self.temp_dir = Path("temp_clips")
        self.temp_dir.mkdir(exist_ok=True)
        
    def generate_clips(self, video_path: str, subtitles: List[Dict], output_path: str) -> bool:
        """生成剪辑视频"""
        try:
            # 模拟视频剪辑过程
            time.sleep(1)  # 模拟处理时间
            
            # 创建输出文件（空文件）
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.touch()
            
            return True
            
        except Exception as e:
            print(f"剪辑生成失败: {e}")
            return False

class MockJianyingProExporter:
    """模拟剪映导出器"""
    
    def export_project(self, video_path: str, subtitles: List[Dict], project_path: str) -> bool:
        """导出剪映工程文件"""
        try:
            project_data = {
                "version": "3.0.0",
                "video_path": video_path,
                "subtitles": subtitles,
                "export_time": time.time()
            }
            
            with open(project_path, 'w', encoding='utf-8') as f:
                json.dump(project_data, f, ensure_ascii=False, indent=2)
                
            return True
            
        except Exception as e:
            print(f"剪映导出失败: {e}")
            return False

def mock_detect_language_from_file(file_path: str) -> str:
    """模拟语言检测"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 简单的语言检测
        chinese_chars = sum(1 for char in content if '\u4e00' <= char <= '\u9fff')
        english_chars = sum(1 for char in content if char.isalpha() and ord(char) < 128)
        
        if chinese_chars > english_chars:
            return "zh"
        else:
            return "en"
            
    except:
        return "zh"  # 默认中文

# 注入模拟模块到sys.modules
import sys

class MockModule:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

# 创建模拟模块
sys.modules['src.parsers.srt_parser'] = MockModule(parse_srt=MockSRTParser.parse_srt)
sys.modules['src.core.screenplay_engineer'] = MockModule(ScreenplayEngineer=MockScreenplayEngineer)
sys.modules['src.core.clip_generator'] = MockModule(ClipGenerator=MockClipGenerator)
sys.modules['src.exporters.jianying_pro_exporter'] = MockModule(JianyingProExporter=MockJianyingProExporter)
sys.modules['src.core.language_detector'] = MockModule(detect_language_from_file=mock_detect_language_from_file)
