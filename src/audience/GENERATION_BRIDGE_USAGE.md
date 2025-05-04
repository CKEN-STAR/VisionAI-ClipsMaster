# 代际差异桥接器使用指南

## 概述

GenerationBridge（代际差异桥接器）是VisionAI-ClipsMaster项目的重要组件，帮助弥合不同世代受众间的文化差异，优化内容在不同年龄层受众中的理解和接受度。通过转换代际特定的表达方式，使内容能够跨代际有效传播。

## 功能特点

- 支持Z世代、90后、80后、70后、60后之间的内容转换
- 自动检测内容的代际倾向 
- 转换代际特定的词汇、表达方式和文化参考
- 根据目标世代调整语气和风格
- 支持向内容中添加特定世代的文化元素

## 使用方法

### 1. 标准集成使用

如果已正确设置项目依赖，可以通过以下方式使用:

```python
from src.audience import (
    get_generation_bridge, 
    bridge_gap, 
    detect_content_generation,
    insert_cultural_elements
)

# 检测内容世代
source_gen = detect_content_generation(content)
print(f"内容世代: {source_gen}")

# 转换为目标世代
target_gen = "80后"
converted = bridge_gap(content, target_gen)

# 插入文化元素
cultural_refs = ["二次元", "yyds", "破防"]
enhanced = insert_cultural_elements(content, cultural_refs)
```

### 2. 使用独立演示脚本

我们提供了多个独立脚本，便于在不同环境中测试和展示代际差异桥接器功能：

#### 完全独立的演示脚本

`standalone_demo.py` 是一个完全自包含的脚本，不依赖于任何外部模块，可以直接运行:

```bash
python src/audience/standalone_demo.py
```

这个脚本包含了完整的 `GenerationBridge` 实现和示例演示。

#### 简易运行脚本 

`run_generation_bridge_simple.py` 是另一个自包含脚本，提供了更多的演示功能:

```bash
python src/audience/run_generation_bridge_simple.py
```

#### 项目集成演示脚本

如果已正确设置项目依赖，可以运行更完整的演示:

```bash
python src/audience/generation_bridge_demo.py
```

### 3. 直接使用GenerationBridge类

您也可以直接导入和使用 `GenerationBridge` 类:

```python
from src.audience.generation_gap import GenerationBridge

bridge = GenerationBridge()

# 检测内容世代
source_gen = bridge._detect_generation(content)

# 转换为目标世代
converted = bridge.bridge_gap(content, "Z世代")
```

## 内容格式

代际差异桥接器处理的内容格式为JSON对象，包含以下字段:

```json
{
  "title": "内容标题",
  "description": "内容描述",
  "dialogues": [
    {"speaker": "narrator", "text": "对话文本1"},
    {"speaker": "presenter", "text": "对话文本2"}
  ],
  "scenes": [
    {
      "id": "scene_1",
      "description": "场景描述",
      "elements": [
        {"type": "text", "content": "元素文本内容"}
      ]
    }
  ]
}
```

## 代际特征

模块支持以下世代特征转换：

- **Z世代**: 简短、直接、使用流行词和表情符号，关键词包括二次元、整片化、玩梗、yyds等
- **90后**: 介于Z世代和80后之间，关键词包括QQ空间、非主流、贴吧、LOL等
- **80后**: 怀旧、叙事性强、较为正式，关键词包括童年、港台文化、经典款等
- **70后**: 更偏传统，注重文化内涵，关键词包括岁月、传统、价值观等
- **60后**: 高度传统，关键词包括传统文化、历史、红色经典等

## 故障排除

如果在使用代际差异桥接器时遇到导入问题，可以尝试：

1. 直接使用 `standalone_demo.py` 脚本，它不依赖其他模块
2. 检查项目依赖是否正确安装
3. 确保 Python 路径设置正确

## 示例转换

### Z世代 → 80后

**原文**：
> 这个角色真的绝绝子，看到就破防了，yyds！🔥

**转换后**：
> 这个角色真的非常好，看到就受打击了，最棒的！

### 80后 → Z世代

**原文**：
> 这些经典角色承载了整整一代人的童年回忆，每次重温都倍感亲切。

**转换后**：
> 嗯，这些经典角色承载了整整一代人的童年回忆，每次重温都倍感亲切，yyds！🔥 