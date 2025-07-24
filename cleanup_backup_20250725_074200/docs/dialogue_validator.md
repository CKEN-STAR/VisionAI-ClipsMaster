# 对话逻辑校验器

本文档介绍如何使用对话逻辑校验器来检测和分析视频对话中的逻辑一致性。该校验器可以帮助识别对话中的历史错误、角色背景冲突、时代用语错误等问题。

## 功能概述

对话逻辑校验器提供以下主要功能：

1. **历史知识一致性检测** - 验证对话内容是否与特定历史时期相符
2. **角色背景一致性检测** - 确保对话内容符合角色的教育水平和知识背景
3. **时代准确性验证** - 检查对话中使用的用语和概念是否符合特定时代背景
4. **人物关系校验** - 分析对话中提及的人物关系是否存在矛盾
5. **情感连贯性分析** - 检测角色情感变化是否自然合理

## 基本概念

### 时代划分

系统将历史划分为以下几个主要时期：

- **古代** (Ancient): 公元前3000年至公元476年
- **中世纪** (Medieval): 476年至1453年
- **文艺复兴** (Renaissance): 1453年至1600年
- **早期现代** (Early Modern): 1600年至1800年
- **工业时代** (Industrial): 1800年至1914年
- **现代** (Modern): 1914年至2000年
- **当代** (Contemporary): 2000年至今

### 教育水平分类

系统根据角色的教育背景分为以下几个级别：

- **小学** - 基础教育水平
- **初中** - 初级教育水平
- **高中** - 中级教育水平
- **大学** - 高等教育水平
- **研究生** - 专业研究水平

## 使用方法

### 基本使用

以下是使用对话逻辑校验器的基本示例：

```python
from src.logic.dialogue_validator import DialogueValidator, validate_dialogue_consistency

# 创建一个场景数据
scene = {
    "id": "scene1",
    "year": 1950,
    "dialogues": [
        {
            "character": {
                "name": "张三",
                "education_level": "大学"
            },
            "text": "二战刚结束不久，世界格局已经发生了巨大变化。"
        }
    ]
}

# 方法1：使用便捷函数
result = validate_dialogue_consistency(scene)
if result["valid"]:
    print("对话逻辑验证通过")
else:
    print(f"发现问题: {result['issue']}")
    print(f"修复建议: {result['suggestion']}")

# 方法2：使用验证器类
validator = DialogueValidator()
issue = validator.validate_dialogue(scene)
if issue:
    print(f"发现问题: {issue}")
    # 获取修复建议
    explanation = validator.explain_validation_result(issue)
    print(f"修复建议: {explanation['suggestion']}")
else:
    print("对话逻辑验证通过")
```

### 场景数据格式

场景数据应遵循以下格式：

```json
{
    "id": "场景ID",
    "year": 2020,  // 场景发生的年份
    "dialogues": [  // 对话列表
        {
            "character": {  // 角色信息
                "name": "角色名称",
                "education_level": "教育水平",  // 可选值：小学、初中、高中、大学、研究生
                "occupation": "职业"  // 可选
            },
            "text": "对话内容"
        }
    ]
}
```

## 检测的问题类型

### 1. 历史知识错误

检测对话内容中与历史事实不符的引用，例如：

- 在1939年前提及"二战"
- 在1983年前提及"互联网"
- 在特定朝代之外提及当前朝代的政策

### 2. 角色背景不一致

检测对话内容是否符合角色的教育背景，例如：

- 小学教育水平的角色讨论高深的科学理论
- 教育水平与语言复杂度不匹配

### 3. 时代用语错误

检测对话中使用的术语和概念是否符合特定历史时期，例如：

- 中世纪的人物提及"蒸汽机"
- 古代人物使用现代通讯术语

### 4. 情感连贯性问题

检测角色情感变化是否自然，例如：

- 同一角色在连续对话中从极度开心突变为极度绝望
- 情感转变缺乏合理的过渡

## 高级功能

### 知识图谱扩展

系统可以从对话中提取实体和关系，构建知识图谱：

```python
validator = DialogueValidator()

# 处理多个场景，逐步扩展知识图谱
for scene in scenes:
    validator.expand_knowledge_graph(scene)

# 查看知识图谱内容
print(validator.knowledge_graph.entities)
print(validator.knowledge_graph.relations)
```

### 自定义历史知识库

可以扩展内置的历史知识库：

```python
validator = DialogueValidator()

# 添加历史事实
validator.historical_facts["法国大革命"] = {"start_year": 1789, "end_year": 1799}

# 添加自定义时代关键词
validator.era_keywords["modern"].add("电子邮件")
```

## 性能考虑

- 对于大量对话的批量处理，建议使用异步方式
- 复杂的NLP分析可能需要更多的计算资源

## 实际应用示例

参见 `dialogue_validator_standalone.py` 文件，其中展示了完整的使用示例。

## API参考

### 主要类和函数

- **DialogueValidator** - 主要验证器类，提供完整的对话验证功能
- **validate_dialogue_consistency()** - 便捷函数，用于快速验证对话一致性

### 异常处理

当发现对话存在严重逻辑问题时，可以选择抛出 `DialogueInconsistencyError` 异常：

```python
from src.utils.exceptions import DialogueInconsistencyError

def validate_with_exception(scene):
    validator = DialogueValidator()
    issue = validator.validate_dialogue(scene)
    if issue:
        explanation = validator.explain_validation_result(issue)
        raise DialogueInconsistencyError(
            msg=issue,
            details=explanation
        )
    return True
``` 