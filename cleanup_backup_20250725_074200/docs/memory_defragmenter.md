# 内存碎片整理 (Memory Defragmenter)

## 概述

内存碎片整理(Memory Defragmenter)是VisionAI-ClipsMaster系统的内存优化组件，专门设计用于解决长时间运行和频繁资源分配/释放过程中产生的内存碎片问题。在内存受限环境(4GB RAM/无GPU)下，这一组件对保持系统的稳定性和性能至关重要。

## 设计原则

内存碎片整理系统的设计遵循以下原则：

1. **适时触发** - 在合适的时机执行整理，如大量资源释放后或定时执行
2. **高效执行** - 使用平台特定的优化策略，保证整理过程本身不会过度占用资源
3. **平台适配** - 针对不同操作系统(Windows/Linux/macOS)提供优化的整理方法
4. **自动化运行** - 后台监控资源释放，自动触发整理，无需人工干预
5. **安全可靠** - 整理过程稳定，不影响系统其他组件的正常运行

## 主要功能

### 1. 内存碎片整理

`compact_memory()`方法是核心功能，执行以下操作：

```python
def compact_memory(self) -> bool:
    """执行内存碎片整理"""
    # 强制执行垃圾回收
    # 针对不同操作系统执行特定整理
    # 更新状态信息
```

### 2. 平台特定优化

针对不同操作系统提供了特定的内存整理方法：

- **Windows平台**：使用`SetProcessWorkingSetSize`API整理内存
- **Linux平台**：使用`malloc_trim`和文件系统同步等方法
- **macOS平台**：使用特定的内存管理调用

### 3. 自动触发机制

系统提供两种自动触发碎片整理的机制：

- **大量资源释放后触发** - 当释放内存超过配置阈值(默认500MB)时触发
- **定时触发** - 每小时自动执行一次(可配置)

### 4. 状态监控与统计

系统记录和提供详细的内存使用和整理统计信息：

- 整理次数、上次整理时间
- 进程内存使用、系统内存状态
- 整理效果统计(释放的内存量)

## 系统配置

默认配置：

```python
self.config = {
    "auto_compact_interval": 3600,    # 自动整理间隔(秒)，默认1小时
    "resource_release_threshold": 500, # 资源释放阈值(MB)，超过该值触发整理
    "post_compact_delay": 2,          # 整理后延迟(秒)
    "use_aggressive_mode": False,     # 是否使用激进模式
    "monitor_interval": 60            # 监控间隔(秒)
}
```

可通过`update_config()`方法动态更新配置。

## 集成方式

### 与资源释放系统集成

当资源被释放时，通知碎片整理器：

```python
# 在资源释放后通知碎片整理器
defragmenter = get_memory_defragmenter()
defragmenter.notify_resource_released(size_mb)
```

### 手动触发整理

在关键时刻可手动触发内存整理：

```python
# 导入便捷函数
from src.memory.defragmenter import compact_memory

# 执行内存碎片整理
compact_memory()
```

## Windows平台特定优化

在Windows平台上，内存碎片整理使用多种技术：

### 基本整理

使用Windows API整理工作集：

```python
# 参数(-1, 0, 0):
# -1：当前进程
# 0：最小工作集大小(设为0表示尽可能减小)
# 0：最大工作集大小(设为0表示尽可能减小)
ctypes.windll.kernel32.SetProcessWorkingSetSize(-1, 0, 0)
```

### 激进模式额外优化

在激进模式下，还会尝试：

1. 使用`EmptyWorkingSet`清空工作集
2. 使用`HeapCompact`紧凑化堆内存

## Linux平台特定优化

在Linux平台上，主要使用以下技术：

1. 使用`malloc_trim`释放空闲内存
2. 在激进模式下，使用`sync`刷新文件系统缓冲区，配合内存建议

## 使用示例

### 基本用法

```python
from src.memory.defragmenter import compact_memory

# 执行内存碎片整理
success = compact_memory()
if success:
    print("内存碎片整理成功")
```

### 获取内存使用状态

```python
from src.memory.defragmenter import get_memory_defragmenter

# 获取碎片整理器实例
defragmenter = get_memory_defragmenter()

# 获取内存使用状态
memory_info = defragmenter._get_memory_usage()
print(f"当前进程内存使用: {memory_info['used_mb']:.2f}MB")
print(f"系统可用内存: {memory_info['system_available_mb']:.2f}MB")
```

### 配置自动整理

```python
from src.memory.defragmenter import get_memory_defragmenter

# 获取碎片整理器实例
defragmenter = get_memory_defragmenter()

# 更新配置，更频繁地整理
defragmenter.update_config({
    "auto_compact_interval": 1800,        # 30分钟
    "resource_release_threshold": 300,    # 降低阈值到300MB
    "use_aggressive_mode": True           # 使用激进模式
})
```

## 演示程序

系统提供了演示程序`src/examples/defragmentation_demo.py`，展示内存碎片整理的功能：

```bash
# 运行演示程序
python src/examples/defragmentation_demo.py
```

演示程序展示：
1. 内存分配和碎片形成过程
2. 手动执行碎片整理及效果
3. 自动触发整理机制
4. 各平台上的优化方法

## 自动整理机制工作流程

1. **监控资源释放**：
   - 资源释放时调用`notify_resource_released(size_mb)`
   - 累积已释放内存量

2. **触发条件检查**：
   - 累积释放量超过阈值(默认500MB)
   - 距离上次整理时间至少1分钟

3. **执行整理**：
   - 调用`compact_memory()`
   - 执行垃圾回收和平台特定整理
   - 重置已释放内存计数器

4. **定时整理**：
   - 后台线程每小时自动执行一次整理
   - 可通过配置调整间隔

## 注意事项

1. **内存整理成本**：
   - 整理过程本身需要少量CPU资源
   - 整理后短暂延迟让系统稳定

2. **整理时机选择**：
   - 避免在关键操作期间整理
   - 优先在大量资源释放后整理

3. **兼容性考虑**：
   - 各平台API可能有差异
   - 代码包含适当的错误处理确保稳定

## 总结

内存碎片整理组件是VisionAI-ClipsMaster系统在内存受限环境中保持稳定运行的关键工具。通过周期性整理和特定触发条件下的碎片整理，显著改善长时间运行时的内存使用效率，提高系统整体性能和稳定性。该组件充分考虑不同操作系统的特性，提供平台优化的解决方案，确保在各种环境下的最佳表现。 