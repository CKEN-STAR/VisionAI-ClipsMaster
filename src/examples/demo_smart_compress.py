#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
智能压缩算法示例

此示例展示了智能压缩算法的基本使用方法：
1. 基本压缩
2. 带场景保护的压缩
3. 基于目标大小的压缩
4. 自定义配置的压缩
"""

import os
import sys
import time
import argparse
import json
import logging
from typing import List, Dict, Any, Optional

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.timecode import (
    SmartCompressor,
    compress_video,
    CompressionLevel,
    KeySceneGuard
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("智能压缩示例")


def format_size(size_bytes: int) -> str:
    """格式化文件大小
    
    Args:
        size_bytes: 字节大小
        
    Returns:
        str: 格式化后的大小
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


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


def demo_basic_compression(input_path: str, output_path: str) -> None:
    """基本压缩示例
    
    Args:
        input_path: 输入视频路径
        output_path: 输出视频路径
    """
    logger.info("=== 基本压缩示例 ===")
    
    start_time = time.time()
    result = compress_video(input_path, output_path)
    elapsed = time.time() - start_time
    
    # 打印结果
    logger.info(f"压缩完成，耗时: {elapsed:.2f}秒")
    logger.info(f"原始大小: {format_size(result['source_size'])}")
    logger.info(f"压缩后大小: {format_size(result['compressed_size'])}")
    logger.info(f"压缩率: {result['compression_ratio']:.2%}")
    logger.info(f"压缩方法: {result['method']}")


def demo_protected_compression(input_path: str, output_path: str, scene_file: str) -> None:
    """带保护的压缩示例
    
    Args:
        input_path: 输入视频路径
        output_path: 输出视频路径
        scene_file: 场景文件路径
    """
    logger.info("=== 带场景保护的压缩示例 ===")
    
    # 加载场景数据
    scenes = load_scenes(scene_file)
    if not scenes:
        logger.warning("无场景数据，将使用自动检测")
    
    # 标记关键场景
    scene_guard = KeySceneGuard()
    scenes = scene_guard.mark_protected(scenes)
    
    # 执行压缩
    start_time = time.time()
    result = compress_video(input_path, output_path, scene_data=scenes)
    elapsed = time.time() - start_time
    
    # 打印结果
    logger.info(f"带保护压缩完成，耗时: {elapsed:.2f}秒")
    logger.info(f"原始大小: {format_size(result['source_size'])}")
    logger.info(f"压缩后大小: {format_size(result['compressed_size'])}")
    logger.info(f"压缩率: {result['compression_ratio']:.2%}")
    logger.info(f"压缩方法: {result['method']}")
    if 'segments' in result:
        logger.info(f"处理的场景数量: {result['segments']}")


def demo_target_size_compression(input_path: str, output_path: str, target_size: str) -> None:
    """基于目标大小的压缩示例
    
    Args:
        input_path: 输入视频路径
        output_path: 输出视频路径
        target_size: 目标大小（百分比形式，如"50%"）
    """
    logger.info(f"=== 基于目标大小的压缩示例 (目标: {target_size}) ===")
    
    # 执行压缩
    start_time = time.time()
    result = compress_video(
        input_path, 
        output_path, 
        target_size=target_size
    )
    elapsed = time.time() - start_time
    
    # 打印结果
    logger.info(f"目标大小压缩完成，耗时: {elapsed:.2f}秒")
    logger.info(f"原始大小: {format_size(result['source_size'])}")
    logger.info(f"压缩后大小: {format_size(result['compressed_size'])}")
    logger.info(f"压缩率: {result['compression_ratio']:.2%}")
    logger.info(f"目标比特率: {result['target_bitrate']:.2f}kbps")
    logger.info(f"实际比特率: {result['result_bitrate']:.2f}kbps")


def demo_custom_compression(input_path: str, output_path: str, quality_preference: float) -> None:
    """自定义配置的压缩示例
    
    Args:
        input_path: 输入视频路径
        output_path: 输出视频路径
        quality_preference: 质量偏好（0.0-1.0）
    """
    logger.info(f"=== 自定义配置的压缩示例 (质量偏好: {quality_preference}) ===")
    
    # 创建自定义配置
    custom_config = {
        "base_crf": 20,                   # 更低的CRF，更好的质量
        "bitrate_factor": 0.8,            # 相对更高的码率
        "adaptive_quantization": "auto",  # 启用自适应量化
        "fast_start": True,               # 启用快速启动
        "max_threads": 4                  # 使用4个线程
    }
    
    # 创建压缩器
    compressor = SmartCompressor(custom_config)
    
    # 执行压缩
    start_time = time.time()
    result = compressor.dynamic_compress(
        input_path, 
        output_path, 
        quality_preference=quality_preference
    )
    elapsed = time.time() - start_time
    
    # 打印结果
    logger.info(f"自定义压缩完成，耗时: {elapsed:.2f}秒")
    logger.info(f"原始大小: {format_size(result['source_size'])}")
    logger.info(f"压缩后大小: {format_size(result['compressed_size'])}")
    logger.info(f"压缩率: {result['compression_ratio']:.2%}")
    logger.info(f"质量偏好: {quality_preference}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="智能压缩算法示例")
    parser.add_argument("input", help="输入视频文件路径")
    parser.add_argument("--output-dir", "-o", default="outputs", help="输出目录")
    parser.add_argument("--scene-file", "-s", help="场景数据文件路径")
    parser.add_argument("--demo-type", "-t", 
                        choices=["basic", "protected", "target_size", "custom", "all"],
                        default="all", 
                        help="示例类型")
    parser.add_argument("--target-size", default="50%", help="目标大小（百分比）")
    parser.add_argument("--quality", type=float, default=0.7, help="质量偏好（0.0-1.0）")
    
    args = parser.parse_args()
    
    # 检查输入文件
    if not os.path.exists(args.input):
        logger.error(f"输入文件不存在: {args.input}")
        return
    
    # 创建输出目录
    os.makedirs(args.output_dir, exist_ok=True)
    
    # 根据示例类型执行不同的演示
    if args.demo_type in ["basic", "all"]:
        output_path = os.path.join(args.output_dir, "basic_compressed.mp4")
        demo_basic_compression(args.input, output_path)
        logger.info(f"基本压缩输出: {output_path}")
    
    if args.demo_type in ["protected", "all"] and args.scene_file:
        output_path = os.path.join(args.output_dir, "protected_compressed.mp4")
        demo_protected_compression(args.input, output_path, args.scene_file)
        logger.info(f"带保护压缩输出: {output_path}")
    
    if args.demo_type in ["target_size", "all"]:
        output_path = os.path.join(args.output_dir, "target_size_compressed.mp4")
        demo_target_size_compression(args.input, output_path, args.target_size)
        logger.info(f"目标大小压缩输出: {output_path}")
    
    if args.demo_type in ["custom", "all"]:
        output_path = os.path.join(args.output_dir, "custom_compressed.mp4")
        demo_custom_compression(args.input, output_path, args.quality)
        logger.info(f"自定义压缩输出: {output_path}")
    
    logger.info("示例运行完成")


if __name__ == "__main__":
    main() 