#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
对话逻辑校验器示例

演示如何使用对话逻辑校验器检测视频对话中的逻辑问题。
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

from src.logic.dialogue_validator import DialogueValidator, validate_dialogue_consistency
from src.utils.exceptions import DialogueInconsistencyError

def load_demo_scenes():
    """加载演示用的场景数据"""
    # 历史剧场景 - 1700年的欧洲贵族对话
    historical_scene = {
        "id": "historical_scene",
        "year": 1700,
        "dialogues": [
            {
                "character": {
                    "name": "伯爵",
                    "education_level": "大学",
                    "occupation": "贵族"
                },
                "text": "这场战争已经持续太久，我国的财政难以为继。"
            },
            {
                "character": {
                    "name": "公爵",
                    "education_level": "大学",
                    "occupation": "军官"
                },
                "text": "是的，但国王不会轻易放弃对新大陆的野心。"
            }
        ]
    }
    
    # 现代场景 - 2020年的技术讨论
    modern_scene = {
        "id": "modern_scene",
        "year": 2020,
        "dialogues": [
            {
                "character": {
                    "name": "技术总监",
                    "education_level": "研究生",
                    "occupation": "工程师"
                },
                "text": "我们需要优化算法，提高人工智能模型的性能。"
            },
            {
                "character": {
                    "name": "产品经理",
                    "education_level": "大学",
                    "occupation": "管理人员"
                },
                "text": "用户反馈显示，应用的响应速度还有提升空间。"
            }
        ]
    }
    
    # 问题场景1 - 历史错误
    error_scene1 = {
        "id": "error_scene1",
        "year": 1800,
        "dialogues": [
            {
                "character": {
                    "name": "商人",
                    "education_level": "高中",
                    "occupation": "贸易"
                },
                "text": "我刚用手机联系了美洲的合作伙伴，他们的货物已经在路上了。"
            }
        ]
    }
    
    # 问题场景2 - 角色背景不匹配
    error_scene2 = {
        "id": "error_scene2",
        "year": 2020,
        "dialogues": [
            {
                "character": {
                    "name": "小学生",
                    "education_level": "小学",
                    "occupation": "学生"
                },
                "text": "爱因斯坦的相对论中，E=mc²表明能量与质量的转换关系，这解释了核裂变的原理。"
            }
        ]
    }
    
    # 问题场景3 - 情感突变
    error_scene3 = {
        "id": "error_scene3",
        "year": 2020,
        "dialogues": [
            {
                "character": {
                    "name": "王小明",
                    "education_level": "大学",
                    "occupation": "销售"
                },
                "text": "今天真是太棒了！我成功签下了年度最大的订单，老板非常满意！"
            },
            {
                "character": {
                    "name": "王小明",
                    "education_level": "大学",
                    "occupation": "销售"
                },
                "text": "我恨这份工作，恨这个公司，我要立刻辞职！"
            }
        ]
    }
    
    return [historical_scene, modern_scene, error_scene1, error_scene2, error_scene3]

def validate_with_exception(validator, scene):
    """使用异常处理方式验证场景"""
    try:
        issue = validator.validate_dialogue(scene)
        if issue:
            explanation = validator.explain_validation_result(issue)
            raise DialogueInconsistencyError(
                msg=issue,
                details=explanation
            )
        return True
    except DialogueInconsistencyError as e:
        print(f"验证失败: {e}")
        print(f"详细信息: {e.details}")
        return False

def demo_dialogue_validation():
    """演示对话逻辑校验器的功能"""
    print("===== 对话逻辑校验器示例 =====\n")
    
    # 创建验证器
    validator = DialogueValidator()
    
    # 加载演示场景
    scenes = load_demo_scenes()
    
    # 遍历场景进行验证
    for i, scene in enumerate(scenes):
        print(f"\n场景 {i+1}: {scene['id']} (年份: {scene['year']})")
        print("-" * 50)
        
        # 打印场景对话
        print("对话内容:")
        for j, dialogue in enumerate(scene["dialogues"]):
            character = dialogue["character"]["name"]
            occupation = dialogue["character"].get("occupation", "未知")
            education = dialogue["character"].get("education_level", "未知")
            text = dialogue["text"]
            print(f"  [{j+1}] {character} ({occupation}, {education}教育): \"{text}\"")
        
        # 方法1: 使用便捷函数验证
        print("\n验证结果 (便捷函数):")
        result = validate_dialogue_consistency(scene)
        if result["valid"]:
            print("  ✓ 对话逻辑验证通过")
        else:
            print(f"  ✗ 发现问题: {result['issue']}")
            print(f"  → 修复建议: {result['suggestion']}")
        
        # 方法2: 使用异常处理验证
        print("\n验证结果 (异常处理):")
        if validate_with_exception(validator, scene):
            print("  ✓ 对话逻辑验证通过")
        
        print("-" * 50)
    
    # 额外演示：扩展历史知识库
    print("\n额外演示：扩展历史知识库")
    validator.historical_facts["法国大革命"] = {"start_year": 1789, "end_year": 1799}
    
    custom_scene = {
        "id": "french_revolution",
        "year": 1780,
        "dialogues": [
            {
                "character": {
                    "name": "贵族",
                    "education_level": "大学"
                },
                "text": "法国大革命已经改变了欧洲的政治格局。"
            }
        ]
    }
    
    result = validate_dialogue_consistency(custom_scene)
    print(f"自定义历史知识验证结果: {'通过' if result['valid'] else '失败'}")
    if not result["valid"]:
        print(f"问题: {result['issue']}")

def demo_knowledge_graph():
    """演示知识图谱构建功能"""
    print("\n===== 知识图谱构建示例 =====\n")
    
    validator = DialogueValidator()
    
    # 创建一系列相互关联的对话
    connected_dialogues = [
        {
            "id": "scene1",
            "dialogues": [
                {
                    "character": {"name": "老师"},
                    "text": "小明今天表现很好，在北京的比赛中获得了第一名。"
                }
            ]
        },
        {
            "id": "scene2",
            "dialogues": [
                {
                    "character": {"name": "小明"},
                    "text": "谢谢老师的鼓励，我在上海的训练成果得到了体现。"
                }
            ]
        },
        {
            "id": "scene3",
            "dialogues": [
                {
                    "character": {"name": "小红"},
                    "text": "小明是我的好朋友，他在数学方面很有天赋。"
                }
            ]
        }
    ]
    
    # 构建知识图谱
    for scene in connected_dialogues:
        validator.expand_knowledge_graph(scene)
    
    # 显示知识图谱内容
    print("知识图谱实体:")
    for entity_name, entity_data in validator.knowledge_graph.entities.items():
        print(f"  - {entity_name} ({entity_data['type']})")
    
    print("\n知识图谱关系:")
    for source, relation, target, _ in validator.knowledge_graph.relations:
        print(f"  - {source} --[{relation}]--> {target}")
    
    print("\n推断出的地点和人物:")
    places = [name for name, data in validator.knowledge_graph.entities.items() 
              if data["type"] == "location"]
    persons = [name for name, data in validator.knowledge_graph.entities.items() 
               if data["type"] == "person" or data["type"] == "character"]
    
    print(f"  地点: {', '.join(places)}")
    print(f"  人物: {', '.join(persons)}")

if __name__ == "__main__":
    # 运行对话验证演示
    demo_dialogue_validation()
    
    # 运行知识图谱演示
    demo_knowledge_graph() 