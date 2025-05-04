#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
剪映导出器模块

导出为剪映应用可导入的项目格式
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
            version: 版本数据，包含场景和剪辑信息
            output_path: 输出文件路径
            
        Returns:
            生成的文件路径
        """
        if not self._validate_version(version):
            raise ValueError("无效的版本数据")
        
        self._ensure_output_directory(output_path)
        
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
        # 获取版本信息
        scenes = version.get('scenes', [])
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
        
        # 当前时间点
        current_time = 0
        
        for i, scene in enumerate(scenes):
            # 获取场景信息
            scene_id = scene.get('scene_id', f"scene_{i+1}")
            start_time = float(scene.get('start_time', i * 5))  # 默认每5秒一个场景
            duration = float(scene.get('duration', 5))  # 默认5秒
            
            # 创建视频片段
            video_segment = {
                "id": str(uuid.uuid4()),
                "material_id": draft["materials"]["videos"][0]["id"] if draft["materials"]["videos"] else "",
                "start_time": start_time,
                "duration": duration,
                "target_timerange": {
                    "start": current_time,
                    "duration": duration
                }
            }
            
            main_video_segments.append(video_segment)
            
            # 创建音频片段（如果需要）
            if scene.get('has_audio', True):
                audio_segment = {
                    "id": str(uuid.uuid4()),
                    "material_id": draft["materials"]["videos"][0]["id"] if draft["materials"]["videos"] else "",
                    "start_time": start_time,
                    "duration": duration,
                    "target_timerange": {
                        "start": current_time,
                        "duration": duration
                    }
                }
                
                main_audio_segments.append(audio_segment)
            
            # 更新当前时间
            current_time += duration
        
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