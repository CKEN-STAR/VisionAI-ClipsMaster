#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户画像构建测试脚本

用于测试多维度用户画像构建功能
"""

import os
import json
import sys
from pathlib import Path
import logging
from pprint import pprint

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from src.audience.profile_builder import (
    get_profile_engine,
    create_user_profile,
    update_user_profile,
    get_user_profile
)
from src.utils.log_handler import get_logger

# 配置日志
test_logger = get_logger("test_profile")

def test_user_profile_creation():
    """测试用户画像创建功能"""
    test_logger.info("开始测试用户画像创建功能")
    
    # 测试用户ID
    test_user_id = "test_user_001"
    
    # 创建用户画像
    profile = create_user_profile(test_user_id)
    
    # 打印结果
    test_logger.info(f"用户画像创建结果:")
    print("\n用户画像概览:")
    print(f"用户ID: {profile.get('user_id')}")
    print(f"创建时间: {profile.get('created_at')}")
    
    # 打印主要维度
    dimensions = [
        ("基本信息", "basic_info"),
        ("内容偏好", "content_preferences"),
        ("情感响应", "emotion_response"),
        ("设备约束", "device_constraints"),
        ("剪辑偏好", "editing_preferences"),
        ("叙事偏好", "narrative_preferences"),
        ("节奏偏好", "pacing_preferences")
    ]
    
    for label, key in dimensions:
        data = profile.get(key, {})
        confidence = data.get("confidence", 0)
        print(f"\n{label} (置信度: {confidence:.2f}):")
        # 根据维度类型打印关键信息
        if key == "basic_info":
            print(f"  年龄组: {data.get('age_group', 'unknown')}")
            print(f"  语言: {data.get('language', 'unknown')}")
        elif key == "content_preferences":
            genres = data.get("favorite_genres", [])
            if genres:
                print("  喜爱的短剧类型:")
                for genre in genres:
                    print(f"    - {genre.get('genre')}: {genre.get('strength', 0):.2f}")
        elif key == "device_constraints":
            print(f"  内存限制: {data.get('memory_limit', 0)}MB")
            print(f"  GPU可用: {'是' if data.get('gpu_available', False) else '否'}")
    
    test_logger.info("用户画像创建测试完成")
    return profile

def test_profile_update():
    """测试用户画像更新功能"""
    test_logger.info("开始测试用户画像更新功能")
    
    # 测试用户ID
    test_user_id = "test_user_001"
    
    # 更新用户画像
    updated_profile = update_user_profile(test_user_id)
    
    # 打印更新时间
    print(f"\n用户画像更新时间: {updated_profile.get('updated_at')}")
    
    test_logger.info("用户画像更新测试完成")
    return updated_profile

def test_profile_retrieval():
    """测试用户画像获取功能"""
    test_logger.info("开始测试用户画像获取功能")
    
    # 测试用户ID
    test_user_id = "test_user_001"
    
    # 获取用户画像
    profile = get_user_profile(test_user_id)
    
    if profile:
        print(f"\n成功获取用户 {test_user_id} 的画像")
        print(f"版本: {profile.get('version')}")
        if 'updated_at' in profile:
            print(f"上次更新: {profile.get('updated_at')}")
    else:
        print(f"\n未找到用户 {test_user_id} 的画像")
    
    test_logger.info("用户画像获取测试完成")
    return profile

if __name__ == "__main__":
    print("\n===== 用户画像构建系统测试 =====\n")
    
    # 测试画像创建
    profile = test_user_profile_creation()
    
    # 测试画像更新
    updated_profile = test_profile_update()
    
    # 测试画像获取
    retrieved_profile = test_profile_retrieval()
    
    print("\n===== 测试完成 =====\n") 