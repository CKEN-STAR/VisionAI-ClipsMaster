# 回退引擎 (Fallback Engine)

回退引擎是 VisionAI-ClipsMaster 的核心组件之一，提供智能化的处理模式选择和资源管理功能。该模块能够在系统资源不足或硬件加速不可用时自动降级，确保系统稳定性和性能。

## 主要功能

- 自动检测零拷贝能力
- 资源不足时自动降级处理
- 处理策略自适应选择
- 错误恢复和降级处理链
- 多种处理模式支持(零拷贝/传统/混合/自动)

## 处理模式

回退引擎支持多种处理模式:

1. **零拷贝模式 (ZERO_COPY)**: 通过内存映射和指针传递避免不必要的数据拷贝，适用于处理大型视频文件。
2. **传统模式 (TRADITIONAL)**: 完整数据复制，适用于小文件或零拷贝不可用的情况。
3. **混合模式 (HYBRID)**: 根据数据大小智能选择处理方式。
4. **自动模式 (AUTO)**: 系统根据当前资源状态自动选择最佳处理模式。

## 使用方法

### 基本用法

```python
from src.exporters.fallback_engine import safe_zero_copy

# 安全处理 - 自动尝试零拷贝，不可用时回退到传统方式
result = safe_zero_copy(input_data)
print(f"处理结果: {result}")
```

### 高级用法 - 手动控制回退机制

```python
from src.exporters.fallback_engine import get_fallback_engine, ProcessingMode

# 获取回退引擎实例
engine = get_fallback_engine()

# 注册处理器
engine.register_processor(
    "video_processor",           # 处理器名称
    zero_copy_video_process,     # 零拷贝处理函数
    traditional_video_process    # 传统处理函数
)

# 使用自动模式处理数据
result = engine.process_with_fallback(
    "video_processor",           # 处理器名称
    video_path,                  # 输入数据
    mode=ProcessingMode.AUTO,    # 处理模式
    start_frame=0,               # 其他参数
    frame_count=30
)

# 获取回退状态
status = engine.get_fallback_status()
print(f"回退状态: {status}")
```

### 自定义零拷贝和传统处理函数

```python
def my_zero_copy_process(data):
    """自定义零拷贝处理函数
    
    Args:
        data: 输入数据
        
    Returns:
        处理结果
    """
    # 零拷贝实现，例如使用内存映射或指针传递
    # ...
    
    return processed_data


def my_traditional_process(data):
    """自定义传统处理函数
    
    Args:
        data: 输入数据
        
    Returns:
        处理结果
    """
    # 传统实现，可能涉及完整数据复制
    # ...
    
    return processed_data


# 注册自定义处理器
engine = get_fallback_engine()
engine.register_processor("my_processor", my_zero_copy_process, my_traditional_process)
```

## 内存管理

回退引擎内置了内存监控功能，可以在内存使用率超过阈值时自动选择更低资源消耗的处理方式。默认情况下，当内存使用率超过90%时会触发回退机制，可以通过修改引擎的 `fallback_thresholds` 来调整这个阈值。

```python
engine = get_fallback_engine()
# 调整回退阈值
engine.fallback_thresholds['memory'] = 0.85  # 内存使用率超过85%触发回退
```

## 集成示例

### 与视频处理管道集成

```python
from src.exporters.fallback_engine import get_fallback_engine
from src.exporters.stream_pipe import ZeroCopyPipeline, Processor

class VideoProcessor(Processor):
    """视频处理器"""
    
    def __init__(self, name=None):
        super().__init__(name or "VideoProcessor")
        self.fallback_engine = get_fallback_engine()
        
    def process(self, video_path):
        """处理视频文件
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            处理结果
        """
        return self.fallback_engine.process_with_fallback(
            "video_processor",
            video_path
        )
```

### 错误处理

```python
from src.exporters.fallback_engine import ZeroCopyUnavailableError

try:
    result = engine.process_with_fallback("processor_name", input_data)
except ZeroCopyUnavailableError as e:
    # 零拷贝不可用且回退也失败
    print(f"处理失败: {e}")
    # 执行后备处理逻辑
```

## API 参考

### 主要类

- `FallbackEngine`: 回退引擎核心类
- `ProcessingMode`: 处理模式枚举
- `ZeroCopyUnavailableError`: 零拷贝不可用异常

### 主要函数

- `get_fallback_engine()`: 获取全局回退引擎实例
- `safe_zero_copy(input_data, fallback_threshold=0.9)`: 安全零拷贝处理函数
- `get_memory_usage()`: 获取当前内存使用率 