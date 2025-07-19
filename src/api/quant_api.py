#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
量化策略管理API

提供量化策略配置调整、状态查询和性能分析功能
"""

import os
import json
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Body, Query
from pydantic import BaseModel, Field
import logging

from src.utils.quant_config_loader import get_quant_config
from src.quant.quant_decision import quant_decision_engine
from src.quant.quant_switcher import QuantSwitcher
from src.memory.quant_logger import get_quant_logger, log_strategy_change

# 创建日志
logger = logging.getLogger("quant_api")

# 创建路由
router = APIRouter(prefix="/api/quant", tags=["quantization"])

# 创建全局量化切换器
_quant_switcher = None

def get_quant_switcher():
    """获取或创建量化切换器实例"""
    global _quant_switcher
    if _quant_switcher is None:
        _quant_switcher = QuantSwitcher()
    return _quant_switcher


# 定义数据模型
class QuantConfig(BaseModel):
    """量化配置模型"""
    new_rules: Dict[str, Any] = Field(..., description="新的量化规则配置")


class QuantStatusResponse(BaseModel):
    """量化状态响应"""
    current_level: str = Field(..., description="当前使用的量化级别")
    available_levels: List[str] = Field(..., description="可用的量化级别列表")
    memory_usage: Dict[str, float] = Field(..., description="当前内存使用情况(MB)")
    auto_select: bool = Field(..., description="是否启用自动选择")


class ThresholdUpdate(BaseModel):
    """阈值更新请求"""
    level_name: str = Field(..., description="量化级别名称")
    threshold_name: str = Field(..., description="阈值名称")
    value: float = Field(..., description="新阈值值")


class StrategyResponse(BaseModel):
    """策略调整响应"""
    status: str = Field(..., description="操作状态")
    message: str = Field(None, description="详细信息")
    updated_rules: Dict[str, Any] = Field(None, description="更新后的规则")


@router.get("/status", response_model=QuantStatusResponse)
async def get_quant_status():
    """
    获取当前量化状态
    
    返回当前使用的量化级别、可用级别列表和内存使用情况
    """
    quant_config = get_quant_config()
    quant_switcher = get_quant_switcher()
    
    # 获取内存信息
    memory_info = quant_switcher.memory_guard.get_memory_info()
    memory_usage = {
        "total": memory_info["total"] / (1024 * 1024),  # MB
        "used": memory_info["used"] / (1024 * 1024),    # MB
        "available": memory_info["available"] / (1024 * 1024)  # MB
    }
    
    return {
        "current_level": quant_switcher.current_quant or quant_config.get_default_level(),
        "available_levels": quant_config.get_quant_level_names(),
        "memory_usage": memory_usage,
        "auto_select": quant_config.is_auto_select_enabled()
    }


@router.post("/adjust_strategy", response_model=StrategyResponse)
async def adjust_strategy(config: QuantConfig):
    """
    调整量化策略
    
    允许用户配置量化阈值和规则，从而调整模型的内存使用和性能平衡
    """
    try:
        # 记录原始规则(用于对比)
        quant_config = get_quant_config()
        old_config = quant_config.get_config()
        
        # 更新规则(这里只是示例，实际中可能需要修改配置文件)
        # 在更复杂的实现中，应当考虑持久化存储这些规则
        updated_rules = {}
        
        # 处理阈值规则
        if "Q4_K_M_threshold" in config.new_rules:
            updated_rules["Q4_K_M_threshold"] = config.new_rules["Q4_K_M_threshold"]
            
            # 更新自动选择阈值
            auto_thresholds = old_config.get("auto_select_thresholds", {})
            auto_thresholds["normal"] = config.new_rules["Q4_K_M_threshold"]
            
            # 动态更新量化决策引擎
            quant_decision_engine.update_thresholds({
                "normal": config.new_rules["Q4_K_M_threshold"]
            })
        
        # 处理其他规则
        for rule_name, value in config.new_rules.items():
            if rule_name not in updated_rules:
                updated_rules[rule_name] = value
        
        # 记录策略变更
        log_strategy_change(
            None,  # 没有真实的级别变更
            "config_update",
            {
                "reason": "user_adjustment",
                "config_changes": updated_rules
            }
        )
        
        return {
            "status": "策略已更新",
            "updated_rules": updated_rules
        }
        
    except Exception as e:
        logger.error(f"调整量化策略失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"调整策略失败: {str(e)}")


@router.post("/switch_level", response_model=StrategyResponse)
async def switch_quant_level(level: str = Body(..., embed=True)):
    """
    手动切换量化级别
    
    允许用户直接指定要使用的量化级别
    """
    quant_switcher = get_quant_switcher()
    quant_config = get_quant_config()
    
    # 检查级别是否有效
    available_levels = quant_config.get_quant_level_names()
    if level not in available_levels:
        raise HTTPException(
            status_code=400, 
            detail=f"无效的量化级别。可用级别: {', '.join(available_levels)}"
        )
    
    # 执行切换
    success = quant_switcher.switch(level)
    
    if success:
        return {
            "status": "success",
            "message": f"已切换到量化级别: {level}"
        }
    else:
        raise HTTPException(
            status_code=500,
            detail="切换量化级别失败"
        )


@router.get("/history", response_model=List[Dict[str, Any]])
async def get_strategy_history(
    limit: int = Query(20, description="返回记录的最大数量"),
    reason: Optional[str] = Query(None, description="筛选特定的变更原因")
):
    """
    获取量化策略变更历史
    
    返回最近的量化策略变更记录，可以按原因筛选
    """
    quant_logger = get_quant_logger()
    records = quant_logger.get_records(limit=limit, reason=reason)
    
    return records


@router.get("/analytics", response_model=Dict[str, Any])
async def get_strategy_analytics():
    """
    获取量化策略分析报告
    
    返回策略使用统计、性能分析和推荐配置
    """
    from src.memory.quant_logger import get_strategy_analytics
    
    analytics = get_strategy_analytics()
    return analytics


@router.get("/best_strategies", response_model=List[Dict[str, Any]])
async def get_best_strategies(top_n: int = Query(3, description="返回的最佳策略数量")):
    """
    获取效果最好的量化策略
    
    根据历史数据分析，返回表现最佳的量化策略
    """
    from src.memory.quant_logger import get_best_strategies
    
    best = get_best_strategies(top_n)
    return best


def register_quant_api(app):
    """
    注册量化API到FastAPI应用
    
    Args:
        app: FastAPI应用实例
    """
    app.include_router(router) 