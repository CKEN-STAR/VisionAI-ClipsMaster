#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
双工通信协议Echo服务器示例

演示如何使用双工通信协议引擎创建一个简单的Echo服务器。
客户端发送消息，服务器将相同的消息返回给客户端。
"""

import os
import sys
import asyncio
import json
import logging
from datetime import datetime

# 将项目根目录添加到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from src.realtime.duplex_engine import (
    Message, 
    MessageType, 
    ProtocolType,
    initialize_duplex_engine,
    get_duplex_engine,
    shutdown_duplex_engine
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("echo_server")

# 全局变量存储连接的客户端
connected_clients = set()

# 处理echo消息
async def handle_echo(message: Message, session_id: str):
    """处理echo消息并回复"""
    logger.info(f"收到来自 {session_id} 的消息: {message.action}")
    logger.info(f"消息内容: {message.data}")
    
    # 创建响应消息
    response = Message(
        id=f"echo-{message.id}",
        type=MessageType.RESPONSE,
        action="echo_response",
        data={
            "original_message": message.data.get("text", ""),
            "timestamp": datetime.now().isoformat(),
            "client_id": session_id
        },
        session_id=session_id
    )
    
    # 获取引擎实例
    engine = get_duplex_engine()
    
    # 向客户端发送响应
    await engine.send_message(response, session_id)
    logger.info(f"已向客户端 {session_id} 发送响应")

# 处理客户端连接
async def handle_connection_established(message: Message, session_id: str):
    """处理新的客户端连接"""
    logger.info(f"新客户端连接: {session_id}")
    connected_clients.add(session_id)
    
    # 创建欢迎消息
    welcome = Message(
        id=f"welcome-{message.id}",
        type=MessageType.NOTIFICATION,
        action="welcome",
        data={
            "message": "欢迎使用Echo服务器!",
            "server_time": datetime.now().isoformat(),
            "client_count": len(connected_clients)
        },
        session_id=session_id
    )
    
    # 获取引擎实例
    engine = get_duplex_engine()
    
    # 向客户端发送欢迎消息
    await engine.send_message(welcome, session_id)
    
    # 广播有新客户端连接的消息
    broadcast = Message(
        id=f"broadcast-{message.id}",
        type=MessageType.NOTIFICATION,
        action="client_joined",
        data={
            "client_id": session_id,
            "client_count": len(connected_clients),
            "timestamp": datetime.now().isoformat()
        }
    )
    
    # 向除新客户端外的所有客户端广播
    await engine.broadcast_message(broadcast, exclude=[session_id])

async def main():
    """主函数"""
    logger.info("启动Echo服务器...")
    
    # 初始化双工通信引擎
    await initialize_duplex_engine(
        protocols=[ProtocolType.WEBSOCKET],
        ws_host="0.0.0.0",
        ws_port=8765
    )
    
    # 获取引擎实例
    engine = get_duplex_engine()
    
    # 注册消息处理回调
    engine.register_callback("echo", handle_echo)
    engine.register_callback("connection_established", handle_connection_established)
    
    logger.info("Echo服务器已启动，监听 ws://0.0.0.0:8765")
    logger.info("按Ctrl+C停止服务器")
    
    try:
        # 保持服务器运行
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("正在关闭服务器...")
    finally:
        # 关闭引擎
        await shutdown_duplex_engine()
        logger.info("服务器已关闭")

if __name__ == "__main__":
    asyncio.run(main()) 