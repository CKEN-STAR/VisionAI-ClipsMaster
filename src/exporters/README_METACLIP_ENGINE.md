# 元数据驱动剪辑引擎 (Metadata-Driven Clip Engine)

元数据驱动剪辑引擎是VisionAI-ClipsMaster项目中的一个核心组件，它通过统一的元数据抽象层来描述和执行视频剪辑操作。该引擎使用声明式元数据结构表示剪辑操作，实现了剪辑逻辑与实际执行的解耦，支持跨平台、跨格式的剪辑项目生成。

## 功能特点

- **声明式剪辑描述**: 使用统一的元数据格式描述剪辑操作，降低复杂性
- **操作抽象**: 将复杂的剪辑操作抽象为简单的元数据结构
- **可扩展性**: 支持自定义处理器扩展不同类型的剪辑操作
- **内存优化**: 与内存映射引擎集成，高效处理大型视频文件
- **嵌套操作**: 支持复杂的嵌套剪辑操作描述
- **JSON序列化**: 支持将剪辑描述保存为JSON格式，便于存储和传输
- **批量处理**: 支持批量处理多个剪辑操作
- **错误处理**: 完善的错误捕获和报告机制

## 使用方法

### 基本用法

```python
from src.exporters.metaclip_engine import generate_metadata_clip, get_metaclip_engine

# 创建元数据剪辑描述
clip = generate_metadata_clip(
    src="video.mp4",
    in_point=10.5,
    out_point=20.5,
    operation="slice",
    codec="copy",
    output="output.mp4"
)

# 创建引擎并处理
engine = get_metaclip_engine()

try:
    # 处理剪辑
    result = engine.process(clip)
    print(f"处理结果: {result}")
    
finally:
    # 清理资源
    engine.cleanup()
```

### 视频连接

```python
from src.exporters.metaclip_engine import generate_metadata_clip, get_metaclip_engine

# 创建连接剪辑描述
concat_clip = generate_metadata_clip(
    src=["clip1.mp4", "clip2.mp4", "clip3.mp4"],
    in_point=None,
    out_point=None,
    operation="concat",
    codec="copy",
    output="combined.mp4"
)

# 创建引擎并处理
engine = get_metaclip_engine()
result = engine.process(concat_clip)
```

### 复杂嵌套操作

```python
from src.exporters.metaclip_engine import MetaClip, get_metaclip_engine

# 创建主操作
parent_clip = MetaClip(
    operation="composite",
    src="background.mp4",
    params={"output": "final.mp4"}
)

# 添加子操作
parent_clip.add_child(MetaClip(
    operation="overlay",
    src="overlay1.mp4",
    params={"position": "top-left"}
))

parent_clip.add_child(MetaClip(
    operation="text",
    src=None,
    params={
        "text": "示例文本",
        "position": "bottom",
        "font_size": 24
    }
))

# 创建引擎并处理
engine = get_metaclip_engine()
result = engine.process(parent_clip)
```

### 批量处理

```python
from src.exporters.metaclip_engine import generate_metadata_clip, get_metaclip_engine

# 创建多个剪辑描述
clips = [
    generate_metadata_clip(
        src="video.mp4",
        in_point=10.0,
        out_point=20.0,
        operation="slice",
        output=f"output1.mp4"
    ),
    generate_metadata_clip(
        src="video.mp4",
        in_point=30.0,
        out_point=40.0,
        operation="slice",
        output=f"output2.mp4"
    )
]

# 批量处理
engine = get_metaclip_engine()
results = engine.batch_process(clips)
```

### 保存和加载元数据剪辑描述

```python
from src.exporters.metaclip_engine import generate_metadata_clip, get_metaclip_engine

# 创建元数据剪辑描述
clips = [
    generate_metadata_clip(
        src="video.mp4",
        in_point=10.0,
        out_point=20.0,
        operation="slice",
        output="output1.mp4"
    ),
    generate_metadata_clip(
        src="video.mp4",
        in_point=30.0,
        out_point=40.0,
        operation="slice",
        output="output2.mp4"
    )
]

# 创建引擎
engine = get_metaclip_engine()

# 保存到JSON文件
engine.save_to_json(clips, "clips.json")

# 从JSON文件加载
loaded_clips = engine.load_from_json("clips.json")
```

## 支持的操作类型

元数据驱动剪辑引擎当前支持以下操作类型：

1. **slice**: 切片操作，从视频中提取特定时间段
2. **trim**: 修剪操作，去除视频开头或结尾部分
3. **concat**: 连接操作，将多个视频片段连接为一个
4. **speed**: 速度调整，改变视频播放速度
5. **filter**: 滤镜效果，应用视频滤镜
6. **transition**: 转场效果，添加视频转场
7. **audio**: 音频操作，处理音频轨道
8. **text**: 文本叠加，添加字幕或文字
9. **overlay**: 视频叠加，添加水印或覆盖内容
10. **transform**: 变换操作，如旋转、缩放等
11. **crop**: 裁剪操作，裁剪视频帧的部分区域
12. **composite**: 合成操作，组合多个视频或效果

## 扩展自定义处理器

可以通过继承`MetaClipProcessor`基类来实现自定义处理器：

```python
from src.exporters.metaclip_engine import MetaClipProcessor, MetaClip, MetaClipError

class CustomEffectProcessor(MetaClipProcessor):
    """自定义效果处理器"""
    
    def __init__(self):
        super().__init__("CustomEffectProcessor")
    
    def process(self, meta_clip: MetaClip) -> Dict[str, Any]:
        """处理自定义效果
        
        Args:
            meta_clip: 元数据剪辑描述
            
        Returns:
            Dict[str, Any]: 处理结果
        """
        # 实现自定义处理逻辑
        try:
            # 处理代码...
            return {
                "status": "success",
                "operation": meta_clip.operation,
                "custom_data": "自定义结果数据"
            }
        except Exception as e:
            raise MetaClipError(f"自定义效果处理失败: {str(e)}")

# 注册自定义处理器
engine = get_metaclip_engine()
engine.processors["custom_effect"] = CustomEffectProcessor()
```

## 与其他模块集成

元数据驱动剪辑引擎与项目中的其他模块无缝集成：

### 与FFmpeg零拷贝集成

```python
from src.exporters.metaclip_engine import generate_metadata_clip, get_metaclip_engine
from src.exporters.ffmpeg_zerocopy import create_ffmpeg_pipeline, FFmpegSettings

# 使用FFmpeg零拷贝管道进行实际处理
class EnhancedSliceProcessor(SliceProcessor):
    def process(self, meta_clip):
        # 验证参数
        super().validate(meta_clip)
        
        # 使用FFmpeg零拷贝管道处理
        pipeline = create_ffmpeg_pipeline()
        result = pipeline.cut_video(
            input_path=meta_clip.src,
            output_path=meta_clip.params.get("output", ""),
            start_time=meta_clip.in_point,
            duration=meta_clip.out_point - meta_clip.in_point
        )
        
        return {"status": "success", "output": result}

# 注册增强版处理器
engine = get_metaclip_engine()
engine.processors["slice"] = EnhancedSliceProcessor()
```

### 与流式处理管道集成

```python
from src.exporters.metaclip_engine import MetaClipProcessor
from src.exporters.stream_pipe import ZeroCopyPipeline, VideoProcessor

class StreamingMetaProcessor(MetaClipProcessor):
    def process(self, meta_clip):
        # 创建处理管道
        pipeline = ZeroCopyPipeline()
        
        # 添加视频处理器
        pipeline.add_stage(MyCustomVideoProcessor())
        
        # 处理视频
        return pipeline.execute(meta_clip.src)
```

## 错误处理

元数据驱动剪辑引擎提供了专门的异常类型`MetaClipError`来处理操作错误：

```python
from src.exporters.metaclip_engine import get_metaclip_engine, MetaClipError

engine = get_metaclip_engine()

try:
    result = engine.process(clip)
except MetaClipError as e:
    print(f"处理错误: {e}")
    print(f"详细信息: {e.details}")
```

## 性能优化

引擎内部使用内存映射技术来优化大型视频文件的处理：

1. **零拷贝处理**: 处理过程中避免不必要的内存拷贝
2. **资源清理**: 自动管理和释放资源，避免内存泄漏
3. **并行处理**: 支持批量操作的并行处理（未来版本）
4. **缓存管理**: 内部使用缓存提高重复操作的性能

## 最佳实践

1. **合理使用操作嵌套**: 避免过深的嵌套层次，以保持清晰的处理逻辑
2. **及时清理资源**: 使用完成后调用`cleanup()`方法释放资源
3. **错误处理**: 使用try-except块捕获和处理异常
4. **批量处理**: 对多个相似操作使用批量处理以提高效率
5. **使用标准操作类型**: 优先使用预定义的操作类型，而不是自定义操作

## 示例应用场景

1. **自动剪辑**: 基于分析结果自动生成剪辑片段
2. **批量处理**: 对大量视频应用相同的处理流程
3. **跨平台项目**: 生成适用于不同编辑软件的项目文件
4. **模板应用**: 将预定义的剪辑模板应用到不同的视频

## 未来扩展

1. **GPU加速**: 集成GPU加速处理特定操作
2. **分布式处理**: 支持跨多台机器的分布式处理
3. **预览生成**: 生成轻量级预览而不需要完整处理
4. **更多操作类型**: 添加更多专业视频编辑操作
5. **实时处理**: 支持实时视频流处理 