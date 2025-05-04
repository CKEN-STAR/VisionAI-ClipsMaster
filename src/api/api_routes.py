"""
RESTful API路由实现

为VisionAI-ClipsMaster提供全面的RESTful API接口
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Request, Body
from fastapi.responses import JSONResponse
from pydantic import UUID4
import uuid
import time
import os
from typing import Dict, List, Optional
import asyncio

from .schema import (
    ClipRequest, ClipResponse, StatusRequest, BatchClipRequest, 
    BatchClipResponse, TaskStatus, ExportFormat
)
from .security import JWTBearer
from ..core.clip_generator import ClipGenerator
from ..core.model_switcher import ModelSwitcher
from ..core.language_detector import detect_language
from ..utils.log_handler import get_logger

# 导入时空折叠引擎API
from src.api.timefold_api import (
    fold_scenes, get_folding_strategies_info, 
    get_folding_modes_info, estimate_folding_result
)

# 创建路由器
router = APIRouter(tags=["clips"])
logger = get_logger()

# 内存中存储任务状态（生产环境应使用Redis等持久化）
tasks: Dict[str, Dict] = {}
batch_tasks: Dict[str, Dict] = {}

# 初始化增量更新广播器
try:
    from src.realtime import DeltaBroadcaster, set_delta_broadcaster
    _delta_broadcaster = None
except ImportError:
    logger.warning("无法导入增量更新广播器模块，相关功能将不可用")
    _delta_broadcaster = None

@router.on_event("startup")
async def startup_event():
    """应用程序启动时初始化"""
    global _delta_broadcaster
    
    try:
        # 初始化增量更新广播器
        if _delta_broadcaster is None:
            _delta_broadcaster = DeltaBroadcaster()
            await _delta_broadcaster.initialize()
            await _delta_broadcaster.start()
            set_delta_broadcaster(_delta_broadcaster)
            logger.info("增量更新广播器已初始化")
    except Exception as e:
        logger.error(f"初始化增量更新广播器失败: {str(e)}")

@router.on_event("shutdown")
async def shutdown_event():
    """应用程序关闭时清理资源"""
    global _delta_broadcaster
    
    # 关闭增量更新广播器
    if _delta_broadcaster:
        await _delta_broadcaster.stop()
        logger.info("增量更新广播器已关闭")

@router.post("/generate", response_model=ClipResponse)
async def generate_clip(
    request: ClipRequest,
    background_tasks: BackgroundTasks
):
    """
    创建新的视频剪辑任务
    
    - 接收视频和字幕路径
    - 异步处理剪辑任务
    - 返回任务ID和初始状态
    """
    # 路径校验
    if not os.path.exists(request.video_path):
        raise HTTPException(status_code=400, detail="视频文件不存在")
    if not os.path.exists(request.srt_path):
        raise HTTPException(status_code=400, detail="字幕文件不存在")
        
    # 自动检测语言（如果未指定）
    lang = request.lang
    if lang == "auto":
        detected_lang = detect_language(request.srt_path)
        lang = detected_lang
        logger.info(f"自动检测到语言: {lang}")
    
    # 英文模型检查（仅配置未下载）
    if lang == "en":
        model_status = ModelSwitcher.check_model_status("en")
        if not model_status.get("available", False):
            raise HTTPException(
                status_code=400, 
                detail="英文模型仅配置未下载。请下载模型后重试，或切换到中文模型。"
            )
    
    # 创建任务
    task_id = str(uuid.uuid4())
    
    # 记录任务状态
    tasks[task_id] = {
        "request": request.dict(),
        "status": TaskStatus.PENDING,
        "start_time": time.time(),
        "progress": 0.0,
        "result": None,
        "message": "任务已创建，等待处理"
    }
    
    # 在后台处理任务
    background_tasks.add_task(
        process_clip_task,
        task_id=task_id,
        request=request
    )
    
    return ClipResponse(
        task_id=task_id,
        status=TaskStatus.PENDING,
        render_time=0.0,
        progress=0.0,
        message="任务已创建，正在开始处理"
    )

@router.get("/task/{task_id}", response_model=ClipResponse)
async def get_task_status(task_id: str):
    """
    获取任务状态
    
    - 接收任务ID
    - 返回当前处理状态和进度
    """
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task_info = tasks[task_id]
    
    # 计算处理时间
    current_time = time.time()
    start_time = task_info.get("start_time", current_time)
    render_time = current_time - start_time
    
    # 构造响应
    response = ClipResponse(
        task_id=task_id,
        status=task_info["status"],
        render_time=render_time,
        progress=task_info.get("progress", 0.0),
        message=task_info.get("message", "")
    )
    
    # 添加结果信息（如果可用）
    if task_info["status"] == TaskStatus.SUCCESS and task_info.get("result"):
        result = task_info["result"]
        response.project_path = result.get("project_path")
        response.video_path = result.get("video_path")
        response.metrics = result.get("metrics")
    
    return response

@router.post("/batch", response_model=BatchClipResponse)
async def batch_generate(
    request: BatchClipRequest,
    background_tasks: BackgroundTasks
):
    """
    创建批量视频剪辑任务
    
    - 接收多个剪辑请求
    - 并行处理多个任务
    - 返回批次ID和任务状态
    """
    if not request.clips:
        raise HTTPException(status_code=400, detail="至少需要一个剪辑请求")
    
    # 创建批次ID和任务ID列表
    batch_id = str(uuid.uuid4())
    task_ids = []
    
    # 为每个剪辑请求创建任务
    for clip_request in request.clips:
        task_id = str(uuid.uuid4())
        task_ids.append(task_id)
        
        # 初始化任务状态
        tasks[task_id] = {
            "request": clip_request.dict(),
            "status": TaskStatus.PENDING,
            "start_time": time.time(),
            "progress": 0.0,
            "result": None,
            "message": "批量任务已创建，等待处理",
            "batch_id": batch_id
        }
    
    # 记录批次状态
    batch_tasks[batch_id] = {
        "task_ids": task_ids,
        "total": len(task_ids),
        "completed": 0,
        "status": TaskStatus.PENDING,
        "start_time": time.time(),
        "parallel": min(request.parallel, len(task_ids))
    }
    
    # 在后台处理批量任务
    background_tasks.add_task(
        process_batch_tasks,
        batch_id=batch_id
    )
    
    return BatchClipResponse(
        batch_id=batch_id,
        task_ids=task_ids,
        status=TaskStatus.PENDING,
        completed=0,
        total=len(task_ids),
        message="批量任务已创建，正在开始处理"
    )

@router.get("/batch/{batch_id}", response_model=BatchClipResponse)
async def get_batch_status(batch_id: str):
    """
    获取批量任务状态
    
    - 接收批次ID
    - 返回整体进度和任务列表
    """
    if batch_id not in batch_tasks:
        raise HTTPException(status_code=404, detail="批次任务不存在")
    
    batch_info = batch_tasks[batch_id]
    task_ids = batch_info["task_ids"]
    
    # 统计完成情况
    completed = sum(1 for task_id in task_ids if 
                   task_id in tasks and tasks[task_id]["status"] in 
                   [TaskStatus.SUCCESS, TaskStatus.FAILED])
    
    # 判断整体状态
    status = TaskStatus.PROCESSING
    if completed == batch_info["total"]:
        status = TaskStatus.SUCCESS
        # 检查是否有失败任务
        if any(task_id in tasks and tasks[task_id]["status"] == TaskStatus.FAILED 
              for task_id in task_ids):
            status = TaskStatus.FAILED
    
    # 更新批次信息
    batch_tasks[batch_id]["completed"] = completed
    batch_tasks[batch_id]["status"] = status
    
    return BatchClipResponse(
        batch_id=batch_id,
        task_ids=task_ids,
        status=status,
        completed=completed,
        total=batch_info["total"],
        message=f"已完成 {completed}/{batch_info['total']} 任务"
    )

@router.delete("/task/{task_id}", response_model=dict)
async def cancel_task(task_id: str):
    """
    取消正在进行的任务
    
    - 接收任务ID
    - 尝试取消任务处理
    - 返回取消状态
    """
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task_info = tasks[task_id]
    
    # 只能取消处理中或等待中的任务
    if task_info["status"] not in [TaskStatus.PENDING, TaskStatus.PROCESSING]:
        return {"success": False, "message": "任务已完成或失败，无法取消"}
    
    # 更新任务状态
    task_info["status"] = TaskStatus.FAILED
    task_info["message"] = "任务已取消"
    tasks[task_id] = task_info
    
    return {"success": True, "message": "任务已取消"}

@router.get("/models/status", response_model=Dict)
async def get_models_status():
    """
    获取模型状态
    
    - 返回中英文模型的可用性、大小、配置状态
    """
    zh_status = ModelSwitcher.check_model_status("zh")
    en_status = ModelSwitcher.check_model_status("en")
    
    return {
        "zh": {
            "available": zh_status.get("available", False),
            "size_mb": zh_status.get("size_mb", 0),
            "quantization": zh_status.get("quantization", "unknown"),
            "config_only": zh_status.get("config_only", False)
        },
        "en": {
            "available": en_status.get("available", False),
            "size_mb": en_status.get("size_mb", 0),
            "quantization": en_status.get("quantization", "unknown"),
            "config_only": en_status.get("config_only", True)  # 英文模型默认仅配置
        }
    }

# 后台任务处理函数
async def process_clip_task(task_id: str, request: ClipRequest):
    """
    处理单个剪辑任务的后台函数
    
    - 更新任务状态和进度
    - 调用核心剪辑生成器
    - 保存结果或错误信息
    """
    # 更新任务状态为处理中
    tasks[task_id]["status"] = TaskStatus.PROCESSING
    tasks[task_id]["message"] = "任务处理中"
    tasks[task_id]["progress"] = 0.05
    
    # 获取生成器实例
    generator = ClipGenerator()
    
    # 注册进度回调
    def progress_callback(progress: float):
        tasks[task_id]["progress"] = progress
    
    try:
        # 开始处理，附带进度回调
        result = await generator.generate_async(
            video_path=request.video_path,
            srt_path=request.srt_path,
            quant_level=request.quant_level,
            lang=request.lang,
            max_duration=request.max_duration,
            narrative_focus=request.narrative_focus,
            temperature=request.temperature,
            preserve_segments=request.preserve_segments,
            export_format=request.export_format,
            progress_callback=progress_callback
        )
        
        # 更新任务状态为成功
        end_time = time.time()
        render_time = end_time - tasks[task_id]["start_time"]
        
        tasks[task_id].update({
            "status": TaskStatus.SUCCESS,
            "progress": 1.0,
            "result": result,
            "message": "任务处理成功",
            "render_time": render_time
        })
        
        logger.info(f"任务 {task_id} 处理完成，用时: {render_time:.2f}s")
        
    except Exception as e:
        # 更新任务状态为失败
        tasks[task_id].update({
            "status": TaskStatus.FAILED,
            "progress": 0.0,
            "message": f"任务处理失败: {str(e)}"
        })
        
        logger.error(f"任务 {task_id} 处理失败: {str(e)}")

async def process_batch_tasks(batch_id: str):
    """
    处理批量任务的后台函数
    
    - 根据指定并行度处理多个任务
    - 更新批次和任务状态
    """
    batch_info = batch_tasks[batch_id]
    task_ids = batch_info["task_ids"]
    parallel = batch_info["parallel"]
    
    # 按指定并行度处理任务
    for i in range(0, len(task_ids), parallel):
        # 获取当前批次要处理的任务ID
        current_batch = task_ids[i:i+parallel]
        
        # 并行处理当前批次任务
        tasks_to_process = []
        for task_id in current_batch:
            if task_id in tasks:
                task_info = tasks[task_id]
                request = ClipRequest(**task_info["request"])
                task = process_clip_task(task_id, request)
                tasks_to_process.append(task)
        
        # 等待所有任务完成
        if tasks_to_process:
            await asyncio.gather(*tasks_to_process)
    
    # 更新批次状态
    completed = sum(1 for task_id in task_ids if 
                   task_id in tasks and tasks[task_id]["status"] in 
                   [TaskStatus.SUCCESS, TaskStatus.FAILED])
    
    # 判断整体状态
    status = TaskStatus.SUCCESS
    if any(task_id in tasks and tasks[task_id]["status"] == TaskStatus.FAILED 
          for task_id in task_ids):
        status = TaskStatus.FAILED
        
    batch_tasks[batch_id]["completed"] = completed
    batch_tasks[batch_id]["status"] = status 

# 添加时空折叠引擎API路由
@router.post("/nonlinear/fold", 
            summary="折叠时间轴", 
            description="将线性时间轴重构为非线性叙事结构")
async def api_fold_timeline(request: dict):
    """
    折叠时间轴
    
    接收场景列表和可选参数，返回折叠结果
    """
    try:
        scenes = request.get("scenes", [])
        anchors = request.get("anchors", None)
        structure_name = request.get("structure_name", None)
        strategy_name = request.get("strategy_name", None)
        folding_mode = request.get("folding_mode", None)
        
        result = fold_scenes(
            scenes, anchors, structure_name, strategy_name, folding_mode
        )
        
        return result
    
    except Exception as e:
        logger.error(f"API折叠时间轴失败: {str(e)}")
        return {"success": False, "error": str(e)}


@router.get("/nonlinear/strategies", 
           summary="获取折叠策略", 
           description="获取所有可用的折叠策略信息")
async def api_get_strategies():
    """
    获取所有可用的折叠策略信息
    """
    try:
        return get_folding_strategies_info()
    
    except Exception as e:
        logger.error(f"API获取折叠策略失败: {str(e)}")
        return {"success": False, "error": str(e)}


@router.get("/nonlinear/modes", 
           summary="获取折叠模式", 
           description="获取所有可用的折叠模式信息")
async def api_get_modes():
    """
    获取所有可用的折叠模式信息
    """
    try:
        return get_folding_modes_info()
    
    except Exception as e:
        logger.error(f"API获取折叠模式失败: {str(e)}")
        return {"success": False, "error": str(e)}


@router.post("/nonlinear/estimate", 
            summary="估算折叠结果", 
            description="估算折叠结果，不执行实际折叠")
async def api_estimate_folding(request: dict):
    """
    估算折叠结果
    
    接收场景列表和可选参数，返回估算结果
    """
    try:
        scenes = request.get("scenes", [])
        structure_name = request.get("structure_name", None)
        folding_mode = request.get("folding_mode", None)
        
        result = estimate_folding_result(
            scenes, structure_name, folding_mode
        )
        
        return result
    
    except Exception as e:
        logger.error(f"API估算折叠结果失败: {str(e)}")
        return {"success": False, "error": str(e)}

# 增量更新接口
@router.post("/delta/broadcast")
async def broadcast_delta(session_id: str, delta: Dict[str, Any]):
    """广播增量更新
    
    Args:
        session_id: 会话ID
        delta: 增量更新数据
    """
    if not _delta_broadcaster:
        raise HTTPException(status_code=503, detail="增量更新广播器未初始化")
    
    try:
        await _delta_broadcaster.broadcast_changes(session_id, delta)
        return {"success": True, "message": "增量更新已广播"}
    except Exception as e:
        logger.error(f"广播增量更新失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"广播增量更新失败: {str(e)}")

@router.post("/delta/subscribe")
async def subscribe_session(channel: str, session_id: str):
    """为会话订阅频道
    
    Args:
        channel: 频道名
        session_id: 会话ID
    """
    if not _delta_broadcaster:
        raise HTTPException(status_code=503, detail="增量更新广播器未初始化")
    
    try:
        success = await _delta_broadcaster.subscribe_session(channel, session_id)
        if success:
            return {"success": True, "message": f"会话 {session_id} 已订阅频道 {channel}"}
        else:
            raise HTTPException(status_code=400, detail="订阅失败，广播器可能未启动")
    except Exception as e:
        logger.error(f"订阅频道失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"订阅频道失败: {str(e)}")

@router.post("/delta/unsubscribe")
async def unsubscribe_session(channel: str, session_id: str):
    """取消会话的频道订阅
    
    Args:
        channel: 频道名
        session_id: 会话ID
    """
    if not _delta_broadcaster:
        raise HTTPException(status_code=503, detail="增量更新广播器未初始化")
    
    try:
        success = await _delta_broadcaster.unsubscribe_session(channel, session_id)
        if success:
            return {"success": True, "message": f"会话 {session_id} 已取消订阅频道 {channel}"}
        else:
            raise HTTPException(status_code=400, detail="取消订阅失败，会话或频道不存在")
    except Exception as e:
        logger.error(f"取消订阅频道失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"取消订阅频道失败: {str(e)}") 