#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
剪映导出器模块

导出为剪映应用可导入的项目格式

重构说明：
- 使用新的JianyingExporterAdapter（基于pyCapCut实现）
- 保持向后兼容性
"""

import os
import json
import logging
import zipfile
import uuid
import shutil
from typing import Dict, List, Any, Optional
from datetime import datetime

from src.export.base_exporter import BaseExporter
from src.utils.log_handler import get_logger

# 导入新的导出器适配器
try:
    from src.exporters.jianying_exporter_adapter import JianyingExporterAdapter
    HAS_NEW_EXPORTER = True
except ImportError:
    HAS_NEW_EXPORTER = False
    print("警告: 无法导入新的剪映导出器适配器")

class JianyingExporter(BaseExporter):
    """
    剪映导出器
    
    将版本数据导出为剪映应用可导入的项目格式
    """
    
    def __init__(self):
        """初始化剪映导出器"""
        super().__init__("剪映")
        self.draft_template = {
            "id": "",
            "materials": {
                "videos": []
            },
            "tracks": {
                "main_video_track": {
                    "segments": []
                },
                "main_audio_track": {
                    "segments": []
                }
            },
            "canvas_setting": {
                "width": 1920,
                "height": 1080,
                "fps": 30
            }
        }
    
    def export(self, version: Dict[str, Any], output_path: str) -> str:
        """
        将版本数据导出为剪映格式

        Args:
            version: 版本数据，包含场景和剪辑信息或segments信息
            output_path: 输出文件路径

        Returns:
            生成的文件路径
        """
        # 优先使用新的导出器（不需要严格的版本验证）
        if HAS_NEW_EXPORTER:
            self.logger.info("使用新的剪映导出器（基于pyCapCut实现）")
            try:
                # 提取segments数据
                segments = version.get('segments', [])
                if not segments:
                    # 尝试从scenes中提取
                    scenes = version.get('scenes', [])
                    segments = []
                    for scene in scenes:
                        clips = scene.get('clips', [])
                        segments.extend(clips)

                # 如果还是没有segments，记录警告但继续
                if not segments:
                    self.logger.warning("未找到segments或scenes数据，将生成空项目")

                # 创建适配器
                canvas = self.draft_template.get('canvas_setting', {})
                adapter = JianyingExporterAdapter(
                    width=canvas.get('width', 1920),
                    height=canvas.get('height', 1080),
                    fps=canvas.get('fps', 30)
                )

                # 构建项目数据
                project_data = {
                    "project_name": version.get('project_name') or version.get('version_id', 'VisionAI_Project'),
                    "segments": segments
                }

                # 导出
                actual_path = adapter.export_project(project_data, output_path)

                if actual_path:
                    self.logger.info(f"已导出剪映项目文件: {actual_path}")
                    return actual_path
                else:
                    self.logger.warning("新导出器导出失败，尝试使用旧导出器")
                    # 继续使用旧导出器
            except Exception as e:
                self.logger.error(f"新导出器出错: {e}，尝试使用旧导出器")
                # 继续使用旧导出器
        else:
            self.logger.warning("新导出器不可用，使用旧导出器")

        # 使用旧导出器时才进行严格验证
        if not self._validate_version(version):
            raise ValueError("无效的版本数据")

        self._ensure_output_directory(output_path)

        # 使用旧的导出器（向后兼容）
        # 获取版本信息
        scenes = version.get('scenes', [])
        version_id = version.get('version_id', 'unknown')

        # 创建临时目录 - 使用uuid确保唯一性
        temp_dir = os.path.join(self.temp_dir, f"jianying_export_{uuid.uuid4().hex}")
        os.makedirs(temp_dir, exist_ok=True)

        try:
            # 创建草稿文件
            draft_path = os.path.join(temp_dir, "draft_content.json")
            self._create_draft_file(version, draft_path)

            # 如果导出的是压缩包
            if output_path.endswith('.zip'):
                # 创建压缩文件
                with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    zipf.write(draft_path, arcname="draft_content.json")

                self.logger.info(f"已导出剪映项目压缩包: {output_path}")

            else:
                # 复制文件
                shutil.copy2(draft_path, output_path)
                self.logger.info(f"已导出剪映项目文件: {output_path}")

            return output_path

        except Exception as e:
            self.logger.error(f"导出剪映项目失败: {str(e)}")
            raise

        finally:
            # 清理临时目录
            if os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except Exception as e:
                    self.logger.warning(f"清理临时目录失败: {str(e)}")
    
    def _create_draft_file(self, version: Dict[str, Any], output_path: str) -> None:
        """
        创建剪映草稿文件
        
        Args:
            version: 版本数据
            output_path: 输出文件路径
        """
        # 关键修复：直接使用 version 中的 segments 数据，不再错误地重新计算时间轴
        segments = version.get('segments', [])
        version_id = version.get('version_id', 'unknown')

        # 创建草稿结构
        draft = self.draft_template.copy()
        draft["id"] = str(uuid.uuid4())

        # 假设视频素材已存在
        video_path = version.get('video_path', "")
        if video_path:
            video_material = {
                "id": str(uuid.uuid4()),
                "path": video_path,
                "name": os.path.basename(video_path)
            }
            draft["materials"]["videos"].append(video_material)

        # 添加视频轨道片段
        main_video_segments = []
        main_audio_segments = []

        timeline_cursor = 0  # 时间线上的当前位置

        for segment in segments:
            # 使用 segment 中已经过AI处理和时间轴重建的精确时间码
            source_start_time = float(segment.get('start_time', 0))
            source_end_time = float(segment.get('end_time', 0))
            duration = source_end_time - source_start_time

            if duration <= 0:
                continue

            # 创建视频片段
            video_segment = {
                "id": str(uuid.uuid4()),
                "material_id": draft["materials"]["videos"][0]["id"] if draft["materials"]["videos"] else "",
                "start_time": source_start_time,  # 源素材的开始时间
                "duration": duration,  # 源素材的持续时间
                "target_timerange": {
                    "start": timeline_cursor,  # 在剪映时间线上的开始位置
                    "duration": duration
                }
            }
            main_video_segments.append(video_segment)

            # 创建音频片段
            audio_segment = video_segment.copy()  # 音视频同步
            audio_segment["id"] = str(uuid.uuid4())
            main_audio_segments.append(audio_segment)

            # 更新时间线光标
            timeline_cursor += duration

        # 更新轨道信息
        draft["tracks"]["main_video_track"]["segments"] = main_video_segments
        draft["tracks"]["main_audio_track"]["segments"] = main_audio_segments
        
        # 添加项目元数据
        draft["meta"] = {
            "name": f"VisionAI_{version_id}_{self._create_timestamp()}",
            "create_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "duration": current_time
        }
        
        # 写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(draft, f, indent=2, ensure_ascii=False) 