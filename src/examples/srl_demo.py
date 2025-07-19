#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
语义角色标注演示脚本
展示如何在短剧分析中使用SRL系统提取事件和角色关系
"""

import sys
import os
import logging
import json
import time
from typing import List, Dict, Any

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(project_root)

# 导入相关模块
from src.nlp.srl_annotator import annotate_text, annotate_subtitles, extract_events
from src.nlp.sentiment_analyzer import analyze_sentiment
from src.utils.log_handler import get_logger

# 设置日志
logger = get_logger("srl_demo")

def load_sample_subtitles(file_path: str = None) -> List[Dict[str, Any]]:
    """
    加载示例字幕文件或使用内置示例
    
    参数:
        file_path: 字幕文件路径(可选)
        
    返回:
        字幕列表
    """
    if file_path and os.path.exists(file_path):
        # 读取SRT或JSON格式的字幕文件
        if file_path.endswith('.json'):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # 这里应该添加SRT解析代码，当前使用内置示例代替
            logger.warning(f"不支持的字幕文件格式: {file_path}")
    
    # 使用内置示例
    logger.info("使用内置字幕示例")
    return [
        {
            "text": "小明走进教室，发现小红正在读书。",
            "time": {"start": 0.0, "end": 3.5}
        },
        {
            "text": "他微笑着向她打招呼。",
            "time": {"start": 3.6, "end": 5.0}
        },
        {
            "text": "小红抬起头，开心地回应了他。",
            "time": {"start": 5.1, "end": 7.5}
        },
        {
            "text": "老师拿着试卷走进教室，对同学们说道：",
            "time": {"start": 7.6, "end": 10.0}
        },
        {
            "text": "今天我们要讨论上次考试的结果。",
            "time": {"start": 10.1, "end": 13.0}
        },
        {
            "text": "小明紧张地看了看小红，低声说：",
            "time": {"start": 13.1, "end": 15.5}
        },
        {
            "text": "希望我考得还不错。",
            "time": {"start": 15.6, "end": 17.0}
        },
        {
            "text": "小红安慰他说：别担心，你一定没问题的。",
            "time": {"start": 17.1, "end": 20.0}
        }
    ]

def analyze_subtitle_events(subtitles: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    分析字幕中的事件和角色关系
    
    参数:
        subtitles: 字幕列表
        
    返回:
        分析结果
    """
    logger.info(f"开始分析 {len(subtitles)} 条字幕")
    
    # 使用SRL标注字幕
    start_time = time.time()
    annotated_subtitles = annotate_subtitles(subtitles)
    logger.info(f"SRL标注完成，耗时: {time.time() - start_time:.2f}秒")
    
    # 提取所有事件
    all_events = []
    character_relations = {}
    
    for subtitle in annotated_subtitles:
        # 从SRL结果提取事件
        srl_results = subtitle.get('srl', [])
        events = extract_events(srl_results)
        
        # 为每个事件添加情感和时间信息
        text = subtitle.get('text', '')
        sentiment = analyze_sentiment(text)
        
        for event in events:
            event['sentiment'] = sentiment
            event['time'] = subtitle.get('time', {})
            all_events.append(event)
            
            # 提取角色关系
            subject = event.get('subject', '').strip()
            object_text = event.get('object', '').strip()
            action = event.get('action', '').strip()
            
            if subject and object_text:
                if subject not in character_relations:
                    character_relations[subject] = {}
                    
                if object_text not in character_relations[subject]:
                    character_relations[subject][object_text] = []
                    
                character_relations[subject][object_text].append({
                    'action': action,
                    'sentiment': sentiment.get('label', 'NEUTRAL')
                })
    
    # 构建结果
    result = {
        'event_count': len(all_events),
        'events': all_events,
        'character_count': len(character_relations),
        'character_relations': character_relations
    }
    
    logger.info(f"分析完成，共提取 {len(all_events)} 个事件和 {len(character_relations)} 个角色")
    return result

def pretty_print_results(results: Dict[str, Any]) -> None:
    """
    美观打印分析结果
    
    参数:
        results: 分析结果
    """
    print("\n" + "="*50)
    print("语义角色标注分析结果")
    print("="*50)
    
    print(f"\n共发现 {results['event_count']} 个事件和 {results['character_count']} 个角色")
    
    # 打印事件列表
    print("\n事件列表:")
    print("-"*50)
    for i, event in enumerate(results['events'], 1):
        print(f"{i}. 主体: {event.get('subject', '无')} | " +
              f"动作: {event.get('action', '无')} | " +
              f"客体: {event.get('object', '无')} | " +
              f"情感: {event.get('sentiment', {}).get('label', 'NEUTRAL')}")
    
    # 打印角色关系
    print("\n角色关系:")
    print("-"*50)
    for subject, relations in results['character_relations'].items():
        print(f"\n角色: {subject}")
        for obj, actions in relations.items():
            print(f"  ↓ 与 {obj} 的关系:")
            for action in actions:
                print(f"    - {action.get('action', '无')} ({action.get('sentiment', 'NEUTRAL')})")

def main():
    """主函数"""
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    
    # 获取示例字幕
    sample_path = os.path.join(project_root, "data", "samples", "subtitles_sample.json")
    subtitles = load_sample_subtitles(sample_path)
    
    # 分析字幕事件
    results = analyze_subtitle_events(subtitles)
    
    # 打印结果
    pretty_print_results(results)
    
    # 保存结果
    output_dir = os.path.join(project_root, "data", "output", "srl_analysis")
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "srl_analysis_results.json")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n结果已保存至: {output_file}")

if __name__ == "__main__":
    main() 