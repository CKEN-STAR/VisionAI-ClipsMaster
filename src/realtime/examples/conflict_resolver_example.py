#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
操作转换冲突解决器示例

演示如何使用OTResolver解决实时协作编辑中的冲突。
本示例模拟多个用户同时编辑同一个短剧剪辑项目的情况。
"""

import os
import sys
import json
import time
import uuid
import logging
from typing import Dict, List, Any

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.realtime.conflict_resolver import get_ot_resolver, initialize_ot_resolver

# 配置日志
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("conflict_resolver_example")

def create_sample_state() -> Dict[str, Any]:
    """创建示例编辑状态
    
    Returns:
        Dict[str, Any]: 包含版本和操作历史的状态对象
    """
    return {
        "version": time.time(),
        "ops": [],
        "clips": [
            {
                "id": "clip1",
                "start_time": 0,
                "end_time": 10,
                "content": "这是第一个片段"
            },
            {
                "id": "clip2",
                "start_time": 10,
                "end_time": 20,
                "content": "这是第二个片段"
            }
        ]
    }

def create_sample_operations(base_time: float) -> List[List[Dict[str, Any]]]:
    """创建示例用户操作
    
    Args:
        base_time: 基础时间戳，用于创建不同时间点的操作
        
    Returns:
        List[List[Dict[str, Any]]]: 多个用户的操作列表
    """
    # 用户1的操作：插入新片段
    user1_ops = [
        {
            "id": str(uuid.uuid4()),
            "type": "insert",
            "position": 1,
            "content": {
                "id": "clip3",
                "start_time": 20,
                "end_time": 30,
                "content": "用户1插入的片段"
            },
            "timestamp": base_time + 1
        }
    ]
    
    # 用户2的操作：更新第一个片段
    user2_ops = [
        {
            "id": str(uuid.uuid4()),
            "type": "update",
            "target_id": "clip1",
            "properties": {
                "content": "用户2修改的第一个片段"
            },
            "timestamp": base_time + 2
        }
    ]
    
    # 用户3的操作：删除第二个片段
    user3_ops = [
        {
            "id": str(uuid.uuid4()),
            "type": "delete",
            "position": 1,
            "length": 1,
            "timestamp": base_time + 3
        }
    ]
    
    return [user1_ops, user2_ops, user3_ops]

def simulate_concurrent_edits():
    """模拟并发编辑场景"""
    logger.info("==== 开始模拟并发编辑场景 ====")
    
    # 初始化冲突解决器
    resolver = initialize_ot_resolver()
    
    # 创建初始状态
    base_time = time.time()
    state = create_sample_state()
    state["version"] = base_time
    
    logger.info(f"初始状态: {json.dumps(state, ensure_ascii=False, indent=2)}")
    
    # 创建模拟操作
    all_user_ops = create_sample_operations(base_time)
    
    # 模拟用户1的操作应用
    logger.info("\n==== 用户1操作 ====")
    user1_ops = all_user_ops[0]
    logger.info(f"用户1操作: {json.dumps(user1_ops, ensure_ascii=False, indent=2)}")
    
    # 转换用户1操作并应用
    transformed_ops = resolver.resolve(state, user1_ops)
    new_state = resolver.merge_ops(state, transformed_ops)
    
    logger.info(f"应用用户1操作后状态: {json.dumps(new_state, ensure_ascii=False, indent=2)}")
    
    # 模拟用户2的操作应用（在用户1操作已应用的基础上）
    logger.info("\n==== 用户2操作 ====")
    user2_ops = all_user_ops[1]
    logger.info(f"用户2操作: {json.dumps(user2_ops, ensure_ascii=False, indent=2)}")
    
    # 转换用户2操作并应用
    transformed_ops = resolver.resolve(new_state, user2_ops)
    new_state = resolver.merge_ops(new_state, transformed_ops)
    
    logger.info(f"应用用户2操作后状态: {json.dumps(new_state, ensure_ascii=False, indent=2)}")
    
    # 模拟用户3的操作应用，但假设它不知道用户1的操作（基于初始状态进行操作）
    logger.info("\n==== 用户3操作（基于初始状态）====")
    user3_ops = all_user_ops[2]
    logger.info(f"用户3操作: {json.dumps(user3_ops, ensure_ascii=False, indent=2)}")
    
    # 转换用户3操作并应用到当前状态
    transformed_ops = resolver.resolve(new_state, user3_ops)
    logger.info(f"转换后的用户3操作: {json.dumps(transformed_ops, ensure_ascii=False, indent=2)}")
    
    final_state = resolver.merge_ops(new_state, transformed_ops)
    
    logger.info(f"最终状态: {json.dumps(final_state, ensure_ascii=False, indent=2)}")
    
    # 检验结果
    logger.info("\n==== 验证结果 ====")
    logger.info(f"初始片段数量: {len(state['clips'])}")
    logger.info(f"最终片段数量: {len(final_state['clips'])}")
    logger.info(f"操作历史数量: {len(final_state['ops'])}")
    
    return final_state

def test_conflict_resolution_scenarios():
    """测试各种冲突解决场景"""
    logger.info("\n===== 测试特定冲突解决场景 =====")
    resolver = get_ot_resolver()
    
    # 场景1: 两个插入操作在同一位置
    logger.info("\n-- 场景1: 两个插入操作在同一位置 --")
    state = {
        "version": 100,
        "ops": [],
        "content": "这是测试内容"
    }
    
    op1 = {
        "id": "op1",
        "type": "insert",
        "position": 2,
        "content": "AAA",
        "timestamp": 101
    }
    
    op2 = {
        "id": "op2",
        "type": "insert",
        "position": 2,
        "content": "BBB",
        "timestamp": 102
    }
    
    # 先应用操作1
    transformed_op1 = resolver.resolve(state, [op1])
    state1 = resolver.merge_ops(state, transformed_op1)
    logger.info(f"应用操作1后: {state1}")
    
    # 然后应用操作2（应该被转换）
    transformed_op2 = resolver.resolve(state1, [op2])
    state2 = resolver.merge_ops(state1, transformed_op2)
    logger.info(f"应用操作2后: {state2}")
    
    # 场景2: 删除操作与更新操作冲突
    logger.info("\n-- 场景2: 删除操作与更新操作冲突 --")
    state = {
        "version": 100,
        "ops": [],
        "clips": [
            {"id": "clip1", "content": "内容1"},
            {"id": "clip2", "content": "内容2"},
        ]
    }
    
    op1 = {
        "id": "op1",
        "type": "delete",
        "position": 1,
        "length": 1,
        "timestamp": 101
    }
    
    op2 = {
        "id": "op2",
        "type": "update",
        "target_id": "clip2",
        "properties": {"content": "修改后的内容2"},
        "timestamp": 102
    }
    
    # 先应用删除操作
    transformed_op1 = resolver.resolve(state, [op1])
    state1 = resolver.merge_ops(state, transformed_op1)
    logger.info(f"应用删除操作后: {state1}")
    
    # 然后应用更新操作（应该被智能处理）
    transformed_op2 = resolver.resolve(state1, [op2])
    state2 = resolver.merge_ops(state1, transformed_op2)
    logger.info(f"应用更新操作后: {state2}")

if __name__ == "__main__":
    logger.info("启动操作转换冲突解决器示例")
    
    # 模拟并发编辑
    final_state = simulate_concurrent_edits()
    
    # 测试特定冲突场景
    test_conflict_resolution_scenarios()
    
    logger.info("\n示例结束") 