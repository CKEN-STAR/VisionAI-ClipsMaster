#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
无损压缩核心引擎演示

展示VisionAI-ClipsMaster系统的高性能无损压缩功能
"""

import os
import sys
import time
import logging
import json
import numpy as np
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("CompressionDemo")

# 导入压缩模块
from src.compression.core import (
    Compressor,
    compress,
    decompress,
    compress_file,
    decompress_file,
    benchmark
)

def demo_basic_compression():
    """基本压缩功能演示"""
    logger.info("=== 基本压缩功能演示 ===")
    
    # 创建测试数据
    data_size = 10 * 1024 * 1024  # 10MB
    test_data = os.urandom(data_size)
    
    logger.info(f"原始数据大小: {len(test_data)/1024/1024:.2f}MB")
    
    # 使用不同的压缩算法
    algorithms = ["zstd", "lz4", "gzip"]
    
    for algo in algorithms:
        logger.info(f"\n使用 {algo} 算法压缩:")
        
        # 压缩
        start_time = time.time()
        compressed, metadata = compress(test_data, algo=algo)
        compress_time = time.time() - start_time
        
        # 解压
        start_time = time.time()
        decompressed = decompress(compressed, metadata)
        decompress_time = time.time() - start_time
        
        # 验证
        success = decompressed == test_data
        
        # 计算性能指标
        ratio = len(compressed) / len(test_data)
        compress_speed = len(test_data) / (compress_time * 1024 * 1024)  # MB/s
        decompress_speed = len(test_data) / (decompress_time * 1024 * 1024)  # MB/s
        
        # 打印结果
        logger.info(f"压缩率: {ratio:.3f}")
        logger.info(f"压缩大小: {len(compressed)/1024/1024:.2f}MB")
        logger.info(f"压缩速度: {compress_speed:.1f}MB/s")
        logger.info(f"解压速度: {decompress_speed:.1f}MB/s")
        logger.info(f"数据验证: {'成功' if success else '失败'}")
        logger.info(f"压缩元数据: {json.dumps(metadata, indent=2)}")

def demo_object_compression():
    """对象压缩演示"""
    logger.info("\n=== Python对象压缩演示 ===")
    
    # 创建一些Python对象
    python_objects = [
        # 字典
        {"name": "VisionAI-ClipsMaster", "version": "1.0.0", "data": [1, 2, 3, 4] * 1000},
        
        # 列表
        [{"id": i, "value": f"item-{i}", "tags": ["tag1", "tag2"]} for i in range(1000)],
        
        # 集合
        {f"key-{i}" for i in range(2000)},
        
        # NumPy数组
        np.random.randn(1000, 1000)
    ]
    
    object_names = ["字典", "列表", "集合", "NumPy数组"]
    
    for obj, name in zip(python_objects, object_names):
        logger.info(f"\n压缩 {name}:")
        
        # 压缩对象
        start_time = time.time()
        compressed, metadata = compress(obj, algo="zstd")
        compress_time = time.time() - start_time
        
        # 解压对象
        start_time = time.time()
        decompressed = decompress(compressed, metadata)
        decompress_time = time.time() - start_time
        
        # 验证(对于NumPy数组需要特殊处理)
        if isinstance(obj, np.ndarray):
            success = np.array_equal(obj, decompressed)
        else:
            success = obj == decompressed
        
        # 打印结果
        logger.info(f"原始对象内存: {sys.getsizeof(obj):,} 字节")
        logger.info(f"压缩后大小: {len(compressed):,} 字节")
        logger.info(f"压缩率: {len(compressed) / sys.getsizeof(obj):.3f}")
        logger.info(f"压缩时间: {compress_time*1000:.1f}ms")
        logger.info(f"解压时间: {decompress_time*1000:.1f}ms")
        logger.info(f"数据验证: {'成功' if success else '失败'}")

def demo_file_compression():
    """文件压缩演示"""
    logger.info("\n=== 文件压缩演示 ===")
    
    # 创建临时测试文件
    test_file_path = Path(project_root) / "temp_test_file.dat"
    compressed_file = Path(project_root) / "temp_test_file.vaic"
    restored_file = Path(project_root) / "temp_test_file_restored.dat"
    
    # 生成有模式的测试数据(便于压缩)
    logger.info("创建测试文件...")
    file_size_mb = 50
    
    # 创建模式数据，每个块512KB，共100个块
    block_size = 512 * 1024
    num_blocks = int(file_size_mb * 1024 * 1024 / block_size)
    
    with open(test_file_path, 'wb') as f:
        for i in range(num_blocks):
            # 每个块重复相同的模式，便于压缩
            pattern = f"Block{i:04d}:".encode() + bytes([(i + j) % 256 for j in range(256)])
            block = pattern * (block_size // len(pattern) + 1)
            f.write(block[:block_size])
    
    # 确认文件大小
    actual_size = os.path.getsize(test_file_path)
    logger.info(f"测试文件大小: {actual_size/1024/1024:.2f}MB")
    
    try:
        # 压缩文件
        logger.info("\n压缩文件:")
        compress_stats = compress_file(
            test_file_path, 
            compressed_file, 
            algo="zstd", 
            level=3
        )
        
        logger.info(f"压缩文件大小: {compress_stats['output_size']/1024/1024:.2f}MB")
        logger.info(f"压缩比例: {compress_stats['compression_ratio']:.2f}")
        logger.info(f"压缩速度: {compress_stats['compress_speed_mbs']:.1f}MB/s")
        
        # 解压文件
        logger.info("\n解压文件:")
        decompress_stats = decompress_file(
            compressed_file,
            restored_file
        )
        
        logger.info(f"解压速度: {decompress_stats['decompress_speed_mbs']:.1f}MB/s")
        
        # 验证
        original_size = os.path.getsize(test_file_path)
        restored_size = os.path.getsize(restored_file)
        
        if original_size == restored_size:
            # 比较文件内容的前10KB和最后10KB
            with open(test_file_path, 'rb') as f1, open(restored_file, 'rb') as f2:
                header1 = f1.read(10240)
                f1.seek(-10240, 2)
                footer1 = f1.read()
                
                header2 = f2.read(10240)
                f2.seek(-10240, 2)
                footer2 = f2.read()
                
                if header1 == header2 and footer1 == footer2:
                    logger.info("文件验证成功 ✓")
                else:
                    logger.error("文件内容不匹配 ✗")
        else:
            logger.error(f"文件大小不匹配: 原始={original_size}, 恢复={restored_size}")
        
    finally:
        # 清理临时文件
        for file_path in [test_file_path, compressed_file, restored_file]:
            if os.path.exists(file_path):
                os.unlink(file_path)
                logger.debug(f"已删除临时文件: {file_path}")

def performance_benchmark():
    """压缩性能基准测试"""
    logger.info("\n=== 压缩性能基准测试 ===")
    
    # 执行基准测试
    logger.info("运行多算法基准测试...")
    results = benchmark(data_size=20*1024*1024, iterations=2)
    
    # 打印结果
    for algo, metrics in results.items():
        logger.info(f"\n{algo} 性能:")
        logger.info(f"  压缩速度: {metrics['compression_speed']:.1f}MB/s")
        logger.info(f"  解压速度: {metrics['decompression_speed']:.1f}MB/s")
        logger.info(f"  压缩比例: {metrics['ratio']:.3f}")
        
        # 检查性能目标
        meets_compression_target = metrics['compression_speed'] >= 300
        meets_decompression_target = metrics['decompression_speed'] >= 800
        
        logger.info(f"  压缩速度目标(≥300MB/s): {'✓' if meets_compression_target else '✗'}")
        logger.info(f"  解压速度目标(≥800MB/s): {'✓' if meets_decompression_target else '✗'}")

def main():
    """主函数"""
    logger.info("开始VisionAI-ClipsMaster无损压缩核心引擎演示...")
    
    # 运行基本压缩演示
    demo_basic_compression()
    
    # 运行对象压缩演示
    demo_object_compression()
    
    # 运行文件压缩演示
    demo_file_compression()
    
    # 运行性能基准测试
    performance_benchmark()
    
    logger.info("\n演示完成!")

if __name__ == "__main__":
    main() 