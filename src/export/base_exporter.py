#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
基础导出器模块

定义所有导出器的共同接口和基本功能
"""

import os
import json
import logging
import tempfile
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from abc import ABC, abstractmethod

from src.utils.log_handler import get_logger

# 配置日志
logger = get_logger("exporter")

class BaseExporter(ABC):
    """
    基础导出器抽象类
    
    为所有导出器提供共同的接口和基本功能
    """
    
    def __init__(self, name: str):
        """
        初始化导出器
        
        Args:
            name: 导出器名称
        """
        self.name = name
        self.logger = get_logger(f"exporter.{name}")
        self.temp_dir = os.path.join(tempfile.gettempdir(), "visionai_exports")
        os.makedirs(self.temp_dir, exist_ok=True)
        
    @abstractmethod
    def export(self, version: Dict[str, Any], output_path: str) -> str:
        """
        导出版本数据
        
        Args:
            version: 版本数据，包含场景和剪辑信息
            output_path: 输出文件路径
            
        Returns:
            生成的文件路径
        """
        pass
    
    def _ensure_output_directory(self, output_path: str) -> None:
        """
        确保输出目录存在
        
        Args:
            output_path: 输出文件路径
        """
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
    
    def _create_timestamp(self) -> str:
        """
        创建时间戳字符串
        
        Returns:
            形如 'YYYYMMDD_HHMMSS' 的时间戳字符串
        """
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def _generate_temp_path(self, extension: str) -> str:
        """
        生成临时文件路径
        
        Args:
            extension: 文件扩展名
            
        Returns:
            临时文件路径
        """
        timestamp = self._create_timestamp()
        return os.path.join(self.temp_dir, f"{self.name}_{timestamp}.{extension}")
    
    def _validate_version(self, version: Dict[str, Any]) -> bool:
        """
        验证版本数据是否有效
        
        Args:
            version: 版本数据
            
        Returns:
            数据是否有效
        """
        # 验证版本数据基本结构
        if not isinstance(version, dict):
            self.logger.error("版本数据必须是字典类型")
            return False
        
        # 检查必需字段
        required_fields = ['version_id', 'scenes']
        for field in required_fields:
            if field not in version:
                self.logger.error(f"版本数据缺少必需字段: {field}")
                return False
        
        # 检查场景数据
        scenes = version.get('scenes', [])
        if not scenes or not isinstance(scenes, list):
            self.logger.error("场景数据必须是非空列表")
            return False
        
        # 检查每个场景的必需字段
        for i, scene in enumerate(scenes):
            if not isinstance(scene, dict):
                self.logger.error(f"场景 {i} 必须是字典类型")
                return False
            
            scene_required_fields = ['scene_id', 'text']
            for field in scene_required_fields:
                if field not in scene:
                    self.logger.error(f"场景 {i} 缺少必需字段: {field}")
                    return False
        
        return True 