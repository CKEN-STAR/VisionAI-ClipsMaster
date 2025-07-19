# 跨平台兼容测试

本目录包含VisionAI-ClipsMaster应用的跨平台兼容性测试框架，用于测试应用程序在不同操作系统和显示设置下的表现。

## 测试框架组件

- **cross_platform.py**: 平台模拟器，用于模拟不同操作系统环境和显示设置
- **ui_test_runner.py**: UI测试运行器，用于执行UI测试
- **cross_platform_test_example.py**: 跨平台测试示例，展示如何使用测试框架

## 支持的平台

- Windows 11 (1920x1080, DPI 96)
- macOS 14 (2560x1440, DPI 110)
- Linux Ubuntu 22 (1366x768, DPI 96)
- Android 13 (1080x2340, DPI 420)

## 如何运行测试

### 方法1: 使用测试脚本

```bash
# 运行所有跨平台测试
python tests/run_platform_tests.py

# 仅运行平台模拟测试
python tests/run_platform_tests.py --mode platform

# 仅运行UI测试
python tests/run_platform_tests.py --mode ui

# 指定测试平台
python tests/run_platform_tests.py --platforms windows,macos

# 指定报告输出路径
python tests/run_platform_tests.py --report ./my_report.html

# 显示详细日志
python tests/run_platform_tests.py --verbose
```

### 方法2: 使用示例程序

```bash
# 运行测试示例
python tests/interaction/cross_platform_test_example.py
```

然后按照提示选择测试类型：

1. 测试简单组件
2. 测试SimpleScreenplayApp
3. 运行完整测试套件

### 方法3: 直接使用测试框架

```python
from tests.interaction.cross_platform import PlatformSimulator, TestRunner
from tests.interaction.ui_test_runner import UITestRunner

# 创建平台模拟器
simulator = PlatformSimulator()

# 模拟Windows平台
simulator.simulate_platform("windows")
simulator.simulate_screen((1920, 1080), 96)

# 创建UI测试运行器
runner = UITestRunner()

# 运行UI测试
result = runner.run_simple_ui_test("windows", (1920, 1080), 96)
print(f"测试结果: {'通过' if result.get('success', False) else '失败'}")
```

## 测试报告

测试报告将保存在 `tests/reports/` 目录下，默认文件名为 `platform_test_report.html`。报告包含以下内容：

- 测试平台信息
- 测试结果摘要
- 每个平台的测试结果详情
- 发现的问题列表

## 扩展测试框架

### 添加新的平台配置

在 `cross_platform.py` 中的 `PlatformSimulator.PLATFORM_CONFIGS` 字典中添加新的平台配置：

```python
"new_platform": {
    "style": "fusion",
    "attributes": {
        Qt.ApplicationAttribute.AA_UseHighDpiPixmaps: True
    },
    "resolution": (1280, 720),
    "dpi": 120
}
```

### 添加新的测试用例

在 `ui_test_runner.py` 中添加新的测试方法：

```python
def test_new_feature(self, window: QMainWindow, result: Dict[str, Any]) -> None:
    """测试新功能"""
    # 测试代码
    pass
```

然后在 `_test_ui_elements` 或 `_test_basic_interactions` 中调用新方法。

## 注意事项

1. 测试框架只能模拟Qt应用程序的平台特定行为，无法完全模拟操作系统环境。
2. 在实际测试中，建议在真实的操作系统环境中运行测试，以获取更准确的结果。
3. 测试过程中可能会短暂显示测试窗口，这是正常现象。
4. 如果测试失败，请查看日志以获取详细信息。 