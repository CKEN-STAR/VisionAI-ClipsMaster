#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
冲突解决校验器示例

演示如何使用冲突解决校验器分析视频中的冲突解决方案。
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

from src.logic.conflict_resolution import (
    ConflictResolver, 
    validate_conflict_resolution, 
    ConflictType, 
    ResolutionMethod, 
    ConflictResolutionError
)

def load_demo_conflicts():
    """加载示例冲突数据"""
    # 场景1：适当的冲突解决方案
    appropriate_resolutions = [
        {
            "id": "conflict1",
            "type": "verbal",
            "intensity": "medium",
            "description": "张三和李四关于项目方向的争论",
            "parties": [
                {"id": "char1", "name": "张三", "strength": 7, "position": "使用传统方法"},
                {"id": "char2", "name": "李四", "strength": 6, "position": "使用创新方法"}
            ],
            "resolution": {
                "type": "negotiation",
                "outcome": "双方达成折中方案，融合两种方法"
            },
            "resolver": {
                "id": "char1",
                "name": "张三",
                "skills": ["negotiation", "diplomacy", "persuasion"]
            }
        },
        {
            "id": "conflict2",
            "type": "physical",
            "intensity": "high",
            "description": "王五和赵六的武力对抗",
            "parties": [
                {"id": "char3", "name": "王五", "strength": 9, "position": "保卫领地"},
                {"id": "char4", "name": "赵六", "strength": 7, "position": "入侵领地"}
            ],
            "resolution": {
                "type": "force",
                "outcome": "王五成功防御，赵六撤退"
            },
            "resolver": {
                "id": "char3",
                "name": "王五",
                "skills": ["combat", "martial arts", "strength", "defense"]
            }
        }
    ]
    
    # 场景2：问题冲突解决方案
    problematic_resolutions = [
        {
            "id": "problem1",
            "type": "ideological",
            "intensity": "high",
            "description": "孙七和周八关于信仰的争论",
            "parties": [
                {"id": "char5", "name": "孙七", "strength": 6, "position": "科学主义"},
                {"id": "char6", "name": "周八", "strength": 6, "position": "传统信仰"}
            ],
            "resolution": {
                "type": "force",  # 不适合用武力解决意识形态冲突
                "outcome": "孙七强制周八接受其观点"
            },
            "resolver": {
                "id": "char5",
                "name": "孙七",
                "skills": ["science", "logic", "strength"]
            }
        },
        {
            "id": "problem2",
            "type": "physical",
            "intensity": "medium",
            "description": "吴九和郑十的打斗",
            "parties": [
                {"id": "char7", "name": "吴九", "strength": 4, "position": "防守"},
                {"id": "char8", "name": "郑十", "strength": 8, "position": "进攻"}
            ],
            "resolution": {
                "type": "force",
                "outcome": "吴九战胜郑十"  # 力量对比不合理
            },
            "resolver": {
                "id": "char7",
                "name": "吴九",
                "skills": ["martial arts", "agility"]
            }
        },
        {
            "id": "problem3",
            "type": "relational",
            "intensity": "medium",
            "description": "冯十一和陈十二的关系冲突",
            "parties": [
                {"id": "char9", "name": "冯十一", "strength": 5, "position": "分手"},
                {"id": "char10", "name": "陈十二", "strength": 5, "position": "继续关系"}
            ],
            "resolution": {
                "type": "arbitration",  # 缺少仲裁者
                "outcome": "双方接受第三方仲裁结果"
            }
        }
    ]
    
    return {
        "appropriate": appropriate_resolutions,
        "problematic": problematic_resolutions
    }

def demo_conflict_analysis():
    """演示冲突解决方案分析功能"""
    print("===== 冲突解决方案分析演示 =====\n")
    
    conflicts = load_demo_conflicts()
    resolver = ConflictResolver()
    
    # 分析适当的解决方案
    print("1. 分析合理的冲突解决方案")
    error_message = resolver.verify_resolutions(conflicts["appropriate"])
    if error_message:
        print(f"发现问题: {error_message}")
    else:
        print("  ✓ 所有解决方案合理，未检测到问题")
    
    # 分析问题解决方案
    print("\n2. 分析存在问题的冲突解决方案")
    error_message = resolver.verify_resolutions(conflicts["problematic"])
    if error_message:
        print(f"发现问题: {error_message}")
        
        issues = resolver.get_all_issues()
        print(f"\n共检测到 {len(issues)} 个问题:")
        for i, issue in enumerate(issues, 1):
            print(f"  问题 {i}: {issue['message']}")
            print(f"  冲突ID: {issue['conflict_id']}")
            print(f"  问题类型: {issue['type']}")
            if issue['details']:
                print(f"  详细信息: {json.dumps(issue['details'], ensure_ascii=False, indent=2)}")
            print()
    else:
        print("  ✓ 未检测到问题")

def demo_suggestions():
    """演示冲突解决方案建议功能"""
    print("\n===== 冲突解决方案建议演示 =====\n")
    
    conflicts = load_demo_conflicts()
    resolver = ConflictResolver()
    
    # 生成改进建议
    suggestions = resolver.generate_suggestions(conflicts["problematic"])
    
    print(f"共生成 {len(suggestions)} 个冲突的改进建议:\n")
    
    for conflict_id, conflict_suggestions in suggestions.items():
        print(f"冲突 {conflict_id} 的建议:")
        for i, suggestion in enumerate(conflict_suggestions, 1):
            print(f"  建议 {i}:")
            print(f"  问题: {suggestion['problem']}")
            print(f"  建议: {suggestion['suggestion']}")
        print()

def demo_convenience_function():
    """演示便捷函数使用方式"""
    print("\n===== 便捷函数使用演示 =====\n")
    
    conflicts = load_demo_conflicts()
    
    # 使用便捷函数验证冲突解决方案
    try:
        print("1. 验证合理的冲突解决方案")
        result = validate_conflict_resolution(conflicts["appropriate"])
        print(f"  验证结果: {'通过' if result['valid'] else '未通过'}")
        print(f"  检测到问题数量: {len(result['issues'])}")
        
        print("\n2. 验证存在问题的冲突解决方案")
        result = validate_conflict_resolution(conflicts["problematic"])
        print(f"  验证结果: {'通过' if result['valid'] else '未通过'}")
        print(f"  检测到问题数量: {len(result['issues'])}")
        print(f"  生成建议数量: {len(result['suggestions'])}")
        
        # 测试异常抛出
        print("\n3. 测试异常抛出功能")
        try:
            validate_conflict_resolution(conflicts["problematic"], raise_exception=True)
            print("  未抛出预期异常")
        except ConflictResolutionError as e:
            print(f"  ✓ 成功抛出异常: {e}")
    
    except Exception as e:
        print(f"验证过程中发生错误: {e}")

if __name__ == "__main__":
    print("冲突解决校验器演示程序\n")
    
    # 创建输出目录
    os.makedirs("./output", exist_ok=True)
    
    # 运行演示
    demo_conflict_analysis()
    demo_suggestions()
    demo_convenience_function()
    
    print("\n演示完成!") 