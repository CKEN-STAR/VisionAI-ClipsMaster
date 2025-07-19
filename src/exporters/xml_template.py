#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
剪映XML模板处理模块

提供剪映导出XML模板的处理功能，支持模板填充和验证。
"""

import os
import sys
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import datetime
import hashlib

# 导入工具模块
from src.utils.logger import get_module_logger

# 初始化日志记录器
logger = get_module_logger("xml_template")

class XMLTemplateProcessor:
    """剪映XML模板处理器"""
    
    def __init__(self, template_path: Optional[Union[str, Path]] = None):
        """
        初始化XML模板处理器
        
        Args:
            template_path: XML模板路径，如果不提供则使用默认模板
        """
        self.template_path = template_path
        
        # 如果提供了模板路径，加载模板
        if template_path:
            self.load_template(template_path)
        else:
            # 使用默认模板
            self.root = self._create_default_template()
            
        # XML验证标志
        self.is_validated = False
    
    def load_template(self, template_path: Union[str, Path]) -> bool:
        """
        加载XML模板
        
        Args:
            template_path: 模板路径
            
        Returns:
            是否成功加载
        """
        try:
            tree = ET.parse(template_path)
            self.root = tree.getroot()
            logger.info(f"已加载XML模板: {template_path}")
            return True
        except Exception as e:
            logger.error(f"加载XML模板失败: {str(e)}")
            # 使用默认模板作为后备
            self.root = self._create_default_template()
            return False
    
    def _create_default_template(self) -> ET.Element:
        """
        创建默认剪映XML模板
        
        Returns:
            XML根元素
        """
        # 创建项目根元素
        root = ET.Element("jianying_project")
        root.set("version", "1.0")
        
        # 创建基本元素
        ET.SubElement(root, "project_meta")
        ET.SubElement(root, "timeline")
        ET.SubElement(root, "resources")
        ET.SubElement(root, "export_settings")
        ET.SubElement(root, "legal_info")
        
        return root
    
    def fill_project_meta(self, project_info: Dict[str, Any]) -> None:
        """
        填充项目元数据
        
        Args:
            project_info: 项目信息字典
        """
        meta = self.root.find("project_meta")
        if meta is None:
            meta = ET.SubElement(self.root, "project_meta")
        
        # 清空现有数据
        meta.clear()
        
        # 添加基本项目信息
        for key, value in project_info.items():
            if isinstance(value, (str, int, float, bool)):
                ET.SubElement(meta, key).text = str(value)
            elif isinstance(value, dict):
                sub_elem = ET.SubElement(meta, key)
                for sub_key, sub_value in value.items():
                    ET.SubElement(sub_elem, sub_key).text = str(sub_value)
        
        # 添加生成时间
        if "creation_time" not in project_info:
            ET.SubElement(meta, "creation_time").text = datetime.datetime.now().isoformat()
    
    def fill_timeline(self, timeline_data: Dict[str, Any]) -> None:
        """
        填充时间轴数据
        
        Args:
            timeline_data: 时间轴数据字典
        """
        timeline = self.root.find("timeline")
        if timeline is None:
            timeline = ET.SubElement(self.root, "timeline")
        
        # 清空现有数据
        timeline.clear()
        
        # 添加时间轴属性
        if "attributes" in timeline_data:
            for key, value in timeline_data["attributes"].items():
                timeline.set(key, str(value))
        
        # 添加时间轴轨道
        if "tracks" in timeline_data and isinstance(timeline_data["tracks"], list):
            for track_data in timeline_data["tracks"]:
                track = ET.SubElement(timeline, "track")
                track.set("type", track_data.get("type", "video"))
                track.set("id", track_data.get("id", ""))
                
                # 添加片段
                if "clips" in track_data and isinstance(track_data["clips"], list):
                    for clip_data in track_data["clips"]:
                        clip = ET.SubElement(track, "clip")
                        # 设置片段属性
                        for key, value in clip_data.items():
                            if key != "effects" and key != "properties":
                                clip.set(key, str(value))
                        
                        # 添加效果
                        if "effects" in clip_data and isinstance(clip_data["effects"], list):
                            effects = ET.SubElement(clip, "effects")
                            for effect_data in clip_data["effects"]:
                                effect = ET.SubElement(effects, "effect")
                                for key, value in effect_data.items():
                                    effect.set(key, str(value))
                        
                        # 添加属性
                        if "properties" in clip_data and isinstance(clip_data["properties"], dict):
                            properties = ET.SubElement(clip, "properties")
                            for key, value in clip_data["properties"].items():
                                ET.SubElement(properties, key).text = str(value)
    
    def fill_resources(self, resources_data: List[Dict[str, Any]]) -> None:
        """
        填充资源数据
        
        Args:
            resources_data: 资源数据列表
        """
        resources = self.root.find("resources")
        if resources is None:
            resources = ET.SubElement(self.root, "resources")
        
        # 清空现有数据
        resources.clear()
        
        # 添加资源
        for resource_data in resources_data:
            resource = ET.SubElement(resources, "resource")
            # 设置资源属性
            for key, value in resource_data.items():
                if key != "metadata":
                    resource.set(key, str(value))
            
            # 添加元数据
            if "metadata" in resource_data and isinstance(resource_data["metadata"], dict):
                metadata = ET.SubElement(resource, "metadata")
                for key, value in resource_data["metadata"].items():
                    ET.SubElement(metadata, key).text = str(value)
    
    def fill_export_settings(self, export_settings: Dict[str, Any]) -> None:
        """
        填充导出设置
        
        Args:
            export_settings: 导出设置字典
        """
        settings = self.root.find("export_settings")
        if settings is None:
            settings = ET.SubElement(self.root, "export_settings")
        
        # 清空现有数据
        settings.clear()
        
        # 添加导出设置
        for key, value in export_settings.items():
            if isinstance(value, (str, int, float, bool)):
                ET.SubElement(settings, key).text = str(value)
            elif isinstance(value, dict):
                sub_elem = ET.SubElement(settings, key)
                for sub_key, sub_value in value.items():
                    ET.SubElement(sub_elem, sub_key).text = str(sub_value)
    
    def inject_legal_info(self, legal_info: Dict[str, str]) -> None:
        """
        注入法律声明信息
        
        Args:
            legal_info: 法律声明信息字典
        """
        legal = self.root.find("legal_info")
        if legal is None:
            legal = ET.SubElement(self.root, "legal_info")
        
        # 清空现有数据
        legal.clear()
        
        # 添加版权声明
        if "copyright" in legal_info:
            ET.SubElement(legal, "copyright").text = legal_info["copyright"]
        else:
            ET.SubElement(legal, "copyright").text = f"© {datetime.datetime.now().year} VisionAI-ClipsMaster"
        
        # 添加许可声明
        if "license" in legal_info:
            ET.SubElement(legal, "license").text = legal_info["license"]
        
        # 添加数据处理声明
        if "data_processing" in legal_info:
            ET.SubElement(legal, "data_processing").text = legal_info["data_processing"]
        else:
            # 默认GDPR声明
            ET.SubElement(legal, "data_processing").text = (
                "本导出内容符合GDPR和中国个人信息保护法规定，"
                "所有个人数据已经过适当处理，并获得相关许可。"
            )
        
        # 添加其他声明
        for key, value in legal_info.items():
            if key not in ["copyright", "license", "data_processing"]:
                ET.SubElement(legal, key).text = value
    
    def validate(self) -> bool:
        """
        验证XML模板
        
        Returns:
            是否验证通过
        """
        # 检查必要元素是否存在
        required_elements = ["project_meta", "timeline", "resources", "export_settings", "legal_info"]
        for element in required_elements:
            if self.root.find(element) is None:
                logger.error(f"验证失败: 缺少必要元素 {element}")
                self.is_validated = False
                return False
        
        # 检查法律声明
        legal = self.root.find("legal_info")
        if legal is None or legal.find("copyright") is None or legal.find("data_processing") is None:
            logger.error("验证失败: 法律声明不完整")
            self.is_validated = False
            return False
        
        # 通过验证
        logger.info("XML模板验证通过")
        self.is_validated = True
        return True
    
    def to_string(self, pretty: bool = True) -> str:
        """
        将XML转换为字符串
        
        Args:
            pretty: 是否美化输出
            
        Returns:
            XML字符串
        """
        xml_str = ET.tostring(self.root, encoding="utf-8", method="xml")
        
        if pretty:
            # 美化XML
            dom = minidom.parseString(xml_str)
            return dom.toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")
        
        return xml_str.decode("utf-8")
    
    def save(self, output_path: Union[str, Path], pretty: bool = True) -> bool:
        """
        保存XML到文件
        
        Args:
            output_path: 输出文件路径
            pretty: 是否美化输出
            
        Returns:
            是否成功保存
        """
        try:
            # 获取XML字符串
            xml_str = self.to_string(pretty)
            
            # 保存到文件
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(xml_str)
            
            logger.info(f"已保存XML到: {output_path}")
            return True
        except Exception as e:
            logger.error(f"保存XML失败: {str(e)}")
            return False
    
    def compute_fingerprint(self) -> str:
        """
        计算XML指纹
        
        Returns:
            XML指纹（SHA-256哈希）
        """
        # 获取规范化的XML字符串（不美化，避免空白字符影响）
        xml_str = ET.tostring(self.root, encoding="utf-8", method="xml")
        
        # 计算SHA-256哈希
        return hashlib.sha256(xml_str).hexdigest()


# 模块函数

def create_template_processor(template_path: Optional[Union[str, Path]] = None) -> XMLTemplateProcessor:
    """
    创建XML模板处理器
    
    Args:
        template_path: 模板路径，如果不提供则使用默认模板
        
    Returns:
        XML模板处理器实例
    """
    return XMLTemplateProcessor(template_path)

def load_template(template_path: Union[str, Path]) -> XMLTemplateProcessor:
    """
    加载XML模板
    
    Args:
        template_path: 模板路径
        
    Returns:
        XML模板处理器实例
    """
    processor = XMLTemplateProcessor()
    processor.load_template(template_path)
    return processor

def validate_xml(xml_path: Union[str, Path]) -> bool:
    """
    验证XML文件
    
    Args:
        xml_path: XML文件路径
        
    Returns:
        是否验证通过
    """
    processor = XMLTemplateProcessor()
    processor.load_template(xml_path)
    return processor.validate()


if __name__ == "__main__":
    # 测试代码
    processor = XMLTemplateProcessor()
    
    # 填充项目元数据
    processor.fill_project_meta({
        "name": "测试项目",
        "author": "测试用户",
        "description": "这是一个测试项目",
        "duration": 60.0
    })
    
    # 填充时间轴
    processor.fill_timeline({
        "attributes": {"fps": "30", "duration": "60.0"},
        "tracks": [
            {
                "type": "video",
                "id": "track_video_1",
                "clips": [
                    {
                        "id": "clip_1",
                        "start": "0.0",
                        "duration": "30.0",
                        "media_id": "media_1",
                        "effects": [
                            {"id": "effect_1", "type": "filter", "name": "暖色"}
                        ],
                        "properties": {
                            "volume": "1.0",
                            "scale": "1.0"
                        }
                    }
                ]
            }
        ]
    })
    
    # 填充资源
    processor.fill_resources([
        {
            "id": "media_1",
            "type": "video",
            "path": "/path/to/video.mp4",
            "metadata": {
                "duration": "60.0",
                "width": "1920",
                "height": "1080"
            }
        }
    ])
    
    # 填充导出设置
    processor.fill_export_settings({
        "format": "mp4",
        "codec": "h264",
        "resolution": {
            "width": "1920",
            "height": "1080"
        },
        "bitrate": "8000000"
    })
    
    # 注入法律声明
    processor.inject_legal_info({
        "copyright": "© 2023 VisionAI-ClipsMaster",
        "license": "仅供个人使用",
        "data_processing": "本导出内容符合GDPR和中国个人信息保护法规定，所有个人数据已经过适当处理。"
    })
    
    # 验证
    if processor.validate():
        print("XML模板验证通过")
        
        # 输出XML
        xml_str = processor.to_string()
        print(xml_str)
    else:
        print("XML模板验证失败") 