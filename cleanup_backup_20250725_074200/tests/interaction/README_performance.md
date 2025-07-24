# 性能基准测试

本目录包含VisionAI-ClipsMaster应用的性能基准测试框架，用于测量应用程序的交互响应时间和渲染性能，确保用户体验流畅。

## 测试框架组件

- **performance_bench.py**: 性能分析器，用于测量UI交互的响应时间
- **performance_test_example.py**: 性能测试示例，展示如何使用测试框架
- **run_performance_tests.py**: 测试脚本，用于运行性能测试

## 性能基准指标

框架定义了以下交互操作的性能基准：

| 操作类型 | 最大延迟 (ms) | 描述 |
|---------|--------------|------|
| ButtonClick | 200 | 按钮点击延迟 |
| TextInput | 500 | 文本输入延迟 |
| ComplexDrag | 1000 | 复杂拖拽延迟 |
| MenuOpen | 300 | 菜单打开延迟 |
| TabSwitch | 400 | 标签页切换延迟 |
| DialogOpen | 600 | 对话框打开延迟 |
| FileOpen | 1500 | 文件打开延迟 |
| RenderUpdate | 100 | 渲染更新延迟 |
| ScrollOperation | 150 | 滚动操作延迟 |
| HoverEffect | 50 | 悬停效果延迟 |

## 如何运行测试

### 方法1: 使用测试脚本

```bash
# 运行自动化测试
python tests/run_performance_tests.py

# 运行交互式测试
python tests/run_performance_tests.py --mode interactive

# 测试simple_ui
python tests/run_performance_tests.py --mode simple_ui

# 指定测试类型
python tests/run_performance_tests.py --test-types button,input

# 指定测试迭代次数
python tests/run_performance_tests.py --iterations 20

# 指定报告输出路径
python tests/run_performance_tests.py --report ./my_report.html

# 显示详细日志
python tests/run_performance_tests.py --verbose
```

### 方法2: 使用示例程序

```bash
# 运行测试示例
python tests/interaction/performance_test_example.py
```

### 方法3: 直接使用测试框架

```python
from tests.interaction.performance_bench import InteractionProfiler, PerformanceTestRunner

# 创建性能分析器
profiler = InteractionProfiler()

# 测量操作响应时间
def my_action():
    # 执行某些操作
    pass

duration = profiler.measure_response(my_action, "ButtonClick")
print(f"操作耗时: {duration}ms")

# 断言性能符合基准
is_fast_enough = profiler.assert_performance(my_action, "ButtonClick")
print(f"性能是否符合基准: {is_fast_enough}")

# 运行完整测试
runner = PerformanceTestRunner()
runner.run_comprehensive_test(main_window)
```

## 测试报告

测试报告将保存在 `tests/reports/performance/` 目录下，默认文件名为 `performance_report_<timestamp>.html`。报告包含以下内容：

- 测试摘要信息
- 各操作类型的性能统计
- 与基准值的比较
- 可视化图表

## 事件监控

框架还提供了事件监控功能，可以监控UI事件并测量响应时间：

```python
from tests.interaction.performance_bench import EventMonitor

# 创建事件监视器
monitor = EventMonitor()

# 开始监控
monitor.start_monitoring()

# 执行一些操作
# ...

# 停止监控
monitor.stop_monitoring()
```

## 扩展测试框架

### 添加新的性能基准

在 `performance_bench.py` 中的 `InteractionProfiler.MAX_LATENCY` 字典中添加新的基准：

```python
MAX_LATENCY = {
    # 现有基准
    "ButtonClick": 200,
    # 添加新基准
    "NewOperation": 300  # 新操作的最大延迟为300ms
}
```

### 添加新的测试方法

在 `PerformanceTestRunner` 类中添加新的测试方法：

```python
def run_new_test(self, widget):
    """运行新测试"""
    self.profiler.start_test("NewTest")
    
    # 测试代码
    def my_action():
        # 执行某些操作
        pass
    
    self.profiler.measure_response(my_action, "NewOperation")
    
    return self.profiler.end_test()
```

## 注意事项

1. 性能测试结果可能受到系统负载、硬件配置等因素的影响，建议在稳定的环境中运行测试。
2. 对于复杂的UI操作，可能需要调整基准值以适应不同的硬件和平台。
3. 测试过程中可能会短暂显示测试窗口，这是正常现象。
4. 如果测试失败，请查看日志以获取详细信息。
5. 对于自动化测试，建议增加适当的延迟，以确保事件处理完成。 