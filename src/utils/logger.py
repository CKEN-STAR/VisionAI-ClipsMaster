#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
日志工具模块

提供日志配置和简单的日志工具函数。
"""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from loguru import logger

def setup_logger(level=logging.INFO, log_dir="logs", name=None):
    """
    设置日志记录器
    
    Args:
        level: 日志级别
        log_dir: 日志文件目录
        name: 日志记录器名称
    
    Returns:
        配置好的logger对象
    """
    # 创建日志目录
    os.makedirs(log_dir, exist_ok=True)
    
    # 配置loguru
    logger.remove()  # 移除默认处理器
    
    # 添加控制台处理器
    log_format = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    logger.add(sys.stderr, format=log_format, level=level)
    
    # 添加文件处理器
    file_name = name if name else "app"
    file_path = os.path.join(log_dir, f"{file_name}.log")
    
    logger.add(
        file_path, 
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}", 
        level=level, 
        rotation="10 MB", 
        retention="7 days",
        encoding="utf-8"
    )
    
    return logger

def get_module_logger(module_name):
    """
    获取模块级别的日志记录器
    
    Args:
        module_name: 模块名称
    
    Returns:
        模块专用的logger对象
    """
    return logger.bind(name=module_name) 