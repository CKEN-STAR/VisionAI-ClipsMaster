# 智能容差管理系统

## 概述

智能容差管理系统是VisionAI-ClipsMaster的核心质量控制模块，负责定义和实施一系列质量标准，以确保生成的视频混剪质量符合预期，同时适应不同设备条件下的运行需求。本系统通过动态调整质量评估参数，在保证视频可接受质量的同时，优化低配置设备的性能表现。

## 主要功能

1. **多维度质量评估**：从视频、字幕和剧情叙事三个维度进行全面评估
2. **自适应容差控制**：根据设备配置动态调整质量评估标准
3. **版权安全检测**：识别潜在的版权侵权风险
4. **综合评分系统**：生成加权综合质量得分和质量级别

## 配置文件

系统配置文件位于`configs/tolerance_rules.yaml`，主要包含以下配置项：

```yaml
# 视频质量容差参数
video:
  duration_tolerance: 0.5            # 视频时长偏差容许度（秒）
  psnr_threshold: 28                 # 关键帧PSNR最低要求
  resolution_tolerance: 5%           # 分辨率容差
  color_fidelity: 85%                # 色彩保真度要求
  
# 字幕质量容差参数
subtitle:
  timecode_tolerance: 0.1            # 时间码允许误差（秒）
  text_similarity: 90                # 文本相似度最低要求（百分比）
  entity_coverage: 100%              # 关键实体覆盖率要求
  
# 剧情完整性评估标准
narrative:
  key_plot_retention: 95%            # 关键情节点保留率
  duration_ratio:                    # 剧情时长比例
    min: 25%                         # 最小值（防止过短）
    max: 75%                         # 最大值（防止与原片差异过小）
    ideal: 40%                       # 理想值
```

## 系统架构

```
ToleranceManager
├── 配置管理
│   ├── _load_config()           # 加载配置文件
│   ├── _get_default_config()    # 提供默认配置
│   └── save_adjusted_config()   # 保存调整后的配置
│
├── 系统资源检测
│   ├── _collect_system_info()   # 收集系统信息
│   ├── _check_gpu()             # 检测GPU可用性
│   └── _adjust_for_resources()  # 根据资源调整容差
│
├── 质量检测
│   ├── check_video_quality()    # 视频质量检测
│   ├── check_subtitle_quality() # 字幕质量检测
│   ├── check_narrative_quality()# 剧情质量检测
│   └── calculate_overall_score()# 计算综合评分
│
└── 安全检测
    └── verify_copyright_safety()# 版权安全检测
```

## 使用示例

```python
from src.core.tolerance_manager import ToleranceManager

# 初始化容差管理器
manager = ToleranceManager()

# 评估视频质量
video_metrics = {
    "duration": 120.5,
    "target_duration": 120.0,
    "psnr": 32.0,
    "resolution_match": 0.97
}
passed, results = manager.check_video_quality(video_metrics)

# 评估字幕质量
subtitle_metrics = {
    "max_timecode_error": 0.08,
    "text_similarity": 92.5,
    "entity_match_rate": 1.0
}
passed, results = manager.check_subtitle_quality(subtitle_metrics)

# 计算总体评分
overall = manager.calculate_overall_score(video_results, subtitle_results, narrative_results)
print(f"质量评分: {overall['overall_score']} - {overall['quality_level']}")
```

## 容差调整策略

### 低配置设备适配

当系统检测到运行在低配置设备上时（内存≤4GB或CPU核心≤2或无GPU），系统将根据`adaptive_tolerance`配置自动调整容差标准：

1. 降低视频PSNR阈值（最低至20）
2. 降低色彩保真度要求（最低至70%）
3. 降低字幕相似度要求（最低至75%）
4. 降低剧情连贯性要求（最低至55分）

这些调整确保了即使在资源受限的环境中，系统也能保持基本功能而不牺牲关键质量要求。

### 版权安全阈值

系统会检测原始视频中的水印和音频指纹，以防止潜在的版权侵权问题：

- 水印检测置信度阈值：0.85（高于此值视为存在水印）
- 音频指纹匹配阈值：0.9（高于此值视为存在版权音频）

## 质量评分标准

系统根据综合评分将质量分为四个级别：

- **优秀** (≥85分)：高质量输出，无需调整
- **提示** (75-85分)：可接受质量，但有改进空间
- **警告** (60-75分)：存在明显质量问题，建议调整
- **严重问题** (<60分)：质量不可接受，必须修复

## 相关文件

- 配置文件：`configs/tolerance_rules.yaml`
- 实现代码：`src/core/tolerance_manager.py`
- 单元测试：`tests/unit_test/test_tolerance_manager.py` 