# 压力测试套件

## 简介

压力测试套件是为VisionAI-ClipsMaster项目开发的一组工具，用于测试和评估系统在各种极端条件下的性能和稳定性。特别关注内存管理，这对于针对4GB RAM/无GPU低资源环境优化的项目至关重要。

主要功能：

1. **内存压力模拟**：模拟各种内存使用模式，如高频分配、内存泄漏、内存峰值和波动场景
2. **内存监控**：实时监控进程和系统内存使用情况
3. **泄漏检测**：检测潜在的内存泄漏和异常使用模式
4. **集成测试**：模拟实际工作流程中的内存使用

## 安装依赖

压力测试套件需要以下依赖：

```bash
pip install numpy psutil matplotlib
```

## 工具组件

### 1. 内存压力模拟器 (MemoryPressureSimulator)

用于模拟各种内存压力场景：

- **恒定速率**：以恒定速率分配内存
- **内存峰值**：模拟突发的大内存分配
- **波浪模式**：模拟内存使用的周期性波动
- **内存泄漏**：模拟逐渐增加的内存泄漏

示例：

```python
from src.monitor.pressure import MemoryPressureSimulator

# 使用上下文管理器应用内存压力
with MemoryPressureSimulator(rate=500, pattern="spike").apply_pressure():
    # 在内存压力下执行代码
    my_function()
```

### 2. 内存监控器 (MemoryMonitor)

用于监控和分析内存使用情况：

- 跟踪进程内存使用
- 监控系统内存使用率
- 检测内存泄漏和峰值
- 生成内存使用统计

示例：

```python
from src.monitor.pressure import start_monitor

# 启动内存监控
monitor = start_monitor()

# 执行操作
some_operation()

# 检查内存情况
leak_detected = monitor.detect_leak()
spikes = monitor.detect_spikes()
max_mem = monitor.get_max_memory()

# 停止监控
monitor.stop()
```

### 3. 测试套件

包含各种内存压力测试：

- **高频内存分配**：测试系统处理高频内存分配的能力
- **内存峰值**：测试系统对内存使用急剧增加的响应
- **内存泄漏**：模拟并检测内存泄漏
- **波动模式**：测试内存使用波动的情况
- **组合压力**：结合多种压力模式的综合测试

## 运行测试

### 单元测试

```bash
# 运行所有压力测试
python tests/monitor_test/stress_test.py

# 运行特定测试
python tests/monitor_test/stress_test.py MemoryPressureTests.test_high_frequency_allocation

# 运行长时间测试
python tests/monitor_test/stress_test.py --long
```

### 使用命令行工具

```bash
# 运行所有压力测试
python tools/run_stress_tests.py all

# 运行特定测试
python tools/run_stress_tests.py test high_frequency_allocation

# 运行5秒的测试
python tools/run_stress_tests.py all --duration 5

# 运行内存基准测试
python tools/run_stress_tests.py benchmark
```

### 集成测试

```bash
# 运行模型加载测试
python tests/monitor_test/integration_test.py --type model

# 运行视频处理测试
python tests/monitor_test/integration_test.py --type video

# 运行组合工作负载测试
python tests/monitor_test/integration_test.py --type combined --duration 60
```

## 内存压力模式说明

1. **恒定模式 (constant)**：以恒定速率分配内存
   - 适用于测试系统在稳定负载下的表现

2. **峰值模式 (spike)**：短时间内分配大量内存，然后释放部分
   - 适用于测试系统对突发内存需求的响应

3. **波动模式 (wave)**：内存使用呈周期性波动
   - 适用于测试系统在动态负载下的稳定性

4. **泄漏模式 (leak)**：内存使用缓慢但持续增长
   - 适用于测试内存泄漏检测和处理机制

## 性能指标

压力测试会收集和报告以下性能指标：

- **峰值内存使用**：测试期间的最大内存使用量
- **内存峰值次数**：内存使用急剧增加的次数
- **内存波动率**：内存使用的波动程度
- **泄漏检测时间**：检测到内存泄漏所需的时间

## 最佳实践

1. **定期运行压力测试**：建议在每次重要更改后和发布前运行压力测试
2. **关注低资源环境**：确保在4GB RAM环境中测试，模拟目标设备
3. **测试实际场景**：使用集成测试模拟真实用户工作流程
4. **监控长时间测试**：进行长时间测试以发现缓慢的内存泄漏
5. **收集基准数据**：定期运行基准测试，追踪性能变化趋势

## 故障排除

### 常见问题

1. **测试失败，OOM错误**
   - 降低压力测试的内存率（rate参数）
   - 检查系统可用内存是否足够

2. **测试报告内存泄漏但代码正常**
   - 调整检测阈值（threshold_percent参数）
   - 检查外部库是否有已知的内存问题

3. **无法启动监控器**
   - 确保已安装psutil库
   - 检查用户权限是否足够

## 后续计划

1. 添加更多特定场景的压力测试
2. 改进内存泄漏检测算法
3. 添加自动化测试报告生成
4. 集成到CI/CD流程 