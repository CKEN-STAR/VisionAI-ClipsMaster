# 动态模板引擎

## 简介

动态模板引擎是VisionAI-ClipsMaster系统的核心组件之一，可以根据不同的版本规格动态生成适配的XML、JSON或文本模板。该引擎基于版本特征库，能够自动识别不同版本支持的特性，并根据这些特性生成相应的模板结构。

主要功能包括：

1. **根据版本自动选择** 适当的模板结构
2. **特性感知** 根据版本支持的特性动态调整模板内容
3. **多格式输出** 支持XML、JSON和文本等多种格式
4. **分辨率限制** 自动应用版本的分辨率限制
5. **效果支持检查** 根据版本支持的效果生成对应的结构

## 基本架构

```
src/
└── exporters/
    └── dynamic_template.py  # 动态模板引擎主模块

examples/
└── dynamic_template_demo.py # 动态模板引擎演示程序
```

## 使用方法

### 基础用法

```python
from src.exporters.dynamic_template import create_template_engine

# 创建模板引擎，指定目标版本
engine = create_template_engine("3.0.0")

# 定义模板参数
params = {
    "title": "我的项目",
    "width": 3840,
    "height": 2160,
    "fps": 29.97,
    "video_tracks": 3,
    "audio_tracks": 2,
    "use_nested": True,
    "nested_name": "场景1"
}

# 生成XML模板
xml_template = engine.generate_template('xml', params)

# 生成JSON模板
json_template = engine.generate_template('json', params)

# 生成文本描述
text_template = engine.generate_template('text', params)
```

### 特性检查

```python
from src.exporters.dynamic_template import create_template_engine

engine = create_template_engine("3.0.0")

# 检查版本是否支持某个特性
if engine.is_feature_supported("nested_sequences"):
    print("此版本支持嵌套序列")
    
# 检查版本是否支持某个效果
if engine.is_effect_supported("blur"):
    print("此版本支持模糊效果")
    
# 获取版本支持的最大分辨率
max_width, max_height = engine.get_max_resolution()
print(f"最大分辨率: {max_width}x{max_height}")
```

### 获取预设模板路径

```python
from src.exporters.dynamic_template import create_template_engine

engine = create_template_engine("3.0.0")

# 获取XML模板文件路径
xml_template_path = engine.get_template_path('xml')

# 获取JSON模板文件路径
json_template_path = engine.get_template_path('json')
```

## 命令行工具

动态模板引擎提供了一个命令行演示工具，可以用于测试和展示引擎功能。

### 生成模板

```bash
python examples/dynamic_template_demo.py generate 3.0.0 --format xml --output template.xml
```

参数说明：
- `version`: 目标版本号
- `--format, -f`: 输出格式（xml, json, text）
- `--output, -o`: 输出文件路径
- `--title`: 项目标题
- `--width`: 视频宽度
- `--height`: 视频高度
- `--fps`: 帧率
- `--video-tracks`: 视频轨道数
- `--audio-tracks`: 音频轨道数
- `--no-nested`: 禁用嵌套序列

### 列出版本支持的特性

```bash
python examples/dynamic_template_demo.py features 3.0.0
```

输出包括：
- 支持的功能列表
- 最大分辨率
- 支持的效果

### 比较多个版本

```bash
python examples/dynamic_template_demo.py compare 2.0.0 2.5.0 2.9.5 3.0.0
```

以表格形式展示多个版本的特性支持情况，方便对比。

### 批量生成模板

```bash
python examples/dynamic_template_demo.py batch 3.0.0 --output-dir templates --formats xml json text
```

将指定版本的多种格式模板一次性生成到指定目录。

## 模板参数

动态模板引擎支持的参数包括：

| 参数 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| title | 字符串 | 项目标题 | "新项目" |
| width | 整数 | 视频宽度 | 1920 |
| height | 整数 | 视频高度 | 1080 |
| fps | 浮点数 | 帧率 | 30.0 |
| video_tracks | 整数 | 视频轨道数 | 1 |
| audio_tracks | 整数 | 音频轨道数 | 1 |
| use_nested | 布尔值 | 是否使用嵌套序列 | False |
| nested_name | 字符串 | 嵌套序列名称 | "嵌套序列" |
| id | 字符串 | 项目ID | "project_001" |
| type | 字符串 | 项目类型 | "project" |
| timeline_id | 字符串 | 时间线ID | "timeline_001" |
| duration | 字符串 | 项目时长 | "00:01:00.000" |
| language | 字符串 | 字幕语言 | "zh-CN" |

## 扩展新版本支持

要添加对新版本的支持，需要在`configs/jianying_versions.yaml`文件中添加相应的版本规格定义。动态模板引擎会自动读取这些定义并应用到模板生成过程中。

## 模板格式

### XML 模板

XML模板遵循Jianying项目格式，根节点为`jianying_project`，包含版本属性和以下主要子节点：
- `info`: 包含项目元数据和设置
- `resources`: 包含项目资源
- `timeline`: 包含时间线和轨道信息

### JSON 模板

JSON模板是XML格式的JSON等价表示，使用嵌套对象表示项目结构。

### 文本模板

文本模板是一种人类可读的描述性格式，主要用于调试和查看项目信息。

## 错误处理

动态模板引擎在遇到错误时会记录日志并返回适当的错误信息。常见错误包括：

1. 找不到版本特征库配置文件
2. 无法解析版本号
3. 模板生成过程中的错误

## 性能考虑

- 版本特征和效果支持状态会被缓存，以提高重复查询的性能
- 对于未找到的精确版本，引擎会尝试查找最接近的版本
- 大型项目生成可能需要更多资源，建议使用异步或批处理模式 