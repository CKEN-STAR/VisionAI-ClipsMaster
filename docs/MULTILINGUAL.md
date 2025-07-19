# VisionAI-ClipsMaster 多语言支持文档

本文档详细介绍VisionAI-ClipsMaster应用程序的多语言支持功能、配置方法和开发指南。

## 目录

1. [支持的语言](#支持的语言)
2. [语言配置](#语言配置)
3. [使用方法](#使用方法)
4. [开发指南](#开发指南)
5. [添加新语言](#添加新语言)
6. [测试多语言功能](#测试多语言功能)
7. [常见问题](#常见问题)

## 支持的语言

VisionAI-ClipsMaster 当前支持以下语言：

| 语言代码 | 语言名称 | 完成度 |
|---------|---------|-------|
| zh_CN   | 简体中文 | 100%  |
| en_US   | 英语(美国) | 100% |
| ja_JP   | 日语 | 100%  |

注意：完成度指语言翻译的覆盖率。更多语言将在未来版本中添加。

## 语言配置

语言配置存储在 `configs/locale_config.json` 文件中，可以通过修改此文件来更改默认语言和其他设置：

```json
{
  "current_locale": "zh_CN",  // 当前语言
  "supported_locales": ["zh_CN", "en_US", "ja_JP"],  // 支持的语言列表
  "auto_detect_language": true,  // 是否自动检测系统语言
  "use_system_locale": false,  // 是否使用系统区域设置
  "fallback_locale": "en_US"  // 回退语言
}
```

## 使用方法

### 切换语言

用户可以通过以下方式切换应用程序语言：

1. 在主界面点击"设置"按钮
2. 选择"语言"选项
3. 从列表中选择所需语言
4. 点击"应用"按钮确认更改

语言切换后，界面将立即更新，无需重启应用程序。

### 开发者API

对于开发者，可以使用本地化管理器API来访问多语言功能：

```python
from src.utils.locale_manager import get_text, set_locale

# 设置语言
set_locale("en_US")

# 获取翻译文本
title = get_text("app_title")
confirm_btn = get_text("confirm")

# 格式化日期和时间
from src.utils.locale_manager import get_formatted_date, get_formatted_time
from datetime import datetime

now = datetime.now()
date_str = get_formatted_date(now)
time_str = get_formatted_time(now)
```

## 开发指南

### 文件结构

多语言支持相关文件的结构如下：

```
VisionAI-ClipsMaster/
├── configs/
│   └── locale_config.json  # 语言配置文件
├── resources/
│   └── locales/
│       ├── zh_CN.json      # 简体中文翻译
│       ├── en_US.json      # 英语(美国)翻译
│       └── ja_JP.json      # 日语翻译
├── src/
│   └── utils/
│       └── locale_manager.py  # 本地化管理器
└── tests/
    └── user_experience/
        └── i18n_test.py    # 多语言测试
```

### 本地化规则

为保持一致性，请遵循以下本地化规则：

1. **键名规则**：
   - 使用小写字母和下划线
   - 使用有意义且简洁的名称
   - 相关功能使用一致的前缀（如 `error_*`, `menu_*`）

2. **文本规则**：
   - 保持专业性和一致性
   - 考虑不同语言的文本长度差异
   - 保留原始格式化占位符（如 `%s`, `{0}`）

3. **日期时间格式**：
   - 遵循各语言的惯例
   - 中文: YYYY年MM月DD日
   - 英语: MM/DD/YYYY
   - 日语: YYYY年MM月DD日

## 添加新语言

要添加新语言支持，请按照以下步骤操作：

1. 在 `resources/locales/` 目录中创建新的语言文件，如 `ko_KR.json`
2. 将现有语言文件（如 `en_US.json`）复制为模板
3. 翻译所有文本键值
4. 在 `configs/locale_config.json` 中添加新语言代码到 `supported_locales` 数组
5. 运行翻译覆盖率测试以验证完整性

示例 - 添加韩语支持：

```json
// resources/locales/ko_KR.json
{
  "app_title": "VisionAI 클립마스터",
  "main_menu": "메인 메뉴",
  "file": "파일",
  "edit": "편집",
  // ... 其他翻译
}
```

## 测试多语言功能

可以使用提供的测试脚本来验证多语言功能：

```bash
# 测试所有语言
python run_locale_test.py

# 测试特定语言
python run_locale_test.py --locales zh_CN en_US

# 测试特定功能
python run_locale_test.py --test basic
python run_locale_test.py --test datetime
python run_locale_test.py --test coverage

# 输出结果到文件
python run_locale_test.py --output locale_test_results.txt
```

对于单元测试，可以运行：

```bash
python -m pytest tests/user_experience/i18n_test.py -v
```

## 常见问题

### 为什么某些文本未被翻译？

可能的原因：
- 缺少翻译键
- 硬编码的文本未使用本地化API
- 动态生成的文本没有适当处理

解决方案：
- 运行翻译覆盖率测试查找缺失的键
- 使用 `get_text()` 函数而非硬编码字符串
- 确保所有用户可见文本都通过本地化管理器

### 日期时间格式不正确

可能的原因：
- 缺少特定语言的格式定义
- 未使用本地化API格式化日期时间

解决方案：
- 检查 `configs/locale_config.json` 中的格式定义
- 使用 `get_formatted_date()` 和 `get_formatted_time()` 函数

### 如何支持RTL(从右到左)语言？

当前版本尚不完全支持RTL语言（如阿拉伯语和希伯来语）。计划在未来版本中添加支持。

---

如果您发现任何多语言相关的问题或有改进建议，请提交issue或联系开发团队。 