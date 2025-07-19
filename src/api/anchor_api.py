"""
关键情节锚点检测API

提供关键情节锚点检测的API接口
"""

from typing import Dict, List, Any, Optional, Union
import json
from pathlib import Path
from dataclasses import asdict
import logging

from src.narrative.anchor_detector import detect_anchors, get_top_anchors, visualize_anchors
from src.narrative.anchor_types import AnchorType, AnchorInfo

logger = logging.getLogger("anchor_api")


def detect_scene_anchors(scenes: List[Dict[str, Any]], 
                        config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    检测场景中的关键情节锚点
    
    Args:
        scenes: 场景列表
        config_path: 配置文件路径
        
    Returns:
        检测结果字典
    """
    try:
        logger.info(f"开始检测 {len(scenes)} 个场景的关键情节锚点")
        
        # 执行锚点检测
        anchors = detect_anchors(scenes, config_path)
        
        # 统计每种锚点类型的数量
        anchor_stats = {}
        for anchor in anchors:
            anchor_type = anchor.type.value
            if anchor_type not in anchor_stats:
                anchor_stats[anchor_type] = 0
            anchor_stats[anchor_type] += 1
        
        # 获取最重要的锚点（前5个）
        top_anchors = get_top_anchors(anchors, 5)
        
        # 计算总时长
        total_duration = sum(scene.get("duration", 0) for scene in scenes)
        
        # 将结果转换为字典
        result = {
            "success": True,
            "total_anchors": len(anchors),
            "anchor_stats": anchor_stats,
            "top_anchors": [_format_anchor(anchor) for anchor in top_anchors],
            "all_anchors": [_format_anchor(anchor) for anchor in anchors],
            "anchors_by_type": _group_anchors_by_type(anchors),
            "total_duration": total_duration
        }
        
        logger.info(f"锚点检测完成，共 {len(anchors)} 个锚点")
        return result
        
    except Exception as e:
        logger.error(f"锚点检测失败: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


def detect_anchors_from_file(file_path: Union[str, Path], 
                            output_path: Optional[Union[str, Path]] = None,
                            config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    从文件中读取场景并检测锚点
    
    Args:
        file_path: 场景JSON文件路径
        output_path: 输出结果文件路径（可选）
        config_path: 配置文件路径（可选）
        
    Returns:
        检测结果字典
    """
    try:
        # 读取场景文件
        with open(file_path, "r", encoding="utf-8") as f:
            scenes = json.load(f)
        
        # 检测锚点
        result = detect_scene_anchors(scenes, config_path)
        
        # 保存结果
        if output_path and result["success"]:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            logger.info(f"锚点检测结果已保存到: {output_path}")
        
        return result
        
    except Exception as e:
        logger.error(f"从文件检测锚点失败: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


def visualize_scene_anchors(scenes: List[Dict[str, Any]], 
                          output_path: Union[str, Path],
                          config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    可视化场景中的关键情节锚点
    
    Args:
        scenes: 场景列表
        output_path: 输出可视化文件路径
        config_path: 配置文件路径（可选）
        
    Returns:
        可视化结果字典
    """
    try:
        # 检测锚点
        anchors = detect_anchors(scenes, config_path)
        
        # 计算总时长
        total_duration = sum(scene.get("duration", 0) for scene in scenes)
        
        # 生成可视化
        vis_data = visualize_anchors(anchors, total_duration, output_path)
        
        return {
            "success": True,
            "visualization_path": str(output_path),
            "data": vis_data
        }
        
    except Exception as e:
        logger.error(f"可视化锚点失败: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


def _format_anchor(anchor: AnchorInfo) -> Dict[str, Any]:
    """将AnchorInfo对象格式化为字典"""
    anchor_dict = asdict(anchor)
    
    # 将枚举值转换为字符串
    if isinstance(anchor_dict["type"], AnchorType):
        anchor_dict["type"] = anchor_dict["type"].value
    elif hasattr(anchor_dict["type"], "value"):
        anchor_dict["type"] = anchor_dict["type"].value
    
    return anchor_dict


def _group_anchors_by_type(anchors: List[AnchorInfo]) -> Dict[str, List[Dict[str, Any]]]:
    """按类型分组锚点"""
    grouped = {}
    
    for anchor in anchors:
        anchor_type = anchor.type.value
        if anchor_type not in grouped:
            grouped[anchor_type] = []
        
        grouped[anchor_type].append(_format_anchor(anchor))
    
    return grouped


# 导出API函数
__all__ = ["detect_scene_anchors", "detect_anchors_from_file", "visualize_scene_anchors"] 