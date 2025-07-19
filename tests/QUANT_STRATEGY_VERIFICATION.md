# 量化策略验证套件

## 概述

量化策略验证套件是为VisionAI-ClipsMaster项目开发的测试工具，用于验证量化决策引擎在不同内存条件下的正确性。该套件确保系统能够基于可用内存自动选择合适的量化级别，从而在保证应用性能的同时优化模型加载和推理过程。

## 主要功能

1. **策略映射验证**：测试指定内存值是否映射到正确的量化级别
2. **降级链验证**：确保量化降级链按照质量从高到低正确排序
3. **内存估计验证**：测试不同量化级别的内存使用量估计是否准确
4. **内存适配验证**：测试系统是否能正确判断模型是否能装入特定内存
5. **集成策略验证**：在不同硬件配置场景下测试决策策略的一致性
6. **多语言模型验证**：测试针对中文和英文模型的量化决策差异

## 目标映射关系

量化策略验证主要针对以下内存值到量化级别的映射关系进行验证：

| 可用内存 (MB) | 量化级别 | 描述 |
|--------------|---------|------|
| 4000        | Q5_K    | 充足内存，使用更高质量的量化 |
| 2500        | Q4_K_M  | 中等内存，使用中等质量量化 |
| 800         | Q2_K    | 极低内存，使用最低质量量化 |
| 3000        | Q4_K_M  | 中低内存，使用中等质量量化 |

## 内存适配测试

内存适配测试验证以下情况：

| 可用内存 (GB) | 量化级别 | 预期结果 | 描述 |
|--------------|---------|---------|------|
| 2            | Q2_K    | 能装入  | 2GB内存足够装载Q2_K (约2.1GB) |
| 2            | Q4_K    | 不能装入 | 2GB内存不足以装载Q4_K (约4.2GB) |
| 4            | Q4_K    | 不能装入 | 4GB内存勉强不足以装载Q4_K (需要考虑安全边界) |
| 5            | Q4_K    | 能装入  | 5GB内存足够装载Q4_K |
| 8            | Q8_0    | 能装入  | 8GB内存足够装载Q8_0 (约8.4GB) |

## 使用方法

### 独立测试版本

独立测试版本不依赖完整的代码库，可以单独运行：

```bash
# 运行独立测试版本
python tests/run_quant_strategy_standalone.py

# 运行并生成详细日志
python tests/run_quant_strategy_standalone.py -v

# 运行并生成测试报告
python tests/run_quant_strategy_standalone.py -r

# 运行特定测试方法
python tests/run_quant_strategy_standalone.py -t test_quant_strategy_mapping
```

### 集成测试版本

集成测试版本依赖项目完整代码库，需在项目环境中运行：

```bash
# Windows
tests\run_quant_strategy_tests.bat

# Unix/Linux
./tests/run_quant_strategy_tests.sh
```

## 项目文件结构

- `tests/test_quant_strategy_verification.py` - 集成测试版本
- `tests/quant_strategy_standalone_test.py` - 独立测试版本
- `tests/run_quant_strategy_tests.py` - 集成测试运行脚本
- `tests/run_quant_strategy_standalone.py` - 独立测试运行脚本
- `tests/run_quant_strategy_tests.bat` - Windows批处理运行脚本
- `tests/run_quant_strategy_tests.sh` - Unix/Linux Shell运行脚本
- `tests/reports/` - 测试报告保存目录

## 开发注意事项

1. 进行测试开发时，请确保测试用例与参考映射关系一致
2. 在实际应用中，量化决策算法的阈值可能需要根据实际硬件环境进行调整
3. 测试时使用的模型大小为7B参数，如有不同规模的模型，内存使用估计应相应调整

## 持续集成

该测试套件可集成到CI/CD流程中，以确保量化决策引擎的更改不会破坏预期的内存适配行为。建议在发布前运行完整的测试套件。 