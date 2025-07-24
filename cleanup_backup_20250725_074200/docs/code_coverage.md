# 代码覆盖率强制检查

本文档描述了VisionAI-ClipsMaster项目的代码覆盖率强制检查机制，包括配置、运行和解释结果。

## 覆盖率要求

项目对不同类型的模块设置了不同的覆盖率要求标准：

| 模块类型 | 最低覆盖率要求 | 说明 |
|---------|--------------|------|
| 核心模块 (core/, utils/) | ≥95% | 这些模块包含项目的核心功能，需要严格的测试覆盖 |
| 辅助模块 (api/, exporters/) | ≥80% | 这些模块通常是对核心功能的封装或扩展 |
| 其他模块 | ≥70% | 默认覆盖率要求 |

## 运行覆盖率检查

### 使用脚本运行

我们提供了运行覆盖率检查的脚本，支持Windows和Linux/Mac系统：

#### Windows

```batch
scripts\run_coverage_check.bat [--strict]
```

#### Linux/Mac

```bash
./scripts/run_coverage_check.sh [--strict]
```

### 参数说明

- `--strict`: 严格模式，如果覆盖率未达标则脚本返回非零退出码（适用于CI/CD环境）
- `--test-dirs=<目录>`: 指定测试目录，默认为`tests/unit_test`
- `--output-dir=<目录>`: 指定报告输出目录，默认为`coverage_reports`

### 手动运行

也可以直接使用pytest运行覆盖率检查：

```bash
python -m pytest tests/unit_test --cov=src --cov-report=html:coverage_reports/html
```

> **注意**: 如果遇到命令行参数冲突问题，可尝试禁用默认的pytest配置文件：
> ```bash
> python -m pytest tests/unit_test -c NUL --cov=src --cov-report=html:coverage_reports/html
> ```
> Windows系统使用`NUL`，Linux/Mac系统使用`/dev/null`。

## 覆盖率报告

运行覆盖率检查后，将生成以下报告：

1. **终端报告**：直接在命令行中显示各模块的覆盖率和通过/失败状态
2. **HTML报告**：生成在`coverage_reports/html/`目录下，提供详细的文件级和行级覆盖率信息
3. **XML报告**：生成在`coverage_reports/coverage.xml`，用于CI/CD系统集成
4. **覆盖率徽章**：生成在`coverage_reports/coverage_badge.json`，可以集成到项目文档中

## CI/CD集成

在CI/CD环境中，可以使用严格模式确保代码覆盖率符合要求：

```yaml
# 示例 GitHub Actions 配置
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements_test.txt
      - name: Run coverage check
        run: ./scripts/run_coverage_check.sh --strict
```

## 提高覆盖率的策略

如果某些模块覆盖率不达标，可以采取以下策略：

1. **增加单元测试**：针对未被测试的函数或分支编写新的测试用例
2. **使用参数化测试**：使用`@pytest.mark.parametrize`减少重复测试代码
3. **测试边界条件**：确保覆盖极端情况和错误处理路径
4. **测试模拟**：使用`unittest.mock`或`pytest-mock`模拟外部依赖
5. **使用覆盖率报告**：HTML报告会清晰标记未覆盖的代码行，帮助定位需要测试的代码

## 最佳实践

1. **先编写测试**：采用测试驱动开发(TDD)，先编写测试再实现功能
2. **持续监控覆盖率**：定期运行覆盖率检查，避免覆盖率下降
3. **注重质量而非数字**：覆盖率只是衡量测试完整性的一个指标，更重要的是测试的质量和有效性
4. **排除不需要测试的代码**：某些代码可能不适合测试，可以使用`# pragma: no cover`标记
5. **集成CI/CD**：将覆盖率检查集成到CI/CD流程中，确保每次提交都符合覆盖率要求

## 故障排除

### 常见问题

1. **覆盖率计算不准确**：
   - 确保`.coveragerc`文件配置正确
   - 检查是否有模块被排除在覆盖率统计之外

2. **测试运行失败**：
   - 检查测试环境是否正确设置
   - 确保所有依赖包已安装

3. **HTML报告未生成**：