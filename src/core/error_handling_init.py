"""
容错与修复系统初始化模块

此模块负责在程序启动时初始化所有错误处理和恢复机制，包括：
1. 初始化各种恢复管理器
2. 设置全局异常捕获
3. 配置错误日志记录
4. 注册自定义错误处理器
"""

import os
import sys
import traceback
from pathlib import Path
from typing import Dict, List, Any, Optional

from loguru import logger

# 导入错误处理和恢复组件
from src.core.error_handler import get_error_handler, ErrorHandler
from src.core.recovery_manager import get_recovery_manager
from src.core.subtitle_recovery import get_subtitle_recovery
from src.core.model_recovery import get_model_recovery
from src.utils.exceptions import (
    ClipMasterError, ErrorCode, ModelLoadError, 
    InvalidSRTError, FileOperationError
)


def setup_error_handling(log_dir: str = "logs") -> ErrorHandler:
    """
    设置全局错误处理系统
    
    Args:
        log_dir: 日志目录
        
    Returns:
        初始化后的错误处理器
    """
    # 确保日志目录存在
    os.makedirs(log_dir, exist_ok=True)
    
    # 配置详细错误日志
    error_log_file = os.path.join(log_dir, "errors.log")
    logger.add(error_log_file, 
              level="ERROR", 
              rotation="5 MB", 
              retention="30 days", 
              format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message} | {extra}")
    
    # 获取错误处理器
    error_handler = get_error_handler()
    
    # 设置全局异常钩子
    def global_exception_handler(exctype, value, tb):
        if issubclass(exctype, KeyboardInterrupt):
            # 对于键盘中断，使用默认处理
            sys.__excepthook__(exctype, value, tb)
            return
        
        # 构建错误上下文
        context = {
            "uncaught": True,
            "traceback": "".join(traceback.format_exception(exctype, value, tb))
        }
        
        # 处理未捕获的异常
        error_handler.handle_error(value, context)
        
        # 输出到标准错误
        sys.__excepthook__(exctype, value, tb)
    
    # 设置全局异常钩子
    sys.excepthook = global_exception_handler
    logger.info("已设置全局异常处理钩子")
    
    return error_handler


def initialize_recovery_systems() -> None:
    """初始化所有恢复系统"""
    # 初始化恢复管理器（处理断点续传）
    recovery_manager = get_recovery_manager()
    logger.info("已初始化恢复管理器")
    
    # 初始化字幕恢复系统
    subtitle_recovery = get_subtitle_recovery()
    logger.info("已初始化字幕恢复系统")
    
    # 初始化模型恢复系统
    model_recovery = get_model_recovery()
    logger.info("已初始化模型恢复系统")


def register_custom_error_handlers() -> None:
    """注册自定义错误处理器"""
    error_handler = get_error_handler()
    model_recovery = get_model_recovery()
    subtitle_recovery = get_subtitle_recovery()
    
    # 注册模型加载错误处理器
    def handle_model_load_error(error: Exception, context: Dict[str, Any]) -> bool:
        logger.info(f"处理模型加载错误: {error}")
        if "model_name" in context:
            return model_recovery.recover_model_loading_error(context["model_name"], error)
        return False
    
    # 注册字幕格式错误处理器
    def handle_srt_format_error(error: Exception, context: Dict[str, Any]) -> bool:
        logger.info(f"处理字幕格式错误: {error}")
        if "file" in context:
            try:
                subtitle_recovery.recover_srt_file(context["file"])
                return True
            except Exception as e:
                logger.error(f"字幕恢复失败: {e}")
        return False
    
    # 注册文件操作错误处理器
    def handle_file_operation_error(error: Exception, context: Dict[str, Any]) -> bool:
        logger.info(f"处理文件操作错误: {error}")
        if hasattr(error, "details") and "file_path" in error.details:
            file_path = error.details["file_path"]
            # 检查是否有备份文件
            backup_path = f"{file_path}.bak"
            if os.path.exists(backup_path):
                try:
                    from src.utils.file_checker import restore_from_backup
                    return restore_from_backup(backup_path, file_path)
                except Exception as e:
                    logger.error(f"从备份恢复失败: {e}")
        return False
    
    # 注册处理器
    error_handler.register_error_handler(ErrorCode.MODEL_LOAD_ERROR, handle_model_load_error)
    error_handler.register_error_handler(ErrorCode.SRT_FORMAT_ERROR, handle_srt_format_error)
    error_handler.register_error_handler(ErrorCode.FILE_OPERATION_ERROR, handle_file_operation_error)
    
    logger.info("已注册自定义错误处理器")


def init_all_error_handling(log_dir: str = "logs") -> None:
    """
    初始化所有错误处理和恢复系统
    
    Args:
        log_dir: 日志目录
    """
    logger.info("开始初始化容错与修复系统...")
    
    # 设置错误处理
    setup_error_handling(log_dir)
    
    # 初始化恢复系统
    initialize_recovery_systems()
    
    # 注册自定义错误处理器
    register_custom_error_handlers()
    
    # 创建必要的目录
    os.makedirs("recovery", exist_ok=True)
    os.makedirs("checkpoints", exist_ok=True)
    
    logger.success("容错与修复系统初始化完成")


def cleanup_old_recovery_data(max_age_days: int = 30) -> None:
    """
    清理老旧的恢复数据
    
    Args:
        max_age_days: 最大保留天数
    """
    recovery_manager = get_recovery_manager()
    cleaned_count = recovery_manager.cleanup_old_recovery_files(max_age_days)
    logger.info(f"已清理 {cleaned_count} 个过期恢复文件")


if __name__ == "__main__":
    # 如果直接运行此模块，初始化错误处理系统
    init_all_error_handling()
    print("容错与修复系统初始化完成") 