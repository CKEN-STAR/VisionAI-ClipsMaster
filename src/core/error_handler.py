"""
统一错误处理模块

提供集中式的错误处理机制，整合各种容错和恢复策略：
1. 统一异常处理接口
2. 智能分发到专门的恢复模块
3. 错误记录与统计
4. 用户友好的错误反馈
"""

import os
import sys
import traceback
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Union, Callable, Type

from loguru import logger
from src.utils.exceptions import ClipMasterError, ErrorCode

# 导入专业恢复模块
from src.core.recovery_manager import get_recovery_manager
from src.core.subtitle_recovery import get_subtitle_recovery
from src.core.model_recovery import get_model_recovery
from src.core.auto_recovery import auto_heal


class ErrorHandler:
    """集中式错误处理器"""
    
    def __init__(self):
        """初始化错误处理器"""
        self.error_stats = {
            "total_errors": 0,
            "handled_errors": 0,
            "unhandled_errors": 0,
            "recoveries": 0,
            "by_type": {},
            "by_module": {}
        }
        self.recovery_manager = get_recovery_manager()
        self.subtitle_recovery = get_subtitle_recovery()
        self.model_recovery = get_model_recovery()
        self.last_error = None
        self.last_error_time = None
        self.registered_handlers = {}
    
    def handle_error(self, 
                    error: Exception, 
                    context: Dict[str, Any] = None,
                    retry: bool = False) -> bool:
        """
        处理异常
        
        Args:
            error: 捕获的异常
            context: 上下文信息
            retry: 是否是重试处理
            
        Returns:
            是否成功处理
        """
        context = context or {}
        error_type = type(error).__name__
        error_message = str(error)
        error_code = getattr(error, "code", None)
        error_details = getattr(error, "details", {})
        module_name = context.get("module", "unknown")
        
        # 更新错误统计
        self.error_stats["total_errors"] += 1
        self.error_stats["by_type"][error_type] = self.error_stats["by_type"].get(error_type, 0) + 1
        self.error_stats["by_module"][module_name] = self.error_stats["by_module"].get(module_name, 0) + 1
        
        # 记录错误信息
        error_trace = "".join(traceback.format_exception(type(error), error, error.__traceback__))
        logger.error(f"捕获到错误: {error_type}: {error_message}\n上下文: {context}\n{error_trace}")
        
        # 保存最后一次错误信息
        self.last_error = error
        self.last_error_time = datetime.now()
        
        # 尝试处理错误
        handled = False
        
        # 1. 检查是否有特定处理器注册
        if error_code and error_code.value in self.registered_handlers:
            handler = self.registered_handlers[error_code.value]
            try:
                logger.info(f"使用注册的处理器处理错误 {error_code}")
                handled = handler(error, context)
                if handled:
                    logger.info(f"注册处理器成功处理了错误 {error_code}")
                    self.error_stats["handled_errors"] += 1
                    self.error_stats["recoveries"] += 1
                    return True
            except Exception as handler_error:
                logger.error(f"注册处理器发生异常: {handler_error}")
        
        # 2. 根据错误类型分发到专业恢复模块
        if not handled and not retry:
            handled = self._dispatch_to_recovery_module(error, context)
        
        # 3. 如果专业模块无法处理，尝试通用自动恢复
        if not handled and isinstance(error, ClipMasterError) and not retry:
            try:
                logger.info(f"尝试使用通用恢复机制处理错误: {error_type}")
                handled = auto_heal(error)
                if handled:
                    logger.info(f"通用恢复机制成功处理了错误")
                    self.error_stats["handled_errors"] += 1
                    self.error_stats["recoveries"] += 1
                    return True
            except Exception as recovery_error:
                logger.error(f"通用恢复过程中发生异常: {recovery_error}")
        
        # 4. 如果所有尝试都失败，记录为未处理错误
        if not handled:
            self.error_stats["unhandled_errors"] += 1
            logger.warning(f"无法处理错误: {error_type}: {error_message}")
            
            # 通知用户
            self._notify_user(error, context)
        else:
            self.error_stats["handled_errors"] += 1
        
        return handled
    
    def _dispatch_to_recovery_module(self, error: Exception, context: Dict[str, Any]) -> bool:
        """
        将错误分发到专业恢复模块
        
        Args:
            error: 捕获的异常
            context: 上下文信息
            
        Returns:
            是否成功处理
        """
        error_str = str(error).lower()
        error_type = type(error).__name__
        
        # 根据错误内容和上下文选择合适的恢复模块
        if context.get("component") == "subtitle" or "srt" in error_str or "字幕" in error_str:
            # 字幕相关错误
            try:
                if "file" in context:
                    logger.info(f"分发字幕错误到字幕恢复模块: {context['file']}")
                    self.subtitle_recovery.recover_srt_file(context["file"])
                    return True
            except Exception as recovery_error:
                logger.error(f"字幕恢复过程中发生异常: {recovery_error}")
        
        elif context.get("component") == "model" or "model" in error_str or "模型" in error_str:
            # 模型相关错误
            try:
                if "model_name" in context:
                    logger.info(f"分发模型错误到模型恢复模块: {context['model_name']}")
                    return self.model_recovery.recover_model_loading_error(context["model_name"], error)
            except Exception as recovery_error:
                logger.error(f"模型恢复过程中发生异常: {recovery_error}")
        
        elif context.get("component") == "task" or "task" in context:
            # 任务处理相关错误，尝试使用断点续传
            try:
                if "task_id" in context:
                    logger.info(f"尝试恢复中断的任务: {context['task_id']}")
                    recovery_point = self.recovery_manager.resume_task(context["task_id"])
                    if recovery_point:
                        return True
            except Exception as recovery_error:
                logger.error(f"任务恢复过程中发生异常: {recovery_error}")
        
        return False
    
    def _notify_user(self, error: Exception, context: Dict[str, Any]) -> None:
        """
        向用户通知错误
        
        Args:
            error: 捕获的异常
            context: 上下文信息
        """
        # 这里根据实际UI实现来通知用户
        error_message = str(error)
        error_type = type(error).__name__
        
        if hasattr(error, "code"):
            error_code = error.code
            category = ErrorCode.get_error_category(error_code.value)
            error_info = f"{category}: {error_message}"
        else:
            error_info = f"{error_type}: {error_message}"
        
        # 记录用户通知
        logger.info(f"向用户通知错误: {error_info}")
        
        # 通过全局通知管理器通知用户
        try:
            from src.ui.components.alert_manager import notify_error
            notify_error(error_info, context)
        except ImportError:
            # UI组件可能尚未准备好
            logger.warning("无法通知用户，UI组件未导入")
    
    def register_error_handler(self, 
                              error_code: Union[int, ErrorCode],
                              handler: Callable[[Exception, Dict[str, Any]], bool]) -> None:
        """
        注册特定错误代码的处理器
        
        Args:
            error_code: 错误代码
            handler: 处理函数
        """
        if isinstance(error_code, ErrorCode):
            code_value = error_code.value
        else:
            code_value = error_code
        
        self.registered_handlers[code_value] = handler
        logger.debug(f"已注册错误处理器: {code_value}")
    
    def with_error_handling(self, 
                           reraise: bool = False, 
                           component: str = None) -> Callable:
        """
        创建一个错误处理装饰器
        
        Args:
            reraise: 是否重新抛出异常
            component: 组件名称
            
        Returns:
            装饰器函数
        """
        def decorator(func):
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as error:
                    # 构建上下文
                    context = {
                        "function": func.__name__,
                        "args": str(args),
                        "kwargs": str(kwargs),
                        "component": component or func.__module__
                    }
                    
                    # 处理错误
                    handled = self.handle_error(error, context)
                    
                    # 如果需要重新抛出或未处理，则抛出
                    if reraise or not handled:
                        raise
                    
                    # 返回None表示出错
                    return None
            return wrapper
        return decorator
    
    def get_error_stats(self) -> Dict[str, Any]:
        """获取错误统计信息"""
        return self.error_stats


# 全局错误处理器实例
_error_handler = None

def get_error_handler() -> ErrorHandler:
    """获取全局错误处理器实例"""
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler()
    return _error_handler


def safe_execute(func: Callable, 
                *args, 
                default_return=None, 
                component: str = None, 
                **kwargs) -> Any:
    """
    安全执行函数，捕获并处理异常
    
    Args:
        func: 要执行的函数
        *args: 位置参数
        default_return: 出错时的默认返回值
        component: 组件名称
        **kwargs: 关键字参数
        
    Returns:
        函数执行结果或默认值
    """
    handler = get_error_handler()
    
    try:
        return func(*args, **kwargs)
    except Exception as error:
        # 构建上下文
        context = {
            "function": func.__name__,
            "component": component or func.__module__
        }
        
        # 处理错误
        handler.handle_error(error, context)
        
        # 返回默认值
        return default_return 