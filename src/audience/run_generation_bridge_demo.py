#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
代际差异桥接器运行脚本

这是一个简单的脚本，用于演示代际差异桥接器的功能，
不依赖于完整的VisionAI-ClipsMaster项目，可以独立运行。
"""

import sys
import os
import json
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
sys.modules['src.nlp.text_processor'] = MockModule()
sys.modules['src.nlp.language_detector'] = MockModule()
sys.modules['src.emotion.intensity_mapper'] = MockModule()
sys.modules['src.adaptation.culture_adapter'] = MockModule()

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

# 模拟必要的类
class TextProcessor:
    def __init__(self):
        pass

class CultureAdapter:
    def __init__(self):
        pass
    
    def localize_cultural_references(self, text, source_lang, target_lang):
        return text

# 创建简单测试内容
def create_test_contents():
    # Z世代内容
    z_gen_content = {
        "title": "二次元动漫角色大盘点",
        "description": "这些角色简直绝绝子，太可了，我直接笑死！",
        "scenes": [
            {
                "id": "scene_1",
                "description": "玩梗时刻，满屏yyds",
                "elements": [
                    {"type": "text", "content": "这个角色也太A了，破防了"},
                    {"type": "image", "source": "meme.png"}
                ]
            },
            {
                "id": "scene_2",
                "description": "整片化的原神场景",
                "elements": [
                    {"type": "video", "content": "原神游戏中最嘎嘎猛的时刻"}
                ]
            }
        ],
        "dialogues": [
            {"speaker": "narrator", "text": "这些梗真是太香了，yyds！"},
            {"speaker": "presenter", "text": "直接一整个无语子，破防了家人们！"}
        ]
    }
    
    # 80后内容
    gen80_content = {
        "title": "怀旧经典动画角色回顾",
        "description": "这些角色陪伴了我们的童年，满满的回忆",
        "scenes": [
            {
                "id": "scene_1",
                "description": "经典港台动画，长篇叙事",
                "elements": [
                    {"type": "text", "content": "小时候最喜欢看的卡通形象"},
                    {"type": "image", "source": "classic.png"}
                ]
            },
            {
                "id": "scene_2",
                "description": "青春记忆，经典款角色",
                "elements": [
                    {"type": "video", "content": "80年代最流行的动画角色"}
                ]
            }
        ],
        "dialogues": [
            {"speaker": "narrator", "text": "这些经典角色真是满满的回忆啊"},
            {"speaker": "presenter", "text": "那个年代的动画真是越看越有味道"}
        ]
    }
    
    # 90后内容
    gen90_content = {
        "title": "那些年我们追过的动漫",
        "description": "从QQ空间到微博，这些角色陪伴了我们",
        "scenes": [
            {
                "id": "scene_1",
                "description": "非主流时代的经典角色",
                "elements": [
                    {"type": "text", "content": "那时候贴吧上到处都是这些角色"},
                    {"type": "image", "source": "90s.png"}
                ]
            }
        ],
        "dialogues": [
            {"speaker": "narrator", "text": "这些角色简直是我们这代人的青春啊"},
            {"speaker": "presenter", "text": "LOL和这些动漫角色简直是绝配"}
        ]
    }
    
    return {
        "Z世代": z_gen_content,
        "80后": gen80_content,
        "90后": gen90_content
    }

def print_content_summary(content, label="内容"):
    """打印内容摘要"""
    print(f"\n{label}摘要:")
    print(f"标题: {content.get('title', '无标题')}")
    print(f"描述: {content.get('description', '无描述')}")
    
    if "dialogues" in content and content["dialogues"]:
        print(f"对话示例: {content['dialogues'][0].get('text', '无内容')}")
    
    if "scenes" in content and content["scenes"]:
        print(f"场景描述: {content['scenes'][0].get('description', '无描述')}")
        if "elements" in content["scenes"][0] and content["scenes"][0]["elements"]:
            print(f"元素内容: {content['scenes'][0]['elements'][0].get('content', '无内容')}")

# 主函数
def main():
    print("代际差异桥接器简单演示运行中...\n")
    
    try:
        # 手动替换模块
        sys.modules['src.utils.log_handler'].get_logger = get_logger
        sys.modules['src.nlp.text_processor'].TextProcessor = TextProcessor
        sys.modules['src.adaptation.culture_adapter'].CultureAdapter = CultureAdapter
        
        # 导入代际差异桥接器模块
        from src.audience.generation_gap import (
            GenerationBridge, get_generation_bridge, 
            bridge_gap, detect_content_generation,
            insert_cultural_elements
        )
        print("成功导入代际差异桥接器模块")
        
        # 创建测试内容
        contents = create_test_contents()
        print("创建测试内容成功")
        
        # 1. 检测内容的代际倾向
        print("\n1. 检测内容代际倾向:")
        for gen_name, content in contents.items():
            detected = detect_content_generation(content)
            print(f"- {gen_name}内容的检测结果: {detected}")
        
        # 2. 代际转换示例
        print("\n2. 代际转换示例:")
        
        # Z世代 -> 80后
        z_to_80 = bridge_gap(contents["Z世代"], "80后")
        print("\nZ世代 -> 80后 转换:")
        print_content_summary(contents["Z世代"], "原始Z世代内容")
        print_content_summary(z_to_80, "转换为80后风格后")
        
        # 80后 -> Z世代
        gen80_to_z = bridge_gap(contents["80后"], "Z世代")
        print("\n80后 -> Z世代 转换:")
        print_content_summary(contents["80后"], "原始80后内容") 
        print_content_summary(gen80_to_z, "转换为Z世代风格后")
        
        # 3. 插入文化元素
        print("\n3. 文化元素插入示例:")
        
        # 创建通用内容
        generic_content = {
            "title": "动画角色分析",
            "description": "探讨几个经典动画角色的特点",
            "scenes": [
                {
                    "id": "scene_1",
                    "description": "展示不同角色类型",
                    "elements": [
                        {"type": "text", "content": "这些角色各有不同的设计理念"}
                    ]
                }
            ],
            "dialogues": [
                {"speaker": "narrator", "text": "动画角色的设计反映了时代特征"}
            ]
        }
        
        # 向通用内容中插入Z世代文化元素
        z_elements = ["二次元", "yyds", "破防"]
        z_enhanced = insert_cultural_elements(generic_content, z_elements)
        print_content_summary(generic_content, "原始通用内容")
        print_content_summary(z_enhanced, "添加Z世代元素后")
        
        # 4. 世代风格应用
        print("\n4. 世代风格应用示例:")
        
        # 获取桥接器实例
        bridge = get_generation_bridge()
        
        # 测试文本样本
        test_text = "这些动画角色设计很好，值得一看"
        
        # 应用不同世代风格
        z_styled = bridge._apply_z_generation_style(test_text)
        gen80_styled = bridge._apply_80s_style(test_text)
        gen90_styled = bridge._apply_90s_style(test_text)
        
        print(f"原始文本: {test_text}")
        print(f"Z世代风格: {z_styled}")
        print(f"80后风格: {gen80_styled}")
        print(f"90后风格: {gen90_styled}")
        
        print("\n代际差异桥接器演示完成")
        
    except Exception as e:
        print(f"演示过程中发生错误: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    main() 