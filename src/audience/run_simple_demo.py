#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
代际差异桥接器最小化演示脚本
可独立运行，不依赖其他模块
"""

import sys
import os
import traceback

# 设置路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../..'))
sys.path.insert(0, project_root)

# 创建必要的模拟对象
class MockClass:
    def __init__(self, *args, **kwargs):
        pass
    
    def __getattr__(self, name):
        return lambda *args, **kwargs: None

class MockLogger:
    def info(self, msg):
        print(f"[INFO] {msg}")
    
    def debug(self, msg):
        pass
    
    def warning(self, msg):
        print(f"[WARNING] {msg}")
    
    def error(self, msg):
        print(f"[ERROR] {msg}")

# 模拟包
for module_name in [
    'src.data.storage_manager',
    'src.utils.log_handler',
    'src.utils.privacy_manager',
    'src.core.privacy_manager',
    'src.nlp.text_processor',
    'src.nlp.language_detector',
    'src.emotion.intensity_mapper',
    'src.adaptation.culture_adapter'
]:
    sys.modules[module_name] = MockClass()

# 设置必要的函数和类
sys.modules['src.utils.log_handler'].get_logger = lambda name: MockLogger()
sys.modules['src.nlp.text_processor'].TextProcessor = MockClass
sys.modules['src.adaptation.culture_adapter'].CultureAdapter = MockClass

def run_demo():
    """运行简化版演示"""
    try:
        # 导入模块
        print("正在导入代际差异桥接器...")
        from src.audience.generation_gap import (
            GenerationBridge, 
            get_generation_bridge,
            bridge_gap, 
            detect_content_generation
        )
        print("✓ 成功导入模块")
        
        # 示例内容
        z_gen_content = {
            "title": "二次元动漫角色大盘点",
            "description": "这些角色简直绝绝子，太可了，我直接笑死！",
            "dialogues": [
                {"speaker": "narrator", "text": "这些梗真是太香了，yyds！"}
            ]
        }
        
        gen80_content = {
            "title": "怀旧经典动画角色回顾",
            "description": "这些角色陪伴了我们的童年，满满的回忆",
            "dialogues": [
                {"speaker": "narrator", "text": "这些经典角色真是满满的回忆啊"}
            ]
        }
        
        # 测试检测
        print("\n测试代际检测:")
        z_detected = detect_content_generation(z_gen_content)
        print(f"Z世代内容检测结果: {z_detected}")
        
        gen80_detected = detect_content_generation(gen80_content)
        print(f"80后内容检测结果: {gen80_detected}")
        
        # 测试转换
        print("\n测试代际转换:")
        z_to_80 = bridge_gap(z_gen_content, "80后")
        print(f"Z世代 -> 80后:")
        print(f"原始标题: {z_gen_content['title']}")
        print(f"转换后标题: {z_to_80['title']}")
        print(f"原始描述: {z_gen_content['description']}")
        print(f"转换后描述: {z_to_80['description']}")
        
        gen80_to_z = bridge_gap(gen80_content, "Z世代")
        print(f"\n80后 -> Z世代:")
        print(f"原始标题: {gen80_content['title']}")
        print(f"转换后标题: {gen80_to_z['title']}")
        print(f"原始描述: {gen80_content['description']}")
        print(f"转换后描述: {gen80_to_z['description']}")
        
        print("\n演示完成!")
    
    except Exception as e:
        print(f"演示出错: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    print("=" * 50)
    print("代际差异桥接器简化演示")
    print("=" * 50)
    run_demo() 