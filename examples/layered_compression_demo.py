#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
分层压缩策略演示

演示分层压缩策略的使用和效果
"""

import os
import sys
import time
import logging
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(project_root))

# 导入压缩模块
from src.compression.layered_policy import (
    get_policy_manager,
    compress_with_policy,
    get_resource_policy
)
from src.compression.compressors import (
    get_available_compressors,
    compress_data,
    decompress_data
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("Demo")

def get_safe_compression_algorithm():
    """获取系统上可用的安全压缩算法"""
    available = get_available_compressors()
    
    # 优先使用这些算法
    preferred = ["zstd", "lz4", "gzip", "bzip2", "lzma"]
    
    for alg in preferred:
        if alg in available:
            return alg
    
    # 如果没有找到首选算法，使用第一个可用的
    if available:
        return available[0]
    
    # 如果没有可用算法，使用无压缩
    return "none"

def demonstrate_layered_policy():
    """演示分层压缩策略"""
    logger.info("加载分层压缩策略...")
    
    # 获取策略管理器
    manager = get_policy_manager()
    
    # 获取所有策略
    policies = manager.get_all_policies()
    
    # 获取可用的压缩算法
    available_algs = get_available_compressors()
    logger.info(f"可用压缩算法: {available_algs}")
    
    # 确定一个安全的压缩算法
    safe_algorithm = get_safe_compression_algorithm()
    logger.info(f"将使用 {safe_algorithm} 作为安全压缩算法")
    
    # 打印策略摘要
    logger.info(f"加载了 {len(policies)} 个压缩策略:")
    for res_type, policy in policies.items():
        logger.info(f"  {res_type}: 算法={policy.get('algorithm', '-')}, "
                  f"级别={policy.get('level', '-')}, "
                  f"自动压缩={'是' if policy.get('auto_compress', False) else '否'}, "
                  f"阈值={policy.get('threshold_mb', '-')}MB")
    
    # 创建并压缩各种类型的测试数据
    test_data = {
        "model_weights": os.urandom(5 * 1024 * 1024),  # 5MB模型权重
        "subtitle": ("WEBVTT\n\n"
                     "00:00:01.000 --> 00:00:05.000\n"
                     "This is an example subtitle\n\n"
                     "00:00:06.000 --> 00:00:10.000\n"
                     "Testing layered compression policy\n\n" * 1000).encode('utf-8'),  # ~100KB字幕
        "log_data": "\n".join([
            f"2025-05-11 13:{minute}:{second} [INFO] Sample log entry {i}"
            for i in range(1000)
            for minute in range(0, 60, 10)
            for second in range(0, 60, 30)
        ]).encode('utf-8'),  # ~2MB日志
        "default": os.urandom(3 * 1024 * 1024)  # 3MB默认数据
    }
    
    results = {}
    
    logger.info("\n测试不同资源类型的压缩效果:")
    
    # 对每种数据类型应用相应的压缩策略
    for data_type, data in test_data.items():
        logger.info(f"\n处理 {data_type} 数据 ({len(data)/1024/1024:.2f}MB)...")
        
        # 获取该类型的压缩策略
        policy = manager.get_policy(data_type)
        logger.info(f"原始策略: {policy}")
        
        # 确保使用可用的压缩算法
        algorithm = policy.get("algorithm", "gzip")
        if algorithm not in available_algs:
            logger.warning(f"算法 {algorithm} 不可用，改用 {safe_algorithm}")
            algorithm = safe_algorithm
        
        # 压缩
        start_time = time.time()
        compressed, metadata = compress_data(
            data, 
            algorithm=algorithm
        )
        compress_time = time.time() - start_time
        
        # 解压
        start_time = time.time()
        decompressed = decompress_data(compressed, metadata)
        decompress_time = time.time() - start_time
        
        # 验证数据完整性
        if isinstance(data, bytes) and isinstance(decompressed, bytes):
            assert data == decompressed, f"{data_type} 解压后数据不匹配"
        
        # 保存结果
        original_size = len(data)
        compressed_size = len(compressed)
        ratio = compressed_size / original_size
        
        results[data_type] = {
            "original_mb": original_size / 1024 / 1024,
            "compressed_mb": compressed_size / 1024 / 1024,
            "ratio": ratio,
            "compress_time_ms": compress_time * 1000,
            "decompress_time_ms": decompress_time * 1000,
            "algorithm": algorithm,
            "level": policy.get("level", "default")
        }
        
        # 打印结果
        r = results[data_type]
        logger.info(f"结果: {r['original_mb']:.2f}MB -> {r['compressed_mb']:.2f}MB "
                  f"(比例: {r['ratio']:.2f})")
        logger.info(f"性能: 压缩 {r['compress_time_ms']:.1f}ms, "
                  f"解压 {r['decompress_time_ms']:.1f}ms")
    
    return results

def demonstrate_custom_policy():
    """演示自定义压缩策略"""
    logger.info("\n演示自定义压缩策略:")
    
    # 获取策略管理器
    manager = get_policy_manager()
    
    # 获取可用的压缩算法
    available_algs = get_available_compressors()
    logger.info(f"可用压缩算法: {available_algs}")
    
    # 确定安全的压缩算法
    if "lzma" in available_algs:
        high_compression_alg = "lzma"
    else:
        high_compression_alg = "gzip"
        
    if "gzip" in available_algs:
        balanced_alg = "gzip"
    else:
        balanced_alg = available_algs[0] if available_algs else "none"
    
    # 创建一个测试资源类型
    test_type = "custom_resource"
    
    # 测试数据
    test_data = os.urandom(10 * 1024 * 1024)  # 10MB
    
    # 测试不同的自定义策略
    test_policies = [
        {
            "name": "超高压缩率",
            "config": {
                "algorithm": high_compression_alg,
                "level": 9,
                "chunk_size": "1MB",
                "auto_compress": False,
                "threshold_mb": 1.0,
                "priority": "low"
            }
        },
        {
            "name": "平衡模式",
            "config": {
                "algorithm": balanced_alg,
                "level": 6,
                "chunk_size": "2MB",
                "auto_compress": True,
                "threshold_mb": 2.0,
                "priority": "medium"
            }
        }
    ]
    
    results = {}
    
    for policy_spec in test_policies:
        name = policy_spec["name"]
        config = policy_spec["config"]
        
        logger.info(f"\n测试策略: {name}")
        logger.info(f"配置: {config}")
        
        # 应用策略
        manager.set_policy(test_type, config)
        
        # 压缩
        start_time = time.time()
        compressed, metadata = compress_data(
            test_data, 
            algorithm=config["algorithm"]
        )
        compress_time = time.time() - start_time
        
        # 解压
        start_time = time.time()
        decompressed = decompress_data(compressed, metadata)
        decompress_time = time.time() - start_time
        
        # 验证数据
        assert test_data == decompressed, f"策略 '{name}' 解压后数据不匹配"
        
        # 保存结果
        original_size = len(test_data)
        compressed_size = len(compressed)
        ratio = compressed_size / original_size
        
        results[name] = {
            "original_mb": original_size / 1024 / 1024,
            "compressed_mb": compressed_size / 1024 / 1024,
            "ratio": ratio,
            "compress_time_ms": compress_time * 1000,
            "decompress_time_ms": decompress_time * 1000
        }
        
        # 打印结果
        r = results[name]
        logger.info(f"结果: {r['original_mb']:.2f}MB -> {r['compressed_mb']:.2f}MB "
                  f"(比例: {r['ratio']:.2f})")
        logger.info(f"性能: 压缩 {r['compress_time_ms']:.1f}ms, "
                  f"解压 {r['decompress_time_ms']:.1f}ms")
    
    return results

def main():
    """主函数"""
    logger.info("=== 分层压缩策略演示 ===")
    
    # 演示分层策略
    policy_results = demonstrate_layered_policy()
    
    # 演示自定义策略
    custom_results = demonstrate_custom_policy()
    
    # 打印总结
    logger.info("\n=== 压缩效果总结 ===")
    
    logger.info("\n资源类型压缩效果:")
    for data_type, result in policy_results.items():
        logger.info(f"{data_type} ({result['algorithm']} 级别{result['level']}): "
                  f"比例={result['ratio']:.2f}, "
                  f"压缩={result['compress_time_ms']:.1f}ms, "
                  f"解压={result['decompress_time_ms']:.1f}ms")
    
    logger.info("\n自定义策略效果:")
    for name, result in custom_results.items():
        logger.info(f"{name}: 比例={result['ratio']:.2f}, "
                  f"压缩={result['compress_time_ms']:.1f}ms, "
                  f"解压={result['decompress_time_ms']:.1f}ms")

if __name__ == "__main__":
    main() 