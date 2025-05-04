"""
错误处理集成模块

此模块负责将错误处理系统集成到应用程序的各个核心组件中，
提供统一的初始化入口和错误处理策略应用。
"""

import sys
import os
from loguru import logger
from typing import Optional, Dict, Any, List, Callable

from src.utils.error_handler import init_error_handler, get_error_handler
from src.utils.error_logger import get_error_logger
from src.core.auto_recovery import auto_heal, register_recovery_strategy
from src.utils.exceptions import ClipMasterError, ErrorCode

# 应用程序核心组件列表
CORE_COMPONENTS = [
    "model_manager",
    "data_processor", 
    "video_processor",
    "subtitle_manager", 
    "config_manager"
]

# 核心组件初始化函数映射
COMPONENT_INIT_FUNCS = {}

def init_error_handling_system() -> None:
    """
    初始化错误处理系统
    
    此函数负责初始化整个应用程序的错误处理系统，包括：
    1. 设置全局异常钩子
    2. 初始化错误日志记录器
    3. 配置自动恢复策略
    """
    logger.info("初始化错误处理系统...")
    
    # 初始化错误处理器（包括设置全局异常钩子）
    error_handler = init_error_handler()
    
    # 确保错误日志记录器已初始化
    error_logger = get_error_logger()
    
    # 配置特定恢复策略（如有需要）
    _configure_recovery_strategies()
    
    logger.success("错误处理系统初始化完成")
    return error_handler

def _configure_recovery_strategies() -> None:
    """配置应用程序特定的恢复策略"""
    # 针对特定错误定制恢复策略
    # 此处可以根据应用程序的特性添加更多恢复策略
    pass

def wrap_component_methods(component_name: str, component: Any) -> Any:
    """
    为组件的所有公共方法添加错误处理装饰器
    
    Args:
        component_name: 组件名称
        component: 组件对象
        
    Returns:
        包装后的组件对象
    """
    error_handler = get_error_handler()
    
    # 遍历组件的所有方法
    for attr_name in dir(component):
        # 跳过私有方法和特殊方法
        if attr_name.startswith('_'):
            continue
        
        attr = getattr(component, attr_name)
        # 仅处理方法
        if callable(attr):
            # 封装方法
            wrapped_method = error_handler.with_error_handling(reraise=False)(attr)
            # 替换原方法
            setattr(component, attr_name, wrapped_method)
            logger.debug(f"已为组件 {component_name} 的方法 {attr_name} 添加错误处理")
    
    return component

def register_component_init(component_name: str, init_func: Callable) -> None:
    """
    注册组件初始化函数
    
    Args:
        component_name: 组件名称
        init_func: 初始化函数
    """
    COMPONENT_INIT_FUNCS[component_name] = init_func
    logger.debug(f"已注册组件 {component_name} 的初始化函数")

def init_core_components() -> Dict[str, Any]:
    """
    初始化所有核心组件，并为其添加错误处理
    
    Returns:
        Dict[str, Any]: 组件名称到组件实例的映射
    """
    logger.info("初始化核心组件...")
    
    components = {}
    for component_name in CORE_COMPONENTS:
        try:
            # 获取组件初始化函数
            init_func = COMPONENT_INIT_FUNCS.get(component_name)
            if init_func:
                # 初始化组件
                logger.debug(f"初始化组件: {component_name}")
                component = init_func()
                
                # 为组件添加错误处理
                component = wrap_component_methods(component_name, component)
                
                # 添加到组件字典
                components[component_name] = component
            else:
                logger.warning(f"组件 {component_name} 没有注册初始化函数")
        except Exception as e:
            logger.error(f"初始化组件 {component_name} 失败: {e}")
            # 记录错误但继续初始化其他组件
            get_error_handler().handle_error(e, {"component": component_name})
    
    logger.success(f"已初始化 {len(components)}/{len(CORE_COMPONENTS)} 个核心组件")
    return components

def handle_critical_startup_error(error: Exception) -> bool:
    """
    处理启动过程中的严重错误
    
    Args:
        error: 捕获的异常
        
    Returns:
        bool: 是否成功恢复
    """
    logger.critical(f"启动过程中发生严重错误: {error}")
    
    # 记录错误
    error_handler = get_error_handler()
    error_handler.handle_error(error, {"stage": "startup"})
    
    # 尝试恢复
    if isinstance(error, ClipMasterError):
        try:
            return auto_heal(error)
        except Exception as recovery_error:
            logger.error(f"恢复失败: {recovery_error}")
    
    return False

def setup_failsafe_mode() -> None:
    """
    设置应用程序的故障安全模式
    
    当应用程序无法正常启动时，启用最小功能集，
    允许用户查看错误日志和执行基本操作。
    """
    logger.warning("启用故障安全模式")
    
    # 在实际应用中，这里可以设置最小功能集和UI
    # 例如关闭高级功能，只保留基本功能和日志查看器
    
    # 记录进入故障安全模式的事件
    from src.utils.log_handler import get_logger
    get_logger().bind(AUDIT=True).warning("应用程序已进入故障安全模式")

def integrate_error_handling() -> None:
    """
    完整集成错误处理系统到应用程序
    
    此函数是应用程序启动过程中应调用的主要入口点，
    负责设置错误处理系统和初始化核心组件。
    """
    try:
        # 初始化错误处理系统
        init_error_handling_system()
        
        # 初始化核心组件
        components = init_core_components()
        
        # 将组件设置为全局可访问
        # 这里根据实际应用架构可能有所不同
        for name, component in components.items():
            setattr(sys.modules[__name__], name, component)
        
        logger.success("错误处理系统已完全集成到应用程序")
    except Exception as e:
        # 处理初始化过程中的错误
        recovery_success = handle_critical_startup_error(e)
        
        if not recovery_success:
            # 如果无法恢复，启用故障安全模式
            setup_failsafe_mode()
            
            # 记录启动失败
            logger.critical("应用程序启动失败，已启用故障安全模式")
            
            # 在实际应用中，可能需要通知用户
        else:
            logger.info("已从启动错误中恢复，继续初始化")
            # 重试初始化
            integrate_error_handling()

# 导出主要函数
__all__ = [
    'init_error_handling_system',
    'init_core_components',
    'register_component_init',
    'integrate_error_handling',
] 