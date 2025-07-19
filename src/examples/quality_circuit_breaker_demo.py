#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
质量熔断器演示脚本

展示质量熔断器的基本功能和工作流程，包括质量检查、熔断触发和恢复等。
"""

import os
import sys
import time
import random
import logging
from typing import Dict, List, Any

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.versioning.quality_circuit_breaker import (
    QualityGuardian, 
    QualityCollapseError,
    CircuitBreakerState,
    get_quality_guardian
)
from src.utils.log_handler import configure_logging, get_logger

# 配置日志
configure_logging({
    "level": "info",
    "console_enabled": True,
    "file_enabled": True,
    "file_path": "logs",
    "file_prefix": "quality_demo"
})

logger = get_logger("quality_demo")

def create_test_version(version_id: str, quality_level: float) -> Dict[str, Any]:
    """创建测试版本
    
    Args:
        version_id: 版本ID
        quality_level: 质量级别 (0.0-1.0)
        
    Returns:
        测试版本数据
    """
    # 基于质量级别生成不同的质量指标
    coherence = min(1.0, quality_level * random.uniform(0.9, 1.1))
    emotion_flow = min(1.0, quality_level * random.uniform(0.85, 1.15))
    pacing = min(1.0, quality_level * random.uniform(0.9, 1.1))
    structure = min(1.0, quality_level * random.uniform(0.85, 1.15))
    engagement = min(1.0, quality_level * random.uniform(0.9, 1.1))
    
    # 创建测试版本
    version = {
        "id": version_id,
        "quality_level": quality_level,
        "content": {
            "emotion_intensities": [0.3, 0.5, quality_level, 0.8 * quality_level, 0.5],
            "emotion_curve": [
                {"position": 0.0, "intensity": 0.3, "emotion": "neutral"},
                {"position": 0.25, "intensity": 0.5, "emotion": "joy"},
                {"position": 0.5, "intensity": quality_level, "emotion": "surprise"},
                {"position": 0.75, "intensity": 0.8 * quality_level, "emotion": "fear"},
                {"position": 1.0, "intensity": 0.5, "emotion": "neutral"}
            ],
            "pacing_data": {
                "scene_durations": [30, 45, 60, 75, 60],
                "emotion_intensities": [0.3, 0.5, quality_level, 0.8 * quality_level, 0.5],
                "climax_position": 0.7
            },
            "structure_data": {
                "has_beginning": True,
                "has_middle": True,
                "has_ending": True,
                "has_conflict": quality_level > 0.5,
                "has_resolution": quality_level > 0.6,
                "acts": [
                    {"name": "Act I", "quality": quality_level},
                    {"name": "Act II", "quality": quality_level},
                    {"name": "Act III", "quality": quality_level}
                ],
                "turning_points": [
                    {"name": "Inciting Incident", "position": 0.12, "importance": quality_level},
                    {"name": "First Plot Point", "position": 0.25, "importance": quality_level},
                    {"name": "Midpoint", "position": 0.5, "importance": quality_level},
                    {"name": "Second Plot Point", "position": 0.75, "importance": quality_level},
                    {"name": "Climax", "position": 0.9, "importance": quality_level}
                ],
                "themes": ["成长", "挑战", "友情"] if quality_level > 0.7 else ["成长"]
            },
            "engagement_data": {
                "emotional_impact": quality_level,
                "narrative_clarity": quality_level,
                "pacing_quality": quality_level,
                "relatability": quality_level,
                "novelty": quality_level
            }
        },
        # 用于直接测试的数据
        "coherence": coherence,
        "emotion_flow": emotion_flow,
        "pacing": pacing,
        "structure": structure,
        "engagement": engagement
    }
    
    return version

def simulate_quality_check(guardian: QualityGuardian, versions: List[Dict[str, Any]], user_group: str = "stable") -> None:
    """模拟质量检查
    
    Args:
        guardian: 质量守护者实例
        versions: 要检查的版本列表
        user_group: 用户组
    """
    logger.info(f"开始检查 {len(versions)} 个版本，用户组: {user_group}")
    
    for version in versions:
        version_id = version.get("id", "unknown")
        quality_level = version.get("quality_level", 0.0)
        logger.info(f"检查版本 {version_id}, 质量级别: {quality_level:.2f}")
        
        try:
            # 添加自定义检查器，直接使用版本中的质量数据
            if "coherence" in version:
                guardian.add_custom_checker(
                    "coherence_direct",
                    lambda v: v.get("coherence", 0.0),
                    0.7
                )
            
            if "emotion_flow" in version:
                guardian.add_custom_checker(
                    "emotion_flow_direct",
                    lambda v: v.get("emotion_flow", 0.0),
                    0.7
                )
            
            if "pacing" in version:
                guardian.add_custom_checker(
                    "pacing_direct",
                    lambda v: v.get("pacing", 0.0),
                    0.65
                )
            
            if "structure" in version:
                guardian.add_custom_checker(
                    "structure_direct",
                    lambda v: v.get("structure", 0.0),
                    0.72
                )
            
            if "engagement" in version:
                guardian.add_custom_checker(
                    "engagement_direct",
                    lambda v: v.get("engagement", 0.0),
                    0.68
                )
            
            # 执行质量监控
            guardian.monitor([version], user_group)
            logger.info(f"版本 {version_id} 通过质量检查")
            
            # 展示质量守护者状态
            status = guardian.get_status()
            logger.info(f"当前熔断器状态: {status['state']}")
            logger.info(f"失败计数: {status['failure_count']}/{status['failure_threshold']}")
            logger.info(f"成功计数: {status['success_count']}/{status['recovery_threshold']}")
            
        except QualityCollapseError as e:
            logger.error(f"版本 {version_id} 触发熔断: {str(e)}")
            
            # 展示熔断状态
            status = guardian.get_status()
            logger.error(f"熔断器状态: {status['state']}")
            logger.error(f"失败计数: {status['failure_count']}/{status['failure_threshold']}")
            
            # 如果熔断已触发，等待一段时间后继续
            if status['state'] == CircuitBreakerState.OPEN:
                logger.info("熔断已触发，暂停生成...")
                time.sleep(2)  # 实际应用中可能等待更长时间

def run_demo():
    """运行质量熔断器演示"""
    logger.info("=== 质量熔断器演示开始 ===")
    
    # 创建质量守护者，设置低阈值以便于演示
    guardian = QualityGuardian(failure_threshold=2, recovery_threshold=2)
    
    # 创建测试版本
    good_versions = [
        create_test_version("v1.0.0", 0.85),
        create_test_version("v1.1.0", 0.80),
        create_test_version("v1.2.0", 0.82)
    ]
    
    medium_versions = [
        create_test_version("v1.3.0", 0.70),
        create_test_version("v1.4.0", 0.65)
    ]
    
    bad_versions = [
        create_test_version("v1.5.0-bad", 0.55),
        create_test_version("v1.6.0-bad", 0.45),
        create_test_version("v1.7.0-bad", 0.40)
    ]
    
    recovery_versions = [
        create_test_version("v1.8.0", 0.75),
        create_test_version("v1.9.0", 0.80)
    ]
    
    # 第一阶段：正常质量，应该全部通过
    logger.info("\n=== 阶段1：高质量版本 ===")
    simulate_quality_check(guardian, good_versions)
    
    # 第二阶段：中等质量，应该全部通过
    logger.info("\n=== 阶段2：中等质量版本 ===")
    simulate_quality_check(guardian, medium_versions)
    
    # 第三阶段：低质量，应该触发熔断
    logger.info("\n=== 阶段3：低质量版本 ===")
    simulate_quality_check(guardian, bad_versions)
    
    # 展示熔断状态
    status = guardian.get_status()
    logger.info(f"当前熔断器状态: {status['state']}")
    
    # 如果已经触发熔断，手动重置熔断器
    if status['state'] == CircuitBreakerState.OPEN:
        logger.info("\n=== 手动重置熔断器 ===")
        guardian.manually_reset()
        
        status = guardian.get_status()
        logger.info(f"重置后熔断器状态: {status['state']}")
    
    # 第四阶段：恢复质量，应该成功恢复
    logger.info("\n=== 阶段4：恢复质量版本 ===")
    simulate_quality_check(guardian, recovery_versions)
    
    # 展示质量检查历史
    logger.info("\n=== 质量检查历史 ===")
    history = guardian.get_quality_history()
    for record in history:
        logger.info(f"版本 {record['version_id']}: {'通过' if record['passed'] else '未通过'}")
        for metric, score in record['metrics'].items():
            logger.info(f"  - {metric}: {score:.2f}")
    
    logger.info("\n=== 质量熔断器演示结束 ===")

def run_user_group_demo():
    """运行不同用户组质量阈值演示"""
    logger.info("\n=== 不同用户组质量阈值演示 ===")
    
    # 创建质量守护者
    guardian = QualityGuardian(failure_threshold=2)
    
    # 创建中等质量版本
    medium_version = create_test_version("v-medium", 0.65)
    
    # 为不同用户组测试相同版本
    user_groups = ["internal", "beta", "stable"]
    
    for group in user_groups:
        logger.info(f"\n测试用户组: {group}")
        
        try:
            # 重置熔断器状态
            guardian.manually_reset()
            
            # 为该版本添加自定义检查器
            guardian.add_custom_checker(
                "quality_score_direct",
                lambda v: v.get("quality_level", 0.0),
                0.7 if group == "stable" else (0.65 if group == "beta" else 0.6)
            )
            
            # 测试该用户组
            simulate_quality_check(guardian, [medium_version], group)
            
        except QualityCollapseError as e:
            logger.error(f"用户组 {group} 测试触发熔断: {str(e)}")
    
    logger.info("\n=== 用户组测试结束 ===")

if __name__ == "__main__":
    # 运行主演示
    run_demo()
    
    # 运行用户组演示
    run_user_group_demo() 