#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
时空连续性检验演示脚本
展示如何检查混剪片段之间的时空连贯性
"""

import sys
import os
import json
import logging
from typing import Dict, List, Any
from datetime import datetime
import pprint

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(project_root)

# 导入相关模块
from src.core.spatial_temporal_checker import (
    SceneConsistencyValidator, 
    validate_scenes, 
    enhance_scene_data
)
from src.utils.log_handler import get_logger

# 配置日志
logger = get_logger("continuity_checker_demo")

def load_sample_scenes(json_path: str = None) -> List[Dict[str, Any]]:
    """
    加载样例场景数据
    
    参数:
        json_path: 场景JSON文件路径
        
    返回:
        场景列表
    """
    if json_path and os.path.exists(json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载场景文件失败: {e}")
    
    # 使用内置样例
    logger.info("使用内置样例场景")
    return [
        # 示例1：正常的连续场景
        {
            "text": "小明在学校教室里专心听讲。",
            "time": {"start": 0, "end": 5},
            "location": "教室",
            "characters": ["小明", "老师"],
            "props": ["书本", "笔记本"],
            "time_of_day": "上午"
        },
        {
            "text": "下课铃响了，小明收拾书包。",
            "time": {"start": 5, "end": 8},
            "location": "教室",
            "characters": ["小明"],
            "props": ["书本", "笔记本", "书包"],
            "time_of_day": "上午"
        },
        # 示例2：地点突变问题
        {
            "text": "小明正在公园里踢足球。",
            "time": {"start": 8, "end": 12},
            "location": "公园",
            "characters": ["小明", "小红"],
            "props": ["足球"],
            "time_of_day": "下午"
        },
        # 示例3：时间段突变问题
        {
            "text": "晚上，小明在家里做作业。",
            "time": {"start": 12, "end": 18},
            "location": "家",
            "characters": ["小明", "妈妈"],
            "props": ["书本", "笔记本", "手机"],
            "time_of_day": "晚上"
        },
        # 示例4：角色连续性问题
        {
            "text": "小明和爸爸一起吃晚饭，讨论今天的学校生活。",
            "time": {"start": 18, "end": 25},
            "location": "家",
            "characters": ["小明", "爸爸"],
            "props": ["餐具", "饭菜"],
            "time_of_day": "晚上"
        },
        # 示例5：道具连续性问题
        {
            "text": "小明走进卧室，放下书包准备休息。",
            "time": {"start": 25, "end": 30},
            "location": "卧室",
            "characters": ["小明"],
            "props": ["书包"],
            "time_of_day": "晚上"
        },
        {
            "text": "小明躺在床上玩手机，突然发现手机不见了。",
            "time": {"start": 30, "end": 35},
            "location": "卧室",
            "characters": ["小明"],
            "props": [],
            "time_of_day": "晚上"
        }
    ]

def create_problematic_scenes() -> List[Dict[str, Any]]:
    """
    创建包含各种连续性问题的场景序列
    
    返回:
        有问题的场景列表
    """
    return [
        # 基础场景
        {
            "text": "小红坐在咖啡厅里，正在喝咖啡看书。",
            "time": {"start": 0, "end": 4},
            "original_time": {"start": 1000, "end": 1004},
            "location": "咖啡厅",
            "characters": ["小红"],
            "props": ["书", "咖啡", "眼镜"],
            "time_of_day": "上午"
        },
        # 时间倒退问题
        {
            "text": "小红走进咖啡厅，点了一杯拿铁。",
            "time": {"start": 4, "end": 8},
            "original_time": {"start": 990, "end": 994},
            "location": "咖啡厅",
            "characters": ["小红", "服务员"],
            "props": ["钱包"],
            "time_of_day": "上午"
        },
        # 地点瞬间变化问题
        {
            "text": "小红走在公园的小路上，欣赏着春天的景色。",
            "time": {"start": 8, "end": 13},
            "original_time": {"start": 1020, "end": 1025},
            "location": "公园",
            "characters": ["小红"],
            "props": ["书", "眼镜"],
            "time_of_day": "上午"
        },
        # 道具连续性问题
        {
            "text": "小红坐在长椅上继续看书，忽然一阵风吹来。",
            "time": {"start": 13, "end": 18},
            "original_time": {"start": 1025, "end": 1030},
            "location": "公园",
            "characters": ["小红"],
            "props": ["书"],  # 眼镜消失了
            "time_of_day": "上午"
        },
        # 时间跳跃过大问题
        {
            "text": "小红走进教室，准备上课。",
            "time": {"start": 18, "end": 22},
            "original_time": {"start": 5000, "end": 5004},  # 时间跳跃过大
            "location": "教室",
            "characters": ["小红", "老师", "同学们"],
            "props": ["书包", "书"],
            "time_of_day": "上午"
        },
        # 时间段不合理变化
        {
            "text": "小红在灯光下认真做着习题。",
            "time": {"start": 22, "end": 26},
            "original_time": {"start": 5010, "end": 5014},
            "location": "教室",
            "characters": ["小红"],
            "props": ["习题", "笔"],
            "time_of_day": "晚上"  # 时间段突然从上午变成晚上
        },
        # 角色连续性问题
        {
            "text": "老师走到小红身边，表扬她的作业做得很好。",
            "time": {"start": 26, "end": 30},
            "original_time": {"start": 5020, "end": 5024},
            "location": "教室",
            "characters": ["小红", "老师", "小明"],  # 小明突然出现
            "props": ["习题", "笔", "作业本"],
            "time_of_day": "晚上"
        }
    ]

def demonstrate_basic_validation():
    """演示基本的场景连续性检查"""
    print("\n===== 基本场景连续性检查 =====")
    
    # 加载样例场景
    scenes = load_sample_scenes()
    
    # 创建验证器
    validator = SceneConsistencyValidator()
    
    # 检查相邻场景对
    for i in range(1, len(scenes)):
        prev_scene = scenes[i-1]
        curr_scene = scenes[i]
        
        print(f"\n检查场景对 {i-1}-{i}:")
        print(f"前一场景: {prev_scene['text']}")
        print(f"当前场景: {curr_scene['text']}")
        
        # 验证连续性
        errors = validator.validate(prev_scene, curr_scene)
        
        if errors:
            print("发现连续性问题:")
            for error in errors:
                print(f"  - {error}")
        else:
            print("未发现连续性问题")

def demonstrate_batch_validation():
    """演示批量场景连续性检查"""
    print("\n===== 批量场景连续性检查 =====")
    
    # 创建问题场景集
    scenes = create_problematic_scenes()
    
    # 验证整个场景序列
    results = validate_scenes(scenes)
    
    # 打印结果摘要
    print(f"总场景数: {results['total_scenes']}")
    print(f"检测到的连续性问题: {results['total_errors']}")
    
    # 打印各类错误统计
    print("\n问题分类统计:")
    for category, count in results['error_counts'].items():
        if count > 0:
            print(f"  {category}: {count}个问题")
    
    # 打印详细问题
    if results['error_details']:
        print("\n详细问题列表:")
        for i, detail in enumerate(results['error_details']):
            scene_idx = detail['scene_pair']
            print(f"\n问题 {i+1}:")
            print(f"场景对 {scene_idx[0]}-{scene_idx[1]}:")
            print(f"  前一场景: {detail['prev_scene_text']}")
            print(f"  当前场景: {detail['curr_scene_text']}")
            print("  连续性问题:")
            for error in detail['errors']:
                print(f"    - {error}")

def demonstrate_metadata_enhancement():
    """演示场景元数据增强"""
    print("\n===== 场景元数据增强 =====")
    
    # 创建缺少元数据的场景
    incomplete_scenes = [
        {
            "text": "小明在教室里听讲。",
            "time": {"start": 0, "end": 5}
            # 缺少 location, characters, time_of_day
        },
        {
            "text": "放学后，小明和小红一起在操场上踢足球。",
            "time": {"start": 5, "end": 10}
            # 缺少 location, characters, time_of_day
        },
        {
            "text": "晚上，小明回到家里，拿出作业本开始写作业。",
            "time": {"start": 10, "end": 15}
            # 缺少 location, characters, time_of_day, props
        }
    ]
    
    # 增强场景元数据
    enhanced_scenes = enhance_scene_data(incomplete_scenes)
    
    # 打印增强结果
    print("增强前后对比:")
    for i, (before, after) in enumerate(zip(incomplete_scenes, enhanced_scenes)):
        print(f"\n场景 {i}:")
        print("增强前:")
        pprint.pprint(before)
        print("\n增强后:")
        pprint.pprint(after)
        
        # 显示新增的元数据
        new_keys = set(after.keys()) - set(before.keys())
        if new_keys:
            print("\n新增元数据:")
            for key in new_keys:
                print(f"  {key}: {after[key]}")

def suggest_fixes(results: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    为检测到的连续性问题提供修复建议
    
    参数:
        results: validate_scenes的结果
        
    返回:
        修复建议列表
    """
    suggestions = []
    
    for detail in results['error_details']:
        scene_pair = detail['scene_pair']
        errors = detail['errors']
        
        suggestion = {
            "scene_pair": scene_pair,
            "problems": [],
            "fixes": []
        }
        
        for error in errors:
            problem = {"description": error}
            
            # 根据错误类型生成修复建议
            if "时间倒退" in error:
                problem["type"] = "time_reversal"
                problem["fix"] = "调整场景顺序或修改时间值，确保时间从早到晚顺序排列"
                
            elif "时间跳跃过大" in error:
                problem["type"] = "time_jump"
                problem["fix"] = "添加过渡场景，或在台词中加入时间流逝的暗示，如'几小时后'、'第二天'"
                
            elif "地点变化但时间间隔过短" in error:
                problem["type"] = "location_jump"
                problem["fix"] = "增加场景之间的时间间隔，或添加移动场景，如'小明坐车前往学校'"
                
            elif "角色连续性" in error and "突然消失" in error:
                problem["type"] = "character_disappearance"
                problem["fix"] = "添加角色离开的描述，或确保场景中提及角色去向"
                
            elif "角色连续性" in error and "突然出现" in error:
                problem["type"] = "character_appearance"
                problem["fix"] = "添加角色进入的描述，或在前一场景中预先提及该角色即将到来"
                
            elif "道具连续性" in error:
                problem["type"] = "prop_consistency"
                problem["fix"] = "确保关键道具在场景间保持一致，或添加道具交接的描述"
                
            elif "时间段连续性" in error and "时间倒退" in error:
                problem["type"] = "time_of_day_reversal"
                problem["fix"] = "添加日期变化的说明，如'第二天早上'，或调整场景顺序"
                
            elif "时间段连续性" in error and "跳跃过大" in error:
                problem["type"] = "time_of_day_jump"
                problem["fix"] = "添加时间流逝的过渡，如'几小时后'、'到了晚上'"
                
            else:
                problem["type"] = "other"
                problem["fix"] = "检查场景内容，确保时空逻辑连贯性"
            
            suggestion["problems"].append(problem)
            suggestion["fixes"].append(problem["fix"])
        
        suggestions.append(suggestion)
    
    return suggestions

def main():
    """主函数"""
    logging.basicConfig(level=logging.INFO)
    print("===== 时空连续性检验演示 =====")
    
    # 演示基本验证
    demonstrate_basic_validation()
    
    # 演示批量验证
    demonstrate_batch_validation()
    
    # 演示元数据增强
    demonstrate_metadata_enhancement()
    
    # 演示修复建议
    print("\n===== 连续性问题修复建议 =====")
    scenes = create_problematic_scenes()
    results = validate_scenes(scenes)
    suggestions = suggest_fixes(results)
    
    print(f"发现 {len(suggestions)} 组连续性问题:")
    for i, suggestion in enumerate(suggestions):
        print(f"\n问题组 {i+1} (场景对 {suggestion['scene_pair'][0]}-{suggestion['scene_pair'][1]}):")
        for j, (problem, fix) in enumerate(zip(suggestion["problems"], suggestion["fixes"])):
            print(f"  问题 {j+1}: {problem['description']}")
            print(f"  修复建议: {fix}")
            print()

if __name__ == "__main__":
    main() 