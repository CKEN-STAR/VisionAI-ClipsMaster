# 冲突解决校验模块

本文档描述了VisionAI-ClipsMaster项目中的冲突解决校验模块。该模块用于检验视频剧情中的冲突解决方案是否合理，并提供相应的改进建议。

## 基本概念

### 冲突类型

该模块支持以下几种基本冲突类型：

- **物理冲突 (PHYSICAL)** - 涉及身体接触、打斗或暴力的冲突
- **言语冲突 (VERBAL)** - 争论、辩论或言语上的对抗
- **情感冲突 (EMOTIONAL)** - 情绪或感受上的对抗
- **意识形态冲突 (IDEOLOGICAL)** - 基于信仰、价值观或思想的冲突
- **资源冲突 (RESOURCE)** - 争夺有限资源的冲突
- **利益冲突 (INTEREST)** - 基于获取利益的冲突
- **关系冲突 (RELATIONAL)** - 人际关系中的冲突
- **内心冲突 (INTERNAL)** - 角色内部的自我矛盾

### 解决方法

支持的冲突解决方法包括：

- **武力解决 (FORCE)** - 通过武力或暴力解决冲突
- **谈判解决 (NEGOTIATION)** - 通过讨论和协商达成一致
- **妥协解决 (COMPROMISE)** - 双方各让一步达成中间解决方案
- **回避解决 (AVOIDANCE)** - 暂时回避或延缓冲突
- **合作解决 (COLLABORATION)** - 共同寻求双赢的解决方案
- **调解解决 (MEDIATION)** - 通过第三方调解达成解决
- **仲裁解决 (ARBITRATION)** - 第三方做出决断并由冲突双方接受
- **投降/屈服 (SURRENDER)** - 一方放弃立场并接受另一方的条件
- **破坏/阻挠 (SABOTAGE)** - 通过破坏或阻挠对方行动解决冲突

## 功能特性

冲突解决校验模块提供以下主要功能：

1. **冲突解决合理性验证** - 分析解决方案是否符合冲突类型和情境
2. **解决强度匹配性检查** - 确保解决方案的强度与冲突强度相匹配
3. **解决者能力验证** - 确保解决者具备解决特定冲突的能力
4. **解决方式连贯性验证** - 检查同一角色在不同冲突中的解决方式是否连贯
5. **改进建议生成** - 为不合理的解决方案提供具体改进建议

## 使用方法

### 基本使用

最简单的使用方式是通过便捷函数`validate_conflict_resolution`：

```python
from src.logic.conflict_resolution import validate_conflict_resolution

# 定义冲突数据
conflicts = [
    {
        "id": "conflict1",
        "type": "verbal",
        "intensity": "medium",
        "parties": [
            {"id": "char1", "name": "张三", "strength": 7},
            {"id": "char2", "name": "李四", "strength": 5}
        ],
        "resolution": {
            "type": "negotiation",
            "outcome": "reached agreement"
        },
        "resolver": {
            "id": "char1",
            "name": "张三",
            "skills": ["negotiation", "diplomacy"]
        }
    }
]

# 验证冲突解决方案
result = validate_conflict_resolution(conflicts)

# 查看结果
print(f"验证通过: {result['valid']}")
if not result['valid']:
    print(f"问题数量: {len(result['issues'])}")
    print(f"建议数量: {len(result['suggestions'])}")
```

### 高级使用

如果需要更精细的控制，可以直接使用`ConflictResolver`类：

```python
from src.logic.conflict_resolution import ConflictResolver

# 创建冲突解决校验器
resolver = ConflictResolver()

# 验证冲突解决方案
error_message = resolver.verify_resolutions(conflicts)

# 如果有错误
if error_message:
    print(f"发现问题: {error_message}")
    
    # 获取所有问题
    issues = resolver.get_all_issues()
    for issue in issues:
        print(f"问题类型: {issue['type']}")
        print(f"问题描述: {issue['message']}")
        
    # 生成改进建议
    suggestions = resolver.generate_suggestions(conflicts)
    for conflict_id, conflict_suggestions in suggestions.items():
        print(f"冲突 {conflict_id} 的建议:")
        for suggestion in conflict_suggestions:
            print(f"问题: {suggestion['problem']}")
            print(f"建议: {suggestion['suggestion']}")
```

## 数据结构

### 冲突数据格式

冲突数据应该包含以下字段：

- `id`: 冲突唯一标识符
- `type`: 冲突类型
- `intensity`: 冲突强度 (可选，默认为"medium"，可选值: "low", "medium", "high")
- `parties`: 冲突参与方数组
  - 每个参与方包含: `id`, `name`, `strength`等属性
- `resolution`: 冲突解决方案
  - `type`: 解决方法类型
  - `outcome`: 解决结果
- `resolver`: 解决者信息 (可选)
  - `id`: 解决者ID
  - `name`: 解决者名称
  - `skills`: 解决者技能数组
  - `authority`: 解决者权威性 (可选，用于仲裁)

### 验证结果格式

验证结果包含以下字段：

- `valid`: 布尔值，表示验证是否通过
- `issues`: 问题数组，每个问题包含:
  - `type`: 问题类型
  - `conflict_id`: 相关冲突ID
  - `message`: 问题描述
  - `details`: 问题详细信息
- `suggestions`: 建议对象，以冲突ID为键，每个建议包含:
  - `problem`: 问题描述
  - `suggestion`: 改进建议

## 例子

请参见[冲突解决校验器示例](../examples/conflict_resolution_demo.py)获取完整的使用示例。

## 注意事项

1. 该模块主要关注冲突解决方案的逻辑合理性，不直接分析冲突本身的合理性
2. 冲突强度会影响解决方法的适用性评估
3. 对于武力解决方案，会检查参与方的力量对比是否与结果一致
4. 仲裁和调解解决方案需要有对应的第三方解决者 