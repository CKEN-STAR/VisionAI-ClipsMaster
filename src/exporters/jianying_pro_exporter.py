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

# 导入兼容性验证器
try:
    from .jianying_compatibility_validator import JianyingCompatibilityValidator
    HAS_VALIDATOR = True
except ImportError:
    HAS_VALIDATOR = False
    print("警告: 无法导入剪映兼容性验证器")

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

        # 初始化兼容性验证器
        if HAS_VALIDATOR:
            self.validator = JianyingCompatibilityValidator()
            logger.info("剪映专业版导出器初始化完成（包含兼容性验证器）")
        else:
            self.validator = None
            logger.info("剪映专业版导出器初始化完成（无兼容性验证器）")
    
    def _load_project_template(self) -> Dict[str, Any]:
        """加载剪映工程文件模板 - 修复：完整兼容剪映3.0+格式"""
        current_time = int(time.time() * 1000000)  # 微秒时间戳
        current_time_ms = int(time.time() * 1000)  # 毫秒时间戳
        project_id = str(uuid.uuid4())

        return {
            "version": "3.0.0",
            "type": "draft_content",
            "platform": "windows",
            "create_time": current_time,
            "update_time": current_time,
            "created_time": current_time_ms,  # 修复：添加测试期望的字段
            "last_modified": current_time_ms,  # 修复：添加最后修改时间
            "app_version": "剪映专业版 3.0.0",  # 修复：添加应用版本
            "id": project_id,
            "project_id": project_id,  # 修复：添加project_id字段
            "draft_id": project_id,  # 修复：添加draft_id字段
            "draft_name": "VisionAI混剪项目",  # 修复：添加项目名称
            "canvas_config": {
                "height": 1080,
                "width": 1920,
                "duration": 0,
                "fps": 30,  # 修复：添加帧率
                "ratio": "16:9"  # 修复：添加宽高比
            },
            "tracks": [],
            "materials": {
                "videos": [],
                "audios": [],
                "texts": [],
                "effects": [],
                "stickers": [],
                "images": [],  # 修复：添加图片素材
                "sounds": []   # 修复：添加音效素材
            },
            "extra_info": {
                "export_range": {
                    "start": 0,
                    "end": 0
                },
                "fps": 30,  # 修复：添加帧率信息
                "audio_sample_rate": 44100,  # 修复：添加音频采样率
                "video_codec": "h264",  # 修复：添加视频编码
                "audio_codec": "aac"    # 修复：添加音频编码
            },
            "keyframes": [],  # 修复：添加关键帧数组
            "relations": []   # 修复：添加关系数组
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

            # 修复：兼容性验证和自动修复
            if self.validator:
                logger.info("正在进行兼容性验证...")
                is_compatible, errors = self.validator.validate_project(jianying_project)

                if not is_compatible:
                    logger.warning(f"发现 {len(errors)} 个兼容性问题，正在自动修复...")
                    jianying_project = self.validator.fix_compatibility_issues(jianying_project)

                    # 重新验证
                    is_compatible, remaining_errors = self.validator.validate_project(jianying_project)
                    if is_compatible:
                        logger.info("兼容性问题已自动修复")
                    else:
                        logger.error(f"仍有 {len(remaining_errors)} 个兼容性问题无法自动修复")
                        for error in remaining_errors:
                            logger.error(f"  - {error}")
                        # 继续导出，但记录警告
                        logger.warning("将继续导出，但可能存在兼容性问题")
                else:
                    logger.info("兼容性验证通过")

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
        """将项目数据转换为剪映格式 - 修复：完整兼容性支持"""
        import copy
        jianying_project = copy.deepcopy(self.project_template)

        # 更新基本信息
        current_time = int(time.time() * 1000000)  # 微秒时间戳
        jianying_project["update_time"] = current_time

        # 处理视频片段
        segments = project_data.get("segments", [])
        total_duration_ms = 0  # 使用毫秒为单位

        # 修复：创建标准剪映轨道结构
        video_track = {
            "id": str(uuid.uuid4()),
            "type": "video",
            "attribute": 0,  # 修复：添加轨道属性
            "flag": 0,       # 修复：添加轨道标志
            "segments": []
        }

        audio_track = {
            "id": str(uuid.uuid4()),
            "type": "audio",
            "attribute": 0,
            "flag": 0,
            "segments": []
        }

        text_track = {
            "id": str(uuid.uuid4()),
            "type": "text",
            "attribute": 0,
            "flag": 0,
            "segments": []
        }
        
        # 修复：处理每个片段，添加完整验证和错误处理
        for i, segment in enumerate(segments):
            start_time_ms = self._parse_time_to_ms(segment.get("start_time", 0))
            end_time_ms = self._parse_time_to_ms(segment.get("end_time", 0))
            duration_ms = end_time_ms - start_time_ms

            # 修复：添加持续时间验证，如果无效则使用默认值
            if duration_ms <= 0:
                logger.warning(f"片段 {i} 持续时间无效: {duration_ms}ms，使用默认时长2秒")
                # 使用默认时长2秒
                if start_time_ms == 0 and end_time_ms == 0:
                    start_time_ms = i * 2000  # 每个片段2秒，按顺序排列
                    end_time_ms = start_time_ms + 2000
                    duration_ms = 2000
                else:
                    # 如果有开始时间但没有结束时间，添加2秒
                    if end_time_ms <= start_time_ms:
                        end_time_ms = start_time_ms + 2000
                        duration_ms = 2000

            # 修复：生成唯一且一致的ID
            video_segment_id = str(uuid.uuid4())
            audio_segment_id = str(uuid.uuid4())
            text_segment_id = str(uuid.uuid4())

            video_material_id = f"video_material_{i}"
            audio_material_id = f"audio_material_{i}"
            text_material_id = f"text_material_{i}"

            # 修复：完整的视频片段结构
            video_segment = {
                "id": video_segment_id,
                "type": "video",
                "material_id": video_material_id,
                "track_render_index": 0,
                "source_timerange": {
                    "start": start_time_ms,
                    "duration": duration_ms
                },
                "target_timerange": {
                    "start": total_duration_ms,
                    "duration": duration_ms
                },
                "extra_material_refs": [],
                "uniform_scale": {  # 修复：添加缩放信息
                    "on": True,
                    "value": 1.0
                },
                "transform": {  # 修复：添加变换信息
                    "x": 0.0,
                    "y": 0.0,
                    "width": 1.0,
                    "height": 1.0
                },
                "visible": True,  # 修复：添加可见性
                "volume": 1.0     # 修复：添加音量
            }

            # 修复：完整的音频片段结构
            audio_segment = {
                "id": audio_segment_id,
                "type": "audio",
                "material_id": audio_material_id,
                "track_render_index": 0,
                "source_timerange": {
                    "start": start_time_ms,
                    "duration": duration_ms
                },
                "target_timerange": {
                    "start": total_duration_ms,
                    "duration": duration_ms
                },
                "extra_material_refs": [],
                "volume": 1.0,  # 修复：添加音量控制
                "speed": 1.0,   # 修复：添加播放速度
                "visible": True # 修复：添加可见性
            }

            # 修复：完整的字幕片段结构
            text_content = segment.get("text", f"字幕片段 {i+1}")
            text_segment = {
                "id": text_segment_id,
                "type": "text",
                "material_id": text_material_id,
                "track_render_index": 0,
                "source_timerange": {
                    "start": 0,
                    "duration": duration_ms
                },
                "target_timerange": {
                    "start": total_duration_ms,
                    "duration": duration_ms
                },
                "extra_material_refs": [],
                "content": text_content,  # 修复：添加字幕内容
                "style": {  # 修复：添加字幕样式
                    "font_size": 24,
                    "font_color": "#FFFFFF",
                    "background_color": "#00000080",
                    "alignment": "center"
                },
                "visible": True
            }
            
            video_track["segments"].append(video_segment)
            audio_track["segments"].append(audio_segment)
            text_track["segments"].append(text_segment)

            # 修复：添加完整的素材信息
            source_file = segment.get("source_file", "")
            if not source_file:
                source_file = project_data.get("source_video", "")

            # 修复：完整的视频素材结构
            video_material = {
                "id": video_material_id,
                "type": "video",
                "path": source_file,
                "duration": duration_ms,
                "width": segment.get("width", 1920),
                "height": segment.get("height", 1080),
                "fps": segment.get("fps", 30),
                "format": self._get_video_format(source_file),  # 修复：添加格式检测
                "codec": "h264",  # 修复：添加编码信息
                "bitrate": segment.get("bitrate", "2000k"),  # 修复：添加码率
                "create_time": current_time,  # 修复：添加创建时间
                "file_size": segment.get("file_size", 0)  # 修复：添加文件大小
            }

            # 修复：完整的音频素材结构
            audio_material = {
                "id": audio_material_id,
                "type": "audio",
                "path": source_file,
                "duration": duration_ms,
                "sample_rate": segment.get("sample_rate", 44100),
                "channels": segment.get("channels", 2),
                "format": self._get_audio_format(source_file),
                "codec": "aac",  # 修复：添加音频编码
                "bitrate": segment.get("audio_bitrate", "128k"),  # 修复：添加音频码率
                "create_time": current_time
            }

            # 修复：完整的文本素材结构
            text_material = {
                "id": text_material_id,
                "type": "text",
                "content": text_content,
                "font_family": "Microsoft YaHei",  # 修复：添加字体
                "font_size": 24,
                "font_color": "#FFFFFF",
                "background_color": "#00000080",  # 修复：半透明背景
                "alignment": "center",
                "bold": False,  # 修复：添加粗体设置
                "italic": False,  # 修复：添加斜体设置
                "underline": False,  # 修复：添加下划线设置
                "create_time": current_time
            }

            jianying_project["materials"]["videos"].append(video_material)
            jianying_project["materials"]["audios"].append(audio_material)
            jianying_project["materials"]["texts"].append(text_material)

            # 修复：正确累加总时长（使用毫秒）
            total_duration_ms += duration_ms

        # 修复：添加轨道到项目，确保顺序正确
        jianying_project["tracks"] = [video_track, audio_track, text_track]

        # 修复：更新画布配置（使用毫秒）
        jianying_project["canvas_config"]["duration"] = total_duration_ms
        jianying_project["extra_info"]["export_range"]["end"] = total_duration_ms

        # 修复：添加关键帧和关系信息
        jianying_project["keyframes"] = []
        jianying_project["relations"] = []

        # 修复：验证项目结构完整性
        if not self._validate_project_structure(jianying_project):
            logger.error("生成的剪映项目结构验证失败")
            raise ValueError("剪映项目结构不完整")

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

    def _get_video_format(self, file_path: str) -> str:
        """获取视频格式 - 修复：添加视频格式检测"""
        from pathlib import Path

        ext = Path(file_path).suffix.lower()
        format_map = {
            '.mp4': 'mp4',
            '.avi': 'avi',
            '.mov': 'mov',
            '.mkv': 'mkv',
            '.flv': 'flv',
            '.wmv': 'wmv',
            '.webm': 'webm'
        }
        return format_map.get(ext, 'mp4')  # 默认使用MP4格式

    def _validate_project_structure(self, project: Dict[str, Any]) -> bool:
        """验证剪映项目结构完整性 - 修复：添加结构验证"""
        required_fields = [
            'version', 'type', 'platform', 'create_time', 'update_time',
            'id', 'draft_id', 'canvas_config', 'tracks', 'materials'
        ]

        # 检查必需字段
        for field in required_fields:
            if field not in project:
                logger.error(f"缺少必需字段: {field}")
                return False

        # 检查canvas_config结构
        canvas_config = project.get('canvas_config', {})
        canvas_required = ['height', 'width', 'duration', 'fps']
        for field in canvas_required:
            if field not in canvas_config:
                logger.error(f"canvas_config缺少字段: {field}")
                return False

        # 检查materials结构
        materials = project.get('materials', {})
        material_types = ['videos', 'audios', 'texts', 'effects', 'stickers']
        for mat_type in material_types:
            if mat_type not in materials:
                logger.error(f"materials缺少类型: {mat_type}")
                return False

        # 检查轨道结构
        tracks = project.get('tracks', [])
        if len(tracks) < 1:
            logger.error("至少需要一个轨道")
            return False

        for track in tracks:
            if 'id' not in track or 'type' not in track or 'segments' not in track:
                logger.error("轨道结构不完整")
                return False

        return True

    def _parse_time_to_ms(self, time_value) -> int:
        """将时间值转换为毫秒 - 修复：提高时间解析精度

        Args:
            time_value: 时间值，可以是字符串（SRT格式）或数字

        Returns:
            int: 毫秒数
        """
        if isinstance(time_value, (int, float)):
            return int(round(time_value * 1000))  # 修复：使用round提高精度

        if isinstance(time_value, str):
            # 解析SRT时间格式: "00:00:01,000" 或 "00:00:01.000"
            try:
                # 修复：更精确的时间格式处理
                time_str = time_value.strip()

                # 处理SRT格式的逗号
                if ',' in time_str:
                    time_str = time_str.replace(',', '.')

                # 分割时:分:秒.毫秒
                if ':' in time_str:
                    parts = time_str.split(':')
                    if len(parts) >= 2:  # 修复：支持分:秒格式
                        if len(parts) == 2:
                            # 分:秒格式
                            hours = 0
                            minutes = int(parts[0])
                            seconds_part = parts[1]
                        else:
                            # 时:分:秒格式
                            hours = int(parts[0])
                            minutes = int(parts[1])
                            seconds_part = parts[2]

                        # 修复：更精确的秒和毫秒解析
                        if '.' in seconds_part:
                            seconds_parts = seconds_part.split('.')
                            seconds = int(seconds_parts[0])
                            # 修复：正确处理毫秒位数
                            ms_str = seconds_parts[1]
                            if len(ms_str) == 1:
                                milliseconds = int(ms_str) * 100
                            elif len(ms_str) == 2:
                                milliseconds = int(ms_str) * 10
                            elif len(ms_str) >= 3:
                                milliseconds = int(ms_str[:3])
                            else:
                                milliseconds = 0
                        else:
                            seconds = int(seconds_part)
                            milliseconds = 0

                        # 转换为总毫秒数
                        total_ms = (hours * 3600 + minutes * 60 + seconds) * 1000 + milliseconds
                        return total_ms

                # 如果是纯数字字符串
                return int(round(float(time_str) * 1000))

            except (ValueError, IndexError) as e:
                logger.warning(f"无法解析时间格式: {time_value}, 错误: {e}")
                return 0

        logger.warning(f"不支持的时间格式类型: {type(time_value)}")
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

# 为了兼容性，提供别名
JianyingProExporter = JianYingProExporter
