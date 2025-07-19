# 关键情节锚点检测

本文档介绍如何使用关键情节锚点检测模块来识别视频/剧本中的关键情节转折点，从而辅助模式匹配和叙事结构优化。

## 什么是关键情节锚点？

关键情节锚点是指视频/剧本中具有特殊叙事意义的关键点，这些点往往代表着情节的重要转折、情感的显著变化或人物关系的关键互动。锚点检测可以帮助我们更好地理解叙事结构，识别模式，并进行有针对性的内容优化。

主要的锚点类型包括：

1. **情感锚点**：情感高潮或低谷，情绪显著变化的点
2. **人物锚点**：角色关系发生变化的场景，如相遇、对抗、和解等
3. **悬念锚点**：设置悬念或揭示真相的关键点

## 使用方法

### 1. 通过Python API使用

```python
from src.narrative.anchor_detector import detect_anchors, get_top_anchors, visualize_anchors

# 准备场景数据
scenes = [
    {
        "id": "scene_1",
        "text": "张三走在回家的路上，思考着刚才发生的事。",
        "emotion_score": 0.2,
        "characters": ["张三"],
        "duration": 5.0
    },
    # ... 更多场景
]

# 检测锚点
anchors = detect_anchors(scenes)

# 获取最重要的锚点
top_anchors = get_top_anchors(anchors, top_n=5)

# 输出结果
for anchor in top_anchors:
    print(f"锚点类型: {anchor.type.value}")
    print(f"描述: {anchor.description}")
    print(f"位置: {anchor.position:.2f}")
    print(f"重要性: {anchor.importance:.2f}")
    print("-" * 30)

# 可视化锚点
total_duration = sum(scene.get("duration", 1.0) for scene in scenes)
vis_data = visualize_anchors(anchors, total_duration, "anchors_visualization.json")
```

### 2. 通过命令行工具使用

```bash
# 使用示例数据生成锚点并可视化
python -m src.examples.anchor_detector_demo --output visualization.json

# 从JSON文件中加载场景数据
python -m src.examples.anchor_detector_demo --input scenes.json --output visualization.json
```

### 3. 通过REST API使用

```bash
# 检测锚点
curl -X POST "http://localhost:8000/api/narrative/detect-anchors" \
     -H "Content-Type: application/json" \
     -d '{"scenes": [...场景数据...], "config_path": null}'

# 上传场景文件并检测锚点
curl -X POST "http://localhost:8000/api/narrative/upload-scenes" \
     -F "file=@scenes.json"

# 可视化锚点
curl -X POST "http://localhost:8000/api/narrative/visualize-anchors" \
     -H "Content-Type: application/json" \
     -d '{"scenes": [...场景数据...], "config_path": null}'
```

## 配置文件

锚点检测器支持通过配置文件自定义检测行为。默认配置文件位于`configs/narrative/anchor_detector.yaml`。

主要配置项包括：

- **thresholds**: 各类锚点的检测阈值
- **priority_weights**: 不同锚点类型的优先级权重
- **detection_windows**: 检测窗口设置
- **merge_strategy**: 锚点合并策略
- **models**: 模型设置（保留了对中英文的支持，但默认不加载英文模型）

## 锚点类型与属性

每个检测到的锚点都具有以下属性：

```python
class AnchorInfo:
    id: str                                 # 锚点ID
    type: AnchorType                        # 锚点类型
    position: float                         # 位置（0-1之间的相对位置）
    start_time: Optional[Union[float, timedelta]] = None  # 开始时间
    end_time: Optional[Union[float, timedelta]] = None    # 结束时间
    confidence: float = 0.0                 # 置信度（0-1）
    importance: float = 0.0                 # 重要性（0-1）
    description: str = ""                   # 锚点描述
    scene_id: Optional[str] = None          # 所属场景ID
    emotion_score: Optional[float] = None   # 情感分数（-1到1）
    characters: List[str] = None            # 相关角色
    keywords: List[str] = None              # 关键词
    related_anchors: List[str] = None       # 相关锚点IDs
    metadata: Dict[str, Any] = None         # 其他元数据
```

锚点类型包括：

```python
class AnchorType(Enum):
    EMOTION = "emotion"         # 情感锚点（高潮/低谷）
    CHARACTER = "character"     # 人物关系锚点（相遇/决裂）
    SUSPENSE = "suspense"       # 悬念锚点（未解谜题）
    CONFLICT = "conflict"       # 冲突锚点
    REVELATION = "revelation"   # 揭示锚点（真相揭露）
    TRANSITION = "transition"   # 转场锚点（场景/时间跳转）
    CLIMAX = "climax"           # 高潮锚点（情节最高点）
    RESOLUTION = "resolution"   # 解决锚点（问题解决）
```

## 注意事项

1. 虽然默认不加载英文模型，但保留了配置文件中的相关设置，以便在未来直接加载
2. 锚点检测结果的质量取决于输入场景的详细程度，建议在场景数据中包含尽可能多的信息，如情感分数、角色信息等
3. 如果没有提供预标注的情感分数，系统会尝试通过文本分析来估算，但准确度可能较低
4. 系统会自动缓存已检测过的场景的锚点结果，以提高效率

## 与现有系统的集成

锚点检测模块已经与现有系统集成，可以通过以下方式使用：

1. **模式匹配**: 使用锚点来匹配叙事模式，优化模式识别的精确度
2. **剧情结构优化**: 基于锚点分析来优化剧情结构，提高叙事效果
3. **关键情节提取**: 使用重要锚点来提取视频的关键情节，用于生成摘要或预告片
4. **跨媒介模式迁移**: 在跨媒介迁移过程中保持关键情节锚点的一致性

## 示例

以下是一个检测结果示例：

```json
{
  "success": true,
  "total_anchors": 12,
  "anchor_stats": {
    "emotion": 5,
    "character": 4,
    "suspense": 3
  },
  "top_anchors": [
    {
      "id": "emotion_peak_a1b2c3d4",
      "type": "emotion",
      "position": 0.67,
      "confidence": 0.85,
      "importance": 0.92,
      "description": "情感高潮点 (0.82)",
      "keywords": ["情感", "高潮", "激动"]
    },
    // ... 更多锚点
  ]
}
```

## 高级用法

### 自定义检测策略

您可以通过修改配置文件来自定义检测策略，例如调整阈值、权重等参数：

```yaml
thresholds:
  emotion:
    significant_change: 0.35    # 调整情感变化检测阈值
    peak_value: 0.8            # 调整高潮情感阈值
```

### 集成外部NLP模型

系统设计考虑了与外部NLP模型的集成，可以通过配置来启用更强大的语言理解能力：

```yaml
models:
  emotion:
    chinese:
      path: "models/emotion/chinese_emotion_model"
      enabled: true
```

### 二次开发

如果您需要添加新的锚点类型或检测策略，可以扩展`AnchorDetector`类，添加新的检测方法。 