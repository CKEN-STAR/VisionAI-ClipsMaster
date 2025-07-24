#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
时间轴标记生成器
为剪映工程文件添加时间轴标记和章节分割点
"""

from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class TimelineMarkerGenerator:
    """时间轴标记生成器"""
    
    def __init__(self):
        """初始化标记生成器"""
        self.marker_types = {
            "chapter": "章节标记",
            "highlight": "精彩片段",
            "transition": "转场点",
            "sync_point": "同步点"
        }
    
    def generate_markers(self, segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        为视频片段生成时间轴标记
        
        Args:
            segments: 视频片段列表
            
        Returns:
            List: 时间轴标记列表
        """
        markers = []
        
        try:
            for i, segment in enumerate(segments):
                # 片段开始标记
                start_marker = {
                    "id": f"marker_{i}_start",
                    "time": segment.get("start_time", 0),
                    "type": "chapter",
                    "title": f"片段 {i+1} 开始",
                    "description": segment.get("text", ""),
                    "color": "#4CAF50"  # 绿色
                }
                markers.append(start_marker)
                
                # 如果片段较长，添加中间标记
                duration = segment.get("duration", 0)
                if duration > 5:  # 超过5秒的片段
                    mid_time = segment.get("start_time", 0) + duration / 2
                    mid_marker = {
                        "id": f"marker_{i}_mid",
                        "time": mid_time,
                        "type": "highlight",
                        "title": f"片段 {i+1} 重点",
                        "description": "精彩内容",
                        "color": "#FF9800"  # 橙色
                    }
                    markers.append(mid_marker)
                
                # 片段结束标记
                end_marker = {
                    "id": f"marker_{i}_end",
                    "time": segment.get("end_time", 0),
                    "type": "transition",
                    "title": f"片段 {i+1} 结束",
                    "description": "转场点",
                    "color": "#2196F3"  # 蓝色
                }
                markers.append(end_marker)
            
            logger.info(f"生成了 {len(markers)} 个时间轴标记")
            
        except Exception as e:
            logger.error(f"生成时间轴标记失败: {e}")
        
        return markers
    
    def generate_chapters(self, segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        生成章节分割点
        
        Args:
            segments: 视频片段列表
            
        Returns:
            List: 章节列表
        """
        chapters = []
        
        try:
            for i, segment in enumerate(segments):
                chapter = {
                    "id": f"chapter_{i+1}",
                    "title": f"第{i+1}章",
                    "start_time": segment.get("start_time", 0),
                    "end_time": segment.get("end_time", 0),
                    "duration": segment.get("duration", 0),
                    "description": segment.get("text", ""),
                    "thumbnail_time": segment.get("start_time", 0) + 1  # 缩略图时间点
                }
                chapters.append(chapter)
            
            logger.info(f"生成了 {len(chapters)} 个章节")
            
        except Exception as e:
            logger.error(f"生成章节失败: {e}")
        
        return chapters
