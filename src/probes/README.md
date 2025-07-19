# VisionAI-ClipsMaster 内存探针系统

## 概述

内存探针系统是VisionAI-ClipsMaster的内存监控和管理组件，专为低内存环境（如4GB RAM无GPU设备）优化设计。该系统能够自动监测内存使用情况，在关键点插入内存检测代码，并在内存压力大时触发响应措施。

探针系统提供Python和C两种实现：
- Python实现提供灵活、易于扩展的内存监控功能
- C实现提供高性能、低开销的内存监控，适用于性能关键部分

## 系统组件

内存探针系统包含以下主要组件：

1. **内存探针**(`src/utils/memory_probes.py`)：核心Python探针实现
2. **探针初始化器**(`src/utils/probe_initializer.py`)：负责在应用启动时初始化探针系统
3. **C语言探针**(`src/probes/memory_probes.c`)：高性能C语言实现
4. **C语言包装器**(`src/probes/probe_wrapper.py`)：使用ctypes连接C探针
5. **统一接口**(`src/probes/__init__.py`)：提供统一的API访问所有探针功能

## 使用方法

### 基本使用

```python
from src.probes import check_memory, probe_memory

# 方法1：使用内存检查函数
memory_info = check_memory("my_operation")
print(f"内存使用率: {memory_info['memory_usage']*100:.1f}%")
print(f"可用内存: {memory_info['memory_available_mb']:.1f}MB")

# 方法2：使用装饰器
@probe_memory(level="medium")
def process_large_data(data):
    # 函数前后会自动检查内存使用情况
    result = do_something_with(data)
    return result
```

### 高级功能

```python
from src.probes import get_probe_manager, HAS_C_PROBES

# 获取探针管理器
manager = get_probe_manager()

# 自定义注入点
manager.add_custom_probe("src.my_module.my_function", level="high")

# 使用C探针（如果可用）
if HAS_C_PROBES:
    from src.probes import fast_check
    fast_check(threshold_mb=1000)  # 快速检查内存，超过1000MB时触发警告
```

## 注入点

内存探针系统会自动注入到以下关键代码点：

- 模型加载器 (`src.core.model_loader.load_model`)
- 内存分配器 (`src.memory.compressed_allocator.allocate`)
- 分片加载器 (`src.core.shard_policy_manager.load_shard`)
- 大文件读取 (`src.utils.file_handler.read_large_file`)
- SRT解析器 (`src.core.srt_parser.parse_file`)
- 资源分配器 (`src.memory.resource_tracker.allocate_resource`)
- 模型加载适配器 (`src.core.model_loader_adapter.load_model_with_config`)
- 缓存分配器 (`src.core.cache_manager.allocate_cache`)

## 扩展自定义探针

要添加自定义探针，可以使用以下方法：

1. **装饰器方法**：
```python
from src.probes import probe_memory

@probe_memory(level="critical")
def my_memory_intensive_function():
    # 函数内容
    pass
```

2. **手动插入检查点**：
```python
from src.probes import check_memory

def my_function():
    # 初始检查
    check_memory("before_operation")
    
    # 执行内存密集操作
    result = perform_operation()
    
    # 操作后检查
    check_memory("after_operation")
    return result
```

3. **C语言高性能探针**：
```python
from src.probes import fast_check

def performance_critical_function():
    # 只在内存超过阈值时触发警告，几乎没有开销
    fast_check(threshold_mb=500)
    # 执行操作
```

## 运行测试

可以使用以下命令运行探针系统测试：

- Windows:
```
scripts\run_memory_probes.bat
```

- Linux/macOS:
```
./scripts/run_memory_probes.sh
```

## 编译C扩展

如果需要手动编译C扩展，可以使用以下命令：

- Windows:
```
scripts\build_memory_probes.bat
```

- Linux/macOS:
```
./scripts/build_memory_probes.sh
```

## 注意事项

1. 探针级别说明：
   - `low`: 低频监控，适用于一般函数
   - `medium`: 中等频率监控，默认级别
   - `high`: 高频监控，适用于内存密集操作
   - `critical`: 最高级别监控，适用于关键核心操作

2. 在性能关键路径上，优先使用C探针以减少开销

3. 探针会在内存压力过大时自动触发垃圾回收 