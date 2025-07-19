#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster UI整合模块

将各个功能模块整合到UI中
"""

import os
import sys
import logging
from typing import Any, Dict, Optional

# 配置日志
logger = logging.getLogger(__name__)

# 导入系统监控
try:
    from src.monitor.system_monitor_ui import show_system_monitor
    HAS_MONITOR = True
except ImportError:
    logger.warning("无法导入系统监控模块")
    HAS_MONITOR = False

# 导入计算任务卸载器
try:
    from src.hardware.compute_offloader import get_compute_offloader
    HAS_OFFLOADER = True
except ImportError:
    logger.warning("无法导入计算任务卸载器模块")
    HAS_OFFLOADER = False

def integrate_system_monitor(main_window):
    """整合系统监控功能
    
    Args:
        main_window: 主窗口实例
    
    Returns:
        是否成功整合
    """
    if not HAS_MONITOR:
        logger.warning("系统监控模块不可用")
        return False
    
    try:
        # 添加系统监控功能
        def open_system_monitor():
            try:
                window = show_system_monitor()
                return window
            except Exception as e:
                logger.error(f"打开系统监控窗口失败: {e}")
                return None
        
        # 将打开函数绑定到主窗口
        main_window.open_system_monitor = open_system_monitor
        logger.info("系统监控功能已整合")
        return True
    except Exception as e:
        logger.error(f"整合系统监控功能失败: {e}")
        return False

def integrate_compute_offloader(main_window):
    """整合计算任务卸载器功能
    
    Args:
        main_window: 主窗口实例
    
    Returns:
        是否成功整合
    """
    if not HAS_OFFLOADER:
        logger.warning("计算任务卸载器模块不可用")
        return False
    
    try:
        # 获取计算任务卸载器
        offloader = get_compute_offloader()
        if not offloader:
            logger.warning("计算任务卸载器初始化失败")
            return False
        
        # 将卸载器绑定到主窗口
        main_window.compute_offloader = offloader
        
        # 添加卸载任务的方法
        def offload_task(func, *args, **kwargs):
            if hasattr(main_window, 'compute_offloader') and main_window.compute_offloader:
                return main_window.compute_offloader.offload(func, args, kwargs)
            else:
                # 如果卸载器不可用，直接执行
                return func(*args, **kwargs)
        
        main_window.offload_task = offload_task
        logger.info("计算任务卸载器功能已整合")
        return True
    except Exception as e:
        logger.error(f"整合计算任务卸载器功能失败: {e}")
        return False

def integrate_all(main_window):
    """整合所有功能
    
    Args:
        main_window: 主窗口实例
    
    Returns:
        成功整合的功能数量
    """
    success_count = 0
    
    if integrate_system_monitor(main_window):
        success_count += 1
    
    if integrate_compute_offloader(main_window):
        success_count += 1
    
    return success_count
