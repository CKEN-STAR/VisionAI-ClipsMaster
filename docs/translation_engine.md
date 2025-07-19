# VisionAI-ClipsMaster 动态翻译引擎

VisionAI-ClipsMaster 的动态翻译引擎提供了一个强大的多语言翻译系统，支持上下文感知的翻译、嵌套键值和参数格式化。

## 主要特性

- **上下文感知翻译**: 根据不同的上下文为相同的键提供不同的翻译
- **嵌套键值对**: 支持分层组织的翻译资源
- **参数格式化**: 在翻译文本中支持动态参数替换
- **缓存优化**: 使用LRU缓存提高性能
- **完整集成**: 与现有的资源管理器和UI框架无缝集成

## 使用方法

### 基本翻译

```python
from ui.i18n.translation_engine import tr

# 基本翻译，无上下文
text = tr("", "hello", default="你好")

# 带上下文的翻译
welcome_text = tr("main_window", "welcome", default="欢迎")
error_message = tr("dialog", "error", default="错误")
```

### 带参数的翻译

```python
# 带参数格式化的翻译
file_error = tr("errors", "file_not_found", default="文件未找到: {path}", path="example.txt")

# 多参数
message = tr("user", "greeting", default="你好，{name}！今天是{date}。", 
             name="张三", date="2023-05-01")
```

### 嵌套键访问

```python
# 通过 context.key 格式直接访问嵌套键
from ui.i18n.translation_engine import get_nested_text

text = get_nested_text("dialog.title", default="对话框标题")
```

### 语言切换

```python
from ui.i18n.translation_engine import update_language

# 切换到英文
update_language("en_US")

# 切换到中文
update_language("zh_CN")

# 切换到日文
update_language("ja_JP")
```

### UI集成

```python
from ui.i18n.translation_integration import get_translation_integrator

# 获取集成器
integrator = get_translation_integrator()

# 重新翻译界面
integrator.retranslate_ui(my_widget)

# 配置应用程序翻译
integrator.setup_application(app)
```

### SimpleUI集成

```python
from simple_ui_language_integration import integrate_language_with_simple_ui

# 将语言支持集成到SimpleScreenplayApp
helper = integrate_language_with_simple_ui(main_window)

# 更新UI文本
helper.update_ui_texts()
```

## 语言资源格式

语言资源文件使用JSON格式，支持嵌套结构：

```json
{
  "app_title": "VisionAI 短视频剪辑大师",
  
  "dialog": {
    "title": "对话框",
    "ok": "确定",
    "cancel": "取消"
  },
  
  "errors": {
    "file_not_found": "文件未找到: {path}"
  }
}
```

## 添加新语言

1. 在 `resources/locales` 目录下创建新的语言文件（例如 `fr_FR.json`）
2. 在 `ui/resource_manager.py` 文件中的 `LanguageResource.LANG_PACKS` 中添加新语言配置
3. 重启应用程序以加载新语言

## 架构

动态翻译引擎由以下几个主要组件组成：

- **翻译引擎 (ui/i18n/translation_engine.py)**: 核心翻译功能
- **集成模块 (ui/i18n/translation_integration.py)**: 与UI框架的集成
- **资源处理器 (ui/i18n/resource_handler.py)**: 与资源管理器的连接
- **SimpleUI集成 (simple_ui_language_integration.py)**: 与SimpleUI的集成

## 最佳实践

1. **使用上下文**: 始终使用适当的上下文来组织翻译键
2. **提供默认值**: 总是提供默认值作为回退选项
3. **使用参数**: 对于含有变量的字符串，使用参数格式化而不是字符串拼接
4. **保持一致性**: 在整个应用程序中保持一致的命名约定
