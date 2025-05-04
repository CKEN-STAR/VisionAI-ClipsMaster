#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
生物反馈收集器示例

演示如何使用生物反馈收集器收集用户生物特征数据，
分析用户参与度，并进行交互式内容适应。
"""

import os
import sys
import json
import time
import asyncio
import logging
from typing import Dict, Any

# 将项目根目录添加到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("feedback_example")

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

from src.realtime.feedback_loop import (
    BioFeedbackCollector,
    initialize_feedback_collector,
    get_feedback_collector,
    BiometricData,
    BioMetricType,
    WearableSDK
)


class FeedbackDemo:
    """反馈收集器演示"""
    
    def __init__(self):
        """初始化演示"""
        self.session_ids = []
        self.user_ids = ["user1", "user2", "user3"]
    
    async def setup(self):
        """设置演示环境"""
        # 初始化双工通信引擎
        await initialize_duplex_engine(
            protocols=[ProtocolType.WEBSOCKET],
            ws_host="localhost",
            ws_port=8765
        )
        logger.info("双工通信引擎已初始化")
        
        # 初始化会话管理器
        initialize_session_manager()
        logger.info("会话管理器已初始化")
        
        # 初始化生物反馈收集器
        await initialize_feedback_collector()
        logger.info("生物反馈收集器已初始化")
    
    async def create_test_sessions(self):
        """创建测试会话"""
        logger.info("创建测试会话...")
        
        session_manager = get_session_manager()
        feedback_collector = get_feedback_collector()
        
        for user_id in self.user_ids:
            # 创建会话
            session = session_manager.create_session(
                user_id=user_id,
                device_info={"type": "test_device", "os": "demo"},
                metadata={
                    "location": {"lat": 34.0522, "lng": -118.2437},
                    "preferences": {"theme": "dark", "notifications": True}
                }
            )
            
            # 添加虚拟连接
            connection_id = f"conn_{user_id}"
            session_manager.add_connection(
                session_id=session.session_id,
                connection_id=connection_id,
                protocol_type=ProtocolType.WEBSOCKET
            )
            
            # 注册反馈收集
            await feedback_collector.register_session(session.session_id)
            
            self.session_ids.append(session.session_id)
            logger.info(f"已创建会话: {session.session_id} (用户: {user_id})")
    
    async def simulate_interactions(self, duration: int = 30):
        """模拟用户交互
        
        Args:
            duration: 模拟持续时间(秒)
        """
        logger.info(f"开始模拟用户交互 ({duration} 秒)...")
        
        session_manager = get_session_manager()
        feedback_collector = get_feedback_collector()
        
        start_time = time.time()
        while time.time() - start_time < duration:
            # 每秒检查一次
            for session_id in self.session_ids:
                # 获取会话指标
                metrics = feedback_collector.get_session_metrics(session_id)
                
                # 显示状态
                engagement = metrics.get("metrics", {}).get("engagement_score", 0)
                attention = metrics.get("metrics", {}).get("attention_level", 0)
                adaptations = metrics.get("adaptations", 0)
                
                logger.info(f"会话 {session_id}: 参与度={engagement:.2f}, 注意力={attention:.2f}, 适应次数={adaptations}")
                
                # 处理消息
                messages = session_manager.process_pending_messages(session_id)
                for msg in messages:
                    if msg.action == "adaptation":
                        adaptation_type = msg.data.get("type")
                        level = msg.data.get("level")
                        logger.info(f"适应性调整: {adaptation_type} (级别: {level:.2f})")
            
            # 等待1秒
            await asyncio.sleep(1)
    
    async def cleanup(self):
        """清理演示环境"""
        logger.info("清理演示环境...")
        
        feedback_collector = get_feedback_collector()
        session_manager = get_session_manager()
        
        # 取消注册反馈收集
        for session_id in self.session_ids:
            feedback_collector.unregister_session(session_id)
            session_manager.close_session(session_id)
        
        # 停止反馈收集器
        await feedback_collector.stop()
        
        # 关闭双工通信引擎
        await shutdown_duplex_engine()
        
        logger.info("演示环境已清理")


async def test_wearable_sdk():
    """测试可穿戴设备SDK"""
    logger.info("=== 测试可穿戴设备SDK ===")
    
    # 创建SDK实例
    sdk = WearableSDK()
    
    # 启动SDK
    sdk.start()
    logger.info("SDK已启动")
    
    # 连接设备
    device_id = await sdk.connect()
    logger.info(f"已连接设备: {device_id}")
    
    # 获取数据流
    count = 0
    logger.info("开始接收数据流...")
    
    async for data in sdk.stream():
        count += 1
        logger.info(f"数据 #{count}: 类型={data.type.value}, 值={data.value:.2f}, 置信度={data.confidence:.2f}")
        
        # 接收10个数据点后停止
        if count >= 10:
            break
    
    # 停止SDK
    sdk.stop()
    logger.info("SDK已停止")


async def main():
    """主函数"""
    try:
        # 测试可穿戴设备SDK
        await test_wearable_sdk()
        
        # 创建演示实例
        demo = FeedbackDemo()
        
        # 设置演示环境
        await demo.setup()
        
        # 创建测试会话
        await demo.create_test_sessions()
        
        # 模拟用户交互
        await demo.simulate_interactions(duration=20)
        
        # 清理演示环境
        await demo.cleanup()
        
        logger.info("演示完成")
    except Exception as e:
        logger.error(f"演示出错: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())


if __name__ == "__main__":
    asyncio.run(main()) 