#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 测试数据生成器
生成各种测试场景所需的示例数据
"""

import os
import json
import random
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any

class TestDataGenerator:
    """测试数据生成器"""
    
    def __init__(self, output_dir: str = "test_data"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # 创建子目录
        (self.output_dir / "subtitles").mkdir(exist_ok=True)
        (self.output_dir / "videos").mkdir(exist_ok=True)
        (self.output_dir / "training").mkdir(exist_ok=True)
        (self.output_dir / "export").mkdir(exist_ok=True)
    
    def generate_all_test_data(self):
        """生成所有测试数据"""
        print("🎬 生成VisionAI-ClipsMaster测试数据")
        print("=" * 50)
        
        # 1. 生成字幕文件
        self.generate_subtitle_files()
        
        # 2. 生成训练数据
        self.generate_training_data()
        
        # 3. 生成配置文件
        self.generate_config_files()
        
        # 4. 生成示例视频信息
        self.generate_video_metadata()
        
        # 5. 生成测试用例
        self.generate_test_cases()
        
        print(f"\n✅ 所有测试数据已生成到: {self.output_dir}")
    
    def generate_subtitle_files(self):
        """生成字幕文件"""
        print("\n📝 生成字幕文件...")
        
        # 中文字幕 - 短剧示例
        zh_drama_srt = self._generate_chinese_drama_srt()
        self._save_file("subtitles/zh_drama_original.srt", zh_drama_srt)
        
        # 英文字幕 - 短剧示例
        en_drama_srt = self._generate_english_drama_srt()
        self._save_file("subtitles/en_drama_original.srt", en_drama_srt)
        
        # 混合语言字幕
        mixed_srt = self._generate_mixed_language_srt()
        self._save_file("subtitles/mixed_language.srt", mixed_srt)
        
        # 爆款混剪字幕示例
        zh_viral_srt = self._generate_viral_chinese_srt()
        self._save_file("subtitles/zh_viral_example.srt", zh_viral_srt)
        
        en_viral_srt = self._generate_viral_english_srt()
        self._save_file("subtitles/en_viral_example.srt", en_viral_srt)
        
        # 错误格式字幕（用于测试异常处理）
        invalid_srt = self._generate_invalid_srt()
        self._save_file("subtitles/invalid_format.srt", invalid_srt)
        
        print("  ✅ 字幕文件生成完成")
    
    def _generate_chinese_drama_srt(self) -> str:
        """生成中文短剧字幕"""
        segments = [
            (1, "00:00:01,000", "00:00:04,000", "林小雨刚刚大学毕业，怀着忐忑的心情走进了这家知名公司。"),
            (2, "00:00:05,000", "00:00:08,000", "她没想到，第一天上班就遇到了传说中的霸道总裁陈浩然。"),
            (3, "00:00:09,000", "00:00:12,000", "陈浩然冷漠地看着她：'你就是新来的实习生？'"),
            (4, "00:00:13,000", "00:00:16,000", "林小雨紧张地点头：'是的，总裁，我是林小雨。'"),
            (5, "00:00:17,000", "00:00:20,000", "陈浩然皱眉：'我不需要花瓶，只要有能力的人。'"),
            (6, "00:00:21,000", "00:00:24,000", "林小雨咬牙：'我会证明给您看的！'"),
            (7, "00:00:25,000", "00:00:28,000", "就这样，一场职场爱情故事拉开了序幕..."),
            (8, "00:00:29,000", "00:00:32,000", "三个月后，林小雨凭借出色的表现赢得了所有人的认可。"),
            (9, "00:00:33,000", "00:00:36,000", "陈浩然开始对这个倔强的女孩刮目相看。"),
            (10, "00:00:37,000", "00:00:40,000", "但是，一个意外的消息打破了平静..."),
            (11, "00:00:41,000", "00:00:44,000", "林小雨发现陈浩然竟然是她失散多年的青梅竹马！"),
            (12, "00:00:45,000", "00:00:48,000", "面对这个惊人的真相，两人该如何面对？")
        ]
        
        return self._format_srt_segments(segments)
    
    def _generate_english_drama_srt(self) -> str:
        """生成英文短剧字幕"""
        segments = [
            (1, "00:00:01,000", "00:00:04,000", "Emma just graduated from college and nervously entered the prestigious company."),
            (2, "00:00:05,000", "00:00:08,000", "She never expected to meet the legendary CEO Alex on her first day."),
            (3, "00:00:09,000", "00:00:12,000", "Alex looked at her coldly: 'So you're the new intern?'"),
            (4, "00:00:13,000", "00:00:16,000", "Emma nodded nervously: 'Yes, Mr. Alex. I'm Emma.'"),
            (5, "00:00:17,000", "00:00:20,000", "Alex frowned: 'I don't need decorations, only capable people.'"),
            (6, "00:00:21,000", "00:00:24,000", "Emma gritted her teeth: 'I'll prove it to you!'"),
            (7, "00:00:25,000", "00:00:28,000", "Thus began a workplace romance story..."),
            (8, "00:00:29,000", "00:00:32,000", "Three months later, Emma won everyone's recognition with her outstanding performance."),
            (9, "00:00:33,000", "00:00:36,000", "Alex began to see this stubborn girl in a new light."),
            (10, "00:00:37,000", "00:00:40,000", "But an unexpected news broke the peace..."),
            (11, "00:00:41,000", "00:00:44,000", "Emma discovered that Alex was her long-lost childhood friend!"),
            (12, "00:00:45,000", "00:00:48,000", "Facing this shocking truth, how should they deal with it?")
        ]
        
        return self._format_srt_segments(segments)
    
    def _generate_mixed_language_srt(self) -> str:
        """生成混合语言字幕"""
        segments = [
            (1, "00:00:01,000", "00:00:03,000", "Welcome to VisionAI-ClipsMaster 测试"),
            (2, "00:00:04,000", "00:00:06,000", "This is a mixed language test 这是混合语言测试"),
            (3, "00:00:07,000", "00:00:09,000", "AI模型 should handle this correctly"),
            (4, "00:00:10,000", "00:00:12,000", "中英文混合 content processing test")
        ]
        
        return self._format_srt_segments(segments)
    
    def _generate_viral_chinese_srt(self) -> str:
        """生成爆款中文字幕（重构后的精华版）"""
        segments = [
            (1, "00:00:01,000", "00:00:03,000", "霸道总裁第一次见面就说：我不需要花瓶！"),
            (2, "00:00:04,000", "00:00:06,000", "女主霸气回应：我会证明给您看！"),
            (3, "00:00:07,000", "00:00:09,000", "三个月后，总裁对她刮目相看..."),
            (4, "00:00:10,000", "00:00:12,000", "但是！意外发现他竟然是青梅竹马！"),
            (5, "00:00:13,000", "00:00:15,000", "这个惊天秘密将如何改变一切？")
        ]
        
        return self._format_srt_segments(segments)
    
    def _generate_viral_english_srt(self) -> str:
        """生成爆款英文字幕（重构后的精华版）"""
        segments = [
            (1, "00:00:01,000", "00:00:03,000", "CEO's first words: 'I don't need decorations!'"),
            (2, "00:00:04,000", "00:00:06,000", "Her bold response: 'I'll prove it to you!'"),
            (3, "00:00:07,000", "00:00:09,000", "Three months later, he saw her differently..."),
            (4, "00:00:10,000", "00:00:12,000", "But PLOT TWIST! He's her childhood friend!"),
            (5, "00:00:13,000", "00:00:15,000", "How will this shocking secret change everything?")
        ]
        
        return self._format_srt_segments(segments)
    
    def _generate_invalid_srt(self) -> str:
        """生成无效格式字幕（用于测试异常处理）"""
        return """这不是有效的SRT格式
没有时间轴
没有序号
只是普通文本
"""
    
    def _format_srt_segments(self, segments: List[tuple]) -> str:
        """格式化SRT片段"""
        srt_content = ""
        for index, start_time, end_time, text in segments:
            srt_content += f"{index}\n{start_time} --> {end_time}\n{text}\n\n"
        return srt_content.strip()
    
    def generate_training_data(self):
        """生成训练数据"""
        print("\n🎓 生成训练数据...")
        
        # 中文训练数据对
        zh_training_pairs = [
            {
                "original_srt": "zh_drama_original.srt",
                "viral_srt": "zh_viral_example.srt",
                "metadata": {
                    "genre": "romance",
                    "style": "domineering_ceo",
                    "target_length_ratio": 0.4,
                    "key_elements": ["first_meeting", "workplace", "identity_reveal"]
                }
            }
        ]
        
        # 英文训练数据对
        en_training_pairs = [
            {
                "original_srt": "en_drama_original.srt",
                "viral_srt": "en_viral_example.srt",
                "metadata": {
                    "genre": "romance",
                    "style": "workplace_drama",
                    "target_length_ratio": 0.4,
                    "key_elements": ["first_meeting", "workplace", "plot_twist"]
                }
            }
        ]
        
        self._save_json("training/zh_training_pairs.json", zh_training_pairs)
        self._save_json("training/en_training_pairs.json", en_training_pairs)
        
        # 生成增强数据配置
        augmentation_config = {
            "text_augmentation": {
                "synonym_replacement": True,
                "random_insertion": False,
                "random_swap": True,
                "random_deletion": False
            },
            "plot_augmentation": {
                "emotion_variation": True,
                "character_substitution": True,
                "scene_reordering": True
            }
        }
        
        self._save_json("training/augmentation_config.json", augmentation_config)
        
        print("  ✅ 训练数据生成完成")
    
    def generate_config_files(self):
        """生成配置文件"""
        print("\n⚙️ 生成配置文件...")
        
        # 模型配置
        model_config = {
            "available_models": [
                {
                    "name": "mistral-7b-en",
                    "language": "en",
                    "path": "models/mistral/",
                    "quantization": "Q5_K_M",
                    "max_memory_mb": 4000
                },
                {
                    "name": "qwen2.5-7b-zh",
                    "language": "zh",
                    "path": "models/qwen/",
                    "quantization": "Q4_K_M",
                    "max_memory_mb": 3800
                }
            ],
            "active_model": "auto",
            "memory_limit_mb": 3800,
            "cpu_threads": 4
        }
        
        self._save_json("model_config.json", model_config)
        
        # 剪辑设置
        clip_settings = {
            "target_compression_ratio": 0.6,
            "min_segment_duration": 2.0,
            "max_segment_duration": 10.0,
            "transition_buffer": 0.5,
            "quality_threshold": 0.7,
            "emotion_weight": 0.8,
            "narrative_weight": 0.9
        }
        
        self._save_json("clip_settings.json", clip_settings)
        
        # 导出设置
        export_settings = {
            "default_format": "mp4",
            "supported_formats": ["mp4", "avi", "mov"],
            "jianying_export": {
                "enabled": True,
                "version": "3.0",
                "template_path": "templates/jianying_template.json"
            },
            "quality_settings": {
                "resolution": "1080p",
                "bitrate": "5000k",
                "fps": 30
            }
        }
        
        self._save_json("export_settings.json", export_settings)
        
        print("  ✅ 配置文件生成完成")
    
    def generate_video_metadata(self):
        """生成视频元数据"""
        print("\n🎥 生成视频元数据...")
        
        video_metadata = [
            {
                "filename": "zh_drama_episode1.mp4",
                "duration": 48.0,
                "resolution": "1920x1080",
                "fps": 30,
                "language": "zh",
                "genre": "romance",
                "subtitle_file": "zh_drama_original.srt"
            },
            {
                "filename": "en_drama_episode1.mp4",
                "duration": 48.0,
                "resolution": "1920x1080",
                "fps": 30,
                "language": "en",
                "genre": "romance",
                "subtitle_file": "en_drama_original.srt"
            }
        ]
        
        self._save_json("videos/video_metadata.json", video_metadata)
        
        print("  ✅ 视频元数据生成完成")
    
    def generate_test_cases(self):
        """生成测试用例"""
        print("\n🧪 生成测试用例...")
        
        test_cases = {
            "language_detection": [
                {
                    "name": "纯中文检测",
                    "input_file": "subtitles/zh_drama_original.srt",
                    "expected_language": "zh",
                    "confidence_threshold": 0.9
                },
                {
                    "name": "纯英文检测",
                    "input_file": "subtitles/en_drama_original.srt",
                    "expected_language": "en",
                    "confidence_threshold": 0.9
                },
                {
                    "name": "混合语言检测",
                    "input_file": "subtitles/mixed_language.srt",
                    "expected_language": "mixed",
                    "confidence_threshold": 0.7
                }
            ],
            "srt_parsing": [
                {
                    "name": "标准SRT解析",
                    "input_file": "subtitles/zh_drama_original.srt",
                    "expected_segments": 12,
                    "should_succeed": True
                },
                {
                    "name": "无效格式处理",
                    "input_file": "subtitles/invalid_format.srt",
                    "expected_segments": 0,
                    "should_succeed": False
                }
            ],
            "narrative_analysis": [
                {
                    "name": "中文剧情分析",
                    "input_file": "subtitles/zh_drama_original.srt",
                    "expected_plot_points": ["introduction", "conflict", "resolution"],
                    "min_coherence_score": 0.8
                }
            ],
            "screenplay_reconstruction": [
                {
                    "name": "中文剧本重构",
                    "input_file": "subtitles/zh_drama_original.srt",
                    "target_compression": 0.4,
                    "min_quality_score": 0.7
                }
            ]
        }
        
        self._save_json("test_cases.json", test_cases)
        
        print("  ✅ 测试用例生成完成")
    
    def _save_file(self, filename: str, content: str):
        """保存文件"""
        filepath = self.output_dir / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _save_json(self, filename: str, data: Any):
        """保存JSON文件"""
        filepath = self.output_dir / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

def main():
    """主函数"""
    generator = TestDataGenerator()
    generator.generate_all_test_data()
    
    print(f"\n📁 测试数据目录结构:")
    print(f"test_data/")
    print(f"├── subtitles/          # 字幕文件")
    print(f"├── videos/             # 视频元数据")
    print(f"├── training/           # 训练数据")
    print(f"├── export/             # 导出配置")
    print(f"├── test_cases.json     # 测试用例")
    print(f"├── model_config.json   # 模型配置")
    print(f"├── clip_settings.json  # 剪辑设置")
    print(f"└── export_settings.json # 导出设置")

if __name__ == "__main__":
    main()
