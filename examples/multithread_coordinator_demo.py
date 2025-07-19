#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
多线叙事协调器示例

演示如何使用多线叙事协调器分析和验证多条叙事线的一致性。
"""

import sys
import os
from pathlib import Path
import json

# 添加项目根目录到Python路径
current_dir = Path(__file__).resolve().parent
root_dir = current_dir.parent
if str(root_dir) not in sys.path:
    sys.path.append(str(root_dir))

from src.logic.multithread_coordinator import (
    NarrativeThreadIntegrator,
    validate_narrative_thread_consistency,
    ThreadConsistencyProblem
)


def load_demo_data():
    """加载示例数据"""
    # 创建示例故事线数据
    threads = [
        {
            "id": "main_thread",
            "name": "主要故事线",
            "description": "讲述主角小明的冒险",
            "properties": {
                "genre": "adventure",
                "importance": 1.0
            }
        },
        {
            "id": "side_thread",
            "name": "次要故事线",
            "description": "讲述配角小红的经历",
            "properties": {
                "genre": "drama",
                "importance": 0.7
            }
        },
        {
            "id": "background_thread",
            "name": "背景故事线",
            "description": "讲述世界背景和历史",
            "properties": {
                "genre": "history",
                "importance": 0.5
            }
        }
    ]
    
    # 创建示例事件数据
    events = [
        # 主线事件
        {
            "id": "main_start",
            "thread_ids": ["main_thread"],
            "timestamp": "00:01:00.000",
            "duration": "00:02:00.000",
            "location": "小镇",
            "characters": ["小明"],
            "description": "小明决定离开小镇",
            "type": "start"
        },
        {
            "id": "main_event1",
            "thread_ids": ["main_thread"],
            "timestamp": "00:05:00.000",
            "duration": "00:03:00.000",
            "location": "森林",
            "characters": ["小明"],
            "description": "小明在森林中迷路",
            "type": "event"
        },
        
        # 次要线事件
        {
            "id": "side_start",
            "thread_ids": ["side_thread"],
            "timestamp": "00:03:00.000",
            "duration": "00:01:30.000",
            "location": "学校",
            "characters": ["小红"],
            "description": "小红离开学校",
            "type": "start"
        },
        {
            "id": "side_event1",
            "thread_ids": ["side_thread"],
            "timestamp": "00:07:00.000",
            "duration": "00:02:00.000",
            "location": "市场",
            "characters": ["小红"],
            "description": "小红在市场购物",
            "type": "event"
        },
        
        # 背景线事件
        {
            "id": "background_start",
            "thread_ids": ["background_thread"],
            "timestamp": "00:00:30.000",
            "duration": "00:01:00.000",
            "location": "王国",
            "characters": ["国王"],
            "description": "王国建立的历史",
            "type": "start"
        },
        
        # 故事线交叉点
        {
            "id": "crossover1",
            "thread_ids": ["main_thread", "side_thread"],
            "timestamp": "00:10:00.000",
            "duration": "00:02:30.000",
            "location": "河边",
            "characters": ["小明", "小红"],
            "description": "小明和小红在河边相遇",
            "type": "crossover",
            "properties": {
                "is_conflict": False,
                "resolution": "友好相遇"
            }
        },
        
        # 主线结束
        {
            "id": "main_end",
            "thread_ids": ["main_thread"],
            "timestamp": "00:15:00.000",
            "duration": "00:01:00.000",
            "location": "山顶",
            "characters": ["小明"],
            "description": "小明到达目的地",
            "type": "conclusion"
        }
    ]
    
    # 故事线关系
    relations = [
        {
            "thread_id1": "main_thread",
            "thread_id2": "side_thread",
            "type": "CONVERGENT"
        },
        {
            "thread_id1": "background_thread",
            "thread_id2": "main_thread",
            "type": "EMBEDDED"
        }
    ]
    
    # 创建有问题的数据 - 时间悖论
    problem_events = events + [
        {
            "id": "paradox_event",
            "thread_ids": ["main_thread"],
            "timestamp": "00:10:30.000",  # 与crossover1时间重叠
            "duration": "00:01:00.000",
            "location": "山洞",  # 与crossover1位置不同
            "characters": ["小明"],  # 同一角色在同一时间出现在不同地点
            "description": "小明探索山洞",
            "type": "event"
        }
    ]
    
    valid_data = {
        "threads": threads,
        "events": events,
        "relations": relations
    }
    
    problem_data = {
        "threads": threads,
        "events": problem_events,
        "relations": relations
    }
    
    return valid_data, problem_data


def demo_thread_consistency():
    """演示故事线一致性验证"""
    print("\n===== 故事线一致性验证演示 =====")
    
    # 加载示例数据
    valid_data, problem_data = load_demo_data()
    
    # 创建协调器实例
    integrator = NarrativeThreadIntegrator()
    
    # 验证有效数据
    print("\n1. 验证正常的多线叙事数据")
    integrator.load_narrative_data(valid_data)
    problems = integrator.check_thread_consistency(valid_data["threads"])
    
    if not problems:
        print("  ✓ 验证通过，没有检测到问题")
    else:
        print(f"  × 检测到 {len(problems)} 个问题:")
        for i, problem in enumerate(problems, 1):
            print(f"    问题 {i}: {problem['message']}")
    
    # 验证有问题的数据
    print("\n2. 验证存在问题的多线叙事数据")
    integrator.reset()
    integrator.load_narrative_data(problem_data)
    problems = integrator.check_thread_consistency(problem_data["threads"])
    
    if problems:
        print(f"  ! 检测到 {len(problems)} 个问题:")
        for i, problem in enumerate(problems, 1):
            print(f"    问题 {i}: {problem['message']}")
            if "details" in problem:
                details = problem["details"]
                if "character_id" in details:
                    print(f"      角色: {details['character_id']}")
                if "location1" in details and "location2" in details:
                    print(f"      位置冲突: {details['location1']} 与 {details['location2']}")
                if "time" in details:
                    print(f"      时间: {details['time']}")
    else:
        print("  × 未检测到预期的问题")


def demo_thread_analysis():
    """演示故事线结构分析"""
    print("\n===== 故事线结构分析演示 =====")
    
    # 加载示例数据
    valid_data, _ = load_demo_data()
    
    # 创建协调器实例
    integrator = NarrativeThreadIntegrator()
    integrator.load_narrative_data(valid_data)
    
    # 分析故事线结构
    analysis = integrator.analyze_thread_structure()
    
    # 输出分析结果摘要
    print(f"\n故事线数量: {analysis['thread_count']}")
    print(f"事件数量: {analysis['event_count']}")
    print(f"交叉点数量: {analysis['crossover_count']}")
    
    print("\n主要故事线特征:")
    for thread_id, features in analysis["thread_features"].items():
        print(f"  线程 '{features['name']}':")
        print(f"    事件数量: {features['event_count']}")
        print(f"    时长: {format_time_ms(features['duration'])}")
        print(f"    主要角色: {', '.join(features['main_characters'])}")
    
    print("\n交叉点分析:")
    for i, crossover in enumerate(analysis["crossover_analysis"], 1):
        print(f"  交叉点 {i}: {crossover['description']}")
        print(f"    涉及故事线: {len(crossover['involved_threads'])}")
        print(f"    类型: {crossover['type']}")
        print(f"    角色: {', '.join(crossover['characters'])}")


def demo_suggestion_generation():
    """演示改进建议生成"""
    print("\n===== 改进建议生成演示 =====")
    
    # 创建一个不平衡的故事线数据
    threads = [
        {
            "id": "main_thread",
            "name": "主线",
            "description": "主要故事线"
        },
        {
            "id": "side_thread",
            "name": "次要线",
            "description": "次要故事线"
        },
        {
            "id": "abandoned_thread",
            "name": "未完成线",
            "description": "未完成的故事线"
        }
    ]
    
    events = [
        # 主线有多个事件
        {
            "id": "main1",
            "thread_ids": ["main_thread"],
            "timestamp": "00:01:00.000",
            "duration": "00:01:00.000",
            "location": "起点",
            "characters": ["主角"],
            "description": "主线开始",
            "type": "start"
        },
        {
            "id": "main2",
            "thread_ids": ["main_thread"],
            "timestamp": "00:03:00.000",
            "duration": "00:01:00.000",
            "location": "城市",
            "characters": ["主角"],
            "description": "主线发展",
            "type": "event"
        },
        {
            "id": "main3",
            "thread_ids": ["main_thread"],
            "timestamp": "00:05:00.000",
            "duration": "00:01:00.000",
            "location": "终点",
            "characters": ["主角"],
            "description": "主线结束",
            "type": "conclusion"
        },
        
        # 次要线只有一个事件 - 线程不平衡
        {
            "id": "side1",
            "thread_ids": ["side_thread"],
            "timestamp": "00:02:00.000",
            "duration": "00:00:30.000",
            "location": "侧边",
            "characters": ["配角"],
            "description": "次要线事件",
            "type": "event"
        },
        
        # 未完成线没有结论 - 线程放弃
        {
            "id": "abandoned1",
            "thread_ids": ["abandoned_thread"],
            "timestamp": "00:01:30.000",
            "duration": "00:01:00.000",
            "location": "远方",
            "characters": ["配角2"],
            "description": "未完成线开始",
            "type": "start"
        },
        {
            "id": "abandoned2",
            "thread_ids": ["abandoned_thread"],
            "timestamp": "00:02:30.000",
            "duration": "00:01:00.000",
            "location": "山区",
            "characters": ["配角2"],
            "description": "未完成线发展",
            "type": "event"
            # 没有结论事件
        }
    ]
    
    unbalanced_data = {
        "threads": threads,
        "events": events
    }
    
    # 创建协调器并分析
    integrator = NarrativeThreadIntegrator()
    integrator.load_narrative_data(unbalanced_data)
    problems = integrator.check_thread_consistency(threads)
    
    print(f"检测到 {len(problems)} 个问题")
    
    # 生成建议
    suggestions = integrator.generate_thread_suggestions()
    
    print("\n生成的建议:")
    for category, category_suggestions in suggestions.items():
        if category_suggestions:
            print(f"\n{category.upper()} 建议:")
            for i, suggestion in enumerate(category_suggestions, 1):
                print(f"  {i}. {suggestion}")
    
    # 为两个故事线生成交叉点建议
    print("\n为主线和次要线生成交叉点建议:")
    crossover_suggestions = integrator.generate_crossover_suggestions("main_thread", "side_thread")
    
    for i, suggestion in enumerate(crossover_suggestions, 1):
        print(f"  建议 {i}: {suggestion['description']}")
        print(f"    类型: {suggestion['type']}")
        if "location" in suggestion:
            print(f"    位置: {suggestion['location']}")


def demo_convenience_function():
    """演示便捷函数使用"""
    print("\n===== 便捷函数使用演示 =====")
    
    # 加载示例数据
    valid_data, problem_data = load_demo_data()
    
    # 使用便捷函数验证
    print("1. 验证有效数据")
    result = validate_narrative_thread_consistency(valid_data["threads"])
    print(f"  验证结果: {'有效' if result['valid'] else '无效'}")
    print(f"  问题数量: {len(result['problems'])}")
    
    # 验证问题数据
    print("\n2. 验证有问题的数据")
    result = validate_narrative_thread_consistency(problem_data["threads"])
    print(f"  验证结果: {'有效' if result['valid'] else '无效'}")
    print(f"  问题数量: {len(result['problems'])}")
    
    if result["problems"]:
        print("\n  检测到的问题:")
        for i, problem in enumerate(result["problems"], 1):
            print(f"    {i}. {problem['message']}")


def format_time_ms(ms):
    """格式化毫秒为时间字符串"""
    hours = ms // 3600000
    ms %= 3600000
    minutes = ms // 60000
    ms %= 60000
    seconds = ms // 1000
    ms %= 1000
    
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{ms:03d}"


if __name__ == "__main__":
    print("多线叙事协调器演示程序\n")
    
    # 创建输出目录
    os.makedirs("./output", exist_ok=True)
    
    # 运行各个演示
    demo_thread_consistency()
    demo_thread_analysis()
    demo_suggestion_generation()
    demo_convenience_function()
    
    print("\n演示完成!") 