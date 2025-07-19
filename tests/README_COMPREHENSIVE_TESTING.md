# VisionAI-ClipsMaster 全面测试方案

## 📋 测试概览

本测试方案覆盖VisionAI-ClipsMaster项目的6大关键领域，确保95%以上测试通过率，满足生产环境部署要求。

### 🎯 测试目标

- **总体通过率**: ≥95%
- **P0功能**: 100%通过
- **P1功能**: ≥90%通过  
- **P2功能**: ≥80%通过
- **生产就绪**: 满足4GB RAM无独显设备要求

## 🏗️ 测试架构

### 测试分类 (按优先级)

| 优先级 | 测试类别 | 目标通过率 | 关键指标 |
|--------|----------|------------|----------|
| **P0** | 核心功能测试 | ≥95% | AI剧本重构、双模型切换、训练系统 |
| **P0** | 性能与资源测试 | ≥90% | 内存≤3.8GB、启动≤5s、响应≤2s |
| **P0** | 导出兼容性测试 | ≥95% | 剪映100%兼容、时间轴≤0.2s误差 |
| **P1** | UI界面测试 | ≥85% | 组件完整性、主题切换、内存≤400MB |
| **P1** | 异常处理与恢复测试 | ≥90% | 断点续剪≥95%、8小时稳定性 |
| **P2** | 安全与合规测试 | ≥80% | 水印检测、数据保护、合规性 |

## 🚀 快速开始

### 1. 环境准备

```bash
# 安装测试依赖
pip install -r tests/requirements-test.txt

# 验证环境
python -c "import pytest; print('pytest ready')"
```

### 2. 执行全面测试

```bash
# 运行完整测试套件
python tests/run_comprehensive_tests.py

# 跳过长时间测试 (8小时稳定性测试)
python tests/run_comprehensive_tests.py --skip-slow

# 只运行特定类别
python tests/run_comprehensive_tests.py --category core_functionality
```

### 3. 查看测试报告

测试完成后，详细报告保存在 `tests/reports/` 目录：
- `comprehensive_test_report_YYYYMMDD_HHMMSS.json` - 完整JSON报告
- 控制台输出包含实时进度和摘要

## 📊 测试详情

### 1. 核心功能测试 (P0)

**文件**: `tests/core_functionality/`

**测试内容**:
- ✅ AI剧本重构逻辑验证 (原片→剧情理解→重新编排→爆款字幕)
- ✅ 双语言模型切换 (Mistral-7B英文 + Qwen2.5-7B中文)
- ✅ 字幕-视频精准对齐 (≤0.5秒误差)
- ✅ 投喂训练系统 ("原片-爆款"学习逻辑)

**关键指标**:
- 重构质量: BLEU≥0.75
- 模型切换: ≤1.5秒
- 语言检测: ≥95%准确率
- 训练收敛: >50%/10轮

### 2. 性能与资源测试 (P0)

**文件**: `tests/performance/`

**测试内容**:
- ✅ 4GB内存设备兼容性 (峰值≤3.8GB)
- ✅ 启动时间验证 (≤5秒)
- ✅ UI响应时间 (≤2秒)
- ✅ 8小时长时间稳定性
- ✅ 内存泄漏检测

**关键指标**:
- 内存峰值: ≤3.8GB
- 启动时间: ≤5秒
- UI响应: ≤2秒
- 稳定运行: 8小时

### 3. UI界面测试 (P1)

**文件**: `tests/ui_interface/`

**测试内容**:
- ✅ 所有UI组件加载与交互
- ✅ 中英文界面切换
- ✅ 三主题切换 (light/dark/high-contrast)
- ✅ 进度监控与实时图表
- ✅ 内存使用监控 (≤400MB)

**关键指标**:
- UI内存: ≤400MB
- 主题切换: ≤1秒
- 组件响应: ≤2秒
- 界面完整性: 100%

### 4. 导出兼容性测试 (P0)

**文件**: `tests/export_compatibility/`

**测试内容**:
- ✅ 剪映工程文件生成与导入 (100%兼容)
- ✅ 多独立视频片段时间轴显示
- ✅ 达芬奇Resolve兼容性
- ✅ 多格式输出 (MP4/SRT/JSON)
- ✅ 时间轴精度验证 (≤0.2s误差)

**关键指标**:
- 剪映兼容: 100%
- 时间轴误差: ≤0.2秒
- 导出成功率: ≥98%
- 质量保持: 100%

### 5. 异常处理与恢复测试 (P1)

**文件**: `tests/exception_recovery/`

**测试内容**:
- ✅ 断点续剪功能 (≥95%恢复成功率)
- ✅ 内存不足情况处理
- ✅ 文件损坏恢复
- ✅ 网络中断处理
- ✅ 异常处理成功率 (≥90%)

**关键指标**:
- 断点恢复: ≥95%
- 异常处理: ≥90%
- 恢复时间: ≤30秒
- 稳定性: 8小时

### 6. 安全与合规测试 (P2)

**文件**: `tests/security_compliance/`

**测试内容**:
- ✅ 版权水印检测功能
- ✅ 用户协议绑定验证
- ✅ 数据安全策略测试
- ✅ 敏感信息保护
- ✅ 文件完整性校验

**关键指标**:
- 水印检测: ≥85%准确率
- 数据加密: 100%
- 合规检查: 100%
- 隐私保护: 100%

## 🔧 测试执行选项

### 按类别执行

```bash
# 核心功能测试
python tests/run_comprehensive_tests.py --category core_functionality

# 性能测试
python tests/run_comprehensive_tests.py --category performance

# UI测试
python tests/run_comprehensive_tests.py --category ui_interface

# 导出测试
python tests/run_comprehensive_tests.py --category export_compatibility

# 异常恢复测试
python tests/run_comprehensive_tests.py --category exception_recovery

# 安全合规测试
python tests/run_comprehensive_tests.py --category security_compliance
```

### 使用pytest直接执行

```bash
# 运行特定测试文件
pytest tests/core_functionality/test_screenplay_reconstruction.py -v

# 运行特定标记的测试
pytest -m "core_functionality" -v

# 运行性能测试
pytest -m "performance" -v

# 跳过慢速测试
pytest -m "not slow" -v

# 生成覆盖率报告
pytest --cov=src --cov-report=html tests/
```

## 📈 测试报告解读

### 报告结构

```json
{
  "test_summary": {
    "overall_status": "PASS/FAIL",
    "overall_pass_rate": 0.95,
    "execution_time": 1800
  },
  "statistics": {
    "total_tests": 150,
    "passed_tests": 143,
    "failed_tests": 7
  },
  "category_results": {
    "core_functionality": {
      "status": "PASS",
      "pass_rate": 0.96
    }
  },
  "production_readiness": {
    "ready": true,
    "confidence_level": "High",
    "deployment_recommendation": "推荐部署到生产环境"
  }
}
```

### 状态说明

- **PASS**: 达到目标通过率
- **FAIL**: 未达到目标通过率
- **置信度等级**: Very High (≥98%) > High (≥95%) > Medium (≥90%) > Low (≥80%) > Very Low (<80%)

## 🛠️ 故障排除

### 常见问题

1. **PyQt6导入失败**
   ```bash
   pip install PyQt6
   # 或跳过UI测试
   pytest -m "not ui_interface"
   ```

2. **内存不足**
   ```bash
   # 设置较小的测试数据集
   export TEST_DATASET_SIZE=small
   ```

3. **模型文件缺失**
   ```bash
   # 使用Mock模式
   export USE_MOCK_MODELS=true
   ```

4. **网络连接问题**
   ```bash
   # 跳过网络相关测试
   pytest -m "not network"
   ```

### 性能优化

- 使用 `--skip-slow` 跳过8小时稳定性测试
- 并行执行: `pytest -n auto` (需要pytest-xdist)
- 内存监控: 设置 `MEMORY_LIMIT=3800` (MB)

## 📞 支持

如遇到测试问题，请检查：

1. **环境依赖**: `tests/requirements-test.txt`
2. **配置文件**: `pytest.ini`
3. **日志文件**: `tests/reports/pytest.log`
4. **错误报告**: 测试报告中的 `fix_recommendations` 部分

---

**目标**: 确保VisionAI-ClipsMaster达到95%以上测试通过率，满足生产环境部署要求！
