#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
因果链验证器示例

演示如何使用因果链验证器检测视频剧情的因果一致性。
"""

import sys
import os
import json
from pathlib import Path
from pprint import pprint

# 添加项目根目录到Python路径
current_dir = Path(__file__).resolve().parent
root_dir = current_dir.parent
if str(root_dir) not in sys.path:
    sys.path.append(str(root_dir))

from src.logic import CausalityValidator, validate_causality, CausalityType
from src.utils.exceptions import CausalityBreakError


def create_demo_story():
    """创建演示用的故事事件序列"""
    # 一个推理故事的事件序列
    story = [
        {
            "id": "event1",
            "type": "problem",
            "description": "村庄里发生一系列神秘失窃案",
            "characters": ["村民", "村长"],
            "importance": 0.9
        },
        {
            "id": "event2",
            "type": "clue",
            "description": "目击者称看到黑影在夜间活动",
            "characters": ["目击者", "侦探"],
            "importance": 0.7,
            "causes": [
                {"id": "event1", "relation": "DIRECT"}
            ]
        },
        {
            "id": "event3",
            "description": "侦探发现指向老磨坊的足迹",
            "characters": ["侦探"],
            "importance": 0.6,
            "causes": [
                {"id": "event2", "relation": "DIRECT"}
            ]
        },
        {
            "id": "event4",
            "description": "侦探在老磨坊附近埋伏",
            "characters": ["侦探"],
            "importance": 0.8,
            "causes": [
                {"id": "event3", "relation": "DIRECT"}
            ]
        },
        {
            "id": "event5",
            "type": "resolution",
            "description": "捉到了偷窃的狐狸，解开了谜团",
            "characters": ["侦探", "村民", "狐狸"],
            "importance": 0.9,
            "causes": [
                {"id": "event4", "relation": "DIRECT"}
            ]
        }
    ]
    return story


def create_problematic_story():
    """创建存在因果问题的故事事件序列"""
    # 一个存在因果问题的故事
    story = [
        {
            "id": "event1",
            "type": "problem",
            "description": "城市被大雾笼罩，能见度急剧下降",
            "characters": ["市民", "气象局"],
            "importance": 0.7
        },
        {
            "id": "event2",
            "description": "学校宣布停课一天",
            "characters": ["校长", "学生"],
            "importance": 0.5,
            "causes": [
                {"id": "event1", "relation": "DIRECT"}
            ]
        },
        {
            "id": "event3",
            "type": "clue",
            "description": "气象站发现雾中含有不明物质",
            "characters": ["气象专家"],
            "importance": 0.8,
            "causes": [
                {"id": "event1", "relation": "DIRECT"}
            ]
        },
        {
            "id": "event4",
            "description": "市长召开紧急会议",
            "characters": ["市长", "政府官员"],
            "importance": 0.6,
            "causes": [
                {"id": "event1", "relation": "DIRECT"}
            ]
        },
        {
            "id": "event5",
            "description": "城市交通陷入混乱",
            "characters": ["市民", "交通警察"],
            "importance": 0.7,
            "causes": [
                {"id": "event1", "relation": "DIRECT"}
            ]
        }
        # 没有解决方案，线索没有后续发展
    ]
    return story


def demo_causality_validation():
    """演示因果链验证"""
    print("===== 因果链验证器示例 =====\n")
    
    # 创建验证器
    validator = CausalityValidator()
    
    # 加载示例故事
    print("1. 分析完整的故事情节")
    print("-" * 30)
    story = create_demo_story()
    
    # 分析因果结构
    result = validator.analyze_causal_structure(story)
    
    # 显示分析结果
    print(f"检测到的问题数量: {len(result['issues'])}")
    print(f"故事完整性评分: {result['completeness']:.2f}")
    print(f"事件数量: {result['num_events']}")
    print(f"主要因果链: {len(result['chains'][result['main_chain_index']])} 个事件")
    
    # 打印事件链
    print("\n事件因果链:")
    for event_id in result['chains'][result['main_chain_index']]:
        event = next(event for event in story if event["id"] == event_id)
        print(f"  - {event['description']}")
    
    print("\n2. 分析存在问题的故事情节")
    print("-" * 30)
    problematic_story = create_problematic_story()
    
    # 分析存在问题的故事
    problem_result = validator.analyze_causal_structure(problematic_story)
    
    # 显示分析结果
    print(f"检测到的问题数量: {len(problem_result['issues'])}")
    print(f"故事完整性评分: {problem_result['completeness']:.2f}")
    
    # 打印检测到的问题
    print("\n检测到的问题:")
    for issue in problem_result['issues']:
        print(f"  - {issue['message']}")
    
    # 打印修复建议
    print("\n修复建议:")
    for issue_type, suggestions in problem_result['suggestions'].items():
        for suggestion in suggestions:
            print(f"  - {suggestion['message']}")
    
    print("\n3. 使用便捷函数进行验证")
    print("-" * 30)
    # 使用便捷函数验证因果关系
    try:
        result = validate_causality(story)
        print("故事因果一致性良好")
    except CausalityBreakError as e:
        print(f"故事存在因果问题: {e}")
        for issue in e.details.get("issues", []):
            print(f"  - {issue['message']}")

def display_causal_network(events):
    """简单展示事件之间的因果网络"""
    print("\n因果网络可视化:")
    print("事件ID\t描述\t\t\t\t\t原因")
    print("-" * 70)
    
    for event in events:
        event_id = event["id"]
        description = event["description"]
        causes = []
        
        if "causes" in event:
            for cause in event["causes"]:
                cause_id = cause["id"]
                relation = cause["relation"]
                cause_event = next((e for e in events if e["id"] == cause_id), None)
                if cause_event:
                    causes.append(f"{cause_id}({relation}): {cause_event['description'][:30]}...")
        
        # 截断描述，确保整齐显示
        short_desc = description[:40] + "..." if len(description) > 40 else description
        causes_str = ", ".join(causes) if causes else "无"
        
        print(f"{event_id}\t{short_desc.ljust(40)}\t{causes_str}")


if __name__ == "__main__":
    demo_causality_validation()
    
    # 额外展示因果网络
    print("\n附加展示：因果网络")
    print("-" * 30)
    display_causal_network(create_demo_story()) 