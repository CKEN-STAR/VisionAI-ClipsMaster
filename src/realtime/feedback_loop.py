#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
实时反馈收集器

收集用户生物特征数据和互动反馈，
用于优化混剪体验和内容推荐。
"""

import os
import time
import json
import uuid
import asyncio
import logging
import threading
from typing import Dict, List, Any, Optional, Callable, Set, Tuple, Union
from enum import Enum
from dataclasses import dataclass, field

from src.realtime.duplex_engine import (
    Message, 
    MessageType, 
    ProtocolType,
    get_duplex_engine
)

from src.realtime.session_manager import (
    get_session_manager,
    RealTimeSession
)

# 配置日志记录器
logger = logging.getLogger(__name__)

# 生物特征数据类型
class BioMetricType(Enum):
    """生物特征数据类型"""
    GSR = "galvanic_skin_response"    # 皮电反应
    PULSE = "pulse"                   # 脉搏/心率
    ATTENTION = "attention"           # 注意力水平
    EMOTION = "emotion"               # 情绪状态
    EYE_TRACKING = "eye_tracking"     # 眼动追踪
    FACIAL = "facial_expression"      # 面部表情
    POSTURE = "posture"               # 姿势/体态
    VOICE = "voice_tone"              # 语音音调


@dataclass
class BiometricData:
    """生物特征数据"""
    type: BioMetricType                # 数据类型
    value: float                       # 数值
    confidence: float = 1.0            # 置信度(0-1)
    timestamp: float = field(default_factory=time.time)  # 时间戳
    metadata: Dict[str, Any] = field(default_factory=dict)  # 元数据


class WearableSDK:
    """可穿戴设备SDK
    
    提供与可穿戴设备的通信和数据收集功能。
    此实现支持多种设备类型，包括智能手表、VR设备等。
    """
    
    def __init__(self, device_config: Optional[Dict[str, Any]] = None):
        """初始化可穿戴设备SDK
        
        Args:
            device_config: 设备配置
        """
        self.config = device_config or self._load_default_config()
        self.connected_devices: Dict[str, Dict[str, Any]] = {}
        self.data_buffer: List[BiometricData] = []
        self.buffer_size = self.config.get("buffer_size", 100)
        self.is_simulated = self.config.get("use_simulation", True)
        self.running = False
        self.lock = threading.RLock()
        self.simulation_thread = None
        
        logger.info("可穿戴设备SDK已初始化")
    
    def _load_default_config(self) -> Dict[str, Any]:
        """加载默认配置
        
        Returns:
            Dict[str, Any]: 默认配置
        """
        default_config = {
            "use_simulation": True,
            "buffer_size": 100,
            "sampling_rate": 10,  # Hz
            "supported_devices": ["smart_watch", "vr_headset", "armband"],
            "data_types": ["pulse", "gsr", "attention"]
        }
        
        # 尝试从配置文件加载
        config_path = os.path.join("configs", "wearable.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    user_config = json.load(f)
                    # 合并配置
                    for key, value in user_config.items():
                        default_config[key] = value
                logger.info(f"已加载可穿戴设备配置: {config_path}")
            except Exception as e:
                logger.warning(f"加载可穿戴设备配置失败: {str(e)}")
        
        return default_config
    
    async def connect(self, device_id: Optional[str] = None, device_type: Optional[str] = None) -> str:
        """连接到可穿戴设备
        
        Args:
            device_id: 设备ID，如果为None则自动选择或创建模拟设备
            device_type: 设备类型
            
        Returns:
            str: 设备ID
        """
        with self.lock:
            if self.is_simulated:
                # 创建模拟设备
                sim_id = device_id or f"sim_{uuid.uuid4().hex[:8]}"
                sim_type = device_type or "simulated_device"
                
                self.connected_devices[sim_id] = {
                    "id": sim_id,
                    "type": sim_type,
                    "connected_at": time.time(),
                    "status": "connected",
                    "capabilities": self.config.get("data_types", [])
                }
                
                logger.debug(f"已连接模拟设备: {sim_id}")
                return sim_id
            else:
                # 在真实实现中，这里将包含设备搜索和连接逻辑
                # 现在仅返回模拟设备ID
                return await self.connect(device_id, device_type)
    
    def disconnect(self, device_id: str) -> bool:
        """断开与可穿戴设备的连接
        
        Args:
            device_id: 设备ID
            
        Returns:
            bool: 是否成功断开连接
        """
        with self.lock:
            if device_id in self.connected_devices:
                self.connected_devices.pop(device_id)
                logger.debug(f"已断开设备连接: {device_id}")
                return True
            return False
    
    def get_connected_devices(self) -> List[Dict[str, Any]]:
        """获取已连接的设备列表
        
        Returns:
            List[Dict[str, Any]]: 设备列表
        """
        with self.lock:
            return list(self.connected_devices.values())
    
    def _generate_simulated_data(self) -> BiometricData:
        """生成模拟的生物特征数据
        
        Returns:
            BiometricData: 模拟数据
        """
        import random
        
        # 随机选择一种数据类型
        data_types = self.config.get("data_types", ["pulse", "gsr", "attention"])
        data_type = random.choice(data_types)
        
        # 根据类型生成合理的值
        if data_type == "pulse":
            # 脉搏/心率 (60-100 bpm)
            value = random.uniform(60, 100)
            bio_type = BioMetricType.PULSE
        elif data_type == "gsr":
            # 皮电反应 (1-20 microSiemens)
            value = random.uniform(1, 20)
            bio_type = BioMetricType.GSR
        elif data_type == "attention":
            # 注意力水平 (0-1)
            value = random.uniform(0, 1)
            bio_type = BioMetricType.ATTENTION
        elif data_type == "emotion":
            # 情绪状态 (-1到1，-1为负面，1为正面)
            value = random.uniform(-1, 1)
            bio_type = BioMetricType.EMOTION
        else:
            # 默认随机值
            value = random.random()
            bio_type = BioMetricType.PULSE
        
        # 设置置信度（模拟数据置信度较低）
        confidence = random.uniform(0.6, 0.9)
        
        return BiometricData(
            type=bio_type,
            value=value,
            confidence=confidence,
            timestamp=time.time(),
            metadata={"source": "simulation"}
        )
    
    def _simulation_loop(self):
        """模拟数据生成循环"""
        while self.running:
            try:
                # 生成模拟数据
                data = self._generate_simulated_data()
                
                # 添加到缓冲区
                with self.lock:
                    self.data_buffer.append(data)
                    
                    # 限制缓冲区大小
                    if len(self.data_buffer) > self.buffer_size:
                        self.data_buffer = self.data_buffer[-self.buffer_size:]
                
                # 按照采样率休眠
                sampling_interval = 1.0 / self.config.get("sampling_rate", 10)
                time.sleep(sampling_interval)
            except Exception as e:
                logger.error(f"模拟数据生成出错: {str(e)}")
                time.sleep(1)  # 错误恢复间隔
    
    def start(self):
        """启动数据收集"""
        with self.lock:
            if self.running:
                return
            
            self.running = True
            
            if self.is_simulated:
                # 启动模拟线程
                self.simulation_thread = threading.Thread(target=self._simulation_loop)
                self.simulation_thread.daemon = True
                self.simulation_thread.start()
                logger.info("已启动模拟数据生成")
            else:
                # 真实设备数据收集逻辑
                logger.info("已启动真实设备数据收集")
    
    def stop(self):
        """停止数据收集"""
        with self.lock:
            self.running = False
            
            if self.simulation_thread:
                self.simulation_thread.join(timeout=2)
                self.simulation_thread = None
            
            logger.info("已停止数据收集")
    
    async def stream(self):
        """数据流生成器
        
        以异步生成器的方式提供数据流。
        """
        last_index = 0
        
        while self.running:
            with self.lock:
                if len(self.data_buffer) > last_index:
                    # 有新数据
                    new_data = self.data_buffer[last_index:]
                    last_index = len(self.data_buffer)
                    
                    # 逐个产出数据
                    for data in new_data:
                        yield data
                else:
                    # 无新数据
                    pass
            
            # 等待新数据
            await asyncio.sleep(0.1)


class BioFeedbackCollector:
    """生物反馈收集器
    
    收集用户生物特征数据并分析用户的互动参与度，
    用于优化混剪体验和内容推荐。
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化生物反馈收集器
        
        Args:
            config: 配置
        """
        self.config = config or {}
        self.wearable_conn = WearableSDK()
        self.session_data: Dict[str, Dict[str, Any]] = {}
        self.running = False
        self.feedback_tasks: Dict[str, asyncio.Task] = {}
        self.lock = threading.RLock()
        
        # 快速访问引擎和会话管理器
        self.engine = get_duplex_engine()
        self.session_manager = get_session_manager()
        
        logger.info("生物反馈收集器已初始化")
    
    async def start(self):
        """启动反馈收集器"""
        with self.lock:
            if self.running:
                return
            
            self.running = True
            
            # 启动可穿戴设备SDK
            self.wearable_conn.start()
            
            logger.info("生物反馈收集器已启动")
    
    async def stop(self):
        """停止反馈收集器"""
        with self.lock:
            self.running = False
            
            # 停止所有反馈任务
            for session_id, task in list(self.feedback_tasks.items()):
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
            
            self.feedback_tasks.clear()
            
            # 停止可穿戴设备SDK
            self.wearable_conn.stop()
            
            logger.info("生物反馈收集器已停止")
    
    async def register_session(self, session_id: str) -> bool:
        """注册会话进行反馈收集
        
        Args:
            session_id: 会话ID
            
        Returns:
            bool: 是否成功注册
        """
        # 获取会话
        session = self.session_manager.get_session(session_id)
        if not session:
            logger.warning(f"注册反馈收集失败: 会话 {session_id} 不存在")
            return False
        
        # 初始化会话数据
        with self.lock:
            # 如果已存在，不重复注册
            if session_id in self.session_data:
                return True
            
            # 创建会话数据
            self.session_data[session_id] = {
                "started_at": time.time(),
                "device_id": None,
                "metrics": {
                    "engagement_score": 0.0,
                    "attention_level": 0.0,
                    "emotional_response": 0.0,
                    "interaction_count": 0
                },
                "history": [],
                "adaptations": []
            }
            
            # 启动反馈任务
            if self.running and session_id not in self.feedback_tasks:
                task = asyncio.create_task(self.stream_biometrics(session_id))
                self.feedback_tasks[session_id] = task
            
            logger.info(f"已注册会话 {session_id} 进行反馈收集")
            return True
    
    def unregister_session(self, session_id: str) -> bool:
        """取消注册会话的反馈收集
        
        Args:
            session_id: 会话ID
            
        Returns:
            bool: 是否成功取消注册
        """
        with self.lock:
            # 取消任务
            if session_id in self.feedback_tasks:
                task = self.feedback_tasks.pop(session_id)
                if not task.done():
                    task.cancel()
            
            # 移除会话数据
            if session_id in self.session_data:
                data = self.session_data.pop(session_id)
                
                # 断开设备连接
                if data.get("device_id"):
                    self.wearable_conn.disconnect(data["device_id"])
                
                logger.info(f"已取消注册会话 {session_id} 的反馈收集")
                return True
            
            return False
    
    async def stream_biometrics(self, session_id: str):
        """为指定会话流式收集生物特征数据
        
        Args:
            session_id: 会话ID
        """
        try:
            logger.info(f"开始收集会话 {session_id} 的生物特征数据")
            
            # 连接模拟设备
            device_id = await self.wearable_conn.connect()
            
            # 记录设备ID
            with self.lock:
                if session_id in self.session_data:
                    self.session_data[session_id]["device_id"] = device_id
            
            # 接收数据流
            async for data in self.wearable_conn.stream():
                if not self.running or session_id not in self.session_data:
                    break
                
                # 分析数据
                if data.type == BioMetricType.PULSE:
                    await self._analyze_engagement(data.value, data.confidence, session_id)
                elif data.type == BioMetricType.GSR:
                    # 分析皮电反应
                    pass
                elif data.type == BioMetricType.ATTENTION:
                    # 处理注意力数据并调整内容难度
                    await self._adjust_difficulty(session_id, data.value)
                
                # 记录历史数据(仅保留最近100条)
                with self.lock:
                    if session_id in self.session_data:
                        history = self.session_data[session_id].get("history", [])
                        history.append({
                            "type": data.type.value,
                            "value": data.value,
                            "timestamp": data.timestamp
                        })
                        # 限制历史记录长度
                        if len(history) > 100:
                            history = history[-100:]
                        self.session_data[session_id]["history"] = history
        
        except asyncio.CancelledError:
            logger.info(f"会话 {session_id} 的生物特征数据收集已取消")
            raise
        except Exception as e:
            logger.error(f"收集生物特征数据出错: {str(e)}")
        finally:
            # 清理工作
            with self.lock:
                if session_id in self.feedback_tasks:
                    self.feedback_tasks.pop(session_id, None)
                
                # 断开设备连接
                if session_id in self.session_data and self.session_data[session_id].get("device_id"):
                    device_id = self.session_data[session_id]["device_id"]
                    self.wearable_conn.disconnect(device_id)
    
    async def _analyze_engagement(self, pulse: float, confidence: float, session_id: str):
        """分析用户参与度
        
        基于心率和其他指标分析用户参与度。
        
        Args:
            pulse: 脉搏/心率
            confidence: 数据置信度
            session_id: 会话ID
        """
        # 简化的参与度分析逻辑
        # 在实际实现中，这会更加复杂，包含多种生物指标和历史数据
        
        # 获取会话数据
        session_data = self.session_data.get(session_id)
        if not session_data:
            return
        
        # 基于心率的变化评估参与度
        # 正常心率约为60-100 bpm，显著偏离可能表示参与度变化
        base_rate = 75  # 基础心率
        
        # 计算心率偏离
        rate_diff = abs(pulse - base_rate)
        
        # 简单的兴奋度评分 (0-1)
        excitement = min(1.0, rate_diff / 25.0) * confidence
        
        # 更新会话数据
        with self.lock:
            if session_id in self.session_data:
                # 逐渐衰减旧分数并添加新分数 (时间加权平均)
                current = self.session_data[session_id]["metrics"]["engagement_score"]
                self.session_data[session_id]["metrics"]["engagement_score"] = current * 0.7 + excitement * 0.3
                
                # 增加交互计数
                self.session_data[session_id]["metrics"]["interaction_count"] += 1
    
    async def _adjust_difficulty(self, session_id: str, attention_level: float):
        """根据注意力水平调整内容难度
        
        Args:
            session_id: 会话ID
            attention_level: 注意力水平 (0-1)
        """
        # 更新注意力水平
        with self.lock:
            if session_id in self.session_data:
                # 使用指数移动平均平滑注意力水平
                current = self.session_data[session_id]["metrics"]["attention_level"]
                self.session_data[session_id]["metrics"]["attention_level"] = current * 0.8 + attention_level * 0.2
                
                # 根据注意力水平决定是否调整混剪难度
                smooth_level = self.session_data[session_id]["metrics"]["attention_level"]
                
                # 注意力过低，降低难度
                if smooth_level < 0.3 and len(self.session_data[session_id]["adaptations"]) < 5:
                    adaptation = {
                        "type": "difficulty_decrease",
                        "reason": "low_attention",
                        "level": smooth_level,
                        "timestamp": time.time()
                    }
                    self.session_data[session_id]["adaptations"].append(adaptation)
                    
                    # 发送适应性调整消息
                    await self._send_adaptation_message(session_id, "difficulty_decrease", smooth_level)
                
                # 注意力很高，增加难度
                elif smooth_level > 0.7 and len(self.session_data[session_id]["adaptations"]) < 5:
                    adaptation = {
                        "type": "difficulty_increase",
                        "reason": "high_attention",
                        "level": smooth_level,
                        "timestamp": time.time()
                    }
                    self.session_data[session_id]["adaptations"].append(adaptation)
                    
                    # 发送适应性调整消息
                    await self._send_adaptation_message(session_id, "difficulty_increase", smooth_level)
    
    async def _send_adaptation_message(self, session_id: str, adaptation_type: str, level: float):
        """发送适应性调整消息
        
        Args:
            session_id: 会话ID
            adaptation_type: 调整类型
            level: 适应级别
        """
        try:
            # 获取会话
            session = self.session_manager.get_session(session_id)
            if not session:
                return
            
            # 创建适应性消息
            message = Message(
                id=str(uuid.uuid4()),
                type=MessageType.SYSTEM,
                action="adaptation",
                data={
                    "type": adaptation_type,
                    "level": level,
                    "timestamp": time.time()
                }
            )
            
            # 将消息排队到会话
            self.session_manager.enqueue_message(session_id, message, priority=1)
            
            logger.debug(f"已发送适应性调整消息: {adaptation_type} ({level:.2f}) 到会话 {session_id}")
        except Exception as e:
            logger.error(f"发送适应性调整消息失败: {str(e)}")
    
    def get_session_metrics(self, session_id: str) -> Dict[str, Any]:
        """获取会话的指标数据
        
        Args:
            session_id: 会话ID
            
        Returns:
            Dict[str, Any]: 指标数据
        """
        with self.lock:
            if session_id in self.session_data:
                # 返回指标的副本
                return {
                    "metrics": self.session_data[session_id]["metrics"].copy(),
                    "adaptations": len(self.session_data[session_id]["adaptations"]),
                    "session_duration": time.time() - self.session_data[session_id]["started_at"]
                }
            
            return {
                "metrics": {},
                "adaptations": 0,
                "session_duration": 0
            }
    
    def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """获取所有会话的指标数据
        
        Returns:
            Dict[str, Dict[str, Any]]: 会话ID到指标数据的映射
        """
        result = {}
        with self.lock:
            for session_id in self.session_data:
                result[session_id] = self.get_session_metrics(session_id)
        
        return result


# 全局单例
_feedback_collector = None
_collector_lock = threading.Lock()

def get_feedback_collector() -> BioFeedbackCollector:
    """获取生物反馈收集器单例
    
    Returns:
        BioFeedbackCollector: 生物反馈收集器实例
    """
    global _feedback_collector
    
    if _feedback_collector is None:
        with _collector_lock:
            if _feedback_collector is None:
                _feedback_collector = BioFeedbackCollector()
    
    return _feedback_collector

async def initialize_feedback_collector(config: Optional[Dict[str, Any]] = None) -> BioFeedbackCollector:
    """初始化生物反馈收集器
    
    Args:
        config: 配置
        
    Returns:
        BioFeedbackCollector: 生物反馈收集器实例
    """
    global _feedback_collector
    
    with _collector_lock:
        _feedback_collector = BioFeedbackCollector(config)
        await _feedback_collector.start()
    
    return _feedback_collector 