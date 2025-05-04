#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
跨平台习惯融合演示脚本

展示如何使用跨平台习惯融合模块整合用户在多个平台上的行为习惯和偏好，
构建统一的用户画像。
"""

import os
import sys
import json
import time
from pprint import pprint
from typing import Dict, Any

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.audience.cross_platform import (
    get_platform_integrator, integrate_user_habits, 
    get_unified_preference, get_platform_habit
)

def print_section(title):
    """打印分节标题"""
    print("\n" + "=" * 60)
    print(f" {title} ".center(60, "="))
    print("=" * 60)

def print_platform_data(title, data):
    """打印平台数据摘要"""
    print(f"\n--- {title} ---")
    if not data:
        print("  无可用数据")
        return
    
    # 打印分类偏好
    if "category_preferences" in data:
        print("\n分类偏好:")
        for category, pref in data["category_preferences"].items():
            print(f"  {category}: 分数 {pref.get('score', 0):.2f}")
    
    # 打印内容格式偏好
    if "content_format_preference" in data:
        print("\n内容格式偏好:")
        for format_type, score in data["content_format_preference"].items():
            print(f"  {format_type}: {score:.2f}")
    
    # 打印观看时长
    if "watch_duration" in data:
        duration = data["watch_duration"]
        if "average" in duration:
            print(f"\n平均观看时长: {duration['average']:.1f} {duration.get('unit', 'seconds')}")
    
    # 打印活跃时段
    if "active_time_slots" in data:
        print("\n活跃时段:")
        for slot in data["active_time_slots"]:
            print(f"  {slot}")

def print_unified_preference(pref):
    """打印统一偏好摘要"""
    print("\n--- 统一偏好表达 ---")
    if not pref:
        print("  无可用数据")
        return
    
    # 打印分类偏好
    if "category_preferences" in pref:
        print("\n跨平台分类偏好:")
        for category, data in pref["category_preferences"].items():
            platforms = ', '.join(data.get("platforms", []))
            print(f"  {category}: 分数 {data.get('score', 0):.2f} (来源: {platforms})")
    
    # 打印内容格式偏好
    if "format_preferences" in pref:
        print("\n跨平台内容格式偏好:")
        for format_type, data in pref["format_preferences"].items():
            platforms = ', '.join(data.get("platforms", []))
            print(f"  {format_type}: 分数 {data.get('score', 0):.2f} (来源: {platforms})")
    
    # 打印观看时长
    if "watch_duration" in pref:
        duration = pref["watch_duration"]
        if "average" in duration:
            print(f"\n跨平台平均观看时长: {duration['average']:.1f} {duration.get('unit', 'seconds')}")
    
    # 打印活跃时段
    if "active_time_slots" in pref:
        print("\n跨平台活跃时段:")
        for slot in pref["active_time_slots"]:
            print(f"  {slot}")
    
    # 打印平台覆盖
    if "platform_coverage" in pref:
        print("\n平台数据覆盖:")
        for platform, has_data in pref["platform_coverage"].items():
            print(f"  {platform}: {'✓' if has_data else '✗'}")

def demonstrate_cross_platform_integration():
    """演示跨平台习惯融合功能"""
    test_user_id = "demo_user_123"
    
    print_section("跨平台习惯融合演示")
    print(f"用户ID: {test_user_id}")
    
    # 获取跨平台整合器
    integrator = get_platform_integrator()
    
    # 模拟数据获取
    print("\n获取各平台习惯数据...")
    
    # 为了演示目的，使用内部方法直接访问
    # 这些方法正常情况下会通过API获取数据，现在使用模拟数据
    integrator._get_douyin_habits = lambda user_id: {
        "favorite_categories": ["搞笑", "生活", "美食"],
        "content_format_preference": {
            "短视频": 0.8,
            "直播": 0.2
        },
        "watch_duration": {
            "average": 35.6,
            "unit": "seconds"
        },
        "active_time_slots": ["18:00-22:00", "12:00-13:00"],
        "category_preferences": {
            "搞笑": {"score": 0.8, "strength": "strong_like"},
            "生活": {"score": 0.7, "strength": "like"},
            "美食": {"score": 0.9, "strength": "strong_like"}
        }
    }
    
    integrator._get_bilibili_habits = lambda user_id: {
        "favorite_partitions": ["动画", "游戏", "科技"],
        "content_format_preference": {
            "视频": 0.6,
            "直播": 0.3,
            "番剧": 0.1
        },
        "watch_duration": {
            "average": 420.5,
            "unit": "seconds"
        },
        "active_time_slots": ["19:00-23:00", "13:00-15:00"],
        "category_preferences": {
            "动画": {"score": 0.8, "strength": "strong_like"},
            "游戏": {"score": 0.9, "strength": "strong_like"},
            "科技": {"score": 0.7, "strength": "like"}
        }
    }
    
    integrator._get_youtube_habits = lambda user_id: {
        "subscribed_categories": ["Entertainment", "Technology", "Music"],
        "content_format_preference": {
            "视频": 0.7,
            "短视频": 0.2,
            "直播": 0.1
        },
        "watch_duration": {
            "average": 540.2,
            "unit": "seconds"
        },
        "active_time_slots": ["20:00-24:00", "7:00-9:00"],
        "category_preferences": {
            "Entertainment": {"score": 0.7, "strength": "like"},
            "Technology": {"score": 0.8, "strength": "strong_like"},
            "Music": {"score": 0.6, "strength": "like"}
        }
    }
    
    # 设置存储层模拟
    integrator.storage.get_cross_platform_data = lambda user_id: None
    integrator.storage.save_cross_platform_data = lambda user_id, data: None
    
    # 获取各平台数据
    douyin_data = get_platform_habit(test_user_id, "douyin")
    bilibili_data = get_platform_habit(test_user_id, "bilibili")
    youtube_data = get_platform_habit(test_user_id, "youtube")
    
    # 打印各平台数据摘要
    print_platform_data("抖音平台数据", douyin_data)
    print_platform_data("B站平台数据", bilibili_data)
    print_platform_data("YouTube平台数据", youtube_data)
    
    # 整合跨平台习惯
    print("\n开始整合跨平台习惯数据...")
    integrated_data = integrate_user_habits(test_user_id)
    
    # 获取统一偏好表达
    print("\n获取统一偏好表达...")
    unified_pref = get_unified_preference(test_user_id)
    
    # 打印统一偏好摘要
    print_unified_preference(unified_pref)
    
    print("\n演示完成！")

if __name__ == "__main__":
    try:
        demonstrate_cross_platform_integration()
    except Exception as e:
        print(f"演示过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc() 