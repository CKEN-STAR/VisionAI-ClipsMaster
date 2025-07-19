"""模型分片元数据管理模块

此模块提供模型分片元数据的管理功能，包括：
1. 跟踪分片文件、所含层及其依赖关系
2. 验证分片完整性与依赖合法性
3. 计算最优分片加载顺序
4. 支持API和命令行界面
"""

import os
import time
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Set, Any, Optional, Tuple, Union
from loguru import logger


class ShardMetadata:
    """分片元数据类，管理单个模型的分片信息"""
    
    def __init__(self, model_name: str):
        """初始化分片元数据
        
        Args:
            model_name: 模型名称
        """
        self.model_name = model_name
        self.version = 1.0
        self.creation_time = time.time()
        self.last_modified = time.time()
        self.shards = {}  # 分片元数据映射
        
    def add_shard(self, 
                 shard_id: str, 
                 layers: List[str], 
                 hash: Optional[str] = None,
                 depends_on: Optional[List[str]] = None,
                 shard_path: Optional[str] = None,
                 shard_size: Optional[int] = None) -> Dict:
        """添加分片元数据
        
        Args:
            shard_id: 分片ID
            layers: 分片包含的层列表
            hash: 分片哈希值
            depends_on: 依赖的其他分片ID列表
            shard_path: 分片文件路径
            shard_size: 分片大小(字节)
            
        Returns:
            Dict: 添加的分片元数据
        """
        shard_metadata = {
            "layers": layers or [],
            "hash": hash,
            "depends_on": depends_on or [],
            "created_at": time.time(),
            "updated_at": time.time(),
        }
        
        if shard_path:
            shard_metadata["path"] = shard_path
        
        if shard_size:
            shard_metadata["size_bytes"] = shard_size
        
        self.shards[shard_id] = shard_metadata
        self.last_modified = time.time()
        
        return shard_metadata
    
    def update_shard(self,
                    shard_id: str,
                    layers: Optional[List[str]] = None,
                    hash: Optional[str] = None,
                    depends_on: Optional[List[str]] = None,
                    shard_path: Optional[str] = None,
                    shard_size: Optional[int] = None) -> Optional[Dict]:
        """更新分片元数据
        
        Args:
            shard_id: 分片ID
            layers: 分片包含的层列表
            hash: 分片哈希值
            depends_on: 依赖的其他分片ID列表
            shard_path: 分片文件路径
            shard_size: 分片大小(字节)
            
        Returns:
            Optional[Dict]: 更新后的分片元数据，如果分片不存在则返回None
        """
        if shard_id not in self.shards:
            logger.warning(f"尝试更新不存在的分片: {shard_id}")
            return None
        
        shard = self.shards[shard_id]
        
        if layers is not None:
            shard["layers"] = layers
        
        if hash is not None:
            shard["hash"] = hash
            
        if depends_on is not None:
            shard["depends_on"] = depends_on
            
        if shard_path is not None:
            shard["path"] = shard_path
            
        if shard_size is not None:
            shard["size_bytes"] = shard_size
        
        shard["updated_at"] = time.time()
        self.last_modified = time.time()
        
        return shard
    
    def remove_shard(self, shard_id: str) -> bool:
        """移除分片元数据
        
        Args:
            shard_id: 分片ID
            
        Returns:
            bool: 是否成功移除
        """
        if shard_id not in self.shards:
            logger.warning(f"尝试移除不存在的分片: {shard_id}")
            return False
        
        del self.shards[shard_id]
        self.last_modified = time.time()
        
        return True
    
    def get_shard(self, shard_id: str) -> Optional[Dict]:
        """获取分片元数据
        
        Args:
            shard_id: 分片ID
            
        Returns:
            Optional[Dict]: 分片元数据，如果不存在则返回None
        """
        return self.shards.get(shard_id)
    
    def get_shards(self) -> Dict[str, Dict]:
        """获取所有分片元数据
        
        Returns:
            Dict[str, Dict]: 所有分片元数据映射
        """
        return self.shards
    
    def verify_dependencies(self) -> Dict[str, List[str]]:
        """验证分片依赖关系
        
        Returns:
            Dict[str, List[str]]: 包含缺失依赖的分片映射：{shard_id: [missing_dep1, missing_dep2, ...]}，
                                 如果没有缺失依赖则返回空字典
        """
        missing_dependencies = {}
        
        for shard_id, shard in self.shards.items():
            deps = shard.get("depends_on", [])
            
            # 检查每个依赖是否存在
            missing = [dep for dep in deps if dep not in self.shards]
            
            if missing:
                missing_dependencies[shard_id] = missing
        
        return missing_dependencies
    
    def verify_shard(self, 
                    shard_id: str, 
                    base_dir: Optional[str] = None) -> Tuple[bool, str]:
        """验证分片完整性
        
        Args:
            shard_id: 分片ID
            base_dir: 基础目录，如果分片路径是相对路径，则相对于此目录
            
        Returns:
            Tuple[bool, str]: (是否验证通过, 错误消息)
        """
        if shard_id not in self.shards:
            return False, f"分片 {shard_id} 不存在"
        
        shard = self.shards[shard_id]
        
        # 检查是否有路径
        if "path" not in shard:
            return False, f"分片 {shard_id} 没有路径信息"
        
        # 检查文件是否存在
        path = shard["path"]
        if base_dir and not os.path.isabs(path):
            path = os.path.join(base_dir, path)
        
        if not os.path.exists(path):
            return False, f"分片文件不存在: {path}"
        
        # 如果有哈希值，验证哈希
        if "hash" in shard and shard["hash"]:
            try:
                with open(path, 'rb') as f:
                    content = f.read()
                    actual_hash = hashlib.sha256(content).hexdigest()
                    
                    if actual_hash != shard["hash"]:
                        return False, f"分片哈希不匹配: 期望 {shard['hash'][:8]}...，实际 {actual_hash[:8]}..."
            except Exception as e:
                return False, f"验证分片哈希时出错: {e}"
        
        # 如果有大小信息，验证大小
        if "size_bytes" in shard:
            actual_size = os.path.getsize(path)
            if actual_size != shard["size_bytes"]:
                return False, f"分片大小不匹配: 期望 {shard['size_bytes']} 字节，实际 {actual_size} 字节"
        
        return True, "验证通过"
    
    def verify_all_shards(self, base_dir: Optional[str] = None) -> Dict[str, Tuple[bool, str]]:
        """验证所有分片完整性
        
        Args:
            base_dir: 基础目录，如果分片路径是相对路径，则相对于此目录
            
        Returns:
            Dict[str, Tuple[bool, str]]: 验证结果映射：{shard_id: (是否通过, 消息)}
        """
        results = {}
        
        for shard_id in self.shards:
            results[shard_id] = self.verify_shard(shard_id, base_dir)
        
        return results
    
    def get_loading_order(self) -> List[str]:
        """获取分片加载顺序
        
        Returns:
            List[str]: 分片ID的加载顺序列表
        """
        # 验证依赖关系
        missing_deps = self.verify_dependencies()
        if missing_deps:
            missing_str = ", ".join(f"{sid}: {deps}" for sid, deps in missing_deps.items())
            raise ValueError(f"存在缺失的依赖关系，无法确定加载顺序: {missing_str}")
        
        # 如果没有分片，返回空列表
        if not self.shards:
            return []
        
        # 使用拓扑排序确定加载顺序
        result = []
        visited = set()
        temp_visited = set()
        
        def visit(shard_id):
            if shard_id in temp_visited:
                # 检测到循环依赖
                raise ValueError(f"检测到循环依赖关系，涉及分片: {shard_id}")
            
            if shard_id in visited:
                return
            
            temp_visited.add(shard_id)
            
            # 递归访问依赖
            for dep_id in self.shards[shard_id].get("depends_on", []):
                visit(dep_id)
            
            temp_visited.remove(shard_id)
            visited.add(shard_id)
            result.append(shard_id)
        
        # 对每个分片执行拓扑排序
        for shard_id in self.shards:
            if shard_id not in visited:
                visit(shard_id)
        
        return result
    
    def get_layer_to_shard_mapping(self) -> Dict[str, str]:
        """获取层到分片的映射
        
        Returns:
            Dict[str, str]: 层到分片ID的映射
        """
        layer_to_shard = {}
        
        for shard_id, shard in self.shards.items():
            for layer in shard.get("layers", []):
                # 如果一个层出现在多个分片中，使用最后一个
                layer_to_shard[layer] = shard_id
        
        return layer_to_shard
    
    def to_dict(self) -> Dict:
        """将元数据转换为字典
        
        Returns:
            Dict: 元数据字典
        """
        return {
            "model_name": self.model_name,
            "version": self.version,
            "creation_time": self.creation_time,
            "last_modified": self.last_modified,
            "shards": self.shards
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ShardMetadata':
        """从字典创建元数据对象
        
        Args:
            data: 元数据字典
            
        Returns:
            ShardMetadata: 元数据对象
        """
        metadata = cls(data["model_name"])
        metadata.version = data.get("version", 1.0)
        metadata.creation_time = data.get("creation_time", time.time())
        metadata.last_modified = data.get("last_modified", time.time())
        metadata.shards = data.get("shards", {})
        
        return metadata


class MetadataManager:
    """元数据管理器，管理多个模型的分片元数据"""
    
    def __init__(self, metadata_dir: str = "metadata"):
        """初始化元数据管理器
        
        Args:
            metadata_dir: 元数据存储目录
        """
        self.metadata_dir = Path(metadata_dir)
        self.metadata_cache = {}  # 元数据缓存
        
        # 确保元数据目录存在
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
    
    def create_metadata(self, model_name: str) -> ShardMetadata:
        """创建模型元数据
        
        Args:
            model_name: 模型名称
            
        Returns:
            ShardMetadata: 元数据对象
        """
        metadata = ShardMetadata(model_name)
        self.metadata_cache[model_name] = metadata
        
        return metadata
    
    def get_metadata(self, 
                    model_name: str, 
                    create_if_not_exists: bool = False) -> Optional[ShardMetadata]:
        """获取模型元数据
        
        Args:
            model_name: 模型名称
            create_if_not_exists: 如果不存在是否创建
            
        Returns:
            Optional[ShardMetadata]: 元数据对象，如果不存在且不创建则返回None
        """
        # 检查缓存
        if model_name in self.metadata_cache:
            return self.metadata_cache[model_name]
        
        # 尝试加载
        metadata_path = self.get_metadata_path(model_name)
        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                metadata = ShardMetadata.from_dict(data)
                self.metadata_cache[model_name] = metadata
                
                return metadata
            except Exception as e:
                logger.error(f"加载元数据失败: {metadata_path}, 错误: {e}")
                
                if create_if_not_exists:
                    logger.info(f"创建新的元数据: {model_name}")
                    return self.create_metadata(model_name)
                
                return None
        elif create_if_not_exists:
            return self.create_metadata(model_name)
        
        return None
    
    def save_metadata(self, model_name: str) -> bool:
        """保存模型元数据
        
        Args:
            model_name: 模型名称
            
        Returns:
            bool: 是否保存成功
        """
        if model_name not in self.metadata_cache:
            logger.warning(f"尝试保存不存在的元数据: {model_name}")
            return False
        
        metadata = self.metadata_cache[model_name]
        metadata_path = self.get_metadata_path(model_name)
        
        try:
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata.to_dict(), f, indent=2, ensure_ascii=False)
            
            logger.info(f"保存元数据成功: {metadata_path}")
            return True
        except Exception as e:
            logger.error(f"保存元数据失败: {metadata_path}, 错误: {e}")
            return False
    
    def get_metadata_path(self, model_name: str) -> str:
        """获取元数据文件路径
        
        Args:
            model_name: 模型名称
            
        Returns:
            str: 元数据文件路径
        """
        return str(self.metadata_dir / f"{model_name}_metadata.json")
    
    def list_models(self) -> List[str]:
        """列出所有模型
        
        Returns:
            List[str]: 模型名称列表
        """
        models = []
        
        for file in self.metadata_dir.glob("*_metadata.json"):
            model_name = file.stem.replace("_metadata", "")
            models.append(model_name)
        
        return models
    
    def generate_metadata_from_shards(self,
                                     model_name: str,
                                     shard_dir: str,
                                     shard_info_file: Optional[str] = None) -> Optional[ShardMetadata]:
        """从分片目录生成元数据
        
        Args:
            model_name: 模型名称
            shard_dir: 分片目录
            shard_info_file: 分片信息文件路径
            
        Returns:
            Optional[ShardMetadata]: 生成的元数据对象，失败则返回None
        """
        shard_dir = Path(shard_dir)
        if not shard_dir.exists():
            logger.error(f"分片目录不存在: {shard_dir}")
            return None
        
        # 创建元数据
        metadata = self.create_metadata(model_name)
        
        # 尝试从分片信息文件加载信息
        layer_mapping = None
        shard_info = None
        
        if shard_info_file and os.path.exists(shard_info_file):
            try:
                with open(shard_info_file, 'r', encoding='utf-8') as f:
                    shard_info = json.load(f)
                
                # 尝试加载层映射
                if "layer_mapping_file" in shard_info and os.path.exists(shard_info["layer_mapping_file"]):
                    with open(shard_info["layer_mapping_file"], 'r', encoding='utf-8') as f:
                        layer_mapping = json.load(f)
            except Exception as e:
                logger.warning(f"加载分片信息文件失败: {e}")
                # 继续处理，使用目录扫描方式
        
        # 查找分片文件
        shard_files = sorted(shard_dir.glob("*_part_*.bin"))
        if not shard_files:
            shard_files = sorted(shard_dir.glob("model_part_*.bin"))
        
        if not shard_files:
            logger.error(f"未找到分片文件: {shard_dir}")
            return None
        
        # 获取校验和信息
        checksums = {}
        checksum_file = shard_dir / "checksums.json"
        if checksum_file.exists():
            try:
                with open(checksum_file, 'r', encoding='utf-8') as f:
                    checksum_data = json.load(f)
                    if "checksums" in checksum_data and isinstance(checksum_data["checksums"], list):
                        for i, checksum in enumerate(checksum_data["checksums"]):
                            checksums[f"shard_{i:03d}"] = checksum
            except Exception as e:
                logger.warning(f"加载校验和文件失败: {e}")
        
        # 为每个分片文件创建元数据
        for i, shard_file in enumerate(shard_files):
            shard_id = f"shard_{i:03d}"
            shard_path = str(shard_file)
            
            # 获取分片大小
            shard_size = shard_file.stat().st_size
            
            # 获取分片哈希
            hash_value = checksums.get(shard_id)
            if not hash_value:
                try:
                    with open(shard_file, 'rb') as f:
                        hash_value = hashlib.sha256(f.read()).hexdigest()
                except Exception as e:
                    logger.warning(f"计算分片哈希失败: {shard_file}, 错误: {e}")
                    hash_value = None
            
            # 获取分片包含的层
            layers = []
            if layer_mapping:
                # 从层映射文件获取
                for mapping_key, mapping_info in layer_mapping.items():
                    if mapping_info.get("path") == shard_path or i == int(mapping_key.split('_')[-1]):
                        layers = mapping_info.get("layers", [])
                        break
            
            # 设置依赖关系
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
                shard_size=shard_size
            )
        
        # 保存元数据
        self.save_metadata(model_name)
        
        return metadata
    
    def delete_metadata(self, model_name: str) -> bool:
        """删除模型元数据
        
        Args:
            model_name: 模型名称
            
        Returns:
            bool: 是否删除成功
        """
        # 从缓存中移除
        if model_name in self.metadata_cache:
            del self.metadata_cache[model_name]
        
        # 删除文件
        metadata_path = self.get_metadata_path(model_name)
        if os.path.exists(metadata_path):
            try:
                os.remove(metadata_path)
                logger.info(f"删除元数据成功: {metadata_path}")
                return True
            except Exception as e:
                logger.error(f"删除元数据失败: {metadata_path}, 错误: {e}")
                return False
        
        return False 