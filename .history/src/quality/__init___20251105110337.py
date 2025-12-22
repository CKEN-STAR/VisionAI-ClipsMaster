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

# 使用按需惰性导出，避免在导入包阶段加载重量依赖（如 torch）
from importlib import import_module as _import_module

_export_map = {
    ".golden_compare": ["GoldenComparator", "load_golden_dataset"],
    ".metrics": [
        "calculate_ssim", "calculate_psnr", "optical_flow_analysis",
        "audio_quality_metrics", "scene_transition_quality", "extract_video_features"
    ],
    ".report_generator": ["QualityReport", "generate_quality_report"],
    ".timecode_validator": ["FrameExactValidator", "OCRSubtitleValidator"],
    ".dynamic_probes": ["QualityProbe", "analyze_video_quality", "check_quality_threshold"],
    ".quality_controller": ["QualityController", "process_video_quality"],
    ".scoring_model": ["QualityScorer", "score_video_quality"],
    ".legal_scanner": ["CopyrightValidator", "WatermarkDatabase", "extract_key_frames"],
    ".engagement_predictor": ["WatchTimePredictor", "InteractionPredictor"],
    ".hardware_lab": ["DeviceCompatibilityTester", "DeviceEmulator"],
}

def __getattr__(name):
    for mod, names in _export_map.items():
        if name in names:
            m = _import_module(__name__ + mod)
            obj = getattr(m, name)
            globals()[name] = obj  # 缓存以提升后续访问性能
            return obj
    raise AttributeError(f"module {__name__} has no attribute {name!r}")


def __dir__():
    return sorted(list(globals().keys()) + [n for names in _export_map.values() for n in names])
# from .human_eval import CrowdRatingSystem, EvaluationCampaign, HumanEvaluator  # 模块不存在，暂时注释
# from .provenance_tracer import QualityGenealogy  # 模块不存在，暂时注释

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
    # 'ChaosMonkey',  # 模块不存在，暂时注释
    # 'ResourceLimiter',  # 模块不存在，暂时注释
    # 'StressTestRunner',  # 模块不存在，暂时注释
    # 'CrowdRatingSystem',  # 模块不存在，暂时注释
    # 'EvaluationCampaign',  # 模块不存在，暂时注释
    # 'HumanEvaluator',  # 模块不存在，暂时注释
    # 'QualityGenealogy'  # 模块不存在，暂时注释
] 