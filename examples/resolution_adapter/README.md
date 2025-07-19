# 动态分辨率适配器 (Dynamic Resolution Adapter)

动态分辨率适配器用于确保导出的XML项目设置与原始视频分辨率匹配，提高编辑软件的兼容性和用户体验。

## 主要功能

1. **视频分辨率获取**  
   自动检测视频文件的实际分辨率，支持多种方法获取（FFprobe和OpenCV）。

2. **XML分辨率适配**  
   将导出的XML文件中的分辨率设置自动调整为视频的实际分辨率。

3. **分辨率元数据添加**  
   在XML文件中添加分辨率信息节点，方便后续处理。

4. **装饰器模式集成**  
   提供装饰器函数，可以轻松将分辨率适配功能集成到现有导出器中。

## 使用示例

### 获取视频分辨率

```python
from src.export.resolution_handler import get_video_dimensions

# 获取视频分辨率
video_path = "path/to/your/video.mp4"
width, height = get_video_dimensions(video_path)
print(f"视频分辨率: {width}x{height}")
```

### 添加分辨率元数据

```python
from src.export.resolution_handler import add_resolution_meta

# 向XML内容添加分辨率节点
xml_content = "<project>...</project>"
modified_xml = add_resolution_meta(xml_content, video_path)
```

### 适配XML分辨率

```python
from src.export.resolution_handler import adapt_xml_resolution

# 调整XML中的分辨率设置
modified_xml = adapt_xml_resolution(xml_content, video_path)
```

### 在导出器中使用装饰器

```python
from src.export.resolution_handler import auto_adapt_export_resolution

class MyExporter:
    @auto_adapt_export_resolution
    def export(self, version, output_path):
        # 正常的导出逻辑
        # ...
        return output_path
```

## 演示程序

演示程序`resolution_adapter_demo.py`展示了分辨率适配器的完整功能：

1. 获取视频分辨率
2. 添加分辨率元数据节点
3. 适配XML分辨率设置
4. 使用各种导出器进行分辨率适配

### 运行方法

```bash
python examples/resolution_adapter/resolution_adapter_demo.py --video path/to/your/video.mp4 --output ./output
```

## 注意事项

- 分辨率适配器优先使用FFprobe获取视频分辨率，如果失败会回退到使用OpenCV
- 如果无法获取视频分辨率，将使用默认的1920x1080分辨率
- 确保导出的XML符合视频编辑软件的格式要求
- 不同的视频编辑软件可能对分辨率设置有不同的要求和格式 