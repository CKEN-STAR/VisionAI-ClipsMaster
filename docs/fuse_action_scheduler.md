# VisionAI-ClipsMaster 熔断动作优先级调度系统

## 概述

熔断动作优先级调度系统是VisionAI-ClipsMaster内存管理框架的关键组件，用于在不同内存压力情况下智能地调度熔断动作的执行顺序，从而实现最佳的资源回收和用户体验平衡。

## 系统架构

该系统由以下主要组件构成：

1. **ActionPrioritizer**: 核心调度器，根据内存压力级别对动作进行优先级排序
2. **ActionSchedulerHook**: 熔断管理器的钩子，把优先级调度集成到现有熔断系统
3. **示例与演示工具**: 用于验证和展示优先级调度效果

## 调度策略

系统实现了基于压力级别的智能调度策略：

- **低压力情况(< 90%)**: 优先执行低影响动作，最小化用户体验影响
- **高压力情况(>= 90%)**: 优先执行高影响动作，最大化内存释放速度

各个动作按照其对系统和用户体验的影响程度被分为三类：

| 影响级别 | 权重范围 | 典型动作 |
|---------|---------|---------|
| 低影响   | 0.0-0.4 | 清理临时文件、降低日志级别 |
| 中影响   | 0.4-0.7 | 卸载非关键模型分片、降低质量 |
| 高影响   | 0.7-1.0 | 杀死进程、禁用功能 |

## 主要功能

1. **动作权重配置**: 为每个熔断动作预定义影响权重，也支持运行时自定义
2. **压力感知排序**: 根据当前内存压力自动调整动作执行顺序
3. **资源释放优化**: 在紧急情况下优先释放最大量内存的操作
4. **用户体验保护**: 在低压力情况下优先执行低影响操作
5. **统计与分析**: 跟踪调度效果，提供优化数据

## 集成方式

系统通过轻量级钩子集成到现有熔断系统中，无侵入性：

```python
# 获取调度器钩子并安装
from src.fuse.action_scheduler_hook import get_scheduler_hook

hook = get_scheduler_hook()
hook.install()  # 安装钩子

# 恢复原始行为
hook.uninstall()
```

## 性能特性

1. **响应时间优化**: 在高压力情况下，快速释放大量内存，降低OOM崩溃风险
2. **用户体验平衡**: 在不同压力级别下，智能平衡内存释放与用户体验影响
3. **可扩展性**: 支持自定义权重和新增动作类型
4. **低开销**: 调度算法本身轻量高效，不增加显著计算负担

## 使用示例

```python
from src.fuse.action_scheduler import get_action_prioritizer

# 获取动作优先级调度器
prioritizer = get_action_prioritizer()

# 可用动作列表
actions = [
    "clear_temp_files",
    "reduce_log_verbosity",
    "unload_noncritical_shards",
    "kill_largest_process"
]

# 假设当前压力为95%
pressure = 95.0

# 获取优先级排序后的动作
scheduled_actions = prioritizer.schedule_actions(actions, pressure)
print(f"调度结果: {scheduled_actions}")
# 输出: 调度结果: ['kill_largest_process', 'unload_noncritical_shards', 'clear_temp_files', 'reduce_log_verbosity']

# 注册自定义权重
prioritizer.register_custom_weight("my_custom_action", 0.8)
```

## 未来优化方向

1. **学习优化**: 基于历史执行效果自动调整权重
2. **上下文感知**: 根据用户场景（如渲染中、编辑中）调整优先级策略
3. **动态权重**: 基于实际释放的内存量动态调整权重
4. **并行执行**: 支持无依赖动作的并行执行以加速内存释放 