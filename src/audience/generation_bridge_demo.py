#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
代际差异桥接器演示脚本

展示如何使用代际差异桥接器优化跨世代内容传播，提高不同年龄层受众的理解和接受度。
"""

import os
import sys
import json
from pprint import pprint
import time
from datetime import datetime
import traceback
import random

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

print("开始代际差异桥接器演示脚本...")

# 创建模拟模块类
class MockModule:
    def __getattr__(self, name):
        return lambda *args, **kwargs: None

# 替换真实模块为模拟模块
sys.modules['src.data.storage_manager'] = MockModule()
sys.modules['src.utils.log_handler'] = MockModule()
sys.modules['src.utils.privacy_manager'] = MockModule()
sys.modules['src.core.privacy_manager'] = MockModule()
sys.modules['src.nlp.text_processor'] = MockModule()
sys.modules['src.nlp.language_detector'] = MockModule()
sys.modules['src.emotion.intensity_mapper'] = MockModule()
sys.modules['src.adaptation.culture_adapter'] = MockModule()

# 定义模拟的文本处理器和文化适配器
class MockTextProcessor:
    def __init__(self):
        pass

class MockCultureAdapter:
    def __init__(self):
        pass
    
    def localize_cultural_references(self, text, source_lang, target_lang):
        return text

# 模拟日志处理器
class MockLogger:
    def info(self, msg):
        print(f"INFO: {msg}")
    
    def debug(self, msg):
        pass
    
    def warning(self, msg):
        print(f"WARNING: {msg}")
    
    def error(self, msg):
        print(f"ERROR: {msg}")

def get_logger(name):
    return MockLogger()

# 替换模块中的类
sys.modules['src.utils.log_handler'].get_logger = get_logger
sys.modules['src.nlp.text_processor'].TextProcessor = MockTextProcessor
sys.modules['src.adaptation.culture_adapter'].CultureAdapter = MockCultureAdapter

# 导入代际差异桥接器
try:
    from src.audience.generation_gap import (
        GenerationBridge, get_generation_bridge, 
        bridge_gap, detect_content_generation,
        insert_cultural_elements
    )
    print("成功导入代际差异桥接器模块")
except Exception as e:
    print(f"导入代际差异桥接器模块时出错: {str(e)}")
    traceback.print_exc()
    sys.exit(1)

def print_section(title):
    """打印分节标题"""
    print("\n" + "=" * 60)
    print(f" {title} ".center(60, "="))
    print("=" * 60)

def generate_sample_content(generation_style="Z世代"):
    """
    生成示例内容
    
    Args:
        generation_style: 代际风格，可选值为 Z世代, 90后, 80后, 70后
        
    Returns:
        示例内容数据
    """
    # 基础结构
    content = {
        "id": f"content_{int(time.time())}",
        "title": "动画角色分析",
        "description": "探讨几个经典动画角色的特点",
        "scenes": [],
        "dialogues": []
    }
    
    # 根据世代风格调整内容
    if generation_style == "Z世代":
        content["title"] = "二次元人物大盘点"
        content["description"] = "这些角色简直绝绝子，太爱了！"
        
        content["scenes"] = [
            {
                "id": "scene_1",
                "description": "开局整片化，展示超A的二次元形象",
                "elements": [
                    {"type": "text", "content": "这些角色真的yyds，我直接爱住了🔥"},
                    {"type": "image", "source": "anime.png"}
                ]
            },
            {
                "id": "scene_2",
                "description": "玩梗时刻，展示动漫中的鬼畜场景",
                "elements": [
                    {"type": "video", "content": "绝了，这个画面我直接破防了"},
                    {"type": "text", "content": "笑死，这个梗太上头了"}
                ]
            }
        ]
        
        content["dialogues"] = [
            {"speaker": "narrator", "text": "这些角色真的是我吹爆👍，嘎嘎猛，太可了"},
            {"speaker": "presenter", "text": "一整个无语子，这个剧情神了，真香！"},
            {"speaker": "guest", "text": "破防了家人们，这波原神设计绝绝子"}
        ]
    
    elif generation_style == "90后":
        content["title"] = "动漫角色深度解析"
        content["description"] = "盘点这些年我们追过的动漫角色"
        
        content["scenes"] = [
            {
                "id": "scene_1",
                "description": "展示经典角色的成长历程",
                "elements": [
                    {"type": "text", "content": "从QQ空间到微博，这些角色陪伴了我们的青春"},
                    {"type": "image", "source": "anime90s.png"}
                ]
            },
            {
                "id": "scene_2",
                "description": "LOL与动漫文化的交融",
                "elements": [
                    {"type": "video", "content": "这些角色让我们秒懂青春的味道"},
                    {"type": "text", "content": "蓝瘦香菇，回忆真是接地气"}
                ]
            }
        ]
        
        content["dialogues"] = [
            {"speaker": "narrator", "text": "非主流时代过去了，但这些角色依然是小鲜肉"},
            {"speaker": "presenter", "text": "从贴吧到微博，我们见证了动漫文化的变迁"},
            {"speaker": "guest", "text": "这些是我们青春无法复制的记忆"}
        ]
    
    elif generation_style == "80后":
        content["title"] = "怀旧经典动画角色大赏"
        content["description"] = "那些陪伴80后童年的经典角色"
        
        content["scenes"] = [
            {
                "id": "scene_1",
                "description": "展示港台经典动画的长篇叙事",
                "elements": [
                    {"type": "text", "content": "小时候最爱的卡通形象，满满的童年回忆"},
                    {"type": "image", "source": "classic.png"}
                ]
            },
            {
                "id": "scene_2",
                "description": "经典款角色背后的青春记忆",
                "elements": [
                    {"type": "video", "content": "那些年我们看过的流行动画"},
                    {"type": "text", "content": "怀旧金曲搭配这些角色，回忆涌现"}
                ]
            }
        ]
        
        content["dialogues"] = [
            {"speaker": "narrator", "text": "这些经典角色承载了整整一代人的记忆"},
            {"speaker": "presenter", "text": "从黑白电视到彩色动画，我们的童年很幸福"},
            {"speaker": "guest", "text": "长大后才发现，这些角色教会了我们很多人生道理"}
        ]
    
    else:  # 70后
        content["title"] = "老一辈动画形象的文化价值"
        content["description"] = "70年代的经典动画角色与岁月沉淀"
        
        content["scenes"] = [
            {
                "id": "scene_1",
                "description": "传统美术与动画角色的融合",
                "elements": [
                    {"type": "text", "content": "这些角色饱含文化底蕴，是集体记忆的一部分"},
                    {"type": "image", "source": "traditional.png"}
                ]
            },
            {
                "id": "scene_2",
                "description": "老电影中的动画元素",
                "elements": [
                    {"type": "video", "content": "年代感十足的动画形象回顾"},
                    {"type": "text", "content": "那些年的怀旧金曲与动画形象"}
                ]
            }
        ]
        
        content["dialogues"] = [
            {"speaker": "narrator", "text": "这些角色是我们老故事中不可或缺的一部分"},
            {"speaker": "presenter", "text": "岁月沉淀后，这些形象更显珍贵"},
            {"speaker": "guest", "text": "传统文化在这些角色中得到了很好的传承"}
        ]
    
    return content

def print_content_summary(content, title="内容摘要"):
    """
    打印内容摘要
    
    Args:
        content: 内容数据
        title: 摘要标题
    """
    print(f"\n{title}:")
    print(f"- 标题: {content.get('title', '无标题')}")
    print(f"- 描述: {content.get('description', '无描述')}")
    
    # 打印场景摘要
    if "scenes" in content and content["scenes"]:
        print(f"- 场景数量: {len(content['scenes'])}")
        print(f"  场景1描述: {content['scenes'][0].get('description', '无描述')}")
        
        if "elements" in content["scenes"][0] and content["scenes"][0]["elements"]:
            print(f"  场景1元素: {content['scenes'][0]['elements'][0].get('content', '无内容')}")
    
    # 打印对话摘要
    if "dialogues" in content and content["dialogues"]:
        print(f"- 对话数量: {len(content['dialogues'])}")
        print(f"  对话1: {content['dialogues'][0].get('text', '无内容')}")

def demonstrate_generation_bridge():
    """演示代际差异桥接器功能"""
    print_section("代际差异桥接器演示")
    
    # 获取桥接器实例
    print("正在获取代际差异桥接器...")
    try:
        bridge = get_generation_bridge()
        print("成功获取代际差异桥接器")
    except Exception as e:
        print(f"获取代际差异桥接器时发生错误: {str(e)}")
        traceback.print_exc()
        return
    
    # 演示1：生成不同代际风格的内容
    print_section("1. 不同代际风格内容")
    
    print("\n生成不同代际风格的内容...")
    z_gen_content = generate_sample_content("Z世代")
    gen90_content = generate_sample_content("90后")
    gen80_content = generate_sample_content("80后")
    gen70_content = generate_sample_content("70后")
    
    print("\nZ世代内容:")
    print_content_summary(z_gen_content, "Z世代内容")
    
    print("\n90后内容:")
    print_content_summary(gen90_content, "90后内容")
    
    print("\n80后内容:")
    print_content_summary(gen80_content, "80后内容")
    
    print("\n70后内容:")
    print_content_summary(gen70_content, "70后内容")
    
    # 演示2：检测内容的代际倾向
    print_section("2. 检测内容代际倾向")
    
    print("\n检测不同内容的代际倾向...")
    for content_name, content in [
        ("Z世代内容", z_gen_content),
        ("90后内容", gen90_content),
        ("80后内容", gen80_content),
        ("70后内容", gen70_content)
    ]:
        detected = detect_content_generation(content)
        print(f"- {content_name}的检测结果: {detected}")
    
    # 演示3：跨代际内容转换
    print_section("3. 跨代际内容转换")
    
    print("\n将不同代际内容转换为其他代际风格...")
    
    # Z世代 -> 80后
    print("\nZ世代 -> 80后 转换:")
    z_to_80 = bridge_gap(z_gen_content, "80后")
    print_content_summary(z_gen_content, "原始Z世代内容")
    print_content_summary(z_to_80, "转换后内容(80后风格)")
    
    # 80后 -> Z世代
    print("\n80后 -> Z世代 转换:")
    gen80_to_z = bridge_gap(gen80_content, "Z世代")
    print_content_summary(gen80_content, "原始80后内容")
    print_content_summary(gen80_to_z, "转换后内容(Z世代风格)")
    
    # 90后 -> 70后
    print("\n90后 -> 70后 转换:")
    gen90_to_70 = bridge_gap(gen90_content, "70后")
    print_content_summary(gen90_content, "原始90后内容")
    print_content_summary(gen90_to_70, "转换后内容(70后风格)")
    
    # 演示4：插入文化元素
    print_section("4. 文化元素插入")
    
    print("\n向内容中添加特定世代的文化元素...")
    
    # 创建通用内容
    generic_content = {
        "title": "动画角色分析",
        "description": "探讨几个经典动画角色的特点",
        "scenes": [
            {
                "id": "scene_1",
                "description": "展示不同角色类型",
                "elements": [
                    {"type": "text", "content": "这些角色各有不同的设计理念"},
                    {"type": "image", "source": "characters.png"}
                ]
            }
        ],
        "dialogues": [
            {"speaker": "narrator", "text": "动画角色的设计反映了时代特征"},
            {"speaker": "presenter", "text": "不同时期的角色有不同的表现手法"}
        ]
    }
    
    # 向通用内容中插入Z世代文化元素
    z_gen_elements = ["二次元", "玩梗", "yyds", "整片化"]
    z_enhanced = insert_cultural_elements(generic_content, z_gen_elements)
    print_content_summary(generic_content, "原始通用内容")
    print_content_summary(z_enhanced, "添加Z世代元素后")
    
    # 向通用内容中插入80后文化元素
    gen80_elements = ["怀旧", "童年", "港台文化", "经典款"]
    gen80_enhanced = insert_cultural_elements(generic_content, gen80_elements)
    print_content_summary(gen80_enhanced, "添加80后元素后")
    
    # 演示5：代际风格应用
    print_section("5. 代际风格应用")
    
    # 测试文本样本
    test_text = "我认为这些角色设计很好，展现了丰富的故事性和人物特点，值得观众深入欣赏。"
    
    print(f"\n原始文本: {test_text}")
    
    # 应用Z世代风格
    z_styled = bridge._apply_z_generation_style(test_text)
    print(f"Z世代风格: {z_styled}")
    
    # 应用80后风格
    gen80_styled = bridge._apply_80s_style(test_text)
    print(f"80后风格: {gen80_styled}")
    
    # 应用90后风格
    gen90_styled = bridge._apply_90s_style(test_text)
    print(f"90后风格: {gen90_styled}")
    
    print("\n演示完成！")

if __name__ == "__main__":
    try:
        demonstrate_generation_bridge()
    except Exception as e:
        print(f"演示过程中发生错误: {str(e)}")
        traceback.print_exc() 