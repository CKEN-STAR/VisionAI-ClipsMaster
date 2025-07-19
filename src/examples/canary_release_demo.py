#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
灰度发布系统演示程序

该脚本展示如何使用灰度发布系统管理不同版本的发布流程，
包括创建发布计划、执行渐进式发布、监控指标和回滚操作。
"""

import os
import sys
import time
import random
import logging
import argparse
from typing import Dict, List, Any, Optional
from datetime import datetime

# 添加项目根目录到sys.path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(script_dir))
sys.path.insert(0, project_root)

from src.versioning import (
    CanaryDeployer,
    UserGroup,
    ReleaseStage,
    VersionStatus,
    EvolutionTracker
)

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("canary_release_demo")

def create_version_history(tracker: EvolutionTracker) -> List[str]:
    """创建版本历史
    
    Args:
        tracker: 版本追踪器实例
        
    Returns:
        版本ID列表
    """
    versions = []
    
    # 基础版本 - 初始功能
    base_version = "v1.0.0"
    tracker.add_version(base_version, None, {
        "name": "初始版本",
        "description": "基础混剪功能发布版",
        "features": ["基础混剪", "自动场景分割"],
        "stability": 0.95
    })
    versions.append(base_version)
    
    # 功能增强版
    enhanced_version = "v1.1.0"
    tracker.add_version(enhanced_version, base_version, {
        "name": "功能增强版",
        "description": "增加字幕增强和情感分析",
        "features": ["基础混剪", "自动场景分割", "字幕增强", "情感分析"],
        "stability": 0.92
    })
    versions.append(enhanced_version)
    
    # 修复版本
    fixed_version = "v1.1.1"
    tracker.add_version(fixed_version, enhanced_version, {
        "name": "修复版",
        "description": "修复情感分析中的问题",
        "features": ["基础混剪", "自动场景分割", "字幕增强", "情感分析", "错误修复"],
        "stability": 0.98
    })
    versions.append(fixed_version)
    
    # 性能优化版
    optimized_version = "v1.2.0"
    tracker.add_version(optimized_version, fixed_version, {
        "name": "性能优化版",
        "description": "提高处理速度，降低内存占用",
        "features": ["基础混剪", "自动场景分割", "字幕增强", "情感分析", "错误修复", "性能优化"],
        "stability": 0.96
    })
    versions.append(optimized_version)
    
    # 测试版2.0 - 引入AI创意助手
    alpha_version = "v2.0.0-alpha"
    tracker.add_version(alpha_version, optimized_version, {
        "name": "AI创意助手测试版",
        "description": "引入AI创意助手功能的alpha测试版",
        "features": ["基础混剪", "自动场景分割", "字幕增强", "情感分析", "错误修复", "性能优化", "AI创意助手"],
        "stability": 0.75,
        "is_experimental": True
    })
    versions.append(alpha_version)
    
    # 测试版2.0 Beta - 改进AI创意助手
    beta_version = "v2.0.0-beta"
    tracker.add_version(beta_version, alpha_version, {
        "name": "AI创意助手Beta版",
        "description": "AI创意助手的改进版本",
        "features": ["基础混剪", "自动场景分割", "字幕增强", "情感分析", "错误修复", "性能优化", "AI创意助手2.0"],
        "stability": 0.85,
        "is_experimental": True
    })
    versions.append(beta_version)
    
    return versions

def simulate_user_activity(deployer: CanaryDeployer, release_id: str, user_count: int = 100) -> Dict[str, Any]:
    """模拟多个用户使用不同版本的情况
    
    Args:
        deployer: 灰度发布管理器实例
        release_id: 发布计划ID
        user_count: 模拟的用户数量
        
    Returns:
        模拟结果统计
    """
    logger.info(f"模拟 {user_count} 个用户的活动...")
    
    results = {
        "total_users": user_count,
        "success_count": 0,
        "error_count": 0,
        "version_distribution": {},
        "group_distribution": {}
    }
    
    # 生成用户ID
    user_ids = [f"user_{i}" for i in range(user_count)]
    
    # 为每个用户确定版本
    for user_id in user_ids:
        version_result = deployer.get_user_version(user_id, release_id)
        
        if not version_result["success"]:
            logger.warning(f"用户 {user_id} 无法获取版本: {version_result.get('message', '')}")
            continue
        
        version_id = version_result["version_id"]
        user_group = version_result["user_group"]
        deployment_id = version_result.get("deployment_id")
        
        # 记录版本分布情况
        if version_id not in results["version_distribution"]:
            results["version_distribution"][version_id] = 0
        results["version_distribution"][version_id] += 1
        
        # 记录用户组分布情况
        if user_group not in results["group_distribution"]:
            results["group_distribution"][user_group] = 0
        results["group_distribution"][user_group] += 1
        
        # 模拟成功率，测试版本成功率低于稳定版本
        if "alpha" in version_id or "beta" in version_id:
            success_rate = 0.85
        else:
            success_rate = 0.98
        
        # 随机确定操作是否成功
        if random.random() < success_rate:
            results["success_count"] += 1
            # 报告成功指标
            if deployment_id:
                deployer.report_metrics(deployment_id, True, user_id=user_id)
        else:
            results["error_count"] += 1
            # 报告错误指标
            if deployment_id:
                error_message = random.choice([
                    "处理超时",
                    "内存不足",
                    "输出文件损坏",
                    "模型加载失败"
                ])
                deployer.report_metrics(deployment_id, False, error_message=error_message, user_id=user_id)
    
    logger.info(f"模拟完成: 成功 {results['success_count']}, 失败 {results['error_count']}")
    
    # 按版本显示分布情况
    print("\n版本分布情况:")
    print("-" * 50)
    for version, count in results["version_distribution"].items():
        percentage = (count / user_count) * 100
        print(f"{version}: {count} 用户 ({percentage:.1f}%)")
    
    # 按用户组显示分布情况
    print("\n用户组分布情况:")
    print("-" * 50)
    for group, count in results["group_distribution"].items():
        percentage = (count / user_count) * 100
        print(f"{group}: {count} 用户 ({percentage:.1f}%)")
    
    return results

def print_release_info(deployer: CanaryDeployer, release_id: str) -> None:
    """打印发布计划详细信息
    
    Args:
        deployer: 灰度发布管理器实例
        release_id: 发布计划ID
    """
    result = deployer.get_release_info(release_id)
    if not result["success"]:
        logger.error(f"获取发布计划信息失败: {result.get('message', '')}")
        return
    
    release_info = result["release_info"]
    
    print("\n发布计划详细信息:")
    print("=" * 50)
    print(f"ID: {release_info['id']}")
    print(f"名称: {release_info['name']}")
    print(f"描述: {release_info['description']}")
    print(f"阶段: {release_info['stage']}")
    print(f"状态: {release_info['status']}")
    print(f"版本: {', '.join(release_info['versions'])}")
    print(f"创建时间: {release_info['created_at']}")
    print(f"更新时间: {release_info['updated_at']}")
    
    # 打印指标
    print("\n指标统计:")
    print("-" * 50)
    print(f"成功率: {release_info['metrics']['success_rate'] * 100:.1f}%")
    print(f"错误数: {release_info['metrics']['error_count']}")
    
    # 打印部署情况
    print("\n部署情况:")
    print("-" * 50)
    for i, deployment in enumerate(release_info["deployments"]):
        print(f"部署 {i+1}:")
        print(f"  目标用户组: {deployment['user_group']}")
        print(f"  部署版本: {', '.join(deployment['versions']) if isinstance(deployment['versions'], list) else deployment['versions']}")
        print(f"  权重: {deployment['weight'] * 100:.1f}%")
        print(f"  状态: {deployment['status']}")
        print(f"  使用次数: {deployment['metrics'].get('usage_count', 0)}")
        print(f"  成功次数: {deployment['metrics'].get('success_count', 0)}")
        print(f"  错误次数: {deployment['metrics'].get('error_count', 0)}")
        print()
    
    # 如果有回滚信息，打印回滚详情
    if "rollback" in release_info:
        rollback = release_info["rollback"]
        print("\n回滚信息:")
        print("-" * 50)
        print(f"从版本: {', '.join(rollback['from_versions'])}")
        print(f"到版本: {rollback['to_version']}")
        print(f"回滚原因: {rollback['reason']}")
        print(f"回滚时间: {rollback['rollback_at']}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="灰度发布系统演示程序")
    parser.add_argument("--users", "-u", type=int, default=100, help="模拟的用户数量")
    parser.add_argument("--simulate-twice", "-s", action="store_true", help="是否模拟两次用户活动（回滚前和回滚后）")
    args = parser.parse_args()
    
    # 初始化数据目录
    data_dir = os.path.join(project_root, "data")
    os.makedirs(data_dir, exist_ok=True)
    
    # 初始化版本追踪器和灰度发布管理器
    db_path = os.path.join(data_dir, "demo_versions.json")
    tracker = EvolutionTracker(db_path)
    
    canary_db_path = os.path.join(data_dir, "demo_canary.json")
    deployer = CanaryDeployer(canary_db_path)
    
    # 创建版本历史
    versions = create_version_history(tracker)
    
    # 创建发布计划
    release_id = f"release_{int(time.time())}"
    result = deployer.create_release(
        release_id=release_id,
        versions=versions,
        name="混剪工具2.0版本发布",
        description="引入AI创意助手功能的灰度发布计划",
        stage=ReleaseStage.BETA
    )
    
    if not result["success"]:
        logger.error(f"创建发布计划失败: {result.get('message', '')}")
        return
    
    logger.info(f"已创建发布计划: {release_id}")
    
    # 执行灰度发布
    user_groups = UserGroup.get_all_groups()
    result = deployer.gradual_release(release_id, user_groups)
    
    if not result["success"]:
        logger.error(f"执行灰度发布失败: {result.get('message', '')}")
        return
    
    logger.info("灰度发布设置完成")
    
    # 模拟用户活动
    if args.simulate_twice:
        print("\n[第一轮] 回滚前模拟用户活动:")
        simulate_user_activity(deployer, release_id, args.users)
        
        # 输出发布计划详情
        print_release_info(deployer, release_id)
        
        # 执行回滚操作
        print("\n现在执行回滚操作...")
        rollback_result = deployer.rollback_release(release_id, "v1.2.0")
        if rollback_result["success"]:
            logger.info(f"回滚成功: {rollback_result['message']}")
        else:
            logger.error(f"回滚失败: {rollback_result.get('message', '')}")
            return
        
        # 模拟回滚后的用户活动
        print("\n[第二轮] 回滚后模拟用户活动:")
        simulate_user_activity(deployer, release_id, args.users)
    else:
        # 只模拟一次用户活动
        simulate_user_activity(deployer, release_id, args.users)
    
    # 输出最终发布计划详情
    print_release_info(deployer, release_id)
    
    logger.info("演示完成")

if __name__ == "__main__":
    main() 