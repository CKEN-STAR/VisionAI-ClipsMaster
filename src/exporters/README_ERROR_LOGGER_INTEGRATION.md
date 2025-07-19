# 智能错误日志系统与异常分类系统集成

集成模块提供智能错误日志系统与异常分类系统的无缝协作，显著增强项目的错误处理能力。此模块实现了基于错误分类的智能恢复机制和高级错误分析，是强大的故障排除和系统稳定性工具。

## 主要功能

- **集成异常分类**：自动将捕获的错误与异常分类系统关联，提供更丰富的上下文信息
- **智能恢复机制**：基于错误类型和异常分类，自动应用适当的恢复策略
- **错误模式分析**：识别重复出现的错误模式，提供趋势分析
- **多格式报告生成**：支持HTML、JSON、Markdown等多种格式的高级错误报告
- **优雅降级**：当异常分类系统不可用时，自动降级到基本错误日志功能
- **装饰器支持**：通过简单的装饰器为任何函数添加带分类的错误日志功能

## 使用方法

### 基本使用

```python
from src.exporters.error_logger_integration import get_integrated_logger, log_classified_error

# 获取集成日志记录器
logger = get_integrated_logger()

try:
    # 执行可能出错的操作
    process_video_data()
except Exception as e:
    # 记录带分类的错误
    log_classified_error(e, phase="VIDEO_PROCESSING", video_hash="3a7bd3e2f")
```

### 使用装饰器

```python
from src.exporters.error_logger_integration import with_classified_logging

# 为函数添加带分类的错误日志记录
@with_classified_logging(phase="AUDIO_PROCESSING")
def process_audio(audio_data, video_hash=None):
    # 函数会自动提取video_hash参数
    # 任何未捕获的异常都会自动被记录并分类
    result = do_processing(audio_data)
    return result
```

### 注册恢复策略

```python
from src.exporters.error_logger_integration import get_integrated_logger

# 获取集成日志记录器
logger = get_integrated_logger()

# 创建恢复策略
def network_error_recovery(error, context):
    """网络错误恢复策略"""
    # 重试连接
    for i in range(3):
        try:
            # 尝试重新连接
            reconnect()
            return True
        except Exception:
            time.sleep(1)
    
    return False

# 注册恢复策略
logger.register_recovery_strategy("CONNECTION_ERROR", network_error_recovery)
```

### 生成高级错误报告

```python
from src.exporters.error_logger_integration import get_integrated_logger

# 获取集成日志记录器
logger = get_integrated_logger()

# 生成HTML报告
html_report = logger.generate_advanced_report(format="html")

# 导出到文件
logger.generate_advanced_report(format="md", output_file="error_report.md")
```

## 与异常分类系统的集成

错误日志集成模块与异常分类系统紧密协作：

1. 当捕获异常时，自动将其传递给异常分类系统进行分类
2. 分类结果作为上下文添加到错误日志中
3. 根据分类的严重性和类型，决定是否应用恢复策略
4. 错误报告和分析基于分类信息提供更有价值的洞察

## 恢复策略系统

恢复策略系统提供了一种智能的方式来自动处理已知类型的错误：

- 每个恢复策略都与特定的错误类型关联
- 当识别到匹配的错误类型时，应用相应的恢复策略
- 如果恢复成功，记录相关信息
- 所有尝试和结果都被记录下来，用于后续分析

### 内置恢复策略

系统预配置了几种常见错误的恢复策略：

- **内存错误恢复**：强制进行垃圾回收，尝试释放内存
- **网络错误恢复**：自动重试连接
- **资源超限恢复**：释放非关键资源，尝试继续执行

## 高级错误报告

系统支持多种格式的高级错误报告，帮助团队快速诊断和解决问题：

- **HTML报告**：包含可视化图表和交互式错误浏览
- **JSON报告**：提供结构化数据，便于程序分析
- **Markdown报告**：适合直接集成到文档系统

报告内容包括：

- 错误统计和趋势
- 按严重性和来源的错误分类
- 最频繁出现的错误
- 异常模式识别
- 恢复策略成功率分析

## 性能考虑

系统设计考虑了在资源受限环境下的性能表现：

1. **条件分类**：只在恢复可能性高的情况下进行完整分类
2. **复用上下文**：在处理相同错误时避免重复计算
3. **批量统计**：错误模式分析在后台进行，不影响主流程
4. **优雅降级**：在低资源情况下自动降级到基本功能

## 集成初始化

在应用启动时，建议调用`initialize_error_recovery()`函数，该函数会：

1. 注册所有内置恢复策略
2. 尝试加载自定义恢复策略
3. 初始化错误模式分析系统

```python
from src.exporters.error_logger_integration import initialize_error_recovery

# 初始化错误恢复系统
initialize_error_recovery() 