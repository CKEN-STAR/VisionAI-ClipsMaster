"""
知识图谱API - 提供字幕剧情分析和知识图谱构建接口
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query, Path
from fastapi.responses import JSONResponse, FileResponse
import tempfile
import os
import json
from typing import List, Dict, Any, Optional

from src.knowledge.graph_builder import DramaKnowledgeGraph, build_knowledge_graph
from src.parsers.srt_decoder import SRTDecoder
from src.api.security import api_key_auth
from src.utils.log_handler import get_logger

# 配置日志
logger = get_logger("knowledge_api")

# 创建API路由
router = APIRouter(
    prefix="/api/v1/knowledge",
    tags=["knowledge"],
    dependencies=[Depends(api_key_auth)],
    responses={404: {"description": "找不到资源"}},
)

@router.post("/build-graph", response_model=Dict[str, Any])
async def create_knowledge_graph(
    srt_file: UploadFile = File(...),
    language: Optional[str] = Query(None, description="语言代码 (zh/en)，不提供则自动检测")
):
    """
    从SRT字幕文件构建知识图谱
    
    上传SRT字幕文件，构建并返回剧情知识图谱数据
    """
    try:
        # 创建临时文件保存上传的SRT
        with tempfile.NamedTemporaryFile(delete=False, suffix=".srt") as temp_file:
            content = await srt_file.read()
            temp_file.write(content)
            temp_path = temp_file.name
        
        # 解析SRT文件
        try:
            srt_decoder = SRTDecoder()
            subtitles_doc = srt_decoder.parse_file(temp_path)
            subtitles = [subtitle.to_dict() for subtitle in subtitles_doc.subtitles]
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"解析SRT字幕失败: {str(e)}")
        finally:
            # 删除临时文件
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        
        # 构建知识图谱
        kg = build_knowledge_graph(subtitles, language)
        
        # 提取图谱数据
        result = {
            "characters": list(kg.characters),
            "locations": list(kg.locations),
            "events": list(kg.events),
            "character_importance": kg.get_character_importance(),
            "key_events": kg.get_key_events(top_k=5),
            "graph_stats": {
                "nodes": len(kg.graph.nodes()),
                "edges": len(kg.graph.edges()),
                "scene_count": kg.scene_count
            }
        }
        
        # 对结果进行排序，使输出更加有序
        result["characters"] = sorted(result["characters"])
        result["locations"] = sorted(result["locations"])
        
        return result
        
    except Exception as e:
        logger.error(f"构建知识图谱失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"构建知识图谱失败: {str(e)}")

@router.post("/visualize", response_class=FileResponse)
async def visualize_knowledge_graph(
    srt_file: UploadFile = File(...),
    language: Optional[str] = Query(None, description="语言代码 (zh/en)，不提供则自动检测"),
    output_format: str = Query("png", description="输出格式 (png/svg/pdf)")
):
    """
    可视化知识图谱
    
    上传SRT字幕文件，生成并返回知识图谱可视化图像
    """
    try:
        # 验证输出格式
        if output_format not in ["png", "svg", "pdf"]:
            raise HTTPException(status_code=400, detail="不支持的输出格式，请使用png、svg或pdf")
        
        # 创建临时文件保存上传的SRT
        with tempfile.NamedTemporaryFile(delete=False, suffix=".srt") as temp_file:
            content = await srt_file.read()
            temp_file.write(content)
            temp_path = temp_file.name
        
        # 解析SRT文件
        try:
            srt_decoder = SRTDecoder()
            subtitles_doc = srt_decoder.parse_file(temp_path)
            subtitles = [subtitle.to_dict() for subtitle in subtitles_doc.subtitles]
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"解析SRT字幕失败: {str(e)}")
        finally:
            # 删除临时文件
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        
        # 构建知识图谱
        kg = build_knowledge_graph(subtitles, language)
        
        # 创建临时文件保存可视化图像
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{output_format}") as viz_file:
            output_path = viz_file.name
        
        # 生成可视化图像
        kg.visualize(output_path)
        
        # 返回图像文件
        return FileResponse(
            output_path, 
            media_type=f"image/{output_format}", 
            filename=f"knowledge_graph.{output_format}"
        )
        
    except Exception as e:
        logger.error(f"生成知识图谱可视化失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"生成知识图谱可视化失败: {str(e)}")

@router.post("/character-relationships/{character_name}", response_model=List[Dict[str, Any]])
async def get_character_relationships(
    character_name: str = Path(..., description="角色名称"),
    srt_file: UploadFile = File(...),
    language: Optional[str] = Query(None, description="语言代码 (zh/en)，不提供则自动检测")
):
    """
    获取角色关系
    
    分析指定角色与其他角色的关系，返回详细的关系数据
    """
    try:
        # 创建临时文件保存上传的SRT
        with tempfile.NamedTemporaryFile(delete=False, suffix=".srt") as temp_file:
            content = await srt_file.read()
            temp_file.write(content)
            temp_path = temp_file.name
        
        # 解析SRT文件
        try:
            srt_decoder = SRTDecoder()
            subtitles_doc = srt_decoder.parse_file(temp_path)
            subtitles = [subtitle.to_dict() for subtitle in subtitles_doc.subtitles]
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"解析SRT字幕失败: {str(e)}")
        finally:
            # 删除临时文件
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        
        # 构建知识图谱
        kg = build_knowledge_graph(subtitles, language)
        
        # 检查角色是否存在
        if character_name not in kg.characters:
            raise HTTPException(status_code=404, detail=f"未找到角色: {character_name}")
        
        # 获取角色关系
        relationships = kg.get_character_relationships(character_name)
        
        return relationships
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取角色关系失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取角色关系失败: {str(e)}")

@router.post("/export", response_class=FileResponse)
async def export_knowledge_graph(
    srt_file: UploadFile = File(...),
    language: Optional[str] = Query(None, description="语言代码 (zh/en)，不提供则自动检测")
):
    """
    导出知识图谱
    
    将知识图谱导出为JSON格式文件
    """
    try:
        # 创建临时文件保存上传的SRT
        with tempfile.NamedTemporaryFile(delete=False, suffix=".srt") as temp_file:
            content = await srt_file.read()
            temp_file.write(content)
            temp_path = temp_file.name
        
        # 解析SRT文件
        try:
            srt_decoder = SRTDecoder()
            subtitles_doc = srt_decoder.parse_file(temp_path)
            subtitles = [subtitle.to_dict() for subtitle in subtitles_doc.subtitles]
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"解析SRT字幕失败: {str(e)}")
        finally:
            # 删除临时文件
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        
        # 构建知识图谱
        kg = build_knowledge_graph(subtitles, language)
        
        # 创建临时文件保存JSON
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as json_file:
            output_path = json_file.name
        
        # 导出为JSON
        kg.export_json(output_path)
        
        # 返回JSON文件
        return FileResponse(
            output_path, 
            media_type="application/json", 
            filename="knowledge_graph.json"
        )
        
    except Exception as e:
        logger.error(f"导出知识图谱失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"导出知识图谱失败: {str(e)}") 