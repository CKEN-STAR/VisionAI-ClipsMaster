#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
实时会话管理器

提供对实时通信会话的创建、管理和监控功能。
支持会话生命周期管理、消息优先级队列、会话状态跟踪等功能。
"""

import os
import time
import uuid
import json
import threading
import asyncio
import logging
from typing import Dict, List, Any, Optional, Union, Callable, Awaitable, Set, Tuple
from enum import Enum
from collections import OrderedDict, defaultdict
from queue import PriorityQueue, Empty
from dataclasses import dataclass, field

from src.realtime.duplex_engine import (
    Message, 
    MessageType, 
    ProtocolType,
    get_duplex_engine
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("session_manager")

class LRUCache:
    """LRU缓存实现
    
    用于管理有限数量的会话，当达到最大容量时移除最近最少使用的项。
    """
    
    def __init__(self, max_size: int = 10000):
        """初始化LRU缓存
        
        Args:
            max_size: 最大缓存容量
        """
        self.cache = OrderedDict()
        self.max_size = max_size
        self.lock = threading.RLock()
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存项
        
        如果项目存在，自动将其移动到最近使用位置
        
        Args:
            key: 键
            
        Returns:
            Optional[Any]: 值或None（如果不存在）
        """
        with self.lock:
            if key not in self.cache:
                return None
            
            # 将项移到最近使用的位置
            value = self.cache.pop(key)
            self.cache[key] = value
            return value
    
    def put(self, key: str, value: Any) -> None:
        """添加或更新缓存项
        
        如果缓存已满，移除最近最少使用的项
        
        Args:
            key: 键
            value: 值
        """
        with self.lock:
            if key in self.cache:
                self.cache.pop(key)
            elif len(self.cache) >= self.max_size:
                # 移除最早的项（LRU原则）
                self.cache.popitem(last=False)
            
            self.cache[key] = value
    
    def pop(self, key: str) -> Optional[Any]:
        """移除并返回缓存项
        
        Args:
            key: 键
            
        Returns:
            Optional[Any]: 值或None（如果不存在）
        """
        with self.lock:
            if key not in self.cache:
                return None
            
            return self.cache.pop(key)
    
    def __contains__(self, key: str) -> bool:
        """检查键是否存在
        
        Args:
            key: 键
            
        Returns:
            bool: 是否存在
        """
        with self.lock:
            return key in self.cache
    
    def __len__(self) -> int:
        """获取缓存大小
        
        Returns:
            int: 缓存项数量
        """
        with self.lock:
            return len(self.cache)
    
    def keys(self) -> List[str]:
        """获取所有键
        
        Returns:
            List[str]: 键列表
        """
        with self.lock:
            return list(self.cache.keys())
    
    def values(self) -> List[Any]:
        """获取所有值
        
        Returns:
            List[Any]: 值列表
        """
        with self.lock:
            return list(self.cache.values())
    
    def items(self) -> List[Tuple[str, Any]]:
        """获取所有键值对
        
        Returns:
            List[Tuple[str, Any]]: 键值对列表
        """
        with self.lock:
            return list(self.cache.items())
    
    def clear(self) -> None:
        """清空缓存"""
        with self.lock:
            self.cache.clear()


class SessionStatus(Enum):
    """会话状态枚举"""
    ACTIVE = "active"          # 活跃状态
    IDLE = "idle"              # 空闲状态
    DISCONNECTED = "disconnected"  # 断开连接
    EXPIRED = "expired"        # 已过期
    CLOSED = "closed"          # 已关闭


@dataclass(order=True)
class PrioritizedMessage:
    """带优先级的消息
    
    用于在PriorityQueue中对消息进行排序
    """
    priority: int
    timestamp: float = field(compare=False)
    message: Message = field(compare=False)


class RealTimeSession:
    """实时会话
    
    表示一个用户的实时通信会话，管理会话状态和消息队列。
    """
    
    def __init__(self, user_id: str, session_id: Optional[str] = None, 
                 device_info: Optional[Dict[str, Any]] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        """初始化实时会话
        
        Args:
            user_id: 用户ID
            session_id: 会话ID，如果未提供则自动生成
            device_info: 设备信息
            metadata: 元数据
        """
        self.user_id = user_id
        self.session_id = session_id or str(uuid.uuid4())
        self.device_info = device_info or {}
        self.metadata = metadata or {}
        
        # 会话状态跟踪
        self.status = SessionStatus.ACTIVE
        self.created_at = time.time()
        self.last_active = time.time()
        self.last_message_at = None
        self.expiration_time = None  # 过期时间，None表示不过期
        
        # 消息队列 - 使用优先级队列
        self.message_queue = PriorityQueue()
        self.pending_messages = 0  # 等待处理的消息数量
        
        # 连接跟踪
        self.connections: Set[str] = set()  # 连接ID集合
        self.protocol_types: Dict[str, ProtocolType] = {}  # 连接ID到协议类型的映射
        
        # 会话统计
        self.total_messages_sent = 0
        self.total_messages_received = 0
        self.total_bytes_sent = 0
        self.total_bytes_received = 0
        
        # 线程安全锁
        self.lock = threading.RLock()
        
        logger.info(f"创建会话: {self.session_id} (用户: {self.user_id})")
    
    def update_activity(self) -> None:
        """更新会话活动时间"""
        with self.lock:
            self.last_active = time.time()
            # 如果会话处于空闲状态，重新激活
            if self.status == SessionStatus.IDLE:
                self.status = SessionStatus.ACTIVE
                logger.debug(f"会话已激活: {self.session_id}")
    
    def add_connection(self, connection_id: str, protocol_type: ProtocolType) -> None:
        """添加连接到会话
        
        Args:
            connection_id: 连接ID
            protocol_type: 协议类型
        """
        with self.lock:
            self.connections.add(connection_id)
            self.protocol_types[connection_id] = protocol_type
            self.update_activity()
            logger.debug(f"会话 {self.session_id} 添加连接: {connection_id} ({protocol_type.value})")
    
    def remove_connection(self, connection_id: str) -> None:
        """从会话中移除连接
        
        Args:
            connection_id: 连接ID
        """
        with self.lock:
            if connection_id in self.connections:
                self.connections.remove(connection_id)
                self.protocol_types.pop(connection_id, None)
                logger.debug(f"会话 {self.session_id} 移除连接: {connection_id}")
            
            # 如果没有连接，将会话标记为断开连接
            if not self.connections:
                self.status = SessionStatus.DISCONNECTED
                logger.info(f"会话已断开连接: {self.session_id}")
    
    def enqueue_message(self, message: Message, priority: int = 0) -> None:
        """将消息添加到队列
        
        Args:
            message: 要排队的消息
            priority: 消息优先级，数字越小优先级越高
        """
        with self.lock:
            # 创建带优先级的消息
            prioritized_message = PrioritizedMessage(
                priority=priority,
                timestamp=time.time(),
                message=message
            )
            
            # 添加到优先级队列
            self.message_queue.put(prioritized_message)
            self.pending_messages += 1
            
            self.update_activity()
            logger.debug(f"会话 {self.session_id} 排队消息: {message.action} (优先级: {priority})")
    
    def dequeue_message(self, timeout: Optional[float] = None) -> Optional[Message]:
        """从队列中取出消息
        
        Args:
            timeout: 等待超时时间(秒)，None表示不等待
            
        Returns:
            Optional[Message]: 消息，如果队列为空则返回None
        """
        try:
            with self.lock:
                # 如果队列为空，直接返回None（避免在锁内等待）
                if self.message_queue.empty():
                    return None
            
            # 在锁外等待以避免阻塞
            prioritized_message = self.message_queue.get(block=timeout is not None, timeout=timeout)
            
            with self.lock:
                self.pending_messages -= 1
                return prioritized_message.message
                
        except Empty:
            return None
    
    def close(self) -> None:
        """关闭会话"""
        with self.lock:
            self.status = SessionStatus.CLOSED
            self.connections.clear()
            self.protocol_types.clear()
            # 清空消息队列
            while not self.message_queue.empty():
                try:
                    self.message_queue.get_nowait()
                except Empty:
                    break
            
            self.pending_messages = 0
            logger.info(f"会话已关闭: {self.session_id}")
    
    def mark_expired(self) -> None:
        """将会话标记为已过期"""
        with self.lock:
            self.status = SessionStatus.EXPIRED
            logger.info(f"会话已过期: {self.session_id}")
    
    def is_active(self) -> bool:
        """检查会话是否活跃
        
        Returns:
            bool: 是否活跃
        """
        with self.lock:
            return self.status == SessionStatus.ACTIVE
    
    def is_idle(self) -> bool:
        """检查会话是否空闲
        
        Returns:
            bool: 是否空闲
        """
        with self.lock:
            return self.status == SessionStatus.IDLE
    
    def is_connected(self) -> bool:
        """检查会话是否已连接
        
        Returns:
            bool: 是否已连接
        """
        with self.lock:
            return self.status in (SessionStatus.ACTIVE, SessionStatus.IDLE)
    
    def get_active_time(self) -> float:
        """获取会话活跃时间（秒）
        
        Returns:
            float: 活跃时间
        """
        with self.lock:
            return time.time() - self.created_at
    
    def get_idle_time(self) -> float:
        """获取会话空闲时间（秒）
        
        Returns:
            float: 空闲时间
        """
        with self.lock:
            return time.time() - self.last_active
    
    def to_dict(self) -> Dict[str, Any]:
        """将会话转换为字典
        
        Returns:
            Dict[str, Any]: 会话字典表示
        """
        with self.lock:
            return {
                "session_id": self.session_id,
                "user_id": self.user_id,
                "status": self.status.value,
                "created_at": self.created_at,
                "last_active": self.last_active,
                "connections": list(self.connections),
                "pending_messages": self.pending_messages,
                "device_info": self.device_info,
                "metadata": self.metadata,
                "stats": {
                    "messages_sent": self.total_messages_sent,
                    "messages_received": self.total_messages_received,
                    "bytes_sent": self.total_bytes_sent,
                    "bytes_received": self.total_bytes_received
                }
            }


class SessionManager:
    """会话管理器
    
    管理所有实时通信会话，提供会话创建、查找和维护功能。
    """
    
    def __init__(self, max_sessions: int = 10000, 
                 idle_timeout: int = 3600, 
                 cleanup_interval: int = 300):
        """初始化会话管理器
        
        Args:
            max_sessions: 最大会话数量
            idle_timeout: 空闲超时时间(秒)
            cleanup_interval: 清理间隔时间(秒)
        """
        self.sessions = LRUCache(max_size=max_sessions)
        self.user_sessions: Dict[str, Set[str]] = defaultdict(set)  # 用户ID到会话ID的映射
        self.connection_sessions: Dict[str, str] = {}  # 连接ID到会话ID的映射
        
        self.idle_timeout = idle_timeout
        self.cleanup_interval = cleanup_interval
        
        # 引擎实例
        self.engine = get_duplex_engine()
        
        # 统计信息
        self.stats = {
            "created_sessions": 0,
            "closed_sessions": 0,
            "expired_sessions": 0,
            "total_messages": 0
        }
        
        # 线程安全锁
        self.lock = threading.RLock()
        
        # 启动清理线程
        self._start_cleanup_thread()
        
        logger.info(f"会话管理器初始化完成 (最大会话数: {max_sessions}, 空闲超时: {idle_timeout}秒)")
    
    def create_session(self, user_id: str, device_info: Optional[Dict[str, Any]] = None,
                    metadata: Optional[Dict[str, Any]] = None) -> RealTimeSession:
        """创建新会话
        
        Args:
            user_id: 用户ID
            device_info: 设备信息
            metadata: 元数据
            
        Returns:
            RealTimeSession: 创建的会话
        """
        with self.lock:
            # 创建会话
            session = RealTimeSession(
                user_id=user_id,
                device_info=device_info,
                metadata=metadata
            )
            
            # 存储会话
            self.sessions.put(session.session_id, session)
            self.user_sessions[user_id].add(session.session_id)
            
            # 更新统计
            self.stats["created_sessions"] += 1
            
            logger.info(f"已创建会话: {session.session_id} (用户: {user_id})")
            return session
    
    def get_session(self, session_id: str) -> Optional[RealTimeSession]:
        """获取会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            Optional[RealTimeSession]: 会话，如果不存在则返回None
        """
        return self.sessions.get(session_id)
    
    def get_sessions_by_user(self, user_id: str) -> List[RealTimeSession]:
        """获取用户的所有会话
        
        Args:
            user_id: 用户ID
            
        Returns:
            List[RealTimeSession]: 会话列表
        """
        with self.lock:
            session_ids = self.user_sessions.get(user_id, set())
            return [self.sessions.get(sid) for sid in session_ids if self.sessions.get(sid)]
    
    def get_session_by_connection(self, connection_id: str) -> Optional[RealTimeSession]:
        """通过连接ID获取会话
        
        Args:
            connection_id: 连接ID
            
        Returns:
            Optional[RealTimeSession]: 会话，如果不存在则返回None
        """
        with self.lock:
            session_id = self.connection_sessions.get(connection_id)
            if session_id:
                return self.sessions.get(session_id)
            return None
    
    def close_session(self, session_id: str) -> bool:
        """关闭会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            bool: 是否成功关闭
        """
        with self.lock:
            session = self.sessions.get(session_id)
            if not session:
                return False
            
            # 移除连接映射
            for conn_id in list(session.connections):
                if conn_id in self.connection_sessions:
                    self.connection_sessions.pop(conn_id)
            
            # 关闭会话
            session.close()
            
            # 从用户会话映射中移除
            if session.user_id in self.user_sessions:
                self.user_sessions[session.user_id].discard(session_id)
                if not self.user_sessions[session.user_id]:
                    self.user_sessions.pop(session.user_id)
            
            # 从缓存中移除
            self.sessions.pop(session_id)
            
            # 更新统计
            self.stats["closed_sessions"] += 1
            
            logger.info(f"已关闭会话: {session_id}")
            return True
    
    def add_connection(self, session_id: str, connection_id: str, protocol_type: ProtocolType) -> bool:
        """向会话添加连接
        
        Args:
            session_id: 会话ID
            connection_id: 连接ID
            protocol_type: 协议类型
            
        Returns:
            bool: 是否成功添加
        """
        try:
            session = self.get_session(session_id)
            if not session:
                logger.warning(f"添加连接失败: 会话 {session_id} 不存在")
                return False
            
            # 更新会话状态为活跃
            session.last_active = time.time()
            if session.status == SessionStatus.DISCONNECTED:
                session.status = SessionStatus.IDLE
            
            # 添加连接
            session.add_connection(connection_id, protocol_type)
            
            # 记录连接映射
            self.connection_sessions[connection_id] = session_id
            
            # 尝试优化连接参数
            try:
                asyncio.create_task(self._optimize_connection(session, connection_id))
            except Exception as e:
                logger.debug(f"连接优化任务创建失败: {str(e)}")
            
            return True
        except Exception as e:
            logger.error(f"添加连接失败: {str(e)}")
            return False
            
    async def _optimize_connection(self, session: RealTimeSession, connection_id: str) -> None:
        """优化连接参数
        
        使用延迟优化器优化连接参数，减少交互延迟。
        
        Args:
            session: 会话
            connection_id: 连接ID
        """
        try:
            # 导入延迟优化器
            from src.realtime import get_lag_reducer
            lag_reducer = get_lag_reducer()
            
            if not lag_reducer:
                return
            
            # 获取用户位置信息（如果有）
            user_location = None
            if session.metadata and "location" in session.metadata:
                location = session.metadata["location"]
                if isinstance(location, dict) and "lat" in location and "lng" in location:
                    user_location = {"lat": location["lat"], "lng": location["lng"]}
            
            # 优化连接
            optimization = await lag_reducer.optimize_connection(session.session_id, user_location)
            
            # 更新会话元数据
            if "network" not in session.metadata:
                session.metadata["network"] = {}
            
            # 记录网络优化信息
            session.metadata["network"].update({
                "optimized": True,
                "edge_node": optimization["edge_node"],
                "region": optimization["region"],
                "latency": optimization["latency"],
                "buffer_size": optimization["buffer_size"],
                "protocol": optimization["protocol"],
                "compression": optimization["compression"],
                "timestamp": time.time()
            })
            
            logger.debug(f"会话 {session.session_id} 连接 {connection_id} 优化完成")
        except ImportError:
            # 延迟优化器未启用
            pass
        except Exception as e:
            logger.debug(f"连接优化失败: {str(e)}")
    
    def remove_connection(self, connection_id: str) -> bool:
        """移除连接
        
        从会话中移除连接，并清理相关映射。
        
        Args:
            connection_id: 连接ID
            
        Returns:
            bool: 是否成功移除
        """
        try:
            # 获取连接对应的会话ID
            session_id = self.connection_sessions.get(connection_id)
            if not session_id:
                logger.debug(f"移除连接失败: 连接 {connection_id} 不存在")
                return False
            
            # 获取会话
            session = self.get_session(session_id)
            if not session:
                # 如果会话不存在，清理映射
                self.connection_sessions.pop(connection_id, None)
                logger.debug(f"移除连接失败: 会话 {session_id} 不存在")
                return False
            
            # 从会话中移除连接
            session.remove_connection(connection_id)
            
            # 从映射中移除
            self.connection_sessions.pop(connection_id)
            
            logger.debug(f"会话 {session_id} 移除连接: {connection_id}")
            return True
        except Exception as e:
            logger.error(f"移除连接失败: {str(e)}")
            return False
    
    def enqueue_message(self, session_id: str, message: Message, priority: int = 0) -> bool:
        """向会话队列添加消息
        
        Args:
            session_id: 会话ID
            message: 消息
            priority: 优先级
            
        Returns:
            bool: 是否成功添加
        """
        session = self.sessions.get(session_id)
        if not session:
            return False
        
        # 向会话队列添加消息
        session.enqueue_message(message, priority)
        
        # 更新统计
        with self.lock:
            self.stats["total_messages"] += 1
        
        return True
    
    def broadcast_to_user(self, user_id: str, message: Message, priority: int = 0) -> int:
        """向用户的所有会话广播消息
        
        Args:
            user_id: 用户ID
            message: 消息
            priority: 优先级
            
        Returns:
            int: 成功广播的会话数量
        """
        count = 0
        with self.lock:
            session_ids = self.user_sessions.get(user_id, set())
            for session_id in session_ids:
                if self.enqueue_message(session_id, message, priority):
                    count += 1
        
        return count
    
    def broadcast_to_all(self, message: Message, priority: int = 0,
                      exclude_users: Optional[List[str]] = None) -> int:
        """向所有会话广播消息
        
        Args:
            message: 消息
            priority: 优先级
            exclude_users: 要排除的用户ID列表
            
        Returns:
            int: 成功广播的会话数量
        """
        count = 0
        exclude_users = exclude_users or []
        
        with self.lock:
            for session in self.sessions.values():
                if session.user_id not in exclude_users:
                    session.enqueue_message(message, priority)
                    count += 1
            
            # 更新统计
            self.stats["total_messages"] += count
        
        return count
    
    def process_pending_messages(self, session_id: str, 
                               max_messages: int = 10) -> List[Message]:
        """处理会话的待处理消息
        
        Args:
            session_id: 会话ID
            max_messages: 最大处理消息数
            
        Returns:
            List[Message]: 处理的消息列表
        """
        session = self.sessions.get(session_id)
        if not session:
            return []
        
        messages = []
        for _ in range(max_messages):
            msg = session.dequeue_message(timeout=None)  # 不等待
            if not msg:
                break
            messages.append(msg)
        
        return messages
    
    def get_stats(self) -> Dict[str, Any]:
        """获取会话管理器统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        with self.lock:
            active_sessions = sum(1 for s in self.sessions.values() if s.is_active())
            idle_sessions = sum(1 for s in self.sessions.values() if s.is_idle())
            disconnected_sessions = sum(1 for s in self.sessions.values() if s.status == SessionStatus.DISCONNECTED)
            
            return {
                "total_sessions": len(self.sessions),
                "active_sessions": active_sessions,
                "idle_sessions": idle_sessions,
                "disconnected_sessions": disconnected_sessions,
                "total_users": len(self.user_sessions),
                "total_connections": len(self.connection_sessions),
                "created_sessions": self.stats["created_sessions"],
                "closed_sessions": self.stats["closed_sessions"],
                "expired_sessions": self.stats["expired_sessions"],
                "total_messages": self.stats["total_messages"]
            }
    
    def _start_cleanup_thread(self) -> None:
        """启动定期清理线程
        
        定期检查并清理过期会话
        """
        def cleanup_routine():
            while True:
                try:
                    self._cleanup_sessions()
                    time.sleep(self.cleanup_interval)
                except Exception as e:
                    logger.error(f"会话清理失败: {str(e)}")
                    time.sleep(self.cleanup_interval)
        
        # 启动清理线程
        cleanup_thread = threading.Thread(target=cleanup_routine, daemon=True)
        cleanup_thread.start()
        logger.info(f"会话清理线程已启动 (清理间隔: {self.cleanup_interval}秒)")
    
    def _cleanup_sessions(self) -> None:
        """清理过期会话"""
        now = time.time()
        expired_sessions = []
        
        # 找出过期会话
        with self.lock:
            for session_id, session in self.sessions.items():
                # 检查会话是否过期
                if session.get_idle_time() > self.idle_timeout:
                    # 已过期
                    expired_sessions.append(session_id)
                elif session.is_active() and session.get_idle_time() > 300:  # 5分钟无活动
                    # 标记为空闲
                    session.status = SessionStatus.IDLE
        
        # 处理过期会话
        if expired_sessions:
            for session_id in expired_sessions:
                session = self.sessions.get(session_id)
                if session:
                    session.mark_expired()
                    self.close_session(session_id)
            
            # 更新统计
            with self.lock:
                self.stats["expired_sessions"] += len(expired_sessions)
                
            logger.info(f"已清理 {len(expired_sessions)} 个过期会话")


# 全局会话管理器实例
_session_manager: Optional[SessionManager] = None

def get_session_manager() -> SessionManager:
    """获取全局会话管理器实例
    
    Returns:
        SessionManager: 会话管理器实例
    """
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager

def initialize_session_manager(max_sessions: int = 10000, 
                             idle_timeout: int = 3600,
                             cleanup_interval: int = 300) -> None:
    """初始化全局会话管理器
    
    Args:
        max_sessions: 最大会话数量
        idle_timeout: 空闲超时时间(秒)
        cleanup_interval: 清理间隔时间(秒)
    """
    global _session_manager
    _session_manager = SessionManager(
        max_sessions=max_sessions,
        idle_timeout=idle_timeout,
        cleanup_interval=cleanup_interval
    )
    logger.info("全局会话管理器已初始化")


# 示例：如何使用会话管理器
if __name__ == "__main__":
    # 初始化会话管理器
    initialize_session_manager(max_sessions=1000, idle_timeout=60)
    manager = get_session_manager()
    
    # 创建会话
    session = manager.create_session(
        user_id="test_user",
        device_info={"platform": "web", "browser": "Chrome", "version": "90.0"},
        metadata={"plan": "premium"}
    )
    
    print(f"会话ID: {session.session_id}")
    
    # 模拟添加连接
    manager.add_connection(
        session_id=session.session_id,
        connection_id="conn_123",
        protocol_type=ProtocolType.WEBSOCKET
    )
    
    # 向会话队列添加消息
    message = Message(
        id="msg_123",
        type=MessageType.NOTIFICATION,
        action="test_notification",
        data={"text": "这是一条测试消息"}
    )
    
    manager.enqueue_message(session.session_id, message)
    
    # 处理待处理消息
    messages = manager.process_pending_messages(session.session_id)
    for msg in messages:
        print(f"处理消息: {msg.action} - {msg.data}")
    
    # 显示统计信息
    print(manager.get_stats()) 