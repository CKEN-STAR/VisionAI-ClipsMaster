#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
安全余量管理功能演示脚本

此脚本演示了如何使用VisionAI-ClipsMaster的安全余量管理功能：
1. 基本的安全余量计算
2. 自动检测是否需要压缩
3. 带有场景保护的智能时长调整
4. 自定义配置选项
"""

import sys
import os
import logging
from typing import Dict, List, Any

# 添加项目根目录到系统路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# 导入安全余量管理相关函数
from src.timecode.safety_margin import MarginKeeper, apply_safety_margin, adjust_for_safety

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("safety_margin_demo")

def demo_basic_margin_calculation():
    """演示基本的安全余量计算"""
    logger.info("===== 基本安全余量计算演示 =====")
    
    # 目标时长（秒）
    target_duration = 600.0  # 10分钟
    
    # 应用默认的5%安全余量
    safe_duration = apply_safety_margin(target_duration)
    logger.info(f"目标时长: {target_duration}秒")
    logger.info(f"应用5%安全余量后的实际可用时长: {safe_duration}秒")
    
    # 使用不同的安全余量比例
    safe_duration_3p = apply_safety_margin(target_duration, margin_ratio=0.03)
    logger.info(f"应用3%安全余量后的实际可用时长: {safe_duration_3p}秒")
    
    safe_duration_10p = apply_safety_margin(target_duration, margin_ratio=0.10)
    logger.info(f"应用10%安全余量后的实际可用时长: {safe_duration_10p}秒")
    
    # 演示超出合理范围的安全余量比例会被自动调整
    keeper = MarginKeeper()
    keeper.set_margin_ratio(0.01)  # 低于默认最小值0.02
    keeper.set_margin_ratio(0.20)  # 高于默认最大值0.15
    
def demo_safety_check():
    """演示安全状态检查"""
    logger.info("\n===== 安全状态检查演示 =====")
    
    # 创建安全余量管理器
    keeper = MarginKeeper()
    
    # 目标时长（秒）
    target_duration = 600.0  # 10分钟
    
    # 不同的当前时长场景
    current_durations = [
        570.0,  # 9分30秒 - 安全范围内
        580.0,  # 9分40秒 - 接近临界点
        590.0,  # 9分50秒 - 接近临界点
        600.0,  # 10分钟 - 临界点
        610.0,  # 10分10秒 - 超出安全范围
        630.0,  # 10分30秒 - 明显超出
    ]
    
    for current in current_durations:
        safety_info = keeper.check_duration_safety(current, target_duration)
        status = "安全" if safety_info["safe"] else "需要压缩"
        ratio_percent = safety_info["ratio"] * 100
        
        logger.info(f"当前时长: {current}秒 ({ratio_percent:.1f}% 目标时长) - 状态: {status}")
        
        if not safety_info["safe"]:
            safe_target = safety_info.get("safe_target")
            compression = safety_info["compression_ratio"]
            logger.info(f"  → 建议压缩至 {safe_target:.1f}秒 (压缩比例: {compression:.2f})")

def create_demo_scenes() -> List[Dict[str, Any]]:
    """创建演示用的场景数据
    
    Returns:
        场景列表
    """
    return [
        {
            "id": "scene1",
            "name": "开场白",
            "start_time": 0,
            "end_time": 60,
            "duration": 60,  # 1分钟
            "_protection_info": {
                "level": "HIGH",
                "strategies": ["NO_TRIM", "LOCK"],
                "reason": "关键开场内容"
            }
        },
        {
            "id": "scene2",
            "name": "过渡场景",
            "start_time": 60,
            "end_time": 90,
            "duration": 30,  # 30秒
        },
        {
            "id": "scene3",
            "name": "主题内容A",
            "start_time": 90,
            "end_time": 270,
            "duration": 180,  # 3分钟
            "_compression_info": {
                "restriction_level": "LOW",
                "allowed_ratio": 0.8
            }
        },
        {
            "id": "scene4",
            "name": "主题内容B",
            "start_time": 270,
            "end_time": 450,
            "duration": 180,  # 3分钟
        },
        {
            "id": "scene5",
            "name": "主题内容C",
            "start_time": 450,
            "end_time": 570,
            "duration": 120,  # 2分钟
        },
        {
            "id": "scene6",
            "name": "结尾总结",
            "start_time": 570,
            "end_time": 630,
            "duration": 60,  # 1分钟
            "_protection_info": {
                "level": "MEDIUM",
                "strategies": ["NO_COMPRESS"],
                "reason": "总结关键点"
            }
        }
    ]

def demo_scene_adjustment():
    """演示场景时长调整"""
    logger.info("\n===== 场景时长调整演示 =====")
    
    # 创建测试场景
    scenes = create_demo_scenes()
    
    # 计算原始总时长
    total_duration = sum(scene["duration"] for scene in scenes)
    logger.info(f"原始场景总时长: {total_duration}秒")
    
    # 设置目标时长略小于当前总时长，触发调整
    target_duration = 600  # 10分钟
    logger.info(f"目标时长上限: {target_duration}秒")
    
    # 使用默认5%安全余量
    adjusted_scenes, info = adjust_for_safety(scenes, target_duration)
    
    if info["adjusted"]:
        logger.info(f"场景已调整: {info['original_duration']}秒 -> {info['new_duration']}秒")
        logger.info(f"调整了 {info['scenes_adjusted']} 个场景，保护了 {info['scenes_protected']} 个场景")
        
        # 打印每个场景的调整信息
        logger.info("\n调整后的场景时长:")
        for i, scene in enumerate(adjusted_scenes):
            original_scene = scenes[i]
            original_duration = original_scene["duration"]
            new_duration = scene["duration"]
            name = scene["name"]
            
            if "_adjustment_info" in scene:
                adjustment = scene["_adjustment_info"]
                ratio = adjustment["compression_ratio"]
                logger.info(f"  {name}: {original_duration}秒 -> {new_duration:.1f}秒 (压缩比例: {ratio:.2f})")
            else:
                logger.info(f"  {name}: {original_duration}秒 (未调整)")
    else:
        logger.info(f"未调整场景: {info['reason']}")

def demo_custom_configuration():
    """演示自定义配置选项"""
    logger.info("\n===== 自定义配置选项演示 =====")
    
    # 创建测试场景
    scenes = create_demo_scenes()
    
    # 设置目标时长触发调整
    target_duration = 600  # 10分钟
    
    # 自定义配置
    custom_config = {
        "auto_adjust": True,
        "min_margin": 0.03,            # 最小安全余量3%
        "max_margin": 0.12,            # 最大安全余量12%
        "critical_threshold": 0.90,    # 更严格的临界阈值90%
        "preserve_keyframes": True,
    }
    
    logger.info("使用自定义配置:")
    for key, value in custom_config.items():
        logger.info(f"  {key}: {value}")
    
    # 使用自定义配置和更高的安全余量
    margin_ratio = 0.08  # 8%安全余量
    logger.info(f"安全余量: {margin_ratio:.1%}")
    
    adjusted_scenes, info = adjust_for_safety(scenes, target_duration, margin_ratio, custom_config)
    
    if info["adjusted"]:
        logger.info(f"场景已调整: {info['original_duration']}秒 -> {info['new_duration']}秒")
        logger.info(f"安全阈值: {info['safety_threshold']}")
        logger.info(f"应用的压缩比例: {info['compression_applied']:.2f}")
    else:
        logger.info(f"未调整场景: {info['reason']}")

def main():
    """主函数"""
    logger.info("安全余量管理功能演示\n")
    
    # 演示基本安全余量计算
    demo_basic_margin_calculation()
    
    # 演示安全状态检查
    demo_safety_check()
    
    # 演示场景时长调整
    demo_scene_adjustment()
    
    # 演示自定义配置选项
    demo_custom_configuration()
    
    logger.info("\n演示完成!")

if __name__ == "__main__":
    main() 