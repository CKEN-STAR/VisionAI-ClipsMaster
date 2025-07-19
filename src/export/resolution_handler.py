#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
分辨率处理模块

提供动态视频分辨率获取和适配功能，确保导出的XML项目设置与原始视频分辨率匹配。
主要功能：
1. 获取视频分辨率
2. 将分辨率信息添加到XML文件
3. 动态适配不同分辨率的视频
"""

import os
import cv2
import re
import subprocess
import json
import logging
from typing import Dict, List, Any, Optional, Tuple, Union

from src.utils.log_handler import get_logger

# 配置日志
logger = get_logger("resolution_handler")

def get_video_dimensions(video_path: str) -> Tuple[int, int]:
    """
    获取视频分辨率
    
    支持多种方法获取视频分辨率，优先使用FFprobe，失败则回退到OpenCV
    
    Args:
        video_path: 视频文件路径
        
    Returns:
        Tuple[int, int]: 视频宽度和高度的元组
    """
    if not os.path.exists(video_path):
        logger.error(f"视频文件不存在: {video_path}")
        return (1920, 1080)  # 默认返回1080p
    
    # 方法1: 使用FFprobe获取视频信息
    try:
        result = subprocess.run([
            'ffprobe',
            '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height',
            '-of', 'json',
            video_path
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            if 'streams' in data and len(data['streams']) > 0:
                width = int(data['streams'][0].get('width', 0))
                height = int(data['streams'][0].get('height', 0))
                
                if width > 0 and height > 0:
                    logger.info(f"使用FFprobe获取视频分辨率: {width}x{height}")
                    return (width, height)
    except Exception as e:
        logger.warning(f"FFprobe获取视频分辨率失败: {str(e)}")
    
    # 方法2: 使用OpenCV获取视频信息
    try:
        cap = cv2.VideoCapture(video_path)
        if cap.isOpened():
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            cap.release()
            
            if width > 0 and height > 0:
                logger.info(f"使用OpenCV获取视频分辨率: {width}x{height}")
                return (width, height)
    except Exception as e:
        logger.warning(f"OpenCV获取视频分辨率失败: {str(e)}")
    
    # 如果以上方法都失败，返回默认分辨率
    logger.warning(f"无法获取视频分辨率，使用默认值: 1920x1080")
    return (1920, 1080)

def add_resolution_meta(xml_content: str, video_path: str) -> str:
    """
    向XML内容添加分辨率信息
    
    获取视频的实际分辨率，并将其添加到XML文件中
    
    Args:
        xml_content: 原始XML内容
        video_path: 视频文件路径
        
    Returns:
        str: 添加了分辨率信息的XML内容
    """
    # 获取视频分辨率
    width, height = get_video_dimensions(video_path)
    
    # 创建分辨率节点
    resolution_node = f'<resolution width="{width}" height="{height}"/>'
    
    # 将分辨率节点添加到</project>标签前
    modified_content = xml_content.replace("</project>", f"{resolution_node}\n</project>")
    
    return modified_content

def adapt_xml_resolution(xml_content: str, video_path: str) -> str:
    """
    适配XML内容中的分辨率设置
    
    根据视频文件的实际分辨率，更新XML中的分辨率设置
    
    Args:
        xml_content: 原始XML内容
        video_path: 视频文件路径
        
    Returns:
        str: 更新了分辨率的XML内容
    """
    # 获取视频分辨率
    width, height = get_video_dimensions(video_path)
    
    # 更新XML中的分辨率设置
    modified_content = xml_content
    
    # 修改settings中的分辨率设置
    width_pattern = r'<width>(\d+)</width>'
    height_pattern = r'<height>(\d+)</height>'
    
    modified_content = re.sub(width_pattern, f'<width>{width}</width>', modified_content)
    modified_content = re.sub(height_pattern, f'<height>{height}</height>', modified_content)
    
    # 修改format属性中的分辨率
    format_pattern = r'<format[^>]*width="(\d+)"[^>]*height="(\d+)"[^>]*'
    modified_content = re.sub(format_pattern, lambda m: m.group(0).replace(f'width="{m.group(1)}"', f'width="{width}"').replace(f'height="{m.group(2)}"', f'height="{height}"'), modified_content)
    
    # 修改format节点中的分辨率属性
    format_node_pattern = r'<format[^>]*>'
    if 'width=' not in modified_content and 'height=' not in modified_content:
        modified_content = re.sub(format_node_pattern, f'<format width="{width}" height="{height}">', modified_content)
    
    logger.info(f"XML分辨率已适配为 {width}x{height}")
    return modified_content

def auto_adapt_export_resolution(export_func):
    """
    导出函数的分辨率自适应装饰器
    
    装饰导出器的export方法，使其自动适配视频分辨率
    
    Args:
        export_func: 要装饰的导出函数
        
    Returns:
        装饰后的函数
    """
    def wrapper(self, version: Dict[str, Any], output_path: str, *args, **kwargs):
        # 获取视频路径
        video_path = version.get('video_path', '')
        
        # 调用原始导出函数
        result = export_func(self, version, output_path, *args, **kwargs)
        
        # 如果视频路径存在且输出文件已生成，执行分辨率适配
        if video_path and os.path.exists(output_path):
            try:
                # 读取输出文件
                with open(output_path, 'r', encoding='utf-8') as f:
                    xml_content = f.read()
                
                # 适配分辨率
                modified_content = adapt_xml_resolution(xml_content, video_path)
                
                # 写回输出文件
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(modified_content)
                
                logger.info(f"已自动适配分辨率: {output_path}")
            except Exception as e:
                logger.error(f"自动适配分辨率失败: {str(e)}")
        
        return result
    
    return wrapper
