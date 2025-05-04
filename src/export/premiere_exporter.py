#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Premiere XML导出器模块

导出Premiere Pro XML格式项目文件
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

class PremiereXMLExporter(BaseExporter):
    """
    Premiere XML导出器
    
    将版本数据导出为Premiere Pro可导入的XML格式
    """
    
    def __init__(self):
        """初始化Premiere XML导出器"""
        super().__init__("Premiere")
        self.fps = 30.0  # 默认帧率
        self.framerate_numerator = 30
        self.framerate_denominator = 1
        
    def export(self, version: Dict[str, Any], output_path: str) -> str:
        """
        将版本数据导出为Premiere XML格式
        
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
        root = ET.Element("xmeml", {"version": "5"})
        
        # 创建项目节点
        project = ET.SubElement(root, "project")
        name = ET.SubElement(project, "name")
        name.text = f"VisionAI_{version_id}_{self._create_timestamp()}"
        
        # 创建序列节点
        sequence = ET.SubElement(project, "sequence")
        seq_name = ET.SubElement(sequence, "name")
        seq_name.text = f"混剪序列_{version_id}"
        
        # 时间设置
        self._add_timing_settings(sequence)
        
        # 设置媒体节点
        media = ET.SubElement(sequence, "media")
        
        # 添加视频轨道
        video = ET.SubElement(media, "video")
        self._add_video_track(video, scenes)
        
        # 添加音频轨道（如果需要）
        audio = ET.SubElement(media, "audio")
        self._add_audio_track(audio, scenes)
        
        # 格式化XML并写入文件
        try:
            xml_string = ET.tostring(root, encoding='utf-8')
            dom = minidom.parseString(xml_string)
            pretty_xml = dom.toprettyxml(indent="  ", encoding='utf-8')
            
            with open(output_path, 'wb') as f:
                f.write(pretty_xml)
            
            self.logger.info(f"已导出Premiere XML文件: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"导出Premiere XML文件失败: {str(e)}")
            raise
    
    def _add_timing_settings(self, sequence: ET.Element) -> None:
        """
        添加时间设置节点
        
        Args:
            sequence: 序列节点
        """
        # 时间设置
        rate = ET.SubElement(sequence, "rate")
        timebase = ET.SubElement(rate, "timebase")
        timebase.text = str(int(self.fps))
        ntsc = ET.SubElement(rate, "ntsc")
        ntsc.text = "FALSE"
        
        # 时间码设置
        timecode = ET.SubElement(sequence, "timecode")
        tc_rate = ET.SubElement(timecode, "rate")
        tc_timebase = ET.SubElement(tc_rate, "timebase")
        tc_timebase.text = str(int(self.fps))
        tc_ntsc = ET.SubElement(tc_rate, "ntsc")
        tc_ntsc.text = "FALSE"
        tc_format = ET.SubElement(timecode, "format")
        tc_format.text = "NonDropFrame"
        tc_source = ET.SubElement(timecode, "source")
        tc_source.text = "source"
        
    def _add_video_track(self, video: ET.Element, scenes: List[Dict[str, Any]]) -> None:
        """
        添加视频轨道
        
        Args:
            video: 视频节点
            scenes: 场景列表
        """
        # 创建视频轨道
        track = ET.SubElement(video, "track")
        
        # 累计时间点
        current_time = 0
        
        # 为每个场景创建剪辑
        for i, scene in enumerate(scenes):
            # 获取场景信息
            start_time = scene.get('start_time', i * 5)  # 默认每5秒一个场景
            duration = scene.get('duration', 5)  # 默认5秒
            
            # 创建剪辑节点
            clipitem = ET.SubElement(track, "clipitem", {"id": f"clipitem-{i+1}"})
            
            # 设置剪辑名称
            name = ET.SubElement(clipitem, "name")
            name.text = scene.get('scene_id', f"场景_{i+1}")
            
            # 设置剪辑启用状态
            enabled = ET.SubElement(clipitem, "enabled")
            enabled.text = "TRUE"
            
            # 设置剪辑时间范围
            in_point = ET.SubElement(clipitem, "in")
            in_point.text = self._seconds_to_frames(start_time)
            
            out_point = ET.SubElement(clipitem, "out")
            out_point.text = self._seconds_to_frames(start_time + duration)
            
            # 设置序列中的位置
            start = ET.SubElement(clipitem, "start")
            start.text = self._seconds_to_frames(current_time)
            
            end = ET.SubElement(clipitem, "end")
            end.text = self._seconds_to_frames(current_time + duration)
            
            # 更新当前时间点
            current_time += duration
    
    def _add_audio_track(self, audio: ET.Element, scenes: List[Dict[str, Any]]) -> None:
        """
        添加音频轨道
        
        Args:
            audio: 音频节点
            scenes: 场景列表
        """
        # 创建音频轨道
        track = ET.SubElement(audio, "track")
        
        # 累计时间点
        current_time = 0
        
        # 为每个场景创建剪辑
        for i, scene in enumerate(scenes):
            if not scene.get('has_audio', True):
                continue
                
            # 获取场景信息
            start_time = scene.get('start_time', i * 5)  # 默认每5秒一个场景
            duration = scene.get('duration', 5)  # 默认5秒
            
            # 创建剪辑节点
            clipitem = ET.SubElement(track, "clipitem", {"id": f"audio-clipitem-{i+1}"})
            
            # 设置剪辑名称
            name = ET.SubElement(clipitem, "name")
            name.text = scene.get('scene_id', f"音频_{i+1}")
            
            # 设置剪辑启用状态
            enabled = ET.SubElement(clipitem, "enabled")
            enabled.text = "TRUE"
            
            # 设置剪辑时间范围
            in_point = ET.SubElement(clipitem, "in")
            in_point.text = self._seconds_to_frames(start_time)
            
            out_point = ET.SubElement(clipitem, "out")
            out_point.text = self._seconds_to_frames(start_time + duration)
            
            # 设置序列中的位置
            start = ET.SubElement(clipitem, "start")
            start.text = self._seconds_to_frames(current_time)
            
            end = ET.SubElement(clipitem, "end")
            end.text = self._seconds_to_frames(current_time + duration)
            
            # 更新当前时间点
            current_time += duration
    
    def _seconds_to_frames(self, seconds: float) -> str:
        """
        将秒数转换为帧数
        
        Args:
            seconds: 秒数
            
        Returns:
            帧数字符串
        """
        frames = int(seconds * self.fps)
        return str(frames) 