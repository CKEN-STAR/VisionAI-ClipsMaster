#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据仪表板API接口模块

提供REST API接口，用于查询数据源状态、系统指标和测试结果，
支持JSON格式响应，适合轻量级应用和混沌工程测试。
"""

import time
import json
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

# 创建日志记录器
logger = logging.getLogger("dashboard_api")

# 导入数据聚合器
from .data_integration import DataAggregator, fetch_data_sources_status
from .visualizer import generate_system_report


class DashboardAPI:
    """数据仪表板API接口类，提供HTTP API端点"""
    
    def __init__(self):
        """初始化API接口"""
        self.aggregator = DataAggregator()
        self.logger = logger
        
        # 启动数据自动更新
        self.aggregator.start_auto_update(interval_seconds=30)
    
    def get_data_sources(self) -> Dict[str, Any]:
        """获取所有数据源状态
        
        Returns:
            Dict: 数据源状态信息
        """
        return fetch_data_sources_status()
    
    def get_source_data(self, source_name: str) -> Dict[str, Any]:
        """获取指定数据源的详细数据
        
        Args:
            source_name: 数据源名称
            
        Returns:
            Dict: 数据源详细数据
        """
        if source_name not in self.aggregator.SOURCES:
            return {
                "status": "error",
                "error": f"未知数据源: {source_name}",
                "timestamp": time.time()
            }
            
        data = self.aggregator.get_cached_data(source_name)
        
        return {
            "status": "ok",
            "source": source_name,
            "timestamp": time.time(),
            "data": data
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统健康状态
        
        Returns:
            Dict: 系统健康状态
        """
        # 获取健康状态报告
        health_status = self.aggregator.get_health_status()
        
        # 获取系统资源使用情况
        system_data = self.aggregator.get_cached_data("system")
        system_metrics = system_data.get("system_metrics", {})
        
        # 简化的系统状态报告
        status = {
            "status": health_status.get("status", "unknown"),
            "timestamp": time.time(),
            "datetime": datetime.now().isoformat(),
            "resources": {
                "memory": system_metrics.get("memory", {}),
                "cpu": system_metrics.get("cpu", {}),
                "disk": system_metrics.get("disk", {})
            },
            "sources": {}
        }
        
        # 添加数据源状态摘要
        for source_name, source_status in health_status.get("sources", {}).items():
            status["sources"][source_name] = {
                "status": source_status.get("status", "unknown"),
                "healthy": source_status.get("healthy", False)
            }
            
        return status
    
    def get_system_report(self) -> Dict[str, Any]:
        """获取完整系统报告
        
        Returns:
            Dict: 完整系统报告
        """
        return generate_system_report()
    
    def get_cache_metrics(self) -> Dict[str, Any]:
        """获取缓存指标
        
        Returns:
            Dict: 缓存指标数据
        """
        cache_data = self.aggregator.get_cached_data("cache")
        
        return {
            "status": "ok",
            "timestamp": time.time(),
            "datetime": datetime.now().isoformat(),
            "metrics": cache_data.get("cache_metrics", {})
        }
    
    def get_model_metrics(self) -> Dict[str, Any]:
        """获取模型性能指标
        
        Returns:
            Dict: 模型性能指标
        """
        model_data = self.aggregator.get_cached_data("models")
        
        return {
            "status": "ok",
            "timestamp": time.time(),
            "datetime": datetime.now().isoformat(),
            "metrics": model_data.get("model_metrics", {})
        }
    
    def stop(self):
        """停止API服务"""
        self.aggregator.stop_auto_update()
        self.logger.info("API服务已停止")


# API路由映射
api_routes = {
    "/data_sources": "get_data_sources",
    "/source/{source_name}": "get_source_data",
    "/system/status": "get_system_status",
    "/system/report": "get_system_report",
    "/cache/metrics": "get_cache_metrics",
    "/models/metrics": "get_model_metrics"
}


def get_dashboard_api() -> DashboardAPI:
    """获取仪表板API实例
    
    Returns:
        DashboardAPI: API接口实例
    """
    return DashboardAPI()


# 与框架集成的API处理函数
def api_handler(route: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
    """通用API处理函数
    
    Args:
        route: API路由路径
        params: 请求参数
        
    Returns:
        Dict: API响应
    """
    api = get_dashboard_api()
    params = params or {}
    
    # 按路由分发请求
    if route == "/data_sources":
        return api.get_data_sources()
    elif route.startswith("/source/"):
        source_name = route.split("/")[-1]
        return api.get_source_data(source_name)
    elif route == "/system/status":
        return api.get_system_status()
    elif route == "/system/report":
        return api.get_system_report()
    elif route == "/cache/metrics":
        return api.get_cache_metrics()
    elif route == "/models/metrics":
        return api.get_model_metrics()
    else:
        return {
            "status": "error",
            "error": f"未知路由: {route}",
            "timestamp": time.time()
        }


if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # 模拟API请求
    print("\n== 测试API接口 ==")
    api = get_dashboard_api()
    
    print("\n1. 获取数据源状态:")
    response = api.get_data_sources()
    print(f"状态: {response['status']}")
    print(f"数据源数量: {len(response['sources'])}")
    
    print("\n2. 获取系统状态:")
    response = api.get_system_status()
    print(f"系统状态: {response['status']}")
    if "resources" in response and "memory" in response["resources"]:
        memory = response["resources"]["memory"]
        print(f"内存使用率: {memory.get('percent', 'N/A')}%")
    
    # 停止API服务
    api.stop() 