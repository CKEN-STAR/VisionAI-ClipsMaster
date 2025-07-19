# 时间轴连续性验证模块

本模块提供了一组用于验证视频编辑时间轴连续性的工具，确保视频片段在轨道上排列合理，没有意外的重叠或时间跳跃，从而保证最终输出视频的流畅性。这是VisionAI-ClipsMaster项目中确保视频质量的关键组件。

## 功能概述

- 验证时间轴上片段的排序和连续性
- 检测片段之间的重叠问题
- 检测时间轴上的间隙
- 验证多轨道时间轴的对齐关系
- 检查场景转场的合理性
- 验证片段持续时间是否合适

## 主要函数

### 基本时间轴连续性验证

```python
from src.exporters.timeline_validator import validate_timeline_continuity

# 验证轨道连续性
tracks = [
    {
        "name": "视频轨道1",
        "type": "video",
        "clips": [
            {"id": "clip1", "start": 0, "end": 100},
            {"id": "clip2", "start": 100, "end": 200}
        ]
    }
]

errors = validate_timeline_continuity(tracks)
if not errors:
    print("时间轴连续性验证通过")
else:
    for error in errors:
        print(f"错误: {error['description']}")
```

### 简化版连续性验证

```python
from src.exporters.timeline_validator import validate_timeline_continuity_simple

# 检测轨道重叠
clips = [
    {"id": "clip1", "start": 0, "end": 100},
    {"id": "clip2", "start": 100, "end": 200}
]

try:
    validate_timeline_continuity_simple(clips)
    print("时间轴连续性验证通过")
except TimelineConsistencyError as e:
    print(f"时间轴错误: {str(e)}")
```

### 时间轴间隙检测

```python
from src.exporters.timeline_validator import check_timeline_gaps

# 检测轨道间隙
tracks = [
    {
        "name": "视频轨道1",
        "type": "video",
        "clips": [
            {"id": "clip1", "start": 0, "end": 100},
            {"id": "clip2", "start": 120, "end": 200}  # 间隙: 100-120
        ]
    }
]

gaps = check_timeline_gaps(tracks)
if gaps:
    print("检测到时间轴间隙:")
    for gap in gaps:
        print(f"  {gap['description']}")
```

### 多轨道验证

```python
from src.exporters.timeline_validator import validate_multi_track_timeline

# 验证多轨道关系
timeline_data = {
    "tracks": [
        {
            "name": "视频轨道",
            "type": "video",
            "clips": [
                {"id": "v1", "start": 0, "end": 200}
            ]
        },
        {
            "name": "字幕轨道",
            "type": "subtitle",
            "clips": [
                {"id": "s1", "start": 0, "end": 50},
                {"id": "s2", "start": 60, "end": 120}
            ]
        }
    ]
}

errors = validate_multi_track_timeline(timeline_data)
if not errors:
    print("多轨道时间轴验证通过")
else:
    for error in errors:
        print(f"错误: {error['description']}")
```

### 场景转场验证

```python
from src.exporters.timeline_validator import check_scene_transition_consistency

# 检查场景转场
timeline_data = {
    "tracks": [
        {
            "name": "视频轨道",
            "type": "video",
            "clips": [
                {"id": "clip1", "start": 0, "end": 100, "scene": "客厅"},
                {"id": "clip2", "start": 100, "end": 200, "scene": "卧室"}
            ]
        }
    ],
    "transitions": [
        {"start": 90, "end": 110, "type": "fade"}
    ]
}

issues = check_scene_transition_consistency(timeline_data)
if not issues:
    print("场景转场验证通过")
else:
    for issue in issues:
        print(f"警告: {issue['description']}")
```

### 完整时间轴文件验证

```python
from src.exporters.timeline_validator import validate_timeline_from_file

# 从文件验证时间轴
result = validate_timeline_from_file("path/to/timeline.json")

if result["valid"]:
    print("时间轴文件验证通过")
else:
    print("时间轴文件验证失败:")
    for error in result["errors"]:
        print(f"  - {error}")
        
    if result["warnings"]:
        print("\n警告:")
        for warning in result["warnings"]:
            print(f"  - {warning}")
```

## 命令行使用

该模块可以作为独立脚本运行，用于验证时间轴文件:

```bash
python -m src.exporters.timeline_validator path/to/timeline.json
```

## 错误类型

模块定义了几种错误类型:

1. **TimelineError** - 基本时间轴错误类
2. **TimelineConsistencyError** - 时间轴连续性错误
3. **TimelineOverlapError** - 片段重叠错误

## 集成到视频导出流程

时间轴验证可以集成到导出前的验证流程中:

```python
from src.exporters.timeline_validator import validate_timeline_from_file

def validate_before_export(timeline_path):
    # 验证时间轴
    result = validate_timeline_from_file(timeline_path)
    
    if not result["valid"]:
        raise Exception("时间轴验证失败，不能导出")
        
    # 继续其他验证...
    
    return True
```

## 返回格式

验证函数通常返回包含详细信息的字典:

```python
{
    "valid": True/False,        # 验证是否通过
    "errors": [],               # 错误列表
    "warnings": [],             # 警告列表
    "gaps": [],                 # 检测到的间隙
    "file": "timeline.json"     # 验证的文件
}
``` 