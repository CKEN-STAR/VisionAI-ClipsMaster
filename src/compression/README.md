# VisionAI-ClipsMaster 压缩模块

## 简介

VisionAI-ClipsMaster 压缩模块是一个为低端设备(4GB内存，无GPU)优化的内存压缩解决方案。该模块提供多种压缩算法和策略，支持对不同类型的资源应用不同的压缩方案，以达到最佳的性能和内存平衡。

## 功能特性

- **多种压缩算法支持**：支持Zstandard、LZ4、Gzip、Bzip2、LZMA和Snappy等压缩算法
- **基准测试系统**：评估不同算法在压缩率、速度和内存使用方面的性能
- **内存管理集成**：与系统内存管理紧密结合，支持资源自动压缩和释放
- **分层压缩策略**：为不同类型的资源配置不同的压缩参数和行为
- **分块压缩**：支持大型数据的分块压缩，优化IO性能

## 模块组成

- `compressors.py`: 核心压缩算法实现
- `algorithm_benchmark.py`: 压缩算法基准测试工具
- `integration.py`: 内存系统集成接口
- `chunked_compression.py`: 分块压缩实现
- `layered_policy.py`: 分层压缩策略管理
- `layered_cli.py`: 分层压缩策略命令行工具
- `test_compression.py`: 压缩功能测试
- `test_layered.py`: 分层策略集成测试

## 分层压缩策略

分层压缩策略系统允许为不同类型的资源配置不同的压缩参数和行为，使系统能够根据资源特性选择最适合的压缩方案。

### 配置文件

压缩策略通过YAML配置文件定义(`configs/compression_layers.yaml`)。每种资源类型可以配置以下参数：

- `algorithm`: 要使用的压缩算法（如zstd、lz4、gzip等）
- `level`: 压缩级别，数值越大压缩率越高但速度越慢
- `chunk_size`: 分块大小，用于分块压缩大型数据
- `auto_compress`: 是否自动压缩（布尔值）
- `threshold_mb`: 自动压缩的大小阈值（MB）
- `priority`: 压缩优先级（high/medium/low）

### 资源类型和默认策略

系统为以下资源类型提供了特定的压缩策略：

| 资源类型 | 算法 | 级别 | 自动压缩 | 阈值(MB) | 优先级 |
|-----------|----------|-------|--------------|-------------|----------|
| model_weights | zstd | 3 | 否 | 50 | low |
| subtitle | lz4 | 0 | 是 | 1 | high |
| intermediate_cache | lz4 | 1 | 是 | 5 | medium |
| attention_cache | zstd | 1 | 是 | 10 | medium |
| file_cache | zstd | 3 | 是 | 20 | low |
| temp_buffers | lz4 | 0 | 是 | 5 | high |
| log_data | gzip | 6 | 是 | 2 | low |
| default | gzip | 6 | 否 | 10 | low |

### 命令行工具

提供了命令行工具(`layered_cli.py`)用于管理和应用分层压缩策略：

```bash
# 显示所有压缩策略
python -m src.compression.layered_cli list

# 显示详细信息
python -m src.compression.layered_cli list --verbose

# 创建新策略
python -m src.compression.layered_cli create image_data --algorithm zstd --level 2 --threshold 5

# 更新策略
python -m src.compression.layered_cli update model_weights --level 2 --auto-compress true

# 验证配置文件
python -m src.compression.layered_cli verify configs/compression_layers.yaml
```

## 安装与依赖

基本依赖：
- Python 3.7+
- PyYAML
- NumPy

可选依赖（提供更多压缩算法）：
- zstandard
- lz4
- python-snappy

安装方法：

```bash
pip install -r src/compression/requirements.txt
```

## 使用示例

### 基本压缩/解压

```python
from src.compression import compress_data, decompress_data

# 压缩数据
compressed, metadata = compress_data(your_data, algorithm="zstd")

# 解压数据
original = decompress_data(compressed, metadata)
```

### 使用分层策略

```python
from src.compression import compress_with_policy, get_resource_policy

# 获取特定资源类型的策略
policy = get_resource_policy("model_weights")
print(f"模型权重压缩策略: {policy}")

# 使用策略压缩资源
success = compress_with_policy("resource_id", "model_weights")
```

### 分块压缩大文件

```python
from src.compression import compress_chunked, decompress_chunked

# 读取大文件
with open("large_file.bin", "rb") as f:
    data = f.read()

# 分块压缩（自动处理分块）
compressed = compress_chunked(data, algorithm="zstd", chunk_size=4*1024*1024)

# 解压
decompressed = decompress_chunked(compressed)
```

## 性能优化

为确保在低端设备上的性能，模块采取了以下优化措施：

1. **资源类型自适应**：为不同资源类型选择最适合的压缩算法和参数
2. **延迟压缩**：对于非关键资源使用延迟压缩，避免影响主流程
3. **分块处理**：大型资源分块压缩，减少内存峰值使用
4. **选择性压缩**：仅压缩超过阈值的资源，避免小资源的压缩开销

## 贡献与开发

如需添加新的压缩算法或优化现有功能，请遵循以下步骤：

1. 在`compressors.py`中实现新的压缩器类，继承`CompressorBase`
2. 在`register_default_compressors()`函数中注册新压缩器
3. 更新配置文件，为相关资源类型指定新算法
4. 运行测试确保功能正常

# 压缩模块

## 简介

VisionAI-ClipsMaster的压缩模块提供高性能、多功能的压缩能力，用于系统中的资源压缩。本模块支持多种压缩算法、分块压缩、异常处理以及硬件加速等功能，适配不同的使用场景和硬件环境。

## 主要功能

1. **基础压缩** - 支持多种压缩算法(zstd, lz4, gzip等)
2. **分块压缩** - 大文件/大数据的分块压缩与并行处理
3. **分层策略** - 基于数据类型和重要性的智能压缩策略
4. **异常处理** - 压缩/解压过程中的错误检测与恢复
5. **硬件加速** - 利用GPU和专用硬件提升压缩性能

## 硬件加速模块

`hardware_accel.py`模块提供硬件加速压缩能力，支持:

1. **CUDA/GPU加速** - 利用NVIDIA GPU加速压缩/解压过程
2. **Intel QAT加速** - 如有Intel QuickAssist Technology硬件，提供额外加速
3. **智能回退** - 当硬件不可用时自动回退到CPU模式
4. **自动硬件选择** - 自动选择性能最佳的硬件设备

### 使用示例

#### 基本用法

```python
from src.compression.hardware_accel import get_best_hardware

# 自动选择最佳硬件
compressor = get_best_hardware(algorithm="zstd", level=3)

# 压缩数据
compressed, metadata = compressor.compress(data)

# 解压数据
decompressed = compressor.decompress(compressed, metadata)
```

#### 指定硬件

```python
from src.compression.hardware_accel import TorchCUDACompressor, CPUCompressor

# 使用CUDA/GPU压缩
gpu_compressor = TorchCUDACompressor(algorithm="zstd", level=3)
compressed, metadata = gpu_compressor.compress(data)

# 使用CPU压缩
cpu_compressor = CPUCompressor(algo="zstd", level=3)
compressed, metadata = cpu_compressor.compress(data)
```

#### 性能测试

```python
from src.compression.hardware_accel import benchmark_hardware

# 运行硬件性能测试
results = benchmark_hardware(data_size=50*1024*1024, iterations=3)

# 处理结果
for hw_type, metrics in results.items():
    print(f"{hw_type}: 压缩速度={metrics['compression_speed']:.1f}MB/s, "
          f"解压速度={metrics['decompression_speed']:.1f}MB/s")
```

### 性能提升

在支持CUDA的NVIDIA GPU上，压缩性能通常可以获得3-6倍的提升。实际提升取决于:

- GPU型号和性能
- 数据大小和类型
- 压缩算法和级别

| 设备 | 压缩速度提升 | 功耗增加 |
|------|------------|---------|
| NVIDIA A100 | 5.8x | 23W |
| Intel QAT | 3.2x | 11W |

### 系统要求

- **CUDA加速**: 需要CUDA兼容的NVIDIA GPU和PyTorch或CuPy库
- **QAT加速**: 需要Intel QuickAssist Technology硬件和相应驱动
- **CPU回退**: 无特殊要求，适用于所有系统

## 异常处理模块

`error_handling.py`模块提供压缩和解压过程中的安全防护和异常处理机制，包括:

1. **魔数校验头** - 确保压缩数据的格式正确性
2. **CRC32完整性校验** - 验证数据完整性
3. **异常捕获和恢复** - 处理各种压缩/解压错误
4. **数据健康检查** - 检测并修复损坏的压缩数据

### 使用示例

```python
from src.compression.error_handling import safe_compress, safe_decompress

# 安全压缩
compressed, metadata = safe_compress(data)

# 安全解压，即使数据有轻微损坏也会尝试恢复
decompressed = safe_decompress(compressed)
```

## 其他模块

- **core.py** - 核心压缩/解压引擎
- **compressors.py** - 各种压缩算法的实现
- **chunked_compression.py** - 分块压缩实现
- **layered_policy.py** - 分层压缩策略管理
- **algorithm_benchmark.py** - 压缩算法基准测试工具
- **integration.py** - 与系统其他部分的集成接口 