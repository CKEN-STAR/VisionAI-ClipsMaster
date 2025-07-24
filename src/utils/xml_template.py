#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
XML模板工具
提供XML工程文件模板生成功能
"""

import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
import os
from datetime import datetime
from .log_handler import get_logger

logger = get_logger(__name__)

class XMLTemplate:
    """XML模板生成器"""
    
    def __init__(self):
        """初始化XML模板生成器"""
        self.templates = {
            "fcpxml": self._get_fcpxml_template(),
            "davinci": self._get_davinci_template(),
            "premiere": self._get_premiere_template()
        }
        
        logger.info("📄 XML模板生成器初始化完成")
    
    def generate_fcpxml(self, video_path: str, subtitles: List[Dict], 
                       project_name: str = "VisionAI_Project") -> str:
        """
        生成Final Cut Pro XML
        
        Args:
            video_path: 视频文件路径
            subtitles: 字幕列表
            project_name: 项目名称
            
        Returns:
            str: XML内容
        """
        try:
            # 创建根元素
            fcpxml = ET.Element("fcpxml", version="1.10")
            
            # 添加资源
            resources = ET.SubElement(fcpxml, "resources")
            
            # 添加视频资源
            video_name = os.path.basename(video_path)
            video_id = f"r{hash(video_name) % 10000}"
            
            asset = ET.SubElement(resources, "asset", 
                                id=video_id,
                                name=video_name,
                                src=video_path,
                                hasVideo="1",
                                hasAudio="1")
            
            # 添加项目
            library = ET.SubElement(fcpxml, "library")
            event = ET.SubElement(library, "event", name="VisionAI Event")
            project = ET.SubElement(event, "project", name=project_name)
            
            # 添加序列
            sequence = ET.SubElement(project, "sequence", 
                                   format="r1",
                                   tcStart="0s",
                                   tcFormat="NDF",
                                   audioLayout="stereo",
                                   audioRate="48k")
            
            spine = ET.SubElement(sequence, "spine")
            
            # 添加视频片段
            for i, subtitle in enumerate(subtitles):
                start_time = self._time_to_seconds(subtitle.get("start", "00:00:00,000"))
                end_time = self._time_to_seconds(subtitle.get("end", "00:00:00,000"))
                duration = end_time - start_time
                
                clip = ET.SubElement(spine, "asset-clip",
                                   ref=video_id,
                                   offset=f"{start_time}s",
                                   name=f"Clip_{i+1}",
                                   start=f"{start_time}s",
                                   duration=f"{duration}s")
                
                # 添加字幕
                if subtitle.get("text"):
                    title = ET.SubElement(clip, "title",
                                        ref="r2",
                                        offset="0s",
                                        duration=f"{duration}s",
                                        name="Basic Title")
                    
                    text_elem = ET.SubElement(title, "text")
                    text_style = ET.SubElement(text_elem, "text-style", ref="ts1")
                    text_style.text = subtitle.get("text", "")
            
            # 转换为字符串
            xml_str = ET.tostring(fcpxml, encoding='unicode')
            
            # 添加XML声明
            xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_str
            
            logger.info(f"📄 FCPXML生成完成，包含 {len(subtitles)} 个片段")
            return xml_content
            
        except Exception as e:
            logger.error(f"FCPXML生成失败: {e}")
            return ""
    
    def generate_davinci_xml(self, video_path: str, subtitles: List[Dict],
                           project_name: str = "VisionAI_Project") -> str:
        """
        生成DaVinci Resolve XML
        
        Args:
            video_path: 视频文件路径
            subtitles: 字幕列表
            project_name: 项目名称
            
        Returns:
            str: XML内容
        """
        try:
            # 创建根元素
            xmeml = ET.Element("xmeml", version="5")
            
            # 添加项目
            project = ET.SubElement(xmeml, "project")
            
            # 项目名称
            name_elem = ET.SubElement(project, "name")
            name_elem.text = project_name
            
            # 添加子项目
            children = ET.SubElement(project, "children")
            
            # 添加序列
            sequence = ET.SubElement(children, "sequence")
            seq_name = ET.SubElement(sequence, "name")
            seq_name.text = "Main Sequence"
            
            # 序列设置
            settings = ET.SubElement(sequence, "settings")
            
            # 视频设置
            video = ET.SubElement(settings, "video")
            format_elem = ET.SubElement(video, "format")
            
            samplecharacteristics = ET.SubElement(format_elem, "samplecharacteristics")
            rate = ET.SubElement(samplecharacteristics, "rate")
            timebase = ET.SubElement(rate, "timebase")
            timebase.text = "25"
            ntsc = ET.SubElement(rate, "ntsc")
            ntsc.text = "FALSE"
            
            width = ET.SubElement(samplecharacteristics, "width")
            width.text = "1920"
            height = ET.SubElement(samplecharacteristics, "height")
            height.text = "1080"
            
            # 添加媒体
            media = ET.SubElement(sequence, "media")
            video_track = ET.SubElement(media, "video")
            track = ET.SubElement(video_track, "track")
            
            # 添加片段
            for i, subtitle in enumerate(subtitles):
                start_time = self._time_to_seconds(subtitle.get("start", "00:00:00,000"))
                end_time = self._time_to_seconds(subtitle.get("end", "00:00:00,000"))
                duration = end_time - start_time
                
                clipitem = ET.SubElement(track, "clipitem", id=f"clipitem-{i+1}")
                
                clip_name = ET.SubElement(clipitem, "name")
                clip_name.text = f"Clip_{i+1}"
                
                start_elem = ET.SubElement(clipitem, "start")
                start_elem.text = str(int(start_time * 25))  # 转换为帧数
                
                end_elem = ET.SubElement(clipitem, "end")
                end_elem.text = str(int(end_time * 25))
                
                in_elem = ET.SubElement(clipitem, "in")
                in_elem.text = str(int(start_time * 25))
                
                out_elem = ET.SubElement(clipitem, "out")
                out_elem.text = str(int(end_time * 25))
            
            # 转换为字符串
            xml_str = ET.tostring(xmeml, encoding='unicode')
            xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_str
            
            logger.info(f"📄 DaVinci XML生成完成，包含 {len(subtitles)} 个片段")
            return xml_content
            
        except Exception as e:
            logger.error(f"DaVinci XML生成失败: {e}")
            return ""
    
    def save_xml(self, xml_content: str, output_path: str) -> bool:
        """
        保存XML内容到文件
        
        Args:
            xml_content: XML内容
            output_path: 输出文件路径
            
        Returns:
            bool: 保存是否成功
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(xml_content)
            
            logger.info(f"📄 XML文件已保存: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"XML文件保存失败: {e}")
            return False
    
    def _time_to_seconds(self, time_str: str) -> float:
        """时间字符串转秒数"""
        try:
            parts = time_str.replace(',', '.').split(':')
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = float(parts[2])
            return hours * 3600 + minutes * 60 + seconds
        except:
            return 0.0
    
    def _get_fcpxml_template(self) -> str:
        """获取FCPXML模板"""
        return """<?xml version="1.0" encoding="UTF-8"?>
<fcpxml version="1.10">
    <resources>
        <!-- 资源将在这里添加 -->
    </resources>
    <library>
        <event name="VisionAI Event">
            <project name="VisionAI Project">
                <!-- 项目内容将在这里添加 -->
            </project>
        </event>
    </library>
</fcpxml>"""
    
    def _get_davinci_template(self) -> str:
        """获取DaVinci模板"""
        return """<?xml version="1.0" encoding="UTF-8"?>
<xmeml version="5">
    <project>
        <name>VisionAI Project</name>
        <children>
            <!-- 序列将在这里添加 -->
        </children>
    </project>
</xmeml>"""
    
    def _get_premiere_template(self) -> str:
        """获取Premiere模板"""
        return """<?xml version="1.0" encoding="UTF-8"?>
<PremiereData Version="3">
    <Project ObjectRef="1">
        <Name>VisionAI Project</Name>
        <!-- 项目内容将在这里添加 -->
    </Project>
</PremiereData>"""
