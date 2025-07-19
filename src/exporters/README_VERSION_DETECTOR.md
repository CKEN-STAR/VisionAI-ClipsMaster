# 版本元数据提取模块

本模块提供了从各种项目文件中提取版本信息的功能，包括不同的视频编辑软件格式，特别是剪映(Jianying)格式。

## 主要功能

- 自动检测项目文件格式
- 从剪映项目文件中提取版本信息
- 从XML格式文件中提取版本信息
- 从JSON格式文件中提取版本信息
- 从文本内容中提取版本信息

## API 参考

### `detect_version(file_path)`

检测文件的格式和版本，返回包含详细信息的字典。

**参数**:
- `file_path`: 文件路径

**返回值**:
```python
{
    "format_type": "jianying",  # 文件格式类型
    "version": "2.5",           # 版本号
    "display_name": "剪映",      # 显示名称
    "file_path": "/path/to/file.xml",  # 文件路径
    "file_size": 12345,         # 文件大小（字节）
    "last_modified": 1629456789 # 最后修改时间戳
}
```

### `detect_jianying_version(output_path)`

从剪映工程文件中提取版本信息。

**参数**:
- `output_path`: 剪映工程文件路径

**返回值**:
- 字符串版本号，如 "2.5"，如果无法提取则返回 "unknown"

### `extract_version_from_xml(xml_path)`

从XML文件中提取版本和格式信息。

**参数**:
- `xml_path`: XML文件路径

**返回值**:
```python
{
    "format_type": "jianying",  # 文件格式类型
    "version": "2.5"            # 版本号
}
```

### `extract_version_from_json(json_path)`

从JSON文件中提取版本信息。

**参数**:
- `json_path`: JSON文件路径

**返回值**:
```python
{
    "format_type": "jianying",  # 文件格式类型
    "version": "1.8.0"          # 版本号
}
```

### `detect_jianying_version_from_string(content)`

从字符串内容中提取剪映版本信息。

**参数**:
- `content`: 文件内容字符串

**返回值**:
- 字符串版本号，如 "2.5"，如果无法提取则返回 "unknown"

### `get_format_display_name(format_type)`

获取格式类型的显示名称。

**参数**:
- `format_type`: 格式类型代码

**返回值**:
- 显示名称字符串，如 "剪映"

## 使用示例

### 基本使用

```python
from src.exporters.version_detector import detect_version

# 检测文件版本
file_path = "project_file.xml"
info = detect_version(file_path)

print(f"文件格式: {info['display_name']} ({info['format_type']})")
print(f"版本号: {info['version']}")
```

### 处理多个文件

```python
import os
from pathlib import Path
from src.exporters.version_detector import detect_version

# 处理目录中的所有XML文件
directory = "projects/"
for file_path in Path(directory).glob("**/*.xml"):
    print(f"处理文件: {file_path}")
    info = detect_version(str(file_path))
    if info["version"] != "unknown":
        print(f"  格式: {info['display_name']}")
        print(f"  版本: {info['version']}")
```

### 从字符串提取版本

```python
from src.exporters.version_detector import detect_jianying_version_from_string

# 直接从内容中提取版本
content = """
<jianying_project version="2.5">
  <info>
    <metadata>
      <jy_type>standard</jy_type>
    </metadata>
  </info>
</jianying_project>
"""

version = detect_jianying_version_from_string(content)
print(f"版本: {version}")
```

## 命令行使用

本模块也提供了命令行使用方式，通过 `version_detector_example.py`:

```bash
# 分析单个文件
python src/exporters/version_detector_example.py --file project.xml

# 扫描整个目录
python src/exporters/version_detector_example.py --dir projects/

# 从内容字符串提取版本
python src/exporters/version_detector_example.py --content "<jianying_project version=\"2.5\"></jianying_project>"
```

## 支持的格式

- 剪映 (Jianying)
- Premiere Pro
- Final Cut Pro (FCPXML)
- DaVinci Resolve
- 其他XML和JSON格式

## 注意事项

1. 对于非标准格式或特殊文件，可能无法提取版本信息，此时会返回 "unknown"
2. 检测功能会优先根据文件扩展名进行尝试，但也会尝试其他格式解析方法
3. 如果处理大型文件，请注意性能和内存使用情况 