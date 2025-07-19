#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
分片元数据管理工具

提供命令行界面用于分片元数据的管理：
1. 创建元数据
2. 从分片目录生成元数据
3. 添加/更新/删除分片元数据
4. 查看分片元数据
5. 验证分片完整性和依赖关系
"""

import os
import sys
import json
import time
import hashlib
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Any

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.sharding.metadata_manager import ShardMetadata, MetadataManager
from loguru import logger


def create_metadata(args):
    """创建元数据
    
    Args:
        args: 命令行参数
    """
    # 初始化元数据管理器
    manager = MetadataManager(metadata_dir=args.metadata_dir)
    
    # 创建元数据
    metadata = manager.create_metadata(args.model_name)
    
    # 如果有分片目录，尝试从中加载
    if args.shard_dir and os.path.exists(args.shard_dir):
        shard_info_file = None
        if args.shard_info_file and os.path.exists(args.shard_info_file):
            shard_info_file = args.shard_info_file
        else:
            # 尝试在分片目录中找到分片信息文件
            default_info_file = Path(args.shard_dir) / "shard_info.json"
            if default_info_file.exists():
                shard_info_file = str(default_info_file)
        
        # 从分片目录生成元数据
        metadata = manager.generate_metadata_from_shards(
            args.model_name,
            args.shard_dir,
            shard_info_file
        )
        
        if metadata:
            print(f"成功从分片目录生成元数据: {args.shard_dir}")
        else:
            print(f"从分片目录生成元数据失败")
            return 1
    else:
        # 保存空元数据
        manager.save_metadata(args.model_name)
        print(f"已创建空元数据: {args.model_name}")
    
    # 显示元数据文件路径
    metadata_path = manager.get_metadata_path(args.model_name)
    print(f"元数据文件路径: {metadata_path}")
    
    return 0


def add_shard(args):
    """添加分片元数据
    
    Args:
        args: 命令行参数
    """
    # 初始化元数据管理器
    manager = MetadataManager(metadata_dir=args.metadata_dir)
    
    # 获取模型元数据
    metadata = manager.get_metadata(args.model_name, create_if_not_exists=True)
    
    # 解析依赖分片
    depends_on = []
    if args.depends_on:
        depends_on = args.depends_on.split(',')
    
    # 解析层
    layers = []
    if args.layers:
        layers = args.layers.split(',')
    
    # 计算哈希值
    hash_value = args.hash
    if not hash_value and args.shard_path and os.path.exists(args.shard_path):
        with open(args.shard_path, 'rb') as f:
            hash_value = hashlib.sha256(f.read()).hexdigest()
    
    # 获取分片大小
    shard_size = None
    if args.shard_path and os.path.exists(args.shard_path):
        shard_size = os.path.getsize(args.shard_path)
    
    # 添加分片元数据
    metadata.add_shard(
        args.shard_id,
        layers,
        hash_value,
        depends_on=depends_on,
        shard_path=args.shard_path,
        shard_size=shard_size
    )
    
    # 保存元数据
    manager.save_metadata(args.model_name)
    
    print(f"已添加分片元数据: {args.shard_id}")
    if args.shard_path:
        print(f"分片路径: {args.shard_path}")
    if layers:
        print(f"包含层: {', '.join(layers)}")
    if depends_on:
        print(f"依赖分片: {', '.join(depends_on)}")
    
    return 0


def remove_shard(args):
    """移除分片元数据
    
    Args:
        args: 命令行参数
    """
    # 初始化元数据管理器
    manager = MetadataManager(metadata_dir=args.metadata_dir)
    
    # 获取模型元数据
    metadata = manager.get_metadata(args.model_name)
    if not metadata:
        print(f"模型 {args.model_name} 的元数据不存在")
        return 1
    
    # 移除分片元数据
    if metadata.remove_shard(args.shard_id):
        # 保存元数据
        manager.save_metadata(args.model_name)
        print(f"已移除分片元数据: {args.shard_id}")
        return 0
    else:
        print(f"移除分片元数据失败: {args.shard_id}")
        return 1


def show_metadata(args):
    """显示元数据
    
    Args:
        args: 命令行参数
    """
    # 初始化元数据管理器
    manager = MetadataManager(metadata_dir=args.metadata_dir)
    
    if args.list_models:
        # 列出所有模型
        models = manager.list_models()
        if models:
            print("模型列表:")
            for model in models:
                print(f"  • {model}")
        else:
            print("没有找到任何模型元数据")
        return 0
    
    # 获取模型元数据
    metadata = manager.get_metadata(args.model_name)
    if not metadata:
        print(f"模型 {args.model_name} 的元数据不存在")
        return 1
    
    # 显示元数据
    if args.shard_id:
        # 显示特定分片的元数据
        shard_info = metadata.get_shard(args.shard_id)
        if not shard_info:
            print(f"分片 {args.shard_id} 不存在")
            return 1
        
        print(f"\n分片 {args.shard_id} 的元数据:")
        
        # 格式化输出
        if "layers" in shard_info and shard_info["layers"]:
            print(f"  • 包含层: {', '.join(shard_info['layers'])}")
        else:
            print("  • 包含层: 无层信息")
        
        if "hash" in shard_info:
            print(f"  • 哈希值: {shard_info['hash']}")
        
        if "depends_on" in shard_info and shard_info["depends_on"]:
            print(f"  • 依赖分片: {', '.join(shard_info['depends_on'])}")
        else:
            print("  • 依赖分片: 无")
        
        if "path" in shard_info:
            print(f"  • 分片路径: {shard_info['path']}")
        
        if "size_bytes" in shard_info:
            size_mb = shard_info["size_bytes"] / (1024 * 1024)
            print(f"  • 分片大小: {size_mb:.2f} MB")
        
        if "created_at" in shard_info:
            created_at = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(shard_info["created_at"]))
            print(f"  • 创建时间: {created_at}")
        
        if "updated_at" in shard_info:
            updated_at = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(shard_info["updated_at"]))
            print(f"  • 更新时间: {updated_at}")
    else:
        # 显示模型元数据
        print(f"\n模型 {args.model_name} 的元数据:")
        
        # 基本信息
        print(f"  • 版本: {metadata.version}")
        
        creation_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(metadata.creation_time))
        print(f"  • 创建时间: {creation_time}")
        
        last_modified = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(metadata.last_modified))
        print(f"  • 最后修改: {last_modified}")
        
        # 分片信息
        shards = metadata.get_shards()
        print(f"\n分片数量: {len(shards)}")
        
        if args.verbose:
            for shard_id, shard_info in shards.items():
                print(f"\n分片 {shard_id}:")
                
                # 层信息
                if "layers" in shard_info and shard_info["layers"]:
                    if len(shard_info["layers"]) > 5:
                        layer_display = f"{', '.join(shard_info['layers'][:5])}, ... (共{len(shard_info['layers'])}个)"
                    else:
                        layer_display = ', '.join(shard_info["layers"])
                    print(f"  • 包含层: {layer_display}")
                else:
                    print("  • 包含层: 无层信息")
                
                # 依赖信息
                if "depends_on" in shard_info and shard_info["depends_on"]:
                    print(f"  • 依赖分片: {', '.join(shard_info['depends_on'])}")
                
                # 路径和大小
                if "path" in shard_info:
                    print(f"  • 分片路径: {shard_info['path']}")
                
                if "size_bytes" in shard_info:
                    size_mb = shard_info["size_bytes"] / (1024 * 1024)
                    print(f"  • 分片大小: {size_mb:.2f} MB")
        else:
            # 精简显示
            print("\n分片列表:")
            for shard_id in shards:
                # 简单获取一些关键信息
                shard_info = shards[shard_id]
                layer_count = len(shard_info.get("layers", []))
                
                size_str = ""
                if "size_bytes" in shard_info:
                    size_mb = shard_info["size_bytes"] / (1024 * 1024)
                    size_str = f", {size_mb:.2f} MB"
                
                depend_str = ""
                if shard_info.get("depends_on"):
                    depend_str = f", 依赖: {', '.join(shard_info['depends_on'])}"
                
                print(f"  • {shard_id}: {layer_count} 层{size_str}{depend_str}")
        
        # 加载顺序
        if args.show_order:
            try:
                loading_order = metadata.get_loading_order()
                print(f"\n推荐加载顺序:")
                for i, shard_id in enumerate(loading_order, 1):
                    print(f"  {i}. {shard_id}")
            except Exception as e:
                print(f"\n获取加载顺序失败: {e}")
    
    # 保存为JSON
    if args.save_json:
        try:
            with open(args.save_json, 'w', encoding='utf-8') as f:
                json.dump(metadata.to_dict(), f, indent=2, ensure_ascii=False)
            print(f"\n元数据已保存为JSON: {args.save_json}")
        except Exception as e:
            print(f"\n保存JSON失败: {e}")
    
    return 0


def verify_metadata(args):
    """验证元数据
    
    Args:
        args: 命令行参数
    """
    # 初始化元数据管理器
    manager = MetadataManager(metadata_dir=args.metadata_dir)
    
    # 获取模型元数据
    metadata = manager.get_metadata(args.model_name)
    if not metadata:
        print(f"模型 {args.model_name} 的元数据不存在")
        return 1
    
    # 验证依赖关系
    if args.dependencies:
        missing_deps = metadata.verify_dependencies()
        if missing_deps:
            print("\n依赖关系验证失败，以下分片缺少依赖:")
            for shard_id, missing in missing_deps.items():
                print(f"  • {shard_id} 缺少依赖: {', '.join(missing)}")
            return 1
        else:
            print("\n依赖关系验证通过")
    
    # 验证分片完整性
    if args.files:
        # 确定基础目录
        base_dir = args.base_dir
        if not base_dir:
            # 尝试从第一个分片的路径推断
            shards = metadata.get_shards()
            if shards:
                first_shard = next(iter(shards.values()))
                if "path" in first_shard:
                    base_dir = os.path.dirname(first_shard["path"])
        
        # 验证所有分片
        results = metadata.verify_all_shards(base_dir)
        
        # 统计结果
        success_count = sum(1 for result in results.values() if result[0])
        fail_count = len(results) - success_count
        
        print(f"\n分片完整性验证结果: {success_count} 个通过, {fail_count} 个失败")
        
        if fail_count > 0:
            print("\n验证失败的分片:")
            for shard_id, (success, message) in results.items():
                if not success:
                    print(f"  • {shard_id}: {message}")
            return 1
    
    # 尝试获取加载顺序
    if args.order:
        try:
            loading_order = metadata.get_loading_order()
            print("\n分片加载顺序:")
            for i, shard_id in enumerate(loading_order, 1):
                print(f"  {i}. {shard_id}")
        except ValueError as e:
            print(f"\n获取加载顺序失败: {e}")
            return 1
    
    return 0


def main():
    """主函数"""
    # 创建解析器
    parser = argparse.ArgumentParser(
        description="分片元数据管理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  创建元数据:
    python shard_metadata_tool.py create qwen2.5-7b-zh --shard-dir models/qwen2.5-7b-zh_shards
    
  添加分片元数据:
    python shard_metadata_tool.py add qwen2.5-7b-zh shard_001 --layers embedding,attention_1 --shard-path models/qwen2.5-7b-zh_shards/model_part_000.bin
    
  显示元数据:
    python shard_metadata_tool.py show qwen2.5-7b-zh --verbose
    
  验证元数据:
    python shard_metadata_tool.py verify qwen2.5-7b-zh --dependencies --files
    
  列出所有模型:
    python shard_metadata_tool.py show --list-models
"""
    )
    
    # 添加通用参数
    parser.add_argument("--metadata-dir", default="metadata", help="元数据存储目录")
    
    # 创建子命令
    subparsers = parser.add_subparsers(dest="command", help="子命令")
    
    # 创建元数据命令
    create_parser = subparsers.add_parser("create", help="创建元数据")
    create_parser.add_argument("model_name", help="模型名称")
    create_parser.add_argument("--shard-dir", help="分片目录，如果提供则从中生成元数据")
    create_parser.add_argument("--shard-info-file", help="分片信息文件路径")
    
    # 添加分片元数据命令
    add_parser = subparsers.add_parser("add", help="添加分片元数据")
    add_parser.add_argument("model_name", help="模型名称")
    add_parser.add_argument("shard_id", help="分片ID")
    add_parser.add_argument("--layers", help="分片包含的层列表，逗号分隔")
    add_parser.add_argument("--hash", help="分片哈希值")
    add_parser.add_argument("--depends-on", help="依赖的分片ID列表，逗号分隔")
    add_parser.add_argument("--shard-path", help="分片文件路径")
    
    # 移除分片元数据命令
    remove_parser = subparsers.add_parser("remove", help="移除分片元数据")
    remove_parser.add_argument("model_name", help="模型名称")
    remove_parser.add_argument("shard_id", help="分片ID")
    
    # 显示元数据命令
    show_parser = subparsers.add_parser("show", help="显示元数据")
    show_parser.add_argument("model_name", nargs="?", help="模型名称")
    show_parser.add_argument("--shard-id", help="查看特定分片")
    show_parser.add_argument("-v", "--verbose", action="store_true", help="显示详细信息")
    show_parser.add_argument("--show-order", action="store_true", help="显示加载顺序")
    show_parser.add_argument("--save-json", help="保存元数据为JSON文件")
    show_parser.add_argument("--list-models", action="store_true", help="列出所有模型")
    
    # 验证元数据命令
    verify_parser = subparsers.add_parser("verify", help="验证元数据")
    verify_parser.add_argument("model_name", help="模型名称")
    verify_parser.add_argument("--dependencies", action="store_true", help="验证依赖关系")
    verify_parser.add_argument("--files", action="store_true", help="验证分片文件")
    verify_parser.add_argument("--base-dir", help="分片文件基础目录")
    verify_parser.add_argument("--order", action="store_true", help="验证并显示加载顺序")
    
    # 解析参数
    args = parser.parse_args()
    
    # 执行相应的命令
    if args.command == "create":
        return create_metadata(args)
    elif args.command == "add":
        return add_shard(args)
    elif args.command == "remove":
        return remove_shard(args)
    elif args.command == "show":
        if args.list_models or args.model_name:
            return show_metadata(args)
        else:
            show_parser.print_help()
            return 1
    elif args.command == "verify":
        return verify_metadata(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main()) 