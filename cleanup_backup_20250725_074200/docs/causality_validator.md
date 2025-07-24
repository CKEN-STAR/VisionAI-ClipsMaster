# 因果链验证引擎

本文档介绍如何使用因果链验证引擎来检测和分析视频剧情中的因果关系逻辑。该引擎可以帮助识别故事情节中的逻辑漏洞、未解决的情节线索以及时序矛盾等问题。

## 功能概述

因果链验证引擎提供以下主要功能：

1. **因果链追踪** - 跟踪事件之间的因果关系，构建完整的因果网络
2. **悬念点检测** - 识别剧情中引入但未解决的问题或线索
3. **因果矛盾检测** - 发现剧情中的逻辑矛盾，如时序悖论
4. **故事完整性评分** - 计算故事情节的因果完整性得分
5. **因果链补全建议** - 提供完善因果链的具体建议

## 基本概念

### 事件类型

系统支持以下几种核心事件类型：

- **问题事件(problem)** - 引入需要解决的故事问题，通常是情节的起点
- **线索事件(clue)** - 提供故事发展的线索，需要后续跟进
- **解决事件(resolution)** - 解决前面引入的问题

### 因果关系类型

系统支持多种因果关系类型：

- `DIRECT` - 直接因果：A直接导致B
- `INDIRECT` - 间接因果：A通过中间事件导致B
- `ENABLING` - 使能因果：A使B成为可能
- `PREVENTIVE` - 阻止因果：A阻止B发生
- `MOTIVATIONAL` - 动机因果：A成为B的动机
- `TEMPORAL` - 时序因果：A在时间上先于B

## 使用方法

### 基本使用

以下是使用因果链验证器的基本示例：

```python
from src.logic import CausalityValidator, validate_causality

# 创建一些事件数据
events = [
    {
        "id": "event1",
        "type": "problem",
        "description": "主角失去了重要的钥匙",
        "characters": ["主角"],
        "importance": 0.8
    },
    {
        "id": "event2",
        "description": "主角沿着来时的路寻找钥匙",
        "characters": ["主角"],
        "importance": 0.6,
        "causes": [
            {"id": "event1", "relation": "DIRECT"}
        ]
    },
    {
        "id": "event3",
        "type": "resolution",
        "description": "主角在公园长椅下找到了钥匙",
        "characters": ["主角"],
        "importance": 0.7,
        "causes": [
            {"id": "event2", "relation": "DIRECT"}
        ]
    }
]

# 方法1：使用便捷函数
result = validate_causality(events)

# 方法2：使用验证器类
validator = CausalityValidator()
result = validator.analyze_causal_structure(events)

# 检查结果
print(f"问题数量: {len(result['issues'])}")
print(f"故事完整性: {result['completeness']}")

# 查看事件链
for chain in result['chains']:
    print(f"事件链: {chain}")

# 查看修复建议
if result['suggestions']:
    for issue_type, suggestions in result['suggestions'].items():
        for suggestion in suggestions:
            print(f"建议: {suggestion['message']}")
```

### 事件数据格式

事件数据应遵循以下格式：

```json
{
    "id": "唯一标识符",
    "type": "事件类型(problem/clue/resolution/event)",
    "description": "事件描述",
    "characters": ["相关角色列表"],
    "importance": 0.8,  // 事件重要性(0.0-1.0)
    "causes": [  // 与此事件相关的原因事件
        {
            "id": "原因事件ID",
            "relation": "DIRECT"  // 关系类型
        }
    ],
    "effects": [  // 与此事件相关的结果事件(可选)
        {
            "id": "结果事件ID",
            "relation": "DIRECT"  // 关系类型
        }
    ]
}
```

## 问题检测与建议

### 检测的问题类型

因果链验证引擎可以检测以下类型的问题：

1. **未解决的问题** - 引入了问题事件，但没有对应的解决事件
2. **悬而未决的线索** - 引入了线索，但没有后续发展
3. **时序悖论** - 结果事件出现在原因事件之前
4. **孤立事件** - 重要事件没有与其他事件的因果联系

### 修复建议

针对每种问题类型，系统都会给出具体的修复建议，例如：

- 为未解决的问题添加解决事件
- 为悬而未决的线索添加后续发展
- 调整事件顺序解决时序悖论
- 为孤立事件建立因果联系

## 高级功能

### 因果链分析

系统可以从事件关系中自动识别主要和次要因果链：

```python
# 获取所有事件链
chains = validator.get_event_chains()

# 找出主要因果链
main_chain_index = result['main_chain_index']
main_chain = result['chains'][main_chain_index]
```

### 故事完整性评分

系统提供0.0-1.0的故事完整性评分，反映因果链的完整度：

```python
completeness = result['completeness']
# 1.0表示完美的因果链(所有问题都有解决，所有线索都有发展)
# 低于1.0表示存在未解决的问题或线索
```

## 性能考虑

- 对于大规模事件集合(100+事件)，建议分段分析
- 对于复杂故事，因果网络的构建可能需要更多时间

## 实际应用示例

参见 `examples/causality_demo.py` 文件，其中展示了完整的使用示例。

## API参考

### 主要类和函数

- **CausalityValidator** - 主要验证器类，提供完整的因果分析功能
- **EventNode** - 表示因果网络中的事件节点
- **CausalityType** - 枚举类，定义因果关系类型
- **validate_causality()** - 便捷函数，用于快速验证因果关系

### 异常处理

当发现故事存在严重因果问题时，系统可能会抛出 `CausalityBreakError` 异常：

```python
from src.utils.exceptions import CausalityBreakError

try:
    result = validate_causality(events)
except CausalityBreakError as e:
    print(f"因果链存在问题: {e}")
    print(f"详细信息: {e.details}")
``` 