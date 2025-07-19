#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自动化压力测试模块演示

演示如何使用压力测试模块来测试系统稳定性和恢复能力
"""

import os
import sys
import time
import argparse
from typing import Dict, Any

# 添加src到路径中
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.quality.stress_test import ChaosMonkey, ResourceLimiter, StressTestRunner
from loguru import logger

# 设置日志级别
logger.remove()
logger.add(sys.stderr, level="INFO")


def run_chaos_demo(duration: int = 30) -> None:
    """
    运行混沌测试演示
    
    Args:
        duration: 测试持续时间(秒)
    """
    logger.info("=== 开始混沌测试演示 ===")
    monkey = ChaosMonkey()
    
    for scenario in monkey.FAILURE_SCENARIOS:
        logger.info(f"测试故障场景: {scenario}")
        recovery_time = monkey._trigger(scenario)
        
        if recovery_time > 0:
            logger.success(f"故障恢复成功，耗时: {recovery_time:.2f}秒")
        else:
            logger.error(f"故障恢复失败")
        
        # 暂停一会儿让系统冷静下来
        time.sleep(2.0)
    
    logger.info("=== 混沌测试演示完成 ===")


def run_resource_limiter_demo() -> None:
    """运行资源限制器演示"""
    logger.info("=== 开始资源限制器演示 ===")
    limiter = ResourceLimiter()
    
    try:
        # 限制CPU
        logger.info("测试CPU限制...")
        limiter.limit_cpu(0.5)  # 限制到50%可用
        logger.info("CPU限制已应用，等待5秒...")
        time.sleep(5.0)
        
        # 释放CPU
        limiter.release_cpu()
        logger.info("CPU资源已释放")
        
        # 限制IO
        logger.info("测试IO限制...")
        limiter.limit_io(0.7)  # 70%的IO压力
        logger.info("IO限制已应用，等待5秒...")
        time.sleep(5.0)
        
        # 释放IO
        limiter.release_io()
        logger.info("IO资源已释放")
        
        # 限制内存
        logger.info("测试内存限制...")
        success = limiter.limit_memory(0.6)  # 限制到60%可用
        if success:
            logger.info("内存限制已应用，等待5秒...")
            time.sleep(5.0)
            
            # 释放内存
            limiter.release_memory()
            logger.info("内存资源已释放")
        else:
            logger.warning("内存限制应用失败，跳过")
        
    finally:
        # 确保释放所有资源
        limiter.release_all()
    
    logger.info("=== 资源限制器演示完成 ===")


def run_stress_test_demo() -> None:
    """运行完整压力测试演示"""
    logger.info("=== 开始压力测试演示 ===")
    runner = StressTestRunner()
    
    try:
        # 运行短时间CPU压力测试
        logger.info("运行CPU压力测试...")
        cpu_result = runner.run_cpu_stress_test(
            duration=10,         # 10秒测试
            cpu_limit_start=0.7, # 70%可用
            cpu_limit_end=0.3,   # 30%可用
            steps=2              # 两个步骤
        )
        
        success = cpu_result.get("success", False)
        logger.info(f"CPU压力测试完成，结果: {'成功' if success else '失败'}")
        
        # 短暂暂停
        time.sleep(5.0)
        
        # 运行混沌测试
        logger.info("运行混沌测试...")
        chaos_result = runner.run_chaos_test(
            duration=15,         # 15秒测试
            failure_interval=5   # 每5秒注入一次故障
        )
        
        recovery_rate = chaos_result.get("recovery_rate", 0.0)
        logger.info(f"混沌测试完成，恢复率: {recovery_rate*100:.1f}%")
        
    finally:
        # 确保停止所有测试
        runner.stop_all_tests()
    
    logger.info("=== 压力测试演示完成 ===")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="压力测试模块演示")
    parser.add_argument("--demo", choices=["chaos", "resource", "stress", "all"], 
                        default="all", help="要运行的演示类型")
    parser.add_argument("--duration", type=int, default=30, 
                        help="测试持续时间(秒)")
    
    args = parser.parse_args()
    
    logger.info(f"开始演示: {args.demo}")
    
    if args.demo == "chaos" or args.demo == "all":
        run_chaos_demo(args.duration)
    
    if args.demo == "resource" or args.demo == "all":
        run_resource_limiter_demo()
    
    if args.demo == "stress" or args.demo == "all":
        run_stress_test_demo()
    
    logger.info("演示结束")


if __name__ == "__main__":
    main() 