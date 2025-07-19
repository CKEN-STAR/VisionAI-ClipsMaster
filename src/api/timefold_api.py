"""
时空折叠引擎API

提供时空折叠引擎的REST API接口
"""

from typing import Dict, List, Any, Optional
import logging

from src.nonlinear.time_folder import (
    TimeFolder, fold_timeline, FoldingMode, 
    get_folding_strategy, list_folding_strategies
)
from src.narrative.anchor_types import AnchorInfo
from src.narrative.anchor_detector import detect_anchors

# 创建日志记录器
logger = logging.getLogger("timefold_api")


def fold_scenes(scenes: List[Dict[str, Any]], 
               anchors: Optional[List[AnchorInfo]] = None,
               structure_name: Optional[str] = None,
               strategy_name: Optional[str] = None,
               folding_mode: Optional[str] = None) -> Dict[str, Any]:
    """
    折叠场景时间轴
    
    Args:
        scenes: 场景列表
        anchors: 锚点列表，可选。如果为None，则自动检测
        structure_name: 叙事结构名称，可选
        strategy_name: 折叠策略名称，可选
        folding_mode: 折叠模式名称，可选
        
    Returns:
        折叠结果字典
    """
    try:
        # 如果没有提供锚点，则自动检测
        if not anchors:
            anchors = detect_anchors(scenes)
        
        # 创建时空折叠引擎
        folder = TimeFolder()
        
        # 映射折叠模式
        mode = None
        if folding_mode:
            mode_map = {
                "preserve_anchors": FoldingMode.PRESERVE_ANCHORS,
                "condense_similar": FoldingMode.CONDENSE_SIMILAR,
                "highlight_contrast": FoldingMode.HIGHLIGHT_CONTRAST,
                "narrative_driven": FoldingMode.NARRATIVE_DRIVEN
            }
            mode = mode_map.get(folding_mode)
        
        # 执行折叠
        folded_scenes = folder.fold_timeline(
            scenes, anchors, structure_name, strategy_name, mode
        )
        
        # 获取使用的策略
        used_strategy = folder._get_strategy_for_structure(
            structure_name or folder.config.get("default_structure", "倒叙风暴"),
            strategy_name
        )
        
        # 创建响应
        response = {
            "success": True,
            "original_count": len(scenes),
            "folded_count": len(folded_scenes),
            "reduction_ratio": (1 - len(folded_scenes) / len(scenes)) if scenes else 0,
            "structure_name": structure_name or folder.config.get("default_structure", "倒叙风暴"),
            "strategy_name": used_strategy.name,
            "folding_mode": folding_mode or "preserve_anchors",
            "anchors_count": len(anchors),
            "folded_scenes": folded_scenes
        }
        
        return response
        
    except Exception as e:
        logger.error(f"折叠场景失败: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


def get_folding_strategies_info() -> Dict[str, Any]:
    """
    获取所有折叠策略信息
    
    Returns:
        策略信息字典
    """
    try:
        # 创建时空折叠引擎
        folder = TimeFolder()
        
        # 获取所有策略
        strategies = folder.get_available_strategies()
        
        # 创建响应
        response = {
            "success": True,
            "strategies_count": len(strategies),
            "strategies": strategies
        }
        
        return response
        
    except Exception as e:
        logger.error(f"获取折叠策略失败: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


def get_folding_modes_info() -> Dict[str, Any]:
    """
    获取所有折叠模式信息
    
    Returns:
        模式信息字典
    """
    try:
        # 定义模式信息
        modes = {
            "preserve_anchors": {
                "name": "preserve_anchors",
                "description": "保留关键锚点的折叠方法，压缩非关键场景",
                "suitable_for": ["所有类型的内容"]
            },
            "condense_similar": {
                "name": "condense_similar",
                "description": "压缩相似场景的折叠方法",
                "suitable_for": ["节奏缓慢的内容", "场景重复的内容"]
            },
            "highlight_contrast": {
                "name": "highlight_contrast",
                "description": "强调情感对比的折叠方法",
                "suitable_for": ["情感起伏较大的内容", "戏剧性内容"]
            },
            "narrative_driven": {
                "name": "narrative_driven",
                "description": "基于叙事结构的折叠方法",
                "suitable_for": ["复杂叙事", "非线性叙事"]
            }
        }
        
        # 创建响应
        response = {
            "success": True,
            "modes_count": len(modes),
            "modes": list(modes.values())
        }
        
        return response
        
    except Exception as e:
        logger.error(f"获取折叠模式失败: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


def estimate_folding_result(scenes: List[Dict[str, Any]], 
                          structure_name: Optional[str] = None,
                          folding_mode: Optional[str] = None) -> Dict[str, Any]:
    """
    估算折叠结果，不执行实际折叠
    
    Args:
        scenes: 场景列表
        structure_name: 叙事结构名称，可选
        folding_mode: 折叠模式名称，可选
        
    Returns:
        估算结果字典
    """
    try:
        # 创建时空折叠引擎
        folder = TimeFolder()
        
        # 获取策略
        strategy = folder._get_strategy_for_structure(
            structure_name or folder.config.get("default_structure", "倒叙风暴")
        )
        
        # 估算折叠率
        fold_ratio = strategy.fold_ratio
        estimated_scene_count = max(1, int(len(scenes) * (1 - fold_ratio)))
        
        # 估算时长
        original_duration = sum(s.get("duration", 0) for s in scenes)
        estimated_duration = original_duration * (1 - fold_ratio * 0.8)  # 时长减少略小于场景减少
        
        # 映射折叠模式
        mode_descriptions = {
            None: "默认模式 (保留锚点)",
            "preserve_anchors": "保留关键锚点，压缩非关键场景",
            "condense_similar": "压缩相似场景，保持内容多样性",
            "highlight_contrast": "强调情感对比，突出戏剧冲突",
            "narrative_driven": f"基于{structure_name or '默认'}结构的叙事驱动折叠"
        }
        
        # 创建响应
        response = {
            "success": True,
            "original_count": len(scenes),
            "estimated_count": estimated_scene_count,
            "estimated_reduction": fold_ratio,
            "original_duration": original_duration,
            "estimated_duration": estimated_duration,
            "structure_name": structure_name or folder.config.get("default_structure", "倒叙风暴"),
            "strategy_name": strategy.name,
            "strategy_description": strategy.description,
            "folding_mode": folding_mode or "preserve_anchors",
            "mode_description": mode_descriptions.get(folding_mode, mode_descriptions[None])
        }
        
        return response
        
    except Exception as e:
        logger.error(f"估算折叠结果失败: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        } 