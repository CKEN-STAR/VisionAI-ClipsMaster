#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
压缩异常处理模块

提供压缩和解压过程中的安全防护和异常处理机制，包括:
1. 魔数校验头 
2. CRC32完整性校验
3. 异常捕获和恢复机制
4. 压缩数据健康检查

此模块旨在提高压缩/解压过程的安全性和稳定性，避免因数据损坏导致的错误。
"""

import zlib
import struct
import logging
import binascii
import traceback
from typing import Dict, Any, Optional, Tuple, Union, Callable

# 尝试导入常用压缩库
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

# 从核心压缩模块导入
from src.compression.core import compress, decompress

# 配置日志
logger = logging.getLogger("CompressionErrorHandling")

# 自定义异常类
class CompressionError(Exception):
    """压缩操作相关的基础异常类"""
    pass

class CompressionFormatError(CompressionError):
    """压缩格式错误"""
    pass

class DecompressionError(CompressionError):
    """解压过程中的错误"""
    pass

class IntegrityError(CompressionError):
    """数据完整性错误"""
    pass

class MagicHeaderError(CompressionFormatError):
    """魔数头校验失败"""
    pass


class DecompressionGuard:
    """
    解压防护类
    
    提供安全的解压操作，包含多种防护机制:
    1. 魔数头验证
    2. CRC32校验
    3. 错误捕获与处理
    """
    
    # 标准魔数头，用于标识压缩数据
    MAGIC_HEADER = b'CLIP'
    
    def __init__(self, 
                 verify_magic: bool = True, 
                 verify_checksum: bool = True,
                 raise_on_error: bool = True):
        """
        初始化解压防护
        
        Args:
            verify_magic: 是否验证魔数头
            verify_checksum: 是否验证校验和
            raise_on_error: 错误时是否抛出异常(False则返回None)
        """
        self.verify_magic = verify_magic
        self.verify_checksum = verify_checksum
        self.raise_on_error = raise_on_error
    
    def safe_decompress(self, data: bytes) -> Optional[bytes]:
        """
        带防护的解压过程
        
        Args:
            data: 压缩数据
            
        Returns:
            bytes: 解压后的数据，错误时根据配置返回None或抛出异常
            
        Raises:
            MagicHeaderError: 魔数头验证失败
            IntegrityError: 校验和验证失败
            DecompressionError: 解压失败
        """
        # 验证数据长度
        if len(data) < 8:  # 至少需要魔数头和基本元数据
            if self.raise_on_error:
                raise CompressionFormatError("数据长度不足，无法解压")
            logger.error("数据长度不足，无法解压")
            return None
            
        # 验证魔数头
        header = data[:4]
        if self.verify_magic and header != self.MAGIC_HEADER:
            if self.raise_on_error:
                raise MagicHeaderError(f"压缩头校验失败: {header}")
            logger.error(f"压缩头校验失败: {header}")
            return None
        
        try:
            # 提取数据部分（跳过头部）
            payload = data[4:]
            
            # 使用核心模块的decompress函数
            return decompress(payload)
        except Exception as e:
            error_msg = f"解压失败: {str(e)}"
            if self.raise_on_error:
                raise DecompressionError(error_msg)
            logger.error(error_msg)
            return None


class CompressionGuard:
    """
    压缩防护类
    
    提供安全的压缩操作，添加标准化头部和校验和
    """
    
    # 标准魔数头，用于标识压缩数据
    MAGIC_HEADER = b'CLIP'
    
    def __init__(self, 
                 algo: str = 'zstd', 
                 level: int = 3,
                 add_checksum: bool = True):
        """
        初始化压缩防护
        
        Args:
            algo: 压缩算法
            level: 压缩级别
            add_checksum: 是否添加校验和
        """
        self.algo = algo
        self.level = level
        self.add_checksum = add_checksum
    
    def safe_compress(self, data: bytes) -> Tuple[bytes, Dict[str, Any]]:
        """
        带防护的压缩过程
        
        Args:
            data: 原始数据
            
        Returns:
            Tuple[bytes, Dict]: 压缩后的数据和元数据
        """
        # 计算原始数据的CRC32
        checksum = zlib.crc32(data) & 0xffffffff
        
        # 压缩数据
        compressed, metadata = compress(data, algo=self.algo, level=self.level)
        
        # 构建带魔数头的数据
        protected_data = self.MAGIC_HEADER + compressed
        
        # 更新元数据
        metadata.update({
            'original_checksum': checksum,
            'original_size': len(data),
            'has_magic_header': True,
            'protected': True
        })
        
        return protected_data, metadata


class VerificationUtils:
    """
    压缩数据验证工具类
    
    提供各种验证和检查压缩数据的工具方法
    """
    
    @staticmethod
    def is_compressed_data(data: bytes) -> bool:
        """
        检查数据是否为压缩数据
        
        Args:
            data: 待检查的数据
            
        Returns:
            bool: 是否为压缩数据
        """
        # 检查常见压缩格式的头部标识
        if len(data) < 4:
            return False
            
        # 检查CLIP自定义头
        if data[:4] == b'CLIP':
            return True
            
        # 检查zstd头
        if data[:4] == b'\x28\xB5\x2F\xFD':
            return True
            
        # 检查lz4头
        if data[:4] == b'\x04\x22\x4D\x18':
            return True
            
        # 检查gzip头
        if data[:2] == b'\x1F\x8B':
            return True
            
        # 检查zip头
        if data[:4] == b'PK\x03\x04':
            return True
            
        return False
    
    @staticmethod
    def verify_integrity(data: bytes, checksum: int) -> bool:
        """
        验证数据完整性
        
        Args:
            data: 待验证的数据
            checksum: 期望的校验和
            
        Returns:
            bool: 是否通过验证
        """
        calculated = zlib.crc32(data) & 0xffffffff
        return calculated == checksum
    
    @staticmethod
    def get_compressed_info(data: bytes) -> Dict[str, Any]:
        """
        获取压缩数据的信息
        
        Args:
            data: 压缩数据
            
        Returns:
            Dict: 数据信息
        """
        info = {
            'size': len(data),
            'is_compressed': VerificationUtils.is_compressed_data(data),
            'format': 'unknown'
        }
        
        if len(data) < 4:
            return info
            
        # 识别格式
        if data[:4] == b'CLIP':
            info['format'] = 'clip'
            info['has_magic_header'] = True
        elif data[:4] == b'\x28\xB5\x2F\xFD':
            info['format'] = 'zstd'
        elif data[:4] == b'\x04\x22\x4D\x18':
            info['format'] = 'lz4'
        elif data[:2] == b'\x1F\x8B':
            info['format'] = 'gzip'
        elif data[:4] == b'PK\x03\x04':
            info['format'] = 'zip'
            
        return info


# 便捷函数
def safe_decompress(data: bytes, 
                   verify_magic: bool = True,
                   verify_checksum: bool = True,
                   raise_on_error: bool = True) -> Optional[bytes]:
    """
    安全解压函数
    
    Args:
        data: 压缩数据
        verify_magic: 是否验证魔数头
        verify_checksum: 是否验证校验和
        raise_on_error: 错误时是否抛出异常
        
    Returns:
        bytes: 解压后的数据
    """
    guard = DecompressionGuard(
        verify_magic=verify_magic,
        verify_checksum=verify_checksum,
        raise_on_error=raise_on_error
    )
    return guard.safe_decompress(data)


def safe_compress(data: bytes,
                 algo: str = 'zstd',
                 level: int = 3,
                 add_checksum: bool = True) -> Tuple[bytes, Dict[str, Any]]:
    """
    安全压缩函数
    
    Args:
        data: 原始数据
        algo: 压缩算法
        level: 压缩级别
        add_checksum: 是否添加校验和
        
    Returns:
        Tuple[bytes, Dict]: 压缩后的数据和元数据
    """
    guard = CompressionGuard(
        algo=algo,
        level=level,
        add_checksum=add_checksum
    )
    return guard.safe_compress(data)


def is_valid_compressed_data(data: bytes) -> bool:
    """
    检查数据是否为有效的压缩数据
    
    Args:
        data: 待检查的数据
        
    Returns:
        bool: 是否为有效的压缩数据
    """
    return VerificationUtils.is_compressed_data(data)


# 恢复函数
def try_recover_data(data: bytes) -> Optional[bytes]:
    """
    尝试恢复损坏的压缩数据（尽力而为）
    
    Args:
        data: 可能损坏的压缩数据
        
    Returns:
        Optional[bytes]: 恢复的数据或None
    """
    # 获取数据格式信息
    info = VerificationUtils.get_compressed_info(data)
    
    # 如果不像是压缩数据，直接返回
    if not info['is_compressed']:
        return None
        
    # 根据格式尝试不同的恢复策略
    if info['format'] == 'clip':
        # 尝试跳过头部
        try:
            return safe_decompress(data, raise_on_error=False)
        except:
            pass
            
    # 尝试各种算法解压
    # 优先使用核心模块的decompress
    try:
        return decompress(data)
    except:
        pass
    
    # 尝试各种算法
    for algo in ['zstd', 'lz4', 'gzip']:
        try:
            if algo == 'zstd' and HAS_ZSTD:
                return zstd.decompress(data)
            elif algo == 'lz4' and HAS_LZ4:
                return lz4.frame.decompress(data)
            elif algo == 'gzip':
                import gzip
                return gzip.decompress(data)
        except:
            continue
            
    # 所有尝试都失败
    return None 