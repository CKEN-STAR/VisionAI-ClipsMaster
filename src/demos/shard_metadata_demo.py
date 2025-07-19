#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
分片元数据管理演示

演示如何在程序中使用分片元数据管理功能：
1. 创建和管理元数据
2. 从分片生成元数据
3. 验证分片完整性
4. 根据元数据加载模型
"""

import os
import sys
import time
import hashlib
import argparse
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.sharding.metadata_manager import ShardMetadata, MetadataManager
from src.sharding.model_splitter import ModelSplitter
from src.core.shard_policy_manager import ShardPolicyManager
from src.utils.memory_manager import MemoryManager
from loguru import logger


def demonstrate_metadata_creation():
    """演示元数据创建与更新"""
    print("\n=== 演示元数据创建与更新 ===")
    
    # 创建临时元数据目录
    metadata_dir = Path("temp_metadata")
    metadata_dir.mkdir(exist_ok=True)
    
    # 初始化元数据管理器
    manager = MetadataManager(metadata_dir=str(metadata_dir))
    
    # 创建模型元数据
    model_name = "demo_model"
    metadata = manager.create_metadata(model_name)
    
    # 添加分片元数据
    print("添加分片元数据...")
    
    # 分片1: 包含嵌入层和第一个注意力层
    metadata.add_shard(
        "shard_001",
        ["embedding", "attention_1"],
        hashlib.sha256(b"shard_1_data").hexdigest(),
        depends_on=[],
        shard_size=1024 * 1024 * 100  # 100MB
    )
    
    # 分片2: 包含前馈层和第二个注意力层
    metadata.add_shard(
        "shard_002",
        ["ffn_1", "attention_2"],
        hashlib.sha256(b"shard_2_data").hexdigest(),
        depends_on=["shard_001"],
        shard_size=1024 * 1024 * 150  # 150MB
    )
    
    # 分片3: 包含最后的层
    metadata.add_shard(
        "shard_003",
        ["ffn_2", "lm_head"],
        hashlib.sha256(b"shard_3_data").hexdigest(),
        depends_on=["shard_002"],
        shard_size=1024 * 1024 * 80  # 80MB
    )
    
    # 保存元数据
    manager.save_metadata(model_name)
    metadata_path = manager.get_metadata_path(model_name)
    print(f"元数据已保存到: {metadata_path}")
    
    # 显示分片信息
    shards = metadata.get_shards()
    print(f"\n模型分片数: {len(shards)}")
    
    for shard_id, shard_info in shards.items():
        size_mb = shard_info.get("size_bytes", 0) / (1024 * 1024)
        layers = ", ".join(shard_info.get("layers", []))
        depends = ", ".join(shard_info.get("depends_on", ["无"]))
        
        print(f"分片 {shard_id}:")
        print(f"  • 大小: {size_mb:.2f} MB")
        print(f"  • 层: {layers}")
        print(f"  • 依赖: {depends}")
    
    # 获取加载顺序
    try:
        loading_order = metadata.get_loading_order()
        print("\n推荐加载顺序:")
        for i, shard_id in enumerate(loading_order, 1):
            print(f"  {i}. {shard_id}")
    except ValueError as e:
        print(f"获取加载顺序失败: {e}")
    
    # 测试依赖验证
    missing_deps = metadata.verify_dependencies()
    if missing_deps:
        print("\n依赖关系验证失败:")
        for shard_id, missing in missing_deps.items():
            print(f"  • {shard_id} 缺少依赖: {', '.join(missing)}")
    else:
        print("\n依赖关系验证通过")
    
    # 测试更新分片
    print("\n更新分片 shard_002...")
    metadata.update_shard(
        "shard_002",
        layers=["ffn_1", "attention_2", "new_layer"],
        hash=hashlib.sha256(b"updated_shard_2").hexdigest()
    )
    
    # 重新保存
    manager.save_metadata(model_name)
    print("元数据已更新")
    
    # 再次加载验证
    reloaded_metadata = manager.get_metadata(model_name)
    updated_shard = reloaded_metadata.get_shard("shard_002")
    
    print(f"\n更新后的分片 shard_002:")
    print(f"  • 层: {', '.join(updated_shard['layers'])}")
    print(f"  • 哈希: {updated_shard['hash'][:8]}...")
    
    print("\n清理演示文件...")
    if os.path.exists(metadata_path):
        os.remove(metadata_path)
    
    if metadata_dir.exists():
        try:
            metadata_dir.rmdir()
        except OSError:
            pass
    
    print("演示完成")


def demonstrate_from_real_shards(shard_dir: str = None):
    """从实际分片目录生成元数据
    
    Args:
        shard_dir: 分片目录路径
    """
    print("\n=== 从实际分片生成元数据 ===")
    
    if not shard_dir:
        print("未提供分片目录，跳过此演示")
        return
    
    shard_dir = Path(shard_dir)
    if not shard_dir.exists():
        print(f"分片目录不存在: {shard_dir}")
        return
    
    print(f"使用分片目录: {shard_dir}")
    
    # 创建临时元数据目录
    metadata_dir = Path("temp_metadata_real")
    metadata_dir.mkdir(exist_ok=True)
    
    # 初始化元数据管理器
    manager = MetadataManager(metadata_dir=str(metadata_dir))
    
    # 获取模型名称
    model_name = shard_dir.name.replace("_shards", "")
    
    # 查找分片信息文件
    shard_info_file = shard_dir / "shard_info.json"
    if not shard_info_file.exists():
        print(f"分片信息文件不存在: {shard_info_file}")
        shard_info_file = None
    
    # 从分片目录生成元数据
    print(f"从分片目录生成元数据: {model_name}")
    metadata = manager.generate_metadata_from_shards(
        model_name,
        str(shard_dir),
        str(shard_info_file) if shard_info_file else None
    )
    
    if not metadata:
        print("生成元数据失败")
        return
    
    # 显示分片信息
    shards = metadata.get_shards()
    print(f"成功生成元数据，包含 {len(shards)} 个分片")
    
    # 检查是否有层信息
    has_layers = False
    for shard_info in shards.values():
        if shard_info.get("layers"):
            has_layers = True
            break
    
    if not has_layers:
        print("注意: 生成的元数据中没有层信息，这可能是因为分片信息文件不包含层映射")
    
    # 获取加载顺序
    try:
        loading_order = metadata.get_loading_order()
        print("\n推荐加载顺序:")
        for i, shard_id in enumerate(loading_order, 1):
            print(f"  {i}. {shard_id}")
    except ValueError as e:
        print(f"获取加载顺序失败: {e}")
    
    # 验证分片文件
    print("\n验证分片文件...")
    results = metadata.verify_all_shards()
    
    # 统计结果
    success_count = sum(1 for result in results.values() if result[0])
    fail_count = len(results) - success_count
    
    print(f"分片验证结果: {success_count} 个通过, {fail_count} 个失败")
    
    if fail_count > 0:
        print("\n验证失败的分片:")
        for shard_id, (success, message) in results.items():
            if not success:
                print(f"  • {shard_id}: {message}")
    
    # 清理
    metadata_path = manager.get_metadata_path(model_name)
    
    print("\n清理演示文件...")
    if os.path.exists(metadata_path):
        os.remove(metadata_path)
    
    if metadata_dir.exists():
        try:
            metadata_dir.rmdir()
        except OSError:
            pass
    
    print("演示完成")


def demonstrate_metadata_integration():
    """演示元数据与模型分片切割器的集成"""
    print("\n=== 演示元数据与模型分片集成 ===")
    
    # 创建临时目录
    metadata_dir = Path("temp_metadata_integration")
    metadata_dir.mkdir(exist_ok=True)
    
    # 初始化元数据管理器和模型分片切割器
    metadata_manager = MetadataManager(metadata_dir=str(metadata_dir))
    model_splitter = ModelSplitter()
    
    # 创建简单的模型分片模拟
    print("模拟模型分片过程...")
    
    # 模拟分片结果
    model_name = "integrated_model"
    mock_shard_results = {
        "model_name": model_name,
        "num_shards": 3,
        "strategy": "balanced",
        "strategy_type": "layerwise",
        "shard_paths": [
            f"models/{model_name}_shards/model_part_000.bin",
            f"models/{model_name}_shards/model_part_001.bin",
            f"models/{model_name}_shards/model_part_002.bin"
        ],
        "checksums": [
            hashlib.sha256(f"shard_data_0".encode()).hexdigest(),
            hashlib.sha256(f"shard_data_1".encode()).hexdigest(),
            hashlib.sha256(f"shard_data_2".encode()).hexdigest(),
        ],
        "layer_mapping": {
            "shard_0": ["embedding", "attention_1"],
            "shard_1": ["ffn_1", "attention_2"],
            "shard_2": ["ffn_2", "output"]
        }
    }
    
    # 基于分片结果创建元数据
    print("创建元数据...")
    metadata = metadata_manager.create_metadata(model_name)
    
    # 添加分片元数据
    for i in range(mock_shard_results["num_shards"]):
        shard_id = f"shard_{i:03d}"
        shard_path = mock_shard_results["shard_paths"][i]
        hash_value = mock_shard_results["checksums"][i]
        
        # 获取层信息
        layers = mock_shard_results["layer_mapping"][f"shard_{i}"]
        
        # 确定依赖关系
        depends_on = []
        if i > 0:
            depends_on = [f"shard_{i-1:03d}"]
        
        # 添加分片元数据
        metadata.add_shard(
            shard_id,
            layers,
            hash_value,
            depends_on=depends_on,
            shard_path=shard_path,
            shard_size=1024 * 1024 * (100 + i * 20)  # 模拟不同大小
        )
    
    # 保存元数据
    metadata_manager.save_metadata(model_name)
    metadata_path = metadata_manager.get_metadata_path(model_name)
    print(f"元数据已保存到: {metadata_path}")
    
    # 模拟加载过程
    print("\n模拟加载过程...")
    
    # 获取加载顺序
    loading_order = metadata.get_loading_order()
    print(f"加载顺序: {', '.join(loading_order)}")
    
    # 加载每个分片
    for shard_id in loading_order:
        shard_info = metadata.get_shard(shard_id)
        print(f"加载分片 {shard_id}: {', '.join(shard_info['layers'])}")
        
        # 模拟加载过程
        time.sleep(0.5)  # 假装在加载
    
    print("所有分片加载完成")
    
    # 演示分片元数据API
    print("\n检查特定层所在的分片...")
    layer_to_shard = metadata.get_layer_to_shard_mapping()
    test_layers = ["embedding", "attention_2", "output"]
    
    for layer in test_layers:
        shard_id = layer_to_shard.get(layer, "未知")
        print(f"层 '{layer}' 位于分片: {shard_id}")
    
    # 清理
    print("\n清理演示文件...")
    if os.path.exists(metadata_path):
        os.remove(metadata_path)
    
    if metadata_dir.exists():
        try:
            metadata_dir.rmdir()
        except OSError:
            pass
    
    print("演示完成")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="分片元数据管理演示")
    parser.add_argument("--shard-dir", help="实际分片目录路径")
    args = parser.parse_args()
    
    # 演示元数据创建与更新
    demonstrate_metadata_creation()
    
    # 演示从实际分片生成元数据
    demonstrate_from_real_shards(args.shard_dir)
    
    # 演示元数据与模型分片切割器的集成
    demonstrate_metadata_integration()
    
    print("\n所有演示完成")


if __name__ == "__main__":
    main() 