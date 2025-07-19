#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
日志路径验证模块

验证所有日志模块是否正确使用跨平台路径。
"""

from src.exporters.log_path import get_log_directory, get_temp_log_directory
from src.exporters.structured_logger import get_structured_logger
from src.exporters.log_writer import get_realtime_logger
from src.exporters.log_integration import get_logging_manager

def verify_log_paths():
    """验证日志路径"""
    # 获取基础路径
    base_log_dir = get_log_directory()
    temp_log_dir = get_temp_log_directory()
    
    print(f"基础日志目录: {base_log_dir}")
    print(f"临时日志目录: {temp_log_dir}")
    
    # 验证结构化日志记录器
    structured_logger = get_structured_logger()
    print(f"结构化日志记录器目录: {structured_logger.log_dir}")
    
    # 验证实时日志记录器
    realtime_logger = get_realtime_logger()
    print(f"实时日志记录器目录: {realtime_logger.writer.log_dir}")
    
    # 验证日志管理器
    logging_manager = get_logging_manager()
    print(f"日志管理器目录: {logging_manager.log_dir}")
    
    # 检查目录是否正确
    is_valid = (
        str(base_log_dir) in str(structured_logger.log_dir) and
        str(base_log_dir) in str(realtime_logger.writer.log_dir) and
        str(base_log_dir) in str(logging_manager.log_dir)
    )
    
    if is_valid:
        print("\n✓ 所有日志模块使用了正确的跨平台路径!")
    else:
        print("\n✗ 有日志模块未使用跨平台路径!")
        
    return is_valid

if __name__ == "__main__":
    print("=== 日志路径验证 ===\n")
    verify_log_paths() 