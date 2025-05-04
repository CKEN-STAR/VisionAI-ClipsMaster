# 全链路监控看板 (TelemetryDashboard)

## 功能概述

`TelemetryDashboard` 是一个提供全方位实时监控和性能指标收集的组件，它跟踪VisionAI-ClipsMaster系统的各个部分，收集连接情况、消息流量、延迟、错误和资源使用等核心指标。此组件支持多种监控后端，包括Prometheus和Grafana，提供实时可视化和告警功能。

## 主要特性

- **实时指标收集**: 收集WebSocket连接、消息流量、延迟和错误等关键指标
- **资源监控**: 追踪内存、CPU使用和队列负载
- **多后端支持**: 与Prometheus和Grafana等行业标准监控系统集成
- **自动告警**: 基于可配置的阈值自动触发告警
- **性能分析**: 提供延迟百分位数、错误率和带宽使用等详细统计信息
- **轻量级设计**: 低开销的指标收集，适合在生产环境运行
- **可扩展API**: 简单易用的API，便于与其他组件集成

## 组件结构

全链路监控看板由以下几个主要类组成：

1. **TelemetryDashboard**: 核心组件，管理所有监控功能
   - 收集和聚合各种性能指标
   - 提供监控数据的统一访问点
   - 管理指标的生命周期

2. **PrometheusClient**: Prometheus集成
   - 将指标导出为Prometheus格式
   - 支持自定义指标和标签
   - 提供查询接口获取当前值

3. **GrafanaIntegrator**: Grafana集成
   - 管理Grafana仪表盘和面板
   - 支持动态更新仪表盘
   - 提供数据源配置

## 监控指标

监控看板收集以下关键指标：

### 连接指标
- **活跃连接数**: 当前活跃WebSocket连接数
- **空闲连接数**: 当前空闲WebSocket连接数
- **总连接数**: 所有WebSocket连接总数

### 延迟指标
- **平均延迟**: 所有连接的平均延迟时间(毫秒)
- **最大延迟**: 最大延迟时间(毫秒)
- **最小延迟**: 最小延迟时间(毫秒)
- **P95延迟**: 95%请求的延迟时间(毫秒)
- **P99延迟**: 99%请求的延迟时间(毫秒)

### 消息指标
- **传入消息数**: 接收的消息总数
- **传出消息数**: 发送的消息总数
- **总消息数**: 所有消息总数

### 带宽指标
- **传入带宽**: 接收数据的总字节数
- **传出带宽**: 发送数据的总字节数
- **总带宽**: 所有数据传输的总字节数

### 错误指标
- **错误总数**: 所有错误的总数
- **各组件错误**: 按组件分类的错误数

### 会话指标
- **活跃会话数**: 当前活跃会话数
- **总会话数**: 所有会话总数

### 资源指标
- **内存使用**: 当前内存使用量(字节)
- **CPU使用率**: 当前CPU使用率(%)

### 队列指标
- **队列大小**: 各队列的当前大小

## 使用方法

### 初始化监控看板

```python
from src.realtime import initialize_telemetry_dashboard, get_telemetry_dashboard

# 初始化（通常在应用启动时调用一次）
dashboard = await initialize_telemetry_dashboard()

# 获取单例实例
dashboard = get_telemetry_dashboard()
```

### 记录连接指标

```python
# 更新连接计数
dashboard.update_connection_metrics(
    active=10,  # 活跃连接数
    idle=5      # 空闲连接数
)
```

### 记录延迟数据

```python
# 记录延迟时间
dashboard.record_latency(15.5)  # 15.5毫秒
```

### 记录消息数据

```python
# 记录消息
dashboard.record_message(
    direction="incoming",    # incoming或outgoing
    size_bytes=1024,         # 消息大小(字节)
    msg_type="data"          # 消息类型
)
```

### 记录错误

```python
# 记录错误
dashboard.record_error(
    component="websocket",   # 发生错误的组件
    severity="error"         # 错误严重程度(warning/error/critical)
)
```

### 更新会话和队列

```python
# 更新会话计数
dashboard.update_session_count(active=8, total=12)

# 更新队列大小
dashboard.update_queue_size("message_queue", 25)
```

### 获取实时指标数据

```python
# 获取所有指标的实时数据
metrics = dashboard.display_realtime_metrics()

print(f"活跃连接: {metrics['connections']['active']}")
print(f"平均延迟: {metrics['latency']['avg']}ms")
print(f"消息总数: {metrics['messages']['total']}")
```

## 配置选项

监控看板支持通过`configs/monitoring.json`文件进行配置，主要配置选项包括：

- **启用/禁用各种监控后端**
- **指定采样间隔和保留策略**
- **设置告警阈值**
- **配置Prometheus导出**
- **配置Grafana集成**
- **配置日志记录级别和格式**

配置示例：
```json
{
    "enabled": true,
    "sampling_interval_ms": 100,
    "prometheus": {
        "enabled": true,
        "port": 9090
    },
    "grafana": {
        "enabled": true,
        "url": "http://localhost:3000",
        "api_key": "your-api-key"
    },
    "alerts": {
        "enabled": true,
        "latency_threshold_ms": 1000,
        "error_rate_threshold": 0.05
    }
}
```

## 告警机制

监控看板支持基于阈值的告警机制，当指标超过预设阈值时会触发告警。告警可以通过以下方式发送：

- **日志记录**
- **电子邮件**
- **Prometheus AlertManager**

配置告警阈值：
```json
{
    "alerts": {
        "thresholds": {
            "high_latency_ms": 1000,
            "critical_latency_ms": 5000,
            "error_rate_warning": 0.05,
            "error_rate_critical": 0.1,
            "memory_warning_percent": 75,
            "memory_critical_percent": 90
        }
    }
}
```

## 集成示例

### 与现有系统集成

监控看板可以轻松集成到现有的实时通信组件中：

```python
from src.realtime import get_duplex_engine, get_telemetry_dashboard

# 获取监控看板和通信引擎
dashboard = get_telemetry_dashboard()
engine = get_duplex_engine()

# 设置消息钩子
original_send = engine.send_message

def instrumented_send(message, *args, **kwargs):
    start_time = time.time()
    result = original_send(message, *args, **kwargs)
    latency_ms = (time.time() - start_time) * 1000
    
    # 记录指标
    dashboard.record_message("outgoing", len(str(message)), message.type)
    dashboard.record_latency(latency_ms)
    
    return result

engine.send_message = instrumented_send
```

### 与Prometheus和Grafana集成

监控看板可以将指标导出到Prometheus，然后使用Grafana进行可视化：

1. 确保Prometheus和Grafana已安装并运行
2. 配置Prometheus抓取监控看板的指标端点
3. 在Grafana中创建仪表盘，使用Prometheus作为数据源
4. 添加各种图表展示不同的指标

## 示例

完整的使用示例可在`src/realtime/examples/monitoring_example.py`中找到，它展示了：

- 初始化监控看板
- 模拟WebSocket流量和消息
- 记录各种指标
- 定期显示监控摘要
- 配置与Prometheus/Grafana的集成 