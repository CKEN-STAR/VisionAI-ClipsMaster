#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
XML构建器模块

提供基础XML骨架构建功能，为各种导出器提供通用的XML结构创建工具
"""

import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime
import os

from src.utils.log_handler import get_logger
from src.export.xml_encoder import sanitize_xml, normalize_file_path

# 导入类型验证功能
try:
    from src.exporters.type_checker import (
        validate_numeric_ranges,
        check_data_types,
        TypeError,
        ValidationError
    )
except ImportError:
    # 如果导入失败，定义空的验证函数
    def validate_numeric_ranges(*args, **kwargs):
        return True
    
    def check_data_types(*args, **kwargs):
        return True
    
    class TypeError(Exception):
        pass
    
    class ValidationError(Exception):
        pass

# 配置日志
logger = get_logger("xml_builder")

def create_base_xml() -> str:
    """创建基础XML骨架
    
    返回一个基础的XML结构字符串，包含项目、资源和时间轴区域
    
    Returns:
        str: 基础XML结构字符串
    """
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<project version="3.0">
  <resources>
    <!-- 素材资源区 -->
  </resources>
  <timeline>
    <!-- 时间轴轨道区 -->
  </timeline>
</project>'''

def create_project_xml(
    project_name: str, 
    width: int = 1920, 
    height: int = 1080, 
    fps: float = 30.0
) -> ET.Element:
    """创建项目XML元素树
    
    Args:
        project_name: 项目名称
        width: 视频宽度，默认1920
        height: 视频高度，默认1080
        fps: 帧率，默认30fps
        
    Returns:
        ET.Element: 项目XML元素树根节点
        
    Raises:
        TypeError: 如果参数类型不正确
        ValidationError: 如果参数值不在有效范围内
    """
    # 验证输入参数
    validate_project_params(project_name, width, height, fps)
    
    # 创建项目根节点
    root = ET.Element("project", {
        "version": "3.0",
        "name": project_name,
        "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    
    # 创建项目设置节点
    settings = ET.SubElement(root, "settings")
    
    # 视频设置
    video_settings = ET.SubElement(settings, "video")
    ET.SubElement(video_settings, "width").text = str(width)
    ET.SubElement(video_settings, "height").text = str(height)
    ET.SubElement(video_settings, "fps").text = str(fps)
    
    # 创建资源节点
    resources = ET.SubElement(root, "resources")
    
    # 创建时间轴节点
    timeline = ET.SubElement(root, "timeline")
    
    # 创建视频轨道
    video_track = ET.SubElement(timeline, "track", {"type": "video", "name": "视频轨道 1"})
    
    # 创建音频轨道
    audio_track = ET.SubElement(timeline, "track", {"type": "audio", "name": "音频轨道 1"})
    
    return root

def validate_project_params(project_name: str, width: int, height: int, fps: float) -> bool:
    """
    验证项目参数是否有效
    
    Args:
        project_name: 项目名称
        width: 视频宽度
        height: 视频高度
        fps: 帧率
        
    Returns:
        bool: 验证是否通过
        
    Raises:
        TypeError: 如果参数类型不正确
        ValidationError: 如果参数值不在有效范围内
    """
    # 验证项目名称
    if not isinstance(project_name, str) or not project_name.strip():
        raise TypeError("项目名称必须是非空字符串")
    
    # 验证视频参数范围
    params = {
        "width": width,
        "height": height,
        "fps": fps
    }
    
    rules = {
        "width": {
            "type": "xs:int",
            "min": 1,
            "max": 7680  # 8K分辨率
        },
        "height": {
            "type": "xs:int",
            "min": 1,
            "max": 4320  # 8K分辨率
        },
        "fps": {
            "type": "xs:float",
            "min": 1.0,
            "max": 240.0,
            "allowed": [23.976, 24, 25, 29.97, 30, 50, 59.94, 60, 120, 240]
        }
    }
    
    validate_numeric_ranges(params, rules)
    return True

def add_video_resource(
    resources_elem: ET.Element, 
    resource_id: str, 
    file_path: str, 
    display_name: Optional[str] = None
) -> ET.Element:
    """向资源节点添加视频资源
    
    Args:
        resources_elem: 资源节点元素
        resource_id: 资源ID
        file_path: 视频文件路径
        display_name: 显示名称，默认使用文件名
        
    Returns:
        ET.Element: 创建的视频资源节点
    """
    if display_name is None:
        display_name = os.path.basename(file_path)
    
    # 标准化文件路径，确保XML兼容性
    normalized_path = normalize_file_path(file_path)
    
    video_resource = ET.SubElement(resources_elem, "video", {
        "id": resource_id,
        "path": normalized_path,
        "name": display_name
    })
    
    return video_resource

def add_clip_to_track(
    track_elem: ET.Element,
    resource_id: str, 
    start_time: float,
    duration: float,
    clip_name: Optional[str] = None,
    track_start_time: float = 0.0
) -> ET.Element:
    """向轨道添加片段
    
    Args:
        track_elem: 轨道节点元素
        resource_id: 资源ID
        start_time: 资源开始时间(秒)
        duration: 持续时间(秒)
        clip_name: 片段名称
        track_start_time: 轨道起始时间(秒)
        
    Returns:
        ET.Element: 创建的片段节点
        
    Raises:
        TypeError: 如果参数类型不正确
        ValidationError: 如果参数值不在有效范围内
    """
    if clip_name is None:
        clip_name = f"Clip_{resource_id}"
    
    # 验证片段参数
    validate_clip_params(resource_id, start_time, duration, track_start_time)
    
    clip = ET.SubElement(track_elem, "clip", {
        "name": clip_name,
        "resourceId": resource_id,
        "start": str(start_time),
        "duration": str(duration),
        "trackStart": str(track_start_time)
    })
    
    return clip

def validate_clip_params(resource_id: str, start_time: float, duration: float, track_start_time: float) -> bool:
    """
    验证片段参数是否有效
    
    Args:
        resource_id: 资源ID
        start_time: 资源开始时间(秒)
        duration: 持续时间(秒)
        track_start_time: 轨道起始时间(秒)
        
    Returns:
        bool: 验证是否通过
        
    Raises:
        TypeError: 如果参数类型不正确
        ValidationError: 如果参数值不在有效范围内
    """
    # 验证资源ID
    if not isinstance(resource_id, str) or not resource_id.strip():
        raise TypeError("资源ID必须是非空字符串")
    
    # 验证时间参数
    params = {
        "start_time": start_time,
        "duration": duration,
        "track_start_time": track_start_time
    }
    
    rules = {
        "start_time": {
            "type": "xs:float",
            "min": 0.0
        },
        "duration": {
            "type": "xs:float",
            "min": 0.01  # 至少10毫秒
        },
        "track_start_time": {
            "type": "xs:float",
            "min": 0.0
        }
    }
    
    validate_numeric_ranges(params, rules)
    return True

def xml_to_string(root: ET.Element, pretty: bool = True) -> str:
    """将XML元素树转换为字符串
    
    Args:
        root: XML元素树根节点
        pretty: 是否格式化输出
        
    Returns:
        str: XML字符串
    """
    xml_string = ET.tostring(root, encoding='utf-8')
    
    if pretty:
        dom = minidom.parseString(xml_string)
        result = dom.toprettyxml(indent="  ", encoding='utf-8').decode('utf-8')
        # 处理可能存在的特殊字符，确保输出字符串符合XML规范
        return result
    else:
        result = xml_string.decode('utf-8')
        return result

def create_empty_project(project_name: str) -> str:
    """创建空项目XML字符串
    
    创建一个仅包含基本结构的空项目XML
    
    Args:
        project_name: 项目名称
        
    Returns:
        str: 格式化的XML字符串
    """
    root = create_project_xml(project_name)
    return xml_to_string(root)

def convert_seconds_to_timecode(seconds: float, fps: float = 30.0) -> str:
    """将秒数转换为时间码
    
    Args:
        seconds: 秒数
        fps: 帧率，默认30fps
        
    Returns:
        str: 时间码字符串，格式为"HH:MM:SS:FF"
    """
    # 验证参数
    params = {"seconds": seconds, "fps": fps}
    rules = {
        "seconds": {"type": "xs:float", "min": 0.0},
        "fps": {"type": "xs:float", "min": 1.0}
    }
    try:
        validate_numeric_ranges(params, rules)
    except (TypeError, ValidationError) as e:
        logger.warning(f"时间码转换参数无效: {e}")
        seconds = max(0.0, float(seconds))
        fps = max(1.0, float(fps))
    
    total_frames = int(seconds * fps)
    frames = total_frames % int(fps)
    total_seconds = total_frames // int(fps)
    
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    
    return f"{hours:02d}:{minutes:02d}:{secs:02d}:{frames:02d}"

def build_scene_timeline(
    scenes: List[Dict[str, Any]], 
    video_path: str, 
    project_name: Optional[str] = None
) -> str:
    """根据场景列表构建时间轴XML
    
    Args:
        scenes: 场景列表，每个场景需包含start_time和duration字段
        video_path: 视频文件路径
        project_name: 项目名称，默认从文件名生成
        
    Returns:
        str: 构建好的XML字符串
    """
    if project_name is None:
        project_name = f"VisionAI_{os.path.splitext(os.path.basename(video_path))[0]}"
    
    # 创建项目根节点
    root = create_project_xml(project_name)
    
    # 获取资源节点
    resources = root.find("resources")
    
    # 添加视频资源
    video_resource = add_video_resource(resources, "video_1", video_path)
    
    # 获取视频轨道
    video_track = root.find(".//track[@type='video']")
    
    # 获取音频轨道
    audio_track = root.find(".//track[@type='audio']")
    
    # 当前轨道位置
    current_position = 0.0
    
    # 添加片段到轨道
    for i, scene in enumerate(scenes):
        scene_id = scene.get('scene_id', f"scene_{i+1}")
        start_time = scene.get('start_time', 0.0)
        duration = scene.get('duration', 5.0)
        
        # 添加视频片段
        add_clip_to_track(
            video_track,
            "video_1",
            start_time,
            duration,
            clip_name=f"视频_{scene_id}",
            track_start_time=current_position
        )
        
        # 添加音频片段
        if scene.get('has_audio', True):
            add_clip_to_track(
                audio_track,
                "video_1",
                start_time,
                duration,
                clip_name=f"音频_{scene_id}",
                track_start_time=current_position
            )
        
        # 更新轨道位置
        current_position += duration
    
    # 返回XML字符串
    return xml_to_string(root)

# 测试函数
def test_xml_builder():
    """测试XML构建器功能"""
    # 创建基础XML
    base_xml = create_base_xml()
    print("基础XML:\n", base_xml)
    
    # 创建带场景的项目XML
    scenes = [
        {"scene_id": "开场", "start_time": 10.5, "duration": 5.0},
        {"scene_id": "转场", "start_time": 25.0, "duration": 3.0},
        {"scene_id": "高潮", "start_time": 45.0, "duration": 8.0, "has_audio": False},
        {"scene_id": "结尾", "start_time": 60.0, "duration": 4.0}
    ]
    
    project_xml = build_scene_timeline(
        scenes, 
        "/path/to/video.mp4",
        "测试项目"
    )
    
    print("\n\n场景项目XML:\n", project_xml)

if __name__ == "__main__":
    test_xml_builder() 