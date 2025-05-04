#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
命令路由器示例

演示如何使用命令路由器处理和响应客户端命令。
"""

import os
import sys
import json
import asyncio
import logging
import uuid
from datetime import datetime

# 将项目根目录添加到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("command_demo")

from src.realtime.duplex_engine import (
    Message, 
    MessageType, 
    ProtocolType,
    initialize_duplex_engine,
    get_duplex_engine,
    shutdown_duplex_engine
)

from src.realtime.session_manager import (
    initialize_session_manager,
    get_session_manager
)

from src.realtime.command_router import (
    CommandHandler,
    CommandResult,
    CommandStatus,
    initialize_command_router,
    get_command_router
)


# 自定义命令处理器示例
class LogCommandHandler(CommandHandler):
    """日志命令处理器"""
    
    def __init__(self):
        super().__init__()
        self.command_name = "log"
        self.description = "管理和查询日志信息"
        self.help_text = "用于记录、查询和管理系统日志"
    
    async def process(self, session_id: str, command: Dict[str, Any]) -> CommandResult:
        """处理日志命令"""
        try:
            # 解析子命令
            sub_action = command.get("sub_action", "list")
            
            if sub_action == "list":
                # 模拟获取最近的日志
                logs = [
                    {"timestamp": datetime.now().isoformat(), "level": "INFO", "message": "系统启动成功"},
                    {"timestamp": datetime.now().isoformat(), "level": "WARNING", "message": "磁盘空间不足"},
                    {"timestamp": datetime.now().isoformat(), "level": "ERROR", "message": "连接数据库失败"}
                ]
                return CommandResult.success({"logs": logs}, "获取日志成功")
                
            elif sub_action == "add":
                # 添加新日志
                message = command.get("message", "")
                level = command.get("level", "INFO")
                
                logger.log(
                    logging.getLevelName(level),
                    f"[用户记录] {message}"
                )
                
                return CommandResult.success({
                    "timestamp": datetime.now().isoformat(),
                    "level": level,
                    "message": message
                }, "日志已添加")
                
            else:
                return CommandResult.error(f"不支持的日志操作: {sub_action}")
                
        except Exception as e:
            logger.error(f"日志命令执行出错: {str(e)}")
            return CommandResult.error("日志命令执行出错", error=e)
            
    def validate(self, command: Dict[str, Any]) -> bool:
        """验证日志命令"""
        if "sub_action" not in command:
            return False
            
        sub_action = command.get("sub_action")
        if sub_action == "add" and "message" not in command:
            return False
            
        return True


# 测试客户端
class CommandTestClient:
    """命令测试客户端"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.session_id = None
    
    async def connect(self):
        """连接到服务器并创建会话"""
        # 获取会话管理器
        session_manager = get_session_manager()
        
        # 创建会话
        session = session_manager.create_session(
            user_id=self.user_id,
            metadata={
                "permissions": {"edit", "collaborate"},
                "device_info": {"type": "test_client", "os": "demo"}
            }
        )
        
        self.session_id = session.session_id
        logger.info(f"客户端已连接，会话ID: {self.session_id}")
        
        return session
        
    async def send_command(self, command_type: str, **params):
        """发送命令并获取结果"""
        # 获取命令路由器
        router = get_command_router()
        
        # 准备命令数据
        command = {
            "type": command_type,
            **params
        }
        
        # 发送命令
        logger.info(f"发送命令: {command_type}")
        result = await router.route_command(self.session_id, command)
        
        # 打印结果
        logger.info(f"命令结果: {result.status.value}")
        logger.info(f"详情: {result.to_dict()}")
        
        return result


async def main():
    """主函数"""
    try:
        # 初始化双工通信引擎
        await initialize_duplex_engine(
            protocols=[ProtocolType.WEBSOCKET],
            ws_host="localhost",
            ws_port=8765
        )
        
        # 初始化会话管理器
        initialize_session_manager()
        
        # 初始化命令路由器
        initialize_command_router()
        
        # 注册自定义命令处理器
        router = get_command_router()
        router.register_handler("log", LogCommandHandler())
        
        # 创建测试客户端
        client = CommandTestClient(user_id="test_user")
        await client.connect()
        
        # 发送编辑命令
        await client.send_command(
            "edit", 
            operation="create", 
            target="document.txt", 
            content="这是一个测试文档内容"
        )
        
        # 发送协作命令
        await client.send_command(
            "collab",
            action="share",
            resource="document.txt",
            users=["user2", "user3"]
        )
        
        # 添加操作到撤销栈
        await client.send_command(
            "undo",
            action="add",
            context="editor",
            operation={
                "type": "insert",
                "position": 10,
                "text": "插入的新文本"
            }
        )
        
        # 撤销操作
        await client.send_command(
            "undo",
            action="undo",
            context="editor"
        )
        
        # 使用自定义日志命令
        await client.send_command(
            "log",
            sub_action="list"
        )
        
        await client.send_command(
            "log",
            sub_action="add",
            message="这是一条用户添加的测试日志",
            level="INFO"
        )
        
        # 测试未知命令
        await client.send_command(
            "unknown_command",
            param1="value1"
        )
        
        logger.info("命令测试完成")
        
    finally:
        # 关闭引擎
        await shutdown_duplex_engine()


if __name__ == "__main__":
    asyncio.run(main()) 