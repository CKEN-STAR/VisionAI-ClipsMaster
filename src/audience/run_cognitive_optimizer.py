#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
认知负荷优化器运行脚本

这是一个简单的脚本，用于演示认知负荷优化器的功能，
不依赖于完整的VisionAI-ClipsMaster项目，可以独立运行。
"""

import sys
import os
import json
import time
import traceback

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# 替换真实模块为模拟模块
class MockModule:
    def __getattr__(self, name):
        return lambda *args, **kwargs: None

sys.modules['src.data.storage_manager'] = MockModule()
sys.modules['src.utils.log_handler'] = MockModule()
sys.modules['src.utils.privacy_manager'] = MockModule()
sys.modules['src.core.privacy_manager'] = MockModule()

# 定义简单的日志处理器
class SimpleLogger:
    def info(self, msg):
        print(f"[INFO] {msg}")
    
    def debug(self, msg):
        pass
    
    def warning(self, msg):
        print(f"[WARNING] {msg}")
    
    def error(self, msg):
        print(f"[ERROR] {msg}")

# 模拟log_handler
def get_logger(name):
    return SimpleLogger()

# 创建简单测试内容
def create_test_content():
    return {
        "title": "测试视频",
        "duration": 120.0,  # 2分钟
        "complexity": 0.8,  # 高复杂度
        "twists_per_min": 5.0,  # 高转折频率
        "scenes": [
            {
                "id": "scene_1",
                "description": "开场介绍",
                "duration": 15.0,
                "importance": 0.8,
                "elements": [
                    {"type": "text", "content": "欢迎", "importance": 0.8},
                    {"type": "image", "source": "logo.png", "importance": 0.7}
                ],
                "transitions": [
                    {"type": "fade", "duration": 1.0, "importance": 0.6}
                ],
                "effects": []
            },
            {
                "id": "scene_2",
                "description": "主要内容",
                "duration": 60.0,
                "importance": 0.9,
                "has_key_information": True,
                "elements": [
                    {"type": "video", "source": "clip1.mp4", "importance": 0.9},
                    {"type": "text", "content": "关键信息1", "importance": 0.9},
                    {"type": "text", "content": "关键信息2", "importance": 0.8},
                    {"type": "image", "source": "graphic1.png", "importance": 0.7},
                    {"type": "image", "source": "graphic2.png", "importance": 0.5},
                    {"type": "text", "content": "补充说明", "importance": 0.4},
                    {"type": "text", "content": "额外细节", "importance": 0.3}
                ],
                "transitions": [
                    {"type": "slide", "duration": 0.8, "importance": 0.7},
                    {"type": "zoom", "duration": 1.2, "importance": 0.5}
                ],
                "effects": [
                    {"type": "highlight", "duration": 2.0, "importance": 0.8},
                    {"type": "blur", "duration": 1.5, "importance": 0.4}
                ]
            },
            {
                "id": "scene_3",
                "description": "次要内容",
                "duration": 30.0,
                "importance": 0.6,
                "elements": [
                    {"type": "video", "source": "clip2.mp4", "importance": 0.6},
                    {"type": "text", "content": "次要信息", "importance": 0.5},
                    {"type": "image", "source": "graphic3.png", "importance": 0.4}
                ],
                "transitions": [
                    {"type": "fade", "duration": 1.0, "importance": 0.5},
                    {"type": "wipe", "duration": 1.2, "importance": 0.4},
                    {"type": "dissolve", "duration": 0.8, "importance": 0.3}
                ],
                "effects": [
                    {"type": "color_shift", "duration": 2.0, "importance": 0.3},
                    {"type": "particle", "duration": 3.0, "importance": 0.2}
                ]
            },
            {
                "id": "scene_4",
                "description": "结尾总结",
                "duration": 15.0,
                "importance": 0.7,
                "emotional_peak": True,
                "elements": [
                    {"type": "text", "content": "总结", "importance": 0.8},
                    {"type": "image", "source": "logo.png", "importance": 0.7},
                    {"type": "text", "content": "联系方式", "importance": 0.6}
                ],
                "transitions": [
                    {"type": "fade", "duration": 1.0, "importance": 0.6}
                ],
                "effects": [
                    {"type": "glow", "duration": 2.0, "importance": 0.5}
                ]
            }
        ],
        "dialogues": [
            {"speaker": "narrator", "text": "欢迎观看我们的演示视频", "importance": 0.8},
            {"speaker": "presenter", "text": "今天我们将介绍一个重要的新功能", "importance": 0.9},
            {"speaker": "presenter", "text": "这个功能有很多优点和特性", "importance": 0.7},
            {"speaker": "presenter", "text": "首先，它能够大幅提升效率", "importance": 0.8},
            {"speaker": "presenter", "text": "其次，它使用起来非常简单", "importance": 0.7},
            {"speaker": "presenter", "text": "最后，它与现有系统完美兼容", "importance": 0.6},
            {"speaker": "narrator", "text": "感谢观看，请不要忘记关注我们", "importance": 0.7}
        ],
        "tags": ["教程", "技术", "新功能"]
    }

# 创建用户画像
def create_user_profiles():
    return {
        "高认知能力用户": {
            "cognitive_abilities": {
                "attention_span": 0.9,
                "processing_speed": 0.8,
                "domain_knowledge": 0.8
            }
        },
        "中等认知能力用户": {
            "cognitive_abilities": {
                "attention_span": 0.6,
                "processing_speed": 0.6,
                "domain_knowledge": 0.5
            }
        },
        "低认知能力用户": {
            "cognitive_abilities": {
                "attention_span": 0.3,
                "processing_speed": 0.4,
                "domain_knowledge": 0.2
            }
        }
    }

# 打印内容统计
def print_content_stats(content, label="内容"):
    print(f"\n{label}统计:")
    print(f"- 场景数量: {len(content.get('scenes', []))}")
    
    total_elements = sum(len(scene.get("elements", [])) for scene in content.get("scenes", []))
    print(f"- 总元素数量: {total_elements}")
    
    total_transitions = sum(len(scene.get("transitions", [])) for scene in content.get("scenes", []))
    print(f"- 总转场数量: {total_transitions}")
    
    total_effects = sum(len(scene.get("effects", [])) for scene in content.get("scenes", []))
    print(f"- 总特效数量: {total_effects}")
    
    print(f"- 对话数量: {len(content.get('dialogues', []))}")

# 主函数
def main():
    print("认知负荷优化器简单演示运行中...\n")
    
    try:
        # 手动导入认知负荷优化器模块
        sys.modules['src.utils.log_handler'].get_logger = get_logger
        
        from src.audience.cognitive_optimizer import (
            CognitiveLoadBalancer, optimize_content, calculate_cognitive_load
        )
        print("成功导入认知负荷优化器模块")
        
        # 创建测试内容
        content = create_test_content()
        print("创建测试内容成功")
        
        # 创建用户画像
        user_profiles = create_user_profiles()
        print("创建用户画像成功")
        
        # 计算不同用户的认知负荷
        print("\n计算认知负荷:")
        for profile_name, profile in user_profiles.items():
            load = calculate_cognitive_load(content, profile)
            print(f"- {profile_name}: {load:.2f}")
        
        # 优化内容
        print("\n对不同用户优化内容:")
        for profile_name, profile in user_profiles.items():
            print(f"\n为 {profile_name} 优化内容:")
            
            # 计算优化前负荷
            original_load = calculate_cognitive_load(content, profile)
            print(f"- 优化前认知负荷: {original_load:.2f}")
            
            # 优化内容
            start_time = time.time()
            optimized_content = optimize_content(content, profile)
            optimization_time = time.time() - start_time
            
            # 计算优化后负荷
            optimized_load = calculate_cognitive_load(optimized_content, profile)
            print(f"- 优化后认知负荷: {optimized_load:.2f}")
            print(f"- 优化耗时: {optimization_time:.3f}秒")
            
            # 打印统计信息
            print_content_stats(content, "优化前")
            print_content_stats(optimized_content, "优化后")
            
            # 打印负荷降低
            if original_load > optimized_load:
                reduction = ((original_load - optimized_load) / original_load) * 100
                print(f"- 负荷降低: {reduction:.1f}%")
        
        print("\n认知负荷优化器演示完成")
        
    except Exception as e:
        print(f"演示过程中发生错误: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    main() 