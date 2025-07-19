#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
灰度发布系统API

提供灰度发布系统的REST API接口，支持版本控制、发布管理和指标收集等功能。
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Union
from fastapi import APIRouter, HTTPException, Query, Body, Path, Depends

from src.versioning import (
    CanaryDeployer,
    UserGroup,
    ReleaseStage,
    VersionStatus
)

# 创建日志记录器
logger = logging.getLogger("canary_api")

# 创建路由
router = APIRouter(prefix="/api/canary", tags=["canary"])

# 全局部署器实例
_deployer = None

def get_deployer() -> CanaryDeployer:
    """获取或创建灰度发布管理器实例
    
    Returns:
        CanaryDeployer实例
    """
    global _deployer
    
    if _deployer is None:
        db_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "data", "canary_release_db.json"
        )
        _deployer = CanaryDeployer(db_path)
    
    return _deployer

# API路由定义
@router.post("/releases")
async def create_release(
    release_id: str = Body(..., description="发布计划ID"),
    name: str = Body(..., description="发布计划名称"),
    versions: List[str] = Body(..., description="版本ID列表"),
    description: str = Body("", description="发布计划描述"),
    stage: str = Body(ReleaseStage.ALPHA, description="发布阶段"),
    deployer: CanaryDeployer = Depends(get_deployer)
):
    """创建新的灰度发布计划"""
    result = deployer.create_release(
        release_id=release_id,
        name=name,
        versions=versions,
        description=description,
        stage=stage
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result

@router.get("/releases")
async def list_releases(
    status: Optional[str] = Query(None, description="按状态筛选"),
    deployer: CanaryDeployer = Depends(get_deployer)
):
    """列出所有发布计划"""
    return deployer.list_releases(status)

@router.get("/releases/{release_id}")
async def get_release(
    release_id: str = Path(..., description="发布计划ID"),
    deployer: CanaryDeployer = Depends(get_deployer)
):
    """获取发布计划详情"""
    result = deployer.get_release_info(release_id)
    
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["message"])
    
    return result

@router.post("/releases/{release_id}/deploy")
async def deploy_release(
    release_id: str = Path(..., description="发布计划ID"),
    user_groups: List[str] = Body(..., description="目标用户组列表"),
    deployer: CanaryDeployer = Depends(get_deployer)
):
    """执行灰度发布"""
    result = deployer.gradual_release(release_id, user_groups)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result

@router.post("/releases/{release_id}/status")
async def update_release_status(
    release_id: str = Path(..., description="发布计划ID"),
    status: str = Body(..., description="新状态"),
    deployer: CanaryDeployer = Depends(get_deployer)
):
    """更新发布计划状态"""
    result = deployer.update_release_status(release_id, status)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result

@router.post("/releases/{release_id}/rollback")
async def rollback_release(
    release_id: str = Path(..., description="发布计划ID"),
    target_version: Optional[str] = Body(None, description="目标回滚版本"),
    deployer: CanaryDeployer = Depends(get_deployer)
):
    """回滚发布"""
    result = deployer.rollback_release(release_id, target_version)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result

@router.post("/metrics")
async def report_metrics(
    deployment_id: str = Body(..., description="部署ID"),
    success: bool = Body(..., description="是否成功"),
    error_message: Optional[str] = Body(None, description="错误信息"),
    user_id: Optional[str] = Body(None, description="用户ID"),
    deployer: CanaryDeployer = Depends(get_deployer)
):
    """报告指标数据"""
    result = deployer.report_metrics(deployment_id, success, error_message, user_id)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result

@router.get("/user_version")
async def get_user_version(
    user_id: str = Query(..., description="用户ID"),
    release_id: Optional[str] = Query(None, description="发布计划ID"),
    deployer: CanaryDeployer = Depends(get_deployer)
):
    """获取用户应使用的版本"""
    result = deployer.get_user_version(user_id, release_id)
    
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["message"])
    
    return result

@router.get("/user_groups")
async def get_user_groups():
    """获取所有用户组"""
    return {
        "user_groups": UserGroup.get_all_groups()
    }

@router.get("/version_statuses")
async def get_version_statuses():
    """获取所有版本状态"""
    return {
        "statuses": [
            VersionStatus.PENDING,
            VersionStatus.RELEASING,
            VersionStatus.RELEASED,
            VersionStatus.SUSPENDED,
            VersionStatus.DEPRECATED,
            VersionStatus.ROLLBACKED
        ]
    }

@router.get("/release_stages")
async def get_release_stages():
    """获取所有发布阶段"""
    return {
        "stages": [
            ReleaseStage.ALPHA,
            ReleaseStage.BETA,
            ReleaseStage.STABLE,
            ReleaseStage.ROLLBACK
        ]
    } 