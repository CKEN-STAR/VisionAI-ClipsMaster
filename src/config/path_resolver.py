#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
跨平台路径解析模块

此模块负责处理路径中的特殊标记，确保在不同操作系统(Windows/macOS/Linux)下正确解析路径。
支持以下特殊标记:
- "~": 用户主目录
- "%USERPROFILE%": Windows用户主目录
- "$HOME": UNIX/Linux用户主目录
- "${VAR}": 环境变量
"""

import os
import sys
import re
import platform
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

# 导入日志模块
try:
    from src.utils.log_handler import get_logger
    logger = get_logger("path_resolver")
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("path_resolver")


def resolve_special_path(raw_path: str) -> str:
    """处理路径中的特殊标记
    
    将路径中的特殊标记（如~、%USERPROFILE%、环境变量等）替换为实际路径
    
    Args:
        raw_path: 原始路径字符串
        
    Returns:
        str: 处理后的绝对路径
    """
    # 如果路径为空，返回当前目录
    if not raw_path:
        return os.path.abspath('.')
        
    # 创建替换规则字典
    replacements = {
        "~": os.path.expanduser("~"),
        "%USERPROFILE%": os.environ.get("USERPROFILE", ""),
        "$HOME": os.environ.get("HOME", ""),
        "%APPDATA%": os.environ.get("APPDATA", ""),
        "%LOCALAPPDATA%": os.environ.get("LOCALAPPDATA", ""),
        "%PROGRAMDATA%": os.environ.get("PROGRAMDATA", ""),
        "%TEMP%": os.environ.get("TEMP", ""),
        "%TMP%": os.environ.get("TMP", ""),
    }
    
    # 替换特殊标记
    for k, v in replacements.items():
        raw_path = raw_path.replace(k, v)
    
    # 处理${VAR}形式的环境变量
    env_var_pattern = r'\${([^}]+)}'
    matches = re.findall(env_var_pattern, raw_path)
    for match in matches:
        env_value = os.environ.get(match, "")
        raw_path = raw_path.replace(f"${{{match}}}", env_value)
    
    # 标准化路径分隔符
    if platform.system() == "Windows":
        raw_path = raw_path.replace('/', '\\')
    else:
        raw_path = raw_path.replace('\\', '/')
    
    # 返回绝对路径
    return os.path.abspath(raw_path)


def ensure_dir_exists(path: str) -> str:
    """确保目录存在，如果不存在则创建
    
    Args:
        path: 目录路径
        
    Returns:
        str: 目录的绝对路径
    """
    abs_path = resolve_special_path(path)
    os.makedirs(abs_path, exist_ok=True)
    return abs_path


def get_app_data_dir(app_name: str = "VisionAI-ClipsMaster") -> str:
    """获取应用数据目录，在不同操作系统下返回适当的路径
    
    Args:
        app_name: 应用名称
        
    Returns:
        str: 应用数据目录的绝对路径
    """
    system = platform.system()
    
    if system == "Windows":
        # Windows: %APPDATA%\AppName
        base_dir = os.environ.get("APPDATA", "")
        if not base_dir:
            base_dir = os.path.join(os.path.expanduser("~"), "AppData", "Roaming")
        app_dir = os.path.join(base_dir, app_name)
    elif system == "Darwin":
        # macOS: ~/Library/Application Support/AppName
        app_dir = os.path.join(os.path.expanduser("~"), 
                             "Library", "Application Support", app_name)
    else:
        # Linux/Unix: ~/.config/AppName
        base_dir = os.environ.get("XDG_CONFIG_HOME", "")
        if not base_dir:
            base_dir = os.path.join(os.path.expanduser("~"), ".config")
        app_dir = os.path.join(base_dir, app_name)
    
    # 确保目录存在
    os.makedirs(app_dir, exist_ok=True)
    return app_dir


def get_temp_dir(prefix: str = "visionai_") -> str:
    """获取临时目录
    
    Args:
        prefix: 临时目录前缀
        
    Returns:
        str: 临时目录的绝对路径
    """
    import tempfile
    temp_dir = os.path.join(tempfile.gettempdir(), f"{prefix}{os.getpid()}")
    os.makedirs(temp_dir, exist_ok=True)
    return temp_dir


def get_project_root() -> Path:
    """获取项目根目录路径
    
    Returns:
        Path: 项目根目录
    """
    try:
        # 查找包含特定文件/目录的根目录
        current_path = Path(__file__).resolve().parent
        while current_path != current_path.parent:
            if (current_path / "src").is_dir() and (current_path / "models").is_dir():
                return current_path
            current_path = current_path.parent
    except Exception as e:
        logger.error(f"获取项目根目录失败: {str(e)}")
    
    # 如果找不到项目根目录，返回当前文件的2级父目录
    return Path(__file__).resolve().parent.parent.parent


def convert_to_platform_path(path: str) -> str:
    """转换路径为当前平台适用的格式
    
    Args:
        path: 原始路径
        
    Returns:
        str: 适合当前平台的路径
    """
    if platform.system() == "Windows":
        # 转换为Windows路径格式
        path = path.replace('/', '\\')
        # 如果是网络路径但不是以\\开头的，添加正确前缀
        if path.startswith('\\') and not path.startswith('\\\\'):
            path = '\\' + path
    else:
        # 转换为UNIX路径格式
        path = path.replace('\\', '/')
        
    return path


def normalize_path(path: str) -> str:
    """标准化路径，解析特殊标记并转换为平台适用的格式
    
    Args:
        path: 原始路径
        
    Returns:
        str: 标准化后的路径
    """
    resolved_path = resolve_special_path(path)
    return convert_to_platform_path(resolved_path)


def get_relative_path(path: str, base_path: Optional[str] = None) -> str:
    """获取相对于指定基准路径的相对路径
    
    Args:
        path: 目标路径
        base_path: 基准路径，默认为项目根目录
        
    Returns:
        str: 相对路径
    """
    resolved_path = resolve_special_path(path)
    
    if base_path is None:
        base_path = str(get_project_root())
    else:
        base_path = resolve_special_path(base_path)
    
    try:
        return os.path.relpath(resolved_path, base_path)
    except ValueError:
        # 如果两个路径在不同的磁盘上，无法获取相对路径
        logger.warning(f"无法获取相对路径: {path} 相对于 {base_path}")
        return resolved_path


def is_subpath(path: str, parent_path: str) -> bool:
    """检查路径是否是另一个路径的子路径
    
    Args:
        path: 要检查的路径
        parent_path: 父路径
        
    Returns:
        bool: 如果path是parent_path的子路径则返回True
    """
    path = os.path.abspath(resolve_special_path(path))
    parent_path = os.path.abspath(resolve_special_path(parent_path))
    
    # 使用Path对象进行比较，这样可以处理不同操作系统的路径分隔符
    return Path(path).is_relative_to(Path(parent_path))


def join_paths(*paths: str) -> str:
    """连接多个路径部分，并标准化结果
    
    Args:
        *paths: 要连接的路径部分
        
    Returns:
        str: 连接并标准化后的路径
    """
    joined_path = os.path.join(*paths)
    return normalize_path(joined_path)


# 测试函数，如果作为独立脚本运行则执行
if __name__ == "__main__":
    # 打印一些示例路径解析结果
    test_paths = [
        "~/Documents",
        "%USERPROFILE%\\Documents",
        "$HOME/Downloads",
        "${TEMP}/test_folder",
        "../relative/path",
    ]
    
    print("跨平台路径解析测试:")
    for path in test_paths:
        resolved = resolve_special_path(path)
        print(f"原始路径: {path} -> 解析后: {resolved}")
    
    print(f"\n应用数据目录: {get_app_data_dir()}")
    print(f"临时目录: {get_temp_dir()}")
    print(f"项目根目录: {get_project_root()}") 