#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
回退引擎演示

演示如何使用回退引擎管理处理模式，以及在资源不足时自动降级。
比较零拷贝和传统处理方法的性能差异。
"""

import os
import sys
import time
import argparse
import tempfile
import numpy as np
import cv2
import psutil
from pathlib import Path

# 添加项目根目录到模块搜索路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.utils.log_handler import get_logger
from src.exporters.fallback_engine import (
    FallbackEngine, 
    ProcessingMode, 
    ZeroCopyUnavailableError,
    safe_zero_copy, 
    get_memory_usage
)
from src.exporters.memmap_engine import get_memmap_engine

# 配置日志记录器
logger = get_logger("fallback_demo")

# 创建回退引擎
fallback_engine = FallbackEngine()


def zero_copy_video_process(video_path, start_frame=0, frame_count=None):
    """使用零拷贝方式处理视频
    
    Args:
        video_path: 视频文件路径
        start_frame: 起始帧
        frame_count: 处理帧数
        
    Returns:
        processed_frames: 处理后的帧
    """
    logger.info(f"使用零拷贝方式处理视频: {video_path}")
    start_time = time.time()
    
    try:
        # 检查是否真实视频文件路径或者是模拟数据
        if isinstance(video_path, np.ndarray) or isinstance(video_path, list):
            # 对模拟数据进行处理 - 使用视图而非复制
            frames = video_path if isinstance(video_path, np.ndarray) else np.array(video_path)
            
            processed_frames = []
            for i in range(len(frames)):
                # 获取帧视图
                frame_view = frames[i].view() if hasattr(frames[i], 'view') else frames[i]
                
                # 进行处理（使用视图而非复制）
                if len(frame_view.shape) == 3 and frame_view.shape[2] == 3:
                    gray = cv2.cvtColor(frame_view, cv2.COLOR_BGR2GRAY)
                else:
                    gray = frame_view  # 已经是灰度图
                
                blurred = cv2.GaussianBlur(gray, (5, 5), 0)
                edges = cv2.Canny(blurred, 50, 150)
                
                processed_frames.append(edges)
            
            end_time = time.time()
            logger.info(f"零拷贝处理完成: 处理了 {len(processed_frames)} 帧")
            logger.info(f"处理时间: {end_time - start_time:.4f} 秒")
            
            return processed_frames
    
        # 真实视频文件处理
        memmap_engine = get_memmap_engine()
        
        # 使用内存映射获取视频帧
        frames, _ = memmap_engine.map_video_frames(
            video_path, 
            start_frame=start_frame, 
            frame_count=frame_count
        )
        
        if frames is None or frames.size == 0:
            logger.error("零拷贝映射帧失败")
            raise ZeroCopyUnavailableError("无法映射视频帧")
        
        # 处理帧 - 使用视图而非复制
        processed_frames = []
        for i in range(frames.shape[0]):
            # 获取帧视图
            frame_view = frames[i]
            
            # 进行处理（使用视图而非复制）
            gray = cv2.cvtColor(frame_view, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            edges = cv2.Canny(blurred, 50, 150)
            
            processed_frames.append(edges)
        
        end_time = time.time()
        logger.info(f"零拷贝处理完成: 处理了 {len(processed_frames)} 帧")
        logger.info(f"处理时间: {end_time - start_time:.4f} 秒")
        
        return processed_frames
        
    except Exception as e:
        logger.error(f"零拷贝处理出错: {str(e)}")
        raise ZeroCopyUnavailableError(f"零拷贝处理失败: {str(e)}")


def traditional_video_process(video_path, start_frame=0, frame_count=None):
    """使用传统方式处理视频
    
    Args:
        video_path: 视频文件路径
        start_frame: 起始帧
        frame_count: 处理帧数
        
    Returns:
        processed_frames: 处理后的帧
    """
    logger.info(f"使用传统方式处理视频: {video_path}")
    start_time = time.time()
    
    try:
        # 检查是否真实视频文件路径或者是模拟数据
        if isinstance(video_path, np.ndarray) or isinstance(video_path, list):
            # 对模拟数据进行处理 - 复制数据处理
            frames = video_path if isinstance(video_path, np.ndarray) else np.array(video_path)
            
            processed_frames = []
            for i in range(len(frames)):
                # 复制帧
                frame_copy = frames[i].copy()
                
                # 进行处理
                if len(frame_copy.shape) == 3 and frame_copy.shape[2] == 3:
                    gray = cv2.cvtColor(frame_copy, cv2.COLOR_BGR2GRAY)
                else:
                    gray = frame_copy  # 已经是灰度图
                
                blurred = cv2.GaussianBlur(gray, (5, 5), 0)
                edges = cv2.Canny(blurred, 50, 150)
                
                processed_frames.append(edges)
            
            end_time = time.time()
            logger.info(f"传统处理完成: 处理了 {len(processed_frames)} 帧")
            logger.info(f"处理时间: {end_time - start_time:.4f} 秒")
            
            return processed_frames
            
        # 真实视频文件处理
        # 打开视频
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.error(f"无法打开视频: {video_path}")
            return []
        
        # 获取视频属性
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if frame_count is None:
            frame_count = total_frames - start_frame
        
        # 限制帧数
        frame_count = min(frame_count, total_frames - start_frame)
        
        # 设置起始帧
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        
        processed_frames = []
        # 读取并处理帧
        for _ in range(frame_count):
            ret, frame = cap.read()
            if not ret:
                break
                
            # 进行处理
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            edges = cv2.Canny(blurred, 50, 150)
            
            # 将处理后的帧追加到列表
            processed_frames.append(edges)
            
        # 释放视频
        cap.release()
        
        end_time = time.time()
        logger.info(f"传统方式处理完成: 处理了 {len(processed_frames)} 帧")
        logger.info(f"处理时间: {end_time - start_time:.4f} 秒")
        
        return processed_frames
        
    except Exception as e:
        logger.error(f"传统处理方法出错: {e}")
        return []


def generate_test_frames(frame_count=30, width=640, height=480):
    """生成测试用的视频帧数据
    
    Args:
        frame_count: 生成的帧数
        width: 帧宽度
        height: 帧高度
        
    Returns:
        frames: 生成的帧数据
    """
    logger.info(f"生成{frame_count}帧测试数据，分辨率: {width}x{height}")
    
    frames = []
    for i in range(frame_count):
        # 创建随机颜色帧
        frame = np.random.randint(0, 255, (height, width, 3), dtype=np.uint8)
        
        # 添加一些结构以便于处理后可以看到差异
        cv2.putText(
            frame, 
            f"Frame #{i}", 
            (50, 50), 
            cv2.FONT_HERSHEY_SIMPLEX, 
            1, 
            (255, 255, 255), 
            2
        )
        
        # 绘制一些随机形状
        for _ in range(5):
            # 随机圆
            center = (
                np.random.randint(0, width), 
                np.random.randint(0, height)
            )
            radius = np.random.randint(20, 100)
            color = (
                np.random.randint(0, 255), 
                np.random.randint(0, 255), 
                np.random.randint(0, 255)
            )
            cv2.circle(frame, center, radius, color, -1)
        
        frames.append(frame)
    
    return frames


def run_performance_comparison(video_path, start_frame=0, frame_count=30):
    """运行性能比较测试
    
    Args:
        video_path: 视频文件路径
        start_frame: 起始帧
        frame_count: 处理帧数
    """
    logger.info("=== 性能比较测试 ===")
    
    # 如果video_path是None或找不到，生成测试数据
    if video_path is None or (isinstance(video_path, str) and not os.path.exists(video_path)):
        logger.info("没有找到视频文件，使用生成的测试数据")
        test_data = generate_test_frames(frame_count)
        video_path = test_data
    
    logger.info(f"视频: {'模拟数据' if isinstance(video_path, list) else video_path}, 起始帧: {start_frame}, 帧数: {frame_count}")
    
    # 注册处理器
    fallback_engine.register_processor(
        "video_processor",
        zero_copy_video_process,
        traditional_video_process
    )
    
    # 测试不同处理模式
    modes = [
        (ProcessingMode.TRADITIONAL, "传统模式"),
        (ProcessingMode.ZERO_COPY, "零拷贝模式"),
        (ProcessingMode.AUTO, "自动模式")
    ]
    
    for mode, name in modes:
        logger.info(f"\n--- 测试 {name} ---")
        
        # 记录开始状态
        start_mem = get_memory_usage()
        start_time = time.time()
        
        try:
            # 使用回退引擎处理
            frames = fallback_engine.process_with_fallback(
                "video_processor",
                video_path,
                mode=mode,
                start_frame=start_frame,
                frame_count=frame_count
            )
            
            # 记录结束状态
            end_time = time.time()
            end_mem = get_memory_usage()
            
            logger.info(f"处理结果: {len(frames) if frames else 0} 帧")
            logger.info(f"处理时间: {end_time - start_time:.4f} 秒")
            logger.info(f"内存使用率变化: {start_mem:.1%} -> {end_mem:.1%}")
            
        except Exception as e:
            logger.error(f"处理失败: {e}")
    
    # 打印回退状态
    logger.info("\n=== 回退引擎状态 ===")
    status = fallback_engine.get_fallback_status()
    for key, value in status.items():
        logger.info(f"{key}: {value}")


def simulate_memory_pressure(size_mb=1000):
    """模拟内存压力
    
    Args:
        size_mb: 分配内存大小(MB)
    
    Returns:
        allocated_data: 分配的数据，用于防止被垃圾回收
    """
    logger.info(f"模拟内存压力: 分配 {size_mb}MB 内存")
    try:
        # 分配指定大小的内存
        data = [np.ones((1024, 1024), dtype=np.float32) for _ in range(size_mb)]
        logger.info(f"内存分配完成, 当前内存使用率: {get_memory_usage():.1%}")
        return data
    except Exception as e:
        logger.error(f"内存分配失败: {e}")
        return None


def test_safe_zero_copy(video_path, start_frame=0, frame_count=30):
    """测试安全零拷贝函数
    
    Args:
        video_path: 视频文件路径
        start_frame: 起始帧
        frame_count: 处理帧数
    """
    logger.info("=== 测试安全零拷贝函数 ===")
    
    # 如果video_path是None或找不到，生成测试数据
    if video_path is None or (isinstance(video_path, str) and not os.path.exists(video_path)):
        logger.info("没有找到视频文件，使用生成的测试数据")
        test_data = generate_test_frames(frame_count)
        video_path = test_data
    
    # 修复零拷贝处理和传统处理方法
    global zero_copy_process, traditional_process
    from types import MethodType
    
    # 将具体实现绑定到全局接口
    import src.exporters.fallback_engine as fe
    fe.zero_copy_process = lambda x: zero_copy_video_process(
        x, start_frame=start_frame, frame_count=frame_count
    )
    fe.traditional_process = lambda x: traditional_video_process(
        x, start_frame=start_frame, frame_count=frame_count
    )
    
    # 正常情况
    logger.info("--- 正常情况 ---")
    try:
        # 使用带回退的安全方法
        result = safe_zero_copy(video_path, fallback_threshold=0.9)
        logger.info(f"处理成功: {len(result) if result else 0} 帧")
    except Exception as e:
        logger.error(f"处理失败: {e}")
    
    # 内存压力情况
    logger.info("\n--- 内存压力情况 ---")
    try:
        # 模拟内存压力
        data = simulate_memory_pressure(500)
        
        # 使用带回退的安全方法
        result = safe_zero_copy(video_path, fallback_threshold=0.9)
        logger.info(f"处理成功: {len(result) if result else 0} 帧")
    except Exception as e:
        logger.error(f"处理失败: {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="回退引擎演示")
    parser.add_argument("--video", type=str, help="视频文件路径")
    parser.add_argument("--frames", type=int, default=30, help="处理帧数")
    parser.add_argument("--start", type=int, default=0, help="起始帧")
    parser.add_argument("--test", choices=["performance", "fallback", "pressure"], 
                        default="performance", help="测试类型")
    args = parser.parse_args()
    
    # 如果没有提供视频，尝试使用测试视频或生成测试数据
    video_path = args.video
    if not video_path or not os.path.exists(video_path):
        # 查找测试视频
        test_videos = [
            os.path.join("samples", "videos", "test.mp4"),
            os.path.join("test", "samples", "test.mp4"),
            os.path.join("data", "samples", "test.mp4")
        ]
        
        for test_video in test_videos:
            if os.path.exists(test_video):
                video_path = test_video
                break
                
        if not video_path or not os.path.exists(video_path):
            # 找不到视频文件时不报错，让各函数自行生成测试数据
            video_path = None
    
    # 运行所选测试
    if args.test == "performance":
        run_performance_comparison(video_path, args.start, args.frames)
    elif args.test == "fallback":
        test_safe_zero_copy(video_path, args.start, args.frames)
    elif args.test == "pressure":
        # 先模拟内存压力
        mem_data = simulate_memory_pressure(1500)
        # 然后运行性能比较
        run_performance_comparison(video_path, args.start, args.frames)


if __name__ == "__main__":
    main() 