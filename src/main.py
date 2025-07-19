try:
    from fastapi import FastAPI, Request
    from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
    from fastapi.openapi.utils import get_openapi
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import HTMLResponse, JSONResponse
    from src.api import api_router
    from src.api.security import (
        RateLimiter, 
        SQLInjectionGuard, 
        RequestValidator, 
        CORSMiddleware,
        RequestLoggerMiddleware
    )
    # 导入API监控中间件和路由
    from src.api.middleware.api_monitor_middleware import add_monitoring_middleware
    from src.api.monitoring_api import router as monitoring_router
except ImportError as e:
    # 记录导入错误但允许程序继续执行核心功能
    from loguru import logger
    logger.warning(f"FastAPI相关模块导入失败: {e}")
    logger.warning("API服务将不可用，但其他核心功能不受影响")
    
    # 创建空的模拟对象以避免引用错误
    class MockObject:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
        def __getattr__(self, name):
            return lambda *args, **kwargs: None
    
    # 创建模拟的FastAPI对象
    FastAPI = lambda **kwargs: MockObject(**kwargs)
    api_router = MockObject()
    monitoring_router = MockObject()
    add_monitoring_middleware = lambda *args, **kwargs: None
    StaticFiles = lambda **kwargs: None

import os

# 导入容错与修复系统
from src.core.error_handling_init import init_all_error_handling, cleanup_old_recovery_data
from loguru import logger

# 导入并抑制可选依赖警告
try:
    from src.utils.log_handler import suppress_optional_dependency_warnings, check_spacy
    suppress_optional_dependency_warnings()
    spacy_available = check_spacy()
    logger.debug(f"已抑制可选依赖项警告，spaCy可用性: {'可用' if spacy_available else '使用模拟实现'}")
except Exception as e:
    logger.warning(f"抑制可选依赖项警告失败: {e}")

# 初始化容错与修复系统
logger.info("正在初始化VisionAI-ClipsMaster容错与修复系统...")
init_all_error_handling()
cleanup_old_recovery_data(30)  # 清理30天以上的恢复数据

# 创建FastAPI应用
app = FastAPI(
    title="VisionAI-ClipsMaster API",
    description="""
    # 智能短剧混剪系统API

    基于大语言模型的智能短剧混剪系统，支持多语言处理和模型热切换。

    ## 核心功能

    * **剧本重构**：分析原片剧情，生成爆款结构
    * **智能拼接**：基于重构剧本自动生成混剪视频
    * **低资源运行**：支持4GB内存/无GPU设备
    * **双语言支持**：中文(Qwen2.5-7B)/英文(Mistral-7B)双模型

    ## 授权说明

    使用API需要提供API密钥，请在请求头中添加`X-API-Key`。
    """,
    version="1.0.0",
    docs_url=None,  # 禁用默认的Swagger UI
    redoc_url=None, # 禁用默认的ReDoc
    terms_of_service="https://visionai.example.com/terms/",
    contact={
        "name": "技术支持",
        "url": "https://visionai.example.com/support/",
        "email": "support@visionai.example.com",
    },
    license_info={
        "name": "专有许可",
        "url": "https://visionai.example.com/license/",
    },
)

# 添加安全中间件（按执行顺序添加）
app.add_middleware(RequestLoggerMiddleware)  # 日志应该最先执行，记录所有请求
app.add_middleware(CORSMiddleware, allowed_origins=["*"])  # CORS头处理
app.add_middleware(RequestValidator)  # 请求验证
app.add_middleware(SQLInjectionGuard)  # SQL注入防护
app.add_middleware(RateLimiter, max_requests=30, window_seconds=60)  # 限流控制

# 添加API监控中间件 - 替换原有性能监控中间件
# 配置InfluxDB（可选）
influx_config = None
# 如果存在配置文件，则加载配置
config_path = os.path.join("configs", "monitoring.json")
if os.path.exists(config_path):
    try:
        import json
        with open(config_path, "r") as f:
            config = json.load(f)
        influx_config = config.get("influxdb")
    except Exception as e:
        logger.error(f"加载监控配置失败: {e}")

# 添加API监控
add_monitoring_middleware(
    app,
    influx_config=influx_config,
    exclude_paths=["/api/docs", "/api/redoc", "/api/openapi.json", "/api/v1/monitoring/prometheus", "/static"]
)

# 添加API路由
app.include_router(api_router)

# 添加监控API路由
app.include_router(monitoring_router)

# 尝试挂载静态文件目录（如果存在）
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# 自定义OpenAPI文档生成
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        terms_of_service=app.terms_of_service,
        contact=app.contact,
        license_info=app.license_info,
    )
    
    # 添加安全模式
    openapi_schema["components"]["securitySchemes"] = {
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": "API密钥认证"
        },
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT令牌认证"
        }
    }
    
    # 全局安全要求
    openapi_schema["security"] = [
        {"ApiKeyAuth": []}
    ]
    
    # 设置服务器信息
    openapi_schema["servers"] = [
        {
            "url": "/",
            "description": "当前服务器"
        },
        {
            "url": "https://api.visionai.example.com",
            "description": "生产环境"
        }
    ]
    
    # 添加标签说明
    openapi_schema["tags"] = [
        {
            "name": "clips",
            "description": "短剧混剪相关操作",
            "externalDocs": {
                "description": "混剪处理文档",
                "url": "https://visionai.example.com/docs/clips/"
            }
        },
        {
            "name": "models",
            "description": "大语言模型相关操作",
            "externalDocs": {
                "description": "模型管理文档",
                "url": "https://visionai.example.com/docs/models/"
            }
        },
        {
            "name": "knowledge",
            "description": "知识图谱和剧情分析",
            "externalDocs": {
                "description": "知识图谱文档",
                "url": "https://visionai.example.com/docs/knowledge/"
            }
        },
        {
            "name": "monitoring",
            "description": "API性能监控",
            "externalDocs": {
                "description": "监控文档",
                "url": "https://visionai.example.com/docs/monitoring/"
            }
        }
    ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# 自定义Swagger UI路由
@app.get("/api/docs", include_in_schema=False)
async def custom_swagger_ui_html(req: Request):
    """自定义Swagger UI界面"""
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - API文档",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui.css",
        swagger_favicon_url="/static/favicon.png" if os.path.exists(STATIC_DIR + "/favicon.png") else None,
        swagger_ui_parameters={
            "docExpansion": "none",  # 默认折叠所有操作
            "persistAuthorization": True,  # 保持授权信息
            "displayRequestDuration": True,  # 显示请求耗时
            "defaultModelsExpandDepth": 2,  # 模型展开深度
            "filter": True,  # 启用过滤功能
            "syntaxHighlight.theme": "monokai"  # 代码高亮主题
        }
    )

# 自定义ReDoc路由
@app.get("/api/redoc", include_in_schema=False)
async def custom_redoc_html():
    """自定义ReDoc界面"""
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - API参考文档",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js",
        redoc_favicon_url="/static/favicon.png" if os.path.exists(STATIC_DIR + "/favicon.png") else None,
        with_google_fonts=True
    )

# 提供OpenAPI JSON端点
@app.get("/api/openapi.json", include_in_schema=False)
async def get_openapi_json():
    """获取OpenAPI规范JSON"""
    return JSONResponse(content=app.openapi())

# 健康检查端点 - 重定向到监控健康检查
@app.get("/api/health", tags=["system"])
async def health_check():
    """系统健康检查接口"""
    # 基本健康信息
    health_info = {
        "status": "ok",
        "version": app.version,
        "api": app.title,
        "models": {
            "zh": "Qwen2.5-7B (已加载)",
            "en": "Mistral-7B (仅配置)"
        }
    }
    
    # 尝试获取详细的监控健康信息
    try:
        from src.utils.api_monitoring import get_api_monitor
        monitor = get_api_monitor()
        stats = monitor.get_statistics()
        
        # 添加性能统计摘要
        health_info["performance"] = {
            "uptime": f"{stats['uptime']:.2f}秒",
            "memory": {
                "current": f"{stats['system']['memory']['current'] / (1024*1024):.2f} MB",
                "peak": f"{stats['system']['memory']['peak'] / (1024*1024):.2f} MB"
            },
            "cpu": {
                "current": f"{stats['system']['cpu']['current']:.2f}%",
                "average": f"{stats['system']['cpu']['average']:.2f}%"
            }
        }
        
        # 添加错误统计
        from src.core.error_handler import get_error_handler
        error_handler = get_error_handler()
        error_stats = error_handler.get_error_stats()
        
        health_info["errors"] = {
            "total": error_stats["total_errors"],
            "handled": error_stats["handled_errors"],
            "recovery_rate": f"{error_stats['recoveries'] / max(1, error_stats['total_errors']) * 100:.1f}%" 
            if error_stats["total_errors"] > 0 else "N/A"
        }
        
    except Exception as e:
        logger.warning(f"获取监控统计信息失败: {e}")
    
    return health_info

# 启动事件 - 用于处理应用启动时的额外初始化
@app.on_event("startup")
async def startup_event():
    """应用启动时触发的事件"""
    logger.info("VisionAI-ClipsMaster API服务启动完成")
    
    # 验证模型配置
    try:
        from src.core.model_recovery import verify_model
        # 检查中文模型配置
        zh_model_valid = verify_model("qwen2.5-7b-zh")
        logger.info(f"中文模型配置验证: {'通过' if zh_model_valid else '失败'}")
        
        # 英文模型仅检查配置
        en_model_config = os.path.join("configs", "models", "available_models", "mistral-7b-en.yaml")
        en_model_config_exists = os.path.exists(en_model_config)
        logger.info(f"英文模型配置验证: {'文件存在' if en_model_config_exists else '文件不存在'}")
    except Exception as e:
        logger.error(f"模型配置验证失败: {e}")
    
    # 初始化双工通信引擎和增量更新广播器
    try:
        from src.realtime import (
            initialize_duplex_engine, 
            DeltaBroadcaster, 
            set_delta_broadcaster,
            initialize_operation_logger,
            initialize_ot_resolver,
            initialize_lag_reducer,
            initialize_feedback_collector,
            initialize_interaction_sandbox
        )
        
        # 初始化通信引擎
        await initialize_duplex_engine(
            ws_host=settings.websocket_host,
            ws_port=settings.websocket_port
        )
        logger.info(f"双工通信引擎已初始化 (WebSocket: {settings.websocket_host}:{settings.websocket_port})")
        
        # 初始化增量更新广播器
        try:
            delta_broadcaster = DeltaBroadcaster(redis_url=settings.redis_url)
            await delta_broadcaster.initialize()
            await delta_broadcaster.start()
            set_delta_broadcaster(delta_broadcaster)
            logger.info(f"增量更新广播器已初始化 (Redis: {settings.redis_url})")
        except Exception as e:
            logger.error(f"初始化增量更新广播器失败: {str(e)}")
        
        # 初始化操作转换冲突解决器
        try:
            ot_resolver = initialize_ot_resolver()
            logger.info("操作转换冲突解决器已初始化")
        except Exception as e:
            logger.error(f"初始化操作转换冲突解决器失败: {str(e)}")
        
        # 初始化交互延迟优化器
        try:
            # 加载配置
            lag_reducer_config = None
            config_path = os.path.join("configs", "edge_cache.json")
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    lag_reducer_config = json.load(f)
            
            # 初始化延迟优化器
            lag_reducer = await initialize_lag_reducer(lag_reducer_config)
            logger.info("交互延迟优化器已初始化")
        except Exception as e:
            logger.error(f"初始化交互延迟优化器失败: {str(e)}")
        
        # 初始化生物反馈收集器
        try:
            # 加载配置
            feedback_config = None
            config_path = os.path.join("configs", "wearable.json")
            if os.path.exists(config_path):
                try:
                    with open(config_path, "r", encoding="utf-8") as f:
                        feedback_config = json.load(f)
                except Exception as e:
                    logger.warning(f"加载生物反馈配置失败: {str(e)}")
            
            # 初始化反馈收集器
            feedback_collector = await initialize_feedback_collector(feedback_config)
            logger.info("实时反馈收集器已初始化")
        except Exception as e:
            logger.error(f"初始化实时反馈收集器失败: {str(e)}")
            
        # 初始化交互沙盒隔离器
        try:
            # 检查安全策略配置
            sandbox_config = {
                "timeout": 30,  # 默认超时时间(秒)
                "force_subprocess": False  # 默认使用Docker(如果可用)
            }
            
            # 尝试从安全策略加载沙盒配置
            try:
                security_path = os.path.join("configs", "security_policy.yaml")
                if os.path.exists(security_path):
                    import yaml
                    with open(security_path, "r", encoding="utf-8") as f:
                        security_config = yaml.safe_load(f)
                        if "resource_protection" in security_config:
                            resource_config = security_config["resource_protection"]
                            # 从资源保护配置中提取沙盒配置
                            if "process_isolation" in resource_config:
                                isolation_config = resource_config["process_isolation"]
                                # 使用配置覆盖默认值
                                if "sandbox_timeout" in isolation_config:
                                    sandbox_config["timeout"] = isolation_config["sandbox_timeout"]
                                if "enable_sandboxing" in isolation_config and not isolation_config["enable_sandboxing"]:
                                    sandbox_config["force_subprocess"] = True
            except Exception as e:
                logger.warning(f"加载沙盒配置失败: {str(e)}")
            
            # 初始化交互沙盒隔离器
            interaction_sandbox = await initialize_interaction_sandbox(
                timeout=sandbox_config["timeout"],
                force_subprocess=sandbox_config["force_subprocess"]
            )
            
            # 测试沙盒功能
            test_result = await interaction_sandbox.safe_execute("print('沙盒测试成功')")
            if test_result["success"]:
                logger.info(f"交互沙盒隔离器已初始化 (类型: {interaction_sandbox.sandbox.__class__.__name__})")
            else:
                logger.warning(f"交互沙盒测试失败: {test_result['stderr']}")
        except Exception as e:
            logger.error(f"初始化交互沙盒隔离器失败: {str(e)}")
        
        # 初始化操作日志溯源器
        try:
            # 使用配置文件中的设置
            from src.config import settings
            
            # 检查是否启用操作日志
            if settings.operation_log_enabled:
                # 初始化操作日志记录器
                op_logger = initialize_operation_logger(
                    base_log_dir=settings.operation_log_dir,
                    enable_s3=settings.operation_log_s3_enabled,
                    s3_bucket=settings.operation_log_s3_bucket,
                    s3_prefix=settings.operation_log_s3_prefix,
                    auto_flush=True,
                    flush_interval=settings.operation_log_flush_interval
                )
                logger.info(f"操作日志溯源器已初始化 (目录: {settings.operation_log_dir}, S3备份: {'已启用' if settings.operation_log_s3_enabled else '未启用'})")
            else:
                logger.info("操作日志溯源器已禁用（通过配置）")
        except Exception as e:
            logger.error(f"初始化操作日志溯源器失败: {str(e)}")
            
    except ImportError:
        logger.warning("未安装双工通信引擎相关依赖，WebSocket功能将不可用")

# 关闭事件 - 用于处理应用关闭时的清理工作
@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时触发的事件"""
    logger.info("VisionAI-ClipsMaster API服务即将关闭")
    
    # 保存恢复点状态
    try:
        from src.core.recovery_manager import get_recovery_manager
        recovery_manager = get_recovery_manager()
        # 清理过期恢复文件
        recovery_manager.cleanup_old_recovery_files(30)
        logger.info("已保存恢复状态并清理过期数据")
    except Exception as e:
        logger.error(f"保存恢复状态失败: {e}")
    
    # 关闭双工通信引擎和增量更新广播器
    try:
        from src.realtime import (
            shutdown_duplex_engine, 
            get_delta_broadcaster, 
            get_operation_logger, 
            get_ot_resolver, 
            get_lag_reducer, 
            get_feedback_collector,
            get_interaction_sandbox
        )
        
        # 关闭增量更新广播器
        delta_broadcaster = get_delta_broadcaster()
        if delta_broadcaster:
            await delta_broadcaster.stop()
            logger.info("增量更新广播器已关闭")
        
        # 关闭实时反馈收集器
        try:
            feedback_collector = get_feedback_collector()
            if feedback_collector:
                await feedback_collector.stop()
                logger.info("实时反馈收集器已关闭")
        except Exception as e:
            logger.error(f"关闭实时反馈收集器失败: {str(e)}")
            
        # 关闭交互沙盒隔离器
        try:
            interaction_sandbox = get_interaction_sandbox()
            if interaction_sandbox:
                await interaction_sandbox.cleanup()
                logger.info("交互沙盒隔离器已关闭")
        except Exception as e:
            logger.error(f"关闭交互沙盒隔离器失败: {str(e)}")
            
        # 关闭操作日志溯源器
        try:
            op_logger = get_operation_logger()
            if op_logger:
                # 停止自动刷新线程
                op_logger.stop_flush_thread()
                
                # 最后一次上传到S3
                if op_logger.enable_s3:
                    success = op_logger.upload_to_s3()
                    log_status = "成功" if success else "失败"
                    logger.info(f"操作日志最终S3备份{log_status}")
                
                logger.info("操作日志溯源器已关闭")
        except Exception as e:
            logger.error(f"关闭操作日志溯源器失败: {str(e)}")
        
        # 关闭交互延迟优化器
        try:
            lag_reducer = get_lag_reducer()
            if lag_reducer:
                await lag_reducer.stop()
                logger.info("交互延迟优化器已关闭")
        except Exception as e:
            logger.error(f"关闭交互延迟优化器失败: {str(e)}")
        
        # 记录操作转换冲突解决器状态
        try:
            ot_resolver = get_ot_resolver()
            if ot_resolver:
                logger.info("操作转换冲突解决器已关闭")
        except Exception as e:
            logger.error(f"关闭操作转换冲突解决器失败: {str(e)}")
        
        # 关闭通信引擎
        await shutdown_duplex_engine()
        logger.info("双工通信引擎已关闭")
    except ImportError:
        pass 