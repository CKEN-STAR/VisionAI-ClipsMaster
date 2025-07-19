# VisionAI-ClipsMaster 法律文本配置加载模块

## 模块概述

法律文本配置加载模块为VisionAI-ClipsMaster系统提供统一的法律文本管理功能，包括版权声明、免责声明和使用条款等内容。该模块通过配置文件实现多语言支持，并可根据不同场景提供定制化的法律文本。

## 核心功能

1. **多语言支持**：支持中英文双语法律文本，便于适应不同地区和场景的需求
2. **场景定制**：根据不同场景（如商业用途、教育用途等）提供差异化的法律文本
3. **格式设置**：为不同输出格式（如视频、文档、音频）提供专门的配置参数
4. **变量替换**：支持在法律文本中使用变量，实现动态内容生成
5. **单例模式**：采用单例模式实现，确保全局一致性
6. **容错机制**：当配置文件不存在或加载失败时，提供合理的默认值

## 主要文件

- `configs/legal_templates.yaml`: 法律文本模板配置文件
- `src/utils/legal_text_loader.py`: 法律文本加载器实现
- `src/quality/legal_scanner.py`: 版权验证器（已整合法律文本加载功能）
- `src/examples/demo_legal_text.py`: 演示程序
- `src/test_legal_loader.py`: 测试脚本
- `src/test_copyright_validator.py`: 版权验证器测试脚本

## 使用示例

### 基本使用

```python
from src.utils.legal_text_loader import load_legal_text

# 获取中文版权声明
copyright_zh = load_legal_text("copyright", "zh")
print(copyright_zh)  # 输出: "本视频由AI生成，版权归原作者所有"

# 获取英文免责声明
disclaimer_en = load_legal_text("disclaimer", "en")
print(disclaimer_en)  # 输出: "For technical demonstration only"

# 获取特定场景的声明（如商业用途）
commercial_disclaimer = load_legal_text("disclaimer", "zh", "commercial")
print(commercial_disclaimer)  # 输出: "本内容为商业用途，使用需获得授权"
```

### 高级用法

```python
from src.utils.legal_text_loader import LegalTextLoader

# 获取单例实例
loader = LegalTextLoader()

# 变量替换
variables = {
    "app_name": "ClipsMaster Pro",
    "current_year": "2023"
}
attribution = loader.get_legal_text("attribution", "zh", variables=variables)
print(attribution)

# 获取格式设置
video_settings = loader.get_format_settings("video")
print(video_settings)  # 输出: {'watermark_position': 'bottom-right', 'watermark_opacity': 0.8, 'credits_duration': 3.0}

# 重新加载配置
loader.reload_templates()
```

### 在版权验证器中使用

```python
from src.quality.legal_scanner import CopyrightValidator

# 创建版权验证器
validator = CopyrightValidator()

# 检查文本是否包含必要的版权声明
text = "这是一段测试文本，包含版权声明：本视频由AI生成，版权归原作者所有"
is_valid = validator.check_text_copyright(text)
print(is_valid)  # 输出: True

# 生成版权文本
copyright_text = validator.generate_copyright_text("zh", False)
print(copyright_text)
```

## 配置文件格式

`legal_templates.yaml` 文件使用以下结构：

```yaml
templates:
  zh:
    copyright: "本视频由AI生成，版权归原作者所有"
    disclaimer: "本内容仅用于技术演示，禁止商用"
    # 其他中文模板...
  
  en:
    copyright: "AI Generated Content, All Rights Reserved"
    disclaimer: "For technical demonstration only"
    # 其他英文模板...

format_templates:
  video:
    watermark_position: "bottom-right"
    # 视频格式的其他设置...
  
  document:
    # 文档格式的设置...

special_cases:
  commercial:
    zh:
      disclaimer: "本内容为商业用途，使用需获得授权"
    # 其他商业场景设置...
  
  educational:
    # 教育场景设置...
```

## 扩展方法

要添加新的法律文本类型，只需在配置文件中的相应语言部分添加新条目：

```yaml
templates:
  zh:
    new_legal_text: "这是新添加的法律文本"
  en:
    new_legal_text: "This is newly added legal text"
```

然后可以通过 `load_legal_text("new_legal_text", "zh")` 来获取。

## 注意事项

1. 确保法律文本符合相关法律法规和平台规定
2. 针对不同地区和用途，可能需要定制不同的法律文本
3. 程序发布前应进行法律合规性检查 