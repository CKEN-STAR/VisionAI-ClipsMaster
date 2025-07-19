# 跨环境验证套件

VisionAI-ClipsMaster 项目跨环境验证套件用于确保关键配置参数、质量门限和功能行为在不同环境（开发、测试、生产）中保持一致和合理。

## 主要功能

该验证套件提供以下功能：

1. **质量门限一致性验证**：确保关键质量门限（如代码覆盖率、性能指标）在所有环境中保持一致。
2. **资源限制合理性检查**：确保生产环境的资源配置（内存、CPU）足够支撑应用运行。
3. **功能标志一致性检查**：确保关键功能在所有环境中具有一致的启用状态。
4. **安全设置验证**：验证所有环境中的安全配置是否合理，特别是生产环境是否具有足够的安全级别。
5. **模型配置一致性检查**：验证AI模型配置在不同环境中是否一致。
6. **日志配置检查**：确保日志级别和存储位置在不同环境中合理配置。

## 使用方法

### 命令行运行

使用以下命令运行环境验证：

```bash
# 使用默认环境（dev,staging,prod）运行验证
python tests/quality_gate/env_validator.py

# 验证指定环境集
python tests/quality_gate/env_validator.py --environments dev,prod

# 生成详细报告并指定输出文件
python tests/quality_gate/env_validator.py --report reports/env_validation_report.json

# 显示详细日志
python tests/quality_gate/env_validator.py --verbose
```

### 集成到CI/CD流程

建议在部署前的CI/CD流程中加入环境验证步骤，可以添加到GitHub Actions工作流中：

```yaml
- name: 运行环境验证
  run: python tests/quality_gate/env_validator.py --report env_validation_report.json
  continue-on-error: true

- name: 检查环境验证结果
  run: |
    CRITICAL_FAILURES=$(cat env_validation_report.json | jq '.summary.critical_failures')
    if [ $CRITICAL_FAILURES -gt 0 ]; then
      echo "环境验证发现严重问题，请修复后重试"
      exit 1
    fi
```

### 在代码中使用

```python
from tests.quality_gate.env_validator import EnvironmentValidator

# 创建验证器
validator = EnvironmentValidator(["dev", "staging", "prod"])

# 执行所有验证测试
passed = validator.validate_all()

# 获取结果
if passed:
    print("所有环境配置一致性检查通过")
else:
    critical_failures = [r for r in validator.validation_results 
                      if r["level"] == "critical" and not r["passed"]]
    print(f"发现 {len(critical_failures)} 个严重问题:")
    for failure in critical_failures:
        print(f"- {failure['check_name']}: {failure['details']}")
```

## 测试和演示

使用以下命令测试和演示环境验证套件：

```bash
# 运行完整演示
python tests/test_env_validation.py

# 运行特定测试
python tests/test_env_validation.py --test basic
python tests/test_env_validation.py --test gate
python tests/test_env_validation.py --test inconsistency
python tests/test_env_validation.py --test report
```

## 配置文件

环境配置文件位于 `configs/environments/<环境名>/config.json`，每个环境至少应包含以下配置项：

```json
{
  "name": "环境名称",
  "description": "环境描述",
  "unit_test": {
    "coverage": 90,
    "pass_rate": 100
  },
  "performance": {
    "response_time": 8000,
    "memory_usage": 4096
  },
  "compliance": {
    "privacy": 98,
    "legal": 100
  }
}
```

## 验证报告

验证报告以JSON格式存储在 `tests/results/env_validation/` 目录中，包含以下信息：

- 总体验证摘要（通过项数、失败项数、成功率）
- 每项检查的详细结果（通过/失败、严重程度、详细信息）
- 受影响的环境列表

## 最佳实践

1. **保持关键质量门限一致**：所有环境应使用相同的关键质量门限，例如代码覆盖率、性能指标等。
2. **逐步提高安全级别**：从开发环境到生产环境，安全设置应逐步收紧，而不是放松。
3. **避免在生产环境启用实验性功能**：实验性功能应在开发和测试环境中验证后，才考虑在生产环境启用。
4. **统一模型配置**：确保AI模型在所有环境中使用相同的版本和量化级别，以避免行为差异。
5. **日志级别区分**：开发环境可使用详细日志（DEBUG），而生产环境应使用较高级别（INFO/WARNING）以提高性能。

## 排查问题

如果验证失败，请检查：

1. 配置文件是否存在：确保 `configs/environments/<环境名>/config.json` 文件存在且格式正确。
2. 配置项差异：检查报告中指出的不一致配置项，评估是否需要统一。
3. 安全设置：确保生产环境的安全级别不低于其他环境。
4. 功能标志：确保关键功能在所有环境中状态一致，且生产环境未启用实验性功能。 