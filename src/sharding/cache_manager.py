"""分片缓存管理模块

此模块提供高效的分片缓存管理功能，包括：
1. 基于LRU策略管理模型分片
2. 分片加载和释放机制
3. 依赖关系管理和追踪
4. 内存占用监控
5. 缓存命中率统计
"""

import os
import gc
import time
import threading
import torch
from typing import Dict, List, Set, Any, Optional, Tuple, Union, Callable
from collections import OrderedDict
from pathlib import Path
from loguru import logger

from src.sharding.metadata_manager import ShardMetadata, MetadataManager
from src.sharding.strategy_manager import StrategyManager
from src.sharding.cache_policy import CachePolicy, LRUPolicy


class ShardCache:
    """分片缓存管理器
    
    基于LRU策略管理模型分片的加载和卸载，优化内存使用。
    """
    
    def __init__(
        self, 
        max_size: int = 5,
        load_callback: Optional[Callable[[str], Any]] = None,
        unload_callback: Optional[Callable[[str], bool]] = None
    ):
        """初始化分片缓存管理器
        
        Args:
            max_size: 最大缓存分片数量
            load_callback: 分片加载回调函数 (shard_id -> loaded_shard)
            unload_callback: 分片卸载回调函数 (shard_id -> success)
        """
        self.max_size = max_size
        self.cache = OrderedDict()  # 使用OrderedDict实现LRU缓存
        self.load_callback = load_callback
        self.unload_callback = unload_callback
        
        # 缓存统计
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "total_access": 0,
            "bytes_loaded": 0,
            "bytes_evicted": 0
        }
        
        # 锁，防止并发访问冲突
        self._lock = threading.RLock()
        
        logger.info(f"分片缓存管理器初始化完成，最大缓存容量: {max_size}个分片")
    
    def get(self, shard_id: str, load_if_missing: bool = True) -> Optional[Any]:
        """获取分片
        
        如果分片在缓存中，移动到最近使用的位置并返回
        如果分片不在缓存中且load_if_missing为True，则尝试加载
        
        Args:
            shard_id: 分片ID
            load_if_missing: 如果分片不在缓存中，是否尝试加载
            
        Returns:
            Optional[Any]: 分片数据，如果不存在且未加载则返回None
        """
        with self._lock:
            self.stats["total_access"] += 1
            
            # 检查分片是否在缓存中
            if shard_id in self.cache:
                # 缓存命中
                self.stats["hits"] += 1
                
                # 将此分片移到最近使用的位置
                self.cache.move_to_end(shard_id)
                
                return self.cache[shard_id]
            
            # 缓存未命中
            self.stats["misses"] += 1
            
            if not load_if_missing:
                return None
            
            # 尝试加载分片
            shard_data = self._load_shard(shard_id)
            if shard_data is not None:
                # 将新加载的分片添加到缓存
                self.put(shard_id, shard_data)
                return shard_data
            
            return None
    
    def put(self, shard_id: str, data: Any, size_bytes: int = 0) -> bool:
        """将分片添加到缓存
        
        如果缓存已满，会删除最久未使用的分片
        
        Args:
            shard_id: 分片ID
            data: 分片数据
            size_bytes: 分片大小（字节），用于统计
            
        Returns:
            bool: 操作是否成功
        """
        with self._lock:
            # 如果缓存已满，需要删除最久未使用的分片
            if len(self.cache) >= self.max_size and shard_id not in self.cache:
                self._evict_lru()
            
            # 添加/更新分片
            self.cache[shard_id] = data
            # 将此分片移到最近使用的位置
            self.cache.move_to_end(shard_id)
            
            # 更新统计
            if size_bytes > 0:
                self.stats["bytes_loaded"] += size_bytes
            
            return True
    
    def remove(self, shard_id: str) -> bool:
        """从缓存中移除分片
        
        Args:
            shard_id: 分片ID
            
        Returns:
            bool: 是否成功移除
        """
        with self._lock:
            if shard_id not in self.cache:
                return False
            
            # 尝试卸载分片
            success = self._unload_shard(shard_id)
            if not success:
                logger.warning(f"分片 {shard_id} 卸载失败")
                return False
            
            # 从缓存中移除
            del self.cache[shard_id]
            return True
    
    def _evict_lru(self) -> bool:
        """驱逐最久未使用的分片
        
        Returns:
            bool: 是否成功驱逐
        """
        if not self.cache:
            return False
        
        # 获取最久未使用的分片ID
        lru_shard_id, _ = next(iter(self.cache.items()))
        
        # 尝试卸载
        success = self._unload_shard(lru_shard_id)
        if success:
            # 从缓存中移除
            del self.cache[lru_shard_id]
            # 更新统计
            self.stats["evictions"] += 1
            return True
        
        logger.warning(f"最久未使用的分片 {lru_shard_id} 卸载失败")
        return False
    
    def _load_shard(self, shard_id: str) -> Optional[Any]:
        """加载分片
        
        使用注册的加载回调函数加载分片
        
        Args:
            shard_id: 分片ID
            
        Returns:
            Optional[Any]: 加载的分片数据，如果加载失败则返回None
        """
        if not self.load_callback:
            logger.warning("未配置分片加载回调函数")
            return None
        
        try:
            logger.debug(f"加载分片: {shard_id}")
            return self.load_callback(shard_id)
        except Exception as e:
            logger.error(f"分片 {shard_id} 加载失败: {str(e)}")
            return None
    
    def _unload_shard(self, shard_id: str) -> bool:
        """卸载分片
        
        使用注册的卸载回调函数卸载分片
        
        Args:
            shard_id: 分片ID
            
        Returns:
            bool: 是否成功卸载
        """
        if not self.unload_callback:
            logger.warning("未配置分片卸载回调函数")
            # 默认返回True，表示可以从缓存中移除
            return True
        
        try:
            logger.debug(f"卸载分片: {shard_id}")
            return self.unload_callback(shard_id)
        except Exception as e:
            logger.error(f"分片 {shard_id} 卸载失败: {str(e)}")
            return False
    
    def clear(self) -> bool:
        """清空缓存
        
        Returns:
            bool: 是否成功清空缓存
        """
        with self._lock:
            # 遍历所有分片，尝试卸载
            failed_shards = []
            for shard_id in list(self.cache.keys()):
                success = self._unload_shard(shard_id)
                if not success:
                    failed_shards.append(shard_id)
            
            # 清空缓存
            self.cache.clear()
            
            # 如果有卸载失败的分片，记录警告
            if failed_shards:
                logger.warning(f"以下分片卸载失败: {failed_shards}")
                return False
            
            return True
    
    def contains(self, shard_id: str) -> bool:
        """检查分片是否在缓存中
        
        Args:
            shard_id: 分片ID
            
        Returns:
            bool: 分片是否在缓存中
        """
        return shard_id in self.cache
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息
        
        Returns:
            Dict[str, Any]: 缓存统计信息
        """
        stats = dict(self.stats)
        
        # 计算命中率
        total = stats["hits"] + stats["misses"]
        stats["hit_rate"] = stats["hits"] / total if total > 0 else 0
        
        # 添加当前缓存大小
        stats["current_size"] = len(self.cache)
        stats["max_size"] = self.max_size
        
        return stats
    
    def resize(self, new_max_size: int) -> None:
        """调整缓存大小
        
        Args:
            new_max_size: 新的最大缓存容量
        """
        with self._lock:
            if new_max_size < 1:
                logger.warning(f"缓存大小不能小于1, 设置为1")
                new_max_size = 1
                
            self.max_size = new_max_size
            
            # 如果当前缓存大于新容量，驱逐多余的分片
            while len(self.cache) > self.max_size:
                self._evict_lru()
                
            logger.info(f"缓存大小已调整为: {new_max_size}")
    
    def get_cached_shards(self) -> List[str]:
        """获取当前已缓存的分片ID列表
        
        Returns:
            List[str]: 分片ID列表
        """
        return list(self.cache.keys())


class ShardManager:
    """分片管理器
    
    加载、管理和提供模型分片，处理依赖关系和优化内存使用。
    """
    
    def __init__(
        self,
        model_name: str,
        max_shards_in_memory: int = 5,
        metadata_manager: Optional[MetadataManager] = None,
        shard_dir: Optional[str] = None,
        cache_dir: Optional[str] = None,
        strategy_name: Optional[str] = None,
        auto_adjust_strategy: bool = True
    ):
        """初始化分片管理器
        
        Args:
            model_name: 模型名称
            max_shards_in_memory: 最大内存中分片数量
            metadata_manager: 元数据管理器实例，如果为None则自动创建
            shard_dir: 分片存放目录
            cache_dir: 缓存目录
            strategy_name: 使用的缓存策略名称，如果为None则自动选择
            auto_adjust_strategy: 是否自动调整缓存策略
        """
        self.model_name = model_name
        self.max_shards_in_memory = max_shards_in_memory
        
        # 设置分片目录
        if shard_dir:
            self.shard_dir = shard_dir
        else:
            # 默认使用models/{model_name}/shards
            self.shard_dir = os.path.join("models", model_name, "shards")
        
        # 设置缓存目录
        if cache_dir:
            self.cache_dir = cache_dir
        else:
            # 默认使用.cache/{model_name}
            self.cache_dir = os.path.join(".cache", model_name)
        
        # 确保目录存在
        os.makedirs(self.shard_dir, exist_ok=True)
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # 元数据管理器
        self.metadata_manager = metadata_manager or MetadataManager(
            model_name=model_name,
            shard_dir=self.shard_dir
        )
        
        # 缓存策略管理器
        self.strategy_manager = StrategyManager(
            model_name=model_name,
            auto_adjust=auto_adjust_strategy
        )
        
        # 如果指定了策略，则切换到指定策略
        if strategy_name:
            self.strategy_manager.switch_strategy(strategy_name)
            
        # 获取缓存策略实例
        self.cache_policy = self.strategy_manager.get_policy()
        
        # 分片依赖图
        self.shard_dependencies = {}
        self.reverse_dependencies = {}
        
        # 加载分片映射和依赖关系
        self._build_dependency_graph()
        
        # 预热缓存
        self._warm_up_cache()
        
        logger.info(f"分片管理器初始化完成，策略: {self.strategy_manager.get_current_strategy_name()}, 最大分片数: {self.max_shards_in_memory}")
        
    def _build_dependency_graph(self) -> None:
        """构建分片依赖图
        
        从元数据中提取分片依赖关系
        """
        # 获取所有分片的元数据
        shard_metadatas = self.metadata_manager.get_all_shard_metadata()
        
        for shard_id, metadata in shard_metadatas.items():
            # 保存依赖关系
            self.shard_dependencies[shard_id] = metadata.dependencies
            
            # 构建反向依赖关系（被依赖图）
            for dep_id in metadata.dependencies:
                if dep_id not in self.reverse_dependencies:
                    self.reverse_dependencies[dep_id] = set()
                self.reverse_dependencies[dep_id].add(shard_id)
    
    def _load_shard_callback(self, shard_id: str) -> Optional[Any]:
        """加载分片回调
        
        加载指定ID的分片数据
        
        Args:
            shard_id: 分片ID
            
        Returns:
            Optional[Any]: 加载的分片数据
        """
        try:
            # 获取分片路径
            metadata = self.metadata_manager.get_shard_metadata(shard_id)
            if not metadata:
                logger.error(f"分片元数据不存在: {shard_id}")
                return None
                
            # 如果没有指定路径，使用ID作为文件名
            shard_path = os.path.join(self.shard_dir, f"{shard_id}.pt")
            
            # 如果分片文件存在，则加载
            if os.path.exists(shard_path):
                logger.debug(f"加载分片: {shard_id}")
                start_time = time.time()
                
                # 加载模型分片
                shard_data = torch.load(shard_path, map_location="cpu")
                
                load_time = time.time() - start_time
                logger.debug(f"分片 {shard_id} 加载完成，耗时: {load_time:.2f}秒")
                
                # 检查是否需要调整缓存策略
                self.strategy_manager.adjust_strategy_if_needed()
                
                return shard_data
            else:
                logger.error(f"分片文件不存在: {shard_path}")
                return None
                
        except Exception as e:
            logger.error(f"加载分片 {shard_id} 失败: {str(e)}")
            return None
    
    def _unload_shard_callback(self, shard_id: str) -> bool:
        """卸载分片回调
        
        卸载指定ID的分片数据
        
        Args:
            shard_id: 分片ID
            
        Returns:
            bool: 是否成功卸载
        """
        try:
            logger.debug(f"卸载分片: {shard_id}")
            
            # 这里只是从内存中删除引用，让Python的垃圾回收机制回收内存
            # 实际应用中可能需要更复杂的内存管理逻辑
            
            # 强制进行垃圾回收
            gc.collect()
            
            # 如果使用了CUDA，清空CUDA缓存
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                
            return True
            
        except Exception as e:
            logger.error(f"卸载分片 {shard_id} 失败: {str(e)}")
            return False
    
    def load_shard(self, shard_id: str, recursive: bool = True) -> Optional[Any]:
        """加载分片
        
        如果递归加载，会首先加载依赖的分片
        
        Args:
            shard_id: 分片ID
            recursive: 是否递归加载依赖
            
        Returns:
            Optional[Any]: 加载的分片数据
        """
        # 首先检查分片是否已在缓存中
        shard_data = self.cache_policy.get(shard_id)
        if shard_data is not None:
            return shard_data
        
        # 如果递归加载，首先加载依赖
        if recursive and shard_id in self.shard_dependencies:
            for dep_id in self.shard_dependencies[shard_id]:
                self.load_shard(dep_id, recursive=True)
        
        # 加载当前分片
        shard_data = self._load_shard_callback(shard_id)
        if shard_data is not None:
            # 获取分片元数据中的大小信息
            size_bytes = 0
            metadata = self.metadata_manager.get_shard_metadata(shard_id)
            if metadata:
                size_bytes = metadata.size_bytes
            
            # 将分片添加到缓存
            self.cache_policy.add(shard_id, shard_data, size=size_bytes)
            
            return shard_data
        
        return None
    
    def get_loading_sequence(self, target_shard_ids: List[str] = None) -> List[str]:
        """获取加载序列
        
        根据依赖关系计算最优的分片加载顺序
        
        Args:
            target_shard_ids: 目标分片ID列表，如果为None则计算所有分片
            
        Returns:
            List[str]: 分片加载顺序
        """
        if target_shard_ids is None:
            # 如果没有指定目标分片，使用所有分片
            target_shard_ids = list(self.shard_dependencies.keys())
        
        # 使用拓扑排序计算加载顺序
        visited = set()
        temp_visited = set()  # 用于检测循环依赖
        result = []
        
        def visit(node):
            if node in temp_visited:
                # 检测到循环依赖
                logger.warning(f"分片依赖中存在循环: {node}")
                return
            
            if node in visited:
                return
            
            temp_visited.add(node)
            
            # 首先遍历所有依赖
            if node in self.shard_dependencies:
                for dep in self.shard_dependencies[node]:
                    visit(dep)
            
            temp_visited.remove(node)
            visited.add(node)
            result.append(node)
        
        # 对每个目标分片执行DFS
        for shard_id in target_shard_ids:
            if shard_id not in visited:
                visit(shard_id)
        
        return result

    def prefetch_shards(self, shard_ids: List[str]) -> int:
        """预加载分片
        
        按照依赖顺序预加载指定分片
        
        Args:
            shard_ids: 要预加载的分片ID列表
            
        Returns:
            int: 成功预加载的分片数量
        """
        # 计算加载顺序
        loading_sequence = self.get_loading_sequence(shard_ids)
        
        # 根据顺序加载分片
        loaded_count = 0
        for shard_id in loading_sequence:
            # 检查缓存中是否已存在
            if self.cache_policy.contains(shard_id):
                continue
                
            # 加载分片
            shard_data = self.load_shard(shard_id, recursive=False)
            if shard_data is not None:
                loaded_count += 1
        
        return loaded_count
    
    def get_layer_mapping(self) -> Dict[str, str]:
        """获取层到分片的映射
        
        Returns:
            Dict[str, str]: 层名称到分片ID的映射
        """
        layer_to_shard = {}
        
        # 从元数据中提取层映射
        shard_metadatas = self.metadata_manager.get_all_shard_metadata()
        for shard_id, metadata in shard_metadatas.items():
            for layer_name in metadata.layers:
                layer_to_shard[layer_name] = shard_id
        
        return layer_to_shard
    
    def get_shard_for_layer(self, layer_name: str) -> Optional[str]:
        """获取包含指定层的分片ID
        
        Args:
            layer_name: 层名称
            
        Returns:
            Optional[str]: 分片ID，如果不存在返回None
        """
        # 构建层到分片的映射
        layer_mapping = self.get_layer_mapping()
        
        # 查找指定层
        if layer_name in layer_mapping:
            return layer_mapping[layer_name]
        
        # 支持模糊匹配
        for mapped_layer, shard_id in layer_mapping.items():
            if layer_name in mapped_layer:
                return shard_id
        
        return None
    
    def load_layers(self, layer_names: List[str]) -> Dict[str, Any]:
        """加载包含指定层的分片
        
        Args:
            layer_names: 层名称列表
            
        Returns:
            Dict[str, Any]: 层名称到加载数据的映射
        """
        # 获取层到分片的映射
        layer_mapping = {}
        for layer_name in layer_names:
            shard_id = self.get_shard_for_layer(layer_name)
            if shard_id:
                layer_mapping[layer_name] = shard_id
            else:
                logger.warning(f"未找到包含层 {layer_name} 的分片")
        
        # 加载所有需要的分片
        shard_data_cache = {}
        for layer_name, shard_id in layer_mapping.items():
            if shard_id not in shard_data_cache:
                shard_data = self.load_shard(shard_id)
                if shard_data is not None:
                    shard_data_cache[shard_id] = shard_data
        
        # 从分片中提取层数据
        layer_data = {}
        for layer_name, shard_id in layer_mapping.items():
            if shard_id in shard_data_cache:
                # 假设分片数据是一个字典，其中包含各层数据
                # 实际实现可能需要根据具体的数据结构进行调整
                if isinstance(shard_data_cache[shard_id], dict) and layer_name in shard_data_cache[shard_id]:
                    layer_data[layer_name] = shard_data_cache[shard_id][layer_name]
                else:
                    logger.warning(f"分片 {shard_id} 中未找到层 {layer_name} 的数据")
            
        return layer_data
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息
        
        Returns:
            Dict[str, Any]: 缓存统计信息
        """
        # 获取当前缓存策略的名称
        strategy_name = self.strategy_manager.get_current_strategy_name()
        
        # 基本统计信息
        stats = {
            "strategy": strategy_name,
            "max_shards": self.max_shards_in_memory,
            "cached_shards": len(self.cache_policy.get_keys()),
            "policy_stats": self.cache_policy.get_stats()
        }
        
        return stats
    
    def resize_cache(self, new_size: int) -> None:
        """调整缓存大小
        
        Args:
            new_size: 新的最大缓存分片数
        """
        self.max_shards_in_memory = new_size
        self.cache_policy.resize(new_size)
        logger.info(f"缓存大小已调整为 {new_size} 个分片")
    
    def clear_cache(self) -> bool:
        """清空缓存
        
        Returns:
            bool: 是否成功清空
        """
        self.cache_policy.clear()
        return True
    
    def switch_cache_strategy(self, strategy_name: str) -> bool:
        """切换缓存策略
        
        Args:
            strategy_name: 策略名称
            
        Returns:
            bool: 是否成功切换
        """
        # 获取当前缓存内容
        cached_items = {}
        for key in self.cache_policy.get_keys():
            cached_items[key] = self.cache_policy.get(key)
        
        # 清空当前缓存
        self.cache_policy.clear()
        
        # 切换到新策略
        success = self.strategy_manager.switch_strategy(strategy_name)
        if not success:
            logger.error(f"切换到策略 {strategy_name} 失败")
            return False
        
        # 获取新策略实例
        self.cache_policy = self.strategy_manager.get_policy()
        
        # 将缓存内容转移到新策略
        for key, value in cached_items.items():
            size_bytes = 0
            metadata = self.metadata_manager.get_shard_metadata(key)
            if metadata:
                size_bytes = metadata.size_bytes
            
            self.cache_policy.add(key, value, size=size_bytes)
        
        logger.info(f"已切换缓存策略到: {strategy_name}")
        return True
    
    def get_available_strategies(self) -> List[str]:
        """获取可用的缓存策略列表
        
        Returns:
            List[str]: 策略名称列表
        """
        return list(self.strategy_manager.get_all_strategies().keys())
    
    def _warm_up_cache(self) -> None:
        """预热缓存
        
        加载预热项目列表中的分片
        """
        # 获取应该预热的项目
        warm_up_items = self.strategy_manager.get_warm_up_items()
        if not warm_up_items:
            return
            
        logger.info(f"开始预热缓存，预热项目: {warm_up_items}")
        
        # 将层名称转换为分片ID
        shard_ids = []
        for layer_name in warm_up_items:
            shard_id = self.get_shard_for_layer(layer_name)
            if shard_id and shard_id not in shard_ids:
                shard_ids.append(shard_id)
        
        # 预加载分片
        if shard_ids:
            loaded_count = self.prefetch_shards(shard_ids)
            logger.info(f"缓存预热完成，已加载 {loaded_count} 个分片")
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出，清理资源"""
        self.clear_cache() 