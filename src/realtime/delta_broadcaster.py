#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
增量更新广播器

使用Redis的发布/订阅功能实现实时增量更新广播。
在协作编辑场景中，当一个用户对内容进行修改时，
该组件负责将增量变更广播给所有相关会话，确保所有用户
能够实时看到内容的变化。
"""

import json
import logging
import zlib
import asyncio
from typing import Dict, Any, Optional, List, Set
import time
import uuid
import gc

import redis.asyncio as redis
from redis.asyncio.client import PubSub

from src.realtime.duplex_engine import Message, MessageType, get_duplex_engine
from src.utils.memory_guard import memory_usage_monitor

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("delta_broadcaster")

class DeltaBroadcaster:
    """增量更新广播器
    
    使用Redis的发布/订阅机制实现实时协作编辑功能。
    当一个用户对内容进行修改时，会生成增量更新并广播给所有订阅的用户。
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        """初始化增量更新广播器
        
        Args:
            redis_url: Redis连接URL，默认为本地Redis
        """
        self.redis_url = redis_url
        self.pubsub: Optional[PubSub] = None
        self.redis_client: Optional[redis.Redis] = None
        self.running = False
        self.listener_task = None
        self.active_sessions: Dict[str, Set[str]] = {}  # 映射频道到活跃会话
        self.duplex_engine = get_duplex_engine()
        
    async def initialize(self) -> None:
        """初始化Redis连接和订阅"""
        try:
            self.redis_client = await redis.from_url(self.redis_url, decode_responses=False)
            self.pubsub = self.redis_client.pubsub()
            logger.info(f"成功连接到Redis: {self.redis_url}")
        except Exception as e:
            logger.error(f"连接Redis失败: {str(e)}")
            raise
    
    async def start(self) -> None:
        """启动广播器监听"""
        if self.running:
            return
            
        self.running = True
        # 首次启动时不订阅任何频道，等待会话显式订阅
        self.listener_task = asyncio.create_task(self._message_listener())
        logger.info("增量更新广播器已启动")
    
    async def stop(self) -> None:
        """停止广播器"""
        self.running = False
        
        if self.listener_task:
            self.listener_task.cancel()
            try:
                await self.listener_task
            except asyncio.CancelledError:
                pass
            self.listener_task = None
        
        if self.pubsub:
            await self.pubsub.unsubscribe()
            await self.pubsub.close()
            self.pubsub = None
            
        if self.redis_client:
            await self.redis_client.close()
            self.redis_client = None
        
        logger.info("增量更新广播器已停止")
    
    async def subscribe_session(self, channel: str, session_id: str) -> bool:
        """为会话订阅频道
        
        Args:
            channel: 要订阅的频道名称
            session_id: 会话ID
            
        Returns:
            bool: 是否成功订阅
        """
        if not self.pubsub or not self.running:
            logger.error("广播器未运行，无法订阅")
            return False
        
        # 更新活跃会话映射
        if channel not in self.active_sessions:
            self.active_sessions[channel] = set()
            # 首次订阅该频道
            await self.pubsub.subscribe(channel)
            logger.info(f"订阅频道: {channel}")
        
        self.active_sessions[channel].add(session_id)
        logger.info(f"会话 {session_id} 已订阅频道 {channel}")
        return True
    
    async def unsubscribe_session(self, channel: str, session_id: str) -> bool:
        """取消会话的频道订阅
        
        Args:
            channel: 频道名称
            session_id: 会话ID
            
        Returns:
            bool: 是否成功取消订阅
        """
        if channel not in self.active_sessions:
            return False
        
        self.active_sessions[channel].discard(session_id)
        
        # 如果该频道没有活跃会话，取消订阅
        if not self.active_sessions[channel] and self.pubsub:
            await self.pubsub.unsubscribe(channel)
            del self.active_sessions[channel]
            logger.info(f"取消订阅频道: {channel}")
        
        logger.info(f"会话 {session_id} 已取消订阅频道 {channel}")
        return True
    
    async def broadcast_changes(self, session_id: str, delta: Dict[str, Any]) -> None:
        """向同一频道的其他会话广播增量更新
        
        Args:
            session_id: 发送会话ID
            delta: 增量更新数据
        """
        try:
            # 触发垃圾回收
            gc.collect()
            
            # 记录开始时间和内存
            start_time = time.time()
            
            # 构建频道名称
            channel = f"session_{session_id}"
            
            # 压缩数据以减少网络传输
            compressed = zlib.compress(json.dumps(delta).encode())
            
            if self.redis_client:
                try:
                    # 通过Redis发布消息
                    await self.redis_client.publish(channel, compressed)
                    logger.debug(f"已广播增量更新到频道: {channel}")
                except Exception as e:
                    logger.error(f"广播增量更新失败: {str(e)}")
                    
            # 记录结束时间和内存使用
            end_time = time.time()
            execution_time = end_time - start_time
            logger.debug(f"增量更新广播耗时: {execution_time:.4f}秒")
        
        except Exception as e:
            logger.error(f"广播增量更新出错: {str(e)}")
    
    async def _message_listener(self) -> None:
        """Redis消息监听循环"""
        if not self.pubsub:
            logger.error("PubSub未初始化，无法启动监听")
            return
        
        try:
            while self.running:
                message = await self.pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message and message["type"] == "message":
                    await self._process_redis_message(message)
                    
                # 小暂停，避免CPU占用过高
                await asyncio.sleep(0.01)
        except asyncio.CancelledError:
            logger.info("消息监听任务已取消")
        except Exception as e:
            logger.error(f"消息监听出错: {str(e)}")
            # 如果出错，尝试重新启动监听
            if self.running:
                logger.info("尝试重新启动消息监听...")
                await asyncio.sleep(1.0)
                self.listener_task = asyncio.create_task(self._message_listener())
    
    async def _process_redis_message(self, redis_message: Dict[str, Any]) -> None:
        """处理从Redis收到的消息
        
        Args:
            redis_message: Redis消息
        """
        try:
            channel = redis_message["channel"].decode()
            compressed_data = redis_message["data"]
            
            # 解压缩数据
            data = json.loads(zlib.decompress(compressed_data).decode())
            
            # 找到订阅该频道的所有会话
            if channel in self.active_sessions:
                session_ids = self.active_sessions[channel]
                
                # 通过双工引擎将消息发送给所有会话
                for session_id in session_ids:
                    message = Message(
                        id=str(uuid.uuid4()),
                        type=MessageType.NOTIFICATION,
                        action="delta_update",
                        data=data,
                        session_id=session_id
                    )
                    
                    # 通过双工引擎广播消息
                    if self.duplex_engine:
                        await self.duplex_engine.broadcast_message(message)
                        
                logger.debug(f"已将增量更新转发给 {len(session_ids)} 个会话")
            
        except Exception as e:
            logger.error(f"处理Redis消息失败: {str(e)}")

    async def broadcast_delta(self, session_id: str, delta_type: str, delta_data: Dict[str, Any]) -> bool:
        """广播增量更新
        
        将增量更新广播到所有订阅了指定会话的客户端。
        
        Args:
            session_id: 会话ID
            delta_type: 增量类型
            delta_data: 增量数据
            
        Returns:
            bool: 是否成功发送
        """
        if not self.initialized or not self.redis_client:
            logger.warning("广播增量更新失败：未初始化或Redis客户端不可用")
            return False
        
        # 添加时间戳
        delta_data["timestamp"] = time.time()
        delta_data["delta_type"] = delta_type
        
        # 应用操作转换解决冲突（如果需要）
        if delta_type in ["edit", "update", "delete", "insert"]:
            try:
                from src.realtime.conflict_resolver import get_ot_resolver
                
                # 获取当前状态
                state_key = f"state:{session_id}"
                current_state = await self._get_state(session_id)
                
                # 将delta_data转换为操作格式
                operation = {
                    "id": delta_data.get("id", str(uuid.uuid4())),
                    "type": delta_type,
                    "timestamp": delta_data["timestamp"],
                    **delta_data
                }
                
                # 解决冲突
                resolver = get_ot_resolver()
                transformed_ops = resolver.resolve(current_state, [operation])
                
                # 更新状态
                new_state = resolver.merge_ops(current_state, transformed_ops)
                await self._set_state(session_id, new_state)
                
                # 使用转换后的操作
                if transformed_ops:
                    # 更新delta_data中的相关字段
                    for key, value in transformed_ops[0].items():
                        if key != "type":  # 保留原始delta_type
                            delta_data[key] = value
                    
                    logger.debug(f"操作转换已应用: {delta_type}")
            except Exception as e:
                logger.error(f"应用操作转换失败: {str(e)}")
        
        try:
            # 创建消息
            message = {
                "session_id": session_id,
                "delta_type": delta_type,
                "data": delta_data,
                "timestamp": delta_data["timestamp"]
            }
            
            # 将消息发布到Redis
            channel = f"delta:{session_id}"
            await self.redis_client.publish(channel, json.dumps(message, ensure_ascii=False))
            
            # 记录日志
            from src.realtime import get_operation_logger
            try:
                op_logger = get_operation_logger()
                if op_logger:
                    op_logger.log_operation(
                        session_id=session_id,
                        operation=f"broadcast_{delta_type}",
                        metadata=delta_data
                    )
            except Exception as e:
                logger.warning(f"记录操作日志失败: {str(e)}")
            
            logger.debug(f"已广播增量更新: {delta_type} 到会话 {session_id}")
            return True
        
        except Exception as e:
            logger.error(f"广播增量更新失败: {str(e)}")
            return False
            
    async def _get_state(self, session_id: str) -> Dict[str, Any]:
        """获取会话的当前状态
        
        Args:
            session_id: 会话ID
            
        Returns:
            Dict[str, Any]: 会话状态
        """
        if not self.redis_client:
            return {"version": time.time(), "ops": []}
        
        try:
            state_key = f"state:{session_id}"
            state_data = await self.redis_client.get(state_key)
            
            if state_data:
                return json.loads(state_data)
            else:
                # 返回初始状态
                return {"version": time.time(), "ops": []}
        
        except Exception as e:
            logger.error(f"获取会话状态失败: {str(e)}")
            return {"version": time.time(), "ops": []}
    
    async def _set_state(self, session_id: str, state: Dict[str, Any]) -> bool:
        """设置会话的当前状态
        
        Args:
            session_id: 会话ID
            state: 会话状态
            
        Returns:
            bool: 是否成功设置
        """
        if not self.redis_client:
            return False
        
        try:
            state_key = f"state:{session_id}"
            await self.redis_client.set(state_key, json.dumps(state, ensure_ascii=False))
            
            # 设置过期时间（24小时）
            await self.redis_client.expire(state_key, 86400)
            
            return True
        
        except Exception as e:
            logger.error(f"设置会话状态失败: {str(e)}")
            return False 