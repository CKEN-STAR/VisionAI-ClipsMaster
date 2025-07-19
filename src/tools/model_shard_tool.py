#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
模型分片工具

提供命令行界面用于模型分片操作：
1. 分片模型
2. 合并分片
3. 查看分片信息
4. 验证分片完整性
"""

import os
import sys
import time
import json
import argparse
from pathlib import Path
from typing import Optional

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.sharding.model_splitter import ModelSplitter
from src.core.shard_policy_manager import ShardPolicyManager
from loguru import logger


def split_model(args):
    """分片模型
    
    Args:
        args: 命令行参数
    """
    # 初始化分片切割器
    splitter = ModelSplitter(working_dir=args.output_dir)
    
    # 分片处理
    model_path = Path(args.model_path)
    if not model_path.exists():
        logger.error(f"模型文件不存在: {model_path}")
        return 1
    
    try:
        # 准备元数据
        metadata = {}
        if args.metadata:
            try:
                metadata = json.loads(args.metadata)
            except:
                logger.warning(f"无法解析元数据，将使用空元数据。输入: {args.metadata}")
        
        logger.info(f"开始对模型 {model_path} 进行分片...")
        start_time = time.time()
        
        # 执行分片
        result = splitter.split_model(
            model_path=model_path,
            model_name=args.model_name,
            strategy=args.strategy,
            output_dir=args.output_dir,
            metadata=metadata
        )
        
        elapsed = time.time() - start_time
        logger.info(f"分片完成，耗时 {elapsed:.2f} 秒")
        
        # 输出分片信息
        num_shards = result["num_shards"]
        model_size_mb = result["model_size_mb"] if "model_size_mb" in result else result.get("model_size_bytes", 0) / (1024 * 1024)
        
        print("\n分片结果信息:")
        print(f"  • 模型名称: {result['model_name']}")
        print(f"  • 模型大小: {model_size_mb:.2f} MB")
        print(f"  • 分片策略: {result['strategy']}")
        print(f"  • 分片类型: {result['strategy_type']}")
        print(f"  • 分片数量: {num_shards}")
        
        if "shard_size_mb" in result:
            print(f"  • 每片大小: {result['shard_size_mb']:.2f} MB")
        
        # 如果是按层分片，显示层信息
        if result["strategy_type"] == "layerwise" and "total_layers" in result:
            print(f"  • 模型总层数: {result['total_layers']}")
            print(f"  • 层映射文件: {result['layer_mapping_file']}")
        
        print(f"\n分片文件存储在: {Path(result['shard_paths'][0]).parent}")
        
        # 保存完整结果
        if args.save_info:
            info_path = Path(args.output_dir) / f"{result['model_name']}_split_info.json"
            with open(info_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"详细分片信息已保存到: {info_path}")
        
        return 0
        
    except Exception as e:
        logger.error(f"分片模型出错: {e}")
        return 1


def merge_shards(args):
    """合并分片
    
    Args:
        args: 命令行参数
    """
    # 初始化分片切割器
    splitter = ModelSplitter()
    
    # 合并处理
    shard_dir = Path(args.shard_dir)
    if not shard_dir.exists():
        logger.error(f"分片目录不存在: {shard_dir}")
        return 1
    
    try:
        # 输出路径处理
        output_path = args.output_path
        if not output_path:
            # 默认使用与分片目录同级的模型文件
            model_name = shard_dir.name.replace("_shards", "")
            output_path = shard_dir.parent / f"{model_name}.model"
        else:
            output_path = Path(output_path)
        
        logger.info(f"开始合并分片: {shard_dir} -> {output_path}")
        start_time = time.time()
        
        # 执行合并
        result_path = splitter.merge_shards(
            shard_dir=shard_dir,
            output_path=output_path,
            verify=not args.no_verify
        )
        
        elapsed = time.time() - start_time
        logger.info(f"合并完成，耗时 {elapsed:.2f} 秒")
        
        # 输出结果信息
        output_path = Path(result_path)
        model_size_mb = output_path.stat().st_size / (1024 * 1024)
        
        print("\n合并结果信息:")
        print(f"  • 输出文件: {output_path}")
        print(f"  • 模型大小: {model_size_mb:.2f} MB")
        
        return 0
        
    except Exception as e:
        logger.error(f"合并分片出错: {e}")
        return 1


def show_info(args):
    """显示分片信息
    
    Args:
        args: 命令行参数
    """
    # 初始化分片切割器
    splitter = ModelSplitter()
    
    # 路径处理
    path = Path(args.path)
    if not path.exists():
        logger.error(f"路径不存在: {path}")
        return 1
    
    try:
        # 获取分片信息
        info = splitter.get_shard_info(path)
        
        # 显示信息
        if info["status"] == "sharded":
            # 显示分片信息
            print("\n模型分片信息:")
            
            if "model_name" in info:
                print(f"  • 模型名称: {info['model_name']}")
            
            print(f"  • 分片目录: {info['shard_dir']}")
            
            if "num_shards" in info:
                print(f"  • 分片数量: {info['num_shards']}")
            
            if "strategy" in info:
                print(f"  • 分片策略: {info['strategy']}")
            
            if "strategy_type" in info:
                print(f"  • 分片类型: {info['strategy_type']}")
            
            if "model_size_mb" in info:
                print(f"  • 模型大小: {info['model_size_mb']:.2f} MB")
            elif "model_size_bytes" in info:
                model_size_mb = info["model_size_bytes"] / (1024 * 1024)
                print(f"  • 模型大小: {model_size_mb:.2f} MB")
            
            if "creation_time" in info:
                print(f"  • 创建时间: {info['creation_time']}")
            
            # 显示详细信息
            if args.verbose:
                if "shard_paths" in info:
                    print("\n分片文件:")
                    for i, path in enumerate(info["shard_paths"]):
                        print(f"  {i+1}. {Path(path).name}")
                
                if "layer_mapping_file" in info:
                    print(f"\n层映射文件: {info['layer_mapping_file']}")
                    
                    # 加载层映射
                    try:
                        with open(info['layer_mapping_file'], 'r', encoding='utf-8') as f:
                            layer_mapping = json.load(f)
                        
                        print(f"层分组信息: {len(layer_mapping)} 个分组")
                        for shard_id, shard_info in layer_mapping.items():
                            size_mb = shard_info.get("size_bytes", 0) / (1024 * 1024)
                            layer_count = len(shard_info.get("layers", []))
                            print(f"  • {shard_id}: {layer_count} 层, {size_mb:.2f} MB")
                    except:
                        print("无法加载层映射文件")
        
        elif info["status"] == "not_sharded_file":
            print(f"\n文件 {path} 尚未进行分片处理")
            
            # 显示文件信息
            file_size_mb = path.stat().st_size / (1024 * 1024)
            print(f"  • 文件大小: {file_size_mb:.2f} MB")
            
            # 提供分片建议
            policy_manager = ShardPolicyManager()
            shard_plan = policy_manager.generate_sharding_plan("generic_model", path.stat().st_size)
            
            print("\n分片建议:")
            print(f"  • 推荐策略: {shard_plan['strategy']}")
            print(f"  • 建议分片数: {shard_plan['num_shards']}")
            print(f"  • 每片大小: {shard_plan['shard_size_mb']:.2f} MB")
            
            # 分片命令
            script_path = Path(__file__).name
            cmd = f"python {script_path} split {path} --strategy {shard_plan['strategy']}"
            print(f"\n可执行以下命令进行分片:")
            print(f"  {cmd}")
            
        elif info["status"] == "not_sharded_dir":
            print(f"\n目录 {path} 不是一个模型分片目录")
            
        elif info["status"] == "invalid_path":
            print(f"\n无效的路径: {path}")
            
        return 0
        
    except Exception as e:
        logger.error(f"获取分片信息出错: {e}")
        return 1


def verify_shards(args):
    """验证分片完整性
    
    Args:
        args: 命令行参数
    """
    # 初始化分片切割器
    splitter = ModelSplitter()
    
    # 路径处理
    shard_dir = Path(args.shard_dir)
    if not shard_dir.exists():
        logger.error(f"分片目录不存在: {shard_dir}")
        return 1
    
    try:
        # 获取分片信息
        info = splitter.get_shard_info(shard_dir)
        
        if info["status"] != "sharded" and "status" not in info:
            logger.error(f"{shard_dir} 不是有效的分片目录")
            return 1
        
        # 获取分片路径
        shard_paths = info.get("shard_paths", [])
        if not shard_paths:
            # 尝试查找分片文件
            shard_paths = list(sorted(str(p) for p in shard_dir.glob("model_part_*.bin")))
            
            if not shard_paths:
                logger.error(f"未找到分片文件: {shard_dir}")
                return 1
        
        # 加载校验和文件
        checksum_file = shard_dir / "checksums.json"
        if not checksum_file.exists():
            logger.error(f"未找到校验和文件: {checksum_file}")
            return 1
        
        with open(checksum_file, 'r', encoding='utf-8') as f:
            checksum_info = json.load(f)
        
        original_checksums = checksum_info.get("checksums", [])
        if not original_checksums:
            logger.error("校验和文件中没有校验和信息")
            return 1
        
        # 验证每个分片
        if len(original_checksums) != len(shard_paths):
            logger.error(f"校验和数量 ({len(original_checksums)}) 与分片数量 ({len(shard_paths)}) 不匹配")
            return 1
        
        print(f"开始验证 {len(shard_paths)} 个分片文件...")
        start_time = time.time()
        
        import hashlib

# 内存使用警告阈值（百分比）
MEMORY_WARNING_THRESHOLD = 80

        
        for i, (shard_path, original_checksum) in enumerate(zip(shard_paths, original_checksums), 1):
            print(f"验证分片 {i}/{len(shard_paths)}: {Path(shard_path).name}")
            
            with open(shard_path, 'rb') as f:
                content = f.read()
                current_checksum = hashlib.sha256(content).hexdigest()
                
                if current_checksum != original_checksum:
                    logger.error(f"分片校验失败: {Path(shard_path).name}")
                    return 1
        
        elapsed = time.time() - start_time
        print(f"\n✅ 所有分片验证通过，耗时 {elapsed:.2f} 秒")
        
        return 0
        
    except Exception as e:
        logger.error(f"验证分片出错: {e}")
        return 1


def list_strategies(args):
    """列出可用的分片策略
    
    Args:
        args: 命令行参数
    """
    try:
        # 获取分片策略
        policy_manager = ShardPolicyManager()
        strategies = policy_manager.get_all_strategies()
        
        print("\n可用的分片策略:")
        for i, strategy in enumerate(strategies, 1):
            print(f"\n{i}. {strategy['name']}")
            print(f"   描述: {strategy['desc']}")
            print(f"   最大分片大小: {strategy['max_shard_size']} MB")
            print(f"   适用场景: {strategy['suitable_for']}")
            
            if args.verbose:
                print(f"   加载模式: {strategy['loading_mode']}")
                print(f"   层分组方式: {strategy['layer_grouping']}")
                print(f"   优先加载层: {', '.join(strategy['priority_layers'])}")
                print(f"   内存阈值: {strategy['memory_threshold']} MB")
                print(f"   磁盘IO优化: {strategy['disk_io_optimization']}")
                print(f"   对质量影响: {strategy['quality_impact']}")
        
        # 显示当前策略
        current = policy_manager.get_current_strategy()
        print(f"\n当前使用的策略: {current['name']} ({current['desc']})")
        
        return 0
        
    except Exception as e:
        logger.error(f"获取策略信息出错: {e}")
        return 1


def main():
    """主函数"""
    # 创建解析器
    parser = argparse.ArgumentParser(
        description="模型分片工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  分片模型:
    python model_shard_tool.py split models/qwen2.5-7b-zh.pt --strategy balanced
    
  合并分片:
    python model_shard_tool.py merge models/qwen2.5-7b-zh_shards
    
  查看分片信息:
    python model_shard_tool.py info models/qwen2.5-7b-zh_shards
    
  验证分片完整性:
    python model_shard_tool.py verify models/qwen2.5-7b-zh_shards
    
  列出可用策略:
    python model_shard_tool.py strategies
"""
    )
    subparsers = parser.add_subparsers(dest="command", help="子命令")
    
    # 分片命令
    split_parser = subparsers.add_parser("split", help="分片模型")
    split_parser.add_argument("model_path", help="模型文件路径")
    split_parser.add_argument("--model-name", help="模型名称（如果不指定，则从文件名提取）")
    split_parser.add_argument("--strategy", help="使用的分片策略")
    split_parser.add_argument("--output-dir", help="输出目录")
    split_parser.add_argument("--metadata", help="额外的元数据（JSON格式）")
    split_parser.add_argument("--save-info", action="store_true", help="保存详细的分片信息")
    
    # 合并命令
    merge_parser = subparsers.add_parser("merge", help="合并分片")
    merge_parser.add_argument("shard_dir", help="分片目录")
    merge_parser.add_argument("--output-path", help="输出文件路径")
    merge_parser.add_argument("--no-verify", action="store_true", help="跳过分片验证")
    
    # 信息查看命令
    info_parser = subparsers.add_parser("info", help="查看分片信息")
    info_parser.add_argument("path", help="模型文件或分片目录路径")
    info_parser.add_argument("-v", "--verbose", action="store_true", help="显示详细信息")
    
    # 验证命令
    verify_parser = subparsers.add_parser("verify", help="验证分片完整性")
    verify_parser.add_argument("shard_dir", help="分片目录")
    
    # 策略列表命令
    strategies_parser = subparsers.add_parser("strategies", help="列出可用的分片策略")
    strategies_parser.add_argument("-v", "--verbose", action="store_true", help="显示详细策略信息")
    
    # 解析参数
    args = parser.parse_args()
    
    # 执行相应的命令
    if args.command == "split":
        return split_model(args)
    elif args.command == "merge":
        return merge_shards(args)
    elif args.command == "info":
        return show_info(args)
    elif args.command == "verify":
        return verify_shards(args)
    elif args.command == "strategies":
        return list_strategies(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main()) 