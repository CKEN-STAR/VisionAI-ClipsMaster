#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
情感流评估器

评估混剪脚本的情感流动性，分析情感变化是否自然、是否有吸引力，
以及是否能引发观众共鸣。
"""

import os
import json
import logging
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union

from src.utils.log_handler import get_logger

# 配置日志
logger = get_logger("emotion_flow_evaluator")

class EmotionMetrics:
    """情感评估指标"""
    
    CONSISTENCY = "emotion_consistency"        # 情感一致性
    VARIATION = "emotion_variation"            # 情感变化丰富度
    TRANSITION = "emotion_transition"          # 情感过渡自然度
    PEAK_PRESENCE = "emotion_peak_presence"    # 情感高潮存在度
    ENGAGEMENT = "emotion_engagement"          # 情感参与度
    
    @staticmethod
    def all_metrics() -> List[str]:
        """获取所有情感指标"""
        return [
            EmotionMetrics.CONSISTENCY,
            EmotionMetrics.VARIATION,
            EmotionMetrics.TRANSITION,
            EmotionMetrics.PEAK_PRESENCE,
            EmotionMetrics.ENGAGEMENT
        ]

def evaluate_emotion_flow(version: Dict[str, Any],
                        metrics: Optional[List[str]] = None,
                        threshold: float = 0.7) -> float:
    """评估版本的情感流动性
    
    Args:
        version: 版本信息字典
        metrics: 要评估的指标列表，默认为全部
        threshold: 判断为流畅的阈值
        
    Returns:
        情感流畅度得分 (0.0-1.0)
    """
    if not metrics:
        metrics = EmotionMetrics.all_metrics()
    
    # 获取版本内容
    content = _get_version_content(version)
    if not content:
        logger.warning(f"无法获取版本 {version.get('id', 'unknown')} 的内容")
        return 0.0
    
    # 提取情感曲线
    emotion_curve = _extract_emotion_curve(content)
    if not emotion_curve:
        logger.warning(f"无法提取版本 {version.get('id', 'unknown')} 的情感曲线")
        return 0.0
    
    scores = {}
    
    # 评估每个指标
    if EmotionMetrics.CONSISTENCY in metrics:
        scores[EmotionMetrics.CONSISTENCY] = _evaluate_emotion_consistency(emotion_curve)
        
    if EmotionMetrics.VARIATION in metrics:
        scores[EmotionMetrics.VARIATION] = _evaluate_emotion_variation(emotion_curve)
        
    if EmotionMetrics.TRANSITION in metrics:
        scores[EmotionMetrics.TRANSITION] = _evaluate_emotion_transition(emotion_curve)
        
    if EmotionMetrics.PEAK_PRESENCE in metrics:
        scores[EmotionMetrics.PEAK_PRESENCE] = _evaluate_emotion_peak_presence(emotion_curve)
        
    if EmotionMetrics.ENGAGEMENT in metrics:
        scores[EmotionMetrics.ENGAGEMENT] = _evaluate_emotion_engagement(emotion_curve)
    
    # 计算总分
    if not scores:
        return 0.0
        
    overall_score = sum(scores.values()) / len(scores)
    
    # 记录评估结果
    logger.info(f"版本 {version.get('id', 'unknown')} 情感流评分: {overall_score:.2f}")
    for metric, score in scores.items():
        logger.debug(f"  - {metric}: {score:.2f}")
    
    return overall_score

def _get_version_content(version: Dict[str, Any]) -> Dict[str, Any]:
    """获取版本内容
    
    Args:
        version: 版本信息
        
    Returns:
        版本内容
    """
    # 如果版本直接包含内容，直接返回
    if "content" in version:
        return version["content"]
    
    # 如果版本包含脚本内容
    if "screenplay" in version:
        return version["screenplay"]
    
    # 如果版本包含脚本路径
    if "screenplay_path" in version and os.path.exists(version["screenplay_path"]):
        try:
            with open(version["screenplay_path"], 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"读取脚本文件失败: {str(e)}")
    
    # 如果版本包含情感曲线，创建一个包装字典返回
    if "emotion_curve" in version:
        return {"emotion_curve": version["emotion_curve"]}
    
    # 返回空内容
    return {}

def _extract_emotion_curve(content: Dict[str, Any]) -> List[Dict[str, Any]]:
    """从内容中提取情感曲线
    
    Args:
        content: 版本内容
        
    Returns:
        情感曲线，格式为[{"position": 0.1, "intensity": 0.5, "emotion": "joy"}, ...]
    """
    # 如果内容直接包含情感曲线，直接返回
    if "emotion_curve" in content:
        return content["emotion_curve"]
    
    # 如果内容包含场景列表，从场景中提取情感
    if "scenes" in content:
        curve = []
        scenes = content["scenes"]
        for i, scene in enumerate(scenes):
            position = i / len(scenes)
            
            # 提取情感数据
            emotion = scene.get("emotion", "neutral")
            intensity = scene.get("emotion_intensity", 0.5)
            
            curve.append({
                "position": position,
                "intensity": intensity,
                "emotion": emotion
            })
        
        return curve
    
    # 如果内容包含对话列表，从对话中提取情感
    if "dialogues" in content:
        curve = []
        dialogues = content["dialogues"]
        for i, dialogue in enumerate(dialogues):
            position = i / len(dialogues)
            
            # 提取情感数据
            emotion = dialogue.get("emotion", "neutral")
            intensity = dialogue.get("emotion_intensity", 0.5)
            
            curve.append({
                "position": position,
                "intensity": intensity,
                "emotion": emotion
            })
        
        return curve
    
    # 如果没有足够信息，创建模拟曲线
    return [
        {"position": 0.0, "intensity": 0.3, "emotion": "neutral"},
        {"position": 0.2, "intensity": 0.5, "emotion": "joy"},
        {"position": 0.4, "intensity": 0.7, "emotion": "surprise"},
        {"position": 0.6, "intensity": 0.9, "emotion": "fear"},
        {"position": 0.8, "intensity": 0.7, "emotion": "sadness"},
        {"position": 1.0, "intensity": 0.5, "emotion": "neutral"}
    ]

def _evaluate_emotion_consistency(emotion_curve: List[Dict[str, Any]]) -> float:
    """评估情感一致性
    
    检查情感变化是否符合故事发展逻辑，是否有突兀的情感转变
    
    Args:
        emotion_curve: 情感曲线
        
    Returns:
        情感一致性得分 (0.0-1.0)
    """
    # 在实际产品中，这里需要实现真正的情感一致性评估
    # 这里使用模拟实现
    
    # 计算情感强度的变化率
    intensity_changes = []
    for i in range(1, len(emotion_curve)):
        prev_intensity = emotion_curve[i-1]["intensity"]
        curr_intensity = emotion_curve[i]["intensity"]
        change = abs(curr_intensity - prev_intensity)
        intensity_changes.append(change)
    
    # 计算变化率的平均值，太大表示情感变化过于剧烈
    if not intensity_changes:
        return 0.5
    
    avg_change = sum(intensity_changes) / len(intensity_changes)
    
    # 变化率越小，一致性越高
    consistency_score = 1.0 - min(1.0, avg_change * 2)
    
    return consistency_score

def _evaluate_emotion_variation(emotion_curve: List[Dict[str, Any]]) -> float:
    """评估情感变化丰富度
    
    检查故事中情感变化是否丰富多样，是否有足够的情感变化
    
    Args:
        emotion_curve: 情感曲线
        
    Returns:
        情感变化丰富度得分 (0.0-1.0)
    """
    # 在实际产品中，这里需要实现真正的情感丰富度评估
    # 这里使用模拟实现
    
    # 统计不同情感类型的数量
    emotions = set()
    for point in emotion_curve:
        emotions.add(point["emotion"])
    
    # 情感类型越多，变化越丰富
    emotion_count = len(emotions)
    
    # 计算情感强度的标准差，越大表示情感起伏越大
    intensities = [point["intensity"] for point in emotion_curve]
    if not intensities:
        return 0.5
    
    mean_intensity = sum(intensities) / len(intensities)
    variance = sum((x - mean_intensity) ** 2 for x in intensities) / len(intensities)
    std_dev = variance ** 0.5
    
    # 结合情感类型数量和强度变化
    variation_score = min(1.0, (emotion_count / 5) * 0.5 + std_dev)
    
    return variation_score

def _evaluate_emotion_transition(emotion_curve: List[Dict[str, Any]]) -> float:
    """评估情感过渡自然度
    
    检查情感之间的过渡是否自然，是否有突兀的情感变化
    
    Args:
        emotion_curve: 情感曲线
        
    Returns:
        情感过渡自然度得分 (0.0-1.0)
    """
    # 在实际产品中，这里需要实现真正的情感过渡评估
    # 这里使用模拟实现
    
    # 定义情感过渡合理性映射表
    # 表示从一种情感到另一种情感的过渡自然度
    transition_map = {
        "neutral": {"joy": 0.9, "sadness": 0.9, "anger": 0.8, "fear": 0.8, "surprise": 0.9, "disgust": 0.8},
        "joy": {"neutral": 0.9, "sadness": 0.5, "anger": 0.3, "fear": 0.3, "surprise": 0.7, "disgust": 0.3},
        "sadness": {"neutral": 0.8, "joy": 0.4, "anger": 0.6, "fear": 0.7, "surprise": 0.5, "disgust": 0.6},
        "anger": {"neutral": 0.7, "joy": 0.3, "sadness": 0.6, "fear": 0.6, "surprise": 0.5, "disgust": 0.7},
        "fear": {"neutral": 0.7, "joy": 0.3, "sadness": 0.7, "anger": 0.6, "surprise": 0.8, "disgust": 0.6},
        "surprise": {"neutral": 0.8, "joy": 0.7, "sadness": 0.5, "anger": 0.5, "fear": 0.8, "disgust": 0.6},
        "disgust": {"neutral": 0.7, "joy": 0.3, "sadness": 0.6, "anger": 0.7, "fear": 0.6, "surprise": 0.6}
    }
    
    # 计算情感过渡的自然度
    transition_scores = []
    for i in range(1, len(emotion_curve)):
        prev_emotion = emotion_curve[i-1]["emotion"]
        curr_emotion = emotion_curve[i]["emotion"]
        
        # 如果情感没有变化，过渡自然度为1.0
        if prev_emotion == curr_emotion:
            transition_scores.append(1.0)
            continue
        
        # 如果情感发生变化，查询过渡自然度
        # 处理可能不在映射表中的情感
        if prev_emotion not in transition_map:
            prev_emotion = "neutral"
        if curr_emotion not in transition_map.get(prev_emotion, {}):
            curr_emotion = "neutral"
        
        score = transition_map.get(prev_emotion, {}).get(curr_emotion, 0.5)
        transition_scores.append(score)
    
    # 计算平均过渡自然度
    if not transition_scores:
        return 0.7
    
    avg_transition = sum(transition_scores) / len(transition_scores)
    
    return avg_transition

def _evaluate_emotion_peak_presence(emotion_curve: List[Dict[str, Any]]) -> float:
    """评估情感高潮存在度
    
    检查故事中是否有明显的情感高潮，高潮是否出现在合适的位置
    
    Args:
        emotion_curve: 情感曲线
        
    Returns:
        情感高潮存在度得分 (0.0-1.0)
    """
    # 在实际产品中，这里需要实现真正的情感高潮评估
    # 这里使用模拟实现
    
    # 找出情感强度最大的点
    if not emotion_curve:
        return 0.0
    
    max_intensity = max(emotion_curve, key=lambda x: x["intensity"])
    peak_intensity = max_intensity["intensity"]
    peak_position = max_intensity["position"]
    
    # 情感高潮的强度至少要达到0.7才算有效
    if peak_intensity < 0.7:
        return 0.5 * (peak_intensity / 0.7)
    
    # 情感高潮最好出现在故事的60%-80%位置
    ideal_position = 0.7
    position_score = 1.0 - min(1.0, abs(peak_position - ideal_position) * 2)
    
    # 结合强度和位置评分
    peak_score = 0.7 * peak_intensity + 0.3 * position_score
    
    return peak_score

def _evaluate_emotion_engagement(emotion_curve: List[Dict[str, Any]]) -> float:
    """评估情感参与度
    
    评估情感曲线是否能引发观众共鸣，是否有吸引力
    
    Args:
        emotion_curve: 情感曲线
        
    Returns:
        情感参与度得分 (0.0-1.0)
    """
    # 在实际产品中，这里需要实现真正的情感参与度评估
    # 这里使用模拟实现
    
    # 计算情感强度的均值和波动
    intensities = [point["intensity"] for point in emotion_curve]
    if not intensities:
        return 0.5
    
    mean_intensity = sum(intensities) / len(intensities)
    
    # 情感的平均强度要适中，太低缺乏吸引力，太高令人疲劳
    intensity_score = 1.0 - abs(mean_intensity - 0.7) * 2
    
    # 情感的变化频率
    changes = 0
    for i in range(1, len(emotion_curve)):
        if emotion_curve[i]["emotion"] != emotion_curve[i-1]["emotion"]:
            changes += 1
    
    # 适当的情感变化有利于观众参与
    ideal_changes = len(emotion_curve) * 0.3
    change_score = 1.0 - min(1.0, abs(changes - ideal_changes) / ideal_changes)
    
    # 结合强度和变化评分
    engagement_score = 0.6 * intensity_score + 0.4 * change_score
    
    return engagement_score

# 测试函数
def test_emotion_flow_evaluator():
    """测试情感流评估器"""
    # 创建测试版本
    test_version = {
        "id": "test_version",
        "emotion_curve": [
            {"position": 0.0, "intensity": 0.3, "emotion": "neutral"},
            {"position": 0.2, "intensity": 0.5, "emotion": "joy"},
            {"position": 0.4, "intensity": 0.7, "emotion": "surprise"},
            {"position": 0.7, "intensity": 0.9, "emotion": "fear"},
            {"position": 0.9, "intensity": 0.7, "emotion": "sadness"},
            {"position": 1.0, "intensity": 0.5, "emotion": "neutral"}
        ]
    }
    
    # 测试情感流评估
    score = evaluate_emotion_flow(test_version)
    print(f"测试版本情感流评分: {score:.2f}")
    
    # 测试单项指标评估
    consistency_score = evaluate_emotion_flow(test_version, [EmotionMetrics.CONSISTENCY])
    print(f"情感一致性评分: {consistency_score:.2f}")
    
    variation_score = evaluate_emotion_flow(test_version, [EmotionMetrics.VARIATION])
    print(f"情感变化丰富度评分: {variation_score:.2f}")

if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # 运行测试
    test_emotion_flow_evaluator() 