# 错误可视化系统

VisionAI-ClipsMaster的错误可视化系统提供了美观、直观且具有交互性的错误展示界面，帮助用户更好地理解错误并提供解决方案。

## 概述

错误可视化系统采用了全息投影式设计，通过动画效果和分层信息展示，降低了用户在遇到错误时的焦虑感，并提供了清晰的解决路径。

## 主要特性

### 1. 全息投影式显示

- 半透明背景叠加，创造类似全息投影的视觉效果
- 渐入渐出动画，提供平滑的视觉体验
- 错误信息分层展示，便于快速把握重点

### 2. 错误类型区分

系统支持多种错误类型，并通过不同的视觉标识进行区分：

- **严重错误(CRITICAL)**: 需要立即处理的系统级错误
- **一般错误(ERROR)**: 常规操作错误
- **警告(WARNING)**: 潜在问题提示
- **信息(INFO)**: 一般通知
- **调试(DEBUG)**: 开发调试信息

### 3. 解决方案建议

- 针对常见错误提供一键解决方案
- 支持多个解决步骤选择
- 与用户反馈系统集成

### 4. 集成与兼容性

- 与主程序无缝集成
- 支持在不同模块中统一调用
- 提供向下兼容的传统错误提示方式

## 实现细节

### 类结构

1. **ErrorType**: 错误类型常量定义
2. **ErrorInfo**: 结构化错误信息数据类
3. **HolographicErrorDisplay**: 全息错误显示组件
4. **ErrorDisplayManager**: 错误显示管理器

### 示例用法

```python
# 导入模块
from ui.feedback.error_visualizer import ErrorInfo, ErrorType, show_error

try:
    # 执行可能出错的操作
    result = process_video(video_path)
except Exception as e:
    # 显示错误
    error_info = ErrorInfo(
        title="视频处理失败",
        description=str(e),
        error_type=ErrorType.ERROR,
        solutions=["检查视频文件", "尝试其他格式"]
    )
    show_error(error_info)
```

## 开发者注意事项

1. 使用`show_error`函数可以在任何位置显示错误
2. 可以传入`ErrorInfo`对象或直接传入异常对象
3. 检查`HAS_ERROR_VISUALIZER`变量确定是否支持错误可视化

## 未来计划

- 支持更多的自定义主题
- 添加更丰富的动画效果
- 提供错误统计和分析功能
- 集成机器学习推荐最佳解决方案 