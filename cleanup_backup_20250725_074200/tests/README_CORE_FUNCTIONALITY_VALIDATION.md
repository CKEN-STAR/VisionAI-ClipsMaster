# VisionAI-ClipsMaster 核心功能验证测试系统

## 概述

本测试系统专门验证VisionAI-ClipsMaster的两大核心功能：
1. **视频-字幕映射精度验证** - 验证原片视频与SRT字幕的时间轴同步精度
2. **AI剧本重构功能验证** - 验证大模型理解剧情并生成爆款字幕的能力

## 测试架构

```
tests/core_functionality_validation/
├── README.md                          # 本文档
├── test_config.yaml                   # 测试配置文件
├── data_preparation/                  # 测试数据准备
│   ├── test_data_generator.py         # 测试数据生成器
│   ├── sample_generator.py            # 样本生成器
│   └── golden_samples/                # 黄金标准样本
├── video_subtitle_mapping/            # 视频-字幕映射测试
│   ├── test_timeline_accuracy.py      # 时间轴精度测试
│   ├── test_sync_validation.py        # 同步验证测试
│   └── test_multilingual_support.py   # 多语言支持测试
├── ai_script_reconstruction/          # AI剧本重构测试
│   ├── test_plot_understanding.py     # 剧情理解测试
│   ├── test_viral_generation.py       # 爆款生成测试
│   └── test_narrative_coherence.py    # 叙事连贯性测试
├── dual_model_system/                 # 双模型系统测试
│   ├── test_language_detection.py     # 语言检测测试
│   ├── test_model_switching.py        # 模型切换测试
│   └── test_performance_comparison.py # 性能对比测试
├── memory_stability/                  # 内存稳定性测试
│   ├── test_4gb_constraint.py         # 4GB内存限制测试
│   ├── test_memory_monitoring.py      # 内存监控测试
│   └── test_performance_baseline.py   # 性能基准测试
├── integration_tests/                 # 集成测试
│   ├── test_end_to_end_workflow.py    # 端到端工作流测试
│   └── test_system_integration.py     # 系统集成测试
└── reporting/                         # 测试报告
    ├── report_generator.py            # 报告生成器
    ├── visualization.py               # 结果可视化
    └── templates/                     # 报告模板
```

## 测试目标与指标

### 1. 视频-字幕映射精度验证

**测试目标：**
- 验证原片视频与SRT字幕的时间轴对应关系
- 确保同步误差 ≤ 0.5秒
- 支持中英文字幕解析和映射

**关键指标：**
- 时间轴精度：≤ 0.5秒误差
- 映射成功率：≥ 95%
- 多语言支持：中文/英文字幕正确解析率 ≥ 98%

### 2. AI剧本重构功能验证

**测试目标：**
- 验证大模型理解原片剧情结构的能力
- 验证基于"原片字幕→爆款字幕"逻辑的重构效果
- 确保生成字幕保持剧情连贯性且实现有效压缩

**关键指标：**
- 剧情理解准确率：≥ 85%
- 叙事连贯性评分：≥ 0.8
- 内容压缩比：30%-70%（避免过短或过长）
- 爆款特征匹配度：≥ 75%

### 3. 双语言模型系统验证

**测试目标：**
- 验证Mistral-7B（英文）和Qwen2.5-7B（中文）模型切换
- 验证语言检测准确性
- 对比两个模型的处理效果

**关键指标：**
- 语言检测准确率：≥ 95%
- 模型切换延迟：≤ 1.5秒
- 处理质量一致性：中英文模型输出质量差异 ≤ 10%

### 4. 内存稳定性验证

**测试目标：**
- 验证4GB内存限制下的系统稳定性
- 监控内存使用峰值和泄漏
- 建立性能基准

**关键指标：**
- 内存峰值：≤ 3.8GB
- 内存泄漏率：≤ 1%/小时
- 处理稳定性：24小时连续运行无崩溃

## 测试数据要求

### 测试数据集结构
```
test_data/
├── original_videos/           # 原片视频文件
│   ├── chinese_drama_01.mp4   # 中文短剧原片
│   ├── english_drama_01.mp4   # 英文短剧原片
│   └── mixed_language_01.mp4  # 中英混合内容
├── original_subtitles/        # 原片字幕文件
│   ├── chinese_drama_01.srt   # 对应中文字幕
│   ├── english_drama_01.srt   # 对应英文字幕
│   └── mixed_language_01.srt  # 混合语言字幕
├── viral_subtitles/           # 爆款混剪字幕
│   ├── chinese_viral_01.srt   # 中文爆款字幕
│   ├── english_viral_01.srt   # 英文爆款字幕
│   └── mixed_viral_01.srt     # 混合语言爆款字幕
└── golden_standards/          # 黄金标准参考
    ├── expected_outputs/      # 预期输出结果
    └── quality_metrics/       # 质量评估基准
```

## 自动化测试流程

### 1. 测试环境准备
```bash
# 安装测试依赖
pip install -r tests/requirements-test.txt

# 初始化测试数据
python tests/core_functionality_validation/data_preparation/test_data_generator.py

# 配置测试环境
python tests/core_functionality_validation/setup_test_environment.py
```

### 2. 执行核心功能测试
```bash
# 运行完整测试套件
python tests/core_functionality_validation/run_comprehensive_validation.py

# 运行特定测试模块
python tests/core_functionality_validation/video_subtitle_mapping/test_timeline_accuracy.py
python tests/core_functionality_validation/ai_script_reconstruction/test_plot_understanding.py
```

### 3. 生成测试报告
```bash
# 生成综合测试报告
python tests/core_functionality_validation/reporting/report_generator.py

# 生成可视化报告
python tests/core_functionality_validation/reporting/visualization.py
```

## 测试配置

### test_config.yaml 示例
```yaml
# 测试配置文件
test_environment:
  memory_limit: "4GB"
  cpu_cores: 4
  gpu_enabled: false
  
models:
  chinese_model:
    name: "qwen2.5-7b-zh"
    quantization: "Q4_K_M"
    max_memory: "2GB"
  english_model:
    name: "mistral-7b-en"
    quantization: "Q5_K_M"
    max_memory: "2GB"

test_thresholds:
  timeline_accuracy: 0.5  # 秒
  mapping_success_rate: 0.95
  plot_understanding: 0.85
  narrative_coherence: 0.8
  compression_ratio_min: 0.3
  compression_ratio_max: 0.7
  language_detection: 0.95
  model_switch_delay: 1.5  # 秒
  memory_peak: "3.8GB"

test_data:
  sample_count: 50
  languages: ["zh", "en", "mixed"]
  video_durations: [300, 600, 1200]  # 秒
  subtitle_complexity: ["simple", "medium", "complex"]
```

## 预期输出

### 测试报告格式
```json
{
  "test_summary": {
    "total_tests": 156,
    "passed": 142,
    "failed": 8,
    "skipped": 6,
    "success_rate": 91.0
  },
  "core_functionality_results": {
    "video_subtitle_mapping": {
      "timeline_accuracy": {
        "average_error": 0.23,
        "max_error": 0.48,
        "success_rate": 96.2
      },
      "multilingual_support": {
        "chinese_accuracy": 98.5,
        "english_accuracy": 97.8,
        "mixed_accuracy": 94.2
      }
    },
    "ai_script_reconstruction": {
      "plot_understanding": {
        "accuracy": 87.3,
        "coherence_score": 0.82
      },
      "viral_generation": {
        "compression_ratio": 0.45,
        "viral_features_match": 78.6
      }
    },
    "dual_model_system": {
      "language_detection": 96.8,
      "model_switching": {
        "average_delay": 1.2,
        "success_rate": 98.4
      }
    },
    "memory_stability": {
      "peak_memory": "3.6GB",
      "memory_leak_rate": 0.3,
      "stability_score": 94.7
    }
  },
  "performance_metrics": {
    "processing_speed": "2.3x realtime",
    "resource_efficiency": 89.2,
    "error_recovery_rate": 95.8
  },
  "recommendations": [
    "优化中英混合内容的语言检测算法",
    "改进内存管理策略以降低峰值使用",
    "增强异常情况下的错误恢复机制"
  ]
}
```

## 快速开始

### 1. 安装依赖
```bash
cd VisionAI-ClipsMaster
pip install -r requirements.txt
pip install -r tests/requirements-test.txt
```

### 2. 运行完整验证
```bash
# 运行所有核心功能测试
python tests/core_functionality_validation/run_comprehensive_validation.py

# 使用自定义配置
python tests/core_functionality_validation/run_comprehensive_validation.py --config custom_config.yaml

# 详细输出模式
python tests/core_functionality_validation/run_comprehensive_validation.py --verbose
```

### 3. 运行特定测试模块
```bash
# 仅运行时间轴精度测试
python tests/core_functionality_validation/video_subtitle_mapping/test_timeline_accuracy.py

# 仅运行AI剧本重构测试
python tests/core_functionality_validation/ai_script_reconstruction/test_plot_understanding.py

# 仅运行多语言支持测试
python tests/core_functionality_validation/video_subtitle_mapping/test_multilingual_support.py
```

### 4. 查看测试报告
测试完成后，报告将保存在 `tests/reports/core_functionality/` 目录下：
- `*.html` - 可视化HTML报告
- `*.json` - 详细JSON数据
- `*.pdf` - PDF格式报告（如果配置了）

## 测试结果解读

### 成功标准
- **时间轴精度**: 平均误差 ≤ 0.5秒，成功率 ≥ 95%
- **AI剧本理解**: 总体理解评分 ≥ 0.85
- **爆款生成**: 压缩比在30%-70%，爆款特征匹配度 ≥ 75%
- **多语言支持**: 解析准确率 ≥ 98%，语言检测准确率 ≥ 95%

### 报告指标说明
- **成功率**: 通过测试的用例占总用例的比例
- **平均评分**: 所有测试用例评分的平均值
- **处理时间**: 每个测试用例的平均处理时间
- **内存使用**: 测试过程中的内存占用情况

## 使用说明

1. **环境要求**：Python 3.8+，4GB+ RAM，支持CPU推理
2. **依赖安装**：运行 `pip install -r requirements-test.txt`
3. **数据准备**：执行数据生成脚本创建测试样本
4. **执行测试**：运行综合验证脚本
5. **查看结果**：检查生成的HTML/JSON测试报告

## 故障排除

### 常见问题
1. **内存不足**：调整模型量化等级或减少并发测试数量
2. **模型加载失败**：检查模型文件完整性和路径配置
3. **时间轴精度低**：验证测试视频和字幕文件的质量
4. **语言检测错误**：检查字幕文件编码和内容格式

### 调试模式
```bash
# 启用详细日志
export VISIONAI_LOG_LEVEL=DEBUG

# 运行单个测试用例
python -m pytest tests/core_functionality_validation/video_subtitle_mapping/test_timeline_accuracy.py::test_basic_timeline_sync -v
```

## 扩展测试

### 添加新测试用例
1. 在相应目录下创建测试文件
2. 继承基础测试类
3. 实现测试方法
4. 更新测试配置文件
5. 运行验证确保集成正确

### 自定义评估指标
1. 在 `reporting/metrics.py` 中定义新指标
2. 在测试类中实现计算逻辑
3. 更新报告模板以显示新指标
4. 验证指标的有效性和准确性

## 持续集成

### GitHub Actions 集成
```yaml
name: Core Functionality Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.8
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r tests/requirements-test.txt
    - name: Run core functionality tests
      run: python tests/core_functionality_validation/run_comprehensive_validation.py
```

### 定期回归测试
建议设置定期回归测试以确保系统稳定性：
- 每日构建测试
- 版本发布前完整测试
- 性能基准对比测试
