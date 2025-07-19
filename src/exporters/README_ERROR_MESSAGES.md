# 用户友好错误提示系统

用户友好错误提示系统为VisionAI-ClipsMaster项目提供多语言、结构化的错误消息展示功能。该系统能够将技术性错误代码和异常转换为终端用户可以理解的、提供解决方案建议的友好消息。

## 主要功能

- **多语言支持**：支持中文和英文两种语言的错误提示
- **变量插值**：错误消息中可包含动态变量，提供更具体的上下文信息
- **灵活的错误代码格式**：支持多种错误代码格式（十六进制字符串、整数、枚举等）
- **与异常系统集成**：自动从ClipMasterError异常中提取有用信息
- **优雅降级**：处理未知错误代码和普通异常的情况
- **简洁的API**：提供便捷的函数和格式化器类，适应不同使用场景

## 错误代码体系

错误代码采用十六进制格式，按功能模块分类：

- **0xE1xx**: 项目格式和配置错误
- **0xE2xx**: 视频处理错误
- **0xE3xx**: 音频处理错误
- **0xE4xx**: 模型和AI错误
- **0xE5xx**: 系统资源错误
- **0xE6xx**: 导出错误
- **0xE7xx**: 网络错误
- **0xE8xx**: 权限和授权错误
- **0xEFxx**: 一般错误

## 使用方法

### 基本使用

```python
from src.exporters.error_messages import generate_user_message

# 生成中文错误消息
chinese_msg = generate_user_message("0xE200", "zh")
print(chinese_msg)  # 输出: "视频文件损坏(代码:E200), 请检查视频文件完整性"

# 生成英文错误消息
english_msg = generate_user_message("0xE200", "en")
print(english_msg)  # 输出: "Video file corrupted (Code:E200), check video file integrity"

# 带变量的错误消息
format_msg = generate_user_message("0xE201", "zh", format="MOV")
print(format_msg)  # 输出: "不支持的视频格式(代码:E201), 当前格式: MOV"
```

### 从异常获取错误消息

```python
from src.exporters.error_messages import get_error_message
from src.utils.exceptions import ClipMasterError, ErrorCode

try:
    # 尝试处理视频
    process_video()
except ClipMasterError as e:
    # 获取用户友好错误消息
    user_msg = get_error_message(e, "zh")
    # 显示给用户
    show_error_dialog(user_msg)
except Exception as e:
    # 处理一般异常
    generic_msg = get_error_message(e, "zh")
    show_error_dialog(generic_msg)
```

### 使用错误消息格式化器

```python
from src.exporters.error_messages import ErrorMessageFormatter

# 创建格式化器
formatter = ErrorMessageFormatter(default_lang="zh")

# 格式化错误消息
msg = formatter.format_error(error)

# 切换语言
formatter.set_default_language("en")
english_msg = formatter.format_error(error)

# 指定语言覆盖默认设置
zh_msg = formatter.format_error(error, lang="zh")
```

### 便捷函数

```python
from src.exporters.error_messages import format_error, format_code, set_default_language

# 设置默认语言
set_default_language("zh")

# 格式化错误
msg = format_error(error)

# 格式化错误代码
code_msg = format_code("0xE100")
```

## 与错误日志系统集成

用户友好错误提示系统设计为与错误日志系统无缝集成：

```python
from src.exporters.error_logger import log_export_error
from src.exporters.error_messages import get_error_message
from src.utils.exceptions import ClipMasterError, ErrorCode

try:
    export_video()
except ClipMasterError as e:
    # 记录详细错误日志
    log_export_error(e, phase="EXPORT", video_hash="3a7bd3e2f")
    
    # 同时获取用户友好消息
    user_msg = get_error_message(e, "zh")
    
    # 显示给用户
    display_error_message(user_msg)
```

## 扩展错误代码

错误代码映射表位于`error_messages.py`文件的`ERROR_MAPPING`字典中。要添加新的错误代码：

1. 选择适当的错误代码范围
2. 为每种支持的语言添加消息
3. 如果需要变量插值，在消息中使用`{variable_name}`格式

示例：

```python
ERROR_MAPPING.update({
    "0xE900": {
        "zh": "自定义错误(代码:E900), 详情: {detail}",
        "en": "Custom error (Code:E900), details: {detail}"
    }
})
```

## 最佳实践

- 为每个错误提供清晰的原因和解决建议
- 在用户界面中总是使用用户友好消息，而不是技术错误代码
- 对于可能由用户操作导致的错误，提供具体的解决步骤
- 对于系统错误，提供明确的联系支持或报告问题的指导
- 在国际化应用中，始终使用相应的语言代码 