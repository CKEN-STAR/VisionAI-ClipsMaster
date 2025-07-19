#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
分片缓存管理器演示

此示例展示如何使用ShardCache和ShardManager实现高效的模型分片缓存管理，
包括LRU策略，内存管理，以及依赖关系处理。
"""

import os
import sys
import time
import logging
import argparse
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
    from src.sharding.cache_manager import ShardCache, ShardManager
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
    test_dir = ".test_cache"
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
    
    print("测试环境创建完成")
    
    return {
        "test_dir": test_dir,
        "models_dir": models_dir,
        "metadata_dir": metadata_dir,
        "cache_dir": cache_dir,
        "metadata_manager": metadata_manager,
        "shard_manager": shard_manager
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

def demo_shard_cache_basic(env):
    """演示ShardCache基本功能
    
    Args:
        env: 测试环境
    """
    print_separator("ShardCache基本功能演示")
    
    # 创建一个简单的分片缓存
    cache = ShardCache(max_size=3)
    
    # 自定义加载/卸载回调函数
    def load_callback(shard_id):
        print(f"加载分片: {shard_id}")
        return f"分片{shard_id}的数据"
    
    def unload_callback(shard_id):
        print(f"卸载分片: {shard_id}")
        return True
    
    # 设置回调函数
    cache.load_callback = load_callback
    cache.unload_callback = unload_callback
    
    # 1. 加载分片
    print("\n1. 加载分片")
    for i in range(1, 4):
        shard_id = f"shard_{i}"
        data = cache.get(shard_id)
        print(f"获取到分片 {shard_id}: {data}")
    
    # 显示缓存状态
    print(f"\n当前缓存状态: {cache.get_cached_shards()}")
    print(f"缓存统计: {cache.get_stats()}")
    
    # 2. 演示LRU淘汰
    print("\n2. LRU淘汰演示")
    print("加载新分片会淘汰最久未使用的分片")
    
    # 加载新分片，触发LRU淘汰
    shard_id = "shard_4"
    data = cache.get(shard_id)
    print(f"获取到分片 {shard_id}: {data}")
    
    # 显示缓存状态
    print(f"\n当前缓存状态: {cache.get_cached_shards()}")
    
    # 3. 演示缓存命中
    print("\n3. 缓存命中演示")
    
    # 再次访问已缓存的分片
    for shard_id in ["shard_2", "shard_3", "shard_4"]:
        data = cache.get(shard_id)
        print(f"获取到分片 {shard_id}: {data}")
    
    # 显示缓存状态和统计
    print(f"\n当前缓存状态: {cache.get_cached_shards()}")
    print(f"缓存统计: {cache.get_stats()}")
    
    # 4. 手动移除分片
    print("\n4. 手动移除分片")
    success = cache.remove("shard_3")
    print(f"移除分片 shard_3: {'成功' if success else '失败'}")
    
    # 显示缓存状态
    print(f"\n当前缓存状态: {cache.get_cached_shards()}")
    
    # 5. 调整缓存大小
    print("\n5. 调整缓存大小")
    cache.resize(2)
    print(f"缓存大小调整为2")
    
    # 显示缓存状态
    print(f"\n当前缓存状态: {cache.get_cached_shards()}")
    
    # 6. 清空缓存
    print("\n6. 清空缓存")
    cache.clear()
    
    # 显示缓存状态
    print(f"\n当前缓存状态: {cache.get_cached_shards()}")
    print(f"缓存统计: {cache.get_stats()}")

def demo_shard_manager(env):
    """演示ShardManager功能
    
    Args:
        env: 测试环境
    """
    print_separator("ShardManager功能演示")
    
    shard_manager = env["shard_manager"]
    
    # 1. 获取加载顺序
    print("\n1. 获取分片加载顺序")
    loading_sequence = shard_manager.get_loading_sequence()
    print(f"分片加载顺序: {loading_sequence}")
    
    # 2. 加载单个分片及其依赖
    print("\n2. 加载单个分片及其依赖")
    data = shard_manager.load_shard("shard_3", recursive=True)
    print(f"加载分片shard_3及其依赖，当前缓存: {shard_manager.shard_cache.get_cached_shards()}")
    
    # 3. 预加载分片
    print("\n3. 预加载分片")
    shard_manager.shard_cache.clear()  # 先清空缓存
    count = shard_manager.prefetch_shards(["shard_5"])
    print(f"预加载shard_5，加载了{count}个分片")
    print(f"当前缓存: {shard_manager.shard_cache.get_cached_shards()}")
    
    # 4. 获取层映射
    print("\n4. 获取层映射")
    layer_mapping = shard_manager.get_layer_mapping()
    print("层到分片的映射:")
    for layer, shard_id in layer_mapping.items():
        print(f"  {layer} -> {shard_id}")
    
    # 5. 加载指定层
    print("\n5. 加载指定层")
    shard_manager.shard_cache.clear()  # 先清空缓存
    result = shard_manager.load_layers(["attention_1", "attention_2"])
    print(f"加载attention_1和attention_2层")
    print(f"当前缓存: {shard_manager.shard_cache.get_cached_shards()}")
    
    # 6. 缓存统计
    print("\n6. 缓存统计")
    print(f"缓存统计: {shard_manager.get_cache_stats()}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="分片缓存管理器演示")
    parser.add_argument("--cleanup", action="store_true", help="运行后清理测试环境")
    args = parser.parse_args()
    
    print_separator("分片缓存管理器演示")
    print("本示例展示如何使用ShardCache和ShardManager进行高效的模型分片管理")
    
    try:
        # 创建测试环境
        env = create_test_environment()
        
        # 运行演示
        demo_shard_cache_basic(env)
        demo_shard_manager(env)
        
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