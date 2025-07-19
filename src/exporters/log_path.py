#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
日志路径管理工具

提供日志文件存储路径的相关功能，包括目录创建、路径生成和过期日志清理。
确保日志文件结构合理、便于管理和查询。
"""

import os
import shutil
import time
import datetime
import glob
from pathlib import Path
from typing import List, Optional, Union, Tuple

# 默认日志目录相对路径
DEFAULT_LOG_DIR = "logs"
DEFAULT_TEMP_LOG_DIR = "logs/temp"
DEFAULT_ARCHIVE_LOG_DIR = "logs/archives/encrypted"

# 日志扩展名
LOG_EXTENSION = ".log"

def get_log_directory() -> Path:
    """获取日志主目录
    
    返回系统日志目录的Path对象。如果目录不存在会自动创建。
    
    Returns:
        日志目录的Path对象
    """
    # 获取应用根目录
    root_dir = Path(os.getenv("APP_ROOT", "."))
    
    # 构建日志目录路径
    log_dir = root_dir / DEFAULT_LOG_DIR
    
    # 确保目录存在
    log_dir.mkdir(parents=True, exist_ok=True)
    
    return log_dir

def get_temp_log_directory() -> Path:
    """获取临时日志目录
    
    返回临时日志文件的目录。如果不存在会自动创建。
    用于存储正在处理中的或临时性的日志文件。
    
    Returns:
        临时日志目录的Path对象
    """
    # 构建临时日志目录
    temp_log_dir = get_log_directory() / "temp"
    
    # 确保目录存在
    temp_log_dir.mkdir(parents=True, exist_ok=True)
    
    return temp_log_dir

def get_archived_logs_directory() -> Path:
    """获取加密归档日志目录
    
    返回加密归档日志文件的目录。如果不存在会自动创建。
    用于存储已加密的归档日志文件。
    
    Returns:
        加密归档日志目录的Path对象
    """
    # 构建加密归档日志目录
    archive_dir = get_log_directory() / "archives" / "encrypted"
    
    # 确保目录存在
    archive_dir.mkdir(parents=True, exist_ok=True)
    
    return archive_dir

def get_log_file_path(
    module_name: str, 
    date_str: Optional[str] = None,
    suffix: Optional[str] = None,
    is_temp: bool = False
) -> Path:
    """获取日志文件路径
    
    根据模块名称和日期创建标准化的日志文件路径
    
    Args:
        module_name: 模块名称
        date_str: 日期字符串，默认为当前日期
        suffix: 可选后缀
        is_temp: 是否为临时日志
        
    Returns:
        日志文件路径
    """
    # 确定基础目录
    base_dir = get_temp_log_directory() if is_temp else get_log_directory()
    
    # 如果未提供日期，使用当前日期
    if not date_str:
        date_str = datetime.datetime.now().strftime("%Y%m%d")
    
    # 构建文件名
    file_name = f"{module_name}_{date_str}"
    if suffix:
        file_name += f"_{suffix}"
    file_name += LOG_EXTENSION
    
    # 返回完整路径
    return base_dir / file_name

def clean_old_logs(
    max_age_days: int = 30, 
    exclude_patterns: Optional[List[str]] = None
) -> int:
    """清理过期日志文件
    
    删除超过指定天数的日志文件，可以指定例外模式
    
    Args:
        max_age_days: 最大保留天数
        exclude_patterns: 排除的文件模式列表
        
    Returns:
        清理的文件数
    """
    # 获取日志目录
    log_dir = get_log_directory()
    
    # 计算截止时间
    cutoff_time = time.time() - (max_age_days * 86400)
    
    # 默认排除模式
    if exclude_patterns is None:
        exclude_patterns = ["*permanent*", "*archive*", "*encrypted*"]
    
    # 查找所有日志文件
    log_files = list(log_dir.glob(f"**/*{LOG_EXTENSION}"))
    
    cleaned_count = 0
    cleaned_bytes = 0
    
    for log_file in log_files:
        # 检查文件是否应该被排除
        should_exclude = False
        for pattern in exclude_patterns:
            if log_file.match(pattern):
                should_exclude = True
                break
        
        if should_exclude:
            continue
        
        # 检查文件修改时间
        mtime = os.path.getmtime(log_file)
        if mtime < cutoff_time:
            # 获取文件大小
            file_size = os.path.getsize(log_file)
            
            try:
                # 删除文件
                os.remove(log_file)
                cleaned_count += 1
                cleaned_bytes += file_size
            except Exception as e:
                print(f"无法删除文件 {log_file}: {e}")
    
    return cleaned_count

if __name__ == "__main__":
    # 如果直接运行模块，执行简单的示例
    print(f"日志目录: {get_log_directory()}")
    print(f"临时日志目录: {get_temp_log_directory()}")
    print(f"加密归档日志目录: {get_archived_logs_directory()}")
    
    # 生成示例日志文件路径
    log_file = get_log_file_path("test_module")
    print(f"示例日志文件: {log_file}")
    
    # 清理旧日志
    count = clean_old_logs()
    print(f"清理了 {count} 个过期日志文件") 