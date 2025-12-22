#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
压缩核心模块

提供基础的压缩和解压功能，支持多种算法
"""

import logging
from typing import Dict, Any, Optional, Tuple
import gzip
import bz2
import lzma

logger = logging.getLogger("CompressionCore")

# 尝试导入可选的压缩库
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


def compress(data: bytes, algo: str = "gzip", level: int = 6, with_metadata: bool = False) -> Tuple[bytes, Optional[Dict[str, Any]]]:
    """
    压缩数据
    
    Args:
        data: 待压缩数据
        algo: 压缩算法 (gzip, bz2, lzma, zstd, lz4, snappy)
        level: 压缩级别 (1-9)
        with_metadata: 是否返回元数据
        
    Returns:
        (压缩数据, 元数据字典或None)
    """
    metadata = {
        "algorithm": algo,
        "level": level,
        "original_size": len(data),
    } if with_metadata else None
    
    try:
        if algo == "gzip":
            compressed = gzip.compress(data, compresslevel=level)
        elif algo == "bz2":
            compressed = bz2.compress(data, compresslevel=level)
        elif algo == "lzma":
            compressed = lzma.compress(data, preset=level)
        elif algo == "zstd":
            if not HAS_ZSTD:
                logger.warning("zstd未安装，回退到gzip")
                return compress(data, "gzip", level, with_metadata)
            cctx = zstd.ZstdCompressor(level=level)
            compressed = cctx.compress(data)
        elif algo == "lz4":
            if not HAS_LZ4:
                logger.warning("lz4未安装，回退到gzip")
                return compress(data, "gzip", level, with_metadata)
            compressed = lz4.frame.compress(data, compression_level=level)
        elif algo == "snappy":
            if not HAS_SNAPPY:
                logger.warning("snappy未安装，回退到gzip")
                return compress(data, "gzip", level, with_metadata)
            compressed = snappy.compress(data)
        else:
            logger.warning(f"未知算法: {algo}，使用gzip")
            return compress(data, "gzip", level, with_metadata)
        
        if metadata:
            metadata["compressed_size"] = len(compressed)
            metadata["compression_ratio"] = len(compressed) / len(data) if len(data) > 0 else 0
        
        return compressed, metadata
        
    except Exception as e:
        logger.error(f"压缩失败: {e}")
        raise


def decompress(data: bytes, metadata: Optional[Dict[str, Any]] = None, algo: str = "gzip") -> bytes:
    """
    解压数据
    
    Args:
        data: 待解压数据
        metadata: 元数据字典（包含算法信息）
        algo: 压缩算法
        
    Returns:
        解压后的数据
    """
    # 从元数据中获取算法
    if metadata and "algorithm" in metadata:
        algo = metadata["algorithm"]
    
    try:
        if algo == "gzip":
            return gzip.decompress(data)
        elif algo == "bz2":
            return bz2.decompress(data)
        elif algo == "lzma":
            return lzma.decompress(data)
        elif algo == "zstd":
            if not HAS_ZSTD:
                logger.warning("zstd未安装，无法解压")
                raise ImportError("zstd not installed")
            dctx = zstd.ZstdDecompressor()
            return dctx.decompress(data)
        elif algo == "lz4":
            if not HAS_LZ4:
                logger.warning("lz4未安装，无法解压")
                raise ImportError("lz4 not installed")
            return lz4.frame.decompress(data)
        elif algo == "snappy":
            if not HAS_SNAPPY:
                logger.warning("snappy未安装，无法解压")
                raise ImportError("snappy not installed")
            return snappy.decompress(data)
        else:
            logger.warning(f"未知算法: {algo}")
            raise ValueError(f"Unknown algorithm: {algo}")
            
    except Exception as e:
        logger.error(f"解压失败: {e}")
        raise


def get_compression_info() -> Dict[str, bool]:
    """获取可用的压缩算法信息"""
    return {
        "gzip": True,  # 总是可用
        "bz2": True,   # 总是可用
        "lzma": True,  # 总是可用
        "zstd": HAS_ZSTD,
        "lz4": HAS_LZ4,
        "snappy": HAS_SNAPPY,
    }

