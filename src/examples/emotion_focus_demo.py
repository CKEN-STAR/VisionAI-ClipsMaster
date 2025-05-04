#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
情感焦点定位器演示

展示如何使用情感焦点定位器识别和定位文本/剧本中的情感焦点。
包括基本定位、上下文提取和可视化功能。
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

# 导入情感焦点定位器
from src.emotion.focus_locator import EmotionFocusLocator, locate_emotional_cores, find_emotion_focus_ranges
from src.utils.sample_data import generate_sample_script
from src.nlp.text_processor import process_text

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def highlight_focus_in_text(text: str, focus_ranges: List[Dict[str, Any]], 
                           use_color: bool = True) -> str:
    """
    在文本中高亮显示情感焦点
    
    Args:
        text: 原始文本
        focus_ranges: 情感焦点范围列表
        use_color: 是否使用颜色高亮（终端支持ANSI颜色时）
        
    Returns:
        高亮后的文本
    """
    if not text or not focus_ranges:
        return text
    
    # 按开始位置排序
    sorted_ranges = sorted(focus_ranges, key=lambda x: x["start"])
    
    # 准备高亮标记
    if use_color:
        # ANSI颜色代码
        highlight_start = "\033[91m"  # 红色
        highlight_end = "\033[0m"     # 重置
    else:
        # 普通标记
        highlight_start = "【"
        highlight_end = "】"
    
    # 构建高亮文本
    result = ""
    last_end = 0
    
    for focus in sorted_ranges:
        start = focus["start"]
        end = focus["end"]
        
        # 添加前面未修改的部分
        if start > last_end:
            result += text[last_end:start]
        
        # 添加高亮部分
        result += highlight_start + text[start:end] + highlight_end
        
        last_end = end
    
    # 添加最后剩余部分
    if last_end < len(text):
        result += text[last_end:]
    
    return result

def save_focus_results(focus_ranges: List[Dict[str, Any]], output_file: str):
    """
    保存情感焦点结果为JSON格式
    
    Args:
        focus_ranges: 情感焦点范围列表
        output_file: 输出文件路径
    """
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(focus_ranges, f, ensure_ascii=False, indent=2)
        logger.info(f"情感焦点结果已保存至: {output_file}")
    except Exception as e:
        logger.error(f"保存结果失败: {e}")

def process_scene(scene_text: str, show_highlight: bool = True):
    """
    处理单个场景的情感焦点
    
    Args:
        scene_text: 场景文本
        show_highlight: 是否显示高亮文本
    """
    # 初始化定位器
    locator = EmotionFocusLocator()
    
    # 获取情感焦点
    focus_ranges = locator.find_emotion_focus_ranges(scene_text)
    
    # 打印结果
    logger.info(f"检测到 {len(focus_ranges)} 个情感焦点")
    
    # 如果需要显示高亮
    if show_highlight and focus_ranges:
        highlighted = highlight_focus_in_text(scene_text, focus_ranges)
        logger.info("高亮显示结果:")
        print("\n" + highlighted + "\n")
    
    # 输出详细结果
    for i, focus in enumerate(focus_ranges):
        logger.info(f"焦点 {i+1}:")
        logger.info(f"  位置: {focus['start']}-{focus['end']}")
        logger.info(f"  情感得分: {focus['emotion_score']:.2f}")
        logger.info(f"  焦点文本: {focus['focus_text']}")
    
    return focus_ranges

def analyze_script(script_data: List[Dict[str, Any]], output_dir: str):
    """
    分析剧本的情感焦点
    
    Args:
        script_data: 剧本数据
        output_dir: 输出目录
    """
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 初始化定位器
    locator = EmotionFocusLocator()
    
    results = []
    all_focus_points = []
    
    # 处理每个场景
    for i, scene in enumerate(script_data):
        scene_text = scene.get("text", "")
        if not scene_text:
            continue
            
        logger.info(f"正在处理场景 {i+1}/{len(script_data)}")
        
        # 分析场景情感焦点
        scene_with_focus = locator.analyze_scene_emotion_focus(scene)
        
        # 收集结果
        results.append(scene_with_focus)
        
        # 收集焦点数据
        focus_ranges = scene_with_focus.get("emotion_focus", {}).get("ranges", [])
        for focus in focus_ranges:
            focus_info = {
                "scene_id": scene.get("id", f"scene_{i+1}"),
                "start_time": scene.get("start", ""),
                "end_time": scene.get("end", ""),
                "focus_text": focus.get("focus_text", ""),
                "emotion_score": focus.get("emotion_score", 0),
                "context_text": focus.get("context_text", "")
            }
            all_focus_points.append(focus_info)
    
    # 保存处理后的完整剧本
    script_output = os.path.join(output_dir, "script_with_focus.json")
    with open(script_output, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    logger.info(f"带情感焦点的剧本已保存至: {script_output}")
    
    # 保存提取的焦点数据
    focus_output = os.path.join(output_dir, "emotion_focus_points.json")
    with open(focus_output, 'w', encoding='utf-8') as f:
        json.dump(all_focus_points, f, ensure_ascii=False, indent=2)
    logger.info(f"情感焦点数据已保存至: {focus_output}")
    
    # 分析结果统计
    focus_count = len(all_focus_points)
    avg_score = sum(f["emotion_score"] for f in all_focus_points) / max(1, focus_count)
    
    logger.info("情感焦点分析统计:")
    logger.info(f"  总场景数: {len(script_data)}")
    logger.info(f"  总焦点数: {focus_count}")
    logger.info(f"  平均情感得分: {avg_score:.2f}")
    logger.info(f"  每场景平均焦点数: {focus_count/max(1, len(script_data)):.2f}")
    
    return results, all_focus_points

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='情感焦点定位器演示')
    parser.add_argument('--text', type=str, help='待分析的文本')
    parser.add_argument('--script', type=str, help='剧本文件路径')
    parser.add_argument('--sample', action='store_true', help='使用示例剧本')
    parser.add_argument('--output-dir', type=str, default='reports/emotion_focus',
                      help='输出目录')
    parser.add_argument('--scene-count', type=int, default=5,
                      help='示例剧本场景数量')
    parser.add_argument('--script-type', type=str, default='emotional',
                      choices=['standard', 'emotional', 'flat', 'rollercoaster'],
                      help='示例剧本类型')
    
    args = parser.parse_args()
    
    # 确保输出目录存在
    os.makedirs(args.output_dir, exist_ok=True)
    
    # 判断输入方式
    if args.text:
        # 处理单个文本
        logger.info("处理输入文本:")
        focus_ranges = process_scene(args.text)
        
        # 保存结果
        output_file = os.path.join(args.output_dir, "text_focus_result.json")
        save_focus_results(focus_ranges, output_file)
        
    elif args.script:
        # 处理脚本文件
        logger.info(f"处理脚本文件: {args.script}")
        try:
            with open(args.script, 'r', encoding='utf-8') as f:
                script_data = json.load(f)
            analyze_script(script_data, args.output_dir)
        except Exception as e:
            logger.error(f"读取脚本文件失败: {e}")
    
    elif args.sample:
        # 使用示例剧本
        logger.info(f"生成{args.script_type}类型的示例剧本，包含{args.scene_count}个场景")
        sample_script = generate_sample_script(
            scene_count=args.scene_count,
            script_type=args.script_type
        )
        
        # 保存示例剧本
        sample_path = os.path.join(args.output_dir, 'sample_script.json')
        with open(sample_path, 'w', encoding='utf-8') as f:
            json.dump(sample_script, f, ensure_ascii=False, indent=2)
        logger.info(f"示例剧本已保存至: {sample_path}")
        
        # 分析剧本
        analyze_script(sample_script, args.output_dir)
    
    else:
        # 无输入时使用默认示例文本
        example_text = """
        李明站在小区门口，手里拿着一束鲜花，不时地看看手表。他有些紧张，额头上有细密的汗珠。
        
        "小雨，你可千万要来啊！"他低声自语道。
        
        这时，小雨匆匆跑来，脸上带着歉意的笑容。"对不起！对不起！我迟到了，路上太堵了！"
        
        李明瞬间绽放出灿烂的笑容，快步迎上前去。"没关系，我刚到没多久。"他轻声说着，将花束递给她，"这是送给你的。"
        
        小雨接过花束，惊喜地瞪大眼睛："哇！好漂亮的花！谢谢你李明！"她开心地抱了抱花束，然后两人相视而笑。
        """
        
        logger.info("使用示例文本进行演示:")
        focus_ranges = process_scene(example_text)
        
        # 保存结果
        output_file = os.path.join(args.output_dir, "example_focus_result.json")
        save_focus_results(focus_ranges, output_file)
    
    logger.info("情感焦点定位演示完成")

if __name__ == "__main__":
    main() 