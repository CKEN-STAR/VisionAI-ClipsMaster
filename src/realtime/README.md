# VisionAI-ClipsMaster 双工通信协议引擎

双工通信协议引擎是 VisionAI-ClipsMaster 的实时通信模块，提供高性能、灵活的双向通信功能。该模块支持多种通信协议，使客户端和服务器能够进行实时数据交换，实现交互式的用户体验。

## 功能特点

- **多协议支持**：同时支持 WebSocket、gRPC 和 HTTP 长轮询，根据客户端能力自动选择最适合的协议
- **统一的消息格式**：所有协议共享相同的消息结构，简化开发
- **自动重连**：客户端断线自动重连机制
- **消息可靠性**：支持离线消息队列和消息确认
- **心跳检测**：自动维持连接活跃
- **广播功能**：支持向指定客户端或所有客户端广播消息
- **事件回调**：基于事件的处理模型，扩展灵活
- **易于集成**：提供与 FastAPI、Flask 等主流框架的集成

## 组件结构

- `duplex_engine.py`：核心引擎，处理所有通信协议
- `duplex_client.py`：客户端实现，提供连接、发送和接收消息功能
- `http_adapter.py`：HTTP 长轮询和 Server-Sent Events 适配器
- `fastapi_integration.py`：FastAPI 框架集成
- `proto/`：Protocol Buffers 定义，用于 gRPC 通信
- `examples/`：示例代码和使用演示

## 快速开始

### 安装依赖

```bash
pip install websockets grpcio grpcio-tools pydantic
```

### 服务器端使用示例

```python
import asyncio
from src.realtime import (
    Message, 
    MessageType, 
    ProtocolType,
    initialize_duplex_engine,
    get_duplex_engine
)

# 处理 echo 消息的回调函数
async def handle_echo(message, session_id):
    print(f"收到消息: {message.data}")
    
    # 创建响应
    response = Message(
        id=str(uuid.uuid4()),
        type=MessageType.RESPONSE,
        action="echo_response",
        data={"echo": message.data.get("text", "")},
        session_id=session_id
    )
    
    # 发送响应
    engine = get_duplex_engine()
    await engine.send_message(response, session_id)

async def main():
    # 初始化引擎
    await initialize_duplex_engine(
        protocols=[ProtocolType.WEBSOCKET, ProtocolType.GRPC],
        ws_port=8765,
        grpc_port=50051
    )
    
    # 获取引擎实例
    engine = get_duplex_engine()
    
    # 注册消息处理回调
    engine.register_callback("echo", handle_echo)
    
    # 保持服务器运行
    while True:
        await asyncio.sleep(1)

# 运行服务器
asyncio.run(main())
```

### 客户端使用示例

```python
import asyncio
from src.realtime import DuplexClient, ProtocolType

# 处理响应的回调函数
async def handle_echo_response(message):
    print(f"收到响应: {message.data}")

async def main():
    # 创建客户端
    client = DuplexClient(
        server_url="ws://localhost:8765",
        protocol_type=ProtocolType.WEBSOCKET
    )
    
    # 注册响应处理回调
    client.register_callback("echo_response", handle_echo_response)
    
    # 连接到服务器
    connected = await client.connect()
    if not connected:
        print("连接失败")
        return
        
    # 发送消息
    await client.send_message(
        action="echo",
        data={"text": "Hello, world!"}
    )
    
    # 等待响应
    await asyncio.sleep(2)
    
    # 断开连接
    await client.disconnect()

# 运行客户端
asyncio.run(main())
```

### 与 FastAPI 集成

```python
from fastapi import FastAPI
import asyncio

app = FastAPI(title="VisionAI 双工通信示例")

# 在应用启动时初始化实时通信
@app.on_event("startup")
async def startup_event():
    from src.realtime.fastapi_integration import initialize_realtime
    await initialize_realtime(app, prefix="/api/realtime")

# API 路由
@app.get("/")
async def root():
    return {"message": "双工通信引擎已启动"}
```

## 消息格式

所有通信使用统一的消息格式：

```json
{
  "id": "消息唯一ID",
  "type": "request|response|notification|heartbeat|error",
  "action": "消息动作/事件类型",
  "data": {
    "key1": "value1",
    "key2": "value2"
  },
  "timestamp": 1620000000.123,
  "session_id": "会话ID"
}
```

## 性能考虑

- WebSocket 适合大多数客户端，尤其是浏览器环境
- gRPC 适合服务器间通信和性能要求高的场景
- HTTP 长轮询作为不支持 WebSocket 环境的后备方案
- 心跳间隔可根据网络环境和业务需求调整
- 对于高并发场景，建议使用消息队列进行扩展

## 安全考虑

- 生产环境应启用 TLS/SSL 加密
- 实现适当的认证和授权机制
- 限制消息大小和频率，防止 DoS 攻击
- 敏感数据应该额外加密

## 扩展性

双工通信引擎设计为可扩展的模块化系统：

- 添加新的协议处理器只需继承 `ProtocolHandler` 类
- 消息路由基于事件注册，可根据需要动态添加
- 适配器模式允许与不同的 Web 框架集成
- 可以集成外部消息队列系统进行横向扩展 