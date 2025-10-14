# 剪映新导出器使用文档

## 概述

基于 [pyCapCut](https://github.com/GuanYixuan/pyCapCut) 项目的实现，完全重写了剪映导出器，生成标准的 `draft_content.json` 格式，确保与剪映专业版完全兼容。

## 核心模块

### 1. 时间转换器 (`jianying_time_converter.py`)

统一处理时间单位转换，所有时间使用微秒作为标准单位。

```python
from src.exporters.jianying_time_converter import TimeConverter, Timerange

# 秒转微秒
us = TimeConverter.seconds_to_microseconds(1.5)  # 1,500,000

# 毫秒转微秒
us = TimeConverter.milliseconds_to_microseconds(1500)  # 1,500,000

# SRT时间戳解析
us = TimeConverter.parse_srt_timestamp("00:01:23,456")  # 83,456,000

# 智能时间解析
us = TimeConverter.tim("1.5s")  # 1,500,000
us = TimeConverter.tim("1500ms")  # 1,500,000
us = TimeConverter.tim("00:01:23,456")  # 83,456,000

# 创建时间范围
timerange = TimeConverter.create_timerange(start=0, duration=5.0)
# 或
timerange = TimeConverter.create_timerange(start=0, end=5.0)
```

### 2. 素材管理器 (`jianying_material_manager.py`)

管理所有素材（视频、音频），确保ID一致性。

```python
from src.exporters.jianying_material_manager import MaterialManager, VideoMaterial

# 创建管理器
manager = MaterialManager()

# 添加视频素材
video = manager.add_video_material("path/to/video.mp4")

# 添加音频素材
audio = manager.add_audio_material("path/to/audio.mp3")

# 导出所有素材
materials_json = manager.export_all_materials()
```

**特性：**
- 自动提取视频元数据（如果安装了 pymediainfo）
- 自动路径标准化（转换为绝对路径）
- 自动去重（相同路径的素材只添加一次）
- 自动文件验证

### 3. 轨道管理器 (`jianying_track_manager.py`)

管理视频、音频、文本轨道和片段。

```python
from src.exporters.jianying_track_manager import TrackManager, TrackType, VideoSegment

# 创建管理器
track_manager = TrackManager()

# 创建视频轨道
video_track = track_manager.create_track(TrackType.VIDEO)

# 创建视频片段
segment = VideoSegment(
    material_id="素材ID",
    source_timerange=Timerange(start=0, duration=5000000),  # 源视频0-5秒
    target_timerange=Timerange(start=0, duration=5000000),  # 时间轴0-5秒
    speed=1.0,
    volume=1.0
)

# 添加片段到轨道
video_track.add_segment(segment)

# 导出所有轨道
tracks_json = track_manager.export_all_tracks()
```

**特性：**
- 自动片段重叠检测
- 自动片段排序（按开始时间）
- 支持多种轨道类型（video, audio, text, effect, filter, sticker）

### 4. 草稿生成器 (`jianying_draft_generator.py`)

主生成器，生成完整的 `draft_content.json` 文件。

```python
from src.exporters.jianying_draft_generator import JianyingDraftGenerator

# 创建生成器
generator = JianyingDraftGenerator(width=1920, height=1080, fps=30)

# 添加视频片段
generator.add_video_segment(
    video_path="path/to/video.mp4",
    start_time=0.0,      # 源视频开始时间（秒）
    end_time=5.0,        # 源视频结束时间（秒）
    target_start=0.0,    # 时间轴开始时间（秒）
    speed=1.0,
    volume=1.0
)

# 添加更多片段
generator.add_video_segment(
    video_path="path/to/video.mp4",
    start_time=10.0,
    end_time=15.0,
    target_start=5.0,
    speed=1.0,
    volume=1.0
)

# 导出为JSON字符串
json_str = generator.dumps()

# 保存为文件
generator.save("output/draft_content.json")

# 创建完整的草稿文件夹
draft_folder = generator.create_draft_folder("output", "MyProject")
```

### 5. 导出器适配器 (`jianying_exporter_adapter.py`)

提供兼容层，将新导出器集成到现有系统。

```python
from src.exporters.jianying_exporter_adapter import JianyingExporterAdapter

# 创建适配器
adapter = JianyingExporterAdapter(width=1920, height=1080, fps=30)

# 方式1：从项目数据导出
project_data = {
    "project_name": "测试项目",
    "segments": [
        {
            "source_file": "path/to/video.mp4",
            "start_time": 0.0,
            "end_time": 5.0,
            "duration": 5.0,
            "speed": 1.0,
            "volume": 1.0
        }
    ]
}
adapter.export_project(project_data, "output/project.json")

# 方式2：从字幕列表导出
subtitles = [
    {"start_time": 0.0, "end_time": 5.0, "text": "字幕1"},
    {"start_time": 5.0, "end_time": 10.0, "text": "字幕2"}
]
adapter.export_from_subtitles("path/to/video.mp4", subtitles, "output/project.json")
```

## 集成到现有系统

新导出器已自动集成到现有的导出器中，无需修改现有代码：

### 1. 使用 `JianyingProExporter`

```python
from src.exporters.jianying_pro_exporter import JianyingProExporter

exporter = JianyingProExporter()

# 现有代码无需修改，会自动使用新导出器
project_data = {"segments": [...]}
exporter.export_project(project_data, "output/project.json")
```

### 2. 使用 `JianyingExporter`

```python
from src.export.jianying_exporter import JianyingExporter

exporter = JianyingExporter()

# 现有代码无需修改，会自动使用新导出器
version_data = {"scenes": [...]}
exporter.export(version_data, "output/project.json")
```

## 技术特点

### 1. 完全兼容剪映格式

- 基于 pyCapCut 的成熟实现
- 生成标准的 `draft_content.json` 格式
- 所有字段完整，符合剪映专业版要求

### 2. 时间精度

- 统一使用微秒作为时间单位
- 支持多种时间格式输入（秒、毫秒、SRT格式）
- 自动时间转换和验证

### 3. 素材管理

- 自动元数据提取（需要 pymediainfo）
- 自动路径标准化
- 自动去重和验证

### 4. 向后兼容

- 保持所有现有接口不变
- 优先使用新导出器，失败时自动回退到旧导出器
- 支持多种输入数据格式

### 5. 错误处理

- 完善的异常处理
- 详细的日志记录
- 自动验证和修复

## 依赖项

### 必需依赖

- Python 3.7+
- 无其他必需依赖

### 可选依赖

- `pymediainfo`: 用于自动提取视频元数据
  ```bash
  pip install pymediainfo
  ```

## 测试

### 运行测试

```bash
# 简单格式测试
python test_jianying_simple.py
```

### 在剪映中测试

1. 运行测试脚本生成测试文件
2. 打开剪映专业版
3. 导入生成的 `draft_content.json` 文件
4. 验证以下功能：
   - 文件能否正常打开
   - 时间轴显示是否正确
   - 片段是否可以拖拽调整
   - 所有编辑功能是否正常

## 故障排除

### 问题1：文件无法在剪映中打开

**可能原因：**
- 素材路径不存在
- 时间单位不正确
- 缺少必需字段

**解决方案：**
- 确保所有素材文件存在
- 检查时间单位是否为微秒
- 使用验证器检查文件格式

### 问题2：时间轴显示不正确

**可能原因：**
- 时间单位混用
- source_timerange 和 target_timerange 不匹配

**解决方案：**
- 统一使用 TimeConverter 进行时间转换
- 检查片段的时间范围设置

### 问题3：素材无法预览

**可能原因：**
- 素材路径不是绝对路径
- 素材文件格式不支持

**解决方案：**
- 使用绝对路径
- 确保素材格式为剪映支持的格式（MP4, AVI, MOV等）

## 更新日志

### v1.0.0 (2025-10-05)

- ✅ 完全重写剪映导出器
- ✅ 基于 pyCapCut 实现
- ✅ 生成标准 draft_content.json 格式
- ✅ 统一时间单位（微秒）
- ✅ 完善的素材管理
- ✅ 完善的轨道管理
- ✅ 向后兼容现有系统
- ✅ 详细的文档和测试

## 参考资料

- [pyCapCut GitHub](https://github.com/GuanYixuan/pyCapCut)
- [剪映专业版官网](https://www.capcut.cn/)

## 许可证

本项目遵循 MIT 许可证。

