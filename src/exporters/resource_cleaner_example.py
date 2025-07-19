#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
资源回收引擎使用示例

展示如何使用资源回收引擎进行资源管理和清理。
"""

import os
import sys
import time
import tempfile
import numpy as np
from pathlib import Path

# 添加项目根目录到路径
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

# 导入资源清理器模块
from src.exporters.resource_cleaner import (
    get_resource_cleaner,
    CleanupPriority,
    emergency_cleanup,
    resource_cleanup_context
)

def create_temp_directory():
    """创建临时目录
    
    Returns:
        str: 临时目录路径
    """
    temp_dir = tempfile.mkdtemp(prefix="visionai_example_")
    print(f"创建临时目录: {temp_dir}")
    return temp_dir

def create_temp_files(directory, count=5):
    """在目录中创建临时文件
    
    Args:
        directory: 目录路径
        count: 文件数量
        
    Returns:
        list: 文件句柄列表
    """
    handles = []
    for i in range(count):
        file_path = os.path.join(directory, f"temp_file_{i}.txt")
        f = open(file_path, 'w')
        f.write(f"临时文件 {i} 内容")
        handles.append(f)
    
    print(f"创建了 {count} 个临时文件")
    return handles

def allocate_memory_buffer(size_mb=10):
    """分配内存缓冲区
    
    Args:
        size_mb: 缓冲区大小（MB）
        
    Returns:
        numpy.ndarray: 分配的数组
    """
    # 分配指定大小的内存
    buffer = np.ones((size_mb * 1024 * 1024 // 4,), dtype=np.float32)
    print(f"分配了 {size_mb}MB 内存缓冲区")
    return buffer

def example_basic_usage():
    """基本使用示例"""
    print("\n=== 基本使用示例 ===")
    
    # 获取资源清理器实例
    cleaner = get_resource_cleaner()
    
    # 创建临时资源
    temp_dir = create_temp_directory()
    file_handles = create_temp_files(temp_dir, 3)
    memory_buffer = allocate_memory_buffer(5)
    
    # 注册资源以便后续清理
    cleaner.register_temp_dir(temp_dir)
    for i, handle in enumerate(file_handles):
        cleaner.register_file_handle(f"file_{i}", handle)
    
    # 执行一些操作
    print("执行一些操作...")
    time.sleep(1)
    
    # 执行资源清理
    print("执行资源清理...")
    result = cleaner.clean(CleanupPriority.MEDIUM)
    
    # 打印清理结果
    print(f"清理结果: {result['status']}")
    print(f"清理了 {result['cleaned_items']} 项资源")
    print(f"清理耗时: {result['duration']:.3f}秒")
    
    # 验证清理结果
    print(f"临时目录是否存在: {os.path.exists(temp_dir)}")
    for handle in file_handles:
        print(f"文件句柄是否已关闭: {handle.closed}")

def example_context_manager():
    """上下文管理器示例"""
    print("\n=== 上下文管理器示例 ===")
    
    # 使用上下文管理器进行资源管理
    with resource_cleanup_context("视频处理") as context:
        # 创建临时目录
        temp_dir = create_temp_directory()
        context["temp_dir"] = temp_dir  # 自动清理
        
        # 打开文件
        file_handles = create_temp_files(temp_dir, 2)
        context["open_files"] = {f"file_{i}": handle for i, handle in enumerate(file_handles)}
        
        # 分配内存
        buffer = allocate_memory_buffer(10)
        
        # 执行一些操作
        print("执行一些操作...")
        time.sleep(1)
    
    # 上下文退出时自动清理所有资源
    print("上下文已退出")
    print(f"临时目录是否存在: {os.path.exists(temp_dir)}")
    for handle in file_handles:
        print(f"文件句柄是否已关闭: {handle.closed}")

def example_error_handling():
    """错误处理示例"""
    print("\n=== 错误处理示例 ===")
    
    try:
        # 使用上下文管理器
        with resource_cleanup_context("错误处理") as context:
            # 创建临时资源
            temp_dir = create_temp_directory()
            context["temp_dir"] = temp_dir
            
            file_handles = create_temp_files(temp_dir, 2)
            context["open_files"] = {f"file_{i}": handle for i, handle in enumerate(file_handles)}
            
            # 分配内存
            buffer = allocate_memory_buffer(10)
            
            # 模拟错误
            print("模拟错误...")
            raise ValueError("示例错误")
            
    except ValueError as e:
        print(f"捕获到异常: {e}")
        print(f"临时目录是否存在: {os.path.exists(temp_dir)}")
        for handle in file_handles:
            print(f"文件句柄是否已关闭: {handle.closed}")

def example_emergency_cleanup():
    """紧急清理示例"""
    print("\n=== 紧急清理示例 ===")
    
    # 获取资源清理器
    cleaner = get_resource_cleaner()
    
    # 创建临时资源
    temp_dir = create_temp_directory()
    file_handles = create_temp_files(temp_dir, 3)
    memory_buffer = allocate_memory_buffer(15)
    
    # 注册资源
    cleaner.register_temp_dir(temp_dir)
    for i, handle in enumerate(file_handles):
        cleaner.register_file_handle(f"file_{i}", handle)
    
    # 模拟关键操作
    try:
        print("执行关键操作...")
        # 模拟错误
        raise RuntimeError("严重错误")
    except Exception as e:
        print(f"捕获到严重错误: {e}")
        
        # 执行紧急清理
        print("执行紧急资源回收...")
        result = emergency_cleanup()
        
        print(f"紧急清理结果: {result['status']}")
        print(f"紧急清理了 {result['cleaned_items']} 项资源")
        
        # 验证清理结果
        print(f"临时目录是否存在: {os.path.exists(temp_dir)}")
        for handle in file_handles:
            print(f"文件句柄是否已关闭: {handle.closed}")
        
        # 重新抛出异常或执行错误恢复
        print("执行错误恢复...")

def example_custom_cleaner():
    """自定义清理器示例"""
    print("\n=== 自定义清理器示例 ===")
    
    # 定义自定义清理函数
    def custom_resource_cleaner(context):
        """自定义清理函数"""
        print("执行自定义清理...")
        # 执行特定的清理逻辑
        time.sleep(0.5)
        return {"cleaned_items": 1, "details": "清理了自定义资源"}
    
    # 获取资源清理器
    cleaner = get_resource_cleaner()
    
    # 注册自定义清理器
    cleaner.register_cleaner(custom_resource_cleaner, CleanupPriority.MEDIUM)
    
    # 执行清理
    print("执行资源清理，包括自定义清理器...")
    result = cleaner.clean(CleanupPriority.MEDIUM)
    
    print(f"清理结果: {result['status']}")
    print(f"清理了 {result['cleaned_items']} 项资源")
    
    # 查看详细结果
    if "custom_resource_cleaner" in result["details"]:
        custom_result = result["details"]["custom_resource_cleaner"]["result"]
        print(f"自定义清理器结果: {custom_result.get('details')}")

def run_all_examples():
    """运行所有示例"""
    print("=== 资源回收引擎使用示例 ===\n")
    
    example_basic_usage()
    example_context_manager()
    example_error_handling()
    example_emergency_cleanup()
    example_custom_cleaner()
    
    print("\n=== 示例结束 ===")

if __name__ == "__main__":
    run_all_examples() 