#!/usr/bin/env python
"""分片内存管理工具

此工具用于管理模型分片的内存使用，提供手动和自动卸载功能，
以及内存监控和卸载策略配置。
"""

import os
import sys
import time
import signal
import argparse
import psutil
from pathlib import Path
from loguru import logger

# 获取项目根目录并添加到路径
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.sharding.metadata_manager import MetadataManager
from src.sharding.cache_manager import ShardManager
from src.sharding.unload_strategy import create_unload_strategy, UnloadPriority


def format_bytes(size):
    """将字节格式化为人类可读的形式
    
    Args:
        size: 字节数
        
    Returns:
        str: 格式化后的字符串
    """
    power = 2**10
    n = 0
    power_labels = {0: 'B', 1: 'KB', 2: 'MB', 3: 'GB', 4: 'TB'}
    while size > power:
        size /= power
        n += 1
    return f"{size:.2f} {power_labels[n]}"


def monitor_memory(interval=2.0):
    """监控系统内存使用情况
    
    Args:
        interval: 监控间隔（秒）
    """
    try:
        while True:
            memory = psutil.virtual_memory()
            total = format_bytes(memory.total)
            used = format_bytes(memory.used)
            available = format_bytes(memory.available)
            percent = memory.percent
            
            logger.info(f"内存使用: {used}/{total} ({percent:.1f}%), 可用: {available}")
            time.sleep(interval)
    except KeyboardInterrupt:
        logger.info("内存监控已停止")


def unload_shards_interactive(shard_manager, unload_strategy):
    """交互式卸载分片
    
    显示当前加载的分片，并允许用户选择要卸载的分片
    
    Args:
        shard_manager: 分片管理器
        unload_strategy: 卸载策略
    """
    while True:
        # 获取当前缓存状态
        cached_shards = shard_manager.shard_cache.get_cached_shards()
        if not cached_shards:
            logger.info("当前没有加载的分片")
            break
            
        # 显示分片列表和内存使用
        print("\n当前加载的分片:")
        for i, shard_id in enumerate(cached_shards):
            memory_usage = unload_strategy.memory_usage.get(shard_id, 0)
            memory_str = format_bytes(memory_usage) if memory_usage > 0 else "未知"
            
            # 检查是否有依赖
            dependent_shards = unload_strategy.reverse_dependency_graph.get(shard_id, set())
            dependent_shards = [s for s in dependent_shards if s in cached_shards]
            
            if dependent_shards:
                print(f"  {i+1}. {shard_id} (内存: {memory_str}, 被 {', '.join(dependent_shards)} 依赖)")
            else:
                print(f"  {i+1}. {shard_id} (内存: {memory_str}, 无依赖)")
        
        print("\n选择操作:")
        print("  a. 自动卸载 (基于当前策略)")
        print("  q. 返回主菜单")
        print("  数字. 卸载指定分片")
        
        choice = input("请输入选择: ").strip().lower()
        
        if choice == 'q':
            break
        elif choice == 'a':
            # 自动卸载
            unloaded_count = unload_strategy.trigger_unload_if_needed()
            if unloaded_count > 0:
                logger.info(f"已自动卸载 {unloaded_count} 个分片")
            else:
                logger.info("没有分片需要卸载")
        else:
            try:
                index = int(choice) - 1
                if 0 <= index < len(cached_shards):
                    shard_id = cached_shards[index]
                    if shard_manager.shard_cache.remove(shard_id):
                        logger.info(f"已卸载分片: {shard_id}")
                    else:
                        logger.error(f"卸载分片失败: {shard_id}")
                else:
                    logger.warning("无效的选择")
            except ValueError:
                logger.warning("无效的输入")


def load_shards_interactive(shard_manager, model_name, metadata_manager):
    """交互式加载分片
    
    显示可用的分片，并允许用户选择要加载的分片
    
    Args:
        shard_manager: 分片管理器
        model_name: 模型名称
        metadata_manager: 元数据管理器
    """
    # 获取元数据
    metadata = metadata_manager.get_metadata(model_name)
    if not metadata:
        logger.error(f"无法获取模型 {model_name} 的元数据")
        return
        
    while True:
        # 获取所有分片和已加载分片
        all_shards = list(metadata.get_shards().keys())
        cached_shards = shard_manager.shard_cache.get_cached_shards()
        
        # 计算未加载的分片
        unloaded_shards = [s for s in all_shards if s not in cached_shards]
        
        if not unloaded_shards:
            logger.info("所有分片都已加载")
            break
            
        # 显示未加载的分片
        print("\n可加载的分片:")
        for i, shard_id in enumerate(unloaded_shards):
            # 获取依赖
            shard_info = metadata.get_shard(shard_id)
            dependencies = shard_info.get("depends_on", [])
            
            if dependencies:
                # 检查依赖是否已加载
                unloaded_deps = [d for d in dependencies if d not in cached_shards]
                if unloaded_deps:
                    dep_status = f"依赖未加载: {', '.join(unloaded_deps)}"
                else:
                    dep_status = "所有依赖已加载"
                print(f"  {i+1}. {shard_id} ({dep_status})")
            else:
                print(f"  {i+1}. {shard_id} (无依赖)")
        
        print("\n选择操作:")
        print("  a. 自动加载 (基于依赖顺序)")
        print("  q. 返回主菜单")
        print("  数字. 加载指定分片")
        
        choice = input("请输入选择: ").strip().lower()
        
        if choice == 'q':
            break
        elif choice == 'a':
            # 自动加载
            loading_sequence = shard_manager.get_loading_sequence(unloaded_shards)
            for shard_id in loading_sequence:
                logger.info(f"加载分片: {shard_id}")
                shard_manager.load_shard(shard_id, recursive=True)
        else:
            try:
                index = int(choice) - 1
                if 0 <= index < len(unloaded_shards):
                    shard_id = unloaded_shards[index]
                    logger.info(f"加载分片: {shard_id}")
                    shard_manager.load_shard(shard_id, recursive=True)
                else:
                    logger.warning("无效的选择")
            except ValueError:
                logger.warning("无效的输入")


def change_unload_strategy(shard_manager, current_strategy=None):
    """更改卸载策略
    
    Args:
        shard_manager: 分片管理器
        current_strategy: 当前卸载策略
        
    Returns:
        ShardUnloadStrategy: 新的卸载策略
    """
    print("\n选择卸载策略:")
    print("  1. 无依赖优先 - 优先卸载不被其他加载分片依赖的分片")
    print("  2. LRU优先 - 优先卸载最近最少使用的分片")
    print("  3. 内存优先 - 优先卸载内存占用最大的分片")
    print("  4. 混合策略 - 综合考虑依赖、使用时间和内存占用")
    
    strategy_map = {
        "1": "no_dependencies",
        "2": "lru",
        "3": "memory",
        "4": "hybrid"
    }
    
    choice = input("请选择策略 (1-4): ").strip()
    if choice not in strategy_map:
        logger.warning("无效的选择，使用默认的混合策略")
        choice = "4"
    
    strategy_name = strategy_map[choice]
    
    # 获取内存阈值
    threshold_input = input("请输入触发卸载的内存使用率阈值 (50-95): ").strip()
    try:
        threshold = float(threshold_input)
        if threshold < 50:
            threshold = 50
            logger.warning("阈值太低，已设置为最小值 50%")
        elif threshold > 95:
            threshold = 95
            logger.warning("阈值太高，已设置为最大值 95%")
    except ValueError:
        threshold = 80
        logger.warning("无效的阈值，使用默认值 80%")
    
    # 获取最小缓存大小
    min_cache_input = input("请输入最小缓存大小 (至少保留的分片数): ").strip()
    try:
        min_cache = int(min_cache_input)
        if min_cache < 1:
            min_cache = 1
            logger.warning("最小缓存大小太小，已设置为最小值 1")
    except ValueError:
        min_cache = 2
        logger.warning("无效的最小缓存大小，使用默认值 2")
    
    # 创建新的卸载策略
    return create_unload_strategy(
        shard_manager=shard_manager,
        priority=strategy_name,
        memory_threshold=threshold,
        min_cache_size=min_cache
    )


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="模型分片内存管理工具")
    parser.add_argument("model_name", help="模型名称")
    parser.add_argument("--shard-dir", help="分片目录")
    parser.add_argument("--cache-dir", help="缓存目录")
    parser.add_argument("--max-shards", type=int, default=5, help="最大内存中分片数量")
    parser.add_argument("--monitor", action="store_true", help="启动内存监控")
    parser.add_argument("--strategy", choices=["no_dependencies", "lru", "memory", "hybrid"], 
                        default="hybrid", help="卸载策略")
    parser.add_argument("--threshold", type=float, default=80.0, help="内存使用率阈值")
    
    args = parser.parse_args()
    
    # 设置日志
    logger.remove()
    logger.add(
        lambda msg: print(msg, end=""), 
        level="INFO", 
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{function}</cyan>: <level>{message}</level>"
    )
    
    # 创建元数据管理器
    metadata_manager = MetadataManager()
    
    # 确定分片目录和缓存目录
    shard_dir = args.shard_dir or f"models/{args.model_name}/shards"
    cache_dir = args.cache_dir or f".cache/{args.model_name}"
    
    # 创建分片管理器
    shard_manager = ShardManager(
        model_name=args.model_name,
        max_shards_in_memory=args.max_shards,
        metadata_manager=metadata_manager,
        shard_dir=shard_dir,
        cache_dir=cache_dir
    )
    
    # 创建卸载策略
    unload_strategy = create_unload_strategy(
        shard_manager=shard_manager,
        priority=args.strategy,
        memory_threshold=args.threshold,
        min_cache_size=2
    )
    
    # 如果启用监控，在后台启动内存监控
    if args.monitor:
        import threading

# 内存使用警告阈值（百分比）
MEMORY_WARNING_THRESHOLD = 80

        monitor_thread = threading.Thread(
            target=monitor_memory,
            daemon=True  # 设为守护线程，主线程结束时自动结束
        )
        monitor_thread.start()
        logger.info("内存监控已启动")
    
    # 主菜单循环
    try:
        while True:
            print("\n===== 模型分片内存管理 =====")
            print(f"模型: {args.model_name}")
            print(f"策略: {args.strategy.upper()}")
            print(f"内存阈值: {args.threshold}%")
            print(f"最大分片数: {args.max_shards}")
            
            # 显示当前缓存状态
            cached_shards = shard_manager.shard_cache.get_cached_shards()
            print(f"当前加载的分片: {len(cached_shards)}/{args.max_shards}")
            
            # 显示内存使用
            memory = psutil.virtual_memory()
            print(f"系统内存: {memory.percent}% 已用")
            
            print("\n选择操作:")
            print("  1. 查看/卸载分片")
            print("  2. 加载分片")
            print("  3. 更改卸载策略")
            print("  4. 触发自动卸载")
            print("  5. 清空所有分片")
            print("  q. 退出")
            
            choice = input("请输入选择: ").strip().lower()
            
            if choice == 'q':
                break
            elif choice == '1':
                unload_shards_interactive(shard_manager, unload_strategy)
            elif choice == '2':
                load_shards_interactive(shard_manager, args.model_name, metadata_manager)
            elif choice == '3':
                unload_strategy = change_unload_strategy(shard_manager, unload_strategy)
                # 更新命令行参数，使得菜单显示正确的信息
                args.strategy = unload_strategy.priority.name.lower()
                args.threshold = unload_strategy.memory_threshold
            elif choice == '4':
                unloaded_count = unload_strategy.trigger_unload_if_needed()
                if unloaded_count > 0:
                    logger.info(f"已自动卸载 {unloaded_count} 个分片")
                else:
                    logger.info("没有分片需要卸载")
            elif choice == '5':
                if shard_manager.clear_cache():
                    logger.info("已清空所有分片")
                else:
                    logger.warning("清空分片失败")
            else:
                logger.warning("无效的选择")
                
    except KeyboardInterrupt:
        print("\n")
        logger.info("正在退出...")
    finally:
        # 清理资源
        shard_manager.clear_cache()
        logger.info("已清理资源")


if __name__ == "__main__":
    main() 