# 操作转换冲突解决器 (OTResolver)

## 功能概述

`OTResolver` 是一个基于操作转换（Operational Transformation, OT）算法的实时冲突解决器组件，用于处理多用户同时编辑同一内容时产生的冲突问题。该组件是VisionAI-ClipsMaster系统中协作编辑功能的核心部分，确保用户在协同编辑短剧时能够看到一致的内容状态。

## 主要特性

- **操作转换算法**：将并发操作智能转换，使其在不同时间点应用时能达到一致的最终状态
- **多种操作类型支持**：适配短剧混剪场景的多种操作类型（插入、删除、更新、移动等）
- **单例模式**：提供全局唯一的解决器实例，确保系统中的一致性
- **线程安全**：支持多线程环境下的并发访问
- **可扩展架构**：易于添加新的操作类型和转换规则

## 使用方法

### 获取实例

```python
from src.realtime import get_ot_resolver, initialize_ot_resolver

# 初始化（通常在应用启动时调用一次）
resolver = initialize_ot_resolver()

# 在其他地方获取已初始化的实例
resolver = get_ot_resolver()
```

### 解决冲突和合并操作

```python
# 假设有当前状态和一组新操作
current_state = {
    "version": 1234567890,
    "ops": [...],  # 已应用的操作历史
    "clips": [...]  # 当前的剪辑列表
}

# 新接收到的操作
incoming_ops = [
    {
        "id": "op123",
        "type": "insert",
        "position": 2,
        "content": {...},
        "timestamp": 1234567891
    }
]

# 解决冲突并转换操作
transformed_ops = resolver.resolve(current_state, incoming_ops)

# 将转换后的操作应用到当前状态
new_state = resolver.merge_ops(current_state, transformed_ops)
```

## 支持的操作类型

OTResolver支持以下主要操作类型的冲突解决：

1. **插入操作**（`insert`）：插入新的片段或内容
2. **删除操作**（`delete`）：删除现有片段或内容
3. **更新操作**（`update`）：修改片段属性或内容
4. **移动操作**（`move`）：调整片段的位置
5. **分割操作**（`split`）：将一个片段分成两个
6. **合并操作**（`merge`）：将两个片段合并为一个
7. **效果应用**（`apply_effect`）：添加视觉或音频效果
8. **时间调整**（`adjust_timing`）：修改片段的开始/结束时间

## 技术细节

### 操作结构

每个操作都应具有以下基本属性：

```json
{
    "id": "唯一操作ID",
    "type": "操作类型",
    "timestamp": 1234567890,
    "...": "操作特有的其他属性"
}
```

### 状态结构

应用程序状态应包含版本信息和操作历史：

```json
{
    "version": 1234567890,
    "ops": [
        操作1, 操作2, ...
    ],
    "clips": [
        片段1, 片段2, ...
    ]
}
```

### 转换规则

操作转换基于以下核心原则：

1. **因果一致性**：如果操作A在操作B之前生成，则最终结果应反映这一因果关系
2. **意图保留**：尽可能保留每个操作的原始意图，即使在冲突情况下
3. **操作独立性**：转换操作不应改变其语义，只调整其参数以适应新的上下文

## 示例场景

### 场景1：两用户同时在相同位置插入内容

用户A在位置10插入内容"ABC"，用户B在位置10插入内容"XYZ"。

- 如果用户A的操作先到达服务器，用户B的操作将被转换为在位置13插入"XYZ"
- 最终结果："...ABCXYZ..."（保持了操作的到达顺序）

### 场景2：用户A删除内容，用户B更新同一内容

用户A删除片段ID为"clip123"的内容，用户B更新该片段的属性。

- 如果用户A的删除操作先应用，用户B的更新操作将被标记为无效（因为目标已不存在）
- 系统可以提供UI反馈，通知用户B目标内容已被删除

## 测试和示例

在`src/realtime/examples/conflict_resolver_example.py`中提供了详细的示例和测试场景，演示了如何使用OTResolver处理各种冲突情况。

## 集成指南

1. 在应用启动时初始化OTResolver：
   ```python
   from src.realtime import initialize_ot_resolver
   initialize_ot_resolver()
   ```

2. 在接收到用户操作时使用OTResolver转换操作：
   ```python
   from src.realtime import get_ot_resolver
   resolver = get_ot_resolver()
   transformed_ops = resolver.resolve(current_state, incoming_ops)
   ```

3. 结合操作日志溯源器(OperationLogger)记录所有操作：
   ```python
   from src.realtime import get_operation_logger
   logger = get_operation_logger()
   logger.log_operation(session_id, "apply_operation", {
       "operations": transformed_ops,
       "source": "user_input"
   })
   ```

## 性能考虑

- OTResolver对单个操作的转换复杂度与已应用操作的数量成正比
- 对于大型编辑会话，建议定期"快照"当前状态，并清除不再需要的历史操作
- 转换处理使用了线程锁，确保在高并发环境中的安全性

## 未来扩展

- 支持更复杂的内容结构操作转换（如嵌套片段）
- 添加基于用户权限的操作优先级处理
- 实现撤销/重做功能的操作转换支持
- 与版本控制系统的集成 