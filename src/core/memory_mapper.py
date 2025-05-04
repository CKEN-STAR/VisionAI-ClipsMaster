"""内存映射优化器模块

此模块实现了高效的内存映射和优化机制，包括:
1. 智能内存映射
2. 共享内存管理
3. 内存访问模式优化
4. 内存碎片整理
5. 映射状态监控
"""

import os
import mmap
import torch
import psutil
import numpy as np
from typing import Dict, List, Optional, Union
from pathlib import Path
from loguru import logger

class MemoryMapper:
    """内存映射优化器"""
    
    def __init__(self,
                 page_size: int = 4096,
                 max_cached_maps: int = 10,
                 enable_shared_memory: bool = True):
        """初始化内存映射优化器
        
        Args:
            page_size: 内存页大小(字节)
            max_cached_maps: 最大缓存映射数
            enable_shared_memory: 是否启用共享内存
        """
        self.page_size = page_size
        self.max_cached_maps = max_cached_maps
        self.enable_shared_memory = enable_shared_memory
        
        # 映射缓存
        self._mapped_files: Dict[str, mmap.mmap] = {}
        self._map_usage_count: Dict[str, int] = {}
        self._map_access_time: Dict[str, float] = {}
        
        # 共享内存区
        self._shared_segments: Dict[str, np.ndarray] = {}
        
        # 访问模式统计
        self._access_patterns: Dict[str, List[int]] = {}
        
        # 性能统计
        self._stats = {
            "total_maps": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "total_mapped_size": 0
        }
    
    def map_tensor(self,
                   tensor_path: Union[str, Path],
                   shape: Optional[tuple] = None,
                   dtype: Optional[torch.dtype] = None,
                   device: str = 'cpu',
                   access_mode: str = 'r') -> torch.Tensor:
        """将文件映射为Tensor
        
        Args:
            tensor_path: Tensor文件路径
            shape: Tensor形状
            dtype: 数据类型
            device: 设备
            access_mode: 访问模式('r'或'r+')
            
        Returns:
            torch.Tensor: 映射的Tensor
        """
        tensor_path = str(tensor_path)
        
        # 检查缓存
        if tensor_path in self._mapped_files:
            self._stats["cache_hits"] += 1
            self._update_usage_stats(tensor_path)
            return self._tensor_from_map(self._mapped_files[tensor_path], shape, dtype, device)
        
        self._stats["cache_misses"] += 1
        
        # 创建新映射
        file_size = os.path.getsize(tensor_path)
        access_flag = mmap.ACCESS_READ if access_mode == 'r' else mmap.ACCESS_WRITE
        
        with open(tensor_path, access_mode + 'b') as f:
            mapped_mem = mmap.mmap(
                f.fileno(), 
                length=file_size,
                access=access_flag,
                offset=0
            )
        
        # 缓存管理
        self._manage_cache()
        
        # 更新缓存
        self._mapped_files[tensor_path] = mapped_mem
        self._update_usage_stats(tensor_path)
        self._stats["total_maps"] += 1
        self._stats["total_mapped_size"] += file_size
        
        return self._tensor_from_map(mapped_mem, shape, dtype, device)
    
    def create_shared_segment(self,
                            name: str,
                            shape: tuple,
                            dtype: np.dtype) -> np.ndarray:
        """创建共享内存段
        
        Args:
            name: 段名称
            shape: 数组形状
            dtype: 数据类型
            
        Returns:
            np.ndarray: 共享内存数组
        """
        if not self.enable_shared_memory:
            raise RuntimeError("共享内存未启用")
        
        if name in self._shared_segments:
            return self._shared_segments[name]
        
        # 创建共享内存数组
        shared_array = np.zeros(shape, dtype=dtype)
        self._shared_segments[name] = shared_array
        
        return shared_array
    
    def optimize_access_pattern(self, tensor_path: str):
        """优化内存访问模式
        
        Args:
            tensor_path: Tensor文件路径
        """
        if tensor_path not in self._access_patterns:
            return
            
        patterns = self._access_patterns[tensor_path]
        
        # 分析访问模式
        if len(patterns) > 100:
            # 检测顺序访问模式
            is_sequential = all(
                patterns[i] <= patterns[i+1]
                for i in range(len(patterns)-1)
            )
            
            if is_sequential:
                # 启用预读
                mapped_mem = self._mapped_files.get(tensor_path)
                if mapped_mem:
                    mapped_mem.madvise(mmap.MADV_SEQUENTIAL)
            else:
                # 检测随机访问模式
                is_random = len(set(
                    patterns[i] - patterns[i-1]
                    for i in range(1, len(patterns))
                )) > len(patterns) // 2
                
                if is_random:
                    mapped_mem = self._mapped_files.get(tensor_path)
                    if mapped_mem:
                        mapped_mem.madvise(mmap.MADV_RANDOM)
    
    def defragment(self):
        """内存碎片整理"""
        # 获取当前进程
        process = psutil.Process()
        
        # 强制内存整理
        if hasattr(process, "memory_maps"):
            maps = process.memory_maps()
            fragmentation = self._calculate_fragmentation(maps)
            
            if fragmentation > 0.3:  # 碎片率超过30%
                # 触发内存整理
                mapped_paths = list(self._mapped_files.keys())
                for path in mapped_paths:
                    self.unmap(path)
                    self.map_tensor(path)
    
    def unmap(self, tensor_path: str):
        """解除内存映射
        
        Args:
            tensor_path: Tensor文件路径
        """
        if tensor_path in self._mapped_files:
            self._mapped_files[tensor_path].close()
            del self._mapped_files[tensor_path]
            del self._map_usage_count[tensor_path]
            del self._map_access_time[tensor_path]
    
    def get_stats(self) -> Dict:
        """获取性能统计
        
        Returns:
            Dict: 性能统计信息
        """
        return {
            **self._stats,
            "active_maps": len(self._mapped_files),
            "shared_segments": len(self._shared_segments)
        }
    
    def _tensor_from_map(self,
                        mapped_mem: mmap.mmap,
                        shape: Optional[tuple],
                        dtype: Optional[torch.dtype],
                        device: str) -> torch.Tensor:
        """从内存映射创建Tensor
        
        Args:
            mapped_mem: 内存映射对象
            shape: Tensor形状
            dtype: 数据类型
            device: 设备
            
        Returns:
            torch.Tensor: 创建的Tensor
        """
        # 创建numpy数组视图
        array = np.frombuffer(mapped_mem, dtype=np.float32)
        
        if shape is not None:
            array = array.reshape(shape)
        
        # 转换为Tensor
        tensor = torch.from_numpy(array)
        
        if dtype is not None:
            tensor = tensor.to(dtype=dtype)
            
        return tensor.to(device)
    
    def _update_usage_stats(self, tensor_path: str):
        """更新使用统计
        
        Args:
            tensor_path: Tensor文件路径
        """
        import time
        self._map_usage_count[tensor_path] = self._map_usage_count.get(tensor_path, 0) + 1
        self._map_access_time[tensor_path] = time.time()
    
    def _manage_cache(self):
        """管理映射缓存"""
        if len(self._mapped_files) >= self.max_cached_maps:
            # 基于使用频率和访问时间的LRU策略
            paths = list(self._mapped_files.keys())
            scores = [
                self._map_usage_count[p] * 0.7 + self._map_access_time[p] * 0.3
                for p in paths
            ]
            
            # 移除得分最低的映射
            min_score_idx = scores.index(min(scores))
            self.unmap(paths[min_score_idx])
    
    def _calculate_fragmentation(self, memory_maps) -> float:
        """计算内存碎片率
        
        Args:
            memory_maps: 内存映射信息
            
        Returns:
            float: 碎片率(0-1)
        """
        if not memory_maps:
            return 0.0
            
        # 计算总空间和已用空间
        total_space = sum(m.size for m in memory_maps)
        used_space = sum(m.rss for m in memory_maps)
        
        # 计算碎片率
        return 1.0 - (used_space / total_space)
    
    def __del__(self):
        """清理资源"""
        # 关闭所有映射
        for mapped_mem in self._mapped_files.values():
            mapped_mem.close()
        
        # 清理共享内存
        self._shared_segments.clear() 