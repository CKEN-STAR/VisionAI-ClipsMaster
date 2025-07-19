"""缓存策略模块

此模块定义了不同的分片缓存替换策略，用于决定当缓存满时应该移除哪些分片。
支持的策略包括：
1. LRU (最近最少使用) - 移除最长时间未访问的分片
2. LFU (最不经常使用) - 移除访问频率最低的分片
3. FIFO (先进先出) - 按加载顺序移除最早加载的分片
4. 权重感知 - 考虑分片大小和重要性的综合策略
5. 频率感知 - 考虑分片的热度和冷却时间的策略
"""

import time
import heapq
from abc import ABC, abstractmethod
from typing import Dict, List, Set, Any, Optional, Tuple, Generic, TypeVar, Callable
from enum import Enum
from collections import Counter, defaultdict, OrderedDict, deque
from loguru import logger


# 缓存项目的泛型类型
T = TypeVar('T')


class CachePolicyType(Enum):
    """缓存策略类型枚举"""
    LRU = "LRU"                  # 最近最少使用
    LFU = "LFU"                  # 最不经常使用 
    FIFO = "FIFO"                # 先进先出
    WEIGHT_AWARE = "Weight-Aware" # 权重感知
    FREQ_AWARE = "Freq-Aware"    # 频率感知


class CachePolicy(ABC, Generic[T]):
    """缓存策略基类
    
    定义了缓存策略的通用接口。所有具体策略实现必须继承此类。
    """
    
    def __init__(self, max_size: int = 5):
        """初始化缓存策略
        
        Args:
            max_size: 缓存的最大项目数
        """
        self.max_size = max_size
        self.name = "BasePolicy"
    
    @abstractmethod
    def add(self, key: str, value: T, **kwargs) -> None:
        """添加项目到缓存
        
        Args:
            key: 缓存项目的键
            value: 缓存项目的值
            **kwargs: 额外参数，可能包含size, weight等
        """
        pass
    
    @abstractmethod
    def get(self, key: str) -> Optional[T]:
        """获取缓存项目
        
        Args:
            key: 缓存项目的键
            
        Returns:
            Optional[T]: 缓存的项目，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    def remove(self, key: str) -> bool:
        """从缓存中移除项目
        
        Args:
            key: 要移除的项目键
            
        Returns:
            bool: 是否成功移除
        """
        pass
    
    @abstractmethod
    def evict(self) -> Optional[str]:
        """根据策略驱逐一个缓存项目
        
        Returns:
            Optional[str]: 被驱逐的项目键，如果缓存为空则返回None
        """
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """清空缓存"""
        pass
    
    @abstractmethod
    def contains(self, key: str) -> bool:
        """检查缓存是否包含指定键
        
        Args:
            key: 缓存项目的键
            
        Returns:
            bool: 是否包含指定键
        """
        pass
    
    def resize(self, new_max_size: int) -> None:
        """调整缓存大小
        
        Args:
            new_max_size: 新的最大缓存大小
        """
        self.max_size = new_max_size
    
    def get_size(self) -> int:
        """获取当前缓存中的项目数量
        
        Returns:
            int: 缓存项目数量
        """
        pass
    
    def is_full(self) -> bool:
        """检查缓存是否已满
        
        Returns:
            bool: 缓存是否已满
        """
        return self.get_size() >= self.max_size
    
    def get_keys(self) -> List[str]:
        """获取所有缓存键的列表
        
        Returns:
            List[str]: 缓存键列表
        """
        pass
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息
        
        Returns:
            Dict[str, Any]: 缓存统计信息
        """
        return {
            "name": self.name,
            "max_size": self.max_size,
            "current_size": self.get_size(),
            "keys": self.get_keys()
        }


class LRUPolicy(CachePolicy[T]):
    """最近最少使用缓存策略
    
    保留最近使用的项目，移除最长时间未使用的项目。
    """
    
    def __init__(self, max_size: int = 5):
        """初始化LRU缓存策略
        
        Args:
            max_size: 最大缓存项目数
        """
        super().__init__(max_size)
        self.name = "LRU"
        self.cache = OrderedDict()  # 有序字典用于跟踪使用顺序
    
    def add(self, key: str, value: T, **kwargs) -> None:
        """添加项目到缓存
        
        如果键已存在，更新值并刷新使用顺序
        
        Args:
            key: 缓存项目的键
            value: 缓存项目的值
            **kwargs: 额外参数（在LRU中未使用）
        """
        if key in self.cache:
            # 如果键已存在，删除旧记录
            del self.cache[key]
        
        # 添加到缓存，新项目会在最后（最近使用）
        self.cache[key] = value
    
    def get(self, key: str) -> Optional[T]:
        """获取缓存项目并刷新其使用顺序
        
        Args:
            key: 缓存项目的键
            
        Returns:
            Optional[T]: 缓存的项目，如果不存在则返回None
        """
        if key not in self.cache:
            return None
        
        # 获取值
        value = self.cache[key]
        
        # 刷新使用顺序
        del self.cache[key]
        self.cache[key] = value
        
        return value
    
    def remove(self, key: str) -> bool:
        """从缓存中移除项目
        
        Args:
            key: 要移除的项目键
            
        Returns:
            bool: 是否成功移除
        """
        if key in self.cache:
            del self.cache[key]
            return True
        return False
    
    def evict(self) -> Optional[str]:
        """驱逐最久未使用的项目
        
        Returns:
            Optional[str]: 被驱逐的项目键，如果缓存为空则返回None
        """
        if not self.cache:
            return None
        
        # 移除第一个项目（最久未使用）
        key, _ = self.cache.popitem(last=False)
        return key
    
    def clear(self) -> None:
        """清空缓存"""
        self.cache.clear()
    
    def contains(self, key: str) -> bool:
        """检查缓存是否包含指定键
        
        Args:
            key: 缓存项目的键
            
        Returns:
            bool: 是否包含指定键
        """
        return key in self.cache
    
    def get_size(self) -> int:
        """获取当前缓存中的项目数量
        
        Returns:
            int: 缓存项目数量
        """
        return len(self.cache)
    
    def get_keys(self) -> List[str]:
        """获取所有缓存键的列表
        
        Returns:
            List[str]: 缓存键列表
        """
        return list(self.cache.keys())


class LFUPolicy(CachePolicy[T]):
    """最不经常使用缓存策略
    
    保留使用频率最高的项目，移除使用频率最低的项目。
    """
    
    def __init__(self, max_size: int = 5):
        """初始化LFU缓存策略
        
        Args:
            max_size: 最大缓存项目数
        """
        super().__init__(max_size)
        self.name = "LFU"
        self.cache = {}  # 键 -> 值
        self.freq = Counter()  # 键 -> 频率
        self.last_access = {}  # 键 -> 最后访问时间（用于相同频率时的比较）
    
    def add(self, key: str, value: T, **kwargs) -> None:
        """添加项目到缓存
        
        Args:
            key: 缓存项目的键
            value: 缓存项目的值
            **kwargs: 额外参数（在LFU中未使用）
        """
        self.cache[key] = value
        # 新项目初始频率为1
        self.freq[key] = 1
        # 记录当前时间作为访问时间
        self.last_access[key] = time.time()
    
    def get(self, key: str) -> Optional[T]:
        """获取缓存项目并增加其使用频率
        
        Args:
            key: 缓存项目的键
            
        Returns:
            Optional[T]: 缓存的项目，如果不存在则返回None
        """
        if key not in self.cache:
            return None
        
        # 增加使用频率
        self.freq[key] += 1
        # 更新访问时间
        self.last_access[key] = time.time()
        
        return self.cache[key]
    
    def remove(self, key: str) -> bool:
        """从缓存中移除项目
        
        Args:
            key: 要移除的项目键
            
        Returns:
            bool: 是否成功移除
        """
        if key in self.cache:
            del self.cache[key]
            del self.freq[key]
            del self.last_access[key]
            return True
        return False
    
    def evict(self) -> Optional[str]:
        """驱逐使用频率最低的项目
        
        当多个项目频率相同时，驱逐最久未访问的项目
        
        Returns:
            Optional[str]: 被驱逐的项目键，如果缓存为空则返回None
        """
        if not self.cache:
            return None
        
        # 找到频率最低的项目
        min_freq = min(self.freq.values())
        min_freq_keys = [k for k, v in self.freq.items() if v == min_freq]
        
        if len(min_freq_keys) == 1:
            # 只有一个最低频率项目
            key_to_evict = min_freq_keys[0]
        else:
            # 有多个最低频率项目，选择最久未访问的
            key_to_evict = min(min_freq_keys, key=lambda k: self.last_access.get(k, 0))
        
        # 从缓存中移除
        self.remove(key_to_evict)
        return key_to_evict
    
    def clear(self) -> None:
        """清空缓存"""
        self.cache.clear()
        self.freq.clear()
        self.last_access.clear()
    
    def contains(self, key: str) -> bool:
        """检查缓存是否包含指定键
        
        Args:
            key: 缓存项目的键
            
        Returns:
            bool: 是否包含指定键
        """
        return key in self.cache
    
    def get_size(self) -> int:
        """获取当前缓存中的项目数量
        
        Returns:
            int: 缓存项目数量
        """
        return len(self.cache)
    
    def get_keys(self) -> List[str]:
        """获取所有缓存键的列表
        
        Returns:
            List[str]: 缓存键列表
        """
        return list(self.cache.keys())


class FIFOPolicy(CachePolicy[T]):
    """先进先出缓存策略
    
    按加载顺序移除项目，最早加载的先移除。
    """
    
    def __init__(self, max_size: int = 5):
        """初始化FIFO缓存策略
        
        Args:
            max_size: 最大缓存项目数
        """
        super().__init__(max_size)
        self.name = "FIFO"
        self.cache = {}  # 键 -> 值
        self.queue = deque()  # 保存加载顺序
    
    def add(self, key: str, value: T, **kwargs) -> None:
        """添加项目到缓存
        
        Args:
            key: 缓存项目的键
            value: 缓存项目的值
            **kwargs: 额外参数（在FIFO中未使用）
        """
        # 如果已存在，先移除旧记录
        if key in self.cache:
            self.queue.remove(key)
        
        # 添加到缓存
        self.cache[key] = value
        self.queue.append(key)  # 添加到队列末尾
    
    def get(self, key: str) -> Optional[T]:
        """获取缓存项目
        
        Args:
            key: 缓存项目的键
            
        Returns:
            Optional[T]: 缓存的项目，如果不存在则返回None
        """
        return self.cache.get(key)
    
    def remove(self, key: str) -> bool:
        """从缓存中移除项目
        
        Args:
            key: 要移除的项目键
            
        Returns:
            bool: 是否成功移除
        """
        if key in self.cache:
            del self.cache[key]
            try:
                self.queue.remove(key)
            except ValueError:
                # 如果队列中找不到键，可能是由于某些错误
                pass
            return True
        return False
    
    def evict(self) -> Optional[str]:
        """驱逐最早加入的项目
        
        Returns:
            Optional[str]: 被驱逐的项目键，如果缓存为空则返回None
        """
        if not self.queue:
            return None
        
        # 从队列前面取出（最早加入的）
        key_to_evict = self.queue.popleft()
        # 从缓存中移除
        if key_to_evict in self.cache:
            del self.cache[key_to_evict]
        
        return key_to_evict
    
    def clear(self) -> None:
        """清空缓存"""
        self.cache.clear()
        self.queue.clear()
    
    def contains(self, key: str) -> bool:
        """检查缓存是否包含指定键
        
        Args:
            key: 缓存项目的键
            
        Returns:
            bool: 是否包含指定键
        """
        return key in self.cache
    
    def get_size(self) -> int:
        """获取当前缓存中的项目数量
        
        Returns:
            int: 缓存项目数量
        """
        return len(self.cache)
    
    def get_keys(self) -> List[str]:
        """获取所有缓存键的列表
        
        Returns:
            List[str]: 缓存键列表
        """
        return list(self.cache.keys())


class WeightAwarePolicy(CachePolicy[T]):
    """权重感知缓存策略
    
    考虑项目大小和用户定义的重要性权重，优先保留重要且小的项目。
    """
    
    def __init__(self, max_size: int = 5):
        """初始化权重感知缓存策略
        
        Args:
            max_size: 最大缓存项目数
        """
        super().__init__(max_size)
        self.name = "Weight-Aware"
        self.cache = {}  # 键 -> 值
        self.weights = {}  # 键 -> 权重
        self.sizes = {}  # 键 -> 大小
        self.last_access = {}  # 键 -> 最后访问时间
    
    def add(self, key: str, value: T, **kwargs) -> None:
        """添加项目到缓存
        
        Args:
            key: 缓存项目的键
            value: 缓存项目的值
            **kwargs: 额外参数，包括:
                - weight: 项目的重要性权重
                - size: 项目的大小
        """
        # 从kwargs获取权重和大小
        weight = kwargs.get('weight', 1.0)
        size = kwargs.get('size', 1.0)
        
        # 添加到缓存
        self.cache[key] = value
        self.weights[key] = weight
        self.sizes[key] = size
        self.last_access[key] = time.time()
    
    def get(self, key: str) -> Optional[T]:
        """获取缓存项目
        
        Args:
            key: 缓存项目的键
            
        Returns:
            Optional[T]: 缓存的项目，如果不存在则返回None
        """
        if key not in self.cache:
            return None
        
        # 更新访问时间
        self.last_access[key] = time.time()
        return self.cache[key]
    
    def remove(self, key: str) -> bool:
        """从缓存中移除项目
        
        Args:
            key: 要移除的项目键
            
        Returns:
            bool: 是否成功移除
        """
        if key in self.cache:
            del self.cache[key]
            del self.weights[key]
            del self.sizes[key]
            del self.last_access[key]
            return True
        return False
    
    def evict(self) -> Optional[str]:
        """驱逐最低评分的项目
        
        评分 = 权重 / (大小 * 时间因子)
        时间因子是基于上次访问时间的，越久远时间因子越大
        
        Returns:
            Optional[str]: 被驱逐的项目键，如果缓存为空则返回None
        """
        if not self.cache:
            return None
        
        now = time.time()
        # 计算每个项目的评分
        scores = {}
        for key in self.cache:
            # 计算时间因子：经过的时间越长，因子越大
            time_elapsed = now - self.last_access[key]
            time_factor = min(1.0 + time_elapsed / 3600, 10.0)  # 限制在1-10范围内
            
            # 评分 = 权重 / (大小 * 时间因子)
            # 大的项目评分低（更可能被驱逐）
            # 重要的项目评分高（不太可能被驱逐）
            # 长时间未访问的项目评分低（更可能被驱逐）
            scores[key] = self.weights[key] / (max(self.sizes[key], 0.1) * time_factor)
        
        # 找到评分最低的项目
        key_to_evict = min(scores, key=scores.get)
        
        # 从缓存中移除
        self.remove(key_to_evict)
        return key_to_evict
    
    def clear(self) -> None:
        """清空缓存"""
        self.cache.clear()
        self.weights.clear()
        self.sizes.clear()
        self.last_access.clear()
    
    def contains(self, key: str) -> bool:
        """检查缓存是否包含指定键
        
        Args:
            key: 缓存项目的键
            
        Returns:
            bool: 是否包含指定键
        """
        return key in self.cache
    
    def get_size(self) -> int:
        """获取当前缓存中的项目数量
        
        Returns:
            int: 缓存项目数量
        """
        return len(self.cache)
    
    def get_keys(self) -> List[str]:
        """获取所有缓存键的列表
        
        Returns:
            List[str]: 缓存键列表
        """
        return list(self.cache.keys())


class FreqAwarePolicy(CachePolicy[T]):
    """频率感知缓存策略
    
    结合访问频率和冷却时间，对热点和冷数据进行智能管理。
    """
    
    def __init__(self, max_size: int = 5, hot_threshold: int = 10, cold_time: int = 300):
        """初始化频率感知缓存策略
        
        Args:
            max_size: 最大缓存项目数
            hot_threshold: 热点项目的阈值（访问次数）
            cold_time: 冷却时间（秒）
        """
        super().__init__(max_size)
        self.name = "Freq-Aware"
        self.hot_threshold = hot_threshold
        self.cold_time = cold_time
        
        self.cache = {}  # 键 -> 值
        self.access_count = Counter()  # 键 -> 访问次数
        self.last_access = {}  # 键 -> 最后访问时间
        self.first_access = {}  # 键 -> 首次访问时间
    
    def add(self, key: str, value: T, **kwargs) -> None:
        """添加项目到缓存
        
        Args:
            key: 缓存项目的键
            value: 缓存项目的值
            **kwargs: 额外参数（未使用）
        """
        now = time.time()
        self.cache[key] = value
        # 如果是新项目，初始化访问统计
        if key not in self.access_count:
            self.access_count[key] = 1
            self.first_access[key] = now
        else:
            self.access_count[key] += 1
        
        self.last_access[key] = now
    
    def get(self, key: str) -> Optional[T]:
        """获取缓存项目
        
        Args:
            key: 缓存项目的键
            
        Returns:
            Optional[T]: 缓存的项目，如果不存在则返回None
        """
        if key not in self.cache:
            return None
        
        now = time.time()
        self.access_count[key] += 1
        self.last_access[key] = now
        
        return self.cache[key]
    
    def remove(self, key: str) -> bool:
        """从缓存中移除项目
        
        Args:
            key: 要移除的项目键
            
        Returns:
            bool: 是否成功移除
        """
        if key in self.cache:
            del self.cache[key]
            # 保留访问统计，以便将来可能重新加载时使用
            return True
        return False
    
    def evict(self) -> Optional[str]:
        """驱逐策略：
        1. 优先驱逐冷却项目（长时间未访问且非热点）
        2. 其次驱逐频率低的项目
        
        Returns:
            Optional[str]: 被驱逐的项目键，如果缓存为空则返回None
        """
        if not self.cache:
            return None
        
        now = time.time()
        
        # 找出冷却的项目（长时间未访问且不是热点）
        cold_keys = []
        for key in self.cache:
            time_since_last_access = now - self.last_access[key]
            is_hot = self.access_count[key] >= self.hot_threshold
            if time_since_last_access > self.cold_time and not is_hot:
                cold_keys.append(key)
        
        if cold_keys:
            # 如果有冷却项目，选择访问频率最低的一个
            key_to_evict = min(cold_keys, key=lambda k: self.access_count[k])
        else:
            # 否则，从所有项目中选择最少访问的
            key_to_evict = min(self.cache.keys(), key=lambda k: self.access_count[k])
        
        # 从缓存中移除
        self.remove(key_to_evict)
        return key_to_evict
    
    def clear(self) -> None:
        """清空缓存"""
        self.cache.clear()
        # 不清除访问统计，以便将来可能重新加载时使用
    
    def contains(self, key: str) -> bool:
        """检查缓存是否包含指定键
        
        Args:
            key: 缓存项目的键
            
        Returns:
            bool: 是否包含指定键
        """
        return key in self.cache
    
    def get_size(self) -> int:
        """获取当前缓存中的项目数量
        
        Returns:
            int: 缓存项目数量
        """
        return len(self.cache)
    
    def get_keys(self) -> List[str]:
        """获取所有缓存键的列表
        
        Returns:
            List[str]: 缓存键列表
        """
        return list(self.cache.keys())
    
    def get_hot_keys(self) -> List[str]:
        """获取热点项目键列表
        
        Returns:
            List[str]: 热点项目键列表
        """
        return [k for k in self.cache if self.access_count[k] >= self.hot_threshold]
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息
        
        Returns:
            Dict[str, Any]: 缓存统计信息
        """
        stats = super().get_stats()
        stats.update({
            "hot_threshold": self.hot_threshold,
            "cold_time": self.cold_time,
            "hot_keys": self.get_hot_keys(),
            "access_counts": dict(self.access_count)
        })
        return stats


class CachePolicyFactory:
    """缓存策略工厂类
    
    创建和管理不同类型的缓存策略实例。
    """
    
    @staticmethod
    def create_policy(policy_type: str, max_size: int = 5, **kwargs) -> CachePolicy:
        """创建缓存策略实例
        
        Args:
            policy_type: 策略类型名称
            max_size: 最大缓存大小
            **kwargs: 其他策略特定参数
            
        Returns:
            CachePolicy: 缓存策略实例
            
        Raises:
            ValueError: 如果策略类型无效
        """
        policy_type = policy_type.upper()
        
        if policy_type == CachePolicyType.LRU.name:
            return LRUPolicy(max_size)
        
        elif policy_type == CachePolicyType.LFU.name:
            return LFUPolicy(max_size)
        
        elif policy_type == CachePolicyType.FIFO.name:
            return FIFOPolicy(max_size)
        
        elif policy_type == CachePolicyType.WEIGHT_AWARE.name or policy_type == "WEIGHT_AWARE":
            return WeightAwarePolicy(max_size)
        
        elif policy_type == CachePolicyType.FREQ_AWARE.name or policy_type == "FREQ_AWARE":
            hot_threshold = kwargs.get('hot_threshold', 10)
            cold_time = kwargs.get('cold_time', 300)
            return FreqAwarePolicy(max_size, hot_threshold, cold_time)
        
        else:
            raise ValueError(f"未知的缓存策略类型: {policy_type}")
    
    @staticmethod
    def get_available_policies() -> List[str]:
        """获取所有可用的策略类型
        
        Returns:
            List[str]: 可用策略类型列表
        """
        return [policy.name for policy in CachePolicyType] 