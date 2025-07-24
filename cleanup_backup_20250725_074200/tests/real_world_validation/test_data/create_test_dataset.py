#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 真实测试数据集创建器

此模块创建用于真实环境测试的标准化测试数据集，
包括不同类型、时长、分辨率的测试视频文件和相关元数据。
"""

import os
import sys
import json
import time
import logging
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from src.utils.log_handler import LogHandler

logger = logging.getLogger(__name__)


@dataclass
class TestVideoSpec:
    """测试视频规格"""
    name: str
    duration: int  # 秒
    resolution: str
    format: str
    codec: str
    audio_codec: str
    language: str
    content_type: str
    file_size_mb: int
    description: str


@dataclass
class TestDataset:
    """测试数据集"""
    dataset_id: str
    creation_time: float
    videos: List[TestVideoSpec]
    metadata: Dict[str, Any]
    validation_data: Dict[str, Any]


class RealWorldTestDatasetCreator:
    """真实世界测试数据集创建器"""
    
    def __init__(self, config_path: str = None):
        """初始化测试数据集创建器"""
        self.config = self._load_config(config_path)
        
        # 设置日志
        self.logger = LogHandler.get_logger(
            name=__name__,
            level=self.config.get('test_environment', {}).get('log_level', 'INFO')
        )
        
        # 数据集配置
        self.dataset_config = self.config.get('test_data', {})
        
        # 创建输出目录
        self.output_dir = Path("tests/real_world_validation/test_data")
        self.videos_dir = self.output_dir / "videos"
        self.reference_dir = self.output_dir / "reference_data"
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.videos_dir.mkdir(parents=True, exist_ok=True)
        self.reference_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """加载配置"""
        if config_path is None:
            config_path = "tests/real_world_validation/real_world_config.yaml"
        
        try:
            import yaml
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.warning(f"无法加载配置文件 {config_path}: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'test_environment': {'log_level': 'INFO'},
            'test_data': {
                'video_files': {
                    'short_video': {
                        'duration': 300, 'resolution': '1920x1080', 'format': 'mp4',
                        'language': 'zh', 'content_type': 'educational'
                    },
                    'medium_video': {
                        'duration': 900, 'resolution': '1280x720', 'format': 'mov',
                        'language': 'zh-en', 'content_type': 'entertainment'
                    },
                    'long_video': {
                        'duration': 1800, 'resolution': '1920x1080', 'format': 'avi',
                        'language': 'en', 'content_type': 'tutorial'
                    }
                }
            }
        }
    
    def create_complete_test_dataset(self) -> TestDataset:
        """创建完整的测试数据集"""
        dataset_id = f"real_world_dataset_{int(time.time())}"
        
        self.logger.info(f"开始创建真实世界测试数据集: {dataset_id}")
        
        # 定义测试视频规格
        video_specs = self._define_test_video_specs()
        
        # 创建测试视频文件
        created_videos = []
        for spec in video_specs:
            try:
                video_file_path = self._create_test_video(spec)
                if video_file_path:
                    spec.name = str(video_file_path)  # 更新为实际路径
                    created_videos.append(spec)
                    self.logger.info(f"创建测试视频: {spec.name}")
            except Exception as e:
                self.logger.error(f"创建测试视频失败: {spec.name}, 错误: {str(e)}")
        
        # 创建参考数据
        validation_data = self._create_validation_data(created_videos)
        
        # 创建数据集元数据
        metadata = self._create_dataset_metadata(created_videos)
        
        # 保存数据集信息
        dataset = TestDataset(
            dataset_id=dataset_id,
            creation_time=time.time(),
            videos=created_videos,
            metadata=metadata,
            validation_data=validation_data
        )
        
        self._save_dataset_info(dataset)
        
        self.logger.info(f"测试数据集创建完成: {dataset_id}, 包含 {len(created_videos)} 个视频")
        
        return dataset
    
    def _define_test_video_specs(self) -> List[TestVideoSpec]:
        """定义测试视频规格"""
        video_configs = self.dataset_config.get('video_files', {})
        
        specs = []
        
        # 短视频 (5分钟)
        short_config = video_configs.get('short_video', {})
        specs.append(TestVideoSpec(
            name="short_video_5min.mp4",
            duration=short_config.get('duration', 300),
            resolution=short_config.get('resolution', '1920x1080'),
            format=short_config.get('format', 'mp4'),
            codec="h264",
            audio_codec="aac",
            language=short_config.get('language', 'zh'),
            content_type=short_config.get('content_type', 'educational'),
            file_size_mb=150,
            description="5分钟教育类中文视频，用于测试基本功能"
        ))
        
        # 中等视频 (15分钟)
        medium_config = video_configs.get('medium_video', {})
        specs.append(TestVideoSpec(
            name="medium_video_15min.mov",
            duration=medium_config.get('duration', 900),
            resolution=medium_config.get('resolution', '1280x720'),
            format=medium_config.get('format', 'mov'),
            codec="h265",
            audio_codec="aac",
            language=medium_config.get('language', 'zh-en'),
            content_type=medium_config.get('content_type', 'entertainment'),
            file_size_mb=400,
            description="15分钟娱乐类中英混合视频，用于测试复杂场景"
        ))
        
        # 长视频 (30分钟)
        long_config = video_configs.get('long_video', {})
        specs.append(TestVideoSpec(
            name="long_video_30min.avi",
            duration=long_config.get('duration', 1800),
            resolution=long_config.get('resolution', '1920x1080'),
            format=long_config.get('format', 'avi'),
            codec="h264",
            audio_codec="mp3",
            language=long_config.get('language', 'en'),
            content_type=long_config.get('content_type', 'tutorial'),
            file_size_mb=800,
            description="30分钟教程类英文视频，用于测试长时间处理"
        ))
        
        # 高分辨率视频 (4K)
        specs.append(TestVideoSpec(
            name="4k_video_10min.mp4",
            duration=600,
            resolution="3840x2160",
            format="mp4",
            codec="h265",
            audio_codec="aac",
            language="zh",
            content_type="demo",
            file_size_mb=1200,
            description="10分钟4K分辨率视频，用于测试高分辨率处理"
        ))
        
        # 低分辨率视频 (480p)
        specs.append(TestVideoSpec(
            name="low_res_video_8min.mp4",
            duration=480,
            resolution="854x480",
            format="mp4",
            codec="h264",
            audio_codec="aac",
            language="zh",
            content_type="mobile",
            file_size_mb=80,
            description="8分钟低分辨率视频，用于测试移动端兼容性"
        ))
        
        return specs
    
    def _create_test_video(self, spec: TestVideoSpec) -> Optional[str]:
        """创建测试视频文件"""
        try:
            video_path = self.videos_dir / spec.name
            
            # 检查是否已存在
            if video_path.exists():
                self.logger.info(f"测试视频已存在: {video_path}")
                return str(video_path)
            
            # 使用FFmpeg创建测试视频
            success = self._generate_video_with_ffmpeg(spec, str(video_path))
            
            if success and video_path.exists():
                return str(video_path)
            else:
                # 如果FFmpeg不可用，创建占位符文件
                return self._create_placeholder_video(spec, str(video_path))
                
        except Exception as e:
            self.logger.error(f"创建测试视频失败: {spec.name}, 错误: {str(e)}")
            return None
    
    def _generate_video_with_ffmpeg(self, spec: TestVideoSpec, output_path: str) -> bool:
        """使用FFmpeg生成测试视频"""
        try:
            import subprocess
            
            # 解析分辨率
            width, height = spec.resolution.split('x')
            
            # 构建FFmpeg命令
            cmd = [
                'ffmpeg',
                '-f', 'lavfi',
                '-i', f'testsrc2=duration={spec.duration}:size={spec.resolution}:rate=30',
                '-f', 'lavfi',
                '-i', f'sine=frequency=1000:duration={spec.duration}',
                '-c:v', 'libx264' if spec.codec == 'h264' else 'libx265',
                '-c:a', 'aac' if spec.audio_codec == 'aac' else 'mp3',
                '-preset', 'fast',
                '-y',  # 覆盖输出文件
                output_path
            ]
            
            # 执行FFmpeg命令
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                self.logger.debug(f"FFmpeg成功生成视频: {output_path}")
                return True
            else:
                self.logger.warning(f"FFmpeg生成视频失败: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error(f"FFmpeg生成视频超时: {output_path}")
            return False
        except FileNotFoundError:
            self.logger.warning("FFmpeg未找到，将创建占位符文件")
            return False
        except Exception as e:
            self.logger.error(f"FFmpeg生成视频异常: {str(e)}")
            return False
    
    def _create_placeholder_video(self, spec: TestVideoSpec, output_path: str) -> str:
        """创建占位符视频文件"""
        try:
            # 创建一个包含视频元数据的占位符文件
            placeholder_data = {
                'type': 'placeholder_video',
                'spec': {
                    'name': spec.name,
                    'duration': spec.duration,
                    'resolution': spec.resolution,
                    'format': spec.format,
                    'codec': spec.codec,
                    'audio_codec': spec.audio_codec,
                    'language': spec.language,
                    'content_type': spec.content_type,
                    'file_size_mb': spec.file_size_mb,
                    'description': spec.description
                },
                'note': '这是一个占位符文件，用于测试环境中没有FFmpeg的情况',
                'creation_time': time.time()
            }
            
            # 写入占位符数据
            with open(output_path + '.placeholder.json', 'w', encoding='utf-8') as f:
                json.dump(placeholder_data, f, ensure_ascii=False, indent=2)
            
            # 创建一个小的二进制文件作为占位符
            placeholder_size = min(spec.file_size_mb * 1024 * 1024, 1024 * 1024)  # 最大1MB
            with open(output_path, 'wb') as f:
                f.write(b'PLACEHOLDER_VIDEO_DATA' * (placeholder_size // 22))
            
            self.logger.info(f"创建占位符视频: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"创建占位符视频失败: {str(e)}")
            return None
    
    def _create_validation_data(self, videos: List[TestVideoSpec]) -> Dict[str, Any]:
        """创建验证数据"""
        validation_data = {
            'expected_results': {},
            'quality_benchmarks': {},
            'performance_baselines': {}
        }
        
        for video in videos:
            video_id = Path(video.name).stem
            
            # 期望的AI分析结果
            validation_data['expected_results'][video_id] = {
                'content_type': video.content_type,
                'language': video.language,
                'duration': video.duration,
                'expected_scenes': self._estimate_scene_count(video),
                'expected_segments': self._estimate_segment_count(video),
                'compression_ratio_range': [0.3, 0.7]
            }
            
            # 质量基准
            validation_data['quality_benchmarks'][video_id] = {
                'min_ai_confidence': 0.8,
                'min_viral_score': 0.7,
                'max_cutting_error_seconds': 0.5,
                'min_timeline_accuracy': 0.95
            }
            
            # 性能基准
            validation_data['performance_baselines'][video_id] = {
                'max_processing_time_seconds': video.duration * 2,  # 2x实时速度
                'max_memory_usage_mb': 2048,
                'max_cpu_usage_percent': 80
            }
        
        return validation_data
    
    def _estimate_scene_count(self, video: TestVideoSpec) -> int:
        """估算场景数量"""
        # 基于视频时长和内容类型估算场景数
        base_scenes = max(1, video.duration // 60)  # 每分钟至少1个场景
        
        if video.content_type == 'educational':
            return base_scenes
        elif video.content_type == 'entertainment':
            return base_scenes * 2  # 娱乐类场景变化更频繁
        elif video.content_type == 'tutorial':
            return base_scenes
        else:
            return base_scenes
    
    def _estimate_segment_count(self, video: TestVideoSpec) -> int:
        """估算片段数量"""
        # 基于视频时长估算爆款片段数量
        if video.duration <= 300:  # 5分钟以内
            return min(8, max(3, video.duration // 30))
        elif video.duration <= 900:  # 15分钟以内
            return min(15, max(8, video.duration // 60))
        else:  # 更长视频
            return min(25, max(15, video.duration // 90))
    
    def _create_dataset_metadata(self, videos: List[TestVideoSpec]) -> Dict[str, Any]:
        """创建数据集元数据"""
        return {
            'dataset_version': '1.0.0',
            'creation_tool': 'VisionAI-ClipsMaster Test Dataset Creator',
            'creation_time': time.time(),
            'total_videos': len(videos),
            'total_duration_seconds': sum(v.duration for v in videos),
            'total_size_mb': sum(v.file_size_mb for v in videos),
            'video_formats': list(set(v.format for v in videos)),
            'resolutions': list(set(v.resolution for v in videos)),
            'languages': list(set(v.language for v in videos)),
            'content_types': list(set(v.content_type for v in videos)),
            'purpose': 'Real-world end-to-end testing for VisionAI-ClipsMaster',
            'usage_instructions': {
                'setup': 'Place video files in tests/real_world_validation/test_data/videos/',
                'execution': 'Run python tests/real_world_validation/run_real_world_e2e_test.py',
                'cleanup': 'Remove temporary files after testing'
            }
        }
    
    def _save_dataset_info(self, dataset: TestDataset):
        """保存数据集信息"""
        try:
            # 保存数据集信息
            dataset_info_path = self.output_dir / "dataset_info.json"
            dataset_info = {
                'dataset_id': dataset.dataset_id,
                'creation_time': dataset.creation_time,
                'metadata': dataset.metadata,
                'videos': [
                    {
                        'name': v.name,
                        'duration': v.duration,
                        'resolution': v.resolution,
                        'format': v.format,
                        'codec': v.codec,
                        'audio_codec': v.audio_codec,
                        'language': v.language,
                        'content_type': v.content_type,
                        'file_size_mb': v.file_size_mb,
                        'description': v.description
                    }
                    for v in dataset.videos
                ]
            }
            
            with open(dataset_info_path, 'w', encoding='utf-8') as f:
                json.dump(dataset_info, f, ensure_ascii=False, indent=2)
            
            # 保存验证数据
            validation_data_path = self.reference_dir / "validation_data.json"
            with open(validation_data_path, 'w', encoding='utf-8') as f:
                json.dump(dataset.validation_data, f, ensure_ascii=False, indent=2)
            
            # 创建README文件
            readme_path = self.output_dir / "README.md"
            self._create_readme_file(readme_path, dataset)
            
            self.logger.info(f"数据集信息已保存: {dataset_info_path}")
            
        except Exception as e:
            self.logger.error(f"保存数据集信息失败: {str(e)}")
    
    def _create_readme_file(self, readme_path: Path, dataset: TestDataset):
        """创建README文件"""
        readme_content = f"""# VisionAI-ClipsMaster 真实世界测试数据集

## 数据集信息
- **数据集ID**: {dataset.dataset_id}
- **创建时间**: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(dataset.creation_time))}
- **视频数量**: {len(dataset.videos)}
- **总时长**: {sum(v.duration for v in dataset.videos) // 60} 分钟
- **总大小**: {sum(v.file_size_mb for v in dataset.videos)} MB

## 视频文件列表

| 文件名 | 时长 | 分辨率 | 格式 | 语言 | 内容类型 | 描述 |
|--------|------|--------|------|------|----------|------|
"""
        
        for video in dataset.videos:
            duration_str = f"{video.duration // 60}:{video.duration % 60:02d}"
            readme_content += f"| {Path(video.name).name} | {duration_str} | {video.resolution} | {video.format.upper()} | {video.language} | {video.content_type} | {video.description} |\n"
        
        readme_content += f"""
## 使用说明

### 环境要求
- Python 3.8+
- VisionAI-ClipsMaster 系统
- 4GB+ 可用内存
- FFmpeg (可选，用于视频处理)

### 运行测试
```bash
# 完整端到端测试
python tests/real_world_validation/run_real_world_e2e_test.py

# 指定视频文件测试
python tests/real_world_validation/run_real_world_e2e_test.py --videos short_video_5min.mp4

# 性能测试
python tests/real_world_validation/run_real_world_e2e_test.py --performance-test
```

### 验证数据
参考数据位于 `reference_data/validation_data.json`，包含：
- 期望的AI分析结果
- 质量基准指标
- 性能基线数据

### 注意事项
1. 确保所有视频文件都在 `videos/` 目录中
2. 测试过程中会产生临时文件，测试完成后会自动清理
3. 如果使用占位符文件，某些测试可能会跳过
4. 建议在测试前检查系统资源使用情况

## 数据集更新
如需更新数据集，请运行：
```bash
python tests/real_world_validation/test_data/create_test_dataset.py
```

生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)


def main():
    """主函数"""
    creator = RealWorldTestDatasetCreator()
    
    print("开始创建VisionAI-ClipsMaster真实世界测试数据集...")
    
    dataset = creator.create_complete_test_dataset()
    
    print(f"\n数据集创建完成!")
    print(f"数据集ID: {dataset.dataset_id}")
    print(f"视频数量: {len(dataset.videos)}")
    print(f"总时长: {sum(v.duration for v in dataset.videos) // 60} 分钟")
    print(f"总大小: {sum(v.file_size_mb for v in dataset.videos)} MB")
    
    print(f"\n文件位置:")
    print(f"- 视频文件: tests/real_world_validation/test_data/videos/")
    print(f"- 验证数据: tests/real_world_validation/test_data/reference_data/")
    print(f"- 数据集信息: tests/real_world_validation/test_data/dataset_info.json")
    
    print(f"\n使用方法:")
    print(f"python tests/real_world_validation/run_real_world_e2e_test.py")


if __name__ == "__main__":
    main()
