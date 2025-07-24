#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 端到端测试数据生成器

此模块生成完整的端到端测试数据集，包括原片视频、爆款SRT字幕、预期输出文件等。
支持多种测试场景，确保测试的全面性和真实性。
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
import uuid

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

# 导入核心模块
from src.utils.log_handler import LogHandler
from src.utils.file_checker import FileChecker

logger = logging.getLogger(__name__)


@dataclass
class E2ETestDataSet:
    """端到端测试数据集"""
    dataset_id: str
    scenario_type: str
    original_video_path: str
    viral_srt_path: str
    expected_segments_dir: str
    expected_draftinfo_path: str
    metadata: Dict[str, Any]
    creation_time: float


class E2EDataGenerator:
    """端到端测试数据生成器"""
    
    def __init__(self, config_path: str = None):
        """初始化端到端测试数据生成器"""
        self.config = self._load_config(config_path)
        
        # 设置日志
        self.logger = LogHandler.get_logger(
            name=__name__,
            level=self.config.get('test_environment', {}).get('log_level', 'INFO')
        )
        
        # 初始化组件
        self.file_checker = FileChecker()
        
        # 数据生成配置
        self.data_config = self.config.get('data_generation', {})
        self.generation_seed = self.data_config.get('generation_seed', 42)
        random.seed(self.generation_seed)
        
        # 测试场景配置
        self.scenarios = self.config.get('test_data', {}).get('test_scenarios', {})
        
        # 创建输出目录
        self.output_dir = Path(self.config.get('file_paths', {}).get('output', {}).get('reports_dir', 'tests/temp/e2e'))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成的数据集存储
        self.generated_datasets = []
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """加载配置"""
        if config_path is None:
            config_path = "tests/end_to_end_validation/e2e_config.yaml"
        
        try:
            import yaml
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.logger.warning(f"无法加载配置文件 {config_path}: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'test_environment': {'log_level': 'INFO'},
            'data_generation': {'generation_seed': 42},
            'test_data': {
                'test_scenarios': {
                    'basic': {'segment_count': 8, 'continuous_segments': True},
                    'complex': {'segment_count': 15, 'continuous_segments': False},
                    'boundary': {'segment_count': 3, 'edge_cases': True},
                    'stress': {'segment_count': 50, 'rapid_cuts': True}
                }
            },
            'file_paths': {'output': {'reports_dir': 'tests/temp/e2e'}}
        }
    
    def generate_complete_dataset(self, scenario_type: str = "basic") -> E2ETestDataSet:
        """
        生成完整的测试数据集
        
        Args:
            scenario_type: 测试场景类型
            
        Returns:
            E2ETestDataSet: 生成的测试数据集
        """
        dataset_id = f"e2e_dataset_{scenario_type}_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        
        self.logger.info(f"开始生成端到端测试数据集: {dataset_id}")
        
        try:
            # 创建数据集目录
            dataset_dir = self.output_dir / dataset_id
            dataset_dir.mkdir(exist_ok=True)
            
            # 生成原片视频
            original_video_path = self._generate_original_video(dataset_dir, scenario_type)
            
            # 生成爆款SRT字幕
            viral_srt_path = self._generate_viral_srt(dataset_dir, scenario_type, original_video_path)
            
            # 生成期望的视频片段
            expected_segments_dir = self._generate_expected_segments(dataset_dir, viral_srt_path, original_video_path)
            
            # 生成期望的剪映工程文件
            expected_draftinfo_path = self._generate_expected_draftinfo(dataset_dir, expected_segments_dir)
            
            # 生成元数据
            metadata = self._generate_metadata(scenario_type, dataset_dir)
            
            dataset = E2ETestDataSet(
                dataset_id=dataset_id,
                scenario_type=scenario_type,
                original_video_path=original_video_path,
                viral_srt_path=viral_srt_path,
                expected_segments_dir=expected_segments_dir,
                expected_draftinfo_path=expected_draftinfo_path,
                metadata=metadata,
                creation_time=time.time()
            )
            
            # 保存数据集信息
            self._save_dataset_info(dataset_dir, dataset)
            
            self.generated_datasets.append(dataset)
            self.logger.info(f"端到端测试数据集生成完成: {dataset_id}")
            
            return dataset
            
        except Exception as e:
            self.logger.error(f"生成端到端测试数据集失败: {str(e)}")
            raise
    
    def _generate_original_video(self, dataset_dir: Path, scenario_type: str) -> str:
        """生成原片视频"""
        scenario_config = self.scenarios.get(scenario_type, {})
        
        # 根据场景类型确定视频参数
        if scenario_type == "basic":
            duration = 60  # 1分钟
            resolution = "1280x720"
        elif scenario_type == "complex":
            duration = 300  # 5分钟
            resolution = "1920x1080"
        elif scenario_type == "boundary":
            duration = 30  # 30秒
            resolution = "640x480"
        elif scenario_type == "stress":
            duration = 600  # 10分钟
            resolution = "1920x1080"
        else:
            duration = 120  # 默认2分钟
            resolution = "1280x720"
        
        video_path = dataset_dir / "original_video.mp4"
        
        # 生成模拟视频文件
        # 在实际环境中，这里应该生成真实的视频文件
        video_metadata = {
            "duration": duration,
            "resolution": resolution,
            "fps": 30,
            "codec": "h264",
            "audio_codec": "aac",
            "file_size": duration * 1024 * 1024,  # 估算文件大小
            "creation_method": "synthetic"
        }
        
        # 创建模拟视频文件
        with open(video_path, 'wb') as f:
            # 写入一些模拟数据
            f.write(b"MOCK_VIDEO_DATA" * 1000)
        
        # 保存视频元数据
        metadata_path = dataset_dir / "original_video_metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(video_metadata, f, ensure_ascii=False, indent=2)
        
        self.logger.debug(f"生成原片视频: {video_path}")
        return str(video_path)
    
    def _generate_viral_srt(self, dataset_dir: Path, scenario_type: str, video_path: str) -> str:
        """生成爆款SRT字幕"""
        scenario_config = self.scenarios.get(scenario_type, {})
        segment_count = scenario_config.get('segment_count', 8)
        continuous_segments = scenario_config.get('continuous_segments', True)
        
        # 获取视频时长（从元数据中读取）
        metadata_path = dataset_dir / "original_video_metadata.json"
        with open(metadata_path, 'r', encoding='utf-8') as f:
            video_metadata = json.load(f)
        
        video_duration = video_metadata.get('duration', 120)
        
        # 生成时间段
        segments = self._generate_time_segments(segment_count, video_duration, continuous_segments, scenario_type)
        
        # 生成SRT内容
        srt_content = self._create_srt_content(segments, scenario_type)
        
        srt_path = dataset_dir / "viral_subtitles.srt"
        with open(srt_path, 'w', encoding='utf-8') as f:
            f.write(srt_content)
        
        self.logger.debug(f"生成爆款SRT字幕: {srt_path}, 片段数: {len(segments)}")
        return str(srt_path)
    
    def _generate_time_segments(self, segment_count: int, video_duration: float, 
                              continuous: bool, scenario_type: str) -> List[Dict[str, Any]]:
        """生成时间段"""
        segments = []
        
        if continuous:
            # 连续片段
            segment_duration = video_duration / segment_count
            for i in range(segment_count):
                start_time = i * segment_duration
                end_time = (i + 1) * segment_duration
                
                segments.append({
                    'start_seconds': start_time,
                    'end_seconds': end_time,
                    'duration': segment_duration
                })
        else:
            # 非连续片段
            available_time = video_duration
            used_time = 0
            
            for i in range(segment_count):
                # 随机选择片段时长
                if scenario_type == "boundary":
                    # 边界场景：极短或极长片段
                    if i % 2 == 0:
                        duration = random.uniform(0.5, 2.0)  # 极短片段
                    else:
                        duration = random.uniform(30, 60)    # 较长片段
                else:
                    duration = random.uniform(5, 30)  # 正常片段
                
                # 随机选择开始时间
                max_start = video_duration - duration
                if max_start > used_time:
                    start_time = random.uniform(used_time, max_start)
                else:
                    start_time = used_time
                
                end_time = start_time + duration
                used_time = end_time + random.uniform(1, 10)  # 添加间隔
                
                if end_time <= video_duration:
                    segments.append({
                        'start_seconds': start_time,
                        'end_seconds': end_time,
                        'duration': duration
                    })
        
        return segments[:segment_count]  # 确保不超过指定数量
    
    def _create_srt_content(self, segments: List[Dict[str, Any]], scenario_type: str) -> str:
        """创建SRT内容"""
        srt_lines = []
        
        # 根据场景类型生成不同的字幕文本
        text_templates = self._get_text_templates(scenario_type)
        
        for i, segment in enumerate(segments):
            # 序号
            srt_lines.append(str(i + 1))
            
            # 时间码
            start_timecode = self._seconds_to_timecode(segment['start_seconds'])
            end_timecode = self._seconds_to_timecode(segment['end_seconds'])
            srt_lines.append(f"{start_timecode} --> {end_timecode}")
            
            # 字幕文本
            text = random.choice(text_templates).format(index=i+1)
            srt_lines.append(text)
            
            # 空行分隔
            srt_lines.append("")
        
        return "\n".join(srt_lines)
    
    def _get_text_templates(self, scenario_type: str) -> List[str]:
        """获取字幕文本模板"""
        if scenario_type == "basic":
            return [
                "这是第{index}个基础测试片段",
                "基础场景片段{index}：正常内容",
                "测试片段{index}：标准格式"
            ]
        elif scenario_type == "complex":
            return [
                "复杂场景第{index}段：包含特殊字符！@#￥%",
                "片段{index}：多行\n字幕内容\n测试",
                "Complex segment {index}: Mixed language content",
                "第{index}个片段：emoji测试🎬🎭🎪"
            ]
        elif scenario_type == "boundary":
            return [
                "短{index}",
                "边界测试片段{index}：这是一个非常长的字幕文本，用于测试系统对长文本的处理能力和边界条件",
                ""  # 空字幕测试
            ]
        elif scenario_type == "stress":
            return [
                "压力测试片段{index}",
                "高频切换{index}",
                "快速剪切{index}"
            ]
        else:
            return ["测试片段{index}"]
    
    def _seconds_to_timecode(self, seconds: float) -> str:
        """将秒数转换为SRT时间码格式"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        milliseconds = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"
    
    def _generate_expected_segments(self, dataset_dir: Path, srt_path: str, video_path: str) -> str:
        """生成期望的视频片段"""
        segments_dir = dataset_dir / "expected_segments"
        segments_dir.mkdir(exist_ok=True)
        
        # 解析SRT文件获取片段信息
        with open(srt_path, 'r', encoding='utf-8') as f:
            srt_content = f.read()
        
        segments = self._parse_srt_segments(srt_content)
        
        # 为每个片段创建模拟文件
        for i, segment in enumerate(segments):
            segment_filename = f"segment_{i+1:03d}.mp4"
            segment_path = segments_dir / segment_filename
            
            # 创建模拟片段文件
            with open(segment_path, 'wb') as f:
                # 写入模拟数据，大小与时长成比例
                duration = segment['end_seconds'] - segment['start_seconds']
                data_size = int(duration * 100 * 1024)  # 每秒100KB
                f.write(b"MOCK_SEGMENT_DATA" * (data_size // 17))
        
        self.logger.debug(f"生成期望视频片段: {segments_dir}, 片段数: {len(segments)}")
        return str(segments_dir)
    
    def _parse_srt_segments(self, srt_content: str) -> List[Dict[str, Any]]:
        """解析SRT内容获取片段信息"""
        segments = []
        blocks = srt_content.strip().split('\n\n')
        
        for block in blocks:
            lines = block.strip().split('\n')
            if len(lines) >= 3:
                # 解析时间码
                timecode_line = lines[1]
                if '-->' in timecode_line:
                    start_str, end_str = timecode_line.split(' --> ')
                    start_seconds = self._timecode_to_seconds(start_str.strip())
                    end_seconds = self._timecode_to_seconds(end_str.strip())
                    
                    segments.append({
                        'start_seconds': start_seconds,
                        'end_seconds': end_seconds,
                        'text': '\n'.join(lines[2:])
                    })
        
        return segments
    
    def _timecode_to_seconds(self, timecode: str) -> float:
        """将时间码转换为秒数"""
        try:
            time_part, ms_part = timecode.split(',')
            hours, minutes, seconds = map(int, time_part.split(':'))
            milliseconds = int(ms_part)
            
            total_seconds = hours * 3600 + minutes * 60 + seconds + milliseconds / 1000.0
            return total_seconds
        except (ValueError, IndexError):
            return 0.0
    
    def _generate_expected_draftinfo(self, dataset_dir: Path, segments_dir: str) -> str:
        """生成期望的剪映工程文件"""
        segments_path = Path(segments_dir)
        segment_files = sorted(segments_path.glob("*.mp4"))
        
        # 创建剪映工程文件结构
        project_data = {
            "version": "3.0.0",
            "tracks": [
                {
                    "type": "video",
                    "segments": []
                }
            ],
            "materials": {},
            "canvas_config": {
                "width": 1920,
                "height": 1080,
                "fps": 30
            },
            "duration": 0
        }
        
        current_time = 0
        
        # 为每个片段创建轨道条目和素材条目
        for i, segment_file in enumerate(segment_files):
            material_id = f"material_{i+1}"
            
            # 估算片段时长（基于文件大小）
            file_size = segment_file.stat().st_size
            estimated_duration = max(1.0, file_size / (100 * 1024))  # 假设每秒100KB
            
            # 添加轨道片段
            project_data["tracks"][0]["segments"].append({
                "start": current_time,
                "end": current_time + estimated_duration,
                "material_id": material_id
            })
            
            # 添加素材
            project_data["materials"][material_id] = {
                "type": "video",
                "path": str(segment_file.absolute()),
                "duration": estimated_duration
            }
            
            current_time += estimated_duration
        
        project_data["duration"] = current_time
        
        # 保存工程文件
        draftinfo_path = dataset_dir / "expected_project.draftinfo"
        with open(draftinfo_path, 'w', encoding='utf-8') as f:
            json.dump(project_data, f, ensure_ascii=False, indent=2)
        
        self.logger.debug(f"生成期望剪映工程文件: {draftinfo_path}")
        return str(draftinfo_path)
    
    def _generate_metadata(self, scenario_type: str, dataset_dir: Path) -> Dict[str, Any]:
        """生成数据集元数据"""
        return {
            "scenario_type": scenario_type,
            "generation_time": time.time(),
            "generator_version": "1.0.0",
            "dataset_dir": str(dataset_dir),
            "scenario_config": self.scenarios.get(scenario_type, {}),
            "generation_seed": self.generation_seed,
            "files": {
                "original_video": "original_video.mp4",
                "viral_srt": "viral_subtitles.srt",
                "expected_segments_dir": "expected_segments",
                "expected_draftinfo": "expected_project.draftinfo"
            }
        }
    
    def _save_dataset_info(self, dataset_dir: Path, dataset: E2ETestDataSet):
        """保存数据集信息"""
        dataset_info = {
            "dataset_id": dataset.dataset_id,
            "scenario_type": dataset.scenario_type,
            "creation_time": dataset.creation_time,
            "files": {
                "original_video_path": dataset.original_video_path,
                "viral_srt_path": dataset.viral_srt_path,
                "expected_segments_dir": dataset.expected_segments_dir,
                "expected_draftinfo_path": dataset.expected_draftinfo_path
            },
            "metadata": dataset.metadata
        }
        
        info_path = dataset_dir / "dataset_info.json"
        with open(info_path, 'w', encoding='utf-8') as f:
            json.dump(dataset_info, f, ensure_ascii=False, indent=2)
    
    def generate_all_scenarios(self) -> List[E2ETestDataSet]:
        """生成所有测试场景的数据集"""
        datasets = []
        
        for scenario_type in self.scenarios.keys():
            try:
                dataset = self.generate_complete_dataset(scenario_type)
                datasets.append(dataset)
            except Exception as e:
                self.logger.error(f"生成场景 {scenario_type} 的数据集失败: {str(e)}")
        
        self.logger.info(f"生成了 {len(datasets)} 个测试数据集")
        return datasets


if __name__ == "__main__":
    # 示例用法
    generator = E2EDataGenerator()
    
    # 生成单个场景的数据集
    basic_dataset = generator.generate_complete_dataset("basic")
    print(f"生成基础场景数据集: {basic_dataset.dataset_id}")
    
    # 生成所有场景的数据集
    all_datasets = generator.generate_all_scenarios()
    print(f"生成了 {len(all_datasets)} 个数据集")
