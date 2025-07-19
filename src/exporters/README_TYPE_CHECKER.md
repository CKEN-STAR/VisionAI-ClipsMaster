# 数据类型校验模块

本模块提供了一组用于验证XML元素和其他数据结构类型的工具，确保它们符合预期的类型和约束条件。这是VisionAI-ClipsMaster导出工作流程的关键组件，用于确保导出前的数据符合格式规范。

## 功能概述

- 基于XSD类型系统的严格数据类型验证
- 支持多种数据类型，包括整数、浮点数、字符串、布尔值、日期时间等
- 提供属性值验证和数值范围检查
- 支持完整的XML元素结构验证
- 提供预定义的常用规则集合

## 主要函数

### 基本类型验证

```python
from src.validation import validate_type

# 基本类型检查
is_valid = validate_type("42", "xs:int")           # True
is_valid = validate_type("3.14", "xs:float")       # True
is_valid = validate_type("true", "xs:boolean")     # True
is_valid = validate_type("2023-01-15", "xs:date")  # True
is_valid = validate_type("PT1H30M", "xs:duration") # True
```

### 元素属性验证

```python
from src.validation import check_data_types

# 为XML元素定义验证规则
type_rules = {
    'width': ('xs:int', lambda x: int(x) > 0),
    'height': ('xs:int', lambda x: int(x) > 0),
    'fps': ('xs:float', lambda x: float(x) > 0)
}

# 验证元素属性
try:
    check_data_types(element, type_rules)
    print("验证通过")
except TypeError as e:
    print(f"验证失败: {str(e)}")
```

### 数值范围验证

```python
from src.validation import validate_numeric_ranges

# 测试数据
video_data = {
    "width": "1920",
    "height": "1080",
    "fps": "29.97"
}

# 验证规则
rules = {
    "width": {
        "type": "xs:int",
        "min": 1,
        "max": 7680  # 8K分辨率的宽度
    },
    "height": {
        "type": "xs:int",
        "min": 1,
        "max": 4320  # 8K分辨率的高度
    },
    "fps": {
        "type": "xs:float",
        "min": 1.0,
        "max": 240.0,
        "allowed": [23.976, 24, 25, 29.97, 30, 50, 59.94, 60]
    }
}

# 验证数值范围
try:
    validate_numeric_ranges(video_data, rules)
    print("范围验证通过")
except ValidationError as e:
    print(f"范围验证失败: {str(e)}")
```

### XML元素结构验证

```python
from src.validation import validate_xml_element_types

# 定义验证规则
project_rules = {
    'attributes': {
        'version': {
            'type': 'xs:string',
            'required': True
        }
    },
    'children': {
        'video_settings': {
            'required': True,
            'min_occurs': 1,
            'max_occurs': 1,
            'child_rules': {
                'attributes': {
                    'width': {
                        'type': 'xs:int',
                        'required': True
                    }
                }
            }
        }
    }
}

# 验证XML元素
errors = validate_xml_element_types(root_element, project_rules)
if errors:
    print("验证失败:", errors)
else:
    print("验证通过")
```

### 常用规则集合

```python
from src.validation import get_common_type_rules

# 获取预定义的通用规则
common_rules = get_common_type_rules()

# 使用针对视频属性的规则
video_rules = common_rules['video']
```

## 支持的数据类型

该模块支持以下XSD标准数据类型：

| 类型标识 | 说明 | 示例 |
|----------|------|------|
| xs:int, xs:integer | 整数 | 42, -10 |
| xs:float, xs:decimal | 浮点数 | 3.14, -2.5 |
| xs:string | 字符串 | "文本" |
| xs:boolean | 布尔值 | true, false, 1, 0 |
| xs:date | 日期 | 2023-01-15 |
| xs:time | 时间 | 14:30:00 |
| xs:dateTime | 日期时间 | 2023-01-15T14:30:00 |
| xs:duration | 时长 | PT1H30M45S |
| xs:anyURI | URI | http://example.com |
| xs:ID, xs:IDREF | ID引用 | element_id_123 |

## 与其他模块集成

类型验证器设计为与其他验证模块协同工作：

- 与XSD模式验证（`src.validation.xsd_schema_loader`）互补，提供更精细的控制
- 可以与结构验证器（`src.export.structure_validator`）结合使用
- 支持导出器（`src.export`）工作流程中的类型验证

## 使用示例

完整的使用示例可以在 `src/examples/type_validator_demo.py` 中找到：

```bash
# 运行演示脚本
python src/examples/type_validator_demo.py
```

## 错误处理

模块定义了两种主要异常类型：

- `TypeError`: 当值与预期类型不匹配时抛出
- `ValidationError`: 当值不满足验证规则（如范围限制）时抛出

应当捕获这些异常并适当处理：

```python
try:
    # 执行验证
    check_data_types(element, rules)
except (TypeError, ValidationError) as e:
    # 处理验证错误
    print(f"验证错误: {str(e)}")
    # 可选的错误修复或记录逻辑
``` 