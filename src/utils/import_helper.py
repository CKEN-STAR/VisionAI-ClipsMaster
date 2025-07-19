"""
导入帮助工具

提供各种帮助导入模块的工具函数，解决常见导入问题
"""

import os
import sys
import importlib
from typing import Optional, Any, List
from loguru import logger


def ensure_module_path(module_dir: str) -> bool:
    """
    确保模块目录在系统路径中
    
    Args:
        module_dir: 模块目录
        
    Returns:
        bool: 是否成功
    """
    abs_path = os.path.abspath(module_dir)
    if abs_path not in sys.path:
        sys.path.append(abs_path)
        logger.debug(f"已将 {abs_path} 添加到系统路径")
    return True


def safe_import(module_name: str, fallback: Any = None) -> Any:
    """
    安全导入模块，如果失败则返回默认值
    
    Args:
        module_name: 模块名称
        fallback: 导入失败时返回的默认值
        
    Returns:
        导入的模块或默认值
    """
    try:
        return importlib.import_module(module_name)
    except ImportError:
        logger.warning(f"无法导入模块 {module_name}")
        return fallback


def ensure_interpretability_available() -> bool:
    """
    确保可解释性分析模块可用
    
    Returns:
        bool: 模块是否可用
    """
    # 确保src目录在系统路径中
    ensure_module_path("src")
    
    # 检查解释器模块是否存在
    try:
        import src.interpretability.pattern_explainer
        logger.info("可解释性分析模块已加载")
        return True
    except ImportError:
        logger.warning("可解释性分析模块不可用")
        return False
    except Exception as e:
        logger.error(f"加载可解释性分析模块时出错: {e}")
        return False 