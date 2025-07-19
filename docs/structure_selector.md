# 叙事结构选择器

本文档介绍如何使用叙事结构选择器来选择最适合特定剧本的叙事结构模式，根据剧本特征和锚点进行智能匹配。

## 什么是叙事结构选择器？

叙事结构选择器是一个智能组件，能够分析剧本元数据（如类型、情感基调、节奏）和关键情节锚点，选择最适合的叙事结构模式，用于指导非线性叙事重构，提升剧情的叙事效果和观感。

结构选择器支持多种常见和创新的叙事结构模式，如：
- 倒叙风暴：从高潮场景开始，通过倒叙揭示前因后果
- 多线织网：多条故事线并行发展，最终汇聚成完整叙事
- 高潮迭起：多个情感和剧情高潮点连续出现，形成强烈节奏感
- 环形结构：故事结尾回到开始，但主角或情境已有深刻变化
- 悬念递进：不断设置和解决悬念，推动故事向前发展

## 使用方法

### 1. 通过Python API使用

```python
from src.narrative.structure_selector import select_narrative_structure, get_structure_patterns
from src.narrative.anchor_detector import detect_anchors

# 准备剧本元数据
script_metadata = {
    "genre": "悬疑,犯罪",      # 剧本类型
    "emotion_tone": "紧张",    # 情感基调
    "pace": "fast"            # 节奏
}

# 仅基于元数据选择结构
result = select_narrative_structure(script_metadata)
print(f"推荐结构: {result['pattern_name']}")
print(f"匹配原因: {result['reason']}")
print(f"结构步骤: {result['pattern_data']['steps']}")

# 从场景数据检测锚点
scenes = [...]  # 场景数据列表
anchors = detect_anchors(scenes)

# 基于元数据和锚点选择结构
result_with_anchors = select_narrative_structure(script_metadata, anchors)
print(f"推荐结构: {result_with_anchors['pattern_name']}")

# 获取所有可用的结构模式
all_patterns = get_structure_patterns()
for name, pattern in all_patterns.items():
    print(f"{name}: {pattern['description']}")
```

### 2. 通过命令行工具使用

```bash
# 使用示例剧本测试结构选择器
python -m src.examples.structure_selector_demo --type suspense

# 测试不同类型的剧本
python -m src.examples.structure_selector_demo --type action
python -m src.examples.structure_selector_demo --type romance

# 保存可视化结果
python -m src.examples.structure_selector_demo --type epic --output epic_structure.json

# 使用自定义配置
python -m src.examples.structure_selector_demo --type comedy --config path/to/custom_config.yaml
```

### 3. 通过REST API使用

```bash
# 基于剧本元数据选择结构
curl -X POST "http://localhost:8000/api/narrative/select-structure" \
     -H "Content-Type: application/json" \
     -d '{
       "script_metadata": {
         "genre": "悬疑,犯罪",
         "emotion_tone": "紧张",
         "pace": "fast"
       }
     }'

# 获取所有可用的叙事结构模式
curl -X GET "http://localhost:8000/api/narrative/available-structures"
```

## 配置文件

叙事结构选择器支持通过配置文件自定义行为。默认配置文件位于`configs/narrative/structure_selector.yaml`。

主要配置项包括：

- **narrative_patterns**: 叙事模式定义，包含各种结构模式的步骤、适用类型等
- **structure_selection**: 结构选择算法的参数，如匹配阈值、权重等
- **anchor_mapping**: 锚点映射到结构的配置
- **models**: 模型配置（保留了对英文模型的支持，但默认不加载）

## 叙事结构模式

每个叙事结构模式包含以下属性：

```yaml
模式名称:
  steps: [步骤1, 步骤2, ...]           # 结构步骤
  suitability: [类型1, 类型2, ...]     # 适用的剧本类型
  description: "模式描述"              # 模式的详细描述
  min_anchors: 3                      # 推荐的最小锚点数量
  anchor_types: [类型1, 类型2, ...]    # 适用的锚点类型
  emotion_tone: "情感基调"             # 适合的情感基调
  pace: "节奏"                        # 适合的节奏
  beat_distribution:                  # 节拍分布
    步骤1: 0.25                       # 步骤占比
    步骤2: 0.50
    步骤3: 0.25
```

## 锚点映射

结构选择器可以将检测到的关键情节锚点映射到叙事结构的各个步骤上，支持基于锚点的内容重组和精准叙事控制。

```python
from src.narrative.structure_selector import StructureSelector, organize_anchors_by_structure
from src.narrative.anchor_detector import detect_anchors

# 检测锚点
scenes = [...]  # 场景数据
anchors = detect_anchors(scenes)

# 选择结构
selector = StructureSelector()
result = selector.select_best_fit(script_metadata, anchors)
structure_name = result["pattern_name"]

# 映射锚点到结构步骤
anchor_mapping = selector.map_anchors_to_structure(anchors, structure_name)

# 查看每个步骤的锚点
for step, step_anchors in anchor_mapping.items():
    print(f"{step}: {len(step_anchors)} 个锚点")
    for anchor in step_anchors:
        print(f"  - {anchor.description} ({anchor.type.value})")
```

## 与锚点检测器的集成

叙事结构选择器可以无缝集成关键情节锚点检测器，形成完整的叙事分析和结构优化工作流：

1. 使用锚点检测器识别剧本中的关键情节锚点
2. 使用结构选择器选择最适合的叙事结构
3. 将锚点映射到结构的各个步骤
4. 基于结构和锚点进行内容重组和优化

## 注意事项

1. 虽然默认不加载英文模型，但保留了配置文件中的相关设置，以便在未来直接加载
2. 结构选择的质量取决于剧本元数据的准确性和锚点检测的精度
3. 对于特殊类型的内容，建议手动调整配置文件中的模式参数以获得更好的匹配结果
4. 当锚点数量不足时，系统会更多地依赖剧本元数据进行结构选择

## 示例输出

以下是一个结构选择结果的示例：

```json
{
  "success": true,
  "pattern_name": "悬念递进",
  "confidence": 0.82,
  "reason": "类型匹配度高，情节锚点匹配良好",
  "steps": ["谜题设置", "线索播撒", "悬念解决"],
  "description": "不断设置和解决悬念，推动故事向前发展",
  "suitability": ["悬疑", "犯罪"],
  "anchor_mapping": {
    "谜题设置": [
      {
        "id": "emotion_valley_a1b2c3d4",
        "type": "emotion",
        "position": 0.15,
        "confidence": 0.75,
        "importance": 0.68,
        "description": "情感低谷点 (-0.72)"
      }
    ],
    "线索播撒": [
      {
        "id": "suspense_setup_e5f6g7h8",
        "type": "suspense",
        "position": 0.42,
        "confidence": 0.88,
        "importance": 0.79,
        "description": "悬念设置点"
      }
    ],
    "悬念解决": [
      {
        "id": "suspense_resolution_i9j0k1l2",
        "type": "suspense",
        "position": 0.78,
        "confidence": 0.92,
        "importance": 0.85,
        "description": "悬念解决点"
      }
    ]
  }
}
```

## 高级使用

### 自定义结构模式

您可以通过编辑配置文件添加自定义的叙事结构模式：

```yaml
narrative_patterns:
  my_custom_structure:
    steps: ["我的步骤1", "我的步骤2", "我的步骤3"]
    suitability: ["我的类型1", "我的类型2"]
    description: "我的自定义结构描述"
    min_anchors: 3
    anchor_types: ["emotion", "character"]
    emotion_tone: "我的情感基调"
    pace: "medium"
```

### 调整匹配权重

可以通过配置文件调整各个特征的匹配权重，以适应不同的应用场景：

```yaml
structure_selection:
  match_threshold: 0.6     # 匹配阈值
  anchor_weight: 0.7       # 锚点匹配权重
  genre_weight: 0.8        # 类型匹配权重
  emotion_weight: 0.5      # 情感匹配权重
  pace_weight: 0.4         # 节奏匹配权重
```

### 结构可视化

可以生成叙事结构的可视化数据，用于UI显示或进一步分析：

```python
from src.api.structure_api import generate_structure_visualization

visualization_data = generate_structure_visualization(
    anchors, 
    structure_name,
    output_path="structure_visualization.json"
)
``` 