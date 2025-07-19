#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
模型完整性验证工具

此工具用于验证模型分片的完整性，包括哈希校验、数字签名验证和依赖关系检查。
可作为命令行工具使用，提供多种验证级别选项。
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 配置日志
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    from src.sharding.integrity_checker import (
        IntegrityChecker, VerificationLevel, IntegrityError,
        CorruptedShardError, SignatureError, HeaderError,
        verify_model_cli
    )
    from src.sharding.metadata_manager import MetadataManager
except ImportError as e:
    logger.error(f"导入模块失败: {str(e)}")
    sys.exit(1)

def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(description="模型完整性验证工具")
    
    # 主要命令参数
    subparsers = parser.add_subparsers(dest="command", help="要执行的命令")
    
    # 验证命令
    verify_parser = subparsers.add_parser("verify", help="验证模型完整性")
    verify_parser.add_argument("model_name", help="要验证的模型名称")
    verify_parser.add_argument("--level", choices=["basic", "hash", "signature", "full"],
                             default="hash", help="验证级别")
    verify_parser.add_argument("--models-dir", default="models", help="模型目录")
    verify_parser.add_argument("--metadata-dir", default="metadata", help="元数据目录")
    verify_parser.add_argument("--verbose", "-v", action="store_true", help="显示详细信息")
    
    # 更新哈希命令
    hash_parser = subparsers.add_parser("update-hash", help="更新模型分片哈希值")
    hash_parser.add_argument("model_name", help="要处理的模型名称")
    hash_parser.add_argument("--models-dir", default="models", help="模型目录")
    hash_parser.add_argument("--metadata-dir", default="metadata", help="元数据目录")
    
    # 签名命令
    sign_parser = subparsers.add_parser("sign", help="为模型分片生成签名")
    sign_parser.add_argument("model_name", help="要签名的模型名称")
    sign_parser.add_argument("--key-file", required=True, help="包含密钥的文件")
    sign_parser.add_argument("--key-id", default="primary", help="密钥ID")
    sign_parser.add_argument("--models-dir", default="models", help="模型目录")
    sign_parser.add_argument("--metadata-dir", default="metadata", help="元数据目录")
    
    # 状态命令
    status_parser = subparsers.add_parser("status", help="查看模型验证状态")
    status_parser.add_argument("model_name", help="要查看的模型名称")
    status_parser.add_argument("--metadata-dir", default="metadata", help="元数据目录")
    
    args = parser.parse_args()
    
    # 如果没有指定命令，显示帮助信息
    if not args.command:
        parser.print_help()
        return 1
    
    # 创建元数据管理器
    metadata_manager = MetadataManager(metadata_dir=args.metadata_dir)
    
    if args.command == "verify":
        # 转换验证级别
        level_map = {
            "basic": VerificationLevel.BASIC,
            "hash": VerificationLevel.HASH,
            "signature": VerificationLevel.SIGNATURE,
            "full": VerificationLevel.FULL
        }
        level = level_map.get(args.level, VerificationLevel.HASH)
        
        # 创建完整性校验器
        checker = IntegrityChecker(
            metadata_manager=metadata_manager,
            models_dir=args.models_dir,
            default_level=level
        )
        
        # 验证模型完整性
        results = checker.verify_dependency_integrity(
            model_name=args.model_name,
            level=level
        )
        
        # 输出结果
        print(f"模型: {args.model_name}")
        print(f"验证级别: {args.level}")
        print(f"总分片数: {results['total_shards']}")
        print(f"通过分片数: {results['passed_shards']}")
        print(f"失败分片数: {results['failed_shards']}")
        print(f"缺失依赖: {'无' if not results['missing_dependencies'] else str(results['missing_dependencies'])}")
        
        if results['failed_shards'] > 0 or args.verbose:
            print("\n验证详情:")
            for shard_id, (success, error) in results['integrity_results'].items():
                status = "✓" if success else "✗"
                if args.verbose or not success:
                    print(f"  {status} 分片 {shard_id}: {error or '验证通过'}")
        
        # 如果有错误，返回非零退出码
        return 0 if results['success'] else 1
        
    elif args.command == "update-hash":
        # 创建完整性校验器
        checker = IntegrityChecker(
            metadata_manager=metadata_manager,
            models_dir=args.models_dir
        )
        
        # 更新哈希值
        updated_count = checker.update_all_hashes(args.model_name)
        
        print(f"已更新 {updated_count} 个分片的哈希值")
        return 0
        
    elif args.command == "sign":
        # 读取密钥
        try:
            with open(args.key_file, "r") as f:
                secret_key = f.read().strip()
        except Exception as e:
            logger.error(f"读取密钥文件失败: {str(e)}")
            return 1
            
        # 创建完整性校验器
        checker = IntegrityChecker(
            metadata_manager=metadata_manager,
            models_dir=args.models_dir,
            secret_key=secret_key
        )
        
        # 获取模型元数据
        metadata = metadata_manager.get_metadata(args.model_name)
        if not metadata:
            logger.error(f"未找到模型 {args.model_name} 的元数据")
            return 1
            
        # 为所有分片生成签名
        success_count = 0
        for shard_id in metadata.get_shards().keys():
            signature = checker.generate_shard_signature(
                model_name=args.model_name,
                shard_id=shard_id,
                key=secret_key,
                key_id=args.key_id
            )
            
            if signature:
                success_count += 1
                print(f"为分片 {shard_id} 生成签名成功")
                
        print(f"成功为 {success_count}/{len(metadata.get_shards())} 个分片生成签名")
        return 0
        
    elif args.command == "status":
        # 创建完整性校验器
        checker = IntegrityChecker(
            metadata_manager=metadata_manager
        )
        
        # 获取验证状态
        status = checker.get_verification_status(args.model_name)
        
        if not status["exists"]:
            print(status["message"])
            return 1
            
        print(f"模型: {args.model_name}")
        print(f"总分片数: {status['total_shards']}")
        print(f"带有哈希值的分片数: {status['hashed_shards']}")
        print(f"带有签名的分片数: {status['signed_shards']}")
        
        if status['last_verified']:
            print(f"上次验证时间: {status['last_verified']}")
            print(f"上次验证结果: {'成功' if status['last_result'] else '失败'}")
            
        return 0

if __name__ == "__main__":
    sys.exit(main()) 