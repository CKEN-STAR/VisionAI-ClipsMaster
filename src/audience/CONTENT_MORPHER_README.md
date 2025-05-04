# 动态内容变形器 (ContentMorpher)

## 概述

动态内容变形器是VisionAI-ClipsMaster项目的一个核心组件，用于根据用户偏好对内容进行智能调整和变形，使内容更符合用户的喜好和体验期望。通过内容变形器，系统可以针对不同用户的喜好特点，对同一内容进行个性化处理，从而提升用户体验。

## 主要功能

内容变形器提供三大核心变形策略：

1. **情感增强 (Emotion Amplification)**：
   - 增强内容的情感强度，使情感表达更加明显
   - 针对特定情感类型（如喜悦、悲伤、紧张等）进行有针对性的增强
   - 自动控制增强程度，避免过度失真

2. **节奏调整 (Pacing Adjustment)**：
   - 根据用户偏好调整内容的节奏快慢
   - 支持快节奏、中节奏和慢节奏三种模式
   - 根据场景切换频率和内容特点智能调整

3. **文化本地化 (Cultural Localization)**：
   - 将内容中的文化引用替换为目标文化中的等价概念
   - 支持中西文化互相转换
   - 保持内容连贯性和上下文一致性

## 实现架构

内容变形器采用模块化设计，包括以下主要组件：

- **ContentMorpher类**：核心变形引擎，协调各种变形策略的应用
- **变形策略映射**：定义了各种可应用的变形策略及其实现方式
- **偏好解析器**：将用户偏好数据转换为变形策略权重
- **辅助函数**：提供单一变形功能的独立实现

## 使用方法

### 基本用法

```python
from src.audience import get_content_morpher, morph_content

# 方法1：使用全局变形器实例
morpher = get_content_morpher()
morphed_content = morpher.morph_content(original_content, strategy_weights)

# 方法2：使用便捷函数
morphed_content = morph_content(original_content, strategy_weights)
```

### 直接应用特定变形

```python
from src.audience import amplify_emotion, adjust_pacing, replace_cultural_references

# 情感增强
amplified = amplify_emotion(content, factor=1.5)

# 节奏调整
fast_paced = adjust_pacing(content, target_bpm=150)

# 文化本地化
localized = replace_cultural_references(content, "zh", "en")
```

### 根据用户偏好应用变形

```python
from src.audience import apply_user_preferences

# 获取用户偏好数据
user_preferences = get_user_preferences(user_id)

# 根据用户偏好应用变形
personalized_content = apply_user_preferences(content, user_preferences)
```

## 策略权重配置

策略权重是一个字典，定义了应用各种变形策略的强度：

```python
strategy_weights = {
    "情感极化": 0.8,    # 情感增强强度
    "快节奏": 0.7,     # 快节奏应用强度
    "西方化": 0.9      # 文化本地化(西方化)强度
}
```

权重值范围从0到1，其中：
- 0-0.3：弱应用
- 0.3-0.6：中等应用
- 0.6-1.0：强应用

只有权重值超过系统设定的阈值(默认0.5)，对应策略才会被应用。

## 如何扩展

要添加新的变形策略，可以按照以下步骤操作：

1. 在ContentMorpher类的`_initialize_strategies`方法中添加新策略
2. 实现策略对应的变形函数
3. 更新策略权重解析逻辑，支持从用户偏好中提取新策略的权重

例如，添加一个"对比度增强"策略：

```python
# 1. 在_initialize_strategies中添加
self.MORPH_STRATEGIES.update({
    "对比度增强": lambda x, factor=1.5: enhance_contrast(x, factor)
})

# 2. 实现变形函数
def enhance_contrast(content, factor=1.5):
    # 实现对比度增强逻辑
    result = copy.deepcopy(content)
    # ...
    return result
    
# 3. 更新_preferences_to_strategies方法
def _preferences_to_strategies(self, preferences):
    # ...
    # 添加对比度偏好处理
    if "visual_preferences" in preferences:
        contrast_pref = preferences["visual_preferences"].get("contrast", 0.5)
        if contrast_pref > 0.7:
            strategy_weights["对比度增强"] = min(1.0, contrast_pref * 1.1)
    # ...
```

## 注意事项

1. 内容变形器总是返回内容的副本，不会修改原始内容
2. 多个变形策略可以同时应用，系统会按照一定顺序处理以确保最佳效果
3. 策略应用顺序：情感增强 → 节奏调整 → 文化本地化
4. 变形器通过内部阈值控制，避免过度变形导致内容失真 