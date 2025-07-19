"""
API监控中间件

该中间件拦截所有API请求，收集性能指标，并将数据记录到APIMonitor中。
实现以下核心功能：
1. 响应时间测量
2. 请求成功/失败记录
3. 资源使用情况监控
4. 异常跟踪
"""

import time
from typing import Callable, Dict, Any
from fastapi import FastAPI, Request, Response
from fastapi.routing import APIRoute
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from src.utils.api_monitoring import get_api_monitor
from src.utils.log_handler import LogHandler
from loguru import logger

log_handler = LogHandler()

class APIMonitorMiddleware(BaseHTTPMiddleware):
    """API监控中间件，用于收集API性能指标"""
    
    def __init__(
        self, 
        app: ASGIApp, 
        influx_config: Dict[str, Any] = None,
        exclude_paths: list = None
    ):
        """
        初始化中间件
        
        Args:
            app: ASGI应用
            influx_config: InfluxDB配置，默认为None
            exclude_paths: 排除监控的路径列表，默认为None
        """
        super().__init__(app)
        self.api_monitor = get_api_monitor(influx_config)
        self.exclude_paths = exclude_paths or []
        logger.info("API监控中间件已初始化")
    
    async def dispatch(self, request: Request, call_next):
        """
        处理请求并收集性能指标
        
        Args:
            request: 请求对象
            call_next: 下一个中间件的调用函数
            
        Returns:
            响应对象
        """
        # 跳过不需要监控的路径
        path = request.url.path
        if any(path.startswith(exclude) for exclude in self.exclude_paths):
            return await call_next(request)
        
        # 记录请求开始时间
        start_time = time.time()
        
        # 记录请求信息
        client_host = request.client.host if request.client else "unknown"
        method = request.method
        endpoint = path
        
        # 资源使用基准
        response = None
        status_code = 500  # 默认状态码，如果出现异常
        
        try:
            # 执行请求
            response = await call_next(request)
            status_code = response.status_code
            
            # 计算处理时间
            duration = (time.time() - start_time) * 1000  # 转换为毫秒
            
            # 记录请求详情
            log_handler.log_performance_metric(
                metric_name=f"api_req_{method}_{path.replace('/', '_')}",
                value=duration,
                unit="ms"
            )
            
            # 通过API监控器追踪请求
            self.api_monitor.track_request(
                path=f"{method}:{path}",
                latency=duration,
                status_code=status_code
            )
            
            return response
            
        except Exception as e:
            # 记录异常
            duration = (time.time() - start_time) * 1000
            
            # 记录错误详情
            logger.error(f"API请求异常: {path} - {str(e)}")
            
            # 通过API监控器追踪请求(异常)
            self.api_monitor.track_request(
                path=f"{method}:{path}",
                latency=duration,
                status_code=500  # 内部服务器错误
            )
            
            # 继续抛出异常，让FastAPI的异常处理器处理
            raise


# API路由性能监控增强器
class MonitoredAPIRoute(APIRoute):
    """
    带性能监控功能的API路由
    
    用于替代FastAPI的标准APIRoute，自动为每个路由添加性能监控。
    使用方法：app.router.route_class = MonitoredAPIRoute
    """
    
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()
        monitor = get_api_monitor()
        
        async def monitored_route_handler(request: Request) -> Response:
            # 记录开始时间
            start_time = time.time()
            
            # 执行原始路由处理程序
            response = None
            try:
                response = await original_route_handler(request)
                status_code = response.status_code
            except Exception as e:
                # 记录异常，然后重新抛出
                duration = (time.time() - start_time) * 1000
                monitor.track_request(
                    path=f"{request.method}:{self.path}",
                    latency=duration,
                    status_code=500
                )
                raise
                
            # 计算处理时间
            duration = (time.time() - start_time) * 1000
            
            # 记录性能指标
            monitor.track_request(
                path=f"{request.method}:{self.path}",
                latency=duration,
                status_code=response.status_code
            )
            
            return response
            
        return monitored_route_handler


def add_monitoring_middleware(
    app: FastAPI, 
    influx_config: Dict[str, Any] = None,
    exclude_paths: list = None
) -> None:
    """
    向FastAPI应用添加监控中间件
    
    Args:
        app: FastAPI应用实例
        influx_config: InfluxDB配置，默认为None
        exclude_paths: 排除监控的路径列表，默认为["/docs", "/redoc", "/openapi.json"]
    """
    # 设置默认排除路径
    if exclude_paths is None:
        exclude_paths = ["/docs", "/redoc", "/openapi.json", "/metrics", "/health"]
    
    # 添加中间件
    app.add_middleware(
        APIMonitorMiddleware,
        influx_config=influx_config,
        exclude_paths=exclude_paths
    )
    
    # 使用增强的API路由类
    app.router.route_class = MonitoredAPIRoute
    
    logger.info("API监控中间件已添加到应用程序") 