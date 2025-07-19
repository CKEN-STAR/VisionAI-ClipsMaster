#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
指令级并行 (ILP) 优化演示 - VisionAI-ClipsMaster
展示指令级并行优化对不同类型任务的性能影响
"""

import os
import sys
import time
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# 添加项目根目录到路径
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

# 导入指令级并行模块
from src.hardware.parallel_scheduler import (
    ParallelScheduler, 
    parallel_for, 
    schedule_instructions,
    parallel,
    optimize_matrix_operations
)

# 尝试导入其他优化模块
try:
    from src.hardware.optimization_router import OptimizationRouter
    from src.hardware.memory_aligner import create_aligned_array
    from src.hardware.simd_utils import get_simd_ops
    HAS_OPTIMIZATIONS = True
except ImportError:
    HAS_OPTIMIZATIONS = False
    print("注意: 其他优化模块不可用，仅展示指令级并行优化")

print("=== VisionAI-ClipsMaster 指令级并行 (ILP) 优化演示 ===\n")

# 如果有优化路由器，获取最佳线程数
if HAS_OPTIMIZATIONS:
    router = OptimizationRouter()
    optimal_threads = router.get_optimization_level().get('parallel_threads', 4)
    print(f"根据当前硬件检测到的最佳线程数: {optimal_threads}")
else:
    optimal_threads = 4
    print(f"使用默认线程数: {optimal_threads}")

# 创建结果目录
output_dir = current_dir / 'results'
os.makedirs(output_dir, exist_ok=True)

#################################################
# 演示 1: 基本并行操作
#################################################
print("\n== 演示 1: 基本并行操作 ==")

def cpu_intensive_task(x):
    """模拟CPU密集型任务"""
    result = 0
    # 模拟复杂计算
    for _ in range(1000000):
        result += (x * x) % 10
    return result

# 创建测试数据
print("创建测试数据...")
test_data = list(range(16))  # 使用较小的数据，使演示快速完成

# 串行执行
print("\n串行执行...")
start_time = time.time()
serial_results = [cpu_intensive_task(x) for x in test_data]
serial_time = time.time() - start_time
print(f"串行执行耗时: {serial_time:.4f}秒")

# 并行执行
print("\n并行执行...")
scheduler = ParallelScheduler(n_jobs=optimal_threads)
start_time = time.time()
parallel_results = scheduler.schedule_instructions(cpu_intensive_task, test_data)
parallel_time = time.time() - start_time
print(f"并行执行({optimal_threads}线程)耗时: {parallel_time:.4f}秒")

# 计算加速比
speedup = serial_time / parallel_time if parallel_time > 0 else 0
print(f"加速比: {speedup:.2f}x")

# 验证结果
is_correct = parallel_results == serial_results
print(f"结果正确: {is_correct}")

#################################################
# 演示 2: 不同线程数的性能对比
#################################################
print("\n== 演示 2: 不同线程数的性能对比 ==")

def simple_task(x):
    """简单计算任务"""
    time.sleep(0.01)  # 模拟IO或计算耗时
    return x * x

# 创建较大的测试数据
data_size = 100
test_data = list(range(data_size))
print(f"使用数据大小: {data_size}项")

# 测试不同线程数
thread_counts = [1, 2, 4, 8]
execution_times = []

print("测试不同线程数的性能...")
for n_threads in thread_counts:
    print(f"  使用 {n_threads} 线程...", end="")
    scheduler = ParallelScheduler(n_jobs=n_threads)
    
    start_time = time.time()
    _ = scheduler.schedule_instructions(simple_task, test_data)
    exec_time = time.time() - start_time
    
    execution_times.append(exec_time)
    print(f" 耗时: {exec_time:.4f}秒")

# 绘制性能对比图
plt.figure(figsize=(10, 6))
plt.plot(thread_counts, execution_times, 'o-', linewidth=2)
plt.xlabel('线程数')
plt.ylabel('执行时间 (秒)')
plt.title('不同线程数对执行时间的影响')
plt.grid(True)
plt.savefig(output_dir / 'thread_scaling.png')
print(f"\n线程扩展性能图表已保存到: {output_dir / 'thread_scaling.png'}")

#################################################
# 演示 3: 装饰器用法
#################################################
print("\n== 演示 3: 装饰器用法 ==")

# 使用装饰器
@parallel(n_jobs=optimal_threads)
def process_data(items):
    # 这个函数应该处理单个项目，但装饰器会使其并行处理列表
    time.sleep(0.01)
    return items * 2

# 创建测试数据
test_data = list(range(100))

# 测试装饰器性能
print("使用装饰器执行并行处理...")
start_time = time.time()
decorator_results = process_data(test_data)
decorator_time = time.time() - start_time
print(f"装饰器方式耗时: {decorator_time:.4f}秒")

# 串行执行对比
print("对比串行执行...")
start_time = time.time()
serial_results = [x * 2 for x in test_data]
serial_time = time.time() - start_time
print(f"串行方式耗时: {serial_time:.4f}秒")

# 计算加速比
speedup = serial_time / decorator_time if decorator_time > 0 else 0
print(f"加速比: {speedup:.2f}x")

# 验证结果
is_correct = decorator_results == serial_results
print(f"结果正确: {is_correct}")

#################################################
# 演示 4: 矩阵运算优化
#################################################
print("\n== 演示 4: 矩阵运算优化 ==")

def matrix_operation(matrix):
    """矩阵运算函数"""
    # 模拟复杂的矩阵运算
    result = np.dot(matrix, matrix.T)  # 矩阵乘以其转置
    return result

# 创建测试矩阵
matrix_size = 500  # Reduce from 1000 to 500
print(f"创建 {matrix_size}x{matrix_size} 矩阵...")

# 创建对齐矩阵（如果可用）
if HAS_OPTIMIZATIONS:
    try:
        matrices = [
            create_aligned_array((matrix_size, matrix_size), np.float32)
            for _ in range(4)
        ]
        for m in matrices:
            m[:] = np.random.random((matrix_size, matrix_size)).astype(np.float32)
        print("使用内存对齐的矩阵")
    except:
        matrices = [
            np.random.random((matrix_size, matrix_size)).astype(np.float32)
            for _ in range(4)
        ]
        print("使用标准NumPy矩阵")
else:
    matrices = [
        np.random.random((matrix_size, matrix_size)).astype(np.float32)
        for _ in range(4)
    ]
    print("使用标准NumPy矩阵")

# 串行执行
print("\n串行执行矩阵运算...")
start_time = time.time()
serial_results = [matrix_operation(m) for m in matrices]
serial_time = time.time() - start_time
print(f"串行执行耗时: {serial_time:.4f}秒")

# 并行执行
print("\n并行执行矩阵运算...")
start_time = time.time()
parallel_results = optimize_matrix_operations(matrix_operation, matrices)
parallel_time = time.time() - start_time
print(f"并行执行耗时: {parallel_time:.4f}秒")

# 计算加速比
speedup = serial_time / parallel_time if parallel_time > 0 else 0
print(f"加速比: {speedup:.2f}x")

# 验证结果一致性
is_same = all(
    np.allclose(s, p, rtol=1e-5, atol=1e-5)
    for s, p in zip(serial_results, parallel_results)
)
print(f"结果一致: {is_same}")

#################################################
# 演示 5: 与其他优化技术集成
#################################################
if HAS_OPTIMIZATIONS:
    print("\n== 演示 5: 与其他优化技术集成 ==")
    
    try:
        # 获取SIMD操作
        simd_ops = get_simd_ops()
        print(f"使用SIMD类型: {simd_ops.simd_type}")
        
        # 创建对齐矩阵
        matrix_size = 1000
        print(f"创建 {matrix_size}x{matrix_size} 对齐矩阵...")
        
        a = create_aligned_array((matrix_size, matrix_size), np.float32)
        b = create_aligned_array((matrix_size, matrix_size), np.float32)
        
        # 填充随机数据
        a[:] = np.random.random((matrix_size, matrix_size)).astype(np.float32)
        b[:] = np.random.random((matrix_size, matrix_size)).astype(np.float32)
        
        # 定义使用SIMD的函数
        def simd_matrix_multiply(matrices):
            a, b = matrices
            return simd_ops.matrix_multiply(a, b)
        
        # 准备矩阵对
        matrix_pairs = [(a, b) for _ in range(5)]
        
        # 串行执行
        print("\n串行执行SIMD矩阵乘法...")
        start_time = time.time()
        serial_results = [simd_matrix_multiply(pair) for pair in matrix_pairs]
        serial_time = time.time() - start_time
        print(f"串行SIMD耗时: {serial_time:.4f}秒")
        
        # 并行执行
        print("\n并行执行SIMD矩阵乘法...")
        scheduler = ParallelScheduler(n_jobs=optimal_threads)
        start_time = time.time()
        parallel_results = scheduler.schedule_instructions(
            simd_matrix_multiply, matrix_pairs
        )
        parallel_time = time.time() - start_time
        print(f"并行SIMD耗时: {parallel_time:.4f}秒")
        
        # 计算加速比
        speedup = serial_time / parallel_time if parallel_time > 0 else 0
        print(f"SIMD+并行加速比: {speedup:.2f}x")
    except Exception as e:
        print(f"集成演示失败: {str(e)}")

#################################################
# 总结
#################################################
print("\n=== 演示总结 ===")

print("""
指令级并行 (ILP) 优化通过并行执行多个独立任务，充分利用多核CPU提高性能。
适用场景:
1. CPU密集型操作
2. 大规模数据处理
3. 可并行的独立任务

当与SIMD向量化和内存对齐优化结合时，性能提升最为显著。
""")

print("演示完成!") 