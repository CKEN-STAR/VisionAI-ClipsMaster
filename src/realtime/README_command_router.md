# 交互式命令路由器 (Command Router)

## 概述

交互式命令路由器是VisionAI-ClipsMaster系统的核心组件之一，负责处理客户端发送的各种命令请求，将命令路由到相应的处理器，并返回处理结果。该模块与实时通信引擎(Duplex Engine)和会话管理器(Session Manager)集成，提供了一套完整的命令处理框架。

## 核心功能

- **命令路由**：根据命令类型将请求路由到相应的处理器
- **命令处理**：提供标准化的命令处理流程
- **权限管理**：支持基于会话的权限检查
- **命令结果封装**：统一的命令执行结果返回格式
- **命令历史记录**：支持撤销/重做等历史操作管理

## 架构设计

命令路由器采用以下核心组件设计：

1. **CommandHandler**：命令处理器基类，所有具体命令处理器都继承自此类
2. **CommandResult**：命令执行结果，包含状态、数据和错误信息
3. **CommandRouter**：主路由器，负责注册处理器和分发命令
4. **内置处理器**：系统预置了几个基础命令处理器
   - EditCommandHandler：处理编辑操作
   - CollaborationHandler：处理协作交互
   - UndoStackManager：管理操作历史

## 命令处理流程

1. 客户端发送命令消息到服务器
2. 双工通信引擎接收消息并传递给命令路由器
3. 命令路由器根据消息类型找到对应的处理器
4. 处理器执行相应的命令并返回结果
5. 命令路由器将结果封装为响应消息返回给客户端

## 使用方式

### 初始化命令路由器

在应用启动时初始化命令路由器：

```python
from src.realtime import initialize_command_router

# 初始化命令路由器
initialize_command_router()
```

### 创建自定义命令处理器

创建自定义命令处理器需要继承CommandHandler基类：

```python
from src.realtime import CommandHandler, CommandResult

class MyCustomHandler(CommandHandler):
    """自定义命令处理器"""
    
    def __init__(self):
        super().__init__()
        self.command_name = "custom"
        self.description = "自定义命令处理器"
        self.help_text = "用于处理特定业务逻辑"
        self.required_permissions = {"custom_permission"}
    
    async def process(self, session_id: str, command: Dict[str, Any]) -> CommandResult:
        """处理命令"""
        try:
            # 执行业务逻辑
            # ...
            
            return CommandResult.success({"result": "success"}, "命令执行成功")
        except Exception as e:
            return CommandResult.error("命令执行失败", error=e)
    
    def validate(self, command: Dict[str, Any]) -> bool:
        """验证命令参数"""
        # 检查必要参数
        required_fields = ["param1", "param2"]
        return all(field in command for field in required_fields)
```

### 注册自定义命令处理器

```python
from src.realtime import get_command_router

# 获取命令路由器实例
router = get_command_router()

# 注册自定义处理器
router.register_handler("custom", MyCustomHandler())
```

### 发送和处理命令

从客户端发送命令：

```python
# 客户端代码
async def send_command():
    client = DuplexClient()
    await client.connect()
    
    # 发送自定义命令
    await client.send_message(
        action="custom",
        data={
            "param1": "value1",
            "param2": "value2"
        },
        message_type=MessageType.REQUEST
    )
```

服务端通过命令路由器接收并处理：

```python
# 命令路由器自动处理接收到的命令
# 无需额外代码
```

## 内置命令处理器

### 编辑命令 (edit)

处理文本或内容的编辑操作。

**命令参数：**
- `operation`: 操作类型（create, update, delete）
- `target`: 操作目标
- `content`: 内容数据

**使用示例：**
```python
command = {
    "type": "edit",
    "operation": "update",
    "target": "document.txt",
    "content": "新的文档内容"
}
```

### 协作命令 (collab)

处理多用户协作交互。

**命令参数：**
- `action`: 协作动作（share, join, leave）
- `resource`: 协作资源
- `users`: 目标用户列表

**使用示例：**
```python
command = {
    "type": "collab",
    "action": "share",
    "resource": "document.txt",
    "users": ["user1", "user2"]
}
```

### 撤销/重做命令 (undo)

管理操作历史，支持撤销和重做。

**命令参数：**
- `action`: 操作类型（undo, redo, add, clear）
- `context`: 上下文标识
- `operation`: 要添加的操作（仅add时需要）

**使用示例：**
```python
# 添加操作到历史
command = {
    "type": "undo",
    "action": "add",
    "context": "editor",
    "operation": {
        "type": "insert",
        "position": 10,
        "text": "插入的文本"
    }
}

# 撤销上一步操作
command = {
    "type": "undo",
    "action": "undo",
    "context": "editor"
}
```

## 客户端集成

命令路由器设计与客户端无关，可以支持多种客户端类型的接入：

1. **浏览器客户端**：通过WebSocket连接发送命令
2. **移动客户端**：通过HTTP长轮询或WebSocket发送命令
3. **桌面客户端**：通过WebSocket或gRPC发送命令
4. **其他服务**：通过gRPC或HTTP API发送命令

## 安全性考虑

命令路由器实现了基于会话的权限控制，确保只有具有适当权限的用户才能执行特定命令。权限检查在命令路由阶段进行，避免未授权访问。

## 扩展建议

1. **命令批处理**：支持批量命令执行
2. **命令调度优先级**：为命令添加优先级排序
3. **命令执行超时**：添加命令执行时间限制
4. **命令执行指标**：记录命令执行效率和统计信息
5. **命令依赖关系**：支持命令之间的依赖执行 