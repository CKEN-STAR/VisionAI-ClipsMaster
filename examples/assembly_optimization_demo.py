#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
平台特定汇编优化演示 - VisionAI-ClipsMaster
演示如何使用平台特定的汇编优化进行高性能计算
"""

import os
import sys
import time
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# 添加项目根目录到路径
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

# 导入汇编包装器
from src.hardware.assembly_wrapper import get_platform_asm, PlatformAsm
from src.hardware.optimization_router import get_optimization_info, get_assembly_operations

def print_header(title):
    """打印演示标题"""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)

def print_section(title):
    """打印章节标题"""
    print("\n" + "-" * 40)
    print(f" {title}")
    print("-" * 40)

def benchmark_matrix_multiply(asm: PlatformAsm, sizes=[256, 512, 1024]):
    """测试矩阵乘法性能"""
    print_section("矩阵乘法性能测试")
    
    for size in sizes:
        print(f"\n矩阵大小: {size}x{size}")
        
        # 创建随机矩阵
        a = np.random.rand(size, size).astype(np.float32)
        b = np.random.rand(size, size).astype(np.float32)
        
        # 预热
        _ = asm.optimized_matrix_multiply(a, b)
        _ = np.matmul(a, b)
        
        # 测试优化版本
        start = time.time()
        c_opt = asm.optimized_matrix_multiply(a, b)
        opt_time = time.time() - start
        print(f"  优化版本: {opt_time:.6f}秒")
        
        # 测试NumPy版本
        start = time.time()
        c_np = np.matmul(a, b)
        np_time = time.time() - start
        print(f"  NumPy版本: {np_time:.6f}秒")
        
        # 计算加速比和检查结果
        speedup = np_time / opt_time if opt_time > 0 else 0
        is_correct = np.allclose(c_opt, c_np, rtol=1e-4, atol=1e-4)
        print(f"  加速比: {speedup:.2f}x")
        print(f"  结果正确: {'是' if is_correct else '否'}")

def demo_vector_operations(asm: PlatformAsm, size=1000000):
    """演示向量操作"""
    print_section("向量操作演示")
    
    # 创建随机向量
    a = np.random.rand(size).astype(np.float32)
    b = np.random.rand(size).astype(np.float32)
    scalar = 2.5
    
    print(f"向量大小: {size}")
    
    # 点积操作
    print("\n向量点积:")
    start = time.time()
    dot_opt = asm.optimized_vector_dot(a, b)
    opt_time = time.time() - start
    print(f"  优化版本: {opt_time:.6f}秒, 结果: {dot_opt:.4f}")
    
    start = time.time()
    dot_np = np.dot(a, b)
    np_time = time.time() - start
    print(f"  NumPy版本: {np_time:.6f}秒, 结果: {dot_np:.4f}")
    
    speedup = np_time / opt_time if opt_time > 0 else 0
    print(f"  加速比: {speedup:.2f}x")
    
    # 向量缩放
    print("\n向量缩放:")
    start = time.time()
    scaled_opt = asm.optimized_vector_scale(a, scalar)
    opt_time = time.time() - start
    print(f"  优化版本: {opt_time:.6f}秒")
    
    start = time.time()
    scaled_np = a * scalar
    np_time = time.time() - start
    print(f"  NumPy版本: {np_time:.6f}秒")
    
    speedup = np_time / opt_time if opt_time > 0 else 0
    is_correct = np.allclose(scaled_opt, scaled_np, rtol=1e-4, atol=1e-4)
    print(f"  加速比: {speedup:.2f}x")
    print(f"  结果正确: {'是' if is_correct else '否'}")

def demo_using_optimization_router():
    """演示通过优化路由器使用汇编优化"""
    print_section("通过优化路由器使用汇编优化")
    
    # 获取系统优化信息
    opt_info = get_optimization_info()
    print(f"系统优化路径: {opt_info['path']}")
    print(f"指令集: {', '.join(opt_info['cpu_summary']['supported_features'])}")
    
    # 获取汇编优化实例
    asm_ops = get_assembly_operations()
    
    if asm_ops is None:
        print("平台汇编优化不可用，将使用标准实现")
        return
        
    # 测试简单矩阵乘法
    size = 512
    a = np.random.rand(size, size).astype(np.float32)
    b = np.random.rand(size, size).astype(np.float32)
    
    print(f"\n测试{size}x{size}矩阵乘法:")
    
    # 使用通用接口
    start = time.time()
    result = asm_ops.optimized_op(a, operation='matrix_multiply', b=b)
    duration = time.time() - start
    print(f"  耗时: {duration:.6f}秒")
    
def visualize_performance(asm: PlatformAsm):
    """可视化性能测试结果"""
    print_section("性能可视化")
    
    try:
        # 创建数据点
        sizes = [128, 256, 512, 1024, 2048]
        numpy_times = []
        asm_times = []
        speedups = []
        
        for size in sizes:
            a = np.random.rand(size, size).astype(np.float32)
            b = np.random.rand(size, size).astype(np.float32)
            
            # 测试NumPy版本
            start = time.time()
            _ = np.matmul(a, b)
            numpy_time = time.time() - start
            numpy_times.append(numpy_time)
            
            # 测试优化版本
            start = time.time()
            _ = asm.optimized_matrix_multiply(a, b)
            asm_time = time.time() - start
            asm_times.append(asm_time)
            
            # 计算加速比
            speedup = numpy_time / asm_time if asm_time > 0 else 0
            speedups.append(speedup)
            
        # 创建可视化
        plt.figure(figsize=(10, 8))
        
        # 执行时间对比
        plt.subplot(2, 1, 1)
        plt.plot(sizes, numpy_times, 'o-', label='NumPy')
        plt.plot(sizes, asm_times, 's-', label='汇编优化')
        plt.xlabel('矩阵大小')
        plt.ylabel('执行时间 (秒)')
        plt.title('矩阵乘法性能对比')
        plt.legend()
        plt.grid(True)
        
        # 加速比
        plt.subplot(2, 1, 2)
        plt.bar(range(len(sizes)), speedups)
        plt.xticks(range(len(sizes)), [str(s) for s in sizes])
        plt.xlabel('矩阵大小')
        plt.ylabel('加速比')
        plt.title('汇编优化加速比')
        plt.grid(True)
        
        plt.tight_layout()
        
        # 保存图表
        output_dir = os.path.join(ROOT_DIR, 'examples', 'results')
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, 'assembly_performance.png')
        plt.savefig(output_file)
        
        print(f"性能图表已保存到: {output_file}")
    except Exception as e:
        print(f"创建性能图表失败: {str(e)}")
        
def practical_example(asm: PlatformAsm):
    """实际应用示例：批量图像卷积计算"""
    print_section("实际应用示例：批量图像卷积计算")
    
    # 模拟批量图像数据 (10张图像，每张128x128)
    batch_size = 10
    img_size = 128
    images = np.random.rand(batch_size, img_size, img_size).astype(np.float32)
    
    # 模拟卷积核
    kernel_size = 3
    kernel = np.random.rand(kernel_size, kernel_size).astype(np.float32)
    
    # 使用优化的矩阵操作实现卷积
    def optimized_convolution(images, kernel):
        batch, h, w = images.shape
        k_h, k_w = kernel.shape
        result = np.zeros((batch, h-k_h+1, w-k_w+1), dtype=np.float32)
        
        # 展开卷积核为一维数组
        flat_kernel = kernel.flatten()
        
        # 对每张图像应用卷积
        for b in range(batch):
            for i in range(h-k_h+1):
                for j in range(w-k_w+1):
                    # 提取图像补丁
                    patch = images[b, i:i+k_h, j:j+k_w].flatten()
                    # 使用优化的点积计算
                    result[b, i, j] = asm.optimized_vector_dot(patch, flat_kernel)
                    
        return result
    
    # 使用NumPy实现卷积的参考函数
    def numpy_convolution(images, kernel):
        batch, h, w = images.shape
        k_h, k_w = kernel.shape
        result = np.zeros((batch, h-k_h+1, w-k_w+1), dtype=np.float32)
        
        for b in range(batch):
            for i in range(h-k_h+1):
                for j in range(w-k_w+1):
                    result[b, i, j] = np.sum(images[b, i:i+k_h, j:j+k_w] * kernel)
                    
        return result
    
    # 测试优化版本
    start = time.time()
    res_opt = optimized_convolution(images, kernel)
    opt_time = time.time() - start
    print(f"优化版本耗时: {opt_time:.6f}秒")
    
    # 测试NumPy版本
    start = time.time()
    res_np = numpy_convolution(images, kernel)
    np_time = time.time() - start
    print(f"NumPy版本耗时: {np_time:.6f}秒")
    
    # 验证结果并计算加速比
    is_correct = np.allclose(res_opt, res_np, rtol=1e-4, atol=1e-4)
    speedup = np_time / opt_time if opt_time > 0 else 0
    print(f"加速比: {speedup:.2f}x")
    print(f"结果正确: {'是' if is_correct else '否'}")
    print(f"输出形状: {res_opt.shape}")
    
def main():
    """主函数"""
    print_header("VisionAI-ClipsMaster 平台特定汇编优化演示")
    
    # 获取平台信息
    print(f"系统: {sys.platform}")
    print(f"Python版本: {sys.version.split()[0]}")
    
    # 获取汇编优化实例
    asm = get_platform_asm()
    
    # 显示库信息
    info = asm.get_library_info()
    print(f"\n汇编库信息:")
    print(f"  可用性: {'可用' if info['available'] else '不可用'}")
    
    if info['available']:
        print(f"  版本: {info['version']}")
        print(f"  优化级别: {info['optimization_level']}")
        print(f"  平台ID: {info['platform_id']}")
        
        # 运行演示
        benchmark_matrix_multiply(asm)
        demo_vector_operations(asm)
        demo_using_optimization_router()
        visualize_performance(asm)
        practical_example(asm)
    else:
        print("\n汇编优化库不可用，所有操作将使用NumPy回退实现")
        print("要构建汇编库，请运行以下命令之一:")
        print("  python build_assembly_extension.py")
        print("  python build_assembly_cmake.py")
    
    print("\n演示完成!")

if __name__ == "__main__":
    main() 