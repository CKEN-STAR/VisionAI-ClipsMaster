# VisionAI-ClipsMaster 测试框架

这个目录包含 VisionAI-ClipsMaster 的测试框架和测试用例，以及用于生成测试报告的工具。

## 测试组件

测试框架包含以下组件：

1. **单元测试**: 测试各个组件的功能正确性
2. **集成测试**: 测试组件间的交互和协作
3. **压力测试**: 测试系统在极端情况下的表现
4. **配置系统测试**: 测试配置管理、热重载和安全存储功能
5. **隐私测试**: 测试隐私保护和数据安全功能
6. **法律合规性测试**: 测试水印检测和版权保护功能
7. **用户旅程测试**: 测试不同用户场景下的使用体验
8. **测试报告生成器**: 收集测试结果并生成HTML报告

## 如何运行测试

### 单元测试

```bash
# 运行所有单元测试
python -m pytest

# 运行特定测试文件
python -m pytest test/test_file.py

# 运行测试并收集覆盖率
python -m pytest --cov=src --cov-report=html
```

### 配置系统测试

```bash
# 运行所有配置系统测试
python -m tests.config_test.run_config_tests

# 运行特定配置测试类
python -m tests.config_test.run_config_tests --test TestConfigLifecycle

# 运行测试并生成报告
python -m tests.config_test.run_config_tests --report
```

### 压力测试

```bash
# 运行所有压力测试
python tests/run_stress_tests.py

# 运行压力测试并指定参数
python tests/run_stress_tests.py --memory-iterations 5 --memory-duration 60 --threads 16
```

### 生成测试报告

```bash
# 生成测试报告
python tests/generate_report.py

# 生成测试报告并指定输出路径
python tests/generate_report.py -o reports/my_report.html

# 在生成报告前运行测试
python tests/generate_report.py --run-tests
```

## 使用便捷脚本

为了简化测试的运行，我们提供了便捷脚本：

### 运行配置系统测试

#### Windows

```batch
# 运行所有配置系统测试
tests\run_config_tests.bat

# 运行特定配置测试类
tests\run_config_tests.bat --test TestHotReload

# 生成测试报告
tests\run_config_tests.bat --report
```

#### Linux/Mac

```bash
# 先确保脚本是可执行的
chmod +x tests/run_config_tests.sh

# 运行所有配置系统测试
./tests/run_config_tests.sh

# 运行特定配置测试类
./tests/run_config_tests.sh --test TestHotReload

# 生成测试报告
./tests/run_config_tests.sh --report
```

### 生成测试报告

#### Windows

在 Windows 上，可以直接双击 `tests/run_report.bat` 文件生成报告，或在命令行中运行：

```batch
tests\run_report.bat
```

#### Linux/Mac

在 Linux 或 Mac 上，可以运行：

```bash
# 先确保脚本是可执行的
chmod +x tests/run_report.sh

# 运行脚本生成报告
./tests/run_report.sh
```

## 测试报告内容

生成的测试报告包含以下内容：

1. **总体概览**: 包括核心功能、可靠性、性能、安全性和可用性的总体评分
2. **图表**: 包括测试失败分布和代码覆盖率图表
3. **单元测试结果**: 显示通过、失败和跳过的测试数量及通过率
4. **配置系统测试结果**: 显示配置管理功能的测试状态和可靠性
5. **压力测试结果**: 包括内存测试和并行处理测试的结果
6. **隐私与合规测试结果**: 显示隐私保护和法律合规性测试的详情
7. **用户体验测试结果**: 显示不同用户场景的测试完成率和状态
8. **代码覆盖率详情**: 显示整体覆盖率和各模块的详细覆盖率

## 依赖项

测试框架需要以下依赖项：

- pytest: 运行单元测试
- pytest-cov: 收集代码覆盖率数据
- matplotlib: 生成图表
- coverage: 处理代码覆盖率
- watchdog: 用于热重载测试

可以使用以下命令安装依赖：

```bash
pip install pytest pytest-cov matplotlib coverage watchdog
``` 