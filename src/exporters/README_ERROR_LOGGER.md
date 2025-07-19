# 智能错误日志系统

智能错误日志系统为VisionAI-ClipsMaster项目提供先进的错误日志记录、分析和故障排除功能。该系统专为处理导出流程中的各类复杂错误而设计，具有内存分析、错误模式识别和智能聚合能力。

## 主要功能

- **结构化JSON日志**: 以结构化格式记录所有错误，包含丰富的上下文信息
- **内存状态捕获**: 发生错误时自动捕获进程内存状态，助力排查内存相关问题
- **系统资源监控**: 记录CPU、内存和磁盘使用情况，帮助识别资源瓶颈
- **错误去重与聚合**: 通过智能哈希算法对相似错误进行去重和聚合
- **错误模式识别**: 自动识别重复出现的错误模式，提前预警潜在问题
- **多格式导出**: 支持将错误日志导出为JSON、CSV或HTML格式
- **上下文管理**: 简化不同阶段的错误捕获和日志记录
- **装饰器支持**: 通过简单的装饰器为任何函数添加错误日志功能

## 使用方法

### 基本使用

```python
from src.exporters.error_logger import get_export_logger, log_export_error

# 获取日志记录器
logger = get_export_logger()

# 设置当前上下文（导出阶段和视频哈希）
logger.set_context(phase="RENDERING", video_hash="3a7bd3e2f")

try:
    # 执行可能出错的操作
    process_video()
except Exception as e:
    # 记录错误
    logger.log_structured_error(e, context={"custom_data": "value"})
```

### 使用上下文管理器

```python
from src.exporters.error_logger import get_export_logger

logger = get_export_logger()

# 使用上下文管理器自动捕获和记录错误
with logger.log_errors(phase="ENCODING", video_hash="3a7bd3e2f"):
    # 此块中的任何异常将自动被捕获并记录
    encode_video()
    
# 正常执行继续
print("完成")
```

### 使用装饰器

```python
from src.exporters.error_logger import with_error_logging

# 为函数添加自动错误日志记录
@with_error_logging(phase="VIDEO_PROCESSING")
def process_video(video_data):
    # 函数中的任何异常都会被自动捕获并记录
    # 函数的参数会被检查是否包含video_hash
    result = do_processing(video_data)
    return result
```

### 快速记录错误

```python
from src.exporters.error_logger import log_export_error

try:
    # 执行操作
    validate_input(data)
except Exception as e:
    # 快速记录错误
    log_export_error(e, phase="VALIDATION", video_hash="3a7bd3e2f")
    # 适当处理异常
    raise
```

## 错误模式识别

系统能够自动识别重复出现的错误模式，并在日志中提供警告：

```python
# 查看错误统计和模式
stats = logger.get_error_stats()
print(f"总错误数: {stats['total_errors']}")
print(f"独立错误数: {stats['unique_errors']}")
print("最常见错误:")
for error_hash, count in stats['most_frequent'].items():
    print(f"  - {error_hash}: {count}次")
```

## 日志导出

可以将错误日志导出为不同格式，便于分析和报告：

```python
# 导出为JSON
json_data = logger.export_logs(format="json")

# 导出为CSV
csv_data = logger.export_logs(format="csv")

# 导出为HTML报告
logger.export_logs(format="html", output_file="error_report.html")
```

## 与异常分类系统集成

智能错误日志系统设计为与项目的异常分类系统无缝集成，提供更精确的错误分类和处理建议：

```python
from src.utils.exception_classifier import classify_exception

try:
    # 执行操作
    process_complex_task()
except Exception as e:
    # 分类异常
    classification = classify_exception(e)
    
    # 记录带有分类信息的错误
    logger.log_structured_error(e, context={"classification": classification.to_dict()})
```

## 配置选项

ExportLogger类支持多种配置选项，以适应不同的使用场景：

```python
# 自定义日志记录器
logger = ExportLogger(
    log_file="custom/path/errors.json",  # 自定义日志文件路径
    max_logs=2000,                       # 单个文件最大记录数
    retention_days=60,                   # 日志保留天数
    auto_flush=True                      # 自动刷新到磁盘
)
```

## 性能考虑

系统设计时考虑了在资源受限环境下的性能表现：

1. **懒加载**: 系统组件按需加载，最小化内存使用
2. **批量处理**: 错误日志批量刷新到磁盘，减少I/O开销
3. **优雅降级**: 在无法获取完整系统信息时，自动降级到基本信息收集
4. **文件轮转**: 自动管理日志文件大小，防止过大影响性能

## 最佳实践

- 在所有关键导出阶段使用错误日志系统
- 为错误提供尽可能多的上下文信息
- 定期分析错误模式，识别系统性问题
- 在长时间运行的进程中，定期调用`flush()`确保日志写入磁盘
- 对于性能敏感的部分，使用自定义上下文而不是完整内存转储 