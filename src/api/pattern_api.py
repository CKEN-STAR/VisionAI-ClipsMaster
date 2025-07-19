"""
模式管理相关API接口
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import time
import uuid
from datetime import datetime

from src.core.pattern_updater import PatternUpdater
from src.version_management.pattern_version_manager import (
    get_available_versions, 
    get_version_metadata,
    set_current_version
)

# 创建路由器
router = APIRouter(
    prefix="/api/v1/patterns",
    tags=["patterns"],
    responses={
        404: {"description": "不存在"},
        500: {"description": "服务器内部错误"}
    }
)

# 定义请求模型
class HitData(BaseModel):
    """命中数据模型"""
    id: str = Field(..., description="数据ID")
    origin_srt: str = Field(..., description="原始字幕")
    hit_srt: str = Field(..., description="命中字幕")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")


class PatternUpdateRequest(BaseModel):
    """模式更新请求模型"""
    hit_data: List[HitData] = Field(..., description="命中数据列表")
    timeout: Optional[int] = Field(30, description="最大处理时间(秒)")


# 定义响应模型
class PatternUpdateResponse(BaseModel):
    """模式更新响应模型"""
    update_id: str = Field(..., description="更新操作ID")
    timestamp: str = Field(..., description="更新时间")
    stats: Dict[str, Any] = Field(..., description="更新统计信息")


class VersionInfo(BaseModel):
    """版本信息模型"""
    version: str = Field(..., description="版本名称")
    created_at: str = Field(..., description="创建时间")
    description: str = Field(..., description="版本描述")
    author: str = Field(..., description="作者")


# 异步任务存储
background_tasks_status = {}

# API接口实现
@router.post(
    "/update",
    response_model=PatternUpdateResponse,
    summary="更新模式库",
    description="处理新的命中数据，更新模式库"
)
async def update_patterns(
    request: PatternUpdateRequest,
    background_tasks: BackgroundTasks
) -> PatternUpdateResponse:
    """
    处理新的命中数据，更新模式库
    
    - **hit_data**: 命中数据列表，每项包含原始字幕和命中字幕
    - **timeout**: 最大处理时间(秒)，默认30秒
    
    返回更新操作ID和统计信息
    """
    # 准备数据
    hit_data_list = [item.dict() for item in request.hit_data]
    
    # 创建请求ID
    request_id = str(uuid.uuid4())
    background_tasks_status[request_id] = {"status": "pending", "result": None}
    
    # 定义后台任务
    def process_update():
        try:
            background_tasks_status[request_id]["status"] = "processing"
            
            # 初始化更新器并处理数据
            updater = PatternUpdater()
            result = updater.streaming_update(hit_data_list)
            
            # 更新任务状态
            background_tasks_status[request_id]["status"] = "completed"
            background_tasks_status[request_id]["result"] = result
            
            # 清理旧任务状态（保留2小时）
            cleanup_old_tasks()
        except Exception as e:
            background_tasks_status[request_id]["status"] = "failed"
            background_tasks_status[request_id]["error"] = str(e)
    
    # 添加后台任务
    background_tasks.add_task(process_update)
    
    # 准备初始响应
    response = {
        "update_id": request_id,
        "timestamp": datetime.now().isoformat(),
        "stats": {
            "status": "processing",
            "processed_items": len(hit_data_list),
            "estimated_time": min(10 * len(hit_data_list), request.timeout)
        }
    }
    
    return response


@router.get(
    "/update/{update_id}",
    response_model=PatternUpdateResponse,
    summary="获取更新状态",
    description="获取模式更新操作的状态和结果"
)
async def get_update_status(update_id: str) -> PatternUpdateResponse:
    """
    获取模式更新操作的状态和结果
    
    - **update_id**: 更新操作ID
    
    返回更新操作的状态和结果
    """
    if update_id not in background_tasks_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"未找到ID为 {update_id} 的更新任务"
        )
    
    task_info = background_tasks_status[update_id]
    
    # 如果任务已完成，返回完整结果
    if task_info["status"] == "completed" and task_info["result"]:
        return task_info["result"]
    
    # 如果任务失败，返回错误信息
    if task_info["status"] == "failed":
        error_message = task_info.get("error", "未知错误")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新任务失败: {error_message}"
        )
    
    # 任务仍在处理中
    return {
        "update_id": update_id,
        "timestamp": datetime.now().isoformat(),
        "stats": {
            "status": task_info["status"],
            "message": "任务正在处理中，请稍后再查询"
        }
    }


@router.get(
    "/versions",
    response_model=List[VersionInfo],
    summary="获取可用版本",
    description="获取所有可用的模式版本"
)
async def list_versions() -> List[VersionInfo]:
    """
    获取所有可用的模式版本
    
    返回可用版本列表
    """
    try:
        versions = get_available_versions()
        return [
            {
                "version": v["version"],
                "created_at": v.get("created_at", ""),
                "description": v.get("description", ""),
                "author": v.get("author", "系统")
            }
            for v in versions
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取版本列表失败: {str(e)}"
        )


@router.put(
    "/versions/{version_name}/activate",
    response_model=Dict[str, Any],
    summary="激活版本",
    description="激活指定的模式版本"
)
async def activate_version(version_name: str) -> Dict[str, Any]:
    """
    激活指定的模式版本
    
    - **version_name**: 版本名称
    
    返回操作结果
    """
    try:
        result = set_current_version(version_name)
        if result:
            metadata = get_version_metadata(version_name)
            return {
                "success": True,
                "message": f"成功激活版本 {version_name}",
                "version": metadata
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"激活版本 {version_name} 失败"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"激活版本失败: {str(e)}"
        )


def cleanup_old_tasks():
    """清理2小时以上的旧任务状态"""
    current_time = time.time()
    to_delete = []
    
    for task_id, task_info in background_tasks_status.items():
        # 获取任务创建时间（如果没有，默认为当前时间）
        created_at = task_info.get("created_at", current_time)
        
        # 如果任务已经完成或失败，且创建时间超过2小时
        if (task_info["status"] in ["completed", "failed"] and 
            current_time - created_at > 2 * 60 * 60):  # 2小时
            to_delete.append(task_id)
    
    # 删除旧任务
    for task_id in to_delete:
        del background_tasks_status[task_id] 