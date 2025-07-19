#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
多策略生成引擎使用示例

该示例展示如何使用多策略生成引擎来同时生成多种风格的剧本混剪，
并比较不同策略的特点和效果。
"""

import os
import sys
import json
from typing import List, Dict, Any
from loguru import logger

# 添加项目根目录到Python路径
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if root_dir not in sys.path:
    sys.path.append(root_dir)

from src.versioning import (
    MultiStrategyEngine, 
    run_multi_strategy,
    ReverseNarrativeStrategy,
    ParallelThreadsStrategy,
    EmotionAmplificationStrategy,
    MinimalistAdaptationStrategy
)
from src.core.screenplay_engineer import ScreenplayEngineer
from src.core.srt_parser import parse_srt_file

# 设置日志
logger.add(os.path.join(root_dir, "logs", "multi_strategy_example.log"))

def load_sample_subtitles() -> List[Dict[str, Any]]:
    """加载示例字幕
    
    如果没有字幕文件，则生成一个简单的示例字幕
    
    Returns:
        List[Dict[str, Any]]: 字幕数据
    """
    # 首先尝试从SRT文件加载
    samples_dir = os.path.join(root_dir, "samples")
    os.makedirs(samples_dir, exist_ok=True)
    
    srt_files = [f for f in os.listdir(samples_dir) if f.endswith('.srt')]
    
    if srt_files:
        srt_path = os.path.join(samples_dir, srt_files[0])
        logger.info(f"从SRT文件加载字幕: {srt_path}")
        return parse_srt_file(srt_path)
    
    # 如果没有找到SRT文件，生成示例字幕
    logger.info("生成示例字幕数据")
    
    # 创建一个简单的对话示例
    sample_subtitles = [
        {
            "index": 1,
            "start_time": 0.0,
            "end_time": 4.0,
            "text": "张明：今天的天气真不错，要不要一起去公园?"
        },
        {
            "index": 2,
            "start_time": 4.5,
            "end_time": 7.0,
            "text": "李华：可是我还有工作要完成..."
        },
        {
            "index": 3,
            "start_time": 7.5,
            "end_time": 10.0,
            "text": "张明：工作总是做不完的，偶尔放松一下吧。"
        },
        {
            "index": 4,
            "start_time": 11.0,
            "end_time": 15.0,
            "text": "李华：你说得对，但我下午有个重要会议，必须准备好。"
        },
        {
            "index": 5,
            "start_time": 16.0,
            "end_time": 19.0,
            "text": "张明：那会议结束后呢？我可以等你。"
        },
        {
            "index": 6,
            "start_time": 20.0,
            "end_time": 24.0,
            "text": "李华：(叹气) 好吧，会议大概5点结束，到时候联系你。"
        },
        {
            "index": 7,
            "start_time": 25.0,
            "end_time": 28.0,
            "text": "张明：太好了！我会在咖啡厅等你。"
        },
        {
            "index": 8,
            "start_time": 29.0,
            "end_time": 32.0,
            "text": "李华：希望会议不会拖延..."
        },
        {
            "index": 9,
            "start_time": 33.0,
            "end_time": 38.0,
            "text": "旁白：但李华没想到，这次会议将彻底改变他的职业生涯。"
        },
        {
            "index": 10,
            "start_time": 39.0,
            "end_time": 43.0,
            "text": "老板：李华，我们决定升你为项目主管，但你需要立即飞往上海。"
        },
        {
            "index": 11,
            "start_time": 44.0,
            "end_time": 48.0,
            "text": "李华：(震惊) 什么？今天？但我有约..."
        },
        {
            "index": 12,
            "start_time": 49.0,
            "end_time": 53.0,
            "text": "老板：机会只有一次，航班两小时后起飞。你怎么选择？"
        },
        {
            "index": 13,
            "start_time": 54.0,
            "end_time": 59.0,
            "text": "李华：(看着手机，张明发来消息：「我已经到咖啡厅了，点了你喜欢的蛋糕」)"
        },
        {
            "index": 14,
            "start_time": 60.0,
            "end_time": 65.0,
            "text": "李华：(深呼吸) 我需要一点时间考虑..."
        },
        {
            "index": 15,
            "start_time": 66.0,
            "end_time": 70.0,
            "text": "旁白：有时候，人生的选择题并没有标准答案。"
        }
    ]
    
    return sample_subtitles

def compare_strategy_results(results: List[Dict[str, Any]]) -> None:
    """比较不同策略的结果
    
    Args:
        results: 多策略生成的结果列表
    """
    if not results:
        logger.warning("没有生成结果可比较")
        return
    
    # 打印比较表格
    logger.info("===== 不同策略生成结果比较 =====")
    logger.info(f"{'策略名称':<12} {'片段数':<6} {'预计时长':<8} {'主要特点'}")
    logger.info("-" * 60)
    
    for result in results:
        strategy = result.get("strategy", {})
        segments = result.get("segments", [])
        
        # 计算总时长
        total_duration = 0
        for seg in segments:
            start_time = seg.get("start_time", 0)
            end_time = seg.get("end_time", 0)
            total_duration += (end_time - start_time)
        
        # 获取策略特点
        strategy_name = strategy.get("name", "未知策略")
        segments_count = len(segments)
        
        # 提取主要特点
        features = []
        if "reverse_narrative" in strategy:
            features.append("倒叙叙事")
        if "character_threads" in strategy:
            chars = strategy.get("character_threads", [])
            features.append(f"多角色({len(chars)})")
        if "emotion_peaks_count" in strategy:
            peaks = strategy.get("emotion_peaks_count", 0)
            features.append(f"情感高潮({peaks})")
        if "main_character" in strategy:
            char = strategy.get("main_character", "")
            features.append(f"聚焦'{char}'")
        if "reduction_ratio" in strategy:
            ratio = strategy.get("reduction_ratio", 1.0)
            features.append(f"精简率{ratio:.2f}")
        
        features_str = ", ".join(features) if features else "标准处理"
        
        # 打印结果行
        logger.info(f"{strategy_name:<12} {segments_count:<6} {total_duration:<8.1f}秒 {features_str}")
    
    logger.info("=" * 60)

def export_results(results: List[Dict[str, Any]], output_dir: str) -> None:
    """导出生成结果
    
    Args:
        results: 多策略生成的结果列表
        output_dir: 输出目录
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # 为每个策略结果创建SRT文件
    for result in results:
        strategy = result.get("strategy", {})
        strategy_name = strategy.get("name", "unknown")
        segments = result.get("segments", [])
        
        # 创建SRT内容
        srt_content = []
        for i, segment in enumerate(segments, 1):
            start_time = segment.get("start_time", 0)
            end_time = segment.get("end_time", 0)
            text = segment.get("text", "")
            
            # 转换时间格式为SRT格式 (HH:MM:SS,mmm)
            start_formatted = format_time_for_srt(start_time)
            end_formatted = format_time_for_srt(end_time)
            
            srt_content.extend([
                str(i),
                f"{start_formatted} --> {end_formatted}",
                text,
                ""
            ])
        
        # 写入SRT文件
        file_name = f"{strategy_name}_结果.srt"
        file_path = os.path.join(output_dir, file_name)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(srt_content))
        
        logger.info(f"已导出结果到: {file_path}")
        
        # 同时保存元数据JSON
        meta_file_name = f"{strategy_name}_元数据.json"
        meta_file_path = os.path.join(output_dir, meta_file_name)
        
        with open(meta_file_path, 'w', encoding='utf-8') as f:
            json.dump(strategy, f, ensure_ascii=False, indent=2)

def format_time_for_srt(seconds: float) -> str:
    """将秒数转换为SRT时间格式
    
    Args:
        seconds: 秒数
        
    Returns:
        str: SRT格式的时间字符串 (HH:MM:SS,mmm)
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = seconds % 60
    milliseconds = int((seconds - int(seconds)) * 1000)
    
    return f"{hours:02d}:{minutes:02d}:{int(seconds):02d},{milliseconds:03d}"

def run_example():
    """运行多策略生成示例"""
    logger.info("=== 多策略生成引擎示例 ===")
    
    # 加载示例字幕
    subtitles = load_sample_subtitles()
    logger.info(f"加载了 {len(subtitles)} 个字幕片段")
    
    # 创建输出目录
    output_dir = os.path.join(root_dir, "output", "multi_strategy_results")
    os.makedirs(output_dir, exist_ok=True)
    
    # 设置基础参数
    base_params = {
        "target_duration": 50,  # 目标时长50秒
        "max_segments": 10,     # 最多10个片段
    }
    
    # 运行多策略生成
    logger.info("开始执行多策略生成...")
    results = run_multi_strategy(
        subtitles=subtitles,
        # 不指定策略名称，将使用所有策略
        params=base_params
    )
    
    # 比较结果
    logger.info(f"生成完成，共 {len(results)} 个结果")
    compare_strategy_results(results)
    
    # 导出结果
    export_results(results, output_dir)
    
    logger.info(f"所有结果已导出到目录: {output_dir}")
    logger.info("示例运行完成")

if __name__ == "__main__":
    run_example()

 