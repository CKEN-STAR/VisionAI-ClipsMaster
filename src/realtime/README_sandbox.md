# 交互沙盒隔离器 (InteractionSandbox)

## 功能概述

`InteractionSandbox` 是一个用于安全执行用户代码的组件，它通过隔离环境执行潜在不安全的代码，保护主应用程序免受恶意代码的影响。该组件支持两种隔离策略：基于Docker容器的完全隔离和基于子进程的轻量级隔离。

## 主要特性

- **安全执行代码**: 在隔离环境中执行用户提供的Python代码
- **双重隔离机制**: 支持Docker容器隔离和子进程隔离
- **资源限制**: 限制CPU、内存和执行时间，防止资源滥用
- **代码净化**: 自动移除危险操作和对敏感资源的访问
- **智能降级**: 在Docker不可用时自动降级使用子进程隔离
- **全面日志记录**: 记录所有执行活动，便于后期审计
- **优雅错误处理**: 捕获并处理所有执行错误，保证主应用稳定性

## 组件结构

交互沙盒隔离器由以下几个主要类组成：

1. **InteractionSandbox**: 主体类，提供统一的代码执行接口
   - 自动选择合适的隔离实现
   - 管理沙盒生命周期
   - 提供全局单例访问

2. **DockerSandbox**: 基于Docker容器的隔离实现
   - 提供最高级别的隔离安全性
   - 完全限制系统资源访问
   - 支持精细的资源限制

3. **SubprocessSandbox**: 基于子进程的隔离实现
   - 轻量级隔离，无需Docker
   - 适合Docker不可用的环境
   - 基于Python内置安全机制

4. **DockerManager**: Docker容器管理
   - 管理容器生命周期
   - 实现容器池复用
   - 处理容器级资源限制

## 使用方法

### 初始化交互沙盒隔离器

```python
from src.realtime import initialize_interaction_sandbox, get_interaction_sandbox

# 初始化（通常在应用启动时调用一次）
sandbox = await initialize_interaction_sandbox(
    timeout=30,  # 执行超时时间（秒）
    force_subprocess=False  # 是否强制使用子进程沙盒
)

# 获取单例实例
sandbox = get_interaction_sandbox()
```

### 安全执行代码

```python
# 执行代码片段
result = await sandbox.safe_execute("""
import math
import random

# 计算圆周率
def estimate_pi(n):
    inside = 0
    for _ in range(n):
        x, y = random.random(), random.random()
        if x*x + y*y <= 1:
            inside += 1
    return 4 * inside / n

print(f"圆周率估计: {estimate_pi(10000)}")
print(f"实际圆周率: {math.pi}")
""")

# 处理执行结果
if result["success"]:
    print("执行成功！")
    print(f"输出: {result['stdout']}")
else:
    print(f"执行失败: {result['stderr']}")
```

### 清理资源

```python
# 手动清理资源（通常在应用关闭时调用）
await sandbox.cleanup()
```

## 安全考虑

交互沙盒隔离器实现了多层安全防护：

1. **环境隔离**: Docker容器提供操作系统级隔离，子进程提供进程级隔离
2. **资源限制**: 限制CPU、内存、进程数和执行时间
3. **代码净化**: 移除危险模块导入和系统调用
4. **网络限制**: Docker容器默认禁用网络访问
5. **特权降级**: 在容器内使用非root用户执行代码
6. **超时控制**: 强制终止长时间运行的代码

## 配置选项

交互沙盒隔离器支持以下配置选项：

- **timeout**: 执行超时时间（秒）
- **force_subprocess**: 是否强制使用子进程沙盒
- **Docker配置**:
  - 内存限制: 默认512MB
  - CPU限制: 默认0.5核
  - 进程数限制: 默认50个进程

## 错误处理

交互沙盒隔离器设计为失败安全，即使在执行错误的情况下也不会影响主应用程序。所有错误都将被捕获并以结构化的方式返回，包括：

- 执行超时
- 资源耗尽
- 语法错误
- 运行时异常
- 系统级错误

## 示例

请参阅 `src/realtime/examples/sandbox_example.py` 获取完整的使用示例，包括：

- Docker沙盒测试
- 子进程沙盒测试
- 安全代码执行
- 不安全代码处理
- 资源密集型代码测试
- 无限循环处理

## 日志和监控

交互沙盒隔离器会记录详细的操作日志，包括：

- 沙盒初始化和清理
- 代码执行请求和结果
- 执行错误和异常
- 资源使用情况

所有日志都使用标准的日志级别，可以集成到应用程序的监控系统中。 