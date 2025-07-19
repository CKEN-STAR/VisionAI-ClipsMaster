#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
硬件加速压缩演示

展示如何使用硬件加速提高压缩性能
"""

import os
import sys
import time
import logging
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(level=logging.INFO, 
                  format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("HardwareAccelDemo")

# 导入压缩模块
from src.compression.hardware_accel import (
    get_best_hardware,
    CPUCompressor,
    TorchCUDACompressor,
    HardwareAcceleratedCompressor,
    benchmark_hardware,
    HARDWARE_INFO,
    HAS_CUDA
)

def print_system_info():
    """打印系统硬件信息"""
    print("\n======== 系统硬件信息 ========")
    print(f"CUDA可用: {'是' if HAS_CUDA else '否'}")
    
    if HAS_CUDA:
        print("\nCUDA设备:")
        for i, device in enumerate(HARDWARE_INFO["cuda"]["devices"]):
            print(f"  设备 #{i}: {device['name']}")
            print(f"  内存: {device['memory'] / (1024**3):.2f} GB")
    
    print("\n进行基准测试...\n")

def compress_file_demo(filename, out_dir="./compressed"):
    """
    演示文件压缩
    
    Args:
        filename: 要压缩的文件名
        out_dir: 输出目录
    """
    if not os.path.exists(filename):
        logger.error(f"文件不存在: {filename}")
        return
    
    # 创建输出目录
    os.makedirs(out_dir, exist_ok=True)
    
    # 读取文件
    with open(filename, "rb") as f:
        data = f.read()
    
    file_size = len(data)
    logger.info(f"文件大小: {file_size / 1024 / 1024:.2f} MB")
    
    # CPU压缩
    cpu_compressor = CPUCompressor(algo="zstd", level=3)
    
    start_time = time.time()
    cpu_compressed, cpu_metadata = cpu_compressor.compress(data)
    cpu_time = time.time() - start_time
    
    cpu_ratio = len(cpu_compressed) / file_size
    logger.info(f"CPU压缩: 比例={cpu_ratio:.3f}, 时间={cpu_time:.3f}秒, "
               f"速度={(file_size/cpu_time)/1024/1024:.2f} MB/s")
    
    # 保存CPU压缩结果
    cpu_output = os.path.join(out_dir, os.path.basename(filename) + ".cpu.zst")
    with open(cpu_output, "wb") as f:
        f.write(cpu_compressed)
    
    # 如果有CUDA，进行GPU压缩
    if HAS_CUDA:
        gpu_compressor = TorchCUDACompressor(algorithm="zstd", level=3)
        
        start_time = time.time()
        gpu_compressed, gpu_metadata = gpu_compressor.compress(data)
        gpu_time = time.time() - start_time
        
        gpu_ratio = len(gpu_compressed) / file_size
        gpu_speedup = cpu_time / gpu_time
        
        logger.info(f"GPU压缩: 比例={gpu_ratio:.3f}, 时间={gpu_time:.3f}秒, "
                   f"速度={(file_size/gpu_time)/1024/1024:.2f} MB/s")
        logger.info(f"GPU加速比: {gpu_speedup:.2f}x")
        
        # 保存GPU压缩结果
        gpu_output = os.path.join(out_dir, os.path.basename(filename) + ".gpu.zst")
        with open(gpu_output, "wb") as f:
            f.write(gpu_compressed)
    
    # 自动选择最佳硬件
    best_compressor = get_best_hardware(algorithm="zstd", level=3)
    logger.info(f"选择最佳硬件: {type(best_compressor).__name__}")

def main():
    """主函数"""
    print_system_info()
    
    # 创建测试文件
    test_file = "test_data.bin"
    if not os.path.exists(test_file):
        logger.info(f"创建测试文件: {test_file} (100MB)")
        with open(test_file, "wb") as f:
            f.write(os.urandom(100 * 1024 * 1024))
    
    # 压缩演示
    compress_file_demo(test_file)
    
    # 进行性能基准测试
    print("\n======== 性能基准测试 ========")
    results = benchmark_hardware(data_size=50*1024*1024, iterations=2)
    
    # 打印结果表格
    print("\n压缩性能比较:")
    print("| 硬件类型 | 压缩速度 (MB/s) | 解压速度 (MB/s) | 压缩比例 |")
    print("|----------|----------------|----------------|----------|")
    
    for hw_type, metrics in results.items():
        print(f"| {hw_type.upper()} | {metrics['compression_speed']:.1f} | "
              f"{metrics['decompression_speed']:.1f} | {metrics['ratio']:.3f} |")

if __name__ == "__main__":
    main() 