# 资源锁定机制 (Resource Locking)

## 概述

资源锁定机制是VisionAI-ClipsMaster系统的关键组件，负责确保在多线程环境下安全访问共享资源。在内存受限环境(4GB RAM/无GPU)下，高效的并发控制对系统的稳定性至关重要。该机制主要实现了读写锁模式，支持多读单写的并发控制策略。

## 设计原则

资源锁定系统的设计遵循以下原则：

1. **读写分离** - 允许多个读取操作同时进行，但写入操作需要独占
2. **超时自动释放** - 锁持有超过指定时间自动释放，防止死锁
3. **锁自动升降级** - 支持锁级别的升级(读→写)和降级(写→读)
4. **线程安全** - 所有操作都是线程安全的，适用于多线程环境
5. **死锁预防** - 通过超时机制和所有权验证防止死锁

## 主要功能

### 1. 读写锁模式

系统实现了标准的读写锁模式：

- **读锁（共享锁）** - 允许多个线程同时读取资源
- **写锁（排他锁）** - 只允许一个线程写入资源，且写入时不允许任何读取

```python
# 获取读锁
with read_locked("resource_id") as acquired:
    if acquired:
        # 安全读取资源
        read_resource()

# 获取写锁
with write_locked("resource_id") as acquired:
    if acquired:
        # 安全修改资源
        modify_resource()
```

### 2. 自动超时释放

系统会自动监控锁的持有状态，如果锁持有时间超过配置的超时时间（默认30秒），会自动释放锁：

```python
# 锁超时设置
lock_manager = get_resource_lock()
lock_manager.lock_timeout = 30  # 单位：秒
```

### 3. 锁升级和降级

系统支持锁的升级和降级：

- **锁升级** - 持有读锁的线程可以升级为写锁（如果没有其他读锁）
- **锁降级** - 持有写锁的线程可以自动获取读锁（写锁包含读锁的权限）

```python
# 锁升级示例
if acquire_read(res_id):
    # 读取操作
    # ...
    
    # 升级到写锁
    if acquire_write(res_id):
        # 写入操作
        # ...
        release_write(res_id)
    
    # 仍然持有读锁
    release_read(res_id)
```

### 4. 状态监控

系统提供了锁状态监控功能：

```python
# 获取所有锁的状态
lock_states = lock_manager.get_all_locks()
for lock in lock_states:
    print(f"资源: {lock['resource_id']}")
    print(f"读者数量: {lock['readers']}")
    print(f"写者数量: {lock['writers']}")
    print(f"是否锁定: {lock['is_locked']}")
```

## 系统组件

### 1. ReadWriteLock 类

底层的读写锁实现，提供以下功能：

- `acquire_read()` - 获取读锁
- `release_read()` - 释放读锁
- `acquire_write()` - 获取写锁
- `release_write()` - 释放写锁
- `get_status()` - 获取锁状态

### 2. ResourceLock 类

资源锁管理器，负责管理系统中各资源的锁状态：

- `acquire_read(res_id)` - 获取资源的读锁
- `release_read(res_id)` - 释放资源的读锁
- `acquire_write(res_id)` - 获取资源的写锁
- `release_write(res_id)` - 释放资源的写锁
- `read_lock(res_id)` - 读锁上下文管理器
- `write_lock(res_id)` - 写锁上下文管理器
- `get_all_locks()` - 获取所有锁的状态

### 3. 监控线程

系统包含一个后台监控线程，负责：

- 定期检查所有锁的状态
- 自动释放超时的锁
- 清理未使用的锁对象

## 使用方式

### 使用上下文管理器（推荐）

```python
from src.memory.lock_manager import read_locked, write_locked

# 读取资源
with read_locked("resource_id", timeout=5.0) as acquired:
    if acquired:
        # 安全读取资源
        read_resource()
    else:
        # 获取锁超时
        handle_timeout()

# 修改资源
with write_locked("resource_id", timeout=5.0) as acquired:
    if acquired:
        # 安全修改资源
        modify_resource()
    else:
        # 获取锁超时
        handle_timeout()
```

### 直接使用锁函数

```python
from src.memory.lock_manager import acquire_read, release_read, acquire_write, release_write

# 读取资源
if acquire_read("resource_id"):
    try:
        # 安全读取资源
        read_resource()
    finally:
        # 确保锁被释放
        release_read("resource_id")

# 修改资源
if acquire_write("resource_id"):
    try:
        # 安全修改资源
        modify_resource()
    finally:
        # 确保锁被释放
        release_write("resource_id")
```

### 获取锁管理器实例

```python
from src.memory.lock_manager import get_resource_lock

# 获取锁管理器单例
lock_manager = get_resource_lock()

# 修改超时配置
lock_manager.lock_timeout = 10  # 10秒超时

# 获取所有锁状态
lock_states = lock_manager.get_all_locks()
```

## 与其他组件的集成

### 与资源跟踪器集成

资源锁机制与资源跟踪器（ResourceTracker）紧密集成：

```python
from src.memory.resource_tracker import get_resource_tracker
from src.memory.lock_manager import write_locked

tracker = get_resource_tracker()

# 安全更新资源
with write_locked("resource_id") as acquired:
    if acquired:
        # 更新资源
        modify_resource()
        
        # 通知资源跟踪器资源被访问
        tracker.touch("resource_id")
```

### 与内存碎片整理器集成

在进行关键操作前，可以使用锁防止内存碎片整理器中断操作：

```python
from src.memory.defragmenter import get_memory_defragmenter
from src.memory.lock_manager import write_locked

# 在关键操作前锁定资源
with write_locked("critical_operation") as acquired:
    if acquired:
        # 执行不应被碎片整理中断的操作
        perform_critical_operation()
```

## 演示程序

系统提供了演示程序`src/examples/resource_lock_demo.py`，展示资源锁定机制的各种特性：

```bash
# 运行演示程序
python src/examples/resource_lock_demo.py
```

演示程序展示：
1. 基本的读写锁操作
2. 锁升级和降级
3. 自动超时释放
4. 并发环境下的锁竞争

## 锁定规则总结

1. **读操作：共享锁**
   - 多个读操作可以同时进行
   - 获取读锁时，如果有写锁或写请求，则会等待

2. **写操作：排他锁**
   - 写操作需要独占资源
   - 获取写锁时，需要等待所有读锁释放

3. **自动超时释放（最长30秒）**
   - 锁持有超过30秒自动释放
   - 可通过配置调整超时时间

4. **锁优先级**
   - 写操作优先级高于读操作
   - 当有写请求时，新的读请求会等待

## 最佳实践

1. **使用上下文管理器**
   - 推荐使用`read_locked`和`write_locked`上下文管理器
   - 确保锁总是被正确释放

2. **设置合理的超时时间**
   - 为每个锁操作设置合理的超时时间
   - 避免线程长时间等待锁

3. **避免锁嵌套**
   - 尽量避免在持有一个锁的同时获取另一个锁
   - 如需多个锁，按统一顺序获取，避免死锁

4. **锁粒度控制**
   - 保持锁的粒度尽可能小
   - 尽量减少锁持有的时间

5. **异常处理**
   - 确保在异常情况下锁也能被释放
   - 使用上下文管理器或try-finally结构

## 总结

资源锁定机制是VisionAI-ClipsMaster系统在多线程环境中保持资源安全访问的关键工具。通过读写锁模式和超时自动释放功能，系统在保证线程安全的同时，有效避免了死锁问题。该机制与资源生命周期管理系统紧密集成，确保系统在内存受限环境下的稳定运行。 