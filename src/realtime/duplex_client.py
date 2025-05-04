#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
双工通信客户端

提供连接到双工通信服务器的客户端接口，支持WebSocket和gRPC通信方式。
"""

import os
import sys
import json
import asyncio
import logging
import uuid
import time
from typing import Dict, List, Any, Optional, Union, Callable, Awaitable
from enum import Enum
from dataclasses import dataclass
import threading

try:
    import websockets
except ImportError:
    websockets = None

try:
    import grpc
except ImportError:
    grpc = None

# 导入共享的消息类型定义
from src.realtime.duplex_engine import Message, MessageType, ProtocolType

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("duplex_client")

class DuplexClient:
    """双工通信客户端
    
    提供与双工通信服务器建立连接、发送和接收消息的功能。
    """
    
    def __init__(self, server_url: str, protocol_type: ProtocolType = ProtocolType.WEBSOCKET,
                 auto_reconnect: bool = True, max_reconnect_attempts: int = 5,
                 reconnect_delay: float = 2.0):
        """初始化双工通信客户端
        
        Args:
            server_url: 服务器URL，格式为"ws://host:port"或"grpc://host:port"
            protocol_type: 通信协议类型，默认为WebSocket
            auto_reconnect: 是否自动重连
            max_reconnect_attempts: 最大重连尝试次数
            reconnect_delay: 重连延迟(秒)
        """
        self.server_url = server_url
        self.protocol_type = protocol_type
        self.auto_reconnect = auto_reconnect
        self.max_reconnect_attempts = max_reconnect_attempts
        self.reconnect_delay = reconnect_delay
        
        # 连接状态
        self.connected = False
        self.connecting = False
        self.reconnect_attempts = 0
        
        # 会话信息
        self.session_id = None
        self.client_id = str(uuid.uuid4())
        
        # 连接对象
        self.connection = None
        
        # 消息处理回调
        self.message_callbacks: Dict[str, List[Callable[[Message], Awaitable[None]]]] = {}
        
        # 消息队列，用于暂存离线消息
        self.message_queue: List[Message] = []
        
        # 心跳和消息处理任务
        self.heartbeat_task = None
        self.receiver_task = None
        
        # 确保协议库已安装
        if protocol_type == ProtocolType.WEBSOCKET and websockets is None:
            raise ImportError("WebSocket协议需要安装websockets库")
        elif protocol_type == ProtocolType.GRPC and grpc is None:
            raise ImportError("gRPC协议需要安装grpc库")
    
    async def connect(self) -> bool:
        """连接到服务器
        
        Returns:
            bool: 连接是否成功
        """
        if self.connected or self.connecting:
            return self.connected
        
        self.connecting = True
        
        try:
            if self.protocol_type == ProtocolType.WEBSOCKET:
                await self._connect_websocket()
            elif self.protocol_type == ProtocolType.GRPC:
                await self._connect_grpc()
            else:
                raise ValueError(f"不支持的协议类型: {self.protocol_type}")
            
            # 连接成功后启动心跳和消息接收任务
            self._start_tasks()
            
            # 处理离线消息队列
            if self.message_queue:
                await self._process_message_queue()
            
            return True
            
        except Exception as e:
            logger.error(f"连接服务器失败: {str(e)}")
            
            if self.auto_reconnect and self.reconnect_attempts < self.max_reconnect_attempts:
                self.reconnect_attempts += 1
                logger.info(f"尝试重连 ({self.reconnect_attempts}/{self.max_reconnect_attempts})，{self.reconnect_delay}秒后...")
                await asyncio.sleep(self.reconnect_delay)
                self.connecting = False
                return await self.connect()
            
            self.connecting = False
            return False
    
    async def disconnect(self) -> None:
        """断开连接"""
        if not self.connected:
            return
        
        # 停止任务
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
            self.heartbeat_task = None
        
        if self.receiver_task:
            self.receiver_task.cancel()
            self.receiver_task = None
        
        # 断开连接
        if self.protocol_type == ProtocolType.WEBSOCKET and self.connection:
            await self.connection.close()
        elif self.protocol_type == ProtocolType.GRPC and self.connection:
            # gRPC连接关闭逻辑
            pass
        
        self.connection = None
        self.connected = False
        self.session_id = None
        logger.info("已断开与服务器的连接")
    
    async def send_message(self, action: str, data: Dict[str, Any],
                         message_type: MessageType = MessageType.REQUEST) -> Optional[str]:
        """发送消息到服务器
        
        Args:
            action: 消息动作
            data: 消息数据
            message_type: 消息类型，默认为请求类型
        
        Returns:
            Optional[str]: 消息ID，如果发送失败则返回None
        """
        # 创建消息
        message = Message(
            id=str(uuid.uuid4()),
            type=message_type,
            action=action,
            data=data,
            session_id=self.session_id
        )
        
        # 如果未连接，加入消息队列
        if not self.connected:
            self.message_queue.append(message)
            logger.debug(f"未连接到服务器，消息已加入队列: {action}")
            return message.id
        
        try:
            if self.protocol_type == ProtocolType.WEBSOCKET and self.connection:
                await self.connection.send(message.to_json())
                logger.debug(f"消息已发送: {action}")
                return message.id
            elif self.protocol_type == ProtocolType.GRPC and self.connection:
                # gRPC消息发送逻辑
                # 示例: self.connection.stream.write(message_pb)
                pass
            else:
                self.message_queue.append(message)
                logger.warning(f"无法发送消息，连接不可用: {action}")
        except Exception as e:
            logger.error(f"发送消息失败: {str(e)}")
            # 连接可能已断开，添加到队列
            self.message_queue.append(message)
            self.connected = False
            
            # 尝试重新连接
            if self.auto_reconnect:
                asyncio.create_task(self._reconnect())
        
        return message.id
    
    def register_callback(self, action: str, callback: Callable[[Message], Awaitable[None]]) -> None:
        """注册消息处理回调
        
        Args:
            action: 消息动作
            callback: 回调函数
        """
        if action not in self.message_callbacks:
            self.message_callbacks[action] = []
        
        self.message_callbacks[action].append(callback)
        logger.debug(f"已注册回调函数: {action}")
    
    def unregister_callback(self, action: str, callback: Callable[[Message], Awaitable[None]]) -> None:
        """注销消息处理回调
        
        Args:
            action: 消息动作
            callback: 回调函数
        """
        if action in self.message_callbacks and callback in self.message_callbacks[action]:
            self.message_callbacks[action].remove(callback)
            logger.debug(f"已注销回调函数: {action}")
    
    async def _connect_websocket(self) -> None:
        """连接WebSocket服务器"""
        try:
            self.connection = await websockets.connect(self.server_url)
            self.connected = True
            self.connecting = False
            self.reconnect_attempts = 0
            logger.info(f"已连接到WebSocket服务器: {self.server_url}")
            
            # 等待服务器发送欢迎消息，获取会话ID
            # 通常服务器会在连接建立后发送一个包含会话ID的消息
            try:
                message_str = await asyncio.wait_for(self.connection.recv(), timeout=5.0)
                message = Message.from_json(message_str)
                if message.action == "connection_established":
                    self.session_id = message.data.get("connection_id")
                    logger.info(f"会话已建立，ID: {self.session_id}")
            except asyncio.TimeoutError:
                logger.warning("等待会话ID超时")
            
        except Exception as e:
            self.connected = False
            self.connecting = False
            logger.error(f"连接WebSocket服务器失败: {str(e)}")
            raise
    
    async def _connect_grpc(self) -> None:
        """连接gRPC服务器"""
        # gRPC连接逻辑需要根据具体的proto定义来实现
        # 这里只提供框架
        
        # 示例: 
        # channel = grpc.aio.insecure_channel(self.server_url)
        # self.connection = MessageServiceStub(channel)
        # self.connected = True
        # self.connecting = False
        # self.reconnect_attempts = 0
        
        # 获取会话ID
        # ...
        
        logger.info("gRPC连接功能尚未完全实现")
        raise NotImplementedError("gRPC连接功能尚未完全实现")
    
    async def _reconnect(self) -> None:
        """重新连接到服务器"""
        if self.connecting:
            return
        
        logger.info("正在尝试重新连接...")
        await self.connect()
    
    def _start_tasks(self) -> None:
        """启动心跳和消息接收任务"""
        if self.heartbeat_task is None:
            self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        
        if self.receiver_task is None:
            self.receiver_task = asyncio.create_task(self._message_receiver_loop())
    
    async def _heartbeat_loop(self) -> None:
        """心跳循环"""
        while self.connected:
            try:
                await asyncio.sleep(30)  # 30秒发送一次心跳
                if self.connected:
                    await self.send_message(
                        action="heartbeat",
                        data={"timestamp": time.time()},
                        message_type=MessageType.HEARTBEAT
                    )
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"心跳消息发送失败: {str(e)}")
                # 连接可能已断开
                self.connected = False
                # 尝试重连
                if self.auto_reconnect:
                    await self._reconnect()
                break
    
    async def _message_receiver_loop(self) -> None:
        """消息接收循环"""
        if self.protocol_type == ProtocolType.WEBSOCKET:
            await self._websocket_receiver_loop()
        elif self.protocol_type == ProtocolType.GRPC:
            await self._grpc_receiver_loop()
    
    async def _websocket_receiver_loop(self) -> None:
        """WebSocket消息接收循环"""
        if not self.connection:
            return
        
        try:
            async for message_str in self.connection:
                try:
                    message = Message.from_json(message_str)
                    
                    # 处理心跳响应
                    if message.type == MessageType.HEARTBEAT:
                        continue
                    
                    # 处理其他消息
                    await self._handle_message(message)
                    
                except json.JSONDecodeError:
                    logger.warning(f"收到无效JSON消息: {message_str[:100]}")
                except Exception as e:
                    logger.error(f"处理消息时出错: {str(e)}")
        
        except websockets.exceptions.ConnectionClosed:
            logger.info("WebSocket连接已关闭")
        except Exception as e:
            logger.error(f"WebSocket接收循环出错: {str(e)}")
        finally:
            # 连接已断开
            self.connected = False
            
            # 尝试重连
            if self.auto_reconnect:
                await self._reconnect()
    
    async def _grpc_receiver_loop(self) -> None:
        """gRPC消息接收循环"""
        # gRPC接收逻辑需要根据具体的proto定义来实现
        # 这里只提供框架
        logger.info("gRPC消息接收功能尚未完全实现")
    
    async def _handle_message(self, message: Message) -> None:
        """处理接收到的消息"""
        logger.debug(f"收到消息: {message.action}")
        
        # 查找并调用对应的回调函数
        if message.action in self.message_callbacks:
            tasks = []
            for callback in self.message_callbacks[message.action]:
                tasks.append(callback(message))
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
        else:
            logger.debug(f"未找到消息处理回调: {message.action}")
    
    async def _process_message_queue(self) -> None:
        """处理离线消息队列"""
        if not self.message_queue:
            return
        
        logger.info(f"处理离线消息队列，共 {len(self.message_queue)} 条消息")
        
        queued_messages = self.message_queue.copy()
        self.message_queue.clear()
        
        for message in queued_messages:
            try:
                if self.protocol_type == ProtocolType.WEBSOCKET and self.connection:
                    await self.connection.send(message.to_json())
                    logger.debug(f"离线消息已发送: {message.action}")
                elif self.protocol_type == ProtocolType.GRPC and self.connection:
                    # gRPC消息发送逻辑
                    pass
            except Exception as e:
                logger.error(f"发送离线消息失败: {str(e)}")
                # 将消息添加回队列
                self.message_queue.append(message)
                # 连接可能已断开
                self.connected = False
                break


# 示例: 如何使用客户端
if __name__ == "__main__":
    async def main():
        # 创建客户端
        client = DuplexClient("ws://localhost:8765")
        
        # 注册消息处理回调
        async def handle_echo_response(message: Message):
            print(f"收到响应: {message.data}")
        
        client.register_callback("echo_response", handle_echo_response)
        
        # 连接服务器
        connected = await client.connect()
        if not connected:
            print("连接服务器失败")
            return
        
        # 发送消息
        await client.send_message("echo", {"text": "Hello, Server!"})
        
        # 等待一段时间接收响应
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("正在关闭...")
        finally:
            # 断开连接
            await client.disconnect()
    
    asyncio.run(main()) 