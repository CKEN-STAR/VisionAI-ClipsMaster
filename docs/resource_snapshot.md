# 资源快照 (Resource Snapshot)

## 概述

资源快照(ReleaseSnapshot)是VisionAI-ClipsMaster资源生命周期管理系统的安全保障组件，负责在资源释放前创建快照，允许系统在需要时恢复资源，提高系统稳定性和可靠性。

## 设计原则

资源快照系统的设计遵循以下原则：

1. **优先级管理** - 仅为高优先级资源创建快照，节省内存开销
2. **时效控制** - 快照会在一定时间后自动清理，避免占用过多内存
3. **智能恢复** - 支持单个资源的精确恢复，无需重建整个系统状态
4. **效率优先** - 快照操作高效执行，对系统性能影响最小化
5. **安全可靠** - 保证快照数据与原始资源完全一致，确保恢复准确性

## 主要功能

### 1. 创建资源快照

`take_snapshot`方法是核心方法，根据资源优先级创建快照：

```python
def take_snapshot(self, res_id: str, res_metadata: Optional[Dict[str, Any]] = None) -> bool:
    """创建资源快照"""
    # 优先级检查
    # 资源获取
    # 快照创建
    # 快照管理
```

### 2. 恢复资源

从快照恢复资源的功能由`rollback`方法提供：

```python
def rollback(self, res_id: str) -> bool:
    """从快照恢复资源"""
    # 快照检查
    # 资源恢复
```

### 3. 快照生命周期管理

系统自动管理快照的生命周期，避免占用过多内存：

- **自动过期清理** - 超过生存期(TTL)的快照自动清理
- **数量限制** - 控制系统中的最大快照数量
- **主动清理** - 提供API手动清理不再需要的快照

### 4. 优先级智能决策

系统根据资源的优先级决定是否为其创建快照：

- 只为优先级高于阈值(默认为3)的资源创建快照
- 根据配置文件定义的资源类型优先级判断
- 可通过配置调整快照策略

## 快照策略

默认策略：

1. **仅对高优先级资源保留快照**：
   - 模型分片(priority=1)
   - 渲染缓存(priority=2)
   - 临时缓冲区(priority=3)
   - 其他低优先级资源不保留快照

2. **快照保留时间控制**：
   - 快照默认保留10分钟
   - 定期自动清理过期快照
   - 超过最大数量时，优先删除最旧的快照

## 集成方式

### 与资源释放执行器集成

在资源释放前自动创建快照，示例：

```python
# 在资源释放前创建快照
snapshot_manager = get_release_snapshot()
snapshot_manager.take_snapshot(resource_id)

# 执行资源释放
reaper = get_resource_reaper()
reaper.release(resource_id, resource, metadata)
```

### 与内存监控系统集成

在内存紧急时可快速恢复重要资源：

```python
# 释放资源后，在需要时从快照恢复
if memory_pressure_reduced and resource_needed:
    snapshot_manager.rollback(resource_id)
```

## 资源备份与恢复实现

### 备份机制

系统对不同类型的资源采用不同的备份策略：

```python
def backup_resource(resource: Any) -> Any:
    """创建资源对象的备份"""
    # 支持多种类型资源的备份
    # 调用资源自身备份方法或进行深拷贝
```

支持的备份方式：
- NumPy数组 - 使用`copy()`方法
- 字典和列表 - 使用`deepcopy`
- 自定义对象 - 优先使用其`snapshot()`方法
- 其他对象 - 尝试`deepcopy`

### 恢复机制

根据资源存在状态采用不同恢复策略：

```python
def restore_resource(res_id: str, snapshot: Dict[str, Any]) -> bool:
    """从快照恢复资源"""
    # 资源存在性检查
    # 根据不同情况选择恢复策略
    # 执行恢复操作
```

恢复策略：
- 资源已删除 - 重新注册资源
- 资源仍存在 - 更新现有资源内容
- 自定义对象 - 优先使用其`restore()`方法
- 可变对象 - 更新内部状态

## 使用示例

### 基本用法

```python
from src.memory.snapshot import get_release_snapshot

# 获取快照管理器单例
snapshot_manager = get_release_snapshot()

# 创建快照
snapshot_manager.take_snapshot("model_shards:layer1")

# 检查是否存在快照
has_snapshot = snapshot_manager.has_snapshot("model_shards:layer1")

# 从快照恢复
snapshot_manager.rollback("model_shards:layer1")
```

### 查看快照信息

```python
# 获取所有快照信息
snapshots = snapshot_manager.list_snapshots()

# 获取特定快照信息
info = snapshot_manager.get_snapshot_info("model_shards:layer1")
```

### 自定义快照配置

```python
# 更新快照配置
snapshot_manager.update_config({
    "max_snapshots": 30,
    "snapshot_ttl": 900,  # 15分钟
    "snapshot_priority_threshold": 2
})
```

## 演示程序

系统提供了演示程序`src/examples/snapshot_recovery_demo.py`，展示资源快照的功能：

```bash
# 运行演示程序
python src/examples/snapshot_recovery_demo.py
```

演示程序展示：
1. 创建不同优先级的资源
2. 根据优先级创建资源快照
3. 修改资源并从快照恢复
4. 释放资源后从快照重建

## 总结

资源快照系统是VisionAI-ClipsMaster在内存受限环境下的安全防护网，确保即使在资源释放过程中出现问题，也能快速恢复关键资源，提高系统稳定性。通过只为高优先级资源创建快照，并智能管理快照生命周期，在保障安全的同时最小化内存开销。 