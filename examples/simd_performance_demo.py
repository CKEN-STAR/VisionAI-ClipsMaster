#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SIMD性能演示 - VisionAI-ClipsMaster
展示如何在项目中使用SIMD向量化优化
"""

import os
import sys
import time
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import logging

# 添加项目根目录到路径
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("simd-demo")

# 导入SIMD操作和优化路由器
from src.hardware.optimization_router import get_optimization_info
from src.hardware.simd_wrapper import get_simd_operations

def print_system_info():
    """打印系统信息"""
    import platform
    
    logger.info(f"系统: {platform.system()} {platform.release()}")
    logger.info(f"处理器: {platform.processor()}")
    logger.info(f"Python版本: {platform.python_version()}")
    logger.info(f"NumPy版本: {np.__version__}")
    
    # 获取优化信息
    opt_info = get_optimization_info()
    
    logger.info(f"优化路径: {opt_info['path']}")
    logger.info(f"SIMD宽度: {opt_info['details']['simd_width']}位")
    logger.info(f"CPU特性: {', '.join(opt_info['cpu_summary'].get('features', []))}")

def benchmark_matrix_operations(simd_ops, sizes=(500, 1000, 1500, 2000)):
    """
    对矩阵操作进行基准测试
    
    Args:
        simd_ops: SIMD操作对象
        sizes: 矩阵大小列表
    """
    results = {}
    
    for size in sizes:
        logger.info(f"测试矩阵大小: {size}x{size}")
        
        # 创建测试矩阵
        a = np.random.rand(size, size).astype(np.float32)
        b = np.random.rand(size, size).astype(np.float32)
        c = np.random.rand(size, size).astype(np.float32)
        
        operations = {
            "矩阵乘法": {
                "numpy": lambda: np.matmul(a, b),
                "simd": lambda: simd_ops.matrix_multiply(a, b)
            },
            "元素乘法": {
                "numpy": lambda: a * b,
                "simd": lambda: simd_ops.matrix_element_multiply(a, b)
            },
            "矩阵加法": {
                "numpy": lambda: a + b,
                "simd": lambda: simd_ops.matrix_add(a, b)
            },
            "融合乘加": {
                "numpy": lambda: a * b + c,
                "simd": lambda: simd_ops.fused_multiply_add(a, b, c)
            }
        }
        
        size_results = {}
        
        for op_name, op_funcs in operations.items():
            # NumPy实现
            start_time = time.time()
            c_numpy = op_funcs["numpy"]()
            numpy_time = time.time() - start_time
            
            # SIMD实现
            start_time = time.time()
            c_simd = op_funcs["simd"]()
            simd_time = time.time() - start_time
            
            # 验证结果正确性
            is_correct = np.allclose(c_numpy, c_simd, rtol=1e-4, atol=1e-4)
            
            # 计算加速比
            if numpy_time > 0:
                speedup = numpy_time / simd_time
            else:
                speedup = 0.0
            
            size_results[op_name] = {
                "numpy_time": numpy_time,
                "simd_time": simd_time,
                "speedup": speedup,
                "is_correct": is_correct
            }
            
            logger.info(f"  {op_name}:")
            logger.info(f"    NumPy时间: {numpy_time:.4f}秒")
            logger.info(f"    SIMD时间: {simd_time:.4f}秒")
            logger.info(f"    加速比: {speedup:.2f}x")
            logger.info(f"    结果正确: {is_correct}")
        
        results[size] = size_results
    
    return results

def plot_results(results, simd_type):
    """
    绘制基准测试结果
    
    Args:
        results: 基准测试结果
        simd_type: SIMD类型
    """
    sizes = list(results.keys())
    operations = list(results[sizes[0]].keys())
    
    # 创建结果目录
    results_dir = os.path.join(ROOT_DIR, "results")
    os.makedirs(results_dir, exist_ok=True)
    
    # 为每种操作绘制一个图表
    for op_name in operations:
        plt.figure(figsize=(10, 6))
        
        # 提取数据
        numpy_times = [results[size][op_name]["numpy_time"] for size in sizes]
        simd_times = [results[size][op_name]["simd_time"] for size in sizes]
        
        # 绘制时间对比
        plt.plot(sizes, numpy_times, "o-", label="NumPy")
        plt.plot(sizes, simd_times, "o-", label=f"SIMD ({simd_type})")
        
        plt.xlabel("矩阵大小 (N×N)")
        plt.ylabel("计算时间 (秒)")
        plt.title(f"{op_name}性能对比: NumPy vs SIMD ({simd_type})")
        plt.legend()
        plt.grid(True)
        
        # 保存图表
        plt.savefig(os.path.join(results_dir, f"{op_name}_{simd_type}.png"))
        
    # 绘制加速比图表
    plt.figure(figsize=(12, 8))
    
    for op_name in operations:
        speedups = [results[size][op_name]["speedup"] for size in sizes]
        plt.plot(sizes, speedups, "o-", label=op_name)
    
    plt.axhline(y=1.0, color="r", linestyle="--", label="无加速")
    plt.xlabel("矩阵大小 (N×N)")
    plt.ylabel("加速比 (NumPy时间 / SIMD时间)")
    plt.title(f"SIMD ({simd_type}) 各操作加速比")
    plt.legend()
    plt.grid(True)
    
    # 保存图表
    plt.savefig(os.path.join(results_dir, f"speedup_all_{simd_type}.png"))

def simd_integration_example():
    """SIMD集成示例，展示如何在项目中使用SIMD优化"""
    from src.hardware.optimization_router import OptimizationRouter
    
    # 创建优化路由器
    router = OptimizationRouter()
    
    # 获取优化级别
    level = router.get_optimization_level()
    logger.info(f"使用优化级别: {level['name']} - {level['description']}")
    
    # 获取SIMD操作对象
    simd_ops = router.get_simd_operations()
    if not simd_ops:
        logger.warning("SIMD操作不可用，将使用NumPy实现")
        return
    
    # 创建示例数据
    size = 1000
    input_data = np.random.rand(size, size).astype(np.float32)
    weights = np.random.rand(size, size).astype(np.float32)
    bias = np.random.rand(size, size).astype(np.float32)
    
    # 使用SIMD优化的矩阵乘法计算特征
    start_time = time.time()
    features = simd_ops.matrix_multiply(input_data, weights)
    
    # 应用激活函数 (y = x * w + b)
    output = simd_ops.matrix_add(features, bias)
    
    # 缩放结果
    result = simd_ops.vector_scale(output, 0.5)
    
    total_time = time.time() - start_time
    logger.info(f"完整计算链用时: {total_time:.4f}秒")
    
    # 计算处理速度
    ops = size * size * size * 2 + size * size * 2  # 乘法、加法和缩放操作的浮点运算数
    gflops = ops / total_time / 1e9
    logger.info(f"处理速度: {gflops:.2f} GFLOPS")
    
    return result

def main():
    """主函数"""
    logger.info("=== VisionAI-ClipsMaster SIMD性能演示 ===\n")
    
    # 打印系统信息
    print_system_info()
    
    # 获取SIMD操作对象
    simd_ops = get_simd_operations()
    
    logger.info(f"\nSIMD类型: {simd_ops.simd_type}")
    logger.info(f"SIMD库已加载: {simd_ops.simd_lib_loaded}")
    
    # 如果未加载SIMD库，使用的是NumPy实现，这在没有编译器的环境下是正常的
    if not simd_ops.simd_lib_loaded:
        logger.info("使用NumPy实现作为回退方案 (无需本地库)")
    
    # 运行基准测试
    logger.info("\n开始矩阵操作基准测试...")
    results = benchmark_matrix_operations(simd_ops, sizes=(200, 500, 800, 1000))
    
    # 绘制结果
    logger.info("\n生成性能图表...")
    plot_results(results, simd_ops.simd_type)
    
    # 展示SIMD集成示例
    logger.info("\n运行SIMD集成示例...")
    simd_integration_example()
    
    logger.info("\n演示完成。查看results目录下的图表来比较性能。")

if __name__ == "__main__":
    main() 