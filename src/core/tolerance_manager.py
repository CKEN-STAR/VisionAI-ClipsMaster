#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
智能容差管理系统
负责加载、解析和应用容差规则，确保生成的视频和字幕质量符合预期
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union, Tuple
import psutil

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ToleranceManager")

class ToleranceManager:
    """智能容差管理系统，负责评估视频质量和字幕匹配精度"""
    
    def __init__(self, config_path: Optional[str] = None):
        """初始化容差管理器
        
        Args:
            config_path: 容差规则配置文件路径，默认为configs/tolerance_rules.yaml
        """
        self.config_path = config_path or os.path.join('configs', 'tolerance_rules.yaml')
        self.rules = self._load_config()
        self.system_info = self._collect_system_info()
        self._adjust_for_resources()
        logger.info(f"容差管理系统初始化完成，当前设备内存: {self.system_info['memory_gb']}GB")
    
    def _load_config(self) -> Dict[str, Any]:
        """加载容差规则配置文件
        
        Returns:
            Dict[str, Any]: 容差规则配置
        """
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            logger.info(f"成功加载容差规则配置: {self.config_path}")
            return config
        except Exception as e:
            logger.error(f"加载容差规则失败: {str(e)}")
            # 返回默认配置
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """当配置文件加载失败时返回默认配置
        
        Returns:
            Dict[str, Any]: 默认容差规则
        """
        logger.warning("使用默认容差规则配置")
        return {
            "video": {
                "duration_tolerance": 0.5,
                "psnr_threshold": 28,
                "resolution_tolerance": "5%",
                "color_fidelity": "85%",
                "audio": {
                    "sync_tolerance_ms": 50,
                    "quality_db_min": -30,
                    "target_lufs": -14
                }
            },
            "subtitle": {
                "timecode_tolerance": 0.1,
                "text_similarity": 90,
                "entity_coverage": "100%",
                "emotion_fidelity": "85%",
                "coherence_score": 75
            },
            "narrative": {
                "key_plot_retention": "95%",
                "character_arc_completeness": "90%",
                "duration_ratio": {
                    "min": "25%", 
                    "max": "75%",
                    "ideal": "40%"
                },
                "pacing_score_min": 70
            },
            "quality_weights": {
                "video_quality": 0.3,
                "audio_quality": 0.2,
                "subtitle_accuracy": 0.25,
                "narrative_coherence": 0.25
            },
            "adaptive_tolerance": {
                "enabled": True,
                "adjust_for_low_resources": True,
                "max_relaxation_factor": 1.2
            }
        }
    
    def _collect_system_info(self) -> Dict[str, Any]:
        """收集系统资源信息
        
        Returns:
            Dict[str, Any]: 系统资源信息
        """
        system_info = {}
        
        # 检测可用内存
        memory = psutil.virtual_memory()
        system_info['memory_gb'] = round(memory.total / (1024**3), 1)
        system_info['memory_available_gb'] = round(memory.available / (1024**3), 1)
        system_info['memory_percent'] = memory.percent
        
        # 检测CPU信息
        system_info['cpu_count'] = psutil.cpu_count(logical=True)
        system_info['cpu_physical'] = psutil.cpu_count(logical=False)
        
        # 检测是否有GPU
        system_info['has_gpu'] = self._check_gpu()
        
        # 检测存储空间
        disk = psutil.disk_usage('/')
        system_info['disk_free_gb'] = round(disk.free / (1024**3), 1)
        
        # 判断是否为低配置设备
        system_info['is_low_resource'] = (
            system_info['memory_gb'] <= 4 or 
            system_info['cpu_count'] <= 2 or
            not system_info['has_gpu']
        )
        
        logger.info(f"系统资源信息: {system_info}")
        return system_info
    
    def _check_gpu(self) -> bool:
        """检测系统是否有可用的GPU
        
        Returns:
            bool: 是否有GPU
        """
        # 简单检测方法，实际项目中可能需要更复杂的检测
        try:
            # 尝试导入GPU相关库
            import torch
            return torch.cuda.is_available()
        except ImportError:
            pass
        
        # 备用方法检测
        try:
            # 检查NVIDIA驱动
            has_nvidia = os.path.exists('/proc/driver/nvidia')
            if has_nvidia:
                return True
        except:
            pass
        
        # Windows系统可以尝试使用wmi检测
        if os.name == 'nt':
            try:
                import wmi

# 内存使用警告阈值（百分比）
MEMORY_WARNING_THRESHOLD = 80

                computer = wmi.WMI()
                gpu_info = computer.Win32_VideoController()
                for gpu in gpu_info:
                    if gpu.AdapterRAM and int(gpu.AdapterRAM) > 512*1024*1024:  # 大于512MB认为是独显
                        return True
            except:
                pass
        
        return False
    
    def _adjust_for_resources(self) -> None:
        """根据系统资源情况调整容差规则"""
        if (self.rules.get('adaptive_tolerance', {}).get('enabled', False) and 
            self.rules.get('adaptive_tolerance', {}).get('adjust_for_low_resources', False) and
            self.system_info.get('is_low_resource', False)):
            
            # 获取调整系数
            factor = self.rules.get('adaptive_tolerance', {}).get('max_relaxation_factor', 1.2)
            logger.info(f"低配置设备，应用容差调整系数: {factor}")
            
            # 调整视频质量阈值
            if 'video' in self.rules:
                self.rules['video']['psnr_threshold'] = max(20, int(self.rules['video']['psnr_threshold'] / factor))
                
                # 解析和调整百分比值
                if 'color_fidelity' in self.rules['video']:
                    color_fidelity = self._parse_percentage(self.rules['video']['color_fidelity'])
                    self.rules['video']['color_fidelity'] = f"{max(70, int(color_fidelity / factor))}%"
            
            # 调整字幕匹配阈值
            if 'subtitle' in self.rules:
                self.rules['subtitle']['text_similarity'] = max(75, int(self.rules['subtitle']['text_similarity'] / factor))
                
                if 'coherence_score' in self.rules['subtitle']:
                    self.rules['subtitle']['coherence_score'] = max(60, int(self.rules['subtitle']['coherence_score'] / factor))
            
            # 调整剧情评估标准
            if 'narrative' in self.rules and 'pacing_score_min' in self.rules['narrative']:
                self.rules['narrative']['pacing_score_min'] = max(55, int(self.rules['narrative']['pacing_score_min'] / factor))
            
            logger.info("已完成低配置设备容差规则调整")
    
    def _parse_percentage(self, value: str) -> float:
        """解析百分比字符串为浮点数
        
        Args:
            value: 百分比字符串，如"85%"
            
        Returns:
            float: 解析后的浮点数，如0.85
        """
        if isinstance(value, (int, float)):
            return float(value)
        
        if isinstance(value, str) and value.endswith('%'):
            try:
                return float(value.rstrip('%')) / 100
            except ValueError:
                logger.warning(f"无法解析百分比值: {value}，使用默认值0.8")
                return 0.8
        
        return float(value)
    
    def check_video_quality(self, video_metrics: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """检查视频质量是否符合容差标准
        
        Args:
            video_metrics: 视频质量指标，包含duration, psnr, resolution_match等
            
        Returns:
            Tuple[bool, Dict]: (是否通过检查, 详细评估结果)
        """
        results = {}
        video_rules = self.rules.get('video', {})
        
        # 检查时长
        if 'duration' in video_metrics and 'duration_tolerance' in video_rules:
            duration_diff = abs(video_metrics['duration'] - video_metrics.get('target_duration', 0))
            results['duration_check'] = duration_diff <= video_rules['duration_tolerance']
            results['duration_diff'] = duration_diff
        
        # 检查PSNR
        if 'psnr' in video_metrics and 'psnr_threshold' in video_rules:
            results['psnr_check'] = video_metrics['psnr'] >= video_rules['psnr_threshold']
            results['psnr_value'] = video_metrics['psnr']
        
        # 检查分辨率匹配
        if 'resolution_match' in video_metrics:
            resolution_tolerance = self._parse_percentage(video_rules.get('resolution_tolerance', '5%'))
            results['resolution_check'] = video_metrics['resolution_match'] >= (1 - resolution_tolerance)
        
        # 检查色彩保真度
        if 'color_hist_similarity' in video_metrics and 'color_fidelity' in video_rules:
            color_threshold = self._parse_percentage(video_rules['color_fidelity'])
            results['color_check'] = video_metrics['color_hist_similarity'] >= color_threshold
            results['color_similarity'] = video_metrics['color_hist_similarity']
        
        # 检查音频同步
        if 'audio_sync_offset_ms' in video_metrics and 'audio' in video_rules:
            audio_sync_tolerance = video_rules['audio'].get('sync_tolerance_ms', 50)
            results['audio_sync_check'] = abs(video_metrics['audio_sync_offset_ms']) <= audio_sync_tolerance
        
        # 计算总体通过情况
        checks_passed = [v for k, v in results.items() if k.endswith('_check')]
        results['overall_passed'] = all(checks_passed) if checks_passed else False
        results['pass_rate'] = sum(1 for c in checks_passed if c) / len(checks_passed) if checks_passed else 0
        
        return results['overall_passed'], results
    
    def check_subtitle_quality(self, subtitle_metrics: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """检查字幕质量是否符合容差标准
        
        Args:
            subtitle_metrics: 字幕质量指标，包含timecode_accuracy, text_similarity, entity_match等
            
        Returns:
            Tuple[bool, Dict]: (是否通过检查, 详细评估结果)
        """
        results = {}
        subtitle_rules = self.rules.get('subtitle', {})
        
        # 检查时间码精度
        if 'timecode_accuracy' in subtitle_metrics and 'timecode_tolerance' in subtitle_rules:
            max_timecode_error = subtitle_metrics.get('max_timecode_error', 0)
            results['timecode_check'] = max_timecode_error <= subtitle_rules['timecode_tolerance']
            results['max_timecode_error'] = max_timecode_error
        
        # 检查文本相似度
        if 'text_similarity' in subtitle_metrics and 'text_similarity' in subtitle_rules:
            results['text_similarity_check'] = subtitle_metrics['text_similarity'] >= subtitle_rules['text_similarity']
            results['text_similarity_value'] = subtitle_metrics['text_similarity']
        
        # 检查实体匹配
        if 'entity_match_rate' in subtitle_metrics and 'entity_coverage' in subtitle_rules:
            entity_threshold = self._parse_percentage(subtitle_rules['entity_coverage'])
            results['entity_check'] = subtitle_metrics['entity_match_rate'] >= entity_threshold
            results['entity_match_rate'] = subtitle_metrics['entity_match_rate']
        
        # 检查情感表达
        if 'emotion_accuracy' in subtitle_metrics and 'emotion_fidelity' in subtitle_rules:
            emotion_threshold = self._parse_percentage(subtitle_rules['emotion_fidelity'])
            results['emotion_check'] = subtitle_metrics['emotion_accuracy'] >= emotion_threshold
        
        # 检查语义连贯性
        if 'coherence_score' in subtitle_metrics and 'coherence_score' in subtitle_rules:
            results['coherence_check'] = subtitle_metrics['coherence_score'] >= subtitle_rules['coherence_score']
            results['coherence_value'] = subtitle_metrics['coherence_score']
        
        # 计算总体通过情况
        checks_passed = [v for k, v in results.items() if k.endswith('_check')]
        results['overall_passed'] = all(checks_passed) if checks_passed else False
        results['pass_rate'] = sum(1 for c in checks_passed if c) / len(checks_passed) if checks_passed else 0
        
        return results['overall_passed'], results
    
    def check_narrative_quality(self, narrative_metrics: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """检查剧情质量是否符合标准
        
        Args:
            narrative_metrics: 剧情质量指标，包括关键情节点保留率、角色弧线完整度等
            
        Returns:
            Tuple[bool, Dict]: (是否通过检查, 详细评估结果)
        """
        results = {}
        narrative_rules = self.rules.get('narrative', {})
        
        # 检查关键情节点保留率
        if 'plot_retention' in narrative_metrics and 'key_plot_retention' in narrative_rules:
            plot_threshold = self._parse_percentage(narrative_rules['key_plot_retention'])
            results['plot_check'] = narrative_metrics['plot_retention'] >= plot_threshold
            results['plot_retention'] = narrative_metrics['plot_retention']
        
        # 检查角色弧线完整度
        if 'character_arc_score' in narrative_metrics and 'character_arc_completeness' in narrative_rules:
            arc_threshold = self._parse_percentage(narrative_rules['character_arc_completeness'])
            results['arc_check'] = narrative_metrics['character_arc_score'] >= arc_threshold
        
        # 检查时长比例
        if 'duration_ratio' in narrative_metrics and 'duration_ratio' in narrative_rules:
            ratio = narrative_metrics['duration_ratio']
            min_ratio = self._parse_percentage(narrative_rules['duration_ratio'].get('min', '25%'))
            max_ratio = self._parse_percentage(narrative_rules['duration_ratio'].get('max', '75%'))
            results['duration_ratio_check'] = min_ratio <= ratio <= max_ratio
            results['duration_ratio'] = ratio
            
            # 计算与理想比例的差距
            ideal_ratio = self._parse_percentage(narrative_rules['duration_ratio'].get('ideal', '40%'))
            results['ideal_ratio_distance'] = abs(ratio - ideal_ratio)
        
        # 检查叙事节奏
        if 'pacing_score' in narrative_metrics and 'pacing_score_min' in narrative_rules:
            results['pacing_check'] = narrative_metrics['pacing_score'] >= narrative_rules['pacing_score_min']
            results['pacing_score'] = narrative_metrics['pacing_score']
        
        # 计算总体通过情况
        checks_passed = [v for k, v in results.items() if k.endswith('_check')]
        results['overall_passed'] = all(checks_passed) if checks_passed else False
        results['pass_rate'] = sum(1 for c in checks_passed if c) / len(checks_passed) if checks_passed else 0
        
        return results['overall_passed'], results
    
    def calculate_overall_score(self, video_results: Dict[str, Any], 
                               subtitle_results: Dict[str, Any],
                               narrative_results: Dict[str, Any]) -> Dict[str, Any]:
        """计算整体质量得分
        
        Args:
            video_results: 视频质量评估结果
            subtitle_results: 字幕质量评估结果
            narrative_results: 剧情质量评估结果
            
        Returns:
            Dict[str, Any]: 整体质量评分和级别
        """
        # 获取权重
        weights = self.rules.get('quality_weights', {
            'video_quality': 0.3,
            'audio_quality': 0.2,
            'subtitle_accuracy': 0.25,
            'narrative_coherence': 0.25
        })
        
        # 计算加权得分
        video_score = video_results.get('pass_rate', 0) * 100
        subtitle_score = subtitle_results.get('pass_rate', 0) * 100
        narrative_score = narrative_results.get('pass_rate', 0) * 100
        
        overall_score = (
            video_score * weights['video_quality'] +
            subtitle_score * weights['subtitle_accuracy'] +
            narrative_score * weights['narrative_coherence']
        )
        
        # 确定质量级别
        alert_thresholds = self.rules.get('alert_thresholds', {
            'critical_failure': 60,
            'warning_level': 75,
            'notice_level': 85
        })
        
        if overall_score < alert_thresholds.get('critical_failure', 60):
            quality_level = "严重问题"
        elif overall_score < alert_thresholds.get('warning_level', 75):
            quality_level = "警告"
        elif overall_score < alert_thresholds.get('notice_level', 85):
            quality_level = "提示"
        else:
            quality_level = "优秀"
        
        return {
            'overall_score': round(overall_score, 1),
            'quality_level': quality_level,
            'video_score': round(video_score, 1),
            'subtitle_score': round(subtitle_score, 1),
            'narrative_score': round(narrative_score, 1),
            'passed': quality_level not in ["严重问题", "警告"]
        }
    
    def verify_copyright_safety(self, safety_metrics: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """验证版权安全性
        
        Args:
            safety_metrics: 版权安全指标，包括水印检测、音频指纹等
            
        Returns:
            Tuple[bool, Dict]: (是否通过安全检查, 详细结果)
        """
        results = {}
        safety_rules = self.rules.get('copyright_safety', {})
        
        # 检查水印
        if 'watermark_confidence' in safety_metrics and 'watermark_detection_confidence' in safety_rules:
            watermark_threshold = safety_rules['watermark_detection_confidence']
            has_watermark = safety_metrics['watermark_confidence'] >= watermark_threshold
            results['watermark_check'] = not has_watermark  # 通过检查意味着没有水印
            results['watermark_confidence'] = safety_metrics['watermark_confidence']
        
        # 检查音频指纹
        if 'audio_fingerprint_match' in safety_metrics and 'audio_fingerprint_threshold' in safety_rules:
            fingerprint_threshold = safety_rules['audio_fingerprint_threshold']
            fingerprint_match = safety_metrics['audio_fingerprint_match'] >= fingerprint_threshold
            results['fingerprint_check'] = not fingerprint_match  # 通过检查意味着没有匹配指纹
        
        # 计算总体安全状态
        checks_passed = [v for k, v in results.items() if k.endswith('_check')]
        results['is_safe'] = all(checks_passed) if checks_passed else True  # 默认安全
        
        return results['is_safe'], results
    
    def save_adjusted_config(self, output_path: Optional[str] = None) -> str:
        """保存调整后的配置到文件
        
        Args:
            output_path: 输出文件路径，默认为原配置路径
            
        Returns:
            str: 配置文件保存路径
        """
        output_path = output_path or self.config_path
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.rules, f, default_flow_style=False, allow_unicode=True)
            logger.info(f"配置已保存至: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"保存配置失败: {str(e)}")
            return ""


# 简单的使用示例
if __name__ == "__main__":
    # 创建容差管理器
    manager = ToleranceManager()
    
    # 模拟视频质量评估数据
    video_metrics = {
        "duration": 120.5,
        "target_duration": 120,
        "psnr": 32.5,
        "resolution_match": 0.98,
        "color_hist_similarity": 0.92,
        "audio_sync_offset_ms": 25
    }
    
    # 模拟字幕质量评估数据
    subtitle_metrics = {
        "max_timecode_error": 0.08,
        "text_similarity": 92.5,
        "entity_match_rate": 0.95,
        "emotion_accuracy": 0.87,
        "coherence_score": 82
    }
    
    # 模拟剧情质量评估数据
    narrative_metrics = {
        "plot_retention": 0.96,
        "character_arc_score": 0.91,
        "duration_ratio": 0.45,
        "pacing_score": 85
    }
    
    # 进行评估
    video_passed, video_results = manager.check_video_quality(video_metrics)
    subtitle_passed, subtitle_results = manager.check_subtitle_quality(subtitle_metrics)
    narrative_passed, narrative_results = manager.check_narrative_quality(narrative_metrics)
    
    # 计算总分
    overall = manager.calculate_overall_score(
        video_results, subtitle_results, narrative_results
    )
    
    print(f"视频质量评估: {'通过' if video_passed else '失败'}")
    print(f"字幕质量评估: {'通过' if subtitle_passed else '失败'}")
    print(f"剧情质量评估: {'通过' if narrative_passed else '失败'}")
    print(f"总体评分: {overall['overall_score']} - {overall['quality_level']}") 