# 情感焦点定位器使用指南

## 概述

情感焦点定位器是VisionAI-ClipsMaster的核心功能之一，用于自动检测和定位文本/剧本中的情感高潮点。该模块能够识别各种情感焦点，包括高情感强度的句子、包含肢体动作描述的片段以及富有情感的对话内容，为短视频混剪提供情感核心定位支持。

## 主要功能

- **情感焦点检测**：自动识别文本中的情感焦点
- **焦点位置定位**：精确定位情感焦点在文本中的起始和结束位置
- **上下文提取**：自动提取情感焦点的上下文内容
- **情感得分计算**：评估每个焦点的情感强度得分
- **多维度分析**：综合考虑情感强度、肢体动作和对话特征
- **批量处理**：支持对整个剧本或字幕文件进行批量分析

## 快速入门

### 基本用法

```python
from src.emotion.focus_locator import EmotionFocusLocator

# 初始化定位器
locator = EmotionFocusLocator()

# 定位文本中的情感焦点
text = "小雨惊讶地瞪大眼睛："哇！这太让人难以置信了！"她激动地抱住了李明。"
focus_ranges = locator.find_emotion_focus_ranges(text)

# 输出结果
for focus in focus_ranges:
    print(f"焦点文本: {focus['focus_text']}")
    print(f"情感得分: {focus['emotion_score']}")
    print(f"位置: {focus['start']}-{focus['end']}")
```

### 命令行工具

```bash
# 使用默认示例文本
python src/examples/emotion_focus_demo.py

# 分析自定义文本
python src/examples/emotion_focus_demo.py --text "王芳愤怒地摔门而去："我再也不想见到你了！"小明呆立在原地，眼泪不断滑落。"

# 分析剧本文件
python src/examples/emotion_focus_demo.py --script data/scripts/my_script.json

# 使用样本剧本
python src/examples/emotion_focus_demo.py --sample --script-type emotional
```

## 配置选项

情感焦点定位器通过`configs/emotion_focus.yaml`配置文件控制其行为：

### 焦点检测配置

```yaml
focus_detection:
  # 情感得分阈值，高于此值的句子被视为情感焦点
  emotion_score_threshold: 0.7
  
  # 各特征权重
  body_language_weight: 0.2    # 肢体动作描述权重
  dialogue_weight: 0.15        # 对话特征权重
  exclamation_weight: 0.1      # 感叹词和强调权重
```

### 肢体动作描述词

```yaml
body_language_patterns:
  - "摇头"
  - "点头"
  - "皱眉"
  - "微笑"
  # 更多动作描述...
```

### 情感对话标记词

```yaml
emotional_dialogue_markers:
  - "!"      # 感叹号
  - "?!"     # 问号+感叹号
  - "..."    # 省略号
  # 更多标记...
```

## 情感焦点数据结构

情感焦点的结果数据结构如下：

```json
{
  "start": 23,               // 焦点开始位置
  "end": 56,                 // 焦点结束位置
  "focus_text": "...",       // 焦点文本内容
  "context_text": "...",     // 带上下文的文本
  "context_start": 3,        // 上下文开始位置
  "context_end": 76,         // 上下文结束位置
  "emotion_score": 0.92      // 情感得分(0-1)
}
```

## 应用场景

1. **视频混剪的关键点定位**：自动识别应该保留的高情感时刻
2. **情感高潮分析**：找出剧本中的情感高潮点
3. **字幕筛选**：从大量字幕中筛选出情感强烈的部分
4. **内容摘要生成**：基于情感焦点生成内容摘要

## 实现原理

情感焦点定位器基于多种方法识别情感焦点：

1. **情感分析**：使用情感分析算法计算基础情感强度
2. **肢体动作检测**：识别文本中描述的肢体语言
3. **对话特征检测**：识别对话中的情感标记和强调
4. **文本分析**：基于标点、强调和句式结构进行分析

## 集成应用

情感焦点定位器可以与其他模块集成：

1. **与情感强度图谱集成**：为情感曲线提供精确定位
2. **与剧本重构集成**：基于情感焦点重构剧本
3. **与视频剪辑模块集成**：直接指导视频剪辑点的选择

## 高级应用

### 自定义焦点检测

```python
# 自定义配置
config = {
    "focus_detection": {
        "emotion_score_threshold": 0.6,  # 降低阈值检测更多焦点
        "body_language_weight": 0.3      # 增加肢体动作的权重
    }
}

# 使用自定义配置
locator = EmotionFocusLocator(config=config)
```

### 分析整个剧本

```python
# 读取剧本
with open('script.json', 'r', encoding='utf-8') as f:
    script_data = json.load(f)

# 分析每个场景
for scene in script_data:
    scene_with_focus = locator.analyze_scene_emotion_focus(scene)
    
    # 处理结果
    focus_ranges = scene_with_focus["emotion_focus"]["ranges"]
    highest_score = scene_with_focus["emotion_focus"]["highest_score"]
    
    if highest_score > 0.8:
        print(f"高情感场景: {scene['id']}")
```

## 常见问题

**Q: 为什么某些明显的情感内容没有被检测到？**  
A: 检测依赖于情感阈值设置，尝试在配置中降低`emotion_score_threshold`值。

**Q: 如何增加肢体动作的检测范围？**  
A: 在配置文件的`body_language_patterns`列表中添加更多肢体动作描述词。

**Q: 结果中包含了过多不相关的焦点？**  
A: 增加情感阈值，或调整各特征的权重，减少不相关特征的影响。

## 技术限制与债务

- **多模态分析**：当前仅支持文本分析，音频和视觉信息分析能力有限
- **人物情感关联**：角色与情感焦点的关联识别功能需要完善
- **场景关联分析**：情感焦点在整体叙事中的作用分析相对简单
- **情感转折点检测**：情感转折点的专门识别机制需要改进