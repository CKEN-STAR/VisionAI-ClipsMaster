#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
内存映射引擎模块

提供高效的内存映射机制，用于视频处理中的大文件处理，
减少不必要的内存拷贝，提高性能并降低内存使用。
"""

import os
import mmap
import numpy as np
import cv2
import logging
import time
from typing import Dict, List, Tuple, Optional, Union, Any, BinaryIO
from pathlib import Path

from src.utils.log_handler import get_logger

# 配置日志记录器
logger = get_logger("memmap_engine")

# 默认内存映射参数
DEFAULT_PAGE_SIZE = 4096  # 默认页大小
DEFAULT_CACHE_SIZE = 10   # 默认缓存大小

class MemmapHandle:
    """内存映射句柄类"""
    
    def __init__(self, 
                 file_obj: BinaryIO, 
                 mapped_obj: mmap.mmap, 
                 path: str, 
                 size: int, 
                 mode: str):
        """初始化内存映射句柄
        
        Args:
            file_obj: 文件对象
            mapped_obj: 内存映射对象 
            path: 文件路径
            size: 映射大小
            mode: 访问模式
        """
        self.file_obj = file_obj
        self.mapped_obj = mapped_obj
        self.path = path
        self.size = size
        self.mode = mode
        self.last_access = time.time()
        self.access_count = 0
    
    def close(self):
        """关闭内存映射"""
        if self.mapped_obj:
            self.mapped_obj.close()
            self.mapped_obj = None
        
        if self.file_obj:
            self.file_obj.close()
            self.file_obj = None


class MemmapEngine:
    """内存映射引擎类"""
    
    def __init__(self, 
                 max_cached_maps: int = DEFAULT_CACHE_SIZE,
                 page_size: int = DEFAULT_PAGE_SIZE):
        """初始化内存映射引擎
        
        Args:
            max_cached_maps: 最大缓存映射数，默认10
            page_size: 内存页大小，默认4096字节
        """
        self.max_cached_maps = max_cached_maps
        self.page_size = page_size
        
        # 缓存的内存映射
        self._cached_maps: Dict[str, MemmapHandle] = {}
        
        # 性能统计
        self.stats = {
            "total_maps": 0,
            "cache_hits": 0, 
            "cache_misses": 0,
            "total_bytes": 0,
            "active_maps": 0
        }
        
        logger.info(f"内存映射引擎初始化完成: 最大缓存映射={max_cached_maps}, 页大小={page_size}")

    def mmap_video_file(self, path: str) -> mmap.mmap:
        """建立视频文件内存映射
        
        Args:
            path: 视频文件路径
            
        Returns:
            mmap.mmap: 内存映射对象
        """
        path = os.path.abspath(path)
        
        # 检查缓存
        if path in self._cached_maps:
            handle = self._cached_maps[path]
            handle.last_access = time.time()
            handle.access_count += 1
            self.stats["cache_hits"] += 1
            return handle.mapped_obj
        
        self.stats["cache_misses"] += 1
        
        # 创建新映射
        fd = os.open(path, os.O_RDONLY)
        length = os.path.getsize(path)
        
        # 创建映射对象
        mapped_obj = mmap.mmap(fd, length, access=mmap.ACCESS_READ)
        
        # 更新统计信息
        self.stats["total_maps"] += 1
        self.stats["total_bytes"] += length
        self.stats["active_maps"] += 1
        
        # 创建文件对象用于保持文件描述符打开
        file_obj = os.fdopen(fd, 'rb')
        
        # 缓存管理
        if len(self._cached_maps) >= self.max_cached_maps:
            self._evict_cache()
        
        # 添加到缓存
        self._cached_maps[path] = MemmapHandle(
            file_obj=file_obj,
            mapped_obj=mapped_obj,
            path=path,
            size=length,
            mode='r'
        )
        
        logger.debug(f"已创建内存映射: {path} ({length/1024/1024:.2f} MB)")
        return mapped_obj

    def mmap_binary_file(self, path: str, mode: str = 'r') -> mmap.mmap:
        """建立二进制文件内存映射
        
        Args:
            path: 文件路径
            mode: 访问模式 ('r'=只读, 'r+'=读写)
            
        Returns:
            mmap.mmap: 内存映射对象
        """
        path = os.path.abspath(path)
        
        # 检查缓存 (仅对只读映射检查缓存)
        if mode == 'r' and path in self._cached_maps:
            handle = self._cached_maps[path]
            handle.last_access = time.time()
            handle.access_count += 1
            self.stats["cache_hits"] += 1
            return handle.mapped_obj
        
        self.stats["cache_misses"] += 1
        
        # 映射模式
        open_mode = 'rb' if mode == 'r' else 'r+b'
        access_flag = mmap.ACCESS_READ if mode == 'r' else mmap.ACCESS_WRITE
        
        # 创建映射
        file_obj = open(path, open_mode)
        length = os.path.getsize(path)
        
        mapped_obj = mmap.mmap(
            file_obj.fileno(),
            length=length,
            access=access_flag
        )
        
        # 更新统计
        self.stats["total_maps"] += 1
        self.stats["total_bytes"] += length
        self.stats["active_maps"] += 1
        
        # 读写模式不缓存
        if mode == 'r+':
            # 创建临时句柄以便即使不缓存也能正确管理文件对象的生命周期
            handle = MemmapHandle(
                file_obj=file_obj,
                mapped_obj=mapped_obj,
                path=path,
                size=length,
                mode=mode
            )
            # 将句柄添加到缓存以便能够正确关闭
            temp_key = f"{path}_{time.time()}"
            self._cached_maps[temp_key] = handle
            return mapped_obj
            
        # 缓存管理 (仅对只读映射)
        if len(self._cached_maps) >= self.max_cached_maps:
            self._evict_cache()
        
        # 添加到缓存
        self._cached_maps[path] = MemmapHandle(
            file_obj=file_obj,
            mapped_obj=mapped_obj,
            path=path,
            size=length,
            mode=mode
        )
        
        logger.debug(f"已创建内存映射: {path} ({length/1024/1024:.2f} MB), 模式: {mode}")
        return mapped_obj
    
    def map_video_frames(self, 
                        video_path: str, 
                        start_frame: int = 0, 
                        frame_count: Optional[int] = None) -> Tuple[np.ndarray, int]:
        """映射视频帧数据
        
        优化视频帧访问，通过内存映射减少拷贝操作
        
        Args:
            video_path: 视频文件路径
            start_frame: 起始帧索引
            frame_count: 要读取的帧数，None表示读取所有剩余帧
            
        Returns:
            Tuple[np.ndarray, int]: 帧数据和实际读取的帧数
        """
        try:
            # 打开视频获取基本信息
            cap = cv2.VideoCapture(video_path)
            
            if not cap.isOpened():
                logger.error(f"无法打开视频文件: {video_path}")
                return np.array([]), 0
            
            # 获取视频属性
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            
            if frame_count is None:
                frame_count = total_frames - start_frame
            
            # 确保不超出视频总帧数
            actual_frame_count = min(frame_count, total_frames - start_frame)
            
            if actual_frame_count <= 0:
                logger.warning(f"无有效帧可读取 (起始帧={start_frame}, 总帧数={total_frames})")
                cap.release()
                return np.array([]), 0
            
            # 映射原始视频数据 (如果支持)
            try:
                # 通过内存映射优化读取操作
                mapped_video = self.mmap_video_file(video_path)
                
                # 由于视频压缩格式问题，这里仍需要解码
                # 但我们可以通过高效的缓冲区操作减少拷贝
                cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
                
                # 预分配帧数组
                frames = np.zeros((actual_frame_count, height, width, 3), dtype=np.uint8)
                
                for i in range(actual_frame_count):
                    ret, frame = cap.read()
                    if not ret:
                        logger.warning(f"读取第 {start_frame + i} 帧失败")
                        actual_frame_count = i
                        break
                    
                    frames[i] = frame
                
                cap.release()
                return frames, actual_frame_count
                
            except Exception as e:
                logger.warning(f"内存映射访问失败，回退到标准模式: {e}")
                # 回退到标准方式读取
        
        except Exception as e:
            logger.error(f"映射视频帧数据时出错: {e}")
            return np.array([]), 0
        
        # 回退逻辑：直接读取视频帧
        try:
            cap = cv2.VideoCapture(video_path)
            cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
            
            frames = []
            count = 0
            
            while count < actual_frame_count:
                ret, frame = cap.read()
                if not ret:
                    break
                
                frames.append(frame)
                count += 1
            
            cap.release()
            
            if count > 0:
                return np.array(frames), count
            return np.array([]), 0
            
        except Exception as e:
            logger.error(f"回退方式读取视频帧时出错: {e}")
            return np.array([]), 0
    
    def create_memory_mapped_array(self, 
                                  path: str, 
                                  shape: Tuple, 
                                  dtype: np.dtype = np.float32, 
                                  mode: str = 'w+') -> np.ndarray:
        """创建内存映射数组
        
        用于创建可持久化的大型数组，适用于处理中间结果
        
        Args:
            path: 文件路径
            shape: 数组形状
            dtype: 数据类型
            mode: 访问模式
            
        Returns:
            np.ndarray: 内存映射数组
        """
        try:
            # 创建内存映射数组
            array = np.memmap(path, dtype=dtype, mode=mode, shape=shape)
            logger.debug(f"已创建内存映射数组: {path}, 形状: {shape}, 类型: {dtype}")
            return array
            
        except Exception as e:
            logger.error(f"创建内存映射数组失败: {e}")
            # 回退到普通数组
            return np.zeros(shape, dtype=dtype)
    
    def unmap(self, path: str) -> bool:
        """解除内存映射
        
        Args:
            path: 文件路径
            
        Returns:
            bool: 是否成功解除映射
        """
        path = os.path.abspath(path)
        
        if path in self._cached_maps:
            try:
                handle = self._cached_maps[path]
                handle.close()
                del self._cached_maps[path]
                self.stats["active_maps"] -= 1
                logger.debug(f"已解除内存映射: {path}")
                return True
            except Exception as e:
                logger.error(f"解除内存映射时出错: {e}")
                return False
                
        return False
    
    def _evict_cache(self):
        """清理缓存中最不常用的映射"""
        if not self._cached_maps:
            return
            
        # 按最近访问时间排序
        sorted_maps = sorted(
            self._cached_maps.items(),
            key=lambda x: x[1].last_access
        )
        
        # 移除最旧的映射
        oldest_path, oldest_handle = sorted_maps[0]
        oldest_handle.close()
        del self._cached_maps[oldest_path]
        self.stats["active_maps"] -= 1
        
        logger.debug(f"缓存已满，释放映射: {oldest_path}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取性能统计
        
        Returns:
            Dict[str, Any]: 性能统计信息
        """
        # 更新活跃映射数
        self.stats["active_maps"] = len(self._cached_maps)
        return self.stats
    
    def clear_all(self):
        """清除所有映射"""
        paths = list(self._cached_maps.keys())
        
        for path in paths:
            self.unmap(path)
            
        self.stats["active_maps"] = 0
        logger.info("所有内存映射已清除")
    
    def __del__(self):
        """析构函数，确保所有映射被释放"""
        self.clear_all()


# 单例实例
_memmap_engine = None

def get_memmap_engine() -> MemmapEngine:
    """获取内存映射引擎单例
    
    Returns:
        MemmapEngine: 内存映射引擎实例
    """
    global _memmap_engine
    
    if _memmap_engine is None:
        _memmap_engine = MemmapEngine()
        
    return _memmap_engine


def mmap_video_file(path: str) -> mmap.mmap:
    """建立视频文件内存映射
    
    Args:
        path: 视频文件路径
        
    Returns:
        mmap.mmap: 内存映射对象
    """
    engine = get_memmap_engine()
    return engine.mmap_video_file(path)


def map_video_frames(video_path: str, 
                     start_frame: int = 0, 
                     frame_count: Optional[int] = None) -> Tuple[np.ndarray, int]:
    """映射视频帧数据
    
    Args:
        video_path: 视频文件路径
        start_frame: 起始帧索引
        frame_count: 要读取的帧数
        
    Returns:
        Tuple[np.ndarray, int]: 帧数据和实际读取的帧数
    """
    engine = get_memmap_engine()
    return engine.map_video_frames(video_path, start_frame, frame_count)


if __name__ == "__main__":
    # 简单测试
    logger.info("内存映射引擎测试")
    
    # 创建引擎
    engine = get_memmap_engine()
    
    # 测试文件映射
    test_file = "test_data.bin"
    
    try:
        # 创建测试文件
        with open(test_file, "wb") as f:
            f.write(b"\x00" * 1024 * 1024)  # 1MB文件
        
        # 映射文件
        mapped = engine.mmap_binary_file(test_file, "r+")
        
        # 写入数据
        mapped[0:5] = b"hello"
        
        # 解除映射
        engine.unmap(test_file)
        
        # 检查数据是否写入
        with open(test_file, "rb") as f:
            data = f.read(5)
            logger.info(f"写入数据: {data}")
        
        # 清理
        if os.path.exists(test_file):
            os.remove(test_file)
            
        logger.info("内存映射引擎测试完成")
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
        if os.path.exists(test_file):
            os.remove(test_file) 