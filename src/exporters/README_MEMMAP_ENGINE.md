# 内存映射引擎 (Memory Mapping Engine)

内存映射引擎是VisionAI-ClipsMaster项目中的一个核心组件，用于优化视频处理过程中的内存使用和性能表现。通过使用内存映射技术，该引擎能够显著减少数据复制操作，降低内存消耗，并提高大型视频文件处理的效率。

## 功能特点

- **零拷贝机制**: 通过内存映射直接访问文件内容，避免不必要的内存拷贝
- **缓存管理**: 智能缓存常用映射，提高重复访问性能
- **资源优化**: 自动管理和释放映射资源，防止内存泄漏
- **高性能视频处理**: 优化视频帧的读取和处理流程
- **错误恢复**: 提供优雅的错误处理和回退机制
- **性能监控**: 内置性能统计和监控功能

## 使用方法

### 基本用法

```python
from src.exporters.memmap_engine import get_memmap_engine, map_video_frames

# 获取引擎实例
engine = get_memmap_engine()

# 映射视频帧
frames, frame_count = map_video_frames('video.mp4', start_frame=0, frame_count=100)

# 处理帧
for i in range(frame_count):
    # 处理每一帧
    process_frame(frames[i])

# 清理映射
engine.clear_all()
```

### 内存映射文件

```python
from src.exporters.memmap_engine import get_memmap_engine

# 获取引擎实例
engine = get_memmap_engine()

# 只读方式映射二进制文件
mapped = engine.mmap_binary_file('data.bin', 'r')

# 读取数据
data = mapped[0:1024]

# 解除映射
engine.unmap('data.bin')
```

### 创建内存映射数组

```python
import numpy as np
from src.exporters.memmap_engine import get_memmap_engine

# 获取引擎实例
engine = get_memmap_engine()

# 创建形状为(100, 100, 3)的内存映射数组
array = engine.create_memory_mapped_array(
    'output.bin', 
    shape=(100, 100, 3), 
    dtype=np.uint8, 
    mode='w+'
)

# 写入数据
array[:] = 255

# 同步到磁盘
array.flush()
```

## 性能优势

内存映射引擎带来的主要性能优势包括：

1. **内存使用效率**: 通过减少冗余拷贝，显著降低内存占用
2. **处理速度**: 尤其对大型视频文件，处理速度提升明显
3. **文件I/O优化**: 通过系统级优化提高文件访问性能
4. **资源释放**: 智能管理资源，防止内存泄漏

## 示例代码

查看 `src/demos/memmap_engine_demo.py` 了解完整的性能对比演示。该示例对比了使用传统方法和内存映射方法处理视频的性能差异。

## 技术实现

内存映射引擎基于以下技术实现：

- Python `mmap` 模块: 提供低级内存映射功能
- NumPy `memmap`: 用于创建内存映射数组
- 缓存淘汰算法: LRU (最近最少使用) 策略
- OpenCV: 用于视频解码和处理
- 单例模式: 确保系统中只有一个引擎实例

## 最佳实践

1. 对于只读操作，优先使用内存映射
2. 对于大型文件，内存映射优势更为明显
3. 处理完成后，确保调用 `clear_all()` 释放资源
4. 对于写操作频繁的场景，可能需要手动优化同步策略
5. 结合热点定位器识别性能瓶颈，优先映射热点区域

## 注意事项

- 内存映射文件大小不应超过可用物理内存，否则可能导致性能下降
- 32位系统可能存在文件大小限制，建议在64位系统上使用
- 对于非常小的文件(<1MB)，传统I/O可能更有效率
- 视频编解码器的兼容性可能影响性能优化效果 