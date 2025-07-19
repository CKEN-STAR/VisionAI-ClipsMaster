# 资源回收引擎 (Resource Cleaner)

资源回收引擎是VisionAI-ClipsMaster项目的重要组成部分，负责管理和回收系统资源，确保应用程序高效运行并防止资源泄露。此模块在视频处理和AI模型应用过程中尤为重要，因为这些操作通常会消耗大量系统资源。

## 主要功能

- **紧急资源回收**：在异常或错误发生时快速释放所有资源
- **常规资源回收**：在操作完成后有序地清理资源
- **定时资源回收**：对长时间运行的任务进行周期性资源优化
- **智能资源监控**：根据系统负载自动调整资源使用策略
- **多类型资源管理**：支持文件句柄、内存、GPU内存、临时文件、数据库连接等资源类型
- **上下文管理器支持**：提供方便的`with`语法支持，简化资源管理

## 优先级系统

资源清理器使用优先级系统来控制清理的范围和强度：

- **低优先级(LOW)**：只清理不重要的资源，如临时文件
- **中优先级(MEDIUM)**：清理大部分资源，包括临时缓冲区
- **高优先级(HIGH)**：清理所有非关键资源，包括内存和GPU内存
- **紧急优先级(CRITICAL)**：强制清理所有资源，用于紧急情况

## 使用方法

### 基本用法

```python
from src.exporters.resource_cleaner import get_resource_cleaner, CleanupPriority

# 获取资源清理器实例
cleaner = get_resource_cleaner()

# 注册需要清理的资源
cleaner.register_temp_dir("/path/to/temp/dir")
cleaner.register_file_handle("log_file", file_handle)
cleaner.register_gpu_buffer("model_buffer", {"tensor": tensor})
cleaner.register_db_connection("main_db", db_conn)

# 执行资源清理
result = cleaner.clean(CleanupPriority.MEDIUM)
print(f"清理了 {result['cleaned_items']} 项资源")
```

### 作为上下文管理器使用

```python
from src.exporters.resource_cleaner import resource_cleanup_context

# 使用上下文管理器进行资源管理
with resource_cleanup_context("video_processing") as context:
    # 创建临时目录
    temp_dir = create_temp_directory()
    context["temp_dir"] = temp_dir  # 记录在上下文中，将自动清理
    
    # 打开文件
    file_handle = open("output.log", "w")
    context["open_files"] = {"log": file_handle}  # 记录在上下文中，将自动关闭
    
    # 分配缓冲区
    buffer_key = allocate_buffer()
    context["buffer_keys"] = [buffer_key]  # 记录在上下文中，将自动释放
    
    # 建立数据库连接
    db_conn = connect_to_database()
    context["db_conn"] = db_conn  # 记录在上下文中，将自动关闭
    
    # 处理视频...
    process_video()

# 退出上下文时自动清理所有资源
```

### 紧急清理

```python
from src.exporters.resource_cleaner import emergency_cleanup

try:
    # 执行风险操作
    perform_risky_operation()
except Exception as e:
    # 发生异常，执行紧急清理
    cleanup_result = emergency_cleanup()
    print(f"紧急清理完成，状态：{cleanup_result['status']}")
    # 重新抛出异常
    raise
```

### 注册自定义清理器

```python
from src.exporters.resource_cleaner import get_resource_cleaner, CleanupPriority

def custom_resource_cleaner(context):
    """自定义清理函数"""
    # 执行特定的清理逻辑
    # ...
    return {"cleaned_items": 1, "details": "清理了自定义资源"}

# 注册自定义清理器
cleaner = get_resource_cleaner()
cleaner.register_cleaner(custom_resource_cleaner, CleanupPriority.MEDIUM)
```

## 集成方式

资源回收引擎与系统的其他部分集成，包括：

1. **内存管理器**：利用内存管理器进行内存优化和监控
2. **缓冲区管理器**：清理临时缓冲区和流缓冲区
3. **显存检测器**：监控和清理GPU显存
4. **存储管理器**：管理数据库连接和数据存储资源

## 设计考量

- **优雅降级**：当某些依赖组件不可用时，资源清理器会优雅降级，跳过相应的清理步骤
- **异常安全**：即使在清理过程中发生异常，也会尝试清理尽可能多的资源
- **线程安全**：所有操作都是线程安全的，可以在多线程环境中使用
- **资源依赖关系**：清理时考虑了资源之间的依赖关系，确保按正确顺序释放
- **可扩展性**：通过自定义清理器机制支持扩展

## 应用场景

1. **视频导出**：视频处理完成后回收大量内存和临时文件
2. **批量处理**：在处理多个视频文件之间回收资源
3. **长时间运行**：对于长时间运行的任务，定期回收资源
4. **错误恢复**：在发生错误时快速回收资源，避免资源泄露
5. **硬件资源受限**：在低端设备上更积极地回收资源

## 最佳实践

1. 尽可能使用上下文管理器，而不是直接调用清理方法
2. 为不同的操作阶段选择合适的清理优先级
3. 在处理大文件或执行内存密集型操作后，主动调用资源清理
4. 注册所有临时资源，确保它们能被正确清理
5. 在开发自定义模块时，考虑如何与资源清理器集成

## 性能考量

资源清理过程本身也会消耗一定的系统资源。在设计中，我们尽量平衡了清理的彻底性和清理过程的开销。对于时间关键的操作，可以选择低优先级清理，减少清理的开销；而对于资源关键的情况，可以选择高优先级清理，确保尽可能多的资源被回收。 