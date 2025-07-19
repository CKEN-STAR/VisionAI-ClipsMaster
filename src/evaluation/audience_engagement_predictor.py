#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
观众参与度预测器

预测混剪内容对观众的吸引力和参与度，评估内容的潜在传播力。
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Tuple, Union

from src.utils.log_handler import get_logger

# 配置日志
logger = get_logger("audience_engagement_predictor")

class EngagementFactors:
    """参与度影响因素"""
    
    EMOTIONAL_IMPACT = "emotional_impact"      # 情感冲击力
    NARRATIVE_CLARITY = "narrative_clarity"    # 叙事清晰度
    PACING_QUALITY = "pacing_quality"          # 节奏质量
    RELATABILITY = "relatability"              # 共鸣度
    NOVELTY = "novelty"                        # 新颖度
    
    @staticmethod
    def all_factors() -> List[str]:
        """获取所有参与度因素"""
        return [
            EngagementFactors.EMOTIONAL_IMPACT,
            EngagementFactors.NARRATIVE_CLARITY,
            EngagementFactors.PACING_QUALITY,
            EngagementFactors.RELATABILITY,
            EngagementFactors.NOVELTY
        ]

def predict_engagement_score(version: Dict[str, Any],
                           factors: Optional[List[str]] = None,
                           threshold: float = 0.7) -> float:
    """预测观众参与度得分
    
    Args:
        version: 版本信息字典
        factors: 要评估的因素列表，默认为全部
        threshold: 判断为高参与度的阈值
        
    Returns:
        参与度得分 (0.0-1.0)
    """
    if not factors:
        factors = EngagementFactors.all_factors()
    
    # 获取版本内容
    content = _get_version_content(version)
    if not content:
        logger.warning(f"无法获取版本 {version.get('id', 'unknown')} 的内容")
        return 0.0
    
    scores = {}
    
    # 评估每个因素
    if EngagementFactors.EMOTIONAL_IMPACT in factors:
        scores[EngagementFactors.EMOTIONAL_IMPACT] = _evaluate_emotional_impact(content)
        
    if EngagementFactors.NARRATIVE_CLARITY in factors:
        scores[EngagementFactors.NARRATIVE_CLARITY] = _evaluate_narrative_clarity(content)
        
    if EngagementFactors.PACING_QUALITY in factors:
        scores[EngagementFactors.PACING_QUALITY] = _evaluate_pacing_quality(content)
        
    if EngagementFactors.RELATABILITY in factors:
        scores[EngagementFactors.RELATABILITY] = _evaluate_relatability(content)
        
    if EngagementFactors.NOVELTY in factors:
        scores[EngagementFactors.NOVELTY] = _evaluate_novelty(content)
    
    # 计算总分，加权计算
    if not scores:
        return 0.0
    
    # 因素权重
    weights = {
        EngagementFactors.EMOTIONAL_IMPACT: 0.3,   # 情感冲击最重要
        EngagementFactors.NARRATIVE_CLARITY: 0.2,  # 叙事清晰度次之
        EngagementFactors.PACING_QUALITY: 0.2,     # 节奏质量同等重要
        EngagementFactors.RELATABILITY: 0.15,      # 共鸣度
        EngagementFactors.NOVELTY: 0.15            # 新颖度
    }
    
    weighted_sum = 0.0
    total_weight = 0.0
    
    for factor, score in scores.items():
        weight = weights.get(factor, 1.0)
        weighted_sum += score * weight
        total_weight += weight
    
    overall_score = weighted_sum / total_weight if total_weight > 0 else 0.0
    
    # 记录评估结果
    logger.info(f"版本 {version.get('id', 'unknown')} 参与度预测得分: {overall_score:.2f}")
    for factor, score in scores.items():
        logger.debug(f"  - {factor}: {score:.2f}")
    
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
    
    # 如果版本包含参与度数据，创建一个包装字典返回
    if "engagement_data" in version:
        return {"engagement_data": version["engagement_data"]}
    
    # 返回空内容
    return {}

def _evaluate_emotional_impact(content: Dict[str, Any]) -> float:
    """评估情感冲击力
    
    检查内容是否能引起强烈的情感反应
    
    Args:
        content: 版本内容
        
    Returns:
        情感冲击力得分 (0.0-1.0)
    """
    # 在实际产品中，这里应该实现更复杂的情感分析
    # 这里使用模拟实现
    
    # 如果有情感强度数据，直接使用
    if "emotion_intensities" in content:
        intensities = content["emotion_intensities"]
        if intensities:
            # 情感波动越大，冲击力越强
            max_intensity = max(intensities)
            min_intensity = min(intensities)
            range_score = max_intensity - min_intensity
            
            # 情感高点越高，冲击力越强
            peak_score = max_intensity
            
            # 综合得分
            return 0.6 * peak_score + 0.4 * range_score
    
    # 如果有情感曲线数据，提取情感强度
    if "emotion_curve" in content:
        curve = content["emotion_curve"]
        if curve:
            intensities = [point.get("intensity", 0.5) for point in curve]
            if intensities:
                max_intensity = max(intensities)
                min_intensity = min(intensities)
                range_score = max_intensity - min_intensity
                peak_score = max_intensity
                
                return 0.6 * peak_score + 0.4 * range_score
    
    # 如果有情感分析数据，直接使用
    if "emotional_impact" in content:
        return content["emotional_impact"]
    
    # 默认中等偏上的情感冲击力
    return 0.7

def _evaluate_narrative_clarity(content: Dict[str, Any]) -> float:
    """评估叙事清晰度
    
    检查故事是否容易理解，是否有清晰的脉络
    
    Args:
        content: 版本内容
        
    Returns:
        叙事清晰度得分 (0.0-1.0)
    """
    # 在实际产品中，这里应该实现更复杂的叙事结构分析
    # 这里使用模拟实现
    
    # 如果有叙事清晰度数据，直接使用
    if "narrative_clarity" in content:
        return content["narrative_clarity"]
    
    # 根据结构完整性估计叙事清晰度
    if "structure_data" in content:
        structure = content["structure_data"]
        
        # 检查基本结构要素
        completeness_factors = [
            structure.get("has_beginning", False),  # 有开始
            structure.get("has_middle", False),     # 有中间
            structure.get("has_ending", False),     # 有结尾
            structure.get("has_conflict", False),   # 有冲突
            structure.get("has_resolution", False)  # 有解决
        ]
        
        completeness_score = sum(1 for factor in completeness_factors if factor) / len(completeness_factors)
        
        # 检查转折点是否清晰
        turning_points = structure.get("turning_points", [])
        if turning_points:
            turning_points_score = min(1.0, len(turning_points) / 5)
        else:
            turning_points_score = 0.5
        
        return 0.7 * completeness_score + 0.3 * turning_points_score
    
    # 默认中等的叙事清晰度
    return 0.65

def _evaluate_pacing_quality(content: Dict[str, Any]) -> float:
    """评估节奏质量
    
    检查内容的节奏是否吸引人，是否有良好的张驰
    
    Args:
        content: 版本内容
        
    Returns:
        节奏质量得分 (0.0-1.0)
    """
    # 在实际产品中，这里应该实现更复杂的节奏分析
    # 这里使用模拟实现
    
    # 如果有节奏质量数据，直接使用
    if "pacing_quality" in content:
        return content["pacing_quality"]
    
    # 如果有节奏数据，分析节奏变化
    if "pacing_data" in content:
        pacing_data = content["pacing_data"]
        
        durations = pacing_data.get("scene_durations", [])
        if durations:
            # 计算场景长度的变异系数
            mean_duration = sum(durations) / len(durations) if durations else 0
            if mean_duration > 0:
                variance = sum((d - mean_duration) ** 2 for d in durations) / len(durations)
                std_dev = variance ** 0.5
                cv = std_dev / mean_duration
                
                # 变异系数在0.2-0.4之间最理想
                if 0.2 <= cv <= 0.4:
                    return 0.9
                elif cv < 0.2:
                    return 0.7  # 节奏过于平缓
                else:  # cv > 0.4
                    return 0.6  # 节奏变化过大
    
    # 默认中等的节奏质量
    return 0.6

def _evaluate_relatability(content: Dict[str, Any]) -> float:
    """评估共鸣度
    
    检查内容是否能引起观众的共鸣，是否贴近生活
    
    Args:
        content: 版本内容
        
    Returns:
        共鸣度得分 (0.0-1.0)
    """
    # 在实际产品中，这里应该实现更复杂的共鸣度分析
    # 这里使用模拟实现
    
    # 如果有共鸣度数据，直接使用
    if "relatability" in content:
        return content["relatability"]
    
    # 如果有主题数据，检查主题的普遍性
    if "structure_data" in content and "themes" in content["structure_data"]:
        themes = content["structure_data"]["themes"]
        
        # 常见的高共鸣主题
        high_relatability_themes = ["爱情", "友情", "家庭", "成长", "奋斗", "挑战", "梦想"]
        
        # 计算主题共鸣度
        relatability_count = sum(1 for theme in themes if theme in high_relatability_themes)
        theme_score = min(1.0, relatability_count / 3)  # 至少3个高共鸣主题得满分
        
        return 0.6 + 0.3 * theme_score  # 基础分0.6，主题加分最多0.3
    
    # 默认中等的共鸣度
    return 0.6

def _evaluate_novelty(content: Dict[str, Any]) -> float:
    """评估新颖度
    
    检查内容是否有创新点，是否能给观众带来新鲜感
    
    Args:
        content: 版本内容
        
    Returns:
        新颖度得分 (0.0-1.0)
    """
    # 在实际产品中，这里应该实现更复杂的新颖度分析
    # 这里使用模拟实现
    
    # 如果有新颖度数据，直接使用
    if "novelty" in content:
        return content["novelty"]
    
    # 如果有叙事结构数据，检查是否有非传统的结构
    if "structure_data" in content:
        structure = content["structure_data"]
        
        # 检查转折点布局是否新颖
        turning_points = structure.get("turning_points", [])
        if turning_points:
            # 标准转折点位置
            standard_positions = [0.12, 0.25, 0.5, 0.75, 0.9]
            
            # 计算平均偏离度
            deviations = []
            for point in turning_points:
                position = point.get("position", 0)
                # 找到最近的标准位置
                min_deviation = min(abs(position - std_pos) for std_pos in standard_positions)
                deviations.append(min_deviation)
            
            avg_deviation = sum(deviations) / len(deviations) if deviations else 0
            
            # 偏离得适度，太小表示太传统，太大表示太混乱
            if 0.05 <= avg_deviation <= 0.15:
                return 0.8  # 适度新颖
            elif avg_deviation < 0.05:
                return 0.5  # 太传统
            else:  # avg_deviation > 0.15
                return 0.6  # 太混乱，新颖但可能降低理解度
    
    # 默认中等的新颖度
    return 0.55

# 测试函数
def test_engagement_predictor():
    """测试观众参与度预测器"""
    # 创建测试版本
    test_version = {
        "id": "test_version",
        "engagement_data": {
            "emotional_impact": 0.85,
            "narrative_clarity": 0.75,
            "pacing_quality": 0.8,
            "relatability": 0.7,
            "novelty": 0.65
        }
    }
    
    # 测试参与度预测
    score = predict_engagement_score(test_version)
    print(f"测试版本参与度预测得分: {score:.2f}")
    
    # 测试单项因素评估
    emotional_score = predict_engagement_score(test_version, [EngagementFactors.EMOTIONAL_IMPACT])
    print(f"情感冲击力得分: {emotional_score:.2f}")
    
    novelty_score = predict_engagement_score(test_version, [EngagementFactors.NOVELTY])
    print(f"新颖度得分: {novelty_score:.2f}")

if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # 运行测试
    test_engagement_predictor() 