"""
磁盘缓存管理器
提供磁盘缓存管理功能
"""

import os
import json
import time
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, Union

class DiskCacheManager:
    """磁盘缓存管理器"""
    
    def __init__(self, cache_dir: str = "cache", max_size_mb: int = 500):
        self.cache_dir = Path(cache_dir)
        self.max_size_mb = max_size_mb
        self.cache_index_file = self.cache_dir / "cache_index.json"
        self.cache_index: Dict[str, Dict[str, Any]] = {}
        
        # 创建缓存目录
        self.cache_dir.mkdir(exist_ok=True)
        
        # 加载缓存索引
        self._load_cache_index()
    
    def _load_cache_index(self):
        """加载缓存索引"""
        try:
            if self.cache_index_file.exists():
                with open(self.cache_index_file, 'r', encoding='utf-8') as f:
                    self.cache_index = json.load(f)
        except Exception as e:
            print(f"[WARN] 加载缓存索引失败: {e}")
            self.cache_index = {}
    
    def _save_cache_index(self):
        """保存缓存索引"""
        try:
            with open(self.cache_index_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache_index, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[WARN] 保存缓存索引失败: {e}")
    
    def _get_cache_key(self, key: str) -> str:
        """生成缓存键"""
        return hashlib.md5(key.encode()).hexdigest()
    
    def put(self, key: str, data: Union[str, bytes, dict], ttl_seconds: int = 3600) -> bool:
        """
        存储数据到缓存
        
        Args:
            key: 缓存键
            data: 要缓存的数据
            ttl_seconds: 生存时间（秒）
            
        Returns:
            是否成功存储
        """
        try:
            cache_key = self._get_cache_key(key)
            cache_file = self.cache_dir / f"{cache_key}.cache"
            
            # 准备缓存数据
            if isinstance(data, dict):
                cache_data = json.dumps(data, ensure_ascii=False)
                data_type = "json"
            elif isinstance(data, str):
                cache_data = data
                data_type = "text"
            elif isinstance(data, bytes):
                cache_data = data
                data_type = "binary"
            else:
                cache_data = str(data)
                data_type = "text"
            
            # 写入缓存文件
            if data_type == "binary":
                with open(cache_file, 'wb') as f:
                    f.write(cache_data)
            else:
                with open(cache_file, 'w', encoding='utf-8') as f:
                    f.write(cache_data)
            
            # 更新索引
            self.cache_index[cache_key] = {
                'original_key': key,
                'file_path': str(cache_file),
                'data_type': data_type,
                'created_time': time.time(),
                'ttl_seconds': ttl_seconds,
                'size_bytes': cache_file.stat().st_size
            }
            
            self._save_cache_index()
            
            # 检查缓存大小
            self._cleanup_if_needed()
            
            return True
            
        except Exception as e:
            print(f"[WARN] 缓存存储失败: {e}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """
        从缓存获取数据
        
        Args:
            key: 缓存键
            
        Returns:
            缓存的数据，如果不存在或过期则返回None
        """
        try:
            cache_key = self._get_cache_key(key)
            
            if cache_key not in self.cache_index:
                return None
            
            cache_info = self.cache_index[cache_key]
            cache_file = Path(cache_info['file_path'])
            
            # 检查文件是否存在
            if not cache_file.exists():
                del self.cache_index[cache_key]
                self._save_cache_index()
                return None
            
            # 检查是否过期
            if self._is_expired(cache_info):
                self.delete(key)
                return None
            
            # 读取缓存数据
            data_type = cache_info['data_type']
            
            if data_type == "binary":
                with open(cache_file, 'rb') as f:
                    return f.read()
            else:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                if data_type == "json":
                    return json.loads(content)
                else:
                    return content
                    
        except Exception as e:
            print(f"[WARN] 缓存读取失败: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """删除缓存项"""
        try:
            cache_key = self._get_cache_key(key)
            
            if cache_key in self.cache_index:
                cache_info = self.cache_index[cache_key]
                cache_file = Path(cache_info['file_path'])
                
                # 删除文件
                if cache_file.exists():
                    cache_file.unlink()
                
                # 从索引中删除
                del self.cache_index[cache_key]
                self._save_cache_index()
                
                return True
            
            return False
            
        except Exception as e:
            print(f"[WARN] 缓存删除失败: {e}")
            return False
    
    def _is_expired(self, cache_info: Dict[str, Any]) -> bool:
        """检查缓存是否过期"""
        try:
            created_time = cache_info['created_time']
            ttl_seconds = cache_info['ttl_seconds']
            
            if ttl_seconds <= 0:  # 永不过期
                return False
            
            return time.time() - created_time > ttl_seconds
            
        except Exception:
            return True
    
    def _cleanup_if_needed(self):
        """如果需要则清理缓存"""
        try:
            total_size = self.get_cache_size_mb()
            
            if total_size > self.max_size_mb:
                self._cleanup_old_entries()
                
        except Exception as e:
            print(f"[WARN] 缓存清理失败: {e}")
    
    def _cleanup_old_entries(self):
        """清理旧的缓存项"""
        try:
            # 按创建时间排序
            sorted_entries = sorted(
                self.cache_index.items(),
                key=lambda x: x[1]['created_time']
            )
            
            # 删除最旧的条目，直到大小合适
            for cache_key, cache_info in sorted_entries:
                if self.get_cache_size_mb() <= self.max_size_mb * 0.8:
                    break
                
                cache_file = Path(cache_info['file_path'])
                if cache_file.exists():
                    cache_file.unlink()
                
                del self.cache_index[cache_key]
            
            self._save_cache_index()
            
        except Exception as e:
            print(f"[WARN] 清理旧缓存项失败: {e}")
    
    def get_cache_size_mb(self) -> float:
        """获取缓存大小（MB）"""
        try:
            total_size = 0
            for cache_info in self.cache_index.values():
                total_size += cache_info.get('size_bytes', 0)
            
            return total_size / (1024 * 1024)
            
        except Exception:
            return 0.0
    
    def clear_cache(self):
        """清空所有缓存"""
        try:
            # 删除所有缓存文件
            for cache_info in self.cache_index.values():
                cache_file = Path(cache_info['file_path'])
                if cache_file.exists():
                    cache_file.unlink()
            
            # 清空索引
            self.cache_index.clear()
            self._save_cache_index()
            
            print("[OK] 缓存已清空")
            
        except Exception as e:
            print(f"[WARN] 清空缓存失败: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        try:
            total_entries = len(self.cache_index)
            total_size_mb = self.get_cache_size_mb()
            
            # 统计过期项
            expired_count = 0
            for cache_info in self.cache_index.values():
                if self._is_expired(cache_info):
                    expired_count += 1
            
            return {
                'total_entries': total_entries,
                'expired_entries': expired_count,
                'total_size_mb': round(total_size_mb, 2),
                'max_size_mb': self.max_size_mb,
                'usage_percent': round((total_size_mb / self.max_size_mb) * 100, 1),
                'cache_dir': str(self.cache_dir)
            }
            
        except Exception as e:
            print(f"[WARN] 获取缓存统计失败: {e}")
            return {}

# 全局缓存管理器实例
_cache_manager: Optional[DiskCacheManager] = None

def get_disk_cache_manager() -> DiskCacheManager:
    """获取全局磁盘缓存管理器"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = DiskCacheManager()
    return _cache_manager

def setup_cache(cache_dir: str = "cache", max_size_mb: int = 500):
    """设置缓存"""
    global _cache_manager
    _cache_manager = DiskCacheManager(cache_dir, max_size_mb)

def clear_cache():
    """清空缓存"""
    manager = get_disk_cache_manager()
    manager.clear_cache()

def get_cache_stats() -> Dict[str, Any]:
    """获取缓存统计"""
    manager = get_disk_cache_manager()
    return manager.get_cache_stats()

__all__ = [
    'DiskCacheManager',
    'get_disk_cache_manager',
    'setup_cache',
    'clear_cache',
    'get_cache_stats'
]
