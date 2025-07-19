from src.utils.exceptions import ClipMasterError, ErrorCode
from src.utils.error_logger import ErrorLogger
from src.core.auto_recovery import auto_heal
from loguru import logger
import traceback
import functools
import inspect
import sys
import contextlib
import datetime
from typing import Any, Callable, Dict, Optional, Type, TypeVar, cast, Union, List, Generator

F = TypeVar('F', bound=Callable[..., Any])

class ErrorHandler:
    """
    全局错误处理器，集成错误日志记录与自动恢复功能
    """
    _instance = None
    _logger = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ErrorHandler, cls).__new__(cls)
            cls._instance._logger = ErrorLogger()
            cls._instance._errors = []  # 存储捕获的错误
        return cls._instance
    
    def handle_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
        """
        处理异常：记录日志并尝试自动恢复
        
        Args:
            error: 捕获的异常
            context: 错误发生时的上下文信息
        """
        if context is None:
            context = {}
            
        # 提取堆栈信息
        frame = inspect.currentframe().f_back
        if frame:
            context.update({
                "file": frame.f_code.co_filename,
                "function": frame.f_code.co_name,
                "line": frame.f_lineno
            })
        
        # 记录错误日志
        if isinstance(error, ClipMasterError):
            self._logger.log(error)
            
            # 对于标记为 critical 的错误尝试自动恢复
            if hasattr(error, 'critical') and error.critical:
                logger.info(f"尝试自动恢复 {error.code.name} 错误")
                try:
                    auto_heal(error)
                except Exception as recovery_error:
                    logger.error(f"自动恢复失败: {recovery_error}")
        else:
            # 非自定义异常，记录为通用错误
            generic_error = ClipMasterError(
                message=str(error),
                code=ErrorCode.UNKNOWN_ERROR,
                details={"original_error": error.__class__.__name__, "context": context}
            )
            self._logger.log(generic_error)
        
        # 存储错误信息
        self._store_error(error, context)
        
        # 根据错误类型决定是否需要重新抛出
        if isinstance(error, ClipMasterError) and hasattr(error, 'critical') and error.critical:
            logger.warning(f"发生严重错误: {error}，应用可能需要重启")
        else:
            # 非致命错误，记录后继续
            logger.warning(f"捕获到非致命错误: {error}")
    
    def _store_error(self, error: Exception, context: Dict[str, Any]) -> None:
        """存储错误信息供后续分析"""
        error_info = {
            "timestamp": datetime.datetime.now().isoformat(),
            "exception_type": error.__class__.__name__,
            "message": str(error),
            "context": context,
            "traceback": traceback.format_exc(),
        }
        self._errors.append(error_info)
    
    def has_errors(self) -> bool:
        """检查是否有捕获的错误"""
        return len(self._errors) > 0
    
    def get_errors(self) -> List[Dict[str, Any]]:
        """获取所有捕获的错误信息"""
        return self._errors.copy()
    
    def clear_errors(self) -> None:
        """清除已捕获的错误记录"""
        self._errors.clear()
    
    @contextlib.contextmanager
    def capture(self, operation_name: str = "operation") -> Generator[None, None, None]:
        """
        上下文管理器：捕获并处理代码块中的异常
        
        Args:
            operation_name: 操作名称，用于错误日志
            
        Yields:
            None
        """
        try:
            yield
        except Exception as e:
            context = {"operation": operation_name}
            self.handle_error(e, context)
            # 这里不重新抛出异常，让程序可以继续执行
    
    def with_error_handling(self, reraise: bool = False) -> Callable[[F], F]:
        """
        装饰器：为函数添加错误处理
        
        Args:
            reraise: 是否重新抛出捕获的异常
            
        Returns:
            装饰后的函数
        """
        def decorator(func: F) -> F:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    # 提取上下文信息
                    context = {
                        "function": func.__name__,
                        "args": str(args),
                        "kwargs": str(kwargs)
                    }
                    
                    # 处理错误
                    self.handle_error(e, context)
                    
                    # 根据配置决定是否重新抛出
                    if reraise:
                        raise
                    
                    # 对于非重新抛出的情况，返回 None 或其他默认值
                    return None
            
            return cast(F, wrapper)
        
        return decorator
    
    def global_exception_handler(self, exctype, value, tb):
        """
        全局未捕获异常处理器
        
        Args:
            exctype: 异常类型
            value: 异常值
            tb: 异常追踪对象
        """
        # 记录未捕获的异常
        error_msg = "".join(traceback.format_exception(exctype, value, tb))
        logger.error(f"未捕获的异常: {error_msg}")
        
        # 尝试进行错误处理
        self.handle_error(value)
        
        # 调用原始的异常处理器
        sys.__excepthook__(exctype, value, tb)
    
    def get_last_error(self) -> Optional[Dict[str, Any]]:
        """获取最近发生的错误"""
        if self._errors:
            return self._errors[-1]
        return None
    
    def get_error_summary(self) -> Dict[str, int]:
        """获取错误类型统计摘要"""
        summary = {}
        for error in self._errors:
            error_type = error["exception_type"]
            if error_type in summary:
                summary[error_type] += 1
            else:
                summary[error_type] = 1
        return summary

def init_error_handler():
    """初始化全局错误处理器"""
    handler = ErrorHandler()
    # 注册全局未捕获异常处理器
    sys.excepthook = handler.global_exception_handler
    logger.info("全局错误处理器已初始化")
    return handler

# 提供全局访问点
_error_handler = None

def get_error_handler() -> ErrorHandler:
    """获取全局错误处理器实例"""
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler()
    return _error_handler


def handle_exception(exception: Exception, error_context: str = "") -> None:
    """
    处理异常的简化包装函数
    
    该函数是为其他模块提供的简化错误处理接口，以便与error_handler集成
    
    Args:
        exception: 捕获的异常
        error_context: 错误上下文描述
    """
    # 获取错误处理器
    handler = get_error_handler()
    
    # 构建上下文信息
    context = {"description": error_context} if error_context else {}
    
    # 委托给错误处理器
    handler.handle_error(exception, context)
    
    # 记录到日志
    logger.error(f"{error_context}: {str(exception)}")
    logger.debug(f"异常详情: {traceback.format_exc()}") 