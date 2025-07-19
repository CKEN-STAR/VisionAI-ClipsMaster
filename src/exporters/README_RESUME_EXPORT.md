# 断点续导出引擎 (Resume Export Engine)

断点续导出引擎是VisionAI-ClipsMaster项目的重要组件，用于提供可靠的导出恢复机制，确保在导出过程中断后能从上次中断点继续导出，而不必从头开始。此功能在处理大型视频项目或在不稳定环境中尤为重要。

## 主要功能

- **状态保存与恢复**：自动保存导出进度状态，在重启导出时无缝恢复
- **进度跟踪**：提供精确的进度报告，支持进度回调
- **数据校验**：使用校验和验证状态文件的完整性，确保恢复点可靠
- **优雅的错误处理**：在导出过程中断时保存状态，便于后续恢复
- **资源清理**：与资源清理器集成，确保即使在中断情况下也能正确释放资源
- **导出器适配**：为现有导出器添加断点续传能力，无需修改原有代码

## 使用方法

### 基本使用方式

```python
from src.exporters.resume_export import resumable_export_context

# 创建版本数据
version_data = {...}  # 版本数据
output_path = "path/to/output.xml"

# 使用可恢复导出上下文
with resumable_export_context() as resumer:
    # 获取起始进度
    start_progress = resumer.progress
    
    # 执行导出步骤，定期更新进度
    for step in range(total_steps):
        # 计算当前进度
        current_progress = (step + 1) / total_steps
        
        # 保存状态
        resumer.save_state(current_progress)
        
        # 执行导出操作...
        # ...
        
    # 完成导出，上下文退出时会自动清理状态
```

### 与现有导出器集成

```python
from src.exporters.resume_export import make_resumable
from src.export.jianying_exporter import JianyingExporter

# 创建标准导出器
exporter = JianyingExporter()

# 转换为可恢复导出器
resumable_exporter = make_resumable(exporter)

# 添加进度回调函数
def progress_callback(progress):
    print(f"导出进度: {progress:.2%}")

# 执行可恢复导出
result = resumable_exporter.export(
    version_data,
    output_path,
    progress_callback=progress_callback
)
```

### 处理中断

```python
from src.exporters.resume_export import get_export_resumer

try:
    # 执行导出操作
    # ...
except KeyboardInterrupt:
    # 获取当前进度
    current_progress = get_export_resumer().progress
    print(f"导出已暂停，当前进度: {current_progress:.2%}")
    print("您可以稍后继续导出")
```

## 架构设计

断点续导出引擎采用分层设计：

1. **核心续传组件** (`ExportResumer`): 负责状态的保存、加载和验证
2. **上下文管理器** (`resumable_export_context`): 提供方便的上下文语法
3. **导出器适配层** (`ResumableExporter`): 为现有导出器添加续传能力
4. **工具函数** (`make_resumable`, `get_export_resumer`): 简化使用流程

### 状态管理

导出状态以二进制形式存储，包含以下信息：

- 当前进度百分比
- 时间戳
- 校验和（确保数据完整性）

状态文件默认保存在当前目录下的`.export_state`文件中，也可以自定义路径。

## 最佳实践

1. **定期保存状态**：对于长时间运行的导出任务，建议以适当的间隔保存状态
2. **使用上下文管理器**：优先使用`resumable_export_context`上下文管理器，确保资源正确管理
3. **添加进度回调**：使用进度回调向用户提供实时反馈
4. **处理中断信号**：特别是在命令行环境中，正确处理Ctrl+C等中断信号
5. **与资源清理集成**：确保在导出过程中使用资源清理器管理临时资源

## 性能考量

状态保存操作本身是轻量级的，但频繁保存可能影响性能。默认设置为每5秒最多保存一次状态，可以根据具体需求调整`save_interval`参数。

## 使用场景

1. **大型视频项目导出**：导出大型视频项目时，避免因意外中断而从头开始
2. **批量导出**：在批量处理多个项目时，即使部分失败也能继续未完成的部分
3. **不稳定环境**：在网络或系统不稳定的环境中提供可靠的导出机制
4. **长时间运行任务**：对于需要长时间运行的导出任务，支持分阶段完成

## 示例

完整示例请参考`resume_export_example.py`文件，其中包含以下示例：

- 基本断点续导出示例
- 与真实导出器集成示例
- 中断处理示例 