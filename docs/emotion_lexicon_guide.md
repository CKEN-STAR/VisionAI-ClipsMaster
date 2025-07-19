# 情感词汇强化器使用指南

## 概述

情感词汇强化器是VisionAI-ClipsMaster的重要功能之一，用于增强或减弱文本中的情感表达强度。该模块能够智能替换文本中的情感词汇，使情感表达更加丰富、生动或适度削弱过于强烈的情感表达，为视频混剪提供情感调节支持。

## 主要功能

- **情感词汇增强**：增强文本中情感词汇的表达强度
- **情感词汇减弱**：降低文本中情感词汇的表达强度
- **目标级别调整**：将文本情感调整到指定强度级别
- **词汇智能替换**：根据上下文智能替换情感词汇
- **自定义增强模式**：支持多种预设增强/减弱模式
- **批量处理**：支持对整个剧本进行情感词汇调整

## 快速入门

### 基本用法

```python
from src.emotion.lexicon_enhancer import EmotionLexicon

# 初始化词汇强化器
enhancer = EmotionLexicon()

# 情感增强
text = "李明感到很高兴，因为他终于完成了这个项目。"
intensified_text = enhancer.intensify(text)
print(f"增强后: {intensified_text}")

# 情感减弱
reduced_text = enhancer.reduce(text)
print(f"减弱后: {reduced_text}")

# 调整到特定情感级别
adjusted_text = enhancer.adjust_to_level(text, 0.9)
print(f"调整到0.9级别: {adjusted_text}")
```

### 使用便捷函数

```python
from src.emotion import intensify_text, reduce_emotion, adjust_emotion_level

# 增强文本情感
text = "小红生气地看着摔碎的花瓶。"
result = intensify_text(text)
print(result)

# 减弱文本情感
result = reduce_emotion(text)
print(result)

# 调整到特定级别
result = adjust_emotion_level(text, 0.5)
print(result)
```

### 命令行工具

```bash
# 默认演示
python src/examples/emotion_lexicon_demo.py

# 处理自定义文本并增强
python src/examples/emotion_lexicon_demo.py --text "我很喜欢这部电影，演员的表演非常好。" --mode intensify

# 处理自定义文本并减弱
python src/examples/emotion_lexicon_demo.py --text "我讨厌这种天气，太糟糕了！" --mode reduce --factor 0.6

# 调整到特定情感级别
python src/examples/emotion_lexicon_demo.py --text "我非常喜欢这个礼物！" --mode adjust --target-level 0.7

# 运行完整演示
python src/examples/emotion_lexicon_demo.py --demo

# 处理示例剧本
python src/examples/emotion_lexicon_demo.py --sample
```

## 配置选项

情感词汇强化器通过`configs/emotion_lexicon.yaml`配置文件控制其行为：

### 基本配置

```yaml
lexicon_enhancer:
  # 强化/减弱因子
  intensify_factor: 1.3      # 情感强化因子
  reduce_factor: 0.7         # 情感减弱因子
  
  # 替换控制
  smart_replacement: true    # 智能替换
  context_aware: true        # 上下文感知
  use_synonyms: true         # 使用同义词
  max_replacements: 3        # 每句最大替换次数
  min_confidence: 0.7        # 最小替换置信度
```

### 增强模式配置

```yaml
enhancement_modes:
  # 情感高潮增强
  climax:
    intensify_factor: 1.5
    max_replacements: 5
    min_confidence: 0.6
    
  # 温和增强
  mild:
    intensify_factor: 1.2
    max_replacements: 2
    min_confidence: 0.75
```

### 自定义替换配置

```yaml
replacements:
  "高兴":
    - {word: "开心", intensity: 0.8}
    - {word: "兴奋", intensity: 0.9}
    - {word: "喜悦", intensity: 0.85}
    - {word: "狂喜", intensity: 0.95}
```

## 应用场景

1. **情感高潮增强**：增强视频情感高潮点的表现力
2. **情感过度削弱**：降低过于夸张的情感表达
3. **情感流控制**：调整情感表达，使整体情感曲线更加平滑
4. **叙事风格调整**：根据不同的叙事需求调整情感表达风格
5. **多版本生成**：生成不同情感强度的多个版本供选择

## 实现原理

情感词汇强化器基于以下技术实现：

1. **词汇替换**：根据情感词典替换文本中的情感词汇
2. **智能分词**：使用jieba分词处理中文文本
3. **情感强度映射**：为每个情感词维护情感强度值
4. **上下文感知**：考虑词汇上下文进行替换决策
5. **同义词网络**：利用同义词进行更自然的替换

## 高级应用

### 自定义词汇强化

```python
# 创建自定义配置
config = {
    "lexicon_enhancer": {
        "intensify_factor": 1.5,
        "max_replacements": 5,
        "min_confidence": 0.6
    }
}

# 使用自定义配置创建强化器
enhancer = EmotionLexicon(config_path=None)  # 不使用配置文件
enhancer.config = config  # 直接设置配置

# 应用自定义强化
text = "导演对最终剪辑感到满意。"
intensified = enhancer.intensify(text)
```

### 情感高潮点处理

```python
def process_emotional_highlights(script_data, threshold=0.8):
    """处理剧本中的情感高潮点"""
    enhancer = EmotionLexicon()
    
    for scene in script_data:
        # 检查是否为情感高潮点
        if scene.get("emotion_score", 0) > threshold:
            # 增强情感高潮点
            scene["text"] = enhancer.intensify(scene["text"], factor=1.5)
        else:
            # 保持原样或轻微增强
            scene["text"] = enhancer.intensify(scene["text"], factor=1.1)
    
    return script_data
```

## 实际效果示例

原始文本：
> 小明感到很高兴，他终于完成了这个项目。小红看到花瓶摔碎了很生气。

增强后：
> 小明感到欣喜若狂，他终于完成了这个项目。小红看到花瓶摔碎了勃然大怒。

减弱后：
> 小明感到开心，他终于完成了这个项目。小红看到花瓶摔碎了不高兴。

## 常见问题

**Q: 为什么某些情感词没有被替换？**  
A: 只有在配置的替换表中的词汇才会被替换。您可以在配置文件中添加更多的替换词汇。

**Q: 替换后的文本有时不够流畅，如何解决？**  
A: 启用"上下文感知"功能，并确保`min_confidence`值设置得足够高(如0.8)，可以减少不合适的替换。

**Q: 可以同时增强积极情感和减弱消极情感吗？**  
A: 可以通过先调用`adjust_emotion_level`函数将情感调整到目标水平来实现这一效果。

## 未来计划

- **多语言支持**：增加英文等其他语言的情感词汇替换
- **情感词库扩展**：进一步扩充情感词典和替换表
- **深度学习增强**：集成深度学习模型进行更智能的词汇替换
- **上下文理解**：增强上下文理解能力，提高替换准确性
- **情感连贯性**：确保整个文本的情感表达连贯一致 