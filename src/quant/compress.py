"""无损压缩集成模块

此模块实现模型的无损压缩功能，包括：
1. 多种压缩算法支持
2. 自适应压缩策略
3. 压缩性能优化
4. 数据完整性验证
"""

import os
import zlib
import lzma
import bz2
import pickle
from typing import Dict, Optional, Union, Tuple
from pathlib import Path
import numpy as np
from loguru import logger
from ..utils.file_handler import FileHandler

class CompressionManager:
    """压缩管理器"""
    
    def __init__(self):
        """初始化压缩管理器"""
        self.file_handler = FileHandler()
        
        # 支持的压缩算法
        self.compression_methods = {
            'zstd': self._compress_zstd,
            'lzma': self._compress_lzma,
            'zlib': self._compress_zlib,
            'bz2': self._compress_bz2
        }
        
        # 压缩配置
        self.compression_config = {
            'zstd': {'level': 3, 'threads': -1},
            'lzma': {'preset': 6},
            'zlib': {'level': 6},
            'bz2': {'compresslevel': 9}
        }
        
        # 性能统计
        self.stats = {
            'original_size': 0,
            'compressed_size': 0,
            'compression_ratio': 0,
            'compression_time': 0
        }

    def compress_model(self,
                      model_data: Union[Dict, bytes],
                      method: str = 'zstd',
                      optimize: bool = True) -> Tuple[bytes, Dict]:
        """压缩模型数据

        Args:
            model_data: 模型数据
            method: 压缩方法
            optimize: 是否优化压缩

        Returns:
            Tuple[bytes, Dict]: (压缩后的数据, 压缩统计信息)
        """
        try:
            # 序列化模型数据
            if not isinstance(model_data, bytes):
                model_data = pickle.dumps(model_data)
            
            # 记录原始大小
            self.stats['original_size'] = len(model_data)
            
            # 选择压缩方法
            if optimize:
                method = self._select_best_method(model_data)
            
            if method not in self.compression_methods:
                raise ValueError(f"不支持的压缩方法: {method}")
            
            # 执行压缩
            compressed_data = self.compression_methods[method](model_data)
            
            # 更新统计信息
            self.stats['compressed_size'] = len(compressed_data)
            self.stats['compression_ratio'] = 1 - (len(compressed_data) / len(model_data))
            
            # 验证压缩结果
            self._verify_compression(model_data, compressed_data, method)
            
            return compressed_data, self.get_stats()
            
        except Exception as e:
            logger.error(f"模型压缩失败: {str(e)}")
            raise

    def decompress_model(self,
                        compressed_data: bytes,
                        method: str = 'zstd') -> Dict:
        """解压模型数据

        Args:
            compressed_data: 压缩数据
            method: 压缩方法

        Returns:
            Dict: 解压后的模型数据
        """
        try:
            # 选择解压方法
            decompress_method = getattr(self, f"_decompress_{method}")
            if not decompress_method:
                raise ValueError(f"不支持的解压方法: {method}")
            
            # 执行解压
            decompressed_data = decompress_method(compressed_data)
            
            # 反序列化
            model_data = pickle.loads(decompressed_data)
            
            return model_data
            
        except Exception as e:
            logger.error(f"模型解压失败: {str(e)}")
            raise

    def _compress_zstd(self, data: bytes) -> bytes:
        """使用zstd压缩

        Args:
            data: 原始数据

        Returns:
            bytes: 压缩后的数据
        """
        try:
            import zstandard as zstd
            compressor = zstd.ZstdCompressor(**self.compression_config['zstd'])
            return compressor.compress(data)
        except ImportError:
            logger.warning("zstd未安装，回退到zlib压缩")
            return self._compress_zlib(data)

    def _compress_lzma(self, data: bytes) -> bytes:
        """使用lzma压缩

        Args:
            data: 原始数据

        Returns:
            bytes: 压缩后的数据
        """
        return lzma.compress(data, **self.compression_config['lzma'])

    def _compress_zlib(self, data: bytes) -> bytes:
        """使用zlib压缩

        Args:
            data: 原始数据

        Returns:
            bytes: 压缩后的数据
        """
        return zlib.compress(data, **self.compression_config['zlib'])

    def _compress_bz2(self, data: bytes) -> bytes:
        """使用bz2压缩

        Args:
            data: 原始数据

        Returns:
            bytes: 压缩后的数据
        """
        return bz2.compress(data, **self.compression_config['bz2'])

    def _decompress_zstd(self, data: bytes) -> bytes:
        """使用zstd解压

        Args:
            data: 压缩数据

        Returns:
            bytes: 解压后的数据
        """
        try:
            import zstandard as zstd
            decompressor = zstd.ZstdDecompressor()
            return decompressor.decompress(data)
        except ImportError:
            raise RuntimeError("zstd未安装")

    def _decompress_lzma(self, data: bytes) -> bytes:
        """使用lzma解压

        Args:
            data: 压缩数据

        Returns:
            bytes: 解压后的数据
        """
        return lzma.decompress(data)

    def _decompress_zlib(self, data: bytes) -> bytes:
        """使用zlib解压

        Args:
            data: 压缩数据

        Returns:
            bytes: 解压后的数据
        """
        return zlib.decompress(data)

    def _decompress_bz2(self, data: bytes) -> bytes:
        """使用bz2解压

        Args:
            data: 压缩数据

        Returns:
            bytes: 解压后的数据
        """
        return bz2.decompress(data)

    def _select_best_method(self, data: bytes) -> str:
        """选择最佳压缩方法

        Args:
            data: 原始数据

        Returns:
            str: 压缩方法名称
        """
        # 使用数据样本测试各种方法
        sample_size = min(len(data), 1024 * 1024)  # 最多使用1MB样本
        sample = data[:sample_size]
        
        best_method = 'zstd'
        best_ratio = 0
        
        for method in self.compression_methods:
            try:
                compressed = self.compression_methods[method](sample)
                ratio = 1 - (len(compressed) / len(sample))
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_method = method
            except Exception:
                continue
        
        return best_method

    def _verify_compression(self,
                          original: bytes,
                          compressed: bytes,
                          method: str):
        """验证压缩结果

        Args:
            original: 原始数据
            compressed: 压缩数据
            method: 压缩方法
        """
        try:
            # 解压验证
            decompressed = getattr(self, f"_decompress_{method}")(compressed)
            if decompressed != original:
                raise ValueError("压缩验证失败：数据不一致")
        except Exception as e:
            logger.error(f"压缩验证失败: {str(e)}")
            raise

    def get_stats(self) -> Dict:
        """获取压缩统计信息

        Returns:
            Dict: 统计信息
        """
        return {
            'original_size': self.stats['original_size'],
            'compressed_size': self.stats['compressed_size'],
            'compression_ratio': self.stats['compression_ratio'],
            'compression_time': self.stats['compression_time']
        }

    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            'original_size': 0,
            'compressed_size': 0,
            'compression_ratio': 0,
            'compression_time': 0
        } 