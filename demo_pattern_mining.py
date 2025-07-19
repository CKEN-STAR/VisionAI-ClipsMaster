#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
模式挖掘演示脚本

展示模式挖掘模块的基本功能，包括分析叙事节拍、发现模式和提取叙事指纹
"""

import os
import sys
import json
from pathlib import Path

# 设置logging输出格式
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("demo_pattern_mining")

# 导入所需模块
from src.core.narrative_unit_splitter import NarrativeUnitSplitter
from src.algorithms.pattern_mining import PatternMiner

def demo_simple_text():
    """演示简单文本的模式挖掘"""
    logger.info("=== 简单文本模式挖掘演示 ===")
    
    # 定义示例文本
    text = """
    小明走进教室，环顾四周，发现同学们都已经到齐了。
    "今天我们来讨论一下期末考试的复习计划。"老师微笑着说道。
    小明紧张地举起了手："老师，我们能不能先讨论一下上次测验的问题？"
    老师点点头："好的，我们先来看看大家在上次测验中的常见错误。"
    老师打开投影仪，展示了一系列数据图表。全班同学都惊讶地发现，最多人错的竟然是最基础的概念题。
    "看来我们需要重新复习基础知识。"老师严肃地说，"如果基础不牢，后面的内容就更难理解了。"
    小明若有所思地记下了笔记，决定回去后重新整理所有基础概念。
    下课铃响了，同学们收拾书包准备离开，老师最后提醒道："别忘了完成今天布置的复习任务！"
    小明走出教室，心里已经有了一个完整的复习计划。
    """
    
    # 分割叙事节拍
    splitter = NarrativeUnitSplitter()
    beats = splitter.split_into_beats(text)
    
    logger.info(f"识别出 {len(beats)} 个叙事节拍")
    for i, beat in enumerate(beats):
        logger.info(f"节拍 {i+1}: 类型={beat['type']}, 情感值={beat['emotion'].get('sentiment', 0):.2f}, 文本={beat['text'][:50]}...")
    
    # 创建模式挖掘器
    miner = PatternMiner()
    
    # 提取叙事指纹
    fingerprint = miner.extract_narrative_fingerprint(beats)
    logger.info("\n叙事指纹:")
    print(json.dumps(fingerprint, ensure_ascii=False, indent=2))
    
    return beats

def demo_multiple_texts():
    """演示多个文本的模式挖掘"""
    logger.info("\n=== 多文本模式挖掘演示 ===")
    
    # 定义几个不同的叙事文本
    texts = [
        # 文本1: 惊喜类故事
        """
        小红今天过生日，但她觉得所有人都忘记了这件事。
        上学路上，同学们都很正常地和她打招呼，没有任何特别之处。
        整个上午的课程中，连最好的朋友都没有提起她的生日。
        下午放学时，小红失落地收拾书包，准备独自回家。
        "小红，你能帮我拿一下东西吗？在活动室。"班长突然走过来说。
        小红勉强点点头，跟着班长走向活动室。
        推开门的一瞬间，教室里突然亮起彩灯，所有同学跳出来高喊："生日快乐！"
        小红惊讶地张大嘴巴，眼泪涌了出来。原来大家都记得，而且精心准备了这个惊喜。
        那天，在欢笑与祝福中，小红度过了最难忘的生日。
        """,
        
        # 文本2: 解决问题类故事
        """
        老王家的水管突然坏了，水流得到处都是。
        他急忙打电话叫修理工，但所有人都说至少要等三天。
        眼看家里的水越积越多，老王开始自己查找解决方案。
        他在网上搜索教程，买来了工具，决定自己动手修理。
        第一次尝试失败了，水流得更厉害了。
        老王没有放弃，仔细研究问题出在哪里。
        经过反复尝试，他终于找到了漏水点，成功修好了水管。
        这次经历让老王明白，遇到问题时，与其等待别人帮助，不如学习解决问题的能力。
        从那以后，他开始学习各种家庭维修技能，成了小区里的"万能修理工"。
        """,
        
        # 文本3: 成长类故事
        """
        小李是个内向的学生，从不敢在班上发言。
        一次课堂讨论中，老师点名让他回答问题。
        小李结结巴巴地说了几句，引得几个同学轻笑。
        放学后，小李难过地躲在厕所里哭泣。
        班主任找到他，鼓励他说："勇气不是没有恐惧，而是战胜恐惧。"
        在班主任的建议下，小李开始参加学校的演讲课。
        最初的几次练习，他紧张得手心冒汗，声音发抖。
        但随着一次次练习，他逐渐变得自信起来。
        期末演讲比赛上，小李流利地完成了演讲，赢得了全场掌声。
        那一刻，他知道自己真正战胜了恐惧，成长为更好的自己。
        """
    ]
    
    # 处理所有文本
    all_beats = []
    for i, text in enumerate(texts):
        splitter = NarrativeUnitSplitter()
        beats = splitter.split_into_beats(text)
        all_beats.append(beats)
        logger.info(f"文本 {i+1}: 识别出 {len(beats)} 个叙事节拍")
    
    # 创建模式挖掘器
    miner = PatternMiner()
    
    # 使用叙事模式分析器发现模式
    narrative_analyzer = miner.algorithms['narrative']
    patterns = narrative_analyzer.discover_patterns(all_beats)
    
    # 输出部分结果
    logger.info("\n发现的模式:")
    for pattern_type, pattern_list in patterns.items():
        logger.info(f"\n--- {pattern_type} ---")
        for i, pattern in enumerate(pattern_list[:2]):  # 只显示前2个
            logger.info(f"模式 {i+1}: {pattern}")
    
    # 比较叙事指纹
    logger.info("\n叙事指纹比较:")
    fingerprints = []
    for i, beats in enumerate(all_beats):
        fingerprint = miner.extract_narrative_fingerprint(beats)
        fingerprints.append(fingerprint)
        logger.info(f"文本 {i+1} 叙事类型分布: {fingerprint['beat_type_distribution']}")
    
    return patterns, all_beats

if __name__ == "__main__":
    logger.info("开始模式挖掘演示...")
    
    # 演示单一文本分析
    single_beats = demo_simple_text()
    
    # 演示多文本模式挖掘
    patterns, all_beats = demo_multiple_texts()
    
    logger.info("\n演示完成。") 