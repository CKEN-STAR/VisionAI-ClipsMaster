#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
情感词汇强化器演示

展示如何使用情感词汇强化器对文本的情感表达进行增强或减弱。
包括基本强化、减弱、目标级别调整和自定义模式等功能。
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# 导入情感词汇强化器
from src.emotion.lexicon_enhancer import EmotionLexicon, intensify_text, reduce_emotion, adjust_emotion_level
from src.utils.sample_data import generate_sample_script
from src.nlp.text_processor import process_text

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def show_comparison(original: str, modified: str, operation: str = "强化"):
    """显示文本修改前后的对比"""
    logger.info(f"原始文本: {original}")
    logger.info(f"{operation}后: {modified}")
    logger.info("-" * 50)

def demo_basic_operations():
    """演示基本的情感词汇强化操作"""
    logger.info("=== 基本情感词汇强化演示 ===")
    
    # 实例化强化器
    enhancer = EmotionLexicon()
    
    # 示例文本
    texts = [
        "李明感到很高兴，因为他终于完成了这个项目。",
        "小红生气地看着摔碎的花瓶，这是妈妈最喜欢的礼物。",
        "张华听到这个消息后非常难过，眼泪都快流出来了。",
        "我很喜欢这部电影，演员的表演太好了。"
    ]
    
    # 1. 情感增强
    logger.info("\n*** 情感增强示例 ***")
    for text in texts:
        intensified = enhancer.intensify(text)
        show_comparison(text, intensified, "增强")
    
    # 2. 情感减弱
    logger.info("\n*** 情感减弱示例 ***")
    for text in texts:
        reduced = enhancer.reduce(text)
        show_comparison(text, reduced, "减弱")
    
    # 3. 情感调整到特定级别
    logger.info("\n*** 情感调整到特定级别示例 ***")
    target_levels = [0.3, 0.5, 0.9]
    
    for text in texts[:2]:  # 只用前两个示例
        for level in target_levels:
            adjusted = enhancer.adjust_to_level(text, level)
            show_comparison(text, adjusted, f"调整到级别{level}")

def demo_custom_modes():
    """演示自定义情感强化模式"""
    logger.info("\n=== 自定义情感强化模式演示 ===")
    
    # 实例化强化器
    enhancer = EmotionLexicon()
    
    # 示例文本
    text = "导演看到最终的电影剪辑后很满意，他认为这是一部好电影，演员的表演很棒。"
    
    logger.info(f"原始文本: {text}")
    
    # 自定义配置，模拟不同场景下的情感强化需求
    modes = {
        "温和增强": {"intensify_factor": 1.2, "max_replacements": 2},
        "标准增强": {"intensify_factor": 1.3, "max_replacements": 3},
        "强烈增强": {"intensify_factor": 1.5, "max_replacements": 4},
        "夸张增强": {"intensify_factor": 1.8, "max_replacements": 6}
    }
    
    # 应用不同模式进行增强
    for mode_name, params in modes.items():
        # 创建临时配置
        config = {
            "lexicon_enhancer": {
                "intensify_factor": params["intensify_factor"],
                "max_replacements": params["max_replacements"]
            }
        }
        
        # 应用自定义配置的增强
        modified = enhancer.intensify(text, params["intensify_factor"])
        logger.info(f"{mode_name}: {modified}")
    
    logger.info("-" * 50)

def process_script(script_data: List[Dict[str, Any]], output_dir: str):
    """
    处理剧本，应用情感词汇强化
    
    Args:
        script_data: 剧本数据
        output_dir: 输出目录
    """
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 初始化强化器
    enhancer = EmotionLexicon()
    
    # 处理结果
    original_script = []
    enhanced_script = []
    reduced_script = []
    
    # 处理每个场景
    for i, scene in enumerate(script_data):
        scene_text = scene.get("text", "")
        if not scene_text:
            continue
            
        logger.info(f"正在处理场景 {i+1}/{len(script_data)}")
        
        # 保存原始文本
        original_scene = scene.copy()
        original_script.append(original_scene)
        
        # 增强版本
        enhanced_scene = scene.copy()
        enhanced_scene["text"] = enhancer.intensify(scene_text)
        enhanced_script.append(enhanced_scene)
        
        # 减弱版本
        reduced_scene = scene.copy()
        reduced_scene["text"] = enhancer.reduce(scene_text)
        reduced_script.append(reduced_scene)
    
    # 保存处理结果
    results = {
        "original": original_script,
        "enhanced": enhanced_script,
        "reduced": reduced_script
    }
    
    # 保存到文件
    output_file = os.path.join(output_dir, "emotion_lexicon_results.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    logger.info(f"处理结果已保存至: {output_file}")
    
    return results

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='情感词汇强化器演示')
    parser.add_argument('--text', type=str, help='待处理的文本')
    parser.add_argument('--factor', type=float, default=1.3, help='情感强化因子')
    parser.add_argument('--mode', type=str, default='intensify',
                      choices=['intensify', 'reduce', 'adjust'],
                      help='处理模式: intensify(增强), reduce(减弱), adjust(调整)')
    parser.add_argument('--target-level', type=float, default=0.8, help='情感目标级别(0.0-1.0)')
    parser.add_argument('--script', type=str, help='剧本文件路径')
    parser.add_argument('--sample', action='store_true', help='使用示例剧本')
    parser.add_argument('--output-dir', type=str, default='reports/emotion_lexicon',
                      help='输出目录')
    parser.add_argument('--demo', action='store_true', help='运行完整演示')
    
    args = parser.parse_args()
    
    # 确保输出目录存在
    os.makedirs(args.output_dir, exist_ok=True)
    
    # 运行完整演示
    if args.demo:
        demo_basic_operations()
        demo_custom_modes()
        return
    
    # 处理单个文本
    if args.text:
        logger.info("处理输入文本:")
        enhancer = EmotionLexicon()
        
        original_text = args.text
        logger.info(f"原始文本: {original_text}")
        
        if args.mode == 'intensify':
            processed = enhancer.intensify(original_text, args.factor)
            logger.info(f"增强文本 (因子 {args.factor}): {processed}")
            
        elif args.mode == 'reduce':
            processed = enhancer.reduce(original_text, args.factor)
            logger.info(f"减弱文本 (因子 {args.factor}): {processed}")
            
        elif args.mode == 'adjust':
            processed = enhancer.adjust_to_level(original_text, args.target_level)
            logger.info(f"调整文本 (目标级别 {args.target_level}): {processed}")
    
    # 处理剧本文件
    elif args.script:
        logger.info(f"处理剧本文件: {args.script}")
        try:
            with open(args.script, 'r', encoding='utf-8') as f:
                script_data = json.load(f)
            process_script(script_data, args.output_dir)
        except Exception as e:
            logger.error(f"读取剧本文件失败: {e}")
    
    # 使用示例剧本
    elif args.sample:
        logger.info("生成并处理示例剧本")
        sample_script = generate_sample_script(
            scene_count=5,
            script_type='emotional'
        )
        
        # 保存示例剧本
        sample_path = os.path.join(args.output_dir, 'sample_script.json')
        with open(sample_path, 'w', encoding='utf-8') as f:
            json.dump(sample_script, f, ensure_ascii=False, indent=2)
        logger.info(f"示例剧本已保存至: {sample_path}")
        
        # 处理剧本
        process_script(sample_script, args.output_dir)
    
    # 无参数时运行简单演示
    else:
        logger.info("无参数提供，运行简单演示")
        demo_text = "李明感到很高兴，因为他终于完成了这个项目。小红生气地看着摔碎的花瓶，这是妈妈最喜欢的礼物。"
        
        # 强化示例
        intensified = intensify_text(demo_text)
        logger.info("情感强化示例:")
        logger.info(f"原始: {demo_text}")
        logger.info(f"强化: {intensified}")
        
        # 减弱示例
        reduced = reduce_emotion(demo_text)
        logger.info("\n情感减弱示例:")
        logger.info(f"原始: {demo_text}")
        logger.info(f"减弱: {reduced}")
        
        # 调整到特定级别示例
        adjusted = adjust_emotion_level(demo_text, 0.9)
        logger.info("\n情感级别调整示例:")
        logger.info(f"原始: {demo_text}")
        logger.info(f"调整到0.9: {adjusted}")
    
    logger.info("情感词汇强化器演示完成")

if __name__ == "__main__":
    main() 