#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
动态质量探针系统

在视频处理流程中插入多个质量检测点，实时监控和评估生成内容的质量。
主要功能：
1. 在视频处理的关键节点插入探针
2. 收集质量指标数据
3. 实时评估内容质量
4. 提供质量改进建议
"""

import os
import json
import time
import logging
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime
import ffmpeg
from loguru import logger

from src.utils.log_handler import get_logger
from src.utils.file_handler import ensure_dir_exists
from src.core.exceptions import QualityCheckError

# 获取logger
quality_logger = get_logger("quality_probes")

class QualityProbe:
    """
    质量探针类 - 负责在视频处理流程中插入检测点并评估质量
    """
    # 探针点定义 - 视频处理进度的百分比位置
    PROBE_POINTS = [
        0.1, 0.25, 0.5, 0.75, 0.9  # 视频时长百分比
    ]
    
    # 质量评估阈值
    QUALITY_THRESHOLDS = {
        'narrative_coherence': 0.7,  # 叙事连贯性阈值
        'audio_quality': 0.65,       # 音频质量阈值
        'visual_quality': 0.6,       # 视频质量阈值
        'emotion_consistency': 0.75, # 情感一致性阈值
        'dialog_naturalness': 0.8    # 对话自然度阈值
    }
    
    def __init__(self, 
                 output_dir: Optional[str] = None, 
                 custom_thresholds: Optional[Dict[str, float]] = None):
        """
        初始化质量探针
        
        Args:
            output_dir: 质量报告输出目录
            custom_thresholds: 自定义质量阈值
        """
        self.probe_data = {}
        self.session_id = datetime.now().strftime("%Y%m%d%H%M%S")
        
        # 设置输出目录
        if output_dir:
            self.output_dir = output_dir
        else:
            self.output_dir = os.path.join("data", "quality_reports")
        
        ensure_dir_exists(self.output_dir)
        
        # 更新质量阈值
        if custom_thresholds:
            self.QUALITY_THRESHOLDS.update(custom_thresholds)
            
        # 初始化探针数据结构
        self._init_probe_data()
        
    def _init_probe_data(self):
        """初始化探针数据结构"""
        self.probe_data = {
            'session_id': self.session_id,
            'timestamp': datetime.now().isoformat(),
            'probes': {},
            'summary': {
                'overall_quality': None,
                'issues': [],
                'recommendations': []
            }
        }
    
    def insert_probes(self, video_path: str) -> str:
        """
        在视频中插入质量检测探针
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            str: 处理后的视频路径
        """
        quality_logger.info(f"开始在视频 {video_path} 中插入质量探针")
        
        # 获取视频总时长
        try:
            probe = ffmpeg.probe(video_path)
            duration = float(probe['format']['duration'])
            quality_logger.debug(f"视频总时长: {duration}秒")
        except Exception as e:
            quality_logger.error(f"获取视频信息失败: {str(e)}")
            duration = 0
        
        # 在关键时间点插入元数据标记
        for pos in self.PROBE_POINTS:
            timestamp = duration * pos
            self._inject_metadata(video_path, f"PROBE_{pos}", self._get_timestamp(timestamp))
            
            # 记录探针信息
            self.probe_data['probes'][f"{pos:.2f}"] = {
                'timestamp': timestamp,
                'metrics': {}
            }
            
            quality_logger.debug(f"在位置 {pos:.2f} (时间: {timestamp:.2f}秒) 插入探针")
        
        return video_path
    
    def _inject_metadata(self, video_path: str, marker_name: str, timestamp: float):
        """
        在视频中注入元数据标记（实际实现可能需要视频编辑库）
        
        由于直接修改视频文件较为复杂，这里仅记录标记信息，
        在实际实现中可以使用FFmpeg的metadata选项或生成EDL文件
        
        Args:
            video_path: 视频文件路径
            marker_name: 标记名称
            timestamp: 时间戳
        """
        # 在探针数据中记录标记
        marker_key = f"marker_{marker_name}"
        if 'markers' not in self.probe_data:
            self.probe_data['markers'] = {}
            
        self.probe_data['markers'][marker_key] = {
            'timestamp': timestamp,
            'name': marker_name
        }
    
    def _get_timestamp(self, seconds: float) -> str:
        """
        将秒数转换为时间戳格式 HH:MM:SS.mmm
        
        Args:
            seconds: 秒数
            
        Returns:
            str: 格式化的时间戳
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:06.3f}"
    
    def collect_metrics(self, 
                        position: float, 
                        metrics: Dict[str, Any]) -> None:
        """
        收集特定位置的质量指标
        
        Args:
            position: 探针位置（0-1之间的比例）
            metrics: 质量指标数据
        """
        pos_key = f"{position:.2f}"
        if pos_key not in self.probe_data['probes']:
            quality_logger.warning(f"位置 {pos_key} 的探针不存在，将创建新探针")
            self.probe_data['probes'][pos_key] = {
                'timestamp': None,
                'metrics': {}
            }
        
        # 更新指标
        self.probe_data['probes'][pos_key]['metrics'].update(metrics)
        quality_logger.debug(f"在位置 {pos_key} 收集质量指标: {metrics}")
    
    def analyze_narrative_coherence(self, 
                                   subtitle_segments: List[Dict[str, Any]]) -> float:
        """
        分析叙事连贯性
        
        Args:
            subtitle_segments: 字幕片段列表
            
        Returns:
            float: 叙事连贯性得分 (0-1)
        """
        # 简化版的叙事连贯性分析
        if not subtitle_segments or len(subtitle_segments) < 2:
            return 0.0
            
        # 分析相邻字幕的时间连续性
        time_gaps = []
        for i in range(1, len(subtitle_segments)):
            prev_end = subtitle_segments[i-1].get('end_time', 0)
            curr_start = subtitle_segments[i].get('start_time', 0)
            if prev_end and curr_start:
                gap = curr_start - prev_end
                time_gaps.append(max(0, gap))  # 只考虑正的间隔
        
        # 计算平均间隔并归一化
        if time_gaps:
            avg_gap = sum(time_gaps) / len(time_gaps)
            # 理想间隔应小于0.5秒
            coherence_score = max(0, 1 - (avg_gap / 2))
        else:
            coherence_score = 0.5  # 默认中等得分
        
        return min(1.0, coherence_score)
    
    def analyze_audio_quality(self, video_path: str, position: float) -> float:
        """
        分析音频质量
        
        Args:
            video_path: 视频文件路径
            position: 视频位置 (0-1)
            
        Returns:
            float: 音频质量得分 (0-1)
        """
        try:
            # 使用ffmpeg探测音频信息
            probe = ffmpeg.probe(video_path)
            
            # 默认质量分数
            quality_score = 0.8
            
            # 查找音频流
            audio_stream = next((stream for stream in probe['streams'] 
                               if stream['codec_type'] == 'audio'), None)
            
            if not audio_stream:
                return 0.0  # 无音频流
                
            # 基于音频码率和声道数的简单评分
            bit_rate = float(audio_stream.get('bit_rate', 0)) / 1000  # kbps
            channels = int(audio_stream.get('channels', 0))
            
            # 码率评分 (128kbps为基准)
            if bit_rate > 0:
                br_score = min(1.0, bit_rate / 128)
            else:
                br_score = 0.5
                
            # 声道评分 (立体声为佳)
            ch_score = min(1.0, channels / 2)
            
            # 加权平均
            quality_score = (br_score * 0.7) + (ch_score * 0.3)
            
            return quality_score
            
        except Exception as e:
            quality_logger.error(f"分析音频质量时出错: {str(e)}")
            return 0.5  # 出错时返回中等分数
    
    def analyze_visual_quality(self, video_path: str, position: float) -> float:
        """
        分析视频画面质量
        
        Args:
            video_path: 视频文件路径
            position: 视频位置 (0-1)
            
        Returns:
            float: 视频质量得分 (0-1)
        """
        try:
            # 使用ffmpeg探测视频信息
            probe = ffmpeg.probe(video_path)
            
            # 默认质量分数
            quality_score = 0.8
            
            # 查找视频流
            video_stream = next((stream for stream in probe['streams'] 
                               if stream['codec_type'] == 'video'), None)
            
            if not video_stream:
                return 0.0  # 无视频流
                
            # 基于分辨率和比特率的简单评分
            width = int(video_stream.get('width', 0))
            height = int(video_stream.get('height', 0))
            bit_rate = float(video_stream.get('bit_rate', 0)) / 1000000  # Mbps
            
            # 分辨率评分 (1080p为基准)
            resolution = width * height
            res_score = min(1.0, resolution / (1920 * 1080))
            
            # 比特率评分 (5Mbps为基准)
            if bit_rate > 0:
                br_score = min(1.0, bit_rate / 5)
            else:
                br_score = 0.6
                
            # 加权平均
            quality_score = (res_score * 0.5) + (br_score * 0.5)
            
            return quality_score
            
        except Exception as e:
            quality_logger.error(f"分析视频质量时出错: {str(e)}")
            return 0.5  # 出错时返回中等分数
    
    def evaluate_quality(self, 
                        video_path: str,
                        subtitle_segments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        评估整体视频质量并生成报告
        
        Args:
            video_path: 视频文件路径
            subtitle_segments: 字幕片段列表
            
        Returns:
            Dict: 质量评估报告
        """
        quality_logger.info(f"开始评估视频 {video_path} 的质量")
        
        # 1. 分析叙事连贯性
        coherence_score = self.analyze_narrative_coherence(subtitle_segments)
        
        # 2. 在各探针点分析质量
        overall_metrics = {
            'narrative_coherence': coherence_score,
            'audio_quality': [],
            'visual_quality': []
        }
        
        # 遍历探针点
        for pos in self.PROBE_POINTS:
            pos_key = f"{pos:.2f}"
            
            # 音频质量
            audio_score = self.analyze_audio_quality(video_path, pos)
            overall_metrics['audio_quality'].append(audio_score)
            
            # 视频质量
            visual_score = self.analyze_visual_quality(video_path, pos)
            overall_metrics['visual_quality'].append(visual_score)
            
            # 更新探针数据
            if pos_key in self.probe_data['probes']:
                self.probe_data['probes'][pos_key]['metrics'].update({
                    'audio_quality': audio_score,
                    'visual_quality': visual_score
                })
        
        # 计算平均分数
        overall_metrics['audio_quality'] = np.mean(overall_metrics['audio_quality'])
        overall_metrics['visual_quality'] = np.mean(overall_metrics['visual_quality'])
        
        # 3. 生成整体质量评分 (加权平均)
        weights = {
            'narrative_coherence': 0.4,
            'audio_quality': 0.3,
            'visual_quality': 0.3
        }
        
        overall_score = sum([
            overall_metrics[metric] * weights[metric] 
            for metric in weights
        ])
        
        # 4. 识别问题并提出建议
        issues = []
        recommendations = []
        
        for metric, threshold in self.QUALITY_THRESHOLDS.items():
            if metric in overall_metrics and overall_metrics[metric] < threshold:
                issues.append(f"{metric}得分过低 ({overall_metrics[metric]:.2f} < {threshold})")
                
                # 根据不同指标给出建议
                if metric == 'narrative_coherence':
                    recommendations.append("提高字幕片段之间的连贯性，减少时间间隔")
                elif metric == 'audio_quality':
                    recommendations.append("提高音频码率或修复音频问题")
                elif metric == 'visual_quality':
                    recommendations.append("提高视频分辨率或比特率")
        
        # 5. 更新总结信息
        self.probe_data['summary'] = {
            'overall_quality': overall_score,
            'metrics': overall_metrics,
            'issues': issues,
            'recommendations': recommendations,
            'pass': overall_score >= 0.7  # 总体质量阈值
        }
        
        # 6. 保存报告
        self._save_report()
        
        quality_logger.info(f"质量评估完成，总体得分: {overall_score:.2f}")
        if issues:
            quality_logger.warning(f"发现质量问题: {', '.join(issues)}")
        
        return self.probe_data['summary']
    
    def _save_report(self) -> str:
        """
        保存质量报告到文件
        
        Returns:
            str: 报告文件路径
        """
        report_path = os.path.join(
            self.output_dir, 
            f"quality_report_{self.session_id}.json"
        )
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.probe_data, f, ensure_ascii=False, indent=2)
            
        quality_logger.info(f"质量报告已保存至: {report_path}")
        return report_path
    
    def get_recommendations(self) -> List[str]:
        """
        获取质量改进建议
        
        Returns:
            List[str]: 建议列表
        """
        return self.probe_data['summary'].get('recommendations', [])


def analyze_video_quality(video_path: str, 
                        subtitle_segments: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    分析视频质量的便捷函数
    
    Args:
        video_path: 视频文件路径
        subtitle_segments: 字幕片段列表
        
    Returns:
        Dict: 质量评估报告
    """
    probe = QualityProbe()
    probe.insert_probes(video_path)
    return probe.evaluate_quality(video_path, subtitle_segments)


def check_quality_threshold(video_path: str, 
                          subtitle_segments: List[Dict[str, Any]],
                          threshold: float = 0.7) -> bool:
    """
    检查视频是否满足质量阈值的便捷函数
    
    Args:
        video_path: 视频文件路径
        subtitle_segments: 字幕片段列表
        threshold: 质量阈值 (0-1)
        
    Returns:
        bool: 是否通过质量检查
    """
    report = analyze_video_quality(video_path, subtitle_segments)
    return report.get('overall_quality', 0) >= threshold 