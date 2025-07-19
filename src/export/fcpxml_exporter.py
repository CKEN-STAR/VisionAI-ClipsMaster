#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
FCPXML导出器模块

导出Final Cut Pro XML格式项目文件
"""

import os
import json
import logging
import xml.dom.minidom as minidom
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

from src.export.base_exporter import BaseExporter
from src.utils.log_handler import get_logger

class FCPXMLExporter(BaseExporter):
    """
    FCPXML导出器
    
    将版本数据导出为Final Cut Pro可导入的FCPXML格式
    """
    
    def __init__(self):
        """初始化FCPXML导出器"""
        super().__init__("FCPX")
        self.fps = 30.0  # 默认帧率
        self.format_id = "r1"  # 资源格式ID
        self.project_id = "p1"  # 项目ID
        self.sequence_id = "s1"  # 序列ID
        
    def export(self, version: Dict[str, Any], output_path: str) -> str:
        """
        将版本数据导出为FCPXML格式
        
        Args:
            version: 版本数据，包含场景和剪辑信息
            output_path: 输出文件路径
            
        Returns:
            生成的XML文件路径
        """
        if not self._validate_version(version):
            raise ValueError("无效的版本数据")
        
        self._ensure_output_directory(output_path)
        
        # 获取版本信息
        scenes = version.get('scenes', [])
        version_id = version.get('version_id', 'unknown')
        
        # 创建XML根节点
        root = ET.Element("fcpxml", {
            "version": "1.8",
            "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance"
        })
        
        # 创建资源列表
        resources = ET.SubElement(root, "resources")
        
        # 添加格式定义
        self._add_format(resources)
        
        # 添加项目资源
        ET.SubElement(resources, "projectref", {
            "id": self.project_id,
            "name": f"VisionAI_{version_id}_{self._create_timestamp()}"
        })
        
        # 创建库节点
        library = ET.SubElement(root, "library")
        
        # 创建事件节点
        event = ET.SubElement(library, "event", {"name": f"VisionAI_{version_id}"})
        
        # 创建项目节点
        project = ET.SubElement(event, "project", {
            "id": self.project_id,
            "name": f"VisionAI_{version_id}"
        })
        
        # 创建序列节点
        sequence = ET.SubElement(project, "sequence", {
            "id": self.sequence_id,
            "format": self.format_id,
            "duration": self._seconds_to_timecode(sum(s.get('duration', 5) for s in scenes))
        })
        
        # 创建主轨道
        spine = ET.SubElement(sequence, "spine")
        
        # 为每个场景创建剪辑
        self._add_clips_to_spine(spine, scenes)
        
        # 格式化XML并写入文件
        try:
            xml_string = ET.tostring(root, encoding='utf-8')
            dom = minidom.parseString(xml_string)
            pretty_xml = dom.toprettyxml(indent="  ", encoding='utf-8')
            
            with open(output_path, 'wb') as f:
                f.write(pretty_xml)
            
            self.logger.info(f"已导出FCPXML文件: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"导出FCPXML文件失败: {str(e)}")
            raise
    
    def _add_format(self, resources: ET.Element) -> None:
        """
        添加格式资源
        
        Args:
            resources: 资源节点
        """
        ET.SubElement(resources, "format", {
            "id": self.format_id,
            "name": "FFVideoFormat1080p30",
            "frameDuration": "1/30s",
            "width": "1920",
            "height": "1080"
        })
    
    def _add_clips_to_spine(self, spine: ET.Element, scenes: List[Dict[str, Any]]) -> None:
        """
        向主轨道添加剪辑
        
        Args:
            spine: 主轨道节点
            scenes: 场景列表
        """
        # 累计开始时间
        current_start = 0
        
        for i, scene in enumerate(scenes):
            # 获取场景信息
            scene_id = scene.get('scene_id', f"scene_{i+1}")
            start_time = scene.get('start_time', i * 5)  # 默认每5秒一个场景
            duration = scene.get('duration', 5)  # 默认5秒
            
            # 创建剪辑ID
            clip_id = f"clip_{i+1}"
            
            # 创建剪辑节点
            clip = ET.SubElement(spine, "clip", {
                "name": scene_id,
                "offset": self._seconds_to_timecode(current_start),
                "duration": self._seconds_to_timecode(duration),
                "start": self._seconds_to_timecode(start_time),
                "tcFormat": "NDF"
            })
            
            # 添加片段视频
            video = ET.SubElement(clip, "video", {
                "name": scene_id,
                "offset": self._seconds_to_timecode(0),
                "ref": f"r{i+2}",  # 假设资源引用ID
                "duration": self._seconds_to_timecode(duration)
            })
            
            # 添加片段音频（如果有）
            if scene.get('has_audio', True):
                audio = ET.SubElement(clip, "audio", {
                    "name": f"{scene_id}_audio",
                    "offset": self._seconds_to_timecode(0),
                    "ref": f"r{i+2}a",  # 假设音频资源引用ID
                    "duration": self._seconds_to_timecode(duration)
                })
            
            # 更新当前开始时间
            current_start += duration
    
    def _seconds_to_timecode(self, seconds: float) -> str:
        """
        将秒数转换为FCP时间码格式
        
        Args:
            seconds: 秒数
            
        Returns:
            FCP时间码字符串，格式为"HH:MM:SS:FF/30"
        """
        total_frames = int(seconds * self.fps)
        frames = total_frames % int(self.fps)
        total_seconds = total_frames // int(self.fps)
        
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        secs = total_seconds % 60
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d}:{frames:02d}/30" 