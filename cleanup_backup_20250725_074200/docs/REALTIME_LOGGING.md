# VisionAI-ClipsMaster 实时日志系统

本文档描述了 VisionAI-ClipsMaster 项目中的实时日志系统设计和使用方法。该系统旨在提供高性能、低延迟的日志记录功能，特别适用于高并发和大数据量场景。

## 1. 系统概述

实时日志系统包含以下主要组件：

1. **异步日志写入器** (`AsyncLogWriter`): 在后台线程中处理日志写入操作
2. **实时日志记录器** (`RealtimeLogger`): 提供内存缓冲和批量写入功能
3. **实时日志集成器** (`RealtimeLogIntegrator`): 将实时日志系统与结构化日志系统集成

整个系统设计遵循以下原则：

- **高性能**: 通过内存缓冲和异步写入提高日志记录性能
- **低延迟**: 减少日志记录对主线程的影响
- **容错性**: 支持失败重试和错误处理
- **批量处理**: 减少 I/O 操作，提高写入效率
- **与结构化日志集成**: 结合结构化日志系统的优势，同时保持高性能

## 2. 主要特性

- **内存缓冲**: 缓冲日志条目，减少 I/O 操作
- **异步写入**: 在后台线程中处理日志写入
- **批量处理**: 批量写入日志，提高效率
- **失败重试**: 自动重试失败的写入操作
- **自动分割**: 按日期自动分割日志文件
- **性能统计**: 提供详细的性能统计信息
- **线程安全**: 支持多线程并发写入

## 3. 使用方法

### 3.1 基本用法

```python
from src.exporters.log_writer import get_realtime_logger

# 获取全局实时日志记录器
logger = get_realtime_logger()

# 记录日志
logger.log({
    "timestamp": "2023-11-01T12:34:56",
    "level": "INFO",
    "message": "这是一条测试日志"
})

# 确保日志写入文件（在程序结束前调用）
logger.flush()
```

### 3.2 与结构化日志集成

```python
from src.exporters.log_integration_realtime import log_realtime, get_log_integrator

# 方法1: 使用便捷函数
log_realtime({
    "operation": "export",
    "result": "success",
    "processing_stats": {
        "processing_time": 2.5,
        "clips_created": 8
    }
})

# 方法2: 使用集成器
integrator = get_log_integrator()
integrator.log({
    "operation": "clip",
    "result": "success",
    "video_info": {
        "duration": 120.5,
        "resolution": "1920x1080"
    }
})

# 确保日志写入
integrator.flush()
```

### 3.3 使用装饰器

```python
from src.exporters.log_integration_realtime import realtime_log

# 使用实时日志装饰器
@realtime_log("math_operation", category="arithmetic")
def add_numbers(a, b):
    return a + b

# 调用函数时会自动记录日志
result = add_numbers(1, 2)
```

### 3.4 自定义日志记录器

```python
from src.exporters.log_writer import RealtimeLogger

# 创建自定义日志记录器
logger = RealtimeLogger(
    log_dir="logs/custom",
    file_prefix="my_app",
    buffer_size=5000,  # 更大的缓冲区
    auto_flush_interval=10.0  # 每10秒自动刷新
)

# 记录日志
logger.log({"message": "自定义日志记录器测试"})

# 获取统计信息
stats = logger.get_stats()
print(stats)

# 关闭日志记录器
logger.shutdown()
```

## 4. 性能优化建议

1. **增大缓冲区**: 对于高并发场景，可以增大缓冲区大小（`buffer_size`）
2. **调整刷新间隔**: 根据性能需求调整自动刷新间隔（`auto_flush_interval`）
3. **减少验证**: 如果性能是首要考虑因素，可以关闭日志验证（`validate=False`）
4. **批量记录**: 尽可能一次记录多个日志，而不是多次调用 log 方法
5. **定时刷新**: 对于长时间运行的应用，定期手动调用 flush 方法

## 5. 与结构化日志系统的集成

实时日志系统可以与结构化日志系统（`structured_logger.py`）无缝集成，同时获得两者的优势：

- **结构化日志系统**: 提供格式验证、查询和分析功能
- **实时日志系统**: 提供高性能、低延迟的日志记录

集成器（`RealtimeLogIntegrator`）会同时将日志发送到两个系统，同时处理错误情况和性能统计。

## 6. 故障排除

### 6.1 内存使用过高

如果发现内存使用过高，可以尝试以下方法：

1. 减小缓冲区大小（`buffer_size`）
2. 减少自动刷新间隔（`auto_flush_interval`）
3. 定期手动调用 `flush()` 方法

### 6.2 日志丢失

如果发现日志丢失，可能的原因包括：

1. 程序异常退出，没有正确调用 `flush()` 或 `shutdown()`
2. 磁盘空间不足
3. 写入权限问题

确保在程序结束前调用 `flush()` 或 `shutdown()` 方法，并检查磁盘空间和权限。

### 6.3 性能问题

如果日志记录影响了应用性能，可以尝试以下方法：

1. 增大缓冲区大小
2. 禁用结构化日志（`enable_structured_logging=False`）
3. 减少日志数量，只记录重要事件
4. 使用更简单的日志格式，减少序列化开销

## 7. 示例应用场景

### 7.1 高并发视频处理

对于同时处理多个视频的场景，实时日志系统可以记录各个处理任务的状态和性能指标，而不会影响处理速度。

```python
@realtime_log("video_processing", video_type="mp4")
def process_video(video_path):
    # 处理视频...
    return result
```

### 7.2 性能监控

实时记录应用资源使用情况，用于性能监控和优化。

```python
def monitor_resources():
    while True:
        resource_info = collect_resource_usage()
        log_realtime({
            "operation": "monitor",
            "resource_usage": resource_info
        })
        time.sleep(5)  # 每5秒记录一次
```

### 7.3 错误跟踪

快速记录和分析错误，提高故障排除效率。

```python
try:
    result = some_operation()
except Exception as e:
    log_realtime({
        "operation": "some_operation",
        "result": "error",
        "error": {
            "code": type(e).__name__,
            "message": str(e)
        }
    })
    raise  # 重新抛出异常
```

## 8. 运行测试

我们提供了一个测试脚本 `src/test_realtime_logging.py`，用于演示和测试实时日志系统的所有功能：

```bash
python -m src.test_realtime_logging
```

该脚本会执行多种测试场景，包括基本日志记录、并发日志记录、高吞吐量测试等，并输出性能指标。 