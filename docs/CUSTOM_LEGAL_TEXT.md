# 用户自定义法律文本替换

## 概述

VisionAI-ClipsMaster 提供了灵活的用户自定义法律文本替换功能，允许用户:
- 替换默认法律声明中的特定文本（如公司名称、版权年份等）
- 创建和应用自定义替换模板
- 在不同类型的输出中（XML、JSON、SRT等）应用一致的替换规则
- 为不同的使用场景定义不同的模板集

此功能使您能够为所有导出内容提供个性化的法律声明，确保组织品牌的一致性和专业性。

## 主要功能

### 1. 变量替换

系统支持多种变量插值，您可以在法律文本中使用 `{variable_name}` 语法引用变量：

```
版权所有 © {current_year} {company_name}. 由 {app_name} v{version} 生成
```

**预定义变量**:
- `{company_name}` - 公司名称
- `{app_name}` - 应用名称
- `{current_year}` - 当前年份（自动更新）
- `{current_date}` - 当前日期
- `{author}` - 作者名称
- `{contact_email}` - 联系邮箱

### 2. 替换模板

系统支持创建和使用多个替换模板，方便在不同场景下应用不同的法律文本风格：

- **默认模板**: 适用于一般用途
- **商业模板**: 适用于商业用途，强调版权和使用限制
- **教育模板**: 适用于教育用途，强调归属和引用

每个模板包含一组文本替换规则，可快速应用于任何法律文本。

### 3. 正则表达式替换

除了简单的变量替换，系统还支持基于正则表达式的复杂替换规则，例如：
- 自动更新版权年份
- 替换特定格式的标识符
- 处理特殊格式的法律文本

### 4. 多种内容格式支持

支持对不同类型的内容进行处理：
- XML 项目文件
- JSON 配置文件
- SRT 字幕文件
- 纯文本内容

系统会根据内容类型自动选择适当的处理方式，确保替换的安全性和有效性。

## 配置文件

用户自定义替换规则存储在配置文件中，默认位置为 `~/.visionai_clips/custom_legal_rules.json`。配置文件结构如下：

```json
{
  "simple_replacements": {
    "company_name": "我的公司",
    "app_name": "VisionAI-ClipsMaster",
    "author": "AI视频创作者",
    "contact_email": "support@example.com"
  },
  "regex_replacements": {
    "版权所有\\s*©\\s*\\d{4}": "版权所有 © 2023",
    "Copyright\\s*©\\s*\\d{4}": "Copyright © 2023"
  },
  "full_replacements": {
    "AI Generated Content by ClipsMaster v1.0": "由{company_name}提供的AI生成内容",
    "本视频仅用于技术演示，不代表任何观点。内容由AI生成，可能存在不准确之处。": "本内容由{company_name}的AI系统生成，仅供参考，不代表{company_name}官方观点。"
  },
  "templates": {
    "default": {
      "ClipsMaster AI": "{company_name} AI",
      "仅用于技术演示": "仅供参考，请勿用于商业目的"
    },
    "commercial": {
      "ClipsMaster AI": "{company_name}",
      "仅用于技术演示": "保留所有权利，未经授权不得使用"
    }
  },
  "active_template": "default"
}
```

## 使用方法

### 基本用法

```python
from src.exporters.custom_legal import apply_custom_rules, load_user_config

# 加载用户配置
config = load_user_config()

# 应用自定义规则
original_text = "Copyright © 2023 ClipsMaster AI. 本视频仅用于技术演示。"
processed_text = apply_custom_rules(original_text, config)
```

### 直接替换（无需配置文件）

```python
from src.exporters.custom_legal import apply_direct

text = "版权所有 © 2023 {company_name}. 由{app_name}生成"
result = apply_direct(
    text,
    company_name="我的公司",
    app_name="超级剪辑"
)
```

### 创建自定义模板

```python
from src.exporters.custom_legal import create_user_template

# 创建新模板
template_rules = {
    "ClipsMaster AI": "专业视频工作室",
    "技术演示": "专业制作",
    "AI生成": "精心制作"
}

# 创建模板并设置为活动模板
config = create_user_template("professional", template_rules)
```

### 处理特定类型的内容

```python
from src.exporters.custom_legal import apply_custom_legal

# 读取XML文件
with open("project.xml", "r", encoding="utf-8") as f:
    xml_content = f.read()

# 处理XML内容
processed_xml = apply_custom_legal(xml_content, "xml")

# 写入处理后的XML
with open("processed_project.xml", "w", encoding="utf-8") as f:
    f.write(processed_xml)
```

### 与法律注入器集成

```python
from src.exporters.custom_legal import apply_to_legal_injector
from src.export.legal_injector import LegalInjector

# 创建法律注入器实例
injector = LegalInjector()

# 应用自定义规则到注入器
apply_to_legal_injector(injector)

# 现在注入器将使用自定义的法律文本
```

## 示例应用场景

### 1. 商业品牌定制

对于商业用户，可以创建包含公司名称、品牌标语和公司联系信息的自定义模板，确保所有导出内容都包含一致的品牌信息。

**示例模板**:
```json
{
  "ClipsMaster AI": "ABC公司视频工作室",
  "仅用于技术演示": "© 2023 ABC公司保留所有权利",
  "AI生成": "专业制作"
}
```

### 2. 教育用途定制

对于教育机构，可以创建强调学术引用和教育用途的模板。

**示例模板**:
```json
{
  "ClipsMaster AI": "XYZ大学媒体中心",
  "仅用于技术演示": "仅供教育目的使用",
  "AI生成": "由XYZ大学媒体中心制作"
}
```

### 3. 多语言支持

可以为不同语言创建不同的模板，确保法律声明适合目标受众。

**示例**:
```json
{
  "templates": {
    "zh": {
      "ClipsMaster AI": "{company_name} AI",
      "仅用于技术演示": "仅供参考，请勿用于商业目的"
    },
    "en": {
      "ClipsMaster AI": "{company_name} AI",
      "For Technical Demonstration Only": "For Reference Only, Not For Commercial Use"
    }
  }
}
```

## 最佳实践

1. **保持一致性**: 为组织创建统一的替换规则，确保所有输出内容使用一致的法律文本风格
2. **定期更新**: 定期更新版权年份和法律声明内容，确保符合最新要求
3. **测试替换效果**: 在应用到重要内容前，先测试替换效果，确保文本语义清晰、格式正确
4. **备份配置**: 定期备份自定义配置文件，避免意外丢失
5. **使用变量**: 尽量使用变量而非硬编码值，提高配置的灵活性和可维护性

## 演示脚本

系统提供了完整的演示脚本，展示各种功能的使用方法：

```bash
python examples/custom_legal_demo.py
```

演示内容包括：
- 简单的变量替换
- 使用预先定义的替换模板
- 创建和保存自定义模板
- 对不同类型内容进行处理
- 与Legal Injector集成

## 故障排除

**问题**: 替换未生效
- 检查变量名称是否正确，包括大小写
- 确认配置文件加载路径正确
- 检查"active_template"设置是否正确

**问题**: 正则表达式替换出错
- 确保正则表达式语法正确
- 对特殊字符进行适当转义
- 检查日志中的详细错误信息

**问题**: 内容格式错误
- 确保XML或JSON格式正确
- 在处理前进行格式验证
- 对特殊字符使用适当的转义处理 