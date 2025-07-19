#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
指令级并行 (ILP) 优化最小演示 - VisionAI-ClipsMaster
简化版演示，展示指令级并行的基本功能和性能
"""

import os
import sys
import time
import numpy as np
from pathlib import Path

# 添加项目根目录到路径
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

# 导入指令级并行模块
from src.hardware.parallel_scheduler import ParallelScheduler

print("=== 指令级并行优化最小演示 ===\n")

# 创建线程数配置
n_threads = 4
print(f"使用 {n_threads} 个线程进行并行处理")

# 定义一个计算密集型函数
def compute_intensive(x):
    """模拟计算密集型任务"""
    result = 0
    for _ in range(1000000):
        result += (x * x) % 10
    return result

# 创建测试数据
print("\n创建测试数据...")
data_size = 16
test_data = list(range(data_size))
print(f"数据大小: {data_size}项")

# 串行执行
print("\n1. 串行执行...")
start_time = time.time()
serial_results = [compute_intensive(x) for x in test_data]
serial_time = time.time() - start_time
print(f"串行执行耗时: {serial_time:.4f}秒")

# 并行执行
print("\n2. 并行执行...")
scheduler = ParallelScheduler(n_jobs=n_threads)
start_time = time.time()
parallel_results = scheduler.schedule_instructions(compute_intensive, test_data)
parallel_time = time.time() - start_time
print(f"并行执行耗时: {parallel_time:.4f}秒")

# 计算加速比
speedup = serial_time / parallel_time if parallel_time > 0 else 0
print(f"加速比: {speedup:.2f}x")

# 验证结果
is_correct = parallel_results == serial_results
print(f"结果正确: {is_correct}")

# 性能统计
stats = scheduler.get_stats()
print(f"\n性能统计:")
print(f"  调度任务数: {stats['scheduled_tasks']}")
print(f"  完成任务数: {stats['completed_tasks']}")
print(f"  总耗时: {stats['total_time']:.4f}秒")
print(f"  加速比: {stats['speedup']:.2f}x")

print("\n演示完成!") 