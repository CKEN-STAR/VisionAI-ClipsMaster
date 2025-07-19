#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 熔断事件溯源系统演示
展示记录和分析熔断事件的功能
"""

import os
import sys
import time
import json
import logging
import argparse
import random
import gc
import datetime
from typing import Dict, Any

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 导入熔断事件溯源系统
from src.fuse.event_tracer import (
    get_audit, 
    log_event,
    log_fuse_triggered,
    log_fuse_completed,
    log_resource_released,
    log_memory_snapshot,
    log_error,
    log_gc_performed,
    log_system_state_change,
    EventType,
    get_analyzer,
    init_event_tracer,
    start_trace,
    end_trace
)

# 如果可用，导入其他熔断系统组件
try:
    from src.fuse.safe_executor import get_executor, safe_execute, register_action, register_resource
    safe_executor_available = True
except ImportError:
    safe_executor_available = False

try:
    from src.fuse.recovery_manager import get_recovery_manager, save_system_state, restore_system_state
    recovery_available = True
except ImportError:
    recovery_available = False

try:
    from src.fuse.effect_validator import get_validator, execute_with_validation
    validator_available = True
except ImportError:
    validator_available = False


def simulate_memory_usage():
    """模拟内存使用变化"""
    # 创建一些大对象
    data_list = []
    for i in range(5):
        # 每个对象约10MB
        data = [random.random() for _ in range(1250000)]
        data_list.append(data)
        
        # 记录内存快照
        log_memory_snapshot(f"allocation_{i}")
        time.sleep(0.2)
    
    # 返回占用内存的数据
    return data_list


def simulate_fuse_events(count=3):
    """模拟熔断事件序列"""
    for i in range(count):
        # 记录熔断触发
        trigger_id = log_fuse_triggered({
            "reason": "memory_pressure",
            "threshold": 85.0 + random.random() * 10,
            "current": 90.0 + random.random() * 5,
            "sequence": i + 1
        })
        
        # 记录开始追踪
        trace_id = start_trace("memory_recovery", {
            "trigger_id": trigger_id,
            "level": "warning" if i == 0 else "critical" if i == 1 else "emergency"
        })
        
        # 模拟执行一些操作
        actions_taken = []
        memory_freed = 0.0
        
        # 总是执行GC
        gc_start = time.time()
        collected = gc.collect()
        gc_duration = time.time() - gc_start
        
        log_gc_performed(collected, gc_duration)
        actions_taken.append("force_gc")
        memory_freed += 10.0 + random.random() * 20
        
        # 模拟释放一些资源
        resources = ["model_cache", "audio_buffer", "frame_cache", "subtitle_index"]
        for j in range(random.randint(1, 3)):
            resource = random.choice(resources)
            size = 50.0 + random.random() * 100
            
            log_resource_released(
                resource_id=f"{resource}_{j}",
                size_mb=size,
                details={
                    "resource_type": resource,
                    "priority": "high" if j == 0 else "medium",
                    "in_use": random.random() > 0.7
                }
            )
            
            actions_taken.append(f"release_{resource}")
            memory_freed += size
            time.sleep(0.1)
        
        # 记录结束追踪
        end_trace("memory_recovery", {
            "trigger_id": trigger_id,
            "actions_count": len(actions_taken)
        })
        
        # 记录熔断完成
        log_fuse_completed({
            "success": True,
            "actions_taken": actions_taken,
            "total_freed_mb": memory_freed,
            "duration": 0.5 + random.random() * 1.0
        }, trigger_id)
        
        # 记录系统状态变化
        log_system_state_change(
            old_state="critical" if i > 0 else "warning",
            new_state="normal" if i < count - 1 else "warning",
            details={
                "memory_before": 92.5 - i * 2,
                "memory_after": 75.0 - i * 5
            }
        )
        
        # 间隔一段时间
        time.sleep(0.5 + random.random() * 0.5)


def simulate_error_recovery():
    """模拟错误和恢复"""
    # 记录错误
    error_id = log_error(
        error_type="memory_allocation_error",
        message="无法分配内存给新模型",
        details={
            "model": "text_analyzer",
            "required_mb": 850,
            "available_mb": 300
        }
    )
    
    # 记录恢复尝试
    recovery_trace = start_trace("error_recovery", {
        "error_id": error_id,
        "strategy": "release_and_retry"
    })
    
    # 模拟释放一些资源
    log_resource_released(
        resource_id="model_main",
        size_mb=1200,
        details={
            "resource_type": "model",
            "forced": True
        }
    )
    
    # 记录GC
    log_gc_performed(2500, 1.2)
    
    # 结束恢复追踪
    end_trace("error_recovery", {
        "error_id": error_id,
        "success": True,
        "freed_mb": 1450
    })
    
    # 记录系统状态变化
    log_system_state_change(
        old_state="emergency",
        new_state="normal",
        details={
            "recovery_id": recovery_trace,
            "error_resolved": True
        }
    )


def demonstrate_safe_executor_integration():
    """演示与安全熔断执行器的集成"""
    if not safe_executor_available:
        print("安全熔断执行器组件未导入，跳过集成演示")
        return
    
    print("演示与安全熔断执行器的集成...")
    
    # 注册测试动作
    def test_action(name, duration=0.5):
        """测试动作"""
        print(f"执行测试动作: {name}, 持续: {duration}秒")
        time.sleep(duration)
        return {"status": "completed", "name": name}
    
    register_action("test_action", test_action)
    
    # 注册测试资源
    data = [0] * 1000000  # 约8MB
    
    def release_data(resource):
        """释放数据资源"""
        resource.clear()
        return True
    
    register_resource("test_data", data, release_data)
    
    # 执行动作 (如果有效果验证器，会触发事件记录)
    if validator_available:
        print("通过验证器执行动作...")
        result, success = execute_with_validation("test_action", name="integration_test")
    else:
        print("直接执行动作...")
        result = safe_execute("test_action", name="integration_test")
    
    print(f"动作执行结果: {result}")
    
    # 释放资源 (会触发资源释放事件)
    from src.fuse.safe_executor import release_resource

# 内存使用警告阈值（百分比）
MEMORY_WARNING_THRESHOLD = 80

    release_resource("test_data")
    
    # 等待事件记录完成
    time.sleep(0.2)


def analyze_events():
    """分析记录的事件"""
    # 获取分析器
    analyzer = get_analyzer()
    
    # 获取内存趋势
    memory_trend = analyzer.get_memory_trend()
    
    print("\n内存使用趋势:")
    print("=" * 60)
    for point in memory_trend:
        timestamp = datetime.datetime.fromtimestamp(point['timestamp']).strftime('%H:%M:%S')
        if 'memory' in point and 'system' in point['memory']:
            memory_percent = point['memory']['system'].get('percent', 0)
            print(f"{timestamp} - 系统内存使用: {memory_percent:.1f}%")
    
    # 获取操作时间统计
    timings = analyzer.get_action_timing()
    
    print("\n操作执行时间统计:")
    print("=" * 60)
    for timing in timings:
        action = timing['action']
        exec_time = timing['execution_time']
        print(f"{action} - 执行时间: {exec_time:.3f}秒")
    
    # 获取熔断效率
    efficiency = analyzer.get_fuse_efficiency()
    
    print("\n熔断效率统计:")
    print("=" * 60)
    print(f"总熔断次数: {efficiency['total_fuses']}")
    print(f"完成次数: {efficiency['completed_fuses']}")
    print(f"成功率: {efficiency['success_rate']:.1f}%")
    print(f"平均响应时间: {efficiency['avg_response_time']:.3f}秒")
    print(f"平均内存释放: {efficiency['avg_memory_freed']:.1f}MB")
    
    # 恢复状态统计
    recovery_status = analyzer.get_recovery_status()
    
    print("\n恢复状态统计:")
    print("=" * 60)
    for status in recovery_status:
        timestamp = datetime.datetime.fromtimestamp(status['start_time']).strftime('%H:%M:%S')
        completed = status['completed']
        success = status.get('success', False)
        
        status_str = "成功" if completed and success else \
                    "失败" if completed else "未完成"
                    
        print(f"{timestamp} - 状态: {status_str}")
        
        if completed and 'recovery_time' in status:
            print(f"  恢复时间: {status['recovery_time']:.3f}秒")


def save_events_to_file(filename="fuse_events_report.json"):
    """将事件保存到文件"""
    audit = get_audit()
    
    # 查询所有事件
    all_events = audit.query_events(limit=1000)
    
    # 保存到文件
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(all_events, f, indent=2, ensure_ascii=False)
    
    print(f"\n事件报告已保存到: {filename}")
    print(f"共 {len(all_events)} 个事件")


def run_demo(args):
    """运行熔断事件溯源系统演示"""
    # 设置日志
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("初始化熔断事件溯源系统...")
    init_event_tracer()
    
    # 模拟一些内存使用
    print("\n模拟内存使用变化...")
    data = simulate_memory_usage()
    
    # 模拟熔断事件
    print("\n模拟熔断事件序列...")
    simulate_fuse_events(count=args.events)
    
    # 模拟错误和恢复
    print("\n模拟错误和恢复...")
    simulate_error_recovery()
    
    # 与安全熔断执行器集成
    if args.integration:
        demonstrate_safe_executor_integration()
    
    # 分析事件
    if args.analyze:
        print("\n分析记录的事件...")
        analyze_events()
    
    # 保存事件报告
    if args.save:
        save_events_to_file(args.output)
    
    # 释放模拟数据
    print("\n清理模拟数据...")
    del data
    gc.collect()
    
    print("\n演示完成!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VisionAI-ClipsMaster 熔断事件溯源系统演示")
    parser.add_argument("--events", type=int, default=3, help="模拟的熔断事件数量")
    parser.add_argument("--integration", action="store_true", help="演示与其他组件的集成")
    parser.add_argument("--analyze", action="store_true", help="分析记录的事件")
    parser.add_argument("--save", action="store_true", help="保存事件到文件")
    parser.add_argument("--output", type=str, default="fuse_events_report.json", help="输出文件名")
    parser.add_argument("-v", "--verbose", action="store_true", help="输出详细日志")
    
    args = parser.parse_args()
    
    # 如果没有指定任何操作，默认全部执行
    if not (args.analyze or args.save or args.integration):
        args.analyze = True
        args.save = True
        args.integration = True
    
    run_demo(args) 