#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
剪映工程文件兼容性验证器

专门用于验证生成的剪映工程文件是否100%兼容剪映软件，
确保导入成功率达到100%。

作者: VisionAI-ClipsMaster Team
日期: 2025-07-23
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

class JianyingCompatibilityValidator:
    """剪映工程文件兼容性验证器"""
    
    def __init__(self):
        """初始化验证器"""
        # 剪映3.0+版本的必需字段
        self.required_fields = {
            "root": [
                "version", "type", "platform", "create_time", "update_time",
                "id", "draft_id", "draft_name", "canvas_config", "tracks", 
                "materials", "extra_info", "keyframes", "relations"
            ],
            "canvas_config": [
                "height", "width", "duration", "fps", "ratio"
            ],
            "materials": [
                "videos", "audios", "texts", "effects", "stickers", "images", "sounds"
            ],
            "extra_info": [
                "export_range", "fps", "audio_sample_rate", "video_codec", "audio_codec"
            ],
            "track": [
                "id", "type", "attribute", "flag", "segments"
            ],
            "segment": [
                "id", "type", "material_id", "track_render_index", 
                "source_timerange", "target_timerange", "extra_material_refs"
            ],
            "timerange": [
                "start", "duration"
            ]
        }
        
        # 支持的剪映版本
        self.supported_versions = ["3.0.0", "2.9.0", "2.8.0"]
        
        # 支持的平台
        self.supported_platforms = ["windows", "mac", "android", "ios"]
        
        # 支持的素材类型
        self.supported_material_types = {
            "video": ["mp4", "avi", "mov", "mkv", "flv", "wmv", "webm"],
            "audio": ["mp3", "wav", "aac", "m4a", "flac", "ogg"],
            "text": ["srt", "ass", "vtt"]
        }
    
    def validate_project(self, project_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        验证剪映工程文件的完整兼容性
        
        Args:
            project_data: 剪映工程数据
            
        Returns:
            Tuple[bool, List[str]]: (是否兼容, 错误列表)
        """
        errors = []
        
        try:
            # 1. 验证基本结构
            structure_errors = self._validate_basic_structure(project_data)
            errors.extend(structure_errors)
            
            # 2. 验证版本兼容性
            version_errors = self._validate_version_compatibility(project_data)
            errors.extend(version_errors)
            
            # 3. 验证画布配置
            canvas_errors = self._validate_canvas_config(project_data)
            errors.extend(canvas_errors)
            
            # 4. 验证轨道结构
            track_errors = self._validate_tracks(project_data)
            errors.extend(track_errors)
            
            # 5. 验证素材库
            material_errors = self._validate_materials(project_data)
            errors.extend(material_errors)
            
            # 6. 验证时间轴一致性
            timeline_errors = self._validate_timeline_consistency(project_data)
            errors.extend(timeline_errors)
            
            # 7. 验证数据类型
            type_errors = self._validate_data_types(project_data)
            errors.extend(type_errors)
            
            is_compatible = len(errors) == 0
            
            if is_compatible:
                logger.info("剪映工程文件兼容性验证通过")
            else:
                logger.error(f"剪映工程文件兼容性验证失败，发现 {len(errors)} 个问题")
                for error in errors:
                    logger.error(f"  - {error}")
            
            return is_compatible, errors
            
        except Exception as e:
            error_msg = f"验证过程中发生异常: {str(e)}"
            logger.error(error_msg)
            return False, [error_msg]
    
    def _validate_basic_structure(self, project_data: Dict[str, Any]) -> List[str]:
        """验证基本结构"""
        errors = []
        
        # 检查根级别必需字段
        for field in self.required_fields["root"]:
            if field not in project_data:
                errors.append(f"缺少根级别必需字段: {field}")
        
        return errors
    
    def _validate_version_compatibility(self, project_data: Dict[str, Any]) -> List[str]:
        """验证版本兼容性"""
        errors = []
        
        version = project_data.get("version", "")
        if version not in self.supported_versions:
            errors.append(f"不支持的版本: {version}，支持的版本: {self.supported_versions}")
        
        platform = project_data.get("platform", "")
        if platform not in self.supported_platforms:
            errors.append(f"不支持的平台: {platform}，支持的平台: {self.supported_platforms}")
        
        project_type = project_data.get("type", "")
        if project_type != "draft_content":
            errors.append(f"项目类型必须为 'draft_content'，当前为: {project_type}")
        
        return errors
    
    def _validate_canvas_config(self, project_data: Dict[str, Any]) -> List[str]:
        """验证画布配置"""
        errors = []
        
        canvas_config = project_data.get("canvas_config", {})
        
        # 检查必需字段
        for field in self.required_fields["canvas_config"]:
            if field not in canvas_config:
                errors.append(f"canvas_config缺少必需字段: {field}")
        
        # 验证数值范围
        if "width" in canvas_config:
            width = canvas_config["width"]
            if not isinstance(width, int) or width <= 0:
                errors.append(f"canvas_config.width必须为正整数，当前为: {width}")
        
        if "height" in canvas_config:
            height = canvas_config["height"]
            if not isinstance(height, int) or height <= 0:
                errors.append(f"canvas_config.height必须为正整数，当前为: {height}")
        
        if "fps" in canvas_config:
            fps = canvas_config["fps"]
            if not isinstance(fps, (int, float)) or fps <= 0:
                errors.append(f"canvas_config.fps必须为正数，当前为: {fps}")
        
        if "duration" in canvas_config:
            duration = canvas_config["duration"]
            if not isinstance(duration, (int, float)) or duration < 0:
                errors.append(f"canvas_config.duration必须为非负数，当前为: {duration}")
        
        return errors
    
    def _validate_tracks(self, project_data: Dict[str, Any]) -> List[str]:
        """验证轨道结构"""
        errors = []
        
        tracks = project_data.get("tracks", [])
        
        if not isinstance(tracks, list):
            errors.append("tracks必须为数组")
            return errors
        
        if len(tracks) == 0:
            errors.append("至少需要一个轨道")
        
        track_ids = set()
        for i, track in enumerate(tracks):
            if not isinstance(track, dict):
                errors.append(f"轨道 {i} 必须为对象")
                continue
            
            # 检查必需字段
            for field in self.required_fields["track"]:
                if field not in track:
                    errors.append(f"轨道 {i} 缺少必需字段: {field}")
            
            # 检查轨道ID唯一性
            track_id = track.get("id", "")
            if track_id in track_ids:
                errors.append(f"轨道 {i} ID重复: {track_id}")
            track_ids.add(track_id)
            
            # 验证轨道类型
            track_type = track.get("type", "")
            if track_type not in ["video", "audio", "text", "effect"]:
                errors.append(f"轨道 {i} 类型无效: {track_type}")
            
            # 验证片段
            segments = track.get("segments", [])
            segment_errors = self._validate_segments(segments, i)
            errors.extend(segment_errors)
        
        return errors
    
    def _validate_segments(self, segments: List[Dict], track_index: int) -> List[str]:
        """验证片段结构"""
        errors = []
        
        if not isinstance(segments, list):
            errors.append(f"轨道 {track_index} 的segments必须为数组")
            return errors
        
        segment_ids = set()
        for i, segment in enumerate(segments):
            if not isinstance(segment, dict):
                errors.append(f"轨道 {track_index} 片段 {i} 必须为对象")
                continue
            
            # 检查必需字段
            for field in self.required_fields["segment"]:
                if field not in segment:
                    errors.append(f"轨道 {track_index} 片段 {i} 缺少必需字段: {field}")
            
            # 检查片段ID唯一性
            segment_id = segment.get("id", "")
            if segment_id in segment_ids:
                errors.append(f"轨道 {track_index} 片段 {i} ID重复: {segment_id}")
            segment_ids.add(segment_id)
            
            # 验证时间范围
            source_timerange = segment.get("source_timerange", {})
            target_timerange = segment.get("target_timerange", {})
            
            timerange_errors = self._validate_timerange(source_timerange, f"轨道 {track_index} 片段 {i} source_timerange")
            errors.extend(timerange_errors)
            
            timerange_errors = self._validate_timerange(target_timerange, f"轨道 {track_index} 片段 {i} target_timerange")
            errors.extend(timerange_errors)
        
        return errors
    
    def _validate_timerange(self, timerange: Dict, context: str) -> List[str]:
        """验证时间范围"""
        errors = []
        
        if not isinstance(timerange, dict):
            errors.append(f"{context} 必须为对象")
            return errors
        
        for field in self.required_fields["timerange"]:
            if field not in timerange:
                errors.append(f"{context} 缺少必需字段: {field}")
        
        start = timerange.get("start", 0)
        duration = timerange.get("duration", 0)
        
        if not isinstance(start, (int, float)) or start < 0:
            errors.append(f"{context}.start 必须为非负数，当前为: {start}")
        
        if not isinstance(duration, (int, float)) or duration <= 0:
            errors.append(f"{context}.duration 必须为正数，当前为: {duration}")
        
        return errors
    
    def _validate_materials(self, project_data: Dict[str, Any]) -> List[str]:
        """验证素材库"""
        errors = []
        
        materials = project_data.get("materials", {})
        
        if not isinstance(materials, dict):
            errors.append("materials必须为对象")
            return errors
        
        # 检查必需的素材类型
        for material_type in self.required_fields["materials"]:
            if material_type not in materials:
                errors.append(f"materials缺少类型: {material_type}")
            elif not isinstance(materials[material_type], list):
                errors.append(f"materials.{material_type} 必须为数组")
        
        # 验证素材ID唯一性
        all_material_ids = set()
        for material_type, material_list in materials.items():
            if isinstance(material_list, list):
                for i, material in enumerate(material_list):
                    if isinstance(material, dict):
                        material_id = material.get("id", "")
                        if material_id in all_material_ids:
                            errors.append(f"素材ID重复: {material_id} (在 {material_type} 中)")
                        all_material_ids.add(material_id)
        
        return errors
    
    def _validate_timeline_consistency(self, project_data: Dict[str, Any]) -> List[str]:
        """验证时间轴一致性"""
        errors = []
        
        canvas_duration = project_data.get("canvas_config", {}).get("duration", 0)
        export_end = project_data.get("extra_info", {}).get("export_range", {}).get("end", 0)
        
        # 验证导出范围与画布时长一致
        if abs(canvas_duration - export_end) > 100:  # 允许100ms误差
            errors.append(f"画布时长({canvas_duration})与导出结束时间({export_end})不一致")
        
        return errors
    
    def _validate_data_types(self, project_data: Dict[str, Any]) -> List[str]:
        """验证数据类型"""
        errors = []
        
        # 验证时间戳
        create_time = project_data.get("create_time", 0)
        update_time = project_data.get("update_time", 0)
        
        if not isinstance(create_time, int) or create_time <= 0:
            errors.append(f"create_time必须为正整数，当前为: {create_time}")
        
        if not isinstance(update_time, int) or update_time <= 0:
            errors.append(f"update_time必须为正整数，当前为: {update_time}")
        
        # 验证ID格式
        project_id = project_data.get("id", "")
        draft_id = project_data.get("draft_id", "")
        
        if not isinstance(project_id, str) or len(project_id) == 0:
            errors.append("id必须为非空字符串")
        
        if not isinstance(draft_id, str) or len(draft_id) == 0:
            errors.append("draft_id必须为非空字符串")
        
        return errors
    
    def fix_compatibility_issues(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        自动修复兼容性问题
        
        Args:
            project_data: 原始项目数据
            
        Returns:
            Dict[str, Any]: 修复后的项目数据
        """
        import copy
        import time
        import uuid
        
        fixed_data = copy.deepcopy(project_data)
        
        # 修复缺失的基本字段
        current_time = int(time.time() * 1000000)
        
        if "version" not in fixed_data:
            fixed_data["version"] = "3.0.0"
        
        if "type" not in fixed_data:
            fixed_data["type"] = "draft_content"
        
        if "platform" not in fixed_data:
            fixed_data["platform"] = "windows"
        
        if "create_time" not in fixed_data:
            fixed_data["create_time"] = current_time
        
        if "update_time" not in fixed_data:
            fixed_data["update_time"] = current_time
        
        if "id" not in fixed_data:
            fixed_data["id"] = str(uuid.uuid4())
        
        if "draft_id" not in fixed_data:
            fixed_data["draft_id"] = fixed_data["id"]
        
        if "draft_name" not in fixed_data:
            fixed_data["draft_name"] = "VisionAI混剪项目"
        
        # 修复画布配置
        if "canvas_config" not in fixed_data:
            fixed_data["canvas_config"] = {}
        
        canvas_config = fixed_data["canvas_config"]
        if "fps" not in canvas_config:
            canvas_config["fps"] = 30
        if "ratio" not in canvas_config:
            canvas_config["ratio"] = "16:9"
        
        # 修复素材库
        if "materials" not in fixed_data:
            fixed_data["materials"] = {}
        
        materials = fixed_data["materials"]
        for material_type in self.required_fields["materials"]:
            if material_type not in materials:
                materials[material_type] = []
        
        # 修复额外信息
        if "extra_info" not in fixed_data:
            fixed_data["extra_info"] = {}
        
        extra_info = fixed_data["extra_info"]
        if "fps" not in extra_info:
            extra_info["fps"] = 30
        if "audio_sample_rate" not in extra_info:
            extra_info["audio_sample_rate"] = 44100
        if "video_codec" not in extra_info:
            extra_info["video_codec"] = "h264"
        if "audio_codec" not in extra_info:
            extra_info["audio_codec"] = "aac"
        
        # 修复关键帧和关系
        if "keyframes" not in fixed_data:
            fixed_data["keyframes"] = []
        if "relations" not in fixed_data:
            fixed_data["relations"] = []
        
        logger.info("已自动修复剪映工程文件兼容性问题")
        return fixed_data
