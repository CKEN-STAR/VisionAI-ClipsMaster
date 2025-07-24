#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 剪映导出测试数据生成器

专门为剪映导出功能测试生成各种测试数据：
1. 多格式视频文件信息
2. 原始和爆款字幕文件
3. 剪映工程文件模板
4. 测试场景配置

作者: VisionAI-ClipsMaster Team
日期: 2025-07-23
"""

import os
import json
import time
import random
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET

class JianyingTestDataGenerator:
    """剪映测试数据生成器"""
    
    def __init__(self, output_dir: str = None):
        """初始化测试数据生成器"""
        self.output_dir = Path(output_dir) if output_dir else Path("test_output/jianying_test_data")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建子目录
        self.videos_dir = self.output_dir / "videos"
        self.subtitles_dir = self.output_dir / "subtitles"
        self.projects_dir = self.output_dir / "projects"
        self.templates_dir = self.output_dir / "templates"
        
        for dir_path in [self.videos_dir, self.subtitles_dir, self.projects_dir, self.templates_dir]:
            dir_path.mkdir(exist_ok=True)
    
    def generate_all_test_data(self):
        """生成所有测试数据"""
        print("开始生成剪映导出测试数据...")
        
        # 生成视频文件信息
        video_data = self.generate_video_test_data()
        
        # 生成字幕文件
        subtitle_data = self.generate_subtitle_test_data()
        
        # 生成剪映工程模板
        template_data = self.generate_jianying_templates()
        
        # 生成测试场景配置
        scenario_data = self.generate_test_scenarios()
        
        # 生成综合配置文件
        config = self.generate_master_config(video_data, subtitle_data, template_data, scenario_data)
        
        print(f"剪映导出测试数据生成完成，输出目录: {self.output_dir}")
        return config
    
    def generate_video_test_data(self):
        """生成视频测试数据"""
        print("生成视频测试数据...")
        
        # 定义测试视频格式
        video_formats = [
            {
                "name": "standard_mp4",
                "format": "mp4",
                "codec": "h264",
                "resolution": "1920x1080",
                "fps": 25,
                "duration": 300,  # 5分钟
                "bitrate": "2000k",
                "audio_codec": "aac"
            },
            {
                "name": "high_quality_mp4",
                "format": "mp4", 
                "codec": "h265",
                "resolution": "3840x2160",
                "fps": 60,
                "duration": 180,  # 3分钟
                "bitrate": "8000k",
                "audio_codec": "aac"
            },
            {
                "name": "legacy_avi",
                "format": "avi",
                "codec": "xvid",
                "resolution": "1280x720",
                "fps": 30,
                "duration": 240,  # 4分钟
                "bitrate": "1500k",
                "audio_codec": "mp3"
            },
            {
                "name": "web_flv",
                "format": "flv",
                "codec": "h264",
                "resolution": "854x480",
                "fps": 24,
                "duration": 360,  # 6分钟
                "bitrate": "1000k",
                "audio_codec": "aac"
            }
        ]
        
        # 生成详细的视频信息
        video_data = {}
        for video_format in video_formats:
            video_info = {
                "file_path": str(self.videos_dir / f"{video_format['name']}.{video_format['format']}"),
                "format": video_format["format"],
                "codec": video_format["codec"],
                "width": int(video_format["resolution"].split('x')[0]),
                "height": int(video_format["resolution"].split('x')[1]),
                "fps": video_format["fps"],
                "duration": video_format["duration"],
                "bitrate": video_format["bitrate"],
                "audio_codec": video_format["audio_codec"],
                "file_size": random.randint(50, 500) * 1024 * 1024,  # 50MB-500MB
                "created_time": datetime.now().isoformat(),
                "metadata": {
                    "title": f"测试短剧_{video_format['name']}",
                    "description": f"用于测试的{video_format['format'].upper()}格式短剧视频",
                    "tags": ["测试", "短剧", video_format["format"]]
                }
            }
            video_data[video_format["name"]] = video_info
        
        # 保存视频数据
        video_data_file = self.videos_dir / "video_test_data.json"
        with open(video_data_file, 'w', encoding='utf-8') as f:
            json.dump(video_data, f, indent=2, ensure_ascii=False)
        
        print(f"  生成视频测试数据: {len(video_data)}个格式")
        return video_data
    
    def generate_subtitle_test_data(self):
        """生成字幕测试数据"""
        print("生成字幕测试数据...")
        
        subtitle_data = {}
        
        # 生成原始字幕（完整剧情）
        original_subtitles = self._create_original_drama_subtitles()
        subtitle_data["original"] = {
            "file_path": str(self.subtitles_dir / "original_drama.srt"),
            "content": original_subtitles,
            "language": "zh",
            "subtitle_count": len(self._parse_srt_content(original_subtitles)),
            "total_duration": 300,
            "style": "complete_narrative"
        }
        
        # 生成爆款字幕（重构剧情）
        viral_subtitles = self._create_viral_style_subtitles()
        subtitle_data["viral"] = {
            "file_path": str(self.subtitles_dir / "viral_style.srt"),
            "content": viral_subtitles,
            "language": "zh",
            "subtitle_count": len(self._parse_srt_content(viral_subtitles)),
            "total_duration": 120,
            "style": "viral_hooks"
        }
        
        # 生成英文测试字幕
        english_subtitles = self._create_english_test_subtitles()
        subtitle_data["english"] = {
            "file_path": str(self.subtitles_dir / "english_test.srt"),
            "content": english_subtitles,
            "language": "en",
            "subtitle_count": len(self._parse_srt_content(english_subtitles)),
            "total_duration": 150,
            "style": "standard_narrative"
        }
        
        # 生成混合语言字幕
        mixed_subtitles = self._create_mixed_language_subtitles()
        subtitle_data["mixed"] = {
            "file_path": str(self.subtitles_dir / "mixed_language.srt"),
            "content": mixed_subtitles,
            "language": "mixed",
            "subtitle_count": len(self._parse_srt_content(mixed_subtitles)),
            "total_duration": 90,
            "style": "multilingual"
        }
        
        # 保存字幕文件
        for subtitle_type, data in subtitle_data.items():
            with open(data["file_path"], 'w', encoding='utf-8') as f:
                f.write(data["content"])
        
        # 保存字幕数据配置
        subtitle_config_file = self.subtitles_dir / "subtitle_test_data.json"
        with open(subtitle_config_file, 'w', encoding='utf-8') as f:
            # 移除content字段以减少文件大小
            config_data = {}
            for key, value in subtitle_data.items():
                config_data[key] = {k: v for k, v in value.items() if k != "content"}
            json.dump(config_data, f, indent=2, ensure_ascii=False)
        
        print(f"  生成字幕测试数据: {len(subtitle_data)}种类型")
        return subtitle_data
    
    def _create_original_drama_subtitles(self) -> str:
        """创建原始短剧字幕"""
        subtitles = [
            {"start": 0, "end": 8, "text": "今天是个特别的日子"},
            {"start": 8, "end": 16, "text": "我要去见一个很重要的人"},
            {"start": 16, "end": 24, "text": "心情既紧张又期待"},
            {"start": 24, "end": 32, "text": "希望一切都能顺利进行"},
            {"start": 32, "end": 40, "text": "这次见面对我来说意义重大"},
            {"start": 40, "end": 48, "text": "我已经准备了很久"},
            {"start": 48, "end": 56, "text": "无论结果如何都要勇敢面对"},
            {"start": 56, "end": 64, "text": "相信自己一定可以的"},
            {"start": 64, "end": 72, "text": "走进咖啡厅，看到了那个熟悉的身影"},
            {"start": 72, "end": 80, "text": "心跳开始加速"},
            {"start": 80, "end": 88, "text": "我们的眼神相遇了"},
            {"start": 88, "end": 96, "text": "这一刻，时间仿佛停止了"},
            {"start": 96, "end": 104, "text": "我鼓起勇气走向前"},
            {"start": 104, "end": 112, "text": "开始了我们的对话"},
            {"start": 112, "end": 120, "text": "没想到一切都这么自然"},
            {"start": 120, "end": 128, "text": "我们聊得很投机"},
            {"start": 128, "end": 136, "text": "时间过得真快"},
            {"start": 136, "end": 144, "text": "不知不觉已经聊了很久"},
            {"start": 144, "end": 152, "text": "这次见面比我想象的还要好"},
            {"start": 152, "end": 160, "text": "我们约定了下次再见面"}
        ]
        return self._create_srt_content(subtitles)
    
    def _create_viral_style_subtitles(self) -> str:
        """创建爆款风格字幕"""
        subtitles = [
            {"start": 0, "end": 6, "text": "震惊！今天发生了这件事"},
            {"start": 6, "end": 12, "text": "我要去见的这个人竟然是..."},
            {"start": 12, "end": 18, "text": "心跳加速！紧张到不行"},
            {"start": 18, "end": 24, "text": "这次见面将改变我的一生"},
            {"start": 24, "end": 30, "text": "准备了这么久终于要见面了"},
            {"start": 30, "end": 36, "text": "走进咖啡厅的那一刻"},
            {"start": 36, "end": 42, "text": "看到了让我心动的身影"},
            {"start": 42, "end": 48, "text": "四目相对的瞬间"},
            {"start": 48, "end": 54, "text": "时间静止了！"},
            {"start": 54, "end": 60, "text": "勇敢迈出的第一步"},
            {"start": 60, "end": 66, "text": "开始了命中注定的对话"},
            {"start": 66, "end": 72, "text": "没想到我们这么合拍"},
            {"start": 72, "end": 78, "text": "时光飞逝，意犹未尽"},
            {"start": 78, "end": 84, "text": "这是我人生中最美好的时光"},
            {"start": 84, "end": 90, "text": "约定下次见面的那一刻"},
            {"start": 90, "end": 96, "text": "我知道，这就是爱情的开始"}
        ]
        return self._create_srt_content(subtitles)
    
    def _create_english_test_subtitles(self) -> str:
        """创建英文测试字幕"""
        subtitles = [
            {"start": 0, "end": 8, "text": "Today is a very special day"},
            {"start": 8, "end": 16, "text": "I'm going to meet someone very important"},
            {"start": 16, "end": 24, "text": "I feel both nervous and excited"},
            {"start": 24, "end": 32, "text": "I hope everything goes smoothly"},
            {"start": 32, "end": 40, "text": "This meeting means a lot to me"},
            {"start": 40, "end": 48, "text": "I've been preparing for a long time"},
            {"start": 48, "end": 56, "text": "I must face it bravely no matter what"},
            {"start": 56, "end": 64, "text": "I believe I can do it"},
            {"start": 64, "end": 72, "text": "Walking into the cafe, I see that familiar figure"},
            {"start": 72, "end": 80, "text": "My heart starts beating faster"},
            {"start": 80, "end": 88, "text": "Our eyes meet"},
            {"start": 88, "end": 96, "text": "At this moment, time seems to stop"},
            {"start": 96, "end": 104, "text": "I gather courage and walk forward"},
            {"start": 104, "end": 112, "text": "We begin our conversation"},
            {"start": 112, "end": 120, "text": "Everything feels so natural"},
            {"start": 120, "end": 128, "text": "We have great chemistry"},
            {"start": 128, "end": 136, "text": "Time flies so fast"},
            {"start": 136, "end": 144, "text": "We've been talking for so long"},
            {"start": 144, "end": 152, "text": "This meeting is better than I imagined"}
        ]
        return self._create_srt_content(subtitles)
    
    def _create_mixed_language_subtitles(self) -> str:
        """创建混合语言字幕"""
        subtitles = [
            {"start": 0, "end": 6, "text": "Hello, 今天是个特别的日子"},
            {"start": 6, "end": 12, "text": "I'm going to meet 一个很重要的人"},
            {"start": 12, "end": 18, "text": "My heart is beating fast 心跳加速"},
            {"start": 18, "end": 24, "text": "This meeting will change 我的一生"},
            {"start": 24, "end": 30, "text": "准备了这么久 finally the day has come"},
            {"start": 30, "end": 36, "text": "Walking into the cafe 走进咖啡厅"},
            {"start": 36, "end": 42, "text": "看到了那个身影 that familiar figure"},
            {"start": 42, "end": 48, "text": "Our eyes meet 四目相对"},
            {"start": 48, "end": 54, "text": "Time stops 时间静止了"},
            {"start": 54, "end": 60, "text": "勇敢地走向前 walking forward bravely"},
            {"start": 60, "end": 66, "text": "We start talking 开始对话"},
            {"start": 66, "end": 72, "text": "Everything feels natural 一切都很自然"},
            {"start": 72, "end": 78, "text": "Time flies 时光飞逝"},
            {"start": 78, "end": 84, "text": "This is wonderful 这太美好了"},
            {"start": 84, "end": 90, "text": "约定下次见面 promise to meet again"}
        ]
        return self._create_srt_content(subtitles)
    
    def _create_srt_content(self, subtitles: List[Dict]) -> str:
        """创建SRT格式内容"""
        srt_content = ""
        for i, subtitle in enumerate(subtitles, 1):
            start_time = self._seconds_to_srt_time(subtitle["start"])
            end_time = self._seconds_to_srt_time(subtitle["end"])
            
            srt_content += f"{i}\n{start_time} --> {end_time}\n{subtitle['text']}\n\n"
        
        return srt_content
    
    def _seconds_to_srt_time(self, seconds: float) -> str:
        """将秒数转换为SRT时间格式"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"
    
    def _parse_srt_content(self, srt_content: str) -> List[Dict]:
        """解析SRT内容"""
        lines = srt_content.strip().split('\n\n')
        subtitles = []
        
        for block in lines:
            if block.strip():
                lines_in_block = block.strip().split('\n')
                if len(lines_in_block) >= 3:
                    time_line = lines_in_block[1]
                    text = '\n'.join(lines_in_block[2:])
                    
                    if ' --> ' in time_line:
                        start_str, end_str = time_line.split(' --> ')
                        start_seconds = self._srt_time_to_seconds(start_str)
                        end_seconds = self._srt_time_to_seconds(end_str)
                        
                        subtitles.append({
                            "start": start_seconds,
                            "end": end_seconds,
                            "text": text
                        })
        
        return subtitles

    def generate_jianying_templates(self):
        """生成剪映工程模板"""
        print("生成剪映工程模板...")

        template_data = {}

        # 基础工程模板
        basic_template = self._create_basic_project_template()
        template_data["basic"] = {
            "file_path": str(self.templates_dir / "basic_project_template.xml"),
            "content": basic_template,
            "description": "基础剪映工程模板",
            "tracks": 2,
            "supports_version": "3.0+"
        }

        # 多轨道工程模板
        multi_track_template = self._create_multi_track_template()
        template_data["multi_track"] = {
            "file_path": str(self.templates_dir / "multi_track_template.xml"),
            "content": multi_track_template,
            "description": "多轨道剪映工程模板",
            "tracks": 4,
            "supports_version": "2.9+"
        }

        # 保存模板文件
        for template_type, data in template_data.items():
            with open(data["file_path"], 'w', encoding='utf-8') as f:
                f.write(data["content"])

        # 保存模板配置
        template_config_file = self.templates_dir / "template_config.json"
        with open(template_config_file, 'w', encoding='utf-8') as f:
            config_data = {}
            for key, value in template_data.items():
                config_data[key] = {k: v for k, v in value.items() if k != "content"}
            json.dump(config_data, f, indent=2, ensure_ascii=False)

        print(f"  生成剪映工程模板: {len(template_data)}个模板")
        return template_data

    def _create_basic_project_template(self) -> str:
        """创建基础工程模板"""
        template = '''<?xml version="1.0" encoding="UTF-8"?>
<project version="3.0">
    <settings>
        <width>1920</width>
        <height>1080</height>
        <fps>25</fps>
        <duration>120</duration>
    </settings>
    <timeline>
        <track id="video_track_1" type="video">
            <!-- Video clips will be inserted here -->
        </track>
        <track id="audio_track_1" type="audio">
            <!-- Audio clips will be inserted here -->
        </track>
    </timeline>
    <materials>
        <videos>
            <!-- Video materials will be listed here -->
        </videos>
        <audios>
            <!-- Audio materials will be listed here -->
        </audios>
    </materials>
</project>'''
        return template

    def _create_multi_track_template(self) -> str:
        """创建多轨道模板"""
        template = '''<?xml version="1.0" encoding="UTF-8"?>
<project version="2.9">
    <settings>
        <width>1920</width>
        <height>1080</height>
        <fps>25</fps>
        <duration>180</duration>
    </settings>
    <timeline>
        <track id="video_track_1" type="video" layer="1">
            <!-- Main video track -->
        </track>
        <track id="video_track_2" type="video" layer="2">
            <!-- Overlay video track -->
        </track>
        <track id="audio_track_1" type="audio" layer="1">
            <!-- Main audio track -->
        </track>
        <track id="audio_track_2" type="audio" layer="2">
            <!-- Background music track -->
        </track>
    </timeline>
    <materials>
        <videos>
            <!-- Video materials -->
        </videos>
        <audios>
            <!-- Audio materials -->
        </audios>
        <effects>
            <!-- Effects library -->
        </effects>
    </materials>
</project>'''
        return template

    def generate_test_scenarios(self):
        """生成测试场景配置"""
        print("生成测试场景配置...")

        scenarios = {
            "basic_clipping": {
                "name": "基础剪辑测试",
                "description": "测试基本的视频剪辑功能",
                "input_video": "standard_mp4",
                "input_subtitle": "viral",
                "expected_clips": 16,
                "max_precision_error": 0.5,
                "test_cases": [
                    "clip_generation_accuracy",
                    "timeline_structure_validation",
                    "material_library_completeness"
                ]
            },
            "multi_format_compatibility": {
                "name": "多格式兼容性测试",
                "description": "测试不同视频格式的兼容性",
                "input_videos": ["standard_mp4", "high_quality_mp4", "legacy_avi", "web_flv"],
                "input_subtitle": "original",
                "test_cases": [
                    "format_support_validation",
                    "quality_preservation_check",
                    "export_compatibility_test"
                ]
            },
            "precision_alignment": {
                "name": "精度对齐测试",
                "description": "测试高精度时间轴对齐",
                "input_video": "high_quality_mp4",
                "input_subtitle": "viral",
                "precision_requirements": {
                    "standard": 0.5,
                    "high": 0.2,
                    "ultra": 0.1
                },
                "test_cases": [
                    "sub_frame_accuracy_test",
                    "frame_boundary_alignment",
                    "audio_sync_validation"
                ]
            },
            "large_scale_processing": {
                "name": "大规模处理测试",
                "description": "测试大量片段的处理能力",
                "input_video": "standard_mp4",
                "input_subtitle": "original",
                "scale_parameters": {
                    "max_clips": 100,
                    "max_duration": 600,
                    "memory_limit_gb": 3.8
                },
                "test_cases": [
                    "memory_usage_monitoring",
                    "processing_speed_benchmark",
                    "stability_under_load"
                ]
            },
            "jianying_integration": {
                "name": "剪映集成测试",
                "description": "测试与剪映的完整集成",
                "input_video": "standard_mp4",
                "input_subtitle": "viral",
                "jianying_versions": ["3.0", "2.9", "2.8"],
                "test_cases": [
                    "project_file_generation",
                    "version_compatibility_check",
                    "import_success_validation",
                    "editing_functionality_test"
                ]
            }
        }

        # 保存测试场景配置
        scenarios_file = self.output_dir / "test_scenarios.json"
        with open(scenarios_file, 'w', encoding='utf-8') as f:
            json.dump(scenarios, f, indent=2, ensure_ascii=False)

        print(f"  生成测试场景配置: {len(scenarios)}个场景")
        return scenarios

    def generate_master_config(self, video_data, subtitle_data, template_data, scenario_data):
        """生成主配置文件"""
        print("生成主配置文件...")

        config = {
            "test_data_version": "1.0",
            "generated_time": datetime.now().isoformat(),
            "generator_info": {
                "name": "JianyingTestDataGenerator",
                "version": "1.0",
                "description": "VisionAI-ClipsMaster 剪映导出功能测试数据生成器"
            },
            "output_directories": {
                "root": str(self.output_dir),
                "videos": str(self.videos_dir),
                "subtitles": str(self.subtitles_dir),
                "projects": str(self.projects_dir),
                "templates": str(self.templates_dir)
            },
            "data_summary": {
                "video_formats": len(video_data),
                "subtitle_types": len(subtitle_data),
                "project_templates": len(template_data),
                "test_scenarios": len(scenario_data)
            },
            "validation_standards": {
                "clipping_precision": {
                    "standard": 0.5,
                    "high": 0.2,
                    "ultra": 0.1
                },
                "project_compatibility": {
                    "jianying_import_success_rate": 1.0,
                    "timeline_structure_validity": 1.0,
                    "material_mapping_accuracy": 1.0
                },
                "editing_functionality": {
                    "drag_adjustment_support": True,
                    "real_time_preview_support": True,
                    "clip_extension_support": True
                },
                "performance_requirements": {
                    "max_memory_usage_gb": 3.8,
                    "max_processing_time_per_minute": 30,
                    "min_clips_per_second": 2
                }
            },
            "test_execution_order": [
                "basic_clipping",
                "precision_alignment",
                "multi_format_compatibility",
                "jianying_integration",
                "large_scale_processing"
            ]
        }

        # 保存主配置文件
        master_config_file = self.output_dir / "master_test_config.json"
        with open(master_config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        print(f"  生成主配置文件: {master_config_file}")
        return config

    def _srt_time_to_seconds(self, time_str: str) -> float:
        """将SRT时间格式转换为秒数"""
        try:
            time_part, ms_part = time_str.split(',')
            h, m, s = map(int, time_part.split(':'))
            ms = int(ms_part)
            return h * 3600 + m * 60 + s + ms / 1000.0
        except:
            return 0.0

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="VisionAI-ClipsMaster 剪映导出测试数据生成器")
    parser.add_argument("--output-dir", "-o", help="输出目录", default=None)
    
    args = parser.parse_args()
    
    generator = JianyingTestDataGenerator(args.output_dir)
    config = generator.generate_all_test_data()
    
    print(f"\n剪映导出测试数据生成完成！")
    print(f"输出目录: {generator.output_dir}")
    print("\n生成的文件结构:")
    for root, dirs, files in os.walk(generator.output_dir):
        level = root.replace(str(generator.output_dir), '').count(os.sep)
        indent = ' ' * 2 * level
        print(f"{indent}{os.path.basename(root)}/")
        subindent = ' ' * 2 * (level + 1)
        for file in files:
            print(f"{subindent}{file}")

if __name__ == "__main__":
    main()
