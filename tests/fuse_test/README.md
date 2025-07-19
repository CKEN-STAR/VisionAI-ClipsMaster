# 熔断演练测试框架

这个测试框架用于验证VisionAI-ClipsMaster项目的内存熔断机制在各种场景下的有效性和可靠性。

## 系统组件

- **内存压力模拟器** (`memory_simulator.py`): 模拟不同级别的内存压力，支持线性增长、指数增长、步进式和尖峰式内存分配
- **熔断演练测试类** (`drill_test.py`): 自动化测试各种熔断场景，包括单级熔断、多级升级和恢复稳定性
- **测试运行器** (`run_tests.py`): 执行测试套件并生成详细报告
- **演练执行器** (`run_drill.py`): 手动执行特定熔断演练，用于系统演示和验证

## 主要测试场景

1. **单级熔断有效性测试** - 验证不同级别的熔断是否正确触发和执行相应操作
   - 警告级别熔断测试 (`test_warning_scenario`)
   - 临界级别熔断测试 (`test_critical_scenario`)
   - 紧急级别熔断测试 (`test_emergency_scenario`)

2. **多级熔断升级流程测试** - 验证熔断如何从低级别逐步升级到高级别 (`test_escalation_scenario`)

3. **恢复过程稳定性测试** - 验证系统恢复后是否稳定，以及多次恢复的一致性 (`test_recovery_stability`)

4. **手动触发熔断测试** - 验证手动触发熔断的功能 (`test_manual_fuse_trigger`)

## 使用方法

### 运行所有测试

```bash
python -m tests.fuse_test.run_tests
```

### 运行特定测试

```bash
python -m tests.fuse_test.run_tests --test test_emergency_scenario
```

### 执行熔断演练

警告级别演练:
```bash
python -m tests.fuse_test.run_drill warning
```

临界级别演练:
```bash
python -m tests.fuse_test.run_drill critical
```

紧急级别演练:
```bash
python -m tests.fuse_test.run_drill emergency
```

熔断升级演练:
```bash
python -m tests.fuse_test.run_drill escalation
```

手动触发演练:
```bash
python -m tests.fuse_test.run_drill manual --level EMERGENCY
```

## 测试报告

测试报告默认保存在 `test_reports` 目录中，可以通过 `--output` 参数指定其他输出目录:

```bash
python -m tests.fuse_test.run_tests --output my_reports
```

## 注意事项

1. 确保系统中已正确配置熔断相关组件（熔断管理器、压力检测器、效果验证器等）
2. 测试会模拟高内存压力，请确保系统有足够的内存空间
3. 紧急级别测试可能导致进程重启，请保存重要工作后再运行

## 扩展

如需添加新的测试场景，请在 `drill_test.py` 中添加新的测试方法，并确保方法名以 `test_` 开头。

如需自定义内存压力模式，可以修改 `memory_simulator.py` 中的 `MemoryPressureSimulator` 类。 