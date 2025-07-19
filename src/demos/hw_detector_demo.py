#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
硬件检测器演示

演示如何检测和使用系统中可用的硬件加速能力。
展示智能选择最佳处理方式的功能。
"""

import os
import sys
import time
import argparse
import numpy as np
import cv2

# 添加项目根目录到模块搜索路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.utils.log_handler import get_logger
from src.exporters.hw_detector import (
    AccelerationType,
    detect_zero_copy_acceleration,
    check_nvidia_support,
    check_intel_qsv,
    get_cuda_device_info,
    get_detected_acceleration,
    print_acceleration_report
)

# 配置日志记录器
logger = get_logger("hw_detector_demo")


def main():
    """硬件检测器演示主函数"""
    parser = argparse.ArgumentParser(description="硬件加速检测演示")
    parser.add_argument("--benchmark", action="store_true", help="运行基准测试")
    parser.add_argument("--video", type=str, help="用于测试的视频文件路径")
    args = parser.parse_args()
    
    # 打印硬件加速报告
    logger.info("正在检测系统硬件加速能力...")
    print_acceleration_report()
    
    # 获取加速能力
    acceleration = get_detected_acceleration()
    
    # 选择最佳加速方式
    accelerator = select_best_accelerator(acceleration)
    logger.info(f"选择的最佳加速方式: {accelerator}")
    
    # 运行基准测试
    if args.benchmark:
        if args.video and os.path.exists(args.video):
            run_benchmark(args.video, acceleration)
        else:
            logger.error("要运行基准测试，请提供有效的视频文件路径")
            if not args.video:
                logger.info("示例用法: python hw_detector_demo.py --benchmark --video path/to/video.mp4")
            else:
                logger.error(f"视频文件不存在: {args.video}")


def select_best_accelerator(acceleration):
    """选择最佳加速器
    
    基于系统检测结果，智能选择最佳加速方式
    
    Args:
        acceleration: 加速能力字典
        
    Returns:
        str: 最佳加速方式名称
    """
    # 优先级: NVIDIA > Intel QSV > CPU AVX2 > 标准CPU
    if acceleration[AccelerationType.NVIDIA_CUDA]:
        return "NVIDIA CUDA/NVDEC"
    elif acceleration[AccelerationType.INTEL_QSV]:
        return "Intel Quick Sync Video"
    elif acceleration[AccelerationType.CPU_AVX2]:
        return "CPU AVX2"
    else:
        return "标准CPU处理"


def run_benchmark(video_path, acceleration):
    """运行视频处理基准测试
    
    对比不同加速方式的性能差异
    
    Args:
        video_path: 测试视频路径
        acceleration: 加速能力字典
    """
    logger.info(f"使用视频 {video_path} 运行基准测试...")
    
    # 打开视频文件
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        logger.error(f"无法打开视频文件: {video_path}")
        return
    
    # 获取视频信息
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    logger.info(f"视频信息: {width}x{height}, {frame_count}帧, {fps}FPS")
    
    # 测试设置
    test_frame_count = min(frame_count, 300)  # 最多测试300帧
    logger.info(f"将处理 {test_frame_count} 帧进行基准测试")
    
    # 基准测试: 标准CPU处理
    logger.info("运行标准CPU处理基准测试...")
    run_standard_cpu_benchmark(cap, test_frame_count)
    
    # 重置视频
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    
    # 基准测试: 使用CPU优化
    if acceleration[AccelerationType.CPU_AVX2]:
        logger.info("运行CPU AVX2优化基准测试...")
        run_avx_benchmark(cap, test_frame_count)
        # 重置视频
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    
    # 基准测试: 使用GPU (如果可用)
    if acceleration[AccelerationType.NVIDIA_CUDA]:
        logger.info("运行NVIDIA CUDA基准测试...")
        run_cuda_benchmark(cap, test_frame_count)
    
    # 释放资源
    cap.release()


def run_standard_cpu_benchmark(cap, frame_count):
    """运行标准CPU处理基准测试
    
    Args:
        cap: 视频捕获对象
        frame_count: 要处理的帧数
    """
    start_time = time.time()
    processed_frames = 0
    
    # 处理指定数量的帧
    while processed_frames < frame_count:
        ret, frame = cap.read()
        if not ret:
            break
        
        # 标准CPU处理: 高斯模糊
        processed = cv2.GaussianBlur(frame, (15, 15), 0)
        
        # 标准CPU处理: 边缘检测
        gray = cv2.cvtColor(processed, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        
        processed_frames += 1
    
    elapsed_time = time.time() - start_time
    fps = processed_frames / elapsed_time if elapsed_time > 0 else 0
    
    logger.info(f"标准CPU处理: {processed_frames} 帧用时 {elapsed_time:.2f} 秒 ({fps:.2f} FPS)")


def run_avx_benchmark(cap, frame_count):
    """运行AVX优化基准测试
    
    Args:
        cap: 视频捕获对象
        frame_count: 要处理的帧数
    """
    # OpenCV通常已针对AVX2进行了优化，这里我们使用多线程处理来进一步提高性能
    import threading
    
    def process_frame(frame):
        # 高斯模糊
        processed = cv2.GaussianBlur(frame, (15, 15), 0)
        # 边缘检测
        gray = cv2.cvtColor(processed, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        return edges
    
    start_time = time.time()
    processed_frames = 0
    max_threads = 4
    active_threads = []
    
    # 处理指定数量的帧
    while processed_frames < frame_count:
        # 如果活动线程达到上限，等待一些线程完成
        while len(active_threads) >= max_threads:
            active_threads = [t for t in active_threads if t.is_alive()]
            if len(active_threads) >= max_threads:
                time.sleep(0.01)
        
        ret, frame = cap.read()
        if not ret:
            break
        
        # 创建处理线程
        thread = threading.Thread(target=process_frame, args=(frame.copy(),))
        thread.start()
        active_threads.append(thread)
        
        processed_frames += 1
    
    # 等待所有线程完成
    for thread in active_threads:
        thread.join()
    
    elapsed_time = time.time() - start_time
    fps = processed_frames / elapsed_time if elapsed_time > 0 else 0
    
    logger.info(f"CPU AVX2优化处理: {processed_frames} 帧用时 {elapsed_time:.2f} 秒 ({fps:.2f} FPS)")


def run_cuda_benchmark(cap, frame_count):
    """运行CUDA优化基准测试
    
    Args:
        cap: 视频捕获对象
        frame_count: 要处理的帧数
    """
    try:
        # 尝试导入CUDA模块
        import cv2
        
        # 检查是否有CUDA支持的OpenCV
        if cv2.cuda.getCudaEnabledDeviceCount() == 0:
            logger.warning("OpenCV未启用CUDA支持")
            return
        
        # 创建CUDA流
        stream = cv2.cuda_Stream()
        
        # 创建CUDA滤镜
        gaussian_filter = cv2.cuda.createGaussianFilter(
            cv2.CV_8UC3, cv2.CV_8UC3, (15, 15), 0
        )
        
        start_time = time.time()
        processed_frames = 0
        
        # 处理指定数量的帧
        while processed_frames < frame_count:
            ret, frame = cap.read()
            if not ret:
                break
            
            # 上传到GPU
            gpu_frame = cv2.cuda_GpuMat()
            gpu_frame.upload(frame)
            
            # CUDA处理: 高斯模糊
            gpu_blurred = cv2.cuda_GpuMat()
            gaussian_filter.apply(gpu_frame, gpu_blurred, stream)
            
            # CUDA处理: 边缘检测
            gpu_gray = cv2.cuda.cvtColor(gpu_blurred, cv2.COLOR_BGR2GRAY, stream=stream)
            gpu_edges = cv2.cuda.createCannyEdgeDetector(50, 150).detect(gpu_gray, stream=stream)
            
            # 下载结果
            edges = gpu_edges.download()
            
            processed_frames += 1
        
        elapsed_time = time.time() - start_time
        fps = processed_frames / elapsed_time if elapsed_time > 0 else 0
        
        logger.info(f"CUDA优化处理: {processed_frames} 帧用时 {elapsed_time:.2f} 秒 ({fps:.2f} FPS)")
    
    except Exception as e:
        logger.error(f"CUDA基准测试失败: {e}")
        logger.info("可能需要安装支持CUDA的OpenCV版本")


if __name__ == "__main__":
    main() 