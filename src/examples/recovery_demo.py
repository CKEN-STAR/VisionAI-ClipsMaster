#!/usr/bin/env python
"""分片容错恢复系统演示

此脚本演示如何使用分片容错恢复系统，包括不同的恢复策略，
处理各种失败场景，以及自动恢复过程。
"""

import os
import sys
import time
import argparse
import random
import shutil
from pathlib import Path
from loguru import logger

# 将项目根目录添加到路径
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.sharding.metadata_manager import MetadataManager, ShardMetadata
from src.sharding.cache_manager import ShardManager
from src.sharding.recovery import (
    ShardRecoveryManager, RecoveryStrategy, 
    handle_load_failure, create_recovery_manager
)


def create_test_metadata(model_name="recovery_test_model", shard_count=10):
    """创建测试用的模型元数据
    
    Args:
        model_name: 模型名称
        shard_count: 分片数量
        
    Returns:
        MetadataManager: 元数据管理器
    """
    metadata_manager = MetadataManager()
    
    # 创建模型元数据
    metadata = metadata_manager.create_metadata(model_name)
    
    # 创建分片元数据
    for i in range(shard_count):
        shard_id = f"shard_{i}"
        
        # 随机生成依赖关系（保证没有循环依赖）
        dependencies = [f"shard_{j}" for j in range(i) if random.random() < 0.3]
        
        # 随机分配层
        layers = [f"layer_{i}_{j}" for j in range(random.randint(1, 3))]
        
        # 随机大小（10MB~50MB）
        size_bytes = random.randint(10, 50) * 1024 * 1024
        
        # 设置哈希值（在实际测试中会被替换）
        hash_value = f"dummy_hash_{shard_id}"
        
        # 添加分片
        metadata.add_shard(
            shard_id=shard_id,
            layers=layers,
            hash=hash_value,
            depends_on=dependencies,
            shard_path=f"shards/{shard_id}.bin",
            shard_size=size_bytes
        )
    
    # 保存元数据
    metadata_manager.save_metadata(model_name)
    
    return metadata_manager


def create_test_shards(model_dir, metadata_manager, model_name):
    """创建测试用的分片文件
    
    Args:
        model_dir: 模型目录
        metadata_manager: 元数据管理器
        model_name: 模型名称
        
    Returns:
        Path: 分片目录路径
    """
    # 创建模型目录
    model_path = Path(model_dir) / model_name
    shard_dir = model_path / "shards"
    os.makedirs(shard_dir, exist_ok=True)
    
    # 获取模型元数据
    metadata = metadata_manager.get_metadata(model_name)
    if not metadata:
        logger.error(f"找不到模型 {model_name} 的元数据")
        return shard_dir
    
    all_shards = metadata.get_shards()
    
    # 创建分片文件
    for shard_id, shard_meta in all_shards.items():
        file_path = shard_dir / f"{shard_id}.bin"
        
        # 获取分片大小
        size_bytes = shard_meta.get("size_bytes", 1024 * 1024)
        
        # 创建测试分片文件
        with open(file_path, "wb") as f:
            # 写入标识头
            f.write(b"GGML")
            
            # 写入一些随机数据
            f.write(os.urandom(min(size_bytes - 4, 1024 * 1024)))
            
            # 如果文件太大，用空字节填充
            remaining = size_bytes - 4 - min(size_bytes - 4, 1024 * 1024)
            if remaining > 0:
                f.write(b"\0" * remaining)
        
        # 更新元数据中的路径
        shard_meta["path"] = f"shards/{shard_id}.bin"
        metadata.update_shard(shard_id, shard_path=f"shards/{shard_id}.bin")
    
    # 保存更新后的元数据
    metadata_manager.save_metadata(model_name)
    
    logger.info(f"已创建 {len(all_shards)} 个测试分片文件")
    return shard_dir


def simulate_failures(shard_dir, model_name, metadata_manager, failure_count=3, backup_first=True):
    """模拟分片失败
    
    随机破坏一些分片文件以模拟失败
    
    Args:
        shard_dir: 分片目录
        model_name: 模型名称
        metadata_manager: 元数据管理器
        failure_count: 失败数量
        backup_first: 是否先备份
        
    Returns:
        List[str]: 被破坏的分片ID列表
    """
    metadata = metadata_manager.get_metadata(model_name)
    if not metadata:
        logger.error(f"找不到模型 {model_name} 的元数据")
        return []
    
    all_shards = list(metadata.get_shards().keys())
    
    # 随机选择要破坏的分片
    failure_shards = random.sample(all_shards, min(failure_count, len(all_shards)))
    
    # 创建备份目录
    backup_dir = Path(shard_dir).parent / "backups"
    os.makedirs(backup_dir, exist_ok=True)
    
    for shard_id in failure_shards:
        shard_meta = metadata.get_shard(shard_id)
        if not shard_meta:
            continue
        
        # 获取分片路径
        rel_path = shard_meta.get("path", f"shards/{shard_id}.bin")
        shard_path = Path(shard_dir) / Path(rel_path).name
        
        if not shard_path.exists():
            logger.warning(f"分片文件不存在: {shard_path}")
            continue
        
        # 备份原始文件
        if backup_first:
            backup_path = backup_dir / f"{shard_id}_backup.bin"
            shutil.copy2(shard_path, backup_path)
            logger.info(f"已备份分片 {shard_id} 到 {backup_path}")
        
        # 随机选择故障类型
        failure_type = random.choice([
            "corrupt",      # 损坏文件内容
            "truncate",     # 截断文件
            "delete",       # 删除文件
            "hash_change"   # 修改元数据中的哈希值
        ])
        
        if failure_type == "corrupt":
            # 损坏文件内容
            with open(shard_path, "r+b") as f:
                # 移动到随机位置
                pos = random.randint(0, max(0, os.path.getsize(shard_path) - 100))
                f.seek(pos)
                # 写入随机数据
                f.write(os.urandom(min(100, os.path.getsize(shard_path) - pos)))
            logger.info(f"已损坏分片 {shard_id} 的内容")
            
        elif failure_type == "truncate":
            # 截断文件
            with open(shard_path, "r+b") as f:
                # 截断到原始大小的一半
                new_size = max(10, os.path.getsize(shard_path) // 2)
                f.truncate(new_size)
            logger.info(f"已截断分片 {shard_id} 到 {new_size} 字节")
            
        elif failure_type == "delete":
            # 删除文件
            os.remove(shard_path)
            logger.info(f"已删除分片 {shard_id}")
            
        elif failure_type == "hash_change":
            # 修改元数据中的哈希值
            metadata.update_shard(shard_id, hash=f"wrong_hash_{random.randint(1000, 9999)}")
            metadata_manager.save_metadata(model_name)
            logger.info(f"已修改分片 {shard_id} 的哈希值")
    
    return failure_shards


def test_recovery_strategies(model_name, shards_dir, metadata_manager, failure_shards):
    """测试各种恢复策略
    
    Args:
        model_name: 模型名称
        shards_dir: 分片目录
        metadata_manager: 元数据管理器
        failure_shards: 失败的分片ID列表
    """
    strategies = [
        RecoveryStrategy.CONSERVATIVE,
        RecoveryStrategy.AGGRESSIVE,
        RecoveryStrategy.MINIMAL,
        RecoveryStrategy.FAILFAST
    ]
    
    for strategy in strategies:
        logger.info(f"\n测试恢复策略: {strategy.value}")
        
        # 创建分片管理器
        shard_manager = ShardManager(
            model_name=model_name,
            metadata_manager=metadata_manager,
            shard_dir=str(shards_dir.parent),
            max_shards_in_memory=5
        )
        
        # 创建恢复管理器
        recovery_manager = create_recovery_manager(
            shard_manager=shard_manager,
            strategy=strategy,
            max_retry_count=2,
            backup_dir=str(shards_dir.parent / "backups"),
            enable_notifications=True
        )
        
        # 尝试加载失败的分片
        success_count = 0
        for shard_id in failure_shards:
            logger.info(f"尝试加载故障分片: {shard_id}")
            result = shard_manager.load_shard(shard_id)
            if result is not None:
                logger.info(f"成功加载分片 {shard_id}")
                success_count += 1
            else:
                logger.warning(f"无法加载分片 {shard_id}")
        
        # 获取恢复统计
        stats = recovery_manager.get_recovery_stats()
        
        # 打印结果
        logger.info(f"恢复结果 ({strategy.value}):")
        logger.info(f"  - 成功恢复: {success_count}/{len(failure_shards)}")
        logger.info(f"  - 总失败次数: {stats['total_failures']}")
        logger.info(f"  - 恢复操作: {stats['action_counts']}")
        
        # 清理资源
        shard_manager.clear_cache()


def test_simple_recovery(model_name, shards_dir, metadata_manager, failure_shards):
    """测试简单的恢复函数
    
    使用旧的兼容函数测试恢复功能
    
    Args:
        model_name: 模型名称
        shards_dir: 分片目录
        metadata_manager: 元数据管理器
        failure_shards: 失败的分片ID列表
    """
    logger.info("\n测试简单恢复函数")
    
    for shard_id in failure_shards:
        for retry in range(4):  # 最多重试3次
            logger.info(f"处理分片 {shard_id} 失败，重试 #{retry}")
            handle_load_failure(shard_id, retry)
            
            # 模拟加载结果
            if retry < 2:  # 前两次失败，第三次成功
                result = None
                logger.warning(f"分片 {shard_id} 加载仍然失败")
            else:
                result = {"id": shard_id}
                logger.info(f"分片 {shard_id} 加载成功")
                break


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="分片容错恢复系统演示")
    parser.add_argument("--model-name", default="recovery_test_model", help="模型名称")
    parser.add_argument("--model-dir", default="./models", help="模型目录")
    parser.add_argument("--shards", type=int, default=10, help="分片数量")
    parser.add_argument("--failures", type=int, default=3, help="模拟失败数量")
    
    args = parser.parse_args()
    
    # 设置日志格式
    logger.remove()
    logger.add(
        lambda msg: print(msg, end=""), 
        level="INFO",
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>"
    )
    
    # 创建模型目录
    model_dir = Path(args.model_dir)
    model_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建测试元数据
    logger.info(f"创建测试元数据: {args.model_name}, {args.shards}个分片")
    metadata_manager = create_test_metadata(args.model_name, args.shards)
    
    # 创建测试分片
    logger.info(f"创建测试分片文件")
    shard_dir = create_test_shards(model_dir, metadata_manager, args.model_name)
    
    # 模拟失败
    logger.info(f"模拟 {args.failures} 个分片失败")
    failure_shards = simulate_failures(
        shard_dir, 
        args.model_name, 
        metadata_manager, 
        args.failures
    )
    
    # 测试恢复策略
    test_recovery_strategies(args.model_name, shard_dir, metadata_manager, failure_shards)
    
    # 测试简单恢复
    test_simple_recovery(args.model_name, shard_dir, metadata_manager, failure_shards)
    
    logger.info("演示完成")


if __name__ == "__main__":
    main() 