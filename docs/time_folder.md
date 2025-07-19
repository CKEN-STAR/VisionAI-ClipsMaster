# 时空折叠引擎

本文档介绍时空折叠引擎的使用方法，它能将线性时间轴重构为非线性叙事结构，为剧情创作提供更灵活的叙事可能性。

## 什么是时空折叠引擎？

时空折叠引擎是一个智能工具，可以根据叙事结构和情节锚点将线性时间轴转换为非线性叙事结构。它可以实现各种常见的非线性叙事技巧，如倒叙、插叙、多线并行、环形结构等，帮助创作者突破线性叙事的限制，创造出更具吸引力的故事体验。

主要功能包括：
- 基于关键情节锚点保留重要场景，压缩非关键场景
- 压缩相似场景，提高叙事效率
- 强调情感对比，突出戏剧冲突
- 基于特定叙事结构（如倒叙风暴、多线织网等）重构时间轴

## 使用方法

### 1. 通过Python API使用

```python
from src.nonlinear.time_folder import fold_timeline, FoldingMode
from src.narrative.anchor_detector import detect_anchors

# 准备场景数据
scenes = [...]  # 场景列表

# 检测锚点
anchors = detect_anchors(scenes)

# 执行折叠 - 使用默认参数
folded_scenes = fold_timeline(scenes, anchors)

# 使用特定叙事结构和折叠模式
from src.nonlinear.time_folder import TimeFolder

folder = TimeFolder()
folded_scenes = folder.fold_timeline(
    scenes, 
    anchors,
    structure_name="倒叙风暴",
    mode=FoldingMode.NARRATIVE_DRIVEN
)

# 结果使用
for scene in folded_scenes:
    print(f"场景: {scene['text']}")
    if scene.get("is_climax"):
        print("  (高潮场景)")
    if scene.get("is_flashback"):
        print("  (回闪场景)")
```

### 2. 通过命令行工具使用

```bash
# 使用示例数据测试时空折叠引擎
python -m src.examples.time_folder_demo --type suspense

# 使用不同叙事结构
python -m src.examples.time_folder_demo --type action --structure 高潮迭起

# 使用不同折叠模式
python -m src.examples.time_folder_demo --type suspense --mode highlight_contrast
```

### 3. 通过REST API使用

```bash
# 折叠时间轴
curl -X POST "http://localhost:8000/api/nonlinear/fold" \
     -H "Content-Type: application/json" \
     -d '{
       "scenes": [...],
       "structure_name": "倒叙风暴",
       "folding_mode": "narrative_driven"
     }'

# 获取所有可用的折叠策略
curl -X GET "http://localhost:8000/api/nonlinear/strategies"

# 获取所有可用的折叠模式
curl -X GET "http://localhost:8000/api/nonlinear/modes"

# 估算折叠结果
curl -X POST "http://localhost:8000/api/nonlinear/estimate" \
     -H "Content-Type: application/json" \
     -d '{
       "scenes": [...],
       "structure_name": "多线织网"
     }'
```

## 折叠策略

时空折叠引擎支持多种折叠策略，每种策略适用于不同的叙事结构：

1. **倒叙风暴** - 从高潮点开始，通过回忆和闪回构建叙事
   - 适用结构：倒叙风暴(flashback_storm)
   - 特点：高潮前置，回忆插叙，悬念回收

2. **多线织网** - 交织多条故事线，强调人物关系和情感变化
   - 适用结构：多线织网(multi_thread)
   - 特点：视角切换，平行叙事，线索汇聚

3. **环形结构** - 首尾呼应，形成循环叙事结构
   - 适用结构：环形结构(circular_narrative)
   - 特点：首尾呼应，循环暗示，意义升华

4. **高潮迭起** - 多个高潮点递进，不断提升紧张感
   - 适用结构：高潮迭起(escalating_peaks)
   - 特点：铺垫，多重高潮，余波

5. **并行蒙太奇** - 两条故事线并行发展，通过交替场景展现
   - 适用结构：并行交替(parallel_montage)
   - 特点：双线设定，平行推进，交点转折，统一结局

## 折叠模式

时空折叠引擎支持四种基本的折叠模式：

1. **保留锚点模式(preserve_anchors)** - 保留关键锚点场景，压缩非关键场景
   - 适用于：所有类型的内容
   - 特点：保持叙事的关键点，减少不重要内容

2. **压缩相似模式(condense_similar)** - 识别并合并相似场景，保持内容多样性
   - 适用于：节奏缓慢、场景重复的内容
   - 特点：提高叙事效率，避免内容重复

3. **强调对比模式(highlight_contrast)** - 强调情感和戏剧对比，突出冲突
   - 适用于：情感起伏较大、戏剧性内容
   - 特点：增强戏剧张力，突出情感变化

4. **叙事驱动模式(narrative_driven)** - 基于特定叙事结构重构时间轴
   - 适用于：复杂叙事、非线性叙事
   - 特点：根据特定叙事结构（如倒叙、环形等）重组场景

## 配置自定义

时空折叠引擎支持通过配置文件自定义行为。默认配置文件位于`configs/nonlinear/time_folder.yaml`。

主要配置项包括：

- **default**: 默认设置，包括默认结构、策略和阈值等
- **strategies**: 折叠策略配置，包括各种策略的参数
- **folding_modes**: 折叠模式配置，包括各种模式的参数
- **models**: 模型配置（保留对英文模型的配置支持，但默认不加载）

### 自定义折叠策略示例

```yaml
strategies:
  my_custom_strategy:
    name: "我的自定义策略"
    description: "自定义策略描述"
    structure_types: ["自定义结构1", "自定义结构2"]
    fold_ratio: 0.4
    preserve_start: true
    preserve_end: true
    anchor_weights:
      character: 1.5
      emotion: 1.2
      climax: 1.0
      # ...
```

## 与其他模块的集成

时空折叠引擎可以与其他模块无缝集成，形成完整的工作流：

1. 使用关键情节锚点检测器识别剧本中的关键锚点
2. 使用叙事结构选择器选择最适合的叙事结构
3. 使用时空折叠引擎根据结构和锚点重构时间轴
4. 基于重构后的时间轴生成最终剧本或视频

## 注意事项

1. 折叠率过高可能导致叙事连贯性下降，建议根据内容类型适当调整
2. 对于短内容（场景数少于5个），折叠效果可能不明显
3. 某些叙事结构（如倒叙风暴）对锚点的质量要求较高，建议确保锚点检测的准确性
4. 英文模型目前保留配置但未加载，如需处理英文内容，可以在配置中启用

## 示例输出

以下是一个使用倒叙风暴结构折叠后的结果示例：

```json
{
  "success": true,
  "original_count": 15,
  "folded_count": 8,
  "reduction_ratio": 0.47,
  "structure_name": "倒叙风暴",
  "strategy_name": "倒叙风暴",
  "folding_mode": "narrative_driven",
  "anchors_count": 7,
  "folded_scenes": [
    {
      "id": "scene_12",
      "text": "主角被神秘人袭击，陷入危险。",
      "emotion_score": -0.8,
      "characters": ["主角", "神秘人"],
      "duration": 11.0,
      "folded": true,
      "folding_strategy": "倒叙风暴",
      "structure_name": "倒叙风暴",
      "is_climax": true
    },
    {
      "id": "scene_1",
      "text": "主角在深夜接到一个神秘电话。",
      "emotion_score": -0.2,
      "characters": ["主角"],
      "duration": 8.0,
      "folded": true,
      "folding_strategy": "倒叙风暴",
      "structure_name": "倒叙风暴",
      "is_flashback": true
    },
    {
      // ... 其他场景
    }
  ]
}
``` 