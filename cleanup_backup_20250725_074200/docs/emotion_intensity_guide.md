# 情感强度图谱构建模块使用指南

## 概述

情感强度图谱构建模块是VisionAI-ClipsMaster的核心功能之一，用于分析视频/剧本的情感曲线和高潮分布。该模块能够自动识别剧本中的情感起伏、高潮、低谷，并生成可视化的情感曲线图谱，为创作者提供情感分析依据。

## 主要功能

- **情感强度曲线构建**：根据文本内容分析情感强度变化
- **情感峰值和低谷检测**：自动标记情感高潮和低谷点
- **情感质量评估**：评估情感曲线质量，检测潜在问题
- **情感曲线可视化**：生成多种可视化图表展示情感变化
- **基于情感分析的剧本优化建议**：提供改进剧本情感流程的建议

## 快速入门

### 基本用法

```python
from src.emotion.intensity_mapper import EmotionMapper

# 初始化映射器
mapper = EmotionMapper()

# 分析剧本情感曲线
curve_data = mapper.build_intensity_curve(script_scenes)

# 评估情感流程质量
flow_analysis = mapper.analyze_emotion_flow(curve_data)

# 可视化情感曲线
from src.emotion.visualizer import visualize_intensity_curve
visualize_intensity_curve(curve_data, output_dir="reports/emotion")
```

### 命令行工具

```bash
# 使用随机生成的剧本演示情感分析
python src/examples/emotion_intensity_demo.py --output-dir reports/emotion

# 使用不同情感模式的剧本
python src/examples/emotion_intensity_demo.py --script-type emotional
python src/examples/emotion_intensity_demo.py --script-type flat
python src/examples/emotion_intensity_demo.py --script-type rollercoaster

# 显示可视化结果
python src/examples/emotion_intensity_demo.py --visualize

# 详细输出
python src/examples/emotion_intensity_demo.py --verbose
```

## 配置选项

情感图谱构建模块通过`configs/emotion_intensity.yaml`配置文件控制其行为。主要配置选项包括：

### 情感分析配置

```yaml
sentiment_analysis:
  analyzer:
    type: "simple"  # 分析器类型
    threshold:
      positive: 0.6  # 积极情感阈值
      negative: 0.4  # 消极情感阈值
```

### 强度曲线配置

```yaml
intensity_curve:
  peak_detection:
    exclamation_weight: 0.1  # 感叹号权重
    question_weight: 0.05    # 问号权重
  
  smoothing:
    enabled: true            # 是否启用平滑
    window_size: 3           # 平滑窗口大小
```

### 质量评估配置

```yaml
quality_assessment:
  weights:
    range_weight: 0.3        # 变化范围权重
    climax_weight: 0.3       # 高潮权重
  
  thresholds:
    min_range: 0.2           # 最小变化范围
    climax_threshold: 0.7    # 高潮阈值
```

## 情感曲线数据结构

情感强度曲线数据的结构如下：

```json
[
  {
    "start": "00:00:10,000",       // 场景开始时间码
    "end": "00:00:20,000",         // 场景结束时间码
    "peak_value": 0.75,            // 情感强度值(0-1)
    "original_peak": 0.72,         // 平滑前的原始强度值
    "is_peak": true,               // 是否是峰值点
    "is_valley": false,            // 是否是低谷点
    "is_turning_point": true,      // 是否是转折点
    "is_global_peak": false,       // 是否是全局最高点
    "raw_text": "场景文本内容..."    // 原始文本
  },
  // ...更多数据点
]
```

## 情感质量评估结果

```json
{
  "quality": 0.85,                   // 总体质量评分(0-1)
  "emotion_range": 0.6,              // 情感变化幅度
  "turning_points": 4,               // 转折点数量
  "has_climax": true,                // 是否有明显高潮
  "issues": []                       // 存在的问题列表
}
```

## 示例情感曲线图谱

情感强度图谱可以帮助创作者直观地理解剧本的情感流动：

- **情感强度曲线图**：展示情感随剧情发展的变化趋势
- **情感热力图**：以热力图形式展示情感强度分布
- **交互式图表**：支持动态探索情感数据的交互式图表

## 集成应用

情感强度图谱模块可以与VisionAI-ClipsMaster的其他组件集成：

1. **与剧本重构模块集成**：为剧本重构提供情感分析依据
2. **与沙盒验证模块集成**：验证重构剧本的情感质量
3. **与节奏调节模块集成**：基于情感曲线优化视频节奏感
4. **与导出模块集成**：在导出报告中包含情感分析结果

## 高级应用

### 情感特征提取

```python
# 提取情感特征点
peaks = [p for p in curve_data if p.get("is_peak", False)]
valleys = [p for p in curve_data if p.get("is_valley", False)]
climax = next((p for p in curve_data if p.get("is_global_peak", False)), None)
```

### 自定义情感分析器

```python
# 使用自定义配置
config = {
    "intensity_curve": {
        "peak_detection": {
            "exclamation_weight": 0.15  # 调整感叹号权重
        }
    }
}
mapper = EmotionMapper(config=config)
```

## 常见问题

**Q: 情感图谱与人工感知有差异？**  
A: 情感分析是基于文本特征的计算结果，可能与人类的主观感受有所差异。您可以通过调整配置文件中的权重来校准分析结果。

**Q: 如何提高情感曲线质量评分？**  
A: 增加情感变化幅度，确保剧本有明显的高潮和转折点，避免情感变化过于线性或平坦。

**Q: 中文文本的情感分析效果不佳？**  
A: 系统使用了中文情感词典，但某些复杂情感或特定领域术语可能不在词典中。可以考虑扩充词典或使用更高级的情感分析模型。

## 未来计划

- 多模态情感分析：结合音频和视觉信息进行更全面的情感分析
- 情感类型细分：区分更多细分情感类型（恐惧、惊讶、期待等）
- 个性化情感模型：根据不同类型的内容自适应调整情感分析模型 