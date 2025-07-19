#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
分片完整性校验器演示

此示例展示如何使用分片完整性校验器验证模型分片的完整性，
包括哈希校验、数字签名验证和文件头检查等功能。
"""

import os
import sys
import time
import logging
import argparse
import hashlib
import base64
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
    from src.sharding.integrity_checker import (
        IntegrityChecker, VerificationLevel, IntegrityError,
        CorruptedShardError, SignatureError, HeaderError
    )
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
    test_dir = ".test_integrity"
    os.makedirs(test_dir, exist_ok=True)
    
    # 创建模型目录结构
    models_dir = os.path.join(test_dir, "models")
    metadata_dir = os.path.join(test_dir, "metadata")
    
    # 创建目录
    for d in [models_dir, metadata_dir]:
        os.makedirs(d, exist_ok=True)
    
    # 创建测试模型目录
    test_model_dirs = ["test_model"]
    for model_name in test_model_dirs:
        model_dir = os.path.join(models_dir, model_name)
        os.makedirs(model_dir, exist_ok=True)
    
    # 创建测试元数据
    metadata_manager = MetadataManager(metadata_dir=metadata_dir)
    test_metadata = create_test_metadata(metadata_manager)
    
    # 创建测试分片文件
    create_test_shard_files(models_dir, test_metadata)
    
    # 创建完整性校验器
    integrity_checker = IntegrityChecker(
        metadata_manager=metadata_manager,
        models_dir=models_dir,
        secret_key="test_secret_key_for_demo_only",
        default_level=VerificationLevel.HASH
    )
    
    print("测试环境创建完成")
    
    return {
        "test_dir": test_dir,
        "models_dir": models_dir,
        "metadata_dir": metadata_dir,
        "metadata_manager": metadata_manager,
        "integrity_checker": integrity_checker
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
    
    # 有意缺少依赖关系的分片，用于测试依赖关系验证
    test_metadata.add_shard(
        shard_id="shard_4",
        layers=["output_layer"],
        depends_on=["shard_5"],  # shard_5不存在
        shard_path="shard_4.bin",
        shard_size=512*1024  # 512KB
    )
    
    # 保存元数据
    metadata_manager.save_metadata("test_model")
    
    logger.info("测试元数据创建完成")
    
    return test_metadata

def create_test_shard_files(models_dir, test_metadata):
    """创建测试分片文件
    
    Args:
        models_dir: 模型目录
        test_metadata: 测试元数据
    """
    model_dir = os.path.join(models_dir, "test_model")
    
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
            
            # 写入一些随机数据
            if shard_id == "shard_3":
                # 为shard_3故意写入不同的数据，以测试完整性校验
                f.write(os.urandom(shard["size_bytes"] - 28))
            else:
                # 使用确定性数据，以便计算正确的哈希
                fake_data = bytes([i % 256 for i in range(shard["size_bytes"] - 28)])
                f.write(fake_data)
    
    logger.info("测试分片文件创建完成")

def corrupt_shard_file(models_dir, shard_path):
    """故意损坏分片文件，用于测试完整性校验
    
    Args:
        models_dir: 模型目录
        shard_path: 分片文件路径
    """
    file_path = os.path.join(models_dir, "test_model", shard_path)
    
    with open(file_path, "r+b") as f:
        # 跳到文件中间位置
        f.seek(512)
        # 写入一些随机数据
        f.write(os.urandom(64))
    
    logger.info(f"已故意损坏分片文件: {shard_path}")

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

def demo_basic_verification(env):
    """演示基本的完整性校验功能
    
    Args:
        env: 测试环境
    """
    print_separator("基本完整性校验演示")
    
    integrity_checker = env["integrity_checker"]
    model_name = "test_model"
    
    # 1. 计算并更新所有分片的哈希值
    print("\n1. 计算并更新所有分片的哈希值")
    updated_count = integrity_checker.update_all_hashes(model_name)
    print(f"已更新 {updated_count} 个分片的哈希值")
    
    # 2. 验证单个分片
    print("\n2. 验证单个分片")
    for shard_id in ["shard_1", "shard_2", "shard_3"]:
        success, error = integrity_checker.verify_shard(
            model_name=model_name,
            shard_id=shard_id,
            level=VerificationLevel.HASH
        )
        
        status = "通过" if success else "失败"
        print(f"分片 {shard_id} 验证结果: {status}")
        if error:
            print(f"  错误信息: {error}")
    
    # 3. 故意损坏一个分片，然后验证
    print("\n3. 故意损坏分片并验证")
    corrupt_shard_file(env["models_dir"], "shard_2.bin")
    
    success, error = integrity_checker.verify_shard(
        model_name=model_name,
        shard_id="shard_2",
        level=VerificationLevel.HASH
    )
    
    status = "通过" if success else "失败"
    print(f"损坏后分片 shard_2 验证结果: {status}")
    if error:
        print(f"  错误信息: {error}")
    
    # 4. 验证依赖关系
    print("\n4. 验证依赖关系")
    results = integrity_checker.verify_dependency_integrity(model_name)
    
    print(f"依赖关系验证结果: {'通过' if not results['missing_dependencies'] else '失败'}")
    if results['missing_dependencies']:
        print(f"  缺失依赖: {results['missing_dependencies']}")

def demo_signature_verification(env):
    """演示数字签名验证功能
    
    Args:
        env: 测试环境
    """
    print_separator("数字签名验证演示")
    
    integrity_checker = env["integrity_checker"]
    model_name = "test_model"
    
    # 1. 为所有分片生成签名
    print("\n1. 为所有分片生成签名")
    metadata = env["metadata_manager"].get_metadata(model_name)
    
    for shard_id in metadata.get_shards().keys():
        signature = integrity_checker.generate_shard_signature(
            model_name=model_name,
            shard_id=shard_id,
            key_id="test_key"
        )
        
        if signature:
            print(f"为分片 {shard_id} 生成签名成功")
        else:
            print(f"为分片 {shard_id} 生成签名失败")
    
    # 2. 验证签名
    print("\n2. 验证带有签名的分片")
    for shard_id in ["shard_1", "shard_3"]:
        success, error = integrity_checker.verify_shard(
            model_name=model_name,
            shard_id=shard_id,
            level=VerificationLevel.SIGNATURE
        )
        
        status = "通过" if success else "失败"
        print(f"分片 {shard_id} 签名验证结果: {status}")
        if error:
            print(f"  错误信息: {error}")
    
    # 3. 修改密钥后验证签名（应失败）
    print("\n3. 修改密钥后验证签名（应失败）")
    
    # 使用不同的密钥创建一个新的校验器
    new_checker = IntegrityChecker(
        metadata_manager=env["metadata_manager"],
        models_dir=env["models_dir"],
        secret_key="different_key",
        default_level=VerificationLevel.SIGNATURE
    )
    
    success, error = new_checker.verify_shard(
        model_name=model_name,
        shard_id="shard_1",
        level=VerificationLevel.SIGNATURE
    )
    
    status = "通过" if success else "失败"
    print(f"使用不同密钥验证分片 shard_1 结果: {status}")
    if error:
        print(f"  错误信息: {error}")

def demo_full_verification(env):
    """演示完整验证功能
    
    Args:
        env: 测试环境
    """
    print_separator("完整验证演示")
    
    integrity_checker = env["integrity_checker"]
    model_name = "test_model"
    
    # 验证所有分片的完整性
    print("\n验证所有分片的完整性")
    results = integrity_checker.verify_model_shards(
        model_name=model_name,
        level=VerificationLevel.FULL
    )
    
    for shard_id, (success, error) in results.items():
        status = "通过" if success else "失败"
        print(f"分片 {shard_id} 完整验证结果: {status}")
        if error:
            print(f"  错误信息: {error}")
    
    # 获取验证状态
    print("\n获取验证状态")
    status = integrity_checker.get_verification_status(model_name)
    print(f"总分片数: {status['total_shards']}")
    print(f"带有哈希值的分片数: {status['hashed_shards']}")
    print(f"带有签名的分片数: {status['signed_shards']}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="分片完整性校验器演示")
    parser.add_argument("--cleanup", action="store_true", help="运行后清理测试环境")
    args = parser.parse_args()
    
    print_separator("分片完整性校验器演示")
    print("本示例展示如何使用分片完整性校验器验证模型分片的完整性")
    
    try:
        # 创建测试环境
        env = create_test_environment()
        
        # 运行演示
        demo_basic_verification(env)
        demo_signature_verification(env)
        demo_full_verification(env)
        
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