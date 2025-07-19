#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
因果链验证引擎独立演示

直接导入causality_engine.py模块进行演示，展示因果链验证引擎的功能。
"""

import sys
import os
import logging
from pathlib import Path
import importlib.util
from pprint import pprint

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 直接导入causality_engine.py模块
module_path = Path("src/logic/causality_engine.py")
module_name = "causality_engine"

# 创建模块对象
spec = importlib.util.spec_from_file_location(module_name, module_path)
module = importlib.util.module_from_spec(spec)
sys.modules[module_name] = module
spec.loader.exec_module(module)

# 从模块中导入类
CausalityValidator = module.CausalityValidator
CausalityType = module.CausalityType
validate_causality = module.validate_causality
EventNode = module.EventNode

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

def create_temporal_paradox_story():
    """创建有时序悖论的故事事件序列"""
    story = [
        {
            "id": "event1",
            "description": "主角起床准备上班",
            "characters": ["主角"],
            "importance": 0.5
        },
        {
            "id": "event2",
            "description": "主角得知公司破产",
            "characters": ["主角", "同事"],
            "importance": 0.9,
            "causes": [
                {"id": "event3", "relation": "DIRECT"}  # 原因是后面的事件，形成悖论
            ]
        },
        {
            "id": "event3",
            "description": "公司股价暴跌",
            "characters": ["CEO", "股东"],
            "importance": 0.8
        }
    ]
    return story

def demo_causality_validation():
    """演示因果链验证"""
    print("===== 因果链验证引擎演示 =====\n")
    
    # 创建验证器
    validator = CausalityValidator()
    
    # 1. 分析完整的故事
    print("1. 分析完整的故事情节")
    print("-" * 40)
    story = create_demo_story()
    
    # 打印故事内容
    print("故事事件:")
    for i, event in enumerate(story):
        print(f"{i+1}. {event['description']}")
    
    # 分析因果结构
    result = validator.analyze_causal_structure(story)
    
    # 显示分析结果
    print("\n分析结果:")
    print(f"检测到的问题数量: {len(result['issues'])}")
    print(f"故事完整性评分: {result['completeness']:.2f}/1.00")
    print(f"事件总数: {result['num_events']}")
    print(f"问题事件数: {result['num_problems']}")
    print(f"线索事件数: {result['num_clues']}")
    print(f"解决事件数: {result['num_resolutions']}")
    print(f"未解决问题数: {result['num_unresolved']}")
    print(f"悬而未决线索数: {result['num_dangling']}")
    
    # 打印事件链
    print("\n主要因果链:")
    main_chain = result['chains'][result['main_chain_index']]
    for i, event_id in enumerate(main_chain):
        event = next(e for e in story if e["id"] == event_id)
        print(f"  {i+1}. {event['description']}")
    
    # 2. 分析有问题的故事
    print("\n\n2. 分析存在问题的故事情节")
    print("-" * 40)
    problematic_story = create_problematic_story()
    
    # 打印故事内容
    print("故事事件:")
    for i, event in enumerate(problematic_story):
        print(f"{i+1}. {event['description']}")
    
    # 分析存在问题的故事
    problem_result = validator.analyze_causal_structure(problematic_story)
    
    # 显示分析结果
    print("\n分析结果:")
    print(f"检测到的问题数量: {len(problem_result['issues'])}")
    print(f"故事完整性评分: {problem_result['completeness']:.2f}/1.00")
    
    # 打印检测到的问题
    print("\n检测到的问题:")
    for issue in problem_result['issues']:
        print(f"  - {issue['message']}")
    
    # 打印修复建议
    print("\n修复建议:")
    for issue_type, suggestions in problem_result['suggestions'].items():
        for suggestion in suggestions:
            print(f"  - {suggestion['message']}")
    
    # 3. 分析有时序悖论的故事
    print("\n\n3. 分析存在时序悖论的故事情节")
    print("-" * 40)
    paradox_story = create_temporal_paradox_story()
    
    # 打印故事内容
    print("故事事件:")
    for i, event in enumerate(paradox_story):
        print(f"{i+1}. {event['description']}")
    
    # 分析存在时序悖论的故事
    paradox_result = validator.analyze_causal_structure(paradox_story)
    
    # 显示分析结果
    print("\n分析结果:")
    paradox_issues = [issue for issue in paradox_result['issues'] if issue['type'] == 'temporal_paradox']
    print(f"检测到的时序悖论: {len(paradox_issues)}")
    
    # 打印检测到的问题
    print("\n检测到的问题:")
    for issue in paradox_issues:
        print(f"  - {issue['message']}")
    
    # 打印修复建议
    print("\n修复建议:")
    if 'temporal_paradox' in paradox_result['suggestions']:
        for suggestion in paradox_result['suggestions']['temporal_paradox']:
            print(f"  - {suggestion['message']}")

def display_causal_network(events):
    """简单展示事件之间的因果网络"""
    print("\n因果网络可视化:")
    print("事件ID\t描述\t\t\t\t\t\t原因")
    print("-" * 80)
    
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
        short_desc = description[:45] + "..." if len(description) > 45 else description.ljust(45)
        causes_str = ", ".join(causes) if causes else "无"
        
        print(f"{event_id}\t{short_desc}\t{causes_str}")


if __name__ == "__main__":
    # 运行主演示
    demo_causality_validation()
    
    # 额外展示因果网络
    print("\n\n附加展示：因果网络")
    print("-" * 40)
    display_causal_network(create_demo_story()) 