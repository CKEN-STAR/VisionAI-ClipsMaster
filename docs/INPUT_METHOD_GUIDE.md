# VisionAI-ClipsMaster 输入法支持指南

本文档介绍了VisionAI-ClipsMaster中输入法支持功能的使用方法和技术细节。

## 概述

输入法支持模块提供了对多语言输入的全面支持，包括：

- 中文拼音输入
- 日语假名输入
- 韩语输入
- 阿拉伯语文本处理
- 印度语系复杂脚本渲染
- 泰语等其他语言输入

该模块与语言管理器和文本方向适配模块无缝集成，为多语言环境下的文本输入提供完整解决方案。

## 功能特性

- **多语言输入法适配**：根据语言自动设置输入法提示
- **RTL(从右到左)语言支持**：适配阿拉伯语、希伯来语等RTL语言
- **字体自动适配**：根据语言自动选择合适的字体
- **文本方向控制**：自动设置文本方向以适应不同语言
- **复杂脚本渲染**：支持印度语系等复杂脚本的正确渲染

## 使用方法

### 基本用法

```python
from ui.i18n import configure_widget_for_language, set_input_method_language

# 配置文本编辑器支持中文输入
text_edit = QTextEdit()
configure_widget_for_language(text_edit, "zh_CN")

# 切换到日语输入法
set_input_method_language("ja_JP")
```

### 获取输入法支持实例

```python
from ui.i18n import get_input_method_support

# 获取单例实例
input_method_support = get_input_method_support()

# 监听输入法变更信号
input_method_support.input_method_changed.connect(on_input_method_changed)
```

### 手动配置文本输入控件

```python
from ui.i18n import get_input_method_support

input_method_support = get_input_method_support()

# 为文本控件安装事件过滤器
input_method_support.install_event_filter(text_edit)

# 设置适合语言的字体
input_method_support.set_font_for_language(text_edit, "ar_SA")

# 应用输入法提示
input_method_support.apply_input_method_hints(text_edit, "zh_CN")

# 完整配置文本输入控件
input_method_support.configure_text_input(text_edit, "hi_IN")
```

## 支持的语言

输入法支持模块支持以下语言：

| 语言代码 | 语言名称 | 特殊处理 |
|---------|---------|---------|
| zh_CN   | 中文(简体) | 优化输入提示，适配中文字体 |
| ja_JP   | 日语 | 优化输入提示，日文字体支持 |
| ko_KR   | 韩语 | 优化输入提示，韩文字体支持 |
| ar_SA   | 阿拉伯语 | RTL支持，适配阿拉伯字体 |
| hi_IN   | 印地语 | 复杂脚本渲染，专用字体 |
| bn_BD   | 孟加拉语 | 复杂脚本渲染，专用字体 |
| th_TH   | 泰语 | 复杂文字处理，专用字体 |
| he_IL   | 希伯来语 | RTL支持，专用字体 |
| ur_PK   | 乌尔都语 | RTL支持，复杂脚本 |
| fa_IR   | 波斯语 | RTL支持，专用字体 |
| ta_IN   | 泰米尔语 | 复杂脚本渲染，专用字体 |
| en_US   | 英语(美国) | 标准拉丁输入 |
| ru_RU   | 俄语 | 西里尔字母支持 |

## 字体支持

针对不同语言，输入法支持模块会自动选择适合的字体。默认选择如下：

- 中文：Microsoft YaHei, SimHei, SimSun
- 日语：Yu Gothic, MS Gothic, Meiryo
- 韩语：Malgun Gothic, Gulim, Batang
- 阿拉伯语/希伯来语：Arial, Tahoma, Segoe UI
- 印度语系：Nirmala UI, Mangal
- 泰语：Leelawadee UI, Tahoma
- 西文：Segoe UI, Arial, Tahoma

## 文本方向适配

对于RTL语言（如阿拉伯语、希伯来语），输入法支持模块会自动设置正确的文本方向：

```python
# 配置阿拉伯语输入，自动设置RTL方向
configure_widget_for_language(text_edit, "ar_SA")
```

## 与现有UI集成

### 在现有表单中添加输入法支持

```python
from ui.i18n import configure_widget_for_language

class MyForm(QWidget):
    def __init__(self):
        super().__init__()
        
        # 创建表单控件
        self.name_edit = QLineEdit()
        self.comment_edit = QTextEdit()
        
        # 配置输入法支持
        configure_widget_for_language(self.name_edit, "zh_CN")
        configure_widget_for_language(self.comment_edit, "zh_CN")
```

### 动态切换输入法

```python
from ui.i18n import set_input_method_language

def on_language_changed(lang_code):
    # 切换输入法
    set_input_method_language(lang_code)
    
    # 可能需要更新UI方向
    update_ui_direction(lang_code)
```

## 高级用法

### 自定义字体

```python
from ui.i18n import get_input_method_support

ims = get_input_method_support()

# 获取适合中文的字体列表
chinese_fonts = ims.get_suitable_fonts_for_language("zh_CN")

# 使用自定义字体
custom_font = QFont("My Custom Font", 12)
text_edit.setFont(custom_font)
```

### 监听输入法变更

```python
from ui.i18n import get_input_method_support

ims = get_input_method_support()

# 监听输入法变更信号
ims.input_method_changed.connect(self.on_input_method_changed)

def on_input_method_changed(language):
    print(f"输入法已变更为: {language}")
    # 执行其他操作...
```

### 重置输入法状态

```python
from ui.i18n import get_input_method_support

ims = get_input_method_support()

# 重置特定控件的输入法
ims.reset_input_method(text_edit)

# 重置全局输入法状态
ims.reset_input_method()
```

## 示例程序

参考`input_method_demo.py`中的完整示例，该示例展示了：

1. 多语言输入切换
2. 不同语言的文本输入
3. RTL语言支持
4. 字体自动适配

## 技术细节

输入法支持模块基于以下技术实现：

- **PyQt5 输入法支持**：利用Qt的输入法机制
- **输入法提示**：通过`setInputMethodHints`设置适当的输入法提示
- **字体自动适配**：根据语言选择合适的字体
- **事件过滤**：处理输入法相关的特殊事件
- **文本方向控制**：结合文本方向适配模块实现RTL支持

## 常见问题

### 问题：某些语言的字符无法正确显示

**解决方案**：确保系统安装了适合该语言的字体。例如，显示中文需要安装中文字体如"Microsoft YaHei"或"SimSun"。

### 问题：RTL文本显示混乱

**解决方案**：确保正确调用了`configure_widget_for_language`并传入正确的RTL语言代码（如"ar_SA"）。

### 问题：输入法切换不生效

**解决方案**：确保应用程序初始化时已创建了QApplication实例，并且在调用输入法相关功能之前先创建UI控件。

## 更多资源

- 查看`ui/i18n/input_method.py`源代码获取更多技术细节
- 运行`input_method_demo.py`体验完整功能
- 参考`ui/utils/text_direction.py`了解文本方向适配的实现 