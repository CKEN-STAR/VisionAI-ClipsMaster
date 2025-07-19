#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
XML更新器模块

提供对已有工程XML文件的增量更新功能，支持添加新片段、修改资源等操作
"""

import os
import logging
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime

from src.utils.log_handler import get_logger
from src.export.xml_encoder import sanitize_xml, normalize_file_path
from src.export.xml_builder import xml_to_string
from src.export.rollback_manager import with_xml_rollback, backup_xml, restore_xml
from src.exporters.simple_legal_logger import with_legal_audit

# 配置日志
logger = get_logger("xml_updater")

class XMLUpdater:
    """
    XML更新器
    
    用于对已有工程文件进行增量更新，如添加新片段等
    """
    
    def __init__(self):
        """初始化XML更新器"""
        self.logger = get_logger("xml_updater")
    
    @with_xml_rollback
    @with_legal_audit("append_clip")
    def append_clip(self, xml_path: str, new_clip: Dict[str, Any]) -> bool:
        """
        向已有工程文件追加新片段
        
        Args:
            xml_path: XML工程文件路径
            new_clip: 新片段信息，包含start_time、duration等
            
        Returns:
            bool: 更新是否成功
        """
        self.logger.info(f"向XML工程文件追加新片段: {xml_path}")
        
        try:
            # 解析XML文件
            tree = ET.parse(xml_path)
            
            # 获取根节点
            root = tree.getroot()
            
            # 查找视频轨道
            video_track = self._find_video_track(root)
            if video_track is None:
                self.logger.error("未找到视频轨道")
                return False
            
            # 计算新片段在轨道上的起始位置
            track_start = self._calculate_track_end(video_track)
            
            # 添加新片段
            self._add_clip_to_track(
                video_track, 
                new_clip.get('resource_id', 'video_1'),
                new_clip.get('start_time', 0.0),
                new_clip.get('duration', 5.0),
                new_clip.get('name', f"新片段_{datetime.now().strftime('%H%M%S')}"),
                track_start
            )
            
            # 同步添加音频片段（如果需要）
            if new_clip.get('has_audio', True):
                audio_track = self._find_audio_track(root)
                if audio_track is not None:
                    self._add_clip_to_track(
                        audio_track,
                        new_clip.get('resource_id', 'video_1'),
                        new_clip.get('start_time', 0.0),
                        new_clip.get('duration', 5.0),
                        f"{new_clip.get('name', '新片段')}音频",
                        track_start
                    )
                
            # 保存修改后的XML
            tree.write(xml_path, encoding='utf-8', xml_declaration=True)
            self.logger.info(f"成功添加新片段到XML工程文件: {xml_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"向XML添加片段失败: {str(e)}")
            return False
    
    @with_xml_rollback
    @with_legal_audit("append_clips")
    def append_clips(self, xml_path: str, new_clips: List[Dict[str, Any]]) -> bool:
        """
        向已有工程文件批量追加多个新片段
        
        Args:
            xml_path: XML工程文件路径
            new_clips: 新片段信息列表
            
        Returns:
            bool: 更新是否成功
        """
        self.logger.info(f"向XML工程文件批量追加{len(new_clips)}个新片段: {xml_path}")
        
        try:
            # 解析XML文件
            tree = ET.parse(xml_path)
            
            # 获取根节点
            root = tree.getroot()
            
            # 查找视频轨道
            video_track = self._find_video_track(root)
            if video_track is None:
                self.logger.error("未找到视频轨道")
                return False
            
            # 计算新片段在轨道上的起始位置
            track_start = self._calculate_track_end(video_track)
            
            # 查找音频轨道
            audio_track = self._find_audio_track(root)
            
            # 批量添加新片段
            current_pos = track_start
            for i, clip in enumerate(new_clips):
                # 添加视频片段
                self._add_clip_to_track(
                    video_track, 
                    clip.get('resource_id', 'video_1'),
                    clip.get('start_time', 0.0),
                    clip.get('duration', 5.0),
                    clip.get('name', f"新片段_{i+1}_{datetime.now().strftime('%H%M%S')}"),
                    current_pos
                )
                
                # 同步添加音频片段（如果需要）
                if clip.get('has_audio', True) and audio_track is not None:
                    self._add_clip_to_track(
                        audio_track,
                        clip.get('resource_id', 'video_1'),
                        clip.get('start_time', 0.0),
                        clip.get('duration', 5.0),
                        f"{clip.get('name', f'新片段_{i+1}')}音频",
                        current_pos
                    )
                
                # 更新下一个片段的位置
                current_pos += clip.get('duration', 5.0)
            
            # 保存修改后的XML
            tree.write(xml_path, encoding='utf-8', xml_declaration=True)
            self.logger.info(f"成功添加{len(new_clips)}个新片段到XML工程文件: {xml_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"向XML批量添加片段失败: {str(e)}")
            return False
    
    @with_xml_rollback
    @with_legal_audit("add_resource")
    def add_resource(self, xml_path: str, resource: Dict[str, Any]) -> bool:
        """
        向XML工程添加新资源
        
        Args:
            xml_path: XML工程文件路径
            resource: 资源信息
            
        Returns:
            bool: 添加是否成功
        """
        try:
            # 解析XML文件
            tree = ET.parse(xml_path)
            root = tree.getroot()
            
            # 查找资源区域
            resources_elem = self._find_resources_element(root)
            if resources_elem is None:
                self.logger.error("未找到资源区域")
                return False
                
            # 检查资源是否已存在
            resource_id = resource.get('id', f"resource_{len(resources_elem)}")
            if self._resource_exists(resources_elem, resource_id):
                self.logger.info(f"资源 {resource_id} 已存在，跳过添加")
                return True
                
            # 创建新资源节点
            resource_elem = ET.SubElement(resources_elem, "resource", {
                "id": resource_id,
                "type": resource.get('type', 'video'),
            })
            
            # 添加资源属性
            for key, value in resource.items():
                if key not in ['id', 'type']:
                    elem = ET.SubElement(resource_elem, key)
                    elem.text = str(value)
            
            # 保存修改后的XML
            tree.write(xml_path, encoding='utf-8', xml_declaration=True)
            self.logger.info(f"成功添加资源 {resource_id} 到XML工程文件")
            return True
            
        except Exception as e:
            self.logger.error(f"添加资源失败: {str(e)}")
            return False
    
    @with_xml_rollback
    @with_legal_audit("change_project_settings")
    def change_project_settings(self, xml_path: str, settings: Dict[str, Any]) -> bool:
        """
        更改项目设置
        
        Args:
            xml_path: XML工程文件路径
            settings: 设置信息
            
        Returns:
            bool: 更新是否成功
        """
        try:
            # 解析XML文件
            tree = ET.parse(xml_path)
            root = tree.getroot()
            
            # 查找项目设置区域
            settings_elem = root.find(".//settings")
            if settings_elem is None:
                # 部分工程可能没有独立的settings节点
                settings_elem = ET.SubElement(root, "settings")
            
            # 更新设置
            for key, value in settings.items():
                # 查找设置节点
                setting_elem = settings_elem.find(key)
                if setting_elem is None:
                    # 如果设置不存在，创建新节点
                    setting_elem = ET.SubElement(settings_elem, key)
                
                # 更新设置值
                setting_elem.text = str(value)
            
            # 保存修改后的XML
            tree.write(xml_path, encoding='utf-8', xml_declaration=True)
            self.logger.info(f"成功更新项目设置: {xml_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"更新项目设置失败: {str(e)}")
            return False
    
    def _find_video_track(self, root: ET.Element) -> Optional[ET.Element]:
        """查找视频轨道"""
        # 尝试不同格式查找视频轨道
        track = root.find(".//track[@type='video']")
        if track is not None:
            return track
            
        track = root.find(".//video/track")
        if track is not None:
            return track
        
        track = root.find(".//timeline/track")
        if track is not None:
            return track
            
        # Final Cut Pro格式
        track = root.find(".//spine")
        return track
    
    def _find_audio_track(self, root: ET.Element) -> Optional[ET.Element]:
        """查找音频轨道"""
        # 尝试不同格式查找音频轨道
        track = root.find(".//track[@type='audio']")
        if track is not None:
            return track
            
        track = root.find(".//audio/track")
        return track
    
    def _find_resources_element(self, root: ET.Element) -> Optional[ET.Element]:
        """查找资源元素"""
        # 尝试不同格式查找资源区域
        resources = root.find("resources")
        if resources is not None:
            return resources
            
        resources = root.find("asset-list")
        if resources is not None:
            return resources
            
        # 没有找到时，可能需要创建
        if root.tag == "project":
            return ET.SubElement(root, "resources")
        
        return None
    
    def _calculate_track_end(self, track: ET.Element) -> float:
        """计算轨道当前结束位置"""
        # 获取所有片段
        clips = track.findall(".//clip") or track.findall("clipitem")
        if not clips:
            return 0.0
        
        # 计算每个片段的结束位置
        max_end = 0.0
        
        for clip in clips:
            # 适配不同格式
            if 'trackStart' in clip.attrib and 'duration' in clip.attrib:
                # 标准格式
                track_start = float(clip.attrib.get('trackStart', '0.0'))
                duration = float(clip.attrib.get('duration', '0.0'))
                end_pos = track_start + duration
                
            elif clip.find("start") is not None and clip.find("end") is not None:
                # Premiere格式
                start = float(clip.find("start").text)
                end = float(clip.find("end").text)
                end_pos = end
                
            elif 'offset' in clip.attrib and 'duration' in clip.attrib:
                # FCPXML格式
                offset = self._parse_timecode(clip.attrib.get('offset', '0s'))
                duration = self._parse_timecode(clip.attrib.get('duration', '0s'))
                end_pos = offset + duration
                
            else:
                # 无法确定位置的情况
                continue
            
            max_end = max(max_end, end_pos)
        
        return max_end
    
    def _add_clip_to_track(self, track: ET.Element, resource_id: str, 
                          start_time: float, duration: float, 
                          clip_name: str, track_start: float) -> ET.Element:
        """添加片段到轨道"""
        # 根据轨道类型选择适当的添加方式
        if track.tag == "spine":
            # FCPXML格式
            return self._add_clip_to_fcpxml(track, resource_id, start_time, 
                                           duration, clip_name, track_start)
        else:
            # 标准格式
            return self._add_clip_standard(track, resource_id, start_time, 
                                         duration, clip_name, track_start)
    
    def _add_clip_standard(self, track: ET.Element, resource_id: str, 
                          start_time: float, duration: float, 
                          clip_name: str, track_start: float) -> ET.Element:
        """添加标准格式片段"""
        clip = ET.SubElement(track, "clip", {
            "name": clip_name,
            "resourceId": resource_id,
            "start": str(start_time),
            "duration": str(duration),
            "trackStart": str(track_start)
        })
        return clip
    
    def _add_clip_to_fcpxml(self, spine: ET.Element, resource_id: str, 
                           start_time: float, duration: float, 
                           clip_name: str, track_start: float) -> ET.Element:
        """添加FCPXML格式片段"""
        # 转换为时间码
        offset_tc = self._seconds_to_timecode(track_start)
        duration_tc = self._seconds_to_timecode(duration)
        start_tc = self._seconds_to_timecode(start_time)
        
        # 创建剪辑节点
        clip = ET.SubElement(spine, "clip", {
            "name": clip_name,
            "offset": offset_tc,
            "duration": duration_tc,
            "start": start_tc,
            "tcFormat": "NDF"
        })
        
        # 添加视频引用
        video = ET.SubElement(clip, "video", {
            "name": clip_name,
            "offset": self._seconds_to_timecode(0),
            "ref": resource_id,
            "duration": duration_tc
        })
        
        return clip
    
    def _parse_timecode(self, tc_str: str) -> float:
        """解析时间码为秒数"""
        # 处理形如 "10s" 或 "00:00:10:00" 的时间码
        if tc_str.endswith('s'):
            return float(tc_str[:-1])
        elif ':' in tc_str:
            parts = tc_str.split(':')
            if len(parts) == 4:  # 00:00:10:00 格式
                h, m, s, f = map(int, parts)
                return h * 3600 + m * 60 + s + f / 30  # 假设30fps
        
        # 无法解析时返回0
        return 0.0
    
    def _seconds_to_timecode(self, seconds: float) -> str:
        """将秒数转换为FCPXML时间码"""
        return f"{seconds}s"
    
    def _resource_exists(self, resources_elem: ET.Element, resource_id: str) -> bool:
        """检查资源是否已存在"""
        resource = resources_elem.find(f"./resource[@id='{resource_id}']")
        if resource is not None:
            return True
            
        resource = resources_elem.find(f"./asset[@id='{resource_id}']")
        return resource is not None 