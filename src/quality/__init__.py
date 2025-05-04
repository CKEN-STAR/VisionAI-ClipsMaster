#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
质量评估模块

提供用于评估生成内容质量的工具和评估标准。
包含黄金标准对比引擎、质量指标计算、时间轴精密校验和评估报告生成功能。
新增动态质量探针系统，实时评估视频处理质量。
新增多维度评分模型，综合技术与艺术维度评估视频质量。
新增法律合规扫描器，提供版权水印检测和合规检查功能。
新增观众行为预测器，预测观众观看和互动行为。
新增硬件兼容性实验室，评估不同设备配置的兼容性。
新增自动化压力测试，模拟各种异常场景并测试系统恢复能力。
新增人工评估接口，收集和管理人类对视频质量的评价。
新增质量溯源追踪器，追踪视频处理流程中的质量问题，找出瓶颈点和关键路径。
"""

from .golden_compare import GoldenComparator, load_golden_dataset
from .metrics import (
    calculate_ssim, 
    calculate_psnr, 
    optical_flow_analysis,
    audio_quality_metrics,
    scene_transition_quality,
    extract_video_features
)
from .report_generator import QualityReport, generate_quality_report
from .timecode_validator import FrameExactValidator, OCRSubtitleValidator
from .dynamic_probes import QualityProbe, analyze_video_quality, check_quality_threshold
from .quality_controller import QualityController, process_video_quality
from .scoring_model import QualityScorer, score_video_quality
from .legal_scanner import CopyrightValidator, WatermarkDatabase, extract_key_frames
from .engagement_predictor import WatchTimePredictor, InteractionPredictor
from .hardware_lab import DeviceCompatibilityTester, DeviceEmulator
from .stress_test import ChaosMonkey, ResourceLimiter, StressTestRunner
from .human_eval import CrowdRatingSystem, EvaluationCampaign, HumanEvaluator
from .provenance_tracer import QualityGenealogy

__all__ = [
    'GoldenComparator',
    'load_golden_dataset',
    'calculate_ssim',
    'calculate_psnr',
    'optical_flow_analysis',
    'audio_quality_metrics',
    'scene_transition_quality',
    'extract_video_features',
    'QualityReport',
    'FrameExactValidator',
    'OCRSubtitleValidator',
    'QualityProbe',
    'analyze_video_quality',
    'check_quality_threshold',
    'QualityController',
    'process_video_quality',
    'generate_quality_report',
    'QualityScorer',
    'score_video_quality',
    'CopyrightValidator',
    'WatermarkDatabase',
    'extract_key_frames',
    'WatchTimePredictor',
    'InteractionPredictor',
    'DeviceCompatibilityTester',
    'DeviceEmulator',
    'ChaosMonkey',
    'ResourceLimiter',
    'StressTestRunner',
    'CrowdRatingSystem',
    'EvaluationCampaign',
    'HumanEvaluator',
    'QualityGenealogy'
] 