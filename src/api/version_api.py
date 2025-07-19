#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
版本追踪和演化可视化API

该模块提供版本谱系追踪和可视化的API接口，方便其他模块调用。
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Tuple, Union
from fastapi import APIRouter, HTTPException

from src.versioning import (
    EvolutionTracker,
    generate_html_visualization
)

# 配置日志
logger = logging.getLogger("version_api")

# 创建路由
router = APIRouter(prefix="/api/version", tags=["version"])

# 全局追踪器实例
_tracker = None

def get_tracker(db_path: Optional[str] = None) -> EvolutionTracker:
    """获取或创建版本追踪器实例
    
    Args:
        db_path: 数据库文件路径，可选
        
    Returns:
        EvolutionTracker实例
    """
    global _tracker
    
    if _tracker is None:
        _tracker = EvolutionTracker(db_path)
    
    return _tracker

def add_version(
    version_id: str, 
    parent_id: Optional[str] = None, 
    params: Optional[Dict[str, Any]] = None,
    db_path: Optional[str] = None
) -> Dict[str, Any]:
    """添加新版本
    
    Args:
        version_id: 版本ID
        parent_id: 父版本ID
        params: 版本参数
        db_path: 可选的数据库路径
        
    Returns:
        结果信息字典
    """
    tracker = get_tracker(db_path)
    
    try:
        success = tracker.add_version(version_id, parent_id, params)
        
        if success:
            return {
                "success": True,
                "message": f"成功添加版本 {version_id}",
                "version_id": version_id
            }
        else:
            return {
                "success": False,
                "message": f"添加版本 {version_id} 失败，可能已存在该版本"
            }
    except Exception as e:
        logger.error(f"添加版本时出错: {str(e)}")
        return {
            "success": False,
            "message": f"添加版本时发生错误: {str(e)}"
        }

def get_version_info(version_id: str, db_path: Optional[str] = None) -> Dict[str, Any]:
    """获取版本信息
    
    Args:
        version_id: 版本ID
        db_path: 可选的数据库路径
        
    Returns:
        版本信息字典
    """
    tracker = get_tracker(db_path)
    
    try:
        version_info = tracker.get_version(version_id)
        
        if version_info:
            return {
                "success": True,
                "version_info": version_info
            }
        else:
            return {
                "success": False,
                "message": f"未找到版本 {version_id}"
            }
    except Exception as e:
        logger.error(f"获取版本信息时出错: {str(e)}")
        return {
            "success": False,
            "message": f"获取版本信息时发生错误: {str(e)}"
        }

def visualize_version_evolution(
    version_id: str,
    output_path: Optional[str] = None,
    db_path: Optional[str] = None
) -> Dict[str, Any]:
    """生成版本演化可视化
    
    Args:
        version_id: 版本ID
        output_path: 输出文件路径
        db_path: 可选的数据库路径
        
    Returns:
        结果信息字典
    """
    tracker = get_tracker(db_path)
    
    if output_path is None:
        # 默认输出路径
        output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
                                 "output", "visualization")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"version_evolution_{version_id}.html")
    
    try:
        # 检查版本是否存在
        version_info = tracker.get_version(version_id)
        if not version_info:
            return {
                "success": False,
                "message": f"未找到版本 {version_id}"
            }
        
        # 生成可视化
        tree_data = tracker.visualize_lineage(version_id)
        html_path = generate_html_visualization(tree_data, output_path)
        
        if html_path:
            return {
                "success": True,
                "message": f"成功生成版本演化可视化",
                "visualization_path": html_path,
                "version_id": version_id
            }
        else:
            return {
                "success": False,
                "message": "生成可视化失败"
            }
    except Exception as e:
        logger.error(f"生成版本演化可视化时出错: {str(e)}")
        return {
            "success": False,
            "message": f"生成版本演化可视化时发生错误: {str(e)}"
        }

def merge_versions(
    target_version_id: str,
    source_version_id: str,
    params: Optional[Dict[str, Any]] = None,
    db_path: Optional[str] = None
) -> Dict[str, Any]:
    """合并两个版本，创建从源版本到目标版本的连接
    
    Args:
        target_version_id: 目标版本ID
        source_version_id: 源版本ID
        params: 可选的更新参数
        db_path: 可选的数据库路径
        
    Returns:
        结果信息字典
    """
    tracker = get_tracker(db_path)
    
    try:
        # 检查两个版本是否都存在
        target_info = tracker.get_version(target_version_id)
        source_info = tracker.get_version(source_version_id)
        
        if not target_info:
            return {
                "success": False,
                "message": f"目标版本 {target_version_id} 不存在"
            }
        
        if not source_info:
            return {
                "success": False,
                "message": f"源版本 {source_version_id} 不存在"
            }
        
        # 创建连接（复用add_version方法，但不更新参数）
        success = tracker.add_version(target_version_id, source_version_id, None)
        
        if success:
            return {
                "success": True,
                "message": f"成功合并版本 {source_version_id} 到 {target_version_id}",
                "target_version_id": target_version_id,
                "source_version_id": source_version_id
            }
        else:
            return {
                "success": False,
                "message": f"合并版本失败"
            }
    except Exception as e:
        logger.error(f"合并版本时出错: {str(e)}")
        return {
            "success": False,
            "message": f"合并版本时发生错误: {str(e)}"
        }


# API Routes
@router.post("/version/add")
async def api_add_version(version_id: str, parent_id: Optional[str] = None, params: Optional[Dict[str, Any]] = None):
    """API接口：添加新版本"""
    result = add_version(version_id, parent_id, params)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result

@router.get("/version/{version_id}")
async def api_get_version_info(version_id: str):
    """API接口：获取版本信息"""
    result = get_version_info(version_id)
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["message"])
    return result

@router.get("/version/{version_id}/visualize")
async def api_visualize_version(version_id: str):
    """API接口：可视化版本谱系"""
    result = visualize_version_evolution(version_id)
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["message"])
    return result

@router.post("/version/merge")
async def api_merge_versions(target_version_id: str, source_version_id: str):
    """API接口：合并两个版本"""
    result = merge_versions(target_version_id, source_version_id)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result 