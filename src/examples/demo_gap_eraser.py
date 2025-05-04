#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
毫秒级间隙消除示例

此示例展示了如何使用毫秒级间隙消除功能处理视频场景，
确保场景之间无缝衔接，提供更连贯的观看体验。

示例包括：
1. 基本的间隙消除
2. 带有场景保护的间隙消除
3. 自定义配置的间隙消除
4. 处理真实场景数据的示例
"""

import os
import sys
import json
import argparse
import logging
from typing import List, Dict, Any

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.timecode import eliminate_gaps, GapEraser, KeySceneGuard

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("间隙消除示例")


def load_scenes(scene_file: str) -> List[Dict[str, Any]]:
    """加载场景数据
    
    Args:
        scene_file: 场景文件路径
        
    Returns:
        List[Dict[str, Any]]: 场景数据列表
    """
    if not os.path.exists(scene_file):
        logger.warning(f"场景文件不存在: {scene_file}")
        return []
    
    try:
        with open(scene_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"加载场景文件失败: {str(e)}")
        return []


def create_sample_scenes() -> List[Dict[str, Any]]:
    """创建样例场景数据
    
    Returns:
        List[Dict[str, Any]]: 样例场景数据列表
    """
    return [
        {
            "id": "scene_1",
            "start_time": 0.0,
            "end_time": 10.0,
            "duration": 10.0,
            "importance": 0.9,
            "tags": ["开场", "关键"]
        },
        {
            "id": "scene_2",
            "start_time": 10.035,  # 35ms间隙
            "end_time": 20.0,
            "duration": 9.965,
            "importance": 0.5
        },
        {
            "id": "scene_3",
            "start_time": 20.08,  # 80ms间隙，超过默认阈值
            "end_time": 30.0,
            "duration": 9.92,
            "importance": 0.7
        },
        {
            "id": "scene_4",
            "start_time": 30.012,  # 12ms间隙
            "end_time": 40.0,
            "duration": 9.988,
            "importance": 0.8,
            "tags": ["高潮"]
        },
        {
            "id": "scene_5",
            "start_time": 40.042,  # 42ms间隙
            "end_time": 50.0,
            "duration": 9.958,
            "importance": 0.6
        }
    ]


def print_scene_gaps(scenes: List[Dict[str, Any]]) -> None:
    """打印场景间隙信息
    
    Args:
        scenes: 场景列表
    """
    print("\n场景间隙信息:")
    print("=" * 60)
    print(f"{'场景ID':<10} {'开始时间':<10} {'结束时间':<10} {'持续时间':<10} {'间隙(ms)':<10}")
    print("-" * 60)
    
    for i, scene in enumerate(scenes):
        # 计算与前一个场景的间隙
        gap = "N/A"
        if i > 0:
            prev_end = scenes[i-1].get("end_time", 0)
            curr_start = scene.get("start_time", 0)
            gap = f"{(curr_start - prev_end) * 1000:.1f}"
        
        print(f"{scene.get('id', f'场景{i}'):<10} "
              f"{scene.get('start_time', 0):<10.3f} "
              f"{scene.get('end_time', 0):<10.3f} "
              f"{scene.get('duration', 0):<10.3f} "
              f"{gap:<10}")
    
    print("=" * 60)


def demo_basic_gap_elimination() -> None:
    """基本间隙消除示例"""
    logger.info("=== 基本间隙消除示例 ===")
    
    # 创建样例场景
    scenes = create_sample_scenes()
    
    # 打印原始场景间隙
    logger.info("原始场景信息:")
    print_scene_gaps(scenes)
    
    # 执行间隙消除（使用默认设置）
    processed_scenes = eliminate_gaps(scenes)
    
    # 打印处理后的场景间隙
    logger.info("间隙消除后的场景信息:")
    print_scene_gaps(processed_scenes)
    
    logger.info("基本间隙消除示例完成")


def demo_protected_gap_elimination() -> None:
    """带场景保护的间隙消除示例"""
    logger.info("=== 带场景保护的间隙消除示例 ===")
    
    # 创建样例场景
    scenes = create_sample_scenes()
    
    # 应用场景保护
    scene_guard = KeySceneGuard({
        "emotion_threshold": 0.7,
        "importance_threshold": 0.8,
        "critical_tags": ["关键", "高潮"]
    })
    
    protected_scenes = scene_guard.mark_protected(scenes)
    
    # 打印保护信息
    logger.info("应用场景保护后:")
    for i, scene in enumerate(protected_scenes):
        protection_info = scene.get("_protection_info", {})
        if protection_info:
            logger.info(f"场景 {scene.get('id', f'场景{i}')} 已受保护，级别: {protection_info.get('level')}")
    
    # 打印原始场景间隙
    logger.info("原始场景信息:")
    print_scene_gaps(protected_scenes)
    
    # 执行间隙消除（尊重保护标记）
    processed_scenes = eliminate_gaps(protected_scenes, config={"respect_protection": True})
    
    # 打印处理后的场景间隙
    logger.info("间隙消除后的场景信息:")
    print_scene_gaps(processed_scenes)
    
    logger.info("带场景保护的间隙消除示例完成")


def demo_custom_gap_elimination() -> None:
    """自定义配置的间隙消除示例"""
    logger.info("=== 自定义配置的间隙消除示例 ===")
    
    # 创建样例场景
    scenes = create_sample_scenes()
    
    # 打印原始场景间隙
    logger.info("原始场景信息:")
    print_scene_gaps(scenes)
    
    # 创建自定义配置的间隙消除器
    custom_config = {
        "min_gap_threshold": 5,      # 最小5毫秒
        "max_gap_threshold": 100,    # 最大100毫秒（比默认值高）
        "prefer_end_adjustment": False,  # 优先调整开始点而不是结束点
        "start_key": "start_time",
        "end_key": "end_time",
        "duration_key": "duration"
    }
    
    eraser = GapEraser(custom_config)
    processed_scenes = eraser.eliminate_gaps(scenes)
    
    # 打印处理后的场景间隙
    logger.info("自定义配置间隙消除后的场景信息:")
    print_scene_gaps(processed_scenes)
    
    logger.info("自定义配置的间隙消除示例完成")


def demo_real_data_gap_elimination(scene_file: str) -> None:
    """真实数据间隙消除示例
    
    Args:
        scene_file: 场景文件路径
    """
    logger.info("=== 真实数据间隙消除示例 ===")
    
    # 加载真实场景数据
    scenes = load_scenes(scene_file)
    if not scenes:
        logger.error("无法加载场景数据")
        return
    
    logger.info(f"已加载 {len(scenes)} 个场景")
    
    # 打印原始场景间隙
    logger.info("原始场景信息:")
    print_scene_gaps(scenes)
    
    # 执行间隙消除
    processed_scenes = eliminate_gaps(scenes, max_gap_ms=40.0)
    
    # 打印处理后的场景间隙
    logger.info("间隙消除后的场景信息:")
    print_scene_gaps(processed_scenes)
    
    # 保存处理后的场景数据
    output_file = os.path.splitext(scene_file)[0] + "_processed.json"
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(processed_scenes, f, ensure_ascii=False, indent=2)
        logger.info(f"处理后的场景数据已保存到: {output_file}")
    except Exception as e:
        logger.error(f"保存处理后的场景数据失败: {str(e)}")
    
    logger.info("真实数据间隙消除示例完成")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="毫秒级间隙消除示例")
    parser.add_argument("--scene-file", "-s", help="场景数据文件路径（用于真实数据示例）")
    parser.add_argument("--demo-type", "-t", 
                        choices=["basic", "protected", "custom", "real", "all"],
                        default="all", 
                        help="示例类型")
    
    args = parser.parse_args()
    
    # 根据示例类型执行不同的演示
    if args.demo_type in ["basic", "all"]:
        demo_basic_gap_elimination()
        print("\n")
    
    if args.demo_type in ["protected", "all"]:
        demo_protected_gap_elimination()
        print("\n")
    
    if args.demo_type in ["custom", "all"]:
        demo_custom_gap_elimination()
        print("\n")
    
    if (args.demo_type in ["real", "all"]) and args.scene_file:
        demo_real_data_gap_elimination(args.scene_file)
    
    logger.info("示例运行完成")


if __name__ == "__main__":
    main() 