#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
分层压缩策略命令行工具

管理和应用分层压缩策略的命令行接口
"""

import os
import sys
import argparse
import logging
import yaml
import json
from typing import Dict, Any, Optional, List
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("LayeredCLI")

def load_policy(args):
    """加载分层压缩策略"""
    from src.compression.layered_policy import get_policy_manager
    
    config_path = args.config
    
    # 获取策略管理器
    manager = get_policy_manager(config_path)
    
    # 显示加载的策略
    policies = manager.get_all_policies()
    print(f"\n成功从 {config_path} 加载了 {len(policies)} 个压缩策略")
    
    # 如果提供了输出格式
    if args.format == "yaml":
        # 打印YAML格式
        print("\n策略内容:")
        print(yaml.dump({"compression_policy": policies}, default_flow_style=False, allow_unicode=True))
    elif args.format == "json":
        # 打印JSON格式
        print("\n策略内容:")
        print(json.dumps({"compression_policy": policies}, indent=2, ensure_ascii=False))
    else:
        # 打印摘要
        summary = manager.get_policy_summary()
        print("\n策略摘要:")
        for res_type, info in summary.items():
            print(f"{res_type}: 算法={info['algorithm']} (级别{info['level']}), "
                  f"自动压缩={info['auto_compress']}, 阈值={info['threshold']}")
    
    return 0

def update_policy(args):
    """更新分层压缩策略"""
    from src.compression.layered_policy import get_policy_manager
    
    # 获取策略管理器
    manager = get_policy_manager()
    
    # 获取当前策略
    policy = manager.get_policy(args.resource_type)
    
    # 更新策略
    changes = {}
    
    if args.algorithm:
        changes["algorithm"] = args.algorithm
    
    if args.level is not None:
        changes["level"] = args.level
    
    if args.chunk_size:
        changes["chunk_size"] = args.chunk_size
    
    if args.auto_compress is not None:
        changes["auto_compress"] = args.auto_compress
    
    if args.threshold is not None:
        changes["threshold_mb"] = args.threshold
    
    if args.priority:
        changes["priority"] = args.priority
    
    # 如果没有变更
    if not changes:
        print(f"没有提供任何变更参数，保持 {args.resource_type} 的策略不变")
        return 0
    
    # 更新策略
    updated_policy = policy.copy()
    updated_policy.update(changes)
    
    # 设置策略
    manager.set_policy(args.resource_type, updated_policy)
    
    # 保存到文件
    if args.save:
        config_path = args.save
        manager.save_config(config_path)
        print(f"已将更新后的策略保存到: {config_path}")
    
    # 显示更新后的策略
    print(f"\n已更新 {args.resource_type} 的压缩策略:")
    for key, value in updated_policy.items():
        print(f"  {key}: {value}")
    
    return 0

def list_policies(args):
    """列出所有压缩策略"""
    from src.compression.layered_policy import get_policy_manager
    
    # 获取策略管理器
    manager = get_policy_manager()
    
    # 获取所有策略
    policies = manager.get_all_policies()
    
    # 如果提供了详细参数
    if args.verbose:
        print("\n所有压缩策略详情:")
        for res_type, policy in policies.items():
            print(f"\n{res_type}:")
            for key, value in policy.items():
                print(f"  {key}: {value}")
    else:
        # 打印摘要
        summary = manager.get_policy_summary()
        print("\n压缩策略摘要:")
        for res_type, info in summary.items():
            print(f"{res_type}: 算法={info['algorithm']} (级别{info['level']}), "
                  f"自动压缩={info['auto_compress']}, 阈值={info['threshold']}")
    
    return 0

def apply_policy(args):
    """应用压缩策略到资源"""
    from src.compression.layered_policy import compress_with_policy
    from src.compression.integration import get_compression_stats
    
    # 应用策略压缩资源
    success = compress_with_policy(args.resource_id, args.resource_type)
    
    if success:
        print(f"成功对资源 {args.resource_id} 应用 {args.resource_type or 'default'} 压缩策略")
        
        # 获取压缩统计
        stats = get_compression_stats()
        resource_stats = None
        
        for res_id, res_info in getattr(stats, "compressed_resources", {}).items():
            if res_id == args.resource_id:
                resource_stats = res_info
                break
        
        if resource_stats:
            print(f"\n压缩结果:")
            print(f"原始大小: {resource_stats.get('original_mb', 0):.2f}MB")
            print(f"压缩后大小: {resource_stats.get('compressed_mb', 0):.2f}MB")
            print(f"压缩率: {resource_stats.get('ratio', 0):.2f}")
            print(f"使用算法: {resource_stats.get('algorithm', 'unknown')}")
    else:
        print(f"对资源 {args.resource_id} 应用压缩策略失败")
        return 1
    
    return 0

def create_policy(args):
    """创建新的压缩策略"""
    from src.compression.layered_policy import get_policy_manager
    
    # 获取策略管理器
    manager = get_policy_manager()
    
    # 检查资源类型是否已存在
    if args.resource_type in manager.get_available_policies() and not args.force:
        print(f"资源类型 {args.resource_type} 已存在策略，使用 --force 覆盖或使用 update-policy 命令更新")
        return 1
    
    # 创建新策略
    new_policy = {
        "algorithm": args.algorithm or "zstd",
        "level": args.level if args.level is not None else 3,
        "chunk_size": args.chunk_size or "4MB",
        "auto_compress": args.auto_compress if args.auto_compress is not None else True,
        "threshold_mb": args.threshold or 10,
        "priority": args.priority or "medium"
    }
    
    # 设置策略
    manager.set_policy(args.resource_type, new_policy)
    
    # 保存到文件
    if args.save:
        config_path = args.save
        manager.save_config(config_path)
        print(f"已将新策略保存到: {config_path}")
    
    # 显示新策略
    print(f"\n已创建 {args.resource_type} 的压缩策略:")
    for key, value in new_policy.items():
        print(f"  {key}: {value}")
    
    return 0

def verify_config(args):
    """验证压缩策略配置文件"""
    try:
        # 加载配置文件
        with open(args.config, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # 检查基本结构
        if not isinstance(config, dict):
            print(f"错误: 配置文件 {args.config} 根节点必须是字典")
            return 1
        
        if "compression_policy" not in config:
            print(f"错误: 配置文件 {args.config} 中找不到 compression_policy 节点")
            return 1
        
        policies = config["compression_policy"]
        if not isinstance(policies, dict):
            print(f"错误: compression_policy 必须是字典")
            return 1
        
        # 验证每个策略
        errors = []
        warnings = []
        
        for res_type, policy in policies.items():
            # 检查必要字段
            if "algorithm" not in policy:
                errors.append(f"{res_type}: 缺少必要字段 'algorithm'")
            
            # 检查算法是否可用
            from src.compression.compressors import get_available_compressors
            available_algs = get_available_compressors()
            if "algorithm" in policy and policy["algorithm"] not in available_algs:
                warnings.append(f"{res_type}: 算法 '{policy['algorithm']}' 可能不可用，"
                               f"可用算法: {available_algs}")
            
            # 检查数值字段
            if "level" in policy and not isinstance(policy["level"], (int, float)):
                errors.append(f"{res_type}: 'level' 必须是数字")
            
            if "threshold_mb" in policy and not isinstance(policy["threshold_mb"], (int, float)):
                errors.append(f"{res_type}: 'threshold_mb' 必须是数字")
            
            # 检查布尔字段
            if "auto_compress" in policy and not isinstance(policy["auto_compress"], bool):
                errors.append(f"{res_type}: 'auto_compress' 必须是布尔值")
            
            # 检查优先级
            if "priority" in policy and policy["priority"] not in ["high", "medium", "low"]:
                warnings.append(f"{res_type}: 'priority' 值 '{policy['priority']}' 不是标准值"
                               f"(high/medium/low)")
        
        # 打印验证结果
        if errors:
            print(f"\n发现 {len(errors)} 个错误:")
            for error in errors:
                print(f"- {error}")
        
        if warnings:
            print(f"\n发现 {len(warnings)} 个警告:")
            for warning in warnings:
                print(f"- {warning}")
        
        if not errors and not warnings:
            print(f"配置文件 {args.config} 验证通过")
            return 0
        elif not errors:
            print(f"配置文件 {args.config} 验证通过，但有警告")
            return 0
        else:
            return 1
        
    except Exception as e:
        print(f"验证配置文件时出错: {e}")
        return 1

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="分层压缩策略管理工具")
    subparsers = parser.add_subparsers(dest="command", help="命令")
    
    # 加载策略命令
    load_parser = subparsers.add_parser("load", help="加载压缩策略配置")
    load_parser.add_argument("config", help="配置文件路径")
    load_parser.add_argument("--format", choices=["summary", "yaml", "json"], default="summary",
                           help="输出格式")
    
    # 更新策略命令
    update_parser = subparsers.add_parser("update", help="更新压缩策略")
    update_parser.add_argument("resource_type", help="资源类型")
    update_parser.add_argument("--algorithm", help="压缩算法")
    update_parser.add_argument("--level", type=int, help="压缩级别")
    update_parser.add_argument("--chunk-size", help="分块大小")
    update_parser.add_argument("--auto-compress", type=bool, help="是否自动压缩")
    update_parser.add_argument("--threshold", type=float, help="压缩阈值(MB)")
    update_parser.add_argument("--priority", choices=["high", "medium", "low"], help="优先级")
    update_parser.add_argument("--save", help="保存到配置文件")
    
    # 列出策略命令
    list_parser = subparsers.add_parser("list", help="列出所有压缩策略")
    list_parser.add_argument("--verbose", "-v", action="store_true", help="显示详细信息")
    
    # 应用策略命令
    apply_parser = subparsers.add_parser("apply", help="应用压缩策略到资源")
    apply_parser.add_argument("resource_id", help="资源ID")
    apply_parser.add_argument("--resource-type", help="资源类型(可选)")
    
    # 创建策略命令
    create_parser = subparsers.add_parser("create", help="创建新的压缩策略")
    create_parser.add_argument("resource_type", help="资源类型")
    create_parser.add_argument("--algorithm", help="压缩算法")
    create_parser.add_argument("--level", type=int, help="压缩级别")
    create_parser.add_argument("--chunk-size", help="分块大小")
    create_parser.add_argument("--auto-compress", type=bool, help="是否自动压缩")
    create_parser.add_argument("--threshold", type=float, help="压缩阈值(MB)")
    create_parser.add_argument("--priority", choices=["high", "medium", "low"], help="优先级")
    create_parser.add_argument("--save", help="保存到配置文件")
    create_parser.add_argument("--force", action="store_true", help="强制覆盖已有策略")
    
    # 验证配置命令
    verify_parser = subparsers.add_parser("verify", help="验证压缩策略配置文件")
    verify_parser.add_argument("config", help="配置文件路径")
    
    # 解析参数
    args = parser.parse_args()
    
    # 根据命令执行对应的函数
    if args.command == "load":
        return load_policy(args)
    elif args.command == "update":
        return update_policy(args)
    elif args.command == "list":
        return list_policies(args)
    elif args.command == "apply":
        return apply_policy(args)
    elif args.command == "create":
        return create_policy(args)
    elif args.command == "verify":
        return verify_config(args)
    else:
        parser.print_help()
        return 0

if __name__ == "__main__":
    sys.exit(main()) 