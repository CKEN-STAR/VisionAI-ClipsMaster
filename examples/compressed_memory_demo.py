#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
透明压缩内存分配器演示

展示VisionAI-ClipsMaster系统的透明内存压缩功能
"""

import os
import sys
import time
import logging
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Dict, Any, List

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("MemoryDemo")

# 导入压缩内存分配器
from src.memory.compressed_allocator import (
    CompressedAllocator,
    malloc,
    access,
    free,
    get_compression_stats
)

def create_demo_data(size_mb: float) -> bytearray:
    """创建演示数据"""
    size_bytes = int(size_mb * 1024 * 1024)
    
    # 创建一个高度可压缩的数据集
    # 使用模拟的结构化记录，每个记录都有很多重复内容
    result = bytearray()
    record_size = 1024  # 每条记录1KB
    
    for i in range(0, size_bytes, record_size):
        # 记录头部 (可变部分)
        header = f"Record-{i//record_size:05d}".encode()
        
        # 记录内容 (高度可压缩的重复内容)
        content = b"VALUE:" + b"0" * (record_size - len(header) - 7)
        
        # 组合
        record = bytearray(header + content)
        record = record[:record_size]  # 确保大小一致
        
        # 添加到结果
        result.extend(record)
    
    return result[:size_bytes]

def demo_basic_usage():
    """演示基本用法"""
    logger.info("=== 透明压缩内存分配器基本用法 ===")
    
    # 创建测试数据
    data_size_mb = 50  # 50MB数据
    logger.info(f"创建 {data_size_mb}MB 演示数据...")
    data = create_demo_data(data_size_mb)
    
    logger.info(f"原始数据大小: {len(data)/1024/1024:.2f}MB")
    
    # 分配内存
    logger.info("分配压缩内存...")
    ptr = malloc(len(data))
    
    # 写入数据
    logger.info("写入数据...")
    from src.memory.compressed_allocator import default_allocator

# 内存使用警告阈值（百分比）
MEMORY_WARNING_THRESHOLD = 80

    buffer = default_allocator._read_memory(
        default_allocator.address_map[ptr], 
        default_allocator.memory_blocks[ptr].original_size
    )
    for i in range(len(data)):
        buffer[i] = data[i]
    
    # 获取初始统计信息
    stats_before = get_compression_stats()
    logger.info("\n初始内存统计:")
    logger.info(f"已分配块数: {stats_before['active_blocks']}")
    logger.info(f"已压缩块数: {stats_before['compressed_blocks']}")
    logger.info(f"原始内存大小: {stats_before['total_original_bytes']/1024/1024:.2f}MB")
    logger.info(f"压缩后大小: {stats_before['total_compressed_bytes']/1024/1024:.2f}MB")
    
    # 等待自动压缩
    logger.info("\n等待自动压缩...")
    time.sleep(6)  # 默认5秒后自动压缩
    
    # 获取压缩后统计信息
    stats_after = get_compression_stats()
    logger.info("\n压缩后内存统计:")
    logger.info(f"已分配块数: {stats_after['active_blocks']}")
    logger.info(f"已压缩块数: {stats_after['compressed_blocks']}")
    logger.info(f"原始内存大小: {stats_after['total_original_bytes']/1024/1024:.2f}MB")
    logger.info(f"压缩后大小: {stats_after['total_compressed_bytes']/1024/1024:.2f}MB")
    logger.info(f"压缩率: {stats_after['overall_compression_ratio']:.3f}")
    logger.info(f"内存节省: {stats_after['memory_saving_percent']:.1f}%")
    
    # 访问内存
    logger.info("\n访问压缩内存...")
    start_time = time.time()
    accessed_data = access(ptr)
    access_time = time.time() - start_time
    
    logger.info(f"访问耗时: {access_time*1000:.2f}ms")
    
    # 验证数据一致性
    logger.info("验证数据一致性...")
    if bytes(accessed_data) == bytes(data):
        logger.info("✓ 数据一致性验证通过")
    else:
        logger.error("✗ 数据一致性验证失败！")
    
    # 释放内存
    logger.info("释放内存...")
    free(ptr)
    
    logger.info("基本用法演示完成")

def demo_memory_savings():
    """演示不同类型数据的内存节省效果"""
    logger.info("\n=== 不同数据类型的内存节省效果 ===")
    
    # 创建压缩分配器
    allocator = CompressedAllocator(
        compression_algo='zstd',
        compression_level=3,
        compression_threshold=1024,  # 降低阈值以便于演示
        auto_compress_after=1  # 1秒后自动压缩
    )
    
    # 测试数据类型
    data_types = {
        'random': "随机数据 (不可压缩)",
        'text': "文本数据 (中等可压缩)",
        'structured': "结构化数据 (高度可压缩)",
        'zeros': "全零数据 (极度可压缩)"
    }
    
    data_size_mb = 10  # 每类10MB
    
    results = {}
    ptrs = []
    
    for data_type, desc in data_types.items():
        logger.info(f"\n测试 {desc}...")
        
        # 创建测试数据
        if data_type == 'random':
            data = bytearray(os.urandom(int(data_size_mb * 1024 * 1024)))
        elif data_type == 'text':
            words = ["压缩", "算法", "测试", "性能", "优化", "内存", "数据", "文本"]
            text = " ".join([words[i % len(words)] for i in range(int(data_size_mb * 1024 * 1024) // 8)])
            data = bytearray(text.encode('utf-8'))
        elif data_type == 'structured':
            data = create_demo_data(data_size_mb)
        elif data_type == 'zeros':
            data = bytearray(b"\x00" * int(data_size_mb * 1024 * 1024))
        
        # 分配内存
        ptr = allocator.malloc(len(data))
        ptrs.append(ptr)
        
        # 写入数据
        buffer = allocator._read_memory(
            allocator.address_map[ptr], 
            allocator.memory_blocks[ptr].original_size
        )
        for i in range(len(data)):
            buffer[i] = data[i]
        
        # 等待自动压缩
        time.sleep(2)
        
        # 获取块信息
        meta = allocator.memory_blocks[ptr]
        
        if meta.compressed_size:
            compression_ratio = meta.compressed_size / meta.original_size
            memory_saving = (1 - compression_ratio) * 100
        else:
            compression_ratio = 1.0
            memory_saving = 0.0
        
        # 记录结果
        results[data_type] = {
            'description': desc,
            'original_size_mb': data_size_mb,
            'compressed_size_mb': meta.compressed_size / 1024 / 1024 if meta.compressed_size else data_size_mb,
            'compression_ratio': compression_ratio,
            'memory_saving_percent': memory_saving,
            'state': meta.state.name
        }
        
        # 打印结果
        logger.info(f"状态: {meta.state.name}")
        logger.info(f"原始大小: {data_size_mb:.1f}MB")
        logger.info(f"压缩大小: {results[data_type]['compressed_size_mb']:.1f}MB")
        logger.info(f"压缩率: {compression_ratio:.3f}")
        logger.info(f"内存节省: {memory_saving:.1f}%")
    
    # 释放内存
    for ptr in ptrs:
        allocator.free(ptr)
    
    # 绘制结果图表
    try:
        plt.figure(figsize=(10, 6))
        
        types = list(results.keys())
        original_sizes = [results[t]['original_size_mb'] for t in types]
        compressed_sizes = [results[t]['compressed_size_mb'] for t in types]
        
        x = np.arange(len(types))
        width = 0.35
        
        plt.bar(x - width/2, original_sizes, width, label='原始大小 (MB)')
        plt.bar(x + width/2, compressed_sizes, width, label='压缩大小 (MB)')
        
        plt.ylabel('大小 (MB)')
        plt.title('不同数据类型的压缩效果')
        plt.xticks(x, [results[t]['description'] for t in types], rotation=15)
        plt.legend()
        
        plt.tight_layout()
        plt.savefig('compression_results.png')
        logger.info("结果图表已保存为 compression_results.png")
    except Exception as e:
        logger.warning(f"无法创建图表: {e}")
    
    return results

def demo_real_world_usage():
    """演示实际应用场景"""
    logger.info("\n=== 实际应用场景演示 ===")
    
    # 模拟一个大型数据处理场景，需要在内存中保存多个大数据块
    
    # 创建压缩分配器，使用更激进的压缩设置
    allocator = CompressedAllocator(
        compression_algo='zstd',
        compression_level=9,  # 更高压缩级别
        compression_threshold=64 * 1024,
        auto_compress_after=3
    )
    
    # 模拟大型数据集
    num_datasets = 10
    dataset_size_mb = 20  # 每个20MB
    
    # 分配数据集
    logger.info(f"分配 {num_datasets} 个数据集，每个 {dataset_size_mb}MB...")
    
    datasets = []
    ptrs = []
    
    for i in range(num_datasets):
        # 创建数据
        if i % 3 == 0:
            # 随机数据 (不可压缩)
            data = bytearray(os.urandom(int(dataset_size_mb * 1024 * 1024)))
            data_type = "随机"
        elif i % 3 == 1:
            # 文本数据 (中等可压缩)
            words = ["数据", "压缩", "内存", "优化"] * 25
            text = " ".join([words[j % len(words)] for j in range(int(dataset_size_mb * 1024 * 1024) // 8)])
            data = bytearray(text.encode('utf-8'))
            data_type = "文本"
        else:
            # 结构化数据 (高度可压缩)
            data = create_demo_data(dataset_size_mb)
            data_type = "结构化"
        
        # 分配内存
        ptr = allocator.malloc(len(data))
        
        # 写入数据
        buffer = allocator._read_memory(
            allocator.address_map[ptr], 
            allocator.memory_blocks[ptr].original_size
        )
        for j in range(len(data)):
            buffer[j] = data[j]
        
        datasets.append(data)
        ptrs.append(ptr)
        
        logger.info(f"分配数据集 {i+1}: {data_type}数据，大小 {len(data)/1024/1024:.1f}MB")
    
    # 显示初始内存使用情况
    total_mb = num_datasets * dataset_size_mb
    logger.info(f"\n总计分配: {total_mb:.1f}MB 原始数据")
    
    # 等待自动压缩
    logger.info("\n等待自动压缩...")
    time.sleep(5)
    
    # 获取当前内存使用情况
    stats = allocator.get_stats()
    compressed_blocks = stats['compressed_blocks']
    compressed_mb = stats['total_compressed_bytes'] / 1024 / 1024
    saved_mb = stats['memory_saved'] / 1024 / 1024
    
    logger.info(f"压缩后内存使用: {compressed_mb:.1f}MB")
    logger.info(f"节省内存: {saved_mb:.1f}MB")
    logger.info(f"压缩块数: {compressed_blocks}/{num_datasets}")
    logger.info(f"总压缩率: {stats['overall_compression_ratio']:.3f}")
    logger.info(f"内存节省百分比: {stats['memory_saving_percent']:.1f}%")
    
    # 模拟访问部分数据
    logger.info("\n模拟数据访问...")
    
    for i in [1, 4, 7]:  # 访问部分数据
        logger.info(f"访问数据集 {i+1}...")
        start_time = time.time()
        data = allocator.access(ptrs[i])
        access_time = time.time() - start_time
        
        logger.info(f"访问耗时: {access_time*1000:.2f}ms")
        
        # 验证
        if bytes(data) == bytes(datasets[i]):
            logger.info("✓ 数据验证通过")
        else:
            logger.error("✗ 数据验证失败")
    
    # 再次等待自动压缩
    logger.info("\n再次等待自动压缩...")
    time.sleep(4)
    
    # 重新获取统计
    stats = allocator.get_stats()
    logger.info(f"压缩块数: {stats['compressed_blocks']}/{num_datasets}")
    
    # 释放内存
    logger.info("\n释放所有内存...")
    for ptr in ptrs:
        allocator.free(ptr)
    
    logger.info("实际场景演示完成")

def run_demo():
    """运行完整演示"""
    logger.info("=== 开始透明压缩内存分配器演示 ===")
    
    demo_basic_usage()
    demo_memory_savings()
    demo_real_world_usage()
    
    logger.info("=== 透明压缩内存分配器演示完成 ===")

if __name__ == "__main__":
    run_demo() 