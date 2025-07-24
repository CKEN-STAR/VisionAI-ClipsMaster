#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 测试数据生成器

此模块负责生成测试所需的各种数据，包括：
1. 模拟视频文件
2. 多语言字幕文件
3. 爆款参考字幕
4. 黄金标准测试数据
5. 边界条件测试用例
"""

import os
import sys
import json
import time
import logging
import random
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
import tempfile

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from src.utils.log_handler import LogHandler

logger = logging.getLogger(__name__)


@dataclass
class TestDataSpec:
    """测试数据规格"""
    language: str
    duration: int  # 秒
    subtitle_count: int
    complexity: str  # simple, medium, complex
    content_type: str  # drama, comedy, action, romance
    has_viral_version: bool = False


class TestDataGenerator:
    """测试数据生成器"""
    
    def __init__(self, config_path: str = None):
        """初始化测试数据生成器"""
        self.config = self._load_config(config_path)
        
        # 设置日志
        self.logger = LogHandler.get_logger(
            name=__name__,
            level=self.config.get('test_environment', {}).get('log_level', 'INFO')
        )
        
        # 创建输出目录
        self.output_dir = Path("test_data")
        self.output_dir.mkdir(exist_ok=True)
        
        # 创建子目录
        (self.output_dir / "videos").mkdir(exist_ok=True)
        (self.output_dir / "subtitles").mkdir(exist_ok=True)
        (self.output_dir / "viral_subtitles").mkdir(exist_ok=True)
        (self.output_dir / "golden_standards").mkdir(exist_ok=True)
        
        # 内容模板
        self.content_templates = self._load_content_templates()
        
        # 生成的文件记录
        self.generated_files = []
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """加载配置"""
        if config_path is None:
            config_path = "tests/core_functionality_validation/test_config.yaml"
        
        try:
            import yaml
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.logger.warning(f"无法加载配置文件 {config_path}: {e}")
            return {
                'test_data': {
                    'sample_count': 10,
                    'languages': ['zh', 'en', 'mixed'],
                    'video_durations': [300, 600, 1200],
                    'subtitle_complexity': ['simple', 'medium', 'complex']
                },
                'test_environment': {'log_level': 'INFO'}
            }
    
    def _load_content_templates(self) -> Dict[str, Dict]:
        """加载内容模板"""
        return {
            'zh': {
                'drama': {
                    'characters': ['小明', '小红', '老王', '李医生'],
                    'scenarios': ['医院', '学校', '家里', '公司'],
                    'emotions': ['开心', '难过', '愤怒', '惊讶'],
                    'plot_points': ['相遇', '冲突', '和解', '分别']
                },
                'comedy': {
                    'characters': ['阿呆', '小聪', '老板', '邻居'],
                    'scenarios': ['办公室', '餐厅', '商店', '公园'],
                    'emotions': ['搞笑', '尴尬', '兴奋', '困惑'],
                    'plot_points': ['误会', '笑话', '意外', '解决']
                }
            },
            'en': {
                'drama': {
                    'characters': ['John', 'Mary', 'Dr. Smith', 'Teacher'],
                    'scenarios': ['hospital', 'school', 'home', 'office'],
                    'emotions': ['happy', 'sad', 'angry', 'surprised'],
                    'plot_points': ['meeting', 'conflict', 'resolution', 'farewell']
                },
                'comedy': {
                    'characters': ['Bob', 'Alice', 'Boss', 'Neighbor'],
                    'scenarios': ['office', 'restaurant', 'store', 'park'],
                    'emotions': ['funny', 'awkward', 'excited', 'confused'],
                    'plot_points': ['misunderstanding', 'joke', 'accident', 'solution']
                }
            }
        }
    
    def generate_test_dataset(self, sample_count: int = None) -> List[Dict[str, str]]:
        """
        生成完整的测试数据集
        
        Args:
            sample_count: 样本数量，默认使用配置中的值
            
        Returns:
            List[Dict[str, str]]: 生成的文件路径列表
        """
        if sample_count is None:
            sample_count = self.config.get('test_data', {}).get('sample_count', 10)
        
        self.logger.info(f"开始生成测试数据集，样本数量: {sample_count}")
        
        generated_files = []
        
        # 生成各种类型的测试数据
        languages = self.config.get('test_data', {}).get('languages', ['zh', 'en', 'mixed'])
        durations = self.config.get('test_data', {}).get('video_durations', [300, 600, 1200])
        complexities = self.config.get('test_data', {}).get('subtitle_complexity', ['simple', 'medium', 'complex'])
        
        for i in range(sample_count):
            # 随机选择参数
            language = random.choice(languages)
            duration = random.choice(durations)
            complexity = random.choice(complexities)
            content_type = random.choice(['drama', 'comedy'])
            
            spec = TestDataSpec(
                language=language,
                duration=duration,
                subtitle_count=self._calculate_subtitle_count(duration, complexity),
                complexity=complexity,
                content_type=content_type,
                has_viral_version=random.choice([True, False])
            )
            
            # 生成测试用例
            test_case = self._generate_test_case(spec, i)
            generated_files.append(test_case)
        
        # 生成特殊测试用例
        special_cases = self._generate_special_test_cases()
        generated_files.extend(special_cases)
        
        self.generated_files = generated_files
        self.logger.info(f"测试数据集生成完成，共生成 {len(generated_files)} 个测试用例")
        
        return generated_files
    
    def _generate_test_case(self, spec: TestDataSpec, case_id: int) -> Dict[str, str]:
        """生成单个测试用例"""
        case_name = f"test_case_{case_id:03d}_{spec.language}_{spec.content_type}_{spec.complexity}"
        
        # 生成视频文件（模拟）
        video_file = self._generate_mock_video_file(case_name, spec)
        
        # 生成原片字幕
        original_subtitle_file = self._generate_original_subtitle(case_name, spec)
        
        # 生成爆款字幕（如果需要）
        viral_subtitle_file = None
        if spec.has_viral_version:
            viral_subtitle_file = self._generate_viral_subtitle(case_name, spec, original_subtitle_file)
        
        # 生成黄金标准数据
        golden_standard_file = self._generate_golden_standard(case_name, spec)
        
        return {
            'case_name': case_name,
            'video_file': video_file,
            'original_subtitle_file': original_subtitle_file,
            'viral_subtitle_file': viral_subtitle_file,
            'golden_standard_file': golden_standard_file,
            'spec': spec.__dict__
        }
    
    def _generate_mock_video_file(self, case_name: str, spec: TestDataSpec) -> str:
        """生成模拟视频文件"""
        video_file = self.output_dir / "videos" / f"{case_name}.mp4"
        
        # 创建模拟视频文件（实际项目中可能需要真实的视频文件）
        video_info = {
            'filename': video_file.name,
            'duration': spec.duration,
            'resolution': '1920x1080',
            'fps': 25,
            'format': 'mp4',
            'language': spec.language,
            'content_type': spec.content_type,
            'generated_at': time.time()
        }
        
        # 保存视频信息文件
        info_file = video_file.with_suffix('.info')
        with open(info_file, 'w', encoding='utf-8') as f:
            json.dump(video_info, f, ensure_ascii=False, indent=2)
        
        # 创建空的视频文件占位符
        with open(video_file, 'w') as f:
            f.write(f"# Mock video file for {case_name}\n")
            f.write(f"# Duration: {spec.duration} seconds\n")
            f.write(f"# Language: {spec.language}\n")
        
        return str(video_file)
    
    def _generate_original_subtitle(self, case_name: str, spec: TestDataSpec) -> str:
        """生成原片字幕文件"""
        subtitle_file = self.output_dir / "subtitles" / f"{case_name}.srt"
        
        # 根据规格生成字幕内容
        subtitles = self._create_subtitle_content(spec)
        
        # 保存字幕文件
        with open(subtitle_file, 'w', encoding='utf-8') as f:
            for i, subtitle in enumerate(subtitles, 1):
                f.write(f"{i}\n")
                f.write(f"{subtitle['start_time']} --> {subtitle['end_time']}\n")
                f.write(f"{subtitle['text']}\n\n")
        
        return str(subtitle_file)
    
    def _generate_viral_subtitle(self, case_name: str, spec: TestDataSpec, original_file: str) -> str:
        """生成爆款字幕文件"""
        viral_file = self.output_dir / "viral_subtitles" / f"{case_name}_viral.srt"
        
        # 读取原片字幕
        original_subtitles = self._parse_subtitle_file(original_file)
        
        # 生成爆款版本（压缩和优化）
        viral_subtitles = self._create_viral_version(original_subtitles, spec)
        
        # 保存爆款字幕文件
        with open(viral_file, 'w', encoding='utf-8') as f:
            for i, subtitle in enumerate(viral_subtitles, 1):
                f.write(f"{i}\n")
                f.write(f"{subtitle['start_time']} --> {subtitle['end_time']}\n")
                f.write(f"{subtitle['text']}\n\n")
        
        return str(viral_file)
    
    def _generate_golden_standard(self, case_name: str, spec: TestDataSpec) -> str:
        """生成黄金标准数据"""
        golden_file = self.output_dir / "golden_standards" / f"{case_name}_golden.json"
        
        # 创建黄金标准数据
        golden_data = {
            'case_name': case_name,
            'spec': spec.__dict__,
            'expected_results': {
                'characters': self._get_expected_characters(spec),
                'plot_points': self._get_expected_plot_points(spec),
                'emotional_arc': self._get_expected_emotional_arc(spec),
                'narrative_structure': self._get_expected_narrative_structure(spec),
                'key_scenes': self._get_expected_key_scenes(spec)
            },
            'quality_thresholds': {
                'timeline_accuracy': 0.5,
                'character_recognition_accuracy': 0.8,
                'plot_understanding_score': 0.85,
                'viral_features_match': 0.75
            }
        }
        
        # 保存黄金标准文件
        with open(golden_file, 'w', encoding='utf-8') as f:
            json.dump(golden_data, f, ensure_ascii=False, indent=2)
        
        return str(golden_file)
    
    def _generate_special_test_cases(self) -> List[Dict[str, str]]:
        """生成特殊测试用例"""
        special_cases = []
        
        # 边界条件测试用例
        boundary_cases = [
            {'name': 'empty_subtitle', 'type': 'empty'},
            {'name': 'single_subtitle', 'type': 'minimal'},
            {'name': 'very_long_subtitle', 'type': 'extreme_length'},
            {'name': 'invalid_timestamps', 'type': 'corrupted'},
            {'name': 'mixed_encoding', 'type': 'encoding_test'}
        ]
        
        for case in boundary_cases:
            special_case = self._generate_boundary_test_case(case['name'], case['type'])
            special_cases.append(special_case)
        
        return special_cases
    
    def _generate_boundary_test_case(self, case_name: str, case_type: str) -> Dict[str, str]:
        """生成边界条件测试用例"""
        if case_type == 'empty':
            return self._generate_empty_subtitle_case(case_name)
        elif case_type == 'minimal':
            return self._generate_minimal_subtitle_case(case_name)
        elif case_type == 'extreme_length':
            return self._generate_long_subtitle_case(case_name)
        elif case_type == 'corrupted':
            return self._generate_corrupted_subtitle_case(case_name)
        elif case_type == 'encoding_test':
            return self._generate_encoding_test_case(case_name)
        else:
            return self._generate_default_case(case_name)
    
    def _calculate_subtitle_count(self, duration: int, complexity: str) -> int:
        """根据时长和复杂度计算字幕数量"""
        base_count = duration // 5  # 每5秒一条字幕作为基准
        
        if complexity == 'simple':
            return int(base_count * 0.7)
        elif complexity == 'medium':
            return base_count
        elif complexity == 'complex':
            return int(base_count * 1.5)
        else:
            return base_count
    
    def _create_subtitle_content(self, spec: TestDataSpec) -> List[Dict[str, str]]:
        """创建字幕内容"""
        subtitles = []
        
        # 获取内容模板
        if spec.language == 'mixed':
            # 混合语言，随机选择中英文
            templates = [self.content_templates['zh'], self.content_templates['en']]
        else:
            templates = [self.content_templates.get(spec.language, self.content_templates['zh'])]
        
        # 生成字幕
        time_per_subtitle = spec.duration / spec.subtitle_count
        
        for i in range(spec.subtitle_count):
            start_time = i * time_per_subtitle
            end_time = (i + 1) * time_per_subtitle
            
            # 选择模板
            template = random.choice(templates)
            content_template = template.get(spec.content_type, template['drama'])
            
            # 生成字幕文本
            text = self._generate_subtitle_text(content_template, spec.complexity)
            
            subtitles.append({
                'start_time': self._format_timestamp(start_time),
                'end_time': self._format_timestamp(end_time),
                'text': text
            })
        
        return subtitles
    
    def _generate_subtitle_text(self, template: Dict, complexity: str) -> str:
        """生成字幕文本"""
        character = random.choice(template['characters'])
        scenario = random.choice(template['scenarios'])
        emotion = random.choice(template['emotions'])
        
        if complexity == 'simple':
            return f"{character}: 我在{scenario}感到{emotion}。"
        elif complexity == 'medium':
            action = random.choice(['走进', '离开', '看到', '听到'])
            return f"{character}: 我{action}{scenario}的时候感到{emotion}，这真是意外。"
        else:  # complex
            plot_point = random.choice(template['plot_points'])
            return f"{character}: 在{scenario}发生{plot_point}的时候，我感到{emotion}，这让我想起了过去的经历。"
    
    def _format_timestamp(self, seconds: float) -> str:
        """格式化时间戳"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"
    
    def _create_viral_version(self, original_subtitles: List[Dict], spec: TestDataSpec) -> List[Dict[str, str]]:
        """创建爆款版本字幕"""
        # 简化实现：选择关键字幕并调整时间
        viral_subtitles = []
        
        # 选择30%-70%的关键字幕
        compression_ratio = random.uniform(0.3, 0.7)
        selected_count = int(len(original_subtitles) * compression_ratio)
        
        # 选择关键字幕（简化：等间隔选择）
        step = len(original_subtitles) // selected_count if selected_count > 0 else 1
        selected_indices = list(range(0, len(original_subtitles), step))[:selected_count]
        
        # 重新调整时间轴
        new_duration = spec.duration * compression_ratio
        time_per_subtitle = new_duration / selected_count if selected_count > 0 else 0
        
        for i, original_index in enumerate(selected_indices):
            original_subtitle = original_subtitles[original_index]
            
            start_time = i * time_per_subtitle
            end_time = (i + 1) * time_per_subtitle
            
            # 优化文本（添加爆款元素）
            optimized_text = self._optimize_text_for_viral(original_subtitle['text'])
            
            viral_subtitles.append({
                'start_time': self._format_timestamp(start_time),
                'end_time': self._format_timestamp(end_time),
                'text': optimized_text
            })
        
        return viral_subtitles
    
    def _optimize_text_for_viral(self, text: str) -> str:
        """优化文本使其更具爆款特征"""
        # 简化实现：添加一些爆款关键词
        viral_prefixes = ['突然', '竟然', '没想到', '震惊', '意外发现']
        viral_suffixes = ['太意外了', '真是震惊', '完全没想到']
        
        if random.random() < 0.3:  # 30%概率添加前缀
            prefix = random.choice(viral_prefixes)
            text = f"{prefix}，{text}"
        
        if random.random() < 0.2:  # 20%概率添加后缀
            suffix = random.choice(viral_suffixes)
            text = f"{text}，{suffix}！"
        
        return text
    
    # 辅助方法
    def _parse_subtitle_file(self, file_path: str) -> List[Dict[str, str]]:
        """解析字幕文件"""
        subtitles = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 简化的SRT解析
            blocks = content.strip().split('\n\n')
            for block in blocks:
                lines = block.strip().split('\n')
                if len(lines) >= 3:
                    time_line = lines[1]
                    text = '\n'.join(lines[2:])
                    
                    if '-->' in time_line:
                        start_time, end_time = time_line.split(' --> ')
                        subtitles.append({
                            'start_time': start_time.strip(),
                            'end_time': end_time.strip(),
                            'text': text
                        })
        except Exception as e:
            self.logger.error(f"解析字幕文件失败: {file_path}, 错误: {str(e)}")
        
        return subtitles
    
    def _get_expected_characters(self, spec: TestDataSpec) -> List[str]:
        """获取期望的角色列表"""
        template = self.content_templates.get(spec.language, self.content_templates['zh'])
        content_template = template.get(spec.content_type, template['drama'])
        return content_template['characters'][:3]  # 返回前3个角色
    
    def _get_expected_plot_points(self, spec: TestDataSpec) -> List[Dict[str, Any]]:
        """获取期望的情节点"""
        template = self.content_templates.get(spec.language, self.content_templates['zh'])
        content_template = template.get(spec.content_type, template['drama'])
        
        plot_points = []
        for i, point in enumerate(content_template['plot_points']):
            plot_points.append({
                'type': point,
                'timestamp': (i + 1) * (spec.duration / len(content_template['plot_points'])),
                'importance': 0.8
            })
        
        return plot_points
    
    def _get_expected_emotional_arc(self, spec: TestDataSpec) -> List[Dict[str, Any]]:
        """获取期望的情感弧线"""
        emotions = [
            {'timestamp': 0, 'emotion_value': 0.5},
            {'timestamp': spec.duration * 0.25, 'emotion_value': 0.7},
            {'timestamp': spec.duration * 0.5, 'emotion_value': 0.3},
            {'timestamp': spec.duration * 0.75, 'emotion_value': 0.9},
            {'timestamp': spec.duration, 'emotion_value': 0.6}
        ]
        return emotions
    
    def _get_expected_narrative_structure(self, spec: TestDataSpec) -> Dict[str, Any]:
        """获取期望的叙事结构"""
        return {
            'beginning': {'start': 0, 'end': spec.duration * 0.25},
            'middle': {'start': spec.duration * 0.25, 'end': spec.duration * 0.75},
            'end': {'start': spec.duration * 0.75, 'end': spec.duration},
            'coherence_score': 0.85
        }
    
    def _get_expected_key_scenes(self, spec: TestDataSpec) -> List[Dict[str, Any]]:
        """获取期望的关键场景"""
        scenes = []
        scene_count = max(2, spec.duration // 300)  # 每5分钟一个关键场景
        
        for i in range(scene_count):
            scenes.append({
                'timestamp': (i + 1) * (spec.duration / scene_count),
                'importance': 0.8,
                'scene_type': 'key_moment'
            })
        
        return scenes
    
    # 边界条件测试用例生成方法
    def _generate_empty_subtitle_case(self, case_name: str) -> Dict[str, str]:
        """生成空字幕测试用例"""
        subtitle_file = self.output_dir / "subtitles" / f"{case_name}.srt"
        with open(subtitle_file, 'w', encoding='utf-8') as f:
            f.write("")  # 空文件
        
        return {
            'case_name': case_name,
            'video_file': "",
            'original_subtitle_file': str(subtitle_file),
            'viral_subtitle_file': None,
            'golden_standard_file': None,
            'spec': {'type': 'boundary_empty'}
        }
    
    def _generate_minimal_subtitle_case(self, case_name: str) -> Dict[str, str]:
        """生成最小字幕测试用例"""
        subtitle_file = self.output_dir / "subtitles" / f"{case_name}.srt"
        with open(subtitle_file, 'w', encoding='utf-8') as f:
            f.write("1\n00:00:00,000 --> 00:00:05,000\n单条字幕测试\n")
        
        return {
            'case_name': case_name,
            'video_file': "",
            'original_subtitle_file': str(subtitle_file),
            'viral_subtitle_file': None,
            'golden_standard_file': None,
            'spec': {'type': 'boundary_minimal'}
        }
    
    def _generate_long_subtitle_case(self, case_name: str) -> Dict[str, str]:
        """生成超长字幕测试用例"""
        subtitle_file = self.output_dir / "subtitles" / f"{case_name}.srt"
        long_text = "这是一个非常长的字幕内容，" * 50  # 创建很长的文本
        
        with open(subtitle_file, 'w', encoding='utf-8') as f:
            f.write(f"1\n00:00:00,000 --> 00:00:10,000\n{long_text}\n")
        
        return {
            'case_name': case_name,
            'video_file': "",
            'original_subtitle_file': str(subtitle_file),
            'viral_subtitle_file': None,
            'golden_standard_file': None,
            'spec': {'type': 'boundary_long'}
        }
    
    def _generate_corrupted_subtitle_case(self, case_name: str) -> Dict[str, str]:
        """生成损坏字幕测试用例"""
        subtitle_file = self.output_dir / "subtitles" / f"{case_name}.srt"
        corrupted_content = """1
invalid_timestamp --> 00:00:05,000
测试损坏的时间戳

2
00:00:05,000 --> invalid_end
另一个损坏的时间戳
"""
        
        with open(subtitle_file, 'w', encoding='utf-8') as f:
            f.write(corrupted_content)
        
        return {
            'case_name': case_name,
            'video_file': "",
            'original_subtitle_file': str(subtitle_file),
            'viral_subtitle_file': None,
            'golden_standard_file': None,
            'spec': {'type': 'boundary_corrupted'}
        }
    
    def _generate_encoding_test_case(self, case_name: str) -> Dict[str, str]:
        """生成编码测试用例"""
        subtitle_file = self.output_dir / "subtitles" / f"{case_name}.srt"
        mixed_content = """1
00:00:00,000 --> 00:00:05,000
测试Unicode: αβγδε ñáéíóú 😀😃😄

2
00:00:05,000 --> 00:00:10,000
Mixed content: 中文English日本語한국어
"""
        
        with open(subtitle_file, 'w', encoding='utf-8') as f:
            f.write(mixed_content)
        
        return {
            'case_name': case_name,
            'video_file': "",
            'original_subtitle_file': str(subtitle_file),
            'viral_subtitle_file': None,
            'golden_standard_file': None,
            'spec': {'type': 'boundary_encoding'}
        }
    
    def _generate_default_case(self, case_name: str) -> Dict[str, str]:
        """生成默认测试用例"""
        return {
            'case_name': case_name,
            'video_file': "",
            'original_subtitle_file': "",
            'viral_subtitle_file': None,
            'golden_standard_file': None,
            'spec': {'type': 'default'}
        }
    
    def generate_chinese_test_case(self) -> Tuple[str, str]:
        """生成中文测试用例"""
        spec = TestDataSpec(
            language='zh',
            duration=600,
            subtitle_count=120,
            complexity='medium',
            content_type='drama'
        )
        
        case = self._generate_test_case(spec, 9999)
        return case['video_file'], case['original_subtitle_file']
    
    def generate_english_test_case(self) -> Tuple[str, str]:
        """生成英文测试用例"""
        spec = TestDataSpec(
            language='en',
            duration=600,
            subtitle_count=120,
            complexity='medium',
            content_type='drama'
        )
        
        case = self._generate_test_case(spec, 9998)
        return case['video_file'], case['original_subtitle_file']
    
    def generate_mixed_language_test_case(self) -> Tuple[str, str]:
        """生成混合语言测试用例"""
        spec = TestDataSpec(
            language='mixed',
            duration=600,
            subtitle_count=120,
            complexity='medium',
            content_type='drama'
        )
        
        case = self._generate_test_case(spec, 9997)
        return case['video_file'], case['original_subtitle_file']
    
    def cleanup_generated_files(self):
        """清理生成的测试文件"""
        try:
            import shutil
            if self.output_dir.exists():
                shutil.rmtree(self.output_dir)
                self.logger.info("测试文件清理完成")
        except Exception as e:
            self.logger.error(f"清理测试文件失败: {str(e)}")


if __name__ == "__main__":
    # 测试数据生成器
    generator = TestDataGenerator()
    
    # 生成测试数据集
    test_files = generator.generate_test_dataset(sample_count=5)
    
    print("生成的测试文件:")
    for test_file in test_files:
        print(f"- {test_file['case_name']}: {test_file['original_subtitle_file']}")
    
    # 清理（可选）
    # generator.cleanup_generated_files()
