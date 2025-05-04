#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试语义角色标注系统
"""

import sys
import os
import logging

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.nlp.srl_annotator import (
    annotate_text, 
    annotate_batch, 
    annotate_subtitles, 
    extract_events
)

# 设置日志级别
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_chinese_srl():
    """测试中文SRL功能"""
    print("\n===== 测试中文语义角色标注 =====")
    
    test_sentences = [
        "小明在公园里遇见了他的朋友小红",
        "老师正在教室里给学生们讲解数学题",
        "妈妈昨天晚上做了一顿丰盛的晚餐",
        "这个电影讲述了一个关于友谊的感人故事"
    ]
    
    print("单句测试:")
    for sentence in test_sentences:
        result = annotate_text(sentence, "zh")
        print(f"\n文本: {sentence}")
        print(f"结果: {result}")
        
        # 提取事件
        events = extract_events(result)
        print(f"事件: {events}")
    
    print("\n批量测试:")
    batch_results = annotate_batch(test_sentences, "zh")
    print(f"批量处理结果数量: {len(batch_results)}")
    
    # 测试字幕处理
    print("\n字幕处理测试:")
    subtitles = [
        {"text": "小明在公园里遇见了他的朋友小红", "time": {"start": 0.0, "end": 3.5}},
        {"text": "他们一起去了图书馆", "time": {"start": 3.6, "end": 6.0}},
        {"text": "在那里学习了一整天", "time": {"start": 6.1, "end": 9.0}}
    ]
    subtitle_results = annotate_subtitles(subtitles, "zh")
    for result in subtitle_results:
        print(f"\n字幕: {result['text']}")
        print(f"时间: {result['time']}")
        print(f"SRL: {result['srl']}")

def test_english_srl():
    """测试英文SRL功能（使用备用方案）"""
    print("\n===== 测试英文语义角色标注 =====")
    
    test_sentences = [
        "John met his friend Mary in the park yesterday",
        "The teacher is explaining math problems to students in the classroom",
        "My mother cooked a delicious dinner last night",
        "This movie tells a touching story about friendship"
    ]
    
    print("单句测试:")
    for sentence in test_sentences:
        result = annotate_text(sentence, "en")
        print(f"\n文本: {sentence}")
        print(f"结果: {result}")
        
        # 提取事件
        events = extract_events(result)
        print(f"事件: {events}")
    
    # 测试字幕处理
    print("\n字幕处理测试:")
    subtitles = [
        {"text": "John met his friend Mary in the park", "time": {"start": 0.0, "end": 3.5}},
        {"text": "They went to the library together", "time": {"start": 3.6, "end": 6.0}},
        {"text": "They studied there all day", "time": {"start": 6.1, "end": 9.0}}
    ]
    subtitle_results = annotate_subtitles(subtitles, "en")
    for result in subtitle_results:
        print(f"\n字幕: {result['text']}")
        print(f"时间: {result['time']}")
        print(f"SRL: {result['srl']}")

def test_auto_language_detection():
    """测试自动语言检测功能"""
    print("\n===== 测试自动语言检测 =====")
    
    test_sentences = [
        "小明在公园里遇见了他的朋友小红",
        "John met his friend Mary in the park yesterday",
        "这个电影讲述了一个关于友谊的感人故事",
        "This movie tells a touching story about friendship"
    ]
    
    for sentence in test_sentences:
        result = annotate_text(sentence)  # 不指定语言，使用自动检测
        print(f"\n文本: {sentence}")
        print(f"结果: {result}")

if __name__ == "__main__":
    print("开始测试语义角色标注系统...")
    
    # 测试中文SRL
    test_chinese_srl()
    
    # 测试英文SRL
    test_english_srl()
    
    # 测试自动语言检测
    test_auto_language_detection()
    
    print("\n所有测试完成!") 