#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据流分析示例程序

展示如何使用数据流分析器来识别和优化性能瓶颈
"""

import os
import sys
import time
import random
import argparse
from pathlib import Path
from typing import List, Dict, Any

# 添加项目根目录到路径
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

from src.exporters.dataflow_analyzer import (
    start_profiling, stop_profiling, profile_operation,
    get_memory_usage, summarize_performance, visualization_helper
)
from src.utils.log_handler import get_logger

# 配置日志
logger = get_logger("dataflow_example")

# 模拟视频数据
class VideoFrame:
    """模拟视频帧类"""
    def __init__(self, frame_number: int, width: int = 1920, height: int = 1080):
        self.frame_number = frame_number
        self.width = width
        self.height = height
        # 模拟帧数据 (RGB数据，每像素3字节)
        self.data = bytearray(width * height * 3)
        
    def size_mb(self) -> float:
        """返回帧大小(MB)"""
        return len(self.data) / (1024 * 1024)


@profile_operation(module='video_processing', category='io')
def load_frames(count: int, width: int = 1920, height: int = 1080) -> List[VideoFrame]:
    """模拟从文件加载视频帧
    
    Args:
        count: 帧数量
        width: 帧宽度
        height: 帧高度
        
    Returns:
        List[VideoFrame]: 视频帧列表
    """
    logger.info(f"加载 {count} 帧视频数据...")
    frames = []
    
    # 模拟IO延迟
    time.sleep(0.5)
    
    for i in range(count):
        frames.append(VideoFrame(i, width, height))
        # 模拟每帧的加载时间
        time.sleep(0.01)
    
    return frames


@profile_operation(module='video_processing', category='cpu')
def process_frames(frames: List[VideoFrame]) -> List[VideoFrame]:
    """模拟处理视频帧
    
    Args:
        frames: 输入视频帧列表
        
    Returns:
        List[VideoFrame]: 处理后的视频帧
    """
    logger.info(f"处理 {len(frames)} 帧视频数据...")
    processed_frames = []
    
    for frame in frames:
        # 模拟复杂的帧处理
        processed_frame = VideoFrame(frame.frame_number, frame.width, frame.height)
        
        # 模拟计算密集型操作
        for _ in range(frame.width * frame.height // 100000):  # 降低循环次数以加快演示
            sum([i*i for i in range(100)])
        
        processed_frames.append(processed_frame)
    
    return processed_frames


@profile_operation(module='video_processing', category='memory')
def merge_frames(frames: List[VideoFrame]) -> bytes:
    """模拟将帧合并为视频流
    
    Args:
        frames: 视频帧列表
        
    Returns:
        bytes: 合并后的视频数据
    """
    logger.info(f"合并 {len(frames)} 帧为视频流...")
    
    # 创建一个大的字节数组来模拟大内存使用
    merged_data = bytearray()
    
    for frame in frames:
        # 模拟复制框架数据 - 这是一个数据复制热点
        merged_data.extend(frame.data)
    
    # 模拟IO操作
    time.sleep(0.2)
    
    return bytes(merged_data)


@profile_operation(module='video_processing', category='io')
def save_video(data: bytes, output_path: str) -> str:
    """模拟保存视频数据到文件
    
    Args:
        data: 视频数据
        output_path: 输出文件路径
        
    Returns:
        str: 保存的文件路径
    """
    logger.info(f"保存视频数据到 {output_path}...")
    
    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # 模拟写入延迟 - 根据数据大小调整
    time.sleep(len(data) / (50 * 1024 * 1024))  # 假设50MB/s的写入速度
    
    # 实际上不写入数据，只是创建空文件
    with open(output_path, 'wb') as f:
        f.write(b'DEMO')  # 只写入一个标记，而不是全部数据
    
    return output_path


@profile_operation(module='video_processing', category='cpu')
def optimize_color(frames: List[VideoFrame]) -> List[VideoFrame]:
    """模拟优化帧的颜色
    
    Args:
        frames: 输入视频帧列表
        
    Returns:
        List[VideoFrame]: 处理后的视频帧
    """
    logger.info(f"优化 {len(frames)} 帧的颜色...")
    optimized_frames = []
    
    for frame in frames:
        # 复制帧
        optimized_frame = VideoFrame(frame.frame_number, frame.width, frame.height)
        
        # 模拟颜色优化处理
        time.sleep(0.05)  # 假设每帧需要50ms
        
        optimized_frames.append(optimized_frame)
    
    return optimized_frames


@profile_operation(module='video_processing', category='io')
def create_thumbnail(frames: List[VideoFrame], output_path: str) -> str:
    """从视频帧创建缩略图
    
    Args:
        frames: 视频帧列表
        output_path: 输出文件路径
        
    Returns:
        str: 缩略图文件路径
    """
    logger.info("创建视频缩略图...")
    
    # 选择中间的帧作为缩略图
    middle_frame = frames[len(frames) // 2]
    
    # 模拟缩略图创建
    time.sleep(0.1)
    
    # 确保输出目录存在
    thumbnail_path = os.path.splitext(output_path)[0] + "_thumbnail.jpg"
    os.makedirs(os.path.dirname(thumbnail_path), exist_ok=True)
    
    # 创建空缩略图文件
    with open(thumbnail_path, 'wb') as f:
        f.write(b'THUMBNAIL')
    
    return thumbnail_path


def run_video_processing(frame_count: int, output_path: str, with_optimization: bool = False) -> Dict[str, Any]:
    """运行视频处理流程
    
    Args:
        frame_count: 处理的帧数量
        output_path: 输出文件路径
        with_optimization: 是否启用优化
        
    Returns:
        Dict: 处理结果信息
    """
    # 开始性能分析
    start_profiling('video_processing')
    start_time = time.time()
    initial_memory = get_memory_usage()
    
    try:
        # 步骤1: 加载帧
        frames = load_frames(frame_count)
        
        # 记录内存使用
        memory_after_load = get_memory_usage()
        
        # 步骤2: 处理帧
        processed_frames = process_frames(frames)
        
        # 步骤3: 可选的优化
        if with_optimization:
            processed_frames = optimize_color(processed_frames)
        
        # 记录内存使用
        memory_after_process = get_memory_usage()
        
        # 步骤4: 合并帧
        video_data = merge_frames(processed_frames)
        
        # 步骤5: 保存视频
        saved_path = save_video(video_data, output_path)
        
        # 步骤6: 创建缩略图
        thumbnail_path = create_thumbnail(processed_frames, output_path)
        
        # 记录最终内存
        final_memory = get_memory_usage()
        
        return {
            'output_path': saved_path,
            'thumbnail_path': thumbnail_path,
            'frame_count': frame_count,
            'optimization_enabled': with_optimization,
            'initial_memory_mb': initial_memory,
            'memory_after_load_mb': memory_after_load,
            'memory_after_process_mb': memory_after_process,
            'final_memory_mb': final_memory,
            'total_memory_change_mb': final_memory - initial_memory
        }
    
    finally:
        # 停止性能分析
        end_time = time.time()
        profile_data = stop_profiling('video_processing')
        
        if profile_data:
            # 设置元数据
            profile_data.set_metadata('frame_count', frame_count)
            profile_data.set_metadata('optimization_enabled', with_optimization)
            profile_data.set_metadata('data_size_mb', sum(frame.size_mb() for frame in frames))
            
            # 保存性能数据
            profile_path = os.path.splitext(output_path)[0] + "_profile.json"
            profile_data.save_to_file(profile_path)
            
            # 生成性能摘要
            summary = summarize_performance('video_processing')
            logger.info(f"处理完成，总耗时: {end_time - start_time:.2f}秒")
            logger.info(f"性能摘要: {summary}")
            
            # 生成可视化报告
            try:
                viz_path = visualization_helper('video_processing', 
                                       os.path.splitext(output_path)[0] + "_viz.png")
                if viz_path:
                    logger.info(f"性能可视化图表已生成: {viz_path}")
            except Exception as viz_error:
                logger.warning(f"生成可视化报告失败: {viz_error}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="数据流分析示例程序")
    parser.add_argument("--frames", type=int, default=30, help="处理的帧数量")
    parser.add_argument("--output", default="outputs/processed_video.mp4", help="输出文件路径")
    parser.add_argument("--optimize", action="store_true", help="启用额外的颜色优化")
    
    args = parser.parse_args()
    
    # 设置输出路径
    output_path = args.output
    if not os.path.isabs(output_path):
        output_path = os.path.join(project_root, output_path)
    
    logger.info(f"启动视频处理示例，帧数: {args.frames}")
    logger.info(f"优化模式: {'启用' if args.optimize else '禁用'}")
    
    # 运行处理
    result = run_video_processing(args.frames, output_path, args.optimize)
    
    # 输出结果
    logger.info("\n处理结果摘要:")
    logger.info(f"  - 输出文件: {result['output_path']}")
    logger.info(f"  - 缩略图: {result['thumbnail_path']}")
    logger.info(f"  - 内存使用变化: {result['total_memory_change_mb']:.2f}MB")
    logger.info(f"  - 帧数: {result['frame_count']}")


 