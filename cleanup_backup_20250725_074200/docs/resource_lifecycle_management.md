# 资源生命周期管理系统

本文档描述了VisionAI-ClipsMaster中的资源生命周期管理系统，这是一个专为内存受限设备(4GB RAM/无GPU)而设计的智能资源跟踪和释放机制。

## 功能概述

资源生命周期管理系统通过跟踪资源的创建和访问时间，并根据预定义的策略自动释放过期或不再需要的资源。这使得系统能够在内存受限的环境中高效运行大型语言模型(如Qwen2.5-7B和Mistral-7B)，同时保持稳定性和性能。

主要功能包括：

1. **资源生命周期跟踪** - 记录资源的创建和最后访问时间
2. **基于配置的资源管理策略** - 不同类型资源具有不同的生命周期策略
3. **自动过期检测和清理** - 定期检查并释放过期资源
4. **内存压力感知** - 在内存紧张时主动释放低优先级资源
5. **资源优先级管理** - 确保重要资源优先保留
6. **统计和报告** - 提供资源使用情况的实时统计

## 关键组件

### ResourceTracker

`src/memory/resource_tracker.py` 是系统的核心，负责跟踪资源的创建、访问和释放。它支持：

- 资源注册和元数据管理
- 资源访问时间更新
- 过期资源检测
- 按类型、模式或优先级释放资源
- 资源使用统计收集

### 集成组件

系统与以下组件紧密集成：

1. **MemoryGuard** (`src/utils/memory_guard.py`) - 内存监控和保护
2. **DeviceManager** (`src/utils/device_manager.py`) - 设备资源分配
3. **ModelSwitcher** (`src/core/model_switcher.py`) - 模型动态切换
4. **ModelLoader** (`src/core/model_loader.py`) - 模型加载和管理

## 资源类型和策略

系统通过`configs/releasable_resources.yaml`配置文件管理不同资源类型的生命周期策略：

1. **model_shards** - 模型分片，优先级最高，5分钟未使用自动释放
2. **render_cache** - 渲染缓存，3分钟后释放，支持压缩
3. **temp_buffers** - 临时缓冲区，30秒后释放
4. **audio_cache** - 音频数据缓存，2分钟后释放
5. **model_weights_cache** - 模型权重，10分钟未使用自动卸载
6. **subtitle_index** - 字幕索引数据，15分钟未使用自动释放

## 内存监控和恢复

系统实现了多层内存监控：

- **常规监控** - 每5秒检查一次内存状态和过期资源
- **警告阈值** (75% 内存使用率) - 发出警告并释放过期资源
- **紧急阈值** (90% 内存使用率) - 触发紧急释放和量化调整
- **恢复策略** - 释放资源后，系统会预留512MB内存防止OOM，并支持渐进式重新加载

## 使用示例

可以通过`src/examples/resource_lifecycle_demo.py`查看系统演示：

```bash
# 运行完整演示
python src/examples/resource_lifecycle_demo.py --demo all

# 只测试资源创建和过期
python src/examples/resource_lifecycle_demo.py --demo creation

# 测试内存压力下的资源释放
python src/examples/resource_lifecycle_demo.py --demo pressure
```

## 开发说明

资源生命周期管理系统是VisionAI-ClipsMaster的核心功能之一，特别为在低配置设备上运行大型语言模型而设计。它通过智能管理内存资源，使应用能够在4GB内存的设备上处理复杂的短视频重构任务。

系统设计遵循以下原则：

1. **资源隔离** - 通过类型区分不同资源，独立管理生命周期
2. **最小必要资源** - 只保留必须的资源，其余自动释放
3. **优先级管理** - 在内存受限时，按优先级释放资源
4. **实时监控** - 持续监控内存压力，及时调整策略

这些功能共同确保了VisionAI-ClipsMaster能在资源受限环境中高效运行，将有限内存资源充分利用于关键任务。 