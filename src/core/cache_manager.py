"""智能缓存管理模块

此模块实现了高效的缓存管理机制，包括：
1. LRU缓存策略
2. 内存使用监控
3. 智能预加载
4. 缓存持久化
5. 分级缓存系统
"""

import os
import json
import time
import pickle
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from collections import OrderedDict
from loguru import logger

from src.utils.memory_manager import MemoryManager
from src.utils.device_manager import HybridDevice

class CacheEntry:
    """缓存条目类"""
    
    def __init__(self, key: str, value: Any, size: int = 0):
        self.key = key
        self.value = value
        self.size = size
        self.access_count = 0
        self.last_access = time.time()
        self.creation_time = time.time()
    
    def update_access(self):
        """更新访问信息"""
        self.access_count += 1
        self.last_access = time.time()

class CacheManager:
    """智能缓存管理器"""
    
    def __init__(self,
                 max_memory_size: int = 8 * 1024 * 1024 * 1024,  # 8GB
                 max_disk_size: int = 20 * 1024 * 1024 * 1024,   # 20GB
                 cache_dir: str = "cache",
                 enable_persistent: bool = True):
        """初始化缓存管理器
        
        Args:
            max_memory_size: 最大内存缓存大小（字节）
            max_disk_size: 最大磁盘缓存大小（字节）
            cache_dir: 缓存目录
            enable_persistent: 是否启用持久化
        """
        self.max_memory_size = max_memory_size
        self.max_disk_size = max_disk_size
        self.cache_dir = Path(cache_dir)
        self.enable_persistent = enable_persistent
        
        # 创建缓存目录
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化缓存
        self.memory_cache = OrderedDict()  # 内存缓存
        self.disk_cache = OrderedDict()    # 磁盘缓存索引
        
        # 当前缓存大小
        self.current_memory_size = 0
        self.current_disk_size = 0
        
        # 缓存统计
        self.stats = {
            "memory_hits": 0,
            "disk_hits": 0,
            "misses": 0,
            "evictions": 0
        }
        
        # 工具类实例
        self.memory_manager = MemoryManager()
        self.device_manager = HybridDevice()
        
        # 加载持久化数据
        if enable_persistent:
            self._load_persistent_data()
        
        # 启动后台监控线程
        self._start_monitor()
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存项
        
        Args:
            key: 缓存键
            
        Returns:
            Optional[Any]: 缓存值，不存在则返回None
        """
        # 检查内存缓存
        if key in self.memory_cache:
            entry = self.memory_cache[key]
            entry.update_access()
            self.stats["memory_hits"] += 1
            
            # 移动到最新位置
            self.memory_cache.move_to_end(key)
            return entry.value
        
        # 检查磁盘缓存
        if key in self.disk_cache:
            self.stats["disk_hits"] += 1
            
            # 从磁盘加载
            entry = self._load_from_disk(key)
            if entry:
                # 尝试移动到内存缓存
                self._try_promote_to_memory(key, entry)
                return entry.value
        
        self.stats["misses"] += 1
        return None
    
    def put(self, key: str, value: Any, size: Optional[int] = None):
        """存入缓存项
        
        Args:
            key: 缓存键
            value: 缓存值
            size: 项目大小（字节），None则自动计算
        """
        # 计算大小
        if size is None:
            size = self._estimate_size(value)
        
        # 创建缓存条目
        entry = CacheEntry(key, value, size)
        
        # 如果大小在允许范围内，优先放入内存缓存
        if size <= self.max_memory_size * 0.1:  # 单个项不超过内存缓存的10%
            self._put_to_memory(key, entry)
        else:
            # 否则放入磁盘缓存
            self._put_to_disk(key, entry)
    
    def _put_to_memory(self, key: str, entry: CacheEntry):
        """放入内存缓存"""
        # 确保有足够空间
        while self.current_memory_size + entry.size > self.max_memory_size:
            self._evict_from_memory()
        
        # 添加到内存缓存
        self.memory_cache[key] = entry
        self.current_memory_size += entry.size
        
        # 移动到最新位置
        self.memory_cache.move_to_end(key)
    
    def _put_to_disk(self, key: str, entry: CacheEntry):
        """放入磁盘缓存"""
        # 确保有足够空间
        while self.current_disk_size + entry.size > self.max_disk_size:
            self._evict_from_disk()
        
        # 保存到磁盘
        cache_path = self.cache_dir / f"{key}.cache"
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(entry, f)
            
            # 更新索引
            self.disk_cache[key] = {
                "path": str(cache_path),
                "size": entry.size,
                "last_access": entry.last_access
            }
            self.current_disk_size += entry.size
            
        except Exception as e:
            logger.error(f"写入磁盘缓存失败: {e}")
    
    def _evict_from_memory(self):
        """从内存缓存中驱逐"""
        if not self.memory_cache:
            return
        
        # 获取最早的项
        key, entry = next(iter(self.memory_cache.items()))
        
        # 如果启用了持久化，尝试移动到磁盘
        if self.enable_persistent:
            self._put_to_disk(key, entry)
        
        # 从内存中移除
        del self.memory_cache[key]
        self.current_memory_size -= entry.size
        self.stats["evictions"] += 1
    
    def _evict_from_disk(self):
        """从磁盘缓存中驱逐"""
        if not self.disk_cache:
            return
        
        # 获取最早的项
        key, info = next(iter(self.disk_cache.items()))
        
        # 删除文件
        try:
            os.remove(info["path"])
        except Exception as e:
            logger.warning(f"删除缓存文件失败: {e}")
        
        # 更新索引
        del self.disk_cache[key]
        self.current_disk_size -= info["size"]
        self.stats["evictions"] += 1
    
    def _load_from_disk(self, key: str) -> Optional[CacheEntry]:
        """从磁盘加载缓存项"""
        info = self.disk_cache.get(key)
        if not info:
            return None
        
        try:
            with open(info["path"], 'rb') as f:
                entry = pickle.load(f)
                entry.update_access()
                return entry
        except Exception as e:
            logger.error(f"读取磁盘缓存失败: {e}")
            return None
    
    def _try_promote_to_memory(self, key: str, entry: CacheEntry):
        """尝试将磁盘缓存项提升到内存"""
        if entry.size <= self.max_memory_size * 0.1:
            # 检查内存使用情况
            if self.memory_manager.check_system_memory(entry.size):
                self._put_to_memory(key, entry)
                # 从磁盘缓存中移除
                self._remove_from_disk(key)
    
    def _remove_from_disk(self, key: str):
        """从磁盘缓存中移除"""
        info = self.disk_cache.get(key)
        if info:
            try:
                os.remove(info["path"])
                del self.disk_cache[key]
                self.current_disk_size -= info["size"]
            except Exception as e:
                logger.warning(f"移除磁盘缓存失败: {e}")
    
    def _estimate_size(self, value: Any) -> int:
        """估算对象大小"""
        try:
            return len(pickle.dumps(value))
        except Exception:
            return sys.getsizeof(value)
    
    def _start_monitor(self):
        """启动缓存监控"""
        def monitor_routine():
            while True:
                try:
                    # 检查系统内存压力
                    if self.memory_manager.get_memory_pressure() > 80:
                        # 主动清理部分内存缓存
                        self._reduce_memory_cache()
                    
                    # 检查磁盘空间
                    if self.current_disk_size > self.max_disk_size * 0.9:
                        # 清理旧的磁盘缓存
                        self._cleanup_disk_cache()
                    
                    # 更新访问统计
                    self._update_stats()
                    
                    # 每60秒运行一次
                    time.sleep(60)
                    
                except Exception as e:
                    logger.error(f"缓存监控异常: {e}")
                    time.sleep(60)
        
        # 启动监控线程
        threading.Thread(target=monitor_routine, daemon=True).start()
    
    def _reduce_memory_cache(self):
        """减少内存缓存使用"""
        target_size = self.max_memory_size * 0.7  # 减少到70%
        while self.current_memory_size > target_size and self.memory_cache:
            self._evict_from_memory()
    
    def _cleanup_disk_cache(self):
        """清理过期的磁盘缓存"""
        current_time = time.time()
        expired_keys = []
        
        # 查找7天未访问的项目
        for key, info in self.disk_cache.items():
            if current_time - info["last_access"] > 7 * 24 * 3600:
                expired_keys.append(key)
        
        # 删除过期项目
        for key in expired_keys:
            self._remove_from_disk(key)
    
    def _update_stats(self):
        """更新缓存统计信息"""
        stats_file = self.cache_dir / "cache_stats.json"
        try:
            with open(stats_file, 'w') as f:
                json.dump({
                    "timestamp": time.time(),
                    "memory_cache_size": self.current_memory_size,
                    "disk_cache_size": self.current_disk_size,
                    "stats": self.stats
                }, f, indent=2)
        except Exception as e:
            logger.warning(f"更新缓存统计失败: {e}")
    
    def _load_persistent_data(self):
        """加载持久化数据"""
        try:
            # 加载磁盘缓存索引
            index_file = self.cache_dir / "cache_index.json"
            if index_file.exists():
                with open(index_file, 'r') as f:
                    self.disk_cache = OrderedDict(json.load(f))
                    
                # 验证文件存在性并更新大小
                self.current_disk_size = 0
                for key, info in list(self.disk_cache.items()):
                    if not os.path.exists(info["path"]):
                        del self.disk_cache[key]
                    else:
                        self.current_disk_size += info["size"]
            
        except Exception as e:
            logger.error(f"加载持久化数据失败: {e}")
    
    def save_persistent_data(self):
        """保存持久化数据"""
        if not self.enable_persistent:
            return
            
        try:
            # 保存磁盘缓存索引
            index_file = self.cache_dir / "cache_index.json"
            with open(index_file, 'w') as f:
                json.dump(dict(self.disk_cache), f, indent=2)
                
        except Exception as e:
            logger.error(f"保存持久化数据失败: {e}")
    
    def clear(self):
        """清空所有缓存"""
        # 清空内存缓存
        self.memory_cache.clear()
        self.current_memory_size = 0
        
        # 清空磁盘缓存
        for key in list(self.disk_cache.keys()):
            self._remove_from_disk(key)
        
        # 重置统计
        self.stats = {
            "memory_hits": 0,
            "disk_hits": 0,
            "misses": 0,
            "evictions": 0
        }
    
    def get_stats(self) -> Dict:
        """获取缓存统计信息
        
        Returns:
            Dict: 统计信息
        """
        return {
            "memory_cache": {
                "size": self.current_memory_size,
                "limit": self.max_memory_size,
                "items": len(self.memory_cache)
            },
            "disk_cache": {
                "size": self.current_disk_size,
                "limit": self.max_disk_size,
                "items": len(self.disk_cache)
            },
            "stats": self.stats
        }
    
    def __del__(self):
        """析构时保存持久化数据"""
        self.save_persistent_data() 