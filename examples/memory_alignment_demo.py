#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
内存对齐优化演示 - VisionAI-ClipsMaster
展示内存对齐对常见操作的性能影响
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

# 导入内存对齐模块
from src.hardware.memory_aligner import (
    create_aligned_array,
    align_array,
    is_aligned,
    get_alignment_for_simd
)

print("=== VisionAI-ClipsMaster 内存对齐优化演示 ===\n")

# 获取当前平台的最佳对齐值
alignment = get_alignment_for_simd()
print(f"当前平台最佳内存对齐: {alignment}字节")

# 演示1: 创建对齐和非对齐数组
print("\n== 演示1: 对齐状态检查 ==")

# 创建标准NumPy数组
std_array = np.zeros((100, 100), dtype=np.float32)
print(f"标准NumPy数组是否{alignment}字节对齐: {is_aligned(std_array, alignment)}")

# 创建对齐数组
aligned_array = create_aligned_array((100, 100), dtype=np.float32)
print(f"使用create_aligned_array创建的数组是否{alignment}字节对齐: {is_aligned(aligned_array, alignment)}")

# 将标准数组对齐
aligned_copy = align_array(std_array)
print(f"使用align_array对齐的数组是否{alignment}字节对齐: {is_aligned(aligned_copy, alignment)}")

# 演示2: 矩阵乘法性能对比
print("\n== 演示2: 矩阵乘法性能对比 ==")

# 设置矩阵大小
sizes = [500, 1000, 2000]
iterations = 3  # 每个矩阵大小测试的迭代次数

# 保存结果的字典
results = {
    'sizes': sizes,
    'std_times': [],
    'aligned_times': [],
    'speedups': []
}

for size in sizes:
    print(f"\n矩阵大小: {size}x{size}")
    
    # 创建随机数据
    shape = (size, size)
    data = np.random.random(shape).astype(np.float32)
    
    # 创建标准数组和对齐数组
    std_array = data.copy()
    aligned_array = align_array(data)
    
    # 打印对齐状态
    print(f"标准数组是否{alignment}字节对齐: {is_aligned(std_array, alignment)}")
    print(f"对齐数组是否{alignment}字节对齐: {is_aligned(aligned_array, alignment)}")
    
    # 测试标准数组性能
    print("执行标准数组矩阵乘法...", end='', flush=True)
    start = time.time()
    for _ in range(iterations):
        result_std = np.dot(std_array, std_array)
    std_time = (time.time() - start) / iterations
    print(f" 完成, 平均耗时: {std_time*1000:.2f}ms")
    
    # 测试对齐数组性能
    print("执行对齐数组矩阵乘法...", end='', flush=True)
    start = time.time()
    for _ in range(iterations):
        result_aligned = np.dot(aligned_array, aligned_array)
    aligned_time = (time.time() - start) / iterations
    print(f" 完成, 平均耗时: {aligned_time*1000:.2f}ms")
    
    # 计算加速比
    speedup = std_time / aligned_time if aligned_time > 0 else 0
    print(f"加速比: {speedup:.2f}x")
    
    # 验证结果正确性
    is_same = np.allclose(result_std, result_aligned)
    print(f"结果一致性: {is_same}")
    
    # 保存结果
    results['std_times'].append(std_time * 1000)    # 转换为毫秒
    results['aligned_times'].append(aligned_time * 1000)
    results['speedups'].append(speedup)

# 演示3: 向量操作性能对比
print("\n== 演示3: 向量操作性能对比 ==")

vector_size = 10000000    # 1千万元素
iterations = 5

print(f"向量大小: {vector_size}")

# 创建随机向量
vec_data = np.random.random(vector_size).astype(np.float32)

# 创建标准数组和对齐数组
std_vec = vec_data.copy()
aligned_vec = align_array(vec_data)

# 验证对齐状态
print(f"标准向量是否{alignment}字节对齐: {is_aligned(std_vec, alignment)}")
print(f"对齐向量是否{alignment}字节对齐: {is_aligned(aligned_vec, alignment)}")

# 测试向量求和
print("\n向量求和测试:")

# 标准向量
print("执行标准向量求和...", end='', flush=True)
start = time.time()
for _ in range(iterations):
    result_std = np.sum(std_vec)
std_time = (time.time() - start) / iterations
print(f" 完成, 平均耗时: {std_time*1000:.2f}ms")

# 对齐向量
print("执行对齐向量求和...", end='', flush=True)
start = time.time()
for _ in range(iterations):
    result_aligned = np.sum(aligned_vec)
aligned_time = (time.time() - start) / iterations
print(f" 完成, 平均耗时: {aligned_time*1000:.2f}ms")

# 计算加速比
speedup = std_time / aligned_time if aligned_time > 0 else 0
print(f"加速比: {speedup:.2f}x")

# 测试向量乘法
print("\n向量元素乘法测试:")

# 标准向量
print("执行标准向量元素乘法...", end='', flush=True)
start = time.time()
for _ in range(iterations):
    result_std = std_vec * std_vec
std_time = (time.time() - start) / iterations
print(f" 完成, 平均耗时: {std_time*1000:.2f}ms")

# 对齐向量
print("执行对齐向量元素乘法...", end='', flush=True)
start = time.time()
for _ in range(iterations):
    result_aligned = aligned_vec * aligned_vec
aligned_time = (time.time() - start) / iterations
print(f" 完成, 平均耗时: {aligned_time*1000:.2f}ms")

# 计算加速比
speedup = std_time / aligned_time if aligned_time > 0 else 0
print(f"加速比: {speedup:.2f}x")

# 创建性能对比图表
print("\n生成性能对比图表...")

plt.figure(figsize=(12, 8))

# 矩阵乘法性能对比
plt.subplot(2, 1, 1)
x = range(len(sizes))
width = 0.35
plt.bar(x, results['std_times'], width, label='标准数组')
plt.bar([i + width for i in x], results['aligned_times'], width, label='对齐数组')
plt.xlabel('矩阵大小')
plt.ylabel('执行时间 (毫秒)')
plt.title('内存对齐优化效果 - 矩阵乘法')
plt.xticks([i + width/2 for i in x], [f"{s}x{s}" for s in sizes])
plt.legend()
plt.grid(axis='y', linestyle='--', alpha=0.7)

# 加速比
plt.subplot(2, 1, 2)
plt.bar(x, results['speedups'], 0.6)
plt.axhline(y=1.0, color='r', linestyle='-')
plt.xlabel('矩阵大小')
plt.ylabel('加速比')
plt.title('内存对齐加速比')
plt.xticks(x, [f"{s}x{s}" for s in sizes])
plt.grid(axis='y', linestyle='--', alpha=0.7)

plt.tight_layout()

# 保存图表
try:
    output_dir = os.path.join(current_dir, 'results')
    os.makedirs(output_dir, exist_ok=True)
    plt.savefig(os.path.join(output_dir, 'memory_alignment_performance.png'))
    print(f"性能图表已保存到 {output_dir}/memory_alignment_performance.png")
except Exception as e:
    print(f"保存图表时出错: {e}")

# 总结
print("\n=== 演示总结 ===")
avg_speedup = sum(results['speedups']) / len(results['speedups'])
print(f"矩阵乘法平均加速比: {avg_speedup:.2f}x")

if avg_speedup > 1.2:
    print("结论: 内存对齐提供了显著的性能提升！")
elif avg_speedup > 1.05:
    print("结论: 内存对齐提供了适度的性能提升")
elif avg_speedup > 0.95:
    print("结论: 内存对齐对性能影响不明显")
else:
    print("结论: 在此平台和操作上，内存对齐可能有轻微性能开销")

print("\n说明: 性能提升效果取决于硬件架构、矩阵大小和操作类型。")
print("      大型数据集和支持SIMD指令的处理器通常能获得更大收益。")
print("      对齐内存与SIMD和汇编优化结合使用时，效果最佳。")

print("\n演示完成！") 