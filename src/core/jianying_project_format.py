#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 剪映项目文件格式分析器
研究和生成符合剪映标准的项目文件格式，确保多个视频片段在时间轴上正确分离显示

剪映项目文件结构分析：
1. 剪映使用.json格式的项目文件
2. 项目文件包含tracks（轨道）、materials（素材）、canvases（画布）等核心结构
3. 每个视频片段作为独立的segment在video track中
4. 字幕作为独立的text track
"""

import json
import uuid
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class JianyingProjectGenerator:
    """剪映项目文件生成器"""
    
    def __init__(self):
        """初始化项目生成器"""
        self.project_version = "13.0.0"  # 剪映版本
        self.platform = "pc"  # 平台标识
        
    def generate_project_file(self,
                            video_segments: List[Dict[str, Any]],
                            subtitles: List[Dict[str, Any]],
                            project_name: str,
                            output_path: str,
                            original_video_files: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        生成剪映项目文件（增强版：支持原片映射和完整素材库）

        Args:
            video_segments: 视频片段列表
            subtitles: 字幕列表
            project_name: 项目名称
            output_path: 输出路径
            original_video_files: 原始视频文件列表（用于素材库和映射）

        Returns:
            项目文件数据
        """
        try:
            logger.info(f"开始生成剪映项目文件: {project_name}")
            
            # 生成项目基础结构
            project_data = self._create_project_structure(project_name)
            
            # 生成素材库（增强版：包含原片映射）
            materials = self._generate_materials_with_mapping(
                video_segments, subtitles, original_video_files
            )
            project_data["materials"] = materials
            
            # 生成轨道结构（增强版：支持原片映射和可拖拽边界）
            tracks = self._generate_tracks_with_mapping(
                video_segments, subtitles, materials, original_video_files
            )
            project_data["tracks"] = tracks
            
            # 生成画布设置
            canvases = self._generate_canvases()
            project_data["canvases"] = canvases
            
            # 计算项目时长
            total_duration = self._calculate_total_duration(video_segments)
            project_data["duration"] = total_duration
            
            # 保存项目文件
            self._save_project_file(project_data, output_path)
            
            logger.info(f"剪映项目文件生成完成: {output_path}")
            
            return {
                "status": "success",
                "project_file": output_path,
                "project_data": project_data,
                "segments_count": len(video_segments),
                "total_duration": total_duration
            }
            
        except Exception as e:
            logger.error(f"生成剪映项目文件失败: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _create_project_structure(self, project_name: str) -> Dict[str, Any]:
        """创建项目基础结构"""
        return {
            "version": self.project_version,
            "platform": self.platform,
            "id": str(uuid.uuid4()),
            "name": project_name,
            "create_time": int(datetime.now().timestamp() * 1000000),
            "update_time": int(datetime.now().timestamp() * 1000000),
            "draft_fold": "",
            "draft_removable": True,
            "source": "visionai_clipmaster",
            "materials": {},
            "tracks": [],
            "canvases": [],
            "duration": 0,
            "extra_info": {
                "export_range": {
                    "start": 0,
                    "end": 0
                },
                "is_landscape": True,
                "video_resolution": {
                    "width": 1920,
                    "height": 1080
                },
                "fps": 30
            }
        }
    
    def _generate_materials_with_mapping(self,
                                       video_segments: List[Dict[str, Any]],
                                       subtitles: List[Dict[str, Any]],
                                       original_video_files: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """生成素材库（增强版：包含原片映射和完整素材库）"""
        materials = {
            "videos": [],
            "audios": [],
            "texts": [],
            "images": [],
            "effects": []
        }

        # 1. 添加原始视频文件到素材库（完整素材库功能）
        original_video_materials = {}
        if original_video_files:
            for i, original_file in enumerate(original_video_files):
                original_material = {
                    "id": str(uuid.uuid4()),
                    "type": "video",
                    "path": original_file.get("filepath", ""),
                    "name": original_file.get("filename", f"original_video_{i+1}"),
                    "duration": int(original_file.get("duration", 0) * 1000000),  # 微秒
                    "width": original_file.get("width", 1920),
                    "height": original_file.get("height", 1080),
                    "fps": original_file.get("fps", 30),
                    "create_time": int(datetime.now().timestamp() * 1000000),
                    "extra_info": {
                        "is_original_source": True,
                        "original_index": i,
                        "file_type": "source_material"
                    }
                }
                materials["videos"].append(original_material)
                original_video_materials[original_file.get("id", f"original_{i}")] = original_material["id"]

        # 2. 添加视频片段素材（与原片建立映射关系）
        for i, segment in enumerate(video_segments):
            # 查找对应的原始视频文件
            original_video_id = segment.get("original_video_id", "")
            mapped_original_material_id = original_video_materials.get(original_video_id, "")

            video_material = {
                "id": str(uuid.uuid4()),
                "type": "video",
                "path": segment.get("filepath", ""),
                "name": segment.get("filename", f"segment_{i+1}"),
                "duration": int(segment.get("duration", 0) * 1000000),  # 微秒
                "width": 1920,
                "height": 1080,
                "fps": 30,
                "create_time": int(datetime.now().timestamp() * 1000000),
                "extra_info": {
                    "segment_index": i + 1,
                    "start_time": segment.get("start_time", 0),
                    "end_time": segment.get("end_time", 0),
                    "original_text": segment.get("text", ""),
                    "original_video_id": original_video_id,
                    "mapped_original_material_id": mapped_original_material_id,
                    "source_start_time": segment.get("original_start_time", 0),
                    "source_end_time": segment.get("original_end_time", 0),
                    "is_segment": True,
                    "editable_boundaries": True  # 支持边界拖拽
                }
            }
            materials["videos"].append(video_material)
        
        # 添加字幕素材
        for i, subtitle in enumerate(subtitles):
            text_material = {
                "id": str(uuid.uuid4()),
                "type": "text",
                "content": subtitle.get("text", ""),
                "duration": int((subtitle.get("end", 0) - subtitle.get("start", 0)) * 1000000),
                "style": {
                    "font_family": "Microsoft YaHei",
                    "font_size": 24,
                    "color": "#FFFFFF",
                    "background_color": "#00000080",
                    "alignment": "center",
                    "position": "bottom"
                },
                "create_time": int(datetime.now().timestamp() * 1000000)
            }
            materials["texts"].append(text_material)
        
        return materials
    
    def _generate_tracks_with_mapping(self,
                                    video_segments: List[Dict[str, Any]],
                                    subtitles: List[Dict[str, Any]],
                                    materials: Dict[str, Any],
                                    original_video_files: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """生成轨道结构（增强版：支持原片映射和可拖拽边界）"""
        tracks = []

        # 主视频轨道
        video_track = {
            "id": str(uuid.uuid4()),
            "type": "video",
            "attribute": 0,
            "flag": 0,
            "segments": []
        }

        # 获取片段素材（排除原始素材）
        segment_materials = [m for m in materials["videos"] if m.get("extra_info", {}).get("is_segment", False)]

        # 添加视频片段到轨道（增强版：原片映射和可拖拽边界）
        current_time = 0
        for i, (segment, material) in enumerate(zip(video_segments, segment_materials)):
            segment_duration = int(segment.get("duration", 0) * 1000000)

            # 获取原片映射信息
            original_video_id = segment.get("original_video_id", "")
            source_start_time = int(segment.get("original_start_time", 0) * 1000000)
            source_end_time = int(segment.get("original_end_time", segment.get("duration", 0)) * 1000000)
            source_duration = source_end_time - source_start_time

            video_segment = {
                "id": str(uuid.uuid4()),
                "material_id": material["id"],
                "target_timerange": {
                    "start": current_time,
                    "duration": segment_duration
                },
                "source_timerange": {
                    "start": source_start_time,  # 原片中的开始时间
                    "duration": source_duration   # 原片中的时长
                },
                "extra_material_refs": [],
                "uniform_scale": {
                    "on": True,
                    "value": 1.0
                },
                "transform": {
                    "x": 0.0,
                    "y": 0.0,
                    "width": 1.0,
                    "height": 1.0,
                    "rotation": 0.0
                },
                "visible": True,
                "volume": 1.0,
                "speed": 1.0,  # 播放速度
                "extra_info": {
                    "segment_index": i + 1,
                    "original_text": segment.get("text", ""),
                    "is_independent": True,  # 标记为独立片段
                    "original_video_id": original_video_id,
                    "original_start_time": segment.get("original_start_time", 0),
                    "original_end_time": segment.get("original_end_time", 0),
                    "editable_boundaries": True,  # 支持边界拖拽
                    "source_mapping": {
                        "original_file": original_video_id,
                        "source_start": source_start_time,
                        "source_end": source_end_time,
                        "can_extend": True  # 可以扩展边界
                    }
                }
            }

            video_track["segments"].append(video_segment)
            current_time += segment_duration
        
        tracks.append(video_track)
        
        # 字幕轨道
        if subtitles and materials["texts"]:
            text_track = {
                "id": str(uuid.uuid4()),
                "type": "text",
                "attribute": 0,
                "flag": 0,
                "segments": []
            }
            
            # 添加字幕片段到轨道
            for i, (subtitle, material) in enumerate(zip(subtitles, materials["texts"])):
                subtitle_start = int(subtitle.get("start", 0) * 1000000)
                subtitle_duration = int((subtitle.get("end", 0) - subtitle.get("start", 0)) * 1000000)
                
                text_segment = {
                    "id": str(uuid.uuid4()),
                    "material_id": material["id"],
                    "target_timerange": {
                        "start": subtitle_start,
                        "duration": subtitle_duration
                    },
                    "source_timerange": {
                        "start": 0,
                        "duration": subtitle_duration
                    },
                    "extra_material_refs": [],
                    "visible": True,
                    "extra_info": {
                        "subtitle_index": i + 1,
                        "content": subtitle.get("text", "")
                    }
                }
                
                text_track["segments"].append(text_segment)
            
            tracks.append(text_track)
        
        return tracks
    
    def _generate_canvases(self) -> List[Dict[str, Any]]:
        """生成画布设置"""
        return [{
            "id": str(uuid.uuid4()),
            "type": "main_canvas",
            "width": 1920,
            "height": 1080,
            "color": "#000000",
            "is_main": True
        }]
    
    def _calculate_total_duration(self, video_segments: List[Dict[str, Any]]) -> int:
        """计算项目总时长（微秒）"""
        total_duration = 0
        for segment in video_segments:
            duration = segment.get("duration", 0)
            total_duration += duration
        return int(total_duration * 1000000)
    
    def _save_project_file(self, project_data: Dict[str, Any], output_path: str):
        """保存项目文件"""
        try:
            # 确保输出目录存在
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 保存为JSON格式
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(project_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"项目文件已保存: {output_path}")
            
        except Exception as e:
            logger.error(f"保存项目文件失败: {str(e)}")
            raise
    
    def generate_draft_content(self, project_data: Dict[str, Any]) -> str:
        """生成剪映草稿内容文件"""
        try:
            # 剪映草稿内容格式
            draft_content = {
                "version": self.project_version,
                "content": project_data,
                "create_time": int(datetime.now().timestamp() * 1000000),
                "update_time": int(datetime.now().timestamp() * 1000000),
                "source": "visionai_clipmaster"
            }
            
            return json.dumps(draft_content, ensure_ascii=False, separators=(',', ':'))
            
        except Exception as e:
            logger.error(f"生成草稿内容失败: {str(e)}")
            raise
    
    def validate_project_structure(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """验证项目文件结构"""
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        try:
            # 检查必需字段
            required_fields = ["version", "platform", "id", "name", "materials", "tracks"]
            for field in required_fields:
                if field not in project_data:
                    validation_result["errors"].append(f"缺少必需字段: {field}")
                    validation_result["valid"] = False
            
            # 检查轨道结构
            if "tracks" in project_data:
                video_tracks = [t for t in project_data["tracks"] if t.get("type") == "video"]
                if not video_tracks:
                    validation_result["warnings"].append("未找到视频轨道")
                
                for track in video_tracks:
                    if not track.get("segments"):
                        validation_result["warnings"].append("视频轨道中没有片段")
            
            # 检查素材库
            if "materials" in project_data:
                materials = project_data["materials"]
                if "videos" in materials and len(materials["videos"]) == 0:
                    validation_result["warnings"].append("素材库中没有视频文件")
            
            logger.info(f"项目文件验证完成: {'有效' if validation_result['valid'] else '无效'}")
            
        except Exception as e:
            validation_result["valid"] = False
            validation_result["errors"].append(f"验证过程出错: {str(e)}")
        
        return validation_result


def create_jianying_project_generator() -> JianyingProjectGenerator:
    """创建剪映项目生成器"""
    try:
        return JianyingProjectGenerator()
    except Exception as e:
        logger.error(f"创建剪映项目生成器失败: {str(e)}")
        raise
