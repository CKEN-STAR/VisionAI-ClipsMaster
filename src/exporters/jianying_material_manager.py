"""
剪映素材管理器
管理所有素材（视频、音频、文本等），确保ID一致性
"""

import os
import uuid
from typing import Dict, List, Any, Optional, Literal
from dataclasses import dataclass, field
from pathlib import Path

try:
    import pymediainfo
    PYMEDIAINFO_AVAILABLE = True
except ImportError:
    PYMEDIAINFO_AVAILABLE = False


@dataclass
class CropSettings:
    """素材裁剪设置"""
    upper_left_x: float = 0.0
    upper_left_y: float = 0.0
    upper_right_x: float = 1.0
    upper_right_y: float = 0.0
    lower_left_x: float = 0.0
    lower_left_y: float = 1.0
    lower_right_x: float = 1.0
    lower_right_y: float = 1.0
    
    def export_json(self) -> Dict[str, Any]:
        """导出为JSON格式"""
        return {
            "upper_left_x": self.upper_left_x,
            "upper_left_y": self.upper_left_y,
            "upper_right_x": self.upper_right_x,
            "upper_right_y": self.upper_right_y,
            "lower_left_x": self.lower_left_x,
            "lower_left_y": self.lower_left_y,
            "lower_right_x": self.lower_right_x,
            "lower_right_y": self.lower_right_y
        }


@dataclass
class VideoMaterial:
    """视频素材"""
    path: str
    """素材文件路径（绝对路径）"""
    material_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    """素材全局ID"""
    material_name: str = ""
    """素材名称"""
    duration: int = 0
    """素材时长（微秒）"""
    width: int = 1920
    """素材宽度"""
    height: int = 1080
    """素材高度"""
    material_type: Literal["video", "photo"] = "video"
    """素材类型"""
    crop_settings: CropSettings = field(default_factory=CropSettings)
    """裁剪设置"""
    local_material_id: str = ""
    """本地素材ID"""
    
    def __post_init__(self):
        """初始化后处理"""
        # 确保路径是绝对路径
        self.path = os.path.abspath(self.path)
        
        # 如果没有指定名称，使用文件名
        if not self.material_name:
            self.material_name = os.path.basename(self.path)
        
        # 验证文件存在
        if not os.path.exists(self.path):
            raise FileNotFoundError(f"素材文件不存在: {self.path}")
        
        # 如果有pymediainfo，提取元数据
        if PYMEDIAINFO_AVAILABLE and self.duration == 0:
            self._extract_metadata()
    
    def _extract_metadata(self):
        """使用pymediainfo提取素材元数据"""
        try:
            info = pymediainfo.MediaInfo.parse(
                self.path,
                mediainfo_options={"File_TestContinuousFileNames": "0"}
            )
            
            # 检查视频轨道
            if len(info.video_tracks) > 0:
                video_track = info.video_tracks[0]
                self.material_type = "video"
                self.duration = int(video_track.duration * 1000)  # 转换为微秒
                self.width = video_track.width
                self.height = video_track.height
            # 检查图片轨道
            elif len(info.image_tracks) > 0:
                image_track = info.image_tracks[0]
                self.material_type = "photo"
                self.duration = 10800000000  # 3小时（图片默认时长）
                self.width = image_track.width
                self.height = image_track.height
            else:
                # 无法识别，使用默认值
                pass
        except Exception:
            # 提取失败，使用默认值
            pass
    
    def export_json(self) -> Dict[str, Any]:
        """导出为剪映JSON格式"""
        return {
            "audio_fade": None,
            "category_id": "",
            "category_name": "local",
            "check_flag": 63487,
            "crop": self.crop_settings.export_json(),
            "crop_ratio": "free",
            "crop_scale": 1.0,
            "duration": self.duration,
            "height": self.height,
            "id": self.material_id,
            "local_material_id": self.local_material_id,
            "material_id": self.material_id,
            "material_name": self.material_name,
            "media_path": "",
            "path": self.path,
            "type": self.material_type,
            "width": self.width
        }


@dataclass
class AudioMaterial:
    """音频素材"""
    path: str
    """素材文件路径（绝对路径）"""
    material_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    """素材全局ID"""
    material_name: str = ""
    """素材名称"""
    duration: int = 0
    """素材时长（微秒）"""
    
    def __post_init__(self):
        """初始化后处理"""
        # 确保路径是绝对路径
        self.path = os.path.abspath(self.path)
        
        # 如果没有指定名称，使用文件名
        if not self.material_name:
            self.material_name = os.path.basename(self.path)
        
        # 验证文件存在
        if not os.path.exists(self.path):
            raise FileNotFoundError(f"音频文件不存在: {self.path}")
        
        # 如果有pymediainfo，提取元数据
        if PYMEDIAINFO_AVAILABLE and self.duration == 0:
            self._extract_metadata()
    
    def _extract_metadata(self):
        """使用pymediainfo提取音频元数据"""
        try:
            info = pymediainfo.MediaInfo.parse(self.path)
            
            if len(info.audio_tracks) > 0:
                audio_track = info.audio_tracks[0]
                self.duration = int(audio_track.duration * 1000)  # 转换为微秒
        except Exception:
            # 提取失败，使用默认值
            pass
    
    def export_json(self) -> Dict[str, Any]:
        """导出为剪映JSON格式"""
        return {
            "app_id": 0,
            "category_id": "",
            "category_name": "local",
            "check_flag": 3,
            "copyright_limit_type": "none",
            "duration": self.duration,
            "effect_id": "",
            "formula_id": "",
            "id": self.material_id,
            "local_material_id": self.material_id,
            "music_id": self.material_id,
            "name": self.material_name,
            "path": self.path,
            "source_platform": 0,
            "type": "extract_music",
            "wave_points": []
        }


class MaterialManager:
    """素材管理器 - 管理所有素材，确保ID一致性"""
    
    def __init__(self):
        self.video_materials: Dict[str, VideoMaterial] = {}
        self.audio_materials: Dict[str, AudioMaterial] = {}
        self._path_to_id: Dict[str, str] = {}  # 路径到ID的映射
    
    def add_video_material(self, path: str, **kwargs) -> VideoMaterial:
        """
        添加视频素材
        
        Args:
            path: 视频文件路径
            **kwargs: 其他参数（material_name, duration等）
            
        Returns:
            VideoMaterial对象
        """
        # 标准化路径
        abs_path = os.path.abspath(path)
        
        # 检查是否已存在
        if abs_path in self._path_to_id:
            material_id = self._path_to_id[abs_path]
            return self.video_materials[material_id]
        
        # 创建新素材
        material = VideoMaterial(path=abs_path, **kwargs)
        
        # 存储
        self.video_materials[material.material_id] = material
        self._path_to_id[abs_path] = material.material_id
        
        return material
    
    def add_audio_material(self, path: str, **kwargs) -> AudioMaterial:
        """
        添加音频素材
        
        Args:
            path: 音频文件路径
            **kwargs: 其他参数（material_name, duration等）
            
        Returns:
            AudioMaterial对象
        """
        # 标准化路径
        abs_path = os.path.abspath(path)
        
        # 检查是否已存在
        if abs_path in self._path_to_id:
            material_id = self._path_to_id[abs_path]
            if material_id in self.audio_materials:
                return self.audio_materials[material_id]
        
        # 创建新素材
        material = AudioMaterial(path=abs_path, **kwargs)
        
        # 存储
        self.audio_materials[material.material_id] = material
        self._path_to_id[abs_path] = material.material_id
        
        return material
    
    def get_material_by_path(self, path: str) -> Optional[Any]:
        """根据路径获取素材"""
        abs_path = os.path.abspath(path)
        material_id = self._path_to_id.get(abs_path)
        
        if material_id:
            if material_id in self.video_materials:
                return self.video_materials[material_id]
            elif material_id in self.audio_materials:
                return self.audio_materials[material_id]
        
        return None
    
    def export_all_materials(self) -> Dict[str, List[Dict[str, Any]]]:
        """导出所有素材为剪映格式"""
        return {
            "videos": [m.export_json() for m in self.video_materials.values()],
            "audios": [m.export_json() for m in self.audio_materials.values()],
            "texts": [],  # 文本素材暂时为空
            "effects": [],  # 特效素材暂时为空
            "filters": [],  # 滤镜素材暂时为空
            "transitions": [],  # 转场素材暂时为空
            "stickers": []  # 贴纸素材暂时为空
        }

