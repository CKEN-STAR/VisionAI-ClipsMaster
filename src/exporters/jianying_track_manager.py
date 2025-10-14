"""
剪映轨道管理器
管理视频、音频、文本轨道
"""

import uuid
from typing import Dict, List, Any, Literal, Optional
from dataclasses import dataclass, field
from enum import Enum

try:
    from .jianying_time_converter import Timerange
except ImportError:
    from src.exporters.jianying_time_converter import Timerange


class TrackType(Enum):
    """轨道类型枚举"""
    VIDEO = "video"
    AUDIO = "audio"
    TEXT = "text"
    EFFECT = "effect"
    FILTER = "filter"
    STICKER = "sticker"


@dataclass
class BaseSegment:
    """片段基类"""
    material_id: str
    """关联的素材ID"""
    target_timerange: Timerange
    """片段在时间轴上的时间范围"""
    segment_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    """片段ID"""
    
    def overlaps(self, other: 'BaseSegment') -> bool:
        """检查是否与另一个片段重叠"""
        return not (self.target_timerange.end <= other.target_timerange.start or
                   other.target_timerange.end <= self.target_timerange.start)


@dataclass
class VideoSegment(BaseSegment):
    """视频片段"""
    source_timerange: Optional[Timerange] = None
    """素材中的源时间范围"""
    speed: float = 1.0
    """播放速度"""
    volume: float = 1.0
    """音量"""
    render_index: int = 0
    """渲染索引"""
    
    # 变换参数
    scale_x: float = 1.0
    scale_y: float = 1.0
    rotation: float = 0.0
    position_x: float = 0.0
    position_y: float = 0.0
    
    def export_json(self) -> Dict[str, Any]:
        """导出为剪映JSON格式"""
        # 如果没有指定源时间范围，使用目标时间范围
        if self.source_timerange is None:
            source_start = 0
            source_duration = round(self.target_timerange.duration * self.speed)
        else:
            source_start = self.source_timerange.start
            source_duration = self.source_timerange.duration
        
        return {
            "cartoon": False,
            "clip": {
                "alpha": 1.0,
                "flip": {"horizontal": False, "vertical": False},
                "rotation": self.rotation,
                "scale": {"x": self.scale_x, "y": self.scale_y},
                "transform": {"x": self.position_x, "y": self.position_y}
            },
            "common_keyframes": [],
            "enable_adjust": True,
            "enable_color_curves": True,
            "enable_color_match_adjust": False,
            "enable_color_wheels": True,
            "enable_lut": True,
            "enable_smart_color_adjust": False,
            "extra_material_refs": [],
            "group_id": "",
            "hdr_settings": {"intensity": 1.0, "mode": 1, "nits": 1000},
            "id": self.segment_id,
            "intensifies_audio": False,
            "is_placeholder": False,
            "is_tone_modify": False,
            "keyframe_refs": [],
            "last_nonzero_volume": 1.0,
            "material_id": self.material_id,
            "render_index": self.render_index,
            "reverse": False,
            "source_timerange": {
                "duration": source_duration,
                "start": source_start
            },
            "speed": self.speed,
            "target_timerange": {
                "duration": self.target_timerange.duration,
                "start": self.target_timerange.start
            },
            "template_id": "",
            "template_scene": "default",
            "track_attribute": 0,
            "track_render_index": 0,
            "uniform_scale": {"on": True, "value": 1.0},
            "visible": True,
            "volume": self.volume
        }


@dataclass
class AudioSegment(BaseSegment):
    """音频片段"""
    source_timerange: Optional[Timerange] = None
    """素材中的源时间范围"""
    speed: float = 1.0
    """播放速度"""
    volume: float = 1.0
    """音量"""
    
    def export_json(self) -> Dict[str, Any]:
        """导出为剪映JSON格式"""
        # 如果没有指定源时间范围，使用目标时间范围
        if self.source_timerange is None:
            source_start = 0
            source_duration = round(self.target_timerange.duration * self.speed)
        else:
            source_start = self.source_timerange.start
            source_duration = self.source_timerange.duration
        
        return {
            "cartoon": False,
            "clip": {"alpha": 1.0, "flip": {}, "rotation": 0.0, "scale": {}, "transform": {}},
            "common_keyframes": [],
            "enable_adjust": False,
            "extra_material_refs": [],
            "group_id": "",
            "id": self.segment_id,
            "intensifies_audio": False,
            "is_placeholder": False,
            "keyframe_refs": [],
            "last_nonzero_volume": 1.0,
            "material_id": self.material_id,
            "render_index": 0,
            "reverse": False,
            "source_timerange": {
                "duration": source_duration,
                "start": source_start
            },
            "speed": self.speed,
            "target_timerange": {
                "duration": self.target_timerange.duration,
                "start": self.target_timerange.start
            },
            "template_id": "",
            "template_scene": "default",
            "track_attribute": 0,
            "track_render_index": 0,
            "visible": True,
            "volume": self.volume
        }


@dataclass
class TextSegment(BaseSegment):
    """文本片段（字幕）"""
    content: str = ""
    """文本内容"""
    
    def export_json(self) -> Dict[str, Any]:
        """导出为剪映JSON格式"""
        return {
            "cartoon": False,
            "clip": {
                "alpha": 1.0,
                "flip": {},
                "rotation": 0.0,
                "scale": {"x": 1.0, "y": 1.0},
                "transform": {"x": 0.0, "y": 0.0}
            },
            "common_keyframes": [],
            "enable_adjust": False,
            "extra_material_refs": [],
            "group_id": "",
            "id": self.segment_id,
            "material_id": self.material_id,
            "render_index": 15000,
            "source_timerange": None,
            "target_timerange": {
                "duration": self.target_timerange.duration,
                "start": self.target_timerange.start
            },
            "template_id": "",
            "template_scene": "default",
            "track_attribute": 0,
            "track_render_index": 0,
            "visible": True
        }


class Track:
    """轨道类"""
    
    def __init__(self, track_type: TrackType, name: str = "", render_index: int = 0, mute: bool = False):
        self.track_type = track_type
        self.name = name
        self.track_id = uuid.uuid4().hex
        self.render_index = render_index
        self.mute = mute
        self.segments: List[BaseSegment] = []
    
    @property
    def end_time(self) -> int:
        """轨道结束时间（微秒）"""
        if not self.segments:
            return 0
        return max(seg.target_timerange.end for seg in self.segments)
    
    def add_segment(self, segment: BaseSegment) -> 'Track':
        """
        添加片段到轨道
        
        Args:
            segment: 片段对象
            
        Returns:
            self（支持链式调用）
            
        Raises:
            ValueError: 片段重叠
        """
        # 检查重叠
        for existing_seg in self.segments:
            if existing_seg.overlaps(segment):
                raise ValueError(
                    f"片段重叠: 新片段[{segment.target_timerange.start}-{segment.target_timerange.end}] "
                    f"与现有片段[{existing_seg.target_timerange.start}-{existing_seg.target_timerange.end}]重叠"
                )
        
        self.segments.append(segment)
        # 按开始时间排序
        self.segments.sort(key=lambda s: s.target_timerange.start)
        return self
    
    def export_json(self) -> Dict[str, Any]:
        """导出为剪映JSON格式"""
        # 为每个片段设置render_index
        segment_exports = []
        for seg in self.segments:
            seg_json = seg.export_json()
            seg_json["render_index"] = self.render_index
            segment_exports.append(seg_json)
        
        return {
            "attribute": int(self.mute),
            "flag": 0,
            "id": self.track_id,
            "is_default_name": len(self.name) == 0,
            "name": self.name,
            "segments": segment_exports,
            "type": self.track_type.value
        }


class TrackManager:
    """轨道管理器"""
    
    def __init__(self):
        self.tracks: List[Track] = []
    
    def create_track(self, track_type: TrackType, name: str = "", 
                    render_index: Optional[int] = None, mute: bool = False) -> Track:
        """
        创建新轨道
        
        Args:
            track_type: 轨道类型
            name: 轨道名称
            render_index: 渲染索引（None则自动分配）
            mute: 是否静音
            
        Returns:
            Track对象
        """
        if render_index is None:
            # 自动分配render_index
            if track_type == TrackType.VIDEO:
                render_index = 0
            elif track_type == TrackType.AUDIO:
                render_index = 0
            elif track_type == TrackType.TEXT:
                render_index = 15000
            else:
                render_index = 10000
        
        track = Track(track_type, name, render_index, mute)
        self.tracks.append(track)
        return track
    
    def export_all_tracks(self) -> List[Dict[str, Any]]:
        """导出所有轨道"""
        return [track.export_json() for track in self.tracks]

