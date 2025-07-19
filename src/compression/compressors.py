#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
压缩器模块

定义和管理各种压缩算法，提供统一的接口
"""

import logging
import time
from typing import Dict, Any, List, Optional, Callable, Tuple, Union
import io
import pickle
import gzip
import bz2
import lzma

# 条件导入，可能不是所有系统都有这些库
try:
    import zstd
    HAS_ZSTD = True
except ImportError:
    HAS_ZSTD = False

try:
    import lz4.frame
    HAS_LZ4 = True
except ImportError:
    HAS_LZ4 = False

try:
    import snappy
    HAS_SNAPPY = True
except ImportError:
    HAS_SNAPPY = False

# 配置日志
logger = logging.getLogger("Compressors")

# 压缩器注册表
_COMPRESSORS = {}

class CompressorBase:
    """压缩器基类"""
    
    def __init__(self, name: str, description: str = ""):
        """
        初始化压缩器
        
        Args:
            name: 压缩器名称
            description: 压缩器描述
        """
        self.name = name
        self.description = description
        
    def compress(self, data: Union[bytes, bytearray, memoryview]) -> bytes:
        """
        压缩数据
        
        Args:
            data: 待压缩的数据
            
        Returns:
            bytes: 压缩后的数据
        """
        raise NotImplementedError("子类必须实现compress方法")
        
    def decompress(self, data: Union[bytes, bytearray, memoryview]) -> bytes:
        """
        解压数据
        
        Args:
            data: 压缩的数据
            
        Returns:
            bytes: 解压后的数据
        """
        raise NotImplementedError("子类必须实现decompress方法")
    
    def get_info(self) -> Dict[str, Any]:
        """
        获取压缩器信息
        
        Returns:
            Dict: 压缩器信息
        """
        return {
            "name": self.name,
            "description": self.description,
            "available": True
        }
    
    def __str__(self) -> str:
        return f"{self.name} - {self.description}"


class GzipCompressor(CompressorBase):
    """Gzip压缩器"""
    
    def __init__(self, level: int = 6):
        """
        初始化Gzip压缩器
        
        Args:
            level: 压缩级别，1-9，越大压缩率越高但速度越慢
        """
        super().__init__("gzip", "通用压缩算法，平衡的压缩率和速度")
        self.level = level
        
    def compress(self, data: Union[bytes, bytearray, memoryview]) -> bytes:
        """使用gzip压缩数据"""
        return gzip.compress(data, compresslevel=self.level)
        
    def decompress(self, data: Union[bytes, bytearray, memoryview]) -> bytes:
        """使用gzip解压数据"""
        return gzip.decompress(data)
    
    def get_info(self) -> Dict[str, Any]:
        """获取压缩器信息"""
        info = super().get_info()
        info["level"] = self.level
        return info


class Bzip2Compressor(CompressorBase):
    """Bzip2压缩器"""
    
    def __init__(self, level: int = 9):
        """
        初始化Bzip2压缩器
        
        Args:
            level: 压缩级别，1-9，越大压缩率越高但速度越慢
        """
        super().__init__("bzip2", "高压缩率，但速度较慢")
        self.level = level
        
    def compress(self, data: Union[bytes, bytearray, memoryview]) -> bytes:
        """使用bzip2压缩数据"""
        return bz2.compress(data, compresslevel=self.level)
        
    def decompress(self, data: Union[bytes, bytearray, memoryview]) -> bytes:
        """使用bzip2解压数据"""
        return bz2.decompress(data)
    
    def get_info(self) -> Dict[str, Any]:
        """获取压缩器信息"""
        info = super().get_info()
        info["level"] = self.level
        return info


class LzmaCompressor(CompressorBase):
    """LZMA压缩器"""
    
    def __init__(self, preset: int = 6):
        """
        初始化LZMA压缩器
        
        Args:
            preset: 压缩预设级别，0-9，越大压缩率越高但速度越慢
        """
        super().__init__("lzma", "很高的压缩率，速度很慢")
        self.preset = preset
        
    def compress(self, data: Union[bytes, bytearray, memoryview]) -> bytes:
        """使用lzma压缩数据"""
        return lzma.compress(data, preset=self.preset)
        
    def decompress(self, data: Union[bytes, bytearray, memoryview]) -> bytes:
        """使用lzma解压数据"""
        return lzma.decompress(data)
    
    def get_info(self) -> Dict[str, Any]:
        """获取压缩器信息"""
        info = super().get_info()
        info["preset"] = self.preset
        return info


class ZstdCompressor(CompressorBase):
    """Zstandard压缩器"""
    
    def __init__(self, level: int = 3):
        """
        初始化Zstandard压缩器
        
        Args:
            level: 压缩级别，1-22，越大压缩率越高但速度越慢
        """
        super().__init__("zstd", "高性能压缩算法，平衡速度和压缩率")
        self.level = level
        
        if not HAS_ZSTD:
            logger.warning("zstd库未安装，将返回原始数据")
        
    def compress(self, data: Union[bytes, bytearray, memoryview]) -> bytes:
        """使用zstd压缩数据"""
        if HAS_ZSTD:
            return zstd.compress(data, self.level)
        return bytes(data)
        
    def decompress(self, data: Union[bytes, bytearray, memoryview]) -> bytes:
        """使用zstd解压数据"""
        if HAS_ZSTD:
            return zstd.decompress(data)
        return bytes(data)
    
    def get_info(self) -> Dict[str, Any]:
        """获取压缩器信息"""
        info = super().get_info()
        info["level"] = self.level
        info["available"] = HAS_ZSTD
        return info


class Lz4Compressor(CompressorBase):
    """LZ4压缩器"""
    
    def __init__(self, level: int = 0):
        """
        初始化LZ4压缩器
        
        Args:
            level: 压缩级别，0-16，越大压缩率越高但速度越慢
        """
        super().__init__("lz4", "极快的压缩算法，适合实时数据")
        self.level = level
        
        if not HAS_LZ4:
            logger.warning("lz4库未安装，将返回原始数据")
        
    def compress(self, data: Union[bytes, bytearray, memoryview]) -> bytes:
        """使用lz4压缩数据"""
        if HAS_LZ4:
            return lz4.frame.compress(data, compression_level=self.level)
        return bytes(data)
        
    def decompress(self, data: Union[bytes, bytearray, memoryview]) -> bytes:
        """使用lz4解压数据"""
        if HAS_LZ4:
            return lz4.frame.decompress(data)
        return bytes(data)
    
    def get_info(self) -> Dict[str, Any]:
        """获取压缩器信息"""
        info = super().get_info()
        info["level"] = self.level
        info["available"] = HAS_LZ4
        return info


class SnappyCompressor(CompressorBase):
    """Snappy压缩器"""
    
    def __init__(self):
        """初始化Snappy压缩器"""
        super().__init__("snappy", "Google的超快压缩算法，压缩率适中")
        
        if not HAS_SNAPPY:
            logger.warning("snappy库未安装，将返回原始数据")
        
    def compress(self, data: Union[bytes, bytearray, memoryview]) -> bytes:
        """使用snappy压缩数据"""
        if HAS_SNAPPY:
            return snappy.compress(bytes(data))
        return bytes(data)
        
    def decompress(self, data: Union[bytes, bytearray, memoryview]) -> bytes:
        """使用snappy解压数据"""
        if HAS_SNAPPY:
            return snappy.decompress(data)
        return bytes(data)
    
    def get_info(self) -> Dict[str, Any]:
        """获取压缩器信息"""
        info = super().get_info()
        info["available"] = HAS_SNAPPY
        return info


class NoCompression(CompressorBase):
    """无压缩"""
    
    def __init__(self):
        """初始化无压缩处理器"""
        super().__init__("none", "不进行压缩，仅用于测试或基准比较")
        
    def compress(self, data: Union[bytes, bytearray, memoryview]) -> bytes:
        """直接返回原始数据"""
        return bytes(data)
        
    def decompress(self, data: Union[bytes, bytearray, memoryview]) -> bytes:
        """直接返回原始数据"""
        return bytes(data)


# 注册默认压缩器
def register_default_compressors():
    """注册所有默认的压缩器"""
    # Gzip (默认不同压缩级别)
    register_compressor(GzipCompressor(level=1))  # 速度优先
    register_compressor(GzipCompressor(level=6))  # 默认平衡
    register_compressor(GzipCompressor(level=9))  # 压缩率优先
    
    # Bzip2
    register_compressor(Bzip2Compressor())
    
    # LZMA
    register_compressor(LzmaCompressor())
    
    # Zstandard (如果可用)
    if HAS_ZSTD:
        register_compressor(ZstdCompressor(level=1))  # 速度优先
        register_compressor(ZstdCompressor(level=3))  # 默认平衡
        register_compressor(ZstdCompressor(level=10))  # 更高压缩率
        register_compressor(ZstdCompressor(level=22))  # 最高压缩率
    
    # LZ4 (如果可用)
    if HAS_LZ4:
        register_compressor(Lz4Compressor(level=0))  # 速度优先
        register_compressor(Lz4Compressor(level=9))  # 更高压缩率
    
    # Snappy (如果可用)
    if HAS_SNAPPY:
        register_compressor(SnappyCompressor())
    
    # 无压缩（用于基准比较）
    register_compressor(NoCompression())
    
    logger.info(f"已注册 {len(_COMPRESSORS)} 个压缩器")


def register_compressor(compressor: CompressorBase) -> None:
    """
    注册压缩器
    
    Args:
        compressor: 压缩器实例
    """
    _COMPRESSORS[compressor.name] = compressor


def get_compressor(name: str) -> Optional[CompressorBase]:
    """
    获取指定名称的压缩器
    
    Args:
        name: 压缩器名称
        
    Returns:
        Optional[CompressorBase]: 压缩器实例或None
    """
    # 确保压缩器已注册
    if not _COMPRESSORS:
        register_default_compressors()
        
    if name not in _COMPRESSORS:
        names = list(_COMPRESSORS.keys())
        logger.warning(f"找不到压缩器 '{name}'，可用压缩器: {names}")
        return None
        
    return _COMPRESSORS[name]


def get_available_compressors() -> List[str]:
    """
    获取所有可用的压缩器名称
    
    Returns:
        List[str]: 压缩器名称列表
    """
    # 确保压缩器已注册
    if not _COMPRESSORS:
        register_default_compressors()
        
    return list(_COMPRESSORS.keys())


def compress_data(data: Union[bytes, bytearray, memoryview, object], 
                 algorithm: str = "gzip") -> Tuple[bytes, Dict[str, Any]]:
    """
    压缩数据的便捷函数
    
    Args:
        data: 要压缩的数据，如果不是bytes类型，将自动序列化
        algorithm: 压缩算法名称
        
    Returns:
        Tuple[bytes, Dict]: 压缩后的数据和元数据
    """
    # 确保压缩器已注册
    if not _COMPRESSORS:
        register_default_compressors()
        
    # 获取压缩器
    compressor = get_compressor(algorithm)
    if not compressor:
        logger.warning(f"未找到压缩器 '{algorithm}'，使用无压缩")
        compressor = NoCompression()
        
    # 准备元数据
    metadata = {
        "algorithm": compressor.name,
        "timestamp": time.time()
    }
    
    # 如果不是bytes，先序列化
    if not isinstance(data, (bytes, bytearray, memoryview)):
        logger.debug("输入不是bytes类型，进行序列化")
        data = pickle.dumps(data)
        metadata["serialized"] = True
    else:
        metadata["serialized"] = False
    
    # 记录原始大小
    metadata["original_size"] = len(data)
    
    # 压缩
    start_time = time.time()
    compressed = compressor.compress(data)
    compress_time = time.time() - start_time
    
    # 更新元数据
    metadata["compressed_size"] = len(compressed)
    metadata["ratio"] = len(compressed) / max(len(data), 1)
    metadata["compress_time_ms"] = compress_time * 1000
    
    return compressed, metadata


def decompress_data(data: Union[bytes, bytearray, memoryview],
                   metadata: Dict[str, Any]) -> object:
    """
    解压数据的便捷函数
    
    Args:
        data: 压缩的数据
        metadata: 压缩元数据
        
    Returns:
        解压后的数据
    """
    # 确保压缩器已注册
    if not _COMPRESSORS:
        register_default_compressors()
        
    # 获取算法
    algorithm = metadata.get("algorithm", "gzip")
    
    # 获取压缩器
    compressor = get_compressor(algorithm)
    if not compressor:
        logger.warning(f"未找到解压器 '{algorithm}'，假设无压缩")
        compressor = NoCompression()
    
    # 解压
    start_time = time.time()
    decompressed = compressor.decompress(data)
    decompress_time = time.time() - start_time
    
    logger.debug(f"解压耗时 {decompress_time*1000:.2f}ms")
    
    # 如果之前进行了序列化，需要反序列化
    if metadata.get("serialized", False):
        logger.debug("数据已序列化，进行反序列化")
        return pickle.loads(decompressed)
    
    return decompressed


# 确保默认压缩器已注册
register_default_compressors()


# 测试代码
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    # 测试数据
    test_data = b"This is test data" * 1000  # 约17KB
    
    print(f"\n原始数据大小: {len(test_data) / 1024:.2f}KB")
    
    # 测试所有压缩器
    for name in get_available_compressors():
        compressor = get_compressor(name)
        if not compressor:
            continue
            
        # 如果压缩器不可用，跳过
        if not compressor.get_info().get("available", True):
            continue
        
        # 压缩
        start_time = time.time()
        compressed = compressor.compress(test_data)
        compress_time = time.time() - start_time
        
        # 解压
        start_time = time.time()
        decompressed = compressor.decompress(compressed)
        decompress_time = time.time() - start_time
        
        # 验证
        assert decompressed == test_data, f"解压结果不匹配: {name}"
        
        # 打印结果
        ratio = len(compressed) / len(test_data)
        print(f"{name.ljust(20)}: "
              f"压缩率 {ratio:.2f}, "
              f"大小 {len(compressed)/1024:.2f}KB, "
              f"压缩 {compress_time*1000:.2f}ms, "
              f"解压 {decompress_time*1000:.2f}ms")
    
    # 测试便捷函数
    compressed, metadata = compress_data(test_data, "zstd")
    decompressed = decompress_data(compressed, metadata)
    
    print("\n压缩元数据:", metadata)
    print(f"解压后大小: {len(decompressed) / 1024:.2f}KB") 