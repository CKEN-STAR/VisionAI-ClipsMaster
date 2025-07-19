# 角色行为一致性验证器

本文档介绍如何使用VisionAI-ClipsMaster项目中的角色行为一致性验证器。该验证器可以检测角色行为与其已建立性格特征之间的不一致性，确保剧情和角色表现的连贯性。

## 功能概述

角色行为一致性验证器主要提供以下功能：

1. **角色特性分析**：从文本和对话中提取角色的性格特征
2. **行为一致性验证**：检查角色的行为是否与其已建立的性格特征一致
3. **角色发展弧线分析**：监测角色特性随时间变化是否合理
4. **角色关系一致性**：检查角色间关系是否保持一致
5. **性格特性矛盾检测**：识别角色具有的矛盾特性（如同时表现出"勇敢"和"谨慎"）
6. **性格调整建议**：基于行为观察提供角色性格设定的调整建议

## 使用方法

### 基本用法

最简单的使用方式是通过便捷函数 `validate_character_behavior` 来分析场景序列：

```python
from src.validation import validate_character_behavior

# 准备场景数据
scenes = [
    {
        "id": "scene1",
        "character": "小明",
        "text": "小明勇敢地站了出来，面对困难。"
    },
    # 更多场景...
]

# 执行验证
results = validate_character_behavior(scenes)

# 处理结果
print(f"检测到 {len(results['behavior_inconsistencies'])} 个行为不一致问题")
```

### 高级用法

如需更灵活的控制，可以直接使用 `CharacterBehaviorValidator` 类：

```python
from src.validation import CharacterBehaviorValidator

validator = CharacterBehaviorValidator()

# 逐场景分析
for i, scene in enumerate(scenes):
    inconsistencies = validator.analyze_scene(scene, i)
    if inconsistencies:
        print(f"场景 {i} 存在角色行为不一致问题: {inconsistencies}")
        
# 获取角色性格调整建议
suggestions = validator.suggest_personality_adjustments("小明")
print(f"小明的性格调整建议: {suggestions}")
```

也可以直接使用 `CharacterPersonaDatabase` 来管理角色性格特性：

```python
from src.validation import CharacterPersonaDatabase

persona_db = CharacterPersonaDatabase()

# 添加特性观察
persona_db.add_trait_observation("小明", "勇敢", 1.0)
persona_db.add_trait_observation("小明", "乐观", 0.8)

# 获取角色主要特性
dominant_traits = persona_db.get_dominant_traits("小明", top_n=2)
print(f"小明的主要特性: {dominant_traits}")

# 检查矛盾特性
contradictions = persona_db.has_contradicting_traits("小明")
if contradictions:
    print(f"检测到矛盾特性: {contradictions}")
```

## 输入数据格式

角色行为验证器接受以下格式的场景数据：

```python
{
    "id": "scene_id",              # 场景ID
    "character": "主角名",         # 场景主角（可选）
    "characters": ["角色1", "角色2"], # 场景中出现的角色列表（可选）
    "location": "场景位置",        # 场景位置（可选）
    "text": "场景描述文本",        # 场景文本内容
    "dialog": [                    # 对话内容（可选）
        {"speaker": "角色1", "text": "对话内容"},
        {"speaker": "角色2", "text": "回复内容"}
    ]
}
```

系统会自动从场景文本和对话中提取角色特性信息。

## 结果解析

验证结果是一个包含以下键的字典：

```python
{
    "character_profiles": {
        "角色1": {"特性1": 权重, "特性2": 权重, ...},
        # 更多角色...
    },
    "behavior_inconsistencies": [
        {
            "character": "角色名",
            "problem": "问题描述",
            "details": "详细信息",
            "scene_index": 场景索引
        },
        # 更多问题...
    ],
    "character_arcs": {
        "角色1": {
            "main_trait": "主要特性",
            "development": {场景索引: 特性强度, ...}
        },
        # 更多角色...
    },
    "arc_problems": [
        {
            "character": "角色名",
            "problem": "问题描述",
            "trait": "特性名称",
            "scene_indices": [有问题的场景索引列表]
        },
        # 更多问题...
    ],
    "trait_contradictions": [
        {
            "character": "角色名",
            "problem": "问题描述",
            "traits": "冲突的特性"
        },
        # 更多问题...
    ],
    "relationship_issues": [
        {
            "characters": ["角色1", "角色2"],
            "problem": "问题描述",
            "details": "详细信息"
        },
        # 更多问题...
    ]
}
```

## 监测的性格特性

系统当前监测的主要性格特性对包括：

- 勇敢 vs. 谨慎
- 乐观 vs. 悲观
- 诚实 vs. 欺骗
- 慷慨 vs. 吝啬
- 忠诚 vs. 背叛

系统通过关键词和行为模式来检测这些特性。如需扩展，可以修改 `PERSONALITY_TRAITS` 和 `BEHAVIOR_TO_TRAIT` 字典。

## 示例

以下是一个完整的使用示例：

```python
from src.validation import validate_character_behavior

# 测试场景
test_scenes = [
    {
        "id": "scene1",
        "character": "小明",
        "location": "教室",
        "text": "小明勇敢地举手回答了老师的提问。他从不犹豫，总是第一个站出来。"
    },
    {
        "id": "scene2",
        "character": "小明",
        "location": "操场",
        "text": "看到同学摔倒，小明立刻冲上前去帮助他。小刚：谢谢你，小明！小明：不用谢，这是我应该做的。"
    },
    {
        "id": "scene3",
        "character": "小明",
        "location": "家中",
        "text": "面对困难的数学题，小明犹豫不决，不敢尝试解答。他担心自己会做错。"
    }
]

# 执行验证
results = validate_character_behavior(test_scenes)

# 输出结果
print("角色性格档案:")
for character, profile in results["character_profiles"].items():
    print(f"{character}: {profile}")

print("\n行为不一致问题:")
for issue in results["behavior_inconsistencies"]:
    print(f"{issue['character']}: {issue['problem']} - {issue.get('details', '')}")
```

## 注意事项

1. 验证器需要足够的角色行为数据才能建立可靠的性格档案，建议至少有3个包含同一角色的场景
2. 系统使用简单的文本匹配进行特性提取，可能会漏掉复杂的表达方式
3. 对于中英文混合的内容都有良好的支持
4. 随着场景的增加，性格档案会不断更新，可能会影响之前的分析结果

## 实现位置

本组件的实现位于 `src/validation/character_behavior_analyzer.py` 