"""分片完整性校验模块

此模块提供模型分片文件的完整性校验功能，包括：
1. 哈希校验 - 验证文件哈希值
2. 数字签名验证 - 验证文件签名
3. 文件头格式检查 - 确保文件格式正确
4. 批量验证工具 - 验证模型的所有分片
"""

import os
import time
import json
import hashlib
import hmac
import struct
import base64
from enum import Enum
from pathlib import Path
from typing import Dict, List, Set, Any, Optional, Tuple, Union, Callable
from loguru import logger

from src.sharding.metadata_manager import ShardMetadata, MetadataManager


class IntegrityError(Exception):
    """完整性检查错误基类"""
    pass


class CorruptedShardError(IntegrityError):
    """分片损坏错误"""
    pass


class SignatureError(IntegrityError):
    """签名验证失败错误"""
    pass


class HeaderError(IntegrityError):
    """文件头错误"""
    pass


class VerificationLevel(Enum):
    """校验级别"""
    BASIC = 0      # 只进行基本检查（文件是否存在等）
    HASH = 1       # 包含哈希校验
    SIGNATURE = 2  # 包含数字签名校验
    FULL = 3       # 完整校验（包括文件头格式等）


class IntegrityChecker:
    """分片完整性校验器
    
    提供各种级别的分片完整性校验功能
    """
    
    # 有效的文件头魔数 (模型文件类型的标识符)
    VALID_MAGIC_NUMBERS = {
        b'GGUF': "GGUF格式模型文件",
        b'GGML': "GGML格式模型文件",
        b'SAFETENSORS': "SafeTensors格式模型文件",
        b'PK\x03\x04': "ZIP格式文件(可能是模型权重)"
    }
    
    def __init__(
        self,
        metadata_manager: Optional[MetadataManager] = None,
        models_dir: str = "models",
        secret_key: Optional[str] = None,
        default_level: VerificationLevel = VerificationLevel.HASH,
        trusted_keys: Optional[Dict[str, str]] = None
    ):
        """初始化完整性校验器
        
        Args:
            metadata_manager: 元数据管理器实例
            models_dir: 模型目录
            secret_key: 用于签名验证的密钥
            default_level: 默认验证级别
            trusted_keys: 可信任的公钥集合 {key_id: public_key}
        """
        self.metadata_manager = metadata_manager or MetadataManager()
        self.models_dir = models_dir
        self.secret_key = secret_key
        self.default_level = default_level
        self.trusted_keys = trusted_keys or {}
        
        # 缓存验证结果
        self.verification_cache = {}
        
        logger.info(f"分片完整性校验器初始化完成，默认验证级别: {default_level.name}")
    
    def verify_shard(
        self,
        model_name: str,
        shard_id: str,
        level: Optional[VerificationLevel] = None,
        base_dir: Optional[str] = None,
        update_hash: bool = False
    ) -> Tuple[bool, Optional[str]]:
        """验证单个分片的完整性
        
        Args:
            model_name: 模型名称
            shard_id: 分片ID
            level: 验证级别
            base_dir: 基础目录（如果不指定则使用models_dir/model_name）
            update_hash: 是否更新元数据中的哈希值
            
        Returns:
            Tuple[bool, Optional[str]]: (是否验证通过, 错误信息)
        """
        level = level or self.default_level
        
        # 尝试获取模型元数据
        metadata = self.metadata_manager.get_metadata(model_name)
        if not metadata:
            return False, f"未找到模型 {model_name} 的元数据"
        
        # 检查分片是否存在于元数据中
        shard_meta = metadata.get_shard(shard_id)
        if not shard_meta:
            return False, f"分片 {shard_id} 在模型 {model_name} 的元数据中不存在"
        
        # 获取分片路径
        shard_path = shard_meta.get("path")
        if not shard_path:
            return False, f"分片 {shard_id} 没有指定路径"
        
        # 获取完整路径
        if not base_dir:
            base_dir = os.path.join(self.models_dir, model_name)
        
        if not os.path.isabs(shard_path):
            full_path = os.path.join(base_dir, shard_path)
        else:
            full_path = shard_path
        
        # 检查文件是否存在
        if not os.path.exists(full_path):
            return False, f"分片文件不存在: {full_path}"
        
        # 根据验证级别执行相应的验证
        try:
            # 基本验证通过，继续进行哈希验证
            if level.value >= VerificationLevel.HASH.value:
                self._verify_hash(shard_meta, full_path, update_hash)
            
            # 验证数字签名
            if level.value >= VerificationLevel.SIGNATURE.value:
                self._verify_signature(shard_meta, full_path)
            
            # 进行完整验证，包括文件头格式检查
            if level.value >= VerificationLevel.FULL.value:
                self._verify_file_format(shard_meta, full_path)
            
            # 所有验证通过
            return True, None
            
        except IntegrityError as e:
            return False, str(e)
    
    def _verify_hash(self, shard_meta: Dict, file_path: str, update_hash: bool = False) -> bool:
        """验证分片哈希值
        
        Args:
            shard_meta: 分片元数据
            file_path: 分片文件路径
            update_hash: 是否更新元数据中的哈希值
            
        Returns:
            bool: 是否验证通过
            
        Raises:
            CorruptedShardError: 如果哈希验证失败
        """
        expected_hash = shard_meta.get("hash")
        actual_hash = self._calculate_file_hash(file_path)
        
        if expected_hash and expected_hash != actual_hash:
            raise CorruptedShardError(
                f"分片哈希验证失败: 期望={expected_hash}, 实际={actual_hash}, 文件={file_path}"
            )
        
        # 如果元数据中没有哈希值或者需要更新，则更新哈希值
        if update_hash or not expected_hash:
            shard_meta["hash"] = actual_hash
        
        return True
    
    def _calculate_file_hash(self, file_path: str, algorithm: str = "sha256") -> str:
        """计算文件哈希值
        
        Args:
            file_path: 文件路径
            algorithm: 哈希算法，默认sha256
            
        Returns:
            str: 哈希值的十六进制表示
        """
        hash_obj = hashlib.new(algorithm)
        
        with open(file_path, "rb") as f:
            # 分块读取以处理大文件
            for chunk in iter(lambda: f.read(4096), b""):
                hash_obj.update(chunk)
        
        return hash_obj.hexdigest()
    
    def _verify_signature(self, shard_meta: Dict, file_path: str) -> bool:
        """验证分片数字签名
        
        Args:
            shard_meta: 分片元数据
            file_path: 分片文件路径
            
        Returns:
            bool: 是否验证通过
            
        Raises:
            SignatureError: 如果签名验证失败
        """
        signature = shard_meta.get("signature")
        if not signature:
            logger.warning(f"分片 {os.path.basename(file_path)} 没有数字签名")
            return True  # 没有签名不失败，只是提醒
        
        key_id = shard_meta.get("key_id")
        if not key_id:
            raise SignatureError(f"分片有签名但没有指定key_id")
        
        # 获取密钥
        if key_id not in self.trusted_keys and not self.secret_key:
            raise SignatureError(f"未找到验证签名所需的密钥: {key_id}")
        
        key = self.trusted_keys.get(key_id) or self.secret_key
        
        # 验证签名
        try:
            # 读取文件内容
            with open(file_path, "rb") as f:
                content = f.read()
            
            # 解码签名
            decoded_signature = base64.b64decode(signature)
            
            # 创建HMAC对象并验证
            h = hmac.new(key.encode() if isinstance(key, str) else key, content, hashlib.sha256)
            computed_signature = h.digest()
            
            if not hmac.compare_digest(computed_signature, decoded_signature):
                raise SignatureError(f"分片 {os.path.basename(file_path)} 的签名验证失败")
                
            return True
            
        except Exception as e:
            raise SignatureError(f"签名验证过程出错: {str(e)}")
    
    def _verify_file_format(self, shard_meta: Dict, file_path: str) -> bool:
        """验证文件格式和文件头
        
        Args:
            shard_meta: 分片元数据
            file_path: 分片文件路径
            
        Returns:
            bool: 是否验证通过
            
        Raises:
            HeaderError: 如果文件头验证失败
        """
        try:
            with open(file_path, "rb") as f:
                # 读取头部
                header = f.read(16)  # 假设魔数不超过16字节
                
                # 检查魔数
                magic_found = False
                for magic, desc in self.VALID_MAGIC_NUMBERS.items():
                    if header.startswith(magic):
                        magic_found = True
                        break
                
                if not magic_found:
                    raise HeaderError(f"文件 {os.path.basename(file_path)} 不是有效的模型文件格式")
                
                # 可以进一步检查版本、文件大小等
                # ...
                
                return True
                
        except Exception as e:
            if isinstance(e, HeaderError):
                raise
            raise HeaderError(f"验证文件头时出错: {str(e)}")
    
    def verify_model_shards(
        self,
        model_name: str,
        level: Optional[VerificationLevel] = None,
        base_dir: Optional[str] = None,
        update_hash: bool = False
    ) -> Dict[str, Tuple[bool, Optional[str]]]:
        """验证模型的所有分片
        
        Args:
            model_name: 模型名称
            level: 验证级别
            base_dir: 基础目录
            update_hash: 是否更新元数据中的哈希值
            
        Returns:
            Dict[str, Tuple[bool, Optional[str]]]: {shard_id: (是否通过, 错误信息)}
        """
        # 获取模型元数据
        metadata = self.metadata_manager.get_metadata(model_name)
        if not metadata:
            return {
                "model_metadata": (False, f"未找到模型 {model_name} 的元数据")
            }
        
        results = {}
        
        # 遍历所有分片进行验证
        for shard_id in metadata.get_shards().keys():
            success, error = self.verify_shard(
                model_name=model_name,
                shard_id=shard_id,
                level=level,
                base_dir=base_dir,
                update_hash=update_hash
            )
            
            results[shard_id] = (success, error)
            
            # 如果更新了哈希值，需要保存元数据
            if success and update_hash:
                self.metadata_manager.save_metadata(model_name)
        
        return results
    
    def generate_shard_signature(
        self,
        model_name: str,
        shard_id: str,
        key: Optional[str] = None,
        key_id: Optional[str] = None,
        base_dir: Optional[str] = None
    ) -> Optional[str]:
        """为分片生成数字签名
        
        Args:
            model_name: 模型名称
            shard_id: 分片ID
            key: 用于签名的密钥，如果为None则使用self.secret_key
            key_id: 密钥ID，用于标识使用的密钥
            base_dir: 基础目录
            
        Returns:
            Optional[str]: 生成的签名，如果失败则返回None
        """
        if not key and not self.secret_key:
            logger.error("未提供签名密钥")
            return None
        
        # 使用提供的密钥或默认密钥
        signing_key = key or self.secret_key
        
        # 获取模型元数据
        metadata = self.metadata_manager.get_metadata(model_name)
        if not metadata:
            logger.error(f"未找到模型 {model_name} 的元数据")
            return None
        
        # 获取分片元数据
        shard_meta = metadata.get_shard(shard_id)
        if not shard_meta:
            logger.error(f"分片 {shard_id} 在模型 {model_name} 的元数据中不存在")
            return None
        
        # 获取分片路径
        shard_path = shard_meta.get("path")
        if not shard_path:
            logger.error(f"分片 {shard_id} 没有指定路径")
            return None
        
        # 获取完整路径
        if not base_dir:
            base_dir = os.path.join(self.models_dir, model_name)
        
        if not os.path.isabs(shard_path):
            full_path = os.path.join(base_dir, shard_path)
        else:
            full_path = shard_path
        
        # 检查文件是否存在
        if not os.path.exists(full_path):
            logger.error(f"分片文件不存在: {full_path}")
            return None
        
        try:
            # 读取文件内容
            with open(full_path, "rb") as f:
                content = f.read()
            
            # 创建HMAC对象并计算签名
            signing_key_bytes = signing_key.encode() if isinstance(signing_key, str) else signing_key
            h = hmac.new(signing_key_bytes, content, hashlib.sha256)
            signature = base64.b64encode(h.digest()).decode('utf-8')
            
            # 更新元数据
            shard_meta["signature"] = signature
            if key_id:
                shard_meta["key_id"] = key_id
            
            # 保存元数据
            self.metadata_manager.save_metadata(model_name)
            
            return signature
            
        except Exception as e:
            logger.error(f"生成签名时出错: {str(e)}")
            return None
    
    def verify_dependency_integrity(
        self,
        model_name: str,
        level: Optional[VerificationLevel] = None
    ) -> Dict[str, Any]:
        """验证依赖完整性
        
        检查分片依赖关系是否完整，以及所有依赖分片是否完整
        
        Args:
            model_name: 模型名称
            level: 验证级别
            
        Returns:
            Dict[str, Any]: 验证结果，包括依赖关系和完整性检查结果
        """
        # 获取模型元数据
        metadata = self.metadata_manager.get_metadata(model_name)
        if not metadata:
            return {
                "success": False,
                "error": f"未找到模型 {model_name} 的元数据"
            }
        
        # 检查依赖关系
        missing_deps = metadata.verify_dependencies()
        
        # 验证所有分片的完整性
        integrity_results = self.verify_model_shards(
            model_name=model_name,
            level=level
        )
        
        # 统计结果
        total_shards = len(metadata.get_shards())
        passed_shards = sum(1 for success, _ in integrity_results.values() if success)
        
        return {
            "success": len(missing_deps) == 0 and passed_shards == total_shards,
            "missing_dependencies": missing_deps,
            "integrity_results": integrity_results,
            "total_shards": total_shards,
            "passed_shards": passed_shards,
            "failed_shards": total_shards - passed_shards
        }
    
    def update_all_hashes(self, model_name: str) -> int:
        """更新模型所有分片的哈希值
        
        Args:
            model_name: 模型名称
            
        Returns:
            int: 成功更新的分片数量
        """
        # 获取模型元数据
        metadata = self.metadata_manager.get_metadata(model_name)
        if not metadata:
            logger.error(f"未找到模型 {model_name} 的元数据")
            return 0
        
        base_dir = os.path.join(self.models_dir, model_name)
        updated_count = 0
        
        # 遍历所有分片更新哈希值
        for shard_id in metadata.get_shards().keys():
            success, _ = self.verify_shard(
                model_name=model_name,
                shard_id=shard_id,
                level=VerificationLevel.HASH,
                base_dir=base_dir,
                update_hash=True
            )
            
            if success:
                updated_count += 1
        
        # 保存元数据
        if updated_count > 0:
            self.metadata_manager.save_metadata(model_name)
        
        return updated_count
    
    def get_verification_status(self, model_name: str) -> Dict[str, Any]:
        """获取模型验证状态
        
        Args:
            model_name: 模型名称
            
        Returns:
            Dict[str, Any]: 验证状态信息
        """
        # 获取模型元数据
        metadata = self.metadata_manager.get_metadata(model_name)
        if not metadata:
            return {
                "exists": False,
                "message": f"未找到模型 {model_name} 的元数据"
            }
        
        shards = metadata.get_shards()
        
        # 统计签名和哈希值的状态
        signed_shards = sum(1 for shard in shards.values() if "signature" in shard)
        hashed_shards = sum(1 for shard in shards.values() if "hash" in shard)
        
        return {
            "exists": True,
            "total_shards": len(shards),
            "signed_shards": signed_shards,
            "hashed_shards": hashed_shards,
            "last_verified": self.verification_cache.get(model_name, {}).get("timestamp"),
            "last_result": self.verification_cache.get(model_name, {}).get("result")
        }

# 命令行工具
def verify_model_cli(args=None):
    """命令行工具入口"""
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description="模型分片完整性校验工具")
    parser.add_argument("model_name", help="要验证的模型名称")
    parser.add_argument("--level", type=str, choices=["basic", "hash", "signature", "full"],
                      default="hash", help="验证级别")
    parser.add_argument("--update-hash", action="store_true", help="是否更新哈希值")
    parser.add_argument("--models-dir", type=str, default="models", help="模型目录")
    parser.add_argument("--metadata-dir", type=str, default="metadata", help="元数据目录")
    parser.add_argument("--generate-signatures", action="store_true", help="为所有分片生成签名")
    parser.add_argument("--key-file", type=str, help="包含密钥的文件")
    
    if args is None:
        args = parser.parse_args()
    else:
        args = parser.parse_args(args)
    
    # 转换验证级别
    level_map = {
        "basic": VerificationLevel.BASIC,
        "hash": VerificationLevel.HASH,
        "signature": VerificationLevel.SIGNATURE,
        "full": VerificationLevel.FULL
    }
    level = level_map.get(args.level, VerificationLevel.HASH)
    
    # 加载密钥
    secret_key = None
    if args.key_file and os.path.exists(args.key_file):
        try:
            with open(args.key_file, "r") as f:
                secret_key = f.read().strip()
        except Exception as e:
            print(f"读取密钥文件失败: {str(e)}")
            return 1
    
    # 创建元数据管理器
    metadata_manager = MetadataManager(metadata_dir=args.metadata_dir)
    
    # 创建完整性校验器
    checker = IntegrityChecker(
        metadata_manager=metadata_manager,
        models_dir=args.models_dir,
        secret_key=secret_key,
        default_level=level
    )
    
    # 执行验证
    if args.generate_signatures:
        if not secret_key:
            print("错误: 生成签名需要提供密钥")
            return 1
        
        metadata = metadata_manager.get_metadata(args.model_name)
        if not metadata:
            print(f"错误: 未找到模型 {args.model_name} 的元数据")
            return 1
        
        success_count = 0
        for shard_id in metadata.get_shards().keys():
            signature = checker.generate_shard_signature(
                model_name=args.model_name,
                shard_id=shard_id,
                key=secret_key,
                key_id="primary"
            )
            
            if signature:
                success_count += 1
                print(f"为分片 {shard_id} 生成签名成功")
        
        print(f"成功为 {success_count}/{len(metadata.get_shards())} 个分片生成签名")
        return 0
    
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
    
    if results['failed_shards'] > 0:
        print("\n失败详情:")
        for shard_id, (success, error) in results['integrity_results'].items():
            if not success:
                print(f"  分片 {shard_id}: {error}")
    
    # 如果有错误，返回非零退出码
    return 0 if results['success'] else 1

if __name__ == "__main__":
    import sys
    sys.exit(verify_model_cli()) 