# VisionAI-ClipsMaster 文本方向适配

本文档介绍 VisionAI-ClipsMaster 的文本方向适配功能，该功能支持从右到左(RTL)的语言布局，如阿拉伯语、希伯来语和波斯语。

## 功能概述

文本方向适配模块使 VisionAI-ClipsMaster 能够根据所选语言自动调整界面布局方向，主要特点包括：

1. **自动检测系统语言**：启动时自动识别系统语言，并据此设置初始布局方向
2. **支持 RTL 语言**：完整支持阿拉伯语(ar)、希伯来语(he)和波斯语(fa)的从右到左布局
3. **动态切换**：允许用户在运行时切换界面语言和布局方向
4. **样式自适应**：自动调整文本对齐、按钮顺序和其他 UI 元素以匹配当前文本方向

## 支持的语言

目前支持以下语言的文本方向适配：

| 语言代码 | 语言名称 | 文本方向 |
|---------|--------|---------|
| zh      | 简体中文 | 从左到右 (LTR) |
| en      | 英文    | 从左到右 (LTR) |
| ar      | 阿拉伯语 | 从右到左 (RTL) |
| he      | 希伯来语 | 从右到左 (RTL) |
| fa      | 波斯语  | 从右到左 (RTL) |

## 使用方法

### 1. 通过启动器使用

启动器脚本 `launch_rtl_support.py` 提供了便捷的方式来启动支持 RTL 的应用：

```bash
# 启动简化 UI（默认）
python launch_rtl_support.py

# 指定启动新 UI
python launch_rtl_support.py --ui new

# 启动文本方向演示应用
python launch_rtl_support.py --ui demo

# 指定初始语言（例如阿拉伯语）
python launch_rtl_support.py --lang ar
```

### 2. 在代码中使用

在您自己的代码中集成文本方向适配功能：

```python
from ui.utils.text_direction import LayoutDirection, set_application_layout_direction, apply_rtl_styles

# 设置应用程序的布局方向
set_application_layout_direction("ar")  # 设置为阿拉伯语

# 检查是否为 RTL 语言
is_rtl = LayoutDirection.is_rtl_language("ar")  # 返回 True

# 应用 RTL 样式到窗口或部件
apply_rtl_styles(my_widget, "ar")
```

## 演示应用

本项目包含一个专门的演示应用 `text_direction_demo.py`，用于展示文本方向适配功能。演示应用具有以下特点：

1. 支持在多种语言之间切换
2. 实时显示文本方向变化
3. 展示各种 UI 元素在 RTL/LTR 布局下的表现
4. 包含多语言翻译示例

运行演示应用：

```bash
python text_direction_demo.py
```

## 技术实现

文本方向适配功能主要通过以下组件实现：

1. **LayoutDirection 类**：核心组件，负责管理布局方向切换
2. **set_application_layout_direction 函数**：设置整个应用程序的布局方向
3. **apply_rtl_styles 函数**：为特定组件应用 RTL 相关样式

核心逻辑位于 `ui/utils/text_direction.py` 文件中。

## 集成到现有项目

文本方向适配模块设计为非侵入式，可以轻松集成到现有项目中：

1. 引入必要的模块和类
2. 在初始化 UI 后调用 `setup_language_direction()` 方法
3. 在语言切换功能中添加布局方向切换逻辑

具体实现可参考 `simple_ui_text_direction.py` 文件。

## 注意事项

1. RTL 布局可能与某些第三方组件不完全兼容，需要额外调整
2. 某些复杂布局（如表格、图表）可能需要特殊处理
3. 建议在启用 RTL 支持后全面测试所有 UI 功能
4. 自定义绘制的组件可能需要额外的适配工作

## 未来计划

1. 添加更多 RTL 语言支持
2. 改进复杂 UI 组件的 RTL 适配
3. 实现完整的多语言翻译系统
4. 支持混合方向文本（如在阿拉伯语界面中显示英文内容） 