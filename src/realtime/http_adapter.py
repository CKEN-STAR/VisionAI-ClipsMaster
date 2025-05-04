#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
HTTP适配器

提供HTTP长轮询和Server-Sent Events适配，便于将双工通信集成到现有HTTP API。
"""

import os
import json
import asyncio
import logging
import time
from typing import Dict, List, Any, Optional, Callable, Awaitable
from queue import Queue, Empty
import threading
import uuid

# 导入共享的消息类型定义
from src.realtime.duplex_engine import (
    Message, 
    MessageType, 
    ProtocolType,
    get_duplex_engine
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("http_adapter")

class HttpLongPollingAdapter:
    """HTTP长轮询适配器
    
    支持将双工通信转换为HTTP长轮询方式，便于客户端集成。
    客户端可以通过定期轮询获取消息。
    """
    
    def __init__(self, session_timeout: int = 3600):
        """初始化HTTP长轮询适配器
        
        Args:
            session_timeout: 会话超时时间(秒)，默认1小时
        """
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.session_timeout = session_timeout
        self.engine = get_duplex_engine()
        
        # 启动会话清理任务
        self._cleanup_task = None
    
    async def initialize(self):
        """初始化适配器"""
        # 启动会话清理任务
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_sessions())
    
    async def create_session(self, client_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """创建新的会话
        
        Args:
            client_info: 客户端信息
            
        Returns:
            Dict: 会话信息
        """
        session_id = str(uuid.uuid4())
        client_info = client_info or {}
        
        # 创建会话
        self.sessions[session_id] = {
            "id": session_id,
            "created_at": time.time(),
            "last_active": time.time(),
            "client_info": client_info,
            "message_queue": Queue(),
            "is_polling": False
        }
        
        logger.info(f"创建新会话: {session_id}")
        
        # 注册消息处理回调
        self._register_session_callbacks(session_id)
        
        return {
            "session_id": session_id,
            "created_at": self.sessions[session_id]["created_at"],
            "expires_at": self.sessions[session_id]["created_at"] + self.session_timeout
        }
    
    def close_session(self, session_id: str) -> bool:
        """关闭会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            bool: 是否成功关闭
        """
        if session_id not in self.sessions:
            return False
        
        # 从会话列表中移除
        session = self.sessions.pop(session_id)
        logger.info(f"关闭会话: {session_id}")
        
        return True
    
    async def send_message(self, session_id: str, action: str, data: Dict[str, Any],
                          message_type: MessageType = MessageType.REQUEST) -> Optional[str]:
        """发送消息
        
        Args:
            session_id: 会话ID
            action: 消息动作
            data: 消息数据
            message_type: 消息类型
            
        Returns:
            Optional[str]: 消息ID，失败时返回None
        """
        if session_id not in self.sessions:
            logger.warning(f"会话不存在: {session_id}")
            return None
        
        # 更新会话活动时间
        self.sessions[session_id]["last_active"] = time.time()
        
        # 创建消息
        message = Message(
            id=str(uuid.uuid4()),
            type=message_type,
            action=action,
            data=data,
            session_id=session_id
        )
        
        # 使用双工引擎发送消息
        # 注意: 这里将消息传递给了双工引擎，对方会基于注册的回调函数来处理消息
        await self.engine.broadcast_message(message)
        
        return message.id
    
    async def poll_messages(self, session_id: str, timeout: float = 30.0) -> List[Dict[str, Any]]:
        """轮询消息
        
        Args:
            session_id: 会话ID
            timeout: 超时时间(秒)
            
        Returns:
            List[Dict[str, Any]]: 消息列表
        """
        if session_id not in self.sessions:
            logger.warning(f"会话不存在: {session_id}")
            return []
        
        # 更新会话活动时间
        session = self.sessions[session_id]
        session["last_active"] = time.time()
        session["is_polling"] = True
        
        messages = []
        queue = session["message_queue"]
        
        # 立即获取现有消息
        while not queue.empty():
            try:
                message = queue.get_nowait()
                messages.append(message.to_dict())
                queue.task_done()
            except Empty:
                break
        
        # 如果没有消息且超时时间大于0，则等待新消息
        if not messages and timeout > 0:
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    # 使用短超时轮询，以便定期检查会话状态
                    message = await asyncio.to_thread(queue.get, True, 1.0)
                    messages.append(message.to_dict())
                    queue.task_done()
                    break  # 获取到一条消息就返回
                except Empty:
                    # 检查会话是否仍然有效
                    if session_id not in self.sessions:
                        break
                except Exception as e:
                    logger.error(f"轮询消息时出错: {str(e)}")
                    break
        
        session["is_polling"] = False
        return messages
    
    def _register_session_callbacks(self, session_id: str) -> None:
        """为会话注册消息处理回调
        
        Args:
            session_id: 会话ID
        """
        # 这里简单地将所有消息都放入会话的消息队列
        # 在实际应用中，可能需要更复杂的消息路由逻辑
        async def handle_message(message: Message, source_session_id: str) -> None:
            # 忽略来自自己的消息
            if source_session_id == session_id:
                return
                
            # 检查会话是否存在
            if session_id not in self.sessions:
                return
                
            # 将消息添加到会话的消息队列
            self.sessions[session_id]["message_queue"].put(message)
        
        # 注册全局消息处理回调
        # 这是一个简化的实现，实际应用中通常需要更精确的消息路由
        for action in ["*"]:  # 处理所有类型的消息
            self.engine.register_callback(action, handle_message)
    
    async def _cleanup_sessions(self) -> None:
        """定期清理过期会话"""
        while True:
            try:
                now = time.time()
                # 找出过期的会话
                expired_sessions = [
                    session_id for session_id, session in self.sessions.items()
                    if now - session["last_active"] > self.session_timeout
                ]
                
                # 关闭过期会话
                for session_id in expired_sessions:
                    self.close_session(session_id)
                
                if expired_sessions:
                    logger.info(f"已清理 {len(expired_sessions)} 个过期会话")
                
                # 每分钟检查一次
                await asyncio.sleep(60)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"清理会话时出错: {str(e)}")
                await asyncio.sleep(60)


class ServerSentEventsAdapter:
    """服务器发送事件(SSE)适配器
    
    支持将双工通信转换为SSE方式，便于Web客户端集成。
    客户端可以通过单个HTTP连接接收服务器推送的消息。
    """
    
    def __init__(self, session_timeout: int = 3600):
        """初始化SSE适配器
        
        Args:
            session_timeout: 会话超时时间(秒)，默认1小时
        """
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.session_timeout = session_timeout
        self.engine = get_duplex_engine()
        
        # 启动会话清理任务
        self._cleanup_task = None
    
    async def initialize(self):
        """初始化适配器"""
        # 启动会话清理任务
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_sessions())
    
    async def create_session(self, client_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """创建新的会话
        
        Args:
            client_info: 客户端信息
            
        Returns:
            Dict: 会话信息
        """
        session_id = str(uuid.uuid4())
        client_info = client_info or {}
        
        # 创建会话
        self.sessions[session_id] = {
            "id": session_id,
            "created_at": time.time(),
            "last_active": time.time(),
            "client_info": client_info,
            "message_queues": {},  # 按事件类型分组的消息队列
            "connections": set()   # 活动的SSE连接
        }
        
        logger.info(f"创建新SSE会话: {session_id}")
        
        return {
            "session_id": session_id,
            "created_at": self.sessions[session_id]["created_at"],
            "expires_at": self.sessions[session_id]["created_at"] + self.session_timeout
        }
    
    def close_session(self, session_id: str) -> bool:
        """关闭会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            bool: 是否成功关闭
        """
        if session_id not in self.sessions:
            return False
        
        # 从会话列表中移除
        session = self.sessions.pop(session_id)
        logger.info(f"关闭SSE会话: {session_id}")
        
        return True
    
    async def send_message(self, session_id: str, action: str, data: Dict[str, Any],
                          message_type: MessageType = MessageType.NOTIFICATION) -> Optional[str]:
        """发送消息
        
        Args:
            session_id: 会话ID
            action: 消息动作
            data: 消息数据
            message_type: 消息类型
            
        Returns:
            Optional[str]: 消息ID，失败时返回None
        """
        if session_id not in self.sessions:
            logger.warning(f"SSE会话不存在: {session_id}")
            return None
        
        # 更新会话活动时间
        self.sessions[session_id]["last_active"] = time.time()
        
        # 创建消息
        message = Message(
            id=str(uuid.uuid4()),
            type=message_type,
            action=action,
            data=data,
            session_id=session_id
        )
        
        # 使用双工引擎发送消息
        await self.engine.broadcast_message(message)
        
        return message.id
    
    async def subscribe(self, session_id: str, event_types: List[str] = None):
        """订阅SSE事件
        
        这个方法会返回一个异步生成器，用于生成SSE事件。
        
        Args:
            session_id: 会话ID
            event_types: 事件类型列表，为空则订阅所有事件
            
        Yields:
            str: SSE格式的事件数据
        """
        if session_id not in self.sessions:
            logger.warning(f"SSE会话不存在: {session_id}")
            yield f"event: error\ndata: {json.dumps({'error': 'Session not found'})}\n\n"
            return
        
        # 更新会话活动时间
        session = self.sessions[session_id]
        session["last_active"] = time.time()
        
        # 创建消息队列
        queue = asyncio.Queue()
        connection_id = str(uuid.uuid4())
        session["connections"].add(connection_id)
        
        # 注册消息处理回调
        callback_remove_funcs = self._register_session_callbacks(session_id, queue, event_types)
        
        try:
            # 发送初始连接成功消息
            yield f"event: connected\ndata: {json.dumps({'session_id': session_id, 'connection_id': connection_id})}\n\n"
            
            # 持续监听消息队列并生成SSE事件
            while session_id in self.sessions:
                try:
                    # 使用超时等待，以便定期检查会话状态
                    message = await asyncio.wait_for(queue.get(), timeout=30.0)
                    
                    # 格式化为SSE事件
                    event_name = message.action
                    event_data = json.dumps(message.to_dict())
                    yield f"event: {event_name}\ndata: {event_data}\n\n"
                    
                    queue.task_done()
                except asyncio.TimeoutError:
                    # 发送保持连接的注释
                    yield f": keepalive {time.time()}\n\n"
                except Exception as e:
                    logger.error(f"处理SSE事件时出错: {str(e)}")
                    yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
                    break
        finally:
            # 清理连接和回调
            if session_id in self.sessions:
                session["connections"].discard(connection_id)
            
            # 移除事件处理回调
            for remove_func in callback_remove_funcs:
                remove_func()
    
    def _register_session_callbacks(self, session_id: str, queue: asyncio.Queue, 
                                 event_types: List[str] = None) -> List[Callable]:
        """为会话注册消息处理回调
        
        Args:
            session_id: 会话ID
            queue: 消息队列
            event_types: 事件类型列表，为空则订阅所有事件
            
        Returns:
            List[Callable]: 回调移除函数列表
        """
        event_types = event_types or ["*"]  # 为空则处理所有类型的消息
        remove_funcs = []
        
        async def handle_message(message: Message, source_session_id: str) -> None:
            # 检查是否应该处理该消息
            if "*" not in event_types and message.action not in event_types:
                return
                
            # 将消息添加到队列
            await queue.put(message)
        
        # 注册回调
        for action in event_types:
            self.engine.register_callback(action, handle_message)
            # 创建对应的移除函数
            remove_funcs.append(lambda: self.engine.unregister_callback(action, handle_message))
            
        return remove_funcs
    
    async def _cleanup_sessions(self) -> None:
        """定期清理过期会话"""
        while True:
            try:
                now = time.time()
                # 找出过期的会话
                expired_sessions = [
                    session_id for session_id, session in self.sessions.items()
                    if now - session["last_active"] > self.session_timeout and not session["connections"]
                ]
                
                # 关闭过期会话
                for session_id in expired_sessions:
                    self.close_session(session_id)
                
                if expired_sessions:
                    logger.info(f"已清理 {len(expired_sessions)} 个过期SSE会话")
                
                # 每分钟检查一次
                await asyncio.sleep(60)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"清理SSE会话时出错: {str(e)}")
                await asyncio.sleep(60)


# 创建适配器实例
long_polling_adapter = HttpLongPollingAdapter()
sse_adapter = ServerSentEventsAdapter()

async def initialize_http_adapters():
    """初始化HTTP适配器"""
    await long_polling_adapter.initialize()
    await sse_adapter.initialize()
    logger.info("HTTP适配器已初始化")

# 示例: 如何在Flask中使用适配器
"""
from flask import Flask, jsonify, request, Response
import json

app = Flask(__name__)

@app.route('/api/sessions', methods=['POST'])
async def create_session():
    client_info = request.json or {}
    session = await long_polling_adapter.create_session(client_info)
    return jsonify(session)

@app.route('/api/sessions/<session_id>', methods=['DELETE'])
def close_session(session_id):
    success = long_polling_adapter.close_session(session_id)
    return jsonify({"success": success})

@app.route('/api/sessions/<session_id>/messages', methods=['POST'])
async def send_message(session_id):
    data = request.json or {}
    action = data.get('action', 'message')
    message_data = data.get('data', {})
    message_id = await long_polling_adapter.send_message(session_id, action, message_data)
    return jsonify({"message_id": message_id})

@app.route('/api/sessions/<session_id>/messages', methods=['GET'])
async def poll_messages(session_id):
    timeout = float(request.args.get('timeout', 30.0))
    messages = await long_polling_adapter.poll_messages(session_id, timeout)
    return jsonify({"messages": messages})

@app.route('/api/sse/<session_id>', methods=['GET'])
async def sse_stream(session_id):
    event_types = request.args.get('events')
    event_types = event_types.split(',') if event_types else None
    
    async def event_stream():
        async for event in sse_adapter.subscribe(session_id, event_types):
            yield event
    
    return Response(event_stream(), mimetype='text/event-stream')

if __name__ == '__main__':
    import asyncio
    from hypercorn.asyncio import serve
    from hypercorn.config import Config
    
    async def main():
        await initialize_http_adapters()
        config = Config()
        config.bind = ["0.0.0.0:5000"]
        await serve(app, config)
    
    asyncio.run(main())
""" 