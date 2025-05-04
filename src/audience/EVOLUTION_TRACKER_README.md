# 偏好进化追踪器 (Preference Evolution Tracker)

偏好进化追踪器是VisionAI-ClipsMaster项目的关键组件，专门用于检测、分析和预测用户内容偏好随时间的变化。通过持续追踪用户偏好的演变趋势，为内容创作者和平台提供用户兴趣转变的动态视图，助力内容的精准推荐和优化。

## 功能特点

- **偏好迁移检测**：识别用户偏好在不同维度上的变化趋势
- **偏好预测**：基于历史数据预测未来可能的偏好转变方向
- **趋势分析**：量化偏好变化的强度和稳定性
- **多维度追踪**：同时监控内容类型、叙述风格、节奏偏好等多个维度
- **置信度评估**：为每项分析和预测提供可靠性评分

## 使用场景

- **内容个性化**：根据用户偏好演变趋势动态调整推荐内容
- **创作指导**：为创作者提供受众偏好变化的趋势洞察
- **用户体验优化**：预测用户偏好转变，提前调整内容策略
- **长期用户留存**：通过适应用户偏好演变增强用户黏性
- **趋势预警**：当检测到用户偏好显著转变时发出预警

## 核心组件

### 1. 偏好进化追踪器 (PreferenceEvolution)

主要类，负责追踪和分析用户偏好的变化。

```python
from src.audience.evolution_tracker import PreferenceEvolution

# 创建追踪器实例
tracker = PreferenceEvolution()

# 检测用户偏好迁移
shift_result = tracker.detect_shift(user_id)

# 追踪并记录用户偏好演变
tracking_result = tracker.track_preference_evolution(user_id)

# 获取用户偏好演变摘要
evolution_summary = tracker.get_evolution_summary(user_id, time_range=90)
```

### 2. 便捷函数

提供简化的调用接口，方便快速使用核心功能。

```python
from src.audience.evolution_tracker import (
    detect_preference_shift,
    track_preference_changes,
    get_preference_evolution_summary
)

# 检测偏好迁移
shift_result = detect_preference_shift(user_id)

# 追踪偏好变化
tracking_result = track_preference_changes(user_id)

# 获取偏好演变摘要
evolution_summary = get_preference_evolution_summary(user_id, days=90)
```

## 支持的偏好维度

偏好进化追踪器可以同时监控多个维度的偏好变化：

1. **genre** - 内容类型偏好
2. **narrative** - 叙述风格偏好
3. **pace** - 节奏偏好
4. **visuals** - 视觉风格偏好
5. **audio** - 音频风格偏好
6. **complexity** - 内容复杂度偏好
7. **emotional** - 情感偏好
8. **themes** - 主题偏好

## 技术原理

### 偏好迁移检测

通过分析用户偏好历史数据，计算各维度的变化趋势。使用线性回归等统计方法量化趋势方向和强度，并根据数据量、相关性和时间跨度评估置信度。

### 偏好预测

基于历史数据的时间序列分析，预测未来一段时间内各维度偏好的可能变化。预测结果包括变化方向、幅度和置信度。

### 稳定性评估

计算用户偏好的整体稳定性指数，反映用户兴趣变化的剧烈程度。稳定性越高，表示用户偏好越稳定；稳定性越低，表示用户偏好正在经历显著转变。

## 输出示例

### 偏好迁移检测

```json
{
  "current_trend": {
    "status": "success",
    "analyzed_at": "2023-08-15T14:30:25.123456",
    "dimension_trends": {
      "genre": {"direction": "increasing", "magnitude": 0.35, "correlation": 0.78, "confidence": 0.82},
      "pace": {"direction": "stable", "magnitude": 0.05, "correlation": 0.12, "confidence": 0.65}
    },
    "significant_shifts": [
      {"dimension": "genre", "direction": "increasing", "magnitude": 0.35, "confidence": 0.82}
    ],
    "overall_stability": 0.75
  },
  "predicted_shift": {
    "status": "success",
    "forecasted_at": "2023-08-15T14:30:25.234567",
    "forecast_window": "30 days",
    "dimension_forecasts": {
      "genre": {
        "current_value": 0.55,
        "predicted_value": 0.72,
        "change_direction": "increasing",
        "confidence": 0.76
      }
    },
    "potential_shifts": [
      {
        "dimension": "genre",
        "current_value": 0.55,
        "predicted_value": 0.72,
        "change_percentage": 30.9,
        "direction": "increasing",
        "confidence": 0.76
      }
    ]
  }
}
```

## 演示脚本

项目提供两个演示脚本：

1. **简化演示脚本** (`run_evolution_tracker_demo.py`)：提供基本功能演示，适合快速测试

```bash
# 运行简化演示
python src/audience/run_evolution_tracker_demo.py
```

演示脚本执行结果示例：

```
偏好进化追踪器演示
==================================================

>> 检测用户偏好迁移
--------------------------------------------------

当前趋势:
总体偏好稳定性: 60.0%

显著偏好变化:
  • genre 偏好增加，变化幅度: 30.0%
    置信度: 80.0%
  • complexity 偏好减少，变化幅度: 20.0%
    置信度: 70.0%

预测未来偏好变化:
预测窗口: 30 days

预测的偏好转变:
  • genre 偏好预计将增加
    当前: 0.50 → 预测: 0.70
    变化幅度: 40.0%
    置信度: 75.0%
  • complexity 偏好预计将减少
    当前: 0.70 → 预测: 0.50
    变化幅度: 28.6%
    置信度: 65.0%


>> 追踪记录用户偏好演变
--------------------------------------------------

偏好演变记录已成功保存
记录时间: 2025-05-03T12:55:33.337639


>> 获取偏好演变摘要 (过去90天)
--------------------------------------------------

总体偏好稳定性: 60.0%

重要变化:
  1. [观察到的趋势] genre 偏好增加
     变化幅度: 30.0%
     置信度: 80.0%
  2. [观察到的趋势] complexity 偏好减少
     变化幅度: 20.0%
     置信度: 70.0%
  3. [预测的转变] genre 偏好增加
     变化幅度: 40.0%
     置信度: 75.0%
```

2. **完整演示脚本** (`evolution_tracker_demo.py`)：包含完整功能演示和可视化，适合深入了解

## 集成指南

### 1. 检测偏好迁移

```python
from src.audience.evolution_tracker import detect_preference_shift

# 检测用户偏好迁移
result = detect_preference_shift("user_123")

# 获取显著变化
significant_shifts = result["current_trend"]["significant_shifts"]
for shift in significant_shifts:
    print(f"{shift['dimension']} 偏好{shift['direction']}，幅度：{shift['magnitude']*100:.1f}%")

# 获取预测的未来转变
potential_shifts = result["predicted_shift"]["potential_shifts"]
for shift in potential_shifts:
    print(f"{shift['dimension']} 偏好预计将{shift['direction']}，变化：{shift['change_percentage']:.1f}%")
```

### 2. 追踪偏好演变

```python
from src.audience.evolution_tracker import track_preference_changes

# 追踪用户偏好演变
result = track_preference_changes("user_123")

if result["status"] == "success":
    print("用户偏好演变记录已保存")
    print(f"记录时间：{result['tracked_at']}")
else:
    print(f"偏好演变记录失败：{result.get('message', '未知错误')}")
```

### 3. 获取偏好演变摘要

```python
from src.audience.evolution_tracker import get_preference_evolution_summary

# 获取过去60天的偏好演变摘要
summary = get_preference_evolution_summary("user_123", days=60)

print(f"分析数据点数：{summary['history_points']}")
print(f"偏好稳定性：{summary['overall_stability']*100:.1f}%")

# 输出重要变化
print("\n重要变化：")
for change in summary["significant_changes"]:
    print(f"- {change['dimension']} 偏好{change['direction']}")
```

## 注意事项

1. 偏好进化追踪器需要足够的历史数据才能提供高置信度的分析和预测
2. 建议至少有5个历史数据点才能进行有效的趋势分析
3. 置信度评分反映了预测的可靠性，建议关注置信度高于0.6的结果
4. 预测结果的可靠性会随着预测窗口的扩大而降低 