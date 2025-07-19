#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
分片预加载系统演示

此示例展示如何使用ShardPreloader实现模型分片的智能预加载，
包括使用不同的预加载策略和基于系统资源状态的自适应加载。
"""

import os
import sys
import time
import logging
import argparse
import threading
from pathlib import Path
from typing import Dict, Any, List

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 配置日志
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 导入所需模块
try:
    from src.sharding.preloader import ShardPreloader, PreloadStrategy, PreloaderState
    from src.sharding.cache_manager import ShardManager, ShardCache
    from src.sharding.metadata_manager import MetadataManager, ShardMetadata
except ImportError as e:
    logger.error(f"导入模块失败: {str(e)}")
    sys.exit(1)

def print_separator(title=""):
    """打印分隔线"""
    width = 80
    print("\n" + "=" * width)
    if title:
        print(f"{title.center(width)}")
        print("-" * width)

def create_test_environment():
    """创建测试环境
    
    Returns:
        Dict: 包含测试环境中的组件
    """
    print_separator("创建测试环境")
    
    # 创建临时目录
    test_dir = ".test_preloader"
    os.makedirs(test_dir, exist_ok=True)
    
    # 创建模型目录结构
    models_dir = os.path.join(test_dir, "models")
    metadata_dir = os.path.join(test_dir, "metadata")
    cache_dir = os.path.join(test_dir, "cache")
    
    # 创建目录
    for d in [models_dir, metadata_dir, cache_dir]:
        os.makedirs(d, exist_ok=True)
    
    # 创建测试模型目录
    test_model_dir = os.path.join(models_dir, "test_model")
    os.makedirs(test_model_dir, exist_ok=True)
    
    # 创建测试元数据
    metadata_manager = MetadataManager(metadata_dir=metadata_dir)
    test_metadata = create_test_metadata(metadata_manager)
    
    # 创建测试分片文件
    create_test_shard_files(test_model_dir, test_metadata)
    
    # 创建分片管理器
    shard_manager = ShardManager(
        model_name="test_model",
        max_shards_in_memory=3,  # 设置较小的值以演示LRU功能
        metadata_manager=metadata_manager,
        shard_dir=test_model_dir,
        cache_dir=cache_dir
    )
    
    # 创建预加载器
    preloader = ShardPreloader(
        shard_manager=shard_manager,
        strategy=PreloadStrategy.HYBRID,
        max_cpu_usage=80.0,  # 设置较高的值以便在演示中容易触发预加载
        max_memory_usage=80.0,
        max_preload_shards=2,
        check_interval=1.0,
        history_file=os.path.join(test_dir, "preload_history.json")
    )
    
    print("测试环境创建完成")
    
    return {
        "test_dir": test_dir,
        "models_dir": models_dir,
        "metadata_dir": metadata_dir,
        "cache_dir": cache_dir,
        "metadata_manager": metadata_manager,
        "shard_manager": shard_manager,
        "preloader": preloader
    }

def create_test_metadata(metadata_manager):
    """创建测试元数据
    
    Args:
        metadata_manager: 元数据管理器
    """
    # 为test_model创建测试元数据
    test_metadata = metadata_manager.create_metadata("test_model")
    
    # 添加分片元数据
    test_metadata.add_shard(
        shard_id="shard_1",
        layers=["embedding", "positional_encoding"],
        shard_path="shard_1.bin",
        shard_size=1024*1024  # 1MB
    )
    
    test_metadata.add_shard(
        shard_id="shard_2",
        layers=["attention_1", "ffn_1"],
        depends_on=["shard_1"],
        shard_path="shard_2.bin",
        shard_size=1024*1024  # 1MB
    )
    
    test_metadata.add_shard(
        shard_id="shard_3",
        layers=["attention_2", "ffn_2"],
        depends_on=["shard_2"],
        shard_path="shard_3.bin",
        shard_size=1024*1024  # 1MB
    )
    
    test_metadata.add_shard(
        shard_id="shard_4",
        layers=["attention_3", "ffn_3"],
        depends_on=["shard_3"],
        shard_path="shard_4.bin",
        shard_size=1024*1024  # 1MB
    )
    
    test_metadata.add_shard(
        shard_id="shard_5",
        layers=["output_layer"],
        depends_on=["shard_4"],
        shard_path="shard_5.bin",
        shard_size=512*1024  # 512KB
    )
    
    # 添加一些并行分支的分片，用于测试复杂依赖
    test_metadata.add_shard(
        shard_id="shard_6",
        layers=["parallel_branch_1"],
        depends_on=["shard_2"],
        shard_path="shard_6.bin",
        shard_size=768*1024  # 768KB
    )
    
    test_metadata.add_shard(
        shard_id="shard_7",
        layers=["parallel_branch_2"],
        depends_on=["shard_6"],
        shard_path="shard_7.bin",
        shard_size=768*1024  # 768KB
    )
    
    # 保存元数据
    metadata_manager.save_metadata("test_model")
    
    logger.info("测试元数据创建完成")
    
    return test_metadata

def create_test_shard_files(model_dir, test_metadata):
    """创建测试分片文件
    
    Args:
        model_dir: 模型目录
        test_metadata: 测试元数据
    """
    # 为每个分片创建简单的二进制文件
    for shard_id, shard in test_metadata.get_shards().items():
        file_path = os.path.join(model_dir, shard["path"])
        
        # 创建包含魔数的文件
        with open(file_path, "wb") as f:
            # 写入魔数 (GGUF)
            f.write(b'GGUF')
            
            # 写入版本号 (1.0)
            f.write((1.0).to_bytes(8, byteorder='little'))
            
            # 写入分片ID
            f.write(shard_id.encode('utf-8').ljust(16, b'\0'))
            
            # 写入一些填充数据
            f.write(bytes([i % 256 for i in range(shard["size_bytes"] - 28)]))
    
    logger.info("测试分片文件创建完成")

def cleanup_test_environment(test_dir):
    """清理测试环境
    
    Args:
        test_dir: 测试目录
    """
    print_separator("清理测试环境")
    
    # 检查目录是否存在
    if os.path.exists(test_dir):
        import shutil
        try:
            shutil.rmtree(test_dir)
            print(f"已删除测试目录: {test_dir}")
        except Exception as e:
            logger.error(f"删除测试目录失败: {str(e)}")
    
    print("测试环境清理完成")

def simulate_access_pattern(preloader, pattern=None, delay=0.5):
    """模拟分片访问模式
    
    Args:
        preloader: 预加载器
        pattern: 访问模式列表，如果为None则使用默认模式
        delay: 访问间隔时间（秒）
    """
    if pattern is None:
        # 默认访问模式: 1->2->3->4->5, 然后1->2->6->7
        pattern = [
            "shard_1", "shard_2", "shard_3", "shard_4", "shard_5",
            "shard_1", "shard_2", "shard_6", "shard_7"
        ]
    
    # 模拟分片访问
    for shard_id in pattern:
        print(f"访问分片: {shard_id}")
        preloader.record_access(shard_id)
        time.sleep(delay)

def demo_sequential_preload(env):
    """演示顺序预加载策略
    
    Args:
        env: 测试环境
    """
    print_separator("顺序预加载策略演示")
    
    # 获取组件
    shard_manager = env["shard_manager"]
    preloader = env["preloader"]
    
    # 设置为顺序预加载策略
    preloader.strategy = PreloadStrategy.SEQUENTIAL
    
    # 启动预加载线程
    preloader.start()
    print("预加载器已启动，状态:", preloader.state.value)
    
    # 模拟访问1->2->3的模式
    print("\n模拟顺序访问分片：1->2->3")
    simulate_access_pattern(preloader, ["shard_1", "shard_2", "shard_3"], delay=1.0)
    
    # 等待一些预加载发生
    time.sleep(3.0)
    
    # 查看预加载状态
    print("\n预加载状态:")
    stats = preloader.get_preload_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # 预测下一个分片
    print("\n基于当前访问模式预测下一个分片:")
    predicted = preloader.predict_next_shard("shard_3")
    print(f"从分片'shard_3'预测下一个分片: {predicted}")
    
    # 停止预加载器
    preloader.stop()
    print("\n预加载器已停止")
    
    # 清空缓存，为下一个演示准备
    shard_manager.clear_cache()

def demo_dependency_preload(env):
    """演示依赖关系预加载策略
    
    Args:
        env: 测试环境
    """
    print_separator("依赖关系预加载策略演示")
    
    # 获取组件
    shard_manager = env["shard_manager"]
    preloader = env["preloader"]
    
    # 设置为依赖关系预加载策略
    preloader.strategy = PreloadStrategy.DEPENDENCY
    
    # 启动预加载线程
    preloader.start()
    print("预加载器已启动，策略:", preloader.strategy.value)
    
    # 模拟访问shard_2，应该预测shard_3和shard_6（依赖于shard_2的分片）
    print("\n访问分片'shard_2':")
    preloader.record_access("shard_2")
    
    # 等待一些预加载发生
    time.sleep(3.0)
    
    # 查看预加载状态
    print("\n预加载状态:")
    stats = preloader.get_preload_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # 预测下一个分片
    print("\n基于依赖关系预测下一个分片:")
    predicted = preloader.predict_next_shard("shard_2")
    print(f"从分片'shard_2'预测依赖分片: {predicted}")
    
    # 停止预加载器
    preloader.stop()
    print("\n预加载器已停止")
    
    # 清空缓存，为下一个演示准备
    shard_manager.clear_cache()

def demo_hybrid_preload(env):
    """演示混合预加载策略
    
    Args:
        env: 测试环境
    """
    print_separator("混合预加载策略演示")
    
    # 获取组件
    shard_manager = env["shard_manager"]
    preloader = env["preloader"]
    
    # 设置为混合预加载策略
    preloader.strategy = PreloadStrategy.HYBRID
    
    # 启动预加载线程
    preloader.start()
    print("预加载器已启动，策略:", preloader.strategy.value)
    
    # 模拟复杂的访问模式
    print("\n模拟复杂访问模式：1->2->3->1->2->6")
    simulate_access_pattern(
        preloader, 
        ["shard_1", "shard_2", "shard_3", "shard_1", "shard_2", "shard_6"],
        delay=1.0
    )
    
    # 等待一些预加载发生
    time.sleep(3.0)
    
    # 查看预加载状态
    print("\n预加载状态:")
    stats = preloader.get_preload_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # 预测下一个分片
    print("\n基于混合策略预测下一个分片:")
    predicted = preloader.predict_next_shard("shard_6")
    print(f"从分片'shard_6'预测下一个分片: {predicted}")
    
    # 停止预加载器
    preloader.stop()
    print("\n预加载器已停止")

def demo_resource_aware_preload(env):
    """演示资源感知预加载
    
    Args:
        env: 测试环境
    """
    print_separator("资源感知预加载演示")
    
    # 获取组件
    preloader = env["preloader"]
    
    # 设置较低的资源阈值，以便演示资源感知
    preloader.max_cpu_usage = 10.0  # 非常低的CPU使用率阈值
    print(f"设置CPU使用率阈值为 {preloader.max_cpu_usage}%")
    
    # 启动预加载器
    preloader.start()
    
    # 模拟一些分片访问
    print("\n模拟分片访问...")
    preloader.record_access("shard_1")
    
    # 模拟高CPU使用率情况
    print("\n模拟高CPU使用率环境:")
    
    # 创建一个内存池，以模拟高内存使用率
    memory_pool = []
    
    # 创建消耗CPU的线程
    def cpu_intensive_task():
        """CPU密集型任务"""
        print("开始执行CPU密集型任务...")
        start_time = time.time()
        while time.time() - start_time < 5.0:  # 运行5秒
            # 执行一些计算密集型操作
            for i in range(10000000):
                _ = i * i
        print("CPU密集型任务完成")
    
    # 启动CPU密集型线程
    cpu_thread = threading.Thread(target=cpu_intensive_task)
    cpu_thread.start()
    
    # 等待一些时间
    time.sleep(1.0)
    
    # 检查预加载状态
    print("\n高负载时的预加载状态:")
    print(f"当前CPU使用率: {preloader.get_preload_stats()}")
    
    # 等待CPU密集型任务完成
    cpu_thread.join()
    
    # 检查预加载是否继续
    time.sleep(2.0)
    print("\n负载降低后的预加载状态:")
    print(f"预加载状态: {preloader.get_preload_stats()}")
    
    # 停止预加载器
    preloader.stop()
    print("\n预加载器已停止")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="分片预加载系统演示")
    parser.add_argument("--cleanup", action="store_true", help="运行后清理测试环境")
    args = parser.parse_args()
    
    print_separator("分片预加载系统演示")
    print("本示例展示如何使用ShardPreloader实现模型分片的智能预加载")
    
    try:
        # 创建测试环境
        env = create_test_environment()
        
        # 运行各种预加载策略演示
        demo_sequential_preload(env)
        demo_dependency_preload(env)
        demo_hybrid_preload(env)
        
        # 资源感知预加载演示
        demo_resource_aware_preload(env)
        
        # 清理测试环境
        if args.cleanup:
            cleanup_test_environment(env["test_dir"])
        else:
            print(f"\n测试环境保留在 {os.path.abspath(env['test_dir'])} 目录下")
            print("使用 --cleanup 参数运行可以自动清理测试环境")
        
    except Exception as e:
        logger.error(f"演示过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print_separator("演示完成")

if __name__ == "__main__":
    main() 