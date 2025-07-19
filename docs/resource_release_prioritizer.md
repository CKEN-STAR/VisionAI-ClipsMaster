# 资源释放优先级决策树

## 概述

资源释放优先级决策树是VisionAI-ClipsMaster资源管理系统的核心组件，负责在内存压力下智能确定资源释放的顺序。该组件基于多因素评分机制，确保最优的资源释放策略，在维持系统性能的同时高效管理内存资源。

## 设计原则

资源释放优先级决策树的设计遵循以下原则：

1. **配置驱动** - 根据`configs/releasable_resources.yaml`中定义的资源类型优先级排序资源
2. **多因素评分** - 考虑资源类型优先级、最后访问时间、资源大小等多个因素
3. **同优先级智能排序** - 同优先级资源按最近访问时间排序，最久未访问的资源优先释放
4. **活动资源保护** - 降低当前活动资源（如活动模型）的释放优先级
5. **可解释性** - 提供释放决策的详细解释，便于调试和监控

## 关键功能

### 1. 计算释放优先级

`calculate_release_priority`方法对所有资源进行评分，并返回按释放优先级排序的资源ID列表：

```python
# 评分因子包括:
# - 资源类型优先级(低数字优先)
# - 最后访问时间(越久未访问越优先)
# - 资源大小(大资源优先释放，释放更多内存)
# - 活动状态(非活动资源优先)
# - 是否已过期(已过期资源优先)
```

### 2. 获取释放候选资源

`get_release_candidates`方法根据所需内存量选择释放候选资源：

```python
# 基于优先级列表选择资源
# 累计所选资源大小直到满足所需内存量
# 返回候选资源ID列表
```

### 3. 释放决策解释

`explain_decision`方法提供资源被选择释放的详细原因：

```python
# 返回包含以下信息的解释:
# - 资源基本信息(ID、类型、优先级)
# - 访问时间和过期状态
# - 具体释放原因列表
```

### 4. 优化的排序算法

排序算法综合考虑多个因素计算资源评分：
- 优先级作为基础分(低优先级数字产生低评分)
- 访问时间因子(根据访问年龄计算的减分)
- 大小因子(大资源获得更多减分)
- 活动状态(活动资源获得加分)
- 压缩能力(可压缩资源获得少量加分)
- 过期状态(已过期资源获得大量减分)

最终，低评分的资源优先释放。

## 集成方式

释放优先级决策树已与以下组件集成：

1. **ResourceTracker** - 资源跟踪器使用决策树确定最佳释放顺序
2. **MemoryGuard** - 内存监控系统在内存压力下使用决策树选择释放资源
3. **DeviceManager** - 设备管理器使用决策树获取释放建议

## 使用方法

### 基本用法

```python
# 获取释放优先级决策器
from src.memory.release_prioritizer import get_release_prioritizer
prioritizer = get_release_prioritizer()

# 计算释放优先级
priority_list = prioritizer.calculate_release_priority(resources, resource_types)

# 获取释放候选资源
candidates = prioritizer.get_release_candidates(resources, resource_types, needed_mb)

# 解释释放决策
explanation = prioritizer.explain_decision(resource_id, resources, resource_types)
```

### 在内存压力下释放资源

```python
# 获取资源跟踪器
from src.memory.resource_tracker import get_resource_tracker
tracker = get_resource_tracker()

# 在内存压力下释放资源
released_count = tracker.release_by_memory_pressure(needed_mb)
```

## 配置示例

在`configs/releasable_resources.yaml`中配置资源优先级：

```yaml
resource_types:
  # 优先级1(最优先释放)
  - name: "model_shards"
    priority: 1
    max_retain_time: 300
    
  # 优先级2
  - name: "render_cache"
    priority: 2
    max_retain_time: 180
    
  # 优先级3
  - name: "temp_buffers"
    priority: 3
    max_retain_time: 30
    
  # 优先级越大，越晚释放
  - name: "model_weights_cache"
    priority: 5
    max_retain_time: 600
```

## 演示程序

提供了一个演示脚本`src/examples/release_prioritizer_demo.py`，展示释放优先级决策树的工作原理：

```bash
# 运行完整演示
python src/examples/release_prioritizer_demo.py --demo all

# 只演示优先级排序
python src/examples/release_prioritizer_demo.py --demo priority

# 只演示内存压力下的释放
python src/examples/release_prioritizer_demo.py --demo pressure
```

## 性能考虑

- 排序操作的时间复杂度为O(n log n)
- 对于大量资源，可以使用批处理方式减少计算开销
- 决策树会缓存计算结果，减少重复计算 