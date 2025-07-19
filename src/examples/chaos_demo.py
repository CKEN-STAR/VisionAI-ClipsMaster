#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
混沌测试演示

演示如何使用混沌测试功能注入故障并测试系统恢复能力
"""

import os
import sys
import time

# 添加src到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# 确保目录存在
os.makedirs("data/stress_test_files", exist_ok=True)
os.makedirs("logs", exist_ok=True)

# 设置日志记录
import logging
logging.basicConfig(level=logging.INFO)

# 引入混沌测试模块
from src.quality.stress_test import ChaosMonkey

def main():
    """混沌测试演示"""
    print("开始混沌测试演示")
    
    # 创建混沌测试工具
    monkey = ChaosMonkey()
    
    # 测试文件损坏和恢复
    print("\n1. 测试文件损坏和恢复:")
    recovery_time = monkey._trigger_file_corruption()
    
    if recovery_time > 0:
        print(f"   文件恢复成功，耗时: {recovery_time:.2f}秒")
    else:
        print("   文件恢复失败")
    
    # 测试CPU负载
    print("\n2. 测试CPU负载:")
    recovery_time = monkey._trigger_cpu_throttling()
    
    if recovery_time > 0:
        print(f"   CPU负载恢复成功，耗时: {recovery_time:.2f}秒")
    else:
        print("   CPU负载恢复失败")
    
    # 测试磁盘延迟
    print("\n3. 测试磁盘延迟:")
    recovery_time = monkey._trigger_disk_latency()
    
    if recovery_time > 0:
        print(f"   磁盘延迟恢复成功，耗时: {recovery_time:.2f}秒")
    else:
        print("   磁盘延迟恢复失败")
    
    # 打印恢复统计
    total = monkey.recovery_stats["total_failures"]
    success = monkey.recovery_stats["successful_recoveries"]
    failed = monkey.recovery_stats["failed_recoveries"]
    
    print("\n混沌测试统计:")
    print(f"总故障数: {total}")
    print(f"成功恢复: {success}")
    print(f"恢复失败: {failed}")
    
    if total > 0:
        success_rate = (success / total) * 100
        print(f"恢复成功率: {success_rate:.1f}%")
    
    print("\n演示完成")

if __name__ == "__main__":
    main() 