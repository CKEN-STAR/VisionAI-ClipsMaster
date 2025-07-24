# 自检容错系统

## 简介

自检容错系统是VisionAI-ClipsMaster的核心组件之一，提供全面的自我监控和错误恢复机制，确保应用在各种极端条件下仍能稳定运行。这对于在低资源环境（如4GB RAM/无GPU）下运行的系统尤为重要，因为此类环境更容易出现资源受限相关的问题。

本系统主要解决以下问题：
- 服务进程无响应或崩溃
- 关键线程异常停止
- 数据处理管道阻塞
- 缓冲区数据实时性丢失
- 系统资源耗尽
- 预警通道失效

## 架构设计

自检容错系统由以下核心组件组成：

1. **Watchdog（监视器）**：
   - 监控各个关键进程和线程的存活状态
   - 检测心跳超时并采取恢复措施
   - 提供线程注册和管理功能

2. **SystemSelfCheck（系统自检）**：
   - 提供可扩展的检查框架
   - 集成多种内置检查功能
   - 协调检查结果与恢复操作

3. **ComponentStatus（组件状态）**：
   - 定义组件状态级别（正常、警告、错误、严重）
   - 提供状态管理和转换功能

4. **CheckResult（检查结果）**：
   - 封装检查结果和详细信息
   - 提供结果序列化功能

## 主要功能

### 1. 线程监控

监控关键线程的存活状态，在检测到线程停止时自动重启：

```python
from src.monitor.self_check import get_self_check

# 获取全局自检实例
self_check = get_self_check()

# 注册线程到监视器
self_check.watchdog.register_thread(
    "worker_thread",  # 线程名称
    worker_thread,    # 线程对象
    restart_worker    # 重启函数
)
```

### 2. 心跳检测

通过心跳机制确保服务正常运行：

```python
# 在关键线程或循环中更新心跳
self_check.watchdog.heartbeat()

# 检查服务是否活跃
if not self_check.watchdog.check_alive():
    # 处理服务无响应情况
    pass
```

### 3. 自定义检查

扩展自检系统，添加应用特定的检查：

```python
# 定义自定义检查
def check_database_connection() -> CheckResult:
    try:
        # 检查数据库连接
        if not database.is_connected():
            return CheckResult(
                ComponentStatus.ERROR,
                "数据库连接已断开",
                {"db_host": database.host}
            )
        return CheckResult(ComponentStatus.NORMAL, "数据库连接正常")
    except Exception as e:
        return CheckResult(
            ComponentStatus.ERROR,
            f"检查数据库连接时出错: {e}",
            {"exception": str(e)}
        )

# 注册自定义检查
self_check.register_check("database", check_database_connection)
```

### 4. 恢复处理

自定义恢复操作，处理检查发现的问题：

```python
# 定义恢复处理器
def reconnect_database(check_name: str, details: Dict[str, Any]) -> bool:
    try:
        # 重新连接数据库
        database.reconnect()
        return database.is_connected()
    except Exception as e:
        logger.error(f"重新连接数据库失败: {e}")
        return False

# 注册恢复处理器
self_check.register_recovery("reconnect_db", reconnect_database)
```

### 5. 运行诊断

执行系统诊断，获取全面的状态报告：

```python
# 运行所有检查
results = self_check.run_all_checks()

# 处理检查结果
for name, result in results.items():
    if result.status == ComponentStatus.ERROR:
        logger.error(f"检查 '{name}' 失败: {result.message}")
    elif result.status == ComponentStatus.WARNING:
        logger.warning(f"检查 '{name}' 警告: {result.message}")
```

## 集成指南

### 基本集成

最简单的集成方式是使用全局自检实例：

```python
from src.monitor.self_check import start_self_check, stop_self_check

# 应用启动时
self_check = start_self_check()

# 在关键线程中更新心跳
self_check.watchdog.heartbeat()

# 应用退出时
stop_self_check()
```

### 高级集成

对于需要更多定制的场景，可以创建自定义的自检实例：

```python
from src.monitor.self_check import SystemSelfCheck

# 创建自定义自检实例
self_check = SystemSelfCheck()

# 注册应用特定的检查
self_check.register_check("app_health", check_app_health)
self_check.register_check("worker_threads", check_worker_threads)

# 注册应用特定的恢复处理器
self_check.register_recovery("restart_workers", restart_workers)

# 启动自检系统
self_check.start()

# 应用退出时
self_check.stop()
```

## 配置选项

自检容错系统提供以下配置选项：

### Watchdog选项

- `check_interval`：检查间隔时间（秒）

```python
# 创建自定义检查间隔的监视器
watchdog = Watchdog(check_interval=10.0)  # 10秒检查一次
```

### 自检系统选项

自检系统使用内部Watchdog的配置选项，可以通过创建时指定：

```python
# 创建自定义自检系统
self_check = SystemSelfCheck(check_interval=5.0)
```

## 最佳实践

1. **集成到应用生命周期**：
   - 在应用启动时启动自检系统
   - 在应用关闭时停止自检系统

2. **定期更新心跳**：
   - 在关键循环或线程中定期调用`heartbeat()`
   - 推荐的心跳间隔为监视器检查间隔的1/2或更短

3. **注册关键线程**：
   - 确保所有关键线程都已注册到监视器
   - 提供适当的重启函数以自动恢复

4. **添加应用特定检查**：
   - 针对应用核心功能添加自定义检查
   - 确保检查执行效率高，不会导致性能问题

5. **优先级处理**：
   - 按重要性顺序处理检查结果
   - 对严重问题优先采取恢复措施

## 示例

### 基本使用示例

```python
import time
from src.monitor.self_check import start_self_check

# 启动自检系统
self_check = start_self_check()

# 主循环
while running:
    try:
        # 业务逻辑
        process_data()
        
        # 更新心跳
        self_check.watchdog.heartbeat()
        
    except Exception as e:
        logger.error(f"处理数据异常: {e}")
    
    time.sleep(0.1)
```

### 高级使用示例

参考示例脚本：`src/examples/self_check_demo.py`

## 常见问题

1. **自检逻辑过重导致性能问题**
   - 降低检查频率
   - 简化检查逻辑
   - 使用异步检查方法

2. **误报或过度干预**
   - 调整检查阈值和条件
   - 使用多次确认后再触发恢复

3. **资源消耗过高**
   - 设置更长的检查间隔
   - 减少非关键检查
   - 在资源紧张时自动降级检查频率

4. **循环重启问题**
   - 实现重启计数和退避策略
   - 设置最大重启次数
   - 添加联级恢复策略

## 性能注意事项

- 自检系统本身也会消耗系统资源，要避免过于频繁的检查
- 对于低资源设备，推荐设置较长的检查间隔（5-10秒）
- 优化检查逻辑，减少执行时间和资源消耗

## 参考资料

- 完整API文档请参考源代码注释
- 查看示例脚本：`src/examples/self_check_demo.py`
- 测试用例：`tests/monitor_test/self_check_test.py` 