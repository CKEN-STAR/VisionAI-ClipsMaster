#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
A/B测试路由器演示脚本

展示如何使用A/B测试路由器进行特性和内容变体测试。
"""

import os
import sys
import json
from pprint import pprint
import time
from datetime import datetime
import traceback
import random
import numpy as np

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

print("开始A/B测试路由器演示脚本...")

# 替换真实模块为模拟模块
import src.audience.privacy_guard_mock as mock
sys.modules['src.data.storage_manager'] = mock
sys.modules['src.utils.log_handler'] = mock
sys.modules['src.utils.privacy_manager'] = mock
sys.modules['src.core.privacy_manager'] = mock

# 准备模拟用户画像引擎
class MockProfileEngine:
    """模拟用户画像引擎"""
    
    def __init__(self):
        """初始化模拟用户画像引擎"""
        self.profiles = {}
        self._create_sample_profiles()
    
    def _create_sample_profiles(self):
        """创建示例用户画像"""
        # 用户1：喜欢快节奏、动作内容
        self.profiles["user_001"] = {
            "content_preferences": {
                "action": {"score": 0.9},
                "comedy": {"score": 0.6},
                "drama": {"score": 0.3},
                "thriller": {"score": 0.7}
            },
            "emotion_response": {
                "excitement": {"score": 0.8},
                "tension": {"score": 0.7},
                "amusement": {"score": 0.5}
            },
            "editing_preferences": {
                "fast_cuts": {"score": 0.9},
                "dynamic_camera": {"score": 0.8},
                "special_effects": {"score": 0.7}
            },
            "narrative_preferences": {
                "direct": {"score": 0.8},
                "twist_ending": {"score": 0.6},
                "character_focus": {"score": 0.4}
            },
            "pacing_preferences": {
                "fast": {"score": 0.9},
                "consistent": {"score": 0.7},
                "building": {"score": 0.5}
            }
        }
        
        # 用户2：喜欢慢节奏、情感内容
        self.profiles["user_002"] = {
            "content_preferences": {
                "drama": {"score": 0.9},
                "romance": {"score": 0.8},
                "documentary": {"score": 0.6},
                "comedy": {"score": 0.4}
            },
            "emotion_response": {
                "empathy": {"score": 0.9},
                "warmth": {"score": 0.8},
                "reflection": {"score": 0.7}
            },
            "editing_preferences": {
                "slow_cuts": {"score": 0.8},
                "stable_camera": {"score": 0.9},
                "natural_lighting": {"score": 0.7}
            },
            "narrative_preferences": {
                "complex": {"score": 0.8},
                "character_development": {"score": 0.9},
                "open_ending": {"score": 0.7}
            },
            "pacing_preferences": {
                "slow": {"score": 0.8},
                "gradual": {"score": 0.9},
                "reflective": {"score": 0.7}
            }
        }
        
        # 用户3：平衡类型
        self.profiles["user_003"] = {
            "content_preferences": {
                "action": {"score": 0.5},
                "comedy": {"score": 0.6},
                "drama": {"score": 0.5},
                "documentary": {"score": 0.4}
            },
            "emotion_response": {
                "excitement": {"score": 0.5},
                "empathy": {"score": 0.6},
                "amusement": {"score": 0.6}
            },
            "editing_preferences": {
                "balanced_cuts": {"score": 0.7},
                "varied_camera": {"score": 0.6},
                "subtle_effects": {"score": 0.5}
            },
            "narrative_preferences": {
                "linear": {"score": 0.6},
                "character_focus": {"score": 0.6},
                "satisfying_ending": {"score": 0.7}
            },
            "pacing_preferences": {
                "varied": {"score": 0.8},
                "contextual": {"score": 0.7},
                "adaptive": {"score": 0.6}
            }
        }
    
    def get_profile(self, user_id):
        """获取用户画像"""
        if user_id in self.profiles:
            return self.profiles[user_id]
        
        # 如果没有找到用户，返回随机生成的画像
        return self._generate_random_profile()
    
    def _generate_random_profile(self):
        """生成随机用户画像"""
        return {
            "content_preferences": {
                "action": {"score": random.random()},
                "comedy": {"score": random.random()},
                "drama": {"score": random.random()},
                "thriller": {"score": random.random()}
            },
            "emotion_response": {
                "excitement": {"score": random.random()},
                "empathy": {"score": random.random()},
                "amusement": {"score": random.random()}
            },
            "editing_preferences": {
                "fast_cuts": {"score": random.random()},
                "dynamic_camera": {"score": random.random()},
                "special_effects": {"score": random.random()}
            },
            "narrative_preferences": {
                "linear": {"score": random.random()},
                "character_focus": {"score": random.random()},
                "twist_ending": {"score": random.random()}
            },
            "pacing_preferences": {
                "fast": {"score": random.random()},
                "consistent": {"score": random.random()},
                "building": {"score": random.random()}
            }
        }

# 替换用户画像引擎
sys.modules['src.audience.profile_builder'] = type('', (), {
    'get_profile_engine': lambda: MockProfileEngine()
})

try:
    from src.audience.ab_router import (
        get_ab_router, route_variant, create_ab_test, 
        record_ab_event, analyze_ab_results
    )
    print("成功导入A/B测试路由器模块")
except Exception as e:
    print(f"导入A/B测试路由器模块时出错: {str(e)}")
    traceback.print_exc()
    sys.exit(1)

def print_section(title):
    """打印分节标题"""
    print("\n" + "=" * 60)
    print(f" {title} ".center(60, "="))
    print("=" * 60)

def demonstrate_ab_testing():
    """演示A/B测试功能"""
    print_section("A/B测试路由器演示")
    
    # 获取路由器实例
    print("正在获取A/B测试路由器...")
    try:
        ab_router = get_ab_router()
        print("成功获取A/B测试路由器")
    except Exception as e:
        print(f"获取A/B测试路由器时发生错误: {str(e)}")
        traceback.print_exc()
        return
    
    # 设置测试用户
    test_users = ["user_001", "user_002", "user_003", "user_004", "user_005"]
    
    # 演示1：内容变体路由
    print_section("1. 内容变体路由演示")
    
    # 准备内容变体
    content_variants = [
        {
            "id": "content_v1",
            "name": "标准版内容",
            "description": "标准节奏和剪辑风格",
            "feature_vector": [0.5, 0.5, 0.5, 0.5, 0.5, 0.5]
        },
        {
            "id": "content_v2",
            "name": "快节奏版内容",
            "description": "快速剪辑和高能量内容",
            "feature_vector": [0.9, 0.3, 0.8, 0.2, 0.7, 0.4]
        },
        {
            "id": "content_v3",
            "name": "情感强化版内容",
            "description": "强调情感共鸣和角色发展",
            "feature_vector": [0.3, 0.9, 0.4, 0.8, 0.5, 0.7]
        }
    ]
    
    print("\n内容变体列表:")
    for i, variant in enumerate(content_variants):
        print(f"变体 {i+1}: {variant['name']} - {variant['description']}")
    
    print("\n为不同用户分配内容变体:")
    for user_id in test_users:
        try:
            best_variant = route_variant(user_id, content_variants)
            print(f"用户 {user_id} -> {best_variant['name']}")
        except Exception as e:
            print(f"为用户 {user_id} 分配变体时发生错误: {str(e)}")
    
    # 演示2：创建A/B测试
    print_section("2. 创建A/B测试")
    
    # 准备UI变体
    ui_variants = [
        {
            "id": "ui_standard",
            "name": "标准UI",
            "description": "当前使用的标准界面",
            "feature_vector": [0.5, 0.5, 0.5, 0.5]
        },
        {
            "id": "ui_simplified",
            "name": "简化UI",
            "description": "减少按钮和选项的简化界面",
            "feature_vector": [0.3, 0.8, 0.4, 0.2]
        },
        {
            "id": "ui_advanced",
            "name": "高级UI",
            "description": "提供更多控制选项的高级界面",
            "feature_vector": [0.8, 0.3, 0.7, 0.9]
        }
    ]
    
    # 创建测试配置
    test_config = {
        "start_time": datetime.now().isoformat(),
        "metrics": ["completion_rate", "engagement_time", "interaction_count"],
        "assignment_strategy": "weighted"
    }
    
    print("\n创建UI界面A/B测试...")
    try:
        test_id = "ui_test_001"
        test_result = create_ab_test(test_id, ui_variants, test_config)
        print(f"成功创建A/B测试: {test_id}")
        print("\n测试配置:")
        pprint(test_result)
    except Exception as e:
        print(f"创建A/B测试时发生错误: {str(e)}")
        traceback.print_exc()
    
    # 演示3：记录用户事件
    print_section("3. 记录用户事件")
    
    # 模拟一些用户事件
    events = [
        {"user_id": "user_001", "variant_id": "content_v2", "event_type": "view", "data": {"duration": 45}},
        {"user_id": "user_001", "variant_id": "content_v2", "event_type": "completion", "data": {"full": True}},
        {"user_id": "user_001", "variant_id": "content_v2", "event_type": "share", "data": {"platform": "wechat"}},
        
        {"user_id": "user_002", "variant_id": "content_v3", "event_type": "view", "data": {"duration": 60}},
        {"user_id": "user_002", "variant_id": "content_v3", "event_type": "interaction", "data": {"type": "like"}},
        {"user_id": "user_002", "variant_id": "content_v3", "event_type": "completion", "data": {"full": True}},
        
        {"user_id": "user_003", "variant_id": "content_v1", "event_type": "view", "data": {"duration": 30}},
        {"user_id": "user_003", "variant_id": "content_v1", "event_type": "interaction", "data": {"type": "comment"}},
        {"user_id": "user_003", "variant_id": "content_v1", "event_type": "skip", "data": {"time": 25}}
    ]
    
    print("\n记录用户事件...")
    for event in events:
        try:
            record_ab_event(
                event["user_id"], 
                event["variant_id"], 
                event["event_type"], 
                event["data"]
            )
            print(f"记录事件: 用户 {event['user_id']} - {event['event_type']} - 变体 {event['variant_id']}")
        except Exception as e:
            print(f"记录事件时发生错误: {str(e)}")
    
    # 演示4：分析测试结果
    print_section("4. 分析测试结果")
    
    # 创建内容测试
    content_test_id = "content_test_001"
    create_ab_test(content_test_id, content_variants)
    
    # 模拟内容测试已收集了足够的数据
    ab_router = get_ab_router()
    ab_router.storage.get_ab_events = MagicMock(return_value=events)
    
    print("\n分析内容变体测试结果...")
    try:
        analysis = analyze_ab_results(content_test_id)
        print("\n测试分析结果:")
        pprint(analysis)
        
        print("\n性能指标:")
        for metric, values in analysis.get("metrics", {}).items():
            print(f"- {metric}:")
            for variant_id, value in values.items():
                variant_name = next((v["name"] for v in content_variants if v["id"] == variant_id), variant_id)
                print(f"  {variant_name}: {value:.2f}")
        
        print("\n建议:")
        for recommendation in analysis.get("recommendations", []):
            print(f"- {recommendation}")
    except Exception as e:
        print(f"分析测试结果时发生错误: {str(e)}")
        traceback.print_exc()
    
    # 演示5：多变量测试
    print_section("5. 多变量测试演示")
    
    # 准备多变量测试的变体
    multivariate_variants = [
        {
            "id": "mv_variant_1",
            "name": "组合变体1",
            "description": "标准内容 + 简化UI",
            "content_variant": "content_v1",
            "ui_variant": "ui_simplified",
            "feature_vector": [0.4, 0.6, 0.5, 0.4, 0.5, 0.3]
        },
        {
            "id": "mv_variant_2",
            "name": "组合变体2",
            "description": "快节奏内容 + 标准UI",
            "content_variant": "content_v2",
            "ui_variant": "ui_standard",
            "feature_vector": [0.7, 0.4, 0.6, 0.3, 0.6, 0.5]
        },
        {
            "id": "mv_variant_3",
            "name": "组合变体3",
            "description": "情感内容 + 高级UI",
            "content_variant": "content_v3",
            "ui_variant": "ui_advanced",
            "feature_vector": [0.5, 0.8, 0.5, 0.9, 0.4, 0.7]
        },
        {
            "id": "mv_variant_4",
            "name": "组合变体4",
            "description": "快节奏内容 + 高级UI",
            "content_variant": "content_v2",
            "ui_variant": "ui_advanced",
            "feature_vector": [0.8, 0.3, 0.7, 0.8, 0.6, 0.5]
        }
    ]
    
    print("\n多变量测试变体:")
    for i, variant in enumerate(multivariate_variants):
        print(f"变体 {i+1}: {variant['name']} - {variant['description']}")
    
    print("\n为用户分配多变量测试变体:")
    for user_id in test_users:
        try:
            best_variant = route_variant(user_id, multivariate_variants)
            print(f"用户 {user_id} -> {best_variant['name']}")
        except Exception as e:
            print(f"为用户 {user_id} 分配变体时发生错误: {str(e)}")
    
    print("\n演示完成！")

if __name__ == "__main__":
    try:
        demonstrate_ab_testing()
    except Exception as e:
        print(f"演示过程中发生错误: {str(e)}")
        traceback.print_exc() 