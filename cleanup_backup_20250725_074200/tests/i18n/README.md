# VisionAI-ClipsMaster 多语言测试框架

这是VisionAI-ClipsMaster项目的多语言测试框架，用于测试多语言支持、文本方向和本地化格式化等功能。

## 框架结构

```
tests/i18n/
├── __init__.py             # 包初始化文件
├── test_localization.py    # 本地化格式化测试
├── test_text_direction.py  # RTL文本方向测试
├── test_ui_compatibility.py # UI文本溢出和输入法兼容性测试
├── test_framework.py       # 测试辅助函数和模拟类
├── run_language_tests.py   # 测试运行器
├── resources/              # 测试资源
│   └── test_data.py        # 测试数据
└── README.md               # 本文档
```

## 测试覆盖范围

多语言测试框架涵盖以下方面的测试：

1. **文本溢出检测** - 测试不同语言下UI元素的文本显示是否正常，避免文本溢出
2. **布局方向验证** - 测试RTL(从右到左)语言的布局方向是否正确
3. **日期/数字格式化** - 测试不同语言环境下日期、时间、数字和货币的格式化
4. **输入法兼容性** - 测试多语言输入法的兼容性

## 使用方法

### 运行所有测试

```bash
python tests/i18n/run_language_tests.py
```

### 运行指定测试

```bash
python tests/i18n/run_language_tests.py -t test_localization.py
```

### 添加新的测试

1. 创建新的测试文件，如`test_new_feature.py`
2. 导入必要的模块和测试框架辅助函数
3. 编写测试类和测试方法
4. 使用`run_language_tests.py`运行测试

## 开发指南

### 添加新的测试数据

在`resources/test_data.py`文件中添加新的测试数据。

### 扩展测试框架

如需扩展测试框架的功能，可以在`test_framework.py`文件中添加新的辅助函数或类。

### 测试结果

测试结果将显示在控制台中，也可以使用`pytest`的参数生成HTML或XML格式的报告。

## 注意事项

- 测试框架依赖`pytest`，请确保已安装
- 测试中的模拟类和函数仅用于测试，不应在生产环境中使用
- 在添加新的测试时，应确保测试覆盖到不同语言和文化背景下的使用场景 