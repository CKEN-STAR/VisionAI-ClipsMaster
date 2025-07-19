# VisionAI-ClipsMaster 本地化格式化器使用指南

## 概述

本地化格式化器是VisionAI-ClipsMaster中用于处理不同语言环境下格式化显示的核心组件。它提供了对日期、时间、数字、货币等数据的本地化格式化功能，确保在不同语言和地区的用户界面中，这些信息都能以符合当地习惯的方式显示。

## 主要功能

本地化格式化器提供以下主要功能：

1. **日期格式化**：根据不同语言环境格式化日期，例如：
   - 中文：2023年01月01日
   - 美式英语：01/01/2023
   - 英式英语：01/01/2023
   - 德语：01.01.2023

2. **时间格式化**：根据不同语言环境格式化时间，支持12小时制和24小时制：
   - 中文：13:45:30
   - 美式英语：1:45:30 PM
   - 英式英语：13:45:30

3. **数字格式化**：根据不同语言环境格式化数字，处理千位分隔符和小数点：
   - 中文：1,234.56
   - 英语：1,234.56
   - 德语：1.234,56

4. **货币格式化**：根据不同语言环境和货币代码格式化货币：
   - 中文人民币：¥1,234.56
   - 美元：$1,234.56
   - 欧元（德语）：1.234,56 €

5. **百分比格式化**：根据不同语言环境格式化百分比：
   - 23.45%

6. **文件大小格式化**：将字节数转换为易读的文件大小格式：
   - 中文：15.36 兆字节
   - 英语：15.36 MB

## 支持的语言

当前版本支持以下语言的本地化格式：

- 简体中文 (zh_CN)
- 繁体中文 (zh_TW)
- 美式英语 (en_US)
- 英式英语 (en_GB)
- 法语 (fr)
- 德语 (de)
- 西班牙语 (es)
- 日语 (ja)
- 韩语 (ko)
- 俄语 (ru)
- 阿拉伯语 (ar) - 支持从右到左(RTL)文本方向
- 希伯来语 (he) - 支持从右到左(RTL)文本方向
- 波斯语 (fa) - 支持从右到左(RTL)文本方向

## 基本用法

### 导入模块

```python
from ui.i18n.localization import (
    format_date, format_time, format_datetime, 
    format_number, format_currency, format_percentage,
    format_file_size, LocalizationFormatter
)
```

### 简单示例

```python
import datetime

# 当前时间
now = datetime.datetime.now()

# 格式化日期 (使用中文)
chinese_date = format_date(now, "zh_CN")  # 例如：2023年06月24日

# 格式化数字 (使用英语)
english_number = format_number(1234.56, "en_US")  # 1,234.56

# 格式化货币 (使用欧元和德语)
german_currency = format_currency(1234.56, "EUR", "de")  # 1.234,56 €

# 格式化百分比
percentage = format_percentage(0.2356, "zh_CN")  # 23.56%

# 格式化文件大小
file_size = format_file_size(15728640, "en_US")  # 15.00 MB
```

### 自动检测系统语言

如果不指定语言代码，格式化函数会使用系统默认语言：

```python
# 使用系统语言格式化
system_date = format_date(now)  # 根据系统语言自动选择格式
```

### 使用 LocalizationFormatter 类

对于需要更高级自定义的场景，可以直接使用 `LocalizationFormatter` 类：

```python
# 创建格式化器实例
formatter = LocalizationFormatter()

# 自定义小数位数
custom_number = formatter.format_number(1234.56789, "zh_CN", decimal_places=3)  # 1,234.568
```

## 与文本方向适配集成

本地化格式化器已经与文本方向适配功能完全集成，这意味着对于从右到左(RTL)的语言（如阿拉伯语、希伯来语和波斯语），它能够正确处理文本方向：

```python
# 阿拉伯语日期格式化
arabic_date = format_date(now, "ar")  # 将以RTL方向显示
```

## 演示程序

项目提供了一个完整的演示程序 `localization_demo.py`，可以直接运行查看不同语言环境下的格式化效果：

```bash
python localization_demo.py
```

## 扩展和自定义

如果需要添加新的语言支持或自定义格式，可以通过以下方式进行：

1. 修改 `ui/i18n/localization.py` 文件中的 `LocalizationFormatter` 类
2. 在 `locale_mapping` 字典中添加新的语言映射
3. 在 `custom_formats` 字典中添加自定义格式

例如，添加意大利语支持：

```python
# 在 __init__ 方法中的 locale_mapping 字典添加：
"it": QLocale.Language.Italian,

# 在 custom_formats 字典添加：
"it": {
    "date_format": "dd/MM/yyyy",
    "time_format": "HH:mm:ss",
    "datetime_format": "dd/MM/yyyy HH:mm:ss",
    "short_date": "dd/MM/yyyy",
    "currency_format": "%1 €",
},
```

## 最佳实践

1. **始终使用格式化函数**：不要手动格式化日期、数字或货币，始终使用本地化格式化器
2. **在 UI 中应用格式化**：在显示任何数字、日期、货币等信息前应用适当的格式化
3. **保持原始数据**：在内部处理中保留原始数据格式，只在显示时应用格式化
4. **考虑RTL语言**：对于支持多语言的界面，确保布局能够适应RTL文本方向的变化

## 技术细节

本地化格式化器基于Qt的QLocale类实现，提供了高性能的本地化格式化功能。它通过以下方式工作：

1. 将语言代码映射到Qt的Locale对象
2. 使用Locale对象的toString方法格式化数据
3. 对于特殊需求，应用自定义格式字符串

该实现支持多种时间戳格式（datetime对象、Unix时间戳或ISO格式字符串），并具有良好的错误处理机制。

## 与其他模块的集成

本地化格式化器与以下模块无缝集成：

- **文本方向适配**：配合ui.utils.text_direction模块处理RTL语言
- **语言管理器**：与ui.i18n.language_manager协同工作
- **翻译引擎**：与ui.i18n.translation_engine配合，提供完整的国际化解决方案

## 未来计划

- 增加更多区域特定的格式支持
- 添加更多自定义格式选项
- 支持更多类型的数据格式化，如电话号码、地址等
- 提供更丰富的RTL语言支持 