# 硬件故障与软件异常模拟测试框架

本模块用于模拟各种硬件故障和软件异常场景，测试VisionAI-ClipsMaster系统在面对异常情况时的稳定性和恢复能力。

## 功能概述

### 硬件故障模拟
- **GPU故障模拟**：模拟GPU完全不可用、间歇性故障和性能降级
- **磁盘空间问题模拟**：模拟磁盘空间耗尽、间歇性磁盘空间不足和I/O性能降级

### 软件异常模拟
- **进程崩溃模拟**：模拟段错误、未处理异常等导致的崩溃场景
- **资源问题模拟**：模拟内存泄漏、CPU使用率过高等资源问题
- **死锁模拟**：模拟线程死锁导致的程序挂起
- **文件损坏模拟**：模拟配置文件或数据文件的损坏场景

### 数据完整性攻击测试
- **模型文件损坏测试**：模拟模型文件被损坏的场景，测试系统的检测和恢复能力
- **配置文件损坏测试**：模拟配置文件损坏情况，测试系统的自动修复和恢复机制
- **JSON文件字段损坏测试**：模拟配置JSON中关键字段被修改或损坏的场景

### 级联故障测试
- **多重故障组合测试**：模拟多种故障连续或同时发生，测试系统的恢复能力
- **自动恢复验证**：验证系统在一系列故障后能否自动恢复到正常状态
- **存活率计算**：计算系统在复合故障环境下的存活率指标

### 状态快照与回滚（新增）
- **系统状态保存**：保存系统关键状态以便在故障后恢复
- **配置快照**：保存配置文件状态，支持多版本备份和恢复
- **进程状态保存**：在可用时使用CRIU保存完整进程状态（Linux平台）
- **跨平台兼容**：在不同平台上提供适当级别的状态保存和恢复能力

## 日志驱动恢复 (Log-Driven Recovery)

日志驱动恢复是一种自动化故障恢复机制，通过分析系统日志文件来识别错误模式和问题原因，并自动执行相应的恢复操作。这一机制具有以下特点：

### 功能特性

- **高效日志分析**：针对大型日志文件进行优化，能够在3秒内分析1GB大小的日志
- **错误模式识别**：支持多种错误类型的识别，包括内存问题、GPU错误、磁盘空间不足、模型损坏等
- **自动恢复操作**：根据识别的错误自动执行恢复操作，如降低量化级别、清理缓存、恢复备份等
- **跨平台支持**：适用于Windows、Linux和macOS平台
- **交互式和命令行界面**：提供友好的交互式和命令行界面进行测试和使用

### 错误类型和恢复操作

日志驱动恢复系统支持以下错误类型和对应的恢复操作：

| 错误类型 | 说明 | 恢复操作 |
| --- | --- | --- |
| OutOfMemory | 内存不足错误 | 降低量化级别、清理缓存、释放GPU内存 |
| GPUError | GPU相关错误 | 释放GPU内存、降低量化级别 |
| DiskSpace | 磁盘空间不足 | 清理缓存 |
| ModelCorruption | 模型文件损坏 | 从备份恢复 |
| ConfigError | 配置错误 | 从备份恢复 |
| ProcessCrash | 进程崩溃 | 重启服务 |
| Deadlock | 死锁 | 清理死锁、重启服务 |
| PermissionDenied | 权限问题 | 修复权限 |

### 使用方法

```bash
# 基本用法
python run_log_recovery_test.py analyze <log_file>  # 分析日志文件
python run_log_recovery_test.py recover <log_file>  # 执行恢复操作

# 生成测试日志
python run_log_recovery_test.py genlog --size 1000  # 生成1GB测试日志

# 性能测试
python run_log_recovery_test.py perf --size 1000  # 测试1GB日志分析性能

# 交互模式
python run_log_recovery_test.py --interactive

# 运行单元测试
python run_log_recovery_test.py test
```

### 技术实现

日志驱动恢复系统的关键技术实现包括：

1. **内存映射优化**：对于大型日志文件，使用内存映射（mmap）技术提高分析效率
2. **正则表达式模式匹配**：使用正则表达式高效匹配错误模式
3. **上下文提取**：从日志中提取上下文信息，包括文件路径、行号和函数名
4. **堆栈跟踪分析**：分析异常堆栈跟踪信息，精确定位错误来源
5. **并发处理**：支持多线程分析以提高大型日志的处理速度

### 性能指标

- **分析速度**：3秒内完成1GB日志文件的分析
- **内存占用**：处理1GB日志文件时内存峰值不超过200MB
- **准确率**：错误识别准确率>95%

## 使用方法

### 硬件故障测试

运行完整的硬件故障测试套件：

```bash
python run_failure_test.py --test-type all --duration 15
```

仅测试GPU故障：

```bash
python run_failure_test.py --test-type gpu --duration 10
```

仅测试磁盘问题：

```bash
python run_failure_test.py --test-type disk --duration 10 --target /path/to/test
```

### 软件异常测试

运行完整的软件异常测试：

```bash
python run_software_failure_test.py --test-type all
```

特定测试：

```bash
python run_software_failure_test.py --test-type memory_leak --severity high
```

### 级联故障测试

运行基本级联故障测试：

```bash
python run_cascade_failure_test.py --scenario basic
```

自定义级联故障测试：

```bash
python run_cascade_failure_test.py --custom-scenario path/to/scenario.json
```

### 状态快照与回滚（新增）

创建系统状态快照：

```bash
python run_state_recovery_test.py snapshot --name "我的快照" --type full
```

从快照恢复系统状态：

```bash
python run_state_recovery_test.py restore 1679852361 --type full
```

列出所有可用快照：

```bash
python run_state_recovery_test.py list --verbose
```

进入交互模式：

```bash
python run_state_recovery_test.py --interactive
```

## 快照功能详解

### 快照类型

- **full**: 完整快照，包含进程状态和配置文件
- **config**: 仅保存配置文件状态
- **process**: 仅保存进程状态（仅Linux下使用CRIU时完整支持）

### 平台支持

- **Linux**: 完整支持（通过CRIU可保存和恢复完整进程状态）
- **Windows/macOS**: 部分支持（配置文件完整支持，进程状态仅支持信息记录）

### 主要命令

| 命令 | 描述 | 示例 |
|------|------|------|
| snapshot | 创建系统状态快照 | `--pid 1234 --name "测试快照"` |
| restore | 从快照恢复系统 | `1234567890 --type config` |
| list | 列出所有可用快照 | `--verbose` |
| show | 显示快照详情 | `1234567890` |
| delete | 删除指定快照 | `1234567890 --force` |
| test | 运行快照测试 | `--iterations 5` |

### 配置文件备份

快照功能可以备份和恢复以下类型的配置：

- 模型配置文件（*.yaml, *.json）
- 系统设置文件
- 用户自定义配置

## 开发指南

### 添加新的故障类型

1. 在对应的故障模拟模块中添加新的故障类型
2. 实现故障模拟逻辑
3. 添加故障注入和恢复逻辑
4. 更新测试套件以包含新故障类型

### 增强故障测试覆盖率

- 添加更多组合故障场景
- 设计更细粒度的故障级别
- 实现更复杂的恢复策略测试

### 添加新的快照功能

1. 在`state_snapshot.py`中扩展`StateRecovery`类
2. 添加新的状态保存和恢复方法
3. 在`run_state_recovery_test.py`中添加相应的命令行参数和处理逻辑

## 命令行参数

### 硬件故障测试参数
- `--test-type`：测试类型，可选值为 "gpu"、"disk" 或 "all"（默认）
- `--duration`：每项测试的持续时间（秒），默认为15秒
- `--target`：磁盘测试的目标目录（可选）
- `--output-dir`：测试结果输出目录（可选）

### 软件异常测试参数
- `--test-type`：测试类型，可选值为 "exception"、"crash"、"file" 或 "all"（默认）
- `--duration`：每项测试的持续时间（秒），默认为15秒
- `--target`：文件测试的目标目录（可选）
- `--output-dir`：测试结果输出目录（可选）
- `--isolation`：是否在隔离环境中运行测试（默认为true）
- `--include-crash`：是否包含崩溃测试（谨慎使用）

### 数据完整性测试参数
- `--test-type`：测试类型，可选值为 "model"、"config"、"json" 或 "all"（默认）
- `--target`：目标文件路径，用于测试特定文件
- `--output-dir`：测试结果输出目录（可选）

### 级联故障测试参数（新增）
- `--scenario`：测试场景，可选值为 "basic"、"random"、"intense"、"long" 或 "custom"
- `--config-file`：自定义测试配置JSON文件路径（与 --scenario=custom 一起使用）
- `--repeat`：测试重复次数（覆盖默认配置）
- `--interval`：故障间隔时间(秒)（覆盖默认配置）
- `--recovery-interval`：恢复间隔时间(秒)（覆盖默认配置）
- `--random-order`：随机故障顺序（覆盖默认配置）
- `--output-dir`：测试结果输出目录（默认: tests/failure_test/logs）
- `--verbose`：启用详细日志输出
- `--quick-test`：运行快速级联故障测试（忽略其他参数）

## 模拟故障类型

### 硬件故障

#### GPU故障
1. **完全故障 (complete)**：GPU完全不可用
2. **间歇性故障 (intermittent)**：GPU周期性可用/不可用
3. **性能降级 (degraded)**：GPU内存限制或计算能力降低

#### 磁盘故障
1. **空间耗尽 (complete)**：填充指定目录直至磁盘空间接近耗尽
2. **间歇性空间问题 (intermittent)**：周期性创建/删除大文件
3. **I/O性能降级 (degraded)**：通过频繁读写或调整I/O优先级降低磁盘性能

### 软件异常

#### 进程崩溃
1. **段错误 (segfault)**：通过访问无效内存触发SIGSEGV信号
2. **未处理异常 (exception)**：抛出未捕获的异常导致程序崩溃

#### 资源问题
1. **内存泄漏 (memory_leak)**：持续分配内存而不释放
2. **CPU过载 (cpu_load)**：创建计算密集型任务占用CPU资源

#### 线程问题
1. **死锁 (deadlock)**：创建两个线程互相等待对方持有的锁

#### 文件问题
1. **文件损坏 (file_corruption)**：修改文件部分内容导致损坏

### 数据完整性攻击

#### 模型文件损坏
1. **随机损坏 (random)**：随机位置修改模型文件内容
2. **头部损坏 (header)**：损坏模型文件头部
3. **中间损坏 (middle)**：损坏模型文件中间部分
4. **尾部损坏 (footer)**：损坏模型文件尾部

#### 配置文件损坏
1. **二进制损坏**：直接修改配置文件的二进制内容
2. **JSON字段损坏**：修改JSON配置中的特定字段

### 级联故障组合（新增）

#### 基础级联故障
1. **GPU故障 → 内存溢出 → 磁盘IO错误**：测试系统在连续故障环境下的恢复能力

#### 随机顺序级联故障
1. **随机排序的多种故障**：在无法预测的顺序下触发多种故障

#### 高强度级联故障
1. **高强度多轮循环短间隔**：在短时间内多次触发高强度故障

#### 长时间级联故障
1. **低强度长持续时间**：模拟长时间的低强度故障场景

## 开发者接口

### 硬件故障模拟

```python
from hardware_failure import HardwareFailureSimulator, FailureConfig

# 创建故障配置
config = FailureConfig(
    failure_type="gpu",
    failure_mode="complete",
    duration=30,
    severity="medium"
)

# 初始化模拟器
simulator = HardwareFailureSimulator()
simulator.initialize()

# 模拟故障
result = simulator.simulate_gpu_failure(config)

# 等待故障持续
time.sleep(30)

# 手动恢复故障（如果需要）
# simulator.recover_failure(result["failure_id"])
```

### 软件异常模拟

```python
from software_failure import SoftwareFailureSimulator, ExceptionConfig

# 创建异常配置
config = ExceptionConfig(
    exception_type="memory_leak",
    duration=30,
    severity="medium",
    isolation=False
)

# 初始化模拟器
simulator = SoftwareFailureSimulator()
simulator.initialize()

# 模拟异常
result = simulator.simulate_exception(config)

# 等待异常持续
time.sleep(30)

# 手动恢复（如果需要）
# simulator.recover_simulation(result["simulation_id"])
```

### 数据完整性测试

```python
from data_corruption import DataCorruptionTester

# 初始化测试器
tester = DataCorruptionTester()

# 损坏模型文件并测试恢复
model_path = "models/zh/active.bin"
original_hash, corrupted_hash = tester.corrupt_model_file(model_path, corruption_type="random")
recovery_success = tester.test_model_recovery(model_path, "zh")

# 损坏JSON配置文件
config_path = "config/model_config.json"
original_hash, corrupted_fields = tester.corrupt_json_file(config_path)
recovery_success = tester.test_config_recovery(config_path)

# 运行完整测试套件
results = tester.run_all_tests()
```

### 级联故障测试（新增）

```python
from cascade_failure import CascadeFailureTester, CascadeFailureConfig

# 初始化测试器
tester = CascadeFailureTester()
tester.initialize()

# 创建级联故障配置
config = CascadeFailureConfig(
    failure_sequence=[
        {"type": "gpu", "mode": "complete", "duration": 15, "severity": "medium"},
        {"type": "memory", "duration": 15, "severity": "medium"},
        {"type": "io_error", "severity": "medium"}
    ],
    interval_between_failures=5.0,
    recovery_interval=10.0,
    auto_recovery=True,
    verify_after_recovery=True,
    repeat_count=1
)

# 执行测试
result = tester.run_test(config)

# 验证系统存活率
print(f"系统存活率: {result['success_rate']:.2f}%")
```

## 系统要求

- Python 3.7+
- 可选依赖：
  - psutil (用于系统指标收集)
  - torch (用于GPU状态检测)

## 注意事项

1. 某些故障模拟可能需要管理员/root权限
2. 磁盘空间测试可能会临时占用大量磁盘空间
3. 崩溃测试可能导致测试进程终止，请在隔离环境中运行
4. 不建议在生产环境中运行故障测试
5. 数据完整性测试会创建文件备份，确保有足够的磁盘空间
6. 级联故障测试可能会对系统造成较大压力，确保在测试环境中运行

## 测试报告格式

测试结果将以JSON格式保存在指定的输出目录中，包含以下信息：

- 测试时间和持续时间
- 故障/异常配置参数
- 系统状态指标（故障前、故障中、恢复后）
- 故障影响评估
- 恢复状态和结果 