# VisionAI-ClipsMaster 用户界面配置绑定系统

本模块提供了一个强大的用户界面配置绑定系统，实现了界面元素与配置系统的双向同步。

## 主要功能

- **双向绑定**：UI元素的更改自动同步到配置系统，配置系统的更改也自动同步到UI元素
- **支持多种UI组件**：支持常见的所有Qt控件，包括下拉框、文本输入框、复选框等
- **配置热重载**：支持配置文件实时监控和自动重载
- **验证器支持**：可以为每个配置项添加验证函数，确保输入值符合要求
- **数据转换**：支持UI值和配置值之间的自动转换
- **便捷的插件接口**：简化现有应用程序的集成过程

## 核心组件

1. **ConfigBinder**：配置绑定器，核心类，负责UI元素和配置之间的双向绑定
2. **Validators**：验证器集合，提供常用的验证函数
3. **Transformers**：转换器集合，提供常用的数据转换函数
4. **BiTransformer**：双向转换器基类，用于创建自定义的双向转换器
5. **ConfigBinderPlugin**：配置绑定插件，简化与现有应用程序的集成

## 使用方法

### 1. 基本用法

```python
from src.ui.ui_config_panel import ConfigBinder, Validators, Transformers

# 创建UI元素字典
ui_elements = {
    "resolution_dropdown": self.resolution_combo,
    "output_path": self.output_path
}

# 创建配置绑定器
binder = ConfigBinder(ui_elements, "export")

# 绑定配置
binder.bind("video.resolution", "resolution_dropdown", "1280x720")
binder.bind("output.path", "output_path", "D:/output")

# 加载配置到UI
binder.config_to_ui()

# 保存UI值到配置
binder.ui_to_config()
```

### 2. 使用验证器

```python
from src.ui.ui_config_panel import ConfigBinder, Validators

binder = ConfigBinder(ui_elements, "system")

# 使用范围验证器
binder.bind("performance.threads", "threads_spinbox", 4, 
           validator=Validators.range(1, 16))

# 使用正则表达式验证器
binder.bind("user.email", "email_input", "",
           validator=Validators.pattern(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"))
```

### 3. 使用转换器

```python
from src.ui.ui_config_panel import ConfigBinder, Transformers

binder = ConfigBinder(ui_elements, "user")

# 使用路径转换器
binder.bind("project.path", "project_path_input", "D:/Projects",
           transformer=Transformers.path_to_string())

# 使用布尔值转换器
binder.bind("interface.auto_save", "auto_save_checkbox", True,
           transformer=Transformers.bool_to_str())
```

### 4. 创建自定义的双向转换器

```python
from src.ui.ui_config_panel import BiTransformer

class TimeTransformer(BiTransformer):
    """时间转换器，在秒和格式化时间字符串之间转换"""
    
    def forward(self, value):
        """秒 -> '分:秒'"""
        if isinstance(value, (int, float)):
            minutes = int(value) // 60
            seconds = int(value) % 60
            return f"{minutes:02d}:{seconds:02d}"
        return str(value)
    
    def inverse(self, value):
        """'分:秒' -> 秒"""
        if isinstance(value, str) and ":" in value:
            try:
                minutes, seconds = value.split(":")
                return int(minutes) * 60 + int(seconds)
            except ValueError:
                pass
        return value

# 使用自定义转换器
time_transformer = TimeTransformer()
binder.bind("video.duration", "duration_input", 120, transformer=time_transformer)
```

### 5. 使用配置绑定插件

```python
from src.ui.ui_config_plugin import ConfigBinderPlugin

# 创建并初始化配置插件
plugin = ConfigBinderPlugin(app)
plugin.initialize_app_settings()

# 注册配置变更回调
plugin.register_config_change_callback(on_config_changed)

# 应用预设
plugin.apply_preset("high_quality")

# 保存配置
plugin.save_configs()
```

## 配置面板

我们还提供了一个完整的配置面板实现，可以直接集成到您的应用程序中：

```python
from src.ui.config_panel import ConfigPanel

# 创建配置面板
config_panel = ConfigPanel()
config_panel.config_saved.connect(on_config_saved)
config_panel.show()
```

## 集成示例

提供了一个完整的集成示例，展示如何将配置绑定系统集成到现有应用程序中：

```python
# 运行集成示例
python -m src.ui.run_config_demo --type integration
```

## 自定义扩展

您可以通过以下方式扩展系统功能：

1. **自定义验证器**：创建自己的验证函数，接受一个值并返回布尔值
2. **自定义转换器**：创建自己的转换函数，或者继承`BiTransformer`类实现双向转换
3. **自定义配置面板**：继承`ConfigPanel`类，定制您自己的配置界面

## 注意事项

1. 确保所有的UI元素ID在UI元素字典中是唯一的
2. 验证器和转换器应该处理所有可能的输入情况，避免抛出异常
3. 当使用热重载时，确保配置文件格式正确，避免加载错误的配置

## 故障排除

如果您遇到以下问题：

1. **配置不同步**：确保正确调用了`config_to_ui()`或`ui_to_config()`方法
2. **验证器不工作**：检查验证器函数是否正确实现并返回布尔值
3. **转换器错误**：确保转换器能够处理所有可能的输入类型
4. **热重载问题**：检查配置文件路径和格式是否正确

## 完整演示

运行以下命令查看完整演示：

```
python -m src.ui.run_config_demo
``` 