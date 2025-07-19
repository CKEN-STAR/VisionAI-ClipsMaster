#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
内存映射引擎演示脚本

演示内存映射引擎如何提高视频处理性能并降低内存占用。
对比使用内存映射与常规方法处理视频文件的效率差异。
"""

import os
import sys
import time
import argparse
import cv2
import numpy as np
import psutil
import matplotlib.pyplot as plt
from pathlib import Path

# 添加项目根目录到路径
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

from src.exporters.memmap_engine import (
    get_memmap_engine,
    map_video_frames
)
from src.utils.log_handler import get_logger

# 配置日志记录器
logger = get_logger("memmap_demo")


def process_video_traditional(video_path, start_frame=0, frame_count=None):
    """使用传统方法处理视频
    
    Args:
        video_path: 视频文件路径
        start_frame: 起始帧索引
        frame_count: 要处理的帧数
        
    Returns:
        tuple: (处理时间, 最大内存使用)
    """
    logger.info(f"使用传统方法处理视频: {video_path}")
    
    # 记录初始内存使用
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss / (1024 * 1024)  # MB
    
    start_time = time.time()
    max_memory_usage = initial_memory
    
    try:
        # 打开视频
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.error(f"无法打开视频: {video_path}")
            return 0, 0
        
        # 获取视频属性
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if frame_count is None:
            frame_count = total_frames - start_frame
        
        # 限制帧数
        frame_count = min(frame_count, total_frames - start_frame)
        
        # 设置起始帧
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        
        frames = []
        # 读取并处理帧
        for _ in range(frame_count):
            ret, frame = cap.read()
            if not ret:
                break
                
            # 进行一些处理（例如灰度转换）
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            # 应用高斯模糊
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            # 边缘检测
            edges = cv2.Canny(blurred, 50, 150)
            
            # 将处理后的帧追加到列表
            frames.append(edges)
            
            # 记录内存使用
            current_memory = process.memory_info().rss / (1024 * 1024)
            max_memory_usage = max(max_memory_usage, current_memory)
            
        # 释放视频
        cap.release()
        
        # 将帧转换为数组（可能导致额外的内存使用）
        if frames:
            frames_array = np.array(frames)
            # 记录最终内存使用
            current_memory = process.memory_info().rss / (1024 * 1024)
            max_memory_usage = max(max_memory_usage, current_memory)
            
        end_time = time.time()
        processing_time = end_time - start_time
        
        logger.info(f"传统方法处理完成: 处理了 {len(frames)} 帧")
        logger.info(f"处理时间: {processing_time:.4f} 秒")
        logger.info(f"最大内存使用: {max_memory_usage:.2f} MB")
        
        return processing_time, max_memory_usage
        
    except Exception as e:
        logger.error(f"传统处理方法出错: {e}")
        return 0, 0


def process_video_memmap(video_path, start_frame=0, frame_count=None):
    """使用内存映射处理视频
    
    Args:
        video_path: 视频文件路径
        start_frame: 起始帧索引
        frame_count: 要处理的帧数
        
    Returns:
        tuple: (处理时间, 最大内存使用)
    """
    logger.info(f"使用内存映射处理视频: {video_path}")
    
    # 记录初始内存使用
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss / (1024 * 1024)  # MB
    
    start_time = time.time()
    max_memory_usage = initial_memory
    
    try:
        # 获取内存映射引擎
        engine = get_memmap_engine()
        
        # 使用内存映射读取视频帧
        frames, actual_frame_count = engine.map_video_frames(
            video_path, start_frame, frame_count
        )
        
        if actual_frame_count == 0:
            logger.error("未能读取任何帧")
            return 0, 0
        
        # 记录当前内存使用
        current_memory = process.memory_info().rss / (1024 * 1024)
        max_memory_usage = max(max_memory_usage, current_memory)
        
        # 处理帧
        processed_frames = []
        for i in range(actual_frame_count):
            # 进行相同的处理操作
            frame = frames[i]
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            edges = cv2.Canny(blurred, 50, 150)
            
            processed_frames.append(edges)
            
            # 记录内存使用
            current_memory = process.memory_info().rss / (1024 * 1024)
            max_memory_usage = max(max_memory_usage, current_memory)
        
        # 转换为数组
        if processed_frames:
            processed_array = np.array(processed_frames)
            # 记录最终内存使用
            current_memory = process.memory_info().rss / (1024 * 1024)
            max_memory_usage = max(max_memory_usage, current_memory)
        
        # 清理引擎
        engine.clear_all()
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        logger.info(f"内存映射方法处理完成: 处理了 {actual_frame_count} 帧")
        logger.info(f"处理时间: {processing_time:.4f} 秒")
        logger.info(f"最大内存使用: {max_memory_usage:.2f} MB")
        
        # 返回性能统计
        return processing_time, max_memory_usage
        
    except Exception as e:
        logger.error(f"内存映射处理方法出错: {e}")
        return 0, 0


def compare_methods(video_path, frame_count=100):
    """比较两种方法的性能
    
    Args:
        video_path: 视频文件路径
        frame_count: 要处理的帧数
    """
    logger.info("开始性能比较...")
    
    # 使用传统方法
    trad_time, trad_memory = process_video_traditional(video_path, 0, frame_count)
    
    # 短暂暂停，让系统恢复
    time.sleep(2)
    
    # 强制垃圾回收
    import gc
    gc.collect()
    
    # 使用内存映射方法
    mmap_time, mmap_memory = process_video_memmap(video_path, 0, frame_count)
    
    # 比较结果
    if trad_time > 0 and mmap_time > 0:
        time_improvement = (trad_time - mmap_time) / trad_time * 100
        memory_improvement = (trad_memory - mmap_memory) / trad_memory * 100
        
        logger.info("\n性能比较结果:")
        logger.info(f"时间效率提升: {time_improvement:.2f}%")
        logger.info(f"内存使用减少: {memory_improvement:.2f}%")
        
        # 绘制比较图表
        plot_comparison(trad_time, mmap_time, trad_memory, mmap_memory)
    else:
        logger.error("无法进行有效比较，处理过程出错")


def plot_comparison(trad_time, mmap_time, trad_memory, mmap_memory):
    """绘制性能比较图表
    
    Args:
        trad_time: 传统方法处理时间
        mmap_time: 内存映射方法处理时间
        trad_memory: 传统方法内存使用
        mmap_memory: 内存映射方法内存使用
    """
    try:
        # 创建图表
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        # 处理时间比较
        methods = ['传统方法', '内存映射方法']
        times = [trad_time, mmap_time]
        bars1 = ax1.bar(methods, times, color=['blue', 'green'])
        ax1.set_title('处理时间比较 (秒)')
        ax1.set_ylabel('时间 (秒)')
        ax1.grid(axis='y', linestyle='--', alpha=0.7)
        
        # 添加数据标签
        for bar in bars1:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.2f}s',
                    ha='center', va='bottom')
            
        # 内存使用比较
        memories = [trad_memory, mmap_memory]
        bars2 = ax2.bar(methods, memories, color=['blue', 'green'])
        ax2.set_title('内存使用比较 (MB)')
        ax2.set_ylabel('内存 (MB)')
        ax2.grid(axis='y', linestyle='--', alpha=0.7)
        
        # 添加数据标签
        for bar in bars2:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.1f}MB',
                    ha='center', va='bottom')
        
        # 调整布局
        plt.tight_layout()
        
        # 保存图表
        os.makedirs("outputs", exist_ok=True)
        plt.savefig("outputs/memmap_performance_comparison.png")
        logger.info("性能比较图表已保存至 outputs/memmap_performance_comparison.png")
        
        # 显示图表
        plt.show()
        
    except Exception as e:
        logger.error(f"绘制图表出错: {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="内存映射引擎演示")
    parser.add_argument("--video", type=str, required=True,
                        help="视频文件路径")
    parser.add_argument("--frames", type=int, default=100,
                        help="要处理的帧数 (默认: 100)")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.video):
        logger.error(f"视频文件不存在: {args.video}")
        return
    
    # 比较两种方法
    compare_methods(args.video, args.frames)
    
    # 获取引擎统计信息
    engine = get_memmap_engine()
    stats = engine.get_stats()
    
    logger.info("\n内存映射引擎统计:")
    for key, value in stats.items():
        logger.info(f"{key}: {value}")


if __name__ == "__main__":
    main() 