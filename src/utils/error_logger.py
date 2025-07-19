import logging
import json
import traceback
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
from src.utils.exceptions import ClipMasterError
from typing import Dict, Any, Optional

def get_runtime_context():
    """收集当前运行时上下文信息"""
    try:
        import psutil
        import torch
        
        process = psutil.Process()
        memory_info = process.memory_info()
        
        # 检查是否有CUDA可用
        gpu_available = torch.cuda.is_available() if hasattr(torch, 'cuda') else False
        
        # 收集当前活动的模型信息
        active_model = "unknown"
        from src.core import model_manager
        if hasattr(model_manager, 'get_active_model'):
            try:
                active_model = model_manager.get_active_model()
            except:
                pass
        
        return {
            "memory_usage": memory_info.rss // (1024 * 1024),  # 转换为MB
            "active_model": active_model,
            "gpu_available": gpu_available,
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "os_name": os.name
        }
    except Exception as e:
        # 如果收集信息失败，返回基本信息
        return {
            "memory_usage": 0,
            "active_model": "unknown",
            "gpu_available": False,
            "error_context": str(e)
        }

class ErrorLogger:
    """错误日志记录器，负责将异常信息写入结构化日志"""
    
    _instance = None
    
    def __new__(cls):
        """单例模式实现"""
        if cls._instance is None:
            cls._instance = super(ErrorLogger, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初始化日志记录器"""
        if getattr(self, '_initialized', False):
            return
            
        # 创建日志目录
        os.makedirs('logs', exist_ok=True)
        
        # 配置错误日志记录器
        self.logger = logging.getLogger('error')
        self.logger.setLevel(logging.ERROR)
        
        # 如果已经有处理器，不再添加
        if not self.logger.handlers:
            # 配置日志轮转
            handler = RotatingFileHandler(
                'logs/errors.log', 
                maxBytes=5*1024*1024,  # 5MB
                backupCount=10,
                encoding='utf-8'
            )
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        
        # 标记为已初始化
        self._initialized = True

    def log(self, error: ClipMasterError):
        """结构化日志记录
        
        Args:
            error: ClipMaster异常实例
        """
        # 确保异常是ClipMasterError类型
        if not isinstance(error, ClipMasterError):
            error = ClipMasterError(
                message=str(error),
                details={"original_type": error.__class__.__name__}
            )
            
        # 构建日志条目
        entry = {
            "timestamp": datetime.now().isoformat(),
            "code": getattr(error.code, 'value', 0),
            "code_name": getattr(error.code, 'name', 'UNKNOWN_ERROR'),
            "message": str(error),
            "details": error.details,
            "stack": traceback.format_exc(),
            "context": get_runtime_context()
        }
        
        # 记录日志
        self.logger.error(json.dumps(entry, ensure_ascii=False, default=str))
        
        # 针对严重错误，同时输出到控制台
        if hasattr(error, 'critical') and error.critical:
            from loguru import logger
            logger.critical(f"严重错误: {error.code.name} - {str(error)}")

def get_error_logger() -> ErrorLogger:
    """获取错误日志记录器的单例实例"""
    return ErrorLogger() 