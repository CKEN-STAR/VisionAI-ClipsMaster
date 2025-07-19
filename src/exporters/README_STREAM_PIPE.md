# 流式处理管道 (Stream Processing Pipeline)

流式处理管道是VisionAI-ClipsMaster项目中的一个核心组件，提供高效的数据流处理框架，特别适用于视频和音频等媒体处理。通过零拷贝机制和流水线设计模式，该模块能够显著提高大型数据处理的效率，同时提供灵活的组合方式处理复杂任务。

## 功能特点

- **零拷贝机制**: 通过引用传递而非数据复制来提高处理效率，特别适用于大型视频/音频数据
- **组合式设计**: 支持将复杂处理流程分解为简单可组合的处理单元
- **多种处理器类型**: 提供函数处理器、转换处理器、过滤处理器和组合处理器等多种类型
- **专业媒体处理器**: 内置视频处理器和音频处理器基类，简化媒体处理开发
- **流式处理支持**: 支持分块处理大型数据流，适用于超大文件处理
- **错误处理机制**: 内置错误处理和恢复功能
- **性能监控**: 自动记录各处理阶段的性能统计信息

## 核心类

- `ZeroCopyPipeline`: 零拷贝管道基类，提供基础管道处理功能
- `StreamingPipeline`: 流式处理管道，支持分块处理大型数据
- `Processor`: 处理器抽象基类，定义处理器接口
- `VideoProcessor`: 视频处理器基类，简化视频帧处理
- `AudioProcessor`: 音频处理器基类，简化音频数据处理

## 使用方法

### 基本用法

```python
from src.exporters.stream_pipe import ZeroCopyPipeline

# 创建管道
pipeline = ZeroCopyPipeline()

# 添加处理阶段
pipeline.add_stage(lambda x: x * 2)
pipeline.add_stage(lambda x: x + 10)

# 执行管道
result = pipeline.execute(5)  # 结果: 20

# 查看性能统计
stats = pipeline.get_stats()
print(stats)
```

### 自定义处理器

```python
from src.exporters.stream_pipe import Processor, ZeroCopyPipeline

# 定义自定义处理器
class MyProcessor(Processor):
    def __init__(self):
        super().__init__("MyProcessor")
        
    def process(self, data):
        # 进行处理
        processed_data = data + 1
        return processed_data

# 创建管道并添加处理器
pipeline = ZeroCopyPipeline()
pipeline.add_stage(MyProcessor())

# 执行管道
result = pipeline.execute(10)  # 结果: 11
```

### 视频处理示例

```python
import cv2
import numpy as np
from src.exporters.stream_pipe import VideoProcessor, ZeroCopyPipeline

# 定义视频处理器
class GrayscaleConverter(VideoProcessor):
    def __init__(self):
        super().__init__("GrayscaleConverter")
        
    def process_frame(self, frame):
        # 处理单帧
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

# 创建管道
pipeline = ZeroCopyPipeline()
pipeline.add_stage(GrayscaleConverter())

# 读取视频帧
video_frames = ...  # 从视频文件或相机获取的帧

# 执行处理
processed_frames = pipeline.execute(video_frames)
```

### 流式处理大型数据

```python
from src.exporters.stream_pipe import StreamingPipeline

# 创建流式处理管道
pipeline = StreamingPipeline(chunk_size=30)  # 每次处理30帧

# 添加处理阶段
pipeline.add_stage(...)

# 定义数据生成器函数
def data_generator():
    for i in range(100):
        # 生成或读取数据块
        yield create_data_chunk(i)

# 流式处理
for result_chunk in pipeline.process_stream(data_generator()):
    # 处理结果块
    process_result(result_chunk)
```

### 错误处理

```python
from src.exporters.stream_pipe import ZeroCopyPipeline

# 创建管道
pipeline = ZeroCopyPipeline()

# 添加可能出错的处理阶段
pipeline.add_stage(lambda x: x / 0)  # 将引发除零错误

# 设置错误处理器
def handle_error(error, context):
    print(f"捕获到错误: {error}")
    return 0  # 返回默认值

pipeline.set_error_handler(handle_error)

# 执行管道，错误会被捕获并处理
result = pipeline.execute(10)  # 结果: 0
```

### 使用工厂函数

```python
from src.exporters.stream_pipe import create_pipeline, create_processor

# 使用工厂函数创建管道
pipeline = create_pipeline()

# 使用工厂函数创建处理器
transform_processor = create_processor('transform', lambda x: x * 2)
filter_processor = create_processor('filter', lambda x: x > 0)

# 添加处理器
pipeline.add_stage(transform_processor)
pipeline.add_stage(filter_processor)
```

## 进阶用法

### 组合处理器

```python
from src.exporters.stream_pipe import CompositeProcessor, FunctionProcessor

# 创建组合处理器
composite = CompositeProcessor(name="数学处理器")

# 添加多个子处理器
composite.add_processor(FunctionProcessor(lambda x: x * 2, "乘2"))
composite.add_processor(FunctionProcessor(lambda x: x + 5, "加5"))
composite.add_processor(FunctionProcessor(lambda x: x ** 2, "平方"))

# 使用组合处理器
result = composite(3)  # ((3*2)+5)^2 = 121
```

### 处理模式设置

```python
from src.exporters.stream_pipe import ZeroCopyPipeline, ProcessingMode

# 创建管道
pipeline = ZeroCopyPipeline()

# 设置处理模式
pipeline.set_mode(ProcessingMode.BATCH)  # 批处理模式
# 或
pipeline.set_mode(ProcessingMode.STREAMING)  # 流式处理模式
# 或
pipeline.set_mode(ProcessingMode.PARALLEL)  # 并行处理模式
```

## 最佳实践

1. **使用专用处理器类型**: 根据处理需求选择合适的处理器类型，如视频处理用`VideoProcessor`
2. **保持处理器单一职责**: 每个处理器只负责一项明确的任务，便于组合和重用
3. **流式处理大型数据**: 对于大型视频或音频文件，使用`StreamingPipeline`进行分块处理
4. **错误处理**: 始终设置错误处理器，确保出现异常时可以优雅恢复
5. **性能监控**: 定期检查管道统计信息，找出性能瓶颈

## 示例代码

更多示例请参考 `examples/stream_pipe_demo.py` 