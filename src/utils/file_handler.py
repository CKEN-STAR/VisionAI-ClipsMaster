#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
文件处理模块

提供文件和目录操作的工具函数
"""

import os
import json
import yaml
import shutil
import tempfile
import logging
from typing import List, Optional, Union, Dict, Any
from pathlib import Path
from loguru import logger

def ensure_dir_exists(directory_path: Union[str, Path]) -> str:
    """
    确保目录存在，如果不存在则创建
    
    Args:
        directory_path: 目录路径
        
    Returns:
        str: 创建的目录路径
    """
    if isinstance(directory_path, str):
        directory_path = Path(directory_path)
    
    # 确保父目录存在
    if not directory_path.parent.exists():
        directory_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 确保目录本身存在
    if not directory_path.exists():
        directory_path.mkdir(parents=True, exist_ok=True)
    
    return str(directory_path)

def is_file_exists(file_path: str) -> bool:
    """
    检查文件是否存在
    
    Args:
        file_path: 文件路径
        
    Returns:
        bool: 文件是否存在
    """
    return os.path.isfile(file_path)

def is_dir_exists(dir_path: str) -> bool:
    """
    检查目录是否存在
    
    Args:
        dir_path: 目录路径
        
    Returns:
        bool: 目录是否存在
    """
    return os.path.isdir(dir_path)

def is_writable(path: str) -> bool:
    """
    检查路径是否可写
    
    Args:
        path: 文件或目录路径
        
    Returns:
        bool: 路径是否可写
    """
    if os.path.exists(path):
        return os.access(path, os.W_OK)
    
    # 如果路径不存在，检查父目录是否可写
    parent_dir = os.path.dirname(path)
    if not parent_dir:  # 如果是当前目录
        parent_dir = '.'
    return os.access(parent_dir, os.W_OK)

def create_temp_dir(prefix: str = "visionai_") -> str:
    """
    创建临时目录
    
    Args:
        prefix: 临时目录名称前缀
        
    Returns:
        str: 临时目录路径
    """
    try:
        temp_dir = tempfile.mkdtemp(prefix=prefix)
        logger.debug(f"创建临时目录: {temp_dir}")
        return temp_dir
    except Exception as e:
        logger.error(f"创建临时目录失败: {str(e)}")
        raise

def remove_dir(directory: str, ignore_errors: bool = False) -> bool:
    """
    删除目录及其内容
    
    Args:
        directory: 目录路径
        ignore_errors: 是否忽略错误
        
    Returns:
        bool: 操作是否成功
    """
    try:
        if os.path.exists(directory):
            shutil.rmtree(directory, ignore_errors=ignore_errors)
            logger.debug(f"删除目录: {directory}")
        return True
    except Exception as e:
        logger.error(f"删除目录失败 {directory}: {str(e)}")
        return False

def list_files(directory: str, 
              pattern: Optional[str] = None, 
              recursive: bool = False) -> List[str]:
    """
    列出目录中的文件
    
    Args:
        directory: 目录路径
        pattern: 文件名匹配模式（支持通配符）
        recursive: 是否递归搜索子目录
        
    Returns:
        List[str]: 文件路径列表
    """
    result = []
    
    try:
        if not os.path.exists(directory):
            logger.warning(f"目录不存在: {directory}")
            return []
            
        if recursive:
            for root, _, files in os.walk(directory):
                for file in files:
                    if pattern is None or Path(file).match(pattern):
                        result.append(os.path.join(root, file))
        else:
            for file in os.listdir(directory):
                file_path = os.path.join(directory, file)
                if os.path.isfile(file_path):
                    if pattern is None or Path(file).match(pattern):
                        result.append(file_path)
        
        return result
    except Exception as e:
        logger.error(f"列出文件失败 {directory}: {str(e)}")
        return []

def get_file_size(file_path: str) -> int:
    """
    获取文件大小（字节）
    
    Args:
        file_path: 文件路径
        
    Returns:
        int: 文件大小（字节）
    """
    try:
        if os.path.isfile(file_path):
            return os.path.getsize(file_path)
        return 0
    except Exception as e:
        logger.error(f"获取文件大小失败 {file_path}: {str(e)}")
        return 0

def ensure_parent_dir_exists(file_path: str) -> bool:
    """
    确保文件的父目录存在
    
    Args:
        file_path: 文件路径
        
    Returns:
        bool: 操作是否成功
    """
    parent_dir = os.path.dirname(file_path)
    if parent_dir:
        return ensure_dir_exists(parent_dir)
    return True

def get_file_extension(file_path: Union[str, Path]) -> str:
    """
    获取文件扩展名（小写）
    
    Args:
        file_path: 文件路径
        
    Returns:
        str: 小写的扩展名(不包含点)
    """
    if isinstance(file_path, str):
        return os.path.splitext(file_path)[1].lower().lstrip('.')
    return file_path.suffix.lower().lstrip('.')

def is_valid_file(file_path: Union[str, Path], required_ext: Optional[List[str]] = None, min_size: int = 0) -> bool:
    """
    检查文件是否有效
    
    Args:
        file_path: 文件路径
        required_ext: 所需的扩展名列表(不包含点)
        min_size: 最小文件大小(字节)
        
    Returns:
        bool: 是否是有效文件
    """
    if isinstance(file_path, str):
        file_path = Path(file_path)
    
    # 检查文件是否存在
    if not file_path.exists() or not file_path.is_file():
        return False
    
    # 检查扩展名
    if required_ext is not None:
        if file_path.suffix.lower().lstrip('.') not in required_ext:
            return False
    
    # 检查文件大小
    if min_size > 0 and file_path.stat().st_size < min_size:
        return False
    
    return True

def save_json(data: Dict[str, Any], file_path: Union[str, Path], indent: int = 2) -> bool:
    """
    保存数据为JSON文件
    
    Args:
        data: 要保存的数据
        file_path: 文件路径
        indent: JSON缩进
        
    Returns:
        bool: 是否成功保存
    """
    if isinstance(file_path, Path):
        file_path = str(file_path)
    
    # 确保目录存在
    ensure_dir_exists(os.path.dirname(file_path))
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=indent)
        return True
    except Exception as e:
        print(f"保存JSON文件失败: {e}")
        return False

def load_json(file_path: Union[str, Path], default: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    加载JSON文件
    
    Args:
        file_path: 文件路径
        default: 文件不存在或加载失败时返回的默认值
        
    Returns:
        Dict[str, Any]: 加载的数据或默认值
    """
    if isinstance(file_path, Path):
        file_path = str(file_path)
    
    if not os.path.exists(file_path):
        return default if default is not None else {}
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载JSON文件失败: {e}")
        return default if default is not None else {} 