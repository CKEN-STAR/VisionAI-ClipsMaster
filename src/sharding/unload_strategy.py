"""分片卸载策略模块

此模块提供智能分片卸载策略，用于在内存压力大时选择最适合卸载的分片。
卸载策略基于以下优先级:
1. 无依赖关系的分片（不被其他已加载分片依赖）
2. 最近最少使用的分片（LRU原则）
3. 内存占用最大的分片
"""

import time
from enum import Enum
from typing import Dict, List, Set, Any, Optional, Tuple, Union, Callable
from loguru import logger

from src.sharding.cache_manager import ShardManager


class UnloadPriority(Enum):
    """卸载优先级枚举"""
    NO_DEPENDENCIES = 1    # 优先级1: 无依赖关系的分片
    LEAST_RECENTLY_USED = 2  # 优先级2: 最近最少使用的分片
    LARGEST_MEMORY = 3     # 优先级3: 内存占用最大的分片
    HYBRID = 4             # 混合策略


class ShardUnloadStrategy:
    """分片卸载策略
    
    根据各种因素确定最适合卸载的分片，以优化内存使用。
    """
    
    def __init__(
        self, 
        shard_manager: ShardManager,
        priority: UnloadPriority = UnloadPriority.HYBRID,
        memory_threshold: float = 80.0,  # 内存使用率阈值（百分比）
        min_cache_size: int = 2          # 最小缓存大小
    ):
        """初始化分片卸载策略
        
        Args:
            shard_manager: 分片管理器实例
            priority: 卸载优先级策略
            memory_threshold: 触发卸载的内存使用率阈值
            min_cache_size: 缓存中保留的最小分片数量
        """
        self.shard_manager = shard_manager
        self.priority = priority
        self.memory_threshold = memory_threshold
        self.min_cache_size = min_cache_size
        
        # 分片访问时间记录
        self.last_access_time = {}
        
        # 分片内存占用记录 (shard_id -> bytes)
        self.memory_usage = {}
        
        # 反向依赖图 (被哪些分片所依赖)
        self.reverse_dependency_graph = {}
        
        # 初始化反向依赖图
        self._build_reverse_dependency_graph()
        
        logger.info(f"分片卸载策略初始化完成，优先级: {priority.name}")
    
    def _build_reverse_dependency_graph(self):
        """构建反向依赖图
        
        记录每个分片被哪些分片所依赖
        """
        self.reverse_dependency_graph = {}
        
        if not self.shard_manager.metadata:
            return
            
        # 初始化每个分片的反向依赖列表
        for shard_id in self.shard_manager.metadata.get_shards().keys():
            self.reverse_dependency_graph[shard_id] = set()
        
        # 构建反向依赖关系
        for shard_id, shard_info in self.shard_manager.metadata.get_shards().items():
            dependencies = shard_info.get("depends_on", [])
            
            # 更新每个依赖分片的反向依赖列表
            for dep_id in dependencies:
                if dep_id in self.reverse_dependency_graph:
                    self.reverse_dependency_graph[dep_id].add(shard_id)
    
    def record_access(self, shard_id: str):
        """记录分片访问时间
        
        Args:
            shard_id: 分片ID
        """
        self.last_access_time[shard_id] = time.time()
    
    def record_memory_usage(self, shard_id: str, size_bytes: int):
        """记录分片内存占用
        
        Args:
            shard_id: 分片ID
            size_bytes: 内存占用（字节）
        """
        self.memory_usage[shard_id] = size_bytes
    
    def get_shards_to_unload(self, count: int = 1) -> List[str]:
        """获取应该卸载的分片列表
        
        Args:
            count: 需要卸载的分片数量
            
        Returns:
            List[str]: 应该卸载的分片ID列表
        """
        # 如果缓存中的分片数量小于等于最小缓存大小，不卸载
        cached_shards = self.shard_manager.shard_cache.get_cached_shards()
        if len(cached_shards) <= self.min_cache_size:
            logger.debug(f"缓存分片数量 ({len(cached_shards)}) 小于等于最小缓存大小 ({self.min_cache_size})，不卸载")
            return []
        
        # 根据优先级获取候选分片
        if self.priority == UnloadPriority.NO_DEPENDENCIES:
            candidates = self._get_no_dependency_shards(cached_shards)
        elif self.priority == UnloadPriority.LEAST_RECENTLY_USED:
            candidates = self._get_lru_shards(cached_shards)
        elif self.priority == UnloadPriority.LARGEST_MEMORY:
            candidates = self._get_largest_memory_shards(cached_shards)
        else:  # HYBRID
            # 混合策略: 首先尝试无依赖分片，然后是LRU，最后是内存占用最大的
            candidates = self._get_hybrid_candidates(cached_shards)
            
        # 返回需要卸载的分片
        return candidates[:count]
    
    def _get_no_dependency_shards(self, cached_shards: List[str]) -> List[str]:
        """获取无依赖关系的分片
        
        返回那些不被其他已加载分片依赖的分片
        
        Args:
            cached_shards: 当前已缓存的分片ID列表
            
        Returns:
            List[str]: 无依赖的分片ID列表，按最近最少使用排序
        """
        # 找出没有被其他已加载分片依赖的分片
        no_dependency_shards = []
        
        for shard_id in cached_shards:
            # 获取依赖此分片的其他分片
            dependent_shards = self.reverse_dependency_graph.get(shard_id, set())
            
            # 检查依赖此分片的分片是否有任何一个在缓存中
            has_loaded_dependents = any(
                dep_id in cached_shards for dep_id in dependent_shards
            )
            
            # 如果没有已加载的分片依赖此分片，则可以卸载
            if not has_loaded_dependents:
                no_dependency_shards.append(shard_id)
        
        # 按最近最少使用排序
        return self._sort_by_last_access(no_dependency_shards)
    
    def _get_lru_shards(self, cached_shards: List[str]) -> List[str]:
        """获取最近最少使用的分片
        
        Args:
            cached_shards: 当前已缓存的分片ID列表
            
        Returns:
            List[str]: 按访问时间排序的分片ID列表（最久未访问的在前）
        """
        return self._sort_by_last_access(cached_shards)
    
    def _get_largest_memory_shards(self, cached_shards: List[str]) -> List[str]:
        """获取内存占用最大的分片
        
        Args:
            cached_shards: 当前已缓存的分片ID列表
            
        Returns:
            List[str]: 按内存占用排序的分片ID列表（占用最大的在前）
        """
        # 过滤出有内存占用记录的分片
        memory_recorded_shards = [
            shard_id for shard_id in cached_shards
            if shard_id in self.memory_usage
        ]
        
        # 按内存占用从大到小排序
        sorted_shards = sorted(
            memory_recorded_shards,
            key=lambda shard_id: self.memory_usage.get(shard_id, 0),
            reverse=True
        )
        
        # 将没有内存记录的分片添加到列表末尾
        for shard_id in cached_shards:
            if shard_id not in self.memory_usage and shard_id not in sorted_shards:
                sorted_shards.append(shard_id)
                
        return sorted_shards
    
    def _get_hybrid_candidates(self, cached_shards: List[str]) -> List[str]:
        """混合策略获取候选分片
        
        综合考虑依赖关系、使用时间和内存占用
        
        Args:
            cached_shards: 当前已缓存的分片ID列表
            
        Returns:
            List[str]: 候选分片ID列表
        """
        # 1. 首先尝试获取无依赖的分片
        no_dep_shards = self._get_no_dependency_shards(cached_shards)
        if no_dep_shards:
            return no_dep_shards
            
        # 2. 如果没有无依赖的分片，获取LRU分片
        lru_shards = self._get_lru_shards(cached_shards)
        
        # 3. 考虑内存占用因素，调整排序
        # 计算每个分片的综合得分: 0.7 * LRU排名 + 0.3 * 内存占用排名
        # 排名越小，得分越小，越优先卸载
        
        # 获取内存占用排名
        memory_shards = self._get_largest_memory_shards(cached_shards)
        
        # 计算综合得分并排序
        scored_shards = []
        for shard_id in cached_shards:
            lru_rank = lru_shards.index(shard_id) if shard_id in lru_shards else len(cached_shards)
            memory_rank = memory_shards.index(shard_id) if shard_id in memory_shards else len(cached_shards)
            
            # 综合得分 (较小的排名得分较低，优先级较高)
            score = 0.7 * lru_rank + 0.3 * memory_rank
            scored_shards.append((shard_id, score))
            
        # 按得分排序（得分低的优先）
        sorted_shards = [shard_id for shard_id, _ in sorted(scored_shards, key=lambda x: x[1])]
        return sorted_shards
    
    def _sort_by_last_access(self, shard_ids: List[str]) -> List[str]:
        """按最后访问时间排序分片
        
        Args:
            shard_ids: 分片ID列表
            
        Returns:
            List[str]: 按访问时间排序的分片ID列表（最久未访问的在前）
        """
        # 按最后访问时间排序（从早到晚）
        return sorted(
            shard_ids,
            key=lambda shard_id: self.last_access_time.get(shard_id, 0)
        )
    
    def trigger_unload_if_needed(self) -> int:
        """根据当前内存状况触发分片卸载
        
        Returns:
            int: 卸载的分片数量
        """
        import psutil

# 内存使用警告阈值（百分比）
MEMORY_WARNING_THRESHOLD = 80

        
        # 获取当前内存使用率
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        
        # 如果内存使用率超过阈值，触发卸载
        if memory_percent > self.memory_threshold:
            logger.warning(f"内存使用率 ({memory_percent:.1f}%) 超过阈值 ({self.memory_threshold:.1f}%)，触发分片卸载")
            
            # 计算需要卸载的分片数量（根据内存压力调整）
            pressure = (memory_percent - self.memory_threshold) / (100 - self.memory_threshold)
            cached_count = len(self.shard_manager.shard_cache.get_cached_shards())
            
            # 至少卸载1个，最多卸载缓存中一半的分片
            unload_count = max(1, min(
                int(cached_count * pressure * 0.5),  # 最多卸载一半
                cached_count - self.min_cache_size    # 至少保留最小缓存数量
            ))
            
            # 获取要卸载的分片
            shards_to_unload = self.get_shards_to_unload(unload_count)
            
            # 卸载分片
            unloaded_count = 0
            for shard_id in shards_to_unload:
                success = self.shard_manager.shard_cache.remove(shard_id)
                if success:
                    unloaded_count += 1
                    logger.info(f"已卸载分片: {shard_id}")
                else:
                    logger.warning(f"分片卸载失败: {shard_id}")
            
            return unloaded_count
        
        return 0
    
    def update_shard_manager_callbacks(self):
        """更新分片管理器的回调函数
        
        将卸载策略集成到分片管理器中
        """
        # 保存原始的加载回调函数
        original_load_callback = self.shard_manager.shard_cache.load_callback
        
        # 创建新的加载回调，记录访问时间
        def enhanced_load_callback(shard_id: str) -> Any:
            result = original_load_callback(shard_id)
            if result is not None:
                # 记录访问时间
                self.record_access(shard_id)
                
                # 估计内存占用（如果是PyTorch张量）
                if hasattr(result, 'element_size') and hasattr(result, 'nelement'):
                    try:
                        size_bytes = result.element_size() * result.nelement()
                        self.record_memory_usage(shard_id, size_bytes)
                    except (AttributeError, RuntimeError):
                        pass
                # 对于字典类型（模拟数据）
                elif isinstance(result, dict) and 'size_bytes' in result:
                    self.record_memory_usage(shard_id, result['size_bytes'])
            return result
        
        # 更新分片缓存的加载回调
        self.shard_manager.shard_cache.load_callback = enhanced_load_callback
        
        logger.info("已更新分片管理器回调函数，集成卸载策略")


def create_unload_strategy(
    shard_manager: ShardManager,
    priority: str = "hybrid",
    memory_threshold: float = 80.0,
    min_cache_size: int = 2
) -> ShardUnloadStrategy:
    """创建分片卸载策略
    
    Args:
        shard_manager: 分片管理器实例
        priority: 优先级策略 ("no_dependencies", "lru", "memory", "hybrid")
        memory_threshold: 触发卸载的内存使用率阈值
        min_cache_size: 缓存中保留的最小分片数量
        
    Returns:
        ShardUnloadStrategy: 分片卸载策略实例
    """
    # 转换优先级字符串为枚举
    priority_map = {
        "no_dependencies": UnloadPriority.NO_DEPENDENCIES,
        "lru": UnloadPriority.LEAST_RECENTLY_USED,
        "memory": UnloadPriority.LARGEST_MEMORY,
        "hybrid": UnloadPriority.HYBRID
    }
    
    priority_enum = priority_map.get(priority.lower(), UnloadPriority.HYBRID)
    
    # 创建卸载策略
    strategy = ShardUnloadStrategy(
        shard_manager=shard_manager,
        priority=priority_enum,
        memory_threshold=memory_threshold,
        min_cache_size=min_cache_size
    )
    
    # 集成到分片管理器
    strategy.update_shard_manager_callbacks()
    
    return strategy 