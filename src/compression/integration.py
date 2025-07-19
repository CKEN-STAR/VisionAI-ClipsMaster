#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
压缩集成模块

将压缩功能集成到内存管理系统中，优化资源使用
"""

import os
import time
import logging
from typing import Dict, Any, List, Optional, Tuple, Union
import threading
import weakref
import numpy as np

# 导入压缩模块
from src.compression.compressors import (
    get_compressor, 
    compress_data, 
    decompress_data
)
from src.compression.algorithm_benchmark import get_recommended_algorithm

# 尝试导入内存相关模块
try:
    from src.memory.resource_tracker import get_resource_tracker
    has_resource_tracker = True
except ImportError:
    has_resource_tracker = False

try:
    from src.memory.release_event_listener import get_release_listener
    has_event_listener = True
except ImportError:
    has_event_listener = False

# 日志配置
logger = logging.getLogger("CompressionIntegration")

class CompressionManager:
    """压缩管理器，负责系统资源的压缩策略"""
    
    def __init__(self):
        """初始化压缩管理器"""
        self.resource_tracker = None
        if has_resource_tracker:
            self.resource_tracker = get_resource_tracker()
            logger.info("已连接到资源跟踪器")
        
        self.event_listener = None
        if has_event_listener:
            self.event_listener = get_release_listener()
            logger.info("已连接到释放事件监听器")
        
        # 压缩策略配置
        self.compression_config = {
            "model_weights": {
                "algorithm": "zstd",
                "balance_mode": "ratio",
                "auto_compress": False,
                "compression_threshold_mb": 50,
                "compression_level": 3
            },
            "subtitle": {
                "algorithm": "lz4",
                "balance_mode": "speed",
                "auto_compress": True,
                "compression_threshold_mb": 1,
                "compression_level": 0
            },
            "temp_buffers": {
                "algorithm": "lz4",
                "balance_mode": "speed",
                "auto_compress": True,
                "compression_threshold_mb": 5,
                "compression_level": 0
            },
            "attention_cache": {
                "algorithm": "zstd",
                "balance_mode": "balanced",
                "auto_compress": True,
                "compression_threshold_mb": 10,
                "compression_level": 1
            },
            "file_cache": {
                "algorithm": "zstd",
                "balance_mode": "ratio",
                "auto_compress": True,
                "compression_threshold_mb": 20,
                "compression_level": 3
            },
            "default": {
                "algorithm": "gzip",
                "balance_mode": "balanced",
                "auto_compress": False,
                "compression_threshold_mb": 10,
                "compression_level": 6
            }
        }
        
        # 压缩统计
        self.stats = {
            "total_compressed_resources": 0,
            "total_original_mb": 0.0,
            "total_compressed_mb": 0.0,
            "average_ratio": 0.0,
            "compression_by_type": {}
        }
        
        # 压缩资源映射 {资源ID: 压缩元数据}
        self.compressed_resources = {}
        
        # 注册到资源跟踪器
        self._register_with_resource_tracker()
        
    def _register_with_resource_tracker(self):
        """向资源跟踪器注册回调"""
        if not self.resource_tracker:
            return
            
        try:
            # 注册资源创建回调
            if hasattr(self.resource_tracker, "register_resource_callback"):
                self.resource_tracker.register_resource_callback(self._on_resource_created)
                logger.info("已注册资源创建回调")
        except Exception as e:
            logger.error(f"注册资源回调失败: {e}")
    
    def _on_resource_created(self, res_id: str, res_type: str, metadata: Dict[str, Any]):
        """
        资源创建回调
        
        Args:
            res_id: 资源ID
            res_type: 资源类型
            metadata: 资源元数据
        """
        # 检查是否符合自动压缩条件
        config = self._get_compression_config(res_type)
        
        if not config["auto_compress"]:
            return
            
        # 获取资源大小
        size_mb = metadata.get("size_estimate", 0)
        
        # 如果资源大小超过阈值，安排压缩
        if size_mb >= config["compression_threshold_mb"]:
            logger.debug(f"安排压缩资源: {res_id}, 类型: {res_type}, 大小: {size_mb}MB")
            
            # 使用线程以避免阻塞主流程
            threading.Thread(
                target=self._compress_resource_later,
                args=(res_id, res_type, 5),  # 5秒后压缩
                daemon=True
            ).start()
    
    def _compress_resource_later(self, res_id: str, res_type: str, delay_seconds: int):
        """
        延迟压缩资源
        
        Args:
            res_id: 资源ID
            res_type: 资源类型
            delay_seconds: 延迟秒数
        """
        time.sleep(delay_seconds)
        
        # 检查资源是否仍然存在
        if self.resource_tracker and not self.resource_tracker.has_resource(res_id):
            logger.debug(f"资源已不存在，取消压缩: {res_id}")
            return
            
        # 执行压缩
        try:
            self.compress_resource(res_id)
        except Exception as e:
            logger.error(f"延迟压缩资源失败: {res_id} - {e}")
    
    def _get_compression_config(self, res_type: str) -> Dict[str, Any]:
        """
        获取指定资源类型的压缩配置
        
        Args:
            res_type: 资源类型
            
        Returns:
            Dict: 压缩配置
        """
        if res_type in self.compression_config:
            return self.compression_config[res_type]
        return self.compression_config["default"]
    
    def _map_res_type_to_data_type(self, res_type: str) -> str:
        """
        将资源类型映射到数据类型
        
        Args:
            res_type: 资源类型
            
        Returns:
            str: 数据类型
        """
        mapping = {
            "model_weights": "model_weights",
            "model_weights_cache": "model_weights",
            "subtitle": "subtitle",
            "subtitle_data": "subtitle",
            "temp_buffers": "binary",
            "attention_cache": "numeric",
            "token_cache": "numeric",
            "file_cache": "binary",
            "image_data": "binary"
        }
        
        return mapping.get(res_type, "binary")
    
    def compress_resource(self, res_id: str) -> bool:
        """
        压缩指定资源
        
        Args:
            res_id: 资源ID
            
        Returns:
            bool: 是否成功
        """
        if not self.resource_tracker:
            logger.error("资源跟踪器不可用")
            return False
            
        # 获取资源信息
        resource_info = self.resource_tracker.get_resource_info(res_id)
        if not resource_info:
            logger.warning(f"找不到资源: {res_id}")
            return False
            
        # 已经压缩过
        if res_id in self.compressed_resources:
            logger.debug(f"资源已压缩: {res_id}")
            return True
            
        # 获取资源类型和对象引用
        res_type = resource_info.get("res_type", "unknown")
        obj_ref = resource_info.get("obj_ref")
        
        # 如果没有对象引用，无法压缩
        if not obj_ref:
            logger.warning(f"资源没有对象引用: {res_id}")
            return False
            
        # 获取实际对象
        obj = obj_ref()
        if obj is None:
            logger.warning(f"资源对象已被回收: {res_id}")
            return False
            
        # 获取压缩配置
        config = self._get_compression_config(res_type)
        
        # 确定压缩算法
        data_type = self._map_res_type_to_data_type(res_type)
        algorithm = config.get("algorithm") or get_recommended_algorithm(
            data_type, config.get("balance_mode", "balanced")
        )
        
        # 确保选择的压缩器有正确的级别
        if algorithm == "zstd":
            algorithm = f"zstd"  # 使用默认级别
        elif algorithm == "gzip":
            level = config.get("compression_level", 6)
            if level == 1:
                algorithm = "gzip"  # 最快
            elif level == 9:
                algorithm = "gzip"  # 最高压缩
            else:
                algorithm = "gzip"  # 默认平衡
        
        try:
            # 获取数据
            start_time = time.time()
            data = self._get_resource_data(obj, res_type)
            
            if data is None:
                logger.warning(f"无法获取资源数据: {res_id}")
                return False
                
            # 压缩数据
            compressed, metadata = compress_data(data, algorithm)
            
            # 记录原始资源大小和压缩后大小
            original_size = len(data) if isinstance(data, (bytes, bytearray, memoryview)) else metadata["original_size"]
            compressed_size = len(compressed)
            
            ratio = compressed_size / original_size if original_size > 0 else 1.0
            original_mb = original_size / (1024 * 1024)
            compressed_mb = compressed_size / (1024 * 1024)
            
            # 更新资源信息
            self.compressed_resources[res_id] = {
                "res_id": res_id,
                "res_type": res_type,
                "original_mb": original_mb,
                "compressed_mb": compressed_mb,
                "ratio": ratio,
                "algorithm": algorithm,
                "compression_time": time.time() - start_time,
                "compressed_data": compressed,
                "metadata": metadata,
                "timestamp": time.time()
            }
            
            # 更新统计信息
            self._update_stats(res_type, original_mb, compressed_mb)
            
            # 替换原始对象
            self._replace_resource_data(obj, res_id, res_type, compressed, metadata)
            
            logger.info(f"成功压缩资源: {res_id}, 类型: {res_type}, "
                      f"大小: {original_mb:.2f}MB -> {compressed_mb:.2f}MB, "
                      f"比例: {ratio:.2f}")
            
            return True
            
        except Exception as e:
            logger.error(f"压缩资源失败: {res_id} - {e}")
            return False
    
    def decompress_resource(self, res_id: str) -> bool:
        """
        解压指定资源
        
        Args:
            res_id: 资源ID
            
        Returns:
            bool: 是否成功
        """
        # 检查资源是否已压缩
        if res_id not in self.compressed_resources:
            logger.warning(f"资源未压缩: {res_id}")
            return False
            
        if not self.resource_tracker:
            logger.error("资源跟踪器不可用")
            return False
            
        # 获取资源信息
        resource_info = self.resource_tracker.get_resource_info(res_id)
        if not resource_info:
            logger.warning(f"找不到资源: {res_id}")
            # 移除压缩记录
            if res_id in self.compressed_resources:
                del self.compressed_resources[res_id]
            return False
            
        # 获取对象引用
        obj_ref = resource_info.get("obj_ref")
        if not obj_ref:
            logger.warning(f"资源没有对象引用: {res_id}")
            return False
            
        # 获取实际对象
        obj = obj_ref()
        if obj is None:
            logger.warning(f"资源对象已被回收: {res_id}")
            return False
            
        # 获取压缩信息
        compressed_info = self.compressed_resources[res_id]
        res_type = compressed_info["res_type"]
        
        try:
            # 获取压缩数据
            compressed_data = compressed_info["compressed_data"]
            metadata = compressed_info["metadata"]
            
            # 解压数据
            start_time = time.time()
            decompressed = decompress_data(compressed_data, metadata)
            
            # 恢复原始对象
            self._restore_resource_data(obj, res_id, res_type, decompressed)
            
            logger.info(f"成功解压资源: {res_id}, 类型: {res_type}, "
                      f"耗时: {(time.time() - start_time)*1000:.1f}ms")
            
            # 移除压缩记录
            del self.compressed_resources[res_id]
            
            return True
            
        except Exception as e:
            logger.error(f"解压资源失败: {res_id} - {e}")
            return False
    
    def _get_resource_data(self, obj: Any, res_type: str) -> Optional[Union[bytes, object]]:
        """
        获取资源数据
        
        Args:
            obj: 资源对象
            res_type: 资源类型
            
        Returns:
            Optional[Union[bytes, object]]: 资源数据
        """
        try:
            # 根据资源类型获取数据
            if isinstance(obj, (bytes, bytearray, memoryview)):
                return obj
                
            elif isinstance(obj, str):
                return obj.encode('utf-8')
                
            elif isinstance(obj, np.ndarray):
                return obj.tobytes()
                
            elif hasattr(obj, "to_bytes") and callable(getattr(obj, "to_bytes")):
                return obj.to_bytes()
                
            elif hasattr(obj, "tobytes") and callable(getattr(obj, "tobytes")):
                return obj.tobytes()
                
            elif hasattr(obj, "serialize") and callable(getattr(obj, "serialize")):
                return obj.serialize()
                
            # 特定类型的处理
            elif res_type == "model_weights" or res_type == "model_weights_cache":
                # 尝试获取模型权重
                if hasattr(obj, "state_dict") and callable(getattr(obj, "state_dict")):
                    return obj.state_dict()
                    
            # 作为最后的手段，直接返回对象进行序列化
            return obj
            
        except Exception as e:
            logger.error(f"获取资源数据失败: {str(e)}")
            return None
    
    def _replace_resource_data(self, obj: Any, res_id: str, res_type: str, 
                              compressed: bytes, metadata: Dict[str, Any]) -> bool:
        """
        替换资源数据为压缩版本
        
        Args:
            obj: 资源对象
            res_id: 资源ID
            res_type: 资源类型
            compressed: 压缩数据
            metadata: 压缩元数据
            
        Returns:
            bool: 是否成功
        """
        # 将压缩标志添加到对象
        if hasattr(obj, "__dict__"):
            obj.__dict__["_compressed"] = True
            obj.__dict__["_compressed_data"] = compressed
            obj.__dict__["_compression_metadata"] = metadata
            
        # 注意：这里我们并不真正替换原始对象，而是保留压缩数据
        # 实际替换会在需要时进行（例如内存紧张时）
        
        return True
    
    def _restore_resource_data(self, obj: Any, res_id: str, res_type: str, 
                              decompressed: Any) -> bool:
        """
        恢复资源数据
        
        Args:
            obj: 资源对象
            res_id: 资源ID
            res_type: 资源类型
            decompressed: 解压后的数据
            
        Returns:
            bool: 是否成功
        """
        try:
            # 更新对象
            if hasattr(obj, "__dict__"):
                # 删除压缩标志
                if "_compressed" in obj.__dict__:
                    del obj.__dict__["_compressed"]
                if "_compressed_data" in obj.__dict__:
                    del obj.__dict__["_compressed_data"]
                if "_compression_metadata" in obj.__dict__:
                    del obj.__dict__["_compression_metadata"]
                    
            # 根据类型恢复数据
            if isinstance(obj, np.ndarray) and isinstance(decompressed, bytes):
                # 恢复NumPy数组
                shape = obj.shape
                dtype = obj.dtype
                
                # 确保大小匹配
                expected_size = np.prod(shape) * dtype.itemsize
                if len(decompressed) == expected_size:
                    # 将字节复制回数组
                    new_array = np.frombuffer(decompressed, dtype=dtype).reshape(shape)
                    obj.flat = new_array.flat
                    
            elif hasattr(obj, "from_bytes") and callable(getattr(obj, "from_bytes")):
                obj.from_bytes(decompressed)
                
            elif hasattr(obj, "deserialize") and callable(getattr(obj, "deserialize")):
                obj.deserialize(decompressed)
                
            # 特定类型的处理
            elif res_type == "model_weights" or res_type == "model_weights_cache":
                if hasattr(obj, "load_state_dict") and callable(getattr(obj, "load_state_dict")):
                    obj.load_state_dict(decompressed)
            
            return True
            
        except Exception as e:
            logger.error(f"恢复资源数据失败: {str(e)}")
            return False
    
    def _update_stats(self, res_type: str, original_mb: float, compressed_mb: float) -> None:
        """
        更新压缩统计信息
        
        Args:
            res_type: 资源类型
            original_mb: 原始大小(MB)
            compressed_mb: 压缩后大小(MB)
        """
        # 更新总体统计
        self.stats["total_compressed_resources"] += 1
        self.stats["total_original_mb"] += original_mb
        self.stats["total_compressed_mb"] += compressed_mb
        
        # 更新平均压缩率
        if self.stats["total_original_mb"] > 0:
            self.stats["average_ratio"] = self.stats["total_compressed_mb"] / self.stats["total_original_mb"]
        
        # 更新类型统计
        if res_type not in self.stats["compression_by_type"]:
            self.stats["compression_by_type"][res_type] = {
                "count": 0,
                "original_mb": 0.0,
                "compressed_mb": 0.0,
                "ratio": 0.0
            }
            
        type_stats = self.stats["compression_by_type"][res_type]
        type_stats["count"] += 1
        type_stats["original_mb"] += original_mb
        type_stats["compressed_mb"] += compressed_mb
        
        if type_stats["original_mb"] > 0:
            type_stats["ratio"] = type_stats["compressed_mb"] / type_stats["original_mb"]
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取压缩统计信息
        
        Returns:
            Dict: 统计信息
        """
        # 复制统计信息
        stats = dict(self.stats)
        
        # 添加当前压缩资源数量
        stats["current_compressed_resources"] = len(self.compressed_resources)
        
        # 添加每种算法的统计
        algorithm_stats = {}
        
        for info in self.compressed_resources.values():
            alg = info["algorithm"]
            if alg not in algorithm_stats:
                algorithm_stats[alg] = {
                    "count": 0,
                    "original_mb": 0.0,
                    "compressed_mb": 0.0,
                    "ratio": 0.0
                }
                
            alg_stats = algorithm_stats[alg]
            alg_stats["count"] += 1
            alg_stats["original_mb"] += info["original_mb"]
            alg_stats["compressed_mb"] += info["compressed_mb"]
            
            if alg_stats["original_mb"] > 0:
                alg_stats["ratio"] = alg_stats["compressed_mb"] / alg_stats["original_mb"]
        
        stats["compression_by_algorithm"] = algorithm_stats
        
        # 添加节省的内存
        stats["saved_mb"] = stats["total_original_mb"] - stats["total_compressed_mb"]
        
        return stats
    
    def compress_all_resources(self, type_filter: Optional[str] = None, 
                              min_size_mb: float = 1.0) -> Dict[str, Any]:
        """
        压缩所有符合条件的资源
        
        Args:
            type_filter: 资源类型过滤器，None表示所有类型
            min_size_mb: 最小资源大小(MB)
            
        Returns:
            Dict: 压缩结果统计
        """
        if not self.resource_tracker:
            return {"error": "资源跟踪器不可用"}
            
        results = {
            "attempted": 0,
            "succeeded": 0,
            "failed": 0,
            "total_original_mb": 0.0,
            "total_compressed_mb": 0.0,
            "saved_mb": 0.0
        }
        
        # 获取所有资源
        resources = self.resource_tracker.get_all_resources()
        
        for res_id, info in resources.items():
            # 检查类型过滤器
            if type_filter and info.get("res_type") != type_filter:
                continue
                
            # 检查大小
            size_mb = info.get("size_estimate", 0)
            if size_mb < min_size_mb:
                continue
                
            # 如果已经压缩过，跳过
            if res_id in self.compressed_resources:
                continue
                
            # 尝试压缩
            results["attempted"] += 1
            
            success = self.compress_resource(res_id)
            
            if success:
                results["succeeded"] += 1
                
                # 更新统计
                compressed_info = self.compressed_resources.get(res_id, {})
                results["total_original_mb"] += compressed_info.get("original_mb", 0)
                results["total_compressed_mb"] += compressed_info.get("compressed_mb", 0)
            else:
                results["failed"] += 1
        
        # 计算节省的内存
        results["saved_mb"] = results["total_original_mb"] - results["total_compressed_mb"]
        
        return results
    
    def decompress_all_resources(self, type_filter: Optional[str] = None) -> Dict[str, Any]:
        """
        解压所有压缩的资源
        
        Args:
            type_filter: 资源类型过滤器，None表示所有类型
            
        Returns:
            Dict: 解压结果统计
        """
        results = {
            "attempted": 0,
            "succeeded": 0,
            "failed": 0,
            "released_mb": 0.0
        }
        
        # 获取所有压缩的资源ID
        compressed_ids = list(self.compressed_resources.keys())
        
        for res_id in compressed_ids:
            # 获取压缩信息
            info = self.compressed_resources.get(res_id)
            if not info:
                continue
                
            # 检查类型过滤器
            if type_filter and info.get("res_type") != type_filter:
                continue
                
            # 尝试解压
            results["attempted"] += 1
            
            success = self.decompress_resource(res_id)
            
            if success:
                results["succeeded"] += 1
                results["released_mb"] += info.get("original_mb", 0) - info.get("compressed_mb", 0)
            else:
                results["failed"] += 1
        
        return results
    
    def update_compression_config(self, res_type: str, config: Dict[str, Any]) -> bool:
        """
        更新特定资源类型的压缩配置
        
        Args:
            res_type: 资源类型
            config: 配置字典
            
        Returns:
            bool: 是否成功
        """
        if res_type not in self.compression_config and res_type != "default":
            self.compression_config[res_type] = dict(self.compression_config["default"])
            
        # 更新配置
        for key, value in config.items():
            self.compression_config[res_type][key] = value
            
        logger.info(f"已更新 {res_type} 的压缩配置: {config}")
        
        return True
    
    def get_compression_config(self, res_type: Optional[str] = None) -> Dict[str, Any]:
        """
        获取压缩配置
        
        Args:
            res_type: 资源类型，None表示获取所有配置
            
        Returns:
            Dict: 压缩配置
        """
        if res_type:
            return self._get_compression_config(res_type)
        return self.compression_config

# 单例模式
_compression_manager = None

def get_compression_manager() -> CompressionManager:
    """
    获取压缩管理器单例
    
    Returns:
        CompressionManager: 压缩管理器实例
    """
    global _compression_manager
    if _compression_manager is None:
        _compression_manager = CompressionManager()
    return _compression_manager


# 暴露便捷函数
def compress_resource(res_id: str) -> bool:
    """
    压缩指定资源的便捷函数
    
    Args:
        res_id: 资源ID
        
    Returns:
        bool: 是否成功
    """
    manager = get_compression_manager()
    return manager.compress_resource(res_id)

def decompress_resource(res_id: str) -> bool:
    """
    解压指定资源的便捷函数
    
    Args:
        res_id: 资源ID
        
    Returns:
        bool: 是否成功
    """
    manager = get_compression_manager()
    return manager.decompress_resource(res_id)

def compress_all_resources(type_filter: Optional[str] = None, 
                          min_size_mb: float = 1.0) -> Dict[str, Any]:
    """
    压缩所有符合条件的资源的便捷函数
    
    Args:
        type_filter: 资源类型过滤器，None表示所有类型
        min_size_mb: 最小资源大小(MB)
        
    Returns:
        Dict: 压缩结果统计
    """
    manager = get_compression_manager()
    return manager.compress_all_resources(type_filter, min_size_mb)

def get_compression_stats() -> Dict[str, Any]:
    """
    获取压缩统计信息的便捷函数
    
    Returns:
        Dict: 统计信息
    """
    manager = get_compression_manager()
    return manager.get_stats()


# 测试代码
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    # 获取压缩管理器
    manager = get_compression_manager()
    
    # 打印配置
    print("\n压缩配置:")
    for res_type, config in manager.get_compression_config().items():
        print(f"{res_type}: {config}")
    
    # 测试压缩
    if has_resource_tracker:
        # 创建测试资源
        from src.memory.resource_tracker import get_resource_tracker

# 内存使用警告阈值（百分比）
MEMORY_WARNING_THRESHOLD = 80

def test_resource_tracker():
    """测试资源跟踪器"""
    tracker = get_resource_tracker()

    # 注册测试资源
    test_data = b"Test resource data" * 1000  # 约10KB
    res_id = tracker.register("test_buffer", "test_compression", resource=test_data)

    if res_id:
        print(f"\n注册测试资源: {res_id}")

        # 压缩资源
        print("压缩资源...")
        success = manager.compress_resource(res_id)

        if success:
            # 打印统计
            stats = manager.get_stats()
            print(f"\n压缩统计:")
            print(f"压缩资源数: {stats['total_compressed_resources']}")
            print(f"原始大小: {stats['total_original_mb']:.2f}MB")
            print(f"压缩后大小: {stats['total_compressed_mb']:.2f}MB")
            print(f"压缩率: {stats['average_ratio']:.2f}")
            print(f"节省内存: {stats['total_original_mb'] - stats['total_compressed_mb']:.2f}MB")

            # 解压资源
            print("\n解压资源...")
            manager.decompress_resource(res_id)

        # 清理
        tracker.release(res_id)
    else:
        print("资源跟踪器不可用，跳过压缩测试") 