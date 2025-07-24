# 内存优化策略

## 概述

VisionAI-ClipsMaster的内存优化策略是一套根据设备性能动态调整内存使用的机制，确保应用在低端设备上也能流畅运行，同时在高端设备上充分利用可用资源。

## 核心组件

### 1. UIMemoryManager

内存管理器负责：
- 根据性能等级配置内存使用策略
- 管理图像缓存大小
- 优化垃圾回收频率
- 监控内存使用情况
- 在内存压力下执行清理

### 2. MemoryWatcher

内存监控器负责：
- 定期检查系统和应用内存使用
- 在内存使用超过阈值时发出警告
- 提供内存使用状态信息

## 性能等级适配

根据设备性能等级，内存优化策略提供不同级别的配置：

| 性能等级 | 缓存限制 | 垃圾回收间隔 | 垃圾回收阈值 | 监控频率 |
|---------|----------|------------|------------|---------|
| Low     | 50项     | 30秒        | (100,5,2)   | 5秒     |
| Medium  | 100项    | 60秒        | (700,10,5)  | 10秒    |
| High    | 200项    | 120秒       | (1000,15,10)| 15秒    |

## 内存压力处理

内存管理器会根据内存压力级别执行不同程度的清理：

1. **轻度清理（5%）**：定期执行的预防性清理
2. **中度清理（25%）**：当应用内存使用较高时执行
3. **积极清理（75%）**：当系统内存使用率超过警告阈值时执行
4. **紧急清理（100%）**：当系统内存使用率超过危险阈值时执行

## 集成方式

内存管理器与应用程序集成：

```python
# 初始化内存管理器
def init_memory_manager(self):
    # 创建内存管理器实例
    self.memory_manager = UIMemoryManager(self)
    
    # 确定性能等级并激活
    self.memory_manager.determine_tier()
    self.memory_manager.activate()
    
    # 创建内存监控器
    self.memory_watcher = MemoryWatcher(self)
    self.memory_watcher.memory_warning.connect(self.on_memory_warning)
    self.memory_watcher.start_monitoring()
```

## 优化策略

1. **缓存优化**：
   - 根据设备性能设置图像缓存大小
   - 优先清理不常用缓存

2. **垃圾回收优化**：
   - 根据设备性能调整垃圾回收阈值和频率
   - 低端设备：更积极的垃圾回收策略
   - 高端设备：保守的垃圾回收策略

3. **字体优化**：
   - 低端设备移除多余字体，仅保留核心字体
   - 减少字体占用的内存

4. **紧急恢复机制**：
   - 在内存危急时通知用户
   - 执行紧急清理
   - 必要时提示保存工作并重启应用

## 实现文件

- `ui/hardware/memory_manager.py`：内存管理器和监控器实现
- `simple_ui.py`：内存管理集成

## 配置项

内存优化策略的配置项位于`configs/system_settings.yaml`：

```yaml
resource_limits:
  max_memory_percent: 85        # 最大内存使用百分比
  max_cpu_percent: 90           # 最大CPU使用百分比
  emergency_save_threshold: 95  # 紧急保存阈值（内存百分比）
``` 