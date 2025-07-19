#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
分块压缩模块

提供分块压缩功能，优化大型数据的处理效率
"""

import os
import io
import logging
import time
from typing import Dict, List, Any, Tuple, Optional, Union, BinaryIO
import struct
import pickle
import hashlib
import uuid

# 导入压缩模块
from src.compression.compressors import get_compressor, CompressorBase

# 日志配置
logger = logging.getLogger("ChunkedCompression")

# 分块压缩的头魔术字符串
CHUNK_MAGIC = b"VCD"  # VisionAI Chunked Data

# 分块压缩格式版本
FORMAT_VERSION = 1

class ChunkedCompressor:
    """分块压缩器类"""
    
    def __init__(self, 
                 algorithm: str = "zstd", 
                 chunk_size: int = 4 * 1024 * 1024,  # 默认4MB
                 compression_level: Optional[int] = None):
        """
        初始化分块压缩器
        
        Args:
            algorithm: 压缩算法名称
            chunk_size: 分块大小(字节)
            compression_level: 压缩级别(可选)
        """
        self.algorithm = algorithm
        self.chunk_size = chunk_size
        self.compression_level = compression_level
        
        # 获取压缩器
        self.compressor = get_compressor(algorithm)
        if not self.compressor:
            logger.warning(f"找不到压缩算法 '{algorithm}'，使用gzip")
            self.algorithm = "gzip"
            self.compressor = get_compressor("gzip")
        
        # 设置压缩级别(如果可能)
        if compression_level is not None and hasattr(self.compressor, "level"):
            self.compressor.level = compression_level
    
    def compress(self, data: Union[bytes, bytearray, memoryview]) -> bytes:
        """
        压缩数据，大于chunk_size的数据将被分块压缩
        
        Args:
            data: 待压缩数据
            
        Returns:
            bytes: 压缩后的数据
        """
        data_size = len(data)
        
        # 如果数据小于块大小，直接压缩
        if data_size <= self.chunk_size:
            return self._compress_single(data)
        
        # 分块压缩
        return self._compress_chunked(data)
    
    def _compress_single(self, data: Union[bytes, bytearray, memoryview]) -> bytes:
        """
        单块压缩实现
        
        Args:
            data: 待压缩数据
            
        Returns:
            bytes: 压缩后的数据，包含头信息
        """
        # 压缩数据
        compressed = self.compressor.compress(data)
        
        # 构建头部
        header = self._build_header(len(data), len(compressed), is_chunked=False)
        
        # 组合头部和压缩数据
        return header + compressed
    
    def _compress_chunked(self, data: Union[bytes, bytearray, memoryview]) -> bytes:
        """
        分块压缩实现
        
        Args:
            data: 待压缩数据
            
        Returns:
            bytes: 压缩后的数据，包含头信息和块信息
        """
        data_size = len(data)
        chunks = []
        chunk_infos = []
        total_compressed_size = 0
        
        # 分块压缩
        for i in range(0, data_size, self.chunk_size):
            chunk = data[i:min(i + self.chunk_size, data_size)]
            chunk_original_size = len(chunk)
            
            # 压缩块
            compressed_chunk = self.compressor.compress(chunk)
            chunk_compressed_size = len(compressed_chunk)
            
            # 记录块信息
            chunk_infos.append({
                "original_size": chunk_original_size,
                "compressed_size": chunk_compressed_size,
                "offset": total_compressed_size
            })
            
            # 更新总压缩大小
            total_compressed_size += chunk_compressed_size
            
            # 添加到块列表
            chunks.append(compressed_chunk)
        
        # 序列化块信息
        chunk_infos_data = pickle.dumps(chunk_infos)
        
        # 构建头部
        header = self._build_header(
            data_size, 
            total_compressed_size, 
            is_chunked=True,
            num_chunks=len(chunks),
            chunk_infos_size=len(chunk_infos_data)
        )
        
        # 组合所有部分
        result = bytearray(header)
        result.extend(chunk_infos_data)
        for chunk in chunks:
            result.extend(chunk)
        
        return bytes(result)
    
    def _build_header(self, 
                     original_size: int, 
                     compressed_size: int, 
                     is_chunked: bool = False,
                     num_chunks: int = 1,
                     chunk_infos_size: int = 0) -> bytes:
        """
        构建压缩头部
        
        Args:
            original_size: 原始数据大小
            compressed_size: 压缩后大小
            is_chunked: 是否分块
            num_chunks: 块数
            chunk_infos_size: 块信息大小
            
        Returns:
            bytes: 头部数据
        """
        # 生成唯一ID
        uid = uuid.uuid4().bytes[:8]  # 使用8字节UUID
        
        # 创建头部(48字节固定大小)
        header = struct.pack(
            "<3sBBHQ8sQQII",
            CHUNK_MAGIC,             # 3字节魔术字符串
            FORMAT_VERSION,          # 1字节版本号
            1 if is_chunked else 0,  # 1字节标志位
            len(self.algorithm),     # 2字节算法名长度
            int(time.time()),        # 8字节时间戳
            uid,                     # 8字节UUID
            original_size,           # 8字节原始大小
            compressed_size,         # 8字节压缩后大小
            num_chunks,              # 4字节块数
            chunk_infos_size         # 4字节块信息大小
        )
        
        # 添加算法名
        header += self.algorithm.encode("utf-8")
        
        return header
    
    def decompress(self, data: Union[bytes, bytearray, memoryview]) -> bytes:
        """
        解压数据
        
        Args:
            data: 压缩数据
            
        Returns:
            bytes: 解压后的数据
        """
        # 解析头部
        header, algorithm, is_chunked, chunk_infos_size, header_size = self._parse_header(data)
        
        # 获取压缩器
        compressor = get_compressor(algorithm)
        if not compressor:
            raise ValueError(f"找不到解压算法 '{algorithm}'")
        
        # 如果是单块，直接解压
        if not is_chunked:
            compressed_data = data[header_size:]
            return compressor.decompress(compressed_data)
        
        # 解析块信息
        chunk_infos_data = data[header_size:header_size + chunk_infos_size]
        chunk_infos = pickle.loads(chunk_infos_data)
        data_offset = header_size + chunk_infos_size
        
        # 分块解压
        result = bytearray()
        for chunk_info in chunk_infos:
            # 获取块的压缩数据
            chunk_offset = data_offset + chunk_info["offset"]
            chunk_size = chunk_info["compressed_size"]
            compressed_chunk = data[chunk_offset:chunk_offset + chunk_size]
            
            # 解压块
            decompressed_chunk = compressor.decompress(compressed_chunk)
            
            # 添加到结果
            result.extend(decompressed_chunk)
        
        return bytes(result)
    
    def _parse_header(self, data: Union[bytes, bytearray, memoryview]) -> Tuple[Dict[str, Any], str, bool, int, int]:
        """
        解析压缩头部
        
        Args:
            data: 压缩数据
            
        Returns:
            Tuple: (头部信息, 算法名, 是否分块, 块信息大小, 头部大小)
        """
        # 检查魔术字符串
        if data[:3] != CHUNK_MAGIC:
            raise ValueError("无效的压缩数据格式")
        
        # 解析固定部分头部(48字节)
        magic, version, is_chunked, alg_len, timestamp, uid, original_size, compressed_size, num_chunks, chunk_infos_size = struct.unpack(
            "<3sBBHQ8sQQII", data[:48]
        )
        
        # 检查版本
        if version != FORMAT_VERSION:
            raise ValueError(f"不支持的格式版本: {version}")
        
        # 获取算法名
        algorithm = data[48:48 + alg_len].decode("utf-8")
        
        # 头部总大小
        header_size = 48 + alg_len
        
        # 构建头部信息
        header = {
            "version": version,
            "is_chunked": bool(is_chunked),
            "algorithm": algorithm,
            "timestamp": timestamp,
            "uid": uid.hex(),
            "original_size": original_size,
            "compressed_size": compressed_size,
            "num_chunks": num_chunks
        }
        
        return header, algorithm, bool(is_chunked), chunk_infos_size, header_size

    def get_header_info(self, data: Union[bytes, bytearray, memoryview]) -> Dict[str, Any]:
        """
        获取压缩数据的头部信息
        
        Args:
            data: 压缩数据
            
        Returns:
            Dict: 头部信息
        """
        header, algorithm, is_chunked, _, _ = self._parse_header(data)
        return header

# 便捷函数
def compress_chunked(data: Union[bytes, bytearray, memoryview], 
                     algorithm: str = "zstd", 
                     chunk_size: int = 4 * 1024 * 1024,
                     compression_level: Optional[int] = None) -> bytes:
    """
    分块压缩数据的便捷函数
    
    Args:
        data: 待压缩数据
        algorithm: 压缩算法
        chunk_size: 分块大小(字节)
        compression_level: 压缩级别(可选)
        
    Returns:
        bytes: 压缩后的数据
    """
    compressor = ChunkedCompressor(algorithm, chunk_size, compression_level)
    return compressor.compress(data)

def decompress_chunked(data: Union[bytes, bytearray, memoryview]) -> bytes:
    """
    解压分块压缩数据的便捷函数
    
    Args:
        data: 压缩数据
        
    Returns:
        bytes: 解压后的数据
    """
    compressor = ChunkedCompressor()
    return compressor.decompress(data)

def get_chunked_header_info(data: Union[bytes, bytearray, memoryview]) -> Dict[str, Any]:
    """
    获取压缩数据头部信息的便捷函数
    
    Args:
        data: 压缩数据
        
    Returns:
        Dict: 头部信息
    """
    compressor = ChunkedCompressor()
    return compressor.get_header_info(data)


# 测试代码
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    # 创建测试数据
    test_data_small = b"This is a small test data" * 100  # ~2KB
    test_data_large = os.urandom(10 * 1024 * 1024)  # 10MB随机数据
    
    # 测试小数据压缩(不分块)
    logger.info("Testing small data compression (single chunk)...")
    compressor = ChunkedCompressor("zstd", chunk_size=1024*1024)
    
    start_time = time.time()
    compressed_small = compressor.compress(test_data_small)
    compress_time = time.time() - start_time
    
    start_time = time.time()
    decompressed_small = compressor.decompress(compressed_small)
    decompress_time = time.time() - start_time
    
    logger.info(f"Original size: {len(test_data_small)/1024:.2f}KB, "
               f"Compressed: {len(compressed_small)/1024:.2f}KB, "
               f"Ratio: {len(compressed_small)/len(test_data_small):.2f}, "
               f"Compress time: {compress_time*1000:.1f}ms, "
               f"Decompress time: {decompress_time*1000:.1f}ms")
    
    assert decompressed_small == test_data_small, "Small data decompression mismatch"
    
    # 测试大数据压缩(分块)
    logger.info("\nTesting large data chunked compression...")
    
    # 使用1MB块大小
    compressor = ChunkedCompressor("zstd", chunk_size=1*1024*1024)
    
    start_time = time.time()
    compressed_large = compressor.compress(test_data_large)
    compress_time = time.time() - start_time
    
    start_time = time.time()
    decompressed_large = compressor.decompress(compressed_large)
    decompress_time = time.time() - start_time
    
    # 获取头部信息
    header_info = compressor.get_header_info(compressed_large)
    
    logger.info(f"Original size: {len(test_data_large)/1024/1024:.2f}MB, "
               f"Compressed: {len(compressed_large)/1024/1024:.2f}MB, "
               f"Ratio: {len(compressed_large)/len(test_data_large):.2f}, "
               f"Compress time: {compress_time*1000:.1f}ms, "
               f"Decompress time: {decompress_time*1000:.1f}ms")
    
    logger.info(f"Header info: {header_info}")
    
    assert decompressed_large == test_data_large, "Large data decompression mismatch"
    
    logger.info("Chunked compression test successful!") 