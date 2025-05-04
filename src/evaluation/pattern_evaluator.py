"""
模式重要性评估器

该模块负责评估不同剧本模式对最终爆款视频的影响程度，帮助排序和筛选最有效的模式。
评估维度包括：
1. 观众留存提升率
2. 社交媒体传播系数
3. 平台推荐权重
4. 情感强度
5. 叙事节奏和结构
"""

import os
import json
import yaml
import math
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Tuple, Optional, Union, Set
from dataclasses import dataclass
from pathlib import Path
from loguru import logger
from collections import defaultdict, Counter

from src.utils.memory_guard import track_memory
from src.algorithms.pattern_mining import PatternMiner
from src.nlp.sentiment_analyzer_fallback import SimpleSentimentAnalyzer
from src.utils.exceptions import EvaluationError, ErrorCode
from src.knowledge.pattern_analyzer import PatternAnalyzer


@dataclass
class PatternFeature:
    """模式特征数据类"""
    # 模式ID
    id: str
    # 模式类型
    type: str
    # 模式频率（在爆款视频中出现的频率）
    frequency: float
    # 模式位置（通常在视频中的相对位置0-1）
    position: float
    # 模式持续时间（秒）
    duration: float
    # 转场类型（如硬切、溶解、淡入淡出等）
    transition: str
    # 情感强度（-1到1）
    sentiment: float
    # 与模式相关的关键词
    keywords: List[str]
    # 上下文相关性（与前后内容的连贯性，0-1）
    context_relevance: float
    # 冲突程度（0-1）
    conflict_level: float
    # 惊喜程度（视频中的意外转折，0-1）
    surprise_level: float
    # 能够触发的情感类型
    emotion_types: List[str]


class PatternEvaluator:
    """模式重要性评估器"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化模式评估器
        
        Args:
            config_path: 配置文件路径，如果为None，使用默认配置
        """
        self.config = self._load_config(config_path)
        self.metrics = self.config["metrics"]
        self.pattern_analyzer = PatternAnalyzer()
        self.sentiment_analyzer = SimpleSentimentAnalyzer()
        self._init_models()
        logger.info("模式重要性评估器初始化完成")
    
    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """
        加载配置
        
        Args:
            config_path: 配置文件路径，如果为None，使用默认路径
            
        Returns:
            配置字典
        """
        default_config_path = os.path.join("configs", "pattern_evaluation.yaml")
        config_path = config_path or default_config_path
        
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                logger.info(f"从 {config_path} 加载配置成功")
                return config
            else:
                logger.warning(f"未找到配置文件: {config_path}，使用默认配置")
        except Exception as e:
            logger.warning(f"加载配置失败: {e}，使用默认配置")
        
        # 默认配置
        return {
            "metrics": {
                "audience_retention": {
                    "weight": 0.25,
                    "threshold": 0.6,
                    "description": "观众留存提升率"
                },
                "viral_coefficient": {
                    "weight": 0.2,
                    "threshold": 0.5,
                    "description": "社交媒体传播系数"
                },
                "recommendation_weight": {
                    "weight": 0.15,
                    "threshold": 0.55,
                    "description": "平台推荐权重"
                },
                "emotional_intensity": {
                    "weight": 0.25,
                    "threshold": 0.65,
                    "description": "情感强度指数"
                },
                "narrative_coherence": {
                    "weight": 0.15,
                    "threshold": 0.5,
                    "description": "叙事结构合理性"
                }
            },
            "model_paths": {
                "retention_model": "models/evaluation/retention_estimator.pkl",
                "virality_model": "models/evaluation/virality_estimator.pkl",
                "recommendation_model": "models/evaluation/recommendation_estimator.pkl"
            },
            "thresholds": {
                "min_impact_score": 0.6,
                "min_confidence": 0.65
            },
            "feature_importance": {
                "frequency": 0.3,
                "position": 0.15,
                "sentiment": 0.25,
                "duration": 0.1,
                "surprise_level": 0.2
            }
        }
    
    def _init_models(self):
        """初始化评估模型"""
        try:
            # 在实际环境中，这里应该加载预训练模型
            # 由于我们在低资源环境下，使用轻量级的统计模型
            
            # 准备基于规则的评估函数
            self.model_functions = {
                "audience_retention": self._evaluate_retention,
                "viral_coefficient": self._evaluate_virality,
                "recommendation_weight": self._evaluate_recommendation,
                "emotional_intensity": self._evaluate_emotion,
                "narrative_coherence": self._evaluate_coherence
            }
            
            logger.info("轻量级评估模型初始化完成")
            
        except Exception as e:
            logger.error(f"模型初始化失败: {e}")
            # 使用备用方案
            self._use_fallback_models()
    
    def _use_fallback_models(self):
        """使用备用评估模型"""
        logger.info("使用基于规则的备用评估模型")
        # 简单的基于规则的评估函数
        self.model_functions = {
            "audience_retention": lambda p: min(0.9, 0.3 + 0.6 * p.frequency + 0.1 * p.sentiment),
            "viral_coefficient": lambda p: min(0.9, 0.2 + 0.3 * p.surprise_level + 0.3 * abs(p.sentiment)),
            "recommendation_weight": lambda p: min(0.9, 0.4 + 0.2 * p.frequency + 0.2 * p.context_relevance),
            "emotional_intensity": lambda p: min(0.9, 0.2 + 0.7 * abs(p.sentiment)),
            "narrative_coherence": lambda p: min(0.9, 0.3 + 0.6 * p.context_relevance)
        }
    
    @track_memory("evaluate_pattern")
    def evaluate_pattern(self, pattern: Union[Dict[str, Any], PatternFeature]) -> Dict[str, Any]:
        """
        评估单个模式的重要性
        
        Args:
            pattern: 模式特征或特征字典
            
        Returns:
            Dict: 包含评估结果的字典，包括各项指标和总分
        """
        # 如果输入是字典，转换为PatternFeature
        if isinstance(pattern, dict):
            pattern = self._dict_to_feature(pattern)
        
        # 评估各个指标
        scores = {}
        for metric_name, model_func in self.model_functions.items():
            metric_config = self.metrics[metric_name]
            raw_score = model_func(pattern)
            
            # 应用阈值
            threshold = metric_config["threshold"]
            if raw_score >= threshold:
                normalized_score = (raw_score - threshold) / (1 - threshold)
            else:
                normalized_score = raw_score / threshold * 0.5
            
            # 添加评分
            scores[metric_name] = {
                "raw_score": float(raw_score),
                "normalized_score": float(normalized_score),
                "weight": metric_config["weight"],
                "description": metric_config["description"]
            }
        
        # 计算加权总分
        weighted_sum = sum(
            score["normalized_score"] * score["weight"]
            for score in scores.values()
        )
        
        # 总体影响力评分
        impact_score = min(1.0, weighted_sum)
        
        # 构建结果
        result = {
            "pattern_id": pattern.id,
            "pattern_type": pattern.type,
            "metrics": scores,
            "impact_score": float(impact_score),
            "is_significant": impact_score >= self.config["thresholds"]["min_impact_score"]
        }
        
        return result
    
    def evaluate_multiple_patterns(self, patterns: List[Union[Dict[str, Any], PatternFeature]]) -> List[Dict[str, Any]]:
        """
        评估多个模式并返回排序结果
        
        Args:
            patterns: 模式列表
            
        Returns:
            List[Dict]: 按影响力排序的评估结果列表
        """
        results = []
        for pattern in patterns:
            try:
                result = self.evaluate_pattern(pattern)
                results.append(result)
            except Exception as e:
                logger.error(f"评估模式 {getattr(pattern, 'id', 'unknown')} 失败: {e}")
                continue
        
        # 按影响力排序
        sorted_results = sorted(
            results,
            key=lambda x: x["impact_score"],
            reverse=True
        )
        
        return sorted_results
    
    def get_top_patterns(self, 
                       patterns: List[Union[Dict[str, Any], PatternFeature]], 
                       top_k: int = 5) -> List[Dict[str, Any]]:
        """
        获取最重要的前K个模式
        
        Args:
            patterns: 模式列表
            top_k: 返回的模式数量
            
        Returns:
            前K个最重要的模式
        """
        sorted_results = self.evaluate_multiple_patterns(patterns)
        top_patterns = sorted_results[:min(top_k, len(sorted_results))]
        
        return top_patterns
    
    def group_by_pattern_type(self, 
                           patterns: List[Union[Dict[str, Any], PatternFeature]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        按模式类型分组评估结果
        
        Args:
            patterns: 模式列表
            
        Returns:
            Dict: 按模式类型分组的评估结果
        """
        results = self.evaluate_multiple_patterns(patterns)
        
        # 按类型分组
        grouped = defaultdict(list)
        for result in results:
            pattern_type = result["pattern_type"]
            grouped[pattern_type].append(result)
        
        # 对每组内的模式按影响力排序
        for pattern_type in grouped:
            grouped[pattern_type] = sorted(
                grouped[pattern_type],
                key=lambda x: x["impact_score"],
                reverse=True
            )
        
        return dict(grouped)
    
    def calculate_impact(self, pattern: Union[Dict[str, Any], PatternFeature]) -> float:
        """
        计算模式的影响力分数
        
        Args:
            pattern: 模式特征
            
        Returns:
            float: 影响力分数(0-1)
        """
        # 在原始模式基础上，采用更自然的计算方式
        if isinstance(pattern, dict):
            pattern = self._dict_to_feature(pattern)
        
        # 获取主要特征并计算基础分数
        frequency = getattr(pattern, "frequency", 0.5)
        position = getattr(pattern, "position", 0.5)
        sentiment = abs(getattr(pattern, "sentiment", 0))
        surprise = getattr(pattern, "surprise_level", 0.3)
        conflict = getattr(pattern, "conflict_level", 0.3)
        
        # 应用特征重要性权重
        weights = self.config["feature_importance"]
        weighted_score = (
            frequency * weights["frequency"] +
            position * weights["position"] +
            sentiment * weights["sentiment"] +
            surprise * weights["surprise_level"]
        )
        
        # 应用非线性变换，使评分更有区分度
        impact = min(1.0, 1 / (1 + math.exp(-5 * (weighted_score - 0.5))))
        
        return float(impact)
    
    def _dict_to_feature(self, pattern_dict: Dict[str, Any]) -> PatternFeature:
        """
        将字典转换为PatternFeature对象
        
        Args:
            pattern_dict: 模式特征字典
            
        Returns:
            PatternFeature: 特征对象
        """
        # 获取必要字段，缺失则使用默认值
        return PatternFeature(
            id=pattern_dict.get("id", "unknown"),
            type=pattern_dict.get("type", "generic"),
            frequency=float(pattern_dict.get("frequency", 0.5)),
            position=float(pattern_dict.get("position", 0.5)),
            duration=float(pattern_dict.get("duration", 3.0)),
            transition=pattern_dict.get("transition", "cut"),
            sentiment=float(pattern_dict.get("sentiment", 0.0)),
            keywords=pattern_dict.get("keywords", []),
            context_relevance=float(pattern_dict.get("context_relevance", 0.5)),
            conflict_level=float(pattern_dict.get("conflict_level", 0.3)),
            surprise_level=float(pattern_dict.get("surprise_level", 0.3)),
            emotion_types=pattern_dict.get("emotion_types", ["neutral"])
        )
    
    # 以下是各个评估指标的具体实现
    
    def _evaluate_retention(self, pattern: PatternFeature) -> float:
        """评估模式对观众留存的影响"""
        # 观众留存关键因素：情感强度、位置重要性、冲突程度
        
        # 情感影响因子：情感越强烈，留存率越高
        sentiment_factor = 0.3 + 0.7 * abs(pattern.sentiment)
        
        # 位置影响因子：通常开头和结尾位置最重要
        position = pattern.position
        position_factor = 1.0 - 2.0 * abs(position - 0.5)  # 位于0和1处最高
        
        # 冲突和惊喜影响：制造冲突和惊喜可以增加留存
        conflict_surprise = 0.7 * pattern.conflict_level + 0.3 * pattern.surprise_level
        
        # 加权计算
        retention_score = (
            0.4 * sentiment_factor +
            0.3 * position_factor +
            0.3 * conflict_surprise
        )
        
        return min(1.0, max(0.0, retention_score))
    
    def _evaluate_virality(self, pattern: PatternFeature) -> float:
        """评估模式的社交媒体传播潜力"""
        # 社交传播关键因素：惊喜程度、情感强度、关键词吸引力
        
        # 惊喜因子：惊喜越大越容易传播
        surprise_factor = 0.3 + 0.7 * pattern.surprise_level
        
        # 情感因子：情感越强烈（不管正负）越容易传播
        emotion_factor = 0.2 + 0.8 * abs(pattern.sentiment)
        
        # 关键词因子：关键词越多越好
        keyword_factor = min(1.0, len(pattern.keywords) / 5.0)
        
        # 加权计算
        virality_score = (
            0.5 * surprise_factor +
            0.4 * emotion_factor +
            0.1 * keyword_factor
        )
        
        return min(1.0, max(0.0, virality_score))
    
    def _evaluate_recommendation(self, pattern: PatternFeature) -> float:
        """评估模式在推荐系统中的权重"""
        # 推荐权重关键因素：频率、上下文相关性、持续时间
        
        # 频率因子：出现频率高表示受欢迎
        frequency_factor = 0.3 + 0.7 * pattern.frequency
        
        # 上下文因子：更加连贯的内容更受推荐算法青睐
        context_factor = 0.2 + 0.8 * pattern.context_relevance
        
        # 持续时间因子：理想的片段持续时间（2-5秒为最佳）
        duration = pattern.duration
        if 2.0 <= duration <= 5.0:
            duration_factor = 1.0
        else:
            duration_factor = 1.0 - min(1.0, abs(duration - 3.5) / 5.0)
        
        # 加权计算
        recommendation_score = (
            0.5 * frequency_factor +
            0.4 * context_factor +
            0.1 * duration_factor
        )
        
        return min(1.0, max(0.0, recommendation_score))
    
    def _evaluate_emotion(self, pattern: PatternFeature) -> float:
        """评估模式的情感强度"""
        # 情感强度关键因素：情感极性、冲突程度、情感类型
        
        # 情感极性因子：情感越强烈越好
        polarity_factor = 0.1 + 0.9 * abs(pattern.sentiment)
        
        # 冲突因子：冲突越高越能引起情感波动
        conflict_factor = 0.3 + 0.7 * pattern.conflict_level
        
        # 情感类型因子：某些情感类型更容易引起共鸣
        emotion_type_weights = {
            "joy": 0.8,
            "surprise": 0.9,
            "anger": 0.7,
            "sadness": 0.6,
            "fear": 0.7,
            "disgust": 0.5,
            "neutral": 0.3
        }
        
        type_factors = []
        for emotion_type in pattern.emotion_types:
            type_factors.append(emotion_type_weights.get(emotion_type, 0.5))
        
        emotion_type_factor = max(type_factors) if type_factors else 0.5
        
        # 加权计算
        emotion_score = (
            0.5 * polarity_factor +
            0.3 * conflict_factor +
            0.2 * emotion_type_factor
        )
        
        return min(1.0, max(0.0, emotion_score))
    
    def _evaluate_coherence(self, pattern: PatternFeature) -> float:
        """评估模式的叙事连贯性"""
        # 叙事连贯性关键因素：上下文相关性、位置适当性
        
        # 上下文因子
        context_factor = 0.2 + 0.8 * pattern.context_relevance
        
        # 位置适当性：不同类型的模式适合不同位置
        position = pattern.position
        pattern_type = pattern.type
        
        # 不同模式类型的位置适当性评分函数
        position_scores = {
            "opening": 1.0 - position * 0.8,  # 开场模式应靠前
            "climax": 1.0 - abs(position - 0.7) * 1.5,  # 高潮模式应在70%处
            "transition": 1.0 - abs(position - 0.5) * 1.2,  # 转场应在中间
            "ending": position * 0.9,  # 结尾模式应靠后
            "conflict": 1.0 - abs(position - 0.4) * 1.2,  # 冲突在40%处
            "resolution": 1.0 - abs(position - 0.8) * 1.5,  # 解决在80%处
            "generic": 0.7  # 通用模式位置不那么重要
        }
        
        position_factor = position_scores.get(pattern_type, 0.7)
        position_factor = max(0.3, min(1.0, position_factor))  # 限制在0.3-1.0范围
        
        # 加权计算
        coherence_score = (
            0.7 * context_factor +
            0.3 * position_factor
        )
        
        return min(1.0, max(0.0, coherence_score))


def evaluate_patterns(patterns: List[Dict[str, Any]], config_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    评估模式重要性的便捷函数
    
    Args:
        patterns: 模式列表
        config_path: 配置文件路径
        
    Returns:
        List[Dict]: 评估结果列表
    """
    evaluator = PatternEvaluator(config_path)
    return evaluator.evaluate_multiple_patterns(patterns)


def get_top_patterns(patterns: List[Dict[str, Any]], top_k: int = 5, config_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    获取最重要的模式的便捷函数
    
    Args:
        patterns: 模式列表
        top_k: 返回的模式数量
        config_path: 配置文件路径
        
    Returns:
        List[Dict]: 前K个最重要的模式
    """
    evaluator = PatternEvaluator(config_path)
    return evaluator.get_top_patterns(patterns, top_k)


def evaluate_and_explain(patterns: List[Dict[str, Any]], 
                       top_k: int = None, 
                       config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    评估模式重要性并提供解释（便捷函数）
    
    Args:
        patterns: 模式列表
        top_k: 如果设置，只解释前K个重要的模式，否则解释所有模式
        config_path: 配置文件路径
        
    Returns:
        Dict: 包含评估结果、解释和元数据的字典
    """
    # 评估模式
    evaluation_results = evaluate_patterns(patterns, config_path)
    
    # 提取前K个重要模式（如果指定）
    if top_k is not None and top_k > 0:
        top_evaluations = sorted(
            evaluation_results,
            key=lambda x: x.get("impact_score", 0),
            reverse=True
        )[:min(top_k, len(evaluation_results))]
        
        # 找出top_k模式对应的原始模式
        top_pattern_ids = [eval_result.get("pattern_id") for eval_result in top_evaluations]
        top_patterns = [p for p in patterns if p.get("id") in top_pattern_ids]
    else:
        top_evaluations = evaluation_results
        top_patterns = patterns
    
    # 尝试导入解释器
    try:
        from src.interpretability.pattern_explainer import batch_explain_patterns
        
        # 生成解释
        explanations = batch_explain_patterns(top_patterns, top_evaluations)
        
        # 构建结果
        result = {
            "evaluation": evaluation_results,
            "top_evaluations": top_evaluations if top_k else None,
            "explanations": explanations,
            "has_explanations": True
        }
        
    except ImportError:
        # 解释器模块不可用
        logger.warning("解释器模块不可用，将只返回评估结果")
        result = {
            "evaluation": evaluation_results,
            "top_evaluations": top_evaluations if top_k else None,
            "explanations": None,
            "has_explanations": False
        }
    
    return result 