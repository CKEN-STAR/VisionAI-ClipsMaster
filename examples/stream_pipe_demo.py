#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
流式处理管道示例脚本

演示如何使用流式处理管道进行视频处理
"""

import os
import sys
import time
import numpy as np
from pathlib import Path

# 添加项目根目录到路径
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

from src.utils.log_handler import get_logger
from src.exporters.stream_pipe import (
    ZeroCopyPipeline,
    StreamingPipeline,
    Processor,
    VideoProcessor,
    FilterProcessor,
    create_processor,
    ProcessingMode
)

# 配置日志记录器
logger = get_logger("stream_pipe_demo")


class GrayscaleConverter(VideoProcessor):
    """灰度转换处理器"""
    
    def __init__(self):
        """初始化灰度转换处理器"""
        super().__init__("GrayscaleConverter")
    
    def process_frame(self, frame):
        """将彩色帧转换为灰度"""
        import cv2
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # 保持三通道格式，避免后续处理兼容性问题
        return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)


class BlurProcessor(VideoProcessor):
    """模糊处理器"""
    
    def __init__(self, kernel_size=5):
        """初始化模糊处理器
        
        Args:
            kernel_size: 模糊核大小
        """
        super().__init__("BlurProcessor")
        self.kernel_size = kernel_size
    
    def process_frame(self, frame):
        """对帧应用高斯模糊"""
        import cv2
        return cv2.GaussianBlur(frame, (self.kernel_size, self.kernel_size), 0)


class EdgeDetector(VideoProcessor):
    """边缘检测处理器"""
    
    def __init__(self, low_threshold=50, high_threshold=150):
        """初始化边缘检测处理器
        
        Args:
            low_threshold: Canny检测器低阈值
            high_threshold: Canny检测器高阈值
        """
        super().__init__("EdgeDetector")
        self.low_threshold = low_threshold
        self.high_threshold = high_threshold
    
    def process_frame(self, frame):
        """对帧应用Canny边缘检测"""
        import cv2
        # 如果是彩色图像，先转为灰度
        if len(frame.shape) == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame
            
        edges = cv2.Canny(gray, self.low_threshold, self.high_threshold)
        # 转换回三通道，保持与其他处理器兼容
        return cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)


def create_test_video_frames(num_frames=30, width=640, height=480):
    """创建测试视频帧
    
    Args:
        num_frames: 帧数
        width: 宽度
        height: 高度
        
    Returns:
        numpy.ndarray: 视频帧数组
    """
    frames = []
    for i in range(num_frames):
        # 创建渐变图像
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        
        # 添加一些动态元素
        # 移动的圆
        import cv2
        x = int(width / 2 + width / 4 * np.sin(i * 0.1))
        y = int(height / 2 + height / 4 * np.cos(i * 0.1))
        cv2.circle(frame, (x, y), 30, (0, 0, 255), -1)
        
        # 变化的矩形
        size = int(50 + 20 * np.sin(i * 0.2))
        cv2.rectangle(frame, (width - 100, height - 100), 
                     (width - 100 + size, height - 100 + size), 
                     (0, 255, 0), -1)
        
        # 添加文本
        cv2.putText(frame, f"Frame {i}", (50, 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        frames.append(frame)
    
    return np.array(frames)


def demo_pipeline():
    """演示基本管道处理"""
    logger.info("开始演示基本管道处理")
    
    # 创建管道
    pipeline = ZeroCopyPipeline()
    
    # 添加处理阶段
    pipeline.add_stage(GrayscaleConverter())
    pipeline.add_stage(BlurProcessor(kernel_size=5))
    pipeline.add_stage(EdgeDetector(low_threshold=50, high_threshold=150))
    
    # 创建测试视频帧
    frames = create_test_video_frames(num_frames=5)
    logger.info(f"创建了测试视频帧: 形状={frames.shape}")
    
    # 执行管道处理
    start_time = time.time()
    result_frames = pipeline.execute(frames)
    end_time = time.time()
    
    logger.info(f"管道处理完成: 耗时={end_time - start_time:.4f}秒")
    logger.info(f"结果视频帧: 形状={result_frames.shape}")
    
    # 打印统计信息
    stats = pipeline.get_stats()
    logger.info(f"管道统计信息: {stats}")


def demo_streaming_pipeline():
    """演示流式处理管道"""
    logger.info("开始演示流式处理管道")
    
    # 创建流式处理管道
    pipeline = StreamingPipeline(chunk_size=5)
    
    # 添加处理阶段
    pipeline.add_stage(GrayscaleConverter())
    pipeline.add_stage(BlurProcessor(kernel_size=5))
    pipeline.add_stage(EdgeDetector(low_threshold=50, high_threshold=150))
    
    # 创建测试视频帧
    frames = create_test_video_frames(num_frames=30)
    
    # 将视频帧分块
    chunks = []
    chunk_size = 5
    for i in range(0, len(frames), chunk_size):
        chunks.append(frames[i:i+chunk_size])
    
    # 流式处理
    start_time = time.time()
    result_chunks = list(pipeline.process_stream(chunks))
    end_time = time.time()
    
    logger.info(f"流式处理完成: 耗时={end_time - start_time:.4f}秒")
    logger.info(f"处理了 {len(chunks)} 个数据块, 得到 {len(result_chunks)} 个结果块")
    
    # 打印统计信息
    stats = pipeline.get_stats()
    logger.info(f"管道统计信息: {stats}")


def demo_error_handling():
    """演示错误处理"""
    logger.info("开始演示错误处理")
    
    # 创建管道
    pipeline = ZeroCopyPipeline()
    
    # 添加一个会抛出异常的处理器
    def error_processor(data):
        if isinstance(data, np.ndarray) and len(data) > 2:
            raise ValueError("演示错误: 数据太多")
        return data
    
    pipeline.add_stage(error_processor)
    
    # 设置错误处理器
    def handle_error(error, context):
        logger.warning(f"捕获到错误: {error}, 上下文: {context}")
        # 返回一个空数组作为后备结果
        return np.array([])
    
    pipeline.set_error_handler(handle_error)
    
    # 创建测试数据
    test_data = np.array([1, 2, 3, 4, 5])
    
    # 执行管道处理
    result = pipeline.execute(test_data)
    
    logger.info(f"错误处理完成，结果: {result}")


if __name__ == "__main__":
    logger.info("=== 流式处理管道示例开始 ===")
    
    # 演示基本管道处理
    demo_pipeline()
    
    # 演示流式处理管道
    demo_streaming_pipeline()
    
    # 演示错误处理
    demo_error_handling()
    
    logger.info("=== 流式处理管道示例结束 ===") 