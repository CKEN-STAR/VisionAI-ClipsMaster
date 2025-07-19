"""
叙事分析和锚点检测API

提供叙事分析和关键情节锚点检测的RESTful API接口
"""

from typing import Dict, List, Any, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Body, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import json
import os
from pathlib import Path
import logging

from src.api.anchor_api import detect_scene_anchors, visualize_scene_anchors
from src.api.structure_api import select_structure, select_structure_from_scenes, get_available_structures
from src.utils.file_utils import ensure_directory

# 创建路由器
router = APIRouter(prefix="/api/narrative", tags=["narrative"])

# 创建日志记录器
logger = logging.getLogger("narrative_api")

# 创建临时目录
TEMP_DIR = "temp/narrative"
ensure_directory(TEMP_DIR)


# 定义请求/响应模型
class ScenesRequest(BaseModel):
    """场景数据请求"""
    scenes: List[Dict[str, Any]] = Field(..., description="场景数据列表")
    config_path: Optional[str] = Field(None, description="配置文件路径")


class AnchorResponse(BaseModel):
    """锚点检测响应"""
    success: bool = Field(..., description="是否成功")
    total_anchors: Optional[int] = Field(None, description="锚点总数")
    anchor_stats: Optional[Dict[str, int]] = Field(None, description="各类锚点统计")
    top_anchors: Optional[List[Dict[str, Any]]] = Field(None, description="最重要的锚点")
    all_anchors: Optional[List[Dict[str, Any]]] = Field(None, description="所有锚点")
    anchors_by_type: Optional[Dict[str, List[Dict[str, Any]]]] = Field(None, description="按类型分组的锚点")
    total_duration: Optional[float] = Field(None, description="总时长(秒)")
    error: Optional[str] = Field(None, description="错误信息")


class StructureRequest(BaseModel):
    """叙事结构请求"""
    script_metadata: Dict[str, Any] = Field(..., description="剧本元数据")
    scenes: Optional[List[Dict[str, Any]]] = Field(None, description="场景数据列表（可选）")
    config_path: Optional[str] = Field(None, description="配置文件路径")


class StructureResponse(BaseModel):
    """叙事结构响应"""
    success: bool = Field(..., description="是否成功")
    pattern_name: Optional[str] = Field(None, description="结构模式名称")
    confidence: Optional[float] = Field(None, description="匹配置信度")
    reason: Optional[str] = Field(None, description="匹配原因")
    steps: Optional[List[str]] = Field(None, description="结构步骤")
    description: Optional[str] = Field(None, description="结构描述")
    suitability: Optional[List[str]] = Field(None, description="适用类型")
    anchor_mapping: Optional[Dict[str, List[Dict[str, Any]]]] = Field(None, description="锚点映射")
    error: Optional[str] = Field(None, description="错误信息")


# API端点
@router.post("/detect-anchors", response_model=AnchorResponse, 
            summary="检测关键情节锚点", 
            description="分析场景数据，检测关键情节锚点")
async def api_detect_anchors(request: ScenesRequest):
    """
    检测场景中的关键情节锚点
    
    接收场景数据列表，返回检测到的关键情节锚点
    """
    try:
        scenes = request.scenes
        config_path = request.config_path
        
        # 执行锚点检测
        result = detect_scene_anchors(scenes, config_path)
        
        return result
    
    except Exception as e:
        logger.error(f"API锚点检测失败: {str(e)}")
        return {"success": False, "error": str(e)}


@router.post("/upload-scenes", response_model=AnchorResponse,
            summary="上传场景文件并检测锚点", 
            description="上传场景JSON文件，检测关键情节锚点")
async def api_upload_and_detect(
    file: UploadFile = File(..., description="场景JSON文件"),
    config_path: Optional[str] = Form(None, description="配置文件路径")
):
    """
    上传场景文件并检测锚点
    
    接收场景JSON文件，返回检测到的关键情节锚点
    """
    try:
        # 保存上传的文件
        file_path = os.path.join(TEMP_DIR, file.filename)
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # 读取场景数据
        with open(file_path, "r", encoding="utf-8") as f:
            scenes = json.load(f)
        
        # 执行锚点检测
        result = detect_scene_anchors(scenes, config_path)
        
        # 清理临时文件
        try:
            os.remove(file_path)
        except:
            pass
        
        return result
    
    except Exception as e:
        logger.error(f"API文件上传锚点检测失败: {str(e)}")
        return {"success": False, "error": str(e)}


@router.post("/visualize-anchors", 
            summary="可视化场景锚点", 
            description="分析场景数据，生成锚点可视化")
async def api_visualize_anchors(request: ScenesRequest):
    """
    可视化场景中的关键情节锚点
    
    接收场景数据列表，返回锚点可视化数据
    """
    try:
        scenes = request.scenes
        config_path = request.config_path
        
        # 生成输出文件名
        output_path = os.path.join(TEMP_DIR, f"visualization_{len(scenes)}_scenes.json")
        
        # 执行可视化
        result = visualize_scene_anchors(scenes, output_path, config_path)
        
        # 读取可视化数据
        if result["success"] and os.path.exists(output_path):
            with open(output_path, "r", encoding="utf-8") as f:
                vis_data = json.load(f)
            
            return {
                "success": True,
                "visualization_data": vis_data
            }
        
        return result
    
    except Exception as e:
        logger.error(f"API锚点可视化失败: {str(e)}")
        return {"success": False, "error": str(e)}


@router.post("/select-structure", response_model=StructureResponse,
            summary="选择叙事结构", 
            description="根据剧本元数据和场景选择最佳叙事结构")
async def api_select_structure(request: StructureRequest):
    """
    选择最佳叙事结构
    
    接收剧本元数据和可选的场景数据，返回最佳匹配的叙事结构
    """
    try:
        script_metadata = request.script_metadata
        scenes = request.scenes
        config_path = request.config_path
        
        # 如果提供了场景数据，使用场景和元数据选择结构
        if scenes:
            result = select_structure_from_scenes(scenes, script_metadata, config_path)
        else:
            # 否则仅使用元数据选择结构
            result = select_structure(script_metadata, None, config_path)
        
        return result
    
    except Exception as e:
        logger.error(f"API选择叙事结构失败: {str(e)}")
        return {"success": False, "error": str(e)}


@router.get("/available-structures", 
           summary="获取可用叙事结构",
           description="获取所有可用的叙事结构模式")
async def api_get_structures(config_path: Optional[str] = None):
    """
    获取所有可用的叙事结构模式
    
    返回所有可用的叙事结构模式信息
    """
    try:
        return get_available_structures(config_path)
    
    except Exception as e:
        logger.error(f"API获取叙事结构模式失败: {str(e)}")
        return {"success": False, "error": str(e)}


# 健康检查端点
@router.get("/health", summary="健康检查", description="检查叙事和锚点模块健康状态")
async def api_health_check():
    """健康检查"""
    return {"status": "ok", "service": "narrative_api"} 