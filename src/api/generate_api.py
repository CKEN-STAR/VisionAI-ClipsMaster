from fastapi import APIRouter, HTTPException
from .schema import ClipRequest, ClipResponse
from ..core.clip_generator import ClipGenerator
from ..core.model_switcher import ModelSwitcher
import time
import os
from loguru import logger

router = APIRouter()

@router.post("/api/v1/generate", response_model=ClipResponse)
async def generate_clip(request: ClipRequest):
    """
    生成视频剪辑接口（异步，RESTful 完善实现）
    """
    # 路径校验
    if not os.path.exists(request.video_path):
        raise HTTPException(status_code=400, detail="视频文件不存在")
    if not os.path.exists(request.srt_path):
        raise HTTPException(status_code=400, detail="字幕文件不存在")

    # 检查模型配置
    if request.lang == "en":
        model_status = ModelSwitcher.check_model_status("en")
        if not model_status.get("available", False):
            raise HTTPException(status_code=400, detail="英文模型未下载，仅配置。请下载模型后重试。")
    
    generator = ClipGenerator()
    start_time = time.time()
    try:
        # 性能日志
        logger.info(f"开始处理: {request.video_path}, {request.srt_path}, lang={request.lang}, quant={request.quant_level}")
        project_path = await generator.generate_async(
            video_path=request.video_path,
            srt_path=request.srt_path,
            quant_level=request.quant_level,
            lang=request.lang
        )
        render_time = time.time() - start_time
        logger.info(f"处理完成: {project_path}, 用时: {render_time:.2f}s")
        return ClipResponse(
            project_path=project_path,
            render_time=render_time,
            status="success",
            message="剪辑生成成功"
        )
    except Exception as e:
        logger.error(f"生成失败: {str(e)}")
        return ClipResponse(
            project_path="",
            render_time=0.0,
            status="failed",
            message=str(e)
        ) 