#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
文化语境验证器示例

演示如何使用文化语境验证器分析和验证场景的文化一致性。
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

from src.logic.cultural_validator import (
    CulturalContextChecker,
    validate_cultural_context,
    CulturalEra,
    CulturalRegion,
    CulturalErrorType
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
    print(f"{Fore.GREEN}  文化准确性: {Fore.RED if not result['is_accurate'] else Fore.GREEN}{result['is_accurate']}{Style.RESET_ALL}")
    
    if result["errors"]:
        print(f"\n{Fore.RED}  检测到的错误:{Style.RESET_ALL}")
        for i, error in enumerate(result["errors"], 1):
            print(f"  {i}. [{error['type']}] {error['description']}")
    
    if result["warnings"]:
        print(f"\n{Fore.YELLOW}  警告:{Style.RESET_ALL}")
        for i, warning in enumerate(result["warnings"], 1):
            print(f"  {i}. [{warning['type']}] {warning['description']}")
    
    if result["suggestions"]:
        print(f"\n{Fore.BLUE}  改进建议:{Style.RESET_ALL}")
        for i, suggestion in enumerate(result["suggestions"], 1):
            print(f"  {i}. {suggestion}")
    
    print(f"\n{Fore.MAGENTA}  适用的规则:{Style.RESET_ALL}")
    for i, rule in enumerate(result["applicable_rules"], 1):
        print(f"  - {rule}")
    
    print(f"\n{Fore.MAGENTA}--------{Style.RESET_ALL}\n")


def demo_ancient_china():
    """演示中国古代场景验证"""
    print_header("中国古代场景验证")
    
    # 创建正确的中国古代场景
    correct_scene = {
        "era": "中国古代",
        "region": "中国",
        "description": "一个古代中国的宫廷场景，皇帝坐在龙椅上接见大臣。",
        "props": ["龙椅", "朝服", "玉玺", "茶具", "书卷"],
        "costumes": ["朝服", "官帽", "布鞋", "长袍"],
        "characters": ["皇帝", "大臣", "侍女", "太监"]
    }
    
    # 创建有错误的中国古代场景
    error_scene = {
        "era": "中国古代",
        "region": "中国",
        "description": "古代宫廷中，皇帝正在用手机与大臣视频通话，讨论国家大事。",
        "props": ["龙椅", "手机", "电脑", "塑料杯", "玉玺"],
        "costumes": ["朝服", "运动鞋", "西装"],
        "characters": ["皇帝", "大臣", "IT顾问"]
    }
    
    # 验证场景
    correct_result = validate_cultural_context(correct_scene)
    error_result = validate_cultural_context(error_scene)
    
    # 打印结果
    print_result("正确的中国古代场景", correct_result)
    print_result("错误的中国古代场景", error_result)


def demo_western_periods():
    """演示西方不同时期场景验证"""
    print_header("西方不同时期场景验证")
    
    # 中世纪场景
    medieval_scene = {
        "era": "中世纪",
        "region": "欧洲",
        "description": "中世纪的欧洲城堡，骑士们正在准备一场比武大会。",
        "props": ["剑", "盾牌", "战马", "长矛", "旗帜"],
        "costumes": ["盔甲", "长袍", "皮靴"],
        "characters": ["骑士", "侍从", "领主", "贵族"]
    }
    
    # 维多利亚时代场景
    victorian_scene = {
        "era": "维多利亚时代",
        "region": "西欧",
        "description": "19世纪末的英国贵族社交晚宴，绅士淑女们正在交谈。",
        "props": ["茶具", "蜡烛", "书籍", "手杖", "手表"],
        "costumes": ["长裙", "燕尾服", "高领衬衫", "礼帽", "手套"],
        "characters": ["男爵", "女伯爵", "管家", "商人"]
    }
    
    # 混合了不同时代元素的场景
    mixed_scene = {
        "era": "中世纪",
        "region": "欧洲",
        "description": "中世纪的欧洲城堡，骑士们正在用智能手机拍摄城堡照片。",
        "props": ["剑", "盾牌", "智能手机", "太阳镜", "可乐"],
        "costumes": ["盔甲", "牛仔裤", "T恤", "运动鞋"],
        "characters": ["骑士", "游客", "导游"]
    }
    
    # 验证场景
    medieval_result = validate_cultural_context(medieval_scene)
    victorian_result = validate_cultural_context(victorian_scene)
    mixed_result = validate_cultural_context(mixed_scene)
    
    # 打印结果
    print_result("中世纪欧洲场景", medieval_result)
    print_result("维多利亚时代场景", victorian_result)
    print_result("混合元素场景", mixed_result)


def demo_cultural_taboos():
    """演示文化禁忌验证"""
    print_header("文化禁忌验证")
    
    # 伊斯兰文化场景 - 正确
    islamic_correct = {
        "region": "伊斯兰中东",
        "description": "在清真寺中，人们正在进行祷告仪式。",
        "props": ["古兰经", "祷告毯", "念珠"],
        "costumes": ["传统长袍", "头巾"],
        "characters": ["伊玛目", "信徒"]
    }
    
    # 伊斯兰文化场景 - 错误
    islamic_error = {
        "region": "伊斯兰中东",
        "description": "在清真寺附近的餐厅，人们正在享用猪肉和酒精饮料。",
        "props": ["古兰经", "酒瓶", "猪肉菜肴"],
        "costumes": ["暴露服装", "比基尼"],
        "characters": ["伊玛目", "游客"]
    }
    
    # 验证场景
    correct_result = validate_cultural_context(islamic_correct)
    error_result = validate_cultural_context(islamic_error)
    
    # 打印结果
    print_result("正确的伊斯兰文化场景", correct_result)
    print_result("错误的伊斯兰文化场景", error_result)


def demo_custom_analysis():
    """演示自定义文化分析"""
    print_header("自定义文化分析")
    
    # 创建包含刻板印象的场景
    stereotype_scene = {
        "description": "东方神秘主义场景，充满了神秘的东方元素和刻板印象。",
        "props": ["烟雾缭绕的熏香", "水晶球", "神秘符号"],
        "costumes": ["神秘长袍", "奇怪的面具"],
        "characters": ["神秘大师", "求助者"]
    }
    
    # 创建文化挪用场景
    appropriation_scene = {
        "description": "西方人穿着不当改造的传统服饰参加派对，将文化元素作为装饰品。",
        "props": ["文化挪用的装饰品", "不尊重的文化模仿物"],
        "costumes": ["不当改造的传统服饰", "带有宗教符号的时尚单品"],
        "characters": ["派对客人", "摄影师"]
    }
    
    # 验证场景
    stereotype_result = validate_cultural_context(stereotype_scene)
    appropriation_result = validate_cultural_context(appropriation_scene)
    
    # 打印结果
    print_result("刻板印象场景", stereotype_result)
    print_result("文化挪用场景", appropriation_result)


def demo_suggestions():
    """演示文化建议生成"""
    print_header("文化建议生成")
    
    # 创建文化检查器
    checker = CulturalContextChecker()
    
    # 不同时代场景
    scenes = {
        "中国古代": {
            "era": "中国古代",
            "region": "中国",
            "description": "中国古代场景",
        },
        "维多利亚时代": {
            "era": "维多利亚时代",
            "region": "西欧",
            "description": "维多利亚时代场景",
        },
        "中世纪": {
            "era": "中世纪",
            "region": "欧洲",
            "description": "中世纪场景",
        }
    }
    
    # 获取并打印每个场景的建议
    for name, scene in scenes.items():
        suggestions = checker.get_cultural_suggestions(scene)
        print(f"{Fore.YELLOW}● {name}场景建议:{Style.RESET_ALL}")
        for i, suggestion in enumerate(suggestions, 1):
            print(f"  {i}. {suggestion}")
        print()


def main():
    """主函数"""
    print("\n文化语境验证器演示程序\n")
    setup_colorama()
    
    # 运行各个演示
    demo_ancient_china()
    demo_western_periods()
    demo_cultural_taboos()
    demo_custom_analysis()
    demo_suggestions()
    
    print("演示完成!")


if __name__ == "__main__":
    main() 