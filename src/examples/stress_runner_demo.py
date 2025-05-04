#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
压力测试运行器演示

演示如何使用压力测试运行器执行综合压力测试
"""

import os
import sys
import time
import json
import traceback

# 添加src到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# 确保目录存在
os.makedirs("data/stress_test_results", exist_ok=True)
os.makedirs("data/stress_test_io", exist_ok=True)
os.makedirs("data/stress_test_files", exist_ok=True)
os.makedirs("logs", exist_ok=True)

# 设置日志记录
import logging
logging.basicConfig(level=logging.INFO)

# 引入压力测试模块
try:
    from src.quality.stress_test import StressTestRunner
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保已安装所需依赖:")
    print("  - psutil: 用于系统资源监控")
    print("  - numpy: 用于数据处理")
    print("  - torch (可选): 用于GPU测试")
    sys.exit(1)

def main():
    """压力测试运行器演示"""
    print("开始压力测试运行器演示")
    
    # 创建压力测试运行器
    runner = StressTestRunner()
    
    try:
        # 运行短时CPU压力测试
        print("\n1. 运行CPU压力测试(5秒)...")
        cpu_result = runner.run_cpu_stress_test(
            duration=5,  # 短时测试
            cpu_limit_start=0.7,  # 开始保留70%可用
            cpu_limit_end=0.5,    # 结束保留50%可用
            steps=1               # 只有一个步骤
        )
        
        # 显示结果摘要
        if cpu_result.get("success", False):
            print("   CPU压力测试成功")
        else:
            print("   CPU压力测试失败")
        
        if "steps" in cpu_result and len(cpu_result["steps"]) > 0:
            step = cpu_result["steps"][0]
            if "actual_duration" in step:
                print(f"   实际耗时: {step['actual_duration']:.2f}秒")
        
        # 运行混沌测试
        print("\n2. 运行混沌测试(10秒)...")
        chaos_result = runner.run_chaos_test(
            duration=10,          # 短时测试
            failure_interval=3    # 每3秒注入一次故障
        )
        
        # 显示结果摘要
        if "recovery_rate" in chaos_result:
            print(f"   恢复率: {chaos_result['recovery_rate']*100:.1f}%")
        
        if "failures" in chaos_result:
            print(f"   注入故障数: {len(chaos_result['failures'])}")
            
            # 显示故障类型统计
            scenario_counts = {}
            for failure in chaos_result["failures"]:
                scenario = failure.get("scenario", "unknown")
                scenario_counts[scenario] = scenario_counts.get(scenario, 0) + 1
            
            print("   故障类型统计:")
            for scenario, count in scenario_counts.items():
                print(f"     - {scenario}: {count}")
        
        # 获取汇总结果
        summary = runner.get_test_results()
        print("\n压力测试汇总:")
        print(f"总测试数: {summary.get('total_tests', 0)}")
        print(f"成功测试: {summary.get('succeeded_tests', 0)}")
        print(f"失败测试: {summary.get('failed_tests', 0)}")
        
    except Exception as e:
        print(f"运行压力测试时发生错误: {e}")
        print(traceback.format_exc())
    finally:
        # 停止所有测试
        runner.stop_all_tests()
    
    print("\n演示完成")

if __name__ == "__main__":
    main() 