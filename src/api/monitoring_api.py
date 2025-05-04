"""
API性能监控端点

提供以下功能：
1. 获取当前性能统计信息
2. 重置统计数据
3. 导出统计数据
4. 健康检查
5. Prometheus指标导出
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks, Request, Response
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel

from src.utils.api_monitoring import get_api_monitor
from loguru import logger

# 创建路由处理器
router = APIRouter(prefix="/api/v1/monitoring", tags=["monitoring"])

# 数据模型
class TimeWindowQuery(BaseModel):
    """时间窗口查询参数"""
    minutes: Optional[int] = None


class ExportRequest(BaseModel):
    """导出请求参数"""
    output_path: Optional[str] = None
    format: str = "json"  # json, csv


class ApiMetrics(BaseModel):
    """API性能指标响应模型"""
    uptime: float
    time_since_reset: float
    endpoints: Dict[str, Any]
    system: Dict[str, Any]
    timestamp: str


@router.get("/metrics", response_model=ApiMetrics)
async def get_metrics(time_window: Optional[int] = None):
    """
    获取API性能指标
    
    Args:
        time_window: 可选的时间窗口(分钟)，如果提供，则只返回该时间窗口内的统计数据
    
    Returns:
        API性能指标
    """
    monitor = get_api_monitor()
    stats = monitor.get_statistics(time_window)
    
    # 添加时间戳
    stats["timestamp"] = datetime.now().isoformat()
    
    return JSONResponse(content=stats)


@router.post("/reset")
async def reset_metrics():
    """
    重置所有性能统计数据
    
    Returns:
        成功消息
    """
    monitor = get_api_monitor()
    monitor.reset_statistics()
    
    return {"message": "性能统计数据已重置", "reset_time": datetime.now().isoformat()}


@router.post("/export")
async def export_metrics(
    request: ExportRequest,
    background_tasks: BackgroundTasks
):
    """
    导出性能统计数据
    
    Args:
        request: 导出请求参数
    
    Returns:
        导出状态
    """
    monitor = get_api_monitor()
    
    # 使用默认输出路径(如果未提供)
    if not request.output_path:
        os.makedirs("logs/exports", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        request.output_path = f"logs/exports/api_metrics_{timestamp}.{request.format}"
    
    # 确保输出目录存在
    os.makedirs(os.path.dirname(request.output_path), exist_ok=True)
    
    # 在后台执行导出(避免阻塞API)
    def export_task():
        try:
            if request.format.lower() == "json":
                success = monitor.export_statistics(request.output_path)
            else:
                # 暂不支持其他格式
                logger.error(f"不支持的导出格式: {request.format}")
                return
                
            if not success:
                logger.error(f"导出统计数据失败: {request.output_path}")
        except Exception as e:
            logger.error(f"导出过程异常: {e}")
    
    background_tasks.add_task(export_task)
    
    return {
        "message": "性能统计数据导出已开始",
        "export_time": datetime.now().isoformat(),
        "output_path": request.output_path
    }


@router.get("/download/{timestamp}")
async def download_metrics(timestamp: str):
    """
    下载指定时间戳的性能统计数据
    
    Args:
        timestamp: 导出时间戳(格式: YYYYMMDD_HHMMSS)
    
    Returns:
        文件下载响应
    """
    file_path = f"logs/exports/api_metrics_{timestamp}.json"
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="找不到该导出文件")
    
    return FileResponse(
        path=file_path,
        filename=f"api_metrics_{timestamp}.json",
        media_type="application/json"
    )


@router.get("/health")
async def health_check():
    """
    API健康检查端点
    
    Returns:
        健康状态信息
    """
    monitor = get_api_monitor()
    stats = monitor.get_statistics()
    
    # 计算整体健康状态
    status = "healthy"
    issues = []
    
    # 检查内存使用
    memory_usage = stats["system"]["memory"]["current"]
    memory_total = os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES')  # 系统总内存
    memory_percent = memory_usage / memory_total * 100
    
    if memory_percent > 90:
        status = "critical"
        issues.append("内存使用率超过90%")
    elif memory_percent > 75:
        status = "warning" if status != "critical" else status
        issues.append("内存使用率超过75%")
    
    # 检查CPU使用
    cpu_percent = stats["system"]["cpu"]["current"]
    if cpu_percent > 90:
        status = "critical"
        issues.append("CPU使用率超过90%")
    elif cpu_percent > 75:
        status = "warning" if status != "critical" else status
        issues.append("CPU使用率超过75%")
    
    # 检查错误率
    high_error_endpoints = []
    for endpoint, data in stats.get("endpoints", {}).items():
        success = data["requests"]["success"]
        error = data["requests"]["error"]
        total = success + error
        if total > 0 and error / total > 0.1:  # 错误率>10%
            high_error_endpoints.append(endpoint)
    
    if high_error_endpoints:
        status = "warning" if status != "critical" else status
        issues.append(f"高错误率端点: {', '.join(high_error_endpoints)}")
    
    return {
        "status": status,
        "uptime": stats["uptime"],
        "issues": issues,
        "timestamp": datetime.now().isoformat()
    }


# 如果启用了Prometheus，添加指标导出端点
try:
    from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
    
    @router.get("/prometheus", include_in_schema=False)
    async def metrics_prometheus(request: Request):
        """导出Prometheus格式的指标"""
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
        
except ImportError:
    # 如果Prometheus不可用，则忽略此端点
    pass 