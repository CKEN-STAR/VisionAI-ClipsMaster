# 情感演进监测器

本文档介绍如何使用情感演进监测器来分析和验证视频情感的连贯性和流动性。该工具可以帮助创作者确保视频的情感节奏合理，避免情感跳跃造成的观感割裂。

## 功能概述

情感演进监测器提供以下主要功能：

1. **情感跳跃检测** - 识别场景之间不自然的情感强度变化
2. **情感曲线分析** - 评估整体视频的情感起伏是否符合预期模式
3. **情感节奏构建** - 确保视频情感变化的节奏感符合特定类型视频的期望
4. **情感冲突检测** - 分析跨场景的情感类型冲突，避免不合理的情感转变
5. **情感连贯性建议** - 提供改善情感连贯性的建议，包括添加过渡场景等

## 基本概念

### 情感强度

每个场景需要提供一个介于0-1之间的情感强度评分（emotion_score），代表场景中情感的强度：
- 0: 极低强度（平淡、无感情）
- 0.5: 中等强度（普通情感表达）
- 1: 极高强度（极其强烈的情感）

### 情感类别

系统内置九种基本情感类别：

- `HAPPINESS` - 欢乐、愉悦、幸福
- `SADNESS` - 悲伤、忧郁、痛苦
- `ANGER` - 愤怒、恼火、暴躁
- `FEAR` - 恐惧、害怕、担忧
- `DISGUST` - 厌恶、反感
- `SURPRISE` - 惊讶、震惊
- `NEUTRAL` - 中性、平淡
- `ANTICIPATION` - 期待、预期
- `TRUST` - 信任、依赖

### 情感节奏模式

系统内置了多种情感节奏模式，用于分析和构建情感曲线：

- `mountain` (山形曲线) - 情感起伏呈山峰状，适合有明确高潮的故事
- `valley` (谷型曲线) - 情感开始高，中间下降，最后上升，适合挫折-克服类故事
- `rising` (上升曲线) - 情感持续上升，适合悬疑和恐怖类型
- `falling` (下降曲线) - 情感持续下降，适合悲剧类型
- `wave` (波浪曲线) - 情感有规律波动，适合喜剧和冒险类型

## 使用方法

### 基本使用

以下是使用情感演进监测器的基本示例：

```python
from src.logic.emotion_continuity import EmotionTransitionMonitor, validate_emotion_continuity

# 场景数据示例
scenes = [
    {"id": "scene1", "emotion_score": 0.3, "emotion_type": "neutral"},
    {"id": "scene2", "emotion_score": 0.5, "emotion_type": "happiness"},
    {"id": "scene3", "emotion_score": 0.8, "emotion_type": "happiness"},
    {"id": "scene4", "emotion_score": 0.4, "emotion_type": "surprise"}
]

# 方法1：使用便捷函数
result = validate_emotion_continuity(scenes)
if result["issues_detected"]:
    print(f"检测到 {len(result['emotion_jumps'])} 个情感跳跃问题")
    print(f"检测到 {len(result['emotion_conflicts'])} 个情感冲突问题")
else:
    print("情感流畅连贯，未检测到问题")

# 方法2：使用监测器类
monitor = EmotionTransitionMonitor(max_jump=0.4)  # 自定义最大允许跳跃度
problems = monitor.check_emotion_flow(scenes)
if problems:
    for problem in problems:
        print(f"情感跳跃问题: {problem['message']}")
```

### 场景数据格式

场景数据应遵循以下格式：

```json
[
    {
        "id": "场景ID",
        "emotion_score": 0.5,  // 情感强度，0-1之间的浮点数
        "emotion_type": "happiness"  // 情感类型，可选
    }
]
```

## 高级功能

### 情感节奏匹配度分析

评估视频情感曲线与特定节奏类型的匹配程度：

```python
monitor = EmotionTransitionMonitor()
result = monitor.evaluate_rhythm_alignment(scenes, "mountain")
print(f"匹配度: {result['similarity_score']}")
print(f"评估: {result['message']}")

# 如果匹配度低，会提供改进建议
if "suggestions" in result:
    for suggestion in result["suggestions"]:
        print(suggestion["message"])
```

### 过渡场景建议

在情感跳跃处提供添加过渡场景的具体建议：

```python
# 先检测情感流
monitor.check_emotion_flow(scenes)

# 获取过渡建议
suggestions = monitor.suggest_transition_scenes(scenes)
for suggestion in suggestions:
    print(f"建议: {suggestion['message']}")
    
    if "transition_advice" in suggestion:
        advice = suggestion["transition_advice"]
        print(f"描述: {advice['description']}")
        print(f"建议: {advice['suggestion']}")
```

### 情感曲线可视化

生成情感曲线的可视化图表：

```python
# 生成并显示图表
monitor.visualize_emotion_curve(scenes)

# 与目标节奏对比并保存图表
monitor.visualize_emotion_curve(
    scenes, 
    target_rhythm="mountain",
    output_path="emotion_curve.png"
)
```

### 情感平衡分析

分析视频中情感类型的分布是否平衡：

```python
balance = monitor.check_emotion_balance(scenes)
if balance["balanced"]:
    print("情感分布平衡")
else:
    print(f"情感分布不平衡: {balance['message']}")
    if "missing_emotions" in balance:
        print(f"建议添加: {', '.join(balance['missing_emotions'])}")
```

### 视频类型情感推荐

根据视频类型获取推荐的情感节奏模式：

```python
recommendations = monitor.get_best_emotion_patterns(scenes, "恐怖")
print(f"推荐的节奏模式: {recommendations['recommendations']}")
print(recommendations["message"])
```

## 特殊场景处理

### 情感冲突矩阵

系统内置了情感冲突矩阵，定义了哪些情感类型之间的转变需要特别注意：

```python
# 部分情感冲突关系示例
EMOTION_CONFLICT_MATRIX = {
    EmotionCategory.HAPPINESS: [
        EmotionCategory.SADNESS, 
        EmotionCategory.ANGER, 
        EmotionCategory.DISGUST
    ],
    # ...其他情感类型的冲突关系
}
```

当相邻场景的情感类型存在冲突时，系统会提供特定的过渡建议。

## 实际应用示例

查看 `examples/emotion_continuity_demo.py` 获取完整的使用示例，包括：

1. 分析不同类型视频（喜剧、剧情片、恐怖片）的情感曲线
2. 检测情感跳跃和冲突
3. 提供改进建议
4. 生成情感曲线可视化

## API参考

### 主要类和函数

- **EmotionTransitionMonitor** - 主要监测器类，提供全面的情感分析功能
- **validate_emotion_continuity()** - 便捷函数，用于快速分析情感连贯性
- **EmotionCategory** - 情感类别枚举，定义了系统支持的情感类型

### 异常处理

当发现情感连贯性问题时，可以选择抛出 `EmotionDiscontinuityError` 异常：

```python
def validate_with_exception(scenes):
    monitor = EmotionTransitionMonitor()
    problems = monitor.check_emotion_flow(scenes)
    if problems:
        raise EmotionDiscontinuityError(
            message=problems[0]["message"],
            details={"problems": problems}
        )
    return True
```

## 性能考虑

- 适用于中小规模视频的场景分析（数十到数百个场景）
- 如果需要处理大型项目，建议分段分析
- 可视化功能需要matplotlib库，但基础分析功能不依赖该库 