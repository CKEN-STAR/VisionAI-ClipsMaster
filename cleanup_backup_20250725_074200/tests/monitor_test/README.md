# VisionAI-ClipsMaster 监控系统测试

本目录包含VisionAI-ClipsMaster项目监控系统的测试用例，用于确保监控功能的正确性和稳定性。

## 测试内容

### 看板交互测试

`test_dashboard.py` 文件包含了对监控看板交互功能的测试，主要测试以下功能：

1. **仪表盘初始化** - 测试仪表盘组件是否正确加载
2. **告警触发** - 测试当指标超过阈值时，告警系统是否正确触发
3. **告警消除** - 测试当指标恢复正常后，告警是否可以正确消除

### 平台兼容性测试

`platform_test.py` 文件包含了对不同平台兼容性的测试，确保监控系统在各种环境下正常工作。

### 集成测试

`integration_test.py` 文件包含了监控系统与其他模块集成的测试用例。

### 压力测试

`stress_test.py` 文件包含了监控系统在高负载情况下的稳定性测试。

## 运行测试

### 运行单个测试文件

```bash
# 运行看板交互测试
python -m tests.monitor_test.test_dashboard

# 运行平台兼容性测试
python -m tests.monitor_test.platform_test

# 运行集成测试
python -m tests.monitor_test.integration_test

# 运行压力测试
python -m tests.monitor_test.stress_test
```

### 运行所有测试

```bash
# 运行所有监控系统测试
python -m tests.monitor_test.run_dashboard_tests
```

## 测试环境要求

- Python 3.8+
- PyQt6
- pytest
- 项目依赖项（见 requirements.txt）

## 添加新测试

添加新测试时，请遵循以下规范：

1. 测试文件命名为 `test_*.py`
2. 测试类继承 `unittest.TestCase`
3. 测试方法命名为 `test_*`
4. 使用 `setUp` 和 `tearDown` 方法设置和清理测试环境
5. 使用 `assert*` 方法验证测试结果

示例：

```python
class TestNewFeature(unittest.TestCase):
    def setUp(self):
        # 设置测试环境
        pass
        
    def tearDown(self):
        # 清理测试环境
        pass
        
    def test_feature_functionality(self):
        # 测试功能
        self.assertTrue(feature_works())
```

## 测试工具函数

`test_dashboard.py` 文件中提供了一些有用的测试工具函数：

- `find_widget(parent, widget_name)` - 在父部件中查找指定名称的子部件
- `inject_metrics(dashboard, metrics, duration)` - 向仪表盘注入模拟指标数据
- `wait_for(condition_func, timeout)` - 等待条件满足

## 常见问题

### 测试时UI不显示

确保在测试类的 `setUpClass` 方法中创建了 QApplication 实例：

```python
@classmethod
def setUpClass(cls):
    cls.app = QApplication.instance() or QApplication([])
```

### 测试超时

如果测试运行时间过长，可能是因为某些操作阻塞了事件循环。确保在等待操作完成时调用 `QApplication.processEvents()`。

### 测试失败但UI正常

可能是因为测试执行太快，UI来不及更新。使用 `wait_for` 函数等待UI更新完成。 