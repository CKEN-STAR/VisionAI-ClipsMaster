# VisionAI-ClipsMaster 日志系统

本文档介绍 VisionAI-ClipsMaster 项目的日志系统及其使用方法。

## 概述

VisionAI-ClipsMaster 使用 Python 标准库的 `logging` 模块构建了一套完整的日志系统，支持以下功能：

- 多级别日志记录（DEBUG, INFO, WARNING, ERROR, CRITICAL）
- 同时输出到控制台和文件
- 中英文日志支持（UTF-8编码）
- 异常堆栈跟踪
- 测试日志与应用日志分离
- 按模块分类的日志记录

## 日志级别

项目使用以下日志级别：

| 级别 | 数值 | 使用场景 |
|------|------|---------|
| DEBUG | 10 | 详细的调试信息，仅在开发或排查问题时启用 |
| INFO | 20 | 标准信息，记录应用的正常运行状态 |
| WARNING | 30 | 潜在问题或不规范使用的警告 |
| ERROR | 40 | 错误信息，但应用仍可继续运行 |
| CRITICAL | 50 | 严重错误，可能导致应用终止运行 |

默认的日志级别为 INFO，可以通过环境变量 `VISIONAI_LOG_LEVEL` 修改。

## 日志格式

标准日志格式为：
```
%(asctime)s [%(levelname)s] %(name)s: %(message)s
```

格式说明：
- `%(asctime)s` - 时间戳（如：2023-01-01 12:00:00）
- `%(levelname)s` - 日志级别（如：INFO, ERROR）
- `%(name)s` - 记录器名称，通常是模块名
- `%(message)s` - 日志消息内容

## 如何使用

### 在应用代码中使用

1. 在模块顶部导入日志处理器：
   ```python
   from src.utils.log_handler import get_logger
   
   # 使用模块名作为记录器名称
   logger = get_logger(__name__)
   ```

2. 记录不同级别的日志：
   ```python
   # 信息性日志
   logger.info("模型加载成功")
   
   # 带格式化的日志
   logger.info("处理文件: %s", filename)
   
   # 警告日志
   logger.warning("检测到潜在问题：字幕时间轴不连续")
   
   # 错误日志
   logger.error("无法打开文件: %s", filename)
   
   # 异常日志（自动包含堆栈跟踪）
   try:
       result = some_operation()
   except Exception as e:
       logger.exception("操作失败: %s", e)
   ```

### 在测试代码中使用

测试代码使用独立配置的日志系统，日志文件位于 `tests/reports/pytest.log`。

1. 使用测试记录器：
   ```python
   def test_something(test_logger):
       test_logger.info("开始测试")
       # 测试代码...
       test_logger.info("测试完成")
   ```

2. 使用模块记录器：
   ```python
   from src.utils.log_handler import get_logger
   
   logger = get_logger(__name__)
   
   def test_something():
       logger.info("模块级别的日志记录")
   ```

## 配置选项

### 环境变量

可以通过环境变量控制日志行为：

- `VISIONAI_LOG_LEVEL` - 设置日志级别（默认：INFO）
- `VISIONAI_LOG_FILE` - 指定日志文件路径
- `VISIONAI_TEST_MODE` - 启用测试模式（值为1时）

### 使用API修改配置

可以在代码中动态修改日志配置：

```python
from src.utils.log_handler import setup_logger, set_global_log_level

# 创建自定义记录器
custom_logger = setup_logger(
    name="custom_module",
    level="DEBUG",
    log_file="custom.log",
    log_format="%(asctime)s - %(levelname)s - %(message)s"
)

# 修改全局日志级别
set_global_log_level("DEBUG")
```

## 测试日志系统

项目包含了测试日志系统的测试用例和验证脚本：

- `tests/test_log_config.py` - 测试日志配置是否正确
- `verify_log_config.py` - 独立验证脚本，不依赖于项目结构

### 验证日志配置

运行验证脚本：
```bash
python verify_log_config.py
```

这将生成一个验证报告，记录日志系统的各项功能是否正常工作。

## 最佳实践

1. **使用合适的日志级别**：
   - DEBUG：仅用于开发调试，不要在生产环境启用
   - INFO：记录常规操作和状态变化
   - WARNING：记录潜在问题
   - ERROR：记录实际错误
   - CRITICAL：记录致命错误

2. **结构化日志消息**：
   - 使用简洁明了的消息
   - 包含关键参数和上下文信息
   - 对于中文消息，确保使用UTF-8编码

3. **异常处理**：
   - 使用 `logger.exception()` 记录异常，它会自动包含堆栈跟踪
   - 提供足够的上下文信息，便于排查问题

4. **性能考虑**：
   - 避免在循环中过度记录日志
   - 使用 `logger.isEnabledFor(level)` 检查是否启用特定级别，再进行耗时的字符串格式化

## 常见问题解答

### Q: 如何查看日志文件？

A: 应用日志默认位于项目根目录下的 `logs/app.log`，测试日志位于 `tests/reports/pytest.log`。

### Q: 如何更改日志级别？

A: 设置环境变量 `VISIONAI_LOG_LEVEL` 为所需级别（DEBUG, INFO, WARNING, ERROR, CRITICAL）。

### Q: 日志文件会自动轮换吗？

A: 当前版本不包含日志轮换功能。在未来版本中将添加基于大小和时间的日志轮换功能。

### Q: 如何禁用某个库的日志？

A: 在 `conftest.py` 中已经为一些常用库设置了较高的日志级别。如需为其他库设置，可以使用：
```python
logging.getLogger('noisy_library').setLevel(logging.WARNING)
``` 