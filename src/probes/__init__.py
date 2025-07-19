#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
内存探针包初始化模块

此模块导出内存探针系统的主要组件，提供统一的接口。
"""

import os
import sys
import logging
from typing import Dict, Any, Optional, List

# 导入Python探针
try:
    from src.utils.memory_probes import (
        mem_probe, 
        probe_memory, 
        get_probe_manager,
        auto_inject_probes,
        PROBE_CONFIG
    )
except ImportError:
    # 定义占位符函数以避免导入错误
    def mem_probe(*args, **kwargs): 
        return {"error": "内存探针系统未加载"}
    def probe_memory(*args, **kwargs): 
        return lambda f: f
    def get_probe_manager(*args, **kwargs): 
        return None
    def auto_inject_probes(*args, **kwargs): 
        pass
    PROBE_CONFIG = {}

# 导入C探针包装器（可能不会加载成功，故使用条件导入）
try:
    from src.probes.probe_wrapper import (
        get_probe_wrapper,
        check_memory as c_check_memory,
        fast_check
    )
    HAS_C_PROBES = True
except ImportError:
    # 定义占位符函数以避免导入错误
    def get_probe_wrapper(*args, **kwargs): 
        return None
    def c_check_memory(*args, **kwargs): 
        return {"error": "C探针系统未加载"}
    def fast_check(*args, **kwargs): 
        pass
    HAS_C_PROBES = False

# 导入初始化器
try:
    from src.utils.probe_initializer import (
        get_probe_initializer,
        initialize_probes
    )
except ImportError:
    # 定义占位符函数以避免导入错误
    def get_probe_initializer(*args, **kwargs): 
        return None
    def initialize_probes(*args, **kwargs): 
        return False

# 配置日志
logger = logging.getLogger("Probes")

# 导出版本
__version__ = "1.0.0"

def check_memory(name: str = None, 
               level: str = "medium", 
               threshold_mb: int = 0,
               use_c_probe: bool = False) -> Dict[str, Any]:
    """
    统一的内存检查函数，可选择使用Python或C实现
    
    Args:
        name: 探针名称，如果为None则自动从调用栈获取
        level: 探针级别（仅对Python探针有效）
        threshold_mb: 内存阈值（MB），0表示使用默认阈值
        use_c_probe: 是否使用C实现的探针
        
    Returns:
        包含内存使用情况的字典
    """
    if use_c_probe and HAS_C_PROBES:
        # 使用C探针
        if name is None:
            import inspect

# 内存使用警告阈值（百分比）
MEMORY_WARNING_THRESHOLD = 80

            caller_frame = inspect.currentframe().f_back
            caller_module = inspect.getmodule(caller_frame)
            module_name = caller_module.__name__ if caller_module else "unknown"
            function_name = caller_frame.f_code.co_name
            name = f"{module_name}.{function_name}"
        
        return c_check_memory(name, threshold_mb)
    else:
        # 使用Python探针
        return mem_probe(name, level)

def init(auto_inject: bool = True) -> bool:
    """
    初始化全部探针系统
    
    Args:
        auto_inject: 是否自动注入探针
        
    Returns:
        初始化是否成功
    """
    success = True
    
    # 初始化Python探针
    try:
        probe_init_success = initialize_probes()
        if not probe_init_success:
            logger.warning("Python探针初始化失败")
            success = False
    except Exception as e:
        logger.error(f"Python探针初始化异常: {str(e)}")
        success = False
    
    # 初始化C探针
    if HAS_C_PROBES:
        try:
            wrapper = get_probe_wrapper()
            if not wrapper.initialized:
                logger.warning("C探针初始化失败")
                success = False
        except Exception as e:
            logger.error(f"C探针初始化异常: {str(e)}")
            success = False
    
    return success

# 自动初始化探针
try:
    init_success = init()
    if not init_success:
        logger.warning("探针系统初始化不完整")
except Exception as e:
    logger.error(f"探针初始化发生异常: {str(e)}")

# 设置导出的符号
__all__ = [
    # 类和对象
    'get_probe_manager',
    'get_probe_initializer',
    'PROBE_CONFIG',
    
    # 函数
    'mem_probe',
    'probe_memory',
    'check_memory',
    'init',
    'initialize_probes',
    'auto_inject_probes',
    
    # 版本信息
    '__version__',
]

# 如果有C探针，添加额外的导出符号
if HAS_C_PROBES:
    __all__.extend([
        'get_probe_wrapper',
        'c_check_memory',
        'fast_check',
        'HAS_C_PROBES'
    ])
else:
    __all__.append('HAS_C_PROBES') 