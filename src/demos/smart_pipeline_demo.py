#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
智能缓冲区与流式处理管道集成演示

演示如何将SmartBuffer与流式处理管道集成，实现高效的视频处理。
通过零拷贝操作和智能内存管理，显著提高大规模视频处理的性能。
"""

import os
import sys
import time
import numpy as np
import cv2
from typing import Tuple, List, Optional

from src.utils.log_handler import get_logger
from src.utils.buffer_manager import BufferManager, BufferType, get_buffer_manager
from src.exporters.stream_pipe import (
    Processor, VideoProcessor, ZeroCopyPipeline, 
    ProcessingMode, create_processor, create_pipeline
)

# 配置日志
logger = get_logger("smart_pipeline_demo")


class SmartBufferVideoProcessor(VideoProcessor):
    """使用智能缓冲区的视频处理器"""
    
    def __init__(self, name: str = None, effect: str = "grayscale"):
        """初始化智能缓冲区视频处理器
        
        Args:
            name: 处理器名称
            effect: 处理效果('grayscale', 'blur', 'edge')
        """
        super().__init__(name or "SmartBufferVideoProcessor")
        self.effect = effect
        self.buffer_manager = get_buffer_manager()
        self.frame_count = 0
        self.processed_frames = 0
        
        # 为处理中间结果分配缓冲区
        self.intermediate_key = f"proc.{self.name}.intermediate"
    
    def process_frame(self, frame: np.ndarray) -> np.ndarray:
        """处理单帧
        
        使用智能缓冲区管理中间结果
        
        Args:
            frame: 输入帧
            
        Returns:
            处理后的帧
        """
        # 将中间结果存入缓冲区
        self.buffer_manager.put(
            f"{self.intermediate_key}.{self.frame_count}",
            frame,
            buffer_type=BufferType.TEMPORARY
        )
        
        # 应用不同效果
        if self.effect == "grayscale":
            # 转换为灰度
            if frame.ndim == 3:
                result = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                # 转回RGB以保持一致的输出格式
                result = cv2.cvtColor(result, cv2.COLOR_GRAY2BGR)
            else:
                result = frame
        elif self.effect == "blur":
            # 应用模糊
            result = cv2.GaussianBlur(frame, (15, 15), 0)
        elif self.effect == "edge":
            # 边缘检测
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if frame.ndim == 3 else frame
            result = cv2.Canny(gray, 50, 150)
            # 转回RGB
            result = cv2.cvtColor(result, cv2.COLOR_GRAY2BGR)
        else:
            result = frame
        
        self.frame_count += 1
        self.processed_frames += 1
        
        # 每100帧清理一次临时缓冲区
        if self.processed_frames % 100 == 0:
            self._cleanup_temp_buffers()
        
        return result
    
    def _cleanup_temp_buffers(self):
        """清理临时缓冲区"""
        # 保留最近50帧的中间结果
        for i in range(max(0, self.frame_count - 100), self.frame_count - 50):
            self.buffer_manager.release(
                f"{self.intermediate_key}.{i}",
                buffer_type=BufferType.TEMPORARY
            )


class SmartHistogramProcessor(Processor):
    """直方图分析处理器
    
    使用智能缓冲区存储和分析帧直方图
    """
    
    def __init__(self, name: str = None, bins: int = 256):
        """初始化直方图处理器
        
        Args:
            name: 处理器名称
            bins: 直方图柱数
        """
        super().__init__(name or "HistogramProcessor")
        self.bins = bins
        self.buffer_manager = get_buffer_manager()
        self.histogram_key = f"proc.{self.name}.histograms"
        self.frame_count = 0
    
    def process(self, frames: np.ndarray) -> Tuple[np.ndarray, List[np.ndarray]]:
        """处理帧数据
        
        计算并存储每帧的颜色直方图
        
        Args:
            frames: 输入帧数组
            
        Returns:
            Tuple[np.ndarray, List[np.ndarray]]: 原始帧和直方图列表
        """
        # 如果是单帧
        if len(frames.shape) == 3:
            return self._process_single_frame(frames)
        
        # 处理多帧
        histograms = []
        for i, frame in enumerate(frames):
            _, hist = self._process_single_frame(frame)
            histograms.append(hist)
        
        return frames, histograms
    
    def _process_single_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """处理单帧
        
        Args:
            frame: 输入帧
            
        Returns:
            Tuple[np.ndarray, np.ndarray]: 原始帧和直方图
        """
        # 为BGR每个通道计算直方图
        hist_b = cv2.calcHist([frame], [0], None, [self.bins], [0, 256])
        hist_g = cv2.calcHist([frame], [1], None, [self.bins], [0, 256])
        hist_r = cv2.calcHist([frame], [2], None, [self.bins], [0, 256])
        
        # 合并直方图
        combined_hist = np.concatenate([hist_b, hist_g, hist_r], axis=0)
        
        # 存储到缓冲区
        self.buffer_manager.put(
            f"{self.histogram_key}.{self.frame_count}",
            combined_hist,
            buffer_type=BufferType.PIPELINE
        )
        
        self.frame_count += 1
        return frame, combined_hist


class SmartFrameBuffer(Processor):
    """智能帧缓冲处理器
    
    使用循环缓冲区管理视频帧，支持回顾和前瞻
    """
    
    def __init__(self, name: str = None, buffer_size: int = 30):
        """初始化智能帧缓冲处理器
        
        Args:
            name: 处理器名称
            buffer_size: 缓冲区大小（帧数）
        """
        super().__init__(name or "FrameBuffer")
        self.buffer_size = buffer_size
        self.buffer_manager = get_buffer_manager()
        self.frame_key = f"proc.{self.name}.frames"
        self.current_idx = 0
        self.total_frames = 0
    
    def process(self, frame: np.ndarray) -> Tuple[np.ndarray, Optional[np.ndarray], Optional[np.ndarray]]:
        """处理帧数据
        
        将当前帧存入循环缓冲区，并提供前一帧和后一帧引用
        
        Args:
            frame: 输入帧
            
        Returns:
            Tuple[np.ndarray, Optional[np.ndarray], Optional[np.ndarray]]: 
                当前帧、前一帧和后一帧
        """
        # 计算缓冲区索引
        buffer_idx = self.current_idx % self.buffer_size
        
        # 存储当前帧
        self.buffer_manager.put(
            f"{self.frame_key}.{buffer_idx}",
            frame,
            buffer_type=BufferType.STREAM
        )
        
        # 获取前一帧
        prev_idx = (buffer_idx - 1) % self.buffer_size
        prev_frame = None
        if self.total_frames > 0:
            prev_frame = self.buffer_manager.get(
                f"{self.frame_key}.{prev_idx}",
                buffer_type=BufferType.STREAM
            )
        
        # 后一帧（通常为None，除非是回放模式）
        next_idx = (buffer_idx + 1) % self.buffer_size
        next_frame = None
        if self.total_frames >= self.buffer_size:
            next_frame = self.buffer_manager.get(
                f"{self.frame_key}.{next_idx}",
                buffer_type=BufferType.STREAM
            )
        
        # 更新索引
        self.current_idx += 1
        self.total_frames += 1
        
        return frame, prev_frame, next_frame


def create_demo_pipeline() -> ZeroCopyPipeline:
    """创建演示管道
    
    创建使用智能缓冲区的视频处理管道
    
    Returns:
        ZeroCopyPipeline: 处理管道
    """
    # 创建基础管道
    pipeline = create_pipeline()
    
    # 添加处理阶段
    pipeline.add_stage(SmartFrameBuffer(buffer_size=30))
    pipeline.add_stage(SmartBufferVideoProcessor(effect="edge"))
    pipeline.add_stage(SmartHistogramProcessor(bins=64))
    
    # 设置处理模式
    pipeline.set_mode(ProcessingMode.STREAMING)
    
    return pipeline


def process_video(video_path: str, output_path: Optional[str] = None) -> None:
    """处理视频文件
    
    使用智能缓冲区管道处理视频
    
    Args:
        video_path: 输入视频路径
        output_path: 输出视频路径，如果为None则不保存
    """
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
    
    # 创建视频写入器(如果需要)
    writer = None
    if output_path:
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    # 创建处理管道
    pipeline = create_demo_pipeline()
    
    # 获取缓冲区管理器
    buffer_manager = get_buffer_manager()
    
    # 为视频流创建专用缓冲区
    buffer_manager.create_stream_buffer(
        "video.frames",
        frames=min(frame_count, 300),  # 最多缓冲300帧
        height=height,
        width=width,
        channels=3
    )
    
    # 进度统计
    start_time = time.time()
    frame_idx = 0
    
    # 处理每一帧
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # 存入缓冲区
        buffer_manager.put(
            f"video.frames.{frame_idx}",
            frame,
            buffer_type=BufferType.STREAM
        )
        
        # 执行管道处理
        try:
            result = pipeline.execute(frame)
            
            # 分解结果
            if isinstance(result, tuple) and len(result) >= 2:
                processed_frame, histograms = result[0], result[1]
            else:
                processed_frame = result
            
            # 写入输出视频
            if writer is not None:
                writer.write(processed_frame)
            
            # 每100帧显示进度
            if frame_idx % 100 == 0 or frame_idx == frame_count - 1:
                elapsed = time.time() - start_time
                fps_achieved = frame_idx / elapsed if elapsed > 0 else 0
                logger.info(
                    f"处理进度: {frame_idx+1}/{frame_count} "
                    f"({(frame_idx+1)/frame_count*100:.1f}%) "
                    f"速度: {fps_achieved:.1f} FPS"
                )
        except Exception as e:
            logger.error(f"处理第{frame_idx}帧时出错: {e}")
        
        frame_idx += 1
    
    # 释放资源
    cap.release()
    if writer:
        writer.release()
    
    # 显示缓冲区统计
    stats = buffer_manager.get_buffer_stats()
    logger.info("=== 缓冲区性能统计 ===")
    
    # 总体统计
    logger.info(f"总缓冲区数: {stats['total_buffer_count']}")
    logger.info(f"总内存使用: {stats['total_current_size'] / (1024*1024):.2f} MB")
    logger.info(f"内存峰值: {stats['total_peak_size'] / (1024*1024):.2f} MB")
    logger.info(f"缓存命中率: {stats['total_hits'] / (stats['total_hits'] + stats['total_misses']) * 100:.2f}% "
                f"({stats['total_hits']}/{stats['total_hits'] + stats['total_misses']})")
    
    # 各缓冲区使用情况
    logger.info("=== 各缓冲区使用情况 ===")
    for buf_type, utilization in stats["buffer_utilization"].items():
        logger.info(
            f"{buf_type}: {utilization['current_size_mb']:.2f}/{utilization['capacity_mb']:.2f} MB "
            f"({utilization['usage_percent']:.2f}%) "
            f"缓冲区数: {utilization['buffer_count']}"
        )
    
    # 总处理性能
    total_time = time.time() - start_time
    logger.info(f"总处理时间: {total_time:.2f}秒")
    logger.info(f"平均处理速度: {frame_idx/total_time:.2f} FPS")
    
    # 清理缓冲区
    buffer_manager.clear(BufferType.TEMPORARY)
    buffer_manager.clear(BufferType.STREAM)


def create_sample_video(
        output_path: str, 
        duration: int = 5,
        width: int = 640,
        height: int = 480,
        fps: int = 30) -> None:
    """创建样本视频用于测试
    
    Args:
        output_path: 输出路径
        duration: 视频时长(秒)
        width: 宽度
        height: 高度
        fps: 帧率
    """
    # 创建视频写入器
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    if not writer.isOpened():
        logger.error(f"无法创建视频文件: {output_path}")
        return
    
    # 生成帧
    total_frames = int(duration * fps)
    for i in range(total_frames):
        # 创建渐变帧
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        
        # 添加动态图案
        t = i / total_frames
        
        # 绘制移动的圆形
        radius = int(min(width, height) * 0.2)
        center_x = int(width * (0.5 + 0.3 * np.sin(t * 6)))
        center_y = int(height * (0.5 + 0.3 * np.cos(t * 8)))
        
        # 变化的颜色
        color = (
            int(255 * (0.5 + 0.5 * np.sin(t * 9))),
            int(255 * (0.5 + 0.5 * np.sin(t * 7 + 2))),
            int(255 * (0.5 + 0.5 * np.sin(t * 5 + 4)))
        )
        
        # 绘制圆形
        cv2.circle(frame, (center_x, center_y), radius, color, -1)
        
        # 添加彩色条纹
        for j in range(5):
            stripe_y = int(height * (j / 5 + 0.1 * np.sin(t * 10 + j)))
            stripe_color = (
                int(255 * (0.5 + 0.5 * np.sin(j + t * 5))),
                int(255 * (0.5 + 0.5 * np.cos(j + t * 7))),
                int(255 * (0.2 + 0.8 * np.sin(j + t * 9)))
            )
            cv2.line(frame, (0, stripe_y), (width, stripe_y), stripe_color, 5)
        
        # 添加文字
        text = f"Frame {i}/{total_frames}"
        cv2.putText(
            frame, text, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, 
            (255, 255, 255), 2, cv2.LINE_AA
        )
        
        # 写入帧
        writer.write(frame)
    
    # 释放资源
    writer.release()
    logger.info(f"样本视频已创建: {output_path}")


def main():
    """主函数"""
    # 设置临时目录
    temp_dir = os.path.join(os.getcwd(), "temp")
    os.makedirs(temp_dir, exist_ok=True)
    
    # 创建样本视频
    sample_video = os.path.join(temp_dir, "sample_video.mp4")
    output_video = os.path.join(temp_dir, "processed_video.mp4")
    
    # 检查是否需要创建样本视频
    if not os.path.exists(sample_video):
        logger.info("创建样本视频...")
        create_sample_video(sample_video, duration=10)
    
    # 处理视频
    logger.info("开始处理视频...")
    process_video(sample_video, output_video)
    
    logger.info(f"处理完成，输出视频保存至: {output_video}")


if __name__ == "__main__":
    main() 