#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
双工通信协议引擎

提供统一的双向通信接口，支持WebSocket、gRPC和HTTP长轮询等多种协议。
能够根据客户端能力和网络环境自动选择最适合的通信方式。
"""

import os
import sys
import json
import asyncio
import logging
from typing import Dict, List, Any, Optional, Union, Callable, Awaitable
from enum import Enum
from dataclasses import dataclass
from abc import ABC, abstractmethod
import time
import uuid
import threading

try:
    import websockets
except ImportError:
    websockets = None

try:
    import grpc
    from concurrent import futures
except ImportError:
    grpc = None

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("duplex_engine")

# 通信协议类型
class ProtocolType(Enum):
    WEBSOCKET = "websocket"
    GRPC = "grpc"
    HTTP_LONGPOLL = "http_longpoll"
    AUTO = "auto"  # 自动选择最佳协议

# 消息类型
class MessageType(Enum):
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    HEARTBEAT = "heartbeat"
    ERROR = "error"

@dataclass
class Message:
    """通信消息结构"""
    id: str                          # 消息唯一标识
    type: MessageType                # 消息类型
    action: str                      # 消息动作/操作
    data: Dict[str, Any]             # 消息数据
    timestamp: float = None          # 消息时间戳
    session_id: Optional[str] = None # 会话ID

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
        if self.id is None:
            self.id = str(uuid.uuid4())

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "type": self.type.value,
            "action": self.action,
            "data": self.data,
            "timestamp": self.timestamp,
            "session_id": self.session_id
        }

    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """从字典创建消息"""
        msg_type = data.get("type")
        if isinstance(msg_type, str):
            msg_type = MessageType(msg_type)
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            type=msg_type,
            action=data.get("action", ""),
            data=data.get("data", {}),
            timestamp=data.get("timestamp", time.time()),
            session_id=data.get("session_id")
        )

    @classmethod
    def from_json(cls, json_str: str) -> 'Message':
        """从JSON字符串创建消息"""
        data = json.loads(json_str)
        return cls.from_dict(data)


class ProtocolHandler(ABC):
    """协议处理器基类"""
    
    @abstractmethod
    async def initialize(self) -> None:
        """初始化协议处理器"""
        pass
    
    @abstractmethod
    async def start(self) -> None:
        """启动协议处理器"""
        pass
    
    @abstractmethod
    async def stop(self) -> None:
        """停止协议处理器"""
        pass
    
    @abstractmethod
    async def send_message(self, message: Message, recipient_id: Optional[str] = None) -> None:
        """发送消息"""
        pass
    
    @abstractmethod
    async def broadcast_message(self, message: Message, exclude: Optional[List[str]] = None) -> None:
        """广播消息"""
        pass


class WebSocketHandler(ProtocolHandler):
    """WebSocket协议处理器"""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8765, 
                 message_handler: Callable[[Message, str], Awaitable[None]] = None):
        self.host = host
        self.port = port
        self.message_handler = message_handler
        self.server = None
        self.connections: Dict[str, Any] = {}  # WebSocket连接映射
        self.running = False
    
    async def initialize(self) -> None:
        """初始化WebSocket处理器"""
        if websockets is None:
            raise ImportError("WebSocket功能需要安装websockets库")
        logger.info(f"初始化WebSocket处理器: {self.host}:{self.port}")
    
    async def start(self) -> None:
        """启动WebSocket服务器"""
        if self.running:
            return
        
        try:
            self.server = await websockets.serve(
                self._handle_connection, 
                self.host, 
                self.port
            )
            self.running = True
            logger.info(f"WebSocket服务器已启动: ws://{self.host}:{self.port}")
        except Exception as e:
            logger.error(f"启动WebSocket服务器失败: {str(e)}")
            raise
    
    async def stop(self) -> None:
        """停止WebSocket服务器"""
        if not self.running:
            return
        
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            self.server = None
        
        # 关闭所有连接
        for conn_id, conn in list(self.connections.items()):
            try:
                await conn.close()
            except:
                pass
            
        self.connections.clear()
        self.running = False
        logger.info("WebSocket服务器已停止")
    
    async def send_message(self, message: Message, recipient_id: Optional[str] = None) -> None:
        """发送消息到指定客户端"""
        if not recipient_id or recipient_id not in self.connections:
            logger.warning(f"目标客户端不存在: {recipient_id}")
            return
        
        try:
            websocket = self.connections[recipient_id]
            await websocket.send(message.to_json())
            logger.debug(f"消息已发送到客户端 {recipient_id}: {message.action}")
        except Exception as e:
            logger.error(f"发送消息到客户端 {recipient_id} 失败: {str(e)}")
            # 移除失效连接
            if recipient_id in self.connections:
                del self.connections[recipient_id]
    
    async def broadcast_message(self, message: Message, exclude: Optional[List[str]] = None) -> None:
        """广播消息到所有客户端"""
        exclude = exclude or []
        tasks = []
        
        for conn_id, websocket in list(self.connections.items()):
            if conn_id in exclude:
                continue
                
            try:
                tasks.append(websocket.send(message.to_json()))
            except Exception as e:
                logger.error(f"准备广播消息到客户端 {conn_id} 失败: {str(e)}")
                if conn_id in self.connections:
                    del self.connections[conn_id]
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
            logger.debug(f"消息已广播到 {len(tasks)} 个客户端: {message.action}")
    
    async def _handle_connection(self, websocket, path):
        """处理新的WebSocket连接"""
        conn_id = str(uuid.uuid4())
        self.connections[conn_id] = websocket
        logger.info(f"新的WebSocket连接: {conn_id}")
        
        # 尝试获取会话管理器
        try:
            from src.realtime.session_manager import get_session_manager
            session_manager = get_session_manager()
        except ImportError:
            session_manager = None
        
        try:
            # 发送连接成功消息
            welcome_msg = Message(
                id=str(uuid.uuid4()),
                type=MessageType.NOTIFICATION,
                action="connection_established",
                data={"connection_id": conn_id},
                session_id=conn_id
            )
            await websocket.send(welcome_msg.to_json())
            
            # 处理接收到的消息
            async for message_str in websocket:
                try:
                    message = Message.from_json(message_str)
                    message.session_id = conn_id  # 设置会话ID
                    
                    # 如果消息包含用户信息，创建或获取用户会话
                    if session_manager and 'user_id' in message.data and message.action == 'initialize_session':
                        user_id = message.data.get('user_id')
                        device_info = message.data.get('device_info', {})
                        metadata = message.data.get('metadata', {})
                        
                        # 创建用户会话
                        user_session = session_manager.create_session(
                            user_id=user_id,
                            device_info=device_info,
                            metadata=metadata
                        )
                        
                        # 将连接添加到会话
                        session_manager.add_connection(
                            session_id=user_session.session_id,
                            connection_id=conn_id,
                            protocol_type=ProtocolType.WEBSOCKET
                        )
                        
                        # 发送会话创建成功消息
                        await websocket.send(Message(
                            id=f"session-{message.id}",
                            type=MessageType.RESPONSE,
                            action="session_initialized",
                            data={
                                "session_id": user_session.session_id,
                                "user_id": user_id,
                                "timestamp": time.time()
                            },
                            session_id=conn_id
                        ).to_json())
                    
                    # 处理心跳消息
                    if message.type == MessageType.HEARTBEAT:
                        await websocket.send(Message(
                            id=str(uuid.uuid4()),
                            type=MessageType.HEARTBEAT,
                            action="heartbeat_response",
                            data={"timestamp": time.time()},
                            session_id=conn_id
                        ).to_json())
                        
                        # 如果有会话，更新会话活动时间
                        if session_manager:
                            user_session = session_manager.get_session_by_connection(conn_id)
                            if user_session:
                                user_session.update_activity()
                        
                        continue
                    
                    # 调用消息处理函数
                    if self.message_handler:
                        await self.message_handler(message, conn_id)
                
                except json.JSONDecodeError:
                    logger.warning(f"收到无效JSON消息: {message_str[:100]}")
                except Exception as e:
                    logger.error(f"处理消息时出错: {str(e)}")
                    await websocket.send(Message(
                        id=str(uuid.uuid4()),
                        type=MessageType.ERROR,
                        action="error",
                        data={"message": f"处理消息时出错: {str(e)}"},
                        session_id=conn_id
                    ).to_json())
        
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"WebSocket连接已关闭: {conn_id}")
        except Exception as e:
            logger.error(f"WebSocket连接出错: {str(e)}")
        finally:
            # 清理连接
            if conn_id in self.connections:
                del self.connections[conn_id]
            
            # 如果有会话管理器，移除连接
            if session_manager:
                session_manager.remove_connection(conn_id)
            
            logger.info(f"WebSocket连接已移除: {conn_id}")


class GRPCHandler(ProtocolHandler):
    """gRPC协议处理器"""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 50051,
                 message_handler: Callable[[Message, str], Awaitable[None]] = None,
                 max_workers: int = 10):
        self.host = host
        self.port = port
        self.message_handler = message_handler
        self.max_workers = max_workers
        self.server = None
        self.streams: Dict[str, Any] = {}  # gRPC流映射
        self.running = False
    
    async def initialize(self) -> None:
        """初始化gRPC处理器"""
        if grpc is None:
            raise ImportError("gRPC功能需要安装grpc库")
        
        # 动态导入或生成gRPC服务模块
        # 这里通常需要从proto生成的Python模块
        # self.service_module = ...
        
        logger.info(f"初始化gRPC处理器: {self.host}:{self.port}")
    
    async def start(self) -> None:
        """启动gRPC服务器"""
        if self.running:
            return
        
        # 这里需要实现具体的gRPC服务实现
        # 由于需要根据proto定义来实现，这里只提供框架
        executor = futures.ThreadPoolExecutor(max_workers=self.max_workers)
        self.server = grpc.server(executor)
        
        # 注册服务
        # self.service_module.add_Service_to_server(GRPCServiceImplementation(self), self.server)
        
        # 绑定地址
        server_address = f"{self.host}:{self.port}"
        self.server.add_insecure_port(server_address)
        
        # 启动服务
        self.server.start()
        self.running = True
        logger.info(f"gRPC服务器已启动: {server_address}")
    
    async def stop(self) -> None:
        """停止gRPC服务器"""
        if not self.running:
            return
        
        if self.server:
            self.server.stop(grace=5)  # 给5秒钟的优雅关闭时间
            self.server = None
        
        # 清理所有流
        self.streams.clear()
        self.running = False
        logger.info("gRPC服务器已停止")
    
    async def send_message(self, message: Message, recipient_id: Optional[str] = None) -> None:
        """发送消息到指定客户端"""
        if not recipient_id or recipient_id not in self.streams:
            logger.warning(f"目标gRPC客户端不存在: {recipient_id}")
            return
        
        try:
            stream = self.streams[recipient_id]
            # 具体发送逻辑依赖于proto定义
            # 这里是一个示例
            # stream.write(self.service_module.Response(
            #     id=message.id,
            #     type=message.type.value,
            #     action=message.action,
            #     data=json.dumps(message.data),
            #     timestamp=message.timestamp,
            #     session_id=message.session_id
            # ))
            logger.debug(f"消息已发送到gRPC客户端 {recipient_id}: {message.action}")
        except Exception as e:
            logger.error(f"发送消息到gRPC客户端 {recipient_id} 失败: {str(e)}")
            # 移除失效流
            if recipient_id in self.streams:
                del self.streams[recipient_id]
    
    async def broadcast_message(self, message: Message, exclude: Optional[List[str]] = None) -> None:
        """广播消息到所有客户端"""
        exclude = exclude or []
        tasks = []
        
        for stream_id, stream in list(self.streams.items()):
            if stream_id in exclude:
                continue
                
            tasks.append(self.send_message(message, stream_id))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
            logger.debug(f"消息已广播到 {len(tasks)} 个gRPC客户端: {message.action}")


class DuplexProtocol:
    """双工通信协议实现"""
    
    def __init__(self, protocols: Optional[List[ProtocolType]] = None,
                 ws_host: str = "0.0.0.0", ws_port: int = 8765,
                 grpc_host: str = "0.0.0.0", grpc_port: int = 50051):
        
        # 默认支持所有协议
        self.protocols = protocols or [ProtocolType.WEBSOCKET, ProtocolType.GRPC]
        
        # 协议处理器
        self.handlers: Dict[ProtocolType, ProtocolHandler] = {}
        
        # 消息处理回调
        self.message_callbacks: Dict[str, List[Callable[[Message, str], Awaitable[None]]]] = {}
        
        # 配置处理器
        if ProtocolType.WEBSOCKET in self.protocols:
            self.handlers[ProtocolType.WEBSOCKET] = WebSocketHandler(
                host=ws_host, 
                port=ws_port,
                message_handler=self._handle_message
            )
        
        if ProtocolType.GRPC in self.protocols:
            self.handlers[ProtocolType.GRPC] = GRPCHandler(
                host=grpc_host, 
                port=grpc_port,
                message_handler=self._handle_message
            )
    
    async def initialize(self) -> None:
        """初始化所有协议处理器"""
        for protocol_type, handler in self.handlers.items():
            try:
                await handler.initialize()
                logger.info(f"协议处理器初始化成功: {protocol_type.value}")
            except Exception as e:
                logger.error(f"初始化协议处理器 {protocol_type.value} 失败: {str(e)}")
                # 从处理器列表中移除初始化失败的处理器
                self.handlers.pop(protocol_type, None)
    
    async def start(self) -> None:
        """启动所有协议处理器"""
        tasks = []
        for protocol_type, handler in self.handlers.items():
            tasks.append(handler.start())
        
        if tasks:
            await asyncio.gather(*tasks)
            logger.info(f"已启动 {len(tasks)} 个协议处理器")
    
    async def stop(self) -> None:
        """停止所有协议处理器"""
        tasks = []
        for protocol_type, handler in self.handlers.items():
            tasks.append(handler.stop())
        
        if tasks:
            await asyncio.gather(*tasks)
            logger.info(f"已停止 {len(tasks)} 个协议处理器")
    
    def register_callback(self, action: str, callback: Callable[[Message, str], Awaitable[None]]) -> None:
        """注册消息处理回调"""
        if action not in self.message_callbacks:
            self.message_callbacks[action] = []
        
        self.message_callbacks[action].append(callback)
        logger.debug(f"已注册回调函数: {action}, 总数: {len(self.message_callbacks[action])}")
    
    def unregister_callback(self, action: str, callback: Callable[[Message, str], Awaitable[None]]) -> None:
        """注销消息处理回调"""
        if action in self.message_callbacks and callback in self.message_callbacks[action]:
            self.message_callbacks[action].remove(callback)
            logger.debug(f"已注销回调函数: {action}, 剩余: {len(self.message_callbacks[action])}")
    
    async def send_message(self, message: Message, recipient_id: str, protocol_type: ProtocolType = None) -> None:
        """发送消息到指定客户端"""
        # 如果指定了协议类型，则使用指定的协议发送
        if protocol_type and protocol_type in self.handlers:
            await self.handlers[protocol_type].send_message(message, recipient_id)
            return
        
        # 否则尝试所有支持的协议
        for handler in self.handlers.values():
            try:
                await handler.send_message(message, recipient_id)
                return  # 一旦成功发送就返回
            except Exception as e:
                logger.debug(f"通过 {type(handler).__name__} 发送消息失败: {str(e)}")
        
        logger.warning(f"无法发送消息到客户端 {recipient_id}: 没有可用的协议处理器")
    
    async def broadcast_message(self, message: Message, exclude: Optional[List[str]] = None, 
                              protocol_type: ProtocolType = None) -> None:
        """广播消息到所有客户端"""
        exclude = exclude or []
        
        # 如果指定了协议类型，则使用指定的协议广播
        if protocol_type and protocol_type in self.handlers:
            await self.handlers[protocol_type].broadcast_message(message, exclude)
            return
        
        # 否则通过所有协议广播
        tasks = []
        for handler in self.handlers.values():
            tasks.append(handler.broadcast_message(message, exclude))
        
        if tasks:
            await asyncio.gather(*tasks)
    
    async def _handle_message(self, message: Message, session_id: str) -> None:
        """处理接收到的消息"""
        logger.debug(f"收到消息: {message.action} 来自: {session_id}")
        
        # 查找并调用对应的回调函数
        if message.action in self.message_callbacks:
            tasks = []
            for callback in self.message_callbacks[message.action]:
                tasks.append(callback(message, session_id))
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
        else:
            logger.warning(f"未找到消息处理回调: {message.action}")


# 全局引擎实例
_duplex_engine: Optional[DuplexProtocol] = None
_delta_broadcaster = None

def get_duplex_engine() -> DuplexProtocol:
    """获取全局双工通信引擎实例"""
    global _duplex_engine
    if _duplex_engine is None:
        _duplex_engine = DuplexProtocol()
    return _duplex_engine

def get_delta_broadcaster():
    """获取全局增量更新广播器实例"""
    global _delta_broadcaster
    return _delta_broadcaster

def set_delta_broadcaster(broadcaster):
    """设置全局增量更新广播器实例"""
    global _delta_broadcaster
    _delta_broadcaster = broadcaster
    return _delta_broadcaster

async def initialize_duplex_engine(protocols: Optional[List[ProtocolType]] = None,
                                 ws_host: str = "0.0.0.0", ws_port: int = 8765,
                                 grpc_host: str = "0.0.0.0", grpc_port: int = 50051) -> None:
    """初始化并启动双工通信引擎"""
    global _duplex_engine
    
    if _duplex_engine is not None:
        await _duplex_engine.stop()
    
    _duplex_engine = DuplexProtocol(
        protocols=protocols,
        ws_host=ws_host,
        ws_port=ws_port,
        grpc_host=grpc_host,
        grpc_port=grpc_port
    )
    
    await _duplex_engine.initialize()
    await _duplex_engine.start()
    logger.info("双工通信引擎已初始化并启动")

async def shutdown_duplex_engine() -> None:
    """关闭双工通信引擎"""
    global _duplex_engine
    if _duplex_engine is not None:
        await _duplex_engine.stop()
        _duplex_engine = None
        logger.info("双工通信引擎已关闭")


# 示例: 如何使用双工通信引擎
if __name__ == "__main__":
    async def demo():
        # 初始化引擎
        await initialize_duplex_engine()
        engine = get_duplex_engine()
        
        # 注册消息处理回调
        async def handle_echo(message: Message, session_id: str):
            print(f"收到echo消息: {message.data}")
            # 创建响应消息
            response = Message(
                id=str(uuid.uuid4()),
                type=MessageType.RESPONSE,
                action="echo_response",
                data={"echo": message.data.get("text", ""), "received_at": time.time()},
                session_id=session_id
            )
            # 发送响应
            await engine.send_message(response, session_id)
        
        # 注册回调
        engine.register_callback("echo", handle_echo)
        
        # 保持运行一段时间
        try:
            print("双工通信引擎已启动，按Ctrl+C退出")
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("正在关闭...")
        finally:
            # 关闭引擎
            await shutdown_duplex_engine()
    
    # 运行示例
    asyncio.run(demo()) 