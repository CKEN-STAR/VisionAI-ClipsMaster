#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 测试数据准备脚本

生成各种测试场景所需的数据文件：
1. 多语言字幕文件（中文/英文/混合）
2. 不同格式的视频文件信息
3. 爆款训练数据对
4. 边界测试用例

作者: VisionAI-ClipsMaster Team
日期: 2025-07-23
"""

import os
import json
import time
import random
from pathlib import Path
from typing import Dict, List, Any, Tuple
import tempfile

class TestDataGenerator:
    """测试数据生成器"""
    
    def __init__(self, output_dir: str = None):
        """初始化测试数据生成器"""
        self.output_dir = output_dir or tempfile.mkdtemp()
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 创建子目录
        self.subtitles_dir = os.path.join(self.output_dir, "subtitles")
        self.videos_dir = os.path.join(self.output_dir, "videos")
        self.training_dir = os.path.join(self.output_dir, "training")
        self.edge_cases_dir = os.path.join(self.output_dir, "edge_cases")
        
        for dir_path in [self.subtitles_dir, self.videos_dir, self.training_dir, self.edge_cases_dir]:
            os.makedirs(dir_path, exist_ok=True)
    
    def generate_all_test_data(self):
        """生成所有测试数据"""
        print("开始生成测试数据...")
        
        # 生成字幕文件
        self.generate_subtitle_files()
        
        # 生成视频信息文件
        self.generate_video_info_files()
        
        # 生成训练数据对
        self.generate_training_data_pairs()
        
        # 生成边界测试用例
        self.generate_edge_case_files()
        
        # 生成测试配置文件
        self.generate_test_config()
        
        print(f"测试数据生成完成，输出目录: {self.output_dir}")
        return self.output_dir
    
    def generate_subtitle_files(self):
        """生成各种字幕文件"""
        print("生成字幕文件...")
        
        # 中文字幕 - 短剧风格
        zh_drama_content = self._create_chinese_drama_subtitles()
        self._save_srt_file("zh_drama_original.srt", zh_drama_content)
        
        # 英文字幕 - 短剧风格
        en_drama_content = self._create_english_drama_subtitles()
        self._save_srt_file("en_drama_original.srt", en_drama_content)
        
        # 混合语言字幕
        mixed_content = self._create_mixed_language_subtitles()
        self._save_srt_file("mixed_language.srt", mixed_content)
        
        # 长时间字幕（测试内存使用）
        long_content = self._create_long_duration_subtitles()
        self._save_srt_file("long_duration_test.srt", long_content)
        
        # 高密度字幕（测试处理性能）
        dense_content = self._create_dense_subtitles()
        self._save_srt_file("dense_subtitles_test.srt", dense_content)
    
    def _create_chinese_drama_subtitles(self) -> str:
        """创建中文短剧字幕"""
        lines = [
            "今天是我人生中最重要的一天",
            "我终于要见到那个人了",
            "心情既紧张又兴奋",
            "希望一切都能顺利进行",
            "这个决定将改变我的一生",
            "我已经准备好面对任何挑战",
            "无论结果如何，我都不会后悔",
            "因为这是我内心真正想要的",
            "爱情需要勇气去追求",
            "我相信真爱终将战胜一切"
        ]
        return self._create_srt_content(lines, segment_duration=3.0)
    
    def _create_english_drama_subtitles(self) -> str:
        """创建英文短剧字幕"""
        lines = [
            "Today is the most important day of my life",
            "I'm finally going to meet that person",
            "I feel both nervous and excited",
            "I hope everything goes smoothly",
            "This decision will change my life",
            "I'm ready to face any challenge",
            "No matter what happens, I won't regret it",
            "Because this is what I truly want",
            "Love requires courage to pursue",
            "I believe true love will conquer all"
        ]
        return self._create_srt_content(lines, segment_duration=3.0)
    
    def _create_mixed_language_subtitles(self) -> str:
        """创建混合语言字幕"""
        lines = [
            "Hello, 你好世界",
            "This is a mixed language test 这是混合语言测试",
            "AI人工智能 is changing the world",
            "我们需要 adapt to new technology",
            "Future未来 looks very promising"
        ]
        return self._create_srt_content(lines, segment_duration=4.0)
    
    def _create_long_duration_subtitles(self) -> str:
        """创建长时间字幕（用于内存测试）"""
        lines = []
        for i in range(200):  # 200条字幕，约10分钟
            lines.append(f"这是第{i+1}条测试字幕，用于验证长时间处理能力")
        return self._create_srt_content(lines, segment_duration=3.0)
    
    def _create_dense_subtitles(self) -> str:
        """创建高密度字幕（用于性能测试）"""
        lines = []
        for i in range(100):
            lines.append(f"密集字幕{i+1}")
        return self._create_srt_content(lines, segment_duration=0.5)  # 每0.5秒一条
    
    def _create_srt_content(self, lines: List[str], segment_duration: float = 3.0) -> str:
        """创建SRT格式内容"""
        srt_content = ""
        current_time = 0.0
        
        for i, line in enumerate(lines):
            start_time = current_time
            end_time = current_time + segment_duration
            
            start_str = self._seconds_to_srt_time(start_time)
            end_str = self._seconds_to_srt_time(end_time)
            
            srt_content += f"{i+1}\n{start_str} --> {end_str}\n{line}\n\n"
            current_time = end_time
        
        return srt_content
    
    def _seconds_to_srt_time(self, seconds: float) -> str:
        """将秒数转换为SRT时间格式"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"
    
    def _save_srt_file(self, filename: str, content: str):
        """保存SRT文件"""
        file_path = os.path.join(self.subtitles_dir, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  生成字幕文件: {filename}")
    
    def generate_video_info_files(self):
        """生成视频信息文件"""
        print("生成视频信息文件...")
        
        video_formats = [
            {"format": "mp4", "codec": "h264", "fps": 25, "bitrate": "2000k"},
            {"format": "avi", "codec": "xvid", "fps": 30, "bitrate": "1500k"},
            {"format": "flv", "codec": "h264", "fps": 24, "bitrate": "1000k"},
            {"format": "mkv", "codec": "h265", "fps": 60, "bitrate": "4000k"}
        ]
        
        resolutions = [
            {"width": 1920, "height": 1080, "name": "1080p"},
            {"width": 1280, "height": 720, "name": "720p"},
            {"width": 854, "height": 480, "name": "480p"},
            {"width": 3840, "height": 2160, "name": "4K"}
        ]
        
        video_info_list = []
        
        for i, fmt in enumerate(video_formats):
            for j, res in enumerate(resolutions):
                video_info = {
                    "id": f"video_{i}_{j}",
                    "filename": f"test_video_{fmt['format']}_{res['name']}.{fmt['format']}",
                    "duration": random.uniform(30, 300),  # 30秒到5分钟
                    "format": fmt["format"],
                    "codec": fmt["codec"],
                    "fps": fmt["fps"],
                    "bitrate": fmt["bitrate"],
                    "width": res["width"],
                    "height": res["height"],
                    "resolution_name": res["name"],
                    "file_size": random.randint(10, 500) * 1024 * 1024,  # 10MB-500MB
                    "created_time": time.time()
                }
                video_info_list.append(video_info)
        
        # 保存视频信息列表
        video_info_file = os.path.join(self.videos_dir, "video_info_list.json")
        with open(video_info_file, 'w', encoding='utf-8') as f:
            json.dump(video_info_list, f, indent=2, ensure_ascii=False)
        
        print(f"  生成视频信息文件: video_info_list.json ({len(video_info_list)}个视频)")
    
    def generate_training_data_pairs(self):
        """生成训练数据对"""
        print("生成训练数据对...")
        
        # 中文训练数据对
        zh_training_pairs = self._create_chinese_training_pairs()
        zh_file = os.path.join(self.training_dir, "zh_training_pairs.json")
        with open(zh_file, 'w', encoding='utf-8') as f:
            json.dump(zh_training_pairs, f, indent=2, ensure_ascii=False)
        
        # 英文训练数据对
        en_training_pairs = self._create_english_training_pairs()
        en_file = os.path.join(self.training_dir, "en_training_pairs.json")
        with open(en_file, 'w', encoding='utf-8') as f:
            json.dump(en_training_pairs, f, indent=2, ensure_ascii=False)
        
        print(f"  生成中文训练数据对: {len(zh_training_pairs)}对")
        print(f"  生成英文训练数据对: {len(en_training_pairs)}对")
    
    def _create_chinese_training_pairs(self) -> List[Dict[str, Any]]:
        """创建中文训练数据对"""
        pairs = []
        
        # 原片字幕 -> 爆款字幕的训练对
        original_plots = [
            ["男主角走进咖啡厅", "看到女主角在等待", "两人开始交谈", "气氛逐渐融洽"],
            ["女主角收到神秘信件", "决定前往指定地点", "发现了惊人秘密", "人生从此改变"],
            ["主角面临重要选择", "经过内心挣扎", "最终做出决定", "迎接新的挑战"]
        ]
        
        viral_versions = [
            ["震惊！咖啡厅偶遇改变一生", "这个眼神让我心动不已", "没想到爱情来得这么突然"],
            ["神秘信件背后的真相", "这个秘密让所有人震惊", "人生逆转就在一瞬间"],
            ["人生最难的选择来了", "这个决定让我泪目", "勇敢的人才能获得幸福"]
        ]
        
        for i, (original, viral) in enumerate(zip(original_plots, viral_versions)):
            pair = {
                "id": f"zh_pair_{i+1}",
                "original_subtitles": self._create_srt_content(original, 4.0),
                "viral_subtitles": self._create_srt_content(viral, 3.0),
                "style": "emotional_hook",
                "engagement_score": random.uniform(0.8, 0.95)
            }
            pairs.append(pair)
        
        return pairs
    
    def _create_english_training_pairs(self) -> List[Dict[str, Any]]:
        """创建英文训练数据对"""
        pairs = []
        
        original_plots = [
            ["Hero enters the coffee shop", "Sees heroine waiting", "They start talking", "Atmosphere becomes pleasant"],
            ["Heroine receives mysterious letter", "Decides to go to specified location", "Discovers shocking secret", "Life changes forever"],
            ["Protagonist faces important choice", "After internal struggle", "Finally makes decision", "Embraces new challenge"]
        ]
        
        viral_versions = [
            ["SHOCKING! Coffee shop encounter changes everything", "This look made my heart skip", "Love came so unexpectedly"],
            ["The truth behind the mysterious letter", "This secret shocked everyone", "Life reversal in an instant"],
            ["The hardest choice of life", "This decision made me cry", "Only brave people find happiness"]
        ]
        
        for i, (original, viral) in enumerate(zip(original_plots, viral_versions)):
            pair = {
                "id": f"en_pair_{i+1}",
                "original_subtitles": self._create_srt_content(original, 4.0),
                "viral_subtitles": self._create_srt_content(viral, 3.0),
                "style": "emotional_hook",
                "engagement_score": random.uniform(0.8, 0.95)
            }
            pairs.append(pair)
        
        return pairs
    
    def generate_edge_case_files(self):
        """生成边界测试用例"""
        print("生成边界测试用例...")
        
        # 空字幕文件
        self._save_srt_file("empty.srt", "")
        
        # 格式错误的字幕文件
        invalid_content = "这不是有效的SRT格式\n没有时间码\n没有序号"
        self._save_srt_file("invalid_format.srt", invalid_content)
        
        # 时间码错误的字幕文件
        invalid_time_content = """1
25:61:61,999 --> 25:61:62,000
时间码格式错误

2
00:00:10,000 --> 00:00:05,000
结束时间早于开始时间
"""
        self._save_srt_file("invalid_timecode.srt", invalid_time_content)
        
        # 超长字幕行
        long_line = "这是一行非常非常长的字幕" * 100
        long_line_content = f"1\n00:00:00,000 --> 00:00:05,000\n{long_line}\n\n"
        self._save_srt_file("long_line.srt", long_line_content)
        
        print("  生成边界测试用例: empty.srt, invalid_format.srt, invalid_timecode.srt, long_line.srt")
    
    def generate_test_config(self):
        """生成测试配置文件"""
        test_config = {
            "test_data_version": "1.0",
            "generated_time": time.time(),
            "directories": {
                "subtitles": self.subtitles_dir,
                "videos": self.videos_dir,
                "training": self.training_dir,
                "edge_cases": self.edge_cases_dir
            },
            "test_scenarios": {
                "alignment_precision": {
                    "target_precision": 0.5,
                    "high_precision_target": 0.2,
                    "ultra_precision_target": 0.1
                },
                "language_detection": {
                    "accuracy_threshold": 0.9,
                    "mixed_language_support": True
                },
                "model_switching": {
                    "max_switch_time": 1.5,
                    "memory_limit_gb": 3.8
                },
                "screenplay_reconstruction": {
                    "min_coherence_score": 0.7,
                    "min_duration_ratio": 0.3,
                    "max_duration_ratio": 0.8
                }
            }
        }
        
        config_file = os.path.join(self.output_dir, "test_config.json")
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(test_config, f, indent=2, ensure_ascii=False)
        
        print(f"  生成测试配置文件: test_config.json")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="VisionAI-ClipsMaster 测试数据生成器")
    parser.add_argument("--output-dir", "-o", help="输出目录", default=None)
    
    args = parser.parse_args()
    
    generator = TestDataGenerator(args.output_dir)
    output_dir = generator.generate_all_test_data()
    
    print(f"\n测试数据生成完成！")
    print(f"输出目录: {output_dir}")
    print("\n生成的文件结构:")
    for root, dirs, files in os.walk(output_dir):
        level = root.replace(output_dir, '').count(os.sep)
        indent = ' ' * 2 * level
        print(f"{indent}{os.path.basename(root)}/")
        subindent = ' ' * 2 * (level + 1)
        for file in files:
            print(f"{subindent}{file}")

if __name__ == "__main__":
    main()
