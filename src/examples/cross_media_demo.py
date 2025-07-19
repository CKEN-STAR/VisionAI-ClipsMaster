"""
跨媒介模式迁移演示

演示如何将叙事模式从一种媒介类型迁移到另一种媒介类型
"""

import os
import json
import yaml
import time
from typing import Dict, List, Any
from pathlib import Path
import random

from loguru import logger
from src.adaptation.cross_media import CrossMediaAdapter
from src.version_management.pattern_version_manager import PatternVersionManager


def create_sample_pattern(pattern_id: str, pattern_type: str) -> Dict[str, Any]:
    """
    创建样本模式
    
    Args:
        pattern_id: 模式ID
        pattern_type: 模式类型
        
    Returns:
        样本模式
    """
    pattern = {
        "id": pattern_id,
        "type": pattern_type,
        "media_type": "电影",  # 默认为电影类型
        "description": f"{pattern_type.capitalize()}类型叙事模式",
        "frequency": random.uniform(0.6, 0.9),
        "position": {
            "opening": 0.1,
            "climax": 0.7,
            "conflict": 0.4,
            "transition": random.uniform(0.2, 0.8),
            "resolution": 0.8,
            "ending": 0.9
        }.get(pattern_type, random.uniform(0.2, 0.8)),
        "duration": {
            "opening": random.uniform(60, 120),
            "climax": random.uniform(120, 240),
            "conflict": random.uniform(90, 180),
            "transition": random.uniform(30, 60),
            "resolution": random.uniform(60, 120),
            "ending": random.uniform(60, 120)
        }.get(pattern_type, random.uniform(60, 180)),
        "sentiment": {
            "opening": random.uniform(0.2, 0.5),
            "climax": random.uniform(-0.8, 0.8),
            "conflict": random.uniform(-0.8, -0.3),
            "transition": random.uniform(-0.2, 0.2),
            "resolution": random.uniform(0.3, 0.7),
            "ending": random.uniform(0.2, 0.8)
        }.get(pattern_type, random.uniform(-0.3, 0.3)),
        "keywords": get_sample_keywords(pattern_type),
        "narrative_density": random.uniform(0.7, 1.0),
        "visual_complexity": random.uniform(0.6, 0.9),
        "audio_elements": ["dialogue", "music", "sound_effects"],
        "pacing": random.uniform(0.5, 0.8),
        "impact_score": random.uniform(0.65, 0.9)
    }
    
    return pattern


def get_sample_keywords(pattern_type: str) -> List[str]:
    """
    获取样本关键词
    
    Args:
        pattern_type: 模式类型
        
    Returns:
        关键词列表
    """
    keywords_map = {
        "opening": ["开场", "介绍", "背景", "设定", "人物", "环境"],
        "climax": ["高潮", "转折", "惊喜", "震撼", "失败", "成功", "情感"],
        "conflict": ["冲突", "对抗", "矛盾", "挑战", "障碍", "危机"],
        "transition": ["过渡", "转换", "变化", "调整", "变动"],
        "resolution": ["解决", "结局", "和解", "理解", "成长"],
        "ending": ["结束", "落幕", "告别", "离开", "新起点"]
    }
    
    all_keywords = keywords_map.get(pattern_type, ["关键", "重要", "核心"])
    return random.sample(all_keywords, min(3, len(all_keywords)))


def generate_sample_patterns(count: int = 6) -> List[Dict[str, Any]]:
    """
    生成样本模式
    
    Args:
        count: 模式数量
        
    Returns:
        模式列表
    """
    pattern_types = ["opening", "climax", "conflict", "transition", "resolution", "ending"]
    patterns = []
    
    for i in range(count):
        pattern_type = pattern_types[i % len(pattern_types)]
        pattern_id = f"pattern_{i+1}"
        pattern = create_sample_pattern(pattern_id, pattern_type)
        patterns.append(pattern)
    
    return patterns


def print_pattern_summary(pattern: Dict[str, Any], prefix: str = "") -> None:
    """
    打印模式摘要
    
    Args:
        pattern: 模式
        prefix: 前缀
    """
    logger.info(f"{prefix}模式ID: {pattern['id']}")
    logger.info(f"{prefix}模式类型: {pattern['type']}")
    logger.info(f"{prefix}媒介类型: {pattern['media_type']}")
    logger.info(f"{prefix}描述: {pattern['description']}")
    logger.info(f"{prefix}位置: {pattern['position']:.2f}")
    logger.info(f"{prefix}时长: {pattern['duration']:.2f}秒")
    
    if "adaptation_method" in pattern:
        logger.info(f"{prefix}适配方法: {pattern['adaptation_method']}")
    
    if "keywords_highlighted" in pattern:
        logger.info(f"{prefix}关键词突出: {pattern['keywords_highlighted']}")
    
    if "audio_enhanced" in pattern:
        logger.info(f"{prefix}音频增强: {pattern['audio_enhanced']}")
    
    if "has_branches" in pattern:
        logger.info(f"{prefix}分支数量: {pattern['branch_points']}")
    
    logger.info(f"{prefix}{'='*40}")


def main():
    """主函数"""
    logger.info("开始跨媒介模式迁移演示")
    
    # 初始化跨媒介适配器
    config_path = "configs/adaptation/cross_media.yaml"
    adapter = CrossMediaAdapter(config_path)
    logger.info("跨媒介适配器初始化完成")
    
    # 获取支持的媒介类型
    media_types = adapter.get_supported_media_types()
    logger.info(f"支持的媒介类型: {', '.join(media_types)}")
    
    # 生成样本模式
    patterns = generate_sample_patterns(6)
    logger.info(f"生成了 {len(patterns)} 个样本模式")
    
    # 打印原始模式
    logger.info("\n原始模式示例:")
    print_pattern_summary(patterns[0])
    
    # 演示适配到不同媒介类型
    target_media_types = ["短视频", "互动剧", "广播剧", "漫画"]
    
    for i, target_media_type in enumerate(target_media_types):
        # 选择一个模式进行适配
        source_pattern = patterns[i % len(patterns)]
        
        logger.info(f"\n将模式 {source_pattern['id']} 适配到 {target_media_type}")
        
        # 适配模式
        adapted_pattern = adapter.adapt_pattern(source_pattern, target_media_type)
        
        # 打印适配后的模式
        logger.info(f"适配后的 {target_media_type} 模式:")
        print_pattern_summary(adapted_pattern, "  ")
        
        # 添加间隔
        logger.info("\n" + "-" * 60 + "\n")
    
    # 演示批量适配
    target_media = "短视频"
    logger.info(f"\n批量将模式适配到 {target_media}")
    
    # 批量适配
    start_time = time.time()
    adapted_patterns = adapter.batch_adapt_patterns(patterns, target_media)
    elapsed_time = time.time() - start_time
    
    logger.info(f"成功适配 {len(adapted_patterns)} 个模式到 {target_media}，耗时 {elapsed_time:.2f} 秒")
    
    # 演示创建适配版本
    try:
        # 初始化版本管理器并创建一个基础版本
        version_manager = PatternVersionManager()
        
        # 创建基础版本配置
        base_config = {
            "pattern_types": ["opening", "climax", "conflict", "transition", "resolution", "ending"],
            "top_patterns": patterns,
            "media_type": "电影",
            "description": "基础电影模式集合"
        }
        
        # 创建或更新基础版本
        base_version = "v1.0"
        if not version_manager.update_pattern_config(base_config, base_version):
            # 如果版本不存在，创建新版本
            version_manager.create_new_version(
                base_version, 
                description="基础电影模式集合",
                author="CrossMediaDemo"
            )
            version_manager.update_pattern_config(base_config, base_version)
            logger.info(f"创建了基础版本 {base_version}")
        else:
            logger.info(f"更新了基础版本 {base_version}")
        
        # 创建适配版本
        target_media = "互动剧"
        result = adapter.create_adapted_version(base_version, target_media)
        
        if result:
            logger.info(f"成功创建适配版本 {base_version}_{adapter.reverse_media_mapping.get(target_media, 'media')}")
        else:
            logger.error("创建适配版本失败")
    
    except Exception as e:
        logger.error(f"版本管理演示失败: {e}")
    
    logger.info("\n跨媒介模式迁移演示完成")


if __name__ == "__main__":
    main() 