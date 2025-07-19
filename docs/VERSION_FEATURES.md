# VisionAI-ClipsMaster 版本特征库

## 简介

版本特征库是VisionAI-ClipsMaster系统的核心组件之一，负责管理和存储不同版本的剪映项目格式特性，支持版本检测、格式验证和版本兼容性转换。通过版本特征库，系统能够：

1. **自动识别** 项目文件的版本信息
2. **验证合规性** 确认项目文件是否符合特定版本的要求
3. **特性查询** 获取各版本支持的功能和效果
4. **兼容性检查** 判断不同版本之间的兼容性
5. **转换路径提供** 在版本转换时提供操作指南

本文档详细介绍了版本特征库的结构、使用方式和扩展方法。

## 目录结构

```
VisionAI-ClipsMaster/
├── configs/
│   ├── jianying_versions.yaml   # 版本特征定义文件
│   ├── jianying_v1.xsd          # 版本1模式文件
│   ├── jianying_v2.xsd          # 版本2模式文件
│   └── jianying_v3.xsd          # 版本3模式文件
├── src/
│   └── versioning/              # 版本管理模块
│       ├── __init__.py          # 模块初始化文件
│       ├── version_features.py  # 版本特征库管理
│       ├── version_detector.py  # 版本检测器
│       └── schema_validator.py  # 模式验证器
└── examples/
    └── version_features_demo.py # 版本特征库演示程序
```

## 版本特征库配置

版本特征库通过YAML格式的配置文件定义，存储在`configs/jianying_versions.yaml`中。该文件包含以下主要部分：

### 1. 版本规格 (version_specs)

定义了各个版本的详细信息，包括：

- **version**: 版本号
- **schema**: 对应的XSD模式文件
- **max_resolution**: 支持的最大分辨率
- **required_nodes**: 版本所需的节点
- **deprecated_nodes**: 版本废弃的节点
- **supported_features**: 支持的功能列表
- **supported_effects**: 支持的效果列表
- **compatibility**: 兼容的版本列表
- **display_name**: 显示名称
- **validation_level**: 验证严格程度

示例：

```yaml
version_specs:
  - version: "3.0.0"
    schema: "jianying_v3.xsd"
    max_resolution: 7680x4320  # 8K支持
    required_nodes:
      - "4K"     # 4K分辨率支持
      - "HDR"    # HDR色彩支持
    supported_features:
      - name: "multi_track"
        description: "多轨道支持"
        required: true
    supported_effects:
      - "blur"         # 模糊效果
      - "color"        # 颜色调整
    compatibility:
      - "2.9.5"
      - "2.5.0"
    display_name: "专业版"
    validation_level: "strict"
```

### 2. 版本转换 (version_conversions)

定义了不同版本之间的转换操作，分为升级和降级两种类型：

- **upgrade**: 从低版本升级到高版本的操作
- **downgrade**: 从高版本降级到低版本的操作

示例：

```yaml
version_conversions:
  downgrade:
    "3.0.0-to-2.9.5":
      operations:
        - type: "remove_feature"
          target: "nested_sequences"
          description: "移除嵌套序列"
        - type: "filter_effects"
          keep: ["transition"]
          description: "仅保留转场效果"
```

## 核心组件

### 1. 版本特征库管理器 (VersionFeatures)

位于`src/versioning/version_features.py`，负责加载和管理版本特征库，提供以下主要功能：

- 获取所有版本信息
- 查询特定版本的功能和效果
- 检查版本兼容性
- 获取版本转换操作

主要API：

```python
# 获取版本特征库实例
features = get_version_features()

# 获取特定版本信息
version_info = features.get_version_info("3.0.0")

# 获取版本支持的特性
supported_features = features.get_supported_features("3.0.0")

# 检查特性是否支持
is_supported = features.is_feature_supported("3.0.0", "multi_track")

# 获取版本转换操作
operations = features.get_conversion_operations("3.0.0", "2.9.5")
```

### 2. 版本检测器 (VersionDetector)

位于`src/versioning/version_detector.py`，用于从文件中检测版本信息，支持以下功能：

- 从XML文件中检测版本
- 从JSON文件中检测版本
- 从文本内容中提取版本信息
- 添加版本特性支持信息

主要API：

```python
# 检测文件版本
version_info = detect_version("path/to/project.xml")

# 检查版本兼容性
compatible = is_compatible("3.0.0", "2.9.5")

# 获取版本转换路径
path = get_conversion_path("3.0.0", "2.5.0")
```

### 3. 模式验证器 (SchemaValidator)

位于`src/versioning/schema_validator.py`，负责根据XSD模式验证XML文件，支持以下功能：

- 验证XML文件是否符合特定版本的模式
- 自动检测适用的模式文件
- 获取模式文件的描述信息
- 列出所有可用的模式文件

主要API：

```python
# 验证XML文件
result = validate_xml_file("path/to/project.xml")

# 获取模式信息
schema_info = get_schema_info("jianying_v3.xsd")

# 列出所有模式文件
schemas = list_schemas()
```

## 使用示例

### 1. 基本用法

```python
from src.versioning import detect_version

# 检测文件版本
version_info = detect_version("path/to/project.xml")
print(f"文件格式: {version_info['format_type']}")
print(f"版本: {version_info['version']}")
print(f"显示名称: {version_info['display_name']}")
```

### 2. 特性查询

```python
from src.versioning import get_version_features

# 获取版本特征库
features = get_version_features()

# 检查版本是否支持特定功能
if features.is_feature_supported("3.0.0", "nested_sequences"):
    print("版本3.0.0支持嵌套序列")
else:
    print("版本3.0.0不支持嵌套序列")

# 获取支持的效果列表
effects = features.get_supported_effects("3.0.0")
print(f"支持的效果: {', '.join(effects)}")
```

### 3. 版本兼容性检查

```python
from src.versioning import is_compatible, get_conversion_path

# 检查版本兼容性
if is_compatible("3.0.0", "2.9.5"):
    print("版本3.0.0兼容2.9.5")
else:
    print("版本3.0.0不兼容2.9.5")

# 获取转换路径
path = get_conversion_path("3.0.0", "2.0.0")
print(f"转换路径: {' -> '.join(path)}")
```

### 4. XML验证

```python
from src.versioning import validate_xml_file

# 验证XML文件
result = validate_xml_file("path/to/project.xml")

if result["valid"]:
    print("验证通过")
else:
    print("验证失败")
    for error in result.get("errors", []):
        print(f"行 {error['line']}, 列 {error['column']}: {error['message']}")
```

## 扩展版本特征库

要添加新的版本支持，需要进行以下步骤：

1. **更新版本特征配置文件**：在`configs/jianying_versions.yaml`中添加新版本的规格

```yaml
version_specs:
  - version: "4.0.0"
    schema: "jianying_v4.xsd"
    max_resolution: 15360x8640  # 16K支持
    required_nodes:
      - "8K"
      - "HDR+"
    supported_features:
      - name: "ai_enhancement"
        description: "AI增强"
        required: true
    # ... 其他配置
```

2. **创建新版本的XSD模式文件**：在`configs/`目录下创建对应的XSD模式文件

3. **添加版本转换规则**：在`version_conversions`部分添加新版本的转换规则

```yaml
version_conversions:
  upgrade:
    "3.0.0-to-4.0.0":
      operations:
        - type: "add_feature"
          target: "ai_enhancement"
          description: "添加AI增强功能"
  downgrade:
    "4.0.0-to-3.0.0":
      operations:
        - type: "remove_feature"
          target: "ai_enhancement"
          description: "移除AI增强功能"
```

## 故障排除

### 常见问题

#### 1. 无法检测到版本信息

可能原因：
- 文件格式不支持
- 文件损坏
- 版本信息格式不规范

解决方法：
- 确认文件来源和格式
- 使用正确的版本标记
- 尝试手动指定版本

#### 2. 验证失败

可能原因：
- XML格式不符合XSD规范
- 使用了不支持的特性
- 缺少必需的节点

解决方法：
- 检查错误详情
- 根据错误信息修正文件
- 使用兼容的版本特性

## 参考

- [XML Schema (XSD) 官方文档](https://www.w3.org/XML/Schema)
- [YAML 规范](https://yaml.org/spec/1.2/spec.html)
- [剪映官方文档](https://api.larkoffice.com/wiki/JkL3wkM8airppdkdDFhcMD1Unfg) 