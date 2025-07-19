#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
质量控制器模块

负责集成动态质量探针系统到视频处理流程中，并提供对外接口。
主要功能：
1. 初始化和配置质量探针
2. 在视频处理流程的关键节点插入探针
3. 收集和分析质量指标
4. 生成质量报告
5. 提供质量控制接口
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from loguru import logger

from src.quality.dynamic_probes import QualityProbe, check_quality_threshold
from src.quality.report_generator import generate_quality_report
from src.utils.log_handler import get_logger
from src.utils.file_handler import ensure_dir_exists
from src.core.exceptions import QualityCheckError, QualityThresholdError

# 获取logger
quality_logger = get_logger("quality_controller")

class QualityController:
    """
    质量控制器 - 集成动态质量探针系统到视频处理流程中
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化质量控制器
        
        Args:
            config_path: 质量配置文件路径
        """
        # 加载配置
        self.config = self._load_config(config_path)
        
        # 创建质量探针
        self.probe = QualityProbe(
            output_dir=self.config.get('reporting', {}).get('save_path'),
            custom_thresholds=self.config.get('thresholds')
        )
        
        # 创建会话ID
        self.session_id = datetime.now().strftime("%Y%m%d%H%M%S")
        
        quality_logger.info(f"质量控制器初始化完成，会话ID: {self.session_id}")
    
    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """
        加载质量配置
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            Dict: 配置信息
        """
        # 默认配置路径
        if config_path is None:
            config_path = os.path.join("configs", "quality_probes.json")
        
        # 默认配置
        default_config = {
            'probes': {
                'enabled': True,
                'points': [0.1, 0.25, 0.5, 0.75, 0.9]
            },
            'thresholds': {
                'narrative_coherence': 0.7,
                'audio_quality': 0.65,
                'visual_quality': 0.6,
                'overall_quality': 0.75
            },
            'reporting': {
                'auto_save': True,
                'save_path': os.path.join("data", "quality_reports")
            }
        }
        
        # 尝试加载配置文件
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                quality_logger.info(f"已加载质量配置: {config_path}")
                return config
        except Exception as e:
            quality_logger.error(f"加载质量配置失败: {str(e)}")
        
        quality_logger.warning("使用默认质量配置")
        return default_config
    
    def process_video(self, 
                     video_path: str, 
                     subtitle_segments: List[Dict[str, Any]],
                     check_threshold: bool = True,
                     generate_report: bool = True) -> Dict[str, Any]:
        """
        处理视频并进行质量评估
        
        Args:
            video_path: 视频文件路径
            subtitle_segments: 字幕片段列表
            check_threshold: 是否检查质量阈值
            generate_report: 是否生成质量报告
            
        Returns:
            Dict: 处理结果，包含质量评估信息
        """
        quality_logger.info(f"开始处理视频并进行质量评估: {video_path}")
        
        try:
            # 1. 插入质量探针
            if self.config.get('probes', {}).get('enabled', True):
                video_path = self.probe.insert_probes(video_path)
            
            # 2. 评估质量
            quality_summary = self.probe.evaluate_quality(video_path, subtitle_segments)
            
            # 3. 检查质量阈值
            if check_threshold:
                overall_threshold = self.config.get('thresholds', {}).get('overall_quality', 0.7)
                overall_quality = quality_summary.get('overall_quality', 0)
                
                if overall_quality < overall_threshold:
                    message = f"视频质量未达到阈值 ({overall_quality:.2f} < {overall_threshold})"
                    
                    # 检查是否允许覆盖质量检查
                    if self.config.get('actions', {}).get('blocking', {}).get('enabled', False):
                        # 如果启用了阻止功能，则抛出异常
                        if not self.config.get('actions', {}).get('blocking', {}).get('allow_override', True):
                            raise QualityThresholdError(
                                message=message,
                                threshold=overall_threshold,
                                actual=overall_quality,
                                metric="overall_quality"
                            )
                    
                    # 否则只记录警告
                    quality_logger.warning(message)
                    quality_logger.warning(f"质量问题: {', '.join(quality_summary.get('issues', []))}")
            
            # 4. 生成质量报告
            if generate_report and self.config.get('reporting', {}).get('auto_save', True):
                output_dir = self.config.get('reporting', {}).get('save_path')
                formats = []
                
                if self.config.get('reporting', {}).get('generate_html', True):
                    formats.append('html')
                
                formats.append('json')  # 总是生成JSON报告
                
                report_paths = generate_quality_report(
                    self.probe.probe_data,
                    output_dir=output_dir,
                    formats=formats
                )
                
                if report_paths:
                    quality_logger.info(f"已生成质量报告: {', '.join(report_paths.values())}")
            
            # 5. 返回处理结果
            result = {
                'success': True,
                'video_path': video_path,
                'quality': quality_summary,
                'recommendations': self.probe.get_recommendations(),
                'session_id': self.session_id
            }
            
            if generate_report and 'report_paths' in locals():
                result['reports'] = report_paths
            
            return result
            
        except Exception as e:
            quality_logger.error(f"视频质量评估失败: {str(e)}")
            
            # 返回错误信息
            return {
                'success': False,
                'error': str(e),
                'video_path': video_path,
                'session_id': self.session_id
            }
    
    def get_recommendations(self) -> List[str]:
        """
        获取质量改进建议
        
        Returns:
            List[str]: 建议列表
        """
        return self.probe.get_recommendations()


def process_video_quality(video_path: str, 
                        subtitle_segments: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    处理视频质量的便捷函数
    
    Args:
        video_path: 视频文件路径
        subtitle_segments: 字幕片段列表
        
    Returns:
        Dict: 处理结果
    """
    controller = QualityController()
    return controller.process_video(video_path, subtitle_segments) 