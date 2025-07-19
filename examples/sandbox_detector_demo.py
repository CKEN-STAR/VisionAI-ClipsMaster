#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
逻辑漏洞沙盒检测器演示

演示如何使用逻辑漏洞沙盒检测器分析和验证场景的逻辑一致性。
"""

import sys
import os
from pathlib import Path
import json
import colorama
from colorama import Fore, Style, init

# 添加项目根目录到Python路径
current_dir = Path(__file__).resolve().parent
root_dir = current_dir.parent
if str(root_dir) not in sys.path:
    sys.path.append(str(root_dir))

from src.logic.sandbox_detector import (
    LogicSandbox,
    validate_logic_sandbox,
    LogicDefectType,
    LogicDefect
)


def setup_colorama():
    """初始化彩色输出"""
    init()


def print_header(text):
    """打印标题"""
    print(f"\n{Fore.CYAN}{Style.BRIGHT}" + "=" * 80)
    print(f" {text}")
    print("=" * 80 + f"{Style.RESET_ALL}\n")


def print_result(title, result):
    """打印验证结果"""
    print(f"{Fore.YELLOW}● {title}:{Style.RESET_ALL}")
    print(f"{Fore.GREEN}  逻辑评分: {Fore.RED if result['score'] < 0.6 else Fore.GREEN}{result['score']:.2f}/1.0{Style.RESET_ALL}")
    
    defects = result["defects"]
    if defects:
        print(f"\n{Fore.RED}  检测到的逻辑缺陷:{Style.RESET_ALL}")
        for i, defect in enumerate(defects, 1):
            defect_type = defect.get("defect_type")
            if isinstance(defect_type, LogicDefectType):
                defect_type = defect_type.name
                
            severity = defect.get("severity", "").upper()
            severity_color = Fore.YELLOW
            if severity == "HIGH":
                severity_color = Fore.RED
            elif severity == "CRITICAL":
                severity_color = Fore.MAGENTA
            elif severity == "LOW":
                severity_color = Fore.GREEN
            
            print(f"  {i}. [{severity_color}{severity}{Style.RESET_ALL}] [{defect_type}] {defect.get('description', '')}")
            
            if "suggested_fix" in defect:
                print(f"     {Fore.BLUE}建议修复: {defect['suggested_fix']}{Style.RESET_ALL}")
    else:
        print(f"\n{Fore.GREEN}  未检测到逻辑缺陷{Style.RESET_ALL}")
    
    if "stress_test" in result:
        print(f"\n{Fore.MAGENTA}  压力测试结果:{Style.RESET_ALL}")
        print(f"  - 检出率: {result['stress_test']['detection_rate']:.2%}")
        print(f"  - {result['stress_test']['description']}")
    
    print(f"\n{Fore.MAGENTA}--------{Style.RESET_ALL}\n")


def create_sample_script():
    """创建示例脚本"""
    # 正常逻辑脚本
    normal_script = {
        "scenes": [
            {
                "id": "scene1",
                "timestamp": 1000,
                "characters": [
                    {"name": "主角", "traits": ["勇敢", "忠诚"]},
                    {"name": "配角", "traits": ["聪明", "谨慎"]}
                ],
                "props": [
                    {"name": "宝剑", "state": "visible"},
                    {"name": "地图", "state": "visible"}
                ],
                "dialogues": [
                    {"character": "主角", "text": "我们必须找到宝藏！", "emotion": "excited"},
                    {"character": "配角", "text": "我们得小心行事。", "emotion": "cautious"}
                ],
                "emotion": "positive"
            },
            {
                "id": "scene2",
                "timestamp": 2000,
                "characters": [
                    {"name": "主角", "traits": ["勇敢", "忠诚"]},
                    {"name": "配角", "traits": ["聪明", "谨慎"]}
                ],
                "props": [
                    {"name": "宝剑", "state": "wielded"},
                    {"name": "地图", "state": "used"}
                ],
                "dialogues": [
                    {"character": "主角", "text": "看，地图上标记的位置就在前方！", "emotion": "excited"},
                    {"character": "配角", "text": "有些不对劲，我们可能被跟踪了。", "emotion": "worried"}
                ],
                "emotion": "tense",
                "is_cause": True,
                "cause_for": "scene3"
            },
            {
                "id": "scene3",
                "timestamp": 3000,
                "characters": [
                    {"name": "主角", "traits": ["勇敢", "忠诚"]},
                    {"name": "敌人", "traits": ["凶狠", "贪婪"]}
                ],
                "props": [
                    {"name": "宝剑", "state": "wielded"},
                    {"name": "宝箱", "state": "visible"}
                ],
                "dialogues": [
                    {"character": "敌人", "text": "这宝藏是我的了！", "emotion": "aggressive"},
                    {"character": "主角", "text": "我不会让你得逞的！", "emotion": "determined"}
                ],
                "emotion": "negative"
            }
        ]
    }
    
    # 带有逻辑缺陷的脚本
    defective_script = {
        "scenes": [
            {
                "id": "scene1",
                "timestamp": 1000,
                "characters": [
                    {"name": "主角", "traits": ["勇敢", "忠诚"]},
                    {"name": "配角", "traits": ["聪明", "谨慎"]}
                ],
                "props": [
                    {"name": "宝剑", "state": "visible"},
                    {"name": "地图", "state": "visible"}
                ],
                "dialogues": [
                    {"character": "主角", "text": "我们必须找到宝藏！", "emotion": "excited"},
                    {"character": "配角", "text": "我们得小心行事。", "emotion": "cautious"}
                ],
                "emotion": "positive"
            },
            {
                "id": "scene3",  # 先展示结果
                "timestamp": 900,  # 时间倒流
                "characters": [
                    {"name": "主角", "traits": ["勇敢", "忠诚"]},
                    {"name": "敌人", "traits": ["凶狠", "贪婪"]}
                ],
                "props": [
                    {"name": "宝剑", "state": "wielded"},
                    {"name": "宝箱", "state": "visible"}
                ],
                "dialogues": [
                    {"character": "敌人", "text": "这宝藏是我的了！", "emotion": "aggressive"},
                    {"character": "主角", "text": "我浪费我嘞时间！", "emotion": "happy"}  # 对话与角色设定不符
                ],
                "emotion": "negative"
            },
            {
                "id": "scene2",  # 后展示原因
                "timestamp": 2000,
                "characters": [
                    {"name": "主角", "traits": ["勇敢", "忠诚"]},
                    {"name": "配角", "traits": ["聪明", "谨慎"]}
                ],
                "props": [
                    {"name": "魔法杖", "state": "visible"},  # 道具突然出现
                    {"name": "地图", "state": "used"}
                ],
                "dialogues": [
                    {"character": "主角", "text": "看，地图上标记的位置就在前方！", "emotion": "excited"},
                    {"character": "配角", "text": "有些不对劲，我们可能被跟踪了。", "emotion": "worried"}
                ],
                "emotion": "tense",
                "is_cause": True,
                "cause_for": "scene3"
            }
        ]
    }
    
    # 情感翻转脚本
    emotion_flip_script = {
        "scenes": [
            {
                "id": "scene1",
                "timestamp": 1000,
                "characters": [
                    {"name": "主角", "emotion": "happy"}
                ],
                "dialogues": [
                    {"character": "主角", "text": "今天真是个好日子！", "emotion": "happy"}
                ],
                "emotion": "positive"
            },
            {
                "id": "scene2",
                "timestamp": 1100,  # 紧接着
                "characters": [
                    {"name": "主角", "emotion": "devastated"}
                ],
                "dialogues": [
                    {"character": "主角", "text": "这是我人生中最糟糕的一天！", "emotion": "devastated"}
                ],
                "emotion": "negative"
            }
        ]
    }
    
    return {
        "normal": normal_script,
        "defective": defective_script,
        "emotion_flip": emotion_flip_script
    }


def demo_normal_script():
    """演示正常脚本验证"""
    print_header("正常逻辑脚本验证")
    
    # 获取样本脚本
    scripts = create_sample_script()
    normal_script = scripts["normal"]
    
    # 验证脚本
    result = validate_logic_sandbox(normal_script)
    
    # 打印结果
    print_result("正常逻辑脚本", result)


def demo_defective_script():
    """演示缺陷脚本验证"""
    print_header("逻辑缺陷脚本验证")
    
    # 获取样本脚本
    scripts = create_sample_script()
    defective_script = scripts["defective"]
    
    # 验证脚本
    result = validate_logic_sandbox(defective_script)
    
    # 打印结果
    print_result("逻辑缺陷脚本", result)


def demo_emotion_flip_script():
    """演示情感翻转脚本验证"""
    print_header("情感翻转脚本验证")
    
    # 获取样本脚本
    scripts = create_sample_script()
    emotion_flip_script = scripts["emotion_flip"]
    
    # 验证脚本
    result = validate_logic_sandbox(emotion_flip_script)
    
    # 打印结果
    print_result("情感翻转脚本", result)


def demo_stress_test():
    """演示压力测试"""
    print_header("压力测试演示")
    
    # 获取样本脚本
    scripts = create_sample_script()
    normal_script = scripts["normal"]
    
    # 运行带压力测试的验证
    result = validate_logic_sandbox(normal_script, stress_test=True)
    
    # 打印结果
    print_result("压力测试结果", result)


def demo_inject_defects():
    """演示缺陷注入"""
    print_header("缺陷注入演示")
    
    # 获取样本脚本
    scripts = create_sample_script()
    normal_script = scripts["normal"]
    
    # 创建沙盒实例
    sandbox = LogicSandbox()
    
    # 注入时间跳跃缺陷
    time_jump_script = sandbox.inject_defect(
        normal_script, 
        {"type": "TIME_JUMP", "value": -500}
    )
    
    # 验证注入后的脚本
    result = validate_logic_sandbox(time_jump_script)
    
    # 打印结果
    print_result("注入时间跳跃缺陷后的脚本", result)
    
    # 注入道具传送缺陷
    prop_teleport_script = sandbox.inject_defect(
        normal_script, 
        {"type": "PROP_TELEPORT", "item": "宝剑"}
    )
    
    # 验证注入后的脚本
    result = validate_logic_sandbox(prop_teleport_script)
    
    # 打印结果
    print_result("注入道具传送缺陷后的脚本", result)


def main():
    """主函数"""
    print("\n逻辑漏洞沙盒检测器演示程序\n")
    setup_colorama()
    
    # 运行各个演示
    demo_normal_script()
    demo_defective_script()
    demo_emotion_flip_script()
    demo_stress_test()
    demo_inject_defects()
    
    print("演示完成!")


if __name__ == "__main__":
    main() 