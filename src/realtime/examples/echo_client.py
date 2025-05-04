#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
双工通信协议Echo客户端示例

演示如何使用双工通信客户端与Echo服务器通信。
"""

import os
import sys
import asyncio
import json
import logging
import time
import random
from datetime import datetime

# 将项目根目录添加到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from src.realtime.duplex_client import DuplexClient
from src.realtime.duplex_engine import Message, MessageType, ProtocolType

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("echo_client")

# 处理欢迎消息
async def handle_welcome(message: Message):
    """处理服务器发送的欢迎消息"""
    logger.info(f"收到服务器欢迎消息: {message.data}")

# 处理客户端加入通知
async def handle_client_joined(message: Message):
    """处理其他客户端加入的通知"""
    logger.info(f"新客户端加入: {message.data}")

# 处理Echo响应
async def handle_echo_response(message: Message):
    """处理来自服务器的Echo响应"""
    logger.info(f"收到Echo响应: {message.data}")

async def main():
    """主函数"""
    # 创建客户端
    client = DuplexClient(
        server_url="ws://localhost:8765",
        protocol_type=ProtocolType.WEBSOCKET,
        auto_reconnect=True
    )
    
    # 注册消息处理回调
    client.register_callback("welcome", handle_welcome)
    client.register_callback("client_joined", handle_client_joined)
    client.register_callback("echo_response", handle_echo_response)
    
    # 连接到服务器
    logger.info("正在连接到Echo服务器...")
    connected = await client.connect()
    
    if not connected:
        logger.error("连接服务器失败，退出")
        return
    
    logger.info("已连接到Echo服务器!")
    
    # 发送10条Echo消息
    try:
        for i in range(1, 11):
            message_text = f"这是测试消息 #{i}，时间: {datetime.now().isoformat()}"
            logger.info(f"发送消息: {message_text}")
            
            await client.send_message(
                action="echo",
                data={"text": message_text}
            )
            
            # 等待一段随机时间，模拟真实用户
            delay = random.uniform(1.0, 3.0)
            logger.info(f"等待 {delay:.2f} 秒...")
            await asyncio.sleep(delay)
        
        # 等待最后一条消息的响应
        logger.info("等待最后响应...")
        await asyncio.sleep(2)
        
    except KeyboardInterrupt:
        logger.info("收到中断信号")
    finally:
        # 断开连接
        logger.info("正在断开连接...")
        await client.disconnect()
        logger.info("已断开连接")

if __name__ == "__main__":
    asyncio.run(main()) 