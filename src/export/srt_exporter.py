#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SRT导出器模块

导出SRT格式字幕文件
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import timedelta

from src.export.base_exporter import BaseExporter
from src.utils.log_handler import get_logger

class SRTExporter(BaseExporter):
    """
    SRT导出器
    
    将版本数据导出为SRT格式字幕文件
    """
    
    def __init__(self):
        """初始化SRT导出器"""
        super().__init__("SRT")
    
    def export(self, version: Dict[str, Any], output_path: str) -> str:
        """
        将版本数据导出为SRT格式
        
        Args:
            version: 版本数据，包含场景和剪辑信息
            output_path: 输出文件路径
            
        Returns:
            生成的SRT文件路径
        """
        if not self._validate_version(version):
            raise ValueError("无效的版本数据")
        
        self._ensure_output_directory(output_path)
        
        scenes = version.get('scenes', [])
        version_id = version.get('version_id', 'unknown')
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                for i, scene in enumerate(scenes):
                    # 获取场景信息
                    start_time = scene.get('start_time', i * 5)  # 默认每5秒一个场景
                    duration = scene.get('duration', 5)  # 默认5秒
                    end_time = start_time + duration
                    
                    # 获取文本
                    text = scene.get('text', f"场景 {i+1}")
                    
                    # 将时间转换为SRT格式时间戳
                    start_timestamp = self._format_timestamp(start_time)
                    end_timestamp = self._format_timestamp(end_time)
                    
                    # 写入SRT条目
                    f.write(f"{i+1}\n")
                    f.write(f"{start_timestamp} --> {end_timestamp}\n")
                    f.write(f"{text}\n\n")
            
            self.logger.info(f"已导出SRT文件: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"导出SRT文件失败: {str(e)}")
            raise
    
    def _format_timestamp(self, seconds: float) -> str:
        """
        将秒数格式化为SRT时间戳格式: 00:00:00,000
        
        Args:
            seconds: 秒数
            
        Returns:
            SRT格式时间戳
        """
        td = timedelta(seconds=seconds)
        
        # 获取小时、分钟、秒和毫秒
        hours, remainder = divmod(td.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        # 获取毫秒
        milliseconds = int(td.microseconds / 1000)
        
        # 格式化为SRT时间戳
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}" 