#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
探针初始化模块 - 确保内存探针在应用启动时正确配置和注册

此模块负责在应用启动时初始化内存探针系统，并确保探针被注入到关键代码点。
"""

import os
import sys
import logging
from typing import Dict, Any, List, Optional

# 导入探针模块
from src.utils.memory_probes import (
    get_probe_manager,
    auto_inject_probes,
    PROBE_CONFIG
)

# 配置日志
logger = logging.getLogger("ProbeInitializer")

class ProbeInitializer:
    """探针初始化器类"""
    
    def __init__(self):
        """初始化探针初始化器"""
        self.manager = get_probe_manager()
        self.initialized = False
        
    def initialize(self, config_override: Optional[Dict[str, Any]] = None) -> bool:
        """
        初始化探针系统
        
        Args:
            config_override: 可选的配置覆盖参数
            
        Returns:
            初始化是否成功
        """
        if self.initialized:
            logger.info("探针系统已经初始化，跳过")
            return True
            
        try:
            # 应用配置覆盖
            if config_override:
                for key, value in config_override.items():
                    if key in PROBE_CONFIG:
                        PROBE_CONFIG[key] = value
                        logger.info(f"覆盖探针配置: {key} = {value}")
            
            # 初始化探针系统
            logger.info("初始化内存探针系统...")
            auto_inject_probes()
            
            # 记录注入点
            injection_points = PROBE_CONFIG.get("injection_points", [])
            injection_points_str = "\n    ".join([
                f"{point.get('module')}.{point.get('function')} (级别: {point.get('level', 'medium')})"
                for point in injection_points
            ])
            logger.info(f"配置的探针注入点:\n    {injection_points_str}")
            
            # 标记为已初始化
            self.initialized = True
            logger.info("内存探针系统初始化完成")
            return True
            
        except Exception as e:
            logger.error(f"初始化探针系统失败: {str(e)}")
            return False
    
    def register_additional_injection_points(self, injection_points: List[Dict[str, Any]]) -> bool:
        """
        注册额外的探针注入点
        
        Args:
            injection_points: 注入点配置列表
            
        Returns:
            注册是否成功
        """
        try:
            for point in injection_points:
                PROBE_CONFIG["injection_points"].append(point)
                
            if self.initialized:
                # 如果已经初始化，立即注入新的探针
                self.manager.inject_probes()
                
            logger.info(f"已注册{len(injection_points)}个额外探针注入点")
            return True
            
        except Exception as e:
            logger.error(f"注册额外注入点失败: {str(e)}")
            return False
            
    def add_custom_probe(self, 
                       function_path: str, 
                       level: str = "medium") -> bool:
        """
        添加自定义探针到特定函数
        
        Args:
            function_path: 函数路径（格式: 模块.函数名）
            level: 探针级别
            
        Returns:
            添加是否成功
        """
        try:
            # 解析模块和函数名
            parts = function_path.rsplit(".", 1)
            if len(parts) != 2:
                logger.error(f"无效的函数路径: {function_path}")
                return False
                
            module_name, function_name = parts
            
            # 创建注入点配置
            injection_point = {
                "module": module_name,
                "function": function_name,
                "level": level
            }
            
            # 注册到配置
            PROBE_CONFIG["injection_points"].append(injection_point)
            
            if self.initialized:
                # 尝试立即注入
                try:
                    module = __import__(module_name, fromlist=[""])
                    if hasattr(module, function_name):
                        self.manager.inject_probes()
                        logger.info(f"已添加并注入探针: {function_path} (级别: {level})")
                    else:
                        logger.warning(f"已添加探针配置，但函数不存在: {function_path}")
                except ImportError:
                    logger.warning(f"已添加探针配置，但模块不存在: {module_name}")
                    
            return True
            
        except Exception as e:
            logger.error(f"添加自定义探针失败: {str(e)}")
            return False

# 全局探针初始化器
_PROBE_INITIALIZER = None

def get_probe_initializer() -> ProbeInitializer:
    """获取探针初始化器单例"""
    global _PROBE_INITIALIZER
    if _PROBE_INITIALIZER is None:
        _PROBE_INITIALIZER = ProbeInitializer()
    return _PROBE_INITIALIZER

# 默认的额外注入点配置
DEFAULT_ADDITIONAL_POINTS = [
    # 大文件解析模块
    {
        "module": "src.core.srt_parser",
        "function": "parse_file",
        "level": "medium"
    },
    # 资源分配函数
    {
        "module": "src.memory.resource_tracker",
        "function": "allocate_resource",
        "level": "high"
    },
    # 模型加载器适配器
    {
        "module": "src.core.model_loader_adapter",
        "function": "load_model_with_config",
        "level": "critical"
    },
    # 缓存管理器
    {
        "module": "src.core.cache_manager",
        "function": "allocate_cache",
        "level": "high"
    }
]

def initialize_probes(enable_additional_points: bool = True) -> bool:
    """
    初始化内存探针系统
    
    Args:
        enable_additional_points: 是否启用额外的默认注入点
        
    Returns:
        初始化是否成功
    """
    initializer = get_probe_initializer()
    
    # 先初始化基本探针
    success = initializer.initialize()
    
    # 注册额外注入点
    if success and enable_additional_points:
        initializer.register_additional_injection_points(DEFAULT_ADDITIONAL_POINTS)
        
    return success 