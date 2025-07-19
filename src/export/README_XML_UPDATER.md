# XML更新器模块使用指南

## 功能介绍

XML更新器(`XMLUpdater`)是VisionAI-ClipsMaster中的一个关键组件，提供了对已有工程XML文件进行增量更新的功能。该模块可以帮助用户在不重新生成整个项目的情况下，向现有工程添加新的片段、资源或更改项目设置。

主要功能包括：

1. 向已有工程文件追加单个新片段
2. 批量追加多个新片段
3. 添加新的视频/音频资源
4. 更改项目设置参数

## 兼容格式

XML更新器支持多种常见XML格式：

- 通用XML项目格式 (标准格式)
- Final Cut Pro XML格式 (FCPXML)
- Premiere Pro XML格式
- 剪映XML格式

## 使用方法

### 基本使用

```python
from src.export import XMLUpdater

# 初始化XML更新器
updater = XMLUpdater()

# 向已有工程文件添加新片段
new_clip = {
    'resource_id': 'video_1',      # 资源ID
    'start_time': 10.0,            # 资源开始时间(秒)
    'duration': 5.0,               # 持续时间(秒)
    'name': '新片段',              # 片段名称
    'has_audio': True              # 是否包含音频
}

# 添加片段
result = updater.append_clip('project.xml', new_clip)
if result:
    print("成功添加新片段!")
```

### 批量添加片段

```python
# 定义多个片段
clips = [
    {
        'resource_id': 'video_1',
        'start_time': 15.0,
        'duration': 3.0,
        'name': '片段1',
        'has_audio': True
    },
    {
        'resource_id': 'video_1',
        'start_time': 20.0,
        'duration': 4.0,
        'name': '片段2',
        'has_audio': False
    }
]

# 批量添加片段
updater.append_clips('project.xml', clips)
```

### 添加新资源

```python
# 定义新资源
resource = {
    'id': 'video_2',               # 资源ID
    'type': 'video',               # 资源类型(video/audio)
    'path': '/path/to/video.mp4',  # 文件路径
    'width': '1920',               # 视频宽度
    'height': '1080',              # 视频高度
    'fps': '30'                    # 帧率
}

# 添加资源
updater.add_resource('project.xml', resource)
```

### 更改项目设置

```python
# 定义新设置
settings = {
    'name': '更新后的项目名称',
    'fps': '60',
    'width': '3840',
    'height': '2160'
}

# 更新设置
updater.change_project_settings('project.xml', settings)
```

## 命令行演示

项目中包含了一个演示脚本`demo_xml_updater.py`，可以通过命令行参数来演示XML更新器的功能：

```bash
# 创建示例项目
python src/export/demo_xml_updater.py --create

# 添加单个片段
python src/export/demo_xml_updater.py --add

# 批量添加多个片段
python src/export/demo_xml_updater.py --batch

# 指定工程文件路径
python src/export/demo_xml_updater.py --add --file my_project.xml
```

## 注意事项

1. 添加片段时，如果资源不存在，请先使用`add_resource()`方法添加相应资源
2. XML更新器会自动计算新片段在轨道上的起始位置，确保片段不会重叠
3. 如果启用了音频(has_audio=True)，XML更新器会同时添加视频和音频片段
4. 工程文件格式不同，XML更新器会自动适配对应格式进行更新
5. 更新后的工程文件可能需要在相应的编辑软件中刷新才能看到变化

## 测试

可以通过运行测试脚本来验证XML更新器的功能：

```bash
python src/export/test_xml_updater.py
```

测试包括对以下功能的验证：

- 添加单个片段
- 批量添加片段
- 添加资源
- 更改项目设置
- 计算轨道结束位置 