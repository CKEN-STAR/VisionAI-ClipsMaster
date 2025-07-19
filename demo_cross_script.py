#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
跨剧本模式对齐演示脚本

展示如何分析原片剧本模式与爆款剧本模式之间的关系，并识别模式转换规律
"""

import os
import json
import logging
from loguru import logger

# 设置日志
logging.basicConfig(level=logging.INFO)

# 导入模块
from src.core.cross_script_aligner import align_patterns
from src.core.narrative_unit_splitter import NarrativeUnitSplitter
from src.algorithms.pattern_mining import PatternMiner

def demo_cross_script_alignment():
    """演示跨剧本模式对齐功能"""
    logger.info("=== 跨剧本模式对齐演示 ===")
    
    # 示例: 原片剧本片段
    origin_script = """
    李明走进教室，看到同学们都已经到齐了。
    "今天我们讨论一下期末考试的复习计划。"老师说道。
    李明举手发言："老师，我们能不能先讨论一下上次的考试题？"
    老师点点头同意了。
    老师展示了考试的数据，大家发现基础题错得最多。
    "我们需要重新复习基础知识。"老师说。
    李明记下了笔记，准备回去复习。
    下课后，李明和同学们讨论了一下复习计划。
    """
    
    # 示例: 爆款改编后的剧本片段
    hit_script = """
    李明一脸紧张地冲进教室，发现所有人都已经坐好，目光齐刷刷地看向他。
    "今天，我们将讨论期末考试的复习计划。"老师面无表情地宣布。
    李明猛地举起手，声音颤抖："老师！我们能不能先看看上次的考试题？那些题太难了！"
    老师意味深长地看了他一眼，缓缓点头。
    老师打开投影仪，触目惊心的数据出现在屏幕上——全班90%的人连最基础的题目都做错了！
    "看来，我们需要从头开始！"老师的声音回荡在死寂的教室里。
    李明疯狂地记着笔记，心中暗暗发誓一定要拿下这次考试。
    下课铃响，李明立刻拉住几个同学："我有一个万无一失的复习计划..."
    """
    
    # 步骤1: 分割叙事节拍
    splitter = NarrativeUnitSplitter()
    origin_beats = splitter.split_into_beats(origin_script)
    hit_beats = splitter.split_into_beats(hit_script)
    
    logger.info(f"原片剧本: {len(origin_beats)} 个节拍")
    logger.info(f"爆款剧本: {len(hit_beats)} 个节拍")
    
    # 步骤2: 挖掘叙事模式
    miner = PatternMiner()
    origin_patterns = miner.mine(origin_beats)
    hit_patterns = miner.mine(hit_beats)
    
    logger.info(f"原片模式: {len(origin_patterns)} 个")
    logger.info(f"爆款模式: {len(hit_patterns)} 个")
    
    # 步骤3: 对齐模式，分析差异
    alignment_result = align_patterns(origin_patterns, hit_patterns)
    
    # 步骤4: 分析结果
    logger.info("\n对齐结果:")
    
    # 新增模式
    logger.info(f"\n新增模式 ({len(alignment_result['added'])} 个):")
    for i, pattern in enumerate(alignment_result['added'][:3], 1):  # 只显示前3个
        logger.info(f"{i}. 模式: {pattern.get('pattern', 'N/A')}")
        logger.info(f"   影响分数: {pattern.get('impact_score', 0):.2f}")
        logger.info(f"   支持度: {pattern.get('support', 0):.2f}")
    
    # 移除模式
    logger.info(f"\n移除模式 ({len(alignment_result['removed'])} 个):")
    for i, pattern in enumerate(alignment_result['removed'][:3], 1):  # 只显示前3个
        logger.info(f"{i}. 模式: {pattern.get('pattern', 'N/A')}")
        logger.info(f"   影响分数: {pattern.get('impact_score', 0):.2f}")
        logger.info(f"   支持度: {pattern.get('support', 0):.2f}")
    
    # 强化模式
    logger.info(f"\n强化模式 ({len(alignment_result['enhanced'])} 个):")
    for i, pattern in enumerate(alignment_result['enhanced'][:3], 1):  # 只显示前3个
        logger.info(f"{i}. 模式: {pattern.get('pattern', 'N/A')}")
        logger.info(f"   影响分数: {pattern.get('impact_score', 0):.2f}")
        
        # 显示强化信息
        if 'enhancements' in pattern:
            for j, enhancement in enumerate(pattern['enhancements'], 1):
                logger.info(f"   强化 {j}: {enhancement.get('description', 'N/A')}")
    
    # 总结转换规律
    logger.info("\n总结:")
    logger.info(f"爆款剧本主要通过 {len(alignment_result['added'])} 个新增模式和 "
                f"{len(alignment_result['enhanced'])} 个强化模式提升效果")
    
    # 如果有强化模式，分析最常见的强化类型
    if alignment_result['enhanced']:
        enhancement_types = {}
        for pattern in alignment_result['enhanced']:
            for enhancement in pattern.get('enhancements', []):
                enhancement_type = enhancement.get('type', 'unknown')
                enhancement_types[enhancement_type] = enhancement_types.get(enhancement_type, 0) + 1
        
        # 找出最常见的强化类型
        if enhancement_types:
            top_type = max(enhancement_types.items(), key=lambda x: x[1])
            logger.info(f"最常见的强化类型是 '{top_type[0]}'，出现 {top_type[1]} 次")
    
    return alignment_result


if __name__ == "__main__":
    logger.info("开始跨剧本模式对齐演示...")
    result = demo_cross_script_alignment()
    logger.info("\n演示完成。") 