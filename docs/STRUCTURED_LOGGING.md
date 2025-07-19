# VisionAI-ClipsMaster 结构化日志系统

本文档描述了 VisionAI-ClipsMaster 项目中的结构化日志系统设计和使用方法。该系统旨在提供统一的日志记录、分析和可视化功能，帮助开发人员和用户更好地理解应用程序的运行状态和性能。

## 1. 系统概述

结构化日志系统包含以下主要组件：

1. **日志模式定义** (`log_schema.py`): 定义日志数据结构和验证规则
2. **结构化日志记录器** (`structured_logger.py`): 提供日志记录功能
3. **日志分析器** (`log_analyzer.py`): 分析日志数据，提供统计信息
4. **日志可视化器** (`log_visualizer.py`): 生成可视化图表和仪表板
5. **日志集成模块** (`log_integration.py`): 将日志系统集成到应用程序中

整个系统设计遵循以下原则：

- **结构化数据**: 所有日志以结构化格式存储，便于查询和分析
- **数据验证**: 强制验证日志数据格式，确保数据一致性
- **性能监控**: 自动记录资源使用情况和处理时间
- **隐私保护**: 支持敏感数据掩码处理
- **可视化分析**: 提供直观的图表和仪表板

## 2. 安装依赖

结构化日志系统需要以下依赖项：

```bash
pip install -r requirements_logging.txt
```

或者直接安装各个依赖：

```bash
pip install loguru pandas numpy matplotlib plotly jinja2 psutil
```

## 3. 使用方法

### 3.1 基本用法

```python
from src.exporters.structured_logger import get_structured_logger

# 获取全局日志记录器
logger = get_structured_logger()

# 记录操作日志
logger.log_operation(
    operation="clip",  # 操作类型
    result="success",  # 操作结果
    video_info={       # 其他信息
        "duration": 120.5,
        "resolution": "1920x1080"
    }
)

# 记录错误日志
logger.log_operation(
    operation="export",
    result="error",
    error={
        "code": "IOError",
        "message": "无法写入文件"
    }
)
```

### 3.2 使用装饰器

```python
from src.exporters.log_integration import log_operation, log_video_process

# 操作日志装饰器
@log_operation("math_operation", category="arithmetic")
def add_numbers(a, b):
    return a + b

# 视频处理日志装饰器
@log_video_process("video_processing", video_info={"format": "mp4"})
def process_video(video_path):
    # 处理视频...
    return {
        "clips": ["clip1.mp4", "clip2.mp4"],
        "duration": 60.5
    }
```

### 3.3 错误日志记录

```python
from src.exporters.log_integration import log_error

try:
    # 执行可能出错的操作
    result = some_function()
except Exception as e:
    # 记录错误
    log_error(e, "function_name", {"additional": "info"})
    raise  # 可选：重新抛出异常
```

### 3.4 模型使用日志

```python
from src.exporters.log_integration import log_model_usage

# 记录模型使用
log_model_usage(
    model_name="Qwen2.5-7B",
    language="zh",
    operation="text_generation",
    parameters={
        "temperature": 0.7,
        "top_p": 0.9
    }
)
```

### 3.5 生成分析报告和仪表板

```python
from src.exporters.log_integration import get_logging_manager

# 获取日志管理器
manager = get_logging_manager()

# 生成分析报告
report_path = manager.generate_report()
print(f"报告已生成: {report_path}")

# 生成可视化仪表板
dashboard_path = manager.generate_dashboard()
print(f"仪表板已生成: {dashboard_path}")

# 导出日志数据
manager.export_logs("logs/export.json", format="json")
manager.export_logs("logs/export.csv", format="csv")
```

## 4. 日志数据结构

结构化日志使用以下主要字段：

- `timestamp`: 日志时间戳 (ISO格式)
- `operation`: 操作类型 (如 "init", "clip", "export" 等)
- `result`: 操作结果 (如 "success", "warning", "error")
- `user_id`: 用户ID (可选，支持部分掩码)
- `session_id`: 会话ID
- `event_type`: 事件类型
- `resource_usage`: 资源使用情况 (内存、CPU、GPU)
- `model_info`: 模型信息 (如果使用了模型)
- `video_info`: 视频信息 (如果处理了视频)
- `processing_stats`: 处理统计信息
- `error`: 错误信息 (如果发生错误)

完整的日志模式定义可以在 `src/exporters/log_schema.py` 中找到。

## 5. 日志分析报告

日志分析报告包含以下主要内容：

1. **会话统计**: 会话数量、持续时间和系统信息
2. **操作统计**: 各类操作的数量和成功率
3. **资源使用**: 内存和CPU使用情况
4. **性能分析**: 处理时间统计和趋势
5. **错误分析**: 错误类型和分布

报告以HTML格式生成，可以在浏览器中查看。

## 6. 调试和排错

### 6.1 查看日志文件

日志文件存储在 `logs/structured/{日期}/{会话ID}/` 目录下，以JSONL格式保存。可以使用以下命令查看日志内容：

```bash
cat logs/structured/2023-11-01/{会话ID}/visionai_clips_master.jsonl | jq
```

### 6.2 验证日志格式

可以使用 `validate_log` 函数验证日志数据是否符合模式定义：

```python
from src.exporters.log_schema import validate_log, EXPORT_LOG_SCHEMA

# 验证日志数据
try:
    is_valid = validate_log(log_data, EXPORT_LOG_SCHEMA)
    print("日志验证成功")
except ValueError as e:
    print(f"日志验证失败: {e}")
```

## 7. 最佳实践

1. **合理分类操作**: 保持操作类型的一致性，便于后续分析
2. **添加上下文信息**: 在日志中添加足够的上下文信息，帮助理解操作场景
3. **及时分析日志**: 定期生成和查看分析报告，发现潜在问题
4. **保护敏感信息**: 使用掩码功能处理用户ID等敏感数据
5. **保持日志精简**: 避免记录过大的对象或二进制数据，影响性能

## 8. 与其他系统集成

结构化日志系统可以与以下系统集成：

- **错误报告系统**: 将错误日志发送给错误报告系统
- **监控系统**: 将性能指标发送给监控系统
- **数据分析平台**: 导出日志数据进行深度分析
- **CI/CD流程**: 在自动化测试中生成性能报告

## 9. 运行测试

我们提供了一个测试脚本 `src/test_structured_logging.py`，用于演示和测试结构化日志系统的所有功能：

```bash
python -m src.test_structured_logging
```

该脚本会生成示例日志数据，并执行分析和可视化操作，输出测试结果。 