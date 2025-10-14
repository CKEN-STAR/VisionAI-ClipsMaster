"""
剪映草稿生成器
基于pyCapCut的实现，生成标准的draft_content.json文件
"""

import json
import os
import uuid
from typing import Dict, List, Any, Optional
from pathlib import Path

try:
    from .jianying_time_converter import TimeConverter, Timerange
    from .jianying_material_manager import MaterialManager, VideoMaterial, AudioMaterial
    from .jianying_track_manager import TrackManager, Track, TrackType, VideoSegment, AudioSegment, TextSegment
except ImportError:
    from src.exporters.jianying_time_converter import TimeConverter, Timerange
    from src.exporters.jianying_material_manager import MaterialManager, VideoMaterial, AudioMaterial
    from src.exporters.jianying_track_manager import TrackManager, Track, TrackType, VideoSegment, AudioSegment, TextSegment


class JianyingDraftGenerator:
    """剪映草稿生成器 - 主类"""
    
    def __init__(self, width: int = 1920, height: int = 1080, fps: int = 30):
        """
        初始化草稿生成器
        
        Args:
            width: 画布宽度
            height: 画布高度
            fps: 帧率
        """
        self.width = width
        self.height = height
        self.fps = fps
        self.duration = 0  # 总时长（微秒）
        
        # 初始化管理器
        self.material_manager = MaterialManager()
        self.track_manager = TrackManager()
        
        # 草稿内容模板
        self.content: Dict[str, Any] = {
            "canvas_config": {
                "height": self.height,
                "ratio": "original",
                "width": self.width
            },
            "color_space": 0,
            "config": {
                "export_range": {
                    "duration": 0,
                    "start": 0
                },
                "fps": self.fps,
                "height": self.height,
                "width": self.width
            },
            "create_time": 0,
            "duration": 0,
            "extra_info": "",
            "fps": self.fps,
            "id": uuid.uuid4().hex,
            "keyframe_graph_list": [],
            "last_modified_platform": {
                "app_id": "1233",
                "app_source": "lv",
                "app_version": "5.9.0",
                "device_id": uuid.uuid4().hex,
                "hard_disk_id": "",
                "mac_address": "",
                "os": "windows",
                "os_version": "10.0.22631"
            },
            "materials": {},
            "name": "",
            "new_version": "5.9.0",
            "platform": "windows",
            "relationships": [],
            "tracks": [],
            "update_time": 0,
            "version": 2
        }
    
    def add_video_segment(self, video_path: str, 
                         start_time: float, 
                         end_time: float,
                         target_start: float,
                         speed: float = 1.0,
                         volume: float = 1.0,
                         track: Optional[Track] = None) -> VideoSegment:
        """
        添加视频片段
        
        Args:
            video_path: 视频文件路径
            start_time: 源视频开始时间（秒）
            end_time: 源视频结束时间（秒）
            target_start: 目标时间轴开始时间（秒）
            speed: 播放速度
            volume: 音量
            track: 指定轨道（None则自动创建）
            
        Returns:
            VideoSegment对象
        """
        # 添加素材
        material = self.material_manager.add_video_material(video_path)
        
        # 创建时间范围
        source_timerange = TimeConverter.create_timerange(
            start=start_time,
            end=end_time
        )
        
        # 计算目标时长（考虑速度）
        # 注意：source_timerange.duration已经是微秒，不需要再转换
        target_duration_us = int(source_timerange.duration / speed)
        target_start_us = TimeConverter.tim(target_start)
        target_timerange = Timerange(
            start=target_start_us,
            duration=target_duration_us
        )
        
        # 创建片段
        segment = VideoSegment(
            material_id=material.material_id,
            source_timerange=source_timerange,
            target_timerange=target_timerange,
            speed=speed,
            volume=volume
        )
        
        # 添加到轨道
        if track is None:
            # 查找或创建视频轨道
            video_tracks = [t for t in self.track_manager.tracks if t.track_type == TrackType.VIDEO]
            if not video_tracks:
                track = self.track_manager.create_track(TrackType.VIDEO)
            else:
                track = video_tracks[0]
        
        track.add_segment(segment)
        
        # 更新总时长
        self._update_duration()
        
        return segment
    
    def add_audio_segment(self, audio_path: str,
                         start_time: float,
                         end_time: float,
                         target_start: float,
                         speed: float = 1.0,
                         volume: float = 1.0,
                         track: Optional[Track] = None) -> AudioSegment:
        """
        添加音频片段
        
        Args:
            audio_path: 音频文件路径
            start_time: 源音频开始时间（秒）
            end_time: 源音频结束时间（秒）
            target_start: 目标时间轴开始时间（秒）
            speed: 播放速度
            volume: 音量
            track: 指定轨道（None则自动创建）
            
        Returns:
            AudioSegment对象
        """
        # 添加素材
        material = self.material_manager.add_audio_material(audio_path)
        
        # 创建时间范围
        source_timerange = TimeConverter.create_timerange(
            start=start_time,
            end=end_time
        )
        
        # 计算目标时长（考虑速度）
        # 注意：source_timerange.duration已经是微秒，不需要再转换
        target_duration_us = int(source_timerange.duration / speed)
        target_start_us = TimeConverter.tim(target_start)
        target_timerange = Timerange(
            start=target_start_us,
            duration=target_duration_us
        )
        
        # 创建片段
        segment = AudioSegment(
            material_id=material.material_id,
            source_timerange=source_timerange,
            target_timerange=target_timerange,
            speed=speed,
            volume=volume
        )
        
        # 添加到轨道
        if track is None:
            # 查找或创建音频轨道
            audio_tracks = [t for t in self.track_manager.tracks if t.track_type == TrackType.AUDIO]
            if not audio_tracks:
                track = self.track_manager.create_track(TrackType.AUDIO)
            else:
                track = audio_tracks[0]
        
        track.add_segment(segment)
        
        # 更新总时长
        self._update_duration()
        
        return segment
    
    def _update_duration(self):
        """更新总时长"""
        max_end_time = 0
        for track in self.track_manager.tracks:
            if track.end_time > max_end_time:
                max_end_time = track.end_time
        self.duration = max_end_time
    
    def dumps(self) -> str:
        """
        导出为JSON字符串
        
        Returns:
            draft_content.json的JSON字符串
        """
        # 更新基本信息
        self.content["fps"] = self.fps
        self.content["duration"] = self.duration
        self.content["canvas_config"] = {
            "width": self.width,
            "height": self.height,
            "ratio": "original"
        }
        self.content["config"]["fps"] = self.fps
        self.content["config"]["width"] = self.width
        self.content["config"]["height"] = self.height
        self.content["config"]["export_range"]["duration"] = self.duration
        
        # 导出素材
        self.content["materials"] = self.material_manager.export_all_materials()
        
        # 导出轨道
        self.content["tracks"] = self.track_manager.export_all_tracks()
        
        return json.dumps(self.content, ensure_ascii=False, indent=4)
    
    def save(self, output_path: str):
        """
        保存为draft_content.json文件
        
        Args:
            output_path: 输出文件路径
        """
        # 确保目录存在
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        # 写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(self.dumps())
    
    def create_draft_folder(self, output_dir: str, project_name: str = "VisionAI_Project") -> str:
        """
        创建完整的剪映草稿文件夹
        
        Args:
            output_dir: 输出目录
            project_name: 项目名称
            
        Returns:
            草稿文件夹路径
        """
        # 创建草稿文件夹
        draft_folder = os.path.join(output_dir, project_name)
        os.makedirs(draft_folder, exist_ok=True)
        
        # 保存draft_content.json
        draft_content_path = os.path.join(draft_folder, "draft_content.json")
        self.save(draft_content_path)
        
        # 创建draft_meta_info.json
        meta_info = {
            "draft_fold_path": draft_folder,
            "draft_id": self.content["id"],
            "draft_name": project_name,
            "draft_removable_storage_device": "",
            "tm_draft_create": 0,
            "tm_draft_modified": 0,
            "tm_duration": self.duration
        }
        
        meta_info_path = os.path.join(draft_folder, "draft_meta_info.json")
        with open(meta_info_path, 'w', encoding='utf-8') as f:
            json.dump(meta_info, f, ensure_ascii=False, indent=4)
        
        return draft_folder

