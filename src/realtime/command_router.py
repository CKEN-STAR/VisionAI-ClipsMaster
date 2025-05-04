#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
交互式命令路由器

提供对实时通信命令的路由、处理和响应功能。
支持命令注册、权限管理、命令执行等功能。
"""

import os
import time
import json
import uuid
import asyncio
import inspect
import logging
from typing import Dict, List, Any, Optional, Union, Callable, Awaitable, Type, Set
from enum import Enum
from abc import ABC, abstractmethod

from src.realtime.duplex_engine import (
    Message, 
    MessageType, 
    ProtocolType,
    get_duplex_engine
)

from src.realtime.session_manager import (
    RealTimeSession,
    SessionStatus,
    get_session_manager
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("command_router")

# 命令处理结果状态
class CommandStatus(Enum):
    SUCCESS = "success"
    ERROR = "error"
    PENDING = "pending"
    UNAUTHORIZED = "unauthorized"

# 命令结果
class CommandResult:
    """命令执行结果"""
    
    def __init__(self, 
                 status: CommandStatus = CommandStatus.SUCCESS,
                 data: Dict[str, Any] = None,
                 message: str = "",
                 error: Optional[Exception] = None):
        self.status = status
        self.data = data or {}
        self.message = message
        self.error = error
        self.timestamp = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            "status": self.status.value,
            "data": self.data,
            "message": self.message,
            "timestamp": self.timestamp
        }
        
        if self.error:
            result["error"] = {
                "type": type(self.error).__name__,
                "message": str(self.error)
            }
            
        return result
    
    @classmethod
    def success(cls, data: Dict[str, Any] = None, message: str = "命令执行成功") -> 'CommandResult':
        """创建成功结果"""
        return cls(CommandStatus.SUCCESS, data, message)
    
    @classmethod
    def error(cls, message: str = "命令执行失败", error: Optional[Exception] = None, 
            data: Dict[str, Any] = None) -> 'CommandResult':
        """创建错误结果"""
        return cls(CommandStatus.ERROR, data, message, error)
    
    @classmethod
    def pending(cls, message: str = "命令正在执行中", data: Dict[str, Any] = None) -> 'CommandResult':
        """创建等待结果"""
        return cls(CommandStatus.PENDING, data, message)
    
    @classmethod
    def unauthorized(cls, message: str = "无权执行此命令", 
                   data: Dict[str, Any] = None) -> 'CommandResult':
        """创建未授权结果"""
        return cls(CommandStatus.UNAUTHORIZED, data, message)


# 命令处理器基类
class CommandHandler(ABC):
    """命令处理器基类"""
    
    def __init__(self):
        # 命令名称（默认为类名小写）
        self.command_name = self.__class__.__name__.lower().replace('commandhandler', '')
        # 命令描述
        self.description = "未提供描述"
        # 需要的权限
        self.required_permissions = set()
        # 帮助文本
        self.help_text = ""
        # 是否为异步处理器
        self.is_async = asyncio.iscoroutinefunction(self.process)
    
    @abstractmethod
    async def process(self, session_id: str, command: Dict[str, Any]) -> CommandResult:
        """处理命令
        
        Args:
            session_id: 会话ID
            command: 命令数据
            
        Returns:
            CommandResult: 命令执行结果
        """
        pass
    
    def validate(self, command: Dict[str, Any]) -> bool:
        """验证命令数据是否有效
        
        Args:
            command: 命令数据
            
        Returns:
            bool: 是否有效
        """
        return True
    
    def check_permissions(self, session_id: str) -> bool:
        """检查权限
        
        Args:
            session_id: 会话ID
            
        Returns:
            bool: 是否有权限
        """
        if not self.required_permissions:
            return True
            
        # 获取会话
        session_manager = get_session_manager()
        session = session_manager.get_session_by_connection(session_id)
        if not session:
            return False
            
        # 检查用户权限
        user_permissions = session.metadata.get("permissions", set())
        return all(perm in user_permissions for perm in self.required_permissions)
    
    def get_help(self) -> Dict[str, Any]:
        """获取命令帮助信息"""
        return {
            "command": self.command_name,
            "description": self.description,
            "help": self.help_text,
            "required_permissions": list(self.required_permissions)
        }


# 默认命令处理器
class DefaultHandler(CommandHandler):
    """默认命令处理器，处理未知命令"""
    
    def __init__(self):
        super().__init__()
        self.command_name = "default"
        self.description = "处理未知命令"
        self.help_text = "当命令无法识别时，使用此处理器"
    
    async def process(self, session_id: str, command: Dict[str, Any]) -> CommandResult:
        """处理未知命令"""
        command_type = command.get("type", "未知")
        return CommandResult.error(f"未知命令类型: {command_type}", 
                                 data={"original_command": command})


# 编辑命令处理器
class EditCommandHandler(CommandHandler):
    """编辑命令处理器"""
    
    def __init__(self):
        super().__init__()
        self.command_name = "edit"
        self.description = "处理文本或内容编辑操作"
        self.help_text = "用于编辑、修改或更新内容"
        self.required_permissions = {"edit"}
    
    async def process(self, session_id: str, command: Dict[str, Any]) -> CommandResult:
        """处理编辑命令"""
        try:
            # 验证命令参数
            if not self.validate(command):
                return CommandResult.error("无效的编辑命令参数")
            
            # 获取操作类型和目标
            operation = command.get("operation", "")
            target = command.get("target", "")
            content = command.get("content", "")
            
            logger.info(f"执行编辑命令 - 操作: {operation}, 目标: {target}")
            
            # 根据不同编辑操作类型处理
            if operation == "update":
                # 这里实现更新操作
                return CommandResult.success({
                    "target": target,
                    "operation": operation,
                    "status": "updated"
                }, "内容已更新")
                
            elif operation == "delete":
                # 这里实现删除操作
                return CommandResult.success({
                    "target": target,
                    "operation": operation,
                    "status": "deleted"
                }, "内容已删除")
                
            elif operation == "create":
                # 这里实现创建操作
                return CommandResult.success({
                    "target": target,
                    "operation": operation,
                    "status": "created",
                    "id": str(uuid.uuid4())
                }, "内容已创建")
                
            else:
                return CommandResult.error(f"不支持的编辑操作: {operation}")
                
        except Exception as e:
            logger.error(f"编辑命令执行出错: {str(e)}")
            return CommandResult.error("编辑命令执行出错", error=e)
    
    def validate(self, command: Dict[str, Any]) -> bool:
        """验证编辑命令参数"""
        required_fields = ["operation", "target"]
        return all(field in command for field in required_fields)


# 协作命令处理器
class CollaborationHandler(CommandHandler):
    """协作命令处理器"""
    
    def __init__(self):
        super().__init__()
        self.command_name = "collab"
        self.description = "处理多用户协作操作"
        self.help_text = "用于共享、协作编辑等多用户交互"
        self.required_permissions = {"collaborate"}
    
    async def process(self, session_id: str, command: Dict[str, Any]) -> CommandResult:
        """处理协作命令"""
        try:
            # 验证命令参数
            if not self.validate(command):
                return CommandResult.error("无效的协作命令参数")
            
            # 获取操作类型和目标
            action = command.get("action", "")
            users = command.get("users", [])
            resource = command.get("resource", "")
            
            logger.info(f"执行协作命令 - 动作: {action}, 资源: {resource}, 用户: {users}")
            
            # 根据不同协作动作处理
            if action == "share":
                # 实现共享功能
                # 这里可以广播消息给其他用户
                engine = get_duplex_engine()
                session_manager = get_session_manager()
                
                # 获取当前用户
                current_session = session_manager.get_session_by_connection(session_id)
                if not current_session:
                    return CommandResult.error("无法获取当前用户会话")
                
                # 构建共享通知
                for user_id in users:
                    # 获取用户所有会话
                    user_sessions = session_manager.get_sessions_by_user(user_id)
                    for user_session in user_sessions:
                        # 为每个会话创建通知消息
                        notification = Message(
                            id=str(uuid.uuid4()),
                            type=MessageType.NOTIFICATION,
                            action="resource_shared",
                            data={
                                "resource": resource,
                                "shared_by": current_session.user_id,
                                "timestamp": time.time()
                            },
                            session_id=user_session.session_id
                        )
                        
                        # 添加到会话消息队列
                        session_manager.enqueue_message(user_session.session_id, notification)
                
                return CommandResult.success({
                    "resource": resource,
                    "shared_with": users
                }, "资源已共享")
                
            elif action == "join":
                # 实现加入协作功能
                return CommandResult.success({
                    "resource": resource,
                    "action": "joined"
                }, "已加入协作")
                
            elif action == "leave":
                # 实现离开协作功能
                return CommandResult.success({
                    "resource": resource,
                    "action": "left"
                }, "已退出协作")
                
            else:
                return CommandResult.error(f"不支持的协作动作: {action}")
                
        except Exception as e:
            logger.error(f"协作命令执行出错: {str(e)}")
            return CommandResult.error("协作命令执行出错", error=e)
    
    def validate(self, command: Dict[str, Any]) -> bool:
        """验证协作命令参数"""
        if "action" not in command:
            return False
            
        action = command.get("action", "")
        if action == "share" and ("users" not in command or "resource" not in command):
            return False
            
        return True


# 撤销/重做命令处理器
class UndoStackManager(CommandHandler):
    """撤销栈管理器"""
    
    def __init__(self):
        super().__init__()
        self.command_name = "undo"
        self.description = "管理操作历史，支持撤销和重做"
        self.help_text = "用于撤销或重做之前的操作"
        # 存储用户操作历史
        self.user_stacks: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}
        # 存储用户当前位置
        self.user_positions: Dict[str, Dict[str, int]] = {}
        # 最大历史记录数
        self.max_history = 50
    
    async def process(self, session_id: str, command: Dict[str, Any]) -> CommandResult:
        """处理撤销/重做命令"""
        try:
            # 验证命令参数
            if not self.validate(command):
                return CommandResult.error("无效的撤销/重做命令参数")
            
            # 获取操作类型和目标
            action = command.get("action", "")
            context = command.get("context", "default")
            
            # 获取会话
            session_manager = get_session_manager()
            session = session_manager.get_session_by_connection(session_id)
            if not session:
                return CommandResult.error("无法获取当前用户会话")
            
            user_id = session.user_id
            
            # 初始化用户栈
            if user_id not in self.user_stacks:
                self.user_stacks[user_id] = {}
                self.user_positions[user_id] = {}
            
            if context not in self.user_stacks[user_id]:
                self.user_stacks[user_id][context] = []
                self.user_positions[user_id][context] = -1
            
            # 获取用户当前位置和栈
            position = self.user_positions[user_id][context]
            stack = self.user_stacks[user_id][context]
            
            # 处理命令
            if action == "undo":
                # 撤销操作
                if position < 0:
                    return CommandResult.error("没有可撤销的操作")
                
                # 获取要撤销的操作
                operation = stack[position]
                
                # 移动位置
                self.user_positions[user_id][context] = position - 1
                
                return CommandResult.success({
                    "operation": operation,
                    "new_position": position - 1,
                    "remaining_undos": position,
                    "remaining_redos": len(stack) - position - 1
                }, "操作已撤销")
                
            elif action == "redo":
                # 重做操作
                if position >= len(stack) - 1:
                    return CommandResult.error("没有可重做的操作")
                
                # 移动位置
                self.user_positions[user_id][context] = position + 1
                
                # 获取要重做的操作
                operation = stack[position + 1]
                
                return CommandResult.success({
                    "operation": operation,
                    "new_position": position + 1,
                    "remaining_undos": position + 1,
                    "remaining_redos": len(stack) - position - 2
                }, "操作已重做")
                
            elif action == "add":
                # 添加新操作
                operation = command.get("operation", {})
                
                # 检查是否有有效操作
                if not operation:
                    return CommandResult.error("未提供有效操作")
                
                # 如果不是在栈顶，需要清除之后的历史
                if position < len(stack) - 1:
                    self.user_stacks[user_id][context] = stack[:position + 1]
                
                # 添加新操作
                self.user_stacks[user_id][context].append(operation)
                
                # 如果超出最大历史记录，移除最早的
                if len(self.user_stacks[user_id][context]) > self.max_history:
                    self.user_stacks[user_id][context].pop(0)
                    
                # 更新位置
                self.user_positions[user_id][context] = len(self.user_stacks[user_id][context]) - 1
                
                return CommandResult.success({
                    "position": self.user_positions[user_id][context],
                    "stack_size": len(self.user_stacks[user_id][context])
                }, "操作已添加到历史")
                
            elif action == "clear":
                # 清空历史
                self.user_stacks[user_id][context] = []
                self.user_positions[user_id][context] = -1
                
                return CommandResult.success({
                    "context": context
                }, "历史记录已清空")
                
            else:
                return CommandResult.error(f"不支持的操作: {action}")
                
        except Exception as e:
            logger.error(f"撤销/重做命令执行出错: {str(e)}")
            return CommandResult.error("撤销/重做命令执行出错", error=e)
    
    def validate(self, command: Dict[str, Any]) -> bool:
        """验证撤销/重做命令参数"""
        if "action" not in command:
            return False
            
        action = command.get("action", "")
        valid_actions = {"undo", "redo", "add", "clear"}
        
        if action not in valid_actions:
            return False
            
        if action == "add" and "operation" not in command:
            return False
            
        return True


class CommandRouter:
    """命令路由器
    
    负责注册和路由命令到对应的处理器。
    """
    
    def __init__(self):
        """初始化命令路由器"""
        # 路由表: 命令类型 -> 处理器
        self.ROUTING_TABLE: Dict[str, CommandHandler] = {
            "edit": EditCommandHandler(),
            "collab": CollaborationHandler(),
            "undo": UndoStackManager()
        }
        
        # 默认处理器
        self.default_handler = DefaultHandler()
        
        # 引擎实例
        self.engine = get_duplex_engine()
        
        # 会话管理器
        self.session_manager = get_session_manager()
        
        logger.info("命令路由器初始化完成")
    
    def register_handler(self, command_type: str, handler: CommandHandler) -> None:
        """注册命令处理器
        
        Args:
            command_type: 命令类型
            handler: 处理器实例
        """
        self.ROUTING_TABLE[command_type] = handler
        logger.info(f"已注册命令处理器: {command_type}")
    
    def unregister_handler(self, command_type: str) -> None:
        """注销命令处理器
        
        Args:
            command_type: 命令类型
        """
        if command_type in self.ROUTING_TABLE:
            self.ROUTING_TABLE.pop(command_type)
            logger.info(f"已注销命令处理器: {command_type}")
    
    async def route_command(self, session_id: str, command: Dict[str, Any]) -> CommandResult:
        """路由命令到对应的处理器
        
        Args:
            session_id: 会话ID
            command: 命令数据
            
        Returns:
            CommandResult: 命令执行结果
        """
        logger.debug(f"解析并分发命令: {command.get('type', 'unknown')}")
        
        # 获取处理器
        command_type = command.get("type", "")
        handler = self.ROUTING_TABLE.get(command_type, self.default_handler)
        
        # 检查权限
        if not handler.check_permissions(session_id):
            logger.warning(f"权限不足，无法执行命令: {command_type}")
            return CommandResult.unauthorized(f"无权执行此命令: {command_type}")
        
        # 验证命令
        if not handler.validate(command):
            logger.warning(f"命令验证失败: {command}")
            return CommandResult.error("命令参数无效")
        
        # 执行命令
        try:
            return await handler.process(session_id, command)
        except Exception as e:
            logger.error(f"命令执行出错: {str(e)}")
            return CommandResult.error("命令执行出错", error=e)
    
    def get_available_commands(self, session_id: str) -> List[Dict[str, Any]]:
        """获取用户可用的命令列表
        
        Args:
            session_id: 会话ID
            
        Returns:
            List[Dict[str, Any]]: 可用命令列表
        """
        commands = []
        
        for cmd_type, handler in self.ROUTING_TABLE.items():
            if handler.check_permissions(session_id):
                commands.append(handler.get_help())
        
        return commands
    
    async def handle_command_message(self, message: Message, session_id: str) -> None:
        """处理命令消息
        
        当收到命令消息时，路由到对应处理器并发送响应
        
        Args:
            message: 消息对象
            session_id: 会话ID
        """
        # 检查消息类型
        if message.type != MessageType.REQUEST:
            logger.warning(f"非请求类型消息: {message.type}")
            return
        
        # 获取命令数据
        command = message.data
        command["type"] = message.action
        
        logger.info(f"处理命令消息: {message.action}")
        
        # 路由命令
        result = await self.route_command(session_id, command)
        
        # 构建响应消息
        response = Message(
            id=f"resp-{message.id}",
            type=MessageType.RESPONSE,
            action=f"{message.action}_response",
            data=result.to_dict(),
            session_id=message.session_id
        )
        
        # 发送响应
        await self.engine.send_message(response, session_id)


# 全局命令路由器实例
_command_router: Optional[CommandRouter] = None

def get_command_router() -> CommandRouter:
    """获取全局命令路由器实例
    
    Returns:
        CommandRouter: 命令路由器实例
    """
    global _command_router
    if _command_router is None:
        _command_router = CommandRouter()
    return _command_router

def initialize_command_router() -> None:
    """初始化命令路由器
    
    注册命令处理器并连接到双工通信引擎
    """
    global _command_router
    
    # 创建命令路由器
    _command_router = CommandRouter()
    
    # 获取双工通信引擎
    engine = get_duplex_engine()
    
    # 注册命令消息处理回调
    for command_type in _command_router.ROUTING_TABLE.keys():
        # 为每种命令类型注册回调
        engine.register_callback(command_type, _command_router.handle_command_message)
    
    logger.info("命令路由器已初始化并连接到双工通信引擎")

# 示例：如何使用命令路由器
if __name__ == "__main__":
    import asyncio
    
    async def demo():
        # 初始化双工通信引擎
        from src.realtime.duplex_engine import initialize_duplex_engine
        await initialize_duplex_engine()
        
        # 初始化会话管理器
        from src.realtime.session_manager import initialize_session_manager
        initialize_session_manager()
        
        # 初始化命令路由器
        initialize_command_router()
        router = get_command_router()
        
        # 创建一个测试会话
        session_manager = get_session_manager()
        session = session_manager.create_session(
            user_id="test_user",
            metadata={"permissions": {"edit", "collaborate"}}
        )
        
        # 模拟一个编辑命令
        edit_command = {
            "type": "edit",
            "operation": "create",
            "target": "document.txt",
            "content": "Hello, World!"
        }
        
        # 处理命令
        result = await router.route_command(session.session_id, edit_command)
        print(f"编辑命令结果: {result.to_dict()}")
        
        # 模拟一个协作命令
        collab_command = {
            "type": "collab",
            "action": "share",
            "resource": "document.txt",
            "users": ["user2", "user3"]
        }
        
        # 处理命令
        result = await router.route_command(session.session_id, collab_command)
        print(f"协作命令结果: {result.to_dict()}")
        
        # 模拟撤销/重做
        # 添加操作到历史
        add_operation = {
            "type": "undo",
            "action": "add",
            "context": "editor",
            "operation": {
                "type": "insert",
                "position": 10,
                "text": "New text"
            }
        }
        
        result = await router.route_command(session.session_id, add_operation)
        print(f"添加操作结果: {result.to_dict()}")
        
        # 撤销操作
        undo_command = {
            "type": "undo",
            "action": "undo",
            "context": "editor"
        }
        
        result = await router.route_command(session.session_id, undo_command)
        print(f"撤销操作结果: {result.to_dict()}")
    
    # 运行示例
    asyncio.run(demo()) 