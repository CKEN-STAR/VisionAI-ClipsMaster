"""硬件设置API

提供硬件降级策略和系统资源管理的API接口
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from loguru import logger

from src.core.hardware_manager import (
    get_hardware_strategy,
    set_adaptive_mode,
    get_hardware_status,
    optimize_for_language
)
from src.core.hardware_degradation_strategy import AdaptiveMode
from src.api.security import validate_api_key

router = APIRouter(
    prefix="/api/v1/hardware",
    tags=["hardware"],
    dependencies=[Depends(validate_api_key)],
    responses={404: {"description": "Not found"}},
)


class AdaptiveModeRequest(BaseModel):
    """自适应模式请求模型"""
    mode: str


class LanguageOptimizationRequest(BaseModel):
    """语言优化请求模型"""
    language: str  # "zh" 或 "en"


@router.get("/status", response_model=Dict[str, Any])
async def get_status():
    """获取硬件状态信息"""
    if get_hardware_strategy() is None:
        raise HTTPException(status_code=500, detail="硬件策略管理器未初始化")
    
    return get_hardware_status()


@router.post("/mode", response_model=Dict[str, Any])
async def change_adaptive_mode(request: AdaptiveModeRequest):
    """更改自适应模式"""
    if get_hardware_strategy() is None:
        raise HTTPException(status_code=500, detail="硬件策略管理器未初始化")
    
    try:
        mode = AdaptiveMode(request.mode)
    except ValueError:
        valid_modes = [m.value for m in AdaptiveMode]
        raise HTTPException(
            status_code=400, 
            detail=f"无效的自适应模式: {request.mode}，有效模式: {valid_modes}"
        )
    
    success = set_adaptive_mode(mode)
    if not success:
        raise HTTPException(status_code=500, detail="设置自适应模式失败")
    
    return {
        "success": True,
        "mode": mode.value,
        "status": get_hardware_status()
    }


@router.post("/optimize-language", response_model=Dict[str, Any])
async def optimize_for_language_endpoint(request: LanguageOptimizationRequest):
    """为特定语言优化硬件设置"""
    if get_hardware_strategy() is None:
        raise HTTPException(status_code=500, detail="硬件策略管理器未初始化")
    
    if request.language not in ["zh", "en"]:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的语言: {request.language}，支持的语言: zh, en"
        )
    
    result = optimize_for_language(request.language)
    if not result.get("success", False):
        raise HTTPException(
            status_code=500,
            detail=f"优化失败: {result.get('error', '未知错误')}"
        )
    
    return {
        "success": True,
        "language": request.language,
        "optimized_settings": result.get("optimized_settings", {}),
        "status": get_hardware_status()
    }


@router.get("/available-modes", response_model=List[str])
async def get_available_modes():
    """获取可用的自适应模式"""
    return [mode.value for mode in AdaptiveMode]


@router.post("/reset", response_model=Dict[str, Any])
async def reset_hardware_strategy():
    """重置硬件策略设置"""
    strategy = get_hardware_strategy()
    if strategy is None:
        raise HTTPException(status_code=500, detail="硬件策略管理器未初始化")
    
    try:
        strategy.reset()
        return {
            "success": True,
            "message": "硬件策略已重置",
            "status": get_hardware_status()
        }
    except Exception as e:
        logger.error(f"重置硬件策略失败: {e}")
        raise HTTPException(status_code=500, detail=f"重置失败: {str(e)}")


@router.get("/memory", response_model=Dict[str, Any])
async def get_memory_stats():
    """获取内存使用统计"""
    strategy = get_hardware_strategy()
    if strategy is None:
        raise HTTPException(status_code=500, detail="硬件策略管理器未初始化")
    
    try:
        memory_stats = strategy._get_memory_info()
        memory_manager_stats = strategy.memory_manager.get_memory_usage()
        
        return {
            "system_memory": memory_stats,
            "managed_memory": memory_manager_stats,
            "degradation_level": strategy.degradation_manager.get_state()["level"]
        }
    except Exception as e:
        logger.error(f"获取内存统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取内存统计失败: {str(e)}") 