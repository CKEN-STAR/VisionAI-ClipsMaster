#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
情感强度映射器

构建视频/剧本的情感强度图谱，用于分析情感曲线和高潮低谷。
支持多种情感属性的综合分析，适用于短剧混剪的情感节奏优化。
"""

import re
import logging
import numpy as np
import os
import yaml
from typing import List, Dict, Any, Optional, Tuple, Union
from loguru import logger

# 导入情感分析相关功能
from src.nlp.sentiment_analyzer import analyze_sentiment, SentimentAnalyzer

# 默认配置路径
DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                  "configs", "emotion_intensity.yaml")

class EmotionMapper:
    """情感强度映射器，构建情感曲线和图谱"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, config_path: Optional[str] = None):
        """
        初始化情感强度映射器
        
        Args:
            config: 配置参数字典，包含情感强度映射参数
            config_path: 配置文件路径，如不提供则使用默认路径
        """
        # 加载配置
        self.config = self._load_config(config, config_path)
        
        # 情感分析器
        self._analyzer = SentimentAnalyzer()
        
        # 日志记录
        logger.info("情感强度映射器初始化完成")
    
    def _load_config(self, config: Optional[Dict[str, Any]], config_path: Optional[str]) -> Dict[str, Any]:
        """加载配置"""
        if config:
            return config
        
        # 确定配置文件路径
        if not config_path:
            config_path = DEFAULT_CONFIG_PATH
        
        # 尝试从文件加载配置
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f)
            else:
                logger.warning(f"配置文件不存在: {config_path}，使用默认配置")
        except Exception as e:
            logger.warning(f"加载配置文件失败: {e}，使用默认配置")
        
        # 返回默认配置
        return {
            "intensity_curve": {
                "peak_detection": {
                    "exclamation_weight": 0.1,
                    "question_weight": 0.05,
                    "emphasis_weight": 0.15,
                    "capitals_weight": 0.2
                },
                "smoothing": {
                    "enabled": True,
                    "window_size": 3,
                    "weights": [0.25, 0.5, 0.25]
                },
                "extremes": {
                    "peak_threshold": 0.7,
                    "valley_threshold": 0.3,
                    "highlight": True
                }
            }
        }
        
    def build_intensity_curve(self, scenes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        构建情感强度曲线
        
        根据场景列表构建情感强度曲线，分析情感变化趋势。
        
        Args:
            scenes: 场景列表，每个场景包含文本、时间码等信息
            
        Returns:
            情感曲线数据，包含每个点的情感值、峰值等信息
        """
        if not scenes:
            logger.warning("场景列表为空，无法构建情感强度曲线")
            return []
        
        # 构建基础情感曲线
        curve_points = [
            {
                "start": s["start"],
                "end": s["end"],
                "base_score": s["emotion"]["score"] if isinstance(s.get("emotion"), dict) and "score" in s["emotion"] else 0,
                "peak_value": self._calculate_peak(s["text"]) if "text" in s else 0,
                "raw_text": s.get("text", ""),
                "scene_id": s.get("id", f"scene_{i}")
            } for i, s in enumerate(scenes)
        ]
        
        # 平滑情感曲线
        if len(curve_points) > 3 and self.config.get("intensity_curve", {}).get("smoothing", {}).get("enabled", True):
            self._smooth_curve(curve_points)
        
        # 标记情感峰值和低谷
        self._mark_extremes(curve_points)
        
        return curve_points
    
    def _calculate_peak(self, text: str) -> float:
        """
        计算文本的情感强度峰值
        
        根据文本中的情感标记、标点符号和关键词计算情感峰值
        
        Args:
            text: 文本内容
            
        Returns:
            情感强度峰值 (0.0-1.0)
        """
        if not text:
            return 0.0
        
        # 获取配置参数
        peak_config = self.config.get("intensity_curve", {}).get("peak_detection", {})
        exclamation_weight = peak_config.get("exclamation_weight", 0.1)
        question_weight = peak_config.get("question_weight", 0.05)
        emphasis_weight = peak_config.get("emphasis_weight", 0.15)
        capitals_weight = peak_config.get("capitals_weight", 0.2)
        
        # 基于句子结构和情感词计算峰值
        # 1. 检测感叹词和强烈情感表达
        exclamation_count = len(re.findall(r'[!！]', text))
        question_count = len(re.findall(r'[?？]', text))
        
        # 2. 计算重复标点带来的强调效果
        emphasis_patterns = [r'[!！]{2,}', r'[?？]{2,}', r'[.。]{3,}']
        emphasis_count = sum(len(re.findall(pattern, text)) for pattern in emphasis_patterns)
        
        # 3. 计算大写字母/特殊标记带来的强调
        caps_emphasis = 0.0
        if re.search(r'[A-Z]{2,}', text):
            caps_emphasis = capitals_weight
            
        # 4. 分析情感强度
        sentiment_result = analyze_sentiment(text)
        sentiment_intensity = sentiment_result.get('intensity', 0.5)
        
        # 综合计算峰值
        base_peak = sentiment_intensity
        exclamation_boost = min(0.3, exclamation_count * exclamation_weight)
        question_boost = min(0.2, question_count * question_weight)
        emphasis_boost = min(0.3, emphasis_count * emphasis_weight)
        
        peak_value = base_peak + exclamation_boost + question_boost + emphasis_boost + caps_emphasis
        
        # 确保在合理范围内
        return min(1.0, max(0.0, peak_value))
    
    def _smooth_curve(self, curve_points: List[Dict[str, Any]]) -> None:
        """
        平滑情感曲线，减少噪声
        
        Args:
            curve_points: 情感曲线点列表
        """
        # 获取平滑配置
        smooth_config = self.config.get("intensity_curve", {}).get("smoothing", {})
        window_size = smooth_config.get("window_size", 3)
        weights = smooth_config.get("weights", [0.25, 0.5, 0.25])
        
        # 确保窗口大小合理
        window_size = min(window_size, len(curve_points))
        if window_size < 3:
            return
        
        # 提取峰值数组
        peak_values = [point["peak_value"] for point in curve_points]
        
        # 使用滑动窗口平均进行平滑
        smoothed_peaks = peak_values.copy()
        
        half_window = window_size // 2
        for i in range(len(peak_values)):
            # 确定窗口范围
            start = max(0, i - half_window)
            end = min(len(peak_values), i + half_window + 1)
            window = peak_values[start:end]
            
            # 获取窗口权重
            win_weights = weights[:len(window)]
            if sum(win_weights) == 0:
                win_weights = [1.0 / len(window)] * len(window)
            else:
                # 归一化权重
                win_weights = [w/sum(win_weights) for w in win_weights]
            
            # 计算加权平均
            smoothed_peaks[i] = sum(v * w for v, w in zip(window, win_weights))
        
        # 更新平滑后的值
        for i, point in enumerate(curve_points):
            point["original_peak"] = point["peak_value"]  # 保存原始值
            point["peak_value"] = smoothed_peaks[i]  # 更新为平滑后的值
    
    def _mark_extremes(self, curve_points: List[Dict[str, Any]]) -> None:
        """
        标记情感曲线的峰值和低谷
        
        Args:
            curve_points: 情感曲线点列表
        """
        if len(curve_points) < 3:
            return
        
        # 获取极值配置
        extreme_config = self.config.get("intensity_curve", {}).get("extremes", {})
        peak_threshold = extreme_config.get("peak_threshold", 0.7)
        valley_threshold = extreme_config.get("valley_threshold", 0.3)
        
        peak_values = [point["peak_value"] for point in curve_points]
        
        # 初始化标记
        for point in curve_points:
            point["is_peak"] = False
            point["is_valley"] = False
            point["is_turning_point"] = False
            point["is_global_peak"] = False
            point["is_global_valley"] = False
        
        # 识别局部极值
        for i in range(1, len(peak_values) - 1):
            prev_val = peak_values[i-1]
            curr_val = peak_values[i]
            next_val = peak_values[i+1]
            
            # 标记峰值
            if curr_val > prev_val and curr_val > next_val:
                curve_points[i]["is_peak"] = True
                curve_points[i]["is_turning_point"] = True
                
            # 标记低谷
            elif curr_val < prev_val and curr_val < next_val:
                curve_points[i]["is_valley"] = True
                curve_points[i]["is_turning_point"] = True
        
        # 标记全局极值
        if curve_points:
            max_idx = peak_values.index(max(peak_values))
            min_idx = peak_values.index(min(peak_values))
            
            curve_points[max_idx]["is_global_peak"] = True
            curve_points[min_idx]["is_global_valley"] = True
    
    def analyze_emotion_flow(self, curve_points: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        分析情感流程质量
        
        评估情感曲线的质量，包括变化幅度、曲线形态和高潮分布
        
        Args:
            curve_points: 情感曲线点列表
            
        Returns:
            情感流程分析结果
        """
        if not curve_points or len(curve_points) < 3:
            return {"quality": 0.5, "issues": ["数据点不足，无法进行完整分析"]}
        
        # 获取质量评估配置
        quality_config = self.config.get("quality_assessment", {})
        weights = quality_config.get("weights", {})
        thresholds = quality_config.get("thresholds", {})
        
        # 获取权重
        range_weight = weights.get("range_weight", 0.3)
        turning_point_weight = weights.get("turning_point_weight", 0.2)
        climax_weight = weights.get("climax_weight", 0.3)
        linearity_weight = weights.get("linearity_weight", 0.2)
        
        # 获取阈值
        min_range = thresholds.get("min_range", 0.2)
        min_turning_points = thresholds.get("min_turning_points", 2)
        climax_threshold = thresholds.get("climax_threshold", 0.7)
        
        peak_values = [point["peak_value"] for point in curve_points]
        
        # 计算情感变化幅度
        emotion_range = max(peak_values) - min(peak_values)
        
        # 计算转折点数量
        turning_points = sum(1 for point in curve_points if point.get("is_turning_point", False))
        
        # 判断是否有明显高潮
        has_climax = any(point["peak_value"] > climax_threshold for point in curve_points)
        
        # 检查曲线形态
        monotonic_increasing = all(peak_values[i] <= peak_values[i+1] for i in range(len(peak_values)-1))
        monotonic_decreasing = all(peak_values[i] >= peak_values[i+1] for i in range(len(peak_values)-1))
        
        # 评估情感流程质量
        quality = 0.5  # 基础分
        issues = []
        
        # 根据各指标调整分数
        if emotion_range < min_range:
            quality -= 0.2 * range_weight
            issues.append("情感变化幅度过小，缺乏起伏")
        
        if turning_points < min_turning_points and len(curve_points) > 5:
            quality -= 0.1 * turning_point_weight
            issues.append("情感转折点过少，线性程度高")
        
        if monotonic_increasing or monotonic_decreasing:
            quality -= 0.15 * linearity_weight
            issues.append("情感变化过于线性，缺乏波折")
        
        if not has_climax:
            quality -= 0.15 * climax_weight
            issues.append("缺乏明显情感高潮")
        
        # 确保质量分数在合理范围
        quality = max(0.1, min(1.0, quality))
        
        return {
            "quality": quality,
            "emotion_range": emotion_range,
            "turning_points": turning_points,
            "has_climax": has_climax,
            "issues": issues
        }


def build_intensity_curve(scenes: List[Dict[str, Any]], config_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    构建情感强度曲线的便捷函数
    
    Args:
        scenes: 场景列表
        config_path: 配置文件路径，可选
        
    Returns:
        情感曲线数据
    """
    mapper = EmotionMapper(config_path=config_path)
    return mapper.build_intensity_curve(scenes) 