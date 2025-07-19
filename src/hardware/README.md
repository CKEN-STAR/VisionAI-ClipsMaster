# 硬件优化模块 - VisionAI-ClipsMaster

该目录包含 VisionAI-ClipsMaster 项目的各种硬件优化实现，包括 SIMD 向量化、平台特定汇编优化、内存对齐优化和指令级并行优化等。

## 主要组件

### 1. SIMD 向量化

SIMD（单指令多数据）向量化是一种并行处理技术，可以显著提高处理大量数据的速度。

- **simd_kernels.cpp/h** - 包含 C/C++ 实现的 SIMD 优化内核
- **simd_wrapper.py** - Python 接口，将原生 SIMD 功能暴露给 Python 代码
- **simd_utils.py** - 提供便捷的 SIMD 操作函数

支持的指令集：
- AVX512 (512位向量)
- AVX2 (256位向量)
- AVX (256位向量)
- SSE4.2 (128位向量)
- NEON (ARM平台，128位向量)

### 2. 平台特定汇编优化

汇编优化提供了针对不同平台的高度优化实现，以获得最大性能。

- **assembly_kernels.cpp/h** - 包含平台特定的汇编优化实现
- **assembly_wrapper.py** - Python 接口，将汇编优化功能暴露给 Python 代码

支持的平台：
- Windows: 使用 Intel MKL 和 AVX2/FMA 指令
- macOS: 使用 Accelerate 框架
- Linux: 使用 GCC 内联汇编
- ARM: 使用 NEON 指令

### 3. 内存对齐优化

内存对齐是提高数据访问效率的关键优化，尤其对 SIMD 和汇编操作至关重要。

- **memory_aligner.py** - 提供内存对齐功能，包括对齐内存分配和数组管理

特性：
- 自动根据平台和指令集选择最优对齐值
- 支持对齐内存分配和 NumPy 数组创建
- 与 SIMD 和汇编优化无缝集成
- 提供内存管理和资源跟踪

### 4. 指令级并行优化

指令级并行 (ILP) 优化通过并行执行多个独立指令，充分利用多核 CPU 的性能。

- **parallel_scheduler.py** - 提供指令级并行调度功能
- **test_parallel_scheduler.py** - ILP 优化的测试和基准测试

特性：
- 数据分块调度，根据 L1 缓存大小自动调整
- 动态负载均衡，优化多核心利用率
- 多种并行后端支持（线程、进程）
- 简洁的 API（函数式、类和装饰器）
- 与其他优化技术无缝集成

### 5. 优化路由器

优化路由器负责检测系统硬件能力并选择最佳优化路径。

- **optimization_router.py** - 根据 CPU 能力选择最佳优化路径
- 支持自动回退到基线实现以确保兼容性

## 使用示例

### SIMD 优化

```python
from src.hardware.simd_utils import matrix_multiply, matrix_add

# 自动使用最佳 SIMD 指令集
result = matrix_multiply(matrix_a, matrix_b)
sum_matrix = matrix_add(matrix_a, matrix_b)
```

### 汇编优化

```python
from src.hardware.assembly_wrapper import get_platform_asm

asm = get_platform_asm()
result = asm.optimized_matrix_multiply(matrix_a, matrix_b)
```

### 内存对齐

```python
from src.hardware.memory_aligner import create_aligned_array, align_array

# 创建对齐数组
aligned_array = create_aligned_array((1000, 1000), dtype=np.float32)

# 将现有数组对齐
aligned_copy = align_array(existing_array)
```

### 指令级并行

```python
from src.hardware.parallel_scheduler import ParallelScheduler, parallel

# 方法 1：使用调度器
scheduler = ParallelScheduler(n_jobs=4)
results = scheduler.schedule_instructions(my_function, data_list)

# 方法 2：使用装饰器
@parallel(n_jobs=4)
def process_item(x):
    return x * 2
    
results = process_item(data_list)
```

### 使用优化路由器

```python
from src.hardware.optimization_router import OptimizationRouter

router = OptimizationRouter()

# 获取当前平台的最佳内存对齐值
alignment = router.get_memory_alignment()

# 创建对齐数组
aligned_array = router.create_aligned_array((1000, 1000))

# 检查是否对齐
is_aligned = router.is_aligned(array)

# 使用并行调度
results = router.schedule_parallel_tasks(my_function, data_list)
```

## 集成示例

以下是一个完整的集成示例，展示如何结合使用所有优化技术：

```python
import numpy as np
from src.hardware.optimization_router import OptimizationRouter
from src.hardware.simd_utils import get_simd_ops
from src.hardware.assembly_wrapper import get_platform_asm
from src.hardware.parallel_scheduler import ParallelScheduler

# 创建优化路由器
router = OptimizationRouter()

# 创建对齐数组
a = router.create_aligned_array((1000, 1000), np.float32)
b = router.create_aligned_array((1000, 1000), np.float32)

# 填充数据
a.fill(1.0)
b.fill(2.0)

# 获取 SIMD 和汇编操作
simd_ops = get_simd_ops()
asm = get_platform_asm()

# 定义计算函数
def compute_matrix(matrix_pair):
    matrix_a, matrix_b = matrix_pair
    # 先使用 SIMD 乘法
    result1 = simd_ops.matrix_multiply(matrix_a, matrix_b)
    # 再使用汇编优化
    if asm and asm.lib:
        result2 = asm.optimized_matrix_multiply(result1, matrix_b)
        return result2
    return result1

# 准备多个矩阵对
matrix_pairs = [(a, b) for _ in range(10)]

# 使用指令级并行处理所有矩阵对
scheduler = ParallelScheduler(n_jobs=router.get_optimization_level().get('parallel_threads', 4))
results = scheduler.schedule_instructions(compute_matrix, matrix_pairs)
```

## 性能提升

根据测试结果，这些优化可以提供以下性能提升：

| 优化技术 | 典型加速比 | 最佳场景 |
|---------|-----------|---------|
| SIMD 向量化 | 1.5-4x | 大型矩阵和向量运算 |
| 汇编优化 | 2-5x | 高度优化的特定算法 |
| 内存对齐 | 1.2-1.4x | 与 SIMD 和汇编结合 |
| 指令级并行 | 近线性扩展 | 可并行的独立任务 |
| 组合优化 | 3-8x | 大规模数据处理 |

性能提升取决于硬件平台、数据大小和操作类型。

## 构建说明

要构建原生库，请使用以下命令：

```bash
# 构建 SIMD 库
python build_simd_extension.py

# 构建汇编库
python build_assembly_extension.py

# 同时构建两者
python build_optimizations.py
```

## 测试

该目录包含多个测试文件：

- **test_simd.py** - 测试 SIMD 优化
- **test_assembly.py** - 测试汇编优化
- **test_memory_alignment.py** - 测试内存对齐
- **test_parallel_scheduler.py** - 测试指令级并行
- **test_integration.py** - 测试多种优化的集成

运行测试：

```bash
# 运行单个测试
python src/hardware/test_simd.py

# 运行所有测试
python -m unittest discover src/hardware
```

## 文档

有关更详细的信息，请参考：

- [SIMD优化文档](../docs/SIMD_OPTIMIZATION.md)
- [汇编优化文档](../docs/ASSEMBLY_OPTIMIZATION.md)
- [内存对齐文档](../docs/MEMORY_ALIGNMENT.md)
- [指令级并行文档](../docs/INSTRUCTION_LEVEL_PARALLELISM.md)

## 注意事项

- 确保在使用前先构建原生库
- 优化路由器会自动检测系统能力并选择最佳路径
- 所有优化都有回退机制，确保在不支持的平台上仍能正常工作 