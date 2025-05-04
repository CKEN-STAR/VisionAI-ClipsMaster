#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
FastAPI双工通信集成模块

提供与FastAPI框架的集成，允许在FastAPI应用中添加WebSocket和HTTP双工通信能力。
"""

import os
import sys
import json
import asyncio
import logging
from typing import Dict, List, Any, Optional, Union, Callable, Awaitable
from datetime import datetime
import uuid
import time

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, Request, Response
from fastapi.routing import APIRouter
from fastapi.responses import JSONResponse, StreamingResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from pydantic import BaseModel, Field

from src.realtime.duplex_engine import (
    Message, 
    MessageType, 
    ProtocolType,
    get_duplex_engine,
    initialize_duplex_engine,
    shutdown_duplex_engine
)

from src.realtime.http_adapter import (
    HttpLongPollingAdapter,
    ServerSentEventsAdapter
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fastapi_duplex")

# ===================== Pydantic 模型 =====================

class ClientInfo(BaseModel):
    """客户端信息模型"""
    client_id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    client_type: str = "web"
    capabilities: Dict[str, Any] = Field(default_factory=dict)
    user_id: Optional[str] = None
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None

class MessageRequest(BaseModel):
    """消息请求模型"""
    action: str
    data: Dict[str, Any] = Field(default_factory=dict)
    type: Optional[str] = "request"

class SessionResponse(BaseModel):
    """会话响应模型"""
    session_id: str
    created_at: float
    expires_at: float
    client_id: Optional[str] = None

class MessageResponse(BaseModel):
    """消息响应模型"""
    message_id: str
    status: str = "success"
    timestamp: float = Field(default_factory=time.time)

class MessagesResponse(BaseModel):
    """消息列表响应模型"""
    messages: List[Dict[str, Any]] = Field(default_factory=list)
    count: int = 0

# ===================== 初始化函数 =====================

async def initialize_realtime(
    app: FastAPI, 
    protocols: Optional[List[ProtocolType]] = None,
    ws_host: str = "0.0.0.0", 
    ws_port: int = 8765,
    grpc_host: str = "0.0.0.0", 
    grpc_port: int = 50051,
    prefix: str = "/realtime",
    enable_http_adapters: bool = True
) -> None:
    """初始化实时通信模块并集成到FastAPI应用
    
    Args:
        app: FastAPI应用实例
        protocols: 要启用的协议列表，默认为WebSocket和gRPC
        ws_host: WebSocket主机地址
        ws_port: WebSocket端口
        grpc_host: gRPC主机地址
        grpc_port: gRPC端口
        prefix: API路由前缀
        enable_http_adapters: 是否启用HTTP适配器
    """
    # 初始化双工通信引擎
    await initialize_duplex_engine(
        protocols=protocols,
        ws_host=ws_host,
        ws_port=ws_port,
        grpc_host=grpc_host,
        grpc_port=grpc_port
    )
    
    # 添加启动和关闭事件处理器
    @app.on_event("shutdown")
    async def shutdown_event():
        await shutdown_duplex_engine()
        logger.info("双工通信引擎已关闭")
    
    # 如果启用HTTP适配器，则创建HTTP路由
    if enable_http_adapters:
        from src.realtime.http_adapter import initialize_http_adapters
        
        # 初始化HTTP适配器
        await initialize_http_adapters()
        
        # 创建路由
        router = APIRouter(prefix=prefix, tags=["realtime"])
        
        # 添加HTTP路由
        _add_http_routes(router)
        
        # 将路由添加到FastAPI应用
        app.include_router(router)
    
    # 添加WebSocket路由
    @app.websocket(f"{prefix}/ws")
    async def websocket_endpoint(websocket: WebSocket):
        """WebSocket端点
        
        用于直接连接到双工通信引擎的WebSocket端点。
        客户端可以通过此端点与服务器建立WebSocket连接。
        """
        # 接受连接
        await websocket.accept()
        
        # 获取客户端信息
        client_info = websocket.query_params.get("client_info", "{}")
        try:
            client_info = json.loads(client_info)
        except:
            client_info = {}
        
        # 生成会话ID
        session_id = str(uuid.uuid4())
        
        # 创建欢迎消息
        welcome_msg = Message(
            id=str(uuid.uuid4()),
            type=MessageType.NOTIFICATION,
            action="connection_established",
            data={"connection_id": session_id},
            session_id=session_id
        )
        
        # 发送欢迎消息
        await websocket.send_text(welcome_msg.to_json())
        
        # 获取引擎实例
        engine = get_duplex_engine()
        
        # 客户端连接后处理
        await _handle_client_connected(session_id, client_info)
        
        try:
            # 循环处理客户端消息
            while True:
                # 接收消息
                message_text = await websocket.receive_text()
                
                try:
                    # 解析消息
                    message = Message.from_json(message_text)
                    message.session_id = session_id
                    
                    # 处理心跳消息
                    if message.type == MessageType.HEARTBEAT:
                        await websocket.send_text(Message(
                            id=str(uuid.uuid4()),
                            type=MessageType.HEARTBEAT,
                            action="heartbeat_response",
                            data={"timestamp": time.time()},
                            session_id=session_id
                        ).to_json())
                        continue
                    
                    # 处理其他消息
                    action = message.action
                    if action:
                        await _process_message(message, session_id, websocket)
                
                except json.JSONDecodeError:
                    logger.warning(f"收到无效JSON消息: {message_text[:100]}")
                    await websocket.send_text(Message(
                        id=str(uuid.uuid4()),
                        type=MessageType.ERROR,
                        action="error",
                        data={"message": "无效的JSON消息"},
                        session_id=session_id
                    ).to_json())
                except Exception as e:
                    logger.error(f"处理消息时出错: {str(e)}")
                    await websocket.send_text(Message(
                        id=str(uuid.uuid4()),
                        type=MessageType.ERROR,
                        action="error",
                        data={"message": f"处理消息时出错: {str(e)}"},
                        session_id=session_id
                    ).to_json())
        
        except WebSocketDisconnect:
            logger.info(f"客户端断开连接: {session_id}")
            await _handle_client_disconnected(session_id)
        except Exception as e:
            logger.error(f"WebSocket连接出错: {str(e)}")
            await _handle_client_disconnected(session_id)

# ===================== 内部辅助函数 =====================

def _add_http_routes(router: APIRouter) -> None:
    """向路由器添加HTTP端点
    
    Args:
        router: FastAPI路由器
    """
    from src.realtime.http_adapter import long_polling_adapter, sse_adapter
    
    # 会话管理
    @router.post("/sessions", response_model=SessionResponse)
    async def create_session(client_info: ClientInfo):
        """创建新的会话"""
        # 处理客户端信息
        client_data = client_info.dict()
        
        # 创建会话
        session = await long_polling_adapter.create_session(client_data)
        session["client_id"] = client_info.client_id
        
        # 触发客户端连接事件
        await _handle_client_connected(session["session_id"], client_data)
        
        return session
    
    @router.delete("/sessions/{session_id}", response_model=dict)
    async def close_session(session_id: str):
        """关闭会话"""
        success = long_polling_adapter.close_session(session_id)
        
        if success:
            # 触发客户端断开连接事件
            await _handle_client_disconnected(session_id)
        
        return {"success": success}
    
    # 消息处理
    @router.post("/sessions/{session_id}/messages", response_model=MessageResponse)
    async def send_message(session_id: str, message: MessageRequest):
        """发送消息"""
        # 获取消息类型
        try:
            message_type = MessageType(message.type)
        except:
            message_type = MessageType.REQUEST
        
        # 发送消息
        message_id = await long_polling_adapter.send_message(
            session_id=session_id,
            action=message.action,
            data=message.data,
            message_type=message_type
        )
        
        if message_id is None:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {"message_id": message_id, "status": "success"}
    
    @router.get("/sessions/{session_id}/messages", response_model=MessagesResponse)
    async def poll_messages(session_id: str, timeout: Optional[float] = 30.0):
        """轮询消息"""
        messages = await long_polling_adapter.poll_messages(session_id, timeout)
        return {"messages": messages, "count": len(messages)}
    
    # Server-Sent Events
    @router.get("/sse/{session_id}")
    async def sse_endpoint(session_id: str, request: Request, events: Optional[str] = None):
        """SSE端点"""
        # 创建SSE会话(如果不存在)
        if session_id not in sse_adapter.sessions:
            await sse_adapter.create_session({"request": str(request.url)})
        
        # 解析事件类型
        event_types = events.split(',') if events else None
        
        return StreamingResponse(
            sse_adapter.subscribe(session_id, event_types),
            media_type="text/event-stream"
        )

async def _handle_client_connected(session_id: str, client_info: Dict[str, Any]) -> None:
    """处理客户端连接事件
    
    Args:
        session_id: 会话ID
        client_info: 客户端信息
    """
    # 获取引擎实例
    engine = get_duplex_engine()
    
    # 创建连接事件消息
    message = Message(
        id=str(uuid.uuid4()),
        type=MessageType.NOTIFICATION,
        action="client_connected",
        data={
            "session_id": session_id,
            "client_info": client_info,
            "timestamp": time.time()
        },
        session_id=session_id
    )
    
    # 广播客户端连接事件
    await engine.broadcast_message(message)
    logger.info(f"客户端连接: {session_id}")

async def _handle_client_disconnected(session_id: str) -> None:
    """处理客户端断开连接事件
    
    Args:
        session_id: 会话ID
    """
    # 获取引擎实例
    engine = get_duplex_engine()
    
    # 创建断开连接事件消息
    message = Message(
        id=str(uuid.uuid4()),
        type=MessageType.NOTIFICATION,
        action="client_disconnected",
        data={
            "session_id": session_id,
            "timestamp": time.time()
        }
    )
    
    # 广播客户端断开连接事件
    await engine.broadcast_message(message)
    logger.info(f"客户端断开连接: {session_id}")

async def _process_message(message: Message, session_id: str, websocket: WebSocket) -> None:
    """处理客户端消息
    
    Args:
        message: 消息对象
        session_id: 会话ID
        websocket: WebSocket连接
    """
    # 获取引擎实例
    engine = get_duplex_engine()
    
    # 如果有注册的回调，引擎会自动处理
    # 这里我们将消息转发给引擎
    engine_message = Message(
        id=message.id,
        type=message.type,
        action=message.action,
        data=message.data,
        session_id=session_id
    )
    
    # 处理特殊消息
    if message.action == "broadcast":
        # 广播消息
        await engine.broadcast_message(engine_message, exclude=[session_id])
    else:
        # 获取注册的回调数量
        callback_count = len(engine.message_callbacks.get(message.action, []))
        
        if callback_count == 0:
            # 如果没有回调处理此消息，发送默认响应
            await websocket.send_text(Message(
                id=f"response-{message.id}",
                type=MessageType.RESPONSE,
                action=f"{message.action}_response",
                data={
                    "status": "received",
                    "message": "消息已接收，但没有处理程序",
                    "original_action": message.action,
                    "timestamp": time.time()
                },
                session_id=session_id
            ).to_json())
        else:
            # 有处理程序，通过引擎处理
            await engine._handle_message(engine_message, session_id)

# ===================== 辅助函数 =====================

def create_duplex_middleware() -> BaseHTTPMiddleware:
    """创建双工通信中间件
    
    此中间件添加会话跟踪功能，可用于在HTTP请求之间跟踪客户端状态。
    
    Returns:
        BaseHTTPMiddleware: 中间件实例
    """
    
    class DuplexMiddleware(BaseHTTPMiddleware):
        def __init__(self, app: ASGIApp):
            super().__init__(app)
        
        async def dispatch(self, request: Request, call_next):
            # 从请求中获取会话ID
            session_id = request.cookies.get("duplex_session_id")
            
            # 调用下一个中间件或路由处理器
            response = await call_next(request)
            
            # 如果有会话ID，添加到响应Cookie
            if session_id:
                response.set_cookie("duplex_session_id", session_id, httponly=True)
            
            return response
    
    return DuplexMiddleware

# ===================== 示例 =====================

"""
# 示例：如何在FastAPI应用中使用此模块

from fastapi import FastAPI
import uvicorn
import asyncio

app = FastAPI(title="VisionAI双工通信示例")

# 添加中间件(可选)
app.add_middleware(create_duplex_middleware())

# 在应用启动时初始化实时通信
@app.on_event("startup")
async def startup_event():
    from src.realtime.fastapi_integration import initialize_realtime
    await initialize_realtime(app, prefix="/api/realtime")

# 示例路由
@app.get("/")
async def root():
    return {"message": "VisionAI双工通信示例"}

# 启动服务器
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
""" 