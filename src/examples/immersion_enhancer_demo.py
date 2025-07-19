#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
沉浸感增强器演示脚本

演示如何使用沉浸感增强模块为视频内容添加沉浸体验增强效果。
"""

import os
import sys
import json
import logging
import argparse
from pprint import pprint
from typing import Dict, List, Any, Optional

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

# 导入沉浸感增强模块
from src.immersion.enhancer import (
    enhance_immersion, 
    apply_immersion_template,
    suggest_immersion_enhancements,
    get_enhancer
)

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("immersion_demo")

def create_sample_script() -> List[Dict[str, Any]]:
    """创建示例脚本数据"""
    return [
        {
            "text": "我们回到了两年前，那是一个平静的下午。",
            "time": {"start": 0.0, "end": 3.5},
            "tags": ["flashback", "opening"],
            "sentiment": {"label": "NEUTRAL", "intensity": 0.3},
            "bgm": "平静的钢琴曲"
        },
        {
            "text": "小明：这次考试我一定要考好！",
            "time": {"start": 3.5, "end": 6.0},
            "tags": ["dialogue"],
            "sentiment": {"label": "POSITIVE", "intensity": 0.65},
            "bgm": "平静的钢琴曲"
        },
        {
            "text": "突然，一阵急促的电话铃声打破了宁静。",
            "time": {"start": 6.0, "end": 9.0},
            "tags": ["transition"],
            "sentiment": {"label": "SURPRISE", "intensity": 0.7},
            "bgm": "紧张的弦乐"
        },
        {
            "text": "小明：什么？出事了？！",
            "time": {"start": 9.0, "end": 11.0},
            "tags": ["dialogue", "emotional"],
            "sentiment": {"label": "NEGATIVE", "intensity": 0.8},
            "bgm": "紧张的弦乐"
        },
        {
            "text": "小红：别担心，我们一起想办法。",
            "time": {"start": 11.0, "end": 14.0},
            "tags": ["dialogue", "support"],
            "sentiment": {"label": "POSITIVE", "intensity": 0.6},
            "bgm": "安慰的吉他声"
        },
        {
            "text": "两人一路狂奔，穿过繁忙的街道。",
            "time": {"start": 14.0, "end": 17.5},
            "tags": ["action"],
            "sentiment": {"label": "NEUTRAL", "intensity": 0.5},
            "bgm": "急促的打击乐"
        },
        {
            "text": "夜晚，月光照在湖面上，波光粼粼。",
            "time": {"start": 17.5, "end": 21.0},
            "tags": ["scene_setting", "peaceful"],
            "sentiment": {"label": "POSITIVE", "intensity": 0.4},
            "bgm": "舒缓的自然音"
        },
        {
            "text": "小明梦见自己站在高山之巅，鸟儿在天空飞翔。",
            "time": {"start": 21.0, "end": 25.0},
            "tags": ["dream"],
            "sentiment": {"label": "POSITIVE", "intensity": 0.7},
            "bgm": "梦幻音乐"
        }
    ]

def visualize_enhanced_script(script: List[Dict[str, Any]]) -> None:
    """可视化增强后的脚本"""
    print("\n" + "="*70)
    print(" "*25 + "增强后的脚本")
    print("="*70)
    
    for i, scene in enumerate(script):
        print(f"\n[场景 {i+1}] {scene.get('time', {}).get('start', 0):.1f}s - "
              f"{scene.get('time', {}).get('end', 0):.1f}s")
        print("-"*70)
        
        # 内容和标签
        print(f"内容: {scene.get('text', '')}")
        if 'tags' in scene:
            print(f"标签: {', '.join(scene.get('tags', []))}")
            
        # 情感信息
        if 'sentiment' in scene:
            sentiment = scene['sentiment']
            print(f"情感: {sentiment.get('label', 'NEUTRAL')} "
                  f"(强度: {sentiment.get('intensity', 0):.2f})")
        
        # 背景音乐
        if 'bgm' in scene:
            print(f"背景音乐: {scene['bgm']}")
            
        # 视觉效果
        if 'visual_effects' in scene:
            print(f"视觉效果: {', '.join(scene['visual_effects'])}")
            
        # 音频效果
        if 'audio_effects' in scene:
            print(f"音频效果: {', '.join(scene['audio_effects'])}")
            
        # 转场效果
        if 'transition' in scene:
            print(f"转场效果: {scene['transition'].get('type', '')}")
            
        # 反应镜头
        if 'reaction_shot' in scene:
            reaction = scene['reaction_shot']
            print(f"反应镜头: {reaction.get('character', '')} ({reaction.get('emotion', '')})")
    
    print("\n" + "="*70)

def demonstrate_templates(script: List[Dict[str, Any]]) -> None:
    """演示不同模板效果"""
    enhancer = get_enhancer()
    templates = enhancer.templates.keys()
    
    print("\n" + "="*70)
    print(" "*20 + "不同沉浸感模板效果对比")
    print("="*70)
    
    for template_name in templates:
        print(f"\n模板: {template_name}")
        print("-"*40)
        
        # 应用模板
        template_script = apply_immersion_template(script[:2], template_name)
        
        # 显示模板效果
        for scene in template_script:
            visual = scene.get('visual_effects', [])
            audio = scene.get('audio_effects', [])
            
            print(f"视觉效果: {', '.join(visual)}")
            print(f"音频效果: {', '.join(audio)}")
        print()

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="沉浸感增强器演示")
    parser.add_argument("--template", type=str, help="使用的模板名称")
    parser.add_argument("--visualize", action="store_true", help="可视化增强效果")
    parser.add_argument("--compare-templates", action="store_true", help="比较不同模板效果")
    parser.add_argument("--scene-type", type=str, help="获取特定场景类型的增强建议")
    args = parser.parse_args()
    
    # 创建示例脚本
    script = create_sample_script()
    
    # 获取特定场景类型的增强建议
    if args.scene_type:
        suggestions = suggest_immersion_enhancements(args.scene_type)
        print(f"\n{args.scene_type}场景类型的沉浸感增强建议:")
        pprint(suggestions)
        return
    
    # 使用模板
    if args.template:
        enhanced_script = apply_immersion_template(script, args.template)
        print(f"\n已应用{args.template}模板")
    else:
        # 默认增强
        enhanced_script = enhance_immersion(script)
        print("\n已使用默认设置增强脚本")
    
    # 比较不同模板
    if args.compare_templates:
        demonstrate_templates(script)
    
    # 可视化
    if args.visualize:
        visualize_enhanced_script(enhanced_script)
    
if __name__ == "__main__":
    main() 