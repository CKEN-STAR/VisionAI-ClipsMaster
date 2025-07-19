# VisionAI-ClipsMaster 恢复时效性测试

本文档介绍了VisionAI-ClipsMaster系统的恢复时效性测试框架，该框架用于验证系统从各种故障中恢复的速度是否符合服务水平协议(SLA)要求。

## 测试目的

恢复时效性测试的主要目标是确保系统能够在规定的时间内从关键故障中恢复，维持系统的可用性和可靠性。这些测试模拟实际生产环境中可能出现的各种故障情况，并测量系统恢复到正常运行状态所需的时间。

## SLA要求

根据项目需求，系统恢复时间必须满足以下SLA要求：

| 故障类型 | 描述 | 最大恢复时间 |
|---------|------|------------|
| GPU丢失 | GPU资源暂时不可用或崩溃 | ≤5秒 |
| 内存溢出(OOM) | 系统内存不足导致的崩溃 | ≤3秒 |
| 模型损坏 | 模型文件损坏或不完整 | ≤30秒 |

## 测试内容

恢复时效性测试框架包含以下测试：

1. **GPU故障恢复测试**：模拟GPU设备丢失或故障，测试系统是否能在5秒内恢复正常运行
2. **内存溢出恢复测试**：触发内存溢出异常，测试系统是否能在3秒内释放资源并恢复运行
3. **模型损坏恢复测试**：故意损坏模型文件，测试系统是否能在30秒内检测并修复或回退到备用模型

## 测试实现

测试框架通过以下方式实现故障注入和恢复测试：

- 通过硬件故障模拟器(`HardwareFailureSimulator`)模拟GPU故障
- 通过软件故障模拟器(`SoftwareFailureSimulator`)模拟内存溢出情况
- 通过文件操作模拟模型文件损坏
- 使用精确的计时器测量恢复时间
- 通过pytest参数化测试不同的故障类型

## 运行测试

### 前提条件

在运行测试前，请确保：

1. 已完成VisionAI-ClipsMaster的基本安装
2. 已安装测试所需的依赖：`pytest`, `psutil`
3. 系统具有适当的权限操作文件和资源

### 运行方法

1. **使用测试运行器（推荐）**：

   ```bash
   python tests/failure_test/run_recovery_timing_test.py
   ```

   运行器支持以下参数：
   
   - `--failure-type`/`-f`: 指定要测试的故障类型（`gpu_loss`, `oom`, `model_corrupt`, `all`）
   - `--report`/`-r`: 生成HTML测试报告
   - `--output-dir`/`-o`: 指定报告输出目录
   - `--repeat`: 每个测试重复次数
   - `--verbose`/`-v`: 显示详细日志

2. **使用pytest直接运行**：

   ```bash
   python -m pytest tests/failure_test/recovery_timing.py -v
   ```

3. **测试指定故障类型**：

   ```bash
   python tests/failure_test/run_recovery_timing_test.py -f gpu_loss
   ```

### 示例

1. 运行所有故障类型的测试并生成报告：

   ```bash
   python tests/failure_test/run_recovery_timing_test.py --report
   ```

2. 重复测试OOM恢复3次：

   ```bash
   python tests/failure_test/run_recovery_timing_test.py -f oom --repeat 3
   ```

## 测试报告

当使用`--report`选项时，测试运行器将生成一份HTML报告，包含：

- 测试环境信息
- 测试结果摘要
- 各故障类型的SLA要求和实际恢复时间
- 通过/失败状态
- 恢复时间与SLA对比图表
- 每次测试的详细结果

报告默认保存在项目根目录的`reports`文件夹中。

## 故障排除

### 常见问题

1. **测试超时**：如果测试长时间未完成，可能是系统未能正确恢复。检查日志以获取详细信息。

2. **硬件模拟器初始化失败**：确保系统具有足够的权限访问和控制硬件资源。

3. **测试失败但无明显错误**：增加测试的详细级别：

   ```bash
   python tests/failure_test/run_recovery_timing_test.py -v
   ```

### 日志

详细日志会输出到控制台，可以通过`-v`选项增加详细级别。运行测试时的所有异常和错误也会被记录。

## 扩展测试

如需添加新的故障类型测试，请遵循以下步骤：

1. 在`RECOVERY_SLA`字典中添加新的故障类型及其SLA要求
2. 在`RecoveryTester.inject_failure`方法中实现该故障类型的注入逻辑
3. 在`RecoveryTester.wait_for_recovery`方法中实现相应的恢复逻辑
4. 更新测试参数化装饰器以包含新的故障类型

## 注意事项

- 恢复时效性测试可能会暂时影响系统性能或稳定性，建议在非生产环境中运行
- 测试过程中可能会修改或创建临时文件，测试结束后会自动清理这些资源
- GPU故障测试需要系统具有GPU设备，否则测试将被跳过 