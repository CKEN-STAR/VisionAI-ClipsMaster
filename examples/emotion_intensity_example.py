#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
情感强度图谱构建模块应用示例

展示如何在实际项目中使用情感强度图谱构建模块分析字幕/剧本的情感曲线。
"""

import os
import sys
import json
import argparse
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.emotion.intensity_mapper import EmotionMapper
from src.emotion.visualizer import visualize_intensity_curve
from src.nlp.sentiment_analyzer import analyze_text
from src.utils.logger import setup_logger

# 设置日志
logger = setup_logger()

def load_subtitle_file(file_path: str):
    """加载SRT字幕文件为场景列表"""
    import re
    from datetime import datetime

    if not os.path.exists(file_path):
        logger.error(f"字幕文件不存在: {file_path}")
        return []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 分割字幕块
    subtitle_blocks = re.split(r'\n\n+', content.strip())
    
    scenes = []
    for block in subtitle_blocks:
        lines = block.strip().split('\n')
        if len(lines) < 3:
            continue
        
        # 提取时间码
        time_line = lines[1]
        time_match = re.match(r'(\\\1{2}:\\\1{2}:\\\1{2},\\\1{3}) --> (\\\1{2}:\\\1{2}:\\\1{2},\\\1{3})', time_line)
        if not time_match:
            continue
        
        start_time, end_time = time_match.groups()
        
        # 提取文本内容
        text = " ".join(lines[2:])
        
        # 分析情感
        sentiment = analyze_text(text)
        
        # 创建场景
        scene = {
            "id": len(scenes) + 1,
            "start": start_time,
            "end": end_time,
            "text": text,
            "emotion": {
                "type": sentiment.get("sentiment", "neutral").lower(),
                "description": sentiment.get("sentiment", "neutral"),
                "score": sentiment.get("intensity", 0.5)
            }
        }
        
        scenes.append(scene)
    
    return scenes

def analyze_script(script_data, output_dir="reports/emotion_analysis"):
    """分析剧本情感曲线"""
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 保存输入脚本
    input_path = os.path.join(output_dir, "input_script.json")
    with open(input_path, 'w', encoding='utf-8') as f:
        json.dump(script_data, f, ensure_ascii=False, indent=2)
    logger.info(f"输入脚本已保存至: {input_path}")
    
    # 初始化情感强度映射器
    mapper = EmotionMapper()
    
    # 构建情感强度曲线
    logger.info("构建情感强度曲线...")
    curve_data = mapper.build_intensity_curve(script_data)
    
    # 保存曲线数据
    curve_path = os.path.join(output_dir, "emotion_curve.json")
    with open(curve_path, 'w', encoding='utf-8') as f:
        json.dump(curve_data, f, ensure_ascii=False, indent=2)
    logger.info(f"情感曲线数据已保存至: {curve_path}")
    
    # 分析情感质量
    flow_analysis = mapper.analyze_emotion_flow(curve_data)
    
    # 输出分析结果
    logger.info(f"情感流程质量分析结果:")
    logger.info(f"  质量评分: {flow_analysis['quality']:.2f}/1.0")
    logger.info(f"  情感范围: {flow_analysis['emotion_range']:.2f}")
    logger.info(f"  转折点数量: {flow_analysis['turning_points']}")
    logger.info(f"  存在明显高潮: {'是' if flow_analysis['has_climax'] else '否'}")
    
    if flow_analysis['issues']:
        logger.info("检测到的问题:")
        for issue in flow_analysis['issues']:
            logger.info(f"  - {issue}")
            
    # 保存分析结果
    analysis_path = os.path.join(output_dir, "flow_analysis.json")
    with open(analysis_path, 'w', encoding='utf-8') as f:
        json.dump(flow_analysis, f, ensure_ascii=False, indent=2)
        
    # 可视化曲线
    logger.info("生成情感曲线可视化...")
    visualize_intensity_curve(curve_data, output_dir=output_dir)
    
    logger.info(f"情感分析完成，所有结果已保存至: {output_dir}")
    
    # 提取关键情感点
    peaks = [p for p in curve_data if p.get("is_peak", False)]
    valleys = [p for p in curve_data if p.get("is_valley", False)]
    climax = next((p for p in curve_data if p.get("is_global_peak", False)), None)
    
    # 输出关键点信息
    if peaks:
        logger.info(f"情感峰值数量: {len(peaks)}")
        for i, peak in enumerate(peaks):
            logger.info(f"  峰值 {i+1}: 位置={peak.get('scene_id', '?')}, 强度={peak['peak_value']:.2f}")
            
    if climax:
        logger.info(f"情感高潮: 位置={climax.get('scene_id', '?')}, 强度={climax['peak_value']:.2f}")
        logger.info(f"  文本: {climax['raw_text'][:50]}..." if len(climax['raw_text']) > 50 else climax['raw_text'])
    
    return {
        "curve_data": curve_data,
        "analysis": flow_analysis,
        "peaks": peaks,
        "valleys": valleys,
        "climax": climax
    }

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='情感强度图谱分析示例')
    parser.add_argument('--subtitle', type=str, help='SRT字幕文件路径')
    parser.add_argument('--script', type=str, help='JSON剧本文件路径')
    parser.add_argument('--output-dir', type=str, default='reports/emotion_analysis', help='输出目录')
    
    args = parser.parse_args()
    
    if not args.subtitle and not args.script:
        logger.error("请提供--subtitle或--script参数指定输入文件")
        return
    
    if args.subtitle:
        logger.info(f"加载字幕文件: {args.subtitle}")
        script_data = load_subtitle_file(args.subtitle)
        if not script_data:
            logger.error("字幕文件解析失败")
            return
    else:
        logger.info(f"加载剧本文件: {args.script}")
        try:
            with open(args.script, 'r', encoding='utf-8') as f:
                script_data = json.load(f)
        except Exception as e:
            logger.error(f"剧本文件读取失败: {e}")
            return
            
    if not script_data:
        logger.error("剧本数据为空")
        return
        
    logger.info(f"成功加载剧本数据，共 {len(script_data)} 个场景")
    
    # 分析剧本
    result = analyze_script(script_data, output_dir=args.output_dir)
    
    # 根据情感分析结果，生成剧本优化建议
    logger.info("生成情感曲线优化建议:")
    
    if result["analysis"]["quality"] < 0.4:
        logger.info("  - 剧本情感曲线质量较低，建议重新设计情感起伏")
        
    if result["analysis"]["emotion_range"] < 0.3:
        logger.info("  - 情感变化范围小，建议加入更丰富的情感转变")
        
    if not result["analysis"]["has_climax"]:
        logger.info("  - 缺乏情感高潮，建议增加明显的高潮场景")
        
    if result["analysis"]["turning_points"] < 3 and len(script_data) > 10:
        logger.info("  - 情感转折点不足，建议增加情感起伏以提高观众参与感")
        
    logger.info("情感分析示例完成")

if __name__ == "__main__":
    main() 