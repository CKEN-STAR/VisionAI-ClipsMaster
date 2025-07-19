#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
压缩模块命令行接口

提供命令行工具，用于评估压缩算法和管理系统压缩
"""

import os
import sys
import argparse
import logging
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("CompressionCLI")

def run_benchmark(args):
    """运行基准测试"""
    from src.compression.algorithm_benchmark import benchmark_algorithms
    
    # 解析数据类型
    data_types = args.data_types.split(",") if args.data_types else None
    
    # 解析数据大小
    sizes_mb = [float(s) for s in args.sizes.split(",")] if args.sizes else None
    
    # 运行基准测试
    results = benchmark_algorithms(
        data_types=data_types,
        sizes_mb=sizes_mb,
        output_dir=args.output_dir
    )
    
    # 打印结果摘要
    metrics = results["metrics"]
    print("\n基准测试结果摘要:")
    print(f"最佳总体算法: {metrics['best_overall']['algorithm']}, "
          f"平均压缩率: {metrics['best_overall']['avg_ratio']:.2f}")
    
    print(f"最快压缩: {metrics['fastest']['compress']['algorithm']}, "
          f"平均速度: {metrics['fastest']['compress']['avg_speed']:.2f} MB/s")
    
    print(f"最快解压: {metrics['fastest']['decompress']['algorithm']}, "
          f"平均速度: {metrics['fastest']['decompress']['avg_speed']:.2f} MB/s")
    
    # 打印每种数据类型的最佳结果
    print("\n各数据类型最佳算法:")
    for data_type, type_metrics in metrics.get("best_by_type", {}).items():
        for size_key, best in type_metrics.items():
            ratio_alg = best["best_ratio"]["algorithm"]
            ratio_val = best["best_ratio"]["value"]
            
            compress_alg = best["fastest_compress"]["algorithm"]
            compress_val = best["fastest_compress"]["value"]
            
            print(f"{data_type} ({size_key}):")
            print(f"  最佳压缩率: {ratio_alg} ({ratio_val:.3f})")
            print(f"  最快压缩: {compress_alg} ({compress_val:.1f} MB/s)")

def run_evaluation(args):
    """运行实际数据评估"""
    from src.compression.test_compression import main as run_test
    
    # 运行测试
    run_test()

def compress_resources(args):
    """压缩系统资源"""
    from src.compression.integration import compress_all_resources, get_compression_stats
    
    # 压缩资源
    results = compress_all_resources(
        type_filter=args.type_filter if args.type_filter != "all" else None,
        min_size_mb=args.min_size
    )
    
    # 打印结果
    print("\n压缩结果:")
    print(f"尝试压缩: {results['attempted']} 个资源")
    print(f"成功: {results['succeeded']} 个, 失败: {results['failed']} 个")
    print(f"总原始大小: {results['total_original_mb']:.2f}MB")
    print(f"总压缩大小: {results['total_compressed_mb']:.2f}MB")
    print(f"节省内存: {results['saved_mb']:.2f}MB")
    
    # 获取总体统计
    stats = get_compression_stats()
    print("\n系统压缩统计:")
    print(f"总压缩资源数: {stats['total_compressed_resources']}")
    print(f"平均压缩率: {stats['average_ratio']:.2f}")
    print(f"总节省内存: {stats['saved_mb']:.2f}MB")

def show_stats(args):
    """显示压缩统计"""
    from src.compression.integration import get_compression_stats
    
    # 获取统计信息
    stats = get_compression_stats()
    
    # 打印统计信息
    print("\n压缩统计信息:")
    print(f"总压缩资源数: {stats['total_compressed_resources']}")
    print(f"当前压缩资源数: {stats['current_compressed_resources']}")
    print(f"总原始大小: {stats['total_original_mb']:.2f}MB")
    print(f"总压缩后大小: {stats['total_compressed_mb']:.2f}MB")
    print(f"平均压缩率: {stats['average_ratio']:.2f}")
    print(f"总节省内存: {stats['saved_mb']:.2f}MB")
    
    # 按类型打印统计
    print("\n各类型资源统计:")
    for res_type, type_stats in stats.get("compression_by_type", {}).items():
        print(f"{res_type}:")
        print(f"  数量: {type_stats['count']}")
        print(f"  原始大小: {type_stats['original_mb']:.2f}MB")
        print(f"  压缩后大小: {type_stats['compressed_mb']:.2f}MB")
        print(f"  压缩率: {type_stats['ratio']:.2f}")
    
    # 按算法打印统计
    print("\n各算法统计:")
    for alg, alg_stats in stats.get("compression_by_algorithm", {}).items():
        print(f"{alg}:")
        print(f"  数量: {alg_stats['count']}")
        print(f"  原始大小: {alg_stats['original_mb']:.2f}MB")
        print(f"  压缩后大小: {alg_stats['compressed_mb']:.2f}MB")
        print(f"  压缩率: {alg_stats['ratio']:.2f}")

def update_config(args):
    """更新压缩配置"""
    from src.compression.integration import get_compression_manager
    
    # 获取压缩管理器
    manager = get_compression_manager()
    
    # 准备配置更新
    config = {}
    
    # 处理算法
    if args.algorithm:
        config["algorithm"] = args.algorithm
    
    # 处理平衡模式
    if args.balance_mode:
        config["balance_mode"] = args.balance_mode
    
    # 处理自动压缩
    if args.auto_compress is not None:
        config["auto_compress"] = args.auto_compress
    
    # 处理压缩阈值
    if args.threshold is not None:
        config["compression_threshold_mb"] = args.threshold
    
    # 处理压缩级别
    if args.level is not None:
        config["compression_level"] = args.level
    
    # 更新配置
    success = manager.update_compression_config(args.res_type, config)
    
    if success:
        print(f"成功更新 {args.res_type} 的压缩配置")
        
        # 显示更新后的配置
        updated_config = manager.get_compression_config(args.res_type)
        print("\n更新后的配置:")
        for key, value in updated_config.items():
            print(f"  {key}: {value}")
    else:
        print(f"更新 {args.res_type} 的压缩配置失败")

def show_config(args):
    """显示压缩配置"""
    from src.compression.integration import get_compression_manager
    
    # 获取压缩管理器
    manager = get_compression_manager()
    
    # 获取配置
    if args.res_type and args.res_type != "all":
        # 显示指定类型的配置
        config = manager.get_compression_config(args.res_type)
        print(f"\n{args.res_type} 的压缩配置:")
        for key, value in config.items():
            print(f"  {key}: {value}")
    else:
        # 显示所有配置
        all_configs = manager.get_compression_config()
        print("\n所有资源类型的压缩配置:")
        for res_type, config in all_configs.items():
            print(f"\n{res_type}:")
            for key, value in config.items():
                print(f"  {key}: {value}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="VisionAI-ClipsMaster 压缩模块命令行工具")
    subparsers = parser.add_subparsers(dest="command", help="命令")
    
    # 基准测试命令
    benchmark_parser = subparsers.add_parser("benchmark", help="运行压缩算法基准测试")
    benchmark_parser.add_argument("--data-types", help="要测试的数据类型，逗号分隔 (如 'text,model_weights')")
    benchmark_parser.add_argument("--sizes", help="要测试的数据大小(MB)，逗号分隔 (如 '0.5,5.0')")
    benchmark_parser.add_argument("--output-dir", default="reports/compression", help="输出目录")
    
    # 评估命令
    evaluate_parser = subparsers.add_parser("evaluate", help="在实际数据上评估压缩算法")
    
    # 压缩命令
    compress_parser = subparsers.add_parser("compress", help="压缩系统资源")
    compress_parser.add_argument("--type-filter", default="all", help="资源类型过滤器 (如 'model_weights')")
    compress_parser.add_argument("--min-size", type=float, default=1.0, help="最小资源大小(MB)")
    
    # 统计命令
    stats_parser = subparsers.add_parser("stats", help="显示压缩统计信息")
    
    # 配置命令
    config_parser = subparsers.add_parser("config", help="显示压缩配置")
    config_parser.add_argument("--res-type", default="all", help="资源类型 (如 'model_weights')")
    
    # 更新配置命令
    update_parser = subparsers.add_parser("update-config", help="更新压缩配置")
    update_parser.add_argument("res_type", help="资源类型 (如 'model_weights')")
    update_parser.add_argument("--algorithm", help="压缩算法 (如 'zstd', 'lz4')")
    update_parser.add_argument("--balance-mode", choices=["speed", "balanced", "ratio"], help="平衡模式")
    update_parser.add_argument("--auto-compress", type=bool, help="是否自动压缩")
    update_parser.add_argument("--threshold", type=float, help="压缩阈值(MB)")
    update_parser.add_argument("--level", type=int, help="压缩级别")
    
    # 解析参数
    args = parser.parse_args()
    
    # 根据命令执行对应的函数
    if args.command == "benchmark":
        run_benchmark(args)
    elif args.command == "evaluate":
        run_evaluation(args)
    elif args.command == "compress":
        compress_resources(args)
    elif args.command == "stats":
        show_stats(args)
    elif args.command == "config":
        show_config(args)
    elif args.command == "update-config":
        update_config(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 