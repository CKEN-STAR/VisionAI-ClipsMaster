#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
叙事连贯性检查器

评估混剪脚本的叙事连贯性，包括情节逻辑、角色行为一致性、对话衔接等方面。
"""

import os
import re
import json
import logging
from typing import Dict, List, Any, Optional, Tuple, Union
from collections import Counter

from src.utils.log_handler import get_logger

# 配置日志
logger = get_logger("coherence_checker")

class CoherenceMetrics:
    """连贯性评估指标"""
    
    CHARACTER_CONSISTENCY = "character_consistency"  # 角色行为一致性
    PLOT_LOGIC = "plot_logic"                        # 情节逻辑性
    DIALOGUE_FLOW = "dialogue_flow"                  # 对话流畅性
    TIME_CONTINUITY = "time_continuity"              # 时间连续性
    SCENE_TRANSITIONS = "scene_transitions"          # 场景转换自然度
    
    @staticmethod
    def all_metrics() -> List[str]:
        """获取所有连贯性指标"""
        return [
            CoherenceMetrics.CHARACTER_CONSISTENCY,
            CoherenceMetrics.PLOT_LOGIC,
            CoherenceMetrics.DIALOGUE_FLOW,
            CoherenceMetrics.TIME_CONTINUITY,
            CoherenceMetrics.SCENE_TRANSITIONS
        ]

def check_coherence(version: Dict[str, Any], 
                   metrics: Optional[List[str]] = None,
                   threshold: float = 0.7) -> float:
    """检查版本的叙事连贯性
    
    Args:
        version: 版本信息字典
        metrics: 要检查的指标列表，默认为全部
        threshold: 判断为连贯的阈值
        
    Returns:
        连贯性得分 (0.0-1.0)
    """
    if not metrics:
        metrics = CoherenceMetrics.all_metrics()
    
    # 获取版本内容
    content = _get_version_content(version)
    if not content:
        logger.warning(f"无法获取版本 {version.get('id', 'unknown')} 的内容")
        return 0.0
    
    scores = {}
    
    # 评估每个指标
    if CoherenceMetrics.CHARACTER_CONSISTENCY in metrics:
        scores[CoherenceMetrics.CHARACTER_CONSISTENCY] = _evaluate_character_consistency(content)
        
    if CoherenceMetrics.PLOT_LOGIC in metrics:
        scores[CoherenceMetrics.PLOT_LOGIC] = _evaluate_plot_logic(content)
        
    if CoherenceMetrics.DIALOGUE_FLOW in metrics:
        scores[CoherenceMetrics.DIALOGUE_FLOW] = _evaluate_dialogue_flow(content)
        
    if CoherenceMetrics.TIME_CONTINUITY in metrics:
        scores[CoherenceMetrics.TIME_CONTINUITY] = _evaluate_time_continuity(content)
        
    if CoherenceMetrics.SCENE_TRANSITIONS in metrics:
        scores[CoherenceMetrics.SCENE_TRANSITIONS] = _evaluate_scene_transitions(content)
    
    # 计算总分
    if not scores:
        return 0.0
        
    overall_score = sum(scores.values()) / len(scores)
    
    # 记录评估结果
    logger.info(f"版本 {version.get('id', 'unknown')} 连贯性评分: {overall_score:.2f}")
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
    
    # 返回空内容
    return {}

def _evaluate_character_consistency(content: Dict[str, Any]) -> float:
    """评估角色行为一致性
    
    检查角色在整个故事中的行为、说话方式、动机等是否一致
    
    Args:
        content: 版本内容
        
    Returns:
        角色一致性得分 (0.0-1.0)
    """
    # 在实际产品中，这里需要实现真正的角色一致性检查逻辑
    # 这里使用模拟实现，假设角色一致性得分为0.8
    
    # 如果有真实数据，可以实现如下逻辑：
    # 1. 提取所有角色
    # 2. 分析每个角色的行为和对话
    # 3. 检查角色在不同场景中的行为是否一致
    # 4. 根据一致性程度给出分数
    
    return 0.85

def _evaluate_plot_logic(content: Dict[str, Any]) -> float:
    """评估情节逻辑性
    
    检查故事情节是否合理、因果关系是否清晰
    
    Args:
        content: 版本内容
        
    Returns:
        情节逻辑得分 (0.0-1.0)
    """
    # 在实际产品中，这里需要实现真正的情节逻辑性检查
    # 这里使用模拟实现，假设情节逻辑得分为0.75
    
    # 如果有真实数据，可以实现如下逻辑：
    # 1. 提取故事的主要情节点
    # 2. 分析情节点之间的因果关系
    # 3. 检查是否有逻辑断裂
    # 4. 根据逻辑连贯程度给出分数
    
    return 0.78

def _evaluate_dialogue_flow(content: Dict[str, Any]) -> float:
    """评估对话流畅性
    
    检查对话是否自然流畅，是否有逻辑断裂
    
    Args:
        content: 版本内容
        
    Returns:
        对话流畅性得分 (0.0-1.0)
    """
    # 在实际产品中，这里需要实现真正的对话流畅性检查
    # 这里使用模拟实现，假设对话流畅性得分为0.9
    
    # 如果有真实数据，可以实现如下逻辑：
    # 1. 提取所有对话
    # 2. 分析对话的上下文连贯性
    # 3. 检查对话衔接是否自然
    # 4. 根据流畅程度给出分数
    
    return 0.82

def _evaluate_time_continuity(content: Dict[str, Any]) -> float:
    """评估时间连续性
    
    检查故事中的时间线是否连贯，是否有时间矛盾
    
    Args:
        content: 版本内容
        
    Returns:
        时间连续性得分 (0.0-1.0)
    """
    # 在实际产品中，这里需要实现真正的时间连续性检查
    # 这里使用模拟实现，假设时间连续性得分为0.85
    
    # 如果有真实数据，可以实现如下逻辑：
    # 1. 提取故事中的时间标记
    # 2. 分析时间的前后关系
    # 3. 检查是否有时间矛盾
    # 4. 根据时间连贯程度给出分数
    
    return 0.80

def _evaluate_scene_transitions(content: Dict[str, Any]) -> float:
    """评估场景转换自然度
    
    检查场景之间的过渡是否自然，是否有突兀感
    
    Args:
        content: 版本内容
        
    Returns:
        场景转换自然度得分 (0.0-1.0)
    """
    # 在实际产品中，这里需要实现真正的场景转换自然度检查
    # 这里使用模拟实现，假设场景转换自然度得分为0.7
    
    # 如果有真实数据，可以实现如下逻辑：
    # 1. 提取故事中的场景转换
    # 2. 分析场景转换的连贯性
    # 3. 检查场景转换是否自然
    # 4. 根据自然程度给出分数
    
    return 0.75

# 测试函数
def test_coherence_checker():
    """测试连贯性检查器"""
    # 创建测试版本
    test_version = {
        "id": "test_version",
        "content": {
            "scenes": [
                {"id": "scene1", "description": "主角在家中醒来"},
                {"id": "scene2", "description": "主角出门上班"},
                {"id": "scene3", "description": "主角在办公室工作"}
            ],
            "characters": [
                {"id": "char1", "name": "主角", "traits": ["勤奋", "聪明"]}
            ],
            "dialogues": [
                {"scene_id": "scene1", "character_id": "char1", "text": "又是新的一天。"},
                {"scene_id": "scene2", "character_id": "char1", "text": "今天要努力工作。"},
                {"scene_id": "scene3", "character_id": "char1", "text": "终于完成了工作。"}
            ]
        }
    }
    
    # 测试连贯性检查
    score = check_coherence(test_version)
    print(f"测试版本连贯性得分: {score:.2f}")
    
    # 测试单项指标检查
    character_score = check_coherence(test_version, [CoherenceMetrics.CHARACTER_CONSISTENCY])
    print(f"角色一致性得分: {character_score:.2f}")

if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # 运行测试
    test_coherence_checker() 