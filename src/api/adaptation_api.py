"""
跨媒介模式迁移API
"""

from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import uuid
import time
from datetime import datetime
from loguru import logger

from src.adaptation.cross_media import CrossMediaAdapter
from src.version_management.pattern_version_manager import PatternVersionManager


# 创建路由器
router = APIRouter(
    prefix="/api/v1/adaptation",
    tags=["adaptation"],
    responses={
        404: {"description": "不存在"},
        500: {"description": "服务器内部错误"}
    }
)

# 定义API模型
class Pattern(BaseModel):
    """模式数据模型"""
    id: str = Field(..., description="模式ID")
    type: str = Field(..., description="模式类型")
    media_type: str = Field(..., description="原始媒介类型")
    data: Dict[str, Any] = Field(..., description="模式数据")


class AdaptationRequest(BaseModel):
    """模式适配请求"""
    patterns: List[Pattern] = Field(..., description="待适配的模式列表")
    target_media_type: str = Field(..., description="目标媒介类型")


class VersionAdaptRequest(BaseModel):
    """版本适配请求"""
    source_version: Optional[str] = Field(None, description="源版本名称，如果为None则使用最新版本")
    target_media_type: str = Field(..., description="目标媒介类型")


class AdaptationResponse(BaseModel):
    """模式适配响应"""
    request_id: str = Field(..., description="请求ID")
    timestamp: str = Field(..., description="时间戳")
    adapted_patterns: List[Dict[str, Any]] = Field(..., description="适配后的模式")


class VersionAdaptResponse(BaseModel):
    """版本适配响应"""
    request_id: str = Field(..., description="请求ID") 
    timestamp: str = Field(..., description="时间戳")
    source_version: str = Field(..., description="源版本")
    target_version: str = Field(..., description="目标版本")
    target_media_type: str = Field(..., description="目标媒介类型")
    status: str = Field(..., description="适配状态")
    pattern_count: int = Field(..., description="适配模式数量")


# 后台任务状态存储
adaptation_tasks = {}


@router.get(
    "/media-types",
    response_model=List[str],
    summary="获取支持的媒介类型",
    description="获取系统支持的所有媒介类型"
)
async def get_media_types() -> List[str]:
    """获取所有支持的媒介类型"""
    try:
        adapter = CrossMediaAdapter()
        return adapter.get_supported_media_types()
    except Exception as e:
        logger.error(f"获取媒介类型失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取媒介类型失败: {str(e)}"
        )


@router.post(
    "/adapt",
    response_model=AdaptationResponse,
    summary="适配模式",
    description="将一组模式适配到目标媒介类型"
)
async def adapt_patterns(request: AdaptationRequest) -> AdaptationResponse:
    """
    将一组模式适配到目标媒介类型
    
    - **patterns**: 待适配的模式列表
    - **target_media_type**: 目标媒介类型
    
    返回适配后的模式列表
    """
    try:
        # 初始化跨媒介适配器
        adapter = CrossMediaAdapter()
        
        # 检查媒介类型是否支持
        supported_types = adapter.get_supported_media_types()
        if request.target_media_type not in supported_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的媒介类型: {request.target_media_type}，支持的类型: {', '.join(supported_types)}"
            )
        
        # 转换请求模式为适配器所需格式
        patterns_to_adapt = []
        for pattern in request.patterns:
            # 合并id、type和media_type到data字典
            pattern_data = pattern.data.copy()
            pattern_data["id"] = pattern.id
            pattern_data["type"] = pattern.type
            pattern_data["media_type"] = pattern.media_type
            patterns_to_adapt.append(pattern_data)
        
        # 进行适配
        adapted_patterns = adapter.batch_adapt_patterns(patterns_to_adapt, request.target_media_type)
        
        # 准备响应
        response = {
            "request_id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "adapted_patterns": adapted_patterns
        }
        
        return response
    
    except Exception as e:
        logger.error(f"模式适配失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"模式适配失败: {str(e)}"
        )


@router.post(
    "/version/adapt",
    response_model=VersionAdaptResponse,
    summary="适配版本",
    description="将指定版本的模式适配到目标媒介类型，并创建新版本"
)
async def adapt_version(
    request: VersionAdaptRequest,
    background_tasks: BackgroundTasks
) -> VersionAdaptResponse:
    """
    将指定版本的模式适配到目标媒介类型，并创建新版本
    
    - **source_version**: 源版本名称，如果为None则使用最新版本
    - **target_media_type**: 目标媒介类型
    
    返回适配版本的信息
    """
    try:
        # 初始化组件
        adapter = CrossMediaAdapter()
        version_manager = PatternVersionManager()
        
        # 检查媒介类型是否支持
        supported_types = adapter.get_supported_media_types()
        if request.target_media_type not in supported_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的媒介类型: {request.target_media_type}，支持的类型: {', '.join(supported_types)}"
            )
        
        # 获取源版本
        source_version = request.source_version
        if not source_version:
            source_version = version_manager.get_latest_version()
            
        # 检查源版本是否存在
        if not version_manager.get_version_metadata(source_version):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"未找到源版本: {source_version}"
            )
        
        # 生成请求ID
        request_id = str(uuid.uuid4())
        
        # 创建任务状态记录
        adaptation_tasks[request_id] = {
            "status": "pending",
            "source_version": source_version,
            "target_media_type": request.target_media_type,
            "created_at": time.time()
        }
        
        # 定义后台任务
        def process_adaptation():
            try:
                # 更新任务状态
                adaptation_tasks[request_id]["status"] = "processing"
                
                # 获取模式数量
                config = version_manager.get_pattern_config(source_version)
                pattern_count = len(config.get("top_patterns", []))
                
                # 执行适配
                result = adapter.create_adapted_version(source_version, request.target_media_type)
                
                # 生成目标版本名
                media_type_short = adapter.reverse_media_mapping.get(request.target_media_type, "media")
                target_version = f"{source_version.rstrip('0123456789')}_{media_type_short}"
                
                # 更新任务状态
                adaptation_tasks[request_id].update({
                    "status": "completed" if result else "failed",
                    "target_version": target_version if result else None,
                    "pattern_count": pattern_count,
                    "completed_at": time.time()
                })
                
                # 清理旧任务（保留24小时）
                _cleanup_old_tasks()
                
            except Exception as e:
                logger.error(f"版本适配失败: {e}")
                adaptation_tasks[request_id].update({
                    "status": "failed",
                    "error": str(e),
                    "completed_at": time.time()
                })
        
        # 添加后台任务
        background_tasks.add_task(process_adaptation)
        
        # 生成目标版本名（预测）
        media_type_short = adapter.reverse_media_mapping.get(request.target_media_type, "media")
        predicted_target_version = f"{source_version.rstrip('0123456789')}_{media_type_short}"
        
        # 准备初始响应
        response = {
            "request_id": request_id,
            "timestamp": datetime.now().isoformat(),
            "source_version": source_version,
            "target_version": predicted_target_version,
            "target_media_type": request.target_media_type,
            "status": "processing",
            "pattern_count": 0  # 初始值，将在后台任务中更新
        }
        
        return response
    
    except Exception as e:
        logger.error(f"启动版本适配失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"启动版本适配失败: {str(e)}"
        )


@router.get(
    "/version/adapt/{request_id}",
    response_model=VersionAdaptResponse,
    summary="获取版本适配状态",
    description="获取版本适配任务的状态和结果"
)
async def get_adaptation_status(request_id: str) -> VersionAdaptResponse:
    """
    获取版本适配任务的状态和结果
    
    - **request_id**: 请求ID
    
    返回适配任务的状态和结果
    """
    if request_id not in adaptation_tasks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"未找到ID为 {request_id} 的适配任务"
        )
    
    task_info = adaptation_tasks[request_id]
    
    # 准备响应
    response = {
        "request_id": request_id,
        "timestamp": datetime.now().isoformat(),
        "source_version": task_info["source_version"],
        "target_version": task_info.get("target_version", "未完成"),
        "target_media_type": task_info["target_media_type"],
        "status": task_info["status"],
        "pattern_count": task_info.get("pattern_count", 0)
    }
    
    return response


def _cleanup_old_tasks():
    """清理24小时以上的旧任务"""
    current_time = time.time()
    to_delete = []
    
    for task_id, task_info in adaptation_tasks.items():
        # 获取任务创建时间
        created_at = task_info.get("created_at", current_time)
        
        # 如果任务已经完成或失败，且创建时间超过24小时
        if ((task_info["status"] in ["completed", "failed"]) and 
            (current_time - created_at > 24 * 60 * 60)):  # 24小时
            to_delete.append(task_id)
    
    # 删除旧任务
    for task_id in to_delete:
        del adaptation_tasks[task_id] 