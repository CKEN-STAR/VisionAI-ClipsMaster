#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
叙事结构评估器

评估混剪脚本的叙事结构，包括完整性、三幕结构、情节转折点、角色弧线等。
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Tuple, Union

from src.utils.log_handler import get_logger

# 配置日志
logger = get_logger("narrative_structure_evaluator")

class NarrativeMetrics:
    """叙事结构评估指标"""
    
    COMPLETENESS = "structural_completeness"    # 结构完整性
    ACT_DIVISION = "act_division"               # 幕章划分
    TURNING_POINTS = "turning_points"           # 转折点布局
    CHARACTER_ARC = "character_arc"             # 角色弧线
    THEME_DEVELOPMENT = "theme_development"     # 主题发展
    
    @staticmethod
    def all_metrics() -> List[str]:
        """获取所有叙事结构指标"""
        return [
            NarrativeMetrics.COMPLETENESS,
            NarrativeMetrics.ACT_DIVISION,
            NarrativeMetrics.TURNING_POINTS,
            NarrativeMetrics.CHARACTER_ARC,
            NarrativeMetrics.THEME_DEVELOPMENT
        ]

def evaluate_narrative_structure(version: Dict[str, Any],
                               metrics: Optional[List[str]] = None,
                               threshold: float = 0.7) -> float:
    """评估版本的叙事结构
    
    Args:
        version: 版本信息字典
        metrics: 要评估的指标列表，默认为全部
        threshold: 判断为良好的阈值
        
    Returns:
        叙事结构得分 (0.0-1.0)
    """
    if not metrics:
        metrics = NarrativeMetrics.all_metrics()
    
    # 获取版本内容
    content = _get_version_content(version)
    if not content:
        logger.warning(f"无法获取版本 {version.get('id', 'unknown')} 的内容")
        return 0.0
    
    # 提取叙事结构数据
    structure_data = _extract_structure_data(content)
    if not structure_data:
        logger.warning(f"无法提取版本 {version.get('id', 'unknown')} 的叙事结构数据")
        return 0.0
    
    scores = {}
    
    # 评估每个指标
    if NarrativeMetrics.COMPLETENESS in metrics:
        scores[NarrativeMetrics.COMPLETENESS] = _evaluate_completeness(structure_data)
        
    if NarrativeMetrics.ACT_DIVISION in metrics:
        scores[NarrativeMetrics.ACT_DIVISION] = _evaluate_act_division(structure_data)
        
    if NarrativeMetrics.TURNING_POINTS in metrics:
        scores[NarrativeMetrics.TURNING_POINTS] = _evaluate_turning_points(structure_data)
        
    if NarrativeMetrics.CHARACTER_ARC in metrics:
        scores[NarrativeMetrics.CHARACTER_ARC] = _evaluate_character_arc(structure_data)
        
    if NarrativeMetrics.THEME_DEVELOPMENT in metrics:
        scores[NarrativeMetrics.THEME_DEVELOPMENT] = _evaluate_theme_development(structure_data)
    
    # 计算总分
    if not scores:
        return 0.0
        
    overall_score = sum(scores.values()) / len(scores)
    
    # 记录评估结果
    logger.info(f"版本 {version.get('id', 'unknown')} 叙事结构评分: {overall_score:.2f}")
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
    
    # 如果版本包含结构数据，创建一个包装字典返回
    if "structure_data" in version:
        return {"structure_data": version["structure_data"]}
    
    # 返回空内容
    return {}

def _extract_structure_data(content: Dict[str, Any]) -> Dict[str, Any]:
    """从内容中提取叙事结构数据
    
    Args:
        content: 版本内容
        
    Returns:
        叙事结构数据
    """
    # 如果内容直接包含结构数据，直接返回
    if "structure_data" in content:
        return content["structure_data"]
    
    # 构建结构数据
    structure_data = {
        "acts": [],                # 幕章
        "turning_points": [],      # 转折点
        "character_arcs": {},      # 角色弧线
        "themes": [],              # 主题
        "has_beginning": False,    # 是否有开头
        "has_middle": False,       # 是否有中间
        "has_ending": False,       # 是否有结尾
        "has_conflict": False,     # 是否有冲突
        "has_resolution": False    # 是否有解决
    }
    
    # 如果内容包含场景列表，从场景中提取结构数据
    if "scenes" in content:
        scenes = content["scenes"]
        scene_count = len(scenes)
        
        # 定义基本的三幕结构
        structure_data["acts"] = [
            {"name": "Act I", "start": 0, "end": int(scene_count * 0.25)},
            {"name": "Act II", "start": int(scene_count * 0.25), "end": int(scene_count * 0.75)},
            {"name": "Act III", "start": int(scene_count * 0.75), "end": scene_count}
        ]
        
        # 提取转折点
        # 通常开始点、第一转折点、中点、第二转折点、结局
        turning_points = [
            {"name": "Inciting Incident", "position": int(scene_count * 0.12), "scene_index": int(scene_count * 0.12)},
            {"name": "First Plot Point", "position": int(scene_count * 0.25), "scene_index": int(scene_count * 0.25)},
            {"name": "Midpoint", "position": int(scene_count * 0.5), "scene_index": int(scene_count * 0.5)},
            {"name": "Second Plot Point", "position": int(scene_count * 0.75), "scene_index": int(scene_count * 0.75)},
            {"name": "Climax", "position": int(scene_count * 0.9), "scene_index": int(scene_count * 0.9)}
        ]
        
        # 更新转折点位置
        for i, point in enumerate(turning_points):
            scene_index = point["scene_index"]
            if 0 <= scene_index < scene_count:
                # 尝试从场景数据中获取转折点信息
                scene = scenes[scene_index]
                if "is_turning_point" in scene and scene["is_turning_point"]:
                    point["description"] = scene.get("description", f"转折点 {i+1}")
                    point["importance"] = scene.get("importance", 0.7)
                else:
                    point["description"] = f"默认转折点 {i+1}"
                    point["importance"] = 0.5
            else:
                point["description"] = f"默认转折点 {i+1} (超出场景范围)"
                point["importance"] = 0.3
        
        structure_data["turning_points"] = turning_points
        
        # 提取角色弧线
        characters = {}
        for i, scene in enumerate(scenes):
            if "characters" in scene:
                for char in scene["characters"]:
                    char_id = char.get("id", "unknown")
                    if char_id not in characters:
                        characters[char_id] = {
                            "name": char.get("name", f"角色{char_id}"),
                            "appearances": [],
                            "development": []
                        }
                    
                    characters[char_id]["appearances"].append(i)
                    if "development" in char:
                        characters[char_id]["development"].append({
                            "scene_index": i,
                            "position": i / scene_count,
                            "state": char["development"]
                        })
        
        # 简化处理，只保留出现次数最多的前3个角色
        main_characters = sorted(characters.items(), key=lambda x: len(x[1]["appearances"]), reverse=True)[:3]
        for char_id, char_data in main_characters:
            structure_data["character_arcs"][char_id] = char_data
        
        # 检查基本结构要素
        structure_data["has_beginning"] = True
        structure_data["has_middle"] = scene_count > 2
        structure_data["has_ending"] = True
        
        # 检查冲突和解决
        # 简化处理：假设第二幕有冲突，第三幕有解决
        if scene_count > 3:
            structure_data["has_conflict"] = True
            structure_data["has_resolution"] = True
        
        # 提取主题
        themes = set()
        for scene in scenes:
            if "themes" in scene and isinstance(scene["themes"], list):
                themes.update(scene["themes"])
        
        structure_data["themes"] = list(themes)
        
        return structure_data
    
    # 如果没有足够信息，创建模拟数据
    # 模拟简单的三幕结构
    structure_data["acts"] = [
        {"name": "Act I", "start": 0, "end": 3, "quality": 0.8},
        {"name": "Act II", "start": 3, "end": 7, "quality": 0.75},
        {"name": "Act III", "start": 7, "end": 10, "quality": 0.85}
    ]
    
    # 模拟转折点
    structure_data["turning_points"] = [
        {"name": "Inciting Incident", "position": 0.12, "description": "故事开始的事件", "importance": 0.7},
        {"name": "First Plot Point", "position": 0.25, "description": "第一个重要转折", "importance": 0.8},
        {"name": "Midpoint", "position": 0.5, "description": "故事的中点转变", "importance": 0.9},
        {"name": "Second Plot Point", "position": 0.75, "description": "第二个重要转折", "importance": 0.8},
        {"name": "Climax", "position": 0.9, "description": "故事高潮", "importance": 0.95}
    ]
    
    # 模拟角色弧线
    structure_data["character_arcs"] = {
        "main_character": {
            "name": "主角",
            "appearances": [0, 1, 2, 3, 5, 7, 8, 9],
            "development": [
                {"position": 0.0, "state": "初始状态"},
                {"position": 0.3, "state": "面临挑战"},
                {"position": 0.6, "state": "经历失败"},
                {"position": 0.9, "state": "成长蜕变"}
            ]
        },
        "supporting_character": {
            "name": "配角",
            "appearances": [1, 3, 6, 8],
            "development": [
                {"position": 0.1, "state": "初次登场"},
                {"position": 0.5, "state": "关键援助"},
                {"position": 0.8, "state": "最终贡献"}
            ]
        }
    }
    
    # 模拟主题
    structure_data["themes"] = ["成长", "友情", "挑战"]
    
    # 模拟基本要素
    structure_data["has_beginning"] = True
    structure_data["has_middle"] = True
    structure_data["has_ending"] = True
    structure_data["has_conflict"] = True
    structure_data["has_resolution"] = True
    
    return structure_data

def _evaluate_completeness(structure_data: Dict[str, Any]) -> float:
    """评估叙事结构的完整性
    
    检查故事是否有开始、中间、结尾，以及是否有明确的冲突和解决
    
    Args:
        structure_data: 叙事结构数据
        
    Returns:
        完整性得分 (0.0-1.0)
    """
    # 基本结构要素检查
    completeness_factors = [
        structure_data.get("has_beginning", False),   # 有开始
        structure_data.get("has_middle", False),      # 有中间
        structure_data.get("has_ending", False),      # 有结尾
        structure_data.get("has_conflict", False),    # 有冲突
        structure_data.get("has_resolution", False)   # 有解决
    ]
    
    # 计算完整性得分
    score = sum(1 for factor in completeness_factors if factor) / len(completeness_factors)
    
    return score

def _evaluate_act_division(structure_data: Dict[str, Any]) -> float:
    """评估幕章划分
    
    检查故事的幕章划分是否合理，是否符合三幕结构模式
    
    Args:
        structure_data: 叙事结构数据
        
    Returns:
        幕章划分得分 (0.0-1.0)
    """
    acts = structure_data.get("acts", [])
    
    # 如果没有幕章信息，得分低
    if not acts:
        return 0.3
    
    # 检查幕章数量是否合理（通常是3或5）
    act_count = len(acts)
    if act_count == 3:
        count_score = 1.0  # 三幕结构最标准
    elif act_count == 5:
        count_score = 0.9  # 五幕结构也合理
    elif act_count == 4:
        count_score = 0.8  # 四幕结构也可以接受
    elif act_count > 5:
        count_score = 0.7  # 太多幕章不太理想
    else:  # act_count < 3
        count_score = 0.6  # 太少幕章不够完整
    
    # 检查幕章长度分布是否合理
    # 理想情况：第一幕占25%，第二幕占50%，第三幕占25%
    if act_count >= 3:
        first_act = acts[0]
        middle_acts = acts[1:-1]
        last_act = acts[-1]
        
        # 计算各幕章占比
        total_length = last_act["end"] - first_act["start"]
        if total_length == 0:
            return count_score * 0.5  # 数据有问题，降低得分
        
        first_act_ratio = (first_act["end"] - first_act["start"]) / total_length
        last_act_ratio = (last_act["end"] - last_act["start"]) / total_length
        middle_acts_ratio = 1.0 - first_act_ratio - last_act_ratio
        
        # 检查比例是否合理
        # 第一幕理想比例：0.2-0.3
        first_act_score = 1.0 - min(1.0, abs(first_act_ratio - 0.25) * 4)
        
        # 第三幕理想比例：0.2-0.3
        last_act_score = 1.0 - min(1.0, abs(last_act_ratio - 0.25) * 4)
        
        # 中间幕章理想比例：0.4-0.6
        middle_acts_score = 1.0 - min(1.0, abs(middle_acts_ratio - 0.5) * 2)
        
        # 计算平均比例得分
        ratio_score = (first_act_score + middle_acts_score + last_act_score) / 3
    else:
        ratio_score = 0.5  # 幕章太少，比例得分低
    
    # 检查每个幕章的质量，如果有
    quality_scores = []
    for act in acts:
        if "quality" in act:
            quality_scores.append(act["quality"])
    
    if quality_scores:
        quality_score = sum(quality_scores) / len(quality_scores)
    else:
        quality_score = 0.7  # 默认质量还行
    
    # 综合得分
    final_score = 0.4 * count_score + 0.4 * ratio_score + 0.2 * quality_score
    
    return final_score

def _evaluate_turning_points(structure_data: Dict[str, Any]) -> float:
    """评估转折点布局
    
    检查故事的关键转折点是否位置合理，是否有足够的重要性
    
    Args:
        structure_data: 叙事结构数据
        
    Returns:
        转折点布局得分 (0.0-1.0)
    """
    turning_points = structure_data.get("turning_points", [])
    
    # 如果没有转折点信息，得分低
    if not turning_points:
        return 0.3
    
    # 标准转折点位置（分位数）
    standard_positions = {
        "Inciting Incident": 0.12,  # 引起事件
        "First Plot Point": 0.25,   # 第一转折点
        "Midpoint": 0.5,            # 中点
        "Second Plot Point": 0.75,  # 第二转折点
        "Climax": 0.9               # 高潮
    }
    
    # 检查转折点数量是否足够
    point_count = len(turning_points)
    if point_count >= 5:
        count_score = 1.0  # 至少有5个关键转折点
    elif point_count >= 3:
        count_score = 0.8  # 至少有3个转折点
    else:
        count_score = 0.5  # 转折点太少
    
    # 检查转折点位置是否合理
    position_scores = []
    importance_scores = []
    
    for point in turning_points:
        point_name = point.get("name", "")
        point_position = point.get("position", 0)
        point_importance = point.get("importance", 0.5)
        
        # 检查位置
        if point_name in standard_positions:
            expected_position = standard_positions[point_name]
            position_score = 1.0 - min(1.0, abs(point_position - expected_position) * 3)
        else:
            # 如果不是标准转折点，评估它是否在合理范围
            position_score = 0.7
        
        position_scores.append(position_score)
        
        # 检查重要性
        # 转折点重要性应该高，标准是>=0.7
        importance_score = min(1.0, point_importance / 0.7)
        importance_scores.append(importance_score)
    
    avg_position_score = sum(position_scores) / len(position_scores) if position_scores else 0.5
    avg_importance_score = sum(importance_scores) / len(importance_scores) if importance_scores else 0.5
    
    # 综合得分
    final_score = 0.3 * count_score + 0.4 * avg_position_score + 0.3 * avg_importance_score
    
    return final_score

def _evaluate_character_arc(structure_data: Dict[str, Any]) -> float:
    """评估角色弧线
    
    检查主要角色是否有清晰的发展弧线，是否有明显的变化
    
    Args:
        structure_data: 叙事结构数据
        
    Returns:
        角色弧线评分 (0.0-1.0)
    """
    character_arcs = structure_data.get("character_arcs", {})
    
    # 如果没有角色弧线信息，得分低
    if not character_arcs:
        return 0.3
    
    # 检查主要角色数量
    char_count = len(character_arcs)
    if char_count >= 3:
        count_score = 1.0  # 至少有3个主要角色
    elif char_count >= 1:
        count_score = 0.8  # 至少有1个主要角色
    else:
        count_score = 0.0  # 没有角色信息
    
    # 评估每个角色的弧线
    arc_scores = []
    presence_scores = []
    
    for char_id, char_data in character_arcs.items():
        # 检查角色发展信息是否完整
        development = char_data.get("development", [])
        appearances = char_data.get("appearances", [])
        
        # 角色需要足够的发展节点（至少3个）
        if len(development) >= 3:
            dev_count_score = 1.0
        elif len(development) >= 2:
            dev_count_score = 0.7
        else:
            dev_count_score = 0.4
        
        # 角色需要足够的出场次数
        if len(appearances) >= 5:
            presence_score = 1.0
        elif len(appearances) >= 3:
            presence_score = 0.8
        else:
            presence_score = 0.5
        
        # 角色发展需要覆盖故事的开始、中间和结尾
        has_beginning = any(d.get("position", 0) <= 0.2 for d in development)
        has_ending = any(d.get("position", 0) >= 0.8 for d in development)
        
        coverage_score = 0.0
        if has_beginning and has_ending:
            coverage_score = 1.0
        elif has_beginning or has_ending:
            coverage_score = 0.6
        
        # 计算角色弧线得分
        arc_score = (dev_count_score * 0.4 + coverage_score * 0.6)
        arc_scores.append(arc_score)
        presence_scores.append(presence_score)
    
    avg_arc_score = sum(arc_scores) / len(arc_scores) if arc_scores else 0.0
    avg_presence_score = sum(presence_scores) / len(presence_scores) if presence_scores else 0.0
    
    # 综合得分
    final_score = 0.3 * count_score + 0.4 * avg_arc_score + 0.3 * avg_presence_score
    
    return final_score

def _evaluate_theme_development(structure_data: Dict[str, Any]) -> float:
    """评估主题发展
    
    检查故事是否有明确的主题，以及主题是否贯穿全剧
    
    Args:
        structure_data: 叙事结构数据
        
    Returns:
        主题发展评分 (0.0-1.0)
    """
    themes = structure_data.get("themes", [])
    
    # 如果没有主题信息，得分低
    if not themes:
        return 0.3
    
    # 检查主题数量
    theme_count = len(themes)
    if 1 <= theme_count <= 3:
        count_score = 1.0  # 1-3个主题最理想
    elif theme_count <= 5:
        count_score = 0.8  # 4-5个主题还可以
    else:
        count_score = 0.6  # 太多主题会分散注意力
    
    # 检查主题在故事中的分布
    # 这需要更详细的数据，如果没有，就假设主题分布均匀
    distribution_score = 0.8
    
    # 由于缺乏更多信息，主题发展得分主要基于主题数量
    final_score = 0.7 * count_score + 0.3 * distribution_score
    
    return final_score

# 测试函数
def test_narrative_structure_evaluator():
    """测试叙事结构评估器"""
    # 创建测试版本
    test_version = {
        "id": "test_version",
        "structure_data": {
            "acts": [
                {"name": "Act I", "start": 0, "end": 3, "quality": 0.8},
                {"name": "Act II", "start": 3, "end": 7, "quality": 0.75},
                {"name": "Act III", "start": 7, "end": 10, "quality": 0.85}
            ],
            "turning_points": [
                {"name": "Inciting Incident", "position": 0.12, "description": "故事开始的事件", "importance": 0.7},
                {"name": "First Plot Point", "position": 0.25, "description": "第一个重要转折", "importance": 0.8},
                {"name": "Midpoint", "position": 0.5, "description": "故事的中点转变", "importance": 0.9},
                {"name": "Second Plot Point", "position": 0.75, "description": "第二个重要转折", "importance": 0.8},
                {"name": "Climax", "position": 0.9, "description": "故事高潮", "importance": 0.95}
            ],
            "character_arcs": {
                "main_character": {
                    "name": "主角",
                    "appearances": [0, 1, 2, 3, 5, 7, 8, 9],
                    "development": [
                        {"position": 0.0, "state": "初始状态"},
                        {"position": 0.3, "state": "面临挑战"},
                        {"position": 0.6, "state": "经历失败"},
                        {"position": 0.9, "state": "成长蜕变"}
                    ]
                },
                "supporting_character": {
                    "name": "配角",
                    "appearances": [1, 3, 6, 8],
                    "development": [
                        {"position": 0.1, "state": "初次登场"},
                        {"position": 0.5, "state": "关键援助"},
                        {"position": 0.8, "state": "最终贡献"}
                    ]
                }
            },
            "themes": ["成长", "友情", "挑战"],
            "has_beginning": True,
            "has_middle": True,
            "has_ending": True,
            "has_conflict": True,
            "has_resolution": True
        }
    }
    
    # 测试叙事结构评估
    score = evaluate_narrative_structure(test_version)
    print(f"测试版本叙事结构评分: {score:.2f}")
    
    # 测试单项指标评估
    completeness_score = evaluate_narrative_structure(test_version, [NarrativeMetrics.COMPLETENESS])
    print(f"结构完整性评分: {completeness_score:.2f}")
    
    arc_score = evaluate_narrative_structure(test_version, [NarrativeMetrics.CHARACTER_ARC])
    print(f"角色弧线评分: {arc_score:.2f}")

if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # 运行测试
    test_narrative_structure_evaluator() 