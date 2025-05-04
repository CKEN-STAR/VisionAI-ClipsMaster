#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
延迟优化器示例

演示如何使用延迟优化器来优化实时交互延迟，
提高短剧混剪过程中的响应速度和用户体验。
"""

import os
import sys
import json
import time
import asyncio
import logging
from typing import Dict, Any

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.realtime.latency_optimizer import get_lag_reducer, initialize_lag_reducer

# 配置日志
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("latency_optimizer_example")

async def test_edge_node_selection():
    """测试边缘节点选择"""
    logger.info("=== 测试边缘节点选择 ===")
    
    # 初始化延迟优化器
    lag_reducer = await initialize_lag_reducer()
    
    # 测试不同地理位置的用户
    test_locations = [
        {"name": "北京", "lat": 39.9042, "lng": 116.4074},
        {"name": "上海", "lat": 31.2304, "lng": 121.4737},
        {"name": "广州", "lat": 23.1291, "lng": 113.2644},
        {"name": "成都", "lat": 30.5728, "lng": 104.0668},
        {"name": "西安", "lat": 34.3416, "lng": 108.9398}
    ]
    
    for location in test_locations:
        logger.info(f"\n测试位置: {location['name']}")
        user_location = {"lat": location["lat"], "lng": location["lng"]}
        
        # 获取最近的边缘节点
        nearest_edge = await lag_reducer.get_nearest_edge(user_location)
        logger.info(f"最近的边缘节点: {nearest_edge['id']} (区域: {nearest_edge['region']})")
        
        # 测量查找时间
        start_time = time.time()
        nearest_edge = await lag_reducer.get_nearest_edge(user_location)
        lookup_time = (time.time() - start_time) * 1000  # 转换为毫秒
        logger.info(f"查找时间: {lookup_time:.3f} ms")
    
    # 输出统计信息
    stats = lag_reducer.get_stats()
    logger.info(f"\n统计信息:\n{json.dumps(stats, indent=2, ensure_ascii=False)}")

async def test_connection_optimization():
    """测试连接优化"""
    logger.info("\n=== 测试连接优化 ===")
    
    # 获取延迟优化器单例
    lag_reducer = get_lag_reducer()
    
    # 模拟多个用户会话
    sessions = [
        {"id": "session-1", "location": {"lat": 39.9042, "lng": 116.4074}},  # 北京
        {"id": "session-2", "location": {"lat": 31.2304, "lng": 121.4737}},  # 上海
        {"id": "session-3", "location": {"lat": 23.1291, "lng": 113.2644}},  # 广州
        {"id": "session-4", "location": None}  # 未知位置
    ]
    
    # 对每个会话进行连接优化
    for session in sessions:
        session_id = session["id"]
        user_location = session["location"]
        
        logger.info(f"\n优化会话: {session_id}")
        
        # 优化连接
        result = await lag_reducer.optimize_connection(session_id, user_location)
        
        logger.info(f"优化结果:")
        logger.info(f"  边缘节点: {result['edge_node']} (区域: {result['region']})")
        logger.info(f"  协议: {result['protocol']}")
        logger.info(f"  缓冲区大小: {result['buffer_size']}")
        logger.info(f"  压缩方式: {result['compression']}")
        logger.info(f"  预估延迟: {result['latency']} ms")
        logger.info(f"  查找时间: {result['lookup_time']:.3f} ms")
    
    # 测试相同会话的重复优化
    logger.info("\n测试会话缓存:")
    result1 = await lag_reducer.optimize_connection("session-1")
    result2 = await lag_reducer.optimize_connection("session-1")
    
    if result1["lookup_time"] > result2["lookup_time"]:
        logger.info(f"会话缓存有效: 首次查找 {result1['lookup_time']:.3f} ms, 第二次查找 {result2['lookup_time']:.3f} ms")
    else:
        logger.info(f"会话缓存无效: 首次查找 {result1['lookup_time']:.3f} ms, 第二次查找 {result2['lookup_time']:.3f} ms")

async def test_cache_operations():
    """测试缓存操作"""
    logger.info("\n=== 测试缓存操作 ===")
    
    # 获取延迟优化器单例
    lag_reducer = get_lag_reducer()
    
    # 获取边缘缓存
    edge_cache = lag_reducer.edge_nodes
    
    # 测试缓存添加和获取
    test_key = "test_key"
    test_value = {"data": "测试数据", "timestamp": time.time()}
    
    # 添加缓存
    result = edge_cache.put(test_key, test_value, ttl=10)
    logger.info(f"添加缓存: {'成功' if result else '失败'}")
    
    # 获取缓存
    cached_value = edge_cache.get(test_key)
    if cached_value:
        logger.info(f"缓存命中: {json.dumps(cached_value, ensure_ascii=False)}")
    else:
        logger.info("缓存未命中")
    
    # 测试缓存过期
    logger.info("\n测试缓存过期:")
    expire_key = "expire_test"
    edge_cache.put(expire_key, "将在2秒后过期的数据", ttl=2)
    
    logger.info(f"刚添加: {edge_cache.get(expire_key)}")
    await asyncio.sleep(1)
    logger.info(f"1秒后: {edge_cache.get(expire_key)}")
    await asyncio.sleep(1.5)
    logger.info(f"2.5秒后: {edge_cache.get(expire_key)}")
    
    # 清理过期缓存
    cleared = edge_cache.clear_expired()
    logger.info(f"清理过期缓存项: {cleared}")

async def main():
    """主函数"""
    logger.info("启动延迟优化器示例程序")
    
    try:
        # 测试边缘节点选择
        await test_edge_node_selection()
        
        # 测试连接优化
        await test_connection_optimization()
        
        # 测试缓存操作
        await test_cache_operations()
        
        # 关闭延迟优化器
        lag_reducer = get_lag_reducer()
        await lag_reducer.stop()
        logger.info("\n延迟优化器已关闭")
    except Exception as e:
        logger.error(f"示例程序出错: {str(e)}")
    
    logger.info("\n示例程序结束")

if __name__ == "__main__":
    asyncio.run(main()) 