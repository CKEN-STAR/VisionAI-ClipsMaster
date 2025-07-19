"""
叙事结构选择器API

提供叙事结构选择和锚点映射的API函数
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Union
from pathlib import Path

from src.narrative.structure_selector import (
    StructureSelector, 
    select_narrative_structure,
    organize_anchors_by_structure,
    get_structure_patterns
)
from src.narrative.anchor_detector import detect_anchors
from src.narrative.anchor_types import AnchorInfo
from src.utils.file_utils import ensure_directory, safe_write_json

# 创建日志记录器
logger = logging.getLogger("structure_api")


def select_structure(script_metadata: Dict[str, Any], 
                    anchors: Optional[List[AnchorInfo]] = None,
                    config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    根据剧本元数据和锚点选择最佳叙事结构
    
    Args:
        script_metadata: 剧本元数据，包含类型、情感基调等
        anchors: 锚点列表，可选。如果为None，则仅基于元数据判断
        config_path: 配置文件路径，可选
        
    Returns:
        结构选择结果字典
    """
    try:
        # 初始化选择器
        selector = StructureSelector(config_path)
        
        # 选择最佳结构
        result = selector.select_best_fit(script_metadata, anchors)
        
        # 构造标准响应
        response = {
            "success": True,
            "pattern_name": result["pattern_name"],
            "confidence": result["confidence"],
            "reason": result["reason"],
            "steps": result["pattern_data"].get("steps", []),
            "description": result["pattern_data"].get("description", ""),
            "suitability": result["pattern_data"].get("suitability", [])
        }
        
        # 如果有锚点，映射到结构
        if anchors:
            anchor_mapping = selector.map_anchors_to_structure(anchors, result["pattern_name"])
            
            # 将锚点对象转换为可序列化的字典
            serializable_mapping = {}
            for step, step_anchors in anchor_mapping.items():
                serializable_mapping[step] = [
                    {
                        "id": a.id,
                        "type": a.type.value,
                        "position": a.position,
                        "confidence": a.confidence,
                        "importance": a.importance,
                        "description": a.description
                    }
                    for a in step_anchors
                ]
            
            response["anchor_mapping"] = serializable_mapping
        
        return response
        
    except Exception as e:
        logger.error(f"选择叙事结构失败: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


def select_structure_from_scenes(scenes: List[Dict[str, Any]], 
                                script_metadata: Dict[str, Any],
                                config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    从场景数据中选择最佳叙事结构
    
    Args:
        scenes: 场景数据列表
        script_metadata: 剧本元数据
        config_path: 配置文件路径，可选
        
    Returns:
        结构选择结果字典
    """
    try:
        # 检测锚点
        anchors = detect_anchors(scenes)
        
        # 选择结构
        return select_structure(script_metadata, anchors, config_path)
        
    except Exception as e:
        logger.error(f"从场景选择叙事结构失败: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


def get_available_structures(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    获取所有可用的叙事结构模式
    
    Args:
        config_path: 配置文件路径，可选
        
    Returns:
        所有结构模式的信息
    """
    try:
        # 初始化选择器
        selector = StructureSelector(config_path)
        
        # 获取所有模式
        patterns = selector.get_all_patterns()
        
        # 构造响应
        response = {
            "success": True,
            "total_patterns": len(patterns),
            "patterns": {}
        }
        
        # 处理每个模式
        for name, data in patterns.items():
            response["patterns"][name] = {
                "steps": data.get("steps", []),
                "description": data.get("description", ""),
                "suitability": data.get("suitability", [])
            }
        
        return response
        
    except Exception as e:
        logger.error(f"获取叙事结构模式失败: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


def generate_structure_visualization(anchors: List[AnchorInfo],
                                   structure_name: str,
                                   output_path: Optional[Union[str, Path]] = None,
                                   config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    生成叙事结构可视化数据
    
    Args:
        anchors: 锚点列表
        structure_name: 结构名称
        output_path: 输出文件路径，如果为None则不保存文件
        config_path: 配置文件路径，可选
        
    Returns:
        可视化数据字典
    """
    try:
        # 初始化选择器
        selector = StructureSelector(config_path)
        
        # 获取结构步骤
        steps = selector.get_structure_steps(structure_name)
        
        if not steps:
            return {
                "success": False,
                "error": f"找不到结构模式: {structure_name}"
            }
        
        # 映射锚点到结构
        anchor_mapping = selector.map_anchors_to_structure(anchors, structure_name)
        
        # 获取结构配置
        pattern_data = selector.patterns.get(structure_name, {})
        beat_distribution = pattern_data.get("beat_distribution", {})
        
        # 构建可视化数据
        visualization_data = {
            "structure_name": structure_name,
            "description": pattern_data.get("description", ""),
            "steps": steps,
            "beat_distribution": beat_distribution,
            "anchors_by_step": {}
        }
        
        # 将锚点数据添加到可视化数据
        for step, step_anchors in anchor_mapping.items():
            visualization_data["anchors_by_step"][step] = [
                {
                    "id": a.id,
                    "type": a.type.value,
                    "position": a.position,
                    "confidence": a.confidence,
                    "importance": a.importance,
                    "description": a.description
                }
                for a in step_anchors
            ]
        
        # 可视化配置
        color_map = {}
        if config_path:
            try:
                # 获取配置中的颜色映射
                selector_config = selector.config
                color_map = selector_config.get("visualization", {}).get("color_map", {})
            except:
                pass
        
        visualization_data["visualization"] = {
            "color_map": color_map,
            "total_anchors": len(anchors)
        }
        
        # 保存到文件
        if output_path:
            try:
                output_path = Path(output_path)
                ensure_directory(output_path.parent)
                safe_write_json(output_path, visualization_data)
            except Exception as e:
                logger.warning(f"保存可视化数据到文件失败: {e}")
        
        # 返回结果
        return {
            "success": True,
            "visualization_data": visualization_data
        }
        
    except Exception as e:
        logger.error(f"生成叙事结构可视化失败: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


def _format_pattern(pattern_name: str, pattern_data: Dict[str, Any]) -> Dict[str, Any]:
    """格式化结构模式数据为API响应格式"""
    return {
        "name": pattern_name,
        "steps": pattern_data.get("steps", []),
        "description": pattern_data.get("description", ""),
        "suitability": pattern_data.get("suitability", []),
        "anchor_types": [str(t) if not isinstance(t, str) else t 
                        for t in pattern_data.get("anchor_types", [])],
        "emotion_tone": pattern_data.get("emotion_tone", ""),
        "pace": pattern_data.get("pace", "medium")
    } 