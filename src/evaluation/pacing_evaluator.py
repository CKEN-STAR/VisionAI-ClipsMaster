#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
节奏控制评估器

评估混剪脚本的节奏控制，包括叙事节奏、场景长度分布、高潮转折点布局等。
"""

import os
import json
import logging
import statistics
from typing import Dict, List, Any, Optional, Tuple, Union

from src.utils.log_handler import get_logger

# 配置日志
logger = get_logger("pacing_evaluator")

class PacingMetrics:
    """节奏评估指标"""
    
    SCENE_DISTRIBUTION = "scene_distribution"      # 场景长度分布
    RHYTHM_VARIATION = "rhythm_variation"          # 节奏变化
    CLIMAX_PLACEMENT = "climax_placement"          # 高潮布局
    BUILDUP_QUALITY = "buildup_quality"            # 铺垫质量
    RESOLUTION_PACING = "resolution_pacing"        # 结局节奏
    
    @staticmethod
    def all_metrics() -> List[str]:
        """获取所有节奏指标"""
        return [
            PacingMetrics.SCENE_DISTRIBUTION,
            PacingMetrics.RHYTHM_VARIATION,
            PacingMetrics.CLIMAX_PLACEMENT,
            PacingMetrics.BUILDUP_QUALITY,
            PacingMetrics.RESOLUTION_PACING
        ]

def evaluate_pacing(version: Dict[str, Any],
                  metrics: Optional[List[str]] = None,
                  threshold: float = 0.7) -> float:
    """评估版本的节奏控制
    
    Args:
        version: 版本信息字典
        metrics: 要评估的指标列表，默认为全部
        threshold: 判断为良好的阈值
        
    Returns:
        节奏控制得分 (0.0-1.0)
    """
    if not metrics:
        metrics = PacingMetrics.all_metrics()
    
    # 获取版本内容
    content = _get_version_content(version)
    if not content:
        logger.warning(f"无法获取版本 {version.get('id', 'unknown')} 的内容")
        return 0.0
    
    # 提取节奏数据
    pacing_data = _extract_pacing_data(content)
    if not pacing_data:
        logger.warning(f"无法提取版本 {version.get('id', 'unknown')} 的节奏数据")
        return 0.0
    
    scores = {}
    
    # 评估每个指标
    if PacingMetrics.SCENE_DISTRIBUTION in metrics:
        scores[PacingMetrics.SCENE_DISTRIBUTION] = _evaluate_scene_distribution(pacing_data)
        
    if PacingMetrics.RHYTHM_VARIATION in metrics:
        scores[PacingMetrics.RHYTHM_VARIATION] = _evaluate_rhythm_variation(pacing_data)
        
    if PacingMetrics.CLIMAX_PLACEMENT in metrics:
        scores[PacingMetrics.CLIMAX_PLACEMENT] = _evaluate_climax_placement(pacing_data)
        
    if PacingMetrics.BUILDUP_QUALITY in metrics:
        scores[PacingMetrics.BUILDUP_QUALITY] = _evaluate_buildup_quality(pacing_data)
        
    if PacingMetrics.RESOLUTION_PACING in metrics:
        scores[PacingMetrics.RESOLUTION_PACING] = _evaluate_resolution_pacing(pacing_data)
    
    # 计算总分
    if not scores:
        return 0.0
        
    overall_score = sum(scores.values()) / len(scores)
    
    # 记录评估结果
    logger.info(f"版本 {version.get('id', 'unknown')} 节奏控制评分: {overall_score:.2f}")
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
    
    # 如果版本包含节奏数据，创建一个包装字典返回
    if "pacing_data" in version:
        return {"pacing_data": version["pacing_data"]}
    
    # 返回空内容
    return {}

def _extract_pacing_data(content: Dict[str, Any]) -> Dict[str, Any]:
    """从内容中提取节奏数据
    
    Args:
        content: 版本内容
        
    Returns:
        节奏数据，包含场景长度、情感强度等信息
    """
    # 如果内容直接包含节奏数据，直接返回
    if "pacing_data" in content:
        return content["pacing_data"]
    
    # 构建节奏数据
    pacing_data = {
        "scene_durations": [],        # 场景持续时间列表
        "emotion_intensities": [],    # 情感强度列表
        "narrative_positions": [],    # 叙事位置列表（0-1）
        "scene_importance": [],       # 场景重要性
        "total_duration": 0,          # 总时长
        "climax_position": 0.7,       # 高潮位置（默认在70%处）
        "act_boundaries": [0.25, 0.75] # 分段边界（默认三段式）
    }
    
    # 如果内容包含场景列表，从场景中提取节奏数据
    if "scenes" in content:
        scenes = content["scenes"]
        total_duration = 0
        
        # 首先计算总时长
        for scene in scenes:
            duration = scene.get("duration", 60)  # 默认场景时长60秒
            total_duration += duration
        
        # 填充节奏数据
        accumulated_time = 0
        for scene in scenes:
            duration = scene.get("duration", 60)
            emotion_intensity = scene.get("emotion_intensity", 0.5)
            importance = scene.get("importance", 0.5)
            
            pacing_data["scene_durations"].append(duration)
            pacing_data["emotion_intensities"].append(emotion_intensity)
            
            # 计算场景在整体中的位置
            position = accumulated_time / total_duration if total_duration > 0 else 0
            pacing_data["narrative_positions"].append(position)
            pacing_data["scene_importance"].append(importance)
            
            accumulated_time += duration
        
        pacing_data["total_duration"] = total_duration
        
        # 找出情感强度最高的点作为高潮
        if pacing_data["emotion_intensities"]:
            max_intensity_index = pacing_data["emotion_intensities"].index(max(pacing_data["emotion_intensities"]))
            pacing_data["climax_position"] = pacing_data["narrative_positions"][max_intensity_index]
        
        return pacing_data
    
    # 如果没有足够信息，创建模拟数据
    # 模拟10个场景的节奏数据
    scene_count = 10
    for i in range(scene_count):
        position = i / (scene_count - 1)
        
        # 生成合理的场景长度分布
        # 开始和结束场景短，中间场景长，高潮场景中等
        if position < 0.2 or position > 0.9:
            duration = 30 + 30 * (0.5 - abs(position - 0.5))  # 30-45秒
        elif abs(position - 0.7) < 0.1:  # 高潮附近
            duration = 45 + 15 * (1 - abs(position - 0.7) * 10)  # 45-60秒
        else:
            duration = 60 + 30 * (0.5 - abs(position - 0.5))  # 60-75秒
        
        # 生成情感强度曲线
        # 开始低，中间逐渐上升，高潮最高，结尾降低
        if position < 0.6:
            intensity = 0.3 + position * 0.8
        elif position < 0.8:
            intensity = 0.8 + (position - 0.6) * 0.5
        else:
            intensity = 0.9 - (position - 0.8) * 2
        
        # 生成场景重要性
        # 高潮和结局场景重要性高
        if position > 0.6 and position < 0.8:  # 高潮
            importance = 0.8 + (position - 0.6) * 0.5
        elif position > 0.9:  # 结局
            importance = 0.9
        else:
            importance = 0.4 + position * 0.4
        
        pacing_data["scene_durations"].append(duration)
        pacing_data["emotion_intensities"].append(intensity)
        pacing_data["narrative_positions"].append(position)
        pacing_data["scene_importance"].append(importance)
    
    pacing_data["total_duration"] = sum(pacing_data["scene_durations"])
    
    return pacing_data

def _evaluate_scene_distribution(pacing_data: Dict[str, Any]) -> float:
    """评估场景长度分布
    
    检查场景长度分布是否合理，是否符合节奏需求
    
    Args:
        pacing_data: 节奏数据
        
    Returns:
        场景分布评分 (0.0-1.0)
    """
    durations = pacing_data.get("scene_durations", [])
    positions = pacing_data.get("narrative_positions", [])
    
    if not durations or not positions or len(durations) != len(positions):
        return 0.5
    
    # 计算场景长度的变异系数（标准差/平均值）
    # 变异系数应该适中，太大说明场景长度差异太大，太小说明节奏单调
    mean_duration = sum(durations) / len(durations)
    if mean_duration == 0:
        return 0.5
    
    try:
        std_dev = statistics.stdev(durations)
        cv = std_dev / mean_duration
    except (statistics.StatisticsError, ZeroDivisionError):
        return 0.5
    
    # 理想的变异系数在0.2-0.4之间
    if 0.2 <= cv <= 0.4:
        cv_score = 1.0
    elif cv < 0.2:
        cv_score = 1.0 - (0.2 - cv) * 5  # 低于0.2，分数线性下降
    else:  # cv > 0.4
        cv_score = 1.0 - (cv - 0.4) * 2  # 高于0.4，分数线性下降
    
    cv_score = max(0.0, min(1.0, cv_score))
    
    # 检查场景长度是否符合叙事位置
    position_scores = []
    for dur, pos in zip(durations, positions):
        # 开头和结尾应该较短，中间应该较长
        expected_duration = mean_duration * (1.0 + 0.5 * (0.5 - abs(pos - 0.5)))
        ratio = dur / expected_duration if expected_duration > 0 else 1.0
        ratio = min(2.0, max(0.5, ratio))  # 限制比例在0.5-2.0之间
        
        # 比例接近1.0得高分，偏离1.0扣分
        position_score = 1.0 - abs(ratio - 1.0)
        position_scores.append(position_score)
    
    avg_position_score = sum(position_scores) / len(position_scores) if position_scores else 0.5
    
    # 综合两个指标
    final_score = 0.6 * cv_score + 0.4 * avg_position_score
    
    return final_score

def _evaluate_rhythm_variation(pacing_data: Dict[str, Any]) -> float:
    """评估节奏变化
    
    检查节奏变化是否有足够的变化，是否有节奏感
    
    Args:
        pacing_data: 节奏数据
        
    Returns:
        节奏变化评分 (0.0-1.0)
    """
    durations = pacing_data.get("scene_durations", [])
    intensities = pacing_data.get("emotion_intensities", [])
    
    if not durations or len(durations) < 3:
        return 0.5
    
    # 计算场景长度的变化率
    duration_changes = []
    for i in range(1, len(durations)):
        change = abs(durations[i] - durations[i-1]) / durations[i-1] if durations[i-1] > 0 else 0
        duration_changes.append(change)
    
    # 变化率应该适中，既不要太大也不要太小
    avg_change = sum(duration_changes) / len(duration_changes) if duration_changes else 0
    
    # 理想的平均变化率在0.15-0.3之间
    if 0.15 <= avg_change <= 0.3:
        change_score = 1.0
    elif avg_change < 0.15:
        change_score = 1.0 - (0.15 - avg_change) * 6.67  # 低于0.15，分数线性下降
    else:  # avg_change > 0.3
        change_score = 1.0 - (avg_change - 0.3) * 2.5  # 高于0.3，分数线性下降
    
    change_score = max(0.0, min(1.0, change_score))
    
    # 如果有情感强度数据，评估情感和节奏的协调性
    if intensities and len(intensities) == len(durations):
        # 检查情感高点是否对应节奏变化
        coordination_scores = []
        for i in range(1, len(intensities)):
            intensity_change = abs(intensities[i] - intensities[i-1])
            duration_change = duration_changes[i-1] if i-1 < len(duration_changes) else 0
            
            # 大的情感变化应该对应大的节奏变化
            if intensity_change > 0.2:
                expected_duration_change = 0.25
                ratio = duration_change / expected_duration_change if expected_duration_change > 0 else 1.0
                ratio = min(2.0, max(0.5, ratio))
                coordination_score = 1.0 - abs(ratio - 1.0)
            else:
                coordination_score = 1.0
            
            coordination_scores.append(coordination_score)
        
        avg_coordination = sum(coordination_scores) / len(coordination_scores) if coordination_scores else 0.5
        
        # 综合两个指标
        final_score = 0.6 * change_score + 0.4 * avg_coordination
    else:
        final_score = change_score
    
    return final_score

def _evaluate_climax_placement(pacing_data: Dict[str, Any]) -> float:
    """评估高潮布局
    
    检查高潮是否放在合适的位置，是否有足够的戏剧性
    
    Args:
        pacing_data: 节奏数据
        
    Returns:
        高潮布局评分 (0.0-1.0)
    """
    climax_position = pacing_data.get("climax_position", 0.7)
    intensities = pacing_data.get("emotion_intensities", [])
    positions = pacing_data.get("narrative_positions", [])
    
    # 高潮位置应该在0.6-0.8之间
    if 0.6 <= climax_position <= 0.8:
        position_score = 1.0
    elif climax_position < 0.6:
        position_score = 1.0 - (0.6 - climax_position) * 2.5  # 低于0.6，分数线性下降
    else:  # climax_position > 0.8
        position_score = 1.0 - (climax_position - 0.8) * 5  # 高于0.8，分数线性下降
    
    position_score = max(0.0, min(1.0, position_score))
    
    # 如果有情感强度数据，评估高潮的强度
    if intensities and positions and len(intensities) == len(positions):
        # 找出高潮附近的情感强度
        climax_intensities = []
        for intensity, position in zip(intensities, positions):
            if abs(position - climax_position) < 0.1:
                climax_intensities.append(intensity)
        
        # 高潮处的情感强度应该高
        if climax_intensities:
            avg_climax_intensity = sum(climax_intensities) / len(climax_intensities)
            intensity_score = avg_climax_intensity
        else:
            intensity_score = 0.5
        
        # 综合两个指标
        final_score = 0.5 * position_score + 0.5 * intensity_score
    else:
        final_score = position_score
    
    return final_score

def _evaluate_buildup_quality(pacing_data: Dict[str, Any]) -> float:
    """评估铺垫质量
    
    检查高潮前的铺垫是否充分，是否有合理的递进
    
    Args:
        pacing_data: 节奏数据
        
    Returns:
        铺垫质量评分 (0.0-1.0)
    """
    climax_position = pacing_data.get("climax_position", 0.7)
    intensities = pacing_data.get("emotion_intensities", [])
    positions = pacing_data.get("narrative_positions", [])
    
    if not intensities or not positions or len(intensities) != len(positions):
        return 0.5
    
    # 高潮前的情感应该有递进
    buildup_intensities = []
    buildup_positions = []
    for intensity, position in zip(intensities, positions):
        if 0.2 <= position < climax_position:
            buildup_intensities.append(intensity)
            buildup_positions.append(position)
    
    if not buildup_intensities or len(buildup_intensities) < 3:
        return 0.5
    
    # 计算铺垫阶段的情感强度递增趋势
    buildup_trend = 0
    for i in range(1, len(buildup_intensities)):
        buildup_trend += buildup_intensities[i] - buildup_intensities[i-1]
    
    buildup_trend = buildup_trend / (len(buildup_intensities) - 1)
    
    # 铺垫阶段应该有正向趋势
    if buildup_trend > 0:
        trend_score = min(1.0, buildup_trend * 10)  # 趋势越强，分数越高
    else:
        trend_score = 0.0  # 没有正向趋势，得0分
    
    # 铺垫应该平稳上升，不应该有太大波动
    variations = []
    for i in range(1, len(buildup_intensities)):
        expected_increase = buildup_trend
        actual_increase = buildup_intensities[i] - buildup_intensities[i-1]
        variations.append(abs(actual_increase - expected_increase))
    
    avg_variation = sum(variations) / len(variations) if variations else 0
    
    # 平均变化应该小，变化越大越不稳定
    stability_score = 1.0 - min(1.0, avg_variation * 5)
    
    # 综合两个指标
    final_score = 0.7 * trend_score + 0.3 * stability_score
    
    return final_score

def _evaluate_resolution_pacing(pacing_data: Dict[str, Any]) -> float:
    """评估结局节奏
    
    检查结局部分的节奏是否合理，是否有足够的收尾
    
    Args:
        pacing_data: 节奏数据
        
    Returns:
        结局节奏评分 (0.0-1.0)
    """
    climax_position = pacing_data.get("climax_position", 0.7)
    durations = pacing_data.get("scene_durations", [])
    positions = pacing_data.get("narrative_positions", [])
    intensities = pacing_data.get("emotion_intensities", [])
    
    if not durations or not positions or not intensities or len(durations) != len(positions) or len(intensities) != len(positions):
        return 0.5
    
    # 结局部分的场景
    resolution_durations = []
    resolution_intensities = []
    for duration, position, intensity in zip(durations, positions, intensities):
        if position > climax_position:
            resolution_durations.append(duration)
            resolution_intensities.append(intensity)
    
    if not resolution_durations:
        return 0.3  # 没有结局，分数很低
    
    # 结局部分长度应该适中，不要太长也不要太短
    resolution_length = sum(resolution_durations)
    total_length = sum(durations)
    resolution_ratio = resolution_length / total_length if total_length > 0 else 0
    
    # 结局应该占总长度的15%-25%
    if 0.15 <= resolution_ratio <= 0.25:
        length_score = 1.0
    elif resolution_ratio < 0.15:
        length_score = 1.0 - (0.15 - resolution_ratio) * 6.67  # 低于0.15，分数线性下降
    else:  # resolution_ratio > 0.25
        length_score = 1.0 - (resolution_ratio - 0.25) * 4  # 高于0.25，分数线性下降
    
    length_score = max(0.0, min(1.0, length_score))
    
    # 结局部分的情感应该有递减趋势
    resolution_trend = 0
    for i in range(1, len(resolution_intensities)):
        resolution_trend += resolution_intensities[i] - resolution_intensities[i-1]
    
    resolution_trend = resolution_trend / len(resolution_intensities) if len(resolution_intensities) > 0 else 0
    
    # 结局应该有负向趋势（情感减弱）
    if resolution_trend < 0:
        trend_score = min(1.0, abs(resolution_trend) * 5)  # 趋势越强，分数越高
    else:
        trend_score = 0.3  # 没有负向趋势，得分低
    
    # 结局最后应该情感平缓
    final_intensity = resolution_intensities[-1] if resolution_intensities else 0
    if final_intensity < 0.4:
        final_score = 1.0
    else:
        final_score = 1.0 - (final_intensity - 0.4) * 1.67  # 高于0.4，分数线性下降
    
    final_score = max(0.0, min(1.0, final_score))
    
    # 综合各项指标
    overall_score = 0.4 * length_score + 0.4 * trend_score + 0.2 * final_score
    
    return overall_score

# 测试函数
def test_pacing_evaluator():
    """测试节奏控制评估器"""
    # 创建测试版本
    test_version = {
        "id": "test_version",
        "pacing_data": {
            "scene_durations": [30, 45, 60, 75, 60, 75, 60, 45, 30, 20],
            "emotion_intensities": [0.3, 0.4, 0.5, 0.6, 0.7, 0.9, 0.8, 0.6, 0.5, 0.3],
            "narrative_positions": [0.0, 0.1, 0.3, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 1.0],
            "scene_importance": [0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.8, 0.7, 0.6, 0.5],
            "total_duration": 500,
            "climax_position": 0.7,
            "act_boundaries": [0.25, 0.75]
        }
    }
    
    # 测试节奏控制评估
    score = evaluate_pacing(test_version)
    print(f"测试版本节奏控制评分: {score:.2f}")
    
    # 测试单项指标评估
    distribution_score = evaluate_pacing(test_version, [PacingMetrics.SCENE_DISTRIBUTION])
    print(f"场景分布评分: {distribution_score:.2f}")
    
    climax_score = evaluate_pacing(test_version, [PacingMetrics.CLIMAX_PLACEMENT])
    print(f"高潮布局评分: {climax_score:.2f}")

if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # 运行测试
    test_pacing_evaluator() 