# FFmpeg零拷贝集成 (FFmpeg Zero-Copy Integration)

FFmpeg零拷贝集成是VisionAI-ClipsMaster项目中的一个核心组件，将流式处理管道与FFmpeg视频处理能力相结合，同时利用内存映射技术实现高效的视频处理。该模块显著减少视频处理过程中的内存使用，提高处理速度，特别适用于大型视频文件的处理。

## 功能特点

- **零拷贝处理**: 通过内存映射和共享内存实现视频数据的零拷贝传输
- **高效命令构建**: 优化FFmpeg命令参数，减少磁盘I/O和内存使用
- **流式处理支持**: 支持分块处理大型视频文件，降低内存峰值使用
- **可自定义设置**: 完全可配置的编码参数、预设和质量设置
- **处理能力封装**: 将常用的视频处理功能（剪切、连接等）封装为简单的接口
- **管道处理模式**: 与流式处理管道无缝集成，支持构建复杂的视频处理流程
- **错误处理机制**: 完善的错误捕获和报告机制

## 核心类

- `FFmpegExecutor`: FFmpeg命令执行器，处理底层命令执行
- `FFmpegCommandBuilder`: FFmpeg命令构建器，生成优化的FFmpeg命令
- `FFmpegSettings`: FFmpeg设置数据类，包含视频处理参数
- `FFmpegMemHandler`: 内存管理处理器，管理临时文件和内存映射
- `ZeroCopyFFmpegPipeline`: 零拷贝FFmpeg处理管道，提供高级处理接口
- `StreamingFFmpegPipeline`: 流式FFmpeg处理管道，用于处理大型视频文件

## 使用方法

### 基本用法

```python
from src.exporters.ffmpeg_zerocopy import create_ffmpeg_pipeline, FFmpegSettings, FFmpegCodec, FFmpegPreset

# 创建零拷贝FFmpeg管道
pipeline = create_ffmpeg_pipeline()

# 设置处理参数
settings = FFmpegSettings(
    video_codec=FFmpegCodec.H264,
    preset=FFmpegPreset.FAST,
    crf=23
)
pipeline.set_settings(settings)

# 剪切视频
result = pipeline.cut_video(
    input_path="input.mp4",
    output_path="output.mp4",
    start_time=10.5,
    duration=30.0
)

print(f"视频剪切完成: {result}")

# 清理临时文件
pipeline.cleanup()
```

### 视频连接

```python
from src.exporters.ffmpeg_zerocopy import create_ffmpeg_pipeline

# 创建管道
pipeline = create_ffmpeg_pipeline()

# 连接多个视频
result = pipeline.concat_videos(
    input_files=["part1.mp4", "part2.mp4", "part3.mp4"],
    output_path="combined.mp4"
)

print(f"视频连接完成: {result}")
```

### 使用工厂函数

```python
from src.exporters.ffmpeg_zerocopy import cut_video, concat_videos, FFmpegSettings

# 直接剪切视频
output_file = cut_video(
    input_path="input.mp4",
    output_path="output.mp4",
    start_time=10.5,
    duration=30.0
)

# 直接连接视频
output_file = concat_videos(
    input_files=["part1.mp4", "part2.mp4", "part3.mp4"],
    output_path="combined.mp4"
)
```

### 流式处理大型视频

```python
from src.exporters.ffmpeg_zerocopy import create_streaming_ffmpeg_pipeline, VideoCutProcessor

# 创建流式处理管道
pipeline = create_streaming_ffmpeg_pipeline(chunk_size=60)  # 每次处理60秒

# 添加处理器
pipeline.add_stage(VideoCutProcessor(start_time=0, duration=10))  # 将每个分块截取前10秒

# 处理大型视频文件
for segment in pipeline.process_stream(generate_video_segments("large_video.mp4")):
    process_segment(segment)
```

### 自定义设置

```python
from src.exporters.ffmpeg_zerocopy import FFmpegSettings, FFmpegCodec, FFmpegPreset

# 创建自定义设置
settings = FFmpegSettings(
    video_codec=FFmpegCodec.H265,      # 使用H.265编码
    audio_codec=FFmpegCodec.OPUS,      # 使用Opus音频编码
    preset=FFmpegPreset.SLOW,          # 慢速预设，更好的压缩率
    crf=18,                            # 更高的视频质量
    width=1280,                        # 输出宽度
    height=720,                        # 输出高度
    fps=30,                            # 输出帧率
    audio_bitrate="192k",              # 音频比特率
    threads=4,                         # 使用4个线程
    extra_args={                       # 额外参数
        "tune": "film",                # 针对电影内容进行优化
        "movflags": "faststart"        # 优化网络播放
    }
)
```

## 性能优化

FFmpeg零拷贝集成模块设计时考虑了多种性能优化策略：

1. **内存映射**: 使用内存映射技术处理视频文件，减少内存拷贝
2. **管道模式**: 利用FFmpeg的管道模式减少中间文件I/O
3. **并行处理**: 支持多线程处理，充分利用多核CPU
4. **流式处理**: 分块处理大型视频，控制内存使用峰值
5. **临时文件管理**: 自动管理和清理临时文件，避免磁盘空间浪费

## 与现有模块集成

FFmpeg零拷贝集成与现有的流式处理管道和内存映射引擎无缝集成：

```python
from src.exporters.stream_pipe import Processor
from src.exporters.ffmpeg_zerocopy import FFmpegProcessor, FFmpegSettings

# 创建自定义FFmpeg处理器
class CustomFFmpegProcessor(FFmpegProcessor):
    def __init__(self, custom_params):
        super().__init__("CustomProcessor")
        self.custom_params = custom_params
    
    def process(self, data):
        # 实现自定义处理逻辑
        return processed_data

# 添加到现有处理管道
pipeline.add_stage(CustomFFmpegProcessor(custom_params))
```

## 最佳实践

1. **预先验证FFmpeg**: 在使用前验证FFmpeg可执行文件是否存在并可访问
2. **选择合适的编码器**: 根据需求选择合适的视频和音频编码器
3. **设置合理的CRF值**: 对于无损质量使用较低的CRF值（如18），对于节省空间使用较高的值（如28）
4. **使用硬件加速**: 在可能的情况下使用GPU硬件加速（通过`extra_args`设置）
5. **及时清理临时文件**: 始终在处理完成后调用`cleanup()`方法
6. **使用流式处理大文件**: 对于大型视频文件，优先使用`StreamingFFmpegPipeline`

## 示例代码

更多示例请参考 `examples/ffmpeg_zerocopy_demo.py` 