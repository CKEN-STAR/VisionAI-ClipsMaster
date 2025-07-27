#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DaVinci Resolve导出器
生成DaVinci Resolve兼容的工程文件
"""

import logging
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional
from pathlib import Path

from .base_exporter import BaseExporter

logger = logging.getLogger(__name__)

class DaVinciResolveExporter(BaseExporter):
    """DaVinci Resolve导出器"""
    
    def __init__(self):
        """初始化导出器"""
        super().__init__()
        self.format_name = "DaVinci Resolve"
        self.file_extension = ".drp"
        logger.info("DaVinci Resolve导出器初始化完成")
    
    def export(self, clips_data: List[Dict[str, Any]], output_path: str, **kwargs) -> bool:
        """
        导出为DaVinci Resolve工程文件
        
        Args:
            clips_data: 剪辑数据列表
            output_path: 输出文件路径
            **kwargs: 其他参数
            
        Returns:
            bool: 导出是否成功
        """
        try:
            logger.info(f"开始导出DaVinci Resolve工程文件: {output_path}")
            
            # 创建基本的工程结构
            project_data = self._create_project_structure(clips_data, **kwargs)
            
            # 生成XML文件
            xml_content = self._generate_xml(project_data)
            
            # 保存文件
            output_file = Path(output_path)
            if not output_file.suffix:
                output_file = output_file.with_suffix(self.file_extension)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(xml_content)
            
            logger.info(f"DaVinci Resolve工程文件导出成功: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"DaVinci Resolve工程文件导出失败: {e}")
            return False
    
    def _create_project_structure(self, clips_data: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """创建工程结构"""
        project_name = kwargs.get('project_name', 'VisionAI_ClipsMaster_Project')
        timeline_name = kwargs.get('timeline_name', 'Main_Timeline')
        
        return {
            "project": {
                "name": project_name,
                "timeline": {
                    "name": timeline_name,
                    "clips": clips_data
                }
            }
        }
    
    def _generate_xml(self, project_data: Dict[str, Any]) -> str:
        """生成XML内容"""
        # 创建根元素
        root = ET.Element("project")
        root.set("version", "1.0")
        
        # 添加项目信息
        project_info = ET.SubElement(root, "projectinfo")
        name_elem = ET.SubElement(project_info, "name")
        name_elem.text = project_data["project"]["name"]
        
        # 添加时间线
        timeline = ET.SubElement(root, "timeline")
        timeline_name = ET.SubElement(timeline, "name")
        timeline_name.text = project_data["project"]["timeline"]["name"]
        
        # 添加剪辑
        clips_elem = ET.SubElement(timeline, "clips")
        for i, clip in enumerate(project_data["project"]["timeline"]["clips"]):
            clip_elem = ET.SubElement(clips_elem, "clip")
            clip_elem.set("id", str(i))
            
            # 添加剪辑属性
            for key, value in clip.items():
                if isinstance(value, (str, int, float)):
                    attr_elem = ET.SubElement(clip_elem, key)
                    attr_elem.text = str(value)
        
        # 转换为字符串
        xml_str = ET.tostring(root, encoding='unicode')
        
        # 添加XML声明
        return f'<?xml version="1.0" encoding="UTF-8"?>\n{xml_str}'
    
    def validate_clips_data(self, clips_data: List[Dict[str, Any]]) -> bool:
        """验证剪辑数据"""
        if not clips_data:
            logger.warning("剪辑数据为空")
            return False
        
        required_fields = ['start_time', 'end_time', 'source_file']
        
        for i, clip in enumerate(clips_data):
            for field in required_fields:
                if field not in clip:
                    logger.error(f"剪辑 {i} 缺少必需字段: {field}")
                    return False
        
        return True

# 创建全局导出器实例
_exporter = None

def get_exporter() -> DaVinciResolveExporter:
    """获取或创建导出器实例"""
    global _exporter
    if _exporter is None:
        _exporter = DaVinciResolveExporter()
    return _exporter

def export_to_davinci_resolve(clips_data: List[Dict[str, Any]], output_path: str, **kwargs) -> bool:
    """导出到DaVinci Resolve的便捷函数"""
    return get_exporter().export(clips_data, output_path, **kwargs)
