# VisionAI-ClipsMaster 自动化门禁系统

本模块实现了 VisionAI-ClipsMaster 项目的自动化门禁系统，用于在代码合并前通过自动化检查确保质量标准得到满足。

## 系统概述

自动化门禁系统是一种在CI/CD流程中执行的质量控制机制，负责在代码集成前进行一系列检查，包括单元测试、性能测试、许可证合规性检查等。任何不符合要求的代码变更都会被阻止合并，从而确保主分支的代码质量和稳定性。

## 文件结构

```
tests/quality_gate/
├── __init__.py             # 包初始化文件
├── quality_model.py        # 质量模型和评分系统
├── run_quality_check.py    # 质量门限检查运行器
└── README.md               # 本文档

.github/
├── quality_gate_config.json   # 质量门限配置文件
├── workflows/
    ├── quality_gate.yml       # 质量门限GitHub Actions工作流
    └── branch_protection.yml  # 分支保护工作流
```

## 组件说明

### 1. 质量模型 (quality_model.py)

定义了项目的质量标准，包括各项指标的阈值和权重。主要指标包括：

- **单元测试**: 代码覆盖率(最低90%)、通过率(必须100%)
- **性能**: 响应时间(最大8000ms)、内存使用(最大4096MB)
- **压力测试**: 成功率(最低95%)、恢复能力(最低90%)
- **用户体验**: 旅程完成率(最低90%)、响应满意度(最低85%)
- **合规性**: 隐私保护(最低98%)、法律合规(必须100%)、许可证合规

### 2. 质量检查运行器 (run_quality_check.py)

负责执行质量门限检查的主要脚本，功能包括：

- 收集测试结果数据
- 根据质量模型评估测试结果
- 生成质量报告（JSON和HTML格式）
- 在CI环境中设置通过/失败状态

### 3. 配置系统 (quality_gate_config.json)

集中管理质量门限的配置文件，允许灵活调整：

- 各项指标的阈值和严重程度
- 允许的许可证列表
- 报告格式和输出目录
- CI集成行为

### 4. GitHub Actions 工作流

两个主要工作流：

- **质量门限工作流 (quality_gate.yml)**: 运行完整的质量检查流程
- **分支保护工作流 (branch_protection.yml)**: 阻止不符合质量要求的代码合并

## 使用方法

### 本地运行质量检查

开发者可以在提交代码前在本地运行质量检查：

```bash
# 基本用法
python -m tests.quality_gate.run_quality_check

# 生成HTML报告
python -m tests.quality_gate.run_quality_check --html-report

# 使用指定的测试结果文件
python -m tests.quality_gate.run_quality_check --result-file path/to/results.json

# 指定输出目录
python -m tests.quality_gate.run_quality_check --output-dir reports/my-quality-report
```

### 许可证合规检查

单独运行许可证合规检查：

```bash
python tests/check_license_compliance.py --output licenses_results.json
```

### 性能基准测试

单独运行性能基准测试：

```bash
python tests/run_performance_benchmark.py --output benchmark_results.json
```

## 阻断规则

以下情况会触发质量门限阻断：

1. 单元测试覆盖率低于90%
2. 单元测试未100%通过
3. 性能指标超出阈值（响应时间>8秒，内存使用>4GB）
4. 使用了不符合要求的开源许可证

## 配置门限阈值

项目管理员可以通过修改`.github/quality_gate_config.json`文件来调整质量门限：

```json
{
  "thresholds": {
    "code_coverage": {
      "min": 90,
      "severity": "error"
    },
    "performance": {
      "response_time_ms": {
        "max": 8000,
        "severity": "error"
      }
    }
  }
}
```

## 集成到持续集成

质量门限系统已集成到项目的GitHub Actions CI/CD流程中：

1. 对主分支和开发分支的所有PR自动运行质量检查
2. 检查结果会以评论形式添加到PR中
3. 检查失败会阻止PR合并

## 报告格式

系统生成两种格式的报告：

1. **JSON报告** - 包含详细的质量检查数据
2. **HTML报告** - 提供直观的质量指标可视化展示

报告存储在`reports/quality/`目录下。 