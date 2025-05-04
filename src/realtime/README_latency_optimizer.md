# 交互延迟优化器 (LagReducer)

## 功能概述

`LagReducer` 是一个交互延迟优化器组件，用于优化短剧混剪过程中的实时交互延迟。通过地理分布式缓存、智能路由和连接管理，提高系统响应速度，改善用户体验。该组件是VisionAI-ClipsMaster系统中实时交互优化的核心部分。

## 主要特性

- **地理分布式边缘节点**：根据用户地理位置选择最佳边缘节点，减少网络传输延迟
- **智能连接优化**：基于网络状况和用户位置动态优化连接参数
- **缓存管理**：提供高效的分布式缓存机制，加速数据访问
- **单例模式**：提供全局唯一的优化器实例，确保系统中的一致性
- **异步设计**：完全支持异步操作，适合高并发场景
- **自适应参数**：根据网络延迟和连接质量自动调整参数

## 组件结构

交互延迟优化器由两个主要类组成：

1. **GeoDistributedCache**：地理分布式缓存管理器
   - 管理多个边缘节点
   - 实现基于地理位置的最近节点选择
   - 提供高效的缓存存取机制

2. **LagReducer**：延迟优化器核心类
   - 管理用户连接参数优化
   - 协调边缘节点选择
   - 提供统计和监控功能

## 使用方法

### 获取实例

```python
from src.realtime import get_lag_reducer, initialize_lag_reducer

# 初始化（通常在应用启动时调用一次）
config = {...}  # 可选配置
lag_reducer = await initialize_lag_reducer(config)

# 在其他地方获取已初始化的实例
lag_reducer = get_lag_reducer()
```

### 优化用户连接

```python
async def handle_connection(session_id, user_location):
    lag_reducer = get_lag_reducer()
    
    # 优化用户连接
    optimization = await lag_reducer.optimize_connection(
        session_id=session_id,
        user_location=user_location  # 包含lat和lng的字典
    )
    
    # 使用优化参数配置连接
    connection_params = {
        "buffer_size": optimization["buffer_size"],
        "compression": optimization["compression"],
        "endpoint": optimization["edge_node"]
    }
    
    return connection_params
```

### 获取最近的边缘节点

```python
async def get_best_edge_node(user_location):
    lag_reducer = get_lag_reducer()
    
    # 获取用户最近的边缘节点
    edge_node = await lag_reducer.get_nearest_edge(user_location)
    
    return edge_node
```

### 监控延迟优化器状态

```python
def get_optimizer_stats():
    lag_reducer = get_lag_reducer()
    
    # 获取延迟优化器状态
    stats = lag_reducer.get_stats()
    
    return stats
```

## 配置文件

延迟优化器通过`configs/edge_cache.json`配置文件进行配置，主要参数包括：

```json
{
  "max_cache_size_mb": 200,
  "default_ttl": 7200,
  "edge_nodes": [
    {
      "id": "cn-east",
      "location": {"lat": 31.2304, "lng": 121.4737},
      "region": "华东",
      "endpoint": "https://east-cdn.example.com"
    },
    ...
  ],
  "connect_timeout": 2.0,
  "retry_count": 3
}
```

## 注意事项

1. 用户位置信息可能不总是可用，组件会在这种情况下自动使用合理的默认值
2. 边缘节点可能会暂时离线，组件会自动选择次优节点
3. 对于高频请求，应考虑复用优化结果，避免频繁查询

## 技术原理

### Haversine算法

组件使用Haversine公式计算两点间的地理距离，公式如下：

```
a = sin²(Δφ/2) + cos φ1 · cos φ2 · sin²(Δλ/2)
c = 2 · atan2(√a, √(1−a))
d = R · c
```

其中：
- φ是纬度，λ是经度（均为弧度）
- R是地球半径（约6371千米）

### 节点选择算法

节点选择基于多因素加权评分：
- 地理距离（50%权重）
- 节点健康状态（30%权重）
- 网络延迟（20%权重）

## 示例代码

查看`src/realtime/examples/latency_optimizer_example.py`获取完整示例。 