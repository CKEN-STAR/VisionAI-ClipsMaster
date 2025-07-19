#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
实时会话管理器示例

演示如何使用实时会话管理器创建、管理和监控用户会话。
"""

import os
import sys
import asyncio
import json
import time
import uuid
import random
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

from src.realtime.session_manager import (
    RealTimeSession,
    SessionStatus,
    SessionManager,
    initialize_session_manager,
    get_session_manager
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("session_demo")

# 模拟用户ID列表
USER_IDS = [
    "user123",
    "user456",
    "user789",
    "admin001",
    "guest"
]

# 模拟设备信息
DEVICE_TYPES = [
    {"platform": "web", "browser": "Chrome", "version": "90.0"},
    {"platform": "web", "browser": "Firefox", "version": "88.0"},
    {"platform": "mobile", "os": "iOS", "version": "14.5"},
    {"platform": "mobile", "os": "Android", "version": "11.0"},
    {"platform": "desktop", "os": "Windows", "version": "10"}
]

# 模拟消息处理
async def handle_chat_message(message: Message, session_id: str):
    """处理聊天消息"""
    logger.info(f"收到聊天消息: {message.data}")
    
    # 获取会话管理器
    session_manager = get_session_manager()
    
    # 获取发送消息的会话
    session = session_manager.get_session_by_connection(session_id)
    if not session:
        logger.warning(f"找不到会话: {session_id}")
        return
    
    # 更新会话统计
    session.total_messages_received += 1
    session.total_bytes_received += len(json.dumps(message.data))
    session.update_activity()
    
    # 创建响应消息
    response = Message(
        id=f"response-{message.id}",
        type=MessageType.RESPONSE,
        action="chat_response",
        data={
            "text": f"收到你的消息: {message.data.get('text', '')}",
            "timestamp": datetime.now().isoformat(),
            "from": "server"
        },
        session_id=session.session_id
    )
    
    # 将响应添加到会话队列
    session_manager.enqueue_message(session.session_id, response)
    
    # 广播消息给所有其他用户
    broadcast = Message(
        id=f"broadcast-{message.id}",
        type=MessageType.NOTIFICATION,
        action="chat_broadcast",
        data={
            "text": message.data.get('text', ''),
            "user_id": session.user_id,
            "timestamp": datetime.now().isoformat()
        }
    )
    
    # 广播给所有其他用户
    session_manager.broadcast_to_all(broadcast, exclude_users=[session.user_id])


# 模拟消息发送线程
async def message_sender():
    """定期向会话队列添加消息"""
    logger.info("启动消息发送线程")
    
    session_manager = get_session_manager()
    engine = get_duplex_engine()
    
    while True:
        try:
            # 获取所有活跃会话
            stats = session_manager.get_stats()
            logger.info(f"当前统计: {stats}")
            
            # 如果有活跃会话，随机发送系统消息
            if stats["active_sessions"] > 0:
                # 随机选择一个用户
                sessions = []
                for user_id in USER_IDS:
                    user_sessions = session_manager.get_sessions_by_user(user_id)
                    sessions.extend(user_sessions)
                
                if sessions:
                    session = random.choice(sessions)
                    
                    # 创建系统消息
                    system_message = Message(
                        id=str(uuid.uuid4()),
                        type=MessageType.NOTIFICATION,
                        action="system_notification",
                        data={
                            "text": f"这是一条系统通知，时间: {datetime.now().isoformat()}",
                            "importance": random.choice(["low", "medium", "high"])
                        },
                        session_id=session.session_id
                    )
                    
                    # 添加到会话队列
                    session_manager.enqueue_message(session.session_id, system_message)
                    logger.info(f"向会话 {session.session_id} 发送系统消息")
            
            # 每10-30秒发送一次消息
            await asyncio.sleep(random.uniform(10, 30))
            
        except Exception as e:
            logger.error(f"消息发送线程错误: {str(e)}")
            await asyncio.sleep(10)


# 模拟消息处理线程
async def message_processor():
    """处理会话队列中的消息"""
    logger.info("启动消息处理线程")
    
    session_manager = get_session_manager()
    engine = get_duplex_engine()
    
    while True:
        try:
            # 获取所有会话
            with session_manager.lock:
                sessions = list(session_manager.sessions.values())
            
            for session in sessions:
                if session.pending_messages > 0:
                    # 处理待处理消息
                    messages = session_manager.process_pending_messages(session.session_id)
                    if messages:
                        logger.info(f"处理会话 {session.session_id} 的 {len(messages)} 条消息")
                        
                        # 发送消息给客户端
                        for message in messages:
                            # 找到会话的所有连接
                            for conn_id in session.connections:
                                try:
                                    # 使用引擎发送消息
                                    await engine.send_message(message, conn_id)
                                    
                                    # 更新统计
                                    session.total_messages_sent += 1
                                    session.total_bytes_sent += len(json.dumps(message.data))
                                except Exception as e:
                                    logger.error(f"发送消息失败: {str(e)}")
            
            # 短暂休眠
            await asyncio.sleep(1)
            
        except Exception as e:
            logger.error(f"消息处理线程错误: {str(e)}")
            await asyncio.sleep(5)


# 模拟会话创建
async def session_creator():
    """定期创建新会话"""
    logger.info("启动会话创建线程")
    
    session_manager = get_session_manager()
    
    # 为每个用户创建初始会话
    for user_id in USER_IDS:
        device_info = random.choice(DEVICE_TYPES)
        
        # 创建会话
        session = session_manager.create_session(
            user_id=user_id,
            device_info=device_info,
            metadata={"created_by": "demo"}
        )
        
        logger.info(f"为用户 {user_id} 创建会话: {session.session_id}")
        
        # 模拟添加连接
        connection_id = f"conn_{user_id}_{str(uuid.uuid4())[:8]}"
        session_manager.add_connection(
            session_id=session.session_id,
            connection_id=connection_id,
            protocol_type=ProtocolType.WEBSOCKET
        )
    
    # 定期随机创建新会话
    while True:
        try:
            # 随机选择一个用户
            user_id = random.choice(USER_IDS)
            device_info = random.choice(DEVICE_TYPES)
            
            # 创建新会话
            session = session_manager.create_session(
                user_id=user_id,
                device_info=device_info,
                metadata={"created_by": "demo"}
            )
            
            logger.info(f"为用户 {user_id} 创建新会话: {session.session_id}")
            
            # 模拟添加连接
            connection_id = f"conn_{user_id}_{str(uuid.uuid4())[:8]}"
            session_manager.add_connection(
                session_id=session.session_id,
                connection_id=connection_id,
                protocol_type=ProtocolType.WEBSOCKET
            )
            
            # 每20-60秒创建一个新会话
            await asyncio.sleep(random.uniform(20, 60))
            
        except Exception as e:
            logger.error(f"会话创建线程错误: {str(e)}")
            await asyncio.sleep(10)


# 模拟连接关闭
async def connection_closer():
    """定期随机关闭连接"""
    logger.info("启动连接关闭线程")
    
    session_manager = get_session_manager()
    
    # 等待一些会话创建
    await asyncio.sleep(30)
    
    while True:
        try:
            # 获取所有会话
            with session_manager.lock:
                sessions = list(session_manager.sessions.values())
            
            if sessions:
                # 随机选择一个会话
                session = random.choice(sessions)
                
                # 如果有连接，随机关闭一个
                if session.connections:
                    conn_id = random.choice(list(session.connections))
                    
                    logger.info(f"关闭会话 {session.session_id} 的连接: {conn_id}")
                    session_manager.remove_connection(conn_id)
            
            # 每15-45秒关闭一个连接
            await asyncio.sleep(random.uniform(15, 45))
            
        except Exception as e:
            logger.error(f"连接关闭线程错误: {str(e)}")
            await asyncio.sleep(10)


async def main():
    """主函数"""
    logger.info("启动实时会话管理器示例")
    
    # 初始化双工通信引擎
    await initialize_duplex_engine(
        protocols=[ProtocolType.WEBSOCKET],
        ws_host="0.0.0.0",
        ws_port=8765
    )
    
    # 获取引擎实例
    engine = get_duplex_engine()
    
    # 注册消息处理回调
    engine.register_callback("chat_message", handle_chat_message)
    
    # 初始化会话管理器
    initialize_session_manager(
        max_sessions=1000,
        idle_timeout=300,  # 5分钟超时
        cleanup_interval=60  # 每分钟清理
    )
    
    logger.info("启动各个模拟线程")
    
    # 启动各个模拟线程
    creator_task = asyncio.create_task(session_creator())
    sender_task = asyncio.create_task(message_sender())
    processor_task = asyncio.create_task(message_processor())
    closer_task = asyncio.create_task(connection_closer())
    
    logger.info("示例已启动，按Ctrl+C停止")
    
    try:
        # 定期显示统计信息
        while True:
            session_manager = get_session_manager()
            stats = session_manager.get_stats()
            
            logger.info(f"会话统计: {json.dumps(stats, indent=2)}")
            
            await asyncio.sleep(30)
    except KeyboardInterrupt:
        logger.info("收到停止信号")
    finally:
        # 取消任务
        creator_task.cancel()
        sender_task.cancel()
        processor_task.cancel()
        closer_task.cancel()
        
        # 关闭引擎
        await shutdown_duplex_engine()
        logger.info("示例已结束")

if __name__ == "__main__":
    asyncio.run(main()) 