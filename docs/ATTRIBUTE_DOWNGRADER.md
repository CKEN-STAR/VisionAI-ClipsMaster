# 属性降级处理器

## 简介

属性降级处理器是VisionAI-ClipsMaster系统的一个重要组件，用于将高版本的项目文件转换为低版本兼容的格式。当用户需要将使用高版本创建的项目分享给使用低版本软件的用户时，这个功能变得尤为重要。

属性降级处理器能够识别XML文件中的高版本特性，并根据目标版本的支持情况进行智能转换，确保项目在低版本软件中仍然可用，同时尽可能保留原始项目的创意意图。

## 主要功能

属性降级处理器提供以下核心功能：

1. **版本检测和比较**：自动识别XML文件的版本，并与目标版本进行比较
2. **分辨率降级**：将高分辨率项目（如4K、8K）转换为低版本支持的分辨率（如1080p、720p）
3. **标签转换**：将高版本特有的标签（如4K标签）转换为低版本兼容的标签（如HD）
4. **HDR转换**：移除不支持的HDR属性，同时添加适当的标记以保持色彩空间信息
5. **嵌套序列转换**：将嵌套序列转换为普通剪辑，以适应不支持嵌套的低版本
6. **效果兼容处理**：移除或转换不支持的效果，保留兼容的效果
7. **关键帧动画转换**：将动画关键帧转换为静态值，以适应不支持关键帧动画的低版本
8. **批量处理**：支持批量处理整个目录中的XML文件

## 技术实现

### 降级规则

属性降级处理器基于版本特征库中定义的功能列表实现智能降级。以下是主要的降级规则：

1. **分辨率规则**：
   - v3.0.0：支持最高8K (7680x4320)
   - v2.5.0-v2.9.5：支持最高1080p (1920x1080)
   - v2.0.0：支持最高720p (1280x720)

2. **效果支持规则**：
   - v3.0.0：支持所有效果类型（blur, color, transform, transition, audio, 3d）
   - v2.9.0-v2.9.5：仅支持transition效果
   - v2.0.0-v2.5.0：不支持效果

3. **嵌套序列规则**：
   - v3.0.0：支持嵌套序列
   - v2.0.0-v2.9.5：不支持嵌套序列，转换为普通剪辑

4. **HDR支持规则**：
   - v3.0.0：支持HDR
   - v2.0.0-v2.9.5：不支持HDR，转换为标准色域

### 代码架构

```
src/
└── exporters/
    └── attribute_downgrader.py  # 属性降级处理器主模块

examples/
└── attribute_downgrader_demo.py # 属性降级处理器演示程序
```

## 使用方法

### 命令行用法

属性降级处理器可以通过命令行直接使用：

```bash
# 单个文件降级
python attribute_downgrader.py input.xml output.xml 2.0.0

# 批量处理目录
python attribute_downgrader.py --batch input_dir/ output_dir/ 2.0.0
```

### 在代码中使用

```python
from src.exporters.attribute_downgrader import process_xml_file

# 将XML文件从高版本降级到2.0.0版本
success = process_xml_file("high_version.xml", "compatible_v2.xml", "2.0.0")

if success:
    print("降级成功!")
else:
    print("降级失败!")
```

### 演示程序

VisionAI-ClipsMaster提供了完整的演示程序，可以快速了解属性降级处理器的功能：

```bash
# 创建示例文件并降级到2.0.0版本
python examples/attribute_downgrader_demo.py demo --target-version 2.0.0

# 创建示例文件
python examples/attribute_downgrader_demo.py create --output sample.xml

# 降级文件并比较差异
python examples/attribute_downgrader_demo.py downgrade sample.xml --target-version 2.0.0 --compare
```

## 降级示例

以下是一些常见的降级场景示例：

### 1. 4K项目降级到720p

**原始项目**：
```xml
<resolution width="3840" height="2160"/>
<4K enabled="true" upscale="false"/>
```

**降级到2.0.0后**：
```xml
<resolution width="1280" height="720" downsampled="true"/>
<HD super_sample="true" enabled="true" upscale="false"/>
```

### 2. HDR项目降级

**原始项目**：
```xml
<color_space hdr="true" type="rec2020"/>
```

**降级到2.5.0后**：
```xml
<color_space colorspace="srgb" converted_from_hdr="true" type="rec2020"/>
```

### 3. 嵌套序列降级

**原始项目**：
```xml
<nested_sequence id="nested_001" name="嵌套场景" duration="00:00:30.000">
    <track id="nested_track_1" type="video">
        <clip id="clip_001" start="00:00:00.000" duration="00:00:05.000"/>
    </track>
</nested_sequence>
```

**降级到2.9.5后**：
```xml
<clip id="nested_001" name="嵌套场景" duration="00:00:30.000" 
      flattened="true" original_type="nested_sequence"/>
```

## 注意事项

1. 降级处理会导致部分高版本特性的丢失或简化，因此建议保留原始项目文件
2. 某些复杂效果可能无法完美降级，会转换为备注或静态值
3. 降级处理不可逆，无法从低版本重新恢复到高版本的全部功能
4. 对于大型项目文件，降级过程可能需要较长时间

## 结论

属性降级处理器是VisionAI-ClipsMaster兼容性策略的重要组成部分，它使用户能够在不同版本的软件之间无缝共享项目，提高了工作流程的灵活性。通过智能降级算法，系统能够在保持项目可用性的同时，尽可能保留原始的创意意图。 