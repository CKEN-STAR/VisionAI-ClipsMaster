"""分片策略配置API模块

此模块提供分片策略配置的REST API接口，包括：
1. 查询当前分片策略
2. 切换分片策略
3. 获取模型特定分片配置
4. 更新模型分片配置
5. 获取分片策略历史记录
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Path, Body
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field

from src.core.shard_policy_manager import ShardPolicyManager

# 创建路由器
router = APIRouter(
    prefix="/api/shard-policy",
    tags=["shard-policy"],
    responses={404: {"description": "Not found"}},
)

# 创建分片策略管理器实例
shard_manager = ShardPolicyManager()


# 数据模型
class StrategyUpdate(BaseModel):
    """分片策略更新模型"""
    strategy_name: str = Field(..., description="策略名称")
    reason: Optional[str] = Field("手动切换", description="更新原因")


class ModelSettings(BaseModel):
    """模型特定设置更新模型"""
    model_name: str = Field(..., description="模型名称")
    settings: Dict[str, Any] = Field(..., description="模型设置")


class LayerDependency(BaseModel):
    """层依赖关系模型"""
    name: str = Field(..., description="层名称")
    next: List[str] = Field(..., description="下一层列表")


class ShardingPlanRequest(BaseModel):
    """分片计划请求模型"""
    model_name: str = Field(..., description="模型名称")
    model_size: int = Field(..., description="模型大小(字节)")


# API端点

@router.get("/")
async def get_shard_policy_info():
    """获取分片策略配置信息摘要"""
    return shard_manager.get_configuration_summary()


@router.get("/current")
async def get_current_strategy():
    """获取当前使用的分片策略"""
    return shard_manager.get_current_strategy()


@router.get("/all")
async def get_all_strategies():
    """获取所有可用的分片策略"""
    return shard_manager.get_all_strategies()


@router.post("/apply")
async def apply_strategy(strategy_update: StrategyUpdate):
    """应用指定的分片策略
    
    - **strategy_name**: 策略名称
    - **reason**: 更新原因(可选)
    """
    success = shard_manager.apply_strategy(
        strategy_update.strategy_name, 
        strategy_update.reason
    )
    
    if not success:
        raise HTTPException(
            status_code=400, 
            detail=f"应用策略 '{strategy_update.strategy_name}' 失败"
        )
    
    return {"success": True, "strategy": strategy_update.strategy_name}


@router.get("/model/{model_name}")
async def get_model_settings(model_name: str = Path(..., description="模型名称")):
    """获取特定模型的分片设置"""
    settings = shard_manager.get_model_specific_settings(model_name)
    if not settings:
        return {"model_name": model_name, "has_custom_settings": False}
    return settings


@router.post("/model/update")
async def update_model_settings(model_settings: ModelSettings):
    """更新特定模型的分片设置
    
    - **model_name**: 模型名称
    - **settings**: 模型设置
    """
    success = shard_manager.update_model_settings(
        model_settings.model_name, 
        model_settings.settings
    )
    
    if not success:
        raise HTTPException(
            status_code=400, 
            detail=f"更新模型 '{model_settings.model_name}' 设置失败"
        )
    
    return {"success": True, "model_name": model_settings.model_name}


@router.get("/dependencies")
async def get_layer_dependencies():
    """获取模型层依赖关系配置"""
    return shard_manager.get_layer_dependencies()


@router.post("/dependencies/update")
async def update_layer_dependencies(dependencies: List[LayerDependency]):
    """更新模型层依赖关系
    
    - **dependencies**: 层依赖关系列表
    """
    # 转换为字典列表
    dependencies_dict = [dep.dict() for dep in dependencies]
    
    success = shard_manager.update_layer_dependencies(dependencies_dict)
    if not success:
        raise HTTPException(
            status_code=400, 
            detail="更新层依赖关系失败"
        )
    
    return {"success": True, "count": len(dependencies)}


@router.get("/history")
async def get_strategy_history():
    """获取分片策略变更历史"""
    return shard_manager.get_strategy_history()


@router.post("/evaluate")
async def evaluate_conditions():
    """评估当前系统条件，检查是否需要调整分片策略"""
    needs_adjustment, suggested_strategy, reason = shard_manager.evaluate_current_conditions()
    
    return {
        "needs_adjustment": needs_adjustment,
        "suggested_strategy": suggested_strategy,
        "reason": reason,
        "current_strategy": shard_manager.current_strategy
    }


@router.post("/adjust")
async def adjust_if_needed():
    """如有必要，自动调整分片策略"""
    adjusted = shard_manager.adjust_if_needed()
    
    if adjusted:
        current = shard_manager.get_current_strategy()
        return {
            "adjusted": True,
            "current_strategy": current["name"],
            "description": current["desc"]
        }
    
    return {"adjusted": False, "current_strategy": shard_manager.current_strategy}


@router.post("/sharding-plan")
async def generate_sharding_plan(request: ShardingPlanRequest):
    """生成模型分片计划
    
    - **model_name**: 模型名称
    - **model_size**: 模型大小(字节)
    """
    plan = shard_manager.generate_sharding_plan(request.model_name, request.model_size)
    return plan


@router.get("/best-strategy/{model_name}")
async def get_best_strategy_for_model(model_name: str = Path(..., description="模型名称")):
    """为特定模型获取当前系统条件下最佳分片策略"""
    strategy_name = shard_manager.select_strategy_for_model(model_name)
    strategy = shard_manager.get_current_strategy() if strategy_name == shard_manager.current_strategy else shard_manager._get_strategy_by_name(strategy_name)
    
    return {
        "model_name": model_name,
        "best_strategy": strategy_name,
        "strategy_details": strategy,
        "is_current": strategy_name == shard_manager.current_strategy
    } 