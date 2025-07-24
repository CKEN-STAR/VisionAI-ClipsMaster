#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
基础导出器
提供通用的导出功能接口
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pathlib import Path
import json
import os
from ..utils.log_handler import get_logger

logger = get_logger(__name__)

class BaseExporter(ABC):
    """基础导出器抽象类"""
    
    def __init__(self):
        """初始化基础导出器"""
        self.export_format = "unknown"
        self.output_extension = ".txt"
        self.supported_features = []
        
        logger.info(f"📁 基础导出器初始化完成")
    
    @abstractmethod
    def export_project(self, video_path: str, subtitles: List[Dict], 
                      output_dir: str) -> str:
        """
        导出项目文件
        
        Args:
            video_path: 视频文件路径
            subtitles: 字幕列表
            output_dir: 输出目录
            
        Returns:
            str: 导出的项目文件路径
        """
        pass
    
    def validate_inputs(self, video_path: str, subtitles: List[Dict]) -> bool:
        """
        验证输入参数
        
        Args:
            video_path: 视频文件路径
            subtitles: 字幕列表
            
        Returns:
            bool: 验证是否通过
        """
        try:
            # 检查视频文件
            if not os.path.exists(video_path):
                logger.error(f"视频文件不存在: {video_path}")
                return False
            
            # 检查字幕列表
            if not subtitles or not isinstance(subtitles, list):
                logger.error("字幕列表为空或格式错误")
                return False
            
            # 检查字幕格式
            for i, subtitle in enumerate(subtitles):
                if not isinstance(subtitle, dict):
                    logger.error(f"字幕项 {i} 格式错误")
                    return False
                
                required_fields = ["start", "end", "text"]
                for field in required_fields:
                    if field not in subtitle:
                        logger.error(f"字幕项 {i} 缺少必需字段: {field}")
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"输入验证失败: {e}")
            return False
    
    def create_output_directory(self, output_dir: str) -> bool:
        """
        创建输出目录
        
        Args:
            output_dir: 输出目录路径
            
        Returns:
            bool: 创建是否成功
        """
        try:
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            logger.info(f"📁 输出目录已创建: {output_dir}")
            return True
        except Exception as e:
            logger.error(f"创建输出目录失败: {e}")
            return False
    
    def generate_metadata(self, video_path: str, subtitles: List[Dict]) -> Dict[str, Any]:
        """
        生成元数据
        
        Args:
            video_path: 视频文件路径
            subtitles: 字幕列表
            
        Returns:
            Dict: 元数据字典
        """
        try:
            metadata = {
                "export_format": self.export_format,
                "video_file": os.path.basename(video_path),
                "video_path": video_path,
                "subtitle_count": len(subtitles),
                "total_duration": self._calculate_total_duration(subtitles),
                "export_timestamp": self._get_current_timestamp(),
                "exporter_version": "1.0.1",
                "supported_features": self.supported_features
            }
            
            return metadata
            
        except Exception as e:
            logger.error(f"生成元数据失败: {e}")
            return {}
    
    def _calculate_total_duration(self, subtitles: List[Dict]) -> float:
        """计算总时长"""
        try:
            if not subtitles:
                return 0.0
            
            total_duration = 0.0
            for subtitle in subtitles:
                start_time = self._time_to_seconds(subtitle.get("start", "00:00:00,000"))
                end_time = self._time_to_seconds(subtitle.get("end", "00:00:00,000"))
                total_duration += (end_time - start_time)
            
            return total_duration
            
        except Exception as e:
            logger.error(f"计算总时长失败: {e}")
            return 0.0
    
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
    
    def _get_current_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def save_metadata(self, metadata: Dict[str, Any], output_path: str) -> bool:
        """
        保存元数据到文件
        
        Args:
            metadata: 元数据字典
            output_path: 输出文件路径
            
        Returns:
            bool: 保存是否成功
        """
        try:
            metadata_path = output_path.replace(self.output_extension, "_metadata.json")
            
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            logger.info(f"📄 元数据已保存: {metadata_path}")
            return True
            
        except Exception as e:
            logger.error(f"保存元数据失败: {e}")
            return False


class SimpleTextExporter(BaseExporter):
    """简单文本导出器实现"""
    
    def __init__(self):
        """初始化简单文本导出器"""
        super().__init__()
        self.export_format = "text"
        self.output_extension = ".txt"
        self.supported_features = ["subtitles", "metadata"]
    
    def export_project(self, video_path: str, subtitles: List[Dict], 
                      output_dir: str) -> str:
        """
        导出为文本文件
        
        Args:
            video_path: 视频文件路径
            subtitles: 字幕列表
            output_dir: 输出目录
            
        Returns:
            str: 导出的文件路径
        """
        try:
            # 验证输入
            if not self.validate_inputs(video_path, subtitles):
                raise ValueError("输入验证失败")
            
            # 创建输出目录
            if not self.create_output_directory(output_dir):
                raise ValueError("创建输出目录失败")
            
            # 生成输出文件路径
            video_name = Path(video_path).stem
            output_path = os.path.join(output_dir, f"{video_name}_export.txt")
            
            # 生成文本内容
            content_lines = []
            content_lines.append(f"# VisionAI-ClipsMaster 导出文件")
            content_lines.append(f"# 原视频: {os.path.basename(video_path)}")
            content_lines.append(f"# 字幕数量: {len(subtitles)}")
            content_lines.append(f"# 导出时间: {self._get_current_timestamp()}")
            content_lines.append("")
            
            for i, subtitle in enumerate(subtitles, 1):
                start_time = subtitle.get("start", "00:00:00,000")
                end_time = subtitle.get("end", "00:00:00,000")
                text = subtitle.get("text", "")
                
                content_lines.append(f"{i}")
                content_lines.append(f"{start_time} --> {end_time}")
                content_lines.append(text)
                content_lines.append("")
            
            # 写入文件
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(content_lines))
            
            # 生成并保存元数据
            metadata = self.generate_metadata(video_path, subtitles)
            self.save_metadata(metadata, output_path)
            
            logger.info(f"📁 文本导出完成: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"文本导出失败: {e}")
            raise
