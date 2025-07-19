#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 剪映专业版导出器
将处理后的视频项目导出为剪映专业版可识别的工程文件格式
"""

import os
import json
import uuid
import time
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class JianYingProExporter:
    """剪映专业版导出器"""
    
    def __init__(self):
        self.project_template = self._load_project_template()
        self.export_settings = {
            "resolution": "1920x1080",
            "fps": 30,
            "audio_sample_rate": 44100,
            "video_codec": "h264",
            "audio_codec": "aac"
        }
        logger.info("剪映专业版导出器初始化完成")
    
    def _load_project_template(self) -> Dict[str, Any]:
        """加载剪映工程文件模板 - 修复：添加完整的素材结构"""
        return {
            "version": "3.0.0",
            "type": "draft_content",
            "platform": "windows",
            "create_time": int(time.time() * 1000),
            "update_time": int(time.time() * 1000),
            "id": str(uuid.uuid4()),
            "canvas_config": {
                "height": 1080,
                "width": 1920,
                "duration": 0
            },
            "tracks": [],
            "materials": {
                "videos": [],
                "audios": [],
                "texts": [],
                "effects": [],      # 修复：添加缺失的effects字段
                "stickers": []      # 修复：添加缺失的stickers字段
            },
            "extra_info": {
                "export_range": {
                    "start": 0,
                    "end": 0
                }
            }
        }
    
    def export_project(self, segments_or_project_data, output_path: str) -> bool:
        """
        导出剪映工程文件

        Args:
            segments_or_project_data: 视频片段列表或项目数据字典
            output_path: 输出路径

        Returns:
            bool: 导出是否成功
        """
        try:
            logger.info(f"开始导出剪映工程文件到: {output_path}")

            # 兼容两种输入格式：列表和字典
            if isinstance(segments_or_project_data, list):
                # 如果输入是列表，转换为项目数据格式
                project_data = {"segments": segments_or_project_data}
                logger.info(f"输入格式: 片段列表，包含 {len(segments_or_project_data)} 个片段")
            elif isinstance(segments_or_project_data, dict):
                # 如果输入是字典，直接使用
                project_data = segments_or_project_data
                logger.info(f"输入格式: 项目数据字典，包含 {len(project_data.get('segments', []))} 个片段")
            else:
                raise ValueError(f"不支持的输入类型: {type(segments_or_project_data)}")

            # 创建剪映工程结构
            logger.info("正在转换为剪映工程格式...")
            jianying_project = self._convert_to_jianying_format(project_data)
            logger.info("格式转换完成")

            # 确保输出目录存在
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"输出目录已准备: {output_dir}")

            # 保存工程文件
            logger.info("正在保存工程文件...")
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(jianying_project, f, ensure_ascii=False, indent=2)

            logger.info(f"剪映工程文件已成功导出到: {output_path}")
            return True

        except Exception as e:
            logger.error(f"导出剪映工程文件失败: {e}")
            return False
    
    def _convert_to_jianying_format(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """将项目数据转换为剪映格式"""
        jianying_project = self.project_template.copy()
        
        # 更新基本信息
        jianying_project["update_time"] = int(time.time() * 1000)
        
        # 处理视频片段
        segments = project_data.get("segments", [])
        total_duration = 0
        
        # 创建视频轨道
        video_track = {
            "id": str(uuid.uuid4()),
            "type": "video",
            "segments": []
        }
        
        # 创建音频轨道
        audio_track = {
            "id": str(uuid.uuid4()),
            "type": "audio", 
            "segments": []
        }
        
        # 创建字幕轨道
        text_track = {
            "id": str(uuid.uuid4()),
            "type": "text",
            "segments": []
        }
        
        for i, segment in enumerate(segments):
            segment_id = str(uuid.uuid4())
            start_time = self._parse_time_to_ms(segment.get("start_time", 0))
            end_time = self._parse_time_to_ms(segment.get("end_time", 0))
            duration = end_time - start_time
            
            # 视频片段
            video_segment = {
                "id": segment_id,
                "type": "video",
                "material_id": f"video_{i}",
                "track_render_index": 0,
                "source_timerange": {
                    "start": start_time,
                    "duration": duration
                },
                "target_timerange": {
                    "start": total_duration,
                    "duration": duration
                },
                "extra_material_refs": []
            }
            
            # 音频片段
            audio_segment = {
                "id": str(uuid.uuid4()),
                "type": "audio",
                "material_id": f"audio_{i}",
                "track_render_index": 0,
                "source_timerange": {
                    "start": start_time,
                    "duration": duration
                },
                "target_timerange": {
                    "start": total_duration,
                    "duration": duration
                }
            }
            
            # 字幕片段
            text_segment = {
                "id": str(uuid.uuid4()),
                "type": "text",
                "material_id": f"text_{i}",
                "track_render_index": 0,
                "source_timerange": {
                    "start": 0,
                    "duration": duration
                },
                "target_timerange": {
                    "start": total_duration,
                    "duration": duration
                },
                "extra_material_refs": []
            }
            
            video_track["segments"].append(video_segment)
            audio_track["segments"].append(audio_segment)
            text_track["segments"].append(text_segment)
            
            # 添加素材信息
            source_file = segment.get("source_file", "")
            
            # 视频素材
            video_material = {
                "id": f"video_{i}",
                "type": "video",
                "path": source_file,
                "duration": duration,
                "width": 1920,
                "height": 1080,
                "fps": 30
            }
            
            # 音频素材 - 修复：添加音频格式支持
            audio_material = {
                "id": f"audio_{i}",
                "type": "audio",
                "path": source_file,
                "duration": duration,
                "sample_rate": 44100,
                "channels": 2,
                "format": self._get_audio_format(source_file)  # 修复：添加格式字段
            }
            
            # 文本素材
            text_material = {
                "id": f"text_{i}",
                "type": "text",
                "content": segment.get("text", ""),
                "font_size": 24,
                "font_color": "#FFFFFF",
                "background_color": "#000000",
                "alignment": "center"
            }
            
            jianying_project["materials"]["videos"].append(video_material)
            jianying_project["materials"]["audios"].append(audio_material)
            jianying_project["materials"]["texts"].append(text_material)
            
            total_duration += duration
        
        # 添加轨道
        jianying_project["tracks"] = [video_track, audio_track, text_track]
        
        # 更新画布配置
        jianying_project["canvas_config"]["duration"] = total_duration
        jianying_project["extra_info"]["export_range"]["end"] = total_duration
        
        return jianying_project

    def _get_audio_format(self, file_path: str) -> str:
        """获取音频格式 - 修复：音频格式支持"""
        from pathlib import Path

        ext = Path(file_path).suffix.lower()
        format_map = {
            '.mp3': 'mp3',
            '.wav': 'wav',
            '.aac': 'aac',
            '.m4a': 'm4a',
            '.mp4': 'aac',  # MP4视频中的音频通常是AAC
            '.avi': 'mp3',  # AVI视频中的音频通常是MP3
            '.mov': 'aac',  # MOV视频中的音频通常是AAC
            '.mkv': 'aac',  # MKV视频中的音频通常是AAC
            '.flv': 'mp3'   # FLV视频中的音频通常是MP3
        }
        return format_map.get(ext, 'aac')  # 默认使用AAC格式

    def _parse_time_to_ms(self, time_value) -> int:
        """将时间值转换为毫秒

        Args:
            time_value: 时间值，可以是字符串（SRT格式）或数字

        Returns:
            int: 毫秒数
        """
        if isinstance(time_value, (int, float)):
            return int(time_value * 1000)

        if isinstance(time_value, str):
            # 解析SRT时间格式: "00:00:01,000" 或 "00:00:01.000"
            try:
                # 替换逗号为点号
                time_str = time_value.replace(',', '.')

                # 分割时:分:秒.毫秒
                if ':' in time_str:
                    parts = time_str.split(':')
                    if len(parts) == 3:
                        hours = int(parts[0])
                        minutes = int(parts[1])
                        seconds_parts = parts[2].split('.')
                        seconds = int(seconds_parts[0])
                        milliseconds = int(seconds_parts[1]) if len(seconds_parts) > 1 else 0

                        # 转换为总毫秒数
                        total_ms = (hours * 3600 + minutes * 60 + seconds) * 1000 + milliseconds
                        return total_ms

                # 如果是纯数字字符串
                return int(float(time_str) * 1000)

            except (ValueError, IndexError):
                logger.warning(f"无法解析时间格式: {time_value}")
                return 0

        return 0
    
    def create_project_package(self, project_data: Dict[str, Any], output_dir: str) -> bool:
        """
        创建完整的剪映工程包
        
        Args:
            project_data: 项目数据
            output_dir: 输出目录
            
        Returns:
            bool: 创建是否成功
        """
        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # 创建工程文件
            draft_file = output_path / "draft_content.json"
            success = self.export_project(project_data, str(draft_file))
            
            if success:
                # 创建工程元数据
                meta_file = output_path / "draft_meta_info.json"
                meta_data = {
                    "draft_id": str(uuid.uuid4()),
                    "draft_name": project_data.get("project_name", "VisionAI混剪项目"),
                    "draft_cover": "",
                    "draft_fold_path": str(output_path),
                    "tm_draft_create": int(time.time() * 1000),
                    "tm_draft_modified": int(time.time() * 1000),
                    "draft_removable": True
                }
                
                with open(meta_file, 'w', encoding='utf-8') as f:
                    json.dump(meta_data, f, ensure_ascii=False, indent=2)
                
                logger.info(f"剪映工程包已创建: {output_path}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"创建剪映工程包失败: {e}")
            return False
    
    def get_supported_formats(self) -> List[str]:
        """获取支持的导出格式"""
        return ["draft", "json"]
    
    def validate_project_data(self, project_data: Dict[str, Any]) -> bool:
        """验证项目数据格式"""
        required_fields = ["segments"]
        
        for field in required_fields:
            if field not in project_data:
                logger.error(f"项目数据缺少必需字段: {field}")
                return False
        
        segments = project_data.get("segments", [])
        if not segments:
            logger.error("项目数据中没有视频片段")
            return False
        
        for i, segment in enumerate(segments):
            required_segment_fields = ["start_time", "end_time", "source_file"]
            for field in required_segment_fields:
                if field not in segment:
                    logger.error(f"片段 {i} 缺少必需字段: {field}")
                    return False
        
        return True

# 便捷函数
def export_to_jianying(project_data: Dict[str, Any], output_path: str) -> bool:
    """
    导出到剪映专业版（便捷函数）
    
    Args:
        project_data: 项目数据
        output_path: 输出路径
        
    Returns:
        bool: 导出是否成功
    """
    exporter = JianYingProExporter()
    return exporter.export_project(project_data, output_path)
