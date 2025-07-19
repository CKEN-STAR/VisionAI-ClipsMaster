#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
压缩模块

提供高性能压缩功能，包括：
1. 多算法支持的无损压缩引擎
2. 硬件加速支持
3. 自适应压缩策略
4. 压缩效能监控
"""

# 导入基础压缩器
from src.compression.compressors import (
    get_compressor,
    get_available_compressors,
    register_compressor,
    compress_data,
    decompress_data
)

# 导入基准测试工具
from src.compression.algorithm_benchmark import (
    benchmark_algorithms,
    get_recommended_algorithm
)

# 导入集成功能
from src.compression.integration import (
    compress_resource,
    decompress_resource,
    compress_all_resources,
    get_compression_stats
)

# 导入分块压缩
from src.compression.chunked_compression import (
    compress_chunked,
    decompress_chunked,
    get_chunked_header_info,
    ChunkedCompressor
)

# 导入分层策略
from src.compression.layered_policy import (
    get_policy_manager,
    compress_with_policy,
    get_resource_policy
)

# 导入高性能无损压缩核心引擎
from src.compression.core import (
    Compressor,
    compress,
    decompress,
    compress_file,
    decompress_file,
    benchmark
)

# 导入压缩异常处理模块
from src.compression.error_handling import (
    DecompressionGuard,
    CompressionGuard,
    VerificationUtils,
    safe_compress,
    safe_decompress,
    is_valid_compressed_data,
    try_recover_data,
    CompressionError,
    CompressionFormatError,
    DecompressionError,
    IntegrityError,
    MagicHeaderError
)

# 导入硬件加速模块
from src.compression.hardware_accel import (
    init_gpu_accel,
    get_best_hardware,
    HardwareAcceleratedCompressor,
    TorchCUDACompressor,
    CPUCompressor,
    QATCompressor,
    benchmark_hardware,
    HARDWARE_INFO,
    HAS_CUDA,
    HAS_QAT
)

# 导入自适应压缩
from src.compression.adaptive_compression import (
    smart_compress, smart_decompress,
    get_smart_compressor, get_compression_stats,
    ResourcePriority, MemoryPressureLevel
)

# 暴露监控功能
has_monitoring = True
try:
    from src.ui.compression_dashboard_integration import (
        initialize_compression_monitoring,
        get_compression_dashboard_launcher,
        get_compression_monitor,
        run_standalone_dashboard
    )
except ImportError:
    has_monitoring = False

__all__ = [
    # 基础压缩器
    'get_compressor',
    'get_available_compressors',
    'register_compressor',
    'compress_data',
    'decompress_data',
    
    # 基准测试
    'benchmark_algorithms',
    'get_recommended_algorithm',
    
    # 内存集成
    'compress_resource',
    'decompress_resource',
    'compress_all_resources',
    'get_compression_stats',
    
    # 分块压缩
    'compress_chunked',
    'decompress_chunked',
    'get_chunked_header_info',
    'ChunkedCompressor',
    
    # 分层策略
    'get_policy_manager',
    'compress_with_policy',
    'get_resource_policy',
    
    # 高性能核心引擎
    'Compressor',
    'compress',
    'decompress',
    'compress_file',
    'decompress_file',
    'benchmark',
    
    # 压缩异常处理
    'DecompressionGuard',
    'CompressionGuard',
    'VerificationUtils',
    'safe_compress',
    'safe_decompress',
    'is_valid_compressed_data',
    'try_recover_data',
    'CompressionError',
    'CompressionFormatError',
    'DecompressionError',
    'IntegrityError',
    'MagicHeaderError',
    
    # 硬件加速
    'init_gpu_accel',
    'get_best_hardware',
    'HardwareAcceleratedCompressor',
    'TorchCUDACompressor',
    'CPUCompressor',
    'QATCompressor',
    'benchmark_hardware',
    'HARDWARE_INFO',
    'HAS_CUDA',
    'HAS_QAT',
    
    # 自适应压缩
    'smart_compress', 'smart_decompress',
    'get_smart_compressor', 'get_compression_stats',
    'ResourcePriority', 'MemoryPressureLevel',
    
    # 监控功能
    'has_monitoring'
]

if has_monitoring:
    __all__.extend([
        'initialize_compression_monitoring', 
        'get_compression_dashboard_launcher',
        'get_compression_monitor',
        'run_standalone_dashboard'
    ]) 